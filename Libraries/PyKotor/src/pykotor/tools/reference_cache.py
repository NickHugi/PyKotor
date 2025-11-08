from __future__ import annotations

import os
import traceback

from contextlib import suppress
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Sequence, Union

from loggerplus import RobustLogger

from pykotor.common.language import LocalizedString
from pykotor.common.stream import BinaryReader
from pykotor.extract.file import FileResource  # noqa: PLC0415

# Runtime import for find_tlk_entry_references
from pykotor.extract.installation import SearchLocation  # noqa: PLC0415
from pykotor.extract.twoda import K1Columns2DA, K2Columns2DA  # noqa: PLC0415
from pykotor.resource.formats.gff.gff_auto import read_gff
from pykotor.resource.formats.gff.gff_data import GFFContent, GFFFieldType, GFFList, GFFStruct
from pykotor.resource.formats.ncs.ncs_auto import read_ncs  # noqa: PLC0415
from pykotor.resource.formats.ssf.ssf_auto import read_ssf
from pykotor.resource.formats.ssf.ssf_data import SSFSound
from pykotor.resource.formats.twoda.twoda_auto import read_2da
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pathlib import Path

    from pykotor.common.misc import Game
    from pykotor.extract.capsule import Capsule
    from pykotor.extract.file import ResourceIdentifier
    from pykotor.extract.installation import Installation
    from pykotor.resource.formats.gff import GFF
    from pykotor.resource.formats.ncs.ncs_data import NCS
    from pykotor.resource.formats.ssf.ssf_data import SSF
    from pykotor.resource.formats.twoda.twoda_data import TwoDA


# Global cache for scan results to avoid re-scanning unchanged resources
# Key: (filepath, offset, size, mtime) -> Value: list of (strref, location) tuples
_SCAN_RESULTS_CACHE: dict[tuple, list[tuple[int, str]]] = {}


def clear_scan_cache() -> None:
    """Clear the global scan results cache to free memory."""
    _SCAN_RESULTS_CACHE.clear()


# Late import to avoid circular dependency
def _get_2da_columns():
    from pykotor.extract.twoda import K1Columns2DA, K2Columns2DA

    return K1Columns2DA, K2Columns2DA


# Import GFF field mapping from twoda module
def _get_gff_field_to_2da_mapping():
    from pykotor.extract.twoda import TwoDARegistry

    return TwoDARegistry.gff_field_mapping()


# GFF field name to 2DA filename mappings
# Maps GFF field names to the 2DA files they reference
# This is used by TwoDAMemoryReferenceCache and other modules that need to know
# which GFF fields reference which 2DA files
GFF_FIELD_TO_2DA_MAPPING: dict[str, ResourceIdentifier] = _get_gff_field_to_2da_mapping()


# Logging helpers for reference caches
# Log level: 0 = normal, 1 = verbose, 2 = debug
_log_level = 2 if os.environ.get("KOTORDIFF_DEBUG") else (1 if os.environ.get("KOTORDIFF_VERBOSE") else 0)


def _log_debug(msg: str) -> None:
    """Log debug message if debug level is enabled."""
    if _log_level >= 2:  # noqa: PLR2004
        print(f"[DEBUG] {msg}")


def _log_verbose(msg: str) -> None:
    """Log verbose message if verbose level is enabled."""
    if _log_level >= 1:
        print(f"[VERBOSE] {msg}")


# Location dataclasses for StrRef references
@dataclass
class TwoDARefLocation:
    """A reference to a StrRef in a 2DA file."""

    row_index: int
    column_name: str


@dataclass
class SSFRefLocation:
    """A reference to a StrRef in an SSF file."""

    sound: SSFSound


@dataclass
class GFFRefLocation:
    """A reference to a StrRef in a GFF file."""

    field_path: str  # e.g. "FirstName", "Description", "ItemList[0].LocalizedName"


@dataclass
class NCSRefLocation:
    """A reference to a StrRef in an NCS file."""

    byte_offset: int


# Union type for all reference location types
StrRefLocation = Union[TwoDARefLocation, SSFRefLocation, GFFRefLocation, NCSRefLocation]


@dataclass
class StrRefSearchResult:
    """Result of a StrRef reference search containing file resource and typed location objects."""

    resource: FileResource
    locations: Sequence[StrRefLocation]


