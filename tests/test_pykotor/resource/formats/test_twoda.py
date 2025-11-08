from __future__ import annotations

import os
import pathlib
import sys
import unittest

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

from pykotor.resource.formats.twoda import TwoDA, TwoDABinaryReader, TwoDACSVReader, bytes_2da, detect_2da, read_2da, write_2da
from pykotor.resource.formats.twoda.io_twoda_json import TwoDAJSONReader
from pykotor.resource.type import ResourceType

CSV_TEST_DATA = ",col1,col2,col3\n10,abc,def,ghi\n1,def,ghi,123\n2,123,,abc"
JSON_TEST_DATA = """{
    "rows": [
        {
            "_id": "0",
            "col3": "ghi",
            "col2": "def",
            "col1": "abc"
        },
        {
            "_id": "1",
            "col3": "123",
            "col2": "ghi",
            "col1": "def"
        },
        {
            "_id": "2",
            "col3": "abc",
            "col2": "",
            "col1": "123"
        }
    ]
}
"""
DOES_NOT_EXIST_FILE = "./thisfiledoesnotexist"
CORRUPT_BINARY_TEST_DATA = b"BAD"
CORRUPT_CSV_TEST_DATA = b"col1,col2\n1"
CORRUPT_JSON_TEST_DATA = b"{"

BASE_TWODA = TwoDA(["col3", "col2", "col1"])
BASE_TWODA.add_row("10", {"col1": "abc", "col2": "def", "col3": "ghi"})
BASE_TWODA.add_row("1", {"col1": "def", "col2": "ghi", "col3": "123"})
BASE_TWODA.add_row("2", {"col1": "123", "col2": "", "col3": "abc"})
BINARY_TEST_DATA = bytes_2da(BASE_TWODA, ResourceType.TwoDA)
CSV_ROUNDTRIP_DATA = CSV_TEST_DATA.encode("utf-8")
JSON_ROUNDTRIP_DATA = JSON_TEST_DATA.encode("utf-8")


class TestTwoDA(unittest.TestCase):
    def test_binary_io(self):
        self.assertEqual(detect_2da(BINARY_TEST_DATA), ResourceType.TwoDA)
        twoda = TwoDABinaryReader(BINARY_TEST_DATA).load()
        self.validate_io(twoda)

        data = bytearray()
        write_2da(twoda, data, ResourceType.TwoDA)
        twoda = read_2da(data)
        self.validate_io(twoda)

    def test_csv_io(self):
        self.assertEqual(detect_2da(CSV_ROUNDTRIP_DATA), ResourceType.TwoDA_CSV)

        twoda = TwoDACSVReader(CSV_TEST_DATA.encode("utf-8")).load()
        self.validate_io(twoda)

        data = bytearray()
        write_2da(twoda, data, ResourceType.TwoDA_CSV)
        twoda = read_2da(data)
        self.validate_io(twoda)

    def test_json_io(self):
        self.assertEqual(detect_2da(JSON_ROUNDTRIP_DATA), ResourceType.TwoDA_JSON)

        twoda = TwoDAJSONReader(JSON_TEST_DATA.encode("utf-8")).load()
        self.validate_io(twoda)

        data = bytearray()
        write_2da(twoda, data, ResourceType.TwoDA_JSON)
        twoda = read_2da(data)
        self.validate_io(twoda)

    def validate_io(self, twoda):
        assert twoda.get_cell(0, "col1") == "abc"
        assert twoda.get_cell(0, "col2") == "def"
        assert twoda.get_cell(0, "col3") == "ghi"

        assert twoda.get_cell(1, "col1") == "def"
        assert twoda.get_cell(1, "col2") == "ghi"
        assert twoda.get_cell(1, "col3") == "123"

        assert twoda.get_cell(2, "col1") == "123"
        assert twoda.get_cell(2, "col2") == ""
        assert twoda.get_cell(2, "col3") == "abc"

    def test_read_raises(self):
        if os.name == "nt":
            self.assertRaises(PermissionError, read_2da, ".")
        else:
            self.assertRaises(IsADirectoryError, read_2da, ".")
        self.assertRaises(FileNotFoundError, read_2da, DOES_NOT_EXIST_FILE)
        self.assertRaises(ValueError, read_2da, CORRUPT_BINARY_TEST_DATA)
        self.assertRaises(ValueError, read_2da, CORRUPT_JSON_TEST_DATA)
        self.assertRaises(ValueError, read_2da, CORRUPT_CSV_TEST_DATA)

    def test_write_raises(self):
        if os.name == "nt":
            self.assertRaises(PermissionError, write_2da, TwoDA(), ".", ResourceType.TwoDA)
        else:
            self.assertRaises(IsADirectoryError, write_2da, TwoDA(), ".", ResourceType.TwoDA)
        self.assertRaises(ValueError, write_2da, TwoDA(), ".", ResourceType.INVALID)

    def test_row_max(self):
        twoda = TwoDA()
        twoda.add_row("0")
        twoda.add_row("1")
        twoda.add_row("2")

        assert twoda.label_max() == 3


if __name__ == "__main__":
    unittest.main()
