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

from pykotor.common.misc import Game
from pykotor.extract.installation import Installation
from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.jrl import construct_jrl, dismantle_jrl
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.gff import GFF
    from pykotor.resource.generics.jrl import JRL, JRLEntry

TEST_FILE = "tests/files/test.jrl"
K1_PATH = os.environ.get("K1_PATH")
K2_PATH = os.environ.get("K2_PATH")


class TestJRL(unittest.TestCase):
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
        for jrl_resource in (resource for resource in self.installation if resource.restype() is ResourceType.JRL):
            gff: GFF = read_gff(jrl_resource.data())
            reconstructed_gff: GFF = dismantle_jrl(construct_jrl(gff), Game.K1)
            self.assertTrue(gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True), os.linesep.join(self.log_messages))

    @unittest.skipIf(
        not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
        "K2_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k2_installation(self):
        self.installation = Installation(K2_PATH)  # type: ignore[arg-type]
        for jrl_resource in (resource for resource in self.installation if resource.restype() is ResourceType.JRL):
            gff: GFF = read_gff(jrl_resource.data())
            reconstructed_gff: GFF = dismantle_jrl(construct_jrl(gff))
            self.assertTrue(gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True), os.linesep.join(self.log_messages))

    def test_gff_reconstruct(self):
        gff = read_gff(TEST_FILE)
        reconstructed_gff = dismantle_jrl(construct_jrl(gff))
        self.assertTrue(gff.compare(reconstructed_gff, self.log_func), os.linesep.join(self.log_messages))

    def test_io_construct(self):
        gff = read_gff(TEST_FILE)
        jrl = construct_jrl(gff)
        self.validate_io(jrl)

    def test_io_reconstruct(self):
        gff = read_gff(TEST_FILE)
        gff = dismantle_jrl(construct_jrl(gff))
        jrl = construct_jrl(gff)
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
