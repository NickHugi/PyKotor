from __future__ import annotations

from io import BytesIO
import pathlib
import sys
import unittest
from unittest import TestCase

THIS_SCRIPT_PATH = pathlib.Path(__file__).resolve()
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[3].joinpath("Libraries", "PyKotor", "src")
UTILITY_PATH = THIS_SCRIPT_PATH.parents[3].joinpath("Libraries", "Utility", "src")


def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from pykotor.common.stream import BinaryReader, BinaryWriter, BinaryWriterBytearray


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


class TestBinaryWriterBytearray(TestCase):
    def test_write_terminated_string_empty_bytearray(self):
        """Test writing terminated string to an empty bytearray."""
        writer = BinaryWriterBytearray(bytearray())
        writer.write_terminated_string("hello")

        # Should have "hello" + null terminator
        assert writer.data() == b"hello\x00"
        assert writer.position() == 6

    def test_write_terminated_string_position_beyond_size(self):
        """Test writing when position is beyond current bytearray size."""
        writer = BinaryWriterBytearray(bytearray(5))
        writer.seek(10)  # Position beyond current size
        writer.write_terminated_string("test")

        # Bytearray should be extended to accommodate the write
        data = writer.data()
        assert len(data) >= 15  # 10 (position) + 4 (test) + 1 (null)
        assert data[10:15] == b"test\x00"
        assert writer.position() == 15

    def test_write_terminated_string_extends_bytearray(self):
        """Test that bytearray is extended when string doesn't fit."""
        writer = BinaryWriterBytearray(bytearray(3))
        writer.seek(2)  # Position 2
        writer.write_terminated_string("abc")  # 3 bytes + 1 null = 4 bytes, needs position 6

        # Should extend from 3 to at least 6 bytes
        data = writer.data()
        assert len(data) >= 6
        assert data[2:6] == b"abc\x00"
        assert writer.position() == 6

    def test_write_terminated_string_fits_existing_space(self):
        """Test writing when bytearray already has enough space."""
        writer = BinaryWriterBytearray(bytearray(10))
        writer.seek(3)
        writer.write_terminated_string("hi")

        # Should write without extending (10 bytes is enough)
        data = writer.data()
        assert len(data) == 10
        assert data[3:6] == b"hi\x00"
        assert writer.position() == 6

    def test_write_terminated_string_null_terminator(self):
        """Test that null terminator is correctly written."""
        writer = BinaryWriterBytearray(bytearray())
        writer.write_terminated_string("test")

        data = writer.data()
        assert data[-1] == 0  # Last byte should be null terminator
        assert data == b"test\x00"

    def test_write_terminated_string_multiple_writes(self):
        """Test multiple terminated string writes."""
        writer = BinaryWriterBytearray(bytearray())
        writer.write_terminated_string("first")
        writer.write_terminated_string("second")

        data = writer.data()
        assert data == b"first\x00second\x00"
        assert writer.position() == 13  # 5 + 1 + 6 + 1

    def test_write_terminated_string_encoding(self):
        """Test writing terminated string with different encoding."""
        writer = BinaryWriterBytearray(bytearray())
        # Test with UTF-8 encoding
        writer.write_terminated_string("héllo", encoding="utf-8")

        data = writer.data()
        # UTF-8 encoding of "héllo" + null
        assert data.endswith(b"\x00")
        assert data[:-1].decode("utf-8") == "héllo"

    def test_write_terminated_string_empty_string(self):
        """Test writing an empty terminated string."""
        writer = BinaryWriterBytearray(bytearray())
        writer.write_terminated_string("")

        data = writer.data()
        assert data == b"\x00"  # Just null terminator
        assert writer.position() == 1

    def test_write_terminated_string_large_string(self):
        """Test writing a large string that requires significant extension."""
        large_string = "x" * 1000
        writer = BinaryWriterBytearray(bytearray(10))
        writer.seek(5)
        writer.write_terminated_string(large_string)

        data = writer.data()
        assert len(data) >= 1006  # 5 (position) + 1000 (string) + 1 (null)
        assert data[5:1005] == large_string.encode("windows-1252")
        assert data[1005] == 0
        assert writer.position() == 1006


