#!/usr/bin/env python3
"""Resource resolution order handling for KotorDiff.

This module provides proper KOTOR resource resolution that matches how the game
actually loads files, respecting the priority order:
1. Override (highest priority - always wins)
2. Modules (.mod files)
3. Modules (.rim/_s.rim/_dlg.erf files)
4. Chitin (BIFs - lowest priority)

When comparing installations, we resolve resources according to this order to
ensure we're comparing what the game actually sees.

CACHE BUILDING PRINCIPLE (for n-way diffs):
-------------------------------------------
When an installation has an entry (2DA row, StrRef, GFF field, SSF entry, TLK entry,
HACK entry, etc.) that doesn't exist in others, references to that entry exist ONLY
in that installation's files. Therefore:
- Build caches from the installation that HAS the entry that others don't
- This applies universally: GFFList, TLKList, SSFList, 2DAList, HACKList, etc.
- For any file type, if one path has an entry others don't, it should result in a patch
"""

from __future__ import annotations

import traceback

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from pykotor.resource.formats.gff.gff_data import GFFContent
from pykotor.tslpatcher.diff.engine import diff_data
from utility.system.path import Path

if TYPE_CHECKING:
    from pykotor.extract.file import FileResource, ResourceIdentifier
    from pykotor.extract.installation import Installation
    from pykotor.extract.talktable import StrRefReferenceCache
    from pykotor.extract.twoda import TwoDAMemoryReferenceCache
    from pykotor.tslpatcher.diff.incremental_writer import IncrementalTSLPatchDataWriter
    from pykotor.tslpatcher.writer import ModificationsByType


@dataclass
class ResolvedResource:
    """A resource resolved through the game's priority order."""

    identifier: ResourceIdentifier
    data: bytes | None
    source_location: str  # Human-readable description of where it was found
    location_type: str | None  # Type of location (Override, Modules, Chitin, etc.)
    filepath: Path | None  # Full path to the file containing this resource
    all_locations: dict[str, list[Path]] | None = None  # All locations where resource was found


def get_location_display_name(location_type: str | None) -> str:
    """Get human-readable name for a location type."""
    if location_type is None:
        return "Not Found"

    # Already a string, just return it
    return location_type


def resolve_resource_in_installation(
    installation: Installation,
    identifier: ResourceIdentifier,
    *,
    log_func: Callable | None = None,
    verbose: bool = True,  # noqa: ARG001
    resource_index: dict[ResourceIdentifier, list[FileResource]] | None = None,
) -> ResolvedResource:
    """Resolve a resource in an installation using game priority order.

    Resolution order (ONLY applies to Override/Modules/Chitin):
    1. Override folder (highest priority)
    2. Modules (.mod files)
    3. Modules (.rim/_s.rim/_dlg.erf files - composite loading)
    4. Chitin BIFs (lowest priority)

    Note: StreamWaves/StreamVoice/etc are diffed but do NOT participate in resolution order.

    Args:
        installation: The Installation to search in
        identifier: Resource identifier (resname + restype)
        log_func: Optional logging function
        verbose: If True, log detailed search process (ignored - logging now handled externally)
        resource_index: Optional pre-built index for O(1) lookups (massive performance gain)

    Returns:
        ResolvedResource with data and source location info
    """
    if log_func is None:
        log_func = lambda _: None  # noqa: E731

    # Find all instances of this resource across the installation
    override_files: list[Path] = []
    module_mod_files: list[Path] = []
    module_rim_files: list[Path] = []
    chitin_files: list[Path] = []

    # Store FileResource instances for data retrieval
    resource_instances: dict[Path, FileResource] = {}

    try:
        # Use index if provided (O(1) lookup), otherwise iterate (O(n) scan)
        if resource_index is not None:
            file_resources = resource_index.get(identifier, [])
        else:
            # Fallback to iteration if no index provided
            file_resources = [fr for fr in installation if fr.identifier() == identifier]

        # Categorize all instances by location
        install_root: Path = installation.path()
        for file_resource in file_resources:
            filepath = file_resource.filepath()
            parent_names_lower = [parent.name.lower() for parent in filepath.parents]

            # Store for data retrieval later
            resource_instances[filepath] = file_resource

            # Categorize by location (ONLY resolution-order locations)
            if "override" in parent_names_lower:
                override_files.append(filepath)
            elif "modules" in parent_names_lower:
                # Distinguish .mod from .rim files
                if filepath.suffix.lower() == ".mod":
                    module_mod_files.append(filepath)
                elif filepath.suffix.lower() in (".rim", ".erf"):
                    module_rim_files.append(filepath)
                else:
                    module_rim_files.append(filepath)  # Default to rim category
            elif "data" in parent_names_lower or filepath.suffix.lower() == ".bif":
                chitin_files.append(filepath)
            elif filepath.parent == install_root:
                # Files directly in installation root (like dialog.tlk, chitin.key, etc.)
                # Treat as Override priority since they're loose files at root level
                override_files.append(filepath)
            # StreamWaves/etc in subdirectories are NOT added - they don't participate in resolution

        # Apply resolution order: Override > .mod > .rim > Chitin
        chosen_filepath: Path | None = None
        location_type: str | None = None

        if override_files:
            chosen_filepath = override_files[0]
            # Check if it's actually in Override folder or root
            if "override" in [parent.name.lower() for parent in chosen_filepath.parents]:
                location_type = "Override folder"
            else:
                location_type = "Installation root"
        elif module_mod_files:
            chosen_filepath = module_mod_files[0]
            location_type = "Modules (.mod)"
        elif module_rim_files:
            # Use first .rim file found (composite loading handled elsewhere)
            chosen_filepath = module_rim_files[0]
            location_type = "Modules (.rim)"
        elif chitin_files:
            chosen_filepath = chitin_files[0]
            location_type = "Chitin BIFs"

        if not chosen_filepath:
            return ResolvedResource(
                identifier=identifier,
                data=None,
                source_location="Not found in installation",
                location_type=None,
                filepath=None,
                all_locations=None,
            )

        # Read the data from the chosen location (O(1) lookup with stored instances)
        data: bytes | None = None
        file_resource = resource_instances.get(chosen_filepath)
        if file_resource is not None:
            data = file_resource.data()

        if data is None:
            return ResolvedResource(
                identifier=identifier,
                data=None,
                source_location=f"Found but couldn't read: {chosen_filepath}",
                location_type=location_type,
                filepath=chosen_filepath,
                all_locations=None,
            )

        # Create human-readable source description
        try:
            rel_path = chosen_filepath.relative_to(installation.path())
            source_desc = f"{location_type}: {rel_path}"
        except ValueError:
            source_desc = f"{location_type}: {chosen_filepath}"

        # Store all found locations for combined logging
        all_locs: dict[str, list[Path]] = {
            "Override folder": override_files,
            "Modules (.mod)": module_mod_files,
            "Modules (.rim/.erf)": module_rim_files,
            "Chitin BIFs": chitin_files,
        }

        return ResolvedResource(
            identifier=identifier,
            data=data,
            source_location=source_desc,
            location_type=location_type,
            filepath=chosen_filepath,
            all_locations=all_locs,
        )

    except Exception as e:  # noqa: BLE001
        log_func(f"[Error] Failed to resolve {identifier}: {e.__class__.__name__}: {e}")
        log_func("Full traceback:")
        for line in traceback.format_exc().splitlines():
            log_func(f"  {line}")

        return ResolvedResource(
            identifier=identifier,
            data=None,
            source_location=f"Error: {e.__class__.__name__}: {e}",
            location_type=None,
            filepath=None,
            all_locations=None,
        )


