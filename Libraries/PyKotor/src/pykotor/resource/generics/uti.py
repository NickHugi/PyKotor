from __future__ import annotations

from copy import deepcopy
from functools import wraps
from typing import TYPE_CHECKING, Any, TypeVar

from pykotor.common.misc import Game
from pykotor.resource.formats.gff import GFF, GFFContent, read_gff, write_gff
from pykotor.resource.formats.gff.gff_auto import bytes_gff
from pykotor.resource.formats.gff.gff_data import FieldProperty, GFFFieldType, GFFStructInterface
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.common.language import LocalizedString
    from pykotor.common.misc import ResRef
    from pykotor.resource.formats.gff import GFFList
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
class UTI(GFFStructInterface):
    """Stores item data."""

    BINARY_TYPE = ResourceType.UTI

    resref: FieldProperty[ResRef, ResRef] = FieldProperty("TemplateResRef", GFFFieldType.ResRef)
    base_item: FieldProperty[int, int] = FieldProperty("BaseItem", GFFFieldType.Int32)
    name: FieldProperty[LocalizedString, LocalizedString] = FieldProperty("LocalizedName", GFFFieldType.LocalizedString)
    description: FieldProperty[LocalizedString, LocalizedString] = FieldProperty("DescIdentified", GFFFieldType.LocalizedString)
    tag: FieldProperty[str, str] = FieldProperty("Tag", GFFFieldType.String)
    charges: FieldProperty[int, int] = FieldProperty("Charges", GFFFieldType.UInt8)
    cost: FieldProperty[int, int] = FieldProperty("Cost", GFFFieldType.UInt32)
    stack_size: FieldProperty[int, int] = FieldProperty("StackSize", GFFFieldType.UInt16)
    plot: FieldProperty[int, int] = FieldProperty("Plot", GFFFieldType.UInt8)
    add_cost: FieldProperty[int, int] = FieldProperty("AddCost", GFFFieldType.UInt32)
    palette_id: FieldProperty[int, int] = FieldProperty("PaletteID", GFFFieldType.UInt8)
    comment: FieldProperty[str, str] = FieldProperty("Comment", GFFFieldType.String)
    properties: FieldProperty[GFFList[GFFStruct], GFFList[UTIProperty]] = FieldProperty("PropertiesList", GFFFieldType.List)

    # Armor Items Only:
    model_variation: FieldProperty[int, int] = FieldProperty("ModelVariation", GFFFieldType.UInt8)
    body_variation: FieldProperty[int, int] = FieldProperty("BodyVariation", GFFFieldType.UInt8)
    texture_variation: FieldProperty[int, int] = FieldProperty("TextureVar", GFFFieldType.UInt8)

    # KOTOR 2 Specific Fields
    upgrade_level: FieldProperty[int, int] = FieldProperty("UpgradeLevel", GFFFieldType.UInt8, game=Game.K2)

    # Deprecated:
    stolen: FieldProperty[int, int] = FieldProperty("Stolen", GFFFieldType.UInt8)
    identified: FieldProperty[int, int] = FieldProperty("Identified", GFFFieldType.UInt8)

    def __init__(
        self,
    ):
        super().__init__()
        #self._fields: UTIFields

    def is_armor(  # TODO(th3w1zard1): Accept a TwoDA object argument instead of hardcoding the base item numbers
        self,
    ) -> bool:
        return self._fields["BaseItem"] in ARMOR_BASE_ITEMS


class UTIProperty(GFFStructInterface):
    cost_table = FieldProperty("CostTable", GFFFieldType.UInt8)
    cost_value = FieldProperty("CostValue", GFFFieldType.UInt16)
    param1 = FieldProperty("Param1", GFFFieldType.UInt8)
    param1_value = FieldProperty("Param1Value", GFFFieldType.UInt8)
    property_name = FieldProperty("PropertyName", GFFFieldType.UInt16)
    subtype = FieldProperty("Subtype", GFFFieldType.UInt16)
    chance_appear = FieldProperty("ChanceAppear", GFFFieldType.UInt8)
    upgrade_type = FieldProperty("UpgradeType", GFFFieldType.UInt8)

    def __init__(
        self,
    ):
        super().__init__(struct_id=0)


def construct_uti(
    gff: GFF,
) -> UTI:
    uti: UTI = deepcopy(gff.root)
    uti.__class__ = UTI
    for property_struct in uti._fields["PropertiesList"].value():
        property_struct.__class__ = UTIProperty
    return uti


def dismantle_uti(
    uti: UTI,
    game: Game = Game.K2,
    *,
    use_deprecated: bool = True,
) -> GFF:
    gff = GFF(GFFContent.UTI)
    gff.root = uti.unwrap()
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
