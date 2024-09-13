from __future__ import annotations

import math
from typing import List, Tuple, Optional
from pykotor.common.geometry import Vector3
from pykotor.resource.formats.bwm.bwm_data import BWM, BWMFace, BWMNodeAABB, BWMEdge

class BWMUtils:
    @staticmethod
    def calculate_face_normal(face: BWMFace) -> Vector3:
        """Calculate the normal vector of a BWMFace."""
        edge1 = face.v2 - face.v1
        edge2 = face.v3 - face.v1
        return edge1.cross(edge2).normalize()

    @staticmethod
    def is_point_inside_face(point: Vector3, face: BWMFace) -> bool:
        """Check if a point is inside a BWMFace using barycentric coordinates."""
        v0 = face.v3 - face.v1
        v1 = face.v2 - face.v1
        v2 = point - face.v1

        dot00 = v0.dot(v0)
        dot01 = v0.dot(v1)
        dot02 = v0.dot(v2)
        dot11 = v1.dot(v1)
        dot12 = v1.dot(v2)

        inv_denom = 1 / (dot00 * dot11 - dot01 * dot01)
        u = (dot11 * dot02 - dot01 * dot12) * inv_denom
        v = (dot00 * dot12 - dot01 * dot02) * inv_denom

        return (u >= 0) and (v >= 0) and (u + v <= 1)

    @staticmethod
    def find_nearest_face(point: Vector3, bwm: BWM) -> Optional[BWMFace]:
        """Find the nearest face in a BWM to a given point."""
        nearest_face = None
        min_distance = float('inf')
        for face in bwm.faces:
            face_center = (face.v1 + face.v2 + face.v3) / 3
            distance = (point - face_center).length()
            if distance < min_distance:
                min_distance = distance
                nearest_face = face
        return nearest_face

    @staticmethod
    def generate_aabb_tree(bwm: BWM) -> BWMNodeAABB:
        """Generate an AABB tree for the BWM."""
        def build_tree(faces: List[BWMFace], depth: int = 0) -> BWMNodeAABB:
            if not faces:
                return None

            # Calculate bounding box for all faces
            bb_min = Vector3(float('inf'), float('inf'), float('inf'))
            bb_max = Vector3(float('-inf'), float('-inf'), float('-inf'))
            for face in faces:
                for vertex in (face.v1, face.v2, face.v3):
                    bb_min = Vector3(min(bb_min.x, vertex.x), min(bb_min.y, vertex.y), min(bb_min.z, vertex.z))
                    bb_max = Vector3(max(bb_max.x, vertex.x), max(bb_max.y, vertex.y), max(bb_max.z, vertex.z))

            # Create node
            node = BWMNodeAABB(bb_min, bb_max, None, 0, None, None)

            # Base case: if we have only one face, make it a leaf node
            if len(faces) == 1:
                node.face = faces[0]
                return node

            # Choose split axis (alternate between x, y, z)
            split_axis = depth % 3

            # Sort faces based on their center along the split axis
            faces.sort(key=lambda f: (f.v1[split_axis] + f.v2[split_axis] + f.v3[split_axis]) / 3)

            # Split faces into two groups
            mid = len(faces) // 2
            left_faces = faces[:mid]
            right_faces = faces[mid:]

            # Recursively build left and right subtrees
            node.left = build_tree(left_faces, depth + 1)
            node.right = build_tree(right_faces, depth + 1)

            return node

        return build_tree(bwm.faces)

    @staticmethod
    def find_path(start: Vector3, end: Vector3, bwm: BWM) -> List[Vector3]:
        """Find a path between two points on the walkmesh using A* algorithm."""
        def heuristic(a: Vector3, b: Vector3) -> float:
            return (b - a).length()

        def get_neighbors(face: BWMFace) -> List[BWMFace]:
            return [adj.face for adj in bwm.adjacencies(face) if adj]

        start_face = BWMUtils.find_nearest_face(start, bwm)
        end_face = BWMUtils.find_nearest_face(end, bwm)

        if not start_face or not end_face:
            return []

        open_set = {start_face}
        came_from = {}
        g_score = {start_face: 0}
        f_score = {start_face: heuristic(start, end)}

        while open_set:
            current = min(open_set, key=lambda x: f_score.get(x, float('inf')))

            if current == end_face:
                path = []
                while current in came_from:
                    path.append(current.centre())
                    current = came_from[current]
                path.append(start)
                return list(reversed(path))

            open_set.remove(current)
            for neighbor in get_neighbors(current):
                tentative_g_score = g_score[current] + (neighbor.centre() - current.centre()).length()

                if tentative_g_score < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = g_score[neighbor] + heuristic(neighbor.centre(), end)
                    if neighbor not in open_set:
                        open_set.add(neighbor)

        return []  # No path found

    @staticmethod
    def optimize_walkmesh(bwm: BWM) -> BWM:
        """Optimize the walkmesh by reducing the number of faces while maintaining accuracy."""
        def can_merge_faces(face1: BWMFace, face2: BWMFace) -> bool:
            # Check if faces are coplanar and share an edge
            normal1 = BWMUtils.calculate_face_normal(face1)
            normal2 = BWMUtils.calculate_face_normal(face2)
            if normal1.dot(normal2) > 0.99:  # Allow for small floating-point errors
                shared_vertices = set(face1.vertices) & set(face2.vertices)
                return len(shared_vertices) == 2
            return False

        def merge_faces(face1: BWMFace, face2: BWMFace) -> BWMFace:
            # Merge two faces into one
            vertices = list(set(face1.vertices + face2.vertices))
            if len(vertices) != 4:
                raise ValueError("Cannot merge faces: resulting shape is not a quad")
            
            # Find the two vertices that are not part of the shared edge
            v1 = next(v for v in face1.vertices if v not in face2.vertices)
            v2 = next(v for v in face2.vertices if v not in face1.vertices)
            
            # Create two new triangles from the quad
            new_face1 = BWMFace(v1, vertices[1], vertices[2])
            new_face2 = BWMFace(v2, vertices[2], vertices[3])
            
            return new_face1, new_face2

        optimized_bwm = BWM()
        optimized_bwm.walkmesh_type = bwm.walkmesh_type
        optimized_bwm.faces = bwm.faces.copy()

        merged = True
        while merged:
            merged = False
            for i, face1 in enumerate(optimized_bwm.faces):
                for j, face2 in enumerate(optimized_bwm.faces[i+1:], i+1):
                    if can_merge_faces(face1, face2):
                        new_face1, new_face2 = merge_faces(face1, face2)
                        optimized_bwm.faces[i] = new_face1
                        optimized_bwm.faces[j] = new_face2
                        merged = True
                        break
                if merged:
                    break

        return optimized_bwm

    @staticmethod
    def validate_walkmesh(bwm: BWM) -> Tuple[bool, List[str]]:
        """Validate the walkmesh for common issues."""
        issues = []
        
        # Check for degenerate faces
        for i, face in enumerate(bwm.faces):
            if (face.v1 - face.v2).length() < 1e-6 or \
               (face.v2 - face.v3).length() < 1e-6 or \
               (face.v3 - face.v1).length() < 1e-6:
                issues.append(f"Degenerate face found: Face {i}")

        # Check for disconnected regions
        visited = set()
        def dfs(face):
            visited.add(face)
            for adj in bwm.adjacencies(face):
                if adj and adj.face not in visited:
                    dfs(adj.face)

        if bwm.faces:
            dfs(bwm.faces[0])
            if len(visited) != len(bwm.faces):
                issues.append("Disconnected regions found in walkmesh")

        # Check for overlapping faces
        for i, face1 in enumerate(bwm.faces):
            for j, face2 in enumerate(bwm.faces[i+1:], i+1):
                if BWMUtils.do_faces_intersect(face1, face2):
                    issues.append(f"Overlapping faces found: Face {i} and Face {j}")

        return len(issues) == 0, issues

    @staticmethod
    def do_faces_intersect(face1: BWMFace, face2: BWMFace) -> bool:
        """Check if two faces intersect."""
        def triangle_intersection(t1: Tuple[Vector3, Vector3, Vector3], t2: Tuple[Vector3, Vector3, Vector3]) -> bool:
            def edge_intersection(a: Vector3, b: Vector3, c: Vector3, d: Vector3) -> bool:
                def ccw(a: Vector3, b: Vector3, c: Vector3) -> bool:
                    return (c.y - a.y) * (b.x - a.x) > (b.y - a.y) * (c.x - a.x)
                return ccw(a, c, d) != ccw(b, c, d) and ccw(a, b, c) != ccw(a, b, d)

            return (
                edge_intersection(t1[0], t1[1], t2[0], t2[1]) or
                edge_intersection(t1[0], t1[1], t2[1], t2[2]) or
                edge_intersection(t1[0], t1[1], t2[2], t2[0]) or
                edge_intersection(t1[1], t1[2], t2[0], t2[1]) or
                edge_intersection(t1[1], t1[2], t2[1], t2[2]) or
                edge_intersection(t1[1], t1[2], t2[2], t2[0]) or
                edge_intersection(t1[2], t1[0], t2[0], t2[1]) or
                edge_intersection(t1[2], t1[0], t2[1], t2[2]) or
                edge_intersection(t1[2], t1[0], t2[2], t2[0])
            )

        return triangle_intersection((face1.v1, face1.v2, face1.v3), (face2.v1, face2.v2, face2.v3))
