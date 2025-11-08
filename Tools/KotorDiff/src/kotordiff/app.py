#!/usr/bin/env python3
"""Main application logic for KotorDiff.

This module contains the core application flow, keeping __main__.py focused
exclusively on CLI argument parsing.
"""

from __future__ import annotations

import cProfile
import sys
import traceback

from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING, TextIO

from pykotor.common.misc import Game
from pykotor.extract.installation import Installation
from pykotor.resource.formats import gff
from pykotor.tools.reference_cache import StrRefReferenceCache

# Cache support removed
from pykotor.tslpatcher.diff.analyzers import analyze_tlk_strref_references
from pykotor.tslpatcher.diff.engine import (
    diff_data,
    get_module_root,
    run_differ_from_args_impl,
)
from pykotor.tslpatcher.diff.generator import (
    TSLPatchDataGenerator,
    determine_install_folders,
)
from pykotor.tslpatcher.writer import IncrementalTSLPatchDataWriter, ModificationsByType, TSLPatcherINISerializer
from utility.error_handling import universal_simplify_exception

if TYPE_CHECKING:
    from pykotor.tools.reference_cache import TwoDAMemoryReferenceCache
    from pykotor.tslpatcher.diff.engine import DiffContext


@dataclass
class KotorDiffConfig:
    """Configuration for KotorDiff operations."""

    paths: list[Path | Installation]
    tslpatchdata_path: Path | None = None
    ini_filename: str = "changes.ini"
    output_log_path: Path | None = None
    log_level: str = "info"
    output_mode: str = "full"
    use_colors: bool = True
    compare_hashes: bool = True
    use_profiler: bool = False
    filters: list[str] | None = None
    logging_enabled: bool = True
    use_incremental_writer: bool = False


gff_types: list[str] = list(gff.GFFContent.get_extensions())


def find_module_root(filename: str) -> str:
    """Wrapper around get_module_root for backwards compatibility."""
    return get_module_root(Path(filename))


@dataclass
class GlobalConfig:
    """Global configuration state for KotorDiff."""

    output_log: Path | None = None
    logging_enabled: bool | None = None
    config: KotorDiffConfig | None = None
    modifications_by_type: ModificationsByType | None = None


# Global configuration instance
_global_config: GlobalConfig = GlobalConfig()


def log_output(*args, **kwargs):
    """Log output to console and file."""
    # Filter out custom kwargs that print() doesn't accept
    separator_above = kwargs.pop("separator_above", False)
    separator = kwargs.pop("separator", False)

    # Handle separator logic
    if separator or separator_above:
        log_output_with_separator(args[0] if args else "", above=separator_above)
        return

    # Create an in-memory text stream
    buffer = StringIO()

    # Print to the in-memory stream
    print(*args, file=buffer, **kwargs)

    # Retrieve the printed content
    msg = buffer.getvalue()

    # Print the captured output to console with Unicode error handling
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Fallback: encode with error handling for Windows console
        try:
            safe_msg = msg.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8")
            print(safe_msg, **kwargs)
        except Exception:  # noqa: BLE001
            # Last resort: use ASCII with backslashreplace
            safe_msg = msg.encode("ascii", errors="backslashreplace").decode("ascii")
            print(safe_msg, **kwargs)

    if not _global_config.logging_enabled or not _global_config.config:
        return

    if not _global_config.output_log:
        chosen_log_file_path: str = "log_install_differ.log"
        _global_config.output_log = Path(chosen_log_file_path).resolve()
        assert _global_config.output_log is not None
        if not _global_config.output_log.parent.is_dir():
            while True:
                chosen_log_file_path = str(_global_config.config.output_log_path or input("Filepath of the desired output logfile: ").strip() or "log_install_differ.log")
                _global_config.output_log = Path(chosen_log_file_path).resolve()
                assert _global_config.output_log is not None
                if _global_config.output_log.parent.is_dir():
                    break
                print("Invalid path:", _global_config.output_log)

    # Write the captured output to the file (always use UTF-8 for file)
    with _global_config.output_log.open("a", encoding="utf-8") as f:
        f.write(msg)


