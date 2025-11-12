from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.language import LocalizedString
from pykotor.common.misc import Game, ResRef
from pykotor.resource.formats.gff import GFF, GFFContent, GFFList, read_gff, write_gff
from pykotor.resource.formats.gff.gff_auto import bytes_gff
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFFStruct
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class UTS:
    """Stores sound data.

    UTS files are GFF-based format files that store sound object definitions including
    audio settings, positioning, looping, and volume controls.

    References:
    ----------
        vendor/reone/src/libs/resource/parser/gff/uts.cpp:34-64 (UTS parsing from GFF)
        vendor/reone/include/reone/resource/parser/gff/uts.h:32-58 (UTS structure definitions)
        vendor/Kotor.NET/Kotor.NET/Resources/KotorUTS/UTS.cs:11-38 (UTS class definition)
        Note: UTS files are GFF format files with specific structure definitions

    Attributes:
    ----------
        resref: "TemplateResRef" field. The resource reference for this sound template.
            Reference: reone/uts.cpp:59 (TemplateResRef field)
            Reference: reone/uts.h:54 (TemplateResRef field)
            Reference: Kotor.NET/UTS.cs:15 (TemplateResRef property)

        tag: "Tag" field. Tag identifier for this sound.
            Reference: reone/uts.cpp:58 (Tag field)
            Reference: reone/uts.h:53 (Tag field)
            Reference: Kotor.NET/UTS.cs:13 (Tag property)

        active: "Active" field. Whether sound is active.
            Reference: reone/uts.cpp:36 (Active field)
            Reference: reone/uts.h:33 (Active field)
            Reference: Kotor.NET/UTS.cs:16 (Active property)

        continuous: "Continuous" field. Whether sound plays continuously.
            Reference: reone/uts.cpp:38 (Continuous field)
            Reference: reone/uts.h:35 (Continuous field)
            Reference: Kotor.NET/UTS.cs:17 (Continuous property)

        looping: "Looping" field. Whether sound loops.
            Reference: reone/uts.cpp:44 (Looping field)
            Reference: reone/uts.h:41 (Looping field)
            Reference: Kotor.NET/UTS.cs:18 (Looping property)

        positional: "Positional" field. Whether sound is positional (3D).
            Reference: reone/uts.cpp:49 (Positional field)
            Reference: reone/uts.h:46 (Positional field)
            Reference: Kotor.NET/UTS.cs:19 (Positional property)

        random_position: "RandomPosition" field. Whether sound position is randomized.
            Reference: reone/uts.cpp:52 (RandomPosition field)
            Reference: reone/uts.h:49 (RandomPosition field)
            Reference: Kotor.NET/UTS.cs:20 (RandomPosition property)

        random_pick: "Random" field. Whether sound is randomly selected from list.
            Reference: reone/uts.cpp:51 (Random field)
            Reference: reone/uts.h:48 (Random field)
            Reference: Kotor.NET/UTS.cs:21 (Random property)

        elevation: "Elevation" field. Elevation offset for positional sounds.
            Reference: reone/uts.cpp:39 (Elevation field)
            Reference: reone/uts.h:36 (Elevation field)
            Reference: Kotor.NET/UTS.cs:22 (Elevation property)

        max_distance: "MaxDistance" field. Maximum distance for positional sounds.
            Reference: reone/uts.cpp:45 (MaxDistance field)
            Reference: reone/uts.h:42 (MaxDistance field)
            Reference: Kotor.NET/UTS.cs:23 (MaxDistance property)

        min_distance: "MinDistance" field. Minimum distance for positional sounds.
            Reference: reone/uts.cpp:46 (MinDistance field)
            Reference: reone/uts.h:43 (MinDistance field)
            Reference: Kotor.NET/UTS.cs:24 (MinDistance property)

        random_range_x: "RandomRangeX" field. X-axis range for random positioning.
            Reference: reone/uts.cpp:53 (RandomRangeX field)
            Reference: reone/uts.h:50 (RandomRangeX field)
            Reference: Kotor.NET/UTS.cs:25 (RandomRangeX property)

        random_range_y: "RandomRangeY" field. Y-axis range for random positioning.
            Reference: reone/uts.cpp:54 (RandomRangeY field)
            Reference: reone/uts.h:51 (RandomRangeY field)
            Reference: Kotor.NET/UTS.cs:26 (RandomRangeY property)

        interval: "Interval" field. Time interval between sound plays (in seconds).
            Reference: reone/uts.cpp:41 (Interval field)
            Reference: reone/uts.h:38 (Interval field)
            Reference: Kotor.NET/UTS.cs:27 (Interval property)

        interval_variation: "IntervalVrtn" field. Variation in interval timing.
            Reference: reone/uts.cpp:42 (IntervalVrtn field)
            Reference: reone/uts.h:39 (IntervalVrtn field)
            Reference: Kotor.NET/UTS.cs:28 (IntervalVrtn property)

        pitch_variation: "PitchVariation" field. Pitch variation amount.
            Reference: reone/uts.cpp:48 (PitchVariation field)
            Reference: reone/uts.h:45 (PitchVariation field)
            Reference: Kotor.NET/UTS.cs:29 (PitchVariation property)

        priority: "Priority" field. Sound priority level.
            Reference: reone/uts.cpp:50 (Priority field)
            Reference: reone/uts.h:47 (Priority field)
            Reference: Kotor.NET/UTS.cs:30 (Priority property)

        volume: "Volume" field. Volume level (0-255).
            Reference: reone/uts.cpp:61 (Volume field)
            Reference: reone/uts.h:56 (Volume field)
            Reference: Kotor.NET/UTS.cs:33 (Volume property)

        volume_variation: "VolumeVrtn" field. Volume variation amount.
            Reference: reone/uts.cpp:62 (VolumeVrtn field)
            Reference: reone/uts.h:57 (VolumeVrtn field)
            Reference: Kotor.NET/UTS.cs:34 (VolumeVrtn property)

        sounds: List of ResRef objects representing sound files to play.
            Reference: reone/uts.cpp:55-57 (Sounds list parsing)
            Reference: reone/uts.h:52 (Sounds vector)
            Reference: reone/uts.h:28-30 (UTS_Sounds struct)
            Reference: Kotor.NET/UTS.cs:35 (Sounds property)

        comment: "Comment" field. Developer comment.
            Reference: reone/uts.cpp:37 (Comment field)
            Reference: reone/uts.h:34 (Comment field)
            Reference: Kotor.NET/UTS.cs:37 (Comment property)

        palette_id: "PaletteID" field. Palette identifier. Used in toolset only.
            Reference: reone/uts.cpp:47 (PaletteID field)
            Reference: reone/uts.h:44 (PaletteID field)
            Reference: Kotor.NET/UTS.cs:36 (PaletteID property)

        name: "LocName" field. Localized name. Not used by the game engine.
            Reference: reone/uts.cpp:43 (LocName field)
            Reference: reone/uts.h:40 (LocName field)
            Reference: Kotor.NET/UTS.cs:14 (LocName property)

        hours: "Hours" field. Hour restriction. Not used by the game engine.
            Reference: reone/uts.cpp:40 (Hours field)
            Reference: reone/uts.h:37 (Hours field)
            Reference: Kotor.NET/UTS.cs:31 (Hours property)

        times: "Times" field. Time restriction. Not used by the game engine.
            Reference: reone/uts.cpp:60 (Times field)
            Reference: reone/uts.h:55 (Times field)
            Reference: Kotor.NET/UTS.cs:32 (Times property)
            Note: PyKotor comment notes some files have this as uint8, others as uint32
    """

    BINARY_TYPE = ResourceType.UTS

    def __init__(
        self,
    ):
        self.resref: ResRef = ResRef.from_blank()
        self.tag: str = ""
        self.comment: str = ""

        self.active: bool = False
        self.continuous: bool = False
        self.looping: bool = False
        self.positional: bool = False
        self.random_pick: bool = False

        self.random_position: bool = False
        self.random_range_x: float = 0.0
        self.random_range_y: float = 0.0

        self.elevation: float = 0.0
        self.max_distance: float = 0.0
        self.min_distance: float = 0.0

        self.priority: int = 0

        self.interval: int = 0
        self.interval_variation: int = 0
        self.pitch_variation: float = 0.0
        self.volume: int = 0
        self.volume_variation: int = 0

        self.sounds: list[ResRef] = []

        # Deprecated:
        self.name: LocalizedString = LocalizedString.from_invalid()
        self.times: int = 0
        self.hours: int = 0
        self.palette_id: int = 0


