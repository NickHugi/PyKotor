from __future__ import annotations

import uuid

from enum import IntEnum
from typing import TYPE_CHECKING, Any

from pykotor.common.geometry import Vector3
from pykotor.common.language import Gender, Language, LocalizedString
from pykotor.common.misc import Color, Game, ResRef
from pykotor.resource.formats.gff.gff_auto import bytes_gff, read_gff, write_gff
from pykotor.resource.formats.gff.gff_data import GFF, GFFContent, GFFList
from pykotor.resource.type import ResourceType
from utility.logger_util import RobustRootLogger

if TYPE_CHECKING:
    from typing_extensions import Literal, Self

    from pykotor.extract.installation import Installation
    from pykotor.resource.formats.gff.gff_data import GFFStruct
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class DLG:
    """Stores dialog data.

    Attributes:
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

    def __init__(
        self,
        blank_node: bool = True,
    ):
        """Initializes a DLGNode object.

        Args:
        ----
            blank_node (bool): Whether to add a blank starter node

        Processing Logic:
        ----------------
            1. Initializes starter and stunt lists
            2. Sets default values for node properties
            3. Adds a blank starter node if blank_node is True
            4. Sets deprecated properties for backwards compatibility.
        """
        self.starters: list[DLGLink] = []
        self.stunts: list[DLGStunt] = []

        if blank_node:
            # Add bare minimum to be openable by DLGEditor
            starter = DLGLink()
            entry = DLGEntry()
            entry.text.set_data(Language.ENGLISH, Gender.MALE, "")
            starter.node = entry
            self.starters.append(starter)

        self.ambient_track: ResRef = ResRef.from_blank()
        self.animated_cut: int = 0
        self.camera_model: ResRef = ResRef.from_blank()
        self.computer_type: DLGComputerType = DLGComputerType.Modern
        self.conversation_type: DLGConversationType = DLGConversationType.Human
        self.on_abort: ResRef = ResRef.from_blank()
        self.on_end: ResRef = ResRef.from_blank()
        self.word_count: int = 0
        self.old_hit_check: bool = False
        self.skippable: bool = False
        self.unequip_items: bool = False
        self.unequip_hands: bool = False
        self.vo_id: str = ""

        # KotOR 2:
        self.alien_race_owner: int = 0
        self.next_node_id: int = 0
        self.post_proc_owner: int = 0
        self.record_no_vo: int = 0

        # Deprecated:
        self.delay_entry: int = 0
        self.delay_reply: int = 0

    def __copy__(self) -> Self:
        return self.__class__.from_dict(self.to_dict())

    def __deepcopy__(self, memo: dict[str, Any]) -> Self:
        if id(self) in memo:
            return memo[id(self)]
        copied_obj = self.__class__.from_dict(self.to_dict())
        memo[id(self)] = copied_obj
        return copied_obj

    def to_dict(self) -> dict:
        node_map = {}
        data = {
            "ambient_track": str(self.ambient_track),
            "animated_cut": self.animated_cut,
            "camera_model": str(self.camera_model),
            "computer_type": self.computer_type.value,
            "conversation_type": self.conversation_type.value,
            "on_abort": str(self.on_abort),
            "on_end": str(self.on_end),
            "word_count": self.word_count,
            "old_hit_check": self.old_hit_check,
            "skippable": self.skippable,
            "unequip_items": self.unequip_items,
            "unequip_hands": self.unequip_hands,
            "vo_id": self.vo_id,
            "alien_race_owner": self.alien_race_owner,
            "next_node_id": self.next_node_id,
            "post_proc_owner": self.post_proc_owner,
            "record_no_vo": self.record_no_vo,
            "delay_entry": self.delay_entry,
            "delay_reply": self.delay_reply,
            "starters": [link.to_dict(node_map) for link in self.starters],
            "stunts": [stunt.to_dict() for stunt in self.stunts],
        }
        return data

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        dlg = cls(blank_node=False)
        node_map = {}

        dlg.ambient_track = ResRef(data["ambient_track"])
        dlg.animated_cut = data["animated_cut"]
        dlg.camera_model = ResRef(data["camera_model"])
        dlg.computer_type = DLGComputerType(data["computer_type"])
        dlg.conversation_type = DLGConversationType(data["conversation_type"])
        dlg.on_abort = ResRef(data["on_abort"])
        dlg.on_end = ResRef(data["on_end"])
        dlg.word_count = data["word_count"]
        dlg.old_hit_check = data["old_hit_check"]
        dlg.skippable = data["skippable"]
        dlg.unequip_items = data["unequip_items"]
        dlg.unequip_hands = data["unequip_hands"]
        dlg.vo_id = data["vo_id"]
        dlg.alien_race_owner = data["alien_race_owner"]
        dlg.next_node_id = data["next_node_id"]
        dlg.post_proc_owner = data["post_proc_owner"]
        dlg.record_no_vo = data["record_no_vo"]
        dlg.delay_entry = data["delay_entry"]
        dlg.delay_reply = data["delay_reply"]

        dlg.starters = [DLGLink.from_dict(link_data, node_map) for link_data in data["starters"]]
        dlg.stunts = [DLGStunt.from_dict(stunt_data) for stunt_data in data["stunts"]]

        return dlg

    def print_tree(
        self,
        install: Installation | None = None,
    ):
        """Prints all the nodes (one per line) in the dialog tree with appropriate indentation."""
        self._print_tree(self.starters, install, 0, [], [])

    def _print_tree(
        self,
        links: list[DLGLink],
        install: Installation | None,
        indent: int,
        seen_links: list[DLGLink],
        seen_nodes: list[DLGNode],
    ):
        for link in links:
            text = link.node.text if install is None else install.string(link.node.text)
            if link.node not in seen_nodes:
                print(f'{" " * indent}-> {text}')
                seen_links.append(link)

                if link.node not in seen_nodes:
                    seen_nodes.append(link.node)
                    self._print_tree(
                        link.node.links,
                        install,
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

        Returns:
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
        entries: list[DLGEntry] = []

        links = self.starters if links is None else links
        seen_entries = [] if seen_entries is None else seen_entries

        for link in links:
            entry: DLGNode = link.node
            if entry not in seen_entries:  # sourcery skip: class-extract-method
                assert isinstance(entry, DLGEntry), f"{type(entry).__name__}: {entry}"  # noqa: S101
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

        links = [_ for link in self.starters for _ in link.node.links] if links is None else links
        seen_replies = [] if seen_replies is None else seen_replies

        for link in links:
            reply = link.node
            if reply not in seen_replies:  # sourcery skip: class-extract-method
                assert isinstance(reply, DLGReply), f"{type(reply).__name__}: {reply}"  # noqa: S101
                replies.append(reply)
                seen_replies.append(reply)
                for entry_link in reply.links:
                    entry: DLGNode | None = entry_link.node
                    replies.extend(self._all_replies(entry.links, seen_replies))

        return replies


class DLGComputerType(IntEnum):
    Modern = 0
    Ancient = 1


class DLGConversationType(IntEnum):
    Human = 0
    Computer = 1
    Other = 2


class DLGNode:
    def __init__(
        self,
    ):
        """Initializes a DLGNode object.

        Processing Logic:
        ----------------
            - Sets default values for all properties of a DLGNode object
            - Initializes lists and optional properties as empty/None
            - Sets flags and identifiers to default values
        """
        if not isinstance(self, (DLGEntry, DLGNode)):
            raise RuntimeError("Cannot construct base class DLGNode: use DLGEntry or DLGReply instead.")  # noqa: TRY004

        self._uuid = uuid.uuid4().hex
        self.comment: str = ""
        self.links: list[DLGLink] = []
        self.list_index: int = -1

        self.camera_angle: int = 0
        self.delay: int = -1
        self.fade_type: int = 0
        self.listener: str = ""
        self.plot_index: int = 0
        self.plot_xp_percentage: float = 0.0
        self.quest: str = ""
        self.script1: ResRef = ResRef.from_blank()
        self.sound: ResRef = ResRef.from_blank()
        self.sound_exists: bool = False
        self.text: LocalizedString = LocalizedString.from_invalid()
        self.vo_resref: ResRef = ResRef.from_blank()
        self.wait_flags: int = 0

        self.animations: list[DLGAnimation] = []

        self.quest_entry: int | None = 0
        self.fade_color: Color | None = None
        self.fade_delay: float | None = None
        self.fade_length: float | None = None
        self.camera_anim: int | None = None
        self.camera_id: int | None = None
        self.camera_fov: float | None = None
        self.camera_height: float | None = None
        self.camera_effect: int | None = None
        self.target_height: float | None = None

        # KotOR 2:
        self.script1_param1: int = 0
        self.script1_param2: int = 0
        self.script1_param3: int = 0
        self.script1_param4: int = 0
        self.script1_param5: int = 0
        self.script1_param6: str = ""
        self.script2_param1: int = 0

        self.script2: ResRef = ResRef.from_blank()
        self.script2_param2: int = 0
        self.script2_param3: int = 0
        self.script2_param4: int = 0
        self.script2_param5: int = 0
        self.script2_param6: str = ""

        self.alien_race_node: int = 0
        self.emotion_id: int = 0
        self.facial_id: int = 0
        self.unskippable: bool = False
        self.node_id: int = 0
        self.post_proc_node: int = 0

        self.record_no_vo_override: bool = False
        self.record_vo: bool = False
        self.vo_text_changed: bool = False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DLGNode):
            return NotImplemented
        if self.__class__ != other.__class__:
            return False
        return (
            self.comment == other.comment
            and self.links == other.links
            and self.list_index == other.list_index
            and self.camera_angle == other.camera_angle
            and self.delay == other.delay
            and self.fade_type == other.fade_type
            and self.listener == other.listener
            and self.plot_index == other.plot_index
            and self.plot_xp_percentage == other.plot_xp_percentage
            and self.quest == other.quest
            and self.script1 == other.script1
            and self.sound == other.sound
            and self.sound_exists == other.sound_exists
            and self.text == other.text
            and self.vo_resref == other.vo_resref
            and self.wait_flags == other.wait_flags
            and self.animations == other.animations
            and self.quest_entry == other.quest_entry
            and self.fade_color == other.fade_color
            and self.fade_delay == other.fade_delay
            and self.fade_length == other.fade_length
            and self.camera_anim == other.camera_anim
            and self.camera_id == other.camera_id
            and self.camera_fov == other.camera_fov
            and self.camera_height == other.camera_height
            and self.camera_effect == other.camera_effect
            and self.target_height == other.target_height
            and self.script1_param1 == other.script1_param1
            and self.script1_param2 == other.script1_param2
            and self.script1_param3 == other.script1_param3
            and self.script1_param4 == other.script1_param4
            and self.script1_param5 == other.script1_param5
            and self.script1_param6 == other.script1_param6
            and self.script2_param1 == other.script2_param1
            and self.script2 == other.script2
            and self.script2_param2 == other.script2_param2
            and self.script2_param3 == other.script2_param3
            and self.script2_param4 == other.script2_param4
            and self.script2_param5 == other.script2_param5
            and self.script2_param6 == other.script2_param6
            and self.alien_race_node == other.alien_race_node
            and self.emotion_id == other.emotion_id
            and self.facial_id == other.facial_id
            and self.unskippable == other.unskippable
            and self.node_id == other.node_id
            and self.post_proc_node == other.post_proc_node
            and self.record_no_vo_override == other.record_no_vo_override
            and self.record_vo == other.record_vo
            and self.vo_text_changed == other.vo_text_changed
            and getattr(self, "speaker", None) == getattr(other, "speaker", None)
        )

    def __repr__(
        self,
    ) -> str:
        text = self.text.get(Language.ENGLISH, Gender.MALE, use_fallback=True)
        strref_display = f"stringref={self.text.stringref}" if text is None else f"text={text}"
        return f"{self.__class__.__name__}({strref_display}, list_index={self.list_index}, links={self.links})"

    def __copy__(self) -> DLGNode:
        return self.__class__.from_dict(self.to_dict())

    def __deepcopy__(self, memo: dict[str, Any]) -> DLGNode:
        if id(self) in memo:
            return memo[id(self)]
        copied_obj = self.__class__.from_dict(self.to_dict())
        memo[id(self)] = copied_obj
        return copied_obj

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(comment={self.comment}, links={self.links}, "
            f"list_index={self.list_index}, camera_angle={self.camera_angle}, delay={self.delay}, "
            f"fade_type={self.fade_type}, listener={self.listener}, plot_index={self.plot_index}, "
            f"plot_xp_percentage={self.plot_xp_percentage}, quest={self.quest}, script1={self.script1}, "
            f"sound={self.sound}, sound_exists={self.sound_exists}, text={self.text}, "
            f"vo_resref={self.vo_resref}, wait_flags={self.wait_flags}, animations={self.animations}, "
            f"quest_entry={self.quest_entry}, fade_color={self.fade_color}, fade_delay={self.fade_delay}, "
            f"fade_length={self.fade_length}, camera_anim={self.camera_anim}, camera_id={self.camera_id}, "
            f"camera_fov={self.camera_fov}, camera_height={self.camera_height}, camera_effect={self.camera_effect}, "
            f"target_height={self.target_height}, script1_param1={self.script1_param1}, script1_param2={self.script1_param2}, "
            f"script1_param3={self.script1_param3}, script1_param4={self.script1_param4}, script1_param5={self.script1_param5}, "
            f"script1_param6={self.script1_param6}, script2_param1={self.script2_param1}, script2={self.script2}, "
            f"script2_param2={self.script2_param2}, script2_param3={self.script2_param3}, script2_param4={self.script2_param4}, "
            f"script2_param5={self.script2_param5}, script2_param6={self.script2_param6}, alien_race_node={self.alien_race_node}, "
            f"emotion_id={self.emotion_id}, facial_id={self.facial_id}, unskippable={self.unskippable}, node_id={self.node_id}, "
            f"post_proc_node={self.post_proc_node}, record_no_vo_override={self.record_no_vo_override}, "
            f"record_vo={self.record_vo}, vo_text_changed={self.vo_text_changed})"
        )

    def add_node(
        self,
        target_links: list[DLGLink],
        source: DLGNode,
    ):
        newLink = DLGLink(source)
        target_links.append(newLink)

    def shift_item(
        self,
        links: list[DLGLink],
        old_index: int,
        new_index: int,
    ):
        if 0 <= new_index < len(links):
            link = links.pop(old_index)
            links.insert(new_index, link)
        else:
            raise IndexError(new_index)

    def get_node_key(self) -> str:
        """Generate a unique key for the node using UUID."""
        if not hasattr(self, "_uuid"):
            self._uuid = uuid.uuid4().hex
        return self._uuid

    def to_dict(self, node_map: dict[str, Any] | None = None) -> dict:
        if node_map is None:
            node_map = {}

        node_key = self.get_node_key()
        if node_key in node_map:
            return {"type": self.__class__.__name__, "ref": node_key}

        node_dict = {"type": self.__class__.__name__, "key": node_key, "data": {}}
        node_map[node_key] = node_dict

        for key, value in self.__dict__.items():
            if key.startswith("__"):  # ignore python built-in attrs
                continue
            if key == "links":
                node_dict["data"][key] = {"value": [link.to_dict(node_map) for link in value], "py_type": "list"}
            elif isinstance(value, bool):
                node_dict["data"][key] = {"value": int(value), "py_type": "bool"}
            elif isinstance(value, int):
                node_dict["data"][key] = {"value": value, "py_type": "int"}
            elif isinstance(value, float):
                node_dict["data"][key] = {"value": value, "py_type": "float"}
            elif isinstance(value, str):
                node_dict["data"][key] = {"value": value, "py_type": "str"}
            elif isinstance(value, ResRef):
                node_dict["data"][key] = {"value": str(value), "py_type": "ResRef"}
            elif isinstance(value, Color):
                node_dict["data"][key] = {"value": value.bgr_integer(), "py_type": "Color"}
            elif isinstance(value, LocalizedString):
                node_dict["data"][key] = {"value": value.to_dict(), "py_type": "LocalizedString"}
            elif isinstance(value, list) and all(isinstance(item, DLGAnimation) for item in value):
                node_dict["data"][key] = {"value": [anim.to_dict() for anim in value], "py_type": "list"}
            elif isinstance(value, list):
                node_dict["data"][key] = {"value": value, "py_type": "list"}
            elif value is None:
                node_dict["data"][key] = {"value": None, "py_type": "None"}
            else:
                raise ValueError(f"Unsupported type: {type(value)} for key: {key}")

        return node_dict

    @staticmethod
    def from_dict(data: dict[str, Any], node_map: dict[str, Any] | None = None) -> DLGNode:
        if node_map is None:
            node_map = {}

        if "ref" in data:
            return node_map[data["ref"]]

        node_key = data.get("key")
        node_type: Literal["DLGEntry", "DLGReply"] | None = data.get("type")
        node_data: dict[str, Any] = data.get("data", {})

        if node_type == "DLGEntry":
            node = DLGEntry()
            node.speaker = node_data.pop("speaker", {"value": ""})["value"]
        elif node_type == "DLGReply":
            node = DLGReply()
        else:
            raise ValueError(f"Unknown node type: {node_type}")

        node._uuid = node_key
        node_map[node_key] = node

        for key, value in node_data.items():
            if value is None:
                continue
            py_type = value.get("py_type")
            actual_value = value.get("value")

            if py_type == "str":
                setattr(node, key, actual_value)
            elif py_type == "int":
                setattr(node, key, int(actual_value))
            elif py_type == "float":
                setattr(node, key, float(actual_value))
            elif py_type == "bool":
                setattr(node, key, bool(actual_value))
            elif py_type == "ResRef":
                setattr(node, key, ResRef(actual_value))
            elif py_type == "Color":
                setattr(node, key, Color.from_bgr_integer(actual_value))
            elif py_type == "LocalizedString":
                node.text = LocalizedString.from_dict(actual_value)
            elif py_type == "list" and key == "links":
                node.links = [DLGLink.from_dict(link, node_map) for link in actual_value]
            elif py_type == "list" and key == "animations":
                node.animations = [DLGAnimation.from_dict(anim) for anim in actual_value]
            elif py_type == "list":
                setattr(node, key, actual_value)
            elif py_type == "None" or actual_value == "None":
                setattr(node, key, None)
            else:
                raise ValueError(f"Unsupported type: {py_type} for key: {key}")

        return node


class DLGReply(DLGNode):
    """Replies are nodes that are responses by the player."""

    def __init__(
        self,
        **kwargs,
    ):
        super().__init__()
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __eq__(self, other: object) -> bool:
        # sourcery skip: assign-if-exp, reintroduce-else, swap-if-else-branches
        if not isinstance(other, DLGReply):
            return NotImplemented
        return super().__eq__(other)


class DLGEntry(DLGNode):
    """Entries are nodes that are responses by NPCs."""

    def __init__(
        self,
        **kwargs,
    ):
        super().__init__()
        self.speaker: str = ""
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DLGEntry):
            return NotImplemented
        return super().__eq__(other) and self.speaker == other.speaker


class DLGAnimation:
    """Represents a unit of animation executed during a node."""

    def __init__(
        self,
    ):
        self.animation_id: int = 6
        self.participant: str = ""

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DLGAnimation):
            return NotImplemented
        return self.animation_id == other.animation_id and self.participant == other.participant

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(animation_id={self.animation_id}, participant={self.participant})"

    def __copy__(self) -> Self:
        return self.__class__.from_dict(self.to_dict())

    def __deepcopy__(self, memo: dict[str, Any]) -> Self:
        if id(self) in memo:
            return memo[id(self)]
        copied_obj = self.__class__.from_dict(self.to_dict())
        memo[id(self)] = copied_obj
        return copied_obj

    def to_dict(self) -> dict[str, Any]:
        return {"animation_id": self.animation_id, "participant": self.participant}

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        animation = cls()
        animation.animation_id = data.get("animation_id", 6)
        animation.participant = data.get("participant", "")
        return animation


class DLGLink:
    """Points to a node. Links are stored either in other nodes or in the starting list of the DLG.

    Attributes:
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

    def __init__(
        self,
        node: DLGNode | None = None,
    ):
        self.active1: ResRef = ResRef.from_blank()
        self.node: DLGNode | None = node
        self.link_index: int = -1

        # not in StartingList
        self.is_child: bool = False
        self.comment: str = ""

        # KotOR 2 Only:
        self.active2: ResRef = ResRef.from_blank()
        self.active1_not: bool = False
        self.active2_not: bool = False
        self.logic: bool = False

        self.active1_param1: int = 0
        self.active1_param2: int = 0
        self.active1_param3: int = 0
        self.active1_param4: int = 0
        self.active1_param5: int = 0
        self.active1_param6: str = ""

        self.active2_param1: int = 0
        self.active2_param2: int = 0
        self.active2_param3: int = 0
        self.active2_param4: int = 0
        self.active2_param5: int = 0
        self.active2_param6: str = ""

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(link_index={self.link_index}, node={self.node}, active1={self.active1}, "
            f"comment={self.comment}, is_child={self.is_child}, active2={self.active2}, active1_not={self.active1_not}, "
            f"active2_not={self.active2_not}, logic={self.logic}, active1_param1={self.active1_param1}, active1_param2={self.active1_param2}, "
            f"active1_param3={self.active1_param3}, active1_param4={self.active1_param4}, active1_param5={self.active1_param5}, "
            f"active1_param6={self.active1_param6}, active2_param1={self.active2_param1}, active2_param2={self.active2_param2}, "
            f"active2_param3={self.active2_param3}, active2_param4={self.active2_param4}, active2_param5={self.active2_param5}, "
            f"active2_param6={self.active2_param6})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DLGLink):
            return NotImplemented
        return (
            self.link_index == other.link_index
            and self.node.get_node_key() == other.node.get_node_key()
            and self.active1 == other.active1
            and self.comment == other.comment
            and self.is_child == other.is_child
            and self.active2 == other.active2
            and self.active1_not == other.active1_not
            and self.active2_not == other.active2_not
            and self.logic == other.logic
            and self.active1_param1 == other.active1_param1
            and self.active1_param2 == other.active1_param2
            and self.active1_param3 == other.active1_param3
            and self.active1_param4 == other.active1_param4
            and self.active1_param5 == other.active1_param5
            and self.active1_param6 == other.active1_param6
            and self.active2_param1 == other.active2_param1
            and self.active2_param2 == other.active2_param2
            and self.active2_param3 == other.active2_param3
            and self.active2_param4 == other.active2_param4
            and self.active2_param5 == other.active2_param5
            and self.active2_param6 == other.active2_param6
        )

    def get_node_key(self) -> str:
        """Generate a unique key for the node using UUID."""
        if not hasattr(self, "_uuid"):
            self._uuid = uuid.uuid4().hex
        return self._uuid

    def get_node_key(self) -> str:
        """Generate a unique key for the node using UUID."""
        if not hasattr(self, "_uuid"):
            self._uuid = uuid.uuid4().hex
        return self._uuid

    def __copy__(self) -> Self:
        return self.__class__.from_dict(self.to_dict())

    def __deepcopy__(self, memo: dict[str, Any]) -> Self:
        if id(self) in memo:
            return memo[id(self)]
        copied_obj = self.__class__.from_dict(self.to_dict())
        memo[id(self)] = copied_obj
        return copied_obj

    def to_dict(self, node_map: dict[str, Any] | None = None) -> dict[str, Any]:
        if node_map is None:
            node_map = {}

        node_key = self.get_node_key()
        if node_key in node_map:
            return {"type": self.__class__.__name__, "ref": node_key}

        link_dict = {
            "type": self.__class__.__name__,
            "key": node_key,
            "node": self.node.to_dict(node_map) if self.node else None,
            "link_index": self.link_index,
        }
        node_map[node_key] = link_dict

        return link_dict

    @classmethod
    def from_dict(cls, data: dict, node_map: dict[str, Any] | None = None) -> Self:
        if node_map is None:
            node_map = {}

        node_key = data["key"]

        if node_key in node_map:
            return node_map[node_key]

        link = cls()
        link._uuid = node_key  # noqa: SLF001
        node_map[node_key] = link

        link.link_index = data.get("link_index", -1)
        if data["node"]:
            link.node = DLGNode.from_dict(data["node"], node_map)

        return link


class DLGStunt:
    """
    Attributes:
    ----------
    participant: "Participant" field.
    stunt_model: "StuntModel" field.
    """  # noqa: D212, D415

    def __init__(
        self,
    ):
        self.participant: str = ""
        self.stunt_model: ResRef = ResRef.from_blank()

    def __copy__(self) -> Self:
        return self.__class__.from_dict(self.to_dict())

    def __deepcopy__(self, memo: dict[str, Any]) -> Self:
        if id(self) in memo:
            return memo[id(self)]
        copied_obj = self.__class__.from_dict(self.to_dict())
        memo[id(self)] = copied_obj
        return copied_obj

    def to_dict(self) -> dict[str, Any]:
        return {"participant": self.participant, "stunt_model": str(self.stunt_model)}

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        stunt = cls()
        stunt.participant = data.get("participant", "")
        stunt.stunt_model = ResRef(data.get("stunt_model", ""))
        return stunt


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

    def construct_node(
        gff_struct: GFFStruct,
        node: DLGNode,
    ):
        """Constructs a DLGNode from a GFFStruct.

        Args:
        ----
            gff_struct: GFFStruct - The GFFStruct to construct the node from
            node: DLGNode - The node to populate

        Returns:
        -------
            None - Populates the node in-place

        Processing Logic:
        ----------------
            - Acquires fields from the GFFStruct and assigns to the node
            - Handles optional fields
            - Populates animations list
            - Sets various parameters.
        """
        node.text = gff_struct.acquire("Text", LocalizedString.from_invalid())
        node.listener = gff_struct.acquire("Listener", "")
        node.vo_resref = gff_struct.acquire("VO_ResRef", ResRef.from_blank())
        node.script1 = gff_struct.acquire("Script", ResRef.from_blank())
        delay: int = gff_struct.acquire("Delay", 0)
        node.delay = -1 if delay == 0xFFFFFFFF else delay
        node.comment = gff_struct.acquire("Comment", "")
        node.sound = gff_struct.acquire("Sound", ResRef.from_blank())
        node.quest = gff_struct.acquire("Quest", "")
        node.plot_index = gff_struct.acquire("PlotIndex", -1)
        node.plot_xp_percentage = gff_struct.acquire("PlotXPPercentage", 0.0)
        node.wait_flags = gff_struct.acquire("WaitFlags", 0)
        node.camera_angle = gff_struct.acquire("CameraAngle", 0)
        node.fade_type = gff_struct.acquire("FadeType", 0)
        node.sound_exists = gff_struct.acquire("SoundExists", default=False)
        node.vo_text_changed = gff_struct.acquire("Changed", default=False)

        anim_list: GFFList = gff_struct.acquire("AnimList", GFFList())
        for anim_struct in anim_list:
            anim = DLGAnimation()
            anim.animation_id = anim_struct.acquire("Animation", 0)
            anim.participant = anim_struct.acquire("Participant", "")
            node.animations.append(anim)

        node.script1_param1 = gff_struct.acquire("ActionParam1", 0)
        node.script2_param1 = gff_struct.acquire("ActionParam1b", 0)
        node.script1_param2 = gff_struct.acquire("ActionParam2", 0)
        node.script2_param2 = gff_struct.acquire("ActionParam2b", 0)
        node.script1_param3 = gff_struct.acquire("ActionParam3", 0)
        node.script2_param3 = gff_struct.acquire("ActionParam3b", 0)
        node.script1_param4 = gff_struct.acquire("ActionParam4", 0)
        node.script2_param4 = gff_struct.acquire("ActionParam4b", 0)
        node.script1_param5 = gff_struct.acquire("ActionParam5", 0)
        node.script2_param5 = gff_struct.acquire("ActionParam5b", 0)
        node.script1_param6 = gff_struct.acquire("ActionParamStrA", "")
        node.script2_param6 = gff_struct.acquire("ActionParamStrB", "")
        node.script2 = gff_struct.acquire("Script2", ResRef.from_blank())
        node.alien_race_node = gff_struct.acquire("AlienRaceNode", 0)
        node.emotion_id = gff_struct.acquire("Emotion", 0)
        node.facial_id = gff_struct.acquire("FacialAnim", 0)
        node.node_id = gff_struct.acquire("NodeID", 0)
        node.unskippable = gff_struct.acquire("NodeUnskippable", default=False)
        node.post_proc_node = gff_struct.acquire("PostProcNode", 0)
        node.record_no_vo_override = gff_struct.acquire("RecordNoVOOverri", default=False)
        node.record_vo = gff_struct.acquire("RecordVO", default=False)
        node.vo_text_changed = gff_struct.acquire("VOTextChanged", default=False)

        if gff_struct.exists("QuestEntry"):
            node.quest_entry = gff_struct.acquire("QuestEntry", 0)
        if gff_struct.exists("FadeDelay"):
            node.fade_delay = gff_struct.acquire("FadeDelay", 0.0)
        if gff_struct.exists("FadeLength"):
            node.fade_length = gff_struct.acquire("FadeLength", 0.0)
        if gff_struct.exists("CameraAnimation"):
            node.camera_anim = gff_struct.acquire("CameraAnimation", 0)
        if gff_struct.exists("CameraID"):
            node.camera_id = gff_struct.acquire("CameraID", 0)
        if gff_struct.exists("CamFieldOfView"):
            node.camera_fov = gff_struct.acquire("CamFieldOfView", 0.0)
        if gff_struct.exists("CamHeightOffset"):
            node.camera_height = gff_struct.acquire("CamHeightOffset", 0.0)
        if gff_struct.exists("CamVidEffect"):
            node.camera_effect = gff_struct.acquire("CamVidEffect", 0)
        if gff_struct.exists("TarHeightOffset"):
            node.target_height = gff_struct.acquire("TarHeightOffset", 0.0)
        if gff_struct.exists("FadeColor"):
            node.fade_color = Color.from_bgr_vector3(gff_struct.acquire("FadeColor", Vector3.from_null()))

    def construct_link(
        gff_struct: GFFStruct,
        link: DLGLink,
    ):
        """Constructs a DLGLink from a GFFStruct.

        Args:
        ----
            gff_struct: GFFStruct - The GFFStruct to acquire resources from
            link: DLGLink - The link to populate

        Returns:
        -------
            None - Populates the link object

        Processing Logic:
        ----------------
            - Acquires an "Active" resource and assigns to link.active1
            - Acquires an "Active2" resource and assigns to link.active2
            - Acquires a "Logic" resource and assigns to link.logic
            - Acquires "Not", "Not2" resources and assigns to link.active1_not, link.active2_not
            - Acquires "Param1-6", "ParamStrA-B" resources and assigns to link parameters.
        """
        link.active1 = gff_struct.acquire("Active", ResRef.from_blank())
        link.active2 = gff_struct.acquire("Active2", ResRef.from_blank())
        link.logic = gff_struct.acquire("Logic", default=False)
        link.active1_not = gff_struct.acquire("Not", default=False)
        link.active2_not = gff_struct.acquire("Not2", default=False)
        link.active1_param1 = gff_struct.acquire("Param1", 0)
        link.active1_param2 = gff_struct.acquire("Param2", 0)
        link.active1_param3 = gff_struct.acquire("Param3", 0)
        link.active1_param4 = gff_struct.acquire("Param4", 0)
        link.active1_param5 = gff_struct.acquire("Param5", 0)
        link.active1_param6 = gff_struct.acquire("ParamStrA", "")
        link.active2_param1 = gff_struct.acquire("Param1b", 0)
        link.active2_param2 = gff_struct.acquire("Param2b", 0)
        link.active2_param3 = gff_struct.acquire("Param3b", 0)
        link.active2_param4 = gff_struct.acquire("Param4b", 0)
        link.active2_param5 = gff_struct.acquire("Param5b", 0)
        link.active2_param6 = gff_struct.acquire("ParamStrB", "")

    dlg = DLG(blank_node=False)

    root: GFFStruct = gff.root

    all_entries: list[DLGEntry] = [DLGEntry() for _ in range(len(root.acquire("EntryList", GFFList())))]
    all_replies: list[DLGReply] = [DLGReply() for _ in range(len(root.acquire("ReplyList", GFFList())))]

    dlg.word_count = root.acquire("NumWords", 0)
    dlg.on_abort = root.acquire("EndConverAbort", ResRef.from_blank())
    dlg.on_end = root.acquire("EndConversation", ResRef.from_blank())
    dlg.skippable = root.acquire("Skippable", default=False)
    dlg.ambient_track = root.acquire("AmbientTrack", ResRef.from_blank())
    dlg.animated_cut = root.acquire("AnimatedCut", 0)
    dlg.camera_model = root.acquire("CameraModel", ResRef.from_blank())
    dlg.computer_type = DLGComputerType(root.acquire("ComputerType", 0))
    dlg.conversation_type = DLGConversationType(root.acquire("ConversationType", 0))

    dlg.old_hit_check = root.acquire("OldHitCheck", default=False)
    dlg.unequip_hands = root.acquire("UnequipHItem", default=False)
    dlg.unequip_items = root.acquire("UnequipItems", default=False)
    dlg.vo_id = root.acquire("VO_ID", "")
    dlg.alien_race_owner = root.acquire("AlienRaceOwner", 0)
    dlg.post_proc_owner = root.acquire("PostProcOwner", 0)
    dlg.record_no_vo = root.acquire("RecordNoVO", 0)
    dlg.next_node_id = root.acquire("NextNodeID", 0)
    dlg.delay_entry = root.acquire("DelayEntry", 0)
    dlg.delay_reply = root.acquire("DelayReply", 0)

    stunt_list: GFFList = root.acquire("StuntList", GFFList())
    for stunt_struct in stunt_list:
        stunt = DLGStunt()
        dlg.stunts.append(stunt)
        stunt.participant = stunt_struct.acquire("Participant", "")
        stunt.stunt_model = stunt_struct.acquire("StuntModel", ResRef.from_blank())

    starting_list: GFFList = root.acquire("StartingList", GFFList())
    for link_struct in starting_list:
        link = DLGLink()
        link.link_index = link_struct.acquire("Index", 0)
        try:
            link.node = all_entries[link.link_index]
        except IndexError:
            RobustRootLogger().error(
                f"'Index' field value '{link.link_index}' (struct #{starting_list._structs.index(link_struct)+1} in StartingList) does not point to a valid EntryList node, omitting..."
            )
        else:
            dlg.starters.append(link)
            construct_link(link_struct, link)

    entry_list: GFFList = root.acquire("EntryList", GFFList())
    for i, entry_struct in enumerate(entry_list):
        entry: DLGEntry = all_entries[i]
        entry.speaker = entry_struct.acquire("Speaker", "")
        entry.list_index = i
        construct_node(entry_struct, entry)

        replies_list: GFFList = entry_struct.acquire("RepliesList", GFFList())
        for link_struct in replies_list:
            link = DLGLink()
            link.link_index = link_struct.acquire("Index", 0)
            try:
                link.node = all_replies[link.link_index]
            except IndexError:
                RobustRootLogger().error(
                    f"'Index' field value '{link.link_index}' (struct #{replies_list._structs.index(link_struct)+1} in RepliesList) does not point to a valid ReplyList node, omitting..."
                )
            else:
                link.is_child = bool(link_struct.acquire("IsChild", 0))
                link.comment = link_struct.acquire("LinkComment", "")

                entry.links.append(link)
                construct_link(link_struct, link)

    reply_list: GFFList = root.acquire("ReplyList", GFFList())
    for i, reply_struct in enumerate(reply_list):
        reply: DLGReply = all_replies[i]
        reply.list_index = i
        construct_node(reply_struct, reply)

        entries_list: GFFList = reply_struct.acquire("EntriesList", GFFList())
        for link_struct in entries_list:
            link = DLGLink()
            link.link_index = link_struct.acquire("Index", 0)
            try:
                link.node = all_entries[link.link_index]
            except IndexError:
                RobustRootLogger().error(
                    f"'Index' field value '{link.link_index}' (struct #{replies_list._structs.index(link_struct)+1} in EntriesList) does not point to a valid EntryList node, omitting..."
                )
            else:
                link.is_child = bool(link_struct.acquire("IsChild", 0))
                link.comment = link_struct.acquire("LinkComment", "")

                reply.links.append(link)
                construct_link(link_struct, link)

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
            list_name: str - The name of the GFF list.

        Returns:
        -------
            None: Populates the GFFStruct

        Processing Logic:
        ----------------
            - Sets the Active resref on the GFFStruct from the link
            - Sets the Index uint32 on the GFFStruct from the node list index
            - If game is K2, sets additional link properties on the GFFStruct.
        """
        # Indexes the prior dialog
        gff_struct.set_uint32("Index", nodes.index(link.node) if link.link_index == -1 else link.link_index)

        if list_name != "StartingList":
            gff_struct.set_uint8("IsChild", int(link.is_child))
        gff_struct.set_resref("Active", link.active1)
        if link.comment and link.comment.strip():
            gff_struct.set_string("LinkComment", link.comment)
        if game.is_k2():
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
        nodes: list[DLGEntry] | list[DLGReply],
        list_name: Literal["EntriesList", "RepliesList"],
    ):
        """Disassembles a DLGNode into a GFFStruct.

        Args:
        ----
            gff_struct: GFFStruct - The GFFStruct to populate
            node: DLGNode - The DLGNode to dismantle into a EntryList/ReplyList GFFStruct node.
            nodes: list - The nodes list (abstracted EntryList/ReplyList represented as list[DLGEntry] | list[DLGReply])
            list_name: Literal["EntriesList", "RepliesList"] - the name of the nested linked list. If nodes is list[DLGEntry], should be 'RepliesList' and vice versa.

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
        gff_struct.set_uint32("Delay", 0xFFFFFFFF if node.delay == -1 else node.delay)
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

        anim_list: GFFList = gff_struct.set_list("AnimList", GFFList())
        for anim in node.animations:
            anim_struct: GFFStruct = anim_list.add(0)
            anim_struct.set_uint16("Animation", anim.animation_id)
            anim_struct.set_string("Participant", anim.participant)

        if node.quest.strip() and node.quest_entry:
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

        if game.is_k2():
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

    all_entries: list[DLGEntry] = dlg.all_entries()
    all_replies: list[DLGReply] = dlg.all_replies()

    gff = GFF(GFFContent.DLG)

    root: GFFStruct = gff.root
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
    if game.is_k2():
        root.set_int32("AlienRaceOwner", dlg.alien_race_owner)
        root.set_int32("PostProcOwner", dlg.post_proc_owner)
        root.set_int32("RecordNoVO", dlg.record_no_vo)
        root.set_int32("NextNodeID", dlg.next_node_id)
    if use_deprecated:
        root.set_uint32("DelayEntry", dlg.delay_entry)
        root.set_uint32("DelayReply", dlg.delay_reply)

    stunt_list: GFFList = root.set_list("StuntList", GFFList())
    for stunt in dlg.stunts:
        stunt_struct: GFFStruct = stunt_list.add(0)
        stunt_struct.set_string("Participant", stunt.participant)
        stunt_struct.set_resref("StuntModel", stunt.stunt_model)

    starting_list: GFFList = root.set_list("StartingList", GFFList())
    for i, starter in enumerate(dlg.starters):
        starting_struct: GFFStruct = starting_list.add(i)
        dismantle_link(starting_struct, starter, all_entries, "StartingList")

    entry_list: GFFList = root.set_list("EntryList", GFFList())
    for i, entry in enumerate(all_entries):
        entry_struct: GFFStruct = entry_list.add(i)
        entry_struct.set_string("Speaker", entry.speaker)
        dismantle_node(entry_struct, entry, all_replies, "RepliesList")

    reply_list: GFFList = root.set_list("ReplyList", GFFList())
    for i, reply in enumerate(all_replies):
        reply_struct: GFFStruct = reply_list.add(i)
        dismantle_node(reply_struct, reply, all_entries, "EntriesList")

    # This part helps preserve the original GFF if this DLG was in fact constructed from one.
    # In scenarios where a brand new DLG is created from scratch this sort algo probably does nothing.
    def sort_entry(struct: GFFStruct) -> int:
        entry: DLGEntry = all_entries[struct.struct_id]
        struct.struct_id = struct.struct_id if entry.list_index == -1 else entry.list_index
        return struct.struct_id

    def sort_reply(struct: GFFStruct) -> int:
        reply: DLGReply = all_replies[struct.struct_id]
        struct.struct_id = struct.struct_id if reply.list_index == -1 else reply.list_index
        return struct.struct_id

    entry_list._structs.sort(key=sort_entry)  # noqa: SLF001
    reply_list._structs.sort(key=sort_reply)  # noqa: SLF001

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
    gff: GFF = read_gff(source, offset, size)
    return construct_dlg(gff)


def write_dlg(
    dlg: DLG,
    target: TARGET_TYPES,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
):
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
    gff: GFF = dismantle_dlg(dlg, game, use_deprecated=use_deprecated)
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
    gff: GFF = dismantle_dlg(dlg, game, use_deprecated=use_deprecated)
    return bytes_gff(gff, file_format)
