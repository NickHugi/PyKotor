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
from pykotor.resource.generics.utp import UTP, construct_utp, dismantle_utp

TEST_FILE = "src/tests/files/test.utp"


class Test(TestCase):
    def setUp(self):
        self.log_messages = [os.linesep]

    def log_func(self, message=""):
        self.log_messages.append(message)

    def test_gff_reconstruct(self) -> None:
        gff = read_gff(TEST_FILE)
        reconstructed_gff = dismantle_utp(construct_utp(gff))
        self.assertTrue(gff.compare(reconstructed_gff, self.log_func), os.linesep.join(self.log_messages))

    def test_io_construct(self):
        gff = read_gff(TEST_FILE)
        utp = construct_utp(gff)
        self.validate_io(utp)

    def test_io_reconstruct(self):
        gff = read_gff(TEST_FILE)
        gff = dismantle_utp(construct_utp(gff))
        utp = construct_utp(gff)
        self.validate_io(utp)

    def validate_io(self, utp: UTP):
        self.assertEqual("SecLoc", utp.tag)
        self.assertEqual(74450, utp.name.stringref)
        self.assertEqual("lockerlg002", utp.resref)
        self.assertEqual(1, utp.auto_remove_key)
        self.assertEqual(13, utp.lock_dc)
        self.assertEqual("conversation", utp.conversation)
        self.assertEqual(1, utp.faction_id)
        self.assertEqual(1, utp.plot)
        self.assertEqual(1, utp.not_blastable)
        self.assertEqual(1, utp.min1_hp)
        self.assertEqual(1, utp.key_required)
        self.assertEqual(0, utp.lockable)
        self.assertEqual(1, utp.locked)
        self.assertEqual(28, utp.unlock_dc)
        self.assertEqual(1, utp.unlock_diff)
        self.assertEqual(1, utp.unlock_diff_mod)
        self.assertEqual("somekey", utp.key_name)
        self.assertEqual(2, utp.animation_state)
        self.assertEqual(67, utp.appearance_id)
        self.assertEqual(1, utp.min1_hp)
        self.assertEqual(15, utp.current_hp)
        self.assertEqual(5, utp.hardness)
        self.assertEqual(16, utp.fortitude)
        self.assertEqual("lockerlg002", utp.resref)
        self.assertEqual("onclosed", utp.on_closed)
        self.assertEqual("ondamaged", utp.on_damaged)
        self.assertEqual("ondeath", utp.on_death)
        self.assertEqual("onheartbeat", utp.on_heartbeat)
        self.assertEqual("onlock", utp.on_lock)
        self.assertEqual("onmeleeattacked", utp.on_melee_attack)
        self.assertEqual("onopen", utp.on_open)
        self.assertEqual("onspellcastat", utp.on_force_power)
        self.assertEqual("onunlock", utp.on_unlock)
        self.assertEqual("onuserdefined", utp.on_user_defined)
        self.assertEqual(1, utp.has_inventory)
        self.assertEqual(1, utp.party_interact)
        self.assertEqual(1, utp.static)
        self.assertEqual(1, utp.useable)
        self.assertEqual("onenddialogue", utp.on_end_dialog)
        self.assertEqual("oninvdisturbed", utp.on_inventory)
        self.assertEqual("onused", utp.on_used)
        self.assertEqual("onfailtoopen", utp.on_open_failed)
        self.assertEqual("Large standup locker", utp.comment)
        self.assertEqual(-1, utp.description.stringref)
        self.assertEqual(1, utp.interruptable)
        self.assertEqual(0, utp.portrait_id)
        self.assertEqual(1, utp.trap_detectable)
        self.assertEqual(0, utp.trap_detect_dc)
        self.assertEqual(1, utp.trap_disarmable)
        self.assertEqual(15, utp.trap_disarm_dc)
        self.assertEqual(0, utp.trap_flag)
        self.assertEqual(1, utp.trap_one_shot)
        self.assertEqual(0, utp.trap_type)
        self.assertEqual(0, utp.will)
        self.assertEqual("ondisarm", utp.on_disarm)
        self.assertEqual("", utp.on_trap_triggered)
        self.assertEqual(0, utp.bodybag_id)
        self.assertEqual(0, utp.trap_type)
        self.assertEqual(6, utp.palette_id)

        self.assertEqual(2, len(utp.inventory))
        self.assertFalse(utp.inventory[0].droppable)
        self.assertTrue(utp.inventory[1].droppable)
        self.assertEqual("g_w_iongren02", utp.inventory[1].resref)


if __name__ == "__main__":
    unittest.main()
