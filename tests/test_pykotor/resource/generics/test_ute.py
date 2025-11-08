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

from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.ute import construct_ute, dismantle_ute
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFF
    from pykotor.resource.generics.ute import UTE

TEST_UTE_XML = """<gff3>
  <struct id="-1">
    <exostring label="Tag">G_KATAARNGROUP01</exostring>
    <locstring label="LocalizedName" strref="31918" />
    <resref label="TemplateResRef">g_kataarngroup01</resref>
    <byte label="Active">1</byte>
    <sint32 label="Difficulty">1</sint32>
    <sint32 label="DifficultyIndex">2</sint32>
    <uint32 label="Faction">1</uint32>
    <sint32 label="MaxCreatures">6</sint32>
    <byte label="PlayerOnly">1</byte>
    <sint32 label="RecCreatures">3</sint32>
    <byte label="Reset">1</byte>
    <sint32 label="ResetTime">60</sint32>
    <sint32 label="Respawns">1</sint32>
    <sint32 label="SpawnOption">1</sint32>
    <resref label="OnEntered">onentered</resref>
    <resref label="OnExit">onexit</resref>
    <resref label="OnExhausted">onexhausted</resref>
    <resref label="OnHeartbeat">onheartbeat</resref>
    <resref label="OnUserDefined">onuserdefined</resref>
    <list label="CreatureList">
      <struct id="0">
        <sint32 label="Appearance">74</sint32>
        <float label="CR">4.0</float>
        <resref label="ResRef">g_kataarn01</resref>
        <byte label="SingleSpawn">1</byte>
        </struct>
      <struct id="0">
        <sint32 label="Appearance">74</sint32>
        <float label="CR">8.0</float>
        <resref label="ResRef">g_kataarn02</resref>
        <byte label="SingleSpawn">1</byte>
        <sint32 label="GuaranteedCount">1</sint32>
        </struct>
      </list>
    <byte label="PaletteID">7</byte>
    <exostring label="Comment">Kashyyyk</exostring>
    </struct>
  </gff3>
"""


class TestUTE(TestCase):
    def setUp(self):
        self.log_messages = [os.linesep]

    def log_func(self, *msgs):
        self.log_messages.append("\t".join(msgs))

    def test_gff_reconstruct(self):
        gff = read_gff(TEST_UTE_XML.encode(), file_format=ResourceType.GFF_XML)
        reconstructed_gff = dismantle_ute(construct_ute(gff))
        assert gff.compare(reconstructed_gff, self.log_func), os.linesep.join(self.log_messages)

    def test_io_construct(self):
        gff = read_gff(TEST_UTE_XML.encode(), file_format=ResourceType.GFF_XML)
        ute = construct_ute(gff)
        self.validate_io(ute)

    def test_io_reconstruct(self):
        gff = read_gff(TEST_UTE_XML.encode(), file_format=ResourceType.GFF_XML)
        gff = dismantle_ute(construct_ute(gff))
        ute = construct_ute(gff)
        self.validate_io(ute)

    def validate_io(self, ute: UTE):
        assert ute.tag == "G_KATAARNGROUP01"
        assert ute.name.stringref == 31918
        assert ute.resref == "g_kataarngroup01"
        assert ute.active == 1
        assert ute.unused_difficulty == 1
        assert ute.difficulty_id == 2
        assert ute.faction_id == 1
        assert ute.max_creatures == 6
        assert ute.player_only == 1
        assert ute.rec_creatures == 3
        assert ute.reset == 1
        assert ute.reset_time == 60
        assert ute.respawns == 1
        assert ute.single_shot == 1
        assert ute.on_entered == "onentered"
        assert ute.on_exit == "onexit"
        assert ute.on_exhausted == "onexhausted"
        assert ute.on_heartbeat == "onheartbeat"
        assert ute.on_user_defined == "onuserdefined"
        assert ute.palette_id == 7
        assert ute.comment == "Kashyyyk"

        assert len(ute.creatures) == 2
        assert ute.creatures[1].appearance_id == 74
        assert ute.creatures[1].challenge_rating == 8.0
        assert ute.creatures[1].resref == "g_kataarn02"
        assert ute.creatures[1].guaranteed_count == 1
        assert ute.creatures[1].single_spawn


if __name__ == "__main__":
    unittest.main()
