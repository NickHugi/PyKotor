from __future__ import annotations

from pykotor.common.geometry import Vector2, Vector3
from pykotor.common.language import LocalizedString
from pykotor.common.misc import Game, ResRef
from pykotor.resource.formats.gff import GFF, GFFContent, GFFList, read_gff, write_gff
from pykotor.resource.formats.gff.gff_auto import bytes_gff
from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES, ResourceType


class IFO:
    """Stores module information.

    Attributes
    ----------
        mod_id: "Mod_ID" field.
        vo_id: "Mod_VO_ID" field.
        mod_name: "Mod_Name" field.
        tag: "Mod_Tag" field.
        identifier: "Mod_Entry_Area" field.
        entry_position.x: "Mod_Entry_X" field.
        entry_position.y: "Mod_Entry_Y" field.
        entry_position.z: "Mod_Entry_Z" field.
        entry_direction.x: "Mod_Entry_Dir_X" field.
        entry_direction.y: "Mod_Entry_Dir_Y" field.
        on_heartbeat: "Mod_OnHeartbeat" field.
        on_load: "Mod_OnModLoad" field.
        on_start: "Mod_OnModStart" field.
        on_enter: "Mod_OnClientEntr" field.
        on_leave: "Mod_OnClientLeav" field.
        on_activate_item: "Mod_OnActvtItem" field.
        on_acquire_item: "Mod_OnAcquirItem" field.
        on_user_defined: "Mod_OnUsrDefined" field.
        on_unacquire_item: "Mod_OnUnAqreItem" field.
        on_player_death: "Mod_OnPlrDeath" field.
        on_player_dying: "Mod_OnPlrDying" field.
        on_player_levelup: "Mod_OnPlrLvlUp" field.
        on_player_respawn: "Mod_OnSpawnBtnDn" field.
        expansion_id: "Expansion_Pack" field.

        hak: "Mod_Hak" field. Not used by the game engine.
        description: "Mod_Description" field. Not used by the game engine.
        on_player_rest: "Mod_OnPlrRest" field. Not used by the game engine.
        dawn_hour: "Mod_DawnHour" field. Not used by the game engine.
        dusk_hour: "Mod_DuskHour" field. Not used by the game engine.
        time_scale: "Mod_MinPerHour" field. Not used by the game engine.
        start_month: "Mod_StartMonth" field. Not used by the game engine.
        start_day: "Mod_StartDay" field. Not used by the game engine.
        start_hour: "Mod_StartHour" field. Not used by the game engine.
        start_year: "Mod_StartYear" field. Not used by the game engine.
        xp_scale: "Mod_XPScale" field. Not used by the game engine.
        start_movie: "Mod_StartMovie" field. Not used by the game engine.
        creator_id: "Mod_Creator_ID" field. Not used by the game engine.
        version: "Mod_Version" field. Not used by the game engine.
    """

    BINARY_TYPE = ResourceType.IFO

    def __init__(
        self,
    ):
        self.mod_id: bytes = b""
        self.mod_name: LocalizedString = LocalizedString.from_invalid()
        self.area_name: ResRef = ResRef.from_blank()

        self.identifier: ResRef = ResRef.from_blank()
        self.entry_direction: float = 0.0
        self.entry_position: Vector3 = Vector3.from_null()
        self.tag: str = ""
        self.vo_id: str = ""

        self.on_acquire_item: ResRef = ResRef.from_blank()
        self.on_activate_item: ResRef = ResRef.from_blank()
        self.on_enter: ResRef = ResRef.from_blank()
        self.on_leave: ResRef = ResRef.from_blank()
        self.on_heartbeat: ResRef = ResRef.from_blank()
        self.on_load: ResRef = ResRef.from_blank()
        self.on_start: ResRef = ResRef.from_blank()
        self.on_player_death: ResRef = ResRef.from_blank()
        self.on_player_dying: ResRef = ResRef.from_blank()
        self.on_player_levelup: ResRef = ResRef.from_blank()
        self.on_player_respawn: ResRef = ResRef.from_blank()
        self.on_unacquire_item: ResRef = ResRef.from_blank()
        self.on_user_defined: ResRef = ResRef.from_blank()

        # Deprecated:
        self.creator_id: int = 0
        self.version: int = 0
        self.expansion_id: int = 0
        self.hak: str = ""
        self.description: LocalizedString = LocalizedString.from_invalid()
        self.dawn_hour: int = 0
        self.dusk_hour: int = 0
        self.time_scale: int = 0
        self.start_month: int = 0
        self.start_day: int = 0
        self.start_hour: int = 0
        self.start_year: int = 0
        self.xp_scale: int = 0
        self.on_player_rest: ResRef = ResRef.from_blank()
        self.start_movie: ResRef = ResRef.from_blank()


