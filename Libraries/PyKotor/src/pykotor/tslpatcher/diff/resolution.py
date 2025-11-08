#!/usr/bin/env python3
"""Resource resolution order handling for KotorDiff.

This module resolves resources in the same priority order the game uses:
1. Override
2. Modules (.mod)
3. Modules (.rim/_s.rim/_dlg.erf)
4. Chitin (BIFs)

All paths are treated interchangeably, and differences always produce
both an InstallList entry and a corresponding modification entry.
"""

from __future__ import annotations

import traceback

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from pykotor.extract.installation import Installation
from pykotor.resource.formats.gff.gff_data import GFFContent
from pykotor.tslpatcher.diff.engine import get_module_root
from utility.error_handling import universal_simplify_exception

if TYPE_CHECKING:
    from pykotor.extract.file import FileResource, ResourceIdentifier
    from pykotor.tslpatcher.mods.tlk import ModificationsTLK
    from pykotor.tslpatcher.writer import IncrementalTSLPatchDataWriter, ModificationsByType


@dataclass
class TLKModificationWithSource:
    """Wrapper that associates a TLK modification with its source path.

    This allows us to track which input path each TLK came from, so we know
    where to scan for StrRef references (references exist ONLY in the path
    that contains the StrRef).

    This wrapper also stores StrRef metadata that's specific to diff operations,
    keeping it separate from the ModificationsTLK class which is used by both
    the reader and writer.

    Attributes:
        modification: The ModificationsTLK object
        source_path: The input path (Installation, folder, or file) this TLK came from
        source_index: Index of the source path (0=first, 1=second, 2=third, etc.)
        is_installation: Whether source_path is an Installation object
        strref_mappings: Maps old StrRef -> token_id for reference analysis
        source_filepath: Path to the source TLK file for StrRef reference finding (base installation)
        source_installation: Source installation for StrRef reference finding (base installation)
    """

    modification: ModificationsTLK
    source_path: Installation | Path  # Installation or Path (order matters for type checking)
    source_index: int
    is_installation: bool = field(default=False)
    strref_mappings: dict[int, int] = field(default_factory=dict)  # old_strref -> token_id
    source_filepath: Path | None = None  # Base installation TLK path for reference finding
    source_installation: Installation | None = None  # Base installation for reference finding


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

        # Group module files by their basename for proper composite handling
        module_groups: dict[str, list[tuple[Path, FileResource]]] = defaultdict(list)

        for file_resource in file_resources:
            filepath = file_resource.filepath()
            parent_names_lower = [parent.name.lower() for parent in filepath.parents]

            # Store for data retrieval later
            resource_instances[filepath] = file_resource

            # Categorize by location (ONLY resolution-order locations)
            if "override" in parent_names_lower:
                override_files.append(filepath)
            elif "modules" in parent_names_lower:
                # Group by module basename to handle composite loading correctly
                try:
                    module_root = get_module_root(filepath)
                    module_groups[module_root].append((filepath, file_resource))
                except Exception as e:  # noqa: BLE001
                    log_func(f"Warning: Could not determine module root for {filepath}: {e}")
                    log_func("Full traceback:")
                    for line in traceback.format_exc().splitlines():
                        log_func(f"  {line}")
                    # Fallback: add to rim files without grouping
                    if filepath.suffix.lower() == ".mod":
                        module_mod_files.append(filepath)
                    else:
                        module_rim_files.append(filepath)
            elif "data" in parent_names_lower or filepath.suffix.lower() == ".bif":
                chitin_files.append(filepath)
            elif filepath.parent == install_root:
                # Files directly in installation root (like dialog.tlk, chitin.key, etc.)
                # Treat as Override priority since they're loose files at root level
                override_files.append(filepath)
            # StreamWaves/etc in subdirectories are NOT added - they don't participate in resolution

        # Within each module basename group, apply composite loading priority
        # Priority within a group: .mod > .rim > _s.rim > _dlg.erf (unsure whether game does this since files in these groups never conflict in vanilla game)
        def get_composite_priority(filepath: Path) -> int:
            """Get priority for composite loading (lower = higher priority)."""
            name_lower = filepath.name.lower()
            if name_lower.endswith(".mod"):
                return 0  # Highest priority
            if name_lower.endswith(".rim") and not name_lower.endswith("_s.rim"):
                return 1
            if name_lower.endswith("_s.rim"):
                return 2
            if name_lower.endswith("_dlg.erf"):
                return 3
            return 4  # Other files

        # Process each module group and pick the winner
        for module_basename, files_in_group in module_groups.items():
            if not files_in_group:
                log_func(f"Warning: Empty module group for basename {module_basename}")
                continue

            # Sort by composite priority and pick the winner
            sorted_files = sorted(files_in_group, key=lambda x: get_composite_priority(x[0]))
            winner_path, _ = sorted_files[0]

            # Add winner to appropriate category
            if winner_path.suffix.lower() == ".mod":
                module_mod_files.append(winner_path)
                continue
            module_rim_files.append(winner_path)

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
        # For modules, only include files from the same module basename group as the chosen file
        module_rim_files_for_logging = module_rim_files.copy()
        module_mod_files_for_logging = module_mod_files.copy()

        # If chosen file is from modules, add all files from its basename group to logging
        if chosen_filepath and "modules" in [parent.name.lower() for parent in chosen_filepath.parents]:
            try:
                chosen_module_root = get_module_root(chosen_filepath)
                # Get all files from this module group (including non-winners for logging)
                if chosen_module_root in module_groups:
                    group_files = [path for path, _ in module_groups[chosen_module_root]]
                    # Separate by type for logging
                    module_mod_files_for_logging = [f for f in group_files if f.suffix.lower() == ".mod"]
                    module_rim_files_for_logging = [f for f in group_files if f.suffix.lower() in (".rim", ".erf")]
            except Exception as e:  # noqa: BLE001
                log_func(f"Warning: Could not get module group for logging: {e}")
                log_func("Full traceback:")
                for line in traceback.format_exc().splitlines():
                    log_func(f"  {line}")

        all_locs: dict[str, list[Path]] = {
            "Override folder": override_files,
            "Modules (.mod)": module_mod_files_for_logging,
            "Modules (.rim/_s.rim/._dlg.erf)": module_rim_files_for_logging,
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
    *,
    additional_resolved: list[ResolvedResource] | None = None,
    additional_installs: list[Installation] | None = None,
) -> None:
    """Log combined resolution results from installations side-by-side.

    Shows which files were CHOSEN by resolution order and which were shadowed.
    Supports n-way comparisons (3+ installations).

    Args:
        install1: Base installation (index 0)
        install2: Target installation (index 1)
        identifier: Resource identifier being resolved
        resolved1: Resolution result from base installation
        resolved2: Resolution result from target installation
        log_func: Logging function
        additional_resolved: Optional list of additional resolution results (indices 2+)
        additional_installs: Optional list of additional installations (indices 2+)
    """
    install1_name = install1.path().name
    install2_name = install2.path().name

    # Build list of all installations and resolutions
    all_names: list[str] = [install1_name, install2_name]
    all_resolved: list[ResolvedResource] = [resolved1, resolved2]

    if additional_installs and additional_resolved:
        all_names.extend(install.path().name for install in additional_installs)
        all_resolved.extend(additional_resolved)

    # Log header showing all installations
    install_count = len(all_names)
    if install_count == 2:
        log_func(f"Installation 0 ({install1_name}), 1 ({install2_name})")
    else:
        log_func(f"Installations: {', '.join(f'{idx} ({name})' for idx, name in enumerate(all_names))}")
    log_func("  Checking each location:")

    # Get all locations from all installations
    all_installation_locations: list[dict[str, list[Path]]] = []
    all_installation_locations.extend(resolved.all_locations or {} for resolved in all_resolved)

    # Priority order for display
    location_order: list[tuple[str, str]] = [
        ("Override folder", "1. Override folder"),
        ("Modules (.mod)", "2. Modules (.mod)"),
        ("Modules (.rim/_s.rim/.erf)", "3. Modules (.rim/_s.rim/.erf)"),
        ("Chitin BIFs", "4. Chitin BIFs"),
    ]

    # Build list of all installations with their paths for relative path calculation
    all_installations_with_paths: list[Installation | Path] = [install1, install2]
    if additional_installs:
        all_installations_with_paths.extend(additional_installs)
    all_installations_with_paths = [install if isinstance(install, Installation) else Path(install) for install in all_installations_with_paths]

    # Track if we've found a chosen file yet (only ONE chosen across all installations)
    found_chosen: bool = False
    chosen_module_root: str | None = None  # For module files, track the chosen module root

    for loc_key, loc_display in location_order:
        # Collect files from all installations at this location
        all_files_to_show: list[tuple[int, str, Path, bool]] = []  # (install_idx, install_name, filepath, is_chosen)

        for idx, (install_name, resolved, locations) in enumerate(zip(all_names, all_resolved, all_installation_locations)):
            files_at_loc = locations.get(loc_key, [])
            for f in files_at_loc:
                is_chosen = (resolved.filepath == f) and not found_chosen

                # For module files, only include files with same base name as chosen
                if loc_key in ("Modules (.mod)", "Modules (.rim/_s.rim/.erf)") and found_chosen and chosen_module_root:
                    try:
                        file_module_root = get_module_root(f)
                        if file_module_root != chosen_module_root:
                            continue  # Skip files with different base names
                    except Exception as e:  # noqa: BLE001
                        log_func(f"Warning: Could not get module root for {f}: {e}")
                        # If we can't get module root, include the file

                # Track chosen module root for filtering subsequent files
                if is_chosen and loc_key in ("Modules (.mod)", "Modules (.rim/_s.rim/.erf)"):
                    try:
                        chosen_module_root = get_module_root(f)
                    except Exception as e:  # noqa: BLE001
                        log_func(f"Warning: Could not get module root for chosen file {f}: {e}")

                if is_chosen:
                    found_chosen = True

                all_files_to_show.append((idx, install_name, f, is_chosen))

        if not all_files_to_show:
            log_func(f"    {loc_display} -> not found")
        else:
            for install_idx, install_name, filepath, is_chosen in all_files_to_show:
                try:  # noqa: PERF203
                    installation = all_installations_with_paths[install_idx]
                    rel_path = filepath.relative_to(installation if isinstance(installation, Path) else installation.path())
                    full_path = f"{install_name}/{rel_path}"

                    if is_chosen:
                        log_func(f"    {loc_display} -> CHOSEN (install{install_idx}) - {full_path}")
                    else:
                        log_func(f"    {loc_display} -> (shadowed, install{install_idx}) {full_path}")
                except ValueError:
                    # Couldn't get relative path, just show filename
                    if is_chosen:
                        log_func(f"    {loc_display} -> CHOSEN (install{install_idx}) - {filepath.name}")
                    else:
                        log_func(f"    {loc_display} -> (shadowed, install{install_idx}) {filepath.name}")


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
    index: dict[ResourceIdentifier, list[FileResource]] = defaultdict(list)

    for file_resource in installation:
        index[file_resource.identifier()].append(file_resource)

    return dict(index)


