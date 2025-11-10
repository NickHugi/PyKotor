from __future__ import annotations

import pathlib
import sys
import unittest

THIS_SCRIPT_PATH: pathlib.Path = pathlib.Path(__file__).resolve()
PYKOTOR_PATH: pathlib.Path = THIS_SCRIPT_PATH.parents[3].joinpath("Libraries", "PyKotor", "src")
UTILITY_PATH: pathlib.Path = THIS_SCRIPT_PATH.parents[3].joinpath("Libraries", "Utility", "src")


def add_sys_path(p: pathlib.Path) -> None:
    working_dir: str = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from pykotor.extract.file import ResourceIdentifier
from pykotor.resource.type import ResourceType


class TestResourceType(unittest.TestCase):
    def test_resource_type_hashing(self):
        for type_name in ResourceType.__members__:
            restype: ResourceType = ResourceType.__members__[type_name]
            test_set: set[ResourceType | str] = {restype, restype.extension}
            assert len(test_set) == 1, f"{repr(test_set)} != 1"

    @unittest.skip("ResourceType.from_invalid usage in this manner is deprecated")
    def test_from_invalid(self):
        invalid: ResourceType = ResourceType.from_invalid(extension="aSdF")
        assert invalid == ResourceType.INVALID, f"{invalid!r} != {ResourceType.INVALID!r}"
        assert invalid.type_id == ResourceType.INVALID.type_id, f"{invalid.type_id!r} != {ResourceType.INVALID.type_id!r}"
        assert invalid.contents == ResourceType.INVALID.contents, f"{invalid.contents!r} != {ResourceType.INVALID.contents!r}"
        assert invalid.category == ResourceType.INVALID.category, f"{invalid.category!r} != {ResourceType.INVALID.category!r}"
        assert invalid.extension == "asdf", f"{invalid.extension!r} != asdf"
        assert repr(invalid) == "ResourceType.from_invalid(type_id=-1, extension=asdf, category=Undefined, contents=binary)", f"{repr(invalid)!r} != ResourceType.from_invalid(type_id=-1, extension=asdf, category=Undefined, contents=binary)"
        assert invalid.name == "INVALID_aSdF", f"{invalid.name!r} != INVALID_aSdF"
        assert repr(ResourceType.INVALID) == "ResourceType.INVALID", f"{repr(ResourceType.INVALID)!r} != ResourceType.INVALID"
        assert str(invalid) == "ASDF", f"{str(invalid)!r} != ASDF"
        assert invalid.extension != ResourceType.INVALID.extension, f"{invalid.extension!r} != {ResourceType.INVALID.extension!r}"

    @unittest.skip("ResourceType.from_invalid usage in this manner is deprecated")
    def test_from_invalid_with_valid_extension(self):  # sourcery skip: class-extract-method
        acquired_type: ResourceType = ResourceType.from_invalid(extension="tlk")
        assert acquired_type == ResourceType.INVALID, f"{acquired_type!r} != {ResourceType.INVALID!r}"
        assert acquired_type == "Tlk", f"{acquired_type!r} != Tlk"
        assert acquired_type.extension == "tlk", f"{acquired_type.extension!r} != tlk"
        assert acquired_type.type_id == -1, f"{acquired_type.type_id!r} != -1"
        assert str(acquired_type) == "TLK", f"{str(acquired_type)!r} != TLK"
        assert acquired_type.contents == "binary", f"{acquired_type.contents!r} != binary"
        assert acquired_type.category == "Undefined", f"{acquired_type.category!r} != Undefined"
        assert acquired_type == ResourceType.INVALID, f"{acquired_type!r} != {ResourceType.INVALID!r}"
        assert acquired_type.type_id == ResourceType.INVALID.type_id, f"{acquired_type.type_id!r} != {ResourceType.INVALID.type_id!r}"
        assert acquired_type.contents == ResourceType.INVALID.contents, f"{acquired_type.contents!r} != {ResourceType.INVALID.contents!r}"
        assert acquired_type.category == ResourceType.INVALID.category, f"{acquired_type.category!r} != {ResourceType.INVALID.category!r}"
        assert acquired_type.extension == "tlk", f"{acquired_type.extension!r} != tlk"
        assert repr(acquired_type) == "ResourceType.from_invalid(type_id=-1, extension=tlk, category=Undefined, contents=binary)", f"{repr(acquired_type)!r} != ResourceType.from_invalid(type_id=-1, extension=tlk, category=Undefined, contents=binary)"
        assert acquired_type.name == "INVALID_tlk", f"{acquired_type.name!r} != INVALID_tlk"
        assert repr(ResourceType.INVALID) == "ResourceType.INVALID", f"{repr(ResourceType.INVALID)!r} != ResourceType.INVALID"
        assert acquired_type.extension != ResourceType.INVALID.extension, f"{acquired_type.extension!r} != {ResourceType.INVALID.extension!r}"
        assert acquired_type != ResourceType.TLK, f"{acquired_type!r} != {ResourceType.TLK!r}"
        assert acquired_type.extension == ResourceType.TLK.extension, f"{acquired_type.extension!r} != {ResourceType.TLK.extension!r}"

    def test_from_extension(self):  # sourcery skip: class-extract-method
        acquired_type: ResourceType = ResourceType.from_extension("tlk")
        assert acquired_type == ResourceType.TLK, f"{acquired_type!r} != {ResourceType.TLK!r}"
        assert ResourceType.TLK == "tLK", f"{ResourceType.TLK!r} != tLK"
        assert acquired_type == "Tlk", f"{acquired_type!r} != Tlk"
        assert ResourceType.TLK.extension == "tlk", f"{ResourceType.TLK.extension!r} != tlk"
        assert ResourceType.TLK.type_id == 2018, f"{ResourceType.TLK.type_id!r} != 2018"
        assert repr(ResourceType.TLK) == "ResourceType.TLK", f"{repr(ResourceType.TLK)!r} != ResourceType.TLK"
        assert str(ResourceType.TLK) == "TLK", f"{str(ResourceType.TLK)!r} != TLK"
        assert ResourceType.TLK.contents == "binary", f"{ResourceType.TLK.contents!r} != binary"
        assert ResourceType.TLK.category == "Talk Tables", f"{ResourceType.TLK.category!r} != Talk Tables"
        assert acquired_type.extension == "tlk", f"{acquired_type.extension!r} != tlk"
        assert acquired_type.type_id == 2018, f"{acquired_type.type_id!r} != 2018"
        assert acquired_type.contents == "binary", f"{acquired_type.contents!r} != binary"
        assert acquired_type.category == "Talk Tables", f"{acquired_type.category!r} != Talk Tables"

    def test_from_id(self):
        acquired_type: ResourceType = ResourceType.from_id(2018)
        assert acquired_type == ResourceType.TLK, f"{acquired_type!r} != {ResourceType.TLK!r}"
        assert ResourceType.TLK == "tLK", f"{ResourceType.TLK!r} != tLK"
        assert acquired_type == "Tlk", f"{acquired_type!r} != Tlk"
        assert ResourceType.TLK.extension == "tlk", f"{ResourceType.TLK.extension!r} != tlk"
        assert ResourceType.TLK.type_id == 2018, f"{ResourceType.TLK.type_id!r} != 2018"
        assert repr(ResourceType.TLK) == "ResourceType.TLK", f"{repr(ResourceType.TLK)!r} != ResourceType.TLK"
        assert str(ResourceType.TLK) == "TLK", f"{str(ResourceType.TLK)!r} != TLK"
        assert ResourceType.TLK.contents == "binary", f"{ResourceType.TLK.contents!r} != binary"
        assert ResourceType.TLK.category == "Talk Tables", f"{ResourceType.TLK.category!r} != Talk Tables"
        assert acquired_type.extension == "tlk", f"{acquired_type.extension!r} != tlk"
        assert acquired_type.type_id == 2018, f"{acquired_type.type_id!r} != 2018"
        assert acquired_type.contents == "binary", f"{acquired_type.contents!r} != binary"
        assert acquired_type.category == "Talk Tables", f"{acquired_type.category!r} != Talk Tables"

    @unittest.skip("ResourceType.from_extension usage in this manner is deprecated")
    def test_from_path_long_extension(self):
        test1: str = ResourceIdentifier.from_path("C:/path/to/l.o.n.g._ex.te.nsio.n.xyz").restype.extension
        expected1: str = "xyz"
        assert test1 == expected1, f"{test1!r} != {expected1!r}"

        test2: str = ResourceType.from_extension(".l.o.n.g._ex.te.nsio.n.xyz").extension
        expected2: str = "l.o.n.g._ex.te.nsio.n.xyz"
        assert test2 == expected2, f"{test2!r} != {expected2!r}"


