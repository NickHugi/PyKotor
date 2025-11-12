from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.language import LocalizedString
from pykotor.common.misc import Game, ResRef
from pykotor.resource.formats.gff import GFF, GFFContent, read_gff, write_gff
from pykotor.resource.formats.gff.gff_auto import bytes_gff
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.extract.installation import GFFStruct
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class UTT:
    """Stores trigger data.

    UTT files are GFF-based format files that store trigger definitions including
    trap mechanics, script hooks, and activation settings.

    References:
    ----------
        vendor/reone/src/libs/resource/parser/gff/utt.cpp:28-62 (UTT parsing from GFF)
        vendor/reone/include/reone/resource/parser/gff/utt.h:28-60 (UTT structure definitions)
        vendor/Kotor.NET/Kotor.NET/Resources/KotorUTT/UTT.cs:11-45 (UTT class definition)
        vendor/KotOR.js/src/module/ModuleTrigger.ts:30-168 (Trigger module object)
        Note: UTT files are GFF format files with specific structure definitions

    Attributes:
    ----------
        resref: "TemplateResRef" field. The resource reference for this trigger template.
            Reference: reone/utt.cpp:53 (TemplateResRef field)
            Reference: reone/utt.h:52 (TemplateResRef field)
            Reference: Kotor.NET/UTT.cs:14 (TemplateResRef property)

        tag: "Tag" field. Tag identifier for this trigger.
            Reference: reone/utt.cpp:52 (Tag field)
            Reference: reone/utt.h:51 (Tag field)
            Reference: Kotor.NET/UTT.cs:13 (Tag property)

        auto_remove_key: "AutoRemoveKey" field. Whether key is removed after use.
            Reference: reone/utt.cpp:30 (AutoRemoveKey field)
            Reference: reone/utt.h:29 (AutoRemoveKey field)
            Reference: Kotor.NET/UTT.cs:16 (AutoRemoveKey property)

        faction_id: "Faction" field. Faction identifier.
            Reference: reone/utt.cpp:34 (Faction field)
            Reference: reone/utt.h:33 (Faction field)
            Reference: Kotor.NET/UTT.cs:17 (Faction property)

        cursor_id: "Cursor" field. Cursor type identifier.
            Reference: reone/utt.cpp:32 (Cursor field)
            Reference: reone/utt.h:31 (Cursor field)
            Reference: Kotor.NET/UTT.cs:18 (Cursor property)

        highlight_height: "HighlightHeight" field. Height of highlight area.
            Reference: reone/utt.cpp:35 (HighlightHeight field)
            Reference: reone/utt.h:34 (HighlightHeight field)
            Reference: Kotor.NET/UTT.cs:19 (HighlightHeight property)

        key_name: "KeyName" field. Tag of the key item required.
            Reference: reone/utt.cpp:36 (KeyName field)
            Reference: reone/utt.h:35 (KeyName field)
            Reference: Kotor.NET/UTT.cs:20 (KeyName property)

        type_id: "Type" field. Trigger type identifier.
            Reference: reone/utt.cpp:60 (Type field)
            Reference: reone/utt.h:59 (Type field)
            Reference: Kotor.NET/UTT.cs:23 (Type property)
            Reference: KotOR.js/ModuleTrigger.ts:46 (type field)

        is_trap: "TrapFlag" field. Whether trigger has a trap.
            Reference: reone/utt.cpp:57 (TrapFlag field)
            Reference: reone/utt.h:56 (TrapFlag field)
            Reference: Kotor.NET/UTT.cs:28 (TrapFlag property)

        trap_type: "TrapType" field. Type of trap.
            Reference: reone/utt.cpp:59 (TrapType field)
            Reference: reone/utt.h:58 (TrapType field)
            Reference: Kotor.NET/UTT.cs:30 (TrapType property)

        trap_once: "TrapOneShot" field. Whether trap fires only once.
            Reference: reone/utt.cpp:58 (TrapOneShot field)
            Reference: reone/utt.h:57 (TrapOneShot field)
            Reference: Kotor.NET/UTT.cs:29 (TrapOneShot property)

        trap_detectable: "TrapDetectable" field. Whether trap is detectable.
            Reference: reone/utt.cpp:55 (TrapDetectable field)
            Reference: reone/utt.h:54 (TrapDetectable field)
            Reference: Kotor.NET/UTT.cs:24 (TrapDetectable property)

        trap_detect_dc: "TrapDetectDC" field. Difficulty class to detect trap.
            Reference: reone/utt.cpp:54 (TrapDetectDC field)
            Reference: reone/utt.h:53 (TrapDetectDC field)
            Reference: Kotor.NET/UTT.cs:25 (TrapDetectDC property)

        trap_disarmable: "TrapDisarmable" field. Whether trap is disarmable.
            Reference: reone/utt.cpp:56 (TrapDisarmable field)
            Reference: reone/utt.h:55 (TrapDisarmable field)
            Reference: Kotor.NET/UTT.cs:26 (TrapDisarmable property)

        trap_disarm_dc: "DisarmDC" field. Difficulty class to disarm trap.
            Reference: reone/utt.cpp:33 (DisarmDC field)
            Reference: reone/utt.h:32 (DisarmDC field)
            Reference: Kotor.NET/UTT.cs:27 (DisarmDC property)

        on_disarm: "OnDisarm" field. Script to run when trap is disarmed.
            Reference: reone/utt.cpp:42 (OnDisarm field)
            Reference: reone/utt.h:41 (OnDisarm field)
            Reference: Kotor.NET/UTT.cs:31 (OnDisarm property)

        on_trap_triggered: "OnTrapTriggered" field. Script to run when trap triggers.
            Reference: reone/utt.cpp:43 (OnTrapTriggered field)
            Reference: reone/utt.h:42 (OnTrapTriggered field)
            Reference: Kotor.NET/UTT.cs:32 (OnTrapTriggered property)

        on_click: "OnClick" field. Script to run when trigger is clicked.
            Reference: reone/utt.cpp:41 (OnClick field)
            Reference: reone/utt.h:40 (OnClick field)
            Reference: Kotor.NET/UTT.cs:33 (OnClick property)

        on_heartbeat: "ScriptHeartbeat" field. Script to run on heartbeat.
            Reference: reone/utt.cpp:48 (ScriptHeartbeat field)
            Reference: reone/utt.h:47 (ScriptHeartbeat field)
            Reference: Kotor.NET/UTT.cs:34 (ScriptHeartbeat property)

        on_enter: "ScriptOnEnter" field. Script to run when area is entered.
            Reference: reone/utt.cpp:49 (ScriptOnEnter field)
            Reference: reone/utt.h:48 (ScriptOnEnter field)
            Reference: Kotor.NET/UTT.cs:35 (ScriptOnEnter property)

        on_exit: "ScriptOnExit" field. Script to run when area is exited.
            Reference: reone/utt.cpp:50 (ScriptOnExit field)
            Reference: reone/utt.h:49 (ScriptOnExit field)
            Reference: Kotor.NET/UTT.cs:36 (ScriptOnExit property)

        on_user_defined: "ScriptUserDefine" field. Script to run on user-defined event.
            Reference: reone/utt.cpp:51 (ScriptUserDefine field)
            Reference: reone/utt.h:50 (ScriptUserDefine field)
            Reference: Kotor.NET/UTT.cs:37 (ScriptUserDefine property)

        comment: "Comment" field. Developer comment.
            Reference: reone/utt.cpp:31 (Comment field)
            Reference: reone/utt.h:30 (Comment field)
            Reference: Kotor.NET/UTT.cs:39 (Comment property)

        palette_id: "PaletteID" field. Palette identifier. Used in toolset only.
            Reference: reone/utt.cpp:44 (PaletteID field)
            Reference: reone/utt.h:43 (PaletteID field)
            Reference: Kotor.NET/UTT.cs:38 (PaletteID property)

        name: "LocalizedName" field. Localized name. Not used by the game engine.
            Reference: reone/utt.cpp:40 (LocalizedName field)
            Reference: reone/utt.h:39 (LocalizedName field)
            Reference: Kotor.NET/UTT.cs:15 (LocalizedName property)

        loadscreen_id: "LoadScreenID" field. Load screen identifier. Not used by the game engine.
            Reference: reone/utt.cpp:39 (LoadScreenID field)
            Reference: reone/utt.h:38 (LoadScreenID field)
            Reference: Kotor.NET/UTT.cs:21 (LoadScreenID property)

        portrait_id: "PortraitId" field. Portrait identifier. Not used by the game engine.
            Reference: reone/utt.cpp:47 (PortraitId field)
            Reference: reone/utt.h:46 (PortraitId field)
            Reference: Kotor.NET/UTT.cs:22 (PortraitId property)
    """

    BINARY_TYPE = ResourceType.UTT

    def __init__(
        self,
    ):
        self.resref: ResRef = ResRef.from_blank()
        self.comment: str = ""
        self.tag: str = ""

        self.name: LocalizedString = LocalizedString.from_invalid()

        self.faction_id: int = 0
        self.cursor_id: int = 0
        self.type_id: int = 0

        self.auto_remove_key: bool = True
        self.key_name: str = ""

        self.highlight_height: float = 0.0

        self.is_trap: bool = False
        self.trap_type: int = 0
        self.trap_once: bool = False
        self.trap_detectable: bool = False
        self.trap_detect_dc: int = 0
        self.trap_disarmable: bool = False
        self.trap_disarm_dc: int = 0

        self.on_disarm: ResRef = ResRef.from_blank()
        self.on_click: ResRef = ResRef.from_blank()
        self.on_trap_triggered: ResRef = ResRef.from_blank()
        self.on_heartbeat: ResRef = ResRef.from_blank()
        self.on_enter: ResRef = ResRef.from_blank()
        self.on_exit: ResRef = ResRef.from_blank()
        self.on_user_defined: ResRef = ResRef.from_blank()

        # Deprecated:
        self.portrait_id: int = 0
        self.loadscreen_id: int = 0
        self.palette_id: int = 0
        self.name: LocalizedString = LocalizedString.from_invalid()


