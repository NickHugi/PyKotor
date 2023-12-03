from __future__ import annotations

import pathlib
import sys
import unittest

THIS_SCRIPT_PATH = pathlib.Path(__file__)
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[3].resolve()
UTILITY_PATH = THIS_SCRIPT_PATH.parents[5].joinpath("Utility", "src").resolve()
if PYKOTOR_PATH.exists():
    working_dir = str(PYKOTOR_PATH)
    if working_dir in sys.path:
        sys.path.remove(working_dir)
    sys.path.insert(0, working_dir)
if UTILITY_PATH.exists():
    working_dir = str(UTILITY_PATH)
    if working_dir in sys.path:
        sys.path.remove(working_dir)
    sys.path.insert(0, working_dir)

from pykotor.resource.formats.gff import GFF, read_gff
from pykotor.resource.generics.jrl import JRL, JRLEntry, construct_jrl, dismantle_jrl

TEST_FILE = "src/tests/files/test.jrl"


class TestJRL(unittest.TestCase):
    def test_io(self) -> None:
        gff = read_gff(TEST_FILE)
        jrl = construct_jrl(gff)
        self.validate_io(jrl)

        gff: GFF = dismantle_jrl(jrl)
        jrl: JRL = construct_jrl(gff)
        self.validate_io(jrl)

    def validate_io(self, jrl: JRL):
        quest = jrl.quests[0]
        self.assertEqual(
            "Plot to be considered worthy to hear the Sand People history.",
            quest.comment,
        )
        self.assertEqual(33089, quest.name.stringref)
        self.assertEqual(4, quest.planet_id)
        self.assertEqual(72, quest.plot_index)
        self.assertEqual(1, quest.priority)
        self.assertEqual("Tat20aa_worthy", quest.tag)

        entry1: JRLEntry = quest.entries[0]
        self.assertFalse(entry1.end)
        self._assert_group(10, entry1, 33090, 5.0, 1)
        entry2: JRLEntry = quest.entries[1]
        self.assertTrue(entry2.end)
        self._assert_group(20, entry2, 33091, 6.0, 1)

    def _assert_group(self, expected_entry_id: int, jrl: JRLEntry, expected_stringref: int, expected_xp, decimal_places: int):
        self.assertEqual(expected_entry_id, jrl.entry_id)
        self.assertEqual(expected_stringref, jrl.text.stringref)
        self.assertAlmostEqual(expected_xp, jrl.xp_percentage, decimal_places)


if __name__ == "__main__":
    unittest.main()
