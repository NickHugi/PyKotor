from __future__ import annotations

import os
import pathlib
import sys
import unittest
from unittest import TestCase

from pykotor.common.language import Gender, Language, LocalizedString

THIS_SCRIPT_PATH: pathlib.Path = pathlib.Path(__file__).resolve()
PYKOTOR_PATH: pathlib.Path = THIS_SCRIPT_PATH.parents[3].resolve()
UTILITY_PATH: pathlib.Path = THIS_SCRIPT_PATH.parents[5].joinpath("Utility", "src").resolve()


def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from typing import TYPE_CHECKING

from pykotor.common.misc import Game, ResRef
from pykotor.extract.installation import Installation
from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.dlg import (
    DLG,
    DLGAnimation,
    DLGEntry,
    DLGLink,
    DLGNode,
    DLGReply,
    DLGStunt,
    construct_dlg,
    dismantle_dlg,
)
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:

    from pykotor.resource.formats.gff import GFF

TEST_FILE = "tests/test_files/test.dlg"
TEST_K1_FILE = "tests/test_files/test_k1.dlg"
K1_PATH = os.environ.get("K1_PATH")
K2_PATH = os.environ.get("K2_PATH")


class TestDLG(TestCase):
    def setUp(self):
        self.log_messages: list[str] = [os.linesep]

    def log_func(self, *args):
        self.log_messages.extend(args)

    def test_k1_reconstruct(self):
        gff: GFF = read_gff(TEST_K1_FILE)
        reconstructed_gff: GFF = dismantle_dlg(construct_dlg(gff), Game.K1)
        result = gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True)
        output = os.linesep.join(self.log_messages)
        assert result, output

    def test_k1_reconstruct_from_reconstruct(self):
        gff: GFF = read_gff(TEST_K1_FILE)
        reconstructed_gff: GFF = dismantle_dlg(construct_dlg(gff), Game.K1)
        re_reconstructed_gff: GFF = dismantle_dlg(construct_dlg(reconstructed_gff), Game.K1)
        result: bool = reconstructed_gff.compare(re_reconstructed_gff, self.log_func)
        output: str = os.linesep.join(self.log_messages)
        assert result, output

    def test_k1_serialization(self):
        gff: GFF = read_gff(TEST_K1_FILE)
        dlg: DLG = construct_dlg(gff)
        for node in dlg.all_entries():
            assert node == DLGNode.from_dict(node.to_dict())

    def test_k2_serialization(self):
        gff: GFF = read_gff(TEST_FILE)
        dlg: DLG = construct_dlg(gff)
        for node in dlg.all_entries():
            reserialized_dlg_node: DLGNode = DLGNode.from_dict(node.to_dict())
            for attr_name, value in node.__dict__.items():
                reserialized_node_attr_value = reserialized_dlg_node.__dict__[attr_name]
                assert reserialized_node_attr_value == value, attr_name + repr(value) + " vs " + repr(reserialized_node_attr_value)

    def test_k2_reconstruct(self):
        gff: GFF = read_gff(TEST_FILE)
        reconstructed_gff: GFF = dismantle_dlg(construct_dlg(gff), Game.K2)
        reconstructed_gff.root.get_list("EntryList").at(0).set_int32("RecordNoOverri", 1)  # HACK: there's an error in this test file
        assert gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True), os.linesep.join(self.log_messages)

    def test_k2_reconstruct_from_reconstruct(self):
        gff: GFF = read_gff(TEST_FILE)
        reconstructed_gff: GFF = dismantle_dlg(construct_dlg(gff), Game.K2)
        re_reconstructed_gff: GFF = dismantle_dlg(construct_dlg(reconstructed_gff), Game.K2)
        result = reconstructed_gff.compare(re_reconstructed_gff, self.log_func)
        output = os.linesep.join(self.log_messages)
        assert result, output

    @unittest.skipIf(
        not K1_PATH or not pathlib.Path(K1_PATH).joinpath("chitin.key").exists(),
        "K1_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k1_installation(self):
        self.installation = Installation(K1_PATH)  # type: ignore[arg-type]
        for resource in (res for res in self.installation if res.restype() is ResourceType.DLG):
            if resource.identifier() in {"lev40_rodpris2.dlg", "tar02_janice021.dlg"}:
                continue
            self.log_func(f"Testing resource '{resource.identifier()}'")
            gff: GFF = read_gff(resource.data())
            reconstructed_gff: GFF = dismantle_dlg(construct_dlg(gff), Game.K1)
            assert gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True), os.linesep.join(self.log_messages)

    @unittest.skipIf(
        not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
        "K2_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k2_installation(self):
        self.installation = Installation(K2_PATH)  # type: ignore[arg-type]
        for resource in (res for res in self.installation if res.restype() is ResourceType.DLG):
            self.log_func(f"Testing resource '{resource.identifier()}'")
            gff: GFF = read_gff(resource.data())
            reconstructed_gff: GFF = dismantle_dlg(construct_dlg(gff))
            assert gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True), os.linesep.join(self.log_messages)

    def test_io_construct(self):
        gff = read_gff(TEST_FILE)
        dlg = construct_dlg(gff)
        self.validate_io(dlg)

    def test_io_reconstruct(self):
        gff = read_gff(TEST_FILE)
        gff = dismantle_dlg(construct_dlg(gff), Game.K2)
        dlg = construct_dlg(gff)
        self.validate_io(dlg)

    def validate_io(self, dlg: DLG):
        all_entries: list[DLGEntry] = dlg.all_entries()
        all_replies: list[DLGReply] = dlg.all_replies()

        entry0 = all_entries[0]
        entry1 = all_entries[1]
        entry2 = all_entries[2]

        reply0 = all_replies[0]
        reply1 = all_replies[1]

        assert len(all_entries) == 3
        assert len(all_replies) == 2
        assert len(dlg.starters) == 2
        assert len(dlg.stunts) == 2

        assert entry0 in [link.node for link in dlg.starters]
        assert entry2 in [link.node for link in dlg.starters]

        assert len(entry0.links) == 2
        assert reply0 in [link.node for link in entry0.links]
        assert reply1 in [link.node for link in entry0.links]

        assert len(reply0.links) == 1
        assert entry0 in [link.node for link in reply0.links]

        assert len(reply1.links) == 1
        assert entry1 in [link.node for link in reply1.links]

        assert len(entry2.links) == 0

        assert dlg.delay_entry == 13
        assert dlg.delay_reply == 14
        assert dlg.word_count == 1337
        assert dlg.on_abort == "abort"
        assert dlg.on_end == "end"
        assert dlg.skippable == 1
        assert dlg.ambient_track == "track"
        assert dlg.animated_cut == 123
        assert dlg.camera_model == "camm"
        assert dlg.computer_type.value == 1
        assert dlg.conversation_type.value == 1
        assert dlg.old_hit_check == 1
        assert dlg.unequip_hands == 1
        assert dlg.unequip_items == 1
        assert dlg.vo_id == "echo"
        assert dlg.alien_race_owner == 123
        assert dlg.post_proc_owner == 12
        assert dlg.record_no_vo == 3

        assert entry0.listener == "yoohoo"
        assert entry0.text.stringref == -1
        assert entry0.vo_resref == "gand"
        assert entry0.script1 == "num1"
        assert entry0.delay == -1
        assert entry0.comment == "commentto"
        assert entry0.sound == "gonk"
        assert entry0.quest == "quest"
        assert entry0.plot_index == -1
        assert entry0.plot_xp_percentage == 1.0
        assert entry0.wait_flags == 1
        assert entry0.camera_angle == 14
        assert entry0.fade_type == 1
        assert entry0.sound_exists == 1
        assert entry0.alien_race_node == 1
        assert entry0.vo_text_changed == 1
        assert entry0.emotion_id == 4
        assert entry0.facial_id == 2
        assert entry0.node_id == 1
        assert entry0.unskippable == 1
        assert entry0.post_proc_node == 3
        assert entry0.record_vo == 1
        assert entry0.script2 == "num2"
        assert entry0.vo_text_changed == 1
        assert entry0.record_no_vo_override == 1
        assert entry0.camera_id == 32
        assert entry0.speaker == "bark"
        assert entry0.camera_effect == -1
        assert entry0.record_no_vo_override == 1

        assert dlg.stunts[1].participant == "bbb"
        assert dlg.stunts[1].stunt_model == "m01aa_c04_char01"


