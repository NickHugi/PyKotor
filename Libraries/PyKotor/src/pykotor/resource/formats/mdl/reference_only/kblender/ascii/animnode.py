from __future__ import annotations

import collections
import re

from typing import Any, Callable, ClassVar, Literal

import bpy

from loggerplus import RobustLogger
from mathutils import Quaternion

from pykotor.resource.formats.mdl.reference_only.ascii.parse import parse
from pykotor.resource.formats.mdl.reference_only.constants import NodeType, defines, utils


class Keys:
    def __init__(self):
        self.position: list[float] = []
        self.orientation: list[float] = []
        self.scale: list[float] = []
        self.selfillumcolor: list[float] = []
        self.alpha: list[float] = []
        # Lights
        self.color: list[float] = []
        self.radius: list[float] = []
        # Emitters
        self.alphastart: list[float] = []
        self.alphamid: list[float] = []
        self.alphaend: list[float] = []
        self.birthrate: list[float] = []
        self.m_frandombirthrate: list[float] = []
        self.bounce_co: list[float] = []
        self.combinetime: list[float] = []
        self.drag: list[float] = []
        self.fps: list[float] = []
        self.frameend: list[int] = []
        self.framestart: list[int] = []
        self.grav: list[float] = []
        self.lifeexp: list[float] = []
        self.mass: list[float] = []
        self.p2p_bezier2: list[float] = []
        self.p2p_bezier3: list[float] = []
        self.particlerot: list[float] = []
        self.randvel: list[float] = []
        self.sizestart: list[float] = []
        self.sizemid: list[float] = []
        self.sizeend: list[float] = []
        self.sizestart_y: list[float] = []
        self.sizemid_y: list[float] = []
        self.sizeend_y: list[float] = []
        self.spread: list[float] = []
        self.threshold: list[float] = []
        self.velocity: list[float] = []
        self.xsize: list[float] = []
        self.ysize: list[float] = []
        self.blurlength: list[float] = []
        self.lightningdelay: list[float] = []
        self.lightningradius: list[float] = []
        self.lightningsubdiv: list[int] = []
        self.lightningscale: list[float] = []
        self.lightningzigzag: list[float] = []
        self.percentstart: list[float] = []
        self.percentmid: list[float] = []
        self.percentend: list[float] = []
        self.targetsize: list[float] = []
        self.numcontrolpts: list[int] = []
        self.controlptradius: list[float] = []
        self.controlptdelay: list[float] = []
        self.tangentspread: list[float] = []
        self.tangentlength: list[float] = []
        self.colorstart: list[float] = []
        self.colormid: list[float] = []
        self.colorend: list[float] = []
        # Unknown. Import as text
        self.rawascii: str = ""

    def has_alpha(self) -> bool:
        return len(self.alpha) > 0