class StrRefReferenceCache:
    """Cache of StrRef references found during resource scanning.

    Maps StrRef -> list of (resource_identifier, locations) where it's referenced.
    """

    def __init__(self, game: Game):
        """Initialize cache with game-specific 2DA column definitions.

        Args:
            game: Game instance for determining which 2DA columns contain StrRefs
        """
        self.game: Game = game

        # Map: strref -> {resource_identifier: [field_paths]}
        # Using dict for O(1) lookups instead of list for O(n) linear search
        self._cache: dict[int, dict[ResourceIdentifier, list[str]]] = {}

        # Statistics
        self._total_references_found: int = 0
        self._files_with_strrefs: set[str] = set()

        # Get game-specific 2DA column definitions
        K1Columns2DA, K2Columns2DA = _get_2da_columns()
        if game.is_k1():
            self._strref_2da_columns = K1Columns2DA.StrRefs.as_dict()
        elif game.is_k2():
            self._strref_2da_columns = K2Columns2DA.StrRefs.as_dict()
        else:
            self._strref_2da_columns = {}

    def scan_resource(
        self,
        resource: FileResource,
        data: bytes,
    ) -> None:
        """Scan a resource for StrRef references and cache them.

        Args:
            resource: FileResource being scanned
            data: Resource data bytes
        """
        identifier: ResourceIdentifier = resource.identifier()
        restype: ResourceType = resource.restype()
        filename: str = resource.filename().lower()

        try:
            # 2DA files
            if restype is ResourceType.TwoDA and filename in self._strref_2da_columns:
                self._scan_2da(identifier, data, filename)

            # SSF files
            elif restype is ResourceType.SSF:
                self._scan_ssf(identifier, data)

            # NCS files - FIXME: TEMPORARILY DISABLED (will revisit later)
            # elif restype is ResourceType.NCS:
            #     self._scan_ncs(identifier, data)

            # GFF files (only try to parse if restype indicates it's a GFF file)
            elif restype.is_gff():
                try:
                    gff_obj = read_gff(data)
                    self._scan_gff(identifier, gff_obj.root)
                except Exception:  # noqa: BLE001, S110
                    # Failed to parse GFF, skip
                    pass
            # All other file types (textures, sounds, etc.) don't contain StrRefs, skip silently

        except Exception:  # noqa: BLE001, S110
            # Skip files that fail to scan
            pass

    def _scan_2da(
        self,
        identifier: ResourceIdentifier,
        data: bytes,
        filename: str,
    ) -> None:
        """Scan 2DA file for StrRef references."""
        twoda_obj = read_2da(data)
        columns_with_strrefs: set[str] = self._strref_2da_columns[filename]

        for row_idx in range(twoda_obj.get_height()):
            for column_name in tuple(columns_with_strrefs):
                if column_name == ">>##HEADER##<<":
                    continue

                cell = twoda_obj.get_cell(row_idx, column_name)
                if cell and cell.strip().isdigit():
                    strref = int(cell.strip())
                    location = f"row_{row_idx}.{column_name}"
                    _log_debug(f"Found StrRef {strref} in 2DA file '{filename}' at row {row_idx}, column '{column_name}'")
                    self._add_reference(strref, identifier, location)

    def _scan_ssf(
        self,
        identifier: ResourceIdentifier,
        data: bytes,
    ) -> None:
        """Scan SSF file for StrRef references."""
        ssf_obj = read_ssf(data)
        filename: str = f"{identifier.resname}.{identifier.restype.extension}"

        for sound in SSFSound:
            strref: int | None = ssf_obj.get(sound)
            if strref is not None and strref != -1:
                location = f"sound_{sound.name}"
                _log_debug(f"Found StrRef {strref} in SSF file '{filename}' at sound slot '{sound.name}'")
                self._add_reference(strref, identifier, location)

    def _scan_ncs(
        self,
        identifier: ResourceIdentifier,
        data: bytes,
    ) -> None:
        """Scan NCS file for StrRef references in CONSTI instructions (optimized).

        FIXME: TEMPORARILY DISABLED - Will revisit NCS scanning later.
        """
        # TEMPORARILY DISABLED - NCS scanning will be revisited later
        return
        # try:
        #     # Validate header - use direct bytes comparison instead of BinaryReader
        #     if len(data) < 13 or data[:4] != b"NCS " or data[4:8] != b"V1.0" or data[8] != 0x42:  # noqa: PLR2004
        #         return
        #
        #     # Extract total_size using struct (faster than BinaryReader)
        #     total_size = struct.unpack(">I", data[9:13])[0]
        #
        #     # Use direct byte indexing instead of BinaryReader (much faster)
        #     pos = 13  # Start after header
        #     while pos < total_size and pos < len(data):
        #         if pos + 1 >= len(data):
        #             break
        #
        #         opcode = data[pos]
        #         qualifier = data[pos + 1]
        #         pos += 2
        #
        #         if opcode == 0x04 and qualifier == 0x03:  # CONSTI  # noqa: PLR2004
        #             if pos + 3 >= len(data):
        #                 break
        #             value_offset = pos
        #             # Use struct.unpack for int32 (much faster than read_int32)
        #             const_value = struct.unpack(">i", data[pos:pos + 4])[0]
        #             pos += 4
        #             # Only cache positive values that could be StrRefs (negative are typically indices)
        #             if const_value >= 0:
        #                 location = f"offset_{value_offset}"
        #                 self._add_reference(const_value, identifier, location)
        #         elif opcode == 0x04:  # CONSTx  # noqa: PLR2004
        #             if qualifier == 0x04:  # CONSTF  # noqa: PLR2004
        #                 pos += 4
        #             elif qualifier == 0x05:  # CONSTS  # noqa: PLR2004
        #                 if pos + 1 >= len(data):
        #                     break
        #                 str_len = struct.unpack(">H", data[pos:pos + 2])[0]
        #                 pos += 2 + str_len
        #             elif qualifier == 0x06:  # CONSTO  # noqa: PLR2004
        #                 pos += 4
        #         elif opcode in (0x01, 0x03, 0x26, 0x27):  # CPDOWNSP, CPTOPSP, CPDOWNBP, CPTOPBP
        #             pos += 6
        #         elif opcode == 0x2C:  # STORE_STATE  # noqa: PLR2004
        #             pos += 8
        #         elif opcode in (0x1B, 0x1D, 0x1E, 0x1F, 0x23, 0x24, 0x25, 0x28, 0x29):
        #             pos += 4
        #         elif opcode == 0x05:  # ACTION  # noqa: PLR2004
        #             pos += 3
        #         elif opcode == 0x21:  # DESTRUCT  # noqa: PLR2004
        #             pos += 6
        #         elif opcode == 0x0B and qualifier == 0x24:  # EQUALTT  # noqa: PLR2004
        #             pos += 2
        #         elif opcode == 0x0C and qualifier == 0x24:  # NEQUALTT  # noqa: PLR2004
        #             pos += 2
        # except Exception:  # noqa: BLE001, S110
        #     pass

    def _scan_gff(
        self,
        identifier: ResourceIdentifier,
        gff_struct: GFFStruct,
        current_path: str = "",
    ) -> None:
        """Recursively scan GFF structure for LocalizedString fields with StrRefs.

        Args:
            identifier: Resource identifier being scanned
            gff_struct: GFF struct to scan
            current_path: Current field path as string (e.g., "FirstName" or "ItemList[0]")
        """
        for label, field_type, value in gff_struct:
            # Build field path using string concatenation (much faster than path operations)
            field_path: str = f"{current_path}.{label}" if current_path else label

            # LocalizedString fields
            is_locstring: bool = field_type == GFFFieldType.LocalizedString
            if is_locstring:
                locstring: LocalizedString = value  # type: ignore[assignment]
                if locstring.stringref != -1:
                    filename: str = f"{identifier.resname}.{identifier.restype.extension}"
                    _log_debug(f"Found StrRef {locstring.stringref} in GFF file '{filename}' at field path '{field_path}'")
                    self._add_reference(locstring.stringref, identifier, field_path)

            # Nested structs
            is_struct: bool = field_type == GFFFieldType.Struct
            if is_struct and isinstance(value, GFFStruct):
                self._scan_gff(identifier, value, field_path)

            # Lists
            is_list: bool = field_type == GFFFieldType.List
            if is_list and isinstance(value, GFFList):
                for idx, item in enumerate(value):
                    if isinstance(item, GFFStruct):
                        # Use string formatting for list indices (faster than path ops)
                        list_path: str = f"{field_path}[{idx}]"
                        self._scan_gff(identifier, item, list_path)

    def _add_reference(
        self,
        strref: int,
        identifier: ResourceIdentifier,
        location: str,
    ) -> None:
        """Add a StrRef reference to the cache.

        Uses O(1) dictionary lookup instead of O(n) linear search for performance.
        """
        filename: str = f"{identifier.resname}.{identifier.restype.extension}"

        # Track statistics
        self._total_references_found += 1
        self._files_with_strrefs.add(filename)

        # Initialize dict for this StrRef if needed
        if strref not in self._cache:
            self._cache[strref] = {}
            _log_verbose(f"  → Cached new StrRef {strref} from '{filename}' at '{location}'")

        # O(1) dictionary lookup instead of O(n) linear search
        if identifier in self._cache[strref]:
            # Identifier already exists, append location
            self._cache[strref][identifier].append(location)
        else:
            # New identifier for this StrRef
            self._cache[strref][identifier] = [location]

    def get_references(self, strref: int) -> list[tuple[ResourceIdentifier, list[str]]]:
        """Get all resources that reference a specific StrRef.

        Args:
            strref: StrRef to look up

        Returns:
            List of (resource_identifier, [field_paths]) tuples
        """
        # Convert dict format back to list of tuples for compatibility
        strref_dict = self._cache.get(strref, {})
        return [(identifier, locations) for identifier, locations in strref_dict.items()]

    def has_references(self, strref: int) -> bool:
        """Check if any resources reference this StrRef."""
        return strref in self._cache

    def get_statistics(self) -> dict[str, int]:
        """Get cache statistics.

        Returns:
            Dictionary with statistics about cached StrRef references
        """
        return {
            "unique_strrefs": len(self._cache),
            "total_references": self._total_references_found,
            "files_with_strrefs": len(self._files_with_strrefs),
        }

    def log_summary(self) -> None:
        """Log a summary of the cache contents."""
        stats: dict[str, int] = self.get_statistics()
        _log_verbose(
            f"\nStrRef Cache Summary:\n"
            f"  • {stats['unique_strrefs']} unique StrRefs cached\n"
            f"  • {stats['total_references']} total StrRef references found\n"
            f"  • {stats['files_with_strrefs']} files contain StrRef references"
        )

    def to_dict(self) -> dict[str, list[dict[str, str | list[str]]]]:
        """Serialize cache to dictionary for saving.

        Returns:
            Dictionary mapping strref -> list of {resname, restype, locations}
        """
        serialized: dict[str, list[dict[str, str | list[str]]]] = {}

        for strref, references_dict in self._cache.items():
            serialized[str(strref)] = [
                {
                    "resname": identifier.resname,
                    "restype": identifier.restype.extension,
                    "locations": locations,
                }
                for identifier, locations in references_dict.items()
            ]

        return serialized

    @classmethod
    def from_dict(
        cls,
        game: Game,
        data: dict[str, list[dict[str, str | list[str]]]],
    ) -> StrRefReferenceCache:
        """Restore cache from dictionary.

        Args:
            game: Game instance for cache initialization
            data: Serialized cache data

        Returns:
            Restored StrRefReferenceCache instance
        """
        from pykotor.extract.file import ResourceIdentifier  # noqa: PLC0415
        from pykotor.resource.type import ResourceType  # noqa: PLC0415

        cache = cls(game)

        for strref_str, references in data.items():
            strref: int = int(strref_str)
            cache._cache[strref] = {}

            for ref_data in references:
                resname: str = str(ref_data["resname"])
                restype_ext: str = str(ref_data["restype"])
                locations: list[str] = list(ref_data["locations"])  # type: ignore[arg-type]

                # Recreate ResourceIdentifier
                restype: ResourceType = ResourceType.from_extension(restype_ext)
                identifier = ResourceIdentifier(resname, restype)

                # Use dict assignment
                cache._cache[strref][identifier] = locations

                # Update statistics
                cache._total_references_found += len(locations)
                filename: str = f"{resname}.{restype_ext}"
                cache._files_with_strrefs.add(filename)

        _log_verbose(f"Restored StrRef cache from saved data: {len(cache._cache)} StrRefs, {cache._total_references_found} references")

        return cache


