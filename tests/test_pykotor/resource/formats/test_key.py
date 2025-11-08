from __future__ import annotations

import io
from unittest import TestCase

from pykotor.resource.type import ResourceType
from pykotor.resource.formats.key import KEY, BifEntry, KeyEntry, KEYBinaryWriter, KEYBinaryReader


class TestKEY(TestCase):
    """Test KEY file reading and writing."""

    def test_write_key(self):
        """Test writing and reading back a KEY file."""
        # Create a new KEY file
        key = KEY()

        # Add two BIFs with test resources
        key.add_bif("test1.bif", 30, 0)
        key.add_bif("test2.bif", 20, 0)

        # Add resources to first BIF
        key.add_key_entry("test1", ResourceType.TXT, 0, 0)
        key.add_key_entry("test2", ResourceType.TXT, 0, 1)
        key.add_key_entry("test3", ResourceType.TXT, 0, 2)

        # Add resources to second BIF
        key.add_key_entry("test4", ResourceType.TXT, 1, 0)
        key.add_key_entry("test5", ResourceType.TXT, 1, 1)

        # Write to memory stream
        data: bytearray = bytearray()
        writer = KEYBinaryWriter(key, data)
        writer.write()

        reader = KEYBinaryReader(data)
        key_read: KEY = reader.load()

        # Verify BIF entries
        assert len(key_read.bif_entries) == 2, f"{len(key_read.bif_entries)} != 2"
        assert key_read.bif_entries[0].filename == "test1.bif", f"{key_read.bif_entries[0].filename!r} != 'test1.bif'"
        assert key_read.bif_entries[1].filename == "test2.bif", f"{key_read.bif_entries[1].filename!r} != 'test2.bif'"

        # Verify resource entries
        assert len(key_read.key_entries) == 5, f"{len(key_read.key_entries)} != 5"

        # First BIF resources
        res1: KeyEntry | None = key_read.get_resource("test1", ResourceType.TXT)
        assert res1 is not None, "Resource 1 not found under name 'test1' and type ResourceType.TXT"
        assert str(res1.resref) == "test1", f"{res1.resref!r} != 'test1'"
        assert res1.restype == ResourceType.TXT, f"{res1.restype!r} != {ResourceType.TXT!r}"
        assert res1.bif_index == 0, f"{res1.bif_index} != 0"
        assert res1.res_index == 0, f"{res1.res_index} != 0"

        res2: KeyEntry | None = key_read.get_resource("test2", ResourceType.TXT)
        assert res2 is not None, "Resource 2 not found under name 'test2' and type ResourceType.TXT"
        assert str(res2.resref) == "test2", f"{res2.resref!r} != 'test2'"
        assert res2.restype == ResourceType.TXT, f"{res2.restype!r} != {ResourceType.TXT!r}"
        assert res2.bif_index == 0, f"{res2.bif_index} != 0"
        assert res2.res_index == 1, f"{res2.res_index} != 1"

        res3: KeyEntry | None = key_read.get_resource("test3", ResourceType.TXT)
        assert res3 is not None, "Resource 3 not found under name 'test3' and type ResourceType.TXT"
        assert str(res3.resref) == "test3", f"{res3.resref!r} != 'test3'"
        assert res3.restype == ResourceType.TXT, f"{res3.restype!r} != {ResourceType.TXT!r}"
        assert res3.bif_index == 0, f"{res3.bif_index} != 0"
        assert res3.res_index == 2, f"{res3.res_index} != 2"

        # Second BIF resources
        res4: KeyEntry | None = key_read.get_resource("test4", ResourceType.TXT)
        assert res4 is not None, "Resource 4 not found under name 'test4' and type ResourceType.TXT"
        assert str(res4.resref) == "test4", f"{res4.resref!r} != 'test4'"
        assert res4.restype == ResourceType.TXT, f"{res4.restype!r} != {ResourceType.TXT!r}"
        assert res4.bif_index == 1, f"{res4.bif_index} != 1"
        assert res4.res_index == 0, f"{res4.res_index} != 0"

        res5: KeyEntry | None = key_read.get_resource("test5", ResourceType.TXT)
        assert res5 is not None, "Resource 5 not found under name 'test5' and type ResourceType.TXT"
        assert str(res5.resref) == "test5", f"{res5.resref!r} != 'test5'"
        assert res5.restype == ResourceType.TXT, f"{res5.restype!r} != {ResourceType.TXT!r}"
        assert res5.bif_index == 1, f"{res5.bif_index} != 1"
        assert res5.res_index == 1, f"{res5.res_index} != 1"

    def test_key_multiple_resources(self):
        """Test KEY file with multiple resources."""
        key = KEY()

        # Add multiple BIFs and resources
        key.add_bif("data/bif1.bif", 100)
        key.add_bif("data/bif2.bif", 200)

        key.add_key_entry("res1", ResourceType.TXT, 0, 0)
        key.add_key_entry("res2", ResourceType.TXT, 0, 1)
        key.add_key_entry("res3", ResourceType.TXT, 1, 0)

        # Write and read back
        data: bytearray = bytearray()
        KEYBinaryWriter(key, data).write()

        key2: KEY = KEYBinaryReader(data).load()

        # Verify
        assert len(key2.bif_entries) == 2, f"{len(key2.bif_entries)} != 2"
        assert len(key2.key_entries) == 3, f"{len(key2.key_entries)} != 3"

    def test_key_v1_write(self):
        """Test writing a KEY V1.0 file."""
        # Create KEY file
        key: KEY = KEY()

        # Add BIF entry
        bif: BifEntry = key.add_bif("data\\xoreos.bif", 76)

        # Add resource entry
        entry: KeyEntry = key.add_key_entry("ozymandias", ResourceType.TXT, 0, 1)

        # Write KEY file
        data: bytearray = bytearray()
        KEYBinaryWriter(key, data).write()

        # Read back and verify
        key2: KEY = KEYBinaryReader(data).load()
        assert len(key2.bif_entries) == 1, f"{len(key2.bif_entries)} != 1"
        assert key2.bif_entries[0].filename == bif.filename, f"{key2.bif_entries[0].filename!r} != {bif.filename!r}"
        assert key2.bif_entries[0].filesize == bif.filesize, f"{key2.bif_entries[0].filesize} != {bif.filesize}"
        assert len(key2.key_entries) == 1, f"{len(key2.key_entries)} != 1"
        entry2: KeyEntry = key2.key_entries[0]
        assert str(entry2.resref) == str(entry.resref), f"{str(entry2.resref)!r} != {str(entry.resref)!r}"
        assert entry2.restype == entry.restype, f"{entry2.restype!r} != {entry.restype!r}"
        assert entry2.bif_index == entry.bif_index, f"{entry2.bif_index} != {entry.bif_index}"
        assert entry2.res_index == entry.res_index, f"{entry2.res_index} != {entry.res_index}"
        assert entry2.resource_id == entry.resource_id, f"{entry2.resource_id} != {entry.resource_id}"

    def test_key_invalid_type(self):
        """Test reading a KEY file with invalid type."""
        data = bytearray([0x49, 0x4E, 0x56, 0x20])  # "INV "

        with self.assertRaises(ValueError) as context:
            key: KEY = KEYBinaryReader(data).load()

        assert "Tried to save or load an unsupported or corrupted file." in str(context.exception), f"{str(context.exception)!r} does not contain 'Tried to save or load an unsupported or corrupted file.'"

    def test_key_invalid_version(self):
        """Test reading a KEY file with invalid version."""
        data = bytearray(
            [
                0x4B,
                0x45,
                0x59,
                0x20,  # "KEY "
                0x56,
                0x32,
                0x20,
                0x20,  # "V2  "
            ]
        )
        stream = io.BytesIO(data)

        with self.assertRaises(ValueError) as context:
            KEYBinaryReader(stream).load()

        assert "Tried to save or load an unsupported or corrupted file." in str(context.exception), f"{str(context.exception)!r} does not contain 'Tried to save or load an unsupported or corrupted file.'"

    def test_key_create_empty(self):
        """Test creating an empty KEY file."""
        key: KEY = KEY()
        assert key.file_type == KEY.FILE_TYPE, f"{key.file_type!r} != {KEY.FILE_TYPE!r}"
        assert key.file_version == KEY.FILE_VERSION, f"{key.file_version} != {KEY.FILE_VERSION}"
        assert len(key.bif_entries) == 0, f"{len(key.bif_entries)} != 0"
        assert len(key.key_entries) == 0, f"{len(key.key_entries)} != 0"
        assert not key.is_modified, "KEY is modified"

    def test_key_add_bif(self):
        """Test adding BIF entries."""
        key = KEY()

        # Add test BIF
        bif: BifEntry = key.add_bif("data/test.bif", 1024)

        assert len(key.bif_entries) == 1, f"{len(key.bif_entries)} != 1"
        assert key.is_modified, "KEY is not modified"
        assert bif.filename == "data/test.bif", f"{bif.filename!r} != 'data/test.bif'"
        assert bif.filesize == 1024, f"{bif.filesize} != 1024"

        # Verify BIF lookup
        assert key.get_bif("data/test.bif") == bif, f"{key.get_bif('data/test.bif')!r} != {bif!r}"
        assert key.get_bif("invalid.bif") is None, "BIF lookup should return None for invalid BIF"

    def test_key_remove_bif(self):
        """Test removing BIF entries."""
        key = KEY()

        # Add BIF and associated resources
        bif: BifEntry = key.add_bif("test.bif")
        key.add_key_entry(bif.filename, ResourceType.TXT, 0, 1)

        # Remove BIF
        key.remove_bif(bif)

        assert len(key.bif_entries) == 0, f"{len(key.bif_entries)} != 0"
        assert len(key.key_entries) == 0, f"{len(key.key_entries)} != 0"
        assert key.is_modified, "KEY is modified"

    def test_key_add_resource(self):
        """Test adding resource entries."""
        key = KEY()
        key.add_bif("test.bif")

        # Add test resource
        entry: KeyEntry = key.add_key_entry("test", ResourceType.TXT, 0, 1)

        assert len(key.key_entries) == 1, f"{len(key.key_entries)} != 1"
        assert key.is_modified, "KEY is modified"

        # Verify entry properties
        assert str(entry.resref) == "test", f"{str(entry.resref)!r} != 'test'"
        assert entry.restype == ResourceType.TXT, f"{entry.restype!r} != {ResourceType.TXT!r}"
        assert entry.bif_index == 0, f"{entry.bif_index} != 0"
        assert entry.res_index == 1, f"{entry.res_index} != 1"

    def test_key_get_resources(self):
        """Test retrieving resources."""
        key = KEY()
        key.add_bif("test.bif")

        # Add test resources
        entry1: KeyEntry = key.add_key_entry("test1", ResourceType.TXT, 0, 1)
        entry2: KeyEntry = key.add_key_entry("test2", ResourceType.TXT, 0, 2)

        # Test getting by ResRef/type
        assert key.get_resource("test1", ResourceType.TXT) == entry1, f"{key.get_resource('test1', ResourceType.TXT)!r} != {entry1!r}"
        assert key.get_resource("invalid", ResourceType.TXT) is None, "Resource lookup should return None for invalid ResRef/type"

        # Test getting by type
        txt_resources: list[KeyEntry] = [key_entry for key_entry in key.key_entries if key_entry.restype == ResourceType.TXT]
        assert len(txt_resources) == 2, f"{len(txt_resources)} != 2"
        assert set(txt_resources) == {entry1, entry2}, f"{set(txt_resources)!r} != {{entry1!r, entry2!r}}"

        # Test getting by BIF index
        bif_resources: list[KeyEntry] = [key_entry for key_entry in key.key_entries if key_entry.bif_index == 0]
        assert len(bif_resources) == 2, f"{len(bif_resources)} != 2"
        assert set(bif_resources) == {entry1, entry2}, f"{set(bif_resources)!r} != {{entry1!r, entry2!r}}"

    def test_key_offset_calculations(self):
        """Test KEY file offset calculations."""
        key = KEY()

        # Add test BIFs
        key.add_bif("test1.bif")
        key.add_bif("test2.bif")

        # Verify offset calculations
        assert key.calculate_file_table_offset() == KEY.HEADER_SIZE, f"{key.calculate_file_table_offset()} != {KEY.HEADER_SIZE}"
        assert key.calculate_filename_table_offset() == KEY.HEADER_SIZE + (2 * KEY.BIF_ENTRY_SIZE), f"{key.calculate_filename_table_offset()} != {KEY.HEADER_SIZE + (2 * KEY.BIF_ENTRY_SIZE)}"

        # Test BIF filename offset calculation
        offset0: int = key.calculate_filename_offset(0)
        offset1: int = key.calculate_filename_offset(1)
        assert offset1 > offset0, f"{offset1} <= {offset0}"
        with self.assertRaises(ValueError):
            key.calculate_filename_offset(2)  # Invalid BIF index

    def test_key_v1_read(self):
        """Test reading a KEY V1.0 file using xoreos-tools test data."""
        # This is the exact same test data from xoreos-tools tests/aurora/keyfile.cpp
        key_data = bytes([
            # Header
            0x4B, 0x45, 0x59, 0x20,  # "KEY "
            0x56, 0x31, 0x20, 0x20,  # "V1  "
            0x01, 0x00, 0x00, 0x00,  # 1 BIF
            0x01, 0x00, 0x00, 0x00,  # 1 resource
            0x40, 0x00, 0x00, 0x00,  # File table offset (64)
            0x5B, 0x00, 0x00, 0x00,  # Key table offset (91)
            0x00, 0x00, 0x00, 0x00,  # Build year
            0x00, 0x00, 0x00, 0x00,  # Build day
            # 32 bytes reserved
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            # BIF entry
            0x4C, 0x00, 0x00, 0x00,  # File size (76)
            0x4C, 0x00, 0x00, 0x00,  # Filename offset
            0x0F, 0x00,              # Filename size (15)
            0x00, 0x00,              # Drives
            # Filename "data\xoreos.bif"
            0x64, 0x61, 0x74, 0x61, 0x5C, 0x78, 0x6F, 0x72,
            0x65, 0x6F, 0x73, 0x2E, 0x62, 0x69, 0x66,
            # Resource entry "ozymandias"
            0x6F, 0x7A, 0x79, 0x6D, 0x61, 0x6E, 0x64, 0x69,
            0x61, 0x73, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x0A, 0x00,              # Type (TXT)
            0x01, 0x00, 0x00, 0x00,  # Resource ID
        ])

        # Read the KEY file
        key: KEY = KEYBinaryReader(key_data).load()

        # Test BIF entries
        assert len(key.bif_entries) == 1, f"{len(key.bif_entries)} != 1"
        assert key.bif_entries[0].filename == "data/xoreos.bif", f"{key.bif_entries[0].filename!r} != 'data/xoreos.bif'"
        assert key.bif_entries[0].filesize == 76, f"{key.bif_entries[0].filesize} != 76"

        # Test resource entries
        assert len(key.key_entries) == 1, f"{len(key.key_entries)} != 1"
        res: KeyEntry | None = key.key_entries[0]
        assert str(res.resref) == "ozymandias", f"{str(res.resref)!r} != 'ozymandias'"
        assert res.restype == ResourceType.TXT, f"{res.restype!r} != {ResourceType.TXT!r}"
        assert res.bif_index == 0, f"{res.bif_index} != 0"
        assert res.res_index == 1, f"{res.res_index} != 1"

        # Test resource lookup
        res = key.get_resource("ozymandias", ResourceType.TXT)
        assert res is not None, "Resource lookup should return a resource"
        assert str(res.resref) == "ozymandias", f"{str(res.resref)!r} != 'ozymandias'"
        assert res.restype == ResourceType.TXT, f"{res.restype!r} != {ResourceType.TXT!r}"
        assert res.bif_index == 0, f"{res.bif_index} != 0"
        assert res.res_index == 1, f"{res.res_index} != 1"
