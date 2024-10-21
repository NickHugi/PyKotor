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
from pykotor.resource.generics.uts import construct_uts, dismantle_uts

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFF
    from pykotor.resource.generics.uts import UTS

TEST_FILE = "tests/test_files/test.uts"
TEST_K1_FILE = "tests/test_files/test_k1.uts"

K1_PATH = os.environ.get("K1_PATH")
K2_PATH = os.environ.get("K2_PATH")


class TestUTS(TestCase):
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
        for are_resource in (resource for resource in self.installation if resource.restype() is ResourceType.UTS):
            gff: GFF = read_gff(are_resource.data())
            reconstructed_gff: GFF = dismantle_uts(construct_uts(gff), Game.K1)
            assert gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True), os.linesep.join(self.log_messages)

    @unittest.skipIf(
        not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
        "K2_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k2_installation(self):
        self.installation = Installation(K2_PATH)  # type: ignore[arg-type]
        for are_resource in (resource for resource in self.installation if resource.restype() is ResourceType.UTS):
            gff: GFF = read_gff(are_resource.data())
            reconstructed_gff: GFF = dismantle_uts(construct_uts(gff))
            assert gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True), os.linesep.join(self.log_messages)

    def test_gff_reconstruct(self):
        gff = read_gff(TEST_FILE)
        reconstructed_gff = dismantle_uts(construct_uts(gff))
        assert gff.compare(reconstructed_gff, self.log_func), os.linesep.join(self.log_messages)

    def test_k1_gff_reconstruct(self):
        gff = read_gff(TEST_K1_FILE)
        reconstructed_gff = dismantle_uts(construct_uts(gff), Game.K1)
        assert gff.compare(reconstructed_gff, self.log_func), os.linesep.join(self.log_messages)

    def test_io_construct(self):
        gff = read_gff(TEST_FILE)
        uts = construct_uts(gff)
        self.validate_io(uts)

    def test_io_reconstruct(self):
        gff = read_gff(TEST_FILE)
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
