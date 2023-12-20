from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.geometry import SurfaceMaterial, Vector2, Vector3, Vector4
from pykotor.common.misc import Color, Game
from pykotor.common.stream import BinaryReader, BinaryWriter
from pykotor.resource.formats.mdl.mdl_data import (
    MDL,
    MDLAnimation,
    MDLBoneVertex,
    MDLController,
    MDLControllerRow,
    MDLControllerType,
    MDLEvent,
    MDLFace,
    MDLMesh,
    MDLNode,
    MDLNodeFlags,
    MDLSkin,
)

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class _ModelHeader:
    SIZE = 196

    def __init__(
        self,
    ):
        self.geometry: _GeometryHeader = _GeometryHeader()
        self.model_type: int = 0
        self.unknown0: int = 0
        self.padding0: int = 0
        self.fog: int = 0
        self.unknown1: int = 0
        self.offset_to_animations: int = 0
        self.animation_count: int = 0
        self.animation_count2: int = 0
        self.unknown2: int = 0
        self.bounding_box_min: Vector3 = Vector3.from_null()
        self.bounding_box_max: Vector3 = Vector3.from_null()
        self.radius: float = 0.0
        self.anim_scale: float = 0.0
        self.supermodel: str = ""
        self.offset_to_super_root: int = 0
        self.unknown3: int = 0
        self.mdx_size: int = 0
        self.mdx_offset: int = 0
        self.offset_to_name_offsets: int = 0
        self.name_offsets_count: int = 0
        self.name_offsets_count2: int = 0

    def read(
        self,
        reader: BinaryReader,
    ) -> _ModelHeader:
        self.geometry = _GeometryHeader().read(reader)
        self.model_type = reader.read_uint8()
        self.unknown0 = reader.read_uint8()
        self.padding0 = reader.read_uint8()
        self.fog = reader.read_uint8()
        self.unknown1 = reader.read_uint32()
        self.offset_to_animations = reader.read_uint32()
        self.animation_count = reader.read_uint32()
        self.animation_count2 = reader.read_uint32()
        self.unknown2 = reader.read_uint32()
        self.bounding_box_min = reader.read_vector3()
        self.bounding_box_max = reader.read_vector3()
        self.radius = reader.read_single()
        self.anim_scale = reader.read_single()
        self.supermodel = reader.read_string(32)
        self.offset_to_super_root = reader.read_uint32()
        self.unknown3 = reader.read_uint32()
        self.mdx_size = reader.read_uint32()
        self.mdx_offset = reader.read_uint32()
        self.offset_to_name_offsets = reader.read_uint32()
        self.name_offsets_count = reader.read_uint32()
        self.name_offsets_count2 = reader.read_uint32()
        return self

    def write(
        self,
        writer: BinaryWriter,
    ) -> None:
        self.geometry.write(writer)
        writer.write_uint8(self.model_type)
        writer.write_uint8(self.unknown0)
        writer.write_uint8(self.padding0)
        writer.write_uint8(self.fog)
        writer.write_uint32(self.unknown1)
        writer.write_uint32(self.offset_to_animations)
        writer.write_uint32(self.animation_count)
        writer.write_uint32(self.animation_count2)
        writer.write_uint32(self.unknown2)
        writer.write_vector3(self.bounding_box_min)
        writer.write_vector3(self.bounding_box_max)
        writer.write_single(self.radius)
        writer.write_single(self.anim_scale)
        writer.write_string(self.supermodel, string_length=32)
        writer.write_uint32(self.offset_to_super_root)
        writer.write_uint32(self.unknown3)
        writer.write_uint32(self.mdx_size)
        writer.write_uint32(self.mdx_offset)
        writer.write_uint32(self.offset_to_name_offsets)
        writer.write_uint32(self.name_offsets_count)
        writer.write_uint32(self.name_offsets_count2)


class _GeometryHeader:
    SIZE = 80

    K1_FUNCTION_POINTER0 = 4273776
    K2_FUNCTION_POINTER0 = 4285200
    K1_ANIM_FUNCTION_POINTER0 = 4273392
    K2_ANIM_FUNCTION_POINTER0 = 4284816

    K1_FUNCTION_POINTER1 = 4216096
    K2_FUNCTION_POINTER1 = 4216320
    K1_ANIM_FUNCTION_POINTER1 = 4451552
    K2_ANIM_FUNCTION_POINTER1 = 4522928

    GEOM_TYPE_ROOT = 2
    GEOM_TYPE_ANIM = 5

    def __init__(
        self,
    ):
        self.function_pointer0: int = 0
        self.function_pointer1: int = 0
        self.model_name: str = ""
        self.root_node_offset: int = 0
        self.node_count: int = 0
        self.unknown0: bytes = b"\x00" * 28
        self.geometry_type: int = 0
        self.padding: bytes = b"\x00" * 3

    def read(
        self,
        reader: BinaryReader,
    ) -> _GeometryHeader:
        self.function_pointer0 = reader.read_uint32()
        self.function_pointer1 = reader.read_uint32()
        self.model_name = reader.read_string(32)
        self.root_node_offset = reader.read_uint32()
        self.node_count = reader.read_uint32()
        self.unknown0 = reader.read_bytes(28)
        self.geometry_type = reader.read_uint8()
        self.padding = reader.read_bytes(3)
        return self

    def write(
        self,
        writer: BinaryWriter,
    ) -> None:
        writer.write_uint32(self.function_pointer0)
        writer.write_uint32(self.function_pointer1)
        writer.write_string(self.model_name, string_length=32)
        writer.write_uint32(self.root_node_offset)
        writer.write_uint32(self.node_count)
        writer.write_bytes(self.unknown0)
        writer.write_uint8(self.geometry_type)
        writer.write_bytes(self.padding)


class _AnimationHeader:
    SIZE = _GeometryHeader.SIZE + 56

    def __init__(
        self,
    ):
        self.geometry: _GeometryHeader = _GeometryHeader()
        self.duration: float = 0.0
        self.transition: float = 0.0
        self.root: str = ""
        self.offset_to_events: int = 0
        self.event_count: int = 0
        self.event_count2: int = 0
        self.unknown0: int = 0

    def read(
        self,
        reader: BinaryReader,
    ) -> _AnimationHeader:
        self.geometry = _GeometryHeader().read(reader)
        self.duration = reader.read_single()
        self.transition = reader.read_single()
        self.root = reader.read_string(32)
        self.offset_to_events = reader.read_uint32()
        self.event_count = reader.read_uint32()
        self.event_count2 = reader.read_uint32()
        self.unknown0 = reader.read_uint32()
        return self

    def write(
        self,
        writer: BinaryWriter,
    ) -> None:
        self.geometry.write(writer)
        writer.write_single(self.duration)
        writer.write_single(self.transition)
        writer.write_string(self.root, string_length=32)
        writer.write_uint32(self.offset_to_events)
        writer.write_uint32(self.event_count)
        writer.write_uint32(self.event_count2)
        writer.write_uint32(self.unknown0)


class _Animation:
    def __init__(
        self,
    ):
        self.header: _AnimationHeader = _AnimationHeader()
        self.events: list[_EventStructure] = []
        self.w_nodes: list[_Node] = []

    def read(
        self,
        reader: BinaryReader,
    ) -> _Animation:
        self.header = _AnimationHeader().read(reader)

        ...  # read events
        return self

    def write(
        self,
        writer: BinaryWriter,
        game: Game,
    ) -> None:
        self.header.write(writer)
        for event in self.events:
            event.write(writer)
        for node in self.w_nodes:
            node.write(writer, game)

    def events_offset(
        self,
    ) -> int:
        # Always after header
        return _AnimationHeader.SIZE

    def events_size(
        self,
    ) -> int:
        return _EventStructure.SIZE * len(self.events)

    def nodes_offset(
        self,
    ) -> int:
        """Returns offset of the first node relative to the start of the animation data."""
        # Always after events
        return self.events_offset() + self.events_size()

    def nodes_size(
        self,
    ):
        return sum(node.calc_size(Game.K1) for node in self.w_nodes)

    def size(
        self,
    ) -> int:
        return self.nodes_offset() + self.nodes_size()


class _EventStructure:
    SIZE = 36

    def __init__(
        self,
    ):
        self.activation_time: float = 0.0
        self.event_name: str = ""

    def read(
        self,
        reader: BinaryReader,
    ) -> _EventStructure:
        self.activation_time = reader.read_single()
        self.event_name = reader.read_string(32)
        return self

    def write(
        self,
        writer: BinaryWriter,
    ) -> None:
        writer.write_single(self.activation_time)
        writer.write_string(self.event_name, string_length=32)


