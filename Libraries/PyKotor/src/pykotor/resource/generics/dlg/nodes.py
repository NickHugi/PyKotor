"""Dialog node classes for entries and replies."""

from __future__ import annotations

import uuid

from collections import deque
from typing import TYPE_CHECKING, Any

from pykotor.common.language import Gender, Language, LocalizedString
from pykotor.common.misc import Color, ResRef
from pykotor.resource.generics.dlg.anims import DLGAnimation

if TYPE_CHECKING:
    from collections import deque

    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]

    from pykotor.resource.generics.dlg.links import DLGLink


class DLGNode:
    """Represents a node in the dialog graph (either DLGEntry or DLGReply).

    DLG nodes represent individual dialog lines (either NPC entries or player replies)
    in the conversation tree. Each node contains text, scripts, animations, camera settings,
    and links to other nodes. Nodes are stored in EntryList or ReplyList arrays in the GFF.

    References:
    ----------
        vendor/reone/include/reone/resource/parser/gff/dlg.h:61-113 (DLG_EntryReplyList struct)
        vendor/reone/src/libs/resource/parser/gff/dlg.cpp:67-172 (DLG_EntryReplyList parsing)
        vendor/KotOR.js/src/resource/DLGNode.ts (DLG node structure)
        vendor/Kotor.NET/Kotor.NET/Resources/KotorDLG/DLG.cs (DLG node structure)
        Note: DLG nodes are GFF structs within EntryList or ReplyList arrays

    Attributes:
    ----------
        links: List of DLGLink objects connecting to other nodes.
            Reference: reone/dlg.h:86,102 (EntriesList/RepliesList vectors)
            Reference: reone/dlg.cpp:95-96,102-103 (EntriesList/RepliesList parsing)
            Outgoing edges in the dialog graph.
        
        list_index: Index of this node in EntryList or ReplyList.
            Reference: reone/dlg.cpp:95-96,102-103 (list iteration)
            Used for GFF path resolution (e.g., "EntryList\\0").
        
        text: "Text" field. Localized string for the dialog line.
            Reference: reone/dlg.h:109 (Text field as pair<int, string>)
            Reference: reone/dlg.cpp:147 (Text parsing)
            The actual dialog text displayed to the player.
        
        speaker: "Speaker" field. Speaker identifier (DLGEntry only).
            Reference: reone/dlg.h:107 (Speaker field)
            Reference: reone/dlg.cpp:146 (Speaker parsing)
            Identifies who is speaking this line.
        
        script1: "Script" field. Primary script to execute.
            Reference: reone/dlg.h:103 (Script field)
            Reference: reone/dlg.cpp:144 (Script parsing)
            Script ResRef executed when this node is reached.
        
        script2: "Script2" field. Secondary script (KotOR 2).
            Reference: reone/dlg.h:104 (Script2 field)
            Reference: reone/dlg.cpp:145 (Script2 parsing)
            Additional script ResRef for KotOR 2.
        
        sound: "Sound" field. Sound effect ResRef.
            Reference: reone/dlg.h:105 (Sound field)
            Reference: reone/dlg.cpp:148 (Sound parsing)
            Sound effect played with this dialog line.
        
        vo_resref: "VO_ResRef" field. Voice-over ResRef.
            Reference: reone/dlg.h:111 (VO_ResRef field)
            Reference: reone/dlg.cpp:149 (VO_ResRef parsing)
            Voice-over audio file for this line.
        
        animations: "AnimList" field. List of dialog animations.
            Reference: reone/dlg.h:51-54 (DLG_EntryReplyList_AnimList struct)
            Reference: reone/dlg.cpp:53-58,82-84 (AnimList parsing)
            Animation references for this dialog line.
        
        camera_angle: "CameraAngle" field. Camera angle setting.
            Reference: reone/dlg.h:79 (CameraAngle field)
            Reference: reone/dlg.cpp:88 (CameraAngle parsing)
        
        camera_id: "CameraID" field. Camera ID reference.
            Reference: reone/dlg.h:81 (CameraID field)
            Reference: reone/dlg.cpp:90 (CameraID parsing)
        
        camera_anim: "CameraAnimation" field. Camera animation ID.
            Reference: reone/dlg.h:80 (CameraAnimation field)
            Reference: reone/dlg.cpp:89 (CameraAnimation parsing)
        
        camera_fov: "CamFieldOfView" field. Camera field of view.
            Reference: reone/dlg.h:76 (CamFieldOfView field)
            Reference: reone/dlg.cpp:85 (CamFieldOfView parsing)
        
        camera_height: "CamHeightOffset" field. Camera height offset.
            Reference: reone/dlg.h:77 (CamHeightOffset field)
            Reference: reone/dlg.cpp:86 (CamHeightOffset parsing)
        
        camera_effect: "CamVidEffect" field. Camera video effect ID.
            Reference: reone/dlg.h:78 (CamVidEffect field)
            Reference: reone/dlg.cpp:87 (CamVidEffect parsing)
        
        target_height: "TarHeightOffset" field. Target height offset.
            Reference: reone/dlg.h:108 (TarHeightOffset field)
            Reference: reone/dlg.cpp:150 (TarHeightOffset parsing)
        
        fade_type: "FadeType" field. Fade effect type.
            Reference: reone/dlg.h:91 (FadeType field)
            Reference: reone/dlg.cpp:92 (FadeType parsing)
        
        fade_color: "FadeColor" field. Fade color (vec3).
            Reference: reone/dlg.h:88 (FadeColor field)
            Reference: reone/dlg.cpp:99 (FadeColor parsing)
        
        fade_delay: "FadeDelay" field. Fade delay in seconds.
            Reference: reone/dlg.h:89 (FadeDelay field)
            Reference: reone/dlg.cpp:100 (FadeDelay parsing)
        
        fade_length: "FadeLength" field. Fade duration in seconds.
            Reference: reone/dlg.h:90 (FadeLength field)
            Reference: reone/dlg.cpp:101 (FadeLength parsing)
        
        delay: "Delay" field. Dialog delay in milliseconds.
            Reference: reone/dlg.h:84 (Delay field)
            Reference: reone/dlg.cpp:93 (Delay parsing)
        
        listener: "Listener" field. Listener identifier.
            Reference: reone/dlg.h:92 (Listener field)
            Reference: reone/dlg.cpp:94 (Listener parsing)
        
        quest: "Quest" field. Quest identifier string.
            Reference: reone/dlg.h:98 (Quest field)
            Reference: reone/dlg.cpp:140 (Quest parsing)
        
        quest_entry: "QuestEntry" field. Quest entry index.
            Reference: reone/dlg.h:99 (QuestEntry field)
            Reference: reone/dlg.cpp:141 (QuestEntry parsing)
        
        plot_index: "PlotIndex" field. Plot flag index.
            Reference: reone/dlg.h:95 (PlotIndex field)
            Reference: reone/dlg.cpp:138 (PlotIndex parsing)
        
        plot_xp_percentage: "PlotXPPercentage" field. XP percentage for plot.
            Reference: reone/dlg.h:96 (PlotXPPercentage field)
            Reference: reone/dlg.cpp:139 (PlotXPPercentage parsing)
        
        emotion_id: "Emotion" field. Emotion animation ID.
            Reference: reone/dlg.h:85 (Emotion field)
            Reference: reone/dlg.cpp:94 (Emotion parsing)
            Reference: emotion.2da for valid IDs.
        
        facial_id: "FacialAnim" field. Facial animation ID.
            Reference: reone/dlg.h:87 (FacialAnim field)
            Reference: reone/dlg.cpp:98 (FacialAnim parsing)
            Reference: facialanim.2da for valid IDs.
        
        alien_race_node: "AlienRaceNode" field. KotOR 2 alien race ID.
            Reference: reone/dlg.h:74 (AlienRaceNode field)
            Reference: reone/dlg.cpp:81 (AlienRaceNode parsing)
            Reference: racialtypes.2da for valid IDs.
        
        node_id: "NodeID" field. KotOR 2 node identifier.
            Reference: reone/dlg.h:93 (NodeID field)
            Reference: reone/dlg.cpp:135 (NodeID parsing)
            Unique identifier for this node.
        
        post_proc_node: "PostProcNode" field. KotOR 2 post-processing node ID.
            Reference: reone/dlg.h:97 (PostProcNode field)
            Reference: reone/dlg.cpp:137 (PostProcNode parsing)
        
        unskippable: "NodeUnskippable" field. KotOR 2 unskippable flag.
            Reference: reone/dlg.h:94 (NodeUnskippable field)
            Reference: reone/dlg.cpp:136 (NodeUnskippable parsing)
        
        record_vo: "RecordVO" field. KotOR 2 record VO flag.
            Reference: reone/dlg.h:101 (RecordVO field)
            Reference: reone/dlg.cpp:142 (RecordVO parsing)
        
        record_no_vo_override: "RecordNoVOOverri" field. KotOR 2 override flag.
            Reference: reone/dlg.h:100 (RecordNoVOOverri field)
            Reference: reone/dlg.cpp:143 (RecordNoVOOverri parsing)
        
        vo_text_changed: "VOTextChanged" field. KotOR 2 VO text changed flag.
            Reference: reone/dlg.h:110 (VOTextChanged field)
            Reference: reone/dlg.cpp:151 (VOTextChanged parsing)
        
        wait_flags: "WaitFlags" field. Wait flags bitmask.
            Reference: reone/dlg.h:112 (WaitFlags field)
            Reference: reone/dlg.cpp:152 (WaitFlags parsing)
        
        sound_exists: "SoundExists" field. Sound existence flag.
            Reference: reone/dlg.h:106 (SoundExists field)
            Reference: reone/dlg.cpp:148 (SoundExists parsing)
        
        script1_param1-6: "ActionParam1-5" and "ActionParamStrA" fields. KotOR 2 script parameters.
            Reference: reone/dlg.h:62-73 (ActionParam fields)
            Reference: reone/dlg.cpp:69-80 (ActionParam parsing)
            Parameters passed to script1.
        
        script2_param1-6: "ActionParam1b-5b" and "ActionParamStrB" fields. KotOR 2 script parameters.
            Reference: reone/dlg.h:63-73 (ActionParam fields)
            Reference: reone/dlg.cpp:69-80 (ActionParam parsing)
            Parameters passed to script2.
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
