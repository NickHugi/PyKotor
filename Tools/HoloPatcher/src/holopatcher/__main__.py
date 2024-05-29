from __future__ import annotations

import atexit
import ctypes
import inspect
import io
import json
import os
import pathlib
import platform
import subprocess
import sys
import tempfile
import time
import tkinter as tk
import webbrowser

from argparse import ArgumentParser
from contextlib import suppress
from datetime import datetime, timezone
from enum import IntEnum
from multiprocessing import Queue
from threading import Event, Thread
from tkinter import (
    filedialog,
    font as tkfont,
    messagebox,
    ttk,
)
from types import TracebackType
from typing import TYPE_CHECKING, Any, NoReturn


def is_frozen() -> bool:
    return (
        getattr(sys, "frozen", False)
        or getattr(sys, "_MEIPASS", False)
        or tempfile.gettempdir() in sys.executable
    )


if not is_frozen():

    def update_sys_path(path):
        working_dir = str(path)
        if working_dir not in sys.path:
            sys.path.append(working_dir)

    with suppress(Exception):
        pykotor_path = pathlib.Path(__file__).parents[3] / "Libraries" / "PyKotor" / "src" / "pykotor"
        if pykotor_path.exists():
            update_sys_path(pykotor_path.parent)
    with suppress(Exception):
        utility_path = pathlib.Path(__file__).parents[3] / "Libraries" / "Utility" / "src" / "utility"
        if utility_path.exists():
            update_sys_path(utility_path.parent)
    with suppress(Exception):
        update_sys_path(pathlib.Path(__file__).parents[1])


from holopatcher.config import CURRENT_VERSION, getRemoteHolopatcherUpdateInfo, remoteVersionNewer
from pykotor.common.misc import Game
from pykotor.common.stream import BinaryReader
from pykotor.extract.file import ResourceIdentifier
from pykotor.tools.encoding import decode_bytes_with_fallbacks
from pykotor.tools.path import CaseAwarePath, find_kotor_paths_from_default
from pykotor.tslpatcher.config import LogLevel
from pykotor.tslpatcher.logger import LogType, PatchLogger
from pykotor.tslpatcher.patcher import ModInstaller
from pykotor.tslpatcher.reader import ConfigReader, NamespaceReader
from pykotor.tslpatcher.uninstall import ModUninstaller
from utility.error_handling import universal_simplify_exception
from utility.logger_util import RobustRootLogger
from utility.misc import ProcessorArchitecture
from utility.string_util import striprtf
from utility.system.os_helper import terminate_main_process, win_get_system32_dir
from utility.system.path import Path
from utility.tkinter.tooltip import ToolTip
from utility.tkinter.updater import TkProgressDialog

if TYPE_CHECKING:
    from argparse import Namespace
    from collections.abc import Callable
    from datetime import timedelta
    from multiprocessing import Process

    from pykotor.tslpatcher.logger import PatchLog
    from pykotor.tslpatcher.namespaces import PatcherNamespace

VERSION_LABEL = f"v{CURRENT_VERSION}"


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
    CRASH = 9
    CLOSE_FOR_UPDATE_PROCESS = 10


