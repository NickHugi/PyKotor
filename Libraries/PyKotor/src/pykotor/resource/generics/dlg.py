from __future__ import annotations

from copy import deepcopy
from enum import IntEnum
from typing import TYPE_CHECKING, ClassVar, TypedDict

from pykotor.common.geometry import Vector3
from pykotor.common.language import Gender, Language, LocalizedString
from pykotor.common.misc import Color, Game
from pykotor.resource.formats.gff import GFF, GFFContent, GFFList, read_gff, write_gff
from pykotor.resource.formats.gff.gff_auto import bytes_gff
from pykotor.resource.formats.gff.gff_data import FieldProperty, GFFFieldType, GFFStruct, GFFStructInterface  # noqa: PLC2701
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.common.misc import ResRef
    from pykotor.resource.formats.gff.gff_data import FieldGFF
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class DLGComputerType(IntEnum):
    Modern = 0
    Ancient = 1


class DLGConversationType(IntEnum):
    Human = 0
    Computer = 1
    Other = 2


class DLGFields(TypedDict):
    EntryList: FieldGFF[GFFList[DLGEntry]]
    ReplyList: FieldGFF[GFFList[DLGReply]]
    StartingList: FieldGFF[GFFList[DLGLink]]
    StuntList: FieldGFF[GFFList[DLGStunt]]

    AmbientTrack: FieldGFF[ResRef]
    AnimatedCut: FieldGFF[int]
    CameraModel: FieldGFF[ResRef]
    ComputerType: FieldGFF[int]
    ConversationType: FieldGFF[int]
    EndConverAbort: FieldGFF[ResRef]
    EndConversation: FieldGFF[ResRef]
    NumWords: FieldGFF[int]
    OldHitCheck: FieldGFF[int]
    Skippable: FieldGFF[int]
    UnequipItems: FieldGFF[int]
    UnequipHItem: FieldGFF[int]
    VO_ID: FieldGFF[str]

    # KotOR 2:
    AlienRaceOwner: FieldGFF[int]
    NextNodeID: FieldGFF[int]
    PostProcOwner: FieldGFF[int]
    RecordNoVO: FieldGFF[int]

    # Deprecated:
    DelayEntry: FieldGFF[int]
    DelayReply: FieldGFF[int]
