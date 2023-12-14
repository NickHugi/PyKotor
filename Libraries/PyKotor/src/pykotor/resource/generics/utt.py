from __future__ import annotations

from pykotor.common.language import LocalizedString
from pykotor.common.misc import Game, ResRef
from pykotor.resource.formats.gff import GFF, GFFContent, read_gff, write_gff
from pykotor.resource.formats.gff.gff_auto import bytes_gff
from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES, ResourceType


class UTT:
    """Stores trigger data.

    Attributes
    ----------
        tag: "Tag" field.
        resref: "TemplateResRef" field.
        auto_remove_key: "AutoRemoveKey" field.
        faction_id: "Faction" field.
        cursor_id: "Cursor" field.
        highlight_height: "HighlightHeight" field.
        key_name: "KeyName" field.
        type_id: "Type" field.
        trap_detectable: "TrapDetectable" field.
        trap_detect_dc: "TrapDetectDC" field.
        trap_disarmable: "TrapDisarmable" field.
        trap_disarm_dc: "DisarmDC" field.
        is_trap: "TrapFlag" field.
        trap_once: "TrapOneShot" field.
        trap_type: "TrapType" field.
        on_disarm: "OnDisarm" field.
        on_trap_triggered: "OnTrapTriggered" field.
        on_click: "OnClick" field.
        on_heartbeat: "ScriptHeartbeat" field.
        on_enter: "ScriptOnEnter" field.
        on_exit: "ScriptOnExit" field.
        on_user_defined: "ScriptUserDefine" field.
        comment: "Comment" field.

        palette_id: "PaletteID" field. Used in toolset only.

        name: "LocalizedName" field. Not used by the game engine.
        loadscreen_id: "LoadScreenID" field. Not used by the game engine.
        portrait_id: "PortraitId" field. Not used by the game engine.
    """

    BINARY_TYPE = ResourceType.UTT

    def __init__(
        self,
    ) -> None:
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
        self.on_user_defined = ResRef.from_blank()

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

    root = gff.root

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
) -> None:
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
