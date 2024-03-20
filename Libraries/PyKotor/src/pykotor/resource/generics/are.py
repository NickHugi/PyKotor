from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

from pykotor.common.geometry import Vector2
from pykotor.common.language import LocalizedString
from pykotor.common.misc import Color, Game, ResRef
from pykotor.resource.formats.gff import GFF, GFFContent, GFFList, GFFStruct, read_gff, write_gff
from pykotor.resource.formats.gff.gff_auto import bytes_gff
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class ARE:
    """Stores static area data.

    Attributes:
    ----------
        tag: "Tag" field.
        name: "Name" field.
        alpha_test: "AlphaTest" field.
        camera_style: "CameraStyle" field.
        default_envmap: "DefaultEnvMap" field.
        grass_texture: "Grass_TexName" field.
        grass_density: "Grass_Density" field.
        grass_size: "Grass_QuadSize" field.
        grass_prob_ll: "Grass_Prob_LL" field.
        grass_prob_lr: "Grass_Prob_LR" field.
        grass_prob_ul: "Grass_Prob_UL" field.
        grass_prob_ur: "Grass_Prob_UR" field.
        fog_enabled: "SunFogOn" field.
        fog_near: "SunFogNear" field.
        fog_far: "SunFogFar" field.
        shadows: "SunShadows" field.
        shadow_opacity: "ShadowOpacity" field.
        wind_power: "WindPower" field.
        unescapable: "Unescapable" field.
        disable_transit: "DisableTransit" field.
        stealth_xp: "StealthXPEnabled" field.
        stealth_xp_loss: "StealthXPLoss" field.
        stealth_xp_max: "StealthXPMax" field.
        on_enter: "OnEnter" field.
        on_exit: "OnExit" field.
        on_heartbeat: "OnHeartbeat" field.
        on_user_defined: "OnUserDefined" field.
        sun_ambient: "SunAmbientColor" field.
        sun_diffuse: "SunDiffuseColor" field.
        dynamic_light: "DynAmbientColor" field.
        fog_color: "SunFogColor" field.
        grass_ambient: "Grass_Ambient" field.
        grass_diffuse: "Grass_Diffuse" field.

        dirty_argb_1: "DirtyARGBOne" field. KotOR 2 Only.
        dirty_argb_2: "DirtyARGBTwo" field. KotOR 2 Only.
        dirty_argb_3: "DirtyARGBThree" field. KotOR 2 Only.
        grass_emissive: "Grass_Emissive" field. KotOR 2 Only.
        chance_rain: "ChanceRain" field. KotOR 2 Only.
        chance_snow: "ChanceSnow" field. KotOR 2 Only.
        chance_lightning: "ChanceLightning" field. KotOR 2 Only.
        dirty_size_1: "DirtySizeOne" field. KotOR 2 Only.
        dirty_formula_1: "DirtyFormulaOne" field. KotOR 2 Only.
        dirty_func_1: "DirtyFuncOne" field. KotOR 2 Only.
        dirty_size_2: "DirtySizeTwo" field. KotOR 2 Only.
        dirty_formula_2: "DirtyFormulaTwo" field. KotOR 2 Only.
        dirty_func_2: "DirtyFuncTwo" field. KotOR 2 Only.
        dirty_size_3: "DirtySizeThree" field. KotOR 2 Only.
        dirty_formula_3: "DirtyFormulaThre" field. KotOR 2 Only.
        dirty_func_3: "DirtyFuncThree" field. KotOR 2 Only.

        comment: "Comments" field. Used in toolset only.

        unused_id: "ID" field. Not used by the game engine.
        creator_id: "Creator_ID" field. Not used by the game engine.
        flags: "Flags" field. Not used by the game engine.
        mod_spot_check: "ModSpotCheck" field. Not used by the game engine.
        mod_listen_check: "ModListenCheck" field. Not used by the game engine.
        moon_ambient: "MoonAmbientColor" field. Not used by the game engine.
        moon_diffuse: "MoonDiffuseColor" field. Not used by the game engine.
        moon_fog: "MoonFogOn" field. Not used by the game engine.
        moon_fog_near: "MoonFogNear" field. Not used by the game engine.
        moon_fog_far: "MoonFogFar" field. Not used by the game engine.
        moon_fog_color: "MoonFogColor" field. Not used by the game engine.
        moon_shadows: "MoonShadows" field. Not used by the game engine.
        is_night: "IsNight" field. Not used by the game engine.
        lighting_scheme: "LightingScheme" field. Not used by the game engine.
        day_night: "DayNightCycle" field. Not used by the game engine.
        loadscreen_id: "LoadScreenID" field. Not used by the game engine.
        no_rest: "NoRest" field. Not used by the game engine.
        no_hang_back: "NoHangBack" field. Not used by the game engine.
        player_only: "PlayerOnly" field. Not used by the game engine.
        player_vs_player: "PlayerVsPlayer" field. Not used by the game engine.
    """

    BINARY_TYPE = ResourceType.ARE

    def __init__(
        self,
    ):
        self.alpha_test: float = 0.0
        self.camera_style: int = 0

        self.chance_lightning: int = 0
        self.chance_snow: int = 0
        self.chance_rain: int = 0

        self.comment: str = ""

        self.default_envmap: ResRef = ResRef.from_blank()

        self.disable_transit: bool = False

        self.dynamic_light: Color = Color.BLACK
        self.sun_ambient: Color = Color.BLACK
        self.sun_diffuse: Color = Color.BLACK
        self.shadow_opacity: int = 0
        self.shadows: bool = False

        self.fog_color: Color = Color.BLACK
        self.fog_near: float = 0
        self.fog_far: float = 0
        self.fog_enabled: bool = False

        self.dirty_argb_1: Color = Color.BLACK
        self.dirty_func_1: int = 0
        self.dirty_size_1: int = 0
        self.dirty_formula_1: int = 0

        self.dirty_argb_2: Color = Color.BLACK
        self.dirty_func_2: int = 0
        self.dirty_size_2: int = 0
        self.dirty_formula_2: int = 0

        self.dirty_argb_3: Color = Color.BLACK
        self.dirty_func_3: int = 0
        self.dirty_size_3: int = 0
        self.dirty_formula_3: int = 0

        self.grass_ambient: Color = Color.BLACK
        self.grass_diffuse: Color = Color.BLACK
        self.grass_emissive: Color = Color.BLACK
        self.grass_density: float = 0.0
        self.grass_size: float = 0.0
        self.grass_prob_ll: float = 0.0
        self.grass_prob_lr: float = 0.0
        self.grass_prob_ul: float = 0.0
        self.grass_prob_ur: float = 0.0
        self.grass_texture: ResRef = ResRef.from_blank()

        self.wind_power: AREWindPower = AREWindPower.Still

        self.on_enter: ResRef = ResRef.from_blank()
        self.on_exit: ResRef = ResRef.from_blank()
        self.on_heartbeat: ResRef = ResRef.from_blank()
        self.on_user_defined: ResRef = ResRef.from_blank()

        self.stealth_xp: bool = False
        self.stealth_xp_loss: int = 0
        self.stealth_xp_max: int = 0

        self.name: LocalizedString = LocalizedString.from_invalid()
        self.tag: str = ""
        self.unescapable: bool = False

        self.map_original_struct_id: int = 0
        self.map_point_1: Vector2 = Vector2.from_null()
        self.map_point_2: Vector2 = Vector2.from_null()
        self.world_point_1: Vector2 = Vector2.from_null()
        self.world_point_2: Vector2 = Vector2.from_null()
        self.map_res_x: int = 0
        self.map_zoom: int = 0
        self.north_axis: ARENorthAxis = ARENorthAxis.PositiveX

        self.rooms: list[ARERoom] = []

        self.version: int = 0

        # Deprecated:
        self.unused_id: int = 0
        self.creator_id: int = 0
        self.flags: int = 0
        self.mod_spot_check: int = 0
        self.mod_listen_check: int = 0
        self.moon_ambient: int = 0
        self.moon_diffuse: int = 0
        self.moon_fog: int = 0
        self.moon_fog_near: float = 0.0
        self.moon_fog_far: float = 0.0
        self.moon_fog_color: int = 0
        self.moon_shadows: int = 0
        self.is_night: int = 0
        self.lighting_scheme: int = 0
        self.day_night: int = 0
        self.loadscreen_id: int = 0
        self.no_rest: int = 0
        self.no_hang_back: int = 0
        self.player_only: int = 0
        self.player_vs_player: int = 0