def visual_length(s: str, tab_length: int = 8) -> int:
    """Calculate visual length of string accounting for tabs."""
    if "\t" not in s:
        return len(s)

    parts: list[str] = s.split("\t")
    vis_length: int = sum(len(part) for part in parts)
    for part in parts[:-1]:
        vis_length += tab_length - (len(part) % tab_length)
    return vis_length


def log_output_with_separator(
    message: str,
    *,
    below: bool = True,
    above: bool = False,
    surround: bool = False,
) -> None:
    """Log output with separator lines."""
    if above or surround:
        log_output(visual_length(message) * "-")
    log_output(message)
    if (below and not above) or surround:
        log_output(visual_length(message) * "-")


def diff_data_wrapper(
    data1: bytes | Path,
    data2: bytes | Path,
    context: DiffContext,
    incremental_writer: IncrementalTSLPatchDataWriter | None = None,
) -> bool | None:
    """Wrapper around diff_data from comparison.py that passes global config.

    Raises:
        AssertionError: If global config is not initialized (programming error)
    """
    if _global_config.config is None:
        error_msg = "Global config config is None - must call run_application first"
        raise AssertionError(error_msg)

    def log_func(msg: str, *, separator: bool = False):
        """Logging function that wraps log_output."""
        if separator:
            log_output_with_separator(msg)
        else:
            log_output(msg)

    return diff_data(
        data1,
        data2,
        context,
        log_func=log_func,
        compare_hashes=_global_config.config.compare_hashes,
        modifications_by_type=_global_config.modifications_by_type,
        incremental_writer=incremental_writer,
    )


def stop_profiler(profiler: cProfile.Profile):
    """Stop and save profiler output."""
    profiler.disable()
    profiler_output_file = Path("profiler_output.pstat")
    profiler.dump_stats(str(profiler_output_file))
    log_output(f"Profiler output saved to: {profiler_output_file}")


def _import_logging_system():
    """Import the logging system components.

    Returns:
        Tuple of (LogLevel, OutputMode, setup_logger) or (None, None, None) if unavailable
    """
    try:
        from kotordiff.logger import LogLevel, OutputMode, setup_logger
    except ImportError:
        return None, None, None
    else:
        return LogLevel, OutputMode, setup_logger


def _setup_logging(config: KotorDiffConfig) -> None:
    """Set up the logging system with the provided configuration.

    Args:
        config: KotorDiff configuration
    """
    LogLevel, OutputMode, setup_logger = _import_logging_system()
    if setup_logger is None or LogLevel is None or OutputMode is None:
        # Logging system not available, skip setup
        return

    log_level = getattr(LogLevel, config.log_level.upper())
    output_mode = getattr(OutputMode, config.output_mode.upper())
    use_colors = config.use_colors

    # Set up output file if specified
    output_file: TextIO | None = None
    if config.output_log_path:
        try:
            output_file = config.output_log_path.open("w", encoding="utf-8")
        except Exception as e:  # noqa: BLE001
            print(f"Warning: Could not open log file {config.output_log_path}: {e}")

    setup_logger(log_level, output_mode, use_colors=use_colors, output_file=output_file)


def _log_configuration(config: KotorDiffConfig) -> None:
    """Log the current configuration."""
    log_output()
    log_output("Configuration:")
    log_output(f"  Mode: {len(config.paths)}-way comparison")

    for i, path in enumerate(config.paths, start=1):
        log_output(f"  Path {i}: '{path}'")

    log_output(f"Using --compare-hashes={config.compare_hashes}")
    log_output(f"Using --use-profiler={config.use_profiler}")


def _execute_diff(
    config: KotorDiffConfig,
) -> tuple[bool | None, int | None]:
    """Execute the diff operation based on configuration.

    Returns:
        Tuple of (comparison result bool or None, exit code or None)
    """
    # Use unified n-way handling for all cases
    comparison, exit_code = handle_diff(config)
    return comparison, exit_code


