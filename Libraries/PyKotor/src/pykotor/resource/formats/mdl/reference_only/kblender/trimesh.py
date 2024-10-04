from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

import bpy
import bpy.types

from typing_extensions import Literal

from pykotor.common.geometry import Vector2, Vector3
from pykotor.resource.formats.mdl.reference_only import material
from pykotor.resource.formats.mdl.reference_only.base import BaseNode
from pykotor.resource.formats.mdl.reference_only.constants import (
    UV_MAP_LIGHTMAP,
    UV_MAP_MAIN,
    MeshType,
    NodeType,
    RootType,
)

if TYPE_CHECKING:
    from pykotor.resource.formats.mdl.reference_only.constants import ImportOptions


# If unpack_list is needed, we can define a simple implementation
def unpack_list(list_of_tuples: list[tuple]) -> list:
    return [item for sublist in list_of_tuples for item in sublist]


# Import constants from a relative path


class Compression:
    DISABLED: Literal[0] = 0
    ENABLED: Literal[1] = 1


class FaceList:
    def __init__(self):
        self.vertices: list[int] = []  # vertex indices
        self.uv: list[tuple[float, float]] = []  # UV indices
        self.materials: list[int] = []  # material indices
        self.normals: list[tuple[float, float, float]] = []  # normal vectors


class EdgeLoopMesh:
    def __init__(self):
        self.verts: list[Vector3] = []  # vertex coordinates
        self.weights: list[int] = []  # vertex bone weights
        self.constraints: list[int] = []  # vertex constraints (danglymesh)

        self.loop_verts: list[int] = []  # vertex indices
        self.loop_normals: list[Vector3] = []  # normal vectors
        self.loop_uv1: list[Vector2] = []  # UV indices
        self.loop_uv2: list[Vector2] = []  # UV indices
        self.loop_tangents: list[tuple[float, float, float]] = []
        self.loop_bitangents: list[tuple[float, float, float]] = []

        self.face_materials: list[int] = []
        self.face_normals: list[tuple[float, float, float]] = []

    def num_faces(self) -> int:
        return self.num_loops() // 3

    def num_loops(self) -> int:
        return len(self.loop_verts)

    def num_verts(self) -> int:
        return len(self.verts)


class SimilarMDLVertex:
    def __init__(
        self,
        coords: tuple[float, float, float],
    ):
        self.coords: tuple[float, float, float] = coords
        self.value: tuple[int, ...] = tuple(int(val * 10000) for val in self.coords)

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, rhs: SimilarMDLVertex) -> bool:
        if not isinstance(rhs, SimilarMDLVertex):
            return NotImplemented
        return self.value == rhs.value


class SimilarEdgeLoopMeshVertex:
    def __init__(
        self,
        coords: tuple[float, float, float],
        normal: tuple[float, float, float],
        uv1: tuple[float, float],
        uv2: tuple[float, float],
    ):
        self.coords: tuple[float, float, float] = coords
        self.normal: tuple[float, float, float] = normal
        self.uv1: tuple[float, float] = uv1
        self.uv2: tuple[float, float] = uv2
        self.value = tuple(int(val * 10000) for val in (*self.coords, *self.normal, *self.uv1, *self.uv2))

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, rhs: SimilarEdgeLoopMeshVertex) -> bool:
        return self.value == rhs.value


