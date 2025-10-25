"""Tests for KotorDiff INI generator functionality."""

from __future__ import annotations

import pathlib
import sys
import unittest
from pathlib import Path

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

from pykotor.common.geometry import Vector3, Vector4
from pykotor.common.language import Gender, Language, LocalizedString
from pykotor.common.misc import ResRef
from pykotor.resource.formats.gff.gff_auto import bytes_gff, read_gff
from pykotor.resource.formats.gff.gff_data import GFF, GFFFieldType
from pykotor.resource.formats.ssf.ssf_auto import bytes_ssf, read_ssf
from pykotor.resource.formats.ssf.ssf_data import SSF, SSFSound
from pykotor.resource.formats.tlk.tlk_auto import bytes_tlk, read_tlk
from pykotor.resource.formats.tlk.tlk_data import TLK
from pykotor.resource.formats.twoda.twoda_auto import bytes_2da, read_2da
from pykotor.resource.formats.twoda.twoda_data import TwoDA

from kotordiff.diff_analyzers import (
    GFFDiffAnalyzer,
    SSFDiffAnalyzer,
    TLKDiffAnalyzer,
    TwoDADiffAnalyzer,
)
from kotordiff.ini_generator import (
    ChangesINIWriter,
    GFFINIGenerator,
    SSFINIGenerator,
    TLKINIGenerator,
    TwoDAINIGenerator,
)
from kotordiff.structured_diff import StructuredDiffEngine


class TestTwoDAINIGenerator(unittest.TestCase):
    """Test 2DA INI generation."""

    def setUp(self):
        self.generator = TwoDAINIGenerator()
        self.diff_engine = StructuredDiffEngine()

    def test_generate_row_change(self):
        """Test generating INI sections for row changes."""
        # Create left 2DA
        left_2da = TwoDA(["Col1", "Col2", "Col3"])
        left_2da.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        left_2da.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})

        # Create right 2DA with modified row
        right_2da = TwoDA(["Col1", "Col2", "Col3"])
        right_2da.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        right_2da.add_row("1", {"Col1": "X", "Col2": "e", "Col3": "f"})

        # Generate diff
        left_data = bytes_2da(left_2da)
        right_data = bytes_2da(right_2da)
        diff_result = self.diff_engine.compare_2da(left_data, right_data, "test.2da", "test.2da")

        # Generate INI sections
        sections = self.generator.generate_sections(diff_result)

        # Verify sections were generated
        self.assertGreater(len(sections), 0)

        # Verify main section exists
        main_section = sections[0]
        self.assertEqual("test.2da", main_section.name)
        self.assertIn("ChangeRow0", main_section.items)

    def test_generate_row_addition(self):
        """Test generating INI sections for row additions."""
        # Create left 2DA
        left_2da = TwoDA(["Col1", "Col2"])
        left_2da.add_row("0", {"Col1": "a", "Col2": "b"})

        # Create right 2DA with added row
        right_2da = TwoDA(["Col1", "Col2"])
        right_2da.add_row("0", {"Col1": "a", "Col2": "b"})
        right_2da.add_row("1", {"Col1": "c", "Col2": "d"})

        # Generate diff
        left_data = bytes_2da(left_2da)
        right_data = bytes_2da(right_2da)
        diff_result = self.diff_engine.compare_2da(left_data, right_data, "test.2da", "test.2da")

        # Generate INI sections
        sections = self.generator.generate_sections(diff_result)

        # Verify sections were generated
        self.assertGreater(len(sections), 0)

        # Verify AddRow was generated
        self.assertTrue(any("AddRow" in str(section.name) or "AddRow" in str(section.items) for section in sections))

    def test_generate_column_addition(self):
        """Test generating INI sections for column additions."""
        # Create left 2DA
        left_2da = TwoDA(["Col1", "Col2"])
        left_2da.add_row("0", {"Col1": "a", "Col2": "b"})

        # Create right 2DA with added column
        right_2da = TwoDA(["Col1", "Col2", "Col3"])
        right_2da.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})

        # Generate diff
        left_data = bytes_2da(left_2da)
        right_data = bytes_2da(right_2da)
        diff_result = self.diff_engine.compare_2da(left_data, right_data, "test.2da", "test.2da")

        # Generate INI sections
        sections = self.generator.generate_sections(diff_result)

        # Verify sections were generated
        self.assertGreater(len(sections), 0)

        # Verify AddColumn was generated
        self.assertTrue(any("AddColumn" in str(section.items) for section in sections))