class TestDLGEntrySerialization(unittest.TestCase):
    def test_dlg_entry_serialization_basic(self):
        entry = DLGEntry()
        entry.comment = "Test Comment"
        entry.camera_angle = 45

        serialized = entry.to_dict()
        deserialized = DLGEntry.from_dict(serialized)

        assert entry.comment == deserialized.comment
        assert entry.camera_angle == deserialized.camera_angle

    def test_dlg_entry_serialization_with_links(self):
        entry = DLGEntry()
        entry.comment = "Entry with links"
        link = DLGLink(entry, 1)
        entry.links.append(link)

        serialized = entry.to_dict()
        deserialized = DLGEntry.from_dict(serialized)

        assert entry.comment == deserialized.comment
        assert len(deserialized.links) == 1
        assert deserialized.links[0].list_index == 1

    def test_dlg_entry_serialization_all_attributes(self):
        entry = DLGEntry()
        entry.comment = "All attributes"
        entry.camera_angle = 30
        entry.listener = "Listener"
        entry.quest = "Quest"
        entry.script1 = ResRef("script1")

        serialized = entry.to_dict()
        deserialized = DLGEntry.from_dict(serialized)

        assert entry.comment == deserialized.comment
        assert entry.camera_angle == deserialized.camera_angle
        assert entry.listener == deserialized.listener
        assert entry.quest == deserialized.quest
        assert entry.script1 == deserialized.script1

    def test_dlg_entry_with_nested_replies(self):
        entry1 = DLGEntry(comment="E248")
        entry2 = DLGEntry(comment="E221")

        reply1 = DLGReply(text=LocalizedString.from_english("R222"))
        reply2 = DLGReply(text=LocalizedString.from_english("R223"))
        reply3 = DLGReply(text=LocalizedString.from_english("R249"))

        entry1.links.append(DLGLink(node=reply1))
        reply1.links.extend([DLGLink(node=entry2), DLGLink(node=reply2)])
        reply2.links.append(DLGLink(node=entry1))
        entry2.links.append(DLGLink(node=reply3))  # Reuse R249

        serialized = entry1.to_dict()
        deserialized = DLGEntry.from_dict(serialized)

        assert entry1.comment == deserialized.comment
        assert len(deserialized.links) == 1
        assert deserialized.links[0].node.text.get(Language.ENGLISH, Gender.MALE) == "R222"
        assert len(deserialized.links[0].node.links) == 2
        assert deserialized.links[0].node.links[0].node.comment == "E221"
        assert deserialized.links[0].node.links[1].node.text.get(Language.ENGLISH, Gender.MALE) == "R223"
        assert deserialized.links[0].node.links[1].node.links[0].node.comment == "E248"

    def test_dlg_entry_with_circular_reference(self):
        # Create DLGEntry and DLGReply objects
        entry1 = DLGEntry(comment="E248")
        entry2 = DLGEntry(comment="E221")

        reply1 = DLGReply(text=LocalizedString.from_english("R222"))
        reply2 = DLGReply(text=LocalizedString.from_english("R249"))

        # Establish links between entries and replies to create circular reference
        entry1.links.append(DLGLink(node=reply1))
        reply1.links.append(DLGLink(node=entry2))
        entry2.links.append(DLGLink(node=reply2))
        reply2.links.append(DLGLink(node=entry1))  # Circular reference

        # Serialize the entry1
        serialized = entry1.to_dict()
        # Deserialize back to object
        deserialized = DLGEntry.from_dict(serialized)

        # Assert top-level comment
        assert entry1.comment == deserialized.comment
        
        # Assert first level link
        assert len(deserialized.links) == 1
        deserialized_reply1 = deserialized.links[0].node
        assert deserialized_reply1.text.get(Language.ENGLISH, Gender.MALE) == "R222"

        # Assert second level link
        assert len(deserialized_reply1.links) == 1
        deserialized_entry2 = deserialized_reply1.links[0].node
        assert deserialized_entry2.comment == "E221"

        # Assert third level link
        assert len(deserialized_entry2.links) == 1
        deserialized_reply2 = deserialized_entry2.links[0].node
        assert deserialized_reply2.text.get(Language.ENGLISH, Gender.MALE) == "R249"

        # Assert circular reference back to the original entry1
        assert len(deserialized_reply2.links) == 1
        deserialized_entry1_circular = deserialized_reply2.links[0].node
        assert deserialized_entry1_circular.comment == "E248"

    def test_dlg_entry_with_multiple_levels(self):
        entry1 = DLGEntry(comment="E248")
        entry2 = DLGEntry(comment="E221")
        entry3 = DLGEntry(comment="E250")

        reply1 = DLGReply(text=LocalizedString.from_english("R222"))
        reply2 = DLGReply(text=LocalizedString.from_english("R223"))
        reply3 = DLGReply(text=LocalizedString.from_english("R249"))
        reply4 = DLGReply(text=LocalizedString.from_english("R225"))
        reply5 = DLGReply(text=LocalizedString.from_english("R224"))

        entry1.links.append(DLGLink(node=reply1))
        reply1.links.extend([DLGLink(node=entry2), DLGLink(node=reply2)])
        reply2.links.append(DLGLink(node=entry3))
        entry3.links.append(DLGLink(node=reply4))
        reply4.links.append(DLGLink(node=reply5))
        entry2.links.append(DLGLink(node=reply3))  # Reuse R249

        serialized = entry1.to_dict()
        deserialized = DLGEntry.from_dict(serialized)

        assert entry1.comment == deserialized.comment
        assert len(deserialized.links) == 1
        assert deserialized.links[0].node.text.get(Language.ENGLISH, Gender.MALE) == "R222"
        assert len(deserialized.links[0].node.links) == 2
        assert deserialized.links[0].node.links[0].node.comment == "E221"
        assert deserialized.links[0].node.links[1].node.text.get(Language.ENGLISH, Gender.MALE) == "R223"
        assert len(deserialized.links[0].node.links[1].node.links) == 1
        assert deserialized.links[0].node.links[1].node.links[0].node.comment == "E250"
        assert len(deserialized.links[0].node.links[1].node.links[0].node.links) == 1
        assert deserialized.links[0].node.links[1].node.links[0].node.links[0].node.text.get(Language.ENGLISH, Gender.MALE) == "R225"
        assert len(deserialized.links[0].node.links[1].node.links[0].node.links[0].node.links) == 1
        assert deserialized.links[0].node.links[1].node.links[0].node.links[0].node.links[0].node.text.get(Language.ENGLISH, Gender.MALE) == "R224"


