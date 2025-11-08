from __future__ import annotations

import tkinter as tk

from contextlib import suppress
from multiprocessing import Process
from queue import Empty
from tkinter import simpledialog, ttk
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from multiprocessing import Queue


def human_readable_size(byte_size: float) -> str:
    with suppress(Exception):
        for unit in ["bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]:
            if byte_size < 1024:
                return f"{round(byte_size, 2)} {unit}"
            byte_size /= 1024
    return str(byte_size)

def run_tk_progress_dialog(progress_queue: Queue, title: str = "Operation Progress") -> Process:
    p = Process(target=dialog_thread_func, args=(progress_queue, title))
    p.start()
    return p  # Return the process if you need to interact with it later (e.g., join or terminate)

def dialog_thread_func(progress_queue: Queue, title: str):
    dialog = TkProgressDialog(progress_queue, title)
    dialog.check_queue()
    dialog.mainloop()

class TkProgressDialog(tk.Tk):
    def __init__(self, progress_queue: Queue, title: str = "Operation Progress"):
        super().__init__()
        self.progress_queue: Queue = progress_queue
        self.title(title)

        self.status_label: tk.Label = tk.Label(self, text="Initializing...")
        self.status_label.pack(pady=(10,0))

        self.bytes_label: tk.Label = tk.Label(self, text="")
        self.bytes_label.pack()

        self.time_left: tk.Label = tk.Label(self, text="--:--")
        self.time_left.pack()

        self.progress_bar: ttk.Progressbar = ttk.Progressbar(self, orient="horizontal", length=400, mode="determinate")
        self.progress_bar.pack(pady=(0,10))

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        self.destroy()

    def check_queue(self):
        with suppress(Empty):
            try:
                message = self.progress_queue.get_nowait()
            except Exception:  # noqa: S112, BLE001
                return
            if message["action"] == "update_progress":
                data: dict[str, Any] = message["data"]
                downloaded = data["downloaded"]
                total = data["total"]
                progress = int((downloaded / total) * 100) if total else 0
                self.progress_bar["value"] = progress
                self.status_label["text"] = f"Downloading... {progress}%"
                self.bytes_label["text"] = f"{human_readable_size(downloaded)} / {human_readable_size(total)}"
                time_left = data.get("time")
                if time_left:
                    self.time_left["text"] = time_left
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

    @staticmethod
    def monitor_and_terminate(process: Process, timeout: int = 5):
        """Monitor and forcefully terminate if this doesn't exit gracefully."""
        process.join(timeout)    # Wait for the process to terminate for 'timeout' seconds
        if process.is_alive():   # Check if the process is still alive
            process.terminate()  # Forcefully terminate the process
            process.join()       # Wait for the process to terminate


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
        self.bind("<Return>", lambda _event=None, opt=self.options[0]: self.ok(opt))
        self.bind("<Escape>", self.cancel)
        box.pack()

    def apply(self):
        pass  # Override to do nothing on default OK press

    def ok(self, opt=None):
        self.result = opt
        super().ok()
