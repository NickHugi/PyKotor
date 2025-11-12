from __future__ import annotations
"""
Binary WalkMesh (BWM/WOK) runtime model for KotOR (Aurora/NWN engine lineage).

KotOR areas use a walkmesh (stored on disk in WOK/BWM form) to describe the set of
triangles the player and AI can stand on, plus edge metadata for transitions
(e.g., doors, area hooks) and an acceleration structure (AABB tree) for queries.

This module contains a high-level, in-memory representation of that data:
 - BWM:     The entire walkmesh object (faces, transforms/hooks, helpers)
 - BWMFace: A single triangle with a material and up to 3 per-edge transition ids
 - BWMEdge: A boundary edge for perimeters (computed from geometry, not stored)
 - BWMAdjacency: Logical adjacency of one face/edge to a neighboring face/edge
 - BWMNodeAABB: AABB tree node for broad-phase intersection

References:
----------
    vendor/reone/include/reone/graphics/walkmesh.h:27-89 - Walkmesh class
    vendor/reone/include/reone/graphics/format/bwmreader.h:29-78 - BwmReader class
    vendor/reone/src/libs/graphics/format/bwmreader.cpp:27-171 - Complete BWM loading
    vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:24-981 - TypeScript walkmesh implementation
    vendor/KotOR.js/src/odyssey/WalkmeshEdge.ts:15-110 - WalkmeshEdge class
    vendor/kotorblender/io_scene_kotor/scene/walkmesh.py:25-60 - Blender walkmesh import
    vendor/WalkmeshVisualizer - Walkmesh visualization tools

Binary Format:
-------------
    Header (8 bytes):
        Offset | Size | Type   | Description
        -------|------|--------|-------------
        0x00   | 4    | char[] | File Type ("BWM ")
        0x04   | 4    | char[] | File Version ("V1.0")
    
    Walkmesh Properties (52 bytes):
        Offset | Size | Type   | Description
        -------|------|--------|-------------
        0x08   | 4    | uint32 | Walkmesh Type (0=PWK/DWK, 1=WOK/Area)
        0x0C   | 12   | float3 | Relative Use Position 1 (x, y, z)
        0x18   | 12   | float3 | Relative Use Position 2 (x, y, z)
        0x24   | 12   | float3 | Absolute Use Position 1 (x, y, z)
        0x30   | 12   | float3 | Absolute Use Position 2 (x, y, z)
        0x3C   | 12   | float3 | Position (x, y, z)
    
    Data Tables (offsets stored in header):
        - Vertices: Array of float3 (x, y, z) per vertex
        - Face Indices: Array of uint32 triplets (vertex indices per face)
        - Materials: Array of uint32 (SurfaceMaterial ID per face)
        - Normals: Array of float3 (face normal per face)
        - Planar Distances: Array of float32 (per face)
        - AABB Nodes: Array of AABB structures (WOK only)
        - Adjacencies: Array of int32 triplets (WOK only, -1 for no neighbor)
        - Edges: Array of (edge_index, transition) pairs (WOK only)
        - Perimeters: Array of edge indices (WOK only)
        
    Reference: reone/bwmreader.cpp:27-92, KotOR.js/OdysseyWalkMesh.ts:200-600

Identity vs Equality
--------------------
Faces and vertices implement value-based equality to support comparisons, hashing
and tests. However, certain algorithms must map a specific face OBJECT back to its
index in the `BWM.faces` sequence to produce edge indices of the form:

    edge_index = face_index * 3 + local_edge_index

Value-based equality makes Python's list.index() unsuitable here because it may
return the index of a different but equal face. To avoid this, code in this module
uses identity-based selection (the `is` operator) when computing indices.
See `_index_by_identity()` and the writer logic in `io_bwm.py`.

Transitions vs Adjacency
------------------------
The `trans1`, `trans2`, and `trans3` fields on `BWMFace` are optional per-edge
transition indices into other area data (e.g., LYT/door references). They are NOT
unique identifiers and do not encode geometric adjacency. Adjacency is derived
purely from geometry (shared vertices on walkable faces).
"""

import itertools
import math

from copy import copy
from enum import IntEnum
from typing import TYPE_CHECKING

