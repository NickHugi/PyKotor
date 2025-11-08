from __future__ import annotations

import os
import sys
import tempfile

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import IntEnum
from pathlib import Path
from typing import TYPE_CHECKING

from holopatcher.config import CURRENT_VERSION
from pykotor.common.misc import Game
from pykotor.common.stream import BinaryReader
from pykotor.extract.file import ResourceIdentifier
from pykotor.tools.encoding import decode_bytes_with_fallbacks
from pykotor.tools.path import CaseAwarePath, find_kotor_paths_from_default
from pykotor.tslpatcher.config import LogLevel
from pykotor.tslpatcher.patcher import ModInstaller
from pykotor.tslpatcher.reader import ConfigReader, NamespaceReader
from pykotor.tslpatcher.uninstall import ModUninstaller
from utility.string_util import striprtf

if TYPE_CHECKING:
    from argparse import Namespace
    from collections.abc import Callable
    from datetime import timedelta
    from threading import Event

    from pykotor.tslpatcher.logger import PatchLog, PatchLogger
    from pykotor.tslpatcher.namespaces import PatcherNamespace

VERSION_LABEL = f"v{CURRENT_VERSION}"


class ExitCode(IntEnum):
    SUCCESS = 0
    UNKNOWN_STARTUP_ERROR = 1
    NUMBER_OF_ARGS = 2
    NAMESPACES_INI_NOT_FOUND = 3
    NAMESPACE_INDEX_OUT_OF_RANGE = 4
    CHANGES_INI_NOT_FOUND = 5
    ABORT_INSTALL_UNSAFE = 6
    EXCEPTION_DURING_INSTALL = 7
    INSTALL_COMPLETED_WITH_ERRORS = 8
    CRASH = 9
    CLOSE_FOR_UPDATE_PROCESS = 10


class HoloPatcherError(Exception): ...


@dataclass
class ModInfo:
    """Information about a loaded mod."""

    mod_path: str
    namespaces: list[PatcherNamespace]
    config_reader: ConfigReader | None


@dataclass
class NamespaceInfo:
    """Information about a selected namespace."""

    config_reader: ConfigReader
    log_level: LogLevel
    game_number: int | None
    game_paths: list[str]
    info_content: str | None


@dataclass
class InstallResult:
    """Result of a mod installation."""

    install_time: timedelta
    num_errors: int
    num_warnings: int
    num_patches: int


def is_frozen() -> bool:
    """Check if running as a frozen executable."""
    return getattr(sys, "frozen", False) or getattr(sys, "_MEIPASS", False) or tempfile.gettempdir() in sys.executable


def is_running_from_temp() -> bool:
    """Check if running from a temporary directory."""
    app_path = Path(sys.executable)
    temp_dir = tempfile.gettempdir()
    return str(app_path).startswith(temp_dir)


def get_namespace_description(
    namespaces: list[PatcherNamespace],
    selected_namespace_name: str,
) -> str:
    """Get the description for a namespace by name."""
    namespace_option: PatcherNamespace | None = next(
        (x for x in namespaces if x.name == selected_namespace_name),
        None,
    )
    return namespace_option.description if namespace_option else ""


def load_mod(
    directory_path: os.PathLike | str,
) -> ModInfo:
    """Load a mod from a directory.

    Args:
    ----
        directory_path: Path to mod directory (or tslpatchdata subdirectory)

    Returns:
    -------
        ModInfo: Information about the loaded mod

    Raises:
    ------
        FileNotFoundError: If no valid mod found at path
    """
    tslpatchdata_path = CaseAwarePath(directory_path, "tslpatchdata")
    if not tslpatchdata_path.is_dir() and tslpatchdata_path.parent.name.lower() == "tslpatchdata":
        tslpatchdata_path = tslpatchdata_path.parent

    mod_path = str(tslpatchdata_path.parent)
    namespace_path: CaseAwarePath = tslpatchdata_path / "namespaces.ini"
    changes_path: CaseAwarePath = tslpatchdata_path / "changes.ini"

    namespaces: list[PatcherNamespace]
    config_reader: ConfigReader | None = None

    if namespace_path.is_file():
        namespaces = NamespaceReader.from_filepath(namespace_path)
    elif changes_path.is_file():
        config_reader = ConfigReader.from_filepath(changes_path, tslpatchdata_path=tslpatchdata_path)
        namespaces = [config_reader.config.as_namespace(changes_path)]
    else:
        raise FileNotFoundError(f"No namespaces.ini or changes.ini found in {tslpatchdata_path}")

    return ModInfo(mod_path, namespaces, config_reader)


