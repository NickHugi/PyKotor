from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.scriptnode.a_expression import AExpression  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.stack_entry import StackEntry  # pyright: ignore[reportMissingImports]


class ABinaryExp(ScriptNode, AExpression):
    def __init__(self, left: AExpression, right: AExpression, op: str):
        from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_expression import AExpression  # pyright: ignore[reportMissingImports]
        super().__init__()
        self.left(left)
        self.right(right)
        self.op: str = op
        self.stackentry: StackEntry | None = None

    def left(self, left: AExpression):
        self._left = left
        left.parent(self)  # type: ignore

    def right(self, right: AExpression):
        self._right = right
        right.parent(self)  # type: ignore

    def __str__(self) -> str:
        return "(" + str(self._left) + " " + self.op + " " + str(self._right) + ")"

    def stackentry(self) -> StackEntry:
        return self.stackentry

    def stackentry(self, stackentry: StackEntry):
        self.stackentry = stackentry

    def close(self):
        super().close()
        if self._left is not None:
            self._left.close()  # type: ignore
            self._left = None
        if self._right is not None:
            self._right.close()  # type: ignore
            self._right = None
        if self.stackentry is not None:
            self.stackentry.close()
        self.stackentry = None

