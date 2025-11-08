"""Loader utilities for converting KotOR MDL/TPC files into Panda3D formats."""

from __future__ import annotations

import struct

from typing import TYPE_CHECKING

from panda3d.core import Geom, GeomNode, GeomTriangles, GeomVertexData, GeomVertexFormat, GeomVertexWriter, LMatrix4, LPoint3, LQuaternion, NodePath, Texture, TransformState

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.tpc import TPCTextureFormat

if TYPE_CHECKING:
    from pykotor.resource.formats.tpc import TPC
    from utility.common.stream import SOURCE_TYPES


def _make_transform(pos: LPoint3, quat: LQuaternion) -> LMatrix4:
    """Create a transform matrix from position and rotation."""
    transform = LMatrix4()
    transform_state = TransformState.makePosQuatScale(pos, quat, LPoint3(1, 1, 1))
    transform.assign(transform_state.getMat())
    return transform


def load_mdl(mdl: SOURCE_TYPES, mdx: SOURCE_TYPES) -> NodePath:
    """Load a KotOR MDL/MDX pair into a Panda3D NodePath."""
    mdl_reader = BinaryReader.from_auto(mdl)
    mdx_reader = BinaryReader.from_auto(mdx)

    # Read header
    mdl_reader.seek(40)
    offset = mdl_reader.read_uint32()

    # Read names
    mdl_reader.seek(184)
    offset_to_name_offsets = mdl_reader.read_uint32()
    name_count = mdl_reader.read_uint32()

    mdl_reader.seek(offset_to_name_offsets)
    name_offsets = [mdl_reader.read_uint32() for _ in range(name_count)]
    names: list[str] = []
    for name_offset in name_offsets:
        mdl_reader.seek(name_offset)
        names.append(mdl_reader.read_terminated_string("\0"))

    # Create root node
    root = NodePath("root")

    # Build list of nodes with meshes that will render
    offsets: list[tuple[int, LMatrix4]] = []
    search = [(offset, LMatrix4())]
    while search:
        offset, transform = search.pop()

        mdl_reader.seek(offset)
        node_type = mdl_reader.read_uint16()
        mdl_reader.read_uint16()  # supernode id
        name_list_index = mdl_reader.read_uint16()

        mdl_reader.seek(offset + 16)
        x = mdl_reader.read_single()
        y = mdl_reader.read_single()
        z = mdl_reader.read_single()
        qw = mdl_reader.read_single()
        qx = mdl_reader.read_single()
        qy = mdl_reader.read_single()
        qz = mdl_reader.read_single()

        # Update transform
        pos = LPoint3(x, y, z)
        quat = LQuaternion(qw, qx, qy, qz)
        local_transform = _make_transform(pos, quat)
        transform = transform * local_transform

        # Handle special nodes
        name = names[name_list_index].lower()
        if name in {"headhook", "rhand", "lhand", "gogglehook", "maskhook"}:
            node = root.attachNewNode(name)
            node.setMat(transform)

        # Read children
        child_offsets = mdl_reader.read_uint32()
        child_count = mdl_reader.read_uint32()
        for i in range(child_count):
            mdl_reader.seek(child_offsets + i * 4)
            offset_to_child = mdl_reader.read_uint32()
            search.append((offset_to_child, transform))

        # Check if this node has a renderable mesh
        walkmesh = bool(node_type & 0b1000000000)
        mesh = bool(node_type & 0b100000)
        if mesh and not walkmesh:
            mdl_reader.seek(offset + 80 + 313)
            render = mdl_reader.read_uint8()
            if render:
                offsets.append((offset, transform))

    # Group meshes by texture
    merged: dict[str, list[tuple[int, LMatrix4]]] = {}
    for offset, transform in offsets:
        mdl_reader.seek(offset + 80 + 88)
        texture = mdl_reader.read_terminated_string("\0", 32)
        lightmap = mdl_reader.read_terminated_string("\0", 32)
        key = texture + "\n" + lightmap
        if key not in merged:
            merged[key] = []
        merged[key].append((offset, transform))

    # Create merged meshes
    for key, value in merged.items():
        vertex_data = bytearray()
        elements: list[int] = []

        # Create a new NodePath for this mesh
        child = NodePath(GeomNode("mesh"))

        last_element = 0
        for offset, transform in value:
            mdl_reader.seek(offset + 80)
            fp = mdl_reader.read_uint32()
            k2 = fp in {4216880, 4216816, 4216864}

            mdl_reader.seek(offset + 80 + 252)
            mdx_block_size = mdl_reader.read_uint32()
            _mdx_data_bitflags = mdl_reader.read_uint32()
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

            # Read and transform vertices
            for i in range(vertex_count):
                mdx_reader.seek(mdx_offset + i * mdx_block_size + mdx_vertex_offset)
                x, y, z = struct.unpack("fff", mdx_reader.read_bytes(12))
                pos = transform.xformPoint(LPoint3(x, y, z))
                vertex_data += struct.pack("fff", pos.x, pos.y, pos.z)

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

        # Create geometry with proper format
        format_array = GeomVertexFormat.getV3n3t2()  # position, normal, texcoord
        vdata = GeomVertexData("mesh", format_array, Geom.UHStatic)
        vertex = GeomVertexWriter(vdata, "vertex")
        normal = GeomVertexWriter(vdata, "normal")
        texcoord = GeomVertexWriter(vdata, "texcoord")

        # Write vertex data
        vertex_count = len(vertex_data) // 40  # 40 = size of vertex (12 + 12 + 8 + 8)
        for i in range(vertex_count):
            base = i * 40

            # Position (x, y, z)
            x, y, z = struct.unpack("fff", vertex_data[base : base + 12])
            vertex.addData3(x, y, z)

            # Normal (nx, ny, nz)
            nx, ny, nz = struct.unpack("fff", vertex_data[base + 12 : base + 24])
            normal.addData3(nx, ny, nz)

            # Texture coords (u, v)
            u, v = struct.unpack("ff", vertex_data[base + 24 : base + 32])
            texcoord.addData2(u, v)

        # Create triangles
        prim = GeomTriangles(Geom.UHStatic)
        for i in range(0, len(elements), 3):
            prim.addVertices(elements[i], elements[i + 1], elements[i + 2])
        prim.closePrimitive()

        # Create geometry and attach to node
        geom = Geom(vdata)
        geom.addPrimitive(prim)
        geom_node = child.node()
        assert isinstance(geom_node, GeomNode)
        geom_node.addGeom(geom)

        # Store texture names and attach to root
        texture, lightmap = key.split("\n")
        child.setPythonTag("texture", texture)
        child.setPythonTag("lightmap", lightmap)
        child.reparentTo(root)

    return root


