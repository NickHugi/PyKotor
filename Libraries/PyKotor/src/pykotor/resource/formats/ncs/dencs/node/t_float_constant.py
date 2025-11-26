from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.node.token import Token  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]


class TFloatConstant(Token):
    def __init__(self, text: str = "0.0", line: int = 0, pos: int = 0):
        from pykotor.resource.formats.ncs.dencs.node.token import Token  # pyright: ignore[reportMissingImports]
        super().__init__(text)
        self.line = line
        self.pos = pos

    def clone(self) -> Token:
        return TFloatConstant(self.get_text(), self.get_line(), self.get_pos())

    def apply(self, sw: Analysis):
        sw.case_t_float_constant(self)

