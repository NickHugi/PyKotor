from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]


class Token(Node):
    def __init__(self, text: str = ""):
        from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
        super().__init__()
        self.text: str = text
        self.line: int = 0
        self.pos: int = 0

    def get_text(self) -> str:
        return self.text

    def set_text(self, text: str):
        self.text = text

    def get_line(self) -> int:
        return self.line

    def set_line(self, line: int):
        self.line = line

    def get_pos(self) -> int:
        return self.pos

    def set_pos(self, pos: int):
        self.pos = pos

    def __str__(self) -> str:
        return self.text + " "

    def remove_child(self, child: Node):
        pass

    def replace_child(self, old_child: Node, new_child: Node):
        pass

    def clone(self) -> Node:
        cloned = self.__class__(self.text)
        cloned.line = self.line
        cloned.pos = self.pos
        return cloned