def _log_consolidated_resolution(  # noqa: PLR0913
    install1: Installation,
    install2: Installation,
    identifier: ResourceIdentifier,  # noqa: ARG001
    resolved1: ResolvedResource,
    resolved2: ResolvedResource,
    log_func: Callable[[str], None],
) -> None:
    """Log combined resolution results from two installations side-by-side.

    Shows which files were CHOSEN by resolution order and which were shadowed.

    Args:
        install1: Installation 1 (vanilla/base)
        install2: Installation 2 (modded/target)
        identifier: Resource identifier being resolved
        resolved1: Resolution result from installation 1
        resolved2: Resolution result from installation 2
        log_func: Logging function
    """
    install1_name = install1.path().name
    install2_name = install2.path().name

    log_func(f"Installation 1 ({install1_name}), 2 ({install2_name})")
    log_func("  Checking each location:")

    # Get all locations from both installations
    all_locs1 = resolved1.all_locations or {}
    all_locs2 = resolved2.all_locations or {}

    # Priority order for display
    location_order = [
        ("Override folder", "1. Override folder"),
        ("Modules (.mod)", "2. Modules (.mod)"),
        ("Modules (.rim/.erf)", "3. Modules (.rim/.erf)"),
        ("Chitin BIFs", "4. Chitin BIFs"),
    ]

    for loc_key, loc_display in location_order:
        files1 = all_locs1.get(loc_key, [])
        files2 = all_locs2.get(loc_key, [])

        # Show all files from both installations
        all_files_to_show: list[tuple[str, Path, bool]] = []  # (install_name, filepath, is_chosen)

        for f in files1:
            is_chosen = (resolved1.filepath == f)
            all_files_to_show.append((install1_name, f, is_chosen))

        for f in files2:
            is_chosen = (resolved2.filepath == f)
            all_files_to_show.append((install2_name, f, is_chosen))

        if not all_files_to_show:
            log_func(f"    {loc_display} -> not found")
        else:
            for install_name, filepath, is_chosen in all_files_to_show:
                try:  # noqa: PERF203
                    if install_name == install1_name:
                        rel_path = filepath.relative_to(install1.path())
                    else:
                        rel_path = filepath.relative_to(install2.path())

                    full_path = f"{install_name}/{rel_path}"

                    if is_chosen:
                        log_func(f"    {loc_display} -> CHOSEN - {full_path}")
                    else:
                        log_func(f"    {loc_display} -> (shadowed) {full_path}")
                except ValueError:
                    # Couldn't get relative path, just show filename
                    if is_chosen:
                        log_func(f"    {loc_display} -> CHOSEN - {filepath.name}")
                    else:
                        log_func(f"    {loc_display} -> (shadowed) {filepath.name}")


