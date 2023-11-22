import struct
from typing import List, Optional

import glm
from glm import mat4, vec3, vec4
from pykotor.common.stream import BinaryReader

from pykotor.gl.models.mdl import Node, Mesh, Model


def _load_node(scene, node: Optional[Node], mdl: BinaryReader, mdx: BinaryReader, offset: int, names: List[str]) -> Node:
    mdl.seek(offset)
    node_type = mdl.read_uint16()
    supernode_id = mdl.read_uint16()
    name_id = mdl.read_uint16()
    node = Node(scene, node, names[name_id])

    mdl.seek(offset + 16)
    node._position = glm.vec3(mdl.read_single(), mdl.read_single(), mdl.read_single())
    node._rotation = glm.quat(mdl.read_single(), mdl.read_single(), mdl.read_single(), mdl.read_single())
    node._recalc_transform()
    child_offsets = mdl.read_uint32()
    child_count = mdl.read_uint32()

    walkmesh = bool(node_type & 0b1000000000)

    if node_type & 0b100000:
        mdl.seek(offset + 80)
        fp = mdl.read_uint32()
        k2 = fp in [4216880, 4216816, 4216864]

        mdl.seek(offset + 80 + 8)
        offset_to_faces = mdl.read_uint32()
        face_count = mdl.read_uint32()

        mdl.seek(offset + 80 + 88)
        texture = mdl.read_string(32)
        lightmap = mdl.read_string(32)

        mdl.seek(offset + 80 + 313)
        node.render = bool(mdl.read_uint8())

        mdl.seek(offset + 80 + 304)
        vertex_count = mdl.read_uint16()
        if k2:
            mdl.seek(offset + 80 + 332)
        else:
            mdl.seek(offset + 80 + 324)
        mdx_offset = mdl.read_uint32()
        offset_to_vertices = mdl.read_uint32()

        element_data = []
        mdl.seek(offset + 80 + 184)
        element_offsets_count = mdl.read_uint32()
        offset_to_element_offsets = mdl.read_int32()
        if offset_to_element_offsets != -1 and element_offsets_count > 0:
            mdl.seek(offset_to_element_offsets)
            offset_to_elements = mdl.read_uint32()
            mdl.seek(offset_to_elements)
            element_data = mdl.read_bytes(face_count * 2 * 3)

        mdl.seek(offset + 80 + 252)
        mdx_block_size = mdl.read_uint32()
        mdx_data_bitflags = mdl.read_uint32()
        mdx_vertex_offset = mdl.read_int32()
        mdx_normal_offset = mdl.read_int32()
        mdl.skip(4)
        mdx_texture_offset = mdl.read_int32()
        mdx_lightmap_offset = mdl.read_int32()

        mdl.seek(offset + 80 + 313)
        render = mdl.read_uint8()

        if render and not walkmesh and element_offsets_count > 0:
            mdx.seek(mdx_offset)
            vertex_data = mdx.read_bytes(mdx_block_size * vertex_count)
            node.mesh = Mesh(scene, node, texture, lightmap, vertex_data, element_data, mdx_block_size, mdx_data_bitflags,
                             mdx_vertex_offset, mdx_normal_offset, mdx_texture_offset, mdx_lightmap_offset)

    for i in range(child_count):
        mdl.seek(child_offsets + i * 4)
        offset_to_child = mdl.read_uint32()
        new_node = _load_node(scene, node, mdl, mdx, offset_to_child, names)
        node.children.append(new_node)

    return node


def gl_load_mdl(scene, mdl: BinaryReader, mdx: BinaryReader) -> Model:
    mdl.seek(40)
    offset = mdl.read_uint32()

    mdl.seek(184)
    offset_to_name_offsets = mdl.read_uint32()
    name_count = mdl.read_uint32()

    mdl.seek(offset_to_name_offsets)
    name_offsets = [mdl.read_uint32() for _ in range(name_count)]
    names = []
    for name_offset in name_offsets:
        mdl.seek(name_offset)
        names.append(mdl.read_terminated_string("\0"))

    return Model(scene, _load_node(scene, None, mdl, mdx, offset, names))


