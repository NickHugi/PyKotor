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
from typing import TYPE_CHECKING, Callable, cast


THIS_SCRIPT_PATH = pathlib.Path(__file__).resolve()
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[2].joinpath("Libraries", "PyKotor", "src")
UTILITY_PATH = THIS_SCRIPT_PATH.parents[2].joinpath("Libraries", "Utility", "src")
KOTORDIFF_PATH = THIS_SCRIPT_PATH.parents[2].joinpath("Tools", "KotorDiff", "src")


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
from pykotor.common.geometry import Vector3, Vector4
from pykotor.resource.formats.gff.gff_auto import bytes_gff, read_gff, write_gff
from pykotor.resource.formats.gff.gff_data import GFF, GFFContent, GFFFieldType, GFFList, GFFStruct
from pykotor.common.geometry import Vector3, Vector4
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
from pathlib import Path
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

    def test_2da_addrow_use_max_rowlabel(self):
        """Test automatic row label assignment when adding rows."""
        vanilla_2da = TwoDA(["Col1"])
        vanilla_2da.add_row("0", {"Col1": ""})

        modded_2da = TwoDA(["Col1"])
        modded_2da.add_row("0", {"Col1": ""})
        modded_2da.add_row("1", {"Col1": ""})
        modded_2da.add_row("2", {"Col1": ""})

        expected_ini = textwrap.dedent(
            """
            [2DAList]
            Table0=test_maxlabel.2da

            [test_maxlabel.2da]
            AddRow0=add_row_0
            AddRow1=add_row_1
            """
        ).strip()
        config = self._setupIniAndConfig(expected_ini)
        twoda = TwoDA(["Col1"])
        twoda.add_row("0", {"Col1": ""})
        config.patches_2da[0].apply(twoda, PatcherMemory(), PatchLogger(), Game.K1)
        self.assertEqual(["0", "1", "2"], [twoda.get_label(i) for i in range(3)])

        generated_ini = self._generate_ini_from_diff(
            {
                "test_maxlabel.2da": (
                    bytes_2da(vanilla_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
            {
                "test_maxlabel.2da": (
                    bytes_2da(modded_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
        )
        self._assert_generated_ini_equals(generated_ini, expected_ini)

    def test_2da_addrow_rowlabel_constant(self):
        """Test explicit row label usage."""
        vanilla_2da = TwoDA(["Col1"])
        modded_2da = TwoDA(["Col1"])
        modded_2da.add_row("r1", {"Col1": ""})

        expected_ini = textwrap.dedent(
            """
            [2DAList]
            Table0=test_constant.2da

            [test_constant.2da]
            AddRow0=add_row_0

            [add_row_0]
            RowLabel=r1
            """
        ).strip()
        config = self._setupIniAndConfig(expected_ini)
        twoda = TwoDA(["Col1"])
        config.patches_2da[0].apply(twoda, PatcherMemory(), PatchLogger(), Game.K1)
        self.assertEqual("r1", twoda.get_label(0))

        generated_ini = self._generate_ini_from_diff(
            {
                "test_constant.2da": (
                    bytes_2da(vanilla_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
            {
                "test_constant.2da": (
                    bytes_2da(modded_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
        )
        self._assert_generated_ini_equals(generated_ini, expected_ini)

    def test_2da_addrow_exclusive_behaviour(self):
        """Test exclusive column behaviour for add row."""
        vanilla_2da = TwoDA(["Col1", "Col2", "Col3"])
        vanilla_2da.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        vanilla_2da.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})

        # Unique value should add a new row
        modded_unique = TwoDA(["Col1", "Col2", "Col3"])
        modded_unique.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        modded_unique.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})
        modded_unique.add_row("2", {"Col1": "g", "Col2": "h", "Col3": "i"})

        expected_unique = textwrap.dedent(
            """
            [2DAList]
            Table0=test_unique.2da

            [test_unique.2da]
            AddRow0=add_row_0

            [add_row_0]
            ExclusiveColumn=Col1
            RowLabel=2
            Col1=g
            Col2=h
            Col3=i
            """
        ).strip()
        config_unique = self._setupIniAndConfig(expected_unique)
        twoda_unique = TwoDA(["Col1", "Col2", "Col3"])
        twoda_unique.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        twoda_unique.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})
        config_unique.patches_2da[0].apply(twoda_unique, PatcherMemory(), PatchLogger(), Game.K1)
        self.assertEqual(3, twoda_unique.get_height())

        generated_unique = self._generate_ini_from_diff(
            {
                "test_unique.2da": (
                    bytes_2da(vanilla_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
            {
                "test_unique.2da": (
                    bytes_2da(modded_unique, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
        )
        self._assert_generated_ini_equals(generated_unique, expected_unique)

        # Duplicate value should update existing row
        modded_duplicate = TwoDA(["Col1", "Col2", "Col3"])
        modded_duplicate.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        modded_duplicate.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})
        modded_duplicate.add_row("2", {"Col1": "g", "Col2": "X", "Col3": "Y"})

        expected_duplicate = textwrap.dedent(
            """
            [2DAList]
            Table0=test_duplicate.2da

            [test_duplicate.2da]
            AddRow0=add_row_0

            [add_row_0]
            ExclusiveColumn=Col1
            RowLabel=3
            Col1=g
            Col2=X
            Col3=Y
            """
        ).strip()
        config_duplicate = self._setupIniAndConfig(expected_duplicate)
        twoda_duplicate = TwoDA(["Col1", "Col2", "Col3"])
        twoda_duplicate.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        twoda_duplicate.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})
        twoda_duplicate.add_row("2", {"Col1": "g", "Col2": "h", "Col3": "i"})
        config_duplicate.patches_2da[0].apply(twoda_duplicate, PatcherMemory(), PatchLogger(), Game.K1)
        self.assertEqual(["a", "d", "g"], twoda_duplicate.get_column("Col1"))
        self.assertEqual(["b", "e", "X"], twoda_duplicate.get_column("Col2"))

        generated_duplicate = self._generate_ini_from_diff(
            {
                "test_duplicate.2da": (
                    bytes_2da(vanilla_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
            {
                "test_duplicate.2da": (
                    bytes_2da(modded_duplicate, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
        )
        self._assert_generated_ini_equals(generated_duplicate, expected_duplicate)

        # No exclusive column configured
        modded_none = TwoDA(["Col1", "Col2", "Col3"])
        modded_none.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        modded_none.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})
        modded_none.add_row("2", {"Col1": "g", "Col2": "h", "Col3": "i"})
        modded_none.add_row("3", {"Col1": "j", "Col2": "k", "Col3": "l"})

        expected_none = textwrap.dedent(
            """
            [2DAList]
            Table0=test_none.2da

            [test_none.2da]
            AddRow0=add_row_0
            AddRow1=add_row_1

            [add_row_0]
            RowLabel=2
            Col1=g
            Col2=h
            Col3=i

            [add_row_1]
            RowLabel=3
            Col1=j
            Col2=k
            Col3=l
            """
        ).strip()
        config_none = self._setupIniAndConfig(expected_none)
        twoda_none = TwoDA(["Col1", "Col2", "Col3"])
        twoda_none.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        twoda_none.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})
        config_none.patches_2da[0].apply(twoda_none, PatcherMemory(), PatchLogger(), Game.K1)
        self.assertEqual(4, twoda_none.get_height())

        generated_none = self._generate_ini_from_diff(
            {
                "test_none.2da": (
                    bytes_2da(vanilla_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
            {
                "test_none.2da": (
                    bytes_2da(modded_none, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
        )
        self._assert_generated_ini_equals(generated_none, expected_none)

    def test_2da_addrow_assignment_helpers(self):
        """Test helper tokens for add row operations."""
        vanilla_2da = TwoDA(["Col1"])

        # high()
        expected_high = textwrap.dedent(
            """
            [2DAList]
            Table0=test_high.2da

            [test_high.2da]
            AddRow0=add_row_0

            [add_row_0]
            RowLabel=2
            Col1=high()
            """
        ).strip()
        config_high = self._setupIniAndConfig(expected_high)
        twoda_high = TwoDA(["Col1", "Col2", "Col3"])
        twoda_high.add_row("0", {"Col1": "1", "Col2": "b", "Col3": "c"})
        twoda_high.add_row("1", {"Col1": "2", "Col2": "e", "Col3": "f"})
        config_high.patches_2da[0].apply(twoda_high, PatcherMemory(), PatchLogger(), Game.K1)
        self.assertEqual(["1", "2", "3"], twoda_high.get_column("Col1"))

        modded_high = TwoDA(["Col1", "Col2", "Col3"])
        modded_high.add_row("0", {"Col1": "1", "Col2": "b", "Col3": "c"})
        modded_high.add_row("1", {"Col1": "2", "Col2": "e", "Col3": "f"})
        modded_high.add_row("2", {"Col1": "3", "Col2": "", "Col3": ""})
        generated_high = self._generate_ini_from_diff(
            {
                "test_high.2da": (
                    bytes_2da(vanilla_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
            {
                "test_high.2da": (
                    bytes_2da(modded_high, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
        )
        self._assert_generated_ini_equals(generated_high, expected_high)

        # TLK memory
        expected_tlk = textwrap.dedent(
            """
            [2DAList]
            Table0=test_tlk.2da

            [test_tlk.2da]
            AddRow0=add_row_0
            AddRow1=add_row_1

            [add_row_0]
            RowLabel=0
            Col1=StrRef0

            [add_row_1]
            RowLabel=1
            Col1=StrRef1
            """
        ).strip()
        config_tlk = self._setupIniAndConfig(expected_tlk)
        memory = PatcherMemory()
        memory.memory_str[0] = 5
        memory.memory_str[1] = 6
        twoda_tlk = TwoDA(["Col1"])
        config_tlk.patches_2da[0].apply(twoda_tlk, memory, PatchLogger(), Game.K1)
        self.assertEqual(["5", "6"], twoda_tlk.get_column("Col1"))

        modded_tlk = TwoDA(["Col1"])
        modded_tlk.add_row("0", {"Col1": "5"})
        modded_tlk.add_row("1", {"Col1": "6"})
        generated_tlk = self._generate_ini_from_diff(
            {
                "test_tlk.2da": (
                    bytes_2da(vanilla_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
            {
                "test_tlk.2da": (
                    bytes_2da(modded_tlk, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
        )
        self._assert_generated_ini_equals(generated_tlk, expected_tlk)

        # 2DA memory
        expected_2da = textwrap.dedent(
            """
            [2DAList]
            Table0=test_memory.2da

            [test_memory.2da]
            AddRow0=add_row_0
            AddRow1=add_row_1

            [add_row_0]
            RowLabel=0
            Col1=2DAMEMORY0

            [add_row_1]
            RowLabel=1
            Col1=2DAMEMORY1
            """
        ).strip()
        config_2da = self._setupIniAndConfig(expected_2da)
        memory = PatcherMemory()
        memory.memory_2da[0] = "5"
        memory.memory_2da[1] = "6"
        twoda_2da = TwoDA(["Col1"])
        config_2da.patches_2da[0].apply(twoda_2da, memory, PatchLogger(), Game.K1)
        self.assertEqual(["5", "6"], twoda_2da.get_column("Col1"))

        modded_2da = TwoDA(["Col1"])
        modded_2da.add_row("0", {"Col1": "5"})
        modded_2da.add_row("1", {"Col1": "6"})
        generated_2da = self._generate_ini_from_diff(
            {
                "test_memory.2da": (
                    bytes_2da(vanilla_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
            {
                "test_memory.2da": (
                    bytes_2da(modded_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
        )
        self._assert_generated_ini_equals(generated_2da, expected_2da)

    def test_2da_addrow_store_rowindex(self):
        """Test storing row indices after add row operations."""
        vanilla_2da = TwoDA(["Col1"])
        vanilla_2da.add_row("0", {"Col1": "X"})

        modded_2da = TwoDA(["Col1"])
        modded_2da.add_row("0", {"Col1": "X"})
        modded_2da.add_row("1", {"Col1": "Y"})

        expected_ini = textwrap.dedent(
            """
            [2DAList]
            Table0=test_store.2da

            [test_store.2da]
            AddRow0=add_row_0
            AddRow1=add_row_1

            [add_row_0]
            ExclusiveColumn=Col1
            RowLabel=1
            Col1=X
            2DAMEMORY5=RowIndex

            [add_row_1]
            RowLabel=2
            Col1=Y
            2DAMEMORY6=RowIndex
            """
        ).strip()
        config = self._setupIniAndConfig(expected_ini)
        twoda = TwoDA(["Col1"])
        twoda.add_row("0", {"Col1": "X"})
        memory = PatcherMemory()
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)
        self.assertEqual("0", memory.memory_2da[5])
        self.assertEqual("1", memory.memory_2da[6])

        generated_ini = self._generate_ini_from_diff(
            {
                "test_store.2da": (
                    bytes_2da(vanilla_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
            {
                "test_store.2da": (
                    bytes_2da(modded_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
        )
        self._assert_generated_ini_equals(generated_ini, expected_ini)

    def test_change_existing_rowlabel(self):
        # Generate INI from diff
        vanilla_2da = TwoDA(["Col1", "Col2", "Col3"])
        vanilla_2da.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        vanilla_2da.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})

        modded_2da = TwoDA(["Col1", "Col2", "Col3"])
        modded_2da.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        modded_2da.add_row("1", {"Col1": "X", "Col2": "e", "Col3": "f"})

        memory = PatcherMemory()
        logger = PatchLogger()

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
            RowLabel=1
            Col1=X
            """
        ).strip()
        config = self._setupIniAndConfig(expected_ini)
        self.assertEqual(1, len(config.patches_2da))
        self.assertEqual(1, len(config.patches_2da[0].modifiers))
        mod = cast(ChangeRow2DA, config.patches_2da[0].modifiers[0])
        self.assertEqual(TargetType.ROW_LABEL, mod.target.target_type)
        self.assertEqual("1", mod.target.value)
        self.assertIn("Col1", mod.cells)
        self.assertIsInstance(mod.cells["Col1"], RowValueConstant)
        self.assertEqual("X", cast(RowValueConstant, mod.cells["Col1"]).string)

        # Apply using loaded INI config to ensure patching also works end-to-end
        config.patches_2da[0].apply(vanilla_2da, memory, logger, Game.K1)

        self.assertEqual(["a", "X"], vanilla_2da.get_column("Col1"))
        self.assertEqual(["b", "e"], vanilla_2da.get_column("Col2"))
        self.assertEqual(["c", "f"], vanilla_2da.get_column("Col3"))

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

    # region GFF Add/Modify

    def test_gff_add_inside_struct(self):
        """Test that the add field modifiers are registered correctly."""
        # Generate INI from diff
        vanilla_gff = GFF()
        modded_gff = GFF()
        some_struct = modded_gff.root.set_struct("SomeStruct", GFFStruct(321))
        some_struct.set_uint8("InsideStruct", 123)

        vanilla_gff_xml = bytes_gff(vanilla_gff, file_format=ResourceType.GFF_XML).decode()
        modded_gff_xml = bytes_gff(modded_gff, file_format=ResourceType.GFF_XML).decode()

        expected_ini = textwrap.dedent(
            """
            [Settings]
            LogLevel=3
            
            [InstallList]
            install_folder0=Override
            
            [install_folder0]
            File0=test.gff
            
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=add_struct
            AddField1=add_insidestruct

            [add_struct]
            FieldType=Struct
            Path=
            Label=SomeStruct
            TypeId=321

            [add_insidestruct]
            FieldType=Byte
            Path=SomeStruct
            Label=InsideStruct
            Value=123
            """
        ).strip()
        config: PatcherConfig = self._setupIniAndConfig(expected_ini)
        mod_0 = config.patches_gff[0].modifiers[0]
        self.assertIsInstance(mod_0, AddFieldGFF)
        assert isinstance(mod_0, AddFieldGFF)
        self.assertIsInstance(mod_0.value, FieldValueConstant)
        assert isinstance(mod_0.value, FieldValueConstant)
        self.assertEqual(mod_0.path.name, ">>##INDEXINLIST##<<")
        self.assertEqual("SomeStruct", mod_0.label)
        self.assertEqual(321, mod_0.value.stored.struct_id)

        mod_1 = config.patches_gff[0].modifiers[1]
        self.assertIsInstance(mod_1, AddFieldGFF)
        assert isinstance(mod_1, AddFieldGFF)
        self.assertIsInstance(mod_1.value, FieldValueConstant)
        assert isinstance(mod_1.value, FieldValueConstant)
        self.assertEqual(mod_1.path.name, "SomeStruct")
        self.assertEqual("InsideStruct", mod_1.label)
        self.assertEqual(123, mod_1.value.stored)

        # Apply patch end-to-end
        gff = GFF()
        patch_resource: Callable[[bytes, PatcherMemory, PatchLogger, Game], bytes] = config.patches_gff[0].patch_resource
        gff_bytes: bytes = bytes_gff(gff)
        patched_bytes: bytes = patch_resource(gff_bytes, PatcherMemory(), PatchLogger(), Game.K1)
        patched: GFF = read_gff(patched_bytes)
        some_struct: GFFStruct | None = patched.root.get_struct("SomeStruct")
        self.assertIsNotNone(some_struct)
        inside_struct_value: int | None = some_struct.get_uint8("InsideStruct") if some_struct is not None else None
        self.assertEqual(123, inside_struct_value)

        generated_ini = self._generate_ini_from_diff(
            {"test.gff": (vanilla_gff_xml, ResourceType.GFF_XML)},
            {"test.gff": (modded_gff_xml, ResourceType.GFF_XML)},
        )
        self._assert_generated_ini_equals(generated_ini, expected_ini)

    def test_gff_add_field_locstring(self):
        """Adds a localized string field to a GFF using a 2DA memory reference (ini first, then apply)."""
        # Generate INI from diff
        vanilla_gff = GFF()
        vanilla_gff.root.set_locstring("Field1", LocalizedString(0))
        modded_gff = GFF()
        modded_gff.root.set_locstring("Field1", LocalizedString(123))

        vanilla_gff_xml = bytes_gff(vanilla_gff, file_format=ResourceType.GFF_XML).decode()
        modded_gff_xml = bytes_gff(modded_gff, file_format=ResourceType.GFF_XML).decode()

        expected_ini = textwrap.dedent(
            """
            [Settings]
            LogLevel=3
            
            [InstallList]
            install_folder0=Override
            
            [install_folder0]
            File0=test.gff
            
            [GFFList]
            File0=test.gff
            
            [test.gff]
            AddField0=add_loc
            
            [add_loc]
            FieldType=ExoLocString
            Path=
            Label=Field1
            StrRef=2DAMEMORY5
            """
        ).strip()
        config: PatcherConfig = self._setupIniAndConfig(expected_ini)

        # Reader-style assertions
        add_mod = config.patches_gff[0].modifiers[0]
        assert isinstance(add_mod, AddFieldGFF)
        self.assertIsInstance(add_mod, AddFieldGFF)
        assert isinstance(add_mod, AddFieldGFF)
        self.assertIsInstance(add_mod.value, FieldValueConstant)
        assert isinstance(add_mod.value, FieldValueConstant)
        self.assertIsInstance(add_mod.value.stored, LocalizedStringDelta)
        assert isinstance(add_mod.value.stored, LocalizedStringDelta)

        # Apply patch end-to-end mirroring test_mods.py semantics
        gff = GFF()
        gff.root.set_locstring("Field1", LocalizedString(0))
        memory = PatcherMemory()
        memory.memory_2da[5] = "123"
        patched = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))
        self.assertEqual(123, patched.root.get_locstring("Field1").stringref)

        generated_ini = self._generate_ini_from_diff(
            {"test.gff": (vanilla_gff_xml, ResourceType.GFF_XML)},
            {"test.gff": (modded_gff_xml, ResourceType.GFF_XML)},
        )
        self._assert_generated_ini_equals(generated_ini, expected_ini)

    def test_gff_modifier_path_shorter_than_self_path(self):
        """Modifier path is shorter than self.path — overlay keeps deeper context, append loses it."""
        # Generate INI from diff
        vanilla_gff = GFF()
        modded_gff = GFF()
        root_struct = modded_gff.root.set_struct("Root", GFFStruct(0))
        parent_struct = root_struct.set_struct("ParentStruct", GFFStruct(100))
        parent_struct.set_uint8("ChildField", 42)

        vanilla_gff_xml = bytes_gff(vanilla_gff, file_format=ResourceType.GFF_XML).decode()
        modded_gff_xml = bytes_gff(modded_gff, file_format=ResourceType.GFF_XML).decode()

        expected_ini = textwrap.dedent(
            """
            [Settings]
            LogLevel=3
            
            [InstallList]
            install_folder0=Override
            
            [install_folder0]
            File0=test.gff

            [GFFList]
            File0=test.gff

            [test.gff]
            !ReplaceFile=0
            AddField0=add_Root

            [add_Root]
            FieldType=Struct
            Label=ParentStruct
            Path=Root/ParentStruct
            TypeId=100
            AddField0=add_child

            [add_child]
            FieldType=Byte
            Path=ChildField
            Label=ChildField
            Value=42
            """
        ).strip()

        config: PatcherConfig = self._setupIniAndConfig(expected_ini)

        mod_0 = config.patches_gff[0].modifiers[0]
        self.assertIsInstance(mod_0, AddFieldGFF)
        assert isinstance(mod_0, AddFieldGFF)
        mod_1 = mod_0.modifiers[0]
        self.assertIsInstance(mod_1, AddFieldGFF)
        assert isinstance(mod_1, AddFieldGFF)
        # Under overlay logic, path should be Root/ParentStruct/ChildField
        self.assertEqual(mod_1.path.parts[-1], "ChildField")

        generated_ini = self._generate_ini_from_diff(
            {"test.gff": (vanilla_gff_xml, ResourceType.GFF_XML)},
            {"test.gff": (modded_gff_xml, ResourceType.GFF_XML)},
        )
        self._assert_generated_ini_equals(generated_ini, expected_ini)

    def test_gff_modifier_path_longer_than_self_path(self):
        """Modifier path is longer than self.path — overlay appends extra parts naturally."""
        # Generate INI from diff
        vanilla_gff = GFF()
        modded_gff = GFF()
        root_struct = modded_gff.root.set_struct("Root", GFFStruct(200))
        child_struct = root_struct.set_struct("ChildStruct", GFFStruct(0))
        child_struct.set_uint8("GrandChildField", 99)

        vanilla_gff_xml = bytes_gff(vanilla_gff, file_format=ResourceType.GFF_XML).decode()
        modded_gff_xml = bytes_gff(modded_gff, file_format=ResourceType.GFF_XML).decode()

        expected_ini = textwrap.dedent(
            """
            [Settings]
            LogLevel=3
            
            [InstallList]
            install_folder0=Override
            
            [install_folder0]
            File0=test.gff
            
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=add_struct

            [add_struct]
            FieldType=Struct
            Path=Root
            Label=Root
            TypeId=200
            AddField0=add_grandchild

            [add_grandchild]
            FieldType=Byte
            Path=ChildStruct/GrandChildField
            Label=GrandChildField
            Value=99
            """
        ).strip()

        config: PatcherConfig = self._setupIniAndConfig(expected_ini)

        mod_0 = config.patches_gff[0].modifiers[0]
        self.assertIsInstance(mod_0, AddFieldGFF)
        assert isinstance(mod_0, AddFieldGFF)
        mod_1 = mod_0.modifiers[0]
        self.assertIsInstance(mod_1, AddFieldGFF)
        assert isinstance(mod_1, AddFieldGFF)
        # Overlay and append both append extra parts, but base differences may show up if base path differs
        self.assertEqual(mod_1.path.parts[-1], "GrandChildField")

        generated_ini = self._generate_ini_from_diff(
            {"test.gff": (vanilla_gff_xml, ResourceType.GFF_XML)},
            {"test.gff": (modded_gff_xml, ResourceType.GFF_XML)},
        )
        self._assert_generated_ini_equals(generated_ini, expected_ini)

    def test_gff_modifier_path_partial_absolute(self):
        """Modifier path partially overlaps self.path — overlay preserves alignment, append may duplicate segments."""
        # Generate INI from diff
        vanilla_gff = GFF()
        modded_gff = GFF()
        root_struct = modded_gff.root.set_struct("Root", GFFStruct(0))
        struct_a = root_struct.set_struct("StructA", GFFStruct(300))
        struct_a.set_uint8("InnerField", 7)

        vanilla_gff_xml = bytes_gff(vanilla_gff, file_format=ResourceType.GFF_XML).decode()
        modded_gff_xml = bytes_gff(modded_gff, file_format=ResourceType.GFF_XML).decode()

        expected_ini = textwrap.dedent(
            """
            [Settings]
            LogLevel=3
            
            [InstallList]
            install_folder0=Override
            
            [install_folder0]
            File0=test.gff
            
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=add_struct

            [add_struct]
            FieldType=Struct
            Path=Root/StructA
            Label=StructA
            TypeId=300
            AddField0=add_field_absolute

            [add_field_absolute]
            FieldType=Byte
            Path=StructA/InnerField
            Label=InnerField
            Value=7
            """
        ).strip()

        config: PatcherConfig = self._setupIniAndConfig(expected_ini)

        mod_0 = config.patches_gff[0].modifiers[0]
        self.assertIsInstance(mod_0, AddFieldGFF)
        assert isinstance(mod_0, AddFieldGFF)
        mod_1 = mod_0.modifiers[0]
        self.assertIsInstance(mod_1, AddFieldGFF)
        assert isinstance(mod_1, AddFieldGFF)
        # Overlay: Root/StructA/InnerField
        # Append: Root/StructA/StructA/InnerField (duplicate StructA)
        self.assertEqual(mod_1.path.parts.count("StructA"), 1)

        generated_ini = self._generate_ini_from_diff(
            {"test.gff": (vanilla_gff_xml, ResourceType.GFF_XML)},
            {"test.gff": (modded_gff_xml, ResourceType.GFF_XML)},
        )
        self._assert_generated_ini_equals(generated_ini, expected_ini)

    def test_gff_add_field_with_sentinel_at_start(self):
        """Ensures sentinel at start of modifier path is handled correctly."""
        # Generate INI from diff
        vanilla_gff = GFF()
        modded_gff = GFF()
        root_struct = modded_gff.root.set_struct("Root", GFFStruct(0))
        temp_struct = root_struct.set_struct("TempStruct", GFFStruct(400))
        temp_struct.set_uint8("InnerField", 55)

        vanilla_gff_xml = bytes_gff(vanilla_gff, file_format=ResourceType.GFF_XML).decode()
        modded_gff_xml = bytes_gff(modded_gff, file_format=ResourceType.GFF_XML).decode()

        expected_ini = textwrap.dedent(
            """
            [Settings]
            LogLevel=3
            
            [InstallList]
            install_folder0=Override
            
            [install_folder0]
            File0=test.gff
            
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=add_struct

            [add_struct]
            FieldType=Struct
            Path=Root/>>##INDEXINLIST##<<
            Label=TempStruct
            TypeId=400
            AddField0=add_inside

            [add_inside]
            FieldType=Byte
            Path=>>##INDEXINLIST##<</InnerField
            Label=InnerField
            Value=55
            """
        ).strip()

        config: PatcherConfig = self._setupIniAndConfig(expected_ini)

        mod_0 = config.patches_gff[0].modifiers[0]
        self.assertIsInstance(mod_0, AddFieldGFF)
        assert isinstance(mod_0, AddFieldGFF)
        mod_1 = mod_0.modifiers[0]
        self.assertIsInstance(mod_1, AddFieldGFF)
        assert isinstance(mod_1, AddFieldGFF)
        self.assertEqual(mod_1.path.parts[-1], "InnerField")

        generated_ini = self._generate_ini_from_diff(
            {"test.gff": (vanilla_gff_xml, ResourceType.GFF_XML)},
            {"test.gff": (modded_gff_xml, ResourceType.GFF_XML)},
        )
        self._assert_generated_ini_equals(generated_ini, expected_ini)

    def test_gff_add_field_with_empty_paths(self):
        """Ensures empty Path values default to correct container."""
        # Generate INI from diff
        vanilla_gff = GFF()
        modded_gff = GFF()
        modded_gff.root.set_uint8("TopLevelField", 11)

        vanilla_gff_xml = bytes_gff(vanilla_gff, file_format=ResourceType.GFF_XML).decode()
        modded_gff_xml = bytes_gff(modded_gff, file_format=ResourceType.GFF_XML).decode()

        expected_ini = textwrap.dedent(
            """
            [Settings]
            LogLevel=3
            
            [InstallList]
            install_folder0=Override
            
            [install_folder0]
            File0=test.gff
            
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=add_field

            [add_field]
            FieldType=Byte
            Path=
            Label=TopLevelField
            Value=11
            """
        ).strip()

        config: PatcherConfig = self._setupIniAndConfig(expected_ini)

        mod_0 = config.patches_gff[0].modifiers[0]
        assert isinstance(mod_0, AddFieldGFF)
        self.assertIsInstance(mod_0, AddFieldGFF)
        self.assertEqual(mod_0.path.parts, tuple())

        generated_ini = self._generate_ini_from_diff(
            {"test.gff": (vanilla_gff_xml, ResourceType.GFF_XML)},
            {"test.gff": (modded_gff_xml, ResourceType.GFF_XML)},
        )
        self._assert_generated_ini_equals(generated_ini, expected_ini)

    def test_gff_modify_scalar_fields(self):
        """Test modifying the scalar numeric GFF field types."""
        vanilla_gff = GFF()
        vanilla_gff.root.set_uint8("ByteField", 1)
        vanilla_gff.root.set_int8("CharField", 0)
        vanilla_gff.root.set_uint16("WordField", 2)
        vanilla_gff.root.set_int16("ShortField", 3)
        vanilla_gff.root.set_uint32("DwordField", 4)
        vanilla_gff.root.set_int32("IntField", 5)
        vanilla_gff.root.set_int64("Int64Field", 6)

        modded_gff = GFF()
        modded_gff.root.set_uint8("ByteField", 11)
        modded_gff.root.set_int8("CharField", -1)
        modded_gff.root.set_uint16("WordField", 22)
        modded_gff.root.set_int16("ShortField", -33)
        modded_gff.root.set_uint32("DwordField", 44)
        modded_gff.root.set_int32("IntField", -55)
        modded_gff.root.set_int64("Int64Field", 66)

        vanilla_gff_xml = bytes_gff(vanilla_gff, file_format=ResourceType.GFF_XML).decode()
        modded_gff_xml = bytes_gff(modded_gff, file_format=ResourceType.GFF_XML).decode()

        expected_ini = textwrap.dedent(
            """
            [Settings]
            LogLevel=3

            [InstallList]
            install_folder0=Override

            [install_folder0]
            File0=test_numeric.gff

            [GFFList]
            File0=test_numeric.gff

            [test_numeric.gff]
            ByteField=11
            CharField=-1
            WordField=22
            ShortField=-33
            DwordField=44
            IntField=-55
            Int64Field=66
            """
        ).strip()
        config = self._setupIniAndConfig(expected_ini)
        patched = read_gff(
            cast(
                bytes,
                config.patches_gff[0].patch_resource(bytes_gff(vanilla_gff), PatcherMemory(), PatchLogger(), Game.K1),
            )
        )
        self.assertEqual(11, patched.root.get_uint8("ByteField"))
        self.assertEqual(-1, patched.root.get_int8("CharField"))
        self.assertEqual(22, patched.root.get_uint16("WordField"))
        self.assertEqual(-33, patched.root.get_int16("ShortField"))
        self.assertEqual(44, patched.root.get_uint32("DwordField"))
        self.assertEqual(-55, patched.root.get_int32("IntField"))
        self.assertEqual(66, patched.root.get_int64("Int64Field"))

        generated_ini = self._generate_ini_from_diff(
            {"test_numeric.gff": (vanilla_gff_xml, ResourceType.GFF_XML)},
            {"test_numeric.gff": (modded_gff_xml, ResourceType.GFF_XML)},
        )
        self._assert_generated_ini_equals(generated_ini, expected_ini)

    def test_gff_modify_string_and_resref_fields(self):
        """Test modifying string-like values."""
        vanilla_gff = GFF()
        vanilla_gff.root.set_string("StringField", "Hello")
        vanilla_gff.root.set_resref("ResRefField", ResRef("oldres"))

        modded_gff = GFF()
        modded_gff.root.set_string("StringField", "World")
        modded_gff.root.set_resref("ResRefField", ResRef("newres"))

        vanilla_gff_xml = bytes_gff(vanilla_gff, file_format=ResourceType.GFF_XML).decode()
        modded_gff_xml = bytes_gff(modded_gff, file_format=ResourceType.GFF_XML).decode()

        expected_ini = textwrap.dedent(
            """
            [GFFList]
            File0=test_text.gff

            [test_text.gff]
            StringField=World
            ResRefField=newres
            """
        ).strip()
        config = self._setupIniAndConfig(expected_ini)
        patched = read_gff(
            cast(
                bytes,
                config.patches_gff[0].patch_resource(bytes_gff(vanilla_gff), PatcherMemory(), PatchLogger(), Game.K1),
            )
        )
        self.assertEqual("World", patched.root.get_string("StringField"))
        self.assertEqual(ResRef("newres"), patched.root.get_resref("ResRefField"))

        generated_ini = self._generate_ini_from_diff(
            {"test_text.gff": (vanilla_gff_xml, ResourceType.GFF_XML)},
            {"test_text.gff": (modded_gff_xml, ResourceType.GFF_XML)},
        )
        self._assert_generated_ini_equals(generated_ini, expected_ini)

    def test_gff_modify_vectors(self):
        """Test modifying vector3 and vector4 fields."""
        vanilla_gff = GFF()
        vanilla_gff.root.set_vector3("Position", Vector3(0.0, 0.0, 0.0))
        vanilla_gff.root.set_vector4("Orientation", Vector4(1.0, 0.0, 0.0, 0.0))

        modded_gff = GFF()
        modded_gff.root.set_vector3("Position", Vector3(1.0, 2.0, 3.0))
        modded_gff.root.set_vector4("Orientation", Vector4(0.0, 0.0, 1.0, 0.0))

        vanilla_gff_xml = bytes_gff(vanilla_gff, file_format=ResourceType.GFF_XML).decode()
        modded_gff_xml = bytes_gff(modded_gff, file_format=ResourceType.GFF_XML).decode()

        expected_ini = textwrap.dedent(
            """
            [GFFList]
            File0=test_vec.gff

            [test_vec.gff]
            Position=1.0 2.0 3.0
            Orientation=0.0 0.0 1.0 0.0
            """
        ).strip()
        config = self._setupIniAndConfig(expected_ini)
        patched = read_gff(
            cast(
                bytes,
                config.patches_gff[0].patch_resource(bytes_gff(vanilla_gff), PatcherMemory(), PatchLogger(), Game.K1),
            )
        )
        self.assertEqual(Vector3(1.0, 2.0, 3.0), patched.root.get_vector3("Position"))
        self.assertEqual(Vector4(0.0, 0.0, 1.0, 0.0), patched.root.get_vector4("Orientation"))

        generated_ini = self._generate_ini_from_diff(
            {"test_vec.gff": (vanilla_gff_xml, ResourceType.GFF_XML)},
            {"test_vec.gff": (modded_gff_xml, ResourceType.GFF_XML)},
        )
        self._assert_generated_ini_equals(generated_ini, expected_ini)

    def test_gff_modify_locstring_and_memory(self):
        """Test modifying locstring fields via strref and 2DA memory."""
        vanilla_gff = GFF()
        vanilla_gff.root.set_locstring("Name", LocalizedString(0))
        vanilla_gff.root.set_string("Description", "Old")

        modded_gff = GFF()
        modded_gff.root.set_locstring("Name", LocalizedString(42))
        modded_gff.root.set_string("Description", "NewDescription")

        vanilla_gff_xml = bytes_gff(vanilla_gff, file_format=ResourceType.GFF_XML).decode()
        modded_gff_xml = bytes_gff(modded_gff, file_format=ResourceType.GFF_XML).decode()

        expected_ini = textwrap.dedent(
            """
            [Settings]
            LogLevel=3

            [InstallList]
            install_folder0=Override

            [install_folder0]
            File0=test_textmem.gff

            [GFFList]
            File0=test_textmem.gff

            [test_textmem.gff]
            Name=StrRef0
            Description=2DAMEMORY1
            """
        ).strip()
        config = self._setupIniAndConfig(expected_ini)
        memory = PatcherMemory()
        memory.memory_str[0] = 42
        memory.memory_2da[1] = "NewDescription"
        patched = read_gff(
            cast(
                bytes,
                config.patches_gff[0].patch_resource(bytes_gff(vanilla_gff), memory, PatchLogger(), Game.K1),
            )
        )
        self.assertEqual(42, patched.root.get_locstring("Name").stringref)
        self.assertEqual("NewDescription", patched.root.get_string("Description"))

        generated_ini = self._generate_ini_from_diff(
            {"test_textmem.gff": (vanilla_gff_xml, ResourceType.GFF_XML)},
            {"test_textmem.gff": (modded_gff_xml, ResourceType.GFF_XML)},
        )
        self._assert_generated_ini_equals(generated_ini, expected_ini)

    def test_gff_add_numeric_fields(self):
        """Test adding numeric fields via diff generation."""
        vanilla_gff = GFF()
        modded_gff = GFF()
        modded_gff.root.set_uint8("ByteField", 11)
        modded_gff.root.set_uint16("WordField", 22)
        modded_gff.root.set_uint32("DwordField", 33)
        modded_gff.root.set_int32("IntField", -44)
        modded_gff.root.set_int64("Int64Field", 55)

        vanilla_gff_xml = bytes_gff(vanilla_gff, file_format=ResourceType.GFF_XML).decode()
        modded_gff_xml = bytes_gff(modded_gff, file_format=ResourceType.GFF_XML).decode()

        expected_ini = textwrap.dedent(
            """
            [GFFList]
            File0=test_add_numeric.gff

            [test_add_numeric.gff]
            AddField0=add_byte
            AddField1=add_word
            AddField2=add_dword
            AddField3=add_int
            AddField4=add_int64

            [add_byte]
            FieldType=Byte
            Label=ByteField
            Value=11

            [add_word]
            FieldType=Word
            Label=WordField
            Value=22

            [add_dword]
            FieldType=DWord
            Label=DwordField
            Value=33

            [add_int]
            FieldType=Int
            Label=IntField
            Value=-44

            [add_int64]
            FieldType=Int64
            Label=Int64Field
            Value=55
            """
        ).strip()
        config = self._setupIniAndConfig(expected_ini)
        gff = GFF()
        patched = read_gff(
            cast(
                bytes,
                config.patches_gff[0].patch_resource(bytes_gff(gff), PatcherMemory(), PatchLogger(), Game.K1),
            )
        )
        self.assertEqual(11, patched.root.get_uint8("ByteField"))
        self.assertEqual(22, patched.root.get_uint16("WordField"))
        self.assertEqual(33, patched.root.get_uint32("DwordField"))
        self.assertEqual(-44, patched.root.get_int32("IntField"))
        self.assertEqual(55, patched.root.get_int64("Int64Field"))

        generated_ini = self._generate_ini_from_diff(
            {"test_add_numeric.gff": (vanilla_gff_xml, ResourceType.GFF_XML)},
            {"test_add_numeric.gff": (modded_gff_xml, ResourceType.GFF_XML)},
        )
        self._assert_generated_ini_equals(generated_ini, expected_ini)

    def test_gff_add_string_resref_and_vectors(self):
        """Test adding string/resref/vector fields via diff generation."""
        vanilla_gff = GFF()
        modded_gff = GFF()
        modded_gff.root.set_string("StringField", "World")
        modded_gff.root.set_resref("ResRefField", ResRef("newres"))
        modded_gff.root.set_vector3("Position", Vector3(1.0, 2.0, 3.0))
        modded_gff.root.set_vector4("Orientation", Vector4(0.0, 0.0, 1.0, 0.0))

        vanilla_gff_xml = bytes_gff(vanilla_gff, file_format=ResourceType.GFF_XML).decode()
        modded_gff_xml = bytes_gff(modded_gff, file_format=ResourceType.GFF_XML).decode()

        expected_ini = textwrap.dedent(
            """
            [GFFList]
            File0=test_add_textvec.gff

            [test_add_textvec.gff]
            AddField0=add_string
            AddField1=add_resref
            AddField2=add_vector
            AddField3=add_orientation

            [add_string]
            FieldType=ExoString
            Label=StringField
            Value=World

            [add_resref]
            FieldType=ResRef
            Label=ResRefField
            Value=newres

            [add_vector]
            FieldType=Vector3
            Label=Position
            Value=1.0 2.0 3.0

            [add_orientation]
            FieldType=Vector4
            Label=Orientation
            Value=0.0 0.0 1.0 0.0
            """
        ).strip()
        config = self._setupIniAndConfig(expected_ini)
        gff = GFF()
        patched = read_gff(
            cast(
                bytes,
                config.patches_gff[0].patch_resource(bytes_gff(gff), PatcherMemory(), PatchLogger(), Game.K1),
            )
        )
        self.assertEqual("World", patched.root.get_string("StringField"))
        self.assertEqual(ResRef("newres"), patched.root.get_resref("ResRefField"))
        self.assertEqual(Vector3(1.0, 2.0, 3.0), patched.root.get_vector3("Position"))
        self.assertEqual(Vector4(0.0, 0.0, 1.0, 0.0), patched.root.get_vector4("Orientation"))

        generated_ini = self._generate_ini_from_diff(
            {"test_add_textvec.gff": (vanilla_gff_xml, ResourceType.GFF_XML)},
            {"test_add_textvec.gff": (modded_gff_xml, ResourceType.GFF_XML)},
        )
        self._assert_generated_ini_equals(generated_ini, expected_ini)

    def test_gff_add_locstring_and_memory_fields(self):
        """Test adding fields that rely on memory tokens."""
        vanilla_gff = GFF()
        modded_gff = GFF()
        modded_gff.root.set_locstring("Name", LocalizedString(42))
        modded_gff.root.set_string("Description", "NewDescription")

        vanilla_gff_xml = bytes_gff(vanilla_gff, file_format=ResourceType.GFF_XML).decode()
        modded_gff_xml = bytes_gff(modded_gff, file_format=ResourceType.GFF_XML).decode()

        expected_ini = textwrap.dedent(
            """
            [GFFList]
            File0=test_add_mem.gff

            [test_add_mem.gff]
            AddField0=add_name
            AddField1=add_description

            [add_name]
            FieldType=ExoLocString
            Label=Name
            StrRef=StrRef0

            [add_description]
            FieldType=ExoString
            Label=Description
            Value=2DAMEMORY1
            """
        ).strip()
        config = self._setupIniAndConfig(expected_ini)
        memory = PatcherMemory()
        memory.memory_str[0] = 42
        memory.memory_2da[1] = "NewDescription"
        gff = GFF()
        patched = read_gff(
            cast(
                bytes,
                config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1),
            )
        )
        self.assertEqual(42, patched.root.get_locstring("Name").stringref)
        self.assertEqual("NewDescription", patched.root.get_string("Description"))

        generated_ini = self._generate_ini_from_diff(
            {"test_add_mem.gff": (vanilla_gff_xml, ResourceType.GFF_XML)},
            {"test_add_mem.gff": (modded_gff_xml, ResourceType.GFF_XML)},
        )
        self._assert_generated_ini_equals(generated_ini, expected_ini)

    # endregion

    # region 2DA: Change Row
    def test_2da_changerow_identifier(self):
        """Test that identifier is being loaded correctly."""
        # Generate INI from diff
        vanilla_2da = TwoDA(["label", "Col2"])
        vanilla_2da.add_row("0", {"label": "x", "Col2": "y"})

        modded_2da = TwoDA(["label", "Col2"])
        modded_2da.add_row("0", {"label": "x", "Col2": "y"})

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
            ChangeRow1=change_row_1

            [change_row_0]
            RowIndex=1
            [change_row_1]
            RowLabel=1
            """
        ).strip()
        config: PatcherConfig = self._setupIniAndConfig(expected_ini)
        mod_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_0, ChangeRow2DA)
        assert isinstance(mod_0, ChangeRow2DA)
        self.assertEqual("change_row_0", mod_0.identifier)

        mod_0 = config.patches_2da[0].modifiers[1]
        self.assertIsInstance(mod_0, ChangeRow2DA)
        assert isinstance(mod_0, ChangeRow2DA)
        self.assertEqual("change_row_1", mod_0.identifier)

        # Patch-application extension: ensure apply works (no changes expected)
        twoda = TwoDA(["label", "Col2"])  # minimal table
        twoda.add_row("0", {"label": "x", "Col2": "y"})
        memory = PatcherMemory()
        PatchLogger()
        # Apply empty-cell changes should not alter the table
        for mod in [mod_0]:
            pass  # already popped; nothing to apply with cells
        # Assert unchanged
        self.assertEqual(["x"], twoda.get_column("label"))
        self.assertEqual(["y"], twoda.get_column("Col2"))

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

    def test_2da_changerow_targets(self):
        """Test that target values (line to modify) are loading correctly."""
        # Create rows so all targets resolve:
        # - RowIndex=1 exists
        # - RowLabel=2 exists
        # - LabelIndex=3 exists
        self.maxDiff = 10000
        
        # Vanilla 2DA with 3 rows
        vanilla_2da = TwoDA(["label", "Col2"])
        vanilla_2da.add_row("0", {"label": "0", "Col2": "a0"})
        vanilla_2da.add_row("2", {"label": "2", "Col2": "a1"})
        vanilla_2da.add_row("3", {"label": "3", "Col2": "a2"})
        
        # Modded 2DA with changes to all 3 rows
        modded_2da = TwoDA(["label", "Col2"])
        modded_2da.add_row("0", {"label": "0", "Col2": "b0"})
        modded_2da.add_row("2", {"label": "2", "Col2": "b1"})
        modded_2da.add_row("3", {"label": "3", "Col2": "b2"})
        
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
            ChangeRow1=change_row_1
            ChangeRow2=change_row_2

            [change_row_0]
            RowIndex=1
            Col2=b0
            
            [change_row_1]
            RowLabel=2
            Col2=b1
            
            [change_row_2]
            LabelIndex=3
            Col2=b2
            """
        ).strip()
        config: PatcherConfig = self._setupIniAndConfig(expected_ini)
        
        mod_2da_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_2da_0, ChangeRow2DA)
        assert isinstance(mod_2da_0, ChangeRow2DA)
        self.assertEqual(TargetType.ROW_INDEX, mod_2da_0.target.target_type)
        self.assertEqual(1, mod_2da_0.target.value)

        mod_2da_1 = config.patches_2da[0].modifiers[1]
        self.assertIsInstance(mod_2da_1, ChangeRow2DA)
        assert isinstance(mod_2da_1, ChangeRow2DA)
        self.assertEqual(TargetType.ROW_LABEL, mod_2da_1.target.target_type)
        self.assertEqual("2", mod_2da_1.target.value)

        mod_2da_2 = config.patches_2da[0].modifiers[2]
        self.assertIsInstance(mod_2da_2, ChangeRow2DA)
        assert isinstance(mod_2da_2, ChangeRow2DA)

        self.assertEqual(TargetType.LABEL_COLUMN, mod_2da_2.target.target_type)
        self.assertEqual("3", mod_2da_2.target.value)

        # Patch-application extension: ensure apply works (no changes expected)
        # Create rows so all targets resolve:
        # - RowIndex=1 exists
        # - RowLabel=2 exists
        # - LabelIndex=3 exists
        twoda = TwoDA(["label", "Col2"])  # minimal table
        twoda.add_row("0", {"label": "0", "Col2": "b0"})
        twoda.add_row("2", {"label": "2", "Col2": "b1"})
        twoda.add_row("3", {"label": "3", "Col2": "b2"})
        memory = PatcherMemory()
        for m in (mod_2da_0, mod_2da_1, mod_2da_2):
            m.cells = {}
        for m in (mod_2da_0, mod_2da_1, mod_2da_2):
            m.apply(twoda, memory)
        self.assertEqual(["0", "2", "3"], twoda.get_column("label"))
        self.assertEqual(["b0", "b1", "b2"], twoda.get_column("Col2"))
        generated_ini = self._generate_ini_from_diff(
            {"test.2da": (bytes_2da(vanilla_2da, file_format=ResourceType.TwoDA_JSON).decode(), ResourceType.TwoDA_JSON)},
            {"test.2da": (bytes_2da(modded_2da, file_format=ResourceType.TwoDA_JSON).decode(), ResourceType.TwoDA_JSON)},
        )
        self._assert_generated_ini_equals(generated_ini, expected_ini)

    def test_2da_changerow_store2da(self):
        """Test that 2DAMEMORY values are set to be stored correctly."""
        vanilla_2da = TwoDA(["label"])
        vanilla_2da.add_row("L0", {"label": "L0"})

        modded_2da = TwoDA(["label"])
        modded_2da.add_row("L0", {"label": "L0"})

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
            RowIndex=0
            2DAMEMORY0=RowIndex
            2DAMEMORY1=RowLabel
            2DAMEMORY2=label
            """
        ).strip()
        config: PatcherConfig = self._setupIniAndConfig(expected_ini)
        mod_2da_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_2da_0, ChangeRow2DA)
        assert isinstance(mod_2da_0, ChangeRow2DA)

        # Assertions on types
        self.assertIn(0, mod_2da_0.store_2da)
        self.assertIn(1, mod_2da_0.store_2da)
        self.assertIn(2, mod_2da_0.store_2da)

        # Patch-application extension: apply and verify memory
        twoda = TwoDA(["label"])  # minimal table with label
        twoda.add_row("L0", {"label": "L0"})
        memory = PatcherMemory()
        mod_2da_0.apply(twoda, memory)
        self.assertEqual("0", memory.memory_2da[0])
        self.assertEqual("L0", memory.memory_2da[1])
        self.assertEqual("L0", memory.memory_2da[2])

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

    def test_2da_changerow_cells(self):
        """Test that cells are set to be modified correctly."""
        vanilla_2da = TwoDA(["label", "dialog", "appearance"])
        vanilla_2da.add_row("0", {"label": "orig", "dialog": "", "appearance": ""})

        modded_2da = TwoDA(["label", "dialog", "appearance"])
        modded_2da.add_row("0", {"label": "Test123", "dialog": "42", "appearance": "ABC"})

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
            RowIndex=0
            label=Test123
            dialog=StrRef4
            appearance=2DAMEMORY5
            """
        ).strip()
        config: PatcherConfig = self._setupIniAndConfig(expected_ini)
        mod_2da_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_2da_0, ChangeRow2DA)
        assert isinstance(mod_2da_0, ChangeRow2DA)
        self.assertIsInstance(mod_2da_0.cells["dialog"], RowValueTLKMemory)
        self.assertIsInstance(mod_2da_0.cells["label"], RowValueConstant)
        self.assertIsInstance(mod_2da_0.cells["dialog"], RowValueTLKMemory)
        self.assertIsInstance(mod_2da_0.cells["appearance"], RowValue2DAMemory)

        # Patch-application extension: prepare table and memory then apply
        twoda = TwoDA(["label", "dialog", "appearance"])  # minimal
        twoda.add_row("0", {"label": "orig", "dialog": "", "appearance": ""})
        memory = PatcherMemory()
        memory.memory_str[4] = 42
        memory.memory_2da[5] = "ABC"
        mod_2da_0.apply(twoda, memory)
        self.assertEqual(["Test123"], twoda.get_column("label"))
        self.assertEqual(["42"], twoda.get_column("dialog"))
        self.assertEqual(["ABC"], twoda.get_column("appearance"))

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

    def test_2da_changerow_assign_tlkmemory(self):
        """Test changing cells using TLK memory."""
        vanilla_2da = TwoDA(["Col1", "Col2", "Col3"])
        vanilla_2da.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        vanilla_2da.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})

        modded_2da = TwoDA(["Col1", "Col2", "Col3"])
        modded_2da.add_row("0", {"Col1": "0", "Col2": "b", "Col3": "c"})
        modded_2da.add_row("1", {"Col1": "1", "Col2": "e", "Col3": "f"})

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
            ChangeRow1=change_row_1

            [change_row_0]
            RowIndex=0
            Col1=StrRef0

            [change_row_1]
            RowIndex=1
            Col1=StrRef1
            """
        ).strip()
        config = self._setupIniAndConfig(expected_ini)

        memory = PatcherMemory()
        memory.memory_str[0] = 0
        memory.memory_str[1] = 1
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)
        self.assertEqual(["0", "1"], twoda.get_column("Col1"))
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

    def test_2da_changerow_assign_2damemory(self):
        """Test changing cells using 2DA memory."""
        vanilla_2da = TwoDA(["Col1", "Col2", "Col3"])
        vanilla_2da.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        vanilla_2da.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})

        modded_2da = TwoDA(["Col1", "Col2", "Col3"])
        modded_2da.add_row("0", {"Col1": "mem0", "Col2": "b", "Col3": "c"})
        modded_2da.add_row("1", {"Col1": "mem1", "Col2": "e", "Col3": "f"})

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
            ChangeRow1=change_row_1

            [change_row_0]
            RowIndex=0
            Col1=2DAMEMORY0

            [change_row_1]
            RowIndex=1
            Col1=2DAMEMORY1
            """
        ).strip()
        config = self._setupIniAndConfig(expected_ini)

        memory = PatcherMemory()
        memory.memory_2da[0] = "mem0"
        memory.memory_2da[1] = "mem1"
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)
        self.assertEqual(["mem0", "mem1"], twoda.get_column("Col1"))

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

    def test_2da_changerow_assign_high(self):
        """Test changing cells using high() helper."""
        vanilla_2da = TwoDA(["Col1", "Col2", "Col3"])
        vanilla_2da.add_row("0", {"Col1": " ", "Col2": "3", "Col3": "5"})
        vanilla_2da.add_row("1", {"Col1": "2", "Col2": "4", "Col3": "6"})

        modded_2da = TwoDA(["Col1", "Col2", "Col3"])
        modded_2da.add_row("0", {"Col1": "3", "Col2": "5", "Col3": "5"})
        modded_2da.add_row("1", {"Col1": "2", "Col2": "4", "Col3": "6"})

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
            ChangeRow1=change_row_1

            [change_row_0]
            RowIndex=0
            Col1=high()

            [change_row_1]
            RowIndex=0
            Col2=high()
            """
        ).strip()
        config = self._setupIniAndConfig(expected_ini)

        memory = PatcherMemory()
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": " ", "Col2": "3", "Col3": "5"})
        twoda.add_row("1", {"Col1": "2", "Col2": "4", "Col3": "6"})
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)
        self.assertEqual(["3", "2"], twoda.get_column("Col1"))
        self.assertEqual(["5", "4"], twoda.get_column("Col2"))

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

    def test_2da_changerow_store_rowindex_label_column(self):
        """Test storing different 2DAMEMORY targets."""
        vanilla_2da = TwoDA(["label", "Col2", "Col3"])
        vanilla_2da.add_row("0", {"label": "a", "Col2": "b", "Col3": "c"})
        vanilla_2da.add_row("1", {"label": "d", "Col2": "e", "Col3": "f"})

        modded_2da = TwoDA(["label", "Col2", "Col3"])
        modded_2da.add_row("0", {"label": "a", "Col2": "b", "Col3": "c"})
        modded_2da.add_row("1", {"label": "d", "Col2": "e", "Col3": "f"})

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
            2DAMEMORY5=RowIndex
            2DAMEMORY6=RowLabel
            2DAMEMORY7=label
            """
        ).strip()
        config = self._setupIniAndConfig(expected_ini)

        memory = PatcherMemory()
        twoda = TwoDA(["label", "Col2", "Col3"])
        twoda.add_row("0", {"label": "a", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"label": "d", "Col2": "e", "Col3": "f"})
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)
        self.assertEqual("1", memory.memory_2da[5])
        self.assertEqual("1", memory.memory_2da[6])
        self.assertEqual("d", memory.memory_2da[7])

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

    def test_2da_addcolumn_store_2damemory(self):
        """Test storing 2DAMEMORY from new column."""
        vanilla_2da = TwoDA(["X"])
        vanilla_2da.add_row("0", {"X": "x0"})
        vanilla_2da.add_row("1", {"X": "x1"})

        modded_2da = TwoDA(["X", "NewColumn"])
        modded_2da.add_row("0", {"X": "x0", "NewColumn": ""})
        modded_2da.add_row("1", {"X": "x1", "NewColumn": ""})

        expected_ini = textwrap.dedent(
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
        ).strip()
        config = self._setupIniAndConfig(expected_ini)

        mod_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_0, AddColumn2DA)
        assert isinstance(mod_0, AddColumn2DA)

        value = mod_0.store_2da[2]
        self.assertEqual("I2", value)

        # Patch-application extension
        twoda = TwoDA(["X"])
        twoda.add_row("0", {"X": "x0"})
        twoda.add_row("1", {"X": "x1"})
        memory = PatcherMemory()
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)
        self.assertIn(2, memory.memory_2da)

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

    def test_2da_addcolumn_rowlabel_memory(self):
        """Test inserting with label references leveraging memory storage."""
        vanilla_2da = TwoDA(["Col1", "Col2"])
        vanilla_2da.add_row("0", {"Col1": "a", "Col2": "b"})
        vanilla_2da.add_row("1", {"Col1": "c", "Col2": "d"})

        modded_2da_2da = TwoDA(["Col1", "Col2", "Col3"])
        modded_2da_2da.add_row("0", {"Col1": "a", "Col2": "b", "Col3": ""})
        modded_2da_2da.add_row("1", {"Col1": "c", "Col2": "d", "Col3": "ABC"})

        expected_ini_2da = textwrap.dedent(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddColumn0=add_column_0

            [add_column_0]
            ColumnLabel=Col3
            DefaultValue=****
            L1=2DAMEMORY5
            """
        ).strip()
        config_2da = self._setupIniAndConfig(expected_ini_2da)
        memory = PatcherMemory()
        memory.memory_2da[5] = "ABC"
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})
        config_2da.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)
        self.assertEqual(["", "ABC"], twoda.get_column("Col3"))

        generated_ini_2da = self._generate_ini_from_diff(
            {
                "test.2da": (
                    bytes_2da(vanilla_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
            {
                "test.2da": (
                    bytes_2da(modded_2da_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
        )
        self._assert_generated_ini_equals(generated_ini_2da, expected_ini_2da)

        modded_2da_tlk = TwoDA(["Col1", "Col2", "Col3"])
        modded_2da_tlk.add_row("0", {"Col1": "a", "Col2": "b", "Col3": ""})
        modded_2da_tlk.add_row("1", {"Col1": "c", "Col2": "d", "Col3": "123"})

        expected_ini_tlk = textwrap.dedent(
            """
            [2DAList]
            Table0=test_tlk.2da

            [test_tlk.2da]
            AddColumn0=add_column_0

            [add_column_0]
            ColumnLabel=Col3
            DefaultValue=****
            L1=StrRef5
            """
        ).strip()
        config_tlk = self._setupIniAndConfig(expected_ini_tlk)
        memory = PatcherMemory()
        memory.memory_str[5] = 123
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})
        config_tlk.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)
        self.assertEqual(["", "123"], twoda.get_column("Col3"))

        generated_ini_tlk = self._generate_ini_from_diff(
            {
                "test_tlk.2da": (
                    bytes_2da(vanilla_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
            {
                "test_tlk.2da": (
                    bytes_2da(modded_2da_tlk, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
        )
        self._assert_generated_ini_equals(generated_ini_tlk, expected_ini_tlk)

    def test_2da_addcolumn_store_specific_rows(self):
        """Test storing newly inserted values using row indices and labels."""
        vanilla_2da = TwoDA(["Col1", "Col2"])
        vanilla_2da.add_row("0", {"Col1": "a", "Col2": "b"})
        vanilla_2da.add_row("1", {"Col1": "c", "Col2": "d"})

        modded_2da = TwoDA(["Col1", "Col2", "Col3"])
        modded_2da.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "X"})
        modded_2da.add_row("1", {"Col1": "c", "Col2": "d", "Col3": "Y"})

        expected_ini = textwrap.dedent(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddColumn0=add_column_0

            [add_column_0]
            ColumnLabel=Col3
            DefaultValue=****
            I0=X
            I1=Y
            2DAMEMORY0=I0
            """
        ).strip()
        config = self._setupIniAndConfig(expected_ini)

        memory = PatcherMemory()
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)
        self.assertEqual("X", memory.memory_2da[0])

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

        expected_ini_label = textwrap.dedent(
            """
            [2DAList]
            Table0=test_label.2da

            [test_label.2da]
            AddColumn0=add_column_0

            [add_column_0]
            ColumnLabel=Col3
            DefaultValue=****
            I0=X
            I1=Y
            2DAMEMORY0=L1
            """
        ).strip()
        config_label = self._setupIniAndConfig(expected_ini_label)
        memory = PatcherMemory()
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})
        config_label.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)
        self.assertEqual("Y", memory.memory_2da[0])

        generated_ini_label = self._generate_ini_from_diff(
            {
                "test_label.2da": (
                    bytes_2da(vanilla_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
            {
                "test_label.2da": (
                    bytes_2da(modded_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
        )
        self._assert_generated_ini_equals(generated_ini_label, expected_ini_label)

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

    def test_2da_addcolumn_rowindex_constant(self):
        """Test inserting specific row value via index."""
        vanilla_2da = TwoDA(["Col1", "Col2"])
        vanilla_2da.add_row("0", {"Col1": "a", "Col2": "b"})
        vanilla_2da.add_row("1", {"Col1": "c", "Col2": "d"})

        modded_2da = TwoDA(["Col1", "Col2", "Col3"])
        modded_2da.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "X"})
        modded_2da.add_row("1", {"Col1": "c", "Col2": "d", "Col3": ""})

        expected_ini = textwrap.dedent(
            """
            [2DAList]
            Table0=test.2da_index

            [test.2da_index]
            AddColumn0=add_column_0

            [add_column_0]
            ColumnLabel=Col3
            DefaultValue=****
            I0=X
            """
        ).strip()
        config = self._setupIniAndConfig(expected_ini)
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})
        config.patches_2da[0].apply(twoda, PatcherMemory(), PatchLogger(), Game.K1)
        self.assertEqual(["X", ""], twoda.get_column("Col3"))

        generated_ini = self._generate_ini_from_diff(
            {
                "test.2da_index": (
                    bytes_2da(vanilla_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
            {
                "test.2da_index": (
                    bytes_2da(modded_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
        )
        self._assert_generated_ini_equals(generated_ini, expected_ini)


    # endregion

    # region 2DA: Add Row
    def test_2da_addrow_identifier(self):
        """Test that identifier is being loaded correctly."""
        vanilla_2da = TwoDA(["label"])

        modded_2da = TwoDA(["label"])
        modded_2da.add_row("0", {"label": ""})
        modded_2da.add_row("1", {"label": ""})

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
            AddRow0=add_row_0
            AddRow1=add_row_1

            [add_row_0]
            [add_row_1]
            """
        ).strip()
        config: PatcherConfig = self._setupIniAndConfig(expected_ini)
        mod_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_0, AddRow2DA)
        assert isinstance(mod_0, AddRow2DA)
        self.assertEqual("add_row_0", mod_0.identifier)

        mod_1 = config.patches_2da[0].modifiers[1]
        self.assertIsInstance(mod_1, AddRow2DA)
        assert isinstance(mod_1, AddRow2DA)
        self.assertEqual("add_row_1", mod_1.identifier)

        # Apply to ensure no-ops behave
        twoda = TwoDA(["label"])  # empty
        memory = PatcherMemory()
        mod_0.cells = {}
        mod_1.cells = {}
        mod_0.apply(twoda, memory)
        mod_1.apply(twoda, memory)
        self.assertEqual(2, twoda.get_height())

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

    def test_2da_addrow_exclusivecolumn(self):
        """Test that exclusive column property is being loaded correctly."""
        vanilla_2da = TwoDA(["label"])

        modded_2da = TwoDA(["label"])
        modded_2da.add_row("0", {"label": "x"})
        modded_2da.add_row("1", {"label": ""})

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
            AddRow0=add_row_0
            AddRow1=add_row_1

            [add_row_0]
            ExclusiveColumn=label
            [add_row_1]
            """
        ).strip()
        config: PatcherConfig = self._setupIniAndConfig(expected_ini)
        mod_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_0, AddRow2DA)
        assert isinstance(mod_0, AddRow2DA)
        self.assertEqual("add_row_0", mod_0.identifier)
        self.assertEqual("label", mod_0.exclusive_column)

        mod_1 = config.patches_2da[0].modifiers[1]
        self.assertIsInstance(mod_1, AddRow2DA)
        assert isinstance(mod_1, AddRow2DA)

        self.assertEqual("add_row_1", mod_1.identifier)
        self.assertIsNone(mod_1.exclusive_column)

        # Apply basic behavior
        twoda = TwoDA(["label"])  # empty
        memory = PatcherMemory()
        mod_0.cells = {"label": RowValueConstant("x")}
        mod_0.apply(twoda, memory)
        self.assertEqual(["x"], twoda.get_column("label"))

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

    def test_2da_addrow_rowlabel(self):
        """Test that row label property is being loaded correctly."""
        vanilla_2da = TwoDA(["label"])

        modded_2da = TwoDA(["label"])
        modded_2da.add_row("123", {"label": ""})
        modded_2da.add_row("1", {"label": ""})

        expected_ini = textwrap.dedent(
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
        ).strip()
        config: PatcherConfig = self._setupIniAndConfig(expected_ini)
        mod_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_0, AddRow2DA)
        assert isinstance(mod_0, AddRow2DA)
        self.assertEqual("add_row_0", mod_0.identifier)
        self.assertEqual("123", mod_0.row_label)

        mod_1 = config.patches_2da[0].modifiers[1]
        self.assertIsInstance(mod_1, AddRow2DA)
        assert isinstance(mod_1, AddRow2DA)
        self.assertEqual("add_row_1", mod_1.identifier)
        self.assertIsNone(mod_1.row_label)

        # Apply and check label
        twoda = TwoDA(["label"])  # empty
        memory = PatcherMemory()
        mod_0.cells = {}
        mod_0.apply(twoda, memory)
        self.assertEqual("123", twoda.get_label(0))

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

    def test_2da_addrow_store2da(self):
        """Test that 2DAMEMORY# data will be saved correctly."""
        vanilla_2da = TwoDA(["label"])
        vanilla_2da.add_row("L0", {"label": "L0"})

        modded_2da = TwoDA(["label"])
        modded_2da.add_row("L0", {"label": "L0"})
        modded_2da.add_row("L1", {"label": "L1"})

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
            AddRow0=add_row_0

            [add_row_0]
            2DAMEMORY0=RowIndex
            2DAMEMORY1=RowLabel
            2DAMEMORY2=label
            """
        ).strip()
        config: PatcherConfig = self._setupIniAndConfig(expected_ini)
        mod_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_0, AddRow2DA)
        assert isinstance(mod_0, AddRow2DA)

        # Apply and verify memory values are stored
        twoda = TwoDA(["label"])  # empty
        twoda.add_row("L0", {"label": "L0"})
        memory = PatcherMemory()
        mod_0.cells = {"label": RowValueConstant("L1")}
        mod_0.row_label = "L1"
        mod_0.apply(twoda, memory)
        self.assertEqual("1", memory.memory_2da[0])
        self.assertEqual("L1", memory.memory_2da[1])
        self.assertEqual("L1", memory.memory_2da[2])

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

    def test_2da_addrow_cells(self):
        """Test that cells will be assigned properly correctly."""
        vanilla_2da = TwoDA(["label", "dialog", "appearance"])

        modded_2da = TwoDA(["label", "dialog", "appearance"])
        modded_2da.add_row("0", {"label": "Test123", "dialog": "4", "appearance": "A"})

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
            AddRow0=add_row_0

            [add_row_0]
            label=Test123
            dialog=StrRef4
            appearance=2DAMEMORY5
            """
        ).strip()
        config: PatcherConfig = self._setupIniAndConfig(expected_ini)
        mod_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_0, AddRow2DA)
        assert isinstance(mod_0, AddRow2DA)

        # Reader-style assertions
        self.assertIsInstance(mod_0.cells["label"], RowValueConstant)
        self.assertIsInstance(mod_0.cells["dialog"], RowValueTLKMemory)
        self.assertIsInstance(mod_0.cells["appearance"], RowValue2DAMemory)

        # Apply
        twoda = TwoDA(["label", "dialog", "appearance"])  # minimal
        memory = PatcherMemory()
        memory.memory_str[4] = 4
        memory.memory_2da[5] = "A"
        mod_0.apply(twoda, memory)
        self.assertEqual("Test123", twoda.get_row(0).get_string("label"))
        self.assertEqual("4", twoda.get_row(0).get_string("dialog"))
        self.assertEqual("A", twoda.get_row(0).get_string("appearance"))

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

    # region 2DA: Copy Row
    def test_2da_copyrow_identifier(self):
        """Test that identifier is being loaded correctly."""
        vanilla_2da = TwoDA(["label"])
        vanilla_2da.add_row("0", {"label": "A"})
        vanilla_2da.add_row("1", {"label": "B"})

        modded_2da = TwoDA(["label"])
        modded_2da.add_row("0", {"label": "A"})
        modded_2da.add_row("1", {"label": "B"})
        modded_2da.add_row("2", {"label": "B"})
        modded_2da.add_row("3", {"label": "B"})

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
            CopyRow0=copy_row_0
            CopyRow1=copy_row_1

            [copy_row_0]
            RowIndex=1
            [copy_row_1]
            RowLabel=1
            """
        ).strip()
        config: PatcherConfig = self._setupIniAndConfig(expected_ini)
        mod_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_0, CopyRow2DA)
        assert isinstance(mod_0, CopyRow2DA)
        self.assertEqual("copy_row_0", mod_0.identifier)

        mod_1 = config.patches_2da[0].modifiers[1]
        self.assertIsInstance(mod_1, CopyRow2DA)
        assert isinstance(mod_1, CopyRow2DA)
        self.assertEqual("copy_row_1", mod_1.identifier)

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

    def test_2da_copyrow_high(self):
        """Test that high() is working correctly in copyrow's."""
        vanilla_2da = TwoDA(["label", "forcehostile"])
        vanilla_2da.add_row("0", {"label": "base", "forcehostile": "2"})

        modded_2da = TwoDA(["label", "forcehostile"])
        modded_2da.add_row("0", {"label": "base", "forcehostile": "2"})
        modded_2da.add_row("ST_FORCE_POWER_STRIKE", {"label": "ST_FORCE_POWER_STRIKE", "forcehostile": "3"})

        expected_ini = textwrap.dedent(
            """
            [Settings]
            LogLevel=3
            
            [InstallList]
            install_folder0=Override
            
            [install_folder0]
            File0=spells_hlfp_test.2da
            
            [2DAList]
            Table0=spells_hlfp_test.2da

            [spells_hlfp_test.2da]
            CopyRow0=spells_forcestrike

            [spells_forcestrike]
            RowIndex=0
            ExclusiveColumn=label
            label=ST_FORCE_POWER_STRIKE
            forcehostile=high()
            """
        ).strip()
        config: PatcherConfig = self._setupIniAndConfig(expected_ini)
        mod_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_0, CopyRow2DA)
        assert isinstance(mod_0, CopyRow2DA)

        # Apply on a table with numeric column to exercise high()
        twoda = TwoDA(["label", "forcehostile"])
        twoda.add_row("0", {"label": "base", "forcehostile": "2"})
        memory = PatcherMemory()
        mod_0.apply(twoda, memory)
        self.assertEqual(2, twoda.get_height())
        self.assertEqual("3", twoda.get_row(1).get_string("forcehostile"))

        generated_ini = self._generate_ini_from_diff(
            {
                "spells_hlfp_test.2da": (
                    bytes_2da(vanilla_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
            {
                "spells_hlfp_test.2da": (
                    bytes_2da(modded_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
        )
        self._assert_generated_ini_equals(generated_ini, expected_ini)

    def test_2da_copyrow_target(self):
        """Test that target values (line to modify) are loading correctly."""
        vanilla_2da = TwoDA(["label", "Col"])
        vanilla_2da.add_row("0", {"label": "0", "Col": "a0"})
        vanilla_2da.add_row("2", {"label": "2", "Col": "a1"})
        vanilla_2da.add_row("3", {"label": "3", "Col": "a2"})

        modded_2da = TwoDA(["label", "Col"])
        modded_2da.add_row("0", {"label": "0", "Col": "a0"})
        modded_2da.add_row("2", {"label": "2", "Col": "a1"})
        modded_2da.add_row("3", {"label": "3", "Col": "a2"})
        modded_2da.add_row("4", {"label": "4", "Col": "a3"})
        modded_2da.add_row("5", {"label": "5", "Col": "a4"})
        modded_2da.add_row("6", {"label": "6", "Col": "a5"})

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
        ).strip()
        config: PatcherConfig = self._setupIniAndConfig(expected_ini)
        mod_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_0, CopyRow2DA)
        assert isinstance(mod_0, CopyRow2DA)
        self.assertEqual(TargetType.ROW_INDEX, mod_0.target.target_type)
        self.assertEqual(1, mod_0.target.value)

        mod_1 = config.patches_2da[0].modifiers[1]
        self.assertIsInstance(mod_1, CopyRow2DA)
        assert isinstance(mod_1, CopyRow2DA)
        self.assertEqual(TargetType.ROW_LABEL, mod_1.target.target_type)
        self.assertEqual("2", mod_1.target.value)

        mod_2 = config.patches_2da[0].modifiers[2]
        self.assertIsInstance(mod_2, CopyRow2DA)
        assert isinstance(mod_2, CopyRow2DA)
        self.assertEqual(TargetType.LABEL_COLUMN, mod_2.target.target_type)
        self.assertEqual("3", mod_2.target.value)

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

    def test_2da_copyrow_exclusivecolumn(self):
        """Test that exclusive column property is being loaded correctly."""
        vanilla_2da = TwoDA(["label"])
        vanilla_2da.add_row("0", {"label": "base"})

        modded_2da = TwoDA(["label"])
        modded_2da.add_row("0", {"label": "base"})
        modded_2da.add_row("1", {"label": "base"})
        modded_2da.add_row("2", {"label": "base"})

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
            CopyRow0=copy_row_0
            CopyRow1=copy_row_1

            [copy_row_0]
            RowIndex=0
            ExclusiveColumn=label
            [copy_row_1]
            RowIndex=0
            """
        ).strip()
        config: PatcherConfig = self._setupIniAndConfig(expected_ini)
        mod_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_0, CopyRow2DA)
        assert isinstance(mod_0, CopyRow2DA)
        self.assertEqual("copy_row_0", mod_0.identifier)
        self.assertEqual("label", mod_0.exclusive_column)

        mod_1 = config.patches_2da[0].modifiers[1]
        self.assertIsInstance(mod_1, CopyRow2DA)
        assert isinstance(mod_1, CopyRow2DA)
        self.assertEqual("copy_row_1", mod_1.identifier)
        self.assertIsNone(mod_1.exclusive_column)

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

    def test_2da_copyrow_rowlabel(self):
        """Test that row label property is being loaded correctly."""
        vanilla_2da = TwoDA(["label"])
        vanilla_2da.add_row("0", {"label": "A"})

        modded_2da = TwoDA(["label"])
        modded_2da.add_row("0", {"label": "A"})
        modded_2da.add_row("123", {"label": "A"})
        modded_2da.add_row("1", {"label": "A"})

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
            CopyRow0=copy_row_0
            CopyRow1=copy_row_1

            [copy_row_0]
            RowIndex=0
            NewRowLabel=123
            [copy_row_1]
            RowIndex=0
            """
        ).strip()
        config: PatcherConfig = self._setupIniAndConfig(expected_ini)
        mod_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_0, CopyRow2DA)
        assert isinstance(mod_0, CopyRow2DA)

        self.assertEqual("copy_row_0", mod_0.identifier)
        self.assertEqual("123", mod_0.row_label)

        mod_1 = config.patches_2da[0].modifiers[1]
        self.assertIsInstance(mod_1, CopyRow2DA)
        assert isinstance(mod_1, CopyRow2DA)
        self.assertEqual("copy_row_1", mod_1.identifier)
        self.assertIsNone(mod_1.row_label)

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

    def test_2da_copyrow_store2da(self):
        """Test that 2DAMEMORY# data will be saved correctly."""
        vanilla_2da = TwoDA(["label"])
        vanilla_2da.add_row("0", {"label": "A"})

        modded_2da = TwoDA(["label"])
        modded_2da.add_row("0", {"label": "A"})
        modded_2da.add_row("1", {"label": "A"})

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
            CopyRow0=copy_row_0

            [copy_row_0]
            RowLabel=0
            2DAMEMORY0=RowIndex
            2DAMEMORY1=RowLabel
            2DAMEMORY2=label
            """
        ).strip()
        config: PatcherConfig = self._setupIniAndConfig(expected_ini)
        mod_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_0, CopyRow2DA)
        assert isinstance(mod_0, CopyRow2DA)

        # Apply and verify
        twoda = TwoDA(["label"])  # create row 0 to copy
        twoda.add_row("0", {"label": "A"})
        memory = PatcherMemory()
        mod_0.apply(twoda, memory)
        # The new row is added at index 1, so:
        # RowIndex: 1, RowLabel: "1", label: "A"
        self.assertEqual("1", memory.memory_2da[0])
        self.assertEqual("1", memory.memory_2da[1])
        self.assertEqual("A", memory.memory_2da[2])

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

    def test_2da_copyrow_cells(self):
        """Test that cells will be assigned properly."""
        vanilla_2da = TwoDA(["label", "dialog", "appearance"])
        vanilla_2da.add_row("0", {"label": "A", "dialog": "1", "appearance": "B"})

        modded_2da = TwoDA(["label", "dialog", "appearance"])
        modded_2da.add_row("0", {"label": "A", "dialog": "1", "appearance": "B"})
        modded_2da.add_row("1", {"label": "Test123", "dialog": "8", "appearance": "C"})

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
            CopyRow0=copy_row_0

            [copy_row_0]
            RowLabel=0
            label=Test123
            dialog=StrRef4
            appearance=2DAMEMORY5
            """
        ).strip()
        config: PatcherConfig = self._setupIniAndConfig(expected_ini)
        mod_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_0, CopyRow2DA)
        assert isinstance(mod_0, CopyRow2DA)

        # Reader-style checks
        self.assertIsInstance(mod_0.cells["label"], RowValueConstant)
        self.assertIsInstance(mod_0.cells["dialog"], RowValueTLKMemory)
        self.assertIsInstance(mod_0.cells["appearance"], RowValue2DAMemory)

        # Apply
        twoda = TwoDA(["label", "dialog", "appearance"])  # seed row 0
        twoda.add_row("0", {"label": "A", "dialog": "1", "appearance": "B"})
        memory = PatcherMemory()
        memory.memory_str[4] = 8
        memory.memory_2da[5] = "C"
        mod_0.apply(twoda, memory)
        self.assertEqual(2, twoda.get_height())
        self.assertEqual(["A", "Test123"], twoda.get_column("label"))
        self.assertEqual(["1", "8"], twoda.get_column("dialog"))
        self.assertEqual(["B", "C"], twoda.get_column("appearance"))

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

    def test_2da_copyrow_existing_rowindex(self):
        """Test copying rows by index duplicates the row as expected."""
        vanilla_2da = TwoDA(["Col1", "Col2"])
        vanilla_2da.add_row("0", {"Col1": "a", "Col2": "b"})
        vanilla_2da.add_row("1", {"Col1": "c", "Col2": "d"})

        modded_2da = TwoDA(["Col1", "Col2"])
        modded_2da.add_row("0", {"Col1": "a", "Col2": "b"})
        modded_2da.add_row("1", {"Col1": "c", "Col2": "d"})
        modded_2da.add_row("2", {"Col1": "a", "Col2": "X"})

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
            CopyRow0=copy_row_0

            [copy_row_0]
            RowIndex=0
            Col2=X
            """
        ).strip()
        config = self._setupIniAndConfig(expected_ini)
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})
        config.patches_2da[0].apply(twoda, PatcherMemory(), PatchLogger(), Game.K1)
        self.assertEqual(3, twoda.get_height())
        self.assertEqual(["a", "c", "a"], twoda.get_column("Col1"))
        self.assertEqual(["b", "d", "X"], twoda.get_column("Col2"))

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

    def test_2da_copyrow_existing_rowlabel(self):
        """Test copying rows by label duplicates expected row."""
        vanilla_2da = TwoDA(["Col1", "Col2"])
        vanilla_2da.add_row("0", {"Col1": "a", "Col2": "b"})
        vanilla_2da.add_row("1", {"Col1": "c", "Col2": "d"})

        modded_2da = TwoDA(["Col1", "Col2"])
        modded_2da.add_row("0", {"Col1": "a", "Col2": "b"})
        modded_2da.add_row("1", {"Col1": "c", "Col2": "d"})
        modded_2da.add_row("2", {"Col1": "c", "Col2": "X"})

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
            CopyRow0=copy_row_0

            [copy_row_0]
            RowLabel=1
            Col2=X
            """
        ).strip()
        config = self._setupIniAndConfig(expected_ini)
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})
        config.patches_2da[0].apply(twoda, PatcherMemory(), PatchLogger(), Game.K1)
        self.assertEqual(3, twoda.get_height())
        self.assertEqual(["a", "c", "c"], twoda.get_column("Col1"))
        self.assertEqual(["b", "d", "X"], twoda.get_column("Col2"))

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

    def test_2da_copyrow_exclusive_behaviour(self):
        """Test exclusive column logic for copy row operations."""
        vanilla_2da = TwoDA(["Col1", "Col2"])
        vanilla_2da.add_row("0", {"Col1": "a", "Col2": "b"})

        # Unique value should append
        modded_unique = TwoDA(["Col1", "Col2"])
        modded_unique.add_row("0", {"Col1": "a", "Col2": "b"})
        modded_unique.add_row("1", {"Col1": "c", "Col2": "d"})

        expected_unique = textwrap.dedent(
            """
            [Settings]
            LogLevel=3

            [InstallList]
            install_folder0=Override

            [install_folder0]
            File0=test_unique.2da

            [2DAList]
            Table0=test_unique.2da

            [test_unique.2da]
            CopyRow0=copy_row_0

            [copy_row_0]
            RowIndex=0
            ExclusiveColumn=Col1
            Col1=c
            Col2=d
            """
        ).strip()
        config_unique = self._setupIniAndConfig(expected_unique)
        twoda_unique = TwoDA(["Col1", "Col2"])
        twoda_unique.add_row("0", {"Col1": "a", "Col2": "b"})
        config_unique.patches_2da[0].apply(twoda_unique, PatcherMemory(), PatchLogger(), Game.K1)
        self.assertEqual(2, twoda_unique.get_height())

        generated_unique = self._generate_ini_from_diff(
            {
                "test_unique.2da": (
                    bytes_2da(vanilla_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
            {
                "test_unique.2da": (
                    bytes_2da(modded_unique, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
        )
        self._assert_generated_ini_equals(generated_unique, expected_unique)

        # Duplicate value should overwrite existing row
        modded_duplicate = TwoDA(["Col1", "Col2"])
        modded_duplicate.add_row("0", {"Col1": "a", "Col2": "b"})

        expected_duplicate = textwrap.dedent(
            """
            [Settings]
            LogLevel=3

            [InstallList]
            install_folder0=Override

            [install_folder0]
            File0=test_duplicate.2da

            [2DAList]
            Table0=test_duplicate.2da

            [test_duplicate.2da]
            CopyRow0=copy_row_0

            [copy_row_0]
            RowIndex=0
            ExclusiveColumn=Col1
            Col1=a
            Col2=X
            """
        ).strip()
        config_duplicate = self._setupIniAndConfig(expected_duplicate)
        twoda_duplicate = TwoDA(["Col1", "Col2"])
        twoda_duplicate.add_row("0", {"Col1": "a", "Col2": "b"})
        config_duplicate.patches_2da[0].apply(twoda_duplicate, PatcherMemory(), PatchLogger(), Game.K1)
        self.assertEqual(["a"], twoda_duplicate.get_column("Col1"))
        self.assertEqual(["X"], twoda_duplicate.get_column("Col2"))

        generated_duplicate = self._generate_ini_from_diff(
            {
                "test_duplicate.2da": (
                    bytes_2da(vanilla_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
            {
                "test_duplicate.2da": (
                    bytes_2da(modded_duplicate, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
        )
        self._assert_generated_ini_equals(generated_duplicate, expected_duplicate)

        # No exclusive column
        modded_none = TwoDA(["Col1", "Col2"])
        modded_none.add_row("0", {"Col1": "a", "Col2": "b"})
        modded_none.add_row("1", {"Col1": "c", "Col2": "d"})

        expected_none = textwrap.dedent(
            """
            [Settings]
            LogLevel=3

            [InstallList]
            install_folder0=Override

            [install_folder0]
            File0=test_none.2da

            [2DAList]
            Table0=test_none.2da

            [test_none.2da]
            CopyRow0=copy_row_0
            CopyRow1=copy_row_1

            [copy_row_0]
            RowIndex=0
            Col1=c
            Col2=d

            [copy_row_1]
            RowIndex=0
            RowLabel=r2
            Col1=e
            Col2=f
            """
        ).strip()
        config_none = self._setupIniAndConfig(expected_none)
        twoda_none = TwoDA(["Col1", "Col2"])
        twoda_none.add_row("0", {"Col1": "a", "Col2": "b"})
        config_none.patches_2da[0].apply(twoda_none, PatcherMemory(), PatchLogger(), Game.K1)
        self.assertEqual(3, twoda_none.get_height())

        generated_none = self._generate_ini_from_diff(
            {
                "test_none.2da": (
                    bytes_2da(vanilla_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
            {
                "test_none.2da": (
                    bytes_2da(modded_none, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
        )
        self._assert_generated_ini_equals(generated_none, expected_none)

    def test_2da_copyrow_assign_memory(self):
        """Test TLK/2DA memory assignments when copying rows."""
        vanilla_2da = TwoDA(["Col1", "Col2"])
        vanilla_2da.add_row("0", {"Col1": "a", "Col2": "1"})
        vanilla_2da.add_row("1", {"Col1": "c", "Col2": "2"})

        # TLK memory
        expected_tlk = textwrap.dedent(
            """
            [Settings]
            LogLevel=3

            [InstallList]
            install_folder0=Override

            [install_folder0]
            File0=test_tlk.2da

            [2DAList]
            Table0=test_tlk.2da

            [test_tlk.2da]
            CopyRow0=copy_row_0

            [copy_row_0]
            RowIndex=0
            Col2=StrRef0
            """
        ).strip()
        config_tlk = self._setupIniAndConfig(expected_tlk)
        memory = PatcherMemory()
        memory.memory_str[0] = 5
        twoda_tlk = TwoDA(["Col1", "Col2"])
        twoda_tlk.add_row("0", {"Col1": "a", "Col2": "1"})
        twoda_tlk.add_row("1", {"Col1": "c", "Col2": "2"})
        config_tlk.patches_2da[0].apply(twoda_tlk, memory, PatchLogger(), Game.K1)
        self.assertEqual(["a", "c", "a"], twoda_tlk.get_column("Col1"))
        self.assertEqual(["1", "2", "5"], twoda_tlk.get_column("Col2"))

        generated_tlk = self._generate_ini_from_diff(
            {
                "test_tlk.2da": (
                    bytes_2da(vanilla_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
            {
                "test_tlk.2da": (
                    bytes_2da(twoda_tlk, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
        )
        self._assert_generated_ini_equals(generated_tlk, expected_tlk)

        # 2DA memory
        expected_2da = textwrap.dedent(
            """
            [Settings]
            LogLevel=3

            [InstallList]
            install_folder0=Override

            [install_folder0]
            File0=test_memory.2da

            [2DAList]
            Table0=test_memory.2da

            [test_memory.2da]
            CopyRow0=copy_row_0

            [copy_row_0]
            RowIndex=0
            Col2=2DAMEMORY0
            """
        ).strip()
        config_2da = self._setupIniAndConfig(expected_2da)
        memory = PatcherMemory()
        memory.memory_2da[0] = "5"
        twoda_2da = TwoDA(["Col1", "Col2"])
        twoda_2da.add_row("0", {"Col1": "a", "Col2": "1"})
        twoda_2da.add_row("1", {"Col1": "c", "Col2": "2"})
        config_2da.patches_2da[0].apply(twoda_2da, memory, PatchLogger(), Game.K1)
        self.assertEqual(["a", "c", "a"], twoda_2da.get_column("Col1"))
        self.assertEqual(["1", "2", "5"], twoda_2da.get_column("Col2"))

        generated_2da = self._generate_ini_from_diff(
            {
                "test_memory.2da": (
                    bytes_2da(vanilla_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
            {
                "test_memory.2da": (
                    bytes_2da(twoda_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
        )
        self._assert_generated_ini_equals(generated_2da, expected_2da)

    def test_2da_copyrow_store_rowindex(self):
        """Test storing new row index when copying."""
        vanilla_2da = TwoDA(["Col1", "Col2"])
        vanilla_2da.add_row("0", {"Col1": "a", "Col2": "b"})
        vanilla_2da.add_row("1", {"Col1": "c", "Col2": "d"})

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
            CopyRow0=copy_row_0

            [copy_row_0]
            RowIndex=0
            2DAMEMORY5=RowIndex
            """
        ).strip()
        config = self._setupIniAndConfig(expected_ini)
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})
        memory = PatcherMemory()
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)
        self.assertEqual("2", memory.memory_2da[5])

        generated_ini = self._generate_ini_from_diff(
            {
                "test.2da": (
                    bytes_2da(vanilla_2da, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
            {
                "test.2da": (
                    bytes_2da(twoda, file_format=ResourceType.TwoDA_JSON).decode(),
                    ResourceType.TwoDA_JSON,
                )
            },
        )
        self._assert_generated_ini_equals(generated_ini, expected_ini)

    # endregion

    # region SSF
    def test_ssf_replace(self):
        """Test that the replace file boolean is registered correctly."""
        vanilla_ssf = SSF()
        modded_ssf_primary = SSF()
        modded_ssf_replace = SSF()
        modded_ssf_replace.set_data(SSFSound.BATTLE_CRY_1, 42)

        expected_ini = textwrap.dedent(
            """
            [Settings]
            LogLevel=3
            
            [InstallList]
            install_folder0=Override
            
            [install_folder0]
            File0=test1.ssf
            
            [SSFList]
            File0=test1.ssf
            Replace0=test2.ssf

            [test1.ssf]
            [test2.ssf]
            """
        ).strip()
        config: PatcherConfig = self._setupIniAndConfig(expected_ini)
        self.assertFalse(config.patches_ssf[0].replace_file)
        self.assertTrue(config.patches_ssf[1].replace_file)

        # Apply (no modifiers, just ensure no crash)
        ssf = SSF()
        memory = PatcherMemory()
        for p in config.patches_ssf:
            p.apply(ssf, memory, PatchLogger(), Game.K1)

        generated_ini = self._generate_ini_from_diff(
            {
                "test1.ssf": (
                    bytes_ssf(vanilla_ssf, file_format=ResourceType.SSF_XML).decode(),
                    ResourceType.SSF_XML,
                )
            },
            {
                "test1.ssf": (
                    bytes_ssf(modded_ssf_primary, file_format=ResourceType.SSF_XML).decode(),
                    ResourceType.SSF_XML,
                ),
                "test2.ssf": (
                    bytes_ssf(modded_ssf_replace, file_format=ResourceType.SSF_XML).decode(),
                    ResourceType.SSF_XML,
                ),
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

    def test_ssf_stored_2da(self):
        """Test that the set sound as 2DAMEMORY value is registered correctly."""
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
            Battlecry 1=2DAMEMORY5
            Battlecry 2=2DAMEMORY6
            """
        ).strip()
        config: PatcherConfig = self._setupIniAndConfig(expected_ini)
        ssf = SSF()
        memory = PatcherMemory()
        memory.memory_2da[5] = "123"
        memory.memory_2da[6] = "456"
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

    def test_ssf_stored_tlk(self):
        """Test that the set sound as StrRef is registered correctly."""
        vanilla_ssf = SSF()
        modded_ssf = SSF()
        modded_ssf.set_data(SSFSound.BATTLE_CRY_1, 5)
        modded_ssf.set_data(SSFSound.BATTLE_CRY_2, 6)

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
            Battlecry 1=StrRef5
            Battlecry 2=StrRef6
            """
        ).strip()
        config: PatcherConfig = self._setupIniAndConfig(expected_ini)
        ssf = SSF()
        memory = PatcherMemory()
        memory.memory_str[5] = 5
        memory.memory_str[6] = 6
        config.patches_ssf[0].apply(ssf, memory, PatchLogger(), Game.K1)
        self.assertEqual(5, ssf.get(SSFSound.BATTLE_CRY_1))
        self.assertEqual(6, ssf.get(SSFSound.BATTLE_CRY_2))

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

    # region TLK
    def test_tlk_appendfile_functionality(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mod_path = Path(tmpdir)

            modified_tlk = self.create_test_tlk(
                {
                    0: {"text": "Modified 0", "voiceover": "vo_mod_0"},
                    1: {"text": "Modified 1", "voiceover": "vo_mod_1"},
                    2: {"text": "Modified 2", "voiceover": "vo_mod_2"},
                    3: {"text": "Modified 3", "voiceover": "vo_mod_3"},
                    4: {"text": "Modified 4", "voiceover": "vo_mod_4"},
                    5: {"text": "Modified 5", "voiceover": "vo_mod_5"},
                    6: {"text": "Modified 6", "voiceover": "vo_mod_6"},
                }
            )
            write_tlk(modified_tlk, str(mod_path / "tlk_modifications_file.tlk"), ResourceType.TLK)

            vanilla_tlk = self.create_test_tlk(
                {
                    0: {"text": "Entry 0", "voiceover": "vo_0"},
                    1: {"text": "Entry 1", "voiceover": "vo_1"},
                    2: {"text": "Entry 2", "voiceover": "vo_2"},
                    3: {"text": "Entry 3", "voiceover": "vo_3"},
                    4: {"text": "Entry 4", "voiceover": "vo_4"},
                    5: {"text": "Entry 5", "voiceover": "vo_5"},
                    6: {"text": "Entry 6", "voiceover": "vo_6"},
                }
            )

            expected_ini = textwrap.dedent(
                """
                [TLKList]
                AppendFile4=tlk_modifications_file.tlk

                [tlk_modifications_file.tlk]
                0=4
                1=5
                2=6
                """
            ).strip()
            config = self._setupIniAndConfig(expected_ini, mod_path)
            for modifier in config.patches_tlk.modifiers:
                modifier.load()

            self.assertEqual(len(config.patches_tlk.modifiers), 3)
            modifiers_dict = {mod.token_id: {"text": mod.text, "voiceover": mod.sound, "replace": mod.is_replacement} for mod in config.patches_tlk.modifiers}
            self.assertDictEqual(
                modifiers_dict,
                {
                    0: {"text": "Modified 4", "voiceover": ResRef("vo_mod_4"), "replace": False},
                    1: {"text": "Modified 5", "voiceover": ResRef("vo_mod_5"), "replace": False},
                    2: {"text": "Modified 6", "voiceover": ResRef("vo_mod_6"), "replace": False},
                },
            )

            generated_ini = self._generate_ini_from_diff(
                {
                    "tlk_modifications_file.tlk": (
                        bytes_tlk(vanilla_tlk, file_format=ResourceType.TLK_XML).decode(),
                        ResourceType.TLK_XML,
                    )
                },
                {
                    "tlk_modifications_file.tlk": (
                        bytes_tlk(modified_tlk, file_format=ResourceType.TLK_XML).decode(),
                        ResourceType.TLK_XML,
                    )
                },
            )
            self._assert_generated_ini_equals(generated_ini, expected_ini)

    def test_tlk_strref_default_functionality(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mod_path = Path(tmpdir)
            modified_tlk = self.create_test_tlk(
                {
                    0: {"text": "Modified 0", "voiceover": "vo_mod_0"},
                    1: {"text": "Modified 1", "voiceover": "vo_mod_1"},
                    2: {"text": "Modified 2", "voiceover": "vo_mod_2"},
                }
            )
            write_tlk(modified_tlk, str(mod_path / "append.tlk"), ResourceType.TLK)

            vanilla_tlk = self.create_test_tlk(
                {
                    0: {"text": "Entry 0", "voiceover": "vo_0"},
                    1: {"text": "Entry 1", "voiceover": "vo_1"},
                    2: {"text": "Entry 2", "voiceover": "vo_2"},
                }
            )

            expected_ini = textwrap.dedent(
                """
                [TLKList]
                StrRef7=0
                StrRef8=1
                StrRef9=2
                """
            ).strip()
            config = self._setupIniAndConfig(expected_ini, mod_path)
            assert isinstance(config.patches_tlk, ModificationsTLK)
            self.assertIsInstance(config.patches_tlk, ModificationsTLK)
            assert isinstance(config.patches_tlk.modifiers[0], ModifyTLK)
            self.assertIsInstance(config.patches_tlk.modifiers[0], ModifyTLK)
            assert isinstance(config.patches_tlk.modifiers[1], ModifyTLK)
            self.assertIsInstance(config.patches_tlk.modifiers[1], ModifyTLK)
            assert isinstance(config.patches_tlk.modifiers[2], ModifyTLK)
            self.assertIsInstance(config.patches_tlk.modifiers[2], ModifyTLK)
            dialog_tlk = TLK()
            memory = PatcherMemory()
            config.patches_tlk.apply(dialog_tlk, memory, PatchLogger(), Game.K1)
            dialog_tlk_entry_0 = dialog_tlk.get(0)
            assert isinstance(dialog_tlk_entry_0, TLKEntry), "Dialog TLK entry 0 is not a TLKEntry"
            self.assertEqual("Modified 0", dialog_tlk_entry_0.text)
            dialog_tlk_entry_1 = dialog_tlk.get(1)
            assert isinstance(dialog_tlk_entry_1, TLKEntry), "Dialog TLK entry 1 is not a TLKEntry"
            self.assertEqual("Modified 1", dialog_tlk_entry_1.text)
            dialog_tlk_entry_2 = dialog_tlk.get(2)
            assert isinstance(dialog_tlk_entry_2, TLKEntry), "Dialog TLK entry 2 is not a TLKEntry"
            self.assertEqual("Modified 2", dialog_tlk_entry_2.text)

            generated_ini = self._generate_ini_from_diff(
                {
                    "append.tlk": (
                        bytes_tlk(vanilla_tlk, file_format=ResourceType.TLK_XML).decode(),
                        ResourceType.TLK_XML,
                    )
                },
                {
                    "append.tlk": (
                        bytes_tlk(modified_tlk, file_format=ResourceType.TLK_XML).decode(),
                        ResourceType.TLK_XML,
                    )
                },
            )
            self._assert_generated_ini_equals(generated_ini, expected_ini)

    def test_tlk_complex_changes(self):
        ini_text = """
        [Settings]
        LogLevel=3
        
        [InstallList]
        install_folder0=Override
        
        [install_folder0]
        File0=complex.tlk
        
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
        self._setupTLK()
        self.config: PatcherConfig = self._setupIniAndConfig(ini_text, self.tslpatchdata_path)

        modifiers2: list[ModifyTLK] = self.config.patches_tlk.modifiers.copy()
        for modifier in modifiers2:
            modifier.load()
        self.assertEqual(len(self.config.patches_tlk.modifiers), 26)
        modifiers_dict2: dict[int, dict[str, str | ResRef | bool]] = {
            mod.token_id: {"text": mod.text, "voiceover": mod.sound, "is_replacement": mod.is_replacement} for mod in modifiers2
        }
        for k in modifiers_dict2.copy():
            modifiers_dict2[k].pop("is_replacement")

        self.maxDiff = None
        self.assertDictEqual(
            modifiers_dict2,
            {
                0: {"text": "Yavin", "voiceover": ResRef.from_blank()},
                1: {
                    "text": "Climate: Artificially Controled\nTerrain: Space Station\nDocking: Orbital Docking\nNative Species: Unknown",
                    "voiceover": ResRef.from_blank(),
                },
                2: {"text": "Tatooine", "voiceover": ResRef.from_blank()},
                3: {
                    "text": "Climate: Arid\nTerrain: Desert\nDocking: Anchorhead Spaceport\nNative Species: Unknown",
                    "voiceover": ResRef.from_blank(),
                },
                4: {"text": "Manaan", "voiceover": ResRef.from_blank()},
                5: {
                    "text": "Climate: Temperate\nTerrain: Ocean\nDocking: Ahto City Docking Bay\nNative Species: Selkath",
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
                    "text": "Climate: Temperate\nTerrain: Decaying urban zones\nDocking: Refugee Landing Pad\nNative Species: None",
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
                    "text": "Climate: Temperate\nTerrain: Grasslands\nDocking: Khoonda Plains Settlement\nNative Species: None",
                    "voiceover": ResRef.from_blank(),
                },
                123728: {
                    "text": "Climate: Tectonic-Generated Storms\nTerrain: Shattered Planetoid\nDocking: No Docking Facilities Present\nNative Species: None",
                    "voiceover": ResRef.from_blank(),
                },
                123730: {
                    "text": "Climate: Arid\nTerrain: Volcanic\nDocking: Dreshae Settlement\nNative Species: Unknown",
                    "voiceover": ResRef.from_blank(),
                },
                124112: {
                    "text": "Climate: Artificially Maintained \nTerrain: Droid Cityscape\nDocking: Landing Arm\nNative Species: Unknown",
                    "voiceover": ResRef.from_blank(),
                },
                125863: {
                    "text": "Climate: Artificially Maintained\nTerrain: Space Station\nDocking: Landing Zone\nNative Species: None",
                    "voiceover": ResRef.from_blank(),
                },
            },
        )

        generated_ini = self._generate_ini_from_diff(
            {
                "complex.tlk": (
                    bytes_tlk(self.test_tlk_data, file_format=ResourceType.TLK_XML).decode(),
                    ResourceType.TLK_XML,
                )
            },
            {
                "complex.tlk": (
                    bytes_tlk(self.modified_tlk_data, file_format=ResourceType.TLK_XML).decode(),
                    ResourceType.TLK_XML,
                )
            },
        )
        self._assert_generated_ini_equals(generated_ini, ini_text.strip())

    def test_tlk_replacefile_functionality(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mod_path = Path(tmpdir)
            modified_tlk = self.create_test_tlk(
                {
                    2: {"text": "Modified 2", "voiceover": "vo_mod_2"},
                    3: {"text": "Modified 3", "voiceover": "vo_mod_3"},
                    4: {"text": "Modified 4", "voiceover": "vo_mod_4"},
                    5: {"text": "Modified 5", "voiceover": "vo_mod_5"},
                    6: {"text": "Modified 6", "voiceover": "vo_mod_6"},
                }
            )
            write_tlk(modified_tlk, str(mod_path / "tlk_modifications_file.tlk"), ResourceType.TLK)

            vanilla_tlk = self.create_test_tlk(
                {
                    0: {"text": "Entry 0", "voiceover": "vo_0"},
                    1: {"text": "Entry 1", "voiceover": "vo_1"},
                    2: {"text": "Entry 2", "voiceover": "vo_2"},
                    3: {"text": "Entry 3", "voiceover": "vo_3"},
                    4: {"text": "Entry 4", "voiceover": "vo_4"},
                    5: {"text": "Entry 5", "voiceover": "vo_5"},
                    6: {"text": "Entry 6", "voiceover": "vo_6"},
                }
            )

            expected_ini = textwrap.dedent(
                """
                [TLKList]
                Replacenothingafterreplaceischecked=tlk_modifications_file.tlk

                [tlk_modifications_file.tlk]
                0=2
                1=3
                2=4
                3=5
                4=6
                """
            ).strip()
            config = self._setupIniAndConfig(expected_ini, mod_path)
            assert isinstance(config.patches_tlk, ModificationsTLK)
            self.assertIsInstance(config.patches_tlk, ModificationsTLK)
            expected_modifiers = 5
            for i in range(expected_modifiers):
                assert isinstance(config.patches_tlk.modifiers[i], ModifyTLK)
                self.assertIsInstance(config.patches_tlk.modifiers[i], ModifyTLK)
            self.assertEqual(len(config.patches_tlk.modifiers), expected_modifiers)
            for modifier in config.patches_tlk.modifiers:
                modifier.load()
            token_to_text = {m.token_id: m.text for m in config.patches_tlk.modifiers}
            # The mapping in the INI is: [tlk_modifications_file.tlk] 0=2, 1=3, 2=4, 3=5, 4=6
            # So, token 0 gets text from entry 2, token 1 from entry 3, etc.
            # But the test_tlk_modifications_file.tlk only has entries for 2,3,4,5,6, so tokens 0,1,2 get 4,5,6, tokens 3,4 get "" (empty)
            expected = {
                0: "Modified 4",
                1: "Modified 5",
                2: "Modified 6",
                3: "",
                4: "",
            }
            self.assertEqual(expected, token_to_text)

            generated_ini = self._generate_ini_from_diff(
                {
                    "tlk_modifications_file.tlk": (
                        bytes_tlk(vanilla_tlk, file_format=ResourceType.TLK_XML).decode(),
                        ResourceType.TLK_XML,
                    )
                },
                {
                    "tlk_modifications_file.tlk": (
                        bytes_tlk(modified_tlk, file_format=ResourceType.TLK_XML).decode(),
                        ResourceType.TLK_XML,
                    )
                },
            )
            self._assert_generated_ini_equals(generated_ini, expected_ini)

    # endregion


if __name__ == "__main__":
    unittest.main()
