"""Model manipulation utilities for MDL/MDX files.

This module provides utility functions for manipulating KotOR model geometry at the binary level,
including texture/lightmap iteration, node renaming, and geometry offset calculations.

References:
----------
    vendor/reone/src/libs/graphics/model.cpp - Model loading and parsing
    vendor/reone/src/libs/resource/format/mdlmdxreader.cpp - MDL/MDX binary reading
    vendor/mdlops (MDL/MDX manipulation tool)
    vendor/kotorblender/io_scene_kotor/format/mdl/ - Blender MDL reader/writer
    vendor/KotOR.js/src/odyssey/OdysseyModel.ts - TypeScript model handling
    Note: Magic float values (_MESH_FP0_K1, etc.) are game-specific floating point offsets for binary patching
"""

from __future__ import annotations

import math
import struct

from collections import deque
from copy import deepcopy
from typing import TYPE_CHECKING, Any, NamedTuple

from pykotor.common.misc import Game
from pykotor.common.stream import BinaryReader
from utility.common.geometry import Vector4

if TYPE_CHECKING:
    from collections.abc import Generator

    from utility.common.geometry import Vector3

_GEOM_ROOT_FP0_K1: int = 4273776
_GEOM_ROOT_FP1_K1: int = 4216096
_GEOM_ROOT_FP0_K2: int = 4285200
_GEOM_ROOT_FP1_K2: int = 4216320

_GEOM_ANIM_FP0_K1: int = 4273392
_GEOM_ANIM_FP1_K1: int = 4451552
_GEOM_ANIM_FP0_K2: int = 4284816
_GEOM_ANIM_FP1_K2: int = 4522928

_NODE_TYPE_MESH: int = 32
_MESH_HEADER_SIZE_K1: int = 332
_MESH_HEADER_SIZE_K2: int = 340
_MESH_FP0_K1: int = 4216656
_MESH_FP1_K1: int = 4216672
_MESH_FP0_K2: int = 4216880
_MESH_FP1_K2: int = 4216896

_NODE_TYPE_SKIN: int = 64
_SKIN_HEADER_SIZE = 108
_SKIN_FP0_K1: int = 4216592
_SKIN_FP1_K1: int = 4216608
_SKIN_FP0_K2: int = 4216816
_SKIN_FP1_K2: int = 4216832

_NODE_TYPE_DANGLY: int = 256
_DANGLY_HEADER_SIZE: int = 28
_DANGLY_FP0_K1: int = 4216640
_DANGLY_FP1_K1: int = 4216624
_DANGLY_FP0_K2: int = 4216864
_DANGLY_FP1_K2: int = 4216848

_NODE_TYPE_SABER: int = 2048
_SABER_HEADER_SIZE: int = 20
_SABER_FP0_K1: int = 4216656
_SABER_FP1_K1: int = 4216672
_SABER_FP0_K2: int = 4216880
_SABER_FP1_K2: int = 4216896

_NODE_TYPE_AABB: int = 512
_AABB_HEADER_SIZE: int = 4
_AABB_FP0_K1: int = 4216656
_AABB_FP1_K1: int = 4216672
_AABB_FP0_K2: int = 4216880
_AABB_FP1_K2: int = 4216896

_NODE_TYPE_LIGHT: int = 2
_LIGHT_HEADER_SIZE: int = 92

_NODE_TYPE_EMITTER: int = 4
_EMITTER_HEADER_SIZE: int = 224


class MDLMDXTuple(NamedTuple):
    mdl: bytes
    mdx: bytes


def rename(
    data: bytes,
    name: str,
) -> bytes:
    return data[:20] + name.ljust(32, "\0").encode("ascii") + data[52:]


