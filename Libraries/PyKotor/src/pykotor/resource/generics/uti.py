from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

from pykotor.common.language import LocalizedString
from pykotor.common.misc import Game, ResRef
from pykotor.resource.formats.gff import GFF, GFFContent, GFFList, read_gff, write_gff
from pykotor.resource.formats.gff.gff_auto import bytes_gff
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFFStruct
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES

ARMOR_BASE_ITEMS: set[int] = {35, 36, 37, 38, 39, 40, 41, 42, 43, 53, 58, 63, 64, 65, 69, 71, 85, 89, 98, 100, 102, 103}
""" Base Item IDs that are considered armor as per the 2DA files. """


class UTI:
    """Stores item data.

    UTI files are GFF-based format files that store item definitions including
    properties, costs, charges, and upgrade information.

    References:
    ----------
        vendor/reone/src/libs/resource/parser/gff/uti.cpp (UTI parsing from GFF)
        vendor/reone/include/reone/resource/parser/gff/uti.h:39-60 (UTI structure definitions)
        vendor/Kotor.NET/Kotor.NET/Resources/KotorUTI/UTI.cs:11-33 (UTI class definition)
        Note: UTI files are GFF format files with specific structure definitions

    Attributes:
    ----------
        resref: "TemplateResRef" field. The resource reference for this item template.
            Reference: reone/uti.h:57 (TemplateResRef field)
            Reference: Kotor.NET/UTI.cs:27 (TemplateResRef property)

        base_item: "BaseItem" field. Base item type identifier.
            Reference: reone/uti.h:41 (BaseItem field)
            Reference: Kotor.NET/UTI.cs:14 (BaseItem property)

        name: "LocalizedName" field. Localized name of the item.
            Reference: reone/uti.h:49 (LocalizedName field)
            Reference: Kotor.NET/UTI.cs:21 (LocalizedName property)

        description: "DescIdentified" field. Localized description when identified.
            Reference: reone/uti.h:46 (DescIdentified field)
            Reference: Kotor.NET/UTI.cs:19 (DescIdentified property)

        description2: "Description" field. Localized description.
            Reference: reone/uti.h:47 (Description field)
            Reference: Kotor.NET/UTI.cs:20 (Description property)

        tag: "Tag" field. Tag identifier for this item.
            Reference: reone/uti.h:56 (Tag field)
            Reference: Kotor.NET/UTI.cs:26 (Tag property)

        charges: "Charges" field. Number of charges remaining.
            Reference: reone/uti.h:43 (Charges field)
            Reference: Kotor.NET/UTI.cs:16 (Charges property)

        cost: "Cost" field. Base cost of the item.
            Reference: reone/uti.h:45 (Cost field)
            Reference: Kotor.NET/UTI.cs:18 (Cost property)

        stack_size: "StackSize" field. Maximum stack size.
            Reference: reone/uti.h:54 (StackSize field)
            Reference: Kotor.NET/UTI.cs:25 (StackSize property)

        plot: "Plot" field. Whether item is plot-critical.
            Reference: reone/uti.h:52 (Plot field)
            Reference: Kotor.NET/UTI.cs:24 (Plot property)

        add_cost: "AddCost" field. Additional cost modifier.
            Reference: reone/uti.h:40 (AddCost field)
            Reference: Kotor.NET/UTI.cs:13 (AddCost property)

        palette_id: "PaletteID" field. Palette identifier. Used in toolset only.
            Reference: reone/uti.h:51 (PaletteID field)
            Reference: Kotor.NET/UTI.cs:23 (PaletteID property)

        comment: "Comment" field. Developer comment.
            Reference: reone/uti.h:44 (Comment field)
            Reference: Kotor.NET/UTI.cs:17 (Comment property)

        upgrade_level: "UpgradeLevel" field. Upgrade level of the item.
            Reference: reone/uti.h:59 (UpgradeLevel field)
            Reference: Kotor.NET/UTI.cs:29 (UpgradeLevel property)

        properties: List of UTIProperty objects representing item properties.
            Reference: reone/uti.h:53 (PropertiesList vector)
            Reference: reone/uti.h:28-37 (UTI_PropertiesList struct)
            Reference: Kotor.NET/UTI.cs:32 (Properties property)

        body_variation: "BodyVariation" field. Body variation index. Armor items only.
            Reference: reone/uti.h:42 (BodyVariation field)
            Reference: Kotor.NET/UTI.cs:15 (BodyVariation property)

        model_variation: "ModelVariation" field. Model variation index. Armor items only.
            Reference: reone/uti.h:50 (ModelVariation field)
            Reference: Kotor.NET/UTI.cs:22 (ModelVariation property)

        texture_variation: "TextureVar" field. Texture variation index. Armor items only.
            Reference: reone/uti.h:58 (TextureVar field)
            Reference: Kotor.NET/UTI.cs:28 (TextureVar property)

        stolen: "Stolen" field. Whether item is stolen. Deprecated.
            Reference: reone/uti.h:55 (Stolen field)
            Reference: Kotor.NET/UTI.cs:30 (Stolen property)

        identified: "Identified" field. Whether item is identified. Deprecated.
            Reference: reone/uti.h:48 (Identified field)
            Reference: Kotor.NET/UTI.cs:31 (Identified property)
    """

    BINARY_TYPE = ResourceType.UTI

    def __init__(self):
        self.resref: ResRef = ResRef.from_blank()
        self.base_item: int = 0
        self.name: LocalizedString = LocalizedString.from_invalid()
        self.description: LocalizedString = LocalizedString.from_invalid()
        self.description2: LocalizedString = LocalizedString.from_invalid()
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
    """Represents an item property (enchantment, upgrade, etc.).

    References:
    ----------
        vendor/reone/include/reone/resource/parser/gff/uti.h:28-37 (UTI_PropertiesList struct)
        vendor/Kotor.NET/Kotor.NET/Resources/KotorUTI/UTI.cs:35-45 (UTIProperty class)

    Attributes:
    ----------
        cost_table: "CostTable" field. Cost table identifier.
            Reference: reone/uti.h:30 (CostTable field)
            Reference: Kotor.NET/UTI.cs:37 (CostTable property)

        cost_value: "CostValue" field. Cost value.
            Reference: reone/uti.h:31 (CostValue field)
            Reference: Kotor.NET/UTI.cs:38 (CostValue property)

        param1: "Param1" field. First parameter.
            Reference: reone/uti.h:32 (Param1 field)
            Reference: Kotor.NET/UTI.cs:39 (Param1 property)

        param1_value: "Param1Value" field. First parameter value.
            Reference: reone/uti.h:33 (Param1Value field)
            Reference: Kotor.NET/UTI.cs:40 (Param1Value property)

        property_name: "PropertyName" field. Property name identifier.
            Reference: reone/uti.h:34 (PropertyName field)
            Reference: Kotor.NET/UTI.cs:41 (PropertyName property)

        subtype: "Subtype" field. Property subtype identifier.
            Reference: reone/uti.h:35 (Subtype field)
            Reference: Kotor.NET/UTI.cs:42 (Subtype property)

        chance_appear: "ChanceAppear" field. Chance this property appears (0-100).
            Reference: reone/uti.h:29 (ChanceAppear field)
            Reference: Kotor.NET/UTI.cs:44 (ChanceAppear property)

        upgrade_type: "UpgradeType" field. Upgrade type identifier.
            Reference: reone/uti.h:36 (UpgradeType field)
            Reference: Kotor.NET/UTI.cs:43 (UpgradeType property)
    """
    def __init__(self):
        self.cost_table: int = 0
        self.cost_value: int = 0
        self.param1: int = 0
        self.param1_value: int = 0
        self.property_name: int = 0
        self.subtype: int = 0
        self.chance_appear: int = 100
        self.upgrade_type: int | None = None


