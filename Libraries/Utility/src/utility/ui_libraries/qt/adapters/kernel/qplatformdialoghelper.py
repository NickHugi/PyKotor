from __future__ import annotations

import mimetypes
import os

from abc import ABC, abstractmethod
from enum import Enum, auto

from qtpy.QtCore import QDir

from utility.ui_libraries.qt.adapters.filesystem.qfiledialog.qfiledialog import QFileDialog


class FileMode(Enum):
    AnyFile = auto()
    ExistingFile = auto()
    Directory = auto()
    ExistingFiles = auto()


class AcceptMode(Enum):
    AcceptOpen = auto()
    AcceptSave = auto()


class ViewMode(Enum):
    Detail = auto()
    List = auto()


class QFileDialogOptions:
    ViewMode = QFileDialog.ViewMode
    AcceptMode = QFileDialog.AcceptMode
    FileMode = QFileDialog.FileMode

    def __init__(self):
        self._mime_type_filters: list[str] = []

        self._name_filters: list[str] = []
        self._selected_name_filter: str = ""
        self._selected_mime_type_filter: str = ""
        self._file_mode: FileMode = FileMode.AnyFile
        self._accept_mode: AcceptMode = AcceptMode.AcceptOpen
        self._view_mode: ViewMode = ViewMode.Detail
        self._supported_schemes: list[str] = ["file"]
        self._default_suffix: str = ""
        self._filter: int = QDir.Filter(0)  # Placeholder for QDir.Filter

    def setMimeTypeFilters(self, filters: list[str]) -> None:
        self._mime_type_filters = filters

    def mimeTypeFilters(self) -> list[str]:
        return self._mime_type_filters

    def setNameFilters(self, filters: list[str]) -> None:
        self._name_filters = filters

    def nameFilters(self) -> list[str]:
        return self._name_filters

    def selectNameFilter(self, filter: str) -> None:  # noqa: A002
        if filter in self._name_filters:
            self._selected_name_filter = filter

    def selectedNameFilter(self) -> str:
        return self._selected_name_filter

    def selectMimeTypeFilter(self, filter: str) -> None:  # noqa: A002
        if filter in self._mime_type_filters:
            self._selected_mime_type_filter = filter

    def selectedMimeTypeFilter(self) -> str:
        return self._selected_mime_type_filter

    def setFileMode(self, mode: FileMode) -> None:
        self._file_mode = mode

    def fileMode(self) -> FileMode:
        return self._file_mode

    def setAcceptMode(self, mode: AcceptMode) -> None:
        self._accept_mode = mode

    def acceptMode(self) -> AcceptMode:
        return self._accept_mode

    def setViewMode(self, mode: ViewMode) -> None:
        self._view_mode = mode

    def viewMode(self) -> ViewMode:
        return self._view_mode

    def setSupportedSchemes(self, schemes: list[str]) -> None:
        self._supported_schemes = schemes

    def supportedSchemes(self) -> list[str]:
        return self._supported_schemes

    def setDefaultSuffix(self, suffix: str) -> None:
        self._default_suffix = suffix

    def defaultSuffix(self) -> str:
        return self._default_suffix

    def setFilter(self, filter: int) -> None:  # noqa: A002
        self._filter = filter

    def filter(self) -> int:
        return self._filter


class QFileDialogPlatformHelper(ABC):
    def __init__(self, options: QFileDialogOptions):
        self._options: QFileDialogOptions = options
        self._selected_files: list[str] = []
        self._current_directory: str = os.path.expanduser("~")  # noqa: PTH111

    @abstractmethod
    def show_dialog(self) -> bool:
        pass

    def selectFile(self, filename: str) -> None:
        if os.path.isabs(filename):  # noqa: PTH117
            self._selected_files = [filename]
        else:
            self._selected_files = [os.path.join(self._current_directory, filename)]  # noqa: PTH118

    def selectedFiles(self) -> list[str]:
        return self._selected_files

    def setDirectory(self, directory: str) -> None:
        if os.path.exists(directory) and os.path.isdir(directory):  # noqa: PTH112, PTH110
            self._current_directory = directory

    def directory(self) -> str:
        return self._current_directory

    def _filter_files(self, files: list[str]) -> list[str]:
        if not self._options.mimeTypeFilters() and not self._options.nameFilters():
            return files

        filtered_files: list[str] = []
        for file in files:
            mime_type, _ = mimetypes.guess_type(file)
            if mime_type and mime_type in self._options.mimeTypeFilters():
                filtered_files.append(file)
                continue

            for name_filter in self._options.nameFilters():
                if self._match_name_filter(file, name_filter):
                    filtered_files.append(file)
                    break

        return filtered_files

    @staticmethod
    def _match_name_filter(filename: str, name_filter: str) -> bool:
        import fnmatch

        patterns: list[str] = name_filter.split(";;")
        return any(fnmatch.fnmatch(filename, pattern.strip()) for pattern in patterns)


