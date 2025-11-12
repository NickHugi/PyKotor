"""This module handles classes relating to KEY files.

KEY (Key Table) files serve as the master index for all BIF files in the game. The KEY file
maps resource names (ResRefs) and types to specific locations within BIF archives. KotOR uses
chitin.key as the main KEY file which references all game BIF files.

References:
----------
    vendor/reone/include/reone/resource/format/keyreader.h:30-68 - KeyReader class
    vendor/reone/src/libs/resource/format/keyreader.cpp:24-128 - KEY loading implementation
    vendor/Kotor.NET/Kotor.NET/Formats/KotorKEY/KEYBinaryStructure.cs:13-114 - Binary structure
    vendor/KotOR_IO/KotOR_IO/File Formats/KEY.cs:19-227 - C# KEY implementation
    vendor/KotOR-dotNET/AuroraParsers/KEYObject.cs:10-95 - Simple KEY parser
    vendor/KotOR.js/src/resource/KEYObject.ts:21-148 - TypeScript KEY implementation
    vendor/xoreos/src/aurora/keyfile.cpp:39-194 - KEY file handling
    vendor/KotOR-Bioware-Libs/KEY.pm:1-289 - Perl KEY library

Binary Format:
-------------
    Header (64 bytes):
        Offset | Size | Type   | Description
        -------|------|--------|-------------
        0x00   | 4    | char[] | File Type ("KEY ")
        0x04   | 4    | char[] | File Version ("V1  " or "V1.1")
        0x08   | 4    | uint32 | BIF Count
        0x0C   | 4    | uint32 | Key Count (number of resources)
        0x10   | 4    | uint32 | Offset to File Table (BIF entries)
        0x14   | 4    | uint32 | Offset to Key Table (resource entries)
        0x18   | 4    | uint32 | Build Year (years since 1900)
        0x1C   | 4    | uint32 | Build Day (days since Jan 1)
        0x20   | 32   | byte[] | Reserved (padding, usually zeros)
    
    File Entry (12 bytes each):
        Offset | Size | Type   | Description
        -------|------|--------|-------------
        0x00   | 4    | uint32 | File Size (of BIF file)
        0x04   | 4    | uint32 | Filename Offset (into filename table)
        0x08   | 2    | uint16 | Filename Length
        0x0A   | 2    | uint16 | Drives (drive flags, e.g. 0x0001 = HD0)
    
    Filename Table (variable length):
        Null-terminated strings for each BIF filename
        Referenced by File Entry's Filename Offset
        
    Key Entry (22 bytes each):
        Offset | Size | Type   | Description
        -------|------|--------|-------------
        0x00   | 16   | char[] | ResRef (null-padded, max 16 chars)
        0x10   | 2    | uint16 | Resource Type
        0x12   | 4    | uint32 | Resource ID
            Bits 31-20: BIF Index (top 12 bits)
            Bits 19-0:  Resource Index within BIF (bottom 20 bits)
        
    Reference: reone/keyreader.cpp:24-128, Kotor.NET:22-47, KotOR_IO:43-89, KotOR.js:41-81
"""

from __future__ import annotations

from typing import ClassVar

from pykotor.common.misc import ResRef
from pykotor.resource.type import ResourceType


