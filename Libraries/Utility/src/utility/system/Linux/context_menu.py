from __future__ import annotations

import ctypes
import subprocess

from ctypes import c_char_p, c_int
from pathlib import PosixPath
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import os


# Check if a command exists
def command_exists(cmd: str) -> bool:
    return subprocess.call(["which", cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0  # noqa: S603, S607

# Get default actions using xdg-mime and gio
def get_default_actions(path: os.PathLike | str) -> list[str]:
    try:
        mime_type = subprocess.check_output(["xdg-mime", "query", "filetype", path], text=True).strip()  # noqa: S603, S607
        actions = subprocess.check_output(["gio", "mime", mime_type], text=True).splitlines()  # noqa: S603, S607
    except Exception:  # noqa: BLE001
        return []
    else:
        return [action.split(":")[1].strip() for action in actions if action.startswith("default:")]

# ctypes method 1: Using GTK
def context_menu_gtk(path: os.PathLike | str) -> bool:
    try:
        libgtk = ctypes.CDLL("libgtk-3.so.0")
        libgtk.gtk_init(None, None)
        menu = libgtk.gtk_menu_new()
        actions = get_default_actions(path)
        if not actions:
            return False
        items = [libgtk.gtk_menu_item_new_with_label(action.encode()) for action in actions]
        for item in items:
            libgtk.gtk_menu_shell_append(menu, item)
        libgtk.gtk_widget_show_all(menu)
        status_icon = libgtk.gtk_status_icon_new()
        libgtk.gtk_status_icon_set_visible(status_icon, 1)
        libgtk.gtk_status_icon_set_from_icon_name(status_icon, b"system-file-manager")
        libgtk.gtk_status_icon_set_tooltip_text(status_icon, b"Context Menu")
        libgtk.gtk_main()
    except Exception:  # noqa: BLE001
        return False
    else:
        return True

# ctypes method 2: Using Qt
def context_menu_qt(path: os.PathLike | str) -> bool:
    try:
        libQt5 = ctypes.CDLL("libQt5Widgets.so.5")
        argc, argv = c_int(1), (c_char_p * 1)(b"ctypes_menu")
        app, menu = libQt5.QApplication_New(argc, argv), libQt5.QMenu_New()
        actions = get_default_actions(path)
        if not actions:
            return False
        for action in actions:
            libQt5.QMenu_addAction(menu, action.encode())
        libQt5.QMenu_exec(menu)
        libQt5.qApp.exec()
    except Exception:  # noqa: BLE001
        return False
    else:
        return True

# ctypes method 3: Using wxWidgets
def context_menu_wxwidgets(path: os.PathLike | str) -> bool:
    try:
        libwx = ctypes.CDLL("libwx_baseu-3.0.so.0")
        argc, argv = c_int(1), (c_char_p * 1)(b"ctypes_menu")
        libwx.wxEntryStart(argc, argv)
        app = libwx.wxTheApp()
        frame = libwx.wxFrame_New(None, -1, b"Context Menu", (50, 50), (450, 340))
        menu, menu_bar = libwx.wxMenu_New(), libwx.wxMenuBar_New()
        actions = get_default_actions(path)
        if not actions:
            return False
        for i, action in enumerate(actions):
            libwx.wxMenu_Append(menu, i + 1, action.encode())
        libwx.wxMenuBar_Append(menu_bar, menu, b"File")
        libwx.wxFrame_SetMenuBar(frame, menu_bar)
        libwx.wxEntry()
    except Exception:  # noqa: BLE001
        return False
    else:
        return True


def context_menu_zenity(path: str):
    if not command_exists("zenity"):
        return False
    try:
        actions = get_default_actions(path)
        if not actions:
            return False
        result = subprocess.run(
            ["zenity", "--list", "--title=Context Menu", "--column=Options", *actions],  # noqa: S603, S607
            stdout=subprocess.PIPE,
            text=True, check=False
        )
        if result.returncode == 0:
            choice = result.stdout.strip()
            if choice:
                subprocess.run(["zenity", "--info", f"--text=You chose '{choice}' for '{path}'"], check=False)  # noqa: S603, S607
    except Exception as e:  # noqa: BLE001
        print(f"Zenity method failed: {e}")
        return False
    else:
        return result.returncode == 0


def context_menu_yad(path: str):
    if not command_exists("yad"):
        return False
    try:
        actions = get_default_actions(path)
        if not actions:
            return False
        result = subprocess.run(
            ["yad", "--list", "--title=Context Menu", "--column=Options", *actions],  # noqa: S607, S603
            stdout=subprocess.PIPE,
            text=True, check=False
        )
        if result.returncode == 0:
            choice = result.stdout.strip()
            if choice:
                subprocess.run(["yad", "--info", f"--text=You chose '{choice}' for '{path}'"], check=False)  # noqa: S607, S603
    except Exception as e:  # noqa: BLE001
        print(f"Yad method failed: {e}")
        return False
    else:
        return result.returncode == 0


def context_menu_dmenu(path: str):  # noqa: ANN201
    if not command_exists("dmenu") or not command_exists("notify-send"):
        return False
    try:
        actions = get_default_actions(path)
        if not actions:
            return False
        process = subprocess.Popen(
            ["dmenu", "-p", "Choose an option:"],  # noqa: S607, S603
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True
        )
        result, _ = process.communicate(input="\n".join(actions))
        if process.returncode == 0:
            choice = result.strip()
            if choice:
                subprocess.run(["notify-send", f"You chose '{choice}' for '{path}'"], check=False)  # noqa: S603, S607
    except Exception as e:  # noqa: BLE001
        print(f"Spawning context menu through dmenu failed: {e.__class__.__name__}: {e}")
        return False
    else:
        return process.returncode == 0


def show_context_menu(path: str):
    abs_path = PosixPath(path).resolve()
    def cmd_exists(cmd) -> bool:
        return subprocess.call(["which", cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0  # noqa: S603, S607
    def get_actions(p) -> list[str]:
        return [
            a.split(":")[1].strip()
            for a in subprocess.check_output(
                ["gio", "mime", subprocess.check_output(["xdg-mime", "query", "filetype", p], text=True).strip()],  # noqa: S607, S603
                text=True,
            ).splitlines()
            if a.startswith("default:")
        ]

    methods = [
        lambda p: cmd_exists("nautilus") and not subprocess.run(["nautilus", "--select", p], check=False).returncode,  # noqa: S603, S607
        lambda p: cmd_exists("dolphin") and not subprocess.run(["dolphin", "--select", p], check=False).returncode,  # noqa: S603, S607
        lambda p: cmd_exists("thunar") and not subprocess.run(["thunar", p], check=False).returncode,  # noqa: S603, S607
        lambda p: cmd_exists("nemo") and not subprocess.run(["nemo", "--no-desktop", "--browser", p], check=False).returncode,  # noqa: S603, S607
        lambda p: cmd_exists("caja") and not subprocess.run(["caja", "--browser", p], check=False).returncode,  # noqa: S603, S607
        lambda p: cmd_exists("pcmanfm") and not subprocess.run(["pcmanfm", p], check=False).returncode,  # noqa: S603, S607
        lambda p: cmd_exists("konqueror") and not subprocess.run(["konqueror", p], check=False).returncode,  # noqa: S603, S607
        lambda p: cmd_exists("spacefm") and not subprocess.run(["spacefm", p], check=False).returncode,  # noqa: S603, S607
        lambda p: cmd_exists("rox") and not subprocess.run(["rox", p], check=False).returncode,  # noqa: S603, S607
        lambda p: cmd_exists("krusader") and not subprocess.run(["krusader", p], check=False).returncode,  # noqa: S603, S607
        context_menu_zenity,
        context_menu_yad,
        context_menu_dmenu,
        context_menu_gtk,
        context_menu_qt,
        context_menu_wxwidgets
    ]
    abs_path = PosixPath(path).resolve()
    for method in methods:
        if method(abs_path):
            return
    print("All methods failed to display the context menu.")


if __name__ == "__main__":
    show_context_menu(r"C:\Program Files (x86)\Steam\steamapps\common\swkotor\modules\danm15.rim")