class DLG(GFFStructInterface):
    """Stores dialog data."""

    BINARY_TYPE = ResourceType.DLG

    ambient_track: FieldProperty[ResRef, ResRef] = FieldProperty("AmbientTrack", GFFFieldType.ResRef)
    animated_cut = FieldProperty("AnimatedCut", GFFFieldType.UInt8)
    camera_model: FieldProperty[ResRef, ResRef] = FieldProperty("CameraModel", GFFFieldType.ResRef)
    computer_type = FieldProperty("ComputerType", GFFFieldType.UInt8, return_type=DLGComputerType)
    conversation_type = FieldProperty("ConversationType", GFFFieldType.Int32, return_type=DLGConversationType)
    on_abort: FieldProperty[ResRef, ResRef] = FieldProperty("EndConverAbort", GFFFieldType.ResRef)
    on_end: FieldProperty[ResRef, ResRef] = FieldProperty("EndConversation", GFFFieldType.ResRef)
    skippable: FieldProperty[int, bool] = FieldProperty("Skippable", GFFFieldType.UInt8, return_type=bool)

    entries: FieldProperty[GFFList[GFFStruct], GFFList[DLGEntry]] = FieldProperty("EntryList", GFFFieldType.List, GFFList())
    replies: FieldProperty[GFFList[GFFStruct], GFFList[DLGReply]] = FieldProperty("ReplyList", GFFFieldType.List, GFFList())
    stunts: FieldProperty[GFFList[DLGStunt], GFFList[GFFStruct]] = FieldProperty("StuntList", GFFFieldType.List, GFFList())
    starters: FieldProperty[GFFList[DLGLink], GFFList[GFFStruct]] = FieldProperty("StartingList", GFFFieldType.List, GFFList())

    word_count: FieldProperty[int, int] = FieldProperty("NumWords", GFFFieldType.UInt32)
    old_hit_check: FieldProperty[int, bool] = FieldProperty("OldHitCheck", GFFFieldType.UInt8, return_type=bool)
    unequip_hands: FieldProperty[int, bool] = FieldProperty("UnequipHItem", GFFFieldType.UInt8, return_type=bool)
    unequip_items: FieldProperty[int, bool] = FieldProperty("UnequipItems", GFFFieldType.UInt8, return_type=bool)
    vo_id: FieldProperty[str, str] = FieldProperty("VO_ID", GFFFieldType.String, "")

    # KotOR 2 TSL Only.
    alien_race_owner: FieldProperty[int, int] = FieldProperty("AlienRaceOwner", GFFFieldType.Int32, game=Game.K2)
    next_node_id: FieldProperty[int, int] = FieldProperty("NextNodeID", GFFFieldType.Int32, game=Game.K2)
    post_proc_owner: FieldProperty[int, int] = FieldProperty("PostProcOwner", GFFFieldType.Int32, game=Game.K2)
    record_no_vo: FieldProperty[int, int] = FieldProperty("RecordNoVO", GFFFieldType.Int32, game=Game.K2)

    # Deprecated. Not used by either game engine
    delay_entry: FieldProperty[int, int] = FieldProperty("DelayEntry", GFFFieldType.UInt32)
    delay_reply: FieldProperty[int, int] = FieldProperty("DelayReply", GFFFieldType.UInt32)  # Not used by game engine

    def __init__(
        self,
    ):
        """Initializes a Conversation dialog (DLG) object that wraps the gff root struct.

        Processing Logic:
        ----------------
            1. Initializes starter and stunt lists
            2. Sets default values for node properties
            3. Adds a blank starter node if blank_node is True
            4. Sets deprecated properties for backwards compatibility.
        """
        super().__init__()
        self._fields: DLGFields

    def init_tree(self):
        if not self.starters:
            # Add bare minimum to be openable by DLGEditor
            starter = DLGLink()
            starter._node = DLGEntry()
            starter._node.text.set_data(Language.ENGLISH, Gender.MALE, "")
            self.starters.append(starter)
            return

    def print_tree(
        self,
    ):
        """Prints all the nodes (one per line) in the dialog tree with appropriate indentation."""
        self._print_tree(self.starters, 0, [], [])

    def _print_tree(
        self,
        links: list[DLGLink],
        indent: int,
        seen_links: list[DLGLink],
        seen_nodes: list[DLGNode],
    ):
        for link in links:
            if link._node in seen_nodes:
                continue

            print(f'{" " * indent}-> {link._node.text}')
            seen_links.append(link)

            if link._node in seen_nodes:
                print(f'{" " * indent}-> [LINK] {link._node.text}')
                continue

            seen_nodes.append(link._node)
            self._print_tree(
                link._node.links,  # type: ignore[attribute]
                indent + 3,
                seen_links,
                seen_nodes,
            )

    def all_entries(
        self,
    ) -> list[DLGEntry]:
        """Returns a flat list of all entries in the dialog.

        Returns:
        -------
            A list of all stored entries.
        """
        return self._all_entries()

    def _all_entries(
        self,
        links: list[DLGLink] | None = None,
        seen_entries: set | None = None,
    ) -> list[DLGEntry]:
        """Collect all entries reachable from the given links.

        Args:
        ----
            links: {List of starting DLGLinks}
            seen_entries: {set of entries already processed}

        Returns:
        -------
            entries: {List of all reachable DLGEntries}

        Processing Logic:
        ----------------
            - The function recursively traverses the graph of DLGLinks starting from the given links
            - It collects all unique DLGEntries in a list
            - Seen entries are tracked to avoid processing the same entry multiple times
            - Child entries are recursively processed by calling the function again
        """
        entries: list[DLGEntry] = []

        starting_links: list[DLGLink] = self.starters if links is None else links
        seen_entries = set() if seen_entries is None else seen_entries

        for link in starting_links:
            entry = link._node
            assert isinstance(entry, DLGEntry), f"Expected DLGEntry instance, instead was '{entry.__class__.__name__}'"
            if id(entry) in seen_entries:
                continue

            entries.append(entry)
            seen_entries.add(id(entry))
            for reply_link in entry.links:
                reply = reply_link._node
                assert isinstance(reply, DLGReply), f"Expected DLGReply instance, instead was '{entry.__class__.__name__}'"
                entries.extend(self._all_entries(reply.links, seen_entries))

        return entries

    def all_replies(
        self,
    ) -> list[DLGReply]:
        """Returns a flat list of all replies in the dialog.

        Returns:
        -------
            A list of all stored replies.
        """
        return self._all_replies()

    def _all_replies(
        self,
        links: list[DLGLink] | None = None,
        seen_replies: set | None = None,
    ) -> list[DLGReply]:
        """Collect all replies reachable from the given links.

        Args:
        ----
            links: list[DLGLink] | None = None: The starting links to traverse
            seen_replies: list | None = None: Replies already seen

        Returns:
        -------
            replies: list[DLGReply]: All reachable replies

        Processing Logic:
        ----------------
            - If no links given, use starters as starting links
            - Initialize seen_replies if not given
            - Iterate over links and add node to replies if not seen
            - Mark node as seen and recurse on its links
            - Extend replies with results of recursion.
        """
        replies: list[DLGReply] = []

        starting_links: list[DLGLink] = links if links is not None else [
            _ for link in self.starters
            for _ in link._node.links  # type: ignore
        ]
        seen_replies = set() if seen_replies is None else seen_replies

        for link in starting_links:
            reply: DLGNode = link._node
            assert isinstance(reply, DLGReply)
            if id(reply) in seen_replies:
                continue
            replies.append(reply)
            seen_replies.add(id(reply))
            for entry_link in reply.links:
                entry: DLGNode = entry_link._node
                assert isinstance(entry, DLGEntry)
                replies.extend(self._all_replies(entry.links, seen_replies))

        return replies