def collect_all_resource_identifiers(installation: Installation) -> set[ResourceIdentifier]:
    """Collect all unique resource identifiers from an installation.

    Args:
        installation: The Installation to scan

    Returns:
        Set of all ResourceIdentifiers found
    """
    identifiers: set[ResourceIdentifier] = set()

    # Iterate through all resources
    for file_resource in installation:
        identifiers.add(file_resource.identifier())

    return identifiers


def build_resource_index(installation: Installation) -> dict[ResourceIdentifier, list[FileResource]]:
    """Build an index mapping ResourceIdentifier to all FileResource instances.

    This dramatically improves performance by avoiding O(n) scans for each resource.

    Args:
        installation: The Installation to index

    Returns:
        Dictionary mapping ResourceIdentifier to list of FileResource instances
    """
    from collections import defaultdict  # noqa: PLC0415

    index: dict[ResourceIdentifier, list[FileResource]] = defaultdict(list)

    for file_resource in installation:
        index[file_resource.identifier()].append(file_resource)

    return dict(index)


def _build_strref_cache(
    installation: Installation,
    strref_cache: StrRefReferenceCache,
    log_func: Callable[[str], None],
) -> None:
    """Build StrRef reference cache by scanning all resources in installation.

    IMPORTANT: StrRef cache should be built from the installation that HAS the StrRef
    that others don't. This is because references to a StrRef exist only in the
    installation that contains that StrRef.

    For n-way diffs:
    - If a StrRef exists in installation A but not in others, references to it exist
      in installation A's files, so build cache from installation A.
    - When an installation has a StrRef that others don't, references to that StrRef
      exist ONLY in that installation's files.

    Args:
        installation: Installation to scan (the one containing StrRefs that others don't)
        strref_cache: Cache to populate
        log_func: Logging function
    """
    scanned_count: int = 0
    cached_count: int = 0

    for file_resource in installation:
        scanned_count += 1

        if scanned_count % 1000 == 0:
            log_func(f"  Scanned {scanned_count} resources...")

        try:
            data: bytes = file_resource.data()
            strref_cache.scan_resource(file_resource, data)
            cached_count += 1
        except Exception:  # noqa: BLE001
            log_func(f"  Failed to scan resource: {file_resource.identifier()}")
            log_func(traceback.format_exc())
            continue

    log_func(f"  Scanned {scanned_count} resources, cached {cached_count} for StrRef analysis")

    # Log cache summary
    strref_cache.log_summary()


def _build_twoda_cache(
    installation: Installation,
    twoda_cache: TwoDAMemoryReferenceCache,
    log_func: Callable[[str], None],
) -> None:
    """Build 2DA memory reference cache by scanning all resources in installation.

    Finds all GFF files that reference 2DA rows (e.g., Appearance_Type, SoundSetFile, etc.)
    so we can create linking patches when those rows are modified.

    IMPORTANT: 2DA cache should be built from the installation that HAS the 2DA row
    that others don't. References to a 2DA row exist only in the installation that
    contains that row.

    For n-way diffs:
    - For ChangeRow2DA (existing rows being modified): Build cache from installation
      that has the row which others don't (references to existing rows exist in that installation).
    - For AddRow2DA (new rows being added): Build cache from installation that has
      the new row (references to new rows exist ONLY in that installation).
    - When an installation has a 2DA row that others don't, references to that row
      exist in that installation's files.

    Args:
        installation: Installation to scan (the one containing 2DA rows that others don't)
        twoda_cache: Cache to populate
        log_func: Logging function
    """
    scanned_count: int = 0
    cached_count: int = 0

    for file_resource in installation:
        scanned_count += 1

        if scanned_count % 1000 == 0:
            log_func(f"  Scanned {scanned_count} resources for 2DA references...")

        try:
            data: bytes = file_resource.data()
            twoda_cache.scan_resource(file_resource, data)
            cached_count += 1
        except Exception:  # noqa: BLE001
            log_func(f"  Failed to scan resource for 2DA references: {file_resource.identifier()}")
            log_func(traceback.format_exc())
            continue

    log_func(f"  Scanned {scanned_count} resources, cached {cached_count} for 2DA reference analysis")

    # Log cache summary
    twoda_cache.log_summary()


def _should_process_tlk_file(resolved2: ResolvedResource) -> bool:
    """Determine if a TLK file should be processed based on filtering rules.

    When both comparison paths are installations, only process TLK files that are:
    - In the root of the installation folder, AND
    - Named 'dialog.tlk' or 'dialog_f.tlk'

    This filters out backup copies, test files, and other irrelevant TLK files.

    Args:
        resolved2: Resolved resource from the second installation

    Returns:
        True if the TLK file should be processed, False otherwise
    """
    # Always process if we don't have filepath info
    if not resolved2.filepath:
        return True

    # Check location type - only process TLKs from Installation root or Override
    if resolved2.location_type not in ("Installation root", "Override folder"):
        return False

    # Check filename - only allow dialog.tlk and dialog_f.tlk
    filename = resolved2.filepath.name.lower()
    return filename in ("dialog.tlk", "dialog_f.tlk")


