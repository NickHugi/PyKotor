from __future__ import annotations

import unittest
import struct

from pexpect.expect import Expecter

from pykotor.resource.formats.tpc.tpc_data import TPC
from unittest.mock import patch, MagicMock

class TestTPCData(unittest.TestCase):

    def setUp(self):
        self.tpc = TPC()

    def test_dxt5_to_rgba_basic(self):
        mock_data = b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f'
        width, height = 4, 4
        
        with patch.object(TPC, 'rgba565_to_rgb', return_value=(255, 0, 0)):
            with patch.object(TPC, 'rgba565_to_rgb888', return_value=65535):
                with patch.object(TPC, 'interpolate_rgb', return_value=(128, 0, 0)):
                    result = self.tpc.dxt5_to_rgba(mock_data, width, height)
        
        self.assertEqual(len(result), width * height * 4)
        self.assertEqual(result[:4], b'\xff\x00\x00\x00')

    def test_dxt5_to_rgba_edge_case(self):
        mock_data = b'\xff\x00' + b'\x00' * 14
        width, height = 4, 4
        
        with patch.object(TPC, 'rgba565_to_rgb', return_value=(0, 255, 0)):
            with patch.object(TPC, 'rgba565_to_rgb888', return_value=0):
                result = self.tpc.dxt5_to_rgba(mock_data, width, height)
        
        self.assertEqual(len(result), width * height * 4)
        self.assertEqual(result[-4:], b'\x00\xff\x00\xff')

    @patch('io.BytesIO')
    def test_dxt5_to_rgba_io_interaction(self, mock_bytesio):
        mock_instance = MagicMock()
        mock_bytesio.return_value = mock_instance
        mock_instance.read.side_effect = [b'\x00\x01', b'\x02\x03\x04\x05\x06\x07', b'\x08\x09\x0a\x0b', b'\x0c\x0d\x0e\x0f']
        
        with patch.object(TPC, 'rgba565_to_rgb', return_value=(0, 0, 255)):
            with patch.object(TPC, 'rgba565_to_rgb888', return_value=32768):
                self.tpc.dxt5_to_rgba(b'\x00' * 16, 4, 4)
        
        mock_instance.read.assert_called()

    def test_dxt5_to_rgba_interpolation(self):
        mock_data = b'\x00\xff' + b'\x00' * 14
        width, height = 4, 4
        
        with patch.object(TPC, 'rgba565_to_rgb', return_value=(255, 255, 255)):
            with patch.object(TPC, 'rgba565_to_rgb888', return_value=65535):
                with patch.object(TPC, 'interpolate_rgb', side_effect=[(170, 170, 170), (85, 85, 85)]):
                    result = self.tpc.dxt5_to_rgba(mock_data, width, height)
        
        self.assertIn(b'\xaa\xaa\xaa', result)
        self.assertIn(b'\x55\x55\x55', result)

    def test_dxt5_to_rgba_alpha_interpolation(self):
        mock_data = b'\x00\x80' + b'\x00' * 14
        width, height = 4, 4
        
        with patch.object(TPC, 'rgba565_to_rgb', return_value=(0, 0, 0)):
            with patch.object(TPC, 'rgba565_to_rgb888', return_value=0):
                result = self.tpc.dxt5_to_rgba(mock_data, width, height)
        
        self.assertIn(b'\x00\x00\x00\x00', result)
        self.assertIn(b'\x00\x00\x00\x80', result)
        self.assertIn(b'\x00\x00\x00\x40', result)

    def test_rgba_to_dxt1_basic(self):
        width, height = 8, 8
        rgba_data = bytes([255, 0, 0, 255] * (width * height))  # Red
        result = TPC.rgba_to_dxt1(rgba_data, width, height)
        self.assertEqual(len(result), 32)  # 8x8 image should compress to 32 bytes

    def test_rgba_to_dxt1_all_black(self):
        width, height = 4, 4
        rgba_data = bytes([0, 0, 0, 255] * (width * height))  # Black
        result = TPC.rgba_to_dxt1(rgba_data, width, height)
        self.assertEqual(result[:4], b'\x00\x00\x00\x00')  # First two colors should be black

    def test_rgba_to_dxt1_all_white(self):
        width, height = 4, 4
        rgba_data = bytes([255, 255, 255, 255] * (width * height))  # White
        result = TPC.rgba_to_dxt1(rgba_data, width, height)
        self.assertEqual(result[:4], b'\xFF\xFF\xFF\xFF')  # First two colors should be white

    def test_rgba_to_dxt1_gradient(self):
        width, height = 4, 4
        rgba_data = bytes(i for _ in range(16) for i in [_, _, _, 255])[:64]
        result = TPC.rgba_to_dxt1(rgba_data, width, height)
        self.assertEqual(len(result), 8)  # 4x4 image should compress to 8 bytes

    def test_rgba_to_dxt1_odd_dimensions(self):
        width, height = 5, 7
        rgba_data = bytes([255, 0, 0, 255] * (width * height))
        result = TPC.rgba_to_dxt1(rgba_data, width, height)
        self.assertEqual(len(result), 32)  # Rounds up to 8x8 blocks

    def test_rgba_to_dxt1_transparency(self):
        width, height = 4, 4
        rgba_data = bytes([255, 0, 0, 0] * 8 + [0, 255, 0, 255] * 8)  # Half transparent red, half opaque green
        result = TPC.rgba_to_dxt1(rgba_data, width, height)
        self.assertEqual(len(result), 8)

    def test_dxt1_to_rgb_basic(self):
        width, height = 8, 8
        mock_data = b'\x00\x00\x00\x00\x00\x00\x00\x00' * (width * height // 16)
        result = TPC.dxt1_to_rgb(mock_data, width, height)
        self.assertEqual(len(result), width * height * 3)

    def test_interpolation(self):
        width, height = 4, 4
        # White and black colors
        mock_data = b'\xFF\xFF\x00\x00\x55\x55\x00\x00'
        result = TPC.dxt1_to_rgb(mock_data, width, height)
        self.assertEqual(result[12:15], b'\xAA\xAA\xAA')  # Gray (interpolated)

    def test_larger_image(self):
        width, height = 8, 8
        mock_data = b'\xFF\xFF\x00\x00\x00\x00\x00\x00' * 4
        result = TPC.dxt1_to_rgb(mock_data, width, height)
        self.assertEqual(len(result), width * height * 3)

    def test_non_square_image(self):
        width, height = 8, 4
        mock_data = b'\xFF\xFF\x00\x00\x00\x00\x00\x00' * 2
        result = TPC.dxt1_to_rgb(mock_data, width, height)
        self.assertEqual(len(result), width * height * 3)

    def test_minimum_size(self):
        width, height = 1, 1
        mock_data = b'\xFF\xFF\x00\x00\x00\x00\x00\x00'
        result = TPC.dxt1_to_rgb(mock_data, width, height)
        self.assertEqual(len(result), 3)  # 1 pixel, 3 bytes (RGB)

    def test_all_same_color_dxt1_to_rgb(self):
        width, height = 4, 4
        # All green
        mock_data = b'\x00\xFC\x00\xFC\x00\x00\x00\x00'
        result = TPC.dxt1_to_rgb(mock_data, width, height)
        for i in range(0, len(result), 3):
            self.assertEqual(result[i:i+3], b'\x00\xFC\x00')

    def test_color_extremes_dxt1_to_rgb(self):
        width, height = 4, 4
        # White and black
        mock_data = b'\xFF\xFF\x00\x00\xFF\xFF\xFF\xFF'
        result = TPC.dxt1_to_rgb(mock_data, width, height)
        self.assertEqual(result[:3], b'\xF8\xFC\xF8')  # White
        self.assertEqual(result[-3:], b'\x00\x00\x00')  # Black

    def test_large_image(self):
        width, height = 1024, 1024
        mock_data = b'\xFF\xFF\x00\x00\x00\x00\x00\x00' * (width * height // 16)
        result = TPC.dxt1_to_rgb(mock_data, width, height)
        self.assertEqual(len(result), width * height * 3)

    def test_different_color_patterns(self):
        width, height = 8, 8
        # Alternating red and blue blocks
        mock_data = (b'\xFF\x00\x00\x1F\x55\x55\x55\x55' + 
                     b'\x00\x1F\xFF\x00\xAA\xAA\xAA\xAA') * 4
        result = TPC.dxt1_to_rgb(mock_data, width, height)
        self.assertEqual(result[0:3], b'\xF8\x00\x00')  # Red
        self.assertEqual(result[24:27], b'\x00\x00\xF8')  # Blue

    def test_gradient(self):
        width, height = 4, 4
        # Gradient from black to white
        mock_data = b'\x00\x00\xFF\xFF\xE0\xE0\xE0\xE0'
        result = TPC.dxt1_to_rgb(mock_data, width, height)
        self.assertEqual(result[0:3], b'\x00\x00\x00')  # Black
        self.assertEqual(result[-3:], b'\xF8\xFC\xF8')  # White
        # Check middle values for gradient
        self.assertNotEqual(result[18:21], b'\x00\x00\x00')
        self.assertNotEqual(result[18:21], b'\xF8\xFC\xF8')

    def test_interpolation_dxt1_to_rgb(self):
        width, height = 4, 4
        mock_data = b'\xFF\xFF\x00\x00\x00\x00\x00\x00'
        result = TPC.dxt1_to_rgb(mock_data, width, height)
        self.assertEqual(result[:3], b'\xFF\xFF\xFF')
        self.assertEqual(result[-3:], b'\x00\x00\x00')

    def test_dxt1_to_rgb_odd_dimensions(self):
        width, height = 5, 7
        mock_data = b'\x00\x00\x00\x00\x00\x00\x00\x00' * ((width * height + 15) // 16)
        result = TPC.dxt1_to_rgb(mock_data, width, height)
        self.assertEqual(len(result), width * height * 3)

    def test_dxt1_to_rgb_large_dimensions(self):
        width, height = 1024, 1024
        mock_data = b'\x00\x00\x00\x00\x00\x00\x00\x00' * (width * height // 16)
        result = TPC.dxt1_to_rgb(mock_data, width, height)
        self.assertEqual(len(result), width * height * 3)

    @patch('io.BytesIO')
    def test_dxt5_to_rgba(self, mock_bytesio):
        mock_data = b'\x00' * 100
        mock_width = 8
        mock_height = 8
        
        mock_bytesio_instance = MagicMock()
        mock_bytesio.return_value = mock_bytesio_instance
        
        mock_bytesio_instance.read.side_effect = [
            b'\x00\x01',  # alpha0, alpha1
            b'\x00' * 6,  # dxt_alpha
            struct.pack('<HH', 0, 0),  # x, y
            struct.pack('>I', 0)  # dxt_pixels
        ] * 4  # 4 blocks for 8x8 image
        
        with patch.object(TPC, 'rgba565_to_rgb', return_value=(0, 0, 0)):
            with patch.object(TPC, 'rgba565_to_rgb888', return_value=0):
                with patch.object(TPC, 'interpolate_rgb', return_value=(0, 0, 0)):
                    result = TPC.dxt5_to_rgba(mock_data, mock_width, mock_height)
        
        self.assertIsInstance(result, bytearray)
        self.assertEqual(len(result), mock_width * mock_height * 4)
        
        # Check if BytesIO was called with the correct data
        mock_bytesio.assert_called_once_with(mock_data)
        
        # Check if read method was called the correct number of times
        self.assertEqual(mock_bytesio_instance.read.call_count, 16)  # 4 calls per block, 4 blocks

    @patch('pykotor.resource.formats.tpc.tpc_data.TPC.rgba565_to_rgb')
    @patch('pykotor.resource.formats.tpc.tpc_data.TPC.rgba565_to_rgb888')
    @patch('pykotor.resource.formats.tpc.tpc_data.TPC.interpolate_rgb')
    def test_dxt1_to_rgba(self, mockinterpolate_rgb, mockrgba565_to_rgb888, mockrgba565_to_rgb):
        mockrgba565_to_rgb.side_effect = [(255, 0, 0), (0, 255, 0)]
        mockrgba565_to_rgb888.side_effect = [65535, 65534]
        mockinterpolate_rgb.side_effect = [(128, 128, 0), (192, 64, 0)]

        data = struct.pack('<HHII', 0xF800, 0x07E0, 0xE4000000, 0)
        width, height = 4, 4

        result = TPC.dxt1_to_rgba(data, width, height)

        # Check if mocked functions were called correctly
        self.assertEqual(mockrgba565_to_rgb.call_count, 2)
        self.assertEqual(mockrgba565_to_rgb888.call_count, 2)
        self.assertEqual(mockinterpolate_rgb.call_count, 2)

        expected = bytearray([
            255, 0, 0, 255,   0, 255, 0, 255,   128, 128, 0, 255,   0, 0, 0, 255,
            255, 0, 0, 255,   255, 0, 0, 255,   255, 0, 0, 255,     255, 0, 0, 255,
            255, 0, 0, 255,   255, 0, 0, 255,   255, 0, 0, 255,     255, 0, 0, 255,
            255, 0, 0, 255,   255, 0, 0, 255,   255, 0, 0, 255,     255, 0, 0, 255
        ])

        for i, (expected_byte, result_byte) in enumerate(zip(expected, result)):
            self.assertEqual(expected_byte, result_byte, f"Mismatch at the {i+1}th byte: expected {expected_byte}, got {result_byte}")

        self.assertEqual(result, expected)

    def test_rgb_to_rgba_basic(self):
        input_data = b'\x01\x02\x03\x04\x05\x06'
        width, height = 2, 1
        result = TPC.rgb_to_rgba(input_data, width, height)
        expected = bytearray(b'\x01\x02\x03\xff\x04\x05\x06\xff')
        self.assertEqual(result, expected)

    def test_rgb_to_rgba_empty(self):
        input_data = b''
        width, height = 0, 0
        result = TPC.rgb_to_rgba(input_data, width, height)
        self.assertEqual(result, bytearray())

    def test_rgb_to_rgba_large(self):
        input_data = b'\x01\x02\x03' * 100
        width, height = 10, 10
        result = TPC.rgb_to_rgba(input_data, width, height)
        self.assertEqual(len(result), width * height * 4)
        self.assertTrue(all(pixel[3] == 255 for pixel in zip(*[iter(result)]*4)))

    def test_rgb_to_rgba_odd_dimensions(self):
        input_data = b'\x01\x02\x03\x04\x05\x06\x07\x08\x09'
        width, height = 3, 1
        result = TPC.rgb_to_rgba(input_data, width, height)
        expected = bytearray(b'\x01\x02\x03\xff\x04\x05\x06\xff\x07\x08\x09\xff')
        self.assertEqual(result, expected)

    def test_rgb_to_rgba_multiple_rows(self):
        input_data = b'\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c'
        width, height = 2, 2
        result = TPC.rgb_to_rgba(input_data, width, height)
        expected = bytearray(b'\x01\x02\x03\xff\x04\x05\x06\xff\x07\x08\x09\xff\x0a\x0b\x0c\xff')
        self.assertEqual(result, expected)

    def test_dxt1_to_rgba_edge_case(self):
        dxt1_data = b'\xFF\xFF\x00\x00\xFF\xFF\xFF\xFF'  # Edge case DXT1 data
        width, height = 4, 4
        result = TPC.dxt1_to_rgba(dxt1_data, width, height)
        self.assertEqual(len(result), width * height * 4)
        self.assertNotEqual(result[0], result[-4])  # Check color variation

    def test_dxt1_to_rgba_large_image(self):
        dxt1_data = b'\x00\x00\x00\x00\x00\x00\x00\x00' * 16  # 8x8 image
        width, height = 8, 8
        result = TPC.dxt1_to_rgba(dxt1_data, width, height)
        self.assertEqual(len(result), width * height * 4)

    def test_rgb_to_rgba(self):
        rgb_data = b'\xFF\x00\x00' * 16  # 4x4 red image
        width, height = 4, 4
        result = TPC.rgb_to_rgba(rgb_data, width, height)
        self.assertEqual(len(result), width * height * 4)
        self.assertEqual(result[0], 255)  # Red channel
        self.assertEqual(result[1], 0)    # Green channel
        self.assertEqual(result[2], 0)    # Blue channel
        self.assertEqual(result[3], 255)  # Alpha channel
        # Check that the pattern repeats for all pixels
        for i in range(0, len(result), 4):
            self.assertEqual(result[i:i+4], b'\xFF\x00\x00\xFF')

    def test_grey_to_rgba(self):
        grey_data = b'\x80' * 16  # 4x4 grey image
        width, height = 4, 4
        result = TPC.grey_to_rgba(grey_data, width, height)
        self.assertEqual(len(result), width * height * 4)
        self.assertEqual(result[0], 128)  # Grey value
        self.assertEqual(result[3], 255)  # Alpha channel

    def test_rgba_to_grey(self):
        rgba_data = b'\xFF\x80\x00\xFF' * 16  # 4x4 orange image
        width, height = 4, 4
        result = TPC.rgba_to_grey(rgba_data, width, height)
        self.assertEqual(len(result), width * height)
        self.assertEqual(result[0], 255)  # Highest value of R, G, B

    def test_bgra_to_grey(self):
        bgra_data = b'\x00\x80\xFF\xFF' * 16  # 4x4 orange image in BGRA
        width, height = 4, 4
        result = TPC.bgra_to_grey(bgra_data, width, height)
        self.assertEqual(len(result), width * height)
        self.assertEqual(result[0], 255)  # Highest value of R, G, B

    def testrgba565_to_rgb888(self):
        color = 0xF800  # Pure red in RGB565
        result = TPC.rgba565_to_rgb888(color)
        self.assertEqual(result >> 16, 248)  # Red channel
        self.assertEqual((result >> 8) & 0xFF, 0)  # Green channel
        self.assertEqual(result & 0xFF, 0)  # Blue channel

    def test_rgb_to_rgba565(self):
        rgb = (255, 0, 0)  # Pure red
        result = TPC.rgb_to_rgba565(rgb[0], rgb[1], rgb[2])
        self.assertEqual(result, 0xF800)

    def testinterpolate_rgb(self):
        color0 = (255, 0, 0)  # Red
        color1 = (0, 255, 0)  # Green
        weight = 0.5
        result = TPC.interpolate_rgb(weight, color0, color1)
        self.assertEqual(result, (128, 128, 0))

    def test_dxt1_to_rgba_basic(self):
        dxt1_data = b'\x00\x00\x00\x00\x00\x00\x00\x00'  # Simplified DXT1 data
        width, height = 4, 4
        result = TPC.dxt1_to_rgba(dxt1_data, width, height)
        self.assertEqual(len(result), width * height * 4)
        self.assertEqual(result[-1], 255)  # Check alpha channel

    def test_dxt1_to_rgba_interpolation(self):
        # This represents a 4x4 DXT1 block with two colors: red (0xF800) and green (0x07E0)
        mock_data = b'\x00\xF8\xE0\x07\x55\x55\x55\x55'
        width, height = 4, 4
        result = TPC.dxt1_to_rgba(mock_data, width, height)
        
        # Check the size of the result
        self.assertEqual(len(result), width * height * 4)
        
        # Check the first pixel (should be red)
        self.assertEqual(result[0:4], b'\xFF\x00\x00\xFF')
        
        # Check the second pixel (should be green)
        self.assertEqual(result[4:8], b'\x00\xFF\x00\xFF')
        
        # Check a third pixel (should be an interpolated color)
        self.assertNotEqual(result[8:12], b'\xFF\x00\x00\xFF')
        self.assertNotEqual(result[8:12], b'\x00\xFF\x00\xFF')
        
        # Verify that we have different colors in the result (interpolation happened)
        self.assertGreater(len(set(result[::4])), 2)  # Check red channel
        self.assertGreater(len(set(result[1::4])), 2)  # Check green channel

    def test_dxt1_to_rgba_non_multiple_of_four(self):
        mock_data = b'\x00\x00\x00\x00\x00\x00\x00\x00' * 2
        width, height = 6, 6
        result = TPC.dxt1_to_rgba(mock_data, width, height)
        self.assertEqual(len(result), width * height * 4)

    def test_dxt1_to_rgba_empty_input(self):
        mock_data = b''
        width, height = 0, 0
        result = TPC.dxt1_to_rgba(mock_data, width, height)
        self.assertEqual(len(result), 0)
        
    def test_basic_conversion_rgba_to_grey(self):
        data = bytes([255, 0, 0, 255, 0, 255, 0, 255, 0, 0, 255, 255])
        result = TPC.rgba_to_grey(data, 3, 1)
        self.assertEqual(result, bytearray([255, 255, 255]))

    def test_basic_conversion_dxt1_to_rgb(self):
        width, height = 4, 4
        # Red and blue colors
        mock_data = b'\xFF\x00\x00\x1F\x00\x00\x00\x00'
        result = TPC.dxt1_to_rgb(mock_data, width, height)
        self.assertEqual(len(result), width * height * 3)
        self.assertEqual(result[:3], b'\xF8\x00\x00')  # Red
        self.assertEqual(result[-3:], b'\x00\x00\xF8')  # Blue

    def test_reconstruction(self):
        width, height = 4, 4
        original_dxt1 = b'\xE0\xF8\x1F\x00\xE4\x44\x44\x44'
        rgb_data = TPC.dxt1_to_rgb(original_dxt1, width, height)
        
        # This test is a bit tricky as perfect reconstruction isn't always possible
        # due to the lossy nature of DXT1 compression. We'll check if the main colors
        # are preserved and in the correct positions.
        self.assertEqual(rgb_data[0:3], b'\xF8\x1C\x00')  # Red
        self.assertEqual(rgb_data[-3:], b'\x00\x00\xF8')  # Blue
        # Check if interpolated colors exist
        interpolated_color = b'\xA4\x00\x54'
        found_interpolated = any(interpolated_color == rgb_data[i:i+3] for i in range(0, len(rgb_data), 3))
        self.assertTrue(
            found_interpolated,
            f"Expected to find the interpolated color {interpolated_color!r} in the RGB data, "
            f"but it was not present. This suggests that color interpolation in the DXT1 to RGB "
            f"conversion may not be working correctly. The first few bytes of the RGB data are: "
            f"{rgb_data[:15]!r}..."
        )


    def test_all_black(self):
        data = bytes([0, 0, 0, 255] * 4)
        result = TPC.rgba_to_grey(data, 2, 2)
        self.assertEqual(result, bytearray([0, 0, 0, 0]))

    def test_all_white(self):
        data = bytes([255, 255, 255, 255] * 4)
        result = TPC.rgba_to_grey(data, 2, 2)
        self.assertEqual(result, bytearray([255, 255, 255, 255]))

    def test_mixed_colors(self):
        data = bytes([100, 150, 200, 255, 50, 100, 150, 255])
        result = TPC.rgba_to_grey(data, 2, 1)
        self.assertEqual(result, bytearray([200, 150]))

    def test_empty_data(self):
        data = bytes()
        result = TPC.rgba_to_grey(data, 0, 0)
        self.assertEqual(result, bytearray())

    def test_single_pixel(self):
        data = bytes([123, 45, 67, 255])
        result = TPC.rgba_to_grey(data, 1, 1)
        self.assertEqual(result, bytearray([123]))


if __name__ == "__main__":
    unittest.main()
