import pathlib
import sys
import unittest
from unittest import TestCase

from pykotor.resource.formats.gff.gff_data import GFF

THIS_SCRIPT_PATH = pathlib.Path(__file__)
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[3].resolve()
UTILITY_PATH = THIS_SCRIPT_PATH.parents[5].joinpath("Utility", "src").resolve()
if PYKOTOR_PATH.exists():
    working_dir = str(PYKOTOR_PATH)
    if working_dir in sys.path:
        sys.path.remove(working_dir)
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
    def test_io(self):
        gff: GFF = read_gff(TEST_FILE)
        utw: UTW = construct_utw(gff)
        self.validate_io(utw)

        gff = dismantle_utw(utw)
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
