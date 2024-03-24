from __future__ import annotations

import contextlib
import tkinter as tk

from queue import Empty
from threading import Event, Thread
from tkinter import simpledialog, ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:

    from queue import Queue


def human_readable_size(byte_size: float) -> str:
    for unit in ["bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]:
        if byte_size < 1024:
            return f"{round(byte_size, 2)} {unit}"
        byte_size /= 1024
    return str(byte_size)

def dialog_thread_func(progress_queue, title):
    dialog = TkProgressDialog(progress_queue, title)
    dialog.check_queue()  # Make sure to call this to start the queue checking loop
    dialog.mainloop()

def run_tk_progress_dialog(progress_queue: Queue, title: str = "Operation Progress"):
    # Create and start the thread for the dialog
    dialog_thread = Thread(target=dialog_thread_func, args=(progress_queue, title), daemon=True)
    dialog_thread.start()
    return dialog_thread

class TkProgressDialog(tk.Tk):
    def __init__(self, progress_queue: Queue, title: str = "Operation Progress"):
        super().__init__()
        self.progress_queue: Queue = progress_queue
        self.title(title)

        self.status_label = tk.Label(self, text="Initializing...")
        self.status_label.pack(pady=(10,0))

        self.bytes_label = tk.Label(self, text="")
        self.bytes_label.pack()

        self.progress_bar = ttk.Progressbar(self, orient="horizontal", length=400, mode="determinate")
        self.progress_bar.pack(pady=(0,10))
        self.shutdown_event = Event()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        # Handle close event
        self.destroy()

    def check_queue(self):
        with contextlib.suppress(Empty):
            while True:
                try:
                    message = self.progress_queue.get_nowait()
                except Exception:  # noqa: S112
                    continue
                if message["action"] == "update_progress":
                    data = message["data"]
                    downloaded = data["downloaded"]
                    total = data["total"]
                    progress = int((downloaded / total) * 100) if total else 0
                    self.progress_bar["value"] = progress
                    self.status_label["text"] = f"Downloading... {progress}%"
                    self.bytes_label["text"] = f"{human_readable_size(downloaded)} / {human_readable_size(total)}"
                elif message["action"] == "update_status":
                    text = message["text"]
                    self.status_label["text"] = text
                elif message["action"] == "shutdown":
                    self.destroy()
                    return
                elif message["action"] == "starting":
                    data = message["data"]
                    self.status_label["text"] = "Starting download..."
                    self.bytes_label["text"] = f"-- / {human_readable_size(data['total'])}"
        self.after(100, self.check_queue)

    def update_status(self, text: str):
        self.status_label = tk.Label(self, text=text)


class UpdateDialog(simpledialog.Dialog):
    def __init__(self, parent: tk.Tk, title: str, text: str, options: list):
        self.text = text  # Store the message text
        self.options = options
        super().__init__(parent, title)

    def body(self, master):
        # Use the stored message text for the label
        tk.Label(master, text=self.text, wraplength=400).pack(pady=10)  # wraplength wraps the text if it's too long

    def buttonbox(self):
        box = tk.Frame(self)
        for option in self.options:
            btn = tk.Button(box, text=option, width=10, command=lambda opt=option: self.ok(opt))
            btn.pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(box, text="Cancel", width=10, command=self.cancel).pack(side=tk.LEFT, padx=5, pady=5)
        self.bind("<Return>", lambda _event, opt=self.options[0]: self.ok(opt))
        self.bind("<Escape>", self.cancel)
        box.pack()

    def apply(self):
        pass  # Override to do nothing on default OK press

    def ok(self, opt=None):
        self.result = opt
        super().ok()
