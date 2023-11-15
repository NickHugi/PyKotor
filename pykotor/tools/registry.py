from __future__ import annotations

import os

from pykotor.common.misc import Game
from pykotor.helpers.misc import ProcessorArchitecture

KOTOR_REG_PATHS = {
    Game.K1: {
        ProcessorArchitecture.BIT_32: [
            (r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 32370", "InstallLocation"),
            (r"HKEY_LOCAL_MACHINE\SOFTWARE\GOG.com\Games\1207666283", "PATH"),
            (r"HKEY_LOCAL_MACHINE\SOFTWARE\BioWare\SW\KOTOR", "InternalPath"),
        ],
        ProcessorArchitecture.BIT_64: [
            (r"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\GOG.com\Games\1207666283", "PATH"),
            (r"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\BioWare\SW\KOTOR", "InternalPath"),
        ],
    },
    Game.K2: {
        ProcessorArchitecture.BIT_32: [
            (r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 208580", "InstallLocation"),
            (r"HKEY_LOCAL_MACHINE\SOFTWARE\GOG.com\Games\1421404581", "PATH"),
            (r"HKEY_LOCAL_MACHINE\SOFTWARE\LucasArts\KotOR2", "Path"),
        ],
        ProcessorArchitecture.BIT_64: [
            (r"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\GOG.com\Games\1421404581", "PATH"),
            (r"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\LucasArts\KotOR2", "InternalPath"),
        ],
    },
}


def winreg_key(game: Game) -> list[tuple[str, str]]:
    """Returns a list of registry keys that are utilized by KOTOR.

    Attributes
    ----------
        game: Game IntEnum - The game to lookup
        access: Access permissions for the key (see winreg module).

    Raises
    ------
        ValueError: Not on a Windows OS.
        WinError: Most likely do not have sufficient permissions.

    Returns
    -------
        Key object or None if no key exists.
    """
    if os.name != "nt":
        msg = "Cannot get or set registry keys on a non-Windows OS."
        raise ValueError(msg)

    return KOTOR_REG_PATHS[game][ProcessorArchitecture.from_os()]


def get_winreg_path(game: Game):
    """Returns the specified path value in the windows registry for the given game.

    Attributes
    ----------
        game: The game to lookup in the registry

    Raises
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

    Attributes
    ----------
        game: The game to set in the registry
        path: New path value for the game.

    Raises
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
