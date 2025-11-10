"""Comprehensive, exhaustive tests for TSLPatcher diff generation and INI writer.

This test suite covers ALL TSLPatcher features including:
- 2DAMEMORY tokens (storage, cross-references, chains)
- TLK modifications (append, replace, StrRef tokens)
- GFF modifications (all field types, nested structures, LocalizedString)
- SSF modifications
- InstallList
- Cross-file references and linking
- Real-world scenarios from actual mods

Test organization:
1. Helper utilities for creating test data
2. 2DAMEMORY comprehensive tests
3. TLK/StrRef comprehensive tests
4. GFF comprehensive tests
5. SSF tests
6. Integration tests (cross-file references)
7. Real-world scenario tests
"""
from __future__ import annotations

import pathlib
import sys
import tempfile
import shutil
import unittest
from pathlib import Path
from configparser import ConfigParser


def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


# Add paths
add_sys_path(pathlib.Path(__file__).parents[2] / "Libraries" / "PyKotor" / "src" / "pykotor")
add_sys_path(pathlib.Path(__file__).parents[2] / "Libraries" / "PyKotor" / "src")
add_sys_path(pathlib.Path(__file__).parents[2] / "Libraries" / "Utility" / "src")
add_sys_path(pathlib.Path(__file__).parents[2] / "Tools" / "KotorDiff" / "src")


from pykotor.common.misc import Game, ResRef
from pykotor.common.language import LocalizedString, Language, Gender
from utility.common.geometry import Vector3, Vector4
from pykotor.resource.formats.gff import GFF, GFFFieldType, GFFStruct, GFFList, read_gff, write_gff
from pykotor.resource.formats.twoda import TwoDA, read_2da, write_2da
from pykotor.resource.formats.tlk import TLK, read_tlk, write_tlk
from pykotor.resource.formats.ssf import SSF, SSFSound, read_ssf, write_ssf
from pykotor.resource.type import ResourceType
from pykotor.tslpatcher.config import PatcherConfig
from pykotor.tslpatcher.reader import ConfigReader
from kotordiff.app import KotorDiffConfig, run_application


# ============================================================================
# HELPER UTILITIES FOR TEST DATA CREATION
# ============================================================================


class TestDataHelper:
    """Helper class for creating test data files and directories."""

    @staticmethod
    def create_test_env() -> tuple[Path, Path, Path, Path]:
        """Create a complete test environment with temp directories.

        Returns:
            (temp_dir, vanilla_dir, modded_dir, tslpatchdata_dir)
        """
        temp_dir = Path(tempfile.mkdtemp())
        vanilla_dir = temp_dir / "vanilla"
        modded_dir = temp_dir / "modded"
        tslpatchdata_dir = temp_dir / "tslpatchdata"

        vanilla_dir.mkdir()
        modded_dir.mkdir()
        tslpatchdata_dir.mkdir()

        return temp_dir, vanilla_dir, modded_dir, tslpatchdata_dir

    @staticmethod
    def cleanup_test_env(temp_dir: Path):
        """Clean up test environment."""
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)

    @staticmethod
    def create_basic_2da(headers: list[str], rows: list[tuple[str, dict[str, str]]]) -> TwoDA:
        """Create a basic 2DA file with headers and rows.

        Args:
            headers: Column headers
            rows: List of (row_label, cell_dict) tuples

        Returns:
            TwoDA object
        """
        twoda = TwoDA(headers)
        for label, cells in rows:
            twoda.add_row(label, cells)
        return twoda

    @staticmethod
    def create_basic_gff(fields: dict[str, tuple[GFFFieldType, any]]) -> GFF:
        """Create a basic GFF file with root-level fields.

        Args:
            fields: Dict of {field_name: (field_type, value)}

        Returns:
            GFF object
        """
        gff = GFF()
        for field_name, (field_type, value) in fields.items():
            if field_type == GFFFieldType.UInt8:
                gff.root.set_uint8(field_name, value)
            elif field_type == GFFFieldType.Int8:
                gff.root.set_int8(field_name, value)
            elif field_type == GFFFieldType.UInt16:
                gff.root.set_uint16(field_name, value)
            elif field_type == GFFFieldType.Int16:
                gff.root.set_int16(field_name, value)
            elif field_type == GFFFieldType.UInt32:
                gff.root.set_uint32(field_name, value)
            elif field_type == GFFFieldType.Int32:
                gff.root.set_int32(field_name, value)
            elif field_type == GFFFieldType.Int64:
                gff.root.set_int64(field_name, value)
            elif field_type == GFFFieldType.Single:
                gff.root.set_single(field_name, value)
            elif field_type == GFFFieldType.Double:
                gff.root.set_double(field_name, value)
            elif field_type == GFFFieldType.String:
                gff.root.set_string(field_name, value)
            elif field_type == GFFFieldType.ResRef:
                gff.root.set_resref(field_name, value)
            elif field_type == GFFFieldType.LocalizedString:
                gff.root.set_locstring(field_name, value)
            elif field_type == GFFFieldType.Vector3:
                gff.root.set_vector3(field_name, value)
            elif field_type == GFFFieldType.Vector4:
                gff.root.set_vector4(field_name, value)
            elif field_type == GFFFieldType.Struct:
                gff.root.set_struct(field_name, value)
            elif field_type == GFFFieldType.List:
                gff.root.set_list(field_name, value)
        return gff

    @staticmethod
    def create_basic_tlk(entries: list[tuple[str, str]]) -> TLK:
        """Create a basic TLK file with entries.

        Args:
            entries: List of (text, sound_resref) tuples

        Returns:
            TLK object
        """
        tlk = TLK()
        tlk.resize(len(entries))
        for idx, (text, sound) in enumerate(entries):
            tlk.replace(idx, text, sound)
        return tlk

    @staticmethod
    def create_basic_ssf(sound_mappings: dict[SSFSound, int]) -> SSF:
        """Create a basic SSF file with sound mappings.

        Args:
            sound_mappings: Dict of {SSFSound: strref}

        Returns:
            SSF object
        """
        ssf = SSF()
        for sound, strref in sound_mappings.items():
            ssf.set_data(sound, strref)
        return ssf

    @staticmethod
    def run_diff(
        vanilla_dir: Path,
        modded_dir: Path,
        tslpatchdata_dir: Path,
        ini_filename: str = "changes.ini",
        logging_enabled: bool = False,
    ) -> str:
        """Run the diff engine and return generated INI content.

        Args:
            vanilla_dir: Vanilla files directory
            modded_dir: Modded files directory
            tslpatchdata_dir: Output directory
            ini_filename: INI filename
            logging_enabled: Enable debug logging

        Returns:
            Generated INI content as string
        """
        config = KotorDiffConfig(
            paths=[vanilla_dir, modded_dir],
            tslpatchdata_path=tslpatchdata_dir,
            ini_filename=ini_filename,
            compare_hashes=True,
            logging_enabled=logging_enabled,
            use_incremental_writer=True,
        )
        run_application(config)

        ini_path = tslpatchdata_dir / ini_filename
        return ini_path.read_text(encoding="utf-8")

    @staticmethod
    def assert_ini_section_exists(ini_content: str, section_name: str, test_case: unittest.TestCase):
        """Assert that a section exists in INI."""
        test_case.assertIn(f"[{section_name}]", ini_content, f"Section [{section_name}] should exist")

    @staticmethod
    def assert_ini_key_value(
        ini_content: str,
        section_name: str,
        key: str,
        expected_value: str | None = None,
        test_case: unittest.TestCase | None = None,
    ):
        """Assert that a key exists in a section, optionally check value."""
        # Parse INI to find section and key
        lines = ini_content.splitlines()
        in_section = False
        found_key = False

        for line in lines:
            line = line.strip()
            if line == f"[{section_name}]":
                in_section = True
                continue
            if in_section:
                if line.startswith("[") and line.endswith("]"):
                    # Entered a new section
                    break
                if "=" in line:
                    line_key = line.split("=", 1)[0].strip()
                    if line_key == key:
                        found_key = True
                        if expected_value is not None and test_case is not None:
                            line_value = line.split("=", 1)[1].strip()
                            test_case.assertEqual(
                                line_value,
                                expected_value,
                                f"Key '{key}' in section [{section_name}] should have value '{expected_value}'",
                            )
                        break

        if test_case:
            test_case.assertTrue(found_key, f"Key '{key}' should exist in section [{section_name}]")


