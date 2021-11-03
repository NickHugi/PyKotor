from unittest import TestCase

from pykotor.resource.formats.erf import ERF
from pykotor.resource.type import ResourceType


BINARY_TEST_FILE = "../../files/test.erf"


class TestERF(TestCase):
    def test_binary_io(self):
        erf: ERF = ERF.load_binary(BINARY_TEST_FILE)
        self.validate_io(erf)

        data = bytearray()
        erf.write_binary(data)
        ERF.load_binary(data)

    def validate_io(self, erf: ERF):
        self.assertEqual(len(erf), 3)
        self.assertEqual(erf.get("1", ResourceType.TXT), b'abc')
        self.assertEqual(erf.get("2", ResourceType.TXT), b'def')
        self.assertEqual(erf.get("3", ResourceType.TXT), b'ghi')
