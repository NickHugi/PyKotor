from __future__ import annotations

import pathlib
import shutil
import sys
import tempfile
import unittest

from unittest import TestCase

THIS_SCRIPT_PATH = pathlib.Path(__file__).resolve()
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[2].joinpath("Libraries", "PyKotor", "src")
UTILITY_PATH = THIS_SCRIPT_PATH.parents[2].joinpath("Libraries", "Utility", "src")


def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from pykotor.extract.capsule import Capsule
from pykotor.resource.type import ResourceType

TEST_ERF_FILE = "tests/files/capsule.mod"
TEST_RIM_FILE = "tests/files/capsule.rim"


class TestCapsule(TestCase):
    def test_add_to_rim_file(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            temp_rim_path = pathlib.Path(tmpdirname).joinpath("capsule.rim")
            shutil.copy(TEST_RIM_FILE, temp_rim_path)
            resource_name = "image"
            resource_type = ResourceType.PNG
            resource_data = b"image data"

            rim_capsule = Capsule(temp_rim_path)
            rim_capsule.add(resource_name, resource_type, resource_data)

            self.assertEqual(4, len(rim_capsule))

            self.assertTrue(rim_capsule.contains("m13aa", ResourceType.ARE))
            self.assertEqual(4096, len(rim_capsule.resource("m13aa", ResourceType.ARE)))
            self.assertEqual("ARE ", rim_capsule.resource("m13aa", ResourceType.ARE)[:4].decode())

            self.assertTrue(rim_capsule.info("m13aa", ResourceType.GIT))
            self.assertEqual(51747, len(rim_capsule.resource("m13aa", ResourceType.GIT)))
            self.assertEqual("GIT ", rim_capsule.resource("m13aa", ResourceType.GIT)[:4].decode())

            self.assertTrue(rim_capsule.contains("module", ResourceType.IFO, reload=True))
            self.assertEqual(1655, len(rim_capsule.resource("module", ResourceType.IFO)))
            self.assertEqual("IFO ", rim_capsule.resource("module", ResourceType.IFO)[:4].decode())

            self.assertTrue(rim_capsule.contains(resource_name, resource_type, reload=True))
            self.assertEqual(10, len(rim_capsule.resource(resource_name, resource_type)))
            self.assertEqual(resource_data, rim_capsule.resource(resource_name, resource_type))

    def test_add_to_erf_file(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            temp_erf_path = pathlib.Path(tmpdirname).joinpath("capsule.rim")
            shutil.copy(TEST_ERF_FILE, temp_erf_path)
            resource_name = "sound"
            resource_type = ResourceType.WAV
            resource_data = b"sound data"

            erf_capsule = Capsule(temp_erf_path)
            erf_capsule.add(resource_name, resource_type, resource_data)

            self.assertEqual(4, len(erf_capsule))

            self.assertTrue(erf_capsule.contains("001ebo", ResourceType.ARE))
            self.assertEqual(4865, len(erf_capsule.resource("001ebo", ResourceType.ARE)))
            self.assertEqual("ARE ", erf_capsule.resource("001ebo", ResourceType.ARE)[:4].decode())

            self.assertTrue(erf_capsule.info("001ebo", ResourceType.GIT))
            self.assertEqual(42565, len(erf_capsule.resource("001ebo", ResourceType.GIT)))
            self.assertEqual("GIT ", erf_capsule.resource("001ebo", ResourceType.GIT)[:4].decode())

            self.assertTrue(erf_capsule.info("001ebo", ResourceType.PTH, reload=True))
            self.assertEqual(19788, len(erf_capsule.resource("001ebo", ResourceType.PTH)))
            self.assertEqual("PTH ", erf_capsule.resource("001ebo", ResourceType.PTH)[:4].decode())

            self.assertTrue(erf_capsule.contains(resource_name, resource_type, reload=True))
            self.assertEqual(10, len(erf_capsule.resource(resource_name, resource_type)))
            self.assertEqual(resource_data, erf_capsule.resource(resource_name, resource_type))

    def test_erf_capsule(self):  # sourcery skip: class-extract-method
        erf_capsule = Capsule(TEST_ERF_FILE)

        self.assertEqual(3, len(erf_capsule))

        self.assertTrue(erf_capsule.contains("001ebo", ResourceType.ARE))
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

        self.assertTrue(rim_capsule.contains("m13aa", ResourceType.ARE))
        self.assertEqual(4096, len(rim_capsule.resource("m13aa", ResourceType.ARE)))
        self.assertEqual("ARE ", rim_capsule.resource("m13aa", ResourceType.ARE)[:4].decode())

        self.assertTrue(rim_capsule.info("m13aa", ResourceType.GIT))
        self.assertEqual(51747, len(rim_capsule.resource("m13aa", ResourceType.GIT)))
        self.assertEqual("GIT ", rim_capsule.resource("m13aa", ResourceType.GIT)[:4].decode())

        self.assertTrue(rim_capsule.contains("module", ResourceType.IFO, reload=True))
        self.assertEqual(1655, len(rim_capsule.resource("module", ResourceType.IFO)))
        self.assertEqual("IFO ", rim_capsule.resource("module", ResourceType.IFO)[:4].decode())


if __name__ == "__main__":
    unittest.main()
