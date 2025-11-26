from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.scriptnode.a_expression import AExpression  # pyright: ignore[reportMissingImports]


class AReturnStatement(ScriptNode):
    def __init__(self, returnexp: AExpression | None = None):
        from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode  # pyright: ignore[reportMissingImports]
        super().__init__()
        if returnexp is not None:
            self.returnexp(returnexp)

    def returnexp(self, returnexp: AExpression):
        returnexp.parent(self)  # type: ignore
        self.returnexp: AExpression | None = returnexp

    def exp(self) -> AExpression | None:
        return self.returnexp

    def __str__(self) -> str:
        if self.returnexp is None:
            return self.tabs + "return;" + self.newline
        return self.tabs + "return " + str(self.returnexp) + ";" + self.newline

    def close(self):
        super().close()
        if self.returnexp is not None:
            self.returnexp.close()  # type: ignore
        self.returnexp = None

