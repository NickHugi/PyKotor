import struct
from copy import deepcopy
from typing import Dict, List

from pykotor.common.geometry import Vector3, Vector4
from pykotor.common.misc import Game
from pykotor.common.stream import BinaryReader

_GEOM_ROOT_FP0_K1 = 4273776
_GEOM_ROOT_FP1_K1 = 4216096
_GEOM_ROOT_FP0_K2 = 4285200
_GEOM_ROOT_FP1_K2 = 4216320

_GEOM_ANIM_FP0_K1 = 4273392
_GEOM_ANIM_FP1_K1 = 4451552
_GEOM_ANIM_FP0_K2 = 4284816
_GEOM_ANIM_FP1_K2 = 4522928

_NODE_TYPE_MESH = 32
_MESH_HEADER_SIZE_K1 = 332
_MESH_HEADER_SIZE_K2 = 340
_MESH_FP0_K1 = 4216656
_MESH_FP1_K1 = 4216672
_MESH_FP0_K2 = 4216880
_MESH_FP1_K2 = 4216896

_NODE_TYPE_SKIN = 64
_SKIN_HEADER_SIZE = 108
_SKIN_FP0_K1 = 4216592
_SKIN_FP1_K1 = 4216608
_SKIN_FP0_K2 = 4216816
_SKIN_FP1_K2 = 4216832

_NODE_TYPE_DANGLY = 256
_DANGLY_HEADER_SIZE = 28
_DANGLY_FP0_K1 = 4216640
_DANGLY_FP1_K1 = 4216624
_DANGLY_FP0_K2 = 4216864
_DANGLY_FP1_K2 = 4216848

_NODE_TYPE_SABER = 2048
_SABER_HEADER_SIZE = 20
_SABER_FP0_K1 = 4216656
_SABER_FP1_K1 = 4216672
_SABER_FP0_K2 = 4216880
_SABER_FP1_K2 = 4216896

_NODE_TYPE_AABB = 512
_AABB_HEADER_SIZE = 4
_AABB_FP0_K1 = 4216656
_AABB_FP1_K1 = 4216672
_AABB_FP0_K2 = 4216880
_AABB_FP1_K2 = 4216896

_NODE_TYPE_LIGHT = 2
_LIGHT_HEADER_SIZE = 92

_NODE_TYPE_EMITTER = 4
_EMITTER_HEADER_SIZE = 224


def rename(
        data: bytes,
        name: str
) -> bytes:
    return data[:20] + name.ljust(32, '\0').encode('ascii') + data[52:]


def list_textures(
        data: bytes
) -> List[str]:
    textures = []

    with BinaryReader.from_bytes(data, 12) as reader:
        reader.seek(168)
        root_offset = reader.read_uint32()

        offsets = {}
        nodes = [root_offset]
        while nodes:
            node_offset = nodes.pop()
            reader.seek(node_offset)
            node_id = reader.read_uint32()

            reader.seek(node_offset + 44)
            child_offsets_offset = reader.read_uint32()
            child_offsets_count = reader.read_uint32()

            reader.seek(child_offsets_offset)
            for i in range(child_offsets_count):
                nodes.append(reader.read_uint32())

            if node_id & 32:
                reader.seek(node_offset + 168)
                texture = reader.read_string(32)
                if texture != "" and texture != "NULL":
                    textures.append(texture.lower())

    return textures


def list_lightmaps(
        data: bytes
) -> List[str]:
    lightmaps = []

    with BinaryReader.from_bytes(data, 12) as reader:
        reader.seek(168)
        root_offset = reader.read_uint32()

        offsets = {}
        nodes = [root_offset]
        while nodes:
            node_offset = nodes.pop()
            reader.seek(node_offset)
            node_id = reader.read_uint32()

            reader.seek(node_offset + 44)
            child_offsets_offset = reader.read_uint32()
            child_offsets_count = reader.read_uint32()

            reader.seek(child_offsets_offset)
            for i in range(child_offsets_count):
                nodes.append(reader.read_uint32())

            if node_id & 32:
                reader.seek(node_offset + 200)
                lightmap = reader.read_string(32)
                if lightmap != "" and lightmap != "NULL":
                    lightmaps.append(lightmap.lower())

    return lightmaps


