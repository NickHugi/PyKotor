from __future__ import annotations

import atexit
import faulthandler
import os
import pathlib
import platform
import shutil
import subprocess
import sys
import tempfile
import time

from collections import OrderedDict
from contextlib import suppress
from datetime import datetime
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Any, Set, cast

import qtpy
import send2trash

from qtpy.QtCore import QUrl, Qt
from qtpy.QtGui import QDesktopServices, QKeySequence
from qtpy.QtWidgets import (
    QAction,
    QApplication,
    QCheckBox,
    QFileDialog,
    QHeaderView,
    QInputDialog,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableView,
    QTableWidget,
    QTableWidgetItem,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

if qtpy.API_NAME in ("PyQt6", "PySide6"):
    ...
else:
    from qtpy.QtWidgets import QDesktopWidget

if __name__ == "__main__":
    with suppress(Exception):
        def update_sys_path(path: pathlib.Path):
            working_dir = str(path)
            if working_dir not in sys.path:
                sys.path.append(working_dir)

        file_absolute_path = pathlib.Path(__file__).resolve()

        pykotor_path = file_absolute_path.parents[6] / "Libraries" / "PyKotor" / "src" / "pykotor"
        if pykotor_path.exists():
            update_sys_path(pykotor_path.parent)
        pykotor_gl_path = file_absolute_path.parents[6] / "Libraries" / "PyKotorGL" / "src" / "pykotor"
        if pykotor_gl_path.exists():
            update_sys_path(pykotor_gl_path.parent)
        utility_path = file_absolute_path.parents[6] / "Libraries" / "Utility" / "src"
        if utility_path.exists():
            update_sys_path(utility_path)
        toolset_path = file_absolute_path.parents[3] / "toolset"
        if toolset_path.exists():
            update_sys_path(toolset_path.parent)
            os.chdir(toolset_path)

from pykotor.common.misc import Game
from pykotor.common.stream import BinaryWriterFile
from pykotor.extract.file import FileResource, ResourceIdentifier
from pykotor.extract.installation import Installation
from pykotor.resource.formats.erf.erf_auto import read_erf, write_erf
from pykotor.resource.formats.rim.rim_auto import read_rim, write_rim
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_any_erf_type_file, is_rim_file
from pykotor.tools.path import find_kotor_paths_from_default
from toolset.data.installation import HTInstallation
from toolset.gui.widgets.settings.installations import GlobalSettings
from toolset.utils.window import openResourceEditor
from utility.logger_util import RobustRootLogger
from utility.misc import is_float, is_int
from utility.system.os_helper import get_size_on_disk, win_get_system32_dir
from utility.system.path import Path

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from qtpy.QtCore import QPoint

    from pykotor.extract.file import LocationResult, ResourceResult
    from pykotor.tools.path import CaseAwarePath
    from toolset.gui.editor import Editor


COLUMN_TO_STAT_MAP = {
    "Size": "st_size",
    "Mode": "st_mode",
    "Last Accessed": "st_atime",
    "Last Modified": "st_mtime",
    "Created": "st_ctime",
    "Hard Links": "st_nlink",
    "Last Accessed (ns)": "st_atime_ns",
    "Last Modified (ns)": "st_mtime_ns",
    "Created (ns)": "st_ctime_ns",
    "Inode": "st_ino",
    "Device": "st_dev",
    "User ID": "st_uid",
    "Group ID": "st_gid",
    "File Attributes": "st_file_attributes",
    "Reparse Tag": "st_reparse_tag",
    "Blocks Allocated": "st_blocks",
    "Block Size": "st_blksize",
    "Device ID": "st_rdev",
    "Flags": "st_flags"
}

STAT_TO_COLUMN_MAP = {
    "st_size": "Size",
    "st_mode": "Mode",
    "st_atime": "Last Accessed",
    "st_mtime": "Last Modified",
    "st_ctime": "Created",
    "st_nlink": "Hard Links",
    "st_atime_ns": "Last Accessed (ns)",
    "st_mtime_ns": "Last Modified (ns)",
    "st_ctime_ns": "Created (ns)",
    "st_ino": "Inode",
    "st_dev": "Device",
    "st_uid": "User ID",
    "st_gid": "Group ID",
    "st_file_attributes": "File Attributes",
    "st_reparse_tag": "Reparse Tag",
    "st_blocks": "Blocks Allocated",
    "st_blksize": "Block Size",
    "st_rdev": "Device ID",
    "st_flags": "Flags"
}


def get_sort_key(value):
    """Process the value to determine the appropriate sort key."""
    # sourcery skip: assign-if-exp, reintroduce-else
    if isinstance(value, str):
        if is_int(value.strip()):
            return int(value.strip())
        if is_float(value.strip()):
            return float(value.strip())
    if is_int(value):
        return int(value)
    if is_float(value):
        return float(value)
    return value


class SortableTableWidgetItem(QTableWidgetItem):
    def __init__(self, value, sort_key=None):
        super().__init__(str(value))
        self.sort_key = sort_key if sort_key is not None else value

    def __lt__(self, other):
        if not isinstance(other, QTableWidgetItem):
            return super().__lt__(other)
        other_sort_key = getattr(other, "sort_key", None)
        if isinstance(self.sort_key, (int, float)) and isinstance(other_sort_key, (int, float)):
            return self.sort_key < other.sort_key
        if isinstance(self.sort_key, str) and isinstance(other_sort_key, str):
            return self.sort_key.lower() < other_sort_key.lower()

        my_data = self.data(Qt.UserRole)
        other_data = other.data(Qt.UserRole)

        # Extract and convert data based on your provided logic
        my_sort_key = (
            get_sort_key(my_data if my_data is not None else self.text())
            if self.sort_key is None
            else self.sort_key
        )
        other_sort_key = (
            get_sort_key(other_data if other_data is not None else other_sort_key)
            if other_sort_key is None
            else other_sort_key
        )

        try:
            return my_sort_key < other_sort_key
        except Exception:  # noqa: BLE001
            return str(my_sort_key) < str(other_sort_key)


class FileTableWidgetItem(SortableTableWidgetItem):
    def __init__(self, *args, filepath: Path, **kwargs):
        super().__init__(*args, **kwargs)
        self.filepath: Path = filepath

    def __eq__(self, other):
        if self is other:
            return True
        return isinstance(other, FileTableWidgetItem) and self.filepath == other.filepath

    def __hash__(self):
        return hash(self.filepath)


class ResourceTableWidgetItem(FileTableWidgetItem):
    def __init__(
        self,
        *args,
        resource: FileResource,
        **kwargs,
    ):
        super().__init__(*args, filepath=resource.filepath(), **kwargs)
        self.resource: FileResource = resource

    def __eq__(self, other):
        if self is other:
            return True
        return isinstance(other, ResourceTableWidgetItem) and self.resource == other.resource

    def __hash__(self):
        return hash(self.resource)

class CustomItem:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def create_action(
        self,
        menu_dict: OrderedDict[str, tuple[QAction, Callable]],
        display_name: str,
        func: Callable,
    ) -> QAction:
        action = QAction(display_name)
        menu_dict[display_name] = (action, func)
        return action

    def build_menu(
        self,
        menu: QMenu | None = None,
    ) -> QMenu:
        menu = QMenu() if menu is None else menu
        menu_dict = self.create_context_menu_dict()
        for action, func in menu_dict.values():
            action.setParent(menu)
            action.triggered.connect(func)
            menu.addAction(action)
        return menu

    def create_context_menu_dict(
        self,
    ) -> OrderedDict[str, tuple[QAction, Callable]]:
        menu_dict = OrderedDict()
        selected = self.selectedItems()
        if not selected:
            return menu_dict
        if hasattr(self, "selectedIndexes"):
            self.create_action(menu_dict, "Copy as Text", self.copy_selection_to_clipboard).setShortcut(QKeySequence.StandardKey.Copy)
            self.create_action(menu_dict, "Remove from Table", self.remove_selected_result)

        return menu_dict

    def runContextMenu(self, position: QPoint) -> QAction:
        menu: QMenu = self.build_menu()
        executed_action = menu.exec_(self.viewport().mapToGlobal(position))
        return executed_action  # noqa: RET504


class FileItems(CustomItem):
    def __init__(self, *args, filepaths: list[Path] | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.filepaths: list[Path] = [] if filepaths is None else filepaths
        self.temp_path: Path | None = None

    def selectedItems(self) -> list[FileTableWidgetItem]:
        return [FileTableWidgetItem(value=str(path), filepath=path) for path in self.filepaths]

    def show_confirmation_dialog(
        self,
        icon: QMessageBox.Icon | int,
        title: str,
        text: str,
        buttons: QMessageBox.StandardButton | int = QMessageBox.Yes | QMessageBox.No,
        default_button: QMessageBox.StandardButton | int = QMessageBox.No,
        detailedMsg: str | None = None,
    ) -> int | QMessageBox.StandardButton:
        if not detailedMsg or not detailedMsg.strip():
            selected = cast(Set[FileTableWidgetItem], {*self.selectedItems()})
            detailedMsg = ""
            for selection in selected:
                file_path = selection.filepath
                detailedMsg += f"{file_path}\n" if detailedMsg else file_path

        reply = QMessageBox(
            QMessageBox.Icon.Question,
            title + (" "*1000),
            text + (" "*1000),
            buttons,
            flags=Qt.WindowType.Dialog | Qt.WindowType.WindowDoesNotAcceptFocus | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowSystemMenuHint,
        )
        reply.setDefaultButton(default_button)
        if detailedMsg:
            reply.setDetailedText(detailedMsg.strip())
        return reply.exec_()

    def selected_files_exist(
        self,
        selected: list[FileTableWidgetItem] | set[FileTableWidgetItem],
    ) -> bool:
        return all(Path(tableItem.filepath).safe_exists() for tableItem in {*selected})

    def _rename_file(self, file_path: Path, tableItem: FileTableWidgetItem):
        new_filename, ok = QInputDialog.getText(
            None, "Rename File", "New name:", text=file_path.name
        )
        if ok and new_filename:
            new_path = file_path.with_name(new_filename)
            shutil.move(str(file_path), str(new_path))
            RobustRootLogger().info("Renamed '%s' to '%s'", file_path, new_path)

    def create_context_menu_dict(
        self,
    ) -> OrderedDict[str, tuple[QAction, Callable]]:
        menu_dict = super().create_context_menu_dict()
        selected = cast(Set[FileTableWidgetItem], {*self.selectedItems()})
        if not selected:
            return menu_dict
        openAction = self.create_action(menu_dict, f"Open ({platform.system()})", lambda: self.do_file_action(self._open_file, "Open file(s) with system"))
        openFolderAction = self.create_action(menu_dict, "Open Containing Folder", lambda: self.do_file_action(self._open_containing_folder, "Open Containing Folder"))
        saveSelectedAction = self.create_action(menu_dict, "Save selected files to...", lambda: self.do_file_action(self._save_files, "Save As..."))
        renameAction = self.create_action(menu_dict, "Rename", lambda: self.do_file_action(self._rename_file, "Rename file.", confirmation=True))
        sendToTrash = self.create_action(menu_dict, "Send to Recycle Bin", lambda: self.do_file_action(self._sendToRecycleBin, "Send to Recycle Bin"))
        deleteAction = self.create_action(menu_dict, "Delete PERMANENTLY", lambda: self.do_file_action(self._delete_files_permanently, "Delete PERMANENTLY", confirmation=True))

        file_paths_exist = all(Path(tableItem.filepath).safe_exists() for tableItem in {*selected})
        inside_bif = file_paths_exist and all(isinstance(item, ResourceTableWidgetItem) and item.resource.inside_bif for item in selected)
        inside_capsule = file_paths_exist and all(isinstance(item, ResourceTableWidgetItem) and item.resource.inside_capsule for item in selected)

        if os.name == "nt":
            propertiesAction = self.create_action(menu_dict, "Properties", lambda: self.do_file_action(self._show_properties, "Show File Properties"))
            openWindowsMenuAction = self.create_action(menu_dict, "Open Windows Explorer Context Menu", lambda: self.do_file_action(self._open_windows_explorer_context_menu, "Open Windows Explorer Context Menu"))
            propertiesAction.setEnabled(file_paths_exist)
            openWindowsMenuAction.setEnabled(file_paths_exist)

        openAction.setEnabled(file_paths_exist)
        openFolderAction.setEnabled(file_paths_exist)
        saveSelectedAction.setEnabled(file_paths_exist)
        renameAction.setEnabled(file_paths_exist and len(selected) == 1 and not inside_capsule and not inside_bif)
        sendToTrash.setEnabled(file_paths_exist and not inside_bif)
        deleteAction.setEnabled(file_paths_exist and not inside_bif)

        return menu_dict

    def _open_containing_folder(
        self,
        file_path: Path,
        tableItem: FileTableWidgetItem,
    ):
        file_path = tableItem.filepath  # Don't use arg file_path here, as it might be the tempfile if used with the ResourceWidgetTableItem.

        def run_subprocess(command: list[str], *, check: bool = True):
            try:
                subprocess.run(command, check=check)  # noqa: S603, S607
            except subprocess.CalledProcessError as e:
                if "returned non-zero exit status 1." in str(e) and platform.system() == "Windows":
                    return
                raise

        system = platform.system()

        if system == "Windows":
            explorer_path = win_get_system32_dir().parent / "explorer.exe"
            cmd = [str(explorer_path), "/select,", str(file_path)]
            run_subprocess(cmd)

        elif system == "Darwin":  # macOS
            # Use AppleScript to reveal the file in Finder
            script_reveal = f'tell application "Finder" to reveal POSIX file "{file_path}"'
            script_activate = 'tell application "Finder" to activate'

            try:
                run_subprocess(["osascript", "-e", script_reveal], check=False)
                run_subprocess(["osascript", "-e", script_activate], check=False)
            except subprocess.CalledProcessError:
                # Handle potential errors and provide feedback
                print(f"Failed to reveal the file: {file_path}")

        else:  # Linux and other Unix-like
            file_managers = [
                ["xdg-open", str(file_path.parent)],  # Generic fallback
                ["nautilus", "--select", str(file_path)],  # GNOME
                ["dolphin", "--select", str(file_path)],  # KDE
                ["nemo", "--no-desktop", str(file_path)],  # Cinnamon
                ["pcmanfm", str(file_path)],  # LXDE/LXQt
                ["thunar", str(file_path)],  # XFCE
                ["caja", str(file_path)],  # MATE
                ["krusader", str(file_path)],  # KDE twin-panel
                ["rox", str(file_path)],  # ROX desktop
                ["doublecmd", str(file_path)],  # Dual-panel
                ["spacefm", str(file_path)],  # Multi-panel
                ["qtfm", str(file_path)],  # Qt-based
                ["lffm", str(file_path)],  # Simple & fast
                ["xplore", str(file_path)],  # Tree view
                ["lf", str(file_path)],  # Terminal-based
                ["nnn", str(file_path)],  # Minimalist
                ["vifm", str(file_path)],  # Vi-like
                ["ranger", str(file_path)],  # Vi-like
                ["mc", str(file_path)],  # Text-mode
            ]

            for command in file_managers:
                try:
                    run_subprocess(command)
                except subprocess.CalledProcessError:  # noqa: S112, PERF203
                    RobustRootLogger.debug(f"command '{command}' not found on your operating system")
                    continue
                else:
                    return

            RobustRootLogger.warning("all specific file manager attempts fail, fall back to opening the parent directory")
            run_subprocess(["xdg-open", str(file_path.parent)], check=True)

    def _save_files(
        self,
        file_path: Path,
        tableItem: FileTableWidgetItem,
    ):
        selected = self.selectedItems()
        if len(selected) == 1:
            # Extract the original filename from the selected item or file path
            original_filename = file_path.name
            # Pass the original filename as the initial selected filter
            savepath_str, _ = QFileDialog.getSaveFileName(None, "Save As", original_filename)
            if not savepath_str or not savepath_str.strip():
                return
            savepath = Path(savepath_str)
        else:
            # Multiple files, save to folder
            if self.temp_path is None:
                savepath_str = QFileDialog.getExistingDirectory(None, f"Save {len(selected)} files to...")
                if not savepath_str or not savepath_str.strip():
                    self.temp_path = ""  # Don't ask again for this sesh
                    return
                self.temp_path = Path(savepath_str)
            if not self.temp_path:
                return
            savepath = self.temp_path / file_path.name
        with file_path.open("rb") as reader, savepath.open("wb") as writer:
            writer.write(reader.read())

    def _open_windows_explorer_context_menu(
        self,
        file_path: Path,
        tableItem: FileTableWidgetItem,
    ):
        from utility.system.windows_context_menu import windows_context_menu_file
        return windows_context_menu_file(file_path)

    def _open_file(
        self,
        file_path: Path,
        tableItem: FileTableWidgetItem,
    ):
        if platform.system() in ["Windows", "Darwin"]:  # Windows and macOS
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(file_path)))
        else:  # Linux and other Unix-like
            subprocess.call(["xdg-open", str(file_path)])


    def _show_properties(
        self,
        file_path: Path,
        tableItem: FileTableWidgetItem,
    ):
        if platform.system() != "Windows":
            return
        import ctypes.wintypes

        SEE_MASK_NOCLOSEPROCESS = 0x00000040
        SEE_MASK_INVOKEIDLIST = 0x0000000C

        class SHELLEXECUTEINFO(ctypes.Structure):
            _fields_ = (
                ("cbSize",ctypes.wintypes.DWORD),
                ("fMask",ctypes.c_ulong),
                ("hwnd",ctypes.wintypes.HANDLE),
                ("lpVerb",ctypes.c_char_p),
                ("lpFile",ctypes.c_char_p),
                ("lpParameters",ctypes.c_char_p),
                ("lpDirectory",ctypes.c_char_p),
                ("nShow",ctypes.c_int),
                ("hInstApp",ctypes.wintypes.HINSTANCE),
                ("lpIDList",ctypes.c_void_p),
                ("lpClass",ctypes.c_char_p),
                ("hKeyClass",ctypes.wintypes.HKEY),
                ("dwHotKey",ctypes.wintypes.DWORD),
                ("hIconOrMonitor",ctypes.wintypes.HANDLE),
                ("hProcess",ctypes.wintypes.HANDLE),
            )

        ShellExecuteEx = ctypes.windll.shell32.ShellExecuteEx
        ShellExecuteEx.restype = ctypes.wintypes.BOOL

        sei = SHELLEXECUTEINFO()
        sei.cbSize = ctypes.sizeof(sei)
        sei.fMask = SEE_MASK_NOCLOSEPROCESS | SEE_MASK_INVOKEIDLIST
        sei.lpVerb = b"properties"
        sei.lpFile = str(file_path).encode("utf-8")
        sei.nShow = 1
        ShellExecuteEx(ctypes.byref(sei))
        time.sleep(1)

    def _sendToRecycleBin(
        self,
        file_path: Path,
        tableItem: FileTableWidgetItem,
    ):
        RobustRootLogger().info(f"Moving '{file_path}' to Recycle Bin")
        send2trash.send2trash(file_path)
        if hasattr(self, "removeRow"):
            self.removeRow(tableItem.row())

    def _delete_files_permanently(
        self,
        file_path: Path,
        tableItem: FileTableWidgetItem,
    ):
        file_path.unlink(missing_ok=True)
        if hasattr(self, "removeRow"):
            self.removeRow(tableItem.row())

    def _prepare_func(
        self,
        path: Path,
        tableItem: FileTableWidgetItem,
        func: Callable[[Path, FileTableWidgetItem], Any],
        missing_files: list[Path],
    ):
        if not path.is_file():
            missing_files.append(path)
        else:
            func(path, tableItem)

    def do_file_action(
        self,
        func: Callable[[Path, FileTableWidgetItem], Any],
        action_name: str,
        *,
        confirmation: bool = False,
    ):
        selected = self.selectedItems()
        if not selected:
            return
        if (
            confirmation
            and self.show_confirmation_dialog(
                QMessageBox.Question,
                "Action requires confirmation",
                f"Really perform action '{action_name}'?",
            )
            != QMessageBox.Yes
        ):
            return

        missing_files: list[Path] = []
        error_files: dict[Path, Exception] = {}
        for tableItem in selected:
            file_path = Path(tableItem.data(Qt.ItemDataRole.UserRole))
            try:
                assert isinstance(tableItem, FileTableWidgetItem)
                self._prepare_func(file_path, tableItem, func, missing_files)
            except AssertionError:
                raise
            except Exception as e:  # noqa: BLE001
                RobustRootLogger().exception("Failed to perform action '%s' filepath: '%s'", action_name, file_path)
                error_files[file_path] = e
        if missing_files:
            self._show_missing_results(missing_files)
        if error_files:
            self._show_errored_results(error_files)
        self.temp_path = None

    def _show_missing_results(
        self,
        missing_files: list[Path],
    ):
        missingMsgBox = QMessageBox(
            QMessageBox.Icon.Warning,
            "Nonexistent files found." + (" "*1000),
            f"The following {len(missing_files)} files no longer exist:" + (" "*1000) + ("<br>"*4),
            flags=Qt.WindowType.Dialog | Qt.WindowType.WindowDoesNotAcceptFocus | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowSystemMenuHint,
        )
        separator="-"*80
        missingMsgBox.setDetailedText(f"\n{separator}\n".join(str(path) for path in missing_files))
        missingMsgBox.exec_()

    def _show_errored_results(
        self,
        error_files: dict[Path, Exception],
    ):
        errMsgBox = QMessageBox(
            QMessageBox.Icon.Critical,
            "Errors occurred." + (" "*1000),
            f"The following {len(error_files)} files threw errors:" + (" "*1000) + ("<br>"*4),
            flags=Qt.WindowType.Dialog
            | Qt.WindowType.WindowDoesNotAcceptFocus
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowSystemMenuHint,
        )
        separator = "-"*80
        detailed_text = f"\n{separator}\n".join(f"{path}: {e}" for path, e in error_files.items())
        errMsgBox.setDetailedText(detailed_text)
        errMsgBox.exec_()