def _should_process_tlk_file(resolved: ResolvedResource) -> bool:
    """Determine if a TLK file should be processed based on filtering rules.

    When both comparison paths are installations, only process TLK files that are:
    - In the root of the installation folder, AND
    - Named 'dialog.tlk' or 'dialog_f.tlk'

    This filters out backup copies, test files, and other irrelevant TLK files.

    Args:
        resolved: Resolved resource from the an installation

    Returns:
        True if the TLK file should be processed, False otherwise
    """
    # Always process if we don't have filepath info
    if not resolved.filepath:
        return True

    # Check location type - only process TLKs from Installation root or Override
    if resolved.location_type not in ("Installation root", "Override folder"):
        return False

    # Check filename - only allow dialog.tlk and dialog_f.tlk
    filename = resolved.filepath.name.lower()
    return filename in ("dialog.tlk", "dialog_f.tlk")


def determine_tslpatcher_destination(
    location_a: str | None,  # noqa: ARG001
    location_b: str | None,
    filepath_b: Path | None,
) -> str:
    r"""Determine the appropriate TSLPatcher destination based on source locations.

    In n-way comparisons, this determines where to install a resource based on
    where it exists across the compared paths. Paths are treated as interchangeable.

    Args:
        location_a: Location type where resource was found in first path (unused - reserved for future)
        location_b: Location type where resource was found in second path (or None if missing)
        filepath_b: Full path to the resource file in second path (or None if missing)

    Returns:
        Destination string for TSLPatcher (e.g., "Override", "modules\\danm13.mod")
    """
    # If resource is in Override, destination is Override
    if location_b == "Override folder":
        return "Override"

    # If resource is in a module
    if location_b and "Modules" in location_b and filepath_b:
        filepath_str = str(filepath_b).lower()

        # Check if it's in a .mod file
        if ".mod" in filepath_str or ".erf" in filepath_str:
            # Extract module filename
            module_name = filepath_b.name
            return f"modules\\{module_name}"

        # It's in a .rim - need to redirect to corresponding .mod
        if ".rim" in filepath_str:
            from pykotor.tslpatcher.diff.engine import get_module_root  # noqa: PLC0415

            module_root = get_module_root(filepath_b)
            return f"modules\\{module_root}.mod"

    # Default to Override for safety
    return "Override"


