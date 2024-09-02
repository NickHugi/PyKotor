from __future__ import annotations

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


def askdirectory(  # noqa: ANN201
    *,
    initialdir: os.PathLike | str | None = None,
    mustexist: bool | None = None,
    parent: Misc | None = None,
    title: str | None = None,
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
        from utility.system.win32.com.windialogs import open_folder_dialog
        result = open_folder_dialog(title, None if initialdir is None else str(initialdir))
        return "" if not result or not result[0].strip() else result[0]


def askopenfile(  # noqa: PLR0913
    mode: str = "r",
    *,
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
        from utility.system.win32.com.windialogs import open_file_dialog
        result = open_file_dialog(
            title,
            None if initialdir is None else str(initialdir),
            filetypes,
            defaultextension,
        )
        return None if not result or not result[0].strip() else open(result[0], mode)  # noqa: PTH123, SIM115


def askopenfilename(  # noqa: PLR0913
    *,
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
        from utility.system.win32.com.windialogs import open_file_dialog
        result = open_file_dialog(
            title,
            None if initialdir is None else str(initialdir),
            filetypes,
            defaultextension,
        )
        return "" if not result or not result[0].strip() else result[0]


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
            filetypes=[] if filetypes is None else filetypes,  # rem: do not send None
            initialdir=initialdir,
            initialfile=initialfile,
            title=title,
            parent=_get_tk_root() if parent is None else parent,
            typevariable=typevariable,
        )
        return tuple(result) if result else ""
    except Exception:  # noqa: BLE001
        RobustLogger().warning("Tkinter's filedialog.askopenfilenames() threw an exception!", exc_info=True)
        from utility.system.win32.com.windialogs import open_file_dialog
        result = open_file_dialog(
            title,
            None if initialdir is None else str(initialdir),
            filetypes,
            defaultextension,
            allow_multiple_selection=True
        )
        return tuple(result) if result else ""


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
        return filedialog.askopenfiles(
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
        RobustLogger().warning("Tkinter's filedialog.askopenfiles() threw an exception!", exc_info=True)
        from utility.system.win32.com.windialogs import open_file_dialog
        result = open_file_dialog(
            title,
            None if initialdir is None else str(initialdir),
            filetypes,
            defaultextension,
            allow_multiple_selection=True
        )
        return tuple(open(file, mode) for file in result) if result else None  # noqa: PTH123, SIM115



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
        from utility.system.win32.com.windialogs import save_file_dialog
        result = save_file_dialog(
            title,
            default_folder=None if initialdir is None else str(initialdir),
            file_types=filetypes,
            default_extension=defaultextension,
            overwrite_prompt=True if confirmoverwrite is None else confirmoverwrite
        )
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
        from utility.system.win32.com.windialogs import save_file_dialog
        result = save_file_dialog(
            title,
            default_folder=None if initialdir is None else str(initialdir),
            file_types=filetypes,
            default_extension=defaultextension,
            overwrite_prompt=True if confirmoverwrite is None else confirmoverwrite
        )
        return "" if not result or not result[0].strip() else result[0]


if __name__ == "__main__":
    askdirectory()
    askopenfile()
    askopenfilename()
    asksaveasfile()
    asksaveasfilename()
