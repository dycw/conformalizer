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
from tomlkit import array, dumps, parse, table
from tomlkit.items import Array, Table
from typed_settings import click_options, settings
from utilities.click import CONTEXT_SETTINGS_HELP_OPTION_NAMES
from utilities.functions import ensure_class
from utilities.logging import basic_config

if TYPE_CHECKING:
    from collections.abc import Iterator

    from tomlkit.container import Container
    from utilities.types import PathLike

_LOGGER = getLogger(__name__)


@settings()
class Settings:
    pyproject__build_system: bool = False
    pyproject__dependency_groups: bool = False
    dry_run: bool = False


@command(**CONTEXT_SETTINGS_HELP_OPTION_NAMES)
@click_options(Settings, "app", show_envvars_in_help=True)
def main(settings: Settings, /) -> None:
    if settings.dry_run:
        _LOGGER.info("Dry run; exiting...")
        return
    _LOGGER.info("Running...")
    if settings.pyproject__build_system:
        _add_pyproject_build_system()
    if settings.pyproject__dependency_groups:
        _add_pyproject_dependency_groups()


def _add_pyproject(*, path: PathLike = "pyproject.toml") -> None:
    path = Path(path)
    if not path.is_file():
        _LOGGER.info("Adding `%s`...", path)
        path.touch()


def _add_pyproject_build_system(*, path: PathLike = "pyproject.toml") -> None:
    with _yield_pyproject("[build-system]", path=path) as doc:
        bs = ensure_class(doc.setdefault("build-system", table()), Table)
        bs["build-backend"] = "uv_build"
        bs["requires"] = ["uv_build"]


def _add_pyproject_dependency_groups(*, path: PathLike = "pyproject2.toml") -> None:
    with _yield_pyproject("[dependency-groups]", path=path) as doc:
        db = ensure_class(doc.setdefault("dependency-groups", table()), Table)
        dev = ensure_class(db.setdefault("dev", array()), Array)
        if (dycw := "dycw-utilities[test]") not in dev:
            dev.append(dycw)
        if (rich := "rich") not in dev:
            dev.append(rich)


@contextmanager
def _yield_pyproject(
    desc: str, /, *, path: PathLike = "pyproject.toml"
) -> Iterator[Container]:
    path = Path(path)
    _add_pyproject(path=path)
    temp = parse(path.read_text())
    yield temp
    current = parse(path.read_text())
    if current != temp:
        _LOGGER.info("Adding `pyproject.toml` %s...", desc)
        _ = path.write_text(dumps(temp))


if __name__ == "__main__":
    basic_config(obj=__name__)
    main()
