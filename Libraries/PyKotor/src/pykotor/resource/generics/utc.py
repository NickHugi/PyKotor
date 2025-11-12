from __future__ import annotations

from typing import TYPE_CHECKING

from loggerplus import RobustLogger

from pykotor.common.language import LocalizedString
from pykotor.common.misc import EquipmentSlot, Game, InventoryItem, ResRef
from pykotor.resource.formats.gff import GFF, GFFContent, GFFList, read_gff, write_gff
from pykotor.resource.formats.gff.gff_auto import bytes_gff
from pykotor.resource.formats.gff.gff_data import GFFFieldType
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class UTC:
    """Stores creature data.

    UTC files are GFF-based format files that store creature definitions including
    stats, appearance, inventory, feats, and script hooks.

    References:
    ----------
        vendor/KotOR-dotNET/AuroraParsers/UTCObject.cs:9 (UTC parser)
        vendor/KotOR.js/src/module/ModuleCreature.ts:73-100 (Creature module object)
        vendor/Kotor.NET/Kotor.NET/Resources/KotorUTC/UTC.cs:13-119 (UTC class definition)
        vendor/reone/include/reone/resource/parser/gff/utc.h:66-142 (UTC structure definitions)
        vendor/reone/src/libs/game/object/creature.cpp:1377 (Creature object loading from UTC)
        vendor/reone/src/libs/resource/parser/gff/utc.cpp:82-178 (UTC parsing from GFF)
        Note: UTC files are GFF format files with specific structure definitions

    Attributes:
    ----------
        resref: "TemplateResRef" field. The resource reference for this creature template.
            Reference: reone/utc.h:134 (TemplateResRef field)
            Reference: Kotor.NET/UTC.cs:15 (ResRef property)
            Reference: KotOR.js/ModuleCreature.ts:73 (inherited from ModuleObject)

        tag: "Tag" field. The tag identifier for this creature.
            Reference: reone/utc.cpp:132 (Tag field)
            Reference: Kotor.NET/UTC.cs:18 (Tag property)

        comment: "Comment" field. Developer comment for this creature.
            Reference: reone/utc.cpp:93 (Comment field)
            Reference: Kotor.NET/UTC.cs:19 (Comment property)
            Reference: KotOR.js/ModuleCreature.ts:96 (comment field)

        conversation: "Conversation" field. ResRef to the dialog file for this creature.
            Reference: reone/utc.cpp:95 (Conversation field)
            Reference: Kotor.NET/UTC.cs:16 (Conversation property)

        first_name: "FirstName" field. Localized first name of the creature.
            Reference: reone/utc.cpp:109 (FirstName field)
            Reference: Kotor.NET/UTC.cs:21 (FirstName property)

        last_name: "LastName" field. Localized last name of the creature.
            Reference: reone/utc.cpp:122 (LastName field)
            Reference: Kotor.NET/UTC.cs:22 (LastName property)

        subrace_id: "SubraceIndex" field. Subrace index identifier.
            Reference: reone/utc.cpp:131 (SubraceIndex field)
            Reference: Kotor.NET/UTC.cs:25 (SubraceID property)

        perception_id: "PerceptionRange" field. Perception range value.
            Reference: reone/utc.cpp:132 (PerceptionRange field)
            Reference: Kotor.NET/UTC.cs:27 (PerceptionID property)

        race_id: "Race" field. Race identifier.
            Reference: reone/utc.cpp:136 (Race field)
            Reference: Kotor.NET/UTC.cs:24 (RaceID property)

        appearance_id: "Appearance_Type" field. Appearance type identifier.
            Reference: reone/utc.cpp:84 (Appearance_Type field)
            Reference: Kotor.NET/UTC.cs:28 (AppearanceID property)

        gender_id: "Gender" field. Gender identifier.
            Reference: reone/utc.cpp:111 (Gender field)
            Reference: Kotor.NET/UTC.cs:29 (GenderID property)

        faction_id: "FactionID" field. Faction identifier.
            Reference: reone/utc.cpp:105 (FactionID field)
            Reference: Kotor.NET/UTC.cs:30 (FactionID property)

        walkrate_id: "WalkRate" field. Walk rate identifier.
            Reference: reone/utc.cpp:136 (WalkRate field)
            Reference: Kotor.NET/UTC.cs:31 (WalkRateID property)

        soundset_id: "SoundSetFile" field. Soundset file identifier.
            Reference: reone/utc.cpp:127 (SoundSetFile field)
            Reference: Kotor.NET/UTC.cs:32 (SoundsetID property)

        portrait_id: "PortraitId" field. Portrait identifier.
            Reference: reone/utc.cpp:135 (PortraitId field)
            Reference: Kotor.NET/UTC.cs:26 (PortraitID property)

        body_variation: "BodyVariation" field. Body variation index.
            Reference: reone/utc.cpp:87 (BodyVariation field)
            Reference: Kotor.NET/UTC.cs:38 (BodyVariation property)
            Reference: KotOR.js/ModuleCreature.ts:82 (bodyVariation field)

        texture_variation: "TextureVar" field. Texture variation index.
            Reference: reone/utc.cpp:135 (TextureVar field)
            Reference: Kotor.NET/UTC.cs:39 (TextureVariation property)

        not_reorienting: "NotReorienting" field. Whether creature should not reorient.
            Reference: reone/utc.cpp:129 (NotReorienting field)
            Reference: Kotor.NET/UTC.cs:41 (NotReorientating property)

        party_interact: "PartyInteract" field. Whether party members can interact.
            Reference: reone/utc.cpp:131 (PartyInteract field)
            Reference: Kotor.NET/UTC.cs:42 (PartyInteract property)

        no_perm_death: "NoPermDeath" field. Whether creature cannot permanently die.
            Reference: reone/utc.cpp:128 (NoPermDeath field)
            Reference: Kotor.NET/UTC.cs:43 (NoPermanentDeath property)

        min1_hp: "Min1HP" field. Whether creature HP cannot go below 1.
            Reference: reone/utc.cpp:125 (Min1HP field)
            Reference: Kotor.NET/UTC.cs:44 (Min1HP property)

        plot: "Plot" field. Whether creature is plot-critical.
            Reference: reone/utc.cpp:134 (Plot field)
            Reference: Kotor.NET/UTC.cs:45 (Plot property)

        interruptable: "Interruptable" field. Whether creature can be interrupted.
            Reference: reone/utc.cpp:117 (Interruptable field)
            Reference: Kotor.NET/UTC.cs:46 (Interruptable property)

        is_pc: "IsPC" field. Whether creature is a player character.
            Reference: reone/utc.cpp:118 (IsPC field)
            Reference: Kotor.NET/UTC.cs:47 (IsPC property)

        disarmable: "Disarmable" field. Whether creature can be disarmed.
            Reference: reone/utc.cpp:101 (Disarmable field)
            Reference: Kotor.NET/UTC.cs:48 (Disarmable property)
            Reference: KotOR.js/ModuleCreature.ts:100 (disarmable field)

        alignment: "GoodEvil" field. Alignment value (good/evil axis).
            Reference: reone/utc.cpp:112 (GoodEvil field)
            Reference: Kotor.NET/UTC.cs:52 (Alignment property)

        challenge_rating: "ChallengeRating" field. Challenge rating value.
            Reference: reone/utc.cpp:89 (ChallengeRating field)
            Reference: Kotor.NET/UTC.cs:54 (ChallengeRating property)
            Reference: KotOR.js/ModuleCreature.ts:94 (challengeRating field)

        blindspot: "BlindSpot" field. Blind spot value. KotOR 2 Only.
            Reference: reone/utc.cpp:85 (BlindSpot field)
            Reference: Kotor.NET/UTC.cs:55 (Blindspot property)

        multiplier_set: "MultiplierSet" field. Multiplier set identifier. KotOR 2 Only.
            Reference: reone/utc.cpp:126 (MultiplierSet field)
            Reference: Kotor.NET/UTC.cs:56 (MultiplierSet property)

        natural_ac: "NaturalAC" field. Natural armor class value.
            Reference: reone/utc.cpp:127 (NaturalAC field)
            Reference: Kotor.NET/UTC.cs:58 (NaturalAC property)

        reflex_bonus: "refbonus" field. Reflex save bonus.
            Reference: reone/utc.cpp:140 (refbonus field)
            Reference: Kotor.NET/UTC.cs:59 (ReflexBonus property)
            Reference: KotOR.js/ModuleCreature.ts:91 (refbonus field)

        willpower_bonus: "willbonus" field. Will save bonus.
            Reference: reone/utc.cpp:141 (willbonus field)
            Reference: Kotor.NET/UTC.cs:60 (WillBonus property)
            Reference: KotOR.js/ModuleCreature.ts:92 (willbonus field)

        fortitude_bonus: "fortbonus" field. Fortitude save bonus.
            Reference: reone/utc.cpp:139 (fortbonus field)
            Reference: Kotor.NET/UTC.cs:61 (FortitudeBonus property)
            Reference: KotOR.js/ModuleCreature.ts:90 (fortbonus field)

        strength: "Str" field. Strength ability score.
            Reference: reone/utc.cpp:129 (Str field)
            Reference: Kotor.NET/UTC.cs:79 (Strength property)
            Reference: KotOR.js/ModuleCreature.ts:88 (str field)

        dexterity: "Dex" field. Dexterity ability score.
            Reference: reone/utc.cpp:100 (Dex field)
            Reference: Kotor.NET/UTC.cs:80 (Dexterity property)
            Reference: KotOR.js/ModuleCreature.ts:86 (dex field)

        constitution: "Con" field. Constitution ability score.
            Reference: reone/utc.cpp:94 (Con field)
            Reference: Kotor.NET/UTC.cs:81 (Constitution property)
            Reference: KotOR.js/ModuleCreature.ts:85 (con field)

        intelligence: "Int" field. Intelligence ability score.
            Reference: reone/utc.cpp:116 (Int field)
            Reference: Kotor.NET/UTC.cs:82 (Intelligence property)
            Reference: KotOR.js/ModuleCreature.ts:87 (int field)

        wisdom: "Wis" field. Wisdom ability score.
            Reference: reone/utc.cpp:138 (Wis field)
            Reference: Kotor.NET/UTC.cs:83 (Wisdom property)
            Reference: KotOR.js/ModuleCreature.ts:89 (wis field)

        charisma: "Cha" field. Charisma ability score.
            Reference: reone/utc.cpp:88 (Cha field)
            Reference: Kotor.NET/UTC.cs:84 (Charisma property)
            Reference: KotOR.js/ModuleCreature.ts:84 (cha field)

        current_hp: "CurrentHitPoints" field. Current hit points.
            Reference: reone/utc.cpp:97 (CurrentHitPoints field)
            Reference: Kotor.NET/UTC.cs:64 (CurrentHP property)
            Reference: KotOR.js/ModuleCreature.ts:98 (currentHitPoints field)

        max_hp: "MaxHitPoints" field. Maximum hit points.
            Reference: reone/utc.cpp:124 (MaxHitPoints field)
            Reference: Kotor.NET/UTC.cs:65 (MaxHP property)

        hp: "HitPoints" field. Base hit points.
            Reference: reone/utc.cpp:113 (HitPoints field)
            Reference: Kotor.NET/UTC.cs:63 (HP property)

        fp: "CurrentForce" field. Current force points.
            Reference: reone/utc.cpp:96 (CurrentForce field)
            Reference: Kotor.NET/UTC.cs:67 (FP property)
            Reference: KotOR.js/ModuleCreature.ts:97 (currentForce field)

        max_fp: "ForcePoints" field. Maximum force points.
            Reference: reone/utc.cpp:110 (ForcePoints field)
            Reference: Kotor.NET/UTC.cs:68 (MaxFP property)

        on_end_dialog: "ScriptEndDialogu" field. Script to run when dialog ends.
            Reference: reone/utc.cpp:142 (ScriptEndDialogu field)
            Reference: Kotor.NET/UTC.cs:87 (OnEndDialog property)

        on_blocked: "ScriptOnBlocked" field. Script to run when blocked.
            Reference: reone/utc.cpp:145 (ScriptOnBlocked field)
            Reference: Kotor.NET/UTC.cs:88 (OnBlocked property)

        on_heartbeat: "ScriptHeartbeat" field. Script to run on heartbeat.
            Reference: reone/utc.cpp:144 (ScriptHeartbeat field)
            Reference: Kotor.NET/UTC.cs:89 (OnHeartbeat property)

        on_notice: "ScriptOnNotice" field. Script to run when noticing something.
            Reference: reone/utc.cpp:146 (ScriptOnNotice field)
            Reference: Kotor.NET/UTC.cs:90 (OnNotice property)

        on_spell: "ScriptSpellAt" field. Script to run when spell is cast at creature.
            Reference: reone/utc.cpp:149 (ScriptSpellAt field)
            Reference: Kotor.NET/UTC.cs:91 (OnSpell property)

        on_attacked: "ScriptAttacked" field. Script to run when attacked.
            Reference: reone/utc.cpp:137 (ScriptAttacked field)
            Reference: Kotor.NET/UTC.cs:92 (OnAttack property)

        on_damaged: "ScriptDamaged" field. Script to run when damaged.
            Reference: reone/utc.cpp:138 (ScriptDamaged field)
            Reference: Kotor.NET/UTC.cs:93 (OnDamaged property)

        on_disturbed: "ScriptDisturbed" field. Script to run when disturbed.
            Reference: reone/utc.cpp:141 (ScriptDisturbed field)
            Reference: Kotor.NET/UTC.cs:94 (OnDisturbed property)

        on_end_round: "ScriptEndRound" field. Script to run at end of combat round.
            Reference: reone/utc.cpp:143 (ScriptEndRound field)
            Reference: Kotor.NET/UTC.cs:95 (OnEndRound property)

        on_dialog: "ScriptDialogue" field. Script to run when dialog starts.
            Reference: reone/utc.cpp:140 (ScriptDialogue field)
            Reference: Kotor.NET/UTC.cs:96 (OnDialog property)

        on_spawn: "ScriptSpawn" field. Script to run when creature spawns.
            Reference: reone/utc.cpp:148 (ScriptSpawn field)
            Reference: Kotor.NET/UTC.cs:97 (OnSpawn property)

        on_rested: "ScriptRested" field. Script to run when creature rests. Not used by engine.
            Reference: reone/utc.cpp:147 (ScriptRested field)
            Reference: Kotor.NET/UTC.cs:98 (OnRested property)

        on_death: "ScriptDeath" field. Script to run when creature dies.
            Reference: reone/utc.cpp:139 (ScriptDeath field)
            Reference: Kotor.NET/UTC.cs:99 (OnDeath property)

        on_user_defined: "ScriptUserDefine" field. Script to run on user-defined event.
            Reference: reone/utc.cpp:150 (ScriptUserDefine field)
            Reference: Kotor.NET/UTC.cs:100 (OnUserDefined property)

        ignore_cre_path: "IgnoreCrePath" field. Whether to ignore creature pathfinding. KotOR 2 Only.
            Reference: reone/utc.cpp:115 (IgnoreCrePath field)
            Reference: Kotor.NET/UTC.cs:49 (IgnoreCreaturePath property)

        hologram: "Hologram" field. Whether creature is a hologram. KotOR 2 Only.
            Reference: reone/utc.cpp:114 (Hologram field)
            Reference: Kotor.NET/UTC.cs:50 (Hologram property)

        palette_id: "PaletteID" field. Palette identifier. Used in toolset only.
            Reference: reone/utc.cpp:130 (PaletteID field)
            Reference: Kotor.NET/UTC.cs:36 (PaletteID property)

        bodybag_id: "BodyBag" field. Body bag identifier. Not used by the game engine.
            Reference: reone/utc.cpp:86 (BodyBag field)
            Reference: Kotor.NET/UTC.cs:81 (bodyBag field)

        deity: "Deity" field. Deity name. Not used by the game engine.
            Reference: reone/utc.cpp:98 (Deity field)
            Reference: Kotor.NET/UTC.cs:99 (deity field)

        description: "Description" field. Localized description. Not used by the game engine.
            Reference: reone/utc.cpp:99 (Description field)

        lawfulness: "LawfulChaotic" field. Lawfulness value. Not used by the game engine.
            Reference: reone/utc.cpp:123 (LawfulChaotic field)

        phenotype_id: "Phenotype" field. Phenotype identifier. Not used by the game engine.
            Reference: reone/utc.cpp:133 (Phenotype field)

        subrace_name: "Subrace" field. Subrace name. Not used by the game engine.
            Reference: reone/utc.cpp:130 (Subrace field)

        classes: List of UTCClass objects representing creature classes and levels.
            Reference: reone/utc.cpp:90-92 (ClassList parsing)
            Reference: reone/utc.h:73 (ClassList vector)
            Reference: Kotor.NET/UTC.cs:101+ (Classes property)

        feats: List of feat identifiers.
            Reference: reone/utc.cpp:106-108 (FeatList parsing)
            Reference: reone/utc.h:85 (FeatList vector)

        inventory: List of InventoryItem objects in creature's inventory.
            Reference: reone/utc.cpp:119-121 (ItemList parsing)
            Reference: reone/utc.h:96 (ItemList vector)

        equipment: Dictionary mapping EquipmentSlot to InventoryItem for equipped items.
            Reference: reone/utc.cpp:102-104 (Equip_ItemList parsing)
            Reference: reone/utc.h:83 (Equip_ItemList vector)
    """

    BINARY_TYPE = ResourceType.UTC

    def __init__(  # noqa: PLR0915
        self,
    ):
        # internal use only, to preserve the original order:
        self._original_feat_mapping: dict[int, int] = {}
        self._extra_unimplemented_skills: list[int] = []

        self.resref: ResRef = ResRef.from_blank()
        self.conversation: ResRef = ResRef.from_blank()
        self.tag: str = ""
        self.comment: str = ""

        self.first_name: LocalizedString = LocalizedString.from_invalid()
        self.last_name: LocalizedString = LocalizedString.from_invalid()

        self.subrace_id: int = 0
        self.portrait_id: int = 0
        self.perception_id: int = 0
        self.race_id: int = 0
        self.appearance_id: int = 0
        self.gender_id: int = 0
        self.faction_id: int = 0
        self.walkrate_id: int = 0
        self.soundset_id: int = 0
        self.save_will: int = 0
        self.save_fortitude: int = 0
        self.morale: int = 0
        self.morale_recovery: int = 0
        self.morale_breakpoint: int = 0

        self.body_variation: int = 0
        self.texture_variation: int = 0

        self.portrait_resref: ResRef = ResRef.from_blank()

        self.not_reorienting: bool = False
        self.party_interact: bool = False
        self.no_perm_death: bool = False
        self.min1_hp: bool = False
        self.plot: bool = False
        self.interruptable: bool = False
        self.is_pc: bool = False  # ???
        self.disarmable: bool = False  # ???
        self.ignore_cre_path: bool = False  # KotOR 2 Only
        self.hologram: bool = False  # KotOR 2 Only
        self.will_not_render: bool = False  # Kotor 2 Only

        self.alignment: int = 0
        self.challenge_rating: float = 0.0
        self.blindspot: float = 0.0  # KotOR 2 Only
        self.multiplier_set: int = 0  # KotOR 2 Only

        self.natural_ac: int = 0
        self.reflex_bonus: int = 0
        self.willpower_bonus: int = 0
        self.fortitude_bonus: int = 0

        self.current_hp: int = 0
        self.max_hp: int = 0
        self.hp: int = 0

        self.max_fp: int = 0
        self.fp: int = 0

        self.strength: int = 0
        self.dexterity: int = 0
        self.constitution: int = 0
        self.intelligence: int = 0
        self.wisdom: int = 0
        self.charisma: int = 0

        self.computer_use: int = 0
        self.demolitions: int = 0
        self.stealth: int = 0
        self.awareness: int = 0
        self.persuade: int = 0
        self.repair: int = 0
        self.security: int = 0
        self.treat_injury: int = 0

        self.on_end_dialog: ResRef = ResRef.from_blank()
        self.on_blocked: ResRef = ResRef.from_blank()
        self.on_heartbeat: ResRef = ResRef.from_blank()
        self.on_notice: ResRef = ResRef.from_blank()
        self.on_spell: ResRef = ResRef.from_blank()
        self.on_attacked: ResRef = ResRef.from_blank()
        self.on_damaged: ResRef = ResRef.from_blank()
        self.on_disturbed: ResRef = ResRef.from_blank()
        self.on_end_round: ResRef = ResRef.from_blank()
        self.on_dialog: ResRef = ResRef.from_blank()
        self.on_spawn: ResRef = ResRef.from_blank()
        self.on_rested: ResRef = ResRef.from_blank()
        self.on_death: ResRef = ResRef.from_blank()
        self.on_user_defined: ResRef = ResRef.from_blank()

        self.classes: list[UTCClass] = []
        self.feats: list[int] = []
        self.inventory: list[InventoryItem] = []
        self.equipment: dict[EquipmentSlot, InventoryItem] = {}

        # Deprecated:
        self.palette_id: int = 0
        self.bodybag_id: int = 1
        self.deity: str = ""
        self.description: LocalizedString = LocalizedString.from_invalid()
        self.lawfulness: int = 0
        self.phenotype_id: int = 0
        # self.on_rested: ResRef = ResRef.from_blank()
        self.subrace_name: str = ""