def construct_utt(
    gff: GFF,
) -> UTT:
    """Constructs a UTT object from a GFF node.

    Args:
    ----
        gff: GFF - The GFF node to parse

    Returns:
    -------
        utt: UTT - The constructed UTT object

    Processing Logic:
    ----------------
        - Initialize an empty UTT object
        - Get the root node of the GFF
        - Acquire and set various UTT properties by parsing attributes from the root node
        - Return the completed UTT object.
    """
    utt = UTT()

    root: GFFStruct = gff.root

    utt.tag = root.acquire("Tag", "")
    utt.resref = root.acquire("TemplateResRef", ResRef.from_blank())
    utt.auto_remove_key = bool(root.acquire("AutoRemoveKey", 0))
    utt.faction_id = root.acquire("Faction", 0)
    utt.cursor_id = root.acquire("Cursor", 0)
    utt.highlight_height = root.acquire("HighlightHeight", 0.0)
    utt.key_name = root.acquire("KeyName", "")
    utt.type_id = root.acquire("Type", 0)
    utt.trap_detectable = bool(root.acquire("TrapDetectable", 0))
    utt.trap_detect_dc = root.acquire("TrapDetectDC", 0)
    utt.trap_disarmable = bool(root.acquire("TrapDisarmable", 0))
    utt.trap_disarm_dc = root.acquire("DisarmDC", 0)
    utt.is_trap = bool(root.acquire("TrapFlag", 0))
    utt.trap_once = bool(root.acquire("TrapOneShot", 0))
    utt.trap_type = root.acquire("TrapType", 0)
    utt.on_disarm = root.acquire("OnDisarm", ResRef.from_blank())
    utt.on_trap_triggered = root.acquire("OnTrapTriggered", ResRef.from_blank())
    utt.on_click = root.acquire("OnClick", ResRef.from_blank())
    utt.on_heartbeat = root.acquire("ScriptHeartbeat", ResRef.from_blank())
    utt.on_enter = root.acquire("ScriptOnEnter", ResRef.from_blank())
    utt.on_exit = root.acquire("ScriptOnExit", ResRef.from_blank())
    utt.on_user_defined = root.acquire("ScriptUserDefine", ResRef.from_blank())
    utt.comment = root.acquire("Comment", "")
    utt.name = root.acquire("LocalizedName", LocalizedString.from_invalid())
    utt.loadscreen_id = root.acquire("LoadScreenID", 0)
    utt.portrait_id = root.acquire("PortraitId", 0)
    utt.palette_id = root.acquire("PaletteID", 0)

    return utt


