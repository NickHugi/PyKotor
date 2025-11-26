from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.node.p_constant import PConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_string_literal import TStringLiteral  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]


class AStringConstant(PConstant):
    def __init__(self):
        from pykotor.resource.formats.ncs.dencs.node.p_constant import PConstant  # pyright: ignore[reportMissingImports]
        super().__init__()
        self._string_literal: TStringLiteral | None = None

    def clone(self):
        return AStringConstant(self.clone_node(self._string_literal))

    def apply(self, sw: Analysis):
        sw.case_a_string_constant(self)

    def get_string_literal(self) -> TStringLiteral | None:
        return self._string_literal

    def set_string_literal(self, node: TStringLiteral | None):
        if self._string_literal is not None:
            self._string_literal.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._string_literal = node

    def remove_child(self, child: Node):
        if self._string_literal == child:
            self._string_literal = None

    def replace_child(self, old_child: Node, new_child: Node):
        if self._string_literal == old_child:
            self.set_string_literal(new_child)  # type: ignore

    def clone_node(self, node: Node | None) -> Node | None:
        if node is not None:
            return node.clone()
        return None

