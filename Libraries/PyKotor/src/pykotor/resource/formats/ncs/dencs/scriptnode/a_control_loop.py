from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.scriptnode.script_root_node import ScriptRootNode  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.scriptnode.a_expression import AExpression  # pyright: ignore[reportMissingImports]


class AControlLoop(ScriptRootNode):
    def __init__(self, start: int = 0, end: int = 0):
        from pykotor.resource.formats.ncs.dencs.scriptnode.script_root_node import ScriptRootNode  # pyright: ignore[reportMissingImports]
        super().__init__(start, end)
        self.condition: AExpression | None = None

    def end(self, end: int):
        self.end = end

    def condition(self, condition: AExpression):
        condition.parent(self)  # type: ignore
        self.condition = condition

    def condition(self) -> AExpression | None:
        return self.condition

    def close(self):
        super().close()
        if self.condition is not None:
            self.condition.close()  # type: ignore
            self.condition = None

