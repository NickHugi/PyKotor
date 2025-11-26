from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.node.p_subroutine import PSubroutine  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_command_block import PCommandBlock  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_return import PReturn  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]


class ASubroutine(PSubroutine):
    def __init__(self):
        from pykotor.resource.formats.ncs.dencs.node.p_subroutine import PSubroutine  # pyright: ignore[reportMissingImports]
        super().__init__()
        self._command_block: PCommandBlock | None = None
        self._return: PReturn | None = None
        self._id: int = 0

    def set_id(self, sub_id: int):
        self._id = sub_id

    def get_id(self) -> int:
        return self._id

    def clone(self):
        return ASubroutine(
            self.clone_node(self._command_block),
            self.clone_node(self._return)
        )

    def apply(self, sw: Analysis):
        sw.case_a_subroutine(self)

    def get_command_block(self) -> PCommandBlock | None:
        return self._command_block

    def set_command_block(self, node: PCommandBlock | None):
        if self._command_block is not None:
            self._command_block.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._command_block = node

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
        if self._command_block == child:
            self._command_block = None
            return
        if self._return == child:
            self._return = None

    def replace_child(self, old_child: Node, new_child: Node):
        if self._command_block == old_child:
            self.set_command_block(new_child)  # type: ignore
            return
        if self._return == old_child:
            self.set_return(new_child)  # type: ignore

    def clone_node(self, node: Node | None) -> Node | None:
        if node is not None:
            return node.clone()
        return None

