from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.scriptnode.a_expression import AExpression  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.variable import Variable  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]


class AVarDecl(ScriptNode):
    def __init__(self, var: Variable):
        from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode  # pyright: ignore[reportMissingImports]
        super().__init__()
        self.var_var(var)
        self.exp: AExpression | None = None
        self.is_fcn_return: bool = False

    def var_var(self, var: Variable):
        self._var = var

    def var_var(self) -> Variable:
        return self._var

    def is_fcn_return(self, is_val: bool):
        self.is_fcn_return = is_val

    def is_fcn_return(self) -> bool:
        return self.is_fcn_return

    def type(self) -> Type:
        return self._var.type()

    def initialize_exp(self, exp: AExpression):
        exp.parent(self)  # type: ignore
        self.exp = exp

    def remove_exp(self) -> AExpression | None:
        aexp = self.exp
        if self.exp is not None:
            self.exp.parent(None)  # type: ignore
        self.exp = None
        return aexp

    def exp(self) -> AExpression | None:
        return self.exp

    def __str__(self) -> str:
        if self.exp is None:
            return self.tabs + self._var.to_decl_string() + ";" + self.newline
        return self.tabs + self._var.to_decl_string() + " = " + str(self.exp) + ";" + self.newline

    def close(self):
        super().close()
        if self.exp is not None:
            self.exp.close()  # type: ignore
        self.exp = None
        if self._var is not None:
            self._var.close()
        self._var = None

