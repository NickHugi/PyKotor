"""Launch command implementation."""
from __future__ import annotations

import os
import subprocess

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import Namespace
    from logging import Logger

from kotornasher.cfg_parser import load_config
from kotornasher.commands.install import cmd_install, find_kotor_install_dir


def find_kotor_executable() -> Path | None:
    """Find the KOTOR game executable."""
    # Check for explicit gameBin setting
    if "KOTOR_BIN" in os.environ:
        path = Path(os.environ["KOTOR_BIN"])
        if path.exists():
            return path

    # Try to find installation directory first
    install_dir = find_kotor_install_dir()
    if install_dir is None:
        return None

    # Look for executable
    import platform

    system = platform.system()

    if system == "Windows":
        exe_names = ["swkotor.exe", "KOTOR.exe"]
    elif system == "Darwin":  # macOS
        exe_names = ["KOTOR", "Knights of the Old Republic"]
    else:  # Linux
        exe_names = ["swkotor", "KOTOR"]

    for exe_name in exe_names:
        exe_path = install_dir / exe_name
        if exe_path.exists():
            return exe_path

        # Try in parent directory (for Steam installs)
        parent_exe = install_dir.parent / exe_name
        if parent_exe.exists():
            return parent_exe

    return None


def cmd_launch(args: Namespace, logger: Logger) -> int:
    """Handle launch command - install and launch game.

    Args:
    ----
        args: Parsed command line arguments
        logger: Logger instance

    Returns:
    -------
        Exit code (0 for success, non-zero for error)
    """
    # Run install first
    logger.info("Installing...")
    install_result = cmd_install(args, logger)
    if install_result != 0:
        logger.error("Install failed, aborting launch")
        return install_result

    # Determine which executable to use
    if hasattr(args, "gameBin") and args.gameBin:
        game_bin = Path(args.gameBin)
    elif hasattr(args, "serverBin") and args.serverBin:
        game_bin = Path(args.serverBin)
    else:
        game_bin = find_kotor_executable()

    if game_bin is None or not game_bin.exists():
        logger.error("KOTOR executable not found")
        logger.info("Use --gameBin to specify location")
        return 1

    logger.info(f"Launching: {game_bin}")

    # Determine launch command based on command alias
    command = args.command if hasattr(args, "command") else "launch"

    try:
        if command == "test":
            # Launch with first character (if supported)
            logger.info("Test mode: launching game with first character")
            subprocess.Popen([str(game_bin)])
        elif command == "serve":
            # Launch as server (if supported)
            logger.info("Server mode: launching game as server")
            subprocess.Popen([str(game_bin)])
        else:
            # Normal launch (play/launch)
            subprocess.Popen([str(game_bin)])

        logger.info("Game launched successfully")
    except Exception as e:
        logger.error(f"Failed to launch game: {e}")
        return 1

    return 0



