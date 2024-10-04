from __future__ import annotations

from typing import ClassVar, Literal

from pykotor.resource.formats.mdl.reference_only.constants import MeshType, NodeType
from pykotor.resource.formats.mdl.reference_only.trimesh import Compression, TrimeshNode


class LightsaberNode(TrimeshNode):
    nodetype: ClassVar[NodeType | Literal["LIGHTSABER"]] = NodeType.LIGHTSABER
    meshtype: ClassVar[MeshType | Literal["LIGHTSABER"]] = MeshType.LIGHTSABER

    def __init__(self, name: str = "UNNAMED"):
        super().__init__(name)
        self.compression: Compression = Compression.DISABLED