from utility.common.geometry import Face, Vector3
from pykotor.resource.formats._base import ComparableMixin

if TYPE_CHECKING:
    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]

# A lot of the code in this module was adapted from the KotorBlender fork by seedhartha:
# https://github.com/seedhartha/kotorblender


class BWMType(IntEnum):
    """Walkmesh type enumeration.
    
    Determines whether walkmesh is for area geometry (WOK) or placeable/door objects (PWK/DWK).
    Area walkmeshes include AABB trees and adjacency data, while placeable walkmeshes are simpler.
    
    References:
    ----------
        vendor/reone/src/libs/graphics/format/bwmreader.h:40-43 (WalkmeshType enum)
        vendor/reone/src/libs/graphics/format/bwmreader.cpp:30 (type reading)
        vendor/KotOR.js/src/enums/odyssey/OdysseyWalkMeshType.ts:11-14 - WalkmeshType enum
        vendor/reone/src/libs/graphics/format/bwmreader.cpp:52-64 (WOK-specific data)
        
    Values:
    ------
        PlaceableOrDoor = 0: Walkmesh for placeable objects or doors (PWK/DWK)
            Reference: reone/bwmreader.h:41 (PWK_DWK = 0)
            Simpler format without AABB trees or adjacency data
            Used for interactive objects that can be placed in areas
            
        AreaModel = 1: Walkmesh for area geometry (WOK)
            Reference: reone/bwmreader.h:42 (WOK = 1)
            Reference: KotOR.js/OdysseyWalkMeshType.ts:13 (AABB = 1)
            Full format with AABB trees, adjacencies, edges, and perimeters
            Used for area room geometry and pathfinding
    """
    
    PlaceableOrDoor = 0
    AreaModel = 1