def determine_tslpatcher_destination(
    vanilla_location: str | None,  # noqa: ARG001
    modded_location: str | None,
    modded_filepath: Path | None,
) -> str:
    r"""Determine the appropriate TSLPatcher destination based on source locations.

    Args:
        vanilla_location: Location type where resource was found in vanilla (unused - reserved for future)
        modded_location: Location type where resource was found in modded installation
        modded_filepath: Full path to the modded resource file

    Returns:
        Destination string for TSLPatcher (e.g., "Override", "modules\\danm13.mod")
    """
    # If resource is in Override in modded installation, destination is Override
    if modded_location == "Override folder":
        return "Override"

    # If resource is in a module in modded installation
    if modded_location and "Modules" in modded_location and modded_filepath:
        filepath_str = str(modded_filepath).lower()

        # Check if it's in a .mod file
        if ".mod" in filepath_str or ".erf" in filepath_str:
            # Extract module filename
            module_name = modded_filepath.name
            return f"modules\\{module_name}"

        # It's in a .rim - need to redirect to corresponding .mod
        if ".rim" in filepath_str:
            from pykotor.tslpatcher.diff.engine import get_module_root  # noqa: PLC0415
            module_root = get_module_root(modded_filepath)
            return f"modules\\{module_root}.mod"

    # Default to Override for safety
    return "Override"


