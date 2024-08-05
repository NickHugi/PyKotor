from __future__ import annotations

import ctypes
import subprocess

from utility.logger_util import RobustRootLogger


# Check if a command exists
def command_exists(cmd: str) -> bool:
    return subprocess.call(["which", cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0  # noqa: S603, S607


# Generic function to run subprocess commands
def run_command(cmd: list[str]) -> str | None:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)  # noqa: S603
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


# Fallback 1: Zenity
def zenity_dialog(cmd: list[str]) -> str | None:
    if command_exists("zenity"):
        return run_command(cmd)
    return None


# Fallback 2: Yad
def yad_dialog(cmd: list[str]) -> str | None:
    if command_exists("yad"):
        return run_command(cmd)
    return None


# Fallback 3: GTK (ctypes)
def gtk_file_dialog(title: str, action: str, file_types: list[str] | None = None) -> str | None:
    try:
        libgtk = ctypes.CDLL("libgtk-3.so.0")
        libgtk.gtk_init(None, None)
        dialog = libgtk.gtk_file_chooser_dialog_new(
            title.encode(),
            None,
            action,
            b"_Cancel",
            libgtk.GTK_RESPONSE_CANCEL,
            b"_Open",
            libgtk.GTK_RESPONSE_ACCEPT,
            None
        )
        if file_types:
            for file_type in file_types:
                filter_ = libgtk.gtk_file_filter_new()
                libgtk.gtk_file_filter_add_pattern(filter_, file_type.encode())
                libgtk.gtk_file_chooser_add_filter(dialog, filter_)
        response = libgtk.gtk_dialog_run(dialog)
        if response == libgtk.GTK_RESPONSE_ACCEPT:
            filename = libgtk.gtk_file_chooser_get_filename(dialog)
            return ctypes.string_at(filename).decode()
        libgtk.gtk_widget_destroy(dialog)
    except Exception:  # noqa: BLE001
        return None
    return None


# Fallback 4: Qt (ctypes)
def qt_file_dialog(title: str, file_types: list[str] | None = None, save: bool = False) -> str | None:
    try:
        libQt5 = ctypes.CDLL("libQt5Widgets.so.5")
        argc, argv = ctypes.c_int(1), (ctypes.c_char_p * 1)(b"ctypes_file_dialog")
        app = libQt5.QApplication_New(argc, argv)
        dialog = libQt5.QFileDialog()
        libQt5.QFileDialog_setWindowTitle(dialog, title.encode())
        if file_types:
            filters = ";;".join(file_types)
            libQt5.QFileDialog_setNameFilters(dialog, filters.encode())
        if save:
            result = libQt5.QFileDialog_getSaveFileName(dialog)
        else:
            result = libQt5.QFileDialog_getOpenFileName(dialog)
        if result:
            return result.decode()
    except Exception:  # noqa: BLE001
        return None
    return None



def open_file_dialog(title: str = "Open File", file_types: list[str] | None = None) -> str | None:
    try:
        import tkinter as tk

        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(title=title, filetypes=[(ft, ft) for ft in file_types] if file_types else None)
    except ImportError:
        RobustRootLogger().error("tkinter not installed, attempting fallbacks...")
    else:
        return file_path if file_path else None

    result = zenity_dialog(["zenity", "--file-selection", "--title", title] + (["--file-filter", file_types] if file_types else []))
    if result:
        return result

    result = yad_dialog(["yad", "--file-selection", "--title", title] + (["--file-filter", file_types] if file_types else []))
    if result:
        return result

    return gtk_file_dialog(title, "GTK_FILE_CHOOSER_ACTION_OPEN", file_types) or qt_file_dialog(title, file_types)


def save_file_dialog(title: str = "Save File", file_types: list[str] | None = None) -> str | None:
    try:
        import tkinter as tk

        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.asksaveasfilename(title=title, filetypes=[(ft, ft) for ft in file_types] if file_types else None)
    except ImportError:  # noqa: S110
        RobustRootLogger().error("tkinter not installed, attempting fallbacks...")
    else:
        return file_path if file_path else None

    result = zenity_dialog(["zenity", "--file-selection", "--save", "--title", title] + (["--file-filter", file_types] if file_types else []))
    if result:
        return result

    result = yad_dialog(["yad", "--file-selection", "--save", "--title", title] + (["--file-filter", file_types] if file_types else []))
    if result:
        return result

    return gtk_file_dialog(title, "GTK_FILE_CHOOSER_ACTION_SAVE", file_types) or qt_file_dialog(title, file_types, save=True)


def open_folder_dialog(title: str = "Select Folder") -> str | None:
    try:
        import tkinter as tk

        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        folder_path = filedialog.askdirectory(title=title)
    except ImportError:  # noqa: S110
        RobustRootLogger().error("tkinter not installed, attempting fallbacks...")
    else:
        return folder_path if folder_path else None

    result = zenity_dialog(["zenity", "--file-selection", "--directory", "--title", title])
    if result:
        return result

    result = yad_dialog(["yad", "--file-selection", "--directory", "--title", title])
    if result:
        return result

    return gtk_file_dialog(title, "GTK_FILE_CHOOSER_ACTION_SELECT_FOLDER") or qt_file_dialog(title)


if __name__ == "__main__":
    # Example usage
    print("Open file dialog result:", open_file_dialog("Open a file", ["*.txt", "*.py"]))
    print("Save file dialog result:", save_file_dialog("Save a file", ["*.txt", "*.py"]))
    print("Open folder dialog result:", open_folder_dialog("Select a folder"))