class _Controller:
    SIZE = 16

    def __init__(
        self,
    ):
        self.type_id: int = 0
        self.unknown0: int = 0xFFFF
        self.row_count: int = 0
        self.key_offset: int = 0
        self.data_offset: int = 0
        self.column_count: int = 0
        self.unknown1: bytes = b"\x00" * 3

    def read(
        self,
        reader: BinaryReader,
    ) -> _Controller:
        self.type_id = reader.read_uint32()
        self.unknown0 = reader.read_uint16()
        self.row_count = reader.read_uint16()
        self.key_offset = reader.read_uint16()
        self.data_offset = reader.read_uint16()
        self.column_count = reader.read_uint8()
        self.unknown1 = reader.read_bytes(3)
        return self

    def write(
        self,
        writer: BinaryWriter,
    ) -> None:
        writer.write_uint32(self.type_id)
        writer.write_uint16(self.unknown0)
        writer.write_uint16(self.row_count)
        writer.write_uint16(self.key_offset)
        writer.write_uint16(self.data_offset)
        writer.write_uint8(self.column_count)
        writer.write_bytes(self.unknown1)


class _Node:
    SIZE = 80

    """
    Ordering:
        # Node Header
        # Trimesh Header
        # ...
        # Face indices count array
        # Face indices offset array
        # Faces
        # Vertices
        # Inverted counter array
        # Children
        # Controllers
        # Controller Data
    """

    def __init__(
        self,
    ):
        self.header: _NodeHeader | None = _NodeHeader()
        self.trimesh: _TrimeshHeader | None = None
        self.skin: _SkinmeshHeader | None = None
        ...
        self.children_offsets: list[int] = []

        self.w_children = []
        self.w_controllers: list[_Controller] = []
        self.w_controller_data: list[float] = []

    def read(
        self,
        reader: BinaryReader,
    ) -> _Node:
        self.header = _NodeHeader().read(reader)

        if self.header.type_id & MDLNodeFlags.MESH:
            self.trimesh = _TrimeshHeader().read(reader)

        if self.header.type_id & MDLNodeFlags.SKIN:
            self.skin = _SkinmeshHeader().read(reader)

        if self.trimesh:
            self.trimesh.read_extra(reader)
        if self.skin:
            self.skin.read_extra(reader)

        reader.seek(self.header.offset_to_children)
        self.children_offsets = [reader.read_uint32() for _ in range(self.header.children_count)]
        return self

    def write(
        self,
        writer: BinaryWriter,
        game: Game,
    ) -> None:
        self.header.write(writer)

        if self.trimesh:
            self.trimesh.write(writer, game)

        if self.trimesh:
            self._write_trimesh_data(writer)
        for child_offset in self.children_offsets:
            writer.write_uint32(child_offset)

        for controller in self.w_controllers:
            controller.write(writer)

        for controller_data in self.w_controller_data:
            writer.write_single(controller_data)

        if len(self.children_offsets) != self.header.children_count:
            msg = f"Number of child offsets in array does not match header count in {self.header.name_id} ({len(self.children_offsets)} vs {self.header.children_count})."
            raise ValueError(msg)

    def _write_trimesh_data(self, writer: BinaryWriter):
        for count in self.trimesh.indices_counts:
            writer.write_uint32(count)
        for offset in self.trimesh.indices_offsets:
            writer.write_uint32(offset)
        for counter in self.trimesh.inverted_counters:
            writer.write_uint32(counter)

        for face in self.trimesh.faces:
            writer.write_uint16(face.vertex1)
            writer.write_uint16(face.vertex2)
            writer.write_uint16(face.vertex3)

        for vertex in self.trimesh.vertices:
            writer.write_vector3(vertex)
        for face in self.trimesh.faces:
            face.write(writer)

    def all_headers_size(
        self,
        game: Game,
    ) -> int:
        size = _Node.SIZE
        if self.trimesh:
            size += _TrimeshHeader.K1_SIZE if game == Game.K1 else _TrimeshHeader.K2_SIZE
        return size

    def indices_counts_offset(
        self,
        game: Game,
    ) -> int:
        return self.all_headers_size(game)

    def indices_offsets_offset(
        self,
        game: Game,
    ) -> int:
        offset = self.indices_counts_offset(game)
        if self.trimesh:
            offset += len(self.trimesh.indices_counts) * 4
        return offset

    def inverted_counters_offset(
        self,
        game: Game,
    ) -> int:
        offset = self.indices_offsets_offset(game)
        if self.trimesh:
            offset += len(self.trimesh.indices_offsets) * 4
        return offset

    def indices_offset(
        self,
        game: Game,
    ) -> int:
        offset = self.inverted_counters_offset(game)
        if self.trimesh:
            offset += len(self.trimesh.inverted_counters) * 4
        return offset

    def vertices_offset(
        self,
        game: Game,
    ) -> int:
        offset = self.indices_offset(game)
        if self.trimesh:
            offset += len(self.trimesh.faces) * 3 * 2
        return offset

    def faces_offset(
        self,
        game: Game,
    ) -> int:
        size = self.vertices_offset(game)
        if self.trimesh:
            size += self.trimesh.vertices_size()
        return size

    def children_offsets_offset(
        self,
        game: Game,
    ) -> int:
        size = self.faces_offset(game)
        if self.trimesh:
            size += self.trimesh.faces_size()
        return size

    def children_offsets_size(
        self,
    ) -> int:
        return 4 * self.header.children_count

    def controllers_offset(
        self,
        game: Game,
    ) -> int:
        return self.children_offsets_offset(game) + self.children_offsets_size()

    def controllers_size(
        self,
    ) -> int:
        return _Controller.SIZE * len(self.w_controllers)

    def controller_data_offset(
        self,
        game: Game,
    ) -> int:
        return self.controllers_offset(game) + self.controllers_size()

    def controller_data_size(
        self,
    ) -> int:
        return len(self.w_controller_data) * 4

    def calc_size(
        self,
        game: Game,
    ) -> int:
        return self.controller_data_offset(game) + self.controller_data_size()


class _NodeHeader:
    SIZE = 80

    def __init__(
        self,
    ):
        self.type_id: int = 1
        self.name_id: int = 0
        self.node_id: int = 0
        self.padding0: int = 0
        self.offset_to_root: int = 0
        self.offset_to_parent: int = 0
        self.position: Vector3 = Vector3.from_null()
        self.orientation: Vector4 = Vector4.from_null()
        self.offset_to_children: int = 0
        self.children_count: int = 0
        self.children_count2: int = 0
        self.offset_to_controllers: int = 0
        self.controller_count: int = 0
        self.controller_count2: int = 0
        self.offset_to_controller_data: int = 0
        self.controller_data_length: int = 0
        self.controller_data_length2: int = 0

    def read(
        self,
        reader: BinaryReader,
    ) -> _NodeHeader:
        self.type_id = reader.read_uint16()
        self.node_id = reader.read_uint16()
        self.name_id = reader.read_uint16()
        self.padding0 = reader.read_uint16()
        self.offset_to_root = reader.read_uint32()
        self.offset_to_parent = reader.read_uint32()
        self.position = reader.read_vector3()
        self.orientation.w = reader.read_single()
        self.orientation.x = reader.read_single()
        self.orientation.y = reader.read_single()
        self.orientation.z = reader.read_single()
        self.offset_to_children = reader.read_uint32()
        self.children_count = reader.read_uint32()
        self.children_count2 = reader.read_uint32()
        self.offset_to_controllers = reader.read_uint32()
        self.controller_count = reader.read_uint32()
        self.controller_count2 = reader.read_uint32()
        self.offset_to_controller_data = reader.read_uint32()
        self.controller_data_length = reader.read_uint32()
        self.controller_data_length2 = reader.read_uint32()
        return self

    def write(
        self,
        writer: BinaryWriter,
    ) -> None:
        writer.write_uint16(self.type_id)
        writer.write_uint16(self.node_id)
        writer.write_uint16(self.name_id)
        writer.write_uint16(self.padding0)
        writer.write_uint32(self.offset_to_root)
        writer.write_uint32(self.offset_to_parent)
        writer.write_vector3(self.position)
        writer.write_single(self.orientation.w)
        writer.write_single(self.orientation.x)
        writer.write_single(self.orientation.y)
        writer.write_single(self.orientation.z)
        writer.write_uint32(self.offset_to_children)
        writer.write_uint32(self.children_count)
        writer.write_uint32(self.children_count2)
        writer.write_uint32(self.offset_to_controllers)
        writer.write_uint32(self.controller_count)
        writer.write_uint32(self.controller_count2)
        writer.write_uint32(self.offset_to_controller_data)
        writer.write_uint32(self.controller_data_length)
        writer.write_uint32(self.controller_data_length2)


class _MDXDataFlags:
    VERTEX = 0x0001
    TEXTURE1 = 0x0002
    TEXTURE2 = 0x0004
    NORMAL = 0x0020
    BUMPMAP = 0x0080


