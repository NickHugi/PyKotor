from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.node.p_cmd import PCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_return import PReturn  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]


class AReturnCmd(PCmd):
    def __init__(self):
        from pykotor.resource.formats.ncs.dencs.node.p_cmd import PCmd  # pyright: ignore[reportMissingImports]
        super().__init__()
        self._return: PReturn | None = None

    def clone(self):
        return AReturnCmd(self.clone_node(self._return))

    def apply(self, sw: Analysis):
        sw.case_a_return_cmd(self)

    def get_return(self) -> PReturn | None:
        return self._return

    def set_return(self, node: PReturn | None):
        if self._return is not None:
            self._return.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._return = node

    def remove_child(self, child: Node):
        if self._return == child:
            self._return = None

    def replace_child(self, old_child: Node, new_child: Node):
        if self._return == old_child:
            self.set_return(new_child)  # type: ignore

    def clone_node(self, node: Node | None) -> Node | None:
        if node is not None:
            return node.clone()
        return None

