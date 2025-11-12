from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.language import LocalizedString
from pykotor.common.misc import Game, ResRef
from pykotor.resource.formats.gff import GFF, GFFContent, GFFList, read_gff, write_gff
from pykotor.resource.formats.gff.gff_auto import bytes_gff
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class UTE:
    """Stores encounter data.

    UTE files are GFF-based format files that store encounter definitions including
    creature spawn lists, difficulty, respawn settings, and script hooks.

    References:
    ----------
        vendor/reone/src/libs/resource/parser/gff/ute.cpp:38-65 (UTE parsing from GFF)
        vendor/reone/include/reone/resource/parser/gff/ute.h:36-59 (UTE structure definitions)
        vendor/Kotor.NET/Kotor.NET/Resources/KotorUTE/UTE.cs:11-35 (UTE class definition)
        Note: UTE files are GFF format files with specific structure definitions

    Attributes:
    ----------
        resref: "TemplateResRef" field. The resource reference for this encounter template.
            Reference: reone/ute.cpp:63 (TemplateResRef field)
            Reference: reone/ute.h:58 (TemplateResRef field)
            Reference: Kotor.NET/UTE.cs:15 (TemplateResRef property)

        tag: "Tag" field. Tag identifier for this encounter.
            Reference: reone/ute.cpp:62 (Tag field)
            Reference: reone/ute.h:57 (Tag field)
            Reference: Kotor.NET/UTE.cs:13 (Tag property)

        comment: "Comment" field. Developer comment.
            Reference: reone/ute.cpp:41 (Comment field)
            Reference: reone/ute.h:38 (Comment field)
            Reference: Kotor.NET/UTE.cs:33 (Comment property)

        active: "Active" field. Whether encounter is active.
            Reference: reone/ute.cpp:40 (Active field)
            Reference: reone/ute.h:37 (Active field)
            Reference: Kotor.NET/UTE.cs:16 (Active property)

        difficulty_id: "DifficultyIndex" field. Difficulty index identifier.
            Reference: reone/ute.cpp:46 (DifficultyIndex field)
            Reference: reone/ute.h:41 (DifficultyIndex field)
            Reference: Kotor.NET/UTE.cs:18 (DifficultyIndex property)

        faction_id: "Faction" field. Faction identifier.
            Reference: reone/ute.cpp:47 (Faction field)
            Reference: reone/ute.h:42 (Faction field)
            Reference: Kotor.NET/UTE.cs:19 (Faction property)

        max_creatures: "MaxCreatures" field. Maximum number of creatures to spawn.
            Reference: reone/ute.cpp:49 (MaxCreatures field)
            Reference: reone/ute.h:44 (MaxCreatures field)
            Reference: Kotor.NET/UTE.cs:20 (MaxCreatures property)

        player_only: "PlayerOnly" field. Whether encounter only triggers for player.
            Reference: reone/ute.cpp:56 (PlayerOnly field)
            Reference: reone/ute.h:51 (PlayerOnly field)
            Reference: Kotor.NET/UTE.cs:21 (PlayerOnly property)

        rec_creatures: "RecCreatures" field. Recommended number of creatures.
            Reference: reone/ute.cpp:57 (RecCreatures field)
            Reference: reone/ute.h:52 (RecCreatures field)
            Reference: Kotor.NET/UTE.cs:22 (RecCreatures property)

        reset: "Reset" field. Whether encounter resets after completion.
            Reference: reone/ute.cpp:58 (Reset field)
            Reference: reone/ute.h:53 (Reset field)
            Reference: Kotor.NET/UTE.cs:23 (Reset property)

        reset_time: "ResetTime" field. Time in seconds before reset.
            Reference: reone/ute.cpp:59 (ResetTime field)
            Reference: reone/ute.h:54 (ResetTime field)
            Reference: Kotor.NET/UTE.cs:24 (ResetTime property)

        respawns: "Respawns" field. Number of times encounter can respawn.
            Reference: reone/ute.cpp:60 (Respawns field)
            Reference: reone/ute.h:55 (Respawns field)
            Reference: Kotor.NET/UTE.cs:25 (Respawns property)

        single_shot: "SpawnOption" field. Whether encounter spawns only once.
            Reference: reone/ute.cpp:61 (SpawnOption field)
            Reference: reone/ute.h:56 (SpawnOption field)
            Reference: Kotor.NET/UTE.cs:26 (SpawnOption property)

        on_entered: "OnEntered" field. Script to run when encounter area is entered.
            Reference: reone/ute.cpp:50 (OnEntered field)
            Reference: reone/ute.h:45 (OnEntered field)
            Reference: Kotor.NET/UTE.cs:27 (OnEntered property)

        on_exit: "OnExit" field. Script to run when leaving encounter area.
            Reference: reone/ute.cpp:52 (OnExit field)
            Reference: reone/ute.h:47 (OnExit field)
            Reference: Kotor.NET/UTE.cs:28 (OnExit property)

        on_exhausted: "OnExhausted" field. Script to run when encounter is exhausted.
            Reference: reone/ute.cpp:51 (OnExhausted field)
            Reference: reone/ute.h:46 (OnExhausted field)
            Reference: Kotor.NET/UTE.cs:29 (OnExhausted property)

        on_heartbeat: "OnHeartbeat" field. Script to run on heartbeat.
            Reference: reone/ute.cpp:53 (OnHeartbeat field)
            Reference: reone/ute.h:48 (OnHeartbeat field)
            Reference: Kotor.NET/UTE.cs:30 (OnHeartbeat property)

        on_user_defined: "OnUserDefined" field. Script to run on user-defined event.
            Reference: reone/ute.cpp:54 (OnUserDefined field)
            Reference: reone/ute.h:49 (OnUserDefined field)
            Reference: Kotor.NET/UTE.cs:31 (OnUserDefined property)

        creatures: List of UTECreature objects representing spawnable creatures.
            Reference: reone/ute.cpp:42-44 (CreatureList parsing)
            Reference: reone/ute.h:39 (CreatureList vector)
            Reference: reone/ute.h:28-34 (UTE_CreatureList struct)
            Reference: Kotor.NET/UTE.cs:34 (Creatures property)

        palette_id: "PaletteID" field. Palette identifier. Used in toolset only.
            Reference: reone/ute.cpp:55 (PaletteID field)
            Reference: reone/ute.h:50 (PaletteID field)
            Reference: Kotor.NET/UTE.cs:32 (PaletteID property)

        name: "LocalizedName" field. Localized name. Not used by the game engine.
            Reference: reone/ute.cpp:48 (LocalizedName field)
            Reference: reone/ute.h:43 (LocalizedName field)
            Reference: Kotor.NET/UTE.cs:14 (LocalizedName property)

        unused_difficulty: "Difficulty" field. Difficulty value. Not used by the game engine.
            Reference: reone/ute.cpp:45 (Difficulty field)
            Reference: reone/ute.h:40 (Difficulty field)
            Reference: Kotor.NET/UTE.cs:17 (Difficulty property)
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

    References:
    ----------
        vendor/reone/include/reone/resource/parser/gff/ute.h:28-34 (UTE_CreatureList struct)
        vendor/reone/src/libs/resource/parser/gff/ute.cpp:28-36 (UTE_CreatureList parsing)
        vendor/Kotor.NET/Kotor.NET/Resources/KotorUTE/UTE.cs:37-44 (UTECreature class)

    Attributes:
    ----------
        appearance_id: "Appearance" field. Appearance type identifier for this creature.
            Reference: reone/ute.cpp:30 (Appearance field)
            Reference: reone/ute.h:29 (Appearance field)
            Reference: Kotor.NET/UTE.cs:39 (Appearance property)

        challenge_rating: "CR" field. Challenge rating value.
            Reference: reone/ute.cpp:31 (CR field)
            Reference: reone/ute.h:30 (CR field)
            Reference: Kotor.NET/UTE.cs:40 (CR property)

        resref: "ResRef" field. Resource reference to creature template (UTC file).
            Reference: reone/ute.cpp:33 (ResRef field)
            Reference: reone/ute.h:32 (ResRef field)
            Reference: Kotor.NET/UTE.cs:41 (ResRef property)

        single_spawn: "SingleSpawn" field. Whether this creature spawns only once.
            Reference: reone/ute.cpp:34 (SingleSpawn field)
            Reference: reone/ute.h:33 (SingleSpawn field)
            Reference: Kotor.NET/UTE.cs:42 (SingleSpawn property)

        guaranteed_count: "GuaranteedCount" field. Guaranteed spawn count. KotOR 2 only.
            Reference: reone/ute.cpp:32 (GuaranteedCount field)
            Reference: reone/ute.h:31 (GuaranteedCount field)
            Reference: Kotor.NET/UTE.cs:43 (GuaranteedCount property)
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
    if creature_list is not None:
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
        if game.is_k2():
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
):
    gff = dismantle_ute(ute, game, use_deprecated=use_deprecated)
    write_gff(gff, target, file_format)


def bytes_ute(
    ute: UTE,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
) -> bytes:
    gff = dismantle_ute(ute, game, use_deprecated=use_deprecated)
    return bytes_gff(gff, file_format)