def construct_uts(
    gff: GFF,
) -> UTS:
    uts = UTS()

    root: GFFStruct = gff.root
    uts.tag = root.acquire("Tag", "")
    uts.resref = root.acquire("TemplateResRef", ResRef.from_blank())
    uts.active = bool(root.acquire("Active", 0))
    uts.continuous = bool(root.acquire("Continuous", 0))
    uts.looping = bool(root.acquire("Looping", 0))
    uts.positional = bool(root.acquire("Positional", 0))
    uts.random_position = bool(root.acquire("RandomPosition", 0))
    uts.random_pick = bool(root.acquire("Random", 0))
    uts.elevation = root.acquire("Elevation", 0.0)
    uts.max_distance = root.acquire("MaxDistance", 0.0)
    uts.min_distance = root.acquire("MinDistance", 0.0)
    uts.random_range_x = root.acquire("RandomRangeX", 0.0)
    uts.random_range_y = root.acquire("RandomRangeY", 0.0)
    uts.interval = root.acquire("Interval", 0)
    uts.interval_variation = root.acquire("IntervalVrtn", 0)
    uts.pitch_variation = root.acquire("PitchVariation", 0.0)
    uts.priority = root.acquire("Priority", 0)
    uts.volume = root.acquire("Volume", 0)
    uts.volume_variation = root.acquire("VolumeVrtn", 0)
    uts.comment = root.acquire("Comment", "")
    uts.name = root.acquire("LocName", LocalizedString.from_invalid())
    uts.hours = root.acquire("Hours", 0)
    uts.times = root.acquire("Times", 0)
    uts.palette_id = root.acquire("PaletteID", 0)

    for sound_struct in root.acquire("Sounds", GFFList()):
        sound = sound_struct.acquire("Sound", ResRef.from_blank())
        uts.sounds.append(sound)

    return uts


