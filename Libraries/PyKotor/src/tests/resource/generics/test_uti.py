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
from pykotor.resource.generics.uti import UTI, construct_uti, dismantle_uti

TEST_FILE = "src/tests/files/test.uti"


class TestUTI(TestCase):
    def setUp(self):
        self.log_messages = [os.linesep]

    def log_func(self, message=""):
        self.log_messages.append(message)

    def test_gff_reconstruct(self) -> None:
        gff = read_gff(TEST_FILE)
        reconstructed_gff = dismantle_uti(construct_uti(gff))
        self.assertTrue(gff.compare(reconstructed_gff, self.log_func), os.linesep.join(self.log_messages))

    def test_io_construct(self):
        gff = read_gff(TEST_FILE)
        uti = construct_uti(gff)
        self.validate_io(uti)

    def test_io_reconstruct(self):
        gff = read_gff(TEST_FILE)
        gff = dismantle_uti(construct_uti(gff))
        uti = construct_uti(gff)
        self.validate_io(uti)

    def validate_io(self, uti: UTI):
        self.assertEqual("g_a_class4001", uti.resref)
        self.assertEqual(38, uti.base_item)
        self.assertEqual(5632, uti.name.stringref)
        self.assertEqual(5633, uti.description.stringref)
        self.assertEqual("G_A_CLASS4001", uti.tag)
        self.assertEqual(13, uti.charges)
        self.assertEqual(50, uti.cost)
        self.assertEqual(1, uti.stolen)
        self.assertEqual(1, uti.stack_size)
        self.assertEqual(1, uti.plot)
        self.assertEqual(50, uti.add_cost)
        self.assertEqual(1, uti.texture_variation)
        self.assertEqual(2, uti.model_variation)
        self.assertEqual(3, uti.body_variation)
        self.assertEqual(1, uti.texture_variation)
        self.assertEqual(1, uti.palette_id)
        self.assertEqual("itemo", uti.comment)

        self.assertEqual(2, len(uti.properties))
        self.assertIsNone(uti.properties[0].upgrade_type, None)
        self.assertEqual(100, uti.properties[1].chance_appear)
        self.assertEqual(1, uti.properties[1].cost_table)
        self.assertEqual(1, uti.properties[1].cost_value)
        self.assertEqual(255, uti.properties[1].param1)
        self.assertEqual(1, uti.properties[1].param1_value)
        self.assertEqual(45, uti.properties[1].property_name)
        self.assertEqual(6, uti.properties[1].subtype)
        self.assertEqual(24, uti.properties[1].upgrade_type)


if __name__ == "__main__":
    unittest.main()
