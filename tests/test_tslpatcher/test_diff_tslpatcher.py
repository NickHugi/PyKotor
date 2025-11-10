from __future__ import annotations

import os
import pathlib
import shutil
import sys
import tempfile
import unittest

import json
import textwrap
from configparser import ConfigParser
from pathlib import Path
from typing import TYPE_CHECKING, Callable, cast


THIS_SCRIPT_PATH = pathlib.Path(__file__).resolve()
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[3].joinpath("Libraries", "PyKotor", "src")
UTILITY_PATH = THIS_SCRIPT_PATH.parents[3].joinpath("Libraries", "Utility", "src")
KOTORDIFF_PATH = THIS_SCRIPT_PATH.parents[3].joinpath("Tools", "KotorDiff", "src")


def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)
if KOTORDIFF_PATH.joinpath("kotordiff").exists():
    add_sys_path(KOTORDIFF_PATH)


from pykotor.resource.formats.tlk.tlk_data import TLKEntry
from pykotor.common.language import LocalizedString, Gender, Language
from pykotor.common.misc import Game, ResRef
from pykotor.resource.formats.gff.gff_auto import bytes_gff, read_gff, write_gff
from pykotor.resource.formats.gff.gff_data import GFF, GFFContent, GFFFieldType, GFFList, GFFStruct
from pykotor.resource.formats.ssf import SSF, SSFSound, bytes_ssf
from pykotor.resource.formats.ssf.ssf_auto import write_ssf, read_ssf
from pykotor.resource.formats.tlk import TLK, write_tlk, read_tlk, bytes_tlk
from pykotor.resource.formats.twoda.twoda_auto import bytes_2da, read_2da, write_2da
from pykotor.resource.formats.twoda.twoda_data import TwoDA
from pykotor.resource.type import ResourceType
from pykotor.tslpatcher.config import PatcherConfig
from pykotor.tslpatcher.logger import PatchLogger
from pykotor.tslpatcher.memory import PatcherMemory
from pykotor.tslpatcher.mods.tlk import ModificationsTLK
from pykotor.tslpatcher.mods.tlk import ModifyTLK
from pykotor.tslpatcher.mods.twoda import (
    AddColumn2DA,
    AddRow2DA,
    ChangeRow2DA,
    CopyRow2DA,
    RowValue2DAMemory,
    RowValueConstant,
    RowValueHigh,
    RowValueRowCell,
    RowValueRowIndex,
    RowValueRowLabel,
    RowValueTLKMemory,
    Target,
    TargetType,
)
from pykotor.tslpatcher.reader import ConfigReader
from pykotor.tslpatcher.mods.gff import (
    AddFieldGFF,
    FieldValue2DAMemory,
    FieldValueConstant,
    LocalizedStringDelta,
)
from utility.common.geometry import Vector3, Vector4
from kotordiff.app import KotorDiffConfig, run_application  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.tslpatcher.mods.twoda import CopyRow2DA


