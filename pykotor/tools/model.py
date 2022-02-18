import io
import struct
from typing import Dict, List

from pykotor.common.misc import Game

from pykotor.common.stream import BinaryReader, BinaryWriter

_GEOM_ROOT_FP0_K1 = 4273776
_GEOM_ROOT_FP1_K1 = 4216096
_GEOM_ROOT_FP0_K2 = ...
_GEOM_ROOT_FP1_K2 = ...

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


def rename(data: bytes, name: str) -> bytes:
    return data[:20] + name.ljust(32, '\0').encode('ascii') + data[52:]


def list_textures(data: bytes) -> List[str]:
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


def list_lightmaps(data: bytes) -> List[str]:
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


def change_textures(data: bytes, textures: Dict[str, str]) -> bytes:
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
                data = data[:offset] + struct.pack('32s', textures[texture].ljust(32, '\0').encode('ascii')) + data[offset+32:]

    return bytes(data)


def change_lightmaps(data: bytes, textures: Dict[str, str]) -> bytes:
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
                data = data[:offset] + struct.pack('32s', textures[texture].ljust(32, '\0').encode('ascii')) + data[offset+32:]

    return bytes(data)


def detect_version(data: bytes) -> Game:
    pointer = struct.unpack("I", data[12:16])[0]
    return Game.K1 if pointer == _GEOM_ROOT_FP0_K1 else Game.K2




def convert_to_k1(data: bytes) -> bytes:
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

        shifting = data[offset_start:offset_start+offset_size]
        data[offset_start-8:offset_start-8+offset_size] = shifting

    return bytes(start + data)

