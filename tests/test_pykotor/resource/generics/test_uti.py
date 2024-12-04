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


from pykotor.resource.type import ResourceType
from pykotor.common.misc import Game
from pykotor.extract.installation import Installation
from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.uti import construct_uti, dismantle_uti

if TYPE_CHECKING:
    from pykotor.resource.formats.gff import GFF
    from pykotor.resource.generics.uti import UTI

TEST_FILE = "tests/test_pykotor/test_files/test.uti"

K1_PATH = os.environ.get("K1_PATH")
K2_PATH = os.environ.get("K2_PATH")


class TestUTI(TestCase):
    def setUp(self):
        self.log_messages: list[str] = [os.linesep]

    def log_func(self, *msgs):
        self.log_messages.append("\t".join(msgs))

    @unittest.skipIf(
        not K1_PATH or not pathlib.Path(K1_PATH).joinpath("chitin.key").exists(),
        "K1_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k1_installation(self):
        self.installation = Installation(K1_PATH)  # type: ignore[arg-type]
        for are_resource in (resource for resource in self.installation if resource.restype() is ResourceType.UTI):
            gff: GFF = read_gff(are_resource.data())
            reconstructed_gff: GFF = dismantle_uti(construct_uti(gff), Game.K1)
            assert gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True), os.linesep.join(self.log_messages)

    @unittest.skipIf(
        not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
        "K2_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k2_installation(self):
        self.installation = Installation(K2_PATH)  # type: ignore[arg-type]
        for are_resource in (resource for resource in self.installation if resource.restype() is ResourceType.UTI):
            gff: GFF = read_gff(are_resource.data())
            reconstructed_gff: GFF = dismantle_uti(construct_uti(gff))
            assert gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True), os.linesep.join(self.log_messages)

    def test_gff_reconstruct(self):
        gff: GFF = read_gff(TEST_FILE)
        reconstructed_gff: GFF = dismantle_uti(construct_uti(gff), Game.K1)
        result: bool = gff.compare(reconstructed_gff, self.log_func)
        output: str = os.linesep.join(self.log_messages)
        if not result:
            expected_output: str = r"Field 'LocalizedString' is different at 'GFFRoot\Description': 456 --> 5633"
            assert output.strip() == expected_output.strip(), "Comparison output does not match expected output"
        else:
            assert result

    def test_io_construct(self):
        gff: GFF = read_gff(TEST_FILE)
        uti: UTI = construct_uti(gff)
        self.validate_io(uti)

    def test_io_reconstruct(self):
        gff: GFF = read_gff(TEST_FILE)
        gff: GFF = dismantle_uti(construct_uti(gff))
        uti: UTI = construct_uti(gff)
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
