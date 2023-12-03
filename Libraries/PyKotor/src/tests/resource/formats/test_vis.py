import os
import pathlib
import sys
import unittest
from unittest import TestCase

THIS_SCRIPT_PATH = pathlib.Path(__file__)
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[3].resolve()
UTILITY_PATH = THIS_SCRIPT_PATH.parents[5].joinpath("Utility", "src").resolve()
if PYKOTOR_PATH.exists():
    working_dir = str(PYKOTOR_PATH)
    if working_dir in sys.path:
        sys.path.remove(working_dir)
    sys.path.insert(0, working_dir)
if UTILITY_PATH.exists():
    working_dir = str(UTILITY_PATH)
    if working_dir in sys.path:
        sys.path.remove(working_dir)
    sys.path.insert(0, working_dir)

from pykotor.resource.formats.vis import VIS, VISAsciiReader, read_vis, write_vis
from pykotor.resource.type import ResourceType

ASCII_TEST_FILE = "src/tests/files/test.vis"
DOES_NOT_EXIST_FILE = "./thisfiledoesnotexist"
CORRUPT_ASCII_TEST_FILE = "src/tests/files/test_corrupted.vis"


class TestVIS(TestCase):
    def test_binary_io(self):
        vis = VISAsciiReader(ASCII_TEST_FILE).load()
        self.validate_io(vis)

        data = bytearray()
        write_vis(vis, data, ResourceType.VIS)
        vis = read_vis(data)
        self.validate_io(vis)

    def validate_io(self, vis: VIS):
        self.assertTrue(vis.get_visible("room_01", "room_02"))
        self.assertTrue(vis.get_visible("room_01", "room_03"))
        self.assertTrue(vis.get_visible("room_01", "room_04"))

        self.assertTrue(vis.get_visible("room_02", "room_01"))
        self.assertFalse(vis.get_visible("room_02", "room_03"))
        self.assertFalse(vis.get_visible("room_02", "room_04"))

        self.assertTrue(vis.get_visible("room_03", "room_01"))
        self.assertTrue(vis.get_visible("room_03", "room_04"))
        self.assertFalse(vis.get_visible("room_03", "room_02"))

        self.assertTrue(vis.get_visible("room_04", "room_01"))
        self.assertTrue(vis.get_visible("room_04", "room_03"))
        self.assertFalse(vis.get_visible("room_04", "room_02"))

    def test_read_raises(self):
        # sourcery skip: no-conditionals-in-tests
        if os.name == "nt":
            self.assertRaises(PermissionError, read_vis, ".")
        else:
            self.assertRaises(IsADirectoryError, read_vis, ".")
        self.assertRaises(FileNotFoundError, read_vis, DOES_NOT_EXIST_FILE)
        self.assertRaises(ValueError, read_vis, CORRUPT_ASCII_TEST_FILE)

    def test_write_raises(self):
        # sourcery skip: no-conditionals-in-tests
        if os.name == "nt":
            self.assertRaises(PermissionError, write_vis, VIS(), ".", ResourceType.VIS)
        else:
            self.assertRaises(IsADirectoryError, write_vis, VIS(), ".", ResourceType.VIS)
        self.assertRaises(ValueError, write_vis, VIS(), ".", ResourceType.INVALID)


if __name__ == "__main__":
    unittest.main()
