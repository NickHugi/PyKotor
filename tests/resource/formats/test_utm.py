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
    os.chdir(PYKOTOR_PATH.parent)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from typing import TYPE_CHECKING

from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.utm import construct_utm, dismantle_utm

if TYPE_CHECKING:
    from pykotor.resource.generics.utm import UTM

TEST_FILE = "tests/files/test.utm"


class TestUTM(unittest.TestCase):
    def test_io(self):
        gff = read_gff(TEST_FILE)
        utm = construct_utm(gff)
        self.validate_io(utm)

        gff = dismantle_utm(utm)
        utm = construct_utm(gff)
        self.validate_io(utm)

    def validate_io(self, utm: UTM):
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
