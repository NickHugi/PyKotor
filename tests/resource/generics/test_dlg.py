from __future__ import annotations

import os
import pathlib
import sys
import unittest

from unittest import TestCase

THIS_SCRIPT_PATH = pathlib.Path(__file__).resolve()
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[3].resolve()
UTILITY_PATH = THIS_SCRIPT_PATH.parents[5].joinpath("Utility", "src").resolve()


def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from typing import TYPE_CHECKING

from pykotor.common.misc import Game
from pykotor.extract.installation import Installation
from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.dlg import construct_dlg, dismantle_dlg
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.gff import GFF
    from pykotor.resource.generics.dlg import DLG, DLGEntry, DLGReply

TEST_FILE = "tests/files/test.dlg"
TEST_K1_FILE = "tests/files/test_k1.dlg"
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
        if not result:
            expected_output = r"""
GFFStruct: number of fields have changed at 'GFFRoot\ReplyList\0': '14' --> '15'
Extra 'Int32' field found at 'GFFRoot\ReplyList\0\PlotIndex': '-1'
GFFStruct: number of fields have changed at 'GFFRoot\ReplyList\1': '14' --> '15'
Extra 'Int32' field found at 'GFFRoot\ReplyList\1\PlotIndex': '-1'
GFFStruct: number of fields have changed at 'GFFRoot\ReplyList\2': '14' --> '15'
Extra 'Int32' field found at 'GFFRoot\ReplyList\2\PlotIndex': '-1'
GFFStruct: number of fields have changed at 'GFFRoot\ReplyList\3': '14' --> '15'
Extra 'Int32' field found at 'GFFRoot\ReplyList\3\PlotIndex': '-1'
GFFStruct: number of fields have changed at 'GFFRoot\ReplyList\4': '14' --> '15'
Extra 'Int32' field found at 'GFFRoot\ReplyList\4\PlotIndex': '-1'
"""
            self.assertEqual(output.strip().replace("\r\n", "\n"), expected_output.strip(), "Comparison output does not match expected output")
        else:
            self.assertTrue(result)

    def test_k1_reconstruct_from_reconstruct(self):
        gff: GFF = read_gff(TEST_K1_FILE)
        reconstructed_gff: GFF = dismantle_dlg(construct_dlg(gff), Game.K1)
        re_reconstructed_gff: GFF = dismantle_dlg(construct_dlg(reconstructed_gff), Game.K1)
        result = reconstructed_gff.compare(re_reconstructed_gff, self.log_func)
        output = os.linesep.join(self.log_messages)
        self.assertTrue(result, output)

    def test_k2_reconstruct(self):
        gff: GFF = read_gff(TEST_FILE)
        reconstructed_gff: GFF = dismantle_dlg(construct_dlg(gff), Game.K2)
        self.assertTrue(gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True), os.linesep.join(self.log_messages))

    def test_k2_reconstruct_from_reconstruct(self):
        gff: GFF = read_gff(TEST_FILE)
        reconstructed_gff: GFF = dismantle_dlg(construct_dlg(gff), Game.K2)
        re_reconstructed_gff: GFF = dismantle_dlg(construct_dlg(reconstructed_gff), Game.K2)
        result = reconstructed_gff.compare(re_reconstructed_gff, self.log_func)
        output = os.linesep.join(self.log_messages)
        self.assertTrue(result, output)

    @unittest.skipIf(
        not K1_PATH or not pathlib.Path(K1_PATH).joinpath("chitin.key").exists(),
        "K1_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k1_installation(self):
        self.installation = Installation(K1_PATH)  # type: ignore[arg-type]
        for dlg_resource in (resource for resource in self.installation if resource.restype() == ResourceType.DLG):
            gff: GFF = read_gff(dlg_resource.data())
            reconstructed_gff: GFF = dismantle_dlg(construct_dlg(gff), Game.K1)
            self.assertTrue(gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True), os.linesep.join(self.log_messages))

    @unittest.skipIf(
        not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
        "K2_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k2_installation(self):
        self.installation = Installation(K2_PATH)  # type: ignore[arg-type]
        for dlg_resource in (resource for resource in self.installation if resource.restype() == ResourceType.DLG):
            gff: GFF = read_gff(dlg_resource.data())
            reconstructed_gff: GFF = dismantle_dlg(construct_dlg(gff))
            self.assertTrue(gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True), os.linesep.join(self.log_messages))

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

        self.assertEqual(3, len(all_entries))
        self.assertEqual(2, len(all_replies))
        self.assertEqual(2, len(dlg.starters))
        self.assertEqual(2, len(dlg.stunts))

        self.assertIn(entry0, [link.node for link in dlg.starters])
        self.assertIn(entry2, [link.node for link in dlg.starters])

        self.assertEqual(2, len(entry0.links))
        self.assertIn(reply0, [link.node for link in entry0.links])
        self.assertIn(reply1, [link.node for link in entry0.links])

        self.assertEqual(1, len(reply0.links))
        self.assertIn(entry0, [link.node for link in reply0.links])

        self.assertEqual(1, len(reply1.links))
        self.assertIn(entry1, [link.node for link in reply1.links])

        self.assertEqual(0, len(entry2.links))

        self.assertEqual(13, dlg.delay_entry)
        self.assertEqual(14, dlg.delay_reply)
        self.assertEqual(1337, dlg.word_count)
        self.assertEqual("abort", dlg.on_abort)
        self.assertEqual("end", dlg.on_end)
        self.assertEqual(1, dlg.skippable)
        self.assertEqual("track", dlg.ambient_track)
        self.assertEqual(123, dlg.animated_cut)
        self.assertEqual("camm", dlg.camera_model)
        self.assertEqual(1, dlg.computer_type.value)
        self.assertEqual(1, dlg.conversation_type.value)
        self.assertEqual(1, dlg.old_hit_check)
        self.assertEqual(1, dlg.unequip_hands)
        self.assertEqual(1, dlg.unequip_items)
        self.assertEqual("echo", dlg.vo_id)
        self.assertEqual(123, dlg.alien_race_owner)
        self.assertEqual(12, dlg.post_proc_owner)
        self.assertEqual(3, dlg.record_no_vo)

        self.assertEqual("yoohoo", entry0.listener)
        self.assertEqual(-1, entry0.text.stringref)
        self.assertEqual("gand", entry0.vo_resref)
        self.assertEqual("num1", entry0.script1)
        self.assertEqual(-1, entry0.delay)
        self.assertEqual("commentto", entry0.comment)
        self.assertEqual("gonk", entry0.sound)
        self.assertEqual("quest", entry0.quest)
        self.assertEqual(-1, entry0.plot_index)
        self.assertEqual(1.0, entry0.plot_xp_percentage)
        self.assertEqual(1, entry0.wait_flags)
        self.assertEqual(14, entry0.camera_angle)
        self.assertEqual(1, entry0.fade_type)
        self.assertEqual(1, entry0.sound_exists)
        self.assertEqual(1, entry0.alien_race_node)
        self.assertEqual(1, entry0.vo_text_changed)
        self.assertEqual(4, entry0.emotion_id)
        self.assertEqual(2, entry0.facial_id)
        self.assertEqual(1, entry0.node_id)
        self.assertEqual(1, entry0.unskippable)
        self.assertEqual(3, entry0.post_proc_node)
        self.assertEqual(1, entry0.record_vo)
        self.assertEqual("num2", entry0.script2)
        self.assertEqual(1, entry0.vo_text_changed)
        self.assertEqual(1, entry0.record_no_vo_override)
        self.assertEqual(32, entry0.camera_id)
        self.assertEqual("bark", entry0.speaker)
        self.assertEqual(-1, entry0.camera_effect)
        self.assertEqual(1, entry0.record_no_vo_override)

        self.assertEqual("bbb", dlg.stunts[1].participant)
        self.assertEqual("m01aa_c04_char01", dlg.stunts[1].stunt_model)


if __name__ == "__main__":
    unittest.main()
