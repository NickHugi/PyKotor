from __future__ import annotations

import uuid

from collections import deque
from enum import IntEnum
from pathlib import PureWindowsPath
from typing import TYPE_CHECKING, Any, Dict, Generator, Generic, Sequence, TypeVar, cast

from loggerplus import RobustLogger

from pykotor.common.geometry import Vector3
from pykotor.common.language import Gender, Language, LocalizedString
from pykotor.common.misc import Color, Game, ResRef
from pykotor.resource.formats.gff.gff_auto import bytes_gff, read_gff, write_gff
from pykotor.resource.formats.gff.gff_data import GFF, GFFContent, GFFList
from pykotor.resource.type import ResourceType

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
    ):
        self.starters: list[DLGLink] = []
        self.stunts: list[DLGStunt] = []

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

    def find_paths(self, target: DLGEntry | DLGReply | DLGLink) -> list[PureWindowsPath]:
        paths: list[PureWindowsPath] = []

        if isinstance(target, DLGLink):
            parent_node = self.getLinkParent(target)
            if parent_node is None:
                raise ValueError(f"Target {target.__class__.__name__} doesn't have a parent, and also not found in starters.")
            if isinstance(parent_node, DLG):
                paths.append(PureWindowsPath("StartingList", str(target.list_index)))
            else:
                self._find_paths_for_link(parent_node, target, paths)
        else:
            self._find_paths_recursive(self.starters, target, PureWindowsPath(), paths, set())

        return paths

    def _find_paths_for_link(self, parent_node: DLGNode, target: DLGLink, paths: list[PureWindowsPath]):
        if isinstance(parent_node, DLGEntry):
            node_list_name = "EntryList"
        else:
            node_list_name = "ReplyList"
        parent_path = PureWindowsPath(node_list_name, str(parent_node.list_index))

        if isinstance(parent_node, DLGEntry):
            link_list_name = "RepliesList"
        else:
            link_list_name = "EntriesList"

        paths.append(parent_path / link_list_name / str(target.list_index))

    def _find_paths_recursive(
        self,
        links: list[DLGLink],
        target: DLGNode,
        current_path: PureWindowsPath,
        paths: list[PureWindowsPath],
        seen_links_and_nodes: set[DLGNode | DLGLink],
    ):
        for link in links:
            if link is None or link in seen_links_and_nodes:
                continue

            seen_links_and_nodes.add(link)
            node = link.node
            assert node is not None, "Corrupted DLG/buggy code detected"

            if node == target:
                if node in seen_links_and_nodes:
                    continue
                seen_links_and_nodes.add(node)
                if isinstance(node, DLGEntry):
                    paths.append(PureWindowsPath("EntryList", str(node.list_index)))
                else:
                    paths.append(PureWindowsPath("ReplyList", str(node.list_index)))
                continue

            if node not in seen_links_and_nodes:
                seen_links_and_nodes.add(node)
                if isinstance(node, DLGEntry):
                    node_list_name, link_list_name = "EntryList", "RepliesList"
                else:
                    node_list_name, link_list_name = "ReplyList", "EntriesList"
                node_path = PureWindowsPath(node_list_name, str(node.list_index))

                self._find_paths_recursive(node.links, target, current_path / node_path / link_list_name, paths, seen_links_and_nodes)

    def lookup_from_path(self, path: PureWindowsPath | str) -> list[DLGNode] | DLGNode | list[DLGLink] | DLGLink | None:
        path = PureWindowsPath(path)
        if not path.parts or not path.name:
            return None
        num_of_parts = len(path.parts)

        def find_by_index(collection: list[DLGNode | DLGLink], index: str | int) -> DLGNode | DLGLink | None:
            try:
                index = int(index)
                return (
                    collection[index]
                    if index < len(collection)
                    else next(node for node in collection if node.list_index == index)
                )
            except (ValueError, IndexError, StopIteration):
                return None

        current_node: DLGNode | DLGLink | None = None
        if path.parts[0] == "EntryList":
            entries = self.all_entries()
            if num_of_parts <= 1:
                return entries
            current_node = find_by_index(entries, path.parts[1])
        elif path.parts[0] == "ReplyList":
            replies = self.all_replies()
            if num_of_parts <= 1:
                return replies
            current_node = find_by_index(replies, path.parts[1])

        if (
            current_node is not None
            and num_of_parts >= 3  # noqa: PLR2004
            and path.parts[2] in {"RepliesList", "EntriesList"}
        ):
            if num_of_parts == 3:  # noqa: PLR2004
                return current_node.links
            current_node = find_by_index(current_node.links, path.parts[3])
        return current_node

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
        *,
        as_sorted: bool = False
    ) -> list[DLGEntry]:
        """Returns a flat list of all entries in the dialog.

        Returns:
        -------
            A list of all stored entries.
        """
        entries = self._all_entries()
        if not as_sorted:
            return entries
        return sorted(entries, key=lambda entry: (entry.list_index == -1, entry.list_index))

    def _all_entries(
        self,
        links: list[DLGLink] | None = None,
        seen_entries: set | None = None,
    ) -> list[DLGEntry]:
        """Collect all entries reachable from the given links.

        Args:
        ----
            links: {List of starting DLGLinks}
            seen_entries: {Set of entries already processed}

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
        seen_entries = set() if seen_entries is None else seen_entries

        for link in links:
            entry: DLGNode | None = link.node
            if entry not in seen_entries:  # sourcery skip: class-extract-method
                assert isinstance(entry, DLGEntry), f"{type(entry).__name__}: {entry}"  # noqa: S101
                entries.append(entry)
                seen_entries.add(entry)
                for reply_link in entry.links:
                    reply = reply_link.node
                    entries.extend(self._all_entries(reply.links, seen_entries))

        return entries

    def all_replies(
        self,
        *,
        as_sorted: bool = False,
    ) -> list[DLGReply]:
        """Returns a flat list of all replies in the dialog.

        Returns:
        -------
            A list of all stored replies.
        """
        replies = self._all_replies()
        if not as_sorted:
            return replies
        return sorted(replies, key=lambda reply: (reply.list_index == -1, reply.list_index))

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

        links = [_ for link in self.starters if link.node is not None for _ in link.node.links] if links is None else links
        seen_replies = [] if seen_replies is None else seen_replies

        for link in links:
            reply = link.node
            if reply not in seen_replies:  # sourcery skip: class-extract-method
                assert isinstance(reply, DLGReply), f"{type(reply).__name__}: {reply}"  # noqa: S101
                replies.append(reply)
                seen_replies.append(reply)
                for entry_link in reply.links:
                    entry: DLGNode | None = entry_link.node
                    if entry is None:
                        continue
                    replies.extend(self._all_replies(entry.links, seen_replies))

        return replies

    def getLinkParent(self, target_link: DLGLink) -> DLGEntry | DLGReply | DLG | None:
        """Find the parent node of a given link."""
        if target_link in self.starters:
            return self
        return next(
            (
                node
                for node in self.all_entries() + self.all_replies()
                if target_link in node.links
            ),
            None,
        )

    def getAllNodeReferences(self, target_node: DLGNode, node_list: Sequence[DLGEntry | DLGReply] | None = None) -> list[DLGLink]:
        """Returns a list of all DLGLink references that link to the given node."""
        use_starting_list = False
        if node_list is None:
            use_starting_list = True
            node_list = (*self.all_entries(), *self.all_replies())
        refs = {
            link
            for dlg_node in node_list
            if dlg_node is not None
            for link in dlg_node.links
            if link.node == target_node
        }
        if use_starting_list:
            refs.update(
                {
                    link
                    for link in self.starters
                    if link.node == target_node
                }
            )
        return list(refs)


class DLGComputerType(IntEnum):
    Modern = 0
    Ancient = 1


class DLGConversationType(IntEnum):
    Human = 0
    Computer = 1
    Other = 2


class DLGNode:
    """Represents a node in the graph (either DLGEntry or DLGReply).

    Contains a list of DLGLink objects to indicate outgoing edges.
    """
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

        self._hash_cache = hash(uuid.uuid4().hex)
        self.comment: str = ""
        self.links: list[DLGLink] = []
        self.list_index: int = -1

        self.camera_angle: int = 0
        self.delay: int = -1
        self.fade_type: int = 0
        self.listener: str = ""
        self.plot_index: int = 0
        self.plot_xp_percentage: float = 1.0
        self.quest: str = ""
        self.script1: ResRef = ResRef.from_blank()
        self.sound: ResRef = ResRef.from_blank()
        self.sound_exists: int = 0
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

        self.script2: ResRef = ResRef.from_blank()
        self.script2_param1: int = 0
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

    def __repr__(
        self,
    ) -> str:
        text = self.text.get(Language.ENGLISH, Gender.MALE, use_fallback=True)
        strref_display = f"stringref={self.text.stringref}" if text is None else f"text={text}"
        return f"{self.__class__.__name__}({strref_display}, list_index={self.list_index}, links={self.links})"

    def __eq__(self, other):
        if self.__class__ is not other.__class__:
            return NotImplemented
        return self.__hash__() == other.__hash__()

    def __hash__(self):
        return self._hash_cache

    def add_node(
        self,
        target_links: list[DLGLink],
        source: DLGNode,
    ):
        target_links.append(DLGLink(source, len(target_links)))

    def calculate_links_and_nodes(self) -> tuple[int, int]:
        queue: deque[DLGNode] = deque([self])
        seen_nodes: set[DLGNode] = set()
        num_links = 0
        num_unique_nodes = 0

        while queue:
            node: DLGNode = queue.popleft()
            assert node is not None
            if node in seen_nodes:
                continue
            seen_nodes.add(node)
            num_links += len(node.links)
            queue.extend(link.node for link in node.links if link.node is not None)

        num_unique_nodes = len(seen_nodes)
        return num_links, num_unique_nodes

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

    def to_dict(
        self,
        node_map: dict[str | int, Any] | None = None,
    ) -> dict[str | int, Any]:
        if node_map is None:
            node_map = {}

        node_key = hash(self)
        if node_key in node_map:
            return {"type": self.__class__.__name__, "ref": node_key}

        node_dict: dict[str | int, Any] = {"type": self.__class__.__name__, "key": node_key, "data": {}}
        node_map[node_key] = node_dict

        for key, value in self.__dict__.items():
            if key.startswith("__"):
                continue
            if key == "links":
                links: list[DLGLink] = value
                node_dict["data"][key] = {"value": [link.to_dict(node_map) for link in links], "py_type": "list"}
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
            elif key == "animations":
                anims: list[DLGAnimation] = value
                node_dict["data"][key] = {"value": [anim.to_dict() for anim in anims], "py_type": "list"}
            elif isinstance(value, list):
                node_dict["data"][key] = {"value": value, "py_type": "list"}
            elif value is None:
                node_dict["data"][key] = {"value": None, "py_type": "None"}
            else:
                raise ValueError(f"Unsupported type: {type(value)} for key: {key}")

        return node_dict

    @staticmethod
    def from_dict(
        data: dict[str | int, Any],
        node_map: dict[str | int, Any] | None = None,
    ) -> DLGEntry | DLGReply:  # noqa: C901, PLR0912
        if node_map is None:
            node_map = {}

        if "ref" in data:
            return node_map[data["ref"]]

        node_key = data.get("key")
        assert isinstance(node_key, (int, str))
        node_type = data.get("type")
        node_data: dict[str, Any] = data.get("data", {})

        node: DLGEntry | DLGReply
        if node_type == "DLGEntry":
            node = DLGEntry()
            node.speaker = node_data.pop("speaker", {"value": ""})["value"]
        elif node_type == "DLGReply":
            node = DLGReply()
        else:
            raise ValueError(f"Unknown node type: {node_type}")

        node_map[node_key] = node

        node._hash_cache = int(node_key)  # noqa: SLF001
        for key, value in cast(Dict[str, dict], node_data).items():
            if value is None:
                continue
            py_type = value.get("py_type")
            actual_value: Any = value.get("value")

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

    def path(self) -> str:
        """Returns the GFF path to this node."""
        node_list_display = "EntryList" if isinstance(self, DLGEntry) else "ReplyList"
        node_path = f"{node_list_display}\\{self.list_index}"
        return node_path


class DLGReply(DLGNode):
    """Replies are nodes that are responses by the player."""

    def __init__(
        self,
        **kwargs,
    ):
        super().__init__()
        for key, value in kwargs.items():
            setattr(self, key, value)


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


class DLGAnimation:
    """Represents a unit of animation executed during a node."""

    def __init__(
        self,
    ):
        self._hash_cache = hash(uuid.uuid4().hex)
        self.animation_id: int = 6
        self.participant: str = ""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(animation_id={self.animation_id}, participant={self.participant})"

    def __eq__(self, other):
        if self.__class__ is not other.__class__:
            return NotImplemented
        return self.__hash__() == other.__hash__()

    def __hash__(self):
        return self._hash_cache

    def to_dict(self) -> dict[str, Any]:
        return {"animation_id": self.animation_id, "participant": self.participant, "_hash_cache": self._hash_cache}

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        animation = cls()
        animation.animation_id = data.get("animation_id", 6)
        animation.participant = data.get("participant", "")
        animation._hash_cache = data.get("_hash_cache", animation._hash_cache)  # noqa: SLF001
        return animation

T = TypeVar("T", bound=DLGNode)

class DLGLink(Generic[T]):
    """Represents a directed edge from a source node to a target node (DLGNode).

    Links are stored either in other nodes or in the starting list of the DLG. By design, all
    DLGLink objects must be unique.

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

    def partial_path(self, *, is_starter: bool) -> str:
        if is_starter:
            p1 = "StartingList"
        else:
            p1 = "EntriesList" if isinstance(self.node, DLGEntry) else "RepliesList"
        return f"{p1}\\{self.list_index}"

    def __init__(
        self,
        node: DLGNode,
        list_index: int = -1,
    ):
        self._hash_cache = hash(uuid.uuid4().hex)
        self.active1: ResRef = ResRef.from_blank()
        self.node: DLGNode = node
        self.list_index: int = list_index

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

    def __iter__(self) -> Generator[Self, Any, None]:
        """Iterate over nested links without recursion."""
        stack: Sequence[Self] = [self]
        while stack:
            current = stack.pop()
            yield current
            if not current.node:
                continue
            stack.extend(current.node.links)

    def __repr__(self) -> str:
        comment_str = str(self.comment)
        comment_display = comment_str[:30] if len(comment_str) > 30 else comment_str
        return (f"{self.__class__.__name__}(link_list_index={self.list_index}, comment={comment_display})")

    def __eq__(self, other):
        if self.__class__ is not other.__class__:
            return NotImplemented
        return self.__hash__() == other.__hash__()

    def __hash__(self) -> int:
        return self._hash_cache

    def to_dict(self, node_map: dict[str | int, Any] | None = None) -> dict[str | int, Any]:
        if node_map is None:
            node_map = {}

        link_key = hash(self)
        if link_key in node_map:
            return {"type": self.__class__.__name__, "ref": link_key}

        link_dict: dict[str | int, Any] = {
            "type": self.__class__.__name__,
            "key": link_key,
            "node": self.node.to_dict(node_map) if self.node else None,
            "link_list_index": self.list_index,
            "data": {},
        }

        for key, value in self.__dict__.items():
            if key.startswith("__"):
                continue
            if key in ("node", "list_index", "_hash_cache"):
                continue
            if isinstance(value, bool):
                link_dict["data"][key] = {"value": int(value), "py_type": "bool"}
            elif isinstance(value, int):
                link_dict["data"][key] = {"value": value, "py_type": "int"}
            elif isinstance(value, float):
                link_dict["data"][key] = {"value": value, "py_type": "float"}
            elif isinstance(value, str):
                link_dict["data"][key] = {"value": value, "py_type": "str"}
            elif isinstance(value, ResRef):
                link_dict["data"][key] = {"value": str(value), "py_type": "ResRef"}
            elif isinstance(value, Color):
                link_dict["data"][key] = {"value": value.bgr_integer(), "py_type": "Color"}
            elif isinstance(value, LocalizedString):
                link_dict["data"][key] = {"value": value.to_dict(), "py_type": "LocalizedString"}
            elif isinstance(value, list):
                link_dict["data"][key] = {"value": value, "py_type": "list"}
            elif value is None:
                link_dict["data"][key] = {"value": None, "py_type": "None"}
            else:
                raise ValueError(f"Unsupported type: {type(value)} for key: {key}")
        node_map[link_key] = link_dict

        return link_dict

    @classmethod
    def from_dict(cls, link_dict: dict[str | int, Any], node_map: dict[str | int, Any] | None = None) -> Self:
        if node_map is None:
            node_map = {}

        if "ref" in link_dict:
            return node_map[link_dict["ref"]]

        link_key = link_dict["key"]
        if link_key in node_map:
            return node_map[link_key]

        link = object.__new__(cls)
        link._hash_cache = int(link_key)  # noqa: SLF001
        link.list_index = link_dict.get("link_list_index", -1)
        for key, value in cast(Dict[str, dict], link_dict["data"]).items():
            if value is None:
                continue
            py_type = value.get("py_type")
            actual_value: Any = value.get("value")

            if py_type == "str":
                setattr(link, key, actual_value)
            elif py_type == "int":
                setattr(link, key, int(actual_value))
            elif py_type == "float":
                setattr(link, key, float(actual_value))
            elif py_type == "bool":
                setattr(link, key, bool(actual_value))
            elif py_type == "ResRef":
                setattr(link, key, ResRef(actual_value))
            elif py_type == "Color":
                setattr(link, key, Color.from_bgr_integer(actual_value))
            elif py_type == "list":
                setattr(link, key, actual_value)
            elif py_type == "None" or actual_value == "None":
                setattr(link, key, None)
            else:
                raise ValueError(f"Unsupported type: {py_type} for key: {key}")
        node_map[link_key] = link

        if link_dict["node"]:
            link.node = DLGNode.from_dict(link_dict["node"], node_map)

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
        self._hash_cache = hash(uuid.uuid4().hex)
        self.participant: str = ""
        self.stunt_model: ResRef = ResRef.from_blank()

    def __eq__(self, other):
        if self.__class__ is not other.__class__:
            return NotImplemented
        return self.__hash__() == other.__hash__()

    def __hash__(self):
        return self._hash_cache

    def to_dict(self) -> dict[str, Any]:
        return {"participant": self.participant, "stunt_model": str(self.stunt_model), "_hash_cache": self._hash_cache}

    @classmethod
    def from_dict(cls, data: dict[str, Any], node_map: dict[str | int, Any] | None = None) -> Self:
        stunt = cls()
        stunt.participant = data.get("participant", "")
        stunt.stunt_model = ResRef(data.get("stunt_model", ""))
        stunt._hash_cache = data.get("_hash_cache", stunt._hash_cache)  # noqa: SLF001
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
        """
        node.text = gff_struct.acquire("Text", LocalizedString.from_invalid())
        node.listener = gff_struct.acquire("Listener", "")
        node.vo_resref = gff_struct.acquire("VO_ResRef", ResRef.from_blank())
        node.script1 = gff_struct.acquire("Script", ResRef.from_blank())
        delay: int = gff_struct.acquire("Delay", 0)
        node.delay = -1 if delay == 0xFFFFFFFF else delay  # noqa: PLR2004
        node.comment = gff_struct.acquire("Comment", "")
        node.sound = gff_struct.acquire("Sound", ResRef.from_blank())
        node.quest = gff_struct.acquire("Quest", "")
        node.plot_index = gff_struct.acquire("PlotIndex", -1)
        node.plot_xp_percentage = gff_struct.acquire("PlotXPPercentage", 0.0)
        node.wait_flags = gff_struct.acquire("WaitFlags", 0)
        node.camera_angle = gff_struct.acquire("CameraAngle", 0)
        node.fade_type = gff_struct.acquire("FadeType", 0)
        node.sound_exists = gff_struct.acquire("SoundExists", 0)
        node.vo_text_changed = gff_struct.acquire("VOTextChanged", default=False)

        anim_list: GFFList = gff_struct.acquire("AnimList", GFFList())
        for anim_struct in anim_list:
            anim = DLGAnimation()
            anim.animation_id = anim_struct.acquire("Animation", 0)
            if anim.animation_id > 10000:
                anim.animation_id -= 10000
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
            node.camera_effect = gff_struct.acquire("CamVidEffect", -1)
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

    dlg = DLG()

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
    for link_list_index, link_struct in enumerate(starting_list):
        node_struct_id = link_struct.acquire("Index", 0)
        try:
            node = all_entries[node_struct_id]
        except IndexError:
            context_link_msg = f"(StartingList/{link_list_index})"  # noqa: SLF001
            RobustLogger().error(f"'Index' field value '{node_struct_id}' at {context_link_msg} does not point to a valid ReplyList node, omitting...")
        else:
            link: DLGLink = DLGLink(node, link_list_index)
            dlg.starters.append(link)
            construct_link(link_struct, link)

    entry_list: GFFList = root.acquire("EntryList", GFFList())
    for node_list_index, entry_struct in enumerate(entry_list):
        entry: DLGEntry = all_entries[node_list_index]
        entry.speaker = entry_struct.acquire("Speaker", "")
        entry.list_index = node_list_index
        construct_node(entry_struct, entry)

        replies_list: GFFList = entry_struct.acquire("RepliesList", GFFList())
        for link_list_index, link_struct in enumerate(replies_list):
            node_struct_id = link_struct.acquire("Index", 0)
            try:
                node = all_replies[node_struct_id]
            except IndexError:
                context_link_msg = f"(EntryList/{node_list_index}/RepliesList/{link_list_index})"  # noqa: SLF001
                RobustLogger().error(f"'Index' field value '{node_struct_id}' at {context_link_msg} does not point to a valid ReplyList node, omitting...")
            else:
                link = DLGLink(node, link_list_index)
                link.is_child = bool(link_struct.acquire("IsChild", default=False))
                link.comment = link_struct.acquire("LinkComment", "")

                entry.links.append(link)
                construct_link(link_struct, link)

    reply_list: GFFList = root.acquire("ReplyList", GFFList())
    for node_list_index, reply_struct in enumerate(reply_list):
        reply: DLGReply = all_replies[node_list_index]
        reply.list_index = node_list_index
        construct_node(reply_struct, reply)

        entries_list: GFFList = reply_struct.acquire("EntriesList", GFFList())
        for link_list_index, link_struct in enumerate(entries_list):
            node_struct_id = link_struct.acquire("Index", 0)
            try:
                node = all_entries[node_struct_id]
            except IndexError:
                context_link_msg = f"(ReplyList/{node_list_index}/EntriesList/{link_list_index})"  # noqa: SLF001
                RobustLogger().error(f"'Index' field value '{node_struct_id}' at {context_link_msg} does not point to a valid EntryList node, omitting...")
            else:
                link = DLGLink(node, link_list_index)
                link.is_child = bool(link_struct.acquire("IsChild", default=False))
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
        object.__setattr__(link, "__class__", DLGLink)
        node_list_index = nodes.index(link.node)
        gff_struct.set_uint32("Index", node_list_index)

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
            anim_struct.set_uint16("Animation", anim.animation_id if anim.animation_id <= 10000 else anim.animation_id + 10000)
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
        # Sort links by link_list_index, treating -1 as the highest value
        sorted_links = sorted(node.links, key=lambda link: (link.list_index == -1, link.list_index))
        for i, link in enumerate(sorted_links):
            link_struct: GFFStruct = link_list.add(i)
            dismantle_link(link_struct, link, nodes, list_name)

    all_entries: list[DLGEntry] = dlg.all_entries(as_sorted=True)
    all_replies: list[DLGReply] = dlg.all_replies(as_sorted=True)

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
    sorted_links: list[DLGLink] = sorted(dlg.starters, key=lambda link: (link.list_index == -1, link.list_index))
    for link_list_index, starter in enumerate(sorted_links):
        starting_struct: GFFStruct = starting_list.add(link_list_index)
        dismantle_link(starting_struct, starter, all_entries, "StartingList")

    entry_list: GFFList = root.set_list("EntryList", GFFList())
    for node_list_index, entry in enumerate(all_entries):
        entry_struct: GFFStruct = entry_list.add(node_list_index)
        entry_struct.set_string("Speaker", entry.speaker)
        dismantle_node(entry_struct, entry, all_replies, "RepliesList")

    reply_list: GFFList = root.set_list("ReplyList", GFFList())
    for node_list_index, reply in enumerate(all_replies):
        reply_struct: GFFStruct = reply_list.add(node_list_index)
        dismantle_node(reply_struct, reply, all_entries, "EntriesList")

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