def dismantle_uts(
    uts: UTS,
    game: Game = Game.K2,  # noqa: ARG001
    *,
    use_deprecated: bool = True,
) -> GFF:
    gff = GFF(GFFContent.UTS)

    root: GFFStruct = gff.root
    root.set_string("Tag", uts.tag)
    root.set_resref("TemplateResRef", uts.resref)
    root.set_uint8("Active", uts.active)
    root.set_uint8("Continuous", uts.continuous)
    root.set_uint8("Looping", uts.looping)
    root.set_uint8("Positional", uts.positional)
    root.set_uint8("RandomPosition", uts.random_position)
    root.set_uint8("Random", uts.random_pick)
    root.set_single("Elevation", uts.elevation)
    root.set_single("MaxDistance", uts.max_distance)
    root.set_single("MinDistance", uts.min_distance)
    root.set_single("RandomRangeX", uts.random_range_x)
    root.set_single("RandomRangeY", uts.random_range_y)
    root.set_uint32("Interval", uts.interval)
    root.set_uint32("IntervalVrtn", uts.interval_variation)
    root.set_single("PitchVariation", uts.pitch_variation)
    root.set_uint8("Priority", uts.priority)
    root.set_uint8("Volume", uts.volume)
    root.set_uint8("VolumeVrtn", uts.volume_variation)
    root.set_string("Comment", uts.comment)

    sound_list = root.set_list("Sounds", GFFList())
    for sound in uts.sounds:
        sound_list.add(0).set_resref("Sound", sound)

    root.set_uint8("PaletteID", uts.palette_id)

    if use_deprecated:
        root.set_locstring("LocName", uts.name)
        root.set_uint32("Hours", uts.hours)
        root.set_uint8("Times", uts.times)  # TODO(th3w1zard1): double check this. Some files have this field as uint8 others as uint32?

    return gff


def read_uts(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
) -> UTS:
    gff: GFF = read_gff(source, offset, size)
    return construct_uts(gff)


def write_uts(
    uts: UTS,
    target: TARGET_TYPES,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
):
    gff: GFF = dismantle_uts(uts, game, use_deprecated=use_deprecated)
    write_gff(gff, target, file_format)


def bytes_uts(
    uts: UTS,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
) -> bytes:
    gff: GFF = dismantle_uts(uts, game, use_deprecated=use_deprecated)
    return bytes_gff(gff, file_format)
