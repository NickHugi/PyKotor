from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path
from threading import Event
from typing import TYPE_CHECKING

from loggerplus import RobustLogger

from kitgenerator import __version__
from kitgenerator.extract import extract_kit
from pykotor.extract.installation import Installation

if TYPE_CHECKING:
    pass

CURRENT_VERSION = __version__


def parse_args() -> Namespace:
    """Parse command line arguments."""
    parser = ArgumentParser(
        description="KitGenerator - Extract kit resources from KOTOR module files (RIM/ERF)."
    )

    parser.add_argument(
        "--installation",
        type=str,
        help="Path to KOTOR installation (if not provided, will prompt in GUI mode)",
    )
    parser.add_argument(
        "--module",
        type=str,
        help="Module name (e.g., danm13) - extension and path will be stripped",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output path for the kit",
    )
    parser.add_argument(
        "--kit-id",
        type=str,
        help="Kit ID (defaults to module name)",
    )
    parser.add_argument(
        "--console",
        action="store_true",
        help="Show console window even in GUI mode",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="info",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Logging level (default: info)",
    )

    return parser.parse_args()


def execute_cli(cmdline_args: Namespace):
    """Execute command line operations in CLI mode.

    Args:
    ----
        cmdline_args: Command line arguments
    """
    logger = RobustLogger()
    if cmdline_args.log_level:
        import logging

        level_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL,
        }
        logger.setLevel(level_map.get(cmdline_args.log_level, logging.INFO))

    # Validate required arguments
    if not cmdline_args.installation:
        print("[Error] No installation path specified. Use --installation <path>", file=sys.stderr)  # noqa: T201
        sys.exit(1)

    if not cmdline_args.module:
        print("[Error] No module name specified. Use --module <name>", file=sys.stderr)  # noqa: T201
        sys.exit(1)

    if not cmdline_args.output:
        print("[Error] No output path specified. Use --output <path>", file=sys.stderr)  # noqa: T201
        sys.exit(1)

    # Validate installation path
    installation_path = Path(cmdline_args.installation)
    if not installation_path.exists():
        print(f"[Error] Installation path does not exist: {installation_path}", file=sys.stderr)  # noqa: T201
        sys.exit(1)

    try:
        installation = Installation(installation_path)
    except Exception as e:  # noqa: BLE001
        logger.exception("Invalid installation directory")
        print(f"[Error] Invalid installation directory: {e.__class__.__name__}: {e}", file=sys.stderr)  # noqa: T201
        sys.exit(1)

    # Normalize module name
    module_path = Path(cmdline_args.module)
    module_name = module_path.stem.lower()

    # Validate output path
    output_path = Path(cmdline_args.output)
    output_path.mkdir(parents=True, exist_ok=True)

    # Get kit ID
    kit_id = cmdline_args.kit_id.strip().lower() if cmdline_args.kit_id else None

    # Execute extraction
    try:
        print(f"[Info] Installing kit from module: {module_name}")  # noqa: T201
        print(f"[Info] Installation: {installation_path}")  # noqa: T201
        print(f"[Info] Output: {output_path}")  # noqa: T201
        if kit_id:
            print(f"[Info] Kit ID: {kit_id}")  # noqa: T201

        extract_kit(
            installation,
            module_name,
            output_path,
            kit_id=kit_id,
            logger=logger,
        )

        print("[Info] Kit extraction completed successfully!")  # noqa: T201
        sys.exit(0)

    except Exception as e:  # noqa: BLE001
        logger.exception("CLI operation failed")
        from utility.error_handling import universal_simplify_exception

        error_name, msg = universal_simplify_exception(e)
        print(f"[Error] {error_name}: {msg}", file=sys.stderr)  # noqa: T201
        sys.exit(1)