class TwoDAMemoryReferenceCache:
    """Cache of 2DA memory token references found during resource scanning.

    Maps (2da_filename, row_index) -> {resource_identifier: [field_paths]}
    where that row is referenced.

    This enables automatic generation of linking patches when 2DA rows are modified,
    similar to how StrRef linking works.
    """

    def __init__(self, game: Game):
        """Initialize cache.

        Args:
            game: Game instance (for potential game-specific logic)
        """
        self.game: Game = game

        # Map: (2da_filename, row_index) -> {resource_identifier: [field_paths]}
        # Using dict for O(1) lookups instead of list for O(n) linear search
        self._cache: dict[tuple[str, int], dict[ResourceIdentifier, list[str]]] = {}

        # Statistics
        self._total_references_found: int = 0
        self._files_with_2da_refs: set[str] = set()

    def scan_resource(
        self,
        resource: FileResource,
        data: bytes,
    ) -> None:
        """Scan a resource for 2DA memory references and cache them.

        Args:
            resource: FileResource being scanned
            data: Resource data bytes
        """
        identifier: ResourceIdentifier = resource.identifier()
        restype: ResourceType = resource.restype()

        try:
            # Only scan GFF files for 2DA references (use is_gff() for consistency with StrRef cache)
            if restype.is_gff():
                try:
                    gff_obj = read_gff(data)
                    self._scan_gff(identifier, gff_obj.root)
                except Exception:  # noqa: BLE001, S110
                    # Failed to parse GFF, skip
                    pass
            # All other file types don't contain 2DA references, skip silently

        except Exception:  # noqa: BLE001, S110
            # Skip files that fail to scan
            pass

    def _scan_gff(
        self,
        identifier: ResourceIdentifier,
        gff_struct: GFFStruct,
        current_path: str = "",
    ) -> None:
        """Recursively scan GFF structure for 2DA references.

        Args:
            identifier: Resource identifier
            gff_struct: GFF struct to scan
            current_path: Current field path as string (e.g., "Appearance" or "ItemList[0]")
        """
        # Get the mapping lazily to avoid circular dependency
        gff_field_to_2da_mapping = _get_gff_field_to_2da_mapping()

        for label, field_type, value in gff_struct:
            # Build field path using string concatenation (much faster than path operations)
            field_path: str = f"{current_path}.{label}" if current_path else label

            # Check if this field references a 2DA
            if label in gff_field_to_2da_mapping:
                # This field references a 2DA file
                twoda_identifier: ResourceIdentifier = gff_field_to_2da_mapping[label]
                twoda_filename = f"{twoda_identifier.resname}.{twoda_identifier.restype.extension}"

                # Extract the numeric value (row index)
                row_index: int | None = None
                if field_type in (
                    GFFFieldType.Int8,
                    GFFFieldType.Int16,
                    GFFFieldType.Int32,
                    GFFFieldType.Int64,
                ):
                    if isinstance(value, int):
                        row_index = value
                elif field_type in (
                    GFFFieldType.UInt8,
                    GFFFieldType.UInt16,
                    GFFFieldType.UInt32,
                    GFFFieldType.UInt64,
                ) and isinstance(value, int):
                    row_index = value

                if row_index is not None and row_index >= 0:
                    self._add_reference(twoda_filename, row_index, identifier, field_path)

            # Recurse into nested structures
            if field_type == GFFFieldType.Struct and isinstance(value, GFFStruct):
                self._scan_gff(identifier, value, field_path)
            elif field_type == GFFFieldType.List and isinstance(value, GFFList):
                for idx, item in enumerate(value):
                    if isinstance(item, GFFStruct):
                        # Use string formatting for list indices (faster than path ops)
                        list_path: str = f"{field_path}[{idx}]"
                        self._scan_gff(identifier, item, list_path)

    def _add_reference(
        self,
        twoda_filename: str,
        row_index: int,
        identifier: ResourceIdentifier,
        location: str,
    ) -> None:
        """Add a reference to the cache.

        Uses O(1) dictionary lookup instead of O(n) linear search for performance.

        Args:
            twoda_filename: Name of the 2DA file (e.g., "soundset.2da")
            row_index: Row index in the 2DA
            identifier: Resource identifier
            location: Field path in the GFF structure
        """
        key = (twoda_filename.lower(), row_index)
        filename: str = f"{identifier.resname}.{identifier.restype.extension}"

        # Track statistics
        self._total_references_found += 1
        self._files_with_2da_refs.add(filename)

        # Initialize dict for this 2DA row if needed
        if key not in self._cache:
            self._cache[key] = {}

        # O(1) dictionary lookup instead of O(n) linear search
        if identifier in self._cache[key]:
            # Identifier already exists, append location
            self._cache[key][identifier].append(location)
        else:
            # New identifier for this 2DA row
            self._cache[key][identifier] = [location]

    def get_references(
        self,
        twoda_filename: str,
        row_index: int,
    ) -> list[tuple[ResourceIdentifier, list[str]]]:
        """Get all references to a specific 2DA row.

        Args:
            twoda_filename: Name of the 2DA file
            row_index: Row index in the 2DA

        Returns:
            List of (resource_identifier, field_paths) tuples
        """
        key = (twoda_filename.lower(), row_index)
        # Convert dict format back to list of tuples for compatibility
        twoda_dict = self._cache.get(key, {})
        return [(identifier, locations) for identifier, locations in twoda_dict.items()]

    def has_references(
        self,
        twoda_filename: str,
        row_index: int,
    ) -> bool:
        """Check if any resources reference this 2DA row.

        Args:
            twoda_filename: Name of the 2DA file
            row_index: Row index in the 2DA

        Returns:
            True if references exist
        """
        key = (twoda_filename.lower(), row_index)
        return key in self._cache

    def get_statistics(self) -> dict[str, int]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        unique_2da_refs = len(self._cache)
        return {
            "unique_2da_refs": unique_2da_refs,
            "total_references": self._total_references_found,
            "files_with_2da_refs": len(self._files_with_2da_refs),
        }

    def log_summary(self) -> None:
        """Log a summary of cache contents."""
        stats = self.get_statistics()
        _log_verbose(f"2DA Memory Reference Cache: {stats['unique_2da_refs']} unique 2DA rows referenced")
        _log_verbose(f"  Total references: {stats['total_references']}")
        _log_verbose(f"  Files with 2DA refs: {stats['files_with_2da_refs']}")

    def to_dict(self) -> dict[str, list[dict[str, str | int | list[str]]]]:
        """Serialize cache to dictionary for saving.

        Returns:
            Serialized cache data
        """
        result: dict[str, list[dict[str, str | int | list[str]]]] = {}

        for (twoda_filename, row_index), references_dict in self._cache.items():
            key = f"{twoda_filename}:{row_index}"
            result[key] = [
                {
                    "resname": identifier.resname,
                    "restype": identifier.restype.extension,
                    "locations": locations,
                }
                for identifier, locations in references_dict.items()
            ]

        return result

    @classmethod
    def from_dict(
        cls,
        game: Game,
        data: dict[str, list[dict[str, str | int | list[str]]]],
    ) -> TwoDAMemoryReferenceCache:
        """Restore cache from serialized dictionary.

        Args:
            game: Game instance
            data: Serialized cache data

        Returns:
            Restored TwoDAMemoryReferenceCache
        """
        from pykotor.extract.file import ResourceIdentifier  # noqa: PLC0415
        from pykotor.resource.type import ResourceType  # noqa: PLC0415

        cache = cls(game)

        for key_str, references in data.items():
            # Parse key: "soundset.2da:123" -> ("soundset.2da", 123)
            twoda_filename, row_index_str = key_str.rsplit(":", 1)
            row_index = int(row_index_str)

            cache_key = (twoda_filename.lower(), row_index)
            cache._cache[cache_key] = {}

            for ref_data in references:
                resname: str = str(ref_data["resname"])
                restype_ext: str = str(ref_data["restype"])
                locations: list[str] = list(ref_data["locations"])  # type: ignore[arg-type]

                # Recreate ResourceIdentifier
                restype: ResourceType = ResourceType.from_extension(restype_ext)
                if restype is None or not restype.is_valid():
                    continue

                identifier = ResourceIdentifier(resname, restype)

                # Use dict assignment
                cache._cache[cache_key][identifier] = locations

                # Update statistics
                cache._total_references_found += len(locations)
                filename: str = f"{resname}.{restype_ext}"
                cache._files_with_2da_refs.add(filename)

        return cache