class TestDLGReplySerialization(unittest.TestCase):
    def test_dlg_reply_serialization_basic(self):
        reply = DLGReply()
        reply.text = LocalizedString.from_english("Hello")
        reply.unskippable = True

        serialized = reply.to_dict()
        deserialized = DLGReply.from_dict(serialized)

        assert reply.text == deserialized.text
        assert reply.unskippable == deserialized.unskippable

    def test_dlg_reply_serialization_with_links(self):
        reply = DLGReply()
        reply.text = LocalizedString.from_english("Reply with links")
        link = DLGLink(reply, 2)
        reply.links.append(link)

        serialized = reply.to_dict()
        deserialized = DLGReply.from_dict(serialized)

        assert reply.text == deserialized.text
        assert len(deserialized.links) == 1
        assert deserialized.links[0].list_index == 2

    def test_dlg_reply_serialization_all_attributes(self):
        reply = DLGReply()
        reply.text = LocalizedString.from_english("Reply with all attributes")
        reply.vo_resref = ResRef("vo_resref")
        reply.wait_flags = 5

        serialized = reply.to_dict()
        deserialized = DLGReply.from_dict(serialized)

        assert reply.text == deserialized.text
        assert reply.vo_resref == deserialized.vo_resref
        assert reply.wait_flags == deserialized.wait_flags

    def test_dlg_reply_with_nested_entries(self):
        # Create replies with localized text
        reply1 = DLGReply()
        reply1.text.set_data(Language.ENGLISH, Gender.MALE, "R222")
        reply2 = DLGReply()
        reply2.text.set_data(Language.ENGLISH, Gender.MALE, "R223")
        reply3 = DLGReply()
        reply3.text.set_data(Language.ENGLISH, Gender.MALE, "R249")

        # Create entries with comments
        entry1 = DLGEntry(comment="E248")
        entry2 = DLGEntry(comment="E221")

        # Link entries and replies together
        reply1.links.append(DLGLink(node=entry1))
        entry1.links.append(DLGLink(node=reply2))
        entry2.links.append(DLGLink(node=reply3))  # Reuse R249

        # Serialize and deserialize reply1
        serialized = reply1.to_dict()
        deserialized = DLGReply.from_dict(serialized)

        # Debug prints
        print("Serialized reply1:", serialized)
        print("Deserialized reply1:", deserialized)

        # Assertions
        # Check the text of the first reply
        original_text = reply1.text.get(Language.ENGLISH, Gender.MALE)
        deserialized_text = deserialized.text.get(Language.ENGLISH, Gender.MALE)
        assert original_text == deserialized_text

        # Check the first link in the deserialized reply
        deserialized_entry1 = deserialized.links[0].node
        assert len(deserialized.links) == 1
        assert deserialized_entry1.comment == "E248"

        # Check the first link in the deserialized entry1
        deserialized_reply2 = deserialized_entry1.links[0].node
        assert len(deserialized_entry1.links) == 1
        assert deserialized_reply2.text.get(Language.ENGLISH, Gender.MALE) == "R223"

        # Check the first link in the deserialized reply2
        deserialized_entry2 = deserialized_reply2.links[0].node
        assert deserialized_entry2.comment == "E221"
        assert len(deserialized_entry2.links) == 1

        # Check the first link in the deserialized entry2
        deserialized_reply3 = deserialized_entry2.links[0].node
        assert deserialized_reply3.text.get(Language.ENGLISH, Gender.MALE) == "R249"

    def test_dlg_reply_with_circular_reference(self):
        reply1 = DLGReply(text=LocalizedString.from_english("R222"))
        reply2 = DLGReply(text=LocalizedString.from_english("R249"))

        entry1 = DLGEntry(comment="E248")
        entry2 = DLGEntry(comment="E221")

        reply1.links.append(DLGLink(node=entry1))
        entry1.links.append(DLGLink(node=reply2))
        reply2.links.append(DLGLink(node=entry2))
        entry2.links.append(DLGLink(node=reply1))  # Circular reference

        serialized = reply1.to_dict()
        deserialized = DLGReply.from_dict(serialized)

        assert reply1.text == deserialized.text
        assert len(deserialized.links) == 1
        assert deserialized.links[0].node.comment == "E248"
        assert len(deserialized.links[0].node.links) == 1
        assert deserialized.links[0].node.links[0].node.text.get(Language.ENGLISH, Gender.MALE) == "R249"
        assert len(deserialized.links[0].node.links[0].node.links) == 1
        assert deserialized.links[0].node.links[0].node.links[0].node.comment == "E221"
        assert len(deserialized.links[0].node.links[0].node.links[0].node.links) == 1
        assert deserialized.links[0].node.links[0].node.links[0].node.links[0].node.text.get(Language.ENGLISH, Gender.MALE) == "R222"

    def test_dlg_reply_with_multiple_levels(self):
        reply1 = DLGReply(text=LocalizedString.from_english("R222"))
        reply2 = DLGReply(text=LocalizedString.from_english("R223"))
        reply3 = DLGReply(text=LocalizedString.from_english("R249"))
        reply4 = DLGReply(text=LocalizedString.from_english("R225"))
        reply5 = DLGReply(text=LocalizedString.from_english("R224"))

        entry1 = DLGEntry(comment="E248")
        entry2 = DLGEntry(comment="E221")
        entry3 = DLGEntry(comment="E250")

        reply1.links.append(DLGLink(node=entry1))
        reply2.links.append(DLGLink(node=entry2))
        entry1.links.append(DLGLink(node=reply2))
        entry2.links.append(DLGLink(node=reply3))  # Reuse R249
        reply3.links.append(DLGLink(node=entry3))
        entry3.links.append(DLGLink(node=reply4))
        reply4.links.append(DLGLink(node=reply5))

        serialized = reply1.to_dict()
        deserialized = DLGReply.from_dict(serialized)

        assert reply1.text == deserialized.text
        assert len(deserialized.links) == 1
        assert deserialized.links[0].node.comment == "E248"
        assert len(deserialized.links[0].node.links) == 1
        assert deserialized.links[0].node.links[0].node.text.get(Language.ENGLISH, Gender.MALE) == "R223"
        assert len(deserialized.links[0].node.links[0].node.links) == 1
        assert deserialized.links[0].node.links[0].node.links[0].node.comment == "E221"
        assert len(deserialized.links[0].node.links[0].node.links[0].node.links) == 1
        assert deserialized.links[0].node.links[0].node.links[0].node.links[0].node.text.get(Language.ENGLISH, Gender.MALE) == "R249"
        assert len(deserialized.links[0].node.links[0].node.links[0].node.links[0].node.links) == 1
        assert deserialized.links[0].node.links[0].node.links[0].node.links[0].node.links[0].node.comment == "E250"
        assert len(deserialized.links[0].node.links[0].node.links[0].node.links[0].node.links[0].node.links) == 1
        assert deserialized.links[0].node.links[0].node.links[0].node.links[0].node.links[0].node.links[0].node.text.get(Language.ENGLISH, Gender.MALE) == "R225"
        assert len(deserialized.links[0].node.links[0].node.links[0].node.links[0].node.links[0].node.links[0].node.links) == 1
        assert deserialized.links[0].node.links[0].node.links[0].node.links[0].node.links[0].node.links[0].node.links[0].node.text.get(Language.ENGLISH, Gender.MALE) == "R224"