def diff_installations_with_resolution(  # noqa: PLR0913
    install1: Installation,
    install2: Installation,
    *,
    filters: list[str] | None = None,
    log_func: Callable[[str], None],
    compare_hashes: bool = True,
    modifications_by_type: ModificationsByType | None = None,
    incremental_writer: IncrementalTSLPatchDataWriter | None = None,
) -> bool | None:
    """Compare two installations using proper resource resolution order.

    This function respects the game's actual file priority:
    - Override (highest)
    - Modules (.mod)
    - Modules (.rim/_s.rim/_dlg.erf)
    - Chitin/BIFs (lowest)

    InstallList Logic (2-way comparison):
    - File exists in install2 but NOT in install1 → [InstallList] (new file to install)
    - File exists in both → [GFFList]/[2DAList]/etc (patch existing file)
    - File exists in install1 but NOT in install2 → Removed (no action)

    Args:
        install1: First installation (vanilla/base - corresponds to --mine)
        install2: Second installation (modded/target - corresponds to --older)
        filters: Optional list of resource name filters
        log_func: Logging function
        compare_hashes: Whether to compare hashes for binary files
        modifications_by_type: Optional collection for TSLPatcher modifications
        incremental_writer: Optional incremental writer for immediate file/INI writes

    Returns:
        True if identical, False if different, None if errors occurred
    """
    from pykotor.tslpatcher.diff.engine import DiffContext, Path as EnginePath, _add_to_install_folder

    log_func("")
    log_func("=" * 80)
    log_func("RESOURCE-AWARE INSTALLATION COMPARISON")
    log_func("=" * 80)
    log_func(f"Install 1 (older/vanilla): {install1.path()}")
    log_func(f"Install 2 (mine/modded):   {install2.path()}")
    log_func("")
    log_func("Using KOTOR resource resolution order (highest to lowest priority):")
    log_func("  1. Override")
    log_func("  2. Modules (.mod)")
    log_func("  3. Modules (.rim/_s.rim/_dlg.erf)")
    log_func("  4. Chitin (BIFs)")
    log_func("=" * 80)
    log_func("")

    # Build resource indices for O(1) lookups (massive performance improvement)
    log_func("Building resource indices for fast lookups...")
    index1 = build_resource_index(install1)
    index2 = build_resource_index(install2)
    log_func(f"  Install 1: {len(index1)} unique resources indexed")
    log_func(f"  Install 2: {len(index2)} unique resources indexed")

    all_identifiers_set: set[ResourceIdentifier] = set(index1.keys()) | set(index2.keys())
    all_identifiers = list(all_identifiers_set)
    log_func(f"  Total unique resources: {len(all_identifiers)}")
    log_func("  Index build complete - ready for O(1) lookups")
    log_func("")

    # PROCESS TLK FILES FIRST AND IMMEDIATELY (before StrRef cache building)
    # TLKList must come immediately after [Settings] per TSLPatcher design
    log_func("Processing TLK files first for immediate TLKList generation...")
    log_func("")

    tlk_identifiers: list[ResourceIdentifier] = [ident for ident in all_identifiers if ident.restype.extension.lower() == "tlk"]
    filtered_tlk_identifiers: list[ResourceIdentifier] = []
    if tlk_identifiers:
        log_func(f"Found {len(tlk_identifiers)} TLK file(s) to process first")

        # Apply filtering for irrelevant TLK files when both paths are installations
        for identifier in tlk_identifiers:
            # Resolve in install2 to check filepath for filtering
            resolved2 = resolve_resource_in_installation(install2, identifier, log_func=log_func, verbose=False, resource_index=index2)

            if _should_process_tlk_file(resolved2):
                filtered_tlk_identifiers.append(identifier)
                log_func(f"  Processing TLK: {identifier.resname}.{identifier.restype.extension}")
            else:
                log_func(f"  Skipping irrelevant TLK: {identifier.resname}.{identifier.restype.extension} (not dialog.tlk/dialog_f.tlk in root)")

    # Process filtered TLK files
    if filtered_tlk_identifiers:
        for identifier in filtered_tlk_identifiers:
            # Resolve in both installations using indices (O(1) lookups)
            resolved1 = resolve_resource_in_installation(install1, identifier, log_func=log_func, verbose=False, resource_index=index1)
            resolved2 = resolve_resource_in_installation(install2, identifier, log_func=log_func, verbose=False, resource_index=index2)

            # Check if resource exists in both
            if resolved1.data is None and resolved2.data is None:
                log_func(f"    TLK {identifier.resname} missing in both installations, skipping")
                continue

            if resolved1.data is None:
                # Only in install2 (new resource) - add to [InstallList] and create patch
                log_func(f"    TLK {identifier.resname} only in modded installation - adding to InstallList")
                destination = determine_tslpatcher_destination(None, resolved2.location_type, resolved2.filepath)
                filename = f"{identifier.resname}.{identifier.restype.extension}"
                if modifications_by_type is not None:
                    # Create context for patch creation
                    file1_rel = EnginePath("vanilla") / filename  # Vanilla (missing)
                    file2_rel = EnginePath("modded") / filename  # Modded (exists)
                    context = DiffContext(file1_rel, file2_rel, identifier.restype.extension.lower(), skip_nss=False)
                    _add_to_install_folder(
                        modifications_by_type,
                        destination,
                        filename,
                        log_func=log_func,
                        modded_data=resolved2.data,
                        modded_path=resolved2.filepath,
                        context=context,
                        incremental_writer=incremental_writer,
                    )
                if incremental_writer is not None:
                    incremental_writer.add_install_file(destination, filename, resolved2.filepath)
                continue

            if resolved2.data is None:
                # Only in install1 (removed resource) - no action needed
                log_func(f"    TLK {identifier.resname} only in vanilla installation - no action needed")
                continue

            # Both exist - compare them using proper format-aware comparison
            log_func(f"    Comparing TLK {identifier.resname} between installations")
            ctx = DiffContext(
                file1_rel=Path(install1.path().name) / resolved1.filepath.name if resolved1.filepath else Path(install1.path().name) / "unknown",
                file2_rel=Path(install2.path().name) / resolved2.filepath.name if resolved2.filepath else Path(install2.path().name) / "unknown",
                ext=identifier.restype.extension.lower(),
                resname=identifier.resname,
                skip_nss=False,
                file1_location_type=resolved1.location_type,
                file2_location_type=resolved2.location_type,
                file2_filepath=resolved2.filepath,
            )

            # Create a temporary log buffer to capture diff_data output
            tlk_diff_output_lines: list[str] = []
            def tlk_buffered_log_func(
                msg: str,
                *,
                separator: bool = False,  # noqa: ARG001
                separator_above: bool = False,  # noqa: ARG001
                _buffer: list[str] = tlk_diff_output_lines,
            ) -> None:  # noqa: ARG001
                _buffer.append(msg)

            result = diff_data(
                resolved1.data,
                resolved2.data,
                ctx,
                log_func=tlk_buffered_log_func,
                compare_hashes=compare_hashes,
                modifications_by_type=modifications_by_type,
                incremental_writer=incremental_writer,
            )

            # Output the buffered diff results
            for line in tlk_diff_output_lines:
                log_func(line)

    # Remove TLK identifiers from the main list since we've processed them
    all_identifiers = [ident for ident in all_identifiers if ident.restype.extension.lower() != "tlk"]
    log_func("TLK processing complete.")
    log_func("")

    # Ensure complete [TLKList] section is written before StrRef cache building
    if incremental_writer is not None:
        incremental_writer.write_pending_tlk_modifications()
        log_func("Full [TLKList] section written before StrRef cache building.")
        log_func("")

    # Sort remaining identifiers to process 2DA before GFF (TSLPatcher-compliant order)
    # Order: InstallList entries (handled in main loop), then 2DA, then GFF, then NCS, then SSF, then others
    def get_processing_priority(identifier: ResourceIdentifier) -> int:
        """Get processing priority (lower = processed first)."""
        ext: str = identifier.restype.extension.lower()
        if ext in ("2da", "twoda"):
            return 0
        if ext in GFFContent.get_extensions():
            return 1
        if ext == "ncs":
            return 2
        if ext == "ssf":
            return 3
        return 4  # Other types (handled as InstallList)

    # Sort by priority, then by identifier
    all_identifiers: list[ResourceIdentifier] = sorted(all_identifiers, key=lambda x: (get_processing_priority(x), str(x)))
    log_func("Sorted resources for processing: 2DA -> GFF -> NCS -> SSF -> Others")
    log_func("")

    # Build StrRef reference cache by scanning all resources (skip if already loaded from cache)
    if incremental_writer and incremental_writer.strref_cache:
        # Check if cache already has data (from loading)
        stats: dict[str, int] = incremental_writer.strref_cache.get_statistics()
        if stats["unique_strrefs"] > 0:
            log_func(f"Using cached StrRef reference data ({stats['unique_strrefs']} StrRefs, {stats['total_references']} references)")
            log_func("")
        else:
            log_func("Building StrRef reference cache...")
            _build_strref_cache(install2, incremental_writer.strref_cache, log_func)
            log_func("StrRef cache built.")
            log_func("")

    # Build 2DA memory reference caches by scanning installations
    # Structure: {installation_index: {2da_filename: TwoDAMemoryReferenceCache}}
    # For 2-way diff: Build caches for install1 (index 0) and install2 (index 1)
    # For n-way: Build cache from whichever installation has the row that others don't
    # Each 2DA filename gets its own cache per installation
    if incremental_writer and incremental_writer.twoda_caches:
        from pykotor.extract.twoda import TwoDAMemoryReferenceCache  # noqa: PLC0415

        # Determine game for cache creation
        game = install1.game() if hasattr(install1, "game") and callable(getattr(install1, "game", None)) else None
        if game is None:
            game = install2.game() if hasattr(install2, "game") and callable(getattr(install2, "game", None)) else None

        from utility.common.more_collections import CaseInsensitiveDict  # noqa: PLC0415

        # Build caches for each installation and each 2DA filename
        for install_idx, installation in enumerate([install1, install2]):
            if install_idx not in incremental_writer.twoda_caches:
                incremental_writer.twoda_caches[install_idx] = CaseInsensitiveDict()

            # Build a single cache that handles all 2DAs for this installation
            # (TwoDAMemoryReferenceCache already handles multiple 2DAs internally)
            if game is not None:
                # Check if we already have a combined cache (we can use one cache per installation for now)
                # Later we could split per 2DA filename if needed, but the cache already indexes by filename
                cache_key = "_all_2das"  # Single cache per installation that handles all 2DAs
                if cache_key not in incremental_writer.twoda_caches[install_idx]:
                    incremental_writer.twoda_caches[install_idx][cache_key] = TwoDAMemoryReferenceCache(game)

                cache = incremental_writer.twoda_caches[install_idx][cache_key]
                cache_stats: dict[str, int] = cache.get_statistics()
                if cache_stats["unique_2da_refs"] > 0:
                    log_func(
                        f"Using cached 2DA reference data (install{install_idx}) "
                        f"({cache_stats['unique_2da_refs']} row refs, {cache_stats['total_references']} references)"
                    )
                    log_func("")
                else:
                    log_func(f"Building 2DA reference cache from install{install_idx}...")
                    _build_twoda_cache(installation, cache, log_func)
                    log_func(f"2DA reference cache (install{install_idx}) built.")
                    log_func("")

    # Apply filters if provided
    if filters:
        filtered_identifiers_set: set[ResourceIdentifier] = set()
        for ident in all_identifiers:
            resource_name = f"{ident.resname}.{ident.restype.extension}".lower()
            for filter_pattern in filters:
                if filter_pattern.lower() in resource_name:
                    filtered_identifiers_set.add(ident)
                    break
        log_func(f"Applied filters: {filters}")
        log_func(f"  Filtered to {len(filtered_identifiers_set)} resources")
        all_identifiers = list(filtered_identifiers_set)
        log_func("")

    # Compare each resource
    is_same_result: bool | None = True
    processed_count: int = 0
    diff_count: int = 0
    error_count: int = 0
    identical_count: int = 0

    log_func(f"Comparing {len(all_identifiers)} resources using resolution order...")
    log_func("")

    # Compare each resource
    for identifier in all_identifiers:
        processed_count += 1

        # Progress update every 100 resources
        if processed_count % 100 == 0:
            log_func(f"Progress: {processed_count}/{len(all_identifiers)} resources processed...")

        # Resolve in both installations using indices (O(1) lookups instead of O(n) scans)
        resolved1: ResolvedResource = resolve_resource_in_installation(install1, identifier, log_func=log_func, verbose=False, resource_index=index1)
        resolved2: ResolvedResource = resolve_resource_in_installation(install2, identifier, log_func=log_func, verbose=False, resource_index=index2)

        # Check if resource exists in both
        if resolved1.data is None and resolved2.data is None:
            # Both missing - this shouldn't happen but handle it
            continue

        if resolved1.data is None:
            # Only in install2 (new resource) - add to [InstallList] and create patch
            log_func(f"\nProcessing resource: {identifier.resname}.{identifier.restype.extension}")

            # Re-resolve with verbose logging to show where it was found
            log_func("Installation 2 (modded/target):")
            resolve_resource_in_installation(install2, identifier, log_func=log_func, verbose=True)

            log_func(f"\n[NEW RESOURCE] {identifier}")
            log_func(f"  Source (install2/target): {resolved2.source_location}")
            log_func("  Missing from install1 (vanilla/base)")

            # Add to InstallList with correct destination based on resolution order
            # Also create patch modifications
            if modifications_by_type is not None:
                from pykotor.tslpatcher.diff.engine import DiffContext, _add_to_install_folder  # noqa: PLC0415

                # Determine destination based on where it was found in modded installation
                destination: str = determine_tslpatcher_destination(
                    None,  # Not in vanilla
                    resolved2.location_type,
                    resolved2.filepath,
                )
                filename = f"{identifier.resname}.{identifier.restype.extension}"

                # Create context for patch creation
                file1_rel = Path("vanilla") / filename  # Vanilla (missing)
                file2_rel = Path("modded") / filename  # Modded (exists)
                context = DiffContext(file1_rel, file2_rel, identifier.restype.extension.lower(), skip_nss=False)

                _add_to_install_folder(
                    modifications_by_type,
                    destination,
                    filename,
                    log_func=log_func,
                    modded_data=resolved2.data,
                    modded_path=resolved2.filepath,
                    context=context,
                    incremental_writer=incremental_writer,
                )
                log_func(f"  → [InstallList] destination: {destination}")
                log_func("  → File will be INSTALLED, then PATCHED")
                # Write immediately if using incremental writer
                if incremental_writer is not None:
                    # Get the source file from modded installation
                    source_path: Path | None = resolved2.filepath
                    incremental_writer.add_install_file(destination, filename, source_path)

            diff_count += 1
            is_same_result = False
            continue

        if resolved2.data is None:
            # Only in install1 (removed resource) - file was removed in target installation
            # Per TSLPatcher design: removals are NOT handled (no UninstallList)
            log_func(f"\nProcessing resource: {identifier.resname}.{identifier.restype.extension}")

            # Re-resolve with verbose logging to show where it was found
            log_func("Installation 1 (vanilla/base):")
            resolve_resource_in_installation(install1, identifier, log_func=log_func, verbose=True)

            log_func(f"\n[REMOVED RESOURCE] {identifier}")
            log_func(f"  Source (install1/base): {resolved1.source_location}")
            log_func("  Missing from install2 (modded/target)")
            log_func("  → No TSLPatcher action (TSLPatcher cannot remove files)")
            diff_count += 1
            is_same_result = False
            continue

        # Both exist - check if both are from BIFs (read-only, skip comparison)
        both_from_bif: bool = (
            resolved1.location_type == "Chitin BIFs"
            and resolved2.location_type == "Chitin BIFs"
        )
        if both_from_bif:
            # Both from read-only BIFs - skip comparison (can't be patched anyway)
            identical_count += 1
            continue

        # Compare them using proper format-aware comparison
        # Build paths with installation name prefix for proper 'where' display
        install1_name: str = install1.path().name
        install2_name: str = install2.path().name

        # Build full context path: install_name/relative_path_to_container
        if resolved1.filepath:
            try:
                rel1 = resolved1.filepath.relative_to(install1.path())
                file1_path = Path(install1_name) / rel1
            except ValueError:
                file1_path = Path(install1_name) / resolved1.filepath.name
        else:
            file1_path = Path(install1_name) / "unknown"

        if resolved2.filepath:
            try:
                rel2 = resolved2.filepath.relative_to(install2.path())
                file2_path = Path(install2_name) / rel2
            except ValueError:
                file2_path = Path(install2_name) / resolved2.filepath.name
        else:
            file2_path = Path(install2_name) / "unknown"

        ctx = DiffContext(
            file1_rel=file1_path,
            file2_rel=file2_path,
            ext=identifier.restype.extension.lower(),
            resname=identifier.resname,  # Pass resname so 'where' property works correctly
            skip_nss=False,  # Don't skip NSS in detailed comparisons
            # Pass resolution information so destination is set correctly from the start
            file1_location_type=resolved1.location_type,
            file2_location_type=resolved2.location_type,
            file2_filepath=resolved2.filepath,
        )

        # Store original modifications count to detect if diff_data added any
        original_mod_count = 0
        if modifications_by_type is not None:
            original_mod_count = (
                len(modifications_by_type.gff) +
                len(modifications_by_type.twoda) +
                len(modifications_by_type.ssf) +
                len(modifications_by_type.tlk) +
                len(modifications_by_type.ncs)
            )

        # Create a temporary log buffer to capture diff_data output
        diff_output_lines: list[str] = []

        def buffered_log_func(
            msg: str,
            *,
            separator: bool = False,  # noqa: ARG001
            separator_above: bool = False,  # noqa: ARG001
            _buffer: list[str] = diff_output_lines,
        ) -> None:  # noqa: ARG001
            """Capture log output during diff_data call."""
            _buffer.append(msg)

        result = diff_data(
            resolved1.data,
            resolved2.data,
            ctx,
            log_func=buffered_log_func,
            compare_hashes=compare_hashes,
            modifications_by_type=modifications_by_type,
            incremental_writer=incremental_writer,
        )

        if result is False:
            # Resources differ - NOW show consolidated resolution logging BEFORE replaying diff output
            log_func(f"\nProcessing resource: {identifier.resname}.{identifier.restype.extension}")

            # Show consolidated resolution for both installations
            _log_consolidated_resolution(
                install1,
                install2,
                identifier,
                resolved1,
                resolved2,
                log_func,
            )

            # Now replay the diff output
            for line in diff_output_lines:
                log_func(line)

            # Add summary
            diff_count += 1
            log_func(f"\n[MODIFIED] {identifier}")
            log_func(f"  Install1 source (vanilla/base): {resolved1.source_location}")
            log_func(f"  Install2 source (modded/target): {resolved2.source_location}")

            # Log priority explanation if sources are different
            if resolved1.location_type != resolved2.location_type:
                priority1 = get_location_display_name(resolved1.location_type)
                priority2 = get_location_display_name(resolved2.location_type)
                log_func(f"  Priority changed: {priority1} → {priority2}")

                if resolved2.location_type == "Override folder":
                    log_func(f"  → Resource moved to Override (will override vanilla {priority1})")
                elif resolved1.location_type == "Chitin BIFs" and resolved2.location_type and "Modules" in resolved2.location_type:
                    log_func("  → Resource moved from BIF to Modules (now modifiable)")

            # Validate TSLPatcher destination was set correctly (now set directly in engine.py)
            if modifications_by_type is not None:
                new_mod_count = (
                    len(modifications_by_type.gff) +
                    len(modifications_by_type.twoda) +
                    len(modifications_by_type.ssf) +
                    len(modifications_by_type.tlk) +
                    len(modifications_by_type.ncs)
                )

                if new_mod_count > original_mod_count:
                    # A modification was added - validate its destination is correct
                    expected_destination = determine_tslpatcher_destination(
                        resolved1.location_type,
                        resolved2.location_type,
                        resolved2.filepath,
                    )

                    # Check the most recently added modification(s)
                    # Note: TLK is excluded because it's append-only and goes to game root
                    for mod_list in [
                        modifications_by_type.gff,
                        modifications_by_type.twoda,
                        modifications_by_type.ssf,
                        modifications_by_type.ncs,
                    ]:
                        if len(mod_list) > 0:
                            most_recent = mod_list[-1]
                            if hasattr(most_recent, "destination"):
                                actual_dest = most_recent.destination
                                if actual_dest != expected_destination:
                                    # Destination mismatch - log warning and correct it
                                    log_func(f"  ⚠ Warning: Destination mismatch! Expected '{expected_destination}', got '{actual_dest}'. Correcting...")
                                    most_recent.destination = expected_destination
                                else:
                                    # Destination is correct - log for confirmation
                                    log_func(f"  ✓ TSLPatcher destination: {actual_dest}")

            is_same_result = False
        elif result is None:
            # Error occurred
            error_count += 1
            log_func(f"\n[ERROR] {identifier}")
            log_func(f"  Install1 source (vanilla/base): {resolved1.source_location}")
            log_func(f"  Install2 source (modded/target): {resolved2.source_location}")
            is_same_result = None
        else:
            # Identical
            identical_count += 1

    # Summary
    log_func("")
    log_func("=" * 80)
    log_func("COMPARISON SUMMARY")
    log_func("=" * 80)
    log_func(f"Total resources processed: {processed_count}")
    log_func(f"  Identical: {identical_count}")
    log_func(f"  Modified: {diff_count}")
    log_func(f"  Errors: {error_count}")
    log_func("=" * 80)

    return is_same_result