class _TrimeshHeader:
    K1_SIZE = 332
    K2_SIZE = 340

    K1_FUNCTION_POINTER0 = 4216656
    K2_FUNCTION_POINTER0 = 4216880
    K1_SKIN_FUNCTION_POINTER0 = 4216592
    K2_SKIN_FUNCTION_POINTER0 = 4216816
    K1_DANGLY_FUNCTION_POINTER0 = 4216640
    K2_DANGLY_FUNCTION_POINTER0 = 4216864

    K1_FUNCTION_POINTER1 = 4216672
    K2_FUNCTION_POINTER1 = 4216896
    K1_SKIN_FUNCTION_POINTER1 = 4216608
    K2_SKIN_FUNCTION_POINTER1 = 4216832
    K1_DANGLY_FUNCTION_POINTER1 = 4216624
    K2_DANGLY_FUNCTION_POINTER1 = 4216848

    def __init__(
        self,
    ):
        self.function_pointer0: int = 0
        self.function_pointer1: int = 0
        self.offset_to_faces: int = 0
        self.faces_count: int = 0
        self.faces_count2: int = 0
        self.bounding_box_min: Vector3 = Vector3.from_null()
        self.bounding_box_max: Vector3 = Vector3.from_null()
        self.radius: float = 0.0
        self.average: Vector3 = Vector3.from_null()
        self.diffuse: Vector3 = Vector3.from_null()
        self.ambient: Vector3 = Vector3.from_null()
        self.transparency_hint: int = 0
        self.texture1: str = ""
        self.texture2: str = ""
        self.unknown0: bytes = b"\x00" * 24
        self.offset_to_indices_counts: int = 0
        self.indices_counts_count: int = 0
        self.indices_counts_count2: int = 0
        self.offset_to_indices_offset: int = 0
        self.indices_offsets_count: int = 0
        self.indices_offsets_count2: int = 0
        self.offset_to_counters: int = 0
        self.counters_count: int = 0
        self.counters_count2: int = 0
        self.unknown1: bytes = b"\xFF\xFF\xFF\xFF" + b"\xFF\xFF\xFF\xFF" + b"\x00\x00\x00\x00"
        self.saber_unknowns: bytes = b"\x00" * 8
        self.unknown2: int = 0
        self.uv_direction: Vector2 = Vector2.from_null()
        self.uv_jitter: float = 0.0
        self.uv_speed: float = 0.0
        self.mdx_data_size: int = 0
        self.mdx_data_bitmap: int = 0
        self.mdx_vertex_offset: int = 0
        self.mdx_normal_offset: int = 0
        self.mdx_color_offset: int = 0xFFFFFFFF
        self.mdx_texture1_offset: int = 0
        self.mdx_texture2_offset: int = 0
        self.unknown3: int = 0xFFFFFFFF
        self.unknown4: int = 0xFFFFFFFF
        self.unknown5: int = 0xFFFFFFFF
        self.unknown6: int = 0xFFFFFFFF
        self.unknown7: int = 0xFFFFFFFF
        self.unknown8: int = 0xFFFFFFFF
        self.vertex_count: int = 0
        self.texture_count: int = 1
        self.has_lightmap: int = 0
        self.rotate_texture: int = 0
        self.background: int = 0
        self.has_shadow: int = 0
        self.beaming: int = 0
        self.render: int = 0
        self.unknown9: int = 0
        self.unknown10: int = 0
        self.total_area: float = 0.0
        self.unknown11: int = 0
        self.unknown12: int = 0
        self.unknown13: int = 0
        self.mdx_data_offset: int = 0
        self.vertices_offset: int = 0

        self.faces: list[_Face] = []
        self.vertices: list[Vector3] = []
        self.indices_offsets: list[int] = []
        self.indices_counts: list[int] = []
        self.inverted_counters: list[int] = []

    def read(
        self,
        reader: BinaryReader,
    ) -> _TrimeshHeader:
        self.function_pointer0 = reader.read_uint32()
        self.function_pointer1 = reader.read_uint32()
        self.offset_to_faces = reader.read_uint32()
        self.faces_count = reader.read_uint32()
        self.faces_count2 = reader.read_uint32()
        self.bounding_box_min = reader.read_vector3()
        self.bounding_box_max = reader.read_vector3()
        self.radius = reader.read_single()
        self.average = reader.read_vector3()
        self.diffuse = reader.read_vector3()
        self.ambient = reader.read_vector3()
        self.transparency_hint = reader.read_uint32()
        self.texture1 = reader.read_string(32)
        self.texture2 = reader.read_string(32)
        self.unknown0 = reader.read_bytes(24)
        self.offset_to_indices_counts = reader.read_uint32()
        self.indices_counts_count = reader.read_uint32()
        self.indices_counts_count2 = reader.read_uint32()
        self.offset_to_indices_offset = reader.read_uint32()
        self.indices_offsets_count = reader.read_uint32()
        self.indices_offsets_count2 = reader.read_uint32()
        self.offset_to_counters = reader.read_uint32()
        self.counters_count = reader.read_uint32()
        self.counters_count2 = reader.read_uint32()
        self.unknown1 = reader.read_bytes(12)  # -1 -1 0
        self.saber_unknowns = reader.read_bytes(8)  # 3 0 0 0 0 0 0 0
        self.unknown2 = reader.read_uint32()
        self.uv_direction = reader.read_vector2()
        self.uv_jitter = reader.read_single()
        self.uv_speed = reader.read_single()
        self.mdx_data_size = reader.read_uint32()
        self.mdx_data_bitmap = reader.read_uint32()
        self.mdx_vertex_offset = reader.read_uint32()
        self.mdx_normal_offset = reader.read_uint32()
        self.mdx_color_offset = reader.read_uint32()
        self.mdx_texture1_offset = reader.read_uint32()
        self.mdx_texture2_offset = reader.read_uint32()
        self.unknown3 = reader.read_uint32()
        self.unknown4 = reader.read_uint32()
        self.unknown5 = reader.read_uint32()
        self.unknown6 = reader.read_uint32()
        self.unknown7 = reader.read_uint32()
        self.unknown8 = reader.read_uint32()
        self.vertex_count = reader.read_uint16()
        self.texture_count = reader.read_uint16()
        self.has_lightmap = reader.read_uint8()
        self.rotate_texture = reader.read_uint8()
        self.background = reader.read_uint8()
        self.has_shadow = reader.read_uint8()
        self.beaming = reader.read_uint8()
        self.render = reader.read_uint8()
        self.unknown9 = reader.read_uint8()
        self.unknown10 = reader.read_uint8()
        self.total_area = reader.read_single()
        self.unknown11 = reader.read_uint32()
        if self.function_pointer0 in (
            _TrimeshHeader.K2_FUNCTION_POINTER0,
            _TrimeshHeader.K2_DANGLY_FUNCTION_POINTER0,
            _TrimeshHeader.K2_SKIN_FUNCTION_POINTER0,
        ):
            self.unknown12 = reader.read_uint32()
            self.unknown13 = reader.read_uint32()
        self.mdx_data_offset = reader.read_uint32()
        self.vertices_offset = reader.read_uint32()
        return self

    def read_extra(
        self,
        reader: BinaryReader,
    ) -> None:
        reader.seek(self.vertices_offset)
        self.vertices = [reader.read_vector3() for _ in range(self.vertex_count)]

        reader.seek(self.offset_to_faces)
        self.faces = [_Face().read(reader) for _ in range(self.faces_count)]

    def write(
        self,
        writer: BinaryWriter,
        game: Game,
    ) -> None:
        writer.write_uint32(self.function_pointer0)
        writer.write_uint32(self.function_pointer1)
        writer.write_uint32(self.offset_to_faces)
        writer.write_uint32(self.faces_count)
        writer.write_uint32(self.faces_count2)
        writer.write_vector3(self.bounding_box_min)
        writer.write_vector3(self.bounding_box_max)
        writer.write_single(self.radius)
        writer.write_vector3(self.average)
        writer.write_vector3(self.diffuse)
        writer.write_vector3(self.ambient)
        writer.write_uint32(self.transparency_hint)
        writer.write_string(self.texture1, string_length=32)
        writer.write_string(self.texture2, string_length=32)
        writer.write_bytes(self.unknown0)
        writer.write_uint32(self.offset_to_indices_counts)
        writer.write_uint32(self.indices_counts_count)
        writer.write_uint32(self.indices_counts_count2)
        writer.write_uint32(self.offset_to_indices_offset)
        writer.write_uint32(self.indices_offsets_count)
        writer.write_uint32(self.indices_offsets_count2)
        writer.write_uint32(self.offset_to_counters)
        writer.write_uint32(self.counters_count)
        writer.write_uint32(self.counters_count2)
        writer.write_bytes(self.unknown1)
        writer.write_bytes(self.saber_unknowns)
        writer.write_uint32(self.unknown2)
        writer.write_vector2(self.uv_direction)
        writer.write_single(self.uv_jitter)
        writer.write_single(self.uv_speed)
        writer.write_uint32(self.mdx_data_size)
        writer.write_uint32(self.mdx_data_bitmap)
        writer.write_uint32(self.mdx_vertex_offset)
        writer.write_uint32(self.mdx_normal_offset)
        writer.write_uint32(self.mdx_color_offset)
        writer.write_uint32(self.mdx_texture1_offset)
        writer.write_uint32(self.mdx_texture2_offset)
        writer.write_uint32(self.unknown3)
        writer.write_uint32(self.unknown4)
        writer.write_uint32(self.unknown5)
        writer.write_uint32(self.unknown6)
        writer.write_uint32(self.unknown7)
        writer.write_uint32(self.unknown8)
        writer.write_uint16(self.vertex_count)
        writer.write_uint16(self.texture_count)
        writer.write_uint8(self.has_lightmap)
        writer.write_uint8(self.rotate_texture)
        writer.write_uint8(self.background)
        writer.write_uint8(self.has_shadow)
        writer.write_uint8(self.beaming)
        writer.write_uint8(self.render)
        writer.write_uint8(self.unknown9)
        writer.write_uint8(self.unknown10)
        writer.write_single(self.total_area)
        writer.write_uint32(self.unknown11)
        if game == Game.K2:
            writer.write_uint32(self.unknown12)
            writer.write_uint32(self.unknown13)
        writer.write_uint32(self.mdx_data_offset)
        writer.write_uint32(self.vertices_offset)

    def header_size(
        self,
        game: Game,
    ) -> int:
        return _TrimeshHeader.K1_SIZE if game == Game.K1 else _TrimeshHeader.K2_SIZE

    def faces_size(
        self,
    ) -> int:
        return len(self.faces) * _Face.SIZE

    def vertices_size(
        self,
    ) -> int:
        return len(self.vertices) * 12


