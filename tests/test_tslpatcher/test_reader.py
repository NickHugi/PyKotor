from __future__ import annotations

import os
import pathlib
import shutil
import sys
import tempfile
import unittest
from configparser import ConfigParser
from pathlib import Path
from typing import TYPE_CHECKING, cast

THIS_SCRIPT_PATH = pathlib.Path(__file__).resolve()
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[3].joinpath("Libraries", "PyKotor", "src")
UTILITY_PATH = THIS_SCRIPT_PATH.parents[3].joinpath("Libraries", "Utility", "src")


def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from utility.common.geometry import Vector3, Vector4  # pyright: ignore[reportMissingImports]
from pykotor.common.language import Gender, Language  # pyright: ignore[reportMissingImports]
from pykotor.common.misc import ResRef  # pyright: ignore[reportMissingImports]
from pykotor.resource.formats.gff.gff_data import GFFFieldType, GFFStruct  # pyright: ignore[reportMissingImports]
from pykotor.resource.formats.ssf import SSFSound  # pyright: ignore[reportMissingImports]
from pykotor.resource.formats.tlk import TLK, write_tlk  # pyright: ignore[reportMissingImports]
from pykotor.resource.type import ResourceType  # pyright: ignore[reportMissingImports]
from pykotor.tslpatcher.config import PatcherConfig  # pyright: ignore[reportMissingImports]
from pykotor.tslpatcher.memory import NoTokenUsage, TokenUsage2DA, TokenUsageTLK  # pyright: ignore[reportMissingImports]
from pykotor.tslpatcher.mods.gff import (  # pyright: ignore[reportMissingImports]
    AddFieldGFF,
    AddStructToListGFF,
    FieldValue2DAMemory,
    FieldValueConstant,
    FieldValueTLKMemory,
    LocalizedStringDelta,
    ModifyFieldGFF,
    ModifyGFF
)
from pykotor.tslpatcher.mods.twoda import (  # pyright: ignore[reportMissingImports]
    AddRow2DA,
    CopyRow2DA,
    RowValue2DAMemory,
    RowValueConstant,
    RowValueHigh,
    RowValueRowCell,
    RowValueRowIndex,
    RowValueRowLabel,
    RowValueTLKMemory,
    TargetType
)
from pykotor.tslpatcher.reader import ConfigReader

