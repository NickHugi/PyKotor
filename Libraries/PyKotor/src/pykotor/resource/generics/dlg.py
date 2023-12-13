from __future__ import annotations

from enum import IntEnum
from typing import ClassVar

from pykotor.common.geometry import Vector3
from pykotor.common.language import Gender, Language, LocalizedString
from pykotor.common.misc import Color, Game, ResRef
from pykotor.resource.formats.gff import GFF, GFFContent, GFFList, GFFStruct, read_gff, write_gff
from pykotor.resource.formats.gff.gff_auto import bytes_gff
from pykotor.resource.formats.gff.gff_data import GFFFieldType, GFFStructInterface, _GFFField
from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES, ResourceType


class DLGComputerType(IntEnum):
    Modern = 0
    Ancient = 1


class DLGConversationType(IntEnum):
    Human = 0
    Computer = 1
    Other = 2

class DLG(GFFStructInterface):
    """Stores dialog data.

    Attributes
    ----------
        word_count: "NumWords" field.
        on_abort: "EndConverAbort" field.
        on_end: "EndConversation" field.
        skippable: "Skippable" field.
        ambient_track: "AmbientTrack" field.
        animated_cut: "AnimatedCut" field.
        camera_model: "CameraModel" field.
        computer_type.value: "ComputerType" field.
        conversation_type.value: "ConversationType" field.
        old_hit_check: "OldHitCheck" field.
        unequip_hands: "UnequipHItem" field.
        unequip_items: "UnequipItems" field.
        vo_id: "VO_ID" field.

        alien_race_owner: "AlienRaceOwner" field. KotOR 2 Only.
        post_proc_owner: "PostProcOwner" field. KotOR 2 Only.
        record_no_vo: "RecordNoVO" field. KotOR 2 Only.
        next_node_id: "NextNodeID" field. KotOR 2 Only.

        delay_entry: "DelayEntry" field. Not used by the game engine.
        delay_reply: "DelayReply" field. Not used by the game engine.
    """

    BINARY_TYPE = ResourceType.DLG
    FIELDS: ClassVar[dict[str, _GFFField]] = {
        "AmbientTrack": _GFFField(GFFFieldType.ResRef, ResRef.from_blank()),
        "AnimatedCut": _GFFField(GFFFieldType.UInt8, 0),
        "CameraModel": _GFFField(GFFFieldType.ResRef, ResRef.from_blank()),
        "ComputerType": _GFFField(GFFFieldType.UInt8, DLGComputerType.Modern.value),
        "ConversationType": _GFFField(GFFFieldType.Int32, DLGConversationType.Human.value),
        "EndConverAbort": _GFFField(GFFFieldType.ResRef, ResRef.from_blank()),
        "EndConversation": _GFFField(GFFFieldType.ResRef, ResRef.from_blank()),
        "Skippable": _GFFField(GFFFieldType.UInt8, 0),

        "StuntList": _GFFField(GFFFieldType.List, GFFList()),
        "StartingList": _GFFField(GFFFieldType.List, GFFList()),

        "NumWords": _GFFField(GFFFieldType.UInt32, 0),
        "OldHitCheck": _GFFField(GFFFieldType.UInt8, 0),
        "UnequipHItem": _GFFField(GFFFieldType.UInt8, 0),
        "UnequipItems": _GFFField(GFFFieldType.UInt8, 0),
        "VO_ID": _GFFField(GFFFieldType.String, ""),

        "DelayEntry": _GFFField(GFFFieldType.UInt32, 0),  # Not used by game engine
        "DelayReply": _GFFField(GFFFieldType.UInt32, 0),  # Not used by game engine
    }

    K2_FIELDS: ClassVar[dict[str, _GFFField]] = {
        "AlienRaceOwner": _GFFField(GFFFieldType.Int32, 0),
        "NextNodeID": _GFFField(GFFFieldType.Int32, 0),
        "PostProcOwner": _GFFField(GFFFieldType.Int32, 0),
        "RecordNoVO": _GFFField(GFFFieldType.Int32, 0),
    }

    def __init__(
        self,
        blank_node: bool = True,
    ):
        super().__init__()

        self.StartingList = GFFList()  # list[DLGLink]
        self.StuntList = GFFList() # list[DLGStunt]

        # Add bare minimum to be openable by DLGEditor
        if blank_node:
            starter = DLGLink()
            entry = DLGEntry()
            entry.Text.set_data(Language.ENGLISH, Gender.MALE, "")
            object.__setattr__(starter, "_node", entry)
            starter.node = entry
            self.StartingList._structs.append(starter)

        self.AmbientTrack: ResRef = ResRef.from_blank()
        self.AnimatedCut: int = 0
        self.CameraModel: ResRef = ResRef.from_blank()
        self.ComputerType: DLGComputerType = DLGComputerType.Modern
        self.ConversationType: DLGConversationType = DLGConversationType.Human
        self.EndConverAbort: ResRef = ResRef.from_blank()
        self.EndConversation: ResRef = ResRef.from_blank()
        self.NumWords: int = 0
        self.OldHitCheck: bool = False
        self.Skippable: bool = False
        self.UnequipItems: bool = False
        self.UnequipHItem: bool = False
        self.VO_ID: str = ""

        # KotOR 2:
        self.AlienRaceOwner: int = 0
        self.NextNodeID: int = 0
        self.PostProcOwner: int = 0
        self.RecordNoVO: int = 0

        # Deprecated:
        self.DelayEntry: int = 0
        self.DelayReply: int = 0


    @property
    def ComputerType(self) -> DLGComputerType:
        return DLGComputerType(self.__getattr__("ComputerType"))

    @ComputerType.setter
    def ComputerType(self, value: DLGComputerType | int) -> None:
        if isinstance(value, DLGComputerType):
            value = value.value
        self.__setattr__("ComputerType", value)

    @property
    def ConversationType(self) -> DLGConversationType:
        return DLGConversationType(self.__getattr__("DLGConversationType"))

    @ConversationType.setter
    def ConversationType(self, value: DLGConversationType | int) -> None:
        if isinstance(value, DLGConversationType):
            value = value.value
        self.__setattr__("ConversationType", value)

    def print_tree(
        self,
    ) -> None:
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
            if link.node not in seen_nodes:
                print(f'{" " * indent}-> {link.node.text}')
                seen_links.append(link)

                if link.node not in seen_nodes:
                    seen_nodes.append(link.node)
                    self._print_tree(
                        link.node.links,
                        indent + 3,
                        seen_links,
                        seen_nodes,
                    )
            else:
                print(f'{" " * indent}-> [LINK] {link.node.text}')

    def all_entries(
        self,
    ) -> list[DLGEntry]:
        """Returns a flat list of all entries in the dialog.

        Returns
        -------
            A list of all stored entries.
        """
        return self._all_entries()

    def _all_entries(
        self,
        links: list[DLGLink] | None = None,
        seen_entries: list | None = None,
    ) -> list[DLGEntry]:
        """Collect all entries reachable from the given links.

        Args:
        ----
            links: {List of starting DLGLinks}
            seen_entries: {List of entries already processed}

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
        entries = []

        links = self.starters if links is None else links
        seen_entries = [] if seen_entries is None else seen_entries

        for link in links:
            entry = link.node
            if entry not in seen_entries:
                entries.append(entry)
                seen_entries.append(entry)
                for reply_link in entry.links:
                    reply = reply_link.node
                    entries.extend(self._all_entries(reply.links, seen_entries))

        return entries

    def all_replies(
        self,
    ) -> list[DLGReply]:
        """Returns a flat list of all replies in the dialog.

        Returns
        -------
            A list of all stored replies.
        """
        return self._all_replies()

    def _all_replies(
        self,
        links: list[DLGLink] | None = None,
        seen_replies: list | None = None,
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
        replies = []

        links = [_ for link in self.starters for _ in link.node.links] if links is None else links
        seen_replies = [] if seen_replies is None else seen_replies

        for link in links:
            reply = link.node
            if reply not in seen_replies:
                replies.append(reply)
                seen_replies.append(reply)
                for entry_link in reply.links:
                    entry = entry_link.node
                    replies.extend(self._all_replies(entry.links, seen_replies))

        return replies


class DLGNode(GFFStructInterface):
    """Represents a node in the dialog tree.

    Attributes
    ----------
        text: "Text" field.
        listener: "Listener" field.
        vo_resref: "VO_ResRef" field.
        script1: "Script" field.
        delay: "Delay" field.
        comment: "Comment" field.
        sound: "Sound" field.
        quest: "Quest" field.
        plot_index: "PlotIndex" field.
        plot_xp_percentage: "PlotXPPercentage" field.
        wait_flags: "WaitFlags" field.
        camera_angle: "CameraAngle" field.
        fade_type: "FadeType" field.
        sound_exists: "SoundExists" field.
        vo_text_changed: "Changed" field.

        quest_entry: "QuestEntry" field.
        fade_delay: "FadeDelay" field.
        fade_length: "FadeLength" field.
        camera_anim: "CameraAnimation" field.
        camera_id: "CameraID" field.
        camera_fov: "CamFieldOfView" field.
        camera_height: "CamHeightOffset" field.
        camera_effect: "CamVidEffect" field.
        target_height: "TarHeightOffset" field.
        fade_color: "FadeColor" field.

        script1_param1: "ActionParam1" field. KotOR 2 Only.
        script2_param1: "ActionParam1b" field. KotOR 2 Only.
        script1_param2: "ActionParam2" field. KotOR 2 Only.
        script2_param2: "ActionParam2b" field. KotOR 2 Only.
        script1_param3: "ActionParam3" field. KotOR 2 Only.
        script2_param3: "ActionParam3b" field. KotOR 2 Only.
        script1_param4: "ActionParam4" field. KotOR 2 Only.
        script2_param4: "ActionParam4b" field. KotOR 2 Only.
        script1_param5: "ActionParam5" field. KotOR 2 Only.
        script2_param5: "ActionParam5b" field. KotOR 2 Only.
        script1_param6: "ActionParamStrA" field. KotOR 2 Only.
        script2_param6: "ActionParamStrB" field. KotOR 2 Only.
        script2: "Script2" field. KotOR 2 Only.
        alien_race_node: "AlienRaceNode" field. KotOR 2 Only.
        emotion_id: "Emotion" field. KotOR 2 Only.
        facial_id: "FacialAnim" field. KotOR 2 Only.
        node_id: "NodeID" field. KotOR 2 Only.
        unskippable: "NodeUnskippable" field. KotOR 2 Only.
        post_proc_node: "PostProcNode" field. KotOR 2 Only.
        record_no_vo_override: "RecordNoVOOverri" field. KotOR 2 Only.
        record_vo: "RecordVO" field. KotOR 2 Only.
        vo_text_changed: "VOTextChanged" field. KotOR 2 Only.
    """

    FIELDS: ClassVar[dict[str, _GFFField]] = {
        "Text": _GFFField(GFFFieldType.LocalizedString, LocalizedString.from_invalid()),
        "Listener": _GFFField(GFFFieldType.String, ""),
        "VO_ResRef": _GFFField(GFFFieldType.ResRef, ResRef.from_blank()),
        "Script": _GFFField(GFFFieldType.ResRef, ResRef.from_blank()),
        "Delay": _GFFField(GFFFieldType.UInt32, 4294967295),
        "Comment": _GFFField(GFFFieldType.String, ""),
        "Sound": _GFFField(GFFFieldType.ResRef, ResRef.from_blank()),
        "Quest": _GFFField(GFFFieldType.String, ""),
        "PlotIndex": _GFFField(GFFFieldType.Int32, 0),
        "PlotXPPercentage": _GFFField(GFFFieldType.Single, 0.0),
        "WaitFlags": _GFFField(GFFFieldType.UInt32, 0),
        "CameraAngle": _GFFField(GFFFieldType.UInt32, 0),
        "FadeType": _GFFField(GFFFieldType.UInt8, 0),
        "SoundExists": _GFFField(GFFFieldType.UInt8, 0),
        "Changed": _GFFField(GFFFieldType.UInt8, 0),
        "AnimList": _GFFField(GFFFieldType.List, GFFList()),
        "QuestEntry": _GFFField(GFFFieldType.UInt32, 0),
        "FadeDelay": _GFFField(GFFFieldType.Single, 0.0),
        "FadeLength": _GFFField(GFFFieldType.Single, 0.0),
        "CameraAnimation": _GFFField(GFFFieldType.UInt16, 0),
        "CameraID": _GFFField(GFFFieldType.Int32, 0),
        "CamFieldOfView": _GFFField(GFFFieldType.Single, 0.0),
        "CamHeightOffset": _GFFField(GFFFieldType.Single, 0.0),
        "CamVidEffect": _GFFField(GFFFieldType.Int32, 0),
        "TarHeightOffset": _GFFField(GFFFieldType.Single, 0.0),
        "FadeColor": _GFFField(GFFFieldType.Vector3, Vector3.from_null()),
        # DLGEntry only:
        "Speaker": _GFFField(GFFFieldType.String, ""),
    }
    K2_FIELDS: ClassVar[dict[str, _GFFField]] = {
        "NodeID": _GFFField(GFFFieldType.Int32, 0),
        "ActionParam1": _GFFField(GFFFieldType.Int32, 0),
        "ActionParam2": _GFFField(GFFFieldType.Int32, 0),
        "ActionParam3": _GFFField(GFFFieldType.Int32, 0),
        "ActionParam4": _GFFField(GFFFieldType.Int32, 0),
        "ActionParam5": _GFFField(GFFFieldType.Int32, 0),
        "ActionParamStrA": _GFFField(GFFFieldType.String, ""),
        "Script2": _GFFField(GFFFieldType.ResRef, ResRef.from_blank()),
        "ActionParam1b": _GFFField(GFFFieldType.Int32, 0),
        "ActionParam2b": _GFFField(GFFFieldType.Int32, 0),
        "ActionParam3b": _GFFField(GFFFieldType.Int32, 0),
        "ActionParam4b": _GFFField(GFFFieldType.Int32, 0),
        "ActionParam5b": _GFFField(GFFFieldType.Int32, 0),
        "ActionParamStrB": _GFFField(GFFFieldType.String, ""),
        "AlienRaceNode": _GFFField(GFFFieldType.Int32, 0),
        "FacialAnim": _GFFField(GFFFieldType.Int32, 0),
        "Emotion": _GFFField(GFFFieldType.Int32, 0),
        "NodeUnskippable": _GFFField(GFFFieldType.Int32, 0),
        "PostProcNode": _GFFField(GFFFieldType.Int32, 0),
        "RecordNoVOOverri": _GFFField(GFFFieldType.Int32, 0),
        "RecordVO": _GFFField(GFFFieldType.Int32, 0),
        "VOTextChanged": _GFFField(GFFFieldType.Int32, 0),
    }

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
        self.links: list[DLGLink]
        object.__setattr__(self, "links", [])
        self.animations: list[DLGAnimation] = []
        object.__setattr__(self, "animations", [])

        self.Comment: str

        self.CameraAngle: int
        self.Delay: int
        self.FadeType: int
        self.Listener: str
        self.PlotIndex: int
        self.PlotXPPercentage: float
        self.Quest: str
        self.Script: ResRef
        self.Sound: ResRef
        self.SoundExists: bool
        self.Text: LocalizedString
        self.VO_ResRef: ResRef
        self.WaitFlags: int


        self.QuestEntry: int
        self.FadeColor: Color
        self.FadeDelay: float
        self.FadeLength: float
        self.CameraAnimation: int
        self.CameraID: int
        self.CamFieldOfView: float
        self.CamHeightOffset: float
        self.CamVidEffect: int
        self.TarHeightOffset: float

        # KotOR 2:
        self.ActionParam1: int
        self.ActionParam2: int
        self.ActionParam3: int
        self.ActionParam4: int
        self.ActionParam5: int
        self.ActionParamStrA: str

        self.Script2: ResRef
        self.ActionParam1b: int
        self.ActionParam2b: int
        self.ActionParam3b: int
        self.ActionParam4b: int
        self.ActionParam5b: int
        self.ActionParamStrB: str

        self.AlienRaceNode: int
        self.Emotion: int
        self.FacialAnim: int
        self.NodeUnskippable: bool
        self.PostProcNode: int

        self.RecordNoVOOverri: bool
        self.RecordVO: bool
        self.VOTextChanged: bool

    def __repr__(
        self,
    ):
        return str(self.Text.get(Language.ENGLISH, Gender.MALE))



class DLGReply(DLGNode):
    """Replies are nodes that are responses by the player."""

    def __init__(
        self,
    ):
        super().__init__()


class DLGEntry(DLGNode):
    """Entries are nodes that are responses by NPCs."""

    def __init__(
        self,
    ) -> None:
        super().__init__()
        Speaker = ""


class DLGAnimation(GFFStructInterface):
    """Represents a unit of animation executed during a node."""

    FIELDS = {}
    K2_FIELDS = {}

    def __init__(
        self,
    ) -> None:
        self.animation_id: int = 6
        self.participant: str = ""


class DLGLink(GFFStructInterface):
    """Points to a node. Links are stored either in other nodes or in the starting list of the DLG.

    Attributes
    ----------
        active1: "Active" field.
        comment: "LinkComment" field. Only used in links stored in nodes.
        is_child: "IsChild" field. Only used in links stored in nodes.
        active2: "Active2" field. KotOR 2 Only.
        logic: "Logic" field. KotOR 2 Only.
        active1_not: "Not" field. KotOR 2 Only.
        active2_not: "Not2" field. KotOR 2 Only.
        active1_param1: "Param1" field. KotOR 2 Only.
        active1_param2: "Param2" field. KotOR 2 Only.
        active1_param3: "Param3" field. KotOR 2 Only.
        active1_param4: "Param4" field. KotOR 2 Only.
        active1_param5: "Param5" field. KotOR 2 Only.
        active1_param6: "ParamStrA" field. KotOR 2 Only.
        active2_param1: "Param1b" field. KotOR 2 Only.
        active2_param2: "Param2b" field. KotOR 2 Only.
        active2_param3: "Param3b" field. KotOR 2 Only.
        active2_param4: "Param4b" field. KotOR 2 Only.
        active2_param5: "Param5b" field. KotOR 2 Only.
        active2_param6: "ParamStrB" field. KotOR 2 Only.
    """

    FIELDS: ClassVar[dict[str, _GFFField]] = {
        "Active": _GFFField(GFFFieldType.ResRef, ResRef.from_blank()),

        # not in StartingList
        "LinkComment": _GFFField(GFFFieldType.String, ""),
        "IsChild": _GFFField(GFFFieldType.UInt8, 0),
    }

    K2_FIELDS: ClassVar[dict[str, _GFFField]] = {
        "Active2": _GFFField(GFFFieldType.ResRef, ResRef.from_blank()),
        "Logic": _GFFField(GFFFieldType.Int32, 0),
        "Not": _GFFField(GFFFieldType.UInt8, 0),
        "Not2": _GFFField(GFFFieldType.UInt8, 0),
        "Param1": _GFFField(GFFFieldType.Int32, 0),
        "Param2": _GFFField(GFFFieldType.Int32, 0),
        "Param3": _GFFField(GFFFieldType.Int32, 0),
        "Param4": _GFFField(GFFFieldType.Int32, 0),
        "Param5": _GFFField(GFFFieldType.Int32, 0),
        "ParamStrA": _GFFField(GFFFieldType.String, ""),
        "Param1b": _GFFField(GFFFieldType.Int32, 0),
        "Param2b": _GFFField(GFFFieldType.Int32, 0),
        "Param3b": _GFFField(GFFFieldType.Int32, 0),
        "Param4b": _GFFField(GFFFieldType.Int32, 0),
        "Param5b": _GFFField(GFFFieldType.Int32, 0),
        "ParamStrB": _GFFField(GFFFieldType.String, ""),
    }

    def __init__(
        self,
        node: DLGNode | None = None,
    ):
        self.node: DLGNode
        object.__setattr__(self, "node", node)


class DLGStunt(GFFStructInterface):
    """
    Attributes
    ----------
    participant: "Participant" field.
    stunt_model: "StuntModel" field.
    """  # noqa: D205, D212

    FIELDS: ClassVar[dict[str, _GFFField]] = {
        "Participant": _GFFField(GFFFieldType.String, ""),
        "StuntModel": _GFFField(GFFFieldType.ResRef, ResRef.from_blank()),
    }
    K2_FIELDS = {}

    def __init__(
        self,
    ) -> None:
        self.Participant: str = ""
        self.StuntModel: ResRef = ResRef.from_blank()


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

    Processing Logic:
    ----------------
        - Constructs DLGNode objects from GFFStructs
        - Constructs DLGLink objects from GFFStructs
        - Populates DLG object with nodes, links, and metadata
        - Loops through GFF lists to populate all nodes and links.
    """
    dlg = DLG(blank_node=False)

    root = gff.root

    all_entries = [DLGEntry() for _ in range(len(root.acquire("EntryList", GFFList())))]
    all_replies = [DLGReply() for _ in range(len(root.acquire("ReplyList", GFFList())))]

    stunt_list = root.acquire("StuntList", GFFList())
    for stunt_struct in stunt_list:
        stunt = DLGStunt()
        dlg.stunts.append(stunt)
        stunt.participant = stunt_struct.acquire("Participant", "")
        stunt.stunt_model = stunt_struct.acquire("StuntModel", ResRef.from_blank())

    starting_list = root.acquire("StartingList", GFFList())
    for link_struct in starting_list:
        entry_index = link_struct.acquire("Index", 0)
        link = DLGLink()
        dlg.starters.append(link)
        link.node = all_entries[entry_index]
        link.from_struct(link_struct)

    entry_list: GFFList = root.acquire("EntryList", GFFList())
    anim_list: GFFList
    for i, entry_struct in enumerate(entry_list):
        entry: DLGEntry = all_entries[i]
        entry.from_struct(entry_struct)
        anim_list = entry_struct.acquire("AnimList", GFFList())
        for anim_struct in anim_list:
            entry.animations.append(DLGAnimation.from_struct(anim_struct))

        nested_replies_list: GFFList = entry_struct.acquire("RepliesList", GFFList())
        for link_struct in nested_replies_list:
            link = DLGLink()
            link.node = all_replies[link_struct.acquire("Index", 0)]
            entry.links.append(link)
            link.from_struct(link_struct)

    replies_list: GFFList = root.acquire("ReplyList", GFFList())
    for i, reply_struct in enumerate(replies_list):
        reply: DLGReply = all_replies[i]
        reply.from_struct(reply_struct)
        anim_list = reply_struct.acquire("AnimList", GFFList())
        for anim_struct in anim_list:
            reply.animations.append(DLGAnimation.from_struct(anim_struct))

        nested_entries_list: GFFList = reply_struct.acquire("EntriesList", GFFList())
        for link_struct in nested_entries_list:
            link = DLGLink()
            entry = all_entries[link_struct.acquire("Index", 0)]
            link.node = entry
            link.from_struct(link_struct)
            reply.links.append(link)

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

    Processing Logic:
    ----------------
        - Extract metadata from DLG and populate GFF root
        - Populate lists for starters, entries, replies
        - Call dismantle functions to extract node and link data
        - dismantle_node handles populating node fields
        - dismantle_link handles populating link fields.
    """
    def dismantle_link(
        gff_struct: GFFStruct,
        link: DLGLink,
        nodes: list,
        list_name: str,
    ):
        """Disassembles a link into a GFFStruct.

        Args:
        ----
            gff_struct: GFFStruct - The struct to populate
            link: DLGLink - The link to disassemble
            nodes: list - The list of nodes

        Returns:
        -------
            None: Populates the GFFStruct

        Processing Logic:
        ----------------
            - Sets the Active resref on the GFFStruct from the link
            - Sets the Index uint32 on the GFFStruct from the node list index
            - If game is K2, sets additional link properties on the GFFStruct.
        """
        gff_struct.set_resref("Active", link.active1)
        gff_struct.set_uint32("Index", nodes.index(link.node))
        if list_name != "StartingList":
            gff_struct.set_uint8("IsChild", int(link.is_child))
        if game == Game.K2:
            gff_struct.set_resref("Active2", link.active2)
            gff_struct.set_int32("Logic", link.logic)
            gff_struct.set_uint8("Not", link.active1_not)
            gff_struct.set_uint8("Not2", link.active2_not)
            gff_struct.set_int32("Param1", link.active1_param1)
            gff_struct.set_int32("Param2", link.active1_param2)
            gff_struct.set_int32("Param3", link.active1_param3)
            gff_struct.set_int32("Param4", link.active1_param4)
            gff_struct.set_int32("Param5", link.active1_param5)
            gff_struct.set_string("ParamStrA", link.active1_param6)
            gff_struct.set_int32("Param1b", link.active2_param1)
            gff_struct.set_int32("Param2b", link.active2_param2)
            gff_struct.set_int32("Param3b", link.active2_param3)
            gff_struct.set_int32("Param4b", link.active2_param4)
            gff_struct.set_int32("Param5b", link.active2_param5)
            gff_struct.set_string("ParamStrB", link.active2_param6)

    def dismantle_node(
        gff_struct: GFFStruct,
        node: DLGNode,
        nodes: list,
        list_name: str,
    ):
        """Disassembles a DLGNode into a GFFStruct.

        Args:
        ----
            gff_struct: GFFStruct - The GFFStruct to populate
            node: DLGNode - The DLGNode to disassemble

        Processing Logic:
        ----------------
            - Sets node properties like text, listener etc on the GFFStruct
            - Handles optional node properties
            - Creates lists for animations and links and populates them.
        """
        gff_struct.set_locstring("Text", node.text)
        gff_struct.set_string("Listener", node.listener)
        gff_struct.set_resref("VO_ResRef", node.vo_resref)
        gff_struct.set_resref("Script", node.script1)
        gff_struct.set_uint32("Delay", 4294967295 if node.delay == -1 else node.delay)
        gff_struct.set_string("Comment", node.comment)
        gff_struct.set_resref("Sound", node.sound)
        gff_struct.set_string("Quest", node.quest)
        gff_struct.set_int32("PlotIndex", node.plot_index)
        if node.plot_xp_percentage:
            gff_struct.set_single("PlotXPPercentage", node.plot_xp_percentage)
        gff_struct.set_uint32("WaitFlags", node.wait_flags)
        gff_struct.set_uint32("CameraAngle", node.camera_angle)
        gff_struct.set_uint8("FadeType", node.fade_type)
        gff_struct.set_uint8("SoundExists", node.sound_exists)
        if node.vo_text_changed:
            gff_struct.set_uint8("Changed", node.vo_text_changed)

        anim_list = gff_struct.set_list("AnimList", GFFList())
        for anim in node.animations:
            anim_struct = anim_list.add(0)
            anim_struct.set_uint16("Animation", anim.animation_id)
            anim_struct.set_string("Participant", anim.participant)

        if node.quest_entry is not None and node.quest_entry:
            gff_struct.set_uint32("QuestEntry", node.quest_entry)
        if node.fade_delay is not None:
            gff_struct.set_single("FadeDelay", node.fade_delay)
        if node.fade_length is not None:
            gff_struct.set_single("FadeLength", node.fade_length)
        if node.camera_anim is not None:
            gff_struct.set_uint16("CameraAnimation", node.camera_anim)
        if node.camera_id is not None:
            gff_struct.set_int32("CameraID", node.camera_id)
        if node.camera_fov is not None:
            gff_struct.set_single("CamFieldOfView", node.camera_fov)
        if node.camera_height is not None:
            gff_struct.set_single("CamHeightOffset", node.camera_height)
        if node.camera_effect is not None:
            gff_struct.set_int32("CamVidEffect", node.camera_effect)
        if node.target_height is not None:
            gff_struct.set_single("TarHeightOffset", node.target_height)
        if node.fade_color is not None:
            gff_struct.set_vector3("FadeColor", node.fade_color.bgr_vector3())

        if game == Game.K2:
            gff_struct.set_int32("ActionParam1", node.script1_param1)
            gff_struct.set_int32("ActionParam1b", node.script2_param1)
            gff_struct.set_int32("ActionParam2", node.script1_param2)
            gff_struct.set_int32("ActionParam2b", node.script2_param2)
            gff_struct.set_int32("ActionParam3", node.script1_param3)
            gff_struct.set_int32("ActionParam3b", node.script2_param3)
            gff_struct.set_int32("ActionParam4", node.script1_param4)
            gff_struct.set_int32("ActionParam4b", node.script2_param4)
            gff_struct.set_int32("ActionParam5", node.script1_param5)
            gff_struct.set_int32("ActionParam5b", node.script2_param5)
            gff_struct.set_string("ActionParamStrA", node.script1_param6)
            gff_struct.set_string("ActionParamStrB", node.script2_param6)
            gff_struct.set_resref("Script2", node.script2)
            gff_struct.set_int32("AlienRaceNode", node.alien_race_node)
            gff_struct.set_int32("Emotion", node.emotion_id)
            gff_struct.set_int32("FacialAnim", node.facial_id)
            gff_struct.set_int32("NodeID", node.node_id)
            gff_struct.set_int32("NodeUnskippable", node.unskippable)
            gff_struct.set_int32("PostProcNode", node.post_proc_node)
            gff_struct.set_int32("RecordNoVOOverri", node.record_no_vo_override)
            gff_struct.set_int32("RecordVO", node.record_vo)
            gff_struct.set_int32("VOTextChanged", node.vo_text_changed)

        link_list: GFFList = gff_struct.set_list(list_name, GFFList())
        for i, link in enumerate(node.links):
            link_struct: GFFStruct = link_list.add(i)
            dismantle_link(link_struct, link, nodes, list_name)

    all_entries = dlg.all_entries()
    all_entries.reverse()
    all_replies = dlg.all_replies()
    all_replies.reverse()

    gff = GFF(GFFContent.DLG)

    root = gff.root
    root.set_uint32("NumWords", dlg.word_count)
    root.set_resref("EndConverAbort", dlg.on_abort)
    root.set_resref("EndConversation", dlg.on_end)
    root.set_uint8("Skippable", dlg.skippable)
    if str(dlg.ambient_track):
        root.set_resref("AmbientTrack", dlg.ambient_track)
    if dlg.animated_cut:
        root.set_uint8("AnimatedCut", dlg.animated_cut)
    if dlg.computer_type:
        root.set_uint8("ComputerType", dlg.computer_type.value)
    root.set_resref("CameraModel", dlg.camera_model)
    if dlg.conversation_type:
        root.set_int32("ConversationType", dlg.conversation_type.value)
    if dlg.old_hit_check:
        root.set_uint8("OldHitCheck", dlg.old_hit_check)
    if dlg.unequip_hands:
        root.set_uint8("UnequipHItem", dlg.unequip_hands)
    if dlg.unequip_items:
        root.set_uint8("UnequipItems", dlg.unequip_items)
    root.set_string("VO_ID", dlg.vo_id)
    if game == Game.K2:
        root.set_int32("AlienRaceOwner", dlg.alien_race_owner)
        root.set_int32("PostProcOwner", dlg.post_proc_owner)
        root.set_int32("RecordNoVO", dlg.record_no_vo)
        root.set_int32("NextNodeID", dlg.next_node_id)
    if use_deprecated:
        root.set_uint32("DelayEntry", dlg.delay_entry)
        root.set_uint32("DelayReply", dlg.delay_reply)

    stunt_list = root.set_list("StuntList", GFFList())
    for stunt in dlg.stunts:
        stunt_struct = stunt_list.add(0)
        stunt_struct.set_string("Participant", stunt.participant)
        stunt_struct.set_resref("StuntModel", stunt.stunt_model)

    starting_list = root.set_list("StartingList", GFFList())
    for i, starter in enumerate(dlg.starters):
        starting_struct = starting_list.add(i)
        dismantle_link(starting_struct, starter, all_entries, "StartingList")

    entries_list = root.set_list("EntryList", GFFList())
    for i, entry in enumerate(all_entries):
        entries_struct: GFFStruct = entries_list.add(i)
        entries_struct.set_string("Speaker", entry.speaker)
        dismantle_node(entries_struct, entry, all_replies, "RepliesList")

    replies_list = root.set_list("ReplyList", GFFList())
    for i, reply in enumerate(all_replies):
        replies_struct = replies_list.add(i)
        dismantle_node(replies_struct, reply, all_entries, "EntriesList")

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