def change_textures(
        data: bytes,
        textures: Dict[str, str]
) -> bytes:
    data = bytearray(data)
    offsets = {}

    textures_ins = {}
    for old_texture, new_texture in textures.items():
        textures_ins[old_texture.lower()] = new_texture.lower()
    textures = textures_ins

    with BinaryReader.from_bytes(data, 12) as reader:
        reader.seek(168)
        root_offset = reader.read_uint32()

        nodes = [root_offset]
        while nodes:
            node_offset = nodes.pop()
            reader.seek(node_offset)
            node_id = reader.read_uint32()

            reader.seek(node_offset + 44)
            child_offsets_offset = reader.read_uint32()
            child_offsets_count = reader.read_uint32()

            reader.seek(child_offsets_offset)
            for i in range(child_offsets_count):
                nodes.append(reader.read_uint32())

            if node_id & 32:
                reader.seek(node_offset + 168)
                texture = reader.read_string(32).lower()

                if texture in textures:
                    if texture in offsets:
                        offsets[texture].append(node_offset + 168)
                    else:
                        offsets[texture] = [node_offset + 168]

        for texture, offsets in offsets.items():
            for offset in offsets:
                offset += 12
                data = data[:offset] + struct.pack('32s', textures[texture].ljust(32, '\0').encode('ascii')) + data[
                                                                                                               offset + 32:]

    return bytes(data)


def change_lightmaps(
        data: bytes,
        textures: Dict[str, str]
) -> bytes:
    data = bytearray(data)
    offsets = {}

    textures_ins = {}
    for old_texture, new_texture in textures.items():
        textures_ins[old_texture.lower()] = new_texture.lower()
    textures = textures_ins

    with BinaryReader.from_bytes(data, 12) as reader:
        reader.seek(168)
        root_offset = reader.read_uint32()

        nodes = [root_offset]
        while nodes:
            node_offset = nodes.pop()
            reader.seek(node_offset)
            node_id = reader.read_uint32()

            reader.seek(node_offset + 44)
            child_offsets_offset = reader.read_uint32()
            child_offsets_count = reader.read_uint32()

            reader.seek(child_offsets_offset)
            for i in range(child_offsets_count):
                nodes.append(reader.read_uint32())

            if node_id & 32:
                reader.seek(node_offset + 200)
                texture = reader.read_string(32).lower()

                if texture in textures:
                    if texture in offsets:
                        offsets[texture].append(node_offset + 200)
                    else:
                        offsets[texture] = [node_offset + 200]

        for texture, offsets in offsets.items():
            for offset in offsets:
                offset += 12
                data = data[:offset] + struct.pack('32s', textures[texture].ljust(32, '\0').encode('ascii')) + data[
                                                                                                               offset + 32:]

    return bytes(data)


def detect_version(
        data: bytes
) -> Game:
    pointer = struct.unpack("I", data[12:16])[0]
    return Game.K1 if pointer == _GEOM_ROOT_FP0_K1 else Game.K2


