# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####
from __future__ import annotations

import math

from typing import Any, Literal

from mathutils import Vector


class BoundingBox:
    def __init__(
        self,
        min: Vector,
        max: Vector,
        center: Vector,
    ):
        self.min: Vector = min
        self.max: Vector = max
        self.center: Vector = center

    def longest_axis(self) -> Literal[0, 1, 2]:
        size = self.max - self.min
        if size.y > size.x and size.y > size.z:
            return 1  # Y
        if size.z > size.x and size.z > size.y:
            return 2  # Z
        return 0  # X


def generate_tree(
    aabb_tree: list[list[int]],
    faces: list[list[int]],
    depth: int = 0,
):
    if depth > 128:
        raise ValueError(f"depth must not exceed 128, but is equal to {depth}")
    if not faces:
        raise ValueError("faces must not be empty")

    bounding_box = compute_bounding_box(faces)

    # Only one face left - this node is a leaf
    if len(faces) == 1:
        face_idx = faces[0][0]
        aabb_tree.append(new_aabb_node(bounding_box, -1, -1, face_idx, 0))
        return

    split_axis = find_split_axis(bounding_box, faces)
    left_faces, right_faces, actual_split_axis = split_faces(
        bounding_box, faces, split_axis
    )

    node = new_aabb_node(bounding_box, 0, 0, -1, 1 + actual_split_axis)
    aabb_tree.append(node)
    node[6] = len(aabb_tree)
    generate_tree(aabb_tree, left_faces, depth + 1)
    node[7] = len(aabb_tree)
    generate_tree(aabb_tree, right_faces, depth + 1)


def compute_bounding_box(faces: list[list[int]]) -> BoundingBox:
    min_vec = Vector((100000.0, 100000.0, 100000.0))
    max_vec = Vector((-100000.0, -100000.0, -100000.0))
    center = Vector()
    for face in faces:
        verts = face[1]
        for vert in verts:
            for axis in range(3):
                min_vec[axis] = min(min_vec[axis], vert[axis])
                max_vec[axis] = max(max_vec[axis], vert[axis])
        face_center = face[2]
        center = center + face_center
    center = center / len(faces)
    return BoundingBox(min_vec, max_vec, center)


def find_split_axis(bounding_box: BoundingBox, faces: list[list[int]]) -> Literal[0, 1, 2]:
    axis = bounding_box.longest_axis()

    # Change axis in case points are coplanar with the split plane
    change = True
    for face in faces:
        face_center = face[2]
        change = change and math.isclose(
            face_center[axis],
            bounding_box.center[axis],
            rel_tol=1e-4,
        )
    if change:
        axis += 1
        if axis == 3:
            axis = 0

    return axis


def split_faces(
    bounding_box: BoundingBox,
    faces: list[list[int]],
    split_axis: Literal[0, 1, 2],
) -> tuple[list[Any], list[Any], Literal[0, 1, 2]]:
    # Put faces on the left and right side of the split plane into separate
    # lists. Try all axises to prevent tree degeneration.
    left_faces: list[list[int]] = []
    right_faces: list[list[int]] = []
    for i in range(4):
        left_faces.clear()
        right_faces.clear()
        for face in faces:
            face_center = face[2]
            if face_center[split_axis] < bounding_box.center[split_axis]:
                left_faces.append(face)
            else:
                right_faces.append(face)
        if left_faces and right_faces:
            break
        # Tree is degenerate. Try another axis, or split into evenly sized
        # lists if already tried all 3.
        if i == 3:
            non_empty_faces = left_faces if left_faces else right_faces
            empty_faces = left_faces if not left_faces else right_faces
            num_faces_to_move = int(len(non_empty_faces) / 2)
            for _ in range(num_faces_to_move):
                empty_faces.append(non_empty_faces.pop())
        split_axis = (split_axis + 1) % 3
    return (left_faces, right_faces, split_axis)


def new_aabb_node(
    bounding_box: BoundingBox,
    left_child_idx: int,
    right_child_idx: int,
    face_idx: int,
    most_significant_plane: int,
):
    return [
        *bounding_box.min[:3],
        *bounding_box.max[:3],
        left_child_idx,
        right_child_idx,
        face_idx,
        most_significant_plane,
    ]
