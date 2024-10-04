
from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from typing_extensions import Literal

NULL: Literal["NULL"] = "NULL"

ANIM_REST_POSE_OFFSET: Literal[5] = 5
ANIM_PADDING: Literal[60] = 60
ANIM_FPS: Literal[30] = 30

WALKMESH_MATERIALS: list[tuple[str, tuple[float, float, float], bool]] = [
    ("wok_NotDefined", (0.400, 0.400, 0.400), False),
    ("wok_Dirt", (0.610, 0.235, 0.050), True),
    ("wok_Obscuring", (0.100, 0.100, 0.100), False),
    ("wok_Grass", (0.000, 0.600, 0.000), True),
    ("wok_Stone", (0.162, 0.216, 0.279), True),
    ("wok_Wood", (0.258, 0.059, 0.007), True),
    ("wok_Water", (0.000, 0.000, 1.000), True),
    ("wok_Nonwalk", (1.000, 0.000, 0.000), False),
    ("wok_Transparent", (1.000, 1.000, 1.000), False),
    ("wok_Carpet", (1.000, 0.000, 1.000), True),
    ("wok_Metal", (0.434, 0.552, 0.730), True),
    ("wok_Puddles", (0.509, 0.474, 0.147), True),
    ("wok_Swamp", (0.216, 0.216, 0.000), True),
    ("wok_Mud", (0.091, 0.147, 0.028), True),
    ("wok_Leaves", (1.000, 0.262, 0.000), True),
    ("wok_Lava", (0.300, 0.000, 0.000), False),
    ("wok_BottomlessPit", (0.000, 0.000, 0.000), True),
    ("wok_DeepWater", (0.000, 0.000, 0.216), False),
    ("wok_Door", (0.000, 0.000, 0.000), True),
    ("wok_Snow", (0.800, 0.800, 0.800), False),
    ("wok_Sand", (1.000, 1.000, 0.000), True),
    ("wok_BareBones", (0.500, 0.500, 0.100), True),
    ("wok_StoneBridge", (0.081, 0.108, 0.139), True),
]
NAME_TO_WALKMESH_MATERIAL: dict[str, tuple[str, tuple[float, float, float], bool]] = {
    mat[0]: mat
    for mat in WALKMESH_MATERIALS
}
NON_WALKABLE: list[int] = [
    mat_idx
    for mat_idx, mat in enumerate(WALKMESH_MATERIALS)
    if not mat[2]
]

UV_MAP_MAIN: Literal["UVMap"] = "UVMap"
UV_MAP_LIGHTMAP: Literal["UVMap_lm"] = "UVMap_lm"


class Classification:
    OTHER: ClassVar[Literal["OTHER"]] = "OTHER"
    TILE: ClassVar[Literal["TILE"]] = "TILE"
    CHARACTER: ClassVar[Literal["CHARACTER"]] = "CHARACTER"
    DOOR: ClassVar[Literal["DOOR"]] = "DOOR"
    EFFECT: ClassVar[Literal["EFFECT"]] = "EFFECT"
    GUI: ClassVar[Literal["GUI"]] = "GUI"
    LIGHTSABER: ClassVar[Literal["LIGHTSABER"]] = "LIGHTSABER"
    PLACEABLE: ClassVar[Literal["PLACEABLE"]] = "PLACEABLE"
    FLYER: ClassVar[Literal["FLYER"]] = "FLYER"
    DANGLYMESH: ClassVar[Literal["DANGLYMESH"]] = "DANGLYMESH"
    TRIMESH: ClassVar[Literal["TRIMESH"]] = "TRIMESH"
    UNKNOWN: ClassVar[Literal["UNKNOWN"]] = "UNKNOWN"


class RootType:
    MODEL: ClassVar[Literal["MODEL"]] = "MODEL"
    WALKMESH: ClassVar[Literal["WALKMESH"]] = "WALKMESH"


class NodeType:
    DUMMY: ClassVar[Literal["DUMMY"]] = "DUMMY"
    REFERENCE: ClassVar[Literal["REFERENCE"]] = "REFERENCE"
    TRIMESH: ClassVar[Literal["TRIMESH"]] = "TRIMESH"
    DANGLYMESH: ClassVar[Literal["DANGLYMESH"]] = "DANGLYMESH"
    SKIN: ClassVar[Literal["SKIN"]] = "SKIN"
    EMITTER: ClassVar[Literal["EMITTER"]] = "EMITTER"
    LIGHT: ClassVar[Literal["LIGHT"]] = "LIGHT"
    AABB: ClassVar[Literal["AABB"]] = "AABB"
    LIGHTSABER: ClassVar[Literal["LIGHTSABER"]] = "LIGHTSABER"


class DummyType:
    NONE: ClassVar[Literal["NONE"]] = "NONE"
    MDLROOT: ClassVar[Literal["MDLROOT"]] = "MDLROOT"
    PWKROOT: ClassVar[Literal["PWKROOT"]] = "PWKROOT"
    DWKROOT: ClassVar[Literal["DWKROOT"]] = "DWKROOT"
    PTHROOT: ClassVar[Literal["PTHROOT"]] = "PTHROOT"
    REFERENCE: ClassVar[Literal["REFERENCE"]] = "REFERENCE"
    PATHPOINT: ClassVar[Literal["PATHPOINT"]] = "PATHPOINT"
    USE1: ClassVar[Literal["USE1"]] = "USE1"
    USE2: ClassVar[Literal["USE2"]] = "USE2"


class MeshType:
    TRIMESH: ClassVar[Literal["TRIMESH"]] = "TRIMESH"
    DANGLYMESH: ClassVar[Literal["DANGLYMESH"]] = "DANGLYMESH"
    LIGHTSABER: ClassVar[Literal["LIGHTSABER"]] = "LIGHTSABER"
    SKIN: ClassVar[Literal["SKIN"]] = "SKIN"
    AABB: ClassVar[Literal["AABB"]] = "AABB"
    EMITTER: ClassVar[Literal["EMITTER"]] = "EMITTER"


class WalkmeshType:
    WOK: ClassVar[Literal["WOK"]] = "WOK"
    PWK: ClassVar[Literal["PWK"]] = "PWK"
    DWK: ClassVar[Literal["DWK"]] = "DWK"


class ImportOptions:
    def __init__(self):
        self.import_geometry: bool = True
        self.import_animations: bool = True
        self.import_walkmeshes: bool = True
        self.build_materials: bool = True
        self.build_armature: bool = False


class ExportOptions:
    def __init__(self):
        self.export_for_tsl: bool = False
        self.export_for_xbox: bool = False
        self.export_animations: bool = True
        self.export_walkmeshes: bool = True
        self.compress_quaternions: bool = False
