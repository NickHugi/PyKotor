from __future__ import annotations

import os
import traceback

from dataclasses import dataclass
from typing import TYPE_CHECKING, NamedTuple, Sequence, Union

from pykotor.common.language import Language
from pykotor.common.misc import ResRef
from pykotor.common.stream import BinaryReader
from utility.system.path import Path

if TYPE_CHECKING:
    from typing import Callable

    from pykotor.common.language import LocalizedString
    from pykotor.common.misc import Game
    from pykotor.extract.file import FileResource, ResourceIdentifier
    from pykotor.extract.installation import Installation

# Import for runtime usage (needed by StrRefReferenceCache)
from pykotor.resource.formats.gff.gff_auto import read_gff
from pykotor.resource.formats.gff.gff_data import GFFContent, GFFFieldType, GFFList, GFFStruct
from pykotor.resource.formats.ssf.ssf_auto import read_ssf
from pykotor.resource.formats.ssf.ssf_data import SSFSound
from pykotor.resource.formats.twoda.twoda_auto import read_2da
from pykotor.resource.type import ResourceType
from utility.system.path import PurePath


# Late import to avoid circular dependency
def _get_2da_columns():
    from pykotor.extract.twoda import K1Columns2DA, K2Columns2DA

    return K1Columns2DA, K2Columns2DA


class StringResult(NamedTuple):
    text: str
    sound: ResRef


class TLKData(NamedTuple):
    flags: int
    voiceover: str
    volume_variance: int
    pitch_variance: int
    text_offset: int
    text_length: int
    sound_length: float


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


class TalkTable:  # TODO(th3w1zard1): dialogf.tlk
    """Talktables are for read-only loading of stringrefs stored in a dialog.tlk file.

    Files are only opened when accessing a stored string, this means that strings are always up to date at
    the time of access as opposed to TLK objects which may be out of date with its source file.
    """

    def __init__(
        self,
        path: os.PathLike | str,
    ):
        self._path: Path = Path.pathify(path)

    def path(self) -> Path:
        return self._path

    def string(
        self,
        stringref: int,
    ) -> str:
        """Access a string from the tlk file.

        Args:
        ----
            stringref: The entry id.

        Returns:
        -------
            A string.
        """
        if stringref == -1:
            return ""
        with BinaryReader.from_file(self._path) as reader:
            reader.seek(12)
            entries_count: int = reader.read_uint32()
            texts_offset: int = reader.read_uint32()

            if stringref >= entries_count:
                return ""

            tlkdata: TLKData = self._extract_common_tlk_data(reader, stringref)
            reader.seek(texts_offset + tlkdata.text_offset)
            return reader.read_string(tlkdata.text_length)

    def sound(
        self,
        stringref: int,
    ) -> ResRef:
        """Access the sound ResRef from the tlk file.

        Args:
        ----
            stringref: The entry id.

        Returns:
        -------
            A ResRef.
        """
        if stringref == -1:
            return ResRef.from_blank()
        with BinaryReader.from_file(self._path) as reader:
            reader.seek(12)
            entries_count = reader.read_uint32()
            reader.skip(4)

            if stringref >= entries_count:
                return ResRef.from_blank()

            tlkdata = self._extract_common_tlk_data(reader, stringref)
            return ResRef(tlkdata.voiceover)

    def _extract_common_tlk_data(
        self,
        reader: BinaryReader,
        stringref: int,
    ) -> TLKData:
        reader.seek(20 + 40 * stringref)

        return TLKData(
            flags=reader.read_uint32(),
            voiceover=reader.read_string(16),
            volume_variance=reader.read_uint32(),
            pitch_variance=reader.read_uint32(),
            text_offset=reader.read_uint32(),
            text_length=reader.read_uint32(),
            sound_length=reader.read_single(),
        )

    def batch(
        self,
        stringrefs: list[int],
    ) -> dict[int, StringResult]:
        """Loads a list of strings and sound ResRefs from the specified list.

        This is all performed using a single file handle and should be used if loading multiple strings from the tlk file.

        Args:
        ----
            stringrefs: A list of stringref ints.

        Returns:
        -------
            Dictionary with stringref keys and Tuples (string, sound) values.
        """
        with BinaryReader.from_file(self._path) as reader:
            reader.seek(8)
            language_id = reader.read_uint32()
            language: Language = Language(language_id)
            encoding: str | None = language.get_encoding()
            entries_count = reader.read_uint32()
            texts_offset = reader.read_uint32()

            batch: dict[int, StringResult] = {}

            for stringref in stringrefs:
                if stringref == -1 or stringref >= entries_count:
                    batch[stringref] = StringResult("", ResRef.from_blank())
                    continue

                tlkdata: TLKData = self._extract_common_tlk_data(reader, stringref)

                reader.seek(texts_offset + tlkdata.text_offset)
                string = reader.read_string(tlkdata.text_length, encoding=encoding)
                sound = ResRef(tlkdata.voiceover)

                batch[stringref] = StringResult(string, sound)

            return batch

    def size(
        self,
    ) -> int:
        """Returns the number of entries in the talk table.

        Returns:
        -------
            The number of entries in the talk table.
        """
        with BinaryReader.from_file(self._path) as reader:
            reader.seek(12)
            return reader.read_uint32()  # entries_count

    def language(
        self,
    ) -> Language:
        """Returns the matching Language of the TLK file.

        Returns:
        -------
            The language of the TLK file.
        """
        with BinaryReader.from_file(self._path) as reader:
            reader.seek(8)
            language_id = reader.read_uint32()
            return Language(language_id)


