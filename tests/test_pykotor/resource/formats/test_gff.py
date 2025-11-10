from __future__ import annotations

import os
import pathlib
import sys
import tempfile
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

from utility.common.geometry import Vector3, Vector4
from pykotor.common.language import Gender, Language
from pykotor.resource.formats.gff import (
    GFF,
    GFFBinaryReader,
    GFFXMLReader,
    bytes_gff,
    read_gff,
    write_gff,
)
from pykotor.resource.type import ResourceType

BINARY_TEST_FILE = "tests/test_pykotor/test_files/test.gff"
XML_TEST_FILE = "tests/test_pykotor/test_files/test.gff.xml"
DOES_NOT_EXIST_FILE = "./thisfiledoesnotexist"
CORRUPT_BINARY_TEST_FILE = "tests/test_pykotor/test_files/test_corrupted.gff"
CORRUPT_XML_TEST_FILE = "tests/test_pykotor/test_files/test_corrupted.gff.xml"
GIT_TEST_FILE = "tests/test_pykotor/test_files/test.git"


class TestGFF(TestCase):
    def test_binary_io(self):
        gff = GFFBinaryReader(BINARY_TEST_FILE).load()
        self.validate_io(gff)

        data = bytearray()
        write_gff(gff, data, ResourceType.GFF)
        gff = read_gff(data)
        self.validate_io(gff)

    def test_xml_io(self):
        gff = GFFXMLReader(XML_TEST_FILE).load()
        self.validate_io(gff)

        data = bytearray()
        write_gff(gff, data, ResourceType.GFF_XML)
        gff = read_gff(data)
        self.validate_io(gff)

    def test_to_raw_data_simple_read_size_unchanged(self):
        """Verify that converting a GFF to raw data preserves its byte length."""
        original_data = pathlib.Path(BINARY_TEST_FILE).read_bytes()
        gff = read_gff(original_data)

        raw_data = bytes_gff(gff)

        self.assertEqual(len(original_data), len(raw_data), "Size of raw data has changed.")

    def test_write_to_file_valid_path_size_unchanged(self):
        """Verify that writing a GFF to disk preserves the original byte length."""
        original_size = pathlib.Path(GIT_TEST_FILE).stat().st_size
        gff = read_gff(GIT_TEST_FILE)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = pathlib.Path(tmpdir).joinpath("test_copy.git")
            write_gff(gff, output_path, ResourceType.GIT)

            self.assertTrue(output_path.exists(), "GFF output file was not created.")
            self.assertEqual(original_size, output_path.stat().st_size, "File size has changed.")

    def validate_io(self, gff: GFF):
        assert gff.root.get_uint8("uint8") == 255
        assert gff.root.get_int8("int8") == -127
        assert gff.root.get_uint16("uint16") == 65535
        assert gff.root.get_int16("int16") == -32768
        assert gff.root.get_uint32("uint32") == 4294967295
        assert gff.root.get_int32("int32") == -2147483648
        # K-GFF does not seem to handle int64 correctly?
        assert gff.root.get_uint64("uint64") == 4294967296

        self.assertAlmostEqual(gff.root.get_single("single"), 12.34567, 5)
        self.assertAlmostEqual(gff.root.get_double("double"), 12.345678901234, 14)

        assert gff.root.get_string("string") == "abcdefghij123456789"
        assert gff.root.get_resref("resref") == "resref01"
        assert gff.root.get_binary("binary") == b"binarydata"

        assert gff.root.get_vector4("orientation") == Vector4(1, 2, 3, 4)
        assert gff.root.get_vector3("position") == Vector3(11, 22, 33)

        locstring = gff.root.get_locstring("locstring")
        assert locstring is not None, "Locstring is None"
        assert locstring.stringref == -1, f"Locstring stringref {locstring.stringref} is not -1"
        assert len(locstring) == 2, f"Locstring length {len(locstring)} is not 2"
        assert locstring.get(Language.ENGLISH, Gender.MALE) == "male_eng", "Locstring get(Language.ENGLISH, Gender.MALE) {locstring.get(Language.ENGLISH, Gender.MALE)} is not 'male_eng'"
        assert locstring.get(Language.GERMAN, Gender.FEMALE) == "fem_german", "Locstring get(Language.GERMAN, Gender.FEMALE) {locstring.get(Language.GERMAN, Gender.FEMALE)} is not 'fem_german'"

        child_struct = gff.root.get_struct("child_struct")
        assert child_struct is not None, "Child struct is None"
        assert child_struct.get_uint8("child_uint8") == 4, f"Child struct get_uint8('child_uint8') {child_struct.get_uint8('child_uint8')} is not 4"
        gff_list = gff.root.get_list("list")
        assert gff_list is not None, "List is None"
        gff_list_entry_0 = gff_list.at(0)
        assert gff_list_entry_0 is not None, "List at(0) is None"
        assert gff_list_entry_0.struct_id == 1, f"List at(0).struct_id {gff_list_entry_0.struct_id} is not 1"
        gff_list_entry_1 = gff_list.at(1)
        assert gff_list_entry_1 is not None, "List at(1) is None"
        assert gff_list_entry_1.struct_id == 2, f"List at(1).struct_id {gff_list_entry_1.struct_id} is not 2"
        assert len(gff_list) == 2, f"List length {len(gff_list)} is not 2"

    def test_read_raises(self):
        if os.name == "nt":
            self.assertRaises(PermissionError, read_gff, ".")
        else:
            self.assertRaises(IsADirectoryError, read_gff, ".")
        self.assertRaises(FileNotFoundError, read_gff, DOES_NOT_EXIST_FILE)
        self.assertRaises(ValueError, read_gff, CORRUPT_BINARY_TEST_FILE)
        self.assertRaises(ValueError, read_gff, CORRUPT_XML_TEST_FILE)

    def test_write_raises(self):
        if os.name == "nt":
            self.assertRaises(PermissionError, write_gff, GFF(), ".", ResourceType.GFF)
        else:
            self.assertRaises(IsADirectoryError, write_gff, GFF(), ".", ResourceType.GFF)
        self.assertRaises(ValueError, write_gff, GFF(), ".", ResourceType.INVALID)


if __name__ == "__main__":
    unittest.main()
