from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.local_stack import LocalStack  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.local_var_stack import LocalVarStack  # pyright: ignore[reportMissingImports]


class StackEntry(ABC):
    def __init__(self):
        self.type: Type | None = None
        self.size: int = 0

    def type(self) -> Type:
        return self.type

    def size(self) -> int:
        return self.size

    @abstractmethod
    def removed_from_stack(self, stack: LocalStack):
        pass

    @abstractmethod
    def added_to_stack(self, stack: LocalStack):
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass

    @abstractmethod
    def get_element(self, pos: int) -> StackEntry:
        pass

    def close(self):
        if self.type is not None:
            self.type.close()
        self.type = None

    @abstractmethod
    def done_parse(self):
        pass

    @abstractmethod
    def done_with_stack(self, stack: LocalVarStack):
        pass

