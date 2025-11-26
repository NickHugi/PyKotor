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

from pykotor.common.misc import EquipmentSlot, Game
from pykotor.extract.installation import Installation
from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.utc import construct_utc, dismantle_utc
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFF
    from pykotor.resource.generics.utc import UTC

TEST_FILE = "tests/test_pykotor/test_files/test.utc"
K1_PATH = os.environ.get("K1_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor")
K2_PATH = os.environ.get("K2_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Knights of the Old Republic II")


class TestUTC(TestCase):
    def setUp(self):
        self.log_messages = [os.linesep]

    def log_func(self, *msgs):
        self.log_messages.append("\t".join(msgs))

    def test_io_construct(self):
        gff = read_gff(TEST_FILE)
        utc = construct_utc(gff)
        self.validate_io(utc)

    def test_io_reconstruct(self):
        gff = read_gff(TEST_FILE)
        gff = dismantle_utc(construct_utc(gff))
        utc = construct_utc(gff)
        self.validate_io(utc)

    def validate_io(self, utc: UTC):
        assert utc.appearance_id == 636
        assert utc.body_variation == 1
        assert utc.blindspot == 120.0
        assert utc.charisma == 10
        assert utc.challenge_rating == 1.0
        assert utc.comment == "comment"
        assert utc.constitution == 10
        assert utc.conversation == "coorta"
        assert utc.fp == 1
        assert utc.current_hp == 8
        assert utc.dexterity == 10
        assert utc.disarmable
        assert utc.faction_id == 5
        assert utc.first_name.stringref == 76046
        assert utc.max_fp == 1
        assert utc.gender_id == 2
        assert utc.alignment == 50
        assert utc.hp == 8
        assert utc.hologram
        assert utc.ignore_cre_path
        assert utc.intelligence == 10
        assert utc.interruptable
        assert utc.is_pc
        assert utc.last_name.stringref == 123
        assert utc.max_hp == 8
        assert utc.min1_hp
        assert utc.multiplier_set == 3
        assert utc.natural_ac == 1
        assert utc.no_perm_death
        assert utc.not_reorienting
        assert utc.party_interact
        assert utc.perception_id == 11
        assert utc.plot
        assert utc.portrait_id == 1
        assert utc.race_id == 6
        assert utc.on_attacked == "k_def_attacked01"
        assert utc.on_damaged == "k_def_damage01"
        assert utc.on_death == "k_def_death01"
        assert utc.on_dialog == "k_def_dialogue01"
        assert utc.on_disturbed == "k_def_disturb01"
        assert utc.on_end_dialog == "k_def_endconv"
        assert utc.on_end_round == "k_def_combend01"
        assert utc.on_heartbeat == "k_def_heartbt01"
        assert utc.on_blocked == "k_def_blocked01"
        assert utc.on_notice == "k_def_percept01"
        assert utc.on_spawn == "k_def_spawn01"
        assert utc.on_spell == "k_def_spellat01"
        assert utc.on_user_defined == "k_def_userdef01"
        assert utc.soundset_id == 46
        assert utc.strength == 10
        assert utc.subrace_id == 1
        assert utc.tag == "Coorta"
        assert utc.resref == "n_minecoorta"
        assert utc.texture_variation == 1
        assert utc.walkrate_id == 7
        assert utc.wisdom == 10
        assert utc.fortitude_bonus == 1
        assert utc.reflex_bonus == 1
        assert utc.willpower_bonus == 1

        assert len(utc.classes) == 2
        assert utc.classes[1].class_id == 1
        assert utc.classes[1].class_level == 3
        assert len(utc.classes[1].powers) == 2
        assert utc.classes[1].powers[0] == 9

        assert len(utc.equipment.items()) == 2
        assert utc.equipment[EquipmentSlot.ARMOR].resref == "mineruniform"
        assert utc.equipment[EquipmentSlot.ARMOR].droppable
        assert utc.equipment[EquipmentSlot.HIDE].resref == "g_i_crhide008"
        assert not utc.equipment[EquipmentSlot.HIDE].droppable

        assert len(utc.feats) == 2
        assert utc.feats[1] == 94

        assert len(utc.inventory) == 4
        assert utc.inventory[0].droppable
        assert not utc.inventory[1].droppable
        assert utc.inventory[1].resref == "g_w_thermldet01"

        assert utc.computer_use == 1
        assert utc.demolitions == 2
        assert utc.stealth == 3
        assert utc.awareness == 4
        assert utc.persuade == 5
        assert utc.repair == 6
        assert utc.security == 7
        assert utc.treat_injury == 8


if __name__ == "__main__":
    unittest.main()
