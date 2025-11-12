from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

from pykotor.common.language import LocalizedString
from pykotor.common.misc import Game
from pykotor.resource.formats.gff import GFF, GFFContent, GFFList, read_gff, write_gff
from pykotor.resource.formats.gff.gff_auto import bytes_gff
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class JRL:
    """Stores journal (quest) data.
    
    JRL files are GFF-based format files that store journal/quest data including
    quest entries, priorities, and planet associations.
    
    References:
    ----------
        vendor/reone/src/libs/resource/format/gffreader.cpp (GFF reading, JRL is GFF-based)
        vendor/xoreos-tools/src/xml/jrldumper.cpp (JRL to XML conversion, if exists)
        Note: JRL files are GFF format files with specific structure definitions
    """

    BINARY_TYPE = ResourceType.JRL

    def __init__(
        self,
    ):
        self.quests: list[JRLQuest] = []


class JRLQuest:
    """Stores data of an individual quest.

    Attributes:
    ----------
        name: "Name" field.
        planet_id: "PlanetID" field.
        plot_index: "PlotIndex" field.
        priority: "Priority" field.
        tag: "Tag" field.

        comment: "Comment" field. Used in toolset only.
    """

    def __init__(
        self,
    ):
        self.comment: str = ""
        self.name: LocalizedString = LocalizedString.from_invalid()
        self.planet_id: int = 0
        self.plot_index: int = 0  # plot.2da
        self.priority: JRLQuestPriority = JRLQuestPriority.LOWEST
        self.tag: str = ""
        self.entries: list[JRLEntry] = []


class JRLEntry:
    """Stores the data for an entry in a quest.

    Attributes:
    ----------
        end: "End" field.
        entry_id: "ID" field.
        text: "Text" field.
        xp_percentage: "XP_Percentage" field.
    """

    def __init__(
        self,
    ):
        self.end: bool = False
        self.entry_id: int = 0
        self.text: LocalizedString = LocalizedString.from_invalid()
        self.xp_percentage: float = 0.0


class JRLQuestPriority(IntEnum):
    HIGHEST = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    LOWEST = 4


def construct_jrl(gff: GFF) -> JRL:
    jrl = JRL()

    for category_struct in gff.root.acquire("Categories", GFFList()):
        quest = JRLQuest()
        jrl.quests.append(quest)
        quest.comment = category_struct.acquire("Comment", "")
        quest.name = category_struct.acquire("Name", LocalizedString.from_invalid())
        quest.planet_id = category_struct.acquire("PlanetID", 0)
        quest.plot_index = category_struct.acquire("PlotIndex", 0)
        quest.priority = JRLQuestPriority(category_struct.acquire("Priority", 0))
        quest.tag = category_struct.acquire("Tag", "")

        for entry_struct in category_struct.acquire("EntryList", GFFList()):
            entry = JRLEntry()
            quest.entries.append(entry)
            entry.end = bool(entry_struct.acquire("End", 0))
            entry.entry_id = entry_struct.acquire("ID", 0)
            entry.text = entry_struct.acquire("Text", LocalizedString.from_invalid())
            entry.xp_percentage = entry_struct.acquire("XP_Percentage", 0.0)

    return jrl


def dismantle_jrl(  # TODO: store original list indices and sort.
    jrl: JRL,
    game: Game = Game.K2,
    *,
    use_deprecated: bool = True,
) -> GFF:
    gff = GFF(GFFContent.JRL)

    category_list: GFFList = gff.root.set_list("Categories", GFFList())
    for i, quest in enumerate(jrl.quests):
        category_struct = category_list.add(i)
        category_struct.set_string("Comment", quest.comment)
        category_struct.set_locstring("Name", quest.name)
        category_struct.set_int32("PlanetID", quest.planet_id)
        category_struct.set_int32("PlotIndex", quest.plot_index)
        category_struct.set_uint32("Priority", quest.priority.value)
        category_struct.set_string("Tag", quest.tag)

        entry_list: GFFList = category_struct.set_list("EntryList", GFFList())
        for j, entry in enumerate(quest.entries):
            entry_struct = entry_list.add(j)
            entry_struct.set_uint16("End", entry.end)
            entry_struct.set_uint32("ID", entry.entry_id)
            entry_struct.set_locstring("Text", entry.text)
            entry_struct.set_single("XP_Percentage", entry.xp_percentage)

    return gff


def read_jrl(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
) -> JRL:
    gff: GFF = read_gff(source, offset, size)
    return construct_jrl(gff)


def write_jrl(
    jrl: JRL,
    target: TARGET_TYPES,
    file_format: ResourceType = ResourceType.GFF,
    game: Game = Game.K2,
):
    gff: GFF = dismantle_jrl(jrl, game)
    write_gff(gff, target, file_format)


def bytes_jrl(
    jrl: JRL,
    file_format: ResourceType = ResourceType.GFF,
) -> bytes:
    gff: GFF = dismantle_jrl(jrl)
    return bytes_gff(gff, file_format)
