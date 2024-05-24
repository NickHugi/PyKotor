from __future__ import annotations

import os
import pathlib
import shutil
import sys
import tempfile
import unittest

from configparser import ConfigParser
from typing import TYPE_CHECKING, cast

THIS_SCRIPT_PATH = pathlib.Path(__file__).resolve()
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[2].joinpath("Libraries", "PyKotor", "src")
UTILITY_PATH = THIS_SCRIPT_PATH.parents[2].joinpath("Libraries", "Utility", "src")


def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from pykotor.common.geometry import Vector3, Vector4
from pykotor.common.language import Gender, Language
from pykotor.common.misc import ResRef
from pykotor.resource.formats.gff.gff_data import GFFFieldType, GFFStruct
from pykotor.resource.formats.ssf import SSFSound
from pykotor.resource.formats.tlk import TLK, write_tlk
from pykotor.resource.type import ResourceType
from pykotor.tslpatcher.config import PatcherConfig
from pykotor.tslpatcher.memory import NoTokenUsage, TokenUsage2DA, TokenUsageTLK
from pykotor.tslpatcher.mods.gff import (
    AddFieldGFF,
    AddStructToListGFF,
    FieldValue2DAMemory,
    FieldValueConstant,
    FieldValueTLKMemory,
    LocalizedStringDelta,
    ModifyFieldGFF,
    ModifyGFF,
)
from pykotor.tslpatcher.mods.twoda import (
    AddRow2DA,
    CopyRow2DA,
    RowValue2DAMemory,
    RowValueConstant,
    RowValueHigh,
    RowValueRowCell,
    RowValueRowIndex,
    RowValueRowLabel,
    RowValueTLKMemory,
    TargetType,
)
from pykotor.tslpatcher.reader import ConfigReader
from utility.system.path import Path

if TYPE_CHECKING:
    from pykotor.tslpatcher.mods.ssf import ModifySSF
    from pykotor.tslpatcher.mods.tlk import ModifyTLK
    from pykotor.tslpatcher.mods.twoda import (
        AddColumn2DA,
        ChangeRow2DA,
    )

K1_PATH: str = os.environ.get("K1_PATH", r"C:\Program Files (x86)\Steam\steamapps\common\swkotor")