class DLGNodeFields(TypedDict):
    Comment: FieldGFF[str]
    AnimList: FieldGFF[GFFList[DLGAnimation]]

    Script: FieldGFF[ResRef]
    Delay: FieldGFF[int]
    SoundExists: FieldGFF[int]
    Text: FieldGFF[LocalizedString]
    Listener: FieldGFF[str]
    VO_ResRef: FieldGFF[ResRef]
    PlotXPPercentage: FieldGFF[float]
    WaitFlags: FieldGFF[int]
    CameraAngle: FieldGFF[int]
    FadeType: FieldGFF[int]
    Sound: FieldGFF[ResRef]
    Quest: FieldGFF[str]
    PlotIndex: FieldGFF[int]

    QuestEntry: FieldGFF[int]
    FadeColor: FieldGFF[Vector3]
    FadeDelay: FieldGFF[float]
    FadeLength: FieldGFF[float]
    CameraAnimation: FieldGFF[int]
    CameraID: FieldGFF[int]
    CamFieldOfView: FieldGFF[float]
    CamHeightOffset: FieldGFF[float]
    CamVidEffect: FieldGFF[int]
    TarHeightOffset: FieldGFF[float]

    # KotOR 2:
    NodeID: FieldGFF[int]
    NextNodeID: FieldGFF[int]
    ActionParam1: FieldGFF[int]
    ActionParam2: FieldGFF[int]
    ActionParam3: FieldGFF[int]
    ActionParam4: FieldGFF[int]
    ActionParam5: FieldGFF[int]
    ActionParamStrA: FieldGFF[str]

    Script2: FieldGFF[ResRef]
    ActionParam1b: FieldGFF[int]
    ActionParam2b: FieldGFF[int]
    ActionParam3b: FieldGFF[int]
    ActionParam4b: FieldGFF[int]
    ActionParam5b: FieldGFF[int]
    ActionParamStrB: FieldGFF[str]

    AlienRaceNode: FieldGFF[int]
    AlienRaceOwner: FieldGFF[int]
    Emotion: FieldGFF[int]
    FacialAnim: FieldGFF[int]
    NodeUnskippable: FieldGFF[int]
    PostProcNode: FieldGFF[int]

    RecordNoVOOverri: FieldGFF[int]
    RecordNoOverri: FieldGFF[int]
    RecordVO: FieldGFF[int]
    VOTextChanged: FieldGFF[int]