def load_namespace_config(
    mod_path: str,
    namespaces: list[PatcherNamespace],
    selected_namespace_name: str,
    *,
    config_reader: ConfigReader | None = None,
) -> NamespaceInfo:
    """Load configuration for a specific namespace.

    Args:
    ----
        mod_path: Path to mod directory
        namespaces: List of available namespaces
        selected_namespace_name: Name of namespace to load
        config_reader: Optional pre-loaded ConfigReader

    Returns:
    -------
        NamespaceInfo: Configuration and metadata for the namespace

    Raises:
    ------
        ValueError: If namespace not found
    """
    namespace_option: PatcherNamespace | None = next(
        (x for x in namespaces if x.name == selected_namespace_name),
        None,
    )
    if namespace_option is None:
        raise ValueError(f"Namespace '{selected_namespace_name}' not found in namespaces list")
    changes_ini_path = CaseAwarePath(mod_path, "tslpatchdata", namespace_option.changes_filepath())
    tslpatchdata_path = CaseAwarePath(mod_path, "tslpatchdata")
    reader: ConfigReader = config_reader or ConfigReader.from_filepath(changes_ini_path, tslpatchdata_path=tslpatchdata_path)
    reader.load_settings()

    game_number: int | None = reader.config.game_number
    game: Game | None = Game(game_number) if game_number else None
    game_paths: list[str] = [
        str(path)
        for game_key in ([game] + ([Game.K1] if game is not None and game == Game.K2 else []))
        for path in (find_kotor_paths_from_default()[game_key] if game_key is not None else [])
    ] if game_number else []

    info_rtf_path = CaseAwarePath(mod_path, "tslpatchdata", namespace_option.rtf_filepath())
    info_rte_path = info_rtf_path.with_suffix(".rte")

    info_content: str | None = None
    if info_rte_path.is_file():
        data: bytes = BinaryReader.load_file(info_rte_path)
        info_content = decode_bytes_with_fallbacks(data, errors="replace")
    elif info_rtf_path.is_file():
        data = BinaryReader.load_file(info_rtf_path)
        rtf_text = decode_bytes_with_fallbacks(data, errors="replace")
        info_content = striprtf(rtf_text)

    return NamespaceInfo(reader, reader.config.log_level, game_number, game_paths, info_content)


def validate_game_directory(
    directory_path: os.PathLike | str,
) -> str:
    """Validate a KOTOR game directory.

    Args:
    ----
        directory_path: Path to validate

    Returns:
    -------
        str: Validated directory path

    Raises:
    ------
        ValueError: If directory is invalid
    """
    directory = CaseAwarePath(directory_path)
    if not directory.is_dir():
        raise ValueError(f"Invalid KOTOR directory: {directory_path}")
    return str(directory)


def check_directory_access(
    directory: Path,
    *,
    recurse: bool = False,
    should_filter: bool = False,
) -> bool:
    """Check if directory is accessible.

    Args:
    ----
        directory: Directory to check
        recurse: Check recursively if True
        should_filter: Filter by valid resource types if True

    Returns:
    -------
        bool: True if accessible
    """
    if should_filter:

        def filter_func(x: Path) -> bool:
            return not ResourceIdentifier.from_path(x).restype.is_invalid

        return directory.has_access(recurse=recurse, filter_results=filter_func)

    return directory.has_access(recurse=recurse)


def validate_install_paths(
    mod_path: str,
    game_path: str,
) -> bool:
    """Validate that mod and game paths are ready for installation.

    Args:
    ----
        mod_path: Path to mod directory
        game_path: Path to game directory

    Returns:
    -------
        bool: True if paths are valid
    """
    return (
        bool(mod_path)
        and CaseAwarePath(mod_path).is_dir()
        and bool(game_path)
        and CaseAwarePath(game_path).is_dir()
    )


def parse_args() -> Namespace:
    """Parse command line arguments.

    Returns:
    -------
        Namespace: Parsed command line arguments
    """
    from argparse import ArgumentParser

    from utility.error_handling import universal_simplify_exception

    parser = ArgumentParser(description="HoloPatcher CLI")

    parser.add_argument("--game-dir", type=str, help="Path to game directory")
    parser.add_argument("--tslpatchdata", type=str, help="Path to tslpatchdata")
    parser.add_argument("--namespace-option-index", type=int, help="Namespace option index")
    parser.add_argument("--console", action="store_true", help="Show the console when launching HoloPatcher.")
    parser.add_argument("--uninstall", action="store_true", help="Uninstalls the selected mod.")
    parser.add_argument("--install", action="store_true", help="Starts an install immediately on launch.")
    parser.add_argument("--validate", action="store_true", help="Starts validation of the selected mod.")

    kwargs, positional = parser.parse_known_args()

    required_number_of_positional_args = 2
    max_positional_args = 3  # sourcery skip: move-assign

    number_of_positional_args = len(positional)
    if number_of_positional_args == required_number_of_positional_args:
        kwargs.game_dir = positional[0]
        kwargs.tslpatchdata = positional[1]
    if number_of_positional_args == max_positional_args:
        kwargs.namespace_option_index = positional[2]
    if kwargs.namespace_option_index:
        try:
            kwargs.namespace_option_index = int(kwargs.namespace_option_index)
        except ValueError as e:
            print(universal_simplify_exception(e), file=sys.stderr)  # noqa: T201
            print(f"Invalid namespace_option_index. It should be an integer, got {kwargs.namespace_option_index}", file=sys.stderr)  # noqa: T201
            sys.exit(ExitCode.NAMESPACE_INDEX_OUT_OF_RANGE)

    return kwargs