def find_all_strref_references(
    installation: Installation,
    strrefs: list[int],
    cache: StrRefReferenceCache | None = None,
    logger: Callable[[str], None] | None = None,
) -> tuple[dict[int, list[StrRefSearchResult]], StrRefReferenceCache]:
    """Find all references to multiple StrRefs in an installation using batch processing.

    This function scans resources once and finds references to all requested StrRefs,
    providing significant performance improvement over calling find_strref_references
    multiple times.

    Args:
        installation: The game installation to search
        strrefs: List of StrRef IDs to find references for
        cache: Optional pre-built StrRefReferenceCache (will build if not provided)
        logger: Optional logging function

    Returns:
    -------
        A tuple containing:
        - Dictionary mapping strref -> list of StrRefSearchResult
        - The StrRefReferenceCache instance used for the search
    """
    if not strrefs:
        return {}, cache or StrRefReferenceCache(installation.game())

    # Build cache if not provided
    if cache is None:
        if logger:
            logger(f"Building StrRef cache for {len(strrefs)} StrRefs for installation {installation.path()}...")
        cache = StrRefReferenceCache(installation.game())

        # Scan all resources to build the cache
        resource_count = 0
        skipped_count = 0
        last_logged_count = 0
        log_interval = 500  # Log progress every 500 resources

        for resource in installation:
            try:
                # Skip RIM files - they're not used at runtime
                try:
                    relative_path = resource.filepath().relative_to(installation.path())
                    path_parts = relative_path.parts
                    if path_parts and path_parts[0].lower() == "rims":
                        skipped_count += 1
                        continue
                except ValueError:
                    abs_path = resource.filepath()
                    if "rims" in abs_path.parts:
                        skipped_count += 1
                        continue

                # Filter by resource type: Only scan types that can contain StrRefs
                # This dramatically improves performance by skipping textures, models, audio, etc.
                restype = resource.restype()
                # StrRefs can only exist in: GFF files, 2DA files, SSF files, NCS files
                can_contain_strref = (
                    restype.is_gff()
                    or restype is ResourceType.TwoDA
                    or restype is ResourceType.SSF
                    or restype is ResourceType.NCS
                )
                if not can_contain_strref:
                    skipped_count += 1
                    continue

                data = resource.data()
                cache.scan_resource(resource, data)
                resource_count += 1

                # Log progress periodically
                if logger and resource_count - last_logged_count >= log_interval:
                    logger(f"  Scanning for StrRefs... {resource_count} resources processed for installation {installation.path()}")
                    last_logged_count = resource_count

            except Exception:  # noqa: BLE001, S110, S112
                skipped_count += 1
                continue

        if logger:
            logger(f"Cache built: scanned {resource_count} resources (skipped {skipped_count} files) for installation {installation.path()}")

    # Convert cache entries to StrRefSearchResult format
    results: dict[int, list[StrRefSearchResult]] = {}

    # Build a map of ResourceIdentifier -> FileResource by iterating installation ONCE
    # This is moved outside the strref loop to avoid re-iterating for each strref
    identifier_to_resource: dict[ResourceIdentifier, FileResource] = {}
    for res in installation:
        try:
            identifier_to_resource[res.identifier()] = res
        except Exception:  # noqa: BLE001, S110, S112
            continue

    for strref in strrefs:
        cache_entries = cache.get_references(strref)
        if not cache_entries:
            results[strref] = []
            continue

        # Convert cache format to StrRefSearchResult format
        strref_results: list[StrRefSearchResult] = []

        for identifier, location_strings in cache_entries:
            # Get the FileResource from our map
            try:
                found_resource: FileResource | None = identifier_to_resource.get(identifier)
                if found_resource:
                    # Convert location strings to proper location objects
                    locations: list[TwoDARefLocation | SSFRefLocation | GFFRefLocation | NCSRefLocation] = []

                    for loc_str in location_strings:
                        # Parse location string format: "row_12.name", "sound_Battlecry 1", "field_path", or byte offset
                        if loc_str.startswith("row_"):
                            # 2DA reference: "row_12.name"
                            parts = loc_str.replace("row_", "").split(".", 1)
                            if len(parts) == 2:
                                row_idx = int(parts[0])
                                column_name = parts[1]
                                locations.append(TwoDARefLocation(row_index=row_idx, column_name=column_name))
                        elif loc_str.startswith("sound_"):
                            # SSF reference: "sound_Battlecry 1"
                            sound_name = loc_str.replace("sound_", "")
                            try:
                                sound = SSFSound[sound_name]
                                locations.append(SSFRefLocation(sound=sound))
                            except KeyError:  # noqa: S110
                                pass
                        elif loc_str.startswith("offset_"):
                            # NCS reference: "offset_1234"
                            byte_offset = int(loc_str.replace("offset_", ""))
                            locations.append(NCSRefLocation(byte_offset=byte_offset))
                        else:
                            # GFF reference: field path
                            locations.append(GFFRefLocation(field_path=loc_str))

                    if locations:
                        strref_results.append(StrRefSearchResult(resource=found_resource, locations=locations))
            except Exception:  # noqa: BLE001, S110, S112
                continue

        results[strref] = strref_results

    return results, cache


