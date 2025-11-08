from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import tkinter as tk  # Do not import tkinter-related outside type-checking blocks, in case not installed.

from utility.system.win32.winapi.messagebox import (
    IDNO,
    IDOK,
    IDRETRY,
    IDYES,
    MB_ICONQUESTION,
    MB_YESNOCANCEL,
    show_error_message_box,
    show_ok_message_box,
    show_retry_cancel_message_box,
    show_warning_message_box,
    show_yes_no_message_box,
    windows_message_box,
)


def _get_tk_root() -> tk.Tk:
    import tkinter as tk
    if tk._default_root is None:  # pyright: ignore[reportAttributeAccessIssue]  # noqa: SLF001
        root = tk.Tk()
        root.withdraw()
        return root
    return tk._default_root  # pyright: ignore[reportAttributeAccessIssue]  # noqa: SLF001

def showinfo(title: str, message: str, **options):
    try:
        from tkinter import messagebox
    except ImportError:
        return show_ok_message_box(message, title)
    else:
        _get_tk_root()
        return messagebox.showinfo(title, message, **options)


def showwarning(title: str, message: str, **options):
    try:
        from tkinter import messagebox
    except ImportError:
        return show_warning_message_box(message, title)
    else:
        _get_tk_root()
        return messagebox.showwarning(title, message, **options)


def showerror(title: str, message: str, **options):
    try:
        from tkinter import messagebox
    except ImportError:
        return show_error_message_box(message, title)
    else:
        _get_tk_root()
        return messagebox.showerror(title, message, **options)


def askquestion(title: str, message: str, **options) -> str:
    try:
        from tkinter import messagebox
    except ImportError:
        response = show_yes_no_message_box(message, title)
        return "yes" if response == IDYES else "no"
    else:
        _get_tk_root()
        return messagebox.askquestion(title, message, **options)


def askokcancel(title: str, message: str, **options) -> bool:
    try:
        from tkinter import messagebox
    except ImportError:
        response = show_ok_message_box(message, title)
        return response == IDOK
    else:
        _get_tk_root()
        return messagebox.askokcancel(title, message, **options)


def askyesno(title: str, message: str, **options) -> bool:
    try:
        from tkinter import messagebox
    except ImportError:
        response = show_yes_no_message_box(message, title)
        return response == IDYES
    else:
        _get_tk_root()
        return messagebox.askyesno(title, message, **options)


def askyesnocancel(title: str, message: str, **options) -> bool | None:
    try:
        from tkinter import messagebox
    except ImportError:
        response = windows_message_box(message, title, MB_YESNOCANCEL, MB_ICONQUESTION)
        if response == IDYES:
            return True
        if response == IDNO:
            return False
        return None
    else:
        _get_tk_root()
        return messagebox.askyesnocancel(title, message, **options)


def askretrycancel(title: str, message: str, **options) -> bool:
    try:
        from tkinter import messagebox
    except ImportError:
        response = show_retry_cancel_message_box(message, title)
        return response == IDRETRY
    else:
        _get_tk_root()
        return messagebox.askretrycancel(title, message, **options)