class HoloPatcherError(Exception): ...


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
    parser.add_argument("--namespace-option-index", type=int, help="Namespace option index")
    parser.add_argument("--console", action="store_true", help="Show the console when launching HoloPatcher.")
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


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"HoloPatcher {VERSION_LABEL}")

        self.set_window(width=400, height=500)

        # Map the title bar's X button to our handle_exit_button function.
        # This probably also means this will be called when attempting to 'End Task' in e.g. task manager.
        self.root.protocol("WM_DELETE_WINDOW", self.handle_exit_button)

        self.install_running: bool = False
        self.task_running: bool = False
        self.task_thread: Thread | None = None
        self.mod_path: str = ""
        self.log_level: LogLevel = LogLevel.WARNINGS
        self.pykotor_logger = RobustRootLogger()
        self.namespaces: list[PatcherNamespace] = []
        self.one_shot: bool = False

        self.initialize_logger()
        self.initialize_top_menu()
        self.initialize_ui_controls()

        cmdline_args: Namespace = parse_args()
        self.open_mod(cmdline_args.tslpatchdata or Path.cwd())
        self.execute_commandline(cmdline_args)
        self.pykotor_logger.debug("Init complete")

    def set_window(
        self,
        width: int,
        height: int,
    ):
        # Get screen dimensions
        screen_width: int = self.root.winfo_screenwidth()
        screen_height: int = self.root.winfo_screenheight()

        # Calculate position to center the window
        x_position = int((screen_width / 2) - (width / 2))
        y_position = int((screen_height / 2) - (height / 2))

        # Set the dimensions and position
        self.root.geometry(f"{width}x{height}+{x_position}+{y_position}")
        self.root.resizable(width=True, height=True)
        self.root.minsize(width=width, height=height)

    def initialize_logger(self):
        self.logger = PatchLogger()
        self.logger.verbose_observable.subscribe(self.write_log)
        self.logger.note_observable.subscribe(self.write_log)
        self.logger.warning_observable.subscribe(self.write_log)
        self.logger.error_observable.subscribe(self.write_log)

    def initialize_top_menu(self):
        # Initialize top menu bar
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

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
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Configure style for Combobox
        ttk.Style(self.root).configure("TCombobox", font=("Helvetica", 10), padding=4)

        # Top area for comboboxes and buttons
        top_frame: tk.Frame = tk.Frame(self.root)
        top_frame.grid(row=0, column=0, sticky="ew")
        top_frame.grid_columnconfigure(0, weight=1)  # Make comboboxes expand
        top_frame.grid_columnconfigure(1, weight=0)  # Keep buttons fixed size

        # Setup the namespaces/changes ini combobox (selected mod)
        self.namespaces_combobox: ttk.Combobox = ttk.Combobox(top_frame, state="readonly", style="TCombobox")
        self.namespaces_combobox.grid(row=0, column=0, padx=5, pady=2, sticky="ew")
        self.namespaces_combobox.set("Select the mod to install")
        ToolTip(self.namespaces_combobox, self.get_namespace_description)
        self.namespaces_combobox.bind("<<ComboboxSelected>>", self.on_namespace_option_chosen)
        # Handle annoyances with Focus Events
        self.namespaces_combobox.bind("<FocusIn>", self.on_combobox_focus_in)
        self.namespaces_combobox.bind("<FocusOut>", self.on_combobox_focus_out)
        self.namespaces_combobox_state: int = 0
        # Browse for a tslpatcher mod
        self.browse_button: ttk.Button = ttk.Button(top_frame, text="Browse", command=self.open_mod)
        self.browse_button.grid(row=0, column=1, padx=5, pady=2, sticky="e")
        self.expand_namespace_description_button: ttk.Button = ttk.Button(
            top_frame,
            width=1,
            text="?",
            command=lambda *args: messagebox.showinfo(
                self.namespaces_combobox.get(),
                self.get_namespace_description(*args),
            ),
        )
        self.expand_namespace_description_button.grid(row=0, column=2, padx=2, pady=2, stick="e")

        # Store all discovered KOTOR install paths
        self.gamepaths = ttk.Combobox(top_frame, style="TCombobox")
        self.gamepaths.set("Select your KOTOR directory path")
        self.gamepaths.grid(row=1, column=0, padx=5, pady=2, sticky="ew")
        self.gamepaths["values"] = [
            str(path)
            for game in find_kotor_paths_from_default().values()
            for path in game
        ]
        self.gamepaths.bind("<<ComboboxSelected>>", self.on_gamepaths_chosen)
        # Browse for a KOTOR path
        self.gamepaths_browse_button = ttk.Button(top_frame, text="Browse", command=self.open_kotor)
        self.gamepaths_browse_button.grid(row=1, column=1, padx=5, pady=2, sticky="e")

        # Middle area for text and scrollbar
        text_frame = tk.Frame(self.root)
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
        bottom_frame = tk.Frame(self.root)
        bottom_frame.grid(row=2, column=0, sticky="ew")

        self.exit_button = ttk.Button(bottom_frame, text="Exit", command=self.handle_exit_button)
        self.exit_button.pack(side="left", padx=5, pady=5)
        self.install_button = ttk.Button(bottom_frame, text="Install", command=self.begin_install)
        self.install_button.pack(side="right", padx=5, pady=5)
        self.simple_thread_event: Event = Event()
        self.progress_value = tk.IntVar(value=0)
        # Bottom area for buttons and progress bar
        bottom_frame = tk.Frame(self.root)
        bottom_frame.grid(row=2, column=0, sticky="ew")
        bottom_frame.grid_columnconfigure(0, weight=1)  # This will allow the progress bar to expand

        # Reconfigure the frame to use grid layout for better control
        self.exit_button = ttk.Button(bottom_frame, text="Exit", command=self.handle_exit_button)
        self.exit_button.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.install_button = ttk.Button(bottom_frame, text="Install", command=self.begin_install)
        self.install_button.grid(row=0, column=1, padx=5, pady=5, sticky="e")

        # Adjust the progress bar to span across the bottom frame
        self.progress_bar = ttk.Progressbar(bottom_frame, maximum=100, variable=self.progress_value)
        self.progress_bar.grid(row=1, column=0, columnspan=2, padx=5, pady=(0, 5), sticky="ew")

    def update_progress_bar_directly(
        self,
        value: int = 1,
    ):
        """Directly update the progress bar; this is the target callable for installer.install."""
        # Safely request an update from the Tkinter main thread
        self.root.after(0, self.update_progress_value, value)

    def update_progress_value(
        self,
        value: int = 1,
    ):
        """Actual update to the progress bar, guaranteed to run in the main thread."""
        new_value = self.progress_value.get() + value
        self.progress_value.set(new_value)
        self.progress_bar["value"] = new_value

    def set_text_font(
        self,
        text_frame: tk.Text,
    ):
        font_obj = tkfont.Font(font=text_frame.cget("font"))  # use the original font
        font_obj.configure(size=9)
        text_frame.configure(font=font_obj)

        # Define a bold and slightly larger font
        bold_font = tkfont.Font(font=text_frame.cget("font"))
        bold_font.configure(size=10, weight="bold")

        self.main_text.tag_configure("DEBUG", foreground="#6495ED")  # Cornflower Blue
        self.main_text.tag_configure("INFO", foreground="#000000")   # Black
        self.main_text.tag_configure("WARNING", foreground="#CC4E00", background="#FFF3E0", font=bold_font)  # Orange with bold font
        self.main_text.tag_configure("ERROR", foreground="#DC143C", font=bold_font)  # Firebrick with bold font
        self.main_text.tag_configure("CRITICAL", foreground="#FFFFFF", background="#8B0000", font=bold_font)  # White on Dark Red with bold font

    def on_combobox_focus_in(
        self,
        event: tk.Event,
    ):
        if self.namespaces_combobox_state == 2:  # no selection, fix the focus  # noqa: PLR2004
            self.root.focus_set()
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
            from utility.tkinter.updater import UpdateDialog
            updateInfoData: dict[str, Any] | Exception = getRemoteHolopatcherUpdateInfo()
            if isinstance(updateInfoData, Exception):
                self._handle_general_exception(updateInfoData)
                return
            latest_version = updateInfoData["holopatcherLatestVersion"]
            if remoteVersionNewer(CURRENT_VERSION, latest_version):
                dialog = UpdateDialog(
                    self.root,
                    "Update Available",
                    "A newer version of HoloPatcher is available, would you like to download it now?",
                    ["Update", "Manual"],
                )
                if dialog.result == "Update":
                    self._run_autoupdate(latest_version, updateInfoData)
                elif dialog.result == "Manual":
                    webbrowser.open_new(updateInfoData["holopatcherDownloadLink"])
            else:
                dialog = UpdateDialog(
                    self.root,
                    "No updates available.",
                    f"You are already running the latest version of HoloPatcher ({VERSION_LABEL})",
                    ["Reinstall"],
                )
                if dialog.result == "Reinstall":
                    self._run_autoupdate(latest_version, updateInfoData)
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            self._handle_general_exception(e, title="Unable to fetch latest version")

    def _run_autoupdate(
        self,
        latest_version: str,
        remote_info: dict[str, Any],
        *,
        is_release: bool = True,
    ):
        from utility.tkinter.updater import run_tk_progress_dialog
        from utility.updater.restarter import RestartStrategy
        from utility.updater.update import AppUpdate
        proc_arch = ProcessorArchitecture.from_os()
        assert proc_arch == ProcessorArchitecture.from_python()
        os_name = platform.system()
        links: list[str] = []

        is_release = True  # TODO(th3w1zard1): remove this line when the beta version direct links are ready.
        if is_release:
            links = remote_info["holopatcherDirectLinks"][os_name][proc_arch.value]
        else:
            links = remote_info["holopatcherBetaDirectLinks"][os_name][proc_arch.value]

        progress_queue: Queue = Queue()
        progress_dialog: Process = run_tk_progress_dialog(progress_queue, "HoloPatcher is updating and will restart shortly...")
        def download_progress_hook(data: dict[str, Any], progress_queue: Queue = progress_queue):
            progress_queue.put(data)

        # Prepare the list of progress hooks with the method from ProgressDialog
        progress_hooks = [download_progress_hook]
        def exitapp(kill_self_here: bool):  # noqa: FBT001
            packaged_data = {"action": "shutdown", "data": {}}
            progress_queue.put(packaged_data)
            progress_queue.put({"action": "shutdown"})
            TkProgressDialog.monitor_and_terminate(progress_dialog)
            if kill_self_here:
                time.sleep(3)
                self.root.destroy()
                sys.exit(ExitCode.CLOSE_FOR_UPDATE_PROCESS)

        def remove_second_dot(s: str) -> str:
            if s.count(".") == 2:
                # Find the index of the second dot
                second_dot_index = s.find(".", s.find(".") + 1)
                # Remove the second dot by slicing and concatenating
                s = s[:second_dot_index] + s[second_dot_index + 1:]
            return f"v{s}-patcher"

        updater = AppUpdate(
            links,
            "HoloPatcher",
            CURRENT_VERSION,
            latest_version,
            downloader=None,
            progress_hooks=progress_hooks,
            exithook=exitapp,
            r_strategy=RestartStrategy.DEFAULT,
            version_to_tag_parser=remove_second_dot
        )
        try:
            progress_queue.put({"action": "update_status", "text": "Downloading update..."})
            updater.download(background=False)
            progress_queue.put({"action": "update_status", "text": "Restarting and Applying update..."})
            updater.extract_restart()
            progress_queue.put({"action": "update_status", "text": "Cleaning up..."})
            updater.cleanup()
        except Exception:  # noqa: BLE001
            RobustRootLogger().critical("Auto-update had an unexpected error", exc_info=True)
        #finally:
        #    exitapp(True)

    def execute_commandline(
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
        self.root.withdraw()
        self.setup_cli_messagebox_overrides()
        if not self.preinstall_validate_chosen():
            sys.exit(ExitCode.NUMBER_OF_ARGS)
        if cmdline_args.install:
            self.begin_install_thread(self.simple_thread_event)
        if cmdline_args.uninstall:
            self.uninstall_selected_mod()
        if cmdline_args.validate:
            self.test_reader()
        sys.exit(ExitCode.SUCCESS)

    def setup_cli_messagebox_overrides(self):
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
            def showinfo(title, message, **options):
                print(f"[Note] - {title}: {message}")  # noqa: T201

            @staticmethod
            def showwarning(title, message, **options):
                print(f"[Warning] - {title}: {message}")  # noqa: T201

            @staticmethod
            def showerror(title, message, **options):
                print(f"[Error] - {title}: {message}")  # noqa: T201

            @staticmethod
            def askyesno(title, message, **options):
                """Console-based replacement for messagebox.askyesno and similar."""
                print(f"{title}\n{message}")  # noqa: T201
                while True:
                    response = input("(y/N)").lower().strip()
                    if response in {"yes", "y"}:
                        return True
                    if response in {"no", "n"}:
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
                f"Could not find backup folder '{backup_parent_folder}'{os.linesep * 2}Are you sure the mod is installed?",
            )
            return
        self.set_state(state=True)
        self.clear_main_text()
        fully_ran: bool = True
        try:
            uninstaller = ModUninstaller(backup_parent_folder, Path(self.gamepaths.get()), self.logger)
            fully_ran = uninstaller.uninstall_selected_mod()
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            self._handle_exception_during_install(e)
        finally:
            self.set_state(state=False)
            self.logger.add_note("Mod uninstaller/backup restore task completed.")
        if not fully_ran:
            self.on_namespace_option_chosen(tk.Event())

    def async_raise(self, tid: int, exctype: type):
        """Raises an exception in the threads with id tid."""
        if not inspect.isclass(exctype):
            msg = "Only types can be raised (not instances)"
            raise TypeError(msg)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), ctypes.py_object(exctype))
        if res == 0:
            msg = "invalid thread id"
            raise ValueError(msg)
        if res != 1:
            # "if it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the effect"
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), None)
            msg = "PyThreadState_SetAsyncExc failed"
            raise SystemError(msg)
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
        if not self.task_running or not self.task_thread or not self.task_thread.is_alive():
            print("Goodbye!")
            sys.exit(ExitCode.SUCCESS)
            return  # leave here for the static type checkers

        # Handle unsafe exit.
        if self.install_running and not messagebox.askyesno(
            "Really cancel the current installation? ",
            "CONTINUING WILL MOST LIKELY BREAK YOUR GAME AND REQUIRE A FULL KOTOR REINSTALL!",
        ):
            return
        if self.task_running and not messagebox.askyesno(
            "Really cancel the current task?",
            "A task is currently running. Exiting now may not be safe. Really continue?",
        ):
            return
        self.simple_thread_event.set()
        time.sleep(1)
        print("Install thread is still alive, attempting force close...")
        i = 0
        while self.task_thread.is_alive():
            try:
                self.task_thread._stop()  # type: ignore[attr-defined]  # pylint: disable=protected-access
                print("force terminate of install thread succeeded")
            except BaseException as e:  # pylint: disable=W0718  # noqa: BLE001
                self._handle_general_exception(e, "Error using self.install_thread._stop()", msgbox=False)
            try:
                if self.task_thread.ident is None:
                    msg = "task ident is None, expected an int."
                    raise ValueError(msg)  # noqa: TRY301
                self.async_raise(self.task_thread.ident, SystemExit)
            except BaseException as e:  # pylint: disable=W0718  # noqa: BLE001
                self._handle_general_exception(e, "Error using async_raise(self.install_thread.ident, SystemExit)", msgbox=False)
            print(f"Install thread is still alive after {i} seconds, waiting...")
            time.sleep(1)
            i += 1
            if i == 2:
                break
        if self.task_thread.is_alive():
            print("Failed to stop thread!")

        print("Destroying self")
        self.root.destroy()
        print("Goodbye! (sys.exit abort unsafe)")
        print("Nevermind, Forcefully kill this process (taskkill or kill command in subprocess)")
        pid = os.getpid()
        try:
            if sys.platform == "win32":
                system32_path = win_get_system32_dir()
                subprocess.run([str(system32_path / "taskkill.exe"), "/F", "/PID", str(pid)], check=True)  # noqa: S603
            else:
                subprocess.run(["kill", "-9", str(pid)], check=True)
        except Exception as e:  # noqa: BLE001
            self._handle_general_exception(e, "Failed to kill process", msgbox=False)
        finally:
            # This code might not be reached, but it's here for completeness
            os._exit(ExitCode.ABORT_INSTALL_UNSAFE)

    def on_gamepaths_chosen(
        self,
        event: tk.Event,
    ):
        """Adjust the combobox after a short delay."""
        self.root.after(10, lambda: self.move_cursor_to_end(event.widget))

    def move_cursor_to_end(
        self,
        combobox: ttk.Combobox,
    ):
        """Shows the rightmost portion of the specified combobox as that's the most relevant."""
        combobox.focus_set()
        position: int = len(combobox.get())
        combobox.icursor(position)
        combobox.xview(position)
        self.root.focus_set()

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
                self.set_state(state=True)
                self.clear_main_text()
                self.logger.add_note("Please wait, this may take awhile...")
                made_change = False
                try:
                    for root, dirs, files in os.walk(str(directory), topdown=False):
                        # Renaming files
                        for file_name in files:
                            file_path: Path = Path(root, file_name)
                            new_file_path: Path = Path(root, file_name.lower())
                            str_file_path = str(file_path)
                            str_new_file_path = str(new_file_path)
                            if str_file_path != str_new_file_path:
                                self.logger.add_note(f"Renaming {str_file_path} to '{new_file_path.name}'")
                                file_path.rename(new_file_path)
                                made_change = True

                        # Renaming directories
                        for folder_name in dirs:
                            dir_path: Path = Path(root, folder_name)
                            new_dir_path: Path = Path(root, folder_name.lower())
                            str_dir_path = str(dir_path)
                            str_new_dir_path = str(new_dir_path)
                            if str_dir_path != str_new_dir_path:
                                self.logger.add_note(f"Renaming {str_dir_path} to '{new_dir_path.name}'")
                                dir_path.rename(str_new_dir_path)
                                made_change = True
                    Path(directory).rename(Path._fix_path_formatting(str(directory).lower()))
                except Exception as e:  # noqa: BLE001
                    self._handle_general_exception(e)
                finally:
                    self.set_state(state=False)
                    if not made_change:
                        self.logger.add_note("Nothing to change - all files/folders already correct case.")
                    self.logger.add_note("iOS case rename task completed.")

            self.task_thread = Thread(target=task)
            self.task_thread.start()
        except Exception as e2:  # noqa: BLE001
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
            self.log_level = reader.config.log_level

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
                rtf_text: str = decode_bytes_with_fallbacks(data, errors="replace")
                self.load_rte_content(rtf_text)
            elif info_rtf_path.safe_isfile():
                data = BinaryReader.load_file(info_rtf_path)
                rtf_text = decode_bytes_with_fallbacks(data, errors="replace")
                self.set_stripped_rtf_text(rtf_text)
                # self.load_rtf_file(info_rtf_path)
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            self._handle_general_exception(e, "An unexpected error occurred while loading the patcher namespace.")
        else:
            self.root.after(10, lambda: self.move_cursor_to_end(self.namespaces_combobox))

    def _handle_general_exception(
        self,
        exc: BaseException,
        custom_msg: str = "Unexpected error.",
        title: str = "",
        *,
        msgbox: bool = True,
    ):
        self.pykotor_logger.exception(custom_msg, exc_info=exc)
        error_name, msg = universal_simplify_exception(exc)
        if msgbox:
            messagebox.showerror(
                title or error_name,
                f"{(error_name + os.linesep * 2) if title else ''}{custom_msg}.{os.linesep * 2}{msg}",
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
            self.check_access(tslpatchdata_path, recurse=True, should_filter=True)
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
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
            self.root.after(10, self.move_cursor_to_end, self.namespaces_combobox)
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            self._handle_general_exception(e, "An unexpected error occurred while loading the game directory.")

    @staticmethod
    def play_complete_sound():
        if os.name == "nt":
            import winsound

            # Play the system "exclamation" sound
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)

    @staticmethod
    def play_error_sound():
        if os.name == "nt":
            import winsound

            # Play the system 'error' sound
            winsound.MessageBeep(winsound.MB_ICONHAND)

    def fix_permissions(
        self,
        directory: os.PathLike | str | None = None,
        reset_namespace: bool = False,
        check: bool = False,
    ):
        path_arg = filedialog.askdirectory() if directory is None else directory
        if not path_arg:
            return
        if not directory and not messagebox.askyesno("Warning!", "This is not a toy. Really continue?"):
            return

        try:
            path: Path = Path.pathify(path_arg)

            def task() -> bool:
                extra_msg: str = ""
                self.set_state(state=True)
                self.clear_main_text()
                self.logger.add_note("Please wait, this may take awhile...")
                try:
                    access: bool = path.gain_access(recurse=True, log_func=self.logger.add_verbose)
                    # self.play_complete_sound()
                    if not access:
                        if not directory:
                            messagebox.showerror("Could not acquire permission!", "Permissions denied! Check the logs for more details.")
                        else:
                            messagebox.showerror(
                                "Could not gain permission!",
                                f"Permission denied to {directory}. Please run HoloPatcher with elevated permissions, and ensure the selected folder exists and is writeable.",
                            )
                        return False
                    check_isdir: bool = path.is_dir()
                    num_files = 0
                    num_folders = 0
                    if check_isdir:
                        for entry in path.rglob("*"):
                            if entry.is_file():
                                num_files += 1
                            elif entry.is_dir():
                                num_folders += 1

                    if check_isdir:
                        extra_msg = f"{num_files} files and {num_folders} folders finished processing."
                        self.logger.add_note(extra_msg)
                    messagebox.showinfo("Successfully acquired permission", f"The operation was successful. {extra_msg}")

                except Exception as e:
                    self._handle_general_exception(e)
                    return False
                else:
                    return True
                finally:
                    self.set_state(state=False)
                    self.logger.add_note("File/Folder permissions fixer task completed.")

            self.task_thread = Thread(target=task)
            self.task_thread.start()
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
        should_filter: bool = False,
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
        filter_results: Callable[[Path], bool] | None = None  # type: ignore[reportGeneralTypeIssues]
        if should_filter:

            def filter_results(x: Path) -> bool:
                return not ResourceIdentifier.from_path(x).restype.is_invalid

        if directory.has_access(recurse=recurse, filter_results=filter_results):
            return True
        if messagebox.askyesno(
            "Permission error",
            f"HoloPatcher does not have permissions to the path '{directory}', would you like to attempt to gain permission automatically?",
        ):
            directory.gain_access(recurse=recurse)
            self.on_namespace_option_chosen(tk.Event())
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
        if self.task_running:
            messagebox.showinfo(
                "Task already running",
                "Wait for the previous task to finish.",
            )
            return False
        if not self.mod_path or not CaseAwarePath(self.mod_path).safe_isdir():
            messagebox.showinfo(
                "No mod chosen",
                "Select your mod directory first.",
            )
            return False
        game_path: str = self.gamepaths.get()
        if not game_path:
            messagebox.showinfo(
                "No KOTOR directory chosen",
                "Select your KOTOR directory first.",
            )
            return False
        case_game_path = CaseAwarePath(game_path)
        if not case_game_path.safe_isdir():
            messagebox.showinfo(
                "Invalid KOTOR directory chosen",
                "Select a valid path to your KOTOR install.",
            )
            return False
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
        self.pykotor_logger.debug("Call begin_install")
        try:
            if not self.preinstall_validate_chosen():
                return
            self.pykotor_logger.debug("Prevalidate finished, starting install thread")
            self.task_thread = Thread(target=self.begin_install_thread, args=(self.simple_thread_event, self.update_progress_bar_directly))
            self.task_thread.start()
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            self._handle_general_exception(e, "An unexpected error occurred during the installation and the program was forced to exit")
            sys.exit(ExitCode.EXCEPTION_DURING_INSTALL)

    def begin_install_thread(
        self,
        should_cancel_thread: Event,
        update_progress_func: Callable | None = None,
    ):
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
        self.pykotor_logger.debug("begin_install_thread reached")
        namespace_option: PatcherNamespace = next(x for x in self.namespaces if x.name == self.namespaces_combobox.get())
        tslpatchdata_path = CaseAwarePath(self.mod_path, "tslpatchdata")
        ini_file_path = tslpatchdata_path.joinpath(namespace_option.changes_filepath())
        namespace_mod_path: CaseAwarePath = ini_file_path.parent

        self.pykotor_logger.debug("set ui state")
        self.set_state(state=True)
        self.install_running = True
        self.clear_main_text()
        self.main_text.config(state=tk.NORMAL)
        self.main_text.insert(tk.END, f"Starting install...{os.linesep}")
        self.main_text.see(tk.END)
        self.main_text.config(state=tk.DISABLED)
        try:
            installer = ModInstaller(namespace_mod_path, self.gamepaths.get(), ini_file_path, self.logger)
            installer.tslpatchdata_path = tslpatchdata_path
            self._execute_mod_install(installer, should_cancel_thread, update_progress_func)
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
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
            except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
                self._handle_general_exception(e, "An unexpected error occurred while testing the config ini reader")
            finally:
                self.set_state(state=False)
                self.logger.add_note("Config reader test is complete.")

        Thread(target=task).start()

    def set_state(
        self,
        *,
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
            self.progress_bar["value"] = 0
            self.progress_bar["maximum"] = 100
            self.progress_value.set(0)
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
        for tag in self.main_text.tag_names():
            if tag not in ["sel"]:
                self.main_text.tag_delete(tag)
        self.main_text.config(state=tk.DISABLED)

    def _execute_mod_install(
        self,
        installer: ModInstaller,
        should_cancel_thread: Event,
        progress_update_func: Callable | None = None
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
        try:
            confirm_msg: str = installer.config().confirm_message.strip()
            if (
                confirm_msg
                and not self.one_shot
                and confirm_msg != "N/A"
                and not messagebox.askokcancel(
                    "This mod requires confirmation",
                    confirm_msg,
                )
            ):
                return
            if progress_update_func is not None:
                self.progress_bar["maximum"] = len(
                [
                    *installer.config().install_list,  # Note: TSLPatcher executes [InstallList] after [TLKList]
                    *installer.get_tlk_patches(installer.config()),
                    *installer.config().patches_2da,
                    *installer.config().patches_gff,
                    *installer.config().patches_nss,
                    *installer.config().patches_ncs,  # Note: TSLPatcher executes [CompileList] after [HACKList]
                    *installer.config().patches_ssf,
                ]
            )
            # profiler = cProfile.Profile()
            # profiler.enable()
            install_start_time: datetime = datetime.now(timezone.utc).astimezone()
            installer.install(should_cancel_thread, progress_update_func)
            total_install_time: timedelta = datetime.now(timezone.utc).astimezone() - install_start_time
            if progress_update_func is not None:
                self.progress_value.set(99)
                self.progress_bar["value"] = 99
                self.progress_bar["maximum"] = 100
                self.update_progress_bar_directly()
                self.root.update_idletasks()
            # profiler.disable()
            # profiler_output_file = Path("profiler_output.pstat").resolve()
            # profiler.dump_stats(str(profiler_output_file))

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
                    f"{os.linesep * 2}Total install time: {time_str}"
                    f"{os.linesep}Total patches: {num_patches}",
                )
                if self.one_shot:
                    sys.exit(ExitCode.INSTALL_COMPLETED_WITH_ERRORS)
            elif num_warnings > 0:
                messagebox.showwarning(
                    "Install completed with warnings",
                    f"The install completed with {num_warnings} warnings! Review the logs for details. The script in the 'uninstall' folder of the mod directory will revert these changes."
                    f"{os.linesep * 2}Total install time: {time_str}"
                    f"{os.linesep}Total patches: {num_patches}",
                )
            else:
                messagebox.showinfo(
                    "Install complete!",
                    f"Check the logs for details on what has been done. Utilize the script in the 'uninstall' folder of the mod directory to revert these changes."
                    f"{os.linesep * 2}Total install time: {time_str}"
                    f"{os.linesep}Total patches: {num_patches}",
                )
                if self.one_shot:
                    sys.exit(ExitCode.SUCCESS)
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            self._handle_general_exception(e, "An unexpected error occurred while testing the config ini reader")
        finally:
            self.set_state(state=False)
            self.logger.add_note("Config reader test is complete.")

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
        self.pykotor_logger.exception("Unhandled exception in HoloPatcher", exc_info=e)
        error_name, msg = universal_simplify_exception(e)
        self.logger.add_error(f"{error_name}: {msg}{os.linesep}The installation was aborted with errors")
        messagebox.showerror(
            error_name,
            f"An unexpected error occurred during the installation and the installation was forced to terminate.{os.linesep * 2}{msg}",
        )
        raise

    def create_rte_content(self, event: tk.Tk | None = None):
        from utility.tkinter.rte_editor import main as start_rte_editor

        start_rte_editor()

    def load_rte_content(
        self,
        rte_content: str | bytes | bytearray | None = None,
    ):
        self.clear_main_text()
        self.main_text.config(state=tk.NORMAL)
        if rte_content is None:
            file_path_str = filedialog.askopenfilename()
            if not file_path_str:
                return
            with Path(file_path_str).open("rb") as f:
                rte_encoded_data: bytes = f.read()
            rte_content = decode_bytes_with_fallbacks(rte_encoded_data)

        document = json.loads(rte_content)

        self.main_text.insert("1.0", document["content"])
        for tag in self.main_text.tag_names():
            if tag not in ["sel"]:
                self.main_text.tag_delete(tag)

        if "tag_configs" in document:
            for tag, config in document["tag_configs"].items():
                self.main_text.tag_configure(tag, **config)
        for tag_name in document["tags"]:
            for tag_range in document["tags"][tag_name]:
                self.main_text.tag_add(tag_name, *tag_range)
        self.main_text.config(state=tk.DISABLED)

    def load_rtf_file(self, file_path: os.PathLike | str):
        from utility.pyth3.plugins.plaintext.writer import PlaintextWriter
        from utility.pyth3.plugins.rtf15.reader import Rtf15Reader

        with Path.pathify(file_path).open("rb") as file:
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
        self.clear_main_text()
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
        def log_type_to_level() -> LogType:
            log_map: dict[LogLevel, LogType] = {
                LogLevel.ERRORS: LogType.WARNING,
                LogLevel.GENERAL: LogType.WARNING,
                LogLevel.FULL: LogType.VERBOSE,
                LogLevel.WARNINGS: LogType.NOTE,
                LogLevel.NOTHING: LogType.WARNING
            }
            return log_map[self.log_level]
        def log_to_tag(this_log: PatchLog) -> str:
            if this_log.log_type == LogType.NOTE:
                return "INFO"
            if this_log.log_type == LogType.VERBOSE:
                return "DEBUG"
            return this_log.log_type.name
        try:
            self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_file_path.open("a", encoding="utf-8") as log_file:
                log_file.write(f"{log.formatted_message}\n")
            if log.log_type.value < log_type_to_level().value:
                return
        except OSError as e:
            RobustRootLogger().error(f"Failed to write the log file at '{self.log_file_path}': {e.__class__.__name__}: {e}")

        self.main_text.config(state=tk.NORMAL)
        self.main_text.insert(tk.END, log.formatted_message + os.linesep, log_to_tag(log))
        self.main_text.see(tk.END)
        self.main_text.config(state=tk.DISABLED)


def onAppCrash(
    etype: type[BaseException],
    exc: BaseException,
    tback: TracebackType | None,
):
    title, short_msg = universal_simplify_exception(exc)
    if tback is None:
        with suppress(Exception):
            import inspect
            # Get the current stack frames
            current_stack = inspect.stack()
            if current_stack:
                # Reverse the stack to have the order from caller to callee
                current_stack = current_stack[1:][::-1]
                fake_traceback = None
                for frame_info in current_stack:
                    frame = frame_info.frame
                    fake_traceback = TracebackType(fake_traceback, frame, frame.f_lasti, frame.f_lineno)
                exc = exc.with_traceback(fake_traceback)
                # Now exc has a traceback :)
                tback = exc.__traceback__
    RobustRootLogger().error("Unhandled exception caught.", exc_info=(etype, exc, tback))

    with suppress(Exception):
        root = tk.Tk()
        root.withdraw()  # Hide
        messagebox.showerror(title, short_msg)
        root.destroy()
    sys.exit(ExitCode.CRASH)


sys.excepthook = onAppCrash


def my_cleanup_function(app: App):
    """Prevents the patcher from running in the background after sys.exit is called."""
    print("Fully shutting down HoloPatcher...")
    terminate_main_process()
    app.root.destroy()


def main():
    app = App()
    app.root.mainloop()
    atexit.register(lambda: my_cleanup_function(app))

def is_running_from_temp():
    app_path = Path(sys.executable)
    temp_dir = tempfile.gettempdir()
    return str(app_path).startswith(temp_dir)

if __name__ == "__main__":
    if is_running_from_temp():
        messagebox.showerror("Error", "This application cannot be run from within a zip or temporary directory. Please extract it to a permanent location before running.")
        sys.exit("Exiting: Application was run from a temporary or zip directory.")
    main()