class UTCClass:
    """Represents a creature class with its level and known powers.

    References:
    ----------
        vendor/reone/include/reone/resource/parser/gff/utc.h:60-64 (UTC_ClassList struct)
        vendor/reone/src/libs/resource/parser/gff/utc.cpp:72-80 (UTC_ClassList parsing)
        vendor/reone/src/libs/resource/parser/gff/utc.cpp:28-34 (UTC_ClassList_KnownList0 parsing)
        vendor/Kotor.NET/Kotor.NET/Resources/KotorUTC/UTC.cs:101+ (Classes property)
        vendor/KotOR.js/src/module/ModuleCreature.ts:95 (classes field)

    Attributes:
    ----------
        class_id: The class identifier.
            Reference: reone/utc.cpp:74 (Class field)
            Reference: reone/utc.h:61 (Class field)

        class_level: The level in this class.
            Reference: reone/utc.cpp:75 (ClassLevel field)
            Reference: reone/utc.h:62 (ClassLevel field)

        powers: List of spell/power identifiers known by this class.
            Reference: reone/utc.cpp:76-78 (KnownList0 parsing)
            Reference: reone/utc.h:63 (KnownList0 vector)
    """
    def __init__(
        self,
        class_id: int,
        class_level: int = 0,
    ):
        # internal use only, to preserve the original order:
        self._original_powers_mapping: dict[int, int] = {}

        self.class_id: int = class_id
        self.class_level: int = class_level
        self.powers: list[int] = []

    def __repr__(
        self,
    ):
        return f"{self.__class__.__name__}(class_id={self.class_id}, class_level={self.class_level})"

    def __eq__(
        self,
        other: UTCClass | object,
    ):
        if self is other:
            return True
        if isinstance(other, UTCClass):
            return self.class_id == other.class_id and self.class_level == self.class_level
        return NotImplemented


