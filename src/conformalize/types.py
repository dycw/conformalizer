from __future__ import annotations

from typing import TYPE_CHECKING, Any

from tomlkit.items import Array, Table

if TYPE_CHECKING:
    from tomlkit.container import Container


type HasAppend = Array | list[Any]
type HasSetDefault = Container | StrDict | Table
type StrDict = dict[str, Any]


__all__ = ["HasAppend", "HasSetDefault", "StrDict"]
