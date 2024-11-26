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

TEST_FILE = "tests/test_pykotor/test_files/test.utm"


class TestUTM(unittest.TestCase):
    def test_io(self):
        gff = read_gff(TEST_FILE)
        utm = construct_utm(gff)
        self.validate_io(utm)

        gff = dismantle_utm(utm)
        utm = construct_utm(gff)
        self.validate_io(utm)

    def validate_io(self, utm: UTM):
        assert utm.resref == "dan_droid"
        assert utm.name.stringref == 33399
        assert utm.tag == "dan_droid"
        assert utm.mark_up == 100
        assert utm.mark_down == 25
        assert utm.on_open == "onopenstore"
        assert utm.comment == "comment"
        assert utm.id == 5
        assert utm.can_buy
        assert utm.can_sell

        assert len(utm.inventory) == 2
        assert not utm.inventory[0].infinite
        assert utm.inventory[1].infinite
        assert utm.inventory[1].resref == "g_i_drdltplat002"


if __name__ == "__main__":
    unittest.main()
