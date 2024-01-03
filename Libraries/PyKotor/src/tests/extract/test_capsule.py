import os
import pathlib
import sys
import unittest
from unittest import TestCase

THIS_SCRIPT_PATH = pathlib.Path(__file__)
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[2].resolve()
UTILITY_PATH = THIS_SCRIPT_PATH.parents[4].joinpath("Utility", "src").resolve()
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

from pykotor.extract.capsule import Capsule
from pykotor.resource.type import ResourceType

TEST_ERF_FILE = "src/tests/files/capsule.mod"
TEST_RIM_FILE = "src/tests/files/capsule.rim"


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
