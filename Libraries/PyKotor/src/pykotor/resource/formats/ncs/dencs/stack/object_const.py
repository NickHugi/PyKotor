from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.stack.const import Const  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]


class ObjectConst(Const):
    def __init__(self, value: object):
        from pykotor.resource.formats.ncs.dencs.stack.const import Const  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
        super().__init__()
        self.type = Type(6)
        self.value: int = int(value) if isinstance(value, (int, str)) else 0
        self.size = 1

    def value(self) -> int:
        return self.value

    def __str__(self) -> str:
        if self.value == 0:
            return "OBJECT_SELF"
        if self.value == 1:
            return "OBJECT_INVALID"
        return str(self.value)

