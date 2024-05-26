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

TEST_FILE = "tests/files/test.uts"
TEST_K1_FILE = "tests/files/test_k1.uts"

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
            self.assertTrue(gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True), os.linesep.join(self.log_messages))

    @unittest.skipIf(
        not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
        "K2_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k2_installation(self):
        self.installation = Installation(K2_PATH)  # type: ignore[arg-type]
        for are_resource in (resource for resource in self.installation if resource.restype() is ResourceType.UTS):
            gff: GFF = read_gff(are_resource.data())
            reconstructed_gff: GFF = dismantle_uts(construct_uts(gff))
            self.assertTrue(gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True), os.linesep.join(self.log_messages))

    def test_gff_reconstruct(self):
        gff = read_gff(TEST_FILE)
        reconstructed_gff = dismantle_uts(construct_uts(gff))
        self.assertTrue(gff.compare(reconstructed_gff, self.log_func), os.linesep.join(self.log_messages))

    def test_k1_gff_reconstruct(self):
        gff = read_gff(TEST_K1_FILE)
        reconstructed_gff = dismantle_uts(construct_uts(gff), Game.K1)
        self.assertTrue(gff.compare(reconstructed_gff, self.log_func), os.linesep.join(self.log_messages))

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
        self.assertEqual("3Csounds", uts.tag)
        self.assertEqual(128551, uts.name.stringref)
        self.assertEqual("3csounds", uts.resref)
        self.assertEqual(1, uts.active)
        self.assertEqual(1, uts.continuous)
        self.assertEqual(1, uts.looping)
        self.assertEqual(1, uts.positional)
        self.assertEqual(1, uts.random_position)
        self.assertEqual(1, uts.random_position)
        self.assertEqual(1.5, uts.elevation)
        self.assertEqual(8.0, uts.max_distance)
        self.assertEqual(5.0, uts.min_distance)
        self.assertEqual(0.10000000149011612, uts.random_range_x)
        self.assertEqual(0.20000000298023224, uts.random_range_y)
        self.assertEqual(4000, uts.interval)
        self.assertEqual(100, uts.interval_variation)
        self.assertEqual(0.10000000149011612, uts.pitch_variation)
        self.assertEqual(22, uts.priority)
        self.assertEqual(0, uts.hours)
        self.assertEqual(3, uts.times)
        self.assertEqual(120, uts.volume)
        self.assertEqual(7, uts.volume_variation)
        self.assertEqual(6, uts.palette_id)
        self.assertEqual("comment", uts.comment)

        self.assertEqual(4, len(uts.sounds))
        self.assertEqual("c_drdastro_atk2", uts.sounds[3])