if TYPE_CHECKING:
    from pykotor.tslpatcher.mods.ssf import ModifySSF  # pyright: ignore[reportMissingImports]
    from pykotor.tslpatcher.mods.tlk import ModifyTLK  # pyright: ignore[reportMissingImports]
    from pykotor.tslpatcher.mods.twoda import (  # pyright: ignore[reportMissingImports]
        AddColumn2DA,
        ChangeRow2DA
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
            inline_comment_prefixes=(";", "#"),
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
        self.temp_dir = tempfile.mkdtemp()
        self.mod_path = Path(self.temp_dir) / "tslpatchdata"
        self.mod_path.mkdir(exist_ok=True, parents=True)
        shutil.copy(Path("tests/test_pykotor/test_files/complex.tlk").resolve(), self.mod_path / "complex.tlk")
        shutil.copy(Path("tests/test_pykotor/test_files/append.tlk").resolve(), self.mod_path / "append.tlk")

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
        self.config_reader = ConfigReader(self.ini, self.mod_path, tslpatchdata_path=self.mod_path)  # type: ignore

    def tearDown(self):
        if hasattr(self, "temp_dir"):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

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

        assert len(self.config.patches_tlk.modifiers) == 3
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

        assert len(self.config.patches_tlk.modifiers) == 3
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
        assert len(self.config.patches_tlk.modifiers) == 26
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

        assert len(self.config.patches_tlk.modifiers) == 5
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
        assert mod_0.identifier == "change_row_0"

        # noinspection PyTypeChecker
        mod_0: ChangeRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore
        assert mod_0.identifier == "change_row_1"

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
        assert mod_2da_0.target.target_type == TargetType.ROW_INDEX
        assert mod_2da_0.target.value == 1

        # noinspection PyTypeChecker
        mod_2da_1: ChangeRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore
        assert mod_2da_1.target.target_type == TargetType.ROW_LABEL
        assert mod_2da_1.target.value == "2"

        # noinspection PyTypeChecker
        mod_2da_2: ChangeRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore
        assert mod_2da_2.target.target_type == TargetType.LABEL_COLUMN
        assert mod_2da_2.target.value == "3"

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
        assert isinstance(store_2da_0a, RowValueRowIndex)

        # noinspection PyTypeChecker
        store_2da_0b: RowValueRowLabel = mod_2da_0.store_2da[1]  # type: ignore
        assert isinstance(store_2da_0b, RowValueRowLabel)

        # noinspection PyTypeChecker
        store_2da_0c: RowValueRowCell = mod_2da_0.store_2da[2]  # type: ignore
        assert isinstance(store_2da_0c, RowValueRowCell)
        assert store_2da_0c.column == "label"

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
        assert isinstance(cell_0_label, RowValueConstant)
        assert cell_0_label.string == "Test123"

        # noinspection PyTypeChecker
        cell_0_dialog: RowValueTLKMemory = mod_2da_0.cells["dialog"]  # type: ignore
        assert isinstance(cell_0_dialog, RowValueTLKMemory)
        assert cell_0_dialog.token_id == 4

        # noinspection PyTypeChecker
        cell_0_appearance: RowValue2DAMemory = mod_2da_0.cells["appearance"]  # type: ignore
        assert isinstance(cell_0_appearance, RowValue2DAMemory)
        assert cell_0_appearance.token_id == 5

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
        assert mod_0.identifier == "add_row_0"

        # noinspection PyTypeChecker
        mod_1: AddRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore
        assert mod_1.identifier == "add_row_1"

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
        assert isinstance(mod_0, AddRow2DA)
        assert mod_0.identifier == "add_row_0"
        assert mod_0.exclusive_column == "label"

        # noinspection PyTypeChecker
        mod_1: AddRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore
        assert isinstance(mod_1, AddRow2DA)
        assert mod_1.identifier == "add_row_1"
        assert mod_1.exclusive_column is None

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
        assert isinstance(mod_0, AddRow2DA)
        assert mod_0.identifier == "add_row_0"
        assert mod_0.row_label == "123"

        # noinspection PyTypeChecker
        mod_1: AddRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore
        assert isinstance(mod_1, AddRow2DA)
        assert mod_1.identifier == "add_row_1"
        assert mod_1.row_label is None

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
        assert isinstance(store_0a, RowValueRowIndex)

        # noinspection PyTypeChecker
        store_0b: RowValueRowLabel = mod_0.store_2da[1]  # type: ignore
        assert isinstance(store_0b, RowValueRowLabel)

        # noinspection PyTypeChecker
        store_0c: RowValueRowCell = mod_0.store_2da[2]  # type: ignore
        assert isinstance(store_0c, RowValueRowCell)
        assert store_0c.column == "label"

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
        assert isinstance(cell_0_label, RowValueConstant)
        assert cell_0_label.string == "Test123"

        # noinspection PyTypeChecker
        cell_0_dialog: RowValueTLKMemory = mod_0.cells["dialog"]  # type: ignore
        assert isinstance(cell_0_dialog, RowValueTLKMemory)
        assert cell_0_dialog.token_id == 4

        # noinspection PyTypeChecker
        cell_0_appearance: RowValue2DAMemory = mod_0.cells["appearance"]  # type: ignore
        assert isinstance(cell_0_appearance, RowValue2DAMemory)
        assert cell_0_appearance.token_id == 5

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
        assert mod_0.identifier == "copy_row_0"

        # noinspection PyTypeChecker
        mod_1: CopyRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore
        assert mod_1.identifier == "copy_row_1"

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
        assert mod_0.target.target_type == TargetType.ROW_INDEX
        assert mod_0.target.value == 23
        assert mod_0.identifier == "spells_forcestrike"
        assert mod_0.exclusive_column == "label"
        assert mod_0.cells["label"].string == "ST_FORCE_POWER_STRIKE"
        assert mod_0.cells["forcepoints"].string == "55"
        assert mod_0.cells["jedimaster"].string == "21"
        assert mod_0.cells["sithlord"].string == "21"
        assert mod_0.cells["guardian"].string == "-1"
        assert mod_0.cells["consular"].string == "-1"
        assert mod_0.cells["sentinel"].string == "-1"
        assert mod_0.cells["weapmstr"].string == "-1"
        assert mod_0.cells["watchman"].string == "-1"
        assert mod_0.cells["marauder"].string == "-1"
        assert mod_0.cells["assassin"].string == "-1"
        assert mod_0.cells["inate"].string == "21"
        assert mod_0.cells["maxcr"].string == "12"
        assert f"{16641:#x}" == mod_0.cells["category"].string
        assert mod_0.cells["iconresref"].string == "ip_st_strike"
        assert mod_0.cells["impactscript"].string == "st_forcestrike"
        assert mod_0.cells["conjanim"].string == "up"
        assert mod_0.cells["castanim"].string == "up"
        assert mod_0.cells["forcehostile"].column == "forcehostile"
        assert isinstance(mod_0.cells["forcehostile"], RowValueHigh)
        assert mod_0.cells["dark_recom"].string == ""
        assert mod_0.cells["light_recom"].string == ""
        assert mod_0.cells["forcepriority"].string == "0"
        assert mod_0.cells["pips"].string == "3"

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
        assert mod_0.target.target_type == TargetType.ROW_INDEX
        assert mod_0.target.value == 1

        # noinspection PyTypeChecker
        mod_1: CopyRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore
        assert mod_1.target.target_type == TargetType.ROW_LABEL
        assert mod_1.target.value == "2"

        # noinspection PyTypeChecker
        mod_2: CopyRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore
        assert mod_2.target.target_type == TargetType.LABEL_COLUMN
        assert mod_2.target.value == "3"

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
        assert isinstance(mod_0, CopyRow2DA)
        assert mod_0.identifier == "copy_row_0"
        assert mod_0.exclusive_column == "label"

        # noinspection PyTypeChecker
        mod_1: CopyRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore
        assert isinstance(mod_1, CopyRow2DA)
        assert mod_1.identifier == "copy_row_1"
        assert mod_1.exclusive_column is None

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
        assert isinstance(mod_0, CopyRow2DA)
        assert mod_0.identifier == "copy_row_0"
        assert mod_0.row_label == "123"

        # noinspection PyTypeChecker
        mod_1: CopyRow2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore
        assert isinstance(mod_1, CopyRow2DA)
        assert mod_1.identifier == "copy_row_1"
        assert mod_1.row_label is None

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
        assert isinstance(store_0a, RowValueRowIndex)

        # noinspection PyTypeChecker
        store_0b: RowValueRowLabel = mod_0.store_2da[1]  # type: ignore
        assert isinstance(store_0b, RowValueRowLabel)

        # noinspection PyTypeChecker
        store_0c: RowValueRowCell = mod_0.store_2da[2]  # type: ignore
        assert isinstance(store_0c, RowValueRowCell)
        assert store_0c.column == "label"

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
        assert isinstance(cell_0_label, RowValueConstant)
        assert cell_0_label.string == "Test123"

        # noinspection PyTypeChecker
        cell_0_dialog: RowValueTLKMemory = mod_0.cells["dialog"]  # type: ignore
        assert isinstance(cell_0_dialog, RowValueTLKMemory)
        assert cell_0_dialog.token_id == 4

        # noinspection PyTypeChecker
        cell_0_appearance: RowValue2DAMemory = mod_0.cells["appearance"]  # type: ignore
        assert isinstance(cell_0_appearance, RowValue2DAMemory)
        assert cell_0_appearance.token_id == 5

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
        assert mod_0.header == "label"
        assert mod_0.default == ""

        # noinspection PyTypeChecker
        mod_1: AddColumn2DA = config.patches_2da[0].modifiers.pop(0)  # type: ignore
        assert mod_1.header == "someint"
        assert mod_1.default == "0"

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
        assert isinstance(value, RowValueConstant)
        assert value.string == "abc"  # type: ignore

        value = mod_0.index_insert[1]
        assert isinstance(value, RowValue2DAMemory)
        assert value.token_id == 4  # type: ignore

        value = mod_0.index_insert[2]
        assert isinstance(value, RowValueTLKMemory)
        assert value.token_id == 5  # type: ignore

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
        assert isinstance(value, RowValueConstant)
        assert value.string == "abc"  # type: ignore

        value = mod_0.label_insert["1"]
        assert isinstance(value, RowValue2DAMemory)
        assert value.token_id == 4  # type: ignore

        value = mod_0.label_insert["2"]
        assert isinstance(value, RowValueTLKMemory)
        assert value.token_id == 5  # type: ignore

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
        assert value == "I2"

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
        assert not config.patches_ssf[0].replace_file
        assert config.patches_ssf[1].replace_file

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
        assert isinstance(mod_0.stringref, NoTokenUsage)
        assert mod_0.stringref.stored == "123"  # type: ignore

        mod_1: ModifySSF = config.patches_ssf[0].modifiers.pop(0)
        assert isinstance(mod_1.stringref, NoTokenUsage)
        assert mod_1.stringref.stored == "456"  # type: ignore

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
        assert isinstance(mod_0.stringref, TokenUsage2DA)
        assert mod_0.stringref.token_id == 5  # type: ignore

        mod_1: ModifySSF = config.patches_ssf[0].modifiers.pop(0)
        assert isinstance(mod_1.stringref, TokenUsage2DA)
        assert mod_1.stringref.token_id == 6  # type: ignore

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
        assert isinstance(mod_0.stringref, TokenUsageTLK)
        assert mod_0.stringref.token_id == 5

        mod_1: ModifySSF = config.patches_ssf[0].modifiers.pop(0)
        assert isinstance(mod_1.stringref, TokenUsageTLK)
        assert mod_1.stringref.token_id == 6

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

        assert mod_battlecry1.sound == SSFSound.BATTLE_CRY_1
        assert mod_battlecry2.sound == SSFSound.BATTLE_CRY_2
        assert mod_battlecry3.sound == SSFSound.BATTLE_CRY_3
        assert mod_battlecry4.sound == SSFSound.BATTLE_CRY_4
        assert mod_battlecry5.sound == SSFSound.BATTLE_CRY_5
        assert mod_battlecry6.sound == SSFSound.BATTLE_CRY_6
        assert mod_selected1.sound == SSFSound.SELECT_1
        assert mod_selected2.sound == SSFSound.SELECT_2
        assert mod_selected3.sound == SSFSound.SELECT_3
        assert mod_attack1.sound == SSFSound.ATTACK_GRUNT_1
        assert mod_attack2.sound == SSFSound.ATTACK_GRUNT_2
        assert mod_attack3.sound == SSFSound.ATTACK_GRUNT_3
        assert mod_pain1.sound == SSFSound.PAIN_GRUNT_1
        assert mod_pain2.sound == SSFSound.PAIN_GRUNT_2
        assert mod_lowhealth.sound == SSFSound.LOW_HEALTH
        assert mod_death.sound == SSFSound.DEAD
        assert mod_criticalhit.sound == SSFSound.CRITICAL_HIT
        assert mod_targetimmune.sound == SSFSound.TARGET_IMMUNE
        assert mod_placemine.sound == SSFSound.LAY_MINE
        assert mod_disarmmine.sound == SSFSound.DISARM_MINE
        assert mod_stealthon.sound == SSFSound.BEGIN_STEALTH
        assert mod_search.sound == SSFSound.BEGIN_SEARCH
        assert mod_picklockstart.sound == SSFSound.BEGIN_UNLOCK
        assert mod_picklockfail.sound == SSFSound.UNLOCK_FAILED
        assert mod_picklockdone.sound == SSFSound.UNLOCK_SUCCESS
        assert mod_leaveparty.sound == SSFSound.SEPARATED_FROM_PARTY
        assert mod_rejoinparty.sound == SSFSound.REJOINED_PARTY
        assert mod_poisoned.sound == SSFSound.POISONED

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
        assert isinstance(mod_0, ModifyFieldGFF)
        assert str(mod_0.path) == "ClassList\\0\\Class"

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
        assert isinstance(mod_0, ModifyFieldGFF)
        assert isinstance(mod_0.value, FieldValueConstant)
        assert str(mod_0.path) == "SomeInt"
        assert mod_0.value.stored == 123

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
        assert isinstance(mod_0, ModifyFieldGFF)
        assert isinstance(mod_0.value, FieldValueConstant)
        assert str(mod_0.path) == "SomeString"
        assert mod_0.value.stored == "abc"

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
        assert isinstance(mod_0, ModifyFieldGFF)
        assert isinstance(mod_0.value, FieldValueConstant)
        assert str(mod_0.path) == "SomeVector"
        assert Vector3(1, 2, 3) == mod_0.value.stored

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
        assert isinstance(mod_0, ModifyFieldGFF)
        assert isinstance(mod_0.value, FieldValueConstant)
        assert str(mod_0.path) == "SomeVector"
        assert Vector4(1, 2, 3, 4) == mod_0.value.stored

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
        assert isinstance(mod_0.value.stored.stringref, FieldValueConstant)
        assert mod_0.value.stored.stringref.stored == 5
        assert len(mod_0.value.stored) == 0

        mod_1 = self._assert_types_and_path(config)
        assert mod_1.value.stored.stringref is None
        assert mod_1.value.stored.get(Language.ENGLISH, Gender.MALE) == "hello"
        assert len(mod_1.value.stored) == 1

        mod_2 = self._assert_types_and_path(config)
        assert mod_2.value.stored.get(Language.FRENCH, Gender.FEMALE) == "world"
        assert mod_2.value.stored.stringref is None
        assert len(mod_2.value.stored) == 1

    def _assert_types_and_path(self, config):
        result = config.patches_gff[0].modifiers.pop(0)
        assert isinstance(result, ModifyFieldGFF)
        assert isinstance(result.value, FieldValueConstant)
        assert isinstance(result.value.stored, LocalizedStringDelta)
        assert str(result.path) == "LocString"
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
        assert isinstance(mod_0, ModifyFieldGFF)
        assert isinstance(mod_0.value, FieldValueConstant)
        assert isinstance(mod_0.value.stored, LocalizedStringDelta)
        assert str(mod_0.path) == "LocString"
        assert isinstance(mod_0.value.stored.stringref, FieldValueTLKMemory)
        assert mod_0.value.stored.stringref.token_id == 5

        mod_1 = config.patches_gff[0].modifiers.pop(0)
        assert isinstance(mod_1, ModifyFieldGFF)
        assert isinstance(mod_1.value, FieldValueTLKMemory)
        assert mod_1.value.token_id == 2

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
        assert isinstance(mod_0, ModifyFieldGFF)
        assert isinstance(mod_0.value, FieldValue2DAMemory)
        assert mod_0.value.token_id == 12

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
        assert isinstance(this_mod, AddFieldGFF)
        assert isinstance(this_mod.value, FieldValueConstant)
        assert str(this_mod.path) == "SomeList"
        assert this_mod.label == "SomeField"
        assert stored == this_mod.value.stored

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
        assert isinstance(mod_0, AddFieldGFF)
        assert isinstance(mod_0, AddFieldGFF)
        assert isinstance(mod_0.value, FieldValueConstant)
        assert isinstance(mod_0.value, FieldValueConstant)
        assert isinstance(mod_0.value.stored, LocalizedStringDelta)
        assert isinstance(mod_0.value.stored, LocalizedStringDelta)
        assert str(mod_0.path) == "SomeList"
        assert mod_0.label == "SomeField"
        assert isinstance(mod_0.value.stored.stringref, FieldValueConstant)
        assert isinstance(mod_0.value.stored.stringref, FieldValueConstant)
        assert mod_0.value.stored.stringref.stored == 123
        assert mod_0.value.stored.get(Language.ENGLISH, Gender.MALE) == "abc"
        assert mod_0.value.stored.get(Language.FRENCH, Gender.FEMALE) == "lmnop"

        mod_1 = config.patches_gff[0].modifiers.pop(0)
        assert isinstance(mod_1, AddFieldGFF)
        assert isinstance(mod_1, AddFieldGFF)
        assert isinstance(mod_1.value, FieldValueConstant)
        assert isinstance(mod_1.value, FieldValueConstant)
        assert isinstance(mod_1.value.stored, LocalizedStringDelta)
        assert isinstance(mod_1.value.stored, LocalizedStringDelta)
        assert isinstance(mod_1.value.stored.stringref, FieldValueTLKMemory)
        assert isinstance(mod_1.value.stored.stringref, FieldValueTLKMemory)
        assert mod_1.value.stored.stringref.token_id == 8

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
        assert isinstance(mod_0, AddFieldGFF)
        assert isinstance(mod_0, AddFieldGFF)
        assert isinstance(mod_0.value, FieldValueConstant)
        assert isinstance(mod_0.value, FieldValueConstant)
        assert mod_0.path.name == ">>##INDEXINLIST##<<"
        assert mod_0.label == "SomeStruct"
        assert mod_0.value.stored.struct_id == 321

        mod_1 = mod_0.modifiers.pop(0)
        assert isinstance(mod_1, AddFieldGFF)
        assert isinstance(mod_1, AddFieldGFF)
        assert isinstance(mod_1.value, FieldValueConstant)
        assert isinstance(mod_1.value, FieldValueConstant)
        assert mod_1.path.name == "SomeStruct"
        assert mod_1.label == "InsideStruct"
        assert mod_1.value.stored == 123

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
        assert isinstance(mod_0, AddFieldGFF)
        assert isinstance(mod_0, AddFieldGFF)
        assert isinstance(mod_0.value, FieldValueConstant)
        assert isinstance(mod_0.value, FieldValueConstant)
        assert not mod_0.path.name
        assert mod_0.label == "SomeList"

        mod_1 = mod_0.modifiers.pop(0)
        assert isinstance(mod_1, AddStructToListGFF)
        assert isinstance(mod_1, AddStructToListGFF)
        assert isinstance(mod_1.value, FieldValueConstant)
        assert isinstance(mod_1.value, FieldValueConstant)
        assert isinstance(mod_1.value.value(None, GFFFieldType.Struct), GFFStruct)  # type: ignore[arg-type, reportGeneralTypeIssues]
        assert isinstance(mod_1.value.stored, GFFStruct)
        assert mod_1.value.stored.struct_id == 111
        assert mod_1.index_to_token == 5

    def _setupIniAndConfig(self, ini_text: str) -> PatcherConfig:
        ini = ConfigParser(delimiters="=", allow_no_value=True, strict=False, interpolation=None, inline_comment_prefixes=(";", "#"))
        ini.optionxform = lambda optionstr: optionstr
        ini.read_string(ini_text)
        result = PatcherConfig()
        ConfigReader(ini, self.temp_dir, tslpatchdata_path=self.mod_path).load(result)
        return result

    # endregion


if __name__ == "__main__":
    unittest.main()