class BWM(ComparableMixin):
    """In-memory walkmesh model (faces, hooks, helpers).
    
    Walkmeshes define collision geometry for areas and objects. They consist of triangular
    faces with materials (determining walkability, line-of-sight blocking, etc.), optional
    edge transitions for area connections, and spatial acceleration structures (AABB trees)
    for efficient queries.
    
    References:
    ----------
        vendor/reone/include/reone/graphics/walkmesh.h:27-89 - Walkmesh class
        vendor/reone/src/libs/graphics/format/bwmreader.cpp:66-91 (walkmesh construction)
        vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:24-981 - OdysseyWalkMesh class
        vendor/kotorblender/io_scene_kotor/scene/walkmesh.py:25-60 - Walkmesh class
        
    Attributes:
    ----------
        walkmesh_type: Type of walkmesh (AreaModel or PlaceableOrDoor)
            Reference: reone/bwmreader.cpp:30 (_type field)
            Reference: reone/bwmreader.cpp:67 (_walkmesh->_area flag)
            Reference: KotOR.js/OdysseyWalkMesh.ts:60 (header.walkMeshType)
            Determines which data structures are present (AABB trees, adjacencies, etc.)
            AreaModel (WOK) includes full spatial acceleration and adjacency data
            
        faces: List of triangular faces making up the walkmesh
            Reference: reone/walkmesh.h:68 (_faces vector)
            Reference: reone/bwmreader.cpp:74-87 (face construction loop)
            Reference: KotOR.js/OdysseyWalkMesh.ts:37 (faces array)
            Each face has 3 vertices, a material (SurfaceMaterial), and optional transitions
            Faces define walkable surfaces, collision boundaries, and line-of-sight blockers
            
        position: 3D position offset for the walkmesh (x, y, z)
            Reference: reone/bwmreader.cpp:37-38 (_position field)
            Reference: reone/bwmreader.cpp:123 (position reading in PyKotor io_bwm.py)
            Reference: KotOR.js/OdysseyWalkMesh.ts:36 (mat4 matrix, position component)
            Used to position walkmesh relative to area origin
            Typically (0, 0, 0) for area walkmeshes
            
        relative_hook1: First relative hook position (x, y, z)
            Reference: reone/bwmreader.cpp:32 (relUsePosition1 reading)
            Reference: PyKotor io_bwm.py:119 (relative_hook1 reading)
            Hook point relative to walkmesh origin
            Used for door/transition placement (relative to walkmesh)
            
        relative_hook2: Second relative hook position (x, y, z)
            Reference: reone/bwmreader.cpp:33 (relUsePosition2 reading)
            Reference: PyKotor io_bwm.py:120 (relative_hook2 reading)
            Hook point relative to walkmesh origin
            Used for door/transition placement (relative to walkmesh)
            
        absolute_hook1: First absolute hook position (x, y, z)
            Reference: reone/bwmreader.cpp:34 (absUsePosition1 reading)
            Reference: PyKotor io_bwm.py:121 (absolute_hook1 reading)
            Hook point in world space (absolute coordinates)
            Used for door/transition placement (absolute world position)
            
        absolute_hook2: Second absolute hook position (x, y, z)
            Reference: reone/bwmreader.cpp:35 (absUsePosition2 reading)
            Reference: PyKotor io_bwm.py:122 (absolute_hook2 reading)
            Hook point in world space (absolute coordinates)
            Used for door/transition placement (absolute world position)
    """

    COMPARABLE_FIELDS = ("walkmesh_type", "position", "relative_hook1", "relative_hook2", "absolute_hook1", "absolute_hook2")
    COMPARABLE_SEQUENCE_FIELDS = ("faces",)

    def __init__(
        self,
    ):
        # vendor/reone/src/libs/graphics/format/bwmreader.cpp:30,67
        # vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:60
        # Walkmesh type (AreaModel=WOK or PlaceableOrDoor=PWK/DWK)
        self.walkmesh_type: BWMType = BWMType.AreaModel
        
        # vendor/reone/include/reone/graphics/walkmesh.h:68
        # vendor/reone/src/libs/graphics/format/bwmreader.cpp:74-87
        # vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:37
        # List of triangular faces (vertices, material, transitions)
        self.faces: list[BWMFace] = []

        # vendor/reone/src/libs/graphics/format/bwmreader.cpp:37-38
        # vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:36
        # 3D position offset for walkmesh (typically 0,0,0 for areas)
        self.position: Vector3 = Vector3.from_null()
        
        # vendor/reone/src/libs/graphics/format/bwmreader.cpp:32
        # First relative hook position (door/transition placement, relative to walkmesh)
        self.relative_hook1: Vector3 = Vector3.from_null()
        
        # vendor/reone/src/libs/graphics/format/bwmreader.cpp:33
        # Second relative hook position (door/transition placement, relative to walkmesh)
        self.relative_hook2: Vector3 = Vector3.from_null()
        
        # vendor/reone/src/libs/graphics/format/bwmreader.cpp:34
        # First absolute hook position (door/transition placement, world space)
        self.absolute_hook1: Vector3 = Vector3.from_null()
        
        # vendor/reone/src/libs/graphics/format/bwmreader.cpp:35
        # Second absolute hook position (door/transition placement, world space)
        self.absolute_hook2: Vector3 = Vector3.from_null()

    def __eq__(self, other):
        if not isinstance(other, BWM):
            return NotImplemented
        return (
            self.walkmesh_type == other.walkmesh_type
            and self.faces == other.faces
            and self.position == other.position
            and self.relative_hook1 == other.relative_hook1
            and self.relative_hook2 == other.relative_hook2
            and self.absolute_hook1 == other.absolute_hook1
            and self.absolute_hook2 == other.absolute_hook2
        )

    def __hash__(self):
        return hash((
            self.walkmesh_type,
            tuple(self.faces),
            self.position,
            self.relative_hook1,
            self.relative_hook2,
            self.absolute_hook1,
            self.absolute_hook2,
        ))

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
        """Returns unique vertex objects referenced by faces in the walkmesh.

        Returns:
        -------
            A list of Vector3 objects. Uniqueness is identity-based; the order
            is first-seen while iterating faces.
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
        rlevel: int = 0,
    ) -> BWMNodeAABB:
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
        max_level = 128
        if rlevel > max_level:
            msg = f"recursion level must not exceed {max_level}, but is currently at level {rlevel}"
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
            leaf = BWMNodeAABB(bbmin, bbmax, faces[0], 0, None, None)
            aabbs.append(leaf)
            return leaf

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
        left_child = self._aabbs_rec(aabbs, faces_left, rlevel + 1)
        aabb.left = left_child
        right_child = self._aabbs_rec(aabbs, faces_right, rlevel + 1)
        aabb.right = right_child
        return aabb

    def edges(
        self,
    ) -> list[BWMEdge]:
        """Returns perimeter edges (edges with no walkable neighbor).

        Args:
        ----
            self: The BWM object.

        Returns:
        -------
            list[BWMEdge]: A list of perimeter edges in face-order traversal.

        Processing Logic:
        ----------------
            - Finds walkable faces and their adjacencies
            - Iterates through faces and edges to find unconnected edges
            - Traces edge paths and adds them to the edges list until it loops back
            - Marks final edges and records perimeter lengths
            - Uses identity-based face indexing when converting adjacency to an
              edge index (see `_index_by_identity`).
        """
        walkable: list[BWMFace] = [face for face in self.faces if face.material.walkable()]
        adjacencies: list[tuple[BWMAdjacency | None, BWMAdjacency | None, BWMAdjacency | None]] = [self.adjacencies(face) for face in walkable]

        visited: set[int] = set()
        edges: list[BWMEdge] = []
        perimeters: list[int] = []
        for i, j in itertools.product(range(len(walkable)), range(3)):
            edge_index: int = i * 3 + j
            if adjacencies[i][j] is not None or edge_index in visited:
                continue  # Skip if adjacency exists or edge has been visited
            next_face: int = i
            next_edge: int = j
            perimeter_length: int = 0
            while next_face != -1:
                adj_edge: BWMAdjacency | None = adjacencies[next_face][next_edge]
                if adj_edge is not None:
                    # Do NOT use list.index() here; faces have value-based equality,
                    # so we must recover indices strictly by identity.
                    adj_edge_index = self._index_by_identity(adj_edge.face) * 3 + adj_edge.edge
                    next_face = adj_edge_index // 3
                    next_edge = ((adj_edge_index % 3) + 1) % 3
                    continue
                edge_index = next_face * 3 + next_edge
                if edge_index in visited:
                    next_face = -1
                    edges[-1].final = True
                    perimeters.append(perimeter_length)
                    continue
                face_id, edge_id = divmod(edge_index, 3)
                transition: int | None = None
                if edge_id == 0 and self.faces[face_id].trans1 is not None:
                    transition = self.faces[face_id].trans1
                if edge_id == 1 and self.faces[face_id].trans2 is not None:
                    transition = self.faces[face_id].trans2
                if edge_id == 2 and self.faces[face_id].trans3 is not None:
                    transition = self.faces[face_id].trans3
                edges.append(BWMEdge(self.faces[next_face], edge_index, -1 if transition is None else transition))
                perimeter_length += 1
                visited.add(edge_index)
                next_edge = (edge_index + 1) % 3

        return edges


    def _index_by_identity(
        self,
        face: BWMFace,
    ) -> int:
        """Find the index of a face by object identity, not value equality.
        
        Args:
        ----
            face: The face object to find.
            
        Returns:
        -------
            The index of the face in self.faces.
            
        Raises:
        ------
            ValueError: If the face is not found.
        """
        for i, f in enumerate(self.faces):
            if f is face:
                return i
        msg = "Face not found in faces list"
        raise ValueError(msg)

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
            face_obj: BWMFace,
            edges: list[Vector3],
        ) -> Literal[2, 1, 0, -1]:
            flag = 0x00
            if face_obj.v1 in edges:
                flag += 0x01
            if face_obj.v2 in edges:
                flag += 0x02
            if face_obj.v3 in edges:
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
            edge_match1 = matches(other, adj1)
            edge_match2 = matches(other, adj2)
            edge_match3 = matches(other, adj3)
            
            if edge_match1 != -1:
                adj_index1 = BWMAdjacency(other, edge_match1)
            if edge_match2 != -1:
                adj_index2 = BWMAdjacency(other, edge_match2)
            if edge_match3 != -1:
                adj_index3 = BWMAdjacency(other, edge_match3)

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


class BWMFace(Face, ComparableMixin):
    """Triangle face with material and optional per-edge transitions.
    
    Each face represents a single triangle in the walkmesh with three vertices, a material
    (determining walkability and surface properties), and optional transition indices for
    each edge. Transitions reference LYT door hooks or area connections, not geometric
    adjacency (which is computed from shared vertices).
    
    References:
    ----------
        vendor/reone/include/reone/graphics/walkmesh.h:29-34 - Face struct
        vendor/reone/src/libs/graphics/format/bwmreader.cpp:78-86 (face construction)
        vendor/KotOR.js/src/three/odyssey/OdysseyFace3.ts - OdysseyFace3 class
        vendor/kotorblender/io_scene_kotor/scene/material.py - Material handling
        
    Binary Format (per face):
    -----------------------
        Face data is stored in separate arrays:
        - Indices: 3x uint32 (vertex indices into vertex array)
        - Material: 1x uint32 (SurfaceMaterial ID)
        - Normal: 3x float32 (face normal vector)
        - Transitions: Stored in edges table (edge_index -> transition mapping)
        
        Reference: reone/bwmreader.cpp:74-87, PyKotor io_bwm.py:147-179
        
    Attributes:
    ----------
        Inherits from Face: v1, v2, v3 (Vector3 vertices)
            Reference: reone/walkmesh.h:32 (vertices vector, 3 elements)
            Reference: reone/bwmreader.cpp:81-83 (vertex reading)
            Reference: KotOR.js/OdysseyWalkMesh.ts:80-84 (triangle construction)
            Three vertices defining the triangular face
            Vertices are shared between faces (stored in BWM vertex array)
            
        material: SurfaceMaterial determining face properties
            Reference: reone/walkmesh.h:31 (material field, uint32)
            Reference: reone/bwmreader.cpp:75,120 (material reading)
            Reference: KotOR.js/OdysseyWalkMesh.ts:76 (materialIndex)
            Reference: PyKotor io_bwm.py:159-160 (material assignment)
            Determines walkability, line-of-sight blocking, grass rendering, etc.
            Stored as uint32 material ID in binary format
            
        trans1: Optional transition index for edge 0 (v1->v2)
            Reference: PyKotor io_bwm.py:164-179 (transition reading from edges table)
            Reference: KotOR.js/WalkmeshEdge.ts:16 (transition field)
            Edge index calculation: face_index * 3 + 0
            Transition index into LYT door hooks or area connections
            Value None/0xFFFFFFFF indicates no transition for this edge
            NOT a geometric adjacency identifier
            
        trans2: Optional transition index for edge 1 (v2->v3)
            Reference: PyKotor io_bwm.py:164-179 (transition reading from edges table)
            Edge index calculation: face_index * 3 + 1
            Transition index into LYT door hooks or area connections
            Value None/0xFFFFFFFF indicates no transition for this edge
            
        trans3: Optional transition index for edge 2 (v3->v1)
            Reference: PyKotor io_bwm.py:164-179 (transition reading from edges table)
            Edge index calculation: face_index * 3 + 2
            Transition index into LYT door hooks or area connections
            Value None/0xFFFFFFFF indicates no transition for this edge
            
    Notes:
    -----
        - `trans1`, `trans2`, `trans3` are metadata for engine transitions (e.g.,
          LYT/door indices) and are not unique identifiers.
        - They do not encode geometric adjacency; adjacency is derived from shared
          vertex identity on walkable faces.
        - Transitions are stored in a separate edges table in binary format, not
          directly in face data (reone doesn't parse transitions, PyKotor does)
    """

    def __init__(
        self,
        v1: Vector3,
        v2: Vector3,
        v3: Vector3,
    ):
        # vendor/reone/include/reone/graphics/walkmesh.h:32
        # vendor/reone/src/libs/graphics/format/bwmreader.cpp:81-83
        # vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:80-84
        # Three vertices defining the triangular face
        super().__init__(v1, v2, v3)
        
        # vendor/PyKotor io_bwm.py:164-179
        # vendor/KotOR.js/src/odyssey/WalkmeshEdge.ts:16
        # Optional transition indices for each edge (stored in edges table in binary)
        # Edge 0 (v1->v2): transition index into LYT door hooks
        self.trans1: int | None = None
        
        # Edge 1 (v2->v3): transition index into LYT door hooks
        self.trans2: int | None = None
        
        # Edge 2 (v3->v1): transition index into LYT door hooks
        self.trans3: int | None = None

    def __eq__(self, other):
        if not isinstance(other, BWMFace):
            return NotImplemented
        parent_eq = super().__eq__(other)
        if parent_eq is NotImplemented:
            return NotImplemented
        return (
            parent_eq
            and self.trans1 == other.trans1
            and self.trans2 == other.trans2
            and self.trans3 == other.trans3
        )

    def __hash__(self):
        return hash((super().__hash__(), self.trans1, self.trans2, self.trans3))


class BWMMostSignificantPlane(IntEnum):
    NEGATIVE_Z = -3
    NEGATIVE_Y = -2
    NEGATIVE_X = -1
    NONE = 0
    POSITIVE_X = 1
    POSITIVE_Y = 2
    POSITIVE_Z = 3


class BWMNodeAABB(ComparableMixin):
    """A node in an AABB (Axis-Aligned Bounding Box) tree for spatial queries.
    
    AABB trees provide efficient spatial acceleration for walkmesh queries (raycasting,
    point containment, etc.). Internal nodes contain bounding boxes and split planes,
    while leaf nodes reference specific faces. The tree is built recursively by splitting
    faces along the longest axis.
    
    References:
    ----------
        vendor/reone/include/reone/graphics/walkmesh.h:36-41 - AABB struct
        vendor/reone/src/libs/graphics/format/bwmreader.cpp:136-171 (AABB loading)
        vendor/reone/src/libs/graphics/walkmesh.cpp:57-100 (AABB raycasting)
        vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:44 (aabbNodes array)
        vendor/KotOR.js/src/interface/odyssey/IOdysseyModelAABBNode.ts - AABB node interface
        
    Binary Format (per AABB node, 32 bytes):
    ---------------------------------------
        Offset | Size | Type   | Description
        -------|------|--------|-------------
        0x00   | 24   | float6 | Bounding Box (min x,y,z, max x,y,z)
        0x18   | 4    | int32  | Face Index (-1 for internal nodes, >=0 for leaves)
        0x1C   | 4    | uint32 | Unknown (typically 0)
        0x20   | 4    | uint32 | Most Significant Plane (split axis)
        0x24   | 4    | uint32 | Left Child Index
        0x28   | 4    | uint32 | Right Child Index
        
        Reference: reone/bwmreader.cpp:145-151, KotOR.js/OdysseyWalkMesh.ts:200-400
        
    Attributes:
    ----------
        bb_min: Minimum bounds of the axis-aligned bounding box (x, y, z)
            Reference: reone/walkmesh.h:37 (value field, AABB struct)
            Reference: reone/bwmreader.cpp:146 (bounds[0-2] reading)
            Reference: KotOR.js/IOdysseyModelAABBNode.ts (box min)
            Minimum corner of the bounding box
            Used for spatial culling and intersection tests
            
        bb_max: Maximum bounds of the axis-aligned bounding box (x, y, z)
            Reference: reone/walkmesh.h:37 (value field, AABB struct)
            Reference: reone/bwmreader.cpp:146 (bounds[3-5] reading)
            Reference: KotOR.js/IOdysseyModelAABBNode.ts (box max)
            Maximum corner of the bounding box
            Used for spatial culling and intersection tests
            
        face: Face referenced by this node (None for internal nodes)
            Reference: reone/walkmesh.h:38 (faceIdx field, -1 for internal)
            Reference: reone/bwmreader.cpp:147 (faceIdx reading)
            Reference: KotOR.js/OdysseyWalkMesh.ts:191 (node.face assignment)
            Leaf nodes reference a specific face (faceIdx >= 0)
            Internal nodes have face = None (faceIdx = -1)
            
        sigplane: Most significant splitting plane (axis index)
            Reference: reone/bwmreader.cpp:149 (mostSignificantPlane reading)
            Reference: PyKotor bwm_data.py:240-245 (split_axis calculation)
            Indicates which axis (0=X, 1=Y, 2=Z) was used to split faces
            Used during tree traversal for efficient queries
            
        left: Left child node in AABB tree (None for leaves)
            Reference: reone/walkmesh.h:39 (left shared_ptr)
            Reference: reone/bwmreader.cpp:150,166 (childIdx1, left assignment)
            Reference: KotOR.js/OdysseyWalkMesh.ts:192 (leftNode assignment)
            Child nodes contain faces on the "left" side of split plane
            None for leaf nodes (face != None)
            
        right: Right child node in AABB tree (None for leaves)
            Reference: reone/walkmesh.h:40 (right shared_ptr)
            Reference: reone/bwmreader.cpp:151,167 (childIdx2, right assignment)
            Reference: KotOR.js/OdysseyWalkMesh.ts:193 (rightNode assignment)
            Child nodes contain faces on the "right" side of split plane
            None for leaf nodes (face != None)
    """

    COMPARABLE_FIELDS = ("bb_min", "bb_max", "face", "sigplane", "left", "right")

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
        # vendor/reone/include/reone/graphics/walkmesh.h:37
        # vendor/reone/src/libs/graphics/format/bwmreader.cpp:146
        # vendor/KotOR.js/src/interface/odyssey/IOdysseyModelAABBNode.ts
        # Minimum bounds of axis-aligned bounding box
        self.bb_min: Vector3 = bb_min
        
        # vendor/reone/include/reone/graphics/walkmesh.h:37
        # vendor/reone/src/libs/graphics/format/bwmreader.cpp:146
        # Maximum bounds of axis-aligned bounding box
        self.bb_max: Vector3 = bb_max
        
        # vendor/reone/include/reone/graphics/walkmesh.h:38
        # vendor/reone/src/libs/graphics/format/bwmreader.cpp:147
        # vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:191
        # Face referenced by this node (None for internal nodes, face for leaves)
        self.face: BWMFace | None = face
        
        # vendor/reone/src/libs/graphics/format/bwmreader.cpp:149
        # vendor/PyKotor bwm_data.py:240-245
        # Most significant splitting plane (axis: 0=X, 1=Y, 2=Z)
        self.sigplane: BWMMostSignificantPlane = BWMMostSignificantPlane(sigplane)
        
        # vendor/reone/include/reone/graphics/walkmesh.h:39
        # vendor/reone/src/libs/graphics/format/bwmreader.cpp:150,166
        # vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:192
        # Left child node (None for leaf nodes)
        self.left: BWMNodeAABB | None = left
        
        # vendor/reone/include/reone/graphics/walkmesh.h:40
        # vendor/reone/src/libs/graphics/format/bwmreader.cpp:151,167
        # vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:193
        # Right child node (None for leaf nodes)
        self.right: BWMNodeAABB | None = right

    def __eq__(self, other):
        if not isinstance(other, BWMNodeAABB):
            return NotImplemented
        if self is other:
            return True
        return (
            self.bb_min == other.bb_min
            and self.bb_max == other.bb_max
            and self.face == other.face
            and self.sigplane == other.sigplane
            and self.left == other.left
            and self.right == other.right
        )

    def __hash__(self):
        return hash((
            self.bb_min,
            self.bb_max,
            self.face,
            self.sigplane,
            self.left,
            self.right,
        ))


class BWMAdjacency(ComparableMixin):
    """Maps an edge index to a target face from a source face.
    
    Adjacency represents geometric connectivity between walkable faces. Two faces are
    adjacent if they share an edge (two vertices). Adjacency is computed from geometry,
    not stored in binary format (unlike transitions, which are stored in edges table).
    
    References:
    ----------
        vendor/reone/src/libs/graphics/format/bwmreader.cpp:58-59 (adjacencies table exists but not parsed)
        vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:45 (walkableFacesEdgesAdjacencyMatrix)
        vendor/PyKotor bwm_data.py:376-440 (adjacencies computation)
        
    Attributes:
    ----------
        face: Target face that is adjacent to the source face
            Reference: PyKotor bwm_data.py:434 (BWMAdjacency construction)
            Reference: KotOR.js/OdysseyWalkMesh.ts:96 (adjacentWalkableFaces)
            The face that shares an edge with the source face
            Used for pathfinding and navigation mesh traversal
            
        edge: Edge index of the target face (0, 1, or 2)
            Reference: PyKotor bwm_data.py:434 (edge_match value)
            Reference: KotOR.js/OdysseyWalkMesh.ts:98-100 (adjacentWalkableFaces assignment)
            Indicates which edge of the target face connects to the source face
            Edge 0 = v1->v2, Edge 1 = v2->v3, Edge 2 = v3->v1
            Used to determine edge orientation for navigation
    """

    COMPARABLE_FIELDS = ("face", "edge")

    def __init__(
        self,
        face: BWMFace,
        index: int,
    ):
        # vendor/PyKotor bwm_data.py:434
        # vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:96
        # Target face that shares an edge with source face
        self.face: BWMFace = face
        
        # vendor/PyKotor bwm_data.py:434
        # vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:98-100
        # Edge index of target face (0, 1, or 2)
        self.edge: int = index

    def __eq__(self, other):
        if not isinstance(other, BWMAdjacency):
            return NotImplemented
        return self.face == other.face and self.edge == other.edge

    def __hash__(self):
        return hash((self.face, self.edge))


class BWMEdge(ComparableMixin):
    """Represents a perimeter edge (boundary edge with no walkable neighbor).
    
    Perimeter edges are edges of walkable faces that are not adjacent to any other
    walkable face. These form the boundaries of walkable areas and may have transition
    indices for area connections (doors, area transitions). Perimeter edges are computed
    from geometry, not stored directly in binary format.
    
    References:
    ----------
        vendor/KotOR.js/src/odyssey/WalkmeshEdge.ts:15-110 - WalkmeshEdge class
        vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:46 (edges Map)
        vendor/PyKotor bwm_data.py:286-349 (edges computation)
        
    Attributes:
    ----------
        face: The face this edge belongs to
            Reference: KotOR.js/WalkmeshEdge.ts:22 (face field)
            Reference: PyKotor bwm_data.py:344 (BWMEdge construction)
            The walkable face that contains this perimeter edge
            Used to determine edge geometry and position
            
        index: Edge index on the face (0, 1, or 2)
            Reference: KotOR.js/WalkmeshEdge.ts:27 (index field)
            Reference: PyKotor bwm_data.py:330-344 (edge_index calculation)
            Edge 0 = v1->v2, Edge 1 = v2->v3, Edge 2 = v3->v1
            Global edge index = face_index * 3 + local_edge_index
            Used to map back to face transitions (trans1/trans2/trans3)
            
        transition: Transition index into LYT file (door hook index)
            Reference: KotOR.js/WalkmeshEdge.ts:16 (transition field)
            Reference: PyKotor bwm_data.py:337-343 (transition reading from face)
            Reference: PyKotor io_bwm.py:169 (transition reading from edges table)
            Index into LYT door hooks for area transitions
            Value -1/0xFFFFFFFF indicates no transition
            Used for door placement and area connections
            
        final: Flag indicating this is the final edge of a perimeter loop
            Reference: PyKotor bwm_data.py:333 (final flag setting)
            Set to True when perimeter edge loop closes
            Used to mark perimeter boundaries for pathfinding
    """

    COMPARABLE_FIELDS = ("face", "index", "transition", "final")

    def __init__(
        self,
        face: BWMFace,
        index: int,
        transition: int,
        *,
        final: bool = False,
    ):
        # vendor/KotOR.js/src/odyssey/WalkmeshEdge.ts:22
        # vendor/PyKotor bwm_data.py:344
        # Face this perimeter edge belongs to
        self.face: BWMFace = face
        
        # vendor/KotOR.js/src/odyssey/WalkmeshEdge.ts:27
        # vendor/PyKotor bwm_data.py:330-344
        # Edge index on face (0, 1, or 2)
        self.index: int = index
        
        # vendor/KotOR.js/src/odyssey/WalkmeshEdge.ts:16
        # vendor/PyKotor bwm_data.py:337-343, io_bwm.py:169
        # Transition index into LYT door hooks (-1 for no transition)
        self.transition: int = transition
        
        # vendor/PyKotor bwm_data.py:333
        # Flag indicating final edge of perimeter loop
        self.final: bool = final

    def __eq__(self, other):
        if not isinstance(other, BWMEdge):
            return NotImplemented
        return (
            self.face == other.face
            and self.index == other.index
            and self.transition == other.transition
            and self.final == other.final
        )

    def __hash__(self):
        return hash((self.face, self.index, self.transition, self.final))
