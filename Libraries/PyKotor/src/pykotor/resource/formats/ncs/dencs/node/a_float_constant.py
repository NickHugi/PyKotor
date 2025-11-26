from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.node.p_constant import PConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_float_constant import TFloatConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]


class AFloatConstant(PConstant):
    def __init__(self):
        from pykotor.resource.formats.ncs.dencs.node.p_constant import PConstant  # pyright: ignore[reportMissingImports]
        super().__init__()
        self._float_constant: TFloatConstant | None = None

    def clone(self):
        return AFloatConstant(self.clone_node(self._float_constant))

    def apply(self, sw: Analysis):
        sw.case_a_float_constant(self)

    def get_float_constant(self) -> TFloatConstant | None:
        return self._float_constant

    def set_float_constant(self, node: TFloatConstant | None):
        if self._float_constant is not None:
            self._float_constant.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._float_constant = node

    def remove_child(self, child: Node):
        if self._float_constant == child:
            self._float_constant = None

    def replace_child(self, old_child: Node, new_child: Node):
        if self._float_constant == old_child:
            self.set_float_constant(new_child)  # type: ignore

    def clone_node(self, node: Node | None) -> Node | None:
        if node is not None:
            return node.clone()
        return None

