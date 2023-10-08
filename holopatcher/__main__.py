from __future__ import annotations

import os
import sys
import tkinter as tk
from configparser import ConfigParser
from threading import Thread
from tkinter import filedialog, messagebox, ttk


def is_debugging() -> bool:
    # Check if being debugged in popular IDEs. From stackoverflow.
    return any(
        [
            bool(getattr(sys, "_MEIPASS", False)),
            bool(getattr(sys, "gettrace", None)),
            "__pydevd__" in sys.modules,
            "pydevconsole" in sys.modules,
            "vscodedebugpy" in sys.modules,
        ],
    )


# Append parent paths for debugging support.
if is_debugging():
    sys.path.append(".")
    sys.path.append("..")

from pykotor.tools.path import CaseAwarePath
from pykotor.tslpatcher.config import ModInstaller, PatcherNamespace
from pykotor.tslpatcher.logger import PatchLogger
from pykotor.tslpatcher.reader import NamespaceReader


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry("400x500")
        self.resizable(width=False, height=False)
        self.title("HoloPatcher")

        self.mod_path = ""
        self.namespaces = []

        self.logger = PatchLogger()
        self.logger.verbose_observable.subscribe(self.write_log)
        self.logger.note_observable.subscribe(self.write_log)
        self.logger.warning_observable.subscribe(self.write_log)
        self.logger.error_observable.subscribe(self.write_log)

        self.namespaces_combobox = ttk.Combobox(self, state="readonly")
        self.namespaces_combobox.place(x=5, y=5, width=310, height=25)

        self.gamepath_entry = ttk.Entry(self)
        self.gamepath_entry.place(x=5, y=35, width=310, height=25)

        self.description_text = tk.Text(self, state="disabled", wrap="none")
        self.description_text.place(x=5, y=65, width=390, height=400)

        ttk.Button(self, text="Browse", command=self.open_mod).place(x=320, y=5, width=75, height=25)
        ttk.Button(self, text="...", command=self.open_kotor).place(x=320, y=35, width=75, height=25)
        ttk.Button(self, text="Install", command=self.begin_install).place(x=5, y=470, width=75, height=25)
        ttk.Progressbar(self).place(x=85, y=470, width=310, height=25)

        self.open_mod(CaseAwarePath.cwd())

    def open_mod(self, default_directory_path_str: os.PathLike | str | None = None) -> None:
        directory_path_str = default_directory_path_str or filedialog.askdirectory()
        self.mod_path = directory_path_str

        namespace_path = CaseAwarePath(directory_path_str, "tslpatchdata", "namespaces.ini")
        changes_path = CaseAwarePath(directory_path_str, "tslpatchdata", "changes.ini")

        try:
            if namespace_path.exists():
                namespaces = NamespaceReader.from_filepath(namespace_path)
                self.load_namespace(namespaces)
            elif changes_path.exists():
                namespaces = self.build_changes_as_namespace(changes_path)
                self.load_namespace([namespaces])
            elif not default_directory_path_str:
                messagebox.showerror("Error", "Could not find a mod located at the given folder.")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred while loading mod info: {e}")

    def open_kotor(self) -> None:
        directory = CaseAwarePath(filedialog.askdirectory())

        # handle possibility of user selecting a nested folder within KOTOR dir (usually override)
        # TODO: double check if chitin.key exists on mac/mobile versions.
        while (
            directory.parent.name
            and directory.parent.name != directory.parts[1]
            and not directory.joinpath("chitin.key").exists()
        ):
            directory = directory.parent
        self.gamepath_entry.delete(0, tk.END)
        self.gamepath_entry.insert(0, str(directory))

    def begin_install(self) -> None:
        try:
            Thread(target=self.begin_install_thread).start()
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"An unexpected error occurred during the installation and the program was forced to exit: {e}",
            )

    def begin_install_thread(self):
        mod_path = CaseAwarePath(self.mod_path, "tslpatchdata")
        game_path = self.gamepath_entry.get()
        ini_file = next(x for x in self.namespaces if x.name == self.namespaces_combobox.get()).ini_filename

        self.description_text.delete(0, tk.END)

        installer = ModInstaller(mod_path, game_path, ini_file, self.logger)
        installer.install()

    def build_changes_as_namespace(self, filepath: os.PathLike | str) -> PatcherNamespace:
        c_filepath = CaseAwarePath(filepath)
        with c_filepath.open() as file:
            ini = ConfigParser(
                delimiters=("="),
                allow_no_value=True,
                strict=False,
                interpolation=None,
            )
            ini.optionxform = lambda optionstr: optionstr  # use case sensitive keys
            ini.read_string(file.read())

            namespace = PatcherNamespace()
            namespace.ini_filename = "changes.ini"
            namespace.info_filename = "info.rtf"
            namespace.name = ini.get("Settings", "WindowCaption")

        return namespace

    def load_namespace(self, namespaces: list[PatcherNamespace]) -> None:
        self.namespaces_combobox["values"] = namespaces
        self.namespaces_combobox.set(self.namespaces_combobox["values"][0])
        self.namespaces = namespaces

    def write_log(self, message: str) -> None:
        self.description_text.config(state="normal")
        self.description_text.insert(tk.END, message + os.linesep)
        self.description_text.see(tk.END)
        self.description_text.config(state="disabled")


def main():
    app = App()
    while True:
        app.mainloop()


main()