def construct_ifo(
    gff: GFF,
) -> IFO:
    ifo = IFO()

    root = gff.root
    ifo.mod_id = root.acquire("Mod_ID", b"")
    ifo.vo_id = root.acquire("Mod_VO_ID", "")
    ifo.mod_name = root.acquire("Mod_Name", LocalizedString.from_invalid())
    ifo.tag = root.acquire("Mod_Tag", "")
    ifo.identifier = root.acquire("Mod_Entry_Area", ResRef.from_blank())
    ifo.entry_position.x = root.acquire("Mod_Entry_X", 0.0)
    ifo.entry_position.y = root.acquire("Mod_Entry_Y", 0.0)
    ifo.entry_position.z = root.acquire("Mod_Entry_Z", 0.0)
    ifo.on_heartbeat = root.acquire("Mod_OnHeartbeat", ResRef.from_blank())
    ifo.on_load = root.acquire("Mod_OnModLoad", ResRef.from_blank())
    ifo.on_start = root.acquire("Mod_OnModStart", ResRef.from_blank())
    ifo.on_enter = root.acquire("Mod_OnClientEntr", ResRef.from_blank())
    ifo.on_leave = root.acquire("Mod_OnClientLeav", ResRef.from_blank())
    ifo.on_activate_item = root.acquire("Mod_OnActvtItem", ResRef.from_blank())
    ifo.on_acquire_item = root.acquire("Mod_OnAcquirItem", ResRef.from_blank())
    ifo.on_user_defined = root.acquire("Mod_OnUsrDefined", ResRef.from_blank())
    ifo.on_unacquire_item = root.acquire("Mod_OnUnAqreItem", ResRef.from_blank())
    ifo.on_player_death = root.acquire("Mod_OnPlrDeath", ResRef.from_blank())
    ifo.on_player_dying = root.acquire("Mod_OnPlrDying", ResRef.from_blank())
    ifo.on_player_levelup = root.acquire("Mod_OnPlrLvlUp", ResRef.from_blank())
    ifo.on_player_respawn = root.acquire("Mod_OnSpawnBtnDn", ResRef.from_blank())
    ifo.expansion_id = root.acquire("Expansion_Pack", 0)
    ifo.hak = root.acquire("Mod_Hak", "")
    ifo.description = root.acquire("Mod_Description", LocalizedString.from_invalid())
    ifo.on_player_rest = root.acquire("Mod_OnPlrRest", ResRef.from_blank())
    ifo.dawn_hour = root.acquire("Mod_DawnHour", 0)
    ifo.dusk_hour = root.acquire("Mod_DuskHour", 0)
    ifo.time_scale = root.acquire("Mod_MinPerHour", 0)
    ifo.start_month = root.acquire("Mod_StartMonth", 0)
    ifo.start_day = root.acquire("Mod_StartDay", 0)
    ifo.start_hour = root.acquire("Mod_StartHour", 0)
    ifo.start_year = root.acquire("Mod_StartYear", 0)
    ifo.xp_scale = root.acquire("Mod_XPScale", 0)
    ifo.start_movie = root.acquire("Mod_StartMovie", ResRef.from_blank())
    ifo.creator_id = root.acquire("Mod_Creator_ID", 0)
    ifo.version = root.acquire("Mod_Version", 0)

    dir_x = root.acquire("Mod_Entry_Dir_X", 0.0)
    dir_y = root.acquire("Mod_Entry_Dir_Y", 0.0)
    ifo.entry_direction = Vector2(dir_x, dir_y).angle()

    ifo.area_name = root.acquire("Mod_Area_list", GFFList()).at(0).acquire("Area_Name", ResRef.from_blank())

    return ifo


