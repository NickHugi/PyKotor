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
from pykotor.resource.generics.utw import construct_utw, dismantle_utw
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFF
    from pykotor.resource.generics.utw import UTW

TEST_UTW_XML = """<gff3>
  <struct id="-1">
    <byte label="Appearance">1</byte>
    <exostring label="LinkedTo"></exostring>
    <resref label="TemplateResRef">sw_mapnote011</resref>
    <exostring label="Tag">MN_106PER2</exostring>
    <locstring label="LocalizedName" strref="76857"></locstring>
    <locstring label="Description" strref="-1"></locstring>
    <byte label="HasMapNote">1</byte>
    <locstring label="MapNote" strref="76858"></locstring>
    <byte label="MapNoteEnabled">1</byte>
    <byte label="PaletteID">5</byte>
    <exostring label="Comment">comment</exostring>
    </struct>
  </gff3>
"""


class TestUTW(TestCase):
    def setUp(self):
        self.log_messages = [os.linesep]

    def log_func(self, *msgs):
        self.log_messages.append("\t".join(msgs))

    def test_gff_reconstruct(self):
        gff = read_gff(TEST_UTW_XML.encode(), file_format=ResourceType.GFF_XML)
        reconstructed_gff = dismantle_utw(construct_utw(gff))
        assert gff.compare(reconstructed_gff, self.log_func), os.linesep.join(self.log_messages)

    def test_io_construct(self):
        gff = read_gff(TEST_UTW_XML.encode(), file_format=ResourceType.GFF_XML)
        utw = construct_utw(gff)
        self.validate_io(utw)

    def test_io_reconstruct(self):
        gff = read_gff(TEST_UTW_XML.encode(), file_format=ResourceType.GFF_XML)
        gff = dismantle_utw(construct_utw(gff))
        utw = construct_utw(gff)
        self.validate_io(utw)

    def validate_io(self, utw: UTW):
        assert utw.appearance_id == 1
        assert utw.linked_to == ""
        assert utw.resref == "sw_mapnote011"
        assert utw.tag == "MN_106PER2"
        assert utw.name.stringref == 76857
        assert utw.description.stringref == -1
        assert utw.has_map_note
        assert utw.map_note.stringref == 76858
        assert utw.map_note_enabled == 1
        assert utw.palette_id == 5
        assert utw.comment == "comment"


if __name__ == "__main__":
    unittest.main()
