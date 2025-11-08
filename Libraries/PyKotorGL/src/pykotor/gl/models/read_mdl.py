from __future__ import annotations

import struct

from typing import TYPE_CHECKING

from pykotor.common.stream import BinaryReader
from pykotor.gl import glm, mat4, vec3, vec4
from pykotor.gl.models.mdl import Mesh, Model, Node

if TYPE_CHECKING:
    from glm import mat4x4

    from pykotor.gl.scene import Scene
    from utility.common.stream import SOURCE_TYPES


def _load_node(
    scene: Scene,
    node: Node | None,
    mdl: SOURCE_TYPES,
    mdx: SOURCE_TYPES,
    offset: int,
    names: list[str],
) -> Node:
    mdl_reader = BinaryReader.from_auto(mdl)
    mdl_reader.seek(offset)
    mdx_reader = BinaryReader.from_auto(mdx)

    node_type = mdl_reader.read_uint16()
    mdl_reader.read_uint16()  # supernode id
    name_id = mdl_reader.read_uint16()
    node = Node(scene, node, names[name_id])

    mdl_reader.seek(offset + 16)
    node._position = glm.vec3(mdl_reader.read_single(), mdl_reader.read_single(), mdl_reader.read_single())  # noqa: SLF001
    node._rotation = glm.quat(mdl_reader.read_single(), mdl_reader.read_single(), mdl_reader.read_single(), mdl_reader.read_single())  # noqa: SLF001
    node._recalc_transform()  # noqa: SLF001
    child_offsets = mdl_reader.read_uint32()
    child_count = mdl_reader.read_uint32()

    walkmesh = bool(node_type & 0b1000000000)

    if node_type & 0b100000:
        mdl_reader.seek(offset + 80)
        fp = mdl_reader.read_uint32()
        k2 = fp in {4216880, 4216816, 4216864}

        mdl_reader.seek(offset + 80 + 8)
        mdl_reader.read_uint32()  # offset_to_faces
        face_count = mdl_reader.read_uint32()

        mdl_reader.seek(offset + 80 + 88)
        texture = mdl_reader.read_terminated_string("\0", 32)
        lightmap = mdl_reader.read_terminated_string("\0", 32)

        mdl_reader.seek(offset + 80 + 313)
        node.render = bool(mdl_reader.read_uint8())

        mdl_reader.seek(offset + 80 + 304)
        vertex_count = mdl_reader.read_uint16()
        if k2:
            mdl_reader.seek(offset + 80 + 332)
        else:
            mdl_reader.seek(offset + 80 + 324)
        mdx_offset = mdl_reader.read_uint32()
        mdl_reader.read_uint32()  # offset_to_vertices

        element_data: list | bytes = []
        mdl_reader.seek(offset + 80 + 184)
        element_offsets_count = mdl_reader.read_uint32()
        offset_to_element_offsets = mdl_reader.read_int32()
        if offset_to_element_offsets != -1 and element_offsets_count > 0:
            mdl_reader.seek(offset_to_element_offsets)
            offset_to_elements = mdl_reader.read_uint32()
            mdl_reader.seek(offset_to_elements)
            element_data = mdl_reader.read_bytes(face_count * 2 * 3)

        mdl_reader.seek(offset + 80 + 252)
        mdx_block_size = mdl_reader.read_uint32()
        mdx_data_bitflags = mdl_reader.read_uint32()
        mdx_vertex_offset = mdl_reader.read_int32()
        mdx_normal_offset = mdl_reader.read_int32()
        mdl_reader.skip(4)
        mdx_texture_offset = mdl_reader.read_int32()
        mdx_lightmap_offset = mdl_reader.read_int32()

        mdl_reader.seek(offset + 80 + 313)
        render = mdl_reader.read_uint8()

        if render and not walkmesh and element_offsets_count > 0:
            mdx_reader.seek(mdx_offset)
            vertex_data = mdx_reader.read_bytes(mdx_block_size * vertex_count)
            node.mesh = Mesh(
                scene,
                node,
                texture,
                lightmap,
                bytearray(vertex_data),
                bytearray(element_data),
                mdx_block_size,
                mdx_data_bitflags,
                mdx_vertex_offset,
                mdx_normal_offset,
                mdx_texture_offset,
                mdx_lightmap_offset,
            )

    for i in range(child_count):
        mdl_reader.seek(child_offsets + i * 4)
        offset_to_child = mdl_reader.read_uint32()
        new_node = _load_node(scene, node, mdl_reader, mdx_reader, offset_to_child, names)
        node.children.append(new_node)

    return node