def construct_utc(
    gff: GFF,
) -> UTC:
    """Constructs a UTC object from a GFF structure.
    
    Parses UTC (creature template) data from a GFF file, reading all fields
    including stats, skills, classes, feats, inventory, and equipment.
    
    References:
    ----------
        vendor/reone/src/libs/resource/parser/gff/utc.cpp:82-171 (parseUTC function)
        vendor/Kotor.NET/Kotor.NET/Resources/KotorUTC/UTCCompiler.cs:1-200 (UTC compilation from GFF)
        vendor/KotOR.js/src/module/ModuleCreature.ts:3231 (UTC loading via ResourceLoader)
        vendor/xoreos-tools/src/xml/utcdumper.cpp (UTC to XML conversion)
        Original BioWare Odyssey Engine (UTC GFF structure specification)
    """
    utc = UTC()

    root = gff.root
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:162 (TemplateResRef field)
    # vendor/Kotor.NET/Kotor.NET/Resources/KotorUTC/UTC.cs:15 (ResRef property)
    utc.resref = root.acquire("TemplateResRef", ResRef.from_blank())
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:132 (Tag field)
    utc.tag = root.acquire("Tag", "", str)
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:93 (Comment field)
    utc.comment = root.acquire("Comment", "", str)
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:95 (Conversation field)
    utc.conversation = root.acquire("Conversation", ResRef.from_blank())

    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:109 (FirstName field as pair<int, string>)
    # vendor/Kotor.NET/Kotor.NET/Resources/KotorUTC/UTC.cs:21 (FirstName property)
    utc.first_name = root.acquire("FirstName", LocalizedString.from_invalid())
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:122 (LastName field as pair<int, string>)
    utc.last_name = root.acquire("LastName", LocalizedString.from_invalid())

    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:131 (SubraceIndex field)
    utc.subrace_id = root.acquire("SubraceIndex", 0)
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:132 (PerceptionRange field)
    utc.perception_id = root.acquire("PerceptionRange", 0)
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:136 (Race field)
    utc.race_id = root.acquire("Race", 0)
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:84 (Appearance_Type field)
    utc.appearance_id = root.acquire("Appearance_Type", 0)
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:111 (Gender field)
    utc.gender_id = root.acquire("Gender", 0)
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:105 (FactionID field)
    utc.faction_id = root.acquire("FactionID", 0)
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:136 (WalkRate field as int)
    utc.walkrate_id = root.acquire("WalkRate", 0)
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:154 (SoundSetFile field)
    utc.soundset_id = root.acquire("SoundSetFile", 0)
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:135 (PortraitId field)
    utc.portrait_id = root.acquire("PortraitId", 0)
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:130 (PaletteID field, toolset-only)
    utc.palette_id = root.acquire("PaletteID", 0)
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:86 (BodyBag field, deprecated)
    utc.bodybag_id = root.acquire("BodyBag", 0)

    # TODO(th3w1zard1): Add these seemingly missing fields into UTCEditor?
    utc.portrait_resref = root.acquire("Portrait", ResRef.from_blank())
    utc.save_will = root.acquire("SaveWill", 0)
    utc.save_fortitude = root.acquire("SaveFortitude", 0)
    utc.morale = root.acquire("Morale", 0)
    utc.morale_recovery = root.acquire("MoraleRecovery", 0)
    utc.morale_breakpoint = root.acquire("MoraleBreakpoint", 0)

    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:87 (BodyVariation field)
    utc.body_variation = root.acquire("BodyVariation", 0)
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:135 (TextureVar field)
    utc.texture_variation = root.acquire("TextureVar", 0)

    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:129 (NotReorienting field)
    utc.not_reorienting = bool(root.acquire("NotReorienting", 0))
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:131 (PartyInteract field)
    utc.party_interact = bool(root.acquire("PartyInteract", 0))
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:128 (NoPermDeath field)
    utc.no_perm_death = bool(root.acquire("NoPermDeath", 0))
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:125 (Min1HP field)
    utc.min1_hp = bool(root.acquire("Min1HP", 0))
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:134 (Plot field)
    utc.plot = bool(root.acquire("Plot", 0))
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:117 (Interruptable field)
    utc.interruptable = bool(root.acquire("Interruptable", 0))
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:118 (IsPC field)
    utc.is_pc = bool(root.acquire("IsPC", 0))
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:101 (Disarmable field)
    utc.disarmable = bool(root.acquire("Disarmable", 0))
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:115 (IgnoreCrePath field, KotOR 2 only)
    utc.ignore_cre_path = bool(root.acquire("IgnoreCrePath", 0))
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:114 (Hologram field, KotOR 2 only)
    utc.hologram = bool(root.acquire("Hologram", 0))
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:137 (WillNotRender field, KotOR 2 only)
    utc.will_not_render = bool(root.acquire("WillNotRender", 0))

    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:112 (GoodEvil field, alignment)
    utc.alignment = root.acquire("GoodEvil", 0)
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:89 (ChallengeRating field as float)
    utc.challenge_rating = root.acquire("ChallengeRating", 0.0)
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:85 (BlindSpot field as float, KotOR 2 only)
    utc.blindspot = root.acquire("BlindSpot", 0.0)
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:126 (MultiplierSet field, KotOR 2 only)
    utc.multiplier_set = root.acquire("MultiplierSet", 0)

    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:127 (NaturalAC field)
    utc.natural_ac = root.acquire("NaturalAC", 0)
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:140 (refbonus field as int16)
    utc.reflex_bonus = root.acquire("refbonus", 0)
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:141 (willbonus field as int16)
    utc.willpower_bonus = root.acquire("willbonus", 0)
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:139 (fortbonus field as int16)
    utc.fortitude_bonus = root.acquire("fortbonus", 0)

    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:129 (Str field)
    utc.strength = root.acquire("Str", 0)
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:100 (Dex field)
    utc.dexterity = root.acquire("Dex", 0)
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:94 (Con field)
    utc.constitution = root.acquire("Con", 0)
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:116 (Int field)
    utc.intelligence = root.acquire("Int", 0)
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:138 (Wis field)
    utc.wisdom = root.acquire("Wis", 0)
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:88 (Cha field)
    utc.charisma = root.acquire("Cha", 0)

    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:97 (CurrentHitPoints field as int16)
    utc.current_hp = root.acquire("CurrentHitPoints", 0)
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:124 (MaxHitPoints field as int16)
    utc.max_hp = root.acquire("MaxHitPoints", 0)
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:113 (HitPoints field as int16, base HP)
    utc.hp = root.acquire("HitPoints", 0)
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:110 (ForcePoints field as int16, max FP)
    utc.max_fp = root.acquire("ForcePoints", 0)
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:96 (CurrentForce field as int16)
    utc.fp = root.acquire("CurrentForce", 0)

    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:142 (ScriptEndDialogu field)
    # Script hooks: ResRefs to NCS scripts executed on specific events
    utc.on_end_dialog = root.acquire("ScriptEndDialogu", ResRef.from_blank())
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:145 (ScriptOnBlocked field)
    utc.on_blocked = root.acquire("ScriptOnBlocked", ResRef.from_blank())
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:144 (ScriptHeartbeat field)
    utc.on_heartbeat = root.acquire("ScriptHeartbeat", ResRef.from_blank())
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:146 (ScriptOnNotice field)
    utc.on_notice = root.acquire("ScriptOnNotice", ResRef.from_blank())
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:149 (ScriptSpellAt field)
    utc.on_spell = root.acquire("ScriptSpellAt", ResRef.from_blank())
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:137 (ScriptAttacked field)
    utc.on_attacked = root.acquire("ScriptAttacked", ResRef.from_blank())
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:138 (ScriptDamaged field)
    utc.on_damaged = root.acquire("ScriptDamaged", ResRef.from_blank())
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:141 (ScriptDisturbed field)
    utc.on_disturbed = root.acquire("ScriptDisturbed", ResRef.from_blank())
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:143 (ScriptEndRound field)
    utc.on_end_round = root.acquire("ScriptEndRound", ResRef.from_blank())
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:140 (ScriptDialogue field)
    utc.on_dialog = root.acquire("ScriptDialogue", ResRef.from_blank())
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:148 (ScriptSpawn field)
    utc.on_spawn = root.acquire("ScriptSpawn", ResRef.from_blank())
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:147 (ScriptRested field, not used by engine)
    utc.on_rested = root.acquire("ScriptRested", ResRef.from_blank())
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:139 (ScriptDeath field)
    utc.on_death = root.acquire("ScriptDeath", ResRef.from_blank())
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:150 (ScriptUserDefine field)
    utc.on_user_defined = root.acquire("ScriptUserDefine", ResRef.from_blank())

    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:151-153 (SkillList parsing)
    # vendor/reone/include/reone/resource/parser/gff/utc.h:40-42 (UTC_SkillList struct with Rank field)
    # vendor/Kotor.NET/Kotor.NET/Resources/KotorUTC/UTCCompiler.cs:95-103 (SkillList parsing with index-based access)
    # SkillList is a GFF List containing 8 structs, each with a "Rank" uint8 field
    # Skill order: [0] Computer Use, [1] Demolitions, [2] Stealth, [3] Awareness,
    #              [4] Persuade, [5] Repair, [6] Security, [7] Treat Injury
    if not root.exists("SkillList") or root.what_type("SkillList") is not GFFFieldType.List:
        if root.exists("SkillList"):
            RobustLogger().error("SkillList in UTC's must be a GFFList, recreating now...")
            del root._fields["SkillList"]
        else:
            RobustLogger().error("SkillList must exist in UTC's, creating now...")
        # vendor/reone/include/reone/resource/parser/gff/utc.h:40-42 (UTC_SkillList struct definition)
        # Create default SkillList with 8 empty skill entries (Rank = 0)
        skill_list = root.set_list("SkillList", GFFList())
        skill_list.add(0).set_uint8("Rank", 0)  # Computer Use
        skill_list.add(1).set_uint8("Rank", 0)  # Demolitions
        skill_list.add(2).set_uint8("Rank", 0)  # Stealth
        skill_list.add(3).set_uint8("Rank", 0)  # Awareness
        skill_list.add(4).set_uint8("Rank", 0)  # Persuade
        skill_list.add(5).set_uint8("Rank", 0)  # Repair
        skill_list.add(6).set_uint8("Rank", 0)  # Security
        skill_list.add(7).set_uint8("Rank", 0)  # Treat Injury
    skill_list_acquired: GFFList = root.acquire("SkillList", GFFList())
    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:151-153 (iterates SkillList)
    # vendor/Kotor.NET/Kotor.NET/Resources/KotorUTC/UTCCompiler.cs:96 (skillList.Get(0).Get("Rank"))
    # Parse each skill from SkillList array by index
    if skill_list_acquired.at(0) is not None:
        skill_struct = skill_list_acquired.at(0)
        assert skill_struct is not None, "SkillList[0] struct is None"
        # vendor/reone/src/libs/resource/parser/gff/utc.cpp:44-46 (parseUTC_SkillList reads Rank field)
        utc.computer_use = skill_struct.acquire("Rank", 0)  # Skill index 0: Computer Use
    if skill_list_acquired.at(1) is not None:
        skill_struct = skill_list_acquired.at(1)
        assert skill_struct is not None, "SkillList[1] struct is None"
        utc.demolitions = skill_struct.acquire("Rank", 0)  # Skill index 1: Demolitions
    if skill_list_acquired.at(2) is not None:
        skill_struct = skill_list_acquired.at(2)
        assert skill_struct is not None, "SkillList[2] struct is None"
        utc.stealth = skill_struct.acquire("Rank", 0)  # Skill index 2: Stealth
    if skill_list_acquired.at(3) is not None:
        skill_struct = skill_list_acquired.at(3)
        assert skill_struct is not None, "SkillList[3] struct is None"
        utc.awareness = skill_struct.acquire("Rank", 0)  # Skill index 3: Awareness
    if skill_list_acquired.at(4) is not None:
        skill_struct = skill_list_acquired.at(4)
        assert skill_struct is not None, "SkillList[4] struct is None"
        utc.persuade = skill_struct.acquire("Rank", 0)  # Skill index 4: Persuade
    if skill_list_acquired.at(5) is not None:
        skill_struct = skill_list_acquired.at(5)
        assert skill_struct is not None, "SkillList[5] struct is None"
        utc.repair = skill_struct.acquire("Rank", 0)  # Skill index 5: Repair
    if skill_list_acquired.at(6) is not None:
        skill_struct = skill_list_acquired.at(6)
        assert skill_struct is not None, "SkillList[6] struct is None"
        utc.security = skill_struct.acquire("Rank", 0)  # Skill index 6: Security
    if skill_list_acquired.at(7) is not None:
        skill_struct = skill_list_acquired.at(7)
        assert skill_struct is not None, "SkillList[7] struct is None"
        utc.treat_injury = skill_struct.acquire("Rank", 0)  # Skill index 7: Treat Injury

    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:151-153 (only parses SkillList items, doesn't limit count)
    # Discrepancy: Some KotOR 1 UTC files contain more than 8 skill entries (up to 20)
    # PyKotor preserves extra skills in _extra_unimplemented_skills for round-trip compatibility
    # Note: reone and Kotor.NET only parse the first 8 skills, ignoring extras
    if len(skill_list_acquired._structs) > 8:
        utc._extra_unimplemented_skills = [skill_struct.acquire("Rank", 0) for skill_struct in skill_list_acquired._structs[8:]]

    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:90-92 (ClassList parsing)
    # vendor/reone/include/reone/resource/parser/gff/utc.h:60-64 (UTC_ClassList struct)
    # vendor/Kotor.NET/Kotor.NET/Resources/KotorUTC/UTCCompiler.cs:105-120 (ClassList parsing)
    # ClassList contains creature classes (e.g., Soldier, Scout, Scoundrel, Jedi Consular, etc.)
    class_list: GFFList = root.acquire("ClassList", GFFList())
    for class_struct in class_list:
        # vendor/reone/src/libs/resource/parser/gff/utc.cpp:90-92 (parseUTC_ClassList reads Class and ClassLevel)
        class_id = class_struct.acquire("Class", 0)  # Class type identifier (e.g., 0=Soldier, 1=Scout)
        class_level = class_struct.acquire("ClassLevel", 0)  # Level in this class
        utc_class = UTCClass(class_id, class_level)

        # vendor/reone/include/reone/resource/parser/gff/utc.h:28-32 (UTC_ClassList_KnownList0 struct)
        # vendor/reone/src/libs/resource/parser/gff/utc.cpp:90-92 (KnownList0 parsing)
        # KnownList0 contains spells/powers known by this class level
        power_list: GFFList = class_struct.acquire("KnownList0", GFFList())
        for index, power_struct in enumerate(power_list):
            # vendor/reone/include/reone/resource/parser/gff/utc.h:29 (Spell field in KnownList0)
            spell_thing = power_struct.acquire("Spell", 0)  # Spell/power ID
            utc_class.powers.append(spell_thing)
            # PyKotor-specific: Preserve original order for round-trip compatibility
            utc_class._original_powers_mapping[spell_thing] = index

        utc.classes.append(utc_class)

    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:106-108 (FeatList parsing)
    # vendor/reone/include/reone/resource/parser/gff/utc.h:51-53 (UTC_FeatList struct)
    # vendor/Kotor.NET/Kotor.NET/Resources/KotorUTC/UTCCompiler.cs:122-125 (FeatList parsing)
    # FeatList contains feat identifiers that the creature has
    feat_list: GFFList = root.acquire("FeatList", GFFList())
    for index, feat_struct in enumerate(feat_list):
        # vendor/reone/include/reone/resource/parser/gff/utc.h:52 (Feat field)
        feat_id_thing: int = feat_struct.acquire("Feat", 0)  # Feat identifier
        utc.feats.append(feat_id_thing)
        # PyKotor-specific: Preserve original order for round-trip compatibility
        utc._original_feat_mapping[feat_id_thing] = index

    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:102-104 (Equip_ItemList parsing)
    # vendor/reone/include/reone/resource/parser/gff/utc.h:55-58 (UTC_Equip_ItemList struct)
    # vendor/Kotor.NET/Kotor.NET/Resources/KotorUTC/UTCCompiler.cs:127-140 (Equip_ItemList parsing)
    # Equip_ItemList contains equipped items, struct_id indicates equipment slot
    equipment_list: GFFList = root.acquire("Equip_ItemList", GFFList())
    for equipment_struct in equipment_list:
        # vendor/reone/include/reone/resource/parser/gff/utc.h:57 (EquippedRes field)
        # struct_id maps to EquipmentSlot enum (e.g., 0=Right Hand, 1=Left Hand, 2=Armor)
        slot = EquipmentSlot(equipment_struct.struct_id)  # Equipment slot from struct_id
        resref = equipment_struct.acquire("EquippedRes", ResRef.from_blank())  # Item ResRef
        droppable = bool(equipment_struct.acquire("Dropable", 0))  # Whether item can be dropped
        utc.equipment[slot] = InventoryItem(resref, droppable)

    # vendor/reone/src/libs/resource/parser/gff/utc.cpp:119-121 (ItemList parsing)
    # vendor/reone/include/reone/resource/parser/gff/utc.h:44-49 (UTC_ItemList struct)
    # vendor/Kotor.NET/Kotor.NET/Resources/KotorUTC/UTCCompiler.cs:142-150 (ItemList parsing)
    # ItemList contains items in creature's inventory (not equipped)
    item_list: GFFList = root.acquire("ItemList", GFFList())
    for item_struct in item_list:
        # vendor/reone/include/reone/resource/parser/gff/utc.h:46 (InventoryRes field)
        resref = item_struct.acquire("InventoryRes", ResRef.from_blank())  # Item ResRef
        droppable = bool(item_struct.acquire("Dropable", 0))  # Whether item can be dropped
        utc.inventory.append(InventoryItem(resref, droppable))

    return utc


def dismantle_utc(
    utc: UTC,
    game: Game = Game.K2,
    *,
    use_deprecated: bool = True,
) -> GFF:
    gff = GFF(GFFContent.UTC)

    root = gff.root
    root.set_resref("TemplateResRef", utc.resref)
    root.set_string("Tag", utc.tag)
    root.set_string("Comment", utc.comment)
    root.set_resref("Conversation", utc.conversation)

    root.set_locstring("FirstName", utc.first_name)
    root.set_locstring("LastName", utc.last_name)

    root.set_uint8("SubraceIndex", utc.subrace_id)
    root.set_uint8("PerceptionRange", utc.perception_id)
    root.set_uint8("Race", utc.race_id)
    root.set_uint16("Appearance_Type", utc.appearance_id)
    root.set_uint8("Gender", utc.gender_id)
    root.set_uint16("FactionID", utc.faction_id)
    root.set_int32("WalkRate", utc.walkrate_id)
    root.set_uint16("SoundSetFile", utc.soundset_id)
    root.set_uint16("PortraitId", utc.portrait_id)

    # TODO(th3w1zard1): Add these seemingly missing fields into UTCEditor?
    root.set_resref("Portrait", utc.portrait_resref)
    root.set_uint8("SaveWill", utc.save_will)
    root.set_uint8("SaveFortitude", utc.save_fortitude)
    root.set_uint8("Morale", utc.morale)
    root.set_uint8("MoraleRecovery", utc.morale_recovery)
    root.set_uint8("MoraleBreakpoint", utc.morale_breakpoint)

    root.set_uint8("BodyVariation", utc.body_variation)
    root.set_uint8("TextureVar", utc.texture_variation)

    root.set_uint8("NotReorienting", utc.not_reorienting)
    root.set_uint8("PartyInteract", utc.party_interact)
    root.set_uint8("NoPermDeath", utc.no_perm_death)
    root.set_uint8("Min1HP", utc.min1_hp)
    root.set_uint8("Plot", utc.plot)
    root.set_uint8("Interruptable", utc.interruptable)
    root.set_uint8("IsPC", utc.is_pc)
    root.set_uint8("Disarmable", utc.disarmable)

    root.set_uint8("GoodEvil", utc.alignment)
    root.set_single("ChallengeRating", utc.challenge_rating)

    root.set_uint8("NaturalAC", utc.natural_ac)
    root.set_int16("refbonus", utc.reflex_bonus)
    root.set_int16("willbonus", utc.willpower_bonus)
    root.set_int16("fortbonus", utc.fortitude_bonus)

    root.set_uint8("Str", utc.strength)
    root.set_uint8("Dex", utc.dexterity)
    root.set_uint8("Con", utc.constitution)
    root.set_uint8("Int", utc.intelligence)
    root.set_uint8("Wis", utc.wisdom)
    root.set_uint8("Cha", utc.charisma)

    root.set_int16("CurrentHitPoints", utc.current_hp)
    root.set_int16("MaxHitPoints", utc.max_hp)
    root.set_int16("HitPoints", utc.hp)
    root.set_int16("CurrentForce", utc.fp)
    root.set_int16("ForcePoints", utc.max_fp)

    root.set_resref("ScriptEndDialogu", utc.on_end_dialog)
    root.set_resref("ScriptOnBlocked", utc.on_blocked)
    root.set_resref("ScriptHeartbeat", utc.on_heartbeat)
    root.set_resref("ScriptOnNotice", utc.on_notice)
    root.set_resref("ScriptSpellAt", utc.on_spell)
    root.set_resref("ScriptAttacked", utc.on_attacked)
    root.set_resref("ScriptDamaged", utc.on_damaged)
    root.set_resref("ScriptDisturbed", utc.on_disturbed)
    root.set_resref("ScriptEndRound", utc.on_end_round)
    root.set_resref("ScriptDialogue", utc.on_dialog)
    root.set_resref("ScriptSpawn", utc.on_spawn)
    root.set_resref("ScriptRested", utc.on_rested)
    root.set_resref("ScriptDeath", utc.on_death)
    root.set_resref("ScriptUserDefine", utc.on_user_defined)

    root.set_uint8("PaletteID", utc.palette_id)

    skill_list: GFFList = root.set_list("SkillList", GFFList())
    skill_list.add(0).set_uint8("Rank", utc.computer_use)
    skill_list.add(0).set_uint8("Rank", utc.demolitions)
    skill_list.add(0).set_uint8("Rank", utc.stealth)
    skill_list.add(0).set_uint8("Rank", utc.awareness)
    skill_list.add(0).set_uint8("Rank", utc.persuade)
    skill_list.add(0).set_uint8("Rank", utc.repair)
    skill_list.add(0).set_uint8("Rank", utc.security)
    skill_list.add(0).set_uint8("Rank", utc.treat_injury)

    class_list: GFFList = root.set_list("ClassList", GFFList())
    for utc_class in utc.classes:
        class_struct = class_list.add(2)
        class_struct.set_int32("Class", utc_class.class_id)
        class_struct.set_int16("ClassLevel", utc_class.class_level)
        power_list: GFFList = class_struct.set_list("KnownList0", GFFList())
        for power in utc_class.powers:
            power_struct = power_list.add(3)
            power_struct.set_uint16("Spell", power)
            power_struct.set_uint8("SpellFlags", 1)
            power_struct.set_uint8("SpellMetaMagic", 0)
        power_list._structs = sorted(
            power_list._structs, key=lambda power_struct_local: utc_class._original_powers_mapping.get(power_struct_local.get_uint16("Spell"), float("inf"))
        )

    feat_list: GFFList = root.set_list("FeatList", GFFList())
    for feat in utc.feats:
        feat_list.add(1).set_uint16("Feat", feat)

    # Sort utc.feats according to their original index, stored in utc._original_feat_mapping
    # Might be better to use GFFStructInterface from that PR.
    feat_list._structs = sorted(feat_list._structs, key=lambda feat: utc._original_feat_mapping.get(feat.get_uint16("Feat"), float("inf")))

    # Not sure what these are for, verified they exist in K1's 'c_drdg.utc' in data\templates.bif. Might be unused in which case this can be deleted.
    if utc._extra_unimplemented_skills:
        for val in utc._extra_unimplemented_skills:
            skill_list.add(0).set_uint8("Rank", val)

    equipment_list: GFFList = root.set_list("Equip_ItemList", GFFList())
    for slot, item in utc.equipment.items():
        equipment_struct = equipment_list.add(slot.value)
        equipment_struct.set_resref("EquippedRes", item.resref)
        if item.droppable:
            equipment_struct.set_uint8("Dropable", value=True)

    item_list: GFFList = root.set_list("ItemList", GFFList())
    for i, item in enumerate(utc.inventory):
        item_struct = item_list.add(i)
        item_struct.set_resref("InventoryRes", item.resref)
        item_struct.set_uint16("Repos_PosX", i)
        item_struct.set_uint16("Repos_Posy", 0)
        if item.droppable:
            item_struct.set_uint8("Dropable", value=True)

    if game.is_k2():
        root.set_single("BlindSpot", utc.blindspot)
        root.set_uint8("MultiplierSet", utc.multiplier_set)
        root.set_uint8("IgnoreCrePath", utc.ignore_cre_path)
        root.set_uint8("Hologram", utc.hologram)
        root.set_uint8("WillNotRender", utc.will_not_render)

    if use_deprecated:
        root.set_uint8("BodyBag", utc.bodybag_id)
        root.set_string("Deity", utc.deity)
        root.set_locstring("Description", utc.description)
        root.set_uint8("LawfulChaotic", utc.lawfulness)
        root.set_int32("Phenotype", utc.phenotype_id)
        root.set_resref("ScriptRested", utc.on_rested)
        root.set_string("Subrace", utc.subrace_name)
        root.set_list("SpecAbilityList", GFFList())
        root.set_list("TemplateList", GFFList())

    return gff


def read_utc(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
) -> UTC:
    gff: GFF = read_gff(source, offset, size)
    return construct_utc(gff)


def write_utc(
    utc: UTC,
    target: TARGET_TYPES,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
):
    gff: GFF = dismantle_utc(utc, game, use_deprecated=use_deprecated)
    write_gff(gff, target, file_format)


def bytes_utc(
    utc: UTC,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
) -> bytes:
    gff: GFF = dismantle_utc(utc, game, use_deprecated=use_deprecated)
    return bytes_gff(gff, file_format)
