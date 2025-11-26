from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.node.p_cmd import PCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_const_command import PConstCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]


class AConstCmd(PCmd):
    def __init__(self):
        from pykotor.resource.formats.ncs.dencs.node.p_cmd import PCmd  # pyright: ignore[reportMissingImports]
        super().__init__()
        self._const_command: PConstCommand | None = None

    def clone(self):
        return AConstCmd(self.clone_node(self._const_command))

    def apply(self, sw: Analysis):
        sw.case_a_const_cmd(self)

    def get_const_command(self) -> PConstCommand | None:
        return self._const_command

    def set_const_command(self, node: PConstCommand | None):
        if self._const_command is not None:
            self._const_command.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._const_command = node

    def remove_child(self, child: Node):
        if self._const_command == child:
            self._const_command = None

    def replace_child(self, old_child: Node, new_child: Node):
        if self._const_command == old_child:
            self.set_const_command(new_child)  # type: ignore

    def clone_node(self, node: Node | None) -> Node | None:
        if node is not None:
            return node.clone()
        return None

