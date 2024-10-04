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

from typing import TYPE_CHECKING, Any

import bpy

from mathutils import Vector

from pykotor.resource.formats.mdl.reference_only.constants import NON_WALKABLE, MeshType, NodeType
from pykotor.resource.formats.mdl.reference_only.material import rebuild_walkmesh_materials
from pykotor.resource.formats.mdl.reference_only.trimesh import TrimeshNode

if TYPE_CHECKING:
    from pykotor.resource.formats.bwm.bwm_data import BWMFace

ROOM_LINKS_COLORS = "RoomLinks"


class AabbNode(TrimeshNode):
    def __init__(self, name="UNNAMED"):
        TrimeshNode.__init__(self, name)
        self.nodetype = NodeType.AABB
        self.meshtype = MeshType.AABB

        self.lytposition = (0.0, 0.0, 0.0)
        self.roomlinks = dict()

    def compute_lyt_position(self, wok_geom):
        wok_position = Vector(wok_geom.position)
        wok_vert = Vector(wok_geom.verts[wok_geom.facelist.vertices[0][0]])
        wok_mat_id = wok_geom.facelist.materials[0]
        for i in range(len(self.facelist.vertices)):
            mdl_mat_id = self.facelist.materials[i]
            if mdl_mat_id == wok_mat_id:
                mdl_vert = self.verts[self.facelist.vertices[i][0]]
                mdl_vert_from_root = self.from_root @ Vector(mdl_vert)
                self.lytposition = wok_vert + wok_position - mdl_vert_from_root
                break

    def add_to_collection(self, collection, options):
        mesh = self.mdl_to_edge_loop_mesh()
        bl_mesh = self.create_blender_mesh(self.name, mesh)
        obj = bpy.data.objects.new(self.name, bl_mesh)
        self.set_object_data(obj, options)
        collection.objects.link(obj)

        rebuild_walkmesh_materials(obj)
        for polygon_idx, polygon in enumerate(bl_mesh.polygons):
            polygon.material_index = self.facelist.materials[polygon_idx]
        self.apply_room_links(bl_mesh)

        return obj

    def apply_room_links(self, mesh):
        if ROOM_LINKS_COLORS in mesh.vertex_colors:
            colors = mesh.vertex_colors[ROOM_LINKS_COLORS]
        else:
            colors = mesh.vertex_colors.new(name=ROOM_LINKS_COLORS)

        for wok_edge_idx, transition in self.roomlinks.items():
            wok_face_idx = wok_edge_idx // 3
            aabb_face: BWMFace | None = None
            for walkable_idx, polygon in enumerate(
                [p for p in mesh.polygons if p.material_index not in NON_WALKABLE]
            ):
                if walkable_idx == wok_face_idx:
                    aabb_face = polygon
                    break
            if not aabb_face:
                continue
            for vert_idx, loop_idx in zip(aabb_face.vertices, aabb_face.loop_indices):
                if vert_idx in aabb_face.edge_keys[wok_edge_idx % 3]:
                    color = [0.0, (200.0 + transition) / 255.0, 0.0]
                    colors.data[loop_idx].color = [*color, 1.0]

    def unapply_room_links(self, obj: bpy.types.Object):
        self.roomlinks = {}
        if ROOM_LINKS_COLORS not in obj.data.vertex_colors:
            return
        colors = obj.data.vertex_colors[ROOM_LINKS_COLORS]
        for walkable_idx, tri in enumerate(
            [p for p in obj.data.loop_triangles if p.material_index not in NON_WALKABLE]
        ):
            for edge, loop_idx in enumerate(tri.loops):
                color = colors.data[loop_idx].color
                if color[0] > 0.0 or color[2] > 0.0 and (255.0 * color[1]) < 200.0:
                    continue
                edge_idx = 3 * walkable_idx + edge
                transition = int((255.0 * color[1]) - 200.0)
                self.roomlinks[edge_idx] = transition

    def set_object_data(
        self,
        obj: bpy.types.Object,
        options: dict[str, Any] | None = None,
    ):
        super().set_object_data(obj, options)

        obj.kb.lytposition = self.lytposition

    def load_object_data(
        self,
        obj: bpy.types.Object,
        eval_obj: bpy.types.Object,
        options: dict[str, Any] | None = None,
    ):
        super().load_object_data(obj, eval_obj, options)

        self.lytposition = obj.kb.lytposition

        self.unapply_room_links(eval_obj)
