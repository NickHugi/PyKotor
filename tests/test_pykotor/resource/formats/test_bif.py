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




class TestBIFFormats(unittest.TestCase):
    def create_test_bif(self) -> bytes:
        """Create a test BIF file with known content."""
        data: bytearray = bytearray()
        with BinaryWriter.to_bytearray(data) as writer:
            # Write header
            writer.write_string("BIFFV1  ")  # Signature
            writer.write_uint32(3)  # Variable resource count
            writer.write_uint32(0)  # Fixed resource count
            writer.write_uint32(20)  # Variable table offset
            writer.write_uint32(0)  # Reserved

            # Write resource table
            data_offset: int = 20 + (3 * 16)  # Header + (3 resources * 16 bytes per entry)

            # Resource 1
            writer.write_uint32(0)  # ID
            writer.write_uint32(0)  # Offset from data section
            writer.write_uint32(13)  # Size
            writer.write_uint32(2002)  # Type (TXT)

            # Resource 2
            writer.write_uint32(1)  # ID
            writer.write_uint32(16)  # Offset (aligned to 4 bytes)
            writer.write_uint32(13)  # Size
            writer.write_uint32(2002)  # Type (TXT)

            # Resource 3
            writer.write_uint32(2)  # ID
            writer.write_uint32(32)  # Offset (aligned to 4 bytes)
            writer.write_uint32(13)  # Size
            writer.write_uint32(2002)  # Type (TXT)

            # Write resource data
            writer.write_string("Hello World 1")
            writer.write_bytes(b"\0" * 3)  # Padding to 4 bytes
            writer.write_string("Hello World 2")
            writer.write_bytes(b"\0" * 3)  # Padding to 4 bytes
            writer.write_string("Hello World 3")

        return data

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

    def test_bif_read(self):
        """Test reading a BIF file."""
        data: bytes = self.create_test_bif()
        bif: BIF = read_bif(data)

        # Check header
        self.assertEqual(bif.bif_type, BIFType.BIF, f"{bif.bif_type} != BIFType.BIF")
        self.assertEqual(len(bif.resources), 3, f"{len(bif.resources)} != 3")

        # Check resources
        res1: BIFResource = bif.resources[0]
        self.assertEqual(res1.resource_id, 0, f"{res1.resource_id} != 0")
        self.assertEqual(res1.offset, 0, f"{res1.offset} != 0")
        self.assertEqual(res1.size, 13, f"{res1.size} != 13")
        self.assertEqual(res1.restype, ResourceType.TXT, f"{res1.restype} != ResourceType.TXT")
        self.assertEqual(res1.data, b"Hello World 1", f"{res1.data} != b'Hello World 1'")

        res2: BIFResource = bif.resources[1]
        self.assertEqual(res2.resource_id, 1, f"{res2.resource_id} != 1")
        self.assertEqual(res2.offset, 16, f"{res2.offset} != 16")
        self.assertEqual(res2.size, 13, f"{res2.size} != 13")
        self.assertEqual(res2.restype, ResourceType.TXT, f"{res2.restype} != ResourceType.TXT")
        self.assertEqual(res2.data, b"Hello World 2", f"{res2.data} != b'Hello World 2'")

        res3: BIFResource = bif.resources[2]
        self.assertEqual(res3.resource_id, 2, f"{res3.resource_id} != 2")
        self.assertEqual(res3.offset, 32, f"{res3.offset} != 32")
        self.assertEqual(res3.size, 13, f"{res3.size} != 13")
        self.assertEqual(res3.restype, ResourceType.TXT, f"{res3.restype} != ResourceType.TXT")
        self.assertEqual(res3.data, b"Hello World 3", f"{res3.data} != b'Hello World 3'")

    def test_bzf_read(self):
        """Test reading a BZF file."""
        data: bytes = self.create_test_bzf()
        bif: BIF = read_bif(data)

        # Check header
        self.assertEqual(bif.bif_type, BIFType.BZF, f"{bif.bif_type} != BIFType.BZF")
        self.assertEqual(len(bif.resources), 3, f"{len(bif.resources)} != 3")

        # Check resources
        res1: BIFResource = bif.resources[0]
        self.assertEqual(res1.resource_id, 0, f"{res1.resource_id} != 0")
        self.assertEqual(res1.size, 13, f"{res1.size} != 13")
        self.assertEqual(res1.restype, ResourceType.TXT, f"{res1.restype} != ResourceType.TXT")
        self.assertEqual(res1.data, b"Hello World 1", f"{res1.data} != b'Hello World 1'")

        res2: BIFResource = bif.resources[1]
        self.assertEqual(res2.resource_id, 1, f"{res2.resource_id} != 1")
        self.assertEqual(res2.size, 13, f"{res2.size} != 13")
        self.assertEqual(res2.restype, ResourceType.TXT, f"{res2.restype} != ResourceType.TXT")
        self.assertEqual(res2.data, b"Hello World 2", f"{res2.data} != b'Hello World 2'")

        res3: BIFResource = bif.resources[2]
        self.assertEqual(res3.resource_id, 2, f"{res3.resource_id} != 2")
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
        data: bytearray = bytearray(bytes_bif(bif))

        bif2: BIF = read_bif(data)

        # Verify resources
        self.assertEqual(len(bif2.resources), 3, f"{len(bif2.resources)} != 3")
        self.assertEqual(bif2.resources[0].data, b"Hello World 1", f"{bif2.resources[0].data} != b'Hello World 1'")
        self.assertEqual(bif2.resources[1].data, b"Hello World 2", f"{bif2.resources[1].data} != b'Hello World 2'")
        self.assertEqual(bif2.resources[2].data, b"Hello World 3", f"{bif2.resources[2].data} != b'Hello World 3'")

    def test_invalid_signature(self):
        """Test handling invalid file signature."""
        data: bytearray = bytearray()
        with BinaryWriter.to_bytearray(data) as writer:
            writer.write_string("INVALID!")

        with self.assertRaises(ValueError):
            read_bif(data)

    def test_invalid_version(self):
        """Test handling invalid version."""
        data: bytearray = bytearray()
        with BinaryWriter.to_bytearray(data) as writer:
            writer.write_string("BIFFV2  ")

        with self.assertRaises(ValueError):
            read_bif(data)

    def test_fixed_resources(self):
        """Test handling fixed resources (not supported)."""
        data = bytearray()
        with BinaryWriter.to_bytearray(data) as writer:
            writer.write_string("BIFFV1  ")
            writer.write_uint32(0)  # Var resources
            writer.write_uint32(1)  # Fixed resources

        with self.assertRaises(ValueError):
            read_bif(data)

    def test_resource_size_mismatch(self):
        """Test handling size mismatch in BZF decompression."""
        data: bytearray = bytearray(self.create_test_bzf())

        # Corrupt the uncompressed size of first resource
        data[28] = 999  # Offset to first resource size

        with self.assertRaises(ValueError):
            read_bif(data)

    def test_bif_basic_structure(self) -> None:
        """Test reading a basic BIF file structure (ported from reone tests)."""
        # Create test data matching reone's test case
        data = (
            b"BIFFV1  "  # Signature
            b"\x01\x00\x00\x00"  # Variable resource count (1)
            b"\x00\x00\x00\x00"  # Fixed resource count (0)
            b"\x14\x00\x00\x00"  # Offset to variable resources (20)
            b"\x00\x00\x00\x00"  # Reserved
            # Variable resource table
            b"\x00\x00\x00\x00"  # ID
            b"\x24\x00\x00\x00"  # Offset (36)
            b"\x0d\x00\x00\x00"  # Size (13)
            b"\xe6\x07\x00\x00"  # Type (2022)
            b"Hello, world!"  # Resource data
        )

        # Read using our implementation
        reader = BIFBinaryReader(io.BytesIO(data))
        bif = reader.load()

        # Verify structure matches
        assert len(bif.resources) == 1
        resource = bif.resources[0]
        assert resource.resource_id == 0
        assert resource.offset == 36
        assert resource.size == 13
        assert resource.restype == ResourceType.from_id(2022)
        assert resource.data == b"Hello, world!"


    def test_bif_size_preservation(self) -> None:
        """Test that BIF read/write preserves file size (ported from KotOR_IO tests)."""
        # Create test BIF data
        original_data = (
            b"BIFFV1  "  # Signature
            b"\x02\x00\x00\x00"  # Variable resource count (2)
            b"\x00\x00\x00\x00"  # Fixed resource count (0)
            b"\x14\x00\x00\x00"  # Offset to variable resources (20)
            b"\x00\x00\x00\x00"  # Reserved
            # Variable resource table
            b"\x01\x00\x00\x00"  # ID 1
            b"\x34\x00\x00\x00"  # Offset (52)
            b"\x0d\x00\x00\x00"  # Size (13)
            b"\xe6\x07\x00\x00"  # Type (2022)
            b"\x02\x00\x00\x00"  # ID 2
            b"\x41\x00\x00\x00"  # Offset (65)
            b"\x0e\x00\x00\x00"  # Size (14)
            b"\xe7\x07\x00\x00"  # Type (2023)
            b"Hello, world!"  # Resource 1 data
            b"Hello, world!!"  # Resource 2 data
        )

        # Read the BIF
        reader = BIFBinaryReader(io.BytesIO(original_data))
        bif = reader.load()

        # Write to new buffer
        output = io.BytesIO()
        writer = BIFBinaryWriter(bif, output)
        writer.write()

        # Compare sizes
        assert len(original_data) == len(output.getvalue())


    def test_bif_roundtrip(self) -> None:
        """Test that BIF data survives a read/write cycle unchanged."""
        # Create a BIF with test resources
        bif = BIF()
        
        # Add test resources
        res1 = BIFResource(ResRef("test1"), ResourceType.UTC, b"Test Data 1", 1)
        res2 = BIFResource(ResRef("test2"), ResourceType.DLG, b"Test Data 2", 2)
        bif.resources.extend([res1, res2])

        # Write to buffer
        output = io.BytesIO()
        writer = BIFBinaryWriter(bif, output)
        writer.write()
        written_data: bytes = output.getvalue()

        # Read back
        reader = BIFBinaryReader(io.BytesIO(written_data))
        read_bif: BIF = reader.load()

        # Compare resources
        assert len(read_bif.resources) == len(bif.resources)
        for orig_res, read_res in zip(bif.resources, read_bif.resources):
            assert orig_res.resource_id == read_res.resource_id
            assert orig_res.restype == read_res.restype
            assert orig_res.data == read_res.data


    def test_bzf_basic_structure(self) -> None:
        """Test reading a basic BZF (compressed BIF) file structure."""
        import lzma

        # Create compressed test data
        uncompressed = b"Hello, compressed world!"
        compressed: bytes = lzma.compress(uncompressed)
        
        data: bytes = (
            b"BZF V1  "  # Signature
            b"\x01\x00\x00\x00"  # Variable resource count (1)
            b"\x00\x00\x00\x00"  # Fixed resource count (0)
            b"\x14\x00\x00\x00"  # Offset to variable resources (20)
            b"\x00\x00\x00\x00"  # Reserved
            # Variable resource table
            b"\x00\x00\x00\x00"  # ID
            b"\x24\x00\x00\x00"  # Offset (36)
            b"\x17\x00\x00\x00"  # Uncompressed size (23)
            b"\xe6\x07\x00\x00"  # Type (2022)
        ) + compressed

        # Read using our implementation
        reader = BIFBinaryReader(io.BytesIO(data))
        bzf: BIF = reader.load()

        # Verify structure matches
        assert bzf.bif_type == BIFType.BZF
        assert len(bzf.resources) == 1
        resource: BIFResource = bzf.resources[0]
        assert resource.resource_id == 0
        assert resource.offset == 36
        assert resource.size == len(uncompressed)
        assert resource.restype == ResourceType.from_id(2022)
        assert resource.data == uncompressed
        assert resource.packed_size == len(compressed)


    def test_bzf_roundtrip(self) -> None:
        """Test that BZF data survives a read/write cycle unchanged."""
        # Create a BZF with test resources
        bzf = BIF(BIFType.BZF)
        
        # Add test resources
        res1 = BIFResource(ResRef("test1"), ResourceType.UTC, b"Test Compressed Data 1", 1)
        res2 = BIFResource(ResRef("test2"), ResourceType.DLG, b"Test Compressed Data 2", 2)
        bzf.resources.extend([res1, res2])

        # Write to buffer
        output = io.BytesIO()
        writer = BIFBinaryWriter(bzf, output)
        writer.write()
        written_data: bytes = output.getvalue()

        # Read back
        reader = BIFBinaryReader(io.BytesIO(written_data))
        read_bzf: BIF = reader.load()

        # Compare resources
        assert read_bzf.bif_type == BIFType.BZF
        assert len(read_bzf.resources) == len(bzf.resources)
        for orig_res, read_res in zip(bzf.resources, read_bzf.resources):
            assert orig_res.resource_id == read_res.resource_id
            assert orig_res.restype == read_res.restype
            assert orig_res.data == read_res.data


    def test_bif_invalid_signature(self) -> None:
        """Test handling of invalid BIF signatures."""
        data = b"INVALID!" + b"\x00" * 100  # Invalid signature
        
        with pytest.raises(ValueError, match="Invalid BIF/BZF file type"):
            reader = BIFBinaryReader(io.BytesIO(data))
            reader.load()


    def test_bif_invalid_version(self) -> None:
        """Test handling of invalid BIF versions."""
        data = b"BIFFV2  " + b"\x00" * 100  # Invalid version
        
        with pytest.raises(ValueError, match="Unsupported BIF/BZF version"):
            reader = BIFBinaryReader(io.BytesIO(data))
            reader.load()


    def test_bif_fixed_resources(self) -> None:
        """Test handling of fixed resources (which are not supported)."""
        data = (
            b"BIFFV1  "  # Signature
            b"\x00\x00\x00\x00"  # Variable resource count (0)
            b"\x01\x00\x00\x00"  # Fixed resource count (1) - not supported
            b"\x14\x00\x00\x00"  # Offset
            b"\x00\x00\x00\x00"  # Reserved
        )
        
        with pytest.raises(ValueError, match="Fixed resources not supported"):
            reader = BIFBinaryReader(io.BytesIO(data))
            reader.load()


    def test_bzf_decompression_error(self) -> None:
        """Test handling of invalid compressed data in BZF."""
        data = (
            b"BZF V1  "  # Signature
            b"\x01\x00\x00\x00"  # Variable resource count (1)
            b"\x00\x00\x00\x00"  # Fixed resource count (0)
            b"\x14\x00\x00\x00"  # Offset (20)
            b"\x00\x00\x00\x00"  # Reserved
            # Variable resource table
            b"\x00\x00\x00\x00"  # ID
            b"\x24\x00\x00\x00"  # Offset (36)
            b"\x0d\x00\x00\x00"  # Size (13)
            b"\xe6\x07\x00\x00"  # Type (2022)
            b"Invalid LZMA data"  # Invalid compressed data
        )
        
        with pytest.raises(ValueError, match="Failed to decompress BZF resource"):
            reader = BIFBinaryReader(io.BytesIO(data))
            reader.load()


    def test_bzf_ozymandias(self) -> None:
        """Test reading a BZF file containing Ozymandias (from xoreos-tools tests)."""
        # Percy Bysshe Shelley's "Ozymandias"
        poem = (
            "I met a traveller from an antique land\n"
            "Who said: Two vast and trunkless legs of stone\n"
            "Stand in the desert. Near them, on the sand,\n"
            "Half sunk, a shattered visage lies, whose frown,\n"
            "And wrinkled lip, and sneer of cold command,\n"
            "Tell that its sculptor well those passions read\n"
            "Which yet survive, stamped on these lifeless things,\n"
            "The hand that mocked them and the heart that fed:\n"
            "And on the pedestal these words appear:\n"
            "'My name is Ozymandias, king of kings:\n"
            "Look on my works, ye Mighty, and despair!'\n"
            "Nothing beside remains. Round the decay\n"
            "Of that colossal wreck, boundless and bare\n"
            "The lone and level sands stretch far away."
        ).encode('ascii')

        # BZF file containing compressed Ozymandias
        bzf_data = bytes([
            0x42,0x49,0x46,0x46,0x56,0x31,0x20,0x20,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
            0x14,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x24,0x00,0x00,0x00,0x6F,0x02,0x00,0x00,
            0x0A,0x00,0x00,0x00,0x5D,0x00,0x00,0x00,0x01,0x00,0x24,0x88,0x09,0xA6,0x53,0xD8,
            0x61,0x0F,0xAE,0x55,0xA9,0x63,0x39,0x41,0xFC,0x9F,0xD4,0xA8,0x78,0x14,0xAC,0xE4,
            0x2B,0xCC,0x0A,0x14,0xAF,0x12,0x42,0x25,0xBC,0xEF,0xA4,0x3C,0x92,0x2C,0xC3,0x41,
            0x1E,0x0C,0x7E,0xAB,0x97,0x95,0x4B,0xE0,0x18,0xFC,0x32,0xE0,0x7E,0xAC,0x35,0xED,
            0x0D,0xE8,0x9D,0xFA,0xB0,0x7D,0xCD,0x26,0x2B,0x71,0xF2,0xC4,0xCF,0x31,0x2C,0xF9,
            0xD8,0xEC,0xFB,0xFC,0xF5,0x7E,0x9E,0x1C,0x36,0xB0,0x30,0x72,0xE7,0x43,0xD8,0x64,
            0xA9,0x22,0x29,0xDD,0x62,0xB2,0x19,0xB5,0x01,0xBD,0xC0,0x21,0xF2,0xEC,0x1C,0xF3,
            0x58,0xF0,0xBD,0x95,0xBA,0xA0,0xBA,0xC4,0x6E,0xB2,0xDC,0x30,0x18,0x5E,0xA0,0x6F,
            0x72,0x03,0x57,0x1B,0x8B,0xE6,0x63,0x39,0x72,0x58,0xE3,0xE8,0x70,0xE3,0x91,0xD1,
            0x0A,0x95,0x8E,0xC3,0x34,0x79,0x10,0x27,0x5F,0x5A,0xFE,0xAA,0x27,0xCA,0xF2,0x15,
            0x1C,0x6C,0x72,0x86,0xE1,0xE1,0x4A,0x57,0x1C,0xA3,0x76,0x66,0xF6,0x6A,0xC5,0xD8,
            0x7E,0xEE,0x04,0x0C,0x98,0x6E,0x4D,0x70,0xBB,0x98,0xD9,0x59,0xD4,0xD0,0x25,0x34,
            0x7D,0x76,0xCF,0x02,0x40,0xD7,0x78,0x47,0xC0,0xE0,0x4E,0xD2,0xF7,0x05,0x45,0x16,
            0x3F,0x2E,0xDD,0xAC,0x68,0x60,0xE3,0x49,0x96,0x36,0xA7,0x52,0x22,0xEE,0x42,0xC8,
            0x6E,0x9A,0x14,0x20,0xD7,0x03,0x35,0x25,0xF7,0xAB,0x8A,0x8B,0x38,0x9F,0xBF,0x79,
            0x81,0x0B,0x3A,0x7B,0xA1,0x55,0xF2,0xF5,0xF6,0x7E,0xA5,0x47,0x34,0xAF,0x22,0x82,
            0x9A,0xFF,0xB1,0x93,0xCF,0x47,0x98,0x63,0xF4,0x11,0xC8,0xD0,0x48,0x3F,0xC5,0xC9,
            0x1E,0xAD,0x4F,0x88,0xBF,0x57,0x40,0xB0,0x7E,0xA2,0xB5,0xC8,0xA7,0x0B,0x64,0x83,
            0xD7,0xAB,0x8A,0x33,0xA6,0x64,0xEA,0x2B,0xCF,0x41,0x96,0x92,0xF5,0x7B,0x66,0x48,
            0xA3,0x53,0x9D,0x01,0x4F,0xC3,0xDF,0xA3,0x85,0x54,0x45,0x65,0xA9,0x3C,0x20,0x31,
            0x02,0x55,0xDB,0x64,0x33,0x50,0x19,0x7A,0x58,0x64,0x87,0x72,0xF6,0x12,0x05,0xA3,
            0x83,0xFC,0xB4,0x0E,0x28,0x5B,0x5C,0x17,0x57,0xB3,0xD8,0xF7,0xBE,0x1D,0xDF,0x96,
            0x32,0x36,0xA0,0xFE,0x51,0x56,0x2D,0x84,0x2B,0xCA,0x2B,0x85,0x53,0x71,0xC1,0x33,
            0x3B,0xD2,0x77,0x2F,0xB3,0x9E,0x87,0x71,0x8A,0x01,0x94,0x26,0x53,0x11,0x73,0x21,
            0xB5,0xD4,0x15,0xFB,0xAC,0xC3,0xE7,0xA5,0x0A,0x09,0xF4,0x36,0x5B,0x88,0x25,0x51,
            0x0C,0x12,0xB5,0x09,0x8A,0x78,0x57,0x5A,0xCC,0x20,0x13,0xC3,0xFD,0xC2,0x1E,0xF9,
            0xA6,0xF4,0xA1,0x77,0xB2,0xAD,0xD3,0x6B,0xEF,0xB9,0xF7,0xA1,0x28,0x8A,0xB4,0x3D,
            0xCE,0x54,0xDA,0x78,0xFF,0xF8,0x6E,0xCB,0x5F
        ])

        # Read the BZF
        reader = BIFBinaryReader(io.BytesIO(bzf_data))
        bzf = reader.load()

        # Verify structure
        assert bzf.bif_type == BIFType.BZF
        assert len(bzf.resources) == 1
        
        # Verify resource
        resource: BIFResource = bzf.resources[0]
        assert resource.resource_id == 0
        assert resource.offset == 36
        assert resource.size == len(poem)
        assert resource.restype == ResourceType.from_id(10)  # TXT file
        assert resource.data == poem
        assert resource.packed_size == 93  # Size of compressed data


    def test_bzf_key_merge(self) -> None:
        """Test merging KEY file information with BZF (from xoreos-tools tests)."""
        # KEY file data from xoreos-tools tests
        key_data = bytes([
            0x4B,0x45,0x59,0x20,0x56,0x31,0x20,0x20,0x01,0x00,0x00,0x00,0x01,0x00,0x00,0x00,
            0x40,0x00,0x00,0x00,0x56,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
            0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
            0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
            0x00,0x00,0x00,0x00,0x4C,0x00,0x00,0x00,0x0A,0x00,0x00,0x00,0x78,0x6F,0x72,0x65,
            0x6F,0x73,0x2E,0x6A,0x69,0x66,0x6F,0x7A,0x79,0x6D,0x61,0x6E,0x64,0x69,0x61,0x73,
            0x00,0x00,0x00,0x00,0x00,0x00,0x0A,0x00,0x00,0x00,0x00,0x00
        ])

        # Create KEY and BZF objects
        from pykotor.resource.formats.key import KEY
        from pykotor.resource.formats.key.io_key import KEYBinaryReader
        
        key_reader = KEYBinaryReader(io.BytesIO(key_data))
        key = key_reader.load()

        bzf_reader = BIFBinaryReader(io.BytesIO(bzf_data))
        bzf = bzf_reader.load()

        # Merge KEY information
        bzf.merge_key(key, 0)

        # Verify resource information
        assert len(bzf.resources) == 1
        resource = bzf.resources[0]
        assert resource.resref == ResRef("ozymandias")
        assert resource.restype == ResourceType.TXT
        assert resource.resource_id == 0


if __name__ == "__main__":
    unittest.main()

