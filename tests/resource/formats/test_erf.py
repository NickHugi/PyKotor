import io
from unittest import TestCase

from pykotor.common.language import Language
from pykotor.common.misc import ResRef
from pykotor.common.stream import BinaryWriter
from pykotor.resource.formats.erf import ERF
from pykotor.resource.formats.tlk import TLK, TLKEntry

import time

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
