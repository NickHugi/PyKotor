from __future__ import annotations

import ctypes
import os
import sys

from ctypes import windll
from pathlib import WindowsPath
from typing import TYPE_CHECKING, Sequence

import win32com.client
import win32con
import win32gui

if TYPE_CHECKING:
    from _win32typing import PyResourceId, PyWNDCLASS
    from win32com.client import DispatchBaseClass
    from win32com.client.dynamic import CDispatch

try:
    from ctypes.wintypes import HWND, LPARAM
except Exception:  # noqa: BLE001  # pyinstaller frozen-related issue observed.
    # just grab from ctypes.wintypes src I suppose
    # WPARAM is defined as UINT_PTR (unsigned type)
    # LPARAM is defined as LONG_PTR (signed type)
    if ctypes.sizeof(ctypes.c_long) == ctypes.sizeof(ctypes.c_void_p):
        WPARAM = ctypes.c_ulong
        LPARAM = ctypes.c_long
    elif ctypes.sizeof(ctypes.c_longlong) == ctypes.sizeof(ctypes.c_void_p):
        WPARAM = ctypes.c_ulonglong
        LPARAM = ctypes.c_longlong
    HWND = ctypes.c_void_p

# Load libraries
user32: ctypes.WinDLL = windll.user32
kernel32: ctypes.WinDLL = windll.kernel32

# Define window class and procedure
WNDPROC: ctypes._FuncPointer = ctypes.WINFUNCTYPE(
    ctypes.c_long,
    HWND,
    ctypes.c_uint,
    ctypes.c_uint,
    LPARAM,
)


def wnd_proc(
    hwnd: int | None,
    message: int,
    wparam: float | None,
    lparam: float | None,
) -> int:
    if message == win32con.WM_DESTROY:
        win32gui.PostQuitMessage(0)
        return 0
    return win32gui.DefWindowProc(hwnd, message, wparam, lparam)


class RobustInvisibleWindow:
    """Context manager for creating and destroying an invisible window."""
    CLASS_NAME: str = "RobustInvisibleWindow"
    DISPLAY_NAME: str = "Robust Invisible Window"

    def __init__(self):
        self.hwnd: int | None = None

    def __enter__(self) -> int:
        self.register_class()
        self.hwnd = self.create_window()
        return self.hwnd

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.hwnd is not None:
            win32gui.DestroyWindow(self.hwnd)
        self.unregister_class()

    def register_class(self):
        """Register the window class."""
        wc: PyWNDCLASS = win32gui.WNDCLASS()
        wc.lpfnWndProc = WNDPROC(wnd_proc)
        wc.lpszClassName = self.CLASS_NAME
        wc.hInstance = kernel32.GetModuleHandleW(None)
        wc.hCursor = user32.LoadCursorW(None, 32512)
        try:
            self._class_atom: PyResourceId = win32gui.RegisterClass(wc)
        except Exception as e:  # Don't import pywintypes here, unsafe.
            if getattr(e, "winerror", None) != 1410:  # class already registered
                raise

    def unregister_class(self):
        """Unregister the window class."""
        win32gui.UnregisterClass(self.CLASS_NAME, kernel32.GetModuleHandleW(None))

    def create_window(self) -> int:
        """Create an invisible window."""
        return user32.CreateWindowExW(
            0, self.CLASS_NAME, self.DISPLAY_NAME, 0, 0, 0, 0, 0, None, None,
            kernel32.GetModuleHandleW(None), None)


def _safe_path_parse(file_path: os.PathLike | str) -> WindowsPath:
    return WindowsPath(os.fspath(file_path))


def safe_isfile(path: WindowsPath) -> bool | None:
    try:
        result: bool = path.is_file()
    except (OSError, ValueError):
        return None
    else:
        return result


def safe_isdir(path: WindowsPath) -> bool | None:
    try:
        result: bool = path.is_dir()
    except (OSError, ValueError):
        return None
    else:
        return result


