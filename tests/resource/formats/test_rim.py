from unittest import TestCase

from pykotor.resource.formats.rim import RIM
from pykotor.resource.type import ResourceType

BINARY_TEST_FILE = "../../files/test.rim"


class TestRIM(TestCase):
    def test_binary_io(self):
        rim: RIM = RIM.load_binary(BINARY_TEST_FILE)
        self.validate_io(rim)

        data = bytearray()
        rim.write_binary(data)
        RIM.load_binary(data)

    def validate_io(self, rim: RIM):
        self.assertEqual(len(rim), 3)
        self.assertEqual(rim.get("1", ResourceType.TXT), b'abc')
        self.assertEqual(rim.get("2", ResourceType.TXT), b'def')
        self.assertEqual(rim.get("3", ResourceType.TXT), b'ghi')
