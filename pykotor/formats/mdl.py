from __future__ import annotations

import io
from enum import IntEnum
from typing import List, Optional

from pykotor.data.color import Color
from pykotor.data.vertex import Vertex
from pykotor.general.binary_reader import BinaryReader
from pykotor.general.binary_writer import BinaryWriter


class ModelType(IntEnum):
    Other = 0
    Effect = 1
    MoveEffect = 2
    CharacterOrCamera = 4
    Door = 8
    Lightsaber = 16
    Placeable = 32
    Unknown = 64


class BinaryNodeFlags(IntEnum):
    Header = 0x0001
    Light = 0x0002
    Emitter = 0x0004
    Camera = 0x0008
    Reference = 0x0010
    Mesh = 0x0020
    Skin = 0x0040
    Anim = 0x0080
    Dangly = 0x0100
    AABB = 0x0200
    Saber = 0x0400


class BinaryEmitterFlags(IntEnum):
    P2P = 0x0001
    P2PSel = 0x0002
    AffectedByWind = 0x0004
    IsTinted = 0x0008
    Bounce = 0x0010
    Random = 0x0020
    Inherit = 0x0040
    InheritVel = 0x0080
    InheritLocal = 0x0100
    Splat = 0x0200
    InheritPart = 0x0400


class BinaryMDXFlags(IntEnum):
    Vertices = 0x001
    Texture = 0x002
    Lightmap = 0x004
    Normals = 0x020
    Bumpmap = 0x080


class MDL:
    @staticmethod
    def load_binary(mdl_data: bytearray, mdx_data: Optional[bytearray] = None) -> MDL:
        return _MDLReader.load(mdl_data, mdx_data)

    @staticmethod
    def load_ascii(mdl_data: str):
        return _MDLReaderAscii.build(mdl_data)

    @staticmethod
    def build_binary(self):
        return _MDLWriter.build(self)

    @staticmethod
    def build_ascii(self):
        return _MDLWriterAscii.build(self)

    def __init__(self):
        self.model_name: str = ""
        self.supermodel: str = ""
        self.root: Node = Node()
        self.animations: List[Animation] = []
        self.box_min: Vertex = Vertex()
        self.box_max: Vertex = Vertex()
        self.radius: float = 0.0
        self.animation_scale: float = 1.0
        self.enable_fog: bool = False
        self.model_type: ModelType = ModelType.Other


class Node:
    def __init__(self):
        self.children: List[Node] = []
        self.controller: List = []


class Animation:
    def __init__(self):
        self.root: Optional[Node] = None
        self.events: List[AnimationEvent] = []
        self.length: float = 0.0
        self.transition: float = 0.0


class AnimationEvent:
    def __init__(self):
        self.time: float = 0.0
        self.name: str = ""


class Trimesh:
    def __init__(self):
        self.faces: List = []

        self.texture: str = ""
        self.lightmap: str = ""

        self.render: bool = False
        self.shadow: bool = False
        self.beaming: bool = False
        self.rotate_texture: bool = False
        self.background_geom: bool = False

        self.animate_uv: bool = False
        self.uv_direction_x: float = 0.0
        self.uv_direction_y: float = 0.0
        self.uv_jitter: float = 0.0
        self.uv_jitter_speed: float = 0.0

        self.transparency_hint: int = 0
        self.ambient_color: Color = Color()
        self.diffuse_color: Color = Color()

        self.box_min: Vertex = Vertex()
        self.box_max: Vertex = Vertex()
        self.average: Vertex = Vertex()
        self.radius: float = 0.0
        self.area: float = 0.0

        self.inverted_counter: List[int] = []


class Light:
    def __init__(self):
        self.light_priority: int = 0
        self.ambient_only: bool = False
        self.dynamic_type: int = 0
        self.affect_dynamic: int = 0
        self.shadow: bool = False
        self.flare: bool = False
        self.fading: bool = False
        # TODO: Convert certain int values to enums


class Emitter:
    def __init__(self):
        self.dead_space: float = 0.0
        self.blast_radius: float = 0.0
        self.blast_length: float = 0.0
        self.branch_count: int = 0
        self.ctrl_pt_smoothing: float = 0.0
        self.x_grid: int = 0
        self.y_grid: int = 0
        self.spawn_type: int = 0
        self.update: str = ""
        self.render: str = ""
        self.blend: str = ""
        self.texture: str = ""
        self.chunk_name: str = ""
        self.twosided_texture: bool = False
        self.loop: bool = False
        self.render_order: int = 0
        self.frame_blender: bool = False
        self.depth_texture: str = ""
        # TODO: Convert certain int values to enums


class AABB:
    def __init__(self):
        self.trimesh: Optional[Trimesh] = None


class Dangly:
    def __init__(self):
        self.trimesh: Optional[Trimesh] = None
        self.displacement: float = 0.0
        self.tightness: float = 0.0
        self.period: float = 0.0
        # TODO: Figure out how to store dangly vertex data...


class Saber:
    def __init__(self):
        self.trimesh: Optional[Trimesh] = None
        # TODO: Figure out how to store saber vertex data...


class _MDLReader:
    @staticmethod
    def load(mdl_data: bytearray, mdx_data:bytearray) -> MDL:
        pass
        # TODO


class _MDLWriter:
    @staticmethod
    def build(mdl: MDL) -> bytearray:
        pass
        # TODO


class _MDLReaderAscii:
    @staticmethod
    def load(mdl_data: str) -> MDL:
        pass
        # TODO


class _MDLWriterAscii:
    @staticmethod
    def build(mdl: MDL) -> str:
        pass