from __future__ import annotations

from copy import deepcopy
from enum import IntEnum
from typing import TYPE_CHECKING, Literal, TypedDict

from pykotor.common.misc import EquipmentSlot, Game, InventoryItem
from pykotor.resource.formats.gff import GFF, FieldProperty, GFFContent, GFFFieldType, GFFList, GFFStruct, GFFStructInterface, bytes_gff, read_gff, write_gff
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.common.language import LocalizedString
    from pykotor.common.misc import ResRef
    from pykotor.extract.installation import Installation
    from pykotor.resource.formats.gff.gff_data import FieldGFF
    from pykotor.resource.formats.twoda import TwoDA
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class UTCSkillIndex(IntEnum):
    """Represents the list indices of a UTC's 'SkillList' Field."""
    COMPUTER_USE = 0
    DEMOLITIONS = 1
    STEALTH = 2
    AWARENESS = 3
    PERSUADE = 4
    REPAIR = 5
    SECURITY = 6
    TREAT_INJURY = 7


class UTCStructID(IntEnum):
    SKILL = 0
    FEAT = 1
    CLASS = 2
    POWER = 3


class UTCEquipmentFields(TypedDict):
    EquippedRes: FieldGFF[ResRef]
    Dropable: FieldGFF[int]
class UTCEquipment(GFFStructInterface, InventoryItem):
    resref: FieldProperty[ResRef, ResRef] = FieldProperty("EquippedRes", GFFFieldType.ResRef)
    droppable: FieldProperty[int, bool] = FieldProperty("Dropable", GFFFieldType.UInt8)
    def __init__(self, slot: EquipmentSlot):
        super().__init__(struct_id=slot.value)
        self._fields: UTCEquipmentFields

    @property
    def slot(self) -> int:
        return self.struct_id
    @slot.setter
    def slot(self, value: int):
        self.struct_id = value


class UTCSkillFields(TypedDict):
    Rank: int
class UTCSkill(GFFStructInterface):
    """A skill in the 'SkillList' UTC list.

    Struct ID must be zero for this GFFStruct.
    """
    rank = FieldProperty("Rank", GFFFieldType.UInt8)
    def __init__(self, skill_type: UTCSkillIndex):
        super().__init__(struct_id=UTCStructID.SKILL.value)
        self._fields: UTCSkillFields
        self.skill_type: UTCSkillIndex = skill_type


class UTCPowerFields(TypedDict):
    Spell: FieldGFF[int]
    SpellFlags: FieldGFF[Literal[1]]
    SpellMetaMagic: FieldGFF[Literal[0]]
class UTCPower(GFFStructInterface):
    spell = FieldProperty("Spell", GFFFieldType.UInt16)
    spell_flags: FieldProperty[Literal[1], Literal[1]] = FieldProperty("SpellFlags", GFFFieldType.UInt8, 1)
    spell_meta_magic: FieldProperty[Literal[0], Literal[0]] = FieldProperty("SpellMetaMagic", GFFFieldType.UInt8, 0)

    def __init__(
        self,
    ):
        super().__init__(struct_id=UTCStructID.POWER.value)
        self._fields: UTCPowerFields


class UTCFeatFields(TypedDict):
    Feat: FieldGFF[int]
class UTCFeat(GFFStructInterface):
    feat: FieldProperty[int, int] = FieldProperty("Feat", GFFFieldType.UInt16)

    def __init__(
        self,
    ):
        super().__init__(struct_id=UTCStructID.FEAT.value)
        self._fields: UTCPowerFields


class UTCItemField(TypedDict):
    Repos_PosX: FieldGFF[int]
    Repos_Posy: FieldGFF[int]
    InventoryRes: FieldGFF[ResRef]
    Dropable: FieldGFF[int]
class UTCItem(GFFStructInterface, InventoryItem):
    repos_x: FieldProperty[int, int] = FieldProperty("Repos_PosX", GFFFieldType.UInt16)
    repos_y: FieldProperty[int, int] = FieldProperty("Repos_Posy", GFFFieldType.UInt16)
    resref: FieldProperty[ResRef, ResRef] = FieldProperty("InventoryRes", GFFFieldType.ResRef)
    droppable: FieldProperty[int, bool] = FieldProperty("Dropable", GFFFieldType.UInt8, return_type=bool)

    def __init__(
        self,
        struct_id: int = -1
    ):
        super().__init__(struct_id)
        self._fields: UTCItemField