def iterate_textures_and_lightmaps(
    data: bytes,
) -> Generator[str, Any, None]:
    seen_names: set[str] = set()

    with BinaryReader.from_bytes(data, 12) as reader:
        reader.seek(168)
        root_offset: int = reader.read_uint32()

        nodes: deque[int] = deque([root_offset])
        while nodes:
            node_offset: int = nodes.popleft()
            reader.seek(node_offset)
            node_id: int = reader.read_uint32()

            reader.seek(node_offset + 44)
            child_offsets_offset: int = reader.read_uint32()
            child_offsets_count: int = reader.read_uint32()

            reader.seek(child_offsets_offset)
            nodes.extend(reader.read_uint32() for _ in range(child_offsets_count))

            if node_id & 32:
                # Extract texture name
                reader.seek(node_offset + 168)
                name: str = reader.read_string(32, encoding="ascii", errors="ignore").strip().lower()
                if name and name != "null" and name not in seen_names and name != "dirt":
                    seen_names.add(name)
                    yield name

                # Extract lightmap name
                reader.seek(node_offset + 200)
                name = reader.read_string(32, encoding="ascii", errors="ignore").strip().lower()
                if name and name != "null" and name not in seen_names:
                    seen_names.add(name)
                    yield name


def iterate_textures(
    data: bytes,
) -> Generator[str, Any, None]:
    texture_caseset: set[str] = set()

    with BinaryReader.from_bytes(data, 12) as reader:
        reader.seek(168)
        root_offset: int = reader.read_uint32()

        nodes: list[int] = [root_offset]
        while nodes:
            node_offset: int = nodes.pop()
            reader.seek(node_offset)
            node_id: int = reader.read_uint32()

            reader.seek(node_offset + 44)
            child_offsets_offset: int = reader.read_uint32()
            child_offsets_count: int = reader.read_uint32()

            reader.seek(child_offsets_offset)
            nodes.extend(reader.read_uint32() for _ in range(child_offsets_count))
            if node_id & 32:
                reader.seek(node_offset + 168)
                texture = reader.read_string(32, encoding="ascii", errors="ignore").strip()
                if (
                    texture and texture != "NULL" and texture.lower() not in texture_caseset and texture.lower() != "dirt"  # TODO(th3w1zard1): determine if the game really prevents the literal resname of 'dirt'.
                ):
                    texture_caseset.add(texture.lower())
                    yield texture.lower()


def iterate_lightmaps(
    data: bytes,
) -> Generator[str, Any, None]:
    lightmaps_caseset: set[str] = set()
    with BinaryReader.from_bytes(data, 12) as reader:
        reader.seek(168)
        root_offset: int = reader.read_uint32()

        nodes: list[int] = [root_offset]
        while nodes:
            node_offset: int = nodes.pop()
            reader.seek(node_offset)
            node_id: int = reader.read_uint32()

            reader.seek(node_offset + 44)
            child_offsets_offset: int = reader.read_uint32()
            child_offsets_count: int = reader.read_uint32()

            reader.seek(child_offsets_offset)
            nodes.extend(reader.read_uint32() for _ in range(child_offsets_count))
            if node_id & 32:
                reader.seek(node_offset + 200)
                lightmap: str = reader.read_string(32, encoding="ascii", errors="ignore").strip()
                lowercase_lightmap: str = lightmap.lower()
                if lightmap and lightmap != "NULL" and lowercase_lightmap not in lightmaps_caseset:
                    lightmaps_caseset.add(lowercase_lightmap)
                    yield lightmap


def change_textures(
    data: bytes,
    textures: dict[str, str],
) -> bytes:
    data = bytearray(data)
    offsets: dict[str, list[int]] = {}

    textures_ins: dict[str, str] = {old_texture.lower(): new_texture.lower() for old_texture, new_texture in textures.items()}
    textures = textures_ins

    with BinaryReader.from_bytes(data, 12) as reader:
        reader.seek(168)
        root_offset: int = reader.read_uint32()

        nodes: list[int] = [root_offset]
        while nodes:
            node_offset: int = nodes.pop()
            reader.seek(node_offset)
            node_id: int = reader.read_uint32()

            reader.seek(node_offset + 44)
            child_offsets_offset: int = reader.read_uint32()
            child_offsets_count: int = reader.read_uint32()

            reader.seek(child_offsets_offset)
            nodes.extend(reader.read_uint32() for _ in range(child_offsets_count))
            if node_id & 32:
                reader.seek(node_offset + 168)
                texture: str = reader.read_string(32).lower()

                if texture in textures:
                    if texture in offsets:
                        offsets[texture].append(node_offset + 168)
                    else:
                        offsets[texture] = [node_offset + 168]

        for texture, offsets_list in offsets.items():
            for offset in offsets_list:
                new_offset: int = offset + 12
                data = (
                    data[:new_offset]
                    + struct.pack(
                        "32s",
                        textures[texture].ljust(32, "\0").encode("ascii"),
                    )
                    + data[new_offset + 32 :]
                )

    return bytes(data)


