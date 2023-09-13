from __future__ import annotations

from pykotor.common.language import LocalizedString
from pykotor.common.misc import Game, ResRef
from pykotor.resource.formats.gff import GFF, GFFContent, write_gff
from pykotor.resource.formats.gff.gff_auto import bytes_gff, read_gff
from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES, ResourceType


class UTD:
    """
    Stores door data.

    Attributes
    ----------
        tag: "Tag" field.
        name: "LocName" field.
        resref: "TemplateResRef" field.
        auto_remove_key: "AutoRemoveKey" field.
        conversation: "Conversation" field.
        faction_id: "Faction" field.
        plot: "Plot" field.
        min1_hp: "Min1HP" field.
        key_required: "KeyRequired" field.
        lockable: "Lockable" field.
        locked: "Locked" field.
        unlock_dc: "OpenLockDC" field.
        key_name: "KeyName" field.
        animation_state: "AnimationState" field.
        maximum_hp: "HP" field.
        current_hp: "CurrentHP" field.
        hardness: "Hardness" field.
        fortitude: "Fort" field.
        on_closed: "OnClosed" field.
        on_damaged: "OnDamaged" field.
        on_death: "OnDeath" field.
        on_heartbeat: "OnHeartbeat" field.
        on_lock: "OnLock" field.
        on_melee: "OnMeleeAttacked" field.
        on_open: "OnOpen" field.
        on_unlock: "OnUnlock" field.
        on_user_defined: "OnUserDefined" field.
        appearance_id: "GenericType" field.
        static: "Static" field.
        on_click: "OnClick" field.
        on_open_failed: "OnFailToOpen" field.
        comment: "Comment" field.

        unlock_diff: "OpenLockDiff" field. KotOR 2 Only.
        unlock_diff_mod: "OpenLockDiffMod" field. KotOR 2 Only.
        open_state: "OpenState" field. KotOR 2 Only.
        not_blastable: "NotBlastable" field. KotOR 2 Only.

        palette_id: "PaletteID" field. Used in toolset only.

        description: "Description" field. Not used by the game engine.
        lock_dc: "CloseLockDC" field. Not used by the game engine.
        interruptable: "Interruptable" field. Not used by the game engine.
        portrait_id: "PortraitId" field. Not used by the game engine.
        trap_detectable: "TrapDetectable" field. Not used by the game engine.
        trap_detect_dc: "TrapDetectDC" field. Not used by the game engine.
        trap_disarmable: "TrapDisarmable" field. Not used by the game engine.
        trap_disarm_dc: "DisarmDC" field. Not used by the game engine.
        trap_flag: "TrapFlag" field. Not used by the game engine.
        trap_one_shot: "TrapOneShot" field. Not used by the game engine.
        trap_type: "TrapType" field. Not used by the game engine.
        unused_appearance: "Appearance" field. Not used by the game engine.
        reflex: "Ref" field. Not used by the game engine.
        willpower: "Will" field. Not used by the game engine.
        on_disarm: "OnDisarm" field. Not used by the game engine.
        on_power: "OnSpellCastAt" field. Not used by the game engine.
        on_trap_triggered: "OnTrapTriggered" field. Not used by the game engine.
        loadscreen_id: "LoadScreenID" field. Not used by the game engine.
    """

    BINARY_TYPE = ResourceType.UTD

    def __init__(
        self,
    ):
        self.resref: ResRef = ResRef.from_blank()
        self.conversation: ResRef = ResRef.from_blank()
        self.tag: str = ""
        self.comment: str = ""

        self.name: LocalizedString = LocalizedString.from_invalid()

        self.faction_id: int = 0
        self.appearance_id: int = 0
        self.animation_state: int = 0

        self.auto_remove_key: bool = False
        self.key_name: str = ""
        self.key_required: bool = False
        self.lockable: bool = False
        self.locked: bool = False

        self.unlock_dc: int = 0
        self.unlock_diff: int = 0  # KotOR 2 Only
        self.unlock_diff_mod: int = 0  # KotOR 2 Only
        self.open_state: int = 0  # KotOR 2 Only

        self.min1_hp: bool = False  # KotOR 2 Only
        self.not_blastable: bool = False  # KotOR 2 Only
        self.plot: bool = False
        self.static: bool = False

        self.current_hp: int = 0
        self.maximum_hp: int = 0
        self.fortitude: int = 0
        self.hardness: int = 0

        self.on_click: ResRef = ResRef.from_blank()
        self.on_damaged: ResRef = ResRef.from_blank()
        self.on_death: ResRef = ResRef.from_blank()
        self.on_open_failed: ResRef = ResRef.from_blank()
        self.on_heartbeat: ResRef = ResRef.from_blank()
        self.on_melee: ResRef = ResRef.from_blank()
        self.on_open: ResRef = ResRef.from_blank()
        self.on_user_defined: ResRef = ResRef.from_blank()
        self.on_unlock: ResRef = ResRef.from_blank()
        self.on_lock: ResRef = ResRef.from_blank()
        self.on_closed: ResRef = ResRef.from_blank()

        self.palette_id: int = 0

        # Deprecated:
        self.description: LocalizedString = LocalizedString.from_invalid()
        self.lock_dc: int = 0
        self.interruptable: bool = False
        self.portrait_id: int = 0
        self.trap_detectable: bool = False
        self.trap_disarmable: bool = False
        self.trap_detect_dc: int = 0
        self.trap_disarm_dc: int = 0
        self.trap_type: int = 0
        self.trap_one_shot: bool = True
        self.trap_flag: int = 0
        self.unused_appearance: int = 0
        self.reflex: int = 0
        self.willpower: int = 0
        self.on_disarm: ResRef = ResRef.from_blank()
        self.on_power: ResRef = ResRef.from_blank()
        self.on_trap_triggered: ResRef = ResRef.from_blank()
        self.loadscreen_id: int = 0