class TestBinaryReaderPorted(unittest.TestCase):
    """Test BinaryReader ported from reone test/system/binaryreader.cpp"""

    def test_seek_ignore_and_tell_in_little_endian_stream(self):
        """Test seeking, skipping bytes, and telling position in little endian stream."""
        input_data = b"Hello, world!\x00"
        stream = BytesIO(input_data)
        reader = BinaryReader(stream)
        expected_pos = 7

        reader.seek(5)
        reader.skip(2)
        actual_pos = reader.position()

        self.assertEqual(expected_pos, actual_pos)

    def test_read_from_little_endian_stream(self):
        """Test reading various data types from little endian stream."""
        input_data = (
            b"\xff"  # byte
            b"\x01\xff"  # uint16
            b"\x02\xff\xff\xff"  # uint32
            b"\x03\xff\xff\xff\xff\xff\xff\xff"  # uint64
            b"\x01\xff"  # int16
            b"\x02\xff\xff\xff"  # int32
            b"\x03\xff\xff\xff\xff\xff\xff\xff"  # int64
            b"\x00\x00\x80\x3f"  # float
            b"\x00\x00\x00\x00\x00\x00\xf0\x3f"  # double
            b"Hello, world!"  # string
            b"Hello, world!\x00"  # cstring
            b"\x01\x02\x03\x04"  # bytes
        )
        stream = BytesIO(input_data)
        reader = BinaryReader(stream)

        expected_byte = 255
        expected_uint16 = 65281
        expected_uint32 = 4294967042
        expected_uint64 = 18446744073709551363
        expected_int16 = -255
        expected_int32 = -254
        expected_int64 = -253
        expected_float = 1.0
        expected_double = 1.0
        expected_str = "Hello, world!"
        expected_cstr = "Hello, world!"
        expected_bytes = bytes([0x01, 0x02, 0x03, 0x04])

        actual_byte = reader.read_uint8()
        actual_uint16 = reader.read_uint16()
        actual_uint32 = reader.read_uint32()
        actual_uint64 = reader.read_uint64()
        actual_int16 = reader.read_int16()
        actual_int32 = reader.read_int32()
        actual_int64 = reader.read_int64()
        actual_float = reader.read_single()
        actual_double = reader.read_double()
        actual_str = reader.read_string(13)
        actual_cstr = reader.read_terminated_string("\0")
        actual_bytes = reader.read_bytes(4)

        self.assertEqual(expected_byte, actual_byte)
        self.assertEqual(expected_uint16, actual_uint16)
        self.assertEqual(expected_uint32, actual_uint32)
        self.assertEqual(expected_uint64, actual_uint64)
        self.assertEqual(expected_int16, actual_int16)
        self.assertEqual(expected_int32, actual_int32)
        self.assertEqual(expected_int64, actual_int64)
        self.assertAlmostEqual(expected_float, actual_float, places=5)
        self.assertAlmostEqual(expected_double, actual_double, places=5)
        self.assertEqual(expected_str, actual_str)
        self.assertEqual(expected_cstr, actual_cstr)
        self.assertEqual(expected_bytes, actual_bytes)

    def test_read_from_big_endian_stream(self):
        """Test reading various data types from big endian stream."""
        input_data = (
            b"\xff\x01"  # uint16
            b"\xff\xff\xff\x02"  # uint32
            b"\xff\xff\xff\xff\xff\xff\xff\x03"  # uint64
            b"\xff\x01"  # int16
            b"\xff\xff\xff\x02"  # int32
            b"\xff\xff\xff\xff\xff\xff\xff\x03"  # int64
            b"\x3f\x80\x00\x00"  # float
            b"\x3f\xf0\x00\x00\x00\x00\x00\x00"  # double
        )
        stream = BytesIO(input_data)
        reader = BinaryReader(stream)

        expected_uint16 = 65281
        expected_uint32 = 4294967042
        expected_uint64 = 18446744073709551363
        expected_int16 = -255
        expected_int32 = -254
        expected_int64 = -253
        expected_float = 1.0
        expected_double = 1.0

        actual_uint16 = reader.read_uint16(big=True)
        actual_uint32 = reader.read_uint32(big=True)
        actual_uint64 = reader.read_uint64(big=True)
        actual_int16 = reader.read_int16(big=True)
        actual_int32 = reader.read_int32(big=True)
        actual_int64 = reader.read_int64(big=True)
        actual_float = reader.read_single(big=True)
        actual_double = reader.read_double(big=True)

        self.assertEqual(expected_uint16, actual_uint16)
        self.assertEqual(expected_uint32, actual_uint32)
        self.assertEqual(expected_uint64, actual_uint64)
        self.assertEqual(expected_int16, actual_int16)
        self.assertEqual(expected_int32, actual_int32)
        self.assertEqual(expected_int64, actual_int64)
        self.assertAlmostEqual(expected_float, actual_float, places=5)
        self.assertAlmostEqual(expected_double, actual_double, places=5)


class TestBinaryWriter(unittest.TestCase):
    """Test BinaryWriter ported from reone test/system/binarywriter.cpp"""

    def test_write_to_little_endian_stream(self):
        """Test writing various data types to little endian stream."""
        data = bytearray()
        writer = BinaryWriter.to_bytearray(data)
        expected_output = (
            b"\x40"  # byte
            b"A"  # char
            b"\x01\x00"  # uint16
            b"\x02\x00\x00\x00"  # uint32
            b"\xfd\xff"  # int16
            b"\xfc\xff\xff\xff"  # int32
            b"\xfb\xff\xff\xff\xff\xff\xff\xff"  # int64
            b"\x00\x00\x80\x3f"  # float
            b"AaBb\x00"  # string + cstring
            b"\x01\x02\x03\x04"  # bytes
        )

        writer.write_uint8(0x40)
        writer.write_string("A", encoding="ascii")
        writer.write_uint16(1)
        writer.write_uint32(2)
        writer.write_int16(-3)
        writer.write_int32(-4)
        writer.write_int64(-5)
        writer.write_single(1.0)
        writer.write_string("Aa", encoding="ascii")
        writer.write_terminated_string("Bb", encoding="ascii")
        writer.write_bytes(bytes([0x01, 0x02, 0x03, 0x04]))

        output = bytes(data)
        self.assertEqual(expected_output, output)

    def test_write_to_big_endian_stream(self):
        """Test writing various data types to big endian stream."""
        data = bytearray()
        writer = BinaryWriter.to_bytearray(data)
        expected_output = (
            b"\x40"  # byte
            b"A"  # char
            b"\x00\x01"  # uint16
            b"\x00\x00\x00\x02"  # uint32
            b"\xff\xfd"  # int16
            b"\xff\xff\xff\xfc"  # int32
            b"\xff\xff\xff\xff\xff\xff\xff\xfb"  # int64
            b"\x3f\x80\x00\x00"  # float
        )

        writer.write_uint8(0x40)
        writer.write_string("A", encoding="ascii")
        writer.write_uint16(1, big=True)
        writer.write_uint32(2, big=True)
        writer.write_int16(-3, big=True)
        writer.write_int32(-4, big=True)
        writer.write_int64(-5, big=True)
        writer.write_single(1.0, big=True)

        output = bytes(data)
        self.assertEqual(expected_output, output)


if __name__ == "__main__":
    unittest.main()
