from __future__ import annotations

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

from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.utm import construct_utm, dismantle_utm

if TYPE_CHECKING:
    from pykotor.resource.generics.utm import UTM

TEST_UTM_XML = """<gff3>
  <struct id="-1">
    <resref label="ResRef">dan_droid</resref>
    <locstring label="LocName" strref="33399" />
    <exostring label="Tag">dan_droid</exostring>
    <sint32 label="MarkUp">100</sint32>
    <sint32 label="MarkDown">25</sint32>
    <resref label="OnOpenStore">onopenstore</resref>
    <byte label="BuySellFlag">3</byte>
    <list label="ItemList">
      <struct id="0">
        <resref label="InventoryRes">g_i_drdltplat001</resref>
        <uint16 label="Repos_PosX">0</uint16>
        <uint16 label="Repos_Posy">0</uint16>
        </struct>
      <struct id="1">
        <resref label="InventoryRes">g_i_drdltplat002</resref>
        <uint16 label="Repos_PosX">1</uint16>
        <uint16 label="Repos_Posy">0</uint16>
        <byte label="Infinite">1</byte>
        </struct>
      </list>
    <byte label="ID">5</byte>
    <exostring label="Comment">comment</exostring>
    </struct>
  </gff3>
"""


class TestUTM(unittest.TestCase):
    def test_io(self):
        gff = read_gff(TEST_UTM_XML.encode())
        gff = read_gff(TEST_UTM_XML.encode())
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