class DLGNode(GFFStructInterface):
    """Represents a node in the dialog tree."""

    links: FieldProperty[GFFList[DLGLink], GFFList[DLGLink]]
    text: FieldProperty[LocalizedString, LocalizedString] = FieldProperty("Text", GFFFieldType.LocalizedString, LocalizedString.from_invalid())
    listener = FieldProperty("Listener", GFFFieldType.String, "")
    vo_resref = FieldProperty("VO_ResRef", GFFFieldType.ResRef)
    script1 = FieldProperty("Script", GFFFieldType.ResRef)
    delay = FieldProperty("Delay", GFFFieldType.UInt32, 0xFFFFFFFF, return_type=lambda x: -1 if x == 0xFFFFFFFF else x)
    comment = FieldProperty("Comment", GFFFieldType.String, "")
    animations = FieldProperty("AnimList", GFFFieldType.List, GFFList())
    sound = FieldProperty("Sound", GFFFieldType.ResRef)
    quest = FieldProperty("Quest", GFFFieldType.String, "")
    plot_index = FieldProperty("PlotIndex", GFFFieldType.Int32)
    plot_xp_percentage = FieldProperty("PlotXPPercentage", GFFFieldType.Single, 0.0)
    wait_flags = FieldProperty("WaitFlags", GFFFieldType.UInt32)
    camera_angle = FieldProperty("CameraAngle", GFFFieldType.UInt32)
    fade_type = FieldProperty("FadeType", GFFFieldType.UInt8)
    sound_exists = FieldProperty("SoundExists", GFFFieldType.UInt8)
    placeholder = FieldProperty("Changed", GFFFieldType.UInt8)  # ???
    quest_entry = FieldProperty("QuestEntry", GFFFieldType.UInt32)
    fade_delay = FieldProperty("FadeDelay", GFFFieldType.Single, 0.0)
    fade_length = FieldProperty("FadeLength", GFFFieldType.Single, 0.0)
    camera_anim = FieldProperty("CameraAnimation", GFFFieldType.UInt16, -1)
    camera_id = FieldProperty("CameraID", GFFFieldType.Int32)
    camera_fov = FieldProperty("CamFieldOfView", GFFFieldType.Single, 0.0)
    camera_height = FieldProperty("CamHeightOffset", GFFFieldType.Single, 0.0)
    camera_effect = FieldProperty("CamVidEffect", GFFFieldType.Int32)
    tar_offset = FieldProperty("TarHeightOffset", GFFFieldType.Single, 0.0)
    fade_color = FieldProperty("FadeColor", GFFFieldType.Vector3, Vector3.from_null(), return_type=Color)
    node_id = FieldProperty("NodeID", GFFFieldType.Int32)
    script1_param1 = FieldProperty("ActionParam1", GFFFieldType.Int32)
    script1_param2 = FieldProperty("ActionParam2", GFFFieldType.Int32)
    script1_param3 = FieldProperty("ActionParam3", GFFFieldType.Int32)
    script1_param4 = FieldProperty("ActionParam4", GFFFieldType.Int32)
    script1_param5 = FieldProperty("ActionParam5", GFFFieldType.Int32)
    script1_param6 = FieldProperty("ActionParamStrA", GFFFieldType.String, "")
    script2 = FieldProperty("Script2", GFFFieldType.ResRef)
    script2_param1 = FieldProperty("ActionParam1b", GFFFieldType.Int32)
    script2_param2 = FieldProperty("ActionParam2b", GFFFieldType.Int32)
    script2_param3 = FieldProperty("ActionParam3b", GFFFieldType.Int32)
    script2_param4 = FieldProperty("ActionParam4b", GFFFieldType.Int32)
    script2_param5 = FieldProperty("ActionParam5b", GFFFieldType.Int32)
    script2_param6 = FieldProperty("ActionParamStrB", GFFFieldType.String, "")
    alien_race_node = FieldProperty("AlienRaceNode", GFFFieldType.Int32)
    facial_id = FieldProperty("FacialAnim", GFFFieldType.Int32)
    emotion_id = FieldProperty("Emotion", GFFFieldType.Int32)
    unskippable = FieldProperty("NodeUnskippable", GFFFieldType.Int32)
    post_proc_node = FieldProperty("PostProcNode", GFFFieldType.Int32)
    record_no_vo_override = FieldProperty("RecordNoVOOverri", GFFFieldType.Int32)
    record_no_vo_override2 = FieldProperty("RecordNoOverri", GFFFieldType.Int32)  # ??? is this or the above the correct one?
    record_vo = FieldProperty("RecordVO", GFFFieldType.Int32)
    vo_text_changed = FieldProperty("VOTextChanged", GFFFieldType.Int32)

    def __init__(
        self,
    ) -> None:
        """Initializes a DLGNode object.

        Processing Logic:
        ----------------
            - Sets default values for all properties of a DLGNode object
            - Initializes lists and optional properties as empty/None
            - Sets flags and identifiers to default values
        """
        super().__init__()
        self._fields: DLGNodeFields
        self.list_index: int = -1
        animation: DLGAnimation
        for animation in self.animations:
            animation.__class__ = DLGAnimation

    def __hash__(self):
        return hash((self.__class__, self.list_index))


