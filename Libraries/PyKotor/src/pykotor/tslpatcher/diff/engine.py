#!/usr/bin/env python3
"""Core comparison operations for KotorDiff.

This module offers unified diff/comparison logic for KotorDiff and is the main entry point
for resource diffing operations. It brings together helpers for:

- Resource walking: walking any path (installation root, container, directory, or single file)
  to yield ComparableResource objects containing all relevant comparison data and metadata.
- Dispatching/comparison: using appropriate compare() mixins when available, supporting all main
  formats (GFF, 2DA, TLK, LIP) and pluggable for additional types.

Designed for both 2-way and 3-way comparisons including changes.ini generation.

Handlers for individual resource formats can be added to the _HANDLERS map to extend support.

References:
----------
    vendor/TSLPatcher/TSLPatcher.pl - Original TSLPatcher INI format and patching logic
    vendor/HoloPatcher.NET/ - C# port of HoloPatcher with diff generation
    vendor/Kotor.NET/Kotor.NET.Patcher/ - Incomplete C# patcher
"""

from __future__ import annotations

import difflib
import traceback

from contextlib import suppress
from dataclasses import dataclass
from io import StringIO
from pathlib import Path, PurePath, PureWindowsPath
from typing import TYPE_CHECKING, Any, Callable, Iterable, Iterator, Mapping, Protocol

from pykotor.extract.capsule import Capsule
from pykotor.extract.installation import Installation, SearchLocation
from pykotor.resource.formats import gff, lip, ssf, tlk, twoda
from pykotor.resource.formats._base import ComparableMixin
from pykotor.resource.formats.erf import ERF, ERFType, write_erf
from pykotor.resource.formats.gff.gff_auto import bytes_gff
from pykotor.resource.formats.gff.gff_data import GFF, GFFComparisonResult, GFFContent
from pykotor.resource.formats.ncs.ncs_data import NCS
from pykotor.resource.formats.ssf.ssf_auto import bytes_ssf
from pykotor.resource.formats.twoda.twoda_auto import bytes_2da
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_capsule_file, is_rim_file
from pykotor.tools.path import CaseAwarePath
from pykotor.tslpatcher.diff.analyzers import DiffAnalyzer, DiffAnalyzerFactory
from pykotor.tslpatcher.mods.gff import ModificationsGFF, ModifyGFF
from pykotor.tslpatcher.mods.install import InstallFile
from pykotor.tslpatcher.mods.ncs import ModificationsNCS, ModifyNCS  # noqa: F401
from pykotor.tslpatcher.mods.ssf import ModificationsSSF, ModifySSF
from pykotor.tslpatcher.mods.template import PatcherModifications
from pykotor.tslpatcher.mods.tlk import ModificationsTLK, ModifyTLK
from pykotor.tslpatcher.mods.twoda import Modifications2DA, Modify2DA
from utility.error_handling import universal_simplify_exception
from utility.misc import generate_hash

if TYPE_CHECKING:
    from pykotor.common.module import ResourceResult
    from pykotor.extract.file import FileResource
    from pykotor.resource.formats.bwm.bwm_data import BWM
    from pykotor.resource.formats.lip.lip_data import LIP
    from pykotor.resource.formats.ltr.ltr_data import LTR
    from pykotor.resource.formats.lyt.lyt_data import LYT
    from pykotor.resource.formats.mdl.mdl_data import MDL
    from pykotor.resource.formats.rim.rim_data import RIM
    from pykotor.resource.formats.ssf.ssf_data import SSF
    from pykotor.resource.formats.tlk.tlk_data import TLK
    from pykotor.resource.formats.twoda.twoda_data import TwoDA
    from pykotor.resource.formats.vis.vis_data import VIS
    from pykotor.tslpatcher.diff.cache import DiffCache
    from pykotor.tslpatcher.writer import IncrementalTSLPatchDataWriter, ModificationsByType


gff_types: list[str] = list(gff.GFFContent.get_extensions())


def is_kotor_install_dir(path: Path) -> bool | None:
    """Check if a path is a KOTOR installation directory."""
    return path.is_dir() and path.joinpath("chitin.key").is_file()


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------


def get_module_root(module_filepath: Path) -> str:
    """Extract the module root name, following Installation.py logic."""
    root: str = module_filepath.stem.lower()
    root = root[:-2] if root.endswith("_s") else root
    root = root[:-4] if root.endswith("_dlg") else root
    return root


def find_related_module_files(module_path: CaseAwarePath) -> list[CaseAwarePath]:
    """Find all related module files for a given module file."""
    root: str = get_module_root(module_path)
    module_dir: CaseAwarePath = module_path.parent

    # Possible extensions for related module files
    extensions: tuple[str, ...] = (".rim", ".mod", "_s.rim", "_dlg.erf")
    related_files: list[CaseAwarePath] = []

    for ext in extensions:
        candidate: CaseAwarePath = module_dir / f"{root}{ext}"
        if candidate.is_file():
            related_files.append(candidate)

    return related_files


def _is_readonly_source(source_path: Path) -> bool:
    """Check if a source path is read-only (RIM, ERF, BIF, etc.).

    Args:
        source_path: Path to check

    Returns:
        True if the source is read-only and cannot be directly modified
    """
    source_lower: str = str(source_path).lower()
    suffix_lower: str = source_path.suffix.lower()

    # RIM and ERF files are read-only
    if suffix_lower in (".rim", ".erf"):
        return True

    # Files in BIF archives (chitin references)
    return bool("chitin" in source_lower or "bif" in source_lower or "data" in source_lower)


def _determine_tslpatchdata_source(
    file1_path: Path,
    file2_path: Path,  # noqa: ARG001
) -> str:
    """Determine which source file should be copied to tslpatchdata.

    Logic:
    - For 2-way diff: Use file1 (vanilla/base) as it will be patched
    - For 3+ way diff: Use second-to-last version that exists

    Args:
        file1_path: Path to first file (vanilla/base)
        file2_path: Path to second file (modded/target) - reserved for future N-way logic

    Returns:
        Display string indicating which source to use
    """
    # For now, implement 2-way logic (use vanilla/base version)
    # TODO(th3w1zard1): Extend for N-way comparison when that's fully implemented
    return f"vanilla ({file1_path.as_posix()})"


def _determine_destination_for_source(
    source_path: Path,
    resource_name: str | None = None,
    *,
    verbose: bool = True,
    log_func: Callable | None = None,
    location_type: str | None = None,
    source_filepath: Path | None = None,
) -> str:
    r"""Determine the proper TSLPatcher destination based on resource resolution order.

    This function determines where TSLPatcher should install/patch a resource based on
    the KOTOR resource resolution order:
        1. Override folder (highest priority - always wins)
        2. Modules (.mod files - priority)
        3. Modules (.rim/_s.rim/_dlg.erf - composite loading)
        4. Chitin BIFs (lowest priority - read-only)

    The destination is based on where the resource is found in the MODDED installation,
    not the vanilla one, because that's where we want TSLPatcher to place it.

    Args:
        source_path: Source file path from MODDED installation (used for fallback path inference)
        resource_name: Name of the resource file (e.g., "dan13_auto.utt")
        verbose: Whether to print destination reasoning
        log_func: Optional logging function
        location_type: Resolution order location type (e.g., "Override folder", "Modules (.mod)")
                      If provided, this takes precedence over path inference
        source_filepath: Full filepath in modded installation (for extracting module names)

    Returns:
        Destination string for TSLPatcher (e.g., "Override", "modules\\danm13.mod")
    """
    if log_func is None:
        log_func = lambda _: None  # noqa: E731

    display_name = resource_name if resource_name else source_path.name

    # PRIORITY 1: Use explicit location_type if provided (resolution-aware path)
    if location_type is not None:
        if location_type == "Override folder":
            if verbose:
                log_func(f"    +-- Resolution: {display_name} found in Override")
                log_func("    +-- Destination: Override (highest priority)")
            return "Override"

        if location_type == "Modules (.mod)":
            # Resource is in a .mod file - patch directly to that .mod
            actual_filepath = source_filepath if source_filepath else source_path
            destination = f"modules\\{actual_filepath.name}"
            if verbose:
                log_func(f"    +-- Resolution: {display_name} found in {actual_filepath.name}")
                log_func(f"    +-- Destination: {destination} (patch .mod directly)")
            return destination

        if location_type in ("Modules (.rim)", "Modules (.rim/_s.rim/_dlg.erf)"):
            # Resource is in read-only .rim/.erf - redirect to corresponding .mod
            actual_filepath = source_filepath if source_filepath else source_path
            module_root = get_module_root(actual_filepath)
            destination = f"modules\\{module_root}.mod"
            if verbose:
                log_func(f"    +-- Resolution: {display_name} found in {actual_filepath.name} (read-only)")
                log_func(f"    +-- Destination: {destination} (.mod overrides .rim/.erf)")
            return destination

        if location_type == "Chitin BIFs":
            # Resource only in BIFs - must go to Override (can't modify BIFs)
            if verbose:
                log_func(f"    +-- Resolution: {display_name} found in Chitin BIFs (read-only)")
                log_func("    +-- Destination: Override (BIFs cannot be modified)")
            return "Override"

        # Unknown location type - log warning and fall through to path inference
        if verbose:
            log_func(f"    +-- Warning: Unknown location_type '{location_type}', using path inference")

    # FALLBACK: Path-based inference (for non-resolution-aware code paths)
    parent_names_lower: set[str] = {parent.name.lower() for parent in (source_filepath.parents if source_filepath is not None else [])}
    if "override" in parent_names_lower:
        # Determine if it's a read-only source (RIM/ERF)
        if not _is_readonly_source(source_path):
            # MOD file - can patch directly
            destination = f"modules\\{source_path.name}"
            if verbose:
                log_func(f"    +-- Path inference: {display_name} in writable .mod")
                log_func(f"    +-- Destination: {destination} (patch directly)")
            return destination
        # Read-only module file - redirect to .mod
        module_root = get_module_root(source_path)
        destination = f"modules\\{module_root}.mod"
        if verbose:
            log_func(f"    +-- Path inference: {display_name} in read-only {source_path.suffix}")
            log_func(f"    +-- Destination: {destination} (.mod overrides read-only)")
        return destination

    # BIF/chitin sources go to Override
    if _is_readonly_source(source_path):
        if verbose:
            log_func(f"    +-- Path inference: {display_name} in read-only BIF/chitin")
            log_func("    +-- Destination: Override (read-only source)")
        return "Override"

    # Default to Override for other cases
    if verbose:
        log_func(f"    +-- Path inference: {display_name} (no specific location detected)")
        log_func("    +-- Destination: Override (default)")
    return "Override"


def _ensure_capsule_install(
    modifications_by_type: ModificationsByType,
    capsule_destination: str,
    *,
    capsule_path: Path | None,
    log_func: Callable[[str], None],
    incremental_writer: IncrementalTSLPatchDataWriter | None,
) -> None:
    r"""Ensure a capsule (.mod) exists in tslpatchdata and is listed before patching."""
    normalized_destination = capsule_destination.replace("/", "\\")
    capsule_pure = PureWindowsPath(normalized_destination)
    capsule_filename = capsule_pure.name
    capsule_suffix = capsule_pure.suffix.lower()

    if capsule_suffix != ".mod":
        return

    capsule_folder = "\\".join(capsule_pure.parts[:-1]) or "."

    filename_lower = capsule_filename.lower()
    folder_lower = capsule_folder.lower()

    already_present = any(
        install_file.destination.lower() == folder_lower and install_file.saveas.lower() == filename_lower
        for install_file in modifications_by_type.install
    )

    if not already_present:
        install_entry = InstallFile(
            capsule_filename,
            replace_existing=True,
            destination=capsule_folder,
        )
        modifications_by_type.install.append(install_entry)

    if incremental_writer is None or already_present:
        return

    def _path_is_file(path_obj: Path | None) -> bool:
        if path_obj is None:
            return False
        if hasattr(path_obj, "safe_isfile"):
            return bool(path_obj.is_file())  # type: ignore[attr-defined]
        return path_obj.is_file()

    if _path_is_file(capsule_path):
        incremental_writer.add_install_file(capsule_folder, capsule_filename, capsule_path)
        log_func(f"    Staged module '{capsule_filename}' for installation")
        return

    incremental_writer._add_to_install_folder(capsule_folder, capsule_filename)  # noqa: SLF001
    output_path = incremental_writer.tslpatchdata_path / capsule_filename
    if not output_path.exists():
        empty_mod = ERF(ERFType.MOD)
        write_erf(empty_mod, output_path, ResourceType.MOD)
        log_func(f"    Created empty module '{capsule_filename}' in tslpatchdata")


def _extract_and_add_capsule_resources(
    capsule_path: Path,
    modifications_by_type: ModificationsByType,
    incremental_writer: IncrementalTSLPatchDataWriter | None,
    log_func: Callable[[str], None],
) -> None:
    """Extract all resources from a capsule and add them to install folders.

    Args:
        capsule_path: Path to the capsule file (.mod/.rim/.erf)
        modifications_by_type: Modifications collection to update
        incremental_writer: Optional incremental writer for immediate file writes
        log_func: Logging function
    """
    try:
        from pykotor.extract.capsule import Capsule  # noqa: PLC0415

        capsule = Capsule(capsule_path)
        capsule_name: str = capsule_path.name

        # Determine destination based on capsule location and type
        parent_names_lower: list[str] = [parent.name.lower() for parent in capsule_path.parents]
        if "modules" in parent_names_lower:
            destination: str = f"modules\\{capsule_name}"
        else:
            destination = "Override"

        if capsule_path.suffix.lower() == ".mod":
            capsule_destination_str = destination if destination.lower().endswith(".mod") else f"{destination}\\{capsule_name}"
            _ensure_capsule_install(
                modifications_by_type,
                capsule_destination_str,
                capsule_path=capsule_path,
                log_func=log_func,
                incremental_writer=incremental_writer,
            )

        resource_count: int = 0
        for resource in capsule:
            resname: str = resource.resname()
            restype: ResourceType = resource.restype()
            filename: str = f"{resname}.{restype.extension.lower()}"

            # Add to install folder
            _add_to_install_folder(modifications_by_type, destination, filename, log_func=log_func)

            # Extract and copy immediately if incremental writer available
            if incremental_writer is not None:
                incremental_writer.add_install_file(destination, filename, capsule_path)

            resource_count += 1

        log_func(f"    Extracted {resource_count} resources from {capsule_name}")

    except Exception as e:  # noqa: BLE001
        log_func(f"  [Error] Failed to extract resources from capsule {capsule_path.name}: {e.__class__.__name__}: {e}")
        log_func("  Full traceback:")
        for line in traceback.format_exc().splitlines():
            log_func(f"    {line}")


