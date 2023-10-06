import os
from configparser import ConfigParser
from threading import Thread
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from typing import List
from tkinter.messagebox import showerror, showwarning, showinfo

from pykotor.tools.path import CaseAwarePath
from pykotor.tslpatcher.config import PatcherNamespace, ModInstaller
from pykotor.tslpatcher.logger import PatchLogger
from pykotor.tslpatcher.reader import NamespaceReader


class App(Tk):
    def __init__(self):
        super().__init__()
        self.geometry("400x500")
        self.resizable(False, False)

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

        self.description_text = Text(self, state="disabled", wrap="none")
        self.description_text.place(x=5, y=65, width=390, height=400)

        ttk.Button(self, text="Browse", command=self.open_mod).place(x=320, y=5, width=75, height=25)
        ttk.Button(self, text="...", command=self.open_kotor).place(x=320, y=35, width=75, height=25)
        ttk.Button(self, text="Install", command=self.begin_install).place(x=5, y=470, width=75, height=25)
        ttk.Progressbar(self).place(x=85, y=470, width=310, height=25)

    def open_mod(self) -> None:
        directory = CaseAwarePath(filedialog.askdirectory())
        self.mod_path = directory

        namespace_path = directory / "tslpatchdata" / "namespaces.ini"
        changes_path = directory / "tslpatchdata" / "changes.ini"

        try:
            if os.path.exists(namespace_path):
                namespaces = NamespaceReader.from_filepath(namespace_path)
                self.load_namespace(namespaces)
            elif os.path.exists(changes_path):
                namespaces = self.build_changes_as_namespace(changes_path)
                self.load_namespace([namespaces])
            else:
                showerror("Error", "Could not find a mod located at the given folder.")
        except Exception as e:
            showerror("Error", "An unknown error occured loading the mod info.")

    def open_kotor(self) -> None:
        directory = CaseAwarePath(filedialog.askdirectory())
        self.gamepath_entry.delete(0, END)
        self.gamepath_entry.insert(0, directory)

    def begin_install(self) -> None:
        try:
            Thread(target=self.begin_install_thread).start()
        except Exception as e:
            showerror("Error", "An unknown error occured during the installation and the program was forced to exit.")

    def begin_install_thread(self):
        mod_path = CaseAwarePath(self.mod_path) / "tslpatchdata"
        game_path = CaseAwarePath(self.gamepath_entry.get())
        ini_file = [x for x in self.namespaces if x.name == self.namespaces_combobox.get()][0].ini_filename

        self.description_text.delete(0, END)

        installer = ModInstaller(mod_path, game_path, ini_file, self.logger)
        installer.install()

    def build_changes_as_namespace(self, filepath: os.PathLike) -> PatcherNamespace:
        with open(filepath, 'r') as file:
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

    def load_namespace(self, namespaces: List[PatcherNamespace]) -> None:
        self.namespaces_combobox['values'] = namespaces
        self.namespaces_combobox.set(self.namespaces_combobox['values'][0])
        self.namespaces = namespaces

    def write_log(self, message: str) -> None:
        self.description_text.config(state="normal")
        self.description_text.insert(END, message + "\n")
        self.description_text.see(END)
        self.description_text.config(state="disabled")


def main():
    app = App()
    while True:
        app.mainloop()


main()
