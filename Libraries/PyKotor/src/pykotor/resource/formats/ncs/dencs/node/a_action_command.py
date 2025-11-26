from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.node.p_action_command import PActionCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_action import TAction  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_integer_constant import TIntegerConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_semi import TSemi  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]


class AActionCommand(PActionCommand):
    def __init__(self):
        from pykotor.resource.formats.ncs.dencs.node.p_action_command import PActionCommand  # pyright: ignore[reportMissingImports]
        super().__init__()
        self._action: TAction | None = None
        self._pos: TIntegerConstant | None = None
        self._type: TIntegerConstant | None = None
        self._id: TIntegerConstant | None = None
        self._arg_count: TIntegerConstant | None = None
        self._semi: TSemi | None = None

    def clone(self):
        return AActionCommand(
            self.clone_node(self._action),
            self.clone_node(self._pos),
            self.clone_node(self._type),
            self.clone_node(self._id),
            self.clone_node(self._arg_count),
            self.clone_node(self._semi)
        )

    def apply(self, sw: Analysis):
        sw.case_a_action_command(self)

    def get_action(self) -> TAction | None:
        return self._action

    def set_action(self, node: TAction | None):
        if self._action is not None:
            self._action.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._action = node

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

    def get_id(self) -> TIntegerConstant | None:
        return self._id

    def set_id(self, node: TIntegerConstant | None):
        if self._id is not None:
            self._id.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._id = node

    def get_arg_count(self) -> TIntegerConstant | None:
        return self._arg_count

    def set_arg_count(self, node: TIntegerConstant | None):
        if self._arg_count is not None:
            self._arg_count.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._arg_count = node

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
        if self._action == child:
            self._action = None
            return
        if self._pos == child:
            self._pos = None
            return
        if self._type == child:
            self._type = None
            return
        if self._id == child:
            self._id = None
            return
        if self._arg_count == child:
            self._arg_count = None
            return
        if self._semi == child:
            self._semi = None

    def replace_child(self, old_child: Node, new_child: Node):
        if self._action == old_child:
            self.set_action(new_child)  # type: ignore
            return
        if self._pos == old_child:
            self.set_pos(new_child)  # type: ignore
            return
        if self._type == old_child:
            self.set_type(new_child)  # type: ignore
            return
        if self._id == old_child:
            self.set_id(new_child)  # type: ignore
            return
        if self._arg_count == old_child:
            self.set_arg_count(new_child)  # type: ignore
            return
        if self._semi == old_child:
            self.set_semi(new_child)  # type: ignore

    def clone_node(self, node: Node | None) -> Node | None:
        if node is not None:
            return node.clone()
        return None

