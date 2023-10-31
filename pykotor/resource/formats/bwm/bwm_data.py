from __future__ import annotations

import itertools
import math
from copy import copy
from enum import IntEnum

from pykotor.common.geometry import Face, Vector3

# A lot of the code in this module was adapted from the KotorBlender fork by seedhartha:
# https://github.com/seedhartha/kotorblender

class BWMType(IntEnum):
    PlaceableOrDoor = 0
    AreaModel = 1


class BWM:
    """Represents the data of a RIM file."""

    def __init__(
        self,
    ):
        self.walkmesh_type: BWMType = BWMType.AreaModel
        self.faces: list[BWMFace] = []

        self.position: Vector3 = Vector3.from_null()
        self.relative_hook1: Vector3 = Vector3.from_null()
        self.relative_hook2: Vector3 = Vector3.from_null()
        self.absolute_hook1: Vector3 = Vector3.from_null()
        self.absolute_hook2: Vector3 = Vector3.from_null()

    def walkable_faces(
        self,
    ):
        return [face for face in self.faces if face.material.walkable()]

    def unwalkable_faces(
        self,
    ):
        return [face for face in self.faces if not face.material.walkable()]

    def vertices(
        self,
    ) -> list[Vector3]:
        """Returns a list of vectors stored in the faces of the walkmesh.

        Returns
        -------
            A list of Vector3 objects.
        """
        vertices: list[Vector3] = []
        for face in self.faces:
            if not face.v1.within(vertices):
                vertices.append(face.v1)
            if not face.v2.within(vertices):
                vertices.append(face.v2)
            if not face.v3.within(vertices):
                vertices.append(face.v3)
        return vertices

    def aabbs(
        self,
    ) -> list[BWMNodeAABB]:
        aabbs: list[BWMNodeAABB] = []
        self._aabbs_rec(aabbs, copy(self.faces))
        return aabbs

    def _aabbs_rec(
        self,
        aabbs: list[BWMNodeAABB],
        faces: list[BWMFace],
        rlevel=0,
    ) -> None:

        max_rlevel = 128
        if rlevel > max_rlevel:
            msg = f"rlevel must not exceed {max_rlevel}, but is equal to {rlevel}"
            raise ValueError(msg)

        if not faces:
            msg = "face_list must not be empty"
            raise ValueError(msg)

        # Calculate bounding box
        bbmin, bbmax, bbcentre = self._calculate_bounding_box(faces)

        # Only one face left - this node is a leaf
        if len(faces) == 1:
            self._create_leaf_node(aabbs, bbmin, bbmax, faces[0])
            return

        # Find longest axis
        split_axis = self._find_longest_axis(bbmin, bbmax)

        # Change axis in case points are coplanar with the split plane
        if self._is_coplanar(faces, split_axis, bbcentre):
            split_axis = self._get_next_axis(split_axis)

        # Split faces along axis
        faces_left, faces_right = self._split_faces(faces, split_axis, bbcentre)

        if not faces_left or not faces_right:
            msg = "Generated tree is degenerate"
            raise RuntimeError(msg)

        # Create node and recurse
        _aabb = self._create_node(aabbs, bbmin, bbmax, split_axis)
        self._aabbs_rec(aabbs, faces_left, rlevel + 1)
        self._aabbs_rec(aabbs, faces_right, rlevel + 1)


    def _calculate_bounding_box(self, faces):
        bbmin = Vector3(100000, 100000, 100000)
        bbmax = Vector3(-100000, -100000, -100000)
        bbcentre = Vector3.from_null()

        for face in faces:
            self._update_bounds(face, bbmin, bbmax, bbcentre)

        bbcentre = bbcentre / len(faces)
        return bbmin, bbmax, bbcentre

    def _update_bounds(self, face, bbmin, bbmax, bbcentre):
        for vertex in [face.v1, face.v2, face.v3]:
            for axis in range(3):
                bbmin[axis] = min(bbmin[axis], vertex[axis]) 
                bbmax[axis] = max(bbmax[axis], vertex[axis])
        bbcentre += face.centre()

    def _find_longest_axis(self, bbmin, bbmax):
        bb_size = bbmax - bbmin
        if bb_size.y > bb_size.x:
            return 1
        if bb_size.z > bb_size.y:
            return 2
        return 0

    def _is_coplanar(self, faces, axis, bbcentre):
        return all(face.centre()[axis] == bbcentre[axis] for face in faces)

    def _get_next_axis(self, axis):
        return 0 if axis == 2 else axis + 1

    def _split_faces(self, faces, axis, bbcentre):
        left = []
        right = []
        for face in faces:
            centre = face.centre()
            if centre[axis] < bbcentre[axis]:
                left.append(face)
            else:
                right.append(face)
        return left, right

    def _create_leaf_node(self, aabbs: list, bbmin, bbmax, face):
        aabbs.append(BWMNodeAABB(bbmin, bbmax, face, 0, None, None))

    def _create_node(self, aabbs: list, bbmin, bbmax, axis):
        aabb = BWMNodeAABB(bbmin, bbmax, None, axis + 1, None, None)
        aabbs.append(aabb)
        return aabb

    def edges(self) -> list[BWMEdge]:
        walkable_faces = self.filter_walkable_faces()
        adjacencies: list[tuple[BWMAdjacency, BWMAdjacency, BWMAdjacency]] = [self.adjacencies(face) for face in walkable_faces]

        visited = set()
        edges = []

        for face_index, edge_index in itertools.product(range(len(walkable_faces)), range(3)):
            self.process_edge(face_index, edge_index, adjacencies, visited, edges)

        return edges

    def filter_walkable_faces(self) -> list[Face]:
        return [face for face in self.faces if face.material.walkable()]

    def process_edge(
            self,
            face_index: int,
            edge_index: int,
            adjacencies: list[tuple[BWMAdjacency, BWMAdjacency, BWMAdjacency]],
            visited: set[int],
            edges: list[BWMEdge]
        ):
        if adjacencies[face_index][edge_index] is not None:
            return

        current_edge_index = face_index * 3 + edge_index
        if current_edge_index in visited:
            return

        next_face = face_index
        next_edge = edge_index
        while next_face != -1:
            next_face, next_edge = self.process_adjacency(next_face, next_edge, adjacencies, visited, edges)

    def process_adjacency(
            self,
            next_face: int,
            next_edge: int,
            adjacencies: list[tuple[BWMAdjacency, BWMAdjacency, BWMAdjacency]],
            visited: set[int],
            edges: list[BWMEdge]
        ) -> tuple[int, int]:
        adj_edge = adjacencies[next_face][next_edge]
        adj_edge_index = self.faces.index(adj_edge.face) * 3 + adj_edge.edge if adj_edge is not None else -1

        if adj_edge is None:
            edge_index = 3 * next_face + next_edge
            if edge_index not in visited:
                transition = self.get_transition(next_face, next_edge)

                edges.append(BWMEdge(self.faces[next_face], next_edge, transition or -1))
                visited.add(edge_index)

                next_edge = (next_edge + 1) % 3
            else:
                next_face = -1

        else:
            next_face = adj_edge_index // 3
            next_edge = ((adj_edge_index % 3) + 1) % 3

        return next_face, next_edge

    def get_transition(self, face_index: int, edge_index: int) -> int:
        face = self.faces[face_index]
        transitions = [face.trans1, face.trans2, face.trans3]
        return transitions[edge_index] or -1

    def adjacencies(
        self,
        face: BWMFace,
    ) -> tuple[BWMAdjacency, BWMAdjacency, BWMAdjacency]:
        walkable = self.walkable_faces()

        adj1 = [face.v1, face.v2]
        adj2 = [face.v2, face.v3]
        adj3 = [face.v3, face.v1]

        adj_index1 = None
        adj_index2 = None
        adj_index3 = None

        def matches(
            face_index,
            edges,
        ):
            flag = 0x00
            other_face = self.faces[face_index]
            if other_face.v1 in edges:
                flag += 0x01
            if other_face.v2 in edges:
                flag += 0x02
            if other_face.v3 in edges:
                flag += 0x04
            edge = -1
            if flag == 0x03:
                edge = 0
            if flag == 0x06:
                edge = 1
            if flag == 0x05:
                edge = 2
            return edge

        for other in walkable:
            if other is face:
                continue
            other_index = walkable.index(other)
            if matches(other_index, adj1) != -1:
                adj_index1 = BWMAdjacency(
                    walkable[other_index],
                    matches(other_index, adj1),
                )
            if matches(other_index, adj2) != -1:
                adj_index2 = BWMAdjacency(
                    walkable[other_index],
                    matches(other_index, adj2),
                )
            if matches(other_index, adj3) != -1:
                adj_index3 = BWMAdjacency(
                    walkable[other_index],
                    matches(other_index, adj3),
                )

        return adj_index1, adj_index2, adj_index3

    def box(
        self,
    ) -> tuple[Vector3, Vector3]:
        bbmin = Vector3(1000000, 1000000, 1000000)
        bbmax = Vector3(-1000000, -1000000, -1000000)
        for vertex in self.vertices():
            self._set_coords_to_bounds(bbmin, vertex, bbmax)
        return bbmin, bbmax

    def _set_coords_to_bounds(self, bbmin, vertex, bbmax):
        bbmin.x = min(bbmin.x, vertex.x)
        bbmin.y = min(bbmin.y, vertex.y)
        bbmin.z = min(bbmin.z, vertex.z)
        bbmax.x = max(bbmax.x, vertex.x)
        bbmax.y = max(bbmax.y, vertex.y)
        bbmax.z = max(bbmax.z, vertex.z)

    def faceAt(
        self,
        x: float,
        y: float,
    ) -> BWMFace | None:
        """Returns the face at the given 2D coordinates if there si one otherwise returns None.

        Args:
        ----
            x: The x coordinate.
            y: The y coordinate.

        Returns:
        -------
            BWMFace object or None.
        """
        for face in self.faces:
            v1 = face.v1
            v2 = face.v2
            v3 = face.v3

            # Formula taken from: https://www.w3resource.com/python-exercises/basic/python-basic-1-exercise-40.php
            c1 = (v2.x - v1.x) * (y - v1.y) - (v2.y - v1.y) * (x - v1.x)
            c2 = (v3.x - v2.x) * (y - v2.y) - (v3.y - v2.y) * (x - v2.x)
            c3 = (v1.x - v3.x) * (y - v3.y) - (v1.y - v3.y) * (x - v3.x)

            if (c1 < 0 and c2 < 0 and c3 < 0) or (c1 > 0 and c2 > 0 and c3 > 0):
                return face
        return None

    def translate(
        self,
        x: float,
        y: float,
        z: float,
    ) -> None:
        """Shifts the position of the walkmesh.

        Args:
        ----
            x: How many units to shift on the X-axis.
            y: How many units to shift on the Y-axis.
            z: How many units to shift on the Z-axis.
        """
        for vertex in self.vertices():
            vertex.x += x
            vertex.y += y
            vertex.z += z

    def rotate(
        self,
        degrees: float,
    ) -> None:
        """Rotates the walkmesh around the Z-axis counter-clockwise.

        Args:
        ----
            degrees: The angle to rotate in degrees.
        """
        radians = math.radians(degrees)
        cos = math.cos(radians)
        sin = math.sin(radians)

        for vertex in self.vertices():
            x, y = vertex.x, vertex.y
            vertex.x = x * cos - y * sin
            vertex.y = x * sin + y * cos

    def change_lyt_indexes(
        self,
        old: int,
        new: int | None,
    ) -> None:
        for face in self.faces:
            if face.trans1 == old:
                face.trans1 = new
            if face.trans2 == old:
                face.trans2 = new
            if face.trans2 == old:
                face.trans2 = new

    def flip(
        self,
        x: bool,
        y: bool,
    ) -> None:
        """Flips the walkmesh around the specified axes.

        Args:
        ----
            x: Flip around the X-axis.
            y: Flip around the Y-axis.
        """
        if not x and not y:
            return

        for vertex in self.vertices():
            if x:
                vertex.x = -vertex.x
            if y:
                vertex.y = -vertex.y

        # Fix the face normals
        if x is not y:
            for face in self.faces:
                v1, v2, v3 = face.v1, face.v2, face.v3
                face.v1, face.v2, face.v3 = v3, v2, v1