class MacFileDialogHelper(QFileDialogPlatformHelper):
    def show_dialog(self) -> bool:
        try:
            from AppKit import NSURL, NSModalResponseOK, NSOpenPanel, NSSavePanel
        except ImportError:
            print("AppKit is not available. Make sure you're running on macOS.")
            return False

        if self._options.acceptMode() == AcceptMode.AcceptOpen:
            panel = NSOpenPanel.openPanel()
            panel.setCanChooseFiles_(self._options.fileMode() != FileMode.Directory)
            panel.setCanChooseDirectories_(self._options.fileMode() in [FileMode.Directory, FileMode.ExistingFiles])
            panel.setAllowsMultipleSelection_(self._options.fileMode() == FileMode.ExistingFiles)
        else:
            panel = NSSavePanel.savePanel()

        panel.setDirectoryURL_(NSURL.fileURLWithPath_(self._current_directory))

        if panel.runModal() == NSModalResponseOK:
            if isinstance(panel, NSOpenPanel):
                self._selected_files = [url.path() for url in panel.URLs()]
            else:
                self._selected_files = [panel.URL().path()]
            return True
        return False


class LinuxFileDialogHelper(QFileDialogPlatformHelper):
    def show_dialog(self) -> bool:
        try:
            import gi

            gi.require_version("Gtk", "3.0")
            from gi.repository import Gtk
        except ImportError:
            print("GTK is not available. Make sure you have the required dependencies installed.")
            return False

        if self._options.acceptMode() == AcceptMode.AcceptOpen:
            dialog = Gtk.FileChooserDialog(
                title="Open File",
                action=Gtk.FileChooserAction.OPEN
                if self._options.fileMode() != FileMode.Directory
                else Gtk.FileChooserAction.SELECT_FOLDER,
            )
            dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
            dialog.add_button(Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        else:
            dialog = Gtk.FileChooserDialog(title="Save File", action=Gtk.FileChooserAction.SAVE)
            dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
            dialog.add_button(Gtk.STOCK_SAVE, Gtk.ResponseType.OK)

        dialog.set_current_folder(self._current_directory)
        dialog.set_select_multiple(self._options.fileMode() == FileMode.ExistingFiles)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            if dialog.get_select_multiple():
                self._selected_files = dialog.get_filenames()
            else:
                self._selected_files = [dialog.get_filename()]
            dialog.destroy()
            return True
        dialog.destroy()
        return False


class WindowsFileDialogHelper(QFileDialogPlatformHelper):
    def show_dialog(self) -> bool:
        try:
            import win32con
            import win32gui
        except ImportError:
            print("pywin32 is not available. Make sure you have it installed.")
            return False

        flags = win32con.OFN_EXPLORER
        if self._options.fileMode() == FileMode.ExistingFiles:
            flags |= win32con.OFN_ALLOWMULTISELECT

        if self._options.acceptMode() == AcceptMode.AcceptOpen:
            flags |= win32con.OFN_FILEMUSTEXIST

        file_filter = self._create_win32_file_filter()

        if self._options.acceptMode() == AcceptMode.AcceptOpen:
            (file_path, customfilter, flags) = win32gui.GetOpenFileNameW(InitialDir=self._current_directory, Flags=flags, Filter=file_filter, Title="Open File")
        else:
            (file_path, customfilter, flags) = win32gui.GetSaveFileNameW(InitialDir=self._current_directory, Flags=flags, Filter=file_filter, Title="Save File")

        if file_path:
            if flags & win32con.OFN_ALLOWMULTISELECT:
                # Handle multiple file selection
                files = file_path.split("\0")
                dir_path = files[0]
                self._selected_files = [os.path.join(dir_path, f) for f in files[1:]]
            else:
                self._selected_files = [file_path]
            return True
        return False

    def _create_win32_file_filter(self) -> str:
        filters = []
        for name_filter in self._options.nameFilters():
            description, extensions = name_filter.split("(")
            extensions = extensions.strip(")").replace("*", "")
            filters.append(f"{description.strip()} ({extensions})|{extensions}|")
        filters.append("All Files (*.*)|*.*|")
        return "".join(filters)


class QFileDialogHelper:
    @staticmethod
    def create_helper(options: QFileDialogOptions) -> QFileDialogPlatformHelper:
        import platform

        system = platform.system()

        if system == "Darwin":
            return MacFileDialogHelper(options)
        if system == "Linux":
            return LinuxFileDialogHelper(options)
        if system == "Windows":
            return WindowsFileDialogHelper(options)
        raise NotImplementedError(f"Unsupported platform: {system}")


# Usage example:
if __name__ == "__main__":
    options = QFileDialogOptions()
    options.setFileMode(FileMode.ExistingFiles)
    options.setAcceptMode(AcceptMode.AcceptOpen)
    options.setNameFilters(["Images (*.png *.jpg)", "Text files (*.txt)"])

    helper = QFileDialogHelper.create_helper(options)
    if helper.show_dialog():
        print("Selected files:", helper.selectedFiles())
    else:
        print("Dialog cancelled")