class TestDLGAnimationSerialization(unittest.TestCase):
    def test_dlg_animation_serialization_basic(self):
        animation = DLGAnimation()
        animation.animation_id = 1200
        animation.participant = "Player"

        serialized = animation.to_dict()
        deserialized = DLGAnimation.from_dict(serialized)

        assert animation.animation_id == deserialized.animation_id
        assert animation.participant == deserialized.participant

    def test_dlg_animation_serialization_default(self):
        animation = DLGAnimation()

        serialized = animation.to_dict()
        deserialized = DLGAnimation.from_dict(serialized)

        assert animation.animation_id == deserialized.animation_id
        assert animation.participant == deserialized.participant

    def test_dlg_animation_serialization_with_custom_values(self):
        animation = DLGAnimation()
        animation.animation_id = 2400
        animation.participant = "NPC"

        serialized = animation.to_dict()
        deserialized = DLGAnimation.from_dict(serialized)

        assert animation.animation_id == deserialized.animation_id
        assert animation.participant == deserialized.participant


class TestDLGStuntSerialization(unittest.TestCase):
    def test_dlg_stunt_serialization_basic(self):
        stunt = DLGStunt()
        stunt.participant = "Player"
        stunt.stunt_model = ResRef("model")

        serialized = stunt.to_dict()
        deserialized = DLGStunt.from_dict(serialized)

        assert stunt.participant == deserialized.participant
        assert stunt.stunt_model == deserialized.stunt_model

    def test_dlg_stunt_serialization_default(self):
        stunt = DLGStunt()

        serialized = stunt.to_dict()
        deserialized = DLGStunt.from_dict(serialized)

        assert stunt.participant == deserialized.participant
        assert stunt.stunt_model == deserialized.stunt_model

    def test_dlg_stunt_serialization_with_custom_values(self):
        stunt = DLGStunt()
        stunt.participant = "NPC"
        stunt.stunt_model = ResRef("npc_model")

        serialized = stunt.to_dict()
        deserialized = DLGStunt.from_dict(serialized)

        assert stunt.participant == deserialized.participant
        assert stunt.stunt_model == deserialized.stunt_model


