from __future__ import annotations

from copy import copy
from enum import IntEnum
from typing import List, Optional, Tuple

from pykotor.common.geometry import Face, Vector3


# A lot of the code in this module was adapted from the KotorBlender fork by seedhartha:
# https://github.com/seedhartha/kotorblender


class BWMType(IntEnum):
    PlaceableOrDoor = 0
    AreaModel = 1


class BWM:
    """
    Represents the data of a RIM file.
    """
    def __init__(self):
        self.walkmesh_type: BWMType = BWMType.AreaModel
        self.faces: List[BWMFace] = []

        self.position: Vector3 = Vector3.from_null()
        self.relative_hook1: Vector3 = Vector3.from_null()
        self.relative_hook2: Vector3 = Vector3.from_null()
        self.absolute_hook1: Vector3 = Vector3.from_null()
        self.absolute_hook2: Vector3 = Vector3.from_null()

    def walkable_faces(self):
        return [face for face in self.faces if face.material.walkable()]

    def vertices(self) -> List[Vector3]:
        """
        Returns a list of vectors stored in the faces of the walkmesh.

        Returns:
            A list of Vector3 objects.
        """
        vertices: List[Vector3] = []
        for face in self.faces:
            if not face.v1.within(vertices):
                vertices.append(face.v1)
            if not face.v2.within(vertices):
                vertices.append(face.v2)
            if not face.v3.within(vertices):
                vertices.append(face.v3)
        return vertices

    def aabbs(self) -> List[BWMNodeAABB]:
        aabbs = []
        self._aabbs_rec(aabbs, copy(self.faces))
        return aabbs

    def _aabbs_rec(self, aabbs, faces, rlevel=0) -> None:
        if rlevel > 128:
            raise ValueError("rlevel must not exceed 128, but is equal to {}".format(rlevel))

        if not faces:
            raise ValueError("face_list must not be empty")

        # Calculate bounding box
        bbmin = Vector3(100000.0, 100000.0, 100000.0)
        bbmax = Vector3(-100000.0, -100000.0, -100000.0)
        bbcentre = Vector3.from_null()
        for face in faces:
            for vertex in [face.v1, face.v2, face.v3]:
                for axis in range(3):
                    if bbmin[axis] > vertex[axis]:
                        bbmin[axis] = vertex[axis]
                    if bbmax[axis] < vertex[axis]:
                        bbmax[axis] = vertex[axis]
            bbcentre += face.centre()
        bbcentre = bbcentre / len(faces)

        # Only one face left - this node is a leaf
        if len(faces) == 1:
            aabbs.append(BWMNodeAABB(bbmin, bbmax, faces[0], 0, None, None))
            return

        # Find longest axis
        split_axis = 0
        bb_size = bbmax - bbmin
        if bb_size.y > bb_size.x:
            split_axis = 1
        if bb_size.z > bb_size.y:
            split_axis = 2

        # Change axis in case points are coplanar with the split plane
        change_axis = True
        for face in faces:
            change_axis = change_axis and face.centre()[split_axis] == bbcentre[split_axis]
        if change_axis:
            split_axis = 0 if split_axis == 2 else split_axis + 1

        # Put faces on the left and right side of the split plane into separate
        # lists. Try all axises to prevent tree degeneration.
        faces_left = []
        faces_right = []
        tested_axes = 1
        while True:
            faces_left = []
            faces_right = []
            for face in faces:
                centre = face.centre()
                if centre[split_axis] < bbcentre[split_axis]:
                    faces_left.append(face)
                else:
                    faces_right.append(face)

            if faces_left and faces_right:
                break

            split_axis = 0 if split_axis == 2 else split_axis + 1
            tested_axes += 1
            if tested_axes == 3:
                raise RuntimeError("Generated tree is degenerate")

        aabb = BWMNodeAABB(bbmin, bbmax, None, split_axis + 1, None, None)
        aabbs.append(aabb)
        aabb.left = aabbs[-1]
        self._aabbs_rec(aabbs, faces_left, rlevel+1)
        aabb.right = aabbs[-1]
        self._aabbs_rec(aabbs, faces_right, rlevel+1)

    def edges(self) -> List[BWMEdge]:
        walkable = [face for face in self.faces if face.material.walkable()]
        adjacencies = [self.adjacencies(face) for face in walkable]

        visited = set()
        edges = []
        perimeters = []
        for i in range(len(walkable)):
            for j in range(3):
                if adjacencies[i][j] is not None:
                    continue
                edge_index = i * 3 + j
                if edge_index in visited:
                    continue
                next_face = i
                next_edge = j
                while next_face != -1:
                    adj_edge = adjacencies[next_face][next_edge]
                    adj_edge_index = self.faces.index(adj_edge.face) * 3 + adj_edge.index if adj_edge is not None else -1
                    if adj_edge is None:
                        edge_index = 3 * next_face + next_edge
                        if edge_index not in visited:
                            face_id = edge_index // 3
                            edge_id = edge_index % 3
                            transition = -1
                            if edge_id == 0 and self.faces[face_id].trans1 is not None:
                                transition = self.faces[face_id].trans1
                            if edge_id == 1 and self.faces[face_id].trans2 is not None:
                                transition = self.faces[face_id].trans2
                            if edge_id == 2 and self.faces[face_id].trans3 is not None:
                                transition = self.faces[face_id].trans3

                            edges.append(BWMEdge(self.faces[next_face], next_edge, transition))

                            visited.add(edge_index)
                            next_edge = (next_edge + 1) % 3
                        else:
                            next_face = -1
                            edges[-1].final = True
                            perimeters.append(len(edges))
                    else:
                        next_face = adj_edge_index // 3
                        next_edge = ((adj_edge_index % 3) + 1) % 3

        return edges

    def adjacencies(self, face: BWMFace) -> Tuple[BWMAdjacency, BWMAdjacency, BWMAdjacency]:
        walkable = self.walkable_faces()

        adj1 = [face.v1, face.v2]
        adj2 = [face.v2, face.v3]
        adj3 = [face.v3, face.v1]

        adj_index1 = None
        adj_index2 = None
        adj_index3 = None

        def matches(face_index, edges):
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
                adj_index1 = BWMAdjacency(walkable[other_index], matches(other_index, adj1))
            if matches(other_index, adj2) != -1:
                adj_index2 = BWMAdjacency(walkable[other_index], matches(other_index, adj2))
            if matches(other_index, adj3) != -1:
                adj_index3 = BWMAdjacency(walkable[other_index], matches(other_index, adj3))

        return adj_index1, adj_index2, adj_index3

    def box(self) -> Tuple[Vector3, Vector3]:
        bbmin = Vector3(1000000, 1000000, 1000000)
        bbmax = Vector3(-1000000, -1000000, -1000000)
        for vertex in self.vertices():
            bbmin.x = min(bbmin.x, vertex.x)
            bbmin.y = min(bbmin.y, vertex.y)
            bbmin.z = min(bbmin.z, vertex.z)
            bbmax.x = max(bbmax.x, vertex.x)
            bbmax.y = max(bbmax.y, vertex.y)
            bbmax.z = max(bbmax.z, vertex.z)
        return bbmin, bbmax

    def faceAt(self, x: float, y: float) -> Optional[BWMFace]:
        """
        Returns the face at the given 2D coordinates if there si one otherwise returns None.

        Args:
            x: The x coordinate.
            y: The y coordinate.

        Returns:
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
        return


class BWMFace(Face):
    """
    An extension of the Face class with a transition index for each edge.
    """
    def __init__(self, v1: Vector3, v2: Vector3, v3: Vector3):
        super().__init__(v1, v2, v3)
        self.trans1: Optional[int] = None
        self.trans2: Optional[int] = None
        self.trans3: Optional[int] = None


class BWMMostSignificantPlane(IntEnum):
    NEGATIVE_Z = -3
    NEGATIVE_Y = -2
    NEGATIVE_X = -1
    NONE = 0
    POSITIVE_X = 1
    POSITIVE_Y = 2
    POSITIVE_Z = 3


class BWMNodeAABB:
    """
    A node in an AABB tree. Calculated with BWM.aabbs().
    """
    def __init__(self, bb_min: Vector3, bb_max: Vector3, face: Optional[BWMFace], sigplane: int, left: Optional[BWMNodeAABB], right: Optional[BWMNodeAABB]):
        self.bb_min: Vector3 = bb_min
        self.bb_max: Vector3 = bb_max
        self.face: Optional[BWMFace] = face
        self.sigplane: BWMMostSignificantPlane = BWMMostSignificantPlane(sigplane)
        self.left: Optional[BWMNodeAABB] = left
        self.right: Optional[BWMNodeAABB] = right


class BWMAdjacency:
    """
    Maps a edge index (0 to 2 inclusive) to a target face from a source face. Calculated with BWM.adjacencies().

    Attributes:
        face: Target face.
        edge: Edge index of the source face (0 to 2 inclusive).
    """
    def __init__(self, face: BWMFace, index: int):
        self.face: BWMFace = face
        self.edge: int = index


class BWMEdge:
    """
    Represents an edge of a the face that is not adjacent to any other walkable face. Calculated with BWM.edges().

    Attributes:
        face: The face.
        index: Edge index on the face (0 to 2 inclusive).
        transition: Index into a LYT file.
        final: The final edge of the perimeter.
    """
    def __init__(self, face: BWMFace, index: int, transition: int, final: bool = False):
        self.face: BWMFace = face
        self.index: int = index
        self.transition: int = transition
        self.final: bool = final
