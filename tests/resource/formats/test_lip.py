from unittest import TestCase

from pykotor.resource.formats.lip import LIP, LIPShape
from pykotor.resource.type import ResourceType


BINARY_TEST_FILE = "../../files/test.lip"
XML_TEST_FILE = "../../files/test.lip.xml"


class TestLIP(TestCase):
    def test_binary_io(self):
        lip: LIP = LIP.load_binary(BINARY_TEST_FILE)
        self.validate_io(lip)

        data = bytearray()
        lip.write_binary(data)
        LIP.load_binary(data)

    def test_xml_io(self):
        lip: LIP = LIP.load_xml(XML_TEST_FILE)
        self.validate_io(lip)

        data = bytearray()
        lip.write_xml(data)
        LIP.load_xml(data)

    def validate_io(self, lip: LIP):
        self.assertAlmostEqual(lip.length, 1.50, 3)
        self.assertEqual(LIPShape.EE, lip.get(0).shape)
        self.assertEqual(LIPShape.OOH, lip.get(1).shape)
        self.assertEqual(LIPShape.TH, lip.get(2).shape)
        self.assertAlmostEqual(0.0, lip.get(0).time, 4)
        self.assertAlmostEqual(0.7777, lip.get(1).time, 4)
        self.assertAlmostEqual(1.25, lip.get(2).time, 4)
