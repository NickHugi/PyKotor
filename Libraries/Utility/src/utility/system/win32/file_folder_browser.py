from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

from utility.logger_util import RobustRootLogger

if TYPE_CHECKING:
    import os

    from tkinter import Misc, StringVar  # Do not import tkinter-related outside type-checking blocks, in case not installed.


def _get_tk_root():
    import tkinter as tk
    if tk._default_root is None:  # pyright: ignore[reportAttributeAccessIssue]  # noqa: SLF001
        root = tk.Tk()
        root.withdraw()
        return root
    return tk._default_root  # pyright: ignore[reportAttributeAccessIssue]  # noqa: SLF001


def askdirectory(  # noqa: ANN201
    *,
    initialdir: os.PathLike | str | None = None,
    mustexist: bool | None = None,
    parent: Misc | None = None,
    title: str | None = None,
):
    try:
        from tkinter import filedialog
        return filedialog.askdirectory(
            initialdir=initialdir,
            mustexist=mustexist,
            title=title,
            parent=_get_tk_root() if parent is None else parent,
        )
    except Exception:  # noqa: BLE001
        RobustRootLogger().warning("Tkinter's filedialog.askopenfilename() threw an exception!", exc_info=True)
        from utility.system.win32.com.windialogs import open_folder_dialog
        result = open_folder_dialog(title, None if initialdir is None else str(initialdir))
        if not result:
            return ""
        return result[0]


def askopenfile(
    mode: str = "r",
    *,
    defaultextension: str | None = None,
    filetypes: Iterable[tuple[str, str | list[str] | tuple[str, ...]]] | None = None,
    initialdir: os.PathLike | str | None = None,
    initialfile: os.PathLike | str | None = None,
    parent: Misc | None = None,
    title: str | None = None,
    typevariable: StringVar | str | None = None,
):
    try:
        from tkinter import filedialog
        return filedialog.askopenfile(
            mode,
            defaultextension=defaultextension,
            filetypes=filetypes,
            initialdir=initialdir,
            initialfile=initialfile,
            title=title,
            parent=_get_tk_root() if parent is None else parent,
            typevariable=typevariable,
        )
    except Exception:  # noqa: BLE001
        RobustRootLogger().warning("Tkinter's filedialog.askopenfilename() threw an exception!", exc_info=True)
        from utility.system.win32.com.windialogs import open_file_dialog
        result = open_file_dialog(
            title,
            None if initialdir is None else str(initialdir),
            filetypes,
            defaultextension,
        )
        if not result:
            return None
        return open(result[0], mode)


def askopenfilename(  # noqa: PLR0913
    *,
    defaultextension: str | None = None,
    filetypes: Iterable[tuple[str, str | list[str] | tuple[str, ...]]] | None = None,
    initialdir: os.PathLike | str | None = None,
    initialfile: os.PathLike | str | None = None,
    parent: Misc | None = None,
    title: str | None = None,
    typevariable: StringVar | str | None = None,
) -> str | None:
    try:
        from tkinter import filedialog
        return filedialog.askopenfilename(
            defaultextension=defaultextension,
            filetypes=filetypes,
            initialdir=initialdir,
            initialfile=initialfile,
            title=title,
            parent=_get_tk_root() if parent is None else parent,
            typevariable=typevariable,
        )
    except Exception:  # noqa: BLE001
        RobustRootLogger().warning("Tkinter's filedialog.askopenfilename() threw an exception!", exc_info=True)
        from utility.system.win32.com.windialogs import open_file_dialog
        result = open_file_dialog(
            title,
            None if initialdir is None else str(initialdir),
            filetypes,
            defaultextension,
        )
        if not result:
            return ""
        return result[0]


def asksaveasfile(  # noqa: PLR0913, ANN201
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
):
    try:
        from tkinter import filedialog
        return filedialog.asksaveasfile(
            mode,
            confirmoverwrite=confirmoverwrite,
            defaultextension=defaultextension,
            filetypes=filetypes,
            initialdir=initialdir,
            initialfile=initialfile,
            parent=_get_tk_root() if parent is None else parent,
            title=title,
            typevariable=typevariable,
        )
    except Exception:  # noqa: BLE001
        RobustRootLogger().warning("Tkinter's filedialog.asksaveasfile() threw an exception!", exc_info=True)
        from utility.system.win32.com.windialogs import save_file_dialog
        result = save_file_dialog(
            title,
            default_folder=None if initialdir is None else str(initialdir),
            file_types=filetypes,
            default_extension=defaultextension,
            overwrite_prompt=True if confirmoverwrite is None else confirmoverwrite
        )
        if not result:
            return None
        return open(result[0], mode)


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
        return filedialog.asksaveasfilename(
            confirmoverwrite=confirmoverwrite,
            defaultextension=defaultextension,
            filetypes=filetypes,
            initialdir=initialdir,
            initialfile=initialfile,
            parent=_get_tk_root() if parent is None else parent,
            title=title,
            typevariable=typevariable,
        )
    except Exception:  # noqa: BLE001
        RobustRootLogger().warning("Tkinter's filedialog.asksaveasfilename() threw an exception!", exc_info=True)
        from utility.system.win32.com.windialogs import save_file_dialog
        result = save_file_dialog(
            title,
            default_folder=None if initialdir is None else str(initialdir),
            file_types=filetypes,
            default_extension=defaultextension,
            overwrite_prompt=True if confirmoverwrite is None else confirmoverwrite
        )
        if not result:
            return ""
        return result[0]
