import pathlib
import sys
import unittest
from unittest import TestCase

if getattr(sys, "frozen", False) is False:
    pykotor_path = pathlib.Path(__file__).parents[3] / "pykotor"
    if pykotor_path.exists() and str(pykotor_path) not in sys.path:
        sys.path.insert(0, str(pykotor_path.parent))

from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.ifo import construct_ifo, dismantle_ifo

TEST_FILE = "tests/files/test.ifo"


class TestIFO(TestCase):
    def test_io(self):
        gff = read_gff(TEST_FILE)
        ifo = construct_ifo(gff)
        self.validate_io(ifo)

        gff = dismantle_ifo(ifo)
        ifo = construct_ifo(gff)
        self.validate_io(ifo)

    def validate_io(self, ifo):
        self.assertEqual(b"R:\xe5\x9e\xe3sq\x1d\x0f\xf0i\x9c\xb9a\x9f\xa7", ifo.mod_id)
        self.assertEqual(2, ifo.creator_id)
        self.assertEqual(3, ifo.version)
        self.assertEqual("262", ifo.vo_id)
        self.assertEqual(0, ifo.expansion_id)
        self.assertEqual(83947, ifo.mod_name.stringref)
        self.assertEqual("262TEL", ifo.tag)
        self.assertEqual("", ifo.hak)
        self.assertEqual(-1, ifo.description.stringref)
        self.assertEqual("262tel", ifo.identifier)
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
