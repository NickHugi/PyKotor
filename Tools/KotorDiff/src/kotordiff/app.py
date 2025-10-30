#!/usr/bin/env python3
"""Main application logic for KotorDiff.

This module contains the core application flow, keeping __main__.py focused
exclusively on CLI argument parsing.
"""

from __future__ import annotations

import cProfile
import os
import sys
import traceback

from dataclasses import dataclass
from datetime import datetime, timezone
from io import StringIO
from typing import TYPE_CHECKING, Any, Callable

from kotordiff.cli_utils import print_path_error_with_help, prompt_for_path
from pykotor.extract.installation import Installation
from pykotor.extract.talktable import StrRefReferenceCache
from pykotor.resource.formats import gff
from pykotor.tools.misc import is_capsule_file
from pykotor.tslpatcher.diff import DiffCache, load_diff_cache, save_diff_cache
from pykotor.tslpatcher.diff.analyzers import (
    DiffAnalyzerFactory,
    analyze_2da_memory_references,
    analyze_tlk_strref_references,
)
from pykotor.tslpatcher.diff.cache import restore_strref_cache_from_cache
from pykotor.tslpatcher.diff.engine import (
    DiffContext,
    diff_capsule_files,
    diff_container_vs_installation,
    diff_data,
    diff_directories,
    diff_installs_implementation,
    diff_installs_with_objects,
    diff_resource_vs_installation,
    ext_of,
    get_module_root,
    print_udiff,
    relative_path_from_to,
    run_differ_from_args_impl,
    should_skip_rel,
    walk_files,
)
from pykotor.tslpatcher.diff.generator import (
    TSLPatchDataGenerator,
    determine_install_folders,
    validate_tslpatchdata_arguments,
)
from pykotor.tslpatcher.diff.incremental_writer import IncrementalTSLPatchDataWriter
from pykotor.tslpatcher.diff.merge3_utils import diff3_files_udiff
from pykotor.tslpatcher.mods.gff import ModificationsGFF, ModifyFieldGFF
from pykotor.tslpatcher.mods.install import InstallFile
from pykotor.tslpatcher.mods.ssf import ModificationsSSF
from pykotor.tslpatcher.mods.tlk import ModificationsTLK
from pykotor.tslpatcher.mods.twoda import Modifications2DA
from pykotor.tslpatcher.writer import IniGenerationConfig, ModificationsByType, TSLPatcherINISerializer
from utility.error_handling import universal_simplify_exception
from utility.system.path import Path

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace

    from pykotor.extract.twoda import TwoDAMemoryReferenceCache



gff_types: list[str] = list(gff.GFFContent.get_extensions())


def find_module_root(filename: str) -> str:
    """Wrapper around get_module_root for backwards compatibility."""
    return get_module_root(Path(filename))


@dataclass
class GlobalConfig:
    """Global configuration state for KotorDiff."""

    output_log: Path | None = None
    logging_enabled: bool | None = None
    parser_args: Namespace | None = None
    parser: ArgumentParser | None = None
    modifications_by_type: ModificationsByType | None = None
    diff_cache: DiffCache | None = None


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

    if not _global_config.logging_enabled or not _global_config.parser_args or not _global_config.parser:
        return

    if not _global_config.output_log:
        chosen_log_file_path: str = "log_install_differ.log"
        _global_config.output_log = Path(chosen_log_file_path).resolve()
        assert _global_config.output_log is not None
        if not _global_config.output_log.parent.safe_isdir():
            while True:
                chosen_log_file_path = _global_config.parser_args.output_log or input("Filepath of the desired output logfile: ").strip() or "log_install_differ.log"
                _global_config.output_log = Path(chosen_log_file_path).resolve()
                assert _global_config.output_log is not None
                if _global_config.output_log.parent.safe_isdir():
                    break
                print("Invalid path:", _global_config.output_log)
                _global_config.parser.print_help()

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
    if _global_config.parser_args is None:
        error_msg = "Global config parser_args is None - must call run_application first"
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
        compare_hashes=_global_config.parser_args.compare_hashes,
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


def _validate_tslpatchdata_early(args: Namespace, parser: ArgumentParser) -> int | None:
    """Perform early validation of tslpatchdata arguments.

    Returns:
        Error code if validation failed, None otherwise
    """
    if not (hasattr(args, "tslpatchdata") or hasattr(args, "ini")):
        return None

    try:
        # Get initial path arguments (may not be resolved yet)
        mine_arg = getattr(args, "mine", None)
        older_arg = getattr(args, "older", None)
        yours_arg = getattr(args, "yours", None)

        # Convert to Path objects if they exist
        mine_path_early = Path(mine_arg).resolve() if mine_arg else None
        older_path_early = Path(older_arg).resolve() if older_arg else None
        yours_path_early = Path(yours_arg).resolve() if yours_arg else None

        # Validate the arguments (this will be called again later with final paths)
        validated_ini, validated_tslpatchdata = validate_tslpatchdata_arguments(
            args.ini,
            args.tslpatchdata,
            mine_path_early,
            older_path_early,
            yours_path_early,
        )

        # Store validated values back (filename correction)
        if validated_ini:
            args.ini = validated_ini
        if validated_tslpatchdata:
            args.tslpatchdata_path = validated_tslpatchdata

    except ValueError as e:
        log_output(f"[Error] Argument validation failed: {e.__class__.__name__}: {e}")
        log_output("Full traceback:")
        for line in traceback.format_exc().splitlines():
            log_output(f"  {line}")
        parser.print_help()
        return 2
    return None


def _setup_logging(
    args: Namespace,
    setup_logger: Callable[..., Any] | None,
    log_level_enum: type | None,
    output_mode_enum: type | None,
) -> None:  # noqa: PLR0913
    """Set up the logging system with the provided arguments.

    Args:
        args: Parsed command-line arguments
        setup_logger: setup_logger function from logger module or None
        log_level_enum: LogLevel enum type or None
        output_mode_enum: OutputMode enum type or None
    """
    if setup_logger is None or log_level_enum is None or output_mode_enum is None:
        # Logging system not available, skip setup
        return

    log_level = getattr(log_level_enum, args.log_level.upper())
    output_mode = getattr(output_mode_enum, args.output_mode.upper())
    use_colors = not args.no_color

    # Set up output file if specified
    output_file = None
    if args.output_log:
        try:
            output_file = Path(args.output_log).open("w", encoding="utf-8")
        except Exception as e:  # noqa: BLE001
            print(f"Warning: Could not open log file {args.output_log}: {e}")

    setup_logger(log_level, output_mode, use_colors=use_colors, output_file=output_file)