class DLGReplyFields(TypedDict):
    EntriesList: FieldGFF[GFFList[DLGLink]]
class DLGReply(DLGNode):
    """Replies are nodes that are responses by the player."""
    links = FieldProperty("EntriesList", GFFFieldType.List, GFFList())

    def __init__(
        self,
    ) -> None:
        super().__init__()
        self._fields: DLGReplyFields


class DLGEntryFields(TypedDict):
    Speaker: FieldGFF[str]
    RepliesList: FieldGFF[GFFList[DLGLink]]
class DLGEntry(DLGNode):
    """Entries are nodes that are responses by NPCs."""
    speaker = FieldProperty("Speaker", GFFFieldType.String, "")
    links: FieldProperty[GFFList[GFFStruct], GFFList[DLGLink]] = FieldProperty("RepliesList", GFFFieldType.List, GFFList())

    def __init__(
        self,
    ) -> None:
        super().__init__()
        self._fields: DLGEntryFields


class DLGAnimationFields(TypedDict):
    Animation: FieldGFF[int]
    Participant: FieldGFF[str]
class DLGAnimation(GFFStructInterface):
    """Represents a unit of animation executed during a node."""

    animation_id = FieldProperty("Animation", GFFFieldType.UInt32, 6)
    participant = FieldProperty("Participant", GFFFieldType.String, "")
    K2_FIELDS: ClassVar[dict[str, FieldGFF]] = {}

    def __init__(
        self,
    ) -> None:
        super().__init__()
        self._fields: DLGAnimationFields


class DLGLinkFields(TypedDict):
    Active: FieldGFF[ResRef]

    # Not in StartingList
    IsChild: FieldGFF[int]
    LinkComment: FieldGFF[str]
    Index: FieldGFF[int]

    # KotOR 2 Only:
    Active2: FieldGFF[ResRef]
    Not: FieldGFF[int]
    Not2: FieldGFF[int]
    Logic: FieldGFF[int]

    Param1: FieldGFF[int]
    Param2: FieldGFF[int]
    Param3: FieldGFF[int]
    Param4: FieldGFF[int]
    Param5: FieldGFF[int]
    ParamStrA: FieldGFF[str]

    Param1b: FieldGFF[int]
    Param2b: FieldGFF[int]
    Param3b: FieldGFF[int]
    Param4b: FieldGFF[int]
    Param5b: FieldGFF[int]
    ParamStrB: FieldGFF[str]
