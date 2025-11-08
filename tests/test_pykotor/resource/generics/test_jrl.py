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
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from typing import TYPE_CHECKING

from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.jrl import construct_jrl, dismantle_jrl

if TYPE_CHECKING:
    from pykotor.resource.formats.gff import GFF
    from pykotor.resource.generics.jrl import JRL, JRLEntry, JRLQuest

TEST_JRL_XML = """<gff3>
  <struct id="-1">
    <list label="Categories">
      <struct id="0">
        <locstring label="Name" strref="33089" />
        <uint32 label="Priority">1</uint32>
        <exostring label="Comment">Plot to be considered worthy to hear the Sand People history.</exostring>
        <exostring label="Tag">Tat20aa_worthy</exostring>
        <sint32 label="PlotIndex">72</sint32>
        <sint32 label="PlanetID">4</sint32>
        <list label="EntryList">
          <struct id="0">
            <uint32 label="ID">10</uint32>
            <uint16 label="End">0</uint16>
            <locstring label="Text" strref="33090" />
            <float label="XP_Percentage">5.0</float>
            </struct>
          <struct id="1">
            <uint32 label="ID">20</uint32>
            <uint16 label="End">1</uint16>
            <locstring label="Text" strref="33091" />
            <float label="XP_Percentage">6.0</float>
            </struct>
          </list>
        </struct>
      </list>
    </struct>
  </gff3>
"""
class TestJRL(unittest.TestCase):
    def setUp(self):
        self.log_messages: list[str] = [os.linesep]

    def log_func(self, message=""):
        self.log_messages.append(message)

    def test_gff_reconstruct(self):
        gff = read_gff(TEST_JRL_XML.encode())
        reconstructed_gff = dismantle_jrl(construct_jrl(gff))
        assert gff.compare(reconstructed_gff, self.log_func), os.linesep.join(self.log_messages)

    def test_io_construct(self):
        gff = read_gff(TEST_JRL_XML.encode())
        jrl = construct_jrl(gff)
        self.validate_io(jrl)

    def test_io_reconstruct(self):
        gff = read_gff(TEST_JRL_XML.encode())
        gff = dismantle_jrl(construct_jrl(gff))
        jrl: JRL = construct_jrl(gff)
        self.validate_io(jrl)

    def validate_io(self, jrl: JRL):
        quest: JRLQuest = jrl.quests[0]
        assert quest.comment == "Plot to be considered worthy to hear the Sand People history."
        assert quest.name.stringref == 33089
        assert quest.planet_id == 4
        assert quest.plot_index == 72
        assert quest.priority == 1
        assert quest.tag == "Tat20aa_worthy"

        entry1: JRLEntry = quest.entries[0]
        assert not entry1.end
        self._assert_group(10, entry1, 33090, 5.0, 1)
        entry2: JRLEntry = quest.entries[1]
        assert entry2.end
        self._assert_group(20, entry2, 33091, 6.0, 1)

    def _assert_group(
        self,
        expected_entry_id: int,
        jrl: JRLEntry,
        expected_stringref: int,
        expected_xp: float,
        decimal_places: int,
    ):
        assert expected_entry_id == jrl.entry_id
        assert expected_stringref == jrl.text.stringref
        self.assertAlmostEqual(expected_xp, jrl.xp_percentage, decimal_places)


if __name__ == "__main__":
    unittest.main()