def _resolve_module_path(
    path: Path,
    parser: ArgumentParser,
) -> Path | None:  # noqa: PLR0913
    """Attempt to resolve a module name to a file path.

    Args:
        path: Path that may be a module name
        parser: ArgumentParser for help display

    Returns:
        Resolved path if found, None otherwise
    """
    if path.safe_exists():
        return path

    # Check if this could be a module name
    potential_module_files = []
    base_name = path.name
    parent_dir = path.parent

    for ext in [".mod", ".rim", "_s.rim", "_dlg.erf"]:
        module_file = parent_dir / f"{base_name}{ext}"
        if module_file.safe_exists():
            potential_module_files.append(module_file)

    if potential_module_files:
        resolved_path = potential_module_files[0]
        log_output(f"Resolved module name '{base_name}' to: {resolved_path}")
        return resolved_path

    print_path_error_with_help(path, parser)
    return None


def _prompt_and_resolve_path(
    prompt_text: str,
    initial_value: os.PathLike | str | None,
    parser: ArgumentParser,
) -> Path | None:
    """Prompt for and resolve a path, with module name resolution support.

    Args:
        prompt_text: Text to display when prompting
        initial_value: Initial path value (if provided)
        parser: ArgumentParser for help display

    Returns:
        Resolved Path object, or None if the path cannot be resolved
    """
    initial_path = initial_value

    while True:
        if initial_path:
            path_str = initial_path
            initial_path = None
        else:
            path_str = prompt_for_path(prompt_text)

        if not path_str:
            print("Path cannot be empty")
            continue

        resolved_path = Path(path_str).resolve()

        # Try to resolve (may be a module name)
        final_path = _resolve_module_path(resolved_path, parser)
        if final_path is not None:
            return final_path

    return None


def _resolve_three_way_paths(
    args: Namespace,
    mine_arg: os.PathLike | str | None,
    older_arg: os.PathLike | str | None,
    yours_arg: os.PathLike | str | None,
):
    """Resolve paths for 3-way diff."""
    if mine_arg is None or older_arg is None or yours_arg is None:
        error_msg = "All three paths are required for 3-way diff"
        raise AssertionError(error_msg)

    args.mine = Path(mine_arg).resolve()
    args.older = Path(older_arg).resolve()
    args.yours = Path(yours_arg).resolve()

    for _label, p in (("--mine", args.mine), ("--older", args.older), ("--yours", args.yours)):
        if not p.safe_exists():
            error_msg = f"Invalid path: {p}"
            raise AssertionError(error_msg)


def _resolve_two_way_paths(
    args: Namespace,
    unknown_args: list[str],
    parser: ArgumentParser,
) -> None:
    """Resolve paths for 2-way diff, with interactive prompting if needed."""
    initial_path1 = args.mine or (unknown_args[0] if len(unknown_args) > 0 else None)
    args.mine = _prompt_and_resolve_path("Path to the first K1/TSL install, file, or directory to diff.", initial_path1, parser)

    initial_path2 = args.older or (unknown_args[1] if len(unknown_args) > 1 else None)
    args.older = _prompt_and_resolve_path("Path to the second K1/TSL install, file, or directory to diff.", initial_path2, parser)

    # Collect any extra paths from --path arguments or remaining unknown args
    extra_paths: list[Path] = []
    if hasattr(args, "extra_paths") and args.extra_paths:
        for extra_path_str in args.extra_paths:
            extra_path = Path(extra_path_str).resolve()
            if extra_path.safe_exists():
                extra_paths.append(extra_path)
            else:
                log_output(f"Warning: Extra path does not exist: {extra_path_str}")

    # Also collect from remaining unknown args (for backwards compatibility)
    for i in range(2, len(unknown_args)):
        extra_path = Path(unknown_args[i]).resolve()
        if extra_path.safe_exists():
            extra_paths.append(extra_path)

    args.extra_paths = extra_paths if extra_paths else None


def _resolve_paths_from_args(
    args: Namespace,
    unknown_args: list[str],
    parser: ArgumentParser,
) -> tuple[bool, int | None]:
    """Resolve paths from arguments, handling both 2-way and 3-way diffs.

    Returns:
        Tuple of (is_three_way, error_code). error_code is None if successful.
    """
    # Positional argument indices
    MINE_INDEX: int = 0
    OLDER_INDEX: int = 1
    YOURS_INDEX: int = 2

    # Determine if this is 2-way or 3-way diff
    mine_arg: str | None = args.mine or (unknown_args[MINE_INDEX] if len(unknown_args) > MINE_INDEX else None)
    older_arg: str | None = args.older or (unknown_args[OLDER_INDEX] if len(unknown_args) > OLDER_INDEX else None)
    yours_arg: str | None = args.yours or (unknown_args[YOURS_INDEX] if len(unknown_args) > YOURS_INDEX else None)

    is_three_way: bool = mine_arg is not None and older_arg is not None and yours_arg is not None

    # Resolve paths based on diff type (may raise AssertionError on validation failure)
    if is_three_way:
        _resolve_three_way_paths(args, mine_arg, older_arg, yours_arg)
    else:
        _resolve_two_way_paths(args, unknown_args, parser)

    return is_three_way, None


def _log_configuration(args: Namespace, *, is_three_way: bool) -> None:
    """Log the current configuration."""
    num_extra_paths = len(args.extra_paths) if hasattr(args, "extra_paths") and args.extra_paths else 0
    total_paths = 2 + (1 if is_three_way else 0) + num_extra_paths

    log_output()
    log_output("Configuration:")
    if total_paths > 3:  # noqa: PLR2004
        log_output(f"  Mode: {total_paths}-way comparison")
    else:
        log_output(f"  Mode: {'3-way' if is_three_way else '2-way'} comparison")

    log_output(f"  Using --mine='{args.mine}' (BASE/REFERENCE)")
    log_output(f"  Using --older='{args.older}'")
    if is_three_way:
        log_output(f"  Using --yours='{args.yours}'")
    if num_extra_paths > 0:
        for i, extra_path in enumerate(args.extra_paths, start=4):
            log_output(f"  Using --path{i}='{extra_path}'")
    log_output(f"Using --compare-hashes={args.compare_hashes}")
    log_output(f"Using --use-profiler={args.use_profiler}")