class TestDLGLinkSerialization(unittest.TestCase):
    def test_dlg_link_serialization_basic(self):
        link = DLGLink(DLGEntry())
        link.list_index = 3

        serialized = link.to_dict()
        deserialized = DLGLink.from_dict(serialized)

        assert link.list_index == deserialized.list_index

    def test_dlg_link_serialization_with_node(self):
        entry = DLGEntry()
        entry.comment = "Linked entry"
        link = DLGLink(entry)

        serialized = link.to_dict()
        deserialized = DLGLink.from_dict(serialized)

        assert link.node.comment == deserialized.node.comment

    def test_dlg_link_serialization_all_attributes(self):
        reply = DLGReply()
        reply.text = "Linked reply"
        link = DLGLink(reply, 5)
        link.node = reply

        serialized = link.to_dict()
        deserialized = DLGLink.from_dict(serialized)

        assert link.list_index == deserialized.list_index
        assert link.node.text == deserialized.node.text

    def test_dlg_link_with_nested_entries_and_replies(self):
        entry1 = DLGEntry(comment="E248")
        entry2 = DLGEntry(comment="E221")

        reply1 = DLGReply(text=LocalizedString.from_english("R222"))
        reply2 = DLGReply(text=LocalizedString.from_english("R223"))
        reply3 = DLGReply(text=LocalizedString.from_english("R249"))

        link1 = DLGLink(node=reply1)
        link2 = DLGLink(node=entry2)
        link3 = DLGLink(node=reply2)
        link4 = DLGLink(node=reply3)

        entry1.links.append(link1)
        reply1.links.extend([link2, link3])
        entry2.links.append(link4)  # Reuse R249

        serialized = link1.to_dict()
        deserialized = DLGLink.from_dict(serialized)

        assert link1.node.text == deserialized.node.text
        assert len(deserialized.node.links) == 2
        assert deserialized.node.links[0].node.comment == "E221"
        assert deserialized.node.links[1].node.text.get(Language.ENGLISH, Gender.MALE) == "R223"
        assert len(deserialized.node.links[1].node.links) == 1
        assert deserialized.node.links[1].node.links[0].node.comment == "E248"

    def test_dlg_link_with_circular_references(self):
        entry1 = DLGEntry(comment="E248")
        entry2 = DLGEntry(comment="E221")

        reply1 = DLGReply(text=LocalizedString.from_english("R222"))
        reply2 = DLGReply(text=LocalizedString.from_english("R249"))

        link1 = DLGLink(node=reply1)
        link2 = DLGLink(node=entry2)
        link3 = DLGLink(node=reply2)
        link4 = DLGLink(node=entry1)  # Circular reference

        entry1.links.append(link1)
        reply1.links.append(link2)
        entry2.links.append(link3)  # Reuse R249
        reply2.links.append(link4)

        serialized = link1.to_dict()
        deserialized = DLGLink.from_dict(serialized)

        assert link1.node.text == deserialized.node.text
        assert len(deserialized.node.links) == 1
        assert deserialized.node.links[0].node.comment == "E221"
        assert len(deserialized.node.links[0].node.links) == 1
        assert deserialized.node.links[0].node.links[0].node.text.get(Language.ENGLISH, Gender.MALE) == "R249"
        assert len(deserialized.node.links[0].node.links[0].node.links) == 1
        assert deserialized.node.links[0].node.links[0].node.links[0].node.comment == "E248"

    def test_dlg_link_with_multiple_levels(self):
        entry1 = DLGEntry(comment="E248")
        entry2 = DLGEntry(comment="E221")
        entry3 = DLGEntry(comment="E250")

        reply1 = DLGReply(text=LocalizedString.from_english("R222"))
        reply2 = DLGReply(text=LocalizedString.from_english("R223"))
        reply3 = DLGReply(text=LocalizedString.from_english("R249"))
        reply4 = DLGReply(text=LocalizedString.from_english("R225"))
        reply5 = DLGReply(text=LocalizedString.from_english("R224"))

        link1 = DLGLink(node=reply1)
        link2 = DLGLink(node=entry2)
        link3 = DLGLink(node=reply2)
        link4 = DLGLink(node=reply3)
        link5 = DLGLink(node=entry3)
        link6 = DLGLink(node=reply4)
        link7 = DLGLink(node=reply5)

        entry1.links.append(link1)
        reply1.links.append(link3)
        reply1.links.append(link2)
        entry2.links.append(link4)  # Reuse R249
        reply3.links.append(link5)
        entry3.links.append(link6)
        reply4.links.append(link7)

        serialized = link1.to_dict()
        deserialized = DLGLink.from_dict(serialized)

        assert link1.node.text == deserialized.node.text
        assert len(deserialized.node.links) == 2
        assert deserialized.node.links[0].node.text.get(Language.ENGLISH, Gender.MALE) == "R223"
        assert deserialized.node.links[1].node.comment == "E221"
        assert len(deserialized.node.links[1].node.links) == 1
        assert deserialized.node.links[1].node.links[0].node.text.get(Language.ENGLISH, Gender.MALE) == "R249"
        assert len(deserialized.node.links[1].node.links[0].node.links) == 1
        assert deserialized.node.links[1].node.links[0].node.links[0].node.comment == "E250"
        assert len(deserialized.node.links[1].node.links[0].node.links[0].node.links) == 1
        assert deserialized.node.links[1].node.links[0].node.links[0].node.links[0].node.text.get(Language.ENGLISH, Gender.MALE) == "R225"
        assert len(deserialized.node.links[1].node.links[0].node.links[0].node.links[0].node.links) == 1
        assert deserialized.node.links[1].node.links[0].node.links[0].node.links[0].node.links[0].node.text.get(Language.ENGLISH, Gender.MALE) == "R224"



