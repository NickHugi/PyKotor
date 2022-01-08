from unittest import TestCase

from pykotor.resource.formats.rim import RIM, RIMBinaryReader, write_rim, RIMBinaryWriter, load_rim
from pykotor.resource.type import ResourceType

BINARY_TEST_FILE = "../../files/test.rim"


class TestRIM(TestCase):
    def test_binary_io(self):
        rim = RIMBinaryReader(BINARY_TEST_FILE).load()
        self.validate_io(rim)

        data = bytearray()
        write_rim(rim, data)
        rim = load_rim(data)
        self.validate_io(rim)

    def validate_io(self, rim: RIM):
        self.assertEqual(len(rim), 3)
        self.assertEqual(rim.get("1", ResourceType.TXT), b'abc')
        self.assertEqual(rim.get("2", ResourceType.TXT), b'def')
        self.assertEqual(rim.get("3", ResourceType.TXT), b'ghi')
