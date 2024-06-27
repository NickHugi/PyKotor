from __future__ import annotations

import os
import pathlib
import sys
import unittest

from unittest import TestCase


try:
    from qtpy.QtTest import QTest
    from qtpy.QtWidgets import QApplication
except (ImportError, ModuleNotFoundError):
    QTest, QApplication = None, None  # type: ignore[misc, assignment]

TESTS_FILES_PATH = next(f for f in pathlib.Path(__file__).parents if f.name == "tests") / "files"

if getattr(sys, "frozen", False) is False:

    def add_sys_path(p):
        working_dir = str(p)
        if working_dir not in sys.path:
            sys.path.append(working_dir)

    pykotor_path = pathlib.Path(__file__).absolute().parents[6] / "Libraries" / "PyKotor" / "src" / "pykotor"
    if pykotor_path.exists():
        add_sys_path(pykotor_path.parent)
    gl_path = pathlib.Path(__file__).absolute().parents[6] / "Libraries" / "PyKotorGL" / "src" / "pykotor"
    if gl_path.exists():
        add_sys_path(gl_path.parent)
    utility_path = pathlib.Path(__file__).absolute().parents[6] / "Libraries" / "Utility" / "src" / "utility"
    if utility_path.exists():
        add_sys_path(utility_path.parent)
    toolset_path = pathlib.Path(__file__).absolute().parents[3] / "toolset"
    if toolset_path.exists():
        add_sys_path(toolset_path.parent)


K1_PATH = os.environ.get("K1_PATH")
K2_PATH = os.environ.get("K2_PATH")

from pykotor.resource.generics.utc import UTC, construct_utc
from pykotor.common.stream import BinaryReader
from pykotor.extract.installation import Installation
from pykotor.resource.formats.gff.gff_auto import read_gff
from pykotor.resource.type import ResourceType


@unittest.skipIf(
    not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
    "K2_PATH environment variable is not set or not found on disk.",
)
@unittest.skipIf(
    QTest is None or not QApplication,
    "qtpy is required, please run pip install -r requirements.txt before running this test.",
)
class UTCEditorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        # Make sure to configure this environment path before testing!
        from toolset.data.installation import HTInstallation

        cls.INSTALLATION = HTInstallation(K2_PATH, "", tsl=True)

    def setUp(self):
        from toolset.gui.editors.utc import UTCEditor

        self.app = QApplication([])
        self.editor = UTCEditor(None, self.INSTALLATION)
        self.log_messages: list[str] = [os.linesep]

    def tearDown(self):
        self.app.deleteLater()

    def log_func(self, *args):
        self.log_messages.append("\t".join(args))

    def test_save_and_load(self):  # sourcery skip: class-extract-method
        filepath = TESTS_FILES_PATH / "../toolset_tests/files/p_hk47.utc"

        data = BinaryReader.load_file(filepath)
        old = read_gff(data)
        self.editor.load(filepath, "p_hk47", ResourceType.UTC, data)

        data, _ = self.editor.build()
        new = read_gff(data)

        diff = old.compare(new, self.log_func)
        self.assertTrue(diff, os.linesep.join(self.log_messages))

    def test_save_and_load_validate(self):
        filepath = TESTS_FILES_PATH / "test.utc"

        data = BinaryReader.load_file(filepath)
        old = read_gff(data)
        self.editor.load(filepath, "p_hk47", ResourceType.UTC, data)

        data, _ = self.editor.build()
        new = read_gff(data)

        diff = old.compare(new, self.log_func)
        self.assertTrue(diff, os.linesep.join(self.log_messages))
        utc = construct_utc(new)
        self.validate_io(utc)

    @unittest.skipIf(
        not K1_PATH or not pathlib.Path(K1_PATH).joinpath("chitin.key").exists(),
        "K1_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k1_installation(self):
        self.installation = Installation(K1_PATH)  # type: ignore[arg-type]
        for utc_resource in (resource for resource in self.installation if resource.restype() is ResourceType.UTC):
            if utc_resource.resname().lower() == "g_assassindrd02":
                continue  # don't care about Repos_Posy/x
            old = read_gff(utc_resource.data())
            self.editor.load(utc_resource.filepath(), utc_resource.resname(), utc_resource.restype(), utc_resource.data())

            data, _ = self.editor.build()
            new = read_gff(data)

            diff = old.compare(new, self.log_func, ignore_default_changes=True)
            self.assertTrue(
                diff,
                f"'{utc_resource.identifier()}' at '{utc_resource.filepath()}' failed to diff{os.linesep*2}{os.linesep.join(self.log_messages)}",
            )

    @unittest.skipIf(
        not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
        "K2_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k2_installation(self):
        self.installation = Installation(K2_PATH)  # type: ignore[arg-type]
        for utc_resource in (resource for resource in self.installation if resource.restype() is ResourceType.UTC):
            old = read_gff(utc_resource.data())
            self.editor.load(utc_resource.filepath(), utc_resource.resname(), utc_resource.restype(), utc_resource.data())

            data, _ = self.editor.build()
            new = read_gff(data)

            diff = old.compare(new, self.log_func, ignore_default_changes=True)
            self.assertTrue(diff, os.linesep.join(self.log_messages))

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