def find_strref_references(
    installation: Installation,
    strref: int,
    cache: StrRefReferenceCache | None = None,
    logger: Callable[[str], None] | None = None,
) -> list[StrRefSearchResult]:
    """Find all references to a specific StrRef in an installation.

    This function scans 2DA, SSF, GFF, and NCS files for references to the given StrRef
    and returns complete location information for each reference.

    Args:
        installation: The game installation to search
        strref: The StrRef ID to find references for
        logger: Optional logging function

    Returns:
        List of StrRefSearchResult containing resources and their exact reference locations
    """
    K1Columns2DA, K2Columns2DA = _get_2da_columns()
    game = installation.game()

    def format_path_with_installation_prefix(path_str: str) -> str:
        """Format a relative path with the installation folder name as a prefix.

        Args:
            path_str: The relative path string (e.g., "data/2da.bif/planetary.2da")

        Returns:
            Formatted path with installation folder prefix (e.g., "swkotor/data/2da.bif/planetary.2da")
        """
        installation_path = installation.path()
        installation_folder = installation_path.name if installation_path else "unknown"
        return f"{installation_folder}/{path_str}"

    # Get game-specific 2DA columns that contain StrRefs
    strref_2da_columns: dict[str, set[str]] = {}
    if game.is_k1():
        strref_2da_columns = K1Columns2DA.StrRefs.as_dict()
    elif game.is_k2():
        strref_2da_columns = K2Columns2DA.StrRefs.as_dict()

    results: list[StrRefSearchResult] = []

    def scan_2da(resource: FileResource) -> StrRefSearchResult | None:
        """Scan a 2DA file and return locations where the StrRef is found."""
        try:
            twoda = read_2da(resource.data())
            filename = resource.filename().lower()

            if filename not in strref_2da_columns:
                return None

            locations: list[TwoDARefLocation] = []
            columns = strref_2da_columns[filename]

            for row_idx in range(twoda.get_height()):
                for column_name in columns:
                    if column_name == ">>##HEADER##<<":
                        continue

                    cell = twoda.get_cell(row_idx, column_name)
                    if cell and cell.strip().isdigit() and int(cell.strip()) == strref:
                        locations.append(TwoDARefLocation(row_index=row_idx, column_name=column_name))

                        if logger:
                            # Use path_ident() to show full path including resource inside BIF/capsule
                            try:
                                path_ident = resource.path_ident()
                                relative_path = path_ident.relative_to(installation.path())
                                path_str = relative_path.as_posix()
                            except ValueError:
                                path_str = str(resource.path_ident())
                            # Format path with installation folder prefix
                            formatted_path = format_path_with_installation_prefix(path_str)
                            logger(f"    Found at: row {row_idx}, column '{column_name}' at {formatted_path}")

            if locations:
                return StrRefSearchResult(resource=resource, locations=locations)

        except Exception:  # noqa: BLE001, S110
            pass

        return None

    def scan_ssf(resource: FileResource) -> StrRefSearchResult | None:
        """Scan an SSF file and return locations where the StrRef is found."""
        try:
            ssf = read_ssf(resource.data())
            locations: list[SSFRefLocation] = []

            for sound in SSFSound:
                sound_strref = ssf.get(sound)
                if sound_strref == strref:
                    locations.append(SSFRefLocation(sound=sound))

                    if logger:
                        # Use path_ident() to show full path including resource inside BIF/capsule
                        try:
                            path_ident = resource.path_ident()
                            relative_path = path_ident.relative_to(installation.path())
                            path_str = relative_path.as_posix()
                        except ValueError:
                            path_str = str(resource.path_ident())
                        # Format path with installation folder prefix
                        formatted_path = format_path_with_installation_prefix(path_str)
                        logger(f"    Found at: sound slot '{sound.name}' at {formatted_path}")

            if locations:
                return StrRefSearchResult(resource=resource, locations=locations)

        except Exception:  # noqa: BLE001, S110
            pass

        return None

    def scan_gff(resource: FileResource) -> StrRefSearchResult | None:
        """Scan a GFF file and return locations where the StrRef is found."""
        try:
            gff = read_gff(resource.data())
            locations: list[GFFRefLocation] = []

            def recurse_gff(gff_struct: GFFStruct, path_prefix: str = "") -> None:
                """Recursively scan GFF struct."""
                for field_label, ftype, fval in gff_struct:
                    field_path = f"{path_prefix}.{field_label}" if path_prefix else field_label

                    try:
                        # Check LocalizedString fields
                        if ftype == GFFFieldType.LocalizedString and isinstance(fval, LocalizedString):
                            if fval.stringref == strref:
                                locations.append(GFFRefLocation(field_path=field_path))

                        # Recurse into nested structs
                        elif ftype == GFFFieldType.Struct and isinstance(fval, GFFStruct):
                            recurse_gff(fval, field_path)

                        # Recurse into list items
                        elif ftype == GFFFieldType.List and isinstance(fval, GFFList):
                            for idx, item in enumerate(fval):
                                if isinstance(item, GFFStruct):
                                    list_path = f"{field_path}[{idx}]"
                                    recurse_gff(item, list_path)
                    except Exception as e:  # noqa: BLE001
                        # Individual field errors - log but continue processing other fields
                        if logger:
                            try:
                                relative_path = resource.filepath().relative_to(installation.path())
                                path_str = relative_path.as_posix()
                            except ValueError:
                                path_str = str(resource.filepath())
                            logger(f"[Debug] Error processing GFF field '{field_path}' in {path_str}: {e.__class__.__name__}: {e}")
                        print(traceback.format_exc())

            recurse_gff(gff.root)

            if locations and logger:
                try:
                    # Use path_ident() to show full path including resource inside BIF/capsule
                    path_ident = resource.path_ident()
                    relative_path = path_ident.relative_to(installation.path())
                    path_str = relative_path.as_posix()
                except ValueError:
                    path_str = str(resource.path_ident())
                # Format path with installation folder prefix
                formatted_path = format_path_with_installation_prefix(path_str)
                for location in locations:
                    logger(f"    Found at: field path '{location.field_path}' at {formatted_path}")

            if locations:
                return StrRefSearchResult(resource=resource, locations=locations)

        except Exception as e:  # noqa: BLE001, S110
            # Log which file failed to parse, but don't spam on expected failures (non-GFF files)
            if logger:
                try:
                    relative_path = resource.filepath().relative_to(installation.path())
                    path_str = relative_path.as_posix()
                except ValueError:
                    path_str = str(resource.filepath())
                logger(f"[Debug] Error scanning GFF {resource.filename()}: {e.__class__.__name__}: {e}")
            print(traceback.format_exc())

        return None

    def scan_ncs(resource: FileResource) -> StrRefSearchResult | None:
        """Scan an NCS file and return byte offsets where the StrRef is found in CONSTI instructions."""
        try:
            locations: list[NCSRefLocation] = []
            ncs_data = resource.data()

            # Parse NCS bytecode to find CONSTI instructions
            with BinaryReader.from_auto(ncs_data) as reader:
                if reader.read_string(4) != "NCS ":
                    return None
                if reader.read_string(4) != "V1.0":
                    return None
                magic_byte = reader.read_uint8()
                if magic_byte != 0x42:  # noqa: PLR2004
                    return None
                total_size = reader.read_uint32(big=True)

                # OPTIMIZATION: Removed redundant remaining() check - if position() < total_size,
                # then remaining() = total_size - position() > 0. This eliminates ~902k redundant
                # position() calls (one per loop iteration via remaining()).
                while reader.position() < total_size:
                    opcode = reader.read_uint8()
                    qualifier = reader.read_uint8()

                    if opcode == 0x04 and qualifier == 0x03:  # CONSTI  # noqa: PLR2004
                        value_offset = reader.position()
                        const_value = reader.read_int32(big=True)
                        if const_value == strref:
                            locations.append(NCSRefLocation(byte_offset=value_offset))
                    elif opcode == 0x04:  # CONSTx  # noqa: PLR2004
                        if qualifier == 0x04:  # CONSTF  # noqa: PLR2004
                            reader.skip(4)
                        elif qualifier == 0x05:  # CONSTS  # noqa: PLR2004
                            str_len = reader.read_uint16(big=True)
                            reader.skip(str_len)
                        elif qualifier == 0x06:  # CONSTO  # noqa: PLR2004
                            reader.skip(4)
                    elif opcode in (0x01, 0x03, 0x26, 0x27):  # CPDOWNSP, CPTOPSP, CPDOWNBP, CPTOPBP
                        reader.skip(6)
                    elif opcode == 0x2C:  # STORE_STATE  # noqa: PLR2004
                        reader.skip(8)
                    elif opcode in (0x1B, 0x1D, 0x1E, 0x1F, 0x23, 0x24, 0x25, 0x28, 0x29):
                        reader.skip(4)
                    elif opcode == 0x05:  # ACTION  # noqa: PLR2004
                        reader.skip(3)
                    elif opcode == 0x21:  # DESTRUCT  # noqa: PLR2004
                        reader.skip(6)
                    elif opcode == 0x0B and qualifier == 0x24:  # EQUALTT  # noqa: PLR2004
                        reader.skip(2)
                    elif opcode == 0x0C and qualifier == 0x24:  # NEQUALTT  # noqa: PLR2004
                        reader.skip(2)

            if locations:
                if logger:
                    try:
                        # Use path_ident() to show full path including resource inside BIF/capsule
                        path_ident = resource.path_ident()
                        relative_path = path_ident.relative_to(installation.path())
                        path_str = relative_path.as_posix()
                    except ValueError:
                        path_str = str(resource.path_ident())
                    # Format path with installation folder prefix
                    formatted_path = format_path_with_installation_prefix(path_str)
                    for location in locations:
                        logger(f"    Found at: byte offset {location.byte_offset:#X} (0x{location.byte_offset:X}) at {formatted_path}")

                return StrRefSearchResult(resource=resource, locations=locations)

        except Exception:  # noqa: BLE001, S110
            pass

        return None

    # If cache is provided, use it for faster lookup
    if cache is not None:
        cache_entries = cache.get_references(strref)
        if cache_entries:
            # Build a map of ResourceIdentifier -> FileResource by iterating installation
            identifier_to_resource: dict[ResourceIdentifier, FileResource] = {}
            for res in installation:
                try:
                    identifier_to_resource[res.identifier()] = res
                except Exception:  # noqa: BLE001, S110, S112
                    continue

            # Convert cache format to StrRefSearchResult format
            for identifier, location_strings in cache_entries:
                try:
                    found_resource: FileResource | None = identifier_to_resource.get(identifier)
                    if found_resource is None:
                        continue

                    # Convert location strings to proper location objects
                    locations: list[TwoDARefLocation | SSFRefLocation | GFFRefLocation | NCSRefLocation] = []

                    for loc_str in location_strings:
                        if loc_str.startswith("row_"):
                            parts = loc_str.replace("row_", "").split(".", 1)
                            if len(parts) == 2:
                                row_idx = int(parts[0])
                                column_name = parts[1]
                                locations.append(TwoDARefLocation(row_index=row_idx, column_name=column_name))
                        elif loc_str.startswith("sound_"):
                            sound_name = loc_str.replace("sound_", "")
                            try:
                                sound = SSFSound[sound_name]
                                locations.append(SSFRefLocation(sound=sound))
                            except KeyError:  # noqa: S110
                                pass
                        elif loc_str.startswith("offset_"):
                            byte_offset = int(loc_str.replace("offset_", ""))
                            locations.append(NCSRefLocation(byte_offset=byte_offset))
                        else:
                            locations.append(GFFRefLocation(field_path=loc_str))

                    if locations:
                        results.append(StrRefSearchResult(resource=found_resource, locations=locations))
                except Exception:  # noqa: BLE001, S110, S112
                    continue

            return results

    # Scan all resources in the installation (no cache available)
    for resource in installation:
        restype = resource.restype()

        # Skip RIM files - they're not used at runtime
        try:
            relative_path = resource.filepath().relative_to(installation.path())
            path_parts = relative_path.parts
            if path_parts and path_parts[0].lower() == "rims":
                continue
        except ValueError:
            # If path isn't relative to installation, check absolute path
            abs_path = resource.filepath()
            if "rims" in abs_path.parts:
                continue

        # Check 2DA files
        if restype is ResourceType.TwoDA:
            result = scan_2da(resource)
            if result:
                results.append(result)

        # Check SSF files
        elif restype is ResourceType.SSF:
            result = scan_ssf(resource)
            if result:
                results.append(result)

        # Check NCS files - FIXME: TEMPORARILY DISABLED (will revisit later)
        # elif restype is ResourceType.NCS:
        #     result = scan_ncs(resource)
        #     if result:
        #         results.append(result)

        # Try to check as GFF - ONLY if it has a GFF extension
        elif restype.extension in GFFContent.get_extensions():
            result = scan_gff(resource)
            if result:
                results.append(result)
        # Skip all other resource types (textures, audio, etc.)

    return results