class ResourceItems(FileItems):
    def __init__(
        self,
        *args,
        resources: Sequence[FileResource | ResourceResult | LocationResult] | None = None,
        **kwargs,
    ):
        self.viewport: Callable
        self.resources: list[FileResource] = []
        if resources is not None:
            self._unify_resources(resources)
        filepaths = [res.filepath() for res in self.resources]
        super().__init__(*args, filepaths=filepaths, **kwargs)

    def _unify_resources(
        self,
        resources: Sequence[FileResource | ResourceResult | LocationResult],
    ) -> list[FileResource]:
        for resource in resources:
            if resource in self.resources:
                continue
            if isinstance(resource, FileResource):
                self.resources.append(resource)
            else:
                self.resources.append(resource.as_file_resource())

    @staticmethod
    def get_identifier(
        resource: FileResource,
    ) -> ResourceIdentifier:
        return resource.identifier()

    def selectedItems(self) -> list[ResourceTableWidgetItem]:
        return [ResourceTableWidgetItem(value=res.identifier(), resource=res) for res in self.resources]

    def selected_files_exist(
        self,
        selected: list[ResourceTableWidgetItem],
    ) -> bool:
        return all(resourceTableItem.resource.exists() for resourceTableItem in {*selected})

    def _prepare_func(
        self,
        path: Path,
        tableItem: ResourceTableWidgetItem,
        func: Callable[[Path, ResourceTableWidgetItem], Any],
        missing_files: list[Path],
    ):
        assert isinstance(tableItem, ResourceTableWidgetItem)
        if not path.is_file():
            missing_files.append(path)
            return
        resource: FileResource = tableItem.resource
        if resource.inside_bif or resource.inside_capsule:
            if not resource.exists():
                missing_files.append(resource._path_ident_obj)  # noqa: SLF001
                return

            # Create a temporary directory that persists until application shutdown
            tempdir = tempfile.mkdtemp(prefix="toolset_", suffix="_tmpext2")

            # Register a cleanup function to delete the temporary directory at exit
            def cleanup_tempdir():
                shutil.rmtree(tempdir, ignore_errors=True)

            atexit.register(cleanup_tempdir)
            tempdir_path = Path(tempdir)
            assert tempdir_path.safe_isdir()
            temp_file = tempdir_path / resource.filename()
            with BinaryWriterFile.to_file(temp_file) as writer:
                writer.write_bytes(resource.data())
            func(temp_file, tableItem)
        else:
            func(path, tableItem)

    def do_file_action(
        self,
        func: Callable[[Path, ResourceTableWidgetItem], Any],
        action_name: str,
        *,
        confirmation: bool = False,
    ):
        selected = self.selectedItems()
        if not selected:
            return
        if (
            confirmation
            and self.show_confirmation_dialog(
                QMessageBox.Question,
                "Action requires confirmation",
                f"Really perform action '{action_name}'?"
            ) != QMessageBox.Yes
        ):
            return

        missing_files: list[Path] = []
        error_files: dict[Path, Exception] = {}
        for tableItem in selected:
            resource: FileResource = tableItem.resource
            filepath = resource.filepath()
            try:
                self._prepare_func(filepath, tableItem, func, missing_files)
            except AssertionError:
                raise
            except Exception as e:  # noqa: BLE001
                RobustRootLogger().exception("Failed to perform action '%s' filepath: '%s'", action_name, filepath)
                error_files[filepath] = e
        if missing_files:
            self._show_missing_results(missing_files)
        if error_files:
            self._show_errored_results(error_files)

    def build_menu(
        self,
        menu: QMenu | None = None,
        installation: HTInstallation | None = None,
        resources: set[FileResource] | None = None,
    ) -> QMenu:
        menu = QMenu() if menu is None else menu
        super().build_menu(menu)
        if hasattr(self, "selectedItems") and resources is None:
            resources = {tableItem.resource for tableItem in self.selectedItems()}
        if resources is not None:
            if all(resource.restype().target_type().contents == "gff" for resource in resources):
                open_with_menu = menu.addMenu("Open With")  # This is the submenu

                # Add actions to the submenu
                open_with_menu.addAction("Open with GFF Editor").triggered.connect(
                    lambda: self.open_selected_resource(resources, installation, gff_specialized=False))
                if installation is not None:
                    open_with_menu.addAction("Open with Specialized Editor").triggered.connect(
                        lambda: self.open_selected_resource(resources, installation, gff_specialized=True))
                    open_with_menu.addAction("Open with Default Editor").triggered.connect(
                        lambda: self.open_selected_resource(resources, installation, gff_specialized=None))
            elif installation is not None:
                menu.addAction("Open with Editor").triggered.connect(lambda: self.open_selected_resource(resources, installation))  # TODO(th3w1zard1): disable when file doesn't exist.
        return menu

    def runContextMenu(
        self,
        position: QPoint,
        installation: HTInstallation | None = None,
        *,
        menu: QMenu | None = None,
    ) -> QAction:
        resources: set[FileResource] = {tableItem.resource for tableItem in self.selectedItems()}
        menu: QMenu = self.build_menu(menu)
        executed_action = menu.exec_(self.viewport().mapToGlobal(position))
        if executed_action is None:
            return executed_action
        self.handle_post_run_actions(executed_action, resources)
        executed_action_text = executed_action.text()
        if executed_action_text in ("Delete PERMANENTLY", "Send to Recycle Bin"):
            RobustRootLogger().debug("Action '%s' called, calling resourcetablewidget's post processing handlers...", executed_action_text)
            total_inside_capsules = {resource for resource in resources if resource.inside_capsule}
            if total_inside_capsules:
                separator="-"*80
                self.show_confirmation_dialog(
                    QMessageBox.Warning,
                    "File(s) are in a capsule",
                    f"Really delete {len(total_inside_capsules)} inside of ERF/RIMs and {len(resources)-len(total_inside_capsules)} other physical files?",
                    detailedMsg=f"\n{separator}\n".join(str(resource.filepath()) for resource in resources)
                )
            for resource in resources:
                if resource.inside_capsule and not resource.inside_bif:
                    filepath = resource.filepath()
                    RobustRootLogger().info(f"Perform post action '{executed_action_text}' on '{resource.identifier()}' in capsule at '{filepath}'")
                    if is_any_erf_type_file(filepath):
                        erf = read_erf(filepath)
                        erf.remove(resource.resname(), resource.restype())
                        write_erf(erf, filepath)
                    elif is_rim_file(filepath):
                        if GlobalSettings().disableRIMSaving:
                            RobustRootLogger().warning(f"Ignoring deletion of '{resource.filename()}' in RIM at path '{filepath}'. Saving into RIMs is disabled in Settings.")
                        else:
                            rim = read_rim(filepath)
                            rim.remove(resource.resname(), resource.restype())
                            write_rim(rim, filepath)
        return executed_action  # noqa: RET504

    def handle_post_run_actions(
        self,
        executed_action: QAction,
        resources: set[FileResource],
    ):
        action_text = executed_action.text()
        if action_text in {"Delete PERMANENTLY", "Send to Recycle Bin"}:
            RobustRootLogger().debug("Action '%s' called, calling resourcetablewidget's post processing handlers...", action_text)
            self.handle_delete_action(resources, executed_action)

    def handle_delete_action(
        self,
        resources: set[FileResource],
        executed_action: QAction,
    ):
        total_inside_capsules = {resource for resource in resources if resource.inside_capsule}
        if total_inside_capsules:
            separator = "-" * 80
            self.show_confirmation_dialog(
                QMessageBox.Warning,
                "File(s) are in a capsule",
                f"Really delete {len(total_inside_capsules)} inside of ERF/RIMs and {len(resources) - len(total_inside_capsules)} other physical files?",
                detailedMsg=f"\n{separator}\n".join(str(resource.filepath()) for resource in resources)
            )
        action_text = executed_action.text()
        for resource in resources:
            if resource.inside_capsule and not resource.inside_bif:
                filepath = resource.filepath()
                RobustRootLogger().info(f"Perform post action '{action_text}' on '{resource.identifier()}' in capsule at '{filepath}'")
                if is_any_erf_type_file(filepath):
                    erf = read_erf(filepath)
                    erf.remove(resource.resname(), resource.restype())
                    write_erf(erf, filepath)
                elif is_rim_file(filepath):
                    if GlobalSettings().disableRIMSaving:
                        RobustRootLogger().warning(f"Ignoring deletion of '{resource.filename()}' in RIM at path '{filepath}'. Reason: saving into RIMs is disabled.")
                    else:
                        rim = read_rim(filepath)
                        rim.remove(resource.resname(), resource.restype())
                        write_rim(rim, filepath)

    def on_double_click(self, *args, installation: HTInstallation):
        RobustRootLogger().debug(f"doubleclick args: {args} installation: {installation}")
        #first_item = next(iter(self.selectedItems()))
        selected = {res.resource for res in self.selectedItems()}
        self.open_selected_resource(
            selected,
            installation,
        )

    def open_selected_resource(
        self,
        resources: set[FileResource],
        installation: HTInstallation | None = None,
        *,
        gff_specialized: bool | None = None,
    ):
        RobustRootLogger().debug(f"open_selected_resource resources: {resources!r} installation: {installation!r} gff_specialized: {gff_specialized}")
        for resource in resources:
            try:
                data: bytes = resource.data()
            except Exception:  # noqa: BLE001
                RobustRootLogger().error("Exception occurred in open_selected_resource", exc_info=True)
                QMessageBox(QMessageBox.Icon.Critical, "Failed to get the file data.", "File no longer exists, might have been deleted.").exec_()
                return
            openResourceEditor(resource.filepath(), resource.resname(), resource.restype(), data, installation, gff_specialized=gff_specialized)