def change_lightmaps(
    data: bytes,
    textures: dict[str, str],
) -> bytes:
    data = bytearray(data)
    offsets: dict[str, list[int]] = {}

    textures_ins: dict[str, str] = {old_texture.lower(): new_texture.lower() for old_texture, new_texture in textures.items()}
    textures = textures_ins

    with BinaryReader.from_bytes(data, 12) as reader:
        reader.seek(168)
        root_offset: int = reader.read_uint32()

        nodes: list[int] = [root_offset]
        while nodes:
            node_offset: int = nodes.pop()
            reader.seek(node_offset)
            node_id: int = reader.read_uint32()

            reader.seek(node_offset + 44)
            child_offsets_offset: int = reader.read_uint32()
            child_offsets_count: int = reader.read_uint32()

            reader.seek(child_offsets_offset)
            nodes.extend(reader.read_uint32() for _i in range(child_offsets_count))
            if node_id & 32:
                reader.seek(node_offset + 200)
                texture: str = reader.read_string(32).lower()

                if texture in textures:
                    if texture in offsets:
                        offsets[texture].append(node_offset + 200)
                    else:
                        offsets[texture] = [node_offset + 200]

        for texture, offsets_list in offsets.items():
            for offset in offsets_list:
                actual_offset: int = offset + 12
                data = (
                    data[:actual_offset]
                    + struct.pack(
                        "32s",
                        textures[texture].ljust(32, "\0").encode("ascii"),
                    )
                    + data[actual_offset + 32 :]
                )

    return bytes(data)


def detect_version(
    data: bytes,
) -> Game:
    pointer: int = struct.unpack("I", data[12:16])[0]
    return Game.K1 if pointer == _GEOM_ROOT_FP0_K1 else Game.K2


def convert_to_k1(
    data: bytes,
) -> bytes:
    if detect_version(data) == Game.K1:
        return data

    trim: list[tuple[int, int]] = []

    with BinaryReader.from_bytes(data, 12) as reader:
        reader.seek(168)
        root_offset: int = reader.read_uint32()

        nodes: list[int] = [root_offset]
        while nodes:
            node_offset: int = nodes.pop()
            reader.seek(node_offset)
            node_type: int = reader.read_uint16()

            if node_type & 32:
                trim.append((node_type, node_offset))

            reader.seek(node_offset + 44)
            child_offsets_offset: int = reader.read_uint32()
            child_offsets_count: int = reader.read_uint32()

            reader.seek(child_offsets_offset)
            nodes.extend(reader.read_uint32() for _ in range(child_offsets_count))
    start: bytes = data[:12]
    data = bytearray(data[12:])

    data[:4] = struct.pack("I", _GEOM_ROOT_FP0_K1)
    data[4:8] = struct.pack("I", _GEOM_ROOT_FP1_K1)

    # TODO(NickHugi): Animations

    for node_type, node_offset in trim:
        mesh_start: int = node_offset + 80  # Start of mesh header

        offset_start: int = node_offset + 80 + 332  # Location of start of bytes to be shifted
        offset_size: int = 8  # How many bytes we have to shift

        if node_type & _NODE_TYPE_SKIN:
            offset_size += _SKIN_HEADER_SIZE
            data[mesh_start : mesh_start + 4] = struct.pack("I", _MESH_FP0_K1)
            data[mesh_start + 4 : mesh_start + 8] = struct.pack("I", _MESH_FP1_K1)

        if node_type & _NODE_TYPE_DANGLY:
            offset_size += _DANGLY_HEADER_SIZE
            data[mesh_start : mesh_start + 4] = struct.pack("I", _DANGLY_FP0_K1)
            data[mesh_start + 4 : mesh_start + 8] = struct.pack("I", _DANGLY_FP1_K1)

        if node_type & _NODE_TYPE_SABER:
            offset_size += _SABER_HEADER_SIZE
            data[mesh_start : mesh_start + 4] = struct.pack("I", _SABER_FP0_K1)
            data[mesh_start + 4 : mesh_start + 8] = struct.pack("I", _SABER_FP1_K1)

        if node_type & _NODE_TYPE_AABB:
            offset_size += _AABB_HEADER_SIZE
            data[mesh_start : mesh_start + 4] = struct.pack("I", _AABB_FP0_K1)
            data[mesh_start + 4 : mesh_start + 8] = struct.pack("I", _AABB_FP1_K1)

        shifting: bytearray = data[offset_start : offset_start + offset_size]
        data[offset_start - 8 : offset_start - 8 + offset_size] = shifting

    return bytes(start + data)


