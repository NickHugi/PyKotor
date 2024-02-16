from __future__ import annotations

import os
import pathlib
import sys
import unittest

THIS_SCRIPT_PATH = pathlib.Path(__file__).resolve()
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[2]
UTILITY_PATH = THIS_SCRIPT_PATH.parents[4].joinpath("Utility", "src")
def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)
if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
    os.chdir(PYKOTOR_PATH.parent)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from pykotor.extract.file import ResourceIdentifier
from pykotor.resource.type import ResourceType


class TestResourceType(unittest.TestCase):
    def test_resource_type_hashing(self):
        for type_name in ResourceType.__members__:
            restype: ResourceType = ResourceType.__members__[type_name]
            test_set = {restype, restype.extension}
            self.assertEqual(len(test_set), 1, repr(test_set))

    def test_from_invalid(self):
        invalid = ResourceType.from_invalid(extension="aSdF")
        self.assertEqual(invalid, ResourceType.INVALID)
        self.assertEqual(invalid.type_id, ResourceType.INVALID.type_id)
        self.assertEqual(invalid.contents, ResourceType.INVALID.contents)
        self.assertEqual(invalid.category, ResourceType.INVALID.category)
        self.assertEqual(invalid.extension, "asdf")
        self.assertEqual(repr(invalid), "ResourceType.from_invalid(type_id=-1, extension=asdf, category=Undefined, contents=binary)")
        self.assertEqual(invalid.name, "INVALID_aSdF")
        self.assertEqual(repr(ResourceType.INVALID), "ResourceType.INVALID")
        self.assertEqual(str(invalid), "ASDF")
        self.assertNotEqual(invalid.extension, ResourceType.INVALID.extension)

    def test_from_invalid_with_valid_extension(self):  # sourcery skip: class-extract-method
        acquired_type = ResourceType.from_invalid(extension="tlk")
        self.assertEqual(acquired_type, ResourceType.INVALID)
        self.assertEqual("Tlk", acquired_type)
        self.assertEqual(acquired_type.extension, "tlk")
        self.assertEqual(acquired_type.type_id, -1)
        self.assertEqual(str(acquired_type), "TLK")
        self.assertEqual(acquired_type.contents, "binary")
        self.assertEqual(acquired_type.category, "Undefined")
        self.assertEqual(acquired_type, ResourceType.INVALID)
        self.assertEqual(acquired_type.type_id, ResourceType.INVALID.type_id)
        self.assertEqual(acquired_type.contents, ResourceType.INVALID.contents)
        self.assertEqual(acquired_type.category, ResourceType.INVALID.category)
        self.assertEqual(acquired_type.extension, "tlk")
        self.assertEqual(repr(acquired_type), "ResourceType.from_invalid(type_id=-1, extension=tlk, category=Undefined, contents=binary)")
        self.assertEqual(acquired_type.name, "INVALID_tlk")
        self.assertEqual(repr(ResourceType.INVALID), "ResourceType.INVALID")
        self.assertNotEqual(acquired_type.extension, ResourceType.INVALID.extension)
        self.assertNotEqual(acquired_type, ResourceType.TLK)
        self.assertEqual(acquired_type.extension, ResourceType.TLK)

    def test_from_extension(self):  # sourcery skip: class-extract-method
        acquired_type = ResourceType.from_extension("tlk")
        self.assertEqual(acquired_type, ResourceType.TLK)
        self.assertEqual("tLK", ResourceType.TLK)
        self.assertEqual("Tlk", acquired_type)
        self.assertEqual(ResourceType.TLK.extension, "tlk")
        self.assertEqual(ResourceType.TLK.type_id, 2018)
        self.assertEqual(repr(ResourceType.TLK), "ResourceType.TLK")
        self.assertEqual(str(ResourceType.TLK), "TLK")
        self.assertEqual(ResourceType.TLK.contents, "binary")
        self.assertEqual(ResourceType.TLK.category, "Talk Tables")
        self.assertEqual(acquired_type.extension, "tlk")
        self.assertEqual(acquired_type.type_id, 2018)
        self.assertEqual(acquired_type.contents, "binary")
        self.assertEqual(acquired_type.category, "Talk Tables")

    def test_from_id(self):
        acquired_type = ResourceType.from_id(2018)
        self.assertEqual(acquired_type, ResourceType.TLK)
        self.assertEqual("tLK", ResourceType.TLK)
        self.assertEqual("Tlk", acquired_type)
        self.assertEqual(ResourceType.TLK.extension, "tlk")
        self.assertEqual(ResourceType.TLK.type_id, 2018)
        self.assertEqual(repr(ResourceType.TLK), "ResourceType.TLK")
        self.assertEqual(str(ResourceType.TLK), "TLK")
        self.assertEqual(ResourceType.TLK.contents, "binary")
        self.assertEqual(ResourceType.TLK.category, "Talk Tables")
        self.assertEqual(acquired_type.extension, "tlk")
        self.assertEqual(acquired_type.type_id, 2018)
        self.assertEqual(acquired_type.contents, "binary")
        self.assertEqual(acquired_type.category, "Talk Tables")

    def test_from_path_long_extension(self):
        self.assertEqual(ResourceIdentifier.from_path("C:/path/to/l.o.n.g._ex.te.nsio.n.xyz").restype.extension, "xyz")
        self.assertEqual(ResourceType.from_extension(".l.o.n.g._ex.te.nsio.n.xyz").extension, "l.o.n.g._ex.te.nsio.n.xyz")

