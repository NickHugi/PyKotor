from __future__ import annotations

import glob
import re

from typing import ClassVar

import bmesh
import bpy

from bpy_extras.io_utils import unpack_list
from loggerplus import RobustLogger
from mathutils import Color, Matrix, Quaternion, Vector
from typing_extensions import Literal

from pykotor.resource.formats.mdl.reference_only import aabb
from pykotor.resource.formats.mdl.reference_only.ascii import parse
from pykotor.resource.formats.mdl.reference_only.constants import Classification, MeshType, NodeType, defines, utils


class FaceList:
    def __init__(self) -> None:
        self.faces: list[tuple[int, int, int]] = []  # int 3-tuple, vertex indices
        self.shdgr: list[int] = []  # int, shading group for this face
        self.uvIdx: list[tuple[int, int, int]] = []  # int 3-tuple, texture/uv vertex indices
        self.matId: list[int] = []  # int, material index


class FlareList:
    def __init__(self) -> None:
        self.textures: list[str] = []
        self.sizes: list[float] = []
        self.positions: list[tuple[float, float, float]] = []
        self.colorshifts: list[tuple[float, float, float, float]] = []


class GeometryNode:
    """Basic node from which every other is derived."""

    def __init__(self, name: str = "UNNAMED") -> None:
        self.nodetype: str = "undefined"

        self.roottype: str = "mdl"
        self.rootname: str = "undefined"

        self.name: str = name
        self.parentName: str = defines.null
        self.position: tuple[float, float, float] = (0.0, 0.0, 0.0)
        self.orientation: tuple[float, float, float, float] = (1.0, 0.0, 0.0, 0.0)
        self.scale: float = 1.0
        self.wirecolor: tuple[float, float, float] = (0.0, 0.0, 0.0)

        # Name of the corresponding object in blender
        # (used to resolve naming conflicts)
        self.objref: str = ""
        # Parsed lines (by number), allow last parser to include unhandled data
        self.parsed_lines: list[int] = []
        self.rawascii: str = ""  # unprocessed directives

    def __eq__(self, other: object) -> bool:
        if isinstance(other, GeometryNode):
            return self.name == other.name
        return False

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __str__(self) -> str:
        return f"node {self.nodetype} {self.name}"

    def parse1f(self, ascii_block: list[list[str]], floatList: list[float]) -> None:
        l_float: Callable[[str], float] = float
        for line in ascii_block:
            floatList.append(l_float(line[0]))

    def parse2f(self, ascii_block: list[list[str]], floatList: list[tuple[float, float]]) -> None:
        l_float: Callable[[str], float] = float
        for line in ascii_block:
            floatList.append((l_float(line[0]), l_float(line[1])))

    def parse3f(self, ascii_block: list[list[str]], floatList: list[tuple[float, float, float]]) -> None:
        l_float: Callable[[str], float] = float
        for line in ascii_block:
            floatList.append((l_float(line[0]), l_float(line[1]), l_float(line[2])))

    def load_ascii(self, ascii_node: list[list[str]]) -> None:
        l_float: Callable[[str], float] = float
        l_is_number: Callable[[str], bool] = utils.is_number

        for index, line in enumerate(ascii_node):
            try:
                label: str = line[0].lower()
            except IndexError:
                # Probably empty line or whatever, skip it
                continue

            if not l_is_number(label):
                if label == "node":
                    self.name = utils.get_name(line[2])
                    self.parsed_lines.append(index)
                elif label == "endnode":
                    self.parsed_lines.append(index)
                    return
                elif label == "parent":
                    self.parentName = utils.get_name(line[1])
                    self.parsed_lines.append(index)
                elif label == "position":
                    self.position = (l_float(line[1]), l_float(line[2]), l_float(line[3]))
                    self.parsed_lines.append(index)
                elif label == "orientation":
                    axis_angle: tuple[float, float, float, float] = (l_float(line[1]), l_float(line[2]), l_float(line[3]), l_float(line[4]))
                    quat: Quaternion = Quaternion(axis_angle[0:3], axis_angle[3])
                    self.orientation = (quat.w, quat.x, quat.y, quat.z)
                    self.parsed_lines.append(index)
                elif label == "scale":
                    self.scale = l_float(line[1])
                    self.parsed_lines.append(index)
                elif label == "wirecolor":
                    self.wirecolor = (l_float(line[1]), l_float(line[2]), l_float(line[3]))
                    self.parsed_lines.append(index)

    def set_object_data(self, obj: bpy.types.Object) -> None:
        self.objref = obj.name  # used to resolve naming conflicts
        obj.rotation_mode = "QUATERNION"
        obj.rotation_quaternion = Quaternion(self.orientation)
        obj.kb.restrot = self.orientation
        obj.scale = (self.scale, self.scale, self.scale)
        obj.location = self.position
        obj.kb.restloc = obj.location
        obj.kb.wirecolor = self.wirecolor
        # add unprocessed data as text objects
        if len(self.rawascii):
            txt: bpy.types.Text = bpy.data.texts.new(obj.name)
            txt.write(self.rawascii)
            obj.kb.rawascii = txt.name

    def add_to_collection(self, collection: bpy.types.Collection) -> bpy.types.Object:
        obj: bpy.types.Object = bpy.data.objects.new(self.name, None)
        self.set_object_data(obj)
        collection.objects.link(obj)
        return obj

    def get_adjusted_matrix(self, obj: bpy.types.Object) -> Matrix:
        if obj.parent:
            parent_mw: Matrix = obj.parent.matrix_world
        else:
            parent_mw: Matrix = Matrix()

        p_mw_scale: Vector = parent_mw.to_scale()

        scaled: Matrix = obj.matrix_local.copy()
        scaled[0][3] = scaled[0][3] * p_mw_scale[0]
        scaled[1][3] = scaled[1][3] * p_mw_scale[1]
        scaled[2][3] = scaled[2][3] * p_mw_scale[2]
        return scaled

    def add_data_to_ascii(
        self,
        obj: bpy.types.Object,
        ascii_lines: list[str],
        classification: str = defines.Classification.UNKNOWN,
        simple: bool = False,
        name_dict: Dict[str, str] | None = None,
    ) -> None:
        if obj.parent and name_dict and obj.parent.name in name_dict:
            ascii_lines.append("  parent " + name_dict[obj.parent.name])
        elif obj.parent:
            ascii_lines.append("  parent " + obj.parent.name)
        else:
            ascii_lines.append("  parent " + defines.null)
        # Scaling fix
        transmat: Matrix = self.get_adjusted_matrix(obj)
        loc: Vector = transmat.to_translation()
        s: str = f"  position {round(loc[0], 7): .7g} {round(loc[1], 7): .7g} {round(loc[2], 7): .7g}"
        ascii_lines.append(s)

        rot: tuple[float, float, float, float] = utils.get_aurora_rot_from_object(obj)
        s = f"  orientation {round(rot[0], 7): .7g} {round(rot[1], 7): .7g} {round(rot[2], 7): .7g} {round(rot[3], 7): .7g}"
        ascii_lines.append(s)

        color: tuple[float, float, float] = obj.kb.wirecolor
        ascii_lines.append("  wirecolor " + str(round(color[0], 2)) + " " + str(round(color[1], 2)) + " " + str(round(color[2], 2)))
        scale: float = round(utils.get_aurora_scale(obj), 3)
        if scale != 1.0:
            ascii_lines.append("  scale " + str(scale))

        # Write out the unprocessed data
        if obj.kb.rawascii and obj.kb.rawascii in bpy.data.texts:
            ascii_lines.append("  " + "\n  ".join(bpy.data.texts[obj.kb.rawascii].as_string().strip().split("\n")))

    def to_ascii(
        self,
        obj: bpy.types.Object,
        ascii_lines: list[str],
        classification: str = defines.Classification.UNKNOWN,
        simple: bool = False,
        name_dict: Dict[str, str] | None = None,
    ) -> None:
        if name_dict and obj.name in name_dict:
            ascii_lines.append("node " + self.nodetype + " " + name_dict[obj.name])
        else:
            ascii_lines.append("node " + self.nodetype + " " + obj.name)
        self.add_data_to_ascii(obj, ascii_lines, classification, simple, name_dict=name_dict)
        ascii_lines.append("endnode")

    def add_unparsed_to_raw(self, ascii_node: list[list[str]]) -> None:
        for idx, line in enumerate(ascii_node):
            if idx in self.parsed_lines or not len("".join(line).strip()):
                continue
            self.rawascii += "\n" + " ".join(line)


