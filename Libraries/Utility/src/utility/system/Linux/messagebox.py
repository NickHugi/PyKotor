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


def showinfo(title: str, message: str):
    try:
        from tkinter import messagebox
        _get_tk_root()
        return messagebox.showinfo(title, message)
    except Exception:  # noqa: BLE001
        try:
            subprocess.run(["zenity", "--info", "--title", title, "--text", message], check=True)  # noqa: S603, S607
        except subprocess.CalledProcessError:
            try:
                subprocess.run(["yad", "--info", "--title", title, "--text", message], check=True)  # noqa: S603, S607
            except subprocess.CalledProcessError:
                subprocess.run(["gtk-message-dialog", "--type=info", "--title", title, "--text", message], check=True)  # noqa: S603, S607


def showwarning(title: str, message: str):
    try:
        from tkinter import messagebox
        _get_tk_root()
        return messagebox.showwarning(title, message)
    except Exception:  # noqa: BLE001
        try:
            subprocess.run(["zenity", "--warning", "--title", title, "--text", message], check=True)  # noqa: S603, S607
        except subprocess.CalledProcessError:
            try:
                subprocess.run(["yad", "--warning", "--title", title, "--text", message], check=True)  # noqa: S603, S607
            except subprocess.CalledProcessError:
                subprocess.run(["gtk-message-dialog", "--type=warning", "--title", title, "--text", message], check=True)  # noqa: S603, S607


def showerror(title: str, message: str):
    try:
        from tkinter import messagebox
        _get_tk_root()
        return messagebox.showerror(title, message)
    except Exception:  # noqa: BLE001
        try:
            subprocess.run(["zenity", "--error", "--title", title, "--text", message], check=True)  # noqa: S603, S607
        except subprocess.CalledProcessError:
            try:
                subprocess.run(["yad", "--error", "--title", title, "--text", message], check=True)  # noqa: S603, S607
            except subprocess.CalledProcessError:
                subprocess.run(["gtk-message-dialog", "--type=error", "--title", title, "--text", message], check=True)  # noqa: S603, S607


def askquestion(title: str, message: str) -> str:
    try:
        from tkinter import messagebox
        _get_tk_root()
        return messagebox.askquestion(title, message)
    except Exception:  # noqa: BLE001
        try:
            result = subprocess.run(["zenity", "--question", "--title", title, "--text", message], check=True)  # noqa: S603, S607
            return "yes" if result.returncode == 0 else "no"  # noqa: TRY300
        except subprocess.CalledProcessError:
            try:
                result = subprocess.run(["yad", "--question", "--title", title, "--text", message], check=True)  # noqa: S603, S607
                return "yes" if result.returncode == 0 else "no" "no"  # noqa: TRY300
            except subprocess.CalledProcessError:
                result = subprocess.run(["gtk-message-dialog", "--type=question", "--title", title, "--text", message], check=True)  # noqa: S603, S607
                return "yes" if result.returncode == 0 else "no"


def askokcancel(title: str, message: str) -> bool:
    try:
        from tkinter import messagebox
        _get_tk_root()
        return messagebox.askokcancel(title, message)
    except Exception:  # noqa: BLE001
        try:
            result = subprocess.run(["zenity", "--question", "--ok-label=OK", "--cancel-label=Cancel", "--title", title, "--text", message], check=True)  # noqa: S603, S607
            return result.returncode == 0  # noqa: TRY300
        except subprocess.CalledProcessError:
            try:
                result = subprocess.run(["yad", "--question", "--button=OK:0", "--button=Cancel:1", "--title", title, "--text", message], check=True)  # noqa: S603, S607
                return result.returncode == 0  # noqa: TRY300
            except subprocess.CalledProcessError:
                result = subprocess.run(["gtk-message-dialog", "--type=question", "--title", title, "--text", message], check=True)  # noqa: S603, S607
                return result.returncode == 0


def askyesno(title: str, message: str) -> bool:
    try:

        from tkinter import messagebox
        _get_tk_root()
        return messagebox.askyesno(title, message)
    except Exception:  # noqa: BLE001
        try:
            result = subprocess.run(["zenity", "--question", "--title", title, "--text", message], check=True)  # noqa: S603, S607
            return result.returncode == 0  # noqa: TRY300
        except subprocess.CalledProcessError:
            try:
                result = subprocess.run(["yad", "--question", "--button=Yes:0", "--button=No:1", "--title", title, "--text", message], check=True)  # noqa: S603, S607
                return result.returncode == 0  # noqa: TRY300
            except subprocess.CalledProcessError:
                result = subprocess.run(["gtk-message-dialog", "--type=question", "--title", title, "--text", message], check=True)  # noqa: S603, S607
                return result.returncode == 0


def askyesnocancel(title: str, message: str) -> bool | None:
    try:

        from tkinter import messagebox
        _get_tk_root()
        return messagebox.askyesnocancel(title, message)
    except Exception:  # noqa: BLE001
        try:
            result = subprocess.run(["zenity", "--question", "--extra-button=Cancel", "--title", title, "--text", message], check=True)  # noqa: S603, S607
            if result.returncode == 0:
                return True
            if result.returncode == 1:
                return False
            return None  # noqa: TRY300
        except subprocess.CalledProcessError:
            try:
                result = subprocess.run(["yad", "--question", "--button=Yes:0", "--button=No:1", "--button=Cancel:2", "--title", title, "--text", message], check=True)  # noqa: S603, S607
                if result.returncode == 0:
                    return True
                if result.returncode == 1:
                    return False
                return None  # noqa: TRY300
            except subprocess.CalledProcessError:
                result = subprocess.run(["gtk-message-dialog", "--type=question", "--title", title, "--text", message, "--buttons=yes-no-cancel"], check=True)  # noqa: S603, S607
                if result.returncode == 0:
                    return True
                if result.returncode == 1:
                    return False
                return None


def askretrycancel(title: str, message: str) -> bool:
    try:
        from tkinter import messagebox
        _get_tk_root()
        return messagebox.askretrycancel(title, message)
    except Exception:  # noqa: BLE001
        try:
            result = subprocess.run(["zenity", "--question", "--ok-label=Retry", "--cancel-label=Cancel", "--title", title, "--text", message], check=True)  # noqa: S603, S607
            return result.returncode == 0  # noqa: TRY300
        except subprocess.CalledProcessError:
            try:
                result = subprocess.run(["yad", "--question", "--button=Retry:0", "--button=Cancel:1", "--title", title, "--text", message], check=True)  # noqa: S603, S607
                return result.returncode == 0  # noqa: TRY300
            except subprocess.CalledProcessError:
                result = subprocess.run(["gtk-message-dialog", "--type=question", "--title", title, "--text", message], check=True)  # noqa: S603, S607
                return result.returncode == 0