def diff_installations_with_resolution(  # noqa: PLR0913, PLR0915, C901
    files_and_folders_and_installations: list[Path | Installation],
    *,
    filters: list[str] | None = None,
    log_func: Callable[[str], None],
    compare_hashes: bool = True,
    modifications_by_type: ModificationsByType | None = None,
    incremental_writer: IncrementalTSLPatchDataWriter | None = None,
) -> bool | None:
    """Compare N installations/paths using proper resource resolution order (N-way wrapper).

    This is the n-way comparison function that accepts an arbitrary number of paths.
    Each path can be an Installation object, a folder Path, or a file Path.
    All paths are treated as interchangeable - no hardcoded "vanilla" vs "modded" assumptions.

    Args:
        files_and_folders_and_installations: List of Installation objects or Path objects (folders or files) to compare
                                            Minimum 2 paths required. Can be 2, 3, 4, 5, ... N paths.
        filters: Optional list of resource name filters
        log_func: Logging function
        compare_hashes: Whether to compare hashes for binary files
        modifications_by_type: Optional collection for TSLPatcher modifications
        incremental_writer: Optional incremental writer for immediate file/INI writes

    Returns:
        True if all identical, False if any differences, None if errors occurred

    Raises:
        ValueError: If less than 2 paths provided
        NotImplementedError: If Path objects are provided (only Installation objects supported currently)
    """
    if len(files_and_folders_and_installations) < 2:  # noqa: PLR2004
        msg = f"At least 2 paths required for comparison, got {len(files_and_folders_and_installations)}"
        raise ValueError(msg)

    # For now, delegate to the 2-way function if exactly 2 installations
    # This is a compatibility shim while we complete the full n-way implementation
    if len(files_and_folders_and_installations) == 2:  # noqa: PLR2004
        install1_candidate = files_and_folders_and_installations[0]
        install2_candidate = files_and_folders_and_installations[1]

        if not isinstance(install1_candidate, Installation) or not isinstance(install2_candidate, Installation):
            msg = "Current implementation requires Installation objects, Path support coming soon"
            raise NotImplementedError(msg)

        return _diff_installations_with_resolution_impl(
            install1_candidate,
            install2_candidate,
            filters=filters,
            log_func=log_func,
            compare_hashes=compare_hashes,
            modifications_by_type=modifications_by_type,
            incremental_writer=incremental_writer,
            additional_installs=None,
        )

    # For 3+ installations, delegate with additional_installs
    install1_candidate = files_and_folders_and_installations[0]
    install2_candidate = files_and_folders_and_installations[1]
    additional_candidates = files_and_folders_and_installations[2:]

    if not isinstance(install1_candidate, Installation) or not isinstance(install2_candidate, Installation):
        msg = "Current implementation requires Installation objects, Path support coming soon"
        raise NotImplementedError(msg)

    additional_installations = [inst for inst in additional_candidates if isinstance(inst, Installation)]

    return _diff_installations_with_resolution_impl(
        install1_candidate,
        install2_candidate,
        filters=filters,
        log_func=log_func,
        compare_hashes=compare_hashes,
        modifications_by_type=modifications_by_type,
        incremental_writer=incremental_writer,
        additional_installs=additional_installations if additional_installations else None,
    )