def _add_missing_file_to_install(
    modifications_by_type: ModificationsByType,
    rel_path: str,
    *,
    log_func: Callable[[str], None] | None = None,
    file2_path: Path | None = None,
    incremental_writer: IncrementalTSLPatchDataWriter | None = None,
) -> None:
    """Add a missing file to the install folders list.

    Args:
        modifications_by_type: Modifications collection to update
        rel_path: Relative path of the file
        log_func: Optional logging function
        file2_path: Full path to the file in dir2 (modded/target)
        incremental_writer: Optional incremental writer for immediate file writes
    """
    if log_func is None:
        log_func = lambda _: None  # noqa: E731

    # Determine the install folder based on the relative path
    filename = PurePath(rel_path).name

    # Check if this is a capsule file (.mod/.rim/.erf)
    # If so, we need to extract resources from it, not copy the entire capsule
    if file2_path and is_capsule_file(filename):
        log_func(f"  Extracting resources from capsule: {filename}")
        if filename.lower().endswith(".mod"):
            capsule_destination = rel_path.replace("/", "\\")
            _ensure_capsule_install(
                modifications_by_type,
                capsule_destination,
                capsule_path=file2_path,
                log_func=log_func,
                incremental_writer=incremental_writer,
            )
        _extract_and_add_capsule_resources(
            file2_path,
            modifications_by_type,
            incremental_writer,
            log_func,
        )
        return

    parent_names_lower = [parent.name.lower() for parent in Path(rel_path).parents]

    # Determine destination folder
    destination = "Override"
    if "modules" in parent_names_lower:
        destination = "modules"
    elif "override" in parent_names_lower:
        destination = "Override"
    elif "streamwaves" in parent_names_lower or "streamvoice" in parent_names_lower:
        destination = "streamwaves"
    elif "streamsounds" in parent_names_lower:
        destination = "streamsounds"
    elif "movies" in parent_names_lower:
        destination = "movies"

    # Load modded file data for patch creation
    modded_data = None
    if file2_path is not None and file2_path.is_file():
        modded_data = file2_path.read_bytes()

    # Create context for patch creation
    modded_context = None
    if file2_path is not None:
        file1_rel = Path(rel_path)  # Vanilla (missing)
        file2_rel = Path(rel_path)  # Modded (exists)
        ext = file2_path.suffix.casefold().lstrip(".")
        modded_context = DiffContext(file1_rel, file2_rel, ext)

    # Add to install folder (will also create patch if supported)
    _add_to_install_folder(
        modifications_by_type,
        destination,
        filename,
        log_func=log_func,
        modded_data=modded_data,
        modded_path=file2_path,
        context=modded_context,
        incremental_writer=incremental_writer,
    )

    # If incremental writer is available, copy the file immediately
    if incremental_writer is not None and file2_path is not None:
        # Determine destination folder
        if "modules" in parent_names_lower:
            destination = "modules"
        elif "override" in parent_names_lower:
            destination = "Override"
        elif "streamwaves" in parent_names_lower or "streamvoice" in parent_names_lower:
            destination = "streamwaves"
        elif "streamsounds" in parent_names_lower:
            destination = "streamsounds"
        elif "movies" in parent_names_lower:
            destination = "movies"
        else:
            destination = "Override"
        incremental_writer.add_install_file(destination, filename, file2_path)


def _create_patch_for_missing_file(
    modifications_by_type: ModificationsByType,
    filename: str,
    folder: str,
    *,
    modded_data: bytes | None = None,
    modded_path: Path | None = None,
    context: DiffContext | None = None,
    log_func: Callable[[str], None] | None = None,
    incremental_writer: IncrementalTSLPatchDataWriter | None = None,
) -> None:
    """Create a patch modification for a file that doesn't exist in vanilla.

    This creates patch modifications that will be applied after the file is installed via InstallList.

    Args:
        modifications_by_type: Modifications collection to update
        filename: Name of the file
        folder: Destination folder
        modded_data: Modded file data (will be loaded from modded_path if not provided)
        modded_path: Path to modded file
        context: Optional diff context
        log_func: Optional logging function
        incremental_writer: Optional incremental writer
    """
    if log_func is None:
        log_func = lambda _: None  # noqa: E731

    # Get modded file data
    if modded_data is None:
        if modded_path is None or not modded_path.is_file():
            log_func(f"  Warning: Cannot create patch for {filename} - no data provided")
            return
        modded_data = modded_path.read_bytes()

    # Determine file extension
    file_ext = Path(filename).suffix.casefold().lstrip(".")
    if not file_ext:
        return  # No extension, can't determine type

    # Get analyzer for this file type
    analyzer = DiffAnalyzerFactory.get_analyzer(file_ext)
    if analyzer is None:
        return  # No analyzer for this type, skip patch creation

    try:
        # Create an empty/minimal file of the same type for comparison
        # For patchable formats, we'll compare modded file against an empty structure
        empty_data = _create_empty_file_data(file_ext)
        if empty_data is None:
            # Can't create empty file for this type, skip patch
            return

        # Create identifier for the file (use context if available, otherwise construct)
        identifier = str(context.where) if context else filename

        # Analyze differences (comparing modded file against empty)
        assert isinstance(analyzer, DiffAnalyzer), f"`analyzer` is not a DiffAnalyzer: {analyzer} (type: {type(analyzer)}) for context: {context}"  # noqa: E501
        result: PatcherModifications | tuple[PatcherModifications, dict[int, int]] | None = analyzer.analyze(empty_data, modded_data, identifier)
        assert result is not None, f"Analyzer returned None for context: {context}"
        if isinstance(result, tuple):
            modifications, _strref_mappings = result
            assert isinstance(modifications, PatcherModifications), (
                f"`modifications` is not a PatcherModifications: {modifications} (type: {type(modifications)}) for context: {context}"
            )  # noqa: E501
        else:
            modifications = result
            assert isinstance(modifications, PatcherModifications), (
                f"`modifications` is not a PatcherModifications: {modifications} (type: {type(modifications)}) for context: {context}"
            )  # noqa: E501
        if not modifications:
            return

        log_func(f"\n[PATCH] {filename}")

        # Set destination and sourcefile
        resource_name = Path(filename).name
        assert isinstance(modifications, PatcherModifications), (
            f"`modifications` is not a PatcherModifications: {modifications} (type: {type(modifications)}) for context: {context}"
        )  # noqa: E501
        modifications.destination = folder
        modifications.sourcefile = resource_name

        if isinstance(modifications, Modifications2DA):
            modifications_by_type.twoda.append(modifications)
            log_func("  |-- Type: [2DAList]")
        elif isinstance(modifications, ModificationsGFF):
            modifications.saveas = resource_name
            modifications_by_type.gff.append(modifications)
            log_func("  |-- Type: [GFFList]")
        elif isinstance(modifications, ModificationsSSF):
            modifications_by_type.ssf.append(modifications)
            log_func("  |-- Type: [SSFList]")
        else:
            # Unknown type, skip
            return

        modifiers_count = len(modifications.modifiers) if modifications.modifiers else 0
        if modifiers_count > 0:
            log_func(f"  |-- Modifications: {modifiers_count} changes")

        log_func("  +-- tslpatchdata: Will use installed file as base, then apply patch")

        # Write immediately if using incremental writer
        if incremental_writer is not None:
            # Use the modded file as the "vanilla" source (it's what will be installed)
            incremental_writer.write_modification(modifications, modded_data)

    except Exception as e:  # noqa: BLE001
        log_func(f"  Warning: Failed to create patch for {filename}: {e.__class__.__name__}: {e}")
        traceback.print_exc()


def _create_empty_file_data(ext: str) -> bytes | None:
    """Create an empty/minimal file data for a given extension.

    Args:
        ext: File extension (without dot)

    Returns:
        Empty file data bytes, or None if not supported
    """
    ext_lower = ext.lower()

    try:
        # For 2DA files, create empty TwoDA
        if ext_lower == "2da":
            empty_2da = twoda.TwoDA()
            return bytes_2da(empty_2da, ResourceType.TwoDA)

        # For SSF files, create empty SSF
        if ext_lower == "ssf":
            empty_ssf = ssf.SSF()
            return bytes_ssf(empty_ssf, ResourceType.SSF)

        # For GFF files, create empty GFF with appropriate content type based on extension
        if ext_lower in gff_types:
            # Try to determine GFFContent from extension
            # Match the logic from generator.py _load_or_create_gff
            try:
                gff_content = GFFContent[ext_lower.upper()] if ext_lower else GFFContent.GFF
            except (KeyError, AttributeError):
                # Fallback to generic GFF content type
                gff_content = GFFContent.GFF

            # Create empty GFF with determined content type
            empty_gff = GFF(gff_content)
            return bytes_gff(empty_gff, ResourceType.GFF)

    except Exception as e:  # noqa: BLE001
        # Log the exception for debugging
        print(f"Failed to create empty file data for extension '{ext}': {e.__class__.__name__}: {e}")
        traceback.print_exc()

    return None


def _add_to_install_folder(
    modifications_by_type: ModificationsByType,
    folder: str,
    filename: str,
    *,
    log_func: Callable[[str], None] | None = None,
    modded_data: bytes | None = None,
    modded_path: Path | None = None,
    context: DiffContext | None = None,
    incremental_writer: IncrementalTSLPatchDataWriter | None = None,
    create_patch: bool = True,
) -> None:
    """Add a file to an install folder, creating the folder entry if needed.

    Args:
        modifications_by_type: Modifications collection to update
        folder: Folder name (e.g., "Override", "modules", "streamwaves")
        filename: Filename to add
        log_func: Optional logging function
        modded_data: Optional modded file data for creating patch modifications
        modded_path: Optional path to modded file for creating patch modifications
        context: Optional diff context for creating patch modifications
        incremental_writer: Optional incremental writer for immediate file writes
        create_patch: Whether to create a patch modification (default: True)
    """
    if log_func is None:
        log_func = lambda _: None  # noqa: E731

    # Check if this file already exists in install list
    file_exists: bool = False
    for install_file in modifications_by_type.install:
        if (  # must be case-insensitive.
            install_file.destination.lower() == folder.lower() and install_file.saveas.lower() == filename.lower()
        ):
            file_exists = True
            break

    if not file_exists:
        # Create new InstallFile entry
        modifications_by_type.install.append(InstallFile(filename, destination=folder))
        log_func(f"\n[INSTALL] {filename}")
        log_func(f"  |-- Filename: {filename}")
        log_func(f"  |-- Destination: {folder}")
        log_func("  +-- tslpatchdata: File will be copied from appropriate source")

    # Ensure host capsule is staged when targeting resources within a .mod
    folder_lower = folder.lower()
    if folder_lower.endswith(".mod"):
        capsule_destination = folder if folder_lower.endswith(".mod") else f"{folder}\\{filename}"
        capsule_source_path: Path | None = None
        if modded_path is not None:
            if hasattr(modded_path, "safe_isfile"):
                if modded_path.is_file():  # type: ignore[attr-defined]
                    capsule_source_path = modded_path
            elif modded_path.is_file():
                capsule_source_path = modded_path

        _ensure_capsule_install(
            modifications_by_type,
            capsule_destination,
            capsule_path=capsule_source_path,
            log_func=log_func,
            incremental_writer=incremental_writer,
        )

    # Also create a patch modification (file will be patched after installation)
    # Only create patch if requested (avoid duplicates when diff_data already created one)
    if create_patch and (modded_data is not None or modded_path is not None):
        _create_patch_for_missing_file(
            modifications_by_type,
            filename,
            folder,
            modded_data=modded_data,
            modded_path=modded_path,
            context=context,
            log_func=log_func,
            incremental_writer=incremental_writer,
        )


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class PathInfo:
    """Metadata wrapper for a path in n-way comparison."""

    path: Path | Installation
    index: int  # Position in the paths list (0, 1, 2, ...)
    name: str  # Display name for logging
    is_installation: bool
    is_file: bool
    is_folder: bool

    @classmethod
    def from_path_or_installation(
        cls,
        path: Path | Installation,
        index: int,
    ) -> PathInfo:
        """Create PathInfo from a Path or Installation object."""
        if isinstance(path, Installation):
            return cls(
                path=path,
                index=index,
                name=path.path().name,
                is_installation=True,
                is_file=False,
                is_folder=False,
            )
        return cls(
            path=path,
            index=index,
            name=path.name,
            is_installation=False,
            is_file=bool(path.is_file()),
            is_folder=bool(path.is_dir()),
        )

    def get_path(self) -> Path:
        """Get the filesystem path."""
        if self.is_installation:
            assert isinstance(self.path, Installation)
            return self.path.path()
        assert isinstance(self.path, Path)
        return self.path


@dataclass
class ComparableResource:
    """A uniform wrapper around any game file/resource we can diff."""

    identifier: str  # e.g. folder/file.ext   or  resref.type inside capsule
    ext: str  # normalized lowercase extension  (for external files) or resource type extension
    data: bytes
    source_index: int = 0  # Which path this resource came from (for n-way comparison)


class CompositeModuleCapsule:
    """A capsule that aggregates resources from multiple related module files."""

    def __init__(self, primary_module_path: CaseAwarePath):
        """Initialize with a primary module file, finding all related files."""
        self.primary_path: Path = primary_module_path
        self.related_files: list[CaseAwarePath] = find_related_module_files(primary_module_path)
        self._capsules: dict[Path, Capsule] = {}

        # Load all related capsules
        for file_path in self.related_files:
            try:
                self._capsules[file_path] = Capsule(file_path)
            except Exception:  # noqa: BLE001, PERF203, S112
                print(f"Cannot load {file_path} as capsule!")
                print("Full traceback:")
                for line in traceback.format_exc().splitlines():
                    print(f"  {line}")
                continue

    def __iter__(self):
        """Iterate over all resources from all related capsules."""
        for capsule in self._capsules.values():
            yield from capsule

    @property
    def name(self) -> str:
        """Get the display name for this composite capsule."""
        return self.primary_path.name


class CompareFunc(Protocol):
    def __call__(self, a: bytes, b: bytes, /) -> bool:  # pyright: ignore[reportReturnType]
        """Return True if *a* equals *b*, False otherwise."""


@dataclass
class CachedFileComparison:
    """Represents a single file comparison for caching."""

    rel_path: str  # Relative path of the file
    status: str  # "identical", "modified", "missing_left", "missing_right"
    ext: str  # File extension
    left_exists: bool
    right_exists: bool


# ---------------------------------------------------------------------------
# Format-aware comparers
# ---------------------------------------------------------------------------


def _compare_gff(a: bytes, b: bytes) -> bool:
    left_gff = gff.read_gff(a)
    right_gff = gff.read_gff(b)
    comparison_result = GFFComparisonResult()
    are_same = left_gff.compare(right_gff, lambda *_a, **_k: None, comparison_result=comparison_result)
    return are_same and not comparison_result.has_field_differences()


def _compare_2da(a: bytes, b: bytes) -> bool:
    return twoda.read_2da(a).compare(twoda.read_2da(b), lambda *_a, **_k: None)


def _compare_tlk(a: bytes, b: bytes) -> bool:
    return tlk.read_tlk(a).compare(tlk.read_tlk(b), lambda *_a, **_k: None)


def _compare_lip(a: bytes, b: bytes) -> bool:
    return lip.read_lip(a).compare(lip.read_lip(b), lambda *_a, **_k: None)


_HANDLERS: Mapping[str, CompareFunc] = {
    # extensions mapped to compare function
    **dict.fromkeys(gff.GFFContent.get_extensions(), _compare_gff),
    "2da": _compare_2da,
    "tlk": _compare_tlk,
    "lip": _compare_lip,
}


class DiffDispatcher:
    """Dispatch comparison to best available handler."""

    @staticmethod
    def equals(res_a: ComparableResource, res_b: ComparableResource) -> bool:
        if res_a.ext.casefold() == res_b.ext.casefold():
            cmp = _HANDLERS.get(res_a.ext)
            if cmp is not None:
                try:
                    return cmp(res_a.data, res_b.data)
                except Exception:  # noqa: BLE001, S110
                    pass
        # Fallback - hash compare
        return generate_hash(res_a.data) == generate_hash(res_b.data)


