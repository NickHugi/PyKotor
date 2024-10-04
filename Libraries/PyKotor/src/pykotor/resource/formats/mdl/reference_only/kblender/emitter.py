from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import bpy

from bpy_extras.io_utils import unpack_list
from typing_extensions import Literal

from pykotor.resource.formats.mdl.reference_only.base import BaseNode
from pykotor.resource.formats.mdl.reference_only.constants import NULL, MeshType, NodeType

if TYPE_CHECKING:
    from typing_extensions import Literal

    from pykotor.resource.formats.mdl.reference_only.constants import ImportOptions


class EmitterNode(BaseNode):
    nodetype: ClassVar[NodeType | Literal["EMITTER"]] = NodeType.EMITTER
    meshtype: ClassVar[MeshType | Literal["EMITTER"]] = MeshType.EMITTER

    EMITTER_ATTRS: ClassVar[list[str]] = [
        "deadspace",
        "blastradius",
        "blastlength",
        "num_branches",
        "controlptsmoothing",
        "xgrid",
        "ygrid",
        "spawntype",
        "update",
        "emitter_render",
        "blend",
        "texture",
        "chunk_name",
        "twosidedtex",
        "loop",
        "renderorder",
        "frame_blending",
        "depth_texture_name",
        "p2p",
        "p2p_sel",
        "affected_by_wind",
        "tinted",
        "bounce",
        "random",
        "inherit",
        "inheritvel",
        "inherit_local",
        "splat",
        "inherit_part",
        "depth_texture",
        "alphastart",
        "alphamid",
        "alphaend",
        "birthrate",
        "randombirthrate",
        "bounce_co",
        "combinetime",
        "drag",
        "fps",
        "frameend",
        "framestart",
        "grav",
        "lifeexp",
        "mass",
        "p2p_bezier2",
        "p2p_bezier3",
        "particlerot",
        "randvel",
        "sizestart",
        "sizemid",
        "sizeend",
        "sizestart_y",
        "sizemid_y",
        "sizeend_y",
        "spread",
        "threshold",
        "velocity",
        "xsize",
        "ysize",
        "blurlength",
        "lightningdelay",
        "lightningradius",
        "lightningsubdiv",
        "lightningscale",
        "lightningzigzag",
        "percentstart",
        "percentmid",
        "percentend",
        "targetsize",
        "numcontrolpts",
        "controlptradius",
        "controlptdelay",
        "tangentspread",
        "tangentlength",
        "colorstart",
        "colormid",
        "colorend",
    ]

    def __init__(self, name: str = "UNNAMED"):
        super().__init__(name)
        # object data
        self.deadspace: float = 0.0
        self.blastradius: float = 0.0
        self.blastlength: float = 0.0
        self.num_branches: int = 0
        self.controlptsmoothing: float = 0
        self.xgrid: float = 0
        self.ygrid: float = 0
        self.spawntype: int = 0
        self.update: str = ""
        self.emitter_render: str = ""
        self.blend: str = ""
        self.texture: str = ""
        self.chunk_name: str = ""
        self.twosidedtex: bool = False
        self.loop: bool = False
        self.renderorder: int = 0
        self.frame_blending: bool = False
        self.depth_texture_name: Literal["NULL"] = NULL
        # flags
        self.p2p: bool = False
        self.p2p_sel: bool = False
        self.affected_by_wind: bool = False
        self.tinted: bool = False
        self.bounce: bool = False
        self.random: bool = False
        self.inherit: bool = False
        self.inheritvel: bool = False
        self.inherit_local: bool = False
        self.splat: bool = False
        self.inherit_part: bool = False
        self.depth_texture: bool = False
        # controllers
        self.alphastart: float = 0.0
        self.alphamid: float = 0.0
        self.alphaend: float = 0.0
        self.birthrate: float = 0.0
        self.randombirthrate: float = 0.0
        self.bounce_co: float = 0.0
        self.combinetime: float = 0.0
        self.drag: float = 0.0
        self.fps: float = 0.0
        self.frameend: float = 0.0
        self.framestart: float = 0.0
        self.grav: float = 0.0
        self.lifeexp: float = 0.0
        self.mass: float = 0.0
        self.p2p_bezier2: float = 0.0
        self.p2p_bezier3: float = 0.0
        self.particlerot: float = 0.0
        self.randvel: float = 0.0
        self.sizestart: float = 0.0
        self.sizemid: float = 0.0
        self.sizeend: float = 0.0
        self.sizestart_y: float = 0.0
        self.sizemid_y: float = 0.0
        self.sizeend_y: float = 0.0
        self.spread: float = 0.0
        self.threshold: float = 0.0
        self.velocity: float = 0.0
        self.xsize: float = 2.0
        self.ysize: float = 2.0
        self.blurlength: float = 0.0
        self.lightningdelay: float = 0.0
        self.lightningradius: float = 0.0
        self.lightningsubdiv: float = 0.0
        self.lightningscale: float = 0.0
        self.lightningzigzag: float = 0.0
        self.percentstart: float = 0.0
        self.percentmid: float = 0.0
        self.percentend: float = 0.0
        self.targetsize: float = 0.0
        self.numcontrolpts: float = 0.0
        self.controlptradius: float = 0.0
        self.controlptdelay: float = 0.0
        self.tangentspread: float = 0.0
        self.tangentlength: float = 0.0
        self.colorstart: tuple[float, float, float] = (1.0, 1.0, 1.0)
        self.colormid: tuple[float, float, float] = (1.0, 1.0, 1.0)
        self.colorend: tuple[float, float, float] = (1.0, 1.0, 1.0)

    def add_to_collection(
        self,
        collection: bpy.types.Collection,
        options: ImportOptions,
    ):
        mesh = self.create_mesh(self.name)
        obj = bpy.data.objects.new(self.name, mesh)

        self.set_object_data(obj, options)
        collection.objects.link(obj)
        return obj

    def create_mesh(self, name: str) -> bpy.types.Mesh:
        verts = [
            ((self.xsize / 2) / 100.0, (self.ysize / 2) / 100.0, 0.0),
            ((self.xsize / 2) / 100.0, (-self.ysize / 2) / 100.0, 0.0),
            ((-self.xsize / 2) / 100.0, (-self.ysize / 2) / 100.0, 0.0),
            ((-self.xsize / 2) / 100.0, (self.ysize / 2) / 100.0, 0.0),
        ]
        indices: list[tuple[int, int, int]] = [(0, 1, 2), (0, 2, 3)]
        # Create the mesh itself
        mesh = bpy.data.meshes.new(name)
        mesh.vertices.add(len(verts))
        mesh.vertices.foreach_set("co", unpack_list(verts))
        num_faces = len(indices)
        mesh.loops.add(3 * num_faces)
        mesh.loops.foreach_set("vertex_index", unpack_list(indices))
        mesh.polygons.add(num_faces)
        mesh.polygons.foreach_set("loop_start", range(0, 3 * num_faces, 3))
        mesh.polygons.foreach_set("loop_total", (3,) * num_faces)
        mesh.update()
        return mesh

    def set_object_data(
        self,
        obj: bpy.types.Object,
        options: ImportOptions,
    ):
        super().set_object_data(obj, options)

        obj.kb.meshtype = self.meshtype

        for attrname in self.EMITTER_ATTRS:
            value = getattr(self, attrname)
            if attrname == "spawntype":
                if value == 0:
                    value = "Normal"
                elif value == 1:
                    value = "Trail"
            elif attrname == "update":
                if value.title() not in [
                    "Fountain",
                    "Single",
                    "Explosion",
                    "Lightning",
                ]:
                    value = "NONE"
                else:
                    value = value.title()
            elif attrname == "emitter_render":
                if value not in [
                    "Normal",
                    "Linked",
                    "Billboard_to_Local_Z",
                    "Billboard_to_World_Z",
                    "Aligned_to_World_Z",
                    "Aligned_to_Particle_Dir",
                    "Motion_Blur",
                ]:
                    value = "NONE"
            elif attrname == "blend":
                if value.lower() == "punchthrough":
                    value = "Punch-Through"
                elif value.title() not in ["Lighten", "Normal", "Punch-Through"]:
                    value = "NONE"
            elif attrname == "p2p_sel":
                if self.p2p_sel:
                    obj.kb.p2p_type = "Bezier"
                else:
                    obj.kb.p2p_type = "Gravity"
                continue
            setattr(obj.kb, attrname, value)

    def load_object_data(
        self,
        obj: bpy.types.Object,
        eval_obj: bpy.types.Object,
        options: ImportOptions,
    ):
        super().load_object_data(obj, eval_obj, options)

        for attrname in self.EMITTER_ATTRS:
            value = getattr(obj.kb, attrname, None)

            if attrname == "spawntype":
                if value == "Normal":
                    value = 0
                elif value == "Trail":
                    value = 1
                else:
                    continue
            elif attrname == "update":
                if value not in ["Fountain", "Single", "Explosion", "Lightning"]:
                    continue
            elif attrname == "emitter_render":
                if value not in [
                    "Normal",
                    "Linked",
                    "Billboard_to_Local_Z",
                    "Billboard_to_World_Z",
                    "Aligned_to_World_Z",
                    "Aligned_to_Particle_Dir",
                    "Motion_Blur",
                ]:
                    continue
            elif attrname == "blend":
                if value == "Punch-Through":
                    value = "PunchThrough"
                elif value not in ["Lighten", "Normal"]:
                    continue
            elif attrname == "p2p_sel":
                self.p2p_sel = obj.kb.p2p_type == "Bezier"
                continue

            setattr(self, attrname, value)
