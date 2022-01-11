from __future__ import annotations

from enum import IntEnum
from typing import List, Optional

from pykotor.common.language import LocalizedString
from pykotor.common.misc import Game, ResRef, Color
from pykotor.resource.formats.gff import GFF


class DLG:
    """
    Stores dialog data.
    """

    def __init__(self):
        self.starters: List[DLGStartLink] = []
        self.stunts: List[DLGStunt] = []

        self.ambient_track: ResRef = ResRef.from_blank()
        self.animated_cut: int = 0
        self.camera_model: ResRef = ResRef.from_blank()
        self.computer_type: DLGComputerType = DLGComputerType.Modern
        self.conversation_type: DLGConversationType = DLGConversationType.Human
        self.on_aborted: ResRef = ResRef.from_blank()
        self.on_ended: ResRef = ResRef.from_blank()
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

    def all_entries(self) -> List[DLGEntry]:
        ...

    def all_replies(self) -> List[DLGReply]:
        ...


class DLGComputerType(IntEnum):
    Modern = 0
    Ancient = 1


class DLGConversationType(IntEnum):
    Human = 0
    Computer = 1


class DLGNode:
    def __init__(self):
        self.comment: str = ""

        self.camera_angle: int = 0
        self.delay: int = 0
        self.fade_type: int = 0
        self.listener: str = ""
        self.plot_index: int = 0
        self.plot_xp_percentage: float = 0.0
        self.quest: str = ""
        self.script1: ResRef.from_blank()
        self.sound: ResRef.from_blank()
        self.sound_exists: bool = False
        self.text: LocalizedString = LocalizedString.from_invalid()
        self.vo_resref: ResRef = ResRef.from_blank()
        self.wait_flags: int = 0

        self.animations: List[DLGAnimation] = []

        self.quest_entry: Optional[int] = 0
        self.fade_color: Optional[Color] = None
        self.fade_delay: Optional[float] = None
        self.fade_length: Optional[float] = None
        self.camera_anim: Optional[int] = None
        self.camera_id: Optional[int] = None
        self.camera_fov: Optional[float] = None
        self.camera_height: Optional[float] = None
        self.camera_effect: Optional[int] = None
        self.target_height: Optional[float] = None

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
        self.emotion: int = 0
        self.facial_id: int = 0
        self.unskippable: bool = False
        self.node_id: int = 0
        self.post_proc_node: int = 0

        self.record_no_vo_override: bool = False
        self.record_vo: bool = False
        self.vo_text_changed: bool = False


class DLGReply(DLGNode):
    def __init__(self):
        super().__init__()
        self.entries: List[DLGEntry] = []


class DLGEntry(DLGNode):
    def __init__(self):
        super().__init__()
        self.replies: List[DLGReply] = []
        self.speaker: str = ""


class DLGAnimation:
    def __init__(self):
        self.animation_id: int = 0
        self.participant: str = ""


class DLGLink:
    def __init__(self):
        self.active: ResRef = ResRef.from_blank()
        self.index: int = 0

        # KotOR 2 Only:
        self.active2: ResRef = ResRef.from_blank()
        self.not1: bool = False
        self.not2: bool = False
        self.logic: bool = False

        self.script1_param1: int = 0
        self.script1_param2: int = 0
        self.script1_param3: int = 0
        self.script1_param4: int = 0
        self.script1_param5: int = 0
        self.script1_param6: str = ""
        self.script2_param1: int = 0

        self.script2_param2: int = 0
        self.script2_param3: int = 0
        self.script2_param4: int = 0
        self.script2_param5: int = 0
        self.script2_param6: str = ""


class DLGNodeLink(DLGLink):
    def __init__(self):
        super().__init__()
        self.is_child: bool = False
        self.comment: str = ""


class DLGStartLink(DLGLink):
    def __init__(self):
        super().__init__()


class DLGStunt:
    def __init__(self):
        self.participant: str = ""
        self.stunt_model: ResRef = ResRef.from_blank()


def construct_dlg(gff: GFF) -> DLG:
    dlg = DLG()

    return dlg


def dismantle_dlg(dlg: DLG, game: Game = Game.K2, *, use_deprecated: bool = True) -> GFF:
    gff = GFF()

    return gff
