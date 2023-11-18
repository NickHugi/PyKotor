import os
import pathlib
import sys
import unittest

if getattr(sys, "frozen", False) is False:
    pykotor_path = pathlib.Path(__file__).parents[3] / "pykotor"
    if pykotor_path.joinpath("__init__.py").exists():
        working_dir = str(pykotor_path.parent)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.insert(0, str(pykotor_path.parent))

from unittest import TestCase

from pykotor.utility.path import Path
from pykotor.resource.formats.erf import ERF, ERFBinaryReader, read_erf, write_erf
from pykotor.resource.type import ResourceType

BINARY_TEST_FILE = Path("tests/files/test.erf")
DOES_NOT_EXIST_FILE = "./thisfiledoesnotexist"
CORRUPT_BINARY_TEST_FILE = Path("tests/files/test_corrupted.gff")


class TestERF(TestCase):
    def test_binary_io(self):
        erf = ERFBinaryReader(BINARY_TEST_FILE).load()
        self.validate_io(erf)

        data = bytearray()
        write_erf(erf, data)
        erf = ERFBinaryReader(data).load()
        self.validate_io(erf)

    def validate_io(self, erf: ERF):
        self.assertEqual(len(erf), 3)
        self.assertEqual(erf.get("1", ResourceType.TXT), b"abc")
        self.assertEqual(erf.get("2", ResourceType.TXT), b"def")
        self.assertEqual(erf.get("3", ResourceType.TXT), b"ghi")

    # sourcery skip: no-conditionals-in-tests
    def test_read_raises(self):
        if os.name == "nt":
            self.assertRaises(PermissionError, read_erf, ".")
        else:
            self.assertRaises(IsADirectoryError, read_erf, ".")
        self.assertRaises(FileNotFoundError, read_erf, DOES_NOT_EXIST_FILE)
        self.assertRaises(ValueError, read_erf, CORRUPT_BINARY_TEST_FILE)

    def test_write_raises(self):
        if os.name == "nt":
            self.assertRaises(PermissionError, write_erf, ERF(), ".", ResourceType.ERF)
        else:
            self.assertRaises(IsADirectoryError, write_erf, ERF(), ".", ResourceType.ERF)
        self.assertRaises(ValueError, write_erf, ERF(), ".", ResourceType.INVALID)


if __name__ == "__main__":
    unittest.main()
