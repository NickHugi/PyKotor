from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.scriptnode.a_expression import AExpression  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.stack_entry import StackEntry  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.const import Const  # pyright: ignore[reportMissingImports]


class AConst(ScriptNode, AExpression):
    def __init__(self, theconst: Const):
        from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_expression import AExpression  # pyright: ignore[reportMissingImports]
        super().__init__()
        self.theconst: Const = theconst

    def __str__(self) -> str:
        return str(self.theconst)

    def stackentry(self) -> StackEntry:
        return self.theconst

    def stackentry(self, stackentry: StackEntry):
        from pykotor.resource.formats.ncs.dencs.stack.const import Const  # pyright: ignore[reportMissingImports]
        self.theconst = stackentry

    def close(self):
        super().close()
        self.theconst = None

