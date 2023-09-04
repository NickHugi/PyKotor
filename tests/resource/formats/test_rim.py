import os
from unittest import TestCase

from pykotor.resource.formats.rim import RIM, RIMBinaryReader, write_rim, read_rim
from pykotor.resource.type import ResourceType


BINARY_TEST_FILE = "tests/files/test.rim"
DOES_NOT_EXIST_FILE = "./thisfiledoesnotexist"
CORRUPT_BINARY_TEST_FILE = "tests/files/test_corrupted.rim"


class TestRIM(TestCase):
    def test_binary_io(self):
        rim = RIMBinaryReader(BINARY_TEST_FILE).load()
        self.validate_io(rim)

        data = bytearray()
        write_rim(rim, data)
        rim = read_rim(data)
        self.validate_io(rim)

    def validate_io(self, rim: RIM):
        self.assertEqual(len(rim), 3)
        self.assertEqual(rim.get("1", ResourceType.TXT), b"abc")
        self.assertEqual(rim.get("2", ResourceType.TXT), b"def")
        self.assertEqual(rim.get("3", ResourceType.TXT), b"ghi")

    def test_read_raises(self):
        if os.name == "nt":
            self.assertRaises(PermissionError, read_rim, ".")
        else:
            self.assertRaises(IsADirectoryError, read_rim, ".")
        self.assertRaises(FileNotFoundError, read_rim, DOES_NOT_EXIST_FILE)
        self.assertRaises(ValueError, read_rim, CORRUPT_BINARY_TEST_FILE)

    def test_write_raises(self):
        if os.name == "nt":
            self.assertRaises(PermissionError, write_rim, RIM(), ".", ResourceType.RIM)
        else:
            self.assertRaises(
                IsADirectoryError, write_rim, RIM(), ".", ResourceType.RIM
            )
        self.assertRaises(ValueError, write_rim, RIM(), ".", ResourceType.INVALID)
