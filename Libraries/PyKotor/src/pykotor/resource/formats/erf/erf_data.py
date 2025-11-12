"""This module handles classes relating to editing ERF files.

ERF (Encapsulated Resource File) files are self-contained archives used for modules, save games,
texture packs, and hak paks. Unlike BIF files which require a KEY file for filename lookups,
ERF files store both resource names (ResRefs) and data in the same file. They also support
localized strings for descriptions in multiple languages.

References:
----------
    vendor/reone/include/reone/resource/format/erfreader.h:29-65 - ErfReader class
    vendor/reone/src/libs/resource/format/erfreader.cpp:24-106 - ERF loading implementation
    vendor/Kotor.NET/Kotor.NET/Formats/KotorERF/ERFBinaryStructure.cs:11-170 - Binary structure
    vendor/KotOR_IO/KotOR_IO/File Formats/ERF.cs:19-308 - C# ERF implementation
    vendor/KotOR.js/src/resource/ERFObject.ts:11-353 - TypeScript ERF implementation
    vendor/xoreos/src/aurora/erffile.cpp:44-229 - ERF file handling
    vendor/KotOR-Bioware-Libs/ERF.pm:1-347 - Perl ERF library

Binary Format:
-------------
    Header (160 bytes):
        Offset | Size | Type   | Description
        -------|------|--------|-------------
        0x00   | 4    | char[] | File Type ("ERF ", "MOD ", "SAV ", "HAK ")
        0x04   | 4    | char[] | File Version ("V1.0")
        0x08   | 4    | uint32 | Language Count
        0x0C   | 4    | uint32 | Localized String Size (total bytes)
        0x10   | 4    | uint32 | Entry Count (number of resources)
        0x14   | 4    | uint32 | Offset to Localized String List
        0x18   | 4    | uint32 | Offset to Key List
        0x1C   | 4    | uint32 | Offset to Resource List
        0x20   | 4    | uint32 | Build Year (years since 1900)
        0x24   | 4    | uint32 | Build Day (days since Jan 1)
        0x28   | 4    | uint32 | Description StrRef (TLK reference)
        0x2C   | 116  | byte[] | Reserved (padding, usually zeros)
    
    Localized String Entry (variable length per language):
        - 4 bytes: Language ID (see Language enum)
        - 4 bytes: String Size (length in bytes)
        - N bytes: String Data (UTF-8 encoded text)
    
    Key Entry (24 bytes each):
        Offset | Size | Type   | Description
        -------|------|--------|-------------
        0x00   | 16   | char[] | ResRef (filename, null-padded, max 16 chars)
        0x10   | 4    | uint32 | Resource ID (index into resource list)
        0x14   | 2    | uint16 | Resource Type
        0x16   | 2    | uint16 | Unused (padding)
    
    Resource Entry (8 bytes each):
        Offset | Size | Type   | Description
        -------|------|--------|-------------
        0x00   | 4    | uint32 | Offset to Resource Data
        0x04   | 4    | uint32 | Resource Size
    
    Resource Data:
        Raw binary data for each resource at specified offsets
        
    Reference: reone/erfreader.cpp:24-106, Kotor.NET:25-46, KotOR_IO:43-96, KotOR.js:69-119
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from pykotor.resource.bioware_archive import ArchiveResource, BiowareArchive
from pykotor.common.misc import ResRef
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_erf_file, is_mod_file, is_sav_file

if TYPE_CHECKING:
    import os

    from pykotor.common.misc import ResRef


class ERFResource(ArchiveResource):
    """A single resource stored in an ERF/MOD/SAV file.
    
    Unlike BIF resources, ERF resources include their ResRef (filename) directly in the
    archive. Each resource is identified by a unique ResRef and ResourceType combination.
    
    References:
    ----------
        vendor/reone/include/reone/resource/format/erfreader.h:31-38 - KeyEntry and ResourceEntry structs
        vendor/Kotor.NET/Kotor.NET/Formats/KotorERF/ERFBinaryStructure.cs:115-168 - Key and Resource entries
        vendor/KotOR_IO/KotOR_IO/File Formats/ERF.cs:183-228 - Key and Resource classes
        vendor/KotOR.js/src/interface/resource/IERFKeyEntry.ts - Key entry interface
        vendor/KotOR.js/src/interface/resource/IERFResource.ts - Resource entry interface
    
    Attributes:
    ----------
        All attributes inherited from ArchiveResource (resref, restype, data, size)
        ERF resources have no additional attributes beyond the base ArchiveResource
    """
    
    def __init__(self, resref: ResRef, restype: ResourceType, data: bytes):
        # vendor/Kotor.NET/Kotor.NET/Formats/KotorERF/ERFBinaryStructure.cs:119-120
        # vendor/KotOR_IO/KotOR_IO/File Formats/ERF.cs:197-198
        # vendor/KotOR.js/src/resource/ERFObject.ts:103-107
        # ResRef stored in Key Entry (16 bytes, null-padded)
        # ResourceType stored in Key Entry (2 bytes, uint16)
        # Resource data referenced via Resource Entry (offset + size)
        super().__init__(resref=resref, restype=restype, data=data)



class ERFType(Enum):
    """The type of ERF file based on file header signature.
    
    ERF files can have different type signatures depending on their purpose:
    - ERF: Generic encapsulated resource file (texture packs, etc.)
    - MOD: Module file (game areas/levels)
    - SAV: Save game file
    - HAK: Hak pak file (custom content, unused in KotOR)
    
    References:
    ----------
        vendor/reone/src/libs/resource/format/erfreader.cpp:32-39 - File type validation
        vendor/Kotor.NET/Kotor.NET/Formats/KotorERF/ERFBinaryStructure.cs:73 - FileType field
        vendor/KotOR_IO/KotOR_IO/File Formats/ERF.cs:46 - FileType reading
        vendor/KotOR.js/src/resource/ERFObject.ts:45 - File type default
    """

    ERF = "ERF "  # Generic ERF archive (texture packs, etc.)
    MOD = "MOD "  # Module file (game levels/areas)

    @classmethod
    def from_extension(cls, ext_or_filepath: os.PathLike | str) -> ERFType:
        if is_erf_file(ext_or_filepath):
            return cls.ERF
        if is_mod_file(ext_or_filepath):
            return cls.MOD
        if is_sav_file(ext_or_filepath):
            return cls.MOD
        msg = f"Invalid ERF extension in filepath '{ext_or_filepath}'."
        raise ValueError(msg)


class ERF(BiowareArchive):
    """Represents an ERF/MOD/SAV file.
    
    ERF (Encapsulated Resource File) is a self-contained archive format used for game modules,
    save games, and resource packs. Unlike BIF+KEY pairs, ERF files contain both resource names
    and data in a single file, making them ideal for distributable content like mods.
    
    References:
    ----------
        vendor/reone/include/reone/resource/format/erfreader.h:29-65 - ErfReader class
        vendor/Kotor.NET/Kotor.NET/Formats/KotorERF/ERFBinaryStructure.cs:13-67 - FileRoot class
        vendor/KotOR_IO/KotOR_IO/File Formats/ERF.cs:19-308 - Complete ERF implementation
        vendor/KotOR.js/src/resource/ERFObject.ts:24-353 - ERFObject class
        vendor/xoreos/src/aurora/erffile.h:40-107 - ERFFile class
        
    Attributes:
    ----------
        erf_type: File type signature (ERF, MOD, SAV, HAK)
            Reference: reone/erfreader.cpp:32-39 (signature validation)
            Reference: Kotor.NET/ERFBinaryStructure.cs:73 (FileType property)
            Reference: KotOR_IO/ERF.cs:46 (FileType field)
            Reference: KotOR.js/ERFObject.ts:45 (fileType default)
            Determines intended use of the archive
            ERF = texture packs, MOD = game modules, SAV = save games
            
        is_save: Flag indicating if this is a save game ERF
            Reference: KotOR_IO/ERF.cs:15-16 (save game comment)
            Save games use MOD signature but have different structure
            Affects how certain fields are interpreted (e.g., build date)
            PyKotor-specific flag for save game handling
    """

    BINARY_TYPE = ResourceType.ERF
    ARCHIVE_TYPE: type[ArchiveResource] = ERFResource
    COMPARABLE_FIELDS = ("erf_type", "is_save_erf")
    COMPARABLE_SET_FIELDS = ("_resources",)

    def __init__(
        self,
        erf_type: ERFType = ERFType.ERF,
        *,
        is_save: bool = False,
    ):
        super().__init__()

        # vendor/reone/src/libs/resource/format/erfreader.cpp:32-39
        # vendor/Kotor.NET/Kotor.NET/Formats/KotorERF/ERFBinaryStructure.cs:73
        # vendor/KotOR_IO/KotOR_IO/File Formats/ERF.cs:46
        # vendor/KotOR.js/src/resource/ERFObject.ts:45
        # File type signature (ERF, MOD, SAV, HAK)
        self.erf_type: ERFType = erf_type
        
        # PyKotor-specific flag for save game handling
        # Save games use MOD signature but have different behavior
        self.is_save: bool = is_save

    @property
    def is_save_erf(self) -> bool:
        """Alias for ComparableMixin compatibility."""
        return self.is_save

    @is_save_erf.setter
    def is_save_erf(self, value: bool) -> None:
        self.is_save = value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.erf_type!r}, is_save={self.is_save})"

    def __eq__(self, other: object):
        from pykotor.resource.formats.rim import RIM  # Prevent circular imports  # noqa: PLC0415

        if not isinstance(other, (ERF, RIM)):
            return NotImplemented
        return set(self._resources) == set(other._resources)

    def __hash__(self) -> int:
        return hash((self.erf_type, tuple(self._resources), self.is_save))

    def get_resource_offset(self, resource: ArchiveResource) -> int:
        from pykotor.resource.formats.erf.io_erf import ERFBinaryWriter

        entry_count = len(self._resources)
        offset_to_keys = ERFBinaryWriter.FILE_HEADER_SIZE
        data_start = offset_to_keys + ERFBinaryWriter.KEY_ELEMENT_SIZE * entry_count

        resource_index = self._resources.index(resource)
        offset = data_start + sum(len(res.data) for res in self._resources[:resource_index])

        return offset
