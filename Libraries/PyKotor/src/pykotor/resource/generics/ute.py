from __future__ import annotations

from pykotor.common.language import LocalizedString
from pykotor.common.misc import Game, ResRef
from pykotor.resource.formats.gff import GFF, GFFContent, GFFList, read_gff, write_gff
from pykotor.resource.formats.gff.gff_auto import bytes_gff
from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES, ResourceType


class UTE:
    """Stores encounter data.

    Attributes
    ----------
        tag: "Tag" field.
        resref: "TemplateResRef" field.
        active: "Active" field.
        difficulty_id: "DifficultyIndex" field.
        faction_id: "Faction" field.
        max_creatures: "MaxCreatures" field.
        player_only: "PlayerOnly" field.
        rec_creatures: "RecCreatures" field.
        reset: "Reset" field.
        reset_time: "ResetTime" field.
        respawns: "Respawns" field.
        single_shot: "SpawnOption" field.
        on_entered: "OnEntered" field.
        on_exit: "OnExit" field.
        on_exhausted: "OnExhausted" field.
        on_heartbeat: "OnHeartbeat" field.
        on_user_defined: "OnUserDefined" field.
        comment: "Comment" field.

        palette_id: "PaletteID" field. Used in toolset only.

        name: "LocalizedName" field. Not used by the game engine.
        unused_difficulty: "Difficulty" field. Not used by the game engine.
    """

    BINARY_TYPE = ResourceType.UTE

    def __init__(
        self,
    ):
        self.resref: ResRef = ResRef.from_blank()
        self.tag: str = ""
        self.comment: str = ""

        self.active: bool = False
        self.player_only: bool = False
        self.reset: bool = False
        self.single_shot: bool = False

        self.difficulty_id: int = 0
        self.faction_id: int = 0

        self.max_creatures: int = 0
        self.rec_creatures: int = 0
        self.reset_time: int = 0
        self.respawns: int = 0

        self.on_exit: ResRef = ResRef.from_blank()
        self.on_exhausted: ResRef = ResRef.from_blank()
        self.on_heartbeat: ResRef = ResRef.from_blank()
        self.on_entered: ResRef = ResRef.from_blank()
        self.on_user_defined: ResRef = ResRef.from_blank()

        self.creatures: list[UTECreature] = []

        # Deprecated:
        self.name: LocalizedString = LocalizedString.from_invalid()
        self.palette_id: int = 0
        self.unused_difficulty: int = 0


class UTECreature:
    """Stores data for a creature that can be spawned by an encounter.

    Attributes
    ----------
        appearance_id: "Appearance" field.
        challenge_rating: "CR" field.
        resref: "ResRef" field.
        single_spawn: "SingleSpawn" field.
        guaranteed_count: "GuaranteedCount" field. KotOR 2 only.
    """

    def __init__(
        self,
    ):
        self.appearance_id: int = 0
        self.challenge_rating: float = 0.0
        self.resref: ResRef = ResRef.from_blank()
        self.single_spawn: bool = False
        self.guaranteed_count: int = 0


def utd_version(
    gff: GFF,
) -> Game:
    for label in "GuaranteedCount":
        for creature_struct in gff.root.acquire("CreatureList", GFFList()):
            if creature_struct.exists(label):
                return Game.K2
    return Game.K1


