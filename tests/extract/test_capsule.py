import os
import pathlib
import sys
import unittest
from unittest import TestCase

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

from pykotor.extract.capsule import Capsule
from pykotor.resource.type import ResourceType

TEST_ERF_FILE = "tests/files/capsule.mod"
TEST_RIM_FILE = "tests/files/capsule.rim"


class TestCapsule(TestCase):
    def test_erf_capsule(self):  # sourcery skip: class-extract-method
        erf_capsule = Capsule(TEST_ERF_FILE)

        self.assertEqual(3, len(erf_capsule))

        self.assertTrue(erf_capsule.exists("001ebo", ResourceType.ARE))
        self.assertEqual(4865, len(erf_capsule.resource("001ebo", ResourceType.ARE)))
        self.assertEqual("ARE ", erf_capsule.resource("001ebo", ResourceType.ARE)[:4].decode())

        self.assertTrue(erf_capsule.info("001ebo", ResourceType.GIT))
        self.assertEqual(42565, len(erf_capsule.resource("001ebo", ResourceType.GIT)))
        self.assertEqual("GIT ", erf_capsule.resource("001ebo", ResourceType.GIT)[:4].decode())

        self.assertTrue(erf_capsule.info("001ebo", ResourceType.PTH, reload=True))
        self.assertEqual(19788, len(erf_capsule.resource("001ebo", ResourceType.PTH)))
        self.assertEqual("PTH ", erf_capsule.resource("001ebo", ResourceType.PTH)[:4].decode())

    def test_rim_capsule(self):
        rim_capsule = Capsule(TEST_RIM_FILE)

        self.assertEqual(3, len(rim_capsule))

        self.assertTrue(rim_capsule.exists("m13aa", ResourceType.ARE))
        self.assertEqual(4096, len(rim_capsule.resource("m13aa", ResourceType.ARE)))
        self.assertEqual("ARE ", rim_capsule.resource("m13aa", ResourceType.ARE)[:4].decode())

        self.assertTrue(rim_capsule.info("m13aa", ResourceType.GIT))
        self.assertEqual(51747, len(rim_capsule.resource("m13aa", ResourceType.GIT)))
        self.assertEqual("GIT ", rim_capsule.resource("m13aa", ResourceType.GIT)[:4].decode())

        self.assertTrue(rim_capsule.exists("module", ResourceType.IFO, reload=True))
        self.assertEqual(1655, len(rim_capsule.resource("module", ResourceType.IFO)))
        self.assertEqual("IFO ", rim_capsule.resource("module", ResourceType.IFO)[:4].decode())


if __name__ == "__main__":
    unittest.main()
