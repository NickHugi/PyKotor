from __future__ import annotations

import os
import pathlib
import sys
import unittest
from unittest import TestCase

from pykotor.resource.type import ResourceType

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
from pykotor.resource.generics.ute import construct_ute, dismantle_ute

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFF
    from pykotor.resource.generics.ute import UTE

TEST_FILE = "tests/test_pykotor/test_files/test.ute"
K1_PATH = os.environ.get("K1_PATH")
K2_PATH = os.environ.get("K2_PATH")


class TestUTE(TestCase):
    def setUp(self):
        self.log_messages = [os.linesep]

    def log_func(self, *msgs):
        self.log_messages.append("\t".join(msgs))

    @unittest.skipIf(
        not K1_PATH or not pathlib.Path(K1_PATH).joinpath("chitin.key").exists(),
        "K1_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k1_installation(self):
        self.installation = Installation(K1_PATH)  # type: ignore[arg-type]
        for ute_resource in (resource for resource in self.installation if resource.restype() is ResourceType.UTE):
            gff: GFF = read_gff(ute_resource.data())
            reconstructed_gff: GFF = dismantle_ute(construct_ute(gff), Game.K1)
            assert gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True), os.linesep.join(self.log_messages)

    @unittest.skipIf(
        not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
        "K2_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k2_installation(self):
        self.installation = Installation(K2_PATH)  # type: ignore[arg-type]
        for ute_resource in (resource for resource in self.installation if resource.restype() is ResourceType.UTE):
            gff: GFF = read_gff(ute_resource.data())
            reconstructed_gff: GFF = dismantle_ute(construct_ute(gff))
            assert gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True), os.linesep.join(self.log_messages)

    def test_k2_reconstruct(self):
        gff = read_gff(TEST_FILE)
        reconstructed_gff = dismantle_ute(construct_ute(gff), Game.K2)
        result = gff.compare(reconstructed_gff, self.log_func)
        output = os.linesep.join(self.log_messages)
        if not result:
            expected_output = r"""
GFFStruct: number of fields have changed at 'GFFRoot\CreatureList\0': '4' --> '5'
Extra 'Int32' field found at 'GFFRoot\CreatureList\0\GuaranteedCount': '0'
""".replace("\r\n", "\n")
            assert output.strip().replace("\r\n", "\n") == expected_output.strip(), "Comparison output does not match expected output"
        else:
            assert result

    def test_io_construct(self):
        gff = read_gff(TEST_FILE)
        ute = construct_ute(gff)
        self.validate_io(ute)

    def test_io_reconstruct(self):
        gff = read_gff(TEST_FILE)
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