def find_tlk_entry_references(
    installation: Installation,
    query_stringref: int,
    order: list[SearchLocation] | None = None,
    *,
    capsules: list[Capsule] | None = None,
    folders: list[Path] | None = None,
    logger: Callable[[str], None] | None = None,
) -> set[FileResource]:
    """Finds all gffs that utilize this stringref in their localizedstring.

    If no gffs could not be found the value will return None.

    Args:
    ----
        installation: The installation to search
        query_stringref: A number representing the locstring to find.
        order: The ordered list of locations to check.
        capsules: An extra list of capsules to search in.
        folders: An extra list of folders to search in.
        logger: A logger to use for logging. (Optional)

    Returns:
    -------
        A set of FileResources.
    """
    capsules = [] if capsules is None else capsules
    folders = [] if folders is None else folders
    if order is None:
        order = [
            SearchLocation.CUSTOM_FOLDERS,
            SearchLocation.OVERRIDE,
            SearchLocation.CUSTOM_MODULES,
            SearchLocation.CHITIN,
            SearchLocation.MODULES,
        ]

    found_resources: set[FileResource] = set()
    gff_extensions: set[str] = GFFContent.get_extensions()
    relevant_2da_filenames: dict[str, set[str]] = {}

    if installation.game().is_k1():  # TODO(th3w1zard1): TSL:
        relevant_2da_filenames = K1Columns2DA.StrRefs.as_dict()
    elif installation.game().is_k2():
        relevant_2da_filenames = K2Columns2DA.StrRefs.as_dict()

    installation_path = installation.path()

    def check_2da(resource2da: FileResource) -> bool:
        valid_2da: TwoDA | None = None
        with suppress(ValueError, OSError):
            valid_2da = read_2da(resource2da.data())
        if not valid_2da:
            print(f"'{resource2da._path_ident_obj}' cannot be loaded, probably corrupted.")  # noqa: SLF001
            return False
        filename_2da = resource2da.filename().lower()

        # Get relative path for logging
        try:
            relative_path = resource2da.filepath().relative_to(installation_path)
            path_str = relative_path.as_posix()
        except ValueError:
            path_str = str(resource2da.filepath())

        found_locations: list[tuple[str, int | None]] = []  # (column_name, row_index)

        for column_name in relevant_2da_filenames[filename_2da]:
            if column_name == ">>##HEADER##<<":
                for header in valid_2da.get_headers():
                    try:
                        stripped_header = header.strip()
                        if not stripped_header.isdigit():
                            if stripped_header and stripped_header not in ("****", "*****", "-1"):
                                RobustLogger().warning(f"header '{header}' in '{filename_2da}' is invalid, expected a stringref number.")
                            continue
                        if int(stripped_header) == query_stringref:
                            found_locations.append((">>##HEADER##<<", None))
                            if logger:
                                logger(f"    Found at: header '{header}' at {path_str}")
                    except Exception as e:  # noqa: BLE001
                        RobustLogger().error("Error parsing '%s' header '%s': %s", filename_2da, header, str(e), exc_info=False)
            else:
                try:
                    for i, cell in enumerate(valid_2da.get_column(column_name)):
                        stripped_cell = cell.strip()
                        if not stripped_cell.isdigit():
                            if stripped_cell and stripped_cell not in ("****", "*****", "-1"):
                                RobustLogger().warning(
                                    f"column '{column_name}' rowindex {i} in '{filename_2da}' is invalid, expected a stringref number. Instead got '{cell}'"
                                )
                            continue
                        if int(stripped_cell) == query_stringref:
                            found_locations.append((column_name, i))
                            if logger:
                                logger(f"    Found at: row {i}, column '{column_name}' at {path_str}")
                except Exception as e:  # noqa: BLE001
                    RobustLogger().error("Error parsing '%s' column '%s': %s", filename_2da, column_name, str(e), exc_info=False)

        return len(found_locations) > 0

    def check_ssf(resource_ssf: FileResource) -> bool:
        """Check if an SSF file contains the query StrRef."""
        valid_ssf: SSF | None = None
        with suppress(ValueError, OSError):
            valid_ssf = read_ssf(resource_ssf.data())
        if not valid_ssf:
            return False

        # Get relative path for logging
        try:
            relative_path = resource_ssf.filepath().relative_to(installation_path)
            path_str = relative_path.as_posix()
        except ValueError:
            path_str = str(resource_ssf.filepath())

        # Check all sound slots for this StrRef
        for sound in SSFSound:
            sound_strref = valid_ssf.get(sound)
            if sound_strref == query_stringref:
                if logger:
                    logger(f"    Found at: sound slot '{sound.name}' at {path_str}")
                return True
        return False

    def check_ncs(resource_ncs: FileResource) -> bool:
        """Check if an NCS (compiled script) file contains the query StrRef.

        StrRefs in scripts appear as CONSTI (constant integer) instructions.
        We extract all CONSTI values and check if any match the query.
        """
        valid_ncs: NCS | None = None
        with suppress(ValueError, OSError):
            valid_ncs = read_ncs(resource_ncs.data())
        if not valid_ncs:
            return False

        # Get relative path for logging
        try:
            relative_path = resource_ncs.filepath().relative_to(installation_path)
            path_str = relative_path.as_posix()
        except ValueError:
            path_str = str(resource_ncs.filepath())

        # Get byte offsets using the existing function
        offsets = get_ncs_consti_offsets(resource_ncs, query_stringref)

        # Log found offsets
        if offsets and logger:
            for offset in offsets:
                logger(f"    Found at: byte offset {offset:#X} (0x{offset:X}) at {path_str}")

        return len(offsets) > 0

    def check_gff(resource_gff: FileResource) -> bool:
        """Check if a GFF file contains the query StrRef."""
        valid_gff: GFF | None = None
        with suppress(ValueError, OSError):
            valid_gff = read_gff(resource_gff.data())
        if valid_gff is None:
            return False

        # Get relative path for logging
        try:
            relative_path = resource_gff.filepath().relative_to(installation_path)
            path_str = relative_path.as_posix()
        except ValueError:
            path_str = str(resource_gff.filepath())

        # Track found field paths for logging
        found_paths: list[str] = []

        def recurse_gff_structs_with_logging(gff_struct: GFFStruct, path_prefix: str = "") -> bool:
            """Recursively scan GFF struct and collect field paths."""
            for field_label, ftype, fval in gff_struct:
                field_path = f"{path_prefix}.{field_label}" if path_prefix else field_label

                if ftype == GFFFieldType.List and isinstance(fval, GFFList):
                    for idx, list_struct in enumerate(fval):
                        list_path = f"{field_path}[{idx}]"
                        if recurse_gff_structs_with_logging(list_struct, list_path):
                            found_paths.append(list_path)
                if ftype == GFFFieldType.Struct and isinstance(fval, GFFStruct) and recurse_gff_structs_with_logging(fval, field_path):
                    found_paths.append(field_path)
                if ftype != GFFFieldType.LocalizedString or not isinstance(fval, LocalizedString):
                    continue
                if fval.stringref == query_stringref:
                    found_paths.append(field_path)
                    return True
            return False

        result = recurse_gff_structs_with_logging(valid_gff.root)

        # Log all found field paths
        if result and logger:
            for field_path in found_paths:
                logger(f"    Found at: field path '{field_path}' at {path_str}")

        return result

    def get_ncs_consti_offsets(resource_ncs: FileResource, target_value: int) -> list[int]:
        """Get byte offsets of all CONSTI instructions with a specific value.

        Returns list of byte offsets where the 4-byte integer value starts
        (i.e., offset + 2 from instruction start).
        """
        offsets: list[int] = []
        try:
            # Re-read with offset tracking
            with BinaryReader.from_auto(resource_ncs.data()) as reader:
                # Skip NCS header (13 bytes)
                if reader.read_string(4) != "NCS ":
                    return offsets
                if reader.read_string(4) != "V1.0":
                    return offsets
                magic_byte = reader.read_uint8()
                if magic_byte != 0x42:  # noqa: PLR2004
                    return offsets
                total_size = reader.read_uint32(big=True)

                # Now read instructions and track offsets
                while reader.position() < total_size and reader.remaining() > 0:
                    opcode = reader.read_uint8()
                    qualifier = reader.read_uint8()

                    # Check if this is CONSTI (opcode=0x04, qualifier=0x03)
                    if opcode == 0x04 and qualifier == 0x03:  # CONSTI  # noqa: PLR2004
                        value_offset = reader.position()  # Current position is where the 4-byte value starts
                        const_value = reader.read_int32(big=True)
                        if const_value == target_value:
                            offsets.append(value_offset)
                    # Skip to next instruction based on opcode/qualifier
                    # This is simplified - just skip common patterns
                    elif opcode == 0x04:  # CONSTx  # noqa: PLR2004
                        if qualifier == 0x04:  # CONSTF  # noqa: PLR2004
                            reader.skip(4)
                        elif qualifier == 0x05:  # CONSTS  # noqa: PLR2004
                            str_len = reader.read_uint16(big=True)
                            reader.skip(str_len)
                        elif qualifier == 0x06:  # CONSTO  # noqa: PLR2004
                            reader.skip(4)
                    elif opcode in (0x01, 0x03, 0x26, 0x27):  # CPDOWNSP, CPTOPSP, CPDOWNBP, CPTOPBP
                        reader.skip(6)
                    elif opcode == 0x2C:  # STORE_STATE  # noqa: PLR2004
                        reader.skip(8)
                    elif opcode in (0x1B, 0x1D, 0x1E, 0x1F, 0x23, 0x24, 0x25, 0x28, 0x29):  # MOVSP, jumps, inc/dec
                        reader.skip(4)
                    elif opcode == 0x05:  # ACTION  # noqa: PLR2004
                        reader.skip(3)
                    elif opcode == 0x21:  # DESTRUCT  # noqa: PLR2004
                        reader.skip(6)
                    elif opcode == 0x0B and qualifier == 0x24:  # EQUALTT  # noqa: PLR2004
                        reader.skip(2)
                    elif opcode == 0x0C and qualifier == 0x24:  # NEQUALTT  # noqa: PLR2004
                        reader.skip(2)
                        # Other instructions have no additional data

        except Exception:  # noqa: BLE001, S110
            # If anything fails, return what we found so far
            pass

        return offsets

    def recurse_gff_lists(gff_list: GFFList) -> bool:
        for gff_struct in gff_list:
            result = recurse_gff_structs(gff_struct)
            if result:
                return True
        return False

    def recurse_gff_structs(gff_struct: GFFStruct) -> bool:
        for _label, ftype, fval in gff_struct:
            if ftype == GFFFieldType.List and isinstance(fval, GFFList):
                result = recurse_gff_lists(fval)
                if result:
                    return True
            if ftype == GFFFieldType.Struct and isinstance(fval, GFFStruct):
                result = recurse_gff_structs(fval)
                if result:
                    return True
            if ftype != GFFFieldType.LocalizedString or not isinstance(fval, LocalizedString):
                continue
            if fval.stringref == query_stringref:  # the matching strref was found
                return True
        return False

    def try_get_gff(gff_data: bytes) -> GFF | None:
        with suppress(OSError, ValueError):
            return read_gff(gff_data)
        return None

    def check_dict(resource_dict: dict[str, list[FileResource]]):
        for resources in resource_dict.values():
            check_list(resources)

    def check_list(resource_list: list[FileResource]):
        for resource in resource_list:
            this_restype: ResourceType = resource.restype()

            # Check 2DA files
            if resource.filename().lower() in relevant_2da_filenames and this_restype is ResourceType.TwoDA and check_2da(resource):
                found_resources.add(resource)
                continue

            # Check SSF files
            if this_restype is ResourceType.SSF and check_ssf(resource):
                found_resources.add(resource)
                continue

            # Check NCS files - FIXME: TEMPORARILY DISABLED (will revisit later)
            # if this_restype is ResourceType.NCS and check_ncs(resource):
            #     found_resources.add(resource)
            #     continue

            # Check GFF files
            if this_restype.extension not in gff_extensions:
                continue
            valid_gff: GFF | None = try_get_gff(resource.data())
            if valid_gff is None:
                continue
            if not recurse_gff_structs(valid_gff.root):
                continue
            found_resources.add(resource)

    def check_capsules(capsules_list: list[Capsule]):
        for capsule in capsules_list:
            for resource in capsule.resources():
                this_restype: ResourceType = resource.restype()

                # Check 2DA files
                if resource.filename().lower() in relevant_2da_filenames and this_restype is ResourceType.TwoDA and check_2da(resource):
                    found_resources.add(resource)
                    continue

                # Check SSF files
                if this_restype is ResourceType.SSF and check_ssf(resource):
                    found_resources.add(resource)
                    continue

                # Check NCS files - FIXME: TEMPORARILY DISABLED (will revisit later)
                # if this_restype is ResourceType.NCS and check_ncs(resource):
                #     found_resources.add(resource)
                #     continue

                # Check GFF files
                if this_restype.extension not in gff_extensions:
                    continue
                valid_gff: GFF | None = try_get_gff(resource.data())
                if valid_gff is None:
                    continue
                if not recurse_gff_structs(valid_gff.root):
                    continue
                found_resources.add(resource)

    def check_folders(values: list[Path]):
        relevant_files: set[Path] = set()
        for folder in values:  # Having two loops makes it easier to filter out irrelevant files when stepping through the 2nd
            relevant_files.update(
                file
                for file in folder.rglob("*")
                if (
                    file.suffix
                    and (
                        file.suffix[1:].casefold() in gff_extensions
                        or (file.name.lower() in relevant_2da_filenames and file.suffix.casefold() == ".2da")
                        or file.suffix.casefold() == ".ssf"
                        or file.suffix.casefold() == ".ncs"
                    )
                    and file.is_file()
                )
            )
        for gff_file in relevant_files:
            restype: ResourceType | None = ResourceType.from_extension(gff_file.suffix)
            if not restype:
                continue
            fileres = FileResource(resname=gff_file.stem, restype=restype, size=gff_file.stat().st_size, offset=0, filepath=gff_file)

            # Check 2DA files
            if restype is ResourceType.TwoDA and check_2da(fileres):
                found_resources.add(fileres)
                continue

            # Check SSF files
            if restype is ResourceType.SSF and check_ssf(fileres):
                found_resources.add(fileres)
                continue

            # Check NCS files - FIXME: TEMPORARILY DISABLED (will revisit later)
            # if restype is ResourceType.NCS and check_ncs(fileres):
            #     found_resources.add(fileres)
            #     continue

            # Check GFF files
            gff_data = BinaryReader.load_file(gff_file)
            valid_gff: GFF | None = None
            with suppress(ValueError, OSError):
                valid_gff = read_gff(gff_data)
            if not valid_gff:
                continue
            if not recurse_gff_structs(valid_gff.root):
                continue
            found_resources.add(fileres)

    # Access Installation internal properties (they're properties so they'll work)
    function_map: dict[SearchLocation, Callable] = {
        SearchLocation.OVERRIDE: lambda: check_dict(installation._override),  # noqa: SLF001
        SearchLocation.MODULES: lambda: check_dict(installation._modules),  # noqa: SLF001
        SearchLocation.RIMS: lambda: check_dict(installation._rims),  # noqa: SLF001
        SearchLocation.CHITIN: lambda: check_list(installation._chitin) or check_list(installation._patch_erf),  # noqa: SLF001
        SearchLocation.CUSTOM_MODULES: lambda: check_capsules(capsules),
        SearchLocation.CUSTOM_FOLDERS: lambda: check_folders(folders),  # type: ignore[arg-type]
    }

    for item in order:
        assert isinstance(item, SearchLocation), f"{type(item).__name__}: {item}"
        function_map.get(item, lambda: None)()

    return found_resources
