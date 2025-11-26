from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.stack.const import Const  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]


class IntConst(Const):
    def __init__(self, value: object):
        from pykotor.resource.formats.ncs.dencs.stack.const import Const  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
        super().__init__()
        self.type = Type(3)
        self.value: int = int(value) if isinstance(value, (int, str)) else 0
        self.size = 1

    def value(self) -> int:
        return self.value

    def __str__(self) -> str:
        if self.value == int("FFFFFFFF", 16):
            return "0xFFFFFFFF"
        return str(self.value)

