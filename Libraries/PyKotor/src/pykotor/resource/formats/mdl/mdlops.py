from __future__ import annotations

import math
import os
import re
import struct

from dataclasses import dataclass

from numpy.lib import type_check

VERSION = "1.0.2"


@dataclass
class Structs:
    fileheader: dict[str, int | str]
    geoheader: dict[str, int | str]
    modelheader: dict[str, int | str]
    nameheader: dict[str, int | str]
    nameindexes: dict[str, int | str]
    names: dict[str, int | str]
    animindexes: dict[str, int | str]
    animheader: dict[str, int | str]
    animevents: dict[str, int | str]
    nodeheader: dict[str, int | str]
    nodechildren: dict[str, int | str]
    controllers: dict[str, int | str]
    controllerdata: dict[str, int | str]


structs = Structs(
    fileheader={
        "loc": 0,
        "num": 3,
        "size": 4,
        "dnum": 1,
        "name": "file_header",
        "tmplt": "III",
    },
    geoheader={
        "loc": 12,
        "num": 1,
        "size": 80,
        "dnum": 1,
        "name": "geo_header",
        "tmplt": "II32sIIIIIIIIBBBB",
    },
    modelheader={
        "loc": 92,
        "num": 1,
        "size": 92,
        "dnum": 1,
        "name": "model_header",
        "tmplt": "BBBBIIIIIffffffffff32sI",
    },
    nameheader={
        "loc": 180,
        "num": 1,
        "size": 28,
        "dnum": 1,
        "name": "name_header",
        "tmplt": "IIIIIII",
    },
    nameindexes={
        "loc": 4,
        "num": 5,
        "size": 4,
        "dnum": 1,
        "name": "name_indexes",
        "tmplt": "I",
    },
    names={"loc": -1, "num": -1, "size": -1, "dnum": 1, "name": "names", "tmplt": "s"},
    animindexes={
        "loc": 5,
        "num": 6,
        "size": 4,
        "dnum": 1,
        "name": "anim_indexes",
        "tmplt": "I",
    },
    animheader={
        "loc": -1,
        "num": 1,
        "size": 56,
        "dnum": 1,
        "name": "anim_header",
        "tmplt": "ff32sIIII",
    },
    animevents={
        "loc": 3,
        "num": 4,
        "size": 36,
        "dnum": 1,
        "name": "anim_event",
        "tmplt": "f32s",
    },
    nodeheader={
        "loc": -1,
        "num": 1,
        "size": 80,
        "dnum": 1,
        "name": "node_header",
        "tmplt": "HHHHIffffffIIIIIIIII",
    },
    nodechildren={
        "loc": 13,
        "num": 14,
        "size": 4,
        "dnum": 1,
        "name": "node_children",
        "tmplt": "I",
    },
    controllers={
        "loc": 16,
        "num": 17,
        "size": 16,
        "dnum": 9,
        "name": "controllers",
        "tmplt": "IhhhBBBB",
    },
    controllerdata={
        "loc": 19,
        "num": 20,
        "size": 4,
        "dnum": 1,
        "name": "controller_data",
        "tmplt": "f",
    },
)

ROOTNODE = 3
ANIMROOT = 5
NODETYPE = 0
NODEINDEX = 2

nodelookup = {
    "dummy": 1,
    "light": 3,
    "emitter": 5,
    "reference": 17,
    "trimesh": 33,
    "skin": 97,
    "animmesh": 161,
    "danglymesh": 289,
    "aabb": 545,
    "lightsaber": 2081,
}

reversenode = {v: k for k, v in nodelookup.items()}

classification = {
    "Effect": 0x01,
    "Tile": 0x02,
    "Character": 0x04,
    "Door": 0x08,
    "Lightsaber": 0x10,
    "Placeable": 0x20,
    "Flyer": 0x40,
    "Other": 0x00,
}

reverseclass = {v: k for k, v in classification.items()}

MDX_VERTICES = 0x00000001
MDX_TEX0_VERTICES = 0x00000002
MDX_TEX1_VERTICES = 0x00000004
MDX_TEX2_VERTICES = 0x00000008
MDX_TEX3_VERTICES = 0x00000010
MDX_VERTEX_NORMALS = 0x00000020
MDX_VERTEX_COLORS = 0x00000040
MDX_TANGENT_SPACE = 0x00000080
MDX_BONE_WEIGHTS = 0x00000800
MDX_BONE_INDICES = 0x00001000

NODE_HAS_HEADER = 0x00000001
NODE_HAS_LIGHT = 0x00000002
NODE_HAS_EMITTER = 0x00000004
NODE_HAS_CAMERA = 0x00000008
NODE_HAS_REFERENCE = 0x00000010
NODE_HAS_MESH = 0x00000020
NODE_HAS_SKIN = 0x00000040
NODE_HAS_ANIM = 0x00000080
NODE_HAS_DANGLY = 0x00000100
NODE_HAS_AABB = 0x00000200
NODE_HAS_SABER = 0x00000800

NODE_DUMMY = 1
NODE_LIGHT = 3
NODE_EMITTER = 5
NODE_REFERENCE = 17
NODE_TRIMESH = 33
NODE_SKIN = 97
NODE_DANGLYMESH = 289
NODE_AABB = 545
NODE_SABER = 2081

controllernames = {
    NODE_HAS_HEADER: {
        8: "position",
        20: "orientation",
        36: "scale",
        132: "alpha",
    },
    NODE_HAS_LIGHT: {
        76: "color",
        88: "radius",
        96: "shadowradius",
        100: "verticaldisplacement",
        140: "multiplier",
    },
    NODE_HAS_EMITTER: {
        80: "alphaEnd",
        84: "alphaStart",
        88: "birthrate",
        92: "bounce_co",
        96: "combinetime",
        100: "drag",
        104: "fps",
        108: "frameEnd",
        112: "frameStart",
        116: "grav",
        120: "lifeExp",
        124: "mass",
        128: "p2p_bezier2",
        132: "p2p_bezier3",
        136: "particleRot",
        140: "randvel",
        144: "sizeStart",
        148: "sizeEnd",
        152: "sizeStart_y",
        156: "sizeEnd_y",
        160: "spread",
        164: "threshold",
        168: "velocity",
        172: "xsize",
        176: "ysize",
        180: "blurlength",
        184: "lightningDelay",
        188: "lightningRadius",
        192: "lightningScale",
        196: "lightningSubDiv",
        200: "lightningzigzag",
        216: "alphaMid",
        220: "percentStart",
        224: "percentMid",
        228: "percentEnd",
        232: "sizeMid",
        236: "sizeMid_y",
        240: "m_fRandomBirthRate",
        252: "targetsize",
        256: "numcontrolpts",
        260: "controlptradius",
        264: "controlptdelay",
        268: "tangentspread",
        272: "tangentlength",
        284: "colorMid",
        380: "colorEnd",
        392: "colorStart",
        502: "detonate",
    },
    NODE_HAS_MESH: {
        100: "selfillumcolor",
    },
}