class CustomTableWidget(CustomItem, QTableWidget):
    def copy_selection_to_clipboard(self):
        selection = self.selectedIndexes()
        if not selection:
            return
        rows = sorted(index.row() for index in selection)
        columns = sorted(index.column() for index in selection)
        row_count = rows[-1] - rows[0] + 1
        column_count = columns[-1] - columns[0] + 1
        table_text = [[""] * column_count for _ in range(row_count)]
        for index in selection:
            row = index.row() - rows[0]
            column = index.column() - columns[0]
            table_text[row][column] = index.data()

        # Format table text as a tab-delimited string
        clipboard_text = "\n".join("\t".join(row) for row in table_text)
        QApplication.clipboard().setText(clipboard_text)

    def remove_selected_result(self):
        selected = self.selectedRanges()
        if not selected:
            return
        for selection in selected:
            for row in range(selection.bottomRow(), selection.topRow()-1, -1):
                self.removeRow(row)

    def set_all_items_editability(
        self,
        *,
        editable: bool,
    ):
        """Set all items in the table to be either editable or read-only based on the `editable` argument.

        Args:
        ----
            editable (bool): If True, all items will be set to editable. If False, items will be read-only.
        """
        for row in range(self.rowCount()):
            for column in range(self.columnCount()):
                item = self.item(row, column)
                if not item:  # Check if the item exists
                    continue
                if editable:
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
    def get_column_index(self, column_name: str) -> int:
        # This method needs to be context-aware for the type of view
        if isinstance(self, QTableWidget):
            for i in range(self.columnCount()):
                headerItem = self.horizontalHeaderItem(i)
                if headerItem is None:
                    continue
                if headerItem.text() == column_name:
                    return i
        elif isinstance(self, (QTreeView, QTableView)):
            model = self.model()
            for i in range(model.columnCount()):
                if model.headerData(i, Qt.Horizontal) == column_name:
                    return i
        raise ValueError(f"Column name '{column_name}' does not exist in this view.")

