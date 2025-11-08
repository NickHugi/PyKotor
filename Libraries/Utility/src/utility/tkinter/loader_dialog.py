from __future__ import annotations

import threading
import tkinter as tk

from tkinter import ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Literal


class LoadingDialog(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Tk,
        title: str = "Loading",
        bounce_speed: int | Literal["idle"] | None = None,
        pb_length: int = 200,
        func: Callable | None = None,
    ):
        super().__init__(parent)

        # Set basic window properties
        self.title(title)
        self.geometry("300x100")
        self.transient(parent)
        self.grab_set()

        # Message label
        self.msg_lbl: tk.Label = tk.Label(self, text="Please wait...")
        self.msg_lbl.pack(padx=10, pady=5)

        # Progress bar
        self.load_bar: ttk.Progressbar = ttk.Progressbar(self, mode="indeterminate", maximum=100, value=0, length=pb_length)
        self.load_bar.pack(padx=10, pady=(0, 10))
        self.load_bar.start(bounce_speed)

        # Function to execute
        self.func: Callable | None = func

        # Start work in a new thread
        self.start_work_thread()

    def start_work_thread(self):
        if self.func is not None:
            self.work_thread = threading.Thread(target=self.work_task, name="LoadingDialog_worker_thread")
            self.work_thread.start()

    def work_task(self):
        if self.func is not None:
            self.func()
        # Stop progress bar and close dialog after work is done
        self.load_bar.stop()
        self.destroy()
