from __future__ import annotations

import base64
import contextlib
import ctypes
import inspect
import io
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time
import tkinter as tk
import traceback
import webbrowser
from argparse import ArgumentParser, Namespace
from datetime import datetime, timedelta, timezone
from enum import IntEnum
from threading import Event, Thread
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont
from typing import TYPE_CHECKING, NoReturn

if getattr(sys, "frozen", False) is False:
    def update_sys_path(path):
        working_dir = str(path)
        if working_dir not in sys.path:
            sys.path.append(working_dir)

    with contextlib.suppress(Exception):
        pykotor_path = pathlib.Path(__file__).parents[3] / "Libraries" / "PyKotor" / "src" / "pykotor"
        if pykotor_path.exists():
            update_sys_path(pykotor_path.parent)
    with contextlib.suppress(Exception):
        utility_path = pathlib.Path(__file__).parents[3] / "Libraries" / "Utility" / "src" / "utility"
        if utility_path.exists():
            update_sys_path(utility_path.parent)


from pykotor.common.misc import Game
from pykotor.common.stream import BinaryReader
from pykotor.tools.encoding import decode_bytes_with_fallbacks
from pykotor.tools.path import CaseAwarePath, find_kotor_paths_from_default
from pykotor.tslpatcher.logger import PatchLog, PatchLogger
from pykotor.tslpatcher.patcher import ModInstaller
from pykotor.tslpatcher.reader import ConfigReader, NamespaceReader
from pykotor.tslpatcher.uninstall import ModUninstaller
from utility.error_handling import format_exception_with_variables, universal_simplify_exception
from utility.string import striprtf
from utility.system.path import Path
from utility.tkinter.tooltip import ToolTip

if TYPE_CHECKING:

    from types import TracebackType

    from pykotor.tslpatcher.namespaces import PatcherNamespace

CURRENT_VERSION: tuple[int, ...] = (1, 5, 0)
VERSION_LABEL = f"v{'.'.join(map(str, CURRENT_VERSION))}"


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

