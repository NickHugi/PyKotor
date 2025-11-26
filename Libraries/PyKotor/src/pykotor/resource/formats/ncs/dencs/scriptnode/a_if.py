from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.scriptnode.a_control_loop import AControlLoop  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.scriptnode.a_expression import AExpression  # pyright: ignore[reportMissingImports]


class AIf(AControlLoop):
    def __init__(self, start: int = 0, end: int = 0, condition: AExpression | None = None):
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_control_loop import AControlLoop  # pyright: ignore[reportMissingImports]
        super().__init__(start, end)
        if condition is not None:
            self.condition(condition)

    def __str__(self) -> str:
        buff = []
        buff.append(self.tabs + "if (" + str(self.condition) + ") {" + self.newline)
        for child in self.children:
            buff.append(str(child))
        buff.append(self.tabs + "}" + self.newline)
        return "".join(buff)

