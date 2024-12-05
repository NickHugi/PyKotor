from __future__ import annotations

import os
import pathlib
import sys
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
from pykotor.resource.formats.lyt import (
    LYT,
    LYTAsciiReader,
    LYTDoorHook,
    LYTObstacle,
    LYTRoom,
    LYTTrack,
)

from pykotor.common.misc import ResRef
from pykotor.resource.formats.lyt.lyt_auto import read_lyt, write_lyt
from pykotor.resource.type import ResourceType

ASCII_TEST_FILE = "tests/test_pykotor/test_files/test.lyt"
DOES_NOT_EXIST_FILE = "./thisfiledoesnotexist"
CORRUPT_BINARY_TEST_FILE = "tests/test_pykotor/test_files/test_corrupted.lyt"


class TestLYT(TestCase):
    def test_binary_io(self):
        lyt = LYTAsciiReader(ASCII_TEST_FILE).load()
        self.validate_io(lyt)

        data = bytearray()
        write_lyt(lyt, data, ResourceType.LYT)
        lyt = read_lyt(data)
        self.validate_io(lyt)

    def validate_io(self, lyt: LYT):
        assert LYTRoom(ResRef("M17mg_01a"), Vector3(100.0, 100.0, 0.0)) in lyt.rooms
        assert LYTRoom(ResRef("M17mg_01b"), Vector3(100.0, 100.0, 0.0)) in lyt.rooms
        assert lyt.tracks[0] == LYTTrack(ResRef("M17mg_MGT01"), Vector3(0.0, 0.0, 0.0))
        assert lyt.tracks[1] == LYTTrack(ResRef("M17mg_MGT02"), Vector3(112.047, 209.04, 0.0))
        assert lyt.obstacles[0] == LYTObstacle(ResRef("M17mg_MGO01"), Vector3(103.309, 3691.61, 0.0))
        assert lyt.obstacles[1] == LYTObstacle(ResRef("M17mg_MGO02"), Vector3(118.969, 3688.0, 0.0))
        assert lyt.doorhooks[0] == LYTDoorHook(ResRef("M02ac_02h"), "door_01", Vector3(170.475, 66.375, 0.0), Vector4(0.707107, 0.0, 0.0, -0.707107))
        assert lyt.doorhooks[1] == LYTDoorHook(ResRef("M02ac_02a"), "door_06", Vector3(90.0, 129.525, 0.0), Vector4(1.0, 0.0, 0.0, 0.0))

    def test_read_raises(self):
        if os.name == "nt":
            self.assertRaises(PermissionError, read_lyt, ".")
        else:
            self.assertRaises(IsADirectoryError, read_lyt, ".")
        self.assertRaises(FileNotFoundError, read_lyt, DOES_NOT_EXIST_FILE)
        self.assertRaises(ValueError, read_lyt, CORRUPT_BINARY_TEST_FILE)

    def test_write_raises(self):
        if os.name == "nt":
            self.assertRaises(PermissionError, write_lyt, LYT(), ".", ResourceType.LYT)
        else:
            self.assertRaises(IsADirectoryError, write_lyt, LYT(), ".", ResourceType.LYT)
        self.assertRaises(ValueError, write_lyt, LYT(), ".", ResourceType.INVALID)


if __name__ == "__main__":
    unittest.main()
