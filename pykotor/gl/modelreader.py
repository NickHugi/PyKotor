from typing import List, Optional

import glm
from pykotor.common.stream import BinaryReader

from pykotor.gl.model import Node, Mesh, Model


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
        k2 = True if fp == 4216880 or fp == 4216816 or fp == 4216864 else False

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

    name_offsets = []
    mdl.seek(offset_to_name_offsets)
    for i in range(name_count):
        name_offsets.append(mdl.read_uint32())

    names = []
    for name_offset in name_offsets:
        mdl.seek(name_offset)
        names.append(mdl.read_terminated_string("\0"))

    model = Model(scene, _load_node(scene, None, mdl, mdx, offset, names))
    return model