class BWMFace(Face):
    """An extension of the Face class with a transition index for each edge."""

    def __init__(
        self,
        v1: Vector3,
        v2: Vector3,
        v3: Vector3,
    ):
        super().__init__(v1, v2, v3)
        self.trans1: int | None = None
        self.trans2: int | None = None
        self.trans3: int | None = None


class BWMMostSignificantPlane(IntEnum):
    NEGATIVE_Z = -3
    NEGATIVE_Y = -2
    NEGATIVE_X = -1
    NONE = 0
    POSITIVE_X = 1
    POSITIVE_Y = 2
    POSITIVE_Z = 3


class BWMNodeAABB:
    """A node in an AABB tree. Calculated with BWM.aabbs()."""

    def __init__(
        self,
        bb_min: Vector3,
        bb_max: Vector3,
        face: BWMFace | None,
        sigplane: int,
        left: BWMNodeAABB | None,
        right: BWMNodeAABB | None,
    ):
        self.bb_min: Vector3 = bb_min
        self.bb_max: Vector3 = bb_max
        self.face: BWMFace | None = face
        self.sigplane: BWMMostSignificantPlane = BWMMostSignificantPlane(sigplane)
        self.left: BWMNodeAABB | None = left
        self.right: BWMNodeAABB | None = right


class BWMAdjacency:
    """Maps a edge index (0 to 2 inclusive) to a target face from a source face. Calculated with BWM.adjacencies().

    Attributes
    ----------
        face: Target face.
        edge: Edge index of the source face (0 to 2 inclusive).
    """

    def __init__(
        self,
        face: BWMFace,
        index: int,
    ):
        self.face: BWMFace = face
        self.edge: int = index


class BWMEdge:
    """Represents an edge of a the face that is not adjacent to any other walkable face. Calculated with BWM.edges().

    Attributes
    ----------
        face: The face.
        index: Edge index on the face (0 to 2 inclusive).
        transition: Index into a LYT file.
        final: The final edge of the perimeter.
    """

    def __init__(
        self,
        face: BWMFace,
        index: int,
        transition: int,
        final: bool = False,
    ):
        self.face: BWMFace = face
        self.index: int = index
        self.transition: int = transition
        self.final: bool = final
