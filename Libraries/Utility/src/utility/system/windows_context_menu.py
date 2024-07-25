from __future__ import annotations

import sys

from contextlib import nullcontext
from pathlib import WindowsPath
from typing import TYPE_CHECKING, Any, Sequence

import win32com.client
import win32con
import win32gui

from utility.system.win32.hwnd import HInvisibleWindow

if TYPE_CHECKING:
    import os

    from win32com.client import DispatchBaseClass
    from win32com.client.dynamic import CDispatch


def safe_isfile(path: WindowsPath) -> bool | None:
    try:
        result: bool = path.is_file()
    except (OSError, ValueError):
        return None
    return result


def safe_isdir(path: WindowsPath) -> bool | None:
    try:
        result: bool = path.is_dir()
    except (OSError, ValueError):
        return None
    return result


def show_context_menu(context_menu: CDispatch, hwnd: int | None):
    hmenu: int = win32gui.CreatePopupMenu()
    for i, verb in enumerate(context_menu):  # pyright: ignore[reportArgumentType]
        if verb.Name:
            win32gui.AppendMenu(hmenu, win32con.MF_STRING, i + 1, verb.Name)  # pyright: ignore[reportCallIssue]

    pt: tuple[int, int] = win32gui.GetCursorPos()

    context = HInvisibleWindow() if hwnd is None else nullcontext(hwnd)
    with context as hwnd:
        cmd: Any = win32gui.TrackPopupMenu(
            hmenu, win32con.TPM_LEFTALIGN | win32con.TPM_RETURNCMD,
            pt[0], pt[1], 0,
            hwnd, None  # pyright: ignore[reportArgumentType]
        )
    if isinstance(cmd, int):
        verb: DispatchBaseClass = context_menu.Item(cmd - 1)
        if verb:
            verb.DoIt()


# Function to display context menu
def windows_context_menu_file(
    file_path: os.PathLike | str,
    hwnd: int | None = None,
):
    """Opens the default windows context menu for a filepath at the position of the cursor."""
    parsed_filepath: WindowsPath = WindowsPath(file_path)

    shell = win32com.client.Dispatch("Shell.Application")
    folder: CDispatch = shell.NameSpace(str(parsed_filepath.parent))
    item: CDispatch = folder.ParseName(parsed_filepath.name)
    context_menu: CDispatch = item.Verbs()

    show_context_menu(context_menu, hwnd)


def windows_context_menu_folder(
    folder_path: os.PathLike | str,
    hwnd: int | None = None,
):
    """Opens the default windows context menu for a folderpath at the position of the cursor."""
    shell = win32com.client.Dispatch("Shell.Application")
    folder: CDispatch = shell.NameSpace(str(WindowsPath(folder_path)))
    item: CDispatch = folder.Self
    context_menu: CDispatch = item.Verbs()

    show_context_menu(context_menu, hwnd)


def windows_context_menu(
    path: os.PathLike | str,
    hwnd: int | None = None,
):
    """Opens the default windows context menu for a folder/file path at the position of the cursor."""
    parsed_path = WindowsPath(path)
    if safe_isfile(parsed_path):
        windows_context_menu_file(parsed_path, hwnd)
    elif safe_isdir(parsed_path):
        windows_context_menu_folder(parsed_path, hwnd)
    else:
        msg = f"Path is neither file nor folder: '{path}'"
        raise ValueError(msg)


def windows_context_menu_multiple(
    paths: Sequence[os.PathLike | str],
    hwnd: int | None = None,
):
    """Opens the default windows context menu for multiple files/folder paths at the position of the cursor."""
    shell = win32com.client.Dispatch("Shell.Application")
    folders_items: list[CDispatch] = [
        shell.NameSpace(str(path.parent if safe_isfile(path) else path)).ParseName(path.name)
        for path in (WindowsPath(path) for path in paths)
    ]
    context_menu: CDispatch = folders_items[0].Verbs()

    show_context_menu(context_menu, hwnd)


# Example usage
if __name__ == "__main__":
    import sys

    from toolset.__main__ import onAppCrash

    sys.excepthook = onAppCrash
    filepath = r"C:\Users\Wizard\test_folder\City.sol"
    windows_context_menu(filepath)

    multiple_files = [
        r"C:\Users\Wizard\test_folder\RestoreBackup.ps1",
        r"C:\Users\Wizard\test_folder\City.sol",
    ]
    windows_context_menu_multiple(multiple_files)

    folderpath = r"C:\Users\Wizard\test_folder"
    windows_context_menu_folder(folderpath)
