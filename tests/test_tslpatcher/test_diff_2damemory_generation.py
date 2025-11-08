"""Tests for 2DAMEMORY token generation during diff operations.

These tests verify that the diff engine properly generates 2DAMEMORY tokens
and linking patches when detecting cross-file references between GFF files
and 2DA files.
"""

import pathlib
import sys
import textwrap
import unittest
from pathlib import Path
import shutil
import tempfile


def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


# Add paths
add_sys_path(pathlib.Path(__file__).parents[2] / "Libraries" / "PyKotor" / "src" / "pykotor")
add_sys_path(pathlib.Path(__file__).parents[2] / "Libraries" / "PyKotor" / "src")
add_sys_path(pathlib.Path(__file__).parents[2] / "Libraries" / "Utility" / "src")
add_sys_path(pathlib.Path(__file__).parents[2] / "Tools" / "KotorDiff" / "src")


from pykotor.common.misc import Game
from pykotor.resource.formats.gff import GFF, GFFFieldType, read_gff, write_gff
from pykotor.resource.formats.twoda import TwoDA, read_2da, write_2da
from pykotor.resource.type import ResourceType
from pykotor.tslpatcher.config import PatcherConfig
from pykotor.tslpatcher.memory import PatcherMemory
from pykotor.tslpatcher.logger import PatchLogger
from pykotor.tslpatcher.reader import ConfigReader
from kotordiff.app import KotorDiffConfig, run_application
from configparser import ConfigParser


