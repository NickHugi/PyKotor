from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.node.p_cmd import PCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_move_sp_command import PMoveSpCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]


class AMovespCmd(PCmd):
    def __init__(self):
        from pykotor.resource.formats.ncs.dencs.node.p_cmd import PCmd  # pyright: ignore[reportMissingImports]
        super().__init__()
        self._move_sp_command: PMoveSpCommand | None = None

    def clone(self):
        return AMovespCmd(self.clone_node(self._move_sp_command))

    def apply(self, sw: Analysis):
        sw.case_a_movesp_cmd(self)

    def get_move_sp_command(self) -> PMoveSpCommand | None:
        return self._move_sp_command

    def set_move_sp_command(self, node: PMoveSpCommand | None):
        if self._move_sp_command is not None:
            self._move_sp_command.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._move_sp_command = node

    def remove_child(self, child: Node):
        if self._move_sp_command == child:
            self._move_sp_command = None

    def replace_child(self, old_child: Node, new_child: Node):
        if self._move_sp_command == old_child:
            self.set_move_sp_command(new_child)  # type: ignore

    def clone_node(self, node: Node | None) -> Node | None:
        if node is not None:
            return node.clone()
        return None

