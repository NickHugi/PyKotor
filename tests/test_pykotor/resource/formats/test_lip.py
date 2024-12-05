from __future__ import annotations

import os
import pathlib
import sys
import unittest
from unittest import TestCase

THIS_SCRIPT_PATH: pathlib.Path = pathlib.Path(__file__).resolve()
PYKOTOR_PATH: pathlib.Path = THIS_SCRIPT_PATH.parents[3].resolve()
UTILITY_PATH: pathlib.Path = THIS_SCRIPT_PATH.parents[5].joinpath("Utility", "src").resolve()


def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from pykotor.resource.formats.lip import LIP, LIPBinaryReader, LIPShape, LIPXMLReader, detect_lip, read_lip, write_lip

from pykotor.resource.type import ResourceType

BINARY_TEST_FILE = "tests/test_pykotor/test_files/test.lip"
XML_TEST_FILE = "tests/test_pykotor/test_files/test.lip.xml"
DOES_NOT_EXIST_FILE = "./thisfiledoesnotexist"
CORRUPT_BINARY_TEST_FILE = "tests/test_pykotor/test_files/test_corrupted.lip"
CORRUPT_XML_TEST_FILE = "tests/test_pykotor/test_files/test_corrupted.lip.xml"


class TestLIP(TestCase):
    def test_binary_io(self):
        assert detect_lip(BINARY_TEST_FILE) == ResourceType.LIP

        lip: LIP = LIPBinaryReader(BINARY_TEST_FILE).load()
        self.validate_io(lip)

        data = bytearray()
        write_lip(lip, data, ResourceType.LIP)
        lip = LIPBinaryReader(data).load()
        self.validate_io(lip)

    def test_xml_io(self):
        assert detect_lip(XML_TEST_FILE) == ResourceType.LIP_XML

        lip: LIP = LIPXMLReader(XML_TEST_FILE).load()
        self.validate_io(lip)

        data = bytearray()
        write_lip(lip, data, ResourceType.LIP_XML)
        lip = LIPXMLReader(data).load()
        self.validate_io(lip)

    def validate_io(
        self,
        lip: LIP,
    ):
        self.assertAlmostEqual(lip.length, 1.50, 3)
        assert lip.get(0).shape == LIPShape.NEUTRAL, f"Expected {LIPShape.NEUTRAL!r} but got {lip.get(0).shape!r}"
        assert lip.get(1).shape == LIPShape.OOH, f"Expected {LIPShape.OOH!r} but got {lip.get(1).shape!r}"
        assert lip.get(2).shape == LIPShape.TH, f"Expected {LIPShape.TH!r} but got {lip.get(2).shape!r}"
        self.assertAlmostEqual(0.0, lip.get(0).time, 4, f"Expected 0.0 but got {lip.get(0).time}")
        self.assertAlmostEqual(0.7777, lip.get(1).time, 4, f"Expected 0.7777 but got {lip.get(1).time}")
        self.assertAlmostEqual(1.25, lip.get(2).time, 4, f"Expected 1.25 but got {lip.get(2).time}")

    def test_read_raises(self):
        if os.name == "nt":
            self.assertRaises(PermissionError, read_lip, ".")
        else:
            self.assertRaises(IsADirectoryError, read_lip, ".")
        self.assertRaises(FileNotFoundError, read_lip, DOES_NOT_EXIST_FILE)
        self.assertRaises(ValueError, read_lip, CORRUPT_BINARY_TEST_FILE)
        self.assertRaises(ValueError, read_lip, CORRUPT_XML_TEST_FILE)

    def test_write_raises(self):
        if os.name == "nt":
            self.assertRaises(PermissionError, write_lip, LIP(), ".", ResourceType.LIP)
        else:
            self.assertRaises(IsADirectoryError, write_lip, LIP(), ".", ResourceType.LIP)
        self.assertRaises(ValueError, write_lip, LIP(), ".", ResourceType.INVALID)


if __name__ == "__main__":
    unittest.main()
