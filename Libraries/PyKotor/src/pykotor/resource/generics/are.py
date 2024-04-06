from __future__ import annotations

from copy import deepcopy
from enum import IntEnum
from typing import TYPE_CHECKING, TypedDict, cast

from pykotor.common.geometry import Vector2
from pykotor.common.misc import Color, Game
from pykotor.resource.formats.gff import GFF, FieldProperty, GFFContent, GFFFieldType, GFFStructInterface, bytes_gff, read_gff, write_gff
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.common.language import LocalizedString
    from pykotor.common.misc import ResRef
    from pykotor.resource.formats.gff import GFFList, GFFStruct
    from pykotor.resource.formats.gff.gff_data import FieldGFF
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class AREWindPower(IntEnum):
    Still = 0
    Weak = 1
    Strong = 2


class ARENorthAxis(IntEnum):
    PositiveY = 0
    NegativeY = 1
    PositiveX = 2
    NegativeX = 3

class AREMapFields(TypedDict):
    MapZoom: FieldGFF[int]
    MapResX: FieldGFF[int]
    NorthAxis: FieldGFF[int]
    MapPt1X: FieldGFF[float]
    MapPt1Y: FieldGFF[float]
    MapPt2X: FieldGFF[float]
    MapPt2Y: FieldGFF[float]
class AREMap(GFFStructInterface):
    map_zoom: FieldProperty[int, int] = FieldProperty("MapZoom", GFFFieldType.Int32)
    map_res_x: FieldProperty[int, int] = FieldProperty("MapResX", GFFFieldType.Int32)
    north_axis: FieldProperty[int, ARENorthAxis] = FieldProperty("NorthAxis", GFFFieldType.Int32, return_type=ARENorthAxis)
    _mp1x: FieldProperty[float, float] = FieldProperty("MapPt1X", GFFFieldType.Single)
    _mp1y: FieldProperty[float, float] = FieldProperty("MapPt1Y", GFFFieldType.Single)
    _mp2x: FieldProperty[float, float] = FieldProperty("MapPt2X", GFFFieldType.Single)
    _mp2y: FieldProperty[float, float] = FieldProperty("MapPt2Y", GFFFieldType.Single)
    _wp1x: FieldProperty[float, float] = FieldProperty("MapPt1X", GFFFieldType.Single)
    _wp1y: FieldProperty[float, float] = FieldProperty("MapPt1Y", GFFFieldType.Single)
    _wp2x: FieldProperty[float, float] = FieldProperty("MapPt2X", GFFFieldType.Single)
    _wp2y: FieldProperty[float, float] = FieldProperty("MapPt2Y", GFFFieldType.Single)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fields: AREMapFields

    @property
    def map_point_1(self) -> Vector2: return Vector2(self._mp1x, self._mp1y)
    @map_point_1.setter
    def map_point_1(self, value: Vector2):
        self._mp1x, self._mp1y = value.x, value.y

    @property
    def map_point_2(self) -> Vector2: return Vector2(self._mp2x, self._mp2y)
    @map_point_2.setter
    def map_point_2(self, value: Vector2):
        self._mp2x, self._mp2y = value.x, value.y

    @property
    def world_point_1(self) -> Vector2: return Vector2(self._wp1x, self._wp1y)
    @world_point_1.setter
    def world_point_1(self, value: Vector2):
        self._wp1x, self._wp1y = value.x, value.y

    @property
    def world_point_2(self) -> Vector2: return Vector2(self._wp2x, self._wp2y)
    @world_point_2.setter
    def world_point_2(self, value: Vector2):
        self._mp2x, self._wp2y = value.x, value.y

