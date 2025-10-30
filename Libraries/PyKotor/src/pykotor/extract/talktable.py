from __future__ import annotations

import os

from typing import TYPE_CHECKING, NamedTuple

from pykotor.common.language import Language
from pykotor.common.misc import ResRef
from pykotor.common.stream import BinaryReader
from utility.system.path import Path

if TYPE_CHECKING:
    from pykotor.common.language import LocalizedString
    from pykotor.common.misc import Game
    from pykotor.extract.file import FileResource, ResourceIdentifier

# Import for runtime usage (needed by StrRefReferenceCache)
from pykotor.resource.formats.gff.gff_auto import read_gff
from pykotor.resource.formats.gff.gff_data import GFFFieldType, GFFList, GFFStruct
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
