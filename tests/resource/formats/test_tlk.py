import io
from unittest import TestCase

from pykotor.common.language import Language
from pykotor.common.misc import ResRef
from pykotor.common.stream import BinaryWriter
from pykotor.resource.formats.tlk import TLK, TLKEntry

import time

BINARY_TEST_FILE = "../../files/test.tlk"


class TestTLK(TestCase):
    def test_binary_io(self):
        tlk: TLK = TLK.load_binary(BINARY_TEST_FILE)
        self.validate_io(tlk)

        data = bytearray()
        tlk.write_binary(data)
        TLK.load_binary(data)

    def validate_io(self, tlk: TLK):
        self.assertIs(tlk.language, Language.ENGLISH)

        self.assertEqual(TLKEntry("abcdef", ResRef("resref01")), tlk[0])
        self.assertEqual(TLKEntry("ghijklmnop", ResRef("resref02")), tlk[1])
        self.assertEqual(TLKEntry("qrstuvwxyz", ResRef("")), tlk[2])