# ---------------------------------------------------------------------------
# Resource walker
# ---------------------------------------------------------------------------


class ResourceWalker:
    """Yield ComparableResource objects from any supported path type."""

    def __init__(self, root: Path, *, other_root: Path | None = None):
        self.root = root
        self.other_root = other_root  # Used to determine if composite loading should be enabled

    # public API
    def __iter__(self) -> Iterator[ComparableResource]:
        if is_capsule_file(self.root.name):
            yield from self._from_capsule(self.root)
        elif self.root.is_file():
            yield self._from_file(self.root, base_prefix="")
        elif self._looks_like_install(self.root):
            yield from self._from_install(self.root)
        else:  # directory
            yield from self._from_directory(self.root)

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _looks_like_install(path: Path) -> bool:
        return bool(path.is_dir()) and bool(path.joinpath("chitin.key").is_file())

    @staticmethod
    def _is_in_rims_folder(file_path: Path) -> bool:
        """Check if the file is in a 'rims' folder (case-insensitive)."""
        return file_path.parent.name.lower() == "rims"

    def _should_use_composite_loading(self, file_path: Path) -> bool:
        """Determine if composite module loading should be used.

        Only use composite loading when comparing module files to other module files.
        """
        if self.other_root is None:
            return True  # Default to composite loading if no comparison context

        # Check if the other root is also a module file
        if self.other_root.is_file() and is_capsule_file(self.other_root.name):
            # Both are capsule files - check if they're both module files (not in rims folder)
            return not self._is_in_rims_folder(self.other_root)

        # Other root is not a module file (directory, installation, etc.)
        return False

    def _from_file(self, file_path: Path, *, base_prefix: str) -> ComparableResource:
        ext = file_path.suffix.casefold().lstrip(".")
        identifier = f"{base_prefix}{file_path.name}" if base_prefix else file_path.name
        return ComparableResource(identifier, ext, file_path.read_bytes())

    def _from_directory(self, dir_path: Path) -> Iterable[ComparableResource]:
        for f in sorted(dir_path.rglob("*")):
            if f.is_file():
                rel = f.relative_to(dir_path).as_posix()
                yield self._from_file(f, base_prefix=f"{rel[: -len(f.name)]}")

    def _from_capsule(self, file_path: Path) -> Iterable[ComparableResource]:
        # Check if this is a RIM file that should use composite module loading
        # Only use composite loading if both paths are module files
        should_use_composite = is_rim_file(file_path.name) and not self._is_in_rims_folder(file_path) and self._should_use_composite_loading(file_path)

        if should_use_composite:
            # Use CompositeModuleCapsule to include related module files
            composite = CompositeModuleCapsule(CaseAwarePath(file_path))
            for res in composite:
                resname = res.resname()
                ext = res.restype().extension.casefold()
                identifier = f"{composite.name}/{resname}.{ext}"
                yield ComparableResource(identifier, ext, res.data())
        else:
            # Use regular single capsule loading
            cap = Capsule(file_path)
            for res in cap:
                resname = res.resname()
                ext = res.restype().extension.casefold()
                identifier = f"{file_path.name}/{resname}.{ext}"
                yield ComparableResource(identifier, ext, res.data())

    def _from_install(self, install_root: Path) -> Iterable[ComparableResource]:
        inst = Installation(install_root)
        # Walk key high-level locations: override, modules, rims, lips, etc.
        # Iterate installation to get FileResource objects.

        def _iter_resources(it: Iterable[FileResource]):
            for r in it:
                identifier = r.filepath().relative_to(install_root).as_posix()
                yield ComparableResource(identifier, r.restype().extension.casefold(), r.data())

        # Override files
        yield from _iter_resources(inst.override_resources())
        # Module capsules
        for mod_name in inst.modules_list():
            cap = inst.module_path() / mod_name
            yield from self._from_capsule(Path(cap))
        # RIMs - Skip the rims folder as it often contains corrupted/incompatible files
        # I don't believe the game uses these even.
        # for rim in inst.rims_path().iterdir():
        #     if is_capsule_file(rim.name):
        #         yield from self._from_capsule(Path(rim))
        # Lips
        for lip_file in inst.lips_path().iterdir():
            if lip_file.suffix.casefold() == ".mod":
                yield from self._from_capsule(Path(lip_file))
        # Override subfolders already handled in override_resources


# ---------------------------------------------------------------------------
# Core comparison context and dataclasses
# ---------------------------------------------------------------------------


@dataclass
class DiffContext:
    """Context for diff operations, grouping related file paths."""

    file1_rel: Path
    file2_rel: Path
    ext: str
    resname: str | None = None

    # Resolution order location types (for resolution-aware diffing)
    file1_location_type: str | None = None  # Location type in vanilla/older install (Override, Modules (.mod), etc.)
    file2_location_type: str | None = None  # Location type in modded/newer install
    file1_filepath: Path | None = None  # Full filepath in base installation (for StrRef reference finding)
    file2_filepath: Path | None = None  # Full filepath in target installation (for module name extraction)
    file1_installation: Installation | None = None  # Base installation object (for StrRef reference finding)
    file2_installation: Installation | None = None  # Target installation object (for StrRef/2DA reference finding)

    @property
    def where(self) -> str:
        """Get the display name for the resource being compared.

        Returns full path context: install_name/location/container/resource.ext
        Uses file2_rel (modded/target) as it's more relevant for patch generation.
        """
        if self.resname:
            # For resources inside containers (capsules/BIFs)
            # file2_rel contains full path like: swkotor/data/2da.bif
            # Build: swkotor/data/2da.bif/appearance.2da
            return f"{self.file2_rel}/{self.resname}.{self.ext}"
        # For loose files, just return the full path from modded/target
        return str(self.file2_rel)


# ---------------------------------------------------------------------------
# Text content utilities
# ---------------------------------------------------------------------------


def is_text_content(data: bytes) -> bool:
    """Heuristically determine if data is text content."""
    if len(data) == 0:
        return True

    with suppress(UnicodeDecodeError):
        # Try to decode as UTF-8 first
        data.decode("utf-8")
        return True

    with suppress(UnicodeDecodeError):
        # Try Windows-1252 (common for KOTOR text files)
        data.decode("windows-1252")
        return True

    # Check for high ratio of printable ASCII characters
    # ASCII printable range: 32-126, plus tab(9), LF(10), CR(13)
    PRINTABLE_ASCII_MIN = 32
    PRINTABLE_ASCII_MAX = 126
    TEXT_THRESHOLD = 0.7

    printable_count: int = sum(1 for b in data if PRINTABLE_ASCII_MIN <= b <= PRINTABLE_ASCII_MAX or b in (9, 10, 13))
    return printable_count / len(data) > TEXT_THRESHOLD


def read_text_lines(filepath: Path) -> list[str]:
    """Read text file lines with encoding fallback."""
    try:
        return filepath.read_bytes().decode("utf-8", errors="ignore").splitlines(keepends=True)
    except Exception:  # noqa: BLE001
        try:
            return filepath.read_bytes().decode("windows-1252", errors="ignore").splitlines(keepends=True)
        except Exception:  # noqa: BLE001
            return []


def compare_text_content(
    data1: bytes,
    data2: bytes,
    where: str,
    log_func: Callable[[str], None],
) -> bool:
    """Compare text content using line-by-line diffing."""
    MAX_LINE_LENGTH = 200  # Maximum characters to display per line

    try:
        # Try UTF-8 first
        text1 = data1.decode("utf-8", errors="ignore")
        text2 = data2.decode("utf-8", errors="ignore")
    except (UnicodeDecodeError, AttributeError):
        try:
            # Fallback to Windows-1252
            text1 = data1.decode("windows-1252", errors="ignore")
            text2 = data2.decode("windows-1252", errors="ignore")
        except (UnicodeDecodeError, AttributeError):
            # Last resort - treat as binary
            return data1 == data2

    if text1 == text2:
        return True

    # Use difflib for detailed text comparison
    lines1 = text1.splitlines(keepends=True)
    lines2 = text2.splitlines(keepends=True)

    diff = difflib.unified_diff(
        lines1,
        lines2,
        fromfile=f"(old){where}",
        tofile=f"(new){where}",
        lineterm="",
    )

    diff_lines = list(diff)
    if diff_lines:
        log_func(f"^ '{where}': Text content differs ^", separator=True)  # pyright: ignore[reportCallIssue]
        for line in diff_lines:
            # Truncate excessively long lines (likely binary data that slipped through)
            if len(line) > MAX_LINE_LENGTH:
                truncated = line[:MAX_LINE_LENGTH] + f"... (truncated, {len(line)} chars total)"
                log_func(truncated)
            else:
                log_func(line.rstrip())
        return False

    return True


# ---------------------------------------------------------------------------
# Resource reader utilities
# ---------------------------------------------------------------------------


def get_resource_reader_function(ext: str) -> Callable[[bytes], GFF | TwoDA | TLK | LIP | ERF | RIM | SSF | MDL | NCS | BWM | LTR | LYT | VIS] | None:
    """Dynamically get the appropriate resource reader function for an extension."""
    # Map extensions to their reader functions
    reader_map: dict[str, Callable[[bytes], Any]] = {
        "2da": lambda data: __import__("pykotor.resource.formats.twoda.twoda_auto", fromlist=["read_2da"]).read_2da(data),
        "dwk": lambda data: __import__("pykotor.resource.formats.bwm.bwm_auto", fromlist=["read_bwm"]).read_bwm(data),
        "wok": lambda data: __import__("pykotor.resource.formats.bwm.bwm_auto", fromlist=["read_bwm"]).read_bwm(data),
        "erf": lambda data: __import__("pykotor.resource.formats.erf.erf_auto", fromlist=["read_erf"]).read_erf(data),
        "gff": lambda data: __import__("pykotor.resource.formats.gff.gff_auto", fromlist=["read_gff"]).read_gff(data),
        "mod": lambda data: __import__("pykotor.resource.formats.erf.erf_auto", fromlist=["read_erf"]).read_erf(data),
        "sav": lambda data: __import__("pykotor.resource.formats.erf.erf_auto", fromlist=["read_erf"]).read_erf(data),
        "rim": lambda data: __import__("pykotor.resource.formats.rim.rim_auto", fromlist=["read_rim"]).read_rim(data),
        "lip": lambda data: __import__("pykotor.resource.formats.lip.lip_auto", fromlist=["read_lip"]).read_lip(data),
        "ltr": lambda data: __import__("pykotor.resource.formats.ltr.ltr_auto", fromlist=["read_ltr"]).read_ltr(data),
        "lyt": lambda data: __import__("pykotor.resource.formats.lyt.lyt_auto", fromlist=["read_lyt"]).read_lyt(data),
        "mdl": lambda data: __import__("pykotor.resource.formats.mdl.mdl_auto", fromlist=["read_mdl"]).read_mdl(data),
        "ncs": lambda data: __import__("pykotor.resource.formats.ncs.ncs_auto", fromlist=["read_ncs"]).read_ncs(data),
        "pwk": lambda data: __import__("pykotor.resource.formats.bwm.bwm_auto", fromlist=["read_bwm"]).read_bwm(data),
        "ssf": lambda data: __import__("pykotor.resource.formats.ssf.ssf_auto", fromlist=["read_ssf"]).read_ssf(data),
        "tlk": lambda data: __import__("pykotor.resource.formats.tlk.tlk_auto", fromlist=["read_tlk"]).read_tlk(data),
        "vis": lambda data: __import__("pykotor.resource.formats.vis.vis_auto", fromlist=["read_vis"]).read_vis(data),
    }

    return reader_map.get(ext.lower())


# ---------------------------------------------------------------------------
# Path and file utilities
# ---------------------------------------------------------------------------


def relative_path_from_to(
    src: PurePath,
    dst: PurePath,
) -> Path:
    """Calculate relative path from src to dst."""
    src_parts: list[str] = list(PurePath(src).parts)
    dst_parts: list[str] = list(PurePath(dst).parts)

    common_length: int = next(
        (i for i, (src_part, dst_part) in enumerate(zip(src_parts, dst_parts)) if src_part != dst_part),
        len(src_parts),
    )
    rel_parts: list[str] = dst_parts[common_length:]
    return Path(*rel_parts)


def visual_length(
    s: str,
    tab_length: int = 8,
) -> int:
    """Calculate visual length of string accounting for tabs."""
    if "\t" not in s:
        return len(s)

    parts: list[str] = s.split("\t")
    vis_length: int = sum(len(part) for part in parts)
    for part in parts[:-1]:
        vis_length += tab_length - (len(part) % tab_length)
    return vis_length


def walk_files(root: Path) -> set[str]:
    """Walk all files in a directory tree."""
    if not root.exists():
        return set()
    if root.is_file():
        return {root.name.casefold()}
    return {f.relative_to(root).as_posix().casefold() for f in root.rglob("*") if f.is_file()}


def ext_of(path: Path) -> str:
    """Extract extension from path."""
    s = path.suffix.casefold()
    return s[1:] if s.startswith(".") else s


def should_skip_rel(_rel: str) -> bool:
    """Check if a relative path should be skipped.

    Note: Currently unused but kept for future filtering capabilities.
    """
    return False


def print_udiff(
    from_file: Path,
    to_file: Path,
    label_from: str,
    label_to: str,
    log_func: Callable[[str], None],
) -> None:
    """Print unified diff between two files."""
    a = read_text_lines(from_file)
    b = read_text_lines(to_file)
    if not a and not b:
        return
    diff: Iterator[str] = difflib.unified_diff(
        a,
        b,
        fromfile=str(label_from),
        tofile=str(label_to),
        lineterm="",
    )
    for line in diff:
        log_func(line)


