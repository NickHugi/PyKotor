from __future__ import annotations

from pykotor.common.language import LocalizedString
from pykotor.common.misc import Game, ResRef
from pykotor.resource.formats.gff import GFF, GFFContent, GFFList, read_gff, write_gff
from pykotor.resource.formats.gff.gff_auto import bytes_gff
from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES, ResourceType


class UTS:
    """
    Stores sound data.

    Attributes
    ----------
        tag: "Tag" field.
        resref: "TemplateResRef" field.
        active: "Active" field.
        continuous: "Continuous" field.
        looping: "Looping" field.
        positional: "Positional" field.
        random_position: "RandomPosition" field.
        random_pick: "Random" field.
        elevation: "Elevation" field.
        max_distance: "MaxDistance" field.
        min_distance: "MinDistance" field.
        random_range_x: "RandomRangeX" field.
        random_range_y: "RandomRangeY" field.
        interval: "Interval" field.
        interval_variation: "IntervalVrtn" field.
        pitch_variation: "PitchVariation" field.
        priority: "Priority" field.
        volume: "Volume" field.
        volume_variation: "VolumeVrtn" field.
        comment: "Comment" field.

        palette_id: "PaletteID" field. Used in toolset only.

        name: "LocName" field. Not used by the game engine.
        hours: "Hours" field. Not used by the game engine.
        times: "Times" field. Not used by the game engine.
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

    root = gff.root
    uts.tag = root.acquire("Tag", "")
    uts.resref = root.acquire("TemplateResRef", ResRef.from_blank())
    uts.active = root.acquire("Active", 0)
    uts.continuous = root.acquire("Continuous", 0)
    uts.looping = root.acquire("Looping", 0)
    uts.positional = root.acquire("Positional", 0)
    uts.random_position = root.acquire("RandomPosition", 0)
    uts.random_pick = root.acquire("Random", 0)
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
    game: Game = Game.K2,
    *,
    use_deprecated: bool = True,
) -> GFF:
    gff = GFF(GFFContent.UTS)

    root = gff.root
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
        root.set_uint32("Times", uts.times)

    return gff


def read_uts(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
) -> UTS:
    gff = read_gff(source, offset, size)
    return construct_uts(gff)


def write_uts(
    uts: UTS,
    target: TARGET_TYPES,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
) -> None:
    gff = dismantle_uts(uts, game, use_deprecated=use_deprecated)
    write_gff(gff, target, file_format)


def bytes_uts(
    uts: UTS,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
) -> bytes:
    gff = dismantle_uts(uts, game, use_deprecated=use_deprecated)
    return bytes_gff(gff, file_format)