def utd_version(
    gff: GFF,
) -> Game:
    return next(
        (
            Game.K2
            for label in (
                "NotBlastable",
                "OpenLockDiff",
                "OpenLockDiffMod",
                "OpenState",
            )
            if gff.root.exists(label)
        ),
        Game.K1,
    )


def construct_utd(
    gff: GFF,
) -> UTD:
    utd = UTD()

    root = gff.root
    utd.tag = root.acquire("Tag", "")
    utd.name = root.acquire("LocName", LocalizedString.from_invalid())
    utd.resref = root.acquire("TemplateResRef", ResRef.from_blank())
    utd.auto_remove_key = bool(root.acquire("AutoRemoveKey", 0))
    utd.conversation = root.acquire("Conversation", ResRef.from_blank())
    utd.faction_id = root.acquire("Faction", 0)
    utd.plot = bool(root.acquire("Plot", 0))
    utd.min1_hp = bool(root.acquire("Min1HP", 0))
    utd.key_required = bool(root.acquire("KeyRequired", 0))
    utd.lockable = bool(root.acquire("Lockable", 0))
    utd.locked = bool(root.acquire("Locked", 0))
    utd.unlock_dc = root.acquire("OpenLockDC", 0)
    utd.key_name = root.acquire("KeyName", "")
    utd.animation_state = root.acquire("AnimationState", 0)
    utd.maximum_hp = root.acquire("HP", 0)
    utd.current_hp = root.acquire("CurrentHP", 0)
    utd.hardness = root.acquire("Hardness", 0)
    utd.fortitude = root.acquire("Fort", 0)
    utd.on_closed = root.acquire("OnClosed", ResRef.from_blank())
    utd.on_damaged = root.acquire("OnDamaged", ResRef.from_blank())
    utd.on_death = root.acquire("OnDeath", ResRef.from_blank())
    utd.on_heartbeat = root.acquire("OnHeartbeat", ResRef.from_blank())
    utd.on_lock = root.acquire("OnLock", ResRef.from_blank())
    utd.on_melee = root.acquire("OnMeleeAttacked", ResRef.from_blank())
    utd.on_open = root.acquire("OnOpen", ResRef.from_blank())
    utd.on_unlock = root.acquire("OnUnlock", ResRef.from_blank())
    utd.on_user_defined = root.acquire("OnUserDefined", ResRef.from_blank())
    utd.appearance_id = root.acquire("GenericType", 0)
    utd.static = bool(root.acquire("Static", 0))
    utd.open_state = root.acquire("OpenState", 0)
    utd.on_click = root.acquire("OnClick", ResRef.from_blank())
    utd.on_open_failed = root.acquire("OnFailToOpen", ResRef.from_blank())
    utd.comment = root.acquire("Comment", "")
    utd.unlock_diff = root.acquire("OpenLockDiff", 0)
    utd.unlock_diff_mod = root.acquire("OpenLockDiffMod", 0)
    utd.description = root.acquire("Description", LocalizedString.from_invalid())
    utd.lock_dc = root.acquire("CloseLockDC", 0)
    utd.interruptable = bool(root.acquire("Interruptable", 0))
    utd.portrait_id = root.acquire("PortraitId", 0)
    utd.trap_detectable = bool(root.acquire("TrapDetectable", 0))
    utd.trap_detect_dc = root.acquire("TrapDetectDC", 0)
    utd.trap_disarmable = bool(root.acquire("TrapDisarmable", 0))
    utd.trap_disarm_dc = root.acquire("DisarmDC", 0)
    utd.trap_flag = root.acquire("TrapFlag", 0)
    utd.trap_one_shot = bool(root.acquire("TrapOneShot", 0))
    utd.trap_type = root.acquire("TrapType", 0)
    utd.unused_appearance = root.acquire("Appearance", 0)
    utd.reflex = root.acquire("Ref", 0)
    utd.willpower = root.acquire("Will", 0)
    utd.on_disarm = root.acquire("OnDisarm", ResRef.from_blank())
    utd.on_power = root.acquire("OnSpellCastAt", ResRef.from_blank())
    utd.on_trap_triggered = root.acquire("OnTrapTriggered", ResRef.from_blank())
    utd.loadscreen_id = root.acquire("LoadScreenID", 0)
    utd.palette_id = root.acquire("PaletteID", 0)
    utd.not_blastable = bool(root.acquire("NotBlastable", 0))

    return utd


