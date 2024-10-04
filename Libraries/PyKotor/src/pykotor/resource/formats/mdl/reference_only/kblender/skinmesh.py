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

from typing import TYPE_CHECKING, ClassVar, Literal

from pykotor.resource.formats.mdl.reference_only.constants import MeshType, NodeType
from pykotor.resource.formats.mdl.reference_only.trimesh import TrimeshNode

if TYPE_CHECKING:
    import bpy

    from pykotor.resource.formats.mdl.reference_only.trimesh import EdgeLoopMesh


class SkinmeshNode(TrimeshNode):
    nodetype: ClassVar[NodeType | Literal["SKIN"]] = NodeType.SKIN
    meshtype: ClassVar[MeshType | Literal["SKIN"]] = MeshType.SKIN

    def __init__(self, name: str = "UNNAMED"):
        TrimeshNode.__init__(self, name)

    def apply_edge_loop_mesh(
        self,
        mesh: EdgeLoopMesh,
        obj: bpy.types.Object,
    ) -> None:
        TrimeshNode.apply_edge_loop_mesh(self, mesh, obj)
        self.apply_bone_weights(mesh, obj)

    def apply_bone_weights(
        self,
        mesh: EdgeLoopMesh,
        obj: bpy.types.Object,
    ) -> None:
        groups: dict[str, bpy.types.VertexGroup] = {}
        for vert_idx, vert_weights in enumerate(mesh.weights):
            for bone_name, weight in vert_weights:
                if bone_name in groups:
                    groups[bone_name].add([vert_idx], weight, "REPLACE")
                else:
                    group = obj.vertex_groups.new(name=bone_name)
                    group.add([vert_idx], weight, "REPLACE")
                    groups[bone_name] = group

    def unapply_edge_loop_mesh(
        self,
        obj: bpy.types.Object,
    ) -> EdgeLoopMesh:
        mesh = TrimeshNode.unapply_edge_loop_mesh(self, obj)
        self.unapply_bone_weights(obj, mesh)
        return mesh

    def unapply_bone_weights(
        self,
        obj: bpy.types.Object,
        mesh: EdgeLoopMesh,
    ) -> None:
        mesh.weights = [[] for _ in range(len(mesh.verts))]
        for vert_idx in range(len(mesh.verts)):
            vert = obj.data.vertices[vert_idx]
            vert_weights: list[tuple[str, float]] = []
            for group_weight in vert.groups:
                if group_weight.weight == 0.0:
                    continue
                group = obj.vertex_groups[group_weight.group]
                vert_weights.append((group.name, group_weight.weight))
            vert_weights.sort(key=lambda x: x[1], reverse=True)
            if len(vert_weights) > 4:
                vert_weights = vert_weights[0:3]
            mesh.weights[vert_idx] = vert_weights
