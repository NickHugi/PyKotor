from unittest import TestCase

from pykotor.resource.formats.gff import load_gff
from pykotor.resource.generics.utw import construct_utw, dismantle_utw

TEST_FILE = "../../files/test.utw"


class TestUTW(TestCase):
    def test_io(self):
        gff = load_gff(TEST_FILE)
        utw = construct_utw(gff)
        self.validate_io(utw)

        gff = dismantle_utw(utw)
        utw = construct_utw(gff)
        self.validate_io(utw)

    def validate_io(self, utw):
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