def _format_comparison_output(
    comparison: bool | None,  # noqa: FBT001
    config: KotorDiffConfig,
) -> int:
    """Format and output the final comparison result.

    Args:
        comparison: True if files match, False if different, None if error
        config: KotorDiff configuration containing paths

    Returns:
        Exit code: 0 for match, 2 for mismatch, 3 for error
    """
    if len(config.paths) >= 2:  # noqa: PLR2004
        log_output(
            f"Comparison of {len(config.paths)} paths: ",
            " MATCHES " if comparison else " DOES NOT MATCH ",
        )
    return 0 if comparison is True else (2 if comparison is False else 3)


def generate_tslpatcher_data(
    tslpatchdata_path: Path,
    ini_filename: str,
    modifications: ModificationsByType,
    base_data_path: Path | None = None,
) -> None:
    """Generate complete TSLPatcher data folder with changes.ini and all resource files.

    DEPRECATED: This batch generation approach is being replaced by IncrementalTSLPatchDataWriter
    which writes files and INI sections as diffs are discovered.

    Args:
        tslpatchdata_path: Path to tslpatchdata folder
        ini_filename: Name of the ini file to generate
        modifications: All modifications to generate files for
        base_data_path: Optional base path for reading original files
    """
    log_output(f"\nGenerating TSLPatcher data at: {tslpatchdata_path}")

    # Analyze TLK StrRef references and create linking patches BEFORE generating files
    if modifications.tlk and base_data_path:
        log_output("\n=== Analyzing StrRef References ===")
        log_output("Searching entire installation/folder for files that reference modified StrRefs...")

        for tlk_mod in modifications.tlk:
            try:
                # Build the tuple expected by new analyze_tlk_strref_references signature.
                # Here we do not have strref_mappings directly, so pass empty mapping for now.
                strref_mappings: dict[int, int] = {}
                analyze_tlk_strref_references(
                    (tlk_mod, strref_mappings),
                    strref_mappings,
                    base_data_path,
                    modifications.gff,
                    modifications.twoda,
                    modifications.ssf,
                    modifications.ncs,
                )
            except Exception as e:  # noqa: BLE001, PERF203
                log_output(f"[Warning] StrRef analysis failed for tlk_mod={tlk_mod}: {e.__class__.__name__}: {e}")
                log_output(f"Full traceback (tlk_mod={tlk_mod}):")
                for line in traceback.format_exc().splitlines():
                    log_output(f"  {line}")

        log_output("StrRef analysis complete. Added linking patches:")
        log_output(f"  GFF patches: {sum(len(m.modifiers) for m in modifications.gff)}")
        log_output(f"  2DA patches: {sum(len(m.modifiers) for m in modifications.twoda)}")
        log_output(f"  SSF patches: {sum(len(m.modifiers) for m in modifications.ssf)}")
        log_output(f"  NCS patches: {sum(len(m.modifiers) for m in modifications.ncs)}")

    # Create the generator
    generator = TSLPatchDataGenerator(tslpatchdata_path)

    # Generate all resource files
    generated_files = generator.generate_all_files(modifications, base_data_path)

    if generated_files:
        log_output(f"Generated {len(generated_files)} resource file(s):")
        for filename in generated_files:
            log_output(f"  - {filename}")

    # Update install folders based on generated files and modifications
    modifications.install = determine_install_folders(modifications)

    # Generate changes.ini
    ini_path = tslpatchdata_path / ini_filename
    log_output(f"\nGenerating {ini_filename} at: {ini_path}")

    serializer = TSLPatcherINISerializer()
    ini_content = serializer.serialize(modifications, include_header=True, include_settings=True)
    ini_path.write_text(ini_content, encoding="utf-8")

    # Summary
    log_output("\nTSLPatcher data generation complete:")
    log_output(f"  Location: {tslpatchdata_path}")
    log_output(f"  INI file: {ini_filename}")
    log_output(f"  TLK modifications: {len(modifications.tlk)}")
    log_output(f"  2DA modifications: {len(modifications.twoda)}")
    log_output(f"  GFF modifications: {len(modifications.gff)}")
    log_output(f"  SSF modifications: {len(modifications.ssf)}")
    log_output(f"  NCS modifications: {len(modifications.ncs)}")
    log_output(f"  Install folders: {len(modifications.install)}")


