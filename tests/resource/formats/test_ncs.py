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

from typing import TYPE_CHECKING

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.ncs import NCSBinaryReader
from pykotor.resource.formats.ncs.ncs_auto import bytes_ncs, read_ncs, write_ncs
from pathlib import Path

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs import NCS

BINARY_TEST_FILE = "tests/files/test.ncs"


EXPECTED_INSTRUCTION_COUNT = 1541


class TestNCS(TestCase):
    def test_binary_io(self):
        """Ensure binary NCS IO produces byte-identical output."""
        ncs = NCSBinaryReader(BINARY_TEST_FILE).load()
        self.validate_io(ncs)

        user_profile_path = os.environ.get("USERPROFILE")
        file_path = Path(user_profile_path or "", "Documents", "ext", "output.ncs")
        
        # Create parent directory if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        write_ncs(ncs, file_path)
        data = bytes_ncs(ncs)
        ncs = read_ncs(data)
        self.validate_io(ncs)

    def validate_io(self, ncs: NCS):
        self.assertEqual(EXPECTED_INSTRUCTION_COUNT, len(ncs.instructions))

        self.assertEqual(BinaryReader.load_file(BINARY_TEST_FILE), bytes_ncs(ncs))


if __name__ == "__main__":
    unittest.main()