class Node:
    KEY_TYPE: ClassVar[dict[str, dict[str, Any]]] = {
        "position": {
            "values": 3,
            "axes": 3,
            "objdata": "location",
        },
        "orientation": {
            "values": 4,
            "axes": 4,
            "objdata": "rotation_quaternion",
        },
        "scale": {
            "values": 1,
            "axes": 3,
            "objdata": "scale",
        },
        "alpha": {
            "values": 1,
            "axes": 1,
            "objdata": "kb.alpha",
        },
        "selfillumcolor": {
            "values": 3,
            "axes": 3,
            "objdata": "kb.selfillumcolor",
        },
        "color": {
            "values": 3,
            "axes": 3,
            "objdata": "color",
        },
        "radius": {
            "values": 1,
            "axes": 1,
            "objdata": "distance",
        },
    }
    EMITTER_KEY_TYPE: ClassVar[dict[str, dict[str, Any]]] = {
        "alphaStart": {
            "values": 1,
            "axes": 1,
        },
        "alphaMid": {
            "values": 1,
            "axes": 1,
        },
        "alphaEnd": {
            "values": 1,
            "axes": 1,
        },
        "birthrate": {
            "values": 1,
            "axes": 1,
            "conversion": float,
        },
        "m_fRandomBirthRate": {
            "values": 1,
            "axes": 1,
            "conversion": float,
        },
        "bounce_co": {
            "values": 1,
            "axes": 1,
        },
        "combinetime": {
            "values": 1,
            "axes": 1,
        },
        "drag": {
            "values": 1,
            "axes": 1,
        },
        "fps": {
            "values": 1,
            "axes": 1,
            "conversion": int,
        },
        "frameEnd": {
            "values": 1,
            "axes": 1,
            "conversion": int,
        },
        "frameStart": {
            "values": 1,
            "axes": 1,
            "conversion": int,
        },
        "grav": {
            "values": 1,
            "axes": 1,
        },
        "lifeExp": {
            "values": 1,
            "axes": 1,
        },
        "mass": {
            "values": 1,
            "axes": 1,
        },
        "p2p_bezier2": {
            "values": 1,
            "axes": 1,
        },
        "p2p_bezier3": {
            "values": 1,
            "axes": 1,
        },
        "particleRot": {
            "values": 1,
            "axes": 1,
        },
        "randvel": {
            "values": 1,
            "axes": 1,
        },
        "sizeStart": {
            "values": 1,
            "axes": 1,
        },
        "sizeMid": {
            "values": 1,
            "axes": 1,
        },
        "sizeEnd": {
            "values": 1,
            "axes": 1,
        },
        "sizeStart_y": {
            "values": 1,
            "axes": 1,
        },
        "sizeMid_y": {
            "values": 1,
            "axes": 1,
        },
        "sizeEnd_y": {
            "values": 1,
            "axes": 1,
        },
        "spread": {
            "values": 1,
            "axes": 1,
        },
        "threshold": {
            "values": 1,
            "axes": 1,
        },
        "velocity": {
            "values": 1,
            "axes": 1,
        },
        "xsize": {
            "values": 1,
            "axes": 1,
            "conversion": int,
        },
        "ysize": {
            "values": 1,
            "axes": 1,
            "conversion": int,
        },
        "blurlength": {
            "values": 1,
            "axes": 1,
        },
        "lightningDelay": {
            "values": 1,
            "axes": 1,
        },
        "lightningRadius": {
            "values": 1,
            "axes": 1,
        },
        "lightningSubDiv": {
            "values": 1,
            "axes": 1,
            "conversion": int,
        },
        "lightningScale": {
            "values": 1,
            "axes": 1,
        },
        "lightningzigzag": {
            "values": 1,
            "axes": 1,
            "conversion": int,
        },
        "percentStart": {
            "values": 1,
            "axes": 1,
        },
        "percentMid": {
            "values": 1,
            "axes": 1,
        },
        "percentEnd": {
            "values": 1,
            "axes": 1,
        },
        "targetsize": {
            "values": 1,
            "axes": 1,
            "conversion": int,
        },
        "numcontrolpts": {
            "values": 1,
            "axes": 1,
            "conversion": int,
        },
        "controlptradius": {
            "values": 1,
            "axes": 1,
        },
        "controlptdelay": {
            "values": 1,
            "axes": 1,
            "conversion": int,
        },
        "tangentspread": {
            "values": 1,
            "axes": 1,
            "conversion": int,
        },
        "tangentlength": {
            "values": 1,
            "axes": 1,
        },
        "colorStart": {
            "values": 3,
            "axes": 3,
        },
        "colorMid": {
            "values": 3,
            "axes": 3,
        },
        "colorEnd": {
            "values": 3,
            "axes": 3,
        },
    }

    def __init__(self, name: str = "UNNAMED"):
        self.name: str = name
        self.nodetype: str = "dummy"
        self.parentName: str = defines.null

        # Keyed
        self.keys: Keys = Keys()

        self.isEmpty: bool = True

    def __bool__(self) -> bool:
        """Return false if the node is empty, i.e. it has no anims attached."""
        return not self.isEmpty

    def requires_unique_data(self):
        return self.keys.has_alpha()

    def parse_keys_9f(self, ascii_block: list[list[str]], key_list: list[float]):
        """Parse animation keys containing 9 floats (not counting the time value)."""
        parse._f(ascii_block, key_list, 10)
        self.isEmpty = False

    def parse_keys_3f(self, ascii_block: list[list[str]], key_list: list[float]):
        """Parse animation keys containing 3 floats (not counting the time value)."""
        parse.f4(ascii_block, key_list)
        self.isEmpty = False

    def parse_keys_4f(self, ascii_block: list[list[str]], key_list: list[float]):
        """Parse animation keys containing 4 floats (not counting the time value)."""
        parse.f5(ascii_block, key_list)
        self.isEmpty = False

    def parse_keys_1f(self, ascii_block: list[list[str]], key_list: list[float]):
        """Parse animation keys containing 1 float (not counting the time value)."""
        parse.f2(ascii_block, key_list)
        self.isEmpty = False

    def parse_keys_incompat(self, ascii_block: list[list[str]]):
        """Parse animation keys incompatible with blender. They will be saved
        as plain text.
        """
        for line in ascii_block:
            self.keys.rawascii = self.keys.rawascii + "\n" + " ".join(line)
        self.isEmpty = False

    @staticmethod
    def find_end(ascii_block: list[list[str]]) -> int:
        """We don't know when a list of keys of keys will end. We'll have to
        search for the first non-numeric value.
        """
        l_is_number: Callable[[str], bool] = utils.is_number
        return next((i for i, v in enumerate(ascii_block) if len(v) and not l_is_number(v[0])), -1)

    def load_ascii(self, ascii_block: list[list[str]]):
        l_is_number: Callable[[str], bool] = utils.is_number
        for idx, line in enumerate(ascii_block):
            try:
                label = line[0].lower()
            except IndexError:  # noqa: S112
                # Probably empty line or whatever, skip it
                continue
            if label == "node":
                self.nodeType = line[1].lower()
                self.name = utils.get_name(line[2])
            elif label == "endnode":
                return
            elif label == "endlist":
                # Can't rely on that being here. We have our own way to get
                # the end of a key list
                pass
            elif label == "parent":
                self.parentName = utils.get_name(line[1])
            elif label in self.KEY_TYPE or label in (attr + "key" for attr in self.KEY_TYPE) or label in (attr + "bezierkey" for attr in self.KEY_TYPE):
                # Parse all controllers: unkeyed, keyed, or bezierkeyed
                attrname = next(attr for attr in self.KEY_TYPE if label.startswith(attr))
                attr_type = self.KEY_TYPE[attrname]
                key_type = ""
                key_type = "key" if label.endswith("key") else key_type
                key_type = "bezierkey" if label.endswith("bezierkey") else key_type
                numVals = attr_type["values"]
                if key_type:
                    if key_type == "bezierkey":
                        numVals *= 3
                    numKeys = type(self).find_end(ascii_block[idx + 1 :])
                    subblock = ascii_block[idx + 1 : idx + numKeys + 1]
                else:
                    numKeys = 1
                    subblock = [[0.0] + line[1:]]
                # parse numvals plus one for time
                parse._f(subblock, getattr(self.keys, attrname), numVals + 1)
                self.isEmpty = False
            elif (
                label in (attr.lower() for attr in self.EMITTER_KEY_TYPE)
                or label in (attr.lower() + "key" for attr in self.EMITTER_KEY_TYPE)
                or label in (attr.lower() + "bezierkey" for attr in self.EMITTER_KEY_TYPE)
            ):
                # Parse all controllers: unkeyed, keyed, or bezierkeyed
                attrname = next(attr for attr in self.EMITTER_KEY_TYPE if attr.lower() in label)
                propname = attrname.lower()
                attr_type = self.EMITTER_KEY_TYPE[attrname]
                key_type = ""
                key_type = "key" if label.endswith("key") else key_type
                key_type = "bezierkey" if label.endswith("bezierkey") else key_type
                numVals = attr_type["values"]
                if key_type:
                    if key_type == "bezierkey":
                        numVals *= 3
                    numKeys = type(self).find_end(ascii_block[idx + 1 :])
                    subblock = ascii_block[idx + 1 : idx + numKeys + 1]
                else:
                    numKeys = 1
                    subblock = [[0.0] + line[1:]]
                # parse numvals plus one for time
                if "conversion" in attr_type and attr_type["conversion"] is int:
                    parse._i(subblock, getattr(self.keys, propname), numVals + 1)
                else:
                    parse._f(subblock, getattr(self.keys, propname), numVals + 1)
                self.isEmpty = False
            # Some unknown text.
            # Probably keys for emitters = incompatible with blender. Import as text.
            elif not l_is_number(line[0]):
                numKeys = type(self).find_end(ascii_block[idx + 1 :])
                if numKeys:
                    self.parse_keys_incompat(ascii_block[idx : idx + numKeys + 1])
                    self.isEmpty = False

    @staticmethod
    def get_keys_from_action(anim: bpy.types.AnimData, action: bpy.types.Action, key_dict: dict[str, Any]):
        for fcurve in action.fcurves:
            # Get the sub dict for this particlar type of fcurve
            axis = fcurve.array_index
            dataPath = fcurve.data_path
            name = ""
            for keyname in Node.KEY_TYPE:
                ktype = Node.KEY_TYPE[keyname]
                if ktype["objdata"] is not None and dataPath == ktype["objdata"]:
                    name = keyname + "key"
                    break
            for keyname in Node.EMITTER_KEY_TYPE:
                if dataPath == "kb." + keyname.lower():
                    ktype = Node.EMITTER_KEY_TYPE[keyname]
                    name = keyname + "key"
                    break

            # does this fcurve have points in this animation?
            # if not, skip it
            if not len([kfp for kfp in fcurve.keyframe_points if kfp.co[0] >= anim.frameStart and kfp.co[0] <= anim.frameEnd]):
                continue

            for kfp in fcurve.keyframe_points:
                if name.startswith("orientation"):
                    # bezier keyed orientation animation currently unsupported
                    break
                if kfp.interpolation == "BEZIER":
                    name = re.sub(r"^(.+)key$", r"\1bezierkey", name)
                    break

            for kfkey, kfp in enumerate(fcurve.keyframe_points):
                frame = int(round(kfp.co[0]))
                if frame < anim.frameStart or frame > anim.frameEnd:
                    continue
                if name not in key_dict:
                    key_dict[name] = collections.OrderedDict()
                keys = key_dict[name]
                values = keys.get(frame, [0.0, 0.0, 0.0, 0.0])
                values[axis] = values[axis] + kfp.co[1]
                if name.endswith("bezierkey"):
                    if kfp.interpolation == "BEZIER":
                        values[ktype["axes"] + (axis * 2) : (ktype["axes"] + 1) + (axis * 2)] = [kfp.handle_left[1] - kfp.co[1], kfp.handle_right[1] - kfp.co[1]]
                    elif kfp.interpolation == "LINEAR":
                        # do the linear emulation,
                        # distance between keyframes / 3 point on linear interpolation @ frame
                        # y = y0 + ((x - x0) * ((y1 - y0)/(x1 - x0)))
                        # right handle is on the segment controlled by this keyframe
                        if kfkey < len(fcurve.keyframe_points) - 1:
                            next_kfp = fcurve.keyframe_points[kfkey + 1]
                            next_frame = int(round((next_kfp.co[0] - kfp.co[0]) / 3.0))
                            right_handle = kfp.co[1] + ((next_frame - frame) * ((next_kfp.co[1] - kfp.co[1]) / (next_kfp.co[0] - kfp.co[0])))
                            # make exported right handle value relative to keyframe value:
                            right_handle = right_handle - kfp.co[1]
                        else:
                            right_handle = 0.0
                        # left handle is on the segment controlled by the previous keyframe
                        if kfkey > 0 and fcurve.keyframe_points[kfkey - 1].interpolation == "LINEAR":
                            prev_kfp = fcurve.keyframe_points[kfkey - 1]
                            prev_frame = int(round((kfp.co[0] - prev_kfp.co[0]) / 3.0))
                            left_handle = prev_kfp.co[1] + ((prev_frame - prev_kfp.co[0]) * ((kfp.co[1] - prev_kfp.co[1]) / (kfp.co[0] - prev_kfp.co[0])))
                            # make exported left handle value relative to keyframe value:
                            left_handle = left_handle - kfp.co[1]
                        elif kfkey > 0 and kfp.handle_left and kfp.handle_left[1]:
                            left_handle = kfp.handle_left[1] - kfp.co[1]
                        else:
                            left_handle = 0.0
                        values[ktype["axes"] + (axis * 2) : (ktype["axes"] + 1) + (axis * 2)] = [left_handle, right_handle]
                    else:
                        # somebody mixed an unknown keyframe type ...
                        # give them some bad data
                        values[ktype["axes"] + (axis * 2) : (ktype["axes"] + 1) + (axis * 2)] = [0.0, 0.0]
                keys[frame] = values

    def add_keys_to_ascii_incompat(
        self,
        obj: bpy.types.Object,
        ascii_lines: list[str],
    ):
        return Node.generate_ascii_keys_incompat(obj, ascii_lines)

    @staticmethod
    def generate_ascii_keys_incompat(
        obj: bpy.types.Object,
        ascii_lines: list[str],
        options: dict[str, Any] | None = None,
    ):
        options = {} if options is None else options
        if obj.kb.rawascii not in bpy.data.texts:
            return
        txt = bpy.data.texts[obj.kb.rawascii]
        txtLines = [l.split() for l in txt.as_string().split("\n")]
        for line in txtLines:
            try:
                label = line[0].lower()
            except IndexError:
                RobustLogger().debug("Probably empty line or whatever, skip it")
                continue
            if label in ("node", "endnode", "parent", "position"):
                # We don't need any of this
                pass
            elif label[0] != "#":
                if utils.is_number(label):
                    ascii_lines.append("      " + " ".join(line))
                else:
                    ascii_lines.append("    " + " ".join(line))

    @staticmethod
    def generate_ascii_keys(
        anim_obj: bpy.types.Object,
        anim: bpy.types.AnimData,
        ascii_lines: list[str],
        options: dict[str, Any] | None = None,
    ):
        options = {} if options is None else options
        key_dict: dict[str, Any] = {}

        # Object Data
        if anim_obj.animation_data:
            action = anim_obj.animation_data.action
            if action:
                Node.get_keys_from_action(anim, action, key_dict)

        # Light Data
        if anim_obj.data and anim_obj.data.animation_data:
            action = anim_obj.data.animation_data.action
            if action:
                Node.get_keys_from_action(anim, action, key_dict)

        for attrname in Node.KEY_TYPE:
            bezname = attrname + "bezierkey"
            keyname = attrname + "key"
            if (bezname not in key_dict or not len(key_dict[bezname])) and (keyname not in key_dict or not len(key_dict[keyname])):
                continue
            ktype = Node.KEY_TYPE[attrname]
            # using a bezierkey
            if bezname in key_dict and len(key_dict[bezname]):
                keyname = bezname
            ascii_lines.append(f"    {keyname} {len(key_dict[keyname])!s}")
            for frame, key in key_dict[keyname].items():
                # convert raw frame number to animation-relative time
                time = round(utils.frame2nwtime(frame - anim.frameStart), 5)
                # orientation value conversion
                if keyname.startswith("orientation"):
                    key = utils.quat2nwangle(key[0:4])
                # export title and
                line = "      {: .7g}" + (" {: .7g}" * ktype["values"])
                s = line.format(time, *key[0 : ktype["values"]])
                # export bezierkey control points
                if keyname == bezname:
                    # left control point(s)
                    s += (" {: .7g}" * ktype["values"]).format(*key[ktype["axes"] :: 2])
                    # right control point(s)
                    s += (" {: .7g}" * ktype["values"]).format(*key[ktype["axes"] + 1 :: 2])
                ascii_lines.append(s)
        for attrname in Node.EMITTER_KEY_TYPE:
            bezname = attrname + "bezierkey"
            keyname = attrname + "key"
            if (
                (bezname not in key_dict or not len(key_dict[bezname]))
                and (keyname not in key_dict or not len(key_dict[keyname]))
            ):
                continue
            ktype = Node.EMITTER_KEY_TYPE[attrname]
            # using a bezierkey
            if bezname in key_dict and len(key_dict[bezname]):
                keyname = bezname
            ascii_lines.append(f"    {keyname} {len(key_dict[keyname])!s}")
            for frame, key in key_dict[keyname].items():
                # convert raw frame number to animation-relative time
                time = round(utils.frame2nwtime(frame - anim.frameStart), 5)
                # orientation value conversion
                # export title and
                value_str = " {: .7g}"
                if "conversion" in ktype and ktype["conversion"] is int:
                    value_str = " {: d}"
                    key[0 : ktype["values"]] = [int(k) for k in key[0 : ktype["values"]]]
                line = "      {: .7g}" + (value_str * ktype["values"])
                s = line.format(time, *key[0 : ktype["values"]])
                # export bezierkey control points
                if keyname == bezname:
                    # left control point(s)
                    s += (" {: .7g}" * ktype["values"]).format(*key[ktype["axes"] :: 2])
                    # right control point(s)
                    s += (" {: .7g}" * ktype["values"]).format(*key[ktype["axes"] + 1 :: 2])
                ascii_lines.append(s)

    @staticmethod
    def get_original_name(node_name: str, anim_name: str) -> str:
        """A bit messy due to compatibility concerns."""
        if node_name.endswith(anim_name):
            orig = node_name[: len(node_name) - len(anim_name)]
            if orig.endswith("."):
                orig = orig[: len(orig) - 1]
            return orig

        # Try to separate the name by the first '.'
        # This is unsafe, but we have no choice if we want to maintain some
        # flexibility. It will be up to the user to name the object properly
        orig = node_name.partition(".")[0]
        if orig:
            return orig

        # Couldn't find anything ? Return the string itself
        return node_name

    @staticmethod
    def export_needed(anim_obj: bpy.types.Object, anim: bpy.types.AnimData) -> bool:
        """Test whether this node should be included in exported ASCII model."""
        # this is the root node, must be included
        if anim_obj.parent is None:
            return True
        # test for object controllers, loc/rot/scale/selfillum
        objects: list[bpy.types.Object] = [anim_obj]
        try:
            # this is for light controllers, radius/color:
            if anim_obj.data:
                objects.append(anim_obj.data)
            # this is for secondary obj controller, alpha:
            if anim_obj.active_material:
                objects.append(anim_obj.active_material)
        except Exception:  # noqa: E722, BLE001
            RobustLogger().debug("XFAIL: failed to get data for " + anim_obj.name, exc_info=True)
        # test the found objects for animation controllers
        for obj in objects:
            if (
                obj.animation_data
                and obj.animation_data.action
                and obj.animation_data.action.fcurves
                and len(obj.animation_data.action.fcurves) > 0
                and len(
                    list(
                        filter(
                            lambda fc: len(
                                [
                                    kfp
                                    for kfp in fc.keyframe_points
                                    if kfp.co[0] >= anim.frameStart
                                    and kfp.co[0] <= anim.frameEnd
                                ]
                            ),
                            obj.animation_data.action.fcurves,
                        )
                    )
                )
            ):
                # this node has animation controllers, include it
                # XXX match actual controllers sometime
                # (current will match ANY animation)
                return True
        # if any children of this node will be included, this node must be
        for child in anim_obj.children:
            if Node.export_needed(child, anim):
                print("export_needed as parent for " + anim_obj.name)
                return True
        # no reason to include this node
        return False

    def to_ascii(self, anim_obj: bpy.types.Object, ascii_lines: list[str], anim_name: str):
        original_name: str = Node.get_original_name(anim_obj.name, anim_name)
        original_obj: bpy.types.Object = bpy.data.objects[original_name]

        # test whether this node should be exported,
        # previous behavior was to export all nodes for all animations
        if not Node.export_needed(anim_obj, anim):
            return

        original_parent = defines.null
        if anim_obj.parent:
            original_parent = Node.get_original_name(anim_obj.parent.name, anim_name)

        if original_obj.kb.meshtype == defines.Meshtype.EMITTER:
            ascii_lines.append("  node emitter " + original_name)
            ascii_lines.append("    parent " + original_parent)
        else:
            ascii_lines.append("  node dummy " + original_name)
            ascii_lines.append("    parent " + original_parent)
        self.add_keys_to_ascii(anim_obj, original_obj, ascii_lines)  # FIXME: missing function.
        self.add_keys_to_ascii_incompat(anim_obj, ascii_lines)
        ascii_lines.append("  endnode")


