"""Config command implementation."""
from __future__ import annotations

import os
import platform

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import Namespace
    from logging import Logger

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[import-not-found, no-redef]

try:
    import tomli_w
except ModuleNotFoundError:
    # Fallback to manual TOML writing if tomli_w not available
    tomli_w = None  # type: ignore[assignment]


def get_config_dir() -> Path:
    """Get the configuration directory based on platform."""
    system = platform.system()
    if system == "Windows":
        base = Path(os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming")))
        return base / "kotornasher"
    else:  # Linux, Mac
        base = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
        return base / "kotornasher"


def get_global_config_path() -> Path:
    """Get the global configuration file path."""
    return get_config_dir() / "user.cfg"


def get_local_config_path() -> Path:
    """Get the local configuration file path (in current package)."""
    return Path.cwd() / ".kotornasher" / "user.cfg"


def load_config_file(config_path: Path) -> dict:
    """Load a configuration file."""
    if not config_path.exists():
        return {}

    with config_path.open("rb") as f:
        return tomllib.load(f)


def save_config_file(config_path: Path, data: dict):
    """Save a configuration file."""
    config_path.parent.mkdir(parents=True, exist_ok=True)

    if tomli_w:
        with config_path.open("wb") as f:
            tomli_w.dump(data, f)
    else:
        # Manual TOML writing fallback
        with config_path.open("w", encoding="utf-8") as f:
            for key, value in data.items():
                if isinstance(value, str):
                    f.write(f'{key} = "{value}"\n')
                elif isinstance(value, bool):
                    f.write(f"{key} = {str(value).lower()}\n")
                elif isinstance(value, (int, float)):
                    f.write(f"{key} = {value}\n")
                else:
                    f.write(f'{key} = "{value}"\n')


def cmd_config(args: Namespace, logger: Logger) -> int:
    """Handle config command.

    Args:
    ----
        args: Parsed command line arguments
        logger: Logger instance

    Returns:
    -------
        Exit code (0 for success, non-zero for error)
    """
    # Determine which config file to use
    if args.local:
        config_path = get_local_config_path()
        scope = "local"
    else:
        config_path = get_global_config_path()
        scope = "global"

    # Load existing configuration
    config_data = load_config_file(config_path)

    # Handle list operation
    if args.list:
        if not config_data:
            logger.info(f"No {scope} configuration set")
            return 0

        logger.info(f"{scope.capitalize()} configuration ({config_path}):")
        for key, value in sorted(config_data.items()):
            logger.info(f"  {key} = {value}")
        return 0

    # Handle unset operation
    if args.unset:
        if not args.key:
            logger.error("Key required for --unset operation")
            return 1

        if args.key in config_data:
            del config_data[args.key]
            save_config_file(config_path, config_data)
            logger.info(f"Unset {scope} config: {args.key}")
            return 0
        else:
            logger.warning(f"Key not found in {scope} config: {args.key}")
            return 0

    # Handle get operation (default if only key provided)
    if args.key and not args.value and not args.set:
        value = config_data.get(args.key)
        if value is None:
            logger.info(f"{args.key} is not set in {scope} config")
        else:
            logger.info(str(value))
        return 0

    # Handle set operation (default if both key and value provided)
    if args.key and args.value:
        config_data[args.key] = args.value
        save_config_file(config_path, config_data)
        logger.info(f"Set {scope} config: {args.key} = {args.value}")
        return 0

    # No operation specified
    logger.error("No configuration operation specified. Use --get, --set, --unset, or --list")
    return 1

