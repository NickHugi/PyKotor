from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.scriptnode.a_expression import AExpression  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.stack_entry import StackEntry  # pyright: ignore[reportMissingImports]


class AActionExp(ScriptNode, AExpression):
    def __init__(self, action: str, id_val: int, params: list[AExpression]):
        from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_expression import AExpression  # pyright: ignore[reportMissingImports]
        super().__init__()
        self.action: str = action
        self.params: list[AExpression] = []
        for param in params:
            self.add_param(param)
        self.stackentry: StackEntry | None = None
        self.id: int = id_val

    def add_param(self, param: AExpression):
        param.parent(self)  # type: ignore
        self.params.append(param)

    def get_param(self, pos: int) -> AExpression:
        return self.params[pos]

    def action(self) -> str:
        return self.action

    def __str__(self) -> str:
        buff = []
        buff.append(self.action + "(")
        prefix = ""
        for param in self.params:
            buff.append(prefix + str(param))
            prefix = ", "
        buff.append(")")
        return "".join(buff)

    def stackentry(self) -> StackEntry:
        return self.stackentry

    def stackentry(self, stackentry: StackEntry):
        self.stackentry = stackentry

    def get_id(self) -> int:
        return self.id

    def close(self):
        super().close()
        if self.params is not None:
            for param in self.params:
                param.close()  # type: ignore
        self.params = None
        if self.stackentry is not None:
            self.stackentry.close()
        self.stackentry = None

