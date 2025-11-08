from __future__ import annotations

import subprocess

from typing import TYPE_CHECKING

from loggerplus import RobustLogger

if TYPE_CHECKING:
    import os

    from tkinter import Misc, StringVar, Tk  # Do not import tkinter-related outside type-checking blocks, in case not installed.
    from typing import IO, Any, Iterable

    from typing_extensions import Literal


def _get_tk_root() -> Tk:
    import tkinter as tk
    if tk._default_root is None:  # pyright: ignore[reportAttributeAccessIssue]  # noqa: SLF001
        root = tk.Tk()
        root.withdraw()
        return root
    return tk._default_root  # pyright: ignore[reportAttributeAccessIssue]  # noqa: SLF001

def _run_apple_script(script: str) -> str:
    result = subprocess.run(
        ["osascript", "-e", script], check=True, capture_output=True, text=True  # noqa: S607, S603
    )
    return result.stdout.strip()

def _run_cocoa_dialog(  # noqa: C901, PLR0913
    dialog_type: str,
    title: str | None = None,
    initialdir: str | None = None,
    initialfile: str | None = None,
    filetypes: Iterable[tuple[str, str | list[str] | tuple[str, ...]]] | None = None,
    defaultextension: str | None = None,
) -> str | None:
    import ctypes
    import ctypes.util

    libobjc = ctypes.cdll.LoadLibrary(ctypes.util.find_library("objc"))

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
    NSArray = libobjc.objc_getClass(b"NSArray")

    def NSString_from_str(string):
        return libobjc.objc_msgSend(NSString, libobjc.sel_registerName(b"stringWithUTF8String:"), ctypes.c_char_p(string.encode("utf-8")))

    def str_from_NSURL(nsurl):
        utf8_string = libobjc.objc_msgSend(nsurl, libobjc.sel_registerName(b"absoluteString"))
        return ctypes.string_at(libobjc.objc_msgSend(utf8_string, libobjc.sel_registerName(b"UTF8String"))).decode("utf-8")

    if dialog_type in ("open_file", "open_folder"):
        panel = libobjc.objc_msgSend(NSOpenPanel, libobjc.sel_registerName(b"openPanel"))
        libobjc.objc_msgSend(panel, libobjc.sel_registerName(b"setCanChooseFiles:"), ctypes.c_bool(dialog_type == "open_file"))
        libobjc.objc_msgSend(panel, libobjc.sel_registerName(b"setCanChooseDirectories:"), ctypes.c_bool(dialog_type == "open_folder"))
    elif dialog_type == "save_file":
        panel = libobjc.objc_msgSend(NSSavePanel, libobjc.sel_registerName(b"savePanel"))

    if title:
        title_nsstring = NSString_from_str(title)
        libobjc.objc_msgSend(panel, libobjc.sel_registerName(b"setTitle:"), title_nsstring)

    if initialdir:
        initialdir_nsstring = NSString_from_str(initialdir)
        url = libobjc.objc_msgSend(NSURL, libobjc.sel_registerName(b"fileURLWithPath:"), initialdir_nsstring)
        libobjc.objc_msgSend(panel, libobjc.sel_registerName(b"setDirectoryURL:"), url)

    if initialfile:
        initialfile_nsstring = NSString_from_str(initialfile)
        libobjc.objc_msgSend(panel, libobjc.sel_registerName(b"setNameFieldStringValue:"), initialfile_nsstring)

    if filetypes:
        allowed_file_types = []
        for ft in filetypes:
            if isinstance(ft[1], str):
                allowed_file_types.append(NSString_from_str(ft[1]))
            else:
                allowed_file_types.extend(NSString_from_str(ext) for ext in ft[1])
        allowed_file_types_nsarray = libobjc.objc_msgSend(NSArray, libobjc.sel_registerName(b"arrayWithObjects:count:"), (cID * len(allowed_file_types))(*allowed_file_types), len(allowed_file_types))
        libobjc.objc_msgSend(panel, libobjc.sel_registerName(b"setAllowedFileTypes:"), allowed_file_types_nsarray)

    if defaultextension:
        defaultextension_nsstring = NSString_from_str(defaultextension)
        libobjc.objc_msgSend(panel, libobjc.sel_registerName(b"setAllowedFileTypes:"), defaultextension_nsstring)

    response = libobjc.objc_msgSend(panel, libobjc.sel_registerName(b"runModal"))

    # NSModalResponseOK is defined as 1 in macOS
    if response == 1:
        nsurl = libobjc.objc_msgSend(panel, libobjc.sel_registerName(b"URL"))
        return str_from_NSURL(nsurl)

    return None