def convert_to_k2(  # noqa: C901, PLR0915, PLR0912
    data: bytes,
) -> bytes:
    if detect_version(data) == Game.K2:
        return data

    offsets: dict[int, int] = {}  # Maps the offset for an offset to its offset
    mesh_offsets: list[list[int]] = []  # tuple of (Offset to every mesh node, Node type)
    anim_offsets: list[int] = []

    # First, we build a dictionary of every offset in the file plus a list of the mesh nodes
    with BinaryReader.from_bytes(data, 12) as reader:

        def node_recursive(  # noqa: C901, PLR0912, PLR0915
            offset_to_root_offset: int,
        ) -> None:
            nodes: list[int] = [offset_to_root_offset]
            while nodes:
                offset_to_node_offset: int = nodes.pop()
                reader.seek(offset_to_node_offset)
                node_offset: int = reader.read_uint32()
                offsets[offset_to_node_offset] = node_offset  # Geometry header/Node children offsets array -> Node offset

                reader.seek(node_offset)
                node_type: int = reader.read_uint16()

                base_offset: int = node_offset + 80
                if node_type & _NODE_TYPE_MESH:
                    mesh_offsets.append([node_offset, node_type])

                    reader.seek(base_offset + 8)
                    offsets[base_offset + 8] = reader.read_uint32()  # Node header -> Face array offset

                    reader.seek(base_offset + 176)
                    offsets[base_offset + 176] = reader.read_uint32()  # Node header -> Vertex indices count array
                    indices_array_count: int = reader.read_uint32()

                    reader.seek(base_offset + 188)
                    offsets[base_offset + 188] = reader.read_uint32()  # Node header -> Vertex indices locations array
                    if indices_array_count == 1:
                        indices_locations_offset: int = offsets[base_offset + 188]
                        reader.seek(indices_locations_offset)
                        offsets[indices_locations_offset] = reader.read_uint32()  # Vertex indices locations array -> Vertex indices array

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
                    texture_count: int = reader.read_uint32()

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

                    aabbs: list[int] = [offsets[base_offset + 0]]
                    while aabbs:
                        aabb: int = aabbs.pop()

                        reader.seek(aabb + 24)
                        leaf0: int = reader.read_uint32()
                        if leaf0:
                            aabbs.append(leaf0)
                            offsets[aabb + 24] = leaf0  # AABB Node -> AABB child node

                        reader.seek(aabb + 28)
                        leaf1: int = reader.read_uint32()
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
                child_offsets_offset: int = reader.read_uint32()
                child_offsets_count: int = reader.read_uint32()
                offsets[node_offset + 44] = child_offsets_offset  # Node header -> Child node offsets array

                nodes = [child_offsets_offset + i * 4 for i in range(child_offsets_count)]
                nodes.insert(0, offset_to_root_offset)

        reader.seek(88)
        anim_locations_offset: int = reader.read_uint32()
        anim_count: int = reader.read_uint32()

        reader.seek(168)
        reader.read_uint32()
        reader.read_uint32()

        reader.seek(184)
        reader.read_uint32()
        name_count: int = reader.read_uint32()

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
            animation_offset: int = reader.read_uint32()
            offsets[anim_locations_offset + i * 4] = animation_offset  # Event locations array -> Offset to event
            anim_offsets.append(animation_offset)

            reader.seek(animation_offset + 120)
            offsets[animation_offset + 120] = reader.read_uint32()  # Animation header -> Offset to event array

            reader.seek(animation_offset + 40)
            node_recursive(animation_offset + 40)

        node_recursive(168)

    # Second, we will update the function pointers to use K2 values instead of K1
    mdx_size: bytes = data[8:12]
    data = bytearray(data[12:])

    data[:4] = struct.pack("I", _GEOM_ROOT_FP0_K2)
    data[4:8] = struct.pack("I", _GEOM_ROOT_FP1_K2)

    for anim_offset in anim_offsets:
        data[anim_offset : anim_offset + 4] = struct.pack("I", _GEOM_ANIM_FP0_K2)
        data[anim_offset + 4 : anim_offset + 8] = struct.pack("I", _GEOM_ANIM_FP1_K2)

    for node_offset, node_type in mesh_offsets:
        mesh_start: int = node_offset + 80  # Start of mesh header

        if node_type & _NODE_TYPE_SKIN:
            data[mesh_start : mesh_start + 4] = struct.pack("I", _MESH_FP0_K2)
            data[mesh_start + 4 : mesh_start + 8] = struct.pack("I", _MESH_FP1_K2)

        if node_type & _NODE_TYPE_DANGLY:
            data[mesh_start : mesh_start + 4] = struct.pack("I", _DANGLY_FP0_K2)
            data[mesh_start + 4 : mesh_start + 8] = struct.pack("I", _DANGLY_FP1_K2)

        if node_type & _NODE_TYPE_SABER:
            data[mesh_start : mesh_start + 4] = struct.pack("I", _SABER_FP0_K1)
            data[mesh_start + 4 : mesh_start + 8] = struct.pack("I", _SABER_FP1_K2)

        if node_type & _NODE_TYPE_AABB:
            data[mesh_start : mesh_start + 4] = struct.pack("I", _AABB_FP0_K2)
            data[mesh_start + 4 : mesh_start + 8] = struct.pack("I", _AABB_FP1_K2)

    offsets = dict(sorted(offsets.items(), reverse=True))

    # Third, we will add the extra data in the mesh headers and update all offsets in our dictionary
    shifted: int = 0
    for i in range(len(mesh_offsets)):
        node_offset, node_type = mesh_offsets[i]
        insert_location: int = node_offset + 80 + 324
        data = (data[:insert_location] + bytes(0 for i in range(8))) + data[insert_location:]

        for offset_location, offset_value in deepcopy(offsets).items():
            if insert_location < offset_location:
                del offsets[offset_location]
                if offset_location + 8 in offsets:
                    msg = "whoops"
                    raise ValueError(msg)
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
        data[offset_location : offset_location + 4] = struct.pack("I", offset_value)

    return bytes(0 for _ in range(4)) + struct.pack("I", len(data)) + mdx_size + data