def diff_data(  # noqa: PLR0913
    data1: bytes | Path,
    data2: bytes | Path,
    context: DiffContext,
    *,
    log_func: Callable,
    compare_hashes: bool = True,
    modifications_by_type: ModificationsByType | None = None,
    incremental_writer: IncrementalTSLPatchDataWriter | None = None,
) -> bool | None:
    """Compare two resources with appropriate format-specific handling.

    Args:
        data1: First resource data or path
        data2: Second resource data or path
        context: Diff context with file information
        log_func: Logging function callback
        compare_hashes: Whether to compare hashes for unsupported types
        modifications_by_type: Optional ModificationsByType object for collecting changes
        incremental_writer: Optional incremental writer for immediate file/INI writes

    Returns:
        True if identical, False if different, None if error

    Complexity is unavoidable due to many file formats and fallback strategies.
    """
    where = context.where

    if not data1 and not data2:
        return True
    if not data1:
        log_func(f"[Error] Cannot determine data for '{where}' in '{context.file1_rel}'")
        return None
    if not data2:
        log_func(f"[Error] Cannot determine data for '{where}' in '{context.file2_rel}'")
        return None

    # Fast path: For large binary files (audio, video), check file size first before reading
    LARGE_BINARY_FORMATS = ("wav", "mp3", "bik", "mve", "tga", "tpc")
    if context.ext in LARGE_BINARY_FORMATS and isinstance(data1, Path) and isinstance(data2, Path):
        # Check file sizes first - if different, no need to read the files
        try:
            size1 = data1.stat().st_size
            size2 = data2.stat().st_size
            if size1 != size2:
                if not compare_hashes:
                    return True  # Sizes differ but not comparing hashes
                log_func(f"'{context.where}': File sizes differ ({size1} vs {size2} bytes)")
                return False
        except Exception:  # noqa: BLE001, PERF203, S110, S112
            pass  # Fall through to normal comparison

    # Convert Path to bytes if needed
    if isinstance(data1, Path):
        data1 = data1.read_bytes()
    if isinstance(data2, Path):
        data2 = data2.read_bytes()

    # Check if this is a GFF type (handled specially for backwards compatibility)
    if context.ext in gff_types:
        gff1: gff.GFF | None = None
        gff2: gff.GFF | None = None
        try:
            gff1 = gff.read_gff(data1)
        except Exception as e:  # noqa: BLE001, PERF203, S112
            log_func(f"[Error] loading GFF {context.file1_rel.parent / where}!\n{universal_simplify_exception(e)}")
            log_func("Full traceback:")
            for line in traceback.format_exc().splitlines():
                log_func(f"  {line}")
            return None
        try:
            gff2 = gff.read_gff(data2)
        except Exception as e:  # noqa: BLE001, PERF203, S112
            log_func(f"[Error] loading GFF {context.file2_rel.parent / where}!\n{universal_simplify_exception(e)}")
            log_func("Full traceback:")
            for line in traceback.format_exc().splitlines():
                log_func(f"  {line}")
            return None
        if not gff1 and not gff2:
            log_func(f"Both GFF resources missing in memory:\t'{context.where}'")
            return None
        if not gff1:
            log_func(f"GFF resource missing in memory:\t'{context.file1_rel.parent / where}'")
            return None
        if not gff2:
            log_func(f"GFF resource missing in memory:\t'{context.file2_rel.parent / where}'")
            return None
        # Extract just the filename from context.where to avoid duplication in field paths
        # If context.where is "swkotor\Override\journal.gui", use just "journal.gui" as the root path
        compare_path = PureWindowsPath(Path(str(context.where)).name)
        comparison_result = GFFComparisonResult()
        if not (gff1 and gff2):
            return True
        are_same = gff1.compare(gff2, log_func, compare_path, comparison_result=comparison_result)
        if are_same and not comparison_result.has_field_differences():
            return True

        # Generate INI modifications if requested (log BEFORE final separator)
        if modifications_by_type is None:
            # Log final separator AFTER all patch info
            log_func(f"^ '{context.where}': GFF is different ^", separator=True)
            return False

        try:
            analyzer = DiffAnalyzerFactory.get_analyzer("gff")
            if analyzer is None:
                # Log final separator AFTER all patch info
                log_func(f"^ '{context.where}': GFF is different ^", separator=True)
                return False

            strref_mappings: dict[int, int] = {}
            result: PatcherModifications | tuple[PatcherModifications, dict[int, int]] | None = analyzer.analyze(data1, data2, str(context.where))
            assert result is not None, f"Analyzer returned None for context: {context}"
            if isinstance(result, tuple):
                modifications, strref_mappings = result
                assert isinstance(modifications, PatcherModifications), (
                    f"`modifications` is not a PatcherModifications: {modifications} (type: {type(modifications)}) for context: {context}"
                )  # noqa: E501
            else:
                modifications = result
                assert isinstance(modifications, PatcherModifications), (
                    f"`modifications` is not a PatcherModifications: {modifications} (type: {type(modifications)}) for context: {context}"
                )  # noqa: E501

            if modifications is None:
                # Log final separator AFTER all patch info
                log_func(f"^ '{context.where}': GFF is different ^", separator=True)
                return False

            # File exists in both vanilla and modded - this is a PATCH, not an install
            log_func(f"\n[PATCH] {context.where}")
            log_func("  |-- !ReplaceFile: 0 (patch existing file, don't replace)")

            # Set destination based on MODDED installation location (file2)
            resource_name = Path(str(context.where)).name
            destination = _determine_destination_for_source(
                context.file2_rel,  # Use MODDED installation, not vanilla
                resource_name,
                log_func=log_func,
                location_type=context.file2_location_type,
                source_filepath=context.file2_filepath,
            )
            modifications.destination = destination
            modifications.sourcefile = resource_name  # Just the filename, not the full path
            # saveas should also be just the filename, NOT the full path
            modifications.saveas = resource_name

            assert isinstance(modifications, ModificationsGFF), (
                f"`modifications` is not a ModificationsGFF: {modifications} (type: {type(modifications)}) for context: {context}"
            )  # noqa: E501
            modifications_by_type.gff.append(modifications)

            modifiers: list | None = getattr(modifications, "modifiers", None)
            if modifiers:
                log_func(f"  |-- Modifications: {len(modifiers)} field/struct changes")

            # Determine which source file to copy to tslpatchdata
            source_to_copy = _determine_tslpatchdata_source(context.file1_rel, context.file2_rel)
            log_func(f"  +-- tslpatchdata: Will copy from {source_to_copy}")

            # Write immediately if using incremental writer
            if incremental_writer is not None:
                # Get source data (vanilla version)
                gff_source_data: bytes = data1 if isinstance(data1, bytes) else data1.read_bytes()
                source_path = context.file1_installation if context.file1_installation else context.file1_filepath
                incremental_writer.write_modification(modifications, gff_source_data, source_path)

        except Exception as e:  # noqa: BLE001, PERF203, S112
            log_func(f"[Error] Failed to generate GFF modifications for '{context.where}': {e.__class__.__name__}: {e}")
            log_func("Full traceback:")
            for line in traceback.format_exc().splitlines():
                log_func(f"  {line}")

        # Log final separator AFTER all patch info
        log_func(f"^ '{context.where}': GFF is different ^", separator=True)
        return False

    # Define known binary formats that should never be treated as text
    BINARY_FORMATS = {
        # Scripts and models
        "ncs", "mdl", "mdx",
        # Walkmesh formats
        "wok", "pwk", "dwk",
        # Textures
        "tga", "tpc", "txi",
        # Audio/Video
        "wav", "bik",
        # Capsule formats (should be handled by capsule reader, but fallback to binary if parsing fails)
        "erf", "rim", "mod", "sav",
        # All GFF-based formats
        *gff_types,
    }

    # Try to get a resource reader function for this extension
    reader_func = get_resource_reader_function(context.ext)

    if reader_func:
        try:
            # Try to parse both resources
            obj1 = reader_func(data1)
            obj2 = reader_func(data2)

            # Check if the parsed objects have ComparableMixin interface
            if isinstance(obj1, ComparableMixin) and isinstance(obj2, ComparableMixin):
                # Special handling for NCS files - provide summary instead of exhaustive diff
                if context.ext == "ncs":
                    assert isinstance(obj1, NCS), f"`obj1` is not a NCS: {obj1} (type: {type(obj1)}) for context: {context}"  # noqa: E501
                    assert isinstance(obj2, NCS), f"`obj2` is not a NCS: {obj2} (type: {type(obj2)}) for context: {context}"  # noqa: E501
                    # Capture comparison output to summarize it
                    comparison_lines: list[str] = []

                    def capture_log(*args, **kwargs):
                        buffer = StringIO()
                        print(*args, file=buffer, **kwargs)
                        comparison_lines.append(buffer.getvalue())

                    is_same = obj1.compare(obj2, capture_log)

                    if is_same:
                        return True

                    # Provide a summary of differences
                    log_func("NCS scripts differ:")
                    log_func(f"  Old: {len(obj1.instructions)} instructions")
                    log_func(f"  New: {len(obj2.instructions)} instructions")

                    # Show first few differences only
                    MAX_DIFF_LINES = 20
                    if len(comparison_lines) > MAX_DIFF_LINES:
                        for line in comparison_lines[:MAX_DIFF_LINES]:
                            log_func(line.rstrip())
                        log_func(f"  ... ({len(comparison_lines) - MAX_DIFF_LINES} more difference lines omitted)")
                    else:
                        for line in comparison_lines:
                            log_func(line.rstrip())

                    log_func(f"^ '{context.where}': {context.ext.upper()} is different ^", separator=True)
                    return False

                # Use the structured compare method for other files
                # Both obj1 and obj2 are already verified as ComparableMixin above
                # Since both come from the same reader_func, they should be the same type
                # Check that they're the same type to satisfy type checker
                if type(obj1) is not type(obj2):
                    log_func(f"[Error] Type mismatch in comparison: {type(obj1).__name__} vs {type(obj2).__name__}")
                    return False

                # Both objects are the same type, so compare will work correctly
                # Access the compare method from the base class to use the base signature (other: object)
                # This avoids type checker issues with subclass overrides that have specific types
                # Get the method from the class and call it with obj1 as self
                base_compare = ComparableMixin.compare
                if base_compare(obj1, obj2, log_func):
                    return True

                # Generate INI modifications if requested (log BEFORE final separator)
                if modifications_by_type is None:
                    # Log final separator AFTER all patch info
                    log_func(f"^ '{context.where}': {context.ext.upper()} is different ^", separator=True)
                    return False

                try:
                    analyzer = DiffAnalyzerFactory.get_analyzer(context.ext)
                    if analyzer is None:
                        # Log final separator AFTER all patch info
                        log_func(f"^ '{context.where}': {context.ext.upper()} is different ^", separator=True)
                        return False

                    modifications: PatcherModifications | tuple[PatcherModifications, dict[int, int]] | None = analyzer.analyze(data1, data2, str(context.where))
                    if modifications is None:
                        # Log final separator AFTER all patch info
                        log_func(f"^ '{context.where}': {context.ext.upper()} is different ^", separator=True)
                        return False

                    # Add to appropriate list based on resource type
                    if context.ext == "2da":
                        # 2DA files that exist in vanilla are PATCHED
                        log_func(f"\n[PATCH] {context.where}")
                        log_func("  |-- !ReplaceFile: 0 (patch existing 2DA)")

                        # Set destination based on MODDED installation location (file2)
                        resource_name = Path(str(context.where)).name
                        destination = _determine_destination_for_source(
                            context.file2_rel,  # Use MODDED installation, not vanilla
                            resource_name,
                            log_func=log_func,
                            location_type=context.file2_location_type,
                            source_filepath=context.file2_filepath,
                        )
                        assert isinstance(modifications, Modifications2DA), (
                            f"`modifications` is not a Modifications2DA: {modifications} (type: {type(modifications)}) for context: {context}"
                        )  # noqa: E501
                        modifications.destination = destination
                        modifications.sourcefile = resource_name  # Just the filename, not the full path
                        modifications_by_type.twoda.append(modifications)
                        twoda_modifiers: list[Modify2DA] = [m for m in modifications.modifiers if isinstance(m, Modify2DA)]

                        if twoda_modifiers:
                            log_func(f"  |-- Modifications: {len(twoda_modifiers)} row/column changes")

                        # Determine which source file to copy
                        source_to_copy = _determine_tslpatchdata_source(context.file1_rel, context.file2_rel)
                        log_func(f"  +-- tslpatchdata: Will copy from {source_to_copy}")

                        # Write immediately if using incremental writer
                        if incremental_writer is not None:
                            twoda_vanilla_bytes: bytes = data1 if isinstance(data1, bytes) else data1.read_bytes()
                            source_path = context.file1_installation if context.file1_installation else context.file1_filepath
                            modded_source_path = context.file2_installation if context.file2_installation else context.file2_filepath
                            log_func(f"[DEBUG] Passing to writer: source_path={source_path}, modded_source_path={modded_source_path}")
                            incremental_writer.write_modification(modifications, twoda_vanilla_bytes, source_path, modded_source_path)
                    elif context.ext == "tlk":
                        log_func(f"\n[PATCH] {context.where}")
                        log_func("  |-- Mode: Append entries (TSLPatcher design)")

                        # TLK analyzer returns tuple: (ModificationsTLK, strref_mappings)
                        if not isinstance(modifications, tuple):
                            msg = f"TLK analyzer must return tuple (ModificationsTLK, dict), got {type(modifications)}"
                            raise TypeError(msg)  # noqa: TRY301
                        mod_tlk, strref_mappings = modifications
                        assert isinstance(mod_tlk, ModificationsTLK), f"`mod_tlk` is not a ModificationsTLK: {mod_tlk} (type: {type(mod_tlk)}) for context: {context}"  # noqa: E501
                        assert isinstance(strref_mappings, dict), f"`strref_mappings` is not a dict: {strref_mappings} (type: {type(strref_mappings)}) for context: {context}"  # noqa: E501

                        # Store metadata for StrRef reference finding
                        # For diff entries, we need to search BOTH installations (file1 and file2)
                        # because references to the old StrRef might exist in either installation
                        source_installations: list[Installation] = []
                        if context.file1_installation is not None:
                            source_installations.append(context.file1_installation)
                        if context.file2_installation is not None:
                            source_installations.append(context.file2_installation)

                        # Store metadata in incremental_writer if available
                        if incremental_writer is not None and strref_mappings:
                            incremental_writer._tlk_metadata[id(mod_tlk)] = {  # noqa: SLF001
                                "strref_mappings": strref_mappings,
                                "source_installations": source_installations,
                                "source_filepath": context.file1_filepath,
                            }

                        modifications_by_type.tlk.append(mod_tlk)
                        tlk_modifiers: list[ModifyTLK] = [m for m in mod_tlk.modifiers if isinstance(m, ModifyTLK)]

                        if tlk_modifiers:
                            log_func(f"  |-- Modifications: {len(tlk_modifiers)} TLK entries")
                        log_func("  +-- tslpatchdata: append.tlk and/or replace.tlk will be generated")

                        # Write immediately if using incremental writer
                        # TLK will trigger linking patch creation via StrRef cache
                        if incremental_writer is not None:
                            # No source_data needed for TLK files (they generate append.tlk)
                            incremental_writer.write_modification(mod_tlk, None)
                    elif context.ext == "ssf":
                        # SSF files that exist in vanilla are PATCHED
                        log_func(f"\n[PATCH] {context.where}")
                        log_func("  |-- !ReplaceFile: 0 (patch existing SSF)")

                        # Set destination based on MODDED installation location (file2)
                        resource_name = Path(str(context.where)).name
                        destination = _determine_destination_for_source(
                            context.file2_rel,  # Use MODDED installation, not vanilla
                            resource_name,
                            log_func=log_func,
                            location_type=context.file2_location_type,
                            source_filepath=context.file2_filepath,
                        )
                        assert isinstance(modifications, ModificationsSSF), (
                            f"`modifications` is not a ModificationsSSF: {modifications} (type: {type(modifications)}) for context: {context}"
                        )  # noqa: E501
                        modifications.destination = destination
                        modifications.sourcefile = resource_name  # Just the filename, not the full path
                        modifications_by_type.ssf.append(modifications)
                        ssf_modifiers: list[ModifySSF] = [m for m in modifications.modifiers if isinstance(m, ModifySSF)]

                        if ssf_modifiers:
                            log_func(f"  |-- Modifications: {len(ssf_modifiers)} sound slot changes")

                        # Determine which source file to copy
                        source_to_copy = _determine_tslpatchdata_source(context.file1_rel, context.file2_rel)
                        log_func(f"  +-- tslpatchdata: Will copy from {source_to_copy}")

                        # Write immediately if using incremental writer
                        if incremental_writer is not None:
                            ssf_vanilla_bytes: bytes = data1 if isinstance(data1, bytes) else data1.read_bytes()
                            source_path = context.file1_installation if context.file1_installation else context.file1_filepath
                            incremental_writer.write_modification(modifications, ssf_vanilla_bytes, source_path)
                    elif context.ext in gff_types:
                        # GFF file exists in both vanilla and modded - this is a PATCH
                        log_func(f"\n[PATCH] {context.where}")
                        log_func("  |-- !ReplaceFile: 0 (patch existing file, don't replace)")

                        # Set destination based on MODDED installation location (file2)
                        resource_name = PurePath(str(context.where)).name
                        destination = _determine_destination_for_source(
                            context.file2_rel,  # Use MODDED installation, not vanilla
                            resource_name,
                            log_func=log_func,
                            location_type=context.file2_location_type,
                            source_filepath=context.file2_filepath,
                        )
                        assert isinstance(modifications, ModificationsGFF), (
                            f"`modifications` is not a ModificationsGFF: {modifications} (type: {type(modifications)}) for context: {context}"
                        )  # noqa: E501
                        modifications.destination = destination
                        modifications.sourcefile = resource_name  # Just the filename, not the full path
                        # saveas should also be just the filename, NOT the full path
                        modifications.saveas = resource_name

                        modifications_by_type.gff.append(modifications)
                        gff_modifiers: list[ModifyGFF] = [m for m in modifications.modifiers if isinstance(m, ModifyGFF)]

                        if gff_modifiers:
                            log_func(f"  |-- Modifications: {len(gff_modifiers)} field/struct changes")

                        # Determine which source file to copy
                        source_to_copy = _determine_tslpatchdata_source(context.file1_rel, context.file2_rel)
                        log_func(f"  +-- tslpatchdata: Will copy from {source_to_copy}")

                        # Write immediately if using incremental writer
                        if incremental_writer is not None:
                            gff2_source_data: bytes = data1 if isinstance(data1, bytes) else data1.read_bytes()
                            source_path = context.file1_installation if context.file1_installation else context.file1_filepath
                            incremental_writer.write_modification(modifications, gff2_source_data, source_path)

                except Exception as e:  # noqa: BLE001, PERF203, S112
                    log_func(f"[Error] Failed to generate {context.ext.upper()} modifications for '{context.where}': {e.__class__.__name__}: {e}")
                    log_func("Full traceback:")
                    for line in traceback.format_exc().splitlines():
                        log_func(f"  {line}")

                # Log final separator AFTER all patch info
                log_func(f"^ '{context.where}': {context.ext.upper()} is different ^", separator=True)
                return False

        except Exception as e:  # noqa: BLE001, PERF203, S112
            # Parsing failed, fall through to other comparison methods
            log_func(f"[Error] Could not parse {context.ext.upper()} for structured comparison at '{context.where}'")
            log_func(f"  Exception: {e.__class__.__name__}: {e}")
            # Show the original cause if available (for chained exceptions)
            if e.__cause__:
                log_func(f"  Caused by: {type(e.__cause__).__name__}: {e.__cause__}")
            log_func("  Full traceback:")
            for line in traceback.format_exc().splitlines():
                log_func(f"    {line}")

            # For known binary formats, skip text comparison and go straight to hash
            if context.ext.lower() in BINARY_FORMATS:
                log_func("  Falling back to hash comparison")
                if not compare_hashes:
                    return True
                if generate_hash(data1) != generate_hash(data2):
                    log_func(f"'{context.where}': SHA256 is different")
                    return False
                return True

    # Check if content appears to be text (but skip for known binary formats)
    if context.ext.lower() not in BINARY_FORMATS and is_text_content(data1) and is_text_content(data2):
        log_func(f"Comparing text content for '{context.where}'")
        return compare_text_content(data1, data2, str(context.where), log_func)

    # Fallback to hash comparison for binary content
    if compare_hashes and generate_hash(data1) != generate_hash(data2):
        log_func(f"'{context.where}': SHA256 is different")
        return False

    return True


