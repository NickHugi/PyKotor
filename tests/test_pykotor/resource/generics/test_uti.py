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
from pykotor.resource.generics.uti import construct_uti, dismantle_uti
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFF
    from pykotor.resource.generics.uti import UTI

TEST_UTI_XML = """<gff3>
  <struct id="-1">
    <resref label="TemplateResRef">g_a_class4001</resref>
    <sint32 label="BaseItem">38</sint32>
    <locstring label="LocalizedName" strref="5632" />
    <locstring label="Description" strref="456" />
    <locstring label="DescIdentified" strref="5633" />
    <exostring label="Tag">G_A_CLASS4001</exostring>
    <byte label="Charges">13</byte>
    <uint32 label="Cost">50</uint32>
    <byte label="Stolen">1</byte>
    <uint16 label="StackSize">1</uint16>
    <byte label="Plot">1</byte>
    <uint32 label="AddCost">50</uint32>
    <byte label="Identified">1</byte>
    <byte label="BodyVariation">3</byte>
    <byte label="TextureVar">1</byte>
    <list label="PropertiesList">
      <struct id="0">
        <uint16 label="PropertyName">45</uint16>
        <uint16 label="Subtype">6</uint16>
        <byte label="CostTable">1</byte>
        <uint16 label="CostValue">1</uint16>
        <byte label="Param1">255</byte>
        <byte label="Param1Value">1</byte>
        <byte label="ChanceAppear">100</byte>
        </struct>
      <struct id="0">
        <uint16 label="PropertyName">45</uint16>
        <uint16 label="Subtype">6</uint16>
        <byte label="CostTable">1</byte>
        <uint16 label="CostValue">1</uint16>
        <byte label="Param1">255</byte>
        <byte label="Param1Value">1</byte>
        <byte label="ChanceAppear">100</byte>
        <byte label="UpgradeType">24</byte>
        </struct>
      </list>
    <byte label="PaletteID">1</byte>
    <exostring label="Comment">itemo</exostring>
    <byte label="ModelVariation">2</byte>
    </struct>
  </gff3>
"""


class TestUTI(TestCase):
    def setUp(self):
        self.log_messages: list[str] = [os.linesep]

    def log_func(self, *msgs):
        self.log_messages.append("\t".join(msgs))

    def test_gff_reconstruct(self):
        gff = read_gff(TEST_UTI_XML.encode(), file_format=ResourceType.GFF_XML)
        reconstructed_gff = dismantle_uti(construct_uti(gff), Game.K1)
        result = gff.compare(reconstructed_gff, self.log_func)
        output = os.linesep.join(self.log_messages)
        if not result:
            expected_output: str = r"Field 'LocalizedString' is different at 'GFFRoot\Description': 456 --> 5633"
            assert output.strip() == expected_output.strip(), "Comparison output does not match expected output"
        else:
            assert result

    def test_io_construct(self):
        gff = read_gff(TEST_UTI_XML.encode(), file_format=ResourceType.GFF_XML)
        uti = construct_uti(gff)
        self.validate_io(uti)

    def test_io_reconstruct(self):
        gff = read_gff(TEST_UTI_XML.encode(), file_format=ResourceType.GFF_XML)
        gff = dismantle_uti(construct_uti(gff))
        uti = construct_uti(gff)
        self.validate_io(uti)

    def validate_io(self, uti: UTI):
        assert uti.resref == "g_a_class4001"
        assert uti.base_item == 38
        assert uti.name.stringref == 5632
        assert uti.description.stringref == 5633
        assert uti.tag == "G_A_CLASS4001"
        assert uti.charges == 13
        assert uti.cost == 50
        assert uti.stolen == 1
        assert uti.stack_size == 1
        assert uti.plot == 1
        assert uti.add_cost == 50
        assert uti.texture_variation == 1
        assert uti.model_variation == 2
        assert uti.body_variation == 3
        assert uti.texture_variation == 1
        assert uti.palette_id == 1
        assert uti.comment == "itemo"

        assert len(uti.properties) == 2
        assert uti.properties[0].upgrade_type is None, None
        assert uti.properties[1].chance_appear == 100
        assert uti.properties[1].cost_table == 1
        assert uti.properties[1].cost_value == 1
        assert uti.properties[1].param1 == 255
        assert uti.properties[1].param1_value == 1
        assert uti.properties[1].property_name == 45
        assert uti.properties[1].subtype == 6
        assert uti.properties[1].upgrade_type == 24


if __name__ == "__main__":
    unittest.main()