# Function to display context menu
def windows_context_menu_file(file_path: os.PathLike | str):
    """Opens the default windows context menu for a filepath at the position of the cursor."""
    # Normalize filepath for safety
    parsed_filepath: WindowsPath = _safe_path_parse(file_path)
    hwnd = None

    shell: CDispatch = win32com.client.Dispatch("Shell.Application")
    folder: CDispatch = shell.NameSpace(str(parsed_filepath.parent))
    item: CDispatch = folder.ParseName(parsed_filepath.name)
    context_menu: CDispatch = item.Verbs()
    hmenu: int = win32gui.CreatePopupMenu()
    for i, verb in enumerate(context_menu):
        if verb.Name:
            win32gui.AppendMenu(hmenu, win32con.MF_STRING, i + 1, verb.Name)
    pt: tuple[int, int] = win32gui.GetCursorPos()

    with RobustInvisibleWindow() as hwnd:
        cmd: int = win32gui.TrackPopupMenu(hmenu, win32con.TPM_LEFTALIGN | win32con.TPM_RETURNCMD,
                                        pt[0], pt[1], 0, hwnd, None)
        if cmd:
            verb: DispatchBaseClass = context_menu.Item(cmd - 1)
            if verb:
                verb.DoIt()


def windows_context_menu_folder(folder_path: os.PathLike | str):
    """Opens the default windows context menu for a folderpath at the position of the cursor."""
    # Normalize folder path for safety
    parsed_folderpath: WindowsPath = _safe_path_parse(folder_path)
    hwnd = None

    shell: CDispatch = win32com.client.Dispatch("Shell.Application")
    folder: CDispatch = shell.NameSpace(str(parsed_folderpath))
    item: CDispatch = folder.Self
    context_menu: CDispatch = item.Verbs()
    hmenu: int = win32gui.CreatePopupMenu()
    for i, verb in enumerate(context_menu):
        if verb.Name:
            win32gui.AppendMenu(hmenu, win32con.MF_STRING, i + 1, verb.Name)

    pt: tuple[int, int] = win32gui.GetCursorPos()

    with RobustInvisibleWindow() as hwnd:
        cmd: int = win32gui.TrackPopupMenu(hmenu, win32con.TPM_LEFTALIGN | win32con.TPM_RETURNCMD,
                                    pt[0], pt[1], 0, hwnd, None)
        if cmd:
            verb: DispatchBaseClass = context_menu.Item(cmd - 1)
            if verb:
                verb.DoIt()


def windows_context_menu_multiple(paths: Sequence[os.PathLike | str]):
    """Opens the default windows context menu for multiple files/folder paths at the position of the cursor."""
    # Normalize paths for safety
    parsed_paths: list[WindowsPath] = [_safe_path_parse(path) for path in paths]
    hwnd = None

    shell: CDispatch = win32com.client.Dispatch("Shell.Application")
    folders_items: list[CDispatch] = [
        shell.NameSpace(str(path.parent if safe_isfile(path) else path)).ParseName(path.name)
        for path in parsed_paths
    ]
    context_menu: CDispatch = folders_items[0].Verbs()
    hmenu: int = win32gui.CreatePopupMenu()
    for i, verb in enumerate(context_menu):
        if verb.Name:
            win32gui.AppendMenu(hmenu, win32con.MF_STRING, i + 1, verb.Name)

    pt: tuple[int, int] = win32gui.GetCursorPos()

    with RobustInvisibleWindow() as hwnd:
        cmd: int = win32gui.TrackPopupMenu(hmenu, win32con.TPM_LEFTALIGN | win32con.TPM_RETURNCMD,
                                        pt[0], pt[1], 0, hwnd, None)
        if cmd:
            verb: DispatchBaseClass = context_menu.Item(cmd - 1)
            if verb:
                verb.DoIt()


def windows_context_menu(path: os.PathLike | str):
    """Opens the default windows context menu for a folder/file path at the position of the cursor."""
    parsed_path: WindowsPath = _safe_path_parse(path)
    if safe_isfile(parsed_path):
        windows_context_menu_file(parsed_path)
    elif safe_isdir(parsed_path):
        windows_context_menu_folder(parsed_path)
    else:
        msg = f"Path is neither file nor folder: {path}"
        raise ValueError(msg)


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