def askdirectory(
    *,
    initialdir: os.PathLike | str | None = None,
    mustexist: bool | None = None,
    parent: Misc | None = None,
    title: str | None = None
) -> str:
    try:
        from tkinter import filedialog
        result = filedialog.askdirectory(
            initialdir=initialdir,
            mustexist=mustexist,
            title=title,
            parent=_get_tk_root() if parent is None else parent,
        )
        return "" if not result or not result.strip() else result
    except Exception:  # noqa: BLE001
        RobustLogger().warning("Tkinter's filedialog.askdirectory() threw an exception!", exc_info=True)
        try:
            result = _run_cocoa_dialog(
                dialog_type="open_folder",
                title=title,
                initialdir=None if initialdir is None else str(initialdir),
            )
            return "" if not result or not result.strip() else result
        except Exception:  # noqa: BLE001
            try:
                script = f"""
                    set directory to POSIX path of (choose folder with prompt "{title}"{f' default location POSIX file "{initialdir}"' if initialdir else ''})
                    return directory
                """
                result = _run_apple_script(script)
                return "" if not result or not result.strip() else result
            except Exception as e3:
                raise RuntimeError("All methods to open directory dialog failed") from e3


def askopenfile(  # noqa: PLR0913
    mode: str = "r",
    *,
    defaultextension: str | None = None,
    filetypes: Iterable[tuple[str, str | list[str] | tuple[str, ...]]] | None = None,
    initialdir: str | None = None,
    initialfile: str | None = None,
    parent: Misc | None = None,
    title: str | None = None,
    typevariable: StringVar | str | None = None,
) -> IO[Any] | None:
    try:
        from tkinter import filedialog
        return filedialog.askopenfile(
            mode,
            defaultextension=defaultextension,
            filetypes=[] if filetypes is None else filetypes,  # rem: do not send None
            initialdir=initialdir,
            initialfile=initialfile,
            title=title,
            parent=_get_tk_root() if parent is None else parent,
            typevariable=typevariable,
        )
    except Exception:  # noqa: BLE001
        RobustLogger().warning("Tkinter's filedialog.askopenfile() threw an exception!", exc_info=True)
        try:
            result = _run_cocoa_dialog(
                "open_file",
                defaultextension=defaultextension,
                filetypes=filetypes,
                initialdir=initialdir,
                initialfile=initialfile,
                title=title,
            )
            return None if not result or not result.strip() else open(result, mode)  # noqa: SIM115, PTH123
        except Exception:  # noqa: BLE001
            try:
                script = f'set file to POSIX path of (choose file with prompt "{title}"'

                if initialdir:
                    script += f' default location POSIX file "{initialdir}"'

                if filetypes:
                    file_types_str = ", ".join([f'"{ft[1]}"' if isinstance(ft[1], str) else "{"+", ".join([f'"{ext}"' for ext in ft[1]])+"}" for ft in filetypes])
                    script += f" of type {{{file_types_str}}}"

                script += ")"
                script += "\nreturn file"

                result = _run_apple_script(script)
                return None if not result or not result.strip() else open(result, mode)  # noqa: SIM115, PTH123
            except Exception as e3:
                raise RuntimeError("All methods to open file dialog failed") from e3