def construct_ute(
    gff: GFF,
) -> UTE:
    ute = UTE()

    root = gff.root
    ute.tag = root.acquire("Tag", "")
    ute.resref = root.acquire("TemplateResRef", ResRef.from_blank())
    ute.active = bool(root.acquire("Active", 0))
    ute.difficulty_id = root.acquire("DifficultyIndex", 0)
    ute.unused_difficulty = root.acquire("Difficulty", 0)
    ute.faction_id = root.acquire("Faction", 0)
    ute.max_creatures = root.acquire("MaxCreatures", 0)
    ute.player_only = bool(root.acquire("PlayerOnly", 0))
    ute.rec_creatures = root.acquire("RecCreatures", 0)
    ute.reset = bool(root.acquire("Reset", 0))
    ute.reset_time = root.acquire("ResetTime", 0)
    ute.respawns = root.acquire("Respawns", 0)
    ute.single_shot = bool(root.acquire("SpawnOption", 0))
    ute.on_entered = root.acquire("OnEntered", ResRef.from_blank())
    ute.on_exit = root.acquire("OnExit", ResRef.from_blank())
    ute.on_exhausted = root.acquire("OnExhausted", ResRef.from_blank())
    ute.on_heartbeat = root.acquire("OnHeartbeat", ResRef.from_blank())
    ute.on_user_defined = root.acquire("OnUserDefined", ResRef.from_blank())
    ute.comment = root.acquire("Comment", "")
    ute.name = root.acquire("LocalizedName", LocalizedString.from_invalid())
    ute.palette_id = root.acquire("PaletteID", 0)

    creature_list = root.get_list("CreatureList")
    for creature_struct in creature_list:
        creature = UTECreature()
        ute.creatures.append(creature)
        creature.appearance_id = creature_struct.acquire("Appearance", 0)
        creature.challenge_rating = creature_struct.acquire("CR", 0.0)
        creature.single_spawn = bool(creature_struct.acquire("SingleSpawn", 0))
        creature.resref = creature_struct.acquire("ResRef", ResRef.from_blank())
        creature.guaranteed_count = creature_struct.acquire("GuaranteedCount", 0)

    return ute


def dismantle_ute(
    ute: UTE,
    game: Game = Game.K2,
    *,
    use_deprecated: bool = True,
) -> GFF:
    gff = GFF(GFFContent.UTE)

    root = gff.root

    root.set_string("Tag", ute.tag)
    root.set_resref("TemplateResRef", ute.resref)
    root.set_uint8("Active", ute.active)
    root.set_int32("DifficultyIndex", ute.difficulty_id)
    root.set_uint32("Faction", ute.faction_id)
    root.set_int32("MaxCreatures", ute.max_creatures)
    root.set_uint8("PlayerOnly", ute.player_only)
    root.set_int32("RecCreatures", ute.rec_creatures)
    root.set_uint8("Reset", ute.reset)
    root.set_int32("ResetTime", ute.reset_time)
    root.set_int32("Respawns", ute.respawns)
    root.set_int32("SpawnOption", ute.single_shot)
    root.set_resref("OnEntered", ute.on_entered)
    root.set_resref("OnExit", ute.on_exit)
    root.set_resref("OnExhausted", ute.on_exhausted)
    root.set_resref("OnHeartbeat", ute.on_heartbeat)
    root.set_resref("OnUserDefined", ute.on_user_defined)
    root.set_string("Comment", ute.comment)

    root.set_uint8("PaletteID", ute.palette_id)

    creature_list = root.set_list("CreatureList", GFFList())
    for creature in ute.creatures:
        creature_struct = creature_list.add(0)
        creature_struct.set_int32("Appearance", creature.appearance_id)
        creature_struct.set_single("CR", creature.challenge_rating)
        creature_struct.set_uint8("SingleSpawn", creature.single_spawn)
        creature_struct.set_resref("ResRef", creature.resref)
        if game == Game.K2:
            creature_struct.set_int32("GuaranteedCount", creature.guaranteed_count)

    if use_deprecated:
        root.set_locstring("LocalizedName", ute.name)
        root.set_int32("Difficulty", ute.unused_difficulty)

    return gff


def read_ute(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
) -> UTE:
    gff = read_gff(source, offset, size)
    return construct_ute(gff)


def write_ute(
    ute: UTE,
    target: TARGET_TYPES,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
) -> None:
    gff = dismantle_ute(ute, game, use_deprecated=use_deprecated)
    write_gff(gff, target, file_format)


def bytes_ute(
    ute: UTE | SOURCE_TYPES,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
) -> bytes:
    if not isinstance(ute, UTE):
        ute = read_ute(ute)
    gff = dismantle_ute(ute, game, use_deprecated=use_deprecated)
    return bytes_gff(gff, file_format)
