import os
import pathlib
import sys
import unittest

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

from pykotor.common.geometry import Vector2
from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.pth import construct_pth, dismantle_pth

TEST_FILE = "src/tests/files/test.pth"


class TestPTH(unittest.TestCase):
    def test_io(self):
        gff = read_gff(TEST_FILE)
        pth = construct_pth(gff)
        self.validate_io(pth)

        gff = dismantle_pth(pth)
        pth = construct_pth(gff)
        self.validate_io(pth)

    def validate_io(self, pth):
        self.assertEqual(pth.get(0), Vector2(0.0, 0.0))
        self.assertEqual(pth.get(1), Vector2(0.0, 1.0))
        self.assertEqual(pth.get(2), Vector2(1.0, 1.0))
        self.assertEqual(pth.get(3), Vector2(0.0, 2.0))

        self.assertEqual(2, len(pth.outgoing(0)))
        self.assertTrue(pth.is_connected(0, 1))
        self.assertTrue(pth.is_connected(0, 2))

        self.assertEqual(3, len(pth.outgoing(1)))
        self.assertTrue(pth.is_connected(1, 0))
        self.assertTrue(pth.is_connected(1, 2))
        self.assertTrue(pth.is_connected(1, 3))

        self.assertEqual(2, len(pth.outgoing(2)))
        self.assertTrue(pth.is_connected(2, 0))
        self.assertTrue(pth.is_connected(2, 1))

        self.assertEqual(1, len(pth.outgoing(3)))
        self.assertTrue(pth.is_connected(3, 1))


if __name__ == "__main__":
    unittest.main()