class UTCClassFields(TypedDict):
    Class: FieldGFF[int]
    ClassLevel: FieldGFF[int]
    KnownList0: FieldGFF[GFFList[UTCPower]]
class UTCClass(GFFStructInterface):
    class_id: FieldProperty[int, int] = FieldProperty("Class", GFFFieldType.Int32)
    class_level: FieldProperty[int, int] = FieldProperty("ClassLevel", GFFFieldType.Int16)
    powers: FieldProperty[GFFList[GFFStruct], GFFList[UTCPower]] = FieldProperty("KnownList0", GFFFieldType.List)
    def __init__(
        self,
        class_id: int,
        class_level: int
    ):
        super().__init__(struct_id=UTCStructID.CLASS.value)
        self.class_id = class_id
        self.class_level = class_level
        self._fields: UTCClassFields

    def __repr__(
        self,
    ):
        return f"{self.__class__.__name__}(class_id={self.class_id}, class_level={self.class_level})"

    def __eq__(
        self,
        other: UTCClass,
    ):
        if isinstance(other, UTCClass):
            return (
                self.class_id == other.class_id
                and self.class_level == other.class_level
                and self.powers == other.powers
            )

        msg = f"Cannot compare {self!r} with {other!r}"
        print(msg)
        return NotImplemented

    def get_known_powers(self, spell_2da: TwoDA, installation: Installation):
        # TODO(th3w1zard1): not sure how the indexing works
        known_list: list[str] = []
        for power_row in spell_2da:
            stringref = power_row.get_integer("name", 0)
            text = installation.talktable().string(stringref) if stringref else power_row.get_string("label")
            for known_power in self.powers:
                text = text.replace("_", " ").replace("XXX", "").replace("\n", "").title()
                text = text and text.strip() or f"[Unused Power ID: {power_row.label()}]"

    def add_power(self): ...
        # TODO(th3w1zard1): ??? how does it index.


