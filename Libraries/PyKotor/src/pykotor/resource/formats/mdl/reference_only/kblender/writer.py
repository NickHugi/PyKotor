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

from pathlib import Path
from typing import TYPE_CHECKING

from pykotor.common.geometry import Vector3
from pykotor.resource.formats.mdl.reference_only.binwriter import BinaryWriter
from pykotor.resource.formats.mdl.reference_only.constants import NodeType
from pykotor.resource.formats.mdl.reference_only.types import (
    AABB_NEGATIVE_X,
    AABB_NEGATIVE_Y,
    AABB_NEGATIVE_Z,
    AABB_NO_CHILDREN,
    AABB_POSITIVE_X,
    AABB_POSITIVE_Y,
    AABB_POSITIVE_Z,
    ANIM_FN_PTR_1_K1_PC,
    ANIM_FN_PTR_1_K1_XBOX,
    ANIM_FN_PTR_1_K2_PC,
    ANIM_FN_PTR_1_K2_XBOX,
    ANIM_FN_PTR_2_K1_PC,
    ANIM_FN_PTR_2_K1_XBOX,
    ANIM_FN_PTR_2_K2_PC,
    ANIM_FN_PTR_2_K2_XBOX,
    CLASS_BY_VALUE,
    CTRL_BASE_ORIENTATION,
    CTRL_BASE_POSITION,
    CTRL_FLAG_BEZIER,
    CTRL_LIGHT_COLOR,
    CTRL_LIGHT_MULTIPLIER,
    CTRL_LIGHT_RADIUS,
    CTRL_MESH_ALPHA,
    CTRL_MESH_SCALE,
    CTRL_MESH_SELFILLUMCOLOR,
    DANGLY_FN_PTR_1_K1_PC,
    DANGLY_FN_PTR_1_K1_XBOX,
    DANGLY_FN_PTR_1_K2_PC,
    DANGLY_FN_PTR_1_K2_XBOX,
    DANGLY_FN_PTR_2_K1_PC,
    DANGLY_FN_PTR_2_K1_XBOX,
    DANGLY_FN_PTR_2_K2_PC,
    DANGLY_FN_PTR_2_K2_XBOX,
    EMITTER_CONTROLLER_KEYS,
    EMITTER_FLAG_AFFECTED_WIND,
    EMITTER_FLAG_BOUNCE,
    EMITTER_FLAG_DEPTH_TEXTURE,
    EMITTER_FLAG_INHERIT,
    EMITTER_FLAG_INHERIT_LOCAL,
    EMITTER_FLAG_INHERIT_PART,
    EMITTER_FLAG_INHERIT_VEL,
    EMITTER_FLAG_P2P,
    EMITTER_FLAG_P2P_SEL,
    EMITTER_FLAG_RANDOM,
    EMITTER_FLAG_SPLAT,
    EMITTER_FLAG_TINTED,
    MESH_FN_PTR_1_K1_PC,
    MESH_FN_PTR_1_K1_XBOX,
    MESH_FN_PTR_1_K2_PC,
    MESH_FN_PTR_1_K2_XBOX,
    MESH_FN_PTR_2_K1_PC,
    MESH_FN_PTR_2_K1_XBOX,
    MESH_FN_PTR_2_K2_PC,
    MESH_FN_PTR_2_K2_XBOX,
    MODEL_ANIM,
    MODEL_FN_PTR_1_K1_PC,
    MODEL_FN_PTR_1_K1_XBOX,
    MODEL_FN_PTR_1_K2_PC,
    MODEL_FN_PTR_1_K2_XBOX,
    MODEL_FN_PTR_2_K1_PC,
    MODEL_FN_PTR_2_K1_XBOX,
    MODEL_FN_PTR_2_K2_XBOX,
    MODEL_MODEL,
    NODE_AABB,
    NODE_BASE,
    NODE_DANGLY,
    NODE_EMITTER,
    NODE_LIGHT,
    NODE_MESH,
    NODE_REFERENCE,
    NODE_SABER,
    NODE_SKIN,
    NUM_SABER_VERTS,
    SKIN_FN_PTR_1_K1_PC,
    SKIN_FN_PTR_1_K1_XBOX,
    SKIN_FN_PTR_1_K2_PC,
    SKIN_FN_PTR_1_K2_XBOX,
    SKIN_FN_PTR_2_K1_PC,
    SKIN_FN_PTR_2_K1_XBOX,
    SKIN_FN_PTR_2_K2_PC,
    SKIN_FN_PTR_2_K2_XBOX,
    ControllerKey,
)

if TYPE_CHECKING:
    import os

    from pykotor.resource.formats.bwm.bwm_data import BWMNodeAABB
    from pykotor.resource.formats.mdl.mdl_data import MDL, MDLNode