class TestResourceIdentifier(unittest.TestCase):
    """These tests were created because of the many soft, hard-to-find errors that occur all over when this function ever fails."""
    def assert_hashing(self, res_ident: ResourceIdentifier):
        lower_ident = ResourceIdentifier(res_ident.resname.swapcase(), res_ident.restype)
        self.assertEqual(res_ident, lower_ident, f"{res_ident!r} != {lower_ident!r}")
        test_set: set[ResourceIdentifier] = {res_ident, lower_ident}
        self.assertEqual(len(test_set), 1, repr(test_set))

    def assert_resource_identifier(self, file_path, expected_resname, expected_restype):
        # Common assertion logic for all tests
        result = ResourceIdentifier.from_path(file_path)
        fail_message = f"\nresname: '{result.resname}' restype: '{result.restype}'\nexpected resname: '{expected_resname}' expected restype: '{expected_restype}'"
        self.assertEqual(result.resname, expected_resname, fail_message)
        self.assertEqual(result.restype, expected_restype, fail_message)
        self.assert_hashing(result)

    def test_hashing(self):
        test_resname = "test_ResnamE"
        for type_name in ResourceType.__members__:
            test_ident = ResourceIdentifier(test_resname, ResourceType.__members__[type_name])
            self.assert_hashing(test_ident)

    def test_from_path_mdl(self):
        self.assert_resource_identifier("C:/path/to/resource.mdl", "resource", ResourceType.MDL)

    def test_from_path_tga(self):
        self.assert_resource_identifier("C:/path/to/texture.tGa", "texture", ResourceType.TGA)

    def test_from_path_wav(self):
        self.assert_resource_identifier("C:/path/to/SounD.wav", "SounD", ResourceType.WAV)

    def test_from_path_tlk_xml(self):
        self.assert_resource_identifier("C:/path/to/asdf.Tlk.XmL", "asdf", ResourceType.TLK_XML)

    def test_from_path_long_suffix_gff_xml(self):
        self.assert_resource_identifier("C:/path/to/asdf.xyz.qwerty.gff.xml", "asdf.xyz.qwerty", ResourceType.GFF_XML)

    def test_from_path_hidden_file(self):
        self.assert_resource_identifier("C:/path/to/.hidden", ".hidden", ResourceType.INVALID)

    def test_from_path_no_extension(self):
        self.assert_resource_identifier("C:/path/to/no_extension", "no_extension", ResourceType.INVALID)

    def test_from_path_long_extension(self):
        self.assert_resource_identifier("C:/path/to/longer_extension.l.o.n.g._ex.te.nsio.n.xyz", "longer_extension.l.o.n.g._ex.te.nsio.n", ResourceType.INVALID)

    def test_from_path_none_file_path(self):
        with self.assertRaises((ValueError, TypeError)):
            ResourceIdentifier.from_path(None).validate()  # type: ignore[arg-type]

    def test_from_path_empty_file_path(self):
        with self.assertRaises((ValueError, TypeError)):
            ResourceIdentifier.from_path("").validate()

    def test_from_path_invalid_extension(self):
        self.assert_resource_identifier("C:/path/to/invalid.ext", "invalid", ResourceType.INVALID)

    def test_from_path_trailing_dot(self):
        self.assert_resource_identifier("C:/path/to/invalid.", "invalid.", ResourceType.INVALID)