def askopenfilename(  # noqa: PLR0913
    *,
    defaultextension: str | None = None,
    filetypes: Iterable[tuple[str, str | list[str] | tuple[str, ...]]] | None = None,
    initialdir: str | None = None,
    initialfile: str | None = None,
    parent: Misc | None = None,
    title: str | None = None,
    typevariable: StringVar | str | None = None,
) -> str:
    try:
        from tkinter import filedialog
        result = filedialog.askopenfilename(
            defaultextension=defaultextension,
            filetypes=[] if filetypes is None else filetypes,  # rem: do not send None
            initialdir=initialdir,
            initialfile=initialfile,
            title=title,
            parent=_get_tk_root() if parent is None else parent,
            typevariable=typevariable,
        )
        return "" if not result or not result.strip() else result
    except Exception:  # noqa: BLE001
        RobustLogger().warning("Tkinter's filedialog.askopenfilename() threw an exception!", exc_info=True)
        try:
            result = _run_cocoa_dialog(
                "open_file",
                defaultextension=defaultextension,
                filetypes=filetypes,
                initialdir=initialdir,
                initialfile=initialfile,
                title=title,
            )
            return "" if not result or not result.strip() else result
        except Exception:  # noqa: BLE001
            try:
                script = f'set file to POSIX path of (choose file with prompt "{title}"'

                if initialdir:
                    script += f' default location POSIX file "{initialdir}"'

                if filetypes:
                    file_types_str = ", ".join([f'"{ft[1]}"' if isinstance(ft[1], str) else "{"+", ".join([f'"{ext}"' for ext in ft[1]])+"}" for ft in filetypes])
                    script += f" of type {{{file_types_str}}}"

                script += ")"
                script += "\nreturn file"

                result = _run_apple_script(script)
                return "" if not result or not result.strip() else result
            except Exception as e3:
                raise RuntimeError("All methods to open file dialog failed") from e3


def askopenfilenames(  # noqa: PLR0913
    *,
    defaultextension: str | None = None,
    filetypes: Iterable[tuple[str, str | list[str] | tuple[str, ...]]] | None = None,
    initialdir: os.PathLike | str | None = None,
    initialfile: os.PathLike | str | None = None,
    parent: Misc | None = None,
    title: str | None = None,
    typevariable: StringVar | str | None = None,
) -> tuple[str, ...] | Literal[""]:
    try:
        from tkinter import filedialog
        result = filedialog.askopenfilenames(
            defaultextension=defaultextension,
            filetypes=[] if filetypes is None else filetypes,
            initialdir=initialdir,
            initialfile=initialfile,
            title=title,
            parent=_get_tk_root() if parent is None else parent,
            typevariable=typevariable,
        )
        return tuple(result) if result else ""
    except Exception:  # noqa: BLE001
        RobustLogger().warning("Tkinter's filedialog.askopenfilenames() threw an exception!", exc_info=True)
        try:
            result = _run_cocoa_dialog(
                dialog_type="open_file",
                defaultextension=defaultextension,
                filetypes=filetypes,
                initialdir=initialdir,
                initialfile=initialfile,
                title=title,
            )
            return tuple(result.split(",")) if result else ""
        except Exception:  # noqa: BLE001
            try:
                script = f'set files to choose file with prompt "{title}"'
                if initialdir:
                    script += f' default location POSIX file "{initialdir}"'
                if filetypes:
                    file_types_str = ", ".join([f'"{ft[1]}"' if isinstance(ft[1], str) else "{"+", ".join([f'"{ext}"' for ext in ft[1]])+"}" for ft in filetypes])
                    script += f" of type {{{file_types_str}}}"
                script += " with multiple selections allowed"
                script += "\nreturn files as POSIX path"
                result = _run_apple_script(script)
                return tuple(result.split(",")) if result else ""
            except Exception as e3:
                raise RuntimeError("All methods to open multiple files dialog failed") from e3


def askopenfiles(  # noqa: PLR0913
    mode: str = "r",
    *,
    defaultextension: str | None = None,
    filetypes: Iterable[tuple[str, str | list[str] | tuple[str, ...]]] | None = None,
    initialdir: os.PathLike | str | None = None,
    initialfile: os.PathLike | str | None = None,
    parent: Misc | None = None,
    title: str | None = None,
    typevariable: StringVar | str | None = None,
) -> tuple[IO[Any], ...] | None:
    try:
        from tkinter import filedialog
        result = filedialog.askopenfiles(
            mode=mode,
            defaultextension=defaultextension,
            filetypes=[] if filetypes is None else filetypes,
            initialdir=initialdir,
            initialfile=initialfile,
            title=title,
            parent=_get_tk_root() if parent is None else parent,
            typevariable=typevariable,
        )
        return tuple(result) if result else None
    except Exception:  # noqa: BLE001
        RobustLogger().warning("Tkinter's filedialog.askopenfiles() threw an exception!", exc_info=True)
        try:
            result = _run_cocoa_dialog(
                dialog_type="open_file",
                defaultextension=defaultextension,
                filetypes=filetypes,
                initialdir=initialdir,
                initialfile=initialfile,
                title=title,
            )
            return tuple(open(f, mode) for f in result.split(",")) if result else None
        except Exception:  # noqa: BLE001
            try:
                script = f'set files to choose file with prompt "{title}"'
                if initialdir:
                    script += f' default location POSIX file "{initialdir}"'
                if filetypes:
                    file_types_str = ", ".join([f'"{ft[1]}"' if isinstance(ft[1], str) else "{"+", ".join([f'"{ext}"' for ext in ft[1]])+"}" for ft in filetypes])
                    script += f" of type {{{file_types_str}}}"
                script += " with multiple selections allowed"
                script += "\nreturn files as POSIX path"
                result = _run_apple_script(script)
                return tuple(open(f, mode) for f in result.split(",")) if result else None
            except Exception as e3:
                raise RuntimeError("All methods to open multiple files dialog failed") from e3


