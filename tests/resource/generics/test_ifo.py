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

TEST_FILE = "tests/files/test.ifo"
K1_PATH = os.environ.get("K1_PATH")
K2_PATH = os.environ.get("K2_PATH")


class TestIFO(TestCase):
    def setUp(self):
        self.log_messages = [os.linesep]

    def log_func(self, message=""):
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
            self.assertTrue(gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True), os.linesep.join(self.log_messages))

    @unittest.skipIf(
        not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
        "K2_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k2_installation(self):
        self.installation = Installation(K2_PATH)  # type: ignore[arg-type]
        for ifo_resource in (resource for resource in self.installation if resource.restype() is ResourceType.IFO):
            gff: GFF = read_gff(ifo_resource.data())
            reconstructed_gff: GFF = dismantle_ifo(construct_ifo(gff))
            self.assertTrue(gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True), os.linesep.join(self.log_messages))

    def test_gff_reconstruct(self):
        gff = read_gff(TEST_FILE)
        reconstructed_gff = dismantle_ifo(construct_ifo(gff))
        self.assertTrue(gff.compare(reconstructed_gff, self.log_func), os.linesep.join(self.log_messages))

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
        self.assertEqual(b"R:\xe5\x9e\xe3sq\x1d\x0f\xf0i\x9c\xb9a\x9f\xa7", ifo.mod_id)
        self.assertEqual(2, ifo.creator_id)
        self.assertEqual(3, ifo.version)
        self.assertEqual("262", ifo.vo_id)
        self.assertEqual(0, ifo.expansion_id)
        self.assertEqual(83947, ifo.mod_name.stringref)
        self.assertEqual("262TEL", ifo.tag)
        self.assertEqual("", ifo.hak)
        self.assertEqual(-1, ifo.description.stringref)
        self.assertEqual("262tel", ifo.resref)
        self.assertEqual(2.5811009407043457, ifo.entry_position.x)
        self.assertEqual(41.46979522705078, ifo.entry_position.y)
        self.assertEqual(21.372770309448242, ifo.entry_position.z)
        self.assertEqual(6, ifo.dawn_hour)
        self.assertEqual(18, ifo.dusk_hour)
        self.assertEqual(2, ifo.time_scale)
        self.assertEqual(6, ifo.start_month)
        self.assertEqual(1, ifo.start_day)
        self.assertEqual(13, ifo.start_hour)
        self.assertEqual(1372, ifo.start_year)
        self.assertEqual(10, ifo.xp_scale)
        self.assertEqual("heartbeat", ifo.on_heartbeat)
        self.assertEqual("load", ifo.on_load)
        self.assertEqual("start", ifo.on_start)
        self.assertEqual("enter", ifo.on_enter)
        self.assertEqual("leave", ifo.on_leave)
        self.assertEqual("activate", ifo.on_activate_item)
        self.assertEqual("acquire", ifo.on_acquire_item)
        self.assertEqual("user", ifo.on_user_defined)
        self.assertEqual("unacquire", ifo.on_unacquire_item)
        self.assertEqual("death", ifo.on_player_death)
        self.assertEqual("dying", ifo.on_player_dying)
        self.assertEqual("levelup", ifo.on_player_levelup)
        self.assertEqual("spawn", ifo.on_player_respawn)
        self.assertEqual("", ifo.on_player_rest)
        self.assertEqual("", ifo.start_movie)
        self.assertAlmostEqual(-1.571, ifo.entry_direction, 3)


if __name__ == "__main__":
    unittest.main()