class TestDLGAnimationSerialization(unittest.TestCase):
    def test_dlg_animation_serialization_basic(self):
        animation = DLGAnimation()
        animation.animation_id = 1200
        animation.participant = "Player"

        serialized = animation.to_dict()
        deserialized = DLGAnimation.from_dict(serialized)

        assert animation.animation_id == deserialized.animation_id
        assert animation.participant == deserialized.participant

    def test_dlg_animation_serialization_default(self):
        animation = DLGAnimation()

        serialized = animation.to_dict()
        deserialized = DLGAnimation.from_dict(serialized)

        assert animation.animation_id == deserialized.animation_id
        assert animation.participant == deserialized.participant

    def test_dlg_animation_serialization_with_custom_values(self):
        animation = DLGAnimation()
        animation.animation_id = 2400
        animation.participant = "NPC"

        serialized = animation.to_dict()
        deserialized = DLGAnimation.from_dict(serialized)

        assert animation.animation_id == deserialized.animation_id
        assert animation.participant == deserialized.participant


class TestDLGStuntSerialization(unittest.TestCase):
    def test_dlg_stunt_serialization_basic(self):
        stunt = DLGStunt()
        stunt.participant = "Player"
        stunt.stunt_model = ResRef("model")

        serialized = stunt.to_dict()
        deserialized = DLGStunt.from_dict(serialized)

        assert stunt.participant == deserialized.participant
        assert stunt.stunt_model == deserialized.stunt_model

    def test_dlg_stunt_serialization_default(self):
        stunt = DLGStunt()

        serialized = stunt.to_dict()
        deserialized = DLGStunt.from_dict(serialized)

        assert stunt.participant == deserialized.participant
        assert stunt.stunt_model == deserialized.stunt_model

    def test_dlg_stunt_serialization_with_custom_values(self):
        stunt = DLGStunt()
        stunt.participant = "NPC"
        stunt.stunt_model = ResRef("npc_model")

        serialized = stunt.to_dict()
        deserialized = DLGStunt.from_dict(serialized)

        assert stunt.participant == deserialized.participant
        assert stunt.stunt_model == deserialized.stunt_model


if __name__ == "__main__":
    unittest.main()
