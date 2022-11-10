from unittest import TestCase

from pykotor.common.stream import BinaryReader

from pykotor.resource.formats.lip import LIP
from pykotor.resource.formats.ncs import NCSBinaryReader, NCS, NCSBinaryWriter
from pykotor.resource.formats.ncs.ncs_auto import bytes_ncs, write_ncs, read_ncs

BINARY_TEST_FILE = "../../files/test.ncs"


class TestNCS(TestCase):
    def test_binary_io(self):
        ncs = NCSBinaryReader(BINARY_TEST_FILE).load()
        self.validate_io(ncs)

        write_ncs(ncs, r"C:\Users\hugin\Desktop\ext\output.ncs")
        data = bytes_ncs(ncs)
        ncs = read_ncs(data)
        self.validate_io(ncs)

    def validate_io(self, ncs: NCS):
        self.assertEqual(8, len(ncs.instructions))

        self.assertEqual(BinaryReader.load_file(BINARY_TEST_FILE), bytes_ncs(ncs))