def _execute_diff(
    args: Namespace,
    *,
    is_three_way: bool,
) -> tuple[bool | None, int | None]:
    """Execute the diff operation based on configuration.

    Returns:
        Tuple of (comparison result bool or None, exit code or None)
        - For 2-way: comparison is bool|None, exit_code is None
        - For 3-way and cached: comparison is None, exit_code is int
    """
    # Handle loading from cached results
    if args.from_results:
        exit_code: int | None = handle_cached_results(args)
        return None, exit_code

    # Run 3-way or 2-way diff
    if is_three_way:
        exit_code = handle_three_way_diff(args)
        comparison: bool | None = None
    else:
        comparison, exit_code = handle_two_way_diff(args)

    return comparison, exit_code


def _format_comparison_output(
    comparison: bool | None,  # noqa: FBT001
    args: Namespace,
) -> int:
    """Format and output the final comparison result.

    Args:
        comparison: True if files match, False if different, None if error
        args: Parsed arguments containing paths

    Returns:
        Exit code: 0 for match, 2 for mismatch, 3 for error
    """
    log_output(
        f"'{relative_path_from_to(args.older, args.mine)}'",
        " MATCHES " if comparison else " DOES NOT MATCH ",
        f"'{relative_path_from_to(args.mine, args.older)}'",
    )
    return 0 if comparison is True else (2 if comparison is False else 3)


def run_application(  # noqa: C901
    args: Namespace,
    parser: ArgumentParser,
    unknown_args: list[str],
) -> int:
    """Run the main KotorDiff application with parsed arguments.

    Args:
        args: Parsed command-line arguments
        parser: ArgumentParser instance for help display
        unknown_args: Unknown positional arguments from parse_known_args

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    # Import the logging system
    LogLevel, OutputMode, setup_logger = _import_logging_system()

    # Store in global config
    _global_config.parser_args = args
    _global_config.parser = parser
    _global_config.logging_enabled = args.logging_enabled

    # Early validation of --ini and --tslpatchdata arguments
    error_code = _validate_tslpatchdata_early(args, parser)
    if error_code is not None:
        return error_code

    # Set up the logging system
    _setup_logging(args, setup_logger, LogLevel, OutputMode)

    # Resolve paths from arguments
    is_three_way, error_code = _resolve_paths_from_args(args, unknown_args, parser)
    if error_code is not None:
        return error_code

    # Log configuration
    _log_configuration(args, is_three_way=is_three_way)

    # Run with optional profiler
    profiler: cProfile.Profile | None = None
    try:
        if args.use_profiler:
            profiler = cProfile.Profile()
            profiler.enable()

        comparison, exit_code = _execute_diff(args, is_three_way=is_three_way)

        if profiler:
            stop_profiler(profiler)

        # Format and return final output
        if comparison is not None:
            return _format_comparison_output(comparison, args)

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


def generate_tslpatcher_data(
    tslpatchdata_path: Path,
    ini_filename: str,
    modifications: ModificationsByType,
    base_data_path: Path | None = None,
) -> None:
    """Generate complete TSLPatcher data folder with changes.ini and all resource files.

    DEPRECATED: This batch generation approach is being replaced by IncrementalTSLPatchDataWriter
    which writes files and INI sections as diffs are discovered. Still used for:
    - 3-way diffs
    - Loading from cached results

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
                analyze_tlk_strref_references(
                    tlk_mod,
                    base_data_path,
                    modifications.gff,
                    modifications.twoda,
                    modifications.ssf,
                    modifications.ncs,
                )
            except Exception as e:  # noqa: BLE001, PERF203
                log_output(f"[Warning] StrRef analysis failed: {e.__class__.__name__}: {e}")
                log_output("Full traceback:")
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


def handle_cached_results(args: Namespace) -> int:  # noqa: C901
    """Handle loading and processing cached diff results."""
    cache_file = Path(args.from_results).resolve()
    log_output(f"Loading diff results from cache: {cache_file}")

    try:

        cache, left_dir, right_dir = load_diff_cache(cache_file, log_func=log_output)

        # Restore StrRef cache if it was saved
        restored_strref_cache = restore_strref_cache_from_cache(cache)
        if restored_strref_cache is not None:
            log_output("  Restored StrRef cache from saved data")

        # Create modifications collection for INI generation
        _global_config.modifications_by_type = ModificationsByType.create_empty()

        # Create incremental writer if --tslpatchdata is specified (even for cached results)
        incremental_writer = None
        if hasattr(args, "tslpatchdata_path") and args.tslpatchdata_path:
            # Create 2DA caches (currently can't be restored from cache, so create new)
            from utility.common.more_collections import CaseInsensitiveDict  # noqa: PLC0415

            twoda_caches: dict[int, CaseInsensitiveDict[TwoDAMemoryReferenceCache]] = {}
            if restored_strref_cache is not None:
                # Use same game as StrRef cache
                # Initialize caches for each installation (for 2-way: 0 and 1)
                # Keys are case-insensitive 2DA filenames
                twoda_caches[0] = CaseInsensitiveDict()
                twoda_caches[1] = CaseInsensitiveDict()

            incremental_writer = IncrementalTSLPatchDataWriter(
                args.tslpatchdata_path,
                args.ini,
                base_data_path=left_dir,  # Use cached data directory as base
                strref_cache=restored_strref_cache,  # Use restored cache
                twoda_caches=twoda_caches if twoda_caches else None,
                log_func=log_output,
            )
            log_output(f"Using incremental writer for tslpatchdata: {args.tslpatchdata_path}")
            if restored_strref_cache is not None:
                log_output("  Using restored StrRef cache for TLK linking")
            if twoda_caches:
                log_output("  Created 2DA caches for 2DAMEMORY linking")

        # Process cached files to regenerate diff output and INI modifications
        log_output("\nRegenerating diff output from cached data...")
        for file_comp in cache.files or []:
            if file_comp.status == "modified":
                left_file = left_dir / file_comp.rel_path
                right_file = right_dir / file_comp.rel_path

                if left_file.safe_isfile() and right_file.safe_isfile():
                    ctx = DiffContext(
                        Path(file_comp.rel_path),
                        Path(file_comp.rel_path),
                        file_comp.ext,
                        skip_nss=False,
                    )
                    diff_data_wrapper(left_file, right_file, ctx, incremental_writer)
            elif file_comp.status == "missing_left":
                log_output(f"Missing file:\t{file_comp.rel_path}")
            elif file_comp.status == "missing_right":
                log_output(f"Missing file:\t{file_comp.rel_path}")

        # Finalize incremental writer if it was created
        if incremental_writer is not None:
            try:
                incremental_writer.finalize()
                log_output("\nTSLPatcher data generation complete (from cache):")
                log_output(f"  Location: {args.tslpatchdata_path}")
                log_output(f"  INI file: {args.ini}")
            except Exception as gen_error:  # noqa: BLE001
                log_output(f"[Error] Failed to finalize TSLPatcher data: {universal_simplify_exception(gen_error)}")
                log_output("Full traceback:")
                for line in traceback.format_exc().splitlines():
                    log_output(f"  {line}")

    except Exception as load_error:  # noqa: BLE001
        log_output(f"[Error] Failed to load cache or generate INI: {universal_simplify_exception(load_error)}")
        log_output("Full traceback:")
        for line in traceback.format_exc().splitlines():
            log_output(f"  {line}")
        return 1

    else:
        return 0


