from unittest import TestCase

from pykotor.resource.formats.twoda import TwoDA, write_2da, TwoDABinaryReader, load_2da, detect_2da, TwoDACSVReader
from pykotor.resource.formats.twoda.io_twoda_json import TwoDAJSONReader, TwoDAJSONWriter
from pykotor.resource.type import ResourceType

BINARY_TEST_FILE = "../../files/test.2da"
CSV_TEST_FILE = "../../files/test.2da.csv"
JSON_TEST_FILE = "../../files/test.2da.json"


class TestTwoDA(TestCase):
    def test_binary_io(self):
        self.assertEqual(detect_2da(BINARY_TEST_FILE), ResourceType.TwoDA)
        twoda = TwoDABinaryReader(BINARY_TEST_FILE).load()
        self.validate_io(twoda)

        data = bytearray()
        write_2da(twoda, data, ResourceType.TwoDA)
        twoda = load_2da(data)
        self.validate_io(twoda)

    def test_csv_io(self):
        self.assertEqual(detect_2da(CSV_TEST_FILE), ResourceType.TwoDA_CSV)

        twoda = TwoDACSVReader(CSV_TEST_FILE).load()
        self.validate_io(twoda)

        data = bytearray()
        write_2da(twoda, data, ResourceType.TwoDA_CSV)
        twoda = load_2da(data)
        self.validate_io(twoda)

    def test_json_io(self):
        self.assertEqual(detect_2da(JSON_TEST_FILE), ResourceType.TwoDA_JSON)

        twoda = TwoDAJSONReader(JSON_TEST_FILE).load()
        self.validate_io(twoda)

        data = bytearray()
        write_2da(twoda, data, ResourceType.TwoDA_JSON)
        twoda = load_2da(data)
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
