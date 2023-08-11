from __future__ import annotations

from enum import IntEnum

from pykotor.common.geometry import Vector3
from pykotor.common.language import Gender, Language, LocalizedString
from pykotor.common.misc import Color, Game, ResRef
from pykotor.resource.formats.gff import (
    GFF,
    GFFContent,
    GFFList,
    GFFStruct,
    read_gff,
    write_gff,
)
from pykotor.resource.formats.gff.gff_auto import bytes_gff
from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES, ResourceType


class DLG:
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

    def __init__(
        self,
        blank_node: bool = True,
    ):
        self.starters: list[DLGLink] = []
        self.stunts: list[DLGStunt] = []

        if blank_node:
            # Add bare minimum to be openable by DLGEditor
            starter = DLGLink()
            entry = DLGEntry()
            entry.text.set(Language.ENGLISH, Gender.MALE, "")
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
        self.record_no_vo: bool = False

        # Deprecated:
        self.delay_entry: int = 0
        self.delay_reply: int = 0

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
                print("{}-> {}".format(" " * indent, link.node.text))
                seen_links.append(link)

                if link.node not in seen_nodes:
                    seen_nodes.append(link.node)
                    self._print_tree(
                        link.node.links, indent + 3, seen_links, seen_nodes
                    )
            else:
                print("{}-> [LINK] {}".format(" " * indent, link.node.text))

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
        replies = []

        links = (
            [_ for link in self.starters for _ in link.node.links]
            if links is None
            else links
        )
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


class DLGComputerType(IntEnum):
    Modern = 0
    Ancient = 1


class DLGConversationType(IntEnum):
    Human = 0
    Computer = 1
    Other = 2


class DLGNode:
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

    def __init__(
        self,
    ):
        self.comment: str = ""
        self.links: list[DLGLink] = []

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

    def __repr__(
        self,
    ):
        return str(self.text.get(Language.ENGLISH, Gender.MALE))


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
    ):
        super().__init__()
        self.speaker: str = ""


class DLGAnimation:
    """Represents a unit of animation executed during a node."""

    def __init__(
        self,
    ):
        self.animation_id: int = 6
        self.participant: str = ""


class DLGLink:
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

    def __init__(
        self,
        node: DLGNode = DLGNode,
    ):
        self.active1: ResRef = ResRef.from_blank()
        self.node: DLGNode = node

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


class DLGStunt:
    """Attributes
    participant: "Participant" field.
    stunt_model: "StuntModel" field.
    """

    def __init__(
        self,
    ):
        self.participant: str = ""
        self.stunt_model: ResRef = ResRef.from_blank()