def handle_nway_diff(args: Namespace) -> int:
    """Handle N-way diff execution (4+ paths).

    Compares all paths against the base (--mine).
    """
    log_output("\n" + "=" * 80)
    log_output("N-WAY COMPARISON")
    log_output("=" * 80)

    all_paths: list[Path] = [args.mine, args.older]
    if args.yours:
        all_paths.append(args.yours)
    if args.extra_paths:
        all_paths.extend(args.extra_paths)

    log_output(f"\nComparing {len(all_paths)} paths (base: --mine):")
    for i, path in enumerate(all_paths, 1):
        label = "mine (BASE)" if i == 1 else f"path{i}"
        log_output(f"  {i}. {label}: {path}")

    log_output("\nComparison Strategy:")
    log_output("  - First path (--mine) is the BASE/REFERENCE")
    log_output("  - Each subsequent path is compared against the base")
    log_output("  - InstallList: Files in target but NOT in base")
    log_output("  - PatchList: Files in both (if different)")
    log_output("=" * 80)

    # Compare each path against the base
    base_path = all_paths[0]
    all_comparisons_same = True

    for i, target_path in enumerate(all_paths[1:], 2):
        log_output(f"\n{'=' * 80}")
        log_output(f"COMPARISON {i - 1}/{len(all_paths) - 1}: BASE vs path{i}")
        log_output(f"  Base:   {base_path}")
        log_output(f"  Target: {target_path}")
        log_output("=" * 80)

        # Run the 2-way comparison
        comparison_result, _ = handle_two_way_diff_internal(
            mine=base_path,
            older=target_path,
            filters=args.filter if hasattr(args, "filter") else None,
        )

        if comparison_result is False:
            all_comparisons_same = False

    # Summary
    log_output(f"\n{'=' * 80}")
    log_output("N-WAY COMPARISON SUMMARY")
    log_output("=" * 80)
    log_output(f"Total paths compared: {len(all_paths)}")
    log_output(f"All identical to base: {'Yes' if all_comparisons_same else 'No'}")
    log_output("=" * 80)

    return 0 if all_comparisons_same else 1


def handle_three_way_diff(args: Namespace) -> int:
    """Handle 3-way diff execution."""
    # Create modifications collection for INI generation
    _global_config.modifications_by_type = ModificationsByType.create_empty()

    # For 3-way diffs, use tslpatchdata if specified
    if hasattr(args, "tslpatchdata_path") and args.tslpatchdata_path:
        config = IniGenerationConfig(
            generate_ini=True,
            ini=args.tslpatchdata_path / args.ini,
        )
    else:
        # Legacy behavior: generate to current directory
        out_ini_path: Path
        if args.ini is not None:
            out_ini_path = Path(args.ini).resolve()
        else:
            out_ini_path = Path("changes.ini").resolve()

        config = IniGenerationConfig(
            generate_ini=True,
            ini=out_ini_path,
        )

    run_differ3_from_args(args.mine, args.older, args.yours, config)

    # Generate TSLPatcher data if --tslpatchdata is specified
    if hasattr(args, "tslpatchdata_path") and args.tslpatchdata_path:
        try:
            # Determine base data path (prefer yours, then mine, then older)
            base_data_path = None
            if args.yours and args.yours.safe_isdir():
                base_data_path = args.yours
            elif args.mine and args.mine.safe_isdir():
                base_data_path = args.mine
            elif args.older and args.older.safe_isdir():
                base_data_path = args.older

            generate_tslpatcher_data(
                args.tslpatchdata_path,
                args.ini,
                _global_config.modifications_by_type,
                base_data_path=base_data_path,
            )
        except Exception as gen_error:  # noqa: BLE001
            log_output(f"[Error] Failed to generate TSLPatcher data: {universal_simplify_exception(gen_error)}")
            log_output("Full traceback:")
            for line in traceback.format_exc().splitlines():
                log_output(f"  {line}")
            return 1

    return 0


def handle_two_way_diff_internal(
    mine: Path,
    older: Path,
    *,
    filters: list[str] | None = None,
    incremental_writer: IncrementalTSLPatchDataWriter | None = None,
) -> tuple[bool | None, int | None]:
    """Internal 2-way diff handler that can be reused by N-way comparison.

    Args:
        mine: Base/reference path
        older: Target path to compare against base
        filters: Optional filters
        incremental_writer: Optional incremental writer for immediate writes

    Returns:
        Tuple of (comparison_result, exit_code)
    """
    comparison = run_differ_from_args(mine, older, filters=filters, incremental_writer=incremental_writer)

    # Format output
    if comparison is True:
        log_output("\n[IDENTICAL] Paths are identical", separator_above=True)
        return comparison, 0
    if comparison is False:
        log_output("\n[DIFFERENT] Paths are different", separator_above=True)
        return comparison, 1

    # Error case
    log_output("\n[ERROR] Comparison failed or returned None", separator_above=True)
    return comparison, 1


