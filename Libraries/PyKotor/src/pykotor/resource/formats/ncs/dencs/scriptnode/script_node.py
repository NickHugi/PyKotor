from __future__ import annotations

from typing import TYPE_CHECKING
import os

if TYPE_CHECKING:
    pass


class ScriptNode:
    def __init__(self):
        self._parent: ScriptNode | None = None
        self.tabs: str = ""
        self.newline: str = os.linesep

    def parent(self) -> ScriptNode | None:
        return self._parent

    def parent(self, parent: ScriptNode | None):
        self._parent = parent
        if parent is not None:
            self.tabs = parent.tabs + "\t"

    def close(self):
        self._parent = None