def asksaveasfile(  # noqa: PLR0913
    mode: str = "w",
    *,
    confirmoverwrite: bool | None = None,
    defaultextension: str | None = None,
    filetypes: Iterable[tuple[str, str | list[str] | tuple[str, ...]]] | None = None,
    initialdir: os.PathLike | str | None = None,
    initialfile: os.PathLike | str | None = None,
    parent: Misc | None = None,
    title: str | None = None,
    typevariable: StringVar | str | None = None,
) -> IO[Any] | None:
    try:
        from tkinter import filedialog
        return filedialog.asksaveasfile(
            mode,
            confirmoverwrite=confirmoverwrite,
            defaultextension=defaultextension,
            filetypes=[] if filetypes is None else filetypes,  # rem: do not send None
            initialdir=initialdir,
            initialfile=initialfile,
            parent=_get_tk_root() if parent is None else parent,
            title=title,
            typevariable=typevariable,
        )
    except Exception:  # noqa: BLE001
        RobustLogger().warning("Tkinter's filedialog.asksaveasfile() threw an exception!", exc_info=True)
        try:
            result = _run_cocoa_dialog(
                "save_file",
                defaultextension=defaultextension,
                filetypes=filetypes,
                initialdir=str(initialdir),
                initialfile=str(initialfile),
                title=title,
            )
            return None if not result or not result[0].strip() else open(result[0], mode)  # noqa: PTH123, SIM115
        except Exception:  # noqa: BLE001
            script = f"""
                set file to POSIX path of (choose file name with prompt "{title}"{f' default location POSIX file "{initialdir}"' if initialdir else ''}{f' default name "{initialfile}"' if initialfile else ''})
                return file
            """
            result = _run_apple_script(script)
            return None if not result or not result[0].strip() else open(result[0], mode)  # noqa: PTH123, SIM115


def asksaveasfilename(  # noqa: PLR0913
    *,
    confirmoverwrite: bool | None = None,
    defaultextension: str | None = None,
    filetypes: Iterable[tuple[str, str | list[str] | tuple[str, ...]]] | None = None,
    initialdir: os.PathLike | str | None = None,
    initialfile: os.PathLike | str | None = None,
    parent: Misc | None = None,
    title: str | None = None,
    typevariable: StringVar | str | None = None,
) -> str:
    try:
        from tkinter import filedialog
        result = filedialog.asksaveasfilename(
            confirmoverwrite=confirmoverwrite,
            defaultextension=defaultextension,
            filetypes=[] if filetypes is None else filetypes,  # rem: do not send None
            initialdir=initialdir,
            initialfile=initialfile,
            parent=_get_tk_root() if parent is None else parent,
            title=title,
            typevariable=typevariable,
        )
        return "" if not result or not result.strip() else result
    except Exception:  # noqa: BLE001
        RobustLogger().warning("Tkinter's filedialog.asksaveasfilename() threw an exception!", exc_info=True)
        try:
            result = _run_cocoa_dialog(
                "save_file",
                defaultextension=defaultextension,
                filetypes=filetypes,
                initialdir=str(initialdir),
                initialfile=str(initialfile),
                title=title,
            )
            return "" if not result or not result.strip() else result
        except Exception:  # noqa: BLE001
            script = f"""
                set file to POSIX path of (choose file name with prompt "{title}"{f' default location POSIX file "{initialdir}"' if initialdir else ''}{f' default name "{initialfile}"' if initialfile else ''})
                return file
            """  # noqa: E501
            result = _run_apple_script(script)
            return "" if not result or not result.strip() else result


if __name__ == "__main__":
    askdirectory()
    askopenfile()
    askopenfilename()
    asksaveasfile()
    asksaveasfilename()
