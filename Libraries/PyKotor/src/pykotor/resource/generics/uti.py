from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Any, ClassVar, Type, TypeVar

from pykotor.common.language import LocalizedString
from pykotor.common.misc import Game, ResRef
from pykotor.resource.formats.gff import GFF, GFFContent, GFFList, read_gff, write_gff
from pykotor.resource.formats.gff.gff_auto import bytes_gff
from pykotor.resource.formats.gff.gff_data import GFFFieldType, FieldGFF, GFFStructInterface
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFFStruct
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES

ARMOR_BASE_ITEMS = {35, 36, 37, 38, 39, 40, 41, 42, 43, 53, 58, 63, 64, 65, 69, 71, 85, 89, 98, 100, 102, 103}
""" Base Item IDs that are considered armor as per the 2DA files. """

T = TypeVar("T")

def typed_property(name: str, type_: T) -> Any:
    """Creates a typed property that allows static type checkers to correctly infer the type."""

    @property
    @wraps(typed_property, assigned=("__annotations__",))
    def prop(self: GFFStruct) -> T:
        return self.acquire(name, self.FIELDS[name]._value())

    @prop.setter
    def prop(self: GFFStruct, value: T) -> None:
        self.set(name, value)

    prop.__annotations__ = {"return": type_}
    return prop

def add_typed_properties(cls):
    """Class decorator that dynamically adds typed properties based on FIELDS and K2_FIELDS definitions."""
    for name, field in cls.FIELDS.items():
        setattr(cls, name, typed_property(name, field.field_type().return_type()))

    if hasattr(cls, "K2_FIELDS"):
        for name, field in cls.K2_FIELDS.items():
            setattr(cls, name, typed_property(name, field.field_type().return_type()))

    return cls

#@add_typed_properties
class UTI:
    """Stores item data."""

    BINARY_TYPE = ResourceType.UTI

    FIELDS: ClassVar[dict[str, FieldGFF]] = {
        "TemplateResRef": FieldGFF(GFFFieldType.ResRef, ResRef.from_blank()),
        "BaseItem": FieldGFF(GFFFieldType.UInt32, 0),
        "LocalizedName": FieldGFF(GFFFieldType.LocalizedString, LocalizedString.from_invalid()),
        "DescIdentified": FieldGFF(GFFFieldType.LocalizedString, LocalizedString.from_invalid()),
        "Tag": FieldGFF(GFFFieldType.String, ""),
        "Charges": FieldGFF(GFFFieldType.UInt32, 0),
        "Cost": FieldGFF(GFFFieldType.UInt32, 0),
        "StackSize": FieldGFF(GFFFieldType.UInt32, 0),
        "Plot": FieldGFF(GFFFieldType.UInt8, 0),
        "AddCost": FieldGFF(GFFFieldType.UInt32, 0),
        "PaletteID": FieldGFF(GFFFieldType.UInt8, 0),
        "Comment": FieldGFF(GFFFieldType.String, ""),
        "ModelVariation": FieldGFF(GFFFieldType.UInt8, 0),
        "BodyVariation": FieldGFF(GFFFieldType.UInt8, 0),
        "TextureVar": FieldGFF(GFFFieldType.UInt8, 0),
    }

    K2_FIELDS: ClassVar[dict[str, FieldGFF]] = {
        # Add K2-specific fields here, following the DLGLink example
        "UpgradeLevel": FieldGFF(GFFFieldType.UInt8, 0),
        "Stolen": FieldGFF(GFFFieldType.UInt8, 0),
        "Identified": FieldGFF(GFFFieldType.UInt8, 0),
    }

    def __init__(
        self,
    ):
        super().__init__()
        self.TemplateResRef: ResRef
        self.BaseItem: int
        self.LocalizedName: LocalizedString
        self.DescIdentified: LocalizedString
        self.Tag: str
        self.Charges: int
        self.Cost: int
        self.StackSize: int
        self.Plot: int
        self.AddCost: int
        self.PaletteID: int
        self.Comment: str

        self.UpgradeLevel: int

        self.PropertiesList: GFFList[UTIProperty]

        # Armor Items Only:
        self.BodyVariation: int
        self.ModelVariation: int
        self.TextureVar: int

        # Deprecated:
        self.Stolen: int
        self.Identified: int

    def is_armor(
        self,
    ) -> bool:
        return self.BaseItem in ARMOR_BASE_ITEMS


class UTIProperty(GFFStructInterface):

    FIELDS: ClassVar[dict[str, FieldGFF]] = {
        "CostTable": FieldGFF(GFFFieldType.UInt8, 0),
        "CostValue": FieldGFF(GFFFieldType.UInt16, 0),
        "Param1": FieldGFF(GFFFieldType.UInt8, 0),
        "Param1Value": FieldGFF(GFFFieldType.UInt8, 0),
        "PropertyName": FieldGFF(GFFFieldType.UInt16, 0),
        "Subtype": FieldGFF(GFFFieldType.UInt16, 0),
        "ChanceAppear": FieldGFF(GFFFieldType.UInt8, 100),
        "UpgradeType": FieldGFF(GFFFieldType.UInt8, 0),
    }
    def __init__(
        self,
    ):
        super().__init__()
    @property
    def cost_table(self) -> int:
        return self.acquire("CostTable", self.CostTable)

    @cost_table.setter
    def cost_table(self, value: int):
        self.CostTable = value

    @property
    def cost_value(self) -> int:
        return self.acquire("CostValue", self.CostValue)

    @cost_value.setter
    def cost_value(self, value: int):
        self.CostValue = value

    @property
    def param1(self) -> int:
        return self.acquire("Param1", self.Param1)

    @param1.setter
    def param1(self, value: int):
        self.Param1 = value

    @property
    def param1_value(self) -> int:
        return self.acquire("Param1Value", self.Param1Value)

    @param1_value.setter
    def param1_value(self, value: int):
        self.Param1Value = value

    @property
    def property_name(self) -> int:
        return self.acquire("PropertyName", self.PropertyName)

    @property_name.setter
    def property_name(self, value: int):
        self.PropertyName = value

    @property
    def subtype(self) -> int:
        return self.acquire("Subtype", self.Subtype)

    @subtype.setter
    def subtype(self, value: int):
        self.Subtype = value

    @property
    def chance_appear(self) -> int:
        return self.acquire("ChanceAppear", self.ChanceAppear)

    @chance_appear.setter
    def chance_appear(self, value: int):
        self.ChanceAppear = value

    @property
    def upgrade_type(self) -> int:
        return self.acquire("UpgradeType", self.UpgradeType)

    @upgrade_type.setter
    def upgrade_type(self, value: int):
        self.UpgradeType = value