class AREFields(TypedDict):
    Map: FieldGFF[AREMap]
    Version: FieldGFF[int]
    SunAmbientColor: FieldGFF[int]
    SunDiffuseColor: FieldGFF[int]
    DynAmbientColor: FieldGFF[int]
    SunFogColor: FieldGFF[int]
    Grass_Ambient: FieldGFF[int]
    Grass_Diffuse: FieldGFF[int]
    Tag: FieldGFF[str]
    Name: FieldGFF[LocalizedString]
    AlphaTest: FieldGFF[float]
    CameraStyle: FieldGFF[int]
    DefaultEnvMap: FieldGFF[ResRef]
    Grass_TexName: FieldGFF[ResRef]
    Grass_Density: FieldGFF[float]
    Grass_QuadSize: FieldGFF[float]
    Grass_Prob_LL: FieldGFF[float]
    Grass_Prob_LR: FieldGFF[float]
    Grass_Prob_UL: FieldGFF[float]
    Grass_Prob_UR: FieldGFF[float]
    SunFogOn: FieldGFF[int]
    SunFogNear: FieldGFF[float]
    SunFogFar: FieldGFF[float]
    SunShadows: FieldGFF[int]
    ShadowOpacity: FieldGFF[int]
    WindPower: FieldGFF[int]
    Unescapable: FieldGFF[int]
    DisableTransit: FieldGFF[int]
    StealthXPEnabled: FieldGFF[int]
    StealthXPLoss: FieldGFF[int]
    StealthXPMax: FieldGFF[int]
    OnEnter: FieldGFF[ResRef]
    OnExit: FieldGFF[ResRef]
    OnHeartbeat: FieldGFF[ResRef]
    OnUserDefined: FieldGFF[ResRef]
    Rooms: FieldGFF[GFFList[ARERoom]]
    # KOTOR 2 TSL Fields:
    DirtyARGBOne: FieldGFF[int]
    DirtyARGBTwo: FieldGFF[int]
    DirtyARGBThree: FieldGFF[int]
    Grass_Emissive: FieldGFF[int]
    ChanceRain: FieldGFF[int]
    ChanceSnow: FieldGFF[int]
    ChanceLightning: FieldGFF[int]
    DirtySizeOne: FieldGFF[int]
    DirtyFormulaOne: FieldGFF[int]
    DirtyFuncOne: FieldGFF[int]
    DirtySizeTwo: FieldGFF[int]
    DirtyFormulaTwo: FieldGFF[int]
    DirtyFuncTwo: FieldGFF[int]
    DirtySizeThree: FieldGFF[int]
    DirtyFormulaThree: FieldGFF[int]
    DirtyFuncThree: FieldGFF[int]
    # Toolset Only
    Comments: FieldGFF[str]
    # Deprecated/Unused by the game engine
    ID: FieldGFF[int]
    Creator_ID: FieldGFF[int]
    Flags: FieldGFF[int]
    ModSpotCheck: FieldGFF[int]
    ModListenCheck: FieldGFF[int]
    MoonAmbientColor: FieldGFF[int]
    MoonDiffuseColor: FieldGFF[int]
    MoonFogOn: FieldGFF[int]
    MoonFogNear: FieldGFF[float]
    MoonFogFar: FieldGFF[float]
    MoonFogColor: FieldGFF[int]
    MoonShadows: FieldGFF[int]
    IsNight: FieldGFF[int]
    LightingScheme: FieldGFF[int]
    DayNightCycle: FieldGFF[int]
    LoadScreenID: FieldGFF[int]
    NoRest: FieldGFF[int]
    NoHangBack: FieldGFF[int]
    PlayerOnly: FieldGFF[int]
    PlayerVsPlayer: FieldGFF[int]
    Expansion_List: FieldGFF[GFFList[GFFStruct]]
