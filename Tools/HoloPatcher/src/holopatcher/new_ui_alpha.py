from __future__ import annotations

import asyncio
import atexit
import ctypes
import inspect
import json
import os
import pathlib
import platform
import queue
import subprocess
import sys
import tempfile
import time
import tkinter as tk
import webbrowser

from argparse import ArgumentParser
from contextlib import contextmanager, suppress
from datetime import datetime, timezone
from enum import IntEnum
from multiprocessing import Queue
from threading import Event, Thread
from tkinter import messagebox
from types import TracebackType
from typing import TYPE_CHECKING, Any, Coroutine, Generator, NoReturn, cast

import pypandoc
import toga

from toga import Group, Selection
from toga.command import Command
from toga.sources import ListSource
from toga.style import Pack
from toga.style.pack import CENTER, COLUMN, ROW
from toga.widgets.base import BaseStyle
from toga.window import Dialog


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
from utility.system.os_helper import terminate_main_process, win_get_system32_dir
from utility.system.path import Path
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


def show_update_dialog(window: toga.MainWindow, title: str, message: str, options: list[dict[str, Any]]):
    class UpdateDialog(toga.Box):  # TODO: move class to library code, for now keep nested in this function so it doesn't clutter the autoimport-completions
        def __init__(self, title: str, message: str, options: list[dict[str, Any]], *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.options: list[dict[str, Any]] = options
            cast(BaseStyle, self.style).update(direction=COLUMN, padding=10)

            # Title
            self.title_label: toga.Label = toga.Label(title, style=Pack(padding_bottom=10))
            self.add(self.title_label)

            # Message
            self.message_label: toga.Label = toga.Label(message, style=Pack(padding_bottom=10))
            self.add(self.message_label)

            # Buttons
            button_box: toga.Box = toga.Box(style=Pack(direction=ROW, padding_top=10))
            for option in options:
                button = toga.Button(option["label"], on_press=lambda widget, opt=option: self.handle_result(opt), style=Pack(padding=5))
                button_box.add(button)
            self.add(button_box)

        def handle_result(self, option: dict[str, Any]):
            if "callback" in option:
                option["callback"]()
            if self.window is None:
                return
            self.window.close()
    dialog = UpdateDialog(title, message, options)
    window.content = dialog
    window.show()


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


class HoloPatcher(toga.App):
    def startup(self):
        print("HoloPatcher.startup!!!\n\n\n")
        self.simple_thread_event = Event()
        self.web_view = toga.WebView(style=Pack(flex=1, padding=5))
        self.html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>WebView Content</title>
            <style>
                body {
                    font-family: 'Helvetica', sans-serif;
                    margin: 0;
                    padding: 0;
                    overflow: auto;
                    height: 100vh; /* Full height */
                    box-sizing: border-box;
                }
                #content {
                    padding: 10px;
                }
                .DEBUG { color: #6495ED; }
                .INFO { color: #000000; }
                .WARNING { color: #CC4E00; background-color: #FFF3E0; font-weight: bold; font-size: 10px; }
                .ERROR { color: #DC143C; font-weight: bold; font-size: 10px; }
                .CRITICAL { color: #FFFFFF; background-color: #8B0000; font-weight: bold; font-size: 10px; }
            </style>
        </head>
        <body>
            <div id="content"></div>
            <script>
                function setContent(newContent) {
                    document.getElementById('content').innerHTML = newContent;
                }
                function appendLogLine(logLine, logType) {
                    var container = document.getElementById('content');
                    var logElement = document.createElement('div');
                    logElement.className = logType;
                    logElement.innerHTML = logLine + '<br>';
                    container.appendChild(logElement);
                    if (container.children.length > 100) {
                        container.removeChild(container.firstChild);
                    }
                    window.scrollTo(0, document.body.scrollHeight);
                }
                function setFontColor(logType, color) {
                    var styleElement = document.createElement('style');
                    styleElement.innerHTML = '.' + logType + ' { color: ' + color + '; }';
                    document.head.appendChild(styleElement);
                }
            </script>
        </body>
        </html>
        """
        self.web_view.set_content("", self.html_template)
        self.main_window: toga.MainWindow = toga.MainWindow(title=f"HoloPatcher {VERSION_LABEL}")
        self.main_window.content = toga.Box(style=Pack(direction=COLUMN))
        self.on_exit = lambda widget, **kwargs: self.run_background_task(self.handle_exit_button()) or True

        self.set_window(width=400, height=500)

        self.install_running: bool = False
        self.task_running: bool = False
        self.task_thread: Thread | None = None
        self.mod_path: str = ""
        self.log_level: LogLevel = LogLevel.WARNINGS
        self.pykotor_logger: RobustRootLogger = RobustRootLogger()
        self.background_tasks: set[asyncio.Task[Any] | asyncio.Future[Any]] = set()  # To store references to tasks

        self.initialize_logger()
        self.initialize_top_menu()
        self.initialize_ui_controls()

        cmdline_args: Namespace = parse_args()
        print(f"init directory: {cmdline_args.tslpatchdata or Path.cwd()}")
        self.run_background_task(self.open_mod(cmdline_args.tslpatchdata or Path.cwd()))
        self.run_background_task(self.execute_commandline(cmdline_args))
        self.pykotor_logger.debug("Init complete")

    def run_background_task(self, coro: Coroutine[Any, Any, Any] | asyncio.Task[Any] | Dialog):
        """Utility method to run a coroutine as a background task and keep a reference to it."""
        if isinstance(coro, Coroutine):
            task = asyncio.run_coroutine_threadsafe(coro, self.loop)
        elif isinstance(coro, asyncio.Task):
            task = coro
        elif isinstance(coro, Dialog):
            task = asyncio.run_coroutine_threadsafe(coro, self.loop)
        else:
            # Directly ensure_future if it's not one of the above types
            task = asyncio.ensure_future(coro, loop=self.loop)

        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)

    def set_window(self, width: int, height: int):
        self.main_window.size = (width, height)

        # Get screen dimensions
        user32 = ctypes.windll.user32
        screen_width = user32.GetSystemMetrics(0)
        screen_height = user32.GetSystemMetrics(1)

        # Calculate position to center the window
        x_position = int((screen_width / 2) - (width / 2))
        y_position = int((screen_height / 2) - (height / 2))

        # Set the position of the window
        self.main_window.position = (x_position, y_position)

    def initialize_logger(self):
        self.logger = PatchLogger()
        self.logger.verbose_observable.subscribe(self.write_log)
        self.logger.note_observable.subscribe(self.write_log)
        self.logger.warning_observable.subscribe(self.write_log)
        self.logger.error_observable.subscribe(self.write_log)

    def initialize_top_menu(self):
        tools_group = Group("Tools")
        help_group = Group("Help")
        deadlystream_group = Group("DeadlyStream", parent=help_group)
        neocities_group = Group("KOTOR Community Portal", parent=help_group)
        pcgamingwiki_group = Group("PCGamingWiki", parent=help_group)
        about_group = Group("About")

        tools_menu = [
            Command(lambda command, **kwargs: self.run_background_task(self.test_reader()) or True, text="Validate INI", group=tools_group),  # noqa: ARG005
            Command(lambda command, **kwargs: self.run_background_task(self.uninstall_selected_mod()) or True, text="Uninstall Mod / Restore Backup", group=tools_group),
            Command(lambda command, **kwargs: self.run_background_task(self.fix_permissions()) or True, text="Fix permissions to file/folder...", group=tools_group),
            Command(lambda command, **kwargs: self.run_background_task(self.lowercase_files_and_folders()) or True, text="Fix iOS Case Sensitivity", group=tools_group),
            Command(lambda command, **kwargs: self.create_rte_content() or True, text="Create info.rte...", group=tools_group)
        ]

        help_menu = [
            Command(lambda command, **kwargs: webbrowser.open_new("https://discord.gg/nDkHXfc36s"), text="Discord", group=deadlystream_group),
            Command(lambda command, **kwargs: webbrowser.open_new("https://deadlystream.com"), text="Website", group=deadlystream_group),
            Command(lambda command, **kwargs: webbrowser.open_new("https://discord.com/invite/kotor"), text="Discord", group=neocities_group),
            Command(lambda command, **kwargs: webbrowser.open_new("https://kotor.neocities.org"), text="Website", group=neocities_group),
            Command(lambda command, **kwargs: webbrowser.open_new("https://www.pcgamingwiki.com/wiki/Star_Wars:_Knights_of_the_Old_Republic"), text="KOTOR 1", group=pcgamingwiki_group),
            Command(lambda command, **kwargs: webbrowser.open_new("https://www.pcgamingwiki.com/wiki/Star_Wars:_Knights_of_the_Old_Republic_II_-_The_Sith_Lords"), text="KOTOR 2: TSL", group=pcgamingwiki_group)
        ]

        about_menu = [
            Command(lambda command, **kwargs: self.check_for_updates() or True, text="Check for Updates", group=about_group),
            Command(lambda command, **kwargs: webbrowser.open_new("https://deadlystream.com/files/file/2243-holopatcher"), text="HoloPatcher Home", group=about_group),
            Command(lambda command, **kwargs: webbrowser.open_new("https://github.com/NickHugi/PyKotor"), text="GitHub Source", group=about_group)
        ]

        self.main_window.toolbar.add(*tools_menu)
        self.main_window.toolbar.add(*help_menu)
        self.main_window.toolbar.add(*about_menu)

    def initialize_ui_controls(self):
        assert self.main_window.content is not None
        top_box = toga.Box(style=Pack(direction=ROW, alignment=CENTER, padding=5))

        # Namespace/Mod row.
        self.namespaces_combobox = toga.Selection(items=[], style=Pack(flex=1, padding_right=5, font_size=10, padding=4), accessor="patcher_namespace")
        self.namespaces_combobox.on_change = self.on_namespace_option_chosen
        top_box.add(self.namespaces_combobox)
        self.browse_button = toga.Button("Browse", on_press=lambda *args, **kwargs: self.run_background_task(self.open_mod()), style=Pack(padding_right=5))
        top_box.add(self.browse_button)
        self.expand_namespace_description_button = toga.Button(
            "?",
            on_press=lambda _widget: self.run_background_task(
                self.main_window.info_dialog(
                    str(cast(PatcherNamespace, self.namespaces_combobox.value.patcher_namespace).name),
                    self.get_namespace_description()
                )
            ),
            style=Pack(padding_right=5, width=30)
        )
        top_box.add(self.expand_namespace_description_button)
        self.main_window.content.add(top_box)

        # KOTOR Install row.
        gamepaths_box = toga.Box(style=Pack(direction=ROW, alignment=CENTER, padding=5))
        self.gamepaths = toga.Selection(items=[], style=Pack(flex=1, padding_right=5, font_size=10, padding=4))
        gamepaths_box.add(self.gamepaths)
        self.gamepaths_browse_button = toga.Button("Browse", on_press=lambda *args, **kwargs: self.run_background_task(self.open_kotor()), style=Pack(padding_right=5))
        gamepaths_box.add(self.gamepaths_browse_button)
        self.main_window.content.add(gamepaths_box)

        # Main WebView for content display
        text_frame = toga.ScrollContainer(horizontal=False, vertical=True, style=Pack(flex=1))  # ScrollContainer to add scrollbars
        text_frame.content = self.web_view
        self.main_window.content.add(text_frame)

        # Bottom widgets.
        bottom_box = toga.Box(style=Pack(direction=ROW, padding=5, alignment=CENTER))
        self.exit_button = toga.Button("Exit", on_press=self.handle_exit_button, style=Pack(flex=1, padding=5))
        self.install_button = toga.Button("Install", on_press=lambda *args, **kwargs: self.run_background_task(self.begin_install()), style=Pack(flex=1, padding=5))
        bottom_box.add(self.exit_button)
        bottom_box.add(self.install_button)
        self.progress_value = 0
        self.progress_bar = toga.ProgressBar(max=100, value=self.progress_value, style=Pack(flex=1, padding_top=5))
        bottom_box.add(self.progress_bar)
        self.main_window.content.add(bottom_box)

        self.main_window.show()

    def update_progress_bar_directly(self, value: int = 1):
        self.progress_value += value
        self.progress_bar.value = self.progress_value

    def check_for_updates(self):
        try:
            updateInfoData: dict[str, Any] | Exception = getRemoteHolopatcherUpdateInfo()
            if isinstance(updateInfoData, Exception):
                self._handle_general_exception(updateInfoData)
                return
            latest_version = updateInfoData["holopatcherLatestVersion"]
            if remoteVersionNewer(CURRENT_VERSION, latest_version):
                result = show_update_dialog(
                    toga.MainWindow(title=f"Updater {VERSION_LABEL}"),
                    "Update Available",
                    "A newer version of HoloPatcher is available, would you like to download it now?",
                    [
                        {"label": "Update", "callback": lambda: self._run_autoupdate(latest_version, updateInfoData)},
                        {"label": "Manual", "callback": lambda: webbrowser.open_new(updateInfoData["holopatcherDownloadLink"])},
                        {"label": "Cancel"}
                    ]
                )
                if result == "Update":
                    self._run_autoupdate(latest_version, updateInfoData)
                elif result == "Manual":
                    webbrowser.open_new(updateInfoData["holopatcherDownloadLink"])
            else:
                result = show_update_dialog(
                    toga.MainWindow(title=f"Updater {VERSION_LABEL}"),
                    "No updates available.",
                    f"You are already running the latest version of HoloPatcher ({VERSION_LABEL})",
                    [
                        {"label": "Reinstall", "callback": lambda: self._run_autoupdate(latest_version, updateInfoData)},
                        {"label": "Cancel"}
                    ]
                )
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
                self.main_window.close()
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

    async def execute_commandline(
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
            await self.open_kotor(cmdline_args.game_dir)
        if cmdline_args.namespace_option_index:
            self.namespaces_combobox.value = self.namespaces_combobox.items[cmdline_args.namespace_option_index]
        if not cmdline_args.console:
            self.hide_console()

        self.one_shot: bool = False
        num_cmdline_actions: int = sum([cmdline_args.install, cmdline_args.uninstall, cmdline_args.validate])
        if num_cmdline_actions == 1:
            await self._begin_oneshot(cmdline_args)
        elif num_cmdline_actions > 1:
            await self.main_window.error_dialog("Invalid cmdline args passed", "Cannot run more than one of [--install, --uninstall, --validate]")
            sys.exit(ExitCode.NUMBER_OF_ARGS)

    async def _begin_oneshot(
        self,
        cmdline_args: Namespace,
    ):
        self.one_shot = True
        self.main_window.visible = False
        self.setup_cli_messagebox_overrides()
        if not await self.preinstall_validate_chosen():
            sys.exit(ExitCode.NUMBER_OF_ARGS)
        if cmdline_args.install:
            self.begin_install_thread(self.simple_thread_event)
        if cmdline_args.uninstall:
            await self.uninstall_selected_mod()
        if cmdline_args.validate:
            await self.test_reader()
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

    async def uninstall_selected_mod(self):
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
        if not await self.preinstall_validate_chosen():
            return
        backup_parent_folder = Path(self.mod_path, "backup")
        if not backup_parent_folder.safe_isdir():
            await self.main_window.error_dialog(
                "Backup Folder Empty/Missing.",
                f"Could not find backup folder '{backup_parent_folder}'{os.linesep * 2}Are you sure the mod is installed?",
            )
            return
        self.set_state(state=True)
        self.clear_main_text()
        fully_ran: bool = True
        try:
            uninstaller = ModUninstaller(backup_parent_folder, Path(self.gamepaths.value), self.logger)
            fully_ran = uninstaller.uninstall_selected_mod()
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            self._handle_exception_during_install(e)
        finally:
            self.set_state(state=False)
            self.logger.add_note("Mod Uninstaller/Backup Restore Task Completed.")
        if not fully_ran:
            self.on_namespace_option_chosen()

    def async_raise(self, tid: int, exctype: type):
        """Raises an exception in the threads with id tid."""
        if not inspect.isclass(exctype):
            msg = "Only types can be raised (not instances)"
            raise TypeError(msg)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), ctypes.py_object(exctype))
        if res == 0:
            msg = "Invalid thread id(0)"
            raise ValueError(msg)
        if res != 1:
            # "if it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the effect"
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), None)
            msg = "PyThreadState_SetAsyncExc FAILED"
            raise SystemError(msg)
        print("PyThreadState_SetAsyncExc SUCCESSFUL")

    async def handle_exit_button(self, unknown_toga_arg: Any | None = None):
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
            self.exit()
            sys.exit(ExitCode.SUCCESS)
            return  # leave here for the static type checkers

        # Handle unsafe exit.
        if self.install_running and not await self.main_window.confirm_dialog(
            "Really cancel the current installation? ",
            "CONTINUING WILL MOST LIKELY BREAK YOUR GAME AND REQUIRE A FULL KOTOR REINSTALL!",
        ):
            return
        if self.task_running and not await self.main_window.confirm_dialog(
            "Really cancel the current task?",
            "A task is currently running. Exiting now may not be safe. Really continue?",
        ):
            return
        self.simple_thread_event.set()
        await asyncio.sleep(1)
        print("Install thread is still alive, attempting force close...")
        i = 0
        while self.task_thread.is_alive():
            if hasattr(self.task_thread, "_stop") and callable(self.task_thread._stop):  # type: ignore[]  # noqa: SLF001
                try:
                    self.task_thread._stop()  # type: ignore[attr-defined]  # pylint: disable=protected-access  # noqa: SLF001
                    print("Force terminate of install thread succeeded")
                except BaseException as e:  # pylint: disable=W0718  # noqa: BLE001
                    self._handle_general_exception(e, "Error using self.install_thread._stop()", msgbox=False)
            try:
                if self.task_thread.ident is None:
                    msg = "Task ident is None, expected an int."
                    raise ValueError(msg)  # noqa: TRY301
                self.async_raise(self.task_thread.ident, SystemExit)
            except BaseException as e:  # pylint: disable=W0718  # noqa: BLE001
                self._handle_general_exception(e, "Error using async_raise(self.install_thread.ident, SystemExit)", msgbox=False)
            print(f"Install thread is still alive after {i} seconds, waiting...")
            await asyncio.sleep(1)
            i += 1
            if i == 2:
                break
        if self.task_thread.is_alive():
            print("Failed to stop thread!")

        print("Destroying self")
        self.main_window.close()
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

    def get_namespace_description(self) -> str:
        """Show the expanded description from namespaces.ini when hovering over an option."""
        namespace_option: PatcherNamespace | None = cast(PatcherNamespace, self.namespaces_combobox.value.patcher_namespace)
        return namespace_option.description if namespace_option else ""

    async def lowercase_files_and_folders(
        self,
        directory: os.PathLike | str | None = None,
        *,
        reset_namespace: bool = False,
    ):
        if not directory:
            directory = await self.main_window.select_folder_dialog("Select target directory")
            if directory is None:
                return  # User cancelled the dialog

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
                                self.logger.add_note(f"Renaming '{str_file_path}' to '{new_file_path.name}'")
                                file_path.rename(new_file_path)
                                made_change = True

                        # Renaming directories
                        for folder_name in dirs:
                            dir_path: Path = Path(root, folder_name)
                            new_dir_path: Path = Path(root, folder_name.lower())
                            str_dir_path = str(dir_path)
                            str_new_dir_path = str(new_dir_path)
                            if str_dir_path != str_new_dir_path:
                                self.logger.add_note(f"Renaming '{str_dir_path}' to '{new_dir_path.name}'")
                                dir_path.rename(str_new_dir_path)
                                made_change = True
                    Path(directory).rename(Path._fix_path_formatting(str(directory).lower()))  # noqa: SLF001
                except Exception as e:  # noqa: BLE001
                    self._handle_general_exception(e)
                finally:
                    self.set_state(state=False)
                    if not made_change:
                        self.logger.add_note("Nothing to change - all files/folders already correct case.")
                    self.logger.add_note("iOS case rename task completed.")

            self.task_thread = Thread(target=task, name="lowercase_tool_task")
            self.task_thread.start()
        except Exception as e2:  # noqa: BLE001
            self._handle_general_exception(e2)
        finally:
            if reset_namespace and self.mod_path:
                self.on_namespace_option_chosen()
            self.logger.add_verbose("iOS case rename task started.")

    def on_namespace_option_chosen(
        self,
        combobox: Selection | None = None,
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
            namespace_option: PatcherNamespace = self.namespaces_combobox.value.patcher_namespace
            changes_ini_path = CaseAwarePath(self.mod_path, "tslpatchdata", namespace_option.changes_filepath())
            reader: ConfigReader = config_reader or ConfigReader.from_filepath(changes_ini_path)
            reader.load_settings()
            self.log_level = reader.config.log_level

            # Filter the listed games in the combobox with the mod's supported ones.
            game_number: int | None = reader.config.game_number
            if game_number:
                game = Game(game_number)
                supported_paths = [
                    str(path)
                    for game_key in ([game] + ([Game.K1] if game == Game.K2 else []))
                    for path in find_kotor_paths_from_default()[game_key]
                ]
                self.gamepaths.items = supported_paths
                self.gamepaths.value = supported_paths[0] if supported_paths else None

            # Strip info.rtf and display in the main window frame.
            info_rtf_path = CaseAwarePath(self.mod_path, "tslpatchdata", namespace_option.rtf_filepath())
            info_rte_path = CaseAwarePath(self.mod_path, "tslpatchdata", namespace_option.rtf_filepath()).with_suffix(".rte")
            if not info_rtf_path.safe_isfile() and not info_rte_path.safe_isfile():
                self.run_background_task(self.main_window.error_dialog("No info.rtf", f"Could not load the info rtf for this mod, file '{info_rtf_path}' not found on disk."))
                return

            if info_rte_path.safe_isfile():
                data: bytes = BinaryReader.load_file(info_rte_path)
                rtf_text: str = decode_bytes_with_fallbacks(data, errors="replace")
                self.load_rte_content(rtf_text)
            elif info_rtf_path.safe_isfile():
                data = BinaryReader.load_file(info_rtf_path)
                rtf_text = decode_bytes_with_fallbacks(data, errors="replace")
                self.load_rtf_content(rtf_text)
                # self.load_rtf_file(info_rtf_path)
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            self._handle_general_exception(e, "An unexpected error occurred while loading the patcher namespace.")

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
            self.run_background_task(
                self.main_window.error_dialog(
                    title or error_name,
                    f"{(error_name + os.linesep * 2) if title else ''}{custom_msg}.{os.linesep * 2}{msg}",
                )
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
        """
        self.namespaces = namespaces
        self.namespaces_combobox.items = ListSource(data=namespaces, accessors=["patcher_namespace"])
        self.on_namespace_option_chosen(config_reader=config_reader)

    async def open_mod(
        self,
        default_directory_path_str: os.PathLike | str | None = None,
        unknown_toga_arg: Any | None = None,
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
                directory_path_str: os.PathLike | str = await self.main_window.select_folder_dialog("Select the mod directory (where tslpatchdata lives)")
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
                print("FOUND namespace_path:", namespace_path)
                self.load_namespace(NamespaceReader.from_filepath(namespace_path))
            elif changes_path.safe_isfile():
                print("FOUND changes_path:", changes_path, "namespace_path not found:", namespace_path)
                config_reader: ConfigReader = ConfigReader.from_filepath(changes_path)
                namespaces: list[PatcherNamespace] = [config_reader.config.as_namespace(changes_path)]
                self.load_namespace(namespaces, config_reader)
            else:
                print("namespace_path not found:", namespace_path, "changes_path not found:", changes_path)
                self.mod_path = ""
                if not default_directory_path_str:  # don't show the error if the cwd was attempted
                    await self.main_window.error_dialog("Error", f"Could not find a mod located chosen target '{directory_path_str}'")
                return
            await self.check_access(tslpatchdata_path, recurse=True, should_filter=True)
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            self._handle_general_exception(e, "An unexpected error occurred while loading the mod info.")
        else:
            if default_directory_path_str:
                self.browse_button.style.visibility = "hidden"
            if not namespace_path.safe_isfile():
                self.namespaces_combobox.style.visibility = "hidden"
                self.expand_namespace_description_button.style.visibility = "hidden"

    async def open_kotor(
        self,
        default_kotor_dir_str: os.PathLike | str | None = None,
        unknown_toga_arg: Any | None = None,
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
            directory_path_str = default_kotor_dir_str
            if not directory_path_str:
                directory_path_str = await self.main_window.select_folder_dialog("Select the KOTOR directory")
                if not directory_path_str:
                    return  # User cancelled the dialog
            directory = CaseAwarePath(directory_path_str)
            await self.check_access(directory)
            directory_str = str(directory)
            if directory_str not in [str(item) for item in self.gamepaths.items]:
                self.gamepaths.items.append(directory_str)
            self.gamepaths.value = directory_str
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

    async def fix_permissions(
        self,
        directory: os.PathLike | str | None = None,
        *,
        reset_namespace: bool = False,
    ):
        path_arg = await self.main_window.select_folder_dialog("Select target directory") if directory is None else directory
        if not path_arg:
            return
        if not directory and not await self.main_window.confirm_dialog(
            "Warning!",
            "This is not a toy. Really continue?"
        ):
            return

        try:
            path: Path = Path.pathify(path_arg)

            def task(result_queue: queue.Queue) -> None:
                extra_msg: str = ""
                self.set_state(state=True)
                self.clear_main_text()
                self.logger.add_note("Please wait, this may take awhile...")
                try:
                    access: bool = path.gain_access(recurse=True, log_func=self.logger.add_verbose)
                    with suppress(Exception):
                        self.play_complete_sound()
                    if not access:
                        result_queue.put(False)
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

                except Exception as e:
                    self._handle_general_exception(e)
                    result_queue.put(False)
                else:
                    result_queue.put(True)
                finally:
                    self.set_state(state=False)
                    self.logger.add_note("File/Folder permissions fixer task completed.")

            result_queue = queue.Queue()
            self.task_thread = Thread(target=task, args=(result_queue,), name="HoloPatcher_install_thread")
            self.task_thread.start()
            self.task_thread.join()
            if not result_queue.get():
                await self.main_window.error_dialog(
                    "Could not gain permission!",
                    f"Permission denied to {directory}. Please run HoloPatcher with elevated permissions, and ensure the selected folder exists and is writeable.",
                )
        except Exception as e2:
            self._handle_general_exception(e2)
        finally:
            if reset_namespace and self.mod_path:
                self.on_namespace_option_chosen()
            self.logger.add_verbose("Started the File/Folder permissions fixer task.")

    async def check_access(
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
        if await self.main_window.confirm_dialog(
            "Permission error",
            f"HoloPatcher does not have permissions to the path '{directory}', would you like to attempt to gain permission automatically?",
        ):
            directory.gain_access(recurse=recurse)
            self.on_namespace_option_chosen()
        if not directory.has_access(recurse=recurse):
            return await self.main_window.error_dialog(
                "Unauthorized",
                (
                    f"HoloPatcher needs permissions to access '{directory}'. {os.linesep}"
                    f"{os.linesep}"
                    f"Please ensure the necessary folders are writeable or rerun holopatcher with elevated privileges.{os.linesep}"
                    "Continue with an install anyway?"
                ),
            )
        return True

    async def preinstall_validate_chosen(self) -> bool:
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
            await self.main_window.info_dialog(
                "Task already running",
                "Wait for the previous task to finish.",
            )
            return False
        if not self.mod_path or not CaseAwarePath(self.mod_path).safe_isdir():
            await self.main_window.error_dialog(
                "No mod chosen",
                "Select your mod directory first.",
            )
            return False
        game_path: str = str(self.gamepaths.value)
        if not game_path:
            await self.main_window.error_dialog(
                "No KOTOR directory chosen",
                "Select your KOTOR directory first.",
            )
            return False
        case_game_path = CaseAwarePath(game_path)
        if not case_game_path.safe_isdir():
            await self.main_window.error_dialog(
                "Invalid KOTOR directory chosen",
                "Select a valid path to your KOTOR install.",
            )
            return False
        game_path_str = str(case_game_path)
        self.gamepaths.value = game_path_str
        return await self.check_access(Path(game_path_str))

    async def begin_install(self):
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
            if not await self.preinstall_validate_chosen():
                return
            self.pykotor_logger.debug("Prevalidate finished, starting install thread")
            self.task_thread = Thread(target=self.begin_install_thread, args=(self.simple_thread_event, self.update_progress_bar_directly), name="HoloPatcher_install_thread")
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
        namespace_option: PatcherNamespace = self.namespaces_combobox.value.patcher_namespace
        tslpatchdata_path = CaseAwarePath(self.mod_path, "tslpatchdata")
        ini_file_path = tslpatchdata_path.joinpath(namespace_option.changes_filepath())
        namespace_mod_path: CaseAwarePath = ini_file_path.parent

        self.pykotor_logger.debug("set ui state")
        self.set_state(state=True)
        self.clear_main_text()
        install_message = f"Starting install...{os.linesep}".replace("\n", "<br>")
        self.web_view.evaluate_javascript(f"setContent('{install_message}');")
        try:
            installer = ModInstaller(namespace_mod_path, str(self.gamepaths.value), ini_file_path, self.logger)
            installer.tslpatchdata_path = tslpatchdata_path
            self._execute_mod_install(installer, should_cancel_thread, update_progress_func)
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            self._handle_exception_during_install(e)
        finally:
            self.set_state(state=False)
            self.install_running = False

    async def test_reader(self):  # sourcery skip: no-conditionals-in-tests
        if not await self.preinstall_validate_chosen():
            return
        namespace_option: PatcherNamespace = self.namespaces_combobox.value.patcher_namespace
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

        Thread(target=task, name="Test_Reader_Thread").start()

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
            self.progress_bar.value = 0
            self.progress_bar.max = 100
            self.progress_value = 0
            self.task_running = True
            self.install_button.enabled = False
            self.gamepaths_browse_button.enabled = False
            self.browse_button.enabled = False
        else:
            self.task_running = False
            self.initialize_logger()  # reset the errors/warnings etc
            self.install_button.enabled = True
            self.gamepaths_browse_button.enabled = True
            self.browse_button.enabled = True

    def clear_main_text(self):
        """Clears all content from the WebView to prepare for new content."""
        self.web_view.evaluate_javascript("document.getElementById('content').innerHTML = '';")

    def _execute_mod_install(
        self,
        installer: ModInstaller,
        should_cancel_thread: Event,
        update_progress_func: Callable | None = None
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
            if confirm_msg and not self.one_shot and confirm_msg != "N/A":
                # Create a function to handle the confirmation dialog result
                def handle_confirmation_dialog(response):
                    if not response:
                        return  # Cancel the operation if the user did not confirm

                # Show a confirmation dialog
                if not self.main_window.confirm_dialog("This mod requires confirmation", confirm_msg):
                    return  # If the dialog returns False, stop the execution
            if update_progress_func is not None:
                self.progress_bar.max = len(
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
            installer.install(should_cancel_thread, update_progress_func)
            total_install_time: timedelta = datetime.now(timezone.utc).astimezone() - install_start_time
            if update_progress_func is not None:
                self.progress_bar.value = 99  # Update the current value
                self.progress_bar.max = 100   # Set the maximum value if needed
                update_progress_func()
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
                self.run_background_task(
                    self.main_window.error_dialog(
                        "Install completed with errors!",
                        f"The install completed with {num_errors} errors and {num_warnings} warnings! The installation may not have been successful, check the logs for more details."
                        f"{os.linesep * 2}Total install time: {time_str}"
                        f"{os.linesep}Total patches: {num_patches}",
                    )
                )
                if self.one_shot:
                    sys.exit(ExitCode.INSTALL_COMPLETED_WITH_ERRORS)
            elif num_warnings > 0:
                self.run_background_task(
                    self.main_window.info_dialog(
                        "Install completed with warnings",
                        f"The install completed with {num_warnings} warnings! Review the logs for details. The script in the 'uninstall' folder of the mod directory will revert these changes."
                        f"{os.linesep * 2}Total install time: {time_str}"
                        f"{os.linesep}Total patches: {num_patches}",
                    )
                )
            else:
                self.run_background_task(
                    self.main_window.info_dialog(
                        "Install complete!",
                        f"Check the logs for details on what has been done. Utilize the script in the 'uninstall' folder of the mod directory to revert these changes."
                        f"{os.linesep * 2}Total install time: {time_str}"
                        f"{os.linesep}Total patches: {num_patches}",
                    )
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

        self.run_background_task(
            self.main_window.error_dialog(
                error_name,
                f"An unexpected error occurred during the installation and the installation was forced to terminate.{os.linesep * 2}{msg}",
            )
        )
        raise

    def create_rte_content(self, event: tk.Tk | None = None):
        from utility.tkinter.rte_editor import main as start_rte_editor

        start_rte_editor()

    def load_rte_content(self, rte_content: str | bytes | bytearray | None = None):
        """Load and display RTE content in the WebView."""
        self.clear_main_text()

        if rte_content is None:
            file_path_str = self.main_window.open_file_dialog("Open", Path.cwd(), ["*.rte"])
            if not file_path_str:
                return
            with Path(file_path_str).open("rb") as f:
                rte_encoded_data: bytes = f.read()
            rte_content = decode_bytes_with_fallbacks(rte_encoded_data)

        document: dict[str, Any] = json.loads(rte_content)
        content: str = document.get("content", "")

        # Handle tag configurations
        tag_configs: dict[str, Any | dict] = document.get("tag_configs", {})
        for tag, config in tag_configs.items():
            style: list[str] = []
            for key, value in config.items():
                if key == "foreground":
                    style.append(f"color:{value};")
                elif key == "background":
                    style.append(f"background-color:{value};")
                elif key == "font":
                    style.append(f"font-family:{value};")
                elif key == "size":
                    style.append(f"font-size:{value}pt;")
                elif key == "bold" and value:
                    style.append("font-weight:bold;")
                elif key == "italic" and value:
                    style.append("font-style:italic;")
                elif key == "underline" and value:
                    style.append("text-decoration:underline;")
                elif key == "overstrike" and value:
                    style.append("text-decoration:line-through;")
                elif key == "justify":
                    if value == "left":
                        style.append("text-align:left;")
                    elif value == "center":
                        style.append("text-align:center;")
                    elif value == "right":
                        style.append("text-align:right;")
                elif key == "spacing1":
                    style.append(f"line-height:{value};")
                elif key == "spacing3":
                    style.append(f"margin-bottom:{value};")
                elif key == "lmargin1":
                    style.append(f"margin-left:{value}px;")
                elif key == "lmargin2":
                    style.append(f"margin-right:{value}px;")
                elif key == "bullet_list":
                    style.append("list-style-type:disc;")
                elif key == "numbered_list":
                    style.append("list-style-type:decimal;")
            style_str = "".join(style)
            content = content.replace(f"<{tag}>", f'<span style="{style_str}">').replace(f"</{tag}>", "</span>")

        content = content.replace("'", "\\'")
        self.web_view.evaluate_javascript(f"setContent('{content}');")

    def load_rtf_content(self, rtf_text: str):
        """Converts the RTF content to HTML and displays it in the WebView."""
        self.clear_main_text()
        try:
            html_content = pypandoc.convert_text(rtf_text, "html", format="rtf")
        except OSError:
            # Download Pandoc if it is not installed
            pypandoc.download_pandoc()
            html_content = pypandoc.convert_text(rtf_text, "html", format="rtf")

        # Use JSON dumps to safely encode the HTML for JavaScript
        safe_html_content = json.dumps(html_content)
        self.web_view.evaluate_javascript(f"setContent({safe_html_content});")

    def write_log(self, log: PatchLog):
        """Writes a message to the log.

        Args:
        ----
            log: PatchLog - The log object containing the message and type.

        Processes the log message by:
            - Setting the description text widget to editable
            - Inserting the message plus a newline at the end of the text
            - Scrolling to the end of the text
            - Making the description text widget not editable again.
        """
        def log_type_to_tag(log: PatchLog) -> str:
            if log.log_type == LogType.NOTE:
                return "INFO"
            if log.log_type == LogType.VERBOSE:
                return "DEBUG"
            return log.log_type.name

        try:
            self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_file_path.open("a", encoding="utf-8") as log_file:
                log_file.write(f"{log.formatted_message}\n")
            if log.log_type.value < self.log_level.value:
                return
        except OSError:
            RobustRootLogger().exception(f"Failed to write the log file at '{self.log_file_path}'!")

        log_tag = log_type_to_tag(log)
        log_message = log.formatted_message.replace("\n", "<br>").replace("'", "\\'").replace("`", "\\`").replace("\\", "\\\\")
        script = f"appendLogLine(`{log_message}`, '{log_tag}');"
        self.web_view.evaluate_javascript(script)


@contextmanager
def temporary_toga_window() -> Generator[toga.Window, Any, None]:
    app = toga.App.app if hasattr(toga.App, "app") else None
    new_app_created: bool = False
    if app is not None:
        window = toga.Window(size=(1, 1))
        window.show()
    else:
        new_app_created = True
        app = toga.App("Error App", "org.example.error")
        window = toga.Window(size=(1, 1))
        window.show()
        Thread(target=app.main_loop, daemon=True, name="Temp_Toga_Window_Daemon").start()
    yield window
    window.close()
    if new_app_created:
        app.exit()


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

    with temporary_toga_window() as temp_window:
        temp_window.error_dialog(title, f"{short_msg}\n{etype.__name__}")
    sys.exit(ExitCode.CRASH)


sys.excepthook = onAppCrash


def hp_exit_cleanup(app: HoloPatcher):
    """Prevents the patcher from running in the background after sys.exit is called."""
    print("Fully shutting down HoloPatcher...")
    app.main_window.close()
    terminate_main_process()


def main():
    app = HoloPatcher(
        formal_name="HoloPatcher",
        app_id="com.pykotor.holopatcher"
    )
    atexit.register(lambda: hp_exit_cleanup(app))
    app.main_loop()

def is_running_from_temp() -> bool:
    return str(Path(sys.executable)).startswith(tempfile.gettempdir())

if __name__ == "__main__":
    if is_running_from_temp():
        messagebox.showerror("Error", "This application cannot be run from within a zip or temporary directory. Please extract it to a permanent location before running.")
        sys.exit("Exiting: Application was run from a temporary or zip directory.")
    main()
