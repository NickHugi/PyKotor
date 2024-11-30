from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TextIO

from pykotor.resource.formats.mdl.mdl_types import (
    MDLControllerType,
    MDLDangly,
    MDLSkin,
)

if TYPE_CHECKING:
    from pykotor.resource.formats.mdl.mdl_types import (
        MDLController,
        MDLData,
        MDLEmitter,
        MDLLight,
        MDLMesh,
        MDLNode,
        MDLReference,
        MDLSaber,
        MDLWalkmesh,
    )


@dataclass
class MDLAsciiWriter:
    """Writer for ASCII MDL files."""

    _writer: TextIO

    def write_line(self, indent: int, line: str) -> None:
        """Write a line with indentation."""
        self._writer.write("  " * indent + line + "\n")

    def write_mdl(self, mdl: MDLData) -> None:
        """Write MDL data to ASCII format."""
        self.write_line(0, "# ASCII MDL")
        self.write_line(0, "filedependancy unknown.tga")
        self.write_line(0, f"newmodel {mdl.name}")
        self.write_line(0, "")
        self.write_line(0, "setsupermodel " + mdl.name + " " + mdl.supermodel)
        self.write_line(0, f"classification {mdl.classification.name}")
        self.write_line(0, "")
        self.write_line(0, "setanimationscale 1.0")
        self.write_line(0, "")
        self.write_line(0, "beginmodelgeom " + mdl.name)
        self.write_line(0, "")
        self._write_node(1, mdl.root)
        self.write_line(0, "")
        self.write_line(0, "donemodel " + mdl.name)

    def _write_node(self, indent: int, node: MDLNode) -> None:
        """Write a node and its children."""
        self.write_line(indent, f"node {node.node_type.name.lower()} {node.name}")
        self.write_line(indent, "{")
        self._write_node_data(indent + 1, node)
        self.write_line(indent, "}")

        for child in node.children:
            self._write_node(indent, child)

    def _write_node_data(self, indent: int, node: MDLNode) -> None:
        """Write node data including position, orientation, and controllers."""
        self.write_line(indent, f"parent {node.parent_id}")
        self.write_line(indent, f"position {node.position.x} {node.position.y} {node.position.z}")
        self.write_line(indent, f"orientation {node.orientation.x} {node.orientation.y} {node.orientation.z} {node.orientation.w}")

        if node.mesh:
            self._write_mesh(indent, node.mesh)
        if node.light:
            self._write_light(indent, node.light)
        if node.emitter:
            self._write_emitter(indent, node.emitter)
        if node.reference:
            self._write_reference(indent, node.reference)
        if node.saber:
            self._write_saber(indent, node.saber)
        if node.aabb:
            self._write_walkmesh(indent, node.aabb)

        for controller in node.controllers:
            self._write_controller(indent, controller)

    def _write_mesh(self, indent: int, mesh: MDLMesh) -> None:
        """Write mesh data."""
        self.write_line(indent, f"ambient {mesh.ambient.r} {mesh.ambient.g} {mesh.ambient.b}")
        self.write_line(indent, f"diffuse {mesh.diffuse.r} {mesh.diffuse.g} {mesh.diffuse.b}")
        self.write_line(indent, f"transparencyhint {mesh.transparency_hint}")
        self.write_line(indent, f"bitmap {mesh.texture_1}")
        if mesh.texture_2:
            self.write_line(indent, f"lightmap {mesh.texture_2}")

        if isinstance(mesh, MDLSkin):
            self._write_skin(indent, mesh)
        elif isinstance(mesh, MDLDangly):
            self._write_dangly(indent, mesh)

        self.write_line(indent, "verts " + str(len(mesh.vertex_positions)))
        for i, pos in enumerate(mesh.vertex_positions):
            line = f"{i} {pos.x} {pos.y} {pos.z}"
            if mesh.vertex_normals:
                normal = mesh.vertex_normals[i]
                line += f" {normal.x} {normal.y} {normal.z}"
            if mesh.vertex_uv1:
                uv = mesh.vertex_uv1[i]
                line += f" {uv.x} {uv.y}"
            if mesh.vertex_uv2:
                uv = mesh.vertex_uv2[i]
                line += f" {uv.x} {uv.y}"
            self.write_line(indent + 1, line)

        self.write_line(indent, "faces " + str(len(mesh.faces)))
        for i, face in enumerate(mesh.faces):
            self.write_line(indent + 1, f"{i} {face.v1} {face.v2} {face.v3} {face.material.value} {face.smoothing_group}")

    def _write_skin(self, indent: int, skin: MDLSkin) -> None:
        """Write skin-specific data."""
        self.write_line(indent, "bones " + str(len(skin.bone_indices)))
        for i, bone_idx in enumerate(skin.bone_indices):
            qbone = skin.qbones[i]
            tbone = skin.tbones[i]
            self.write_line(indent + 1, f"{i} {bone_idx} {qbone.x} {qbone.y} {qbone.z} {qbone.w} {tbone.x} {tbone.y} {tbone.z}")

    def _write_dangly(self, indent: int, dangly: MDLDangly) -> None:
        """Write dangly mesh data."""
        self.write_line(indent, "constraints " + str(len(dangly.constraints)))
        for i, constraint in enumerate(dangly.constraints):
            self.write_line(indent + 1, f"{i} {constraint.type} {constraint.target} {constraint.target_node}")

    def _write_light(self, indent: int, light: MDLLight) -> None:
        """Write light data."""
        self.write_line(indent, f"flareradius {light.flare_radius}")
        self.write_line(indent, f"priority {light.light_priority}")
        if light.ambient_only:
            self.write_line(indent, "ambientonly")
        if light.shadow:
            self.write_line(indent, "shadow")
        if light.flare:
            self.write_line(indent, "flare")
        if light.fading_light:
            self.write_line(indent, "fadinglight")

    def _write_emitter(self, indent: int, emitter: MDLEmitter) -> None:
        """Write emitter data."""
        self.write_line(indent, f"deadspace {emitter.dead_space}")
        self.write_line(indent, f"blastradius {emitter.blast_radius}")
        self.write_line(indent, f"blastlength {emitter.blast_length}")
        self.write_line(indent, f"branchcount {emitter.branch_count}")
        self.write_line(indent, f"controlpointsmoothing {emitter.control_point_smoothing}")
        self.write_line(indent, f"xgrid {emitter.x_grid}")
        self.write_line(indent, f"ygrid {emitter.y_grid}")
        self.write_line(indent, f"render {emitter.render_type.name}")
        self.write_line(indent, f"update {emitter.update_type.name}")
        self.write_line(indent, f"blend {emitter.blend_type.name}")
        self.write_line(indent, f"texture {emitter.texture}")
        self.write_line(indent, f"chunkname {emitter.chunk_name}")
        if emitter.twosided:
            self.write_line(indent, "twosided")
        if emitter.loop:
            self.write_line(indent, "loop")
        self.write_line(indent, f"renderorder {emitter.render_order}")
        if emitter.frame_blend:
            self.write_line(indent, "frameblend")
        self.write_line(indent, f"depth {emitter.depth_texture}")

    def _write_reference(self, indent: int, reference: MDLReference) -> None:
        """Write reference data."""
        self.write_line(indent, f"refmodel {reference.model}")
        if reference.reattachable:
            self.write_line(indent, "reattachable")

    def _write_saber(self, indent: int, saber: MDLSaber) -> None:
        """Write saber data."""
        self.write_line(indent, f"sabertype {saber.saber_type}")
        self.write_line(indent, f"sabercolor {saber.saber_color}")
        self.write_line(indent, f"saberlength {saber.saber_length}")
        self.write_line(indent, f"saberwidth {saber.saber_width}")
        self.write_line(indent, f"saberflarecolor {saber.saber_flare_color}")
        self.write_line(indent, f"saberflareradius {saber.saber_flare_radius}")

    def _write_walkmesh(self, indent: int, walkmesh: MDLWalkmesh) -> None:
        """Write walkmesh data."""
        self.write_line(indent, "aabb " + str(len(walkmesh.aabbs)))
        for i, aabb in enumerate(walkmesh.aabbs):
            self.write_line(indent + 1, f"{i} {aabb.position.x} {aabb.position.y} {aabb.position.z}")

    def _write_controller(self, indent: int, controller: MDLController) -> None:
        """Write controller data."""
        if not controller.rows:
            return

        if controller.controller_type == MDLControllerType.POSITION:
            self.write_line(indent, "positionkey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]} {row.data[1]} {row.data[2]}")

        elif controller.controller_type == MDLControllerType.ORIENTATION:
            self.write_line(indent, "orientationkey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]} {row.data[1]} {row.data[2]} {row.data[3]}")

        elif controller.controller_type == MDLControllerType.SCALE:
            self.write_line(indent, "scalekey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]} {row.data[1]} {row.data[2]}")

        elif controller.controller_type == MDLControllerType.COLOR:
            self.write_line(indent, "colorkey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]} {row.data[1]} {row.data[2]}")

        elif controller.controller_type == MDLControllerType.RADIUS:
            self.write_line(indent, "radiuskey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.SHADOWRADIUS:
            self.write_line(indent, "shadowradiuskey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.VERTICALDISPLACEMENT:
            self.write_line(indent, "verticaldisplacementkey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.MULTIPLIER:
            self.write_line(indent, "multiplierkey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.ALPHAEND:
            self.write_line(indent, "alphaendkey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.ALPHASTART:
            self.write_line(indent, "alphastartkey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.BIRTHRATE:
            self.write_line(indent, "birthratekey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.BOUNCECO:
            self.write_line(indent, "bouncecokey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.COMBINEETIME:
            self.write_line(indent, "combineetimekey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.DRAG:
            self.write_line(indent, "dragkey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.FOCUSZONETX:
            self.write_line(indent, "focuszonetxkey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.FOCUSZONETY:
            self.write_line(indent, "focuszonetykey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.FRAME:
            self.write_line(indent, "framekey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.GRAV:
            self.write_line(indent, "gravkey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.LIFEEXP:
            self.write_line(indent, "lifeexpkey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.MASS:
            self.write_line(indent, "masskey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.P2P_BEZIER2:
            self.write_line(indent, "p2p_bezier2key")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.P2P_BEZIER3:
            self.write_line(indent, "p2p_bezier3key")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.PARTICLEROTX:
            self.write_line(indent, "particlerotxkey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.PARTICLEROTY:
            self.write_line(indent, "particlerotykey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.PARTICLEROTZ:
            self.write_line(indent, "particlerotzkey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.RANDVELX:
            self.write_line(indent, "randvelxkey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.RANDVELY:
            self.write_line(indent, "randvelykey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.RANDVELZ:
            self.write_line(indent, "randvelzkey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.SIZESTART:
            self.write_line(indent, "sizestartkey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.SIZEEND:
            self.write_line(indent, "sizeendkey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.SIZESTART_Y:
            self.write_line(indent, "sizestart_ykey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.SIZEEND_Y:
            self.write_line(indent, "sizeend_ykey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.SPREAD:
            self.write_line(indent, "spreadkey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.THRESHOLD:
            self.write_line(indent, "thresholdkey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.VELOCITY:
            self.write_line(indent, "velocitykey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.XSIZE:
            self.write_line(indent, "xsizekey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.YSIZE:
            self.write_line(indent, "ysizekey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.BLUR:
            self.write_line(indent, "blurkey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.LIGHTNINGDELAY:
            self.write_line(indent, "lightningdelaykey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.LIGHTNINGRADIUS:
            self.write_line(indent, "lightningradiuskey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.LIGHTNINGSCALE:
            self.write_line(indent, "lightningscalekey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.DETONATE:
            self.write_line(indent, "detonatekey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.ALPHAMID:
            self.write_line(indent, "alphamidkey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.SIZEMID:
            self.write_line(indent, "sizemidkey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.SIZEMID_Y:
            self.write_line(indent, "sizemid_ykey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.BOUNCE_CO:
            self.write_line(indent, "bounce_cokey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.RANDOMVELX:
            self.write_line(indent, "randomvelxkey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.RANDOMVELY:
            self.write_line(indent, "randomvelykey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.RANDOMVELZ:
            self.write_line(indent, "randomvelzkey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.TILING:
            self.write_line(indent, "tilingkey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.ILLUM:
            self.write_line(indent, "illumkey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

        elif controller.controller_type == MDLControllerType.ILLUM_COLOR:
            self.write_line(indent, "selfillumcolorkey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]} {row.data[1]} {row.data[2]}")

        elif controller.controller_type == MDLControllerType.ALPHA:
            self.write_line(indent, "alphakey")
            for row in controller.rows:
                self.write_line(indent + 1, f"{row.time} {row.data[0]}")

@dataclass
class MDLAsciiReader:
    """Reader for ASCII MDL files."""

    _reader: TextIO

    def read_mdl(self) -> MDLData:
        """Read MDL data from ASCII format."""
        # TODO: Implement ASCII MDL reader
        raise NotImplementedError("ASCII MDL reader not implemented yet")
