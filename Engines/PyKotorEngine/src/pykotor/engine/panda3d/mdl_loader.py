"""MDL to Panda3D Geom converter.

This module converts PyKotor MDL/MDX models into Panda3D GeomNode structures
with full support for vertex data, tangent space, and face topology.

References:
----------
    Libraries/PyKotor/src/pykotor/resource/formats/mdl - MDL data structures
    vendor/reone/src/libs/graphics/mesh.cpp - Mesh conversion
    vendor/KotOR.js/src/three/odyssey/OdysseyModel3D.ts - Model conversion
    /panda3d/panda3d-docs/programming/internal-structures/procedural-generation - Geom creation
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

# Add PyKotor to path
pykotor_path = Path(__file__).parents[5] / "Libraries" / "PyKotor" / "src"
if str(pykotor_path) not in sys.path:
    sys.path.insert(0, str(pykotor_path))

from panda3d.core import (
    Geom,
    GeomNode,
    GeomTriangles,
    GeomVertexArrayFormat,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
    InternalName,
    NodePath,
    Vec3,
)

from pykotor.resource.formats.mdl import read_mdl
from utility.common.geometry import Vector3

if TYPE_CHECKING:
    from pykotor.resource.formats.mdl.mdl_data import MDL, MDLNode, MDLMesh, MDLFace
from pykotor.engine.materials.base import IMaterialManager


class MDLLoader:
    """Loads KotOR MDL/MDX files and converts them to Panda3D geometry.
    
    References:
    ----------
        vendor/reone/src/libs/graphics/mesh.cpp:100-350 - Mesh conversion
        vendor/KotOR.js/src/three/odyssey/OdysseyModel3D.ts:150-400 - Geometry creation
        /panda3d/panda3d-docs - GeomVertexData and Geom creation
    """
    
    def __init__(
        self,
        material_manager: IMaterialManager | None = None,
        resource_loader: Any | None = None,
        texture_base_path: Path | None = None,
    ):
        """Initialize the MDL loader."""
        self._mdl: MDL | None = None
        self._mdx_path: str | None = None
        self._material_manager = material_manager
        self._resource_loader = resource_loader
        self._texture_base_path = texture_base_path
        self._active_texture_base: Path | None = None
    
    def load(self, mdl_path: str, mdx_path: str | None = None) -> NodePath:
        """Load an MDL/MDX file and convert to Panda3D scene graph.
        
        Args:
        ----
            mdl_path: Path to the MDL file
            mdx_path: Path to the MDX file (auto-detected if None)
        
        Returns:
        -------
            NodePath containing the loaded model geometry
        
        References:
        ----------
            vendor/reone/src/libs/resource/provider/models.cpp:50-100 - Model loading
            Libraries/PyKotor/src/pykotor/resource/formats/mdl/io_mdl.py - MDL reader
        """
        # Auto-detect MDX path
        if mdx_path is None:
            mdx_path = mdl_path.replace(".mdl", ".mdx")
        
        self._mdx_path = mdx_path
        
        # Read MDL file
        # Reference: Libraries/PyKotor/src/pykotor/resource/formats/mdl/io_mdl.py:2085-2130
        self._mdl = read_mdl(mdl_path)

        # Track texture base directory for materials
        mdl_dir = Path(mdl_path).parent
        self._active_texture_base = self._texture_base_path or mdl_dir
        
        # Prepare skin meshes
        # Reference: Libraries/PyKotor/src/pykotor/resource/formats/mdl/mdl_data.py:150-175
        self._mdl.prepare_skin_meshes()
        
        # Convert root node
        root_np = NodePath("root")
        self._convert_node_hierarchy(self._mdl.root_node, root_np)
        
        return root_np
    
    def _convert_node_hierarchy(self, mdl_node: MDLNode, parent_np: NodePath) -> None:
        """Recursively convert MDL node hierarchy to Panda3D.
        
        Args:
        ----
            mdl_node: MDL node to convert
            parent_np: Parent NodePath
        
        References:
        ----------
            vendor/reone/src/libs/scene/node/model.cpp:59-97 - buildNodeTree()
        """
        # Convert this node
        if mdl_node.mesh:
            node_np = self._convert_mesh_node(mdl_node)
        else:
            node_np = NodePath(mdl_node.name)
        
        # Set local transform
        # Reference: /panda3d/panda3d-docs - NodePath.setPos(), setHpr()
        node_np.setPos(
            mdl_node.position.x,
            mdl_node.position.y,
            mdl_node.position.z
        )
        
        # Convert quaternion to HPR
        from panda3d.core import Quat
        quat = Quat(
            mdl_node.orientation.w,
            mdl_node.orientation.x,
            mdl_node.orientation.y,
            mdl_node.orientation.z
        )
        hpr = quat.getHpr()
        node_np.setHpr(hpr)
        
        # Attach to parent
        node_np.reparentTo(parent_np)
        
        # Recursively convert children
        for child in mdl_node.children:
            self._convert_node_hierarchy(child, node_np)
    
    def _convert_mesh_node(self, mdl_node: MDLNode) -> NodePath:
        """Convert an MDL mesh node to Panda3D GeomNode.
        
        Args:
        ----
            mdl_node: MDL node containing mesh data
        
        Returns:
        -------
            NodePath containing the GeomNode
        
        References:
        ----------
            vendor/reone/src/libs/graphics/mesh.cpp:100-350 - Mesh conversion
            /panda3d/panda3d-docs - Geom creation
        """
        mesh = mdl_node.mesh
        if not mesh:
            return NodePath(mdl_node.name)
        
        # Create vertex format
        vertex_format = self._create_vertex_format(mesh)
        
        # Create vertex data
        # Reference: /panda3d/panda3d-docs - GeomVertexData(name, format, Geom.UHStatic)
        vdata = GeomVertexData(mdl_node.name, vertex_format, Geom.UHStatic)
        vdata.setNumRows(len(mesh.vertex_positions))
        
        # Write vertex data
        self._write_vertex_data(vdata, mesh)
        
        # Create geometry primitive
        geom = self._create_geometry(vdata, mesh)
        
        # Create GeomNode
        geom_node = GeomNode(mdl_node.name)
        geom_node.addGeom(geom)
        
        node = NodePath(geom_node)

        if self._material_manager:
            material = self._material_manager.create_material_from_mesh(mesh)
            if self._resource_loader and self._active_texture_base:
                material.load_resources(self._resource_loader, self._active_texture_base)
            self._material_manager.apply_material(node, material)

        return node
    
    def _create_vertex_format(self, mesh: MDLMesh) -> GeomVertexFormat:
        """Create vertex format for the mesh.
        
        Args:
        ----
            mesh: MDL mesh to create format for
        
        Returns:
        -------
            GeomVertexFormat with appropriate vertex attributes
        
        References:
        ----------
            vendor/reone/src/libs/graphics/mesh.cpp:120-150 - Vertex layout
            /panda3d/panda3d-docs - GeomVertexArrayFormat.addColumn()
        """
        # Create array format
        # Reference: /panda3d/panda3d-docs - GeomVertexArrayFormat()
        array = GeomVertexArrayFormat()
        
        # Position, normal, UV (required)
        # Reference: /panda3d/panda3d-docs - addColumn(name, num_components, numeric_type, contents)
        array.addColumn(InternalName.getVertex(), 3, Geom.NTFloat32, Geom.CPoint)
        array.addColumn(InternalName.getNormal(), 3, Geom.NTFloat32, Geom.CVector)
        array.addColumn(InternalName.getTexcoord(), 2, Geom.NTFloat32, Geom.CTexcoord)
        
        # Tangent space for normal mapping
        # Reference: vendor/mdlops/MDLOpsM.pm:5470-5596 - Tangent space
        if len(mesh.vertex_normals) > 0:
            array.addColumn(InternalName.getTangent(), 3, Geom.NTFloat32, Geom.CVector)
            array.addColumn(InternalName.getBinormal(), 3, Geom.NTFloat32, Geom.CVector)
        
        # Lightmap UV
        if mesh.has_lightmap and len(mesh.vertex_uv2) > 0:
            array.addColumn(InternalName.getTexcoord().getIndex(1), 2, Geom.NTFloat32, Geom.CTexcoord)
        
        # Bone weights for skinning
        # Reference: vendor/reone/src/libs/graphics/mesh.cpp:140-150
        if mesh.skin:
            array.addColumn(InternalName.make("bone_indices"), 4, Geom.NTUint16, Geom.CIndex)
            array.addColumn(InternalName.make("bone_weights"), 4, Geom.NTFloat32, Geom.CVector)
        
        # Register format
        # Reference: /panda3d/panda3d-docs - GeomVertexFormat.registerFormat()
        format = GeomVertexFormat()
        format.addArray(array)
        return GeomVertexFormat.registerFormat(format)
    
    def _write_vertex_data(self, vdata: GeomVertexData, mesh: MDLMesh) -> None:
        """Write vertex data from MDL mesh to Panda3D GeomVertexData.
        
        Args:
        ----
            vdata: Panda3D vertex data to write to
            mesh: MDL mesh source data
        
        References:
        ----------
            vendor/reone/src/libs/graphics/mesh.cpp:200-280 - Vertex data writing
            /panda3d/panda3d-docs - GeomVertexWriter
        """
        # Create writers
        # Reference: /panda3d/panda3d-docs - GeomVertexWriter(vdata, 'column_name')
        vertex_writer = GeomVertexWriter(vdata, InternalName.getVertex())
        normal_writer = GeomVertexWriter(vdata, InternalName.getNormal())
        uv_writer = GeomVertexWriter(vdata, InternalName.getTexcoord())
        
        # Optional writers
        tangent_writer = None
        binormal_writer = None
        if len(mesh.vertex_normals) > 0:
            tangent_writer = GeomVertexWriter(vdata, InternalName.getTangent())
            binormal_writer = GeomVertexWriter(vdata, InternalName.getBinormal())
        
        uv2_writer = None
        if mesh.has_lightmap and len(mesh.vertex_uv2) > 0:
            uv2_writer = GeomVertexWriter(vdata, InternalName.getTexcoord().getIndex(1))
        
        bone_indices_writer = None
        bone_weights_writer = None
        if mesh.skin:
            bone_indices_writer = GeomVertexWriter(vdata, InternalName.make("bone_indices"))
            bone_weights_writer = GeomVertexWriter(vdata, InternalName.make("bone_weights"))
        
        # Compute tangent space if needed
        tangent_data = None
        if tangent_writer and len(mesh.faces) > 0 and len(mesh.vertex_uv) > 0:
            tangent_data = self._compute_tangent_space(mesh)
        
        # Write vertex data
        # Reference: /panda3d/panda3d-docs - writer.addData3(x, y, z)
        for i, pos in enumerate(mesh.vertex_positions):
            # Position
            vertex_writer.addData3(pos.x, pos.y, pos.z)
            
            # Normal
            if i < len(mesh.vertex_normals):
                normal = mesh.vertex_normals[i]
                normal_writer.addData3(normal.x, normal.y, normal.z)
            else:
                normal_writer.addData3(0, 0, 1)
            
            # UV
            if i < len(mesh.vertex_uv):
                uv = mesh.vertex_uv[i]
                uv_writer.addData2(uv[0], uv[1])
            else:
                uv_writer.addData2(0, 0)
            
            # Tangent space
            if tangent_writer and tangent_data and i in tangent_data:
                tangent, binormal = tangent_data[i]
                tangent_writer.addData3(tangent.x, tangent.y, tangent.z)
                binormal_writer.addData3(binormal.x, binormal.y, binormal.z)
            elif tangent_writer:
                tangent_writer.addData3(1, 0, 0)
                binormal_writer.addData3(0, 1, 0)
            
            # Lightmap UV
            if uv2_writer and i < len(mesh.vertex_uv2):
                uv2 = mesh.vertex_uv2[i]
                uv2_writer.addData2(uv2[0], uv2[1])
            
            # Bone weights
            if bone_indices_writer and mesh.skin and i < len(mesh.skin.vertex_bones):
                bone_vertex = mesh.skin.vertex_bones[i]
                bone_indices_writer.addData4i(
                    int(bone_vertex.bone_indices[0]) if len(bone_vertex.bone_indices) > 0 else 0,
                    int(bone_vertex.bone_indices[1]) if len(bone_vertex.bone_indices) > 1 else 0,
                    int(bone_vertex.bone_indices[2]) if len(bone_vertex.bone_indices) > 2 else 0,
                    int(bone_vertex.bone_indices[3]) if len(bone_vertex.bone_indices) > 3 else 0,
                )
                bone_weights_writer.addData4(
                    bone_vertex.bone_weights[0] if len(bone_vertex.bone_weights) > 0 else 0.0,
                    bone_vertex.bone_weights[1] if len(bone_vertex.bone_weights) > 1 else 0.0,
                    bone_vertex.bone_weights[2] if len(bone_vertex.bone_weights) > 2 else 0.0,
                    bone_vertex.bone_weights[3] if len(bone_vertex.bone_weights) > 3 else 0.0,
                )
            elif bone_indices_writer:
                bone_indices_writer.addData4i(0, 0, 0, 0)
                bone_weights_writer.addData4(1.0, 0.0, 0.0, 0.0)
    
    def _compute_tangent_space(self, mesh: MDLMesh) -> dict[int, tuple[Vector3, Vector3]]:
        """Compute per-vertex tangent and binormal vectors.
        
        Args:
        ----
            mesh: MDL mesh to compute tangent space for
        
        Returns:
        -------
            Dictionary mapping vertex index to (tangent, binormal)
        
        References:
        ----------
            Libraries/PyKotor/src/pykotor/resource/formats/mdl/io_mdl.py:1449-1578
            vendor/mdlops/MDLOpsM.pm:5470-5596 - Tangent space calculation
        """
        from pykotor.resource.formats.mdl.io_mdl import _calculate_tangent_space, _calculate_face_normal
        
        vertex_tangents: dict[int, list[Vector3]] = {}
        vertex_binormals: dict[int, list[Vector3]] = {}
        
        # Compute per-face tangent space
        for face in mesh.faces:
            v1 = mesh.vertex_positions[face.v1]
            v2 = mesh.vertex_positions[face.v2]
            v3 = mesh.vertex_positions[face.v3]
            
            if face.v1 >= len(mesh.vertex_uv) or face.v2 >= len(mesh.vertex_uv) or face.v3 >= len(mesh.vertex_uv):
                continue
            
            uv1 = mesh.vertex_uv[face.v1]
            uv2 = mesh.vertex_uv[face.v2]
            uv3 = mesh.vertex_uv[face.v3]
            
            face_normal, _ = _calculate_face_normal(v1, v2, v3)
            tangent, binormal = _calculate_tangent_space(v1, v2, v3, uv1, uv2, uv3, face_normal)
            
            # Accumulate for each vertex
            for v_idx in [face.v1, face.v2, face.v3]:
                if v_idx not in vertex_tangents:
                    vertex_tangents[v_idx] = []
                    vertex_binormals[v_idx] = []
                vertex_tangents[v_idx].append(tangent)
                vertex_binormals[v_idx].append(binormal)
        
        # Average accumulated tangents/binormals
        result = {}
        for v_idx in vertex_tangents:
            # Average tangents
            avg_tangent = Vector3(0, 0, 0)
            for t in vertex_tangents[v_idx]:
                avg_tangent = Vector3(avg_tangent.x + t.x, avg_tangent.y + t.y, avg_tangent.z + t.z)
            count = len(vertex_tangents[v_idx])
            avg_tangent = Vector3(avg_tangent.x / count, avg_tangent.y / count, avg_tangent.z / count)
            
            # Normalize
            length = (avg_tangent.x**2 + avg_tangent.y**2 + avg_tangent.z**2) ** 0.5
            if length > 0:
                avg_tangent = Vector3(avg_tangent.x / length, avg_tangent.y / length, avg_tangent.z / length)
            
            # Average binormals
            avg_binormal = Vector3(0, 0, 0)
            for b in vertex_binormals[v_idx]:
                avg_binormal = Vector3(avg_binormal.x + b.x, avg_binormal.y + b.y, avg_binormal.z + b.z)
            avg_binormal = Vector3(avg_binormal.x / count, avg_binormal.y / count, avg_binormal.z / count)
            
            # Normalize
            length = (avg_binormal.x**2 + avg_binormal.y**2 + avg_binormal.z**2) ** 0.5
            if length > 0:
                avg_binormal = Vector3(avg_binormal.x / length, avg_binormal.y / length, avg_binormal.z / length)
            
            result[v_idx] = (avg_tangent, avg_binormal)
        
        return result
    
    def _create_geometry(self, vdata: GeomVertexData, mesh: MDLMesh) -> Geom:
        """Create Panda3D geometry from vertex data and face topology.
        
        Args:
        ----
            vdata: Vertex data
            mesh: MDL mesh with face data
        
        Returns:
        -------
            Geom object containing the mesh geometry
        
        References:
        ----------
            vendor/reone/src/libs/graphics/mesh.cpp:300-350 - Primitive creation
            /panda3d/panda3d-docs - GeomTriangles
        """
        # Create triangle primitive
        prim = GeomTriangles(Geom.UHStatic)
        
        # Add face indices
        for face in mesh.faces:
            # KotOR uses clockwise winding, Panda3D uses counter-clockwise
            # Reverse winding order
            prim.addVertices(face.v1, face.v3, face.v2)
        
        prim.closePrimitive()
        
        # Create Geom
        geom = Geom(vdata)
        geom.addPrimitive(prim)
        
        return geom