def handle_two_way_diff(args: Namespace) -> tuple[bool | None, int | None]:
    """Handle 2-way diff execution.

    Returns:
        Tuple of (comparison_result, exit_code)
        If comparison_result is not None, use that for final output
        Otherwise use exit_code
    """
    # Create modifications collection for INI generation
    _global_config.modifications_by_type = ModificationsByType.create_empty()

    # Create diff cache if --save-results is specified
    if args.save_results:
        _global_config.diff_cache = DiffCache(
            version="1.0",
            mine=str(args.mine),
            older=str(args.older),
            timestamp=datetime.now(tz=timezone.utc).isoformat(),
            files=[],
        )

    # Create incremental writer if --tslpatchdata is specified
    incremental_writer = None
    if hasattr(args, "tslpatchdata_path") and args.tslpatchdata_path:

        # Determine game from installation paths
        base_path = args.mine if args.mine.safe_isdir() else None
        game = None
        if base_path:

            try:
                game = Installation.determine_game(base_path)
            except Exception as e:  # noqa: BLE001
                log_output(f"[Warning] Could not determine game: {e.__class__.__name__}: {e}")
                log_output("Full traceback:")
                for line in traceback.format_exc().splitlines():
                    log_output(f"  {line}")

        # Create StrRef cache if we have a valid game
        strref_cache = StrRefReferenceCache(game) if game else None

        # Create 2DA memory caches if we have a valid game
        # Structure: {installation_index: CaseInsensitiveDict[TwoDAMemoryReferenceCache]}
        # For 2-way diff: build caches for install1 (index 0) and install2 (index 1)
        # Keys are case-insensitive 2DA filenames
        from utility.common.more_collections import CaseInsensitiveDict  # noqa: PLC0415

        twoda_caches: dict[int, CaseInsensitiveDict[TwoDAMemoryReferenceCache]] = {}
        if game:
            # Initialize caches for each installation with CaseInsensitiveDict
            # install1 (index 0) - for rows that exist in install1 but not install2
            twoda_caches[0] = CaseInsensitiveDict()
            # install2 (index 1) - for rows that exist in install2 but not install1
            twoda_caches[1] = CaseInsensitiveDict()

        incremental_writer = IncrementalTSLPatchDataWriter(
            args.tslpatchdata_path,
            args.ini,
            base_data_path=base_path,
            strref_cache=strref_cache,
            twoda_caches=twoda_caches if twoda_caches else None,
            log_func=log_output,
        )
        log_output(f"Using incremental writer for tslpatchdata: {args.tslpatchdata_path}")

    comparison, _ = handle_two_way_diff_internal(
        args.mine,
        args.older,
        filters=args.filter,
        incremental_writer=incremental_writer,
    )

    # Save diff cache if --save-results is specified
    if args.save_results and _global_config.diff_cache is not None:
        cache_file = Path(args.save_results).resolve()
        log_output(f"\nSaving diff results to cache: {cache_file}")
        try:
            # Include StrRef cache if available from incremental_writer
            strref_cache_to_save = incremental_writer.strref_cache if incremental_writer else None

            save_diff_cache(
                _global_config.diff_cache,
                cache_file,
                args.mine,
                args.older,
                strref_cache=strref_cache_to_save,
                log_func=log_output,
            )
        except Exception as save_error:  # noqa: BLE001
            log_output(f"[Error] Failed to save cache: {universal_simplify_exception(save_error)}")
            log_output("Full traceback:")
            for line in traceback.format_exc().splitlines():
                log_output(f"  {line}")

    # Finalize TSLPatcher data if --tslpatchdata is specified
    if hasattr(args, "tslpatchdata_path") and args.tslpatchdata_path and incremental_writer:
        try:
            # Finalize INI by writing InstallList section
            incremental_writer.finalize()

            # Summary
            log_output("\nTSLPatcher data generation complete:")
            log_output(f"  Location: {args.tslpatchdata_path}")
            log_output(f"  INI file: {args.ini}")
            log_output(f"  TLK modifications: {len(incremental_writer.all_modifications.tlk)}")
            log_output(f"  2DA modifications: {len(incremental_writer.all_modifications.twoda)}")
            log_output(f"  GFF modifications: {len(incremental_writer.all_modifications.gff)}")
            log_output(f"  SSF modifications: {len(incremental_writer.all_modifications.ssf)}")
            log_output(f"  NCS modifications: {len(incremental_writer.all_modifications.ncs)}")
            total_install_files: int = sum(len(files) for files in incremental_writer.install_folders.values())
            log_output(f"  Install files: {total_install_files}")
            log_output(f"  Install folders: {len(incremental_writer.install_folders)}")
            # Return early on success
        except Exception as gen_error:  # noqa: BLE001
            log_output(f"[Error] Failed to finalize TSLPatcher data: {universal_simplify_exception(gen_error)}")
            log_output("Full traceback:")
            for line in traceback.format_exc().splitlines():
                log_output(f"  {line}")
            return None, 1
        else:
            return None, 0

    return comparison, None


# ---------------------------------------------------------------------------
# 3-way diff functions
# ---------------------------------------------------------------------------
# Note: diff3_files_udiff has been migrated to pykotor.tslpatcher.diff.merge3_utils


