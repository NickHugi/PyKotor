from __future__ import annotations

from pykotor.common.language import LocalizedString
from pykotor.common.misc import Game, ResRef
from pykotor.resource.formats.gff import GFF, GFFContent, GFFList, read_gff, write_gff
from pykotor.resource.formats.gff.gff_auto import bytes_gff
from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES, ResourceType

ARMOR_BASE_ITEMS = {
    35,
    36,
    37,
    38,
    39,
    40,
    41,
    42,
    43,
    53,
    58,
    63,
    64,
    65,
    69,
    71,
    85,
    89,
    98,
    100,
    102,
    103,
}
""" Base Item IDs that are considered armor as per the 2DA files. """


class UTI:
    """Stores item data."""

    BINARY_TYPE = ResourceType.UTI

    def __init__(
        self,
    ) -> None:
        self.resref: ResRef = ResRef.from_blank()
        self.base_item: int = 0
        self.name: LocalizedString = LocalizedString.from_invalid()
        self.description: LocalizedString = LocalizedString.from_invalid()
        self.tag: str = ""
        self.charges: int = 0
        self.cost: int = 0
        self.stack_size: int = 0
        self.plot: int = 0
        self.add_cost: int = 0
        self.palette_id: int = 0
        self.comment: str = ""

        self.upgrade_level: int = 0

        self.properties: list[UTIProperty] = []

        # Armor Items Only:
        self.body_variation: int = 0
        self.model_variation: int = 0
        self.texture_variation: int = 0

        # Deprecated:
        self.stolen: int = 0
        self.identified: int = 0

    def is_armor(
        self,
    ) -> bool:
        return self.base_item in ARMOR_BASE_ITEMS


class UTIProperty:
    def __init__(
        self,
    ):
        self.cost_table: int = 0
        self.cost_value: int = 0
        self.param1: int = 0
        self.param1_value: int = 0
        self.property_name: int = 0
        self.subtype: int = 0
        self.chance_appear: int = 100
        self.upgrade_type: int | None = None


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

    if game == Game.K2:
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
) -> None:
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
