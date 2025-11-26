from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.node.p_command_block import PCommandBlock  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_cmd import PCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]


class ACommandBlock(PCommandBlock):
    def __init__(self):
        from pykotor.resource.formats.ncs.dencs.node.p_command_block import PCommandBlock  # pyright: ignore[reportMissingImports]
        super().__init__()
        self._cmd: list[PCmd] = []

    def clone(self):
        return ACommandBlock(self.clone_list(self._cmd))

    def apply(self, sw: Analysis):
        sw.case_a_command_block(self)

    def get_cmd(self) -> list[PCmd]:
        return self._cmd

    def set_cmd(self, cmd_list: list[PCmd]):
        self._cmd.clear()
        for cmd in cmd_list:
            if cmd.parent() is not None:
                cmd.parent().remove_child(cmd)
            cmd.set_parent(self)
            self._cmd.append(cmd)

    def add_cmd(self, cmd: PCmd):
        if cmd.parent() is not None:
            cmd.parent().remove_child(cmd)
        cmd.set_parent(self)
        self._cmd.append(cmd)

    def remove_child(self, child: Node):
        if child in self._cmd:
            self._cmd.remove(child)

    def replace_child(self, old_child: Node, new_child: Node):
        if old_child in self._cmd:
            idx = self._cmd.index(old_child)
            if new_child is not None:
                self._cmd[idx] = new_child  # type: ignore
                if new_child.parent() is not None:
                    new_child.parent().remove_child(new_child)
                new_child.set_parent(self)
            else:
                self._cmd.pop(idx)
            old_child.set_parent(None)

    def clone_list(self, lst: list) -> list:
        return [item.clone() for item in lst]

