import os
import pathlib
import sys

THIS_SCRIPT_PATH = pathlib.Path(__file__).resolve()
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[2]
UTILITY_PATH = THIS_SCRIPT_PATH.parents[4].joinpath("Utility", "src")
def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)
if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
    os.chdir(PYKOTOR_PATH.parent)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

import unittest

from pykotor.common.language import Language
from pykotor.extract.talktable import TalkTable

TEST_FILE = "tests/files/test.tlk"


class TestTalkTable(unittest.TestCase):
    def test_size(self):
        talktable = TalkTable(TEST_FILE)
        self.assertEqual(3, talktable.size())

    def test_string(self):
        talktable = TalkTable(TEST_FILE)
        self.assertEqual("abcdef", talktable.string(0))
        self.assertEqual("ghijklmnop", talktable.string(1))
        self.assertEqual("qrstuvwxyz", talktable.string(2))
        self.assertEqual("", talktable.string(-1))
        self.assertEqual("", talktable.string(3))

    def test_voiceover(self):
        talktable = TalkTable(TEST_FILE)
        self.assertEqual("resref01", str(talktable.sound(0)))
        self.assertEqual("resref02", str(talktable.sound(1)))
        self.assertEqual("", str(talktable.sound(2)))
        self.assertEqual("", str(talktable.sound(-1)))
        self.assertEqual("", str(talktable.sound(3)))

    def test_batch(self):
        talktable = TalkTable(TEST_FILE)
        batch = talktable.batch([2, 0, -1, 3])
        self.assertEqual(("abcdef", "resref01"), batch[0])
        self.assertEqual(("qrstuvwxyz", ""), batch[2])
        self.assertEqual(("", ""), batch[-1])
        self.assertEqual(("", ""), batch[3])

    def test_language(self):
        talktable = TalkTable(TEST_FILE)
        self.assertEqual(talktable.language(), Language.ENGLISH)

if __name__ == "__main__":
    unittest.main()
