from __future__ import annotations

import os
import pathlib
import sys
import unittest

from unittest import TestCase

from pykotor.resource.type import ResourceType

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

from pykotor.common.misc import Game
from pykotor.extract.installation import Installation
from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.utw import construct_utw, dismantle_utw

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFF
    from pykotor.resource.generics.utw import UTW

TEST_FILE = "tests/files/test.utw"
K1_PATH = os.environ.get("K1_PATH")
K2_PATH = os.environ.get("K2_PATH")


class TestUTW(TestCase):
    def setUp(self):
        self.log_messages = [os.linesep]

    def log_func(self, *msgs):
        self.log_messages.append("\t".join(msgs))

    @unittest.skipIf(
        not K1_PATH or not pathlib.Path(K1_PATH).joinpath("chitin.key").exists(),
        "K1_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k1_installation(self):
        self.installation = Installation(K1_PATH)  # type: ignore[arg-type]
        for resource in (resource for resource in self.installation if resource.restype() is ResourceType.UTW):
            gff: GFF = read_gff(resource.data())
            reconstructed_gff: GFF = dismantle_utw(construct_utw(gff), Game.K1)
            self.assertTrue(gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True), os.linesep.join(self.log_messages))

    @unittest.skipIf(
        not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
        "K2_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k2_installation(self):
        self.installation = Installation(K2_PATH)  # type: ignore[arg-type]
        for resource in (resource for resource in self.installation if resource.restype() is ResourceType.UTW):
            gff: GFF = read_gff(resource.data())
            reconstructed_gff: GFF = dismantle_utw(construct_utw(gff))
            self.assertTrue(gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True), os.linesep.join(self.log_messages))

    def test_gff_reconstruct(self):
        gff = read_gff(TEST_FILE)
        reconstructed_gff = dismantle_utw(construct_utw(gff))
        self.assertTrue(gff.compare(reconstructed_gff, self.log_func), os.linesep.join(self.log_messages))

    def test_io_construct(self):
        gff = read_gff(TEST_FILE)
        utw = construct_utw(gff)
        self.validate_io(utw)

    def test_io_reconstruct(self):
        gff = read_gff(TEST_FILE)
        gff = dismantle_utw(construct_utw(gff))
        utw = construct_utw(gff)
        self.validate_io(utw)

    def validate_io(self, utw: UTW):
        self.assertEqual(1, utw.appearance_id)
        self.assertEqual("", utw.linked_to)
        self.assertEqual("sw_mapnote011", utw.resref)
        self.assertEqual("MN_106PER2", utw.tag)
        self.assertEqual(76857, utw.name.stringref)
        self.assertEqual(-1, utw.description.stringref)
        self.assertTrue(utw.has_map_note)
        self.assertEqual(76858, utw.map_note.stringref)
        self.assertEqual(1, utw.map_note_enabled)
        self.assertEqual(5, utw.palette_id)
        self.assertEqual("comment", utw.comment)


if __name__ == "__main__":
    unittest.main()
