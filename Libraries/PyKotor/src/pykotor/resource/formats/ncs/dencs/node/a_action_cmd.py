from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.node.p_cmd import PCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_action_command import PActionCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]


class AActionCmd(PCmd):
    def __init__(self):
        from pykotor.resource.formats.ncs.dencs.node.p_cmd import PCmd  # pyright: ignore[reportMissingImports]
        super().__init__()
        self._action_command: PActionCommand | None = None

    def clone(self):
        return AActionCmd(self.clone_node(self._action_command))

    def apply(self, sw: Analysis):
        sw.case_a_action_cmd(self)

    def get_action_command(self) -> PActionCommand | None:
        return self._action_command

    def set_action_command(self, node: PActionCommand | None):
        if self._action_command is not None:
            self._action_command.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._action_command = node

    def remove_child(self, child: Node):
        if self._action_command == child:
            self._action_command = None

    def replace_child(self, old_child: Node, new_child: Node):
        if self._action_command == old_child:
            self.set_action_command(new_child)  # type: ignore

    def clone_node(self, node: Node | None) -> Node | None:
        if node is not None:
            return node.clone()
        return None