def dismantle_utd(
    utd: UTD,
    game: Game = Game.K2,
    *,
    use_deprecated: bool = True,
) -> GFF:
    gff = GFF(GFFContent.UTD)

    root = gff.root
    root.set_string("Tag", utd.tag)
    root.set_locstring("LocName", utd.name)
    root.set_resref("TemplateResRef", utd.resref)
    root.set_uint8("AutoRemoveKey", utd.auto_remove_key)
    root.set_resref("Conversation", utd.conversation)
    root.set_uint32("Faction", utd.faction_id)
    root.set_uint8("Plot", utd.plot)
    root.set_uint8("Min1HP", utd.min1_hp)
    root.set_uint8("KeyRequired", utd.key_required)
    root.set_uint8("Lockable", utd.lockable)
    root.set_uint8("Locked", utd.locked)
    root.set_uint8("OpenLockDC", utd.unlock_dc)
    root.set_string("KeyName", utd.key_name)
    root.set_uint8("AnimationState", utd.animation_state)
    root.set_int16("HP", utd.maximum_hp)
    root.set_int16("CurrentHP", utd.current_hp)
    root.set_uint8("Hardness", utd.hardness)
    root.set_uint8("Fort", utd.fortitude)
    root.set_resref("OnClosed", utd.on_closed)
    root.set_resref("OnDamaged", utd.on_damaged)
    root.set_resref("OnDeath", utd.on_death)
    root.set_resref("OnHeartbeat", utd.on_heartbeat)
    root.set_resref("OnLock", utd.on_lock)
    root.set_resref("OnMeleeAttacked", utd.on_melee)
    root.set_resref("OnOpen", utd.on_open)
    root.set_resref("OnUnlock", utd.on_unlock)
    root.set_resref("OnUserDefined", utd.on_user_defined)
    root.set_uint8("GenericType", utd.appearance_id)
    root.set_uint8("Static", utd.static)
    root.set_resref("OnClick", utd.on_click)
    root.set_resref("OnFailToOpen", utd.on_open_failed)
    root.set_string("Comment", utd.comment)

    if game == Game.K2:
        root.set_uint8("OpenLockDiff", utd.unlock_diff)
        root.set_int8("OpenLockDiffMod", utd.unlock_diff_mod)
        root.set_uint8("OpenState", utd.open_state)
        root.set_uint8("NotBlastable", utd.not_blastable)

    if use_deprecated:
        root.set_locstring("Description", utd.description)
        root.set_uint8("CloseLockDC", utd.lock_dc)
        root.set_uint8("Interruptable", utd.interruptable)
        root.set_uint16("PortraitId", utd.portrait_id)
        root.set_uint8("TrapDetectable", utd.trap_detectable)
        root.set_uint8("TrapDetectDC", utd.trap_detect_dc)
        root.set_uint8("TrapDisarmable", utd.trap_disarmable)
        root.set_uint8("DisarmDC", utd.trap_disarm_dc)
        root.set_uint8("TrapFlag", utd.trap_flag)
        root.set_uint8("TrapOneShot", utd.trap_one_shot)
        root.set_uint8("TrapType", utd.trap_type)
        root.set_uint32("Appearance", utd.unused_appearance)
        root.set_uint8("Ref", utd.reflex)
        root.set_uint8("Will", utd.willpower)
        root.set_resref("OnDisarm", utd.on_disarm)
        root.set_resref("OnSpellCastAt", utd.on_power)
        root.set_resref("OnTrapTriggered", utd.on_trap_triggered)
        root.set_uint16("LoadScreenID", utd.loadscreen_id)
        root.set_uint8("PaletteID", utd.palette_id)

    return gff


def read_utd(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
) -> UTD:
    gff = read_gff(source, offset, size)
    return construct_utd(gff)


def write_utd(
    utd: UTD,
    target: TARGET_TYPES,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
) -> None:
    gff = dismantle_utd(utd, game, use_deprecated=use_deprecated)
    write_gff(gff, target, file_format)


def bytes_utd(
    utd: UTD,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
) -> bytes:
    gff = dismantle_utd(utd, game, use_deprecated=use_deprecated)
    return bytes_gff(gff, file_format)