class ARE(GFFStructInterface):
    """Stores static area data."""

    BINARY_TYPE = ResourceType.ARE
    CONTENT_TYPE = GFFContent.ARE

    map: FieldProperty[GFFStruct, AREMap] = FieldProperty("Map", GFFFieldType.Struct, AREMap())
    version: FieldProperty[int, int] = FieldProperty("Version", GFFFieldType.UInt32)

    sun_ambient: FieldProperty[int, Color] = FieldProperty("SunAmbientColor", GFFFieldType.UInt32, store_type=Color.rgb_integer, return_type=Color.from_rgb_integer)
    sun_diffuse: FieldProperty[int, Color] = FieldProperty("SunDiffuseColor", GFFFieldType.UInt32, store_type=Color.rgb_integer, return_type=Color.from_rgb_integer)
    dynamic_light: FieldProperty[int, Color] = FieldProperty("DynAmbientColor", GFFFieldType.UInt32, store_type=Color.rgb_integer, return_type=Color.from_rgb_integer)
    fog_color: FieldProperty[int, Color] = FieldProperty("SunFogColor", GFFFieldType.UInt32, store_type=Color.rgb_integer, return_type=Color.from_rgb_integer)
    grass_ambient: FieldProperty[int, Color] = FieldProperty("Grass_Ambient", GFFFieldType.UInt32, store_type=Color.rgb_integer, return_type=Color.from_rgb_integer)
    grass_diffuse: FieldProperty[int, Color] = FieldProperty("Grass_Diffuse", GFFFieldType.UInt32, store_type=Color.rgb_integer, return_type=Color.from_rgb_integer)

    tag: FieldProperty[str, str] = FieldProperty("Tag", GFFFieldType.String)
    name: FieldProperty[LocalizedString, LocalizedString] = FieldProperty("Name", GFFFieldType.LocalizedString)
    alpha_test: FieldProperty[float, float] = FieldProperty("AlphaTest", GFFFieldType.Single)
    camera_style: FieldProperty[int, int] = FieldProperty("CameraStyle", GFFFieldType.Int32)
    default_envmap: FieldProperty[ResRef, ResRef] = FieldProperty("DefaultEnvMap", GFFFieldType.ResRef)
    grass_texture: FieldProperty[ResRef, ResRef] = FieldProperty("Grass_TexName", GFFFieldType.ResRef)
    grass_density: FieldProperty[float, float] = FieldProperty("Grass_Density", GFFFieldType.Single)
    grass_size: FieldProperty[float, float] = FieldProperty("Grass_QuadSize", GFFFieldType.Single)
    grass_prob_ll: FieldProperty[float, float] = FieldProperty("Grass_Prob_LL", GFFFieldType.Single)
    grass_prob_lr: FieldProperty[float, float] = FieldProperty("Grass_Prob_LR", GFFFieldType.Single)
    grass_prob_ul: FieldProperty[float, float] = FieldProperty("Grass_Prob_UL", GFFFieldType.Single)
    grass_prob_ur: FieldProperty[float, float] = FieldProperty("Grass_Prob_UR", GFFFieldType.Single)
    fog_enabled: FieldProperty[int, bool] = FieldProperty("SunFogOn", GFFFieldType.Int32, return_type=bool)
    fog_near: FieldProperty[float, float] = FieldProperty("SunFogNear", GFFFieldType.Single)
    fog_far: FieldProperty[float, float] = FieldProperty("SunFogFar", GFFFieldType.Single)
    shadows: FieldProperty[int, bool] = FieldProperty("SunShadows", GFFFieldType.UInt8, return_type=bool)
    shadow_opacity: FieldProperty[int, int] = FieldProperty("ShadowOpacity", GFFFieldType.UInt8)
    wind_power: FieldProperty[int, AREWindPower] = FieldProperty("WindPower", GFFFieldType.Int32, return_type=AREWindPower)
    unescapable: FieldProperty[int, bool] = FieldProperty("Unescapable", GFFFieldType.UInt8, return_type=bool)
    disable_transit: FieldProperty[int, bool] = FieldProperty("DisableTransit", GFFFieldType.UInt8)
    stealth_xp: FieldProperty[int, bool] = FieldProperty("StealthXPEnabled", GFFFieldType.UInt8)
    stealth_xp_loss: FieldProperty[int, int] = FieldProperty("StealthXPLoss", GFFFieldType.UInt32)
    stealth_xp_max: FieldProperty[int, int] = FieldProperty("StealthXPMax", GFFFieldType.UInt32)
    on_enter: FieldProperty[ResRef, ResRef] = FieldProperty("OnEnter", GFFFieldType.ResRef)
    on_exit: FieldProperty[ResRef, ResRef] = FieldProperty("OnExit", GFFFieldType.ResRef)
    on_heartbeat: FieldProperty[ResRef, ResRef] = FieldProperty("OnHeartbeat", GFFFieldType.ResRef)
    on_user_defined: FieldProperty[ResRef, ResRef] = FieldProperty("OnUserDefined", GFFFieldType.ResRef)

    rooms: FieldProperty[GFFList[ARERoom], GFFList[ARERoom]] = FieldProperty("Rooms", GFFFieldType.List)

    # KOTOR 2 TSL Fields:
    dirty_argb_1: FieldProperty[int, Color] = FieldProperty("DirtyARGBOne", GFFFieldType.Int32, game=Game.K2, store_type=Color.rgb_integer, return_type=Color.from_rgb_integer)
    dirty_argb_2: FieldProperty[int, Color] = FieldProperty("DirtyARGBTwo", GFFFieldType.Int32, game=Game.K2, store_type=Color.rgb_integer, return_type=Color.from_rgb_integer)
    dirty_argb_3: FieldProperty[int, Color] = FieldProperty("DirtyARGBThree", GFFFieldType.Int32, game=Game.K2, store_type=Color.rgb_integer, return_type=Color.from_rgb_integer)
    grass_emissive: FieldProperty[int, Color] = FieldProperty("Grass_Emissive", GFFFieldType.UInt32, game=Game.K2, store_type=Color.rgb_integer, return_type=Color.from_rgb_integer)
    chance_rain: FieldProperty[int, int] = FieldProperty("ChanceRain", GFFFieldType.Int32, game=Game.K2)
    chance_snow: FieldProperty[int, int] = FieldProperty("ChanceSnow", GFFFieldType.Int32, game=Game.K2)
    chance_lightning: FieldProperty[int, int] = FieldProperty("ChanceLightning", GFFFieldType.Int32, game=Game.K2)
    dirty_size_1: FieldProperty[int, int] = FieldProperty("DirtySizeOne", GFFFieldType.Int32, game=Game.K2)
    dirty_formula_1: FieldProperty[int, int] = FieldProperty("DirtyFormulaOne", GFFFieldType.Int32, game=Game.K2)
    dirty_func_1: FieldProperty[int, int] = FieldProperty("DirtyFuncOne", GFFFieldType.Int32, game=Game.K2)
    dirty_size_2: FieldProperty[int, int] = FieldProperty("DirtySizeTwo", GFFFieldType.Int32, game=Game.K2)
    dirty_formula_2: FieldProperty[int, int] = FieldProperty("DirtyFormulaTwo", GFFFieldType.Int32, game=Game.K2)
    dirty_func_2: FieldProperty[int, int] = FieldProperty("DirtyFuncTwo", GFFFieldType.Int32, game=Game.K2)
    dirty_size_3: FieldProperty[int, int] = FieldProperty("DirtySizeThree", GFFFieldType.Int32, game=Game.K2)
    dirty_formula_3: FieldProperty[int, int] = FieldProperty("DirtyFormulaThre", GFFFieldType.Int32, game=Game.K2)
    dirty_func_3: FieldProperty[int, int] = FieldProperty("DirtyFuncThree", GFFFieldType.Int32, game=Game.K2)

    # Toolset Only
    comment: FieldProperty[str, str] = FieldProperty("Comments", GFFFieldType.String)

    # Deprecated/Unused by the game engine
    unused_id: FieldProperty[int, int] = FieldProperty("ID", GFFFieldType.Int32)
    creator_id: FieldProperty[int, int] = FieldProperty("Creator_ID", GFFFieldType.Int32)
    flags: FieldProperty[int, int] = FieldProperty("Flags", GFFFieldType.UInt32)#, store_type=lambda x: struct.unpack("I", x)[0], return_type=lambda x: struct.pack("I", x))
    mod_spot_check: FieldProperty[int, int] = FieldProperty("ModSpotCheck", GFFFieldType.Int32)
    mod_listen_check: FieldProperty[int, int] = FieldProperty("ModListenCheck", GFFFieldType.Int32)
    moon_ambient: FieldProperty[int, int] = FieldProperty("MoonAmbientColor", GFFFieldType.UInt32)
    moon_diffuse: FieldProperty[int, int] = FieldProperty("MoonDiffuseColor", GFFFieldType.UInt32)
    moon_fog: FieldProperty[int, bool] = FieldProperty("MoonFogOn", GFFFieldType.UInt8)
    moon_fog_near: FieldProperty[int, int] = FieldProperty("MoonFogNear", GFFFieldType.Single)
    moon_fog_far: FieldProperty[int, int] = FieldProperty("MoonFogFar", GFFFieldType.Single)
    moon_fog_color: FieldProperty[int, int] = FieldProperty("MoonFogColor", GFFFieldType.UInt32)
    moon_shadows: FieldProperty[int, int] = FieldProperty("MoonShadows", GFFFieldType.UInt8, return_type=bool)
    is_night: FieldProperty[int, bool] = FieldProperty("IsNight", GFFFieldType.UInt8, return_type=bool)
    lighting_scheme: FieldProperty[int, int] = FieldProperty("LightingScheme", GFFFieldType.UInt8)
    day_night: FieldProperty[int, bool] = FieldProperty("DayNightCycle", GFFFieldType.UInt8, return_type=bool)
    loadscreen_id: FieldProperty[int, int] = FieldProperty("LoadScreenID", GFFFieldType.UInt16)
    no_rest: FieldProperty[int, bool] = FieldProperty("NoRest", GFFFieldType.UInt8, return_type=bool)
    no_hang_back: FieldProperty[int, bool] = FieldProperty("NoHangBack", GFFFieldType.UInt8, return_type=bool)
    player_only: FieldProperty[int, bool] = FieldProperty("PlayerOnly", GFFFieldType.UInt8, return_type=bool)
    player_vs_player: FieldProperty[int, int] = FieldProperty("PlayerVsPlayer", GFFFieldType.UInt8)
    expansion_list: FieldProperty[GFFList[GFFStruct], GFFList[GFFStruct]] = FieldProperty("Expansion_List", GFFFieldType.List)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fields: AREFields

