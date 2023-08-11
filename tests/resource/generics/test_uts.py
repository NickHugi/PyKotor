from unittest import TestCase

from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.uts import construct_uts, dismantle_uts

TEST_FILE = "../../files/test.uts"


class TestUTS(TestCase):
    def test_io(self):
        gff = read_gff(TEST_FILE)
        uts = construct_uts(gff)
        self.validate_io(uts)

        gff = dismantle_uts(uts)
        uts = construct_uts(gff)
        self.validate_io(uts)

    def validate_io(self, uts):
        self.assertEqual("3Csounds", uts.tag)
        self.assertEqual(128551, uts.name.stringref)
        self.assertEqual("3csounds", uts.resref)
        self.assertEqual(1, uts.active)
        self.assertEqual(1, uts.continuous)
        self.assertEqual(1, uts.looping)
        self.assertEqual(1, uts.positional)
        self.assertEqual(1, uts.random_position)
        self.assertEqual(1, uts.random_position)
        self.assertEqual(1.5, uts.elevation)
        self.assertEqual(8.0, uts.max_distance)
        self.assertEqual(5.0, uts.min_distance)
        self.assertEqual(0.10000000149011612, uts.random_range_x)
        self.assertEqual(0.20000000298023224, uts.random_range_y)
        self.assertEqual(4000, uts.interval)
        self.assertEqual(100, uts.interval_variation)
        self.assertEqual(0.10000000149011612, uts.pitch_variation)
        self.assertEqual(22, uts.priority)
        self.assertEqual(0, uts.hours)
        self.assertEqual(3, uts.times)
        self.assertEqual(120, uts.volume)
        self.assertEqual(7, uts.volume_variation)
        self.assertEqual(6, uts.palette_id)
        self.assertEqual("comment", uts.comment)

        self.assertEqual(4, len(uts.sounds))
        self.assertEqual("c_drdastro_atk2", uts.sounds[3])
