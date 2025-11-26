"""Core tests for the texture loader process - independent of Qt.

These tests only test the serialization/deserialization logic
and don't require Qt to be installed.
"""

from __future__ import annotations

import multiprocessing
import struct
import unittest

from pykotor.resource.formats.tpc import TPCTextureFormat
from pykotor.resource.formats.tpc.tpc_data import TPCMipmap


class TestMipmapSerialization(unittest.TestCase):
    """Tests for mipmap serialization/deserialization.
    
    These tests verify the serialization format used to transfer
    mipmap data between processes.
    """
    
    def _serialize_mipmap(self, mipmap: TPCMipmap) -> bytes:
        """Serialize a TPCMipmap using the same format as TextureLoaderProcess."""
        header = struct.pack(
            "<IIII",
            mipmap.width,
            mipmap.height,
            mipmap.tpc_format.value,
            len(mipmap.data),
        )
        return header + bytes(mipmap.data)
    
    def _deserialize_mipmap(self, data: bytes) -> TPCMipmap:
        """Deserialize a TPCMipmap from bytes."""
        header_size = 16  # 4 * 4 bytes
        width, height, format_value, data_length = struct.unpack("<IIII", data[:header_size])
        mipmap_data = bytearray(data[header_size:header_size + data_length])
        return TPCMipmap(
            width=width,
            height=height,
            tpc_format=TPCTextureFormat(format_value),
            data=mipmap_data,
        )
    
    def test_serialize_deserialize_rgba(self):
        """Test round-trip serialization of RGBA mipmap."""
        width, height = 64, 64
        test_data = bytearray(width * height * 4)  # RGBA = 4 bytes per pixel
        for i in range(len(test_data)):
            test_data[i] = i % 256
        
        original = TPCMipmap(
            width=width,
            height=height,
            tpc_format=TPCTextureFormat.RGBA,
            data=test_data,
        )
        
        serialized = self._serialize_mipmap(original)
        result = self._deserialize_mipmap(serialized)
        
        self.assertEqual(result.width, original.width)
        self.assertEqual(result.height, original.height)
        self.assertEqual(result.tpc_format, original.tpc_format)
        self.assertEqual(result.data, original.data)
    
    def test_serialize_deserialize_rgb(self):
        """Test round-trip serialization of RGB mipmap."""
        width, height = 32, 32
        test_data = bytearray(width * height * 3)  # RGB = 3 bytes per pixel
        
        original = TPCMipmap(
            width=width,
            height=height,
            tpc_format=TPCTextureFormat.RGB,
            data=test_data,
        )
        
        serialized = self._serialize_mipmap(original)
        result = self._deserialize_mipmap(serialized)
        
        self.assertEqual(result.width, original.width)
        self.assertEqual(result.height, original.height)
        self.assertEqual(result.tpc_format, original.tpc_format)
    
    def test_serialize_deserialize_greyscale(self):
        """Test round-trip serialization of greyscale mipmap."""
        width, height = 16, 16
        test_data = bytearray(width * height)  # 1 byte per pixel
        
        original = TPCMipmap(
            width=width,
            height=height,
            tpc_format=TPCTextureFormat.Greyscale,
            data=test_data,
        )
        
        serialized = self._serialize_mipmap(original)
        result = self._deserialize_mipmap(serialized)
        
        self.assertEqual(result.width, original.width)
        self.assertEqual(result.height, original.height)
        self.assertEqual(result.tpc_format, original.tpc_format)
    
    def test_serialize_format(self):
        """Test that serialization format is correct."""
        mipmap = TPCMipmap(
            width=10,
            height=20,
            tpc_format=TPCTextureFormat.RGBA,
            data=bytearray(10 * 20 * 4),
        )
        
        serialized = self._serialize_mipmap(mipmap)
        
        # Check header
        width, height, fmt, data_len = struct.unpack("<IIII", serialized[:16])
        self.assertEqual(width, 10)
        self.assertEqual(height, 20)
        self.assertEqual(fmt, TPCTextureFormat.RGBA.value)
        self.assertEqual(data_len, 10 * 20 * 4)
        
        # Check total length
        self.assertEqual(len(serialized), 16 + 10 * 20 * 4)


class TestQueueCommunication(unittest.TestCase):
    """Tests for multiprocessing queue communication."""
    
    def test_queue_put_get(self):
        """Test that data can be sent through queues."""
        queue = multiprocessing.Queue()
        
        test_data = ("resref", "tpc", ("section", 0), 64)
        queue.put(test_data)
        
        received = queue.get(timeout=1.0)
        self.assertEqual(received, test_data)
        
        queue.close()
    
    def test_queue_multiple_items(self):
        """Test sending multiple items through queue."""
        queue = multiprocessing.Queue()
        
        items = [
            ("tex1", "tpc", ("s1", 0), 64),
            ("tex2", "tga", ("s1", 1), 32),
            ("tex3", "tpc", ("s2", 0), 128),
        ]
        
        for item in items:
            queue.put(item)
        
        for expected in items:
            received = queue.get(timeout=1.0)
            self.assertEqual(received, expected)
        
        queue.close()


if __name__ == "__main__":
    unittest.main()