def construct_dlg(
    gff: GFF,
) -> DLG:
    def construct_node(
        gff_struct: GFFStruct,
        node: DLGNode,
    ):
        node.text = gff_struct.acquire("Text", LocalizedString.from_invalid())
        node.listener = gff_struct.acquire("Listener", "")
        node.vo_resref = gff_struct.acquire("VO_ResRef", ResRef.from_blank())
        node.script1 = gff_struct.acquire("Script", ResRef.from_blank())
        node.delay = (
            -1
            if gff_struct.acquire("Delay", 0) == 0xFFFFFFFF
            else gff_struct.acquire("Delay", 0)
        )
        node.comment = gff_struct.acquire("Comment", "")
        node.sound = gff_struct.acquire("Sound", ResRef.from_blank())
        node.quest = gff_struct.acquire("Quest", "")
        node.plot_index = gff_struct.acquire("PlotIndex", -1)
        node.plot_xp_percentage = gff_struct.acquire("PlotXPPercentage", 0.0)
        node.wait_flags = gff_struct.acquire("WaitFlags", 0)
        node.camera_angle = gff_struct.acquire("CameraAngle", 0)
        node.fade_type = gff_struct.acquire("FadeType", 0)
        node.sound_exists = gff_struct.acquire("SoundExists", 0)
        node.vo_text_changed = gff_struct.acquire("Changed", 0)

        for anim_struct in gff_struct.acquire("AnimList", GFFList()):
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
        node.unskippable = gff_struct.acquire("NodeUnskippable", 0)
        node.post_proc_node = gff_struct.acquire("PostProcNode", 0)
        node.record_no_vo_override = gff_struct.acquire("RecordNoVOOverri", 0)
        node.record_vo = gff_struct.acquire("RecordVO", 0)
        node.vo_text_changed = gff_struct.acquire("VOTextChanged", 0)

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
            node.fade_color = Color.from_bgr_vector3(
                gff_struct.acquire("FadeColor", Vector3.from_null())
            )

    def construct_link(
        gff_struct: GFFStruct,
        link: DLGLink,
    ):
        link.active1 = gff_struct.acquire("Active", ResRef.from_blank())
        link.active2 = gff_struct.acquire("Active2", ResRef.from_blank())
        link.logic = gff_struct.acquire("Logic", 0)
        link.active1_not = gff_struct.acquire("Not", 0)
        link.active2_not = gff_struct.acquire("Not2", 0)
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

    dlg = DLG(False)

    root = gff.root

    all_entries = [DLGEntry() for _ in range(len(root.acquire("EntryList", GFFList())))]
    all_replies = [DLGReply() for _ in range(len(root.acquire("ReplyList", GFFList())))]

    dlg.word_count = root.acquire("NumWords", 0)
    dlg.on_abort = root.acquire("EndConverAbort", ResRef.from_blank())
    dlg.on_end = root.acquire("EndConversation", ResRef.from_blank())
    dlg.skippable = bool(root.acquire("Skippable", 0))
    dlg.ambient_track = root.acquire("AmbientTrack", ResRef.from_blank())
    dlg.animated_cut = root.acquire("AnimatedCut", 0)
    dlg.camera_model = root.acquire("CameraModel", ResRef.from_blank())
    dlg.computer_type = DLGComputerType(root.acquire("ComputerType", 0))
    dlg.conversation_type = DLGConversationType(root.acquire("ConversationType", 0))
    dlg.old_hit_check = root.acquire("OldHitCheck", 0)
    dlg.unequip_hands = root.acquire("UnequipHItem", 0)
    dlg.unequip_items = root.acquire("UnequipItems", 0)
    dlg.vo_id = root.acquire("VO_ID", "")
    dlg.alien_race_owner = root.acquire("AlienRaceOwner", 0)
    dlg.post_proc_owner = root.acquire("PostProcOwner", 0)
    dlg.record_no_vo = root.acquire("RecordNoVO", 0)
    dlg.next_node_id = root.acquire("NextNodeID", 0)
    dlg.delay_entry = root.acquire("DelayEntry", 0)
    dlg.delay_reply = root.acquire("DelayReply", 0)

    for stunt_struct in root.acquire("StuntList", GFFList()):
        stunt = DLGStunt()
        dlg.stunts.append(stunt)
        stunt.participant = stunt_struct.acquire("Participant", "")
        stunt.stunt_model = stunt_struct.acquire("StuntModel", ResRef.from_blank())

    for link_struct in root.acquire("StartingList", GFFList()):
        entry_index = link_struct.acquire("Index", 0)
        link = DLGLink()
        dlg.starters.append(link)
        link.node = all_entries[entry_index]
        construct_link(link_struct, link)

    for i, entry_struct in enumerate(root.acquire("EntryList", GFFList())):
        entry = all_entries[i]
        entry.speaker = entry_struct.acquire("Speaker", "")
        construct_node(entry_struct, entry)

        for link_struct in entry_struct.acquire("RepliesList", GFFList()):
            link = DLGLink()
            link.node = all_replies[link_struct.acquire("Index", 0)]
            link.is_child = bool(link_struct.acquire("IsChild", 0))
            link.comment = link_struct.acquire("LinkComment", 0)

            entry.links.append(link)
            construct_link(link_struct, link)

    for i, reply_struct in enumerate(root.acquire("ReplyList", GFFList())):
        reply = all_replies[i]
        construct_node(reply_struct, reply)

        for link_struct in reply_struct.acquire("EntriesList", GFFList()):
            link = DLGLink()
            link.node = all_entries[link_struct.acquire("Index", 0)]
            link.is_child = bool(link_struct.acquire("IsChild", 0))
            link.comment = link_struct.acquire("LinkComment", 0)

            reply.links.append(link)
            construct_link(link_struct, link)

    return dlg