class BifEntry:
    """Represents a BIF file entry in the KEY file's file table.
    
    Each BIF entry contains the filename and metadata for a single BIF archive. The KEY file
    maintains a list of all BIF files used by the game, and resources reference their containing
    BIF by index into this list.
    
    References:
    ----------
        vendor/reone/include/reone/resource/format/keyreader.h:32-35 - FileEntry struct
        vendor/Kotor.NET/Kotor.NET/Formats/KotorKEY/KEYBinaryStructure.cs:70-82 - BIFInfo class
        vendor/KotOR_IO/KotOR_IO/File Formats/KEY.cs:180-195 - FileEntry class
        vendor/KotOR-dotNET/AuroraParsers/KEYObject.cs:14-24 - Header struct
        vendor/KotOR.js/src/interface/resource/IBIFEntry.ts - IBIFEntry interface
        
    Binary Format (12 bytes):
    -------------------------
        Offset | Size | Type   | Description
        -------|------|--------|-------------
        0x00   | 4    | uint32 | File Size (of BIF file on disk)
        0x04   | 4    | uint32 | Filename Offset (into filename table)
        0x08   | 2    | uint16 | Filename Length (bytes)
        0x0A   | 2    | uint16 | Drives (bitfield: 0x0001=HD0, 0x0002=CD1, etc.)
        
    Attributes:
    ----------
        filename: Path to the BIF file (relative to game directory)
            Reference: reone/keyreader.h:33 (filename field)
            Reference: Kotor.NET/KEYBinaryStructure.cs:38 (Filenames list)
            Reference: KotOR_IO/KEY.cs:72 (Filename property)
            Reference: KotOR.js/KEYObject.ts:70 (filename field)
            Typically paths like "data/models.bif" or "data/textures.bif"
            Forward slashes used as path separators
            
        filesize: Size of the BIF file in bytes
            Reference: reone/keyreader.h:34 (fileSize field)
            Reference: Kotor.NET/KEYBinaryStructure.cs:77 (reads 4 bytes, skipped)
            Reference: KotOR_IO/KEY.cs:61 (FileSize property)
            Reference: KotOR.js/KEYObject.ts:61 (fileSize field)
            Used for validation and disk space calculations
            
        drives: Drive location bitfield
            Reference: Kotor.NET/KEYBinaryStructure.cs:80 (reads 2 bytes, skipped)
            Reference: KotOR_IO/KEY.cs:64 (Drives property)
            Reference: KotOR.js/KEYObject.ts:64 (drives field)
            Bitfield indicating where BIF should be found:
                0x0001 = HD0 (hard drive install)
                0x0002 = CD1 (first CD)
                0x0004 = CD2 (second CD), etc.
            Modern installations typically use HD0 (0x0001)
    """

    def __init__(self):
        # vendor/reone/include/reone/resource/format/keyreader.h:33
        # vendor/Kotor.NET/Kotor.NET/Formats/KotorKEY/KEYBinaryStructure.cs:38
        # vendor/KotOR_IO/KotOR_IO/File Formats/KEY.cs:72
        # vendor/KotOR.js/src/resource/KEYObject.ts:70
        # Path to BIF file (relative to game directory)
        self.filename: str = ""
        
        # vendor/reone/include/reone/resource/format/keyreader.h:34
        # vendor/KotOR_IO/KotOR_IO/File Formats/KEY.cs:61
        # vendor/KotOR.js/src/resource/KEYObject.ts:61
        # Size of BIF file on disk (bytes)
        self.filesize: int = 0
        
        # vendor/KotOR_IO/KotOR_IO/File Formats/KEY.cs:64
        # vendor/KotOR.js/src/resource/KEYObject.ts:64
        # Drive location flags (0x0001=HD0, 0x0002=CD1, etc.)
        self.drives: int = 0  # Drive location flags (e.g. HD0)

    def __eq__(
        self,
        other: object,
    ) -> bool:
        """Compare two BIF entries."""
        if not isinstance(other, BifEntry):
            return NotImplemented
        return self.filename == other.filename and self.filesize == other.filesize and self.drives == other.drives

    def __hash__(self) -> int:
        """Hash BIF entry."""
        return hash((self.filename, self.filesize, self.drives))

    def __str__(self) -> str:
        """Get string representation."""
        return f"{self.filename}({self.filesize} bytes)"