def construct_uti_from_struct(struct: GFFStruct) -> UTI:
    new_gff = GFF(GFFContent.UTI)
    new_gff.root = deepcopy(struct)
    return construct_uti(new_gff)


def construct_uti(gff: GFF) -> UTI:
    """Constructs a UTI object from a GFF structure.
    
    Parses UTI (item template) data from a GFF file, reading all fields
    including properties, costs, charges, and upgrade information.
    
    References:
    ----------
        vendor/reone/src/libs/resource/parser/gff/uti.cpp:41-66 (parseUTI function)
        vendor/reone/include/reone/resource/parser/gff/uti.h:39-60 (UTI struct definition)
        vendor/Kotor.NET/Kotor.NET/Resources/KotorUTI/UTI.cs:11-33 (UTI class definition)
        vendor/xoreos-tools/src/xml/utidumper.cpp (UTI to XML conversion)
        Original BioWare Odyssey Engine (UTI GFF structure specification)
    """
    uti = UTI()

    root = gff.root
    # vendor/reone/src/libs/resource/parser/gff/uti.cpp:62 (TemplateResRef field)
    # vendor/Kotor.NET/Kotor.NET/Resources/KotorUTI/UTI.cs:27 (TemplateResRef property)
    uti.resref = root.acquire("TemplateResRef", ResRef.from_blank())
    # vendor/reone/src/libs/resource/parser/gff/uti.cpp:44 (BaseItem field as int)
    # vendor/Kotor.NET/Kotor.NET/Resources/KotorUTI/UTI.cs:14 (BaseItem property)
    uti.base_item = root.acquire("BaseItem", 0)
    # vendor/reone/src/libs/resource/parser/gff/uti.cpp:52 (LocalizedName field as pair<int, string>)
    # vendor/Kotor.NET/Kotor.NET/Resources/KotorUTI/UTI.cs:21 (LocalizedName property)
    uti.name = root.acquire("LocalizedName", LocalizedString.from_invalid())
    # vendor/reone/src/libs/resource/parser/gff/uti.cpp:49 (DescIdentified field as pair<int, string>)
    # vendor/Kotor.NET/Kotor.NET/Resources/KotorUTI/UTI.cs:19 (DescIdentified property)
    uti.description = root.acquire("DescIdentified", LocalizedString.from_invalid())
    # vendor/reone/src/libs/resource/parser/gff/uti.cpp:50 (Description field as pair<int, string>)
    # vendor/Kotor.NET/Kotor.NET/Resources/KotorUTI/UTI.cs:20 (Description property)
    uti.description2 = root.acquire("Description", LocalizedString.from_invalid())
    # vendor/reone/src/libs/resource/parser/gff/uti.cpp:61 (Tag field)
    # vendor/Kotor.NET/Kotor.NET/Resources/KotorUTI/UTI.cs:26 (Tag property)
    uti.tag = root.acquire("Tag", "")
    # vendor/reone/src/libs/resource/parser/gff/uti.cpp:46 (Charges field as uint8)
    # vendor/Kotor.NET/Kotor.NET/Resources/KotorUTI/UTI.cs:16 (Charges property)
    uti.charges = root.acquire("Charges", 0)
    # vendor/reone/src/libs/resource/parser/gff/uti.cpp:48 (Cost field as uint32)
    # vendor/Kotor.NET/Kotor.NET/Resources/KotorUTI/UTI.cs:18 (Cost property)
    uti.cost = root.acquire("Cost", 0)
    # vendor/reone/src/libs/resource/parser/gff/uti.cpp:59 (StackSize field as uint16)
    # vendor/Kotor.NET/Kotor.NET/Resources/KotorUTI/UTI.cs:25 (StackSize property)
    uti.stack_size = root.acquire("StackSize", 0)
    # vendor/reone/src/libs/resource/parser/gff/uti.cpp:55 (Plot field as uint8)
    # vendor/Kotor.NET/Kotor.NET/Resources/KotorUTI/UTI.cs:24 (Plot property)
    uti.plot = root.acquire("Plot", 0)
    # vendor/reone/src/libs/resource/parser/gff/uti.cpp:43 (AddCost field as uint32)
    # vendor/Kotor.NET/Kotor.NET/Resources/KotorUTI/UTI.cs:13 (AddCost property)
    uti.add_cost = root.acquire("AddCost", 0)
    # vendor/reone/src/libs/resource/parser/gff/uti.cpp:54 (PaletteID field as uint8, toolset-only)
    # vendor/Kotor.NET/Kotor.NET/Resources/KotorUTI/UTI.cs:23 (PaletteID property)
    uti.palette_id = root.acquire("PaletteID", 0)
    # vendor/reone/src/libs/resource/parser/gff/uti.cpp:47 (Comment field)
    # vendor/Kotor.NET/Kotor.NET/Resources/KotorUTI/UTI.cs:17 (Comment property)
    uti.comment = root.acquire("Comment", "")
    # vendor/reone/src/libs/resource/parser/gff/uti.cpp:53 (ModelVariation field as uint8, armor items only)
    # vendor/Kotor.NET/Kotor.NET/Resources/KotorUTI/UTI.cs:22 (ModelVariation property)
    uti.model_variation = root.acquire("ModelVariation", 0)
    # vendor/reone/src/libs/resource/parser/gff/uti.cpp:45 (BodyVariation field as uint8, armor items only)
    # vendor/Kotor.NET/Kotor.NET/Resources/KotorUTI/UTI.cs:15 (BodyVariation property)
    uti.body_variation = root.acquire("BodyVariation", 0)
    # vendor/reone/src/libs/resource/parser/gff/uti.cpp:63 (TextureVar field as uint8, armor items only)
    # vendor/Kotor.NET/Kotor.NET/Resources/KotorUTI/UTI.cs:28 (TextureVar property)
    uti.texture_variation = root.acquire("TextureVar", 0)
    # vendor/reone/src/libs/resource/parser/gff/uti.cpp:64 (UpgradeLevel field as uint8, KotOR 2 only)
    # vendor/Kotor.NET/Kotor.NET/Resources/KotorUTI/UTI.cs:29 (UpgradeLevel property)
    uti.upgrade_level = root.acquire("UpgradeLevel", 0)
    # vendor/reone/src/libs/resource/parser/gff/uti.cpp:60 (Stolen field as uint8, deprecated)
    # vendor/Kotor.NET/Kotor.NET/Resources/KotorUTI/UTI.cs:30 (Stolen property)
    uti.stolen = root.acquire("Stolen", 0)
    # vendor/reone/src/libs/resource/parser/gff/uti.cpp:51 (Identified field as uint8, deprecated)
    # vendor/Kotor.NET/Kotor.NET/Resources/KotorUTI/UTI.cs:31 (Identified property)
    uti.identified = root.acquire("Identified", 0)

    # vendor/reone/src/libs/resource/parser/gff/uti.cpp:56-58 (PropertiesList parsing)
    # vendor/reone/include/reone/resource/parser/gff/uti.h:53 (PropertiesList vector)
    # vendor/Kotor.NET/Kotor.NET/Resources/KotorUTI/UTI.cs:32 (Properties property)
    # PropertiesList contains item properties (enchantments, upgrades, etc.)
    for property_struct in root.acquire("PropertiesList", GFFList()):
        prop = UTIProperty()
        uti.properties.append(prop)
        # vendor/reone/src/libs/resource/parser/gff/uti.cpp:28-38 (parseUTI_PropertiesList)
        # vendor/reone/include/reone/resource/parser/gff/uti.h:28-37 (UTI_PropertiesList struct)
        # vendor/Kotor.NET/Kotor.NET/Resources/KotorUTI/UTI.cs:35-45 (UTIProperty class)
        # vendor/reone/src/libs/resource/parser/gff/uti.cpp:31 (CostTable field as uint8)
        prop.cost_table = property_struct.acquire("CostTable", 0)
        # vendor/reone/src/libs/resource/parser/gff/uti.cpp:32 (CostValue field as uint16)
        prop.cost_value = property_struct.acquire("CostValue", 0)
        # vendor/reone/src/libs/resource/parser/gff/uti.cpp:33 (Param1 field as uint8)
        prop.param1 = property_struct.acquire("Param1", 0)
        # vendor/reone/src/libs/resource/parser/gff/uti.cpp:34 (Param1Value field as uint8)
        prop.param1_value = property_struct.acquire("Param1Value", 0)
        # vendor/reone/src/libs/resource/parser/gff/uti.cpp:35 (PropertyName field as uint16)
        prop.property_name = property_struct.acquire("PropertyName", 0)
        # vendor/reone/src/libs/resource/parser/gff/uti.cpp:36 (Subtype field as uint16)
        prop.subtype = property_struct.acquire("Subtype", 0)
        # vendor/reone/src/libs/resource/parser/gff/uti.cpp:30 (ChanceAppear field as uint8, default 100)
        prop.chance_appear = property_struct.acquire("ChanceAppear", 100)

        # vendor/reone/src/libs/resource/parser/gff/uti.cpp:37 (UpgradeType field as uint8, optional)
        # Discrepancy: PyKotor treats UpgradeType as optional (checks exists()), reone always reads it
        # Note: Kotor.NET also treats UpgradeType as optional (byte UpgradeType { get; set; })
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
    root.set_locstring("Description", uti.description2)
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