class TrimeshNode(BaseNode):
    meshtype: ClassVar[MeshType] = MeshType.TRIMESH
    nodetype: ClassVar[NodeType] = NodeType.TRIMESH
    compression: ClassVar[Compression] = Compression.ENABLED

    def __init__(self, name: str = "UNNAMED"):
        BaseNode.__init__(self, name=name)

        # Properties
        self.center: tuple[float, float, float] = (0.0, 0.0, 0.0)  # Unused ?
        self.lightmapped: int = 0
        self.render: int = 1
        self.shadow: int = 1
        self.beaming: int = 0
        self.background_geometry: int = 0
        self.dirt_enabled: int = 0
        self.dirt_texture: int = 1
        self.dirt_worldspace: int = 1
        self.hologram_donotdraw: int = 0
        self.animateuv: int = 0
        self.uvdirectionx: float = 1.0
        self.uvdirectiony: float = 1.0
        self.uvjitter: float = 0.0
        self.uvjitterspeed: float = 0.0
        self.alpha: float = 1.0
        self.transparencyhint: int = 0
        self.selfillumcolor: tuple[float, float, float] = (0.0, 0.0, 0.0)
        self.ambient: tuple[float, float, float] = (0.2, 0.2, 0.2)
        self.diffuse: tuple[float, float, float] = (0.8, 0.8, 0.8)
        self.bitmap: str | Literal["NULL"] = "NULL"  # noqa: PYI051
        self.bitmap2: str | Literal["NULL"] = "NULL"  # noqa: PYI051
        self.tangentspace: int = 0
        self.rotatetexture: int = 0

        # Mesh
        self.verts: list[Vector3] = []
        self.normals: list[Vector3] = []
        self.uv1: list[Vector2] = []
        self.uv2: list[Vector2] = []
        self.tangents: list[Vector3] = []
        self.bitangents: list[Vector3] = []
        self.tangentspacenormals: list[Vector3] = []
        self.weights: list[int] = []
        self.constraints: list[int] = []
        self.facelist: FaceList = FaceList()

    def add_to_collection(
        self,
        collection: bpy.types.Collection,
        options: ImportOptions,
    ) -> bpy.types.Object:
        mesh = self.mdl_to_edge_loop_mesh()
        bl_mesh = self.create_blender_mesh(self.name, mesh)
        obj = bpy.data.objects.new(self.name, bl_mesh)
        self.apply_edge_loop_mesh(mesh, obj)
        self.set_object_data(obj, options)
        if options.build_materials and self.roottype == RootType.MODEL:
            material.rebuild_object_materials(
                obj,
                options.texture_search_paths,
                options.lightmap_search_paths,
            )
        collection.objects.link(obj)
        return obj

    def mdl_to_edge_loop_mesh(self) -> EdgeLoopMesh:
        num_faces = len(self.facelist.vertices)
        num_loops = 3 * num_faces
        mesh = EdgeLoopMesh()
        mesh.loop_verts = [-1] * num_loops
        mesh.loop_normals = [(0, 0, 1)] * num_loops
        mesh.loop_uv1 = [Vector2(0, 0) for _ in range(num_loops)]
        mesh.loop_uv2 = [Vector2(0, 0) for _ in range(num_loops)]
        if self.compression != Compression.DISABLED:
            attrs_to_vert_idx = {}
            for face_idx in range(num_faces):
                face_verts: list[int] = self.facelist.vertices[face_idx]
                for i in range(3):
                    loop_idx: int = 3 * face_idx + i
                    vert_idx: int = face_verts[i]
                    vert: Vector3 = self.verts[vert_idx]
                    attrs = SimilarMDLVertex(vert)
                    if attrs in attrs_to_vert_idx:
                        mesh.loop_verts[loop_idx] = attrs_to_vert_idx[attrs]
                    else:
                        num_verts: int = len(mesh.verts)
                        mesh.verts.append(vert)
                        if self.weights:
                            mesh.weights.append(self.weights[vert_idx])
                        if self.constraints:
                            mesh.constraints.append(self.constraints[vert_idx])
                        attrs_to_vert_idx[attrs] = num_verts
                        mesh.loop_verts[loop_idx] = num_verts
                    if self.normals:
                        mesh.loop_normals[loop_idx] = self.normals[vert_idx]
                    if self.uv1:
                        mesh.loop_uv1[loop_idx] = self.uv1[vert_idx]
                    if self.uv2:
                        mesh.loop_uv2[loop_idx] = self.uv2[vert_idx]
                    if self.tangents and self.bitangents:
                        mesh.loop_tangents[loop_idx] = self.tangents[vert_idx]
                        mesh.loop_bitangents[loop_idx] = self.bitangents[vert_idx]
        else:
            mesh.verts = self.verts
            mesh.weights = self.weights
            mesh.constraints = self.constraints
            for face_idx in range(num_faces):
                face_verts = self.facelist.vertices[face_idx]
                for i in range(3):
                    loop_idx = 3 * face_idx + i
                    vert_idx = face_verts[i]
                    mesh.loop_verts[loop_idx] = vert_idx
                    mesh.loop_normals[loop_idx] = self.normals[vert_idx]
                    if self.uv1:
                        mesh.loop_uv1[loop_idx] = self.uv1[vert_idx]
                    if self.uv2:
                        mesh.loop_uv2[loop_idx] = self.uv2[vert_idx]
                    if self.tangents and self.bitangents:
                        mesh.loop_tangents[loop_idx] = self.tangents[vert_idx]
                        mesh.loop_bitangents[loop_idx] = self.bitangents[vert_idx]
        mesh.face_materials = self.facelist.materials
        mesh.face_normals = self.facelist.normals
        return mesh

    def create_blender_mesh(
        self,
        name: str,
        mesh: EdgeLoopMesh,
    ) -> bpy.types.Mesh:
        bl_mesh: bpy.types.Mesh = bpy.data.meshes.new(name)
        bl_mesh.vertices.add(len(mesh.verts))
        bl_mesh.vertices.foreach_set("co", [vert.x for vert in mesh.verts])
        bl_mesh.vertices.foreach_set("co", [vert.y for vert in mesh.verts])
        bl_mesh.vertices.foreach_set("co", [vert.z for vert in mesh.verts])
        bl_mesh.loops.add(mesh.num_loops())
        bl_mesh.loops.foreach_set("vertex_index", mesh.loop_verts)
        bl_mesh.polygons.add(mesh.num_faces())
        bl_mesh.polygons.foreach_set("loop_start", range(0, mesh.num_loops(), 3))
        bl_mesh.polygons.foreach_set("loop_total", [3] * mesh.num_faces())
        bl_mesh.polygons.foreach_set("use_smooth", [True] * mesh.num_faces())
        bl_mesh.update()
        if mesh.loop_normals:
            bl_mesh.normals_split_custom_set([normal.x for normal in mesh.loop_normals])
            bl_mesh.normals_split_custom_set([normal.y for normal in mesh.loop_normals])
            bl_mesh.normals_split_custom_set([normal.z for normal in mesh.loop_normals])
            bl_mesh.use_auto_smooth = True
        if mesh.loop_uv1:
            uv_layer = bl_mesh.uv_layers.new(name=UV_MAP_MAIN, do_init=False)
            uv_layer.data.foreach_set("uv", unpack_list(mesh.loop_uv1))
        if mesh.loop_uv2:
            uv_layer = bl_mesh.uv_layers.new(name=UV_MAP_LIGHTMAP, do_init=False)
            uv_layer.data.foreach_set("uv", unpack_list(mesh.loop_uv2))
        return bl_mesh

    def apply_edge_loop_mesh(self, mesh: EdgeLoopMesh, obj: bpy.types.Object):
        pass

    def set_object_data(self, obj: bpy.types.Object, options: dict[str, Any]):
        BaseNode.set_object_data(self, obj, options)

        obj.kb.meshtype = self.meshtype
        obj.kb.bitmap = self.bitmap if self.bitmap != "NULL" else ""
        obj.kb.bitmap2 = self.bitmap2 if self.bitmap2 != "NULL" else ""
        obj.kb.alpha = self.alpha
        obj.kb.lightmapped = self.lightmapped == 1
        obj.kb.render = self.render == 1
        obj.kb.shadow = self.shadow == 1
        obj.kb.beaming = self.beaming == 1
        obj.kb.tangentspace = self.tangentspace == 1
        obj.kb.rotatetexture = self.rotatetexture == 1
        obj.kb.background_geometry = self.background_geometry == 1
        obj.kb.dirt_enabled = self.dirt_enabled == 1
        obj.kb.dirt_texture = self.dirt_texture
        obj.kb.dirt_worldspace = self.dirt_worldspace
        obj.kb.hologram_donotdraw = self.hologram_donotdraw == 1
        obj.kb.animateuv = self.animateuv == 1
        obj.kb.uvdirectionx = self.uvdirectionx
        obj.kb.uvdirectiony = self.uvdirectiony
        obj.kb.uvjitter = self.uvjitter
        obj.kb.uvjitterspeed = self.uvjitterspeed
        obj.kb.transparencyhint = self.transparencyhint
        obj.kb.selfillumcolor = self.selfillumcolor
        obj.kb.diffuse = self.diffuse
        obj.kb.ambient = self.ambient

    def load_object_data(
        self,
        obj: bpy.types.Object,
        eval_obj: bpy.types.Object,
        options: dict[str, Any],
    ):
        super().load_object_data(obj, eval_obj, options)

        self.meshtype = obj.kb.meshtype
        self.bitmap = obj.kb.bitmap if obj.kb.bitmap else "NULL"
        self.bitmap2 = obj.kb.bitmap2 if obj.kb.bitmap2 else "NULL"
        self.alpha = obj.kb.alpha
        self.lightmapped = 1 if obj.kb.lightmapped else 0
        self.render = 1 if obj.kb.render else 0
        self.shadow = 1 if obj.kb.shadow else 0
        self.beaming = 1 if obj.kb.beaming else 0
        self.tangentspace = 1 if obj.kb.tangentspace else 0
        self.rotatetexture = 1 if obj.kb.rotatetexture else 0
        self.background_geometry = 1 if obj.kb.background_geometry else 0
        self.dirt_enabled = 1 if obj.kb.dirt_enabled else 0
        self.dirt_texture = obj.kb.dirt_texture
        self.dirt_worldspace = obj.kb.dirt_worldspace
        self.hologram_donotdraw = 1 if obj.kb.hologram_donotdraw else 0
        self.animateuv = 1 if obj.kb.animateuv else 0
        self.uvdirectionx = obj.kb.uvdirectionx
        self.uvdirectiony = obj.kb.uvdirectiony
        self.uvjitter = obj.kb.uvjitter
        self.uvjitterspeed = obj.kb.uvjitterspeed
        self.transparencyhint = obj.kb.transparencyhint
        self.selfillumcolor = obj.kb.selfillumcolor
        self.diffuse = obj.kb.diffuse
        self.ambient = obj.kb.ambient

        mesh = self.unapply_edge_loop_mesh(eval_obj)
        self.edge_loop_to_mdl_mesh(mesh)

    def unapply_edge_loop_mesh(self, obj: bpy.types.Object) -> EdgeLoopMesh:
        bl_mesh: bpy.types.Mesh = obj.data
        bl_mesh.calc_loop_triangles()
        bl_mesh.calc_normals_split()
        if self.tangentspace and bl_mesh.uv_layers:
            bl_mesh.calc_tangents(uvmap=bl_mesh.uv_layers[0].name)
        mesh = EdgeLoopMesh()
        for vert in bl_mesh.vertices:
            mesh.verts.append(vert.co[:3])
        for face in bl_mesh.loop_triangles:
            for i in range(3):
                mesh.loop_verts.append(face.vertices[i])
                mesh.loop_normals.append(face.split_normals[i])
                loop_idx = face.loops[i]
                if len(bl_mesh.uv_layers) > 0:
                    mesh.loop_uv1.append(bl_mesh.uv_layers[0].data[loop_idx].uv[:2])
                if self.lightmapped:
                    if len(bl_mesh.uv_layers) > 1:
                        mesh.loop_uv2.append(bl_mesh.uv_layers[1].data[loop_idx].uv[:2])
                    else:
                        raise RuntimeError(f"Lightmapped object '{obj.name}' is missing second UV map")
                if self.tangentspace:
                    loop = bl_mesh.loops[loop_idx]
                    mesh.loop_tangents.append(loop.tangent[:3])
                    mesh.loop_bitangents.append(loop.bitangent[:3])
            mesh.face_materials.append(face.material_index)
            mesh.face_normals.append(face.normal)
        return mesh

    def edge_loop_to_mdl_mesh(
        self,
        mesh: EdgeLoopMesh,
    ):
        self.verts.clear()
        self.normals.clear()
        self.uv1.clear()
        self.uv2.clear()
        self.tangents.clear()
        self.bitangents.clear()
        self.tangentspacenormals.clear()
        self.weights.clear()
        self.constraints.clear()
        self.facelist.vertices.clear()
        self.facelist.uv.clear()

        if self.compression:
            attrs_to_vert_idx = {}
            for face_idx in range(mesh.num_faces()):
                vert_indices = []
                for i in range(3):
                    loop_idx = 3 * face_idx + i
                    vert_idx = mesh.loop_verts[loop_idx]
                    attrs = SimilarEdgeLoopMeshVertex(
                        mesh.verts[vert_idx],
                        mesh.loop_normals[loop_idx],
                        mesh.loop_uv1[loop_idx] if mesh.loop_uv1 else (0.0, 0.0),
                        mesh.loop_uv2[loop_idx] if mesh.loop_uv2 else (0.0, 0.0),
                    )
                    if attrs not in attrs_to_vert_idx:
                        attrs_to_vert_idx[attrs] = len(self.verts)
                        self.verts.append(attrs.coords)
                        self.normals.append(attrs.normal)
                        if mesh.loop_uv1:
                            self.uv1.append(attrs.uv1)
                        if mesh.loop_uv2:
                            self.uv2.append(attrs.uv2)
                        if mesh.loop_tangents and mesh.loop_bitangents:
                            self.tangents.append(mesh.loop_tangents[loop_idx])
                            self.bitangents.append(mesh.loop_bitangents[loop_idx])
                            self.tangentspacenormals.append(mesh.loop_normals[loop_idx])
                        if mesh.weights:
                            self.weights.append(mesh.weights[vert_idx])
                        if mesh.constraints:
                            self.constraints.append(mesh.constraints[vert_idx])
                    vert_indices.append(attrs_to_vert_idx[attrs])
                self.facelist.vertices.append(vert_indices)
                self.facelist.uv.append(vert_indices)
        else:
            self.verts = mesh.verts
            self.weights = mesh.weights
            self.constraints = mesh.constraints
            normals = [Vector3((0, 0, 0)) for _ in range(len(mesh.verts))]
            if mesh.loop_tangents and mesh.loop_bitangents:
                tangents = [Vector3((0, 0, 0)) for _ in range(len(mesh.verts))]
                bitangents = [Vector3((0, 0, 0)) for _ in range(len(mesh.verts))]
                tanspacenormals = [Vector3((0, 0, 0)) for _ in range(len(mesh.verts))]
            self.uv1 = [(0, 0) for _ in range(len(mesh.verts))] if mesh.loop_uv1 else []
            self.uv2 = [(0, 0) for _ in range(len(mesh.verts))] if mesh.loop_uv2 else []

            for face_idx in range(mesh.num_faces()):
                start_loop_idx = 3 * face_idx
                face_verts = mesh.loop_verts[start_loop_idx : start_loop_idx + 3]
                for i, vert_idx in enumerate(face_verts):
                    loop_idx = start_loop_idx + i
                    normals[vert_idx] += Vector3(mesh.loop_normals[loop_idx])
                    if mesh.loop_uv1:
                        self.uv1[vert_idx] = mesh.loop_uv1[loop_idx]
                    if mesh.loop_uv2:
                        self.uv2[vert_idx] = mesh.loop_uv2[loop_idx]
                    if mesh.loop_tangents and mesh.loop_bitangents:
                        tangents[vert_idx] += Vector3(mesh.loop_tangents[loop_idx])
                        bitangents[vert_idx] += Vector3(mesh.loop_bitangents[loop_idx])
                        tanspacenormals[vert_idx] += Vector3(mesh.loop_normals[loop_idx])
                self.facelist.vertices.append(face_verts)
                self.facelist.uv.append(face_verts)

            self.normals = [normal.normal() for normal in normals]
            if mesh.loop_tangents and mesh.loop_bitangents:
                self.tangents = [tangent.normal() for tangent in tangents]
                self.bitangents = [bitangent.normal() for bitangent in bitangents]
                self.tangentspacenormals = [normal.normal() for normal in tanspacenormals]

        self.facelist.materials = mesh.face_materials
        self.facelist.normals = mesh.face_normals