class DLGLink(GFFStructInterface):
    """Points to a node. Links are stored either in other nodes or in the starting list of the DLG."""

    active1 = FieldProperty("Active", GFFFieldType.ResRef)

    # not in StartingList
    comment = FieldProperty("LinkComment", GFFFieldType.String, "")
    is_child = FieldProperty("IsChild", GFFFieldType.UInt8)
    link_index = FieldProperty("Index", GFFFieldType.UInt32)

    active2 = FieldProperty("Active2", GFFFieldType.ResRef, game=Game.K2)
    logic = FieldProperty("Logic", GFFFieldType.Int32, game=Game.K2)
    active1_not = FieldProperty("Not", GFFFieldType.UInt8, game=Game.K2)
    active2_not = FieldProperty("Not2", GFFFieldType.UInt8, game=Game.K2)
    active1_param1 = FieldProperty("Param1", GFFFieldType.Int32, game=Game.K2)
    active1_param2 = FieldProperty("Param2", GFFFieldType.Int32, game=Game.K2)
    active1_param3 = FieldProperty("Param3", GFFFieldType.Int32, game=Game.K2)
    active1_param4 = FieldProperty("Param4", GFFFieldType.Int32, game=Game.K2)
    active1_param5 = FieldProperty("Param5", GFFFieldType.Int32, game=Game.K2)
    active1_param6 = FieldProperty("ParamStrA", GFFFieldType.String, "", game=Game.K2)
    active2_param1 = FieldProperty("Param1b", GFFFieldType.Int32, game=Game.K2)
    active2_param2 = FieldProperty("Param2b", GFFFieldType.Int32, game=Game.K2)
    active2_param3 = FieldProperty("Param3b", GFFFieldType.Int32, game=Game.K2)
    active2_param4 = FieldProperty("Param4b", GFFFieldType.Int32, game=Game.K2)
    active2_param5 = FieldProperty("Param5b", GFFFieldType.Int32, game=Game.K2)
    active2_param6 = FieldProperty("ParamStrB", GFFFieldType.String, "", game=Game.K2)

    def __init__(
        self,
        node: DLGNode
    ):
        super().__init__()
        self._fields: DLGLinkFields
        self._node: DLGNode = node

    def __hash__(self):
        return hash((self.__class__, self._node, self.link_index))


class DLGStuntFields(TypedDict):
    Participant: FieldGFF[str]
    StuntModel: FieldGFF[ResRef]
class DLGStunt(GFFStructInterface):
    participant = FieldProperty("Participant", GFFFieldType.String, "")
    stunt_model = FieldProperty("StuntModel", GFFFieldType.ResRef)

    def __init__(
        self,
    ) -> None:
        super().__init__()
        self._fields: DLGStuntFields


def construct_dlg(
    gff: GFF,
) -> DLG:
    """Constructs a DLG from a GFF file.

    Args:
    ----
        gff: GFF - The GFF file to construct the DLG from

    Returns:
    -------
        DLG - The constructed DLG object
    """
    def construct_link(link: DLGLink, relevant_nodes: GFFList[DLGNode]):
        link.__class__ = DLGLink
        link._node = relevant_nodes[link.link_index]

    def construct_node(node: DLGNode, list_index: int):
        node.list_index = list_index
        for animation in node.animations:
            animation.__class__ = DLGAnimation

    dlg: DLG = deepcopy(gff.root)  # type: ignore[assignment]
    dlg.__class__ = DLG
    all_entries: list[DLGEntry] = dlg.acquire("EntryList", GFFList())
    all_replies: list[DLGReply] = dlg.acquire("ReplyList", GFFList())

    stunt: DLGStunt
    for stunt in dlg.stunts:
        stunt.__class__ = DLGStunt

    starter: DLGLink
    for starter in dlg.starters:
        construct_link(starter, all_entries)  # type: ignore[covariance]

    reply_link: DLGLink
    entry: DLGEntry
    for i, entry in enumerate(dlg["EntryList"].value()):
        entry.__class__ = DLGEntry
        construct_node(entry, i)
        for reply_link in entry["RepliesList"].value():
            construct_link(reply_link, all_replies)  # type: ignore[covariance]

    entry_link: DLGLink
    reply: DLGReply
    for i, reply in enumerate(dlg["ReplyList"].value()):
        reply.__class__ = DLGReply
        construct_node(reply, i)
        for entry_link in reply["EntriesList"].value():
            construct_link(entry_link, all_entries)  # type: ignore[covariance]

    assert isinstance(dlg, DLG)
    return dlg