def construct_uti(
    gff: GFF,
) -> UTI:
    uti = UTI()

    root = gff.root
    uti.resref = root.acquire("TemplateResRef", ResRef.from_blank())
    uti.base_item = root.acquire("BaseItem", 0)
    uti.name = root.acquire("LocalizedName", LocalizedString.from_invalid())
    uti.description = root.acquire("DescIdentified", LocalizedString.from_invalid())
    uti.tag = root.acquire("Tag", "")
    uti.charges = root.acquire("Charges", 0)
    uti.cost = root.acquire("Cost", 0)
    uti.stack_size = root.acquire("StackSize", 0)
    uti.plot = root.acquire("Plot", 0)
    uti.add_cost = root.acquire("AddCost", 0)
    uti.palette_id = root.acquire("PaletteID", 0)
    uti.comment = root.acquire("Comment", "")
    uti.model_variation = root.acquire("ModelVariation", 0)
    uti.body_variation = root.acquire("BodyVariation", 0)
    uti.texture_variation = root.acquire("TextureVar", 0)
    uti.upgrade_level = root.acquire("UpgradeLevel", 0)
    uti.stolen = root.acquire("Stolen", 0)
    uti.identified = root.acquire("Identified", 0)

    for property_struct in root.acquire("PropertiesList", GFFList()):
        prop = UTIProperty()
        uti.properties.append(prop)
        prop.cost_table = property_struct.acquire("CostTable", 0)
        prop.cost_value = property_struct.acquire("CostValue", 0)
        prop.param1 = property_struct.acquire("Param1", 0)
        prop.param1_value = property_struct.acquire("Param1Value", 0)
        prop.property_name = property_struct.acquire("PropertyName", 0)
        prop.subtype = property_struct.acquire("Subtype", 0)
        prop.chance_appear = property_struct.acquire("ChanceAppear", 100)

        if property_struct.exists("UpgradeType"):
            prop.upgrade_type = property_struct.acquire("UpgradeType", 0)

    return uti


def dismantle_uti(
    uti: UTI,
    game: Game = Game.K2,
    *,
    use_deprecated: bool = True,
) -> GFF:
    gff = GFF(GFFContent.UTI)

    root = gff.root
    root.set_resref("TemplateResRef", uti.resref)
    root.set_int32("BaseItem", uti.base_item)
    root.set_locstring("LocalizedName", uti.name)
    root.set_locstring("Description", uti.description)
    root.set_locstring("DescIdentified", uti.description)
    root.set_string("Tag", uti.tag)
    root.set_uint8("Charges", uti.charges)
    root.set_uint32("Cost", uti.cost)
    root.set_uint16("StackSize", uti.stack_size)
    root.set_uint8("Plot", uti.plot)
    root.set_uint32("AddCost", uti.add_cost)
    root.set_uint8("PaletteID", uti.palette_id)
    root.set_string("Comment", uti.comment)

    properties_list: GFFList = root.set_list("PropertiesList", GFFList())
    for prop in uti.properties:
        properties_struct = properties_list.add(0)
        properties_struct.set_uint8("CostTable", prop.cost_table)
        properties_struct.set_uint16("CostValue", prop.cost_value)
        properties_struct.set_uint8("Param1", prop.param1)
        properties_struct.set_uint8("Param1Value", prop.param1_value)
        properties_struct.set_uint16("PropertyName", prop.property_name)
        properties_struct.set_uint16("Subtype", prop.subtype)
        properties_struct.set_uint8("ChanceAppear", prop.chance_appear)
        if prop.upgrade_type is not None:
            properties_struct.set_uint8("UpgradeType", prop.upgrade_type)

    root.set_uint8("ModelVariation", uti.model_variation)
    root.set_uint8("BodyVariation", uti.body_variation)
    root.set_uint8("TextureVar", uti.texture_variation)

    if game.is_k2():
        root.set_uint8("UpgradeLevel", uti.upgrade_level)

    if use_deprecated:
        root.set_uint8("Stolen", uti.stolen)
        root.set_uint8("Identified", uti.identified)

    return gff


def read_uti(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
) -> UTI:
    gff = read_gff(source, offset, size)
    return construct_uti(gff)


def write_uti(
    uti: UTI,
    target: TARGET_TYPES,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
):
    gff = dismantle_uti(uti, game, use_deprecated=use_deprecated)
    write_gff(gff, target, file_format)


def bytes_uti(
    uti: UTI,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
) -> bytes:
    gff = dismantle_uti(uti, game, use_deprecated=use_deprecated)
    return bytes_gff(gff, file_format)