def dismantle_dlg(
    dlg: DLG,
    game: Game = Game.K2,
    *,
    use_deprecated: bool = True,
) -> GFF:
    def dismantle_link(
        gff_struct: GFFStruct,
        link: DLGLink,
        nodes: list,
    ):
        gff_struct.set_resref("Active", link.active1)
        gff_struct.set_uint32("Index", nodes.index(link.node))
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
        gff_struct.set_locstring("Text", node.text)
        gff_struct.set_string("Listener", node.listener)
        gff_struct.set_resref("VO_ResRef", node.vo_resref)
        gff_struct.set_resref("Script", node.script1)
        gff_struct.set_uint32("Delay", node.delay)
        gff_struct.set_string("Comment", node.comment)
        gff_struct.set_resref("Sound", node.sound)
        gff_struct.set_string("Quest", node.quest)
        gff_struct.set_int32("PlotIndex", node.plot_index)
        gff_struct.set_single("PlotXPPercentage", node.plot_xp_percentage)
        gff_struct.set_uint32("WaitFlags", node.wait_flags)
        gff_struct.set_uint32("CameraAngle", node.camera_angle)
        gff_struct.set_uint8("FadeType", node.fade_type)
        gff_struct.set_uint8("SoundExists", node.sound_exists)
        gff_struct.set_uint8("Changed", node.vo_text_changed)

        anim_list = gff_struct.set_list("AnimList", GFFList())
        for anim in node.animations:
            anim_struct = anim_list.add(0)
            anim_struct.set_uint16("Animation", anim.animation_id)
            anim_struct.set_string("Participant", anim.participant)

        if node.quest_entry is not None:
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

        link_list = gff_struct.set_list(list_name, GFFList())
        for i, link in enumerate(node.links):
            link_struct = link_list.add(i)
            dismantle_link(link_struct, link, nodes)

    all_entries = dlg.all_entries()
    all_replies = dlg.all_replies()

    gff = GFF(GFFContent.DLG)

    root = gff.root
    root.set_uint32("NumWords", dlg.word_count)
    root.set_resref("EndConverAbort", dlg.on_abort)
    root.set_resref("EndConversation", dlg.on_end)
    root.set_uint8("Skippable", dlg.skippable)
    root.set_resref("AmbientTrack", dlg.ambient_track)
    root.set_uint8("AnimatedCut", dlg.animated_cut)
    root.set_resref("CameraModel", dlg.camera_model)
    root.set_uint8("ComputerType", dlg.computer_type.value)
    root.set_int32("ConversationType", dlg.conversation_type.value)
    root.set_uint8("OldHitCheck", dlg.old_hit_check)
    root.set_uint8("UnequipHItem", dlg.unequip_hands)
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
        dismantle_link(starting_struct, starter, all_entries)

    entries_list = root.set_list("EntryList", GFFList())
    for i, entry in enumerate(all_entries):
        entries_struct = entries_list.add(i)
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
    gff = dismantle_dlg(dlg, game, use_deprecated=use_deprecated)
    write_gff(gff, target, file_format)


def bytes_dlg(
    dlg: DLG,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
) -> bytes:
    gff = dismantle_dlg(dlg, game, use_deprecated=use_deprecated)
    return bytes_gff(gff, file_format)
