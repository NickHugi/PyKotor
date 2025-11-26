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
from pykotor.resource.generics.utd import construct_utd, dismantle_utd
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFF
    from pykotor.resource.generics.utd import UTD

TEST_FILE = "tests/test_pykotor/test_files/test.utd"
K1_SAME_TEST_FILE = "tests/test_pykotor/test_files/k1_utd_same_test.utd"
K1_PATH = os.environ.get("K1_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor")
K2_PATH = os.environ.get("K2_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Knights of the Old Republic II")


class TestUTD(TestCase):
    def setUp(self):
        self.log_messages = [os.linesep]

    def log_func(self, *msgs):
        self.log_messages.append("\t".join(msgs))

    @unittest.skip("This test is known to fail - fixme")  # FIXME:
    def test_gff_reconstruct(self):
        gff = read_gff(K1_SAME_TEST_FILE)
        reconstructed_gff = dismantle_utd(construct_utd(gff))
        assert gff.compare(reconstructed_gff, self.log_func), os.linesep.join(self.log_messages)

    def test_io_construct(self):
        gff = read_gff(TEST_FILE)
        utd = construct_utd(gff)
        self.validate_io(utd)

    def test_io_reconstruct(self):
        gff = read_gff(TEST_FILE)
        gff = dismantle_utd(construct_utd(gff))
        utd = construct_utd(gff)
        self.validate_io(utd)

    def validate_io(self, utd: UTD):
        assert utd.tag == "TelosDoor13"
        assert utd.name.stringref == 123731
        assert utd.description.stringref == -1
        assert utd.resref == "door_tel014"
        assert utd.auto_remove_key == 1
        assert utd.lock_dc == 0
        assert utd.conversation == "convoresref"
        assert utd.interruptable == 1
        assert utd.faction_id == 1
        assert utd.plot == 1
        assert utd.not_blastable == 1
        assert utd.min1_hp == 1
        assert utd.key_required == 1
        assert utd.lockable == 1
        assert utd.locked == 1
        assert utd.unlock_dc == 28
        assert utd.unlock_diff_mod == 1
        assert utd.unlock_diff_mod == 1
        assert utd.portrait_id == 0
        assert utd.trap_detectable == 1
        assert utd.trap_detect_dc == 0
        assert utd.trap_disarmable == 1
        assert utd.trap_disarm_dc == 28
        assert utd.trap_flag == 0
        assert utd.trap_one_shot == 1
        assert utd.trap_type == 2
        assert utd.key_name == "keyname"
        assert utd.animation_state == 1
        assert utd.unused_appearance == 1
        assert utd.min1_hp == 1
        assert utd.current_hp == 60
        assert utd.hardness == 5
        assert utd.fortitude == 28
        assert utd.resref == "door_tel014"
        assert utd.willpower == 0
        assert utd.on_closed == "onclosed"
        assert utd.on_damaged == "ondamaged"
        assert utd.on_death == "ondeath"
        assert utd.on_disarm == "ondisarm"
        assert utd.on_heartbeat == "onheartbeat"
        assert utd.on_lock == "onlock"
        assert utd.on_melee == "onmeleeattacked"
        assert utd.on_open == "onopen"
        assert utd.on_power == "onspellcastat"
        assert utd.on_trap_triggered == "ontraptriggered"
        assert utd.on_unlock == "onunlock"
        assert utd.on_user_defined == "onuserdefined"
        assert utd.loadscreen_id == 0
        assert utd.appearance_id == 110
        assert utd.static == 1
        assert utd.open_state == 1
        assert utd.on_click == "onclick"
        assert utd.on_open_failed == "onfailtoopen"
        assert utd.palette_id == 1
        assert utd.comment == "abcdefg"


if __name__ == "__main__":
    unittest.main()
