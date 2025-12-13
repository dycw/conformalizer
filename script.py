#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#   "click",
#   "dycw-utilities",
#   "pytest-xdist",
# ]
# ///
from __future__ import annotations

from logging import getLogger

from click import command, option
from utilities.click import CONTEXT_SETTINGS_HELP_OPTION_NAMES
from utilities.logging import basic_config

_LOGGER = getLogger(__name__)


@command(**CONTEXT_SETTINGS_HELP_OPTION_NAMES)
@option("--dry-run/--no-dry-run", default=False, show_default=False, help="Dry run")
def main(*, dry_run: bool = False) -> None:
    if dry_run:
        _LOGGER.info("Dry run; exiting...")
        return
    _LOGGER.info("Running...")


if __name__ == "__main__":
    basic_config(obj=__name__)
    main()