def generate_changes_ini(
    mine_root: Path | None,
    older_root: Path,
    yours_root: Path,
    *,
    out_path: Path,
    log_func: Callable,
):
    """Generate a comprehensive TSLPatcher-compatible changes.ini from directory differences.

    Args:
        mine_root: Optional base path for 3-way diff (if None, uses 2-way diff with older_root as base)
        older_root: Second comparison path (becomes base for 2-way diff if mine_root is None)
        yours_root: Target/desired state path
        out_path: Output path for changes.ini
        log_func: Logging function
    """
    # Check debug/verbose flags
    # Log level: 0 = normal, 1 = verbose, 2 = debug
    log_level = 2 if os.environ.get("KOTORDIFF_DEBUG") else (1 if os.environ.get("KOTORDIFF_VERBOSE") else 0)

    # Determine if we're doing 2-way or 3-way diff
    use_3way = mine_root is not None and mine_root.safe_isdir()
    base_root = mine_root if use_3way else older_root

    # Validate base_root exists (should always be true for valid inputs)
    if base_root is None or not base_root.exists():
        log_func(f"[Error] Base root path is invalid: {base_root}")
        return

    mode_str = "3-way" if use_3way else "2-way"
    log_func(f"Generating TSLPatcher changes.ini ({mode_str} diff mode)", separator_above=True)

    if log_level >= 2:
        log_func("[DEBUG] INI Generation Parameters:")
        log_func(f"[DEBUG]   Mode: {mode_str}")
        log_func(f"[DEBUG]   mine_root: {mine_root} (used: {use_3way})")
        log_func(f"[DEBUG]   older_root: {older_root}")
        log_func(f"[DEBUG]   yours_root: {yours_root}")
        log_func(f"[DEBUG]   base_root: {base_root}")
        log_func(f"[DEBUG]   out_path: {out_path}")

    # Collect all files
    log_func("Collecting files from directories...")
    base_files = {str(f.relative_to(base_root)): f for f in base_root.rglob("*") if f.is_file()} if base_root.safe_isdir() else {}
    yours_files = {str(f.relative_to(yours_root)): f for f in yours_root.rglob("*") if f.is_file()} if yours_root.safe_isdir() else {}
    all_rel = sorted(set(base_files.keys()) | set(yours_files.keys()))

    if log_level >= 1:
        log_func(f"[VERBOSE] Found {len(base_files)} files in {'mine' if use_3way else 'older'} installation")
        log_func(f"[VERBOSE] Found {len(yours_files)} files in yours installation")
        log_func(f"[VERBOSE] Total unique files to process: {len(all_rel)}")

    if log_level >= 2:
        log_func(f"[DEBUG] Sample base files (first 10): {list(base_files.keys())[:10]}")
        log_func(f"[DEBUG] Sample yours files (first 10): {list(yours_files.keys())[:10]}")

    # Track modifications by type
    modifications_by_type = ModificationsByType.create_empty()

    # Map casefolded rel -> actual rel from 'yours' for correct casing
    yours_rel_map: dict[str, str] = {}
    for rel in yours_files:
        yours_rel_map[rel.casefold()] = rel

    # Helper function to add file to InstallList
    def add_to_install_list(rel_path: str):
        actual_rel = yours_rel_map.get(rel_path.casefold(), rel_path)
        dest_folder = str(Path(actual_rel).parent)
        filename = Path(actual_rel).name

        if log_level >= 2:
            log_func(f"[DEBUG] add_to_install_list: rel_path={rel_path}")
            log_func(f"[DEBUG]   actual_rel={actual_rel}")
            log_func(f"[DEBUG]   dest_folder={dest_folder}")
            log_func(f"[DEBUG]   filename={filename}")

        # Normalize folder paths
        if dest_folder == ".":
            dest_folder = "Override"
            if log_level >= 1:
                log_func(f"[VERBOSE] Normalized '.' to 'Override' for {filename}")

        # Check if this file already exists in install list
        file_exists = False
        for install_file in modifications_by_type.install:
            install_dest = install_file.destination if install_file.destination != "." else "Override"
            install_filename = install_file.saveas or install_file.sourcefile
            if (
                install_dest.lower() == dest_folder.lower()
                and install_filename.lower() == filename.lower()
            ):
                file_exists = True
                break

        if not file_exists:
            # Create new InstallFile entry
            modifications_by_type.install.append(InstallFile(filename, destination=dest_folder))
            if log_level >= 2:
                log_func(f"[DEBUG] Added {filename} to folder {dest_folder}")
        elif log_level >= 2:
            log_func(f"[DEBUG] Skipped duplicate: {filename} in {dest_folder}")

    # Analyze each file
    log_func(f"Processing {len(all_rel)} files...")

    files_processed: int = 0
    files_skipped_removal: int = 0
    files_new: int = 0
    files_identical: int = 0
    files_modified: int = 0
    files_analyzed_2da: int = 0
    files_analyzed_gff: int = 0
    files_analyzed_tlk: int = 0
    files_analyzed_ssf: int = 0
    files_to_install: int = 0

    for idx, rel in enumerate(all_rel):
        files_processed += 1

        if log_level >= 2 and idx % 100 == 0:  # noqa: PLR2004
            log_func(f"[DEBUG] Progress: {idx}/{len(all_rel)} files processed")

        if should_skip_rel(rel):
            if log_level >= 2:  # noqa: PLR2004
                log_func(f"[DEBUG] Skipping rel (filter): {rel}")
            continue

        base_file = base_files.get(rel)
        yours_file = yours_files.get(rel)

        # Skip if file only exists in base
        if yours_file is None:
            files_skipped_removal += 1
            if log_level >= 1:
                log_func(f"[VERBOSE] Skipped removal (only in {'mine' if use_3way else 'older'}): {rel}")
            continue

        # Handle files that only exist in yours
        if base_file is None:
            files_new += 1
            if log_level >= 1:
                log_func(f"[VERBOSE] New file detected: {rel}")
            add_to_install_list(rel)
            continue

        # File exists in both - check if different
        if log_level >= 2:  # noqa: PLR2004
            log_func(f"[DEBUG] Comparing: {rel}")

        base_data = base_file.read_bytes()
        yours_data = yours_file.read_bytes()

        if base_data == yours_data:
            files_identical += 1
            if log_level >= 2:  # noqa: PLR2004
                log_func(f"[DEBUG] Identical (skipping): {rel}")
            continue

        files_modified += 1
        if log_level >= 1:
            log_func(f"[VERBOSE] Modified file: {rel} (size: {len(base_data)} -> {len(yours_data)})")

        # Try to analyze with diff analyzers
        ext = ext_of(Path(rel))
        analyzer = DiffAnalyzerFactory.get_analyzer(ext)

        if analyzer:
            try:
                if log_level >= 1:
                    log_func(f"[VERBOSE] Using {type(analyzer).__name__} for {rel}...")
                else:
                    log_func(f"Analyzing {rel}...")

                modifications = analyzer.analyze(base_data, yours_data, Path(rel).name)

                if modifications:
                    # Successfully analyzed - add to appropriate list
                    if ext.lower() in ("2da", "twoda"):
                        assert isinstance(modifications, Modifications2DA), f"Expected Modifications2DA, got {type(modifications)}"
                        modifications_by_type.twoda.append(modifications)
                        files_analyzed_2da += 1
                        if log_level >= 1:
                            log_func(f"[VERBOSE] Added 2DA modification for {rel}")
                    elif ext.lower() in gff_types:
                        assert isinstance(modifications, ModificationsGFF), f"Expected ModificationsGFF, got {type(modifications)}"
                        modifications_by_type.gff.append(modifications)
                        files_analyzed_gff += 1
                        if log_level >= 1:
                            log_func(f"[VERBOSE] Added GFF modification for {rel}")
                    elif ext.lower() == "tlk":
                        assert isinstance(modifications, ModificationsTLK), f"Expected ModificationsTLK, got {type(modifications)}"
                        modifications_by_type.tlk.append(modifications)
                        files_analyzed_tlk += 1
                        if log_level >= 1:
                            log_func(f"[VERBOSE] Added TLK modification for {rel}")
                    elif ext.lower() == "ssf":
                        assert isinstance(modifications, ModificationsSSF), f"Expected ModificationsSSF, got {type(modifications)}"
                        modifications_by_type.ssf.append(modifications)
                        files_analyzed_ssf += 1
                        if log_level >= 1:
                            log_func(f"[VERBOSE] Added SSF modification for {rel}")
                else:
                    if log_level >= 1:
                        log_func(f"[VERBOSE] Analyzer returned no modifications for {rel}, falling back to InstallList")
                    files_to_install += 1
                    add_to_install_list(rel)
                continue
            except Exception as e:  # noqa: BLE001
                log_func(f"[Warning] Failed to analyze {rel}: {universal_simplify_exception(e)}")
                if log_level >= 1:
                    log_func("[VERBOSE] Falling back to InstallList due to analysis error")
                files_to_install += 1
                add_to_install_list(rel)
                continue

        # Fallback to InstallList for modified files that couldn't be analyzed
        if log_level >= 1:
            log_func(f"[VERBOSE] No analyzer for .{ext}, adding to InstallList: {rel}")
        files_to_install += 1
        add_to_install_list(rel)

    # Print processing summary
    log_func("\nFile Processing Summary:")
    log_func(f"  Total files processed: {files_processed}")
    log_func(f"  Files skipped (removal): {files_skipped_removal}")
    log_func(f"  New files: {files_new}")
    log_func(f"  Identical files: {files_identical}")
    log_func(f"  Modified files: {files_modified}")
    log_func(f"  Files analyzed as 2DA: {files_analyzed_2da}")
    log_func(f"  Files analyzed as GFF: {files_analyzed_gff}")
    log_func(f"  Files analyzed as TLK: {files_analyzed_tlk}")
    log_func(f"  Files analyzed as SSF: {files_analyzed_ssf}")
    log_func(f"  Files added to InstallList: {files_to_install}")

    if log_level >= 2:
        log_func("\n[DEBUG] Install folder breakdown:")
        # Group InstallFile objects by folder
        files_by_folder: dict[str, list[str]] = {}
        for install_file in modifications_by_type.install:
            folder = install_file.destination if install_file.destination != "." else "Override"
            filename = install_file.saveas or install_file.sourcefile
            if folder not in files_by_folder:
                files_by_folder[folder] = []
            files_by_folder[folder].append(filename)

        for folder, filenames in files_by_folder.items():
            log_func(f"[DEBUG]   {folder}: {len(filenames)} files")
            max_files = 5
            if log_level >= 1:
                for fname in filenames[:max_files]:
                    log_func(f"[DEBUG]     - {fname}")
                if len(filenames) > max_files:
                    log_func(f"[DEBUG]     ... and {len(filenames) - max_files} more")

    # Generate INI content
    if log_level >= 1:
        log_func("\n[VERBOSE] Serializing modifications to INI format...")

    serializer = TSLPatcherINISerializer()
    ini_content = serializer.serialize(modifications_by_type)

    if log_level >= 2:
        log_func(f"[DEBUG] Generated INI content length: {len(ini_content)} characters")
        log_func("[DEBUG] INI sections preview (first 50 lines):")
        for i, line in enumerate(ini_content.split("\n")[:50]):
            log_func(f"[DEBUG]   {i + 1}: {line}")

    # Write the INI file
    out_path.write_text(ini_content, encoding="utf-8")
    log_func(f"\nSuccessfully generated changes.ini at: {out_path}")
    log_func(f"  - 2DA patches: {len(modifications_by_type.twoda)}")
    log_func(f"  - GFF patches: {len(modifications_by_type.gff)}")
    log_func(f"  - TLK patches: {len(modifications_by_type.tlk)}")
    log_func(f"  - SSF patches: {len(modifications_by_type.ssf)}")
    log_func(f"  - NCS patches: {len(modifications_by_type.ncs)}")
    log_func(f"  - Install files: {len(modifications_by_type.install)}")

    # Analyze 2DA memory references (for linking patches)
    if modifications_by_type.twoda:
        twoda_count = len(modifications_by_type.twoda)
        log_func(f"\nBuilding 2DA memory reference links for {twoda_count} 2DA modifications...")
        try:
            analyze_2da_memory_references(
                modifications_by_type.twoda,
                base_root,  # Search in base installation for references
                modifications_by_type.gff,  # Append GFF modifications here
            )
            log_func("2DA memory analysis complete. Added linking patches:")
            gff_2da_ref_count = sum(
                len([mod for mod in m.modifiers if isinstance(mod, ModifyFieldGFF) and "2DAMEMORY" in str(mod.value)])
                for m in modifications_by_type.gff
            )
            log_func(f"  GFF patches for 2DA refs: {gff_2da_ref_count}")
        except Exception as e:  # noqa: BLE001
            log_func(f"[Warning] 2DA memory analysis failed: {e.__class__.__name__}: {e}")
            log_func("Full traceback:")
            for line in traceback.format_exc().splitlines():
                log_func(f"  {line}")
    # Count unique folders
    unique_folders: set[str] = {
        install_file.destination
        if install_file.destination != "."
        else "Override"
        for install_file in modifications_by_type.install
    }
    log_func(f"  - Install folders: {len(unique_folders)}")


