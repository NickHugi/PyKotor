from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]


class Node:
    def __init__(self):
        self._parent: Node | None = None

    def parent(self) -> Node | None:
        return self._parent

    def set_parent(self, parent: Node | None):
        self._parent = parent

    def apply(self, sw: Analysis):
        if hasattr(sw, 'case_node'):
            sw.case_node(self)
        else:
            sw.default_case(self)

    def remove_child(self, child: Node):
        pass

    def replace_child(self, old_child: Node, new_child: Node):
        pass

    def replace_by(self, node: Node):
        if self._parent is not None:
            self._parent.replace_child(self, node)

    def __str__(self) -> str:
        return ""

    def clone(self) -> Node:
        raise NotImplementedError("Subclasses must implement clone")