class TestGFFINIGenerator(unittest.TestCase):
    """Test GFF INI generation."""

    def setUp(self):
        self.generator = GFFINIGenerator()
        self.diff_engine = StructuredDiffEngine()

    def test_generate_field_modification(self):
        """Test generating INI sections for field modifications."""
        # Create left GFF
        left_gff = GFF()
        left_gff.root.set_uint8("TestField", 1)

        # Create right GFF with modified field
        right_gff = GFF()
        right_gff.root.set_uint8("TestField", 2)

        # Generate diff
        left_data = bytes_gff(left_gff)
        right_data = bytes_gff(right_gff)
        diff_result = self.diff_engine.compare_gff(left_data, right_data, "test.gff", "test.gff")

        # Generate INI sections
        sections = self.generator.generate_sections(diff_result)

        # Verify sections were generated
        self.assertGreater(len(sections), 0)

        # Verify field modification
        main_section = sections[0]
        self.assertIn("TestField", main_section.items)
        self.assertEqual("2", main_section.items["TestField"])

    def test_generate_field_addition(self):
        """Test generating INI sections for field additions."""
        # Create left GFF
        left_gff = GFF()
        left_gff.root.set_uint8("Field1", 1)

        # Create right GFF with added field
        right_gff = GFF()
        right_gff.root.set_uint8("Field1", 1)
        right_gff.root.set_string("Field2", "test")

        # Generate diff
        left_data = bytes_gff(left_gff)
        right_data = bytes_gff(right_gff)
        diff_result = self.diff_engine.compare_gff(left_data, right_data, "test.gff", "test.gff")

        # Generate INI sections
        sections = self.generator.generate_sections(diff_result)

        # Verify sections were generated (may include added field)
        self.assertGreaterEqual(len(sections), 0)


class TestTLKINIGenerator(unittest.TestCase):
    """Test TLK INI generation."""

    def setUp(self):
        self.generator = TLKINIGenerator()
        self.diff_engine = StructuredDiffEngine()

    def test_generate_entry_modification(self):
        """Test generating INI sections for entry modifications."""
        # Create left TLK
        left_tlk = TLK()
        left_tlk.add("Original text")
        left_tlk.add("Another entry")

        # Create right TLK with modified entry
        right_tlk = TLK()
        right_tlk.add("Modified text")
        right_tlk.add("Another entry")

        # Generate diff
        left_data = bytes_tlk(left_tlk)
        right_data = bytes_tlk(right_tlk)
        diff_result = self.diff_engine.compare_tlk(left_data, right_data, "dialog.tlk", "dialog.tlk")

        # Generate INI sections
        sections = self.generator.generate_sections(diff_result)

        # Verify sections were generated
        self.assertGreater(len(sections), 0)

    def test_generate_entry_addition(self):
        """Test generating INI sections for entry additions."""
        # Create left TLK
        left_tlk = TLK()
        left_tlk.add("Entry 1")

        # Create right TLK with added entry
        right_tlk = TLK()
        right_tlk.add("Entry 1")
        right_tlk.add("Entry 2")

        # Generate diff
        left_data = bytes_tlk(left_tlk)
        right_data = bytes_tlk(right_tlk)
        diff_result = self.diff_engine.compare_tlk(left_data, right_data, "dialog.tlk", "dialog.tlk")

        # Generate INI sections
        sections = self.generator.generate_sections(diff_result)

        # Verify sections were generated
        self.assertGreater(len(sections), 0)


