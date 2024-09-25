from __future__ import annotations

import multiprocessing
import os
import shutil
import tarfile
import zipfile

from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from qtpy.QtCore import QModelIndex, QObject, Signal  # pyright: ignore[reportPrivateImportUsage]

from utility.system.os_helper import get_size_on_disk

if TYPE_CHECKING:
    from qtpy.QtCore import QPoint
    from qtpy.QtGui import QCursor
    from qtpy.QtWidgets import (
        QAction,  # pyright: ignore[reportPrivateImportUsage]
        QMenu,
    )

    from utility.ui_libraries.qt.filesystem.explorer.explorer import PyFileExplorer




    def show_context_menu(self, pos: QPoint, index: QModelIndex):
        menu = QMenu()
        if index.isValid():
            self.create_item_menu(menu, index)
        else:
            self.create_background_menu(menu)
        menu.exec_(QCursor.pos())

    def create_item_menu(self, menu: QMenu, index: QModelIndex):
        actions = [
            ("Open", lambda: self.open_item.emit(index)),
            ("Cut", lambda: self.cut_items.emit([index])),
            ("Copy", lambda: self.copy_items.emit([index])),
            ("Paste", self.paste_items.emit),
            ("Delete", lambda: self.delete_items.emit([index])),
            ("Rename", lambda: self.rename_item.emit(index)),
            ("Properties", lambda: self.show_properties.emit(index)),
            ("Compress", lambda: self.compress_items.emit([index])),
        ]
        for name, func in actions:
            action: QAction = menu.addAction(name)
            action.triggered.connect(func)
        menu.addSeparator()

    def create_background_menu(self, menu: QMenu):
        actions = [
            ("New Folder", self.create_new_folder.emit),
            ("Paste", self.paste_items.emit),
            ("Refresh", self.refresh.emit),
            ("Sort By", self.create_sort_menu),
            ("View", self.create_view_menu),
        ]
        for name, func in actions:
            action = menu.addAction(name)
            action.triggered.connect(func)

    def create_sort_menu(self):
        sort_menu = QMenu("Sort By")
        sort_options = ("Name", "Size", "Type", "Date Modified")
        for option in sort_options:
            action = sort_menu.addAction(option)
            action.triggered.connect(lambda _, o=option: self.sort_by.emit(o))
        return sort_menu

    def create_view_menu(self):
        view_menu = QMenu("View")
        view_options = ("Icons", "List", "Details")
        for option in view_options:
            action = view_menu.addAction(option)
            action.triggered.connect(lambda _, o=option: self.change_view.emit(o))
        return view_menu


class FileActionDispatcher(QObject):
    """Offloads file operations to a ProcessPoolExecutor, and emits signals with the results.

    We don't use QThread or even the threading module because of the Global Interpreter Lock.
    """

    def __init__(self, parent: QObject | None = None):
        self._executor: ProcessPoolExecutor = ProcessPoolExecutor(max_workers=multiprocessing.cpu_count() or 1)
        self.qt_actions: FileActionsExecutor = FileActionsExecutor()
        super().__init__(parent)


class FileActionsExecutor:
    OpenItem: ClassVar[Signal] = Signal(QModelIndex)
    CutItems: ClassVar[Signal] = Signal(list)
    CopyItems: ClassVar[Signal] = Signal(list)
    PasteItems: ClassVar[Signal] = Signal()
    DeleteItems: ClassVar[Signal] = Signal(list)
    RenameItem: ClassVar[Signal] = Signal(QModelIndex)
    ShowProperties: ClassVar[Signal] = Signal(QModelIndex)
    CompressItems: ClassVar[Signal] = Signal(list, str)
    CreateNewFolder: ClassVar[Signal] = Signal()
    Refresh: ClassVar[Signal] = Signal()
    SortBy: ClassVar[Signal] = Signal(str)
    ChangeView: ClassVar[Signal] = Signal(str)

    @staticmethod
    def delete_items(paths: list[Path]):
        for path in paths:
            if not path.exists():
                continue
            if path.is_file():
                path.unlink(missing_ok=False)
                continue
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=False)

    @staticmethod
    def rename_item(old_path: Path, new_name: str):
        new_path = old_path.with_name(new_name)
        old_path.rename(new_path)

    @staticmethod
    def create_new_folder(parent_path: Path, name: str):
        new_folder = parent_path / name
        new_folder.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def get_properties(path: Path) -> dict[str, str]:
        info = path.stat()
        return {
            "Name": path.name,
            "Type": "Directory" if path.is_dir() else "File",
            "Size": FileActionsExecutor.format_size(info.st_size),
            "Size on disk": FileActionsExecutor.format_size(get_size_on_disk(path, info)),
            "Created": FileActionsExecutor.format_time(info.st_ctime),
            "Modified": FileActionsExecutor.format_time(info.st_mtime),
            "Accessed": FileActionsExecutor.format_time(info.st_atime),
        }

    @classmethod
    def compress_items(cls, paths: list[Path], archive_name: str):

        lower_archive_name = archive_name.lower()
        if lower_archive_name.endswith(".zip"):
            cls.extract_zip(paths, archive_name)
        elif lower_archive_name.endswith((".tar.gz", ".tgz")):
            cls.extract_tar_gz(paths, archive_name)
        elif lower_archive_name.endswith(".tar"):
            cls.extract_tar(paths, archive_name)
        else:
            raise ValueError("Unsupported archive format")

    @staticmethod
    def extract_zip(paths: list[Path], archive_name: str):
        with zipfile.ZipFile(archive_name, "w") as archive:
            for path in paths:
                if not path.exists():
                    continue
                if path.is_file():
                    archive.write(path, path.name)
                    continue
                if path.is_dir():
                    for root, _, files in os.walk(path):
                        for file in files:
                            file_path = Path(root) / file
                            archive.write(file_path, file_path.relative_to(path.parent))

    @staticmethod
    def extract_tar(paths: list[Path], archive_name: str):
        with tarfile.open(archive_name, "w:gz") as archive:
            for path in paths:
                if not path.exists():
                    continue
                archive.add(path, arcname=path.name)

    @staticmethod
    def format_size(size: float) -> str:
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:  # noqa: PLR2004
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    @staticmethod
    def format_time(timestamp: float) -> str:
        from datetime import datetime

        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")  # noqa: DTZ006


class FileExplorerContextMenu:
    def __init__(self, file_explorer: PyFileExplorer):
        self.signals = FileActionSignals()
        self.qt_actions: FileActionsExecutor = FileActionsExecutor(self.signals)
        self.py_actions: FileActionsExecutor = FileActionsExecutor()

    def show_context_menu(self, pos: QPoint, index: QModelIndex):
        self.qt_actions.show_context_menu(pos, index)