def explain_resolution_order(
    identifier: ResourceIdentifier,
    install1_resolved: ResolvedResource,
    install2_resolved: ResolvedResource,
    log_func: Callable[[str], None],
) -> None:
    """Explain the resolution order for a resource in user-friendly terms.

    Args:
        identifier: The resource being explained
        install1_resolved: Resolved resource from install1
        install2_resolved: Resolved resource from install2
        log_func: Logging function
    """
    log_func(f"\nResolution explanation for {identifier}:")
    log_func("")
    log_func("  KOTOR loads files in this order (first match wins):")
    log_func("    1. Override folder (HIGHEST PRIORITY)")
    log_func("    2. Modules folder (.mod files)")
    log_func("    3. Modules folder (.rim/_s.rim/_dlg.erf files)")
    log_func("    4. Chitin/BIF archives (LOWEST PRIORITY)")
    log_func("")

    # Explain install1
    log_func("  Install 1 (vanilla/older):")
    if install1_resolved.data is None:
        log_func("    → Resource NOT FOUND")
    else:
        priority1 = get_location_display_name(install1_resolved.location_type)
        log_func(f"    → Found in: {priority1}")
        log_func(f"    → Path: {install1_resolved.source_location}")

    log_func("")

    # Explain install2
    log_func("  Install 2 (mine/modded):")
    if install2_resolved.data is None:
        log_func("    → Resource NOT FOUND")
    else:
        priority2 = get_location_display_name(install2_resolved.location_type)
        log_func(f"    → Found in: {priority2}")
        log_func(f"    → Path: {install2_resolved.source_location}")

    log_func("")

    # Explain what this means for modding
    if (
        install1_resolved.data is not None
        and install2_resolved.data is not None
        and install1_resolved.location_type != install2_resolved.location_type
    ):
        log_func("  What this means:")
        if install2_resolved.location_type == "Override folder":
            log_func("    ✓ Resource was moved to Override (will override vanilla version)")
            log_func("    ✓ TSLPatcher should install to Override")
        elif (
            install1_resolved.location_type == "Chitin BIFs"
            and install2_resolved.location_type and "Modules" in install2_resolved.location_type
        ):
            log_func("    ✓ Resource extracted from BIF to Modules (now modifiable)")
            log_func("    ✓ TSLPatcher should install to appropriate module")
        else:
            loc1_name = get_location_display_name(install1_resolved.location_type)
            loc2_name = get_location_display_name(install2_resolved.location_type)
            log_func(f"    → Priority changed from {loc1_name} to {loc2_name}")

    log_func("")

