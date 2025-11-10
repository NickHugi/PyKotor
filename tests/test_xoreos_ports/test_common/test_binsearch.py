"""
Port of xoreos-tools binary search tests to PyKotor.

Original file: vendor/xoreos-tools/tests/common/binsearch.cpp
Ported to test binary search algorithms using Python's bisect module.

This test suite validates:
- Binary search for existing elements
- Binary search for non-existing elements
- Binary search with custom key/value pairs
- Binary search edge cases

All test cases maintain 1:1 compatibility with the original xoreos-tools tests.
"""

from __future__ import annotations

import bisect
import unittest
from typing import NamedTuple, List, Optional


class BinSearchValue(NamedTuple):
    """Test structure equivalent to Common::BinSearchValue."""
    key: int
    value: int


class TestXoreosBinarySearch(unittest.TestCase):
    """Test binary search functionality ported from xoreos-tools."""

    def setUp(self):
        """Set up test data equivalent to the original xoreos tests."""
        # Test data equivalent to kTestBinSearch in original
        self.k_test_bin_search = [
            BinSearchValue(5, 23),
            BinSearchValue(6, 42),
            BinSearchValue(7, 60),
        ]

    def test_binary_search_positive(self):
        """Test binary search for existing element.
        
        Original xoreos test: GTEST_TEST(BinSearch, positive)
        """
        entry = self._binary_search(self.k_test_bin_search, 6)
        
        self.assertIsNotNone(entry)
        assert entry is not None
        self.assertEqual(entry.value, 42)

    def test_binary_search_negative(self):
        """Test binary search for non-existing element.
        
        Original xoreos test: GTEST_TEST(BinSearch, negative)
        """
        entry = self._binary_search(self.k_test_bin_search, 42)
        
        self.assertIsNone(entry)

    def test_binary_search_edge_cases(self):
        """Test binary search edge cases."""
        # Test search in empty array
        empty_array = []
        result = self._binary_search(empty_array, 5)
        self.assertIsNone(result)
        
        # Test search for first element
        result = self._binary_search(self.k_test_bin_search, 5)
        self.assertIsNotNone(result)
        assert result is not None, "Result is None"
        self.assertEqual(result.value, 23)
        
        # Test search for last element
        result = self._binary_search(self.k_test_bin_search, 7)
        self.assertIsNotNone(result)
        assert result is not None, "Result is None"
        self.assertEqual(result.value, 60)
        
        # Test search for element smaller than first
        result = self._binary_search(self.k_test_bin_search, 1)
        self.assertIsNone(result)
        
        # Test search for element larger than last
        result = self._binary_search(self.k_test_bin_search, 10)
        self.assertIsNone(result)

    def test_binary_search_single_element(self):
        """Test binary search with single element array."""
        single_element = [BinSearchValue(5, 100)]
        
        # Search for existing element
        result = self._binary_search(single_element, 5)
        self.assertIsNotNone(result)
        assert result is not None, "Result is None"
        self.assertEqual(result.value, 100)
        
        # Search for non-existing element
        result = self._binary_search(single_element, 3)
        self.assertIsNone(result)
        
        result = self._binary_search(single_element, 7)
        self.assertIsNone(result)

    def test_binary_search_large_dataset(self):
        """Test binary search with larger dataset."""
        # Create a larger sorted dataset
        large_dataset = [BinSearchValue(i, i * 10) for i in range(0, 100, 2)]
        
        # Test finding existing elements
        for i in range(0, 100, 2):
            result = self._binary_search(large_dataset, i)
            self.assertIsNotNone(result, f"Failed to find key {i}")
            assert result is not None, "Result is None"
            self.assertEqual(result.value, i * 10)
        
        # Test finding non-existing elements (odd numbers)
        for i in range(1, 100, 2):
            result = self._binary_search(large_dataset, i)
            self.assertIsNone(result, f"Unexpectedly found key {i}")

    def test_binary_search_duplicates(self):
        """Test binary search behavior with duplicate keys."""
        # Create dataset with duplicate keys
        duplicates = [
            BinSearchValue(5, 10),
            BinSearchValue(5, 20),
            BinSearchValue(6, 30),
            BinSearchValue(6, 40),
            BinSearchValue(7, 50),
        ]
        
        # Search should find one of the matching elements
        result = self._binary_search(duplicates, 5)
        self.assertIsNotNone(result)
        assert result is not None, "Result is None"
        self.assertIn(result.value, [10, 20])
        
        result = self._binary_search(duplicates, 6)
        self.assertIsNotNone(result)
        assert result is not None, "Result is None"
        self.assertIn(result.value, [30, 40])

    def _binary_search(self, array: List[BinSearchValue], key: int) -> Optional[BinSearchValue]:
        """Binary search implementation equivalent to Common::binarySearch.
        
        Args:
            array: Sorted array of BinSearchValue objects
            key: Key to search for
            
        Returns:
            BinSearchValue if found, None otherwise
        """
        if not array:
            return None
        
        # Extract keys for bisect search
        keys = [item.key for item in array]
        
        # Use bisect to find insertion point
        index = bisect.bisect_left(keys, key)
        
        # Check if we found the key
        if index < len(array) and array[index].key == key:
            return array[index]
        
        return None

    def _binary_search_alternative(self, array: List[BinSearchValue], key: int) -> Optional[BinSearchValue]:
        """Alternative binary search implementation using manual search.
        
        This provides a more direct port of the C++ binary search algorithm.
        """
        if not array:
            return None
        
        left = 0
        right = len(array) - 1
        
        while left <= right:
            mid = (left + right) // 2
            mid_key = array[mid].key
            
            if mid_key == key:
                return array[mid]
            elif mid_key < key:
                left = mid + 1
            else:
                right = mid - 1
        
        return None

    def test_compare_search_implementations(self):
        """Test that both search implementations give the same results."""
        test_cases = [5, 6, 7, 1, 10, 42]
        
        for key in test_cases:
            result1 = self._binary_search(self.k_test_bin_search, key)
            result2 = self._binary_search_alternative(self.k_test_bin_search, key)
            
            if result1 is None:
                self.assertIsNone(result2, f"Mismatch for key {key}")
            else:
                self.assertIsNotNone(result2, f"Mismatch for key {key}")
                assert result2 is not None, "Result2 is None"
                self.assertEqual(result1.key, result2.key, f"Key mismatch for {key}")
                self.assertEqual(result1.value, result2.value, f"Value mismatch for {key}")


if __name__ == "__main__":
    unittest.main()
