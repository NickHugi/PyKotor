from __future__ import annotations

import os
import re
import sys
import tkinter as tk
import traceback
from configparser import ConfigParser
from pathlib import Path
from threading import Thread
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont

if not getattr(sys, "frozen", False):
    thisfile_path = Path(__file__).resolve()
    sys.path.append(str(thisfile_path.parent.parent.parent))

from pykotor.common.misc import CaseInsensitiveDict, Game
from pykotor.tools.path import CaseAwarePath, locate_game_path
from pykotor.tslpatcher.config import ModInstaller, PatcherNamespace
from pykotor.tslpatcher.logger import PatchLogger
from pykotor.tslpatcher.reader import NamespaceReader


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
        # Set window dimensions
        window_width = 400
        window_height = 500

        # Get screen dimensions
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # Calculate position to center the window
        x_position = int((screen_width / 2) - (window_width / 2))
        y_position = int((screen_height / 2) - (window_height / 2))

        # Set the dimensions and position
        self.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
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
        self.namespaces_combobox.set("Select the mod to install")
        self.namespaces_combobox.place(x=5, y=5, width=310, height=25)
        self.namespaces_combobox.bind("<<ComboboxSelected>>", self.on_namespace_option_chosen)

        self.browse_button = ttk.Button(self, text="Browse", command=self.open_mod)
        self.browse_button.place(x=320, y=5, width=75, height=25)

        self.gamepaths = ttk.Combobox(self)
        self.gamepaths.set("Select your KOTOR directory path")
        self.gamepaths.place(x=5, y=35, width=310, height=25)
        self.default_game_paths = locate_game_path()
        self.gamepaths["values"] = [
            str(path) for path in (self.default_game_paths[Game.K1] + self.default_game_paths[Game.K2]) if path.exists()
        ]
        self.gamepaths.bind("<<ComboboxSelected>>", self.on_gamepaths_chosen)
        ttk.Button(self, text="Browse", command=self.open_kotor).place(x=320, y=35, width=75, height=25)

        # Create a Frame to hold the Text and Scrollbar widgets
        text_frame = tk.Frame(self)
        text_frame.place(x=5, y=65, width=390, height=400)

        # Create the Scrollbar and pack it to the right side of the Frame
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create the Text widget with word wrapping and pack it to the left side of the Frame
        self.description_text = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set)
        self.description_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        # Link the Scrollbar to the Text widget
        scrollbar.config(command=self.description_text.yview)

        ttk.Button(self, text="Exit", command=lambda: sys.exit(0)).place(x=5, y=470, width=75, height=25)
        self.progressbar = ttk.Progressbar(self)
        self.progressbar.place(x=85, y=470, width=230, height=25)
        ttk.Button(self, text="Install", command=self.begin_install).place(x=320, y=470, width=75, height=25)

        self.open_mod(CaseAwarePath.cwd())

    def on_gamepaths_chosen(self, event):
        self.after(10, self.move_cursor_to_end)

    def move_cursor_to_end(self):
        self.gamepaths.focus_set()
        self.gamepaths.icursor(tk.END)
        self.gamepaths.xview(tk.END)

    def on_namespace_option_chosen(self, event):
        try:
            namespace_option = next(x for x in self.namespaces if x.name == self.namespaces_combobox.get())
            if namespace_option.data_folderpath:
                changes_ini_path = CaseAwarePath(
                    self.mod_path,
                    "tslpatchdata",
                    namespace_option.data_folderpath,
                    namespace_option.ini_filename,
                )
            else:
                changes_ini_path = CaseAwarePath(self.mod_path, "tslpatchdata", namespace_option.ini_filename)
            with changes_ini_path.parent.joinpath("info.rtf").open("r") as rtf:
                self.set_stripped_rtf_text(rtf)
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred while loading namespace option: {e}")

    def extract_lookup_game_number(self, changes_path: Path):
        if not changes_path.exists():
            return None
        pattern = r"LookupGameNumber=(\d+)"
        with changes_path.open("r", encoding="utf-8") as file:
            for line in file:
                match = re.search(pattern, line, re.IGNORECASE)
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
                if default_directory_path_str:
                    self.browse_button.place_forget()
            elif changes_path.exists():
                namespaces = self.build_changes_as_namespace(changes_path)
                self.load_namespace([namespaces])
                if default_directory_path_str:
                    self.browse_button.place_forget()
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
        while (
            directory.parent.name
            and directory.parent.name != directory.parts[1]
            and not directory.joinpath("chitin.key").exists()
        ):
            directory = directory.parent
        if not directory.joinpath("chitin.key").exists():
            messagebox.showerror("Invalid KOTOR directory", "Select a valid KOTOR installation.")
            return
        self.gamepaths.set(str(directory))
        self.after(10, self.move_cursor_to_end)

    def begin_install(self) -> None:
        try:
            Thread(target=self.begin_install_thread).start()
        except Exception as e:
            error_type = type(e).__name__
            error_args = e.args
            error_cause = type(e.__cause__).__name__ if e.__cause__ else "None"

            error_message = f"Exception Type: {error_type}\nException Arguments: {error_args}\nOriginal Exception: {error_cause}"

            messagebox.showerror(
                "Error",
                f"An unexpected error occurred during the installation and the program was forced to exit:\n{error_message}",
            )
            sys.exit(1)

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

        self.description_text.config(state="normal")
        self.description_text.delete(1.0, tk.END)
        self.description_text.config(state="disabled")

        installer = ModInstaller(mod_path, game_path, ini_file_path, self.logger)
        try:
            self._execute_mod_install(installer, tslpatchdata_root_path)
        except Exception as e:
            self._handle_exception_during_install(
                e,
                installer,
                tslpatchdata_root_path,
            )

    def _execute_mod_install(self, installer: ModInstaller, tslpatchdata_root_path: CaseAwarePath):
        installer.install()
        installer.log.add_note(
            f"The installation is complete with {len(installer.log.errors)} errors and {len(installer.log.warnings)} warnings",
        )
        self.progressbar["value"] = 100
        log_file_path: CaseAwarePath = tslpatchdata_root_path.parent / "installlog.txt"
        with log_file_path.open("w", encoding="utf-8") as log_file:
            for log in installer.log.all_logs:
                log_file.write(f"{log.message}\n")
        if len(installer.log.errors) > 0:
            messagebox.showwarning(
                "Install completed with errors",
                f"The install completed with {len(installer.log.errors)} errors! The installation may not have been successful, check the logs for more details",
            )
        else:
            messagebox.showinfo(
                "Install complete!",
                "Check the logs for details etc. Utilize the script in the 'uninstall' folder of the mod directory to revert these changes.",
            )

    def _handle_exception_during_install(self, e: Exception, installer: ModInstaller, tslpatchdata_root_path: CaseAwarePath):
        short_error_msg = f"{type(e).__name__}: {e.args[0]}"
        self.write_log(short_error_msg)
        installer.log.add_error("The installation was aborted with errors")
        log_file_path = tslpatchdata_root_path.parent / "installlog.txt"
        with log_file_path.open("w", encoding="utf-8") as log_file:
            for log in installer.log.all_logs:
                log_file.write(f"{log.message}\n")
            log_file.write(f"{traceback.format_exc()}\n")
        messagebox.showerror(
            "Error",
            f"An unexpected error occurred during the installation and the installation was forced to terminate:\n{short_error_msg}",
        )
        raise

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
            settings_section = next(
                (section for section in ini.sections() if section.lower() == "settings"),
                None,
            )
            if not settings_section:
                namespace.name = "default"
                return namespace
            settings_ini = CaseInsensitiveDict(dict(ini[settings_section].items()))
            namespace.name = settings_ini.get("WindowCaption") or "default"

        return namespace

    def load_namespace(self, namespaces: list[PatcherNamespace]) -> None:
        self.namespaces_combobox["values"] = namespaces
        self.namespaces_combobox.set(self.namespaces_combobox["values"][0])
        self.namespaces = namespaces
        namespace_option = next(x for x in self.namespaces if x.name == self.namespaces_combobox.get())
        game_number: int | None
        if namespace_option.data_folderpath:
            changes_ini_path = CaseAwarePath(
                self.mod_path,
                "tslpatchdata",
                namespace_option.data_folderpath,
                namespace_option.ini_filename,
            )
        else:
            changes_ini_path = CaseAwarePath(self.mod_path, "tslpatchdata", namespace_option.ini_filename)
        game_number = self.extract_lookup_game_number(
            changes_ini_path,
        )
        with changes_ini_path.parent.joinpath("info.rtf").open("r") as rtf:
            self.set_stripped_rtf_text(rtf)
        if game_number:
            self._handle_gamepaths_with_mod(game_number)

    def _handle_gamepaths_with_mod(self, game_number):
        game = Game(game_number)
        prechosen_gamepath = self.gamepaths.get()
        gamepaths_list = [str(path) for path in self.default_game_paths[game] if path.exists()]
        if game == Game.K2:
            gamepaths_list.extend([str(path) for path in self.default_game_paths[Game.K1] if path.exists()])
        self.gamepaths["values"] = gamepaths_list
        if prechosen_gamepath in self.gamepaths["values"]:
            self.gamepaths.set(prechosen_gamepath)
        else:
            self.gamepaths.set("Select your KOTOR directory path")

    def set_stripped_rtf_text(self, rtf):
        stripped_content = striprtf(rtf.read())
        self.description_text.config(state="normal")
        self.description_text.delete(1.0, tk.END)
        self.description_text.insert(tk.END, stripped_content)
        self.description_text.config(state="disabled")

    def write_log(self, message: str) -> None:
        self.description_text.config(state="normal")
        self.description_text.insert(tk.END, message + os.linesep)
        self.description_text.see(tk.END)
        self.description_text.config(state="disabled")


