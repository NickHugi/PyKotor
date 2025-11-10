"""
Port of xoreos-tools hash function tests to PyKotor.

Original file: vendor/xoreos-tools/tests/common/hash.cpp
Ported to test hash functions using Python's hashlib and custom implementations.

This test suite validates:
- DJB2 hash algorithm
- FNV32 hash algorithm
- FNV64 hash algorithm
- CRC32 hash algorithm
- Hash functions with different encodings (UTF-16LE)
- Hash formatting utilities

All test cases maintain 1:1 compatibility with the original xoreos-tools tests.
"""

from __future__ import annotations

import hashlib
import unittest
import zlib


class TestXoreosHashFunctions(unittest.TestCase):
    """Test hash utility functions ported from xoreos-tools."""

    def setUp(self):
        """Set up test data."""
        self.k_string = "Foobar"

    def test_djb2_hash(self):
        """Test DJB2 hash algorithm.
        
        Original xoreos test: GTEST_TEST(Hash, DJB2)
        """
        expected_hash = 0xB33F4C9E
        actual_hash = self._djb2_hash(self.k_string)
        self.assertEqual(actual_hash, expected_hash)

    def test_fnv32_hash(self):
        """Test FNV32 hash algorithm.
        
        Original xoreos test: GTEST_TEST(Hash, FNV32)
        """
        expected_hash = 0xED18E8C2
        actual_hash = self._fnv32_hash(self.k_string)
        self.assertEqual(actual_hash, expected_hash)

    def test_fnv64_hash(self):
        """Test FNV64 hash algorithm.
        
        Original xoreos test: GTEST_TEST(Hash, FNV64)
        """
        expected_hash = 0x744E9FFF32CA0A22
        actual_hash = self._fnv64_hash(self.k_string)
        self.assertEqual(actual_hash, expected_hash)

    def test_crc32_hash(self):
        """Test CRC32 hash algorithm.
        
        Original xoreos test: GTEST_TEST(Hash, CRC32)
        """
        expected_hash = 0x995A1AA3
        actual_hash = self._crc32_hash(self.k_string)
        self.assertEqual(actual_hash, expected_hash)

    def test_djb2_hash_utf16le(self):
        """Test DJB2 hash with UTF-16LE encoding.
        
        Original xoreos test: GTEST_TEST(Hash, DJB2Encoding)
        """
        expected_hash = 0xD11D54FE
        # Convert string to UTF-16LE bytes
        utf16le_bytes = self.k_string.encode('utf-16le')
        actual_hash = self._djb2_hash_bytes(utf16le_bytes)
        self.assertEqual(actual_hash, expected_hash)

    def test_fnv32_hash_utf16le(self):
        """Test FNV32 hash with UTF-16LE encoding.
        
        Original xoreos test: GTEST_TEST(Hash, FNV32Encoding)
        """
        expected_hash = 0xCE5005F0
        utf16le_bytes = self.k_string.encode('utf-16le')
        actual_hash = self._fnv32_hash_bytes(utf16le_bytes)
        self.assertEqual(actual_hash, expected_hash)

    def test_fnv64_hash_utf16le(self):
        """Test FNV64 hash with UTF-16LE encoding.
        
        Original xoreos test: GTEST_TEST(Hash, FNV64Encoding)
        """
        expected_hash = 0xA73456F669A95770
        utf16le_bytes = self.k_string.encode('utf-16le')
        actual_hash = self._fnv64_hash_bytes(utf16le_bytes)
        self.assertEqual(actual_hash, expected_hash)

    def test_crc32_hash_utf16le(self):
        """Test CRC32 hash with UTF-16LE encoding.
        
        Original xoreos test: GTEST_TEST(Hash, CRC32Encoding)
        """
        expected_hash = 0x56031CD6
        utf16le_bytes = self.k_string.encode('utf-16le')
        actual_hash = self._crc32_hash_bytes(utf16le_bytes)
        self.assertEqual(actual_hash, expected_hash)

    def test_format_hash(self):
        """Test hash formatting utility.
        
        Original xoreos test: GTEST_TEST(Hash, formatHash)
        """
        hash_value = 0x1234567890ABCDEF
        expected_format = "0x1234567890ABCDEF"
        actual_format = self._format_hash(hash_value)
        self.assertEqual(actual_format, expected_format)

    def _djb2_hash(self, string: str) -> int:
        """DJB2 hash algorithm implementation.
        
        Equivalent to Common::hashString with kHashDJB2.
        """
        return self._djb2_hash_bytes(string.encode('utf-8'))

    def _djb2_hash_bytes(self, data: bytes) -> int:
        """DJB2 hash algorithm for byte data."""
        hash_value = 5381
        for byte in data:
            hash_value = ((hash_value << 5) + hash_value + byte) & 0xFFFFFFFF
        return hash_value

    def _fnv32_hash(self, string: str) -> int:
        """FNV32 hash algorithm implementation.
        
        Equivalent to Common::hashString with kHashFNV32.
        """
        return self._fnv32_hash_bytes(string.encode('utf-8'))

    def _fnv32_hash_bytes(self, data: bytes) -> int:
        """FNV32 hash algorithm for byte data."""
        # FNV-1a 32-bit constants
        FNV_OFFSET_BASIS_32 = 0x811C9DC5
        FNV_PRIME_32 = 0x01000193
        
        hash_value = FNV_OFFSET_BASIS_32
        for byte in data:
            hash_value ^= byte
            hash_value = (hash_value * FNV_PRIME_32) & 0xFFFFFFFF
        return hash_value

    def _fnv64_hash(self, string: str) -> int:
        """FNV64 hash algorithm implementation.
        
        Equivalent to Common::hashString with kHashFNV64.
        """
        return self._fnv64_hash_bytes(string.encode('utf-8'))

    def _fnv64_hash_bytes(self, data: bytes) -> int:
        """FNV64 hash algorithm for byte data."""
        # FNV-1a 64-bit constants
        FNV_OFFSET_BASIS_64 = 0xCBF29CE484222325
        FNV_PRIME_64 = 0x100000001B3
        
        hash_value = FNV_OFFSET_BASIS_64
        for byte in data:
            hash_value ^= byte
            hash_value = (hash_value * FNV_PRIME_64) & 0xFFFFFFFFFFFFFFFF
        return hash_value

    def _crc32_hash(self, string: str) -> int:
        """CRC32 hash algorithm implementation.
        
        Equivalent to Common::hashString with kHashCRC32.
        """
        return self._crc32_hash_bytes(string.encode('utf-8'))

    def _crc32_hash_bytes(self, data: bytes) -> int:
        """CRC32 hash algorithm for byte data."""
        # Python's zlib.crc32 returns a signed integer, we need unsigned
        crc = zlib.crc32(data) & 0xFFFFFFFF
        return crc

    def _format_hash(self, hash_value: int) -> str:
        """Format hash value as hexadecimal string.
        
        Equivalent to Common::formatHash.
        """
        return f"0x{hash_value:X}"


if __name__ == "__main__":
    unittest.main()