def dismantle_utt(
    utt: UTT,
    game: Game = Game.K2,
    *,
    use_deprecated: bool = True,
) -> GFF:
    """Dismantles a UTT object into a GFF structure.

    Args:
    ----
        utt: UTT - The UTT object to dismantle
        game: Game - The game the UTT is for (default K2)
        use_deprecated: bool - Whether to include deprecated fields (default True)

    Returns:
    -------
        GFF - The dismantled UTT as a GFF structure

    Processes the UTT by:
    - Creating a GFF root node
    - Setting UTT fields as properties on the root node
    - Returning the completed GFF.
    """
    gff = GFF(GFFContent.UTT)

    root = gff.root
    root.set_string("Tag", utt.tag)
    root.set_resref("TemplateResRef", utt.resref)
    root.set_uint8("AutoRemoveKey", utt.auto_remove_key)
    root.set_uint32("Faction", utt.faction_id)
    root.set_uint8("Cursor", utt.cursor_id)
    root.set_single("HighlightHeight", utt.highlight_height)
    root.set_string("KeyName", utt.key_name)
    root.set_int32("Type", utt.type_id)
    root.set_uint8("TrapDetectable", utt.trap_detectable)
    root.set_uint8("TrapDetectDC", utt.trap_detect_dc)
    root.set_uint8("TrapDisarmable", utt.trap_disarmable)
    root.set_uint8("DisarmDC", utt.trap_disarm_dc)
    root.set_uint8("TrapFlag", utt.is_trap)
    root.set_uint8("TrapOneShot", utt.trap_once)
    root.set_uint8("TrapType", utt.trap_type)
    root.set_resref("OnDisarm", utt.on_disarm)
    root.set_resref("OnTrapTriggered", utt.on_trap_triggered)
    root.set_resref("OnClick", utt.on_click)
    root.set_resref("ScriptHeartbeat", utt.on_heartbeat)
    root.set_resref("ScriptOnEnter", utt.on_enter)
    root.set_resref("ScriptOnExit", utt.on_exit)
    root.set_resref("ScriptUserDefine", utt.on_user_defined)
    root.set_string("Comment", utt.comment)

    root.set_uint8("PaletteID", utt.palette_id)

    if use_deprecated:
        root.set_locstring("LocalizedName", utt.name)
        root.set_uint16("LoadScreenID", utt.loadscreen_id)
        root.set_uint16("PortraitId", utt.portrait_id)

    return gff


def read_utt(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
) -> UTT:
    gff = read_gff(source, offset, size)
    return construct_utt(gff)


def write_utt(
    utt: UTT,
    target: TARGET_TYPES,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
):
    gff = dismantle_utt(utt, game, use_deprecated=use_deprecated)
    write_gff(gff, target, file_format)


def bytes_utt(
    utt: UTT,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
) -> bytes:
    gff = dismantle_utt(utt, game, use_deprecated=use_deprecated)
    return bytes_gff(gff, file_format)