class TestResourceIdentifier(unittest.TestCase):
    """These tests were created because of the many soft, hard-to-find errors that occur all over when this function ever fails."""

    def assert_hashing(self, res_ident: ResourceIdentifier):
        lower_ident = ResourceIdentifier(res_ident.resname.swapcase(), res_ident.restype)
        assert res_ident == lower_ident, f"{res_ident!r} == {lower_ident!r}"
        test_set: set[ResourceIdentifier] = {res_ident, lower_ident}
        assert len(test_set) == 1, f"{repr(test_set)} != 1"

    def assert_resource_identifier(
        self,
        file_path: str,
        expected_resname: str,
        expected_restype: ResourceType,
    ):
        # Common assertion logic for all tests
        result: ResourceIdentifier = ResourceIdentifier.from_path(file_path)
        fail_message: str = f"\nresname: '{result.resname}' restype: '{result.restype}'\nexpected resname: '{expected_resname}' expected restype: '{expected_restype}'"
        assert result.resname == expected_resname, fail_message
        assert result.restype == expected_restype, fail_message
        self.assert_hashing(result)

    def test_hashing(self):
        test_resname = "test_ResnamE"
        for type_name in ResourceType.__members__:
            test_ident: ResourceIdentifier = ResourceIdentifier(test_resname, ResourceType.__members__[type_name])
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
