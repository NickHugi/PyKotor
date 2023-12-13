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

from pykotor.resource.formats.gff import GFF
from pykotor.common.misc import Game
from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.dlg import DLG, DLGAnimation, DLGEntry, DLGReply, DLGStunt, construct_dlg, dismantle_dlg

TEST_FILE = "src/tests/files/test.dlg"
TEST_K1_FILE = "src/tests/files/test_k1.dlg"


class TestDLG(TestCase):
    def setUp(self):
        self.log_messages: list[str] = [os.linesep]

    def log_func(self, *args):
        self.log_messages.extend(args)

    def test_k1_reconstruct(self) -> None:
        gff: GFF = read_gff(TEST_K1_FILE)
        reconstructed_gff: GFF = dismantle_dlg(construct_dlg(gff), Game.K1)
        result = gff.compare(reconstructed_gff, self.log_func)
        output = os.linesep.join(self.log_messages)
        self.assertTrue(result, output)

    def test_k1_reconstruct_from_reconstruct(self) -> None:
        gff: GFF = read_gff(TEST_K1_FILE)
        reconstructed_gff: GFF = dismantle_dlg(construct_dlg(gff), Game.K1)
        re_reconstructed_gff: GFF = dismantle_dlg(construct_dlg(reconstructed_gff), Game.K1)
        result = reconstructed_gff.compare(re_reconstructed_gff, self.log_func)
        output = os.linesep.join(self.log_messages)
        self.assertTrue(result, output)

    def test_k2_reconstruct(self) -> None:
        gff: GFF = read_gff(TEST_FILE)
        reconstructed_gff: GFF = dismantle_dlg(construct_dlg(gff), Game.K2)
        self.assertTrue(gff.compare(reconstructed_gff, self.log_func), os.linesep.join(self.log_messages))

    def test_k2_reconstruct_from_reconstruct(self) -> None:
        gff: GFF = read_gff(TEST_FILE)
        reconstructed_gff: GFF = dismantle_dlg(construct_dlg(gff), Game.K2)
        re_reconstructed_gff: GFF = dismantle_dlg(construct_dlg(reconstructed_gff), Game.K2)
        result = reconstructed_gff.compare(re_reconstructed_gff, self.log_func)
        output = os.linesep.join(self.log_messages)
        self.assertTrue(result, output)

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
        self.assertEqual(2, len(dlg.StartingList))
        self.assertEqual(2, len(dlg.StuntList))

        self.assertIn(entry0, [link._node for link in dlg.StartingList])
        self.assertIn(entry2, [link._node for link in dlg.StartingList])

        self.assertEqual(2, len(entry0._links))
        self.assertIn(reply0, [link._node for link in entry0._links])
        self.assertIn(reply1, [link._node for link in entry0._links])

        self.assertEqual(1, len(reply0._links))
        self.assertIn(entry0, [link._node for link in reply0._links])

        self.assertEqual(1, len(reply1._links))
        self.assertIn(entry1, [link._node for link in reply1._links])

        self.assertEqual(0, len(entry2._links))

        self.assertEqual(13, dlg.DelayEntry)
        self.assertEqual(14, dlg.DelayReply)
        self.assertEqual(1337, dlg.NumWords)
        self.assertEqual("abort", dlg.EndConverAbort)
        self.assertEqual("end", dlg.EndConversation)
        self.assertEqual(1, dlg.Skippable)
        self.assertEqual("track", dlg.AmbientTrack)
        self.assertEqual(123, dlg.AnimatedCut)
        self.assertEqual("camm", dlg.CameraModel)
        self.assertEqual(1, dlg.ComputerType.value)
        self.assertEqual(1, dlg.ConversationType.value)
        self.assertEqual(1, dlg.OldHitCheck)
        self.assertEqual(1, dlg.UnequipHItem)
        self.assertEqual(1, dlg.UnequipItems)
        self.assertEqual("echo", dlg.VO_ID)
        self.assertEqual(123, dlg.AlienRaceOwner)
        self.assertEqual(12, dlg.PostProcOwner)
        self.assertEqual(3, dlg.RecordNoVO)

        self.assertEqual("yoohoo", entry0.Listener)
        self.assertEqual(-1, entry0.Text.stringref)
        self.assertEqual("gand", entry0.VO_ResRef)
        self.assertEqual("num1", entry0.Script)
        self.assertEqual(-1, entry0.Delay)
        self.assertEqual("commentto", entry0.Comment)
        self.assertEqual("gonk", entry0.Sound)
        self.assertEqual("quest", entry0.Quest)
        self.assertEqual(-1, entry0.PlotIndex)
        self.assertEqual(1.0, entry0.PlotXPPercentage)
        self.assertEqual(1, entry0.WaitFlags)
        self.assertEqual(14, entry0.CameraAngle)
        self.assertEqual(1, entry0.FadeType)
        self.assertEqual(1, entry0.SoundExists)
        self.assertEqual(1, entry0.AlienRaceNode)
        self.assertEqual(1, entry0.VOTextChanged)
        self.assertEqual(4, entry0.Emotion)
        self.assertEqual(2, entry0.FacialAnim)
        self.assertEqual(1, entry0.NodeID)
        self.assertEqual(1, entry0.NodeUnskippable)
        self.assertEqual(3, entry0.PostProcNode)
        self.assertEqual(1, entry0.RecordVO)
        self.assertEqual("num2", entry0.Script2)
        self.assertEqual(1, entry0.VOTextChanged)
        self.assertEqual(1, entry0.RecordNoOverri)
        self.assertEqual(32, entry0.CameraID)
        self.assertEqual("bark", entry0.Speaker)
        self.assertEqual(-1, entry0.CameraAnimation)
        self.assertEqual(1, entry0.RecordNoOverri)

        stunt = dlg.StuntList[1]
        assert isinstance(stunt, DLGStunt)
        self.assertEqual("bbb", stunt.Participant)
        self.assertEqual("m01aa_c04_char01", stunt.stunt_model)


if __name__ == "__main__":
    unittest.main()
