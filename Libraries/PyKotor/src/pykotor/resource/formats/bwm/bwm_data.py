from __future__ import annotations

import itertools
import math

from copy import copy
from enum import IntEnum
from typing import TYPE_CHECKING

from pykotor.common.geometry import Face, Vector3

if TYPE_CHECKING:
    from typing_extensions import Literal

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
    ) -> list[BWMFace]:
        """Get a list of walkable faces'.

        Args:
        ----
            self: Object containing faces

        Returns:
        -------
            list[BWMFace]: List of faces that are walkable

        Processing Logic:
        ----------------
            - Iterate through all faces in self.faces
            - Check if each face's material is walkable using face.material.walkable()
            - Add face to return list if walkable.
        """
        return [face for face in self.faces if face.material.walkable()]

    def unwalkable_faces(
        self,
    ) -> list[BWMFace]:
        """Return unwalkable faces in the mesh.

        Args:
        ----
            self: The mesh object

        Returns:
        -------
            list[BWMFace]: List of unwalkable faces in the mesh

        Processing Logic:
        ----------------
            - Iterate through all faces in the mesh
            - Check if the material of the face is not walkable
            - Add the face to the return list if material is not walkable
            - Return the list of unwalkable faces.
        """
        return [face for face in self.faces if not face.material.walkable()]

    def vertices(
        self,
    ) -> list[Vector3]:
        """Returns a list of vectors stored in the faces of the walkmesh.

        Returns:
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
        """Returns a list of AABBs for all faces in the node.

        Args:
        ----
            self: The node object

        Returns:
        -------
            list[BWMNodeAABB]: List of AABB objects for each face

        Processing Logic:
        ----------------
            - Recursively traverse the faces tree to collect all leaf faces
            - Calculate AABB for each leaf face
            - Add AABB to return list
            - Return list of all AABBs.
        """
        aabbs: list[BWMNodeAABB] = []
        self._aabbs_rec(aabbs, copy(self.faces))
        return aabbs

    def _aabbs_rec(
        self,
        aabbs: list[BWMNodeAABB],
        faces: list[BWMFace],
        rlevel=0,
    ):
        """Recursively build an axis aligned bounding box tree from a list of faces.

        Args:
        ----
            aabbs: list[BWMNodeAABB]: Accumulator for AABBs
            faces: list[BWMFace]: List of faces to build tree from
            rlevel: int: Recursion level

        Returns:
        -------
            None: Tree is built by side effect of modifying aabbs

        Processing Logic:
        ----------------
            - Calculate bounding box of all faces
            - Split faces into left and right based on longest axis
            - Recursively build left and right trees
            - Stop when single face remains or axes exhausted
        """
        if rlevel > 128:
            msg = f"recursion level must not exceed 128, but is currently at level {rlevel}"
            raise ValueError(msg)

        if not faces:
            msg = "face_list must not be empty"
            raise ValueError(msg)

        # Calculate bounding box
        bbmin = Vector3(100000.0, 100000.0, 100000.0)
        bbmax = Vector3(-100000.0, -100000.0, -100000.0)
        bbcentre: Vector3 = Vector3.from_null()
        for face in faces:
            for vertex in (face.v1, face.v2, face.v3):
                for axis in range(3):
                    bbmin[axis] = min(bbmin[axis], vertex[axis])
                    bbmax[axis] = max(bbmax[axis], vertex[axis])
            bbcentre += face.centre()
        bbcentre = bbcentre / len(faces)

        # Only one face left - this node is a leaf
        if len(faces) == 1:
            aabbs.append(BWMNodeAABB(bbmin, bbmax, faces[0], 0, None, None))
            return

        # Find longest axis
        split_axis: int = 0
        bb_size: Vector3 = bbmax - bbmin
        if bb_size.y > bb_size.x:
            split_axis = 1
        if bb_size.z > bb_size.y:
            split_axis = 2

        # Change axis in case points are coplanar with the split plane
        change_axis: bool = True
        for face in faces:
            change_axis = change_axis and face.centre()[split_axis] == bbcentre[split_axis]
        if change_axis:
            split_axis = 0 if split_axis == 2 else split_axis + 1

        # Put faces on the left and right side of the split plane into separate
        # lists. Try all axises to prevent tree degeneration.
        faces_left: list[BWMFace] = []
        faces_right: list[BWMFace] = []
        tested_axes = 1
        while True:
            faces_left = []
            faces_right = []
            for face in faces:
                centre: Vector3 = face.centre()
                if centre[split_axis] < bbcentre[split_axis]:
                    faces_left.append(face)
                else:
                    faces_right.append(face)

            if faces_left and faces_right:
                break

            split_axis = 0 if split_axis == 2 else split_axis + 1
            tested_axes += 1
            if tested_axes == 3:
                msg = "Generated tree is degenerate"
                raise RuntimeError(msg)

        aabb = BWMNodeAABB(bbmin, bbmax, None, split_axis + 1, None, None)
        aabbs.append(aabb)
        aabb.left = aabbs[-1]
        self._aabbs_rec(aabbs, faces_left, rlevel + 1)
        aabb.right = aabbs[-1]
        self._aabbs_rec(aabbs, faces_right, rlevel + 1)

    def edges(
        self,
    ) -> list[BWMEdge]:
        """Returns the edges in the BWM.

        Args:
        ----
            self: The BWM object.

        Returns:
        -------
            list[BWMEdge]: A list of edges in the BWM.

        Processing Logic:
        ----------------
            - Finds walkable faces and their adjacencies
            - Iterates through faces and edges to find unconnected edges
            - Traces edge paths and adds them to the edges list until it loops back
            - Marks final edges and records perimeter lengths
        """
        walkable: list[BWMFace] = [face for face in self.faces if face.material.walkable()]
        adjacencies: list[tuple[BWMAdjacency | None, BWMAdjacency | None, BWMAdjacency | None]] = [self.adjacencies(face) for face in walkable]

        visited: set[int] = set()
        edges: list[BWMEdge] = []
        perimeters: list[int] = []
        for i, j in itertools.product(range(len(walkable)), range(3)):
            if adjacencies[i][j] is not None:
                continue
            edge_index: int = i * 3 + j
            if edge_index in visited:
                continue
            next_face: int = i
            next_edge: int = j
            while next_face != -1:
                adj_edge: BWMAdjacency | None = adjacencies[next_face][next_edge]
                adj_edge_index: int = self.faces.index(adj_edge.face) * 3 + adj_edge.edge if adj_edge is not None else -1
                if adj_edge is None:
                    edge_index = 3 * next_face + next_edge
                    if edge_index not in visited:
                        face_id: int = edge_index // 3
                        edge_id: int = edge_index % 3
                        transition: int | None = -1
                        if edge_id == 0 and self.faces[face_id].trans1 is not None:
                            transition = self.faces[face_id].trans1
                        if edge_id == 1 and self.faces[face_id].trans2 is not None:
                            transition = self.faces[face_id].trans2
                        if edge_id == 2 and self.faces[face_id].trans3 is not None:
                            transition = self.faces[face_id].trans3

                        edges.append(BWMEdge(self.faces[next_face], next_edge, transition or -1))

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

    def adjacencies(
        self,
        face: BWMFace,
    ) -> tuple[BWMAdjacency | None, BWMAdjacency | None, BWMAdjacency | None]:
        """Finds adjacencies of a face.

        Args:
        ----
            face: {Face}: Face to find adjacencies for

        Returns:
        -------
            tuple: {Tuple of adjacencies or None}

        Processing Logic:
        ----------------
            1. Get list of walkable faces
            2. Define edge lists for each potential adjacency
            3. Iterate through walkable faces and check if edges match using a bit flag
            4. Return adjacencies or None.
        """
        walkable: list[BWMFace] = self.walkable_faces()

        adj1: list[Vector3] = [face.v1, face.v2]
        adj2: list[Vector3] = [face.v2, face.v3]
        adj3: list[Vector3] = [face.v3, face.v1]

        adj_index1 = None
        adj_index2 = None
        adj_index3 = None

        def matches(
            face_index: int,
            edges: list[Vector3],
        ) -> Literal[2, 1, 0, -1]:
            flag = 0x00
            other_face: BWMFace = self.faces[face_index]
            if other_face.v1 in edges:
                flag += 0x01
            if other_face.v2 in edges:
                flag += 0x02
            if other_face.v3 in edges:
                flag += 0x04
            edge: Literal[2, 1, 0, -1] = -1
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
            other_index: int = walkable.index(other)
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
        """Calculates bounding box of the mesh.

        Args:
        ----
            self: Mesh object

        Returns:
        -------
            tuple[Vector3, Vector3]: Bounding box minimum and maximum points

        Processing Logic:
        ----------------
            - Initialize bounding box minimum and maximum points to extreme values
            - Iterate through all vertices of the mesh
            - Update minimum x, y, z values of bbmin
            - Update maximum x, y, z values of bbmax
            - Return bounding box minimum and maximum points.
        """
        bbmin = Vector3(1000000, 1000000, 1000000)
        bbmax = Vector3(-1000000, -1000000, -1000000)
        for vertex in self.vertices():
            self._handle_vertex(bbmin, vertex, bbmax)
        return bbmin, bbmax

    def _handle_vertex(self, bbmin: Vector3, vertex: Vector3, bbmax: Vector3):
        """Update bounding box with vertex position.

        Args:
        ----
            bbmin: Vector3 - Bounding box minimum point
            vertex: Vector3 - Vertex position
            bbmax: Vector3 - Bounding box maximum point

        Returns:
        -------
            None - Updates bbmin and bbmax in place

        Processing Logic:
        ----------------
            - Compare vertex x, y, z to bbmin x, y, z and update bbmin with minimum
            - Compare vertex x, y, z to bbmax x, y, z and update bbmax with maximum.
        """
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
        """Returns the face at the given 2D coordinates if there is one otherwise returns None.

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
    ):
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
    ):
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
    ):
        """Changes layout indexes in faces.

        Args:
        ----
            old: Index to replace
            new: New index to set or None

        Processing Logic:
        ----------------
            - Loops through all faces in the object
            - Checks if face's trans1 attribute equals old index
            - If equal, sets trans1 to new index
            - Checks if face's trans2 attribute equals old index
            - If equal, sets trans2 to new index.
        """
        for face in self.faces:
            if face.trans1 == old:
                face.trans1 = new
            if face.trans2 == old:
                face.trans2 = new
            if face.trans2 == old:
                face.trans2 = new

    def flip(
        self,
        x: bool,  # noqa: FBT001
        y: bool,  # noqa: FBT001
    ):
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
        """Initializes a bounding volume node.

        Args:
        ----
            bb_min: Vector3 - Minimum bounds of the bounding box
            bb_max: Vector3 - Maximum bounds of the bounding box
            face: BWMFace | None - Face that splits the node or None
            sigplane: int - Index of most significant splitting plane
            left: BWMNodeAABB | None - Left child node or None
            right: BWMNodeAABB | None - Right child node or None

        Returns:
        -------
            self - The initialized BWMNodeAABB object

        Processing Logic:
        ----------------
            - Sets the bounding box minimum and maximum bounds
            - Sets the splitting face and most significant plane
            - Sets the left and right child nodes.
        """
        self.bb_min: Vector3 = bb_min
        self.bb_max: Vector3 = bb_max
        self.face: BWMFace | None = face
        self.sigplane: BWMMostSignificantPlane = BWMMostSignificantPlane(sigplane)
        self.left: BWMNodeAABB | None = left
        self.right: BWMNodeAABB | None = right


class BWMAdjacency:
    """Maps a edge index (0 to 2 inclusive) to a target face from a source face. Calculated with BWM.adjacencies().

    Attributes:
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

    Attributes:
    ----------
        face: The face.
        index: Edge index on the face (0 to 2 inclusive).
        transition: Index into a LYT file.
        final: This is the final edge of the perimeter.
    """

    def __init__(
        self,
        face: BWMFace,
        index: int,
        transition: int,
        *,
        final: bool = False,
    ):
        self.face: BWMFace = face
        self.index: int = index
        self.transition: int = transition
        self.final: bool = final