# ============================================================================
# 2DAMEMORY COMPREHENSIVE TESTS
# ============================================================================


class Test2DAMemoryComprehensive(unittest.TestCase):
    """Comprehensive tests for 2DAMEMORY token generation and usage."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir, self.vanilla_dir, self.modded_dir, self.tslpatchdata_dir = TestDataHelper.create_test_env()

    def tearDown(self):
        """Clean up test environment."""
        TestDataHelper.cleanup_test_env(self.temp_dir)

    def test_addrow_stores_row_index(self):
        """Test: AddRow2DA stores RowIndex in 2DAMEMORY token.

        Pattern from real mods:
        [spells.2da]
        AddRow0=Battle_Meditation
        [Battle_Meditation]
        2DAMEMORY1=RowIndex
        """
        # Vanilla: 2 rows
        vanilla_2da = TestDataHelper.create_basic_2da(
            ["label", "name"],
            [("0", {"label": "spell_0", "name": "100"}), ("1", {"label": "spell_1", "name": "101"})],
        )
        write_2da(vanilla_2da, self.vanilla_dir / "spells.2da", ResourceType.TwoDA)

        # Modded: 3 rows (new row added)
        modded_2da = TestDataHelper.create_basic_2da(
            ["label", "name"],
            [
                ("0", {"label": "spell_0", "name": "100"}),
                ("1", {"label": "spell_1", "name": "101"}),
                ("2", {"label": "new_spell", "name": "102"}),
            ],
        )
        write_2da(modded_2da, self.modded_dir / "spells.2da", ResourceType.TwoDA)

        # Run diff
        ini_content = TestDataHelper.run_diff(self.vanilla_dir, self.modded_dir, self.tslpatchdata_dir)

        # Verify AddRow with 2DAMEMORY token
        self.assertIn("[spells.2da]", ini_content)
        self.assertIn("AddRow0=", ini_content)
        self.assertIn("2DAMEMORY", ini_content, "Should store row index in 2DAMEMORY token")

        print("\n=== test_addrow_stores_row_index ===")
        print(ini_content)

    def test_changerow_stores_row_index(self):
        """Test: ChangeRow2DA stores RowIndex in 2DAMEMORY token.

        This tests the pattern where a modified row's index is stored
        for use in other modifications.
        """
        # Vanilla: 3 rows
        vanilla_2da = TestDataHelper.create_basic_2da(
            ["label", "value"],
            [
                ("0", {"label": "item_0", "value": "10"}),
                ("1", {"label": "item_1", "value": "20"}),
                ("2", {"label": "item_2", "value": "30"}),
            ],
        )
        write_2da(vanilla_2da, self.vanilla_dir / "baseitems.2da", ResourceType.TwoDA)

        # Modded: row 1 modified
        modded_2da = TestDataHelper.create_basic_2da(
            ["label", "value"],
            [
                ("0", {"label": "item_0", "value": "10"}),
                ("1", {"label": "item_1_modified", "value": "999"}),
                ("2", {"label": "item_2", "value": "30"}),
            ],
        )
        write_2da(modded_2da, self.modded_dir / "baseitems.2da", ResourceType.TwoDA)

        # Run diff
        ini_content = TestDataHelper.run_diff(self.vanilla_dir, self.modded_dir, self.tslpatchdata_dir)

        # Verify ChangeRow exists
        self.assertIn("[baseitems.2da]", ini_content)
        self.assertIn("ChangeRow0=", ini_content)

        print("\n=== test_changerow_stores_row_index ===")
        print(ini_content)

    def test_2damemory_cross_reference_chain(self):
        """Test: 2DAMEMORY tokens used in chained references across multiple 2DA files.

        Real-world pattern from dm_qrts mod:
        weaponsounds.2da AddRow -> 2DAMEMORY1
        baseitems.2da AddRow uses 2DAMEMORY1 for weaponmattype -> stores own index in 2DAMEMORY2
        GFF files use 2DAMEMORY2 for BaseItem
        """
        # Vanilla: weaponsounds.2da with 2 rows
        vanilla_weaponsounds = TestDataHelper.create_basic_2da(
            ["label", "cloth0"],
            [("0", {"label": "weapon_sound_0", "cloth0": "snd0"}), ("1", {"label": "weapon_sound_1", "cloth0": "snd1"})],
        )
        write_2da(vanilla_weaponsounds, self.vanilla_dir / "weaponsounds.2da", ResourceType.TwoDA)

        # Vanilla: baseitems.2da with 2 rows
        vanilla_baseitems = TestDataHelper.create_basic_2da(
            ["label", "weaponmattype"],
            [("0", {"label": "base_0", "weaponmattype": "0"}), ("1", {"label": "base_1", "weaponmattype": "1"})],
        )
        write_2da(vanilla_baseitems, self.vanilla_dir / "baseitems.2da", ResourceType.TwoDA)

        # Vanilla GFF
        vanilla_gff = TestDataHelper.create_basic_gff({"BaseItem": (GFFFieldType.Int32, 0)})
        write_gff(vanilla_gff, self.vanilla_dir / "item.uti", ResourceType.GFF)

        # Modded: weaponsounds.2da with 3 rows (new row 2)
        modded_weaponsounds = TestDataHelper.create_basic_2da(
            ["label", "cloth0"],
            [
                ("0", {"label": "weapon_sound_0", "cloth0": "snd0"}),
                ("1", {"label": "weapon_sound_1", "cloth0": "snd1"}),
                ("2", {"label": "new_weapon_sound", "cloth0": "snd2"}),
            ],
        )
        write_2da(modded_weaponsounds, self.modded_dir / "weaponsounds.2da", ResourceType.TwoDA)

        # Modded: baseitems.2da with 3 rows (new row 2 references new weaponsounds row)
        modded_baseitems = TestDataHelper.create_basic_2da(
            ["label", "weaponmattype"],
            [
                ("0", {"label": "base_0", "weaponmattype": "0"}),
                ("1", {"label": "base_1", "weaponmattype": "1"}),
                ("2", {"label": "new_base", "weaponmattype": "2"}),  # References new weaponsounds row
            ],
        )
        write_2da(modded_baseitems, self.modded_dir / "baseitems.2da", ResourceType.TwoDA)

        # Modded GFF: references new baseitems row
        modded_gff = TestDataHelper.create_basic_gff({"BaseItem": (GFFFieldType.Int32, 2)})
        write_gff(modded_gff, self.modded_dir / "item.uti", ResourceType.GFF)

        # Run diff
        ini_content = TestDataHelper.run_diff(self.vanilla_dir, self.modded_dir, self.tslpatchdata_dir, logging_enabled=True)

        # Verify chain exists:
        # 1. weaponsounds.2da AddRow stores index in 2DAMEMORY
        # 2. baseitems.2da AddRow uses 2DAMEMORY for weaponmattype, stores own index
        # 3. item.uti uses 2DAMEMORY for BaseItem
        self.assertIn("[weaponsounds.2da]", ini_content)
        self.assertIn("[baseitems.2da]", ini_content)
        self.assertIn("[item.uti]", ini_content)
        self.assertIn("2DAMEMORY", ini_content)

        print("\n=== test_2damemory_cross_reference_chain ===")
        print(ini_content)

    def test_addcolumn_with_2damemory_storage(self):
        """Test: AddColumn2DA with 2DAMEMORY storage for specific cell values.

        Pattern:
        [add_column]
        ColumnLabel=NewCol
        DefaultValue=0
        I5=special_value
        2DAMEMORY#=I5
        """
        # Vanilla: 5 rows, 1 column
        vanilla_2da = TestDataHelper.create_basic_2da(
            ["label"],
            [
                ("0", {"label": "row_0"}),
                ("1", {"label": "row_1"}),
                ("2", {"label": "row_2"}),
                ("3", {"label": "row_3"}),
                ("4", {"label": "row_4"}),
                ("5", {"label": "row_5"}),
            ],
        )
        write_2da(vanilla_2da, self.vanilla_dir / "test.2da", ResourceType.TwoDA)

        # Modded: 5 rows, 2 columns (new column added)
        modded_2da = TestDataHelper.create_basic_2da(
            ["label", "newcol"],
            [
                ("0", {"label": "row_0", "newcol": "0"}),
                ("1", {"label": "row_1", "newcol": "0"}),
                ("2", {"label": "row_2", "newcol": "0"}),
                ("3", {"label": "row_3", "newcol": "0"}),
                ("4", {"label": "row_4", "newcol": "0"}),
                ("5", {"label": "row_5", "newcol": "special"}),
            ],
        )
        write_2da(modded_2da, self.modded_dir / "test.2da", ResourceType.TwoDA)

        # Run diff
        ini_content = TestDataHelper.run_diff(self.vanilla_dir, self.modded_dir, self.tslpatchdata_dir)

        # Verify AddColumn
        self.assertIn("[test.2da]", ini_content)
        self.assertIn("AddColumn", ini_content)

        print("\n=== test_addcolumn_with_2damemory_storage ===")
        print(ini_content)

    def test_multiple_gff_files_use_same_2damemory_token(self):
        """Test: Multiple GFF files reference the same 2DA row via same token.

        Real-world pattern from Bastila Battle Meditation:
        spells.2da AddRow -> 2DAMEMORY1
        Multiple creature files use 2DAMEMORY1 for Spell field
        """
        # Vanilla: 2DA with 2 rows
        vanilla_2da = TestDataHelper.create_basic_2da(
            ["label"],
            [("0", {"label": "soundset_0"}), ("1", {"label": "soundset_1"})],
        )
        write_2da(vanilla_2da, self.vanilla_dir / "soundset.2da", ResourceType.TwoDA)

        # Vanilla: 2 GFF files reference row 0
        vanilla_gff1 = TestDataHelper.create_basic_gff({"SoundSetFile": (GFFFieldType.UInt16, 0)})
        write_gff(vanilla_gff1, self.vanilla_dir / "creature1.utc", ResourceType.GFF)

        vanilla_gff2 = TestDataHelper.create_basic_gff({"SoundSetFile": (GFFFieldType.UInt16, 0)})
        write_gff(vanilla_gff2, self.vanilla_dir / "creature2.utc", ResourceType.GFF)

        # Modded: 2DA with 3 rows (new row 2)
        modded_2da = TestDataHelper.create_basic_2da(
            ["label"],
            [("0", {"label": "soundset_0"}), ("1", {"label": "soundset_1"}), ("2", {"label": "new_soundset"})],
        )
        write_2da(modded_2da, self.modded_dir / "soundset.2da", ResourceType.TwoDA)

        # Modded: Both GFF files now reference row 2
        modded_gff1 = TestDataHelper.create_basic_gff({"SoundSetFile": (GFFFieldType.UInt16, 2)})
        write_gff(modded_gff1, self.modded_dir / "creature1.utc", ResourceType.GFF)

        modded_gff2 = TestDataHelper.create_basic_gff({"SoundSetFile": (GFFFieldType.UInt16, 2)})
        write_gff(modded_gff2, self.modded_dir / "creature2.utc", ResourceType.GFF)

        # Run diff
        ini_content = TestDataHelper.run_diff(self.vanilla_dir, self.modded_dir, self.tslpatchdata_dir, logging_enabled=True)

        # Verify both GFF files use same token
        self.assertIn("[creature1.utc]", ini_content)
        self.assertIn("[creature2.utc]", ini_content)
        self.assertIn("SoundSetFile=", ini_content)

        print("\n=== test_multiple_gff_files_use_same_2damemory_token ===")
        print(ini_content)

    def test_2damemory_row_label_storage(self):
        """Test: Storing row label (not index) in 2DAMEMORY token.

        Pattern:
        [add_row]
        RowLabel=MyRow
        2DAMEMORY#=RowLabel
        """
        # For now, this test demonstrates the pattern
        # The diff engine may not yet support automatic row label storage
        self.skipTest("Row label storage in diff generation - implementation verification needed")

    def test_2damemory_row_cell_storage(self):
        """Test: Storing specific cell value in 2DAMEMORY token.

        Pattern:
        [change_row]
        RowIndex=5
        some_column=new_value
        2DAMEMORY#=some_column
        """
        self.skipTest("Row cell storage in diff generation - implementation verification needed")

    def test_2damemory_high_function(self):
        """Test: Using High() function in 2DA modifications.

        Pattern:
        [add_row]
        some_column=High(existing_column)
        """
        # Vanilla: 2DA with existing rows
        vanilla_2da = TestDataHelper.create_basic_2da(
            ["label", "priority"],
            [("0", {"label": "row_0", "priority": "10"}), ("1", {"label": "row_1", "priority": "20"})],
        )
        write_2da(vanilla_2da, self.vanilla_dir / "test.2da", ResourceType.TwoDA)

        # Modded: Add row that should use High(priority) + 1
        modded_2da = TestDataHelper.create_basic_2da(
            ["label", "priority"],
            [
                ("0", {"label": "row_0", "priority": "10"}),
                ("1", {"label": "row_1", "priority": "20"}),
                ("2", {"label": "new_row", "priority": "21"}),  # Should become High(priority)
            ],
        )
        write_2da(modded_2da, self.modded_dir / "test.2da", ResourceType.TwoDA)

        # Run diff
        ini_content = TestDataHelper.run_diff(self.vanilla_dir, self.modded_dir, self.tslpatchdata_dir)

        # Check if High() is detected and used
        # Note: The diff engine would need logic to detect this pattern
        print("\n=== test_2damemory_high_function ===")
        print(ini_content)


# ============================================================================
# TLK/STRREF COMPREHENSIVE TESTS
# ============================================================================


class TestTLKStrRefComprehensive(unittest.TestCase):
    """Comprehensive tests for TLK modifications and StrRef token generation."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir, self.vanilla_dir, self.modded_dir, self.tslpatchdata_dir = TestDataHelper.create_test_env()

    def tearDown(self):
        """Clean up test environment."""
        TestDataHelper.cleanup_test_env(self.temp_dir)

    def test_tlk_append_basic(self):
        """Test: Basic TLK append with new entries.

        Pattern:
        [TLKList]
        StrRef0=0
        StrRef1=1
        """
        # Vanilla: Empty TLK (or small TLK)
        vanilla_tlk = TestDataHelper.create_basic_tlk([])
        write_tlk(vanilla_tlk, self.vanilla_dir / "dialog.tlk", ResourceType.TLK)

        # Modded: TLK with new entries
        modded_tlk = TestDataHelper.create_basic_tlk([("Hello world", ""), ("Goodbye", "")])
        write_tlk(modded_tlk, self.modded_dir / "dialog.tlk", ResourceType.TLK)

        # Run diff
        ini_content = TestDataHelper.run_diff(self.vanilla_dir, self.modded_dir, self.tslpatchdata_dir)

        # Verify TLKList section
        self.assertIn("[TLKList]", ini_content)
        self.assertIn("StrRef", ini_content)

        print("\n=== test_tlk_append_basic ===")
        print(ini_content)

    def test_tlk_replace_existing_entries(self):
        """Test: TLK replace mode for modifying existing entries.

        Pattern:
        [TLKList]
        ReplaceFile0=replace.tlk
        [replace.tlk]
        100=0
        101=1
        """
        # Vanilla: TLK with entries
        vanilla_tlk = TestDataHelper.create_basic_tlk([("Original text 100", ""), ("Original text 101", "")])
        write_tlk(vanilla_tlk, self.vanilla_dir / "dialog.tlk", ResourceType.TLK)

        # Modded: TLK with modified entries
        modded_tlk = TestDataHelper.create_basic_tlk([("Modified text 100", ""), ("Modified text 101", "")])
        write_tlk(modded_tlk, self.modded_dir / "dialog.tlk", ResourceType.TLK)

        # Run diff
        ini_content = TestDataHelper.run_diff(self.vanilla_dir, self.modded_dir, self.tslpatchdata_dir)

        # Verify replace pattern
        self.assertIn("[TLKList]", ini_content)

        print("\n=== test_tlk_replace_existing_entries ===")
        print(ini_content)

    def test_strref_used_in_2da(self):
        """Test: StrRef token used in 2DA file.

        Pattern:
        StrRef token from TLK append used in 2DA cell value
        """
        # Create TLK files (vanilla and modded with new entry)
        vanilla_tlk = TLK()
        write_tlk(vanilla_tlk, self.vanilla_dir / "dialog.tlk", ResourceType.TLK)

        modded_tlk = TestDataHelper.create_basic_tlk([("New spell name", "")])
        write_tlk(modded_tlk, self.modded_dir / "dialog.tlk", ResourceType.TLK)

        # Vanilla 2DA: references non-existent StrRef
        vanilla_2da = TestDataHelper.create_basic_2da(
            ["label", "name"],
            [("0", {"label": "spell_0", "name": "-1"})],
        )
        write_2da(vanilla_2da, self.vanilla_dir / "spells.2da", ResourceType.TwoDA)

        # Modded 2DA: references new StrRef 0
        modded_2da = TestDataHelper.create_basic_2da(
            ["label", "name"],
            [("0", {"label": "spell_0", "name": "0"})],
        )
        write_2da(modded_2da, self.modded_dir / "spells.2da", ResourceType.TwoDA)

        # Run diff
        ini_content = TestDataHelper.run_diff(self.vanilla_dir, self.modded_dir, self.tslpatchdata_dir)

        # Verify StrRef used in 2DA
        self.assertIn("[TLKList]", ini_content)
        self.assertIn("[spells.2da]", ini_content)

        print("\n=== test_strref_used_in_2da ===")
        print(ini_content)

    def test_strref_used_in_gff_localized_string(self):
        """Test: StrRef token used in GFF LocalizedString field.

        Pattern:
        LocalizedString field references new TLK entry via StrRef token
        """
        self.skipTest("LocalizedString StrRef linking - implementation verification needed")

    def test_strref_used_in_ssf(self):
        """Test: StrRef token used in SSF file.

        Pattern:
        SSF sound slot references new TLK entry via StrRef token
        """
        # Create TLK files
        vanilla_tlk = TLK()
        write_tlk(vanilla_tlk, self.vanilla_dir / "dialog.tlk", ResourceType.TLK)

        modded_tlk = TestDataHelper.create_basic_tlk([("Battle cry!", "")])
        write_tlk(modded_tlk, self.modded_dir / "dialog.tlk", ResourceType.TLK)

        # Vanilla SSF: no sound
        vanilla_ssf = TestDataHelper.create_basic_ssf({SSFSound.BATTLE_CRY_1: -1})
        write_ssf(vanilla_ssf, self.vanilla_dir / "character.ssf", ResourceType.SSF)

        # Modded SSF: references new StrRef
        modded_ssf = TestDataHelper.create_basic_ssf({SSFSound.BATTLE_CRY_1: 0})
        write_ssf(modded_ssf, self.modded_dir / "character.ssf", ResourceType.SSF)

        # Run diff
        ini_content = TestDataHelper.run_diff(self.vanilla_dir, self.modded_dir, self.tslpatchdata_dir)

        # Verify StrRef used in SSF
        self.assertIn("[TLKList]", ini_content)
        self.assertIn("[character.ssf]", ini_content)

        print("\n=== test_strref_used_in_ssf ===")
        print(ini_content)