class _DanglymeshHeader:
    def __init__(
        self,
    ):
        self.offset_to_contraints: int = 0
        self.constraints_count: int = 0
        self.constraints_count2: int = 0
        self.displacement: float = 0.0
        self.tightness: float = 0.0
        self.period: float = 0.0
        self.unknown0: int = 0

    def read(
        self,
        reader: BinaryReader,
    ) -> _DanglymeshHeader:
        self.offset_to_contraints = reader.read_uint32()
        self.constraints_count = reader.read_uint32()
        self.constraints_count2 = reader.read_uint32()
        self.displacement = reader.read_single()
        self.tightness = reader.read_single()
        self.period = reader.read_single()
        self.unknown0 = reader.read_uint32()
        return self

    def write(
        self,
        writer: BinaryWriter,
    ) -> None:
        writer.write_uint32(self.offset_to_contraints)
        writer.write_uint32(self.constraints_count)
        writer.write_uint32(self.constraints_count2)
        writer.write_single(self.displacement)
        writer.write_single(self.tightness)
        writer.write_single(self.period)
        writer.write_uint32(self.unknown0)


class _SkinmeshHeader:
    def __init__(
        self,
    ):
        self.unknown2: int = 0
        self.unknown3: int = 0
        self.unknown4: int = 0
        self.offset_to_mdx_weights: int = 0
        self.offset_to_mdx_bones: int = 0
        self.offset_to_bonemap: int = 0
        self.bonemap_count: int = 0
        self.offset_to_qbones: int = 0
        self.qbones_count: int = 0
        self.qbones_count2: int = 0
        self.offset_to_tbones: int = 0
        self.tbones_count: int = 0
        self.tbones_count2: int = 0
        self.offset_to_unknown0: int = 0
        self.unknown0_count: int = 0
        self.unknown0_count2: int = 0
        self.bones: tuple[int, ...] = tuple(-1 for _ in range(16))
        self.unknown1: int = 0

        self.bonemap: list[int] = []
        self.tbones: list[Vector3] = []
        self.qbones: list[Vector4] = []

    def read(
        self,
        reader: BinaryReader,
    ) -> _SkinmeshHeader:
        self.unknown2 = reader.read_int32()
        self.unknown3 = reader.read_int32()
        self.unknown4 = reader.read_int32()
        self.offset_to_mdx_weights = reader.read_uint32()
        self.offset_to_mdx_bones = reader.read_uint32()
        self.offset_to_bonemap = reader.read_uint32()
        self.bonemap_count = reader.read_uint32()
        self.offset_to_qbones = reader.read_uint32()
        self.qbones_count = reader.read_uint32()
        self.qbones_count2 = reader.read_uint32()
        self.offset_to_tbones = reader.read_uint32()
        self.tbones_count = reader.read_uint32()
        self.tbones_count2 = reader.read_uint32()
        self.offset_to_unknown0 = reader.read_uint32()
        self.unknown0_count = reader.read_uint32()
        self.unknown0_count2 = reader.read_uint32()
        self.bones = tuple(reader.read_uint16() for _ in range(16))
        self.unknown1 = reader.read_uint32()
        return self

    def read_extra(
        self,
        reader: BinaryReader,
    ):
        reader.seek(self.offset_to_bonemap)
        self.bonemap = [reader.read_single() for _ in range(self.bonemap_count)]
        self.tbones = [reader.read_vector3() for _ in range(self.tbones_count)]
        self.qbones = [reader.read_vector4() for _ in range(self.qbones_count)]

    def write(
        self,
        writer: BinaryWriter,
    ) -> None:
        writer.write_int32(self.unknown2)
        writer.write_int32(self.unknown3)
        writer.write_int32(self.unknown4)
        writer.write_uint32(self.offset_to_mdx_weights)
        writer.write_uint32(self.offset_to_mdx_bones)
        writer.write_uint32(self.offset_to_bonemap)
        writer.write_uint32(self.bonemap_count)
        writer.write_uint32(self.offset_to_qbones)
        writer.write_uint32(self.qbones_count)
        writer.write_uint32(self.qbones_count2)
        writer.write_uint32(self.offset_to_tbones)
        writer.write_uint32(self.tbones_count)
        writer.write_uint32(self.tbones_count2)
        writer.write_uint32(self.offset_to_unknown0)
        writer.write_uint32(self.unknown0_count)
        writer.write_uint32(self.unknown0_count2)
        [writer.write_uint32(self.bones[i]) for i in range(16)]
        writer.write_uint32(self.unknown1)


class _SaberHeader:
    def __init__(
        self,
    ):
        self.offset_to_vertices: int = 0
        self.offset_to_texcoords: int = 0
        self.offset_to_normals: int = 0
        self.unknown0: int = 0

    def read(
        self,
        reader: BinaryReader,
    ) -> _SaberHeader:
        self.offset_to_vertices = reader.read_uint32()
        self.offset_to_texcoords = reader.read_uint32()
        self.offset_to_normals = reader.read_uint32()
        self.unknown0 = reader.read_uint32()
        self.unknown1 = reader.read_uint32()
        return self

    def write(
        self,
        writer: BinaryWriter,
    ) -> None:
        writer.write_uint32(self.offset_to_vertices)
        writer.write_uint32(self.offset_to_texcoords)
        writer.write_uint32(self.offset_to_normals)
        writer.write_uint32(self.unknown0)


class _LightHeader:
    def __init__(
        self,
    ):
        self.offset_to_unknown0: int = 0
        self.unknown0_count: int = 0
        self.unknown0_count2: int = 0
        self.offset_to_flare_sizes: int = 0
        self.flare_sizes_count: int = 0
        self.flare_sizes_count2: int = 0
        self.offset_to_flare_positions: int = 0
        self.flare_positions_count: int = 0
        self.flare_positions_count2: int = 0
        self.offset_to_flare_colors: int = 0
        self.flare_colors_count: int = 0
        self.flare_colors_count2: int = 0
        self.offset_to_flare_textures: int = 0
        self.flare_textures_count: int = 0
        self.flare_radius: float = 0.0
        self.light_priority: int = 0
        self.ambient_only: int = 0
        self.dynamic_type: int = 0
        self.affect_dynamic: int = 0
        self.shadow: int = 0
        self.flare: int = 0
        self.fading_light: int = 0

    def read(
        self,
        reader: BinaryReader,
    ) -> _LightHeader:
        self.offset_to_unknown0 = reader.read_uint32()
        self.unknown0_count = reader.read_uint32()
        self.unknown0_count2 = reader.read_uint32()
        self.offset_to_flare_sizes = reader.read_uint32()
        self.flare_sizes_count = reader.read_uint32()
        self.flare_sizes_count2 = reader.read_uint32()
        self.offset_to_flare_positions = reader.read_uint32()
        self.flare_positions_count = reader.read_uint32()
        self.flare_positions_count2 = reader.read_uint32()
        self.offset_to_flare_colors = reader.read_uint32()
        self.flare_colors_count = reader.read_uint32()
        self.flare_colors_count2 = reader.read_uint32()
        self.offset_to_flare_textures = reader.read_uint32()
        self.flare_textures_count = reader.read_uint32()
        self.flare_colors_count2 = reader.read_uint32()
        self.flare_radius = reader.read_single()
        self.light_priority = reader.read_uint32()
        self.ambient_only = reader.read_uint32()
        self.dynamic_type = reader.read_uint32()
        self.affect_dynamic = reader.read_uint32()
        self.shadow = reader.read_uint32()
        self.flare = reader.read_uint32()
        self.fading_light = reader.read_uint32()
        return self

    def write(
        self,
        writer: BinaryWriter,
    ) -> None:
        writer.write_uint32(self.offset_to_unknown0)
        writer.write_uint32(self.unknown0_count)
        writer.write_uint32(self.unknown0_count2)
        writer.write_uint32(self.offset_to_flare_sizes)
        writer.write_uint32(self.flare_sizes_count)
        writer.write_uint32(self.flare_sizes_count2)
        writer.write_uint32(self.offset_to_flare_positions)
        writer.write_uint32(self.flare_positions_count)
        writer.write_uint32(self.flare_positions_count2)
        writer.write_uint32(self.offset_to_flare_colors)
        writer.write_uint32(self.flare_colors_count)
        writer.write_uint32(self.flare_colors_count2)
        writer.write_uint32(self.offset_to_flare_textures)
        writer.write_uint32(self.flare_textures_count)
        writer.write_uint32(self.flare_colors_count2)
        writer.write_single(self.flare_radius)
        writer.write_uint32(self.light_priority)
        writer.write_uint32(self.ambient_only)
        writer.write_uint32(self.dynamic_type)
        writer.write_uint32(self.affect_dynamic)
        writer.write_uint32(self.shadow)
        writer.write_uint32(self.flare)
        writer.write_uint32(self.fading_light)


