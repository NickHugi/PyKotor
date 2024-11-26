from __future__ import annotations

import lzma
import pytest

from pykotor.common.misc import ResRef
from pykotor.common.stream import BinaryWriter
from pykotor.resource.formats.bif.bif_auto import read_bif, write_bif, bytes_bif
from pykotor.resource.formats.bif.bif_data import BIF, BIFResource, BIFType
from pykotor.resource.type import ResourceType


def create_test_bif() -> bytes:
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


def create_test_bzf() -> bytes:
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


def test_bif_read():
    """Test reading a BIF file."""
    data: bytes = create_test_bif()
    bif: BIF = read_bif(data)
    
    # Check header
    assert bif.bif_type == BIFType.BIF, f"{bif.bif_type} != BIFType.BIF"
    assert len(bif.resources) == 3, f"{len(bif.resources)} != 3"
    
    # Check resources
    res1: BIFResource = bif.resources[0]
    assert res1.resource_id == 0, f"{res1.resource_id} != 0"
    assert res1.offset == 0, f"{res1.offset} != 0"
    assert res1.size == 13, f"{res1.size} != 13"
    assert res1.restype == ResourceType.TXT, f"{res1.restype} != ResourceType.TXT"
    assert res1.data == b"Hello World 1", f"{res1.data} != b'Hello World 1'"
    
    res2: BIFResource = bif.resources[1]
    assert res2.resource_id == 1, f"{res2.resource_id} != 1"
    assert res2.offset == 16, f"{res2.offset} != 16"
    assert res2.size == 13, f"{res2.size} != 13"
    assert res2.restype == ResourceType.TXT, f"{res2.restype} != ResourceType.TXT"
    assert res2.data == b"Hello World 2", f"{res2.data} != b'Hello World 2'"
    
    res3: BIFResource = bif.resources[2]
    assert res3.resource_id == 2, f"{res3.resource_id} != 2"
    assert res3.offset == 32, f"{res3.offset} != 32"
    assert res3.size == 13, f"{res3.size} != 13"
    assert res3.restype == ResourceType.TXT, f"{res3.restype} != ResourceType.TXT"
    assert res3.data == b"Hello World 3", f"{res3.data} != b'Hello World 3'"


def test_bzf_read():
    """Test reading a BZF file."""
    data: bytes = create_test_bzf()
    bif: BIF = read_bif(data)
    
    # Check header
    assert bif.bif_type == BIFType.BZF, f"{bif.bif_type} != BIFType.BZF"
    assert len(bif.resources) == 3, f"{len(bif.resources)} != 3"
    
    # Check resources
    res1: BIFResource = bif.resources[0]
    assert res1.resource_id == 0, f"{res1.resource_id} != 0"
    assert res1.size == 13, f"{res1.size} != 13"
    assert res1.restype == ResourceType.TXT, f"{res1.restype} != ResourceType.TXT"
    assert res1.data == b"Hello World 1", f"{res1.data} != b'Hello World 1'"
    
    res2: BIFResource = bif.resources[1]
    assert res2.resource_id == 1, f"{res2.resource_id} != 1"
    assert res2.size == 13, f"{res2.size} != 13"
    assert res2.restype == ResourceType.TXT, f"{res2.restype} != ResourceType.TXT"
    assert res2.data == b"Hello World 2", f"{res2.data} != b'Hello World 2'"
    
    res3: BIFResource = bif.resources[2]
    assert res3.resource_id == 2, f"{res3.resource_id} != 2"
    assert res3.size == 13, f"{res3.size} != 13"
    assert res3.restype == ResourceType.TXT, f"{res3.restype} != ResourceType.TXT"
    assert res3.data == b"Hello World 3", f"{res3.data} != b'Hello World 3'"


def test_bif_write():
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
    assert len(bif2.resources) == 3
    assert bif2.resources[0].data == b"Hello World 1", f"{bif2.resources[0].data} != b'Hello World 1'"
    assert bif2.resources[1].data == b"Hello World 2", f"{bif2.resources[1].data} != b'Hello World 2'"
    assert bif2.resources[2].data == b"Hello World 3", f"{bif2.resources[2].data} != b'Hello World 3'"


def test_bzf_write():
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
    assert len(bif2.resources) == 3, f"{len(bif2.resources)} != 3"
    assert bif2.resources[0].data == b"Hello World 1", f"{bif2.resources[0].data} != b'Hello World 1'"
    assert bif2.resources[1].data == b"Hello World 2", f"{bif2.resources[1].data} != b'Hello World 2'"
    assert bif2.resources[2].data == b"Hello World 3", f"{bif2.resources[2].data} != b'Hello World 3'"


def test_invalid_signature():
    """Test handling invalid file signature."""
    data: bytearray = bytearray()
    with BinaryWriter.to_bytearray(data) as writer:
        writer.write_string("INVALID!")
    
    with pytest.raises(ValueError):
        read_bif(data)


def test_invalid_version():
    """Test handling invalid version."""
    data: bytearray = bytearray()
    with BinaryWriter.to_bytearray(data) as writer:
        writer.write_string("BIFFV2  ")
    
    with pytest.raises(ValueError):
        read_bif(data)


def test_fixed_resources():
    """Test handling fixed resources (not supported)."""
    data = bytearray()
    with BinaryWriter.to_bytearray(data) as writer:
        writer.write_string("BIFFV1  ")
        writer.write_uint32(0)  # Var resources
        writer.write_uint32(1)  # Fixed resources
    
    with pytest.raises(ValueError):
        read_bif(data)


def test_resource_size_mismatch():
    """Test handling size mismatch in BZF decompression."""
    data: bytearray = bytearray(create_test_bzf())
    
    # Corrupt the uncompressed size of first resource
    data[28] = 999  # Offset to first resource size
    
    with pytest.raises(ValueError):
        read_bif(data)
