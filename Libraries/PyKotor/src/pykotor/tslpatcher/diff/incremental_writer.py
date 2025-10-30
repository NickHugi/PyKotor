#!/usr/bin/env python3
"""Incremental TSLPatcher data writer.

Writes tslpatchdata files and INI sections as diffs are discovered,
rather than batching everything at the end.
"""

from __future__ import annotations

import os
import traceback

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Iterable

from pykotor.extract.capsule import Capsule
from pykotor.resource.formats.gff import GFFContent
from pykotor.resource.formats.gff.gff_auto import read_gff, write_gff
from pykotor.resource.formats.lip.lip_auto import read_lip, write_lip
from pykotor.resource.formats.ssf.ssf_auto import read_ssf, write_ssf
from pykotor.resource.formats.ssf.ssf_data import SSFSound
from pykotor.resource.formats.tlk.tlk_auto import read_tlk, write_tlk
from pykotor.resource.formats.twoda.twoda_auto import read_2da, write_2da
from pykotor.resource.type import ResourceType
from pykotor.tslpatcher.writer import TSLPatcherINISerializer
from utility.common.more_collections import CaseInsensitiveDict
from utility.system.path import PurePath

if TYPE_CHECKING:
    from pykotor.extract.talktable import StrRefReferenceCache
    from pykotor.extract.twoda import TwoDAMemoryReferenceCache
    from pykotor.tslpatcher.mods.gff import ModificationsGFF
    from pykotor.tslpatcher.mods.ncs import ModificationsNCS
    from pykotor.tslpatcher.mods.ssf import ModificationsSSF
    from pykotor.tslpatcher.mods.template import PatcherModifications
    from pykotor.tslpatcher.mods.tlk import ModificationsTLK
    from pykotor.tslpatcher.mods.twoda import Modifications2DA
    from pykotor.tslpatcher.writer import ModificationsByType
    from utility.system.path import Path


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
        from datetime import datetime, timezone  # noqa: PLC0415

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
    ) -> None:
        """Write a modification's resource file and INI section immediately.

        Args:
            modification: The modification object to write
            source_data: Optional source data (vanilla version for patching)
        """
        # Determine modification type and dispatch
        from pykotor.tslpatcher.mods.gff import ModificationsGFF  # noqa: PLC0415
        from pykotor.tslpatcher.mods.ncs import ModificationsNCS  # noqa: PLC0415
        from pykotor.tslpatcher.mods.ssf import ModificationsSSF  # noqa: PLC0415
        from pykotor.tslpatcher.mods.tlk import ModificationsTLK  # noqa: PLC0415
        from pykotor.tslpatcher.mods.twoda import Modifications2DA  # noqa: PLC0415

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
        self._append_to_ini([mod_2da], "2da")
        self.written_sections.add(filename)

        # Track in all_modifications
        self.all_modifications.twoda.append(mod_2da)

        # Create linking patches for modified existing rows
        # Cache selection determined by which installation has the row
        if change_row_targets:
            mod_2da.twoda_change_row_targets = change_row_targets  # type: ignore[attr-defined]
            self._create_2da_linking_patches_for_existing_rows(mod_2da, change_row_targets)

        # Create linking patches for new rows
        # Cache selection determined by which installation has the row
        if add_row_targets:
            mod_2da.twoda_add_row_targets = add_row_targets  # type: ignore[attr-defined]
            self._create_2da_linking_patches_for_new_rows(mod_2da, add_row_targets)

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
                    if isinstance(row_value, RowValueRowIndex):
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

    def _create_2da_linking_patches_for_existing_rows(
        self,
        mod_2da: Modifications2DA,
        link_targets: list[TwoDALinkTarget],
    ) -> None:
        """Create GFF linking patches for existing 2DA rows being modified (ChangeRow2DA).

        When a 2DA row is modified (ChangeRow2DA) and stores its index in 2DAMEMORY#,
        we find all GFF files in the installation that has that row (which others don't)
        and create patches to update those references to use 2DAMEMORY#.

        This ensures that when TSLPatcher applies the patch:
        1. The 2DA row is modified and its index stored in 2DAMEMORY#
        2. All GFF files that referenced the old row value are updated to reference 2DAMEMORY#
        3. At runtime, 2DAMEMORY# resolves to the (potentially changed) row index

        Note: The cache used here should be built from the installation that has the row
        that others don't, since references to that row exist in that installation.
        Cache is selected per (installation_index, 2da_filename) pair.
        """
        if not link_targets:
            return

        from pykotor.tslpatcher.mods.gff import FieldValue2DAMemory, ModificationsGFF, ModifyFieldGFF

        twoda_filename: str = mod_2da.sourcefile  # Use original case, CaseInsensitiveDict handles it

        # Find the cache for this 2DA filename from the installation that has it
        # For ChangeRow2DA, we determine which installation has the row by checking
        # which cache has references for that row_index. A cache that has references
        # was built from the installation that contains that row (and others don't).
        cache: TwoDAMemoryReferenceCache | None = None
        installation_index: int | None = None

        # Check all caches to find which one has references for our target rows
        # The cache with references indicates the installation that has the row
        for install_idx, filename_to_cache in self.twoda_caches.items():
            # CaseInsensitiveDict handles case-insensitive lookup
            # Check for cache with "_all_2das" key (combined cache) or specific 2DA filename
            cache_key = "_all_2das"
            potential_cache: TwoDAMemoryReferenceCache | None = None

            if cache_key in filename_to_cache:
                potential_cache = filename_to_cache[cache_key]
            elif twoda_filename in filename_to_cache:  # Case-insensitive lookup
                potential_cache = filename_to_cache[twoda_filename]

            if potential_cache is None:
                continue

            # Check if this cache has references for any of our target rows
            # If it does, this is the installation that has the row
            for target in link_targets:
                if potential_cache.has_references(twoda_filename.lower(), target.row_index):
                    cache = potential_cache
                    installation_index = install_idx
                    self.log_func(
                        f"  Using cache from install{installation_index} for {twoda_filename} row {target.row_index} "
                        f"(cache has references, indicating this installation contains the row)"
                    )
                    break

            if cache is not None:
                break

        if cache is None:
            return

        for target in link_targets:
            # Query cache for files that reference this 2DA row in the installation that has the row
            # TwoDAMemoryReferenceCache stores keys as lowercase
            references = cache.get_references(twoda_filename.lower(), target.row_index)
            if not references:
                continue

            self.log_func(f"\n[2DAMEMORY] {mod_2da.sourcefile} row {target.row_index} -> token 2DAMEMORY{target.token_id}")
            install_name: str = f"install{installation_index}" if installation_index is not None else "unknown"
            self.log_func(f"  Found {len(references)} file(s) in {install_name} that reference this row")

            for identifier, locations in references:
                filename = f"{identifier.resname}.{identifier.restype.extension}".lower()

                # Check if we already have a GFF modification for this file
                existing_gff_mod: ModificationsGFF | None = next(
                    (m for m in self.all_modifications.gff if m.sourcefile == filename),
                    None,
                )
                is_new_gff_mod: bool = existing_gff_mod is None

                if existing_gff_mod is None:
                    # Create new GFF modification for linking patches
                    existing_gff_mod = ModificationsGFF(filename, replace=False, modifiers=[])
                    self.all_modifications.gff.append(existing_gff_mod)
                    self._write_gff_modification(existing_gff_mod, None)

                new_field_added: bool = False
                added_fields: list[str] = []

                for location in locations:
                    path_str: str = location.replace("/", "\\")

                    # Skip if this field already uses the token
                    if self._gff_has_twoda_token(existing_gff_mod, path_str, target.token_id):
                        continue

                    # Create linking patch: update field to use 2DAMEMORY token
                    modify_field = ModifyFieldGFF(
                        path=path_str,
                        value=FieldValue2DAMemory(target.token_id),
                    )
                    existing_gff_mod.modifiers.append(modify_field)
                    new_field_added = True
                    added_fields.append(path_str)

                if not new_field_added:
                    continue

                # Log the linking patches created
                self.log_func(f"    → {filename}: {', '.join(added_fields)}")

                # If this is a new GFF modification, it's already written
                if is_new_gff_mod:
                    continue

                # Otherwise, re-write the GFF section to append the new modifiers
                if existing_gff_mod.sourcefile in self.written_sections:
                    self.written_sections.discard(existing_gff_mod.sourcefile)
                self._append_to_ini([existing_gff_mod], "gff")
                self.written_sections.add(existing_gff_mod.sourcefile)

    def _create_2da_linking_patches_for_new_rows(
        self,
        mod_2da: Modifications2DA,
        link_targets: list[TwoDALinkTarget],
    ) -> None:
        """Create GFF linking patches for new 2DA rows being added (AddRow2DA).

        When a new 2DA row is added (AddRow2DA) and stores its index in 2DAMEMORY#,
        we should find all GFF files in the installation that has that row and create
        patches to update those references to use 2DAMEMORY#.

        IMPORTANT: This function queries caches which were built from
        the installation that has the row that others don't. This is correct because:
        - New rows (AddRow2DA) only exist in the installation that has them
        - References to these new rows exist ONLY in that installation's files
        - When one installation has a 2DA row that others don't, references are in that installation
        - Cache is selected per (installation_index, 2da_filename) pair

        LIMITATION: Currently this only logs token allocation because:
        1. The actual row index is unknown until patch time (depends on exclusive_column matching)
        2. We don't have easy access to the modded 2DA data here to look up row_index by row_label
        3. The cache indexes by row_index, not row_label

        TODO: Enhance this to:
        - Store modded 2DA data or load it on-demand to look up row_index by row_label
        - Query cache with the correct row_index
        - Generate automatic linking patches for AddRow2DA

        Args:
            mod_2da: The 2DA modifications being applied
            link_targets: List of targets for new rows (with row_label set, row_index=-1)
        """
        if not link_targets:
            return

        twoda_filename: str = mod_2da.sourcefile  # Use original case, CaseInsensitiveDict handles it

        # Find the cache for this 2DA filename from the installation that has it
        # For AddRow2DA, new rows only exist in one installation. We determine which
        # installation has the new row by checking which cache might have references.
        # However, since row_index is unknown until patch time, we need to:
        # 1. Find which installation has the 2DA file with the new row
        # 2. Optionally: Load that 2DA to look up row_index by row_label
        #
        # For now, we check all caches and use the first one found. In the future,
        # we could enhance this to look up row_index by row_label from the installation's 2DA.
        cache: TwoDAMemoryReferenceCache | None = None
        installation_index: int | None = None

        # Try to find a cache that might have references for new rows
        # Since new rows only exist in one installation, any cache for this 2DA filename
        # could potentially have references (if the installation contains files that reference the new row)
        for install_idx, filename_to_cache in self.twoda_caches.items():
            # CaseInsensitiveDict handles case-insensitive lookup
            # Check for cache with "_all_2das" key (combined cache) or specific 2DA filename
            cache_key = "_all_2das"
            if cache_key in filename_to_cache:
                cache = filename_to_cache[cache_key]
                installation_index = install_idx
                break
            if twoda_filename in filename_to_cache:  # Case-insensitive lookup
                cache = filename_to_cache[twoda_filename]
                installation_index = install_idx
                break

        if cache is None:
            # No cache found - new rows might not have references yet, or cache wasn't built
            install_name = "unknown"
            for target in link_targets:
                self.log_func(
                    f"\n[2DAMEMORY] {mod_2da.sourcefile} NEW row '{target.row_label or '(unlabeled)'}' "
                    f"-> token 2DAMEMORY{target.token_id} (no cache found, manual linking may be needed)"
                )
            return

        # For AddRow2DA, automatic linking is complex because:
        # 1. The row_index is unknown until patch time (depends on exclusive_column matching)
        # 2. The cache indexes by row_index, not row_label
        # 3. We don't have easy access to the modded 2DA data here to look up row_index by row_label
        #
        # FUTURE ENHANCEMENT: To enable automatic linking for AddRow2DA:
        # - Store modded 2DA data when modifications are created, OR
        # - Load the 2DA from the installation that has the new row on-demand
        # - Look up row_index by row_label (or exclusive_column match)
        # - Query cache with the correct row_index
        # - Generate linking patches automatically
        #
        # For now: Log that tokens were allocated and which installation's cache was found.
        # Mod authors can manually create GFF patches using these tokens if needed.
        install_name: str = f"install{installation_index}" if installation_index is not None else "unknown"
        for target in link_targets:
            self.log_func(
                f"\n[2DAMEMORY] {mod_2da.sourcefile} NEW row '{target.row_label or '(unlabeled)'}' "
                f"-> token 2DAMEMORY{target.token_id} (row_index unknown until patch time, cache from {install_name})"
            )
            self.log_func(
                "  Note: Row index depends on exclusive_column matching at patch time. "
                "To enable automatic linking, row_index lookup by row_label/exclusive_column is needed."
            )

            # Attempt to find references if we can determine row_index
            # This is a best-effort approach: try to find references by checking if any
            # installation has a 2DA with this row_label that we could look up
            # Since we don't have the 2DA data here, we can't do full lookup, but we log the attempt
            if target.row_label:
                self.log_func(
                    f"  Hint: To find references, load 2DA from {install_name} and look up row_index "
                    f"for label '{target.row_label}', then query cache with that row_index."
                )

    @staticmethod
    def _gff_has_twoda_token(
        mod_gff: ModificationsGFF,
        path: str,
        token_id: int,
    ) -> bool:
        from pykotor.tslpatcher.mods.gff import FieldValue2DAMemory, ModifyFieldGFF

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

                write_gff(gff_obj, output_path, restype)
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
        self._append_to_ini([mod_gff], "gff")
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
        from pykotor.resource.formats.tlk.tlk_data import TLK  # noqa: PLC0415

        appends = [m for m in mod_tlk.modifiers if not m.is_replacement]

        if appends:
            _log_debug(f"Creating append.tlk with {len(appends)} entries")
            append_tlk = TLK()
            append_tlk.resize(len(appends))

            sorted_appends = sorted(appends, key=lambda m: m.token_id)

            for append_idx, modifier in enumerate(sorted_appends):
                text: str = modifier.text if modifier.text else ""
                sound_str: str = str(modifier.sound) if modifier.sound else ""
                append_tlk.replace(append_idx, text, sound_str)

            append_path: Path = self.tslpatchdata_path / "append.tlk"
            write_tlk(append_tlk, append_path, ResourceType.TLK)
            _log_verbose(f"Wrote append.tlk with {len(appends)} entries")

        # Add to install folders
        self._add_to_install_folder(".", "append.tlk")

        # Use StrRef cache to create linking patches IMMEDIATELY
        if self.strref_cache and hasattr(mod_tlk, "strref_mappings"):
            self._create_linking_patches_from_cache(mod_tlk)

        # Write INI section
        self._append_to_ini([mod_tlk], "tlk")
        self.written_sections.add(filename)

        # Track in all_modifications
        self.all_modifications.tlk.append(mod_tlk)

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

        from pykotor.tslpatcher.memory import TokenUsageTLK  # noqa: PLC0415
        from pykotor.tslpatcher.mods.gff import FieldValueConstant, FieldValueTLKMemory, LocalizedStringDelta, ModificationsGFF, ModifyFieldGFF  # noqa: PLC0415
        from pykotor.tslpatcher.mods.ssf import ModificationsSSF, ModifySSF  # noqa: PLC0415
        from pykotor.tslpatcher.mods.twoda import ChangeRow2DA, Modifications2DA, RowValue2DAMemory, Target, TargetType  # noqa: PLC0415

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
                        self._append_to_ini([existing_mod], "2da")
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
                        self._append_to_ini([existing_ssf_mod], "ssf")
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
                        )
                        existing_gff_mod.modifiers.append(modify_field)

                    # Re-write INI section if we added modifiers to existing mod
                    if not is_new_gff_mod and existing_gff_mod.modifiers:
                        self.written_sections.discard(filename)
                        self._append_to_ini([existing_gff_mod], "gff")
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
        self._append_to_ini([mod_ssf], "ssf")
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
        if source_data:
            output_path: Path = self.tslpatchdata_path / filename
            output_path.write_bytes(source_data)
            _log_verbose(f"Wrote NCS file: {filename}")

        # Write INI section
        self._append_to_ini([mod_ncs], "ncs")
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

    def _write_install_entry_to_ini(self, folder: str, filename: str) -> None:
        """Write a single InstallList entry to INI file in real-time."""
        # Normalize folder name
        dest_folder = folder if folder != "." else "Override"

        # Get or assign folder number
        is_new_folder = dest_folder not in self.folder_numbers
        if is_new_folder:
            folder_num = self.next_folder_number
            self.folder_numbers[dest_folder] = folder_num
            self.next_folder_number += 1

            # Add install_folder#=folder line to [InstallList] section
            install_line = f"install_folder{folder_num}={self._format_ini_value(dest_folder)}"
            self._insert_into_section("[InstallList]", [install_line])

        folder_num = self.folder_numbers[dest_folder]
        folder_section = f"[install_folder{folder_num}]"

        # Get file number for this folder (0-indexed)
        if dest_folder not in self.install_folders:
            self.install_folders[dest_folder] = []
        file_index = len(self.install_folders[dest_folder])
        self.install_folders[dest_folder].append(filename)

        # Read file to find where to insert
        current_content = self.ini_path.read_text(encoding="utf-8")
        lines = current_content.splitlines()

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
        insert_idx = folder_section_idx + 1
        last_file_idx = folder_section_idx

        # Find where existing files end in this section
        for i in range(folder_section_idx + 1, len(lines)):
            line = lines[i].strip()
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
        """Add file to install folder tracking and write to InstallList immediately."""
        if folder not in self.install_folders:
            self.install_folders[folder] = []
        if filename not in self.install_folders[folder]:
            self.install_folders[folder].append(filename)
            # Write to InstallList immediately
            self._write_install_entry_to_ini(folder, filename)

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

        all_sections = ["[TLKList]", "[InstallList]", "[2DAList]", "[GFFList]", "[CompileList]", "[SSFList]"]
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

    def _append_to_ini(
        self,
        modifications: list,
        mod_type: str,
    ) -> None:
        """Insert modification sections into the appropriate section of INI file."""
        serializer = TSLPatcherINISerializer()

        # Generate section content based on type
        if mod_type == "2da":
            lines = serializer._serialize_2da_list(modifications)  # noqa: SLF001
            # Skip the [2DAList] header since it was already written at init
            if lines and lines[0] == "[2DAList]":
                lines = lines[1:]
            section_marker = "[2DAList]"
        elif mod_type == "gff":
            lines = serializer._serialize_gff_list(modifications)  # noqa: SLF001
            # Skip the [GFFList] header since it was already written at init
            if lines and lines[0] == "[GFFList]":
                lines = lines[1:]
            section_marker = "[GFFList]"
        elif mod_type == "tlk":
            lines = serializer._serialize_tlk_list(modifications)  # noqa: SLF001
            # Skip the [TLKList] header since it was already written at init
            if lines and lines[0] == "[TLKList]":
                lines = lines[1:]
            section_marker = "[TLKList]"
        elif mod_type == "ssf":
            lines = serializer._serialize_ssf_list(modifications)  # noqa: SLF001
            # Skip the [SSFList] header since it was already written at init
            if lines and lines[0] == "[SSFList]":
                lines = lines[1:]
            section_marker = "[SSFList]"
        elif mod_type == "ncs":
            lines = serializer._serialize_hack_list(modifications)  # noqa: SLF001
            # Skip the [CompileList] header since it was already written at init
            if lines and lines[0] == "[CompileList]":
                lines = lines[1:]
            section_marker = "[CompileList]"
        else:
            _log_debug(f"Unknown modification type for INI: {mod_type}")
            return

        if not lines:
            return

        # Insert into the correct section
        self._insert_into_section(section_marker, lines)
        _log_debug(f"Inserted {mod_type.upper()} content into {section_marker}")

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
