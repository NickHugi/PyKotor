from __future__ import annotations

import base64
import chardet
import contextlib
import ctypes
import json
import os
import pathlib
import sys
import tkinter as tk
import traceback
import webbrowser
from argparse import ArgumentParser, Namespace
from datetime import datetime, timedelta, timezone
from enum import IntEnum
from threading import Thread
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont
from typing import TYPE_CHECKING, NoReturn

if getattr(sys, "frozen", False) is False:
    def update_sys_path(path):
        working_dir = str(path)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.append(working_dir)

    pykotor_path = pathlib.Path(__file__).parents[3] / "Libraries" / "PyKotor" / "src" / "pykotor"
    if pykotor_path.exists():
        update_sys_path(pykotor_path.parent)
    utility_path = pathlib.Path(__file__).parents[3] / "Libraries" / "Utility" / "src" / "utility"
    if utility_path.exists():
        update_sys_path(utility_path.parent)

from pykotor.common.misc import Game
from pykotor.tools.path import CaseAwarePath, find_kotor_paths_from_default
from pykotor.tslpatcher.logger import PatchLogger
from pykotor.tslpatcher.patcher import ModInstaller
from pykotor.tslpatcher.reader import ConfigReader, NamespaceReader
from tooltip import ToolTip
from uninstall_mod import ModUninstaller
from utility.error_handling import universal_simplify_exception
from utility.path import Path
from utility.string import striprtf

if TYPE_CHECKING:
    from io import TextIOWrapper

    from pykotor.tslpatcher.namespaces import PatcherNamespace

CURRENT_VERSION: tuple[int, ...] = (1, 4, 3)


class ExitCode(IntEnum):
    SUCCESS = 0
    UNKNOWN_STARTUP_ERROR = 1  # happens outside of our code
    NUMBER_OF_ARGS = 2
    NAMESPACES_INI_NOT_FOUND = 3
    NAMESPACE_INDEX_OUT_OF_RANGE = 4
    CHANGES_INI_NOT_FOUND = 5
    ABORT_INSTALL_UNSAFE = 6
    EXCEPTION_DURING_INSTALL = 7
    INSTALL_COMPLETED_WITH_ERRORS = 8


