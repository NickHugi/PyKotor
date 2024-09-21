
from __future__ import annotations

import os

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from typing_extensions import Self


class PyQFileSystemModelNodePathKey(str):
    __slots__ = ()

    def __new__(cls, value: str) -> Self:
        return super().__new__(cls, value)

    def __repr__(self) -> str:
        return f"i{super().__repr__()})"

    def __eq__(self, other: Any) -> bool:  # noqa: PYI032
        if not isinstance(other, str):
            return NotImplemented
        if os.name == "nt":
            return self.lower() == other.lower()
        return super().__eq__(other)

    def __hash__(self):
        if os.name == "nt":
            return hash(self.lower())
        return super().__hash__()
