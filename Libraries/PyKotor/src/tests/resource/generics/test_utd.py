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

from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.utd import construct_utd, dismantle_utd

TEST_FILE = "src/tests/files/test.utd"
K1_SAME_TEST_FILE = "src/tests/files/k1_utd_same_test.utd"


class TestUTD(TestCase):
    def setUp(self):
        self.log_messages = [os.linesep]

    def log_func(self, message=""):
        self.log_messages.append(message)

    def test_gff_reconstruct(self) -> None:
        gff = read_gff(K1_SAME_TEST_FILE)
        reconstructed_gff = dismantle_utd(construct_utd(gff))
        self.assertTrue(gff.compare(reconstructed_gff, self.log_func), os.linesep.join(self.log_messages))

    def test_io_construct(self):
        gff = read_gff(TEST_FILE)
        utd = construct_utd(gff)
        self.validate_io(utd)

    def test_io_reconstruct(self):
        gff = read_gff(TEST_FILE)
        gff = dismantle_utd(construct_utd(gff))
        utd = construct_utd(gff)
        self.validate_io(utd)

    def validate_io(self, utd):
        self.assertEqual("TelosDoor13", utd.tag)
        self.assertEqual(123731, utd.name.stringref)
        self.assertEqual(-1, utd.description.stringref)
        self.assertEqual("door_tel014", utd.resref)
        self.assertEqual(1, utd.auto_remove_key)
        self.assertEqual(0, utd.lock_dc)
        self.assertEqual("convoresref", utd.conversation)
        self.assertEqual(1, utd.interruptable)
        self.assertEqual(1, utd.faction_id)
        self.assertEqual(1, utd.plot)
        self.assertEqual(1, utd.not_blastable)
        self.assertEqual(1, utd.min1_hp)
        self.assertEqual(1, utd.key_required)
        self.assertEqual(1, utd.lockable)
        self.assertEqual(1, utd.locked)
        self.assertEqual(28, utd.unlock_dc)
        self.assertEqual(1, utd.unlock_diff_mod)
        self.assertEqual(1, utd.unlock_diff_mod)
        self.assertEqual(0, utd.portrait_id)
        self.assertEqual(1, utd.trap_detectable)
        self.assertEqual(0, utd.trap_detect_dc)
        self.assertEqual(1, utd.trap_disarmable)
        self.assertEqual(28, utd.trap_disarm_dc)
        self.assertEqual(0, utd.trap_flag)
        self.assertEqual(1, utd.trap_one_shot)
        self.assertEqual(2, utd.trap_type)
        self.assertEqual("keyname", utd.key_name)
        self.assertEqual(1, utd.animation_state)
        self.assertEqual(1, utd.unused_appearance)
        self.assertEqual(1, utd.min1_hp)
        self.assertEqual(60, utd.current_hp)
        self.assertEqual(5, utd.hardness)
        self.assertEqual(28, utd.fortitude)
        self.assertEqual("door_tel014", utd.resref)
        self.assertEqual(0, utd.willpower)
        self.assertEqual("onclosed", utd.on_closed)
        self.assertEqual("ondamaged", utd.on_damaged)
        self.assertEqual("ondeath", utd.on_death)
        self.assertEqual("ondisarm", utd.on_disarm)
        self.assertEqual("onheartbeat", utd.on_heartbeat)
        self.assertEqual("onlock", utd.on_lock)
        self.assertEqual("onmeleeattacked", utd.on_melee)
        self.assertEqual("onopen", utd.on_open)
        self.assertEqual("onspellcastat", utd.on_power)
        self.assertEqual("ontraptriggered", utd.on_trap_triggered)
        self.assertEqual("onunlock", utd.on_unlock)
        self.assertEqual("onuserdefined", utd.on_user_defined)
        self.assertEqual(0, utd.loadscreen_id)
        self.assertEqual(110, utd.appearance_id)
        self.assertEqual(1, utd.static)
        self.assertEqual(1, utd.open_state)
        self.assertEqual("onclick", utd.on_click)
        self.assertEqual("onfailtoopen", utd.on_open_failed)
        self.assertEqual(1, utd.palette_id)
        self.assertEqual("abcdefg", utd.comment)


if __name__ == "__main__":
    unittest.main()
