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

import collections

from typing import TYPE_CHECKING, Any

from loggerplus import RobustLogger

from pykotor.resource.formats.mdl.reference_only.ascii import animnode
from pykotor.resource.formats.mdl.reference_only.constants import defines, utils
from pykotor.resource.formats.mdl.reference_only.exception.malformedmdl import MalformedMdl

if TYPE_CHECKING:
    import bpy

    from pykotor.resource.formats.mdl.reference_only.ascii.animnode import AnimationNode


class Animation:
    def __init__(self, name: str = "UNNAMED", ascii_data: str | None = None):
        self.name: str = name
        self.length: float = 1.0
        self.transtime: float = 1.0
        self.animroot: str = defines.null
        self.eventList: list[tuple[float, str]] = []
        self.nodeList: collections.OrderedDict[str, AnimationNode] = collections.OrderedDict()

        self.nodes: list[AnimationNode] = []
        self.events: list[tuple[float, str]] = []

        if ascii_data:
            self.load_ascii(ascii_data)

    def add_to_objects(self, mdl_root: MdlRoot):
        list_anim = self._create_list_anim(mdl_root)
        self._add_events_to_list_anim(list_anim)
        obj_by_node = self._associate_node_to_object(mdl_root)

        # Add object keyframes
        for node in self.nodes:
            if node.name.lower() in obj_by_node:
                obj = obj_by_node[node.name.lower()]
                node.add_object_keyframes(obj, list_anim, {"mdlname": mdl_root.name})
                self._create_rest_pose(obj, list_anim.frameStart - 5)

    def _create_list_anim(self, mdl_root: MdlRoot):
        result = utils.create_anim_list_item(mdl_root)
        result.name = self.name
        result.transtime = defines.fps * self.transtime
        result.root = result.root_obj = self._get_anim_target(mdl_root).name
        result.frameEnd = utils.nwtime2frame(self.length) + result.frameStart
        return result

    def _get_anim_target(self, mdl_root: MdlRoot):
        result = utils.search_node(mdl_root, lambda o, name=self.animroot: o.name.lower() == name.lower())
        if not result:
            result = mdl_root
            print(f"KotorBlender: animation retargeted from {self.animroot} to {mdl_root.name}")
        return result

    def _add_events_to_list_anim(self, list_anim):
        for time, name in self.events:
            event = list_anim.eventList.add()
            event.name = name
            event.frame = utils.nwtime2frame(time) + list_anim.frameStart

    def _associate_node_to_object(self, mdl_root: MdlRoot):
        result = dict()
        for node in self.nodes:
            obj = utils.search_node(mdl_root, lambda o, name=node.name: o.name.lower() == name.lower())
            if obj:
                result[node.name.lower()] = obj
        return result

    def _create_rest_pose(self, obj, frame=1):
        animnode.Animnode.create_restpose(obj, frame)

    def add_ascii_node(self, ascii_block: list[list[str]]):
        node = animnode.Node()
        node.load_ascii(ascii_block)
        key = node.parentName + node.name
        if key in self.nodeList:
            RobustLogger().debug("TODO: Should probably raise an exception")
            return
        self.nodeList[key] = node

    def add_event(self, event: tuple[float, str]):
        self.eventList.append(event)

    def get_anim_from_ascii(self, ascii_block: list[list[str]]):
        blockStart = -1
        for idx, line in enumerate(ascii_block):
            try:
                label = line[0].lower()
            except IndexError as e:
                RobustLogger().debug("Probably empty line or whatever, skip it", exc_info=True)
                continue
            if label == "newanim":
                self.name = utils.get_name(line[1])
            elif label == "length":
                self.length = float(line[1])
            elif label == "transtime":
                self.transtime = float(line[1])
            elif label == "animroot":
                try:
                    self.animroot = line[1]
                except Exception:
                    RobustLogger().debug("No animroot specified, using 'undefined'", exc_info=True)
                    self.animroot = "undefined"
            elif label == "event":
                self.add_event((float(line[1]), line[2]))
            elif label == "eventlist":
                numEvents = next((i for i, v in enumerate(ascii_block[idx + 1 :]) if not utils.is_number(v[0])), -1)
                list(map(self.add_event, ((float(v[0]), v[1]) for v in ascii_block[idx + 1 : idx + 1 + numEvents])))
            elif label == "node":
                blockStart = idx
            elif label == "endnode":
                if blockStart > 0:
                    self.add_ascii_node(ascii_block[blockStart : idx + 1])
                    blockStart = -1
                elif label == "node":
                    raise MalformedMdl("Unexpected 'endnode'")

    def load_ascii(self, ascii_data: str):
        """Load an animation from a block from an ascii mdl file."""
        self.get_anim_from_ascii([line.strip().split() for line in ascii_data.splitlines()])
        animNodesStart: int = ascii_data.find("node ")
        if animNodesStart > -1:
            self.load_ascii_anim_header(ascii_data[: animNodesStart - 1])
            self.load_ascii_anim_nodes(ascii_data[animNodesStart:])
        else:
            print("NeverBlender - WARNING: Failed to load an animation.")

    def load_ascii_anim_header(self, ascii_data):
        ascii_lines = [l.strip().split() for l in ascii_data.splitlines()]
        for line in ascii_lines:
            try:
                label = line[0].lower()
            except (IndexError, AttributeError):
                RobustLogger().debug("Probably empty line, skip it", exc_info=True)
                continue  # Probably empty line, skip it
            if label == "newanim":
                self.name = utils.str2identifier(line[1])
            elif label == "length":
                self.length = float(line[1])
            elif label == "transtime":
                self.transtime = float(line[1])
            elif label == "animroot":
                try:
                    self.animroot = line[1].lower()
                except (ValueError, IndexError):
                    self.animroot = ""
            elif label == "event":
                self.events.append((float(line[1]), line[2]))

    def load_ascii_anim_nodes(self, ascii_data: str):
        dlm = "node "
        node_list = [dlm + s for s in ascii_data.split(dlm) if s != ""]
        for idx, ascii_node in enumerate(node_list):
            ascii_lines = [line.strip().split() for line in ascii_node.splitlines()]
            node = animnode.Animnode()
            node.load_ascii(ascii_lines, idx)
            self.nodes.append(node)

    def anim_node_to_ascii(self, b_object: bpy.types.Object, ascii_lines: list[str]):
        node = animnode.Node()
        node.to_ascii(b_object, ascii_lines, self.name)

        # If this mdl was imported, we need to retain the order of the
        # objects in the original mdl file. Unfortunately this order is
        # seemingly arbitrary so we need to save it at import
        # Otherwise supermodels don't work correctly.
        childList = [
            (child.kb.imporder, child)
            for child in b_object.children
        ]
        childList.sort(key=lambda tup: tup[0])

        for _, child in childList:
            self.anim_node_to_ascii(child, ascii_lines)

    @staticmethod
    def generate_ascii_nodes(obj: bpy.types.Object, anim: Animation, ascii_lines: list[str], options: dict[str, Any]):
        animnode.Animnode.generate_ascii(obj, anim, ascii_lines, options)

        # Sort children to restore original order before import
        # (important for supermodels/animations to work)
        children = list(obj.children)
        children.sort(key=lambda c: c.name)
        children.sort(key=lambda c: c.kb.imporder)
        for c in children:
            Animation.generate_ascii_nodes(c, anim, ascii_lines, options)

    @staticmethod
    def generate_ascii(
        anim_root_dummy: bpy.types.Object,
        anim,
        ascii_lines: list[str],
        options: dict[str, Any],
    ):
        ascii_lines.append(f"newanim {anim.name} {anim_root_dummy.name}")
        ascii_lines.append(f"  length {round((anim.frameEnd - anim.frameStart)/defines.fps, 5)}")
        ascii_lines.append(f"  transtime {round(anim.ttime, 3)}")
        ascii_lines.append(f"  animroot {anim.root}")
        # Get animation events
        for event in anim.eventList:
            event_time = (event.frame - anim.frameStart) / defines.fps
            ascii_lines.append(f"  event {round(event_time, 3)} {event.name}")

        Animation.generate_ascii_nodes(anim_root_dummy, anim, ascii_lines, options)

        ascii_lines.append(f"doneanim {anim.name} {anim_root_dummy.name}")
        ascii_lines.append("")

    def to_ascii(
        self,
        anim_scene: bpy.types.Scene,
        anim_root_dummy,
        ascii_lines: list[str],
        mdl_name: str = "",
    ):
        self.name = anim_root_dummy.kb.animname
        self.length = utils.frame2nwtime(anim_scene.frame_end, anim_scene.render.fps)
        self.transtime = anim_root_dummy.kb.transtime
        self.animroot = anim_root_dummy.kb.animroot

        ascii_lines.append("newanim " + self.name + " " + mdl_name)
        ascii_lines.append("  length " + str(round(self.length, 5)))
        ascii_lines.append("  transtime " + str(round(self.transtime, 3)))
        ascii_lines.append("  animroot " + self.root)

        for event in anim_root_dummy.kb.eventList:
            eventTime = utils.frame2nwtime(event.frame, anim_scene.render.fps)
            ascii_lines.append("  event " + str(round(eventTime, 5)) + " " + event.name)

        self.anim_node_to_ascii(anim_root_dummy, ascii_lines)
        ascii_lines.append("doneanim " + self.name + " " + mdl_name)
        ascii_lines.append("")
