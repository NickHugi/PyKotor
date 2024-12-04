from __future__ import annotations

import io
import lzma
import os
import tempfile
from pathlib import Path
import unittest

import pytest

from pykotor.common.misc import ResRef
from pykotor.common.stream import BinaryWriter
from pykotor.resource.formats.bif import BIF, BIFResource, BIFType, read_bif, bytes_bif, BIFBinaryReader, BIFBinaryWriter
from pykotor.resource.type import ResourceType

K1_BIF_TEST_FILE = "tests/test_pykotor/test_files/k1_player.bif"

class TestBIFFormats(unittest.TestCase):

    def create_test_bzf(self) -> bytes:
        """Create a test BZF file with known content."""
        data: bytearray = bytearray()
        with BinaryWriter.to_bytearray(data) as writer:
            # Write header
            writer.write_string("BZF V1  ")  # Signature
            writer.write_uint32(3)  # Variable resource count
            writer.write_uint32(0)  # Fixed resource count
            writer.write_uint32(20)  # Variable table offset
            writer.write_uint32(0)  # Reserved

            # Compress test data
            data1: bytes = lzma.compress(b"Hello World 1")
            data2: bytes = lzma.compress(b"Hello World 2")
            data3: bytes = lzma.compress(b"Hello World 3")

            # Calculate offsets
            data_offset: int = 20 + (3 * 16)  # Header + (3 resources * 16 bytes per entry)
            offset1: int = 0
            offset2: int = len(data1)
            if offset2 % 4 != 0:  # Align to 4 bytes
                offset2 += 4 - (offset2 % 4)
            offset3: int = offset2 + len(data2)
            if offset3 % 4 != 0:  # Align to 4 bytes
                offset3 += 4 - (offset3 % 4)

            # Write resource table
            # Resource 1
            writer.write_uint32(0)  # ID
            writer.write_uint32(offset1)  # Offset from data section
            writer.write_uint32(13)  # Uncompressed size
            writer.write_uint32(2002)  # Type (TXT)

            # Resource 2
            writer.write_uint32(1)  # ID
            writer.write_uint32(offset2)  # Offset
            writer.write_uint32(13)  # Uncompressed size
            writer.write_uint32(2002)  # Type (TXT)

            # Resource 3
            writer.write_uint32(2)  # ID
            writer.write_uint32(offset3)  # Offset
            writer.write_uint32(13)  # Uncompressed size
            writer.write_uint32(2002)  # Type (TXT)

            # Write compressed data with padding
            writer.write_bytes(data1)
            padding: int = 4 - (len(data1) % 4) if len(data1) % 4 != 0 else 0
            writer.write_bytes(b"\0" * padding)

            writer.write_bytes(data2)
            padding = 4 - (len(data2) % 4) if len(data2) % 4 != 0 else 0
            writer.write_bytes(b"\0" * padding)

            writer.write_bytes(data3)

        return data

    def test_bif_real_file(self):
        """Test reading a real BIF file."""
        bif: BIF = read_bif(K1_BIF_TEST_FILE)

        # Check header
        self.assertEqual(bif.bif_type, BIFType.BIF, f"{bif.bif_type} != BIFType.BIF")
        self.assertEqual(len(bif.resources), 126, f"{len(bif.resources)} != 126")

        # Check resources
        res1: BIFResource = bif.resources[0]
        self.assertEqual(res1.resname_key_index, 20971520, f"{res1.resname_key_index} != 20971520")
        self.assertEqual(res1.offset, 2036, f"{res1.offset} != 2036")
        self.assertEqual(res1.size, 182290, f"{res1.size} != 182290")
        self.assertEqual(res1.restype, ResourceType.MDL, f"{res1.restype} != ResourceType.MDL")

        res2: BIFResource = bif.resources[1]
        self.assertEqual(res2.resname_key_index, 20971521, f"{res2.resname_key_index} != 20971521")
        self.assertEqual(res2.offset, 184326, f"{res2.offset} != 184326")
        self.assertEqual(res2.size, 144384, f"{res2.size} != 144384")
        self.assertEqual(res2.restype, ResourceType.MDX, f"{res2.restype} != ResourceType.MDX")

    def test_bzf_read(self):
        """Test reading a BZF file."""
        data: bytes = self.create_test_bzf()
        bif: BIF = read_bif(data)

        # Check header
        self.assertEqual(bif.bif_type, BIFType.BZF, f"{bif.bif_type} != BIFType.BZF")
        self.assertEqual(len(bif.resources), 3, f"{len(bif.resources)} != 3")

        # Check resources
        res1: BIFResource = bif.resources[0]
        self.assertEqual(res1.resname_key_index, 0, f"{res1.resname_key_index} != 0")
        self.assertEqual(res1.size, 13, f"{res1.size} != 13")
        self.assertEqual(res1.restype, ResourceType.TXT, f"{res1.restype} != ResourceType.TXT")
        self.assertEqual(res1.data, b"Hello World 1", f"{res1.data} != b'Hello World 1'")

        res2: BIFResource = bif.resources[1]
        self.assertEqual(res2.resname_key_index, 1, f"{res2.resname_key_index} != 1")
        self.assertEqual(res2.size, 13, f"{res2.size} != 13")
        self.assertEqual(res2.restype, ResourceType.TXT, f"{res2.restype} != ResourceType.TXT")
        self.assertEqual(res2.data, b"Hello World 2", f"{res2.data} != b'Hello World 2'")

        res3: BIFResource = bif.resources[2]
        self.assertEqual(res3.resname_key_index, 2, f"{res3.resname_key_index} != 2")
        self.assertEqual(res3.size, 13, f"{res3.size} != 13")
        self.assertEqual(res3.restype, ResourceType.TXT, f"{res3.restype} != ResourceType.TXT")
        self.assertEqual(res3.data, b"Hello World 3", f"{res3.data} != b'Hello World 3'")

    def test_bif_write(self):
        """Test writing a BIF file."""
        # Create test BIF
        bif = BIF()
        bif.bif_type = BIFType.BIF

        res1: BIFResource = BIFResource(ResRef("test1"), ResourceType.TXT, b"Hello World 1", 0)
        res2: BIFResource = BIFResource(ResRef("test2"), ResourceType.TXT, b"Hello World 2", 1)
        res3: BIFResource = BIFResource(ResRef("test3"), ResourceType.TXT, b"Hello World 3", 2)

        bif.resources.extend([res1, res2, res3])

        # Write and read back
        data: bytearray = bytearray(bytes_bif(bif))

        bif2: BIF = read_bif(data)

        # Verify resources
        self.assertEqual(len(bif2.resources), 3)
        self.assertEqual(bif2.resources[0].data, b"Hello World 1", f"{bif2.resources[0].data} != b'Hello World 1'")
        self.assertEqual(bif2.resources[1].data, b"Hello World 2", f"{bif2.resources[1].data} != b'Hello World 2'")
        self.assertEqual(bif2.resources[2].data, b"Hello World 3", f"{bif2.resources[2].data} != b'Hello World 3'")

    def test_bzf_write(self):
        """Test writing a BZF file."""
        # Create test BIF
        bif = BIF()
        bif.bif_type = BIFType.BZF

        res1: BIFResource = BIFResource(ResRef("test1"), ResourceType.TXT, b"Hello World 1", 0)
        res2: BIFResource = BIFResource(ResRef("test2"), ResourceType.TXT, b"Hello World 2", 1)
        res3: BIFResource = BIFResource(ResRef("test3"), ResourceType.TXT, b"Hello World 3", 2)

        bif.resources.extend([res1, res2, res3])

        # Write and read back
        bif2: BIF = read_bif(bytes_bif(bif))

        # Verify resources
        self.assertEqual(len(bif2.resources), 3, f"{len(bif2.resources)} != 3")
        self.assertEqual(bif2.resources[0].data, b"Hello World 1", f"{bif2.resources[0].data} != b'Hello World 1'")
        self.assertEqual(bif2.resources[1].data, b"Hello World 2", f"{bif2.resources[1].data} != b'Hello World 2'")
        self.assertEqual(bif2.resources[2].data, b"Hello World 3", f"{bif2.resources[2].data} != b'Hello World 3'")

if __name__ == "__main__":
    unittest.main()
