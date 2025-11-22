"""Install command implementation."""
from __future__ import annotations

import os
import shutil

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import Namespace
    from logging import Logger

from kotornasher.cfg_parser import load_config
from kotornasher.commands.pack import cmd_pack, should_overwrite_file


def find_kotor_install_dir() -> Path | None:
    """Find the KOTOR installation directory."""
    # Check environment variable first
    if "KOTOR_PATH" in os.environ:
        path = Path(os.environ["KOTOR_PATH"])
        if path.exists():
            return path

    # Check common locations
    import platform

    system = platform.system()

    if system == "Windows":
        possible_paths = [
            Path.home() / "Documents" / "KotOR",
            Path.home() / "Documents" / "KOTOR",
            Path("C:/Program Files (x86)/Steam/steamapps/common/swkotor"),
            Path("C:/Program Files/Steam/steamapps/common/swkotor"),
        ]
    elif system == "Darwin":  # macOS
        possible_paths = [
            Path.home() / "Library" / "Application Support" / "Knights of the Old Republic",
            Path.home() / "Documents" / "KotOR",
        ]
    else:  # Linux
        possible_paths = [
            Path.home() / ".local" / "share" / "aspyr-media" / "kotor",
            Path.home() / ".steam" / "steam" / "steamapps" / "common" / "Knights of the Old Republic",
        ]

    for path in possible_paths:
        if path.exists():
            return path

    return None


def cmd_install(args: Namespace, logger: Logger) -> int:
    """Handle install command - pack and install target.

    Args:
    ----
        args: Parsed command line arguments
        logger: Logger instance

    Returns:
    -------
        Exit code (0 for success, non-zero for error)
    """
    # Load configuration
    config = load_config(logger)
    if config is None:
        return 1

    # Run pack unless --noPack
    if not getattr(args, "noPack", False):
        logger.info("Packing...")
        pack_result = cmd_pack(args, logger)
        if pack_result != 0:
            logger.error("Pack failed, aborting install")
            return pack_result

    # Determine install directory
    if hasattr(args, "installDir") and args.installDir:
        install_dir = Path(args.installDir)
    else:
        install_dir = find_kotor_install_dir()

    if install_dir is None or not install_dir.exists():
        logger.error("KOTOR installation directory not found")
        logger.info("Use --installDir to specify location")
        return 1

    logger.info(f"Installing to: {install_dir}")

    # Determine targets
    target_names = args.targets if args.targets else [None]
    if "all" in target_names:
        targets = config.targets
    else:
        targets = []
        for name in target_names:
            target = config.get_target(name)
            if target is None:
                if name:
                    logger.error(f"Target not found: {name}")
                else:
                    logger.error("No default target found")
                return 1
            targets.append(target)

    # Install each target
    for target in targets:
        target_name = target.get("name", "unnamed")
        logger.info(f"Installing target: {target_name}")

        # Determine source file
        if hasattr(args, "install_file") and args.install_file:
            source_file = Path(args.install_file)
        else:
            output_filename = config.resolve_target_value(target, "file")
            if not output_filename:
                logger.error("No file specified for target")
                return 1
            source_file = config.root_dir / output_filename

        if not source_file.exists():
            logger.error(f"Source file not found: {source_file}")
            return 1

        # Determine destination based on file type
        suffix = source_file.suffix.lower()
        if suffix == ".mod":
            dest_dir = install_dir / "modules"
        elif suffix in (".erf", ".rim"):
            dest_dir = install_dir / "override"
        elif suffix == ".hak":
            dest_dir = install_dir / "haks"
        else:
            dest_dir = install_dir / "override"
            logger.warning(f"Unknown file type {suffix}, installing to override")

        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file = dest_dir / source_file.name

        # Check if destination file exists
        if dest_file.exists():
            source_time = source_file.stat().st_mtime
            overwrite_mode = getattr(args, "overwriteInstalledFile", "ask")
            if not should_overwrite_file(dest_file, source_time, overwrite_mode, logger):
                logger.info(f"Keeping existing file: {dest_file}")
                continue

        # Copy file
        try:
            shutil.copy2(source_file, dest_file)
            logger.info(f"Installed: {dest_file}")
        except Exception as e:
            logger.error(f"Failed to install {source_file.name}: {e}")
            return 1

    logger.info("Installation complete")
    return 0