def diff_files(
    file1: Path,
    file2: Path,
    *,
    log_func: Callable,
    compare_hashes: bool = True,
    modifications_by_type: ModificationsByType | None = None,
    incremental_writer: IncrementalTSLPatchDataWriter | None = None,
) -> bool | None:
    """Compare two files.

    Args:
        file1: First file path
        file2: Second file path
        log_func: Logging function callback
        compare_hashes: Whether to compare hashes for unsupported types
        modifications_by_type: ModificationsByType object for collecting changes
        incremental_writer: Optional incremental writer for immediate file/INI writes

    Returns:
        True if identical, False if different, None if error
    """
    c_file1_rel: Path = file1.relative_to(file2.parent) if file2.parent != file1.parent else file1
    c_file2_rel: Path = file2.relative_to(file1.parent) if file1.parent != file2.parent else file2

    if not file1.is_file():
        log_func(f"Missing file:\t{c_file1_rel}")
        return False
    if not file2.is_file():
        log_func(f"Missing file:\t{c_file2_rel}")
        return False

    # Prefer udiff output by default for text-like files (exclude 2DA; use TwoDA.compare)
    ext = c_file1_rel.suffix.casefold()[1:]
    if ext in {"txi"}:
        a = read_text_lines(file1)
        b = read_text_lines(file2)
        if a or b:
            diff = difflib.unified_diff(
                a,
                b,
                fromfile=str(f"(old){c_file1_rel}"),
                tofile=str(f"(new){c_file2_rel}"),
                lineterm="",
            )
            for line in diff:
                log_func(line)

    if is_capsule_file(c_file1_rel.name):
        # Implementation moved to separate function for clarity
        return diff_capsule_files(
            file1,
            file2,
            c_file1_rel,
            c_file2_rel,
            log_func=log_func,
            compare_hashes=compare_hashes,
            modifications_by_type=modifications_by_type,
            incremental_writer=incremental_writer,
        )

    ctx = DiffContext(c_file1_rel, c_file2_rel, c_file1_rel.suffix.casefold()[1:])
    return diff_data(
        file1,
        file2,
        ctx,
        log_func=log_func,
        compare_hashes=compare_hashes,
        modifications_by_type=modifications_by_type,
        incremental_writer=incremental_writer,
    )


def diff_capsule_files(  # noqa: C901, PLR0913
    c_file1: Path,
    c_file2: Path,
    c_file1_rel: Path,
    c_file2_rel: Path,
    *,
    log_func: Callable,
    compare_hashes: bool = True,
    modifications_by_type: ModificationsByType | None = None,
    incremental_writer: IncrementalTSLPatchDataWriter | None = None,
) -> bool | None:
    """Handle diffing of capsule files."""
    # Check if we should use composite module loading for each file individually
    use_composite_file1 = should_use_composite_for_file(c_file1, c_file2)
    use_composite_file2 = should_use_composite_for_file(c_file2, c_file1)

    if use_composite_file1:
        log_func(f"Using composite module loading for {c_file1_rel.name} ({c_file1_rel.stem}.rim + {c_file1_rel.stem}._s.rim + {c_file1_rel.stem}._dlg.erf)")
    if use_composite_file2:
        log_func(f"Using composite module loading for {c_file2_rel.name} ({c_file2_rel.stem}.rim + {c_file2_rel.stem}._s.rim + {c_file2_rel.stem}._dlg.erf)")

    if modifications_by_type is not None:
        capsule_destination: str | None = None
        capsule_source_path: Path | None = None

        if c_file2.suffix.lower() == ".mod":
            capsule_destination = str(PureWindowsPath(c_file2_rel.as_posix()))
            capsule_source_path = c_file2
        elif c_file1.suffix.lower() == ".mod":
            capsule_destination = str(PureWindowsPath(c_file1_rel.as_posix()))
            capsule_source_path = c_file2 if c_file2.is_file() else c_file1

        if capsule_destination is not None:
            _ensure_capsule_install(
                modifications_by_type,
                capsule_destination,
                capsule_path=capsule_source_path,
                log_func=log_func,
                incremental_writer=incremental_writer,
            )

    # Load capsules
    file1_capsule = load_capsule(CaseAwarePath(c_file1), use_composite=use_composite_file1, log_func=log_func)
    if file1_capsule is None:
        return None

    file2_capsule = load_capsule(CaseAwarePath(c_file2), use_composite=use_composite_file2, log_func=log_func)
    if file2_capsule is None:
        return None

    # Build dict of resources
    capsule1_resources: dict[str, FileResource] = {res.resname(): res for res in file1_capsule}
    capsule2_resources: dict[str, FileResource] = {res.resname(): res for res in file2_capsule}

    # Identify missing resources
    missing_in_capsule1: set[str] = capsule2_resources.keys() - capsule1_resources.keys()
    missing_in_capsule2: set[str] = capsule1_resources.keys() - capsule2_resources.keys()

    # Report missing resources
    for resref in sorted(missing_in_capsule1):
        res_ext: str = capsule2_resources[resref].restype().extension.upper()
        message = f"Resource missing:\t{c_file1_rel}\t{resref}\t{res_ext}"
        log_func(message)

        # Add to install folders - file exists in modded but not vanilla, needs to be installed
        if modifications_by_type is not None:
            file_resource: FileResource = capsule2_resources[resref]
            filename: str = f"{resref}.{res_ext.lower()}"

            # Get resource data for patch creation
            resource_data = file_resource.data()

            # Determine destination based on capsule location
            actual_source_path: Path = file_resource.filepath()
            parent_names_lower: list[str] = [parent.name.lower() for parent in actual_source_path.parents]
            destination: str = "Override"
            if "modules" in parent_names_lower:
                # Resource belongs in a module file
                destination = f"modules\\{actual_source_path.name}"
            elif "override" in parent_names_lower:
                # Resource belongs in Override folder
                destination = "Override"

            # Create context for patch creation
            ctx = DiffContext(c_file1_rel, c_file2_rel, res_ext.lower(), resref)

            # Add to install folder (will also create patch if supported)
            _add_to_install_folder(
                modifications_by_type,
                destination,
                filename,
                log_func=log_func,
                modded_data=resource_data,
                modded_path=actual_source_path,
                context=ctx,
                incremental_writer=incremental_writer,
            )

            # Extract and copy the file from capsule using incremental writer
            if incremental_writer is not None:
                # Copy file from capsule (will extract automatically)
                incremental_writer.add_install_file(destination, filename, actual_source_path)

    for resref in sorted(missing_in_capsule2):
        res_ext = capsule1_resources[resref].restype().extension.upper()
        message = f"Resource missing:\t{c_file2_rel}\t{resref}\t{res_ext}"
        log_func(message)

    # Check for differences in common resources
    is_same_result: bool | None = True
    common_resrefs: set[str] = capsule1_resources.keys() & capsule2_resources.keys()
    for resref in sorted(common_resrefs):
        res1: FileResource = capsule1_resources[resref]
        res2: FileResource = capsule2_resources[resref]
        ext: str = res1.restype().extension.casefold()
        ctx = DiffContext(c_file1_rel, c_file2_rel, ext, resref)
        result: bool | None = diff_data(
            res1.data(),
            res2.data(),
            ctx,
            log_func=log_func,
            compare_hashes=compare_hashes,
            modifications_by_type=modifications_by_type,
        )
        is_same_result = None if result is None else (result and is_same_result)

    return is_same_result


def should_use_composite_for_file(
    file_path: Path,
    other_file_path: Path,
) -> bool:
    """Determine if composite module loading should be used for a specific file.

    Only use composite loading for .rim files when comparing against .mod files.
    """
    # Check if this file is a .rim file (not in rims folder)
    if not is_capsule_file(file_path.name):
        return False
    if file_path.parent.name.lower() == "rims":
        return False
    if file_path.suffix.lower() != ".rim":
        return False

    # Check if the other file is a .mod file (not in rims folder)
    if not is_capsule_file(other_file_path.name):
        return False
    if other_file_path.parent.name.lower() == "rims":
        return False
    return other_file_path.suffix.lower() == ".mod"


def load_capsule(
    file_path: CaseAwarePath,
    *,
    use_composite: bool,
    log_func: Callable,
) -> Capsule | Any | None:
    """Load a capsule file, either as a simple Capsule or ModuleCapsuleWrapper."""
    try:
        if use_composite:
            return CompositeModuleCapsule(file_path)
        return Capsule(file_path)
    except ValueError as e:
        log_func(f"Could not load '{file_path}'. Reason: {universal_simplify_exception(e)}")
        return None


# ---------------------------------------------------------------------------
# Installation Logger
# ---------------------------------------------------------------------------


class InstallationLogger:
    """Logger that captures installation search output to a string."""

    def __init__(self):
        self.log_buffer: list[str] = []
        self.current_resource: str | None = None
        self.resource_logs: dict[str, list[str]] = {}

    def __call__(self, message: str) -> None:
        """Log a message and store it in the buffer."""
        self.log_buffer.append(message)

        # If this is a new resource being processed, start a new log entry
        if message.lower().startswith("processing resource: "):
            self.current_resource = message.split(": ", 1)[1].strip()
            self.resource_logs[self.current_resource] = []
        elif self.current_resource:
            self.resource_logs[self.current_resource].append(message)

    def get_resource_log(self, resource_name: str) -> str:
        """Get the log output for a specific resource."""
        if resource_name in self.resource_logs:
            return "\n".join(self.resource_logs[resource_name])
        return ""

    def clear(self) -> None:
        """Clear the log buffer."""
        self.log_buffer.clear()
        self.resource_logs.clear()
        self.current_resource = None


# ---------------------------------------------------------------------------
# Directory and Module comparison
# ---------------------------------------------------------------------------


def group_module_files(files: set[str]) -> dict[str, list[str]]:
    """Group module files by their root name.

    Args:
        files: Set of relative file paths

    Returns:
        Dict mapping module root names to lists of related files
    """
    module_groups: dict[str, list[str]] = {}

    for file_path in files:
        filename = Path(file_path).name
        if is_capsule_file(filename):
            root = get_module_root(Path(filename))
            if root not in module_groups:
                module_groups[root] = []
            module_groups[root].append(file_path)

    return module_groups


def is_modules_directory(dir_path: Path) -> bool:
    """Check if a directory is a modules directory."""
    return dir_path.name.lower() in ("modules", "module", "mods")


