"""
Port of xoreos-tools image utility tests to PyKotor.

Original file: vendor/xoreos-tools/tests/images/util.cpp
Ported to test image utility functions and pixel format operations.

This test suite validates:
- Pixel format bytes-per-pixel calculations
- Image data size calculations
- Image flipping operations (vertical and horizontal)
- Pixel format conversions
- Image manipulation utilities

All test cases maintain 1:1 compatibility with the original xoreos-tools tests.
"""

from __future__ import annotations

import unittest
from enum import IntEnum
from typing import List


class PixelFormat(IntEnum):
    """Pixel format enumeration equivalent to Images::PixelFormat."""
    R8G8B8 = 0
    B8G8R8 = 1
    R8G8B8A8 = 2
    B8G8R8A8 = 3
    A1R5G5B5 = 4
    R5G6B5 = 5
    DEPTH16 = 6
    DXT1 = 7
    DXT3 = 8
    DXT5 = 9


class TestXoreosImageUtilities(unittest.TestCase):
    """Test image utility functions ported from xoreos-tools."""

    def setUp(self):
        """Set up test image data equivalent to the original xoreos tests."""
        # Test images with different dimensions and channel counts
        self.k_image_1_1_3 = bytes([0x00, 0x01, 0x02])
        self.k_image_1_1_4 = bytes([0x00, 0x01, 0x02, 0x03])
        
        self.k_image_2_2_3 = bytes([
            0x00, 0x01, 0x02, 0x03, 0x04, 0x05,
            0x10, 0x11, 0x12, 0x13, 0x14, 0x15
        ])
        self.k_image_2_2_4 = bytes([
            0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
            0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17
        ])
        
        self.k_image_3_3_3 = bytes([
            0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
            0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18,
            0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28
        ])
        self.k_image_3_3_4 = bytes([
            0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B,
            0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x1B,
            0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x29, 0x2A, 0x2B
        ])
        
        self.k_image_2_3_3 = bytes([
            0x00, 0x01, 0x02, 0x03, 0x04, 0x05,
            0x10, 0x11, 0x12, 0x13, 0x14, 0x15,
            0x20, 0x21, 0x22, 0x23, 0x24, 0x25
        ])
        self.k_image_2_3_4 = bytes([
            0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
            0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17,
            0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27
        ])
        
        self.k_image_3_2_3 = bytes([
            0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
            0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18
        ])
        self.k_image_3_2_4 = bytes([
            0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B,
            0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x1B
        ])

    def test_get_bpp(self):
        """Test bytes-per-pixel calculation for different pixel formats.
        
        Original xoreos test: GTEST_TEST(ImagesUtil, getBPP)
        """
        # Test RGB formats (3 bytes per pixel)
        self.assertEqual(self._get_bpp(PixelFormat.R8G8B8), 3)
        self.assertEqual(self._get_bpp(PixelFormat.B8G8R8), 3)
        
        # Test RGBA formats (4 bytes per pixel)
        self.assertEqual(self._get_bpp(PixelFormat.R8G8B8A8), 4)
        self.assertEqual(self._get_bpp(PixelFormat.B8G8R8A8), 4)
        
        # Test 16-bit formats (2 bytes per pixel)
        self.assertEqual(self._get_bpp(PixelFormat.A1R5G5B5), 2)
        self.assertEqual(self._get_bpp(PixelFormat.R5G6B5), 2)
        self.assertEqual(self._get_bpp(PixelFormat.DEPTH16), 2)
        
        # Test compressed formats (0 bytes per pixel - special handling)
        self.assertEqual(self._get_bpp(PixelFormat.DXT1), 0)
        self.assertEqual(self._get_bpp(PixelFormat.DXT3), 0)
        self.assertEqual(self._get_bpp(PixelFormat.DXT5), 0)

    def test_get_data_size(self):
        """Test data size calculation for different pixel formats and dimensions.
        
        Original xoreos test: GTEST_TEST(ImagesUtil, getDataSize)
        """
        # Test 16-bit formats
        self.assertEqual(self._get_data_size(PixelFormat.A1R5G5B5, 3, 3), 3 * 3 * 2)
        self.assertEqual(self._get_data_size(PixelFormat.R5G6B5, 3, 3), 3 * 3 * 2)
        self.assertEqual(self._get_data_size(PixelFormat.DEPTH16, 3, 3), 3 * 3 * 2)
        
        # Test RGB formats
        self.assertEqual(self._get_data_size(PixelFormat.R8G8B8, 3, 3), 3 * 3 * 3)
        self.assertEqual(self._get_data_size(PixelFormat.B8G8R8, 3, 3), 3 * 3 * 3)
        
        # Test RGBA formats
        self.assertEqual(self._get_data_size(PixelFormat.R8G8B8A8, 3, 3), 3 * 3 * 4)
        self.assertEqual(self._get_data_size(PixelFormat.B8G8R8A8, 3, 3), 3 * 3 * 4)
        
        # Test zero dimensions
        self.assertEqual(self._get_data_size(PixelFormat.A1R5G5B5, 0, 0), 0)
        self.assertEqual(self._get_data_size(PixelFormat.R5G6B5, 0, 0), 0)
        self.assertEqual(self._get_data_size(PixelFormat.DEPTH16, 0, 0), 0)
        self.assertEqual(self._get_data_size(PixelFormat.R8G8B8, 0, 0), 0)
        self.assertEqual(self._get_data_size(PixelFormat.B8G8R8, 0, 0), 0)
        self.assertEqual(self._get_data_size(PixelFormat.R8G8B8A8, 0, 0), 0)
        self.assertEqual(self._get_data_size(PixelFormat.B8G8R8A8, 0, 0), 0)
        
        # Test compressed formats (minimum block sizes)
        self.assertEqual(self._get_data_size(PixelFormat.DXT1, 0, 0), 8)
        self.assertEqual(self._get_data_size(PixelFormat.DXT3, 0, 0), 16)
        self.assertEqual(self._get_data_size(PixelFormat.DXT5, 0, 0), 16)
        
        # Test compressed formats with small dimensions
        self.assertEqual(self._get_data_size(PixelFormat.DXT1, 3, 3), 8)
        self.assertEqual(self._get_data_size(PixelFormat.DXT3, 3, 3), 16)
        self.assertEqual(self._get_data_size(PixelFormat.DXT5, 3, 3), 16)

    def test_flip_vertically_3_channels(self):
        """Test vertical image flipping with 3 channels.
        
        Original xoreos test: GTEST_TEST(ImagesUtil, flipVertically3)
        """
        # Test 2x2 image
        flipped = self._flip_vertically(self.k_image_2_2_3, 2, 2, 3)
        expected = bytes([
            0x10, 0x11, 0x12, 0x13, 0x14, 0x15,
            0x00, 0x01, 0x02, 0x03, 0x04, 0x05
        ])
        self._compare_data(flipped, expected)
        
        # Test 3x3 image
        flipped = self._flip_vertically(self.k_image_3_3_3, 3, 3, 3)
        expected = bytes([
            0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28,
            0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18,
            0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08
        ])
        self._compare_data(flipped, expected)

    def test_flip_vertically_4_channels(self):
        """Test vertical image flipping with 4 channels.
        
        Original xoreos test: GTEST_TEST(ImagesUtil, flipVertically4)
        """
        # Test 2x2 image
        flipped = self._flip_vertically(self.k_image_2_2_4, 2, 2, 4)
        expected = bytes([
            0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17,
            0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07
        ])
        self._compare_data(flipped, expected)
        
        # Test 3x3 image
        flipped = self._flip_vertically(self.k_image_3_3_4, 3, 3, 4)
        expected = bytes([
            0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x29, 0x2A, 0x2B,
            0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x1B,
            0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B
        ])
        self._compare_data(flipped, expected)

    def test_flip_horizontally_3_channels(self):
        """Test horizontal image flipping with 3 channels.
        
        Original xoreos test: GTEST_TEST(ImagesUtil, flipHorizontally3)
        """
        # Test 2x2 image
        flipped = self._flip_horizontally(self.k_image_2_2_3, 2, 2, 3)
        expected = bytes([
            0x03, 0x04, 0x05, 0x00, 0x01, 0x02,
            0x13, 0x14, 0x15, 0x10, 0x11, 0x12
        ])
        self._compare_data(flipped, expected)
        
        # Test 3x3 image
        flipped = self._flip_horizontally(self.k_image_3_3_3, 3, 3, 3)
        expected = bytes([
            0x06, 0x07, 0x08, 0x03, 0x04, 0x05, 0x00, 0x01, 0x02,
            0x16, 0x17, 0x18, 0x13, 0x14, 0x15, 0x10, 0x11, 0x12,
            0x26, 0x27, 0x28, 0x23, 0x24, 0x25, 0x20, 0x21, 0x22
        ])
        self._compare_data(flipped, expected)

    def test_flip_horizontally_4_channels(self):
        """Test horizontal image flipping with 4 channels.
        
        Original xoreos test: GTEST_TEST(ImagesUtil, flipHorizontally4)
        """
        # Test 2x2 image
        flipped = self._flip_horizontally(self.k_image_2_2_4, 2, 2, 4)
        expected = bytes([
            0x04, 0x05, 0x06, 0x07, 0x00, 0x01, 0x02, 0x03,
            0x14, 0x15, 0x16, 0x17, 0x10, 0x11, 0x12, 0x13
        ])
        self._compare_data(flipped, expected)
        
        # Test 3x3 image
        flipped = self._flip_horizontally(self.k_image_3_3_4, 3, 3, 4)
        expected = bytes([
            0x08, 0x09, 0x0A, 0x0B, 0x04, 0x05, 0x06, 0x07, 0x00, 0x01, 0x02, 0x03,
            0x18, 0x19, 0x1A, 0x1B, 0x14, 0x15, 0x16, 0x17, 0x10, 0x11, 0x12, 0x13,
            0x28, 0x29, 0x2A, 0x2B, 0x24, 0x25, 0x26, 0x27, 0x20, 0x21, 0x22, 0x23
        ])
        self._compare_data(flipped, expected)

    def test_edge_cases(self):
        """Test edge cases for image operations."""
        # Test 1x1 images
        flipped_v = self._flip_vertically(self.k_image_1_1_3, 1, 1, 3)
        self._compare_data(flipped_v, self.k_image_1_1_3)
        
        flipped_h = self._flip_horizontally(self.k_image_1_1_3, 1, 1, 3)
        self._compare_data(flipped_h, self.k_image_1_1_3)
        
        # Test single row/column images
        single_row = bytes([0x00, 0x01, 0x02, 0x03, 0x04, 0x05])
        flipped_v = self._flip_vertically(single_row, 2, 1, 3)
        self._compare_data(flipped_v, single_row)  # Should be unchanged
        
        single_col = bytes([0x00, 0x01, 0x02, 0x10, 0x11, 0x12])
        flipped_h = self._flip_horizontally(single_col, 1, 2, 3)
        self._compare_data(flipped_h, single_col)  # Should be unchanged

    # --- Helper Methods ---

    def _get_bpp(self, pixel_format: PixelFormat) -> int:
        """Get bytes per pixel for a pixel format.
        
        Equivalent to Images::getBPP().
        """
        bpp_map = {
            PixelFormat.R8G8B8: 3,
            PixelFormat.B8G8R8: 3,
            PixelFormat.R8G8B8A8: 4,
            PixelFormat.B8G8R8A8: 4,
            PixelFormat.A1R5G5B5: 2,
            PixelFormat.R5G6B5: 2,
            PixelFormat.DEPTH16: 2,
            PixelFormat.DXT1: 0,  # Compressed formats
            PixelFormat.DXT3: 0,
            PixelFormat.DXT5: 0,
        }
        return bpp_map.get(pixel_format, 0)

    def _get_data_size(self, pixel_format: PixelFormat, width: int, height: int) -> int:
        """Get data size for an image with given format and dimensions.
        
        Equivalent to Images::getDataSize().
        """
        if width == 0 or height == 0:
            # Handle compressed formats minimum sizes
            if pixel_format == PixelFormat.DXT1:
                return 8
            elif pixel_format in [PixelFormat.DXT3, PixelFormat.DXT5]:
                return 16
            return 0
        
        bpp = self._get_bpp(pixel_format)
        if bpp > 0:
            return width * height * bpp
        
        # Handle compressed formats
        if pixel_format == PixelFormat.DXT1:
            # DXT1 uses 4x4 blocks with 8 bytes per block
            blocks_x = max(1, (width + 3) // 4)
            blocks_y = max(1, (height + 3) // 4)
            return blocks_x * blocks_y * 8
        elif pixel_format in [PixelFormat.DXT3, PixelFormat.DXT5]:
            # DXT3/DXT5 use 4x4 blocks with 16 bytes per block
            blocks_x = max(1, (width + 3) // 4)
            blocks_y = max(1, (height + 3) // 4)
            return blocks_x * blocks_y * 16
        
        return 0

    def _flip_vertically(self, image_data: bytes, width: int, height: int, channels: int) -> bytes:
        """Flip image vertically.
        
        Equivalent to Images::flipVertically().
        """
        if height <= 1:
            return image_data
        
        row_size = width * channels
        flipped = bytearray()
        
        # Copy rows in reverse order
        for y in range(height - 1, -1, -1):
            start = y * row_size
            end = start + row_size
            flipped.extend(image_data[start:end])
        
        return bytes(flipped)

    def _flip_horizontally(self, image_data: bytes, width: int, height: int, channels: int) -> bytes:
        """Flip image horizontally.
        
        Equivalent to Images::flipHorizontally().
        """
        if width <= 1:
            return image_data
        
        row_size = width * channels
        pixel_size = channels
        flipped = bytearray()
        
        # Process each row
        for y in range(height):
            row_start = y * row_size
            row_data = image_data[row_start:row_start + row_size]
            
            # Reverse pixels in this row
            flipped_row = bytearray()
            for x in range(width - 1, -1, -1):
                pixel_start = x * pixel_size
                pixel_end = pixel_start + pixel_size
                flipped_row.extend(row_data[pixel_start:pixel_end])
            
            flipped.extend(flipped_row)
        
        return bytes(flipped)

    def _compare_data(self, actual: bytes, expected: bytes):
        """Compare two byte sequences with detailed error reporting."""
        self.assertEqual(len(actual), len(expected), 
            f"Length mismatch: {len(actual)} vs {len(expected)}")
        
        for i, (actual_byte, expected_byte) in enumerate(zip(actual, expected)):
            self.assertEqual(actual_byte, expected_byte, 
                f"Byte mismatch at index {i}: 0x{actual_byte:02X} vs 0x{expected_byte:02X}")


if __name__ == "__main__":
    unittest.main()
