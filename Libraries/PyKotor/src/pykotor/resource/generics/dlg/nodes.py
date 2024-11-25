"""Dialog node classes for entries and replies."""

from __future__ import annotations

import uuid

from collections import deque
from typing import TYPE_CHECKING, Any

from pykotor.common.language import Gender, Language, LocalizedString
from pykotor.common.misc import Color, ResRef

if TYPE_CHECKING:
    from collections import deque

    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]

    from pykotor.resource.generics.dlg.links import DLGLink


class DLGAnimation:
    """Represents a unit of animation executed during a node."""

    def __init__(
        self,
    ):
        self._hash_cache: int = hash(uuid.uuid4().hex)
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
    def from_dict(cls, data: dict) -> DLGAnimation:
        animation: DLGAnimation = cls()
        animation.animation_id = data.get("animation_id", 6)
        animation.participant = data.get("participant", "")
        animation._hash_cache = data.get("_hash_cache", animation._hash_cache)  # noqa: SLF001
        return animation


class DLGNode:
    """Represents a node in the graph (either DLGEntry or DLGReply).

    Contains a list of DLGLink objects to indicate outgoing edges.
    """

    def __init__(  # noqa: PLR0915
        self,
    ):
        """Initializes a DLGNode object.

        Processing Logic:
        ----------------
            - Sets default values for all properties of a DLGNode object
            - Initializes lists and optional properties as empty/None
            - Sets flags and identifiers to default values
        """
        if not isinstance(self, (DLGEntry, DLGReply)):
            raise RuntimeError("Cannot construct base class DLGNode: use DLGEntry or DLGReply instead.")  # noqa: TRY004

        self._hash_cache: int = hash(uuid.uuid4().hex)
        self.comment: str = ""
        self.links = []
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
        text: str | None = self.text.get(Language.ENGLISH, Gender.MALE, use_fallback=True)
        strref_display: str = f"stringref={self.text.stringref}" if text is None else f"text={text}"
        return f"{self.__class__.__name__}({strref_display}, list_index={self.list_index}, links={self.links})"

    def __eq__(self, other):
        if self.__class__ is not other.__class__:
            return NotImplemented
        return self.__hash__() == other.__hash__()

    def __hash__(self):
        return self._hash_cache

    def path(self) -> str:
        """Returns the GFF path to this node."""
        node_list_display: Literal["EntryList", "ReplyList"] = "EntryList" if isinstance(self, DLGEntry) else "ReplyList"
        node_path: str = f"{node_list_display}\\{self.list_index}"
        return node_path

    def add_node(
        self,
        target_links: list[DLGLink],
        source: DLGNode,
    ):
        from pykotor.resource.generics.dlg.links import DLGLink
        target_links.append(DLGLink(source, len(target_links)))

    def calculate_links_and_nodes(self) -> tuple[int, int]:
        from collections import deque

        queue: deque[DLGNode] = deque([self])
        seen_nodes: set[DLGNode] = set()
        num_links = 0

        while queue:
            node: DLGNode = queue.popleft()
            assert node is not None
            if node in seen_nodes:
                continue
            seen_nodes.add(node)
            num_links += len(node.links)
            queue.extend(link.node for link in node.links if link.node is not None)

        return num_links, len(seen_nodes)

    def shift_item(
        self,
        links: list[DLGLink],
        old_index: int,
        new_index: int,
    ):
        if 0 <= new_index < len(links):
            link: DLGLink = links.pop(old_index)
            links.insert(new_index, link)
        else:
            raise IndexError(new_index)

    def to_dict(  # noqa: C901, PLR0912
        self,
        node_map: dict[str | int, Any] | None = None,
    ) -> dict[str | int, Any]:
        if node_map is None:
            node_map = {}

        node_key: int = hash(self)
        if node_key in node_map:
            return {"type": self.__class__.__name__, "ref": node_key}

        node_dict: dict[str | int, Any] = {"type": self.__class__.__name__, "key": node_key, "data": {}}
        node_map[node_key] = node_dict

        for key, value in self.__dict__.items():
            if key.startswith("__"):
                continue
            if key == "links":
                links: list[DLGLink] = value
                node_dict["data"][key] = {
                    "value": [link.to_dict(node_map) for link in links],
                    "py_type": "list",
                }
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
                raise ValueError(f"Unsupported type: {value.__class__.__name__} for key: {key}")

        return node_dict

    @staticmethod
    def from_dict(  # noqa: C901, PLR0912
        data: dict[str | int, Any],
        node_map: dict[str | int, Any] | None = None,
    ) -> DLGEntry | DLGReply:  # noqa: C901, PLR0912
        from pykotor.resource.generics.dlg.links import DLGLink

        if node_map is None:
            node_map = {}

        if "ref" in data:
            return node_map[data["ref"]]

        node_key: int | str | None = data.get("key")
        assert isinstance(node_key, (int, str))
        node_type: str | None = data.get("type")
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
        for key, value in node_data.items():
            if not isinstance(value, dict):
                continue
            py_type: str | None = value.get("py_type")
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


class DLGReply(DLGNode):
    """Replies are nodes that are responses by the player."""

    links: list[DLGLink[DLGEntry]]

    def __init__(
        self,
        **kwargs,
    ):
        super().__init__()
        for key, value in kwargs.items():
            setattr(self, key, value)


class DLGEntry(DLGNode):
    """Entries are nodes that are responses by NPCs."""

    links: list[DLGLink[DLGReply]]

    def __init__(
        self,
        **kwargs,
    ):
        super().__init__()
        self.speaker: str = ""
        for key, value in kwargs.items():
            setattr(self, key, value)
