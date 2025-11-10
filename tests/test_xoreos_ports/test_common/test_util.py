"""
Port of xoreos-tools utility template tests to PyKotor.

Original file: vendor/xoreos-tools/tests/common/util.cpp
Ported to test utility functions using Python's built-in functions and operators.

This test suite validates:
- Absolute value calculations for integers, floats, and doubles
- Minimum value selection for various numeric types
- Maximum value selection for various numeric types
- Value clipping/clamping operations
- Power of 2 detection
- Bit manipulation utilities
- Numeric utility functions

All test cases maintain 1:1 compatibility with the original xoreos-tools tests.
"""

from __future__ import annotations

import unittest
from typing import TypeVar

T = TypeVar('T', int, float)


class TestXoreosUtilityFunctions(unittest.TestCase):
    """Test utility template functions ported from xoreos-tools."""

    def test_abs_int(self):
        """Test absolute value for integers.
        
        Original xoreos test: GTEST_TEST(Util, ABS)
        Tests equivalent functionality to ABS<int>() template.
        """
        self.assertEqual(abs(23), 23)
        self.assertEqual(abs(-23), 23)

    def test_min_int(self):
        """Test minimum value selection for integers.
        
        Original xoreos test: GTEST_TEST(Util, MIN)
        Tests equivalent functionality to MIN<int>() template.
        """
        self.assertEqual(min(-23, -5), -23)
        self.assertEqual(min(23, 5), 5)
        self.assertEqual(min(-23, 23), -23)

    def test_max_int(self):
        """Test maximum value selection for integers.
        
        Original xoreos test: GTEST_TEST(Util, MAX)
        Tests equivalent functionality to MAX<int>() template.
        """
        self.assertEqual(max(-23, -5), -5)
        self.assertEqual(max(23, 5), 23)
        self.assertEqual(max(-23, 23), 23)

    def test_clip_int(self):
        """Test value clipping for integers.
        
        Original xoreos test: GTEST_TEST(Util, CLIP)
        Tests equivalent functionality to CLIP<int>() template.
        """
        self.assertEqual(self._clip(23, -5, 5), 5)
        self.assertEqual(self._clip(-23, -5, 5), -5)
        self.assertEqual(self._clip(-1, -5, 5), -1)
        self.assertEqual(self._clip(1, -5, 5), 1)

    def test_abs_float(self):
        """Test absolute value for floats.
        
        Original xoreos test: GTEST_TEST(Util, ABSFloat)
        Tests equivalent functionality to ABS<float>() template.
        """
        self.assertEqual(abs(23.0), 23.0)
        self.assertEqual(abs(-23.0), 23.0)

    def test_min_float(self):
        """Test minimum value selection for floats.
        
        Original xoreos test: GTEST_TEST(Util, MINFloat)
        Tests equivalent functionality to MIN<float>() template.
        """
        self.assertEqual(min(-23.0, -5.0), -23.0)
        self.assertEqual(min(23.0, 5.0), 5.0)
        self.assertEqual(min(-23.0, 23.0), -23.0)

    def test_max_float(self):
        """Test maximum value selection for floats.
        
        Original xoreos test: GTEST_TEST(Util, MAXFloat)
        Tests equivalent functionality to MAX<float>() template.
        """
        self.assertEqual(max(-23.0, -5.0), -5.0)
        self.assertEqual(max(23.0, 5.0), 23.0)
        self.assertEqual(max(-23.0, 23.0), 23.0)

    def test_abs_double(self):
        """Test absolute value for doubles.
        
        Original xoreos test: GTEST_TEST(Util, ABSDouble)
        Tests equivalent functionality to ABS<double>() template.
        Note: In Python, float is equivalent to C++ double.
        """
        self.assertEqual(abs(23.0), 23.0)
        self.assertEqual(abs(-23.0), 23.0)

    def test_min_double(self):
        """Test minimum value selection for doubles.
        
        Original xoreos test: GTEST_TEST(Util, MINDouble)
        Tests equivalent functionality to MIN<double>() template.
        """
        self.assertEqual(min(-23.0, -5.0), -23.0)
        self.assertEqual(min(23.0, 5.0), 5.0)
        self.assertEqual(min(-23.0, 23.0), -23.0)

    def test_max_double(self):
        """Test maximum value selection for doubles.
        
        Original xoreos test: GTEST_TEST(Util, MAXDouble)
        Tests equivalent functionality to MAX<double>() template.
        """
        self.assertEqual(max(-23.0, -5.0), -5.0)
        self.assertEqual(max(23.0, 5.0), 23.0)
        self.assertEqual(max(-23.0, 23.0), 23.0)

    def test_is_power_of_2(self):
        """Test power of 2 detection.
        
        Original xoreos test: GTEST_TEST(Util, ISPOWER2)
        Tests equivalent functionality to ISPOWER2() macro.
        """
        # Test positive powers of 2
        self.assertTrue(self._is_power_of_2(2))
        self.assertTrue(self._is_power_of_2(4))
        self.assertTrue(self._is_power_of_2(8))
        
        # Test negative numbers (should be false)
        self.assertFalse(self._is_power_of_2(-2))
        self.assertFalse(self._is_power_of_2(-4))
        self.assertFalse(self._is_power_of_2(-8))
        
        # Test edge cases and non-powers of 2
        self.assertFalse(self._is_power_of_2(0))
        self.assertFalse(self._is_power_of_2(3))
        self.assertFalse(self._is_power_of_2(5))
        self.assertFalse(self._is_power_of_2(-3))
        self.assertFalse(self._is_power_of_2(-5))

    def test_next_power_of_2(self):
        """Test next power of 2 calculation.
        
        Original xoreos test: GTEST_TEST(Util, NEXTPOWER2)
        Tests equivalent functionality to NEXTPOWER2() macro.
        """
        self.assertEqual(self._next_power_of_2(1), 1)
        self.assertEqual(self._next_power_of_2(2), 2)
        self.assertEqual(self._next_power_of_2(3), 4)
        self.assertEqual(self._next_power_of_2(4), 4)
        self.assertEqual(self._next_power_of_2(5), 8)
        self.assertEqual(self._next_power_of_2(8), 8)
        self.assertEqual(self._next_power_of_2(9), 16)
        self.assertEqual(self._next_power_of_2(15), 16)
        self.assertEqual(self._next_power_of_2(16), 16)
        self.assertEqual(self._next_power_of_2(17), 32)

    def test_swap_values(self):
        """Test value swapping functionality.
        
        Original xoreos test: GTEST_TEST(Util, SWAP)
        Tests equivalent functionality to SWAP() macro.
        """
        # Test integer swapping
        a, b = 23, 42
        a, b = b, a  # Python tuple swap equivalent to SWAP(a, b)
        self.assertEqual(a, 42)
        self.assertEqual(b, 23)
        
        # Test float swapping
        x, y = 1.5, 2.5
        x, y = y, x
        self.assertEqual(x, 2.5)
        self.assertEqual(y, 1.5)

    def test_arraysize_equivalent(self):
        """Test array size calculation.
        
        Original xoreos test: GTEST_TEST(Util, ARRAYSIZE)
        Tests equivalent functionality to ARRAYSIZE() macro.
        """
        # Test with various array types
        int_array = [1, 2, 3, 4, 5]
        self.assertEqual(len(int_array), 5)
        
        string_array = ["a", "b", "c"]
        self.assertEqual(len(string_array), 3)
        
        empty_array = []
        self.assertEqual(len(empty_array), 0)

    def test_bit_manipulation(self):
        """Test bit manipulation utilities.
        
        Tests equivalent functionality to various bit manipulation macros from xoreos-tools.
        """
        # Test bit setting
        value = 0
        value |= (1 << 3)  # Set bit 3
        self.assertEqual(value, 8)
        
        # Test bit clearing
        value &= ~(1 << 3)  # Clear bit 3
        self.assertEqual(value, 0)
        
        # Test bit testing
        value = 8  # Bit 3 is set
        self.assertTrue((value & (1 << 3)) != 0)  # Test bit 3
        self.assertFalse((value & (1 << 2)) != 0)  # Test bit 2

    def _clip(self, value: T, min_val: T, max_val: T) -> T:
        """Clip a value to the specified range.
        
        Equivalent to CLIP() macro from xoreos-tools.
        """
        return max(min_val, min(value, max_val))

    def _is_power_of_2(self, value: int) -> bool:
        """Check if a value is a power of 2.
        
        Equivalent to ISPOWER2() macro from xoreos-tools.
        """
        return value > 0 and (value & (value - 1)) == 0

    def _next_power_of_2(self, value: int) -> int:
        """Calculate the next power of 2 greater than or equal to the given value.
        
        Equivalent to NEXTPOWER2() macro from xoreos-tools.
        """
        if value <= 1:
            return 1
        
        # Use bit manipulation to find next power of 2
        value -= 1
        value |= value >> 1
        value |= value >> 2
        value |= value >> 4
        value |= value >> 8
        value |= value >> 16
        if value.bit_length() > 32:  # Handle 64-bit case
            value |= value >> 32
        value += 1
        
        return value


if __name__ == "__main__":
    unittest.main()