def apply_folder_resolution_order(
    files: set[str],
    log_func: Callable,
) -> set[str]:
    """Apply folder-level resolution order to module files.

    When both .mod and .rim/_s.rim/_dlg.erf files exist for the same module, .mod takes priority.
    Resolution order (for same base name):
      - .rim/_s.rim/_dlg.erf (treated as single entity)
      - .mod (HIGHEST - takes priority over .rim group)

    Args:
        files: Set of file paths to filter
        log_func: Logging function

    Returns:
        Filtered set with lower-priority files removed
    """
    module_groups: dict[str, list[str]] = {}
    non_module_files: list[str] = []

    def file_ext_match(name: str) -> str | None:
        """Return normalized extension if file matches required RIM group (*.rim, *_s.rim, *_dlg.erf), else None."""
        name_lower = name.lower()
        if name_lower.endswith(".mod"):
            return ".mod"
        if name_lower.endswith("_dlg.erf"):
            return "_dlg.erf"
        if name_lower.endswith("_s.rim"):
            return "_s.rim"
        if name_lower.endswith(".rim"):
            return ".rim"
        return None

    for file_path in files:
        file_name: str = Path(file_path).name
        ext: str | None = file_ext_match(file_name)
        if ext is not None:
            try:
                root: str = get_module_root(Path(file_path))
                if root not in module_groups:
                    module_groups[root] = []
                module_groups[root].append(file_path)
            except Exception as e:  # noqa: BLE001
                log_func(f"Warning: Could not determine module root for '{file_path}': {e.__class__.__name__}: {e}")
                non_module_files.append(file_path)
        else:
            non_module_files.append(file_path)

    resolved_files: set[str] = set(non_module_files)

    for root, group_files in module_groups.items():
        # Partition into .mod (highest priority) and rim group (exclusively .rim, _s.rim, _dlg.erf)
        mod_files: list[str] = [f for f in group_files if Path(f).name.lower().endswith(".mod")]
        rimlike_files: list[str] = [
            f
            for f in group_files
            if (Path(f).name.lower().endswith(".rim") and not Path(f).name.lower().endswith("_s.rim"))
            or Path(f).name.lower().endswith("_s.rim")
            or Path(f).name.lower().endswith("_dlg.erf")
        ]

        # Only files with the same basename (no extension) are grouped; above already enforced by get_module_root

        if mod_files or rimlike_files:
            log_func(f"\nFolder resolution for module '{root}':")
            log_func("  Files found:")
            for rim_file in rimlike_files:
                log_func(f"    - {Path(rim_file).name} (.rim/_s.rim/_dlg.erf)")
            for mod_file in mod_files:
                log_func(f"    - {Path(mod_file).name} (.mod)")

        if mod_files:
            # .mod exists - use it, ignore rimlike group
            if len(mod_files) > 1:
                log_func(f"  Warning: Multiple .mod files for module '{root}'")

            if rimlike_files:
                log_func(f"  Resolution: .mod takes priority -> Using '{Path(mod_files[0]).name}'")
                log_func(f"              (ignoring {len(rimlike_files)} .rim/_s.rim/_dlg.erf files)")
            else:
                log_func(f"  Resolution: Using '{Path(mod_files[0]).name}' (.mod file)")

            resolved_files.add(mod_files[0])
        else:
            # No .mod - use all .rim/_s.rim/_dlg.erf files
            if rimlike_files:
                log_func(f"  Resolution: No .mod found -> Using {len(rimlike_files)} .rim/_s.rim/_dlg.erf file(s)")
            for file_path in rimlike_files:
                resolved_files.add(file_path)

    return resolved_files


def diff_module_directories(  # noqa: PLR0913
    c_dir1: Path,
    c_dir2: Path,
    files_path1: set[str],
    files_path2: set[str],
    *,
    log_func: Callable,
    diff_capsule_files_func: Callable,
) -> tuple[bool | None, set[str]]:
    """Special diffing for modules dirs. Only do composite module loading for filenames sharing the same basename, and only for .mod, .rim, _s.rim, _dlg.erf."""
    # Acceptable extensions for composite module loading
    valid_exts: set[str] = {".mod", ".rim", "_s.rim", "_dlg.erf"}  # noqa: F841

    def get_module_basename(fname: str) -> str:
        lower = fname.lower()
        if lower.endswith(".mod"):
            return Path(fname).stem
        if lower.endswith("_dlg.erf"):
            return Path(fname).stem.replace("_dlg", "")
        if lower.endswith("_s.rim"):
            return Path(fname).stem.replace("_s", "")
        if lower.endswith(".rim"):
            return Path(fname).stem
        return Path(fname).stem

    is_same_result: bool | None = True
    files_to_skip: set[str] = set()

    # Resolve each side to proper files using the previous resolution order logic
    resolved_files1: set[str] = apply_folder_resolution_order(files_path1, log_func)
    resolved_files2: set[str] = apply_folder_resolution_order(files_path2, log_func)

    filtered_out1: set[str] = files_path1 - resolved_files1
    filtered_out2: set[str] = files_path2 - resolved_files2
    files_to_skip.update(filtered_out1)
    files_to_skip.update(filtered_out2)

    # Build {basename -> [file]} mapping for valid module extensions on each side
    def group_by_basename(files: set[str]) -> dict[str, list[str]]:
        grouped: dict[str, list[str]] = {}
        for f in files:
            fname = Path(f).name
            lower = fname.lower()
            # Get rid of .mod, .rim, _s.rim, _dlg.erf only
            base = None
            if lower.endswith(".mod"):
                base = fname[:-4]
            elif lower.endswith("_dlg.erf"):
                base = fname[:-8]
            elif lower.endswith("_s.rim"):
                base = fname[:-6]
            elif lower.endswith(".rim"):
                base = fname[:-4]
            if base is not None:
                grouped.setdefault(base.lower(), []).append(f)
        return grouped

    groups1 = group_by_basename(resolved_files1)
    groups2 = group_by_basename(resolved_files2)
    all_basenames: set[str] = set(groups1) | set(groups2)

    for basename in sorted(all_basenames):
        files1: list[str] = groups1.get(basename, [])
        files2: list[str] = groups2.get(basename, [])

        # No composite module logic unless both have >0, and at least two different extensions
        exts1 = {Path(f).name.lower().split(basename)[-1] for f in files1}
        exts2 = {Path(f).name.lower().split(basename)[-1] for f in files2}

        # Only consider .mod/.rim/_s.rim/_dlg.erf as per requirements
        kind1, kind2 = set(), set()
        for ext in exts1:
            if ext in (".mod", ".rim") or ext.endswith(("_s.rim", "_dlg.erf")):
                kind1.add(ext)
        for ext in exts2:
            if ext in (".mod", ".rim") or ext.endswith(("_s.rim", "_dlg.erf")):
                kind2.add(ext)

        # Composite module loading logic: only run for basenames that have any of these extensions on both sides
        if kind1 and kind2:
            # Does one side have .mod, the other has only rimlike?
            filenames1 = [f for f in files1 if Path(f).name.lower().endswith(".mod")]
            filenames2 = [f for f in files2 if Path(f).name.lower().endswith(".mod")]

            rimlike1 = [f for f in files1 if Path(f).name.lower().endswith(".rim") or Path(f).name.lower().endswith("_s.rim") or Path(f).name.lower().endswith("_dlg.erf")]
            rimlike2 = [f for f in files2 if Path(f).name.lower().endswith(".rim") or Path(f).name.lower().endswith("_s.rim") or Path(f).name.lower().endswith("_dlg.erf")]

            side_case = None
            if filenames1 and rimlike2:  # mod in #1, rimlike in #2
                side_case = (c_dir1, c_dir2, filenames1[0], rimlike2)
            elif filenames2 and rimlike1:  # mod in #2, rimlike in #1
                side_case = (c_dir2, c_dir1, filenames2[0], rimlike1)
            else:
                side_case = None

            if side_case:
                mod_dir, rim_dir, mod_file, rim_files = side_case
                # Pick 'main' .rim: the file that has extension ".rim" and not ending with "_s"
                main_rim: str | None = None
                for rf in rim_files:
                    pname = Path(rf).name
                    if pname.lower().endswith(".rim") and not pname.lower().endswith("_s.rim"):
                        main_rim = rf
                        break
                if not main_rim and rim_files:
                    # fallback: use first rimlike file (should not generally happen)
                    main_rim = rim_files[0]

                if main_rim:
                    mod_path: Path = mod_dir / mod_file
                    rim_path: Path = rim_dir / main_rim

                    # always use relative paths for both
                    c_file1_rel: Path = relative_path_from_to(rim_dir, mod_path)
                    c_file2_rel: Path = relative_path_from_to(mod_dir, rim_path)
                    # Compare using composite module loading via supplied function
                    # (Order: "main" side resource, composite side resource, rel1, rel2)
                    result: bool | None
                    if mod_dir is c_dir1:
                        # mod_dir1/mod_file vs rim_dir2/main_rim
                        result = diff_capsule_files_func(
                            mod_path,
                            rim_path,
                            c_file1_rel,
                            c_file2_rel,
                        )
                    else:
                        # mod_dir2/mod_file vs rim_dir1/main_rim
                        result = diff_capsule_files_func(
                            rim_path,
                            mod_path,
                            c_file2_rel,
                            c_file1_rel,
                        )
                    is_same_result = None if result is None else (is_same_result and result)
                    files_to_skip.update(files1)
                    files_to_skip.update(files2)
                else:
                    log_func(f"Warning: Could not find main rim for basename '{basename}', using normal comparison")

    return is_same_result, files_to_skip


def should_include_in_filtered_diff(
    file_path: str,
    filters: list[str] | None,
) -> bool:
    """Check if a file should be included based on filter criteria, using pathlib.Path everywhere."""
    file_path_obj: Path = Path(file_path)

    if not filters:
        return True  # No filters means include everything

    for filter_pattern in filters:
        filter_path: Path = Path(filter_pattern)

        # Direct filename match: check via pathlib equality or filename containment
        if filter_path.name.lower() == file_path_obj.name.lower():
            return True
        parent_names_lower = (parent.name.lower() for parent in file_path_obj.parents)
        if filter_path.name.lower() in parent_names_lower:
            return True

        # Module name match (for .rim/.mod/.erf files)
        if file_path_obj.suffix.lower() in {".rim", ".mod", ".erf"}:
            filename = file_path_obj.name
            try:
                root = get_module_root(Path(filename))
                if filter_path.name and filter_path.name.lower() == root.lower():
                    return True
            except Exception:  # noqa: BLE001, S112
                print(f"Could not call get_module_root for {file_path_obj.as_posix()}")
                print("Full traceback:")
                import traceback

                for line in traceback.format_exc().splitlines():
                    print(f"  {line}")
                continue

    return False


# ---------------------------------------------------------------------------
# Directory comparison with caching support
# ---------------------------------------------------------------------------


def diff_directories(
    dir1: Path,
    dir2: Path,
    *,
    filters: list[str] | None = None,
    log_func: Callable[[str], None],
    diff_files_func: Callable[[Path, Path], bool | None],
    diff_cache: DiffCache | None = None,
    modifications_by_type: ModificationsByType | None = None,
    incremental_writer: IncrementalTSLPatchDataWriter | None = None,
) -> bool | None:
    """Compare two directories recursively."""
    log_func(f"Finding differences in the '{dir1.name}' folders...")

    # Store relative paths instead of just filenames
    files_path1: set[str] = {f.relative_to(dir1).as_posix().casefold() for f in dir1.rglob("*") if f.is_file()}
    files_path2: set[str] = {f.relative_to(dir2).as_posix().casefold() for f in dir2.rglob("*") if f.is_file()}

    # Merge both sets
    all_files: set[str] = files_path1.union(files_path2)

    # Apply filters if provided
    if filters:
        filtered_files = {f for f in all_files if should_include_in_filtered_diff(f, filters)}
        if filtered_files != all_files:
            log_func(f"Applying filters: {filters}")
            log_func(f"Filtered from {len(all_files)} to {len(filtered_files)} files")
        all_files = filtered_files

    # Special handling for modules directories
    files_to_skip: set[str] = set()
    is_same_result: bool | None = True

    if is_modules_directory(dir1) or is_modules_directory(dir2):
        module_result, files_to_skip = diff_module_directories(
            dir1,
            dir2,
            files_path1,
            files_path2,
            log_func=log_func,
            diff_capsule_files_func=lambda *args, **kwargs: diff_capsule_files(
                *args,
                **kwargs,
                log_func=log_func,
                modifications_by_type=modifications_by_type,
                incremental_writer=incremental_writer,
            ),
        )
        is_same_result = module_result

    # Progress tracking
    PROGRESS_FILE_THRESHOLD: int = 100
    remaining_files: set[str] = all_files - files_to_skip

    # Separate files into existing and missing
    existing_in_both: list[str] = []
    missing_files: list[tuple[str, bool]] = []  # (rel_path, is_missing_from_dir1)

    for rel_path in sorted(remaining_files):
        file1_path: Path = dir1 / rel_path
        file2_path: Path = dir2 / rel_path

        if not file1_path.is_file():
            missing_files.append((rel_path, True))
        elif not file2_path.is_file():
            missing_files.append((rel_path, False))
        else:
            existing_in_both.append(rel_path)

    total_files: int = len(remaining_files)
    log_func(f"Comparing {total_files} files...")

    # Process files that exist in both directories
    for idx, rel_path in enumerate(existing_in_both, 1):
        log_func(f"Progress: {idx}/{total_files} files processed...")

        file1_path = dir1 / rel_path
        file2_path = dir2 / rel_path

        result: bool | None = diff_files_func(file1_path, file2_path)
        is_same_result = None if result is None else result and is_same_result

        # Record in cache if caching enabled
        if diff_cache is not None and diff_cache.files is not None:
            ext = Path(rel_path).suffix.casefold()[1:] if Path(rel_path).suffix else ""
            status = "identical" if result else "modified"
            diff_cache.files.append(
                CachedFileComparison(
                    rel_path=rel_path,
                    status=status,
                    ext=ext,
                    left_exists=True,
                    right_exists=True,
                )
            )

    # Report all missing files after comparisons
    for rel_path, is_missing_from_dir1 in sorted(missing_files):
        if is_missing_from_dir1:
            file1_path = dir1 / rel_path
            file2_path = dir2 / rel_path
            c_file1_rel = relative_path_from_to(dir2, file1_path)
            log_func(f"Missing file:\t{c_file1_rel}")

            # Add to install folders - file exists in modded (dir2) but not vanilla (dir1)
            if modifications_by_type is not None:
                _add_missing_file_to_install(
                    modifications_by_type,
                    rel_path,
                    log_func=log_func,
                    file2_path=Path(file2_path),
                    incremental_writer=incremental_writer,
                )

            if diff_cache is not None and diff_cache.files is not None:
                ext = Path(rel_path).suffix.casefold()[1:] if Path(rel_path).suffix else ""
                diff_cache.files.append(
                    CachedFileComparison(
                        rel_path=rel_path,
                        status="missing_left",
                        ext=ext,
                        left_exists=False,
                        right_exists=True,
                    )
                )
        else:
            file2_path = dir2 / rel_path
            c_file2_rel = relative_path_from_to(dir1, file2_path)
            log_func(f"Missing file:\t{c_file2_rel}")

            if diff_cache is not None and diff_cache.files is not None:
                ext = Path(rel_path).suffix.casefold()[1:] if Path(rel_path).suffix else ""
                diff_cache.files.append(
                    CachedFileComparison(
                        rel_path=rel_path,
                        status="missing_right",
                        ext=ext,
                        left_exists=True,
                        right_exists=False,
                    )
                )
        is_same_result = False

    if total_files > PROGRESS_FILE_THRESHOLD:
        log_func(f"Completed: {total_files}/{total_files} files processed.")

    return is_same_result


