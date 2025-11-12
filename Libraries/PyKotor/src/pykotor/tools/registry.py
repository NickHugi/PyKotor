from __future__ import annotations

import os

from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loggerplus import RobustLogger

from pykotor.common.misc import Game
from utility.misc import ProcessorArchitecture

if TYPE_CHECKING:
    import types

    from winreg import HKEYType

    from typing_extensions import Literal, Self  # pyright: ignore[reportMissingModuleSource]


"""Windows registry paths and game installation detection.

References:
----------
    vendor/KOTOR_Registry_Install_Path_Editor (Registry path detection tool)
    vendor/HoloPatcher.NET/src/HoloPatcher/Util/RegistryHelper.cs (C# registry helper)
    vendor/Kotor-Randomizer (Game path detection logic)
    Note: Registry paths vary between Steam, GOG, and disc releases on different architectures
"""

KOTOR_REG_PATHS: dict[Game, dict[ProcessorArchitecture, list[tuple[str, str]]]] = {
    Game.K1: {
        ProcessorArchitecture.BIT_32: [
            (r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 32370", "InstallLocation"),
            (r"HKEY_LOCAL_MACHINE\SOFTWARE\GOG.com\Games\1207666283", "PATH"),
            (r"HKEY_LOCAL_MACHINE\SOFTWARE\BioWare\SW\KOTOR", "InternalPath"),
            (r"HKEY_LOCAL_MACHINE\SOFTWARE\BioWare\SW\KOTOR", "Path"),
            #            (r"HKEY_USERS\S-1-5-21-3288518552-3737095363-3281442775-1001\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\AmazonGames/Star Wars - Knights of the Old", "InstallLocation"),
        ],
        ProcessorArchitecture.BIT_64: [
            (r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 32370", "InstallLocation"),
            (r"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\GOG.com\Games\1207666283", "PATH"),
            (r"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\BioWare\SW\KOTOR", "InternalPath"),
            (r"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\BioWare\SW\KOTOR", "Path"),
        ],
    },
    Game.K2: {
        ProcessorArchitecture.BIT_32: [
            (r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 208580", "InstallLocation"),
            (r"HKEY_LOCAL_MACHINE\SOFTWARE\GOG.com\Games\1421404581", "PATH"),
            (r"HKEY_LOCAL_MACHINE\SOFTWARE\LucasArts\KotOR2", "InternalPath"),
            (r"HKEY_LOCAL_MACHINE\SOFTWARE\LucasArts\KotOR2", "Path"),
        ],
        ProcessorArchitecture.BIT_64: [
            (r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 208580", "InstallLocation"),
            (r"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\GOG.com\Games\1421404581", "PATH"),
            (r"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\LucasArts\KotOR2", "InternalPath"),
            (r"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\LucasArts\KotOR2", "Path"),
        ],
    },
}


# amazon's k1 reg key can be found using the below code. Doesn't store it in HKLM for some reason.
def find_software_key(software_name: str) -> str | None:
    import winreg

    with winreg.ConnectRegistry(None, winreg.HKEY_USERS) as hkey_users:
        i = 0
        while True:
            try:
                # Enumerate through the SIDs
                sid: str = winreg.EnumKey(hkey_users, i)
                software_path: str = f"{sid}\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{software_name}"
                with suppress(FileNotFoundError), winreg.OpenKey(hkey_users, software_path) as software_key:
                    # If this point is reached, the software is installed under this SID
                    return winreg.QueryValue(software_key, "InstallLocation")
                i += 1
            except OSError:  # noqa: PERF203
                break  # No more left to iterate through.

    return None


def resolve_reg_key_to_path(
    registry: str | HKEYType,
    subkey: str,
    value_name: str | None = None,
) -> str | None:
    r"""Resolve a registry key to a file system path."""
    import winreg

    try:
        if isinstance(registry, str):
            root_name, key_path = registry.split("\\", 1)
            root_key = getattr(winreg, root_name)
            value_to_lookup = subkey
        else:
            root_key = registry
            if value_name is None:
                msg = "value_name must be provided when a registry handle is supplied."
                raise ValueError(msg)
            key_path = subkey
            value_to_lookup = value_name

        with winreg.OpenKey(root_key, key_path) as key:
            resolved_path, _ = winreg.QueryValueEx(key, value_to_lookup)
            return resolved_path
    except (AttributeError, FileNotFoundError, PermissionError):
        return None


def check_reg_keys_existence_and_validity() -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """Check registry keys for their existence and validity against default paths."""
    import winreg

    from pathlib import WindowsPath

    from pykotor.tools.path import find_kotor_paths_from_default

    non_existent_keys = []
    invalid_path_keys = []

    default_paths = find_kotor_paths_from_default()

    # Determine the system's architecture
    arch = ProcessorArchitecture.from_os()
    for game, arch_paths in KOTOR_REG_PATHS.items():
        game_defaults = default_paths[game]

        for path, name in arch_paths[arch]:
            reg_path = resolve_reg_key_to_path(winreg.HKEY_LOCAL_MACHINE, path, name)
            if reg_path is None:
                non_existent_keys.append((path, name))
            else:
                # Convert registry path to a proper WindowsPath and check existence and if it's a default path
                reg_path_obj = WindowsPath(reg_path)
                if not reg_path_obj.exists() or all(reg_path_obj != WindowsPath(default_path) for default_path in game_defaults):
                    invalid_path_keys.append((path, name))

    return non_existent_keys, invalid_path_keys


def winreg_key(game: Game) -> list[tuple[str, str]]:
    """Returns a list of registry keys that are utilized by KOTOR.

    Attributes:
    ----------
        game: Game IntEnum - The game to lookup
        access: Access permissions for the key (see winreg module).

    Raises:
    ------
        ValueError: Not on a Windows OS.
        WinError: Most likely do not have sufficient permissions.

    Returns:
    -------
        Key object or None if no key exists.
    """
    if os.name != "nt":
        msg = "Cannot get or set registry keys on a non-Windows OS."
        raise ValueError(msg)

    return KOTOR_REG_PATHS[game][ProcessorArchitecture.from_os()]


def get_winreg_path(game: Game) -> tuple[Any, int] | None | Literal[""]:
    """(untested) Returns the specified path value in the windows registry for the given game.

    Attributes:
    ----------
        game: The game to lookup in the registry

    Raises:
    ------
        ValueError: Not on a Windows OS.
        WinError: Most likely do not have sufficient permissions.
    """
    possible_kotor_reg_paths: list[tuple[str, str]] = winreg_key(game)

    try:
        import winreg

        for key_path, subkey in possible_kotor_reg_paths:
            key: HKEYType = winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ)
            return winreg.QueryValueEx(key, subkey)
    except (FileNotFoundError, PermissionError):
        return ""


def set_winreg_path(
    game: Game,
    path: str,
) -> None:
    """(untested) Sets the kotor install folder path value in the windows registry for the given game.

    Attributes:
    ----------
        game: The game to set in the registry
        path: New path value for the game.

    Raises:
    ------
        ValueError: Not on a Windows OS.
        WinError: Most likely do not have sufficient permissions.
    """
    possible_kotor_reg_paths: list[tuple[str, str]] = winreg_key(game)

    import winreg

    for key_path, subkey in possible_kotor_reg_paths:
        key: HKEYType = winreg.CreateKeyEx(
            winreg.HKEY_LOCAL_MACHINE,
            key_path,
            0,
            winreg.KEY_SET_VALUE,
        )
        winreg.SetValueEx(key, subkey, 1, winreg.REG_SZ, path)


def create_registry_path(
    hive: HKEYType | int,
    path: str,
) -> None:  # sourcery skip: raise-from-previous-error
    """Recursively creates the registry path if it doesn't exist."""
    log = RobustLogger()
    try:
        import winreg

        current_path: str = ""
        for part in path.split("\\"):
            current_path = f"{current_path}\\{part}" if current_path else part
            try:
                winreg.CreateKey(hive, current_path)
            except PermissionError as e:
                raise PermissionError("Permission denied. Administrator privileges required.") from e  # noqa: B904, TRY003, EM101
            except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
                # sourcery skip: raise-specific-error
                raise Exception(f"Failed to create registry key: {current_path}") from e  # noqa: TRY002, TRY003, EM102, B904
    except Exception:  # pylint: disable=W0718  # noqa: BLE001
        log.exception("An unexpected error occurred while creating a registry path.")


def get_retail_key(game: Game) -> str:
    if ProcessorArchitecture.from_os() == ProcessorArchitecture.BIT_64:
        return r"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\LucasArts\KotOR2" if game.is_k2() else r"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\BioWare\SW\KOTOR"
    return r"HKEY_LOCAL_MACHINE\SOFTWARE\LucasArts\KotOR2" if game.is_k2() else r"HKEY_LOCAL_MACHINE\SOFTWARE\BioWare\SW\KOTOR"


class SpoofKotorRegistry:
    """A context manager used to safely spoof the KOTOR 1/2 disk retail registry path temporarily."""

    def __init__(
        self,
        installation_path: os.PathLike | str,
        game: Game | None = None,
    ):
        from pykotor.extract.installation import Installation

        # Key name at the path containing the value.
        self.key: str = "Path"
        self.spoofed_path: Path = Path(installation_path).resolve()

        if game is not None:
            determined_game = game
        else:
            determined_game = Installation.determine_game(installation_path)
            if determined_game is None:
                raise ValueError(f"Could not auto-determine the game k1 or k2 from '{installation_path}'. Try sending 'game' enum to prevent auto-detections like this.")

        # Path to the key.
        self.registry_path: str = get_retail_key(determined_game)

        # The original contents of the key. None if not existing.
        self.original_value: str | None = resolve_reg_key_to_path(self.registry_path, self.key)

    def __enter__(self) -> Self:
        if self.spoofed_path != self.original_value:
            set_registry_key_value(self.registry_path, self.key, str(self.spoofed_path))
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ):
        # Revert the registry key to its original value if it was altered
        if self.original_value is not None and self.spoofed_path != self.original_value:
            set_registry_key_value(self.registry_path, self.key, self.original_value)
        # TODO(th3w1zard1): Determine what to do if the regpath never existed, as deleting it isn't easy. Set it to ""?


def set_registry_key_value(
    full_key_path: str,
    value_name: str,
    value_data: str,
) -> None:
    """Sets a registry key value, creating the key (and its parents, if necessary).

    Args:
    ----
        - full_key_path: The full registry key path, including the hive.
        - value_name: The name of the value to set.
        - value_data: The data to set for the value.

    Raises:
    ------
        - PermissionError: PyKotor doesn't have permission to change the registry (usually fixed by running as admin).
    """
    log = RobustLogger()
    try:
        import winreg

        # Parse the hive from the full key path
        hive_name, sub_key = full_key_path.split("\\", 1)
        hive: int | None = {
            "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
            "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
            "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
            "HKEY_USERS": winreg.HKEY_USERS,
            "HKEY_CURRENT_CONFIG": winreg.HKEY_CURRENT_CONFIG,
        }.get(hive_name)
        if hive is None:
            log.error("Invalid registry hive '%s'.", hive_name)
            return

        # Create the registry path
        try:
            create_registry_path(hive, sub_key)
        except PermissionError:
            raise
        except Exception:  # pylint: disable=W0718  # noqa: BLE001
            log.exception("set_registry_key_value raised an error other than the expected PermissionError")
            return
        # Open or create the key at the specified path
        with winreg.CreateKeyEx(hive, sub_key, 0, winreg.KEY_WRITE | winreg.KEY_WOW64_32KEY) as key:
            # Set the value
            winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, value_data)
            log.debug("Successfully set %s to %s at %s\\%s", value_name, value_data, hive, sub_key)
    except PermissionError:
        raise
    except Exception:  # pylint: disable=W0718  # noqa: BLE001
        log.exception("An unexpected error occured while setting the registry.")


def remove_winreg_path(game: Game):
    """(untested)."""
    possible_kotor_reg_paths: list[tuple[str, str]] = winreg_key(game)

    try:
        import winreg

        for key_path, subkey in possible_kotor_reg_paths:
            key: HKEYType = winreg.OpenKeyEx(
                winreg.HKEY_LOCAL_MACHINE,
                key_path,
                0,
                winreg.KEY_SET_VALUE,
            )
            winreg.DeleteValue(key, subkey)
    except FileNotFoundError:
        ...