class UTCFields(TypedDict):
    ClassList: FieldGFF[GFFList[UTCClass]]
    SkillList: FieldGFF[GFFList[UTCSkill]]
    FeatList: FieldGFF[GFFList[UTCFeat]]
    Equip_ItemList: FieldGFF[GFFList[GFFStruct]]  # TODO(th3w1zard1): type as the interface struct.
    ItemList: FieldGFF[GFFList[GFFStruct]]  # TODO(th3w1zard1): type as the interface struct.
    TemplateResRef: FieldGFF[str]
    Tag: FieldGFF[str]
    Comment: FieldGFF[str]
    Conversation: FieldGFF[str]
    FirstName: FieldGFF[str]
    LastName: FieldGFF[str]
    SubraceIndex: FieldGFF[int]
    PerceptionRange: FieldGFF[int]
    Race: FieldGFF[int]
    Appearance_Type: FieldGFF[int]
    Gender: FieldGFF[int]
    FactionID: FieldGFF[int]
    WalkRate: FieldGFF[int]
    SoundSetFile: FieldGFF[str]
    PortraitId: FieldGFF[int]
    BodyVariation: FieldGFF[int]
    TextureVar: FieldGFF[int]
    NotReorienting: FieldGFF[bool]
    PartyInteract: FieldGFF[bool]
    NoPermDeath: FieldGFF[bool]
    Min1HP: FieldGFF[bool]
    Plot: FieldGFF[bool]
    Interruptable: FieldGFF[bool]
    IsPC: FieldGFF[bool]
    Disarmable: FieldGFF[bool]
    GoodEvil: FieldGFF[int]
    ChallengeRating: FieldGFF[float]
    NaturalAC: FieldGFF[int]
    refbonus: FieldGFF[int]
    willbonus: FieldGFF[int]
    fortbonus: FieldGFF[int]
    Str: FieldGFF[int]
    Dex: FieldGFF[int]
    Con: FieldGFF[int]
    Int: FieldGFF[int]
    Wis: FieldGFF[int]
    Cha: FieldGFF[int]
    CurrentHitPoints: FieldGFF[int]
    MaxHitPoints: FieldGFF[int]
    HitPoints: FieldGFF[int]
    CurrentForce: FieldGFF[int]
    ForcePoints: FieldGFF[int]
    ScriptEndDialogu: FieldGFF[str]
    ScriptOnBlocked: FieldGFF[str]
    ScriptHeartbeat: FieldGFF[str]
    ScriptOnNotice: FieldGFF[str]
    ScriptSpellAt: FieldGFF[str]
    ScriptAttacked: FieldGFF[str]
    ScriptDamaged: FieldGFF[str]
    ScriptDisturbed: FieldGFF[str]
    ScriptEndRound: FieldGFF[str]
    ScriptDialogue: FieldGFF[str]
    ScriptSpawn: FieldGFF[str]
    ScriptRested: FieldGFF[str]
    ScriptDeath: FieldGFF[str]
    ScriptUserDefine: FieldGFF[str]

    # KOTOR 2 TSL Fields Only.
    BlindSpot: FieldGFF[float]
    MultiplierSet: FieldGFF[int]
    IgnoreCrePath: FieldGFF[bool]
    Hologram: FieldGFF[bool]
    WillNotRender: FieldGFF[bool]

    # For toolset use.
    PaletteID: FieldGFF[int]

    # Deprecated/unused by game engine.
    BodyBag: FieldGFF[int]
    Deity: FieldGFF[str]
    Description: FieldGFF[str]
    LawfulChaotic: FieldGFF[int]
    Phenotype: FieldGFF[int]
    Subrace: FieldGFF[str]

    # TODO(th3w1zard1): Find out if these are deprecated
    Portrait: FieldGFF[ResRef]
    SaveWill: FieldGFF[int]
    SaveFortitude: FieldGFF[int]
    Morale: FieldGFF[int]
    MoraleRecovery: FieldGFF[int]
    MoraleBreakpoint: FieldGFF[int]
