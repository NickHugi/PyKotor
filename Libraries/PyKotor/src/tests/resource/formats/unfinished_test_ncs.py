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
        os.chdir(PYKOTOR_PATH.parent)
    sys.path.insert(0, working_dir)
if UTILITY_PATH.exists():
    working_dir = str(UTILITY_PATH)
    if working_dir in sys.path:
        sys.path.remove(working_dir)
    sys.path.insert(0, working_dir)

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.ncs import NCS, NCSBinaryReader
from pykotor.resource.formats.ncs.ncs_auto import bytes_ncs, read_ncs, write_ncs
from utility.path import Path

BINARY_TEST_FILE = "src/tests/files/test.ncs"


class TestNCS(TestCase):
    def test_binary_io(self):
        ncs = NCSBinaryReader(BINARY_TEST_FILE).load()
        self.validate_io(ncs)

        user_profile_path = os.environ.get("USERPROFILE")
        file_path = Path(user_profile_path, "Documents", "ext", "output.ncs")

        write_ncs(ncs, file_path)
        data = bytes_ncs(ncs)
        ncs = read_ncs(data)
        self.validate_io(ncs)

    def validate_io(self, ncs: NCS):
        self.assertEqual(8, len(ncs.instructions))

        self.assertEqual(BinaryReader.load_file(BINARY_TEST_FILE), bytes_ncs(ncs))


if __name__ == "__main__":
    unittest.main()
