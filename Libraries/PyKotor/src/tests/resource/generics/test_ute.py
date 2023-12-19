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
from pykotor.resource.generics.ute import UTE, construct_ute, dismantle_ute

TEST_FILE = "src/tests/files/test.ute"


class TestUTE(TestCase):
    def setUp(self):
        self.log_messages = [os.linesep]

    def log_func(self, message=""):
        self.log_messages.append(message)

    def test_k2_reconstruct(self) -> None:
        gff = read_gff(TEST_FILE)
        reconstructed_gff = dismantle_ute(construct_ute(gff), Game.K2)
        result = gff.compare(reconstructed_gff, self.log_func)
        output = os.linesep.join(self.log_messages)
        if not result:
            expected_output = r"""
GFFStruct: number of fields have changed at 'GFFRoot\CreatureList\0': '4' --> '5'
Extra 'Int32' field found at 'GFFRoot\CreatureList\0\GuaranteedCount': '0'
""".replace("\r\n", "\n")
            self.assertEqual(output.strip().replace("\r\n", "\n"), expected_output.strip(), "Comparison output does not match expected output")
        else:
            self.assertTrue(result)

    def test_io_construct(self):
        gff = read_gff(TEST_FILE)
        ute = construct_ute(gff)
        self.validate_io(ute)

    def test_io_reconstruct(self):
        gff = read_gff(TEST_FILE)
        gff = dismantle_ute(construct_ute(gff))
        ute = construct_ute(gff)
        self.validate_io(ute)

    def validate_io(self, ute: UTE):
        self.assertEqual("G_KATAARNGROUP01", ute.tag)
        self.assertEqual(31918, ute.name.stringref)
        self.assertEqual("g_kataarngroup01", ute.resref)
        self.assertEqual(1, ute.active)
        self.assertEqual(1, ute.unused_difficulty)
        self.assertEqual(2, ute.difficulty_id)
        self.assertEqual(1, ute.faction_id)
        self.assertEqual(6, ute.max_creatures)
        self.assertEqual(1, ute.player_only)
        self.assertEqual(3, ute.rec_creatures)
        self.assertEqual(1, ute.reset)
        self.assertEqual(60, ute.reset_time)
        self.assertEqual(1, ute.respawns)
        self.assertEqual(1, ute.single_shot)
        self.assertEqual("onentered", ute.on_entered)
        self.assertEqual("onexit", ute.on_exit)
        self.assertEqual("onexhausted", ute.on_exhausted)
        self.assertEqual("onheartbeat", ute.on_heartbeat)
        self.assertEqual("onuserdefined", ute.on_user_defined)
        self.assertEqual(7, ute.palette_id)
        self.assertEqual("Kashyyyk", ute.comment)

        self.assertEqual(2, len(ute.creatures))
        self.assertEqual(74, ute.creatures[1].appearance_id)
        self.assertEqual(8.0, ute.creatures[1].challenge_rating)
        self.assertEqual("g_kataarn02", ute.creatures[1].resref)
        self.assertEqual(1, ute.creatures[1].guaranteed_count)
        self.assertTrue(ute.creatures[1].single_spawn)


if __name__ == "__main__":
    unittest.main()
