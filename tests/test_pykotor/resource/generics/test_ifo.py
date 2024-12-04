from __future__ import annotations

import os
import pathlib
import sys
import unittest
from unittest import TestCase

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

from pykotor.common.misc import Game
from pykotor.extract.installation import Installation
from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.ifo import construct_ifo, dismantle_ifo
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFF
    from pykotor.resource.generics.ifo import IFO

TEST_FILE = "tests/test_pykotor/test_files/test.ifo"
K1_PATH = os.environ.get("K1_PATH")
K2_PATH = os.environ.get("K2_PATH")


class TestIFO(TestCase):
    def setUp(self):
        self.log_messages: list[str] = [os.linesep]

    def log_func(self, message: str = ""):
        self.log_messages.append(message)

    @unittest.skipIf(
        not K1_PATH or not pathlib.Path(K1_PATH).joinpath("chitin.key").exists(),
        "K1_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k1_installation(self):
        self.installation = Installation(K1_PATH)  # type: ignore[arg-type]
        for ifo_resource in (resource for resource in self.installation if resource.restype() is ResourceType.IFO):
            gff: GFF = read_gff(ifo_resource.data())
            reconstructed_gff: GFF = dismantle_ifo(construct_ifo(gff), Game.K1)
            assert gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True), os.linesep.join(self.log_messages)

    @unittest.skipIf(
        not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
        "K2_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k2_installation(self):
        self.installation = Installation(K2_PATH)  # type: ignore[arg-type]
        for ifo_resource in (resource for resource in self.installation if resource.restype() is ResourceType.IFO):
            gff: GFF = read_gff(ifo_resource.data())
            reconstructed_gff: GFF = dismantle_ifo(construct_ifo(gff))
            assert gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True), os.linesep.join(self.log_messages)

    def test_gff_reconstruct(self):
        gff = read_gff(TEST_FILE)
        reconstructed_gff = dismantle_ifo(construct_ifo(gff))
        assert gff.compare(reconstructed_gff, self.log_func), os.linesep.join(self.log_messages)

    def test_io_construct(self):
        gff = read_gff(TEST_FILE)
        ifo = construct_ifo(gff)
        self.validate_io(ifo)

    def test_io_reconstruct(self):
        gff = read_gff(TEST_FILE)
        gff = dismantle_ifo(construct_ifo(gff))
        ifo = construct_ifo(gff)
        self.validate_io(ifo)

    def validate_io(self, ifo: IFO):
        assert ifo.mod_id == b"R:\xe5\x9e\xe3sq\x1d\x0f\xf0i\x9c\xb9a\x9f\xa7"
        assert ifo.creator_id == 2
        assert ifo.version == 3
        assert ifo.vo_id == "262"
        assert ifo.expansion_id == 0
        assert ifo.mod_name.stringref == 83947
        assert ifo.tag == "262TEL"
        assert ifo.hak == ""
        assert ifo.description.stringref == -1
        assert ifo.resref == "262tel"
        assert ifo.entry_position.x == 2.5811009407043457
        assert ifo.entry_position.y == 41.46979522705078
        assert ifo.entry_position.z == 21.372770309448242
        assert ifo.dawn_hour == 6
        assert ifo.dusk_hour == 18
        assert ifo.time_scale == 2
        assert ifo.start_month == 6
        assert ifo.start_day == 1
        assert ifo.start_hour == 13
        assert ifo.start_year == 1372
        assert ifo.xp_scale == 10
        assert ifo.on_heartbeat == "heartbeat"
        assert ifo.on_load == "load"
        assert ifo.on_start == "start"
        assert ifo.on_enter == "enter"
        assert ifo.on_leave == "leave"
        assert ifo.on_activate_item == "activate"
        assert ifo.on_acquire_item == "acquire"
        assert ifo.on_user_defined == "user"
        assert ifo.on_unacquire_item == "unacquire"
        assert ifo.on_player_death == "death"
        assert ifo.on_player_dying == "dying"
        assert ifo.on_player_levelup == "levelup"
        assert ifo.on_player_respawn == "spawn"
        assert ifo.on_player_rest == ""
        assert ifo.start_movie == ""
        self.assertAlmostEqual(-1.571, ifo.entry_direction, 3)


if __name__ == "__main__":
    unittest.main()
