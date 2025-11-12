from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.language import LocalizedString
from pykotor.common.misc import Game, ResRef
from pykotor.resource.formats.gff import GFF, GFFContent, write_gff
from pykotor.resource.formats.gff.gff_auto import bytes_gff, read_gff
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFFStruct
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class UTD:
    """Stores door data.

    UTD files are GFF-based format files that store door definitions including
    lock/unlock mechanics, HP, scripts, and appearance.

    References:
    ----------
        vendor/reone/src/libs/resource/parser/gff/utd.cpp:28-89 (UTD parsing from GFF)
        vendor/reone/include/reone/resource/parser/gff/utd.h:28-87 (UTD structure definitions)
        vendor/reone/src/libs/game/object/door.cpp:155-211 (Door object loading from UTD)
        vendor/Kotor.NET/Kotor.NET/Resources/KotorUTD/UTD.cs:11-68 (UTD class definition)
        vendor/KotOR.js/src/module/ModuleDoor.ts:55-167 (Door module object)
        vendor/NorthernLights/Generated/AuroraUTD.cs:64-67 (KotOR 2 specific fields)
        vendor/sotor/src/save/read.rs:488 (OpenState field in save games)
        Note: UTD files are GFF format files with specific structure definitions

    Attributes:
    ----------
        resref: "TemplateResRef" field. The resource reference for this door template.
            Reference: reone/utd.cpp:80 (TemplateResRef field)
            Reference: reone/utd.h:79 (TemplateResRef field)
            Reference: Kotor.NET/UTD.cs:59 (TemplateResRef property)
            Reference: KotOR.js/ModuleDoor.ts:144 (templateResRef field)

        tag: "Tag" field. Tag identifier for this door.
            Reference: reone/utd.cpp:79 (Tag field)
            Reference: reone/utd.h:78 (Tag field)
            Reference: Kotor.NET/UTD.cs:58 (Tag property)
            Reference: KotOR.js/ModuleDoor.ts:143 (tag field)
            Reference: reone/door.cpp:156 (tag loading)

        name: "LocName" field. Localized name of the door.
            Reference: reone/utd.cpp:50 (LocName field)
            Reference: reone/utd.h:49 (LocName field)
            Reference: Kotor.NET/UTD.cs:33 (LocName property)
            Reference: KotOR.js/ModuleDoor.ts:133 (locName field)
            Reference: reone/door.cpp:157 (name loading)

        auto_remove_key: "AutoRemoveKey" field. Whether key is removed after use.
            Reference: reone/utd.cpp:32 (AutoRemoveKey field)
            Reference: reone/utd.h:31 (AutoRemoveKey field)
            Reference: Kotor.NET/UTD.cs:15 (AutoRemoveKey property)
            Reference: KotOR.js/ModuleDoor.ts:120 (autoRemoveKey field)
            Reference: reone/door.cpp:159 (autoRemoveKey loading)

        conversation: "Conversation" field. ResRef to dialog file for this door.
            Reference: reone/utd.cpp:35 (Conversation field)
            Reference: reone/utd.h:34 (Conversation field)
            Reference: Kotor.NET/UTD.cs:18 (Conversation property)
            Reference: reone/door.cpp:160 (conversation loading)

        faction_id: "Faction" field. Faction identifier.
            Reference: reone/utd.cpp:39 (Faction field)
            Reference: reone/utd.h:38 (Faction field)
            Reference: Kotor.NET/UTD.cs:22 (Faction property)
            Reference: reone/door.cpp:162 (faction loading)

        plot: "Plot" field. Whether door is plot-critical.
            Reference: reone/utd.cpp:74 (Plot field)
            Reference: reone/utd.h:73 (Plot field)
            Reference: Kotor.NET/UTD.cs:54 (Plot property)
            Reference: KotOR.js/ModuleDoor.ts:139 (plot field)
            Reference: reone/door.cpp:163 (plot loading)

        min1_hp: "Min1HP" field. Whether door HP cannot go below 1. KotOR 2 Only.
            Reference: reone/utd.cpp:52 (Min1HP field)
            Reference: reone/utd.h:52 (Min1HP field)
            Reference: Kotor.NET/UTD.cs:34 (Min1HP property)
            Reference: KotOR.js/ModuleDoor.ts:136 (min1HP field)
            Reference: reone/door.cpp:164 (minOneHP loading)

        key_required: "KeyRequired" field. Whether a key is required to unlock.
            Reference: reone/utd.cpp:46 (KeyRequired field)
            Reference: reone/utd.h:45 (KeyRequired field)
            Reference: Kotor.NET/UTD.cs:29 (KeyRequired property)
            Reference: KotOR.js/ModuleDoor.ts:131 (keyRequired field)
            Reference: reone/door.cpp:165 (keyRequired loading)

        lockable: "Lockable" field. Whether door can be locked.
            Reference: reone/utd.cpp:51 (Lockable field)
            Reference: reone/utd.h:50 (Lockable field)
            Reference: Kotor.NET/UTD.cs:31 (Lockable property)
            Reference: KotOR.js/ModuleDoor.ts:134 (lockable field)
            Reference: reone/door.cpp:166 (lockable loading)

        locked: "Locked" field. Whether door is currently locked.
            Reference: reone/utd.cpp:52 (Locked field)
            Reference: reone/utd.h:51 (Locked field)
            Reference: Kotor.NET/UTD.cs:32 (Locked property)
            Reference: KotOR.js/ModuleDoor.ts:135 (locked field)
            Reference: reone/door.cpp:167 (locked loading)

        unlock_dc: "OpenLockDC" field. Difficulty class to unlock door.
            Reference: reone/utd.cpp:69 (OpenLockDC field)
            Reference: reone/utd.h:68 (OpenLockDC field)
            Reference: Kotor.NET/UTD.cs:49 (OpenLockDC property)
            Reference: KotOR.js/ModuleDoor.ts:137 (openLockDC field)
            Reference: reone/door.cpp:168 (openLockDC loading)

        key_name: "KeyName" field. Tag of the key item required.
            Reference: reone/utd.cpp:45 (KeyName field)
            Reference: reone/utd.h:44 (KeyName field)
            Reference: Kotor.NET/UTD.cs:28 (KeyName property)
            Reference: KotOR.js/ModuleDoor.ts:130 (keyName field)
            Reference: reone/door.cpp:169 (keyName loading)

        animation_state: "AnimationState" field. Current animation state. Always 0 in files.
            Reference: reone/utd.cpp:30 (AnimationState field)
            Reference: reone/utd.h:29 (AnimationState field)
            Reference: Kotor.NET/UTD.cs:13 (AnimationState property)
            Reference: KotOR.js/ModuleDoor.ts:118 (animationState field)
            Note: reone/door.cpp:202 notes this is always 0 in files

        maximum_hp: "HP" field. Maximum hit points.
            Reference: reone/utd.cpp:42 (HP field)
            Reference: reone/utd.h:41 (HP field)
            Reference: Kotor.NET/UTD.cs:26 (HP property)
            Reference: reone/door.cpp:170 (hitPoints loading)

        current_hp: "CurrentHP" field. Current hit points.
            Reference: reone/utd.cpp:36 (CurrentHP field)
            Reference: reone/utd.h:35 (CurrentHP field)
            Reference: Kotor.NET/UTD.cs:19 (CurrentHP property)
            Reference: reone/door.cpp:171 (currentHitPoints loading)

        hardness: "Hardness" field. Damage reduction value.
            Reference: reone/utd.cpp:43 (Hardness field)
            Reference: reone/utd.h:42 (Hardness field)
            Reference: Kotor.NET/UTD.cs:25 (Hardness property)
            Reference: KotOR.js/ModuleDoor.ts:128 (hardness field)
            Reference: reone/door.cpp:172 (hardness loading)

        fortitude: "Fort" field. Fortitude save value. Always 0 in files.
            Reference: reone/utd.cpp:40 (Fort field)
            Reference: reone/utd.h:39 (Fort field)
            Reference: Kotor.NET/UTD.cs:23 (Fort property)
            Reference: KotOR.js/ModuleDoor.ts:125 (fort field)
            Reference: reone/door.cpp:173 (fortitude loading)

        appearance_id: "GenericType" field. Door appearance type identifier.
            Reference: reone/utd.cpp:41 (GenericType field)
            Reference: reone/utd.h:40 (GenericType field)
            Reference: Kotor.NET/UTD.cs:24 (GenericType property)
            Reference: KotOR.js/ModuleDoor.ts:126 (genericType field)
            Reference: reone/door.cpp:174 (genericType loading)
            Reference: reone/door.cpp:67 (used to lookup model from genericdoors.2da)

        static: "Static" field. Whether door is static (non-interactive).
            Reference: reone/utd.cpp:78 (Static field)
            Reference: reone/utd.h:77 (Static field)
            Reference: Kotor.NET/UTD.cs:57 (Static property)
            Reference: KotOR.js/ModuleDoor.ts:142 (static field)
            Reference: reone/door.cpp:175 (static loading)
            Reference: reone/door.cpp:112 (used for selectability check)

        on_closed: "OnClosed" field. Script to run when door closes. Always empty in files.
            Reference: reone/utd.cpp:56 (OnClosed field)
            Reference: reone/utd.h:55 (OnClosed field)
            Reference: Kotor.NET/UTD.cs:36 (OnClosed property)
            Reference: reone/door.cpp:177 (onClosed loading)
            Note: reone/door.cpp:177 notes this is always empty but could be useful

        on_damaged: "OnDamaged" field. Script to run when door is damaged. Always empty in files.
            Reference: reone/utd.cpp:57 (OnDamaged field)
            Reference: reone/utd.h:56 (OnDamaged field)
            Reference: Kotor.NET/UTD.cs:37 (OnDamaged property)
            Reference: reone/door.cpp:178 (onDamaged loading)
            Note: reone/door.cpp:178 notes this is always empty but could be useful

        on_death: "OnDeath" field. Script to run when door is destroyed.
            Reference: reone/utd.cpp:58 (OnDeath field)
            Reference: reone/utd.h:57 (OnDeath field)
            Reference: Kotor.NET/UTD.cs:38 (OnDeath property)
            Reference: reone/door.cpp:179 (onDeath loading)

        on_heartbeat: "OnHeartbeat" field. Script to run on heartbeat.
            Reference: reone/utd.cpp:61 (OnHeartbeat field)
            Reference: reone/utd.h:60 (OnHeartbeat field)
            Reference: Kotor.NET/UTD.cs:41 (OnHeartbeat property)
            Reference: reone/door.cpp:180 (onHeartbeat loading)

        on_lock: "OnLock" field. Script to run when door is locked. Always empty in files.
            Reference: reone/utd.cpp:62 (OnLock field)
            Reference: reone/utd.h:61 (OnLock field)
            Reference: Kotor.NET/UTD.cs:42 (OnLock property)
            Reference: reone/door.cpp:181 (onLock loading)
            Note: reone/door.cpp:181 notes this is always empty but could be useful

        on_melee: "OnMeleeAttacked" field. Script to run when door is melee attacked. Always empty in files.
            Reference: reone/utd.cpp:63 (OnMeleeAttacked field)
            Reference: reone/utd.h:62 (OnMeleeAttacked field)
            Reference: Kotor.NET/UTD.cs:43 (OnMeleeAttacked property)
            Reference: reone/door.cpp:182 (onMeleeAttacked loading)
            Note: reone/door.cpp:182 notes this is always empty but could be useful

        on_open: "OnOpen" field. Script to run when door opens.
            Reference: reone/utd.cpp:64 (OnOpen field)
            Reference: reone/utd.h:63 (OnOpen field)
            Reference: Kotor.NET/UTD.cs:44 (OnOpen property)
            Reference: reone/door.cpp:183 (onOpen loading)

        on_unlock: "OnUnlock" field. Script to run when door is unlocked. Always empty in files.
            Reference: reone/utd.cpp:67 (OnUnlock field)
            Reference: reone/utd.h:66 (OnUnlock field)
            Reference: Kotor.NET/UTD.cs:47 (OnUnlock property)
            Reference: reone/door.cpp:185 (onUnlock loading)
            Note: reone/door.cpp:185 notes this is always empty but could be useful

        on_user_defined: "OnUserDefined" field. Script to run on user-defined event.
            Reference: reone/utd.cpp:68 (OnUserDefined field)
            Reference: reone/utd.h:67 (OnUserDefined field)
            Reference: Kotor.NET/UTD.cs:48 (OnUserDefined property)
            Reference: reone/door.cpp:186 (onUserDefined loading)

        on_click: "OnClick" field. Script to run when door is clicked.
            Reference: reone/utd.cpp:55 (OnClick field)
            Reference: reone/utd.h:54 (OnClick field)
            Reference: Kotor.NET/UTD.cs:35 (OnClick property)
            Reference: reone/door.cpp:187 (onClick loading)

        on_open_failed: "OnFailToOpen" field. Script to run when door fails to open. KotOR 2 Only.
            Reference: reone/utd.cpp:60 (OnFailToOpen field)
            Reference: reone/utd.h:59 (OnFailToOpen field)
            Reference: Kotor.NET/UTD.cs:40 (OnFailToOpen property)
            Reference: reone/door.cpp:188 (onFailToOpen loading)
            Reference: KotOR.js/ModuleDoor.ts:390 (used in unlock failure handling)

        comment: "Comment" field. Developer comment. Used in toolset only.
            Reference: reone/utd.cpp:34 (Comment field)
            Reference: reone/utd.h:33 (Comment field)
            Reference: Kotor.NET/UTD.cs:17 (Comment property)
            Note: reone/door.cpp:210 notes this is toolset only

        unlock_diff: "OpenLockDiff" field. Unlock difficulty modifier. KotOR 2 Only.
            Reference: reone/utd.cpp:70 (OpenLockDiff field)
            Reference: reone/utd.h:69 (OpenLockDiff field)
            Reference: Kotor.NET/UTD.cs:50 (OpenLockDiff property)
            Reference: NorthernLights/AuroraUTD.cs:65 (OpenLockDiff field)

        unlock_diff_mod: "OpenLockDiffMod" field. Additional unlock difficulty modifier. KotOR 2 Only.
            Reference: reone/utd.cpp:71 (OpenLockDiffMod field as int)
            Reference: reone/utd.h:70 (OpenLockDiffMod field as char)
            Reference: Kotor.NET/UTD.cs:51 (OpenLockDiffMod property as sbyte)
            Reference: NorthernLights/AuroraUTD.cs:66 (OpenLockDiffMod field as Char)
            Note: Type discrepancy - reone uses char/int, Kotor.NET uses sbyte, PyKotor uses int

        open_state: "OpenState" field. Current open state (closed/open1/open2). KotOR 2 Only.
            Reference: reone/utd.cpp:72 (OpenState field)
            Reference: reone/utd.h:71 (OpenState field)
            Reference: Kotor.NET/UTD.cs:52 (OpenState property)
            Reference: NorthernLights/AuroraUTD.cs:67 (OpenState field)
            Reference: sotor/src/save/read.rs:488 (OpenState in save games)
            Reference: KotOR.js/ModuleDoor.ts:56 (openState field)

        not_blastable: "NotBlastable" field. Whether door cannot be blasted. KotOR 2 Only.
            Reference: reone/utd.cpp:54 (NotBlastable field)
            Reference: reone/utd.h:53 (NotBlastable field)
            Reference: Kotor.NET/UTD.cs:67 (NotBlastable property)
            Reference: NorthernLights/AuroraUTD.cs:64 (NotBlastable field)

        palette_id: "PaletteID" field. Palette identifier. Used in toolset only.
            Reference: reone/utd.cpp:73 (PaletteID field)
            Reference: reone/utd.h:72 (PaletteID field)
            Reference: Kotor.NET/UTD.cs:53 (PaletteID property)
            Reference: KotOR.js/ModuleDoor.ts:138 (paletteID field)
            Note: reone/door.cpp:209 notes this is toolset only

        description: "Description" field. Localized description. Not used by the game engine.
            Reference: reone/utd.cpp:37 (Description field)
            Reference: reone/utd.h:36 (Description field)
            Reference: Kotor.NET/UTD.cs:20 (Description property)
            Reference: KotOR.js/ModuleDoor.ts:123 (description field)
            Note: reone/door.cpp:192 notes this is always -1 and unused

        lock_dc: "CloseLockDC" field. Difficulty class to lock door. Not used by the game engine.
            Reference: reone/utd.cpp:33 (CloseLockDC field)
            Reference: reone/utd.h:32 (CloseLockDC field)
            Reference: Kotor.NET/UTD.cs:16 (CloseLockDC property)
            Reference: KotOR.js/ModuleDoor.ts:121 (closeLockDC field)
            Note: reone/door.cpp:193 notes this is always 0 and unused

        interruptable: "Interruptable" field. Whether door can be interrupted. Not used by the game engine.
            Reference: reone/utd.cpp:44 (Interruptable field)
            Reference: reone/utd.h:43 (Interruptable field)
            Reference: Kotor.NET/UTD.cs:27 (Interruptable property)
            Reference: KotOR.js/ModuleDoor.ts:129 (interruptable field)
            Reference: reone/door.cpp:161 (interruptable loading)
            Note: reone/door.cpp:161 loads this but it's unused

        portrait_id: "PortraitId" field. Portrait identifier. Not used by the game engine.
            Reference: reone/utd.cpp:76 (PortraitId field)
            Reference: reone/utd.h:75 (PortraitId field)
            Reference: Kotor.NET/UTD.cs:55 (PortraitId property)
            Reference: KotOR.js/ModuleDoor.ts:140 (portraitId field)
            Note: reone/door.cpp:194 notes this is not applicable and mostly 0

        trap_detectable: "TrapDetectable" field. Whether trap is detectable. Not used by the game engine.
            Reference: reone/utd.cpp:82 (TrapDetectable field)
            Reference: reone/utd.h:81 (TrapDetectable field)
            Reference: Kotor.NET/UTD.cs:60 (TrapDetectable property)
            Reference: KotOR.js/ModuleDoor.ts:146 (trapDetectable field)
            Note: reone/door.cpp:195 notes this is not applicable and always 1

        trap_detect_dc: "TrapDetectDC" field. Difficulty class to detect trap. Not used by the game engine.
            Reference: reone/utd.cpp:81 (TrapDetectDC field)
            Reference: reone/utd.h:80 (TrapDetectDC field)
            Reference: Kotor.NET/UTD.cs:61 (TrapDetectDC property)
            Reference: KotOR.js/ModuleDoor.ts:145 (trapDetectDC field)
            Note: reone/door.cpp:196 notes this is not applicable and always 0

        trap_disarmable: "TrapDisarmable" field. Whether trap is disarmable. Not used by the game engine.
            Reference: reone/utd.cpp:83 (TrapDisarmable field)
            Reference: reone/utd.h:82 (TrapDisarmable field)
            Reference: Kotor.NET/UTD.cs:62 (TrapDisarmable property)
            Reference: KotOR.js/ModuleDoor.ts:147 (trapDisarmable field)
            Note: reone/door.cpp:197 notes this is not applicable and always 1

        trap_disarm_dc: "DisarmDC" field. Difficulty class to disarm trap. Not used by the game engine.
            Reference: reone/utd.cpp:38 (DisarmDC field)
            Reference: reone/utd.h:37 (DisarmDC field)
            Reference: Kotor.NET/UTD.cs:21 (DisarmDC property)
            Reference: KotOR.js/ModuleDoor.ts:124 (disarmDC field)
            Note: reone/door.cpp:198 notes this is not applicable and mostly 28

        trap_flag: "TrapFlag" field. Whether door has a trap. Not used by the game engine.
            Reference: reone/utd.cpp:84 (TrapFlag field)
            Reference: reone/utd.h:83 (TrapFlag field)
            Reference: Kotor.NET/UTD.cs:63 (TrapFlag property)
            Reference: KotOR.js/ModuleDoor.ts:148 (trapFlag field)
            Note: reone/door.cpp:199 notes this is not applicable and always 0

        trap_one_shot: "TrapOneShot" field. Whether trap fires once. Not used by the game engine.
            Reference: reone/utd.cpp:85 (TrapOneShot field)
            Reference: reone/utd.h:84 (TrapOneShot field)
            Reference: Kotor.NET/UTD.cs:64 (TrapOneShot property)
            Reference: KotOR.js/ModuleDoor.ts:149 (trapOneShot field)
            Note: reone/door.cpp:200 notes this is not applicable and always 1

        trap_type: "TrapType" field. Type of trap. Not used by the game engine.
            Reference: reone/utd.cpp:86 (TrapType field)
            Reference: reone/utd.h:85 (TrapType field)
            Reference: Kotor.NET/UTD.cs:65 (TrapType property)
            Reference: KotOR.js/ModuleDoor.ts:150 (trapType field)
            Note: reone/door.cpp:201 notes this is not applicable

        unused_appearance: "Appearance" field. Appearance identifier. Not used by the game engine.
            Reference: reone/utd.cpp:31 (Appearance field)
            Reference: reone/utd.h:30 (Appearance field)
            Reference: Kotor.NET/UTD.cs:14 (Appearance property)
            Note: reone/door.cpp:203 notes this is always 0 and unused

        reflex: "Ref" field. Reflex save value. Not used by the game engine.
            Reference: reone/utd.cpp:77 (Ref field)
            Reference: reone/utd.h:76 (Ref field)
            Reference: Kotor.NET/UTD.cs:56 (Ref property)
            Reference: KotOR.js/ModuleDoor.ts:141 (ref field)
            Note: reone/door.cpp:204 notes this is always 0 and unused

        willpower: "Will" field. Will save value. Not used by the game engine.
            Reference: reone/utd.cpp:87 (Will field)
            Reference: reone/utd.h:86 (Will field)
            Reference: Kotor.NET/UTD.cs:66 (Will property)
            Reference: KotOR.js/ModuleDoor.ts:151 (will field)
            Note: reone/door.cpp:205 notes this is always 0 and unused

        on_disarm: "OnDisarm" field. Script to run when trap is disarmed. Not used by the game engine.
            Reference: reone/utd.cpp:59 (OnDisarm field)
            Reference: reone/utd.h:58 (OnDisarm field)
            Reference: Kotor.NET/UTD.cs:39 (OnDisarm property)
            Note: reone/door.cpp:206 notes this is not applicable and always empty

        on_power: "OnSpellCastAt" field. Script to run when spell is cast at door. Not used by the game engine.
            Reference: reone/utd.cpp:65 (OnSpellCastAt field)
            Reference: reone/utd.h:64 (OnSpellCastAt field)
            Reference: Kotor.NET/UTD.cs:45 (OnSpellCastAt property)
            Note: reone/door.cpp:184 notes this is always empty but could be useful

        on_trap_triggered: "OnTrapTriggered" field. Script to run when trap triggers. Not used by the game engine.
            Reference: reone/utd.cpp:66 (OnTrapTriggered field)
            Reference: reone/utd.h:65 (OnTrapTriggered field)
            Reference: Kotor.NET/UTD.cs:46 (OnTrapTriggered property)
            Note: reone/door.cpp:207 notes this is not applicable and always empty

        loadscreen_id: "LoadScreenID" field. Load screen identifier. Not used by the game engine.
            Reference: reone/utd.cpp:49 (LoadScreenID field)
            Reference: reone/utd.h:48 (LoadScreenID field)
            Reference: Kotor.NET/UTD.cs:30 (LoadScreenID property)
            Reference: KotOR.js/ModuleDoor.ts:132 (loadScreenID field)
            Note: reone/door.cpp:208 notes this is always 0 and unused
    """

    BINARY_TYPE = ResourceType.UTD

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

    root: GFFStruct = gff.root
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

    if game.is_k2():
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
    gff: GFF = read_gff(source, offset, size)
    return construct_utd(gff)


def write_utd(
    utd: UTD,
    target: TARGET_TYPES,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
):
    gff: GFF = dismantle_utd(utd, game, use_deprecated=use_deprecated)
    write_gff(gff, target, file_format)


def bytes_utd(
    utd: UTD,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
) -> bytes:
    gff: GFF = dismantle_utd(utd, game, use_deprecated=use_deprecated)
    return bytes_gff(gff, file_format)
