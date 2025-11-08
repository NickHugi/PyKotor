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
from pykotor.resource.generics.utt import construct_utt, dismantle_utt
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFF
    from pykotor.resource.generics.utt import UTT

TEST_UTT_XML = """<gff3>
  <struct id="-1">
    <exostring label="Tag">GenericTrigger001</exostring>
    <resref label="TemplateResRef">generictrigge001</resref>
    <locstring label="LocalizedName" strref="42968"></locstring>
    <byte label="AutoRemoveKey">1</byte>
    <uint32 label="Faction">1</uint32>
    <byte label="Cursor">1</byte>
    <float label="HighlightHeight">3.0</float>
    <exostring label="KeyName">somekey</exostring>
    <uint16 label="LoadScreenID">0</uint16>
    <uint16 label="PortraitId">0</uint16>
    <sint32 label="Type">1</sint32>
    <byte label="TrapDetectable">1</byte>
    <byte label="TrapDetectDC">10</byte>
    <byte label="TrapDisarmable">1</byte>
    <byte label="DisarmDC">10</byte>
    <byte label="TrapFlag">1</byte>
    <byte label="TrapOneShot">1</byte>
    <byte label="TrapType">1</byte>
    <resref label="OnDisarm">ondisarm</resref>
    <resref label="OnTrapTriggered">ontraptriggered</resref>
    <resref label="OnClick">onclick</resref>
    <resref label="ScriptHeartbeat">onheartbeat</resref>
    <resref label="ScriptOnEnter">onenter</resref>
    <resref label="ScriptOnExit">onexit</resref>
    <resref label="ScriptUserDefine">onuserdefined</resref>
    <byte label="PaletteID">6</byte>
    <exostring label="Comment">comment</exostring>
    </struct>
  </gff3>
"""


class TestUTT(TestCase):
    def setUp(self):
        self.log_messages = [os.linesep]

    def log_func(self, *msgs):
        self.log_messages.append("\t".join(msgs))

    def test_gff_reconstruct(self):
        gff = read_gff(TEST_UTT_XML.encode(), file_format=ResourceType.GFF_XML)
        reconstructed_gff = dismantle_utt(construct_utt(gff))
        assert gff.compare(reconstructed_gff, self.log_func), os.linesep.join(self.log_messages)

    def test_io_construct(self):
        gff = read_gff(TEST_UTT_XML.encode(), file_format=ResourceType.GFF_XML)
        utt = construct_utt(gff)
        self.validate_io(utt)

    def test_io_reconstruct(self):
        gff = read_gff(TEST_UTT_XML.encode(), file_format=ResourceType.GFF_XML)
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


if __name__ == "__main__":
    unittest.main()