def gl_load_mdl(
    scene: Scene,
    mdl: SOURCE_TYPES,
    mdx: SOURCE_TYPES,
) -> Model:
    mdl_reader = BinaryReader.from_auto(mdl)
    mdl_reader.seek(40)
    offset = mdl_reader.read_uint32()

    mdl_reader.seek(184)
    offset_to_name_offsets = mdl_reader.read_uint32()
    name_count = mdl_reader.read_uint32()

    mdl_reader.seek(offset_to_name_offsets)
    name_offsets = [mdl_reader.read_uint32() for _ in range(name_count)]
    names: list[str] = []
    for name_offset in name_offsets:
        mdl_reader.seek(name_offset)
        names.append(mdl_reader.read_terminated_string("\0"))

    return Model(scene, _load_node(scene, None, mdl_reader, mdx, offset, names))


def gl_load_stitched_model(
    scene: Scene,
    mdl: SOURCE_TYPES,
    mdx: SOURCE_TYPES,
) -> Model:  # noqa: C901, PLR0915, PLR0912
    root = Node(scene, None, "root")

    mdl_reader = BinaryReader.from_auto(mdl)
    mdx_reader = BinaryReader.from_auto(mdx)
    mdl_reader.seek(40)
    offset = mdl_reader.read_uint32()

    mdl_reader.seek(184)
    offset_to_name_offsets = mdl_reader.read_uint32()
    name_count = mdl_reader.read_uint32()

    mdl_reader.seek(offset_to_name_offsets)
    name_offsets: list[int] = [mdl_reader.read_uint32() for _ in range(name_count)]
    names: list[str] = []
    for name_offset in name_offsets:
        mdl_reader.seek(name_offset)
        names.append(mdl_reader.read_terminated_string("\0"))

    # Build list offset to nodes that: 1. Have meshes 2. Will render ingame
    offsets: list[tuple[int, mat4x4]] = []
    search = [(offset, mat4())]
    while search:
        offset, transform = search.pop()

        mdl_reader.seek(offset)
        node_type = mdl_reader.read_uint16()
        _supernode_id = mdl_reader.read_uint16()
        name_list_index = mdl_reader.read_uint16()

        mdl_reader.seek(offset + 16)
        position = glm.vec3(mdl_reader.read_single(), mdl_reader.read_single(), mdl_reader.read_single())
        rotation = glm.quat(mdl_reader.read_single(), mdl_reader.read_single(), mdl_reader.read_single(), mdl_reader.read_single())
        child_offsets = mdl_reader.read_uint32()
        child_count = mdl_reader.read_uint32()

        transform = transform * glm.translate(position) * glm.mat4_cast(rotation)

        for i in range(child_count):
            mdl_reader.seek(child_offsets + i * 4)
            offset_to_child = mdl_reader.read_uint32()
            search.append((offset_to_child, transform))

        walkmesh = bool(node_type & 0b1000000000)
        mesh = bool(node_type & 0b100000)

        if mesh and not walkmesh:
            mdl_reader.seek(offset + 80 + 313)
            render = mdl_reader.read_uint8()
            if render:
                offsets.append((offset, transform))

        if names[name_list_index].lower() in {"headhook", "rhand", "lhand", "gogglehook", "maskhook"}:
            node = Node(scene, root, names[name_list_index])
            root.children.append(node)
            glm.decompose(transform, vec3(), node._rotation, node._position, vec3(), vec4())  # noqa: SLF001  # type: ignore[call-overload, reportCallIssue, reportArgumentType]
            node._recalc_transform()  # noqa: SLF001

    merged: dict[str, list[tuple[int, mat4x4]]] = {}
    for offset, transform in offsets:
        mdl_reader.seek(offset + 80 + 88)
        texture = mdl_reader.read_terminated_string("\0", 32)
        lightmap = mdl_reader.read_terminated_string("\0", 32)
        key = texture + "\n" + lightmap
        if key not in merged:
            merged[key] = []
        merged[key].append((offset, transform))

    for key, value in merged.items():
        vertex_data = bytearray()
        elements: list[int] = []
        child = Node(scene, root, "child")
        root.children.append(child)

        last_element = 0
        for offset, transform in value:
            mdl_reader.seek(offset + 80)
            fp = mdl_reader.read_uint32()
            k2 = fp in {4216880, 4216816, 4216864}

            mdl_reader.seek(offset + 80 + 252)
            mdx_block_size = mdl_reader.read_uint32()
            mdx_data_bitflags = mdl_reader.read_uint32()
            mdx_vertex_offset = mdl_reader.read_int32()
            mdx_normal_offset = mdl_reader.read_int32()
            mdl_reader.skip(4)
            mdx_texture_offset = mdl_reader.read_int32()
            mdx_lightmap_offset = mdl_reader.read_int32()

            mdl_reader.seek(offset + 80 + 8)
            mdl_reader.read_uint32()  # offset_to_faces
            face_count = mdl_reader.read_uint32()
            mdl_reader.seek(offset + 80 + 184)
            element_offsets_count = mdl_reader.read_uint32()
            offset_to_element_offsets = mdl_reader.read_int32()
            if offset_to_element_offsets != -1 and element_offsets_count > 0:
                mdl_reader.seek(offset_to_element_offsets)
                offset_to_elements = mdl_reader.read_uint32()
                mdl_reader.seek(offset_to_elements)
                elements.extend(mdl_reader.read_uint16() + last_element for _ in range(face_count * 3))
            mdl_reader.seek(offset + 80 + 304)
            vertex_count = mdl_reader.read_uint16()
            if k2:
                mdl_reader.seek(offset + 80 + 332)
            else:
                mdl_reader.seek(offset + 80 + 324)
            mdx_offset = mdl_reader.read_uint32()

            for i in range(vertex_count):
                mdx_reader.seek(mdx_offset + i * mdx_block_size + mdx_vertex_offset)
                vertex = vec3(mdx_reader.read_single(), mdx_reader.read_single(), mdx_reader.read_single())
                vertex = transform * vertex
                vertex_data += struct.pack("fff", vertex.x, vertex.y, vertex.z)

                if mdx_normal_offset == -1:
                    vertex_data += bytes(12)
                else:
                    mdx_reader.seek(mdx_offset + i * mdx_block_size + mdx_normal_offset)
                    vertex_data += mdx_reader.read_bytes(12)

                if mdx_texture_offset == -1:
                    vertex_data += bytes(8)
                else:
                    mdx_reader.seek(mdx_offset + i * mdx_block_size + mdx_texture_offset)
                    vertex_data += mdx_reader.read_bytes(8)

                if mdx_lightmap_offset == -1:
                    vertex_data += bytes(8)
                else:
                    mdx_reader.seek(mdx_offset + i * mdx_block_size + mdx_lightmap_offset)
                    vertex_data += mdx_reader.read_bytes(8)

            last_element += vertex_count

        element_data = bytearray()
        for element in elements:
            element_data += struct.pack("H", element)

        texture, lightmap = key.split("\n")
        child.mesh = Mesh(scene, child, texture, lightmap, vertex_data, element_data, 40, mdx_data_bitflags, 0, 12, 24, 32)

    return Model(scene, root)