class Dummy(GeometryNode):
    def __init__(self, name: str = "UNNAMED") -> None:
        GeometryNode.__init__(self, name)
        self.nodetype: str = "dummy"

        self.dummytype: str = defines.Dummytype.NONE

    def load_ascii(self, ascii_node: list[list[str]]) -> None:
        GeometryNode.load_ascii(self, ascii_node)

    def set_object_data(self, obj: bpy.types.Object) -> None:
        GeometryNode.set_object_data(self, obj)

        obj.kb.dummytype = self.dummytype

        obj.kb.dummysubtype = defines.DummySubtype.NONE
        subtypes: list[tuple[str, str]] = defines.DummySubtype.SUFFIX_LIST
        for element in subtypes:
            if self.name.endswith(element[0]):
                obj.kb.dummysubtype = element[1]
                break

    def add_data_to_ascii(
        self,
        obj: bpy.types.Object,
        ascii_lines: list[str],
        classification: str = defines.Classification.UNKNOWN,
        simple: bool = False,
        name_dict: Dict[str, str] | None = None,
    ) -> None:
        if obj.parent and name_dict and obj.parent.name in name_dict:
            ascii_lines.append("  parent " + name_dict[obj.parent.name])
        elif obj.parent:
            ascii_lines.append("  parent " + obj.parent.name)
        else:
            ascii_lines.append("  parent " + defines.null)

        dummytype: str = obj.kb.dummytype
        if dummytype == defines.Dummytype.MDLROOT:
            # Only parent for rootdummys
            return

        # scale = round(utils.get_aurora_scale(obj), 3)
        # Scaling fix
        ascii_lines.append("  scale 1.0")

        # Scaling fix
        transmat: Matrix = self.get_adjusted_matrix(obj)
        loc: Vector = transmat.to_translation()
        s: str = f"  position {round(loc[0], 7): .7g} {round(loc[1], 7): .7g} {round(loc[2], 7): .7g}"
        ascii_lines.append(s)

        rot: tuple[float, float, float, float] = utils.quat2nwangle(transmat.to_quaternion())
        s = f"  orientation {round(rot[0], 7): .7g} {round(rot[1], 7): .7g} {round(rot[2], 7): .7g} {round(rot[3], 7): .7g}"
        ascii_lines.append(s)

        color: tuple[float, float, float] = obj.kb.wirecolor
        ascii_lines.append("  wirecolor " + str(round(color[0], 2)) + " " + str(round(color[1], 2)) + " " + str(round(color[2], 2)))

        # TODO: Handle types and subtypes, i.e. Check and modify name
        subtype: str = obj.kb.dummysubtype
        if subtype == defines.Dummytype.NONE:
            pass


class Reference(GeometryNode):
    """Contains a reference to another mdl."""

    def __init__(self, name: str = "UNNAMED") -> None:
        GeometryNode.__init__(self, name)
        self.nodetype: str = "reference"

        self.dummytype: str = defines.Dummytype.REFERENCE
        self.refmodel: str = defines.null
        self.reattachable: int = 0

    def load_ascii(self, ascii_node: list[list[str]]) -> None:
        GeometryNode.load_ascii(self, ascii_node)
        l_is_number: Callable[[str], bool] = utils.is_number

        for idx, line in enumerate(ascii_node):
            try:
                label: str = line[0].lower()
            except IndexError:
                # Probably empty line or whatever, skip it
                continue
            if not l_is_number(label):
                if label == "refmodel":
                    # self.refmodel = line[1].lower()
                    self.refmodel = line[1]
                    self.parsed_lines.append(idx)
                elif label == "reattachable":
                    self.reattachable = int(line[1])
                    self.parsed_lines.append(idx)
        if self.nodetype == "reference":
            self.add_unparsed_to_raw(ascii_node)

    def set_object_data(self, obj: bpy.types.Object) -> None:
        GeometryNode.set_object_data(self, obj)
        obj.kb.dummytype = self.dummytype
        obj.kb.refmodel = self.refmodel
        obj.kb.reattachable = self.reattachable == 1

    def add_data_to_ascii(
        self,
        obj: bpy.types.Object,
        ascii_lines: list[str],
        classification: str = defines.Classification.UNKNOWN,
        simple: bool = False,
        name_dict: Dict[str, str] | None = None,
    ) -> None:
        GeometryNode.add_data_to_ascii(self, obj, ascii_lines, classification, name_dict=name_dict)
        ascii_lines.append("  refmodel " + obj.kb.refmodel)
        ascii_lines.append("  reattachable " + str(int(obj.kb.reattachable)))