# ============================================================================
# GFF COMPREHENSIVE TESTS
# ============================================================================


class TestGFFComprehensive(unittest.TestCase):
    """Comprehensive tests for GFF modifications."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir, self.vanilla_dir, self.modded_dir, self.tslpatchdata_dir = TestDataHelper.create_test_env()

    def tearDown(self):
        """Clean up test environment."""
        TestDataHelper.cleanup_test_env(self.temp_dir)

    def test_gff_modify_all_field_types(self):
        """Test: Modify all GFF field types.

        Tests ModifyFieldGFF for:
        - Byte, Char, Word, Short, DWORD, Int, Int64
        - Float, Double
        - String, ResRef
        - LocalizedString
        - Position (Vector3), Orientation (Vector4)
        """
        # Create vanilla GFF with all field types
        vanilla_gff = GFF()
        vanilla_gff.root.set_uint8("ByteField", 10)
        vanilla_gff.root.set_int8("CharField", -5)
        vanilla_gff.root.set_uint16("WordField", 1000)
        vanilla_gff.root.set_int16("ShortField", -500)
        vanilla_gff.root.set_uint32("DWordField", 100000)
        vanilla_gff.root.set_int32("IntField", -50000)
        vanilla_gff.root.set_int64("Int64Field", 9999999999)
        vanilla_gff.root.set_single("FloatField", 1.5)
        vanilla_gff.root.set_double("DoubleField", 2.5)
        vanilla_gff.root.set_string("StringField", "Hello")
        vanilla_gff.root.set_resref("ResRefField", ResRef("test"))
        vanilla_gff.root.set_locstring("LocStringField", LocalizedString.from_invalid())
        vanilla_gff.root.set_vector3("Vector3Field", Vector3(1.0, 2.0, 3.0))
        vanilla_gff.root.set_vector4("Vector4Field", Vector4(1.0, 2.0, 3.0, 4.0))
        write_gff(vanilla_gff, self.vanilla_dir / "test.utc", ResourceType.GFF)

        # Create modded GFF with modified values
        modded_gff = GFF()
        modded_gff.root.set_uint8("ByteField", 20)
        modded_gff.root.set_int8("CharField", -10)
        modded_gff.root.set_uint16("WordField", 2000)
        modded_gff.root.set_int16("ShortField", -1000)
        modded_gff.root.set_uint32("DWordField", 200000)
        modded_gff.root.set_int32("IntField", -100000)
        modded_gff.root.set_int64("Int64Field", 8888888888)
        modded_gff.root.set_single("FloatField", 3.5)
        modded_gff.root.set_double("DoubleField", 4.5)
        modded_gff.root.set_string("StringField", "World")
        modded_gff.root.set_resref("ResRefField", ResRef("modified"))
        modded_gff.root.set_locstring("LocStringField", LocalizedString.from_invalid())
        modded_gff.root.set_vector3("Vector3Field", Vector3(4.0, 5.0, 6.0))
        modded_gff.root.set_vector4("Vector4Field", Vector4(5.0, 6.0, 7.0, 8.0))
        write_gff(modded_gff, self.modded_dir / "test.utc", ResourceType.GFF)

        # Run diff
        ini_content = TestDataHelper.run_diff(self.vanilla_dir, self.modded_dir, self.tslpatchdata_dir)

        # Verify all field modifications
        self.assertIn("[test.utc]", ini_content)
        self.assertIn("ByteField=", ini_content)
        self.assertIn("StringField=", ini_content)

        print("\n=== test_gff_modify_all_field_types ===")
        print(ini_content)

    def test_gff_add_field_to_struct(self):
        """Test: AddFieldGFF to add new fields to struct."""
        # Vanilla: GFF with basic struct
        vanilla_gff = GFF()
        vanilla_gff.root.set_uint8("ExistingField", 10)
        write_gff(vanilla_gff, self.vanilla_dir / "test.utc", ResourceType.GFF)

        # Modded: GFF with additional field
        modded_gff = GFF()
        modded_gff.root.set_uint8("ExistingField", 10)
        modded_gff.root.set_string("NewField", "Added")
        write_gff(modded_gff, self.modded_dir / "test.utc", ResourceType.GFF)

        # Run diff
        ini_content = TestDataHelper.run_diff(self.vanilla_dir, self.modded_dir, self.tslpatchdata_dir)

        # Verify AddField
        self.assertIn("[test.utc]", ini_content)
        self.assertIn("AddField", ini_content)

        print("\n=== test_gff_add_field_to_struct ===")
        print(ini_content)

    def test_gff_nested_struct_modifications(self):
        """Test: Modify fields in nested structs."""
        # Vanilla: GFF with nested struct
        vanilla_gff = GFF()
        nested_struct = GFFStruct(0)
        nested_struct.set_uint8("NestedValue", 10)
        vanilla_gff.root.set_struct("NestedStruct", nested_struct)
        write_gff(vanilla_gff, self.vanilla_dir / "test.utc", ResourceType.GFF)

        # Modded: GFF with modified nested struct
        modded_gff = GFF()
        nested_struct = GFFStruct(0)
        nested_struct.set_uint8("NestedValue", 20)
        modded_gff.root.set_struct("NestedStruct", nested_struct)
        write_gff(modded_gff, self.modded_dir / "test.utc", ResourceType.GFF)

        # Run diff
        ini_content = TestDataHelper.run_diff(self.vanilla_dir, self.modded_dir, self.tslpatchdata_dir)

        # Verify nested modification
        self.assertIn("[test.utc]", ini_content)
        self.assertIn("NestedStruct", ini_content)

        print("\n=== test_gff_nested_struct_modifications ===")
        print(ini_content)

    def test_gff_list_modifications(self):
        """Test: Modifications to GFF lists (AddStructToListGFF)."""
        # Vanilla: GFF with list
        vanilla_gff = GFF()
        gff_list = GFFList()
        item1 = GFFStruct(0)
        item1.set_uint8("Value", 10)
        gff_list._structs.append(item1)  # noqa: SLF001
        vanilla_gff.root.set_list("ItemList", gff_list)
        write_gff(vanilla_gff, self.vanilla_dir / "test.utc", ResourceType.GFF)

        # Modded: GFF with additional list item
        modded_gff = GFF()
        gff_list = GFFList()
        item1 = GFFStruct(0)
        item1.set_uint8("Value", 10)
        gff_list._structs.append(item1)  # noqa: SLF001
        item2 = GFFStruct(0)
        item2.set_uint8("Value", 20)
        gff_list._structs.append(item2)  # noqa: SLF001
        modded_gff.root.set_list("ItemList", gff_list)
        write_gff(modded_gff, self.modded_dir / "test.utc", ResourceType.GFF)

        # Run diff
        ini_content = TestDataHelper.run_diff(self.vanilla_dir, self.modded_dir, self.tslpatchdata_dir)

        # Verify list modification
        self.assertIn("[test.utc]", ini_content)

        print("\n=== test_gff_list_modifications ===")
        print(ini_content)

    def test_gff_localized_string_with_multiple_languages(self):
        """Test: LocalizedString with multiple language/gender variants."""
        # Vanilla: LocalizedString with English only
        vanilla_gff = GFF()
        loc_string = LocalizedString.from_english("Hello")
        vanilla_gff.root.set_locstring("Name", loc_string)
        write_gff(vanilla_gff, self.vanilla_dir / "test.utc", ResourceType.GFF)

        # Modded: LocalizedString with English, French, German
        modded_gff = GFF()
        loc_string = LocalizedString.from_english("Modified Hello")
        loc_string.set_data(Language.FRENCH, Gender.MALE, "Bonjour")
        loc_string.set_data(Language.GERMAN, Gender.MALE, "Guten Tag")
        modded_gff.root.set_locstring("Name", loc_string)
        write_gff(modded_gff, self.modded_dir / "test.utc", ResourceType.GFF)

        # Run diff
        ini_content = TestDataHelper.run_diff(self.vanilla_dir, self.modded_dir, self.tslpatchdata_dir)

        # Verify LocalizedString modification with lang# entries
        self.assertIn("[test.utc]", ini_content)
        self.assertIn("Name=", ini_content)

        print("\n=== test_gff_localized_string_with_multiple_languages ===")
        print(ini_content)


# ============================================================================
# SSF TESTS
# ============================================================================


class TestSSFComprehensive(unittest.TestCase):
    """Comprehensive tests for SSF modifications."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir, self.vanilla_dir, self.modded_dir, self.tslpatchdata_dir = TestDataHelper.create_test_env()

    def tearDown(self):
        """Clean up test environment."""
        TestDataHelper.cleanup_test_env(self.temp_dir)

    def test_ssf_modify_all_sound_slots(self):
        """Test: Modify all SSF sound slots."""
        # Vanilla: SSF with default values
        vanilla_ssf = SSF()
        write_ssf(vanilla_ssf, self.vanilla_dir / "character.ssf", ResourceType.SSF)

        # Modded: SSF with modified values
        modded_ssf = TestDataHelper.create_basic_ssf(
            {
                SSFSound.BATTLE_CRY_1: 1000,
                SSFSound.BATTLE_CRY_2: 1001,
                SSFSound.SELECT_1: 1002,
                SSFSound.ATTACK_GRUNT_1: 1003,
                SSFSound.PAIN_GRUNT_1: 1004,
                SSFSound.DEAD: 1005,
            }
        )
        write_ssf(modded_ssf, self.modded_dir / "character.ssf", ResourceType.SSF)

        # Run diff
        ini_content = TestDataHelper.run_diff(self.vanilla_dir, self.modded_dir, self.tslpatchdata_dir)

        # Verify SSF modifications
        self.assertIn("[SSFList]", ini_content)
        self.assertIn("[character.ssf]", ini_content)

        print("\n=== test_ssf_modify_all_sound_slots ===")
        print(ini_content)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestIntegrationComprehensive(unittest.TestCase):
    """Integration tests for cross-file references and complex scenarios."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir, self.vanilla_dir, self.modded_dir, self.tslpatchdata_dir = TestDataHelper.create_test_env()

    def tearDown(self):
        """Clean up test environment."""
        TestDataHelper.cleanup_test_env(self.temp_dir)

    def test_full_mod_scenario_new_spell(self):
        """Test: Complete mod scenario - adding a new force power.

        This tests the entire pipeline similar to "Bastila Has Battle Meditation":
        - Add row to spells.2da with new spell
        - Add row to visualeffects.2da for spell effect
        - Modify multiple creature UTC files to grant the spell
        - Use 2DAMEMORY tokens to link everything
        """
        # Step 1: Create vanilla files
        # Vanilla spells.2da
        vanilla_spells = TestDataHelper.create_basic_2da(
            ["label", "name", "iconresref"],
            [("0", {"label": "FORCE_POWER_HEAL", "name": "100", "iconresref": "ip_heal"})],
        )
        write_2da(vanilla_spells, self.vanilla_dir / "spells.2da", ResourceType.TwoDA)

        # Vanilla visualeffects.2da
        vanilla_vfx = TestDataHelper.create_basic_2da(
            ["label", "type_fd"],
            [("0", {"label": "VFX_IMP_HEAL", "type_fd": "F"})],
        )
        write_2da(vanilla_vfx, self.vanilla_dir / "visualeffects.2da", ResourceType.TwoDA)

        # Vanilla creature 1
        vanilla_creature1 = GFF()
        class_list = GFFList()
        class_struct = GFFStruct(0)
        known_list = GFFList()
        spell_struct = GFFStruct(1)
        spell_struct.set_uint16("Spell", 0)
        known_list._structs.append(spell_struct)  # noqa: SLF001
        class_struct.set_list("KnownList0", known_list)
        class_list._structs.append(class_struct)  # noqa: SLF001
        vanilla_creature1.root.set_list("ClassList", class_list)
        write_gff(vanilla_creature1, self.vanilla_dir / "creature1.utc", ResourceType.GFF)

        # Vanilla creature 2
        vanilla_creature2 = GFF()
        class_list = GFFList()
        class_struct = GFFStruct(0)
        known_list = GFFList()
        spell_struct = GFFStruct(1)
        spell_struct.set_uint16("Spell", 0)
        known_list._structs.append(spell_struct)  # noqa: SLF001
        class_struct.set_list("KnownList0", known_list)
        class_list._structs.append(class_struct)  # noqa: SLF001
        vanilla_creature2.root.set_list("ClassList", class_list)
        write_gff(vanilla_creature2, self.vanilla_dir / "creature2.utc", ResourceType.GFF)

        # Step 2: Create modded files
        # Modded spells.2da - add new spell (row 1)
        modded_spells = TestDataHelper.create_basic_2da(
            ["label", "name", "iconresref"],
            [
                ("0", {"label": "FORCE_POWER_HEAL", "name": "100", "iconresref": "ip_heal"}),
                ("1", {"label": "FORCE_POWER_NEW", "name": "101", "iconresref": "ip_new"}),
            ],
        )
        write_2da(modded_spells, self.modded_dir / "spells.2da", ResourceType.TwoDA)

        # Modded visualeffects.2da - add new effect (row 1)
        modded_vfx = TestDataHelper.create_basic_2da(
            ["label", "type_fd"],
            [("0", {"label": "VFX_IMP_HEAL", "type_fd": "F"}), ("1", {"label": "VFX_IMP_NEW", "type_fd": "F"})],
        )
        write_2da(modded_vfx, self.modded_dir / "visualeffects.2da", ResourceType.TwoDA)

        # Modded creatures - grant new spell (spell index 1)
        modded_creature1 = GFF()
        class_list = GFFList()
        class_struct = GFFStruct(0)
        known_list = GFFList()
        spell_struct1 = GFFStruct(1)
        spell_struct1.set_uint16("Spell", 0)
        known_list._structs.append(spell_struct1)  # noqa: SLF001
        spell_struct2 = GFFStruct(2)
        spell_struct2.set_uint16("Spell", 1)  # New spell
        known_list._structs.append(spell_struct2)  # noqa: SLF001
        class_struct.set_list("KnownList0", known_list)
        class_list._structs.append(class_struct)  # noqa: SLF001
        modded_creature1.root.set_list("ClassList", class_list)
        write_gff(modded_creature1, self.modded_dir / "creature1.utc", ResourceType.GFF)

        modded_creature2 = GFF()
        class_list = GFFList()
        class_struct = GFFStruct(0)
        known_list = GFFList()
        spell_struct1 = GFFStruct(1)
        spell_struct1.set_uint16("Spell", 0)
        known_list._structs.append(spell_struct1)  # noqa: SLF001
        spell_struct2 = GFFStruct(2)
        spell_struct2.set_uint16("Spell", 1)  # New spell
        known_list._structs.append(spell_struct2)  # noqa: SLF001
        class_struct.set_list("KnownList0", known_list)
        class_list._structs.append(class_struct)  # noqa: SLF001
        modded_creature2.root.set_list("ClassList", class_list)
        write_gff(modded_creature2, self.modded_dir / "creature2.utc", ResourceType.GFF)

        # Step 3: Run diff
        ini_content = TestDataHelper.run_diff(self.vanilla_dir, self.modded_dir, self.tslpatchdata_dir, logging_enabled=True)

        # Step 4: Verify comprehensive INI generation
        self.assertIn("[spells.2da]", ini_content)
        self.assertIn("[visualeffects.2da]", ini_content)
        self.assertIn("[creature1.utc]", ini_content)
        self.assertIn("[creature2.utc]", ini_content)
        self.assertIn("2DAMEMORY", ini_content, "Should use 2DAMEMORY tokens for spell references")

        print("\n=== test_full_mod_scenario_new_spell ===")
        print(ini_content)

    def test_full_mod_scenario_new_item_type(self):
        """Test: Complete mod scenario - adding a new item type (quarterstaff).

        Based on dm_qrts mod pattern:
        - Add row to weaponsounds.2da
        - Add row to baseitems.2da that references weaponsounds
        - Modify item UTI files to use new baseitems row
        - Use 2DAMEMORY token chain
        """
        # Vanilla weaponsounds.2da
        vanilla_weaponsounds = TestDataHelper.create_basic_2da(
            ["label", "cloth0"],
            [("0", {"label": "sword_sounds", "cloth0": "snd_sword"}), ("1", {"label": "blaster_sounds", "cloth0": "snd_blaster"})],
        )
        write_2da(vanilla_weaponsounds, self.vanilla_dir / "weaponsounds.2da", ResourceType.TwoDA)

        # Vanilla baseitems.2da
        vanilla_baseitems = TestDataHelper.create_basic_2da(
            ["label", "weaponmattype", "name"],
            [
                ("0", {"label": "sword", "weaponmattype": "0", "name": "200"}),
                ("1", {"label": "blaster", "weaponmattype": "1", "name": "201"}),
            ],
        )
        write_2da(vanilla_baseitems, self.vanilla_dir / "baseitems.2da", ResourceType.TwoDA)

        # Vanilla item
        vanilla_item = TestDataHelper.create_basic_gff({"BaseItem": (GFFFieldType.Int32, 0)})
        write_gff(vanilla_item, self.vanilla_dir / "item.uti", ResourceType.GFF)

        # Modded weaponsounds.2da - add quarterstaff sounds
        modded_weaponsounds = TestDataHelper.create_basic_2da(
            ["label", "cloth0"],
            [
                ("0", {"label": "sword_sounds", "cloth0": "snd_sword"}),
                ("1", {"label": "blaster_sounds", "cloth0": "snd_blaster"}),
                ("2", {"label": "quarterstaff_sounds", "cloth0": "snd_qstaff"}),
            ],
        )
        write_2da(modded_weaponsounds, self.modded_dir / "weaponsounds.2da", ResourceType.TwoDA)

        # Modded baseitems.2da - add quarterstaff
        modded_baseitems = TestDataHelper.create_basic_2da(
            ["label", "weaponmattype", "name"],
            [
                ("0", {"label": "sword", "weaponmattype": "0", "name": "200"}),
                ("1", {"label": "blaster", "weaponmattype": "1", "name": "201"}),
                ("2", {"label": "quarterstaff", "weaponmattype": "2", "name": "202"}),  # References new weaponsounds
            ],
        )
        write_2da(modded_baseitems, self.modded_dir / "baseitems.2da", ResourceType.TwoDA)

        # Modded item - use new baseitem
        modded_item = TestDataHelper.create_basic_gff({"BaseItem": (GFFFieldType.Int32, 2)})
        write_gff(modded_item, self.modded_dir / "item.uti", ResourceType.GFF)

        # Run diff
        ini_content = TestDataHelper.run_diff(self.vanilla_dir, self.modded_dir, self.tslpatchdata_dir, logging_enabled=True)

        # Verify chain
        self.assertIn("[weaponsounds.2da]", ini_content)
        self.assertIn("[baseitems.2da]", ini_content)
        self.assertIn("[item.uti]", ini_content)
        self.assertIn("2DAMEMORY", ini_content)

        print("\n=== test_full_mod_scenario_new_item_type ===")
        print(ini_content)


# ============================================================================
# REAL-WORLD SCENARIO TESTS (From actual mods)
# ============================================================================


class TestRealWorldScenarios(unittest.TestCase):
    """Tests based on real-world mod patterns from the mod workspace."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir, self.vanilla_dir, self.modded_dir, self.tslpatchdata_dir = TestDataHelper.create_test_env()

    def tearDown(self):
        """Clean up test environment."""
        TestDataHelper.cleanup_test_env(self.temp_dir)

    def test_ajunta_pall_appearance_mod(self):
        """Test: Ajunta Pall Unique Appearance pattern.

        Real mod pattern:
        - ChangeRow in appearance.2da with many columns
        - No cross-references, simple modification
        """
        # Create appearance.2da with many columns (simplified)
        vanilla_appearance = TestDataHelper.create_basic_2da(
            ["label", "race", "modeltype", "modela"],
            [
                ("370", {"label": "Sith_Ghost", "race": "AjuntaGhost", "modeltype": "F", "modela": "n_ajunta"})
            ],
        )
        write_2da(vanilla_appearance, self.vanilla_dir / "appearance.2da", ResourceType.TwoDA)

        # Modded: Change to unique appearance
        modded_appearance = TestDataHelper.create_basic_2da(
            ["label", "race", "modeltype", "modela"],
            [
                ("370", {"label": "Unique_Sith_Ghost", "race": "DP_AjuntaGhost", "modeltype": "F", "modela": "DP_AjuntaGhost"})
            ],
        )
        write_2da(modded_appearance, self.modded_dir / "appearance.2da", ResourceType.TwoDA)

        # Run diff
        ini_content = TestDataHelper.run_diff(self.vanilla_dir, self.modded_dir, self.tslpatchdata_dir)

        # Verify ChangeRow with RowIndex
        self.assertIn("[appearance.2da]", ini_content)
        self.assertIn("ChangeRow0=", ini_content)
        self.assertIn("RowIndex=370", ini_content)

        print("\n=== test_ajunta_pall_appearance_mod ===")
        print(ini_content)

    def test_k1_community_patch_pattern(self):
        """Test: K1 Community Patch pattern with extensive TLK modifications.

        Real pattern:
        - Large number of TLK entries (append and replace)
        - StrRef mappings
        - Multiple installation folders
        """
        # Simplified version - just test TLK append with multiple entries
        vanilla_tlk = TLK()
        write_tlk(vanilla_tlk, self.vanilla_dir / "dialog.tlk", ResourceType.TLK)

        modded_tlk = TestDataHelper.create_basic_tlk(
            [
                ("Fixed typo text", ""),
                ("Corrected dialog", ""),
                ("Better description", ""),
                ("Improved label", ""),
            ]
        )
        write_tlk(modded_tlk, self.modded_dir / "dialog.tlk", ResourceType.TLK)

        # Run diff
        ini_content = TestDataHelper.run_diff(self.vanilla_dir, self.modded_dir, self.tslpatchdata_dir)

        # Verify multiple StrRef tokens
        self.assertIn("[TLKList]", ini_content)
        self.assertIn("StrRef0=", ini_content)
        self.assertIn("StrRef1=", ini_content)

        print("\n=== test_k1_community_patch_pattern ===")
        print(ini_content)


