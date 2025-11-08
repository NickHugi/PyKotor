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
from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.ifo import construct_ifo, dismantle_ifo

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFF
    from pykotor.resource.generics.ifo import IFO

TEST_IFO_XML = """<gff3>
  <struct id="-1">
    <data label="Mod_ID">UjrlnuNzcR0P8GmcuWGfpw==</data>
    <sint32 label="Mod_Creator_ID">2</sint32>
    <uint32 label="Mod_Version">3</uint32>
    <exostring label="Mod_VO_ID">262</exostring>
    <uint16 label="Expansion_Pack">0</uint16>
    <locstring label="Mod_Name" strref="83947" />
    <exostring label="Mod_Tag">262TEL</exostring>
    <exostring label="Mod_Hak" />
    <locstring label="Mod_Description" strref="-1" />
    <byte label="Mod_IsSaveGame">0</byte>
    <resref label="Mod_Entry_Area">262tel</resref>
    <float label="Mod_Entry_X">2.5811009407043457</float>
    <float label="Mod_Entry_Y">41.46979522705078</float>
    <float label="Mod_Entry_Z">21.372770309448242</float>
    <float label="Mod_Entry_Dir_X">1.5099580252808664e-07</float>
    <float label="Mod_Entry_Dir_Y">-1.0</float>
    <list label="Mod_Expan_List" />
    <byte label="Mod_DawnHour">6</byte>
    <byte label="Mod_DuskHour">18</byte>
    <byte label="Mod_MinPerHour">2</byte>
    <byte label="Mod_StartMonth">6</byte>
    <byte label="Mod_StartDay">1</byte>
    <byte label="Mod_StartHour">13</byte>
    <uint32 label="Mod_StartYear">1372</uint32>
    <byte label="Mod_XPScale">10</byte>
    <resref label="Mod_OnHeartbeat">heartbeat</resref>
    <resref label="Mod_OnModLoad">load</resref>
    <resref label="Mod_OnModStart">start</resref>
    <resref label="Mod_OnClientEntr">enter</resref>
    <resref label="Mod_OnClientLeav">leave</resref>
    <resref label="Mod_OnActvtItem">activate</resref>
    <resref label="Mod_OnAcquirItem">acquire</resref>
    <resref label="Mod_OnUsrDefined">user</resref>
    <resref label="Mod_OnUnAqreItem">unacquire</resref>
    <resref label="Mod_OnPlrDeath">death</resref>
    <resref label="Mod_OnPlrDying">dying</resref>
    <resref label="Mod_OnPlrLvlUp">levelup</resref>
    <resref label="Mod_OnSpawnBtnDn">spawn</resref>
    <resref label="Mod_OnPlrRest" />
    <resref label="Mod_StartMovie" />
    <list label="Mod_CutSceneList" />
    <list label="Mod_GVar_List" />
    <list label="Mod_Area_list">
      <struct id="6">
        <resref label="Area_Name">262tel</resref>
        </struct>
      </list>
    </struct>
  </gff3>
"""
class TestIFO(TestCase):
    def setUp(self):
        self.log_messages = [os.linesep]

    def log_func(self, message=""):
        self.log_messages.append(message)

    def test_gff_reconstruct(self):
        gff = read_gff(TEST_IFO_XML.encode())
        reconstructed_gff = dismantle_ifo(construct_ifo(gff))
        self.assertTrue(gff.compare(reconstructed_gff, self.log_func), os.linesep.join(self.log_messages))

    def test_io_construct(self):
        gff = read_gff(TEST_IFO_XML.encode())
        ifo = construct_ifo(gff)
        self.validate_io(ifo)

    def test_io_reconstruct(self):
        gff = read_gff(TEST_IFO_XML.encode())
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
