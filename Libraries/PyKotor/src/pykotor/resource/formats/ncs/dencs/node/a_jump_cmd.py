from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.node.p_cmd import PCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_jump_command import PJumpCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]


class AJumpCmd(PCmd):
    def __init__(self):
        from pykotor.resource.formats.ncs.dencs.node.p_cmd import PCmd  # pyright: ignore[reportMissingImports]
        super().__init__()
        self._jump_command: PJumpCommand | None = None

    def clone(self):
        return AJumpCmd(self.clone_node(self._jump_command))

    def apply(self, sw: Analysis):
        sw.case_a_jump_cmd(self)

    def get_jump_command(self) -> PJumpCommand | None:
        return self._jump_command

    def set_jump_command(self, node: PJumpCommand | None):
        if self._jump_command is not None:
            self._jump_command.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._jump_command = node

    def remove_child(self, child: Node):
        if self._jump_command == child:
            self._jump_command = None

    def replace_child(self, old_child: Node, new_child: Node):
        if self._jump_command == old_child:
            self.set_jump_command(new_child)  # type: ignore

    def clone_node(self, node: Node | None) -> Node | None:
        if node is not None:
            return node.clone()
        return None