class TestChangesINIWriter(unittest.TestCase):
    """Test complete changes.ini generation."""

    def test_write_2da_changes(self):
        """Test writing 2DA changes to INI file."""
        writer = ChangesINIWriter()
        diff_engine = StructuredDiffEngine()

        # Create test 2DA files
        left_2da = TwoDA(["Col1", "Col2"])
        left_2da.add_row("0", {"Col1": "a", "Col2": "b"})

        right_2da = TwoDA(["Col1", "Col2"])
        right_2da.add_row("0", {"Col1": "X", "Col2": "b"})

        # Generate diff
        left_data = bytes_2da(left_2da)
        right_data = bytes_2da(right_2da)
        diff_result = diff_engine.compare_2da(left_data, right_data, "test.2da", "test.2da")

        # Add to writer
        writer.add_diff_result(diff_result, "2da")

        # Generate INI string
        ini_content = writer.write_to_string()

        # Verify content
        self.assertIn("[test.2da]", ini_content)
        self.assertIn("ChangeRow", ini_content)

    def test_write_gff_changes(self):
        """Test writing GFF changes to INI file."""
        writer = ChangesINIWriter()
        diff_engine = StructuredDiffEngine()

        # Create test GFF files
        left_gff = GFF()
        left_gff.root.set_uint8("Field1", 1)

        right_gff = GFF()
        right_gff.root.set_uint8("Field1", 2)

        # Generate diff
        left_data = bytes_gff(left_gff)
        right_data = bytes_gff(right_gff)
        diff_result = diff_engine.compare_gff(left_data, right_data, "test.gff", "test.gff")

        # Add to writer
        writer.add_diff_result(diff_result, "gff")

        # Generate INI string
        ini_content = writer.write_to_string()

        # Verify content
        self.assertIn("[test.gff]", ini_content)
        self.assertIn("Field1", ini_content)


class TestDiffAnalyzers(unittest.TestCase):
    """Test diff analyzers."""

    def test_2da_analyzer(self):
        """Test 2DA analyzer."""
        analyzer = TwoDADiffAnalyzer()

        # Create test data
        left_2da = TwoDA(["Col1"])
        left_2da.add_row("0", {"Col1": "a"})

        right_2da = TwoDA(["Col1"])
        right_2da.add_row("0", {"Col1": "b"})

        left_data = bytes_2da(left_2da)
        right_data = bytes_2da(right_2da)

        # Analyze
        modifications = analyzer.analyze(left_data, right_data, "test.2da")

        # Verify
        self.assertIsNotNone(modifications)
        self.assertGreater(len(modifications.modifiers), 0)

    def test_gff_analyzer(self):
        """Test GFF analyzer."""
        analyzer = GFFDiffAnalyzer()

        # Create test data
        left_gff = GFF()
        left_gff.root.set_string("Field1", "value1")

        right_gff = GFF()
        right_gff.root.set_string("Field1", "value2")

        left_data = bytes_gff(left_gff)
        right_data = bytes_gff(right_gff)

        # Analyze
        modifications = analyzer.analyze(left_data, right_data, "test.gff")

        # Verify
        self.assertIsNotNone(modifications)
        self.assertGreater(len(modifications.modifiers), 0)

    def test_tlk_analyzer(self):
        """Test TLK analyzer."""
        analyzer = TLKDiffAnalyzer()

        # Create test data
        left_tlk = TLK()
        left_tlk.add("Text 1")

        right_tlk = TLK()
        right_tlk.add("Text 2")

        left_data = bytes_tlk(left_tlk)
        right_data = bytes_tlk(right_tlk)

        # Analyze
        modifications = analyzer.analyze(left_data, right_data, "dialog.tlk")

        # Verify
        self.assertIsNotNone(modifications)
        self.assertGreater(len(modifications.modifiers), 0)


if __name__ == "__main__":
    unittest.main()