class MdlWriter:
    def __init__(
        self,
        path: os.PathLike | str,
        model: MDL,
        *,
        tsl: bool,
        xbox: bool,
        compress_quaternions: bool = False,
    ):
        self.path: Path = Path(path)
        basepath = self.path.parent / self.path.stem
        mdx_path = basepath.with_suffix(".mdx")

        self.mdl_file_handle: BinaryWriter = BinaryWriter(path, "little")
        self.mdx_file_handle: BinaryWriter = BinaryWriter(mdx_path, "little")

        self.model: MDL = model
        self.tsl: bool = tsl
        self.xbox: bool = xbox
        self.compress_quaternions: bool = compress_quaternions

        # Model
        self.mdl_pos: int = 0
        self.mdx_pos: int = 0
        self.mdl_size: int = 0
        self.mdx_size: int = 0
        self.off_name_offsets: int = 0
        self.off_anim_offsets: int = 0

        # Nodes
        self.nodes: list[BWMNodeAABB] = []
        self.node_names: list[str] = []
        self.name_offsets: list[int] = []
        self.node_offsets: list[int] = []
        self.children_offsets: list[int] = []
        self.parent_indices: list[int | None] = []
        self.child_indices: list[list[int]] = []
        self.node_idx_by_name: dict[str, int] = {}
        self.node_idx_by_number: dict[int, int] = {}

        # Lights
        self.flare_sizes_offsets: dict[int, list[int]] = {}
        self.flare_positions_offsets: dict[int, list[int]] = {}
        self.flare_colorshifts_offsets: dict[int, list[int]] = {}
        self.flare_texture_offset_offsets: dict[int, list[int]] = {}
        self.flare_textures_offsets: dict[int, list[int]] = {}

        # Meshes
        self.mesh_bounding_boxes: dict[int, list[float]] = {}
        self.mesh_averages: dict[int, list[float]] = {}
        self.mesh_radii: dict[int, list[float]] = {}
        self.mesh_total_areas: dict[int, float] = {}
        self.verts_offsets: dict[int, list[int]] = {}
        self.faces_offsets: dict[int, list[int]] = {}
        self.index_count_offsets: dict[int, list[int]] = {}
        self.index_offset_offsets: dict[int, list[int]] = {}
        self.inv_count_offsets: dict[int, list[int]] = {}
        self.indices_offsets: dict[int, list[int]] = {}
        self.mdx_offsets: dict[int, int] = {}

        # Skinmeshes
        self.bonemap_offsets: dict[int, list[int]] = {}
        self.qbone_offsets: dict[int, list[int]] = {}
        self.tbone_offsets: dict[int, list[int]] = {}
        self.skin_garbage_offsets: dict[int, list[int]] = {}

        # Danglymeshes
        self.constraints_offsets: dict[int, list[int]] = {}
        self.dangly_verts_offsets: dict[int, list[int]] = {}

        # AABB
        self.aabbs: dict[int, list[float]] = {}
        self.aabb_offsets: dict[int, int] = {}

        # Sabers
        self.saber_verts_offsets: dict[int, list[int]] = {}
        self.saber_uv_offsets: dict[int, list[int]] = {}
        self.saber_normals_offsets: dict[int, list[int]] = {}

        # Controllers
        self.controller_keys: list[ControllerKey] = []
        self.controller_data: list[float] = []
        self.controller_offsets: list[int] = []
        self.controller_counts: list[int] = []
        self.controller_data_offsets: list[int] = []
        self.controller_data_counts: list[int] = []

        # Animations
        self.anim_offsets: list[int] = []
        self.anim_events_offsets: list[int] = []
        self.anim_nodes: list[BWMNodeAABB] = []
        self.anim_node_offsets: list[int] = []
        self.anim_children_offsets: list[int] = []
        self.anim_parent_indices: list[int | None] = []
        self.anim_child_indices: list[list[int]] = []
        self.anim_controller_keys: list[list[ControllerKey]] = []
        self.anim_controller_data: list[list[float]] = []
        self.anim_controller_offsets: list[int] = []
        self.anim_controller_counts: list[int] = []
        self.anim_controller_data_offsets: list[int] = []
        self.anim_controller_data_counts: list[int] = []

    def save(self):
        self.peek_model()

        self.save_file_header()
        self.save_geometry_header()
        self.save_model_header()
        self.save_names()
        self.save_animations()
        self.save_nodes()

    def peek_model(self):
        self.mdl_pos = 80 + 116  # geometry header + model header
        self.off_name_offsets = self.mdl_pos

        self.peek_nodes(self.model.root_node)

        # Nodes
        for node_idx, node in enumerate(self.nodes):
            self.node_names.append(node.name)
            self.node_idx_by_name[node.name] = node_idx
            self.node_idx_by_number[node.node_number] = node_idx

        # Animation Nodes
        for anim_idx, anim in enumerate(self.model.animations):
            self.anim_nodes.append([])
            self.anim_parent_indices.append([])
            self.anim_child_indices.append([])
            self.peek_anim_nodes(anim_idx, anim.root_node)

        self.mdl_pos += 4 * len(self.nodes)  # name offsets

        self.peek_node_names()
        self.peek_animations()
        self.peek_node_data()

        self.mdl_size = self.mdl_pos
        self.mdx_size = self.mdx_pos

    def peek_nodes(
        self,
        node: BWMNodeAABB,
        parent_idx: int | None = None,
    ):
        node_idx = len(self.nodes)
        self.nodes.append(node)
        self.parent_indices.append(parent_idx)
        self.child_indices.append([])

        for child in node.children:
            child_idx = len(self.nodes)
            self.child_indices[node_idx].append(child_idx)
            self.peek_nodes(child, node_idx)

    def peek_anim_nodes(
        self,
        anim_idx: int,
        node: BWMNodeAABB,
        parent_idx: int | None = None,
    ):
        node_idx = len(self.anim_nodes[anim_idx])
        self.anim_nodes[anim_idx].append(node)
        self.anim_parent_indices[anim_idx].append(parent_idx)
        self.anim_child_indices[anim_idx].append([])

        for child in node.children:
            if not child.animated:
                continue
            child_idx = len(self.anim_nodes[anim_idx])
            self.anim_child_indices[anim_idx][node_idx].append(child_idx)
            self.peek_anim_nodes(anim_idx, child, node_idx)

    def peek_node_names(self):
        for node in self.nodes:
            self.name_offsets.append(self.mdl_pos)
            self.mdl_pos += len(node.name) + 1

    def peek_animations(self):
        self.off_anim_offsets = self.mdl_pos
        self.mdl_pos += 4 * len(self.model.animations)

        for anim_idx, anim in enumerate(self.model.animations):
            # Animation Header
            self.anim_offsets.append(self.mdl_pos)
            self.mdl_pos += 136

            # Events
            self.anim_events_offsets.append(self.mdl_pos)
            self.mdl_pos += 36 * len(anim.events)

            self.anim_node_offsets.append([])
            self.anim_children_offsets.append([])
            self.anim_controller_keys.append([])
            self.anim_controller_data.append([])
            self.anim_controller_counts.append([])
            self.anim_controller_data_counts.append([])
            self.anim_controller_offsets.append([])
            self.anim_controller_data_offsets.append([])

            # Animation Nodes
            for node_idx, node in enumerate(self.anim_nodes[anim_idx]):
                model_node = self.nodes[self.node_idx_by_number[node.node_number]]
                type_flags = self.get_node_flags(model_node)

                # Geometry Header
                self.anim_node_offsets[anim_idx].append(self.mdl_pos)
                self.mdl_pos += 80

                # Children
                self.anim_children_offsets[anim_idx].append(self.mdl_pos)
                self.mdl_pos += 4 * len(self.anim_child_indices[anim_idx][node_idx])

                # Controllers
                ctrl_keys = []
                ctrl_data = []
                self.peek_anim_controllers(node, type_flags, ctrl_keys, ctrl_data)
                ctrl_count = len(ctrl_keys)
                ctrl_data_count = len(ctrl_data)
                self.anim_controller_keys[anim_idx].append(ctrl_keys)
                self.anim_controller_data[anim_idx].append(ctrl_data)
                self.anim_controller_counts[anim_idx].append(ctrl_count)
                self.anim_controller_data_counts[anim_idx].append(ctrl_data_count)
                self.anim_controller_offsets[anim_idx].append(self.mdl_pos)
                self.mdl_pos += 16 * ctrl_count

                # Controller Data
                self.anim_controller_data_offsets[anim_idx].append(self.mdl_pos)
                self.mdl_pos += 4 * ctrl_data_count

    def peek_node_data(self):
        for node_idx, node in enumerate(self.nodes):
            # Geometry Header
            self.node_offsets.append(self.mdl_pos)
            self.mdl_pos += 80

            type_flags = self.get_node_flags(node)

            # Light Header
            if type_flags & NODE_LIGHT:
                self.mdl_pos += 92

                # Lens Flares
                if node.lensflares:
                    self.flare_sizes_offsets[node_idx] = self.mdl_pos
                    self.mdl_pos += 4 * len(node.flare_list.sizes)

                    self.flare_positions_offsets[node_idx] = self.mdl_pos
                    self.mdl_pos += 4 * len(node.flare_list.positions)

                    self.flare_colorshifts_offsets[node_idx] = self.mdl_pos
                    self.mdl_pos += 4 * 3 * len(node.flare_list.colorshifts)

                    self.flare_texture_offset_offsets[node_idx] = self.mdl_pos
                    self.mdl_pos += 4 * len(node.flare_list.textures)

                    self.flare_textures_offsets[node_idx] = []
                    for tex in node.flare_list.textures:
                        self.flare_textures_offsets[node_idx].append(self.mdl_pos)
                        self.mdl_pos += len(tex) + 1

            # Emitter Header
            if type_flags & NODE_EMITTER:
                self.mdl_pos += 224

            # Reference Header
            if type_flags & NODE_REFERENCE:
                self.mdl_pos += 36

            # Mesh Header
            if type_flags & NODE_MESH:
                self.mdl_pos += 332
                if self.tsl:
                    self.mdl_pos += 8
                if self.xbox:
                    self.mdl_pos -= 4

            # Skin Header
            if type_flags & NODE_SKIN:
                self.mdl_pos += 100

            # Dangly Header
            if type_flags & NODE_DANGLY:
                self.mdl_pos += 28

            # AABB Header
            if type_flags & NODE_AABB:
                self.mdl_pos += 4

            # Saber Header
            if type_flags & NODE_SABER:
                self.mdl_pos += 20

            # Mesh Data
            if type_flags & NODE_MESH:
                num_faces = len(node.facelist.vertices)

                # Faces
                self.faces_offsets[node_idx] = self.mdl_pos
                self.mdl_pos += 32 * num_faces

                # Vertex Indices Offset
                self.index_offset_offsets[node_idx] = self.mdl_pos
                if not type_flags & NODE_SABER:
                    self.mdl_pos += 4

                # Vertices
                num_verts = NUM_SABER_VERTS if type_flags & NODE_SABER else len(node.verts)
                if not self.xbox:
                    self.verts_offsets[node_idx] = self.mdl_pos
                    self.mdl_pos += 4 * 3 * num_verts

                # Vertex Indices Count
                self.index_count_offsets[node_idx] = self.mdl_pos
                if not type_flags & NODE_SABER:
                    self.mdl_pos += 4

                # Inverted Counter
                self.inv_count_offsets[node_idx] = self.mdl_pos
                if not type_flags & NODE_SABER:
                    self.mdl_pos += 4

                # Vertex Indices
                self.indices_offsets[node_idx] = self.mdl_pos
                if not type_flags & NODE_SABER:
                    self.mdl_pos += 2 * 3 * num_faces

                # MDX data
                if type_flags & NODE_SABER:
                    self.mdx_offsets[node_idx] = 0
                else:
                    # Vertex Coords
                    self.mdx_offsets[node_idx] = self.mdx_pos
                    self.mdx_pos += 4 * 3 * (num_verts + 1)
                    # Normals
                    if self.xbox:
                        self.mdx_pos += 4 * (num_verts + 1)
                    else:
                        self.mdx_pos += 4 * 3 * (num_verts + 1)
                    # UV1
                    if node.uv1:
                        self.mdx_pos += 4 * 2 * (num_verts + 1)
                    # UV2
                    if node.uv2:
                        self.mdx_pos += 4 * 2 * (num_verts + 1)
                    # Tangent Space
                    if node.tangentspace:
                        if self.xbox:
                            self.mdx_pos += 4 * 3 * (num_verts + 1)
                        else:
                            self.mdx_pos += 4 * 9 * (num_verts + 1)
                    if type_flags & NODE_SKIN:
                        if self.xbox:
                            self.mdx_pos += (4 * 4 + 2 * 4) * (num_verts + 1)
                        else:
                            self.mdx_pos += 4 * 8 * (num_verts + 1)

                # Bounding Box, Average, Total Area
                bb_min = Vector3()
                bb_max = Vector3()
                average = Vector3()
                total_area = 0.0
                for face in node.facelist.vertices:
                    verts = [Vector3(node.verts[i]) for i in face]
                    for vert in verts:
                        bb_min.x = min(bb_min.x, vert.x)
                        bb_min.y = min(bb_min.y, vert.y)
                        bb_min.z = min(bb_min.z, vert.z)
                        bb_max.x = max(bb_max.x, vert.x)
                        bb_max.y = max(bb_max.y, vert.y)
                        bb_max.z = max(bb_max.z, vert.z)
                        average += vert
                    edge1 = verts[1] - verts[0]
                    edge2 = verts[2] - verts[0]
                    edge3 = verts[2] - verts[1]
                    area = self.calculate_face_area(edge1, edge2, edge3)
                    if area != 1.0:
                        total_area += area
                average /= 3 * len(node.facelist.vertices)
                self.mesh_bounding_boxes[node_idx] = [*bb_min, *bb_max]
                self.mesh_averages[node_idx] = [*average]
                self.mesh_total_areas[node_idx] = total_area

                # Radius
                radius = 0.0
                for face in node.facelist.vertices:
                    verts = [Vector3(node.verts[i]) for i in face]
                    for vert in verts:
                        radius = max(radius, (vert - average).length)
                self.mesh_radii[node_idx] = radius

            # Skin Data
            if type_flags & NODE_SKIN:
                num_bones = len(self.nodes)

                # Bonemap
                self.bonemap_offsets[node_idx] = self.mdl_pos
                if self.xbox:
                    self.mdl_pos += 2 * num_bones
                else:
                    self.mdl_pos += 4 * num_bones

                # QBones
                self.qbone_offsets[node_idx] = self.mdl_pos
                self.mdl_pos += 4 * 4 * num_bones

                # TBones
                self.tbone_offsets[node_idx] = self.mdl_pos
                self.mdl_pos += 4 * 3 * num_bones

                # Garbage
                self.skin_garbage_offsets[node_idx] = self.mdl_pos
                self.mdl_pos += 4 * num_bones

            # Dangly Data
            if type_flags & NODE_DANGLY:
                # Constraints
                self.constraints_offsets[node_idx] = self.mdl_pos
                self.mdl_pos += 4 * len(node.constraints)

                # Vertices
                self.dangly_verts_offsets[node_idx] = self.mdl_pos
                self.mdl_pos += 4 * 3 * len(node.verts)

            # AABB Data
            if type_flags & NODE_AABB:
                self.aabb_offsets[node_idx] = []
                aabbs = self.generate_aabb_tree(node)
                for _ in range(len(aabbs)):
                    self.aabb_offsets[node_idx].append(self.mdl_pos)
                    self.mdl_pos += 40
                self.aabbs[node_idx] = aabbs
  
            # Saber Data
            if type_flags & NODE_SABER:
                self.saber_verts_offsets[node_idx] = self.mdl_pos
                self.mdl_pos += 4 * 3 * NUM_SABER_VERTS

                self.saber_uv_offsets[node_idx] = self.mdl_pos
                self.mdl_pos += 4 * 2 * NUM_SABER_VERTS

                self.saber_normals_offsets[node_idx] = self.mdl_pos
                self.mdl_pos += 4 * 3 * NUM_SABER_VERTS

            # Children
            self.children_offsets.append(self.mdl_pos)
            self.mdl_pos += 4 * len(node.children)

            # Controllers
            ctrl_keys: list[ControllerKey] = []
            ctrl_data: list[float] = []
            self.peek_controllers(node, type_flags, ctrl_keys, ctrl_data)
            ctrl_count = len(ctrl_keys)
            ctrl_data_count = len(ctrl_data)
            self.controller_keys.append(ctrl_keys)
            self.controller_data.append(ctrl_data)
            self.controller_counts.append(ctrl_count)
            self.controller_data_counts.append(ctrl_data_count)
            self.controller_offsets.append(self.mdl_pos)
            self.mdl_pos += 16 * ctrl_count

            # Controller Data
            self.controller_data_offsets.append(self.mdl_pos)
            self.mdl_pos += 4 * ctrl_data_count

    def peek_controllers(
        self,
        node: MDLNode,
        type_flags: int,
        out_keys: list[ControllerKey],
        out_data: list[float],
    ):
        if not node.parent:
            return

        data_count = 0

        # Base Controllers

        out_keys.append(ControllerKey(CTRL_BASE_POSITION, 1, data_count, data_count + 1, 3))
        out_data.append(0.0)  # timekey
        out_data.extend(list(node.position))
        data_count += 4

        out_keys.append(ControllerKey(CTRL_BASE_ORIENTATION, 1, data_count, data_count + 1, 4))
        out_data.append(0.0)  # timekey
        out_data.extend(list(node.orientation[1:4]))
        out_data.append(node.orientation[0])
        data_count += 5

        # Mesh Controllers

        if type_flags & NODE_MESH:
            out_keys.append(ControllerKey(CTRL_MESH_ALPHA, 1, data_count, data_count + 1, 1))
            out_data.append(0.0)  # timekey
            out_data.append(node.alpha)
            data_count += 2

            out_keys.append(ControllerKey(CTRL_MESH_SCALE, 1, data_count, data_count + 1, 1))
            out_data.append(0.0)  # timekey
            out_data.append(node.scale)
            data_count += 2

            out_keys.append(ControllerKey(CTRL_MESH_SELFILLUMCOLOR, 1, data_count, data_count + 1, 3))
            out_data.append(0.0)  # timekey
            for val in node.selfillumcolor:
                out_data.append(val)
            data_count += 4

        # Light Controllers

        if type_flags & NODE_LIGHT:
            out_keys.append(ControllerKey(CTRL_LIGHT_RADIUS, 1, data_count, data_count + 1, 1))
            out_data.append(0.0)  # timekey
            out_data.append(node.radius)
            data_count += 2

            out_keys.append(ControllerKey(CTRL_LIGHT_MULTIPLIER, 1, data_count, data_count + 1, 1))
            out_data.append(0.0)  # timekey
            out_data.append(node.multiplier)
            data_count += 2

            out_keys.append(ControllerKey(CTRL_LIGHT_COLOR, 1, data_count, data_count + 1, 3))
            out_data.append(0.0)  # timekey
            for val in node.color:
                out_data.append(val)
            data_count += 4

        # Emitter Controllers

        if type_flags & NODE_EMITTER:
            for ctrl_val, key, dim in EMITTER_CONTROLLER_KEYS:
                value = getattr(node, key, None)
                if value is None:
                    continue
                out_keys.append(ControllerKey(ctrl_val, 1, data_count, data_count + 1, dim))
                out_data.append(0.0)  # timekey
                if dim == 1:
                    out_data.append(value)
                else:
                    out_data.extend(list(value))
                data_count += 1 + dim

    def peek_anim_controllers(
        self,
        node: MDLNode,
        type_flags: int,
        out_keys: list[ControllerKey],
        out_data: list[float],
    ):
        def append_keyframes(
            key: str,
            ctrl_type: int,
            dim: int,
            data_count: int,
        ):
            if key not in node.keyframes:
                return data_count
            keyframes = node.keyframes[key]
            if not keyframes:
                return data_count
            num_rows = len(keyframes)
            row_lengths = {len(row) for row in keyframes}
            assert len(row_lengths) == 1, "All rows must have the same size"
            num_values = len(keyframes[0]) - 1
            bezier = num_values == 3 * dim
            assert num_values == dim or bezier, f"Expected {dim} or {3 * dim} values, got {num_values}"
            out_keys.append(
                ControllerKey(
                    ctrl_type,
                    num_rows,
                    data_count,
                    data_count + num_rows,
                    (dim | CTRL_FLAG_BEZIER) if bezier else dim,
                )
            )
            out_data.extend([keyframe[0] for keyframe in keyframes])  # timekeys
            num_columns = 3 * dim if bezier else dim
            out_data.extend([val for keyframe in keyframes for val in keyframe[1 : 1 + num_columns]])
            return data_count + (1 + num_columns) * num_rows

        def append_orientation_keyframes(data_count: int) -> int:
            if not self.compress_quaternions:
                return append_keyframes("orientation", CTRL_BASE_ORIENTATION, 4, data_count)

            if "orientation" not in node.keyframes:
                return data_count
            keyframes = node.keyframes["orientation"]
            if not keyframes:
                return data_count
            num_rows = len(keyframes)
            out_keys.append(
                ControllerKey(
                    CTRL_BASE_ORIENTATION,
                    num_rows,
                    data_count,
                    data_count + num_rows,
                    2,
                )
            )
            out_data.extend([keyframes[i][0] for i in range(num_rows)])  # timekeys
            for i in range(num_rows):
                x, y, z, w = keyframes[i][1:]
                if w < 0.0:
                    x *= -1.0
                    y *= -1.0
                    z *= -1.0
                ix = int((x + 1.0) * 1023.0)
                iy = int((y + 1.0) * 1023.0)
                iz = int((z + 1.0) * 511.0)
                comp = ix | (iy << 11) | (iz << 22)
                out_data.append(comp)
            return data_count + 2 * num_rows

        if not node.parent:
            return

        data_count = 0

        # Base Controllers

        data_count = append_keyframes("position", CTRL_BASE_POSITION, 3, data_count)
        data_count = append_orientation_keyframes(data_count)

        # Mesh Controllers

        if type_flags & NODE_MESH:
            data_count = append_keyframes("alpha", CTRL_MESH_ALPHA, 1, data_count)
            data_count = append_keyframes("scale", CTRL_MESH_SCALE, 1, data_count)
            data_count = append_keyframes(
                "selfillumcolor",
                CTRL_MESH_SELFILLUMCOLOR,
                3,
                data_count,
            )

        # Light ControllersCTRL_LIGHT_RADIUS

        if type_flags & NODE_LIGHT:
            data_count = append_keyframes("radius", CTRL_LIGHT_RADIUS, 1, data_count)
            data_count = append_keyframes("multiplier", CTRL_LIGHT_MULTIPLIER, 1, data_count)
            data_count = append_keyframes("color", CTRL_LIGHT_COLOR, 3, data_count)

        # Emitter Controllers

        if type_flags & NODE_EMITTER:
            for ctrl_type, key, dim in EMITTER_CONTROLLER_KEYS:
                data_count = append_keyframes(key, ctrl_type, dim, data_count)

    def save_file_header(self):
        self.mdl_file_handle.write_uint32(0)  # pseudo signature
        self.mdl_file_handle.write_uint32(self.mdl_size)
        self.mdl_file_handle.write_uint32(self.mdx_size)

    def save_geometry_header(self):
        if self.tsl:
            if self.xbox:
                fn_ptr1 = MODEL_FN_PTR_1_K2_XBOX
                fn_ptr2 = MODEL_FN_PTR_2_K2_XBOX
            else:
                fn_ptr1 = MODEL_FN_PTR_1_K2_PC
                fn_ptr2 = MODEL_FN_PTR_1_K1_XBOX
        elif self.xbox:
            fn_ptr1 = MODEL_FN_PTR_1_K1_XBOX
            fn_ptr2 = MODEL_FN_PTR_2_K1_XBOX
        else:
            fn_ptr1 = MODEL_FN_PTR_1_K1_PC
            fn_ptr2 = MODEL_FN_PTR_2_K1_PC

        model_name = self.model.name.ljust(32, "\0")
        off_root_node = self.node_offsets[0]
        total_num_nodes = len(self.nodes)
        ref_count = 0
        model_type = MODEL_MODEL

        self.mdl_file_handle.write_uint32(fn_ptr1)
        self.mdl_file_handle.write_uint32(fn_ptr2)
        self.mdl_file_handle.write_string(model_name)
        self.mdl_file_handle.write_uint32(off_root_node)
        self.mdl_file_handle.write_uint32(total_num_nodes)
        self.put_array_def(0, 0)  # runtime array
        self.put_array_def(0, 0)  # runtime array
        self.mdl_file_handle.write_uint32(ref_count)
        self.mdl_file_handle.write_uint8(model_type)
        for _ in range(3):
            self.mdl_file_handle.write_uint8(0)  # padding

    def save_model_header(self):
        classification = next(iter(key for key, value in CLASS_BY_VALUE.items() if value == self.model.classification))
        subclassification = self.model.subclassification
        affected_by_fog = 1 if self.model.affected_by_fog else 0
        num_child_models = 0
        supermodel_ref = 0
        bounding_box = [-5.0, -5.0, -1.0, 5.0, 5.0, 10.0]
        radius = 7.0  # TODO  # TODO: document what needs 'todo' and who wrote this?
        scale = self.model.animscale
        supermodel_name = self.model.supermodel.ljust(32, "\0")

        if self.model.animroot != "NULL" and self.node_names.count(self.model.animroot) > 0:
            off_anim_root = self.node_offsets[self.node_names.index(self.model.animroot)]
        else:
            off_anim_root = self.node_offsets[0]

        mdx_size: int = self.mdx_size
        mdx_offset: int = 0

        self.mdl_file_handle.write_uint8(classification)
        self.mdl_file_handle.write_uint8(subclassification)
        self.mdl_file_handle.write_uint8(0)  # unknown
        self.mdl_file_handle.write_uint8(affected_by_fog)
        self.mdl_file_handle.write_uint32(num_child_models)
        self.put_array_def(self.off_anim_offsets, len(self.model.animations))  # animation offsets
        self.mdl_file_handle.write_uint32(supermodel_ref)
        for val in bounding_box:
            self.mdl_file_handle.write_float(val)
        self.mdl_file_handle.write_float(radius)
        self.mdl_file_handle.write_float(scale)
        self.mdl_file_handle.write_string(supermodel_name)
        self.mdl_file_handle.write_uint32(off_anim_root)
        self.mdl_file_handle.write_uint32(0)  # unknown
        self.mdl_file_handle.write_uint32(mdx_size)
        self.mdl_file_handle.write_uint32(mdx_offset)
        self.put_array_def(self.off_name_offsets, len(self.nodes))  # name offsets

    def save_names(self):
        for offset in self.name_offsets:
            self.mdl_file_handle.write_uint32(offset)
        for node in self.nodes:
            self.mdl_file_handle.write_c_string(node.name)

    def save_animations(self):
        for offset in self.anim_offsets:
            self.mdl_file_handle.write_uint32(offset)

        for anim_idx, anim in enumerate(self.model.animations):
            if self.tsl:
                if self.xbox:
                    fn_ptr1 = ANIM_FN_PTR_1_K2_XBOX
                    fn_ptr2 = ANIM_FN_PTR_2_K2_XBOX
                else:
                    fn_ptr1 = ANIM_FN_PTR_1_K2_PC
                    fn_ptr2 = ANIM_FN_PTR_2_K2_PC
            elif self.xbox:
                fn_ptr1 = ANIM_FN_PTR_1_K1_XBOX
                fn_ptr2 = ANIM_FN_PTR_2_K1_XBOX
            else:
                fn_ptr1 = ANIM_FN_PTR_1_K1_PC
                fn_ptr2 = ANIM_FN_PTR_2_K1_PC

            name = anim.name.ljust(32, "\0")
            off_root_node = self.anim_node_offsets[anim_idx][0]
            total_num_nodes = len(self.anim_nodes[anim_idx])
            ref_count = 0
            model_type = MODEL_ANIM
            anim_root = anim.animroot.ljust(32, "\0")

            self.mdl_file_handle.write_uint32(fn_ptr1)
            self.mdl_file_handle.write_uint32(fn_ptr2)
            self.mdl_file_handle.write_string(name)
            self.mdl_file_handle.write_uint32(off_root_node)
            self.mdl_file_handle.write_uint32(total_num_nodes)
            self.put_array_def(0, 0)  # runtime array
            self.put_array_def(0, 0)  # runtime array
            self.mdl_file_handle.write_uint32(ref_count)
            self.mdl_file_handle.write_uint8(model_type)
            for _ in range(3):
                self.mdl_file_handle.write_uint8(0)  # padding
            self.mdl_file_handle.write_float(anim.length)
            self.mdl_file_handle.write_float(anim.transtime)
            self.mdl_file_handle.write_string(anim_root)
            self.put_array_def(self.anim_events_offsets[anim_idx], len(anim.events))
            self.mdl_file_handle.write_uint32(0)  # padding

            for time, event in anim.events:
                self.mdl_file_handle.write_float(time)
                self.mdl_file_handle.write_string(event.ljust(32, "\0"))

            self.save_anim_nodes(anim_idx)

    def save_anim_nodes(self, anim_idx: int):
        for node_idx, node in enumerate(self.anim_nodes[anim_idx]):
            # Geometry Header

            type_flags = NODE_BASE
            name_index = self.node_names.index(node.name)
            off_root = self.anim_offsets[anim_idx]
            parent_idx = self.anim_parent_indices[anim_idx][node_idx]
            off_parent = self.anim_node_offsets[anim_idx][parent_idx] if parent_idx is not None else 0
            position = [0.0] * 3
            orientation = [1.0, 0.0, 0.0, 0.0]
            child_indices = self.anim_child_indices[anim_idx][node_idx]

            self.mdl_file_handle.write_uint16(type_flags)
            self.mdl_file_handle.write_uint16(node.node_number)
            self.mdl_file_handle.write_uint16(name_index)
            self.mdl_file_handle.write_uint16(0)  # padding
            self.mdl_file_handle.write_uint32(off_root)
            self.mdl_file_handle.write_uint32(off_parent)
            for val in position:
                self.mdl_file_handle.write_float(val)
            for val in orientation:
                self.mdl_file_handle.write_float(val)
            self.put_array_def(self.anim_children_offsets[anim_idx][node_idx], len(child_indices))
            self.put_array_def(
                self.anim_controller_offsets[anim_idx][node_idx],
                self.anim_controller_counts[anim_idx][node_idx],
            )
            self.put_array_def(
                self.anim_controller_data_offsets[anim_idx][node_idx],
                self.anim_controller_data_counts[anim_idx][node_idx],
            )

            # Children

            for child_idx in child_indices:
                self.mdl_file_handle.write_uint32(self.anim_node_offsets[anim_idx][child_idx])

            # Controllers

            for key in self.anim_controller_keys[anim_idx][node_idx]:
                if key.ctrl_type in [CTRL_BASE_POSITION, CTRL_BASE_ORIENTATION]:
                    unk1 = key.ctrl_type + 8
                else:
                    unk1 = 0xFFFF

                self.mdl_file_handle.write_uint32(key.ctrl_type)
                self.mdl_file_handle.write_uint16(unk1)
                self.mdl_file_handle.write_uint16(key.num_rows)
                self.mdl_file_handle.write_uint16(key.timekeys_start)
                self.mdl_file_handle.write_uint16(key.values_start)
                self.mdl_file_handle.write_uint8(key.num_columns)

                for _ in range(3):
                    self.mdl_file_handle.write_uint8(0)  # padding

            # Controller Data

            for val in self.anim_controller_data[anim_idx][node_idx]:
                if type(val) is int:
                    self.mdl_file_handle.write_uint32(val)
                else:
                    self.mdl_file_handle.write_float(val)

    def save_nodes(self):
        num_meshes = 0

        for node_idx, node in enumerate(self.nodes):
            # Geometry Header

            type_flags = self.get_node_flags(node)
            node_number = node.node_number
            name_index = node_idx
            off_root = 0
            parent_idx = self.parent_indices[node_idx]
            off_parent = self.node_offsets[parent_idx] if parent_idx is not None else 0
            position = node.position
            orientation = node.orientation
            child_indices = self.child_indices[node_idx]

            self.mdl_file_handle.write_uint16(type_flags)
            self.mdl_file_handle.write_uint16(node_number)
            self.mdl_file_handle.write_uint16(name_index)
            self.mdl_file_handle.write_uint16(0)  # padding
            self.mdl_file_handle.write_uint32(off_root)
            self.mdl_file_handle.write_uint32(off_parent)
            for val in position:
                self.mdl_file_handle.write_float(val)
            for val in orientation:
                self.mdl_file_handle.write_float(val)
            self.put_array_def(self.children_offsets[node_idx], len(child_indices))
            self.put_array_def(self.controller_offsets[node_idx], self.controller_counts[node_idx])
            self.put_array_def(
                self.controller_data_offsets[node_idx],
                self.controller_data_counts[node_idx],
            )

            # Light Header

            if type_flags & NODE_LIGHT:
                shadow = node.shadow
                light_priority = node.lightpriority
                ambient_only = node.ambientonly
                dynamic_type = node.dynamictype
                affect_dynamic = node.affectdynamic
                fading_light = node.fadinglight
                flare = 0  # always 0
                flare_radius = node.flareradius

                self.mdl_file_handle.write_float(flare_radius)
                self.put_array_def(0, 0)  # unknown
                self.put_array_def(
                    self.flare_sizes_offsets[node_idx] if node.lensflares else 0,
                    len(node.flare_list.sizes),
                )
                self.put_array_def(
                    self.flare_positions_offsets[node_idx] if node.lensflares else 0,
                    len(node.flare_list.positions),
                )
                self.put_array_def(
                    self.flare_colorshifts_offsets[node_idx] if node.lensflares else 0,
                    len(node.flare_list.colorshifts),
                )
                self.put_array_def(
                    self.flare_texture_offset_offsets[node_idx] if node.lensflares else 0,
                    len(node.flare_list.textures),
                )
                self.mdl_file_handle.write_int32(light_priority)
                self.mdl_file_handle.write_uint32(ambient_only)
                self.mdl_file_handle.write_uint32(dynamic_type)
                self.mdl_file_handle.write_uint32(affect_dynamic)
                self.mdl_file_handle.write_uint32(shadow)
                self.mdl_file_handle.write_uint32(flare)
                self.mdl_file_handle.write_uint32(fading_light)

                # Lens Flares
                if node.lensflares:
                    for size in node.flare_list.sizes:
                        self.mdl_file_handle.write_float(size)
                    for position in node.flare_list.positions:
                        self.mdl_file_handle.write_float(position)
                    for colorshift in node.flare_list.colorshifts:
                        for val in colorshift:
                            self.mdl_file_handle.write_float(val)
                    for i in range(len(node.flare_list.textures)):
                        off_tex = self.flare_textures_offsets[node_idx][i]
                        self.mdl_file_handle.write_uint32(off_tex)
                    for tex in node.flare_list.textures:
                        self.mdl_file_handle.write_c_string(tex)

            # Emitter Header

            if type_flags & NODE_EMITTER:
                update = node.update.ljust(32, "\0")
                render = node.emitter_render.ljust(32, "\0")
                blend = node.blend.ljust(32, "\0")
                texture = node.texture.ljust(32, "\0")
                chunk_name = node.chunk_name.ljust(16, "\0")
                twosided_tex = 1 if node.twosidedtex else 0
                loop = 1 if node.loop else 0
                frame_blending = 1 if node.frame_blending else 0
                depth_texture_name = node.depth_texture_name.ljust(32, "\0")

                flags = 0
                if node.p2p:
                    flags |= EMITTER_FLAG_P2P
                if node.p2p_sel:
                    flags |= EMITTER_FLAG_P2P_SEL
                if node.affected_by_wind:
                    flags |= EMITTER_FLAG_AFFECTED_WIND
                if node.tinted:
                    flags |= EMITTER_FLAG_TINTED
                if node.bounce:
                    flags |= EMITTER_FLAG_BOUNCE
                if node.random:
                    flags |= EMITTER_FLAG_RANDOM
                if node.inherit:
                    flags |= EMITTER_FLAG_INHERIT
                if node.inheritvel:
                    flags |= EMITTER_FLAG_INHERIT_VEL
                if node.inherit_local:
                    flags |= EMITTER_FLAG_INHERIT_LOCAL
                if node.splat:
                    flags |= EMITTER_FLAG_SPLAT
                if node.inherit_part:
                    flags |= EMITTER_FLAG_INHERIT_PART
                if node.depth_texture:
                    flags |= EMITTER_FLAG_DEPTH_TEXTURE

                self.mdl_file_handle.write_float(node.deadspace)
                self.mdl_file_handle.write_float(node.blastradius)
                self.mdl_file_handle.write_float(node.blastlength)
                self.mdl_file_handle.write_uint32(node.num_branches)
                self.mdl_file_handle.write_float(node.controlptsmoothing)
                self.mdl_file_handle.write_uint32(node.xgrid)
                self.mdl_file_handle.write_uint32(node.ygrid)
                self.mdl_file_handle.write_uint32(node.spawntype)
                self.mdl_file_handle.write_string(update)
                self.mdl_file_handle.write_string(render)
                self.mdl_file_handle.write_string(blend)
                self.mdl_file_handle.write_string(texture)
                self.mdl_file_handle.write_string(chunk_name)
                self.mdl_file_handle.write_uint32(twosided_tex)
                self.mdl_file_handle.write_uint32(loop)
                self.mdl_file_handle.write_uint16(node.renderorder)
                self.mdl_file_handle.write_uint8(frame_blending)
                self.mdl_file_handle.write_string(depth_texture_name)
                self.mdl_file_handle.write_uint8(0)  # padding
                self.mdl_file_handle.write_uint32(flags)

            # Reference Header

            if type_flags & NODE_REFERENCE:
                ref_model = node.refmodel.ljust(32, "\0")
                reattachable = node.reattachable

                self.mdl_file_handle.write_string(ref_model)
                self.mdl_file_handle.write_uint32(reattachable)

            # Mesh Header

            if type_flags & NODE_MESH:
                fn_ptr1, fn_ptr2 = self.get_mesh_fn_ptr(type_flags)

                bounding_box = self.mesh_bounding_boxes[node_idx]
                radius = self.mesh_radii[node_idx]
                average = self.mesh_averages[node_idx]
                diffuse = node.diffuse
                ambient = node.ambient
                transparency_hint = node.transparencyhint
                bitmap = node.bitmap.ljust(32, "\0")
                bitmap2 = node.bitmap2.ljust(32, "\0")
                bitmap3 = "".ljust(12, "\0")
                bitmap4 = "".ljust(12, "\0")
                animate_uv = node.animateuv
                uv_dir_x = node.uvdirectionx
                uv_dir_y = node.uvdirectiony
                uv_jitter = node.uvjitter
                uv_jitter_speed = node.uvjitterspeed

                mdx_data_size = 0
                mdx_data_bitmap = 0
                off_mdx_verts = 0xFFFFFFFF
                off_mdx_normals = 0xFFFFFFFF
                off_mdx_colors = 0xFFFFFFFF
                off_mdx_uv1 = 0xFFFFFFFF
                off_mdx_uv2 = 0xFFFFFFFF
                off_mdx_uv3 = 0xFFFFFFFF
                off_mdx_uv4 = 0xFFFFFFFF
                off_mdx_tan_space1 = 0xFFFFFFFF
                off_mdx_tan_space2 = 0xFFFFFFFF
                off_mdx_tan_space3 = 0xFFFFFFFF
                off_mdx_tan_space4 = 0xFFFFFFFF
                if not type_flags & NODE_SABER:
                    # Vertex Coordinates
                    mdx_data_bitmap = MDX_FLAG_VERTEX
                    off_mdx_verts = 0
                    mdx_data_size += 4 * 3
                    # Normal
                    mdx_data_bitmap |= MDX_FLAG_NORMAL
                    off_mdx_normals = 4 * 3
                    if self.xbox:
                        mdx_data_size += 4
                    else:
                        mdx_data_size += 4 * 3
                    # UV1
                    if node.uv1:
                        mdx_data_bitmap |= MDX_FLAG_UV1
                        off_mdx_uv1 = mdx_data_size
                        mdx_data_size += 4 * 2
                    # UV2
                    if node.uv2:
                        mdx_data_bitmap |= MDX_FLAG_UV2
                        off_mdx_uv2 = mdx_data_size
                        mdx_data_size += 4 * 2
                    # Tangent Space
                    if node.tangentspace:
                        mdx_data_bitmap |= MDX_FLAG_TANGENT1
                        off_mdx_tan_space1 = mdx_data_size
                        if self.xbox:
                            mdx_data_size += 4 * 3
                        else:
                            mdx_data_size += 4 * 9
                    # Bone Weights + Bone Indices
                    if type_flags & NODE_SKIN:
                        mdx_data_size += 4 * 4
                        if self.xbox:
                            mdx_data_size += 4 * 2
                        else:
                            mdx_data_size += 4 * 4

                if type_flags & NODE_SABER:
                    saber_vert_indices = list(range(8))
                    saber_vert_indices.extend([j for _ in range(20) for j in range(4)])
                    saber_vert_indices.extend(range(8, 16))
                    saber_vert_indices.extend([j for _ in range(20) for j in range(8, 12)])
                    num_verts = NUM_SABER_VERTS
                else:
                    num_verts = len(node.verts)

                num_faces = len(node.facelist.vertices)

                num_textures = 0
                if node.uv1:
                    num_textures += 1
                if node.uv2:
                    num_textures += 1

                has_lightmap = node.lightmapped
                rotate_texture = node.rotatetexture
                background_geometry = node.background_geometry
                shadow = node.shadow
                beaming = node.beaming
                render = node.render
                dirt_enabled = node.dirt_enabled
                dirt_texture = node.dirt_texture
                dirt_coord_space = node.dirt_worldspace
                hide_in_holograms = node.hologram_donotdraw
                total_area = self.mesh_total_areas[node_idx]
                mdx_offset = self.mdx_offsets[node_idx]
                if not self.xbox:
                    off_vert_array = self.verts_offsets[node_idx]

                self.mdl_file_handle.write_uint32(fn_ptr1)
                self.mdl_file_handle.write_uint32(fn_ptr2)
                self.put_array_def(self.faces_offsets[node_idx], num_faces)  # faces
                for val in bounding_box:
                    self.mdl_file_handle.write_float(val)
                self.mdl_file_handle.write_float(radius)
                for val in average:
                    self.mdl_file_handle.write_float(val)
                for val in diffuse:
                    self.mdl_file_handle.write_float(val)
                for val in ambient:
                    self.mdl_file_handle.write_float(val)
                self.mdl_file_handle.write_uint32(transparency_hint)
                self.mdl_file_handle.write_string(bitmap)
                self.mdl_file_handle.write_string(bitmap2)
                self.mdl_file_handle.write_string(bitmap3)
                self.mdl_file_handle.write_string(bitmap4)

                if type_flags & NODE_SABER:
                    self.put_array_def(self.index_count_offsets[node_idx], 0)  # indices count
                    self.put_array_def(self.index_offset_offsets[node_idx], 0)  # indices offset
                    self.put_array_def(self.inv_count_offsets[node_idx], 0)  # inverted counter
                else:
                    self.put_array_def(self.index_count_offsets[node_idx], 1)  # indices count
                    self.put_array_def(self.index_offset_offsets[node_idx], 1)  # indices offset
                    self.put_array_def(self.inv_count_offsets[node_idx], 1)  # inverted counter

                self.mdl_file_handle.write_uint32(0xFFFFFFFF)  # unknown
                self.mdl_file_handle.write_uint32(0xFFFFFFFF)  # unknown
                self.mdl_file_handle.write_uint32(0)  # unknown
                self.mdl_file_handle.write_uint8(3)  # saber unknown
                for _ in range(7):
                    self.mdl_file_handle.write_uint8(0)  # saber unknown
                self.mdl_file_handle.write_uint32(animate_uv)
                self.mdl_file_handle.write_float(uv_dir_x)
                self.mdl_file_handle.write_float(uv_dir_y)
                self.mdl_file_handle.write_float(uv_jitter)
                self.mdl_file_handle.write_float(uv_jitter_speed)
                self.mdl_file_handle.write_uint32(mdx_data_size)
                self.mdl_file_handle.write_uint32(mdx_data_bitmap)
                self.mdl_file_handle.write_uint32(off_mdx_verts)
                self.mdl_file_handle.write_uint32(off_mdx_normals)
                self.mdl_file_handle.write_uint32(off_mdx_colors)
                self.mdl_file_handle.write_uint32(off_mdx_uv1)
                self.mdl_file_handle.write_uint32(off_mdx_uv2)
                self.mdl_file_handle.write_uint32(off_mdx_uv3)
                self.mdl_file_handle.write_uint32(off_mdx_uv4)
                self.mdl_file_handle.write_uint32(off_mdx_tan_space1)
                self.mdl_file_handle.write_uint32(off_mdx_tan_space2)
                self.mdl_file_handle.write_uint32(off_mdx_tan_space3)
                self.mdl_file_handle.write_uint32(off_mdx_tan_space4)
                self.mdl_file_handle.write_uint16(num_verts)
                self.mdl_file_handle.write_uint16(num_textures)
                self.mdl_file_handle.write_uint8(has_lightmap)
                self.mdl_file_handle.write_uint8(rotate_texture)
                self.mdl_file_handle.write_uint8(background_geometry)
                self.mdl_file_handle.write_uint8(shadow)
                self.mdl_file_handle.write_uint8(beaming)
                self.mdl_file_handle.write_uint8(render)

                if self.tsl:
                    self.mdl_file_handle.write_uint8(dirt_enabled)
                    self.mdl_file_handle.write_uint8(0)  # padding
                    self.mdl_file_handle.write_uint16(dirt_texture)
                    self.mdl_file_handle.write_uint16(dirt_coord_space)
                    self.mdl_file_handle.write_uint8(hide_in_holograms)
                    self.mdl_file_handle.write_uint8(0)  # padding

                self.mdl_file_handle.write_uint16(0)  # padding
                self.mdl_file_handle.write_float(total_area)
                self.mdl_file_handle.write_uint32(0)  # padding
                self.mdl_file_handle.write_uint32(mdx_offset)
                if not self.xbox:
                    self.mdl_file_handle.write_uint32(off_vert_array)

            # Skin Header

            if type_flags & NODE_SKIN:
                bone_names = set()
                for vert_weights in node.weights:
                    for bone_name, _ in vert_weights:
                        bone_names.add(bone_name)
                bone_indices = []
                for bone_name in bone_names:
                    bone_indices.append(self.node_idx_by_name[bone_name])
                bonemap = [-1] * len(self.nodes)
                for bone_idx, bone_node_idx in enumerate(bone_indices):
                    bonemap[bone_node_idx] = bone_idx

                if self.xbox:
                    off_mdx_bone_indices = mdx_data_size - 2 * 4
                    off_mdx_bone_weights = off_mdx_bone_indices - 4 * 4
                else:
                    off_mdx_bone_indices = mdx_data_size - 4 * 4
                    off_mdx_bone_weights = off_mdx_bone_indices - 4 * 4
                off_bonemap = self.bonemap_offsets[node_idx]
                num_bones = len(self.nodes)

                self.put_array_def(0, 0)  # unknown
                self.mdl_file_handle.write_uint32(off_mdx_bone_weights)
                self.mdl_file_handle.write_uint32(off_mdx_bone_indices)
                self.mdl_file_handle.write_uint32(off_bonemap)
                self.mdl_file_handle.write_uint32(num_bones)
                self.put_array_def(self.qbone_offsets[node_idx], num_bones)  # QBones
                self.put_array_def(self.tbone_offsets[node_idx], num_bones)  # TBones
                self.put_array_def(self.skin_garbage_offsets[node_idx], num_bones)  # garbage
                for i in range(16):
                    if i < len(bone_indices):
                        self.mdl_file_handle.write_uint16(bone_indices[i])
                    else:
                        self.mdl_file_handle.write_uint16(0xFFFF)
                self.mdl_file_handle.write_uint32(0)  # padding

            # Dangly Header

            if type_flags & NODE_DANGLY:
                displacement = node.displacement
                tightness = node.tightness
                period = node.period
                off_vert_data = self.dangly_verts_offsets[node_idx]

                self.put_array_def(self.constraints_offsets[node_idx], len(node.constraints))
                self.mdl_file_handle.write_float(displacement)
                self.mdl_file_handle.write_float(tightness)
                self.mdl_file_handle.write_float(period)
                self.mdl_file_handle.write_uint32(off_vert_data)

            # AABB Header

            if type_flags & NODE_AABB:
                self.mdl_file_handle.write_uint32(self.aabb_offsets[node_idx][0])

            # Saber Header

            if type_flags & NODE_SABER:
                saber_inv_count1 = self.get_inverted_counter(num_meshes + 1)
                saber_inv_count2 = self.get_inverted_counter(num_meshes + 2)
                num_meshes += 2

                self.mdl_file_handle.write_uint32(self.saber_verts_offsets[node_idx])
                self.mdl_file_handle.write_uint32(self.saber_uv_offsets[node_idx])
                self.mdl_file_handle.write_uint32(self.saber_normals_offsets[node_idx])
                self.mdl_file_handle.write_uint32(saber_inv_count1)
                self.mdl_file_handle.write_uint32(saber_inv_count2)

            # Mesh Data

            if type_flags & NODE_MESH:
                # Face Adjacencies
                face_adjacencies = []
                face_adjacencies = [[-1, -1, -1] for _ in range(num_faces)]
                for face_idx, face in enumerate(node.facelist.vertices):
                    edges = [
                        tuple(sorted(edge))
                        for edge in [
                            (face[0], face[1]),
                            (face[1], face[2]),
                            (face[2], face[0]),
                        ]
                    ]
                    for other_face_idx in range(face_idx + 1, num_faces):
                        other_face = node.facelist.vertices[other_face_idx]
                        other_edges = [
                            tuple(sorted(edge))
                            for edge in [
                                (other_face[0], other_face[1]),
                                (other_face[1], other_face[2]),
                                (other_face[2], other_face[0]),
                            ]
                        ]
                        num_adj_faces = 0
                        for i in range(3):
                            if face_adjacencies[face_idx][i] != -1:
                                num_adj_faces += 1
                                continue
                            for j in range(3):
                                if edges[i] == other_edges[j]:
                                    face_adjacencies[face_idx][i] = other_face_idx
                                    face_adjacencies[other_face_idx][j] = face_idx
                                    num_adj_faces += 1
                                    break
                        if num_adj_faces == 3:
                            break

                # Faces
                for face_idx, face in enumerate(node.facelist.vertices):
                    vert1 = Vector3(node.verts[face[0]])
                    normal = Vector3(node.facelist.normals[face_idx])
                    distance = -1.0 * (normal @ vert1)
                    material_id = node.facelist.materials[face_idx]

                    for val in normal:
                        self.mdl_file_handle.write_float(val)
                    self.mdl_file_handle.write_float(distance)
                    self.mdl_file_handle.write_uint32(material_id)
                    for val in face_adjacencies[face_idx]:
                        self.mdl_file_handle.write_int16(val)
                    for val in face:
                        self.mdl_file_handle.write_uint16(val)

                # Vertex Indices Offset
                if not type_flags & NODE_SABER:
                    self.mdl_file_handle.write_uint32(self.indices_offsets[node_idx])

                # Vertices
                if not self.xbox:
                    if type_flags & NODE_SABER:
                        for vert_idx in saber_vert_indices:
                            for val in node.verts[vert_idx]:
                                self.mdl_file_handle.write_float(val)
                    else:
                        for vert in node.verts:
                            for val in vert:
                                self.mdl_file_handle.write_float(val)

                # Vertex Indices Count, Inverted Mesh Counter, Vertex Indices
                if not type_flags & NODE_SABER:
                    num_meshes += 1
                    mesh_inv_count = self.get_inverted_counter(num_meshes)

                    self.mdl_file_handle.write_uint32(3 * len(node.facelist.vertices))  # vertex index count
                    self.mdl_file_handle.write_uint32(mesh_inv_count)  # inverted mesh counter

                    # Vertex Indices
                    for face in node.facelist.vertices:
                        for val in face:
                            self.mdl_file_handle.write_uint16(val)

                # MDX data
                if not type_flags & NODE_SABER:
                    for vert_idx, vert in enumerate(node.verts):
                        for val in vert:
                            self.mdx_file_handle.write_float(val)
                        if self.xbox:
                            comp = self.compress_vector_xbox(node.normals[vert_idx])
                            self.mdx_file_handle.write_uint32(comp)
                        else:
                            for val in node.normals[vert_idx]:
                                self.mdx_file_handle.write_float(val)
                        if node.uv1:
                            for val in node.uv1[vert_idx]:
                                self.mdx_file_handle.write_float(val)
                        if node.uv2:
                            for val in node.uv2[vert_idx]:
                                self.mdx_file_handle.write_float(val)
                        if node.tangentspace:
                            if self.xbox:
                                comp = self.compress_vector_xbox(node.bitangents[vert_idx])
                                self.mdx_file_handle.write_uint32(comp)
                                comp = self.compress_vector_xbox(node.tangents[vert_idx])
                                self.mdx_file_handle.write_uint32(comp)
                                comp = self.compress_vector_xbox(node.tangentspacenormals[vert_idx])
                                self.mdx_file_handle.write_uint32(comp)
                            else:
                                for val in node.bitangents[vert_idx]:
                                    self.mdx_file_handle.write_float(val)
                                for val in node.tangents[vert_idx]:
                                    self.mdx_file_handle.write_float(val)
                                for val in node.tangentspacenormals[vert_idx]:
                                    self.mdx_file_handle.write_float(val)
                        if type_flags & NODE_SKIN:
                            vert_weights = node.weights[vert_idx]
                            bone_weights = []
                            for bone_name, weight in vert_weights:
                                bone_node_idx = self.node_idx_by_name[bone_name]
                                bone_idx = bonemap[bone_node_idx]
                                bone_weights.append((bone_idx, weight))
                            for i in range(4):
                                if i < len(bone_weights):
                                    self.mdx_file_handle.write_float(bone_weights[i][1])
                                else:
                                    self.mdx_file_handle.write_float(0.0)
                            if self.xbox:
                                for i in range(4):
                                    if i < len(bone_weights):
                                        self.mdx_file_handle.write_uint16(bone_weights[i][0])
                                    else:
                                        self.mdx_file_handle.write_uint16(0xFFFF)
                            else:
                                for i in range(4):
                                    if i < len(bone_weights):
                                        self.mdx_file_handle.write_float(float(bone_weights[i][0]))
                                    else:
                                        self.mdx_file_handle.write_float(-1.0)
                    # Extra MDX data
                    for _ in range(3):
                        self.mdx_file_handle.write_float(1e7)
                    if self.xbox:
                        self.mdx_file_handle.write_uint32(0)
                    else:
                        for _ in range(3):
                            self.mdx_file_handle.write_float(0.0)
                    if node.uv1:
                        for _ in range(2):
                            self.mdx_file_handle.write_float(0.0)
                    if node.uv2:
                        for _ in range(2):
                            self.mdx_file_handle.write_float(0.0)
                    if node.tangentspace:
                        if self.xbox:
                            for _ in range(3):
                                self.mdx_file_handle.write_uint32(0)
                        else:
                            for _ in range(9):
                                self.mdx_file_handle.write_float(0.0)
                    if type_flags & NODE_SKIN:
                        weights = (1.0, 0.0, 0.0, 0.0)
                        for val in weights:
                            self.mdx_file_handle.write_float(val)
                        if self.xbox:
                            for _ in range(4):
                                self.mdx_file_handle.write_uint16(0)
                        else:
                            for _ in range(4):
                                self.mdx_file_handle.write_float(0.0)

            # Skin Data

            if type_flags & NODE_SKIN:
                # Bonemap
                for bone_idx in bonemap:
                    if self.xbox:
                        self.mdl_file_handle.write_uint16(bone_idx if bone_idx != -1 else 0xFFFF)
                    else:
                        self.mdl_file_handle.write_float(float(bone_idx))

                num_bones = len(bonemap)

                # QBones, TBones
                qbones = [None] * num_bones
                tbones = [None] * num_bones
                for i in range(num_bones):
                    bone_trans = self.nodes[i].from_root.inverted() @ node.from_root
                    tbones[i], qbones[i], _ = bone_trans.decompose()
                for i in range(num_bones):
                    qbone = qbones[i]
                    self.mdl_file_handle.write_float(qbone.w)
                    self.mdl_file_handle.write_float(qbone.x)
                    self.mdl_file_handle.write_float(qbone.y)
                    self.mdl_file_handle.write_float(qbone.z)
                for i in range(num_bones):
                    tbone = tbones[i]
                    self.mdl_file_handle.write_float(tbone.x)
                    self.mdl_file_handle.write_float(tbone.y)
                    self.mdl_file_handle.write_float(tbone.z)

                # Garbage
                for _ in range(num_bones):
                    self.mdl_file_handle.write_uint32(0)

            # Dangly Data

            if type_flags & NODE_DANGLY:
                for val in node.constraints:
                    self.mdl_file_handle.write_float(val)
                for vert in node.verts:
                    for val in vert:
                        self.mdl_file_handle.write_float(val)

            # AABB Data

            if type_flags & NODE_AABB:
                for aabb in self.aabbs[node_idx]:
                    child_idx1 = aabb[6]
                    child_idx2 = aabb[7]
                    face_idx = aabb[8]
                    split_axis = aabb[9]

                    if face_idx == -1:
                        off_child1 = self.aabb_offsets[node_idx][child_idx1]
                        off_child2 = self.aabb_offsets[node_idx][child_idx2]
                    else:
                        off_child1 = 0
                        off_child2 = 0

                    switch = {
                        -3: AABB_NEGATIVE_Z,
                        -2: AABB_NEGATIVE_Y,
                        -1: AABB_NEGATIVE_X,
                        0: AABB_NO_CHILDREN,
                        1: AABB_POSITIVE_X,
                        2: AABB_POSITIVE_Y,
                        3: AABB_POSITIVE_Z,
                    }
                    most_significant_plane = switch[split_axis]

                    # Bounding Box
                    for val in aabb[:6]:
                        self.mdl_file_handle.write_float(val)

                    self.mdl_file_handle.write_uint32(off_child1)
                    self.mdl_file_handle.write_uint32(off_child2)
                    self.mdl_file_handle.write_int32(face_idx)
                    self.mdl_file_handle.write_uint32(most_significant_plane)

            # Saber Data

            if type_flags & NODE_SABER:
                for vert_idx in saber_vert_indices:
                    for val in node.verts[vert_idx]:
                        self.mdl_file_handle.write_float(val)
                for vert_idx in saber_vert_indices:
                    for val in node.uv1[vert_idx]:
                        self.mdl_file_handle.write_float(val)
                for vert_idx in saber_vert_indices:
                    for val in node.normals[vert_idx]:
                        self.mdl_file_handle.write_float(val)

            # Children

            for child_idx in child_indices:
                self.mdl_file_handle.write_uint32(self.node_offsets[child_idx])

            # Controllers

            for key in self.controller_keys[node_idx]:
                unk1 = 0xFFFF

                self.mdl_file_handle.write_uint32(key.ctrl_type)
                self.mdl_file_handle.write_uint16(unk1)
                self.mdl_file_handle.write_uint16(key.num_rows)
                self.mdl_file_handle.write_uint16(key.timekeys_start)
                self.mdl_file_handle.write_uint16(key.values_start)
                self.mdl_file_handle.write_uint8(key.num_columns)

                for _ in range(3):
                    self.mdl_file_handle.write_uint8(0)  # padding

            # Controller Data

            for val in self.controller_data[node_idx]:
                self.mdl_file_handle.write_float(val)

    def get_node_flags(self, node: MDLNode) -> int:
        switch = {
            NodeType.DUMMY: NODE_BASE,
            NodeType.REFERENCE: NODE_BASE | NODE_REFERENCE,
            NodeType.TRIMESH: NODE_BASE | NODE_MESH,
            NodeType.DANGLYMESH: NODE_BASE | NODE_MESH | NODE_DANGLY,
            NodeType.SKIN: NODE_BASE | NODE_MESH | NODE_SKIN,
            NodeType.EMITTER: NODE_BASE | NODE_EMITTER,
            NodeType.LIGHT: NODE_BASE | NODE_LIGHT,
            NodeType.AABB: NODE_BASE | NODE_MESH | NODE_AABB,
            NodeType.LIGHTSABER: NODE_BASE | NODE_MESH | NODE_SABER,
        }
        return switch[node.nodetype]

    def get_mesh_fn_ptr(self, type_flags: int) -> tuple[int, int]:
        if type_flags & NODE_SKIN:
            if self.tsl:
                if self.xbox:
                    fn_ptr1 = SKIN_FN_PTR_1_K2_XBOX
                    fn_ptr2 = SKIN_FN_PTR_2_K2_XBOX
                else:
                    fn_ptr1 = SKIN_FN_PTR_1_K2_PC
                    fn_ptr2 = SKIN_FN_PTR_2_K2_PC
            elif self.xbox:
                fn_ptr1 = SKIN_FN_PTR_1_K1_XBOX
                fn_ptr2 = SKIN_FN_PTR_2_K1_XBOX
            else:
                fn_ptr1 = SKIN_FN_PTR_1_K1_PC
                fn_ptr2 = SKIN_FN_PTR_2_K1_PC

        elif type_flags & NODE_DANGLY:
            if self.tsl:
                if self.xbox:
                    fn_ptr1 = DANGLY_FN_PTR_1_K2_XBOX
                    fn_ptr2 = DANGLY_FN_PTR_2_K2_XBOX
                else:
                    fn_ptr1 = DANGLY_FN_PTR_1_K2_PC
                    fn_ptr2 = DANGLY_FN_PTR_2_K2_PC
            elif self.xbox:
                fn_ptr1 = DANGLY_FN_PTR_1_K1_XBOX
                fn_ptr2 = DANGLY_FN_PTR_2_K1_XBOX
            else:
                fn_ptr1 = DANGLY_FN_PTR_1_K1_PC
                fn_ptr2 = DANGLY_FN_PTR_2_K1_PC

        elif self.tsl:
            if self.xbox:
                fn_ptr1 = MESH_FN_PTR_1_K2_XBOX
                fn_ptr2 = MESH_FN_PTR_2_K2_XBOX
            else:
                fn_ptr1 = MESH_FN_PTR_1_K2_PC
                fn_ptr2 = MESH_FN_PTR_2_K2_PC
        elif self.xbox:
            fn_ptr1 = MESH_FN_PTR_1_K1_XBOX
            fn_ptr2 = MESH_FN_PTR_2_K1_XBOX
        else:
            fn_ptr1 = MESH_FN_PTR_1_K1_PC
            fn_ptr2 = MESH_FN_PTR_2_K1_PC

        return (fn_ptr1, fn_ptr2)

    def calculate_face_area(self, edge1, edge2, edge3):
        a = edge1.length
        b = edge2.length
        c = edge3.length
        s = (a + b + c) / 2.0
        if a <= 0.0 or b <= 0.0 or c <= 0.0:
            return -1.0
        if a > b + c or b > a + c or c > a + b:
            return -1.0
        area2 = s * (s - a) * (s - b) * (s - c)
        return math.sqrt(area2)

    def generate_aabb_tree(self, node: MDLNode) -> list[tuple[int, list[Vector3], Vector3]]:
        face_list: list[tuple[int, list[Vector3], Vector3]] = []
        face_idx: int = 0

        for face_idx, face in enumerate(node.facelist.vertices):
            v0 = Vector3(node.verts[face[0]])
            v1 = Vector3(node.verts[face[1]])
            v2 = Vector3(node.verts[face[2]])
            centroid = (v0 + v1 + v2) / 3
            face_list.append((face_idx, [v0, v1, v2], centroid))

        aabbs: list[tuple[int, list[Vector3], Vector3]] = []
        generate_tree(aabbs, face_list)

        return aabbs

    def get_inverted_counter(self, count: int) -> int:
        quo = count // 100
        mod = count % 100
        return int(pow(2, quo) * 100 - count + (100 * quo if mod else 0) + (0 if quo else -1))

    def put_array_def(self, offset: int, count: int):
        self.mdl_file_handle.write_uint32(offset)
        self.mdl_file_handle.write_uint32(count)
        self.mdl_file_handle.write_uint32(count)

    def compress_vector_xbox(self, vec: Vector3) -> int:
        x, y, z = vec
        if abs(x) > 1.0 or abs(y) > 1.0 or abs(z) > 1.0:
            return 0

        tmp = round(511.0 * z)
        if z < 0.0:
            tmp = 1023 + tmp
        comp = tmp

        tmp = round(1023.0 * y)
        if y < 0.0:
            tmp = 2047 + tmp
        comp = (comp << 11) | tmp

        tmp = round(1023.0 * x)
        if x < 0.0:
            tmp = 2047 + tmp
        comp = (comp << 11) | tmp

        return comp