def transform(
    data: bytes,
    translation: Vector3,
    rotation: float,
) -> bytes:
    orientation: Vector4 = Vector4.from_euler(0, 0, math.radians(rotation))
    mdx_size: int = struct.unpack("I", data[8:12])[0]
    data = bytearray(data[12:])

    with BinaryReader.from_bytes(data) as reader:
        reader.seek(44)
        node_count: int = reader.read_uint32()

        reader.seek(168)
        root_offset: int = reader.read_uint32()

        reader.seek(root_offset)
        reader.read_uint16()
        reader.read_uint16()
        reader.read_uint32()
        reader.skip(6)
        reader.skip(4)
        reader.skip(4)
        reader.skip(4 * 3)
        reader.skip(4 * 4)

        reader.seek(root_offset + 44)
        child_array_offset: int = reader.read_uint32()
        child_count: int = reader.read_uint32()

    if child_count == 0:
        return data

    root_child_array_offset: int = len(data)
    insert_node_offset: int = len(data) + 4
    insert_controller_offset: int = insert_node_offset + 80
    insert_controller_data_offset: int = insert_controller_offset + 32

    # Increase global node count by 1
    data[44:48] = struct.pack("I", node_count + 1)

    # Update the offset the array of child offsets to our injected array
    data[root_offset + 44 : root_offset + 48] = struct.pack(
        "I",
        root_child_array_offset,
    )
    # Set the root node to have 1 child
    data[root_offset + 48 : root_offset + 52] = struct.pack("I", 1)
    data[root_offset + 52 : root_offset + 56] = struct.pack("I", 1)

    # Populate the injected new root child offsets array
    # It will contain our new node
    data += struct.pack("I", insert_node_offset)
    # Create the new node
    data += struct.pack(
        "HHHH II fff ffff III III III",
        1,  # Node Type
        node_count + 1,  # Node ID
        1,  # Label ID (steal some existing node's label)
        0,  # Padding
        0,
        root_offset,
        *translation,  # Node Position
        orientation.w,
        orientation.x,
        orientation.y,
        orientation.z,  # Node Orientation
        child_array_offset,  # Child Array Offset
        child_count,
        child_count,
        insert_controller_offset,  # Controller Array
        2,
        2,
        insert_controller_data_offset,  # Controller Data Array
        9,
        9,
    )
    # Inject controller and controller data of new node to the end of the file
    data += struct.pack("IHHHHBBBB", 8, 0xFFFF, 1, 0, 1, 3, 0, 0, 0)
    data += struct.pack("IHHHHBBBB", 20, 0xFFFF, 1, 4, 5, 4, 0, 0, 0)
    data += struct.pack("ffff", 0.0, *translation)
    data += struct.pack("fffff", 0.0, *orientation)

    return struct.pack("III", 0, len(data), mdx_size) + data


