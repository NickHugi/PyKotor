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
from pykotor.resource.generics.pth import PTH, construct_pth, dismantle_pth
from pykotor.extract.installation import Installation
from pykotor.resource.formats.gff.gff_data import GFF
from pykotor.resource.type import ResourceType

TEST_FILE = "src/tests/files/test.pth"
K1_PATH = os.environ.get("K1_PATH")
K2_PATH = os.environ.get("K2_PATH")


class TestPTH(unittest.TestCase):
    def setUp(self):
        self.log_messages = [os.linesep]

    def log_func(self, message=""):
        self.log_messages.append(message)

    @unittest.skipIf(
        not K1_PATH or not pathlib.Path(K1_PATH).joinpath("chitin.key").exists(),
        "K1_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k1_installation(self) -> None:
        self.installation = Installation(K1_PATH)  # type: ignore[arg-type]
        for are_resource in (resource for resource in self.installation if resource.restype() == ResourceType.PTH):
            gff: GFF = read_gff(are_resource.data())
            reconstructed_gff: GFF = dismantle_pth(construct_pth(gff))
            self.assertTrue(gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True), os.linesep.join(self.log_messages))

    @unittest.skipIf(
        not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
        "K2_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k2_installation(self) -> None:
        self.installation = Installation(K2_PATH)  # type: ignore[arg-type]
        for are_resource in (resource for resource in self.installation if resource.restype() == ResourceType.PTH):
            gff: GFF = read_gff(are_resource.data())
            reconstructed_gff: GFF = dismantle_pth(construct_pth(gff))
            self.assertTrue(gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True), os.linesep.join(self.log_messages))

    def test_gff_reconstruct(self) -> None:
        gff = read_gff(TEST_FILE)
        reconstructed_gff = dismantle_pth(construct_pth(gff))
        self.assertTrue(gff.compare(reconstructed_gff, self.log_func), os.linesep.join(self.log_messages))

    def test_io_construct(self):
        gff = read_gff(TEST_FILE)
        pth = construct_pth(gff)
        self.validate_io(pth)

    def test_io_reconstruct(self):
        gff = read_gff(TEST_FILE)
        gff = dismantle_pth(construct_pth(gff))
        pth = construct_pth(gff)
        self.validate_io(pth)

    def validate_io(self, pth: PTH):
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
