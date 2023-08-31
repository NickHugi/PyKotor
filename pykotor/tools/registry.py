import platform

from pykotor.common.misc import Game


def winreg_key(game: Game) -> str:
    """Returns what the key path is in the Windows registry for the given game.

    Attributes
    ----------
        game: Path for which game.
        access: Access permissions for the key (see winreg module).

    Raises
    ------
        ValueError: Not on a Windows OS.
        WinError: Most likely do not have sufficient permissions.

    Returns
    -------
        Key object or None if no key exists.
    """
    if platform.system() != "Windows":
        msg = "Cannot set registry keys on a non-Windows OS."
        raise ValueError(msg)

    is_64_bits = platform.machine().endswith("64")

    regpaths = {
        Game.K1: {
            False: r"SOFTWARE\BioWare\SW\KOTOR",
            True: r"SOFTWARE\WOW6432Node\Bioware\SW\KotOR",
        },
        Game.K2: {
            False: r"SOFTWARE\LucasArts\KotOR2",
            True: r"SOFTWARE\WOW6432Node\LucasArts\KotOR2",
        },
    }

    return regpaths[game][is_64_bits]

    #


def get_winreg_path(game: Game):
    """Returns the specified path value in the windows registry for the given game.

    Attributes
    ----------
        game: Path for which game.

    Raises
    ------
        ValueError: Not on a Windows OS.
        WinError: Most likely do not have sufficient permissions.
    """
    key_path = winreg_key(game)

    try:
        import winreg

        key = winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ)
        return winreg.QueryValueEx(key, r"path")
    except FileNotFoundError:
        return ""


def set_winreg_path(game: Game, path: str):
    """Sets the specified path value in the windows registry for the given game.

    Attributes
    ----------
        game: Path for which game.
        path: New path value for the game.

    Raises
    ------
        ValueError: Not on a Windows OS.
        WinError: Most likely do not have sufficient permissions.
    """
    key_path = winreg_key(game)

    import winreg

    key = winreg.CreateKeyEx(
        winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE
    )
    winreg.SetValueEx(key, r"path", 1, winreg.REG_SZ, path)


def remove_winreg_path(game: Game):
    key_path = winreg_key(game)

    try:
        import winreg

        key = winreg.OpenKeyEx(
            winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE
        )
        return winreg.DeleteValue(key, r"path")
    except FileNotFoundError:
        ...
