#!/usr/bin/env python3
"""KotorDiff CLI entry point - handles argument parsing only."""
from __future__ import annotations

import io
import os
import pathlib
import sys
import traceback

from argparse import ArgumentParser

from pykotor.extract.installation import Installation
from utility.system.path import Path

# Configure sys.path for development mode
if getattr(sys, "frozen", False) is False:

    def update_sys_path(path):
        working_dir = str(path)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.append(working_dir)

    pykotor_path = pathlib.Path(__file__).parents[4] / "Libraries" / "PyKotor" / "src" / "pykotor"
    if pykotor_path.exists():
        update_sys_path(pykotor_path.parent)
    utility_path = pathlib.Path(__file__).parents[4] / "Libraries" / "Utility" / "src" / "utility"
    if utility_path.exists():
        update_sys_path(utility_path.parent)
    kotordiff_path = pathlib.Path(__file__).parent
    if kotordiff_path.exists():
        update_sys_path(kotordiff_path.parent)

from kotordiff.app import KotorDiffConfig, run_application
from kotordiff.cli_utils import normalize_path_arg

CURRENT_VERSION = "1.0.0"


def create_argument_parser() -> ArgumentParser:
    """Create and configure the argument parser."""
    parser = ArgumentParser(
        description="Finds differences between KOTOR files/dirs. Supports comparisons across any number of paths."
    )

    # Path arguments (multiple aliases for compatibility)
    parser.add_argument(
        "--path1", type=str,
        help="Path to compare. Multiple path flags can be supplied; at least two paths are required."
    )
    parser.add_argument(
        "--path2", type=str,
        help="Additional path to compare."
    )
    parser.add_argument(
        "--path3", type=str,
        help="Additional path to compare."
    )
    parser.add_argument(
        "--path",
        action="append",
        dest="extra_paths",
        help="Additional paths for N-way comparison (can be used multiple times). "
        "Example: --path path4 --path path5"
    )

    # Output options
    parser.add_argument(
        "--tslpatchdata",
        type=str,
        help="Path where tslpatchdata folder should be created. Requires at least one path to be an Installation.",
    )
    parser.add_argument(
        "--ini",
        type=str,
        default="changes.ini",
        help="Filename for changes.ini (not path, just filename). Requires --tslpatchdata. Must have .ini extension (default: changes.ini).",
    )
    # Cache options removed
    parser.add_argument(
        "--output-log",
        type=str,
        help="Filepath of the desired output logfile"
    )

    # Logging and display options
    parser.add_argument(
        "--log-level",
        type=str,
        default="info",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Logging level (default: info)",
    )
    parser.add_argument(
        "--output-mode",
        type=str,
        default="full",
        choices=["full", "diff_only", "quiet"],
        help="Output mode: full (all logs), diff_only (only diff results), quiet (minimal) (default: full)",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output"
    )

    # Comparison options
    parser.add_argument(
        "--compare-hashes",
        type=bool,
        default=True,
        help="Compare hashes of any unsupported file/resource type (default is True)",
    )
    parser.add_argument(
        "--filter",
        action="append",
        help="Filter specific files/modules for installation-wide diffs (can be used multiple times). "
        "Examples: 'tat_m18ac' for module, 'some_character.utc' for specific resource",
    )
    parser.add_argument(
        "--logging",
        type=bool,
        default=True,
        help="Whether to log the results to a file or not (default is True)",
    )
    parser.add_argument(
        "--use-profiler",
        type=bool,
        default=False,
        help="Use cProfile to find where most of the execution time is taking place in source code.",
    )

    return parser


def _debug_print_argv(label: str, argv: list[str]):
    """Print argv for debugging purposes."""
    print(f"DEBUG: {label}:")
    for idx, arg in enumerate(argv):
        print(f"  [{idx}] {arg!r}")


def _reconstruct_mangled_fragments(parts: list[str], start_index: int) -> tuple[list[str], int]:
    """Reconstruct mangled argument fragments from PowerShell.

    Returns:
        Tuple of (reconstructed arguments, next index to process)
    """
    reconstructed: list[str] = []
    i = start_index

    for idx in range(1, len(parts)):
        part = "--" + parts[idx]
        path_fragments = [part]
        i += 1

        # Collect fragments until we hit a closing quote or another option
        while i < len(sys.argv):
            next_fragment = sys.argv[i]
            if next_fragment.startswith("--"):
                i -= 1
                break
            path_fragments.append(next_fragment)
            if next_fragment.endswith('"'):
                break
            i += 1

        full_arg = " ".join(path_fragments)
        reconstructed.append(full_arg)

    return reconstructed, i


def _reconstruct_mangled_argv(argv: list[str]) -> list[str]:
    """Detect and fix severely mangled arguments from PowerShell."""
    reconstructed_argv: list[str] = [argv[0]]  # Keep the script name
    i: int = 1

    while i < len(argv):
        arg: str = argv[i]

        # Check if this arg contains multiple option flags (sign of mangling)
        if arg.startswith("--") and '" --' in arg:
            # This is severely mangled - split it back up
            parts: list[str] = arg.split('" --')
            reconstructed_argv.append(parts[0])

            # Reassemble fragments
            fragments, i = _reconstruct_mangled_fragments(parts, i)
            reconstructed_argv.extend(fragments)
        else:
            reconstructed_argv.append(arg)

        i += 1

    return reconstructed_argv


