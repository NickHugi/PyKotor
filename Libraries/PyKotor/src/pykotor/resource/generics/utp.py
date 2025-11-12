from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.language import LocalizedString
from pykotor.common.misc import Game, InventoryItem, ResRef
from pykotor.resource.formats.gff import GFF, GFFContent, GFFList, read_gff, write_gff
from pykotor.resource.formats.gff.gff_auto import bytes_gff
from pykotor.resource.formats.gff.gff_data import GFFStruct
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFFStruct
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class UTP:
    """Stores placeable data.

    UTP files are GFF-based format files that store placeable object definitions including
    lock/unlock mechanics, HP, inventory, scripts, and appearance.

    References:
    ----------
        vendor/reone/src/libs/resource/parser/gff/utp.cpp:36-103 (UTP parsing from GFF)
        vendor/reone/include/reone/resource/parser/gff/utp.h:34-97 (UTP structure definitions)
        vendor/Kotor.NET/Kotor.NET/Resources/KotorUTP/UTP.cs:12-75 (UTP class definition)
        vendor/NorthernLights/Generated/AuroraUTP.cs:67-69 (KotOR 2 specific fields)
        Note: UTP files are GFF format files with specific structure definitions

    Attributes:
    ----------
        resref: "TemplateResRef" field. The resource reference for this placeable template.
            Reference: reone/utp.cpp:92 (TemplateResRef field)
            Reference: reone/utp.h:87 (TemplateResRef field)
            Reference: Kotor.NET/UTP.cs:64 (TemplateResRef property)

        tag: "Tag" field. Tag identifier for this placeable.
            Reference: reone/utp.cpp:91 (Tag field)
            Reference: reone/utp.h:86 (Tag field)
            Reference: Kotor.NET/UTP.cs:63 (Tag property)

        name: "LocName" field. Localized name of the placeable.
            Reference: reone/utp.cpp:60 (LocName field)
            Reference: reone/utp.h:55 (LocName field)
            Reference: Kotor.NET/UTP.cs:35 (LocName property)

        appearance_id: "Appearance" field. Placeable appearance type identifier.
            Reference: reone/utp.cpp:39 (Appearance field)
            Reference: reone/utp.h:36 (Appearance field)
            Reference: Kotor.NET/UTP.cs:15 (Appearance property)

        has_inventory: "HasInventory" field. Whether placeable has an inventory.
            Reference: reone/utp.cpp:52 (HasInventory field)
            Reference: reone/utp.h:49 (HasInventory field)
            Reference: Kotor.NET/UTP.cs:27 (HasInventory property)

        inventory: List of InventoryItem objects in this placeable's inventory.
            Reference: reone/utp.cpp:55-57 (ItemList parsing)
            Reference: reone/utp.h:52 (ItemList vector)
            Reference: reone/utp.h:28-32 (UTP_ItemList struct)
            Reference: Kotor.NET/UTP.cs:74 (Inventory property)

        not_blastable: "NotBlastable" field. Whether placeable cannot be blasted. KotOR 2 Only.
            Reference: reone/utp.cpp:64 (NotBlastable field)
            Reference: reone/utp.h:59 (NotBlastable field)
            Reference: Kotor.NET/UTP.cs:37 (NotBlastable property)
            Reference: NorthernLights/AuroraUTP.cs:67 (NotBlastable field)

        unlock_diff: "OpenLockDiff" field. Unlock difficulty modifier. KotOR 2 Only.
            Reference: reone/utp.cpp:82 (OpenLockDiff field)
            Reference: reone/utp.h:77 (OpenLockDiff field)
            Reference: Kotor.NET/UTP.cs:55 (OpenLockDiff property)
            Reference: NorthernLights/AuroraUTP.cs:68 (OpenLockDiff field)

        unlock_diff_mod: "OpenLockDiffMod" field. Additional unlock difficulty modifier. KotOR 2 Only.
            Reference: reone/utp.cpp:83 (OpenLockDiffMod field as int)
            Reference: reone/utp.h:78 (OpenLockDiffMod field as char)
            Reference: Kotor.NET/UTP.cs:56 (OpenLockDiffMod property as sbyte)
            Reference: NorthernLights/AuroraUTP.cs:69 (OpenLockDiffMod field as Char)
            Note: Type discrepancy - reone uses char/int, Kotor.NET uses sbyte, PyKotor uses int

        on_open_failed: "OnFailToOpen" field. Script to run when placeable fails to open. KotOR 2 Only.
            Reference: reone/utp.cpp:70 (OnFailToOpen field)
            Reference: reone/utp.h:65 (OnFailToOpen field)
            Reference: Kotor.NET/UTP.cs:43 (OnFailToOpen property)

        lock_dc: "CloseLockDC" field. Difficulty class to lock placeable. KotOR 2 Only.
            Reference: reone/utp.cpp:42 (CloseLockDC field)
            Reference: reone/utp.h:39 (CloseLockDC field)
            Reference: Kotor.NET/UTP.cs:18 (CloseLockDC property)

        palette_id: "PaletteID" field. Palette identifier. Used in toolset only.
            Reference: reone/utp.cpp:84 (PaletteID field)
            Reference: reone/utp.h:79 (PaletteID field)
            Reference: Kotor.NET/UTP.cs:57 (PaletteID property)

        Note: UTP shares many fields with UTD (door). See UTD documentation for common fields
        like auto_remove_key, conversation, faction_id, plot, min1_hp, key_required, lockable,
        locked, unlock_dc, key_name, animation_state, maximum_hp, current_hp, hardness,
        fortitude, on_closed, on_damaged, on_death, on_heartbeat, on_lock, on_melee_attack,
        on_open, on_force_power, on_unlock, on_user_defined, static, useable, party_interact,
        on_end_dialog, on_inventory, on_used, comment, description, interruptable, portrait_id,
        trap_detectable, trap_detect_dc, trap_disarmable, trap_disarm_dc, trap_flag,
        trap_one_shot, trap_type, will, on_disarm, on_trap_triggered, bodybag_id, type_id.
    """

    BINARY_TYPE = ResourceType.UTP

    def __init__(  # noqa: PLR0915
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
        self.locked: bool = False
        self.lockable: bool = False

        self.unlock_dc: int = 0
        self.unlock_diff: int = 0  # KotOR 2 Only
        self.unlock_diff_mod: int = 0  # KotOR 2 Only

        self.current_hp: int = 0
        self.maximum_hp: int = 0
        self.fortitude: int = 0
        self.hardness: int = 0

        self.min1_hp: bool = False
        self.not_blastable: bool = False
        self.plot: bool = False
        self.static: bool = False
        self.useable: bool = False
        self.party_interact: bool = False

        self.on_closed: ResRef = ResRef.from_blank()
        self.on_damaged: ResRef = ResRef.from_blank()
        self.on_death: ResRef = ResRef.from_blank()
        self.on_end_dialog: ResRef = ResRef.from_blank()
        self.on_open_failed: ResRef = ResRef.from_blank()
        self.on_heartbeat: ResRef = ResRef.from_blank()
        self.on_inventory: ResRef = ResRef.from_blank()
        self.on_melee_attack: ResRef = ResRef.from_blank()
        self.on_force_power: ResRef = ResRef.from_blank()
        self.on_open: ResRef = ResRef.from_blank()
        self.on_lock: ResRef = ResRef.from_blank()
        self.on_unlock: ResRef = ResRef.from_blank()
        self.on_used: ResRef = ResRef.from_blank()
        self.on_user_defined: ResRef = ResRef.from_blank()

        self.has_inventory: bool = False
        self.inventory: list[InventoryItem] = []

        # Deprecated:
        self.description: LocalizedString = LocalizedString.from_invalid()
        self.interruptable: bool = False
        self.portrait_id: int = 0
        self.trap_detectable: bool = False
        self.trap_detect_dc: int = 0
        self.trap_disarmable: bool = False
        self.trap_disarm_dc: int = 0
        self.trap_flag: int = 0
        self.trap_one_shot: bool = False
        self.trap_type: int = 0
        self.will: int = 0
        self.reflex: int = 0
        self.on_disarm: ResRef = ResRef.from_blank()
        self.on_trap_triggered: ResRef = ResRef.from_blank()
        self.bodybag_id: int = 0
        self.type_id: int = 0
        self.palette_id: int = 0
        self.lock_dc: int = 0


def construct_utp(  # noqa: PLR0915
    gff: GFF,
) -> UTP:
    utp = UTP()

    root: GFFStruct = gff.root
    utp.tag = root.acquire("Tag", "")
    utp.name = root.acquire("LocName", LocalizedString.from_invalid())
    utp.resref = root.acquire("TemplateResRef", ResRef.from_blank())
    utp.auto_remove_key = bool(root.acquire("AutoRemoveKey", 0))
    utp.lock_dc = root.acquire("CloseLockDC", 0)
    utp.conversation = root.acquire("Conversation", ResRef.from_blank())
    utp.faction_id = root.acquire("Faction", 0)
    utp.plot = bool(root.acquire("Plot", 0))
    utp.not_blastable = bool(root.acquire("NotBlastable", 0))
    utp.min1_hp = bool(root.acquire("Min1HP", 0))
    utp.key_required = bool(root.acquire("KeyRequired", 0))
    utp.lockable = bool(root.acquire("Lockable", 0))
    utp.locked = bool(root.acquire("Locked", 0))
    utp.unlock_dc = root.acquire("OpenLockDC", 0)
    utp.key_name = root.acquire("KeyName", "")
    utp.animation_state = root.acquire("AnimationState", 0)
    utp.appearance_id = root.acquire("Appearance", 0)
    utp.maximum_hp = root.acquire("HP", 0)
    utp.current_hp = root.acquire("CurrentHP", 0)
    utp.hardness = root.acquire("Hardness", 0)
    utp.fortitude = root.acquire("Fort", 0)
    utp.on_closed = root.acquire("OnClosed", ResRef.from_blank())
    utp.on_damaged = root.acquire("OnDamaged", ResRef.from_blank())
    utp.on_death = root.acquire("OnDeath", ResRef.from_blank())
    utp.on_heartbeat = root.acquire("OnHeartbeat", ResRef.from_blank())
    utp.on_lock = root.acquire("OnLock", ResRef.from_blank())
    utp.on_melee_attack = root.acquire("OnMeleeAttacked", ResRef.from_blank())
    utp.on_open = root.acquire("OnOpen", ResRef.from_blank())
    utp.on_force_power = root.acquire("OnSpellCastAt", ResRef.from_blank())
    utp.on_unlock = root.acquire("OnUnlock", ResRef.from_blank())
    utp.on_user_defined = root.acquire("OnUserDefined", ResRef.from_blank())
    utp.has_inventory = bool(root.acquire("HasInventory", 0))
    utp.party_interact = bool(root.acquire("PartyInteract", 0))
    utp.static = bool(root.acquire("Static", 0))
    utp.useable = bool(root.acquire("Useable", 0))
    utp.on_end_dialog = root.acquire("OnEndDialogue", ResRef.from_blank())
    utp.on_inventory = root.acquire("OnInvDisturbed", ResRef.from_blank())
    utp.on_used = root.acquire("OnUsed", ResRef.from_blank())
    utp.on_open_failed = root.acquire("OnFailToOpen", ResRef.from_blank())
    utp.comment = root.acquire("Comment", "")
    utp.unlock_diff = root.acquire("OpenLockDiff", 0)
    utp.unlock_diff_mod = root.acquire("OpenLockDiffMod", 0)

    item_list: GFFList = root.acquire("ItemList", GFFList())
    for item_struct in item_list:
        resref = item_struct.acquire("InventoryRes", ResRef.from_blank())
        droppable = bool(item_struct.acquire("Dropable", 0))
        utp.inventory.append(InventoryItem(resref, droppable))

    utp.description = root.acquire("Description", LocalizedString.from_invalid())
    utp.interruptable = bool(root.acquire("Interruptable", 0))
    utp.portrait_id = root.acquire("PortraitId", 0)
    utp.trap_detectable = bool(root.acquire("TrapDetectable", 0))
    utp.trap_detect_dc = root.acquire("TrapDetectDC", 0)
    utp.trap_disarmable = bool(root.acquire("TrapDisarmable", 0))
    utp.trap_disarm_dc = root.acquire("DisarmDC", 0)
    utp.trap_flag = root.acquire("TrapFlag", 0)
    utp.trap_one_shot = bool(root.acquire("TrapOneShot", 0))
    utp.trap_type = root.acquire("TrapType", 0)
    utp.will = root.acquire("Will", 0)
    utp.reflex = root.acquire("Ref", 0)
    utp.on_disarm = root.acquire("OnDisarm", ResRef.from_blank())
    utp.on_trap_triggered = root.acquire("OnTrapTriggered", ResRef.from_blank())
    utp.bodybag_id = root.acquire("BodyBag", 0)
    utp.type_id = root.acquire("Type", 0)
    utp.palette_id = root.acquire("PaletteID", 0)

    return utp


def dismantle_utp(  # noqa: PLR0915
    utp: UTP,
    game: Game = Game.K2,
    *,
    use_deprecated: bool = True,
) -> GFF:
    gff = GFF(GFFContent.UTP)

    root: GFFStruct = gff.root
    root.set_string("Tag", utp.tag)
    root.set_locstring("LocName", utp.name)
    root.set_resref("TemplateResRef", utp.resref)
    root.set_uint8("AutoRemoveKey", utp.auto_remove_key)
    root.set_resref("Conversation", utp.conversation)
    root.set_uint32("Faction", utp.faction_id)
    root.set_uint8("Plot", utp.plot)
    root.set_uint8("Min1HP", utp.min1_hp)
    root.set_uint8("KeyRequired", utp.key_required)
    root.set_uint8("Lockable", utp.lockable)
    root.set_uint8("Locked", utp.locked)
    root.set_uint8("OpenLockDC", utp.unlock_dc)
    root.set_string("KeyName", utp.key_name)
    root.set_uint8("AnimationState", utp.animation_state)
    root.set_uint32("Appearance", utp.appearance_id)
    root.set_int16("HP", utp.maximum_hp)
    root.set_int16("CurrentHP", utp.current_hp)
    root.set_uint8("Hardness", utp.hardness)
    root.set_uint8("Fort", utp.fortitude)
    root.set_resref("OnClosed", utp.on_closed)
    root.set_resref("OnDamaged", utp.on_damaged)
    root.set_resref("OnDeath", utp.on_death)
    root.set_resref("OnHeartbeat", utp.on_heartbeat)
    root.set_resref("OnLock", utp.on_lock)
    root.set_resref("OnMeleeAttacked", utp.on_melee_attack)
    root.set_resref("OnOpen", utp.on_open)
    root.set_resref("OnSpellCastAt", utp.on_force_power)
    root.set_resref("OnUnlock", utp.on_unlock)
    root.set_resref("OnUserDefined", utp.on_user_defined)
    root.set_uint8("HasInventory", utp.has_inventory)
    root.set_uint8("PartyInteract", utp.party_interact)
    root.set_uint8("Static", utp.static)
    root.set_uint8("Useable", utp.useable)
    root.set_resref("OnEndDialogue", utp.on_end_dialog)
    root.set_resref("OnInvDisturbed", utp.on_inventory)
    root.set_resref("OnUsed", utp.on_used)
    root.set_string("Comment", utp.comment)

    item_list: GFFList = root.set_list("ItemList", GFFList())
    for i, item in enumerate(utp.inventory):
        item_struct: GFFStruct = item_list.add(i)
        item_struct.set_resref("InventoryRes", item.resref)
        item_struct.set_uint16("Repos_PosX", i)
        item_struct.set_uint16("Repos_PosY", 0)
        if item.droppable:
            item_struct.set_uint8("Dropable", value=True)

    root.set_uint8("PaletteID", utp.palette_id)

    if game.is_k2():
        root.set_uint8("NotBlastable", utp.not_blastable)
        root.set_uint8("OpenLockDiff", utp.unlock_diff)
        root.set_int8("OpenLockDiffMod", utp.unlock_diff_mod)
        root.set_resref("OnFailToOpen", utp.on_open_failed)
        root.set_uint8("CloseLockDC", utp.lock_dc)

    if use_deprecated:
        root.set_locstring("Description", utp.description)
        root.set_uint8("Interruptable", utp.interruptable)
        root.set_uint16("PortraitId", utp.portrait_id)
        root.set_uint8("TrapDetectable", utp.trap_detectable)
        root.set_uint8("TrapDetectDC", utp.trap_detect_dc)
        root.set_uint8("TrapDisarmable", utp.trap_disarmable)
        root.set_uint8("DisarmDC", utp.trap_disarm_dc)
        root.set_uint8("TrapFlag", utp.trap_flag)
        root.set_uint8("TrapOneShot", utp.trap_one_shot)
        root.set_uint8("TrapType", utp.trap_type)
        root.set_uint8("Will", utp.will)
        root.set_uint8("Ref", utp.reflex)
        root.set_resref("OnDisarm", utp.on_disarm)
        root.set_resref("OnTrapTriggered", utp.on_trap_triggered)
        root.set_uint8("BodyBag", utp.bodybag_id)
        root.set_uint8("Type", utp.type_id)

    return gff


def read_utp(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
) -> UTP:
    gff: GFF = read_gff(source, offset, size)
    return construct_utp(gff)


def write_utp(
    utp: UTP,
    target: TARGET_TYPES,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
):
    gff: GFF = dismantle_utp(utp, game, use_deprecated=use_deprecated)
    write_gff(gff, target, file_format)


def bytes_utp(
    utp: UTP,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
) -> bytes:
    gff: GFF = dismantle_utp(utp, game, use_deprecated=use_deprecated)
    return bytes_gff(gff, file_format)