def gl_load_stitched_model(scene, mdl: BinaryReader, mdx: BinaryReader) -> Model:
    """
    Returns a model instance that has meshes with the same textures merged together.
    """
    root = Node(scene, None, "root")

    mdl.seek(40)
    offset = mdl.read_uint32()

    mdl.seek(184)
    offset_to_name_offsets = mdl.read_uint32()
    name_count = mdl.read_uint32()

    mdl.seek(offset_to_name_offsets)
    name_offsets = [mdl.read_uint32() for _ in range(name_count)]
    names = []
    for name_offset in name_offsets:
        mdl.seek(name_offset)
        names.append(mdl.read_terminated_string("\0"))

    # Build list offset to nodes that: 1. Have meshes 2. Will render ingame
    offsets = []
    search = [(offset, mat4())]
    while search:
        offset, transform = search.pop()

        mdl.seek(offset)
        node_type = mdl.read_uint16()
        supernode_id = mdl.read_uint16()
        name_id = mdl.read_uint16()

        mdl.seek(offset + 16)
        position = glm.vec3(mdl.read_single(), mdl.read_single(), mdl.read_single())
        rotation = glm.quat(mdl.read_single(), mdl.read_single(), mdl.read_single(), mdl.read_single())
        child_offsets = mdl.read_uint32()
        child_count = mdl.read_uint32()

        transform = transform * glm.translate(position) * glm.mat4_cast(rotation)

        for i in range(child_count):
            mdl.seek(child_offsets + i * 4)
            offset_to_child = mdl.read_uint32()
            search.append((offset_to_child, transform))

        walkmesh = bool(node_type & 0b1000000000)
        mesh = bool(node_type & 0b100000)

        if mesh and not walkmesh:
            mdl.seek(offset + 80 + 313)
            if render := mdl.read_uint8():
                offsets.append((offset, transform))

        if names[name_id].lower() in ["headhook", "rhand", "lhand", "gogglehook", "maskhook"]:
            node = Node(scene, root, names[name_id])
            root.children.append(node)
            glm.decompose(transform, vec3(), node._rotation, node._position, vec3(), vec4())
            node._recalc_transform()

    merged = {}
    for offset, transform in offsets:
        mdl.seek(offset + 80 + 88)
        texture = mdl.read_string(32)
        lightmap = mdl.read_string(32)
        key = texture + "\n" + lightmap
        if key not in merged:
            merged[key] = []
        merged[key].append((offset, transform))

    for key, value in merged.items():
        vertex_data = bytearray()
        elements = []
        child = Node(scene, root, "child")
        root.children.append(child)

        last_element = 0
        for offset, transform in value:
            mdl.seek(offset + 80)
            fp = mdl.read_uint32()
            k2 = fp in [4216880, 4216816, 4216864]

            mdl.seek(offset + 80 + 252)
            mdx_block_size = mdl.read_uint32()
            mdx_data_bitflags = mdl.read_uint32()
            mdx_vertex_offset = mdl.read_int32()
            mdx_normal_offset = mdl.read_int32()
            mdl.skip(4)
            mdx_texture_offset = mdl.read_int32()
            mdx_lightmap_offset = mdl.read_int32()

            mdl.seek(offset + 80 + 8)
            offset_to_faces = mdl.read_uint32()
            face_count = mdl.read_uint32()
            mdl.seek(offset + 80 + 184)
            element_offsets_count = mdl.read_uint32()
            offset_to_element_offsets = mdl.read_int32()
            if offset_to_element_offsets != -1 and element_offsets_count > 0:
                mdl.seek(offset_to_element_offsets)
                offset_to_elements = mdl.read_uint32()
                mdl.seek(offset_to_elements)
                [
                    elements.append(mdl.read_uint16() + last_element)
                    for _ in range(face_count * 3)
                ]

            mdl.seek(offset + 80 + 304)
            vertex_count = mdl.read_uint16()
            if k2:
                mdl.seek(offset + 80 + 332)
            else:
                mdl.seek(offset + 80 + 324)
            mdx_offset = mdl.read_uint32()

            for i in range(vertex_count):
                mdx.seek(mdx_offset + i * mdx_block_size + mdx_vertex_offset)
                vertex = vec3(mdx.read_single(), mdx.read_single(), mdx.read_single())
                vertex = transform * vertex
                vertex_data += struct.pack('fff', vertex.x, vertex.y, vertex.z)

                if mdx_normal_offset == -1:
                    vertex_data += bytes(12)
                else:
                    mdx.seek(mdx_offset + i * mdx_block_size + mdx_normal_offset)
                    vertex_data += mdx.read_bytes(12)

                if mdx_texture_offset == -1:
                    vertex_data += bytes(8)
                else:
                    mdx.seek(mdx_offset + i * mdx_block_size + mdx_texture_offset)
                    vertex_data += mdx.read_bytes(8)

                if mdx_lightmap_offset == -1:
                    vertex_data += bytes(8)
                else:
                    mdx.seek(mdx_offset + i * mdx_block_size + mdx_lightmap_offset)
                    vertex_data += mdx.read_bytes(8)

            last_element += vertex_count

        element_data = bytearray()
        for element in elements:
            element_data += struct.pack('H', element)

        texture, lightmap = key.split("\n")
        child.mesh = Mesh(scene, child, texture, lightmap, vertex_data, element_data, 40, mdx_data_bitflags, 0, 12, 24, 32)

    return Model(scene, root)
