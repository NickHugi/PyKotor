from __future__ import annotations

import os
import pathlib
import sys
import unittest
from unittest import TestCase

from pykotor.resource.type import ResourceType

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
from pykotor.resource.generics.utp import construct_utp, dismantle_utp

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFF
    from pykotor.resource.generics.utp import UTP

TEST_FILE = "tests/files/test.utp"

K1_PATH = os.environ.get("K1_PATH")
K2_PATH = os.environ.get("K2_PATH")


class Test(TestCase):
    def setUp(self):
        self.log_messages = [os.linesep]

    def log_func(self, *msgs):
        self.log_messages.append("\t".join(msgs))

    @unittest.skipIf(
        not K1_PATH or not pathlib.Path(K1_PATH).joinpath("chitin.key").exists(),
        "K1_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k1_installation(self):
        self.installation = Installation(K1_PATH)  # type: ignore[arg-type]
        for are_resource in (resource for resource in self.installation if resource.restype() is ResourceType.UTP):
            gff: GFF = read_gff(are_resource.data())
            reconstructed_gff: GFF = dismantle_utp(construct_utp(gff), Game.K1)
            assert gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True), os.linesep.join(self.log_messages)

    @unittest.skipIf(
        not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
        "K2_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k2_installation(self):
        self.installation = Installation(K2_PATH)  # type: ignore[arg-type]
        for are_resource in (resource for resource in self.installation if resource.restype() is ResourceType.UTP):
            gff: GFF = read_gff(are_resource.data())
            reconstructed_gff: GFF = dismantle_utp(construct_utp(gff))
            assert gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True), os.linesep.join(self.log_messages)

    def test_gff_reconstruct(self):
        gff = read_gff(TEST_FILE)
        reconstructed_gff = dismantle_utp(construct_utp(gff))
        assert gff.compare(reconstructed_gff, self.log_func), os.linesep.join(self.log_messages)

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
        assert utp.tag == "SecLoc"
        assert utp.name.stringref == 74450
        assert utp.resref == "lockerlg002"
        assert utp.auto_remove_key == 1
        assert utp.lock_dc == 13
        assert utp.conversation == "conversation"
        assert utp.faction_id == 1
        assert utp.plot == 1
        assert utp.not_blastable == 1
        assert utp.min1_hp == 1
        assert utp.key_required == 1
        assert utp.lockable == 0
        assert utp.locked == 1
        assert utp.unlock_dc == 28
        assert utp.unlock_diff == 1
        assert utp.unlock_diff_mod == 1
        assert utp.key_name == "somekey"
        assert utp.animation_state == 2
        assert utp.appearance_id == 67
        assert utp.min1_hp == 1
        assert utp.current_hp == 15
        assert utp.hardness == 5
        assert utp.fortitude == 16
        assert utp.resref == "lockerlg002"
        assert utp.on_closed == "onclosed"
        assert utp.on_damaged == "ondamaged"
        assert utp.on_death == "ondeath"
        assert utp.on_heartbeat == "onheartbeat"
        assert utp.on_lock == "onlock"
        assert utp.on_melee_attack == "onmeleeattacked"
        assert utp.on_open == "onopen"
        assert utp.on_force_power == "onspellcastat"
        assert utp.on_unlock == "onunlock"
        assert utp.on_user_defined == "onuserdefined"
        assert utp.has_inventory == 1
        assert utp.party_interact == 1
        assert utp.static == 1
        assert utp.useable == 1
        assert utp.on_end_dialog == "onenddialogue"
        assert utp.on_inventory == "oninvdisturbed"
        assert utp.on_used == "onused"
        assert utp.on_open_failed == "onfailtoopen"
        assert utp.comment == "Large standup locker"
        assert utp.description.stringref == -1
        assert utp.interruptable == 1
        assert utp.portrait_id == 0
        assert utp.trap_detectable == 1
        assert utp.trap_detect_dc == 0
        assert utp.trap_disarmable == 1
        assert utp.trap_disarm_dc == 15
        assert utp.trap_flag == 0
        assert utp.trap_one_shot == 1
        assert utp.trap_type == 0
        assert utp.will == 0
        assert utp.on_disarm == "ondisarm"
        assert utp.on_trap_triggered == ""
        assert utp.bodybag_id == 0
        assert utp.trap_type == 0
        assert utp.palette_id == 6

        assert len(utp.inventory) == 2
        assert not utp.inventory[0].droppable
        assert utp.inventory[1].droppable
        assert utp.inventory[1].resref == "g_w_iongren02"


if __name__ == "__main__":
    unittest.main()
