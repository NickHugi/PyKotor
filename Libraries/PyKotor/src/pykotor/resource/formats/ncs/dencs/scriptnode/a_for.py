from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode  # pyright: ignore[reportMissingImports]


class AFor(ScriptNode):
    def __init__(self):
        from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode  # pyright: ignore[reportMissingImports]
        super().__init__()

