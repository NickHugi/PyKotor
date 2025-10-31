#!/usr/bin/env python3
"""Incremental TSLPatcher data writer.

Writes tslpatchdata files and INI sections as diffs are discovered,
rather than batching everything at the end.
"""

from __future__ import annotations

import os
import traceback

from dataclasses import dataclass
from datetime import datetime, timezone  # noqa: PLC0415
from typing import TYPE_CHECKING, Any, Callable, Iterable

from pykotor.common.language import LocalizedString
from pykotor.extract.capsule import Capsule
from pykotor.extract.installation import Installation
from pykotor.extract.twoda import GFF_FIELD_TO_2DA_MAPPING
from pykotor.resource.formats.gff import GFFContent, GFFFieldType, read_gff
from pykotor.resource.formats.gff.gff_auto import detect_gff, write_gff
from pykotor.resource.formats.gff.gff_data import GFFList, GFFStruct
from pykotor.resource.formats.lip.lip_auto import read_lip, write_lip
from pykotor.resource.formats.ssf import SSFSound, read_ssf
from pykotor.resource.formats.ssf.ssf_auto import write_ssf
from pykotor.resource.formats.tlk.tlk_auto import read_tlk, write_tlk
from pykotor.resource.formats.tlk.tlk_data import TLK  # noqa: PLC0415
from pykotor.resource.formats.twoda import read_2da
from pykotor.resource.formats.twoda.twoda_auto import write_2da
from pykotor.resource.type import ResourceType
from pykotor.tslpatcher.diff.resolution import TLKModificationWithSource  # noqa: PLC0415
from pykotor.tslpatcher.memory import TokenUsageTLK
from pykotor.tslpatcher.mods.gff import (  # noqa: PLC0415
    FieldValue2DAMemory,
    FieldValueConstant,
    FieldValueTLKMemory,
    LocalizedStringDelta,
    ModificationsGFF,
    ModifyFieldGFF,
)
from pykotor.tslpatcher.mods.ncs import ModificationsNCS, ModifyNCS, NCSTokenType  # noqa: PLC0415
from pykotor.tslpatcher.mods.ssf import ModificationsSSF, ModifySSF
from pykotor.tslpatcher.mods.tlk import ModificationsTLK  # noqa: PLC0415
from pykotor.tslpatcher.mods.twoda import ChangeRow2DA, Modifications2DA, RowValue2DAMemory, RowValueTLKMemory, Target, TargetType  # noqa: PLC0415
from pykotor.tslpatcher.writer import ModificationsByType, TSLPatcherINISerializer
from utility.common.more_collections import CaseInsensitiveDict
from utility.system.path import Path, PurePath

if TYPE_CHECKING:
    from pykotor.common.geometry import Vector3, Vector4
    from pykotor.common.misc import ResRef
    from pykotor.extract.file import FileResource
    from pykotor.extract.talktable import StrRefReferenceCache, StrRefSearchResult
    from pykotor.extract.twoda import TwoDAMemoryReferenceCache
    from pykotor.tslpatcher.mods.template import PatcherModifications
    from pykotor.tslpatcher.mods.tlk import ModifyTLK


# Logging helpers
# Log level: 0 = normal, 1 = verbose, 2 = debug
_log_level = 2 if os.environ.get("KOTORDIFF_DEBUG") else (1 if os.environ.get("KOTORDIFF_VERBOSE") else 0)


def _log_debug(msg: str) -> None:
    """Log debug message if debug level is enabled."""
    if _log_level >= 2:
        print(f"[DEBUG] {msg}")


def _log_verbose(msg: str) -> None:
    """Log verbose message if verbose level is enabled."""
    if _log_level >= 1:
        print(f"[VERBOSE] {msg}")


@dataclass
class TwoDALinkTarget:
    row_index: int
    token_id: int
    row_label: str | None = None


@dataclass
class PendingStrRefReference:
    """Temporarily stored StrRef reference that will be applied when the file is diffed.

    Attributes:
        filename: The resource filename (e.g., "p_vima_ssf.ssf")
        source_path: The installation or path where this StrRef was found
        old_strref: The original StrRef value
        token_id: The TLKMEMORY token ID to use
        location_type: Type of location (2da, ssf, gff, ncs)
        location_data: Location-specific data (row_index/column_name for 2DA, sound for SSF, field_path for GFF, byte_offset for NCS)
    """

    filename: str
    source_path: Installation | Path
    old_strref: int
    token_id: int
    location_type: str  # "2da", "ssf", "gff", "ncs"
    location_data: dict[str, Any]