def convert_to_k1(
        data: bytes
) -> bytes:
    if detect_version(data) == Game.K1:
        return data

    trim = []

    with BinaryReader.from_bytes(data, 12) as reader:
        reader.seek(168)
        root_offset = reader.read_uint32()

        nodes = [root_offset]
        while nodes:
            node_offset = nodes.pop()
            reader.seek(node_offset)
            node_type = reader.read_uint16()

            if node_type & 32:
                trim.append((node_type, node_offset))

            reader.seek(node_offset + 44)
            child_offsets_offset = reader.read_uint32()
            child_offsets_count = reader.read_uint32()

            reader.seek(child_offsets_offset)
            for i in range(child_offsets_count):
                nodes.append(reader.read_uint32())

    start = data[:12]
    data = bytearray(data[12:])

    data[0:4] = struct.pack("I", _GEOM_ROOT_FP0_K1)
    data[4:8] = struct.pack("I", _GEOM_ROOT_FP1_K1)

    # TODO Animations

    for node_type, node_offset in trim:
        mesh_start = node_offset + 80  # Start of mesh header

        offset_start = node_offset + 80 + 332  # Location of start of bytes to be shifted
        offset_size = 8  # How many bytes we have to shift

        if node_type & _NODE_TYPE_SKIN:
            offset_size += _SKIN_HEADER_SIZE
            data[mesh_start:mesh_start + 4] = struct.pack("I", _MESH_FP0_K1)
            data[mesh_start + 4:mesh_start + 8] = struct.pack("I", _MESH_FP1_K1)

        if node_type & _NODE_TYPE_DANGLY:
            offset_size += _DANGLY_HEADER_SIZE
            data[mesh_start:mesh_start + 4] = struct.pack("I", _DANGLY_FP0_K1)
            data[mesh_start + 4:mesh_start + 8] = struct.pack("I", _DANGLY_FP1_K1)

        if node_type & _NODE_TYPE_SABER:
            offset_size += _SABER_HEADER_SIZE
            data[mesh_start:mesh_start + 4] = struct.pack("I", _SABER_FP0_K1)
            data[mesh_start + 4:mesh_start + 8] = struct.pack("I", _SABER_FP1_K1)

        if node_type & _NODE_TYPE_AABB:
            offset_size += _AABB_HEADER_SIZE
            data[mesh_start:mesh_start + 4] = struct.pack("I", _AABB_FP0_K1)
            data[mesh_start + 4:mesh_start + 8] = struct.pack("I", _AABB_FP1_K1)

        shifting = data[offset_start:offset_start + offset_size]
        data[offset_start - 8:offset_start - 8 + offset_size] = shifting

    return bytes(start + data)