class UTC(GFFStructInterface):
    """Stores creature data."""

    BINARY_TYPE = ResourceType.UTC
    CONTENT_TYPE = GFFContent.UTC

    equiplist: FieldProperty[GFFList[GFFStruct], GFFList[UTCEquipment]] = FieldProperty("Equip_ItemList", GFFFieldType.List)

    def __init__(
        self,
    ):
        super().__init__()
        self._fields: UTCFields

    @property
    def equipment(self) -> dict[EquipmentSlot, UTCEquipment]:
        return {  # Shallow copy!
            EquipmentSlot(e.struct_id): e
            for e in self.equiplist
        }

    @staticmethod
    def default_skill_list() -> GFFList[UTCSkill]:
        skill_list: GFFList[UTCSkill] = GFFList()
        skill_list.extend(
            UTCSkill(UTCSkillIndex(i))
            for i in range(8)
        )
        return skill_list

    def get_skill(self, skill_index: UTCSkillIndex) -> UTCSkill:
        return self.skill_list.at(skill_index.value, default=UTCSkill(skill_index))
    def set_skill(self, skill_index: UTCSkillIndex, value: int):
        skill_list: GFFList[UTCSkill] = self.skill_list
        skill_struct: UTCSkill = skill_list.at(skill_index.value)
        if skill_struct is None:
            skill_struct = UTCSkill(skill_index)
            skill_list.append(skill_struct)
        skill_struct.set_uint8("Rank", value)

    @property
    def computer_use(self) -> int: return self.get_skill(UTCSkillIndex.COMPUTER_USE).rank
    @computer_use.setter
    def computer_use(self, value: int):
        self.set_skill(UTCSkillIndex.COMPUTER_USE, value)

    @property
    def demolitions(self) -> int: return self.get_skill(UTCSkillIndex.DEMOLITIONS).rank
    @demolitions.setter
    def demolitions(self, value: int):
        self.set_skill(UTCSkillIndex.DEMOLITIONS, value)

    @property
    def stealth(self) -> int: return self.get_skill(UTCSkillIndex.STEALTH).rank
    @stealth.setter
    def stealth(self, value: int):
        self.set_skill(UTCSkillIndex.STEALTH, value)

    @property
    def awareness(self) -> int: return self.get_skill(UTCSkillIndex.AWARENESS).rank
    @awareness.setter
    def awareness(self, value: int):
        self.set_skill(UTCSkillIndex.AWARENESS, value)

    @property
    def persuade(self) -> int: return self.get_skill(UTCSkillIndex.PERSUADE).rank
    @persuade.setter
    def persuade(self, value: int):
        self.set_skill(UTCSkillIndex.PERSUADE, value)

    @property
    def repair(self) -> int: return self.get_skill(UTCSkillIndex.REPAIR).rank
    @repair.setter
    def repair(self, value: int):
        self.set_skill(UTCSkillIndex.REPAIR, value)

    @property
    def security(self) -> int: return self.get_skill(UTCSkillIndex.SECURITY).rank
    @security.setter
    def security(self, value: int):
        self.set_skill(UTCSkillIndex.SECURITY, value)

    @property
    def treat_injury(self) -> int: return self.get_skill(UTCSkillIndex.TREAT_INJURY).rank
    @treat_injury.setter
    def treat_injury(self, value: int):
        self.set_skill(UTCSkillIndex.TREAT_INJURY, value)

    inventory: FieldProperty[GFFList[GFFStruct], GFFList[UTCItem]] = FieldProperty("ItemList", GFFFieldType.List)
    classes: FieldProperty[GFFList[GFFStruct], GFFList[UTCClass]] = FieldProperty("ClassList", GFFFieldType.List)
    resref: FieldProperty[ResRef, ResRef] = FieldProperty("TemplateResRef", GFFFieldType.ResRef)
    tag: FieldProperty[str, str] = FieldProperty("Tag", GFFFieldType.String)
    comment: FieldProperty[str, str] = FieldProperty("Comment", GFFFieldType.String)
    conversation: FieldProperty[ResRef, ResRef] = FieldProperty("Conversation", GFFFieldType.ResRef)
    first_name: FieldProperty[LocalizedString, LocalizedString] = FieldProperty("FirstName", GFFFieldType.LocalizedString)
    last_name: FieldProperty[LocalizedString, LocalizedString] = FieldProperty("LastName", GFFFieldType.LocalizedString)
    subrace_id: FieldProperty[int, int] = FieldProperty("SubraceIndex", GFFFieldType.Int32)
    perception_id: FieldProperty[int, int] = FieldProperty("PerceptionRange", GFFFieldType.UInt8)
    race_id: FieldProperty[int, int] = FieldProperty("Race", GFFFieldType.UInt8)
    appearance_id: FieldProperty[int, int] = FieldProperty("Appearance_Type", GFFFieldType.UInt16)
    gender_id: FieldProperty[int, int] = FieldProperty("Gender", GFFFieldType.Int32)
    faction_id: FieldProperty[int, int] = FieldProperty("FactionID", GFFFieldType.UInt16)
    walkrate_id: FieldProperty[int, int] = FieldProperty("WalkRate", GFFFieldType.Int32)
    soundset_id: FieldProperty[int, int] = FieldProperty("SoundSetFile", GFFFieldType.UInt16)
    portrait_id: FieldProperty[int, int] = FieldProperty("PortraitId", GFFFieldType.UInt16)
    body_variation: FieldProperty[int, int] = FieldProperty("BodyVariation", GFFFieldType.Int32)
    texture_variation: FieldProperty[int, int] = FieldProperty("TextureVar", GFFFieldType.Int32)
    not_reorienting: FieldProperty[int, bool] = FieldProperty("NotReorienting", GFFFieldType.UInt8, return_type=bool)
    party_interact: FieldProperty[int, int] = FieldProperty("PartyInteract", GFFFieldType.UInt8)
    no_perm_death: FieldProperty[int, bool] = FieldProperty("NoPermDeath", GFFFieldType.UInt8, return_type=bool)
    min1_hp: FieldProperty[int, bool] = FieldProperty("Min1HP", GFFFieldType.UInt8, return_type=bool)
    plot: FieldProperty[int, bool] = FieldProperty("Plot", GFFFieldType.UInt8, return_type=bool)
    interruptable: FieldProperty[int, bool] = FieldProperty("Interruptable", GFFFieldType.UInt8, return_type=bool)
    is_pc: FieldProperty[int, bool] = FieldProperty("IsPC", GFFFieldType.UInt8, return_type=bool)
    disarmable: FieldProperty[int, bool] = FieldProperty("Disarmable", GFFFieldType.UInt8, return_type=bool)
    alignment = FieldProperty("GoodEvil", GFFFieldType.UInt8)
    challenge_rating = FieldProperty("ChallengeRating", GFFFieldType.Single)
    natural_ac = FieldProperty("NaturalAC", GFFFieldType.UInt8)
    reflex_bonus = FieldProperty("refbonus", GFFFieldType.Int32)
    willpower_bonus = FieldProperty("willbonus", GFFFieldType.Int32)
    fortitude_bonus = FieldProperty("fortbonus", GFFFieldType.Int16)
    strength = FieldProperty("Str", GFFFieldType.UInt8)
    dexterity = FieldProperty("Dex", GFFFieldType.UInt8)
    constitution = FieldProperty("Con", GFFFieldType.UInt8)
    intelligence = FieldProperty("Int", GFFFieldType.UInt8)
    wisdom = FieldProperty("Wis", GFFFieldType.UInt8)
    charisma = FieldProperty("Cha", GFFFieldType.UInt8)
    current_hp = FieldProperty("CurrentHitPoints", GFFFieldType.Int16)
    max_hp = FieldProperty("MaxHitPoints", GFFFieldType.Int16)
    hp = FieldProperty("HitPoints", GFFFieldType.Int16)
    fp = FieldProperty("CurrentForce", GFFFieldType.Int16)
    max_fp = FieldProperty("ForcePoints", GFFFieldType.Int16)
    on_end_dialog: FieldProperty[ResRef, ResRef] = FieldProperty("ScriptEndDialogu", GFFFieldType.ResRef)
    on_blocked: FieldProperty[ResRef, ResRef] = FieldProperty("ScriptOnBlocked", GFFFieldType.ResRef)
    on_heartbeat: FieldProperty[ResRef, ResRef] = FieldProperty("ScriptHeartbeat", GFFFieldType.ResRef)
    on_notice: FieldProperty[ResRef, ResRef] = FieldProperty("ScriptOnNotice", GFFFieldType.ResRef)
    on_spell: FieldProperty[ResRef, ResRef] = FieldProperty("ScriptSpellAt", GFFFieldType.ResRef)
    on_attacked: FieldProperty[ResRef, ResRef] = FieldProperty("ScriptAttacked", GFFFieldType.ResRef)
    on_damaged: FieldProperty[ResRef, ResRef] = FieldProperty("ScriptDamaged", GFFFieldType.ResRef)
    on_disturbed: FieldProperty[ResRef, ResRef] = FieldProperty("ScriptDisturbed", GFFFieldType.ResRef)
    on_end_round: FieldProperty[ResRef, ResRef] = FieldProperty("ScriptEndRound", GFFFieldType.ResRef)
    on_dialog: FieldProperty[ResRef, ResRef] = FieldProperty("ScriptDialogue", GFFFieldType.ResRef)
    on_spawn: FieldProperty[ResRef, ResRef] = FieldProperty("ScriptSpawn", GFFFieldType.ResRef)
    on_rested: FieldProperty[ResRef, ResRef] = FieldProperty("ScriptRested", GFFFieldType.ResRef)
    on_death: FieldProperty[ResRef, ResRef] = FieldProperty("ScriptDeath", GFFFieldType.ResRef)
    on_user_defined: FieldProperty[ResRef, ResRef] = FieldProperty("ScriptUserDefine", GFFFieldType.ResRef)

    # KOTOR 2 TSL Only Fields
    blindspot: FieldProperty[float, float] = FieldProperty("BlindSpot", GFFFieldType.Single, game=Game.K2)
    multiplier_set: FieldProperty[int, int] = FieldProperty("MultiplierSet", GFFFieldType.Int32, game=Game.K2)
    ignore_cre_path: FieldProperty[int, bool] = FieldProperty("IgnoreCrePath", GFFFieldType.UInt8, game=Game.K2, return_type=bool)
    hologram: FieldProperty[int, bool] = FieldProperty("Hologram", GFFFieldType.UInt8, game=Game.K2, return_type=bool)
    will_not_render: FieldProperty[int, bool] = FieldProperty("WillNotRender", GFFFieldType.UInt8, game=Game.K2, return_type=bool)

    # Toolset Only:
    palette_id = FieldProperty("PaletteID", GFFFieldType.UInt8)

    # Deprecated/unused by game engine:
    bodybag_id = FieldProperty("BlindSpot", GFFFieldType.UInt8)
    deity = FieldProperty("Deity", GFFFieldType.String)
    description: FieldProperty[LocalizedString, LocalizedString] = FieldProperty("Description", GFFFieldType.LocalizedString)
    lawfulness = FieldProperty("LawfulChaotic", GFFFieldType.UInt8)
    phenotype_id = FieldProperty("Phenotype", GFFFieldType.Int32)
    # on_rested = FieldProperty("ScriptRested", GFFFieldType.ResRef)
    subrace_name = FieldProperty("Subrace", GFFFieldType.String)
    spec_ability_list = FieldProperty("SpecAbilityList", GFFFieldType.List)
    template_list = FieldProperty("TemplateList", GFFFieldType.List)
    skill_list: FieldProperty[GFFList[GFFStruct], GFFList[UTCSkill]]
    feats: FieldProperty[GFFList[GFFStruct], GFFList[UTCFeat]] = FieldProperty("FeatList", GFFFieldType.List)

    # TODO(th3w1zard1): find out if these are deprecated
    portrait: FieldProperty[ResRef, ResRef] = FieldProperty("Portrait", GFFFieldType.ResRef)
    save_will: FieldProperty[int, int] = FieldProperty("SaveWill", GFFFieldType.UInt8)
    save_fortitude: FieldProperty[int, int] = FieldProperty("SaveFortitude", GFFFieldType.UInt8)
    morale: FieldProperty[int, int] = FieldProperty("Morale", GFFFieldType.UInt8)
    morale_recovery: FieldProperty[int, int] = FieldProperty("MoraleRecovery", GFFFieldType.UInt8)
    morale_breakpoint: FieldProperty[int, int] = FieldProperty("MoraleBreakpoint", GFFFieldType.UInt8)

