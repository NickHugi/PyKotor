from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.node.p_cmd import PCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_jump_to_subroutine import PJumpToSubroutine  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]


class AJumpSubCmd(PCmd):
    def __init__(self):
        from pykotor.resource.formats.ncs.dencs.node.p_cmd import PCmd  # pyright: ignore[reportMissingImports, reportUnusedImport]
        super().__init__()
        self._jump_to_subroutine: PJumpToSubroutine | None = None

    def clone(self):
        return AJumpSubCmd(self.clone_node(self._jump_to_subroutine))

    def apply(self, sw: Analysis):
        sw.case_a_jump_sub_cmd(self)

    def get_jump_to_subroutine(self) -> PJumpToSubroutine | None:
        return self._jump_to_subroutine

    def set_jump_to_subroutine(self, node: PJumpToSubroutine | None):
        if self._jump_to_subroutine is not None:
            self._jump_to_subroutine.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._jump_to_subroutine = node

    def remove_child(self, child: Node):
        if self._jump_to_subroutine == child:
            self._jump_to_subroutine = None

    def replace_child(self, old_child: Node, new_child: Node):
        if self._jump_to_subroutine == old_child:
            self.set_jump_to_subroutine(new_child)  # type: ignore

    def clone_node(self, node: Node | None) -> Node | None:
        if node is not None:
            return node.clone()
        return None

