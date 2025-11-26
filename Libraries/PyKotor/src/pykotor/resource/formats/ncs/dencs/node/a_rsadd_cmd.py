from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.node.p_cmd import PCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_rsadd_command import PRsaddCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]


class ARsaddCmd(PCmd):
    def __init__(self):
        from pykotor.resource.formats.ncs.dencs.node.p_cmd import PCmd  # pyright: ignore[reportMissingImports]
        super().__init__()
        self._rsadd_command: PRsaddCommand | None = None

    def clone(self):
        return ARsaddCmd(self.clone_node(self._rsadd_command))

    def apply(self, sw: Analysis):
        sw.case_a_rsadd_cmd(self)

    def get_rsadd_command(self) -> PRsaddCommand | None:
        return self._rsadd_command

    def set_rsadd_command(self, node: PRsaddCommand | None):
        if self._rsadd_command is not None:
            self._rsadd_command.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._rsadd_command = node

    def remove_child(self, child: Node):
        if self._rsadd_command == child:
            self._rsadd_command = None

    def replace_child(self, old_child: Node, new_child: Node):
        if self._rsadd_command == old_child:
            self.set_rsadd_command(new_child)  # type: ignore

    def clone_node(self, node: Node | None) -> Node | None:
        if node is not None:
            return node.clone()
        return None

