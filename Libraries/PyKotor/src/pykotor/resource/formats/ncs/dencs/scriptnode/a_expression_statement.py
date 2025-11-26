from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.scriptnode.a_expression import AExpression  # pyright: ignore[reportMissingImports]


class AExpressionStatement(ScriptNode):
    def __init__(self, exp: AExpression):
        from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode  # pyright: ignore[reportMissingImports]
        super().__init__()
        exp.parent(self)  # type: ignore
        self.exp: AExpression = exp

    def exp(self) -> AExpression:
        return self.exp

    def __str__(self) -> str:
        return self.tabs + str(self.exp) + ";" + self.newline

    def parent(self, parent: ScriptNode | None):
        super().parent(parent)
        self.exp.parent(self)  # type: ignore

    def close(self):
        super().close()
        if self.exp is not None:
            self.exp.close()  # type: ignore
        self.exp = None

