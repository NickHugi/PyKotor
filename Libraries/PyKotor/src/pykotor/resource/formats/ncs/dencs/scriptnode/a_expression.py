from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.stack_entry import StackEntry  # pyright: ignore[reportMissingImports]


class AExpression(ABC):
    @abstractmethod
    def __str__(self) -> str:
        pass

    @abstractmethod
    def parent(self) -> ScriptNode | None:
        pass

    @abstractmethod
    def parent(self, parent: ScriptNode | None):
        pass

    @abstractmethod
    def stackentry(self) -> StackEntry:
        pass

    @abstractmethod
    def stackentry(self, stackentry: StackEntry):
        pass