class TestConfigReader(unittest.TestCase):
    def setUp(self):
        self.config = PatcherConfig()
        self.ini = ConfigParser(
            delimiters=("="),
            allow_no_value=True,
            strict=False,
            interpolation=None,
        )
        # use case-sensitive keys
        self.ini.optionxform = lambda optionstr: optionstr  # type: ignore[method-assign]

        self.test_tlk_data: TLK = self.create_test_tlk(
            {
                0: {"text": "Entry 0", "voiceover": "vo_0"},
                1: {"text": "Entry 1", "voiceover": "vo_1"},
                2: {"text": "Entry 2", "voiceover": "vo_2"},
                3: {"text": "Entry 3", "voiceover": "vo_3"},
                4: {"text": "Entry 4", "voiceover": "vo_4"},
                5: {"text": "Entry 5", "voiceover": "vo_5"},
                6: {"text": "Entry 6", "voiceover": "vo_6"},
                7: {"text": "Entry 7", "voiceover": "vo_7"},
                8: {"text": "Entry 8", "voiceover": "vo_8"},
                9: {"text": "Entry 9", "voiceover": "vo_9"},
                10: {"text": "Entry 10", "voiceover": "vo_10"},
            }
        )
        self.modified_tlk_data: TLK = self.create_test_tlk(
            {
                0: {"text": "Modified 0", "voiceover": "vo_mod_0"},
                1: {"text": "Modified 1", "voiceover": "vo_mod_1"},
                2: {"text": "Modified 2", "voiceover": "vo_mod_2"},
                3: {"text": "Modified 3", "voiceover": "vo_mod_3"},
                4: {"text": "Modified 4", "voiceover": "vo_mod_4"},
                5: {"text": "Modified 5", "voiceover": "vo_mod_5"},
                6: {"text": "Modified 6", "voiceover": "vo_mod_6"},
                7: {"text": "Modified 7", "voiceover": "vo_mod_7"},
                8: {"text": "Modified 8", "voiceover": "vo_mod_8"},
                9: {"text": "Modified 9", "voiceover": "vo_mod_9"},
                10: {"text": "Modified 10", "voiceover": "vo_mod_10"},
            }
        )
        with tempfile.TemporaryDirectory() as tmpdirname:
            self.mod_path = Path(tmpdirname) / "tslpatchdata"
        self.mod_path.mkdir(exist_ok=True, parents=True)
        shutil.copy(Path("tests/files/complex.tlk").resolve(), self.mod_path / "complex.tlk")
        shutil.copy(Path("tests/files/append.tlk").resolve(), self.mod_path / "append.tlk")

        # write it to a real file
        write_tlk(
            self.test_tlk_data,
            str(Path(self.mod_path, "tlk_test_file.tlk")),
            ResourceType.TLK,
        )
        write_tlk(
            self.modified_tlk_data,
            str(Path(self.mod_path, "tlk_modifications_file.tlk")),
            ResourceType.TLK,
        )

        # Load the INI file and the TLK file
        self.config_reader = ConfigReader(self.ini, self.mod_path)  # type: ignore

    def cleanUp(self):
        self.mod_path.unlink()

    def create_test_tlk(self, data: dict[int, dict[str, str]]) -> TLK:
        tlk = TLK()
        for v in data.values():
            tlk.add(text=v["text"], sound_resref=v["voiceover"])
        return tlk

    def test_tlk_appendfile_functionality(self):
        ini_text = """
            [TLKList]
            AppendFile4=tlk_modifications_file.tlk

            [tlk_modifications_file.tlk]
            0=4
            1=5
            2=6
        """
        self.ini.read_string(ini_text)
        self.config_reader.load(self.config)
        for modifier in self.config.patches_tlk.modifiers:
            modifier.load()

        self.assertEqual(len(self.config.patches_tlk.modifiers), 3)
        modifiers_dict = {mod.token_id: {"text": mod.text, "voiceover": mod.sound, "replace": mod.is_replacement} for mod in self.config.patches_tlk.modifiers}
        self.maxDiff = None
        self.assertDictEqual(
            modifiers_dict,
            {
                0: {"text": "Modified 4", "voiceover": ResRef("vo_mod_4"), "replace": False},
                1: {"text": "Modified 5", "voiceover": ResRef("vo_mod_5"), "replace": False},
                2: {"text": "Modified 6", "voiceover": ResRef("vo_mod_6"), "replace": False},
            },
        )

    def test_tlk_strref_default_functionality(self):
        ini_text = """
            [TLKList]
            StrRef7=0
            StrRef8=1
            StrRef9=2
        """

        write_tlk(
            self.modified_tlk_data,
            str(Path(self.mod_path, "append.tlk")),
            ResourceType.TLK,
        )

        self.ini.read_string(ini_text)
        self.config_reader.load(self.config)
        for modifier in self.config.patches_tlk.modifiers:
            modifier.load()

        self.assertEqual(len(self.config.patches_tlk.modifiers), 3)
        modifiers_dict = {mod.token_id: {"text": mod.text, "voiceover": mod.sound, "replace": mod.is_replacement} for mod in self.config.patches_tlk.modifiers}
        self.assertDictEqual(
            modifiers_dict,
            {
                7: {"text": "Modified 0", "voiceover": ResRef("vo_mod_0"), "replace": False},
                8: {"text": "Modified 1", "voiceover": ResRef("vo_mod_1"), "replace": False},
                9: {"text": "Modified 2", "voiceover": ResRef("vo_mod_2"), "replace": False},
            },
        )

    def test_tlk_complex_changes(self):
        # sourcery skip: extract-duplicate-method, remove-dict-keys, use-dict-items
        ini_text2 = """
        [TLKList]
        ReplaceFile10=complex.tlk
        StrRef0=0
        StrRef1=1
        StrRef2=2
        StrRef3=3
        StrRef4=4
        StrRef5=5
        StrRef6=6
        StrRef7=7
        StrRef8=8
        StrRef9=9
        StrRef10=10
        StrRef11=11
        StrRef12=12
        StrRef13=13

        [complex.tlk]
        123716=0
        123717=1
        123718=2
        123720=3
        123722=4
        123724=5
        123726=6
        123728=7
        123730=8
        124112=9
        125863=10
        50302=11
        """
        self.ini.read_string(ini_text2)
        self.config_reader.load(self.config)

        modifiers2: list[ModifyTLK] = self.config.patches_tlk.modifiers.copy()
        for modifier in modifiers2:
            modifier.load()
        self.assertEqual(len(self.config.patches_tlk.modifiers), 26)
        modifiers_dict2: dict[int, dict[str, str | ResRef | bool]] = {
            mod.token_id: {"text": mod.text, "voiceover": mod.sound, "is_replacement": mod.is_replacement}
            for mod in modifiers2
        }
        for k in modifiers_dict2.copy():
            modifiers_dict2[k].pop("is_replacement")

        self.maxDiff = None
        self.assertDictEqual(
            modifiers_dict2,
            {
                0: {"text": "Yavin", "voiceover": ResRef.from_blank()},
                1: {
                    "text": "Climate: Artificially Controled\n" "Terrain: Space Station\n" "Docking: Orbital Docking\n" "Native Species: Unknown",
                    "voiceover": ResRef.from_blank(),
                },
                2: {"text": "Tatooine", "voiceover": ResRef.from_blank()},
                3: {
                    "text": "Climate: Arid\nTerrain: Desert\nDocking: Anchorhead Spaceport\nNative Species: Unknown",
                    "voiceover": ResRef.from_blank(),
                },
                4: {"text": "Manaan", "voiceover": ResRef.from_blank()},
                5: {
                    "text": "Climate: Temperate\n" "Terrain: Ocean\n" "Docking: Ahto City Docking Bay\n" "Native Species: Selkath",
                    "voiceover": ResRef.from_blank(),
                },
                6: {"text": "Kashyyyk", "voiceover": ResRef.from_blank()},
                7: {
                    "text": "Climate: Temperate\nTerrain: Forest\nDocking: Czerka Landing Pad\nNative Species: Wookies",
                    "voiceover": ResRef.from_blank(),
                },
                8: {"text": "", "voiceover": ResRef.from_blank()},
                9: {"text": "", "voiceover": ResRef.from_blank()},
                10: {"text": "Sleheyron", "voiceover": ResRef.from_blank()},
                11: {
                    "text": "Climate: Unknown\nTerrain: Cityscape\nDocking: Unknown\nNative Species: Unknown",
                    "voiceover": ResRef.from_blank(),
                },
                12: {"text": "Coruscant", "voiceover": ResRef.from_blank()},
                13: {
                    "text": "Climate: Unknown\nTerrain: Unknown\nDocking: Unknown\nNative Species: Unknown",
                    "voiceover": ResRef.from_blank(),
                },
                50302: {
                    "text": "Opo Chano, Czerka's contracted droid technician, can't give "
                    "you his droid credentials unless you help relieve his 2,500 "
                    "credit gambling debt to the Exchange. Without them, you "
                    "can't take B-4D4.",
                    "voiceover": ResRef.from_blank(),
                },
                123716: {
                    "text": "Climate: None\nTerrain: Asteroid\nDocking: Peragus Mining Station\nNative Species: None",
                    "voiceover": ResRef.from_blank(),
                },
                123717: {"text": "Lehon", "voiceover": ResRef.from_blank()},
                123718: {
                    "text": "Climate: Tropical\nTerrain: Islands\nDocking: Beach Landing\nNative Species: Rakata",
                    "voiceover": ResRef.from_blank(),
                },
                123720: {
                    "text": "Climate: Temperate\n" "Terrain: Decaying urban zones\n" "Docking: Refugee Landing Pad\n" "Native Species: None",
                    "voiceover": ResRef.from_blank(),
                },
                123722: {
                    "text": "Climate: Tropical\nTerrain: Jungle\nDocking: Jungle Clearing\nNative Species: None",
                    "voiceover": ResRef.from_blank(),
                },
                123724: {
                    "text": "Climate: Temperate\nTerrain: Forest\nDocking: Iziz Spaceport\nNative Species: None",
                    "voiceover": ResRef.from_blank(),
                },
                123726: {
                    "text": "Climate: Temperate\n" "Terrain: Grasslands\n" "Docking: Khoonda Plains Settlement\n" "Native Species: None",
                    "voiceover": ResRef.from_blank(),
                },
                123728: {
                    "text": "Climate: Tectonic-Generated Storms\n" "Terrain: Shattered Planetoid\n" "Docking: No Docking Facilities Present\n" "Native Species: None",
                    "voiceover": ResRef.from_blank(),
                },
                123730: {
                    "text": "Climate: Arid\nTerrain: Volcanic\nDocking: Dreshae Settlement\nNative Species: Unknown",
                    "voiceover": ResRef.from_blank(),
                },
                124112: {
                    "text": "Climate: Artificially Maintained \n" "Terrain: Droid Cityscape\n" "Docking: Landing Arm\n" "Native Species: Unknown",
                    "voiceover": ResRef.from_blank(),
                },
                125863: {
                    "text": "Climate: Artificially Maintained\n" "Terrain: Space Station\n" "Docking: Landing Zone\n" "Native Species: None",
                    "voiceover": ResRef.from_blank(),
                },
            },
        )

    def test_tlk_replacefile_functionality(self):
        ini_text = """
            [TLKList]
            Replacenothingafterreplaceischecked=tlk_modifications_file.tlk

            [tlk_modifications_file.tlk]
            0=2
            1=3
            2=4
            3=5
            4=6
        """
        self.ini.read_string(ini_text)
        self.config_reader.load(self.config)
        for modifier in self.config.patches_tlk.modifiers:
            modifier.load()

        self.assertEqual(len(self.config.patches_tlk.modifiers), 5)
        modifiers_dict = {mod.token_id: {"text": mod.text, "voiceover": mod.sound} for mod in self.config.patches_tlk.modifiers}
        self.assertDictEqual(
            modifiers_dict,
            {
                0: {"text": "Modified 2", "voiceover": ResRef("vo_mod_2")},
                1: {"text": "Modified 3", "voiceover": ResRef("vo_mod_3")},
                2: {"text": "Modified 4", "voiceover": ResRef("vo_mod_4")},
                3: {"text": "Modified 5", "voiceover": ResRef("vo_mod_5")},
                4: {"text": "Modified 6", "voiceover": ResRef("vo_mod_6")},
            },
        )

    # region 2DA: Change Row
    def test_2da_changerow_identifier(self):
        """Test that identifier is being loaded correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            ChangeRow0=change_row_0
            ChangeRow1=change_row_1

            [change_row_0]
            RowIndex=1
            [change_row_1]
            RowLabel=1
            """
        )
        # noinspection PyTypeChecker
        mod_0: ChangeRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore
        self.assertEqual("change_row_0", mod_0.identifier)

        # noinspection PyTypeChecker
        mod_0: ChangeRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore
        self.assertEqual("change_row_1", mod_0.identifier)

    def test_2da_changerow_targets(self):
        """Test that target values (line to modify) are loading correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            ChangeRow0=change_row_0
            ChangeRow1=change_row_1
            ChangeRow2=change_row_2

            [change_row_0]
            RowIndex=1
            [change_row_1]
            RowLabel=2
            [change_row_2]
            LabelIndex=3
            """
        )
        # noinspection PyTypeChecker
        mod_2da_0: ChangeRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore
        self.assertEqual(TargetType.ROW_INDEX, mod_2da_0.target.target_type)
        self.assertEqual(1, mod_2da_0.target.value)

        # noinspection PyTypeChecker
        mod_2da_1: ChangeRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore
        self.assertEqual(TargetType.ROW_LABEL, mod_2da_1.target.target_type)
        self.assertEqual("2", mod_2da_1.target.value)

        # noinspection PyTypeChecker
        mod_2da_2: ChangeRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore
        self.assertEqual(TargetType.LABEL_COLUMN, mod_2da_2.target.target_type)
        self.assertEqual("3", mod_2da_2.target.value)

    def test_2da_changerow_store2da(self):
        """Test that 2DAMEMORY values are set to be stored correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            ChangeRow0=change_row_0

            [change_row_0]
            RowIndex=0
            2DAMEMORY0=RowIndex
            2DAMEMORY1=RowLabel
            2DAMEMORY2=label
            """
        )
        # noinspection PyTypeChecker
        mod_2da_0: ChangeRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore

        # noinspection PyTypeChecker
        store_2da_0a: RowValueRowIndex = mod_2da_0.store_2da[0]  # type: ignore
        self.assertIsInstance(store_2da_0a, RowValueRowIndex)

        # noinspection PyTypeChecker
        store_2da_0b: RowValueRowLabel = mod_2da_0.store_2da[1]  # type: ignore
        self.assertIsInstance(store_2da_0b, RowValueRowLabel)

        # noinspection PyTypeChecker
        store_2da_0c: RowValueRowCell = mod_2da_0.store_2da[2]  # type: ignore
        self.assertIsInstance(store_2da_0c, RowValueRowCell)
        self.assertEqual("label", store_2da_0c.column)

    def test_2da_changerow_cells(self):
        """Test that cells are set to be modified correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            ChangeRow0=change_row_0

            [change_row_0]
            RowIndex=0
            label=Test123
            dialog=StrRef4
            appearance=2DAMEMORY5
            """
        )
        # noinspection PyTypeChecker
        mod_2da_0: ChangeRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore

        # noinspection PyTypeChecker
        cell_0_label: RowValueConstant = mod_2da_0.cells["label"]  # type: ignore
        self.assertIsInstance(cell_0_label, RowValueConstant)
        self.assertEqual("Test123", cell_0_label.string)

        # noinspection PyTypeChecker
        cell_0_dialog: RowValueTLKMemory = mod_2da_0.cells["dialog"]  # type: ignore
        self.assertIsInstance(cell_0_dialog, RowValueTLKMemory)
        self.assertEqual(4, cell_0_dialog.token_id)

        # noinspection PyTypeChecker
        cell_0_appearance: RowValue2DAMemory = mod_2da_0.cells["appearance"]  # type: ignore
        self.assertIsInstance(cell_0_appearance, RowValue2DAMemory)
        self.assertEqual(5, cell_0_appearance.token_id)

    # endregion

    # region 2DA: Add Row
    def test_2da_addrow_identifier(self):
        """Test that identifier is being loaded correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddRow0=add_row_0
            AddRow1=add_row_1

            [add_row_0]
            [add_row_1]
            """
        )
        # noinspection PyTypeChecker
        mod_0: AddRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore
        self.assertEqual("add_row_0", mod_0.identifier)

        # noinspection PyTypeChecker
        mod_1: AddRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore
        self.assertEqual("add_row_1", mod_1.identifier)

    def test_2da_addrow_exclusivecolumn(self):
        """Test that exclusive column property is being loaded correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddRow0=add_row_0
            AddRow1=add_row_1

            [add_row_0]
            ExclusiveColumn=label
            [add_row_1]
            """
        )
        # noinspection PyTypeChecker
        mod_0: AddRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore
        self.assertIsInstance(mod_0, AddRow2DA)
        self.assertEqual("add_row_0", mod_0.identifier)
        self.assertEqual("label", mod_0.exclusive_column)

        # noinspection PyTypeChecker
        mod_1: AddRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore
        self.assertIsInstance(mod_1, AddRow2DA)
        self.assertEqual("add_row_1", mod_1.identifier)
        self.assertIsNone(mod_1.exclusive_column)

    def test_2da_addrow_rowlabel(self):
        """Test that row label property is being loaded correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddRow0=add_row_0
            AddRow1=add_row_1

            [add_row_0]
            RowLabel=123
            [add_row_1]
            """
        )
        # noinspection PyTypeChecker
        mod_0: AddRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore
        self.assertIsInstance(mod_0, AddRow2DA)
        self.assertEqual("add_row_0", mod_0.identifier)
        self.assertEqual("123", mod_0.row_label)

        # noinspection PyTypeChecker
        mod_1: AddRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore
        self.assertIsInstance(mod_1, AddRow2DA)
        self.assertEqual("add_row_1", mod_1.identifier)
        self.assertIsNone(mod_1.row_label)

    def test_2da_addrow_store2da(self):
        """Test that 2DAMEMORY# data will be saved correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddRow0=add_row_0

            [add_row_0]
            2DAMEMORY0=RowIndex
            2DAMEMORY1=RowLabel
            2DAMEMORY2=label
            """
        )
        # noinspection PyTypeChecker
        mod_0: AddRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore

        # noinspection PyTypeChecker
        store_0a: RowValueRowIndex = mod_0.store_2da[0]  # type: ignore
        self.assertIsInstance(store_0a, RowValueRowIndex)

        # noinspection PyTypeChecker
        store_0b: RowValueRowLabel = mod_0.store_2da[1]  # type: ignore
        self.assertIsInstance(store_0b, RowValueRowLabel)

        # noinspection PyTypeChecker
        store_0c: RowValueRowCell = mod_0.store_2da[2]  # type: ignore
        self.assertIsInstance(store_0c, RowValueRowCell)
        self.assertEqual("label", store_0c.column)

    def test_2da_addrow_cells(self):
        """Test that cells will be assigned properly correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddRow0=add_row_0

            [add_row_0]
            label=Test123
            dialog=StrRef4
            appearance=2DAMEMORY5
            """
        )
        # noinspection PyTypeChecker
        mod_0: AddRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore

        # noinspection PyTypeChecker
        cell_0_label: RowValueConstant = mod_0.cells["label"]  # type: ignore
        self.assertIsInstance(cell_0_label, RowValueConstant)
        self.assertEqual("Test123", cell_0_label.string)

        # noinspection PyTypeChecker
        cell_0_dialog: RowValueTLKMemory = mod_0.cells["dialog"]  # type: ignore
        self.assertIsInstance(cell_0_dialog, RowValueTLKMemory)
        self.assertEqual(4, cell_0_dialog.token_id)

        # noinspection PyTypeChecker
        cell_0_appearance: RowValue2DAMemory = mod_0.cells["appearance"]  # type: ignore
        self.assertIsInstance(cell_0_appearance, RowValue2DAMemory)
        self.assertEqual(5, cell_0_appearance.token_id)

    # endregion Add Row

    # region 2DA: Copy Row
    def test_2da_copyrow_identifier(self):
        """Test that identifier is being loaded correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            CopyRow0=copy_row_0
            CopyRow1=copy_row_1

            [copy_row_0]
            RowIndex=1
            [copy_row_1]
            RowLabel=1
            """
        )
        # noinspection PyTypeChecker
        mod_0: CopyRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore
        self.assertEqual("copy_row_0", mod_0.identifier)

        # noinspection PyTypeChecker
        mod_1: CopyRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore
        self.assertEqual("copy_row_1", mod_1.identifier)

    def test_2da_copyrow_high(self):
        """Test that high() is working correctly in copyrow's."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=spells_hlfp_test.2da

            [spells_hlfp_test.2da]
            CopyRow0=spells_forcestrike

            [spells_forcestrike]
            RowIndex=23
            ExclusiveColumn=label
            label=ST_FORCE_POWER_STRIKE
            name=StrRef0
            spelldesc=StrRef1
            forcepoints=55
            jedimaster=21
            sithlord=21
            guardian=-1
            consular=-1
            sentinel=-1
            weapmstr=-1
            watchman=-1
            marauder=-1
            assassin=-1
            inate=21
            maxcr=12
            category=0x4101
            iconresref=ip_st_strike
            impactscript=st_forcestrike
            conjanim=up
            castanim=up
            forcehostile=high()
            dark_recom=****
            light_recom=****
            forcepriority=0
            pips=3
            """
        )
        # noinspection PyTypeChecker
        mod_0: CopyRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore

        # Asserting all properties of mod_0
        self.assertEqual(TargetType.ROW_INDEX, mod_0.target.target_type)
        self.assertEqual(23, mod_0.target.value)
        self.assertEqual("spells_forcestrike", mod_0.identifier)
        self.assertEqual("label", mod_0.exclusive_column)
        self.assertEqual("ST_FORCE_POWER_STRIKE", mod_0.cells["label"].string)
        self.assertEqual("55", mod_0.cells["forcepoints"].string)
        self.assertEqual("21", mod_0.cells["jedimaster"].string)
        self.assertEqual("21", mod_0.cells["sithlord"].string)
        self.assertEqual("-1", mod_0.cells["guardian"].string)
        self.assertEqual("-1", mod_0.cells["consular"].string)
        self.assertEqual("-1", mod_0.cells["sentinel"].string)
        self.assertEqual("-1", mod_0.cells["weapmstr"].string)
        self.assertEqual("-1", mod_0.cells["watchman"].string)
        self.assertEqual("-1", mod_0.cells["marauder"].string)
        self.assertEqual("-1", mod_0.cells["assassin"].string)
        self.assertEqual("21", mod_0.cells["inate"].string)
        self.assertEqual("12", mod_0.cells["maxcr"].string)
        self.assertEqual(f"{0x4101:#x}", mod_0.cells["category"].string)
        self.assertEqual("ip_st_strike", mod_0.cells["iconresref"].string)
        self.assertEqual("st_forcestrike", mod_0.cells["impactscript"].string)
        self.assertEqual("up", mod_0.cells["conjanim"].string)
        self.assertEqual("up", mod_0.cells["castanim"].string)
        self.assertEqual("forcehostile", mod_0.cells["forcehostile"].column)
        self.assertIsInstance(mod_0.cells["forcehostile"], RowValueHigh)
        self.assertEqual("", mod_0.cells["dark_recom"].string)
        self.assertEqual("", mod_0.cells["light_recom"].string)
        self.assertEqual("0", mod_0.cells["forcepriority"].string)
        self.assertEqual("3", mod_0.cells["pips"].string)

    def test_2da_copyrow_target(self):
        """Test that target values (line to modify) are loading correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            CopyRow0=copy_row_0
            CopyRow1=copy_row_1
            CopyRow2=copy_row_2

            [copy_row_0]
            RowIndex=1
            [copy_row_1]
            RowLabel=2
            [copy_row_2]
            LabelIndex=3
            """
        )
        # noinspection PyTypeChecker
        mod_0: CopyRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore
        self.assertEqual(TargetType.ROW_INDEX, mod_0.target.target_type)
        self.assertEqual(1, mod_0.target.value)

        # noinspection PyTypeChecker
        mod_1: CopyRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore
        self.assertEqual(TargetType.ROW_LABEL, mod_1.target.target_type)
        self.assertEqual("2", mod_1.target.value)

        # noinspection PyTypeChecker
        mod_2: CopyRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore
        self.assertEqual(TargetType.LABEL_COLUMN, mod_2.target.target_type)
        self.assertEqual("3", mod_2.target.value)

    def test_2da_copyrow_exclusivecolumn(self):
        """Test that exclusive column property is being loaded correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            CopyRow0=copy_row_0
            CopyRow1=copy_row_1

            [copy_row_0]
            RowIndex=0
            ExclusiveColumn=label
            [copy_row_1]
            RowIndex=0
            """
        )
        # noinspection PyTypeChecker
        mod_0: CopyRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore
        self.assertIsInstance(mod_0, CopyRow2DA)
        self.assertEqual("copy_row_0", mod_0.identifier)
        self.assertEqual("label", mod_0.exclusive_column)

        # noinspection PyTypeChecker
        mod_1: CopyRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore
        self.assertIsInstance(mod_1, CopyRow2DA)
        self.assertEqual("copy_row_1", mod_1.identifier)
        self.assertIsNone(mod_1.exclusive_column)

    def test_2da_copyrow_rowlabel(self):
        """Test that row label property is being loaded correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            CopyRow0=copy_row_0
            CopyRow1=copy_row_1

            [copy_row_0]
            RowIndex=0
            NewRowLabel=123
            [copy_row_1]
            RowIndex=0
            """
        )
        # noinspection PyTypeChecker
        mod_0: CopyRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore
        self.assertIsInstance(mod_0, CopyRow2DA)
        self.assertEqual("copy_row_0", mod_0.identifier)
        self.assertEqual("123", mod_0.row_label)

        # noinspection PyTypeChecker
        mod_1: CopyRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore
        self.assertIsInstance(mod_1, CopyRow2DA)
        self.assertEqual("copy_row_1", mod_1.identifier)
        self.assertIsNone(mod_1.row_label)

    def test_2da_copyrow_store2da(self):
        """Test that 2DAMEMORY# data will be saved correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            CopyRow0=copy_row_0

            [copy_row_0]
            RowLabel=0
            2DAMEMORY0=RowIndex
            2DAMEMORY1=RowLabel
            2DAMEMORY2=label
            """
        )
        # noinspection PyTypeChecker
        mod_0: CopyRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore

        # noinspection PyTypeChecker
        store_0a: RowValueRowIndex = mod_0.store_2da[0]  # type: ignore
        self.assertIsInstance(store_0a, RowValueRowIndex)

        # noinspection PyTypeChecker
        store_0b: RowValueRowLabel = mod_0.store_2da[1]  # type: ignore
        self.assertIsInstance(store_0b, RowValueRowLabel)

        # noinspection PyTypeChecker
        store_0c: RowValueRowCell = mod_0.store_2da[2]  # type: ignore
        self.assertIsInstance(store_0c, RowValueRowCell)
        self.assertEqual("label", store_0c.column)

    def test_2da_copyrow_cells(self):
        """Test that cells will be assigned properly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            CopyRow0=copy_row_0

            [copy_row_0]
            RowLabel=0
            label=Test123
            dialog=StrRef4
            appearance=2DAMEMORY5
            """
        )
        # noinspection PyTypeChecker
        mod_0: CopyRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore

        # noinspection PyTypeChecker
        cell_0_label: RowValueConstant = mod_0.cells["label"]  # type: ignore
        self.assertIsInstance(cell_0_label, RowValueConstant)
        self.assertEqual("Test123", cell_0_label.string)

        # noinspection PyTypeChecker
        cell_0_dialog: RowValueTLKMemory = mod_0.cells["dialog"]  # type: ignore
        self.assertIsInstance(cell_0_dialog, RowValueTLKMemory)
        self.assertEqual(4, cell_0_dialog.token_id)

        # noinspection PyTypeChecker
        cell_0_appearance: RowValue2DAMemory = mod_0.cells["appearance"]  # type: ignore
        self.assertIsInstance(cell_0_appearance, RowValue2DAMemory)
        self.assertEqual(5, cell_0_appearance.token_id)

    # endregion

    # region 2DA: Add Column
    def test_2da_addcolumn_basic(self):
        """Test that column will be inserted with correct label and default values."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddColumn0=add_column_0
            AddColumn1=add_column_1

            [add_column_0]
            ColumnLabel=label
            DefaultValue=****
            2DAMEMORY2=I2

            [add_column_1]
            ColumnLabel=someint
            DefaultValue=0
            2DAMEMORY2=I2
            """
        )
        # noinspection PyTypeChecker
        mod_0: AddColumn2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore
        self.assertEqual("label", mod_0.header)
        self.assertEqual("", mod_0.default)

        # noinspection PyTypeChecker
        mod_1: AddColumn2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore
        self.assertEqual("someint", mod_1.header)
        self.assertEqual("0", mod_1.default)

    def test_2da_addcolumn_indexinsert(self):
        """Test that cells will be inserted to the new column at the given index correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddColumn0=add_column_0

            [add_column_0]
            ColumnLabel=NewColumn
            DefaultValue=****
            I0=abc
            I1=2DAMEMORY4
            I2=StrRef5
            """
        )
        # noinspection PyTypeChecker
        mod_0: AddColumn2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore

        value = mod_0.index_insert[0]
        self.assertIsInstance(value, RowValueConstant)
        self.assertEqual("abc", value.string)  # type: ignore

        value = mod_0.index_insert[1]
        self.assertIsInstance(value, RowValue2DAMemory)
        self.assertEqual(4, value.token_id)  # type: ignore

        value = mod_0.index_insert[2]
        self.assertIsInstance(value, RowValueTLKMemory)
        self.assertEqual(5, value.token_id)  # type: ignore

    def test_2da_addcolumn_labelinsert(self):
        """Test that cells will be inserted to the new column at the given label correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddColumn0=add_column_0

            [add_column_0]
            ColumnLabel=NewColumn
            DefaultValue=****
            L0=abc
            L1=2DAMEMORY4
            L2=StrRef5
            """
        )
        # noinspection PyTypeChecker
        mod_0: AddColumn2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore

        value = mod_0.label_insert["0"]
        self.assertIsInstance(value, RowValueConstant)
        self.assertEqual("abc", value.string)  # type: ignore

        value = mod_0.label_insert["1"]
        self.assertIsInstance(value, RowValue2DAMemory)
        self.assertEqual(4, value.token_id)  # type: ignore

        value = mod_0.label_insert["2"]
        self.assertIsInstance(value, RowValueTLKMemory)
        self.assertEqual(5, value.token_id)  # type: ignore

    def test_2da_addcolumn_2damemory(self):
        """Test that 2DAMEMORY will be stored correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddColumn0=add_column_0

            [add_column_0]
            ColumnLabel=NewColumn
            DefaultValue=****
            2DAMEMORY2=I2
            """
        )
        # noinspection PyTypeChecker
        mod_0: AddColumn2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore

        value = mod_0.store_2da[2]
        self.assertEqual("I2", value)

    # endregion

    # region SSF
    def test_ssf_replace(self):
        """Test that the replace file boolean is registered correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [SSFList]
            File0=test1.ssf
            Replace0=test2.ssf

            [test1.ssf]
            [test2.ssf]
            """
        )
        self.assertFalse(config.patches_ssf[0].replace_file)
        self.assertTrue(config.patches_ssf[1].replace_file)

    def test_ssf_stored_constant(self):
        """Test that the set sound as constant stringref is registered correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [SSFList]
            File0=test.ssf

            [test.ssf]
            Battlecry 1=123
            Battlecry 2=456
            """
        )
        mod_0: ModifySSF = config.patches_ssf[0].modifiers.pop(0)
        self.assertIsInstance(mod_0.stringref, NoTokenUsage)
        self.assertEqual("123", mod_0.stringref.stored)  # type: ignore

        mod_1: ModifySSF = config.patches_ssf[0].modifiers.pop(0)
        self.assertIsInstance(mod_1.stringref, NoTokenUsage)
        self.assertEqual("456", mod_1.stringref.stored)  # type: ignore

    def test_ssf_stored_2da(self):
        """Test that the set sound as 2DAMEMORY value is registered correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [SSFList]
            File0=test.ssf

            [test.ssf]
            Battlecry 1=2DAMEMORY5
            Battlecry 2=2DAMEMORY6
            """
        )
        mod_0: ModifySSF = config.patches_ssf[0].modifiers.pop(0)
        self.assertIsInstance(mod_0.stringref, TokenUsage2DA)
        self.assertEqual(5, mod_0.stringref.token_id)  # type: ignore

        mod_1: ModifySSF = config.patches_ssf[0].modifiers.pop(0)
        self.assertIsInstance(mod_1.stringref, TokenUsage2DA)
        self.assertEqual(6, mod_1.stringref.token_id)  # type: ignore

    def test_ssf_stored_tlk(self):
        """Test that the set sound as StrRef is registered correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [SSFList]
            File0=test.ssf

            [test.ssf]
            Battlecry 1=StrRef5
            Battlecry 2=StrRef6
            """
        )
        mod_0: ModifySSF = config.patches_ssf[0].modifiers.pop(0)
        self.assertIsInstance(mod_0.stringref, TokenUsageTLK)
        self.assertEqual(5, mod_0.stringref.token_id)

        mod_1: ModifySSF = config.patches_ssf[0].modifiers.pop(0)
        self.assertIsInstance(mod_1.stringref, TokenUsageTLK)
        self.assertEqual(6, mod_1.stringref.token_id)

    def test_ssf_set(self):
        """Test that each sound is mapped and will register correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [SSFList]
            File0=test.ssf

            [test.ssf]
            Battlecry 1=1
            Battlecry 2=2
            Battlecry 3=3
            Battlecry 4=4
            Battlecry 5=5
            Battlecry 6=6
            Selected 1=7
            Selected 2=8
            Selected 3=9
            Attack 1=10
            Attack 2=11
            Attack 3=12
            Pain 1=13
            Pain 2=14
            Low health=15
            Death=16
            Critical hit=17
            Target immune=18
            Place mine=19
            Disarm mine=20
            Stealth on=21
            Search=22
            Pick lock start=23
            Pick lock fail=24
            Pick lock done=25
            Leave party=26
            Rejoin party=27
            Poisoned=28
            """
        )
        mod_battlecry1 = config.patches_ssf[0].modifiers.pop(0)
        mod_battlecry2 = config.patches_ssf[0].modifiers.pop(0)
        mod_battlecry3 = config.patches_ssf[0].modifiers.pop(0)
        mod_battlecry4 = config.patches_ssf[0].modifiers.pop(0)
        mod_battlecry5 = config.patches_ssf[0].modifiers.pop(0)
        mod_battlecry6 = config.patches_ssf[0].modifiers.pop(0)
        mod_selected1 = config.patches_ssf[0].modifiers.pop(0)
        mod_selected2 = config.patches_ssf[0].modifiers.pop(0)
        mod_selected3 = config.patches_ssf[0].modifiers.pop(0)
        mod_attack1 = config.patches_ssf[0].modifiers.pop(0)
        mod_attack2 = config.patches_ssf[0].modifiers.pop(0)
        mod_attack3 = config.patches_ssf[0].modifiers.pop(0)
        mod_pain1 = config.patches_ssf[0].modifiers.pop(0)
        mod_pain2 = config.patches_ssf[0].modifiers.pop(0)
        mod_lowhealth = config.patches_ssf[0].modifiers.pop(0)
        mod_death = config.patches_ssf[0].modifiers.pop(0)
        mod_criticalhit = config.patches_ssf[0].modifiers.pop(0)
        mod_targetimmune = config.patches_ssf[0].modifiers.pop(0)
        mod_placemine = config.patches_ssf[0].modifiers.pop(0)
        mod_disarmmine = config.patches_ssf[0].modifiers.pop(0)
        mod_stealthon = config.patches_ssf[0].modifiers.pop(0)
        mod_search = config.patches_ssf[0].modifiers.pop(0)
        mod_picklockstart = config.patches_ssf[0].modifiers.pop(0)
        mod_picklockfail = config.patches_ssf[0].modifiers.pop(0)
        mod_picklockdone = config.patches_ssf[0].modifiers.pop(0)
        mod_leaveparty = config.patches_ssf[0].modifiers.pop(0)
        mod_rejoinparty = config.patches_ssf[0].modifiers.pop(0)
        mod_poisoned = config.patches_ssf[0].modifiers.pop(0)

        self.assertEqual(SSFSound.BATTLE_CRY_1, mod_battlecry1.sound)
        self.assertEqual(SSFSound.BATTLE_CRY_2, mod_battlecry2.sound)
        self.assertEqual(SSFSound.BATTLE_CRY_3, mod_battlecry3.sound)
        self.assertEqual(SSFSound.BATTLE_CRY_4, mod_battlecry4.sound)
        self.assertEqual(SSFSound.BATTLE_CRY_5, mod_battlecry5.sound)
        self.assertEqual(SSFSound.BATTLE_CRY_6, mod_battlecry6.sound)
        self.assertEqual(SSFSound.SELECT_1, mod_selected1.sound)
        self.assertEqual(SSFSound.SELECT_2, mod_selected2.sound)
        self.assertEqual(SSFSound.SELECT_3, mod_selected3.sound)
        self.assertEqual(SSFSound.ATTACK_GRUNT_1, mod_attack1.sound)
        self.assertEqual(SSFSound.ATTACK_GRUNT_2, mod_attack2.sound)
        self.assertEqual(SSFSound.ATTACK_GRUNT_3, mod_attack3.sound)
        self.assertEqual(SSFSound.PAIN_GRUNT_1, mod_pain1.sound)
        self.assertEqual(SSFSound.PAIN_GRUNT_2, mod_pain2.sound)
        self.assertEqual(SSFSound.LOW_HEALTH, mod_lowhealth.sound)
        self.assertEqual(SSFSound.DEAD, mod_death.sound)
        self.assertEqual(SSFSound.CRITICAL_HIT, mod_criticalhit.sound)
        self.assertEqual(SSFSound.TARGET_IMMUNE, mod_targetimmune.sound)
        self.assertEqual(SSFSound.LAY_MINE, mod_placemine.sound)
        self.assertEqual(SSFSound.DISARM_MINE, mod_disarmmine.sound)
        self.assertEqual(SSFSound.BEGIN_STEALTH, mod_stealthon.sound)
        self.assertEqual(SSFSound.BEGIN_SEARCH, mod_search.sound)
        self.assertEqual(SSFSound.BEGIN_UNLOCK, mod_picklockstart.sound)
        self.assertEqual(SSFSound.UNLOCK_FAILED, mod_picklockfail.sound)
        self.assertEqual(SSFSound.UNLOCK_SUCCESS, mod_picklockdone.sound)
        self.assertEqual(SSFSound.SEPARATED_FROM_PARTY, mod_leaveparty.sound)
        self.assertEqual(SSFSound.REJOINED_PARTY, mod_rejoinparty.sound)
        self.assertEqual(SSFSound.POISONED, mod_poisoned.sound)

    # endregion

    # region GFF: Modify
    def test_gff_modify_pathing(self):
        """Test that the modify path for the field registered correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            ClassList\\0\\Class=123
            """
        )
        mod_0 = config.patches_gff[0].modifiers.pop(0)
        self.assertIsInstance(mod_0, ModifyFieldGFF)
        self.assertEqual("ClassList\\0\\Class", str(mod_0.path))

    def test_gff_modify_type_int(self):
        """Test that the modify field modifiers are registered correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            SomeInt=123
            """
        )
        mod_0 = config.patches_gff[0].modifiers.pop(0)
        self.assertIsInstance(mod_0, ModifyFieldGFF)
        self.assertIsInstance(mod_0.value, FieldValueConstant)
        self.assertEqual("SomeInt", str(mod_0.path))
        self.assertEqual(123, mod_0.value.stored)

    def test_gff_modify_type_string(self):
        """Test that the modify field modifiers are registered correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            SomeString=abc
            """
        )
        mod_0 = config.patches_gff[0].modifiers.pop(0)
        self.assertIsInstance(mod_0, ModifyFieldGFF)
        self.assertIsInstance(mod_0.value, FieldValueConstant)
        self.assertEqual("SomeString", str(mod_0.path))
        self.assertEqual("abc", mod_0.value.stored)

    def test_gff_modify_type_vector3(self):
        """Test that the modify field modifiers are registered correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            SomeVector=1|2|3
            """
        )
        mod_0 = config.patches_gff[0].modifiers.pop(0)
        self.assertIsInstance(mod_0, ModifyFieldGFF)
        self.assertIsInstance(mod_0.value, FieldValueConstant)
        self.assertEqual("SomeVector", str(mod_0.path))
        self.assertEqual(Vector3(1, 2, 3), mod_0.value.stored)

    def test_gff_modify_type_vector4(self):
        """Test that the modify field modifiers are registered correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            SomeVector=1|2|3|4
            """
        )
        mod_0 = config.patches_gff[0].modifiers.pop(0)
        self.assertIsInstance(mod_0, ModifyFieldGFF)
        self.assertIsInstance(mod_0.value, FieldValueConstant)
        self.assertEqual("SomeVector", str(mod_0.path))
        self.assertEqual(Vector4(1, 2, 3, 4), mod_0.value.stored)

    def test_gff_modify_type_locstring(self):
        """Test that the modify field modifiers are registered correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            LocString(strref)=5
            LocString(lang0)=hello
            LocString(lang3)=world
            """
        )
        mod_0 = self._assert_types_and_path(config)
        self.assertIsInstance(mod_0.value.stored.stringref, FieldValueConstant)
        self.assertEqual(5, mod_0.value.stored.stringref.stored)
        self.assertEqual(0, len(mod_0.value.stored))

        mod_1 = self._assert_types_and_path(config)
        self.assertIsNone(mod_1.value.stored.stringref)
        self.assertEqual("hello", mod_1.value.stored.get(Language.ENGLISH, Gender.MALE))
        self.assertEqual(1, len(mod_1.value.stored))

        mod_2 = self._assert_types_and_path(config)
        self.assertEqual("world", mod_2.value.stored.get(Language.FRENCH, Gender.FEMALE))
        self.assertIsNone(mod_2.value.stored.stringref)
        self.assertEqual(1, len(mod_2.value.stored))

    def _assert_types_and_path(self, config):
        result = config.patches_gff[0].modifiers.pop(0)
        self.assertIsInstance(result, ModifyFieldGFF)
        self.assertIsInstance(result.value, FieldValueConstant)
        self.assertIsInstance(result.value.stored, LocalizedStringDelta)
        self.assertEqual("LocString", str(result.path))
        return result

    def test_gff_modify_2damemory(self):
        """Test that the modify field modifiers are registered correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            LocString(strref)=StrRef5
            SomeField=StrRef2
            """
        )
        mod_0 = config.patches_gff[0].modifiers.pop(0)
        self.assertIsInstance(mod_0, ModifyFieldGFF)
        self.assertIsInstance(mod_0.value, FieldValueConstant)
        self.assertIsInstance(mod_0.value.stored, LocalizedStringDelta)
        self.assertEqual("LocString", str(mod_0.path))
        self.assertIsInstance(mod_0.value.stored.stringref, FieldValueTLKMemory)
        self.assertEqual(5, mod_0.value.stored.stringref.token_id)

        mod_1 = config.patches_gff[0].modifiers.pop(0)
        self.assertIsInstance(mod_1, ModifyFieldGFF)
        self.assertIsInstance(mod_1.value, FieldValueTLKMemory)
        self.assertEqual(2, mod_1.value.token_id)

    def test_gff_modify_tlkmemory(self):
        """Test that the modify field modifiers are registered correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            SomeField=2DAMEMORY12
            """
        )
        mod_0 = config.patches_gff[0].modifiers.pop(0)
        self.assertIsInstance(mod_0, ModifyFieldGFF)
        self.assertIsInstance(mod_0.value, FieldValue2DAMemory)
        self.assertEqual(12, mod_0.value.token_id)

    # endregion

    # region GFF: Add
    def test_gff_add_ints(self):
        """Test that the add field modifiers are registered correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=add_uint8
            AddField1=add_int8
            AddField2=add_uint16
            AddField3=add_int16
            AddField4=add_uint32
            AddField5=add_int32
            AddField7=add_int64

            [add_uint8]
            FieldType=Byte
            Path=SomeList
            Label=SomeField
            Value=123

            [add_int8]
            FieldType=Char
            Path=SomeList
            Label=SomeField
            Value=123

            [add_uint16]
            FieldType=Word
            Path=SomeList
            Label=SomeField
            Value=123

            [add_int16]
            FieldType=Short
            Path=SomeList
            Label=SomeField
            Value=123

            [add_uint32]
            FieldType=DWORD
            Path=SomeList
            Label=SomeField
            Value=123

            [add_int32]
            FieldType=Int
            Path=SomeList
            Label=SomeField
            Value=123

            [add_int64]
            FieldType=Int64
            Path=SomeList
            Label=SomeField
            Value=123
            """
        )
        mod_0 = config.patches_gff[0].modifiers.pop(0)
        self._assert_batch(mod_0, 123)

        mod_1 = config.patches_gff[0].modifiers.pop(0)
        self._assert_batch(mod_1, 123)

        mod_2 = config.patches_gff[0].modifiers.pop(0)
        self._assert_batch(mod_2, 123)

        mod_3 = config.patches_gff[0].modifiers.pop(0)
        self._assert_batch(mod_3, 123)

        mod_4 = config.patches_gff[0].modifiers.pop(0)
        self._assert_batch(mod_4, 123)

        mod_5 = config.patches_gff[0].modifiers.pop(0)
        self._assert_batch(mod_5, 123)

        mod_6 = config.patches_gff[0].modifiers.pop(0)
        self._assert_batch(mod_6, 123)

    def _assert_batch(self, this_mod: ModifyGFF | AddFieldGFF, stored):
        this_mod = cast(AddFieldGFF, this_mod)
        this_mod.value = cast(FieldValueConstant, this_mod.value)
        self.assertIsInstance(this_mod, AddFieldGFF)
        self.assertIsInstance(this_mod.value, FieldValueConstant)
        self.assertEqual("SomeList", str(this_mod.path))
        self.assertEqual("SomeField", this_mod.label)
        self.assertEqual(stored, this_mod.value.stored)

    def test_gff_add_floats(self):
        """Test that the add field modifiers are registered correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=add_single
            AddField1=add_double

            [add_single]
            FieldType=Float
            Path=SomeList
            Label=SomeField
            Value=1.23

            [add_double]
            FieldType=Double
            Path=SomeList
            Label=SomeField
            Value=1.23
            """
        )
        mod_0 = config.patches_gff[0].modifiers.pop(0)
        self._assert_batch(mod_0, 1.23)

        mod_1 = config.patches_gff[0].modifiers.pop(0)
        self._assert_batch(mod_1, 1.23)

    def test_gff_add_string(self):
        """Test that the add field modifiers are registered correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=add_string

            [add_string]
            FieldType=ExoString
            Path=SomeList
            Label=SomeField
            Value=abc
            """
        )
        mod_0 = config.patches_gff[0].modifiers.pop(0)
        self._assert_batch(mod_0, "abc")

    def test_gff_add_vector3(self):
        """Test that the add field modifiers are registered correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=add_vector3

            [add_vector3]
            FieldType=Position
            Path=SomeList
            Label=SomeField
            Value=1|2|3
            """
        )
        mod_0 = config.patches_gff[0].modifiers.pop(0)
        self._assert_batch(mod_0, Vector3(1, 2, 3))

    def test_gff_add_vector4(self):
        """Test that the add field modifiers are registered correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=add_vector4

            [add_vector4]
            FieldType=Orientation
            Path=SomeList
            Label=SomeField
            Value=1|2|3|4
            """
        )
        mod_0 = config.patches_gff[0].modifiers.pop(0)
        self._assert_batch(mod_0, Vector4(1, 2, 3, 4))

    def test_gff_add_resref(self):
        """Test that the add field modifiers are registered correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=add_resref

            [add_resref]
            FieldType=ResRef
            Path=SomeList
            Label=SomeField
            Value=abc
            """
        )
        mod_0 = config.patches_gff[0].modifiers.pop(0)
        self._assert_batch(mod_0, ResRef("abc"))

    def test_gff_add_locstring(self):
        """Test that the add field modifiers are registered correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=add_locstring
            AddField1=add_locstring2

            [add_locstring]
            FieldType=ExoLocString
            Path=SomeList
            Label=SomeField
            StrRef=123
            lang0=abc
            lang3=lmnop

            [add_locstring2]
            FieldType=ExoLocString
            Path=
            Label=SomeField2
            StrRef=StrRef8
            """
        )
        mod_0 = config.patches_gff[0].modifiers.pop(0)
        self.assertIsInstance(mod_0, AddFieldGFF)
        assert isinstance(mod_0, AddFieldGFF)
        self.assertIsInstance(mod_0.value, FieldValueConstant)
        assert isinstance(mod_0.value, FieldValueConstant)
        self.assertIsInstance(mod_0.value.stored, LocalizedStringDelta)
        assert isinstance(mod_0.value.stored, LocalizedStringDelta)
        self.assertEqual("SomeList", str(mod_0.path))
        self.assertEqual("SomeField", mod_0.label)
        self.assertIsInstance(mod_0.value.stored.stringref, FieldValueConstant)
        assert isinstance(mod_0.value.stored.stringref, FieldValueConstant)
        self.assertEqual(123, mod_0.value.stored.stringref.stored)
        self.assertEqual("abc", mod_0.value.stored.get(Language.ENGLISH, Gender.MALE))
        self.assertEqual("lmnop", mod_0.value.stored.get(Language.FRENCH, Gender.FEMALE))

        mod_1 = config.patches_gff[0].modifiers.pop(0)
        self.assertIsInstance(mod_1, AddFieldGFF)
        assert isinstance(mod_1, AddFieldGFF)
        self.assertIsInstance(mod_1.value, FieldValueConstant)
        assert isinstance(mod_1.value, FieldValueConstant)
        self.assertIsInstance(mod_1.value.stored, LocalizedStringDelta)
        assert isinstance(mod_1.value.stored, LocalizedStringDelta)
        self.assertIsInstance(mod_1.value.stored.stringref, FieldValueTLKMemory)
        assert isinstance(mod_1.value.stored.stringref, FieldValueTLKMemory)
        self.assertEqual(8, mod_1.value.stored.stringref.token_id)

    def test_gff_add_inside_struct(self):
        """Test that the add field modifiers are registered correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=add_struct

            [add_struct]
            FieldType=Struct
            Path=
            Label=SomeStruct
            TypeId=321
            AddField0=add_insidestruct

            [add_insidestruct]
            FieldType=Byte
            Path=
            Label=InsideStruct
            Value=123
            """
        )
        mod_0 = config.patches_gff[0].modifiers.pop(0)
        self.assertIsInstance(mod_0, AddFieldGFF)
        assert isinstance(mod_0, AddFieldGFF)
        self.assertIsInstance(mod_0.value, FieldValueConstant)
        assert isinstance(mod_0.value, FieldValueConstant)
        self.assertEqual(mod_0.path.name, ">>##INDEXINLIST##<<")
        self.assertEqual("SomeStruct", mod_0.label)
        self.assertEqual(321, mod_0.value.stored.struct_id)

        mod_1 = mod_0.modifiers.pop(0)
        self.assertIsInstance(mod_1, AddFieldGFF)
        assert isinstance(mod_1, AddFieldGFF)
        self.assertIsInstance(mod_1.value, FieldValueConstant)
        assert isinstance(mod_1.value, FieldValueConstant)
        self.assertEqual(mod_1.path.name, "SomeStruct")
        self.assertEqual("InsideStruct", mod_1.label)
        self.assertEqual(123, mod_1.value.stored)

    def test_gff_add_inside_list(self):
        """Test that the add field modifiers are registered correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=add_list

            [add_list]
            FieldType=List
            Path=
            Label=SomeList
            AddField0=add_insidelist

            [add_insidelist]
            FieldType=Struct
            Label=
            TypeId=111
            2DAMEMORY5=ListIndex
            """
        )
        mod_0 = config.patches_gff[0].modifiers.pop(0)
        self.assertIsInstance(mod_0, AddFieldGFF)
        assert isinstance(mod_0, AddFieldGFF)
        self.assertIsInstance(mod_0.value, FieldValueConstant)
        assert isinstance(mod_0.value, FieldValueConstant)
        self.assertFalse(mod_0.path.name)
        self.assertEqual("SomeList", mod_0.label)

        mod_1 = mod_0.modifiers.pop(0)
        self.assertIsInstance(mod_1, AddStructToListGFF)
        assert isinstance(mod_1, AddStructToListGFF)
        self.assertIsInstance(mod_1.value, FieldValueConstant)
        assert isinstance(mod_1.value, FieldValueConstant)
        self.assertIsInstance(mod_1.value.value(None, GFFFieldType.Struct), GFFStruct)  # type: ignore[arg-type, reportGeneralTypeIssues]
        assert isinstance(mod_1.value.stored, GFFStruct)
        self.assertEqual(111, mod_1.value.stored.struct_id)
        self.assertEqual(5, mod_1.index_to_token)

    def _setupIniAndConfig(self, ini_text: str) -> PatcherConfig:
        ini = ConfigParser(delimiters="=", allow_no_value=True, strict=False, interpolation=None)
        ini.optionxform = lambda optionstr: optionstr
        ini.read_string(ini_text)
        result = PatcherConfig()
        ConfigReader(ini, "").load(result)
        return result

    # endregion


if __name__ == "__main__":
    unittest.main()
