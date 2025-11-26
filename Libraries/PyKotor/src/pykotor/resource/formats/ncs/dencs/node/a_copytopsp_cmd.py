from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.node.p_cmd import PCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_copy_top_sp_command import PCopyTopSpCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]


class ACopytopspCmd(PCmd):
    def __init__(self):
        from pykotor.resource.formats.ncs.dencs.node.p_cmd import PCmd  # pyright: ignore[reportMissingImports]
        super().__init__()
        self._copy_top_sp_command: PCopyTopSpCommand | None = None

    def clone(self):
        return ACopytopspCmd(self.clone_node(self._copy_top_sp_command))

    def apply(self, sw: Analysis):
        sw.case_a_copytopsp_cmd(self)

    def get_copy_top_sp_command(self) -> PCopyTopSpCommand | None:
        return self._copy_top_sp_command

    def set_copy_top_sp_command(self, node: PCopyTopSpCommand | None):
        if self._copy_top_sp_command is not None:
            self._copy_top_sp_command.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._copy_top_sp_command = node

    def remove_child(self, child: Node):
        if self._copy_top_sp_command == child:
            self._copy_top_sp_command = None

    def replace_child(self, old_child: Node, new_child: Node):
        if self._copy_top_sp_command == old_child:
            self.set_copy_top_sp_command(new_child)  # type: ignore

    def clone_node(self, node: Node | None) -> Node | None:
        if node is not None:
            return node.clone()
        return None

