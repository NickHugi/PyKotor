from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_subroutine import PSubroutine  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_return import PReturn  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_rsadd_command import PRsaddCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_jump_to_subroutine import PJumpToSubroutine  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_size import PSize  # pyright: ignore[reportMissingImports]


class PProgram(Node):
    pass

