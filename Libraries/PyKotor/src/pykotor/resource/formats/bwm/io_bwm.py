"""
Binary reader/writer for KotOR walkmeshes (BWM/WOK).

This module translates between on-disk WOK/BWM files and the in-memory BWM model
defined in `bwm_data.py`. The binary layout mirrors the game's expectations:

- Header:  "BWM " + "V1.0"
- Walkmesh properties (type, hooks, position)
- Vertex array (float32 triplets)
- Face indices (uint32 triplets into the vertex array)
- Materials per face (uint32 SurfaceMaterial id)
- Face normals (float32 triplets)
- Planar distances (float32 per face)
- AABB nodes (bounds, face index or 0xFFFFFFFF, split plane, children)
- Walkable adjacencies (3 ints per walkable face; -1 for no neighbor)
- Edges (pairs of (edge_index, transition) where edge_index = face*3 + edge)
- Perimeters (1-based indices into the edge array for edges with final=True)

Important
---------
Where faces or vertices must be converted to indices, we find indices by object
identity (the `is` operator), not value equality, to avoid collisions when value
equality is true for different objects. This complements the value-based
`__eq__`/`__hash__` used for comparisons on faces/vertices.
"""

from __future__ import annotations

import struct

from typing import TYPE_CHECKING

from pykotor.resource.formats.bwm.bwm_data import BWM, BWMFace, BWMType  # noqa: E402
from pykotor.resource.type import ResourceReader, ResourceWriter, autoclose  # noqa: E402
from utility.common.geometry import SurfaceMaterial, Vector3  # noqa: E402

if TYPE_CHECKING:
    from pykotor.resource.formats.bwm.bwm_data import BWMAdjacency, BWMEdge, BWMNodeAABB
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class BWMBinaryReader(ResourceReader):
    """Reads BWM/WOK (Walkmesh) files.
    
    Walkmesh files define collision geometry for areas, including walkable surfaces,
    adjacencies, AABB trees for spatial queries, and edge transitions.
    
    References:
    ----------
        vendor/reone/src/libs/graphics/format/bwmreader.cpp (BWM reading)
    """
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        """Initializes a walkmesh reader (WOK/BWM).

        Args:
        ----
            source: {The source object to initialize from}
            offset: {The offset into the source}
            size: {The number of bytes to read from the source}.

        Returns:
        -------
            self: {The initialized Wok object}

        Processing Logic:
        ----------------
            - Initializes the superclass with the given source, offset and size
            - Sets the wok attribute to None
            - Initializes the position, relative and absolute hook vectors to null vectors
            - Sets up the instance attributes.
        """
        super().__init__(source, offset, size)
        self._wok: BWM | None = None
        self.position: Vector3 = Vector3.from_null()
        self.relative_hook1: Vector3 = Vector3.from_null()
        self.relative_hook2: Vector3 = Vector3.from_null()
        self.absolute_hook1: Vector3 = Vector3.from_null()
        self.absolute_hook2: Vector3 = Vector3.from_null()

    @autoclose
    def load(self, *, auto_close: bool = True) -> BWM:  # noqa: FBT001, FBT002, ARG002
        """Loads a WOK/BWM binary file into a BWM instance.

        Args:
        ----
            self: The BWMReader object
            auto_close: Whether to automatically close the file after loading

        Returns:
        -------
            BWM: The loaded BWM object

        Processing Logic:
        ----------------
            - Validates header and version
            - Reads properties, vertices, face indices, materials
            - Applies per-edge transitions to faces
            - Populates BWM.faces
        """
        self._wok = BWM()

        file_type = self._reader.read_string(4)
        file_version = self._reader.read_string(4)

        if file_type != "BWM ":
            msg = f"Not a valid binary BWM file. Expected 'BWM ', got '{file_type}' (hex: {file_type.encode('latin1').hex()})"
            raise ValueError(msg)

        if file_version != "V1.0":
            msg = f"Unsupported BWM version: got '{file_version}', expected 'V1.0'"
            raise ValueError(msg)

        self._wok.walkmesh_type = BWMType(self._reader.read_uint32())
        self._wok.relative_hook1 = self._reader.read_vector3()
        self._wok.relative_hook2 = self._reader.read_vector3()
        self._wok.absolute_hook1 = self._reader.read_vector3()
        self._wok.absolute_hook2 = self._reader.read_vector3()
        self._wok.position = self._reader.read_vector3()

        vertices_count = self._reader.read_uint32()
        vertices_offset = self._reader.read_uint32()
        face_count = self._reader.read_uint32()
        indices_offset = self._reader.read_uint32()
        materials_offset = self._reader.read_uint32()
        self._reader.read_uint32()  # normals_offset
        self._reader.read_uint32()  # planar_distances_offset

        self._reader.read_uint32()  # aabb_count
        self._reader.read_uint32()  # aabb_offset
        self._reader.skip(4)
        self._reader.read_uint32()  # adjacencies_count
        self._reader.read_uint32()  # adjacencies_offset
        edges_count = self._reader.read_uint32()
        edges_offset = self._reader.read_uint32()
        self._reader.read_uint32()  # perimeters_count
        self._reader.read_uint32()  # perimeters_offset

        self._reader.seek(vertices_offset)
        vertices = [self._reader.read_vector3() for _ in range(vertices_count)]
        faces: list[BWMFace] = []
        self._reader.seek(indices_offset)
        for _ in range(face_count):
            i1, i2, i3 = (
                self._reader.read_uint32(),
                self._reader.read_uint32(),
                self._reader.read_uint32(),
            )
            v1, v2, v3 = vertices[i1], vertices[i2], vertices[i3]
            faces.append(BWMFace(v1, v2, v3))

        walkable_count = 0
        self._reader.seek(materials_offset)
        for face in faces:
            material_id = self._reader.read_uint32()
            face.material = SurfaceMaterial(material_id)
            if face.material.walkable():
                walkable_count += 1

        self._reader.seek(edges_offset)
        x: list[int] = []
        for _ in range(edges_count):
            edge_index = self._reader.read_uint32()
            x.append(edge_index)
            transition = self._reader.read_uint32()

            if transition != 0xFFFFFFFF:
                face_index = edge_index // 3
                trans_index = edge_index % 3
                if trans_index == 0:
                    faces[face_index].trans1 = transition
                elif trans_index == 1:
                    faces[face_index].trans2 = transition
                elif trans_index == 2:
                    faces[face_index].trans3 = transition

        self._wok.faces = faces

        return self._wok


