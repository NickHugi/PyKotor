from __future__ import annotations

import os
import pathlib
import sys
import unittest

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

from pykotor.common.geometry import Vector2
from pykotor.common.misc import Game
from pykotor.extract.installation import Installation
from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.pth import construct_pth, dismantle_pth
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFF
    from pykotor.resource.generics.pth import PTH

TEST_FILE = "tests/files/test.pth"
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
    def test_gff_reconstruct_from_k1_installation(self):
        self.installation = Installation(K1_PATH)  # type: ignore[arg-type]
        for pth_resource in (resource for resource in self.installation if resource.restype() is ResourceType.PTH):
            gff: GFF = read_gff(pth_resource.data())
            reconstructed_gff: GFF = dismantle_pth(construct_pth(gff), Game.K1)
            self.assertTrue(gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True), os.linesep.join(self.log_messages))

    @unittest.skipIf(
        not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
        "K2_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k2_installation(self):
        self.installation = Installation(K2_PATH)  # type: ignore[arg-type]
        for pth_resource in (resource for resource in self.installation if resource.restype() is ResourceType.PTH):
            gff: GFF = read_gff(pth_resource.data())
            reconstructed_gff: GFF = dismantle_pth(construct_pth(gff))
            self.assertTrue(gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True), os.linesep.join(self.log_messages))

    def test_gff_reconstruct(self):
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