class _EmitterHeader:
    def __init__(
        self,
    ):
        self.dead_space: float = 0.0
        self.blast_radius: float = 0.0
        self.blast_length: float = 0.0
        self.branch_count: int = 0
        self.smoothing: float = 0.0
        self.grid: Vector2 = Vector2.from_null()
        self.update: str = ""
        self.render: str = ""
        self.blend: str = ""
        self.texture: str = ""
        self.chunk_name: str = ""
        self.twosided_texture: int = 0
        self.loop: int = 0
        self.render_order: int = 0
        self.frame_blending: int = 0
        self.depth_texture: str = ""
        self.unknown0: int = 0
        self.flags: int = 0

    def read(
        self,
        reader: BinaryReader,
    ) -> _EmitterHeader:
        self.dead_space = reader.read_single()
        self.blast_radius = reader.read_single()
        self.blast_length = reader.read_single()
        self.branch_count = reader.read_uint32()
        self.smoothing = reader.read_single()
        self.grid = reader.read_vector2()
        self.update = reader.read_string(32)
        self.render = reader.read_string(32)
        self.blend = reader.read_string(32)
        self.texture = reader.read_string(32)
        self.chunk_name = reader.read_string(32)
        self.twosided_texture = reader.read_uint32()
        self.loop = reader.read_uint32()
        self.render_order = reader.read_uint32()
        self.frame_blending = reader.read_uint32()
        self.depth_texture = reader.read_string(32)
        self.unknown0 = reader.read_uint8()
        self.flags = reader.read_uint32()
        return self

    def write(
        self,
        writer: BinaryWriter,
    ) -> None:
        writer.write_single(self.dead_space)
        writer.write_single(self.blast_radius)
        writer.write_single(self.blast_length)
        writer.write_uint32(self.branch_count)
        writer.write_single(self.smoothing)
        writer.write_vector2(self.grid)
        writer.write_string(self.update, string_length=32)
        writer.write_string(self.render, string_length=32)
        writer.write_string(self.blend, string_length=32)
        writer.write_string(self.texture, string_length=32)
        writer.write_string(self.chunk_name, string_length=32)
        writer.write_uint32(self.twosided_texture)
        writer.write_uint32(self.loop)
        writer.write_uint32(self.render_order)
        writer.write_uint32(self.frame_blending)
        writer.write_string(self.depth_texture, string_length=32)
        writer.write_uint8(self.unknown0)
        writer.write_uint32(self.flags)


class _ReferenceHeader:
    def __init__(
        self,
    ):
        self.model: str = ""
        self.reattachable: int = 0

    def read(
        self,
        reader: BinaryReader,
    ) -> _ReferenceHeader:
        self.model = reader.read_string(32)
        self.reattachable = reader.read_uint32()
        return self

    def write(
        self,
        writer: BinaryWriter,
    ) -> None:
        writer.write_string(self.model, string_length=32)
        writer.write_uint32(self.reattachable)


class _Face:
    SIZE = 32

    def __init__(
        self,
    ):
        self.normal: Vector3 = Vector3.from_null()
        self.plane_coefficient: float = 0.0
        self.material: int = 0
        self.adjacent1: int = 0
        self.adjacent2: int = 0
        self.adjacent3: int = 0
        self.vertex1: int = 0
        self.vertex2: int = 0
        self.vertex3: int = 0

    def read(
        self,
        reader: BinaryReader,
    ) -> _Face:
        self.normal = reader.read_vector3()
        self.plane_coefficient = reader.read_single()
        self.material = reader.read_uint32()
        self.adjacent1 = reader.read_uint16()
        self.adjacent2 = reader.read_uint16()
        self.adjacent3 = reader.read_uint16()
        self.vertex1 = reader.read_uint16()
        self.vertex2 = reader.read_uint16()
        self.vertex3 = reader.read_uint16()
        return self

    def write(
        self,
        writer: BinaryWriter,
    ) -> None:
        writer.write_vector3(self.normal)
        writer.write_single(self.plane_coefficient)
        writer.write_uint32(self.material)
        writer.write_uint16(self.adjacent1)
        writer.write_uint16(self.adjacent2)
        writer.write_uint16(self.adjacent3)
        writer.write_uint16(self.vertex1)
        writer.write_uint16(self.vertex2)
        writer.write_uint16(self.vertex3)


