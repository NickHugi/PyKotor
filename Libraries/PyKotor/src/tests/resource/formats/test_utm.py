import pathlib
import sys
import unittest

if getattr(sys, "frozen", False) is False:
    pykotor_path = pathlib.Path(__file__).parents[3] / "pykotor"
    if pykotor_path.joinpath("__init__.py").exists():
        working_dir = str(pykotor_path.parent)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.insert(0, str(pykotor_path.parent))

from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.utm import construct_utm, dismantle_utm

TEST_FILE = "src/tests/files/test.utm"


class TestUTM(unittest.TestCase):
    def test_io(self):
        gff = read_gff(TEST_FILE)
        utm = construct_utm(gff)
        self.validate_io(utm)

        gff = dismantle_utm(utm)
        utm = construct_utm(gff)
        self.validate_io(utm)

    def validate_io(self, utm):
        self.assertEqual("dan_droid", utm.resref)
        self.assertEqual(33399, utm.name.stringref)
        self.assertEqual("dan_droid", utm.tag)
        self.assertEqual(100, utm.mark_up)
        self.assertEqual(25, utm.mark_down)
        self.assertEqual("onopenstore", utm.on_open)
        self.assertEqual("comment", utm.comment)
        self.assertEqual(5, utm.id)
        self.assertTrue(utm.can_buy)
        self.assertTrue(utm.can_sell)

        self.assertEqual(2, len(utm.inventory))
        self.assertFalse(utm.inventory[0].infinite)
        self.assertTrue(utm.inventory[1].infinite)
        self.assertEqual("g_i_drdltplat002", utm.inventory[1].resref)


if __name__ == "__main__":
    unittest.main()
