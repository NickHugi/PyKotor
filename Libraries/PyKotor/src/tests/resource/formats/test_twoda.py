import os
import pathlib
import sys
import unittest

if getattr(sys, "frozen", False) is False:
    pykotor_path = pathlib.Path(__file__).parents[3] / "pykotor"
    if pykotor_path.exists():
        working_dir = str(pykotor_path.parent)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.insert(0, str(pykotor_path.parent))

from pykotor.resource.formats.twoda import TwoDA, TwoDABinaryReader, TwoDACSVReader, detect_2da, read_2da, write_2da
from pykotor.resource.formats.twoda.io_twoda_json import TwoDAJSONReader
from pykotor.resource.type import ResourceType

BINARY_TEST_FILE = "src/tests/files/test.2da"
CSV_TEST_FILE = "src/tests/files/test.2da.csv"
JSON_TEST_FILE = "src/tests/files/test.2da.json"
DOES_NOT_EXIST_FILE = "./thisfiledoesnotexist"
CORRUPT_BINARY_TEST_FILE = "src/tests/files/test_corrupted.2da"
CORRUPT_CSV_TEST_FILE = "src/tests/files/test_corrupted.2da.csv"
CORRUPT_JSON_TEST_FILE = "src/tests/files/test_corrupted.2da.json"


class TestTwoDA(unittest.TestCase):
    def test_binary_io(self):
        self.assertEqual(detect_2da(BINARY_TEST_FILE), ResourceType.TwoDA)
        twoda = TwoDABinaryReader(BINARY_TEST_FILE).load()
        self.validate_io(twoda)

        data = bytearray()
        write_2da(twoda, data, ResourceType.TwoDA)
        twoda = read_2da(data)
        self.validate_io(twoda)

    def test_csv_io(self):
        self.assertEqual(detect_2da(CSV_TEST_FILE), ResourceType.TwoDA_CSV)

        twoda = TwoDACSVReader(CSV_TEST_FILE).load()
        self.validate_io(twoda)

        data = bytearray()
        write_2da(twoda, data, ResourceType.TwoDA_CSV)
        twoda = read_2da(data)
        self.validate_io(twoda)

    def test_json_io(self):
        self.assertEqual(detect_2da(JSON_TEST_FILE), ResourceType.TwoDA_JSON)

        twoda = TwoDAJSONReader(JSON_TEST_FILE).load()
        self.validate_io(twoda)

        data = bytearray()
        write_2da(twoda, data, ResourceType.TwoDA_JSON)
        twoda = read_2da(data)
        self.validate_io(twoda)

    def validate_io(self, twoda):
        self.assertEqual("abc", twoda.get_cell(0, "col1"))
        self.assertEqual("def", twoda.get_cell(0, "col2"))
        self.assertEqual("ghi", twoda.get_cell(0, "col3"))

        self.assertEqual("def", twoda.get_cell(1, "col1"))
        self.assertEqual("ghi", twoda.get_cell(1, "col2"))
        self.assertEqual("123", twoda.get_cell(1, "col3"))

        self.assertEqual("123", twoda.get_cell(2, "col1"))
        self.assertEqual("", twoda.get_cell(2, "col2"))
        self.assertEqual("abc", twoda.get_cell(2, "col3"))

    def test_read_raises(self):
        if os.name == "nt":
            self.assertRaises(PermissionError, read_2da, ".")
        else:
            self.assertRaises(IsADirectoryError, read_2da, ".")
        self.assertRaises(FileNotFoundError, read_2da, DOES_NOT_EXIST_FILE)
        self.assertRaises(ValueError, read_2da, CORRUPT_BINARY_TEST_FILE)
        self.assertRaises(ValueError, read_2da, CORRUPT_JSON_TEST_FILE)
        self.assertRaises(ValueError, read_2da, CORRUPT_CSV_TEST_FILE)

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

        self.assertEqual(3, twoda.label_max())

if __name__ == "__main__":
    unittest.main()