class MDLBinaryReader:
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
        source_ext: SOURCE_TYPES | None = None,
        offset_ext: int = 0,
        size_ext: int = 0,
    ):
        self._mdl: MDL | None = None
        self._reader = BinaryReader.from_auto(source, offset)

        self._reader_ext = None if source_ext is None else BinaryReader.from_auto(source_ext, offset_ext)

        # first 12 bytes do not count in offsets used within the file
        self._reader.set_offset(self._reader.offset() + 12)

        self._names: list[str] = []

    def load(
        self,
        auto_close: bool = True,
    ) -> MDL:
        self._mdl = MDL()
        self._names = []

        model_header = _ModelHeader().read(self._reader)

        self._mdl.name = model_header.geometry.model_name
        self._mdl.supermodel = model_header.supermodel
        self._mdl.fog = model_header.fog

        self._load_names(model_header)
        self._mdl.root = self._load_node(model_header.geometry.root_node_offset)

        self._reader.seek(model_header.offset_to_animations)
        animation_offsets = [self._reader.read_uint32() for _i in range(model_header.animation_count)]
        for animation_offset in animation_offsets:
            anim = self._load_anim(animation_offset)
            self._mdl.anims.append(anim)

        if auto_close:
            self._reader.close()
        if auto_close and self._reader_ext is not None:
                self._reader_ext.close()

        return self._mdl

    def _load_names(
        self,
        model_header,
    ):
        self._reader.seek(model_header.offset_to_name_offsets)
        name_offsets = [self._reader.read_uint32() for _i in range(model_header.name_offsets_count)]
        for offset in name_offsets:
            self._reader.seek(offset)
            name = self._reader.read_terminated_string("\0")
            self._names.append(name)

    def _load_node(
        self,
        offset,
    ):
        self._reader.seek(offset)
        bin_node = _Node().read(self._reader)

        node = MDLNode()
        node.node_id = bin_node.header.node_id
        node.name = self._names[bin_node.header.name_id]
        node.position = bin_node.header.position
        node.orientation = bin_node.header.orientation

        if bin_node.trimesh:
            node.mesh = MDLMesh()
            node.mesh.shadow = bool(bin_node.trimesh.has_shadow)
            node.mesh.render = bool(bin_node.trimesh.render)
            node.mesh.background_geometry = bool(bin_node.trimesh.background)
            node.mesh.has_lightmap = bool(bin_node.trimesh.has_lightmap)
            node.mesh.beaming = bool(bin_node.trimesh.beaming)
            node.mesh.diffuse = Color.from_bgr_vector3(bin_node.trimesh.diffuse)
            node.mesh.ambient = Color.from_bgr_vector3(bin_node.trimesh.ambient)
            node.mesh.texture_1 = bin_node.trimesh.texture1
            node.mesh.texture_2 = bin_node.trimesh.texture2
            node.mesh.bb_min = bin_node.trimesh.bounding_box_min
            node.mesh.bb_max = bin_node.trimesh.bounding_box_max
            node.mesh.radius = bin_node.trimesh.radius
            node.mesh.average = bin_node.trimesh.average
            node.mesh.area = bin_node.trimesh.total_area
            node.mesh.saber_unknowns = bin_node.trimesh.saber_unknowns  # FIXME

            node.mesh.vertex_positions = bin_node.trimesh.vertices

            if bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.NORMAL and self._reader_ext:
                node.mesh.vertex_normals = []
            if bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.TEXTURE1 and self._reader_ext:
                node.mesh.vertex_uv1 = []
            if bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.TEXTURE2 and self._reader_ext:
                node.mesh.vertex_uv2 = []

            mdx_offset = bin_node.trimesh.mdx_data_offset
            mdx_block_size = bin_node.trimesh.mdx_data_size
            for i in range(len(bin_node.trimesh.vertices)):
                if bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.NORMAL and self._reader_ext:
                    self._reader_ext.seek(
                        mdx_offset
                        + i * mdx_block_size
                        + bin_node.trimesh.mdx_normal_offset,
                    )
                    x, y, z = (
                        self._reader_ext.read_single(),
                        self._reader_ext.read_single(),
                        self._reader_ext.read_single(),
                    )
                    node.mesh.vertex_normals.append(Vector3(x, y, z))
                if bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.TEXTURE1 and self._reader_ext:
                    self._reader_ext.seek(
                        mdx_offset
                        + i * mdx_block_size
                        + bin_node.trimesh.mdx_texture1_offset,
                    )
                    u, v = (
                        self._reader_ext.read_single(),
                        self._reader_ext.read_single(),
                    )
                    node.mesh.vertex_uv1.append(Vector2(u, v))
                if bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.TEXTURE2 and self._reader_ext:
                    self._reader_ext.seek(
                        mdx_offset
                        + i * mdx_block_size
                        + bin_node.trimesh.mdx_texture2_offset,
                    )
                    u, v = (
                        self._reader_ext.read_single(),
                        self._reader_ext.read_single(),
                    )
                    node.mesh.vertex_uv2.append(Vector2(u, v))

            for bin_face in bin_node.trimesh.faces:
                face = MDLFace()
                node.mesh.faces.append(face)
                face.v1 = bin_face.vertex1
                face.v2 = bin_face.vertex2
                face.v3 = bin_face.vertex3
                face.a1 = bin_face.adjacent1
                face.a2 = bin_face.adjacent2
                face.a3 = bin_face.adjacent3
                face.normal = bin_face.normal
                face.coefficient = int(bin_face.plane_coefficient)
                face.material = SurfaceMaterial(bin_face.material)

        if bin_node.skin:
            node.skin = MDLSkin()
            node.skin.bone_indices = bin_node.skin.bones
            node.skin.bonemap = bin_node.skin.bonemap
            node.skin.tbones = bin_node.skin.tbones
            node.skin.qbones = bin_node.skin.qbones

            if self._reader_ext:
                for i in range(len(bin_node.trimesh.vertices)):
                    vertex_bone = MDLBoneVertex()
                    node.skin.vertex_bones.append(vertex_bone)

                    mdx_offset = bin_node.trimesh.mdx_data_offset + i * bin_node.trimesh.mdx_data_size
                    self._reader_ext.seek(
                        mdx_offset + bin_node.skin.offset_to_mdx_bones,
                    )
                    t1 = self._reader_ext.read_single()
                    t2 = self._reader_ext.read_single()
                    t3 = self._reader_ext.read_single()
                    t4 = self._reader_ext.read_single()
                    vertex_bone.vertex_indices = (t1, t2, t3, t4)

                    mdx_offset = bin_node.trimesh.mdx_data_offset + i * bin_node.trimesh.mdx_data_size
                    self._reader_ext.seek(
                        mdx_offset + bin_node.skin.offset_to_mdx_weights,
                    )
                    w1 = self._reader_ext.read_single()
                    w2 = self._reader_ext.read_single()
                    w3 = self._reader_ext.read_single()
                    w4 = self._reader_ext.read_single()
                    vertex_bone.vertex_weights = (w1, w2, w3, w4)

        for child_offset in bin_node.children_offsets:
            child_node = self._load_node(child_offset)
            node.children.append(child_node)

        for i in range(bin_node.header.controller_count):
            offset = bin_node.header.offset_to_controllers + i * _Controller.SIZE
            controller = self._load_controller(
                offset,
                bin_node.header.offset_to_controller_data,
            )
            node.controllers.append(controller)

        return node

    def _load_anim(
        self,
        offset,
    ):
        self._reader.seek(offset)

        bin_anim = _AnimationHeader().read(self._reader)

        bin_events = []
        self._reader.seek(bin_anim.offset_to_events)
        for _i in range(bin_anim.event_count):
            bin_event = _EventStructure().read(self._reader)
            bin_events.append(bin_event)

        anim = MDLAnimation()

        anim.name = bin_anim.geometry.model_name
        anim.root_model = bin_anim.root
        anim.anim_length = bin_anim.duration
        anim.transition_length = bin_anim.transition

        for bin_event in bin_events:
            event = MDLEvent()
            event.name = bin_event.event_name
            event.activation_time = bin_event.activation_time
            anim.events.append(event)

        anim.root = self._load_node(bin_anim.geometry.root_node_offset)

        return anim

    def _load_controller(
        self,
        offset,
        data_offset,
    ):
        self._reader.seek(offset)
        bin_controller = _Controller().read(self._reader)

        row_count = bin_controller.row_count
        column_count = bin_controller.column_count

        self._reader.seek(data_offset + bin_controller.key_offset)
        time_keys = [self._reader.read_single() for i in range(row_count)]

        # There are some special cases when reading controller data rows.

        # Orientation data stored in controllers is sometimes compressed into 4 bytes. We need to check for that and
        # uncompress the quaternion if that is the case.
        if bin_controller.type_id == MDLControllerType.ORIENTATION and bin_controller.column_count == 2:
            data = []
            for _i in range(bin_controller.row_count):
                compressed = self._reader.read_uint32()
                decompressed = Vector4.from_compressed(compressed)
                data.append(
                    [decompressed.x, decompressed.y, decompressed.z, decompressed.w],
                )
        else:
            self._reader.seek(data_offset + bin_controller.data_offset * 4)
            data = [[self._reader.read_single() for j in range(column_count)] for i in range(row_count)]

        controller = MDLController()
        controller.controller_type = bin_controller.type_id
        controller.rows = [MDLControllerRow(time_keys[i], data[i]) for i in range(row_count)]
        return controller


