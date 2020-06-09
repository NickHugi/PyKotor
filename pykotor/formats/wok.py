from __future__ import annotations

from enum import IntEnum
from typing import List, Union

from pykotor.data.vertex import Vertex
from pykotor.general.binary_reader import BinaryReader


class WalkmeshType(IntEnum):
    DoorOrPlaceable = 0
    Area = 1


class Material(IntEnum):
    Undefined = 0
    Dirt = 1
    Obscuring = 2
    Grass = 3
    Stone = 4
    Wood = 5
    Water = 6
    NonWalk = 7
    Transparent = 8
    Carpet = 9
    Metal = 10
    Puddles = 11
    Swamp = 12
    Mud = 13
    Leaves = 14
    Lava = 15
    BottomlessPit = 16
    DeepWater = 17
    Door = 18
    NonWalkGrass = 19
    Trigger = 30


class Face:
    def __init__(self):
        self.vertices: List[Vertex] = [Vertex(), Vertex(), Vertex()]
        self.material: Material = Material.Undefined
        self.adjacencies: List[Union[int, Face]] = [-1, -1, -1]


class WOK:
    @staticmethod
    def load_binary(data: bytes) -> WOK:
        return _WOKReader.load(data)

    @staticmethod
    def build_binary(self) -> bytes:
        return _WOKWriter.build(self)

    def __init__(self):
        self.walkmesh_type: WalkmeshType = WalkmeshType.Area
        self.position: Vertex = Vertex()
        self.faces: List[Face] = []


class _WOKReader:
    @staticmethod
    def load(data: bytes) -> WOK:
        reader = BinaryReader.from_data(data)
        wok = WOK()

        file_type = reader.read_string(4)
        file_version = reader.read_string(4)
        wok.walkmesh_type = WalkmeshType(reader.read_int32())
        reader.skip(48)

        vertex_count = reader.read_vertex()
        vertex_count = reader.read_uint32()
        vertices_offset = reader.read_uint32()
        face_count = reader.read_uint32()
        face_indices_offset = reader.read_uint32()
        face_materials_offset = reader.read_uint32()
        face_normals_offset = reader.read_uint32()
        face_distances_offset = reader.read_uint32()
        aabb_count = reader.read_uint32()
        aabbs_offset = reader.read_uint32()
        reader.skip(4)
        adjacency_count = reader.read_int32()
        adjacencies_offset = reader.read_int32()
        edge_count = reader.read_int32()
        edges_offset = reader.read_int32()
        perimeter_count = reader.read_int32()
        perimeters_offset = reader.read_int32()

        wok.faces = [Face() for _ in range(face_count)]

        vertices = []
        reader.seek(vertices_offset)
        for i in range(vertex_count):
            vertices.append(reader.read_vertex())

        reader.seek(face_indices_offset)
        for i in range(face_count):
            v1 = reader.read_uint32()
            v2 = reader.read_uint32()
            v3 = reader.read_uint32()
            wok.faces[i].vertices[0] = vertices[v1]
            wok.faces[i].vertices[1] = vertices[v2]
            wok.faces[i].vertices[2] = vertices[v3]

        reader.seek(face_materials_offset)
        for i in range(face_count):
            wok.faces[i].material = Material(reader.read_int32())

        reader.seek(edges_offset)
        for i in range(edge_count):
            edge_index = reader.read_int32()
            transition = reader.read_int32()
            face_index = edge_index // 3
            adjaceny_index = edge_index % 3
            if transition != -1:
                wok.faces[face_index].transitions[adjaceny_index] = transition

        return wok


class _WOKWriter:
    @staticmethod
    def build(wok: WOK) -> bytes:
        pass
        # TODO