def run_differ3_from_args(
    mine: Path,
    older: Path,
    yours: Path,
    config: IniGenerationConfig,
):
    """Run 3-way diff from command-line arguments."""
    # Print header
    log_output()
    log_output("3-way diff (mine → older → yours)")
    log_output(f"mine:   {mine}")
    log_output(f"older:  {older}")
    log_output(f"yours:  {yours}")
    log_output()

    # Print udiff for older -> yours
    if mine.safe_isfile() and older.safe_isfile() and yours.safe_isfile():
        diff3_files_udiff(mine, older, yours, log_output)
    elif mine.safe_isdir() and older.safe_isdir() and yours.safe_isdir():
        files_old: set[str] = walk_files(older)
        files_new: set[str] = walk_files(yours)
        for rel in sorted(files_old | files_new):
            if should_skip_rel(rel):
                continue
            diff3_files_udiff(mine / rel, older / rel, yours / rel, log_output)
    else:
        msg = "--mine, --older, --yours must all be files or all be directories"
        raise ValueError(msg)

    if config.generate_ini:
        out_path_resolved: Path = config.ini if config.ini is not None else Path("changes.ini").resolve()
        generate_changes_ini(mine, older, yours, out_path=out_path_resolved, log_func=log_output)


# ---------------------------------------------------------------------------
# Orchestration functions with global config wrappers
# ---------------------------------------------------------------------------


