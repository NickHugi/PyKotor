"""This module handles classes relating to editing BIF/BZF files."""

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
    """The type of BIF. More specifically, the first 4 bytes in the file header."""

    BIF = "BIFF"  # Regular BIF file
    BZF = "BZF "  # Compressed BIF file (LZMA)

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
    """A resource stored in a BIF/BZF file."""

    def __init__(
        self,
        resref: ResRef,
        restype: ResourceType,
        data: bytes,
        res_id: int = 0,
    ):
        super().__init__(resref=resref, restype=restype, data=data)
        self.resource_id: int = res_id  # Resource ID from KEY file
        self._offset: int = 0  # Offset in BIF file
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
        return self.resource_id == other.resource_id and self.restype == other.restype and self.size == other.size

    def __hash__(self) -> int:
        """Hash resource."""
        return hash((self.resource_id, self.restype, self.size))

    def __str__(self) -> str:
        """Get string representation."""
        return f"{self.resref}:{self.restype.name}[{self.size}b]"


class BIF(BiowareArchive):
    """Represents a BIF/BZF file in the Aurora engine.

    BIF (Binary Index Format) files contain the actual resource data,
    while BZF files are lzma-compressed BIF files.
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
        self.bif_type: BIFType = bif_type
        self._resources: list[BIFResource] = []
        self._resource_dict: dict[ResourceIdentifier, BIFResource] = {}
        self._id_lookup: dict[int, BIFResource] = {}
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
            resource.resource_id = res_id
        self._resources.append(resource)
        self._resource_dict[ResourceIdentifier(str(resref), restype)] = resource
        self._id_lookup[resource.resource_id] = resource
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
            del self._id_lookup[resource.resource_id]
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
            self._id_lookup[resource.resource_id] = resource

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
                    resid=resource.resource_id,
                    bif_index=bif_idx,
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
            bif_res: BIFResource | None = self.get_resource_by_id(key_res.resource_id)
            if bif_res is None:
                errors.append(f"Resource {key_res.resref}:{key_res.restype} from KEY not found in BIF")
                continue

            if bif_res.restype != key_res.restype:
                errors.append(f"Resource {key_res.resref} type mismatch: KEY={key_res.restype}, BIF={bif_res.restype}")

        # Check all BIF resources exist in KEY
        for bif_res in self._resources:
            key_res: KeyEntry | None = next((r for r in key_resources if r.resource_id == bif_res.resource_id), None)
            if key_res is None:
                errors.append(f"Resource ID {bif_res.resource_id} from BIF not found in KEY")

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
        key_resources: dict[int, KeyEntry] = {r.resource_id: r for r in key.key_entries if r.bif_index == bif_idx}

        # Update BIF resource names from KEY
        for resource in self._resources:
            key_res: KeyEntry | None = key_resources.get(resource.resource_id)
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
            key_res = KeyEntry(resref=resource.resref, restype=resource.restype, resid=resource.resource_id)
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
        key_resources: dict[int, KeyEntry] = {r.resource_id: r for r in key.key_entries if r.bif_index == bif_idx}

        # Update BIF resource names from KEY
        for resource in self._resources:
            if key_res := key_resources.get(resource.resource_id):
                if resource.restype != key_res.restype:
                    errors.append(f"Resource type mismatch for ID {resource.resource_id}: " f"BIF={resource.restype}, KEY={key_res.restype}")
                resource.resref = key_res.resref
            else:
                errors.append(f"Resource ID {resource.resource_id} from BIF not found in KEY")

        # Check for KEY resources not in BIF
        bif_ids: set[int] = {r.resource_id for r in self._resources}
        errors.extend([f"Resource {key_res.resref}:{key_res.restype} from KEY not found in BIF (ID: {key_res.resource_id})" for key_res in key_resources.values() if key_res.resource_id not in bif_ids])  # noqa: E501

        # Rebuild lookup tables with new names
        self.build_lookup_tables()

        return errors

    def reorganize_by_type(self) -> None:
        """Reorganize resources by grouping them by type.

        This can improve access performance when reading resources of the same type.
        """
        self._resources.sort(key=lambda r: (r.restype.type_id, r.resource_id))
        self._modified = True
        self.build_lookup_tables()
