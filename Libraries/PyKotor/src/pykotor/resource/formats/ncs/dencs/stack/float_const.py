from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.stack.const import Const  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]


class FloatConst(Const):
    def __init__(self, value: object):
        from pykotor.resource.formats.ncs.dencs.stack.const import Const  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
        super().__init__()
        self.type = Type(4)
        self.value: float = float(value) if isinstance(value, (int, float, str)) else 0.0
        self.size = 1

    def value(self) -> float:
        return self.value

    def __str__(self) -> str:
        return str(self.value)

