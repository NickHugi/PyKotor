#!/usr/bin/env python3
"""CLI utilities for KotorDiff including path normalization and argument handling."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse

    from pathlib import Path


def normalize_path_arg(path_str: str | None) -> str | None:
    """Normalize a path argument by stripping quotes and handling Windows path issues."""
    if not path_str:
        return None

    # Strip leading/trailing whitespace
    path_str = path_str.strip()

    if not path_str:
        return None

    # Handle Windows PowerShell quote escaping issues where trailing backslash escapes the quote
    # This manifests as paths like: C:\Program Files (x86)\Steam\steamapps\common\swkotor" C:\Program
    # We need to detect and fix this by finding where the actual path likely ends

    # Check if we have what looks like a mangled path (has a quote in the middle followed by space and more path)
    if '"' in path_str and " " in path_str:
        # Try to find the actual path end - look for the quote followed by space
        quote_space_idx = path_str.find('" ')
        if quote_space_idx > 0:
            # Take everything before the quote as the path
            path_str = path_str[:quote_space_idx]

    # Strip quotes if present (handles both single and double quotes)
    if (path_str.startswith('"') and path_str.endswith('"')) or (path_str.startswith("'") and path_str.endswith("'")):
        path_str = path_str[1:-1]

    # Remove any remaining quotes that might be embedded
    path_str = path_str.replace('"', "").replace("'", "")

    # Strip trailing backslashes that may have been used before quotes
    path_str = path_str.rstrip("\\").rstrip("/")

    # Final cleanup
    path_str = path_str.strip()

    return path_str if path_str else None


def is_kotor_install_dir(path: Path) -> bool | None:
    """Check if a path is a KOTOR installation directory."""
    return path.is_dir() and path.joinpath("chitin.key").is_file()


def prompt_for_path(title: str) -> str:
    """Prompt the user for a path input."""
    user_input = input(f"{title}: ").strip()
    return normalize_path_arg(user_input) or ""


def print_path_error_with_help(path: Path, parser: argparse.ArgumentParser) -> None:
    """Print error message for invalid path with helpful quoting guidance."""
    print("Invalid path:", path)
    # Detect if this might be a quoting issue
    path_str = str(path)
    if '"' in path_str or not path.parent.exists():
        print("\nNote: If using paths with spaces and trailing backslashes in PowerShell:")
        print('  - Remove trailing backslash: --path1="C:\\Program Files\\folder"')
        print('  - Or double the backslash: --path1="C:\\Program Files\\folder\\\\"')
        print('  - Or use forward slashes: --path1="C:/Program Files/folder/"')
    if parser:
        parser.print_help()