def convert_to_k2(
        data: bytes
) -> bytes:
    if detect_version(data) == Game.K2:
        return data

    offsets = {}  # Maps the offset for an offset to its offset
    mesh_offsets = []  # Tuple of (Offset to every mesh node, Node type)
    anim_offsets = []

    # First, we build a dictionary of every offset in the file plus a list of the mesh nodes
    with BinaryReader.from_bytes(data, 12) as reader:
        def node_recursive(
                offset_to_root_offset
        ):
            nodes = [offset_to_root_offset]
            while nodes:
                offset_to_node_offset = nodes.pop()
                reader.seek(offset_to_node_offset)
                node_offset = reader.read_uint32()
                offsets[
                    offset_to_node_offset] = node_offset  # Geometry header/Node children offsets array -> Node offset

                reader.seek(node_offset)
                node_type = reader.read_uint16()

                base_offset = node_offset + 80
                if node_type & _NODE_TYPE_MESH:
                    mesh_offsets.append([node_offset, node_type])

                    reader.seek(base_offset + 8)
                    offsets[base_offset + 8] = reader.read_uint32()  # Node header -> Face array offset

                    reader.seek(base_offset + 176)
                    offsets[base_offset + 176] = reader.read_uint32()  # Node header -> Vertex indices count array
                    indicies_array_count = reader.read_uint32()

                    reader.seek(base_offset + 188)
                    offsets[base_offset + 188] = reader.read_uint32()  # Node header -> Vertex indices locations array
                    if indicies_array_count == 1:
                        indices_locations_offset = offsets[base_offset + 188]
                        reader.seek(indices_locations_offset)
                        offsets[
                            indices_locations_offset] = reader.read_uint32()  # Vertex indices locations array -> Vertex indices array

                    reader.seek(base_offset + 200)
                    offsets[base_offset + 200] = reader.read_uint32()  # Node header -> Inverted counter array

                    reader.seek(base_offset + 328)
                    offsets[base_offset + 328] = reader.read_uint32()  # Node header -> Vertex array

                    base_offset += _MESH_HEADER_SIZE_K1

                if node_type & _NODE_TYPE_LIGHT:
                    reader.seek(base_offset + 4)
                    offsets[base_offset + 4] = reader.read_uint32()  # Node header -> Lens flare size array

                    reader.seek(base_offset + 16)
                    offsets[base_offset + 16] = reader.read_uint32()  # Node header -> Lens flare size array

                    reader.seek(base_offset + 28)
                    offsets[base_offset + 28] = reader.read_uint32()  # Node header -> Lens flare positions array

                    reader.seek(base_offset + 40)
                    offsets[base_offset + 40] = reader.read_uint32()  # Node header -> Flare colour shifts array

                    reader.seek(base_offset + 52)
                    offsets[base_offset + 52] = reader.read_uint32()  # Node header -> Flare texture names offsets array
                    texture_count = reader.read_uint32()

                    for i in range(texture_count):
                        reader.seek(offsets[base_offset + 52] + i * 4)
                        offsets[offsets[base_offset + 52] + i * 4] = reader.read_uint32()

                if node_type & _NODE_TYPE_EMITTER:
                    ...  # No offsets. Hooray.

                if node_type & _NODE_TYPE_SKIN:
                    reader.seek(base_offset + 20)
                    offsets[base_offset + 20] = reader.read_uint32()  # Node header -> Bone map array

                    reader.seek(base_offset + 28)
                    offsets[base_offset + 28] = reader.read_uint32()  # Node header -> QBones array

                    reader.seek(base_offset + 40)
                    offsets[base_offset + 40] = reader.read_uint32()  # Node header -> TBones Array

                    reader.seek(base_offset + 52)
                    offsets[base_offset + 52] = reader.read_uint32()  # Node header -> Array8

                    base_offset += _SKIN_HEADER_SIZE

                if node_type & _NODE_TYPE_DANGLY:
                    reader.seek(base_offset + 0)
                    offsets[base_offset + 0] = reader.read_uint32()  # Node header -> Dangly constraint array

                    reader.seek(base_offset + 24)
                    offsets[base_offset + 24] = reader.read_uint32()  # Node header -> Unknown

                    base_offset += _DANGLY_HEADER_SIZE

                if node_type & _NODE_TYPE_AABB:
                    reader.seek(base_offset + 0)
                    offsets[base_offset + 0] = reader.read_uint32()  # Node header -> AABB root node

                    aabbs = [offsets[base_offset + 0]]
                    while aabbs:
                        aabb = aabbs.pop()

                        reader.seek(aabb + 24)
                        leaf0 = reader.read_uint32()
                        if leaf0:
                            aabbs.append(leaf0)
                            offsets[aabb + 24] = leaf0  # AABB Node -> AABB child node

                        reader.seek(aabb + 28)
                        leaf1 = reader.read_uint32()
                        if leaf1:
                            aabbs.append(leaf1)
                            offsets[aabb + 28] = leaf1  # AABB Node -> AABB child node

                    base_offset += _AABB_HEADER_SIZE

                if node_type & _NODE_TYPE_SABER:
                    reader.seek(base_offset + 0)
                    offsets[base_offset + 0] = reader.read_uint32()  # Node header -> Saber Verts array

                    reader.seek(base_offset + 4)
                    offsets[base_offset + 4] = reader.read_uint32()  # Node header -> Saber UVs array

                    reader.seek(base_offset + 8)
                    offsets[base_offset + 8] = reader.read_uint32()  # Node header -> Saber Normals array

                    base_offset += _SABER_HEADER_SIZE

                reader.seek(node_offset + 8)
                offsets[node_offset + 8] = reader.read_uint32()  # Node header -> Geometry header

                reader.seek(node_offset + 12)
                offsets[node_offset + 12] = reader.read_uint32()  # Node header -> Parent node

                reader.seek(node_offset + 56)
                offsets[node_offset + 56] = reader.read_uint32()  # Node header -> controller array offset

                reader.seek(node_offset + 68)
                offsets[node_offset + 68] = reader.read_uint32()  # Node header -> controller data offset

                reader.seek(node_offset + 44)
                child_offsets_offset = reader.read_uint32()
                child_offsets_count = reader.read_uint32()
                offsets[node_offset + 44] = child_offsets_offset  # Node header -> Child node offsets array

                for i in range(child_offsets_count):
                    nodes.append(child_offsets_offset + i * 4)

        reader.seek(88)
        anim_locations_offset = reader.read_uint32()
        anim_count = reader.read_uint32()

        reader.seek(168)
        root_offset = reader.read_uint32()
        node_count = reader.read_uint32()

        reader.seek(184)
        name_offsets = reader.read_uint32()
        name_count = reader.read_uint32()

        reader.seek(40)
        offsets[40] = reader.read_uint32()  # Model header -> Root node

        reader.seek(88)
        offsets[88] = reader.read_uint32()  # Model header -> Animation array

        reader.seek(168)
        offsets[168] = reader.read_uint32()  # Model header -> Head root

        reader.seek(184)
        offsets[184] = reader.read_uint32()  # Model header -> Name offsets array

        for i in range(name_count):
            reader.seek(offsets[184] + i * 4)
            offsets[offsets[184] + i * 4] = reader.read_uint32()  # Name offset array -> Name

        for i in range(anim_count):
            reader.seek(anim_locations_offset + i * 4)
            animation_offset = reader.read_uint32()
            offsets[anim_locations_offset + i * 4] = animation_offset  # Event locations array -> Offset to event
            anim_offsets.append(animation_offset)

            reader.seek(animation_offset + 120)
            offsets[animation_offset + 120] = reader.read_uint32()  # Animation header -> Offset to event array

            reader.seek(animation_offset + 40)
            node_recursive(animation_offset + 40)

        node_recursive(168)

    # Second, we will update the function pointers to use K2 values instead of K1
    mdx_size = data[8:12]
    data = bytearray(data[12:])

    data[0:4] = struct.pack("I", _GEOM_ROOT_FP0_K2)
    data[4:8] = struct.pack("I", _GEOM_ROOT_FP1_K2)

    for anim_offset in anim_offsets:
        data[anim_offset:anim_offset + 4] = struct.pack("I", _GEOM_ANIM_FP0_K2)
        data[anim_offset + 4:anim_offset + 8] = struct.pack("I", _GEOM_ANIM_FP1_K2)

    for node_offset, node_type in mesh_offsets:
        mesh_start = node_offset + 80  # Start of mesh header

        if node_type & _NODE_TYPE_SKIN:
            data[mesh_start:mesh_start + 4] = struct.pack("I", _MESH_FP0_K2)
            data[mesh_start + 4:mesh_start + 8] = struct.pack("I", _MESH_FP1_K2)

        if node_type & _NODE_TYPE_DANGLY:
            data[mesh_start:mesh_start + 4] = struct.pack("I", _DANGLY_FP0_K2)
            data[mesh_start + 4:mesh_start + 8] = struct.pack("I", _DANGLY_FP1_K2)

        if node_type & _NODE_TYPE_SABER:
            data[mesh_start:mesh_start + 4] = struct.pack("I", _SABER_FP0_K1)
            data[mesh_start + 4:mesh_start + 8] = struct.pack("I", _SABER_FP1_K2)

        if node_type & _NODE_TYPE_AABB:
            data[mesh_start:mesh_start + 4] = struct.pack("I", _AABB_FP0_K2)
            data[mesh_start + 4:mesh_start + 8] = struct.pack("I", _AABB_FP1_K2)

    offsets = {k: v for k, v in sorted(list(offsets.items()), reverse=True)}

    # Third, we will add the extra data in the mesh headers and update all offsets in our dictionary
    shifted = 0
    for i in range(len(mesh_offsets)):
        node_offset, node_type = mesh_offsets[i]
        insert_location = node_offset + 80 + 324
        data = data[:insert_location] + bytes([0 for i in range(8)]) + data[insert_location:]

        for offset_location, offset_value in deepcopy(offsets).items():
            if insert_location < offset_location:
                del offsets[offset_location]
                if offset_location + 8 in offsets:
                    raise ValueError("whoops")
                offsets[offset_location + 8] = offset_value

        for offset_location, offset_value in deepcopy(offsets).items():
            if insert_location < offset_value:
                offsets[offset_location] = offset_value + 8

        for j in range(len(mesh_offsets)):
            if insert_location < mesh_offsets[j][0]:
                mesh_offsets[j][0] += 8

        shifted += 8

    # Finally, we update the offsets in the bytes with the offsets in our dictionary
    for offset_location, offset_value in offsets.items():
        data[offset_location:offset_location + 4] = struct.pack("I", offset_value)

    return bytes([0 for i in range(4)]) + struct.pack("I", len(data)) + mdx_size + data


