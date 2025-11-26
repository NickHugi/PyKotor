from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.scriptnode.a_expression import AExpression  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.scriptnode.a_var_ref import AVarRef  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.stack_entry import StackEntry  # pyright: ignore[reportMissingImports]


class AModifyExp(ScriptNode, AExpression):
    def __init__(self, varref: AVarRef, exp: AExpression):
        from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_expression import AExpression  # pyright: ignore[reportMissingImports]
        super().__init__()
        self.var_ref(varref)
        self.expression(exp)

    def var_ref(self, varref: AVarRef):
        self.varref = varref
        varref.parent(self)  # type: ignore

    def expression(self, exp: AExpression):
        self.exp = exp
        exp.parent(self)  # type: ignore

    def expression(self) -> AExpression:
        return self.exp

    def var_ref(self) -> AVarRef:
        return self.varref

    def __str__(self) -> str:
        return str(self.varref) + " = " + str(self.exp)

    def stackentry(self) -> StackEntry:
        return self.varref.var_var()

    def stackentry(self, stackentry: StackEntry):
        pass

    def close(self):
        super().close()
        if self.exp is not None:
            self.exp.close()  # type: ignore
        self.exp = None
        if self.varref is not None:
            self.varref.close()
        self.varref = None