class ARERoom:
    def __init__(
        self,
        name: str,
        weather: bool,
        env_audio: int,
        force_rating: int,
        ambient_scale: float,
    ):
        self.name: str = name
        self.weather: bool = weather
        self.env_audio: int = env_audio
        self.force_rating: int = force_rating
        self.ambient_scale: float = ambient_scale


class AREWindPower(IntEnum):
    Still = 0
    Weak = 1
    Strong = 2


class ARENorthAxis(IntEnum):
    PositiveY = 0
    NegativeY = 1
    PositiveX = 2
    NegativeX = 3


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

    Processing Logic:
    ----------------
        - Acquires values from the GFF root node and assigns them to ARE properties
        - Handles color values as special case, converting to Color objects
        - All other values assigned directly from GFF.
    """
    are = ARE()

    root = gff.root
    map_struct = root.acquire("Map", GFFStruct())
    are.map_original_struct_id = map_struct.struct_id

    are.north_axis = ARENorthAxis(
        map_struct.acquire("NorthAxis", 0),
    )
    are.map_zoom = map_struct.acquire("MapZoom", 0)
    are.map_res_x = map_struct.acquire("MapResX", 0)
    are.map_point_1 = Vector2(
        map_struct.acquire("MapPt1X", 0.0),
        map_struct.acquire("MapPt1Y", 0.0),
    )
    are.map_point_2 = Vector2(
        map_struct.acquire("MapPt2X", 0.0),
        map_struct.acquire("MapPt2Y", 0.0),
    )
    are.world_point_1 = Vector2(
        map_struct.acquire("WorldPt1X", 0.0),
        map_struct.acquire("WorldPt1Y", 0.0),
    )
    are.world_point_2 = Vector2(
        map_struct.acquire("WorldPt2X", 0.0),
        map_struct.acquire("WorldPt2Y", 0.0),
    )
    are.version = root.acquire("Version", 0)
    are.tag = root.acquire("Tag", "")
    are.name = root.acquire("Name", LocalizedString.from_invalid())
    are.comment = root.acquire("Comments", "")
    are.alpha_test = root.acquire("AlphaTest", 0.0)
    are.camera_style = root.acquire("CameraStyle", 0)
    are.default_envmap = root.acquire("DefaultEnvMap", ResRef.from_blank())
    are.grass_texture = root.acquire("Grass_TexName", ResRef.from_blank())
    are.grass_density = root.acquire("Grass_Density", 0.0)
    are.grass_size = root.acquire("Grass_QuadSize", 0.0)
    are.grass_prob_ll = root.acquire("Grass_Prob_LL", 0.0)
    are.grass_prob_lr = root.acquire("Grass_Prob_LR", 0.0)
    are.grass_prob_ul = root.acquire("Grass_Prob_UL", 0.0)
    are.grass_prob_ur = root.acquire("Grass_Prob_UR", 0.0)
    are.fog_enabled = bool(root.acquire("SunFogOn", 0))
    are.fog_near = root.acquire("SunFogNear", 0.0)
    are.fog_far = root.acquire("SunFogFar", 0.0)
    are.shadows = bool(root.acquire("SunShadows", 0))
    are.shadow_opacity = root.acquire("ShadowOpacity", 0)
    are.wind_power = AREWindPower(root.acquire("WindPower", 0))
    are.unescapable = bool(root.acquire("Unescapable", 0))
    are.disable_transit = bool(root.acquire("DisableTransit", 0))
    are.stealth_xp = bool(root.acquire("StealthXPEnabled", 0))
    are.stealth_xp_loss = root.acquire("StealthXPLoss", 0)
    are.stealth_xp_max = root.acquire("StealthXPMax", 0)
    are.on_enter = root.acquire("OnEnter", ResRef.from_blank())
    are.on_exit = root.acquire("OnExit", ResRef.from_blank())
    are.on_heartbeat = root.acquire("OnHeartbeat", ResRef.from_blank())
    are.on_user_defined = root.acquire("OnUserDefined", ResRef.from_blank())
    are.chance_rain = root.acquire("ChanceRain", 0)
    are.chance_snow = root.acquire("ChanceSnow", 0)
    are.chance_lightning = root.acquire("ChanceLightning", 0)
    are.dirty_size_1 = root.acquire("DirtySizeOne", 0)
    are.dirty_formula_1 = root.acquire("DirtyFormulaOne", 0)
    are.dirty_func_1 = root.acquire("DirtyFuncOne", 0)
    are.dirty_size_2 = root.acquire("DirtySizeTwo", 0)
    are.dirty_formula_2 = root.acquire("DirtyFormulaTwo", 0)
    are.dirty_func_2 = root.acquire("DirtyFuncTwo", 0)
    are.dirty_size_3 = root.acquire("DirtySizeThree", 0)
    are.dirty_formula_3 = root.acquire("DirtyFormulaThre", 0)
    are.dirty_func_3 = root.acquire("DirtyFuncThree", 0)
    are.unused_id = root.acquire("ID", 0)
    are.creator_id = root.acquire("Creator_ID", 0)
    are.flags = root.acquire("Flags", 0)
    are.mod_spot_check = root.acquire("ModSpotCheck", 0)
    are.mod_listen_check = root.acquire("ModListenCheck", 0)
    are.moon_ambient = root.acquire("MoonAmbientColor", 0)
    are.moon_diffuse = root.acquire("MoonDiffuseColor", 0)
    are.moon_fog = root.acquire("MoonFogOn", 0)
    are.moon_fog_near = root.acquire("MoonFogNear", 0.0)
    are.moon_fog_far = root.acquire("MoonFogFar", 0.0)
    are.moon_fog_color = root.acquire("MoonFogColor", 0)
    are.moon_shadows = root.acquire("MoonShadows", 0)
    are.is_night = root.acquire("IsNight", 0)
    are.lighting_scheme = root.acquire("LightingScheme", 0)
    are.day_night = root.acquire("DayNightCycle", 0)
    are.loadscreen_id = root.acquire("LoadScreenID", 0)
    are.no_rest = root.acquire("NoRest", 0)
    are.no_hang_back = root.acquire("NoHangBack", 0)
    are.player_only = root.acquire("PlayerOnly", 0)
    are.player_vs_player = root.acquire("PlayerVsPlayer", 0)

    are.sun_ambient = Color.from_rgb_integer(root.acquire("SunAmbientColor", 0))
    are.sun_diffuse = Color.from_rgb_integer(root.acquire("SunDiffuseColor", 0))
    are.dynamic_light = Color.from_rgb_integer(root.acquire("DynAmbientColor", 0))
    are.fog_color = Color.from_rgb_integer(root.acquire("SunFogColor", 0))
    are.grass_ambient = Color.from_rgb_integer(root.acquire("Grass_Ambient", 0))
    are.grass_diffuse = Color.from_rgb_integer(root.acquire("Grass_Diffuse", 0))

    are.grass_emissive = Color.from_rgb_integer(root.acquire("Grass_Emissive", 0))
    are.dirty_argb_1 = Color.from_rgb_integer(root.acquire("DirtyARGBOne", 0))
    are.dirty_argb_2 = Color.from_rgb_integer(root.acquire("DirtyARGBTwo", 0))
    are.dirty_argb_3 = Color.from_rgb_integer(root.acquire("DirtyARGBThree", 0))

    rooms_list = root.acquire("Rooms", GFFList())
    for room_struct in rooms_list:
        ambient_scale = room_struct.acquire("AmbientScale", 0.0)
        env_audio = room_struct.acquire("EnvAudio", 0)
        room_name = room_struct.acquire("RoomName", "")
        disable_weather = bool(room_struct.acquire("DisableWeather", 0))
        force_rating = room_struct.acquire("ForceRating", 0)
        are.rooms.append(ARERoom(room_name, disable_weather, env_audio, force_rating, ambient_scale))

    return are


def dismantle_are(
    are: ARE,
    game: Game = Game.K2,
    *,
    use_deprecated: bool = True,
) -> GFF:
    """Converts an ARE structure to a GFF structure.

    Args:
    ----
        are: ARE - The ARE structure to convert
        game: Game - The game type (K1, K2, etc)
        use_deprecated: bool - Whether to include deprecated fields

    Returns:
    -------
        gff: GFF - The converted GFF structure

    Processing Logic:
    ----------------
        - Creates a new GFF structure
        - Maps ARE fields to GFF fields
        - Includes additional K2-specific fields if game is K2
        - Includes deprecated fields if use_deprecated is True
        - Returns the populated GFF structure.
    """
    gff = GFF(GFFContent.ARE)

    root = gff.root

    map_struct = root.set_struct("Map", GFFStruct(are.map_original_struct_id))
    map_struct.set_int32("MapZoom", are.map_zoom)
    map_struct.set_int32("MapResX", are.map_res_x)
    map_struct.set_int32("NorthAxis", are.north_axis.value)
    map_struct.set_single("MapPt1X", are.map_point_1.x)
    map_struct.set_single("MapPt1Y", are.map_point_1.y)
    map_struct.set_single("MapPt2X", are.map_point_2.x)
    map_struct.set_single("MapPt2Y", are.map_point_2.y)
    map_struct.set_single("WorldPt1X", are.world_point_1.x)
    map_struct.set_single("WorldPt1Y", are.world_point_1.y)
    map_struct.set_single("WorldPt2X", are.world_point_2.x)
    map_struct.set_single("WorldPt2Y", are.world_point_2.y)

    root.set_uint32("Version", are.version)

    root.set_uint32("SunAmbientColor", are.sun_ambient.rgb_integer())
    root.set_uint32("SunDiffuseColor", are.sun_diffuse.rgb_integer())
    root.set_uint32("DynAmbientColor", are.dynamic_light.rgb_integer())
    root.set_uint32("SunFogColor", are.fog_color.rgb_integer())
    root.set_uint32("Grass_Ambient", are.grass_ambient.rgb_integer())
    root.set_uint32("Grass_Diffuse", are.grass_diffuse.rgb_integer())

    root.set_string("Tag", are.tag)
    root.set_locstring("Name", are.name)
    root.set_string("Comments", are.comment)
    root.set_single("AlphaTest", are.alpha_test)
    root.set_int32("CameraStyle", are.camera_style)
    root.set_resref("DefaultEnvMap", are.default_envmap)
    root.set_resref("Grass_TexName", are.grass_texture)
    root.set_single("Grass_Density", are.grass_density)
    root.set_single("Grass_QuadSize", are.grass_size)
    root.set_single("Grass_Prob_LL", are.grass_prob_ll)
    root.set_single("Grass_Prob_LR", are.grass_prob_lr)
    root.set_single("Grass_Prob_UL", are.grass_prob_ul)
    root.set_single("Grass_Prob_UR", are.grass_prob_ur)
    root.set_uint8("SunFogOn", are.fog_enabled)
    root.set_single("SunFogNear", are.fog_near)
    root.set_single("SunFogFar", are.fog_far)
    root.set_uint8("SunShadows", are.shadows)
    root.set_uint8("ShadowOpacity", are.shadow_opacity)
    root.set_int32("WindPower", are.wind_power.value)
    root.set_uint8("Unescapable", are.unescapable)
    root.set_uint8("DisableTransit", are.disable_transit)
    root.set_uint8("StealthXPEnabled", are.stealth_xp)
    root.set_uint32("StealthXPLoss", are.stealth_xp_loss)
    root.set_uint32("StealthXPMax", are.stealth_xp_max)
    root.set_resref("OnEnter", are.on_enter)
    root.set_resref("OnExit", are.on_exit)
    root.set_resref("OnHeartbeat", are.on_heartbeat)
    root.set_resref("OnUserDefined", are.on_user_defined)

    rooms_list = root.set_list("Rooms", GFFList())
    for room in are.rooms:
        room_struct = rooms_list.add(0)
        room_struct.set_single("AmbientScale", room.ambient_scale)
        room_struct.set_int32("EnvAudio", room.env_audio)
        room_struct.set_string("RoomName", room.name)
        if game.is_k2():
            room_struct.set_uint8("DisableWeather", room.weather)
            room_struct.set_int32("ForceRating", room.force_rating)

    if game.is_k2():
        root.set_int32("DirtyARGBOne", are.dirty_argb_1.rgb_integer())
        root.set_int32("DirtyARGBTwo", are.dirty_argb_2.rgb_integer())
        root.set_int32("DirtyARGBThree", are.dirty_argb_3.rgb_integer())
        root.set_uint32("Grass_Emissive", are.grass_emissive.rgb_integer())

        root.set_int32("ChanceRain", are.chance_rain)
        root.set_int32("ChanceSnow", are.chance_snow)
        root.set_int32("ChanceLightning", are.chance_lightning)
        root.set_int32("DirtySizeOne", are.dirty_size_1)
        root.set_int32("DirtyFormulaOne", are.dirty_formula_1)
        root.set_int32("DirtyFuncOne", are.dirty_func_1)
        root.set_int32("DirtySizeTwo", are.dirty_size_2)
        root.set_int32("DirtyFormulaTwo", are.dirty_formula_2)
        root.set_int32("DirtyFuncTwo", are.dirty_func_2)
        root.set_int32("DirtySizeThree", are.dirty_size_3)
        root.set_int32("DirtyFormulaThre", are.dirty_formula_3)
        root.set_int32("DirtyFuncThree", are.dirty_func_3)

    if use_deprecated:
        root.set_int32("ID", are.unused_id)
        root.set_int32("Creator_ID", are.creator_id)
        root.set_uint32("Flags", are.flags)
        root.set_int32("ModSpotCheck", are.mod_spot_check)
        root.set_int32("ModListenCheck", are.mod_listen_check)
        root.set_uint32("MoonAmbientColor", are.moon_ambient)
        root.set_uint32("MoonDiffuseColor", are.moon_diffuse)
        root.set_uint8("MoonFogOn", are.moon_fog)
        root.set_single("MoonFogNear", are.moon_fog_near)
        root.set_single("MoonFogFar", are.moon_fog_far)
        root.set_uint32("MoonFogColor", are.moon_fog_color)
        root.set_uint8("MoonShadows", are.moon_shadows)
        root.set_uint8("IsNight", are.is_night)
        root.set_uint8("LightingScheme", are.lighting_scheme)
        root.set_uint8("DayNightCycle", are.day_night)
        root.set_uint16("LoadScreenID", are.loadscreen_id)
        root.set_uint8("NoRest", are.no_rest)
        root.set_uint8("NoHangBack", are.no_hang_back)
        root.set_uint8("PlayerOnly", are.player_only)
        root.set_uint8("PlayerVsPlayer", are.player_vs_player)
        root.set_list("Expansion_List", GFFList())

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
