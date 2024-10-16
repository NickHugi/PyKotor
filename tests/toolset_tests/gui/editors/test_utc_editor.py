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

if (
    __name__ == "__main__"
    and getattr(sys, "frozen", False) is False
):
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

from pykotor.common.stream import BinaryReader
from pykotor.extract.installation import Installation
from pykotor.resource.formats.gff.gff_auto import read_gff
from pykotor.resource.generics.utc import UTC, construct_utc
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

        data = filepath.read_bytes()
        old = read_gff(data)
        self.editor.load(filepath, "p_hk47", ResourceType.UTC, data)

        data, _ = self.editor.build()
        new = read_gff(data)

        diff = old.compare(new, self.log_func)
        assert diff, os.linesep.join(self.log_messages)

    def test_save_and_load_validate(self):
        filepath = TESTS_FILES_PATH / "test.utc"

        data = filepath.read_bytes()
        old = read_gff(data)
        self.editor.load(filepath, "p_hk47", ResourceType.UTC, data)

        data, _ = self.editor.build()
        new = read_gff(data)

        diff = old.compare(new, self.log_func)
        assert diff, os.linesep.join(self.log_messages)
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
            assert diff, f"'{utc_resource.identifier()}' at '{utc_resource.filepath()}' failed to diff{os.linesep * 2}{os.linesep.join(self.log_messages)}"

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
            assert diff, os.linesep.join(self.log_messages)

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