def load_tpc(tpc: TPC) -> Texture:
    """Load a KotOR TPC file into a Panda3D Texture."""
    mipmap = tpc.get(0, 0)
    tpc_format = tpc.format()

    # Create texture
    texture = Texture()

    # Convert compressed formats to uncompressed
    if tpc_format in {TPCTextureFormat.DXT1, TPCTextureFormat.DXT3, TPCTextureFormat.DXT5}:
        target_format = TPCTextureFormat.RGB if tpc_format == TPCTextureFormat.DXT1 else TPCTextureFormat.RGBA
        tpc.convert(target_format)
        mipmap = tpc.get(0, 0)
        tpc_format = target_format

    # Setup texture based on format and ensure data size matches expected size
    if tpc_format == TPCTextureFormat.RGB:
        expected_size = mipmap.width * mipmap.height * 3
        if len(mipmap.data) != expected_size:
            raise ValueError(f"Invalid RGB image data size. Expected {expected_size}, got {len(mipmap.data)}")
        texture.setup2dTexture(mipmap.width, mipmap.height, Texture.T_unsigned_byte, Texture.F_rgb)
        texture.setRamImage(mipmap.data)
    elif tpc_format == TPCTextureFormat.RGBA:
        expected_size = mipmap.width * mipmap.height * 4
        if len(mipmap.data) != expected_size:
            raise ValueError(f"Invalid RGBA image data size. Expected {expected_size}, got {len(mipmap.data)}")
        texture.setup2dTexture(mipmap.width, mipmap.height, Texture.T_unsigned_byte, Texture.F_rgba)
        texture.setRamImage(mipmap.data)
    elif tpc_format == TPCTextureFormat.BGR:
        expected_size = mipmap.width * mipmap.height * 3
        if len(mipmap.data) != expected_size:
            raise ValueError(f"Invalid BGR image data size. Expected {expected_size}, got {len(mipmap.data)}")
        texture.setup2dTexture(mipmap.width, mipmap.height, Texture.T_unsigned_byte, Texture.F_rgb)
        # Convert BGR to RGB
        converted = bytearray()
        for i in range(0, len(mipmap.data), 3):
            pixel = mipmap.data[i : i + 3]
            converted.extend(reversed(pixel))
        texture.setRamImage(bytes(converted))
    elif tpc_format == TPCTextureFormat.BGRA:
        expected_size = mipmap.width * mipmap.height * 4
        if len(mipmap.data) != expected_size:
            raise ValueError(f"Invalid BGRA image data size. Expected {expected_size}, got {len(mipmap.data)}")
        texture.setup2dTexture(mipmap.width, mipmap.height, Texture.T_unsigned_byte, Texture.F_rgba)
        # Convert BGRA to RGBA
        converted = bytearray()
        for i in range(0, len(mipmap.data), 4):
            pixel = mipmap.data[i : i + 4]
            converted.extend(reversed(pixel[:3]))  # Reverse BGR
            converted.append(pixel[3])  # Keep alpha
        texture.setRamImage(bytes(converted))
    elif tpc_format == TPCTextureFormat.Greyscale:
        expected_size = mipmap.width * mipmap.height
        if len(mipmap.data) != expected_size:
            raise ValueError(f"Invalid Greyscale image data size. Expected {expected_size}, got {len(mipmap.data)}")
        texture.setup2dTexture(mipmap.width, mipmap.height, Texture.T_unsigned_byte, Texture.F_luminance)
        texture.setRamImage(mipmap.data)
    else:
        # Default to RGBA
        texture.setup2dTexture(mipmap.width, mipmap.height, Texture.T_unsigned_byte, Texture.F_rgba)
        texture.setRamImage(mipmap.data)

    # Configure texture settings
    texture.setMagfilter(Texture.FT_linear)
    texture.setMinfilter(Texture.FT_linear_mipmap_linear)
    texture.setAnisotropicDegree(16)
    texture.setWrapU(Texture.WM_clamp)
    texture.setWrapV(Texture.WM_clamp)

    return texture
