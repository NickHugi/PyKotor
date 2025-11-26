from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.stack.const import Const  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]


class StringConst(Const):
    def __init__(self, value: object):
        from pykotor.resource.formats.ncs.dencs.stack.const import Const  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
        super().__init__()
        self.type = Type(5)
        if isinstance(value, str):
            if value.startswith('"') and value.endswith('"'):
                self.value: str = value[1:-1]
            else:
                self.value = value
        else:
            self.value = str(value)
        self.size = 1

    def value(self) -> str:
        return self.value

    def __str__(self) -> str:
        return str(self.value)

