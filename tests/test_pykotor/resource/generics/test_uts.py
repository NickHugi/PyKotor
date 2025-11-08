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
from pykotor.resource.generics.uts import construct_uts, dismantle_uts
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFF
    from pykotor.resource.generics.uts import UTS

TEST_UTS_XML = """<gff3>
  <struct id="-1">
    <exostring label="Tag">3Csounds</exostring>
    <locstring label="LocName" strref="128551" />
    <resref label="TemplateResRef">3csounds</resref>
    <byte label="Active">1</byte>
    <byte label="Continuous">1</byte>
    <byte label="Looping">1</byte>
    <byte label="Positional">1</byte>
    <byte label="RandomPosition">1</byte>
    <byte label="Random">1</byte>
    <float label="Elevation">1.5</float>
    <float label="MaxDistance">8.0</float>
    <float label="MinDistance">5.0</float>
    <float label="RandomRangeX">0.10000000149011612</float>
    <float label="RandomRangeY">0.20000000298023224</float>
    <uint32 label="Interval">4000</uint32>
    <uint32 label="IntervalVrtn">100</uint32>
    <float label="PitchVariation">0.10000000149011612</float>
    <byte label="Priority">22</byte>
    <uint32 label="Hours">0</uint32>
    <byte label="Times">3</byte>
    <byte label="Volume">120</byte>
    <byte label="VolumeVrtn">7</byte>
    <list label="Sounds">
      <struct id="0">
        <resref label="Sound">c_drdastro_dead</resref>
        </struct>
      <struct id="0">
        <resref label="Sound">c_drdastro_atk1</resref>
        </struct>
      <struct id="0">
        <resref label="Sound">p_t3-m4_dead</resref>
        </struct>
      <struct id="0">
        <resref label="Sound">c_drdastro_atk2</resref>
        </struct>
      </list>
    <byte label="PaletteID">6</byte>
    <exostring label="Comment">comment</exostring>
    </struct>
  </gff3>
"""

TEST_K1_UTS_XML = """<gff3>
  <struct id="-1">
    <exostring label="Tag">computersoundsrnd</exostring>
    <locstring label="LocName" strref="45774" />
    <resref label="TemplateResRef">computersoundsrn</resref>
    <byte label="Active">1</byte>
    <byte label="Continuous">1</byte>
    <byte label="Looping">0</byte>
    <byte label="Positional">1</byte>
    <byte label="RandomPosition">0</byte>
    <byte label="Random">1</byte>
    <float label="Elevation">1.5</float>
    <float label="MaxDistance">10.0</float>
    <float label="MinDistance">3.0</float>
    <float label="RandomRangeX">0.0</float>
    <float label="RandomRangeY">0.0</float>
    <uint32 label="Interval">7000</uint32>
    <uint32 label="IntervalVrtn">4000</uint32>
    <float label="PitchVariation">0.10000000149011612</float>
    <byte label="Priority">22</byte>
    <uint32 label="Hours">0</uint32>
    <byte label="Times">3</byte>
    <byte label="Volume">70</byte>
    <byte label="VolumeVrtn">0</byte>
    <list label="Sounds">
      <struct id="0">
        <resref label="Sound">as_el_compsnd_01</resref>
        </struct>
      <struct id="0">
        <resref label="Sound">as_el_compsnd_03</resref>
        </struct>
      <struct id="0">
        <resref label="Sound">as_el_compsnd_04</resref>
        </struct>
      </list>
    <byte label="PaletteID">6</byte>
    <exostring label="Comment" />
    </struct>
  </gff3>
"""


class TestUTS(TestCase):
    def setUp(self):
        self.log_messages = [os.linesep]

    def log_func(self, *msgs):
        self.log_messages.append("\t".join(msgs))

    def test_gff_reconstruct(self):
        gff = read_gff(TEST_UTS_XML.encode(), file_format=ResourceType.GFF_XML)
        reconstructed_gff = dismantle_uts(construct_uts(gff))
        assert gff.compare(reconstructed_gff, self.log_func), os.linesep.join(self.log_messages)

    def test_k1_gff_reconstruct(self):
        gff = read_gff(TEST_K1_UTS_XML.encode(), file_format=ResourceType.GFF_XML)
        reconstructed_gff = dismantle_uts(construct_uts(gff), Game.K1)
        assert gff.compare(reconstructed_gff, self.log_func), os.linesep.join(self.log_messages)

    def test_io_construct(self):
        gff = read_gff(TEST_UTS_XML.encode(), file_format=ResourceType.GFF_XML)
        uts = construct_uts(gff)
        self.validate_io(uts)

    def test_io_reconstruct(self):
        gff = read_gff(TEST_UTS_XML.encode(), file_format=ResourceType.GFF_XML)
        gff = dismantle_uts(construct_uts(gff))
        uts = construct_uts(gff)
        self.validate_io(uts)

    def validate_io(self, uts: UTS):
        assert uts.tag == "3Csounds"
        assert uts.name.stringref == 128551
        assert uts.resref == "3csounds"
        assert uts.active == 1
        assert uts.continuous == 1
        assert uts.looping == 1
        assert uts.positional == 1
        assert uts.random_position == 1
        assert uts.random_position == 1
        assert uts.elevation == 1.5
        assert uts.max_distance == 8.0
        assert uts.min_distance == 5.0
        assert uts.random_range_x == 0.10000000149011612
        assert uts.random_range_y == 0.20000000298023224
        assert uts.interval == 4000
        assert uts.interval_variation == 100
        assert uts.pitch_variation == 0.10000000149011612
        assert uts.priority == 22
        assert uts.hours == 0
        assert uts.times == 3
        assert uts.volume == 120
        assert uts.volume_variation == 7
        assert uts.palette_id == 6
        assert uts.comment == "comment"

        assert len(uts.sounds) == 4
        assert uts.sounds[3] == "c_drdastro_atk2"
