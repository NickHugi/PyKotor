from __future__ import annotations
import os
import sys
from pathlib import Path
from PyQt5.QtWidgets import (QMainWindow, QFileSystemModel, QTreeView, QListView, QSplitter, QLineEdit,
                             QToolButton, QMenu, QAction, QMessageBox, QInputDialog, QFileDialog,
                             QAbstractItemView, QApplication, QWidget, QHBoxLayout, QPushButton, QLabel)
from PyQt5.QtCore import Qt, QDir, QModelIndex, QItemSelectionModel, QSize, QUrl, QMimeData, pyqtSignal
from PyQt5.QtGui import QIcon, QKeySequence, QDesktopServices, QDrag, QCursor
from PyQt5 import uic
import shutil
import subprocess

class FileSystemExplorerWidget(QMainWindow):
    file_selected = pyqtSignal(str)
    directory_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = uic.loadUi("file_system_explorer_widget.ui", self)
        self.setup_model()
        self.setup_connections()
        self.setup_shortcuts()
        self.current_path = QDir.homePath()
        self.navigation_history = []
        self.navigation_index = -1
        self.setup_icons()
        self.update_ui()
        self.clipboard = QApplication.clipboard()

    def setup_icons(self):
        self.ui.back_button.setIcon(QIcon.fromTheme("go-previous"))
        self.ui.forward_button.setIcon(QIcon.fromTheme("go-next"))
        self.ui.up_button.setIcon(QIcon.fromTheme("go-up"))
        self.ui.go_button.setIcon(QIcon.fromTheme("go-jump"))

    def setup_model(self):
        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.rootPath())
        self.ui.navigation_pane.setModel(self.model)
        self.ui.file_list_view.setModel(self.model)

        # Hide all columns in navigation pane except the first one
        for i in range(1, self.model.columnCount()):
            self.ui.navigation_pane.hideColumn(i)

    def setup_connections(self):
        self.ui.navigation_pane.clicked.connect(self.on_navigation_pane_clicked)
        self.ui.file_list_view.clicked.connect(self.on_file_list_view_clicked)
        self.ui.file_list_view.doubleClicked.connect(self.on_file_list_view_double_clicked)
        self.ui.address_bar.returnPressed.connect(self.on_address_bar_return)
        self.ui.go_button.clicked.connect(self.on_go_button_clicked)
        self.ui.file_list_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.file_list_view.customContextMenuRequested.connect(self.show_context_menu)
        self.ui.back_button.clicked.connect(self.go_back)
        self.ui.forward_button.clicked.connect(self.go_forward)
        self.ui.up_button.clicked.connect(self.go_up)
        self.ui.search_bar.textChanged.connect(self.on_search_text_changed)

        # Connect menu actions
        self.ui.action_new_window.triggered.connect(self.new_window)
        self.ui.action_open_windows_terminal.triggered.connect(self.open_windows_terminal)
        self.ui.action_close.triggered.connect(self.close)
        self.ui.action_properties.triggered.connect(self.show_properties)
        self.ui.action_exit.triggered.connect(self.close)

        self.ui.action_cut.triggered.connect(self.cut)
        self.ui.action_copy.triggered.connect(self.copy)
        self.ui.action_paste.triggered.connect(self.paste)
        self.ui.action_delete.triggered.connect(self.delete)
        self.ui.action_select_all.triggered.connect(self.select_all)
        self.ui.action_invert_selection.triggered.connect(self.invert_selection)
        self.ui.action_select_none.triggered.connect(self.select_none)

        self.ui.action_refresh.triggered.connect(self.refresh)
        self.ui.action_extra_large_icons.triggered.connect(lambda: self.change_view_mode("extra_large_icons"))
        self.ui.action_large_icons.triggered.connect(lambda: self.change_view_mode("large_icons"))
        self.ui.action_medium_icons.triggered.connect(lambda: self.change_view_mode("medium_icons"))
        self.ui.action_small_icons.triggered.connect(lambda: self.change_view_mode("small_icons"))
        self.ui.action_list.triggered.connect(lambda: self.change_view_mode("list"))
        self.ui.action_details.triggered.connect(lambda: self.change_view_mode("details"))
        self.ui.action_tiles.triggered.connect(lambda: self.change_view_mode("tiles"))
        self.ui.action_content.triggered.connect(lambda: self.change_view_mode("content"))
        self.ui.action_show_hidden_items.triggered.connect(self.toggle_hidden_items)

    def setup_shortcuts(self):
        QShortcut(QKeySequence.Back, self, self.go_back)
        QShortcut(QKeySequence.Forward, self, self.go_forward)
        QShortcut(QKeySequence.Up, self, self.go_up)
        QShortcut(QKeySequence.Refresh, self, self.refresh)
        QShortcut(QKeySequence.Cut, self, self.cut)
        QShortcut(QKeySequence.Copy, self, self.copy)
        QShortcut(QKeySequence.Paste, self, self.paste)
        QShortcut(QKeySequence.Delete, self, self.delete)
        QShortcut(QKeySequence("F2"), self, self.rename)
        QShortcut(QKeySequence.SelectAll, self, self.select_all)
        QShortcut(QKeySequence("Ctrl+L"), self, self.focus_address_bar)
        QShortcut(QKeySequence("Ctrl+E"), self, self.focus_search_bar)
        QShortcut(QKeySequence("Ctrl+Shift+N"), self, self.create_new_folder)
        QShortcut(QKeySequence("F4"), self, self.open_windows_terminal)

    def on_navigation_pane_clicked(self, index):
        path = self.model.filePath(index)
        self.set_current_path(path)

    def on_file_list_view_clicked(self, index):
        path = self.model.filePath(index)
        self.file_selected.emit(path)

    def on_file_list_view_double_clicked(self, index):
        path = self.model.filePath(index)
        if self.model.isDir(index):
            self.set_current_path(path)
        else:
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def on_address_bar_return(self):
        path = self.ui.address_bar.text()
        self.set_current_path(path)

    def on_go_button_clicked(self):
        self.on_address_bar_return()

    def set_current_path(self, path):
        if os.path.isdir(path):
            self.current_path = path
            self.ui.file_list_view.setRootIndex(self.model.index(path))
            self.ui.navigation_pane.setCurrentIndex(self.model.index(path))
            self.ui.address_bar.setText(path)
            self.directory_changed.emit(path)
            self.add_to_history(path)
            self.update_ui()
        else:
            # Handle invalid path
            self.ui.address_bar.setText(self.current_path)

    def add_to_history(self, path):
        if self.navigation_index < len(self.navigation_history) - 1:
            self.navigation_history = self.navigation_history[:self.navigation_index + 1]
        self.navigation_history.append(path)
        self.navigation_index = len(self.navigation_history) - 1

    def go_back(self):
        if self.navigation_index > 0:
            self.navigation_index -= 1
            self.set_current_path(self.navigation_history[self.navigation_index])

    def go_forward(self):
        if self.navigation_index < len(self.navigation_history) - 1:
            self.navigation_index += 1
            self.set_current_path(self.navigation_history[self.navigation_index])

    def go_up(self):
        parent_path = os.path.dirname(self.current_path)
        if parent_path != self.current_path:
            self.set_current_path(parent_path)

    def on_search_text_changed(self, text):
        if text:
            self.model.setNameFilters([f"*{text}*"])
            self.model.setNameFilterDisables(False)
        else:
            self.model.setNameFilters([])
            self.model.setNameFilterDisables(True)
        self.ui.file_list_view.setRootIndex(self.model.index(self.current_path))

    def focus_address_bar(self):
        self.ui.address_bar.setFocus()
        self.ui.address_bar.selectAll()

    def show_context_menu(self, position):
        index = self.ui.file_list_view.indexAt(position)
        if index.isValid():
            menu = QMenu(self)
            open_action = menu.addAction("Open")
            open_action.triggered.connect(lambda: self.on_file_list_view_double_clicked(index))
            menu.addSeparator()
            cut_action = menu.addAction("Cut")
            cut_action.triggered.connect(self.cut)
            copy_action = menu.addAction("Copy")
            copy_action.triggered.connect(self.copy)
            paste_action = menu.addAction("Paste")
            paste_action.triggered.connect(self.paste)
            delete_action = menu.addAction("Delete")
            delete_action.triggered.connect(self.delete)
            rename_action = menu.addAction("Rename")
            rename_action.triggered.connect(self.rename)
            menu.addSeparator()
            properties_action = menu.addAction("Properties")
            properties_action.triggered.connect(self.show_properties)
            menu.exec_(QCursor.pos())

    def update_ui(self):
        self.update_status_bar()
        self.ui.back_button.setEnabled(self.navigation_index > 0)
        self.ui.forward_button.setEnabled(self.navigation_index < len(self.navigation_history) - 1)
        self.ui.up_button.setEnabled(self.current_path != QDir.rootPath())

    def update_status_bar(self):
        selected_items = len(self.ui.file_list_view.selectedIndexes())
        total_items = self.ui.file_list_view.model().rowCount(self.ui.file_list_view.rootIndex())
        if selected_items > 0:
            status_text = f"{selected_items} item{'s' if selected_items > 1 else ''} selected"
        else:
            status_text = f"{total_items} item{'s' if total_items > 1 else ''}"
        self.ui.status_items.setText(status_text)
        
        total_size = sum(self.model.size(self.ui.file_list_view.model().index(i, 0, self.ui.file_list_view.rootIndex()))
                         for i in range(total_items))
        self.ui.status_size.setText(self.format_size(total_size))

    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    def new_window(self):
        new_window = FileSystemExplorerWidget()
        new_window.show()

    def open_windows_terminal(self):
        subprocess.Popen(f'start cmd /K "cd /d {self.current_path}"', shell=True)

    def show_properties(self):
        selected_indexes = self.ui.file_list_view.selectedIndexes()
        if selected_indexes:
            file_path = self.model.filePath(selected_indexes[0])
            file_info = self.model.fileInfo(selected_indexes[0])
            
            properties = f"Name: {file_info.fileName()}\n"
            properties += f"Type: {'Directory' if file_info.isDir() else 'File'}\n"
            properties += f"Size: {self.format_size(file_info.size())}\n"
            properties += f"Created: {file_info.birthTime().toString()}\n"
            properties += f"Modified: {file_info.lastModified().toString()}\n"
            properties += f"Accessed: {file_info.lastRead().toString()}\n"
            
            QMessageBox.information(self, "Properties", properties)

    def cut(self):
        self.copy(cut=True)

    def copy(self, cut=False):
        selected_indexes = self.ui.file_list_view.selectedIndexes()
        if selected_indexes:
            urls = [QUrl.fromLocalFile(self.model.filePath(index)) for index in selected_indexes]
            mime_data = QMimeData()
            mime_data.setUrls(urls)
            self.clipboard.setMimeData(mime_data)
            if cut:
                self.to_cut = urls
            else:
                self.to_cut = None

    def paste(self):
        mime_data = self.clipboard.mimeData()
        if mime_data.hasUrls():
            for url in mime_data.urls():
                source_path = url.toLocalFile()
                file_name = os.path.basename(source_path)
                destination_path = os.path.join(self.current_path, file_name)
                
                if hasattr(self, 'to_cut') and self.to_cut and url in self.to_cut:
                    shutil.move(source_path, destination_path)
                else:
                    if os.path.isdir(source_path):
                        shutil.copytree(source_path, destination_path)
                    else:
                        shutil.copy2(source_path, destination_path)
            
            self.refresh()
            if hasattr(self, 'to_cut'):
                self.to_cut = None

    def delete(self):
        selected_indexes = self.ui.file_list_view.selectedIndexes()
        if selected_indexes:
            reply = QMessageBox.question(self, 'Confirm Delete',
                                         f"Are you sure you want to delete {len(selected_indexes)} item(s)?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                for index in selected_indexes:
                    file_path = self.model.filePath(index)
                    if os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                    else:
                        os.remove(file_path)
                self.refresh()

    def rename(self):
        selected_indexes = self.ui.file_list_view.selectedIndexes()
        if len(selected_indexes) == 1:
            old_name = self.model.fileName(selected_indexes[0])
            new_name, ok = QInputDialog.getText(self, 'Rename', 'Enter new name:', text=old_name)
            if ok and new_name:
                old_path = self.model.filePath(selected_indexes[0])
                new_path = os.path.join(os.path.dirname(old_path), new_name)
                os.rename(old_path, new_path)
                self.refresh()

    def select_all(self):
        self.ui.file_list_view.selectAll()

    def invert_selection(self):
        selection_model = self.ui.file_list_view.selectionModel()
        for i in range(self.model.rowCount(self.ui.file_list_view.rootIndex())):
            index = self.model.index(i, 0, self.ui.file_list_view.rootIndex())
            selection_model.select(index, QItemSelectionModel.Toggle)

    def select_none(self):
        self.ui.file_list_view.clearSelection()

    def refresh(self):
        current_index = self.model.index(self.current_path)
        self.model.setRootPath(self.current_path)  # This refreshes the model
        self.ui.file_list_view.setRootIndex(current_index)
        self.update_ui()

    def change_view_mode(self, mode):
        if mode == "extra_large_icons":
            self.ui.file_list_view.setViewMode(QListView.IconMode)
            self.ui.file_list_view.setIconSize(QSize(96, 96))
            self.ui.file_list_view.setGridSize(QSize(120, 120))
        elif mode == "large_icons":
            self.ui.file_list_view.setViewMode(QListView.IconMode)
            self.ui.file_list_view.setIconSize(QSize(48, 48))
            self.ui.file_list_view.setGridSize(QSize(80, 80))
        elif mode == "medium_icons":
            self.ui.file_list_view.setViewMode(QListView.IconMode)
            self.ui.file_list_view.setIconSize(QSize(32, 32))
            self.ui.file_list_view.setGridSize(QSize(60, 60))
        elif mode == "small_icons":
            self.ui.file_list_view.setViewMode(QListView.IconMode)
            self.ui.file_list_view.setIconSize(QSize(16, 16))
            self.ui.file_list_view.setGridSize(QSize(40, 40))
        elif mode == "list":
            self.ui.file_list_view.setViewMode(QListView.ListMode)
            self.ui.file_list_view.setIconSize(QSize(16, 16))
            self.ui.file_list_view.setGridSize(QSize())
        elif mode == "details":
            # Switch to QTreeView for details view
            self.ui.file_list_view.setViewMode(QListView.ListMode)
            self.ui.file_list_view.setIconSize(QSize(16, 16))
            self.ui.file_list_view.setGridSize(QSize())
            # Show all columns
            for i in range(self.model.columnCount()):
                self.ui.file_list_view.setColumnHidden(i, False)
        elif mode == "tiles":
            self.ui.file_list_view.setViewMode(QListView.IconMode)
            self.ui.file_list_view.setIconSize(QSize(32, 32))
            self.ui.file_list_view.setGridSize(QSize(120, 80))
        elif mode == "content":
            # Similar to details view but with a preview pane
            self.change_view_mode("details")
            # Add a preview pane here if needed

    def toggle_hidden_items(self):
        filters = self.model.filter()
        if filters & QDir.Hidden:
            self.model.setFilter(filters & ~QDir.Hidden)
            self.ui.action_show_hidden_items.setText("Show Hidden Items")
        else:
            self.model.setFilter(filters | QDir.Hidden)
            self.ui.action_show_hidden_items.setText("Hide Hidden Items")
        self.refresh()

    def create_new_folder(self):
        folder_name, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:")
        if ok and folder_name:
            new_folder_path = os.path.join(self.current_path, folder_name)
            try:
                os.mkdir(new_folder_path)
                self.refresh()
            except OSError:
                QMessageBox.warning(self, "Error", "Failed to create new folder.")

    def focus_search_bar(self):
        self.ui.search_bar.setFocus()
        self.ui.search_bar.selectAll()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            source_path = url.toLocalFile()
            destination_path = os.path.join(self.current_path, os.path.basename(source_path))
            if os.path.isdir(source_path):
                shutil.copytree(source_path, destination_path)
            else:
                shutil.copy2(source_path, destination_path)
        self.refresh()

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget = FileSystemExplorerWidget()
    widget.show()
    sys.exit(app.exec_())