def _diff_installations_with_resolution_impl(  # noqa: PLR0913, PLR0915, C901
    install1: Installation,
    install2: Installation,
    *,
    filters: list[str] | None = None,
    log_func: Callable[[str], None],
    compare_hashes: bool = True,
    modifications_by_type: ModificationsByType | None = None,
    incremental_writer: IncrementalTSLPatchDataWriter | None = None,
    additional_installs: list[Installation] | None = None,
) -> bool | None:
    """Compare installations using proper resource resolution order (2-way implementation).

    This function respects the game's actual file priority:
    - Override (highest)
    - Modules (.mod)
    - Modules (.rim/_s.rim/_dlg.erf)
    - Chitin/BIFs (lowest)

    (todo): Will support N-way comparisons (3+ installations):
    - install1: Base/reference installation (index 0)
    - install2: Target installation (index 1) - generates patches against install1
    - additional_installs: Optional list of additional installations (indices 2+) for future n-way support

    Args:
        install1: Base/reference installation (index 0 - corresponds to --mine)
        install2: Target installation (index 1 - corresponds to --older)
        filters: Optional list of resource name filters
        log_func: Logging function
        compare_hashes: Whether to compare hashes for binary files
        modifications_by_type: Optional collection for TSLPatcher modifications
        incremental_writer: Optional incremental writer for immediate file/INI writes
        additional_installs: Optional additional installations for n-way comparison support

    Returns:
        True if identical, False if different, None if errors occurred
    """
    from pykotor.tslpatcher.diff.engine import DiffContext, Path as EnginePath, _add_to_install_folder, diff_data  # noqa: PLC0415

    # Build list of all installations (base, target, and any additional)
    all_installations: list[Installation] = [install1, install2]
    if additional_installs:
        all_installations.extend(additional_installs)

    install_count: int = len(all_installations)

    # Get display names for logging
    install1_name: str = install1.path().name
    install2_name: str = install2.path().name

    log_func("")
    log_func("=" * 80)
    log_func("RESOURCE-AWARE INSTALLATION COMPARISON")
    log_func("=" * 80)
    log_func(f"Base installation (index 0):   {install1.path()}")
    log_func(f"Target installation (index 1): {install2.path()}")
    if additional_installs:
        for idx, install in enumerate(additional_installs, start=2):
            log_func(f"Additional installation (index {idx}): {install.path()}")
    log_func(f"Total installations: {install_count}")
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

    # Build indices for all installations
    install_indices: dict[int, dict[ResourceIdentifier, list[FileResource]]] = {}
    all_identifiers_set: set[ResourceIdentifier] = set()

    for idx, installation in enumerate(all_installations):
        install_indices[idx] = build_resource_index(installation)
        all_identifiers_set.update(install_indices[idx].keys())
        log_func(f"  Installation {idx}: {len(install_indices[idx])} unique resources indexed")

    # Convenience aliases for primary installations
    index1 = install_indices[0]
    index2 = install_indices[1]

    all_identifiers = list(all_identifiers_set)
    log_func(f"  Total unique resources across all installations: {len(all_identifiers)}")
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
        log_func(f"Processing {len(filtered_tlk_identifiers)} TLK files...")
        log_func("")
        for idx, identifier in enumerate(filtered_tlk_identifiers, start=1):
            log_func(f"Processing TLK {idx}/{len(filtered_tlk_identifiers)}: {identifier.resname}.{identifier.restype.extension}")
            # Resolve in both installations using indices (O(1) lookups)
            resolved1 = resolve_resource_in_installation(install1, identifier, log_func=log_func, verbose=False, resource_index=index1)
            resolved2 = resolve_resource_in_installation(install2, identifier, log_func=log_func, verbose=False, resource_index=index2)

            # Check if resource exists in both
            if resolved1.data is None and resolved2.data is None:
                log_func(f"    TLK {identifier.resname} missing in both installations, skipping")
                continue

            if resolved1.data is None:
                # Only in target installation (new resource) - add to [InstallList] and create patch
                log_func(f"    TLK {identifier.resname} only in target installation - adding to InstallList")
                destination = determine_tslpatcher_destination(None, resolved2.location_type, resolved2.filepath)
                filename = f"{identifier.resname}.{identifier.restype.extension}"
                if modifications_by_type is not None:
                    # Create context for patch creation
                    file1_rel = EnginePath("base") / filename  # Base (missing)
                    file2_rel = EnginePath("target") / filename  # Target (exists)
                    context = DiffContext(file1_rel, file2_rel, identifier.restype.extension.lower())
                    _add_to_install_folder(
                        modifications_by_type,
                        destination,
                        filename,
                        log_func=log_func,
                        modded_data=resolved2.data,  # Data from target path (install1)
                        modded_path=resolved2.filepath,  # Path from target (install1)
                        context=context,
                        incremental_writer=incremental_writer,
                    )
                if incremental_writer is not None:
                    incremental_writer.add_install_file(destination, filename, resolved2.filepath)
                continue

            if resolved2.data is None:
                # Only in base installation (removed resource) - no action needed
                log_func(f"    TLK {identifier.resname} only in base installation - no action needed")
                continue

            # Both exist - compare them using proper format-aware comparison
            log_func(f"    Comparing TLK {identifier.resname} between installations")
            # For TLK files, DON'T set resname - they are loose files, not in containers
            # Setting resname causes duplication in 'where' property (dialog.tlk/dialog.tlk)
            ctx = DiffContext(
                file1_rel=Path(install1.path().name) / resolved1.filepath.name if resolved1.filepath else Path(install1.path().name) / "unknown",
                file2_rel=Path(install2.path().name) / resolved2.filepath.name if resolved2.filepath else Path(install2.path().name) / "unknown",
                ext=identifier.restype.extension.lower(),
                resname=None,  # TLK files are loose files, not in containers
                file1_location_type=resolved1.location_type,
                file2_location_type=resolved2.location_type,
                file1_filepath=resolved1.filepath,  # Base installation path for StrRef reference finding
                file2_filepath=resolved2.filepath,
                file1_installation=install1,  # Base installation object for StrRef reference finding
                file2_installation=install2,  # Target installation object for StrRef/2DA reference finding
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

            result: bool | None = diff_data(
                resolved1.data,
                resolved2.data,
                ctx,
                log_func=tlk_buffered_log_func,
                compare_hashes=compare_hashes,
                modifications_by_type=modifications_by_type,
                incremental_writer=incremental_writer,
            )

            # TLK linking is handled immediately per-diff by the incremental writer

            # Output the buffered diff results
            for line in tlk_diff_output_lines:
                log_func(line)

    # Remove TLK identifiers from the main list since we've processed them
    all_identifiers: list[ResourceIdentifier] = [ident for ident in all_identifiers if ident.restype.extension.lower() != "tlk"]
    log_func("TLK processing complete.")
    log_func("")

    # Ensure complete [TLKList] section is written before StrRef cache building
    if incremental_writer is not None:
        incremental_writer.write_pending_tlk_modifications()
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
    all_identifiers = sorted(all_identifiers, key=lambda x: (get_processing_priority(x), str(x)))

    # Assert that at least ONE modification entry exists before processing resources
    # This ensures TLK StrRef references are found and linked early (fast fail)
    assert modifications_by_type is not None, "modifications_by_type must not be None"
    total_mods: int = (
        len(modifications_by_type.gff) + len(modifications_by_type.twoda) + len(modifications_by_type.ssf) + len(modifications_by_type.ncs) + len(modifications_by_type.tlk)
    )
    assert total_mods > 0, (
        "No modifications found in modifications_by_type before resource processing! "
        f"TLK: {len(modifications_by_type.tlk)}, "
        f"GFF: {len(modifications_by_type.gff)}, "
        f"2DA: {len(modifications_by_type.twoda)}, "
        f"SSF: {len(modifications_by_type.ssf)}, "
        f"NCS: {len(modifications_by_type.ncs)}"
    )
    log_func(f"Found {total_mods} total modifications to process")

    log_func("Sorted resources for processing: 2DA -> GFF -> NCS -> SSF -> Others")
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

    # Cache for resolved resources to avoid re-resolution
    resolution_cache: dict[tuple[int, ResourceIdentifier], ResolvedResource] = {}

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
        # Use cache to avoid re-resolving the same resource
        cache_key1 = (0, identifier)
        cache_key2 = (1, identifier)
        if cache_key1 not in resolution_cache:
            resolution_cache[cache_key1] = resolve_resource_in_installation(install1, identifier, log_func=log_func, verbose=False, resource_index=index1)
        if cache_key2 not in resolution_cache:
            resolution_cache[cache_key2] = resolve_resource_in_installation(install2, identifier, log_func=log_func, verbose=False, resource_index=index2)
        resolved1: ResolvedResource = resolution_cache[cache_key1]
        resolved2: ResolvedResource = resolution_cache[cache_key2]

        # Check if resource exists in both
        if resolved1.data is None and resolved2.data is None:
            # Both missing - this shouldn't happen but handle it
            continue

        if resolved1.data is None:
            # Only in target installation (new resource) - add to [InstallList] and create patch
            log_func(f"\nProcessing resource: {identifier.resname}.{identifier.restype.extension}")

            # Re-resolve with verbose logging to show where it was found
            log_func(f"Installation 1 (target - {install2_name}):")
            resolve_resource_in_installation(install2, identifier, log_func=log_func, verbose=True, resource_index=index2)

            log_func(f"\n[NEW RESOURCE] {identifier}")
            log_func(f"  Source (target/install1): {resolved2.source_location}")
            log_func(f"  Missing from base (install0 - {install1_name})")

            # Add to InstallList with correct destination based on resolution order
            # Also create patch modifications
            if modifications_by_type is not None:
                from pykotor.tslpatcher.diff.engine import DiffContext, _add_to_install_folder  # noqa: PLC0415

                # Determine destination based on where it was found in target installation
                destination = determine_tslpatcher_destination(
                    None,  # Not in base
                    resolved2.location_type,
                    resolved2.filepath,
                )
                filename = f"{identifier.resname}.{identifier.restype.extension}"

                # Create context for patch creation
                file1_rel = Path("base") / filename  # Base (missing)
                file2_rel = Path("target") / filename  # Target (exists)
                context = DiffContext(file1_rel, file2_rel, identifier.restype.extension.lower())

                _add_to_install_folder(
                    modifications_by_type,
                    destination,
                    filename,
                    log_func=log_func,
                    modded_data=resolved2.data,  # Data from target path (install1)
                    modded_path=resolved2.filepath,  # Path from target (install1)
                    context=context,
                    incremental_writer=incremental_writer,
                )
                log_func(f"  → [InstallList] destination: {destination}")
                log_func("  → File will be INSTALLED, then PATCHED")
                # Write immediately if using incremental writer
                if incremental_writer is not None:
                    # Get the source file from target installation
                    source_path = resolved2.filepath
                    incremental_writer.add_install_file(destination, filename, source_path)

            diff_count += 1
            is_same_result = False
            continue

        if resolved2.data is None:
            # Resource exists in install1 but not install2
            # In n-way comparison, we treat this as needing a patch from install1's data
            # The resource should be installable from install1's version
            log_func(f"\nProcessing resource: {identifier.resname}.{identifier.restype.extension}")

            # Re-resolve with verbose logging to show where it was found
            log_func(f"Installation 0 ({install1_name}):")
            resolve_resource_in_installation(install1, identifier, log_func=log_func, verbose=True, resource_index=index1)

            log_func(f"\n[RESOURCE IN INSTALL0 ONLY] {identifier}")
            log_func(f"  Source (install0 - {install1_name}): {resolved1.source_location}")
            log_func(f"  Missing from install1 ({install2_name})")
            log_func("  → Creating patch from install0's version")

            # Add to InstallList and create patch modifications
            if modifications_by_type is not None:
                from pykotor.tslpatcher.diff.engine import DiffContext, _add_to_install_folder  # noqa: PLC0415

                # Determine destination based on where it was found
                destination = determine_tslpatcher_destination(
                    resolved1.location_type,
                    None,  # Not in install2
                    resolved1.filepath,
                )
                filename = f"{identifier.resname}.{identifier.restype.extension}"

                # Create context for patch creation
                file1_rel = Path(f"install0_{install1_name}") / filename
                file2_rel = Path(f"install1_{install2_name}") / filename  # Missing
                context = DiffContext(file1_rel, file2_rel, identifier.restype.extension.lower())

                _add_to_install_folder(
                    modifications_by_type,
                    destination,
                    filename,
                    log_func=log_func,
                    modded_data=resolved1.data,  # Data from first path (install0)
                    modded_path=resolved1.filepath,  # Path from first (install0)
                    context=context,
                    incremental_writer=incremental_writer,
                )
                log_func(f"  → [InstallList] destination: {destination}")
                log_func("  → File will be INSTALLED from install0")

                # Write immediately if using incremental writer
                if incremental_writer is not None:
                    source_path = resolved1.filepath
                    incremental_writer.add_install_file(destination, filename, source_path)

            diff_count += 1
            is_same_result = False
            continue

        # Both exist - check if both are from BIFs (read-only, skip comparison)
        both_from_bif: bool = resolved1.location_type == "Chitin BIFs" and resolved2.location_type == "Chitin BIFs"
        if both_from_bif:
            # Both from read-only BIFs - skip comparison (can't be patched anyway)
            identical_count += 1
            continue

        # Compare them using proper format-aware comparison
        # install1_name and install2_name already defined at function start
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

        # Only set resname for resources inside containers (BIFs/capsules)
        # For loose files, resname should be None to avoid duplication in 'where' property
        # The 'where' property uses resname to build paths like "container.ext/resource.ext"
        # For loose files, file2_rel already contains the full path, so no resname needed
        is_in_container: bool | None = resolved2.location_type == "Chitin BIFs" or (
            resolved2.filepath and resolved2.filepath.suffix.lower() in (".bif", ".rim", ".erf", ".mod", ".sav")
        )
        resname_for_context: str | None = identifier.resname if is_in_container else None

        ctx = DiffContext(
            file1_rel=file1_path,
            file2_rel=file2_path,
            ext=identifier.restype.extension.lower(),
            resname=resname_for_context,
            # Pass resolution information so destination is set correctly from the start
            file1_location_type=resolved1.location_type,
            file2_location_type=resolved2.location_type,
            file2_filepath=resolved2.filepath,
        )

        # Store original modifications count to detect if diff_data added any
        original_mod_count: int = 0
        if modifications_by_type is not None:
            original_mod_count = (
                len(modifications_by_type.gff)
                + len(modifications_by_type.twoda)
                + len(modifications_by_type.ssf)
                + len(modifications_by_type.tlk)
                + len(modifications_by_type.ncs)
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
            log_func(f"  Base source (install0 - {install1_name}): {resolved1.source_location}")
            log_func(f"  Target source (install1 - {install2_name}): {resolved2.source_location}")

            # Log priority explanation if sources are different
            if resolved1.location_type != resolved2.location_type:
                priority1 = get_location_display_name(resolved1.location_type)
                priority2 = get_location_display_name(resolved2.location_type)
                log_func(f"  Priority changed: {priority1} → {priority2}")

                if resolved2.location_type == "Override folder":
                    log_func(f"  → Resource moved to Override (will override base {priority1})")
                elif resolved1.location_type == "Chitin BIFs" and resolved2.location_type and "Modules" in resolved2.location_type:
                    log_func("  → Resource moved from BIF to Modules (now modifiable)")

            # Validate TSLPatcher destination was set correctly (now set directly in engine.py)
            if modifications_by_type is not None:
                new_mod_count = (
                    len(modifications_by_type.gff)
                    + len(modifications_by_type.twoda)
                    + len(modifications_by_type.ssf)
                    + len(modifications_by_type.tlk)
                    + len(modifications_by_type.ncs)
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

                # ALWAYS also add an InstallList entry so the file exists before patching
                try:
                    destination_for_install = determine_tslpatcher_destination(
                        resolved1.location_type,
                        resolved2.location_type,
                        resolved2.filepath,
                    )
                    filename_for_install = f"{identifier.resname}.{identifier.restype.extension}"
                    from pykotor.tslpatcher.diff.engine import _add_to_install_folder  # noqa: PLC0415

                    _add_to_install_folder(
                        modifications_by_type,
                        destination_for_install,
                        filename_for_install,
                        log_func=log_func,
                        modded_data=resolved2.data,
                        modded_path=resolved2.filepath,
                        context=ctx,
                        incremental_writer=incremental_writer,
                    )
                except Exception as e:  # noqa: BLE001
                    log_func(f"Error adding install entry for {identifier.resname}.{identifier.restype.extension}: {universal_simplify_exception(e)}")
                    log_func("Full traceback:")
                    for line in traceback.format_exc().splitlines():
                        log_func(f"  {line}")

            is_same_result = False
        elif result is None:
            # Error occurred
            error_count += 1
            log_func(f"\n[ERROR] {identifier}")
            log_func(f"  Base source (install0 - {install1_name}): {resolved1.source_location}")
            log_func(f"  Target source (install1 - {install2_name}): {resolved2.source_location}")
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
    *,
    additional_resolved: list[ResolvedResource] | None = None,
    install_names: list[str] | None = None,
) -> None:
    """Explain the resolution order for a resource in user-friendly terms.

    Supports n-way comparisons (3+ installations).

    Args:
        identifier: The resource being explained
        install1_resolved: Resolved resource from base installation (index 0)
        install2_resolved: Resolved resource from target installation (index 1)
        log_func: Logging function
        additional_resolved: Optional list of additional resolution results (indices 2+)
        install_names: Optional list of installation names for all installations
    """
    log_func(f"\nResolution explanation for {identifier}:")
    log_func("")
    log_func("  KOTOR loads files in this order (first match wins):")
    log_func("    1. Override folder (HIGHEST PRIORITY)")
    log_func("    2. Modules folder (.mod files)")
    log_func("    3. Modules folder (.rim/_s.rim/_dlg.erf files)")
    log_func("    4. Chitin/BIF archives (LOWEST PRIORITY)")
    log_func("")

    # Build list of all resolutions
    all_resolved: list[ResolvedResource] = [install1_resolved, install2_resolved]
    if additional_resolved:
        all_resolved.extend(additional_resolved)

    # Default names if not provided
    if install_names is None:
        install_names = [f"Installation {idx}" for idx in range(len(all_resolved))]

    # Explain each installation
    for idx, (resolved, name) in enumerate(zip(all_resolved, install_names)):
        log_func(f"  Installation {idx} ({name}):")
        if resolved.data is None:
            log_func("    → Resource NOT FOUND")
        else:
            priority = get_location_display_name(resolved.location_type)
            log_func(f"    → Found in: {priority}")
            log_func(f"    → Path: {resolved.source_location}")
        log_func("")

    # Explain what this means for modding (compare base vs target)
    if install1_resolved.data is not None and install2_resolved.data is not None and install1_resolved.location_type != install2_resolved.location_type:
        log_func("  What this means:")
        if install2_resolved.location_type == "Override folder":
            log_func("    ✓ Resource was moved to Override (will override base version)")
            log_func("    ✓ TSLPatcher should install to Override")
        elif install1_resolved.location_type == "Chitin BIFs" and install2_resolved.location_type and "Modules" in install2_resolved.location_type:
            log_func("    ✓ Resource extracted from BIF to Modules (now modifiable)")
            log_func("    ✓ TSLPatcher should install to appropriate module")
        else:
            loc1_name = get_location_display_name(install1_resolved.location_type)
            loc2_name = get_location_display_name(install2_resolved.location_type)
            log_func(f"    → Priority changed from {loc1_name} to {loc2_name}")

    log_func("")