class BWMBinaryWriter(ResourceWriter):
    HEADER_SIZE = 136

    def __init__(
        self,
        wok: BWM,
        target: TARGET_TYPES,
    ):
        super().__init__(target)
        self._wok: BWM = wok

    @autoclose
    def write(self, *, auto_close: bool = True):  # noqa: FBT001, FBT002, ARG002  # pyright: ignore[reportUnusedParameters]
        """Writes a BWM instance to WOK/BWM binary format.

        Args:
        ----
            self: The walkmesh object
            auto_close: Whether to close the file after writing (default: True).

        Processing Logic:
        ----------------
            1. Extracts vertex, face, edge and metadata from the walkmesh
            2. Packs sections and computes offsets
            3. Writes header, counts and offsets, followed by section data
        """
        vertices: list[Vector3] = self._wok.vertices()

        walkable: list[BWMFace] = [face for face in self._wok.faces if face.material.walkable()]
        unwalkable: list[BWMFace] = [face for face in self._wok.faces if not face.material.walkable()]
        faces: list[BWMFace] = walkable + unwalkable
        aabbs: list[BWMNodeAABB] = self._wok.aabbs()

        vertex_offset = 136
        vertex_data = bytearray()
        for vertex in vertices:
            vertex_data += struct.pack("fff", vertex.x, vertex.y, vertex.z)

        indices_offset = vertex_offset + len(vertex_data)
        indices_data = bytearray()
        for face in faces:
            # Find vertex indices by object identity
            i1 = next(i for i, v in enumerate(vertices) if v is face.v1)
            i2 = next(i for i, v in enumerate(vertices) if v is face.v2)
            i3 = next(i for i, v in enumerate(vertices) if v is face.v3)
            indices_data += struct.pack("III", i1, i2, i3)

        material_offset = indices_offset + len(indices_data)
        material_data = bytearray()
        for face in faces:
            material_data += struct.pack("I", face.material.value)

        normal_offset = material_offset + len(material_data)
        normal_data = bytearray()
        for face in faces:
            normal = face.normal()
            normal_data += struct.pack("fff", normal.x, normal.y, normal.z)

        coefficient_offset = normal_offset + len(normal_data)
        coeffeicent_data = bytearray()
        for face in faces:
            coeffeicent_data += struct.pack("f", face.planar_distance())

        aabb_offset = coefficient_offset + len(coeffeicent_data)
        aabb_data = bytearray()
        for aabb in aabbs:
            aabb_data += struct.pack("fff", aabb.bb_min.x, aabb.bb_min.y, aabb.bb_min.z)
            aabb_data += struct.pack("fff", aabb.bb_max.x, aabb.bb_max.y, aabb.bb_max.z)
            # Find face index by object identity
            face_idx = 0xFFFFFFFF if aabb.face is None else next(i for i, f in enumerate(faces) if f is aabb.face)
            aabb_data += struct.pack("I", face_idx)
            aabb_data += struct.pack("I", 4)
            aabb_data += struct.pack("I", aabb.sigplane.value)
            # Find AABB indices by object identity
            left_idx = 0xFFFFFFFF if aabb.left is None else next(i for i, a in enumerate(aabbs) if a is aabb.left) + 1
            right_idx = 0xFFFFFFFF if aabb.right is None else next(i for i, a in enumerate(aabbs) if a is aabb.right) + 1
            aabb_data += struct.pack("I", left_idx)
            aabb_data += struct.pack("I", right_idx)

        adjacency_offset = aabb_offset + len(aabb_data)
        adjacency_data = bytearray()
        for face in walkable:
            adjancencies: tuple[BWMAdjacency | None, BWMAdjacency | None, BWMAdjacency | None] = self._wok.adjacencies(face)
            indexes: list[int] = []
            for adjacency in adjancencies:
                if adjacency is None:
                    indexes.append(-1)
                else:
                    # Find face index by object identity
                    idx = next(i for i, f in enumerate(faces) if f is adjacency.face)
                    indexes.append(idx * 3 + adjacency.edge)
            adjacency_data += struct.pack("iii", *indexes)

        edges: list[BWMEdge] = self._wok.edges()
        edge_data = bytearray()
        edge_offset = adjacency_offset + len(adjacency_data)
        for edge in edges:
            # Find face index by object identity
            face_idx = next(i for i, f in enumerate(faces) if f is edge.face)
            edge_index = face_idx * 3 + edge.index
            edge_data += struct.pack("ii", edge_index, edge.transition)

        # Find edge indices by object identity for perimeters
        perimeters: list[int] = [next(i for i, e in enumerate(edges) if e is edge) + 1 for edge in edges if edge.final]
        perimeter_data = bytearray()
        perimeter_offset = edge_offset + len(edge_data)
        for perimeter in perimeters:
            perimeter_data += struct.pack("I", perimeter)

        self._writer.write_string("BWM V1.0")
        self._writer.write_uint32(self._wok.walkmesh_type.value)
        self._writer.write_vector3(self._wok.relative_hook1)
        self._writer.write_vector3(self._wok.relative_hook2)
        self._writer.write_vector3(self._wok.absolute_hook1)
        self._writer.write_vector3(self._wok.absolute_hook2)
        self._writer.write_vector3(self._wok.position)

        self._writer.write_uint32(len(vertices))
        self._writer.write_uint32(vertex_offset)
        self._writer.write_uint32(len(faces))
        self._writer.write_uint32(indices_offset)
        self._writer.write_uint32(material_offset)
        self._writer.write_uint32(normal_offset)
        self._writer.write_uint32(coefficient_offset)
        self._writer.write_uint32(len(aabbs))
        self._writer.write_uint32(aabb_offset)
        self._writer.write_uint32(0)
        self._writer.write_uint32(len(self._wok.walkable_faces()))
        self._writer.write_uint32(adjacency_offset)
        self._writer.write_uint32(len(edges))
        self._writer.write_uint32(edge_offset)
        self._writer.write_uint32(len(perimeters))
        self._writer.write_uint32(perimeter_offset)

        self._writer.write_bytes(vertex_data)
        self._writer.write_bytes(indices_data)
        self._writer.write_bytes(material_data)
        self._writer.write_bytes(normal_data)
        self._writer.write_bytes(coeffeicent_data)
        self._writer.write_bytes(aabb_data)
        self._writer.write_bytes(adjacency_data)
        self._writer.write_bytes(edge_data)
        self._writer.write_bytes(perimeter_data)
