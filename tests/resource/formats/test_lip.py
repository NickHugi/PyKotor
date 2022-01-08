from unittest import TestCase

from pykotor.resource.formats.lip import LIP, LIPShape, LIPBinaryReader, detect_lip, write_lip, LIPXMLReader
from pykotor.resource.type import FileFormat

BINARY_TEST_FILE = "../../files/test.lip"
XML_TEST_FILE = "../../files/test.lip.xml"


class TestLIP(TestCase):
    def test_binary_io(self):
        self.assertEqual(detect_lip(BINARY_TEST_FILE), FileFormat.BINARY)

        lip = LIPBinaryReader(BINARY_TEST_FILE).load()
        self.validate_io(lip)

        data = bytearray()
        write_lip(lip, data, FileFormat.BINARY)
        lip = LIPBinaryReader(data).load()
        self.validate_io(lip)

    def test_xml_io(self):
        self.assertEqual(detect_lip(XML_TEST_FILE), FileFormat.XML)

        lip = LIPXMLReader(XML_TEST_FILE).load()
        self.validate_io(lip)

        data = bytearray()
        write_lip(lip, data, FileFormat.XML)
        lip = LIPXMLReader(data).load()
        self.validate_io(lip)

    def validate_io(self, lip: LIP):
        self.assertAlmostEqual(lip.length, 1.50, 3)
        self.assertEqual(LIPShape.EE, lip.get(0).shape)
        self.assertEqual(LIPShape.OOH, lip.get(1).shape)
        self.assertEqual(LIPShape.TH, lip.get(2).shape)
        self.assertAlmostEqual(0.0, lip.get(0).time, 4)
        self.assertAlmostEqual(0.7777, lip.get(1).time, 4)
        self.assertAlmostEqual(1.25, lip.get(2).time, 4)