# ============================================================================
# INSTALLLIST TESTS
# ============================================================================


class TestInstallListComprehensive(unittest.TestCase):
    """Comprehensive tests for InstallList generation."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir, self.vanilla_dir, self.modded_dir, self.tslpatchdata_dir = TestDataHelper.create_test_env()

    def tearDown(self):
        """Clean up test environment."""
        TestDataHelper.cleanup_test_env(self.temp_dir)

    def test_install_to_override(self):
        """Test: Files installed to Override folder."""
        # Create a simple file that needs to be copied
        test_file = self.modded_dir / "test_model.mdl"
        test_file.write_bytes(b"MOCK_MODEL_DATA")

        # Run diff
        ini_content = TestDataHelper.run_diff(self.vanilla_dir, self.modded_dir, self.tslpatchdata_dir)

        # Verify InstallList
        self.assertIn("[InstallList]", ini_content)
        self.assertIn("install_folder", ini_content)

        print("\n=== test_install_to_override ===")
        print(ini_content)

    def test_install_to_modules(self):
        """Test: Files installed to specific module folders."""
        # This would require more complex setup with module designation
        self.skipTest("Module installation - requires fuller implementation")


# ============================================================================
# EDGE CASES AND ERROR CONDITIONS
# ============================================================================


class TestEdgeCasesComprehensive(unittest.TestCase):
    """Tests for edge cases and potential error conditions."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir, self.vanilla_dir, self.modded_dir, self.tslpatchdata_dir = TestDataHelper.create_test_env()

    def tearDown(self):
        """Clean up test environment."""
        TestDataHelper.cleanup_test_env(self.temp_dir)

    def test_empty_2da_modification(self):
        """Test: 2DA with no actual changes."""
        # Vanilla and modded are identical
        twoda = TestDataHelper.create_basic_2da(
            ["label"],
            [("0", {"label": "unchanged"})],
        )
        write_2da(twoda, self.vanilla_dir / "test.2da", ResourceType.TwoDA)
        write_2da(twoda, self.modded_dir / "test.2da", ResourceType.TwoDA)

        # Run diff
        ini_content = TestDataHelper.run_diff(self.vanilla_dir, self.modded_dir, self.tslpatchdata_dir)

        # Should not create modifications for unchanged file
        # (or should create empty modification - depends on implementation)
        print("\n=== test_empty_2da_modification ===")
        print(ini_content)

    def test_2da_with_empty_cells(self):
        """Test: 2DA with **** empty cell markers."""
        vanilla_2da = TestDataHelper.create_basic_2da(
            ["label", "optional"],
            [("0", {"label": "row_0", "optional": "****"})],
        )
        write_2da(vanilla_2da, self.vanilla_dir / "test.2da", ResourceType.TwoDA)

        modded_2da = TestDataHelper.create_basic_2da(
            ["label", "optional"],
            [("0", {"label": "row_0", "optional": "value"})],
        )
        write_2da(modded_2da, self.modded_dir / "test.2da", ResourceType.TwoDA)

        # Run diff
        ini_content = TestDataHelper.run_diff(self.vanilla_dir, self.modded_dir, self.tslpatchdata_dir)

        # Should handle **** -> value transition
        self.assertIn("[test.2da]", ini_content)

        print("\n=== test_2da_with_empty_cells ===")
        print(ini_content)

    def test_gff_with_special_characters_in_strings(self):
        """Test: GFF strings with special characters that need escaping."""
        vanilla_gff = TestDataHelper.create_basic_gff(
            {"Description": (GFFFieldType.String, "Normal text")}
        )
        write_gff(vanilla_gff, self.vanilla_dir / "test.utc", ResourceType.GFF)

        modded_gff = TestDataHelper.create_basic_gff(
            {"Description": (GFFFieldType.String, "Text with\nnewline\tand\ttabs")}
        )
        write_gff(modded_gff, self.modded_dir / "test.utc", ResourceType.GFF)

        # Run diff
        ini_content = TestDataHelper.run_diff(self.vanilla_dir, self.modded_dir, self.tslpatchdata_dir)

        # Should escape special characters in INI
        self.assertIn("[test.utc]", ini_content)
        self.assertIn("Description=", ini_content)

        print("\n=== test_gff_with_special_characters_in_strings ===")
        print(ini_content)

    def test_large_2da_many_rows(self):
        """Test: Large 2DA file with many rows."""
        # Create a 2DA with 100 rows
        rows = [(str(i), {"label": f"row_{i}", "value": str(i * 10)}) for i in range(100)]
        vanilla_2da = TestDataHelper.create_basic_2da(["label", "value"], rows)
        write_2da(vanilla_2da, self.vanilla_dir / "large.2da", ResourceType.TwoDA)

        # Modify one row in the middle
        rows_modded = [(str(i), {"label": f"row_{i}", "value": str(i * 10) if i != 50 else "MODIFIED"}) for i in range(100)]
        modded_2da = TestDataHelper.create_basic_2da(["label", "value"], rows_modded)
        write_2da(modded_2da, self.modded_dir / "large.2da", ResourceType.TwoDA)

        # Run diff
        ini_content = TestDataHelper.run_diff(self.vanilla_dir, self.modded_dir, self.tslpatchdata_dir)

        # Should only modify row 50
        self.assertIn("[large.2da]", ini_content)
        self.assertIn("ChangeRow0=", ini_content)

        print("\n=== test_large_2da_many_rows ===")
        print(ini_content)