def run_differ_from_args(
    mine: Path,
    older: Path,
    *,
    filters: list[str] | None = None,
    incremental_writer: IncrementalTSLPatchDataWriter | None = None,
) -> bool | None:
    """Run 2-way differ using global config.

    Raises:
        AssertionError: If global config is not initialized (programming error)
    """
    if _global_config.parser_args is None:
        error_msg = "Global config parser_args is None - must call run_application first"
        raise AssertionError(error_msg)

    # Extract config values once for type safety
    compare_hashes_enabled: bool = _global_config.parser_args.compare_hashes

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

    def diff_files_wrapper(
        file1: Path,
        file2: Path,
        *,
        skip_nss: bool = False,
    ) -> bool | None:
        """Wrapper for diff_files that adds logging."""
        c_file1: Path = Path.pathify(file1).resolve()
        c_file2: Path = Path.pathify(file2).resolve()
        c_file1_rel: Path = relative_path_from_to(c_file2, c_file1)
        c_file2_rel: Path = relative_path_from_to(c_file1, c_file2)

        if not c_file1.safe_isfile():
            log_output(f"Missing file:\t{c_file1_rel}")
            return False
        if not c_file2.safe_isfile():
            log_output(f"Missing file:\t{c_file2_rel}")
            return False

        # Prefer udiff for text-like files
        ext = c_file1_rel.suffix.casefold()[1:]
        if ext in {"txi"}:
            print_udiff(c_file1, c_file2, f"(old){c_file1}", f"(new){c_file2}", log_output)

        if is_capsule_file(c_file1_rel.name):
            return diff_capsule_files(
                c_file1,
                c_file2,
                c_file1_rel,
                c_file2_rel,
                log_func=log_output,
                skip_nss=skip_nss,
                compare_hashes=compare_hashes_enabled,
                modifications_by_type=_global_config.modifications_by_type,
                incremental_writer=incremental_writer,
            )

        ctx = DiffContext(c_file1_rel, c_file2_rel, c_file1_rel.suffix.casefold()[1:], skip_nss=skip_nss)
        return diff_data_wrapper(c_file1, c_file2, ctx, incremental_writer)

    def diff_capsule_files_wrapper(
        c_file1: Path,
        c_file2: Path,
        c_file1_rel: Path,
        c_file2_rel: Path,
        *,
        skip_nss: bool = False,
    ) -> bool | None:
        """Wrapper for diff_capsule_files."""
        return diff_capsule_files(
            c_file1,
            c_file2,
            c_file1_rel,
            c_file2_rel,
            skip_nss=skip_nss,
            log_func=log_output,
            compare_hashes=compare_hashes_enabled,
            modifications_by_type=_global_config.modifications_by_type,
            incremental_writer=incremental_writer,
        )

    def diff_directories_wrapper(
        dir1: Path,
        dir2: Path,
        *,
        filters: list[str] | None = None,
        skip_nss: bool = False,
    ) -> bool | None:
        """Wrapper for diff_directories."""
        return diff_directories(
            Path.pathify(dir1).resolve(),
            Path.pathify(dir2).resolve(),
            filters=filters,
            skip_nss=skip_nss,
            log_func=log_func_wrapper,
            diff_files_func=diff_files_wrapper,
            diff_cache=_global_config.diff_cache,
            modifications_by_type=_global_config.modifications_by_type,
            incremental_writer=incremental_writer,
        )

    def diff_installs_wrapper(
        install1: Path,
        install2: Path,
        *,
        filters: list[str] | None = None,
    ) -> bool | None:
        """Wrapper for diff_installs_implementation."""
        return diff_installs_implementation(
            Path.pathify(install1).resolve(),
            Path.pathify(install2).resolve(),
            filters=filters,
            log_func=log_func_wrapper,
            diff_files_func=diff_files_wrapper,
            diff_directories_func=diff_directories_wrapper,
        )

    def diff_container_vs_installation_wrapper(
        container_path: Path,
        installation: Installation,
        *,
        container_first: bool = True,
    ) -> bool | None:
        """Wrapper for diff_container_vs_installation."""
        return diff_container_vs_installation(
            container_path=container_path,
            installation=installation,
            container_first=container_first,
            log_func=log_func_wrapper,
            diff_data_func=diff_data_wrapper,
        )

    def diff_resource_vs_installation_wrapper(
        resource_path: Path,
        installation: Installation,
        *,
        resource_first: bool = True,
    ) -> bool | None:
        """Wrapper for diff_resource_vs_installation."""
        return diff_resource_vs_installation(
            resource_path=resource_path,
            installation=installation,
            resource_first=resource_first,
            log_func=log_func_wrapper,
            diff_data_func=diff_data_wrapper,
        )

    def diff_installs_with_objects_wrapper(
        inst1: Installation,
        inst2: Installation,
        *,
        filters: list[str] | None = None,
    ) -> bool | None:
        """Wrapper for diff_installs_with_objects.

        Args:
            inst1: First Installation object
            inst2: Second Installation object
            filters: Optional list of filters

        Returns:
            True if installations are identical, False if different, None on error
        """
        return diff_installs_with_objects(
            installation1=inst1,
            installation2=inst2,
            filters=filters,
            log_func=log_func_wrapper,
            diff_installs_func=diff_installs_wrapper,
            compare_hashes=compare_hashes_enabled,
            modifications_by_type=_global_config.modifications_by_type,
            incremental_writer=incremental_writer,
        )

    # Call the implementation with all wrappers
    return run_differ_from_args_impl(
        mine=mine,
        older=older,
        filters=filters,
        log_func=log_func_wrapper,
        diff_directories_func=diff_directories_wrapper,
        diff_files_func=diff_files_wrapper,
        diff_container_vs_installation_func=diff_container_vs_installation_wrapper,
        diff_resource_vs_installation_func=diff_resource_vs_installation_wrapper,
        diff_installs_with_objects_func=diff_installs_with_objects_wrapper,
    )