class Trimesh(GeometryNode):
    def __init__(self, name: str = "UNNAMED") -> None:
        GeometryNode.__init__(self, name)
        self.nodetype: str = "trimesh"

        self.meshtype: str = defines.Meshtype.TRIMESH
        self.center: tuple[float, float, float] = (0.0, 0.0, 0.0)  # Unused ?
        self.lightmapped: int = 0
        self.render: int = 1
        self.shadow: int = 1
        self.beaming: int = 0
        self.inheritcolor: int = 0  # Unused ?
        self.m_bIsBackgroundGeometry: int = 0
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
        self.ambient: tuple[float, float, float] = (0.0, 0.0, 0.0)
        self.diffuse: tuple[float, float, float] = (0.0, 0.0, 0.0)
        self.bitmap: str = defines.null
        self.bitmap2: str = defines.null
        self.tangentspace: int = 0
        self.rotatetexture: int = 0
        self.verts: list[tuple[float, float, float]] = []  # list of vertices
        self.facelist: FaceList = FaceList()
        self.tverts: list[tuple[float, float]] = []  # list of texture vertices
        self.tverts1: list[tuple[float, float]] = []  # list of texture vertices
        self.texindices1: list[int] = []  # list of texture vertex indices
        self.roomlinks: list[int] = []  # walkmesh only
        self.lytposition: tuple[float, float, float] = (0.0, 0.0, 0.0)

    def load_ascii(self, ascii_node):
        GeometryNode.load_ascii(self, ascii_node)

        l_float = float
        l_is_number = utils.is_number
        for idx, line in enumerate(ascii_node):
            try:
                label = line[0].lower()
            except IndexError:
                # Probably empty line or whatever, skip it
                continue

            if not l_is_number(label):
                if label == "render":
                    self.render = int(line[1])
                    self.parsed_lines.append(idx)
                elif label == "shadow":
                    self.shadow = int(line[1])
                    self.parsed_lines.append(idx)
                elif label == "lightmapped":
                    self.lightmapped = int(line[1])
                    self.parsed_lines.append(idx)
                elif label == "beaming":
                    self.beaming = int(line[1])
                    self.parsed_lines.append(idx)
                elif label == "inheritcolor ":
                    self.inheritcolor = int(line[1])
                    self.parsed_lines.append(idx)
                elif label == "tangentspace":
                    self.tangentspace = int(line[1])
                    self.parsed_lines.append(idx)
                elif label == "rotatetexture":
                    self.rotatetexture = int(line[1])
                    self.parsed_lines.append(idx)
                elif label == "m_bisbackgroundgeometry":
                    self.m_bIsBackgroundGeometry = int(line[1])
                    self.parsed_lines.append(idx)
                elif label == "dirt_enabled":
                    self.dirt_enabled = int(line[1])
                    self.parsed_lines.append(idx)
                elif label == "dirt_texture":
                    self.dirt_texture = int(line[1])
                    self.parsed_lines.append(idx)
                elif label == "dirt_worldspace":
                    self.dirt_worldspace = int(line[1])
                    self.parsed_lines.append(idx)
                elif label == "hologram_donotdraw":
                    self.hologram_donotdraw = int(line[1])
                    self.parsed_lines.append(idx)
                elif label == "animateuv":
                    self.animateuv = int(line[1])
                    self.parsed_lines.append(idx)
                elif label == "uvdirectionx":
                    self.uvdirectionx = l_float(line[1])
                    self.parsed_lines.append(idx)
                elif label == "uvdirectiony":
                    self.uvdirectiony = l_float(line[1])
                    self.parsed_lines.append(idx)
                elif label == "uvjitter":
                    self.uvjitter = l_float(line[1])
                    self.parsed_lines.append(idx)
                elif label == "uvjitterspeed":
                    self.uvjitterspeed = l_float(line[1])
                    self.parsed_lines.append(idx)
                elif label == "alpha":
                    self.alpha = l_float(line[1])
                    self.parsed_lines.append(idx)
                elif label == "transparencyhint":
                    self.transparencyhint = int(line[1])
                    self.parsed_lines.append(idx)
                elif label == "selfillumcolor":  # Self illumination color
                    self.selfillumcolor = (l_float(line[1]), l_float(line[2]), l_float(line[3]))
                    self.parsed_lines.append(idx)
                elif label == "ambient":
                    self.ambient = (l_float(line[1]), l_float(line[2]), l_float(line[3]))
                    self.parsed_lines.append(idx)
                elif label == "diffuse":
                    self.diffuse = (l_float(line[1]), l_float(line[2]), l_float(line[3]))
                    self.parsed_lines.append(idx)
                elif label == "center":
                    # Unused ? Becuase we don't do anything with this
                    try:
                        self.center = (l_float(line[1]), l_float(line[2]), l_float(line[3]))
                        self.parsed_lines.append(idx)
                    except Exception:  # noqa: BLE001
                        RobustLogger().debug('Probably an "undefined" string which cannot be converted to float', exc_info=True)
                elif label == "bitmap":
                    self.bitmap = line[1].lower()
                    self.parsed_lines.append(idx)
                elif label == "bitmap2":
                    self.bitmap2 = line[1].lower()
                    self.parsed_lines.append(idx)
                elif label == "verts":
                    numVals = int(line[1])
                    parse.f3(ascii_node[idx + 1 : idx + numVals + 1], self.verts)
                    self.parsed_lines.extend(range(idx, idx + numVals + 1))
                elif label == "faces":
                    numVals = int(line[1])
                    self.parse_face_list(ascii_node[idx + 1 : idx + numVals + 1])
                    self.parsed_lines.extend(range(idx, idx + numVals + 1))
                elif label == "tverts":
                    numVals = int(line[1])
                    parse.f2(ascii_node[idx + 1 : idx + numVals + 1], self.tverts)
                    self.parsed_lines.extend(range(idx, idx + numVals + 1))
                elif label == "tverts1":
                    numVals = int(line[1])
                    parse.f2(ascii_node[idx + 1 : idx + numVals + 1], self.tverts1)
                    self.parsed_lines.extend(range(idx, idx + numVals + 1))
                elif label == "texindices1":
                    numVals = int(line[1])
                    parse.i3(ascii_node[idx + 1 : idx + numVals + 1], self.texindices1, initial_float=False)
                    self.parsed_lines.extend(range(idx, idx + numVals + 1))
                elif label == "roomlinks":
                    try:
                        numVals = int(line[1])
                    except Exception:  # noqa: BLE001
                        numVals = next((i for i, v in enumerate(ascii_node[idx + 1 :]) if not l_is_number(v[0])), -1)
                    parse.i2(ascii_node[idx + 1 : idx + numVals + 1], self.roomlinks)
                    self.parsed_lines.extend(range(idx, idx + numVals + 1))
        if self.nodetype == "trimesh":
            self.add_unparsed_to_raw(ascii_node)

    def parse_face_list(self, ascii_faces: list[list[str]]):
        for line in ascii_faces:
            self.facelist.faces.append((int(line[0]), int(line[1]), int(line[2])))
            self.facelist.shdgr.append(int(line[3]))
            self.facelist.uvIdx.append((int(line[4]), int(line[5]), int(line[6])))
            self.facelist.matId.append(int(line[7]))

    def create_mesh(self, name: str) -> bpy.types.Mesh:
        # Create the mesh itself
        mesh = bpy.data.meshes.new(name)
        mesh.vertices.add(len(self.verts))
        mesh.vertices.foreach_set("co", unpack_list(self.verts))
        num_faces = len(self.facelist.faces)
        mesh.loops.add(3 * num_faces)
        mesh.loops.foreach_set("vertex_index", unpack_list(self.facelist.faces))
        mesh.polygons.add(num_faces)
        mesh.polygons.foreach_set("loop_start", range(0, 3 * num_faces, 3))
        mesh.polygons.foreach_set("loop_total", (3,) * num_faces)

        # Special handling for mesh in walkmesh files
        if self.roottype in ("pwk", "dwk", "wok"):
            # Create walkmesh materials
            for wokMat in defines.wok_materials:
                matName = wokMat[0]
                # Walkmesh materials will be shared across multiple walkmesh
                # objects
                if matName in bpy.data.materials:
                    material = bpy.data.materials[matName]
                else:
                    material = bpy.data.materials.new(matName)
                    material.diffuse_color = [*wokMat[1], 1.0]
                    material.specular_color = (0.0, 0.0, 0.0)
                    material.specular_intensity = wokMat[2]
                mesh.materials.append(material)

            # Apply the walkmesh materials to each face
            for idx, polygon in enumerate(mesh.polygons):
                polygon.material_index = self.facelist.matId[idx]

        # Create UV map
        if len(self.tverts) > 0:
            uv = unpack_list([self.tverts[i] for indices in self.facelist.uvIdx for i in indices])
            uv_layer = mesh.uv_layers.new(name="UVMap", do_init=False)
            uv_layer.data.foreach_set("uv", uv)

        # Create lightmap UV map
        if len(self.tverts1) > 0:
            if len(self.texindices1) > 0:
                uv = unpack_list([self.tverts1[i] for indices in self.texindices1 for i in indices])
            else:
                uv = unpack_list([self.tverts1[i] for indices in self.facelist.uvIdx for i in indices])

            uv_layer = mesh.uv_layers.new(name="UVMap_lm", do_init=False)
            uv_layer.data.foreach_set("uv", uv)

        # Import smooth groups as sharp edges
        if glob.importSmoothGroups:
            bm = bmesh.new()
            mesh.update()
            bm.from_mesh(mesh)
            if hasattr(bm.edges, "ensure_lookup_table"):
                bm.edges.ensure_lookup_table()
            # Mark edge as sharp if its faces belong to different smooth groups
            for e in bm.edges:
                f = e.link_faces
                if (len(f) > 1) and not (self.facelist.shdgr[f[0].index] & self.facelist.shdgr[f[1].index]):
                    edgeIdx = e.index
                    mesh.edges[edgeIdx].use_edge_sharp = True
            bm.free()
            del bm
            mesh.update()
            # load all smoothgroup numbers into a mesh data layer per-poly
            mesh_sg_list = mesh.polygon_layers_int.new(name=defines.sg_layer_name)
            mesh_sg_list.data.foreach_set("value", self.facelist.shdgr)

        if self.roottype == "wok" and len(self.roomlinks):
            self.set_room_links(mesh)

        mesh.update()
        return mesh

    def set_room_links(
        self,
        mesh: bpy.types.Mesh,
        skip_non_walkable: bool = True,
    ):
        if "RoomLinks" not in mesh.vertex_colors:
            room_vert_colors = mesh.vertex_colors.new(name="RoomLinks")
        else:
            room_vert_colors = mesh.vertex_colors["RoomLinks"]
        for link in self.roomlinks:
            # edge indices don't really match up, but face order does
            faceIdx = int(link[0] / 3)
            edgeIdx = link[0] % 3
            room_color = [0.0 / 255, (200 + link[1]) / 255.0, 0.0 / 255]
            realIdx = 0
            for face_idx, face in enumerate(mesh.polygons):
                if skip_non_walkable and (face.material_index not in defines.WkmMaterial.NONWALKABLE):
                    if realIdx == faceIdx:
                        faceIdx = face_idx
                        break
                    realIdx += 1
            face = mesh.polygons[faceIdx]
            for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                if vert_idx in face.edge_keys[edgeIdx]:
                    room_vert_colors.data[loop_idx].color = [*room_color, 1.0]

    def get_room_links(self, mesh: bpy.types.Mesh):
        """Construct list of room links from vertex colors, for wok files."""
        if "RoomLinks" not in mesh.vertex_colors:
            return
        room_vert_colors = mesh.vertex_colors["RoomLinks"]
        self.roomlinks = []
        face_bonus = 0
        for face_idx, face in enumerate(mesh.polygons):
            verts = {}
            # when the wok is compiled, these faces will be sorted past
            # the walkable faces, so take the index delta into account
            if self.nodetype != "aabb" and face.material_index in defines.WkmMaterial.NONWALKABLE:
                face_bonus -= 1
                continue
            for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                room = int(round(room_vert_colors.data[loop_idx].color[1] * 255, 0)) - 200
                # we use color space for links to 55 rooms,
                # which is likely more than the game could handle
                if room < 0 or room > 54:
                    continue
                verts[vert_idx] = room
            if len(verts) < 2:
                continue
            vertIndices = list(verts.keys())
            for edge_idx, edge in enumerate(face.edge_keys):
                if vertIndices[0] in edge and vertIndices[1] in edge:
                    self.roomlinks.append(((face_idx + face_bonus) * 3 + edge_idx, verts[vertIndices[0]]))

    def set_object_data(self, obj: bpy.types.Object):
        GeometryNode.set_object_data(self, obj)

        obj.kb.meshtype = self.meshtype
        obj.kb.bitmap = self.bitmap if not utils.is_null(self.bitmap) else ""
        obj.kb.bitmap2 = self.bitmap2 if not utils.is_null(self.bitmap2) else ""
        obj.kb.alpha = self.alpha
        obj.kb.lightmapped = self.lightmapped == 1
        obj.kb.render = self.render == 1
        obj.kb.shadow = self.shadow == 1
        obj.kb.beaming = self.beaming == 1
        obj.kb.tangentspace = self.tangentspace == 1
        obj.kb.inheritcolor = self.inheritcolor == 1
        obj.kb.rotatetexture = self.rotatetexture == 1
        obj.kb.m_bIsBackgroundGeometry = self.m_bIsBackgroundGeometry == 1
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
        obj.kb.lytposition = self.lytposition

    def add_to_collection(self, collection: bpy.types.Collection):
        mesh = self.create_mesh(self.name)
        obj = bpy.data.objects.new(self.name, mesh)
        self.set_object_data(obj)

        if glob.importMaterials and self.roottype == "mdl":
            material.rebuild_material(obj)

        collection.objects.link(obj)
        return obj

    def add_material_data_to_ascii(self, obj: bpy.types.Object, ascii_lines: list[str]):
        ascii_lines.append("  alpha " + str(round(obj.kb.alpha, 2)))

        ascii_lines.append(f"  diffuse {obj.kb.diffuse[0]:.2f} {obj.kb.diffuse[1]:.2f} {obj.kb.diffuse[2]:.2f}")

        tangentspace = 1 if obj.kb.tangentspace else 0
        ascii_lines.append("  tangentspace " + str(tangentspace))

        imgName = obj.kb.bitmap if obj.kb.bitmap else defines.null
        ascii_lines.append("  bitmap " + imgName)

        imgName = obj.kb.bitmap2 if obj.kb.bitmap2 else defines.null
        ascii_lines.append("  bitmap2 " + imgName)

    def add_uv_to_list(
        self,
        uv: list[float],
        uv_list: list[list[float]],
        vert: int,
        vert_list: list[int],
    ) -> int:
        """Helper function to keep UVs unique."""
        if uv in uv_list and vert in vert_list:
            return uv_list.index(uv)
        uv_list.append(uv)
        vert_list.append(vert)
        return len(uv_list) - 1

    def get_export_mesh(self, obj: bpy.types.Object):
        """Get the export mesh for an object,
        This mesh has modifiers applied as requested.
        TODO: retain the mesh across contexts instead of recreating every time.
        """
        if obj is None:
            return None

        if glob.applyModifiers:
            depsgraph = bpy.context.evaluated_depsgraph_get()
            obj_eval = obj.evaluated_get(depsgraph)
            mesh = obj_eval.to_mesh()
        else:
            mesh = obj.to_mesh()

        mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))

        # Triangulation (doing it with bmesh to retain edges marked as sharp)
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.to_mesh(mesh)
        bm.free()

        return mesh

    def add_mesh_data_to_ascii(
        self,
        obj: bpy.types.Object,
        ascii_lines: list[str],
        simple: bool = False,
    ):
        mesh = self.get_export_mesh(obj)

        # Calculate smooth groups
        smoothGroups = []
        numSmoothGroups = 0
        if (obj.kb.smoothgroup == "SEPR") or (not glob.exportSmoothGroups):
            # 0 = Do not use smoothgroups
            smoothGroups = [0] * len(mesh.polygons)
            numSmoothGroups = 1
        elif obj.kb.smoothgroup == "SING":
            # All faces belong to smooth group 1
            smoothGroups = [1] * len(mesh.polygons)
            numSmoothGroups = 1
        else:
            (smoothGroups, numSmoothGroups) = mesh.calc_smooth_groups(use_bitflags=True)

        faceList: list[list[int]] = []  # List of triangle faces
        uvList: list[list[float]] = []  # List of uv indices
        uvVertList: list[list[float]] = []  # Temp list of uv verts used for each geometry vert
        # separate lists for the lightmap UVs if they exist
        uvListLM: list[list[float]] = []  # List of uv indices
        uvVertListLM: list[list[float]] = []  # Temp list of uv verts used for each geometry vert

        abs_pos = (0.0, 0.0, 0.0)
        if self.roottype == "wok" and obj.kb.lytposition:
            abs_pos = (
                obj.kb.lytposition[0] + obj.location[0],
                obj.kb.lytposition[1] + obj.location[1],
                obj.kb.lytposition[2] + obj.location[2],
            )
        # Add vertices
        ascii_lines.append("  verts " + str(len(mesh.vertices)))
        l_round = round
        for v in mesh.vertices:
            s = f"    {l_round(v.co[0] + abs_pos[0], 7): .7g} {l_round(v.co[1] + abs_pos[1], 7): .7g} {l_round(v.co[2] + abs_pos[2], 7): .7g}"
            ascii_lines.append(s)

        # Add faces and corresponding tverts and shading groups
        smgroups_layer = mesh.polygon_layers_int.get(defines.sg_layer_name)

        uv_layer = None
        uv_layer_lm = None
        if len(mesh.uv_layers) > 0:
            # AABB nodes only have lightmap UV
            if mesh.uv_layers[0].name.endswith("_lm"):
                uv_layer_lm = mesh.uv_layers[0]
            else:
                uv_layer = mesh.uv_layers[0]
        if uv_layer_lm is None and len(mesh.uv_layers) > 1:
            uv_layer_lm = mesh.uv_layers[1]

        for i in range(len(mesh.polygons)):
            polygon = mesh.polygons[i]
            smGroup = smoothGroups[i]
            if obj.kb.smoothgroup == "DRCT" and smgroups_layer is not None and smgroups_layer.data[i].value != 0:
                smGroup = smgroups_layer.data[i].value
            if uv_layer:
                uv1 = self.add_uv_to_list(uv_layer.data[3 * i + 0].uv, uvList, polygon.vertices[0], uvVertList)
                uv2 = self.add_uv_to_list(uv_layer.data[3 * i + 1].uv, uvList, polygon.vertices[1], uvVertList)
                uv3 = self.add_uv_to_list(uv_layer.data[3 * i + 2].uv, uvList, polygon.vertices[2], uvVertList)
            else:
                uv1 = 0
                uv2 = 0
                uv3 = 0
            matIdx = polygon.material_index
            if uv_layer_lm:
                uv1LM = self.add_uv_to_list(uv_layer_lm.data[3 * i + 0].uv, uvListLM, polygon.vertices[0], uvVertListLM)
                uv2LM = self.add_uv_to_list(uv_layer_lm.data[3 * i + 1].uv, uvListLM, polygon.vertices[1], uvVertListLM)
                uv3LM = self.add_uv_to_list(uv_layer_lm.data[3 * i + 2].uv, uvListLM, polygon.vertices[2], uvVertListLM)
            else:
                uv1LM = 0
                uv2LM = 0
                uv3LM = 0
            faceList.append([*polygon.vertices[:3], smGroup, uv1, uv2, uv3, matIdx, uv1LM, uv2LM, uv3LM])

        # Check a texture, we don't want uv's when there is no texture
        if simple or len(uvList) < 1:
            ascii_lines.append("  faces " + str(len(faceList)))

            vertDigits = str(len(str(len(mesh.vertices))))
            smoothGroupDigits = str(len(str(numSmoothGroups)))
            formatString = "    {:" + vertDigits + "d} {:" + vertDigits + "d} {:" + vertDigits + "d}  " + "{:" + smoothGroupDigits + "d}  " + "0 0 0  " + "{:2d}"
            for f in faceList:
                s = formatString.format(f[0], f[1], f[2], f[3], f[7])
                ascii_lines.append(s)
        else:
            ascii_lines.append("  faces " + str(len(faceList)))

            vertDigits = str(len(str(len(mesh.vertices))))
            smoothGroupDigits = str(len(str(numSmoothGroups)))
            uvDigits = str(len(str(len(uvList))))
            formatString = f"    {{:{vertDigits}d}} {{:{vertDigits}d}} {{:{vertDigits}d}}  {{:{smoothGroupDigits}d}}  {{:{uvDigits}d}} {{:{uvDigits}d}} {{:{uvDigits}d}}  {{:2d}}"
            for f in faceList:
                s = formatString.format(f[0], f[1], f[2], f[3], f[4], f[5], f[6], f[7])
                ascii_lines.append(s)

            if len(uvList) > 0:
                ascii_lines.append("  tverts " + str(len(uvList)))
                formatString = "    {: .7g} {: .7g}"
                for uv in uvList:
                    s = formatString.format(round(uv[0], 7), round(uv[1], 7))
                    ascii_lines.append(s)

            if len(uvListLM) > 0:
                ascii_lines.append("  tverts1 " + str(len(uvListLM)))
                formatString = "    {: .7g} {: .7g} 0"
                for uv in uvListLM:
                    s = formatString.format(round(uv[0], 7), round(uv[1], 7))
                    ascii_lines.append(s)
                ascii_lines.append("  texindices1 " + str(len(faceList)))
                formatString = "    {:3d} {:3d} {:3d}"
                for f in faceList:
                    ascii_lines.append(formatString.format(f[8], f[9], f[10]))

            if (
                len(mesh.vertex_colors.keys())
                and (
                    "RoomLinks" not in mesh.vertex_colors
                    or len(mesh.vertex_colors.keys()) > 1
                )
            ):
                # get dict key for first vertex color layer that is not RoomLinks
                colorKey = next(k for k in mesh.vertex_colors if k != "RoomLinks")
                # insert the vertex colors
                ascii_lines.append(f"  colors {len(mesh.vertices)}")
                formatString = "    {: .7g} {: .7g} {: .7g}"
                for face in mesh.polygons:
                    for loop_idx in face.loop_indices:
                        s = formatString.format(
                            mesh.vertex_colors[colorKey].data[loop_idx].color[0],
                            mesh.vertex_colors[colorKey].data[loop_idx].color[1],
                            mesh.vertex_colors[colorKey].data[loop_idx].color[2],
                        )
                        ascii_lines.append(s)
                # insert vertex color indices
                ascii_lines.append(f"  colorindices {len(faceList)}")
                for f in faceList:
                    s = f"    {f[0]} {f[1]} {f[2]}"
                    ascii_lines.append(s)
        if self.roottype == "wok" or self.nodetype == "aabb":
            if self.nodetype == "aabb":
                self.get_room_links(mesh)
            if self.roomlinks:
                ascii_lines.append(f"  roomlinks {len(self.roomlinks)}")
                ascii_lines.extend([f"    {link[0]:d} {link[1]:d}" for link in self.roomlinks])

    def add_data_to_ascii(
        self,
        obj: bpy.types.Object,
        ascii_lines: list[str],
        classification: defines.Classification = defines.Classification.UNKNOWN,
        simple: bool = False,
        name_dict: dict[str, str] | None = None,
    ):
        GeometryNode.add_data_to_ascii(self, obj, ascii_lines, classification, simple, name_dict=name_dict)

        color = obj.kb.ambient
        ascii_lines.append(f"  ambient {color[0]:.2f} {color[1]:.2f} {color[2]:.2f}")
        self.add_material_data_to_ascii(obj, ascii_lines)
        if not simple:
            color = obj.kb.selfillumcolor
            ascii_lines.append(f"  selfillumcolor {color[0]:.2f} {color[1]:.2f} {color[2]:.2f}")

            ascii_lines.append(f"  render {int(obj.kb.render)}")
            ascii_lines.append(f"  shadow {int(obj.kb.shadow)}")
            ascii_lines.append(f"  lightmapped {int(obj.kb.lightmapped)}")
            ascii_lines.append(f"  beaming {int(obj.kb.beaming)}")
            ascii_lines.append(f"  inheritcolor {int(obj.kb.inheritcolor)}")
            ascii_lines.append(f"  m_bIsBackgroundGeometry {int(obj.kb.m_bIsBackgroundGeometry)}")
            ascii_lines.append(f"  dirt_enabled {int(obj.kb.dirt_enabled)}")
            ascii_lines.append(f"  dirt_texture {obj.kb.dirt_texture}")
            ascii_lines.append(f"  dirt_worldspace {obj.kb.dirt_worldspace}")
            ascii_lines.append(f"  hologram_donotdraw {int(obj.kb.hologram_donotdraw)}")
            ascii_lines.append(f"  animateuv {int(obj.kb.animateuv)}")
            ascii_lines.append(f"  uvdirectionx {obj.kb.uvdirectionx}")
            ascii_lines.append(f"  uvdirectiony {obj.kb.uvdirectiony}")
            ascii_lines.append(f"  uvjitter {obj.kb.uvjitter}")
            ascii_lines.append(f"  uvjitterspeed {obj.kb.uvjitterspeed}")
            ascii_lines.append(f"  transparencyhint {obj.kb.transparencyhint}")
            # These two are for tiles only
            if classification == "TILE":
                ascii_lines.append(f"  rotatetexture {int(obj.kb.rotatetexture)}")

        self.add_mesh_data_to_ascii(obj, ascii_lines, simple)


