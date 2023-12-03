import os
import pathlib
import sys
import unittest
from unittest import TestCase

THIS_SCRIPT_PATH = pathlib.Path(__file__)
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[3].resolve()
UTILITY_PATH = THIS_SCRIPT_PATH.parents[5].joinpath("Utility", "src").resolve()
if PYKOTOR_PATH.exists():
    working_dir = str(PYKOTOR_PATH)
    if working_dir in sys.path:
        sys.path.remove(working_dir)
        os.chdir(PYKOTOR_PATH.parent)
    sys.path.insert(0, working_dir)
if UTILITY_PATH.exists():
    working_dir = str(UTILITY_PATH)
    if working_dir in sys.path:
        sys.path.remove(working_dir)
    sys.path.insert(0, working_dir)

from pykotor.common.misc import Game
from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.dlg import construct_dlg, dismantle_dlg

TEST_FILE = "src/tests/files/test.dlg"


class TestDLG(TestCase):
    def test_io(self):
        gff = read_gff(TEST_FILE)
        dlg = construct_dlg(gff)
        self.validate_io(dlg)

        gff = dismantle_dlg(dlg, Game.K2)
        dlg = construct_dlg(gff)
        self.validate_io(dlg)

    def validate_io(self, dlg):
        all_entries = dlg.all_entries()
        all_replies = dlg.all_replies()

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