class MDLBinaryWriter:
    def __init__(
        self,
        mdl: MDL,
        target: TARGET_TYPES,
        target_ext: TARGET_TYPES,
    ):
        self._mdl = mdl

        self._target = target
        self._target_ext = target_ext
        self._writer = BinaryWriter.to_bytearray()
        self._writer_ext = BinaryWriter.to_bytearray()

        self.game: Game = Game.K1

        self._name_offsets: list[int] = []
        self._anim_offsets: list[int] = []
        self._node_offsets: list[int] = []

        self._bin_anim_nodes: dict[str, _Node] = {}
        self._mdl_nodes: list[MDLNode] = []
        self._bin_nodes: list[_Node] = []
        self._bin_anims: list[_Animation] = []
        self._names: list[str] = []
        self._file_header: _ModelHeader = _ModelHeader()

    def write(
        self,
        auto_close: bool = True,
    ) -> None:
        self._mdl_nodes = self._mdl.all_nodes()
        self._bin_nodes = [_Node() for node in self._mdl_nodes]
        self._bin_anims = [_Animation() for anim in self._mdl.anims]
        self._names = [node.name for node in self._mdl_nodes]

        self._anim_offsets = [0 for _ in self._bin_anims]
        self._node_offsets = [0 for _ in self._bin_nodes]
        self._file_header = _ModelHeader()

        self._update_all_data()

        self._calc_top_offsets()
        self._calc_inner_offsets()

        self._write_all()

        if auto_close:
            self._writer.close()
            if self._writer_ext:
                self._writer_ext.close()

    def _update_all_data(
        self,
    ):
        for i, bin_node in enumerate(self._bin_nodes):
            self._update_node(bin_node, self._mdl_nodes[i])

        for i, bin_anim in enumerate(self._bin_anims):
            self._update_anim(bin_anim, self._mdl.anims[i])

    def _update_node(
        self,
        bin_node: _Node,
        mdl_node: MDLNode,
    ):
        bin_node.header.type_id = self._node_type(mdl_node)
        bin_node.header.position = mdl_node.position
        bin_node.header.orientation = mdl_node.orientation
        bin_node.header.children_count = bin_node.header.children_count2 = len(
            mdl_node.children,
        )
        bin_node.header.name_id = self._names.index(mdl_node.name)
        bin_node.header.node_id = self._get_node_id(bin_node)

        # Determine the appropriate function pointer values to write
        if self.game == Game.K1:
            if mdl_node.skin:
                fp0 = _TrimeshHeader.K1_SKIN_FUNCTION_POINTER0
                fp1 = _TrimeshHeader.K1_SKIN_FUNCTION_POINTER1
            elif mdl_node.dangly:
                fp0 = _TrimeshHeader.K1_DANGLY_FUNCTION_POINTER0
                fp1 = _TrimeshHeader.K1_DANGLY_FUNCTION_POINTER1
            else:
                fp0 = _TrimeshHeader.K1_FUNCTION_POINTER0
                fp1 = _TrimeshHeader.K1_FUNCTION_POINTER1
        elif mdl_node.skin:
            fp0 = _TrimeshHeader.K2_SKIN_FUNCTION_POINTER0
            fp1 = _TrimeshHeader.K2_SKIN_FUNCTION_POINTER1
        elif mdl_node.dangly:
            fp0 = _TrimeshHeader.K2_DANGLY_FUNCTION_POINTER0
            fp1 = _TrimeshHeader.K2_DANGLY_FUNCTION_POINTER1
        else:
            fp0 = _TrimeshHeader.K2_FUNCTION_POINTER0
            fp1 = _TrimeshHeader.K2_FUNCTION_POINTER1

        if mdl_node.mesh:
            bin_node.trimesh = _TrimeshHeader()
            bin_node.trimesh.function_pointer0 = fp0
            bin_node.trimesh.function_pointer1 = fp1
            bin_node.trimesh.average = mdl_node.mesh.average
            bin_node.trimesh.radius = mdl_node.mesh.radius
            bin_node.trimesh.bounding_box_max = mdl_node.mesh.bb_max
            bin_node.trimesh.bounding_box_min = mdl_node.mesh.bb_min
            bin_node.trimesh.total_area = mdl_node.mesh.area
            bin_node.trimesh.texture1 = mdl_node.mesh.texture_1
            bin_node.trimesh.texture2 = mdl_node.mesh.texture_2
            bin_node.trimesh.diffuse = mdl_node.mesh.diffuse.bgr_vector3()
            bin_node.trimesh.ambient = mdl_node.mesh.ambient.bgr_vector3()
            bin_node.trimesh.render = mdl_node.mesh.render
            bin_node.trimesh.transparency_hint = mdl_node.mesh.transparency_hint
            bin_node.trimesh.uv_jitter = mdl_node.mesh.uv_jitter
            bin_node.trimesh.uv_speed = mdl_node.mesh.uv_jitter_speed
            bin_node.trimesh.uv_direction.x = mdl_node.mesh.uv_direction_x
            bin_node.trimesh.uv_direction.y = mdl_node.mesh.uv_direction_y
            bin_node.trimesh.has_lightmap = mdl_node.mesh.has_lightmap
            bin_node.trimesh.rotate_texture = mdl_node.mesh.rotate_texture
            bin_node.trimesh.background = mdl_node.mesh.background_geometry
            bin_node.trimesh.has_shadow = mdl_node.mesh.shadow
            bin_node.trimesh.beaming = mdl_node.mesh.beaming
            bin_node.trimesh.render = mdl_node.mesh.render
            bin_node.trimesh.dirt_enabled = mdl_node.mesh.dirt_enabled  # TODO: undefined??
            bin_node.trimesh.dirt_texture = mdl_node.mesh.dirt_texture  # TODO: undefined??
            bin_node.trimesh.saber_unknowns = mdl_node.mesh.saber_unknowns  # TODO: wrong type??

            bin_node.trimesh.vertex_count = len(mdl_node.mesh.vertex_positions)
            bin_node.trimesh.vertices = mdl_node.mesh.vertex_positions

            bin_node.trimesh.indices_counts = [len(mdl_node.mesh.faces) * 3]
            bin_node.trimesh.indices_counts_count = bin_node.trimesh.indices_counts_count2 = 1

            bin_node.trimesh.indices_offsets = [
                0,
            ]  # Placeholder to be updated with offsets - do not remove line
            bin_node.trimesh.indices_offsets_count = bin_node.trimesh.indices_offsets_count2 = 1

            bin_node.trimesh.inverted_counters = [0]
            bin_node.trimesh.counters_count = bin_node.trimesh.counters_count2 = 1

            bin_node.trimesh.faces_count = bin_node.trimesh.faces_count2 = len(
                mdl_node.mesh.faces,
            )
            for face in mdl_node.mesh.faces:
                bin_face = _Face()
                bin_node.trimesh.faces.append(bin_face)
                bin_face.vertex1 = face.v1
                bin_face.vertex2 = face.v2
                bin_face.vertex3 = face.v3
                bin_face.adjacent1 = face.a1
                bin_face.adjacent2 = face.a2
                bin_face.adjacent3 = face.a3
                bin_face.material = face.material.value
                bin_face.plane_coefficient = face.coefficient
                bin_face.normal = face.normal

        data_offset = 0
        key_offset = 0
        for mdl_controller in mdl_node.controllers:
            bin_controller = _Controller()
            bin_controller.type_id = mdl_controller.controller_type
            bin_controller.row_count = len(mdl_controller.rows)
            bin_controller.column_count = len(mdl_controller.rows[0].data)
            bin_controller.key_offset = key_offset
            data_offset += len(mdl_controller.rows)
            bin_controller.data_offset = data_offset
            bin_node.w_controllers.append(bin_controller)
            data_offset += len(mdl_controller.rows) * len(mdl_controller.rows[0].data)
            key_offset += data_offset

        bin_node.w_controller_data = []
        for controller in mdl_node.controllers:
            for row in controller.rows:
                bin_node.w_controller_data.append(row.time)
            for row in controller.rows:
                bin_node.w_controller_data.extend(row.data)

        bin_node.header.controller_count = bin_node.header.controller_count2 = len(
            mdl_node.controllers,
        )
        bin_node.header.controller_data_length = bin_node.header.controller_data_length2 = len(bin_node.w_controller_data)

    def _update_anim(
        self,
        bin_anim: _Animation,
        mdl_anim: MDLAnimation,
    ):
        if self.game == Game.K1:
            bin_anim.header.geometry.function_pointer0 = _GeometryHeader.K1_ANIM_FUNCTION_POINTER0
            bin_anim.header.geometry.function_pointer1 = _GeometryHeader.K1_ANIM_FUNCTION_POINTER1
        else:
            bin_anim.header.geometry.function_pointer0 = _GeometryHeader.K2_ANIM_FUNCTION_POINTER0
            bin_anim.header.geometry.function_pointer1 = _GeometryHeader.K2_ANIM_FUNCTION_POINTER1

        bin_anim.header.geometry.geometry_type = 5
        bin_anim.header.geometry.model_name = mdl_anim.name
        bin_anim.header.geometry.node_count = 0
        bin_anim.header.duration = mdl_anim.anim_length
        bin_anim.header.transition = mdl_anim.transition_length
        bin_anim.header.root = mdl_anim.root_model
        bin_anim.header.event_count = bin_anim.header.event_count2 = len(
            mdl_anim.events,
        )

        for mdl_event in mdl_anim.events:
            bin_event = _EventStructure()
            bin_event.event_name = mdl_event.name
            bin_event.activation_time = mdl_event.activation_time
            bin_anim.events.append(bin_event)

        all_nodes = mdl_anim.all_nodes()
        bin_nodes = []
        for mdl_node in all_nodes:
            bin_node = _Node()
            self._update_node(bin_node, mdl_node)
            bin_nodes.append(bin_node)
        bin_anim.w_nodes = bin_nodes

    def _update_mdx(
        self,
        bin_node: _Node,
        mdl_node: MDLNode,
    ):
        bin_node.trimesh.mdx_data_offset = self._writer_ext.size()

        bin_node.trimesh.mdx_vertex_offset = 0xFFFFFFFF
        bin_node.trimesh.mdx_normal_offset = 0xFFFFFFFF
        bin_node.trimesh.mdx_texture1_offset = 0xFFFFFFFF
        bin_node.trimesh.mdx_texture2_offset = 0xFFFFFFFF
        bin_node.trimesh.mdx_data_bitmap = 0

        suboffset = 0

        if mdl_node.mesh.vertex_positions:
            bin_node.trimesh.mdx_vertex_offset = suboffset
            bin_node.trimesh.mdx_data_bitmap |= _MDXDataFlags.VERTEX
            suboffset += 12

        if mdl_node.mesh.vertex_normals:
            bin_node.trimesh.mdx_normal_offset = suboffset
            bin_node.trimesh.mdx_data_bitmap |= _MDXDataFlags.NORMAL
            suboffset += 12

        if mdl_node.mesh.vertex_uv1:
            bin_node.trimesh.mdx_texture1_offset = suboffset
            bin_node.trimesh.mdx_data_bitmap |= _MDXDataFlags.TEXTURE1
            suboffset += 8

        if mdl_node.mesh.vertex_uv2:
            bin_node.trimesh.mdx_texture2_offset = suboffset
            bin_node.trimesh.mdx_data_bitmap |= _MDXDataFlags.TEXTURE2
            suboffset += 8

        bin_node.trimesh.mdx_data_size = suboffset

        for i, position in enumerate(mdl_node.mesh.vertex_positions):
            if mdl_node.mesh.vertex_positions:
                self._writer_ext.write_vector3(position)
            if mdl_node.mesh.vertex_normals:
                self._writer_ext.write_vector3(mdl_node.mesh.vertex_normals[i])
            if mdl_node.mesh.vertex_uv1:
                self._writer_ext.write_vector2(mdl_node.mesh.vertex_uv1[i])
            if mdl_node.mesh.vertex_uv2:
                self._writer_ext.write_vector2(mdl_node.mesh.vertex_uv2[i])

        # Why does the mdl/mdx format have this? I have no idea.
        if mdl_node.mesh.vertex_positions:
            self._writer_ext.write_vector3(Vector3(10000000, 10000000, 10000000))
        if mdl_node.mesh.vertex_normals:
            self._writer_ext.write_vector3(Vector3.from_null())
        if mdl_node.mesh.vertex_uv1:
            self._writer_ext.write_vector2(Vector2.from_null())
        if mdl_node.mesh.vertex_uv2:
            self._writer_ext.write_vector2(Vector2.from_null())

    def _calc_top_offsets(
        self,
    ):
        offset_to_name_offsets = _ModelHeader.SIZE

        offset_to_names = offset_to_name_offsets + 4 * len(self._names)
        name_offset = offset_to_names
        for name in self._names:
            self._name_offsets.append(name_offset)
            name_offset += len(name) + 1

        offset_to_anim_offsets = name_offset
        offset_to_anims = name_offset + (4 * len(self._bin_anims))
        anim_offset = offset_to_anims
        for i, anim in enumerate(self._bin_anims):
            self._anim_offsets[i] = anim_offset
            anim_offset += anim.size()

        offset_to_node_offset = anim_offset
        node_offset = offset_to_node_offset
        for i, bin_node in enumerate(self._bin_nodes):
            self._node_offsets[i] = node_offset
            node_offset += bin_node.calc_size(self.game)

        self._file_header.geometry.root_node_offset = offset_to_node_offset
        self._file_header.offset_to_name_offsets = offset_to_name_offsets
        self._file_header.offset_to_super_root = 0
        self._file_header.offset_to_animations = offset_to_anim_offsets

    def _calc_inner_offsets(
        self,
    ):
        for i, bin_anim in enumerate(self._bin_anims):
            bin_anim.header.offset_to_events = self._anim_offsets[i] + bin_anim.events_offset()
            bin_anim.header.geometry.root_node_offset = self._anim_offsets[i] + bin_anim.nodes_offset()

            node_offsets = []
            node_offset = self._anim_offsets[i] + bin_anim.nodes_offset()
            for bin_node in bin_anim.w_nodes:
                node_offsets.append(node_offset)
                node_offset += bin_node.calc_size(self.game)

            for j, _bin_node in enumerate(bin_anim.w_nodes):
                self._calc_node_offset(j, bin_anim.w_nodes, node_offsets)

        for i, _bin_node in enumerate(self._bin_nodes):
            self._calc_node_offset(i, self._bin_nodes, self._node_offsets)

    def _calc_node_offset(
        self,
        index: int,
        bin_nodes: list[_Node],
        bin_offsets: list[int],
    ):
        bin_node = bin_nodes[index]
        node_offset = bin_offsets[index]

        for bin_child in self._get_bin_children(bin_node, bin_nodes):
            child_index = bin_nodes.index(bin_child)
            offset = bin_offsets[child_index]
            bin_node.children_offsets.append(offset)

        bin_node.header.offset_to_children = node_offset + bin_node.children_offsets_offset(self.game)
        bin_node.header.offset_to_controllers = node_offset + bin_node.controllers_offset(self.game)
        bin_node.header.offset_to_controller_data = node_offset + bin_node.controller_data_offset(self.game)
        bin_node.header.offset_to_root = 0
        bin_node.header.offset_to_parent = self._node_offsets[0] if index != 0 else 0

        if bin_node.trimesh:
            bin_node.trimesh.offset_to_counters = node_offset + bin_node.inverted_counters_offset(self.game)
            bin_node.trimesh.offset_to_indices_counts = node_offset + bin_node.indices_counts_offset(self.game)
            bin_node.trimesh.offset_to_indices_offset = node_offset + bin_node.indices_offsets_offset(self.game)
            bin_node.trimesh.indices_offsets = [
                node_offset + bin_node.indices_offset(self.game),
            ]

            bin_node.trimesh.offset_to_faces = node_offset + bin_node.faces_offset(
                self.game,
            )
            bin_node.trimesh.vertices_offset = node_offset + bin_node.vertices_offset(
                self.game,
            )

    def _get_node_id(
        self,
        bin_node: _Node,
    ) -> int:
        name_index = bin_node.header.name_id
        for mdl_node in self._mdl_nodes:
            if self._names.index(mdl_node.name) == name_index:
                return self._mdl_nodes.index(mdl_node)
        raise ValueError

    def _get_bin_children(
        self,
        bin_node: _Node,
        all_nodes: list[_Node],
    ) -> list[_Node]:
        # check the name_id for bin_node
        # get the corresponding mdl_node
        # find name_ids of all children
        # from all_nodes list pick the nodes with the same name_ids
        name_id = bin_node.header.name_id
        mdl_node = None
        for mdlnode in self._mdl_nodes:
            if self._names.index(mdlnode.name) == name_id:
                mdl_node = mdlnode
        if mdl_node is None:
            raise ValueError

        child_name_ids = []
        for mdlnode in mdl_node.children:
            child_name_id = self._names.index(mdlnode.name)
            child_name_ids.append(child_name_id)

        bin_children = []
        for child_name_id in child_name_ids:
            bin_children.extend(binnode for binnode in all_nodes if binnode.header.name_id == child_name_id)
        return bin_children

    def _node_type(
        self,
        node: MDLNode,
    ) -> int:
        type_id = 1
        if node.mesh: type_id = type_id | MDLNodeFlags.MESH
        # if node.skin: type_id = type_id | MDLNodeFlags.SKIN
        # if node.dangly: type_id = type_id | MDLNodeFlags.DANGLY
        # if node.saber: type_id = type_id | MDLNodeFlags.SABER
        # if node.aabb: type_id = type_id | MDLNodeFlags.AABB
        # if node.emitter: type_id = type_id | MDLNodeFlags.EMITTER
        # if node.light: type_id = type_id | MDLNodeFlags.LIGHT
        # if node.reference: type_id = type_id | MDLNodeFlags.REFERENCE
        return type_id

    def _write_all(
        self,
    ):
        for i, bin_node in enumerate(self._bin_nodes):
            if bin_node.trimesh:
                self._update_mdx(bin_node, self._mdl_nodes[i])

        self._file_header.geometry.function_pointer0 = _GeometryHeader.K1_FUNCTION_POINTER0
        self._file_header.geometry.function_pointer1 = _GeometryHeader.K1_FUNCTION_POINTER1
        self._file_header.geometry.model_name = self._mdl.name
        self._file_header.geometry.node_count = len(
            self._mdl_nodes,
        )  # TODO: need to include supermodel in count
        self._file_header.geometry.geometry_type = 2
        self._file_header.offset_to_super_root = self._file_header.geometry.root_node_offset
        self._file_header.mdx_size = self._writer_ext.size()

        # TODO self._file_header.model_type = 0
        # TODO self._file_header.fog = 0
        self._file_header.animation_count = self._file_header.animation_count2 = len(
            self._mdl.anims,
        )
        # TODO self._file_header.bounding_box_min
        # TODO self._file_header.bounding_box_max
        # TODO self._file_header.radius
        # TODO self._file_header.anim_scale
        self._file_header.supermodel = self._mdl.supermodel
        # TODO self._file_header.mdx_size
        # TODO self._file_header.mdx_offset
        self._file_header.name_offsets_count = self._file_header.name_offsets_count2 = len(self._names)

        self._file_header.write(self._writer)

        for name_offset in self._name_offsets:
            self._writer.write_uint32(name_offset)

        for name in self._names:
            self._writer.write_string(name + "\0")

        for anim_offset in self._anim_offsets:
            self._writer.write_uint32(anim_offset)

        for bin_anim in self._bin_anims:
            bin_anim.write(self._writer, self.game)
        for bin_node in self._bin_nodes:
            bin_node.write(self._writer, self.game)

        # Write to MDL
        mdl_writer = BinaryWriter.to_auto(self._target)
        mdl_writer.write_uint32(0)
        mdl_writer.write_uint32(self._writer.size())
        mdl_writer.write_uint32(self._writer_ext.size())
        mdl_writer.write_bytes(self._writer.data())

        # Write to MDX
        if self._target_ext is not None:
            BinaryWriter.to_auto(self._target_ext).write_bytes(self._writer_ext.data())
