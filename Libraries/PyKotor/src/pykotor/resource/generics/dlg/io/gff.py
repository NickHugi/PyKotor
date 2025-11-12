"""GFF format support for dialog system."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypeVar

from loggerplus import RobustLogger

from pykotor.common.language import LocalizedString
from pykotor.common.misc import Color, Game, ResRef
from pykotor.resource.formats.gff.gff_auto import bytes_gff, read_gff, write_gff
from pykotor.resource.formats.gff.gff_data import GFF, GFFContent, GFFList
from pykotor.resource.generics.dlg.anims import DLGAnimation
from pykotor.resource.generics.dlg.base import DLG, DLGComputerType, DLGConversationType
from pykotor.resource.generics.dlg.links import DLGLink
from pykotor.resource.generics.dlg.nodes import DLGEntry, DLGNode, DLGReply
from pykotor.resource.generics.dlg.stunts import DLGStunt
from pykotor.resource.type import ResourceType
from utility.common.geometry import Vector3

if TYPE_CHECKING:
    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]

    from pykotor.resource.formats.gff.gff_data import GFFStruct
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES

T = TypeVar("T", bound=DLGNode)


def construct_dlg(  # noqa: C901, PLR0915
    gff: GFF,
) -> DLG:
    """Constructs a DLG from a GFF file.

    Parses DLG (dialog) data from a GFF file, reading all fields including
    entries, replies, links, stunts, and conversation metadata.

    References:
    ----------
        vendor/reone/src/libs/resource/parser/gff/dlg.cpp:129-165 (parseDLG function)
        vendor/reone/include/reone/resource/parser/gff/dlg.h:115-141 (DLG struct definition)
        vendor/KotOR.js/src/resource/DLGObject.ts:77-493 (DLG initialization from GFF)
        vendor/xoreos-tools/src/xml/dlgdumper.cpp (DLG to XML conversion)
        Original BioWare Odyssey Engine (DLG GFF structure specification)

    Args:
    ----
        gff: GFF - The GFF file to construct the DLG from

    Returns:
    -------
        DLG - The constructed DLG object
    """

    def construct_node(  # noqa: C901, PLR0915
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
        # vendor/reone/src/libs/resource/parser/gff/dlg.cpp:122 (Text field as pair<int, string>)
        # vendor/reone/include/reone/resource/parser/gff/dlg.h:109 (Text field)
        node.text = gff_struct.acquire("Text", LocalizedString.from_invalid())
        # vendor/reone/src/libs/resource/parser/gff/dlg.cpp:103 (Listener field)
        node.listener = gff_struct.acquire("Listener", "")
        # vendor/reone/src/libs/resource/parser/gff/dlg.cpp:124 (VO_ResRef field)
        node.vo_resref = gff_struct.acquire("VO_ResRef", ResRef.from_blank())
        # vendor/reone/src/libs/resource/parser/gff/dlg.cpp:116 (Script field)
        node.script1 = gff_struct.acquire("Script", ResRef.from_blank())
        # vendor/reone/src/libs/resource/parser/gff/dlg.cpp:94 (Delay field as uint32)
        # Discrepancy: PyKotor converts 0xFFFFFFFF to -1, reone stores as-is
        delay: int = gff_struct.acquire("Delay", 0)
        node.delay = -1 if delay == 0xFFFFFFFF else delay  # noqa: PLR2004
        # vendor/reone/src/libs/resource/parser/gff/dlg.cpp:83 (Comment field)
        node.comment = gff_struct.acquire("Comment", "")
        # vendor/reone/src/libs/resource/parser/gff/dlg.cpp:118 (Sound field)
        node.sound = gff_struct.acquire("Sound", ResRef.from_blank())
        # vendor/reone/src/libs/resource/parser/gff/dlg.cpp:98 (Quest field)
        node.quest = gff_struct.acquire("Quest", "")
        # vendor/reone/src/libs/resource/parser/gff/dlg.cpp:95 (PlotIndex field)
        node.plot_index = gff_struct.acquire("PlotIndex", -1)
        # vendor/reone/src/libs/resource/parser/gff/dlg.cpp:96 (PlotXPPercentage field as float)
        node.plot_xp_percentage = gff_struct.acquire("PlotXPPercentage", 0.0)
        # vendor/reone/src/libs/resource/parser/gff/dlg.cpp:125 (WaitFlags field as uint32)
        node.wait_flags = gff_struct.acquire("WaitFlags", 0)
        # vendor/reone/src/libs/resource/parser/gff/dlg.cpp:79 (CameraAngle field)
        node.camera_angle = gff_struct.acquire("CameraAngle", 0)
        # vendor/reone/src/libs/resource/parser/gff/dlg.cpp:91 (FadeType field as uint8)
        node.fade_type = gff_struct.acquire("FadeType", 0)
        # vendor/reone/src/libs/resource/parser/gff/dlg.cpp:106 (SoundExists field as uint8)
        node.sound_exists = gff_struct.acquire("SoundExists", 0)
        # vendor/reone/src/libs/resource/parser/gff/dlg.cpp:110 (VOTextChanged field as uint8)
        node.vo_text_changed = gff_struct.acquire("VOTextChanged", default=False)

        # vendor/reone/src/libs/resource/parser/gff/dlg.cpp:82-84 (AnimList parsing)
        # vendor/reone/include/reone/resource/parser/gff/dlg.h:75 (AnimList vector)
        # AnimList contains participant animations for this dialog node
        anim_list: GFFList = gff_struct.acquire("AnimList", GFFList())
        for anim_struct in anim_list:
            anim = DLGAnimation()
            # vendor/reone/src/libs/resource/parser/gff/dlg.cpp:55 (Animation field)
            anim.animation_id = anim_struct.acquire("Animation", 0)
            # PyKotor-specific hack: Some animation IDs are offset by 10000
            # Discrepancy: reone doesn't apply this offset, may be KotOR-specific quirk
            if anim.animation_id > 10000:  # HACK(th3w1zard1): can't remember why this was needed.  # noqa: PLR2004
                anim.animation_id -= 10000
            # vendor/reone/src/libs/resource/parser/gff/dlg.cpp:56 (Participant field)
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

    # vendor/reone/src/libs/resource/parser/gff/dlg.cpp:147 (NumWords field)
    dlg.word_count = root.acquire("NumWords", 0)
    # vendor/reone/src/libs/resource/parser/gff/dlg.cpp:141 (EndConverAbort field)
    dlg.on_abort = root.acquire("EndConverAbort", ResRef.from_blank())
    # vendor/reone/src/libs/resource/parser/gff/dlg.cpp:142 (EndConversation field)
    dlg.on_end = root.acquire("EndConversation", ResRef.from_blank())
    # vendor/reone/src/libs/resource/parser/gff/dlg.cpp:154 (Skippable field)
    dlg.skippable = root.acquire("Skippable", default=False)
    # vendor/reone/src/libs/resource/parser/gff/dlg.cpp:132 (AmbientTrack field)
    dlg.ambient_track = root.acquire("AmbientTrack", ResRef.from_blank())
    # vendor/reone/src/libs/resource/parser/gff/dlg.cpp:133 (AnimatedCut field)
    dlg.animated_cut = root.acquire("AnimatedCut", 0)
    # vendor/reone/src/libs/resource/parser/gff/dlg.cpp:134 (CameraModel field)
    dlg.camera_model = root.acquire("CameraModel", ResRef.from_blank())
    # vendor/reone/src/libs/resource/parser/gff/dlg.cpp:135 (ComputerType field)
    dlg.computer_type = DLGComputerType(root.acquire("ComputerType", 0))
    # vendor/reone/src/libs/resource/parser/gff/dlg.cpp:136 (ConversationType field)
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

    # vendor/reone/src/libs/resource/parser/gff/dlg.cpp:158-160 (StuntList parsing)
    # vendor/reone/include/reone/resource/parser/gff/dlg.h:137 (StuntList vector)
    # StuntList contains stunt model references for special dialog animations
    stunt_list: GFFList = root.acquire("StuntList", GFFList())
    for stunt_struct in stunt_list:
        stunt = DLGStunt()
        dlg.stunts.append(stunt)
        # vendor/reone/src/libs/resource/parser/gff/dlg.cpp:62 (Participant field)
        stunt.participant = stunt_struct.acquire("Participant", "")
        # vendor/reone/src/libs/resource/parser/gff/dlg.cpp:63 (StuntModel field)
        stunt.stunt_model = stunt_struct.acquire("StuntModel", ResRef.from_blank())

    starting_list: GFFList = root.acquire("StartingList", GFFList())
    for link_list_index, link_struct in enumerate(starting_list):
        node_struct_id = link_struct.acquire("Index", 0)
        try:
            starter_node: DLGEntry = all_entries[node_struct_id]
        except IndexError:
            context_link_msg: str = f"(StartingList/{link_list_index})"  # noqa: SLF001
            RobustLogger().error(f"'Index' field value '{node_struct_id}' at {context_link_msg} does not point to a valid ReplyList node, omitting...")
        else:
            link: DLGLink = DLGLink(starter_node, link_list_index)
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
                reply_node: DLGReply = all_replies[node_struct_id]
            except IndexError:
                context_link_msg: str = f"(EntryList/{node_list_index}/RepliesList/{link_list_index})"  # noqa: SLF001
                RobustLogger().error(f"'Index' field value '{node_struct_id}' at {context_link_msg} does not point to a valid ReplyList node, omitting...")
            else:
                link: DLGLink = DLGLink(reply_node, link_list_index)
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
            node_struct_id: int = link_struct.acquire("Index", 0)
            try:
                entry_node: DLGEntry = all_entries[node_struct_id]
            except IndexError:
                context_link_msg: str = f"(ReplyList/{node_list_index}/EntriesList/{link_list_index})"  # noqa: SLF001
                RobustLogger().error(f"'Index' field value '{node_struct_id}' at {context_link_msg} does not point to a valid EntryList node, omitting...")
            else:
                link: DLGLink = DLGLink(entry_node, link_list_index)
                link.is_child = bool(link_struct.acquire("IsChild", default=False))
                link.comment = link_struct.acquire("LinkComment", "")

                reply.links.append(link)
                construct_link(link_struct, link)

    return dlg


def dismantle_dlg(  # noqa: PLR0912, C901, PLR0915
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

    def dismantle_node(  # noqa: C901, PLR0912, PLR0915
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
            anim_struct.set_uint16(
                "Animation",
                (  # HACK(th3w1zard1): can't remember why the 10000 check is needed.
                    anim.animation_id
                    if anim.animation_id <= 10000  # noqa: PLR2004
                    else anim.animation_id + 10000
                ),
            )
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
        sorted_links: list[DLGLink] = sorted(node.links, key=lambda link: (link.list_index == -1, link.list_index))
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
