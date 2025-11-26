from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.stack_entry import StackEntry  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.variable import Variable  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.var_struct import VarStruct  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]


class AVarRef(ScriptNode, AExpression):
    def __init__(self, var: Variable | VarStruct):
        from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_expression import AExpression  # pyright: ignore[reportMissingImports]
        super().__init__()
        self.var_var(var)

    def type(self) -> Type:
        return self.var_var().type()

    def var_var(self) -> Variable:
        return self._var

    def var_var(self, var: Variable | VarStruct):
        if isinstance(var, VarStruct):
            self._var = var
        else:
            self._var = var

    def choose_struct_element(self, var: Variable):
        from pykotor.resource.formats.ncs.dencs.stack.var_struct import VarStruct  # pyright: ignore[reportMissingImports]
        if isinstance(self._var, VarStruct) and self._var.contains(var):
            self._var = var
            return
        raise RuntimeError("Attempted to select a struct element not in struct")

    def __str__(self) -> str:
        return str(self._var)

    def stackentry(self) -> StackEntry:
        return self._var

    def stackentry(self, stackentry: StackEntry):
        from pykotor.resource.formats.ncs.dencs.stack.variable import Variable  # pyright: ignore[reportMissingImports]
        self.var_var(stackentry)

    def close(self):
        super().close()
        if self._var is not None:
            self._var.close()
        self._var = None

