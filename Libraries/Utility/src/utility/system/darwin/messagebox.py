from __future__ import annotations

import subprocess

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import tkinter as tk  # Do not import tkinter-related outside type-checking blocks, in case not installed.


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
        try:
            subprocess.run(
                ["cocoaDialog", "msgbox", "--title", title, "--text", message, "--informative-text", "", "--button1", "OK"],  # noqa: S603, S607
                check=True,
            )
        except subprocess.CalledProcessError:
            subprocess.run(
                ["osascript", "-e", f'display dialog "{message}" with title "{title}" buttons {{"OK"}} default button "OK"'],  # noqa: S603, S607
                check=True,
            )
    else:
        _get_tk_root()
        messagebox.showinfo(title, message, **options)


def showwarning(title: str, message: str, **options):
    try:
        from tkinter import messagebox
    except ImportError:
        try:
            subprocess.run(
                ["cocoaDialog", "msgbox", "--title", title, "--text", message, "--informative-text", "", "--button1", "OK", "--icon", "caution"],  # noqa: S603, S607
                check=True,
            )
        except subprocess.CalledProcessError:
            subprocess.run(
                ["osascript", "-e", f'display dialog "{message}" with title "{title}" buttons {{"OK"}} default button "OK" with icon caution'],  # noqa: S603, S607
                check=True,
            )
    else:
        _get_tk_root()
        messagebox.showwarning(title, message, **options)


def showerror(title: str, message: str, **options):
    try:
        from tkinter import messagebox
    except ImportError:
        try:
            subprocess.run(
                ["cocoaDialog", "msgbox", "--title", title, "--text", message, "--informative-text", "", "--button1", "OK", "--icon", "stop"],  # noqa: S603, S607
                check=True,
            )
        except subprocess.CalledProcessError:
            subprocess.run(
                ["osascript", "-e", f'display dialog "{message}" with title "{title}" buttons {{"OK"}} default button "OK" with icon stop'],  # noqa: S603, S607
                check=True,
            )
    else:
        _get_tk_root()
        messagebox.showerror(title, message, **options)


def askquestion(title: str, message: str, **options) -> str:
    try:
        from tkinter import messagebox
    except ImportError:
        try:
            result = subprocess.run(
                ["cocoaDialog", "yesno-msgbox", "--title", title, "--text", message, "--informative-text", ""],  # noqa: S603, S607
                check=True,
            )
            return "yes" if result.returncode == 0 else "no"  # noqa: TRY300
        except subprocess.CalledProcessError:
            result = subprocess.run(
                ["osascript", "-e", f'display dialog "{message}" with title "{title}" buttons {{"Yes", "No"}} default button "Yes"'],  # noqa: S603, S607
                check=True,
                capture_output=True,
            )
            return "button returned:Yes" in result.stdout.decode() and "yes" or "no"
    else:
        _get_tk_root()
        return messagebox.askquestion(title, message, **options)


def askokcancel(title: str, message: str, **options) -> bool:
    try:
        from tkinter import messagebox
    except ImportError:
        try:
            result = subprocess.run(
                ["cocoaDialog", "ok-msgbox", "--title", title, "--text", message, "--informative-text", ""],  # noqa: S603, S607
                check=True,
            )
            return result.returncode == 0  # noqa: TRY300
        except subprocess.CalledProcessError:
            result = subprocess.run(
                ["osascript", "-e", f'display dialog "{message}" with title "{title}" buttons {{"OK", "Cancel"}} default button "OK"'],  # noqa: S603, S607
                check=True,
                capture_output=True,
            )
            return "button returned:OK" in result.stdout.decode()
    else:
        _get_tk_root()
        return messagebox.askokcancel(title, message, **options)


def askyesno(title: str, message: str, **options) -> bool:
    try:
        from tkinter import messagebox
    except ImportError:
        try:
            result = subprocess.run(
                ["cocoaDialog", "yesno-msgbox", "--title", title, "--text", message, "--informative-text", ""],  # noqa: S603, S607
                check=True,
            )
            return result.returncode == 0  # noqa: TRY300
        except subprocess.CalledProcessError:
            result = subprocess.run(
                ["osascript", "-e", f'display dialog "{message}" with title "{title}" buttons {{"Yes", "No"}} default button "Yes"'],  # noqa: S603, S607
                check=True,
                capture_output=True,
            )
            return "button returned:Yes" in result.stdout.decode()
    else:
        _get_tk_root()
        return messagebox.askyesno(title, message, **options)


def askyesnocancel(title: str, message: str, **options) -> bool | None:
    try:
        from tkinter import messagebox
    except ImportError:
        try:
            result = subprocess.run(
                ["cocoaDialog", "yesno-msgbox", "--title", title, "--text", message, "--informative-text", "", "--button1", "Yes", "--button2", "No", "--button3", "Cancel"],  # noqa: S603, S607
                check=True,
            )
            if result.returncode == 0:
                return True
            if result.returncode == 1:
                return False
            return None  # noqa: TRY300
        except subprocess.CalledProcessError:
            result = subprocess.run(
                ["osascript", "-e", f'display dialog "{message}" with title "{title}" buttons {{"Yes", "No", "Cancel"}} default button "Yes"'],  # noqa: S603, S607
                check=True,
                capture_output=True,
            )
            if "button returned:Yes" in result.stdout.decode():
                return True
            if "button returned:No" in result.stdout.decode():
                return False
            return None
    else:
        _get_tk_root()
        return messagebox.askyesnocancel(title, message, **options)


def askretrycancel(title: str, message: str, **options) -> bool:
    try:
        from tkinter import messagebox
    except ImportError:
        try:
            result = subprocess.run(
                ["cocoaDialog", "msgbox", "--title", title, "--text", message, "--informative-text", "", "--button1", "Retry", "--button2", "Cancel"],  # noqa: S603, S607
                check=True,
            )
            return result.returncode == 0  # noqa: TRY300
        except subprocess.CalledProcessError:
            result = subprocess.run(
                ["osascript", "-e", f'display dialog "{message}" with title "{title}" buttons {{"Retry", "Cancel"}} default button "Retry"'],  # noqa: S603, S607
                check=True,
            )
            return result.returncode == 0
    else:
        _get_tk_root()
        return messagebox.askretrycancel(title, message, **options)