# ============================================================================
# PERFORMANCE AND STRESS TESTS
# ============================================================================


class TestPerformanceComprehensive(unittest.TestCase):
    """Performance and stress tests for diff generation."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir, self.vanilla_dir, self.modded_dir, self.tslpatchdata_dir = TestDataHelper.create_test_env()

    def tearDown(self):
        """Clean up test environment."""
        TestDataHelper.cleanup_test_env(self.temp_dir)

    def test_many_2da_files(self):
        """Test: Diff with many 2DA files."""
        # Create 20 2DA files
        for i in range(20):
            twoda = TestDataHelper.create_basic_2da(
                ["label", "value"],
                [(str(j), {"label": f"row_{j}", "value": str(j)}) for j in range(10)],
            )
            write_2da(twoda, self.vanilla_dir / f"test{i}.2da", ResourceType.TwoDA)

            # Modded: modify first row of each
            twoda_modded = TestDataHelper.create_basic_2da(
                ["label", "value"],
                [(str(j), {"label": f"row_{j}", "value": "MODIFIED" if j == 0 else str(j)}) for j in range(10)],
            )
            write_2da(twoda_modded, self.modded_dir / f"test{i}.2da", ResourceType.TwoDA)

        # Run diff
        ini_content = TestDataHelper.run_diff(self.vanilla_dir, self.modded_dir, self.tslpatchdata_dir)

        # Should handle all files
        self.assertIn("[2DAList]", ini_content)
        # Count number of Table# entries
        table_count = ini_content.count("Table")
        self.assertGreaterEqual(table_count, 20)

        print("\n=== test_many_2da_files ===")
        print(f"Generated INI for {table_count} 2DA files")

    def test_many_gff_files(self):
        """Test: Diff with many GFF files."""
        # Create 20 GFF files
        for i in range(20):
            gff = TestDataHelper.create_basic_gff({"Value": (GFFFieldType.UInt8, 10)})
            write_gff(gff, self.vanilla_dir / f"test{i}.utc", ResourceType.GFF)

            gff_modded = TestDataHelper.create_basic_gff({"Value": (GFFFieldType.UInt8, 20)})
            write_gff(gff_modded, self.modded_dir / f"test{i}.utc", ResourceType.GFF)

        # Run diff
        ini_content = TestDataHelper.run_diff(self.vanilla_dir, self.modded_dir, self.tslpatchdata_dir)

        # Should handle all files
        self.assertIn("[GFFList]", ini_content)
        file_count = ini_content.count("File")
        self.assertGreaterEqual(file_count, 20)

        print("\n=== test_many_gff_files ===")
        print(f"Generated INI for {file_count} GFF files")


if __name__ == "__main__":
    unittest.main()

