import os
import pathlib
import sys
import unittest
from unittest import TestCase

THIS_SCRIPT_PATH = pathlib.Path(__file__)
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

from pykotor.common.stream import BinaryReader


class TestBinaryReader(TestCase):
    def setUp(self):
        self.data1 = b"\x01" + b"\x02\x00" + b"\x03\x00\x00\x00" + b"\x04\x00\x00\x00\x00\x00\x00\x00"
        self.data2 = b"helloworld\x00"
        self.data3 = b"\xFF" + b"\xFE\xFF" + b"\xFD\xFF\xFF\xFF" + b"\xFC\xFF\xFF\xFF\xFF\xFF\xFF\xFF"
        self.data4 = b"\x79\xE9\xF6\xC2" + b"\x68\x91\xED\x7C\x3F\xDD\x5E\x40"

        self.reader1 = BinaryReader.from_bytes(self.data1)
        self.reader1b = BinaryReader.from_bytes(self.data1, 3)
        self.reader1c = BinaryReader.from_bytes(self.data1, 3, 4)
        self.reader2 = BinaryReader.from_bytes(self.data2)
        self.reader3 = BinaryReader.from_bytes(self.data3)
        self.reader4 = BinaryReader.from_bytes(self.data4)

    def test_read(self):
        self.assertEqual(1, self.reader1.read_uint8())
        self.assertEqual(2, self.reader1.read_uint16())
        self.assertEqual(3, self.reader1.read_uint32())
        self.assertEqual(4, self.reader1.read_uint64())

        self.assertEqual(3, self.reader1b.read_uint32())
        self.assertEqual(4, self.reader1b.read_uint64())

        reader2 = BinaryReader.from_bytes(self.data2)
        self.assertEqual("helloworld", reader2.read_string(10))

        reader3 = BinaryReader.from_bytes(self.data3)
        self.assertEqual(-1, reader3.read_int8())
        self.assertEqual(-2, reader3.read_int16())
        self.assertEqual(-3, reader3.read_int32())
        self.assertEqual(-4, reader3.read_int64())

        reader4 = BinaryReader.from_bytes(self.data4)
        self.assertAlmostEqual(-123.456, reader4.read_single(), 3)
        self.assertAlmostEqual(123.457, reader4.read_double(), 6)

    def test_size(self):
        self.reader1.read_bytes(4)
        self.assertEqual(15, self.reader1.size())

        self.reader1b.read_bytes(4)
        self.assertEqual(12, self.reader1b.size())

        self.reader1c.read_bytes(1)
        self.assertEqual(4, self.reader1c.size())

    def test_true_size(self):
        self.reader1.read_bytes(4)
        self.assertEqual(15, self.reader1.true_size())

        self.reader1b.read_bytes(4)
        self.assertEqual(15, self.reader1b.true_size())

        self.reader1c.read_bytes(4)
        self.assertEqual(15, self.reader1c.true_size())

    def test_position(self):
        self.reader1.read_bytes(3)
        self.reader1.read_bytes(3)
        self.assertEqual(6, self.reader1.position())

        self.reader1b.read_bytes(1)
        self.reader1b.read_bytes(2)
        self.assertEqual(3, self.reader1b.position())

        self.reader1c.read_bytes(1)
        self.reader1c.read_bytes(2)
        self.assertEqual(3, self.reader1c.position())

    def test_seek(self):
        self.reader1.read_bytes(4)
        self.reader1.seek(7)
        self.assertEqual(7, self.reader1.position())
        self.assertEqual(4, self.reader1.read_uint64())

        self.reader1b.read_bytes(3)
        self.reader1b.seek(4)
        self.assertEqual(4, self.reader1b.position())
        self.assertEqual(4, self.reader1b.read_uint32())

        self.reader1c.read_bytes(3)
        self.reader1c.seek(2)
        self.assertEqual(2, self.reader1c.position())
        self.assertEqual(0, self.reader1c.read_uint16())

    def test_skip(self):
        self.reader1.read_uint32()
        self.reader1.skip(2)
        self.reader1.skip(1)
        self.assertEqual(4, self.reader1.read_uint64())

        self.reader1b.skip(4)
        self.assertEqual(4, self.reader1b.read_uint64())

        self.reader1c.skip(2)
        self.assertEqual(0, self.reader1c.read_uint16())

    def test_remaining(self):
        self.reader1.read_uint32()
        self.reader1.skip(2)
        self.reader1.skip(1)
        self.assertEqual(8, self.reader1.remaining())

        self.reader1b.read_uint32()
        self.assertEqual(8, self.reader1b.remaining())

        self.reader1c.read_uint16()
        self.assertEqual(2, self.reader1c.remaining())

    def test_peek(self):
        self.reader1.skip(3)
        self.assertEqual(b"\x03", self.reader1.peek(1))

        self.reader1b.skip(4)
        self.assertEqual(b"\x04", self.reader1b.peek(1))

        self.assertEqual(b"\x03", self.reader1c.peek(1))


if __name__ == "__main__":
    unittest.main()
