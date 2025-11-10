from __future__ import annotations

import pathlib
import sys

THIS_SCRIPT_PATH = pathlib.Path(__file__).resolve()
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[3].joinpath("Libraries", "PyKotor", "src")
UTILITY_PATH = THIS_SCRIPT_PATH.parents[3].joinpath("Libraries", "Utility", "src")


def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

import unittest

from pykotor.common.language import Language
from pykotor.extract.talktable import TalkTable

TEST_FILE = "tests/test_pykotor/test_files/test.tlk"


class TestTalkTable(unittest.TestCase):
    def test_size(self):
        talktable = TalkTable(TEST_FILE)
        assert talktable.size() == 3

    def test_string(self):
        talktable = TalkTable(TEST_FILE)
        assert talktable.string(0) == "abcdef"
        assert talktable.string(1) == "ghijklmnop"
        assert talktable.string(2) == "qrstuvwxyz"
        assert talktable.string(-1) == ""
        assert talktable.string(3) == ""

    def test_voiceover(self):
        talktable = TalkTable(TEST_FILE)
        assert str(talktable.sound(0)) == "resref01"
        assert str(talktable.sound(1)) == "resref02"
        assert str(talktable.sound(2)) == ""
        assert str(talktable.sound(-1)) == ""
        assert str(talktable.sound(3)) == ""

    def test_batch(self):
        talktable = TalkTable(TEST_FILE)
        batch = talktable.batch([2, 0, -1, 3])
        assert batch[0] == ("abcdef", "resref01")
        assert batch[2] == ("qrstuvwxyz", "")
        assert batch[-1] == ("", "")
        assert batch[3] == ("", "")

    def test_language(self):
        talktable = TalkTable(TEST_FILE)
        assert talktable.language() == Language.ENGLISH


if __name__ == "__main__":
    unittest.main()
