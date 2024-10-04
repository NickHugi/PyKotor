#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import atexit
import ctypes
import json
import os
import pathlib
import platform
import subprocess
import sys
import tempfile
import threading
import time
import webbrowser

from argparse import ArgumentParser
from contextlib import contextmanager, suppress
from datetime import datetime, timezone
from enum import IntEnum
from multiprocessing import Queue
from types import TracebackType
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Coroutine,
    Generator,
    NoReturn,
    TypeVar,
    cast,
)

import pypandoc  # pyright: ignore[reportMissingTypeStubs]
import toga

from toga import Group
from toga.command import Command
from toga.handlers import AsyncResult
from toga.sources import ListSource
from toga.style import Pack
from travertino.constants import (  # pyright: ignore[reportMissingTypeStubs]
    CENTER,
    COLUMN,
    ROW,
)
from travertino.declaration import BaseStyle  # pyright: ignore[reportMissingTypeStubs]


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
        pykotor_path = pathlib.Path(__file__).parents[4] / "Libraries" / "PyKotor" / "src" / "pykotor"
        if pykotor_path.exists():
            update_sys_path(pykotor_path.parent)
    with suppress(Exception):
        utility_path = pathlib.Path(__file__).parents[4] / "Libraries" / "Utility" / "src" / "utility"
        if utility_path.exists():
            update_sys_path(utility_path.parent)
    with suppress(Exception):
        update_sys_path(pathlib.Path(__file__).parents[1])



from pathlib import Path  # noqa: E402

from loggerplus import RobustLogger  # noqa: E402

from holopatcher.config import (  # noqa: E402
    CURRENT_VERSION,
    getRemoteHolopatcherUpdateInfo,
    remoteVersionNewer,
)
from pykotor.common.misc import Game  # noqa: E402
from pykotor.common.stream import BinaryReader  # noqa: E402
from pykotor.extract.file import ResourceIdentifier  # noqa: E402
from pykotor.tools.encoding import decode_bytes_with_fallbacks  # noqa: E402
from pykotor.tools.path import (  # noqa: E402
    CaseAwarePath,
    find_kotor_paths_from_default,
)
from pykotor.tslpatcher.config import LogLevel  # noqa: E402
from pykotor.tslpatcher.logger import LogType, PatchLog, PatchLogger  # noqa: E402
from pykotor.tslpatcher.namespaces import PatcherNamespace  # noqa: E402
from pykotor.tslpatcher.patcher import ModInstaller  # noqa: E402
from pykotor.tslpatcher.reader import ConfigReader, NamespaceReader  # noqa: E402
from pykotor.tslpatcher.uninstall import ModUninstaller  # noqa: E402
from utility.common.misc_string.util import striprtf  # noqa: E402
from utility.error_handling import universal_simplify_exception  # noqa: E402
from utility.misc import ProcessorArchitecture, is_debug_mode  # noqa: E402
from utility.system.agnostics import (  # noqa: E402
    askdirectory,
    askokcancel,
    askopenfilename,
    askyesno,
    showerror,
)
from utility.system.app_process.shutdown import terminate_main_process  # noqa: E402

#from utility.system.os_helper import get_app_dir
from utility.system.os_helper import win_get_system32_dir  # noqa: E402
from utility.tkinter.updater import TkProgressDialog  # noqa: E402

if TYPE_CHECKING:
    from argparse import Namespace
    from collections.abc import Callable
    from datetime import timedelta
    from multiprocessing import Process

    from toga import Selection


VERSION_LABEL = f"v{CURRENT_VERSION}"
T = TypeVar("T")

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