def flip(  # noqa: C901, PLR0912, PLR0915
    mdl_data: bytes,
    mdx_data: bytes,
    *,
    flip_x: bool,
    flip_y: bool,
) -> MDLMDXTuple:
    # If neither bools are set to True, no transformations need to be done and we can just return the original data
    if not flip_x and not flip_y:
        return MDLMDXTuple(mdl_data, mdx_data)

    # The data we need to change:
    #    1. The vertices stored in the MDL
    #    2. The vertex positions, normals, stored in the MDX

    # Trim the data to correct the offsets
    mdl_start: bytes = mdl_data[:12]
    mdl_data = bytearray(mdl_data[12:])
    mdx_data = bytearray(mdx_data)

    mdl_vertex_offsets: list[tuple[int, int]] = []  # This is a list of tuples: (count, offset)
    mdx_vertex_offsets: list[tuple[int, int, int, int]] = []  # This is a list of tuples: (count, offset, stride, position)
    mdx_normal_offsets: list[tuple[int, int, int, int]] = []  # This is a list of tuples: (count, offset, stride, position)
    elements_offsets: list[tuple[int, int]] = []  # This is a list of tuples: (count, offset)
    faces_offsets: list[tuple[int, int]] = []  # This is a list of tuples: (count, offset)
    with BinaryReader.from_bytes(mdl_data) as reader:
        reader.seek(168)
        root_offset: int = reader.read_uint32()

        nodes: list[int] = [root_offset]
        while nodes:
            node_offset: int = nodes.pop()
            reader.seek(node_offset)
            node_id: int = reader.read_uint32()

            mdl_vertex_offsets.append((1, node_offset + 16))

            # Need to determine the location of the position controller
            reader.seek(node_offset + 56)
            controllers_offset: int = reader.read_uint32()
            controllers_count: int = reader.read_uint32()

            reader.seek(node_offset + 68)
            controller_datas_offset: int = reader.read_uint32()
            reader.read_uint32()

            for i in range(controllers_count):
                reader.seek(controllers_offset + i * 16)
                controller_type: int = reader.read_uint32()
                if controller_type == 8:  # noqa: PLR2004
                    reader.skip(6)
                    data_offset: int = reader.read_uint16()
                    mdl_vertex_offsets.append(
                        (1, controller_datas_offset + data_offset * 4),
                    )

            reader.seek(node_offset + 44)
            child_offsets_offset: int = reader.read_uint32()
            child_offsets_count: int = reader.read_uint32()

            reader.seek(child_offsets_offset)
            nodes.extend(reader.read_uint32() for i in range(child_offsets_count))
            if node_id & 32:
                reader.seek(node_offset + 80)
                fp: int = reader.read_uint32()
                tsl: bool = fp not in {
                    _MESH_FP0_K1,
                    _SKIN_FP0_K1,
                    _DANGLY_FP0_K2,
                    _AABB_FP0_K1,
                    _SABER_FP0_K1,
                }

                reader.seek(node_offset + 80 + 8)
                faces_offset: int = reader.read_uint32()
                faces_count: int = reader.read_uint32()
                faces_offsets.append((faces_count, faces_offset))

                reader.seek(node_offset + 80 + 188)
                offset_to_elements_offset = reader.read_uint32()
                reader.seek(offset_to_elements_offset)
                elements_offset: int = reader.read_uint32()
                elements_offsets.append((faces_count, elements_offset))

                reader.seek(node_offset + 80 + 304)
                vertex_count: int = reader.read_uint16()
                reader.seek(node_offset + 80 + 336 if tsl else node_offset + 80 + 328)
                vertex_offset: int = reader.read_uint32()
                mdl_vertex_offsets.append((vertex_count, vertex_offset))

                reader.seek(node_offset + 80 + 252)
                mdx_stride: int = reader.read_uint32()
                reader.read_uint32()
                reader.seek(node_offset + 80 + 260)
                mdx_offset_pos: int = reader.read_uint32()
                mdx_offset_norm: int = reader.read_uint32()
                reader.seek(node_offset + 80 + 332 if tsl else node_offset + 80 + 324)
                mdx_start: int = reader.read_uint32()
                mdx_vertex_offsets.append(
                    (vertex_count, mdx_start, mdx_stride, mdx_offset_pos),
                )
                mdx_normal_offsets.append(
                    (vertex_count, mdx_start, mdx_stride, mdx_offset_norm),
                )

    # Fix vertex order
    if flip_x != flip_y:
        for count, start_offset in elements_offsets:
            for i in range(count):
                offset: int = start_offset + i * 6
                v1: int = struct.unpack("H", mdl_data[offset : offset + 2])[0]
                v2: int = struct.unpack("H", mdl_data[offset + 2 : offset + 4])[0]
                v3: int = struct.unpack("H", mdl_data[offset + 4 : offset + 6])[0]
                mdl_data[offset : offset + 2] = struct.pack("H", v1)
                mdl_data[offset + 2 : offset + 4] = struct.pack("H", v3)
                mdl_data[offset + 4 : offset + 6] = struct.pack("H", v2)
        for count, start_offset in faces_offsets:
            for i in range(count):
                offset = start_offset + i * 32 + 26
                v1 = struct.unpack("H", mdl_data[offset : offset + 2])[0]
                v2 = struct.unpack("H", mdl_data[offset + 2 : offset + 4])[0]
                v3 = struct.unpack("H", mdl_data[offset + 4 : offset + 6])[0]
                mdl_data[offset : offset + 2] = struct.pack("H", v1)
                mdl_data[offset + 2 : offset + 4] = struct.pack("H", v3)
                mdl_data[offset + 4 : offset + 6] = struct.pack("H", v2)

    # Update the MDL vertices
    for count, start_offset in mdl_vertex_offsets:
        for i in range(count):
            offset = start_offset + i * 12
            if flip_x:
                x: float = struct.unpack("f", mdl_data[offset : offset + 4])[0]
                mdl_data[offset : offset + 4] = struct.pack("f", -x)
            if flip_y:
                y: float = struct.unpack("f", mdl_data[offset + 4 : offset + 8])[0]
                mdl_data[offset + 4 : offset + 8] = struct.pack("f", -y)

    # Update the MDX vertices
    for count, start_offset, stride, position in mdx_vertex_offsets:
        for i in range(count):
            offset = start_offset + i * stride + position
            if flip_x:
                x = struct.unpack("f", mdx_data[offset : offset + 4])[0]
                mdx_data[offset : offset + 4] = struct.pack("f", -x)
            if flip_y:
                y = struct.unpack("f", mdx_data[offset + 4 : offset + 8])[0]
                mdx_data[offset + 4 : offset + 8] = struct.pack("f", -y)

    # Update the MDX normals
    for count, start_offset, stride, position in mdx_normal_offsets:
        for i in range(count):
            offset = start_offset + i * stride + position
            if flip_x:
                x = struct.unpack("f", mdx_data[offset : offset + 4])[0]
                mdx_data[offset : offset + 4] = struct.pack("f", -x)
            if flip_y:
                y = struct.unpack("f", mdx_data[offset + 4 : offset + 8])[0]
                mdx_data[offset + 4 : offset + 8] = struct.pack("f", -y)

    # Re-add the first 12 bytes
    mdl_data = mdl_start + mdl_data

    return MDLMDXTuple(mdl_data, mdx_data)
