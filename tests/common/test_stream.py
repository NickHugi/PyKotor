from __future__ import annotations

import pathlib
import sys
import unittest
from unittest import TestCase

THIS_SCRIPT_PATH = pathlib.Path(__file__).resolve()
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[2].joinpath("Libraries", "PyKotor", "src")
UTILITY_PATH = THIS_SCRIPT_PATH.parents[2].joinpath("Libraries", "Utility", "src")


def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from pykotor.common.stream import BinaryReader


class TestBinaryReader(TestCase):
    def setUp(self):
        self.data1 = b"\x01" + b"\x02\x00" + b"\x03\x00\x00\x00" + b"\x04\x00\x00\x00\x00\x00\x00\x00"
        self.data2 = b"helloworld\x00"
        self.data3 = b"\xff" + b"\xfe\xff" + b"\xfd\xff\xff\xff" + b"\xfc\xff\xff\xff\xff\xff\xff\xff"
        self.data4 = b"\x79\xe9\xf6\xc2" + b"\x68\x91\xed\x7c\x3f\xdd\x5e\x40"

        self.reader1 = BinaryReader.from_bytes(self.data1)
        self.reader1b = BinaryReader.from_bytes(self.data1, 3)
        self.reader1c = BinaryReader.from_bytes(self.data1, 3, 4)
        self.reader2 = BinaryReader.from_bytes(self.data2)
        self.reader3 = BinaryReader.from_bytes(self.data3)
        self.reader4 = BinaryReader.from_bytes(self.data4)

    def test_read(self):
        assert self.reader1.read_uint8() == 1
        assert self.reader1.read_uint16() == 2
        assert self.reader1.read_uint32() == 3
        assert self.reader1.read_uint64() == 4

        assert self.reader1b.read_uint32() == 3
        assert self.reader1b.read_uint64() == 4

        reader2 = BinaryReader.from_bytes(self.data2)
        assert reader2.read_string(10) == "helloworld"

        reader3 = BinaryReader.from_bytes(self.data3)
        assert reader3.read_int8() == -1
        assert reader3.read_int16() == -2
        assert reader3.read_int32() == -3
        assert reader3.read_int64() == -4

        reader4 = BinaryReader.from_bytes(self.data4)
        self.assertAlmostEqual(-123.456, reader4.read_single(), 3)
        self.assertAlmostEqual(123.457, reader4.read_double(), 6)

    def test_size(self):
        self.reader1.read_bytes(4)
        assert self.reader1.size() == 15

        self.reader1b.read_bytes(4)
        assert self.reader1b.size() == 12

        self.reader1c.read_bytes(1)
        assert self.reader1c.size() == 4

    def test_true_size(self):
        self.reader1.read_bytes(4)
        assert self.reader1.true_size() == 15

        self.reader1b.read_bytes(4)
        assert self.reader1b.true_size() == 15

        self.reader1c.read_bytes(4)
        assert self.reader1c.true_size() == 15

    def test_position(self):
        self.reader1.read_bytes(3)
        self.reader1.read_bytes(3)
        assert self.reader1.position() == 6

        self.reader1b.read_bytes(1)
        self.reader1b.read_bytes(2)
        assert self.reader1b.position() == 3

        self.reader1c.read_bytes(1)
        self.reader1c.read_bytes(2)
        assert self.reader1c.position() == 3

    def test_seek(self):
        self.reader1.read_bytes(4)
        self.reader1.seek(7)
        assert self.reader1.position() == 7
        assert self.reader1.read_uint64() == 4

        self.reader1b.read_bytes(3)
        self.reader1b.seek(4)
        assert self.reader1b.position() == 4
        assert self.reader1b.read_uint32() == 4

        self.reader1c.read_bytes(3)
        self.reader1c.seek(2)
        assert self.reader1c.position() == 2
        assert self.reader1c.read_uint16() == 0

    def test_skip(self):  # sourcery skip: class-extract-method
        self.reader1.read_uint32()
        self.reader1.skip(2)
        self.reader1.skip(1)
        assert self.reader1.read_uint64() == 4

        self.reader1b.skip(4)
        assert self.reader1b.read_uint64() == 4

        self.reader1c.skip(2)
        assert self.reader1c.read_uint16() == 0

    def test_remaining(self):
        self.reader1.read_uint32()
        self.reader1.skip(2)
        self.reader1.skip(1)
        assert self.reader1.remaining() == 8

        self.reader1b.read_uint32()
        assert self.reader1b.remaining() == 8

        self.reader1c.read_uint16()
        assert self.reader1c.remaining() == 2

    def test_peek(self):
        self.reader1.skip(3)
        assert self.reader1.peek(1) == b"\x03"

        self.reader1b.skip(4)
        assert self.reader1b.peek(1) == b"\x04"

        assert self.reader1c.peek(1) == b"\x03"


if __name__ == "__main__":
    unittest.main()
