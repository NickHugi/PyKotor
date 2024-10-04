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
import re

from typing import TYPE_CHECKING

from pykotor.resource.formats.mdl.reference_only.animnode import AnimationNode
from pykotor.resource.formats.mdl.reference_only.constants import ANIM_PADDING, NULL, DummyType
from pykotor.resource.formats.mdl.reference_only.utils import find_object, frame_to_time, time_to_frame

if TYPE_CHECKING:
    import bpy

    from typing_extensions import Literal

    from pykotor.resource.formats.mdl.mdl_data import MDL, MDLAnimation


class Animation:
    def __init__(self, name: str = "UNNAMED"):
        self.name: str = name
        self.length: float = 1.0
        self.transtime: float = 0.25
        self.animroot: int = NULL
        self.root_node: AnimationNode | None = None

        self.events: list[tuple[float, str]] = []

    def add_to_objects(self, mdl_root: MDL, animscale: float):
        list_anim = Animation.append_to_object(mdl_root, self.name, self.length, self.transtime, self.animroot)
        for time, name in self.events:
            Animation.append_event_to_object_anim(list_anim, name, time)

        self.add_nodes_to_objects(list_anim, self.root_node, mdl_root, animscale)

    def add_nodes_to_objects(
        self,
        anim: MDLAnimation,
        node: AnimationNode,
        mdl_root,
        animscale: float,
        below_animroot: bool = False,
    ):
        obj = find_object(mdl_root, lambda o: o.kb.node_number == node.node_number)
        if obj:
            if not below_animroot and obj.name.lower() == mdl_root.kb.animroot.lower():
                below_animroot = True
            if below_animroot:
                node.add_keyframes_to_object(anim, obj, mdl_root.name, animscale)

        for child in node.children:
            self.add_nodes_to_objects(anim, child, mdl_root, animscale, below_animroot)

    @classmethod
    def append_to_object(
        cls,
        mdl_root,
        name: str,
        length: float = 0.0,
        transtime: float = 0.25,
        animroot: Literal["NULL"] = "NULL",
    ):
        anim: MDLAnimation = mdl_root.kb.anim_list.add()
        anim.name = name
        anim.root = animroot
        anim.transtime = transtime
        anim.frame_start = Animation.get_next_frame(mdl_root)
        anim.frame_end = anim.frame_start + time_to_frame(length)
        return anim

    @classmethod
    def append_event_to_object_anim(cls, list_anim: MDLAnimation, name: str, time: float):
        event = list_anim.event_list.add()
        event.name = name
        event.frame = list_anim.frame_start + time_to_frame(time)

    @classmethod
    def get_next_frame(cls, mdl_root: MDL) -> int:
        last_frame = max([a.frame_end for a in mdl_root.kb.anim_list])
        return int(math.ceil((last_frame + ANIM_PADDING) / 10.0)) * 10

    @classmethod
    def from_list_anim(cls, list_anim: MDLAnimation, mdl_root: MDL) -> Animation:
        anim = Animation(list_anim.name)
        anim.length = frame_to_time(list_anim.frame_end - list_anim.frame_start)
        anim.transtime = list_anim.transtime
        anim.animroot = list_anim.root
        anim.root_node = Animation.animation_node_from_object(list_anim, mdl_root)

        for event in list_anim.event_list:
            time = frame_to_time(event.frame - list_anim.frame_start)
            name = event.name
            anim.events.append((time, name))

        return anim

    @classmethod
    def animation_node_from_object(
        cls,
        anim: MDLAnimation,
        obj: bpy.types.Object,
        parent: bpy.types.Object | None = None,
    ) -> AnimationNode:
        name = obj.name
        if re.match(r".+\.\d{3}$", name):
            name = name[:-4]

        node = AnimationNode(name)
        node.node_number = obj.kb.node_number
        node.parent = parent

        node.load_keyframes_from_object(anim, obj)
        if obj.type == "LIGHT":
            node.load_keyframes_from_object(anim, obj.data)
        node.animated = bool(node.keyframes)

        for child_obj in sorted(obj.children, key=lambda o: o.kb.export_order):
            if child_obj.type == "EMPTY" and child_obj.kb.dummytype in [
                DummyType.PWKROOT,
                DummyType.DWKROOT,
            ]:
                continue
            child = Animation.animation_node_from_object(anim, child_obj, node)
            if not node.animated and child.animated:
                node.animated = True
            node.children.append(child)

        return node
