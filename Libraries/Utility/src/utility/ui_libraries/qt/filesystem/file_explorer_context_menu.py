from __future__ import annotations

import os

from pathlib import Path
from typing import TYPE_CHECKING

from qtpy.QtCore import QUrl
from qtpy.QtGui import QCursor
from qtpy.QtWidgets import QApplication, QInputDialog, QMenu, QMessageBox

from utility.system.os_helper import get_size_on_disk
from utility.ui_libraries.qt.filesystem.undo_commands import CopyCommand, DeleteCommand, MoveCommand, RenameCommand

if TYPE_CHECKING:
    from qtpy.QtCore import QModelIndex, QPoint

    from utility.ui_libraries.qt.filesystem.simple_file_dialog_widget import FileSystemExplorerWidget


class FileExplorerContextMenu:
    def __init__(self, file_explorer: FileSystemExplorerWidget):
        self.file_explorer = file_explorer

    def show_context_menu(self, pos: QPoint, index: QModelIndex):
        menu = QMenu(self.file_explorer)

        if index.isValid():
            self.create_item_menu(menu, index)
        else:
            self.create_background_menu(menu)

        menu.exec_(QCursor.pos())

    def create_item_menu(self, menu: QMenu, index: QModelIndex):
        open_action = menu.addAction("Open")
        open_action.triggered.connect(lambda: self.open_item(index))

        menu.addSeparator()

        cut_action = menu.addAction("Cut")
        cut_action.triggered.connect(lambda: self.cut_items([index]))

        copy_action = menu.addAction("Copy")
        copy_action.triggered.connect(lambda: self.copy_items([index]))

        paste_action = menu.addAction("Paste")
        paste_action.triggered.connect(self.paste_items)
        paste_action.setEnabled(QApplication.clipboard().mimeData().hasUrls())

        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(lambda: self.delete_items([index]))

        rename_action = menu.addAction("Rename")
        rename_action.triggered.connect(lambda: self.rename_item(index))

        properties_action = menu.addAction("Properties")
        properties_action.triggered.connect(lambda: self.show_properties(index))

    def create_background_menu(self, menu: QMenu):
        new_folder_action = menu.addAction("New Folder")
        new_folder_action.triggered.connect(self.create_new_folder)

        paste_action = menu.addAction("Paste")
        paste_action.triggered.connect(self.paste_items)
        paste_action.setEnabled(QApplication.clipboard().mimeData().hasUrls())

    def open_item(self, index: QModelIndex):
        path = self.file_explorer.fs_model.filePath(index)
        #self.file_explorer.on_file_list_view_double_clicked(index)
        os.startfile(path, "open")

    def cut_items(self, indexes: list[QModelIndex]):
        self.copy_items(indexes, cut=True)

    def copy_items(self, indexes: list[QModelIndex], cut: bool = False):
        urls = [QUrl.fromLocalFile(self.file_explorer.fs_model.filePath(index)) for index in indexes]
        mime_data = QApplication.clipboard().mimeData()
        mime_data.setUrls(urls)
        mime_data.setText("\n".join(url.toLocalFile() for url in urls))
        if cut:
            mime_data.setData("application/x-cut-data", b"1")
        QApplication.clipboard().setMimeData(mime_data)

    def paste_items(self):
        mime_data = QApplication.clipboard().mimeData()
        if mime_data.hasUrls():
            is_cut = mime_data.hasFormat("application/x-cut-data")
            for url in mime_data.urls():
                source_path = Path(url.toLocalFile())
                dest_path = self.file_explorer.current_path / source_path.name
                if is_cut:
                    command = MoveCommand([source_path], dest_path)
                else:
                    command = CopyCommand([source_path], dest_path)
                self.file_explorer.undo_stack.push(command)
            self.file_explorer.refresh()
            if is_cut:
                QApplication.clipboard().clear()

    def delete_items(self, indexes: list[QModelIndex]):
        paths = [Path(self.file_explorer.fs_model.filePath(index)) for index in indexes]
        reply = QMessageBox.question(self.file_explorer, "Confirm Delete", f"Are you sure you want to delete {len(paths)} item(s)?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            command = DeleteCommand(paths)
            self.file_explorer.undo_stack.push(command)
            self.file_explorer.refresh()

    def rename_item(self, index: QModelIndex):
        old_path = Path(self.file_explorer.fs_model.filePath(index))
        new_name, ok = QInputDialog.getText(self.file_explorer, "Rename", "New name:", text=old_path.name)
        if ok and new_name:
            new_path = old_path.with_name(new_name)
            command = RenameCommand(old_path, new_path)
            self.file_explorer.undo_stack.push(command)
            self.file_explorer.refresh()

    def show_properties(self, index: QModelIndex):
        path = Path(self.file_explorer.fs_model.filePath(index))
        info = path.stat()

        properties = f"Name: {path.name}\n"
        properties += f"Type: {'Directory' if path.is_dir() else 'File'}\n"
        properties += f"Size: {self.format_size(info.st_size)}\n"
        properties += f"Size on disk: {self.format_size(get_size_on_disk(path, info))}\n"
        properties += f"Created: {self.format_time(info.st_ctime)}\n"
        properties += f"Modified: {self.format_time(info.st_mtime)}\n"
        properties += f"Accessed: {self.format_time(info.st_atime)}\n"

        QMessageBox.information(self.file_explorer, "Properties", properties)

    def create_new_folder(self):
        name, ok = QInputDialog.getText(self.file_explorer, "New Folder", "Folder name:")
        if ok and name:
            new_folder = self.file_explorer.current_path / name
            try:
                new_folder.mkdir(parents=True, exist_ok=True)
                self.file_explorer.refresh()
            except OSError:
                QMessageBox.warning(self.file_explorer, "Error", "Failed to create new folder.")

    def format_size(self, size: int) -> str:
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    def format_time(self, timestamp: float) -> str:
        from datetime import datetime

        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
