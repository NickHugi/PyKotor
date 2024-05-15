from __future__ import annotations

import tkinter as tk

from dataclasses import dataclass
from tkinter import messagebox, simpledialog

from utility.gui.base import UserCommunication


@dataclass
class TkUserCommunication(UserCommunication):
    def input(self, prompt: str) -> str:
        return simpledialog.askstring("Input", prompt, parent=self.widget) or ""

    def print(self, *args: str):
        messagebox.showinfo("Print Message", "    ".join(args))

    def messagebox(self, title: str, message: str):
        messagebox.showinfo(title, message)

    def askquestion(self, title: str, message: str) -> bool:
        return messagebox.askyesno(title, message)

    def update_status(self, message: str):
        if isinstance(self.widget, (tk.Tk, tk.Toplevel)):
            status_label = tk.Label(self.widget, text=message)
            status_label.pack()