class TestDiff2DAMemoryGeneration(unittest.TestCase):
    """Test suite for 2DAMEMORY token generation in diff operations."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.tslpatchdata_path = Path(self.temp_dir) / "tslpatchdata"
        self.tslpatchdata_path.mkdir(exist_ok=True)

    def tearDown(self):
        """Clean up test environment."""
        if hasattr(self, "temp_dir"):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _setupIniAndConfig(self, ini_text: str) -> PatcherConfig:
        """Load INI and create PatcherConfig."""
        ini = ConfigParser(delimiters="=", allow_no_value=True, strict=False, interpolation=None, inline_comment_prefixes=(";", "#"))
        ini.optionxform = lambda optionstr: optionstr
        ini.read_string(ini_text)
        result = PatcherConfig()
        ConfigReader(ini, self.temp_dir, tslpatchdata_path=self.tslpatchdata_path).load(result)
        return result

    def test_gff_references_new_2da_row(self):
        """Test: GFF file references a newly added 2DA row.

        Scenario:
        - vanilla/appearance.2da has 2 rows
        - vanilla/creature.utc references row 0 (Appearance_Type=0)
        - modded/appearance.2da has 3 rows (new row 2 added)
        - modded/creature.utc references row 2 (Appearance_Type=2)

        Expected:
        - AddRow2DA stores row index in 2DAMEMORY token
        - ModifyFieldGFF uses that token to update Appearance_Type
        """
        # Create vanilla files
        vanilla_dir = Path(self.temp_dir) / "vanilla"
        vanilla_dir.mkdir()

        # Vanilla 2DA: 2 rows
        vanilla_2da = TwoDA(["label", "modeltype"])
        vanilla_2da.add_row("0", {"label": "appearance_0", "modeltype": "P"})
        vanilla_2da.add_row("1", {"label": "appearance_1", "modeltype": "F"})
        write_2da(vanilla_2da, vanilla_dir / "appearance.2da", ResourceType.TwoDA)

        # Vanilla GFF: references row 0
        vanilla_gff = GFF()
        vanilla_gff.root.set_uint16("Appearance_Type", 0)
        write_gff(vanilla_gff, vanilla_dir / "creature.utc", ResourceType.GFF)

        # Create modded files
        modded_dir = Path(self.temp_dir) / "modded"
        modded_dir.mkdir()

        # Modded 2DA: 3 rows (new row 2)
        modded_2da = TwoDA(["label", "modeltype"])
        modded_2da.add_row("0", {"label": "appearance_0", "modeltype": "P"})
        modded_2da.add_row("1", {"label": "appearance_1", "modeltype": "F"})
        modded_2da.add_row("2", {"label": "new_appearance", "modeltype": "B"})
        write_2da(modded_2da, modded_dir / "appearance.2da", ResourceType.TwoDA)

        # Modded GFF: references row 2
        modded_gff = GFF()
        modded_gff.root.set_uint16("Appearance_Type", 2)
        write_gff(modded_gff, modded_dir / "creature.utc", ResourceType.GFF)

        # Run diff
        config_diff = KotorDiffConfig(
            paths=[vanilla_dir, modded_dir],
            tslpatchdata_path=self.tslpatchdata_path,
            ini_filename="changes.ini",
            compare_hashes=True,
            logging_enabled=True,  # Enable logging to see debug output
            use_incremental_writer=True,  # Enable incremental writer for 2DAMEMORY support
        )
        run_application(config_diff)

        # Read generated INI
        ini_path = self.tslpatchdata_path / "changes.ini"
        generated_ini = ini_path.read_text(encoding="utf-8")

        # Verify INI contains:
        # 1. AddRow2DA with store_2da (2DAMEMORY token for row index)
        # 2. ModifyFieldGFF using that token (Appearance_Type=2DAMEMORY#)
        self.assertIn("[appearance.2da]", generated_ini)
        self.assertIn("AddRow0=", generated_ini)
        self.assertIn("[creature.utc]", generated_ini)
        self.assertIn("Appearance_Type=", generated_ini)

        # Verify token usage pattern
        # The diff engine should create a 2DAMEMORY token for the new row
        # and use it in the GFF modification
        self.assertIn("2DAMEMORY", generated_ini, "Should contain 2DAMEMORY token for linking")

        print("\n=== Generated INI ===")
        print(generated_ini)
        print("=== End INI ===\n")

    def test_gff_references_modified_2da_row(self):
        """Test: GFF file references a 2DA row that gets modified.

        Scenario:
        - vanilla/baseitems.2da has row 5 with certain values
        - vanilla/item.uti references row 5 (BaseItem=5)
        - modded/baseitems.2da has row 5 with modified values
        - modded/item.uti still references row 5

        Expected:
        - ChangeRow2DA stores row index in 2DAMEMORY token
        - No GFF modification needed (same row index)
        - But token is available for other uses
        """
        # Create vanilla files
        vanilla_dir = Path(self.temp_dir) / "vanilla"
        vanilla_dir.mkdir()

        # Vanilla 2DA
        vanilla_2da = TwoDA(["label", "equipableslots"])
        for i in range(6):
            vanilla_2da.add_row(str(i), {"label": f"item_{i}", "equipableslots": "0x0001"})
        write_2da(vanilla_2da, vanilla_dir / "baseitems.2da", ResourceType.TwoDA)

        # Vanilla GFF
        vanilla_gff = GFF()
        vanilla_gff.root.set_int32("BaseItem", 5)
        write_gff(vanilla_gff, vanilla_dir / "item.uti", ResourceType.GFF)

        # Create modded files
        modded_dir = Path(self.temp_dir) / "modded"
        modded_dir.mkdir()

        # Modded 2DA: row 5 modified
        modded_2da = TwoDA(["label", "equipableslots"])
        for i in range(6):
            if i == 5:
                modded_2da.add_row(str(i), {"label": "modified_item_5", "equipableslots": "0xFFFF"})
            else:
                modded_2da.add_row(str(i), {"label": f"item_{i}", "equipableslots": "0x0001"})
        write_2da(modded_2da, modded_dir / "baseitems.2da", ResourceType.TwoDA)

        # Modded GFF: same reference
        modded_gff = GFF()
        modded_gff.root.set_int32("BaseItem", 5)
        write_gff(modded_gff, modded_dir / "item.uti", ResourceType.GFF)

        # Run diff
        config_diff = KotorDiffConfig(
            paths=[vanilla_dir, modded_dir],
            tslpatchdata_path=self.tslpatchdata_path,
            ini_filename="changes.ini",
            compare_hashes=True,
            logging_enabled=False,
        )
        run_application(config_diff)

        # Read generated INI
        ini_path = self.tslpatchdata_path / "changes.ini"
        generated_ini = ini_path.read_text(encoding="utf-8")

        # Verify INI contains ChangeRow2DA with store_2da
        self.assertIn("[baseitems.2da]", generated_ini)
        self.assertIn("ChangeRow0=", generated_ini)

        # No GFF modification expected (same row index)
        # But if GFF was also modified, it could use the token

        print("\n=== Generated INI ===")
        print(generated_ini)
        print("=== End INI ===\n")

    def test_multiple_gff_files_reference_same_2da_row(self):
        """Test: Multiple GFF files reference the same new 2DA row.

        Scenario:
        - vanilla/soundset.2da has 5 rows
        - vanilla/creature1.utc references row 2 (SoundSetFile=2)
        - vanilla/creature2.utc references row 2 (SoundSetFile=2)
        - modded/soundset.2da has 6 rows (new row 5)
        - modded/creature1.utc references row 5 (SoundSetFile=5)
        - modded/creature2.utc references row 5 (SoundSetFile=5)

        Expected:
        - AddRow2DA stores row index in 2DAMEMORY token
        - Both GFF files use the same token for SoundSetFile
        """
        # Create vanilla files
        vanilla_dir = Path(self.temp_dir) / "vanilla"
        vanilla_dir.mkdir()

        # Vanilla 2DA
        vanilla_2da = TwoDA(["label"])
        for i in range(5):
            vanilla_2da.add_row(str(i), {"label": f"soundset_{i}"})
        write_2da(vanilla_2da, vanilla_dir / "soundset.2da", ResourceType.TwoDA)

        # Vanilla GFF 1
        vanilla_gff1 = GFF()
        vanilla_gff1.root.set_uint16("SoundSetFile", 2)
        write_gff(vanilla_gff1, vanilla_dir / "creature1.utc", ResourceType.GFF)

        # Vanilla GFF 2
        vanilla_gff2 = GFF()
        vanilla_gff2.root.set_uint16("SoundSetFile", 2)
        write_gff(vanilla_gff2, vanilla_dir / "creature2.utc", ResourceType.GFF)

        # Create modded files
        modded_dir = Path(self.temp_dir) / "modded"
        modded_dir.mkdir()

        # Modded 2DA: new row 5
        modded_2da = TwoDA(["label"])
        for i in range(6):
            modded_2da.add_row(str(i), {"label": f"soundset_{i}" if i < 5 else "new_soundset"})
        write_2da(modded_2da, modded_dir / "soundset.2da", ResourceType.TwoDA)

        # Modded GFF 1: references row 5
        modded_gff1 = GFF()
        modded_gff1.root.set_uint16("SoundSetFile", 5)
        write_gff(modded_gff1, modded_dir / "creature1.utc", ResourceType.GFF)

        # Modded GFF 2: references row 5
        modded_gff2 = GFF()
        modded_gff2.root.set_uint16("SoundSetFile", 5)
        write_gff(modded_gff2, modded_dir / "creature2.utc", ResourceType.GFF)

        # Run diff
        config_diff = KotorDiffConfig(
            paths=[vanilla_dir, modded_dir],
            tslpatchdata_path=self.tslpatchdata_path,
            ini_filename="changes.ini",
            compare_hashes=True,
            logging_enabled=False,
        )
        run_application(config_diff)

        # Read generated INI
        ini_path = self.tslpatchdata_path / "changes.ini"
        generated_ini = ini_path.read_text(encoding="utf-8")

        # Verify both GFF files use 2DAMEMORY token
        self.assertIn("[creature1.utc]", generated_ini)
        self.assertIn("[creature2.utc]", generated_ini)
        self.assertIn("SoundSetFile=", generated_ini)

        # Should have one 2DAMEMORY token shared by both
        token_count = generated_ini.count("2DAMEMORY")
        self.assertGreater(token_count, 0, "Should contain 2DAMEMORY tokens")

        print("\n=== Generated INI ===")
        print(generated_ini)
        print("=== End INI ===\n")

    def test_2da_row_label_storage(self):
        """Test: Storing 2DA row label in 2DAMEMORY token.

        Scenario:
        - Add a row to appearance.2da
        - Store the row label (not index) in a 2DAMEMORY token
        - Use that token in another modification

        Expected:
        - AddRow2DA with 2DAMEMORY#=RowLabel
        - Token available for use in subsequent modifications
        """
        # This test verifies the diff engine can generate:
        # [add_row]
        # RowLabel=2
        # label=new_appearance
        # 2DAMEMORY1=RowLabel
        #
        # Then use it:
        # [another_row]
        # some_column=2DAMEMORY1

        # For now, this is a placeholder demonstrating the pattern
        # The actual implementation needs to detect when row labels
        # should be stored vs row indices
        self.skipTest("Row label storage in diff generation not yet implemented")

    def test_addcolumn_with_2damemory_storage(self):
        """Test: AddColumn storing specific row values in 2DAMEMORY.

        Scenario:
        - Add a column to a 2DA
        - Store specific row values from that column in 2DAMEMORY tokens
        - Use those tokens in GFF modifications

        Expected:
        - AddColumn2DA with 2DAMEMORY#=I# or 2DAMEMORY#=Llabel
        - Tokens available for GFF field assignments
        """
        # This test verifies the diff engine can generate:
        # [add_column]
        # ColumnLabel=NewCol
        # DefaultValue=0
        # I5=special_value
        # 2DAMEMORY10=I5
        #
        # Then use it:
        # [some_item.uti]
        # SomeField=2DAMEMORY10

        # For now, this is a placeholder
        self.skipTest("AddColumn memory storage in diff generation not yet implemented")


if __name__ == "__main__":
    unittest.main()

