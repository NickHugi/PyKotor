from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.scriptnode.script_root_node import ScriptRootNode  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.scriptnode.a_expression import AExpression  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.stack_entry import StackEntry  # pyright: ignore[reportMissingImports]


class AActionArgExp(ScriptRootNode, AExpression):
    def __init__(self, start: int = 0, end: int = 0):
        from pykotor.resource.formats.ncs.dencs.scriptnode.script_root_node import ScriptRootNode  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_expression import AExpression  # pyright: ignore[reportMissingImports]
        super().__init__(start, end)
        self.start = start
        self.end = end

    def stackentry(self) -> StackEntry | None:
        return None

    def stackentry(self, stackentry: StackEntry):
        pass

