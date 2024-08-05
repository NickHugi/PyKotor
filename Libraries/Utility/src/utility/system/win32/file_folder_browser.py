from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

from utility.system.win32.com.windialogs import open_file_dialog, open_folder_dialog, save_file_dialog

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


def askdirectory(
    *,
    initialdir: os.PathLike | str | None = None,
    mustexist: bool | None = None,
    parent: Misc | None = None,
    title: str | None = None,
):
    try:
        from tkinter import filedialog
    except ImportError:
        result = open_folder_dialog(title, None if initialdir is None else str(initialdir))
        if not result:
            return None
        return result[0]
    else:
        return filedialog.askdirectory(
            initialdir=initialdir,
            mustexist=mustexist,
            title=title,
            parent=_get_tk_root() if parent is None else parent,
        )


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
    except ImportError:
        result = open_file_dialog(
            title,
            None if initialdir is None else str(initialdir),
            filetypes,
            defaultextension,
        )
        if not result:
            return None
        return open(result[0], mode)
    else:
        file = filedialog.askopenfile(
            mode,
            defaultextension=defaultextension,
            filetypes=filetypes,
            initialdir=initialdir,
            initialfile=initialfile,
            title=title,
            parent=_get_tk_root() if parent is None else parent,
            typevariable=typevariable,
        )
        return file


def askopenfilename(
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
    except ImportError:
        result = open_file_dialog(
            title,
            None if initialdir is None else str(initialdir),
            filetypes,
            defaultextension,
        )
        if not result:
            return None
        return result[0]
    else:
        file = filedialog.askopenfilename(
            defaultextension=defaultextension,
            filetypes=filetypes,
            initialdir=initialdir,
            initialfile=initialfile,
            title=title,
            parent=_get_tk_root() if parent is None else parent,
            typevariable=typevariable,
        )
        return file


def asksaveasfile(
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
    except ImportError:
        result = save_file_dialog(
            title,
            default_folder=None if initialdir is None else str(initialdir),
            file_types=filetypes,
            default_extension=defaultextension,
            overwrite_prompt=True if confirmoverwrite is None else confirmoverwrite
        )
        if not result:
            return None
        return result[0]
    else:
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


def asksaveasfilename(
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
    except ImportError as e1:
        ...
    else:
        return filedialog.asksaveasfilename(
            defaultextension=defaultextension,
            filetypes=filetypes,
            initialdir=initialdir,
            initialfile=initialfile,
            parent=_get_tk_root() if parent is None else parent,
            title=title,
            typevariable=typevariable,
        )