class HoloPatcherError(Exception):
    ...


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
        except ValueError as e:
            print(universal_simplify_exception(e), file=sys.stderr)  # noqa: T201
            print(f"Invalid namespace_option_index. It should be an integer, got {kwargs.namespace_option_index}", file=sys.stderr)  # noqa: T201
            sys.exit(ExitCode.NAMESPACE_INDEX_OUT_OF_RANGE)

    return kwargs

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"HoloPatcher {VERSION_LABEL}")
        self.set_window(width=400, height=500)

        self.install_running: bool = False
        self.task_running: bool = False
        self.mod_path: str = ""
        self.namespaces: list[PatcherNamespace] = []

        self.initialize_logger()
        self.initialize_top_menu()
        self.initialize_ui_controls()

        # Map the title bar's X button to our handle_exit_button function.
        # This probably also means this will be called when attempting to 'End Task' in e.g. task manager.
        self.protocol("WM_DELETE_WINDOW", self.handle_exit_button)

        cmdline_args: Namespace = parse_args()
        self.open_mod(cmdline_args.tslpatchdata or Path.cwd())
        self.handle_commandline(cmdline_args)

    def set_window(
        self,
        width: int,
        height: int,
    ):
        # Get screen dimensions
        screen_width: int = self.winfo_screenwidth()
        screen_height: int = self.winfo_screenheight()

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

    def initialize_top_menu(self):
        # Initialize top menu bar
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)

        # Tools menu
        tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        tools_menu.add_command(label="Validate INI", command=self.test_reader)
        tools_menu.add_command(label="Uninstall Mod / Restore Backup", command=self.uninstall_selected_mod)
        tools_menu.add_command(label="Fix permissions to file/folder...", command=self.fix_permissions)
        tools_menu.add_command(label="Fix iOS Case Sensitivity", command=self.lowercase_files_and_folders)
        tools_menu.add_command(label="Create info.rte...", command=self.create_rte_content)
        self.menu_bar.add_cascade(label="Tools", menu=tools_menu)

        # Help menu
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)

        # DeadlyStream submenu
        deadlystream_menu = tk.Menu(help_menu, tearoff=0)
        deadlystream_menu.add_command(label="Discord", command=lambda: webbrowser.open_new("https://discord.gg/nDkHXfc36s"))
        deadlystream_menu.add_command(label="Website", command=lambda: webbrowser.open_new("https://deadlystream.com"))
        help_menu.add_cascade(label="DeadlyStream", menu=deadlystream_menu)

        # Neocities submenu
        neocities_menu = tk.Menu(help_menu, tearoff=0)
        neocities_menu.add_command(label="Discord", command=lambda: webbrowser.open_new("https://discord.com/invite/kotor"))
        neocities_menu.add_command(label="Website", command=lambda: webbrowser.open_new("https://kotor.neocities.org"))
        help_menu.add_cascade(label="KOTOR Community Portal", menu=neocities_menu)

        # PCGamingWiki submenu
        pcgamingwiki_menu = tk.Menu(help_menu, tearoff=0)
        pcgamingwiki_menu.add_command(label="KOTOR 1", command=lambda: webbrowser.open_new("https://www.pcgamingwiki.com/wiki/Star_Wars:_Knights_of_the_Old_Republic"))
        pcgamingwiki_menu.add_command(label="KOTOR 2: TSL", command=lambda: webbrowser.open_new("https://www.pcgamingwiki.com/wiki/Star_Wars:_Knights_of_the_Old_Republic_II_-_The_Sith_Lords"))
        help_menu.add_cascade(label="PCGamingWiki", menu=pcgamingwiki_menu)

        # About menu
        about_menu = tk.Menu(self.menu_bar, tearoff=0)
        about_menu.add_command(label="Check for Updates", command=self.check_for_updates)
        about_menu.add_command(label="HoloPatcher Home", command=lambda: webbrowser.open_new("https://deadlystream.com/files/file/2243-holopatcher"))
        about_menu.add_command(label="GitHub Source", command=lambda: webbrowser.open_new("https://github.com/NickHugi/PyKotor"))
        self.menu_bar.add_cascade(label="About", menu=about_menu)

    def initialize_ui_controls(self):
        # Use grid layout for main window
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Configure style for Combobox
        ttk.Style(self).configure("TCombobox", font=("Helvetica", 10), padding=4)

        # Top area for comboboxes and buttons
        top_frame: tk.Frame = tk.Frame(self)
        top_frame.grid(row=0, column=0, sticky="ew")
        top_frame.grid_columnconfigure(0, weight=1)  # Make comboboxes expand
        top_frame.grid_columnconfigure(1, weight=0)  # Keep buttons fixed size

        # Setup the namespaces/changes ini combobox (selected mod)
        self.namespaces_combobox: ttk.Combobox = ttk.Combobox(top_frame, state="readonly", style="TCombobox")
        self.namespaces_combobox.grid(row=0, column=0, padx=5, pady=2, sticky="ew")
        self.namespaces_combobox.set("Select the mod to install")
        ToolTip(self.namespaces_combobox, lambda: self.get_namespace_description())
        self.namespaces_combobox.bind("<<ComboboxSelected>>", self.on_namespace_option_chosen)
        # Handle annoyances with Focus Events
        self.namespaces_combobox.bind("<FocusIn>", self.on_combobox_focus_in)
        self.namespaces_combobox.bind("<FocusOut>", self.on_combobox_focus_out)
        self.namespaces_combobox_state: int = 0
        # Browse for a tslpatcher mod
        self.browse_button: ttk.Button = ttk.Button(top_frame, text="Browse", command=self.open_mod)
        self.browse_button.grid(row=0, column=1, padx=5, pady=2, sticky="e")

        # Store all discovered KOTOR install paths
        self.gamepaths = ttk.Combobox(top_frame, style="TCombobox")
        self.gamepaths.set("Select your KOTOR directory path")
        self.gamepaths.grid(row=1, column=0, padx=5, pady=2, sticky="ew")
        self.gamepaths["values"] = [str(path) for game in find_kotor_paths_from_default().values() for path in game]
        self.gamepaths.bind("<<ComboboxSelected>>", self.on_gamepaths_chosen)
        # Browse for a KOTOR path
        self.gamepaths_browse_button = ttk.Button(top_frame, text="Browse", command=self.open_kotor)
        self.gamepaths_browse_button.grid(row=1, column=1, padx=5, pady=2, sticky="e")

        # Middle area for text and scrollbar
        text_frame = tk.Frame(self)
        text_frame.grid(row=1, column=0, sticky="nsew")
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)

        # Configure the text
        self.main_text = tk.Text(text_frame, wrap=tk.WORD)
        self.main_text.grid(row=0, column=0, sticky="nsew")
        self.set_text_font(self.main_text)

        # Create scrollbar for main frame
        scrollbar = tk.Scrollbar(text_frame, command=self.main_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.main_text.config(yscrollcommand=scrollbar.set)

        # Bottom area for buttons
        bottom_frame = tk.Frame(self)
        bottom_frame.grid(row=2, column=0, sticky="ew")

        self.exit_button = ttk.Button(bottom_frame, text="Exit", command=self.handle_exit_button)
        self.exit_button.pack(side="left", padx=5, pady=5)
        self.install_button = ttk.Button(bottom_frame, text="Install", command=self.begin_install)
        self.install_button.pack(side="right", padx=5, pady=5)
        self.simple_thread_event: Event = Event()

    def set_text_font(
        self,
        text_frame: tk.Text,
    ):
        font_obj = tkfont.Font(font=self.main_text.cget("font"))
        font_obj.configure(size=9)
        text_frame.configure(font=font_obj)

    def on_combobox_focus_in(
        self,
        event: tk.Event,
    ):
        if self.namespaces_combobox_state == 2: # no selection, fix the focus  # noqa: PLR2004
            self.focus_set()
            self.namespaces_combobox_state = 0  # base status
        else:
            self.namespaces_combobox_state = 1  # combobox clicked

    def on_combobox_focus_out(
        self,
        event: tk.Event,
    ):
        if self.namespaces_combobox_state == 1:
            self.namespaces_combobox_state = 2  # no selection

    def check_for_updates(self):
        try:
            import requests
            req: requests.Response = requests.get("https://api.github.com/repos/NickHugi/PyKotor/contents/update_info.json", timeout=15)
            req.raise_for_status()
            file_data: dict = req.json()
            base64_content: bytes = file_data["content"]
            decoded_content: bytes = base64.b64decode(base64_content)  # Correctly decoding the base64 content
            updateInfoData: dict = json.loads(decoded_content.decode("utf-8"))

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
                    f"You are already running the latest version of HoloPatcher ({VERSION_LABEL})",
                )
        except Exception as e:  # noqa: BLE001
            self._handle_general_exception(e, title="Unable to fetch latest version")

    def handle_commandline(
        self,
        cmdline_args: Namespace,
    ):
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
        num_cmdline_actions: int = sum([cmdline_args.install, cmdline_args.uninstall, cmdline_args.validate])
        if num_cmdline_actions == 1:
            self._begin_oneshot(cmdline_args)
        elif num_cmdline_actions > 1:
            messagebox.showerror("Invalid cmdline args passed", "Cannot run more than one of [--install, --uninstall, --validate]")
            sys.exit(ExitCode.NUMBER_OF_ARGS)


    def _begin_oneshot(
        self,
        cmdline_args: Namespace,
    ):
        self.one_shot = True
        self.withdraw()
        self.handle_console_mode()
        if cmdline_args.install:
            self.begin_install_thread(self.simple_thread_event)
        if cmdline_args.uninstall:
            self.uninstall_selected_mod()
        if cmdline_args.validate:
            self.test_reader()
        sys.exit(ExitCode.SUCCESS)

    def handle_console_mode(self):
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
                print(f"[Note] - {title}: {message}")  # noqa: T201

            @staticmethod
            def showwarning(title, message):
                print(f"[Warning] - {title}: {message}")  # noqa: T201

            @staticmethod
            def showerror(title, message):
                print(f"[Error] - {title}: {message}")  # noqa: T201

            @staticmethod
            def askyesno(title, message):
                """Console-based replacement for messagebox.askyesno and similar."""
                print(f"{title}\n{message}")  # noqa: T201
                while True:
                    response = input("(y/N)").lower().strip()
                    if response in ["yes", "y"]:
                        return True
                    if response in ["no", "n"]:
                        return False
                    print("Invalid input. Please enter 'yes' or 'no'")  # noqa: T201

        messagebox.showinfo = MessageboxOverride.showinfo  # type: ignore[assignment]
        messagebox.showwarning = MessageboxOverride.showwarning  # type: ignore[assignment]
        messagebox.showerror = MessageboxOverride.showerror  # type: ignore[assignment]
        # messagebox.askyesno = MessageboxOverride.askyesno
        # messagebox.askyesnocancel = MessageboxOverride.askyesno
        # messagebox.askretrycancel = MessageboxOverride.askyesno

    def hide_console(self):
        """Hide the console window in GUI mode."""
        # Windows
        if os.name == "nt":
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

    def uninstall_selected_mod(self):
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
        if not backup_parent_folder.safe_isdir():
            messagebox.showerror(
                "Backup folder empty/missing.",
                f"Could not find backup folder '{backup_parent_folder}'{os.linesep*2}Are you sure the mod is installed?",
            )
            return
        self.set_state(state=True)
        self.clear_main_text()
        fully_ran: bool = True
        try:
            uninstaller = ModUninstaller(backup_parent_folder, Path(self.gamepaths.get()), self.logger)
            fully_ran = uninstaller.uninstall_selected_mod()
        except Exception as e:  # noqa: BLE001
            self._handle_exception_during_install(e)
        finally:
            self.set_state(state=False)
            self.logger.add_note("Mod uninstaller/backup restore task completed.")
        if not fully_ran:
            self.on_namespace_option_chosen(tk.Event())

    def async_raise(self, tid, exctype):
        """Raises an exception in the threads with id tid."""
        if not inspect.isclass(exctype):
            raise TypeError("Only types can be raised (not instances)")
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid),
                                                        ctypes.py_object(exctype))
        if res == 0:
            raise ValueError("invalid thread id")
        if res != 1:
            # "if it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the effect"
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), None)
            raise SystemError("PyThreadState_SetAsyncExc failed")
        print("success")

    def handle_exit_button(self):
        """Handle exit button click during installation.

        Processing Logic:
        ----------------
            - Check if installation is running
            - Display confirmation dialog and check response
            - Try stopping install thread gracefully
            - If stopping fails, force terminate install thread
            - Destroy window and exit with abort code.
        """
        if not self.task_running or not self.install_thread.is_alive():
            print("Goodbye!")
            sys.exit(ExitCode.SUCCESS)

        # Handle unsafe exit.
        if self.install_running:
            if not messagebox.askyesno(
                "Really cancel the current installation? ",
                "CONTINUING WILL MOST LIKELY BREAK YOUR GAME AND REQUIRE A FULL KOTOR REINSTALL!",
            ):
                return
        else:
            if not messagebox.askyesno(
                "Really cancel the current task?",
                "A task is currently running. Exiting now may not be safe. Really continue?",
            ):
                return

        self.simple_thread_event.set()
        time.sleep(1)
        print("Install thread is still alive, attempting force close...")
        i = 0
        while self.install_thread.is_alive():
            try:
                self.install_thread._stop()  # type: ignore[attr-defined]
                print("force terminate of install thread succeeded", sys.stdout)  # noqa: T201
            except BaseException as e:  # noqa: BLE001
                self._handle_general_exception(e, "Error using self.install_thread._stop()", msgbox=False)
            try:
                self.async_raise(self.install_thread.ident, SystemExit)
            except BaseException as e:  # noqa: BLE001
                self._handle_general_exception(e, "Error using async_raise(self.install_thread.ident, SystemExit)", msgbox=False)
            print(f"Install thread is still alive after {i} seconds, waiting...")
            time.sleep(1)
            i += 1
            if i == 2:
                break
        if self.install_thread.is_alive():
            print("Failed to stop thread!")

        print("Destroying self")
        self.destroy()
        print("Goodbye! (sys.exit abort unsafe)")
        print("Nevermind, Forcefully kill this process (taskkill or kill command in subprocess)")
        pid = os.getpid()
        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], check=True)
            else:
                subprocess.run(["kill", "-9", str(pid)], check=True)
        except Exception as e:
            self._handle_general_exception(e, "Failed to kill process", msgbox=False)
        finally:
            # This code might not be reached, but it's here for completeness
            os._exit(ExitCode.ABORT_INSTALL_UNSAFE)

    def on_gamepaths_chosen(
        self,
        event: tk.Event,
    ):
        """Adjust the combobox after a short delay."""
        self.after(10, lambda: self.move_cursor_to_end(event.widget))

    def move_cursor_to_end(
        self,
        combobox: ttk.Combobox,
    ):
        """Shows the rightmost portion of the specified combobox as that's the most relevant."""
        combobox.focus_set()
        position: int = len(combobox.get())
        combobox.icursor(position)
        combobox.xview(position)
        self.focus_set()

    def get_namespace_description(self) -> str:
        """Show the expanded description from namespaces.ini when hovering over an option."""
        namespace_option: PatcherNamespace | None = next(
            (x for x in self.namespaces if x.name == self.namespaces_combobox.get()),
            None,
        )
        return namespace_option.description if namespace_option else ""

    def lowercase_files_and_folders(
        self,
        directory: os.PathLike | str | None = None,
        reset_namespace: bool = False,
    ):
        directory = directory or filedialog.askdirectory()
        if not directory:
            return

        try:
            def task():
                self.logger.add_note("Please wait, this may take awhile...")
                self.set_state(state=True)
                self.clear_main_text()
                try:
                    for root, dirs, files in os.walk(directory, topdown=False):
                        # Renaming files
                        for name in files:
                            file_path: Path = Path(root, name)
                            new_file_path: Path = Path(root, name.lower())
                            str_file_path = str(file_path)
                            str_new_file_path = str(new_file_path)
                            if str_file_path != str_new_file_path:
                                self.logger.add_note(f"Renaming {str_file_path} to '{new_file_path.name}'")
                                file_path.rename(new_file_path)

                        # Renaming directories
                        for name in dirs:
                            dir_path: Path = Path(root, name)
                            new_dir_path: Path = Path(root, name.lower())
                            str_dir_path = str(dir_path)
                            str_new_dir_path = str(new_dir_path)
                            if str_dir_path != str_new_dir_path:
                                self.logger.add_note(f"Renaming {str_dir_path} to '{new_dir_path.name}'")
                                dir_path.rename(str_new_dir_path)
                except Exception as e:
                    self._handle_general_exception(e)
                finally:
                    self.set_state(state=False)
                    self.logger.add_note("iOS case rename task completed.")

            self.install_thread = Thread(target=task)
            self.install_thread.start()
        except Exception as e2:
            self._handle_general_exception(e2)
        finally:
            if reset_namespace and self.mod_path:
                self.on_namespace_option_chosen(tk.Event())
            self.logger.add_verbose("iOS case rename task started.")

    def on_namespace_option_chosen(
        self,
        event: tk.Event,
        config_reader: ConfigReader | None = None,
    ):
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
            # Load the settings from the ini changes file.
            namespace_option: PatcherNamespace = next(x for x in self.namespaces if x.name == self.namespaces_combobox.get())
            changes_ini_path = CaseAwarePath(self.mod_path, "tslpatchdata", namespace_option.changes_filepath())
            reader: ConfigReader = config_reader or ConfigReader.from_filepath(changes_ini_path)
            reader.load_settings()

            # Filter the listed games in the combobox with the mod's supported ones.
            game_number: int | None = reader.config.game_number
            if game_number:
                game = Game(game_number)
                self.gamepaths["values"] = [
                    str(path)
                    for game_key in ([game] + ([Game.K1] if game == Game.K2 else []))
                    for path in find_kotor_paths_from_default()[game_key]
                ]

            # Strip info.rtf and display in the main window frame.
            info_rtf_path = CaseAwarePath(self.mod_path, "tslpatchdata", namespace_option.rtf_filepath())
            info_rte_path = CaseAwarePath(self.mod_path, "tslpatchdata", namespace_option.rtf_filepath()).with_suffix(".rte")
            if not info_rtf_path.safe_isfile() and not info_rte_path.safe_isfile():
                messagebox.showwarning("No info.rtf", f"Could not load the info rtf for this mod, file '{info_rtf_path}' not found on disk.")
                return
            if info_rte_path.safe_isfile():
                data: bytes = BinaryReader.load_file(info_rte_path)
                rtf_text: str = decode_bytes_with_fallbacks(data)
                self.load_rte_content(rtf_text)
            elif info_rtf_path.safe_isfile():
                data = BinaryReader.load_file(info_rtf_path)
                rtf_text = decode_bytes_with_fallbacks(data)
                self.set_stripped_rtf_text(rtf_text)
                #self.load_rtf_file(info_rtf_path)
        except Exception as e:  # noqa: BLE001
            self._handle_general_exception(e, "An unexpected error occurred while loading the patcher namespace.")
        else:
            self.after(10, lambda: self.move_cursor_to_end(self.namespaces_combobox))

    def _handle_general_exception(
        self,
        exc: BaseException,
        custom_msg: str = "Unexpected error.",
        title: str = "",
        msgbox: bool = True,
    ):
        detailed_msg = format_exception_with_variables(exc, message=custom_msg)
        print(detailed_msg)
        with Path.cwd().joinpath("errorlog.txt").open("a") as f:
            f.write(detailed_msg)
        error_name, msg = universal_simplify_exception(exc)
        if msgbox:
            messagebox.showerror(
                title or error_name,
                f"{(error_name + os.linesep*2) if title else ''}{custom_msg}.{os.linesep*2}{msg}",
            )

    def load_namespace(
        self,
        namespaces: list[PatcherNamespace],
        config_reader: ConfigReader | None = None,
    ):
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

    def open_mod(
        self,
        default_directory_path_str: os.PathLike | str | None = None,
    ):
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
            if default_directory_path_str is None:
                directory_path_str: os.PathLike | str = filedialog.askdirectory()
                if not directory_path_str:
                    return
            else:
                directory_path_str = default_directory_path_str

            tslpatchdata_path = CaseAwarePath(directory_path_str, "tslpatchdata")
            # handle when a user selects 'tslpatchdata' instead of mod root
            if not tslpatchdata_path.safe_isdir() and tslpatchdata_path.parent.name.lower() == "tslpatchdata":
                tslpatchdata_path = tslpatchdata_path.parent

            self.mod_path = str(tslpatchdata_path.parent)
            namespace_path: CaseAwarePath = tslpatchdata_path / "namespaces.ini"
            changes_path: CaseAwarePath = tslpatchdata_path / "changes.ini"

            if namespace_path.safe_isfile():
                self.load_namespace(NamespaceReader.from_filepath(namespace_path))
            elif changes_path.safe_isfile():
                config_reader: ConfigReader = ConfigReader.from_filepath(changes_path)
                namespaces: list[PatcherNamespace] = [config_reader.config.as_namespace(changes_path)]
                self.load_namespace(namespaces, config_reader)
            else:
                self.mod_path = ""
                if not default_directory_path_str:  # don't show the error if the cwd was attempted
                    messagebox.showerror("Error", "Could not find a mod located at the given folder.")
                return
            self.check_access(tslpatchdata_path, recurse=True)
        except Exception as e:  # noqa: BLE001
            self._handle_general_exception(e, "An unexpected error occurred while loading the mod info.")
        else:
            if default_directory_path_str:
                self.browse_button.place_forget()
            if not namespace_path.safe_isfile():
                self.namespaces_combobox.place_forget()

    def open_kotor(
        self,
        default_kotor_dir_str: os.PathLike | str | None = None,
    ):
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
            directory_path_str: os.PathLike | str = default_kotor_dir_str or filedialog.askdirectory()
            if not directory_path_str:
                return
            directory = CaseAwarePath(directory_path_str)
            self.check_access(directory)
            directory_str = str(directory)
            self.gamepaths.set(str(directory))
            if directory_str not in self.gamepaths["values"]:
                self.gamepaths["values"] = (*self.gamepaths["values"], directory_str)
            self.after(10, self.move_cursor_to_end, self.namespaces_combobox)
        except Exception as e:  # noqa: BLE001
            self._handle_general_exception(e, "An unexpected error occurred while loading the game directory.")

    def fix_permissions(
        self,
        directory: os.PathLike | str | None = None,
        reset_namespace: bool = False,
    ):
        path_arg = filedialog.askdirectory() if directory is None else directory
        if not path_arg:
            return

        try:
            path: Path = Path.pathify(path_arg)
            def task():
                self.set_state(state=True)
                self.clear_main_text()
                self.logger.add_note("Please wait, this may take awhile...")
                try:
                    access = path.gain_access(recurse=True, log_func=self.logger.add_note)
                    if access:
                        messagebox.showinfo("Successfully acquired permission", "The operation was successful.")
                    else:
                        messagebox.showerror("Could not acquire permission!", "Permissions denied! Check the logs for more details.")
                except Exception as e:
                    self._handle_general_exception(e)
                finally:
                    self.set_state(state=False)
                    self.logger.add_note("File/Folder permissions fixer task completed.")
            self.install_thread = Thread(target=task)
            self.install_thread.start()
        except Exception as e2:
            self._handle_general_exception(e2)
        finally:
            if reset_namespace and self.mod_path:
                self.on_namespace_option_chosen(tk.Event())
            self.logger.add_verbose("Started the File/Folder permissions fixer task.")

    def check_access(
        self,
        directory: Path,
        *,
        recurse: bool = False,
    ) -> bool:
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
        if directory.has_access(recurse=recurse):
            return True
        if (
            messagebox.askyesno(
                "Permission error",
                f"HoloPatcher does not have permissions to the path '{directory}', would you like to attempt to gain permission automatically?",
            ) or not self.fix_permissions(directory, reset_namespace=True)
        ):
            messagebox.showerror(
                "Could not gain permission!",
                "Please run HoloPatcher with elevated permissions, and ensure the selected folder exists and is writeable.",
            )
            return False
        if not directory.has_access(recurse=recurse):
            return messagebox.askyesno(
                "Unauthorized",
                (
                    f"HoloPatcher needs permissions to access '{directory}'. {os.linesep}"
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

        def _if_missing(title: str, message: str):
            messagebox.showinfo(title, message)
            if self.one_shot:
                sys.exit(ExitCode.NUMBER_OF_ARGS)
            return False

        if self.task_running:
            messagebox.showinfo(
                "Task already running",
                "Wait for the previous task to finish.",
            )
            return False
        if not self.mod_path or not CaseAwarePath(self.mod_path).safe_isdir():
            return _if_missing(
                "No mod chosen",
                "Select your mod directory first.",
            )
        game_path: str = self.gamepaths.get()
        if not game_path:
            return _if_missing(
                "No KOTOR directory chosen",
                "Select your KOTOR directory first.",
            )
        case_game_path = CaseAwarePath(game_path)
        if not case_game_path.safe_isdir():
            return _if_missing(
                "Invalid KOTOR directory chosen",
                "Select a valid path to your KOTOR install.",
            )
        game_path_str = str(case_game_path)
        self.gamepaths.set(game_path_str)
        return self.check_access(Path(game_path_str))

    def begin_install(self):
        """Starts the installation process in a background thread.

        Note: This function is not called when utilizing the CLI due to the thread creation - for passthrough purposes.

        Processing Logic:
        ----------------
            - Starts a new Thread to run the installation in the background
            - Catches any exceptions during thread start and displays error message
            - Exits program if exception occurs during installation thread start.

        """
        try:
            if not self.preinstall_validate_chosen():
                return
            self.install_thread = Thread(target=self.begin_install_thread, args=(self.simple_thread_event,))
            self.install_thread.start()
        except Exception as e:  # noqa: BLE001
            self._handle_general_exception(e, "An unexpected error occurred during the installation and the program was forced to exit")
            sys.exit(ExitCode.EXCEPTION_DURING_INSTALL)

    def begin_install_thread(self, should_cancel_thread: Event):
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
            - Finally set the install status to not running.
        """
        namespace_option: PatcherNamespace = next(x for x in self.namespaces if x.name == self.namespaces_combobox.get())
        ini_file_path = CaseAwarePath(self.mod_path, "tslpatchdata", namespace_option.changes_filepath())
        namespace_mod_path: CaseAwarePath = ini_file_path.parent

        self.set_state(state=True)
        self.install_running = True
        self.clear_main_text()
        try:
            installer = ModInstaller(namespace_mod_path, self.gamepaths.get(), ini_file_path, self.logger)
            self._execute_mod_install(installer, should_cancel_thread)
        except Exception as e:  # noqa: BLE001
            self._handle_exception_during_install(e)
        finally:
            self.set_state(state=False)
            self.install_running = False

    def test_reader(self):  # sourcery skip: no-conditionals-in-tests
        if not self.preinstall_validate_chosen():
            return
        namespace_option: PatcherNamespace = next(x for x in self.namespaces if x.name == self.namespaces_combobox.get())
        ini_file_path = CaseAwarePath(self.mod_path, "tslpatchdata", namespace_option.changes_filepath())

        self.set_state(state=True)
        self.clear_main_text()
        def task():
            try:
                reader = ConfigReader.from_filepath(ini_file_path, self.logger)
                reader.load(reader.config)
            except Exception as e:  # noqa: BLE001
                self._handle_general_exception(e, "An unexpected error occurred while testing the config ini reader")
            finally:
                self.set_state(state=False)
                self.logger.add_note("Config reader test is complete.")
        Thread(target=task).start()

    def set_state(
        self,
        state: bool,
    ):
        """Sets the active thread task state. Disables UI controls until this function is called again with run=False.

        Args:
        ----
            run: Whether the task is starting/running or not

        Processing Logic:
        ----------------
            - Sets the task_running attribute based on the run argument
            - Configures the state of relevant buttons to disabled if a thread task is running, normal otherwise
            - Handles enabling/disabling buttons during task process.
        """
        if state:
            self.task_running = True
            self.install_button.config(state=tk.DISABLED)
            self.gamepaths_browse_button.config(state=tk.DISABLED)
            self.browse_button.config(state=tk.DISABLED)
        else:
            self.task_running = False
            self.initialize_logger()  # reset the errors/warnings etc
            self.install_button.config(state=tk.NORMAL)
            self.gamepaths_browse_button.config(state=tk.NORMAL)
            self.browse_button.config(state=tk.NORMAL)

    def clear_main_text(self):
        self.main_text.config(state=tk.NORMAL)
        self.main_text.delete(1.0, tk.END)
        self.main_text.config(state=tk.DISABLED)

    def _execute_mod_install(
        self,
        installer: ModInstaller,
        should_cancel_thread: Event,
    ):
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
        confirm_msg: str = installer.config().confirm_message.strip()
        if confirm_msg and not self.one_shot and confirm_msg != "N/A" and not messagebox.askokcancel("This mod requires confirmation", confirm_msg):
            return
        #profiler = cProfile.Profile()
        #profiler.enable()
        install_start_time: datetime = datetime.now(timezone.utc).astimezone()
        installer.install(should_cancel_thread)
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

        num_errors: int = len(self.logger.errors)
        num_warnings: int = len(self.logger.warnings)
        num_patches: int = installer.config().patch_count()
        self.logger.add_note(
            f"The installation is complete with {num_errors} errors and {num_warnings} warnings.{os.linesep}"
            f"Total install time: {time_str}{os.linesep}"
            f"Total patches: {num_patches}",
        )
        if num_errors > 0:
            messagebox.showerror(
                "Install completed with errors!",
                f"The install completed with {num_errors} errors and {num_warnings} warnings! The installation may not have been successful, check the logs for more details."
                f"{os.linesep*2}Total install time: {time_str}"
                f"{os.linesep}Total patches: {num_patches}",
            )
            if self.one_shot:
                sys.exit(ExitCode.INSTALL_COMPLETED_WITH_ERRORS)
        elif num_warnings > 0:
            messagebox.showwarning(
                "Install completed with warnings",
                f"The install completed with {num_warnings} warnings! Review the logs for details. The script in the 'uninstall' folder of the mod directory will revert these changes."
                f"{os.linesep*2}Total install time: {time_str}"
                f"{os.linesep}Total patches: {num_patches}",
            )
        else:
            messagebox.showinfo(
                "Install complete!",
                f"Check the logs for details on what has been done. Utilize the script in the 'uninstall' folder of the mod directory to revert these changes."
                f"{os.linesep*2}Total install time: {time_str}"
                f"{os.linesep}Total patches: {num_patches}",
            )
            if self.one_shot:
                sys.exit(ExitCode.SUCCESS)

    @property
    def log_file_path(self) -> Path:
        return Path.pathify(self.mod_path) / "installlog.txt"

    def _handle_exception_during_install(
        self,
        e: Exception,
    ) -> NoReturn:
        """Handles exceptions during installation.

        Args:
        ----
            e: Exception - The exception raised

        Processing Logic:
        ----------------
            - Simplifies the exception for error name and message
            - Writes the error message to the log
            - Writes the full installer log to a file
            - Shows an error message box with the error name and message
            - Sets the install flag to False
            - Reraises the exception.
        """
        with self.log_file_path.open("a", encoding="utf-8") as log_file:
            log_file.write(f"{traceback.format_exc()}\n")
        error_name, msg = universal_simplify_exception(e)
        self.logger.add_error(f"{error_name}: {msg}{os.linesep}The installation was aborted with errors")
        messagebox.showerror(
            error_name,
            f"An unexpected error occurred during the installation and the installation was forced to terminate.{os.linesep*2}{msg}",
        )
        raise

    def create_rte_content(self, event: tk.Tk | None = None):
        from utility.tkinter.rte_editor import main as start_rte_editor
        start_rte_editor()

    def load_rte_content(self, rte_content: str | bytes | bytearray | None = None):
        from utility.tkinter.rte_editor import tag_types
        if rte_content is None:
            file_path_str = filedialog.askopenfilename()
            if not file_path_str:
                return
            with Path(file_path_str).open("rb") as f:
                rte_encoded_data: bytes = f.read()
            rte_content = decode_bytes_with_fallbacks(rte_encoded_data)

        document = json.loads(rte_content)

        # Clear existing content in the Text widget
        self.main_text.delete("1.0", tk.END)

        # Insert new content
        self.main_text.insert("1.0", document["content"])

        # Apply styles
        for tag_name, positions in document["tags"].items():
            for start_pos, end_pos in positions:
                self.main_text.tag_add(tag_name, start_pos, end_pos)

        # Configure tags based on tag_types
        for tag, config in tag_types.items():
            self.main_text.tag_configure(tag.lower(), **config)

    def load_rtf_file(self, file_path: os.PathLike | str):
        from utility.pyth3.plugins.plaintext.writer import PlaintextWriter
        from utility.pyth3.plugins.rtf15.reader import Rtf15Reader
        with open(file_path, "rb") as file:
            rtf_contents_as_utf8_encoded: bytes = decode_bytes_with_fallbacks(file.read()).encode()
            doc = Rtf15Reader.read(io.BytesIO(rtf_contents_as_utf8_encoded))
        self.main_text.config(state=tk.NORMAL)
        self.main_text.delete(1.0, tk.END)
        self.main_text.insert(tk.END, PlaintextWriter.write(doc).getvalue())
        self.main_text.config(state=tk.DISABLED)

    def set_stripped_rtf_text(
        self,
        rtf_text: str,
    ):
        """Strips the info.rtf of all RTF related text and displays it in the UI."""
        stripped_content: str = striprtf(rtf_text)
        self.main_text.config(state=tk.NORMAL)
        self.main_text.delete(1.0, tk.END)
        self.main_text.insert(tk.END, stripped_content)
        self.main_text.config(state=tk.DISABLED)

    def write_log(
        self,
        log: PatchLog,
    ):
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
        self.main_text.insert(tk.END, log.formatted_message + os.linesep)
        self.main_text.see(tk.END)
        self.main_text.config(state=tk.DISABLED)
        with self.log_file_path.open("a", encoding="utf-8") as log_file:
            log_file.write(f"{log.formatted_message}\n")


def onAppCrash(
    etype: type[BaseException],
    e: BaseException,
    tback: TracebackType | None,
):
    title, short_msg = universal_simplify_exception(e)
    detailed_msg = format_exception_with_variables(e, etype, tback)
    print(detailed_msg)
    with Path.cwd().joinpath("errorlog.txt").open("a") as f:
        f.write(f"\n{detailed_msg}")

    root = tk.Tk()
    root.withdraw()  # Hide
    messagebox.showerror(title, short_msg)
    root.destroy()
    sys.exit()

sys.excepthook = onAppCrash


def is_frozen() -> bool:  # sourcery skip: assign-if-exp, boolean-if-exp-identity, reintroduce-else, remove-unnecessary-cast
    # Check for sys.frozen attribute
    if getattr(sys, "frozen", False):
        return True
    # Check if the executable is in a temp directory (common for frozen apps)
    if tempfile.gettempdir() in sys.executable:
        return True
    return False

def main():
    #if is_frozen():
    #    multiprocessing.freeze_support()
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