class FileTableWidget(FileItems, CustomTableWidget):
    def selectedItems(self) -> list[FileTableWidgetItem]:
        return QTableWidget.selectedItems(self)

class ResourceTableWidget(FileTableWidget, ResourceItems):
    def selectedItems(self) -> list[ResourceTableWidgetItem]:
        return QTableWidget.selectedItems(self)


class FileSelectionWindow(QMainWindow):
    def __init__(
        self,
        search_results: Sequence[FileResource | ResourceResult | LocationResult],
        installation: HTInstallation | None = None,
        *,
        editor: Editor | None = None,
    ):
        super().__init__(editor)

        self.resource_table = ResourceTableWidget(0, 3, resources=search_results)  # Start with zero rows and adjust based on checkbox
        self._installation: HTInstallation = installation
        self.editor: Editor | None = editor
        self.detailed_stat_attributes: list[str] = []
        self.init_ui()

    @property
    def installation(self) -> HTInstallation:
        return self._installation

    def init_ui(self):
        self.setWindowTitle("File Selection")  # Set a window title
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        self.detailed_checkbox = QCheckBox("Show detailed")
        self.detailed_checkbox.stateChanged.connect(self.toggle_detailed_info)
        layout.addWidget(self.detailed_checkbox)

        open_button = QPushButton("Open")
        open_button.clicked.connect(lambda: self.resource_table.on_double_click(installation=self.installation))
        self.resource_table.doubleClicked.connect(lambda: self.resource_table.on_double_click(installation=self.installation))

        layout.addWidget(self.resource_table)
        layout.addWidget(open_button)

        self.resource_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.resource_table.setWordWrap(True)
        self.setMinimumSize(600, 400)  # Width, Height in pixels

        # Automatically resize columns to fit their content, but also allow user adjustments
        for i in range(self.resource_table.columnCount()):
            self.resource_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
            self.resource_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        self._init_table()
        # Resize the main window to fit the contents up to a reasonable maximum
        self.resize(self.resource_table.sizeHint().width(), self.resource_table.sizeHint().height())
        self.resource_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.resource_table.customContextMenuRequested.connect(lambda x: self.resource_table.runContextMenu(x, self.installation))

    def centerAndAdjustWindow(self):
        # Get the screen geometry
        screen = QApplication.primaryScreen().geometry()

        # Calculate the new position to center the window
        new_x = (screen.width() - self.width()) // 2
        new_y = (screen.height() - self.height()) // 2

        # Adjust the position to ensure the window is fully visible
        new_x = max(0, min(new_x, screen.width() - self.width()))
        new_y = max(0, min(new_y, screen.height() - self.height()))

        # Set the new position
        self.move(new_x, new_y)

    def update_table_headers(self):
        headers = ["File Name", "File Path", "Offset", "Size"]
        if self.detailed_stat_attributes:
            for header in self.detailed_stat_attributes:
                if header in headers:
                    continue
                headers.append(header)
        self.resource_table.setColumnCount(len(headers))
        self.resource_table.setHorizontalHeaderLabels(list(headers))

    def format_time(self, timestamp: float) -> str:
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")  # noqa: DTZ006

    def resize_to_content(self):
        self.resource_table.resizeColumnsToContents()
        width = self.resource_table.verticalHeader().width() + 4  # 4 for the frame
        for i in range(self.resource_table.columnCount()):
            width += self.resource_table.columnWidth(i)
        width = min(width, QDesktopWidget().availableGeometry().width())
        height = self.height()  # keep the current height
        self.resize(width, height)
        self.centerAndAdjustWindow()

    def create_table_item(
        self,
        value: Any,
        resource: FileResource,
        sort_key: Any | None = None,
    ) -> ResourceTableWidgetItem:
        item = ResourceTableWidgetItem(value, sort_key, resource=resource)
        return item

    def populate_table(self):
        self.resource_table.setRowCount(len(self.resource_table.resources))  # Ensure the row count is correctly set
        for i, resource in enumerate(self.resource_table.resources):
            print(f"Adding item: {resource.identifier()} ({resource.filepath()}) at index {i}")
            self.resource_table.setItem(i, self.resource_table.get_column_index("File Name"), self.create_table_item(str(resource.identifier()), resource))
            self.resource_table.setItem(i, self.resource_table.get_column_index("Offset"), self.create_table_item(f"0x{hex(resource.offset())[2:].upper()}", resource))
            size_cell = self.create_table_item(self.human_readable_size(resource.size()), resource, sort_key=resource.size())
            self.resource_table.setItem(i, self.resource_table.get_column_index("Size"), size_cell)

            if self.detailed_stat_attributes:
                print(f"Detailed info for row {i}")
                self.resource_table.setItem(i, self.resource_table.get_column_index("File Path"), self.create_table_item(str(resource.filepath()), resource))
                try:
                    res_stat_result = resource.filepath().stat()
                    self.add_file_item(i, resource.filepath(), res_stat_result, resource)
                    if resource.offset():
                        # Replace some of the above stat results with ones specific for this resource.
                        data = resource.data() if resource.filepath().safe_isfile() else None
                        if data is None:
                            continue
                        with TemporaryDirectory("_tmpext", "toolset_") as tempdir:
                            temp_file = Path(tempdir, resource.filename())
                            with BinaryWriterFile.to_file(temp_file) as writer:
                                writer.write_bytes(data)
                            self.add_extra_file_details(i, temp_file, temp_file.stat(), resource)
                    else:
                        self.add_extra_file_details(i, resource.filepath(), res_stat_result, resource)
                except Exception:  # noqa: BLE001
                    RobustRootLogger().exception("Error populating detailed info for '%s'", resource.filepath())
            else:
                filepath_cell = self.create_table_item(str(resource.filepath().relative_to(self.installation.path().parent)), resource)
                self.resource_table.setItem(i, self.resource_table.get_column_index("File Path"), filepath_cell)

        self.resource_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.resource_table.horizontalHeader().setStretchLastSection(True)
        self.resource_table.set_all_items_editability(editable=False)
        self.resize_to_content()  # Adjust the window size after populating

    def human_readable_size(
        self,
        size: float,
        decimal_places: int = 2,
    ) -> str:
        for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
            if size < 1024.0 or unit == "PB":
                break
            size /= 1024.0
        return f"{size:.{decimal_places}f} {unit}"

    def add_extra_file_details(
        self,
        rowIndex: int,
        path: Path,
        stat_result: os.stat_result,
        resource: FileResource,
    ):
        size_on_disk = get_size_on_disk(path, stat_result)
        ratio = (size_on_disk / stat_result.st_size) * 100 if stat_result.st_size else 0  # Avoid division by zero
        display_size_on_disk = self.human_readable_size(size_on_disk)
        display_ratio = f"{ratio:.2f}%"
        self.resource_table.setItem(rowIndex, self.resource_table.get_column_index("Size on Disk"), self.create_table_item(display_size_on_disk, resource, sort_key=size_on_disk))
        self.resource_table.setItem(rowIndex, self.resource_table.get_column_index("Size Ratio"), self.create_table_item(display_ratio, resource, sort_key=ratio))

    def add_file_item(
        self,
        rowIndex: int,
        path: Path,
        stat_result: os.stat_result,
        resource: FileResource,
    ):
        self.resource_table.setItem(rowIndex, self.resource_table.get_column_index("File Path"), self.create_table_item(str(path), resource))

        for stat_attr, column_name in STAT_TO_COLUMN_MAP.items():
            if column_name == "Size":
                continue
            value = getattr(stat_result, stat_attr, None)
            if value is None:
                continue

            try:
                column_index = self.resource_table.get_column_index(column_name)
                if "size" in stat_attr:
                    size_cell = self.create_table_item(self.human_readable_size(value), resource, sort_key=value)
                    self.resource_table.setItem(rowIndex, column_index, size_cell)
                    continue
                if "time" in stat_attr:
                    if stat_attr.endswith("time_ns"):
                        value = value / 1e9
                    time_cell = self.create_table_item(self.format_time(value), resource, sort_key=value)
                    self.resource_table.setItem(rowIndex, column_index, time_cell)
                    continue
                if stat_attr == "st_mode":
                    value = oct(value)[-3:]  # Convert to file mode in octal format

                self.resource_table.setItem(rowIndex, column_index, self.create_table_item(value, resource))
            except Exception as e:  # noqa: BLE001
                RobustRootLogger().exception("Failed to parse stat_result attribute %s (%s): %s", column_name, stat_attr, value)
                QMessageBox.critical(self, "Stat attribute not expected format", f"Failed to parse {column_name} ({stat_attr}): {value}<br><br>{e}")


    def toggle_detailed_info(self):
        try:
            show_detailed = self.detailed_checkbox.isChecked()
            if show_detailed and self.resource_table.resources:
                result = self.resource_table.resources[0]
                filepath = result.filepath()
                self.detailed_stat_attributes = self.get_stat_attributes(filepath)
                self.detailed_stat_attributes.extend(("Size on Disk", "Size Ratio"))
            else:
                self.detailed_stat_attributes = []
            self._init_table()
        except Exception as e:
            # Handle the exception, e.g., show a message box with the error
            QMessageBox.critical(self, "Exception", f"An error occurred: {e}")
            self.detailed_checkbox.setChecked(False)  # Optionally, reset the checkbox to unchecked

    def _init_table(self):
        self.resource_table.setSortingEnabled(False)
        self.resource_table.clearContents()
        self.update_table_headers()
        self.populate_table()
        self.resource_table.setSortingEnabled(True)
        self.resource_table.horizontalHeader().setSectionsClickable(True)  # Make sure headers are clickable

    def get_stat_attributes(self, path: Path) -> list[str]:
        # Get stat result from a real file to dynamically determine the available attributes
        try:
            real_stat: os.stat_result = path.stat()
            return [
                STAT_TO_COLUMN_MAP.get(attr, attr)
                for attr in dir(real_stat)
                if attr.startswith("st_")
            ]
        except FileNotFoundError:
            return []  # Return an empty list if the path is invalid or not found

if __name__ == "__main__":
    from toolset.__main__ import onAppCrash
    faulthandler.enable(file=sys.stderr, all_threads=True)
    sys.excepthook = onAppCrash
    app = QApplication([])
    resname, restype = ResourceIdentifier.from_path("dan14_juhani.utc").unpack()
    found_kotors: dict[Game, list[CaseAwarePath]] = find_kotor_paths_from_default()
    installation = Installation(found_kotors[Game.K1][0])
    search: Sequence[FileResource | ResourceResult | LocationResult] = installation.location(resname, restype)
    if not search:
        raise ValueError("No files found")
    res_result = installation.resource("m02ab", ResourceType.GIT)
    if not res_result:
        raise ValueError("No ResourceResult found.")
    search.append(res_result)
    search.append(installation._modules["danm13.mod"][3])

    window = FileSelectionWindow(search, installation)
    HTInstallation.from_base_instance(installation)
    window.show()
    window.activateWindow()
    app.exec_()