# Please be careful modifying this functionality as 3rd parties depend on this syntax.
def parse_args() -> Namespace:
    """Parses command line arguments.

    Args:
    ----
        parser: ArgumentParser - Argument parser object from the argparse library.
        kwargs: dict - Keyword arguments dictionary
        positional: list - Positional arguments list

    Returns:
    -------
        Namespace - Namespace containing parsed arguments

    Parses command line arguments and returns Namespace:
        - Creates ArgumentParser object to parse arguments
        - Adds supported arguments to parser
        - Parses arguments into kwargs and positional lists
        - Unifies positional and keyword args into kwargs Namespace.
    """
    parser = ArgumentParser(description="HoloPatcher CLI")

    # Positional arguments for the old syntax
    parser.add_argument("--game-dir", type=str, help="Path to game directory")
    parser.add_argument("--tslpatchdata", type=str, help="Path to tslpatchdata")
    parser.add_argument(
        "--namespace-option-index",
        type=int,
        help="Namespace option index",
    )
    parser.add_argument(
        "--console",
        action="store_true",
        help="Show the console when launching HoloPatcher.",
    )
    parser.add_argument("--uninstall", action="store_true", help="Uninstalls the selected mod.")
    parser.add_argument("--install", action="store_true", help="Starts an install immediately on launch.")
    parser.add_argument("--validate", action="store_true", help="Starts validation of the selected mod.")

    kwargs, positional = parser.parse_known_args()

    required_number_of_positional_args = 2
    max_positional_args = 3  # sourcery skip: move-assign

    # Unify positional args with the keyword args.
    number_of_positional_args = len(positional)
    if number_of_positional_args == required_number_of_positional_args:
        kwargs.game_dir = positional[0]
        kwargs.tslpatchdata = positional[1]
    if number_of_positional_args == max_positional_args:
        kwargs.namespace_option_index = positional[2]
    if kwargs.namespace_option_index:
        try:
            kwargs.namespace_option_index = int(kwargs.namespace_option_index)
        except ValueError:
            print("Invalid namespace_option_index. It should be an integer.")
            sys.exit(ExitCode.NAMESPACE_INDEX_OUT_OF_RANGE)

    return kwargs

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HoloPatcher")
        self.set_window(width=400, height=500)

        self.mod_path = ""
        self.namespaces: list[PatcherNamespace] = []

        self.initialize_logger()
        self.initialize_ui_menu()
        self.initialize_ui_controls()

        self.install_running = False
        self.protocol("WM_DELETE_WINDOW", self.handle_exit_button)

        cmdline_args = parse_args()
        self.open_mod(cmdline_args.tslpatchdata or Path.cwd())
        self.handle_commandline(cmdline_args)

    def set_window(self, width: int, height: int):
        # Get screen dimensions
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # Calculate position to center the window
        x_position = int((screen_width / 2) - (width / 2))
        y_position = int((screen_height / 2) - (height / 2))

        # Set the dimensions and position
        self.geometry(f"{width}x{height}+{x_position}+{y_position}")
        self.resizable(width=False, height=False)

    def initialize_logger(self):
        self.logger = PatchLogger()
        self.logger.verbose_observable.subscribe(self.write_log)
        self.logger.note_observable.subscribe(self.write_log)
        self.logger.warning_observable.subscribe(self.write_log)
        self.logger.error_observable.subscribe(self.write_log)

    def initialize_ui_menu(self):
        # Initialize top menu bar
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)

        # Version display - non-clickable
        version_label = f"v{'.'.join(map(str, CURRENT_VERSION))}"
        self.menu_bar.add_command(label=version_label)
        self.menu_bar.entryconfig(version_label, state="disabled")

        # About menu
        about_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="About", menu=about_menu)

        # Adding items to About menu
        about_menu.add_command(label="Check for Updates", command=self.check_for_updates)
        about_menu.add_command(label="Homepage", command=self.open_homepage)
        about_menu.add_command(label="GitHub Source", command=self.open_github)

        # Discord submenu
        discord_menu = tk.Menu(about_menu, tearoff=0)
        about_menu.add_cascade(label="Discord", menu=discord_menu)
        discord_menu.add_command(label="DeadlyStream", command=self.open_deadlystream_discord)
        discord_menu.add_command(label="r/kotor", command=self.open_kotor_discord)

    def initialize_ui_controls(self) -> None:
        # Use grid layout for main window
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Configure style for Combobox
        style = ttk.Style(self)
        style.configure("TCombobox", font=("Helvetica", 10), padding=4)

        # Top area for comboboxes and buttons
        top_frame = tk.Frame(self)
        top_frame.grid(row=0, column=0, sticky="ew")
        top_frame.grid_columnconfigure(0, weight=1)  # Make comboboxes expand
        top_frame.grid_columnconfigure(1, weight=0)  # Keep buttons fixed size

        self.namespaces_combobox = ttk.Combobox(top_frame, state="readonly", style="TCombobox")
        self.namespaces_combobox.set("Select the mod to install")
        self.namespaces_combobox.grid(row=0, column=0, padx=5, pady=2, sticky="ew")
        self.namespaces_combobox.bind("<<ComboboxSelected>>", self.on_namespace_option_chosen)

        # used for handling focus events
        self.namespaces_combobox.bind("<FocusIn>", self.on_combobox_focus_in)
        self.namespaces_combobox.bind("<FocusOut>", self.on_combobox_focus_out)
        self.namespaces_combobox_state = 0

        ToolTip(self.namespaces_combobox, lambda: self.on_namespace_option_hover())

        self.browse_button = ttk.Button(top_frame, text="Browse", command=self.open_mod)
        self.browse_button.grid(row=0, column=1, padx=5, pady=2, sticky="e")

        self.gamepaths = ttk.Combobox(top_frame, style="TCombobox")
        self.gamepaths.set("Select your KOTOR directory path")
        self.gamepaths.grid(row=1, column=0, padx=5, pady=2, sticky="ew")
        self.gamepaths["values"] = [str(path) for game in find_kotor_paths_from_default().values() for path in game]
        self.gamepaths.bind("<<ComboboxSelected>>", self.on_gamepaths_chosen)

        self.gamepaths_browse_button = ttk.Button(top_frame, text="Browse", command=self.open_kotor)
        self.gamepaths_browse_button.grid(row=1, column=1, padx=5, pady=2, sticky="e")

        # Middle area for text and scrollbar
        text_frame = tk.Frame(self)
        text_frame.grid(row=1, column=0, sticky="nsew")
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)

        self.main_text = tk.Text(text_frame, wrap=tk.WORD)
        font_obj = tkfont.Font(font=self.main_text.cget("font"))
        font_obj.configure(size=9)
        self.main_text.configure(font=font_obj)
        self.main_text.grid(row=0, column=0, sticky="nsew")

        scrollbar = tk.Scrollbar(text_frame, command=self.main_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.main_text.config(yscrollcommand=scrollbar.set)

        # Bottom area for buttons
        bottom_frame = tk.Frame(self)
        bottom_frame.grid(row=2, column=0, sticky="ew")

        self.exit_button = ttk.Button(bottom_frame, text="Exit", command=self.handle_exit_button)
        self.exit_button.pack(side="left", padx=5, pady=5)

        self.uninstall_button = ttk.Button(bottom_frame, text="Uninstall", command=self.uninstall_selected_mod)
        #self.uninstall_button.pack(side="right", padx=5, pady=5)

        self.install_button = ttk.Button(bottom_frame, text="Install", command=self.begin_install)
        self.install_button.pack(side="right", padx=5, pady=5)

        self.testreader_button = ttk.Button(bottom_frame, text="Validate INI", command=self.test_reader)
        self.testreader_button.pack(side="right", padx=5, pady=5)

    def on_combobox_focus_in(self, event):
        if self.namespaces_combobox_state == 2: # no selection, fix the focus
            self.focus_set()
            self.namespaces_combobox_state = 0  # base status
        else:
            self.namespaces_combobox_state = 1  # combobox clicked

    def on_combobox_focus_out(self, event):
        if self.namespaces_combobox_state == 1:
            self.namespaces_combobox_state = 2  # no selection

    def check_for_updates(self) -> None:
        try:
            import requests
            req = requests.get("https://api.github.com/repos/NickHugi/PyKotor/contents/update_info.json", timeout=15)
            req.raise_for_status()
            file_data = req.json()
            base64_content = file_data["content"]
            decoded_content = base64.b64decode(base64_content)  # Correctly decoding the base64 content
            updateInfoData = json.loads(decoded_content.decode("utf-8"))

            new_version = tuple(map(int, str(updateInfoData["holopatcherLatestVersion"]).split(".")))
            if new_version > CURRENT_VERSION:
                if messagebox.askyesno(
                    "Update available",
                    "A newer version of HoloPatcher is available, would you like to download it now?",
                ):
                    webbrowser.open_new(updateInfoData["holopatcherDownloadLink"])
            else:
                messagebox.showinfo(
                    "No updates available.",
                    f"You are already running the latest version of HoloPatcher ({updateInfoData['holopatcherLatestVersion']})",
                )
        except Exception as e:
            messagebox.showerror(
                "Unable to fetch latest version.",
                (
                    f"Error: {e!r}\n"
                    "Check if you are connected to the internet."
                ),
            )

    def open_homepage(self):
        webbrowser.open_new("https://deadlystream.com/files/file/2243-holopatcher")
    def open_github(self):
        webbrowser.open_new("https://github.com/NickHugi/PyKotor")
    def open_deadlystream_discord(self):
        webbrowser.open_new("https://discord.gg/HBwVCpAA")
    def open_kotor_discord(self):
        webbrowser.open_new("https://discord.com/invite/kotor")

    def handle_commandline(self, cmdline_args: Namespace) -> None:
        """Handle command line arguments passed to the application.

        Args:
        ----
            cmdline_args: Namespace of command line arguments passed to the application.

        Processing Logic:
        ----------------
            - Open the specified game directory if provided
            - Set the selected namespace if namespace index is provided
            - Hide the console if not explicitly shown
            - Handle install/uninstall in console mode and exit
            - Set one_shot flag for install/uninstall operations
            - Begin install thread or call uninstall method and exit
        """
        if cmdline_args.game_dir:
            self.open_kotor(cmdline_args.game_dir)
        if cmdline_args.namespace_option_index:
            self.namespaces_combobox.set(self.namespaces_combobox["values"][cmdline_args.namespace_option_index])
        if not cmdline_args.console:
            self.hide_console()

        self.one_shot: bool = False
        if cmdline_args.install or cmdline_args.uninstall or cmdline_args.validate:
            self.one_shot = True
            self.withdraw()
            self.handle_console_mode()
        if cmdline_args.install:
            self.begin_install_thread()
            sys.exit()
        if cmdline_args.uninstall:
            self.uninstall_selected_mod()
            sys.exit()
        if cmdline_args.validate:
            self.test_reader()
            sys.exit()

    def handle_console_mode(self) -> None:
        """Overrides message box functions for console mode. This is done for true CLI support.

        Args:
        ----
            self: The class instance.

        Processing Logic:
        ----------------
            - Replaces message box functions with print statements to display messages in the console.
            - Prompts the user for input and returns True/False for yes/no questions instead of opening a message box.
            - Allows message boxes to work as expected in console mode without GUI dependencies.
        """

        class MessageboxOverride:
            @staticmethod
            def showinfo(title, message):
                print(f"[Note] - {title}: {message}")

            @staticmethod
            def showwarning(title, message):
                print(f"[Warning] - {title}: {message}")

            @staticmethod
            def showerror(title, message):
                print(f"[Error] - {title}: {message}")

            @staticmethod
            def askyesno(title, message):
                """Console-based replacement for messagebox.askyesno and similar."""
                print(f"{title}\n{message}")
                while True:
                    response = input("(y/N)").lower().strip()
                    if response in ["yes", "y"]:
                        return True
                    if response in ["no", "n"]:
                        return False
                    print("Invalid input. Please enter 'yes' or 'no'")

        messagebox.showinfo = MessageboxOverride.showinfo  # type: ignore[assignment]
        messagebox.showwarning = MessageboxOverride.showwarning  # type: ignore[assignment]
        messagebox.showerror = MessageboxOverride.showerror  # type: ignore[assignment]
        # messagebox.askyesno = MessageboxOverride.askyesno  # noqa: ERA001
        # messagebox.askyesnocancel = MessageboxOverride.askyesno  # noqa: ERA001
        # messagebox.askretrycancel = MessageboxOverride.askyesno  # noqa: ERA001

    def hide_console(self) -> None:
        """Hide the console window in GUI mode."""
        # Windows
        if os.name == "nt":
            import ctypes

            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

    def uninstall_selected_mod(self) -> None:
        """Uninstalls the selected mod using the most recent backup folder created during the last install.

        Processing Logic:
        ----------------
            - Check if an install is already running
            - Get the selected namespace option
            - Check for valid namespace and game path
            - Get the backup folder path
            - Sort backup folders by date
            - Get the most recent backup folder
            - Check for required files in backup
            - Confirm uninstall with user
            - Delete existing files
            - Restore files from backup
            - Offer to delete restored backup.
        """
        if not self.preinstall_validate_chosen():
            return
        backup_parent_folder = Path(self.mod_path, "backup")
        if not backup_parent_folder.exists():
            messagebox.showerror(
                "Backup folder empty/missing.",
                f"Could not find backup folder '{backup_parent_folder}'{os.linesep*2}Are you sure the mod is installed?",
            )
            return
        self.clear_main_text()
        ModUninstaller(backup_parent_folder, Path(self.gamepaths.get()), self.logger).uninstall_selected_mod()

    def handle_exit_button(self) -> None:
        """Handle exit button click during installation.

        Processing Logic:
        ----------------
            - Check if installation is running
            - Display confirmation dialog and check response
            - Try stopping install thread gracefully
            - If stopping fails, force terminate install thread
            - Destroy window and exit with abort code.
        """
        if not self.install_running:
            sys.exit(ExitCode.SUCCESS)
        if not messagebox.askyesno(
            "Really cancel the current installation? ",
            "CONTINUING WILL BREAK YOUR GAME AND REQUIRE A FULL KOTOR REINSTALL!",
        ):
            return
        with contextlib.suppress(Exception):
            self.install_thread._stop()  # type: ignore[attr-defined]
            print("force terminate of install thread succeeded")
        with contextlib.suppress(Exception):
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(self.install_thread.ident), ctypes.py_object(SystemExit))  # type: ignore[reportGeneralTypeIssues, arg-type]
        self.destroy()
        sys.exit(ExitCode.ABORT_INSTALL_UNSAFE)

    def on_gamepaths_chosen(self, event: tk.Event) -> None:
        """Adjust the combobox after a short delay."""
        self.after(10, lambda: self.move_cursor_to_end(event.widget))

    def move_cursor_to_end(self, combobox: ttk.Combobox) -> None:
        """Shows the rightmost portion of the specified combobox as that's the most relevant."""
        combobox.focus_set()
        position: int = len(combobox.get())
        combobox.icursor(position)
        combobox.xview(position)
        self.focus_set()

    def on_namespace_option_hover(self) -> str:
        namespace_option: PatcherNamespace | None = next(
            (x for x in self.namespaces if x.name == self.namespaces_combobox.get()),
            None,
        )
        return namespace_option.description if namespace_option else ""

    def detect_encoding(self, file_path : CaseAwarePath):
        with file_path.open("rb") as f:
            raw_data = f.read(1024) 
        return chardet.detect(raw_data)['encoding']

    def on_namespace_option_chosen(self, event: tk.Event, config_reader: ConfigReader | None = None) -> None:
        """Handles the namespace option being chosen from the combobox.

        Args:
        ----
            self: The PatcherWindow instance
            event: The event object from the combobox

        Processes the chosen namespace option by:
            1. Finding the matching PatcherNamespace object
            2. Loading the changes.ini file path
            3. Extracting the game number if present
            4. Handling game paths if a game number is found
            5. Loading the info.rtf file as defined.
        """
        try:
            namespace_option: PatcherNamespace = next(x for x in self.namespaces if x.name == self.namespaces_combobox.get())
            changes_ini_path = CaseAwarePath(self.mod_path, "tslpatchdata", namespace_option.changes_filepath())
            reader: ConfigReader = config_reader or ConfigReader.from_filepath(changes_ini_path)
            reader.load_settings()
            game_number: int | None = reader.config.game_number
            if game_number:
                self.filter_kotor_game_paths(game_number)
            info_rtf = CaseAwarePath(self.mod_path, "tslpatchdata", namespace_option.rtf_filepath())
            if not info_rtf.exists():
                messagebox.showwarning("No info.rtf", "Could not load the rtf for this mod, file not found on disk.")
                return
            
            file_encoding = self.detect_encoding(info_rtf)
            # Set fallback encoding if encoding could not be detected
            if file_encoding == None:
                file_encoding = "utf-8"

            with info_rtf.open("r", encoding=file_encoding) as rtf:
                self.set_stripped_rtf_text(rtf)

        except Exception as e:  # noqa: BLE001
            error_name, msg = universal_simplify_exception(e)
            messagebox.showerror(
                error_name,
                f"An unexpected error occurred while loading the patcher namespace.{os.linesep*2}{msg}",
            )
        else:
            self.after(10, lambda: self.move_cursor_to_end(self.namespaces_combobox))

    def load_namespace(self, namespaces: list[PatcherNamespace], config_reader: ConfigReader | None = None) -> None:
        """Loads namespaces into the UI.

        Args:
        ----
            namespaces: List of PatcherNamespace objects
            config_reader: ConfigReader object or None

        Processing Logic:
        ----------------
            - Populates the namespaces combobox with the provided namespaces
            - Sets the first namespace as the selected option
            - Stores the namespaces for later use
            - Calls on_namespace_option_chosen to load initial config.
        """
        self.namespaces_combobox["values"] = namespaces
        self.namespaces_combobox.set(self.namespaces_combobox["values"][0])
        self.namespaces = namespaces
        self.on_namespace_option_chosen(tk.Event(), config_reader)

    def open_mod(self, default_directory_path_str: os.PathLike | str | None = None) -> None:
        """Opens a mod directory.

        Args:
        ----
            default_directory_path_str: The default directory path to open as a string or None. This is
                relevant when HoloPatcher is placed next to a 'tslpatchdata' folder containing the patcher files.
                This is also relevant when using the CLI.

        Processing Logic:
        ----------------
            - Gets the directory path from the argument or opens a file dialog
            - Loads namespaces from namespaces.ini or changes from changes.ini
                - If a changes.ini was loaded, build it as a single entry in a namespace.
            - Checks permissions of the mod folder
            - Handles errors opening the mod.
        """
        try:
            directory_path_str = default_directory_path_str or filedialog.askdirectory()
            if not directory_path_str:
                return

            tslpatchdata_path = CaseAwarePath(directory_path_str, "tslpatchdata")
            # handle when a user selects 'tslpatchdata' instead of mod root
            if not tslpatchdata_path.exists() and tslpatchdata_path.parent.name.lower() == "tslpatchdata":
                tslpatchdata_path = tslpatchdata_path.parent

            self.mod_path = str(tslpatchdata_path.parent)
            namespace_path: CaseAwarePath = tslpatchdata_path / "namespaces.ini"
            changes_path: CaseAwarePath = tslpatchdata_path / "changes.ini"

            if namespace_path.exists():
                self.load_namespace(NamespaceReader.from_filepath(namespace_path))
            elif changes_path.exists():
                config_reader: ConfigReader = ConfigReader.from_filepath(changes_path)
                namespaces: list[PatcherNamespace] = [config_reader.config.as_namespace(changes_path)]
                self.load_namespace(namespaces, config_reader)
            else:
                self.mod_path = ""
                if not default_directory_path_str:  # don't show the error if the cwd was attempted
                    messagebox.showerror("Error", "Could not find a mod located at the given folder.")
                return

            if default_directory_path_str:
                self.browse_button.place_forget()

            self.check_access(tslpatchdata_path, recurse=True)
        except Exception as e:  # noqa: BLE001
            error_name, msg = universal_simplify_exception(e)
            messagebox.showerror(
                error_name,
                f"An unexpected error occurred while loading the mod info.{os.linesep*2}{msg}",
            )

    def open_kotor(self, default_kotor_dir_str=None) -> None:
        """Opens the KOTOR directory.

        Args:
        ----
            default_kotor_dir_str: The default KOTOR directory path as a string. This is only relevant when using the CLI.

        Processing Logic:
        ----------------
            - Try to get the directory path from the default or by opening a file dialog
            - Check access permissions for the directory
            - Set the gamepaths config value and add path to list if not already present
            - Move cursor after a delay to end of dropdown
        """
        try:
            directory_path_str = default_kotor_dir_str or filedialog.askdirectory()
            if not directory_path_str:
                return
            directory = CaseAwarePath(directory_path_str)
            self.check_access(directory)
            directory_str = str(directory)
            self.gamepaths.set(str(directory))
            if directory_str not in self.gamepaths["values"]:
                self.gamepaths["values"] = (*self.gamepaths["values"], directory_str)
            self.after(10, self.move_cursor_to_end)
        except Exception as e:  # noqa: BLE001
            error_name, msg = universal_simplify_exception(e)
            messagebox.showerror(
                error_name,
                f"An unexpected error occurred while loading the game directory.{os.linesep*2}{msg}",
            )

    def check_access(self, directory: Path, recurse=False) -> bool:
        """Check access to a directory.

        Args:
        ----
            directory (Path): Directory path to check access
            recurse (bool): Check access recursively if True

        Returns:
        -------
            bool: True if access is granted, False otherwise

        Processing Logic:
        ----------------
            - Check if directory has access
            - If no access, prompt user to automatically gain access
            - If access cannot be gained, show error
            - If no access after trying, prompt user to continue with an install anyway.
        """
        if directory.has_access(recurse):
            return True
        if (
            messagebox.askyesno(
                "Permission error",
                f"HoloPatcher does not have permissions to the path '{directory!s}', would you like to attempt to gain permission automatically?",
            )
            and not directory.gain_access()
        ):
            messagebox.showerror(
                "Could not gain permission!",
                "Please run HoloPatcher with elevated permissions, and ensure the selected folder exists and is writeable.",
            )
            return False
        if not directory.has_access(recurse):
            return messagebox.askyesno(
                "Unauthorized",
                (
                    f"HoloPatcher needs permissions to access this folder '{directory!s}'. {os.linesep}"
                    f"{os.linesep}"
                    f"Please ensure the necessary folders are writeable or rerun holopatcher with elevated privileges.{os.linesep}"
                    "Continue with an install anyway?"
                ),
            )
        return True

    def preinstall_validate_chosen(self) -> bool:
        """Validates prerequisites for starting an install.

        Args:
        ----
            self: The Installer object.

        Returns:
        -------
            bool: True if validation passed, False otherwise

        Processing Logic:
        ----------------
            - Check if a previous install is still running
            - Check if a mod path is selected
            - Check if a KOTOR install path is selected
            - Check write access to the KOTOR install directory.
        """

        def _if_missing(title, message):
            messagebox.showinfo(title, message)
            if self.one_shot:
                sys.exit(ExitCode.NUMBER_OF_ARGS)
            return False

        if self.install_running:
            messagebox.showinfo(
                "Install already running",
                "Wait for the previous task to finish.",
            )
            return False
        if not self.mod_path or not CaseAwarePath(self.mod_path).exists():
            return _if_missing(
                "No mod chosen",
                "Select your mod directory first.",
            )
        game_path = self.gamepaths.get()
        if not game_path or not CaseAwarePath(game_path).exists():
            return _if_missing(
                "No KOTOR directory chosen",
                "Select your KOTOR directory first.",
            )
        return self.check_access(Path(self.gamepaths.get()))

    def begin_install(self) -> None:
        """Starts the installation process in a background thread.

        Note: This function is not called when utilizing the CLI due to the thread creation - for passthrough purposes.

        Processing Logic:
        ----------------
            - Starts a new Thread to run the installation in the background
            - Catches any exceptions during thread start and displays error message
            - Exits program if exception occurs during installation thread start.

        """
        try:
            self.install_thread = Thread(target=self.begin_install_thread)
            self.install_thread.start()
        except Exception as e:  # noqa: BLE001
            error_name, msg = universal_simplify_exception(e)
            messagebox.showerror(
                error_name,
                f"An unexpected error occurred during the installation and the program was forced to exit.{os.linesep*2}{msg}",
            )
            sys.exit(ExitCode.EXCEPTION_DURING_INSTALL)

    def begin_install_thread(self) -> None:
        """Starts the mod installation thread. This function is called directly when utilizing the CLI.

        Args:
        ----
            self: The PatcherWindow instance

        Processing Logic:
        ----------------
            - Validate pre-install checks have passed
            - Get the selected namespace option
            - Get the path to the ini file
            - Create a ModInstaller instance
            - Try to execute the installation
            - Handle any exceptions during installation
            - Set the install status to not running.
        """
        if not self.preinstall_validate_chosen():
            return
        namespace_option: PatcherNamespace = next(x for x in self.namespaces if x.name == self.namespaces_combobox.get())
        ini_file_path = CaseAwarePath(self.mod_path, "tslpatchdata", namespace_option.changes_filepath())
        namespace_mod_path: CaseAwarePath = ini_file_path.parent

        self.clear_main_text()
        installer = ModInstaller(namespace_mod_path, self.gamepaths.get(), ini_file_path, self.logger)
        try:
            self._execute_mod_install(installer)
        except Exception as e:  # noqa: BLE001
            self._handle_exception_during_install(e, installer)
        self.set_active_install(install_running=False)

    def test_reader(self) -> None:
        if not self.preinstall_validate_chosen():
            return
        namespace_option: PatcherNamespace = next(x for x in self.namespaces if x.name == self.namespaces_combobox.get())
        ini_file_path = CaseAwarePath(self.mod_path, "tslpatchdata", namespace_option.changes_filepath())

        self.set_active_install(install_running=True)
        self.clear_main_text()
        try:
            reader = ConfigReader.from_filepath(ini_file_path, self.logger)
            reader.load(reader.config)
        except Exception as e:  # noqa: BLE001
            messagebox.showerror(*universal_simplify_exception(e))
        self.set_active_install(install_running=False)

    def set_active_install(self, install_running: bool) -> None:
        """Sets the active install state.

        Args:
        ----
            install_running: Whether the install is running or not

        Processing Logic:
        ----------------
            - Sets the install_running attribute based on the install_running argument
            - Configures the state of relevant buttons to disabled if install is running, normal otherwise
            - Handles enabling/disabling buttons during install process.
        """
        if install_running:
            self.install_running = True
            self.install_button.config(state=tk.DISABLED)
            self.uninstall_button.config(state=tk.DISABLED)
            self.gamepaths_browse_button.config(state=tk.DISABLED)
            self.browse_button.config(state=tk.DISABLED)
        else:
            self.install_running = False
            self.initialize_logger()  # reset the errors/warnings etc
            self.install_button.config(state=tk.NORMAL)
            self.uninstall_button.config(state=tk.NORMAL)
            self.gamepaths_browse_button.config(state=tk.NORMAL)
            self.browse_button.config(state=tk.NORMAL)

    def clear_main_text(self) -> None:
        self.main_text.config(state=tk.NORMAL)
        self.main_text.delete(1.0, tk.END)
        self.main_text.config(state=tk.DISABLED)

    def _execute_mod_install(self, installer: ModInstaller) -> None:
        """Executes the mod installation.

        Args:
        ----
            installer: ModInstaller object containing installation logic.

        Processing Logic:
        ----------------
            1. Sets installation status to running
            2. Gets start time of installation
            3. Calls installer install method
            4. Calculates total installation time
            5. Logs installation details including errors, warnings and time
            6. Writes full install log to file
            7. Shows success or error message based on install result
            8. If CLI, exit regardless of success or error.
        """
        self.set_active_install(install_running=True)
        #profiler = cProfile.Profile()
        #profiler.enable()
        install_start_time: datetime = datetime.now(timezone.utc).astimezone()
        installer.install()
        total_install_time: timedelta = datetime.now(timezone.utc).astimezone() - install_start_time
        #profiler.disable()
        #profiler_output_file = Path("profiler_output.pstat").resolve()
        #profiler.dump_stats(str(profiler_output_file))

        days, remainder = divmod(total_install_time.total_seconds(), 24 * 60 * 60)
        hours, remainder = divmod(remainder, 60 * 60)
        minutes, seconds = divmod(remainder, 60)

        time_str = (
            f"{f'{int(days)} days, ' if days else ''}"
            f"{f'{int(hours)} hours, ' if hours else ''}"
            f"{f'{int(minutes)} minutes, ' if minutes or not (days or hours) else ''}"
            f"{int(seconds)} seconds"
        )

        installer.log.add_note(
            f"The installation is complete with {len(installer.log.errors)} errors and {len(installer.log.warnings)} warnings. "
            f"Total install time: {time_str}",
        )
        log_file_path: Path = Path.pathify(self.mod_path) / "installlog.txt"
        with log_file_path.open("w", encoding="utf-8") as log_file:
            for log in installer.log.all_logs:
                log_file.write(f"{log.message}\n")
        if len(installer.log.errors) > 0:
            messagebox.showwarning(
                "Install completed with errors",
                f"The install completed with {len(installer.log.errors)} errors! The installation may not have been successful, check the logs for more details. Total install time: {time_str}",
            )
            if self.one_shot:
                sys.exit(ExitCode.INSTALL_COMPLETED_WITH_ERRORS)
        else:
            messagebox.showinfo(
                "Install complete!",
                f"Check the logs for details etc. Utilize the script in the 'uninstall' folder of the mod directory to revert these changes. Total install time: {time_str}",
            )
            if self.one_shot:
                sys.exit(ExitCode.SUCCESS)

    def _handle_exception_during_install(self, e: Exception, installer: ModInstaller) -> NoReturn:
        """Handles exceptions during installation.

        Args:
        ----
            e: Exception - The exception raised
            installer: ModInstaller - The installer object

        Processing Logic:
        ----------------
            - Simplifies the exception for error name and message
            - Writes the error message to the log
            - Adds an error to the installer log
            - Writes the full installer log to a file
            - Shows an error message box with the error name and message
            - Sets the install flag to False
            - Reraises the exception.
        """
        error_name, msg = universal_simplify_exception(e)
        self.write_log(msg)
        installer.log.add_error("The installation was aborted with errors")
        log_file_path = Path(self.mod_path, "installlog.txt")
        with log_file_path.open("w", encoding="utf-8") as log_file:
            for log in installer.log.all_logs:
                log_file.write(f"{log.message}\n")
            log_file.write(f"{traceback.format_exc()}\n")
        messagebox.showerror(
            error_name,
            f"An unexpected error occurred during the installation and the installation was forced to terminate.{os.linesep*2}{msg}",
        )
        self.set_active_install(install_running=False)
        raise

    def filter_kotor_game_paths(self, game_number) -> None:
        """Determines what shows up in the gamepaths combobox, based on the LookupGameNumber setting."""
        game = Game(game_number)
        gamepaths_list: list[str] = [
            str(path)
            for game_key in ([game] + ([Game.K1] if game == Game.K2 else []))
            for path in find_kotor_paths_from_default()[game_key]
        ]
        self.gamepaths["values"] = gamepaths_list

    def set_stripped_rtf_text(self, rtf: TextIOWrapper) -> None:
        """Strips the info.rtf of all RTF related text and displays it in the UI."""
        stripped_content: str = striprtf(rtf.read())
        self.main_text.config(state=tk.NORMAL)
        self.main_text.delete(1.0, tk.END)
        self.main_text.insert(tk.END, stripped_content)
        self.main_text.config(state=tk.DISABLED)

    def write_log(self, message: str) -> None:
        """Writes a message to the log.

        Args:
        ----
            message (str): The message to write to the log.

        Processes the log message by:
            - Setting the description text widget to editable
            - Inserting the message plus a newline at the end of the text
            - Scrolling to the end of the text
            - Making the description text widget not editable again.
        """
        self.main_text.config(state=tk.NORMAL)
        self.main_text.insert(tk.END, message + os.linesep)
        self.main_text.see(tk.END)
        self.main_text.config(state=tk.DISABLED)


def custom_excepthook(exc_type, exc_value, exc_traceback) -> None:
    """Custom exception hook to display errors in message box.

    When pyinstaller compiled in --console mode, this will match the same error message behavior of --noconsole.

    Args:
    ----
        exc_type: Exception type
        exc_value: Exception value
        exc_traceback: Exception traceback

    Processing Logic:
    ----------------
        - Format the exception using traceback
        - Create a hidden root Tk window
        - Show error message in message box
        - Destroy the root window.
    """
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    messagebox.showerror("Error", error_msg)
    root.destroy()


sys.excepthook = custom_excepthook


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