class IncrementalTSLPatchDataWriter:
    """Writes tslpatchdata files and INI sections incrementally during diff."""

    def __init__(
        self,
        tslpatchdata_path: Path,
        ini_filename: str,
        base_data_path: Path | None = None,
        strref_cache: StrRefReferenceCache | None = None,
        twoda_caches: dict[int, CaseInsensitiveDict[TwoDAMemoryReferenceCache]] | None = None,
        log_func: Callable[[str], None] | None = None,
    ):
        """Initialize incremental writer.

        Args:
            tslpatchdata_path: Path to tslpatchdata folder
            ini_filename: Name of INI file to generate
            base_data_path: Optional base path for reading original files
            strref_cache: Optional StrRef reference cache for TLK linking
                (built from installation that has StrRefs that others don't)
            twoda_caches: Optional nested dict of 2DA caches
                Structure: {installation_index: CaseInsensitiveDict[TwoDAMemoryReferenceCache]}
                Keys are case-insensitive 2DA filenames (e.g., "appearance.2da", "APPEARANCE.2DA")
                Each cache should be built from the installation that has entries
                for that specific 2DA filename that others don't.
            log_func: Optional logging function

        Note: For n-way diffs, caches should be built from whichever installation has
        entries (2DA rows, StrRef entries, GFF fields, SSF entries, etc.) that others don't.
        There should be a separate cache for each unique (installation_index, 2da_filename) pair.
        """
        self.tslpatchdata_path: Path = tslpatchdata_path
        self.ini_path: Path = tslpatchdata_path / ini_filename
        self.base_data_path: Path | None = base_data_path
        self.strref_cache: StrRefReferenceCache | None = strref_cache
        # Convert regular dicts to CaseInsensitiveDict if needed
        self.twoda_caches: dict[int, CaseInsensitiveDict[TwoDAMemoryReferenceCache]] = {}
        if twoda_caches:
            for install_idx, filename_to_cache in twoda_caches.items():
                if isinstance(filename_to_cache, CaseInsensitiveDict):
                    self.twoda_caches[install_idx] = filename_to_cache
                else:
                    # Convert regular dict to CaseInsensitiveDict
                    self.twoda_caches[install_idx] = CaseInsensitiveDict(filename_to_cache)
        self.log_func: Callable[[str], None] = log_func or print

        # Metadata storage for TLK modifications (strref_mappings, source installations)
        # Key: id(ModificationsTLK object), Value: dict with strref_mappings and source_installations
        self._tlk_metadata: dict[int, dict[str, Any]] = {}

        # Create tslpatchdata directory
        self.tslpatchdata_path.mkdir(parents=True, exist_ok=True)

        # Track what we've written
        self.written_sections: set[str] = set()
        self.install_folders: dict[str, list[str]] = {}

        # Track modifications for final InstallList generation
        self.all_modifications: ModificationsByType = self._create_empty_modifications()

        # Track insertion positions for each section (for real-time appending)
        self.section_markers: dict[str, str] = {
            "tlk": "[TLKList]",
            "install": "[InstallList]",
            "2da": "[2DAList]",
            "gff": "[GFFList]",
            "ncs": "[CompileList]",
            "ssf": "[SSFList]",
        }

        # Track folder numbers for InstallList
        self.folder_numbers: dict[str, int] = {}
        self.next_folder_number: int = 0

        # Initialize INI file with all headers
        self._initialize_ini()

        _log_debug(f"Incremental writer initialized at: {self.tslpatchdata_path}")

        # Track global 2DAMEMORY token allocation
        self._next_2da_token_id: int = 0

        # Track TLK modifications with their source paths for intelligent cache building
        # Key: source_index (0=first/vanilla, 1=second/modded, 2=third, etc.)
        # Value: list of TLKModificationWithSource objects from that source
        self.tlk_mods_by_source: dict[int, list[TLKModificationWithSource]] = {}

        # Track pending StrRef references that will be applied when files are diffed
        # Key: filename (lowercase) -> list of PendingStrRefReference
        self._pending_strref_references: dict[str, list[PendingStrRefReference]] = {}

    def register_tlk_modification_with_source(
        self,
        tlk_mod: ModificationsTLK,
        source_path: Path | Installation,  # Installation or Path
        source_index: int,
    ) -> None:
        """Register a TLK modification with its source path for cache building.

        Args:
            tlk_mod: The TLK modification object
            source_path: The installation or folder path this TLK came from
            source_index: Index of the source (0=first/vanilla, 1=second/modded, etc.)
        """
        is_installation: bool = isinstance(source_path, Installation)

        wrapped = TLKModificationWithSource(
            modification=tlk_mod,
            source_path=source_path,
            source_index=source_index,
            is_installation=is_installation,
        )

        if source_index not in self.tlk_mods_by_source:
            self.tlk_mods_by_source[source_index] = []

        self.tlk_mods_by_source[source_index].append(wrapped)
        _log_debug(f"Registered TLK mod from source {source_index}: {tlk_mod.sourcefile} ({len(getattr(tlk_mod, 'strref_mappings', {}))} StrRefs)")

    @staticmethod
    def _create_empty_modifications() -> ModificationsByType:
        """Create empty modifications collection."""
        from pykotor.tslpatcher.writer import ModificationsByType  # noqa: PLC0415

        return ModificationsByType.create_empty()

    def _initialize_ini(self) -> None:
        """Initialize INI file with header, [Settings], and all List section headers."""
        header_lines = self._generate_custom_header()
        settings_lines = self._generate_settings()

        # Write all section headers in TSLPatcher-compliant order
        section_headers = [
            "",
            "[TLKList]",
            "",
            "",
            "[InstallList]",
            "",
            "",
            "[2DAList]",
            "",
            "",
            "[GFFList]",
            "",
            "",
            "[CompileList]",
            "",
            "",
            "[SSFList]",
            "",
        ]

        content = "\n".join([*header_lines, "", *settings_lines, *section_headers])
        self.ini_path.write_text(content, encoding="utf-8")
        _log_debug(f"Initialized INI with all section headers at: {self.ini_path}")

    def _generate_custom_header(self) -> list[str]:
        """Generate custom INI file header with PyKotor branding."""
        today = datetime.now(tz=timezone.utc).strftime("%m/%d/%Y")
        return [
            "; ============================================================================",
            f";  TSLPatcher Modifications File — Generated by HoloPatcher ({today})",
            "; ============================================================================",
            ";",
            ";  Crafted by: th3w1zard1 (Boden Crouch) with love for the KOTOR community",
            ";",
            ";  This file is part of the PyKotor ecosystem — an exhaustive modding for",
            ";  Knights of the Old Republic development, built to be cross-platform,",
            ";  reproducible, and future-proof.",
            ";",
            ";  Core Ecosystem Components:",
            ";    • PyKotor: Python library for reading/writing KOTOR formats",
            ";    • HoloPatcher: Cross-platform TSLPatcher alternative",
            ";    • HolocronToolset: Complete modding suite for KotOR I & II",
            ";    • KotorDiff: Advanced diff engine for patch generation",
            ";        https://github.com/th3w1zard1/PyKotor",
            ";    • KOTORModSync: Multi-mod installer with conflict resolution",
            ";        https://github.com/th3w1zard1/KOTORModSync",
            ";    • HoloLSP: The first ever Language Server Protocol for KotOR",
            ";        https://github.com/th3w1zard1/HoloLSP",
            ";    • HoloPatcher.NET: .NET implementation of HoloPatcher",
            ";        https://github.com/th3w1zard1/HoloPatcher.NET",
            ";",
            ";  https://www.bolabaden.org  - Self-Hosted Infrastructure and Initiatives",
            ";",
            ";  Developer Initiatives — bolabaden Organization:",
            ";    • bolabaden-site: Main website + frontend",
            ";        https://github.com/bolabaden/bolabaden-site",
            ";    • bolabaden-infra: Kubernetes backbone for bolabaden.org",
            ";        https://github.com/bolabaden/bolabaden-infra",
            ";    • ai-researchwizard: AI-powered research assistant",
            ";        https://github.com/bolabaden/ai-researchwizard",
            ";",
            "; ----------------------------------------------------------------------------",
            ";",
            ";  FORMATTING NOTES:",
            ";    • This file is TSLPatcher-compliant and machine-generated.",
            ";    • You may add blank lines between sections (for readability).",
            ";    • You may add comment lines starting with semicolon.",
            ";    • Do NOT add blank lines or comments inside a section (between keys).",
            "; ============================================================================",
            "",
        ]

    def _generate_settings(self) -> list[str]:
        """Generate default [Settings] section with all required TSLPatcher keys."""
        return [
            "[Settings]",
            "FileExists=1",
            "WindowCaption=Mod Installer",
            "ConfirmMessage=Install this mod?",
            "LogLevel=3",
            "InstallerMode=1",
            "BackupFiles=1",
            "PlaintextLog=0",
            "LookupGameFolder=0",
            "LookupGameNumber=1",
            "SaveProcessedScripts=0",
            "",
        ]

    def write_modification(
        self,
        modification: PatcherModifications,
        source_data: bytes | None = None,
        source_path: Installation | Path | None = None,
    ) -> None:
        """Write a modification's resource file and INI section immediately.

        Args:
            modification: The modification object to write
            source_data: Optional source data (vanilla version for patching)
            source_path: Optional source installation or path where this file comes from
        """
        # Check for and apply pending StrRef references before writing
        filename_lower = modification.sourcefile.lower()
        self._apply_pending_strref_references(filename_lower, modification, source_data, source_path)

        # Determine modification type and dispatch
        if isinstance(modification, Modifications2DA):
            self._write_2da_modification(modification, source_data)
        elif isinstance(modification, ModificationsGFF):
            self._write_gff_modification(modification, source_data)
        elif isinstance(modification, ModificationsTLK):
            self._write_tlk_modification(modification)
        elif isinstance(modification, ModificationsSSF):
            self._write_ssf_modification(modification, source_data)
        elif isinstance(modification, ModificationsNCS):
            self._write_ncs_modification(modification, source_data)
        else:
            _log_debug(f"Unknown modification type: {type(modification).__name__}")

    def _write_2da_modification(
        self,
        mod_2da: Modifications2DA,
        source_data: bytes | None,
    ) -> None:
        """Write 2DA resource file and INI section."""
        filename: str = mod_2da.sourcefile

        # Skip if already written
        if filename in self.written_sections:
            _log_debug(f"Skipping already written 2DA: {filename}")
            return

        change_row_targets, add_row_targets = self._prepare_twoda_tokens(mod_2da)

        # Write resource file (base vanilla 2DA that will be patched)
        if source_data:
            output_path: Path = self.tslpatchdata_path / filename
            try:
                twoda_obj = read_2da(source_data)
                write_2da(twoda_obj, output_path, ResourceType.TwoDA)
                _log_verbose(f"Wrote 2DA file: {filename}")
            except Exception as e:  # noqa: BLE001
                self.log_func(f"[Error] Failed to write 2DA {filename}: {e.__class__.__name__}: {e}")
                self.log_func("Full traceback:")
                for line in traceback.format_exc().splitlines():
                    self.log_func(f"  {line}")
                return

        # Add to install folders
        self._add_to_install_folder("Override", filename)

        # Write INI section
        self._write_to_ini([mod_2da], "2da")
        self.written_sections.add(filename)

        # Track in all_modifications
        self.all_modifications.twoda.append(mod_2da)

        # Create linking patches for modified rows - ONE AT A TIME, REAL-TIME
        # Get the source path/installation for this 2DA
        source_path: Installation | Path | None = None
        if hasattr(mod_2da, "source_path"):
            source_path = Path(mod_2da.sourcefile)
        elif self.base_data_path:
            source_path = Path(self.base_data_path, mod_2da.sourcefile)

        # Process each row modification ONE AT A TIME
        if change_row_targets and source_path:
            for target in change_row_targets:
                self.log_func(f"\n=== Finding References for 2DA Row: {filename} row {target.row_index} -> Token {target.token_id} ===")
                self._find_and_patch_single_2da_row(source_path, filename, target.row_index, target.token_id)

        # Process each new row ONE AT A TIME
        if add_row_targets and source_path:
            for target in add_row_targets:
                self.log_func(f"\n=== Finding References for New 2DA Row: {filename} label '{target.row_label}' -> Token {target.token_id} ===")
                # For new rows, we need the row_label since index is unknown
                if target.row_label:
                    self._find_and_patch_single_2da_row_by_label(source_path, filename, target.row_label, target.token_id)

    def _prepare_twoda_tokens(self, mod_2da: Modifications2DA) -> tuple[list[TwoDALinkTarget], list[TwoDALinkTarget]]:
        """Prepare 2DAMEMORY tokens for 2DA row modifications.

        Handles both ChangeRow2DA and AddRow2DA:
        - ChangeRow2DA: Modifies existing rows, creates linking patches for vanilla references
        - AddRow2DA: Adds new rows, creates linking patches for modded references

        Returns:
            (change_row_targets, add_row_targets) - Two lists of link targets for different caches
        """
        from pykotor.tslpatcher.mods.twoda import AddRow2DA, ChangeRow2DA, RowValueRowIndex, TargetType

        change_row_targets: list[TwoDALinkTarget] = []
        add_row_targets: list[TwoDALinkTarget] = []

        for modifier in mod_2da.modifiers:
            # Handle ChangeRow2DA - existing rows being modified
            if isinstance(modifier, ChangeRow2DA):
                # Reserve any existing tokens in store_2da
                if modifier.store_2da:
                    self._reserve_existing_twoda_tokens(modifier.store_2da.keys())

                # Extract row index - only handle ROW_INDEX targets
                if modifier.target.target_type != TargetType.ROW_INDEX:
                    continue
                if not isinstance(modifier.target.value, int):
                    continue

                row_index: int = modifier.target.value

                # If no store_2da, allocate a token and store RowIndex
                if not modifier.store_2da:
                    token_id: int = self._allocate_2da_token()
                    modifier.store_2da = {token_id: RowValueRowIndex()}
                    change_row_targets.append(TwoDALinkTarget(row_index=row_index, token_id=token_id, row_label=None))
                    continue

                # Process existing store_2da tokens
                for token_id, row_value in list(modifier.store_2da.items()):
                    if isinstance(row_value, RowValueRowIndex):
                        # Token stores the row index - use this for linking
                        change_row_targets.append(TwoDALinkTarget(row_index=row_index, token_id=token_id, row_label=None))

            # Handle AddRow2DA - new rows being added
            elif isinstance(modifier, AddRow2DA):
                # Reserve any existing tokens in store_2da
                if not modifier.store_2da:
                    continue

                self._reserve_existing_twoda_tokens(modifier.store_2da.keys())

                # For AddRow2DA, we can't know the final row index until patch time
                # But we CAN create linking patches for the modded installation
                # The row_label is our best identifier for the "new" row
                for token_id, row_value in list(modifier.store_2da.items()):
                    if not isinstance(row_value, RowValueRowIndex):
                        continue
                    # Use row_label as the identifier (since index is unknown)
                    # We'll need to find references by matching the row_label in the modded 2DA
                    add_row_targets.append(
                        TwoDALinkTarget(
                            row_index=-1,  # Unknown until patch time
                            token_id=token_id,
                            row_label=modifier.row_label,
                        )
                    )

        return change_row_targets, add_row_targets

    def _reserve_existing_twoda_tokens(self, token_ids: Iterable[int]) -> None:
        for token_id in token_ids:
            if token_id >= self._next_2da_token_id:
                self._next_2da_token_id = token_id + 1

    def _allocate_2da_token(self) -> int:
        """Allocate a new 2DAMEMORY token ID."""
        token_id: int = self._next_2da_token_id
        self._next_2da_token_id += 1
        return token_id

    # REMOVED: Old cache-based 2DA linking method
    # Now using real-time per-diff linking via _find_and_patch_single_2da_row

    # REMOVED: Old cache-based new row linking method
    # Now using real-time per-diff linking via _find_and_patch_single_2da_row_by_label

    @staticmethod
    def _gff_has_twoda_token(
        mod_gff: ModificationsGFF,
        path: str,
        token_id: int,
    ) -> bool:
        for modifier in mod_gff.modifiers:
            if not isinstance(modifier, ModifyFieldGFF):
                continue

            existing_path: str = str(modifier.path).replace("/", "\\")
            if existing_path.lower() != path.lower():
                continue

            if isinstance(modifier.value, FieldValue2DAMemory) and modifier.value.token_id == token_id:
                return True

        return False

    def _write_gff_modification(
        self,
        mod_gff: ModificationsGFF,
        source_data: bytes | None,
    ) -> None:
        """Write GFF resource file and INI section."""
        filename: str = mod_gff.sourcefile

        # Skip if already written
        if filename in self.written_sections:
            _log_debug(f"Skipping already written GFF: {filename}")
            return

        # Get destination for INI tracking
        destination: str = getattr(mod_gff, "destination", "Override")

        # Get actual filename (might be different from sourcefile)
        actual_filename: str = getattr(mod_gff, "saveas", mod_gff.sourcefile)

        # CRITICAL: ALL files go directly in tslpatchdata root, NOT in subdirectories
        # The destination field tells TSLPatcher where to install them at runtime
        output_path: Path = self.tslpatchdata_path / actual_filename

        # Write resource file (base vanilla GFF that will be patched)
        if source_data:
            try:
                gff_obj = read_gff(source_data)
                ext = PurePath(actual_filename).suffix.lstrip(".").lower()
                restype: ResourceType | None = ResourceType.from_extension(ext)

                # If from_extension fails, try to determine from filename
                if restype is None or not restype.is_valid():
                    # Try mapping common GFF extensions
                    gff_extension_map: dict[str, ResourceType] = {
                        "are": ResourceType.ARE,
                        "dlg": ResourceType.DLG,
                        "fac": ResourceType.FAC,
                        "gff": ResourceType.GFF,
                        "git": ResourceType.GIT,
                        "gui": ResourceType.GUI,
                        "ifo": ResourceType.IFO,
                        "jrl": ResourceType.JRL,
                        "utc": ResourceType.UTC,
                        "utd": ResourceType.UTD,
                        "ute": ResourceType.UTE,
                        "uti": ResourceType.UTI,
                        "utm": ResourceType.UTM,
                        "utp": ResourceType.UTP,
                        "utw": ResourceType.UTW,
                    }
                    restype = gff_extension_map.get(ext)

                if restype is None or not restype.is_valid():
                    msg = f"Could not determine valid ResourceType for GFF file {actual_filename} (extension: {ext})"
                    self.log_func(msg)
                    return

                # Determine the desired output file format (GFF, GFF_XML, or GFF_JSON)
                file_format: ResourceType = detect_gff(source_data)
                if file_format not in {ResourceType.GFF, ResourceType.GFF_XML, ResourceType.GFF_JSON}:
                    file_format = ResourceType.GFF

                write_gff(gff_obj, output_path, file_format)
                _log_verbose(f"Wrote GFF file: {actual_filename}")
            except Exception as e:  # noqa: BLE001
                self.log_func(f"[Error] Failed to write GFF {actual_filename}: {e.__class__.__name__}: {e}")
                self.log_func("Full traceback:")
                for line in traceback.format_exc().splitlines():
                    self.log_func(f"  {line}")
                return

        # Add to install folders
        self._add_to_install_folder(destination, actual_filename)

        # Write INI section
        self._write_to_ini([mod_gff], "gff")
        self.written_sections.add(filename)

        # Track in all_modifications
        self.all_modifications.gff.append(mod_gff)

    def _write_tlk_modification(
        self,
        mod_tlk: ModificationsTLK,
    ) -> None:
        """Write TLK modification and create linking patches.

        This is where we use the StrRef cache to find all files that need
        linking patches for the modified TLK entries.
        """
        filename: str = mod_tlk.sourcefile

        # Skip if already written
        if filename in self.written_sections:
            _log_debug(f"Skipping already written TLK: {filename}")
            return

        # Generate append.tlk file
        appends: list[ModifyTLK] = [m for m in mod_tlk.modifiers if not m.is_replacement]

        if appends:
            _log_debug(f"Creating append.tlk with {len(appends)} entries")
            append_tlk: TLK = TLK()
            append_tlk.resize(len(appends))

            sorted_appends: list[ModifyTLK] = sorted(appends, key=lambda m: m.token_id)

            for append_idx, modifier in enumerate(sorted_appends):
                text: str = modifier.text if modifier.text else ""
                sound_str: str = str(modifier.sound) if modifier.sound else ""
                append_tlk.replace(append_idx, text, sound_str)

            append_path: Path = self.tslpatchdata_path / "append.tlk"
            write_tlk(append_tlk, append_path, ResourceType.TLK)
            _log_verbose(f"Wrote append.tlk with {len(appends)} entries")

        # Add to install folders
        self._add_to_install_folder(".", "append.tlk")

        # Find StrRef references and create linking patches IMMEDIATELY - ONE AT A TIME
        # Get strref_mappings and source installations from the metadata dict
        tlk_metadata: dict[str, Any] | None = self._tlk_metadata.get(id(mod_tlk))
        strref_mappings: dict[int, int] = {}
        source_installations: list[Installation | Path] = []

        if tlk_metadata:
            strref_mappings = tlk_metadata.get("strref_mappings", {})
            source_installations = tlk_metadata.get("source_installations", [])

        if strref_mappings:
            # If no installations from metadata, try fallback
            if not source_installations and self.base_data_path:
                source_installations.append(self.base_data_path)

            # For diff entries, search BOTH installations for references
            # References to the old StrRef might exist in either installation
            if source_installations:
                # Process each StrRef ONE AT A TIME
                for old_strref, new_token_id in strref_mappings.items():
                    # Find the modifier entry that corresponds to this StrRef
                    modifier_entry: ModifyTLK | None = None
                    for modifier in mod_tlk.modifiers:
                        if modifier.mod_index == old_strref:
                            modifier_entry = modifier
                            break

                    # Check if StrRef exists in both installations (diff) or just one (unique)
                    exists_in_path1: bool = False
                    exists_in_path2: bool = False
                    path1_text: str = ""
                    path1_sound: str = ""
                    path2_text: str = ""
                    path2_sound: str = ""
                    new_text: str = ""

                    # Check first source installation (path1)
                    if source_installations and len(source_installations) > 0 and isinstance(source_installations[0], Installation):
                        try:
                            talktable = source_installations[0].talktable()
                            path1_text = talktable.string(old_strref)
                            path1_sound = str(talktable.sound(old_strref))
                            # Empty string means the entry doesn't exist or is invalid
                            exists_in_path1 = bool(path1_text) or bool(path1_sound)
                        except Exception:  # noqa: BLE001
                            exists_in_path1 = False

                    # Check second source installation (path2) if it exists
                    if source_installations and len(source_installations) > 1 and isinstance(source_installations[1], Installation):
                        try:
                            talktable = source_installations[1].talktable()
                            path2_text = talktable.string(old_strref)
                            path2_sound = str(talktable.sound(old_strref))
                            # Empty string means the entry doesn't exist or is invalid
                            exists_in_path2 = bool(path2_text) or bool(path2_sound)
                        except Exception:  # noqa: BLE001
                            exists_in_path2 = False

                    # Get new entry from modifier
                    if modifier_entry:
                        new_text = modifier_entry.text if modifier_entry.text else ""

                    # Log the diff
                    self.log_func(f"\n=== Finding References for StrRef {old_strref} -> Token {new_token_id} ===")

                    # Determine which installations to search based on where the entry exists
                    installations_to_search: list[Installation | Path] = []

                    # If exists in both paths, show diff format
                    if exists_in_path1 and exists_in_path2:
                        self.log_func(f"  Diff: StrRef {old_strref}")
                        path1_name = source_installations[0].path() if isinstance(source_installations[0], Installation) else str(source_installations[0])
                        path2_name = source_installations[1].path() if isinstance(source_installations[1], Installation) else str(source_installations[1])
                        self.log_func(f"    Path 1 ({path1_name}): {path1_text[:100]}{'...' if len(path1_text) > 100 else ''}")
                        self.log_func(f"    Path 2 ({path2_name}): {path2_text[:100]}{'...' if len(path2_text) > 100 else ''}")
                        # Search both paths for diff entries
                        installations_to_search = source_installations
                    # If exists only in path1, show unique to path1
                    elif exists_in_path1:
                        path1_name = source_installations[0].path() if isinstance(source_installations[0], Installation) else str(source_installations[0])
                        self.log_func(f"  Unique to Path 1 ({path1_name}): {path1_text[:100]}{'...' if len(path1_text) > 100 else ''}")
                        # Search only path1
                        installations_to_search = [source_installations[0]]
                    # If exists only in path2, show unique to path2
                    elif exists_in_path2:
                        path2_name = source_installations[1].path() if isinstance(source_installations[1], Installation) else str(source_installations[1])
                        self.log_func(f"  Unique to Path 2 ({path2_name}): {path2_text[:100]}{'...' if len(path2_text) > 100 else ''}")
                        # Search only path2
                        installations_to_search = [source_installations[1]]
                    # If doesn't exist in either but has new text from modifier, it's a new entry
                    elif new_text:
                        self.log_func(f"  New entry: {new_text[:100]}{'...' if len(new_text) > 100 else ''}")
                        # Don't search for references to new entries that don't exist yet
                        installations_to_search = []

                    # Search only the installations where the entry exists
                    for source in installations_to_search:
                        installation_name = source.path() if isinstance(source, Installation) else str(source)
                        self.log_func(f"  Searching in: {installation_name}")
                        self._find_and_patch_single_strref(source, old_strref, new_token_id)
            else:
                self.log_func(f"[Warning] No source installations for TLK {mod_tlk.saveas}, cannot find StrRef references")

        # Write INI section
        self._write_to_ini([mod_tlk], "tlk")
        self.written_sections.add(filename)

        # Track in all_modifications
        self.all_modifications.tlk.append(mod_tlk)

    @staticmethod
    def _get_resource_priority(resource: FileResource, installation: Installation) -> int:
        """Get resource priority based on KOTOR resolution order.

        Returns priority (lower = higher priority):
        0 = Override (highest)
        1 = Modules (.mod)
        2 = Modules (.rim/_s.rim/_dlg.erf)
        3 = Chitin BIFs (lowest)
        """
        filepath = resource.filepath()
        parent_names_lower = [parent.name.lower() for parent in filepath.parents]

        if "override" in parent_names_lower:
            return 0
        if "modules" in parent_names_lower:
            name_lower = filepath.name.lower()
            if name_lower.endswith(".mod"):
                return 1
            return 2  # .rim/_s.rim/_dlg.erf
        if "data" in parent_names_lower or filepath.suffix.lower() == ".bif":
            return 3
        # Files directly in installation root treated as Override priority
        if filepath.parent == installation.path():
            return 0
        # Default to lowest priority if unknown
        return 3

    def _find_and_patch_single_strref(
        self,
        source: Installation | Path,
        strref: int,
        token_id: int,
    ) -> None:
        """Find ALL references to a SINGLE StrRef and create linking patches IMMEDIATELY.

        Only uses the highest priority resource when multiple instances exist,
        following KOTOR resource resolution order: Override > Modules > Chitin

        Args:
            source: Installation or Path where the StrRef came from
            strref: The single StrRef ID to find references for
            token_id: The token ID to use in linking patches
        """
        # If it's an Installation, use the dedicated function from talktable.py
        if isinstance(source, Installation):
            from pykotor.extract.talktable import (  # noqa: PLC0415
                GFFRefLocation,
                NCSRefLocation,
                SSFRefLocation,
                TwoDARefLocation,
                find_strref_references,
            )

            self.log_func(f"Searching Installation for StrRef {strref}...")
            try:
                # Use the new function that returns COMPLETE typed location data
                search_results = find_strref_references(source, strref, logger=self.log_func)

                self.log_func(f"Found {len(search_results)} resource(s) referencing StrRef {strref}")

                # Group results by resource identifier (resname.restype)
                # Only use the highest priority resource when duplicates exist
                grouped_results: dict[str, list[StrRefSearchResult]] = {}
                for search_result in search_results:
                    resource = search_result.resource
                    resource_id = resource.filename().lower()

                    if resource_id not in grouped_results:
                        grouped_results[resource_id] = []
                    grouped_results[resource_id].append(search_result)

                # For each unique resource, pick the highest priority instance
                prioritized_results: list[StrRefSearchResult] = []
                for resource_id, results_group in grouped_results.items():
                    if len(results_group) == 1:
                        prioritized_results.append(results_group[0])
                    else:
                        # Multiple instances - pick highest priority (lowest priority number)
                        best_result: StrRefSearchResult = min(results_group, key=lambda r: self._get_resource_priority(r.resource, source))
                        best_priority = self._get_resource_priority(best_result.resource, source)
                        priority_names = ["Override", "Modules (.mod)", "Modules (.rim)", "Chitin BIFs"]
                        self.log_func(f"  Multiple instances of {resource_id} found, using {priority_names[best_priority]} version")
                        prioritized_results.append(best_result)

                # Store references temporarily instead of creating patches IMMEDIATELY
                # They will be applied when the file is actually diffed
                for search_result in prioritized_results:
                    resource = search_result.resource
                    locations = search_result.locations  # Typed location objects!
                    resource_filename = resource.filename()

                    try:
                        filename = resource_filename.lower()
                        resource_identifier = resource.identifier()

                        # Get relative path for logging (using path_ident for BIF/capsule resources)
                        try:
                            path_ident = resource.path_ident()
                            relative_path = path_ident.relative_to(source.path())
                            rel_path_str = relative_path.as_posix()
                        except ValueError:
                            rel_path_str = str(resource.path_ident())

                        resname_ext = f"{resource_identifier.resname}.{resource_identifier.restype.extension}"
                        self.log_func(f"  Resource: {rel_path_str} ({resname_ext})")

                        # Store references temporarily instead of creating patches immediately
                        # Process each location based on its type - NO STRING PARSING!
                        for location in locations:
                            if isinstance(location, TwoDARefLocation):
                                # Store 2DA reference for later
                                self._store_pending_strref_reference(
                                    filename,
                                    source,
                                    strref,
                                    token_id,
                                    "2da",
                                    {"row_index": location.row_index, "column_name": location.column_name, "resource_path": rel_path_str},
                                )
                            elif isinstance(location, SSFRefLocation):
                                # Store SSF reference for later
                                self._store_pending_strref_reference(
                                    filename,
                                    source,
                                    strref,
                                    token_id,
                                    "ssf",
                                    {"sound": location.sound},
                                )
                            elif isinstance(location, GFFRefLocation):
                                # Store GFF reference for later
                                self._store_pending_strref_reference(
                                    filename,
                                    source,
                                    strref,
                                    token_id,
                                    "gff",
                                    {"field_path": location.field_path},
                                )
                            elif isinstance(location, NCSRefLocation):
                                # Store NCS reference for later
                                self._store_pending_strref_reference(
                                    filename,
                                    source,
                                    strref,
                                    token_id,
                                    "ncs",
                                    {"byte_offset": location.byte_offset},
                                )

                    except Exception as e:
                        self.log_func(f"[Warning] Error processing resource {resource_filename}: {e.__class__.__name__}: {e}")
                        self.log_func(traceback.format_exc())

            except Exception as e:
                self.log_func(f"[Error] Failed to search Installation: {e.__class__.__name__}: {e}")
                self.log_func(traceback.format_exc())

        elif isinstance(source, Path):
            # Path-based scanning is not supported with typed location objects
            # Only Installation-based scanning returns proper typed location data
            self.log_func(f"[Warning] Path-based StrRef searching not supported (only Installation): {source}")

    def _find_and_patch_single_2da_row(
        self,
        source: Installation | Path,
        twoda_filename: str,
        row_index: int,
        token_id: int,
    ) -> None:
        """Find ALL references to a SINGLE 2DA row and create linking patches IMMEDIATELY.

        Args:
            source: Installation or Path where the 2DA came from
            twoda_filename: Name of the 2DA file (e.g., "soundset.2da")
            row_index: The row index to find references for
            token_id: The 2DAMEMORY token ID to use in linking patches
        """
        # Get the 2DA identifier for field mapping
        twoda_resname = twoda_filename.lower().replace(".2da", "")

        # Find which GFF fields reference this 2DA file
        reverse_mapping: dict[str, list[str]] = {}  # 2da_name -> [field_names]
        for field_name, resource_id in GFF_FIELD_TO_2DA_MAPPING.items():
            if resource_id.resname.lower() == twoda_resname:
                if twoda_resname not in reverse_mapping:
                    reverse_mapping[twoda_resname] = []
                reverse_mapping[twoda_resname].append(field_name)

        if twoda_resname not in reverse_mapping:
            self.log_func(f"  No known GFF fields reference {twoda_filename}")
            return

        field_names = reverse_mapping[twoda_resname]
        self.log_func(f"  Looking for fields: {', '.join(field_names)}")

        # If Installation, scan all GFF files
        if isinstance(source, Installation):
            self.log_func(f"Searching Installation for references to {twoda_filename} row {row_index}...")
            found_count = 0

            for resource in source:
                try:
                    restype = resource.restype()
                    if restype not in GFFContent.get_restypes():
                        continue

                    data = resource.data()
                    filename = resource.filename().lower()

                    # Find field paths in this GFF that reference our row index
                    field_paths = self._find_2da_row_in_gff(data, field_names, row_index)
                    if field_paths:
                        self._create_immediate_gff_2da_patches(filename, field_paths, token_id)
                        found_count += 1

                except Exception as e:
                    _log_debug(f"Error scanning resource for 2DA refs: {e.__class__.__name__}: {e}")

            self.log_func(f"Found {found_count} file(s) referencing {twoda_filename} row {row_index}")

        # If Path, scan directory/file
        elif isinstance(source, Path):
            self.log_func(f"Searching Path for references to {twoda_filename} row {row_index}...")
            found_count = 0

            if source.is_dir():
                for file_path in source.rglob("*"):
                    if file_path.is_file():
                        try:
                            restype = ResourceType.from_extension(file_path.suffix)
                            if restype not in GFFContent.get_restypes():
                                continue

                            data = file_path.read_bytes()
                            filename = file_path.name.lower()

                            field_paths = self._find_2da_row_in_gff(data, field_names, row_index)
                            if field_paths:
                                self._create_immediate_gff_2da_patches(filename, field_paths, token_id)
                                found_count += 1

                        except Exception as e:
                            _log_debug(f"Error scanning file for 2DA refs: {e.__class__.__name__}: {e}")

            elif source.is_file():
                try:
                    restype = ResourceType.from_extension(source.suffix)
                    if restype in GFFContent.get_restypes():
                        data = source.read_bytes()
                        filename = source.name.lower()

                        field_paths = self._find_2da_row_in_gff(data, field_names, row_index)
                        if field_paths:
                            self._create_immediate_gff_2da_patches(filename, field_paths, token_id)
                            found_count += 1
                except Exception as e:
                    self.log_func(f"[Warning] Error scanning file: {e.__class__.__name__}: {e}")

            self.log_func(f"Found {found_count} file(s) referencing {twoda_filename} row {row_index}")

    def _find_and_patch_single_2da_row_by_label(
        self,
        source: Installation | Path,
        twoda_filename: str,
        row_label: str,
        token_id: int,
    ) -> None:
        """Find references to a 2DA row by its label (for AddRow2DA)."""
        # For new rows (AddRow2DA), we need to first look up the row index in the source
        # by finding the row with the matching label
        self.log_func(f"  Looking up row index for label '{row_label}' in {twoda_filename}...")

        # Try to load the 2DA and find the row index
        row_index: int | None = None
        if isinstance(source, Installation):
            resource = source.resource(twoda_filename.replace(".2da", ""), ResourceType.TwoDA)
            if resource and resource.data:
                try:
                    twoda = read_2da(resource.data)
                    for idx in range(twoda.get_height()):
                        if twoda.get_row_label(idx) == row_label:
                            row_index = idx
                            break
                except Exception as e:
                    _log_debug(f"Error reading 2DA for label lookup: {e.__class__.__name__}: {e}")
        elif isinstance(source, Path):
            twoda_path = source / twoda_filename if source.is_dir() else source
            if twoda_path.exists():
                try:
                    data = twoda_path.read_bytes()
                    twoda = read_2da(data)
                    for idx in range(twoda.get_height()):
                        if twoda.get_row_label(idx) == row_label:
                            row_index = idx
                            break
                except Exception as e:
                    _log_debug(f"Error reading 2DA for label lookup: {e.__class__.__name__}: {e}")

        if row_index is None:
            self.log_func(f"  Could not find row with label '{row_label}' in {twoda_filename}")
            return

        self.log_func(f"  Found row index {row_index} for label '{row_label}'")
        # Now use the standard row index lookup
        self._find_and_patch_single_2da_row(source, twoda_filename, row_index, token_id)

    def _find_2da_row_in_gff(
        self,
        data: bytes,
        field_names: list[str],
        row_index: int,
    ) -> list[str]:
        """Find GFF field paths that reference a specific 2DA row index."""
        field_paths = []
        try:
            gff = read_gff(data)
            self._scan_gff_for_2da_row(gff.root, field_names, row_index, "", field_paths)
        except Exception as e:
            _log_debug(f"Error reading GFF for 2DA row search: {e.__class__.__name__}: {e}")
        return field_paths

    def _scan_gff_for_2da_row(
        self,
        struct: GFFStruct,
        field_names: list[str],
        row_index: int,
        path_prefix: str,
        field_paths: list[str],
    ) -> None:
        """Recursively scan GFF for fields that reference a specific 2DA row."""
        for field_label, field_type, field_value in struct:
            field_path = f"{path_prefix}.{field_label}" if path_prefix else field_label

            try:
                # Check if this field name matches one we're looking for
                if field_label in field_names and isinstance(field_value, int) and field_value == row_index:
                    field_paths.append(field_path)

                # Recurse into structs and lists
                if field_type == GFFFieldType.Struct:
                    assert isinstance(field_value, GFFStruct), f"Expected GFFStruct, got {type(field_value).__name__}"
                    self._scan_gff_for_2da_row(field_value, field_names, row_index, field_path, field_paths)
                elif field_type == GFFFieldType.List:
                    assert isinstance(field_value, GFFList), f"Expected GFFList, got {type(field_value).__name__}"
                    for idx, list_struct in enumerate(field_value):
                        assert isinstance(list_struct, GFFStruct), f"Expected GFFStruct, got {type(list_struct).__name__}"
                        list_path = f"{field_path}[{idx}]"
                        self._scan_gff_for_2da_row(list_struct, field_names, row_index, list_path, field_paths)

            except Exception as e:
                _log_debug(f"Error scanning GFF field for 2DA row: {e.__class__.__name__}: {e}")

    def _create_immediate_gff_2da_patches(
        self,
        gff_filename: str,
        field_paths: list[str],
        token_id: int,
    ) -> None:
        """Create GFF patches that replace 2DA row references with 2DAMEMORY tokens."""
        # Find or create ModificationsGFF for this file
        existing_mod = next((m for m in self.all_modifications.gff if m.sourcefile == gff_filename), None)
        is_new = existing_mod is None

        if existing_mod is None:
            existing_mod = ModificationsGFF(gff_filename, replace=False, modifiers=[])
            self.all_modifications.gff.append(existing_mod)

        # Create ModifyFieldGFF entries for each field path
        for field_path in field_paths:
            # Create a FieldValue2DAMemory value
            field_value = FieldValue2DAMemory(token_id)

            modifier = ModifyFieldGFF(field_path, field_value)
            existing_mod.modifiers.append(modifier)

            self.log_func(f"  Created patch: {gff_filename} -> {field_path} = 2DAMEMORY{token_id}")

        # Write to changes.ini IMMEDIATELY
        if is_new:
            self._write_gff_modification(existing_mod, None)
        else:
            # Re-append to update existing section
            if existing_mod.sourcefile in self.written_sections:
                self.written_sections.discard(existing_mod.sourcefile)
            self._write_to_ini([existing_mod], "gff")
            self.written_sections.add(existing_mod.sourcefile)

    def _find_strref_locations_in_2da(
        self,
        data: bytes,
        strref: int,
    ) -> list[str]:
        """Find specific cell locations in a 2DA file that contain the StrRef."""
        locations = []
        try:
            twoda = read_2da(data)
            self.log_func(f"    [DEBUG] Scanning 2DA: {twoda.get_height()} rows, {len(twoda.get_labels())} columns")
            for row_idx in range(twoda.get_height()):
                for col_label in twoda.get_labels():
                    try:
                        cell_value = twoda.get_cell(row_idx, col_label)
                        if cell_value and cell_value.strip().isdigit() and int(cell_value) == strref:
                            self.log_func(f"    [DEBUG] Found match: row {row_idx}, column '{col_label}', value='{cell_value}', strref={strref}")
                            locations.append(f"row_{row_idx}.{col_label}")
                    except Exception as e:
                        self.log_func(f"    [DEBUG] Error scanning 2DA cell [{row_idx}][{col_label}]: {e.__class__.__name__}: {e}")
            self.log_func(f"    [DEBUG] _find_strref_locations_in_2da found {len(locations)} locations for StrRef {strref}")
        except Exception as e:
            self.log_func(f"    [DEBUG] Error reading 2DA: {e.__class__.__name__}: {e}")
            self.log_func(traceback.format_exc())
        return locations

    def _find_strref_locations_in_ssf(
        self,
        data: bytes,
        strref: int,
    ) -> list[str]:
        """Find specific sound slots in an SSF file that contain the StrRef."""
        locations = []
        try:
            ssf = read_ssf(data)
            for sound in SSFSound:
                sound_strref = ssf.get(sound)
                if sound_strref == strref:
                    locations.append(f"sound_{sound.name}")
        except Exception as e:
            _log_debug(f"Error reading SSF: {e.__class__.__name__}: {e}")
        return locations

    def _find_strref_locations_in_gff(
        self,
        data: bytes,
        strref: int,
    ) -> list[str]:
        """Find specific field paths in a GFF file that contain the StrRef."""
        locations = []
        try:
            gff = read_gff(data)
            self._scan_gff_for_single_strref(gff.root, strref, "", locations)
        except Exception as e:
            _log_debug(f"Error reading GFF: {e.__class__.__name__}: {e}")
        return locations

    def _find_strref_offsets_in_ncs(
        self,
        resource: FileResource,
        strref: int,
    ) -> list[int]:
        """Find byte offsets of all CONSTI instructions in an NCS file that contain the StrRef.

        Returns list of byte offsets where the 4-byte integer value starts
        (i.e., offset + 2 from instruction start).
        """
        from pykotor.common.stream import BinaryReader

        offsets: list[int] = []
        try:
            ncs_data = resource.data()
            with BinaryReader.from_auto(ncs_data) as reader:
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
                        if const_value == strref:
                            offsets.append(value_offset)
                    # Skip to next instruction based on opcode/qualifier
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
        except Exception as e:  # noqa: BLE001
            _log_debug(f"Error reading NCS for StrRef offsets: {e.__class__.__name__}: {e}")
        return offsets

    def _scan_gff_for_single_strref(
        self,
        struct: GFFStruct,
        strref: int,
        path_prefix: str,
        locations: list[str],
    ) -> None:
        """Recursively scan GFF struct for a single StrRef."""
        field_label: str
        field_type: GFFFieldType
        field_value: int | str | ResRef | Vector3 | Vector4 | LocalizedString | GFFStruct | GFFList | bytes | float
        for field_label, field_type, field_value in struct:
            field_path = f"{path_prefix}.{field_label}" if path_prefix else field_label

            try:
                # LocalizedString fields
                if field_type == GFFFieldType.LocalizedString and isinstance(field_value, LocalizedString) and field_value.stringref == strref:
                    locations.append(field_path)
            except Exception as e:
                _log_debug(f"Error scanning GFF field {field_path}: {e.__class__.__name__}: {e}")

    # REMOVED: _scan_resource_for_strrefs and _scan_gff_struct_for_strrefs
    # These were batch/multi-strref scanners, no longer used
    # Now using single-strref variants: _find_strref_locations_in_*

    def _store_pending_strref_reference(
        self,
        filename: str,
        source_path: Installation | Path,
        old_strref: int,
        token_id: int,
        location_type: str,
        location_data: dict[str, Any],
    ) -> None:
        """Store a StrRef reference temporarily until the file is diffed.

        Args:
            filename: Resource filename (lowercase)
            source_path: Installation or Path where the StrRef was found
            old_strref: The original StrRef value
            token_id: The TLKMEMORY token ID to use
            location_type: Type of location ("2da", "ssf", "gff", "ncs")
            location_data: Location-specific data
        """
        if filename not in self._pending_strref_references:
            self._pending_strref_references[filename] = []

        pending_ref = PendingStrRefReference(
            filename=filename,
            source_path=source_path,
            old_strref=old_strref,
            token_id=token_id,
            location_type=location_type,
            location_data=location_data,
        )
        self._pending_strref_references[filename].append(pending_ref)
        self.log_func(f"    Stored pending StrRef reference: {filename} ({location_type}) -> Token {token_id}")

    def _apply_pending_strref_references(
        self,
        filename: str,
        modification: PatcherModifications,
        source_data: bytes | None,
        source_path: Installation | Path | None = None,
    ) -> None:
        """Check and apply pending StrRef references for a file being diffed.

        Only applies references if:
        - The file matches the pending reference filename
        - AND it comes from the same path as where the StrRef was found
        - AND the StrRef still exists at the expected location in the source data

        References are only relevant to the path they're from.

        Args:
            filename: The filename being diffed (lowercase)
            modification: The modification object being written
            source_data: Optional source data to verify StrRef still exists
            source_path: Optional path where this file is coming from
        """
        if filename not in self._pending_strref_references:
            return

        pending_refs = self._pending_strref_references[filename]
        if not pending_refs:
            return

        applied_refs: list[PendingStrRefReference] = []
        for pending_ref in pending_refs:
            # Only apply references if they come from the same path
            # References are only relevant to the path they're from
            should_apply = False

            if source_path is not None:
                # Check if paths match exactly
                if isinstance(pending_ref.source_path, Installation) and isinstance(source_path, Installation):
                    should_apply = pending_ref.source_path.path() == source_path.path()
                elif isinstance(pending_ref.source_path, Path) and isinstance(source_path, Path):
                    should_apply = pending_ref.source_path == source_path

            # If source_path is None, we can't verify the path match, so don't apply
            # Also verify the StrRef still exists at the expected location in the source data
            if should_apply and source_data is not None:
                should_apply = self._verify_strref_location(source_data, pending_ref)

            if should_apply:
                # Apply the reference to the modification object being written
                if pending_ref.location_type == "2da":
                    self._create_immediate_2da_strref_patch_single(
                        filename,
                        pending_ref.old_strref,
                        pending_ref.token_id,
                        pending_ref.location_data["row_index"],
                        pending_ref.location_data["column_name"],
                        pending_ref.location_data.get("resource_path"),
                        modification,  # Pass the modification object being written
                    )
                elif pending_ref.location_type == "ssf":
                    self._create_immediate_ssf_strref_patch_single(
                        filename,
                        pending_ref.old_strref,
                        pending_ref.token_id,
                        pending_ref.location_data["sound"],
                        modification,  # Pass the modification object being written
                    )
                elif pending_ref.location_type == "gff":
                    self._create_immediate_gff_strref_patch_single(
                        filename,
                        pending_ref.old_strref,
                        pending_ref.token_id,
                        pending_ref.location_data["field_path"],
                        modification,  # Pass the modification object being written
                    )
                elif pending_ref.location_type == "ncs":
                    self._create_immediate_ncs_strref_patch_single(
                        filename,
                        pending_ref.old_strref,
                        pending_ref.token_id,
                        pending_ref.location_data["byte_offset"],
                        modification,  # Pass the modification object being written
                    )
                applied_refs.append(pending_ref)

        # Remove applied references
        for applied_ref in applied_refs:
            pending_refs.remove(applied_ref)
        if not pending_refs:
            del self._pending_strref_references[filename]

    def _verify_strref_location(
        self,
        data: bytes,
        pending_ref: PendingStrRefReference,
    ) -> bool:
        """Verify that a StrRef still exists at the expected location in the data.

        Args:
            data: The file data to check
            pending_ref: The pending StrRef reference

        Returns:
            True if the StrRef exists at the expected location, False otherwise
        """
        try:
            if pending_ref.location_type == "2da":
                twoda = read_2da(data)
                row_index = pending_ref.location_data["row_index"]
                column_name = pending_ref.location_data["column_name"]
                cell_value = twoda.get_cell(row_index, column_name)
                if cell_value and cell_value.strip().isdigit():
                    return int(cell_value.strip()) == pending_ref.old_strref
                return False

            if pending_ref.location_type == "ssf":
                ssf = read_ssf(data)
                sound = pending_ref.location_data["sound"]
                return ssf.get(sound) == pending_ref.old_strref

            if pending_ref.location_type == "gff":
                gff_obj = read_gff(data)
                field_path = pending_ref.location_data["field_path"]
                # Navigate to the field path and check if it has the StrRef
                return self._check_gff_field_strref(gff_obj.root, field_path, pending_ref.old_strref)

            if pending_ref.location_type == "ncs":
                # For NCS, check if the byte offset still contains the StrRef
                from pykotor.common.stream import BinaryReader

                with BinaryReader.from_auto(data) as reader:
                    reader.seek(pending_ref.location_data["byte_offset"])
                    value = reader.read_int32(big=True)
                    return value == pending_ref.old_strref

        except Exception as e:  # noqa: BLE001
            _log_debug(f"Error verifying StrRef location: {e.__class__.__name__}: {e}")
            return False

        return False

    def _check_gff_field_strref(
        self,
        struct: GFFStruct,
        field_path: str,
        strref: int,
    ) -> bool:
        """Check if a GFF field at the given path contains the StrRef.

        Args:
            struct: The GFF struct to search
            field_path: The field path (e.g., "FirstName", "ItemList[0].LocalizedName")
            strref: The StrRef value to check for

        Returns:
            True if the field contains the StrRef, False otherwise
        """
        from pykotor.common.language import LocalizedString
        from pykotor.resource.formats.gff.gff_data import GFFFieldType, GFFList

        # Parse field path (handle array indices)
        parts = field_path.split(".")
        current = struct

        for i, part in enumerate(parts):
            if "[" in part and "]" in part:
                # Array access like "ItemList[0]"
                field_label = part[: part.index("[")]
                index = int(part[part.index("[") + 1 : part.index("]")])
                # Get the field from current struct
                for field_label_check, field_type, field_value in current:
                    if field_label_check == field_label and field_type == GFFFieldType.List and isinstance(field_value, GFFList):
                        if index < len(field_value):
                            current = field_value[index]
                            break
                        return False
                else:
                    return False
            # Regular field access
            if i == len(parts) - 1:
                # Last part - check if it has the StrRef
                for field_label_check, field_type, field_value in current:
                    if field_label_check == part:
                        if field_type == GFFFieldType.LocalizedString and isinstance(field_value, LocalizedString):
                            return field_value.stringref == strref
                        return False
                return False

            # Not the last part - navigate deeper
            for field_label_check, field_type, field_value in current:
                if field_label_check == part:
                    if field_type == GFFFieldType.Struct and isinstance(field_value, GFFStruct):
                        current = field_value
                        break
                    return False
            else:
                return False

        return False

    def _create_immediate_2da_strref_patch_single(
        self,
        filename: str,
        old_strref: int,
        token_id: int,
        row_index: int,
        column_name: str,
        resource_path: str | None = None,
        modification: PatcherModifications | None = None,
    ) -> None:
        """Create a single 2DA patch for a StrRef reference immediately.

        Args:
            filename: 2DA filename (e.g., "planetary.2da")
            old_strref: The original StrRef value
            token_id: The TLKMEMORY token ID to use
            row_index: The row index containing the reference
            column_name: The column name containing the reference
            resource_path: Optional path for logging
            modification: Optional modification object to add to (if provided, use this instead of searching)
        """
        from pykotor.tslpatcher.mods.twoda import (
            ChangeRow2DA,
            Modifications2DA,
            Target,
            TargetType,
        )

        # Use the provided modification if it matches, otherwise find or create one
        if modification is not None and isinstance(modification, Modifications2DA) and modification.sourcefile.lower() == filename.lower():
            existing_mod = modification
            is_new_mod = existing_mod.sourcefile not in self.written_sections
        else:
            # Get or create 2DA modification from all_modifications
            existing_mod = next((m for m in self.all_modifications.twoda if m.sourcefile == filename), None)
            is_new_mod = existing_mod is None

            if not existing_mod:
                existing_mod = Modifications2DA(filename)
                self.all_modifications.twoda.append(existing_mod)

        # Create the patch
        change_row = ChangeRow2DA(
            identifier=f"strref_link_{old_strref}_{row_index}_{column_name}",
            target=Target(TargetType.ROW_INDEX, row_index),
            cells={column_name: RowValueTLKMemory(token_id)},
        )
        existing_mod.modifiers.append(change_row)

        # Log the patch being created
        path_info = f" at {resource_path}" if resource_path else ""
        self.log_func(f"    Creating patch: row {row_index}, column '{column_name}' -> Token {token_id}{path_info}")

        # Write to INI
        if is_new_mod:
            self._write_2da_modification(existing_mod, None)
        else:
            self.written_sections.discard(filename)
            self._write_to_ini([existing_mod], "2da")
            self.written_sections.add(filename)

    def _create_immediate_ssf_strref_patch_single(
        self,
        filename: str,
        old_strref: int,
        token_id: int,
        sound: SSFSound,
        modification: PatcherModifications | None = None,
    ) -> None:
        """Create a single SSF patch for a StrRef reference immediately.

        Args:
            filename: SSF filename
            old_strref: The original StrRef value
            token_id: The TLKMEMORY token ID to use
            sound: The SSFSound enum identifying the sound slot
            modification: Optional modification object to add to (if provided, use this instead of searching)
        """
        from pykotor.tslpatcher.memory import TokenUsageTLK  # noqa: PLC0415
        from pykotor.tslpatcher.mods.ssf import ModificationsSSF, ModifySSF  # noqa: PLC0415

        # Use the provided modification if it matches, otherwise find or create one
        if modification is not None and isinstance(modification, ModificationsSSF) and modification.sourcefile.lower() == filename.lower():
            existing_mod = modification
            is_new_mod = existing_mod.sourcefile not in self.written_sections
        else:
            # Get or create SSF modification from all_modifications
            existing_mod = next((m for m in self.all_modifications.ssf if m.sourcefile == filename), None)
            is_new_mod = existing_mod is None

            if not existing_mod:
                existing_mod = ModificationsSSF(filename, replace=False, modifiers=[])
                self.all_modifications.ssf.append(existing_mod)

        # Create the patch
        modify_ssf = ModifySSF(sound, TokenUsageTLK(token_id))
        existing_mod.modifiers.append(modify_ssf)

        self.log_func(f"    Creating patch: sound '{sound.name}' -> Token {token_id}")

        # Write to INI
        if is_new_mod:
            self._write_ssf_modification(existing_mod, None)
        else:
            self.written_sections.discard(filename)
            self._write_to_ini([existing_mod], "ssf")
            self.written_sections.add(filename)

    def _create_immediate_gff_strref_patch_single(
        self,
        filename: str,
        old_strref: int,
        token_id: int,
        field_path: str,
        modification: PatcherModifications | None = None,
    ) -> None:
        """Create a single GFF patch for a StrRef reference immediately.

        Args:
            filename: GFF filename
            old_strref: The original StrRef value
            token_id: The TLKMEMORY token ID to use
            field_path: The GFF field path (e.g., "FirstName", "ItemList[0].LocalizedName")
            modification: Optional modification object to add to (if provided, use this instead of searching)
        """
        from pykotor.tslpatcher.mods.gff import FieldValueTLKMemory, LocalizedStringDelta, ModificationsGFF, ModifyFieldGFF

        # Use the provided modification if it matches, otherwise find or create one
        if modification is not None and isinstance(modification, ModificationsGFF) and modification.sourcefile.lower() == filename.lower():
            existing_mod = modification
            is_new_mod = existing_mod.sourcefile not in self.written_sections
        else:
            # Get or create GFF modification from all_modifications
            existing_mod = next((m for m in self.all_modifications.gff if m.sourcefile == filename), None)
            is_new_mod = existing_mod is None

            if not existing_mod:
                existing_mod = ModificationsGFF(filename, replace=False, modifiers=[])
                self.all_modifications.gff.append(existing_mod)

        # Create the patch
        locstring_delta = LocalizedStringDelta(FieldValueTLKMemory(token_id))
        modify_field = ModifyFieldGFF(field_path, FieldValueConstant(locstring_delta))
        existing_mod.modifiers.append(modify_field)

        self.log_func(f"    Creating patch: field '{field_path}' -> Token {token_id}")

        # Write to INI
        if is_new_mod:
            self._write_gff_modification(existing_mod, None)
        else:
            self.written_sections.discard(filename)
            self._write_to_ini([existing_mod], "gff")
            self.written_sections.add(filename)

    def _create_immediate_ncs_strref_patch_single(
        self,
        filename: str,
        old_strref: int,
        token_id: int,
        byte_offset: int,
        modification: PatcherModifications | None = None,
    ) -> None:
        """Create a single NCS HACKList patch for a StrRef reference immediately.

        Args:
            filename: NCS filename
            old_strref: The original StrRef value
            token_id: The TLKMEMORY token ID to use
            byte_offset: The byte offset where the StrRef constant is located
            modification: Optional modification object to add to (if provided, use this instead of searching)
        """
        # Use the provided modification if it matches, otherwise find or create one
        if modification is not None and isinstance(modification, ModificationsNCS) and modification.sourcefile.lower() == filename.lower():
            existing_mod = modification
            is_new_mod = existing_mod.sourcefile not in self.written_sections
        else:
            # Get or create NCS modification from all_modifications
            existing_mod = next((m for m in self.all_modifications.ncs if m.sourcefile == filename), None)
            is_new_mod = existing_mod is None

            if not existing_mod:
                existing_mod = ModificationsNCS(filename, replace=False, modifiers=[])
                self.all_modifications.ncs.append(existing_mod)

        # Create the patch
        # CONSTI instructions store 32-bit signed integers, so use STRREF32 token type
        modify_ncs = ModifyNCS(
            token_type=NCSTokenType.STRREF32,
            offset=byte_offset,
            token_id_or_value=token_id,
        )
        existing_mod.modifiers.append(modify_ncs)

        self.log_func(f"    Creating patch: offset {byte_offset:#X} -> Token {token_id}")

        # Write to INI
        if is_new_mod:
            self._write_ncs_modification(existing_mod, None)
        else:
            self.written_sections.discard(filename)
            self._write_to_ini([existing_mod], "ncs")
            self.written_sections.add(filename)

    def _create_linking_patches_from_cache(
        self,
        mod_tlk: ModificationsTLK,
    ) -> None:
        """Create linking patches using the StrRef cache."""
        if not self.strref_cache:
            return

        strref_mappings: dict[int, int] = getattr(mod_tlk, "strref_mappings", {})
        if not strref_mappings:
            return

        self.log_func(f"\n=== Creating Linking Patches from Cache ({len(strref_mappings)} StrRefs) ===")

        for old_strref, token_id in strref_mappings.items():
            references = self.strref_cache.get_references(old_strref)

            if not references:
                continue

            self.log_func(f"  StrRef {old_strref} -> token {token_id}: {len(references)} file(s)")

            for identifier, locations in references:
                filename: str = f"{identifier.resname}.{identifier.restype.extension}".lower()
                restype: ResourceType = identifier.restype

                # 2DA files
                if restype is ResourceType.TwoDA:
                    existing_mod: Modifications2DA | None = next((m for m in self.all_modifications.twoda if m.sourcefile == filename), None)
                    is_new_mod: bool = existing_mod is None
                    if existing_mod is None:
                        existing_mod = Modifications2DA(filename)
                        # Write it immediately
                        self.all_modifications.twoda.append(existing_mod)
                        self._write_2da_modification(existing_mod, None)

                    for location in locations:
                        # Parse location: "row_N.column_name"
                        if location.startswith("row_"):
                            parts: list[str] = location.split(".")
                            row_idx_str: str = parts[0][4:]  # Remove "row_"
                            column_name: str = parts[1] if len(parts) > 1 else ""

                            if row_idx_str.isdigit():
                                row_idx: int = int(row_idx_str)
                                change_row = ChangeRow2DA(
                                    identifier=f"strref_link_{row_idx}_{column_name}",
                                    target=Target(TargetType.ROW_INDEX, row_idx),
                                    cells={column_name: RowValue2DAMemory(token_id)},
                                )
                                existing_mod.modifiers.append(change_row)

                    # Re-write INI section if we added modifiers to existing mod
                    if not is_new_mod and existing_mod.modifiers:
                        self.written_sections.discard(filename)
                        self._write_to_ini([existing_mod], "2da")
                        self.written_sections.add(filename)

                # SSF files
                elif restype is ResourceType.SSF:
                    existing_ssf_mod: ModificationsSSF | None = next((m for m in self.all_modifications.ssf if m.sourcefile == filename), None)
                    is_new_ssf_mod: bool = existing_ssf_mod is None
                    if existing_ssf_mod is None:
                        existing_ssf_mod = ModificationsSSF(filename, replace=False, modifiers=[])
                        self.all_modifications.ssf.append(existing_ssf_mod)
                        self._write_ssf_modification(existing_ssf_mod, None)

                    for location in locations:
                        # Parse location: "sound_SOUND_NAME"
                        if location.startswith("sound_"):
                            sound_name: str = location[6:]  # Remove "sound_"
                            try:
                                sound = SSFSound[sound_name]
                                modify_ssf = ModifySSF(sound, TokenUsageTLK(token_id))
                                existing_ssf_mod.modifiers.append(modify_ssf)
                            except KeyError:
                                _log_debug(f"Unknown SSF sound: {sound_name}")

                    # Re-write INI section if we added modifiers to existing mod
                    if not is_new_ssf_mod and existing_ssf_mod.modifiers:
                        self.written_sections.discard(filename)
                        self._write_to_ini([existing_ssf_mod], "ssf")
                        self.written_sections.add(filename)

                # GFF files
                else:
                    existing_gff_mod: ModificationsGFF | None = next((m for m in self.all_modifications.gff if m.sourcefile == filename), None)
                    is_new_gff_mod: bool = existing_gff_mod is None
                    if existing_gff_mod is None:
                        existing_gff_mod = ModificationsGFF(filename, replace=False, modifiers=[])
                        self.all_modifications.gff.append(existing_gff_mod)
                        self._write_gff_modification(existing_gff_mod, None)

                    for location in locations:
                        # Create LocalizedStringDelta with token
                        locstring_delta = LocalizedStringDelta(FieldValueTLKMemory(token_id))

                        modify_field = ModifyFieldGFF(
                            path=location.replace("/", "\\"),
                            value=FieldValueConstant(locstring_delta),
                            identifier=f"strref_link_{old_strref}_token_{token_id}",
                        )
                        existing_gff_mod.modifiers.append(modify_field)

                    # Re-write INI section if we added modifiers to existing mod
                    if not is_new_gff_mod and existing_gff_mod.modifiers:
                        self.written_sections.discard(filename)
                        self._write_to_ini([existing_gff_mod], "gff")
                        self.written_sections.add(filename)

        gff_count: int = len(self.all_modifications.gff)
        twoda_count: int = len(self.all_modifications.twoda)
        ssf_count: int = len(self.all_modifications.ssf)
        self.log_func(f"=== Linking Patches Created: {gff_count} GFF, {twoda_count} 2DA, {ssf_count} SSF ===")

    def _write_ssf_modification(
        self,
        mod_ssf: ModificationsSSF,
        source_data: bytes | None,
    ) -> None:
        """Write SSF resource file and INI section."""
        filename: str = mod_ssf.sourcefile

        # Skip if already written
        if filename in self.written_sections:
            _log_debug(f"Skipping already written SSF: {filename}")
            return

        # Write resource file
        if source_data:
            output_path: Path = self.tslpatchdata_path / filename
            try:
                ssf_obj = read_ssf(source_data)
                write_ssf(ssf_obj, output_path, ResourceType.SSF)
                _log_verbose(f"Wrote SSF file: {filename}")
            except Exception as e:  # noqa: BLE001
                self.log_func(f"[Error] Failed to write SSF {filename}: {e.__class__.__name__}: {e}")
                self.log_func("Full traceback:")
                for line in traceback.format_exc().splitlines():
                    self.log_func(f"  {line}")
                return

        # Add to install folders
        self._add_to_install_folder("Override", filename)

        # Write INI section
        self._write_to_ini([mod_ssf], "ssf")
        self.written_sections.add(filename)

        # Track in all_modifications
        if mod_ssf not in self.all_modifications.ssf:
            self.all_modifications.ssf.append(mod_ssf)

    def _write_ncs_modification(
        self,
        mod_ncs: ModificationsNCS,
        source_data: bytes | None,
    ) -> None:
        """Write NCS resource file and INI section."""
        filename: str = mod_ncs.sourcefile

        # Skip if already written
        if filename in self.written_sections:
            _log_debug(f"Skipping already written NCS: {filename}")
            return

        # Write resource file (if needed)
        if source_data is not None:
            output_path: Path = self.tslpatchdata_path / filename
            output_path.write_bytes(source_data)
            _log_verbose(f"Wrote NCS file: {filename}")

        # Write INI section
        self._write_to_ini([mod_ncs], "ncs")
        self.written_sections.add(filename)

        # Track in all_modifications
        if mod_ncs not in self.all_modifications.ncs:
            self.all_modifications.ncs.append(mod_ncs)

    @staticmethod
    def _format_ini_value(value: str | int | object) -> str:
        """Format an INI file value, wrapping in double quotes if it contains a single quote.

        Args:
            value: The value to format (will be converted to string)

        Returns:
            Formatted value, wrapped in double quotes if it contains a single quote
        """
        value_str = str(value)
        if "'" in value_str:
            return f'"{value_str}"'
        return value_str

    def _write_install_entry_to_ini(
        self,
        folder: str,
        filename: str,
    ) -> None:
        """Write a single InstallList entry to INI file in real-time."""
        # Normalize folder name
        dest_folder: str = folder if folder != "." else "Override"

        # Get or assign folder number
        is_new_folder: bool = dest_folder not in self.folder_numbers
        if is_new_folder:
            folder_num: int = self.next_folder_number
            self.folder_numbers[dest_folder] = folder_num
            self.next_folder_number += 1

            # Add install_folder#=folder line to [InstallList] section
            install_line = f"install_folder{folder_num}={self._format_ini_value(dest_folder)}"
            self._insert_into_section("[InstallList]", [install_line])

        folder_num = self.folder_numbers[dest_folder]
        folder_section: str = f"[install_folder{folder_num}]"

        # Get file number for this folder (0-indexed)
        if dest_folder not in self.install_folders:
            self.install_folders[dest_folder] = []
        file_index: int = len(self.install_folders[dest_folder])
        self.install_folders[dest_folder].append(filename)

        # Read file to find where to insert
        current_content: str = self.ini_path.read_text(encoding="utf-8")
        lines: list[str] = current_content.splitlines()

        # Find the folder section
        folder_section_idx: int | None = None
        for i, line in enumerate(lines):
            if line == folder_section:
                folder_section_idx = i
                break

        # Create folder section if it doesn't exist (only when first file is added)
        if folder_section_idx is None:
            self._insert_folder_section(folder_num, dest_folder)
            # Re-read to find the section
            current_content = self.ini_path.read_text(encoding="utf-8")
            lines = current_content.splitlines()
            for i, line in enumerate(lines):
                if line == folder_section:
                    folder_section_idx = i
                    break

        if folder_section_idx is None:
            self.log_func(f"[Error] Folder section {folder_section} not found after creation")
            return

        # Find insertion point in folder section (after header and any existing File#= lines)
        insert_idx: int = folder_section_idx + 1
        last_file_idx: int = folder_section_idx

        # Find where existing files end in this section
        for i in range(folder_section_idx + 1, len(lines)):
            line: str = lines[i].strip()
            # Stop at next section marker
            if line.startswith("[") and line.endswith("]") and line != folder_section:
                break
            # Check if this is a File#= line
            if line and not line.startswith(";") and line.startswith("File") and "=" in line:
                last_file_idx = i

        # Insert after the last file entry (or after section header if no files yet)
        insert_idx = last_file_idx + 1
        # Skip trailing blank lines before inserting
        while insert_idx < len(lines):
            line = lines[insert_idx].strip()
            if line.startswith("[") and line.endswith("]"):
                break
            if line and not line.startswith(";"):
                # Found content, insert after it
                insert_idx += 1
                continue
            # Blank line - check if next line is a section marker
            if insert_idx + 1 < len(lines) and lines[insert_idx + 1].strip().startswith("["):
                break
            insert_idx += 1

        # Insert File#=filename line
        file_line = f"File{file_index}={self._format_ini_value(filename)}"
        lines.insert(insert_idx, file_line)

        # Write back
        new_content: str = "\n".join(lines)
        if not new_content.endswith("\n"):
            new_content += "\n"
        self.ini_path.write_text(new_content, encoding="utf-8")
        _log_verbose(f"Added File{file_index}={filename} to {folder_section}")

    def _insert_folder_section(self, folder_num: int, dest_folder: str) -> None:
        """Insert a new [install_folder#] section after [InstallList]."""
        folder_section = f"[install_folder{folder_num}]"
        # Read file
        current_content: str = self.ini_path.read_text(encoding="utf-8")
        lines: list[str] = current_content.splitlines()

        # Find [InstallList] section end (where [2DAList] starts)
        install_list_idx: int | None = None
        twoda_list_idx: int | None = None

        for i, line in enumerate(lines):
            if line == "[InstallList]":
                install_list_idx = i
            elif line == "[2DAList]":
                twoda_list_idx = i
                break

        if install_list_idx is None:
            _log_debug("InstallList section not found, appending to end")
            lines.append("")
            lines.append(folder_section)
            lines.append("")
        else:
            # Insert before [2DAList] or at end if no 2DAList
            insert_idx = twoda_list_idx if twoda_list_idx is not None else len(lines)
            new_lines = ["", folder_section, ""]
            lines[insert_idx:insert_idx] = new_lines

        new_content = "\n".join(lines)
        if not new_content.endswith("\n"):
            new_content += "\n"
        self.ini_path.write_text(new_content, encoding="utf-8")
        _log_verbose(f"Created {folder_section} section")

    def _add_to_install_folder(
        self,
        folder: str,
        filename: str,
    ) -> None:
        """Add file to install folder tracking.

        The InstallList will be written when the INI file is rewritten.
        """
        if folder not in self.install_folders:
            self.install_folders[folder] = []
        if filename not in self.install_folders[folder]:
            self.install_folders[folder].append(filename)

    def add_install_file(
        self,
        folder: str,
        filename: str,
        source_path: Path | None = None,
    ) -> None:
        r"""Add a file to InstallList and copy it to tslpatchdata.

        Args:
            folder: Destination folder (e.g., "Override", "modules\\name.mod")
            filename: Filename to install
            source_path: Optional path to copy file from (can be capsule)
        """
        # Add to tracking
        self._add_to_install_folder(folder, filename)

        # Copy file if source provided
        if source_path is not None:
            # CRITICAL: ALL files go directly in tslpatchdata root, NOT in subdirectories
            # The folder parameter is only used in the INI to tell TSLPatcher where to install
            dest_path: Path = self.tslpatchdata_path / filename

            try:
                # Extract file data (may be from capsule or loose file)
                source_data: bytes | None = self._extract_file_data(source_path, filename)

                if source_data:
                    # Use appropriate io function based on extension
                    file_ext: str = PurePath(filename).suffix.lstrip(".").lower()
                    self._write_resource_with_io(source_data, dest_path, file_ext)
                    _log_verbose(f"Copied install file: {filename} -> {folder}")
                else:
                    self.log_func(f"[Warning] Could not extract data for install file: {filename}")
            except Exception as e:  # noqa: BLE001
                self.log_func(f"[Error] Failed to copy install file {filename}: {e.__class__.__name__}: {e}")
                self.log_func("Full traceback:")
                for line in traceback.format_exc().splitlines():
                    self.log_func(f"  {line}")

    def _extract_file_data(
        self,
        source_path: Path,
        filename: str,
    ) -> bytes | None:
        """Extract file data from source (handles both loose files and capsules).

        Args:
            source_path: Source path (may be a capsule like danm13.mod)
            filename: Filename to extract (if source is capsule)

        Returns:
            File data bytes, or None if extraction failed
        """
        from pykotor.tools.misc import is_capsule_file  # noqa: PLC0415

        # If it's a loose file, just read it
        if source_path.is_file() and not is_capsule_file(source_path.name):
            return source_path.read_bytes()

        # If it's a capsule, extract the resource
        if source_path.is_file() and is_capsule_file(source_path.name):
            try:
                capsule = Capsule(source_path)
                resref: str = PurePath(filename).stem
                res_ext: str = PurePath(filename).suffix.lstrip(".")

                for res in capsule:
                    if res.resname().lower() == resref.lower() and res.restype().extension.lower() == res_ext.lower():
                        return res.data()

                _log_debug(f"Resource {filename} not found in capsule {source_path.name}")
            except Exception as e:  # noqa: BLE001
                self.log_func(f"[Error] Failed to extract from capsule {source_path}: {e.__class__.__name__}: {e}")
                self.log_func("Full traceback:")
                for line in traceback.format_exc().splitlines():
                    self.log_func(f"  {line}")
                return None

            else:
                return None

        return None

    def _write_resource_with_io(
        self,
        data: bytes,
        dest_path: Path,
        file_ext: str,
    ) -> None:
        """Write resource using appropriate io function."""
        try:
            if file_ext.upper() in GFFContent.get_extensions():
                gff_obj = read_gff(data)
                write_gff(gff_obj, dest_path, ResourceType.from_extension(file_ext))
            elif file_ext == "2da":
                twoda_obj = read_2da(data)
                write_2da(twoda_obj, dest_path, ResourceType.TwoDA)
            elif file_ext == "tlk":
                tlk_obj = read_tlk(data)
                write_tlk(tlk_obj, dest_path, ResourceType.TLK)
            elif file_ext == "ssf":
                ssf_obj = read_ssf(data)
                write_ssf(ssf_obj, dest_path, ResourceType.SSF)
            elif file_ext == "lip":
                lip_obj = read_lip(data)
                write_lip(lip_obj, dest_path, ResourceType.LIP)
            else:
                # Binary file
                dest_path.write_bytes(data)
        except Exception as e:  # noqa: BLE001
            self.log_func(f"[Warning] Failed to use io function for {file_ext}, using binary write: {e.__class__.__name__}: {e}")
            self.log_func("Full traceback:")
            for line in traceback.format_exc().splitlines():
                self.log_func(f"  {line}")
            dest_path.write_bytes(data)

    def _insert_into_section(self, section_marker: str, new_lines: list[str]) -> None:
        """Insert content into a specific section of the INI file.

        Args:
            section_marker: The section marker (e.g., "[TLKList]")
            new_lines: Lines to insert into the section
        """
        if not new_lines:
            return

        # Read current file content
        current_content: str = self.ini_path.read_text(encoding="utf-8")
        lines: list[str] = current_content.splitlines()

        # Find the section marker and the next section marker
        section_idx: int | None = None
        next_section_idx: int | None = None

        all_sections = ["[TLKList]", "[InstallList]", "[2DAList]", "[GFFList]", "[CompileList]", "[SSFList]", "[HACKList]"]
        current_section_pos = all_sections.index(section_marker)
        next_section_marker: str | None = all_sections[current_section_pos + 1] if current_section_pos + 1 < len(all_sections) else None

        for i, line in enumerate(lines):
            if line == section_marker:
                section_idx = i
            elif next_section_marker and line == next_section_marker:
                next_section_idx = i
                break

        if section_idx is None:
            _log_debug(f"Section marker {section_marker} not found, appending to end")
            # Fallback: append to end
            content_to_add = "\n".join(new_lines) + "\n"
            with self.ini_path.open("a", encoding="utf-8") as f:
                f.write(content_to_add)
            return

        # Special handling for [InstallList]: skip over [install_folder#] sections
        if section_marker == "[InstallList]":
            # Find the last line in [InstallList] before any [install_folder#] or [2DAList] sections
            insert_idx = section_idx + 1
            last_content_idx = section_idx
            # Find the last actual content line (install_folder#=...) in InstallList
            for i in range(section_idx + 1, len(lines)):
                line = lines[i].strip()
                if line.startswith("[") and line.endswith("]"):
                    # Hit a section marker - stop here
                    if line == "[2DAList]":
                        next_section_idx = i
                    break
                if line and not line.startswith(";") and "=" in line:
                    # This is a content line (install_folder#=...)
                    last_content_idx = i
            # Insert after the last content line, before any [install_folder#] sections
            insert_idx = last_content_idx + 1
            # Remove any trailing blank lines before inserting (but keep section marker spacing)
            # We want no blank lines between install_folder entries
            while insert_idx < len(lines):
                line = lines[insert_idx].strip()
                if line.startswith("[") and line.endswith("]"):
                    break
                if line and not line.startswith(";"):
                    # Found content - insert before it
                    break
                # Skip blank lines or comments
                insert_idx += 1
        elif next_section_idx is not None:
            # Find the last non-empty line in current section (before next section)
            insert_idx = next_section_idx - 1
            # Skip blank lines/comments at end of section
            while insert_idx > section_idx and (lines[insert_idx].strip() == "" or lines[insert_idx].strip().startswith(";")):
                insert_idx -= 1
            # Insert after the last content line
            insert_idx += 1
        else:
            # No next section - append to end of file
            insert_idx = len(lines)

        # Insert new lines
        lines[insert_idx:insert_idx] = new_lines

        # Write back
        new_content = "\n".join(lines)
        if not new_content.endswith("\n"):
            new_content += "\n"
        self.ini_path.write_text(new_content, encoding="utf-8")
        _log_debug(f"Inserted {len(new_lines)} lines into {section_marker}")

    def _write_to_ini(
        self,
        modifications: list[ModificationsTLK | Modifications2DA | ModificationsGFF | ModificationsSSF | ModificationsNCS],
        mod_type: str,
    ) -> None:
        """Rewrite the entire INI file from scratch using all accumulated modifications.

        This prevents duplicate sections by completely regenerating the file each time.
        """
        # Just trigger a full rewrite - the actual work is done in _rewrite_ini_complete
        self._rewrite_ini_complete()

    def _rewrite_ini_complete(self) -> None:
        """Completely rewrite the INI file from all accumulated modifications."""
        serializer = TSLPatcherINISerializer()

        # Build InstallFile list from install_folders tracking
        install_files: list[InstallFile] = []
        for folder, filenames in self.install_folders.items():
            for filename in filenames:
                from pykotor.tslpatcher.mods.install import InstallFile  # noqa: PLC0415

                install_file = InstallFile(
                    filename,
                    destination=folder,
                )
                install_files.append(install_file)

        # Create a ModificationsByType with all accumulated modifications
        modifications_by_type = ModificationsByType(
            tlk=self.all_modifications.tlk,
            install=install_files,
            twoda=self.all_modifications.twoda,
            gff=self.all_modifications.gff,
            ssf=self.all_modifications.ssf,
            ncs=self.all_modifications.ncs,
            nss=[],
        )

        # Generate complete INI content (includes header and settings)
        ini_content = serializer.serialize(
            modifications_by_type,
            include_header=True,
            include_settings=True,
        )

        # Write the entire file from scratch
        self.ini_path.write_text(ini_content, encoding="utf-8")
        _log_debug("Rewrote complete INI file from scratch")

    def finalize(self) -> None:
        """Finalize the INI file.

        All sections are already written incrementally in real-time.
        This method just logs a summary.
        """
        self.log_func(f"\nINI finalized at: {self.ini_path}")
        self.log_func(f"  TLK modifications: {len(self.all_modifications.tlk)}")
        self.log_func(f"  2DA modifications: {len(self.all_modifications.twoda)}")
        self.log_func(f"  GFF modifications: {len(self.all_modifications.gff)}")
        self.log_func(f"  SSF modifications: {len(self.all_modifications.ssf)}")
        self.log_func(f"  NCS modifications: {len(self.all_modifications.ncs)}")
        total_install_files: int = sum(len(files) for files in self.install_folders.values())
        self.log_func(f"  Install files: {total_install_files}")
        self.log_func(f"  Install folders: {len(self.install_folders)}")

    def write_pending_tlk_modifications(self) -> None:
        """Write all pending TLK modifications to INI immediately.

        This ensures the [TLKList] section is complete before StrRef cache building.
        """
        if not self.all_modifications.tlk:
            # [TLKList] header already written at init, nothing to do
            return

        # Write all TLK modifications that haven't been written yet
        for mod_tlk in self.all_modifications.tlk:
            filename = mod_tlk.sourcefile
            if filename not in self.written_sections:
                self._write_tlk_modification(mod_tlk)

        _log_debug(f"Written {len(self.all_modifications.tlk)} TLK modifications to INI")
