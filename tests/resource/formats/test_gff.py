import os
import pathlib
import sys
import unittest
from unittest import TestCase

if getattr(sys, "frozen", False) is False:
    pykotor_path = pathlib.Path(__file__).parents[3] / "pykotor"
    if pykotor_path.exists() and str(pykotor_path) not in sys.path:
        sys.path.insert(0, str(pykotor_path.parent))

from pykotor.common.geometry import Vector3, Vector4
from pykotor.common.language import Gender, Language
from pykotor.resource.formats.gff import GFF, GFFBinaryReader, GFFXMLReader, read_gff, write_gff
from pykotor.resource.type import ResourceType

BINARY_TEST_FILE = "tests/files/test.gff"
XML_TEST_FILE = "tests/files/test.gff.xml"
DOES_NOT_EXIST_FILE = "./thisfiledoesnotexist"
CORRUPT_BINARY_TEST_FILE = "tests/files/test_corrupted.gff"
CORRUPT_XML_TEST_FILE = "tests/files/test_corrupted.gff.xml"


class TestGFF(TestCase):
    def test_binary_io(self):
        gff = GFFBinaryReader(BINARY_TEST_FILE).load()
        self.validate_io(gff)

        data = bytearray()
        write_gff(gff, data, ResourceType.GFF)
        gff = read_gff(data)
        self.validate_io(gff)

    def test_xml_io(self):
        gff = GFFXMLReader(XML_TEST_FILE).load()
        self.validate_io(gff)

        data = bytearray()
        write_gff(gff, data, ResourceType.GFF_XML)
        gff = read_gff(data)
        self.validate_io(gff)

    def validate_io(self, gff: GFF):
        self.assertEqual(gff.root.get_uint8("uint8"), 255)
        self.assertEqual(gff.root.get_int8("int8"), -127)
        self.assertEqual(gff.root.get_uint16("uint16"), 0xFFFF)
        self.assertEqual(gff.root.get_int16("int16"), -32768)
        self.assertEqual(gff.root.get_uint32("uint32"), 0xFFFFFFFF)
        self.assertEqual(gff.root.get_int32("int32"), -2147483648)
        # K-GFF does not seem to handle int64 correctly?
        self.assertEqual(gff.root.get_uint64("uint64"), 4294967296)

        self.assertAlmostEqual(gff.root.get_single("single"), 12.34567, 5)
        self.assertAlmostEqual(gff.root.get_double("double"), 12.345678901234, 14)

        self.assertEqual("abcdefghij123456789", gff.root.get_string("string"))
        self.assertEqual("resref01", gff.root.get_resref("resref"))
        self.assertEqual(b"binarydata", gff.root.get_binary("binary"))

        self.assertEqual(gff.root.get_vector4("orientation"), Vector4(1, 2, 3, 4))
        self.assertEqual(gff.root.get_vector3("position"), Vector3(11, 22, 33))

        locstring = gff.root.get_locstring("locstring")
        self.assertEqual(locstring.stringref, -1)
        self.assertEqual(len(locstring), 2)
        self.assertEqual(locstring.get(Language.ENGLISH, Gender.MALE), "male_eng")
        self.assertEqual(locstring.get(Language.GERMAN, Gender.FEMALE), "fem_german")

        self.assertEqual(gff.root.get_struct("child_struct").get_uint8("child_uint8"), 4)
        self.assertEqual(gff.root.get_list("list").at(0).struct_id, 1)
        self.assertEqual(gff.root.get_list("list").at(1).struct_id, 2)

    def test_read_raises(self):
        if os.name == "nt":
            self.assertRaises(PermissionError, read_gff, ".")
        else:
            self.assertRaises(IsADirectoryError, read_gff, ".")
        self.assertRaises(FileNotFoundError, read_gff, DOES_NOT_EXIST_FILE)
        self.assertRaises(ValueError, read_gff, CORRUPT_BINARY_TEST_FILE)
        self.assertRaises(ValueError, read_gff, CORRUPT_XML_TEST_FILE)

    def test_write_raises(self):
        if os.name == "nt":
            self.assertRaises(PermissionError, write_gff, GFF(), ".", ResourceType.GFF)
        else:
            self.assertRaises(IsADirectoryError, write_gff, GFF(), ".", ResourceType.GFF)
        self.assertRaises(ValueError, write_gff, GFF(), ".", ResourceType.INVALID)


if __name__ == "__main__":
    unittest.main()
