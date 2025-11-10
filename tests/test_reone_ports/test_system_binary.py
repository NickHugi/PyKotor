"""
Port of reone system binary I/O tests to PyKotor.

Original files: vendor/reone/test/system/binaryreader.cpp, binarywriter.cpp
Ported to test PyKotor's BinaryReader and BinaryWriter classes.
"""

from __future__ import annotations

import unittest
from io import BytesIO

from pykotor.common.stream import BinaryReader, BinaryWriter


class TestBinaryReader(unittest.TestCase):
    """Test BinaryReader ported from reone test/system/binaryreader.cpp"""

    def test_seek_ignore_and_tell_in_little_endian_stream(self):
        """Test seeking, skipping bytes, and telling position in little endian stream."""
        input_data = b'Hello, world!\x00'
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
            b'\xff'  # byte
            b'\x01\xff'  # uint16
            b'\x02\xff\xff\xff'  # uint32
            b'\x03\xff\xff\xff\xff\xff\xff\xff'  # uint64
            b'\x01\xff'  # int16
            b'\x02\xff\xff\xff'  # int32
            b'\x03\xff\xff\xff\xff\xff\xff\xff'  # int64
            b'\x00\x00\x80\x3f'  # float
            b'\x00\x00\x00\x00\x00\x00\xf0\x3f'  # double
            b'Hello, world!'  # string
            b'Hello, world!\x00'  # cstring
            b'\x01\x02\x03\x04'  # bytes
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
        actual_cstr = reader.read_terminated_string(128)
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
            b'\xff\x01'  # uint16
            b'\xff\xff\xff\x02'  # uint32
            b'\xff\xff\xff\xff\xff\xff\xff\x03'  # uint64
            b'\xff\x01'  # int16
            b'\xff\xff\xff\x02'  # int32
            b'\xff\xff\xff\xff\xff\xff\xff\x03'  # int64
            b'\x3f\x80\x00\x00'  # float
            b'\x3f\xf0\x00\x00\x00\x00\x00\x00'  # double
        )
        stream = BytesIO(input_data)
        reader = BinaryReader(stream, big_endian=True)

        expected_uint16 = 65281
        expected_uint32 = 4294967042
        expected_uint64 = 18446744073709551363
        expected_int16 = -255
        expected_int32 = -254
        expected_int64 = -253
        expected_float = 1.0
        expected_double = 1.0

        actual_uint16 = reader.read_uint16()
        actual_uint32 = reader.read_uint32()
        actual_uint64 = reader.read_uint64()
        actual_int16 = reader.read_int16()
        actual_int32 = reader.read_int32()
        actual_int64 = reader.read_int64()
        actual_float = reader.read_single()
        actual_double = reader.read_double()

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
            b'\x40'  # byte
            b'A'  # char
            b'\x01\x00'  # uint16
            b'\x02\x00\x00\x00'  # uint32
            b'\xfd\xff'  # int16
            b'\xfc\xff\xff\xff'  # int32
            b'\xfb\xff\xff\xff\xff\xff\xff\xff'  # int64
            b'\x00\x00\x80\x3f'  # float
            b'AaBb\x00'  # string + cstring
            b'\x01\x02\x03\x04'  # bytes
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
            b'\x40'  # byte
            b'A'  # char
            b'\x00\x01'  # uint16
            b'\x00\x00\x00\x02'  # uint32
            b'\xff\xfd'  # int16
            b'\xff\xff\xff\xfc'  # int32
            b'\xff\xff\xff\xff\xff\xff\xff\xfb'  # int64
            b'\x3f\x80\x00\x00'  # float
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