def calculate_total_patches(installer: ModInstaller) -> int:
    """Calculate total number of patches for progress calculation.

    Args:
    ----
        installer: ModInstaller instance

    Returns:
    -------
        int: Total number of patches
    """
    return len([
        *installer.config().install_list,  # Note: TSLPatcher executes [InstallList] after [TLKList]
        *installer.get_tlk_patches(installer.config()),
        *installer.config().patches_2da,
        *installer.config().patches_gff,
        *installer.config().patches_nss,
        *installer.config().patches_ncs,  # Note: TSLPatcher executes [CompileList] after [HACKList]
        *installer.config().patches_ssf,
    ])


def get_confirm_message(installer: ModInstaller) -> str | None:
    """Get confirmation message if mod requires it.

    Args:
    ----
        installer: ModInstaller instance

    Returns:
    -------
        str | None: Confirmation message if required, None otherwise
    """
    msg = installer.config().confirm_message.strip()
    return msg if msg and msg != "N/A" else None


def install_mod(
    mod_path: str,
    game_path: str,
    namespaces: list[PatcherNamespace],
    selected_namespace_name: str,
    logger: PatchLogger,
    should_cancel: Event,
    *,
    progress_callback: Callable[[int], None] | None = None,
) -> InstallResult:
    """Install a mod.

    Args:
    ----
        mod_path: Path to mod directory
        game_path: Path to game directory
        namespaces: List of available namespaces
        selected_namespace_name: Name of namespace to install
        logger: Logger instance
        should_cancel: Event to signal cancellation
        progress_callback: Optional callback for progress updates

    Returns:
    -------
        InstallResult: Installation results

    Raises:
    ------
        Exception: If installation fails
    """
    namespace_option: PatcherNamespace | None = next(
        (x for x in namespaces if x.name == selected_namespace_name),
        None,
    )
    if namespace_option is None:
        raise ValueError(f"Namespace '{selected_namespace_name}' not found in namespaces list")
    tslpatchdata_path = CaseAwarePath(mod_path, "tslpatchdata")
    ini_file_path = tslpatchdata_path.joinpath(namespace_option.changes_filepath())
    namespace_mod_path: CaseAwarePath = ini_file_path.parent

    installer = ModInstaller(namespace_mod_path, game_path, ini_file_path, logger)
    installer.tslpatchdata_path = tslpatchdata_path

    install_start_time: datetime = datetime.now(timezone.utc).astimezone()
    installer.install(should_cancel, progress_callback)
    total_install_time: timedelta = datetime.now(timezone.utc).astimezone() - install_start_time

    num_errors: int = len(logger.errors)
    num_warnings: int = len(logger.warnings)
    num_patches: int = installer.config().patch_count()

    time_str = format_install_time(total_install_time)
    logger.add_note(
        f"The installation is complete with {num_errors} errors and {num_warnings} warnings.{os.linesep}"
        f"Total install time: {time_str}{os.linesep}"
        f"Total patches: {num_patches}",
    )

    return InstallResult(total_install_time, num_errors, num_warnings, num_patches)


def validate_config(
    mod_path: str,
    namespaces: list[PatcherNamespace],
    selected_namespace_name: str,
    logger: PatchLogger,
) -> None:
    """Validate a mod's configuration.

    Args:
    ----
        mod_path: Path to mod directory
        namespaces: List of available namespaces
        selected_namespace_name: Name of namespace to validate
        logger: Logger instance

    Raises:
    ------
        ValueError: If namespace not found
        Exception: If validation fails
    """
    namespace_option: PatcherNamespace | None = next(
        (x for x in namespaces if x.name == selected_namespace_name),
        None,
    )
    if namespace_option is None:
        raise ValueError(f"Namespace '{selected_namespace_name}' not found in namespaces list")
    ini_file_path = CaseAwarePath(mod_path, "tslpatchdata", namespace_option.changes_filepath())
    tslpatchdata_path = CaseAwarePath(mod_path, "tslpatchdata")

    reader = ConfigReader.from_filepath(ini_file_path, logger, tslpatchdata_path=tslpatchdata_path)
    reader.load(reader.config)


