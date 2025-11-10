from __future__ import annotations

import unittest
import struct

from pykotor.resource.formats.tpc.tpc_data import TPC
from pykotor.resource.formats.tpc.convert.dxt.decompress_dxt import dxt5_to_rgba, dxt1_to_rgb
from pykotor.resource.formats.tpc.convert.dxt.compress_dxt import rgb_to_dxt1
from pykotor.resource.formats.tpc.convert.rgb import rgba_to_rgb, rgb_to_rgba, rgba_to_grey, grey_to_rgba
from pykotor.resource.formats.tpc.convert.bgra import bgra_to_grey


class TestTPCData(unittest.TestCase):
    def setUp(self):
        self.tpc = TPC()
        # Real DXT1 block data representing actual texture patterns
        self.dxt1_red: bytes = bytes.fromhex('00F800F800000000')  # Pure red DXT1 block with pure red indices
        self.dxt1_gradient: bytes = bytes.fromhex('F80007E0A4A4A4A4')  # Red-green gradient

    def test_dxt1_decompression_accuracy(self):
        """Test DXT1 decompression with real texture data"""
        width, height = 4, 4
        result: bytearray = dxt1_to_rgb(self.dxt1_red, width, height)
        
        # Verify correct decompression of red color (5:6:5 format)
        self.assertEqual(bytes(result[0:3]), b'\xff\x00\x00')  # Red expanded from 5-bit precision
        self.assertEqual(len(result), width * height * 3)

    def test_dxt1_gradient_compression(self):
        """Test DXT1 compression with real gradient data"""
        width, height = 4, 4
        # Create a real RGB gradient
        rgb_data = bytearray()
        for y in range(height):
            for x in range(width):
                r = int((x / (width-1)) * 248)  # 5-bit red
                g = int((y / (height-1)) * 252)  # 6-bit green
                b = 0
                rgb_data.extend([r, g, b])
        
        result = rgb_to_dxt1(rgb_data, width, height)
        self.assertEqual(len(result), 8)  # Proper DXT1 block size

    def test_rgb_to_rgba_precision(self):
        """Test RGB to RGBA conversion with proper color precision"""
        # Real RGB colors with correct bit precision
        rgb_data = bytes([
            0xF8, 0xFC, 0xF8,  # White (5:6:5)
            0x00, 0x00, 0x00,  # Black
            0xF8, 0x00, 0x00,  # Red (5-bit)
            0x00, 0xFC, 0x00   # Green (6-bit)
        ])
        
        result = rgb_to_rgba(rgb_data)
        self.assertEqual(result[0:4], b'\xf8\xfc\xf8\xff')
        self.assertEqual(result[4:8], b'\x00\x00\x00\xff')

    def test_dxt1_block_boundaries(self):
        """Test DXT1 compression across block boundaries"""
        width, height = 8, 8  # 2x2 DXT blocks
        # Create a checkered pattern crossing block boundaries
        rgb_data = bytearray()
        for y in range(height):
            for x in range(width):
                if (x + y) % 2 == 0:
                    rgb_data.extend([0xF8, 0x00, 0x00])  # Red (5-bit)
                else:
                    rgb_data.extend([0x00, 0xFC, 0x00])  # Green (6-bit)
        
        compressed = rgb_to_dxt1(rgb_data, width, height)
        self.assertEqual(len(compressed), 32)  # 4 DXT1 blocks

if __name__ == "__main__":
    unittest.main()
