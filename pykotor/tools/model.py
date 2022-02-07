import io
import struct
from typing import Dict

from pykotor.common.stream import BinaryReader, BinaryWriter


def change_textures(data: bytes, textures: Dict[str, str]) -> bytes:
    data = bytearray(data)

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
                texture = reader.read_string(32)

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