def uninstall_mod(
    mod_path: str,
    game_path: str,
    logger: PatchLogger,
) -> bool:
    """Uninstall a mod using its backup.

    Args:
    ----
        mod_path: Path to mod directory
        game_path: Path to game directory
        logger: Logger instance

    Returns:
    -------
        bool: True if uninstall completed fully

    Raises:
    ------
        FileNotFoundError: If backup folder not found
    """
    backup_parent_folder = Path(mod_path, "backup")
    if not backup_parent_folder.is_dir():
        raise FileNotFoundError(f"Backup folder not found: {backup_parent_folder}")

    uninstaller = ModUninstaller(backup_parent_folder, Path(game_path), logger)
    return uninstaller.uninstall_selected_mod()


def lowercase_directory(
    directory: str,
    logger: PatchLogger,
) -> bool:
    """Convert all files and folders in a directory to lowercase.

    Args:
    ----
        directory: Directory to process
        logger: Logger instance

    Returns:
    -------
        bool: True if any changes were made
    """
    made_change: bool = False
    for root, dirs, files in os.walk(str(directory), topdown=False):
        for file_name in files:
            file_path: Path = Path(root, file_name)
            new_file_path: Path = Path(root, file_name.lower())
            if str(file_path) != str(new_file_path):
                logger.add_note(f"Renaming {file_path} to '{new_file_path.name}'")
                file_path.rename(new_file_path)
                made_change = True

        for folder_name in dirs:
            dir_path: Path = Path(root, folder_name)
            new_dir_path: Path = Path(root, folder_name.lower())
            if str(dir_path) != str(new_dir_path):
                logger.add_note(f"Renaming {dir_path} to '{new_dir_path.name}'")
                dir_path.rename(new_dir_path)
                made_change = True

    Path(directory).rename(Path.str_norm(str(directory).lower()))
    return made_change


def gain_directory_access(
    directory: str,
    logger: PatchLogger,
) -> tuple[bool, int, int]:
    """Attempt to gain access to a directory.

    Args:
    ----
        directory: Directory to fix permissions for
        logger: Logger instance

    Returns:
    -------
        tuple[bool, int, int]: (success, num_files, num_folders)

    Raises:
    ------
        PermissionError: If access cannot be gained
    """
    path: Path = Path(directory)
    access: bool = path.gain_access(recurse=True, log_func=logger.add_verbose)
    if not access:
        raise PermissionError(f"Permission denied to {directory}")

    num_files = 0
    num_folders = 0
    if path.is_dir():
        for entry in path.rglob("*"):
            if entry.is_file():
                num_files += 1
            elif entry.is_dir():
                num_folders += 1

    return (True, num_files, num_folders)


def get_log_file_path(mod_path: str) -> Path:
    """Get the log file path for a mod.

    Args:
    ----
        mod_path: Path to mod directory

    Returns:
    -------
        Path: Path to log file
    """
    return Path(mod_path) / "installlog.txt"


def write_log_entry(
    log: PatchLog,
    mod_path: str,
    log_level: LogLevel,
) -> None:
    """Write a log entry to file with level filtering.

    Args:
    ----
        log: PatchLog object to write
        mod_path: Path to mod directory
        log_level: Current log level setting
    """
    from loggerplus import RobustLogger

    from pykotor.tslpatcher.logger import LogType

    def log_type_to_level() -> LogType:
        log_map: dict[LogLevel, LogType] = {
            LogLevel.ERRORS: LogType.WARNING,
            LogLevel.GENERAL: LogType.WARNING,
            LogLevel.FULL: LogType.VERBOSE,
            LogLevel.WARNINGS: LogType.NOTE,
            LogLevel.NOTHING: LogType.WARNING
        }
        return log_map[log_level]

    log_file_path = get_log_file_path(mod_path)
    try:
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        with log_file_path.open("a", encoding="utf-8") as log_file:
            log_file.write(f"{log.formatted_message}\n")
        if log.log_type.value < log_type_to_level().value:
            return
    except OSError as e:
        RobustLogger().error(f"Failed to write the log file at '{log_file_path}': {e.__class__.__name__}: {e}")


def format_install_time(install_time: timedelta) -> str:
    """Format an installation time as a human-readable string.

    Args:
    ----
        install_time: Time duration

    Returns:
    -------
        str: Formatted time string
    """
    days, remainder = divmod(install_time.total_seconds(), 24 * 60 * 60)
    hours, remainder = divmod(remainder, 60 * 60)
    minutes, seconds = divmod(remainder, 60)

    return (
        f"{f'{int(days)} days, ' if days else ''}"
        f"{f'{int(hours)} hours, ' if hours else ''}"
        f"{f'{int(minutes)} minutes, ' if minutes or not (days or hours) else ''}"
        f"{int(seconds)} seconds"
    )