# Define outside of class constructor so UTC class object is available
UTC.skill_list = FieldProperty("SkillList", GFFFieldType.List, default=UTC.default_skill_list())  # type: ignore[assignment]


def construct_utc(
    gff: GFF,
) -> UTC:
    utc: UTC = deepcopy(gff.root)  # type: ignore[assignment]
    utc.__class__ = UTC

    skill_list: GFFList[UTCSkill] = utc.skill_list
    for skill in skill_list:
        skill.__class__ = UTCSkill

    for utc_class in utc.classes:
        utc_class.__class__ = UTCClass

        power_list_field: FieldGFF[GFFList[UTCPower]] = utc_class.get("KnownList0")
        if power_list_field is None:
            continue
        for power_struct in power_list_field.value():
            power_struct.__class__ = UTCPower

    feat_list: GFFList[UTCFeat] = utc.feats
    for feat_struct in feat_list:
        feat_struct.__class__ = GFFStruct

    equipment_list: GFFList = utc.equiplist
    for equipment_struct in equipment_list:
        equipment_struct.__class__ = UTCEquipment

    for item in utc.inventory:
        item.__class__ = UTCItem

    return utc


def dismantle_utc(
    utc: UTC,
    game: Game = Game.K2,
    *,
    use_deprecated: bool = True,
) -> GFF:
    gff = GFF(GFFContent.UTC)
    gff.root = utc.unwrap(game=game, use_deprecated=use_deprecated)
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