class Danglymesh(Trimesh):
    nodetype: ClassVar[NodeType | Literal["DANGLYMESH"]] = NodeType.DANGLYMESH
    meshtype: ClassVar[MeshType | Literal["DANGLYMESH"]] = MeshType.DANGLYMESH

    def __init__(self, name: str = "UNNAMED"):
        super().__init__(name)
        self.period: float = 1.0
        self.tightness: float = 1.0
        self.displacement: float = 1.0
        self.constraints: list[int] = []

    def load_ascii(self, ascii_node: list[list[str]]):
        super().load_ascii(ascii_node)

        l_float = float
        l_is_number = utils.is_number
        for idx, line in enumerate(ascii_node):
            try:
                label = line[0].lower()
            except IndexError:  # noqa: S112
                RobustLogger().debug("Probably empty line or whatever, skip it", stack_info=True)

            if not l_is_number(label):
                if label == "period":
                    self.period = l_float(line[1])
                    self.parsed_lines.append(idx)
                elif label == "tightness":
                    self.tightness = l_float(line[1])
                    self.parsed_lines.append(idx)
                elif label == "displacement":
                    self.displacement = l_float(line[1])
                    self.parsed_lines.append(idx)
                elif label == "constraints":
                    numVals = int(line[1])
                    parse.f1(ascii_node[idx + 1 : idx + numVals + 1], self.constraints)
                    self.parsed_lines.extend(range(idx, idx + numVals + 1))
        if self.nodetype == "danglymesh":
            self.add_unparsed_to_raw(ascii_node)

    def add_constraints_to_object(self, obj: bpy.types.Object):
        """Creates a vertex group for the object to contain the vertex
        weights for the danglymesh. The weights are called "constraints"
        in NWN. Range is [0.0, 255.0] as opposed to [0.0, 1.0] in Blender.
        """
        vgroup = obj.vertex_groups.new(name="constraints")
        for vertexIdx, constraint in enumerate(self.constraints):
            weight = constraint / 255
            vgroup.add([vertexIdx], weight, "REPLACE")
        obj.kb.constraints = vgroup.name

    def set_object_data(self, obj: bpy.types.Object):
        Trimesh.set_object_data(self, obj)

        obj.kb.period = self.period
        obj.kb.tightness = self.tightness
        obj.kb.displacement = self.displacement
        self.add_constraints_to_object(obj)

    def add_constraints_to_ascii(self, obj: bpy.types.Object, ascii_lines: list[str]):
        vgroupName = obj.kb.constraints
        vgroup = obj.vertex_groups[vgroupName]

        mesh = self.get_export_mesh(obj)

        ascii_lines.append(f"  constraints {len(mesh.vertices)}")
        for v in mesh.vertices:
            # In case vertex is not weighted with dangly constraint
            weight = 0.0
            for vg in v.groups:
                if vg.group != vgroup.index:
                    continue
                weight = round(vg.weight * 255, 3)
            ascii_lines.append(f"    {weight}")

    def add_data_to_ascii(
        self,
        obj: bpy.types.Object,
        ascii_lines: list[str],
        classification: defines.Classification = defines.Classification.UNKNOWN,
        simple: bool = False,
        name_dict: dict[str, str] | None = None,
    ):
        Trimesh.add_data_to_ascii(self, obj, ascii_lines, classification, name_dict=name_dict)

        ascii_lines.append("  period " + str(round(obj.kb.period, 3)))
        ascii_lines.append("  tightness " + str(round(obj.kb.tightness, 3)))
        ascii_lines.append("  displacement " + str(round(obj.kb.displacement, 3)))
        self.add_constraints_to_ascii(obj, ascii_lines)


