from __future__ import annotations

import os
import pathlib
import re
import sys
import tkinter as tk
from configparser import ConfigParser
from threading import Thread
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont
from typing import TYPE_CHECKING

# Ensure the directory of the script is in sys.path
script_dir = pathlib.Path(__file__).parent.resolve()
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))
from settings import setup_environment

setup_environment()

from pykotor.common.misc import Game
from pykotor.tools.path import CaseAwarePath, locate_game_path
from pykotor.tslpatcher.config import ModInstaller, PatcherNamespace
from pykotor.tslpatcher.logger import PatchLogger
from pykotor.tslpatcher.reader import NamespaceReader

if TYPE_CHECKING:
    from pathlib import Path


class LeftCutOffCombobox(ttk.Combobox):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)

        # Create a separate StringVar to control the display
        self.display_var = tk.StringVar()
        self["textvariable"] = self.display_var
        self.bind("<<ComboboxSelected>>", self.update_display_value)

        # Bind the postcommand to modify dropdown items' display
        self["postcommand"] = self.update_dropdown_display
        # Bind the <Unmap> event to restore the original values
        self.bind("<Unmap>", self.restore_original_values)
        self.bind("<FocusOut>", self.restore_original_values)

    def update_display_value(self, event=None):
        # Update the displayed value based on the actual value selected
        actual_value = self.get()
        display_value = actual_value

        # Estimate the width of the dropdown arrow. This may need tweaking based on the theme or style.
        arrow_width = 25  # This value may need adjustments based on the visual theme

        while self.font_measure(f"...{display_value}") > (self.winfo_width() - arrow_width):
            display_value = display_value[1:]

        if display_value != actual_value:
            self.display_var.set(f"...{display_value}")
        else:
            self.display_var.set(actual_value)

    def update_dropdown_display(self):
        # This method gets called just before the dropdown is displayed
        # Temporarily set the values for display
        display_values = [self.truncate_text(item) for item in self["values"]]
        super().configure(values=display_values)

    def restore_original_values(self, event=None):
        # Restore the original values after the dropdown has been closed
        super().configure(values=self["values"])

    def truncate_text(self, text):
        available_space = self.winfo_width() - 25  # subtract estimated arrow width
        while self.font_measure(f"...{text}") > available_space:
            text = text[1:]
        return f"...{text}" if text != self.get() else text

    def font_measure(self, text):
        return tkfont.Font(font=self.cget("font")).measure(text)

    def font_average_width(self):
        return self.font_measure("m")


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

        self.gamepaths = ttk.Combobox(self)
        self.gamepaths.place(x=5, y=35, width=310, height=25)
        self.default_game_paths = locate_game_path()
        self.gamepaths["values"] = [
            str(path) for path in (self.default_game_paths[Game.K1] + self.default_game_paths[Game.K2]) if path.exists()
        ]

        self.description_text = tk.Text(self, state="disabled", wrap="none")
        self.description_text.place(x=5, y=65, width=390, height=400)

        ttk.Button(self, text="Browse", command=self.open_mod).place(x=320, y=5, width=75, height=25)
        ttk.Button(self, text="...", command=self.open_kotor).place(x=320, y=35, width=75, height=25)
        ttk.Button(self, text="Install", command=self.begin_install).place(x=5, y=470, width=75, height=25)
        ttk.Progressbar(self).place(x=85, y=470, width=310, height=25)

        self.open_mod(CaseAwarePath.cwd())

    def extract_lookup_game_number(self, changes_path: Path):
        if not changes_path.exists():
            return None
        pattern = r"LookupGameNumber=(\d+)"
        with changes_path.open("r", encoding="utf-8") as file:
            for line in file:
                match = re.search(pattern, line)
                if match:
                    return int(match[1])
        return None

    def open_mod(self, default_directory_path_str: os.PathLike | str | None = None) -> None:
        try:
            directory_path_str = default_directory_path_str or filedialog.askdirectory()
            if not directory_path_str:
                return

            self.mod_path = directory_path_str

            tslpatchdata_path = CaseAwarePath(directory_path_str, "tslpatchdata")
            # handle when a user selects 'tslpatchdata' instead of mod root
            if not tslpatchdata_path.exists() and tslpatchdata_path.parent.name.lower() == "tslpatchdata":
                tslpatchdata_path = tslpatchdata_path.parent
                self.mod_path = str(tslpatchdata_path.parent)

            namespace_path = tslpatchdata_path / "namespaces.ini"
            changes_path = tslpatchdata_path / "changes.ini"

            if namespace_path.exists():
                namespaces = NamespaceReader.from_filepath(namespace_path)
                self.load_namespace(namespaces)
            elif changes_path.exists():
                namespaces = self.build_changes_as_namespace(changes_path)
                self.load_namespace([namespaces])
            else:
                self.mod_path = ""
                if not default_directory_path_str:  # don't show the error if the cwd was attempted
                    messagebox.showerror("Error", "Could not find a mod located at the given folder.")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred while loading mod info: {e}")

    def open_kotor(self) -> None:
        directory_path_str = filedialog.askdirectory()
        if not directory_path_str:
            return
        directory = CaseAwarePath(directory_path_str)

        # handle possibility of user selecting a nested folder within KOTOR dir (usually override)
        # TODO: double check if chitin.key exists on mac/mobile versions.
        while (
            directory.parent.name
            and directory.parent.name != directory.parts[1]
            and not directory.joinpath("chitin.key").exists()
        ):
            directory = directory.parent
        if not directory.joinpath("chitin.key").exists():
            messagebox.showerror("Invalid KOTOR directory", "Select a valid KOTOR installation.")
            return
        self.gamepaths["values"] = [str(directory)]

    def begin_install(self) -> None:
        try:
            Thread(target=self.begin_install_thread).start()
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"An unexpected error occurred during the installation and the program was forced to exit: {e}",
            )

    def begin_install_thread(self):
        if not self.mod_path:
            messagebox.showinfo("No mod chosen", "Select your mod directory before starting an install")
            return
        game_path = self.gamepaths.get()
        if not game_path:
            messagebox.showinfo("No KOTOR directory chosen", "Select your KOTOR install before starting an install.")
            return

        tslpatchdata_root_path = CaseAwarePath(self.mod_path, "tslpatchdata")
        namespace_option = next(x for x in self.namespaces if x.name == self.namespaces_combobox.get())
        ini_file_path = (
            tslpatchdata_root_path.joinpath(
                namespace_option.data_folderpath,
                namespace_option.ini_filename,
            )
            if namespace_option.data_folderpath
            else tslpatchdata_root_path.joinpath(
                namespace_option.ini_filename,
            )
        )
        mod_path = ini_file_path.parent

        self.description_text.delete(0, tk.END)

        installer = ModInstaller(mod_path, game_path, ini_file_path, self.logger)
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
            namespace.name = ini.get("Settings", "WindowCaption", fallback="default")

        return namespace

    def load_namespace(self, namespaces: list[PatcherNamespace]) -> None:
        self.namespaces_combobox["values"] = namespaces
        self.namespaces_combobox.set(self.namespaces_combobox["values"][0])
        self.namespaces = namespaces
        namespace_option = next(x for x in self.namespaces if x.name == self.namespaces_combobox.get())
        game_number: int | None
        if namespace_option.data_folderpath:
            game_number = self.extract_lookup_game_number(
                CaseAwarePath(self.mod_path, "tslpatchdata", namespace_option.data_folderpath, namespace_option.ini_filename),
            )
        else:
            game_number = self.extract_lookup_game_number(
                CaseAwarePath(self.mod_path, "tslpatchdata", namespace_option.ini_filename),
            )
        if game_number:
            game = Game(game_number)
            prechosen_gamepath = self.gamepaths.get()
            self.gamepaths["values"] = [str(path) for path in self.default_game_paths[game] if path.exists()]
            if prechosen_gamepath in self.gamepaths["values"]:
                self.gamepaths.set(prechosen_gamepath)
            else:
                self.gamepaths.set("")

    def write_log(self, message: str) -> None:
        self.description_text.config(state="normal")
        self.description_text.insert(tk.END, message + os.linesep)
        self.description_text.see(tk.END)
        self.description_text.config(state="disabled")


def main():
    app = App()
    app.mainloop()


main()
