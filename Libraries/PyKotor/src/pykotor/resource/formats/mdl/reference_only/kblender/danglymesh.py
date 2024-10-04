from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from pykotor.resource.formats.mdl.reference_only.constants import MeshType, NodeType
from pykotor.resource.formats.mdl.reference_only.trimesh import EdgeLoopMesh, TrimeshNode

if TYPE_CHECKING:
    import bpy

    from typing_extensions import Literal

    from pykotor.gl.models.mdl import EdgeLoopMesh
    from pykotor.resource.formats.mdl.reference_only.constants import ImportOptions

CONSTRAINTS: Literal["constraints"] = "constraints"


class DanglymeshNode(TrimeshNode):
    nodetype: ClassVar[NodeType | Literal["DANGLYMESH"]] = NodeType.DANGLYMESH
    meshtype: ClassVar[MeshType | Literal["DANGLYMESH"]] = MeshType.DANGLYMESH

    def __init__(self, name="UNNAMED"):
        super().__init__(name)
        self.period: float = 1.0
        self.tightness: float = 1.0
        self.displacement: float = 1.0

    def apply_edge_loop_mesh(
        self,
        mesh: EdgeLoopMesh,
        obj: bpy.types.Object,
    ):
        super().apply_edge_loop_mesh(mesh, obj)
        self.apply_vertex_constraints(mesh, obj)

    def apply_vertex_constraints(
        self,
        mesh: EdgeLoopMesh,
        obj: bpy.types.Object,
    ):
        group = obj.vertex_groups.new(name=CONSTRAINTS)
        for vert_idx, constraint in enumerate(mesh.constraints):
            weight = constraint / 255
            group.add([vert_idx], weight, "REPLACE")
        obj.kb.constraints = group.name

    def set_object_data(
        self,
        obj: bpy.types.Object,
        options: ImportOptions,
    ):
        super().set_object_data(obj, options)
        obj.kb.period = self.period
        obj.kb.tightness = self.tightness
        obj.kb.displacement = self.displacement

    def load_object_data(
        self,
        obj: bpy.types.Object,
        eval_obj: bpy.types.Object,
        options: ImportOptions,
    ):
        super().load_object_data(obj, eval_obj, options)
        self.period = obj.kb.period
        self.tightness = obj.kb.tightness
        self.displacement = obj.kb.displacement

    def unapply_edge_loop_mesh(
        self,
        obj: bpy.types.Object,
    ) -> EdgeLoopMesh:
        mesh = super().unapply_edge_loop_mesh(obj)
        self.unapply_vertex_constraints(obj, mesh)
        return mesh

    def unapply_vertex_constraints(
        self,
        obj: bpy.types.Object,
        mesh: EdgeLoopMesh,
    ):
        if CONSTRAINTS not in obj.vertex_groups:
            mesh.constraints = [0] * len(mesh.verts)
            return
        group = obj.vertex_groups.get(CONSTRAINTS)
        if group is None:
            mesh.constraints = [0] * len(mesh.verts)
            return
        mesh.constraints = [int(255.0 * group.weight(i)) for i in range(len(mesh.verts))]
