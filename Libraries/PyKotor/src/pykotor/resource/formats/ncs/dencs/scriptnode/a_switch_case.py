from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.scriptnode.script_root_node import ScriptRootNode  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.scriptnode.a_const import AConst  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.scriptnode.a_unk_loop_control import AUnkLoopControl  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode  # pyright: ignore[reportMissingImports]


class ASwitchCase(ScriptRootNode):
    def __init__(self, start: int, val: AConst | None = None):
        from pykotor.resource.formats.ncs.dencs.scriptnode.script_root_node import ScriptRootNode  # pyright: ignore[reportMissingImports]
        super().__init__(start, -1)
        if val is not None:
            self.val(val)

    def end(self, end: int):
        self.end = end

    def val(self, val: AConst):
        val.parent(self)  # type: ignore
        self._val: AConst = val

    def get_unknowns(self) -> list:
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_unk_loop_control import AUnkLoopControl  # pyright: ignore[reportMissingImports]
        unks = []
        for node in self.children:
            if isinstance(node, AUnkLoopControl):
                unks.append(node)
        return unks

    def replace_unknown(self, unk: AUnkLoopControl, newnode: ScriptNode):
        newnode.parent(self)  # type: ignore
        index = self.children.index(unk)
        self.children[index] = newnode
        unk.parent(None)  # type: ignore

    def __str__(self) -> str:
        buff = []
        if self._val is None:
            buff.append(self.tabs + "default:" + self.newline)
        else:
            buff.append(self.tabs + "case " + str(self._val) + ":" + self.newline)
        for child in self.children:
            buff.append(str(child))
        return "".join(buff)

    def close(self):
        super().close()
        if self._val is not None:
            self._val.close()
        self._val = None