def striprtf(text):
    pattern = re.compile(r"\\([a-z]{1,32})(-?\d{1,10})?[ ]?|\\'([0-9a-f]{2})|\\([^a-z])|([{}])|[\r\n]+|(.)", re.I)
    # control words which specify a "destionation".
    destinations = frozenset(
        (
            "aftncn",
            "aftnsep",
            "aftnsepc",
            "annotation",
            "atnauthor",
            "atndate",
            "atnicn",
            "atnid",
            "atnparent",
            "atnref",
            "atntime",
            "atrfend",
            "atrfstart",
            "author",
            "background",
            "bkmkend",
            "bkmkstart",
            "blipuid",
            "buptim",
            "category",
            "colorschememapping",
            "colortbl",
            "comment",
            "company",
            "creatim",
            "datafield",
            "datastore",
            "defchp",
            "defpap",
            "do",
            "doccomm",
            "docvar",
            "dptxbxtext",
            "ebcend",
            "ebcstart",
            "factoidname",
            "falt",
            "fchars",
            "ffdeftext",
            "ffentrymcr",
            "ffexitmcr",
            "ffformat",
            "ffhelptext",
            "ffl",
            "ffname",
            "ffstattext",
            "field",
            "file",
            "filetbl",
            "fldinst",
            "fldrslt",
            "fldtype",
            "fname",
            "fontemb",
            "fontfile",
            "fonttbl",
            "footer",
            "footerf",
            "footerl",
            "footerr",
            "footnote",
            "formfield",
            "ftncn",
            "ftnsep",
            "ftnsepc",
            "g",
            "generator",
            "gridtbl",
            "header",
            "headerf",
            "headerl",
            "headerr",
            "hl",
            "hlfr",
            "hlinkbase",
            "hlloc",
            "hlsrc",
            "hsv",
            "htmltag",
            "info",
            "keycode",
            "keywords",
            "latentstyles",
            "lchars",
            "levelnumbers",
            "leveltext",
            "lfolevel",
            "linkval",
            "list",
            "listlevel",
            "listname",
            "listoverride",
            "listoverridetable",
            "listpicture",
            "liststylename",
            "listtable",
            "listtext",
            "lsdlockedexcept",
            "macc",
            "maccPr",
            "mailmerge",
            "maln",
            "malnScr",
            "manager",
            "margPr",
            "mbar",
            "mbarPr",
            "mbaseJc",
            "mbegChr",
            "mborderBox",
            "mborderBoxPr",
            "mbox",
            "mboxPr",
            "mchr",
            "mcount",
            "mctrlPr",
            "md",
            "mdeg",
            "mdegHide",
            "mden",
            "mdiff",
            "mdPr",
            "me",
            "mendChr",
            "meqArr",
            "meqArrPr",
            "mf",
            "mfName",
            "mfPr",
            "mfunc",
            "mfuncPr",
            "mgroupChr",
            "mgroupChrPr",
            "mgrow",
            "mhideBot",
            "mhideLeft",
            "mhideRight",
            "mhideTop",
            "mhtmltag",
            "mlim",
            "mlimloc",
            "mlimlow",
            "mlimlowPr",
            "mlimupp",
            "mlimuppPr",
            "mm",
            "mmaddfieldname",
            "mmath",
            "mmathPict",
            "mmathPr",
            "mmaxdist",
            "mmc",
            "mmcJc",
            "mmconnectstr",
            "mmconnectstrdata",
            "mmcPr",
            "mmcs",
            "mmdatasource",
            "mmheadersource",
            "mmmailsubject",
            "mmodso",
            "mmodsofilter",
            "mmodsofldmpdata",
            "mmodsomappedname",
            "mmodsoname",
            "mmodsorecipdata",
            "mmodsosort",
            "mmodsosrc",
            "mmodsotable",
            "mmodsoudl",
            "mmodsoudldata",
            "mmodsouniquetag",
            "mmPr",
            "mmquery",
            "mmr",
            "mnary",
            "mnaryPr",
            "mnoBreak",
            "mnum",
            "mobjDist",
            "moMath",
            "moMathPara",
            "moMathParaPr",
            "mopEmu",
            "mphant",
            "mphantPr",
            "mplcHide",
            "mpos",
            "mr",
            "mrad",
            "mradPr",
            "mrPr",
            "msepChr",
            "mshow",
            "mshp",
            "msPre",
            "msPrePr",
            "msSub",
            "msSubPr",
            "msSubSup",
            "msSubSupPr",
            "msSup",
            "msSupPr",
            "mstrikeBLTR",
            "mstrikeH",
            "mstrikeTLBR",
            "mstrikeV",
            "msub",
            "msubHide",
            "msup",
            "msupHide",
            "mtransp",
            "mtype",
            "mvertJc",
            "mvfmf",
            "mvfml",
            "mvtof",
            "mvtol",
            "mzeroAsc",
            "mzeroDesc",
            "mzeroWid",
            "nesttableprops",
            "nextfile",
            "nonesttables",
            "objalias",
            "objclass",
            "objdata",
            "object",
            "objname",
            "objsect",
            "objtime",
            "oldcprops",
            "oldpprops",
            "oldsprops",
            "oldtprops",
            "oleclsid",
            "operator",
            "panose",
            "password",
            "passwordhash",
            "pgp",
            "pgptbl",
            "picprop",
            "pict",
            "pn",
            "pnseclvl",
            "pntext",
            "pntxta",
            "pntxtb",
            "printim",
            "private",
            "propname",
            "protend",
            "protstart",
            "protusertbl",
            "pxe",
            "result",
            "revtbl",
            "revtim",
            "rsidtbl",
            "rxe",
            "shp",
            "shpgrp",
            "shpinst",
            "shppict",
            "shprslt",
            "shptxt",
            "sn",
            "sp",
            "staticval",
            "stylesheet",
            "subject",
            "sv",
            "svb",
            "tc",
            "template",
            "themedata",
            "title",
            "txe",
            "ud",
            "upr",
            "userprops",
            "wgrffmtfilter",
            "windowcaption",
            "writereservation",
            "writereservhash",
            "xe",
            "xform",
            "xmlattrname",
            "xmlattrvalue",
            "xmlclose",
            "xmlname",
            "xmlnstbl",
            "xmlopen",
        ),
    )
    # Translation of some special characters.
    specialchars = {
        "par": "\n",
        "sect": "\n\n",
        "page": "\n\n",
        "line": "\n",
        "tab": "\t",
        "emdash": "\u2014",
        "endash": "\u2013",
        "emspace": "\u2003",
        "enspace": "\u2002",
        "qmspace": "\u2005",
        "bullet": "\u2022",
        "lquote": "\u2018",
        "rquote": "\u2019",
        "ldblquote": "\201C",
        "rdblquote": "\u201D",
    }
    stack = []
    ignorable = False  # Whether this group (and all inside it) are "ignorable".
    ucskip = 1  # Number of ASCII characters to skip after a unicode character.
    curskip = 0  # Number of ASCII characters left to skip
    out = []  # Output buffer.
    for match in pattern.finditer(text):
        word, arg, hex, char, brace, tchar = match.groups()
        if brace:
            curskip = 0
            if brace == "{":
                # Push state
                stack.append((ucskip, ignorable))
            elif brace == "}":
                # Pop state
                ucskip, ignorable = stack.pop()
        elif char:  # \x (not a letter)
            curskip = 0
            if char == "~":
                if not ignorable:
                    out.append("\xA0")
            elif char in "{}\\":
                if not ignorable:
                    out.append(char)
            elif char == "*":
                ignorable = True
        elif word:  # \foo
            curskip = 0
            if word in destinations:
                ignorable = True
            elif ignorable:
                pass
            elif word in specialchars:
                out.append(specialchars[word])
            elif word == "uc":
                ucskip = int(arg)
            elif word == "u":
                c = int(arg)
                if c < 0:
                    c += 0x10000
                out.append(chr(c))
                curskip = ucskip
        elif hex:  # \'xx
            if curskip > 0:
                curskip -= 1
            elif not ignorable:
                c = int(hex, 16)
                out.append(chr(c))
        elif tchar:
            if curskip > 0:
                curskip -= 1
            elif not ignorable:
                out.append(tchar)
    return "".join(out)


def main():
    app = App()
    app.mainloop()


main()
