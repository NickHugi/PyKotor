"""
Port of xoreos-tools mathematical helper tests to PyKotor.

Original file: vendor/xoreos-tools/tests/common/maths.cpp
Ported to test mathematical utility functions using Python's math module.

This test suite validates:
- Integer logarithm base 2 calculations
- Pi constant accuracy
- Degree to radian conversions
- Radian to degree conversions
- Mathematical precision and accuracy

All test cases maintain 1:1 compatibility with the original xoreos-tools tests.
"""

from __future__ import annotations

import math
import unittest


class TestXoreosMathFunctions(unittest.TestCase):
    """Test mathematical utility functions ported from xoreos-tools."""

    def test_int_log2(self):
        """Test integer logarithm base 2 calculation.
        
        Original xoreos test: GTEST_TEST(Maths, intLog2)
        Tests equivalent functionality to Common::intLog2().
        """
        # Test exact powers of 2
        self.assertEqual(self._int_log2(2), 1)
        self.assertEqual(self._int_log2(4), 2)
        self.assertEqual(self._int_log2(8), 3)
        self.assertEqual(self._int_log2(16), 4)
        self.assertEqual(self._int_log2(32), 5)
        
        # Test edge case: log2(0) should return -1
        self.assertEqual(self._int_log2(0), -1)
        
        # Test non-powers of 2 (should return floor of log2)
        self.assertEqual(self._int_log2(3), 1)   # floor(log2(3)) = floor(1.58) = 1
        self.assertEqual(self._int_log2(5), 2)   # floor(log2(5)) = floor(2.32) = 2
        self.assertEqual(self._int_log2(10), 3)  # floor(log2(10)) = floor(3.32) = 3

    def test_pi_constant(self):
        """Test pi constant accuracy.
        
        Original xoreos test: GTEST_TEST(Maths, pi)
        Tests that Python's math.pi matches the expected precision.
        """
        expected_pi = 3.14159265358979323846
        self.assertAlmostEqual(math.pi, expected_pi, places=15)

    def test_deg2rad(self):
        """Test degree to radian conversion.
        
        Original xoreos test: GTEST_TEST(Maths, deg2rad)
        Tests equivalent functionality to Common::deg2rad().
        """
        # Test common angle conversions
        self.assertAlmostEqual(self._deg2rad(0.0), 0.0, places=6)
        self.assertAlmostEqual(self._deg2rad(180.0), math.pi, places=6)
        self.assertAlmostEqual(self._deg2rad(-180.0), -math.pi, places=6)
        self.assertAlmostEqual(self._deg2rad(90.0), math.pi / 2.0, places=6)
        self.assertAlmostEqual(self._deg2rad(-90.0), -math.pi / 2.0, places=6)
        self.assertAlmostEqual(self._deg2rad(360.0), math.pi * 2.0, places=6)
        self.assertAlmostEqual(self._deg2rad(-360.0), -math.pi * 2.0, places=6)

    def test_rad2deg(self):
        """Test radian to degree conversion.
        
        Original xoreos test: GTEST_TEST(Maths, rad2deg)
        Tests equivalent functionality to Common::rad2deg().
        """
        # Test common angle conversions
        self.assertAlmostEqual(self._rad2deg(0.0), 0.0, places=6)
        self.assertAlmostEqual(self._rad2deg(math.pi), 180.0, places=6)
        self.assertAlmostEqual(self._rad2deg(-math.pi), -180.0, places=6)
        self.assertAlmostEqual(self._rad2deg(math.pi / 2.0), 90.0, places=6)
        self.assertAlmostEqual(self._rad2deg(-math.pi / 2.0), -90.0, places=6)
        self.assertAlmostEqual(self._rad2deg(math.pi * 2.0), 360.0, places=6)
        self.assertAlmostEqual(self._rad2deg(-math.pi * 2.0), -360.0, places=6)

    def _int_log2(self, value: int) -> int:
        """Calculate integer logarithm base 2.
        
        Equivalent to Common::intLog2() from xoreos-tools.
        Returns -1 for input of 0, otherwise returns floor(log2(value)).
        """
        if value <= 0:
            return -1
        
        # Calculate floor of log2
        return int(math.log2(value))

    def _deg2rad(self, degrees: float) -> float:
        """Convert degrees to radians.
        
        Equivalent to Common::deg2rad() from xoreos-tools.
        """
        return math.radians(degrees)

    def _rad2deg(self, radians: float) -> float:
        """Convert radians to degrees.
        
        Equivalent to Common::rad2deg() from xoreos-tools.
        """
        return math.degrees(radians)


if __name__ == "__main__":
    unittest.main()
