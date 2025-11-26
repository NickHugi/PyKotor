from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.node.p_const_command import PConstCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_const import TConst  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_integer_constant import TIntegerConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_constant import PConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_semi import TSemi  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]


class AConstCommand(PConstCommand):
    def __init__(self):
        from pykotor.resource.formats.ncs.dencs.node.p_const_command import PConstCommand  # pyright: ignore[reportMissingImports]
        super().__init__()
        self._const: TConst | None = None
        self._pos: TIntegerConstant | None = None
        self._type: TIntegerConstant | None = None
        self._constant: PConstant | None = None
        self._semi: TSemi | None = None

    def clone(self):
        return AConstCommand(
            self.clone_node(self._const),
            self.clone_node(self._pos),
            self.clone_node(self._type),
            self.clone_node(self._constant),
            self.clone_node(self._semi)
        )

    def apply(self, sw: Analysis):
        sw.case_a_const_command(self)

    def get_const(self) -> TConst | None:
        return self._const

    def set_const(self, node: TConst | None):
        if self._const is not None:
            self._const.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._const = node

    def get_pos(self) -> TIntegerConstant | None:
        return self._pos

    def set_pos(self, node: TIntegerConstant | None):
        if self._pos is not None:
            self._pos.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._pos = node

    def get_type(self) -> TIntegerConstant | None:
        return self._type

    def set_type(self, node: TIntegerConstant | None):
        if self._type is not None:
            self._type.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._type = node

    def get_constant(self) -> PConstant | None:
        return self._constant

    def set_constant(self, node: PConstant | None):
        if self._constant is not None:
            self._constant.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._constant = node

    def get_semi(self) -> TSemi | None:
        return self._semi

    def set_semi(self, node: TSemi | None):
        if self._semi is not None:
            self._semi.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._semi = node

    def remove_child(self, child: Node):
        if self._const == child:
            self._const = None
            return
        if self._pos == child:
            self._pos = None
            return
        if self._type == child:
            self._type = None
            return
        if self._constant == child:
            self._constant = None
            return
        if self._semi == child:
            self._semi = None

    def replace_child(self, old_child: Node, new_child: Node):
        if self._const == old_child:
            self.set_const(new_child)  # type: ignore
            return
        if self._pos == old_child:
            self.set_pos(new_child)  # type: ignore
            return
        if self._type == old_child:
            self.set_type(new_child)  # type: ignore
            return
        if self._constant == old_child:
            self.set_constant(new_child)  # type: ignore
            return
        if self._semi == old_child:
            self.set_semi(new_child)  # type: ignore

    def clone_node(self, node: Node | None) -> Node | None:
        if node is not None:
            return node.clone()
        return None