# TODO(th3w1zard1): Make a decorator for test cases that use the _setupIniAndConfig method.
class TestTSLPatcherFromDiff(unittest.TestCase):
    def _generate_ini_from_diff(
        self,
        vanilla_files: dict[str, tuple[str, ResourceType]],
        modded_files: dict[str, tuple[str, ResourceType]],
    ) -> str:
        """Helper to generate INI from diff of two file sets.
        
        Args:
            vanilla_files: Dict of filename -> (content_string, plaintext_format)
            modded_files: Dict of filename -> (content_string, plaintext_format)
        
        Returns:
            Generated INI content as string
        """
        vanilla_dir = Path(self.temp_dir) / "vanilla"
        modded_dir = Path(self.temp_dir) / "modded"
        vanilla_dir.mkdir(exist_ok=True)
        modded_dir.mkdir(exist_ok=True)
        
        # Write vanilla files
        for filename, (content, plaintext_format) in vanilla_files.items():
            if filename.endswith(".2da"):
                obj = read_2da(content.encode(), file_format=plaintext_format)
                write_2da(obj, vanilla_dir / filename, ResourceType.TwoDA)
            elif filename.endswith(".gff") or any(filename.endswith(f".{ext}") for ext in GFFContent.get_extensions()):
                obj = read_gff(content.encode(), file_format=plaintext_format)
                write_gff(obj, vanilla_dir / filename, ResourceType.GFF)
            elif filename.endswith(".tlk"):
                obj = read_tlk(content.encode(), file_format=plaintext_format)
                write_tlk(obj, vanilla_dir / filename, ResourceType.TLK)
            elif filename.endswith(".ssf"):
                obj = read_ssf(content.encode(), file_format=plaintext_format)
                write_ssf(obj, vanilla_dir / filename, ResourceType.SSF)
        
        # Write modded files
        for filename, (content, plaintext_format) in modded_files.items():
            if filename.endswith(".2da"):
                obj = read_2da(content.encode(), file_format=plaintext_format)
                write_2da(obj, modded_dir / filename, ResourceType.TwoDA)
            elif filename.endswith(".gff") or any(filename.endswith(f".{ext}") for ext in GFFContent.get_extensions()):
                obj = read_gff(content.encode(), file_format=plaintext_format)
                write_gff(obj, modded_dir / filename, ResourceType.GFF)
            elif filename.endswith(".tlk"):
                obj = read_tlk(content.encode(), file_format=plaintext_format)
                write_tlk(obj, modded_dir / filename, ResourceType.TLK)
            elif filename.endswith(".ssf"):
                obj = read_ssf(content.encode(), file_format=plaintext_format)
                write_ssf(obj, modded_dir / filename, ResourceType.SSF)
        
        # Run diff
        config_diff = KotorDiffConfig(
            paths=[vanilla_dir, modded_dir],
            tslpatchdata_path=self.tslpatchdata_path,
            ini_filename="changes.ini",
            compare_hashes=True,
            logging_enabled=False,
        )
        run_application(config_diff)
        
        return (self.tslpatchdata_path / "changes.ini").read_text(encoding="utf-8")
    
    def _canonicalize_ini(self, ini_text: str) -> str:
        parser = ConfigParser(
            delimiters=("="),
            allow_no_value=True,
            strict=False,
            interpolation=None,
            inline_comment_prefixes=(";", "#"),
        )
        parser.optionxform = lambda optionstr: optionstr
        parser.read_string(ini_text)
        lines: list[str] = []
        for section in parser.sections():
            lines.append(f"[{section}]")
            for key, value in parser.items(section, raw=True):
                if value is None:
                    lines.append(key)
                elif value == "":
                    lines.append(f"{key}=")
                else:
                    lines.append(f"{key}={value}")
            lines.append("")
        return "\n".join(lines).strip()

    def _assert_generated_ini_equals(self, generated_ini: str, expected_ini: str) -> None:
        self.assertEqual(
            self._canonicalize_ini(expected_ini),
            self._canonicalize_ini(generated_ini),
        )
    
    def _setupIniAndConfig(self, ini_text: str, mod_path: Path | str = "") -> PatcherConfig:
        ini = ConfigParser(delimiters="=", allow_no_value=True, strict=False, interpolation=None, inline_comment_prefixes=(";", "#"))
        ini.optionxform = lambda optionstr: optionstr
        ini.read_string(ini_text)
        result = PatcherConfig()
        actual_mod_path: Path | str = mod_path if mod_path else self.temp_dir
        ConfigReader(ini, actual_mod_path, tslpatchdata_path=self.tslpatchdata_path).load(result)
        return result

    def _setupTLK(self):
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
        shutil.copy(Path("tests/files/complex.tlk").resolve(), self.tslpatchdata_path / "complex.tlk")
        shutil.copy(Path("tests/files/append.tlk").resolve(), self.tslpatchdata_path / "append.tlk")

        # write it to a real file
        write_tlk(
            self.test_tlk_data,
            str(Path(self.tslpatchdata_path, "tlk_test_file.tlk")),
            ResourceType.TLK,
        )
        write_tlk(
            self.modified_tlk_data,
            str(Path(self.tslpatchdata_path, "tlk_modifications_file.tlk")),
            ResourceType.TLK,
        )

    def setUp(self):
        self.temp_dir: str = tempfile.mkdtemp()
        self.tslpatchdata_path: Path = Path(self.temp_dir, "tslpatchdata")
        self.tslpatchdata_path.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        if hasattr(self, "temp_dir"):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_tlk(self, data: dict[int, dict[str, str]]) -> TLK:
        tlk = TLK()
        for v in data.values():
            tlk.add(text=v["text"], sound_resref=v["voiceover"])
        return tlk

    # region Change Row
    def test_change_existing_rowindex(self):
        # Generate INI from diff
        vanilla_2da = TwoDA(["Col1", "Col2", "Col3"])
        vanilla_2da.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        vanilla_2da.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})

        modded_2da = TwoDA(["Col1", "Col2", "Col3"])
        modded_2da.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        modded_2da.add_row("1", {"Col1": "X", "Col2": "e", "Col3": "f"})

        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})

        # INI loading assertions (from reader-style)
        expected_ini = textwrap.dedent(
            """
            [Settings]
            LogLevel=3
            
            [InstallList]
            install_folder0=Override
            
            [install_folder0]
            File0=test.2da
            
            [2DAList]
            Table0=test.2da

            [test.2da]
            ChangeRow0=change_row_0

            [change_row_0]
            RowIndex=1
            Col1=X
            """
        ).strip()
        config = self._setupIniAndConfig(expected_ini)
        self.assertEqual(1, len(config.patches_2da))
        self.assertEqual(1, len(config.patches_2da[0].modifiers))
        mod = cast(ChangeRow2DA, config.patches_2da[0].modifiers[0])
        assert isinstance(mod, ChangeRow2DA)
        self.assertIsInstance(mod, ChangeRow2DA)
        self.assertEqual(TargetType.ROW_INDEX, mod.target.target_type)
        self.assertEqual(1, mod.target.value)
        self.assertIn("Col1", mod.cells)
        self.assertIsInstance(mod.cells["Col1"], RowValueConstant)
        self.assertEqual("X", cast(RowValueConstant, mod.cells["Col1"]).string)

        # Apply using loaded INI config to ensure patching also works end-to-end
        memory = PatcherMemory()
        PatchLogger()
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)

        # Original mod-style assertions
        self.assertEqual(["a", "X"], twoda.get_column("Col1"))
        self.assertEqual(["b", "e"], twoda.get_column("Col2"))
        self.assertEqual(["c", "f"], twoda.get_column("Col3"))

        generated_ini = self._generate_ini_from_diff(
            {
                "test.2da": (
                    bytes_2da(vanilla_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
            {
                "test.2da": (
                    bytes_2da(modded_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
        )
        self._assert_generated_ini_equals(generated_ini, expected_ini)

    # endregion

    # region 2DA: Add Column
    def test_2da_addcolumn_basic(self):
        """Test that column will be inserted with correct label and default values."""
        vanilla_2da = TwoDA(["ColA"])
        vanilla_2da.add_row("0", {"ColA": "a"})
        vanilla_2da.add_row("1", {"ColA": "b"})
        vanilla_2da.add_row("2", {"ColA": "c"})

        modded_2da = TwoDA(["ColA", "label", "someint"])
        modded_2da.add_row("0", {"ColA": "a", "label": "", "someint": "0"})
        modded_2da.add_row("1", {"ColA": "b", "label": "", "someint": "0"})
        modded_2da.add_row("2", {"ColA": "c", "label": "", "someint": "0"})

        expected_ini = textwrap.dedent(
            """
            [Settings]
            LogLevel=3

            [InstallList]
            install_folder0=Override

            [install_folder0]
            File0=test.2da

            [2DAList]
            Table0=test.2da

            [test.2da]
            AddColumn0=add_column_0
            AddColumn1=add_column_1

            [add_column_0]
            ColumnLabel=label
            DefaultValue=****

            [add_column_1]
            ColumnLabel=someint
            DefaultValue=0
            """
        ).strip()
        config: PatcherConfig = self._setupIniAndConfig(expected_ini)
        mod_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_0, AddColumn2DA)
        assert isinstance(mod_0, AddColumn2DA)
        self.assertEqual("label", mod_0.header)
        self.assertEqual("", mod_0.default)

        mod_1 = config.patches_2da[0].modifiers[1]
        self.assertIsInstance(mod_1, AddColumn2DA)
        assert isinstance(mod_1, AddColumn2DA)
        self.assertEqual("someint", mod_1.header)
        self.assertEqual("0", mod_1.default)

        # Patch-application extension: apply and verify
        twoda = TwoDA(["ColA"])  # two rows
        twoda.add_row("0", {"ColA": "a"})
        twoda.add_row("1", {"ColA": "b"})
        # Add a third row to avoid IndexError when referencing row 2
        twoda.add_row("2", {"ColA": "c"})
        memory = PatcherMemory()
        mod_0.apply(twoda, memory)
        self.assertEqual(["a", "b", "c"], twoda.get_column("ColA"))
        self.assertEqual(["", "", ""], twoda.get_column("label"))

        mod_1.apply(twoda, memory)
        self.assertEqual(["0", "0", "0"], twoda.get_column("someint"))

        generated_ini = self._generate_ini_from_diff(
            {
                "test.2da": (
                    bytes_2da(vanilla_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
            {
                "test.2da": (
                    bytes_2da(modded_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
        )
        self._assert_generated_ini_equals(generated_ini, expected_ini)

    def test_2da_addcolumn_indexinsert(self):
        """Test that cells will be inserted to the new column at the given index correctly."""
        vanilla_2da = TwoDA(["X"])
        vanilla_2da.add_row("0", {"X": "x0"})
        vanilla_2da.add_row("1", {"X": "x1"})
        vanilla_2da.add_row("2", {"X": "x2"})

        modded_2da = TwoDA(["X", "NewColumn"])
        modded_2da.add_row("0", {"X": "x0", "NewColumn": "abc"})
        modded_2da.add_row("1", {"X": "x1", "NewColumn": "mem4"})
        modded_2da.add_row("2", {"X": "x2", "NewColumn": "77"})

        expected_ini = textwrap.dedent(
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
        ).strip()
        config: PatcherConfig = self._setupIniAndConfig(expected_ini)
        mod_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_0, AddColumn2DA)
        assert isinstance(mod_0, AddColumn2DA)

        # reader assertions
        value = mod_0.index_insert[0]
        self.assertIsInstance(value, RowValueConstant)
        assert isinstance(value, RowValueConstant)
        self.assertEqual("abc", value.string)

        value = mod_0.index_insert[1]
        self.assertIsInstance(value, RowValue2DAMemory)
        assert isinstance(value, RowValue2DAMemory)
        self.assertEqual(4, value.token_id)

        value = mod_0.index_insert[2]
        self.assertIsInstance(value, RowValueTLKMemory)
        assert isinstance(value, RowValueTLKMemory)
        self.assertEqual(5, value.token_id)

        # Patch-application extension: apply and verify
        twoda = TwoDA(["X"])  # three rows
        twoda.add_row("0", {"X": "x0"})
        twoda.add_row("1", {"X": "x1"})
        twoda.add_row("2", {"X": "x2"})
        memory = PatcherMemory()
        memory.memory_2da[4] = "mem4"
        memory.memory_str[5] = 77
        mod_0.apply(twoda, memory)
        self.assertEqual(["abc", "mem4", "77"], twoda.get_column("NewColumn"))

        generated_ini = self._generate_ini_from_diff(
            {
                "test.2da": (
                    bytes_2da(vanilla_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
            {
                "test.2da": (
                    bytes_2da(modded_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
        )
        # Diff-generated INI should have literal values, not memory tokens
        expected_diff_ini = textwrap.dedent(
            """
            [Settings]
            LogLevel=3

            [InstallList]
            install_folder0=Override

            [install_folder0]
            File0=test.2da

            [2DAList]
            Table0=test.2da

            [test.2da]
            AddColumn0=add_column_0

            [add_column_0]
            ColumnLabel=NewColumn
            DefaultValue=****
            I0=abc
            I1=mem4
            I2=77
            """
        ).strip()
        self._assert_generated_ini_equals(generated_ini, expected_diff_ini)

    def test_2da_addcolumn_labelinsert(self):
        """Test inserting values using label identifiers."""
        vanilla_2da = TwoDA(["X"])
        vanilla_2da.add_row("0", {"X": "x0"})
        vanilla_2da.add_row("1", {"X": "x1"})
        vanilla_2da.add_row("2", {"X": "x2"})

        modded_2da = TwoDA(["X", "NewColumn"])
        modded_2da.add_row("0", {"X": "x0", "NewColumn": "abc"})
        modded_2da.add_row("1", {"X": "x1", "NewColumn": "mem4"})
        modded_2da.add_row("2", {"X": "x2", "NewColumn": "77"})

        expected_ini = textwrap.dedent(
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
        ).strip()
        config = self._setupIniAndConfig(expected_ini)

        mod_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_0, AddColumn2DA)
        assert isinstance(mod_0, AddColumn2DA)

        value = mod_0.label_insert["0"]
        self.assertIsInstance(value, RowValueConstant)
        assert isinstance(value, RowValueConstant)
        self.assertEqual("abc", value.string)

        value = mod_0.label_insert["1"]
        self.assertIsInstance(value, RowValue2DAMemory)
        assert isinstance(value, RowValue2DAMemory)
        self.assertEqual(4, value.token_id)

        value = mod_0.label_insert["2"]
        self.assertIsInstance(value, RowValueTLKMemory)
        assert isinstance(value, RowValueTLKMemory)
        self.assertEqual(5, value.token_id)

        # Patch-application extension
        memory = PatcherMemory()
        memory.memory_2da[4] = "mem4"
        memory.memory_str[5] = 77
        twoda = TwoDA(["X"])
        twoda.add_row("0", {"X": "x0"})
        twoda.add_row("1", {"X": "x1"})
        twoda.add_row("2", {"X": "x2"})
        memory = PatcherMemory()
        memory.memory_2da[4] = "mem4"
        memory.memory_str[5] = 77
        mod_0.apply(twoda, memory)
        self.assertEqual(["abc", "mem4", "77"], twoda.get_column("NewColumn"))

        generated_ini = self._generate_ini_from_diff(
            {
                "test.2da": (
                    bytes_2da(vanilla_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
            {
                "test.2da": (
                    bytes_2da(modded_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
        )
        # Diff-generated INI uses index-based notation (I0, I1, etc.), not label-based (L0, L1, etc.)
        expected_diff_ini = textwrap.dedent(
            """
            [Settings]
            LogLevel=3

            [InstallList]
            install_folder0=Override

            [install_folder0]
            File0=test.2da

            [2DAList]
            Table0=test.2da

            [test.2da]
            AddColumn0=add_column_0

            [add_column_0]
            ColumnLabel=NewColumn
            DefaultValue=****
            I0=abc
            I1=mem4
            I2=77
            """
        ).strip()
        self._assert_generated_ini_equals(generated_ini, expected_diff_ini)


    def test_2da_addcolumn_default(self):
        """Test inserting column with explicit default value."""
        vanilla_2da = TwoDA(["Col1", "Col2"])
        vanilla_2da.add_row("0", {"Col1": "a", "Col2": "b"})
        vanilla_2da.add_row("1", {"Col1": "c", "Col2": "d"})

        modded_2da = TwoDA(["Col1", "Col2", "Col3"])
        modded_2da.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "X"})
        modded_2da.add_row("1", {"Col1": "c", "Col2": "d", "Col3": "X"})

        expected_ini = textwrap.dedent(
            """
            [Settings]
            LogLevel=3

            [InstallList]
            install_folder0=Override

            [install_folder0]
            File0=test.2da

            [2DAList]
            Table0=test.2da

            [test.2da]
            AddColumn0=add_column_0

            [add_column_0]
            ColumnLabel=Col3
            DefaultValue=X
            """
        ).strip()
        config = self._setupIniAndConfig(expected_ini)
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})
        config.patches_2da[0].apply(twoda, PatcherMemory(), PatchLogger(), Game.K1)
        self.assertEqual(["X", "X"], twoda.get_column("Col3"))

        generated_ini = self._generate_ini_from_diff(
            {
                "test.2da": (
                    bytes_2da(vanilla_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
            {
                "test.2da": (
                    bytes_2da(modded_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
        )
        self._assert_generated_ini_equals(generated_ini, expected_ini)

    def test_ssf_stored_constant(self):
        """Test that the set sound as constant stringref is registered correctly."""
        vanilla_ssf = SSF()
        modded_ssf = SSF()
        modded_ssf.set_data(SSFSound.BATTLE_CRY_1, 123)
        modded_ssf.set_data(SSFSound.BATTLE_CRY_2, 456)

        expected_ini = textwrap.dedent(
            """
            [Settings]
            LogLevel=3
            
            [InstallList]
            install_folder0=Override
            
            [install_folder0]
            File0=test.ssf
            
            [SSFList]
            File0=test.ssf

            [test.ssf]
            Battlecry 1=123
            Battlecry 2=456
            """
        ).strip()
        config: PatcherConfig = self._setupIniAndConfig(expected_ini)
        ssf = SSF()
        memory = PatcherMemory()
        config.patches_ssf[0].apply(ssf, memory, PatchLogger(), Game.K1)
        self.assertEqual(123, ssf.get(SSFSound.BATTLE_CRY_1))
        self.assertEqual(456, ssf.get(SSFSound.BATTLE_CRY_2))

        generated_ini = self._generate_ini_from_diff(
            {
                "test.ssf": (
                    bytes_ssf(vanilla_ssf, file_format=ResourceType.SSF_XML).decode(),
                    ResourceType.SSF_XML,
                )
            },
            {
                "test.ssf": (
                    bytes_ssf(modded_ssf, file_format=ResourceType.SSF_XML).decode(),
                    ResourceType.SSF_XML,
                )
            },
        )
        self._assert_generated_ini_equals(generated_ini, expected_ini)

    def test_ssf_set(self):
        """Test that each sound is mapped and will register correctly."""
        vanilla_ssf = SSF()
        modded_ssf = SSF()
        for idx, sound in enumerate(SSFSound):
            modded_ssf.set_data(sound, idx + 1)

        expected_ini = textwrap.dedent(
            """
            [Settings]
            LogLevel=3
            
            [InstallList]
            install_folder0=Override
            
            [install_folder0]
            File0=test.ssf
            
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
        ).strip()
        config: PatcherConfig = self._setupIniAndConfig(expected_ini)
        ssf = SSF()
        memory = PatcherMemory()
        config.patches_ssf[0].apply(ssf, memory, PatchLogger(), Game.K1)
        self.assertEqual(1, ssf.get(SSFSound.BATTLE_CRY_1))
        self.assertEqual(2, ssf.get(SSFSound.BATTLE_CRY_2))
        self.assertEqual(3, ssf.get(SSFSound.BATTLE_CRY_3))
        self.assertEqual(4, ssf.get(SSFSound.BATTLE_CRY_4))
        self.assertEqual(5, ssf.get(SSFSound.BATTLE_CRY_5))
        self.assertEqual(6, ssf.get(SSFSound.BATTLE_CRY_6))
        self.assertEqual(7, ssf.get(SSFSound.SELECT_1))
        self.assertEqual(8, ssf.get(SSFSound.SELECT_2))
        self.assertEqual(9, ssf.get(SSFSound.SELECT_3))
        self.assertEqual(10, ssf.get(SSFSound.ATTACK_GRUNT_1))
        self.assertEqual(11, ssf.get(SSFSound.ATTACK_GRUNT_2))
        self.assertEqual(12, ssf.get(SSFSound.ATTACK_GRUNT_3))
        self.assertEqual(13, ssf.get(SSFSound.PAIN_GRUNT_1))
        self.assertEqual(14, ssf.get(SSFSound.PAIN_GRUNT_2))
        self.assertEqual(15, ssf.get(SSFSound.LOW_HEALTH))
        self.assertEqual(16, ssf.get(SSFSound.DEAD))
        self.assertEqual(17, ssf.get(SSFSound.CRITICAL_HIT))
        self.assertEqual(18, ssf.get(SSFSound.TARGET_IMMUNE))
        self.assertEqual(19, ssf.get(SSFSound.LAY_MINE))
        self.assertEqual(20, ssf.get(SSFSound.DISARM_MINE))
        self.assertEqual(21, ssf.get(SSFSound.BEGIN_STEALTH))
        self.assertEqual(22, ssf.get(SSFSound.BEGIN_SEARCH))
        self.assertEqual(23, ssf.get(SSFSound.BEGIN_UNLOCK))
        self.assertEqual(24, ssf.get(SSFSound.UNLOCK_FAILED))
        self.assertEqual(25, ssf.get(SSFSound.UNLOCK_SUCCESS))
        self.assertEqual(26, ssf.get(SSFSound.SEPARATED_FROM_PARTY))
        self.assertEqual(27, ssf.get(SSFSound.REJOINED_PARTY))
        self.assertEqual(28, ssf.get(SSFSound.POISONED))

        generated_ini = self._generate_ini_from_diff(
            {
                "test.ssf": (
                    bytes_ssf(vanilla_ssf, file_format=ResourceType.SSF_XML).decode(),
                    ResourceType.SSF_XML,
                )
            },
            {
                "test.ssf": (
                    bytes_ssf(modded_ssf, file_format=ResourceType.SSF_XML).decode(),
                    ResourceType.SSF_XML,
                )
            },
        )
        self._assert_generated_ini_equals(generated_ini, expected_ini)

    # endregion


if __name__ == "__main__":
    unittest.main()
