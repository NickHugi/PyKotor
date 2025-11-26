from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode  # pyright: ignore[reportMissingImports]


class ScriptRootNode(ScriptNode):
    def __init__(self, start: int = 0, end: int = 0):
        from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode  # pyright: ignore[reportMissingImports]
        super().__init__()
        self.children: list[ScriptNode] = []
        self.start: int = start
        self.end: int = end

    def add_child(self, child: ScriptNode):
        child.parent(self)  # type: ignore
        self.children.append(child)

    def add_children(self, children: list[ScriptNode]):
        for child in children:
            self.add_child(child)

    def remove_child(self, child: ScriptNode):
        if child in self.children:
            self.children.remove(child)
            child.parent(None)  # type: ignore

    def remove_children(self) -> list[ScriptNode]:
        children = list(self.children)
        for child in children:
            child.parent(None)  # type: ignore
        self.children.clear()
        return children

    def remove_last_child(self) -> ScriptNode | None:
        if len(self.children) == 0:
            return None
        child = self.children.pop()
        child.parent(None)  # type: ignore
        return child

    def get_children(self) -> list[ScriptNode]:
        return self.children

    def size(self) -> int:
        return len(self.children)

    def get_last_child(self) -> ScriptNode | None:
        if len(self.children) == 0:
            return None
        return self.children[-1]

    def close(self):
        super().close()
        if self.children is not None:
            for child in self.children:
                child.close()
        self.children = None

