from __future__ import annotations

import math
from enum import IntEnum
from typing import List, Union, Optional, Tuple

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


class Axis(IntEnum):
    Invalid = 0
    PositiveX = 1
    PositiveY = 2
    PositiveZ = 4
    NegativeX = 8
    NegativeY = 16
    NegativeZ = 32


class AABB:
    def __init__(self):
        self.box_min: Vertex = Vertex()
        self.box_max: Vertex = Vertex()
        self.left_child: Optional[AABB] = None
        self.right_child: Optional[AABB] = None
        self.face: Optional[Face] = None
        self.most_significant_plane: Axis = Axis(0)


class Face:
    def __init__(self):
        self.vertices: List[Vertex] = [Vertex(), Vertex(), Vertex()]
        self.material: Material = Material.Undefined
        self.transitions: List[int] = [-1, -1, -1]

    def get_plane_distance(self) -> Vertex:
        pass
        # TODO

    def get_adjacenct_faces(self, face_list: List[Face]) -> List[Face]:
        pass
        # TODO

    def get_normal(self) -> Vertex:
        pass
        # TOODO

    def is_walkable(self) -> bool:
        if self.material == Material.NonWalk: return False
        if self.material == Material.Transparent: return False
        if self.material == Material.Lava: return False
        if self.material == Material.BottomlessPit: return False
        if self.material == Material.DeepWater: return False
        if self.material == Material.NonWalkGrass: return False
        return True

    def get_shared_vertices(self, other: Face) -> List[Vertex]:
        shared = []
        for self_vertex in self.vertices:
            for other_vertex in other.vertices:
                if self_vertex == other_vertex and self_vertex not in shared:
                    shared.append(self_vertex)
        return shared

    def get_face_center(self) -> Vertex:
        vertex = Vertex()
        vertex.x = (self.vertices[0].x + self.vertices[1].x + self.vertices[2].x) / 3
        vertex.y = (self.vertices[0].y + self.vertices[1].y + self.vertices[2].y) / 3
        vertex.z = (self.vertices[0].z + self.vertices[1].z + self.vertices[2].z) / 3
        return vertex

    def index_in(self, face_list: List[Face]) -> int:
        return face_list.index(self)


class WOK:
    @staticmethod
    def load_binary(data: bytes) -> WOK:
        return _WOKReader.load(data)

    def build_binary(self) -> bytes:
        return _WOKWriter.build(self)

    def __init__(self):
        self.walkmesh_type: WalkmeshType = WalkmeshType.Area
        self.position: Vertex = Vertex()
        self.faces: List[Face] = []

    def _sort_faces(self) -> None:
        for i, face in enumerate(self.faces):
            if face.is_walkable():
                self.faces.remove(face)
                self.faces.insert(0, face)

    def get_vertices(self) -> List[Vertex]:
        vertices = []
        for face in self.faces:
            for vertex in face.vertices:
                # avoid redundancies
                if vertex not in vertices:
                    vertices.append(vertex)
        return vertices

    def get_edges(self):
        unvisited_faces = []
        for face in self.faces:
            if face.is_walkable():
                unvisited_faces.append(face)

        edge_indices = []
        edge_transitions = []
        perimeters = []

        while len(unvisited_faces) > 0:
            self._get_edges_rec(unvisited_faces, unvisited_faces[0], edge_indices, edge_transitions)
            perimeters.append(len(edge_indices))

        return edge_indices, edge_transitions, perimeters

    def _get_edges_rec(self, unvisited_faces, face, edge_indices, edge_transitions):
        unvisited_faces.remove(face)
        adjacent_faces = face.get_adjacenct_faces()
        for i, adjacent in enumerate(adjacent_faces):
            if adjacent is None:
                edge_indices.append(self.faces.index(face) * 3 + i)
                edge_transitions.append(face.transitions[i])
            elif adjacent in unvisited_faces:  # or is not None: (implicit)
                self._get_edges_rec(unvisited_faces, adjacent, edge_indices, edge_transitions)

    def get_aabbs(self) -> List[AABB]:
        aabb_list = []
        faces = self.faces.copy()
        self._get_aabbs_rec(aabb_list, AABB(), faces)
        return aabb_list

    def _get_aabbs_rec(self, aabb_list, aabb, faces):
        aabb_list.append(aabb)
        aabb.box_min, aabb.box_max = self.get_bounding_box(self.faces)
        aabb.most_significant_plane = Axis(0)

        if len(faces) > 1:
            best_axis = self._find_best_axis(aabb.box_min, aabb.box_max)
            split_point, faces = self._find_best_split_order(best_axis, faces)

            left_faces = faces[:split_point + 1]
            right_faces = faces[split_point + 1:]

            if len(left_faces) > 0:
                aabb.left_child = AABB()
                self._get_aabbs_rec(aabb_list, aabb.left_child, left_faces)
            else:
                aabb.left_child = None

            if len(right_faces) > 0:
                aabb.right_child = AABB()
                self._get_aabbs_rec(aabb_list, aabb.right_child, right_faces)
            else:
                aabb.right_child = None
        else:
            aabb.left_child = None
            aabb.right_child = None
            aabb.face = faces[0]
            aabb.most_significant_plane = Axis(0)

    def get_bounding_box(self, faces) -> Tuple[Vertex, Vertex]:
        box_min = Vertex.from_position(1000000, 1000000, 1000000)
        box_max = Vertex.from_position(-1000000, -1000000, -1000000)

        for face in faces:
            for vertex in face.vertices:
                if vertex.x < box_min.x:
                    box_min.x = vertex.x
                if vertex.x > box_max.x:
                    box_max.x = vertex.x
                if vertex.y < box_min.y:
                    box_min.y = vertex.y
                if vertex.y > box_max.y:
                    box_max.y = vertex.y
                if vertex.z < box_min.y:
                    box_min.z = vertex.z
                if vertex.z > box_max.z:
                    box_max.z = vertex.z

        box_min.x -= 0.01
        box_min.y -= 0.01
        box_min.z -= 0.01

        box_max.x += 0.01
        box_max.y += 0.01
        box_max.z += 0.01

        return box_min, box_max

    def _find_best_axis(self, box_min, box_max):
        axis_result = [0.0] * 3
        axis_best_result = 0.0
        best_axis = 0

        axis_result[0] = math.fabs(box_max.x - box_min.x)
        axis_result[1] = math.fabs(box_max.y - box_min.y)
        axis_result[2] = math.fabs(box_max.z - box_min.z)

        axis_best_result = math.fabs(axis_result[0])
        for i in range(3):
            if math.fabs(axis_result[i]) >= axis_best_result:
                axis_best_result = math.fabs(axis_result[i])
                best_axis = i

        return best_axis

    def _find_best_split_order(self, axis, faces):
        if len(faces) <= 1:
            return 0

        sort_coords = []
        for i in range(len(faces)):
            sort_coords = self._get_face_center(faces[i])[axis]

        sorted_faces = faces.copy()
        sorted_faces = sorted(sorted_faces, key=lambda k: sort_coords)
        # TODO sorted_faces = sorted_faces.sort(lambda k: sort_coords[k])

        split_index = math.floor(len(faces) / 2) - 1
        if split_index < 0:
            split_index = 0

        return split_index, sorted_faces

    def _get_face_center(self, face):
        result = []
        result.append((face.vertices[0].x + face.vertices[1].x + face.vertices[2].x) / 3)
        result.append((face.vertices[0].y + face.vertices[1].y + face.vertices[2].y) / 3)
        result.append((face.vertices[0].z + face.vertices[1].z + face.vertices[2].z) / 3)
        return result



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
