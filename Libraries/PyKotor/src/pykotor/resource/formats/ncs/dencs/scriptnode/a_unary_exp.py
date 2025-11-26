from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.scriptnode.a_expression import AExpression  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.stack_entry import StackEntry  # pyright: ignore[reportMissingImports]


class AUnaryExp(ScriptNode, AExpression):
    def __init__(self, exp: AExpression, op: str):
        from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_expression import AExpression  # pyright: ignore[reportMissingImports]
        super().__init__()
        self.exp(exp)
        self.op: str = op
        self.stackentry: StackEntry | None = None

    def exp(self, exp: AExpression):
        self._exp = exp
        exp.parent(self)  # type: ignore

    def __str__(self) -> str:
        return "(" + self.op + str(self._exp) + ")"

    def stackentry(self) -> StackEntry:
        return self.stackentry

    def stackentry(self, stackentry: StackEntry):
        self.stackentry = stackentry

    def close(self):
        super().close()
        if self._exp is not None:
            self._exp.close()  # type: ignore
        self._exp = None
        if self.stackentry is not None:
            self.stackentry.close()
        self.stackentry = None