class Animnode:
    nodetype: ClassVar[NodeType | Literal["DUMMY"]] = NodeType.DUMMY

    def __init__(self, name: str = "UNNAMED"):
        self.nodeidx: int = -1
        self.name: str = name
        self.parent: str = defines.null

        self.emitter_data: dict[str, Any] = {}
        self.object_data: dict[str, Any] = {}

    def __bool__(self) -> bool:
        """Return false if the node is empty, i.e. no anims attached."""
        return bool(self.object_data or self.emitter_data)

    @staticmethod
    def insert_kfp(
        frames: list[float],
        values: list[float],
        action: bpy.types.Action,
        dp: str,
        dp_dim: int,
        action_group: str | None = None,
    ):
        if not frames or not values:
            return
        fcu: list[bpy.types.FCurve] = [
            utils.get_fcurve(action, dp, i, action_group)
            for i in range(dp_dim)
        ]
        kfp_list: list[bpy.types.FCurveKeyframePoints] = [
            fcu[i].keyframe_points
            for i in range(dp_dim)
        ]
        kfp_cnt = [len(x) for x in kfp_list]
        for x in kfp_list:
            x.add(len(values))
        for i, (frm, val) in enumerate(zip(frames, values)):
            for d in range(dp_dim):
                p: bpy.types.Keyframe = kfp_list[d][kfp_cnt[d] + i]
                p.co = (frm, val[d])
                p.interpolation = "LINEAR"
                # could do len == dp_dim * 3...
                if len(val) > dp_dim:
                    p.interpolation = "BEZIER"
                    p.handle_left_type = "FREE"
                    p.handle_right_type = "FREE"
                    # initialize left and right handle x positions
                    h_left_frame = frm - defines.fps
                    h_right_frame = frm + defines.fps
                    # adjust handle x positions based on previous/next keyframes
                    if i > 0:
                        p_left = frames[i - 1]
                        print(f" left {p_left} frm {frm}")
                        # place 1/3 into the distance from current keyframe
                        # to previous keyframe
                        h_left_frame = frm - ((frm - p_left) / 3.0)
                    if i < len(values) - 1:
                        p_right = frames[i + 1]
                        print(f"right {p_right} frm {frm}")
                        # place 1/3 into the distance from current keyframe
                        # to next keyframe
                        h_right_frame = frm + ((p_right - frm) / 3.0)
                    # set bezier handle positions,
                    # y values are relative, so added to initial value
                    p.handle_left[:] = [h_left_frame, val[d + dp_dim] + val[d]]
                    p.handle_right[:] = [h_right_frame, val[d + (2 * dp_dim)] + val[d]]
        for c in fcu:
            c.update()

    def load_ascii(
        self,
        ascii_lines: list[str],
        nodeidx: int = -1,
    ):
        self.nodeidx = nodeidx
        key_data = {}
        l_is_number = utils.is_number
        for i, line in enumerate(ascii_lines):
            try:
                label = line[0].lower()
            except (IndexError, AttributeError):  # noqa: S112
                continue  # Probably empty line, skip it
            else:
                if l_is_number(label):
                    continue
            if label == "node":
                self.nodetype = line[1].lower()
                self.name = utils.str2identifier(line[2])
            elif label == "endnode":
                return
            elif label == "parent":
                self.parentName = utils.str2identifier(line[1])
            else:  # Check for keys
                key_name = label
                key_type = ""
                if key_name.endswith("key"):
                    key_name = key_name[:-3]
                    key_type = "key"
                if key_name.endswith("bezier"):
                    key_name = key_name[:-6]
                    key_type = "bezierkey"
                if key_name in Node.KEY_TYPE or key_name in [k.lower() for k in Node.EMITTER_KEY_TYPE]:
                    attr_name = key_name
                    key_data = self.object_data
                    attr_type = None
                    if attr_name not in Node.KEY_TYPE:
                        # emitter property
                        attr_name = next(attr for attr in Node.EMITTER_KEY_TYPE if attr.lower() in label)
                        key_data = self.emitter_data
                        attr_type = Node.EMITTER_KEY_TYPE[attr_name]
                    else:
                        # object property
                        attr_type = Node.KEY_TYPE[attr_name]
                    numVals = attr_type["values"]
                    numKeys = 0
                    if key_type:
                        if key_type == "bezierkey":
                            numVals *= 3
                        numKeys = Node.find_end(ascii_lines[i + 1 :])
                        subblock = ascii_lines[i + 1 : i + numKeys + 1]
                    else:
                        numKeys = 1
                        subblock = [[0.0] + line[1:]]
                    converter = float
                    if "conversion" in attr_type:
                        converter = attr_type["conversion"]
                    key_data[key_name] = [
                        [
                            # time followed by values, for each line
                            [
                                float(v[0]),
                                *list(map(converter, v[1 : numVals + 1])),
                            ]
                            for v in subblock
                        ],
                        attr_type.get("objdata", ""),
                        numVals,
                    ]

    def create_data_object(
        self,
        obj: bpy.types.Object,
        anim: bpy.types.AnimData,
        options: dict[str, Any] | None = None,
    ):
        """Creates animations in object actions."""
        options = {} if options is None else options
        fps: int = defines.fps
        frame_start: int = anim.frameStart

        # Insert keyframes of each type
        for label, (data, data_path, data_dim) in self.object_data.items():
            frames = [fps * d[0] + frame_start for d in data]

            if obj.type == "LIGHT" and label in {"radius", "color"}:
                # For light radius and color, target the object data
                use_action = utils.get_action(obj.data, options["mdlname"] + "." + obj.name)
            else:
                # Otherwise, target the object
                use_action = utils.get_action(obj, options["mdlname"] + "." + obj.name)

            if label == "position":
                values = [d[1:4] for d in data]
                data_dim = 3  # TODO: add support for Bezier keys
            elif label == "orientation":
                quats = [utils.nwangle2quat(d[1:5]) for d in data]
                values = [quat[0:4] for quat in quats]
                data_dim = 4
            elif label == "scale":
                values = [[d[1]] * 3 for d in data]
                data_dim = 3
            else:
                values = [d[1 : data_dim + 1] for d in data]

            Animnode.insert_kfp(frames, values, use_action, data_path, data_dim)

    def create_data_emitter(
        self,
        obj: bpy.types.Object,
        anim: bpy.types.AnimData,
        options: dict[str, Any] | None = None,
    ) -> None:
        """Creates animations in emitter actions."""
        options = {} if options is None else options
        fps: int = defines.fps
        frame_start: int = anim.frameStart
        action: bpy.types.Action = utils.get_action(obj, options["mdlname"] + "." + obj.name)
        for label, (data, _, data_dim) in self.emitter_data.items():
            frames: list[float] = [fps * d[0] + frame_start for d in data]
            values: list[list[float]] = [d[1 : data_dim + 1] for d in data]
            dp: str = f"kb.{label}"
            dp_dim: int = data_dim
            Animnode.insert_kfp(
                frames,
                values,
                action,
                dp,
                dp_dim,
                "Odyssey Emitter",
            )

    @staticmethod
    def create_restpose(obj: bpy.types.Object, frame: int = 1) -> None:
        def insert_kfp(fcurves: list[bpy.types.FCurve], frame: int, val: list[float], dim: int) -> None:
            for j in range(dim):
                kf: bpy.types.Keyframe = fcurves[j].keyframe_points.insert(frame, val[j], options={"FAST"})
                kf.interpolation = "LINEAR"

        anim_data: bpy.types.AnimData | None = obj.animation_data
        if not anim_data:
            return  # No data = no animation = no need for rest pose

        action: bpy.types.Action | None = anim_data.action
        if not action:
            return  # No action = no animation = no need for rest pose

        fcu: list[bpy.types.FCurve | None] = [action.fcurves.find("rotation_quaternion", index=i) for i in range(4)]
        if fcu.count(None) < 1:
            q: Quaternion = Quaternion(obj.kb.restrot)
            insert_kfp(fcu, frame, [q.w, q.x, q.y, q.z], 4)

        fcu = [action.fcurves.find("location", index=i) for i in range(3)]
        if fcu.count(None) < 1:
            insert_kfp(fcu, frame, obj.kb.restloc, 3)

        fcu = [action.fcurves.find("scale", index=i) for i in range(3)]
        if fcu.count(None) < 1:
            insert_kfp(fcu, frame, [obj.kb.restscl] * 3, 3)

    def add_object_keyframes(
        self,
        obj: bpy.types.Object,
        anim: bpy.types.AnimData,
        options: dict[str, Any] | None = None,
    ) -> None:
        options = {} if options is None else options
        if self.object_data:
            self.create_data_object(obj, anim, options)
        if self.emitter_data:
            self.create_data_emitter(obj, anim, options)

    @staticmethod
    def generate_ascii(
        obj: bpy.types.Object,
        anim: bpy.types.AnimData,
        ascii_lines: list[str],
        options: dict[str, Any] | None = None,
    ) -> None:
        options = {} if options is None else options
        if not obj or not Node.export_needed(obj, anim):
            return
        # Type + Name
        node_type: str = "dummy"
        if obj.kb.meshtype == defines.Meshtype.EMITTER:
            node_type = "emitter"
        node_name: str = Node.get_original_name(obj.name, anim.name)
        ascii_lines.append("  node " + node_type + " " + node_name)
        # Parent
        parent_name: str = defines.null
        if obj.parent:
            parent_name = Node.get_original_name(obj.parent.name, anim.name)
        ascii_lines.append("    parent " + parent_name)
        Node.generate_ascii_keys(obj, anim, ascii_lines, options)
        ascii_lines.append("  endnode")
