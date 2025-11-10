"""
Port of xoreos-tools MD5 digest tests to PyKotor.

Original file: vendor/xoreos-tools/tests/common/md5.cpp
Ported to test MD5 hash functions using Python's hashlib.

This test suite validates:
- MD5 hashing of strings
- MD5 hashing of binary data
- MD5 hashing of streams
- MD5 hashing of byte arrays
- MD5 digest comparison utilities
- MD5 digest validation

All test cases maintain 1:1 compatibility with the original xoreos-tools tests.
"""

from __future__ import annotations

import hashlib
import io
import unittest
from typing import List


class TestXoreosMD5Functions(unittest.TestCase):
    """Test MD5 digest functions ported from xoreos-tools."""

    def setUp(self):
        """Set up test data equivalent to the original xoreos tests."""
        self.k_string = "Foobar"
        self.k_data = bytes([0x12, 0x34, 0x56, 0x78, 0x90, 0xAB, 0xCD, 0xEF])
        
        # Expected MD5 digests from original xoreos tests
        self.k_digest_string = bytes([
            0x89, 0xD5, 0x73, 0x9B, 0xAA, 0xBB, 0xBE, 0x65,
            0xBE, 0x35, 0xCB, 0xE6, 0x1C, 0x88, 0xE0, 0x6D
        ])
        self.k_digest_data = bytes([
            0x79, 0x9D, 0x4F, 0x0B, 0xEC, 0x27, 0xAF, 0xF8,
            0x9D, 0xE3, 0x0B, 0x35, 0xE3, 0xCA, 0x43, 0x32
        ])

    def test_hash_string(self):
        """Test MD5 hashing of strings.
        
        Original xoreos test: GTEST_TEST(MD5, hashString)
        """
        digest = self._hash_md5_string(self.k_string)
        self._compare_data(digest, self.k_digest_string)

    def test_hash_data(self):
        """Test MD5 hashing of binary data.
        
        Original xoreos test: GTEST_TEST(MD5, hashData)
        """
        digest = self._hash_md5_data(self.k_data)
        self._compare_data(digest, self.k_digest_data)

    def test_hash_stream(self):
        """Test MD5 hashing of streams.
        
        Original xoreos test: GTEST_TEST(MD5, hashStream)
        """
        stream = io.BytesIO(self.k_data)
        digest = self._hash_md5_stream(stream)
        self._compare_data(digest, self.k_digest_data)

    def test_hash_vector(self):
        """Test MD5 hashing of byte arrays.
        
        Original xoreos test: GTEST_TEST(MD5, hashVector)
        """
        data_list = list(self.k_data)
        digest = self._hash_md5_list(data_list)
        self._compare_data(digest, self.k_digest_data)

    def test_compare_string(self):
        """Test MD5 digest comparison for strings.
        
        Original xoreos test: GTEST_TEST(MD5, compareString)
        """
        digest = list(self.k_digest_string)
        result = self._compare_md5_digest_string(self.k_string, digest)
        self.assertTrue(result)

    def test_compare_data(self):
        """Test MD5 digest comparison for binary data.
        
        Original xoreos test: GTEST_TEST(MD5, compareData)
        """
        digest = list(self.k_digest_data)
        result = self._compare_md5_digest_data(self.k_data, digest)
        self.assertTrue(result)

    def test_compare_stream(self):
        """Test MD5 digest comparison for streams.
        
        Original xoreos test: GTEST_TEST(MD5, compareStream)
        """
        stream = io.BytesIO(self.k_data)
        digest = list(self.k_digest_data)
        result = self._compare_md5_digest_stream(stream, digest)
        self.assertTrue(result)

    def test_compare_vector(self):
        """Test MD5 digest comparison for byte arrays.
        
        Original xoreos test: GTEST_TEST(MD5, compareVector)
        """
        data_list = list(self.k_data)
        digest = list(self.k_digest_data)
        result = self._compare_md5_digest_list(data_list, digest)
        self.assertTrue(result)

    def test_digest_string_representation(self):
        """Test MD5 digest string representation.
        
        Tests the ability to convert MD5 digests to/from string representations.
        """
        # Test string digest
        digest_bytes = self._hash_md5_string(self.k_string)
        digest_hex = digest_bytes.hex()
        
        # Verify we can reconstruct the digest
        reconstructed = bytes.fromhex(digest_hex)
        self.assertEqual(digest_bytes, reconstructed)
        
        # Test data digest
        digest_bytes = self._hash_md5_data(self.k_data)
        digest_hex = digest_bytes.hex()
        reconstructed = bytes.fromhex(digest_hex)
        self.assertEqual(digest_bytes, reconstructed)

    def test_empty_data_hash(self):
        """Test MD5 hashing of empty data."""
        empty_string = ""
        empty_data = b""
        
        # Hash empty string
        digest_string = self._hash_md5_string(empty_string)
        self.assertEqual(len(digest_string), 16)  # MD5 always produces 16 bytes
        
        # Hash empty data
        digest_data = self._hash_md5_data(empty_data)
        self.assertEqual(len(digest_data), 16)
        
        # Empty string and empty data should produce the same hash
        self.assertEqual(digest_string, digest_data)

    def test_large_data_hash(self):
        """Test MD5 hashing of larger data sets."""
        # Create a larger data set
        large_data = bytes(range(256)) * 10  # 2560 bytes
        digest = self._hash_md5_data(large_data)
        
        # Verify digest length
        self.assertEqual(len(digest), 16)
        
        # Verify consistency - hashing the same data twice should give same result
        digest2 = self._hash_md5_data(large_data)
        self.assertEqual(digest, digest2)

    # --- Helper Methods ---

    def _hash_md5_string(self, string: str) -> bytes:
        """Hash a string using MD5.
        
        Equivalent to Common::hashMD5(string, digest).
        """
        return hashlib.md5(string.encode('utf-8')).digest()

    def _hash_md5_data(self, data: bytes) -> bytes:
        """Hash binary data using MD5.
        
        Equivalent to Common::hashMD5(data, length, digest).
        """
        return hashlib.md5(data).digest()

    def _hash_md5_stream(self, stream: io.BytesIO) -> bytes:
        """Hash stream data using MD5.
        
        Equivalent to Common::hashMD5(stream, digest).
        """
        stream.seek(0)  # Ensure we read from the beginning
        data = stream.read()
        return hashlib.md5(data).digest()

    def _hash_md5_list(self, data_list: List[int]) -> bytes:
        """Hash a list of bytes using MD5.
        
        Equivalent to Common::hashMD5(vector, digest).
        """
        data = bytes(data_list)
        return hashlib.md5(data).digest()

    def _compare_md5_digest_string(self, string: str, expected_digest: List[int]) -> bool:
        """Compare MD5 digest of string with expected digest.
        
        Equivalent to Common::compareMD5Digest(string, digest).
        """
        actual_digest = self._hash_md5_string(string)
        expected_bytes = bytes(expected_digest)
        return actual_digest == expected_bytes

    def _compare_md5_digest_data(self, data: bytes, expected_digest: List[int]) -> bool:
        """Compare MD5 digest of data with expected digest.
        
        Equivalent to Common::compareMD5Digest(data, length, digest).
        """
        actual_digest = self._hash_md5_data(data)
        expected_bytes = bytes(expected_digest)
        return actual_digest == expected_bytes

    def _compare_md5_digest_stream(self, stream: io.BytesIO, expected_digest: List[int]) -> bool:
        """Compare MD5 digest of stream with expected digest.
        
        Equivalent to Common::compareMD5Digest(stream, digest).
        """
        actual_digest = self._hash_md5_stream(stream)
        expected_bytes = bytes(expected_digest)
        return actual_digest == expected_bytes

    def _compare_md5_digest_list(self, data_list: List[int], expected_digest: List[int]) -> bool:
        """Compare MD5 digest of list with expected digest.
        
        Equivalent to Common::compareMD5Digest(vector, digest).
        """
        actual_digest = self._hash_md5_list(data_list)
        expected_bytes = bytes(expected_digest)
        return actual_digest == expected_bytes

    def _compare_data(self, actual: bytes, expected: bytes):
        """Compare two byte sequences with detailed error reporting."""
        self.assertEqual(len(actual), len(expected))
        for i, (actual_byte, expected_byte) in enumerate(zip(actual, expected)):
            self.assertEqual(actual_byte, expected_byte, f"At index {i}")


if __name__ == "__main__":
    unittest.main()
