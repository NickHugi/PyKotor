from __future__ import annotations

import contextlib
import ctypes
import os
import pathlib
import re
import shutil
import sys
import tkinter as tk
import traceback
from argparse import ArgumentParser, Namespace
from configparser import ConfigParser
from datetime import datetime, timedelta, timezone
from enum import IntEnum
from threading import Thread
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont

if not getattr(sys, "frozen", False):
    thisfile_path = pathlib.Path(__file__).resolve()
    project_root = thisfile_path.parents[2]
    if project_root.joinpath("pykotor").exists():
        sys.path.append(str(project_root))

from typing import TYPE_CHECKING, NoReturn

from pykotor.common.misc import CaseInsensitiveDict, Game
from pykotor.tools.misc import striprtf, universal_simplify_exception
from pykotor.tools.path import CaseAwarePath, Path, locate_game_paths
from pykotor.tslpatcher.config import ModInstaller, PatcherNamespace
from pykotor.tslpatcher.logger import PatchLogger
from pykotor.tslpatcher.reader import NamespaceReader

if TYPE_CHECKING:
    from io import TextIOWrapper


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

        self.mod_path = ""
        self.namespaces = []

        self.initialize_logger()
        self.set_window(width=400, height=500)
        self.namespaces_combobox = ttk.Combobox(self, state="readonly")
        self.namespaces_combobox.set("Select the mod to install")
        self.namespaces_combobox.place(x=5, y=5, width=310, height=25)
        self.namespaces_combobox.bind("<<ComboboxSelected>>", self.on_namespace_option_chosen)

        self.browse_button = ttk.Button(self, text="Browse", command=self.open_mod)
        self.browse_button.place(x=320, y=5, width=75, height=25)

        self.gamepaths = ttk.Combobox(self)
        self.gamepaths.set("Select your KOTOR directory path")
        self.gamepaths.place(x=5, y=35, width=310, height=25)
        self.gamepaths["values"] = [str(path) for game in locate_game_paths().values() for path in game]
        self.gamepaths.bind("<<ComboboxSelected>>", self.on_gamepaths_chosen)

        self.gamepaths_browse_button = ttk.Button(self, text="Browse", command=self.open_kotor)
        self.gamepaths_browse_button.place(x=320, y=35, width=75, height=25)

        self.exit_button = ttk.Button(self, text="Exit", command=self.handle_exit_button)
        self.exit_button.place(x=5, y=470, width=75, height=25)

        self.install_button = ttk.Button(self, text="Install", command=self.begin_install)
        self.install_button.place(x=320, y=470, width=75, height=25)

        self.uninstall_button = ttk.Button(self, text="Uninstall", command=self.uninstall_selected_mod)
        self.uninstall_button.place(x=160, y=470, width=75, height=25)
        self.uninstall_button.place_forget()  # comment this to enable the uninstall button.

        # Create a Frame to hold the Text and Scrollbar widgets
        text_frame = tk.Frame(self)
        text_frame.place(x=5, y=65, width=390, height=400)

        # Create the Scrollbar and pack it to the right side of the Frame
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create the Text widget with word wrapping and pack it to the left side of the Frame
        self.description_text = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set)
        # Get the current font properties
        font_obj = tkfont.Font(font=self.description_text.cget("font"))
        font_obj.configure(size=9)
        self.description_text.configure(font=font_obj)
        self.description_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        # Link the Scrollbar to the Text widget
        scrollbar.config(command=self.description_text.yview)

        self.install_running = False
        self.protocol("WM_DELETE_WINDOW", self.handle_exit_button)

        cmdline_args = parse_args()
        self.open_mod(cmdline_args.tslpatchdata or CaseAwarePath.cwd())
        self.handle_commandline(cmdline_args)

    def handle_commandline(self, cmdline_args: Namespace) -> None:
        if cmdline_args.game_dir:
            self.open_kotor(cmdline_args.game_dir)
        if cmdline_args.namespace_option_index:
            self.namespaces_combobox.set(self.namespaces_combobox["values"][cmdline_args.namespace_option_index])
        if not cmdline_args.console:
            self.hide_console()
        if cmdline_args.install or cmdline_args.uninstall:
            self.withdraw()
            self.handle_console_mode()
        self.one_shot: bool = False
        if cmdline_args.install:
            self.one_shot = True
            self.begin_install_thread()
            sys.exit()
        if cmdline_args.uninstall:
            self.one_shot = True
            self.uninstall_selected_mod()
            sys.exit()

    def handle_console_mode(self) -> None:
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

    def initialize_logger(self):
        self.logger = PatchLogger()
        self.logger.verbose_observable.subscribe(self.write_log)
        self.logger.note_observable.subscribe(self.write_log)
        self.logger.warning_observable.subscribe(self.write_log)
        self.logger.error_observable.subscribe(self.write_log)

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

    def hide_console(self) -> None:
        """Hide the console window in GUI mode."""
        # Windows
        if os.name == "nt":
            import ctypes

            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

    def uninstall_selected_mod(self) -> None:
        if self.install_running:
            messagebox.showerror("An install is already running!", "Please wait for all operations to finish")
            return
        namespace_option = next((x for x in self.namespaces if x.name == self.namespaces_combobox.get()), None)
        if not self.namespaces or not namespace_option:
            messagebox.showerror("No mod loaded", "Load/select a mod first.")
            return
        destination_folder = Path(self.gamepaths.get())
        if not destination_folder.exists():
            messagebox.showerror("No game path selected", "Select your KOTOR directory first")
            return
        backup_parent_folder = Path(self.mod_path, "backup")
        if not backup_parent_folder.exists():
            messagebox.showerror(
                "Backup folder empty/missing.",
                f"Could not find backup folder '{backup_parent_folder}'{os.linesep*2}Are you sure the mod is installed?",
            )
            return

        self._clear_description_textbox()
        sorted_backup_folders: list[tuple[Path, datetime]] = []
        for folder in backup_parent_folder.iterdir():
            try:
                dt = datetime.strptime(folder.name, "%Y-%m-%d_%H.%M.%S").astimezone()
                self.write_log(f"Found backup '{folder.name}'")
                sorted_backup_folders.append((folder, dt))
            except ValueError:  # noqa: PERF203
                if folder.name.strip():
                    self.write_log(f"Ignoring directory '{folder.name}' because it is not timestamped as '%Y-%m-%d_%H.%M.%S'")

        if not sorted_backup_folders:
            messagebox.showerror(
                "No backups found!",
                f"No backups found at '{backup_parent_folder}'!{os.linesep}HoloPatcher cannot uninstall TSLPatcher.exe installations.",
            )
            return
        sorted_backup_folders.sort(key=lambda x: x[1], reverse=True)
        most_recent_backup_folder: Path = backup_parent_folder / str(sorted_backup_folders[0][0])
        self.write_log(f"Using backup folder '{most_recent_backup_folder}'")
        delete_list_file = most_recent_backup_folder / "remove these files.txt"
        if not delete_list_file.exists():
            # messagebox.showerror(
            #     "File list missing from backup",
            #     f"'remove these files.txt' missing from backup '{most_recent_backup_folder}', cannot restore backup.",  # noqa: ERA001
            # )  # noqa: ERA001, RUF100
            # return  # noqa: ERA001, RUF100
            pass
        existing_files = set()
        line: str
        if delete_list_file.exists():
            missing_files = False
            with delete_list_file.open("r") as f:
                for line in f:
                    line = line.strip()  # noqa: PLW2901

                    if line:
                        if Path(line).safe_isfile():
                            existing_files.add(line)
                        else:
                            missing_files = True
                            print(f"ERROR! {line} no longer exists!")
            if missing_files:
                messagebox.showerror(
                    "Backup out of date or mismatched",
                    (
                        f"This backup doesn't match your current KOTOR installation. Files are missing/changed in your KOTOR install.{os.linesep}"
                        f"It is important that you uninstall all mods in their installed order when utilizing this feature.{os.linesep}"
                        f"Also ensure you selected the right mod, and the right KOTOR folder."
                    ),
                )
                return
        all_items_in_backup = list(Path(most_recent_backup_folder).safe_rglob("*"))
        files_in_backup: list[Path] = [item for item in all_items_in_backup if item.safe_isfile()]
        folder_count: int = len(all_items_in_backup) - len(files_in_backup)

        if len(files_in_backup) < 6:  # noqa: PLR2004[6 represents a small number of files to display]
            for item in files_in_backup:
                self.write_log(f"Would restore file '{item.relative_to(most_recent_backup_folder)!s}'")
        if not messagebox.askyesno(
            "Confirmation",
            f"Really uninstall {len(existing_files)} files and restore the most recent backup (containing {len(files_in_backup)} files and {folder_count} folders)?",
        ):
            return
        deleted_count = 0

        try:
            for file in existing_files:
                file_path = Path(file)
                if file_path.exists():
                    file_path.unlink()
                    self.write_log(f"Removed {file}...")
                    deleted_count += 1
            for file_path in files_in_backup:
                destination_path = destination_folder / file_path.relative_to(most_recent_backup_folder)
                destination_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(file_path, destination_path)
                self.write_log(
                    f"Restoring backup of '{file_path.name}' to '{destination_path.relative_to(destination_folder.parent)}'...",
                )
        except Exception as e:  # noqa: BLE001
            error_name, msg = universal_simplify_exception(e)
            messagebox.showerror(
                error_name,
                f"Failed to restore backup because of exception:{os.linesep*2}{msg}",
            )
            return
        while messagebox.askyesno(
            "Uninstall completed!",
            f"Deleted {deleted_count} files and successfully restored backup {most_recent_backup_folder.name}{os.linesep*2}"
            f"Would you like to delete the backup {most_recent_backup_folder.name} now that it's been restored?",
        ):
            try:
                shutil.rmtree(most_recent_backup_folder)
                self.write_log(f"Deleted restored backup '{most_recent_backup_folder.name}'")
                break
            except PermissionError:
                messagebox.showerror(
                    "Permission Error",
                    "Unable to delete the restored backup due to permission issues. Please try again.",
                )

    def handle_exit_button(self) -> None:
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

    def on_gamepaths_chosen(self, event) -> None:
        self.after(10, self.move_cursor_to_end)

    def move_cursor_to_end(self) -> None:
        self.gamepaths.focus_set()
        position: int = len(self.gamepaths.get())
        self.gamepaths.icursor(position)
        self.gamepaths.xview(position)

    def on_namespace_option_chosen(self, event) -> None:
        try:
            namespace_option: PatcherNamespace = next(x for x in self.namespaces if x.name == self.namespaces_combobox.get())
            changes_ini_path = CaseAwarePath(self.mod_path, "tslpatchdata", namespace_option.changes_filepath())
            game_number: int | None = self.extract_lookup_game_number(changes_ini_path)
            if game_number:
                self._handle_gamepaths_with_mod(game_number)
            info_rtf = CaseAwarePath(self.mod_path, "tslpatchdata", namespace_option.rtf_filepath())
            if not info_rtf.exists():
                messagebox.showwarning("No info.rtf", "Could not load the rtf for this mod, file not found on disk.")
                return
            with info_rtf.open("r") as rtf:
                self.set_stripped_rtf_text(rtf)
        except Exception as e:  # noqa: BLE001
            error_name, msg = universal_simplify_exception(e)
            messagebox.showerror(
                error_name,
                f"An unexpected error occurred while loading the namespace option.{os.linesep*2}{msg}",
            )

    def extract_lookup_game_number(self, changes_path: Path) -> int | None:
        if not changes_path.exists():
            return None
        pattern = r"LookupGameNumber=(\d+)"
        with changes_path.open("r", encoding="utf-8") as file:
            for line in file:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    return int(match[1])
        return None

    def check_access(self, directory: Path, recurse=False) -> bool:
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
                    f"Please ensure the folder is writeable or rerun holopatcher with elevated privileges.{os.linesep}"
                    "Continue with an install anyway?"
                ),
            )
        return True

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

            namespace_path: CaseAwarePath = tslpatchdata_path / "namespaces.ini"
            changes_path: CaseAwarePath = tslpatchdata_path / "changes.ini"

            if namespace_path.exists():
                namespaces = NamespaceReader.from_filepath(namespace_path)
                self.load_namespace(namespaces)
                if default_directory_path_str:
                    self.browse_button.place_forget()
            elif changes_path.exists():
                namespaces = [self.build_changes_as_namespace(changes_path)]
                self.load_namespace(namespaces)
                if default_directory_path_str:
                    self.browse_button.place_forget()
            else:
                self.mod_path = ""
                if not default_directory_path_str:  # don't show the error if the cwd was attempted
                    messagebox.showerror("Error", "Could not find a mod located at the given folder.")
                return

            self.check_access(tslpatchdata_path, recurse=True)
        except Exception as e:  # noqa: BLE001
            error_name, msg = universal_simplify_exception(e)
            messagebox.showerror(
                error_name,
                f"An unexpected error occurred while loading mod info.{os.linesep*2}{msg}",
            )

    def open_kotor(self, default_kotor_dir_str=None) -> None:
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

    def preinstall_validate_chosen(self) -> bool:
        def _if_missing(title, message):
            messagebox.showinfo(title, message)
            if self.one_shot:
                sys.exit(ExitCode.NUMBER_OF_ARGS)
            return False

        if self.install_running:
            messagebox.showinfo(
                "Install already running",
                "Cannot start an install while the previous installation is still ongoing",
            )
            return False
        if not self.mod_path or not CaseAwarePath(self.mod_path).exists():
            return _if_missing(
                "No mod chosen",
                "Select your mod directory before starting an install",
            )
        game_path = self.gamepaths.get()
        if not game_path or not CaseAwarePath(game_path).exists():
            return _if_missing(
                "No KOTOR directory chosen",
                "Select your KOTOR install before starting an install.",
            )
        return self.check_access(Path(self.gamepaths.get()))

    def begin_install(self) -> None:
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
        if not self.preinstall_validate_chosen():
            return
        namespace_option: PatcherNamespace = next(x for x in self.namespaces if x.name == self.namespaces_combobox.get())
        ini_file_path = CaseAwarePath(self.mod_path, "tslpatchdata", namespace_option.changes_filepath())
        namespace_mod_path: CaseAwarePath = ini_file_path.parent

        self._clear_description_textbox()
        installer = ModInstaller(namespace_mod_path, self.gamepaths.get(), ini_file_path, self.logger)
        try:
            self._execute_mod_install(installer)
        except Exception as e:  # noqa: BLE001
            self._handle_exception_during_install(e, installer)
        self.set_active_install(install_running=False)

    def set_active_install(self, install_running: bool) -> None:
        if install_running:
            self.install_running = True
            self.install_button.config(state=tk.DISABLED)
            self.uninstall_button.config(state=tk.DISABLED)
            self.gamepaths_browse_button.config(state=tk.DISABLED)
            self.browse_button.config(state=tk.DISABLED)
        else:
            self.install_running = False
            self.install_button.config(state=tk.NORMAL)
            self.uninstall_button.config(state=tk.NORMAL)
            self.gamepaths_browse_button.config(state=tk.NORMAL)
            self.browse_button.config(state=tk.NORMAL)

    def _clear_description_textbox(self) -> None:
        self.description_text.config(state=tk.NORMAL)
        self.description_text.delete(1.0, tk.END)
        self.description_text.config(state=tk.DISABLED)

    def _execute_mod_install(self, installer: ModInstaller) -> None:
        self.set_active_install(install_running=True)
        install_start_time: datetime = datetime.now(timezone.utc).astimezone()
        installer.install()
        total_install_time: timedelta = datetime.now(timezone.utc).astimezone() - install_start_time

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
        log_file_path: Path = Path(self.mod_path, "installlog.txt")
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

    def _handle_exception_during_install(self, e: Exception, installer: ModInstaller) -> NoReturn:
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

    def build_changes_as_namespace(self, filepath: CaseAwarePath) -> PatcherNamespace:
        with filepath.open() as file:
            ini = ConfigParser(
                delimiters=("="),
                allow_no_value=True,
                strict=False,
                interpolation=None,
            )
            # use case sensitive keys
            ini.optionxform = lambda optionstr: optionstr  # type: ignore[method-assign]
            ini.read_string(file.read())

            namespace = PatcherNamespace()
            namespace.ini_filename = "changes.ini"
            namespace.info_filename = "info.rtf"
            settings_section = next(
                (section for section in ini.sections() if section.lower() == "settings"),
                None,
            )
            if not settings_section:
                namespace.name = "<< Untitled Mod Loaded >>"
                return namespace
            settings_ini = CaseInsensitiveDict(ini[settings_section].items())
            namespace.name = settings_ini.get("WindowCaption", "<< Untitled Mod Loaded >>")

        return namespace

    def load_namespace(self, namespaces: list[PatcherNamespace]) -> None:
        self.namespaces_combobox["values"] = namespaces
        self.namespaces_combobox.set(self.namespaces_combobox["values"][0])
        self.namespaces = namespaces
        self.on_namespace_option_chosen(None)

    def _handle_gamepaths_with_mod(self, game_number) -> None:
        game = Game(game_number)
        gamepaths_list: list[str] = [
            str(path)
            for game_key in ([game] + ([Game.K1] if game == Game.K2 else []))
            for path in locate_game_paths()[game_key]
        ]
        self.gamepaths["values"] = gamepaths_list

    def set_stripped_rtf_text(self, rtf: TextIOWrapper) -> None:
        stripped_content: str = striprtf(rtf.read())
        self.description_text.config(state=tk.NORMAL)
        self.description_text.delete(1.0, tk.END)
        self.description_text.insert(tk.END, stripped_content)
        self.description_text.config(state=tk.DISABLED)

    def write_log(self, message: str) -> None:
        """Writes a message to the log.

        Args:
        ----
            message (str): The message to write to the log.

        Returns:
        -------
            None
        Processes the log message by:
            - Setting the description text widget to editable
            - Inserting the message plus a newline at the end of the text
            - Scrolling to the end of the text
            - Making the description text widget not editable again.
        """
        self.description_text.config(state=tk.NORMAL)
        self.description_text.insert(tk.END, message + os.linesep)
        self.description_text.see(tk.END)
        self.description_text.config(state=tk.DISABLED)


# when pyinstaller compiled in console mode, this will match the same error message behavior of --noconsole.
def custom_excepthook(exc_type, exc_value, exc_traceback) -> None:
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