class Lightsaber(Trimesh):
    nodetype: ClassVar[NodeType | Literal["LIGHTSABER"]] = NodeType.LIGHTSABER
    meshtype: ClassVar[MeshType | Literal["LIGHTSABER"]] = MeshType.LIGHTSABER

    def __init__(self, name: str = "UNNAMED"):
        super().__init__(name)

    def create_mesh(self, name: str) -> bpy.types.Mesh:
        """Create the mesh itself."""
        mesh = super().create_mesh(name)
        return mesh


class Skinmesh(Trimesh):
    """Skinmeshes are Trimeshes where every vertex has a weight."""

    nodetype: ClassVar[NodeType | Literal["SKIN"]] = NodeType.SKIN
    meshtype: ClassVar[MeshType | Literal["SKIN"]] = MeshType.SKIN

    def __init__(self, name: str = "UNNAMED"):
        super().__init__(name)
        self.weights: list[list[list[str | float]]] = []

    def load_ascii(self, ascii_node: list[list[str]]):
        Trimesh.load_ascii(self, ascii_node)
        l_is_number = utils.is_number
        for idx, line in enumerate(ascii_node):
            try:
                label = line[0].lower()
            except IndexError:  # noqa: S112
                RobustLogger().debug("Probably empty line or whatever, skip it", stack_info=True)

            if not l_is_number(label) and label == "weights":
                numVals = int(line[1])
                self.get_weights_from_ascii(ascii_node[idx + 1 : idx + numVals + 1])
                self.parsed_lines.extend(range(idx, idx + numVals + 1))
                break  # Only one value here, abort loop when read
        if self.nodetype == NodeType.SKIN:
            self.add_unparsed_to_raw(ascii_node)

    def get_weights_from_ascii(self, ascii_block: list[list[str]]):
        lfloat = float
        lchunker = utils.chunker
        for line in ascii_block:
            # A line looks like this
            # [group_name, vertex_weight, group_name, vertex_weight]
            # We create a list looking like this:
            # [[group_name, vertex_weight], [group_name, vertex_weight]]
            memberships: list[list[str | float]] = [[chunk[0], lfloat(chunk[1])] for chunk in lchunker(line, 2)]
            self.weights.append(memberships)

    def add_skin_groups_to_object(self, obj: bpy.types.Object):
        skinGroupDict: dict[str, bpy.types.VertexGroup] = {}
        for vertIdx, vertMemberships in enumerate(self.weights):
            for membership in vertMemberships:
                if membership[0] in skinGroupDict:
                    skinGroupDict[membership[0]].add([vertIdx], membership[1], "REPLACE")
                else:
                    vgroup = obj.vertex_groups.new(name=membership[0])
                    skinGroupDict[membership[0]] = vgroup
                    vgroup.add([vertIdx], membership[1], "REPLACE")

    def set_object_data(self, obj: bpy.types.Object):
        super().set_object_data(obj)
        self.add_skin_groups_to_object(obj)

    def add_weights_to_ascii(
        self,
        obj: bpy.types.Object,
        ascii_lines: list[str],
    ):
        # Get a list of skingroups for this object:
        # A vertex group is a skingroup if there is an object in the mdl
        # with the same name as the group
        skingroups: dict[int, bpy.types.VertexGroup] = {}
        for group in obj.vertex_groups:

            def match_node_name(o, test_name: str = group.name) -> re.Match[str] | None:
                return o.name == test_name or re.match(rf"{test_name}\.\d\d\d", o.name)

            if utils.search_node_in_model(obj, match_node_name):
                skingroups[group.index] = group

        mesh = self.get_export_mesh(obj)

        vertexWeights: list[list[list[str | float]]] = []
        for v in mesh.vertices:
            weights: list[list[str | float]] = []
            for vg in v.groups:
                if vg.group not in skingroups:
                    # vertex group is not for bone weights, skip
                    continue
                group: bpy.types.VertexGroup = skingroups[vg.group]
                weights.append([group.name, vg.weight])
            if len(weights) > 4:
                # 4 is the maximum number of influencing bones per vertex
                # for MDL format, therefore we will remove the smallest
                # influences now to make the vertex format compliant
                weights = sorted(weights, key=lambda w: w[1], reverse=True)[0:4]
            total_weight = sum([w[1] for w in weights])
            if total_weight > 0.0 and round(total_weight, 3) != 1.0:
                # normalize weights to equal 1.0
                for w in weights:
                    w[1] /= total_weight
            vertexWeights.append(weights)

        numVerts: int = len(mesh.vertices)
        ascii_lines.append("  weights " + str(numVerts))
        for weights in vertexWeights:
            line: str = "  "
            if weights:
                for w in weights:
                    line += f"  {w[0]} {w[1]:.6f}"
            else:
                # No weights for this vertex ... this is a problem
                print("KotorBlender: WARNING - missing vertex weight in " + obj.name)
                line = "ERROR: no weight"
            ascii_lines.append(line)

    def add_data_to_ascii(
        self,
        obj: bpy.types.Object,
        ascii_lines: list[str],
        classification: defines.Classification = defines.Classification.UNKNOWN,
        simple: bool = False,
        name_dict: dict[str, str] | None = None,
    ):
        Trimesh.add_data_to_ascii(self, obj, ascii_lines, classification, name_dict=name_dict)

        self.add_weights_to_ascii(obj, ascii_lines)


