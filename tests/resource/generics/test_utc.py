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

TEST_FILE = "tests/files/test.utc"
K1_PATH = os.environ.get("K1_PATH")
K2_PATH = os.environ.get("K2_PATH")


class TestUTC(TestCase):
    def setUp(self):
        self.log_messages = [os.linesep]

    def log_func(self, *msgs):
        self.log_messages.append("\t".join(msgs))

    @unittest.skipIf(
        not K1_PATH or not pathlib.Path(K1_PATH).joinpath("chitin.key").exists(),
        "K1_PATH environment variable is not set or not found on disk.",
    )
    @unittest.skip("This test is known to fail - fixme")  # FIXME:
    def test_gff_reconstruct_from_k1_installation(self):
        self.installation = Installation(K1_PATH)  # type: ignore[arg-type]
        for utc_resource in (resource for resource in self.installation if resource.restype() is ResourceType.UTC):
            gff: GFF = read_gff(utc_resource.data())
            reconstructed_gff: GFF = dismantle_utc(construct_utc(gff), Game.K1)
            self.assertTrue(gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True), os.linesep.join(self.log_messages))

    @unittest.skipIf(
        not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
        "K2_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k2_installation(self):
        self.installation = Installation(K2_PATH)  # type: ignore[arg-type]
        for utc_resource in (resource for resource in self.installation if resource.restype() is ResourceType.UTC):
            gff: GFF = read_gff(utc_resource.data())
            reconstructed_gff: GFF = dismantle_utc(construct_utc(gff))
            self.assertTrue(gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True), os.linesep.join(self.log_messages))

    def test_gff_reconstruct(self):
        gff = read_gff(TEST_FILE)
        reconstructed_gff = dismantle_utc(construct_utc(gff), Game.K2)
        result = gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True)
        output = os.linesep.join(self.log_messages)
        if not result:
            expected_output = r"""
GFFStruct: number of fields have changed at 'GFFRoot': '74' --> '75'
Field 'LocalizedString' is different at 'GFFRoot\Description': 123 --> -1
"""
            self.assertEqual(output.strip().replace("\r\n", "\n"), expected_output.strip(), "Comparison output does not match expected output")
        else:
            self.assertTrue(result)

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
        self.assertEqual(636, utc.appearance_id)
        self.assertEqual(1, utc.body_variation)
        self.assertEqual(120.0, utc.blindspot)
        self.assertEqual(10, utc.charisma)
        self.assertEqual(1.0, utc.challenge_rating)
        self.assertEqual("comment", utc.comment)
        self.assertEqual(10, utc.constitution)
        self.assertEqual("coorta", utc.conversation)
        self.assertEqual(1, utc.fp)
        self.assertEqual(8, utc.current_hp)
        self.assertEqual(10, utc.dexterity)
        self.assertTrue(utc.disarmable)
        self.assertEqual(5, utc.faction_id)
        self.assertEqual(76046, utc.first_name.stringref)
        self.assertEqual(1, utc.max_fp)
        self.assertEqual(2, utc.gender_id)
        self.assertEqual(50, utc.alignment)
        self.assertEqual(8, utc.hp)
        self.assertTrue(utc.hologram)
        self.assertTrue(utc.ignore_cre_path)
        self.assertEqual(10, utc.intelligence)
        self.assertTrue(utc.interruptable)
        self.assertTrue(utc.is_pc)
        self.assertEqual(123, utc.last_name.stringref)
        self.assertEqual(8, utc.max_hp)
        self.assertTrue(utc.min1_hp)
        self.assertEqual(3, utc.multiplier_set)
        self.assertEqual(1, utc.natural_ac)
        self.assertTrue(utc.no_perm_death)
        self.assertTrue(utc.not_reorienting)
        self.assertTrue(utc.party_interact)
        self.assertEqual(11, utc.perception_id)
        self.assertTrue(utc.plot)
        self.assertEqual(1, utc.portrait_id)
        self.assertEqual(6, utc.race_id)
        self.assertEqual("k_def_attacked01", utc.on_attacked)
        self.assertEqual("k_def_damage01", utc.on_damaged)
        self.assertEqual("k_def_death01", utc.on_death)
        self.assertEqual("k_def_dialogue01", utc.on_dialog)
        self.assertEqual("k_def_disturb01", utc.on_disturbed)
        self.assertEqual("k_def_endconv", utc.on_end_dialog)
        self.assertEqual("k_def_combend01", utc.on_end_round)
        self.assertEqual("k_def_heartbt01", utc.on_heartbeat)
        self.assertEqual("k_def_blocked01", utc.on_blocked)
        self.assertEqual("k_def_percept01", utc.on_notice)
        self.assertEqual("k_def_spawn01", utc.on_spawn)
        self.assertEqual("k_def_spellat01", utc.on_spell)
        self.assertEqual("k_def_userdef01", utc.on_user_defined)
        self.assertEqual(46, utc.soundset_id)
        self.assertEqual(10, utc.strength)
        self.assertEqual(1, utc.subrace_id)
        self.assertEqual("Coorta", utc.tag)
        self.assertEqual("n_minecoorta", utc.resref)
        self.assertEqual(1, utc.texture_variation)
        self.assertEqual(7, utc.walkrate_id)
        self.assertEqual(10, utc.wisdom)
        self.assertEqual(1, utc.fortitude_bonus)
        self.assertEqual(1, utc.reflex_bonus)
        self.assertEqual(1, utc.willpower_bonus)

        self.assertEqual(2, len(utc.classes))
        self.assertEqual(1, utc.classes[1].class_id)
        self.assertEqual(3, utc.classes[1].class_level)
        self.assertEqual(2, len(utc.classes[1].powers))
        self.assertEqual(9, utc.classes[1].powers[0])

        self.assertEqual(2, len(utc.equipment.items()))
        self.assertEqual("mineruniform", utc.equipment[EquipmentSlot.ARMOR].resref)
        self.assertTrue(utc.equipment[EquipmentSlot.ARMOR].droppable)
        self.assertEqual("g_i_crhide008", utc.equipment[EquipmentSlot.HIDE].resref)
        self.assertFalse(utc.equipment[EquipmentSlot.HIDE].droppable)

        self.assertEqual(2, len(utc.feats))
        self.assertEqual(94, utc.feats[1])

        self.assertEqual(4, len(utc.inventory))
        self.assertTrue(utc.inventory[0].droppable)
        self.assertFalse(utc.inventory[1].droppable)
        self.assertEqual("g_w_thermldet01", utc.inventory[1].resref)

        self.assertEqual(1, utc.computer_use)
        self.assertEqual(2, utc.demolitions)
        self.assertEqual(3, utc.stealth)
        self.assertEqual(4, utc.awareness)
        self.assertEqual(5, utc.persuade)
        self.assertEqual(6, utc.repair)
        self.assertEqual(7, utc.security)
        self.assertEqual(8, utc.treat_injury)


if __name__ == "__main__":
    unittest.main()