def _normalize_path_argument(arg: str, next_arg: str | None = None) -> tuple[list[str], bool]:
    """Normalize a path argument and return the result.

    Returns:
        Tuple of (normalized arguments to append, whether next_arg was consumed)
    """
    PATH_PREFIXES = ("--path", "--path1", "--path2", "--path3")

    if not arg.startswith(PATH_PREFIXES):
        return [arg], False

    if "=" in arg:
        key, value = arg.split("=", 1)
        normalized = normalize_path_arg(value)
        return [f"{key}={normalized}" if normalized else arg], False

    # No equals sign, value should be in next_arg
    if next_arg is None:
        return [arg], False

    normalized = normalize_path_arg(next_arg)
    return [arg, normalized if normalized else next_arg], True


def _normalize_argv_paths(argv: list[str]) -> list[str]:
    """Normalize path arguments in argv."""
    fixed_argv = []
    i = 0

    while i < len(argv):
        arg = argv[i]
        next_arg = argv[i + 1] if i + 1 < len(argv) else None

        if arg.startswith(("--path", "--path1", "--path2", "--path3")):
            normalized_args, consumed_next = _normalize_path_argument(arg, next_arg)
            fixed_argv.extend(normalized_args)
            if consumed_next:
                i += 1
        elif i > 0 and not arg.startswith("-"):  # Positional argument
            normalized = normalize_path_arg(arg)
            fixed_argv.append(normalized if normalized else arg)
        else:
            fixed_argv.append(arg)

        i += 1

    return fixed_argv


def preprocess_argv_for_windows():
    """Pre-process sys.argv to fix Windows PowerShell quote escaping issues."""
    # Log level: 0 = normal, 1 = verbose, 2 = debug
    log_level = 2 if os.environ.get("KOTORDIFF_DEBUG") else (1 if os.environ.get("KOTORDIFF_VERBOSE") else 0)

    if log_level >= 2:  # noqa: PLR2004
        _debug_print_argv("Original sys.argv", sys.argv)

    # Reconstruct mangled arguments
    reconstructed_argv = _reconstruct_mangled_argv(sys.argv)

    if log_level >= 2:  # noqa: PLR2004
        print()
        _debug_print_argv("Reconstructed sys.argv", reconstructed_argv)

    # Normalize path arguments
    fixed_argv = _normalize_argv_paths(reconstructed_argv)

    sys.argv = fixed_argv

    if log_level >= 2:  # noqa: PLR2004
        print()
        _debug_print_argv("Fixed sys.argv", sys.argv)
        print()


def main():
    """Main CLI entry point."""
    # Configure console for UTF-8 output on Windows
    if sys.platform == "win32":
        try:
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer,
                encoding="utf-8",
                errors="replace",
                line_buffering=True,
            )
            sys.stderr = io.TextIOWrapper(
                sys.stderr.buffer,
                encoding="utf-8",
                errors="replace",
                line_buffering=True,
            )
        except Exception:  # noqa: BLE001
            print("Failed to configure console for UTF-8 output on Windows")
            print(traceback.format_exc())

    print(f"KotorDiff version {CURRENT_VERSION}")

    # Pre-process argv for Windows PowerShell quoting issues
    preprocess_argv_for_windows()

    # Create and parse arguments
    parser: ArgumentParser = create_argument_parser()
    args, unknown_args = parser.parse_known_args()

    # Cache options removed

    # Gather all path inputs (already normalized by preprocess_argv_for_windows)
    raw_path_inputs: list[str] = []

    if hasattr(args, "path1") and args.path1:
        raw_path_inputs.append(args.path1)
    if hasattr(args, "path2") and args.path2:
        raw_path_inputs.append(args.path2)
    if hasattr(args, "path3") and args.path3:
        raw_path_inputs.append(args.path3)

    if hasattr(args, "extra_paths") and args.extra_paths:
        raw_path_inputs.extend(args.extra_paths)

    # Treat remaining positional arguments as additional paths
    raw_path_inputs.extend(unknown_args)

    # Store all paths on args for downstream processing
    args.paths = raw_path_inputs

    # Clear legacy attributes
    if hasattr(args, "path1"):
        args.path1 = None
    if hasattr(args, "path2"):
        args.path2 = None
    if hasattr(args, "path3"):
        args.path3 = None
    if hasattr(args, "extra_paths"):
        args.extra_paths = None

    # Convert string paths to Path/Installation objects
    resolved_paths: list[Path | Installation] = []
    for path_str in args.paths:
        path_obj = Path(path_str)
        try:
            # Try to create an Installation object (for KOTOR installations)
            installation = Installation(path_obj)
            resolved_paths.append(installation)
            print(f"[DEBUG] Loaded Installation for: {path_str}")
        except Exception as e:
            # Fall back to Path object (for folders/files)
            resolved_paths.append(path_obj)
            print(f"[DEBUG] Using Path (not Installation) for: {path_str}")
            print(f"[DEBUG] Installation load failed: {e.__class__.__name__}: {e}")
            print(traceback.format_exc())

    # Create configuration object
    config = KotorDiffConfig(
        paths=resolved_paths,
        tslpatchdata_path=Path(args.tslpatchdata) if args.tslpatchdata else None,
        ini_filename=getattr(args, "ini", "changes.ini"),
        output_log_path=Path(args.output_log) if args.output_log else None,
        log_level=getattr(args, "log_level", "info"),
        output_mode=getattr(args, "output_mode", "full"),
        use_colors=not getattr(args, "no_color", False),
        compare_hashes=not bool(args.compare_hashes),  # Note: inverted logic from original
        use_profiler=bool(args.use_profiler),
        filters=getattr(args, "filter", None),
        logging_enabled=bool(args.logging is None or args.logging),
    )

    # Run the application
    exit_code: int = run_application(config)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

