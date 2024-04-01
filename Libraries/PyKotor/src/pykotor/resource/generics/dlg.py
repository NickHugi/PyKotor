from __future__ import annotations

from copy import deepcopy
from enum import IntEnum
from typing import TYPE_CHECKING, ClassVar, TypedDict, Union

from pykotor.common.geometry import Vector3
from pykotor.common.language import Gender, Language, LocalizedString
from pykotor.common.misc import Game, ResRef
from pykotor.resource.formats.gff import GFF, GFFContent, GFFList, read_gff, write_gff
from pykotor.resource.formats.gff.gff_auto import bytes_gff
from pykotor.resource.formats.gff.gff_data import FieldGFF, GFFFieldType, GFFStruct, GFFStructInterface  # noqa: PLC2701
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
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
    FIELDS: ClassVar[dict[str, FieldGFF]] = {
        "AmbientTrack": FieldGFF(GFFFieldType.ResRef, ResRef.from_blank()),
        "AnimatedCut": FieldGFF(GFFFieldType.UInt8, 0),
        "CameraModel": FieldGFF(GFFFieldType.ResRef, ResRef.from_blank()),
        "ComputerType": FieldGFF(GFFFieldType.UInt8, DLGComputerType.Modern.value),
        "ConversationType": FieldGFF(GFFFieldType.Int32, DLGConversationType.Human.value),
        "EndConverAbort": FieldGFF(GFFFieldType.ResRef, ResRef.from_blank()),
        "EndConversation": FieldGFF(GFFFieldType.ResRef, ResRef.from_blank()),
        "Skippable": FieldGFF(GFFFieldType.UInt8, 0),

        "EntryList": FieldGFF(GFFFieldType.List, GFFList()),
        "ReplyList": FieldGFF(GFFFieldType.List, GFFList()),
        "StuntList": FieldGFF(GFFFieldType.List, GFFList()),
        "StartingList": FieldGFF(GFFFieldType.List, GFFList()),

        "NumWords": FieldGFF(GFFFieldType.UInt32, 0),
        "OldHitCheck": FieldGFF(GFFFieldType.UInt8, 0),
        "UnequipHItem": FieldGFF(GFFFieldType.UInt8, 0),
        "UnequipItems": FieldGFF(GFFFieldType.UInt8, 0),
        "VO_ID": FieldGFF(GFFFieldType.String, ""),

        "DelayEntry": FieldGFF(GFFFieldType.UInt32, 0),  # Not used by game engine
        "DelayReply": FieldGFF(GFFFieldType.UInt32, 0),  # Not used by game engine
    }

    K2_FIELDS: ClassVar[dict[str, FieldGFF]] = {
        "AlienRaceOwner": FieldGFF(GFFFieldType.Int32, 0),
        "NextNodeID": FieldGFF(GFFFieldType.Int32, 0),
        "PostProcOwner": FieldGFF(GFFFieldType.Int32, 0),
        "RecordNoVO": FieldGFF(GFFFieldType.Int32, 0),
    }

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

    def __deepcopy__(self, memo):
        ...

    @property
    def stunts(self) -> GFFList[DLGStunt]: return self._fields.get("StuntList", self.FIELDS["StuntList"]).value()
    @stunts.setter
    def stunts(self, value: FieldGFF[GFFList[DLGStunt]]):
        self._fields["StuntList"] = value

    @property
    def text(self) -> LocalizedString: return self["Text"].value()
    @text.setter
    def text(self, value: FieldGFF[LocalizedString] | LocalizedString):
        if isinstance(value, LocalizedString):
            value = FieldGFF(GFFFieldType.LocalizedString, value)
        self["Text"] = value

    @property
    def starters(self) -> GFFList[DLGLink]: return self._fields.get("StartingList", self.FIELDS["StartingList"]).value()
    @starters.setter
    def starters(self, value: FieldGFF[GFFList[DLGLink]]):
        self._fields["StartingList"] = value

    @property
    def animated_cut(self) -> int: return self._fields["AnimatedCut"].value()
    @animated_cut.setter
    def animated_cut(self, value: FieldGFF[int]):
        self._fields["AnimatedCut"] = value

    @property
    def vo_id(self) -> str: return self._fields["VO_ID"].value()
    @vo_id.setter
    def vo_id(self, value: FieldGFF[str]):
        self._fields["VO_ID"] = value

    @property
    def camera_model(self) -> ResRef:
        return self._fields["CameraModel"].value()
    @camera_model.setter
    def camera_model(self, value: FieldGFF[ResRef] | ResRef | str):
        if isinstance(value, ResRef):
            value = FieldGFF(GFFFieldType.ResRef, value)
        elif isinstance(value, str):
            value = FieldGFF(GFFFieldType.ResRef, ResRef(value))
        self._fields["CameraModel"] = value

    @property
    def on_abort(self) -> ResRef:
        return self._fields["EndConverAbort"].value()
    @on_abort.setter
    def on_abort(self, value: FieldGFF[ResRef] | ResRef | str):
        if isinstance(value, ResRef):
            value = FieldGFF(GFFFieldType.ResRef, value)
        elif isinstance(value, str):
            value = FieldGFF(GFFFieldType.ResRef, ResRef(value))
        self._fields["EndConverAbort"] = value

    @property
    def on_end(self) -> ResRef:
        return self._fields["EndConversation"].value()
    @on_end.setter
    def on_end(self, value: FieldGFF[ResRef] | ResRef | str):
        if isinstance(value, ResRef):
            value = FieldGFF(GFFFieldType.ResRef, value)
        elif isinstance(value, str):
            value = FieldGFF(GFFFieldType.ResRef, ResRef(value))
        self._fields["EndConversation"] = value

    @property
    def ambient_track(self) -> ResRef:
        return self._fields["AmbientTrack"].value()
    @ambient_track.setter
    def ambient_track(self, value: FieldGFF[ResRef] | ResRef | str):
        if isinstance(value, ResRef):
            value = FieldGFF(GFFFieldType.ResRef, value)
        elif isinstance(value, str):
            value = FieldGFF(GFFFieldType.ResRef, ResRef(value))
        self._fields["AmbientTrack"] = value

    @property
    def alien_race_owner(self) -> int:
        return self._fields["AlienRaceOwner"].value()
    @alien_race_owner.setter
    def alien_race_owner(self, value: FieldGFF[int]):
        self._fields["AlienRaceOwner"] = value

    @property
    def post_proc_owner(self) -> int:
        return self._fields["PostProcOwner"].value()
    @post_proc_owner.setter
    def post_proc_owner(self, value: FieldGFF[int]):
        self._fields["PostProcOwner"] = value

    @property
    def next_node_id(self) -> int:
        return self._fields["NextNodeID"].value()
    @next_node_id.setter
    def next_node_id(self, value: FieldGFF[int]):
        self._fields["NextNodeID"] = value

    @property
    def record_no_vo(self) -> int:
        return self._fields["RecordNoVO"].value()
    @record_no_vo.setter
    def record_no_vo(self, value: FieldGFF[int]):
        self._fields["RecordNoVO"] = value

    @property
    def word_count(self) -> int:
        return self._fields["NumWords"].value()
    @word_count.setter
    def word_count(self, value: FieldGFF[int]):
        self._fields["NumWords"] = value

    @property
    def skippable(self) -> int:
        return bool(self._fields["Skippable"].value())
    @skippable.setter
    def skippable(self, value: FieldGFF[int] | int | bool):
        if isinstance(value, FieldGFF):
            self._fields["Skippable"] = value
        else:
            self._fields["Skippable"] = FieldGFF(GFFFieldType.UInt8, int(value))

    @property
    def old_hit_check(self) -> int:
        return bool(self._fields["OldHitCheck"].value())
    @old_hit_check.setter
    def old_hit_check(self, value: FieldGFF[int] | int | bool):
        if isinstance(value, FieldGFF):
            self._fields["OldHitCheck"] = value
        else:
            self._fields["OldHitCheck"] = FieldGFF(GFFFieldType.UInt8, int(value))

    @property
    def unequip_hands(self) -> int:
        return bool(self._fields["UnequipHItem"].value())
    @unequip_hands.setter
    def unequip_hands(self, value: FieldGFF[int] | int | bool):
        if isinstance(value, FieldGFF):
            self._fields["UnequipHItem"] = value
        else:
            self._fields["UnequipHItem"] = FieldGFF(GFFFieldType.UInt8, int(value))

    @property
    def unequip_items(self) -> int:
        return bool(self._fields["UnequipItems"].value())
    @unequip_items.setter
    def unequip_items(self, value: FieldGFF[int] | int | bool):
        if isinstance(value, FieldGFF):
            self._fields["UnequipItems"] = value
        else:
            self._fields["UnequipItems"] = FieldGFF(GFFFieldType.UInt8, int(value))

    @property
    def computer_type(self) -> DLGComputerType:
        return DLGComputerType(self._fields["ComputerType"].value())
    @computer_type.setter
    def computer_type(self, value: FieldGFF[int] | DLGComputerType | int):
        if isinstance(value, DLGComputerType):
            value = FieldGFF(GFFFieldType.UInt8, value.value)
        elif isinstance(value, int):
            value = FieldGFF(GFFFieldType.UInt8, value)
        self._fields["ComputerType"] = value

    @property
    def conversation_type(self) -> DLGConversationType:
        return DLGConversationType(self._fields["ConversationType"].value())
    @conversation_type.setter
    def conversation_type(self, value: FieldGFF[int] | DLGConversationType | int):
        if isinstance(value, DLGConversationType):
            value = FieldGFF(GFFFieldType.Int32, value.value)
        elif isinstance(value, int):
            value = FieldGFF(GFFFieldType.Int32, value)
        self._fields["ConversationType"] = value

    # Deprecated
    @property
    def delay_entry(self) -> int: return self._fields["DelayEntry"].value()
    @delay_entry.setter
    def delay_entry(self, value: FieldGFF[int] | int):
        if isinstance(value, int):
            value = FieldGFF(GFFFieldType.UInt32, value)
        self._fields["DelayEntry"] = value
    @property
    def delay_reply(self) -> int: return self._fields["DelayReply"].value()
    @delay_reply.setter
    def delay_reply(self, value: FieldGFF[int] | int):
        if isinstance(value, int):
            value = FieldGFF(GFFFieldType.UInt32, value)
        self._fields["DelayReply"] = value

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
            entry: DLGNode = link._node
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
        replies: list[DLGReply] = []

        starting_links: list[DLGLink] = links if links is not None else [
            _ for link in self.starters
            for _ in link._node.links
        ]
        seen_replies = [] if seen_replies is None else seen_replies

        for link in starting_links:
            reply: DLGNode = link._node
            assert isinstance(reply, DLGReply)
            if reply in seen_replies:
                continue
            replies.append(reply)
            seen_replies.append(reply)
            for entry_link in reply.links:
                entry: DLGNode = entry_link._node
                assert isinstance(entry, DLGEntry)
                replies.extend(self._all_replies(entry.links, seen_replies))

        return replies