def handle_diff_internal(
    files_and_folders_and_installations: list[Path | Installation],
    *,
    filters: list[str] | None = None,
    incremental_writer: IncrementalTSLPatchDataWriter | None = None,
) -> tuple[bool | None, int | None]:
    """Internal n-way diff handler that accepts arbitrary number of paths.

    Args:
        files_and_folders_and_installations: List of paths to compare (2 or more)
        filters: Optional filters
        incremental_writer: Optional incremental writer for immediate writes

    Returns:
        Tuple of (comparison_result, exit_code)
    """
    if len(files_and_folders_and_installations) < 2:  # noqa: PLR2004
        log_output("[ERROR] At least 2 paths required for comparison")
        return None, 1

    # Use the new n-way implementation for all cases
    log_output(f"[INFO] N-way comparison with {len(files_and_folders_and_installations)} paths")
    comparison = run_differ_from_args(
        files_and_folders_and_installations,
        filters=filters,
        incremental_writer=incremental_writer,
    )

    # Format output
    if comparison is True:
        log_output("\n[IDENTICAL] All paths are identical", separator_above=True)
        return comparison, 0
    if comparison is False:
        log_output("\n[DIFFERENT] Differences found between paths", separator_above=True)
        return comparison, 1

    # Error case
    log_output("\n[ERROR] Comparison failed or returned None", separator_above=True)
    return comparison, 1


def handle_diff(config: KotorDiffConfig) -> tuple[bool | None, int | None]:
    """Handle N-way diff execution.

    Returns:
        Tuple of (comparison_result, exit_code)
        If comparison_result is not None, use that for final output
        Otherwise use exit_code
    """
    # Create modifications collection for INI generation
    _global_config.modifications_by_type = ModificationsByType.create_empty()

    # Use paths from config
    all_paths: list[Path | Installation] = config.paths

    # Create incremental writer if requested
    incremental_writer = None
    base_path: Path | Installation | None = None
    if config.tslpatchdata_path:
        for candidate_path in all_paths:
            if isinstance(candidate_path, Installation) or candidate_path.is_dir():
                base_path = candidate_path
                break

        if config.use_incremental_writer:
            # Determine game from first valid directory path
            game: Game | None = None
            if base_path is not None:
                try:
                    game = base_path.game() if isinstance(base_path, Installation) else Game.K1
                except Exception as e:  # noqa: BLE001
                    log_output(f"[Warning] Could not determine game: {e.__class__.__name__}: {e}")
                    log_output("Full traceback:")
                    for line in traceback.format_exc().splitlines():
                        log_output(f"  {line}")

            # Create StrRef cache if we have a valid game
            strref_cache = StrRefReferenceCache(game) if game else None

            # Create 2DA memory caches if we have a valid game
            # Structure: {installation_index: CaseInsensitiveDict[TwoDAMemoryReferenceCache]}
            # Initialize caches for all installations
            from utility.common.more_collections import CaseInsensitiveDict  # noqa: PLC0415

            twoda_caches: dict[int, CaseInsensitiveDict[TwoDAMemoryReferenceCache]] = {}
            if game:
                # Initialize caches for each path index
                for idx in range(len(all_paths)):
                    twoda_caches[idx] = CaseInsensitiveDict()

            incremental_writer = IncrementalTSLPatchDataWriter(
                config.tslpatchdata_path,
                config.ini_filename,
                base_data_path=base_path if isinstance(base_path, Path) else None,
                strref_cache=strref_cache,
                twoda_caches=twoda_caches if twoda_caches else None,
                log_func=log_output,
            )
            log_output(f"Using incremental writer for tslpatchdata: {config.tslpatchdata_path}")

    comparison, _ = handle_diff_internal(
        all_paths,
        filters=config.filters,
        incremental_writer=incremental_writer,
    )

    # Finalize TSLPatcher data if requested
    if config.tslpatchdata_path:
        if config.use_incremental_writer and incremental_writer:
            try:
                # Finalize INI by writing InstallList section
                incremental_writer.finalize()

                # Summary
                log_output("\nTSLPatcher data generation complete:")
                log_output(f"  Location: {config.tslpatchdata_path}")
                log_output(f"  INI file: {config.ini_filename}")
                log_output(f"  TLK modifications: {len(incremental_writer.all_modifications.tlk)}")
                log_output(f"  2DA modifications: {len(incremental_writer.all_modifications.twoda)}")
                log_output(f"  GFF modifications: {len(incremental_writer.all_modifications.gff)}")
                log_output(f"  SSF modifications: {len(incremental_writer.all_modifications.ssf)}")
                log_output(f"  NCS modifications: {len(incremental_writer.all_modifications.ncs)}")
                total_install_files: int = sum(len(files) for files in incremental_writer.install_folders.values())
                log_output(f"  Install files: {total_install_files}")
                log_output(f"  Install folders: {len(incremental_writer.install_folders)}")
            except Exception as gen_error:  # noqa: BLE001
                log_output(f"[Error] Failed to finalize TSLPatcher data: {universal_simplify_exception(gen_error)}")
                log_output("Full traceback:")
                for line in traceback.format_exc().splitlines():
                    log_output(f"  {line}")
                return None, 1
            else:
                return None, 0
        elif not config.use_incremental_writer:
            try:
                assert _global_config.modifications_by_type is not None
                generate_tslpatcher_data(
                    config.tslpatchdata_path,
                    config.ini_filename,
                    _global_config.modifications_by_type,
                    base_data_path=base_path if isinstance(base_path, Path) else None,
                )
            except Exception as gen_error:  # noqa: BLE001
                log_output(f"[Error] Failed to generate TSLPatcher data: {universal_simplify_exception(gen_error)}")
                log_output("Full traceback:")
                for line in traceback.format_exc().splitlines():
                    log_output(f"  {line}")
                return None, 1
            else:
                return None, 0

    return comparison, None


