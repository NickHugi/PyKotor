"""This module handles classes relating to editing BIF/BZF files.

BIF (Bioware Index File) files are archive containers that store the bulk of game resources.
They work in tandem with KEY files which provide the filename-to-resource mappings. BIF files
contain only resource IDs, types, and data - the actual filenames (ResRefs) are stored in the
KEY file. BZF files are LZMA-compressed BIF files used in some game distributions.

References:
----------
    vendor/reone/include/reone/resource/format/bifreader.h:27-58 - BifReader class
    vendor/reone/src/libs/resource/format/bifreader.cpp:24-73 - BIF loading implementation
    vendor/Kotor.NET/Kotor.NET/Formats/KotorBIF/BIFBinaryStructure.cs:13-67 - Binary structure
    vendor/KotOR_IO/KotOR_IO/File Formats/BIF.cs:20-306 - C# BIF implementation
    vendor/KotOR-Bioware-Libs/BIF.pm:1-252 - Perl BIF library
    vendor/xoreos/src/aurora/biffile.cpp:40-164 - BIF file handling
    vendor/KotOR.js/src/resource/BIFObject.ts:11-152 - TypeScript implementation

Binary Format:
-------------
    Header (20 bytes):
        Offset | Size | Type   | Description
        -------|------|--------|-------------
        0x00   | 4    | char[] | File Type ("BIFF" or "BZF ")
        0x04   | 4    | char[] | File Version ("V1  " for BIF, "V1.0" for BZF)
        0x08   | 4    | uint32 | Variable Resource Count
        0x0C   | 4    | uint32 | Fixed Resource Count (unused in KotOR, always 0)
        0x10   | 4    | uint32 | Offset to Variable Resource Table
    
    Variable Resource Entry (16 bytes each):
        Offset | Size | Type   | Description
        -------|------|--------|-------------
        0x00   | 4    | uint32 | Resource ID (matches KEY file entry)
        0x04   | 4    | uint32 | Offset to resource data
        0x08   | 4    | uint32 | File Size (uncompressed)
        0x0C   | 4    | uint32 | Resource Type
    
    Fixed Resource Entry (unused in KotOR, 20 bytes each if present):
        Similar to Variable but with additional Part Number field
    
    Resource Data:
        Raw binary data for each resource at specified offsets
        
    Reference: reone/bifreader.cpp:24-73, Kotor.NET:20-65, KotOR_IO:42-78
    
BZF Compression:
---------------
    BZF files use LZMA compression on the entire BIF file after the 8-byte header.
    The BZF header contains: "BZF " + "V1.0", followed by LZMA-compressed BIF data.
    Decompression reveals a standard BIF structure.
    
    Reference: reone/biffile.cpp:48-76, xoreos/biffile.cpp:53-82
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, ClassVar

from pykotor.common.misc import ResRef
from pykotor.extract.file import ResourceIdentifier
from pykotor.resource.bioware_archive import ArchiveResource, BiowareArchive
from pykotor.resource.formats.key import KeyEntry
from pykotor.tools.misc import is_bif_file, is_bzf_file

if TYPE_CHECKING:
    import os

    from pykotor.resource.formats.key import KEY, BifEntry
    from pykotor.resource.type import ResourceType


class BIFType(Enum):
    """The type of BIF file based on file header signature.
    
    BIF files can be either uncompressed (BIFF) or LZMA-compressed (BZF).
    The file type is determined by the first 4 bytes of the file header.
    
    References:
    ----------
        vendor/reone/src/libs/resource/format/bifreader.cpp:27-34 - File type detection
        vendor/Kotor.NET/Kotor.NET/Formats/KotorBIF/BIFBinaryStructure.cs:36 - FileType field
        vendor/KotOR_IO/KotOR_IO/File Formats/BIF.cs:47 - FileType reading
    """

    BIF = "BIFF"  # Regular uncompressed BIF file
    BZF = "BZF "  # LZMA-compressed BIF file (used in some distributions)

    @classmethod
    def from_extension(
        cls,
        ext_or_filepath: os.PathLike | str,
    ) -> BIFType:
        """Get BIF type from file extension."""
        if is_bif_file(ext_or_filepath):
            return cls.BIF
        if is_bzf_file(ext_or_filepath):
            return cls.BZF
        msg = f"'{ext_or_filepath}' is not a valid BZF/BIF file extension."
        raise ValueError(msg)


class BIFResource(ArchiveResource):
    """A single resource entry stored in a BIF/BZF file.
    
    BIF resources contain only the resource data, type, and ID. The actual filename (ResRef)
    is stored in the KEY file and matched via the resource ID. Each resource has a unique ID
    within the BIF that corresponds to entries in the KEY file's resource table.
    
    References:
    ----------
        vendor/reone/include/reone/resource/format/bifreader.h:29-34 - ResourceEntry struct
        vendor/Kotor.NET/Kotor.NET/Formats/KotorBIF/BIFBinaryStructure.cs:51-65 - VariableResource
        vendor/KotOR_IO/KotOR_IO/File Formats/BIF.cs:195-213 - VariableResourceEntry class
        
    Attributes:
    ----------
        resname_key_index: Resource ID that matches KEY file entries
            Reference: reone/bifreader.h:30 (id field)
            Reference: Kotor.NET/BIFBinaryStructure.cs:53 (ResourceID property)
            Reference: KotOR_IO/BIF.cs:203 (ID field)
            This is a unique identifier within the BIF file
            Upper 20 bits encode BIF index, lower 14 bits encode resource index
            Used to match resources between BIF and KEY files
            
        _offset: Byte offset to resource data within BIF file
            Reference: reone/bifreader.h:31 (offset field)
            Reference: Kotor.NET/BIFBinaryStructure.cs:54 (Offset property)
            Reference: KotOR_IO/BIF.cs:204 (Offset field)
            Points to start of raw resource data in file
            Offsets are absolute from beginning of file
            
        _packed_size: Size of compressed data (BZF only, unused in regular BIF)
            BZF-specific field for compressed resource size
            Not present in standard BIF format
            Typically equals uncompressed size for BIF files
    """

    def __init__(
        self,
        resref: ResRef,
        restype: ResourceType,
        data: bytes,
        resname_key_index: int = 0,
        size: int | None = None,
    ):
        super().__init__(resref=resref, restype=restype, data=data, size=size)
        
        # vendor/reone/include/reone/resource/format/bifreader.h:30
        # vendor/Kotor.NET/Kotor.NET/Formats/KotorBIF/BIFBinaryStructure.cs:53
        # vendor/KotOR_IO/KotOR_IO/File Formats/BIF.cs:203
        # Resource ID (matches KEY file, unique within BIF)
        self.resname_key_index: int = resname_key_index
        
        # vendor/reone/include/reone/resource/format/bifreader.h:31
        # vendor/Kotor.NET/Kotor.NET/Formats/KotorBIF/BIFBinaryStructure.cs:54
        # vendor/KotOR_IO/KotOR_IO/File Formats/BIF.cs:204
        # Byte offset to resource data in file
        self._offset: int = 0  # Offset in BIF file
        
        # BZF-specific: Size of compressed data
        self._packed_size: int = 0  # Size of compressed data (BZF only)

    @property
    def offset(self) -> int:
        """Get resource offset."""
        return self._offset

    @offset.setter
    def offset(self, value: int) -> None:
        """Set resource offset."""
        self._offset = value

    @property
    def packed_size(self) -> int:
        """Get compressed data size (BZF only)."""
        return self._packed_size

    @packed_size.setter
    def packed_size(self, value: int) -> None:
        """Set compressed data size (BZF only)."""
        self._packed_size = value

    def __eq__(
        self,
        other: object,
    ) -> bool:
        """Compare two resources."""
        if not isinstance(other, BIFResource):
            return NotImplemented
        return self.resname_key_index == other.resname_key_index and self.restype == other.restype and self.size == other.size

    def __hash__(self) -> int:
        """Hash resource."""
        return hash((self.resname_key_index, self.restype, self.size))

    def __str__(self) -> str:
        """Get string representation."""
        return f"{self.resref}:{self.restype.name}[{self.size}b]"


class BIF(BiowareArchive):
    """Represents a BIF/BZF file in the Aurora engine.
    
    BIF (Binary Index Format) files are the primary data containers for KotOR game resources.
    They store thousands of game assets (models, textures, scripts, etc.) in a single file.
    BIF files work in conjunction with KEY files: the BIF contains the data and resource IDs,
    while the KEY file maps filenames (ResRefs) to resource IDs and BIF locations.
    
    References:
    ----------
        vendor/reone/include/reone/resource/format/bifreader.h:27-58 - BifReader class
        vendor/reone/src/libs/resource/format/bifreader.cpp:24-73 - BIF loading
        vendor/Kotor.NET/Kotor.NET/Formats/KotorBIF/BIFBinaryStructure.cs:15-32 - FileRoot
        vendor/KotOR_IO/KotOR_IO/File Formats/BIF.cs:20-306 - Complete BIF implementation
        vendor/xoreos/src/aurora/biffile.h:40-87 - BIFFile class
        vendor/KotOR.js/src/resource/BIFObject.ts:11-152 - TypeScript BIF
        
    Attributes:
    ----------
        HEADER_SIZE: Size of BIF header in bytes (20 bytes)
            Reference: reone/bifreader.cpp:27-42 (header reading)
            Reference: Kotor.NET/BIFBinaryStructure.cs:41-47 (header fields)
            Reference: KotOR_IO/BIF.cs:46-51 (header parsing)
            Fixed size across all BIF versions
            
        VAR_ENTRY_SIZE: Size of each variable resource entry (16 bytes)
            Reference: reone/bifreader.cpp:57-62 (readResourceEntry)
            Reference: Kotor.NET/BIFBinaryStructure.cs:58-64 (VariableResource reading)
            Reference: KotOR_IO/BIF.cs:56 (entry reading loop)
            Each entry: ID(4) + Offset(4) + Size(4) + Type(4)
            
        FIX_ENTRY_SIZE: Size of fixed resource entry (16-20 bytes, unused in KotOR)
            Reference: KotOR_IO/BIF.cs:63 (FixedResourceEntry struct)
            Fixed resources not used in KotOR games (always 0 count)
            
        FILE_VERSION: BIF file format version ("V1  ")
            Reference: reone/bifreader.cpp:30-34 (version check)
            Reference: Kotor.NET/BIFBinaryStructure.cs:44 (FileVersion)
            Reference: KotOR_IO/BIF.cs:48 (Version field)
            
        bif_type: Whether this is regular BIF or compressed BZF
            Reference: reone/biffile.cpp:48-76 (compression detection)
            Determines compression handling during load/save
            
        _resources: List of all resources in this BIF
            Reference: reone/bifreader.h:52 (_resources vector)
            Reference: Kotor.NET/BIFBinaryStructure.cs:18 (Resources list)
            Reference: KotOR_IO/BIF.cs:96 (VariableResourceTable)
            Ordered list maintained for indexing and iteration
            
        _resource_dict: Fast lookup by ResRef and ResourceType
            PyKotor-specific optimization for O(1) resource lookup
            Built from KEY file data or user assignment
            
        _id_lookup: Fast lookup by resource ID
            Reference: Similar to KEY file's resource_by_id mapping
            Maps resource ID to BIFResource for KEY-BIF coordination
            
        _modified: Tracks if BIF has been modified since loading
            Used to determine if file needs to be saved
    """

    HEADER_SIZE: ClassVar[int] = 20  # Fixed header size
    VAR_ENTRY_SIZE: ClassVar[int] = 16  # Size of each variable resource entry
    FIX_ENTRY_SIZE: ClassVar[int] = 16  # Size of each fixed resource entry

    FILE_VERSION: ClassVar[str] = "V1  "

    def __init__(
        self,
        bif_type: BIFType = BIFType.BIF,
    ):
        super().__init__()
        
        # vendor/reone/src/libs/resource/format/bifreader.cpp:48-76
        # File type (BIF vs BZF determines compression)
        self.bif_type: BIFType = bif_type
        
        # vendor/reone/include/reone/resource/format/bifreader.h:52
        # vendor/Kotor.NET/Kotor.NET/Formats/KotorBIF/BIFBinaryStructure.cs:18
        # vendor/KotOR_IO/KotOR_IO/File Formats/BIF.cs:96
        # List of all resources in file (ordered)
        self._resources: list[BIFResource] = []
        
        # PyKotor optimization: ResRef+Type -> Resource lookup (O(1) access)
        self._resource_dict: dict[ResourceIdentifier, BIFResource] = {}
        
        # PyKotor optimization: Resource ID -> Resource lookup (for KEY coordination)
        self._id_lookup: dict[int, BIFResource] = {}
        
        # Modification tracking flag
        self._modified: bool = False

    @property
    def resources(self) -> list[BIFResource]:
        """Get list of resources."""
        return self._resources

    @property
    def var_count(self) -> int:
        """Number of variable resources."""
        return len(self._resources)

    @property
    def fixed_count(self) -> int:
        """Number of fixed resources."""
        return 0  # Currently no fixed resources supported

    def get_resource_offset(
        self,
        resource: ArchiveResource,
    ) -> int:
        """Get offset and size for a resource.

        Required by BiowareArchive.
        """
        if not isinstance(resource, BIFResource):
            msg = "Resource is not a BIFResource: cannot get offset"
            raise TypeError(msg)
        try:
            if self.bif_type == BIFType.BZF:
                return resource.offset
        except ValueError as e:
            msg = "Resource not found in BIF"
            raise ValueError(msg) from e
        return resource.offset

    def set_data(
        self,
        resref: ResRef,
        restype: ResourceType,
        data: bytes,
        res_id: int | None = None,
    ) -> BIFResource:
        """Create and add a new resource."""
        resource = BIFResource(resref, restype, data)
        if res_id is not None:
            resource.resname_key_index = res_id
        self._resources.append(resource)
        self._resource_dict[ResourceIdentifier(str(resref), restype)] = resource
        self._id_lookup[resource.resname_key_index] = resource
        self._modified = True
        return resource

    def remove_resource(
        self,
        resource: BIFResource,
    ) -> None:
        """Remove a resource from the BIF."""
        try:
            self._resources.remove(resource)
            del self._resource_dict[ResourceIdentifier(str(resource.resref), resource.restype)]
            del self._id_lookup[resource.resname_key_index]
            self._modified = True
        except (ValueError, KeyError) as e:
            msg = f"Resource '{resource!r}' not found in BIF"
            raise ValueError(msg) from e

    def reorder_resources(
        self,
        new_order: list[BIFResource],
    ) -> None:
        """Reorder resources in the BIF."""
        if set(new_order) != set(self._resources):
            msg = "New order must contain exactly the same resources"
            raise ValueError(msg)
        self._resources = new_order.copy()
        self.build_lookup_tables()
        self._modified = True

    def get_resource_by_id(
        self,
        resource_id: int,
    ) -> BIFResource | None:
        """Get resource by ID."""
        return self._id_lookup.get(resource_id)

    def get_resources_by_type(
        self,
        restype: ResourceType,
    ) -> list[BIFResource]:
        """Get all resources of a specific type."""
        return [res for res in self._resources if res.restype == restype]

    def try_get_resource(
        self,
        resref: str | ResRef,
        restype: ResourceType,
    ) -> tuple[bool, BIFResource | None]:
        """Try to get resource by ResRef and type."""
        if isinstance(resref, ResRef):
            resref = str(resref)
        resource: BIFResource | None = self._resource_dict.get(ResourceIdentifier(resref.lower(), restype))
        return (resource is not None, resource)

    def build_lookup_tables(self) -> None:
        """Build internal lookup tables for fast resource access."""
        self._resource_dict.clear()
        self._id_lookup.clear()
        for resource in self._resources:
            self._resource_dict[ResourceIdentifier(str(resource.resref), resource.restype)] = resource
            self._id_lookup[resource.resname_key_index] = resource

    @property
    def is_compressed(self) -> bool:
        """Check if this is a compressed BIF (BZF)."""
        return self.bif_type is BIFType.BZF

    @property
    def is_modified(self) -> bool:
        """Whether the BIF has been modified since loading."""
        return self._modified

    def generate_key(
        self,
        filename: str,
        existing_key: KEY | None = None,
    ) -> KEY:
        """Generate a KEY file from this BIF's contents.

        Args:
            filename: The filename to use for this BIF in the KEY.

        Returns:
            A new KEY object containing entries for all resources in this BIF.
        """
        from pykotor.resource.formats.key.key_data import KEY, KeyEntry

        key: KEY = KEY() if existing_key is None else existing_key

        # Add this BIF file
        bif_idx: BifEntry = key.add_bif(filename)

        # Add all resources to the KEY
        for resource in self._resources:
            key.key_entries.append(
                KeyEntry(
                    resref=resource.resref,
                    restype=resource.restype,
                    resid=resource.resname_key_index,
                )
            )

        return key

    def validate_with_key(
        self,
        key: KEY,
        bif_idx: int,
    ) -> list[str]:
        """Validate this BIF's contents against a KEY file.

        Args:
            key: The KEY file to validate against.
            bif_idx: The index of this BIF in the KEY file.

        Returns:
            A list of validation errors, empty if validation passed.
        """
        errors: list[str] = []

        # Get all KEY resources that should be in this BIF
        key_resources: list[KeyEntry] = [r for r in key.key_entries if r.bif_index == bif_idx]

        # Check all KEY resources exist in BIF
        for key_res in key_resources:
            bif_res: BIFResource | None = self.get_resource_by_id(key_res.resname_key_index)
            if bif_res is None:
                errors.append(f"Resource {key_res.resref}:{key_res.restype} from KEY not found in BIF")
                continue

            if bif_res.restype != key_res.restype:
                errors.append(f"Resource {key_res.resref} type mismatch: KEY={key_res.restype}, BIF={bif_res.restype}")

        # Check all BIF resources exist in KEY
        for bif_res in self._resources:
            key_res: KeyEntry | None = next((r for r in key_resources if r.resname_key_index == bif_res.resname_key_index), None)
            if key_res is None:
                errors.append(f"Resource ID {bif_res.resname_key_index} from BIF not found in KEY")

        return errors

    def synchronize_with_key(
        self,
        key: KEY,
        bif_idx: int,
    ) -> None:
        """Synchronize this BIF's resource names with a KEY file.

        Args:
            key: The KEY file to synchronize with.
            bif_idx: The index of this BIF in the KEY file.
        """
        # Get all KEY resources for this BIF
        key_resources: dict[int, KeyEntry] = {r.resname_key_index: r for r in key.key_entries if r.bif_index == bif_idx}

        # Update BIF resource names from KEY
        for resource in self._resources:
            key_res: KeyEntry | None = key_resources.get(resource.resname_key_index)
            if key_res is None:
                continue
            resource.resref = key_res.resref

        self.build_lookup_tables()

    def create_key(
        self,
        filename: str,
    ) -> KEY:
        """Create a KEY file from this BIF's contents.

        Args:
            filename: The filename to use for this BIF in the KEY.

        Returns:
            A new KEY object containing entries for all resources in this BIF.
        """
        from pykotor.resource.formats.key.key_data import KEY

        key = KEY()
        key.add_bif(filename)

        # Add all resources to the KEY
        for resource in self._resources:
            key_res = KeyEntry(resref=resource.resref, restype=resource.restype, resid=resource.resname_key_index)
            key.key_entries.append(key_res)

        return key

    def apply_key(
        self,
        key: KEY,
        bif_idx: int,
    ) -> list[str]:
        """Apply resource names from a KEY file to this BIF.

        Args:
            key: The KEY file to get names from.
            bif_idx: The index of this BIF in the KEY file.

        Returns:
            List of any errors encountered during the process.
        """
        errors: list[str] = []

        # Get all KEY resources for this BIF
        key_resources: dict[int, KeyEntry] = {r.resname_key_index: r for r in key.key_entries if r.bif_index == bif_idx}

        # Update BIF resource names from KEY
        for resource in self._resources:
            if key_res := key_resources.get(resource.resname_key_index):
                if resource.restype != key_res.restype:
                    errors.append(f"Resource type mismatch for ID {resource.resname_key_index}: " f"BIF={resource.restype}, KEY={key_res.restype}")
                resource.resref = key_res.resref
            else:
                errors.append(f"Resource ID {resource.resname_key_index} from BIF not found in KEY")

        # Check for KEY resources not in BIF
        bif_ids: set[int] = {r.resname_key_index for r in self._resources}
        errors.extend([f"Resource {key_res.resref}:{key_res.restype} from KEY not found in BIF (ID: {key_res.resname_key_index})" for key_res in key_resources.values() if key_res.resname_key_index not in bif_ids])  # noqa: E501

        # Rebuild lookup tables with new names
        self.build_lookup_tables()

        return errors

    def reorganize_by_type(self) -> None:
        """Reorganize resources by grouping them by type.

        This can improve access performance when reading resources of the same type.
        """
        self._resources.sort(key=lambda r: (r.restype.type_id, r.resname_key_index))
        self._modified = True
        self.build_lookup_tables()
