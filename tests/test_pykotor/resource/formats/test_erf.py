from __future__ import annotations

import os
import pathlib
import sys
import unittest

from pykotor.resource.formats.erf.erf_data import ERFType

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

from unittest import TestCase

from pathlib import Path

from pykotor.resource.formats.erf import ERF, ERFBinaryReader, read_erf, write_erf
from pykotor.resource.type import ResourceType
from pathlib import Path

BINARY_TEST_FILE = Path("tests/test_pykotor/test_files/test.erf").resolve()
DOES_NOT_EXIST_FILE = "./thisfiledoesnotexist"
CORRUPT_BINARY_TEST_FILE = Path("tests/test_pykotor/test_files/test_corrupted.gff")


class TestERF(TestCase):
    def test_binary_io(self):
        erf = ERFBinaryReader(BINARY_TEST_FILE).load()
        self.validate_io(erf)

        data = bytearray()
        write_erf(erf, data)
        erf = ERFBinaryReader(data).load()
        self.validate_io(erf)

    def validate_io(self, erf: ERF):
        assert len(erf) == 3
        assert erf.get("1", ResourceType.TXT) == b"abc"
        assert erf.get("2", ResourceType.TXT) == b"def"
        assert erf.get("3", ResourceType.TXT) == b"ghi"

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
            self.assertRaises(PermissionError, write_erf, ERF(ERFType.ERF), ".", ResourceType.ERF)
        else:
            self.assertRaises(IsADirectoryError, write_erf, ERF(ERFType.ERF), ".", ResourceType.ERF)
        self.assertRaises(ValueError, write_erf, ERF(ERFType.ERF), ".", ResourceType.INVALID)


if __name__ == "__main__":
    unittest.main()
