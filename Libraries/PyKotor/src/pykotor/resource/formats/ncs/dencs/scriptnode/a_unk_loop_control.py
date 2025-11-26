from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode  # pyright: ignore[reportMissingImports]


class AUnkLoopControl(ScriptNode):
    def __init__(self, dest: int):
        from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode  # pyright: ignore[reportMissingImports]
        super().__init__()
        self.dest: int = dest

    def get_destination(self) -> int:
        return self.dest

    def __str__(self) -> str:
        return "BREAK or CONTINUE undetermined"