emitter_flags = {
    "p2p": 0x0001,
    "p2p_sel": 0x0002,
    "affectedByWind": 0x0004,
    "m_isTinted": 0x0008,
    "bounce": 0x0010,
    "random": 0x0020,
    "inherit": 0x0040,
    "inheritvel": 0x0080,
    "inherit_local": 0x0100,
    "splat": 0x0200,
    "inherit_part": 0x0400,
    "depth_texture": 0x0800,
    "emitterflag13": 0x1000,
}

emitter_properties = [
    "deadspace",
    "blastRadius",
    "blastLength",
    "numBranches",
    "controlptsmoothing",
    "xgrid",
    "ygrid",
    "spawntype",
    "update",
    "render",
    "blend",
    "texture",
    "chunkname",
    "twosidedtex",
    "loop",
    "renderorder",
    "m_bFrameBlending",
    "m_sDepthTextureName",
]

emitter_prop_match = "|".join(emitter_properties)
emitter_flag_match = "|".join(emitter_flags.keys())


class MDLOps:
    def __init__(self):
        self.model = {}
        self.version = ""
        self.printall = False

    def read_ascii_mdl(self, buffer: str, supercheck: bool = False, options: dict[str, bool] | None = None) -> dict[str, any]:
        """Reads a KOTOR MDL file in ASCII format.

        :param buffer: The ASCII MDL file contents.
        :param supercheck: Whether to check for a supermodel.
        :param options: A dictionary of options.
        :return: A dictionary containing the parsed MDL data.
        """
        file, extension, filepath = re.match(r"(.*[\\\/])*([^\\\/]+)\.(mdl.*)$", buffer).groups()
        self.model["filename"] = file
        self.model["filepath+name"] = filepath
        pathonly = filepath[:-len(self.model["filename"])]

        if options is None:
            options = {}

        # set up default options for functionality
        options["weight_by_angle"] = options.get("weight_by_angle", False)
        options["weight_by_area"] = options.get("weight_by_area", True)
        options["use_weights"] = options.get("use_weights", options["weight_by_angle"] or options["weight_by_area"])
        if not options["use_weights"]:
            options["weight_by_angle"] = False
            options["weight_by_area"] = False
        options["use_crease_angle"] = options.get("use_crease_angle", False)
        options["crease_angle"] = options.get("crease_angle", math.pi / 3.0)
        options["validate_vertex_data"] = options.get("validate_vertex_data", True)
        options["recalculate_aabb_tree"] = options.get("recalculate_aabb_tree", True)
        options["skip_extra_partnames"] = options.get("skip_extra_partnames", False)
        options["convert_skin"] = options.get("convert_skin", False)
        options["convert_saber"] = options.get("convert_saber", True)
        options["use_ascii_extension"] = options.get("use_ascii_extension", False)

        self.model["source"] = "ascii"
        self.model["bmin"] = [-5, -5, -1]
        self.model["bmax"] = [5, 5, 10]
        self.model["radius"] = 7
        self.model["numanims"] = 0
        self.model["ignorefog"] = 0
        self.model["animationscale"] = 0.971
        self.model["compress_quaternions"] = 0
        self.model["meshsequence"] = 1
        self.model["fakenodes"] = 0
        self.model["nodes"] = {}
        self.model["partnames"] = []
        self.model["nodeindex"] = {"null": -1}
        self.model["totalnumnodes"] = 0
        self.model["bumpmapped_texture"] = {}
        self.model["headlink"] = 0
        self.model["anims"] = {}
        self.model["nodes"]["truenodenum"] = 0

        # emitter properties
        emitter_properties = [
            "deadspace",
            "blastRadius",
            "blastLength",
            "numBranches",
            "controlptsmoothing",
            "xgrid",
            "ygrid",
            "spawntype",
            "update",
            "render",
            "blend",
            "texture",
            "chunkname",
            "twosidedtex",
            "loop",
            "renderorder",
            "m_bFrameBlending",
            "m_sDepthTextureName",
        ]
        # emitter flags
        emitter_flags = {
            "p2p": 0x0001,
            "p2p_sel": 0x0002,
            "affectedByWind": 0x0004,
            "m_isTinted": 0x0008,
            "bounce": 0x0010,
            "random": 0x0020,
            "inherit": 0x0040,
            "inheritvel": 0x0080,
            "inherit_local": 0x0100,
            "splat": 0x0200,
            "inherit_part": 0x0400,
            "depth_texture": 0x0800,
            "emitterflag13": 0x1000,
        }
        # prepare emitter regex matches, all properties and flags are handled alike
        emitter_prop_match = "|".join(emitter_properties)
        emitter_flag_match = "|".join(emitter_flags.keys())

        nodenum = 0
        isgeometry = False
        isanimation = False
        innode = False
        animnum = 0
        task = ""
        nodeindex = {"null": -1}
        temp1 = 0
        temp2 = 0
        temp3 = 0
        temp4 = 0
        temp5 = 0
        f1matches = 0
        f2matches = 0
        pathonly = ""
        t = 0

        for line in buffer.splitlines():
            if line.strip() == "beginmodelgeom":
                nodenum = 0
                isgeometry = True
            elif line.strip() == "endmodelgeom":
                isgeometry = False
                nodenum = 0
            elif re.match(r"\s*bumpmapped_texture\s+(\S*)", line):
                self.model["bumpmapped_texture"][line.split()[1].lower()] = 1
            elif re.match(r"^\s*headlink\s+(\S+)", line):
                self.model["headlink"] = int(line.split()[1])
            elif re.match(r"\s*compress_quaternions\s+(\S*)", line):
                self.model["compress_quaternions"] = int(line.split()[1])
            elif re.match(r"\s*newanim\s+(\S*)\s+(\S*)", line):
                isanimation = True
                self.model["anims"][animnum] = {}
                self.model["anims"][animnum]["name"] = line.split()[1]
                self.model["numanims"] += 1
                self.model["anims"][animnum]["nodelist"] = []
                self.model["anims"][animnum]["eventtimes"] = []
                self.model["anims"][animnum]["eventnames"] = []
                self.model["anims"][animnum]["compress_quaternions"] = self.model["compress_quaternions"]
            elif isanimation and line.strip() == "doneanim":
                isanimation = False
                animnum += 1
            elif isanimation and re.match(r"\s*length\s+(\S*)", line):
                self.model["anims"][animnum]["length"] = float(line.split()[1])
            elif isanimation and re.match(r"\s*animroot\s+(\S*)", line):
                self.model["anims"][animnum]["animroot"] = line.split()[1]
            elif isanimation and re.match(r"\s*transtime\s+(\S*)", line):
                self.model["anims"][animnum]["transtime"] = float(line.split()[1])
            elif re.match(r"\s*newmodel\s+(\S*)", line):
                self.model["name"] = line.split()[1]
            elif re.match(r"\s*setsupermodel\s+(\S*)\s+(\S*)", line):
                self.model["supermodel"] = line.split()[2]
            elif not innode and re.match(r"\s*bmin\s+(\S*)\s+(\S*)\s+(\S*)", line):
                self.model["bmin"] = [float(line.split()[1]), float(line.split()[2]), float(line.split()[3])]
            elif not innode and re.match(r"\s*bmax\s+(\S*)\s+(\S*)\s+(\S*)", line):
                self.model["bmax"] = [float(line.split()[1]), float(line.split()[2]), float(line.split()[3])]
            elif innode and re.match(r"\s*bmin\s+(\S*)\s+(\S*)\s+(\S*)", line):
                self.model["nodes"][nodenum]["bboxmin"] = [float(line.split()[1]), float(line.split()[2]), float(line.split()[3])]
            elif innode and re.match(r"\s*bmax\s+(\S*)\s+(\S*)\s+(\S*)", line):
                self.model["nodes"][nodenum]["bboxmax"] = [float(line.split()[1]), float(line.split()[2]), float(line.split()[3])]
            elif innode and (self.model["nodes"][nodenum]["nodetype"] & NODE_HAS_MESH) and re.match(r"^\s*radius\s+(\S+)", line):
                self.model["nodes"][nodenum]["radius"] = float(line.split()[1])
            elif innode and re.match(r"\s*average\s+(\S*)\s+(\S*)\s+(\S*)", line):
                self.model["nodes"][nodenum]["average"] = [float(line.split()[1]), float(line.split()[2]), float(line.split()[3])]
            elif re.match(r"\s*classification\s+(\S*)", line):
                self.model["classification"] = line.split()[1].capitalize()
            elif re.match(r"^\s*classification_unk1\s+(\S+)", line):
                self.model["classification_unk1"] = int(line.split()[1])
            elif re.match(r"^\s*ignorefog\s+(\S+)", line):
                self.model["ignorefog"] = int(line.split()[1])
            elif not innode and re.match(r"\s*radius\s+(\S*)", line):
                self.model["radius"] = float(line.split()[1])
            elif re.match(r"\s*setanimationscale\s+(\S*)", line):
                self.model["animationscale"] = float(line.split()[1])
            elif innode and re.match(r"^\s*(" + emitter_prop_match + r")\s+(\S+)\s*$", line):
                self.model["nodes"][nodenum][line.split()[1]] = line.split()[2]
            elif innode and re.match(r"^\s*(" + emitter_flag_match + r")\s+(\S+)\s*$", line):
                if "emitterflags" not in self.model["nodes"][nodenum]:
                    self.model["nodes"][nodenum]["emitterflags"] = 0
                if int(line.split()[2]) == 1:
                    self.model["nodes"][nodenum]["emitterflags"] |= emitter_flags[line.split()[1]]
                self.model["nodes"][nodenum][line.split()[1]] = int(line.split()[2])
            elif not innode and isanimation and re.match(r"\s*node\s+(\S*)\s+(\S*)", line):
                innode = True
                nname = line.split()[2].lower()
                if nname.startswith("2081__"):
                    nname = nname[7:]
                nodenum = self.model["nodeindex"].get(nname, None)
                if nodenum is None:
                    nodenum = len(self.model["partnames"])
                    self.model["nodeindex"][nname] = nodenum
                    self.model["partnames"].append(nname)
                self.model["anims"][animnum]["nodelist"].append(nodenum)
                self.model["anims"][animnum]["nodes"]["numnodes"] = len(self.model["anims"][animnum]["nodelist"])
                self.model["anims"][animnum]["nodes"][nodenum] = {}
                self.model["anims"][animnum]["nodes"][nodenum]["nodenum"] = nodenum
                self.model["anims"][animnum]["nodes"][nodenum]["nodetype"] = nodelookup["dummy"]
                self.model["anims"][animnum]["nodes"][nodenum]["controllernum"] = 0
                self.model["anims"][animnum]["nodes"][nodenum]["controllerdatanum"] = 0
                self.model["anims"][animnum]["nodes"][nodenum]["childcount"] = 0
                self.model["anims"][animnum]["nodes"][nodenum]["children"] = []
            elif innode and isanimation and line.strip() == "endnode":
                innode = False
            elif innode and line.strip() == "endnode" and isgeometry:
                nodenum += 1
                innode = False
                task = ""
                self.model["nodes"][nodenum] = {}
                self.model["nodes"][nodenum]["header"] = {}
            elif not innode and isgeometry and re.match(r"\s*node\s+(\S*)\s+(\S*)", line):
                ntype, nname = line.split()[1].lower(), line.split()[2]
                if nname.startswith("2081__"):
                    ntype = "lightsaber"
                    nname = nname[7:]
                    self.model["nodes"][nodenum]["convert_saber"] = True
                nname_key = nname.lower()
                self.model["nodes"]["truenodenum"] += 1
                innode = True
                self.model["nodes"][nodenum] = {}
                self.model["nodes"][nodenum]["nodenum"] = nodenum
                self.model["nodes"][nodenum]["render"] = 1
                self.model["nodes"][nodenum]["shadow"] = 0
                self.model["nodes"][nodenum]["nodetype"] = nodelookup[ntype]
                if self.model["nodes"][nodenum]["nodetype"] & NODE_HAS_SKIN:
                    self.model["nodes"][nodenum]["mdxdatasize"] = 64
                    self.model["nodes"][nodenum]["texturenum"] = 1
                elif self.model["nodes"][nodenum]["nodetype"] & NODE_HAS_DANGLY:
                    self.model["nodes"][nodenum]["mdxdatasize"] = 32
                    self.model["nodes"][nodenum]["texturenum"] = 1
                else:
                    self.model["nodes"][nodenum]["mdxdatasize"] = 24
                    self.model["nodes"][nodenum]["texturenum"] = 0
                if self.model["nodes"][nodenum]["nodetype"] & NODE_HAS_MESH:
                    quo = self.model["meshsequence"] // 100
                    mod = self.model["meshsequence"] % 100
                    self.model["nodes"][nodenum]["array3"] = (2 ** quo) * 100 - (t - (mod if mod else quo * 100)) - (0 if quo else 1)
                    self.model["nodes"][nodenum]["inv_count1"] = self.model["nodes"][nodenum]["array3"]
                    self.model["meshsequence"] += 1
                self.model["nodes"][nodenum]["texturenum"] = 0
                self.model["nodes"][nodenum]["mdxdatabitmap"] = 0
                self.model["nodes"][nodenum]["sg_base2"] = 1
                self.model["nodes"][nodenum]["bboxmin"] = [-5, -5, -5]
                self.model["nodes"][nodenum]["bboxmax"] = [5, 5, 5]
                self.model["nodes"][nodenum]["radius"] = 10
                self.model["nodes"][nodenum]["average"] = [0, 0, 0]
                self.model["nodes"][nodenum]["diffuse"] = [0.8, 0.8, 0.8]
                self.model["nodes"][nodenum]["ambient"] = [0.2, 0.2, 0.2]
                self.model["nodes"][nodenum]["controllernum"] = 0
                self.model["nodes"][nodenum]["controllerdatanum"] = 0
                self.model["nodes"][nodenum]["childcount"] = 0
                self.model["nodes"][nodenum]["children"] = []
                self.model["partnames"].append(nname)
                self.model["nodeindex"][nname_key] = nodenum
                self.model["nodeindex"][nname] = nodenum
            elif innode and re.match(r"^\s*inv_count\s+(\S+)(?:\s+(\S+))?", line):
                self.model["nodes"][nodenum]["array3"] = int(line.split()[1])
                self.model["nodes"][nodenum]["inv_count1"] = int(line.split()[1])
                if len(line.split()) > 2:
                    self.model["nodes"][nodenum]["inv_count2"] = int(line.split()[2])
            elif innode and re.match(r"^\s*radius\s+(\S*)", line) and self.model["nodes"][nodenum]["nodetype"] != nodelookup["light"]:
                self.model["radius"] = float(line.split()[1])
            elif innode and self.read_ascii_controller(line, self.model["nodes"][nodenum]["nodetype"], innode, isanimation, self.model, nodenum, animnum, buffer):
                pass
            elif innode and re.match(r"\s*parent\s*(\S*)", line):
                if isgeometry:
                    ref = self.model["nodes"]
                else:
                    ref = self.model["anims"][animnum]["nodes"]
                ref[nodenum]["parent"] = line.split()[1]
                ref[nodenum]["parentnodenum"] = self.model["nodeindex"].get(line.split()[1].lower(), -1)
                if ref[nodenum]["parentnodenum"] != -1:
                    ref[nodenum]["childposition"] = ref[ref[nodenum]["parentnodenum"]]["childcount"]
                    ref[ref[nodenum]["parentnodenum"]]["children"].append(nodenum)
                    ref[ref[nodenum]["parentnodenum"]]["childcount"] += 1
            elif innode and re.match(r"\s*flareradius\s+(\S*)", line):
                self.model["nodes"][nodenum]["flareradius"] = float(line.split()[1])
            elif innode and re.match(r"\s*(flarepositions|flaresizes|flarecolorshifts|texturenames)\s+(\S*)", line):
                task = ""
                count = 0
                if int(line.split()[2]) > 0:
                    self.model["nodes"][nodenum][line.split()[1]] = []
                    self.model["nodes"][nodenum][line.split()[1] + "num"] = int(line.split()[2])
                    task = line.split()[1]
            elif innode and re.match(r"\s*ambientonly\s+(\S*)", line):
                self.model["nodes"][nodenum]["ambientonly"] = int(line.split()[1])
            elif innode and re.match(r"\s*ndynamictype\s+(\S*)", line):
                self.model["nodes"][nodenum]["ndynamictype"] = int(line.split()[1])
            elif innode and re.match(r"\s*affectdynamic\s+(\S*)", line):
                self.model["nodes"][nodenum]["affectdynamic"] = int(line.split()[1])
            elif innode and re.match(r"\s*flare\s+(\S*)", line):
                self.model["nodes"][nodenum]["flare"] = int(line.split()[1])
            elif innode and re.match(r"\s*lightpriority\s+(\S*)", line):
                self.model["nodes"][nodenum]["lightpriority"] = int(line.split()[1])
            elif innode and re.match(r"\s*fadinglight\s+(\S*)", line):
                self.model["nodes"][nodenum]["fadinglight"] = int(line.split()[1])
            elif innode and re.match(r"\s*refmodel\s+(\S+)", line):
                self.model["nodes"][nodenum]["refModel"] = line.split()[1]
            elif innode and re.match(r"\s*reattachable\s+(\S+)", line):
                self.model["nodes"][nodenum]["reattachable"] = int(line.split()[1])
            elif innode and re.match(r"\s*render\s+(\S*)", line):
                self.model["nodes"][nodenum]["render"] = int(line.split()[1])
            elif innode and re.match(r"\s*shadow\s+(\S*)", line):
                self.model["nodes"][nodenum]["shadow"] = int(line.split()[1])
            elif innode and re.match(r"\s*lightmapped\s+(\S*)", line):
                self.model["nodes"][nodenum]["lightmapped"] = int(line.split()[1])
            elif innode and re.match(r"\s*rotatetexture\s+(\S*)", line):
                self.model["nodes"][nodenum]["rotatetexture"] = int(line.split()[1])
            elif innode and re.match(r"\s*m_bIsBackgroundGeometry\s+(\S*)", line):
                self.model["nodes"][nodenum]["m_bIsBackgroundGeometry"] = int(line.split()[1])
            elif innode and re.match(r"\s*tangentspace\s+(\S*)", line):
                self.model["nodes"][nodenum]["tangentspace"] = int(line.split()[1])
                if "bitmap" in self.model["nodes"][nodenum] and self.model["nodes"][nodenum]["bitmap"].lower() != "null":
                    self.model["nodes"][nodenum]["mdxdatabitmap"] |= MDX_TANGENT_SPACE
            elif innode and re.match(r"\s*beaming\s+(\S*)", line):
                self.model["nodes"][nodenum]["beaming"] = int(line.split()[1])
            elif innode and re.match(r"\s*transparencyhint\s+(\S*)", line):
                self.model["nodes"][nodenum]["transparencyhint"] = int(line.split()[1])
            elif innode and re.match(r"\s*transparencyhint\s+(\S*)", line):
                self.model["nodes"][nodenum]["transparencyhint"] = int(line.split()[1])
            elif innode and re.match(r"\s*danglymesh\s+(\S*)\s+(\S*)\s+(\S*)\s+(\S*)", line):
                self.model["nodes"][nodenum]["period"] = float(line.split()[1])
                self.model["nodes"][nodenum]["tightness"] = float(line.split()[2])
                self.model["nodes"][nodenum]["displacement"] = float(line.split()[3])
                self.model["nodes"][nodenum]["constraints"] = int(line.split()[4])
            elif innode and re.match(r"\s*constraints\s+(\S*)", line):
                self.model["nodes"][nodenum]["constraints"] = int(line.split()[1])
            elif innode and re.match(r"\s*position\s+(\S*)\s+(\S*)\s+(\S*)", line):
                self.model["nodes"][nodenum]["position"] = [float(x) for x in line.split()[1:4]]
            elif innode and re.match(r"\s*orientation\s+(\S*)\s+(\S*)\s+(\S*)\s+(\S*)", line):
                self.model["nodes"][nodenum]["orientation"] = [float(x) for x in line.split()[1:5]]
            elif innode and re.match(r"\s*scale\s+(\S*)", line):
                self.model["nodes"][nodenum]["scale"] = float(line.split()[1])
            elif innode and re.match(r"\s*bitmap\s+(\S*)", line):
                self.model["nodes"][nodenum]["bitmap"] = line.split()[1]
                if line.split()[1].lower() != "null":
                    self.model["nodes"][nodenum]["texturenum"] += 1
            elif innode and re.match(r"\s*verts\s+(\S*)", line):
                self.model["nodes"][nodenum]["vertnum"] = int(line.split()[1])
                self.model["nodes"][nodenum]["verts"] = []
                task = "verts"
            elif innode and re.match(r"\s*faces\s+(\S*)", line):
                self.model["nodes"][nodenum]["facenum"] = int(line.split()[1])
                self.model["nodes"][nodenum]["faces"] = []
                task = "faces"
            elif innode and re.match(r"\s*tverts\s+(\S*)", line):
                self.model["nodes"][nodenum]["tvertnum"] = int(line.split()[1])
                self.model["nodes"][nodenum]["tverts"] = []
                task = "tverts"
            elif innode and re.match(r"\s*colors\s+(\S*)", line):
                self.model["nodes"][nodenum]["colornum"] = int(line.split()[1])
                self.model["nodes"][nodenum]["colors"] = []
                task = "colors"
            elif innode and re.match(r"\s*weights\s+(\S*)", line):
                self.model["nodes"][nodenum]["weightnum"] = int(line.split()[1])
                self.model["nodes"][nodenum]["weights"] = []
                task = "weights"
            elif innode and task == "verts" and re.match(r"\s*(\S*)\s+(\S*)\s+(\S*)", line):
                self.model["nodes"][nodenum]["verts"].append([float(x) for x in line.split()[:3]])
            elif innode and task == "faces" and re.match(r"\s*(\S*)\s+(\S*)\s+(\S*)\s+(\S*)\s+(\S*)\s+(\S*)\s+(\S*)\s+(\S*)\s+(\S*)\s+(\S*)\s+(\S*)\s+(\S*)", line):
                self.model["nodes"][nodenum]["faces"].append([int(x) for x in line.split()[:12]])
            elif innode and task == "tverts" and re.match(r"\s*(\S*)\s+(\S*)", line):
                self.model["nodes"][nodenum]["tverts"].append([float(x) for x in line.split()[:2]])
            elif innode and task == "colors" and re.match(r"\s*(\S*)\s+(\S*)\s+(\S*)\s+(\S*)", line):
                self.model["nodes"][nodenum]["colors"].append([float(x) for x in line.split()[:4]])
            elif innode and task == "weights" and re.match(r"\s*(\S*)\s+(\S*)\s+(\S*)\s+(\S*)", line):
                self.model["nodes"][nodenum]["weights"].append([float(x) for x in line.split()[:4]])
            elif innode and task in ["flarepositions", "flaresizes", "flarecolorshifts"] and re.match(r"\s*(\S*)\s+(\S*)\s+(\S*)", line):
                self.model["nodes"][nodenum][task].append([float(x) for x in line.split()[:3]])
                count += 1
                if count == self.model["nodes"][nodenum][task + "num"]:
                    task = ""
                    count = 0
        elif innode and task == "texturenames" and re.match(r"\s*(\S*)", line):
            self.model["nodes"][nodenum][task].append(line.strip())
            count += 1
            if count == self.model["nodes"][nodenum][task + "num"]:
                task = ""
                count = 0
        elif isanimation and re.match(r"\s*event\s+(\S*)\s+(\S*)", line):
            self.model["anims"][animnum]["eventtimes"].append(float(line.split()[1]))
            self.model["anims"][animnum]["eventnames"].append(line.split()[2])
        # Calculate new aabb trees if possible
        if options["recalculate_aabb_tree"] and hasattr(self, "detect_format"):
            # Advanced walkmesh functions are available, build working aabb trees
            for i in range(self.model["nodes"]["truenodenum"]):
                if not (self.model["nodes"][i]["nodetype"] & NODE_HAS_AABB):
                    continue
                # Prepare enough walkmesh structure for the walkmesh aabb tree calculation
                self.model["nodes"][i]["walkmesh"] = {
                    "verts": self.model["nodes"][i]["verts"],
                    "faces": [[face[8], face[9], face[10]] for face in self.model["nodes"][i]["faces"]],
                    "aabbs": []
                }
                self.aabb(self.model["nodes"][i]["walkmesh"], list(range(len(self.model["nodes"][i]["walkmesh"]["faces"]))))

        # Compute bounding box, average, radius
        for i in range(self.model["nodes"]["truenodenum"]):
            if not (self.model["nodes"][i]["nodetype"] & NODE_HAS_MESH):
                continue
            used_vpos = {}
            used_verts = [0, 0, 0]
            vsum = [0.0, 0.0, 0.0]
            self.model["nodes"][i]["bboxmin"] = [0.0, 0.0, 0.0]
            self.model["nodes"][i]["bboxmax"] = [0.0, 0.0, 0.0]
            for vert in self.model["nodes"][i]["verts"]:
                vert_key = f"{vert[0]:.4g},{vert[1]:.4g},{vert[2]:.4g}"
                for j in range(3):
                    if vert[j] < self.model["nodes"][i]["bboxmin"][j]:
                        self.model["nodes"][i]["bboxmin"][j] = vert[j]
                    if vert[j] > self.model["nodes"][i]["bboxmax"][j]:
                        self.model["nodes"][i]["bboxmax"][j] = vert[j]
                if vert_key in used_vpos:
                    continue
                used_vpos[vert_key] = 1
                for j in range(3):
                    used_verts[j] += 1
                    vsum[j] += vert[j]
            
            # Compute node average from unique vertex positions
            self.model["nodes"][i]["average"] = [
                vsum[j] / used_verts[j] if used_verts[j] else 0.0 for j in range(3)
            ]
            
            # Compute node radius
            self.model["nodes"][i]["radius"] = 0.0
            for vert in self.model["nodes"][i]["verts"]:
                v_rad = [vert[j] - self.model["nodes"][i]["average"][j] for j in range(3)]
                vec_len = math.sqrt(sum(x**2 for x in v_rad))
                if vec_len > self.model["nodes"][i]["radius"]:
                    self.model["nodes"][i]["radius"] = vec_len

        # Compute model-global translations and vertex coordinates for each node
        for i in range(self.model["nodes"]["truenodenum"]):
            ancestry = [i]
            parent = self.model["nodes"][i]
            while parent["parentnodenum"] != -1:
                ancestry.insert(0, parent["parentnodenum"])
                parent = self.model["nodes"][parent["parentnodenum"]]
            self.model["nodes"][i]["transform"] = {
                "position": [0.0, 0.0, 0.0],
                "orientation": [0.0, 0.0, 0.0, 1.0],
                "verts": []
            }
            for ancestor in ancestry:
                if "Bcontrollers" in self.model["nodes"][ancestor] and 8 in self.model["nodes"][ancestor]["Bcontrollers"]:
                    for j in range(3):
                        self.model["nodes"][i]["transform"]["position"][j] += self.model["nodes"][ancestor]["Bcontrollers"][8]["values"][0][j]
                if "Bcontrollers" in self.model["nodes"][ancestor] and 20 in self.model["nodes"][ancestor]["Bcontrollers"]:
                    self.model["nodes"][i]["transform"]["orientation"] = self.quaternion_multiply(
                        self.model["nodes"][i]["transform"]["orientation"],
                        self.model["nodes"][ancestor]["Bcontrollers"][20]["values"][0]
                    )

        # Create a position-indexed structure containing all vertices in all meshes
        face_by_pos = {}
        for i in range(self.model["nodes"]["truenodenum"]):
            if not (self.model["nodes"][i]["nodetype"] & NODE_HAS_MESH) or (self.model["nodes"][i]["nodetype"] & NODE_HAS_SABER):
                continue
            for work, vert in enumerate(self.model["nodes"][i]["verts"]):
                vert_pos = self.quaternion_apply(self.model["nodes"][i]["transform"]["orientation"], vert)
                vert_pos = [
                    self.model["nodes"][i]["transform"]["position"][j] + vert_pos[j] for j in range(3)
                ]
                self.model["nodes"][i]["transform"]["verts"].append(vert_pos)
                vert_key = f"{vert_pos[0]:.4g},{vert_pos[1]:.4g},{vert_pos[2]:.4g}"
                if vert_key not in face_by_pos:
                    face_by_pos[vert_key] = []
                face_by_pos[vert_key].append({
                    "mesh": i,
                    "meshname": self.model["partnames"][i],
                    "faces": self.model["nodes"][i]["vertfaces"][work],
                    "vertex": work
                })

        # Calculate face surface areas and record surface area totals
        faceareas = {}
        for i in range(self.model["nodes"]["truenodenum"]):
            if not (self.model["nodes"][i]["nodetype"] & NODE_HAS_MESH):
                continue
            self.model["nodes"][i]["surfacearea"] = 0
            self.model["nodes"][i]["surfacearea_by_group"] = {}
            faceareas[i] = {}
            for j, face in enumerate(self.model["nodes"][i]["faces"]):
                area = self.facearea(
                    self.model["nodes"][i]["verts"][face[8]],
                    self.model["nodes"][i]["verts"][face[9]],
                    self.model["nodes"][i]["verts"][face[10]]
                )
                faceareas[i][j] = area
                self.model["nodes"][i]["surfacearea"] += area

        # Calculate face surface normals and tangent/bitangent vectors
        for i in range(self.model["nodes"]["truenodenum"]):
            if not (self.model["nodes"][i]["nodetype"] & NODE_HAS_MESH) or (self.model["nodes"][i]["nodetype"] & NODE_HAS_SABER):
                continue
            self.model["nodes"][i]["rawfacenormals"] = []
            self.model["nodes"][i]["worldfacenormals"] = []
            self.model["nodes"][i]["facenormals"] = []

            for j, face in enumerate(self.model["nodes"][i]["faces"]):
                p1 = self.model["nodes"][i]["verts"][face[8]]
                p2 = self.model["nodes"][i]["verts"][face[9]]
                p3 = self.model["nodes"][i]["verts"][face[10]]

                xpx = p1[1] * (p2[2] - p3[2]) + p2[1] * (p3[2] - p1[2]) + p3[1] * (p1[2] - p2[2])
                xpy = p1[2] * (p2[0] - p3[0]) + p2[2] * (p3[0] - p1[0]) + p3[2] * (p1[0] - p2[0])
                xpz = p1[0] * (p2[1] - p3[1]) + p2[0] * (p3[1] - p1[1]) + p3[0] * (p1[1] - p2[1])
                pd = -p1[0] * (p2[1] * p3[2] - p3[1] * p2[2]) - \
                     p2[0] * (p3[1] * p1[2] - p1[1] * p3[2]) - \
                     p3[0] * (p1[1] * p2[2] - p2[1] * p1[2])

                norm = math.sqrt(xpx**2 + xpy**2 + xpz**2)

                self.model["nodes"][i]["rawfacenormals"].append([xpx, xpy, xpz])
                self.model["nodes"][i]["facenormals"].append(self.normalize_vector([xpx, xpy, xpz]))
                self.model["nodes"][i]["worldfacenormals"].append(self.quaternion_apply(
                    self.model["nodes"][i]["transform"]["orientation"],
                    self.model["nodes"][i]["facenormals"][-1]
                ))

                if norm != 0:
                    pd /= norm
                else:
                    print(f"Overlapping vertices in node: {self.model['partnames'][i]} face: {j}")
                    print(f"x: {p1[0]:.5g}, y: {p1[1]:.5g}, z: {p1[2]:.5g}")
                    print(f"x: {p2[0]:.5g}, y: {p2[1]:.5g}, z: {p2[2]:.5g}")
                    print(f"x: {p3[0]:.5g}, y: {p3[1]:.5g}, z: {p3[2]:.5g}")

                face[0:4] = self.model["nodes"][i]["facenormals"][-1] + [pd]

                if self.model["nodes"][i]["bitmap"].lower() == "null" or not (self.model["nodes"][i]["mdxdatabitmap"] & MDX_TANGENT_SPACE):
                    continue

                # Compute face tangent and bitangent vectors for bump-mapped textures
                v0, v1, v2 = [self.model["nodes"][i]["verts"][face[k]] for k in [8, 9, 10]]
                uv0, uv1, uv2 = [self.model["nodes"][i]["tverts"][self.model["nodes"][i]["tverti"][face[k]]] for k in [8, 9, 10]]

                deltaPos1 = [v1[k] - v0[k] for k in range(3)]
                deltaPos2 = [v2[k] - v0[k] for k in range(3)]
                deltaUV1 = [uv1[k] - uv0[k] for k in range(2)]
                deltaUV2 = [uv2[k] - uv0[k] for k in range(2)]

                tNz = (uv0[0] - uv1[0]) * (uv2[1] - uv1[1]) - (uv0[1] - uv1[1]) * (uv2[0] - uv1[0])

                r = deltaUV1[0] * deltaUV2[1] - deltaUV1[1] * deltaUV2[0]
                if r == 0.000000:
                    print(f"Overlapping texture vertices in node: {self.model['partnames'][i]}")
                    print(f"x: {uv0[0]:.7g}, y: {uv0[1]:.7g}")
                    print(f"x: {uv1[0]:.7g}, y: {uv1[1]:.7g}")
                    print(f"x: {uv2[0]:.7g}, y: {uv2[1]:.7g}")
                    r = 2406.6388
                else:
                    r = 1.0 / r

                tangent = [
                    (deltaPos1[0] * deltaUV2[1] - deltaPos2[0] * deltaUV1[1]) * r,
                    (deltaPos1[1] * deltaUV2[1] - deltaPos2[1] * deltaUV1[1]) * r,
                    (deltaPos1[2] * deltaUV2[1] - deltaPos2[2] * deltaUV1[1]) * r
                ]
                tangent = self.normalize_vector(tangent)

                if tangent == [0.0000, 0.0000, 0.0000]:
                    tangent = [1.0, 0.0, 0.0]

                self.model["nodes"][i]["facetangents"].append(tangent)

                bitangent = [
                    (deltaPos2[0] * deltaUV1[0] - deltaPos1[0] * deltaUV2[0]) * r,
                    (deltaPos2[1] * deltaUV1[0] - deltaPos1[1] * deltaUV2[0]) * r,
                    (deltaPos2[2] * deltaUV1[0] - deltaPos1[2] * deltaUV2[0]) * r
                ]
                bitangent = self.normalize_vector(bitangent)

                if bitangent == [0.0000, 0.0000, 0.0000]:
                    bitangent = [1.0, 0.0, 0.0]

                self.model["nodes"][i]["facebitangents"].append(bitangent)

                # Fix tangent space handedness
                cross_nt = [
                    self.model["nodes"][i]["facenormals"][-1][1] * tangent[2] - self.model["nodes"][i]["facenormals"][-1][2] * tangent[1],
                    self.model["nodes"][i]["facenormals"][-1][2] * tangent[0] - self.model["nodes"][i]["facenormals"][-1][0] * tangent[2],
                    self.model["nodes"][i]["facenormals"][-1][0] * tangent[1] - self.model["nodes"][i]["facenormals"][-1][1] * tangent[0]
                ]
                if sum(a * b for a, b in zip(cross_nt, bitangent)) > 0.0:
                    self.model["nodes"][i]["facetangents"][-1] = [-x for x in tangent]

                if tNz > 0.0:
                    self.model["nodes"][i]["facetangents"][-1] = [-x for x in self.model["nodes"][i]["facetangents"][-1]]
                    self.model["nodes"][i]["facebitangents"][-1] = [-x for x in bitangent]

        # Calculate vertex normals and tangent space basis
        for i in range(self.model["nodes"]["truenodenum"]):
            if not (self.model["nodes"][i]["nodetype"] & NODE_HAS_MESH) or (self.model["nodes"][i]["nodetype"] & NODE_HAS_SABER):
                continue

            for work, vert in enumerate(self.model["nodes"][i]["verts"]):
                vert_key = f"{self.model['nodes'][i]['transform']['verts'][work][0]:.4g},{self.model['nodes'][i]['transform']['verts'][work][2]:.4g}"
                position_data = face_by_pos[vert_key]
                meshA = i
                faceA = -1
                sgA = -1
                if "vertfaces" in self.model["nodes"][i] and work in self.model["nodes"][i]["vertfaces"]:
                    faceA = next((face for data in position_data if data["mesh"] == i and data["vertex"] == work for face in data["faces"]), -1)
                if faceA == -1:
                    self.model["nodes"][i]["vertexnormals"][work] = [1, 0, 0]
                    continue
                sgA = self.model["nodes"][i]["faces"][faceA][11]
                self.model["nodes"][i]["vertexnormals"][work] = [0.0, 0.0, 0.0]
                if self.model["nodes"][i]["mdxdatabitmap"] & MDX_TANGENT_SPACE:
                    self.model["nodes"][i]["vertextangents"][work] = [0.0, 0.0, 0.0]
                    self.model["nodes"][i]["vertexbitangents"][work] = [0.0, 0.0, 0.0]
                vertnorm_initialized = False
                for pos_data in position_data:
                    meshB = pos_data["mesh"]
                    for faceB in pos_data["faces"]:
                        is_self = (meshA == meshB and faceA == faceB)
                        if self.model["nodes"][meshA]["render"] != self.model["nodes"][meshB]["render"]:
                            continue
                        if (self.model["nodes"][meshA]["nodetype"] & NODE_HAS_AABB) and meshA != meshB:
                            continue
                        if not (self.model["nodes"][meshB]["faces"][faceB][11] & sgA) and not is_self:
                            continue
                        if options["use_crease_angle"] and vertnorm_initialized and \
                           self.compute_vector_angle(self.model["nodes"][i]["vertexnormals"][work],
                                                     self.model["nodes"][meshB]["worldfacenormals"][faceB]) > options["crease_angle"]:
                            if self.model["nodes"][meshA]["render"]:
                                continue
                        area = faceareas[meshB][faceB] if options["weight_by_area"] else 1
                        angle = -1 if options["weight_by_angle"] else 1

                        bv1, bv2, bv3 = [self.model["nodes"][meshB]["transform"]["verts"][self.model["nodes"][meshB]["faces"][faceB][8+k]] for k in range(3)]

                        if options["weight_by_angle"]:
                            if self.vertex_equals(self.model["nodes"][i]["transform"]["verts"][work], bv1, 4):
                                angle = self.compute_vertex_angle(bv1, bv2, bv3)
                            elif self.vertex_equals(self.model["nodes"][i]["transform"]["verts"][work], bv2, 4):
                                angle = self.compute_vertex_angle(bv2, bv1, bv3)
                            elif self.vertex_equals(self.model["nodes"][i]["transform"]["verts"][work], bv3, 4):
                                angle = self.compute_vertex_angle(bv3, bv1, bv2)
                        if options["weight_by_angle"] and angle == -1:
                            continue
                        vertnorm_initialized = True
                        for j in range(3):
                            self.model["nodes"][i]["vertexnormals"][work][j] += (
                                self.model["nodes"][meshB]["worldfacenormals"][faceB][j] * area * angle
                            )
                        if "facetangents" in self.model["nodes"][meshB]:
                            for j in range(3):
                                self.model["nodes"][i]["vertextangents"][work][j] += (
                                    self.model["nodes"][meshB]["facetangents"][faceB][j] * area * angle
                                )
                                self.model["nodes"][i]["vertexbitangents"][work][j] += (
                                    self.model["nodes"][meshB]["facebitangents"][faceB][j] * area * angle
                                )

                self.model["nodes"][i]["vertexnormals"][work] = self.normalize_vector(self.model["nodes"][i]["vertexnormals"][work])
                if self.model["nodes"][i]["transform"]["orientation"][:3] != [0.0, 0.0, 0.0]:
                    inv_orientation = [-x for x in self.model["nodes"][i]["transform"]["orientation"][:3]] + [self.model["nodes"][i]["transform"]["orientation"][3]]
                    self.model["nodes"][i]["vertexnormals"][work] = self.quaternion_apply(inv_orientation, self.model["nodes"][i]["vertexnormals"][work])

                if "vertextangents" in self.model["nodes"][i] and work in self.model["nodes"][i]["vertextangents"]:
                    self.model["nodes"][i]["Btangentspace"][work] = (
                        self.normalize_vector(self.model["nodes"][i]["vertexbitangents"][work]) +
                        self.normalize_vector(self.model["nodes"][i]["vertextangents"][work]) +
                        self.model["nodes"][i]["vertexnormals"][work]
                    )


        # Calculate adjacent faces using the face-by-position map
        for i in range(self.model["nodes"]["truenodenum"]):
            if not (self.model["nodes"][i]["nodetype"] & NODE_HAS_MESH) or (self.model["nodes"][i]["nodetype"] & NODE_HAS_SABER):
                continue
            results = {}
            consider_all = True
            for j, face in enumerate(self.model["nodes"][i]["faces"]):
                position_data = [
                    face_by_pos[f"{self.model['nodes'][i]['transform']['verts'][face[8+k]][0]:.4g},{self.model['nodes'][i]['transform']['verts'][face[8+k]][1]:.4g},{self.model['nodes'][i]['transform']['verts'][face[8+k]][2]:.4g}"]
                    for k in range(3)
                ]
                vfs = [[], [], []]
                for facevert in range(3):
                    for pos_data in position_data[facevert]:
                        if pos_data["mesh"] == i and pos_data["vertex"] == face[8 + facevert]:
                            vfs[facevert].extend(pos_data["faces"])
                            break
                    if consider_all:
                        for pos_data in position_data[facevert]:
                            if pos_data["mesh"] == i and pos_data["vertex"] != face[8 + facevert]:
                                vfs[facevert].extend(pos_data["faces"])

                matches = {l: {f for f in vfs[l] if f != j} for l in range(3)}
                for l in range(3):
                    next_l = -2 if l == 2 else 1
                    for f in matches[l]:
                        if f in matches[(l + next_l) % 3]:
                            results.setdefault(j, [None, None, None])[l] = f
                    if results.get(j, [None])[l] is not None:
                        self.model["nodes"][i]["faces"][j][5 + l] = results[j][l]

        # Post-process the geometry nodes
        self.postprocessnodes(self.model["nodes"][0], self.model, False)

        # Post-process the animation nodes
        for i in range(self.model["numanims"]):
            self.postprocessnodes(self.model["anims"][i]["nodes"][0], self.model["anims"][i], True)

        # Cook the bone weights and prepare the bone map
        for i in range(self.model["nodes"]["truenodenum"]):
            work = 0
            if self.model["nodes"][i]["nodetype"] == NODE_SKIN:
                self.model["nodes"][i]["node2index"] = [-1] * self.model["nodes"]["truenodenum"]
                for j in range(self.model["nodes"][i]["weightnum"]):
                    total = sum(self.model["nodes"][i]["weights"][j])
                    if abs(1.0 - total) > 0.0001:
                        extra = (1.0 - total) / len(self.model["nodes"][i]["weights"][j])
                        print(f"Node: {self.model['partnames'][i]} Vertex: {j} has weights == {total:.4g} but must be 1.0, "
                              f"{extra:.4g} will be added to each weight to make the total == 1.0")
                    else:
                        extra = 0
                    self.model["nodes"][i]["Bbones"][j] = []
                    for k in range(4):
                        if k < len(self.model["nodes"][i]["bones"][j]):
                            bone_name = self.model["nodes"][i]["bones"][j][k]
                            bone_index = self.model["nodeindex"].get(bone_name.lower(), -1)
                            if self.model["nodes"][i]["node2index"][bone_index] == -1:
                                self.model["nodes"][i]["index2node"][work] = bone_index
                                self.model["nodes"][i]["node2index"][bone_index] = work
                                work += 1
                            self.model["nodes"][i]["Bbones"][j].extend([
                                self.model["nodes"][i]["weights"][j][k] + extra,
                                self.model["nodes"][i]["node2index"][bone_index]
                            ])
                        else:
                            self.model["nodes"][i]["Bbones"][j].extend([0, -1])

        print(f"\nDone reading ascii model: {self.model['filename']}")
        return self.model