#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#   "click",
#   "dycw-utilities",
#   "pytest-xdist",
#   "tomlkit",
#   "typed-settings[attrs, click]",
# ]
# ///
from __future__ import annotations

from contextlib import contextmanager
from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING

from click import command
from tomlkit import TOMLDocument, aot, array, document, dumps, parse, table
from tomlkit.items import AoT, Array, Table
from typed_settings import click_options, option, settings
from utilities.click import CONTEXT_SETTINGS_HELP_OPTION_NAMES
from utilities.functions import ensure_class
from utilities.logging import basic_config

if TYPE_CHECKING:
    from collections.abc import Iterator


_LOGGER = getLogger(__name__)


@settings()
class Settings:
    version: str = option(default="3.14", help="Python version")
    pyproject: bool = option(default=False, help="Set up 'pyproject.toml'")
    pyproject__dependency_groups__dev: bool = option(
        default=False, help="Set up 'pyproject.toml' [dependency-groups.dev]"
    )
    pyproject__project__name: str | None = option(
        default=None, help="Set up 'pyproject.toml' [project.name]"
    )
    pyproject__project__optional_dependencies__scripts: bool = option(
        default=False,
        help="Set up 'pyproject.toml' [project.optional-dependencies.scripts]",
    )
    pyproject__tool__uv__indexes: str | None = option(
        default=None, help="Set up 'pyproject.toml' [[uv.tool.index]]"
    )
    ruff: bool = option(default=False, help="Set up 'ruff.toml'")
    dry_run: bool = option(default=False, help="Dry run the CLI")


_PYPROJECT_TOML = Path("pyproject.toml")
_SETTINGS = Settings()


@command(**CONTEXT_SETTINGS_HELP_OPTION_NAMES)
@click_options(Settings, "app", show_envvars_in_help=True)
def main(settings: Settings, /) -> None:
    if settings.dry_run:
        _LOGGER.info("Dry run; exiting...")
        return
    _LOGGER.info("Running...")
    if settings.pyproject:
        _add_pyproject(version=settings.version)
    if settings.pyproject__dependency_groups__dev:
        _add_pyproject_dependency_groups_dev(version=settings.version)
    if (name := settings.pyproject__project__name) is not None:
        _add_pyproject_project_name(name)
    if settings.pyproject__project__optional_dependencies__scripts:
        _add_pyproject_project_optional_dependencies_scripts()
    if (indexes := settings.pyproject__tool__uv__indexes) is not None:
        for index in indexes.split("|"):
            name, url = index.split(",")
            _add_pyproject_uv_index(name, url)


def _add_pyproject(*, version: str = _SETTINGS.version) -> None:
    with _yield_pyproject("[]", version=version):
        ...


def _add_pyproject_dependency_groups_dev(*, version: str = _SETTINGS.version) -> None:
    with _yield_pyproject("[dependency-groups.dev]", version=version) as doc:
        dep_grps = ensure_class(doc.setdefault("dependency-groups", table()), Table)
        dev = ensure_class(dep_grps.setdefault("dev", array()), Array)
        if (dycw := "dycw-utilities[test]") not in dev:
            dev.append(dycw)
        if (rich := "rich") not in dev:
            dev.append(rich)


def _add_pyproject_project_name(
    name: str, /, *, version: str = _SETTINGS.version
) -> None:
    with _yield_pyproject("[project.name]", version=version) as doc:
        proj = ensure_class(doc.setdefault("project", table()), Table)
        proj["name"] = name


def _add_pyproject_project_optional_dependencies_scripts(
    *, version: str = _SETTINGS.version
) -> None:
    with _yield_pyproject(
        "[project.optional-dependencies.scripts]", version=version
    ) as doc:
        proj = ensure_class(doc.setdefault("project", table()), Table)
        opt_deps = ensure_class(
            proj.setdefault("optional-dependencies", table()), Table
        )
        scripts = ensure_class(opt_deps.setdefault("scripts", array()), Array)
        if (click := "click >=8.3.1") not in scripts:
            scripts.append(click)


def _add_pyproject_uv_index(
    name: str, url: str, /, *, version: str = _SETTINGS.version
) -> None:
    with _yield_pyproject("[tool.uv.index]", version=version) as doc:
        tool = ensure_class(doc.setdefault("tool", table()), Table)
        uv = ensure_class(tool.setdefault("uv", table()), Table)
        indexes = ensure_class(uv.setdefault("index", aot()), AoT)
        index = table()
        index["explicit"] = True
        index["name"] = name
        index["url"] = url
        if index not in indexes:
            indexes.append(index)


@contextmanager
def _yield_pyproject(
    desc: str, /, *, version: str = _SETTINGS.version
) -> Iterator[TOMLDocument]:
    try:
        doc = parse(_PYPROJECT_TOML.read_text())
    except FileNotFoundError:
        doc = document()
    bld_sys = ensure_class(doc.setdefault("build-system", table()), Table)
    bld_sys["build-backend"] = "uv_build"
    bld_sys["requires"] = ["uv_build"]
    project = ensure_class(doc.setdefault("project", table()), Table)
    project["requires-python"] = f">= {version}"
    yield doc
    try:
        current = parse(_PYPROJECT_TOML.read_text())
    except FileNotFoundError:
        current = document()
    if current != doc:
        _LOGGER.info("Adding `pyproject.toml` %s...", desc)
        _ = _PYPROJECT_TOML.write_text(dumps(doc))


if __name__ == "__main__":
    basic_config(obj=__name__)
    main()
