from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from pykotor.common.misc import ResRef
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from typing_extensions import Self  # pyright: ignore[reportMissingModuleSource]


class BifEntry:
    """Represents a BIF file entry in the KEY file."""

    def __init__(self):
        self.filename: str = ""
        self.filesize: int = 0
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
    """Represents a resource entry in the KEY file."""

    def __init__(
        self,
        resref: str | ResRef | None = None,
        restype: ResourceType | None = None,
        resid: int | None = None,
    ):
        self.resref: ResRef = ResRef.from_blank() if resref is None else ResRef(resref)
        self.restype: ResourceType = ResourceType.INVALID if restype is None else restype
        self.resource_id: int = 0 if resid is None else resid

    @classmethod
    def from_bif(
        cls,
        resref: str | ResRef,
        restype: ResourceType,
        bif_index: int,
    ) -> Self:
        """Create a key entry from a BIF index."""
        entry: Self = cls()
        entry.resref = ResRef(resref)
        entry.restype = restype
        entry.resource_id = bif_index << 20
        return entry

    @classmethod
    def from_res(
        cls,
        resref: str | ResRef,
        restype: ResourceType,
        res_index: int,
    ) -> Self:
        entry: Self = cls()
        entry.resref = ResRef(resref)
        entry.restype = restype
        entry.resource_id = res_index
        return entry

    @property
    def bif_index(self) -> int:
        """Get the index into the BIF file table (top 12 bits of resource_id)."""
        return self.resource_id >> 20

    @property
    def res_index(self) -> int:
        """Get the index into the resource table (bottom 20 bits of resource_id)."""
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
    """Represents a KEY file in the Aurora engine."""

    FILE_TYPE: ClassVar[str] = "KEY "
    FILE_VERSION: ClassVar[str] = "V1  "
    HEADER_SIZE: ClassVar[int] = 64  # Fixed header size
    BIF_ENTRY_SIZE: ClassVar[int] = 12  # Size of each BIF entry
    KEY_ENTRY_SIZE: ClassVar[int] = 22  # Size of each resource entry (16 + 2 + 4)

    def __init__(self):
        self.file_type: str = self.FILE_TYPE
        self.file_version: str = self.FILE_VERSION
        self.build_year: int = 0
        self.build_day: int = 0
        self.bif_entries: list[BifEntry] = []
        self.key_entries: list[KeyEntry] = []
        self._resource_lookup: dict[tuple[str, ResourceType], KeyEntry] = {}
        self._bif_lookup: dict[str, BifEntry] = {}
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