class KeyEntry:
    """Represents a resource entry in the KEY file's key table.
    
    Each key entry maps a resource name (ResRef) and type to a specific location within a BIF file.
    The resource_id field encodes both the BIF index (which BIF contains this resource) and the
    resource index within that BIF. This enables the game to quickly locate any resource by name.
    
    References:
    ----------
        vendor/reone/include/reone/resource/format/keyreader.h:37-41 - KeyEntry struct
        vendor/Kotor.NET/Kotor.NET/Formats/KotorKEY/KEYBinaryStructure.cs:84-112 - Key class
        vendor/KotOR_IO/KotOR_IO/File Formats/KEY.cs:198-227 - KeyEntry class
        vendor/KotOR-dotNET/AuroraParsers/KEYObject.cs:26-31 - _KeyTable struct
        vendor/KotOR.js/src/interface/resource/IKEYEntry.ts - IKEYEntry interface
        
    Binary Format (22 bytes):
    -------------------------
        Offset | Size | Type   | Description
        -------|------|--------|-------------
        0x00   | 16   | char[] | ResRef (resource filename, null-padded, max 16 chars)
        0x10   | 2    | uint16 | Resource Type (file type ID)
        0x12   | 4    | uint32 | Resource ID
            Bits 31-20: BIF Index (top 12 bits, max 4096 BIFs)
            Bits 19-0:  Resource Index within BIF (bottom 20 bits, max 1048576 resources per BIF)
    
    Attributes:
    ----------
        resref: Resource filename (ResRef)
            Reference: reone/keyreader.h:32-33 (resId member in context of KeyEntry)
            Reference: Kotor.NET/KEYBinaryStructure.cs:86 (ResRef property)
            Reference: KotOR_IO/KEY.cs:206 (ResRef field)
            Reference: KotOR-dotNET/KEYObject.cs:28 (ResRef field)
            Reference: KotOR.js/KEYObject.ts:76 (resRef field)
            ASCII string, typically lowercase, max 16 chars
            Null-padded in binary format, stored as ResRef object for compatibility
            
        restype: Resource type identifier
            Reference: Kotor.NET/KEYBinaryStructure.cs:87 (ResourceType property)
            Reference: KotOR_IO/KEY.cs:207 (ResourceType field)
            Reference: KotOR-dotNET/KEYObject.cs:29 (ResourceType field)
            Reference: KotOR.js/KEYObject.ts:77 (resType field)
            Stored as uint16 in binary, converted to ResourceType enum for type safety
            Maps to resource file extensions (e.g., 0x3F = TPC for textures)
            
        resource_id: Composite ID encoding BIF index and resource index
            Reference: reone/keyreader.h:32-33 (resId field, ResourceId type)
            Reference: Kotor.NET/KEYBinaryStructure.cs:88 (ResourceID property)
            Reference: KotOR_IO/KEY.cs:208 (ResID field)
            Reference: KotOR-dotNET/KEYObject.cs:30 (ResID field)
            Reference: KotOR.js/KEYObject.ts:78 (resId field)
            Top 12 bits (31-20): BIF index in KEY's file table
            Bottom 20 bits (19-0): Resource index within that BIF
            Example: 0x00A10005 = BIF index 5, resource index 0xA1
    """

    def __init__(
        self,
        resref: str | ResRef | None = None,
        restype: ResourceType | None = None,
        resid: int | None = None,
    ):
        # vendor/Kotor.NET/Kotor.NET/Formats/KotorKEY/KEYBinaryStructure.cs:92
        # vendor/KotOR_IO/KotOR_IO/File Formats/KEY.cs:80
        # vendor/KotOR-dotNET/AuroraParsers/KEYObject.cs:67
        # Resource filename (max 16 chars, null-padded in binary)
        self.resref: ResRef = ResRef.from_blank() if resref is None else ResRef(resref)
        
        # vendor/Kotor.NET/Kotor.NET/Formats/KotorKEY/KEYBinaryStructure.cs:93
        # vendor/KotOR_IO/KotOR_IO/File Formats/KEY.cs:81
        # vendor/KotOR-dotNET/AuroraParsers/KEYObject.cs:68
        # Resource type (uint16 in binary, converted to ResourceType enum)
        self.restype: ResourceType = ResourceType.INVALID if restype is None else restype
        
        # vendor/Kotor.NET/Kotor.NET/Formats/KotorKEY/KEYBinaryStructure.cs:94
        # vendor/KotOR_IO/KotOR_IO/File Formats/KEY.cs:83
        # vendor/KotOR-dotNET/AuroraParsers/KEYObject.cs:69
        # Composite resource ID: top 12 bits = BIF index, bottom 20 bits = resource index
        self.resource_id: int = 0 if resid is None else resid

    @property
    def bif_index(self) -> int:
        """Get the index into the BIF file table (top 12 bits of resource_id).
        
        References:
        ----------
            vendor/Kotor.NET/Kotor.NET/Formats/KotorKEY/KEYBinaryStructure.cs:101-102 - IndexIntoFileTable
            vendor/KotOR_IO/KotOR_IO/File Formats/KEY.cs:84-85 - IDx calculation
            vendor/KotOR.js/KEYObject.ts:78 - resId encoding documentation
        """
        # vendor/Kotor.NET/Kotor.NET/Formats/KotorKEY/KEYBinaryStructure.cs:101
        # vendor/KotOR_IO/KotOR_IO/File Formats/KEY.cs:84
        # Shift right 20 bits to get BIF index from composite resource_id
        return self.resource_id >> 20

    @property
    def res_index(self) -> int:
        """Get the index into the resource table (bottom 20 bits of resource_id).
        
        References:
        ----------
            vendor/Kotor.NET/Kotor.NET/Formats/KotorKEY/KEYBinaryStructure.cs:105-110 - IndexIntoResourceTable
            vendor/KotOR_IO/KotOR_IO/File Formats/KEY.cs:85 - IDy calculation
            vendor/KotOR.js/KEYObject.ts:78 - resId encoding documentation
        """
        # vendor/Kotor.NET/Kotor.NET/Formats/KotorKEY/KEYBinaryStructure.cs:109-110
        # vendor/KotOR_IO/KotOR_IO/File Formats/KEY.cs:85
        # Mask lower 20 bits to get resource index within the BIF
        return self.resource_id & 0xFFFFF

    def __eq__(
        self,
        other: object,
    ) -> bool:
        """Compare two key entries."""
        if not isinstance(other, KeyEntry):
            return NotImplemented
        return str(self.resref) == str(other.resref) and self.restype == other.restype and self.resource_id == other.resource_id

    def __hash__(self) -> int:
        """Hash key entry."""
        return hash((str(self.resref), self.restype, self.resource_id))

    def __str__(self) -> str:
        """Get string representation."""
        return f"{self.resref}:{self.restype.name}@{self.bif_index}:{self.res_index}"


