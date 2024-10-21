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
from pykotor.resource.generics.utt import construct_utt, dismantle_utt

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFF
    from pykotor.resource.generics.utt import UTT

TEST_FILE = "tests/test_files/test.utt"

K1_PATH = os.environ.get("K1_PATH")
K2_PATH = os.environ.get("K2_PATH")


class TestUTT(TestCase):
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
        for resource in (resource for resource in self.installation if resource.restype() is ResourceType.UTT):
            gff: GFF = read_gff(resource.data())
            reconstructed_gff: GFF = dismantle_utt(construct_utt(gff), Game.K1)
            assert gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True), os.linesep.join(self.log_messages)

    @unittest.skipIf(
        not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
        "K2_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k2_installation(self):
        self.installation = Installation(K2_PATH)  # type: ignore[arg-type]
        for resource in (resource for resource in self.installation if resource.restype() is ResourceType.UTT):
            gff: GFF = read_gff(resource.data())
            reconstructed_gff: GFF = dismantle_utt(construct_utt(gff))
            assert gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True), os.linesep.join(self.log_messages)

    def test_gff_reconstruct(self):
        gff = read_gff(TEST_FILE)
        reconstructed_gff = dismantle_utt(construct_utt(gff))
        assert gff.compare(reconstructed_gff, self.log_func), os.linesep.join(self.log_messages)

    def test_io_construct(self):
        gff = read_gff(TEST_FILE)
        utt = construct_utt(gff)
        self.validate_io(utt)

    def test_io_reconstruct(self):
        gff = read_gff(TEST_FILE)
        gff = dismantle_utt(construct_utt(gff))
        utt = construct_utt(gff)
        self.validate_io(utt)

    def validate_io(self, utt: UTT):
        assert utt.tag == "GenericTrigger001"
        assert utt.resref == "generictrigge001"
        assert utt.name.stringref == 42968
        assert utt.auto_remove_key == 1
        assert utt.faction_id == 1
        assert utt.cursor_id == 1
        assert utt.highlight_height == 3.0
        assert utt.key_name == "somekey"
        assert utt.loadscreen_id == 0
        assert utt.portrait_id == 0
        assert utt.type_id == 1
        assert utt.trap_detectable == 1
        assert utt.trap_detect_dc == 10
        assert utt.trap_disarmable == 1
        assert utt.trap_disarm_dc == 10
        assert utt.is_trap == 1
        assert utt.trap_once == 1
        assert utt.trap_type == 1
        assert utt.on_disarm == "ondisarm"
        assert utt.on_trap_triggered == "ontraptriggered"
        assert utt.on_click == "onclick"
        assert utt.on_heartbeat == "onheartbeat"
        assert utt.on_enter == "onenter"
        assert utt.on_exit == "onexit"
        assert utt.on_user_defined == "onuserdefined"
        assert utt.palette_id == 6
        assert utt.comment == "comment"
