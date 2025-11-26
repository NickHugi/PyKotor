from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.node.a_bp_command import ABpCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_command_block import ACommandBlock  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.analysis.pruned_reversed_depth_first_adapter import PrunedReversedDepthFirstAdapter  # pyright: ignore[reportMissingImports]


class CheckIsGlobals(PrunedReversedDepthFirstAdapter):
    def __init__(self):
        from pykotor.resource.formats.ncs.dencs.analysis.pruned_reversed_depth_first_adapter import PrunedReversedDepthFirstAdapter  # pyright: ignore[reportMissingImports]
        super().__init__()
        self.is_globals: bool = False

    def in_a_bp_command(self, node: ABpCommand):
        self.is_globals = True

    def case_a_command_block(self, node: ACommandBlock):
        self.in_a_command_block(node)
        temp = node.get_cmd()
        for i in range(len(temp) - 1, -1, -1):
            temp[i].apply(self)
            if self.is_globals:
                return
        self.out_a_command_block(node)

    def get_is_globals(self) -> bool:
        return self.is_globals