class KEY:
    """Represents a KEY (Key Table) file in the Aurora engine.
    
    The KEY file is the master index for all game resources. It contains a list of BIF files
    and a complete mapping of all resource names (ResRefs) to their locations within those BIFs.
    The game typically loads chitin.key at startup, which provides access to all BIF archives.
    
    References:
    ----------
        vendor/reone/include/reone/resource/format/keyreader.h:30-68 - KeyReader class
        vendor/reone/src/libs/resource/format/keyreader.cpp:24-128 - KEY loading implementation
        vendor/Kotor.NET/Kotor.NET/Formats/KotorKEY/KEYBinaryStructure.cs:50-68 - FileHeader
        vendor/KotOR_IO/KotOR_IO/File Formats/KEY.cs:19-227 - Complete KEY implementation
        vendor/KotOR.js/src/resource/KEYObject.ts:21-148 - KEYObject class
        vendor/xoreos/src/aurora/keyfile.cpp:39-194 - KEY file handling
    """

    FILE_TYPE: ClassVar[str] = "KEY "
    FILE_VERSION: ClassVar[str] = "V1  "
    HEADER_SIZE: ClassVar[int] = 64  # Fixed header size
    BIF_ENTRY_SIZE: ClassVar[int] = 12  # Size of each BIF entry
    KEY_ENTRY_SIZE: ClassVar[int] = 22  # Size of each resource entry (16 + 2 + 4)

    def __init__(self):
        # vendor/KotOR_IO/KotOR_IO/File Formats/KEY.cs:46
        # vendor/KotOR.js/src/resource/KEYObject.ts:46
        # File type signature ("KEY ")
        self.file_type: str = self.FILE_TYPE
        
        # vendor/KotOR_IO/KotOR_IO/File Formats/KEY.cs:47
        # vendor/KotOR.js/src/resource/KEYObject.ts:47
        # File version ("V1  ")
        self.file_version: str = self.FILE_VERSION
        
        # vendor/KotOR_IO/KotOR_IO/File Formats/KEY.cs:106-107
        # vendor/KotOR.js/src/resource/KEYObject.ts:52
        # Build year (years since 1900)
        self.build_year: int = 0
        
        # vendor/KotOR_IO/KotOR_IO/File Formats/KEY.cs:109
        # vendor/KotOR.js/src/resource/KEYObject.ts:53
        # Build day (days since Jan 1)
        self.build_day: int = 0
        
        # vendor/Kotor.NET/Kotor.NET/Formats/KotorKEY/KEYBinaryStructure.cs:18
        # vendor/KotOR_IO/KotOR_IO/File Formats/KEY.cs:116
        # vendor/KotOR.js/src/resource/KEYObject.ts:56
        # List of BIF file entries
        self.bif_entries: list[BifEntry] = []
        
        # vendor/Kotor.NET/Kotor.NET/Formats/KotorKEY/KEYBinaryStructure.cs:20
        # vendor/KotOR_IO/KotOR_IO/File Formats/KEY.cs:119
        # vendor/KotOR.js/src/resource/KEYObject.ts:73
        # List of resource entries mapping ResRefs to BIF locations
        self.key_entries: list[KeyEntry] = []
        
        # PyKotor optimization: fast ResRef+Type -> KeyEntry lookup (O(1) access)
        self._resource_lookup: dict[tuple[str, ResourceType], KeyEntry] = {}
        
        # PyKotor optimization: fast BIF filename -> BifEntry lookup
        self._bif_lookup: dict[str, BifEntry] = {}
        
        # Modification tracking flag
        self._modified: bool = False

    def calculate_file_table_offset(self) -> int:
        """Calculate offset to the BIF file table."""
        return self.HEADER_SIZE

    def calculate_filename_table_offset(self) -> int:
        """Calculate offset to the filename table."""
        return self.calculate_file_table_offset() + (len(self.bif_entries) * self.BIF_ENTRY_SIZE)

    def calculate_key_table_offset(self) -> int:
        """Calculate offset to the key table."""
        return self.calculate_filename_table_offset() + self._calculate_total_filename_size()

    def calculate_filename_offset(
        self,
        bif_index: int,
    ) -> int:
        """Calculate offset to a BIF filename in the filename table."""
        if bif_index < 0 or bif_index >= len(self.bif_entries):
            raise ValueError(f"Invalid BIF index: {bif_index}")

        offset: int = self.calculate_filename_table_offset()
        for i in range(bif_index):
            offset += len(self.bif_entries[i].filename) + 1  # +1 for null terminator
        return offset

    def _calculate_total_filename_size(self) -> int:
        """Calculate total size of all BIF filenames including null terminators."""
        return sum(len(bif.filename) + 1 for bif in self.bif_entries)  # +1 for each null terminator

    def calculate_resource_id(
        self,
        bif_index: int,
        res_index: int,
    ) -> int:
        """Calculate resource ID from BIF and resource indices."""
        if bif_index < 0:
            raise ValueError(f"BIF index cannot be negative: {bif_index}")
        if bif_index >= len(self.bif_entries):
            raise IndexError(f"BIF index {bif_index} is out of range. Total BIF entries: {len(self.bif_entries)}")
        return (bif_index << 20) | (res_index & 0xFFFFF)

    def get_resource(
        self,
        resref: str | ResRef,
        restype: ResourceType,
    ) -> KeyEntry | None:
        """Get resource entry by ResRef and type."""
        if isinstance(resref, ResRef):
            resref = str(resref)
        return self._resource_lookup.get((resref.lower(), restype))

    def get_bif(
        self,
        filename: str,
    ) -> BifEntry | None:
        """Get BIF entry by filename."""
        return self._bif_lookup.get(filename.lower())

    def add_bif(
        self,
        filename: str,
        filesize: int = 0,
        drives: int = 0,
    ) -> BifEntry:
        """Add a BIF file entry."""
        bif = BifEntry()
        bif.filename = filename.replace("\\", "/").lstrip("/")  # Normalize path
        bif.filesize = filesize
        bif.drives = drives
        self.bif_entries.append(bif)
        self._bif_lookup[filename.lower()] = bif
        self._modified = True
        return bif

    def add_key_entry(
        self,
        resref: str | ResRef,
        restype: ResourceType,
        bif_index: int,
        res_index: int,
    ) -> KeyEntry:
        """Add a resource entry."""
        entry: KeyEntry = KeyEntry()
        entry.resref = ResRef(resref) if isinstance(resref, str) else resref
        entry.restype = restype
        entry.resource_id = self.calculate_resource_id(bif_index, res_index)
        self.key_entries.append(entry)
        self._resource_lookup[(str(entry.resref).lower(), entry.restype)] = entry
        self._modified = True
        return entry

    def remove_bif(
        self,
        bif: BifEntry,
    ) -> None:
        """Remove a BIF entry and all its resources."""
        self._resource_lookup.pop((bif.filename, ResourceType.TXT))
        self._bif_lookup.pop(bif.filename.lower(), None)
        self.bif_entries.remove(bif)
        self.key_entries.remove(next(key_entry for key_entry in self.key_entries if key_entry.resref == bif.filename))
        self.build_lookup_tables()  # Rebuild lookups
        self._modified = True

    def build_lookup_tables(self) -> None:
        """Build internal lookup tables for fast resource access."""
        self._resource_lookup.clear()
        self._bif_lookup.clear()
        for entry in self.key_entries:
            self._resource_lookup[(str(entry.resref).lower(), entry.restype)] = entry
        for bif in self.bif_entries:
            self._bif_lookup[bif.filename.lower()] = bif

    @property
    def is_modified(self) -> bool:
        """Check if the KEY has been modified since last load/save."""
        return self._modified
