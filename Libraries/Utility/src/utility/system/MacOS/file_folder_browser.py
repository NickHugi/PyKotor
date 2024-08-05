from __future__ import annotations

import ctypes
import subprocess

from utility.logger_util import RobustRootLogger


# Check if a command exists
def command_exists(cmd: str) -> bool:
    return subprocess.call(["which", cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0  # noqa: S603, S607


# Run subprocess command
def run_command(cmd: list[str]) -> str | None:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)  # noqa: S603
    except subprocess.CalledProcessError:
        return None
    else:
        return result.stdout.strip()


# AppleScript dialog runner
def applescript_dialog(script: str) -> str | None:
    try:
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=False)  # noqa: S603, S607
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:  # noqa: BLE001
        return None
    else:
        return None


# ctypes method: Using Cocoa Framework
def cocoa_dialog(
    dialog_type: str,
    title: str = "",
    allow_multiple: bool = False,
    show_hidden: bool = False,
    default_name: str = "",
) -> list[str] | str | None:
    try:
        libobjc = ctypes.cdll.LoadLibrary(ctypes.util.find_library("objc"))
        libAppKit = ctypes.cdll.LoadLibrary(ctypes.util.find_library("AppKit"))

        cID = ctypes.c_void_p
        SEL = ctypes.c_void_p
        libobjc.objc_getClass.restype = cID
        libobjc.objc_getClass.argtypes = [ctypes.c_char_p]
        libobjc.sel_registerName.restype = SEL
        libobjc.sel_registerName.argtypes = [ctypes.c_char_p]
        libobjc.objc_msgSend.restype = cID
        libobjc.objc_msgSend.argtypes = [cID, SEL]

        NSOpenPanel = libobjc.objc_getClass(b"NSOpenPanel")
        NSSavePanel = libobjc.objc_getClass(b"NSSavePanel")
        NSURL = libobjc.objc_getClass(b"NSURL")
        NSString = libobjc.objc_getClass(b"NSString")
        NSApplication = libobjc.objc_getClass(b"NSApplication")

        def NSString_from_str(string):
            return libobjc.objc_msgSend(NSString, libobjc.sel_registerName(b"stringWithUTF8String:"), ctypes.c_char_p(string.encode("utf-8")))

        def str_from_NSURL(nsurl):
            utf8_string = libobjc.objc_msgSend(nsurl, libobjc.sel_registerName(b"absoluteString"))
            return ctypes.string_at(libobjc.objc_msgSend(utf8_string, libobjc.sel_registerName(b"UTF8String"))).decode("utf-8")

        app = libobjc.objc_msgSend(NSApplication, libobjc.sel_registerName(b"sharedApplication"))

        if dialog_type in ("open_file", "open_folder"):
            panel = libobjc.objc_msgSend(NSOpenPanel, libobjc.sel_registerName(b"openPanel"))
            libobjc.objc_msgSend_bool(panel, libobjc.sel_registerName(b"setCanChooseFiles:"), ctypes.c_bool(dialog_type == "open_file"))
            libobjc.objc_msgSend_bool(panel, libobjc.sel_registerName(b"setCanChooseDirectories:"), ctypes.c_bool(dialog_type == "open_folder"))
        elif dialog_type == "save_file":
            panel = libobjc.objc_msgSend(NSSavePanel, libobjc.sel_registerName(b"savePanel"))
            if default_name:
                default_name_nsstring = NSString_from_str(default_name)
                libobjc.objc_msgSend_id(panel, libobjc.sel_registerName(b"setNameFieldStringValue:"), default_name_nsstring)

        if title:
            title_nsstring = NSString_from_str(title)
            libobjc.objc_msgSend_id(panel, libobjc.sel_registerName(b"setTitle:"), title_nsstring)

        libobjc.objc_msgSend_bool(panel, libobjc.sel_registerName(b"setAllowsMultipleSelection:"), ctypes.c_bool(allow_multiple))
        libobjc.objc_msgSend_bool(panel, libobjc.sel_registerName(b"setShowsHiddenFiles:"), ctypes.c_bool(show_hidden))

        response = libobjc.objc_msgSend_uint(panel, libobjc.sel_registerName(b"runModal"))

        if response == 1:  # NSModalResponseOK
            if dialog_type == "save_file":
                nsurl = libobjc.objc_msgSend(panel, libobjc.sel_registerName(b"URL"))
                file_path = str_from_NSURL(nsurl)
                return file_path

            urls = libobjc.objc_msgSend(panel, libobjc.sel_registerName(b"URLs"))
            count = libobjc.objc_msgSend_uint(urls, libobjc.sel_registerName(b"count"))

            file_paths = []
            for i in range(count):
                nsurl = libobjc.objc_msgSend_id_uint(urls, libobjc.sel_registerName(b"objectAtIndex:"), i)
                file_paths.append(str_from_NSURL(nsurl))

            return file_paths

    except Exception:  # noqa: BLE001
        RobustRootLogger.exception("Failed to run a cocoa file/folder browser!")
        return None
    else:
        return None


# Primary functions
def open_file_dialog(title: str = "Open File", file_types: list[str] | None = None) -> list[str] | None:
    try:
        import tkinter as tk

        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(title=title, filetypes=[(ft, ft) for ft in file_types] if file_types else None)
    except ImportError:  # noqa: S110
        pass
    else:
        return [file_path] if file_path else None
    file_types_str = "{" + '", "'.join(file_types) + "}" if file_types else "{}"
    script = f"""
        set fileTypes to {file_types_str}
        set filePath to POSIX path of (choose file of type fileTypes with prompt "{title}")
        return filePath
    """

    result = applescript_dialog(script)
    if result:
        return [result]

    return cocoa_dialog("open_file", title)


def save_file_dialog(title: str = "Save File", file_types: list[str] | None = None, default_name: str = "Untitled") -> str | None:
    try:
        import tkinter as tk

        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.asksaveasfilename(title=title, filetypes=[(ft, ft) for ft in file_types] if file_types else None, initialfile=default_name)
    except ImportError:  # noqa: S110
        pass
    else:
        return file_path if file_path else None

    file_types_str = "{" + '", "'.join(file_types) + "}" if file_types else "{}"
    script = f"""
        set fileTypes to {file_types_str}
        set filePath to POSIX path of (choose file name with prompt "{title}")
        return filePath
    """
    result = applescript_dialog(script)
    if result:
        return result

    return cocoa_dialog("save_file", title, default_name=default_name)


def open_folder_dialog(title: str = "Select Folder") -> list[str] | None:
    try:
        import tkinter as tk

        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        folder_path = filedialog.askdirectory(title=title)
    except ImportError:  # noqa: S110
        pass
    else:
        return [folder_path] if folder_path else None

    script = f"""
        set folderPath to POSIX path of (choose folder with prompt "{title}")
        return folderPath
    """
    result = applescript_dialog(script)
    if result:
        return [result]

    return cocoa_dialog("open_folder", title)


if __name__ == "__main__":
    # Example usage
    print("Open file dialog result:", open_file_dialog("Open a file", ["public.text", "public.python-script"]))
    print("Save file dialog result:", save_file_dialog("Save a file", ["public.text", "public.python-script"]))
    print("Open folder dialog result:", open_folder_dialog("Select a folder"))