# ---------------------------------------------------------------------------
# Orchestration functions with global config wrappers
# ---------------------------------------------------------------------------


def run_differ_from_args(
    files_and_folders_and_installations: list[Path | Installation],
    *,
    filters: list[str] | None = None,
    incremental_writer: IncrementalTSLPatchDataWriter | None = None,
) -> bool | None:
    """Run n-way differ using global config.

    Args:
        files_and_folders_and_installations: List of paths/installations to compare (2 or more)
        filters: Optional resource name filters
        incremental_writer: Optional incremental writer for immediate writes

    Raises:
        AssertionError: If global config is not initialized (programming error)
        ValueError: If less than 2 paths provided
    """
    if _global_config.config is None:
        error_msg = "Global config config is None - must call run_application first"
        raise AssertionError(error_msg)

    # Extract config values once for type safety
    compare_hashes_enabled: bool = _global_config.config.compare_hashes

    def log_func_wrapper(
        msg: str,
        *,
        separator: bool = False,
        separator_above: bool = False,
    ):
        """Wrapper for log_output with separator support."""
        if separator or separator_above:
            log_output_with_separator(msg, above=separator_above)
        else:
            log_output(msg)

    # Call the n-way implementation directly
    return run_differ_from_args_impl(
        files_and_folders_and_installations,
        filters=filters,
        log_func=log_func_wrapper,
        compare_hashes=compare_hashes_enabled,
        modifications_by_type=_global_config.modifications_by_type,
        incremental_writer=incremental_writer,
    )


def run_application(config: KotorDiffConfig) -> int:
    """Run the main KotorDiff application with parsed configuration.

    Args:
        config: KotorDiff configuration

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    # Store config in global config
    _global_config.config = config
    _global_config.logging_enabled = config.logging_enabled

    # Set up output log path
    if config.output_log_path:
        _global_config.output_log = config.output_log_path

    # Set up the logging system
    _setup_logging(config)

    # Log configuration
    _log_configuration(config)

    # Run with optional profiler
    profiler: cProfile.Profile | None = None
    try:
        if config.use_profiler:
            profiler = cProfile.Profile()
            profiler.enable()

        comparison, exit_code = _execute_diff(config)

        if profiler:
            stop_profiler(profiler)

        # Format and return final output
        if comparison is not None:
            return _format_comparison_output(comparison, config)

    except KeyboardInterrupt:
        log_output("KeyboardInterrupt - KotorDiff was cancelled by user.")
        if profiler:
            stop_profiler(profiler)
        raise
    except Exception:
        if profiler:
            stop_profiler(profiler)
        raise
    else:
        return exit_code or 0