def diff_installs_with_objects(
    installation1: Installation,
    installation2: Installation,
    *,
    filters: list[str] | None = None,
    log_func: Callable[[str], None],
    diff_installs_func: Callable[[Installation, Installation], bool | None],  # noqa: ARG001
    compare_hashes: bool = True,
    modifications_by_type: ModificationsByType | None = None,
    incremental_writer: IncrementalTSLPatchDataWriter | None = None,
) -> bool | None:
    """Compare two installations using already loaded Installation objects.

    Always uses game's resource resolution order to ensure accurate comparison.
    Priority order (lowest to highest):
      1. Chitin (BIFs)
      2. Modules (.rim/_s.rim/_dlg.erf)
      3. Modules (.mod)
      4. Override (HIGHEST - always wins)

    InstallList Logic (2-way comparison):
      - File exists in installation2 but NOT in installation1 → [InstallList]
      - File exists in both → [GFFList]/[2DAList]/[SSFList]/[HACKList]
      - File exists in installation1 but NOT in installation2 → Removed (no action)

    Mapping to CLI arguments:
      - installation1 corresponds to --mine (vanilla/base)
      - installation2 corresponds to --older (modded/target)

    Args:
        installation1: First installation object (vanilla/base - from --mine)
        installation2: Second installation object (modded/target - from --older)
        filters: Optional list of resource filters
        log_func: Logging function
        diff_installs_func: Unused (kept for signature compatibility)
        compare_hashes: Whether to compare hashes for binary files
        modifications_by_type: Optional collection for TSLPatcher modifications
        incremental_writer: Optional incremental writer for immediate file/INI writes

    Returns:
        True if identical, False if different, None if errors occurred
    """
    log_func("Using resource resolution order (game priority) for comparison...")
    from pykotor.tslpatcher.diff.resolution import diff_installations_with_resolution  # noqa: PLC0415

    return diff_installations_with_resolution(
        [installation1, installation2],
        filters=filters,
        log_func=log_func,
        compare_hashes=compare_hashes,
        modifications_by_type=modifications_by_type,
        incremental_writer=incremental_writer,
    )


class DiffDirectoriesFunc(Protocol):
    """Protocol for diff_directories_func that accepts filters and other parameters."""

    def __call__(
        self,
        dir1: Path,
        dir2: Path,
        *,
        filters: list[str] | None = ...,
        **kwargs: Any,
    ) -> bool | None:
        """Compare two directories."""
        ...


def diff_installs_implementation(
    install_path1: Path,
    install_path2: Path,
    *,
    filters: list[str] | None = None,
    log_func: Callable[[str], None],
    diff_files_func: Callable[[Path, Path], bool | None],
    diff_directories_func: DiffDirectoriesFunc,
) -> bool | None:
    """Compare two KOTOR installations by diffing their standard directories."""
    rinstall_path1: CaseAwarePath = CaseAwarePath(install_path1).resolve()
    rinstall_path2: CaseAwarePath = CaseAwarePath(install_path2).resolve()
    log_func("")
    log_func((max(len(str(rinstall_path1)) + 29, len(str(rinstall_path2)) + 30)) * "-")
    log_func(f"Searching first install dir: {rinstall_path1}")
    log_func(f"Searching second install dir: {rinstall_path2}")
    if filters:
        log_func(f"Using filters: {filters}")
    log_func("")

    is_same_result: bool | None = True

    # Compare dialog.tlk
    if not filters or any("dialog.tlk" in f.lower() or "tlk" in f.lower() for f in filters):
        is_same_result = (
            diff_files_func(
                rinstall_path1.joinpath("dialog.tlk"),
                rinstall_path2 / "dialog.tlk",
            )
            and is_same_result
        )

    # Compare standard directories
    for dir_name in ["Modules", "Override", "Lips"]:
        mine = rinstall_path1 / dir_name
        older = rinstall_path2 / dir_name
        is_same_result = (
            diff_directories_func(
                mine,
                older,
                filters=filters,
            )
            and is_same_result
        )

    # Streamwaves (may be named streamvoice)
    streamwaves_path1 = rinstall_path1.joinpath("streamwaves") if rinstall_path1.joinpath("streamwaves").is_dir() else rinstall_path1.joinpath("streamvoice")
    streamwaves_path2 = rinstall_path2.joinpath("streamwaves") if rinstall_path2.joinpath("streamwaves").is_dir() else rinstall_path2.joinpath("streamvoice")
    is_same_result = (
        diff_directories_func(
            streamwaves_path1,
            streamwaves_path2,
            filters=filters,
        )
        and is_same_result
    )
    return is_same_result


# ---------------------------------------------------------------------------
# Resource resolution
# ---------------------------------------------------------------------------


def resolve_resource_with_installation(
    installation: Installation,
    resource_name: str,
    resource_type: ResourceType,
    *,
    module_root: str | None = None,
    installation_logger: InstallationLogger | None = None,
) -> tuple[bytes | None, str, str]:
    """Resolve a resource using an already-loaded Installation instance."""
    try:
        if installation_logger is None:
            installation_logger = InstallationLogger()

        installation_logger(f"Processing resource: {resource_name}.{resource_type.extension}")
        installation_logger(f"Resolving resource '{resource_name}.{resource_type.extension}' in installation...")

        resource_result: ResourceResult | None = installation.resource(
            resource_name,
            resource_type,
            module_root=module_root,
            logger=installation_logger,
        )

        if resource_result is not None:
            search_log = installation_logger.get_resource_log(f"{resource_name}.{resource_type.extension}")
            return resource_result.data, f"{resource_result.filepath}", search_log

        installation_logger(f"Resource '{resource_name}.{resource_type.extension}' not found in any location")
        search_log = installation_logger.get_resource_log(f"{resource_name}.{resource_type.extension}")

    except Exception as e:  # noqa: BLE001, PERF203, S112
        error_msg = f"Error resolving resource: {universal_simplify_exception(e)}"
        if installation_logger is not None:
            installation_logger(error_msg)
            search_log = installation_logger.get_resource_log(f"{resource_name}.{resource_type.extension}")
            installation_logger("Full traceback:")
            for line in traceback.format_exc().splitlines():
                installation_logger(f"  {line}")
        else:
            search_log = ""
            print("Full traceback:")
            for line in traceback.format_exc().splitlines():
                print(f"  {line}")
        return None, error_msg, search_log
    else:
        return None, "Not found in installation", search_log


def parse_resource_name_and_type(
    resource_name: str,
    resource_type: ResourceType | None,
    log_func: Callable[[str], None],
) -> tuple[str | None, ResourceType, str | None]:
    """Parse resource name and determine resource type."""
    if "." in resource_name and resource_type is None:
        name_part, ext_part = resource_name.rsplit(".", 1)
        try:
            resource_type = ResourceType.from_extension(ext_part)
        except ValueError:
            error_msg = f"Unknown extension: {ext_part}"
            log_func(f"Unknown resource type extension: {ext_part}")
            return None, ResourceType.INVALID, error_msg
        else:
            return name_part, resource_type, None
    elif resource_type is None:
        error_msg = "Cannot determine resource type"
        log_func(f"Cannot determine resource type for: {resource_name}")
        return None, ResourceType.INVALID, error_msg
    else:
        return resource_name, resource_type or ResourceType.INVALID, None


def determine_source_location(filepath: str) -> str:
    """Determine the source location string for logging based on filepath."""
    if "Override" in filepath:
        return f"Override: {filepath}"
    if "Modules" in filepath:
        return f"Module: {filepath}"
    if "rims" in filepath:
        return f"RIM: {filepath}"
    if "chitin.key" in filepath or "data" in filepath.lower():
        return f"Chitin: {filepath}"
    return f"Other: {filepath}"


def resolve_resource_in_installation_impl(
    installation_path: Path,
    resource_name: str,
    resource_type: ResourceType | None = None,
    log_func: Callable | None = None,
) -> tuple[bytes | None, str]:
    """Resolve a resource using KOTOR installation priority order."""
    if log_func is None:
        log_func = print

    try:
        installation = Installation(installation_path)

        name_part, resource_type, error_msg = parse_resource_name_and_type(resource_name, resource_type, log_func)
        if error_msg is not None or name_part is None or resource_type is None:
            return None, error_msg or "Failed to parse resource name and type"

        search_order = [
            SearchLocation.OVERRIDE,
            SearchLocation.CUSTOM_MODULES,
            SearchLocation.MODULES,
            SearchLocation.CHITIN,
            SearchLocation.TEXTURES_TPA,
            SearchLocation.TEXTURES_TPB,
            SearchLocation.TEXTURES_TPC,
            SearchLocation.LIPS,
            # SearchLocation.RIMS intentionally omitted - must be specified explicitly
        ]

        log_func(f"Resolving resource '{name_part}.{resource_type.extension}' in installation...")

        resource_result = installation.resource(name_part, resource_type, search_order)

        if resource_result is None:
            log_func(f"Resource '{name_part}.{resource_type.extension}' not found in installation")
            return None, "Not found in installation"

        data = resource_result.data
        filepath = str(resource_result.filepath)
        source = determine_source_location(filepath)

        log_func(f"Found '{name_part}.{resource_type.extension}' at: {source}")

    except Exception as e:  # noqa: BLE001
        error_msg = f"Error resolving resource: {universal_simplify_exception(e)}"
        log_func(error_msg)
        log_func("Full traceback:")
        for line in traceback.format_exc().splitlines():
            log_func(f"  {line}")
        return None, error_msg
    else:
        return data, source


# ---------------------------------------------------------------------------
# Container vs Installation comparison
# ---------------------------------------------------------------------------


def determine_composite_loading(container_path: Path) -> tuple[bool, list[Path], str]:
    """Determine if composite loading should be used and find related files."""
    module_root: str = get_module_root(container_path)
    container_dir: Path = container_path.parent
    related_files: list[Path] = []

    for ext in [".mod", ".rim", "_s.rim", "_dlg.erf"]:
        related_file = container_dir / f"{module_root}{ext}"
        if related_file.exists():
            related_files.append(related_file)

    use_composite = len(related_files) > 1
    return use_composite, related_files, module_root


def load_container_capsule(
    container_path: CaseAwarePath,
    *,
    use_composite: bool,
    log_func: Callable[[str], None],
) -> Capsule | CompositeModuleCapsule | None:
    """Load container capsule with appropriate loading method."""
    try:
        if use_composite:
            log_func(f"Using composite module loading for {container_path.name}")
            return CompositeModuleCapsule(container_path)
        return Capsule(container_path)
    except Exception as e:  # noqa: BLE001
        log_func(f"Error loading container '{container_path}': {universal_simplify_exception(e)}")
        log_func("Full traceback:")
        for line in traceback.format_exc().splitlines():
            log_func(f"  {line}")
        return None


def process_container_resource(  # noqa: PLR0913
    resource: FileResource,
    container_path: Path,
    installation: Installation,
    *,
    container_first: bool,
    module_root: str | None,
    installation_logger: InstallationLogger | None = None,
    log_func: Callable,
    diff_data_func: Callable,
) -> tuple[bool | None, bool]:
    """Process a single resource from the container.

    Returns:
        Tuple of (comparison_result, should_continue)
    """
    resname = resource.resname()
    restype = resource.restype()
    resource_identifier = f"{resname}.{restype.extension}"

    # Get resource data from container
    try:
        container_data = resource.data()
    except Exception as e:  # noqa: BLE001
        log_func(f"Error reading resource '{resource_identifier}' from container: {universal_simplify_exception(e)}")
        log_func("Full traceback:")
        for line in traceback.format_exc().splitlines():
            log_func(f"  {line}")
        return None, True

    # Resolve resource in installation
    installation_data, _resolution_info, search_log = resolve_resource_with_installation(
        installation,
        resname,
        restype,
        module_root=module_root,
        installation_logger=installation_logger,
    )

    if installation_data is None:
        log_func(f"Resource '{resource_identifier}' not found in installation - container only")
        return False, True

    # Compare the resources
    container_name = container_path.name
    container_rel = Path(f"{container_name}/{resource_identifier}")
    installation_rel = Path(f"installation/{resource_identifier}")

    try:
        if container_first:
            ctx = DiffContext(container_rel, installation_rel, restype.extension.casefold())
            result = diff_data_func(container_data, installation_data, ctx)
        else:
            ctx = DiffContext(installation_rel, container_rel, restype.extension.casefold())
            result = diff_data_func(installation_data, container_data, ctx)
    except Exception as e:  # noqa: BLE001
        log_func(f"Error comparing '{resource_identifier}': {universal_simplify_exception(e)}")
        log_func("Full traceback:")
        for line in traceback.format_exc().splitlines():
            log_func(f"  {line}")
        return None, True
    else:
        # Only show installation search logs if a diff was found
        if result is False and search_log:
            log_func(search_log)
        return result, True


def diff_container_vs_installation(
    container_path: Path,
    installation: Installation,
    *,
    container_first: bool = True,
    log_func: Callable[[str], None],
    diff_data_func: Callable[[bytes, bytes, DiffContext], bool],
) -> bool | None:
    """Compare all resources in a container against their resolved versions in an installation."""
    container_name = container_path.name
    log_func(f"Comparing container '{container_name}' against installation resolution...")

    # Determine composite loading strategy
    use_composite, related_files, module_root = determine_composite_loading(container_path)

    if use_composite:
        log_func(f"Found {len(related_files)} related module files for '{module_root}': {[f.name for f in related_files]}")

    # Load the container
    container_capsule = load_container_capsule(CaseAwarePath(container_path), use_composite=use_composite, log_func=log_func)
    if container_capsule is None:
        return None

    # Create installation logger to capture search output
    installation_logger = InstallationLogger()

    # Process all resources
    is_same_result: bool | None = True
    total_resources = 0
    compared_resources = 0

    # Determine module root for resource resolution
    resolution_module_root = None
    if is_capsule_file(container_path.name) and container_path.parent.name.lower() != "rims":
        resolution_module_root = get_module_root(container_path)
        log_func(f"Constraining search to module root '{resolution_module_root}'")

    for resource in container_capsule:
        total_resources += 1

        result, should_continue = process_container_resource(
            resource,
            container_path,
            installation,
            container_first=container_first,
            module_root=resolution_module_root,
            installation_logger=installation_logger,
            log_func=log_func,
            diff_data_func=diff_data_func,
        )

        if result is None:
            is_same_result = None
        elif not result:
            is_same_result = False

        if should_continue:
            compared_resources += 1

    log_func(f"Container comparison complete: {compared_resources}/{total_resources} resources processed")
    return is_same_result


def diff_resource_vs_installation(
    resource_path: Path,
    installation: Installation,
    *,
    resource_first: bool = True,
    log_func: Callable,
    diff_data_func: Callable,
) -> bool | None:
    """Compare a single resource file against its resolved version in an installation."""
    resource_name = resource_path.name
    log_func(f"Comparing resource '{resource_name}' against installation resolution...")

    # Read the standalone resource
    try:
        resource_data = resource_path.read_bytes()
    except Exception as e:  # noqa: BLE001
        log_func(f"Error reading resource file '{resource_path}': {universal_simplify_exception(e)}")
        log_func("Full traceback:")
        for line in traceback.format_exc().splitlines():
            log_func(f"  {line}")
        return None

    # Parse resource name and type
    if "." in resource_name:
        name_part, ext_part = resource_name.rsplit(".", 1)
        try:
            resource_type = ResourceType.from_extension(ext_part)
        except ValueError:
            log_func(f"Unknown resource type extension: {ext_part}")
            return False
    else:
        log_func(f"Cannot determine resource type for: {resource_name}")
        return False

    # Create installation logger
    installation_logger = InstallationLogger()

    # Resolve the resource in the installation
    installation_data, _resolution_info, search_log = resolve_resource_with_installation(
        installation,
        name_part,
        resource_type,
        installation_logger=installation_logger,
    )

    if installation_data is None:
        log_func(f"Resource '{resource_name}' not found in installation")
        return False

    # Perform the comparison
    resource_rel = Path(resource_path.name)
    installation_rel = Path(f"installation/{resource_name}")

    ext = resource_path.suffix.casefold()[1:] if resource_path.suffix else ""

    if resource_first:
        ctx = DiffContext(resource_rel, installation_rel, ext)
        result = diff_data_func(resource_data, installation_data, ctx)
    else:
        ctx = DiffContext(installation_rel, resource_rel, ext)
        result = diff_data_func(installation_data, resource_data, ctx)

    # Only show installation search logs if a diff was found
    if result is False and search_log:
        log_func(search_log)

    return result