def dismantle_dlg(
    dlg: DLG,
    game: Game = Game.K2,
    *,
    use_deprecated: bool = True,
) -> GFF:
    """Dismantle a dialogue into a GFF structure.

    Args:
    ----
        dlg: (DLG object): The dialogue to dismantle
        game: (Game enum): The game type (default K2)
        use_deprecated: (bool): Use deprecated fields (default True).

    Returns:
    -------
        GFF: The dismantled dialogue as a GFF structure
    """
    def dismantle_node(node: DLGNode):
        animation: DLGAnimation
        for animation in node["AnimList"].value():
            animation.__class__ = GFFStruct
        node.__class__ = GFFStruct
        #del node.__dict__["list_index"]

    def dismantle_link(link: DLGLink):
        #del link.__dict__["_node"]
        link.__class__ = GFFStruct

    gff: GFF = GFF(GFFContent.DLG)
    gff.root = dlg.unwrap()
    gff.root.__class__ = GFFStruct

    stunt: DLGStunt
    for stunt in gff.root.get_list("StuntList"):
        stunt.__class__ = GFFStruct

    starter: DLGLink
    for starter in gff.root.get_list("StartingList"):
        dismantle_link(starter)

    reply_link: DLGLink
    entry: DLGEntry
    for entry in gff.root["EntryList"].value():
        dismantle_node(entry)
        for reply_link in entry["RepliesList"].value():
            dismantle_link(reply_link)

    entry_link: DLGLink
    reply: DLGReply
    for reply in gff.root["ReplyList"].value():
        dismantle_node(reply)
        for entry_link in reply["EntriesList"].value():
            dismantle_link(entry_link)

    assert isinstance(gff.root, GFFStruct)
    return gff


def read_dlg(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
) -> DLG:
    """Read a DLG object from a source.

    Args:
    ----
        source: The source to read from
        offset: The byte offset to start reading from
        size: The maximum number of bytes to read

    Returns:
    -------
        DLG: The constructed DLG object

    Processing Logic:
    ----------------
        - Read GFF data from the source using the given offset and size
        - Construct a DLG object from the parsed GFF data
        - Return the completed DLG object.
    """
    gff = read_gff(source, offset, size)
    return construct_dlg(gff)


def write_dlg(
    dlg: DLG,
    target: TARGET_TYPES,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
) -> None:
    """Writes a dialogue to a target file format.

    Args:
    ----
        dlg: Dialogue to write
        target: Target file or folder to write to
        game: Game the dialogue is for (default K2)
        file_format: Format to write as (default GFF)
        use_deprecated: Use deprecated fields (default True)

    Processing Logic:
    ----------------
        - Dismantles the dialogue into a GFF structure
        - Writes the GFF structure to the target using the specified file format
        - Does not return anything, writes the file directly
    """
    gff = dismantle_dlg(dlg, game, use_deprecated=use_deprecated)
    write_gff(gff, target, file_format)


def bytes_dlg(
    dlg: DLG,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
) -> bytes:
    """Converts a DLG object to bytes in a file format.

    Args:
    ----
        dlg: DLG - Dialogue object
        game: Game - Game the dialogue is from
        file_format: ResourceType - Format to return bytes in
        use_deprecated: bool - Use deprecated fields if True

    Returns:
    -------
        bytes: Bytes of dialogue in specified format

    Processing Logic:
    ----------------
        - Dismantle the DLG into a GFF structure
        - Encode the GFF into bytes in the requested format.
    """
    gff = dismantle_dlg(dlg, game, use_deprecated=use_deprecated)
    return bytes_gff(gff, file_format)