class ARERoomFields(TypedDict):
    RoomName: FieldGFF[str]
    DisableWeather: FieldGFF[bool]
    EnvAudio: FieldGFF[int]
    ForceRating: FieldGFF[int]
    AmbientScale: FieldGFF[float]
class ARERoom(GFFStructInterface):
    name: FieldProperty[str, str] = FieldProperty("RoomName", GFFFieldType.String)
    weather: FieldProperty[int, bool] = FieldProperty("DisableWeather", GFFFieldType.UInt8, return_type=bool)
    env_audio: FieldProperty[int, int] = FieldProperty("EnvAudio", GFFFieldType.Int32)
    force_rating: FieldProperty[int, int] = FieldProperty("ForceRating", GFFFieldType.Int32)
    ambient_scale: FieldProperty[float, float] = FieldProperty("AmbientScale", GFFFieldType.Single)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


def construct_are(
    gff: GFF,
) -> ARE:
    """Constructs an ARE object from a GFF file.

    Args:
    ----
        gff: GFF - The GFF file object

    Returns:
    -------
        ARE - The constructed ARE object
    """
    are: ARE = cast(ARE, deepcopy(gff.root))
    are.__class__ = ARE
    are.map.__class__ = AREMap
    for room_struct in are.rooms:
        room_struct.__class__ = ARERoom
    return are


