from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.scriptnode.a_expression import AExpression  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.stack_entry import StackEntry  # pyright: ignore[reportMissingImports]


class AVectorConstExp(ScriptNode, AExpression):
    def __init__(self, exp1: AExpression, exp2: AExpression, exp3: AExpression):
        from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_expression import AExpression  # pyright: ignore[reportMissingImports]
        super().__init__()
        self.exp1(exp1)
        self.exp2(exp2)
        self.exp3(exp3)

    def exp1(self, exp1: AExpression):
        self._exp1 = exp1
        exp1.parent(self)  # type: ignore

    def exp2(self, exp2: AExpression):
        self._exp2 = exp2
        exp2.parent(self)  # type: ignore

    def exp3(self, exp3: AExpression):
        self._exp3 = exp3
        exp3.parent(self)  # type: ignore

    def __str__(self) -> str:
        return "[" + str(self._exp1) + "," + str(self._exp2) + "," + str(self._exp3) + "]"

    def stackentry(self) -> StackEntry | None:
        return None

    def stackentry(self, stackentry: StackEntry):
        pass

    def close(self):
        super().close()
        if self._exp1 is not None:
            self._exp1.close()  # type: ignore
        self._exp1 = None
        if self._exp2 is not None:
            self._exp2.close()  # type: ignore
        self._exp2 = None
        if self._exp3 is not None:
            self._exp3.close()  # type: ignore
        self._exp3 = None