def show_update_dialog(
    window: toga.MainWindow,
    title: str,
    message: str,
    options: list[dict[str, Any]],
):
    class UpdateDialog(toga.Box):  # TODO(th3w1zard1): move class to library code, for now keep nested in this function so it doesn't clutter the autoimport-completions
        def __init__(self, title: str, message: str, options: list[dict[str, Any]], *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.options: list[dict[str, Any]] = options
            cast(BaseStyle, self.style).update(direction=COLUMN, padding=10)  # type: ignore[]

            # Title
            self.title_label: toga.Label = toga.Label(title, style=Pack(padding_bottom=10))
            self.add(self.title_label)

            # Message
            self.message_label: toga.Label = toga.Label(message, style=Pack(padding_bottom=10))
            self.add(self.message_label)

            # Buttons
            button_box: toga.Box = toga.Box(style=Pack(direction=ROW, padding_top=10))
            for option in options:
                button = toga.Button(option["label"], on_press=lambda widget, opt=option: self.handle_result(opt), style=Pack(padding=5))  # noqa: ARG005
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

        self.html_template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Log Viewer</title>
            <style>
                body {
                    font-family: 'Arial', sans-serif;
                    margin: 0;
                    padding: 10px;
                    background-color: #f0f0f0;
                    overflow: hidden;
                }
                #content {
                    height: calc(100vh - 60px);
                    overflow-y: auto;
                    z-index: 1;
                    position: relative;
                }
                #log-container {
                    position: fixed;
                    bottom: 0;
                    left: 0;
                    width: 100%;
                    transition: height 1s ease, top 1s ease;
                    z-index: 2;
                }
                #expander {
                    text-align: center;
                    cursor: pointer;
                    background-color: #ddd;
                    padding: 10px;
                    font-weight: bold;
                    color: #333;
                }
                #logs {
                    overflow-y: auto;
                    display: none;
                    background-color: rgba(255, 255, 255, 0.9); /* Semi-transparent background */
                    z-index: 3; /* Higher z-index to cover content */
                }
                .collapsed #logs {
                    display: none;
                }
                .slightly-expanded #logs {
                    max-height: 70vh; /* Set a max height to prevent it from covering too much content */
                    display: block;
                    overflow-y: auto; /* Enable vertical scrolling */
                }
                .collapsed #expander::after {
                    content: ' ^^^ LOG VIEW ^^^ ';
                }
                .slightly-expanded #expander::after {
                    content: ' --- LOG VIEW --- ';
                }
                .slightly-expanded #log-container {
                    height: 30%;
                    top: auto;
                }
                .collapsed #log-container {
                    height: 5%;
                    top: auto;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                }
                td {
                    word-wrap: break-word;
                    white-space: pre-wrap; /* Ensures that long words wrap correctly */
                }
                tr:nth-child(even) {
                    background-color: #f2f2f2;
                }
                .log-entry {
                    transition: all 0.5s ease;
                }
                .DEBUG { color: blue; }
                .INFO { color: black; }
                .WARNING { color: orange; }
                .ERROR { color: red; }
                .CRITICAL { color: white; background-color: red; }
                .log-entry.new {
                    animation: customSlideIn 0.25s ease;
                }
                @keyframes customSlideIn {
                    from {
                        transform: translateX(100%);
                        opacity: 0;
                    }
                    to {
                        transform: translateX(0);
                        opacity: 1;
                    }
                }
            </style>
            <script src="marked.min.js"></script>
            <script>
                console.log('Marked library loaded:', typeof marked !== 'undefined');
            </script>
        </head>
        <body>
            <div id="content" class="collapsed">
                <!-- Main content area -->
            </div>
            <div id="log-container" class="collapsed">
                <div id="expander" onclick="toggleExpand()"></div>
                <div id="logs">
                    <table id="logs-table">
                        <tbody>
                            <!-- Log entries will be dynamically inserted here -->
                        </tbody>
                    </table>
                </div>
            </div>
            <script>
                function toggleExpand() {
                    const container = document.getElementById('log-container');
                    if (container.classList.contains('collapsed')) {
                        container.classList.remove('collapsed');
                        container.classList.add('slightly-expanded');
                        document.getElementById('logs').style.display = 'block';
                    } else {
                        container.classList.remove('slightly-expanded');
                        container.classList.add('collapsed');
                        document.getElementById('logs').style.display = 'none';
                    }
                }

                function setContent(newContent) {
                    document.getElementById('content').innerHTML = newContent;
                    updateExpanderState();
                }

                function appendLogLine(logLine, logType) {
                    const tableBody = document.getElementById('logs-table').getElementsByTagName('tbody')[0];
                    const row = tableBody.insertRow();
                    const cell = row.insertCell(0);
                    cell.innerHTML = logLine;
                    row.className = 'log-entry ' + logType + ' new';
                    document.getElementById('logs').scrollTop = document.getElementById('logs').scrollHeight;
                    updateExpanderState();
                }

                function updateExpanderState() {
                    const logs = document.getElementById('logs');
                    const expander = document.getElementById('expander');
                    const logContainer = document.getElementById('log-container');
                    const hasLogs = logs.querySelector('tbody').children.length > 0;
                    const hasContent = document.getElementById('content').innerHTML.trim() !== '';

                    if (hasLogs) {
                        expander.style.display = 'block';
                        if (logContainer.classList.contains('collapsed')) {
                            logContainer.classList.remove('collapsed');
                            logContainer.classList.add('slightly-expanded');
                        }
                    } else {
                        expander.style.display = 'none';
                        logContainer.classList.remove('expanded', 'slightly-expanded');
                        logContainer.classList.add('collapsed');
                    }
                }

                document.addEventListener("DOMContentLoaded", function() {
                    updateExpanderState();
                });
                updateExpanderState();
            </script>
        </body>
        </html>
        """
        # Define the HTML template with JavaScript for dynamic content updates
        # uncomment to test from file
        #template_path = get_app_dir() / "template.html"
        #with template_path.open("r") as file:
        #    self.html_template = file.read()
        self.default_window_size: tuple[int, int] = (400, 500)
        self.main_window: toga.MainWindow = toga.MainWindow(
            title=f"HoloPatcher {VERSION_LABEL}",
            size=self.default_window_size,
            position=self.get_centered_position(*self.default_window_size),
            content=toga.Box(style=Pack(direction=COLUMN)),
        )
        self.on_exit = lambda widget, **kwargs: self.handle_exit_button() or True  # noqa: ARG005

        self.task_running: bool = False
        self.mod_path: str = ""
        self.log_level: LogLevel = LogLevel.WARNINGS
        self.pykotor_logger: RobustLogger = RobustLogger()

        self.initialize_logger()
        self.initialize_top_menu()
        self.initialize_ui_controls()
        print("Init complete")
        self.run_later(self.post_startup())

    async def post_startup(self):
        print("post_startup")
        cmdline_args: Namespace = parse_args()
        print("parse_args complete")
        print(f"init directory: {cmdline_args.tslpatchdata or Path.cwd()}")
        self.open_mod(cmdline_args.tslpatchdata or Path.cwd(), startup=True)
        self.execute_commandline(cmdline_args)

    def run_async_from_sync(
        self,
        coro: Coroutine[Any, Any, T] | Awaitable[Any] | asyncio.Task[Any] | AsyncResult,
    ) -> T:
        """Utility method to run a coroutine as a background task and keep a reference to it.

        DO NOT RUN GUI CODE WITH THIS FUNCTION!
        """
        print("unsafe async function called!")
        try:
            if isinstance(coro, AsyncResult):
                async def await_async_result():
                    return await coro
                return cast(T, asyncio.run_coroutine_threadsafe(await_async_result(), self.loop).result())  # Wait for the coroutine to complete and return the result
            if isinstance(coro, (Coroutine, asyncio.Task, Awaitable)):
                return cast(T, asyncio.run_coroutine_threadsafe(coro, self.loop).result())  # Wait for the coroutine to complete and return the result
        finally:
            print("unsafe async function finished!")
        raise TypeError("Provided argument must be a coroutine or a callable returning a coroutine")

    def run_later(
        self,
        coro: Coroutine | Awaitable | AsyncResult,
        callback: Callable[[Any | None, Exception | None], Any] | None = None,
    ):
        """Execute an awaitable object or coroutine as a background task and optionally call a callback with the result,
        safe to use from any thread or context.

        Args:
        ----
            coro (Coroutine | AsyncResult | Awaitable): The coroutine or awaitable object to run in the background.
            callback (Callable, optional): A function to execute with the result of the coroutine.
        """
        print("run_later called!")
        async def task_wrapper(app: toga.App, **kwargs):  # noqa: ARG001  # type: ignore[]
            try:
                result = await coro
                if callback is not None:
                    callback(result, None)
            except Exception as e:  # noqa: BLE001
                RobustLogger().exception("An exception has occurred while firing an async function.")
                if callback is not None:
                    callback(None, e)
        self.add_background_task(task_wrapper)

    def get_centered_position(self, width: int, height: int) -> tuple[int, int]:
        if platform.system() == "Windows":
            # Windows
            user32 = ctypes.windll.user32
            screen_width = user32.GetSystemMetrics(0)
            screen_height = user32.GetSystemMetrics(1)
        # use screeninfo pip package
        elif self.main_window is None:
            try:
                from screeninfo import get_monitors
                monitors = get_monitors()
                if monitors:
                    primary_monitor = monitors[0]
                    screen_width = primary_monitor.width
                    screen_height = primary_monitor.height
            except ImportError:
                return (100, 100)
        # macOS and Linux using Toga's main_window to get screen dimensions
        else:
            screen = self.main_window.screen_position
            screen_width = screen.x
            screen_height = screen.y

        return (
            int((screen_width / 2) - (width / 2)),
            int((screen_height / 2) - (height / 2))
        )

    def initialize_logger(self):
        self.logger = PatchLogger()
        self.logger.verbose_observable.subscribe(self.write_log)
        self.logger.note_observable.subscribe(self.write_log)
        self.logger.warning_observable.subscribe(self.write_log)
        self.logger.error_observable.subscribe(self.write_log)

    def initialize_top_menu(self):
        # Groups
        tools_group, help_group, about_group = Group("Tools"), Group("Help"), Group("About")

        # Help subgroups
        deadlystream_group = Group("DeadlyStream", parent=help_group)
        neocities_group = Group("KOTOR Community Portal", parent=help_group)
        pcgamingwiki_group = Group("PCGamingWiki", parent=help_group)

        # Tools Menu Commands
        tools_menu = [
            Command(lambda command, **kwargs: self.test_reader() or True, text="Validate INI", group=tools_group),  # noqa: ARG005
            Command(lambda command, **kwargs: self.uninstall_selected_mod() or True, text="Uninstall Mod / Restore Backup", group=tools_group),  # noqa: ARG005
            Command(lambda command, **kwargs: self.fix_permissions() or True, text="Fix permissions to file/folder...", group=tools_group),  # noqa: ARG005
            Command(lambda command, **kwargs: self.lowercase_files_and_folders() or True, text="Fix iOS Case Sensitivity", group=tools_group),  # noqa: ARG005
            Command(lambda command, **kwargs: self.create_rte_content() or True, text="Create info.rte...", group=tools_group)  # noqa: ARG005
        ]

        # Help Menu Commands
        help_menu = [
            Command(lambda command, **kwargs: webbrowser.open_new("https://discord.gg/nDkHXfc36s"), text="Discord", group=deadlystream_group),  # noqa: ARG005
            Command(lambda command, **kwargs: webbrowser.open_new("https://deadlystream.com"), text="Website", group=deadlystream_group),  # noqa: ARG005
            Command(lambda command, **kwargs: webbrowser.open_new("https://discord.com/invite/kotor"), text="Discord", group=neocities_group),  # noqa: ARG005
            Command(lambda command, **kwargs: webbrowser.open_new("https://kotor.neocities.org"), text="Website", group=neocities_group),  # noqa: ARG005
            Command(lambda command, **kwargs: webbrowser.open_new("https://www.pcgamingwiki.com/wiki/Star_Wars:_Knights_of_the_Old_Republic"), text="KOTOR 1", group=pcgamingwiki_group),  # noqa: ARG005
            Command(lambda command, **kwargs: webbrowser.open_new("https://www.pcgamingwiki.com/wiki/Star_Wars:_Knights_of_the_Old_Republic_II_-_The_Sith_Lords"), text="KOTOR 2: TSL", group=pcgamingwiki_group)  # noqa: ARG005
        ]

        # About Menu Commands
        about_menu = [
            Command(lambda command, **kwargs: self.check_for_updates() or True, text="Check for Updates", group=about_group),  # noqa: ARG005
            Command(lambda command, **kwargs: webbrowser.open_new("https://deadlystream.com/files/file/2243-holopatcher"), text="HoloPatcher Home", group=about_group),  # noqa: ARG005
            Command(lambda command, **kwargs: webbrowser.open_new("https://github.com/NickHugi/PyKotor"), text="GitHub Source", group=about_group)  # noqa: ARG005
        ]

        # Test Menu Commands (Ported from Puppeteer script)
        if is_debug_mode():
            test_group = Group("Tests")
            test_menu = [
                Command(lambda command, **kwargs: self.add_log_entry() or True, text="Test Log Entry (direct appendLogLine evaluate call)", group=test_group),
                Command(lambda command, **kwargs: self.remove_all_logs() or True, text="Remove All Logs", group=test_group),
                Command(lambda command, **kwargs: self.test_write_log() or True, text="Test Log Entry (using write_log)", group=test_group),
                Command(lambda command, **kwargs: self.test_add_note() or True, text="Test Log Entry (using add_note)", group=test_group),
                Command(lambda command, **kwargs: self.remove_all_content() or True, text="Remove All Content", group=test_group)
            ]
        else:
            test_menu = []

        # Adding commands to the main window toolbar
        for command in (*tools_menu, *help_menu, *about_menu, *test_menu):
            self.commands.add(command)

    def add_log_entry(self):
        script = "appendLogLine('This is a log message', 'INFO');"
        self.web_view.evaluate_javascript(script)

    def test_add_note(self):
        self.logger.add_note("This is a log message")

    def test_write_log(self):
        self.write_log(PatchLog("This is a log message", LogType.NOTE))

    def remove_all_logs(self):
        script = """
            const logsContainer = document.getElementById('logs').querySelector('tbody');
            while (logsContainer.firstChild) {
                logsContainer.removeChild(logsContainer.firstChild);
            }
            updateExpanderState();
        """
        self.web_view.evaluate_javascript(script)

    def remove_all_content(self):
        script = """
            document.getElementById('content').innerHTML = '';
            updateExpanderState();
        """
        self.web_view.evaluate_javascript(script)


    def initialize_ui_controls(self):
        assert self.main_window.content is not None

        # Namespace/Mod row.
        self.namespaces_combobox: toga.Selection = toga.Selection(
            items=[],
            style=Pack(flex=1, padding_right=5, font_size=10, padding=4),
            accessor="patcher_namespace",
            on_change=self.refresh_ui_data
        )
        self.browse_button = toga.Button("Browse", on_press=lambda *args, **kwargs: self.open_mod(), style=Pack(padding_right=5))
        self.expand_namespace_description_button: toga.Button = toga.Button(
            "?",
            on_press=lambda _widget: self.run_later(
                self.display_info_dialog(
                    str(cast(PatcherNamespace, self.namespaces_combobox.value.patcher_namespace).name),  # type: ignore[]
                    self.get_namespace_description()
                )
            ),
            style=Pack(padding_right=5, width=30, flex=0)
        )
        self.main_window.content.add(
            toga.Box(
                style=Pack(direction=ROW, alignment=CENTER, padding=5),
                children = [self.namespaces_combobox, self.browse_button]
            )
        )

        # KOTOR Install row.
        self.gamepaths = toga.Selection(items=[], style=Pack(flex=1, padding_right=5, font_size=10, padding=4))  # Match the flex of the top row combobox
        self.gamepaths_browse_button = toga.Button("Browse", on_press=lambda *args, **kwargs: self.open_kotor(), style=Pack(padding_right=5))
        self.main_window.content.add(
            toga.Box(
                style=Pack(direction=ROW, alignment=CENTER, padding=5),
                children=[self.gamepaths, self.gamepaths_browse_button]
            )
        )

        # Main WebView for content display
        self.web_view: toga.WebView = toga.WebView(style=Pack(flex=1, padding=5))
        self.web_view.set_content("", self.html_template)
        self.main_text_frame: toga.ScrollContainer = toga.ScrollContainer(  # ScrollContainer to add scrollbars
            horizontal=False,
            vertical=True,
            style=Pack(flex=1),
            content=self.web_view,
        )
        self.main_window.content.add(self.main_text_frame)

        # Bottom widgets.
        self.exit_button: toga.Button = toga.Button("Exit", on_press=self.handle_exit_button, style=Pack(flex=1, padding=5))
        self.progress_bar: toga.ProgressBar = toga.ProgressBar(max=100, value=0, style=Pack(flex=3, padding_top=5))
        self.install_button: toga.Button = toga.Button("Install", on_press=self.begin_install, style=Pack(flex=1, padding=5))
        self.main_window.content.add(
            toga.Box(
                style=Pack(direction=ROW, padding=5, alignment=CENTER),
                children=[self.exit_button, self.progress_bar, self.install_button]
            )
        )
        self.main_window.show()

    def toggle_view(self, view: str):
        """Toggle between content and log views."""
        script = f"toggleExpand('{view}');"
        self.web_view.evaluate_javascript(script)

    def update_progress_bar_directly(self, value: int = 1):
        def update(app: toga.App | None = None, **kwargs):
            self.progress_bar.value += value

        self.add_background_task(update)

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

        os_name = platform.system()
        proc_arch = ProcessorArchitecture.from_os()
        assert proc_arch == ProcessorArchitecture.from_python()

        is_release = True  # TODO(th3w1zard1): remove this line when the beta version direct links are ready.
        links: list[str] = []
        if is_release:
            links = remote_info["holopatcherDirectLinks"][os_name][proc_arch.value]
        else:
            links = remote_info["holopatcherBetaDirectLinks"][os_name][proc_arch.value]

        progress_queue: Queue = Queue()
        progress_dialog: Process = run_tk_progress_dialog(progress_queue, "HoloPatcher is updating and will restart shortly...")
        def download_progress_hook(data: dict[str, Any], progress_queue: Queue = progress_queue):
            progress_queue.put(data)

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
            if s.count(".") == 2:  # noqa: PLR2004
                second_dot_index = s.find(".", s.find(".") + 1)
                s = s[:second_dot_index] + s[second_dot_index + 1:]
            return f"v{s}-patcher"

        updater = AppUpdate(
            links,
            "HoloPatcher",
            CURRENT_VERSION,
            latest_version,
            downloader=None,
            progress_hooks=[download_progress_hook],
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
            RobustLogger().critical("Auto-update had an unexpected error", exc_info=True)
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
            self.namespaces_combobox.value = self.namespaces_combobox.items[cmdline_args.namespace_option_index]
        if not cmdline_args.console:
            self.hide_console()

        self.one_shot: bool = False
        num_cmdline_actions: int = sum([cmdline_args.install, cmdline_args.uninstall, cmdline_args.validate])
        if num_cmdline_actions == 1:
            try:
                self._begin_oneshot(cmdline_args)
            except Exception:  # noqa: BLE001
                if self.one_shot:
                    self.exit()
                    sys.exit(ExitCode.EXCEPTION_DURING_INSTALL)
            finally:
                if self.one_shot:
                    self.exit()
                    sys.exit(ExitCode.SUCCESS)
        elif num_cmdline_actions > 1:
            showerror("Invalid cmdline args passed", "Cannot run more than one of [--install, --uninstall, --validate]")
            sys.exit(ExitCode.NUMBER_OF_ARGS)

    def _begin_oneshot(
        self,
        cmdline_args: Namespace,
    ):
        self.one_shot = True
        self.main_window.visible = False
        if not self.preinstall_validate_chosen():
            sys.exit(ExitCode.NUMBER_OF_ARGS)
        if cmdline_args.install:
            self.begin_install(self.namespaces_combobox.value.patcher_namespace)  # type: ignore[]
        if cmdline_args.uninstall:
            self.uninstall_selected_mod()
        if cmdline_args.validate:
            self.test_reader()
        sys.exit(ExitCode.SUCCESS)

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
        if not backup_parent_folder.is_dir():
            self.run_later(self.display_error_dialog(
                "Backup Folder Empty/Missing.",
                f"Could not find backup folder '{backup_parent_folder}'{os.linesep * 2}Are you sure the mod is installed?",
            ))
            return

        self.set_state(state=True)
        fully_ran: bool = True
        try:  # TODO(th3w1zard1): refactor ModUninstaller to not be hardcoded with tkinter.
            uninstaller = ModUninstaller(backup_parent_folder, Path(self.gamepaths.value), self.logger)
            fully_ran = uninstaller.uninstall_selected_mod()
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            self._handle_exception_during_install(e)
        finally:
            self.set_state(state=False)
            self.logger.add_note("Mod Uninstaller/Backup Restore Task Completed.")
        if not fully_ran:
            self.refresh_ui_data()

    def handle_exit_button(self, button: toga.Button | None = None):
        """Handle exit button click during installation.

        Processing Logic:
        ----------------
            - Check if installation is running
            - Display confirmation dialog and check response
            - Try stopping install thread gracefully
            - If stopping fails, force terminate install thread
            - Destroy window and exit with abort code.
        """
        if not self.task_running:
            print("Goodbye!")
            self.exit()
            sys.exit(ExitCode.SUCCESS)
            return  # leave here for the static type checkers

        # Handle unsafe exit.
        if askyesno(
            "Really cancel the current installation? ",
            "CONTINUING WILL MOST LIKELY BREAK YOUR GAME AND REQUIRE A FULL KOTOR REINSTALL!",
        ):
            return

        print("Close mainwindow")
        self.main_window.close()
        print("Exit main app")
        self.exit()
        print("Goodbye! (sys.exit abort unsafe)")
        print("Nevermind, Forcefully kill this process (taskkill or kill command in subprocess)")
        pid = os.getpid()
        try:
            if os.name == "nt":
                system32_path = win_get_system32_dir()
                subprocess.run([str(system32_path / "taskkill.exe"), "/F", "/PID", str(pid)], check=True)  # noqa: S603
            else:
                subprocess.run(["kill", "-9", str(pid)], check=True)  # noqa: S603, S607
        except Exception as e:  # noqa: BLE001
            self._handle_general_exception(e, "Failed to kill process", msgbox=False)
        finally:
            # This code might not be reached, but it's here for completeness
            os._exit(ExitCode.ABORT_INSTALL_UNSAFE)

    def get_namespace_description(self) -> str:
        """Show the expanded description from namespaces.ini when hovering over an option."""
        namespace_option: PatcherNamespace | None = cast(PatcherNamespace, self.namespaces_combobox.value.patcher_namespace)  # type: ignore[]
        return "" if namespace_option is None else namespace_option.description

    def lowercase_files_and_folders(  # noqa: C901
        self,
        directory: os.PathLike | str | None = None,
        *,
        reset_namespace: bool = False,
    ):
        if not directory:
            results: str | None = self.open_folder_dialog("Select the folder to recursively lowercase.")
            if not results or not Path(results[0]).is_dir():
                return  # User cancelled the dialog
            directory = Path(results[0])
        try:

            def task(app: toga.App | None = None, **kwargs):  # noqa: ARG001
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
                    Path(directory).rename(Path.str_norm(str(directory).lower()))  # noqa: SLF001
                except Exception as e:  # noqa: BLE001
                    self._handle_general_exception(e)
                finally:
                    self.add_background_task(lambda app, **kwargs: self.set_state(state=False))  # noqa: ARG005
                    if not made_change:
                        self.logger.add_note("Nothing to change - all files/folders already correct case.")
                    self.logger.add_note("iOS case rename task completed.")

            self.add_background_task(task)
        except Exception as e2:  # noqa: BLE001
            self._handle_general_exception(e2)
        finally:
            if reset_namespace and self.mod_path:
                self.refresh_ui_data()
            self.logger.add_verbose("iOS case rename task started.")

    def refresh_ui_data(
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
            namespace_option: PatcherNamespace = self.namespaces_combobox.value.patcher_namespace  # type: ignore[]
            changes_ini_path = CaseAwarePath(self.mod_path, "tslpatchdata", namespace_option.changes_filepath())
            reader: ConfigReader = config_reader or ConfigReader.from_filepath(changes_ini_path)
            reader.load_settings()
            self.log_level = reader.config.log_level

            # Filter the listed games in the combobox with the mod's supported ones.
            game_number: int | None = reader.config.game_number
            if game_number:
                game = Game(game_number)
                kotor_paths_stringlist: list[str] = [
                    str(path)
                    for game_key in reversed([game] + ([Game.K1] if game == Game.K2 else []))
                    for path in find_kotor_paths_from_default()[game_key]
                ]
                self.gamepaths.items = kotor_paths_stringlist
                self.gamepaths.value = kotor_paths_stringlist[0] if kotor_paths_stringlist else None

            # Strip info.rtf and display in the main window frame.
            info_rtf_path = CaseAwarePath(self.mod_path, "tslpatchdata", namespace_option.rtf_filepath())
            info_rte_path = CaseAwarePath(self.mod_path, "tslpatchdata", namespace_option.rtf_filepath()).with_suffix(".rte")
            if not info_rtf_path.is_file() and not info_rte_path.is_file():
                self.run_later(self.display_error_dialog("No info.rtf", f"Could not load the info rtf for this mod, file '{info_rtf_path}' not found on disk."))
                return

            if info_rte_path.is_file():
                data: bytes = BinaryReader.load_file(info_rte_path)
                rtf_text: str = decode_bytes_with_fallbacks(data, errors="replace")
                self.load_rte_content(rtf_text)
            elif info_rtf_path.is_file():
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
            self.run_later(
                self.display_error_dialog(
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
        self.namespaces_combobox.items = ListSource(data=namespaces, accessors=["patcher_namespace"])
        self.refresh_ui_data(config_reader=config_reader)

    def open_mod(
        self,
        directory_path_str: os.PathLike | str | None = None,
        exc: BaseException | None = None,
        *,
        startup: bool = False,
    ):
        """Opens a mod directory.

        Args:
        ----
            directory_path_str: The default directory path to open as a string or None. This is
                relevant when HoloPatcher is placed next to a 'tslpatchdata' folder containing the patcher files.
                This is also relevant when using the CLI.
        """
        print(f"open_mod({directory_path_str}, {exc})")
        try:
            if not directory_path_str:
                directory_path_str = self.open_folder_dialog("Select the mod directory (where tslpatchdata lives)")
                if not directory_path_str or not directory_path_str.strip():
                    return
            # handle when a user selects 'tslpatchdata' instead of mod root
            tslpatchdata_path = CaseAwarePath(directory_path_str, "tslpatchdata")
            if not tslpatchdata_path.is_dir() and tslpatchdata_path.parent.name.lower() == "tslpatchdata":
                tslpatchdata_path = tslpatchdata_path.parent

            self.mod_path = str(tslpatchdata_path.parent)
            namespace_path: CaseAwarePath = tslpatchdata_path / "namespaces.ini"
            changes_path: CaseAwarePath = tslpatchdata_path / "changes.ini"

            if namespace_path.is_file():
                print("FOUND namespace_path:", namespace_path)
                self.load_namespace(NamespaceReader.from_filepath(namespace_path))

            elif changes_path.is_file():
                print("FOUND changes_path:", changes_path, "namespace_path not found:", namespace_path)
                config_reader: ConfigReader = ConfigReader.from_filepath(changes_path)
                namespaces: list[PatcherNamespace] = [config_reader.config.as_namespace(changes_path)]
                self.load_namespace(namespaces, config_reader)

            else:
                print("namespace_path not found:", namespace_path, "changes_path not found:", changes_path)
                self.mod_path = ""
                if not startup:  # don't show the error if the cwd was attempted
                    self.run_later(self.display_error_dialog("Error", f"Could not find a mod located chosen target '{directory_path_str}'"))
                return
            self.check_access(tslpatchdata_path, recurse=True, should_filter=True)

        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            self._handle_general_exception(e, "An unexpected error occurred while loading the mod info.")

        else:  # Mod dir is valid at this point.
            if startup:
                self.browse_button.style.visibility = "hidden"
                if not namespace_path.is_file():
                    self.namespaces_combobox.style.visibility = "hidden"
                    self.expand_namespace_description_button.style.visibility = "hidden"

    def open_kotor(
        self,
        directory_path_str: os.PathLike | str | None = None,
        exc: BaseException | None = None,
        *,
        startup: bool = True,
    ):
        """Opens the KOTOR directory.

        Args:
        ----
            directory_path_str: The default KOTOR directory path as a string. This is only relevant when using the CLI.
        """
        print(f"open_kotor({directory_path_str}, {exc}, startup={startup})")
        try:
            if directory_path_str is None:
                directory_path_str = self.open_folder_dialog("Select the KOTOR directory")
                if not directory_path_str or not directory_path_str.strip():
                    return

            directory = str(CaseAwarePath(directory_path_str).resolve())
            self.check_access(Path(directory))
            if directory not in [str(item) for item in self.gamepaths.items]:
                self.gamepaths.items.append(directory)
            self.gamepaths.value = directory

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

            # Play the system "error" sound
            winsound.MessageBeep(winsound.MB_ICONHAND)

    def fix_permissions(
        self,
        directory: os.PathLike | str | None = None,
        reset_namespace: bool = False,
        check: bool = False,
    ):
        path_arg = askdirectory() if directory is None else directory
        if not path_arg:
            return
        if not directory and not askyesno("Warning!", "This is not a toy. Really continue?"):
            return

        try:
            path: Path = Path(path_arg)

            def task(app: toga.App | None = None, **kwargs) -> bool:
                extra_msg: str = ""
                self.set_state(state=True)
                self.clear_main_text()
                self.logger.add_note("Please wait, this may take awhile...")
                try:
                    access: bool = path.gain_access(recurse=True, log_func=self.logger.add_verbose)
                    # self.play_complete_sound()
                    if not access:
                        if not directory:
                            self.run_later(self.display_error_dialog("Could not acquire permission!", "Permissions denied! Check the logs for more details."))
                        else:
                            self.run_later(self.display_error_dialog(
                                "Could not gain permission!",
                                f"Permission denied to {directory}. Please run HoloPatcher with elevated permissions, and ensure the selected folder exists and is writeable.",
                            ))
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
                    self.run_later(self.display_info_dialog("Successfully acquired permission", f"The operation was successful. {extra_msg}"))

                except Exception as e:  # noqa: BLE001
                    self._handle_general_exception(e)
                    return False
                else:
                    return True
                finally:
                    self.set_state(state=False)
                    self.logger.add_note("File/Folder permissions fixer task completed.")

            self.add_background_task(task)
        except Exception as e2:  # noqa: BLE001
            self._handle_general_exception(e2)
        finally:
            if reset_namespace and self.mod_path:
                self.refresh_ui_data()
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
        filter_results: Callable[[Path], bool] | None = None
        if should_filter:

            def filter_results(x: Path) -> bool:
                return not ResourceIdentifier.from_path(x).restype.is_invalid

        print("check_access frontend: call backend has_access")
        if directory.has_access(recurse=recurse, filter_results=filter_results):
            return True
        if askyesno(
            "Permission error",
            f"HoloPatcher does not have permissions to the path '{directory}', would you like to attempt to gain permission automatically?",
        ):
            directory.gain_access(recurse=recurse)
            self.refresh_ui_data()
        if not directory.has_access(recurse=recurse):
            showerror(
                "Unauthorized",
                (
                    f"HoloPatcher needs permissions to access '{directory}'. {os.linesep}"
                    f"{os.linesep}"
                    f"Please ensure the necessary folders are writeable or rerun holopatcher with elevated privileges.{os.linesep}"
                    "Continue with an install anyway?"
                ),
            )
            return False
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
            self.run_later(
                self.display_info_dialog(
                    "Task already running",
                    "Wait for the previous task to finish.",
                )
            )
            return False
        if not self.mod_path or not CaseAwarePath(self.mod_path).is_dir():
            self.run_later(
                self.display_error_dialog(
                    "No mod chosen",
                    "Select your mod directory first.",
                )
            )
            return False
        game_path: str = str(self.gamepaths.value)
        if not game_path:
            self.run_later(
                self.display_error_dialog(
                    "No KOTOR directory chosen",
                    "Select your KOTOR directory first.",
                )
            )
            return False
        case_game_path = CaseAwarePath(game_path)
        if not case_game_path.is_dir():
            self.run_later(
                self.display_error_dialog(
                    "Invalid KOTOR directory chosen",
                    "Select a valid path to your KOTOR install.",
                )
            )
            return False
        print("preinstall validation: check access")
        return self.check_access(Path(str(case_game_path)))

    def begin_install(self, button: toga.Button | None = None):
        """Starts the installation process in a background thread.

        Note: This function is not called when utilizing the CLI due to the thread creation - for passthrough purposes.

        Processing Logic:
        ----------------
            - Starts a new Thread to run the installation in the background
            - Catches any exceptions during thread start and displays error message
            - Exits program if exception occurs during installation thread start.

        """
        print("Call begin_install")
        try:
            if not self.preinstall_validate_chosen():
                return
            print("Preinstall validated")
            self.set_state(state=True)
            install_message = f"Starting install...{os.linesep}".replace("\n", "<br>")
            self.web_view.evaluate_javascript(f"setContent('{install_message}');")

            namespace_option: PatcherNamespace = self.namespaces_combobox.value.patcher_namespace  # type: ignore[]

            self.pykotor_logger.debug("Prevalidate finished, starting install thread")
            print("Start progress bar")
            tslpatchdata_path = CaseAwarePath(self.mod_path, "tslpatchdata")
            ini_file_path = tslpatchdata_path.joinpath(namespace_option.changes_filepath())
            namespace_mod_path: CaseAwarePath = ini_file_path.parent
            installer = ModInstaller(namespace_mod_path, str(self.gamepaths.value), ini_file_path, self.logger)
            installer.tslpatchdata_path = tslpatchdata_path
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
            self.progress_bar.start()
            self.task_thread = threading.Thread(target=self.begin_install_thread, args=(installer, self.update_progress_bar_directly), name="HoloPatcher_install_thread")
            self.task_thread.start()
            print("Started installer in background task")

        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            self._handle_general_exception(e, "An unexpected error occurred during the installation and the program was forced to exit")
        finally:
            self.set_state(state=False)

    def begin_install_thread(
        self,
        installer: ModInstaller,
        update_progress_func: Callable | None = None,
        **kwargs,
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
        print("begin_install_thread reached")
        try:
            self._execute_mod_install(installer, update_progress_func=update_progress_func)
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            self._handle_exception_during_install(e)
        finally:
            self.set_state(state=False)  # noqa: ARG005

    def _execute_mod_install(  # noqa: PLR0915
        self,
        installer: ModInstaller,
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
        print("execute_mod_install reached.")
        try:
            confirm_msg: str = installer.config().confirm_message.strip()
            if confirm_msg and not self.one_shot and confirm_msg.upper() != "N/A":
                # Show a confirmation dialog
                print("Show confirm dialog")
                if not askokcancel("This mod requires confirmation", confirm_msg):
                    print("User did not confirm.")
                    return  # If the dialog returns False, stop the execution
                print("confirm dialog passed.")
            # profiler = cProfile.Profile()
            # profiler.enable()
            print("Jump to ModInstaller code.")
            install_start_time: datetime = datetime.now(timezone.utc).astimezone()
            installer.install(None, update_progress_func)
            total_install_time: timedelta = datetime.now(timezone.utc).astimezone() - install_start_time
            print("install complete")
            # profiler.disable()
            # profiler_output_file = Path("profiler_output.pstat").resolve()
            # profiler.dump_stats(str(profiler_output_file))

            print("calculate how long the install took")
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
                print("show error dialog postinstall")
                self.run_later(
                    self.display_error_dialog(
                        "Install completed with errors!",
                        f"The install completed with {num_errors} errors and {num_warnings} warnings! The installation may not have been successful, check the logs for more details."  # noqa: E501
                        f"{os.linesep * 2}Total install time: {time_str}"
                        f"{os.linesep}Total patches: {num_patches}",
                    )
                )
                if self.one_shot:
                    sys.exit(ExitCode.INSTALL_COMPLETED_WITH_ERRORS)
            elif num_warnings > 0:
                print("show warning dialog postinstall")
                self.run_later(
                    self.display_info_dialog(
                        "Install completed with warnings",
                        f"The install completed with {num_warnings} warnings! Review the logs for details. The script in the 'uninstall' folder of the mod directory will revert these changes."
                        f"{os.linesep * 2}Total install time: {time_str}"
                        f"{os.linesep}Total patches: {num_patches}",
                    )
                )
            else:
                print("show info dialog postinstall")
                self.run_later(
                    self.display_info_dialog(
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
            self.set_state(state=False)  # noqa: ARG005
            self.logger.add_note("Config reader test is complete.")

    def test_reader(self):  # sourcery skip: no-conditionals-in-tests
        if not self.preinstall_validate_chosen():
            return
        namespace_option: PatcherNamespace = self.namespaces_combobox.value.patcher_namespace  # type: ignore[]
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
                self.set_state(state=False)  # noqa: ARG005
                self.logger.add_note("Config reader test is complete.")

        self.add_background_task(lambda app, **kwargs: task)  # noqa: ARG005

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
        else:
            self.initialize_logger()  # reset the errors/warnings etc
        self.task_running = state
        self.install_button.enabled = not state
        self.gamepaths_browse_button.enabled = not state
        self.browse_button.enabled = not state

    def clear_main_text(self):
        """Clears all content from the WebView to prepare for new content."""
        self.web_view.evaluate_javascript("document.getElementById('content').innerHTML = '';")

    @property
    def log_file_path(self) -> Path:
        return Path(self.mod_path) / "installlog.txt"

    async def display_confirm_dialog(self, title: str, message: str) -> bool:
        """Utility to display error dialog on the main thread."""
        if self.one_shot:
            return True
        return await self.main_window.confirm_dialog(title, message)

    async def display_info_dialog(self, title: str, message: str):
        """Utility to display error dialog on the main thread."""
        if self.one_shot:
            print(title, message)
        await self.main_window.info_dialog(title, message)

    async def display_error_dialog(self, title: str, message: str):
        """Utility to display error dialog on the main thread."""
        if self.one_shot:
            print(title, message, file=sys.stderr)
        await self.main_window.error_dialog(title, message)

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
        self.logger.add_error(
            f"{error_name}: {msg}{os.linesep}The installation was aborted with errors"
        )

        showerror(
            error_name,
            f"An unexpected error occurred during the installation and the installation was forced to terminate.{os.linesep * 2}{msg}",
        )
        raise

    def create_rte_content(self):
        from utility.tkinter.rte_editor import main as start_rte_editor

        start_rte_editor()

    def load_rte_content(  # noqa: C901, PLR0912, PLR0915
        self, rte_content: str | bytes | bytearray | None = None
    ):
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

        self.web_view.evaluate_javascript(f"setContent({content});")

    def load_rtf_content(self, rtf_text: str):
        """Converts the RTF content to HTML and displays it in the WebView."""
        self.clear_main_text()
        try:
            try:
                html_content = pypandoc.convert_text(rtf_text, "html", format="rtf")
            except OSError:
                # Download Pandoc if it is not installed
                pypandoc.download_pandoc(delete_installer=True)
                html_content = pypandoc.convert_text(rtf_text, "html", format="rtf")
        except Exception:  # noqa: BLE001
            RobustLogger().exception("Failed to load RTF content. Falling back to plaintext...")
            html_content: str = striprtf(rtf_text)

        safe_html_content = json.dumps(html_content)
        self.web_view.evaluate_javascript(f"setContent({safe_html_content});")

    def write_log(self, log: PatchLog):
        """Writes a message to the log.

        Args:
        ----
            log: PatchLog - The log object containing the message and type.
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
            if log.log_type.value < log_type_to_level().value:
                print(log.log_type.value, "<", self.log_level.value)
                return
        except OSError:
            RobustLogger().exception(f"Failed to write the log file at '{self.log_file_path}'!")

        def update_ui(app: toga.App, **kwargs):  # noqa: ARG001
            log_tag = log_type_to_tag(log)
            # Safely escape the log message for JavaScript execution
            log_message = log.formatted_message.replace("\\", "\\\\").replace("'", "\\'")
            script = f"appendLogLine('{log_message}', '{log_tag}');"
            print(f"evaluating script '{script}'")
            self.web_view.evaluate_javascript(script)

        if threading.current_thread() == threading.main_thread():
            print("update ui (main thread)")
            update_ui(self)
            print("update ui completed (main thread)")
        else:
            print("update ui (OTHER thread)")
            self.add_background_task(update_ui)
            print("update ui completed (OTHER thread)")

    def set_content(self, new_content: str):
        script = f"setContent({json.dumps(new_content)});"
        self.web_view.evaluate_javascript(script)

    def open_file_dialog(self, title: str = "Select the file target.") -> str:
        try:
            return askopenfilename(title=title)
        except Exception:  # noqa: BLE001
            RobustLogger().exception("An error occurred while a file browser was running. Falling back to the Toga variant.")
            return self.run_async_from_sync(self.main_window.open_file_dialog(title))

    def open_folder_dialog(self, title: str = "Select the folder target.") -> str:
        try:
            return askdirectory(title=title)
        except Exception:  # noqa: BLE001
            RobustLogger().exception("An error occurred while a file browser was running. Falling back to the Toga variant.")
            return self.run_async_from_sync(self.main_window.select_folder_dialog(title))


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
        from threading import Thread
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
    RobustLogger().error("Unhandled exception caught.", exc_info=(etype, exc, tback))

    showerror(title, short_msg)
    sys.exit(ExitCode.CRASH)


sys.excepthook = onAppCrash


def hp_exit_cleanup(app: HoloPatcher):
    """Prevents the patcher from running in the background after sys.exit is called."""
    print("Fully shutting down HoloPatcher...")
    if app.main_window is not None:
        app.main_window.close()
    app.exit()
    terminate_main_process()


def main():
    app = HoloPatcher(formal_name="HoloPatcher", app_id="com.pykotor.holopatcher")
    atexit.register(lambda: hp_exit_cleanup(app))
    app.main_loop()


if __name__ == "__main__":
    # fast fail if the user is running from their temp folder (i.e they probably didn't extract the app from the archive)
    if str(Path(sys.executable)).startswith(tempfile.gettempdir()):
        with suppress(Exception):
            showerror("Error", "This application cannot be run from within a zip or temporary directory. Please extract it to a permanent location before running.")
        sys.exit("Exiting: Application was run from a temporary or zip directory.")

    main()
