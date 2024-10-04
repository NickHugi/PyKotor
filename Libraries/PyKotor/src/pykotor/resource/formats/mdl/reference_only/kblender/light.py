from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Tuple, cast

from pykotor.common.misc import Color

if TYPE_CHECKING:

    from typing_extensions import Literal

    from pykotor.resource.formats.mdl.reference_only.constants import ImportOptions, NodeType


import bpy

from pykotor.resource.formats.mdl.reference_only.base import BaseNode
from pykotor.resource.formats.mdl.reference_only.constants import NodeType


class FlareList:
    def __init__(self):
        self.textures: list[str] = []
        self.sizes: list[float] = []
        self.positions: list[float] = []
        self.colorshifts: list[float] = []


class LightNode(BaseNode):
    def __init__(self, name="UNNAMED"):
        super().__init__(name)
        self.nodetype: ClassVar[NodeType | Literal["LIGHT"]] = NodeType.LIGHT

        self.shadow: int = 1
        self.radius: float = 5.0
        self.multiplier: float = 1
        self.lightpriority: int = 5
        self.color: Color = Color(0.0, 0.0, 0.0)
        self.ambientonly: int = 1
        self.dynamictype: int = 0
        self.affectdynamic: int = 1
        self.fadinglight: int = 1
        self.lensflares: int = 0
        self.flareradius: float = 1.0

        self.flare_list = FlareList()

    def add_to_collection(
        self,
        collection: bpy.types.Collection,
        options: ImportOptions,
    ) -> bpy.types.Object:
        light = self.create_light(self.name)
        obj = bpy.data.objects.new(self.name, light)
        self.set_object_data(obj, options)
        collection.objects.link(obj)
        return obj

    def create_light(self, name: str) -> bpy.types.Light:
        negative = any(
            c < 0
            for c in (
                self.color.r,
                self.color.g,
                self.color.b,
            )
        )
        light = bpy.data.lights.new(name, "POINT")
        light.color = (
            (-c if negative else c)
            for c in (
                self.color.r,
                self.color.g,
                self.color.b,
                self.color.a,
            )
        )
        light.use_shadow = self.shadow >= 1
        if self.shadow:
            light.use_contact_shadow = True
            light.contact_shadow_distance = self.radius
        return light

    def set_object_data(
        self,
        obj: bpy.types.Object,
        options: ImportOptions,
    ):
        super().set_object_data(obj, options)

        obj.kb.multiplier = self.multiplier
        obj.kb.radius = self.radius
        obj.kb.ambientonly = self.ambientonly >= 1
        obj.kb.shadow = self.shadow >= 1
        obj.kb.lightpriority = self.lightpriority
        obj.kb.fadinglight = self.fadinglight >= 1
        obj.kb.dynamictype = self.dynamictype
        obj.kb.affectdynamic = self.affectdynamic >= 1
        obj.kb.flareradius = self.flareradius
        obj.kb.negativelight = any(
            c < 0.0
            for c in (
                self.color.r,
                self.color.g,
                self.color.b,
                self.color.a,
            )
        )

        if self.flareradius > 0 or self.lensflares >= 1:
            obj.kb.lensflares = 1
            num_flares = len(self.flare_list.textures)
            for i in range(num_flares):
                newItem = obj.kb.flare_list.add()
                newItem.texture = self.flare_list.textures[i]
                newItem.colorshift = self.flare_list.colorshifts[i]
                newItem.size = self.flare_list.sizes[i]
                newItem.position = self.flare_list.positions[i]

        LightNode.calc_light_power(obj)

    def load_object_data(
        self,
        obj: bpy.types.Object,
        eval_obj: bpy.types.Object,
        options: ImportOptions,
    ):
        super().load_object_data(obj, eval_obj, options)

        self.color = Color(
            *[
                (-c if obj.kb.negativelight else c)
                for c in cast(
                    Tuple[float, float, float],
                    obj.data.color[:3]
                )
            ]
        )
        self.multiplier = obj.kb.multiplier
        self.radius = obj.kb.radius
        self.ambientonly = 1 if obj.kb.ambientonly else 0
        self.shadow = 1 if obj.kb.shadow else 0
        self.lightpriority = obj.kb.lightpriority
        self.fadinglight = 1 if obj.kb.fadinglight else 0
        self.dynamictype = obj.kb.dynamictype
        self.affectdynamic = 1 if obj.kb.affectdynamic else 0
        self.flareradius = obj.kb.flareradius
        self.negativelight = 1 if obj.kb.negativelight else 0

        if obj.kb.lensflares:
            self.lensflares = 1
            for item in obj.kb.flare_list:
                self.flare_list.textures.append(item.texture)
                self.flare_list.sizes.append(item.size)
                self.flare_list.positions.append(item.position)
                self.flare_list.colorshifts.append(item.colorshift)

    @classmethod
    def calc_light_power(
        cls,
        light: bpy.types.Object,
    ):
        if light.kb.negativelight:
            light.data.energy = 0
        else:
            light.data.energy = (
                light.kb.multiplier
                * light.kb.radius
                * light.kb.radius
            )
