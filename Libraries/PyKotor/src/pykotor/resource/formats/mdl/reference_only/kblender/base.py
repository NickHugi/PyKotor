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

from typing import TYPE_CHECKING, Callable

import bpy

from mathutils import Matrix, Quaternion
from typing_extensions import Literal

from pykotor.resource.formats.mdl.reference_only.constants import RootType

if TYPE_CHECKING:
    from pykotor.resource.formats.mdl.mdl_data import MDL
    from pykotor.resource.formats.mdl.reference_only.constants import ImportOptions


class BaseNode:
    def __init__(
        self,
        name: str = "UNNAMED",
    ):
        self.nodetype: Literal["undefined"] = "undefined"
        self.roottype: Literal["MODEL"] = RootType.MODEL

        self.node_number: int = -1
        self.export_order: int = 0
        self.name: str = name
        self.position: tuple[float, float, float] = (0.0, 0.0, 0.0)
        self.orientation: tuple[float, float, float, float] = (1.0, 0.0, 0.0, 0.0)
        self.scale: float = 1.0

        self.parent: BaseNode | None = None
        self.children: list[BaseNode] = []
        self.from_root: Matrix = Matrix()

    def add_to_collection(
        self,
        collection: bpy.types.Collection,
        options: ImportOptions,
    ) -> bpy.types.Object:
        obj = bpy.data.objects.new(self.name, None)
        self.set_object_data(obj, options)
        collection.objects.link(obj)
        return obj

    def set_object_data(
        self,
        obj: bpy.types.Object,
        options: ImportOptions,
    ):
        obj.kb.node_number = self.node_number
        obj.kb.export_order = self.export_order
        obj.location = self.position
        obj.rotation_mode = "QUATERNION"
        obj.rotation_quaternion = Quaternion(self.orientation)
        obj.scale = (self.scale, self.scale, self.scale)

    def load_object_data(
        self,
        obj: MDL,
        eval_obj: MDL,
        options: ImportOptions,
    ):
        if obj.kb.node_number == -1:
            raise RuntimeError(f"Object '{obj.name}' node number is undefined")
        self.node_number = obj.kb.node_number
        self.export_order = obj.kb.export_order
        self.position = eval_obj.location
        if eval_obj.rotation_mode != "QUATERNION":
            raise RuntimeError(
                f"Object '{eval_obj.name}' must have Quaternion rotation mode"
            )
        self.orientation = eval_obj.rotation_quaternion
        self.scale = eval_obj.scale[0]

        self.from_root = eval_obj.matrix_local
        if self.parent:
            self.from_root = self.parent.from_root @ self.from_root

    def find_node(
        self,
        test: Callable[[BaseNode], bool],
    ) -> BaseNode | None:
        if test(self):
            return self
        for child in self.children:
            if test(child):
                return child
        return None
