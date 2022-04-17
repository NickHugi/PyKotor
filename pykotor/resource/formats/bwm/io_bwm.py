from __future__ import annotations

import struct
from typing import Optional

from pykotor.common.geometry import Vector3, SurfaceMaterial
from pykotor.resource.formats.bwm import BWM, BWMFace, BWMType
from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES, ResourceReader, ResourceWriter, autoclose


class BWMBinaryReader(ResourceReader):
    def __init__(
            self,
            source: SOURCE_TYPES,
            offset: int = 0,
            size: int = 0
    ):
        super().__init__(source, offset, size)
        self._wok: Optional[BWM] = None
        self.position: Vector3 = Vector3.from_null()
        self.relative_hook1: Vector3 = Vector3.from_null()
        self.relative_hook2: Vector3 = Vector3.from_null()
        self.absolute_hook1: Vector3 = Vector3.from_null()
        self.absolute_hook2: Vector3 = Vector3.from_null()

    @autoclose
    def load(
            self,
            auto_close: bool = True
    ) -> BWM:
        self._wok = BWM()

        file_type = self._reader.read_string(4)
        file_version = self._reader.read_string(4)

        if file_type != "BWM ":
            raise ValueError("Not a valid binary BWM file.")

        if file_version != "V1.0":
            raise ValueError("The BWM version of the file is unsupported.")

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
        normals_offset = self._reader.read_uint32()
        planar_distances_offset = self._reader.read_uint32()

        aabb_count = self._reader.read_uint32()
        aabb_offset = self._reader.read_uint32()
        self._reader.skip(4)
        adjacencies_count = self._reader.read_uint32()
        adjacencies_offset = self._reader.read_uint32()
        edges_count = self._reader.read_uint32()
        edges_offset = self._reader.read_uint32()
        perimeters_count = self._reader.read_uint32()
        perimeters_offset = self._reader.read_uint32()

        vertices = []
        self._reader.seek(vertices_offset)
        for i in range(vertices_count):
            vertices.append(self._reader.read_vector3())

        faces = []
        self._reader.seek(indices_offset)
        for i in range(face_count):
            i1, i2, i3 = self._reader.read_uint32(), self._reader.read_uint32(), self._reader.read_uint32()
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
        x = []
        for i in range(edges_count):
            edge_index = self._reader.read_uint32()
            x.append(edge_index)
            transition = self._reader.read_uint32()

            if transition != 0xFFFFFFFF:
                face_index = edge_index // 3
                trans_index = edge_index % 3
                if trans_index == 0:
                    faces[face_index].trans1 = transition
                if trans_index == 1:
                    faces[face_index].trans2 = transition
                if trans_index == 2:
                    faces[face_index].trans3 = transition

        self._wok.faces = faces

        return self._wok


class BWMBinaryWriter(ResourceWriter):
    HEADER_SIZE = 136

    def __init__(
            self,
            wok: BWM,
            target: TARGET_TYPES
    ):
        super().__init__(target)
        self._wok: BWM = wok

    @autoclose
    def write(
            self,
            auto_close: bool = True
    ) -> None:
        vertices = self._wok.vertices()

        walkable = [face for face in self._wok.faces if face.material.walkable()]
        unwalkable = [face for face in self._wok.faces if not face.material.walkable()]
        faces = walkable + unwalkable
        aabbs = self._wok.aabbs()

        vertex_offset = 136
        vertex_data = bytearray()
        for vertex in vertices:
            vertex_data += struct.pack("fff", vertex.x, vertex.y, vertex.z)

        indices_offset = vertex_offset + len(vertex_data)
        indices_data = bytearray()
        for face in faces:
            i1, i2, i3 = vertices.index(face.v1), vertices.index(face.v2), vertices.index(face.v3)
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
            aabb_data += struct.pack("I", faces.index(aabb.face) if aabb.face is not None else 0xFFFFFFFF)
            aabb_data += struct.pack("I", 4)
            aabb_data += struct.pack("I", aabb.sigplane.value)
            aabb_data += struct.pack("I", aabbs.index(aabb.left) + 1 if aabb.left is not None else 0xFFFFFFFF)
            aabb_data += struct.pack("I", aabbs.index(aabb.right) + 1 if aabb.right is not None else 0xFFFFFFFF)

        adjacency_offset = aabb_offset + len(aabb_data)
        adjacency_data = bytearray()
        for face in walkable:
            adjancencies = self._wok.adjacencies(face)
            indexes = []
            for adjacency in adjancencies:
                indexes.append(faces.index(adjacency.face) * 3 + adjacency.edge if adjacency is not None else -1)
            adjacency_data += struct.pack("iii", *indexes)

        edges = self._wok.edges()
        edge_data = bytearray()
        edge_offset = adjacency_offset + len(adjacency_data)
        for edge in edges:
            edge_index = faces.index(edge.face) * 3 + edge.index
            edge_data += struct.pack("ii", edge_index, edge.transition)

        perimeters = [edges.index(edge) + 1 for edge in edges if edge.final]
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