def dismantle_are(
    are: ARE,
    game: Game = Game.K2,
    *,
    use_deprecated: bool = True,
) -> GFF:
    """Creates a new GFF object from an ARE object.

    Args:
    ----
        are: ARE - The ARE structure to unwrap
        game: Game - The game type (K1, K2, etc)
        use_deprecated: bool - Whether to include deprecated fields. If False then deprecated fields will be removed.

    Returns:
    -------
        gff: GFF - The converted GFF structure
    """
    gff = GFF(GFFContent.ARE)
    gff.root = are.unwrap(game=game, use_deprecated=use_deprecated)
    return gff


def read_are(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
) -> ARE:
    """Returns an ARE instance from the source.

    Args:
    ----
        source: The source to read from
        offset: The byte offset to start reading from
        size: The maximum number of bytes to read

    Returns:
    -------
        ARE: The constructed annotation regions

    Processing Logic:
    ----------------
        - Read GFF from source starting at offset with max size
        - Construct ARE object from parsed GFF
    """
    gff = read_gff(source, offset, size)
    return construct_are(gff)


def write_are(
    are: ARE,
    target: TARGET_TYPES,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
):
    """Writes an ARE resource to a target file format.

    Args:
    ----
        are: ARE - The ARE resource to write
        target: TARGET_TYPES - The target file path or object to write to
        game: Game - The game type of the ARE (default K2)
        file_format: ResourceType - The file format to write as (default GFF)
        use_deprecated: bool - Whether to include deprecated fields (default True)

    Returns:
    -------
        None: Writes the ARE as GFF to the target without returning anything

    Processing Logic:
    ----------------
        - Dismantles the ARE into a GFF structure
        - Writes the GFF structure to the target using the specified file format
    """
    gff = dismantle_are(are, game, use_deprecated=use_deprecated)
    write_gff(gff, target, file_format)


def bytes_are(
    are: ARE,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
) -> bytes:
    """Converts ARE to bytes in specified file format.

    Args:
    ----
        are: ARE: area object
        game: Game: Game type are is for
        file_format: ResourceType: File format to convert to
        use_deprecated: bool: Use deprecated ARE fields if true

    Returns:
    -------
        bytes: Converted ARE bytes

    Processing Logic:
    ----------------
        - Dismantle ARE to GFF format
        - Convert GFF to specified file format bytes
    """
    gff = dismantle_are(are, game, use_deprecated=use_deprecated)
    return bytes_gff(gff, file_format)
