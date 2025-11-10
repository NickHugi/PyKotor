from __future__ import annotations

import pathlib
import shutil
import sys
import tempfile
import unittest
from unittest import TestCase

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

from pykotor.extract.capsule import Capsule
from pykotor.resource.type import ResourceType

TEST_ERF_FILE = "tests/test_pykotor/test_files/capsule.mod"
TEST_RIM_FILE = "tests/test_pykotor/test_files/capsule.rim"


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

            assert len(rim_capsule) == 4

            assert rim_capsule.contains("m13aa", ResourceType.ARE)
            assert len(rim_capsule.resource("m13aa", ResourceType.ARE)) == 4096
            assert rim_capsule.resource("m13aa", ResourceType.ARE)[:4].decode() == "ARE "

            assert rim_capsule.info("m13aa", ResourceType.GIT)
            assert len(rim_capsule.resource("m13aa", ResourceType.GIT)) == 51747
            assert rim_capsule.resource("m13aa", ResourceType.GIT)[:4].decode() == "GIT "

            assert rim_capsule.contains("module", ResourceType.IFO, reload=True)
            assert len(rim_capsule.resource("module", ResourceType.IFO)) == 1655
            assert rim_capsule.resource("module", ResourceType.IFO)[:4].decode() == "IFO "

            assert rim_capsule.contains(resource_name, resource_type, reload=True)
            assert len(rim_capsule.resource(resource_name, resource_type)) == 10
            assert resource_data == rim_capsule.resource(resource_name, resource_type)

    def test_add_to_erf_file(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            temp_erf_path = pathlib.Path(tmpdirname).joinpath("capsule.rim")
            shutil.copy(TEST_ERF_FILE, temp_erf_path)
            resource_name = "sound"
            resource_type = ResourceType.WAV
            resource_data = b"sound data"

            erf_capsule = Capsule(temp_erf_path)
            erf_capsule.add(resource_name, resource_type, resource_data)

            assert len(erf_capsule) == 4

            assert erf_capsule.contains("001ebo", ResourceType.ARE)
            assert len(erf_capsule.resource("001ebo", ResourceType.ARE)) == 4865
            assert erf_capsule.resource("001ebo", ResourceType.ARE)[:4].decode() == "ARE "

            assert erf_capsule.info("001ebo", ResourceType.GIT)
            assert len(erf_capsule.resource("001ebo", ResourceType.GIT)) == 42565
            assert erf_capsule.resource("001ebo", ResourceType.GIT)[:4].decode() == "GIT "

            assert erf_capsule.info("001ebo", ResourceType.PTH, reload=True)
            assert len(erf_capsule.resource("001ebo", ResourceType.PTH)) == 19788
            assert erf_capsule.resource("001ebo", ResourceType.PTH)[:4].decode() == "PTH "

            assert erf_capsule.contains(resource_name, resource_type, reload=True)
            assert len(erf_capsule.resource(resource_name, resource_type)) == 10
            assert resource_data == erf_capsule.resource(resource_name, resource_type)

    def test_erf_capsule(self):  # sourcery skip: class-extract-method
        erf_capsule = Capsule(TEST_ERF_FILE)

        assert len(erf_capsule) == 3

        assert erf_capsule.contains("001ebo", ResourceType.ARE)
        assert len(erf_capsule.resource("001ebo", ResourceType.ARE)) == 4865
        assert erf_capsule.resource("001ebo", ResourceType.ARE)[:4].decode() == "ARE "

        assert erf_capsule.info("001ebo", ResourceType.GIT)
        assert len(erf_capsule.resource("001ebo", ResourceType.GIT)) == 42565
        assert erf_capsule.resource("001ebo", ResourceType.GIT)[:4].decode() == "GIT "

        assert erf_capsule.info("001ebo", ResourceType.PTH, reload=True)
        assert len(erf_capsule.resource("001ebo", ResourceType.PTH)) == 19788
        assert erf_capsule.resource("001ebo", ResourceType.PTH)[:4].decode() == "PTH "

    def test_rim_capsule(self):
        rim_capsule = Capsule(TEST_RIM_FILE)

        assert len(rim_capsule) == 3

        assert rim_capsule.contains("m13aa", ResourceType.ARE)
        assert len(rim_capsule.resource("m13aa", ResourceType.ARE)) == 4096
        assert rim_capsule.resource("m13aa", ResourceType.ARE)[:4].decode() == "ARE "

        assert rim_capsule.info("m13aa", ResourceType.GIT)
        assert len(rim_capsule.resource("m13aa", ResourceType.GIT)) == 51747
        assert rim_capsule.resource("m13aa", ResourceType.GIT)[:4].decode() == "GIT "

        assert rim_capsule.contains("module", ResourceType.IFO, reload=True)
        assert len(rim_capsule.resource("module", ResourceType.IFO)) == 1655
        assert rim_capsule.resource("module", ResourceType.IFO)[:4].decode() == "IFO "


if __name__ == "__main__":
    unittest.main()
