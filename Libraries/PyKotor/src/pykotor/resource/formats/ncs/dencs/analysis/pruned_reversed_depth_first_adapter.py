from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import AnalysisAdapter  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.start import Start  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]


class PrunedReversedDepthFirstAdapter(AnalysisAdapter):
    def __init__(self):
        from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import AnalysisAdapter  # pyright: ignore[reportMissingImports]
        super().__init__()

    def in_start(self, node: Start):
        self.default_in(node)

    def out_start(self, node: Start):
        self.default_out(node)

    def case_start(self, node: Start):
        self.in_start(node)
        node.get_p_program().apply(self)
        self.out_start(node)

    def default_in(self, node: Node):
        super().default_in(node)

    def default_out(self, node: Node):
        super().default_out(node)