def transform(
        data: bytes,
        translation: Vector3,
        rotation: float
) -> bytes:
    """
    Performs a translation and then rotation on the target MDL data.

    Args:
        data: MDL data.
        translation: Translation value.
        rotation: Rotation value.

    Returns:
        The MDL data post-transformation.
    """
    orientation = Vector4.from_euler(0, 0, rotation)
    mdx_size = struct.unpack("I", data[8:12])[0]
    data = bytearray(data[12:])

    with BinaryReader.from_bytes(data) as reader:
        reader.seek(44)
        node_count = reader.read_uint32()

        reader.seek(168)
        root_offset = reader.read_uint32()

        reader.seek(root_offset)
        type_id = reader.read_uint16()
        supernode_id = reader.read_uint16()
        label_id = reader.read_uint32()
        reader.skip(6)
        reader.skip(4)
        reader.skip(4)
        reader.skip(4 * 3)
        reader.skip(4 * 4)

        reader.seek(root_offset + 44)
        child_array_offset = reader.read_uint32()
        child_count = reader.read_uint32()

    if child_count == 0:
        return data

    root_child_array_offset = len(data)
    insert_node_offset = len(data) + 4
    insert_controller_offset = insert_node_offset + 80
    insert_controller_data_offset = insert_controller_offset + 32

    data[44:48] = struct.pack("I", node_count + 1)

    data[root_offset+44:root_offset+48] = struct.pack("I", root_child_array_offset)
    data[root_offset+48:root_offset+52] = struct.pack("I", 1)
    data[root_offset+52:root_offset+56] = struct.pack("I", 1)

    data += struct.pack("I", insert_node_offset)
    data += struct.pack("HHHH II fff ffff III III III",
                        1,                      # Node Type
                        node_count + 1,         # Node ID
                        1,                      # Label ID (steal some existing node's label)
                        0,                      # Padding

                        0,
                        root_offset,
                        *translation,              # Node Position
                        *orientation,           # Node Orientation
                        child_array_offset,     # Child Array Offset
                        child_count,
                        child_count,
                        insert_controller_offset,  # Controller Array
                        2,
                        2,
                        insert_controller_data_offset,  # Controller Data Array
                        9,
                        9
    )

    data += struct.pack("IHHHHBBBB", 8, 0xFFFF, 1, 0, 1, 3, 0, 0, 0)
    data += struct.pack("IHHHHBBBB", 20, 0xFFFF, 1, 4, 5, 4, 0, 0, 0)
    data += struct.pack("ffff", 0.0, *translation)
    data += struct.pack("fffff", 0.0, *orientation)

    return struct.pack("III", 0, len(data), mdx_size) + data
