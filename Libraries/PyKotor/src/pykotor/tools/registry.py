from __future__ import annotations

import contextlib
import os

from pykotor.common.misc import Game
from utility.error_handling import format_exception_with_variables
from utility.misc import ProcessorArchitecture

KOTOR_REG_PATHS = {
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
                software_path = f"{sid}\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{software_name}"
                with contextlib.suppress(FileNotFoundError), winreg.OpenKey(hkey_users, software_path) as software_key:
                    # If this point is reached, the software is installed under this SID
                    return winreg.QueryValue(software_key, "InstallLocation")
                i += 1
            except OSError:  # noqa: PERF203
                break

    return None


def resolve_reg_key_to_path(reg_key: str, keystr: str):
    r"""Resolves a registry key to a file system path.

    Args:
    ----
        reg_key: Registry key to resolve in format "HKEY_CURRENT_USER\\Software\\Company\\Product".
        keystr: Name of value containing path under the key.

    Returns:
    -------
        resolved_path: File system path resolved from registry key/value or None.

    Processing Logic:
    ----------------
        - Opens the registry key using the root and subkey
        - Queries the key for the value specified by keystr
        - Returns the path if found, otherwise returns None.
    """
    import winreg

    try:
        root, subkey = reg_key.split("\\", 1)
        root_key = getattr(winreg, root)
        with winreg.OpenKey(root_key, subkey) as key:
            resolved_path, _ = winreg.QueryValueEx(key, keystr)
            return resolved_path
    except (FileNotFoundError, PermissionError):
        return None


def check_reg_keys_existence_and_validity() -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """Check registry keys for their existence and validity against default paths."""
    import winreg

    from pykotor.tools.path import find_kotor_paths_from_default
    from utility.system.path import WindowsPath

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
                if not reg_path_obj.exists() or all(
                    reg_path_obj != WindowsPath(default_path)
                    for default_path in game_defaults
                ):
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


def get_winreg_path(game: Game):
    """Returns the specified path value in the windows registry for the given game.

    Attributes:
    ----------
        game: The game to lookup in the registry

    Raises:
    ------
        ValueError: Not on a Windows OS.
        WinError: Most likely do not have sufficient permissions.
    """
    possible_kotor_reg_paths = winreg_key(game)

    try:
        import winreg

        for key_path, subkey in possible_kotor_reg_paths:
            key = winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ)
            return winreg.QueryValueEx(key, subkey)
    except (FileNotFoundError, PermissionError):
        return ""


def set_winreg_path(game: Game, path: str):
    """Sets the kotor install folder path value in the windows registry for the given game.

    Attributes:
    ----------
        game: The game to set in the registry
        path: New path value for the game.

    Raises:
    ------
        ValueError: Not on a Windows OS.
        WinError: Most likely do not have sufficient permissions.
    """
    possible_kotor_reg_paths = winreg_key(game)

    import winreg

    for key_path, subkey in possible_kotor_reg_paths:
        key = winreg.CreateKeyEx(
            winreg.HKEY_LOCAL_MACHINE,
            key_path,
            0,
            winreg.KEY_SET_VALUE,
        )
        winreg.SetValueEx(key, subkey, 1, winreg.REG_SZ, path)


def create_registry_path(hive, path):  # sourcery skip: raise-from-previous-error
    """Recursively creates the registry path if it doesn't exist."""
    try:
        import winreg
        current_path = ""
        for part in path.split("\\"):
            current_path = f"{current_path}\\{part}" if current_path else part
            try:
                winreg.CreateKey(hive, current_path)
            except PermissionError:
                raise PermissionError("Permission denied. Administrator privileges required.")  # noqa: B904, TRY003, EM101
            except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
                # sourcery skip: raise-specific-error
                raise Exception(f"Failed to create registry key: {current_path}. Error: {e}")  # noqa: TRY002, TRY003, EM102, B904
    except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
        print(format_exception_with_variables(e))


def set_registry_key_value(full_key_path, value_name, value_data):
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
    try:
        import winreg
        # Parse the hive from the full key path
        hive_name, sub_key = full_key_path.split("\\", 1)
        hive = {
            "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
            "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
            "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
            "HKEY_USERS": winreg.HKEY_USERS,
            "HKEY_CURRENT_CONFIG": winreg.HKEY_CURRENT_CONFIG
        }.get(hive_name)
        if hive is None:
            print(f"Error: Invalid registry hive '{hive_name}'.")
            return

        # Create the registry path
        try:
            create_registry_path(hive, sub_key)
        except PermissionError:
            raise
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            print(format_exception_with_variables(e))
            return
        # Open or create the key at the specified path
        with winreg.CreateKeyEx(hive, sub_key, 0, winreg.KEY_WRITE | winreg.KEY_WOW64_32KEY) as key:
            # Set the value
            winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, value_data)
            print(f"Successfully set {value_name} to {value_data} at {hive}\\{sub_key}")
    except PermissionError:
        raise
    except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
        print(f"An unexpected error occurred: {e}")
        print(format_exception_with_variables(e))


def remove_winreg_path(game: Game):
    possible_kotor_reg_paths = winreg_key(game)

    try:
        import winreg
        for key_path, subkey in possible_kotor_reg_paths:
            key = winreg.OpenKeyEx(
                winreg.HKEY_LOCAL_MACHINE,
                key_path,
                0,
                winreg.KEY_SET_VALUE,
            )
            winreg.DeleteValue(key, subkey)
    except FileNotFoundError:
        ...
