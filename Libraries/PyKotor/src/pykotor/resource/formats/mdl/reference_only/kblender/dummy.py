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

from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    import bpy

    from typing_extensions import Literal

    from pykotor.resource.formats.mdl.reference_only.constants import ImportOptions

from pykotor.resource.formats.mdl.reference_only.base import BaseNode
from pykotor.resource.formats.mdl.reference_only.constants import DummyType, NodeType


class DummyNode(BaseNode):
    nodetype: ClassVar[NodeType | Literal["DUMMY"]] = NodeType.DUMMY
    dummytype: ClassVar[DummyType | Literal["NONE"]] = DummyType.NONE

    def __init__(
        self,
        name: str = "UNNAMED",
    ):
        super().__init__(name)

    def set_object_data(
        self,
        obj: bpy.types.Object,
        options: ImportOptions,
    ):
        BaseNode.set_object_data(self, obj, options)

        obj.kb.dummytype = self.dummytype

    def load_object_data(
        self,
        obj: bpy.types.Object,
        eval_obj: bpy.types.Object,
        options: ImportOptions,
    ):
        BaseNode.load_object_data(self, obj, eval_obj, options)

        self.dummytype = obj.kb.dummytype
