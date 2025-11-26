from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.node.p_program import PProgram  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_subroutine import PSubroutine  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_return import PReturn  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_rsadd_command import PRsaddCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_jump_to_subroutine import PJumpToSubroutine  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_size import PSize  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]


class AProgram(PProgram):
    def __init__(self):
        from pykotor.resource.formats.ncs.dencs.node.p_program import PProgram  # pyright: ignore[reportMissingImports]
        super().__init__()
        self._size: PSize | None = None
        self._conditional: PRsaddCommand | None = None
        self._jump_to_subroutine: PJumpToSubroutine | None = None
        self._return: PReturn | None = None
        self._subroutine: list[PSubroutine] = []

    def clone(self):
        from pykotor.resource.formats.ncs.dencs.node.p_size import PSize  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.p_rsadd_command import PRsaddCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.p_jump_to_subroutine import PJumpToSubroutine  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.p_return import PReturn  # pyright: ignore[reportMissingImports]
        return AProgram(
            self.clone_node(self._size),
            self.clone_node(self._conditional),
            self.clone_node(self._jump_to_subroutine),
            self.clone_node(self._return),
            self.clone_list(self._subroutine)
        )

    def apply(self, sw: Analysis):
        sw.case_a_program(self)

    def get_size(self) -> PSize | None:
        return self._size

    def set_size(self, node: PSize | None):
        if self._size is not None:
            self._size.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._size = node

    def get_conditional(self) -> PRsaddCommand | None:
        return self._conditional

    def set_conditional(self, node: PRsaddCommand | None):
        if self._conditional is not None:
            self._conditional.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._conditional = node

    def get_jump_to_subroutine(self) -> PJumpToSubroutine | None:
        return self._jump_to_subroutine

    def set_jump_to_subroutine(self, node: PJumpToSubroutine | None):
        if self._jump_to_subroutine is not None:
            self._jump_to_subroutine.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._jump_to_subroutine = node

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

    def get_subroutine(self) -> list[PSubroutine]:
        return self._subroutine

    def add_subroutine(self, sub: PSubroutine):
        if sub.parent() is not None:
            sub.parent().remove_child(sub)
        sub.set_parent(self)
        self._subroutine.append(sub)

    def remove_child(self, child: Node):
        if self._size == child:
            self._size = None
            return
        if self._conditional == child:
            self._conditional = None
            return
        if self._jump_to_subroutine == child:
            self._jump_to_subroutine = None
            return
        if self._return == child:
            self._return = None
            return
        if child in self._subroutine:
            self._subroutine.remove(child)

    def replace_child(self, old_child: Node, new_child: Node):
        if self._size == old_child:
            self.set_size(new_child)  # type: ignore
            return
        if self._conditional == old_child:
            self.set_conditional(new_child)  # type: ignore
            return
        if self._jump_to_subroutine == old_child:
            self.set_jump_to_subroutine(new_child)  # type: ignore
            return
        if self._return == old_child:
            self.set_return(new_child)  # type: ignore
            return
        if old_child in self._subroutine:
            idx = self._subroutine.index(old_child)
            self._subroutine[idx] = new_child  # type: ignore
            if new_child is not None:
                if new_child.parent() is not None:
                    new_child.parent().remove_child(new_child)
                new_child.set_parent(self)

    def clone_node(self, node: Node | None) -> Node | None:
        if node is not None:
            return node.clone()
        return None

    def clone_list(self, lst: list) -> list:
        return [item.clone() for item in lst]

