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

from pykotor.common.language import LocalizedString
from pykotor.common.misc import ResRef
from pykotor.resource.generics.utm import UTM, InventoryItem

TEST_UTM_OBJECT = UTM(
    resref=ResRef("dan_droid"),
    name=LocalizedString(stringref=33399),
    tag="dan_droid",
    mark_up=100,
    mark_down=25,
    on_open=ResRef("onopenstore"),
    can_buy=True,
    can_sell=True,
    inventory=[
        InventoryItem(resref=ResRef("g_i_drdltplat001"), infinite=False),
        InventoryItem(resref=ResRef("g_i_drdltplat002"), infinite=True),
    ],
    id=5,
    comment="comment"
)


class TestUTM(unittest.TestCase):
    def test_io(self):
        gff = dismantle_utm(TEST_UTM_OBJECT)
        utm = construct_utm(gff)
        self.validate_io(utm)

        gff = dismantle_utm(utm)
        utm = construct_utm(gff)
        self.validate_io(utm)

    def validate_io(self, utm: UTM):
        assert utm.resref == ResRef("dan_droid"), f"Expected ResRef('dan_droid'), got '{utm.resref}'"
        assert utm.name.stringref == 33399, f"Expected stringref 33399, got '{utm.name.stringref}'"
        assert utm.tag == "dan_droid", f"Expected 'dan_droid', got '{utm.tag}'"
        assert utm.mark_up == 100, f"Expected 100, got '{utm.mark_up}'"
        assert utm.mark_down == 25, f"Expected 25, got '{utm.mark_down}'"
        assert utm.on_open == ResRef("onopenstore"), f"Expected ResRef('onopenstore'), got '{utm.on_open}'"
        assert utm.comment == "comment", f"Expected 'comment', got '{utm.comment}'"
        assert utm.id == 5, f"Expected 5, got '{utm.id}'"
        assert utm.can_buy, f"Expected True, got '{utm.can_buy}'"
        assert utm.can_sell, f"Expected True, got '{utm.can_sell}'"

        assert len(utm.inventory) == 2, f"Expected 2, got {len(utm.inventory)}"
        assert not utm.inventory[0].infinite, f"Expected False, got '{utm.inventory[0].infinite}'"
        assert utm.inventory[1].infinite, f"Expected True, got '{utm.inventory[1].infinite}'"
        assert utm.inventory[1].resref == ResRef("g_i_drdltplat002"), f"Expected ResRef('g_i_drdltplat002'), got '{utm.inventory[1].resref}'"


if __name__ == "__main__":
    unittest.main()