def dismantle_ifo(
    ifo: IFO,
    game: Game = Game.K2,
    *,
    use_deprecated: bool = True,
) -> GFF:
    gff = GFF(GFFContent.IFO)

    root = gff.root
    root.set_binary("Mod_ID", ifo.mod_id)
    root.set_string("Mod_VO_ID", ifo.vo_id)
    root.set_locstring("Mod_Name", ifo.mod_name)
    root.set_string("Mod_Tag", ifo.tag)
    root.set_uint8("Mod_IsSaveGame", 0)
    root.set_resref("Mod_Entry_Area", ifo.identifier)
    root.set_single("Mod_Entry_X", ifo.entry_position.x)
    root.set_single("Mod_Entry_Y", ifo.entry_position.y)
    root.set_single("Mod_Entry_Z", ifo.entry_position.z)
    root.set_resref("Mod_OnHeartbeat", ifo.on_heartbeat)
    root.set_resref("Mod_OnModLoad", ifo.on_load)
    root.set_resref("Mod_OnModStart", ifo.on_start)
    root.set_resref("Mod_OnClientEntr", ifo.on_enter)
    root.set_resref("Mod_OnClientLeav", ifo.on_leave)
    root.set_resref("Mod_OnActvtItem", ifo.on_activate_item)
    root.set_resref("Mod_OnAcquirItem", ifo.on_acquire_item)
    root.set_resref("Mod_OnUsrDefined", ifo.on_user_defined)
    root.set_resref("Mod_OnUnAqreItem", ifo.on_unacquire_item)
    root.set_resref("Mod_OnPlrDeath", ifo.on_player_death)
    root.set_resref("Mod_OnPlrDying", ifo.on_player_dying)
    root.set_resref("Mod_OnPlrLvlUp", ifo.on_player_levelup)
    root.set_resref("Mod_OnSpawnBtnDn", ifo.on_player_respawn)

    entry_direction = Vector2.from_angle(ifo.entry_direction)
    root.set_single("Mod_Entry_Dir_X", entry_direction.x)
    root.set_single("Mod_Entry_Dir_Y", entry_direction.y)

    root.set_list("Mod_Area_list", GFFList()).add(6).set_resref(
        "Area_Name",
        ifo.area_name,
    )

    if use_deprecated:
        root.set_uint16("Expansion_Pack", ifo.expansion_id)
        root.set_string("Mod_Hak", ifo.hak)
        root.set_locstring("Mod_Description", ifo.description)
        root.set_resref("Mod_OnPlrRest", ifo.on_player_rest)
        root.set_uint8("Mod_DawnHour", ifo.dawn_hour)
        root.set_uint8("Mod_DuskHour", ifo.dusk_hour)
        root.set_uint8("Mod_MinPerHour", ifo.time_scale)
        root.set_uint8("Mod_StartMonth", ifo.start_month)
        root.set_uint8("Mod_StartDay", ifo.start_day)
        root.set_uint8("Mod_StartHour", ifo.start_hour)
        root.set_uint32("Mod_StartYear", ifo.start_year)
        root.set_uint8("Mod_XPScale", ifo.xp_scale)
        root.set_resref("Mod_StartMovie", ifo.start_movie)
        root.set_int32("Mod_Creator_ID", ifo.creator_id)
        root.set_uint32("Mod_Version", ifo.version)

    return gff


def read_ifo(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
) -> IFO:
    gff = read_gff(source, offset, size)
    return construct_ifo(gff)


def write_ifo(
    ifo: IFO,
    target: TARGET_TYPES,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
) -> None:
    gff = dismantle_ifo(ifo, game, use_deprecated=use_deprecated)
    write_gff(gff, target, file_format)


def bytes_ifo(
    ifo: IFO | SOURCE_TYPES,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
) -> bytes:
    if not isinstance(ifo, IFO):
        ifo = read_ifo(ifo)
    gff = dismantle_ifo(ifo, game, use_deprecated=use_deprecated)
    return bytes_gff(gff, file_format)