class DLGNodeFields(TypedDict):
    Comment: FieldGFF[str]
    AnimList: FieldGFF[GFFList[DLGAnimation]]

    SoundExists: FieldGFF[int]
    Text: FieldGFF[LocalizedString]
    Listener: FieldGFF[str]
    VO_ResRef: FieldGFF[ResRef]
    PlotXPPercentage: FieldGFF[float]
    WaitFlags: FieldGFF[int]
    CameraAngle: FieldGFF[int]
    FadeType: FieldGFF[int]

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

    FIELDS: ClassVar[dict[str, FieldGFF]] = {
        "Text": FieldGFF(GFFFieldType.LocalizedString, LocalizedString.from_invalid()),
        "Listener": FieldGFF(GFFFieldType.String, ""),
        "VO_ResRef": FieldGFF(GFFFieldType.ResRef, ResRef.from_blank()),
        "Script": FieldGFF(GFFFieldType.ResRef, ResRef.from_blank()),
        "Delay": FieldGFF(GFFFieldType.UInt32, 0xFFFFFFFF),
        "Comment": FieldGFF(GFFFieldType.String, ""),
        "AnimList": FieldGFF(GFFFieldType.List, GFFList()),
        "Sound": FieldGFF(GFFFieldType.ResRef, ResRef.from_blank()),
        "Quest": FieldGFF(GFFFieldType.String, ""),
        "PlotIndex": FieldGFF(GFFFieldType.Int32, 0),
        "PlotXPPercentage": FieldGFF(GFFFieldType.Single, 0.0),
        "WaitFlags": FieldGFF(GFFFieldType.UInt32, 0),
        "CameraAngle": FieldGFF(GFFFieldType.UInt32, 0),
        "FadeType": FieldGFF(GFFFieldType.UInt8, 0),
        "SoundExists": FieldGFF(GFFFieldType.UInt8, 0),
        "Changed": FieldGFF(GFFFieldType.UInt8, 0),
        "QuestEntry": FieldGFF(GFFFieldType.UInt32, 0),
        "FadeDelay": FieldGFF(GFFFieldType.Single, 0.0),
        "FadeLength": FieldGFF(GFFFieldType.Single, 0.0),
        "CameraAnimation": FieldGFF(GFFFieldType.UInt16, -1),
        "CameraID": FieldGFF(GFFFieldType.Int32, 0),
        "CamFieldOfView": FieldGFF(GFFFieldType.Single, 0.0),
        "CamHeightOffset": FieldGFF(GFFFieldType.Single, 0.0),
        "CamVidEffect": FieldGFF(GFFFieldType.Int32, 0),
        "TarHeightOffset": FieldGFF(GFFFieldType.Single, 0.0),
        "FadeColor": FieldGFF(GFFFieldType.Vector3, Vector3.from_null()),
    }
    K2_FIELDS: ClassVar[dict[str, FieldGFF]] = {
        "NodeID": FieldGFF(GFFFieldType.Int32, 0),
        "ActionParam1": FieldGFF(GFFFieldType.Int32, 0),
        "ActionParam2": FieldGFF(GFFFieldType.Int32, 0),
        "ActionParam3": FieldGFF(GFFFieldType.Int32, 0),
        "ActionParam4": FieldGFF(GFFFieldType.Int32, 0),
        "ActionParam5": FieldGFF(GFFFieldType.Int32, 0),
        "ActionParamStrA": FieldGFF(GFFFieldType.String, ""),
        "Script2": FieldGFF(GFFFieldType.ResRef, ResRef.from_blank()),
        "ActionParam1b": FieldGFF(GFFFieldType.Int32, 0),
        "ActionParam2b": FieldGFF(GFFFieldType.Int32, 0),
        "ActionParam3b": FieldGFF(GFFFieldType.Int32, 0),
        "ActionParam4b": FieldGFF(GFFFieldType.Int32, 0),
        "ActionParam5b": FieldGFF(GFFFieldType.Int32, 0),
        "ActionParamStrB": FieldGFF(GFFFieldType.String, ""),
        "AlienRaceNode": FieldGFF(GFFFieldType.Int32, 0),
        "FacialAnim": FieldGFF(GFFFieldType.Int32, 0),
        "Emotion": FieldGFF(GFFFieldType.Int32, 0),
        "NodeUnskippable": FieldGFF(GFFFieldType.Int32, 0),
        "PostProcNode": FieldGFF(GFFFieldType.Int32, 0),
        "RecordNoVOOverri": FieldGFF(GFFFieldType.Int32, 0),
        "RecordNoOverri": FieldGFF(GFFFieldType.Int32, 0),
        "RecordVO": FieldGFF(GFFFieldType.Int32, 0),
        "VOTextChanged": FieldGFF(GFFFieldType.Int32, 0),
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
        super().__init__()
        self._fields: DLGNodeFields
        self.list_index: int = -1
        animation: DLGAnimation
        for animation in self.animations:
            animation.__class__ = DLGAnimation

    @property
    def animations(self) -> GFFList[DLGAnimation]: return self._fields.get("AnimList", self.FIELDS["AnimList"]).value()
    @animations.setter
    def animations(self, value: FieldGFF[GFFList[DLGAnimation]]):
        self._fields["AnimList"] = value

    @property
    def text(self) -> LocalizedString: return self._fields["Text"].value()
    @text.setter
    def text(self, value: FieldGFF[LocalizedString] | LocalizedString):
        if isinstance(value, LocalizedString):
            value = FieldGFF(GFFFieldType.LocalizedString, value)
        self._fields["Text"] = value

    @property
    def emotion_id(self) -> int: return self._fields["Emotion"].value()
    @emotion_id.setter
    def emotion_id(self, value: FieldGFF[int] | int):
        if isinstance(value, int):
            value = FieldGFF(GFFFieldType.Int32, value)
        self._fields["Emotion"] = value

    @property
    def facial_id(self) -> int: return self._fields["FacialAnim"].value()
    @facial_id.setter
    def facial_id(self, value: FieldGFF[int] | int):
        if isinstance(value, int):
            value = FieldGFF(GFFFieldType.Int32, value)
        self._fields["FacialAnim"] = value

    @property
    def node_id(self) -> int: return self._fields["NodeID"].value()
    @node_id.setter
    def node_id(self, value: FieldGFF[int] | int):
        if isinstance(value, int):
            value = FieldGFF(GFFFieldType.Int32, value)
        self._fields["NodeID"] = value

    @property
    def unskippable(self) -> int: return self._fields["NodeUnskippable"].value()
    @unskippable.setter
    def unskippable(self, value: FieldGFF[int] | int):
        if isinstance(value, int):
            value = FieldGFF(GFFFieldType.Int32, value)
        self._fields["NodeUnskippable"] = value

    @property
    def post_proc_node(self) -> int: return self._fields["PostProcNode"].value()
    @post_proc_node.setter
    def post_proc_node(self, value: FieldGFF[int] | int):
        if isinstance(value, int):
            value = FieldGFF(GFFFieldType.Int32, value)
        self._fields["PostProcNode"] = value

    @property
    def record_no_vo_override(self) -> int: return self._fields["RecordNoVOOverri"].value()
    @record_no_vo_override.setter
    def record_no_vo_override(self, value: FieldGFF[int] | int):
        if isinstance(value, int):
            value = FieldGFF(GFFFieldType.Int32, value)
        self._fields["RecordNoVOOverri"] = value

    @property
    def record_vo(self) -> int: return self._fields["RecordVO"].value()
    @record_vo.setter
    def record_vo(self, value: FieldGFF[int] | int):
        if isinstance(value, int):
            value = FieldGFF(GFFFieldType.Int32, value)
        self._fields["RecordVO"] = value

    @property
    def camera_id(self) -> int: return self._fields["CameraID"].value()
    @camera_id.setter
    def camera_id(self, value: FieldGFF[int] | int):
        if isinstance(value, int):
            value = FieldGFF(GFFFieldType.Int32, value)
        self._fields["CameraID"] = value

    @property
    def camera_effect(self) -> int: return self._fields["CamVidEffect"].value()
    @camera_effect.setter
    def camera_effect(self, value: FieldGFF[int] | int):
        if isinstance(value, int):
            value = FieldGFF(GFFFieldType.Int32, value)
        self._fields["CamVidEffect"] = value

    @property
    def listener(self) -> str: return self._fields["Listener"].value()
    @listener.setter
    def listener(self, value: FieldGFF[str]):
        self._fields["Listener"] = value

    @property
    def alien_race_node(self) -> int: return self._fields["AlienRaceNode"].value()
    @alien_race_node.setter
    def alien_race_node(self, value: FieldGFF[int]):
        self._fields["AlienRaceNode"] = value

    @property
    def vo_resref(self) -> ResRef: return self._fields["VO_ResRef"].value()
    @vo_resref.setter
    def vo_resref(self, value: FieldGFF[ResRef] | ResRef | str):
        if isinstance(value, ResRef):
            value = FieldGFF(GFFFieldType.ResRef, value)
        elif isinstance(value, str):
            value = FieldGFF(GFFFieldType.ResRef, ResRef(value))
        self._fields["VO_ResRef"] = value

    @property
    def script1(self) -> str: return self._fields["Script"].value()
    @script1.setter
    def script1(self, value: FieldGFF[str]):
        self._fields["Script"] = value

    @property
    def delay(self) -> int:
        overflow = -1
        value = self._fields["Delay"].value()
        return overflow if value == 4294967295 else value
    @delay.setter
    def delay(self, value: FieldGFF[int]):
        self._fields["Delay"] = value

    @property
    def comment(self) -> str: return self._fields["Comment"].value()
    @comment.setter
    def comment(self, value: FieldGFF[str]):
        self._fields["Comment"] = value

    @property
    def sound(self) -> str: return self._fields["Sound"].value()
    @sound.setter
    def sound(self, value: FieldGFF[str]):
        self._fields["Sound"] = value

    @property
    def quest(self) -> str: return self._fields["Quest"].value()
    @quest.setter
    def quest(self, value: FieldGFF[str]):
        self._fields["Quest"] = value

    @property
    def plot_index(self) -> int: return self._fields["PlotIndex"].value()
    @plot_index.setter
    def plot_index(self, value: FieldGFF[int]):
        self._fields["PlotIndex"] = value

    @property
    def plot_xp_percentage(self) -> float: return self._fields["PlotXPPercentage"].value()
    @plot_xp_percentage.setter
    def plot_xp_percentage(self, value: FieldGFF[float]):
        self._fields["PlotXPPercentage"] = value

    @property
    def wait_flags(self) -> int: return self._fields["WaitFlags"].value()
    @wait_flags.setter
    def wait_flags(self, value: FieldGFF[int]):
        self._fields["WaitFlags"] = value

    @property
    def camera_angle(self) -> int: return self._fields["CameraAngle"].value()
    @camera_angle.setter
    def camera_angle(self, value: FieldGFF[int]):
        self._fields["CameraAngle"] = value

    @property
    def fade_type(self) -> int: return self._fields["FadeType"].value()
    @fade_type.setter
    def fade_type(self, value: FieldGFF[int]):
        self._fields["FadeType"] = value

    @property
    def sound_exists(self) -> bool: return bool(self._fields.get("SoundExists", self.FIELDS["SoundExists"]).value())
    @sound_exists.setter
    def sound_exists(self, value: FieldGFF[int] | int | bool):
        if isinstance(value, FieldGFF):
            self._fields["SoundExists"] = value
        else:
            self._fields["SoundExists"] = FieldGFF(GFFFieldType.UInt8, int(value))

    @property
    def vo_text_changed(self) -> bool: return bool(self._fields["VOTextChanged"].value())
    @vo_text_changed.setter
    def vo_text_changed(self, value: FieldGFF[int] | int | bool):
        if isinstance(value, FieldGFF):
            self._fields["VOTextChanged"] = value
        else:
            self._fields["VOTextChanged"] = FieldGFF(GFFFieldType.UInt8, int(value))

    # KotOR 2 specific fields
    @property
    def script1_param1(self) -> int: return self._fields["ActionParam1"].value()
    @script1_param1.setter
    def script1_param1(self, value: FieldGFF[int]):
        self._fields["ActionParam1"] = value

    @property
    def script1_param2(self) -> int: return self._fields["ActionParam2"].value()
    @script1_param2.setter
    def script1_param2(self, value: FieldGFF[int]):
        self._fields["ActionParam2"] = value

    @property
    def script1_param3(self) -> int: return self._fields["ActionParam3"].value()
    @script1_param3.setter
    def script1_param3(self, value: FieldGFF[int]):
        self._fields["ActionParam3"] = value

    @property
    def script1_param4(self) -> int: return self._fields["ActionParam4"].value()
    @script1_param4.setter
    def script1_param4(self, value: FieldGFF[int]):
        self._fields["ActionParam4"] = value

    @property
    def script1_param5(self) -> int: return self._fields["ActionParam5"].value()
    @script1_param5.setter
    def script1_param5(self, value: FieldGFF[int]):
        self._fields["ActionParam5"] = value

    @property
    def script1_param6(self) -> str: return self._fields["ActionParamStrA"].value()
    @script1_param6.setter
    def script1_param6(self, value: FieldGFF[str]):
        self._fields["ActionParamStrA"] = value

    @property
    def script2(self) -> ResRef: return self._fields["Script2"].value()
    @script2.setter
    def script2(self, value: FieldGFF[ResRef] | ResRef | str):
        if isinstance(value, ResRef):
            value = FieldGFF(GFFFieldType.ResRef, value)
        elif isinstance(value, str):
            value = FieldGFF(GFFFieldType.ResRef, ResRef(value))
        self._fields["Script2"] = value

    @property
    def script2_param1(self) -> int: return self._fields["ActionParam1b"].value()
    @script2_param1.setter
    def script2_param1(self, value: FieldGFF[int]):
        self._fields["ActionParam1b"] = value

    @property
    def script2_param2(self) -> int: return self._fields["ActionParam2b"].value()
    @script2_param2.setter
    def script2_param2(self, value: FieldGFF[int]):
        self._fields["ActionParam2b"] = value

    @property
    def script2_param3(self) -> int: return self._fields["ActionParam3b"].value()
    @script2_param3.setter
    def script2_param3(self, value: FieldGFF[int]):
        self._fields["ActionParam3b"] = value

    @property
    def script2_param4(self) -> int: return self._fields["ActionParam4b"].value()
    @script2_param4.setter
    def script2_param4(self, value: FieldGFF[int]):
        self._fields["ActionParam4b"] = value

    @property
    def script2_param5(self) -> int: return self._fields["ActionParam5b"].value()
    @script2_param5.setter
    def script2_param5(self, value: FieldGFF[int]):
        self._fields["ActionParam5b"] = value

    @property
    def script2_param6(self) -> str: return self._fields["ActionParamStrB"].value()
    @script2_param6.setter
    def script2_param6(self, value: FieldGFF[str]):
        self._fields["ActionParamStrB"] = value

    def __repr__(
        self,
    ):
        return str(self.text.get(Language.ENGLISH, Gender.MALE))

class DLGReplyFields(TypedDict):
    EntriesList: FieldGFF[GFFList[DLGLink]]

class DLGReply(DLGNode):
    """Replies are nodes that are responses by the player."""

    FIELDS: ClassVar[dict[str, FieldGFF]] = {
        **DLGNode.FIELDS,
        "EntriesList": FieldGFF(GFFFieldType.List, GFFList()),
    }
    K2_FIELDS: ClassVar[dict[str, FieldGFF]] = {
        **DLGNode.K2_FIELDS
    }

    def __init__(
        self,
    ) -> None:
        super().__init__()
        self._fields: DLGReplyFields

    @property
    def links(self) -> GFFList[DLGLink]: return self._fields["EntriesList"].value()
    @links.setter
    def links(self, value: FieldGFF[GFFList[DLGLink]]):
        self["EntriesList"] = value


class DLGEntryFields(TypedDict):
    Speaker: FieldGFF[str]
    RepliesList: FieldGFF[GFFList[DLGLink]]

class DLGEntry(DLGNode):
    """Entries are nodes that are responses by NPCs."""

    FIELDS: ClassVar[dict[str, FieldGFF]] = {
        **DLGNode.FIELDS,
        "Speaker": FieldGFF(GFFFieldType.String, ""),
        "RepliesList": FieldGFF(GFFFieldType.List, GFFList()),
    }
    K2_FIELDS: ClassVar[dict[str, FieldGFF]] = {
        **DLGNode.K2_FIELDS
    }

    def __init__(
        self,
    ) -> None:
        super().__init__()
        self._fields: DLGEntryFields

    @property
    def speaker(self) -> str: return self._fields.get("Speaker", self.FIELDS["Speaker"]).value()
    @speaker.setter
    def speaker(self, value):
        self._fields["Speaker"] = value

    @property
    def links(self) -> GFFList[DLGLink]: return self._fields["RepliesList"].value()
    @links.setter
    def links(self, value: FieldGFF[GFFList[DLGLink]]):
        self["RepliesList"] = value


class DLGAnimationFields(TypedDict):
    Animation: FieldGFF[int]
    Participant: FieldGFF[str]


class DLGAnimation(GFFStructInterface):
    """Represents a unit of animation executed during a node."""

    FIELDS: ClassVar[dict[str, FieldGFF]] = {
        "Animation": FieldGFF(GFFFieldType.UInt32, 6),
        "Participant": FieldGFF(GFFFieldType.String, ""),
    }
    K2_FIELDS: ClassVar[dict[str, FieldGFF]] = {}

    def __init__(
        self,
    ) -> None:
        super().__init__()
        self._fields: DLGAnimationFields

    @property
    def animation_id(self) -> int: return self._fields.get("Animation", self.FIELDS["Animation"]).value()
    @animation_id.setter
    def animation_id(self, value: FieldGFF[int]) -> None:
        self._fields["Animation"] = value

    @property
    def participant(self) -> str: return self._fields.get("Participant", self.FIELDS["Participant"]).value()
    @participant.setter
    def participant(self, value: FieldGFF[str]):
        self._fields["Participant"] = value


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

    FIELDS: ClassVar[dict[str, FieldGFF]] = {
        "Active": FieldGFF(GFFFieldType.ResRef, ResRef.from_blank()),

        # not in StartingList
        "LinkComment": FieldGFF(GFFFieldType.String, ""),
        "IsChild": FieldGFF(GFFFieldType.UInt8, 0),
        "Index": FieldGFF(GFFFieldType.UInt32, 0),
    }

    K2_FIELDS: ClassVar[dict[str, FieldGFF]] = {
        "Active2": FieldGFF(GFFFieldType.ResRef, ResRef.from_blank()),
        "Logic": FieldGFF(GFFFieldType.Int32, 0),
        "Not": FieldGFF(GFFFieldType.UInt8, 0),
        "Not2": FieldGFF(GFFFieldType.UInt8, 0),
        "Param1": FieldGFF(GFFFieldType.Int32, 0),
        "Param2": FieldGFF(GFFFieldType.Int32, 0),
        "Param3": FieldGFF(GFFFieldType.Int32, 0),
        "Param4": FieldGFF(GFFFieldType.Int32, 0),
        "Param5": FieldGFF(GFFFieldType.Int32, 0),
        "ParamStrA": FieldGFF(GFFFieldType.String, ""),
        "Param1b": FieldGFF(GFFFieldType.Int32, 0),
        "Param2b": FieldGFF(GFFFieldType.Int32, 0),
        "Param3b": FieldGFF(GFFFieldType.Int32, 0),
        "Param4b": FieldGFF(GFFFieldType.Int32, 0),
        "Param5b": FieldGFF(GFFFieldType.Int32, 0),
        "ParamStrB": FieldGFF(GFFFieldType.String, ""),
    }

    def __init__(
        self,
        node: DLGNode
    ):
        super().__init__()
        self._fields: DLGLinkFields
        self._node: DLGNode = node

    @property
    def link_index(self) -> int: return self._fields["Index"].value()
    @link_index.setter
    def link_index(self, value: FieldGFF[int]):
        self._fields["Index"] = value

    @property
    def active1(self) -> ResRef: return self._fields.get("Active", self.FIELDS["Active"]).value()
    @active1.setter
    def active1(self, value):
        self._fields["Active"] = value

    @property
    def is_child(self) -> bool: return bool(self._fields.get("Active", self.FIELDS["Active"]).value())
    @is_child.setter
    def is_child(self, value):
        self._fields["IsChild"] = value

    @property
    def comment(self) -> str: return self._fields.get("LinkComment", self.FIELDS["LinkComment"]).value()
    @comment.setter
    def comment(self, value):
        self._fields["LinkComment"] = value

    @property
    def active2(self) -> ResRef: return self._fields.get("Active2", self.K2_FIELDS["Active2"]).value()
    @active2.setter
    def active2(self, value):
        self._fields["Active2"] = value

    @property
    def active1_not(self) -> bool: return bool(self._fields.get("Not", self.K2_FIELDS["Not"]).value())
    @active1_not.setter
    def active1_not(self, value):
        self._fields["Not"] = value

    @property
    def active2_not(self) -> bool: return bool(self._fields.get("Not2", self.K2_FIELDS["Not2"]).value())
    @active2_not.setter
    def active2_not(self, value):
        self._fields["Not2"] = value

    @property
    def logic(self) -> bool: return bool(self._fields.get("Param1", self.K2_FIELDS["Logic"]).value())
    @logic.setter
    def logic(self, value):
        self._fields["Logic"] = value

    @property
    def active1_param1(self) -> int: return self._fields.get("Param1", self.K2_FIELDS["Param1"]).value()
    @active1_param1.setter
    def active1_param1(self, value):
        self._fields["Param1"] = value

    @property
    def active1_param2(self) -> int: return self._fields.get("Param2", self.K2_FIELDS["Param2"]).value()
    @active1_param2.setter
    def active1_param2(self, value):
        self._fields["Param2"] = value

    @property
    def active1_param3(self) -> int: return self._fields.get("Param3", self.K2_FIELDS["Param3"]).value()
    @active1_param3.setter
    def active1_param3(self, value):
        self._fields["Param3"] = value

    @property
    def active1_param4(self) -> int: return self._fields.get("Param4", self.K2_FIELDS["Param4"]).value()
    @active1_param4.setter
    def active1_param4(self, value):
        self._fields["Param4"] = value

    @property
    def active1_param5(self) -> int: return self._fields.get("Param5", self.K2_FIELDS["Param5"]).value()
    @active1_param5.setter
    def active1_param5(self, value):
        self._fields["Param5"] = value

    @property
    def active1_param6(self) -> str: return self._fields.get("ParamStrA", self.K2_FIELDS["ParamStrA"]).value()
    @active1_param6.setter
    def active1_param6(self, value):
        self._fields["ParamStrA"] = value

    @property
    def active2_param1(self) -> int: return self._fields.get("Param1b", self.K2_FIELDS["Param1b"]).value()
    @active2_param1.setter
    def active2_param1(self, value):
        self._fields["Param1b"] = value

    @property
    def active2_param2(self) -> int: return self._fields.get("Param2b", self.K2_FIELDS["Param2b"]).value()
    @active2_param2.setter
    def active2_param2(self, value):
        self._fields["Param2b"] = value

    @property
    def active2_param3(self) -> int: return self._fields.get("Param3b", self.K2_FIELDS["Param3b"]).value()
    @active2_param3.setter
    def active2_param3(self, value):
        self._fields["Param3b"] = value

    @property
    def active2_param4(self) -> int: return self._fields.get("Param4b", self.K2_FIELDS["Param4b"]).value()
    @active2_param4.setter
    def active2_param4(self, value):
        self._fields["Param4b"] = value

    @property
    def active2_param5(self) -> int: return self._fields.get("Param5b", self.K2_FIELDS["Param5b"]).value()
    @active2_param5.setter
    def active2_param5(self, value):
        self._fields["Param5b"] = value

    @property
    def active2_param6(self) -> str: return self._fields.get("ParamStrB", self.K2_FIELDS["ParamStrB"]).value()
    @active2_param6.setter
    def active2_param6(self, value):
        self._fields["ParamStrB"] = value


class DLGStuntFields(TypedDict):
    Participant: FieldGFF[str]
    StuntModel: FieldGFF[ResRef]

class DLGStunt(GFFStructInterface):
    FIELDS: ClassVar[dict[str, FieldGFF]] = {
        "Participant": FieldGFF(GFFFieldType.String, ""),
        "StuntModel": FieldGFF(GFFFieldType.ResRef, ResRef.from_blank()),
    }
    K2_FIELDS: ClassVar[dict[str, FieldGFF]] = {}

    def __init__(
        self,
    ) -> None:
        super().__init__()
        self._fields: DLGStuntFields

    @property
    def participant(self) -> str: return self._fields.get("Participant", self.FIELDS["Participant"]).value()
    @participant.setter
    def participant(self, value: FieldGFF[str]):
        self._fields["Participant"] = value

    @property
    def stunt_model(self) -> ResRef: return self._fields.get("StuntModel", self.FIELDS["StuntModel"]).value()
    @stunt_model.setter
    def stunt_model(self, value: FieldGFF[ResRef] | ResRef | str):
        if isinstance(value, ResRef):
            value = FieldGFF(GFFFieldType.ResRef, value)
        elif isinstance(value, str):
            value = FieldGFF(GFFFieldType.ResRef, ResRef(value))
        self._fields["StuntModel"] = value


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

    dlg: DLG = deepcopy(gff.root)  # type: ignore[assignment]
    dlg.__class__ = DLG
    all_entries: list[DLGEntry] = dlg.acquire("EntryList", GFFList())
    all_replies: list[DLGEntry] = dlg.acquire("ReplyList", GFFList())

    stunt: DLGStunt
    for stunt in dlg.stunts:
        stunt.__class__ = DLGStunt

    starter: DLGLink
    for starter in dlg.starters:
        construct_link(starter, all_entries)

    reply_link: DLGLink
    entry: DLGEntry
    for i, entry in enumerate(dlg["EntryList"].value()):
        entry.__class__ = DLGEntry
        entry.list_index = i
        for reply_link in entry["RepliesList"].value():
            construct_link(reply_link, all_replies)
            entry.links.append(reply_link)

    entry_link: DLGLink
    reply: DLGReply
    for i, reply in enumerate(dlg["ReplyList"].value()):
        reply.__class__ = DLGReply
        reply.list_index = i
        for entry_link in reply["EntriesList"].value():
            construct_link(entry_link, all_entries)
            reply.links.append(entry_link)
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
        del node.__dict__["list_index"]

    def dismantle_link(link: DLGLink):
        del link.__dict__["_node"]
        link.__class__ = GFFStruct

    gff: GFF = GFF(GFFContent.DLG)
    gff.root = deepcopy(dlg)
    gff.root.__class__ = GFFStruct  # type: ignore[assignment]
    if hasattr(gff.root, "_all_fields"):
        del gff.root.__dict__["_all_fields"]

    stunt: DLGStunt
    for stunt in gff.root["StuntList"].value():
        stunt.__class__ = GFFStruct

    starter: DLGLink
    for starter in gff.root["StartingList"].value():
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
