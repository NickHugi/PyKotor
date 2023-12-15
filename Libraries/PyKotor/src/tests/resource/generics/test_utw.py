import os
import pathlib
import sys
import unittest
from unittest import TestCase


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

from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.utw import UTW, construct_utw, dismantle_utw

TEST_FILE = "src/tests/files/test.utw"


class TestUTW(TestCase):
    def setUp(self):
        self.log_messages = [os.linesep]

    def log_func(self, message=""):
        self.log_messages.append(message)

    def test_gff_reconstruct(self) -> None:
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