# ---------------------------------------------------------------------------
# Path validation and Installation loading
# ---------------------------------------------------------------------------


def validate_paths(
    files_and_folders_and_installations: list[Path | Installation],
    log_func: Callable,
) -> bool | None:
    """Validate that all paths exist. Returns None if validation fails."""
    for idx, path in enumerate(files_and_folders_and_installations):
        if isinstance(path, Installation):
            # Installation objects should already be valid
            continue

        if not path.exists():
            log_func(f"Path {idx} ('{path}') does not exist on disk, cannot diff")
            return None
    return True


def load_installations(
    files_and_folders_and_installations: list[Path | Installation],
    log_func: Callable,
) -> list[PathInfo]:
    """Load installations for all paths, creating PathInfo objects.

    Args:
        files_and_folders_and_installations: List of Path or Installation objects
        log_func: Logging function

    Returns:
        List of PathInfo objects with loaded Installation objects where applicable
    """
    path_infos: list[PathInfo] = []

    for idx, path in enumerate(files_and_folders_and_installations):
        if isinstance(path, Installation):
            # Already an Installation object
            path_info = PathInfo.from_path_or_installation(path, idx)
            path_infos.append(path_info)
            log_func(f"Path {idx}: Using existing Installation object: {path.path()}")
        # Check if it's a KOTOR install directory
        elif is_kotor_install_dir(path):
            log_func(f"Path {idx}: Loading installation from: {path}")
            try:
                installation = Installation(path)
                path_info = PathInfo.from_path_or_installation(installation, idx)
                path_infos.append(path_info)
            except Exception as e:  # noqa: BLE001
                log_func(f"Error loading installation from path {idx} '{path}': {universal_simplify_exception(e)}")
                log_func("Full traceback:")
                for line in traceback.format_exc().splitlines():
                    log_func(f"  {line}")
                    # Create PathInfo for the raw path anyway
                    path_info = PathInfo.from_path_or_installation(path, idx)
                    path_infos.append(path_info)
        else:
            # Regular path (file or folder)
            path_info = PathInfo.from_path_or_installation(path, idx)
            path_infos.append(path_info)
            path_type = "File" if path.is_file() else ("Folder" if path.is_dir() else "Unknown")
            log_func(f"Path {idx}: Using {path_type} path: {path}")

    return path_infos


def handle_special_comparisons(
    mine: Path,
    older: Path,
    installation1: Installation | None,
    installation2: Installation | None,
    filters: list[str] | None,
    diff_container_vs_installation_func: Callable,
    diff_resource_vs_installation_func: Callable,
    diff_installs_with_objects_func: Callable,
) -> bool | None:
    """Handle special comparison cases (container vs installation, resource vs installation, etc.)."""
    # Handle container vs installation comparison
    if mine.is_file() and is_capsule_file(mine.name) and installation2:
        return diff_container_vs_installation_func(mine, installation2, container_first=True)
    if installation1 and older.is_file() and is_capsule_file(older.name):
        return diff_container_vs_installation_func(older, installation1, container_first=False)

    # Handle single resource vs installation comparison
    if mine.is_file() and not is_capsule_file(mine.name) and installation2:
        return diff_resource_vs_installation_func(mine, installation2, resource_first=True)
    if installation1 and older.is_file() and not is_capsule_file(older.name):
        return diff_resource_vs_installation_func(older, installation1, resource_first=False)

    # Handle installation vs installation comparison
    if installation1 and installation2:
        return diff_installs_with_objects_func(
            installation1,
            installation2,
            filters=filters,
        )

    return None  # Indicates no special case was handled


def collect_all_resources(
    path_infos: list[PathInfo],
    *,
    filters: list[str] | None = None,
    log_func: Callable,
) -> dict[str, dict[int, ComparableResource]]:
    """Collect all resources from N paths, handling composite modules and mixed path types.

    Returns a mapping of resource_id -> {path_index: ComparableResource}.
    Handles composite module grouping across paths (e.g., .rim from path0 + _s.rim from path1).

    Args:
        path_infos: List of PathInfo objects for all paths
        filters: Optional resource name filters
        log_func: Logging function

    Returns:
        dict[str, dict[int, ComparableResource]] mapping resource identifiers to path-indexed resources
    """
    all_resources: dict[str, dict[int, ComparableResource]] = {}

    for path_info in path_infos:
        log_func(f"Collecting resources from path {path_info.index} ({path_info.name})...")

        try:
            # Use ResourceWalker to collect resources from this path
            path = path_info.get_path()
            walker = ResourceWalker(path)

            resource_count: int = 0
            for resource in walker:
                # Apply filters if provided
                if filters and not should_include_in_filtered_diff(resource.identifier, filters):
                    continue

                # Update resource with source index
                resource.source_index = path_info.index

                # Add to collection
                if resource.identifier not in all_resources:
                    all_resources[resource.identifier] = {}
                all_resources[resource.identifier][path_info.index] = resource
                resource_count += 1

            log_func(f"  Collected {resource_count} resources from path {path_info.index}")

        except Exception as e:  # noqa: BLE001
            log_func(f"Error collecting resources from path {path_info.index}: {universal_simplify_exception(e)}")
            log_func("Full traceback:")
            for line in traceback.format_exc().splitlines():
                log_func(f"  {line}")
            continue

    total_unique_resources: int = len(all_resources)
    log_func(f"Total unique resources across all paths: {total_unique_resources}")

    return all_resources


def compare_resources_n_way(  # noqa: PLR0913
    all_resources: dict[str, dict[int, ComparableResource]],
    path_infos: list[PathInfo],
    *,
    log_func: Callable,
    compare_hashes: bool = True,
    modifications_by_type: ModificationsByType | None = None,
    incremental_writer: IncrementalTSLPatchDataWriter | None = None,
) -> bool | None:
    """Compare resources across N paths and generate patches for differences.

    Args:
        all_resources: Dict mapping resource_id -> {path_index: ComparableResource}
        path_infos: List of PathInfo objects
        log_func: Logging function
        compare_hashes: Whether to compare binary hashes
        modifications_by_type: Optional TSLPatcher modifications collection
        incremental_writer: Optional incremental writer

    Returns:
        True if all identical, False if differences found, None if errors
    """
    from itertools import combinations  # noqa: PLC0415

    is_same_result: bool | None = True
    processed_count: int = 0
    diff_count: int = 0
    error_count: int = 0

    log_func(f"Comparing {len(all_resources)} unique resources across {len(path_infos)} paths...")

    for resource_id, path_data in all_resources.items():
        processed_count += 1

        if processed_count % 100 == 0:
            log_func(f"Progress: {processed_count}/{len(all_resources)} resources processed...")

        # If resource only exists in one path, create install patch
        if len(path_data) == 1:
            path_index, resource = next(iter(path_data.items()))
            path_info: PathInfo = path_infos[path_index]

            log_func(f"\n[UNIQUE RESOURCE] {resource_id}")
            log_func(f"  Only in path {path_index} ({path_info.name})")
            log_func("  → Creating InstallList entry and patch")

            # Generate install patch for unique resource
            if modifications_by_type is not None:
                filename: str = Path(resource_id).name

                # Determine destination - default to Override for safety
                destination: str = "Override"

                resource_path: Path | None = None
                if incremental_writer is not None:
                    try:
                        base_path = path_info.get_path()
                        if path_info.is_file:
                            resource_path = base_path
                        elif path_info.is_folder:
                            resource_path = base_path / Path(resource.identifier)
                        else:
                            resource_path = None
                    except Exception:  # noqa: BLE001
                        resource_path = None

                # Create context for patch creation
                file1_rel: Path = Path(f"path{path_index}") / filename
                file2_rel: Path = Path("missing") / filename
                context: DiffContext = DiffContext(file1_rel, file2_rel, resource.ext)

                # Add to install folder
                _add_to_install_folder(
                    modifications_by_type,
                    destination,
                    filename,
                    log_func=log_func,
                    modded_data=resource.data,
                    modded_path=resource_path,
                    context=context,
                    incremental_writer=incremental_writer,
                )

                if incremental_writer is not None and resource_path is not None:
                    try:
                        if hasattr(resource_path, "is_file") and resource_path.is_file():
                            incremental_writer.add_install_file(destination, filename, resource_path)
                    except Exception as exc:  # noqa: BLE001
                        log_func(f"  [Warning] Failed to stage install file '{filename}': {universal_simplify_exception(exc)}")

            diff_count += 1
            is_same_result = False
            continue

        # Resource exists in multiple paths - compare all pairs
        found_differences: bool = False

        for (idx_a, resource_a), (idx_b, resource_b) in combinations(path_data.items(), 2):
            path_a: PathInfo = path_infos[idx_a]
            path_b: PathInfo = path_infos[idx_b]

            # Compare the two resources
            try:
                if DiffDispatcher.equals(resource_a, resource_b):
                    continue

                if not found_differences:
                    log_func(f"\n[DIFFERENT RESOURCE] {resource_id}")
                    found_differences = True

                log_func(f"  Difference between path {idx_a} ({path_a.name}) and path {idx_b} ({path_b.name})")

                # Generate modification patch using diff_data
                if modifications_by_type is not None:
                    file1_rel = Path(f"path{idx_a}_{path_a.name}") / Path(resource_id).name
                    file2_rel = Path(f"path{idx_b}_{path_b.name}") / Path(resource_id).name
                    context = DiffContext(file1_rel, file2_rel, resource_a.ext)

                    # Use diff_data to generate proper modifications
                    diff_data(
                        resource_a.data,
                        resource_b.data,
                        context,
                        log_func=log_func,
                        compare_hashes=compare_hashes,
                        modifications_by_type=modifications_by_type,
                        incremental_writer=incremental_writer,
                    )

                    # Always also add an InstallList entry so the file exists before patching
                    # Don't create patch here - diff_data already created one above
                    try:
                        destination = "Override"
                        filename = Path(resource_id).name
                        _add_to_install_folder(
                            modifications_by_type,
                            destination,
                            filename,
                            log_func=log_func,
                            modded_data=resource_b.data,
                            modded_path=None,
                            context=context,
                            incremental_writer=incremental_writer,
                            create_patch=False,  # Patch already created by diff_data above
                        )
                    except Exception as e:  # noqa: BLE001, S110
                        print(f"Error adding install entry for {resource_id}: {universal_simplify_exception(e)}")
                        print("Full traceback:")
                        for line in traceback.format_exc().splitlines():
                            print(f"  {line}")

            except Exception as e:  # noqa: BLE001
                log_func(f"Error comparing {resource_id} between paths {idx_a} and {idx_b}: {universal_simplify_exception(e)}")
                log_func("Full traceback:")
                for line in traceback.format_exc().splitlines():
                    log_func(f"  {line}")
                error_count += 1
                is_same_result = None

        if found_differences:
            diff_count += 1
            is_same_result = False

    # Summary
    log_func("")
    log_func("=" * 80)
    log_func("N-WAY COMPARISON SUMMARY")
    log_func("=" * 80)
    log_func(f"Total resources processed: {processed_count}")
    log_func(f"  Differences found: {diff_count}")
    log_func(f"  Errors: {error_count}")
    log_func("=" * 80)

    return is_same_result


def run_differ_from_args_impl(
    files_and_folders_and_installations: list[Path | Installation],
    *,
    filters: list[str] | None = None,
    log_func: Callable,
    compare_hashes: bool = True,
    modifications_by_type: ModificationsByType | None = None,
    incremental_writer: IncrementalTSLPatchDataWriter | None = None,
) -> bool | None:
    """Run differ with N paths of any type.

    Args:
        files_and_folders_and_installations: List of paths/installations (2 or more)
        filters: Optional resource name filters
        log_func: Logging function
        compare_hashes: Whether to compare binary hashes
        modifications_by_type: Optional TSLPatcher modifications collection
        incremental_writer: Optional incremental writer

    Returns:
        True if identical, False if different, None if errors
    """
    try:
        if len(files_and_folders_and_installations) < 2:  # noqa: PLR2004
            msg = f"At least 2 paths required for comparison, got {len(files_and_folders_and_installations)}"
            raise ValueError(msg)  # noqa: TRY301

        log_func(f"Starting {len(files_and_folders_and_installations)}-way comparison...")
        for idx, path in enumerate(files_and_folders_and_installations):
            path_type = "Installation" if isinstance(path, Installation) else ("Folder" if path.is_dir() else "File")
            log_func(f"  Path {idx}: {path} ({path_type})")
        log_func("-------------------------------------------")
        log_func("")

        # Validate all paths exist
        log_func("[DEBUG] Validating paths...")
        if validate_paths(files_and_folders_and_installations, log_func) is None:
            log_func("[ERROR] Path validation failed")
            return None
        log_func("[DEBUG] Path validation successful")

        # Load installations and create PathInfo objects
        log_func("[DEBUG] Loading installations...")
        path_infos: list[PathInfo] = load_installations(files_and_folders_and_installations, log_func)
        log_func(f"[DEBUG] Loaded {len(path_infos)} PathInfo objects")
        for info in path_infos:
            log_func(f"[DEBUG]   Path {info.index}: is_installation={info.is_installation}, is_folder={info.is_folder}, is_file={info.is_file}")

        # For Installation-to-Installation comparison, use resolution-aware comparison
        all_installations: list[Installation] = [path for path in files_and_folders_and_installations if isinstance(path, Installation)]
        log_func(f"[DEBUG] Found {len(all_installations)} Installation objects")

        if len(all_installations) >= 2:  # noqa: PLR2004
            log_func("Detected multiple installations - using resolution-aware comparison...")
            from pykotor.tslpatcher.diff.resolution import diff_installations_with_resolution  # noqa: PLC0415

            return diff_installations_with_resolution(
                files_and_folders_and_installations,
                filters=filters,
                log_func=log_func,
                compare_hashes=compare_hashes,
                modifications_by_type=modifications_by_type,
                incremental_writer=incremental_writer,
            )

        # Mixed path types or non-Installation comparison
        log_func("[DEBUG] Using non-Installation comparison (folder/file diffing)...")

        # Collect all resources from all paths
        log_func("[DEBUG] Collecting resources...")
        all_resources = collect_all_resources(path_infos, filters=filters, log_func=log_func)
        log_func(f"[DEBUG] Collected {len(all_resources)} unique resources")

        # Compare resources across all paths
        log_func("[DEBUG] Starting n-way comparison...")
        result: bool | None = compare_resources_n_way(
            all_resources,
            path_infos,
            log_func=log_func,
            compare_hashes=compare_hashes,
            modifications_by_type=modifications_by_type,
            incremental_writer=incremental_writer,
        )

    except Exception as e:  # noqa: BLE001
        log_func(f"[CRITICAL ERROR] Exception in run_differ_from_args_impl: {universal_simplify_exception(e)}")
        log_func("Full traceback:")
        for line in traceback.format_exc().splitlines():
            log_func(f"  {line}")
        return None
    else:
        log_func(f"[DEBUG] Comparison complete, result={result}")
        return result
