from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.utils.node_analysis_data import NodeAnalysisData  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.analysis.pruned_reversed_depth_first_adapter import PrunedReversedDepthFirstAdapter  # pyright: ignore[reportMissingImports]


class SetPositions(PrunedReversedDepthFirstAdapter):
    def __init__(self, nodedata: NodeAnalysisData):
        from pykotor.resource.formats.ncs.dencs.analysis.pruned_reversed_depth_first_adapter import PrunedReversedDepthFirstAdapter  # pyright: ignore[reportMissingImports]
        super().__init__()
        self.nodedata: NodeAnalysisData = nodedata
        self.current_pos: int = 0

    def done(self):
        self.nodedata = None

    def default_in(self, node: Node):
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        pos = NodeUtils.get_command_pos(node)
        if pos > 0:
            self.current_pos = pos

    def default_out(self, node: Node):
        self.nodedata.set_pos(node, self.current_pos)

