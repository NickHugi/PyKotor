from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.node.p_constant import PConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_integer_constant import TIntegerConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]


class AIntConstant(PConstant):
    def __init__(self):
        from pykotor.resource.formats.ncs.dencs.node.p_constant import PConstant  # pyright: ignore[reportMissingImports]
        super().__init__()
        self._integer_constant: TIntegerConstant | None = None

    def clone(self):
        return AIntConstant(self.clone_node(self._integer_constant))

    def apply(self, sw: Analysis):
        sw.case_a_int_constant(self)

    def get_integer_constant(self) -> TIntegerConstant | None:
        return self._integer_constant

    def set_integer_constant(self, node: TIntegerConstant | None):
        if self._integer_constant is not None:
            self._integer_constant.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._integer_constant = node

    def remove_child(self, child: Node):
        if self._integer_constant == child:
            self._integer_constant = None

    def replace_child(self, old_child: Node, new_child: Node):
        if self._integer_constant == old_child:
            self.set_integer_constant(new_child)  # type: ignore

    def clone_node(self, node: Node | None) -> Node | None:
        if node is not None:
            return node.clone()
        return None

