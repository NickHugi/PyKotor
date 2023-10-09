from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.geometry import AxisAngle, Vector4
from pykotor.common.stream import BinaryReader, BinaryWriter
from pykotor.resource.formats.mdl import MDL
from pykotor.resource.formats.mdl.mdl_data import (
    MDLController,
    MDLControllerType,
    MDLNode,
)

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class MDLAsciiReader:
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        self._mdl: MDL | None = None
        self._reader = BinaryReader.from_auto(source, offset)

    def load(
        self,
        auto_close: bool = True,
    ) -> MDL:
        self._mdl = MDL()

        if auto_close:
            self._reader.close()

        return self._mdl


class MDLAsciiWriter:
    def __init__(
        self,
        mdl: MDL,
        target: TARGET_TYPES,
    ):
        self._mdl = mdl
        self._writer = BinaryWriter.to_auto(target)

    def write(
        self,
        auto_close: bool = True,
    ) -> None:
        self._writer.write_line(0, f"newmodel {self._mdl.name}")
        self._writer.write_line(
            0,
            f"setsupermodel {self._mdl.name} {self._mdl.supermodel}",
        )
        self._writer.write_line(0, f"ignorefog {int(not self._mdl.fog)}")

        self._writer.write_line(0, f"beginmodelgeom {self._mdl.name}")
        self._writer.write_line(1, "bmin 0 0 0")
        self._writer.write_line(1, "bmax 0 0 0")
        self._writer.write_line(1, "radius 0")

        all_nodes = self._mdl.all_nodes()
        for node in all_nodes:
            self._write_node(node, anim=False, indent=0)
        self._writer.write_line(0, f"endmodelgeom {self._mdl.name}")

        for anim in self._mdl.anims:
            self._writer.write_line(0, f"newanim {anim.name} {anim.root_model}")

            self._writer.write_line(1, f"length {anim.anim_length}")
            self._writer.write_line(1, f"transtime {anim.transition_length}")
            self._writer.write_line(1, f"animroot {anim.root_model}")  # ???

            for node in anim.all_nodes():
                self._write_node(node, anim=True, indent=1)

            self._writer.write_line(0, f"doneanim {anim.name} {anim.root_model}")

        if auto_close:
            self._writer.close()

    def _write_node(
        self,
        node: MDLNode,
        anim: bool,
        indent: int,
    ):
        parent = self._mdl.find_parent(node)

        newline = self._writer.write_line

        newline(indent + 0, f"node {self._node_type(node)} {node.name}")
        newline(indent + 1, f'parent {"NULL" if parent is None else parent.name}')

        if parent is not None or not anim:
            newline(
                indent + 1,
                f"orientation {node.orientation.x} {node.orientation.y} {node.orientation.z} {node.orientation.w}",
            )
            newline(
                indent + 1,
                f"position {node.position.x} {node.position.y} {node.position.z}",
            )
            self._write_controllers(node, node.controllers, indent + 1)

            if node.mesh:
                newline(
                    indent + 1,
                    f"diffuse {node.mesh.diffuse.r} {node.mesh.diffuse.g} {node.mesh.diffuse.b}",
                )
                newline(
                    indent + 1,
                    f"ambient {node.mesh.ambient.r} {node.mesh.ambient.g} {node.mesh.ambient.b}",
                )
                newline(indent + 1, f"bitmap {node.mesh.texture_1}")
                newline(indent + 1, f"transparencyhint {node.mesh.transparency_hint}")
                newline(indent + 1, f"animateuv {int(node.mesh.animate_uv)}")
                newline(indent + 1, f"uvdirectionx {int(node.mesh.uv_direction_x)}")
                newline(indent + 1, f"uvjitter {int(node.mesh.uv_jitter)}")
                newline(indent + 1, f"uvjitterspeed {int(node.mesh.uv_jitter_speed)}")
                newline(indent + 1, f"lightmapped {int(node.mesh.has_lightmap)}")
                newline(indent + 1, f"rotatetexture {int(node.mesh.rotate_texture)}")
                newline(
                    indent + 1,
                    f"m_bIsBackgroundGeometry {int(node.mesh.background_geometry)}",
                )
                newline(indent + 1, f"shadow {int(node.mesh.shadow)}")
                newline(indent + 1, f"beaming {int(node.mesh.beaming)}")
                newline(indent + 1, f"render {int(node.mesh.render)}")
                newline(indent + 1, f"dirt_enabled {int(node.mesh.dirt_enabled)}")
                newline(indent + 1, f"dirt_texture {int(node.mesh.dirt_texture)}")
                newline(
                    indent + 1,
                    f"hologram_donotdraw {int(node.mesh.hide_in_hologram)}",
                )

                newline(indent + 1, f"verts {len(node.mesh.vertex_positions)}")
                for vertex in node.mesh.vertex_positions:
                    newline(indent + 2, f"{vertex.x} {vertex.y} {vertex.z}")

                if node.mesh.vertex_uv1:
                    newline(indent + 1, f"tverts {len(node.mesh.vertex_positions)}")
                    for vertex in node.mesh.vertex_uv1:
                        newline(indent + 2, f"{vertex.x} {vertex.y}")

                newline(indent + 1, f"faces {len(node.mesh.faces)}")
                for face in node.mesh.faces:
                    # 4th value -> smoothing group
                    newline(
                        indent + 2,
                        f"{face.v1} {face.v2} {face.v3}  0  {face.v1} {face.v2} {face.v3}  {face.material.value}",
                    )

                if node.skin:
                    newline(indent + 1, f"weights {len(node.skin.vertex_bones)}")
                    for bone in node.skin.vertex_bones:
                        line = ""
                        if bone.vertex_indices[0] != -1.0:
                            bone_id = int(bone.vertex_indices[0])
                            node_id = int(node.skin.bone_indices[bone_id])
                            name = self._mdl.get_by_node_id(node_id).name
                            line += f"{name} {bone.vertex_weights[0]} "
                        if bone.vertex_indices[1] != -1.0:
                            bone_id = int(bone.vertex_indices[1])
                            node_id = node.skin.bone_indices[bone_id]
                            name = self._mdl.get_by_node_id(node_id).name
                            line += f"{name} {bone.vertex_weights[1]} "
                        if bone.vertex_indices[2] != -1.0:
                            bone_id = int(bone.vertex_indices[2])
                            node_id = node.skin.bone_indices[bone_id]
                            name = self._mdl.get_by_node_id(node_id).name
                            line += f"{name} {bone.vertex_weights[2]} "
                        if bone.vertex_indices[3] != -1.0:
                            bone_id = int(bone.vertex_indices[3])
                            node_id = node.skin.bone_indices[bone_id]
                            name = self._mdl.get_by_node_id(node_id).name
                            line += f"{name} {bone.vertex_weights[3]} "
                        newline(indent + 2, line)

        if anim:
            self._write_anim_controllers(node, node.controllers, indent + 1)

        newline(indent + 0, "endnode")

    def _write_controllers(
        self,
        node: MDLNode,
        controllers: list[MDLController],
        indent: int,
    ):
        for controller in controllers:
            if controller.controller_type == MDLControllerType.ILLUM_COLOR:
                red, green, blue = (
                    controller.rows[0].data[0],
                    controller.rows[0].data[1],
                    controller.rows[0].data[2],
                )
                self._writer.write_line(indent, f"selfillumcolor {red} {green} {blue}")

            if controller.controller_type == MDLControllerType.ALPHA:
                self._writer.write_line(indent, f"alpha {controller.rows[0].data[0]}")

            if controller.controller_type == MDLControllerType.SCALE:
                self._writer.write_line(indent, f"scale {controller.rows[0].data[0]}")

    def _write_anim_controllers(
        self,
        node: MDLNode,
        controllers: list[MDLController],
        indent: int,
    ):
        for controller in controllers:
            if controller.controller_type == MDLControllerType.POSITION:
                self._writer.write_line(indent, "positionkey")

                # Ascii position controller values are offset by the nodes global position contrary to binary
                for row in controller.rows:
                    global_position = self._mdl.global_position(node)
                    row.data[0] += global_position.x
                    row.data[1] += global_position.y
                    row.data[2] += global_position.y

            if controller.controller_type == MDLControllerType.ORIENTATION:
                self._writer.write_line(indent, "orientationkey")

                # Ascii rotation controller values are axis-aligned as opposed to binary which are quaternions
                for row in controller.rows:
                    aa = AxisAngle.from_quaternion(
                        Vector4(row.data[0], row.data[1], row.data[2], row.data[3]),
                    )
                    row.data[0] = aa.axis.x
                    row.data[1] = aa.axis.y
                    row.data[2] = aa.axis.z
                    row.data[3] = aa.angle

            for row in controller.rows:
                self._writer.write_line(indent + 1, f"{row}")

    def _node_type(
        self,
        node: MDLNode,
    ) -> str:
        if node.skin:
            return "skin"
        if node.dangly:
            return "dangly"
        if node.saber:
            return "saber"
        if node.aabb:
            return "aabb"
        if node.emitter:
            return "emitter"
        if node.light:
            return "light"
        if node.reference:
            return "reference"
        if node.mesh:
            return "trimesh"
        return "dummy"