# Logging helpers for StrRefReferenceCache
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

        # Map: strref -> [(resource_identifier, [field_paths])]
        self._cache: dict[int, list[tuple[ResourceIdentifier, list[str]]]] = {}

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
            self._strref_2da_columns: dict[str, set[str]] = {}

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

            # NCS files
            elif restype is ResourceType.NCS:
                self._scan_ncs(identifier, data)

            # GFF files (try to parse as GFF)
            else:
                try:
                    gff_obj = read_gff(data)
                    self._scan_gff(identifier, gff_obj.root)
                except Exception:  # noqa: BLE001, S110
                    # Not a GFF file or failed to parse, skip
                    pass

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
        """Scan NCS file for StrRef references in CONSTI instructions."""
        # We don't know which StrRefs we're looking for yet, so we need to scan for all ints
        # This is expensive, so we'll defer NCS scanning to when we actually have TLK mods
        # For now, just mark that this is an NCS file

    def _scan_gff(
        self,
        identifier: ResourceIdentifier,
        gff_struct: GFFStruct,
        current_path: PurePath | None = None,
    ) -> None:
        """Recursively scan GFF structure for LocalizedString fields with StrRefs."""
        if current_path is None:
            current_path = PurePath()

        for label, field_type, value in gff_struct:
            field_path: PurePath = current_path / label

            # LocalizedString fields
            is_locstring: bool = field_type == GFFFieldType.LocalizedString
            if is_locstring:
                locstring: LocalizedString = value  # type: ignore[assignment]
                if locstring.stringref != -1:
                    filename: str = f"{identifier.resname}.{identifier.restype.extension}"
                    _log_debug(f"Found StrRef {locstring.stringref} in GFF file '{filename}' at field path '{field_path}'")
                    self._add_reference(locstring.stringref, identifier, str(field_path))

            # Nested structs
            is_struct: bool = field_type == GFFFieldType.Struct
            if is_struct and isinstance(value, GFFStruct):
                self._scan_gff(identifier, value, field_path)

            # Lists
            is_list: bool = field_type == GFFFieldType.List
            if is_list and isinstance(value, GFFList):
                for idx, item in enumerate(value):
                    if isinstance(item, GFFStruct):
                        self._scan_gff(identifier, item, field_path / str(idx))

    def _add_reference(
        self,
        strref: int,
        identifier: ResourceIdentifier,
        location: str,
    ) -> None:
        """Add a StrRef reference to the cache."""
        filename: str = f"{identifier.resname}.{identifier.restype.extension}"

        # Track statistics
        self._total_references_found += 1
        self._files_with_strrefs.add(filename)

        is_new_strref: bool = strref not in self._cache
        if is_new_strref:
            self._cache[strref] = []
            _log_verbose(f"  → Cached new StrRef {strref} from '{filename}' at '{location}'")

        # Check if we already have this identifier
        for existing_id, existing_locations in self._cache[strref]:
            if existing_id == identifier:
                existing_locations.append(location)
                return

        # New identifier for this StrRef
        self._cache[strref].append((identifier, [location]))

    def get_references(self, strref: int) -> list[tuple[ResourceIdentifier, list[str]]]:
        """Get all resources that reference a specific StrRef.

        Args:
            strref: StrRef to look up

        Returns:
            List of (resource_identifier, [field_paths]) tuples
        """
        return self._cache.get(strref, [])

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

        for strref, references in self._cache.items():
            serialized[str(strref)] = [
                {
                    "resname": identifier.resname,
                    "restype": identifier.restype.extension,
                    "locations": locations,
                }
                for identifier, locations in references
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
            cache._cache[strref] = []

            for ref_data in references:
                resname: str = str(ref_data["resname"])
                restype_ext: str = str(ref_data["restype"])
                locations: list[str] = list(ref_data["locations"])  # type: ignore[arg-type]

                # Recreate ResourceIdentifier
                restype: ResourceType = ResourceType.from_extension(restype_ext)
                identifier = ResourceIdentifier(resname, restype)

                cache._cache[strref].append((identifier, locations))

                # Update statistics
                cache._total_references_found += len(locations)
                filename: str = f"{resname}.{restype_ext}"
                cache._files_with_strrefs.add(filename)

        _log_verbose(f"Restored StrRef cache from saved data: {len(cache._cache)} StrRefs, {cache._total_references_found} references")

        return cache


def find_strref_references(
    installation: Installation,
    strref: int,
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
    from pykotor.common.language import LocalizedString  # noqa: PLC0415

    K1Columns2DA, K2Columns2DA = _get_2da_columns()
    game = installation.game()

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
                            logger(f"    Found at: row {row_idx}, column '{column_name}' at {path_str}")

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
                        logger(f"    Found at: sound slot '{sound.name}' at {path_str}")

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
                for location in locations:
                    logger(f"    Found at: field path '{location.field_path}' at {path_str}")

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

                while reader.position() < total_size and reader.remaining() > 0:
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
                    for location in locations:
                        logger(f"    Found at: byte offset {location.byte_offset:#X} (0x{location.byte_offset:X}) at {path_str}")

                return StrRefSearchResult(resource=resource, locations=locations)

        except Exception:  # noqa: BLE001, S110
            pass

        return None

    # Scan all resources in the installation
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

        # Check NCS files
        elif restype is ResourceType.NCS:
            result = scan_ncs(resource)
            if result:
                results.append(result)

        # Try to check as GFF - ONLY if it has a GFF extension
        elif restype.extension in GFFContent.get_extensions():
            result = scan_gff(resource)
            if result:
                results.append(result)
        # Skip all other resource types (textures, audio, etc.)

    return results