class Emitter(GeometryNode):
    emitter_attrs: ClassVar[list[str]] = [
        "deadspace",
        "blastradius",
        "blastlength",
        "numBranches",
        "controlptsmoothing",
        "xgrid",
        "ygrid",
        "spawntype",
        "update",
        "render",
        "blend",
        "texture",
        "chunkName",
        "twosidedtex",
        "loop",
        "renderorder",
        "m_bFrameBlending",
        "m_sDepthTextureName",
        "p2p",
        "p2p_sel",
        "affectedByWind",
        "m_isTinted",
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
        "m_frandombirthrate",
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

    nodetype: ClassVar[NodeType | Literal["EMITTER"]] = NodeType.EMITTER
    meshtype: ClassVar[MeshType | Literal["EMITTER"]] = MeshType.EMITTER

    def __init__(self, name: str = "UNNAMED"):
        GeometryNode.__init__(self, name)
        # object data
        self.deadspace: float = 0.0
        self.blastradius: float = 0.0
        self.blastlength: float = 0.0
        self.numBranches: int = 0
        self.controlptsmoothing: int = 0
        self.xgrid: int = 0
        self.ygrid: int = 0
        self.spawntype: str = ""
        self.update: str = ""
        self.render: str = ""
        self.blend: str = ""
        self.texture: str = ""
        self.chunkName: str = ""
        self.twosidedtex: bool = False
        self.loop: bool = False
        self.renderorder: int = 0
        self.m_bFrameBlending: bool = False
        self.m_sDepthTextureName: str = defines.null
        # flags
        self.p2p: bool = False
        self.p2p_sel: bool = False
        self.affectedByWind: bool = False
        self.m_isTinted: bool = False
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
        self.m_frandombirthrate: float = 0.0
        self.bounce_co: float = 0.0
        self.combinetime: float = 0.0
        self.drag: float = 0.0
        self.fps: int = 0
        self.frameend: int = 0
        self.framestart: int = 0
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
        self.xsize: float = 2
        self.ysize: float = 2
        self.blurlength: float = 0.0
        self.lightningdelay: float = 0.0
        self.lightningradius: float = 0.0
        self.lightningsubdiv: int = 0
        self.lightningscale: float = 0.0
        self.lightningzigzag: int = 0
        self.percentstart: float = 0.0
        self.percentmid: float = 0.0
        self.percentend: float = 0.0
        self.targetsize: float = 0.0
        self.numcontrolpts: int = 0
        self.controlptradius: float = 0.0
        self.controlptdelay: int = 0
        self.tangentspread: int = 0
        self.tangentlength: float = 0.0
        self.colorstart: Color = (1.0, 1.0, 1.0)
        self.colormid: Color = (1.0, 1.0, 1.0)
        self.colorend: Color = (1.0, 1.0, 1.0)
        # unidentified stuff
        self.rawascii: str = ""

    def load_ascii(self, ascii_node: list[list[str]]):
        l_is_number = utils.is_number

        for line in ascii_node:
            try:
                label = line[0].lower()
            except IndexError:
                RobustLogger().debug(
                    "Probably empty line or whatever, skip it",
                    stacklevel=2,
                    extra={"ascii_node": ascii_node},
                    exc_info=True,
                    stack_info=True,
                )
                continue

            if not l_is_number(label):
                if label == "node":
                    self.name = utils.get_name(line[2])
                elif label == "endnode":
                    return
                elif label == "parent":
                    self.parentName = utils.get_name(line[1])
                elif label == "position":
                    self.position = (float(line[1]), float(line[2]), float(line[3]))
                elif label == "orientation":
                    axis_angle = (float(line[1]), float(line[2]), float(line[3]), float(line[4]))
                    self.orientation = Quaternion(axis_angle[0:3], axis_angle[3])
                elif label == "scale":
                    self.scale = float(line[1])
                elif label == "wirecolor":
                    self.wirecolor = (float(line[1]), float(line[2]), float(line[3]))
                elif label in [x.lower() for x in dir(self)]:
                    # this block covers all object data and controllers
                    attrname = next(name for name in dir(self) if name.lower() == label)
                    default_value = getattr(self, attrname)
                    try:
                        if isinstance(default_value, str):
                            setattr(self, attrname, line[1])
                        elif isinstance(default_value, bool):
                            setattr(self, attrname, bool(int(line[1])))
                        elif isinstance(default_value, int):
                            setattr(self, attrname, int(line[1]))
                        elif isinstance(default_value, float):
                            setattr(self, attrname, float(line[1]))
                        elif isinstance(default_value, tuple):
                            setattr(self, attrname, tuple(map(float, line[1:])))
                    except Exception as e:
                        RobustLogger().debug(f"Error setting attribute {attrname}: {e}")
                else:
                    self.rawascii += "\n  " + " ".join(line)

    def create_mesh(self, obj_name: str) -> bpy.types.Mesh:
        # Create the mesh itself
        mesh = bpy.data.meshes.new(obj_name)
        a_bmesh: bmesh.Bmesh = bmesh.new(use_operators=False)
        a_bmesh.verts.new(((self.xsize / 2) / 100.0, (self.ysize / 2) / 100.0, 0.0))
        a_bmesh.verts.new(((self.xsize / 2) / 100.0, (-self.ysize / 2) / 100.0, 0.0))
        a_bmesh.verts.new(((-self.xsize / 2) / 100.0, (-self.ysize / 2) / 100.0, 0.0))
        a_bmesh.verts.new(((-self.xsize / 2) / 100.0, (self.ysize / 2) / 100.0, 0.0))
        a_bmesh.verts.ensure_lookup_table()
        face_verts = [a_bmesh.verts[i] for i in range(4)]
        a_bmesh.faces.new((*face_verts,))
        a_bmesh.to_mesh(mesh)
        a_bmesh.free()
        return mesh

    def add_raw_ascii(self, obj: bpy.types.Object):
        txt = bpy.data.texts.new(obj.name)
        txt.write(self.rawascii)
        obj.kb.rawascii = txt.name

    def set_object_data(self, obj: bpy.types.Object):
        GeometryNode.set_object_data(self, obj)

        obj.kb.meshtype = self.meshtype

        for attrname in self.emitter_attrs:
            value = getattr(self, attrname)
            # Enum translation is not pretty...
            if attrname == "spawntype":
                if value == "0":
                    value = "Normal"
                elif value == "1":
                    value = "Trail"
                else:
                    value = "NONE"
            elif attrname == "update":
                if value.title() not in ["Fountain", "Single", "Explosion", "Lightning"]:
                    value = "NONE"
                else:
                    value = value.title()
            elif attrname == "render":
                attrname = "render_emitter"
                if value not in ["Normal", "Billboard_to_Local_Z", "Billboard_to_World_Z", "Aligned_to_World_Z", "Aligned_to_Particle_Dir", "Motion_Blur"]:
                    value = "NONE"
            elif attrname == "blend":
                if value.lower() == "punchthrough":
                    value = "Punch-Through"
                elif value.title() not in ["Lighten", "Normal", "Punch-Through"]:
                    value = "NONE"
            # translate p2p_sel to metaproperty p2p_type
            elif attrname == "p2p_sel":
                if self.p2p_sel:
                    obj.kb.p2p_type = "Bezier"
                else:
                    obj.kb.p2p_type = "Gravity"
                # p2p_type has update method, sets p2p_sel
                # except it doesn't seem to initially
                obj.kb.p2p_sel = self.p2p_sel
                continue
            setattr(obj.kb, attrname, value)

    def add_to_collection(
        self,
        collection: bpy.types.Collection,
    ) -> bpy.types.Object:
        mesh = self.create_mesh(self.name)
        obj = bpy.data.objects.new(self.name, mesh)

        self.set_object_data(obj)
        collection.objects.link(obj)
        return obj

    def add_data_to_ascii(
        self,
        obj: bpy.types.Object,
        ascii_lines: list[str],
        classification: Classification | Literal["UNKNOWN"] = Classification.UNKNOWN,
        simple: bool = False,
        name_dict: dict[str, str] | None = None,
    ):
        super().add_data_to_ascii(obj, ascii_lines, classification, simple, name_dict=name_dict)

        # export the copious amounts of emitter data
        for attrname in self.emitter_attrs:
            if attrname == "render":
                value = obj.kb.render_emitter
            else:
                value = getattr(obj.kb, attrname)
            if attrname == "spawntype":
                if value == "Normal":
                    value = 0
                elif value == "Trail":
                    value = 1
            if isinstance(value, Color):
                value = " ".join([f"{x:.6g}" for x in value])
            elif isinstance(value, tuple):
                value = " ".join([f"{x:.6g}" for x in value])
            elif isinstance(value, float):
                value = f"{value:.7g}"
            elif isinstance(value, bool):
                value = str(int(value))
            elif isinstance(value, str) and (not value or value == "NONE"):
                continue
            else:
                value = str(value)
            ascii_lines.append(f"  {attrname} {value}")


class Light(GeometryNode):
    def __init__(self, name: str = "UNNAMED"):
        GeometryNode.__init__(self, name)
        self.nodetype: Literal["light"] = "light"

        self.shadow: int = 1
        self.radius: float = 5.0
        self.multiplier: int = 1
        self.lightpriority: int = 5
        self.color: Color = (0.0, 0.0, 0.0)
        self.ambientonly: int = 1
        self.ndynamictype: int = 0
        self.isdynamic: int = 0
        self.affectdynamic: int = 1
        self.negativelight: int = 0
        self.fadinglight: int = 1
        self.lensflares: int = 0
        self.flareradius: float = 1.0
        self.flareList: FlareList = FlareList()

    def load_ascii(self, ascii_node: list[list[str]]):
        GeometryNode.load_ascii(self, ascii_node)

        flareTextureNamesStart: int = 0
        numFlares: int = 0
        numVals: int = 0

        l_is_number = utils.is_number
        for idx, line in enumerate(ascii_node):
            try:
                label = line[0].lower()
            except IndexError:
                RobustLogger().debug(
                    "Probably empty line or whatever, skip it",
                    stacklevel=2,
                    extra={"ascii_node": ascii_node},
                    exc_info=True,
                    stack_info=True,
                )
                continue

            if not l_is_number(label):
                if label == "radius":
                    self.radius = float(line[1])
                    self.parsed_lines.append(idx)
                elif label == "shadow":
                    self.shadow = int(line[1])
                    self.parsed_lines.append(idx)
                elif label == "multiplier":
                    self.multiplier = float(line[1])
                    self.parsed_lines.append(idx)
                elif label == "color":
                    self.color = Color(float(line[1]), float(line[2]), float(line[3]))
                    self.parsed_lines.append(idx)
                elif label == "ambientonly":
                    self.ambientonly = int(line[1])
                    self.parsed_lines.append(idx)
                elif label == "ndynamictype":
                    self.ndynamictype = int(line[1])
                    self.parsed_lines.append(idx)
                elif label == "isdynamic":
                    self.isdynamic = int(line[1])
                    self.parsed_lines.append(idx)
                elif label == "affectdynamic":
                    self.affectdynamic = int(line[1])
                    self.parsed_lines.append(idx)
                elif label == "negativelight":
                    self.negativelight = int(line[1])
                    self.parsed_lines.append(idx)
                elif label == "lightpriority":
                    self.lightpriority = int(line[1])
                    self.parsed_lines.append(idx)
                elif label == "fadinglight":
                    self.fadinglight = int(line[1])
                    self.parsed_lines.append(idx)
                elif label == "lensflares":
                    self.lensflares = int(line[1])
                    self.parsed_lines.append(idx)
                elif label == "flareradius":
                    self.flareradius = float(line[1])
                    self.parsed_lines.append(idx)
                elif label == "texturenames":
                    # List of names follows, but we don't necessarily know how
                    # many flares there are
                    # We 'll need to read them later. For now save the index
                    flareTextureNamesStart = idx + 1
                    self.parsed_lines.append(idx)
                elif label == "flaresizes":
                    # List of floats
                    numVals = next((i for i, v in enumerate(ascii_node[idx + 1 :]) if not l_is_number(v[0])), -1)
                    parse.f1(ascii_node[idx + 1 : idx + numVals + 1], self.flareList.sizes)
                    self.parsed_lines.extend(range(idx, idx + numVals + 1))
                elif label == "flarepositions":
                    # List of floats
                    numVals = next((i for i, v in enumerate(ascii_node[idx + 1 :]) if not l_is_number(v[0])), -1)
                    parse.f1(ascii_node[idx + 1 : idx + numVals + 1], self.flareList.positions)
                    self.parsed_lines.extend(range(idx, idx + numVals + 1))
                elif label == "flarecolorshifts":
                    # List of float 3-tuples
                    numVals = next((i for i, v in enumerate(ascii_node[idx + 1 :]) if not l_is_number(v[0])), -1)
                    parse.f3(ascii_node[idx + 1 : idx + numVals + 1], self.flareList.colorshifts)
                    self.parsed_lines.extend(range(idx, idx + numVals + 1))

        # Load flare texture names:
        numFlares = min(len(self.flareList.sizes), len(self.flareList.colorshifts), len(self.flareList.positions))
        for i in range(numFlares):
            texName = ascii_node[flareTextureNamesStart + i][0]
            self.flareList.textures.append(texName)
            self.parsed_lines.append(flareTextureNamesStart + i)

        if self.nodetype == "light":
            self.add_unparsed_to_raw(ascii_node)

    def create_light(self, name: str) -> bpy.types.Light:
        light = bpy.data.lights.new(name, "POINT")
        light.color = self.color
        light.use_shadow = self.shadow != 0
        return light

    def set_object_data(self, obj: bpy.types.Object):
        super().set_object_data(obj)

        switch: dict[str, str] = {"ml1": "MAINLIGHT1", "ml2": "MAINLIGHT2", "sl1": "SOURCELIGHT1", "sl2": "SOURCELIGHT2"}
        # TODO: Check light names when exporting tiles
        obj.kb.multiplier = self.multiplier
        obj.kb.radius = self.radius
        obj.kb.ambientonly = self.ambientonly >= 1
        obj.kb.lighttype = switch.get(self.name[-3:], "NONE")
        obj.kb.shadow = self.shadow >= 1
        obj.kb.lightpriority = self.lightpriority
        obj.kb.fadinglight = self.fadinglight >= 1
        obj.kb.isdynamic = self.ndynamictype
        if obj.kb.isdynamic == 0 and self.isdynamic >= 1:
            obj.kb.isdynamic = 1
        obj.kb.affectdynamic = self.affectdynamic >= 1

        if self.flareradius > 0 or self.lensflares >= 1:
            obj.kb.lensflares = True
            numFlares = len(self.flareList.textures)
            for i in range(numFlares):
                newItem = obj.kb.flareList.add()
                newItem.texture = self.flareList.textures[i]
                newItem.colorshift = self.flareList.colorshifts[i]
                newItem.size = self.flareList.sizes[i]
                newItem.position = self.flareList.positions[i]

        obj.kb.flareradius = self.flareradius
        light.calc_light_power(obj)

    def add_to_collection(self, collection: bpy.types.Collection) -> bpy.types.Object:
        light = self.create_light(self.name)
        obj = bpy.data.objects.new(self.name, light)
        self.set_object_data(obj)
        collection.objects.link(obj)
        return obj

    def add_flares_to_ascii(self, obj: bpy.types.Object, ascii_lines: list[str]):
        if obj.kb.lensflares:
            num_flares = int(obj.kb.lensflares)
            ascii_lines.append(f"  lensflares {num_flares}")
            if obj.kb.flareList:
                # TODO: Clean this up
                ascii_lines.append(f"  texturenames {num_flares}")
                ascii_lines.extend([f"    {flare.texture}" for flare in obj.kb.flareList])
                ascii_lines.append(f"  flarepositions {num_flares}")
                ascii_lines.extend([f"    {round(flare.position, 7)}" for flare in obj.kb.flareList])
                ascii_lines.append(f"  flaresizes {num_flares}")
                ascii_lines.extend([f"    {flare.size}" for flare in obj.kb.flareList])
                ascii_lines.append(f"  flarecolorshifts {num_flares}")
                ascii_lines.extend([f"    {' '.join(str(round(c, 2)) for c in flare.colorshift[:3])}" for flare in obj.kb.flareList])
        ascii_lines.append(f"  flareradius {round(obj.kb.flareradius, 1)}")

    def add_data_to_ascii(
        self,
        obj: bpy.types.Object,
        ascii_lines: list[str],
        classification: Classification | Literal["UNKNOWN"] = Classification.UNKNOWN,
        simple: bool = False,
        name_dict: dict[str, str] | None = None,
    ):
        name_dict = {} if name_dict is None else name_dict
        super().add_data_to_ascii(obj, ascii_lines, classification, name_dict=name_dict)

        light: bpy.types.Light = obj.data
        color = (light.color[0], light.color[1], light.color[2])
        ascii_lines.append("  radius " + str(round(obj.kb.radius, 1)))
        ascii_lines.append("  multiplier " + str(round(obj.kb.multiplier, 1)))
        ascii_lines.append("  color " + str(round(color[0], 2)) + " " + str(round(color[1], 2)) + " " + str(round(color[2], 2)))
        ascii_lines.append("  ambientonly " + str(int(obj.kb.ambientonly)))
        ascii_lines.append("  nDynamicType " + str(obj.kb.isdynamic))
        ascii_lines.append("  affectDynamic " + str(int(obj.kb.affectdynamic)))
        ascii_lines.append("  shadow " + str(int(obj.kb.shadow)))
        ascii_lines.append("  lightpriority " + str(obj.kb.lightpriority))
        ascii_lines.append("  fadingLight " + str(int(obj.kb.fadinglight)))
        self.add_flares_to_ascii(obj, ascii_lines)


class Aabb(Trimesh):
    """No need to import Aaabb's. Aabb nodes in mdl files will be
    treated as trimeshes.
    """

    nodetype: ClassVar[NodeType | Literal["AABB"]] = NodeType.AABB
    meshtype: ClassVar[MeshType | Literal["AABB"]] = MeshType.AABB

    def __init__(self, name: str = "UNNAMED"):
        super().__init__(name)

    def compute_layout_position(self, wkm):
        wkmv1 = wkm.verts[wkm.facelist.faces[0][0]]
        wkmv1 = (wkmv1[0] - wkm.position[0], wkmv1[1] - wkm.position[1], wkmv1[2] - wkm.position[2])
        for faceIdx, face in enumerate(self.facelist.faces):
            if self.facelist.matId[faceIdx] != 7:
                v1 = self.verts[face[0]]
                self.lytposition = (round(wkmv1[0] - v1[0], 6), round(wkmv1[1] - v1[1], 6), round(wkmv1[2] - v1[2], 6))
                break
        bpy.data.objects[self.objref].kb.lytposition = self.lytposition

    def add_aabb_to_ascii(self, obj: bpy.types.Object, ascii_lines: list[str]):
        if glob.applyModifiers:
            depsgraph = bpy.context.evaluated_depsgraph_get()
            obj_eval = obj.evaluated_get(depsgraph)
            walkmesh = obj_eval.to_mesh()
        else:
            walkmesh = obj.to_mesh()

        faceList: list[tuple[int, list[Vector], Vector]] = []
        faceIdx: int = 0
        for polygon in walkmesh.polygons:
            if len(polygon.vertices) == 3:
                # Tri
                v0 = polygon.vertices[0]
                v1 = polygon.vertices[1]
                v2 = polygon.vertices[2]

                centroid = Vector((walkmesh.vertices[v0].co + walkmesh.vertices[v1].co + walkmesh.vertices[v2].co) / 3)
                faceList.append(
                    (
                        faceIdx,
                        [
                            walkmesh.vertices[v0].co,
                            walkmesh.vertices[v1].co,
                            walkmesh.vertices[v2].co,
                        ],
                        centroid,
                    )
                )
                faceIdx += 1

            elif len(polygon.vertices) == 4:
                # Quad
                v0 = polygon.vertices[0]
                v1 = polygon.vertices[1]
                v2 = polygon.vertices[2]
                v3 = polygon.vertices[3]

                centroid = Vector((walkmesh.vertices[v0].co + walkmesh.vertices[v1].co + walkmesh.vertices[v2].co) / 3)
                faceList.append(
                    (
                        faceIdx,
                        [
                            walkmesh.vertices[v0].co,
                            walkmesh.vertices[v1].co,
                            walkmesh.vertices[v2].co,
                        ],
                        centroid,
                    )
                )
                faceIdx += 1

                centroid = Vector((walkmesh.vertices[v2].co + walkmesh.vertices[v3].co + walkmesh.vertices[v0].co) / 3)
                faceList.append(
                    (
                        faceIdx,
                        [
                            walkmesh.vertices[v2].co,
                            walkmesh.vertices[v3].co,
                            walkmesh.vertices[v0].co,
                        ],
                        centroid,
                    )
                )
                faceIdx += 1
            else:
                # Ngon or no polygon at all (This should never be the case with tessfaces)
                RobustLogger().warning("ngon in walkmesh. Unable to generate aabb.")
                return

        aabbTree: list[list[float]] = []
        aabb.generate_tree(aabbTree, faceList)
        if aabbTree:
            ascii_lines.extend(
                [
                    f"  aabb   {' '.join(f'{round(n, 7)}' for n in node[:6])} {node[6]}" if i == 0 else f"    {' '.join(f'{round(n, 7)}' for n in node[:6])} {node[6]}"
                    for i, node in enumerate(aabbTree)
                ]
            )

    def add_data_to_ascii(
        self,
        obj: bpy.types.Object,
        ascii_lines: list[str],
        classification: Classification | Literal["UNKNOWN"] = Classification.UNKNOWN,
        simple: bool = False,
        name_dict: dict[str, str] | None = None,
    ):
        if obj.parent and name_dict and obj.parent.name in name_dict:
            ascii_lines.append("  parent " + name_dict[obj.parent.name])
        elif obj.parent:
            ascii_lines.append("  parent " + obj.parent.name)
        else:
            ascii_lines.append("  parent " + defines.null)
        loc = obj.location
        ascii_lines.append("  position " + str(round(loc[0], 7)) + " " + str(round(loc[1], 7)) + " " + str(round(loc[2], 7)))
        rot = utils.get_aurora_rot_from_object(obj)
        ascii_lines.append("  orientation " + str(round(rot[0], 7)) + " " + str(round(rot[1], 7)) + " " + str(round(rot[2], 7)) + " " + str(round(rot[3], 7)))
        color = obj.kb.wirecolor
        ascii_lines.append("  wirecolor " + str(round(color[0], 2)) + " " + str(round(color[1], 2)) + " " + str(round(color[2], 2)))
        ascii_lines.append("  ambient 1.0 1.0 1.0")
        self.add_material_data_to_ascii(obj, ascii_lines)
        Trimesh.add_mesh_data_to_ascii(self, obj, ascii_lines, simple)
        if self.roottype != "wok":
            self.add_aabb_to_ascii(obj, ascii_lines)

    def add_material_data_to_ascii(
        self,
        obj: bpy.types.Object,
        ascii_lines: list[str],
    ):
        ascii_lines.append("  diffuse 1.0 1.0 1.0")

        imgName = obj.kb.bitmap2 if obj.kb.bitmap2 else defines.null

        ascii_lines.append("  bitmap " + defines.null)
        ascii_lines.append("  bitmap2 " + imgName)

        lightmapped = 1 if obj.kb.lightmapped else 0
        ascii_lines.append("  lightmapped " + str(lightmapped))

    def create_mesh(self, name: str) -> bpy.types.Mesh:
        # Create the mesh itself
        mesh = bpy.data.meshes.new(name)
        mesh.vertices.add(len(self.verts))
        mesh.vertices.foreach_set("co", unpack_list(self.verts))
        num_faces = len(self.facelist.faces)
        mesh.loops.add(3 * num_faces)
        mesh.loops.foreach_set("vertex_index", unpack_list(self.facelist.faces))
        mesh.polygons.add(num_faces)
        mesh.polygons.foreach_set("loop_start", range(0, 3 * num_faces, 3))
        mesh.polygons.foreach_set("loop_total", (3,) * num_faces)

        # Create materials
        for wokMat in defines.wok_materials:
            matName = wokMat[0]
            # Walkmesh materials will be shared across multiple walkmesh
            # objects
            if matName in bpy.data.materials:
                material = bpy.data.materials[matName]
            else:
                material = bpy.data.materials.new(matName)
                material.diffuse_color = [*wokMat[1], 1.0]
                material.specular_color = (0.0, 0.0, 0.0)
                material.specular_intensity = wokMat[2]
            mesh.materials.append(material)

        # Apply the walkmesh materials to each face
        for idx, polygon in enumerate(mesh.polygons):
            polygon.material_index = self.facelist.matId[idx]

        # Create UV map
        if len(self.tverts) > 0:
            uv = unpack_list([self.tverts[i] for indices in self.facelist.uvIdx for i in indices])
            uv_layer = mesh.uv_layers.new(name="UVMap", do_init=False)
            uv_layer.data.foreach_set("uv", uv)

        # Create lightmap UV map
        if len(self.tverts1) > 0:
            if len(self.texindices1) > 0:
                uv = unpack_list([self.tverts1[i] for indices in self.texindices1 for i in indices])
            else:
                uv = unpack_list([self.tverts1[i] for indices in self.facelist.uvIdx for i in indices])

            uv_layer = mesh.uv_layers.new(name="UVMap_lm", do_init=False)
            uv_layer.data.foreach_set("uv", uv)

        # If there are room links in MDL, then this model is from MDLedit, and we must NOT skip non-walkable faces
        if self.roottype == "mdl" and len(self.roomlinks):
            self.set_room_links(mesh, False)  # noqa: FBT003

        mesh.update()
        return mesh

    def add_to_collection(self, collection: bpy.types.Collection) -> bpy.types.Object:
        mesh = self.create_mesh(self.name)
        obj = bpy.data.objects.new(self.name, mesh)
        self.set_object_data(obj)
        collection.objects.link(obj)
        return obj
