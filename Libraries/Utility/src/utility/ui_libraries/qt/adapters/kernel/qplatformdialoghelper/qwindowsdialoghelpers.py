from __future__ import annotations

import os

from typing import TYPE_CHECKING

from qtpy.QtCore import QEventLoop, Qt
from qtpy.QtGui import QColor, QFont
from qtpy.QtWidgets import QDialog, QFileDialog, QFontDialog

from utility.system.win32.com.interfaces import COMDLG_FILTERSPEC, IShellItem
from utility.ui_libraries.qt.adapters.kernel.qplatformdialoghelper.qplatformdialoghelper import (
    QFileDialogPlatformHelper,
    QPlatformColorDialogHelper,
    QPlatformDialogHelper,
    QPlatformFileDialogHelper,
    QPlatformFontDialogHelper,
)

if TYPE_CHECKING:
    from qtpy.QtCore import QAbstractProxyModel, QObject, QUrl

try:
    from comtypes.client import CreateObject

    from utility.system.win32.com.com_helpers import S_OK
    from utility.system.win32.com.interfaces import COMDLG_FILTERSPEC, SIGDN, IFileOpenDialog, IFileSaveDialog, IShellItem
    from utility.system.win32.com.windialogs import FileDialogControlEvents

    USE_COMTYPES = True
except ImportError as err:
    try:
        import win32con
        import win32gui

        USE_COMTYPES = False
    except ImportError:
        raise ImportError("Neither comtypes nor pywin32 is available. Please install one of them.") from err


class WindowsFileDialogHelper(QFileDialogPlatformHelper):
    def __init__(self):
        super().__init__()
        self._dialog: IFileOpenDialog | IFileSaveDialog | None = None
        self._events: FileDialogControlEvents | None = None
        self._selected_files: list[str] = []

        self._current_directory: str = ""
        self._selected_name_filter: str = ""

    def show_dialog(self, hwnd: int | None = None) -> bool:
        if USE_COMTYPES:
            return self._show_dialog_comtypes(hwnd)
        return self._show_dialog_pywin32()

    def _show_dialog_comtypes(self, hwnd: int | None = None) -> bool:
        try:
            if self._options.acceptMode() == QFileDialog.AcceptMode.AcceptOpen:
                self._dialog = CreateObject(IFileOpenDialog)
            else:
                self._dialog = CreateObject(IFileSaveDialog)

            self._events = FileDialogControlEvents(self._dialog)
            cookie: int = self._dialog.Advise(self._events)

            options: int = self._get_file_dialog_options()
            self._dialog.SetOptions(options)

            if self._current_directory:
                shell_item: IShellItem = self._create_shell_item(self._current_directory)
                self._dialog.SetFolder(shell_item)

            if self._options.nameFilters():
                filters: list[COMDLG_FILTERSPEC] = self._create_file_filter()
                self._dialog.SetFileTypes(len(filters), filters)

            result = self._dialog.Show(hwnd or 0)

            if result == S_OK:
                if self._options.fileMode() == QFileDialog.FileMode.ExistingFiles:
                    items = self._dialog.GetResults()
                    self._selected_files = [self._get_shell_item_path(item) for item in items]
                else:
                    item = self._dialog.GetResult()
                    self._selected_files = [self._get_shell_item_path(item)]

                self._current_directory = os.path.dirname(self._selected_files[0])  # noqa: PTH120
                return True
            return False
        finally:
            if self._dialog:
                self._dialog.Unadvise(cookie)

    def _show_dialog_pywin32(self) -> bool:
        flags = win32con.OFN_EXPLORER
        if self._options.fileMode() == QFileDialog.FileMode.ExistingFiles:
            flags |= win32con.OFN_ALLOWMULTISELECT

        if self._options.acceptMode() == QFileDialog.AcceptMode.AcceptOpen:
            flags |= win32con.OFN_FILEMUSTEXIST

        file_filter = self._create_win32_file_filter()

        if self._options.acceptMode() == QFileDialog.AcceptMode.AcceptOpen:
            (file_path, customfilter, flags) = win32gui.GetOpenFileNameW(InitialDir=self._current_directory, Flags=flags, Filter=file_filter, Title="Open File")
        else:
            (file_path, customfilter, flags) = win32gui.GetSaveFileNameW(InitialDir=self._current_directory, Flags=flags, Filter=file_filter, Title="Save File")

        if file_path:
            if flags & win32con.OFN_ALLOWMULTISELECT:
                files = file_path.split("\0")
                dir_path = files[0]
                self._selected_files = [os.path.join(dir_path, f) for f in files[1:]]  # noqa: PTH118
            else:
                self._selected_files = [file_path]
            self._current_directory = os.path.dirname(self._selected_files[0])  # noqa: PTH120
            return True
        return False

    def _get_file_dialog_options(self) -> int:
        options = 0
        if self._options.fileMode() == QFileDialog.FileMode.ExistingFiles:
            options |= 0x200  # FOS_ALLOWMULTISELECT
        if self._options.acceptMode() == QFileDialog.AcceptMode.AcceptOpen:
            options |= 0x1000  # FOS_FILEMUSTEXIST
        if self._options.acceptMode() == QFileDialog.AcceptMode.AcceptSave:
            options |= 0x2  # FOS_OVERWRITEPROMPT
        return options

    def _create_file_filter(self) -> list[COMDLG_FILTERSPEC]:
        filters: list[COMDLG_FILTERSPEC] = []
        for name_filter in self._options.nameFilters():
            description, extensions = name_filter.split("(")
            extensions = extensions.strip(")").replace("*", "")
            filters.append(COMDLG_FILTERSPEC(description.strip(), extensions))
        return filters

    def _create_win32_file_filter(self) -> str:
        filters: list[str] = []
        for name_filter in self._options.nameFilters():
            description, extensions = name_filter.split("(")
            extensions = extensions.strip(")").replace("*", "")
            filters.append(f"{description.strip()} ({extensions})|{extensions}|")
        filters.append("All Files (*.*)|*.*|")
        return "".join(filters)

    def _get_shell_item_path(self, item: IShellItem) -> str:
        path: str = item.GetDisplayName(SIGDN.SIGDN_FILESYSPATH)
        return path

    def _create_shell_item(self, path: str) -> IShellItem:
        return IShellItem.from_path(path)

    def _get_hwnd_from_parent(self, parent: QObject | None) -> int | None:
        if parent is None:
            return None
        window = parent.window()
        if hasattr(window, "winId"):
            return int(window.winId())
        return None

    def exec(self) -> QPlatformDialogHelper.DialogCode:
        if self.show_dialog():
            return QPlatformDialogHelper.DialogCode.Accepted
        return QPlatformDialogHelper.DialogCode.Rejected

    def show(self, parent_window_flags: Qt.WindowType, parent_window_state: Qt.WindowState, parent: QObject | None):
        hwnd: int | None = self._get_hwnd_from_parent(parent)
        self.show_dialog(hwnd)

    def hide(self):
        if self._dialog:
            self._dialog.Close(S_OK)

    def setDirectory(self, directory: str):
        self._current_directory = directory

    def directory(self) -> str:
        return self._current_directory

    def selectFile(self, filename: str):
        if self._dialog:
            self._dialog.SetFileName(filename)

    def selectedFiles(self) -> list[str]:
        return self._selected_files

    def selectNameFilter(self, filter: str):  # noqa: A002
        self._selected_name_filter = filter
        if self._dialog:
            index = self._options.nameFilters().index(filter)
            self._dialog.SetFileTypeIndex(index + 1)

    def selectedNameFilter(self) -> str:
        return self._selected_name_filter

    def setFilter(self):
        if self._dialog:
            filters: list[COMDLG_FILTERSPEC] = self._create_file_filter()
            self._dialog.SetFileTypes(len(filters), filters)

    def setOptions(self, options: QFileDialog.Options):
        super().setOptions(options)
        if self._dialog:
            dialog_options: int = self._get_file_dialog_options()
            self._dialog.SetOptions(dialog_options)

    def setWindowTitle(self, title: str):
        if self._dialog:
            self._dialog.SetTitle(title)

    def defaultNameFilterString(self) -> str:
        return "All Files (*.*)"


class QWindowsDialogHelperBase(QPlatformDialogHelper):
    def __init__(self):
        super().__init__()
        self.m_eventLoop: QEventLoop | None = None
        self.m_visible: bool = False

    def exec(self) -> QPlatformDialogHelper.DialogCode:
        if self.m_eventLoop:
            raise RuntimeError("QWindowsDialogHelperBase::exec(): Recursive calls are not supported")
        self.m_eventLoop = QEventLoop()
        self.show(Qt.WindowType(0), Qt.WindowState.WindowNoState, None)
        self.m_eventLoop.exec()
        self.m_eventLoop = None
        return QPlatformDialogHelper.DialogCode.Accepted if self.result() else QPlatformDialogHelper.DialogCode.Rejected

    def show(self, parent_window_flags: Qt.WindowType, parent_window_state: Qt.WindowState, parent: QObject | None):
        self.m_visible = True

    def hide(self):
        self.m_visible = False
        if self.m_eventLoop:
            self.m_eventLoop.exit()

    def result(self) -> bool:
        return False

    def defaultStyleHint(self) -> QPlatformDialogHelper.StyleHint:
        return QPlatformDialogHelper.StyleHint.DialogIsQtWindow


class QWindowsFileDialogHelper(QWindowsDialogHelperBase, QPlatformFileDialogHelper):
    def __init__(self):
        super().__init__()
        self.m_fileDialog: QFileDialog | None = None
        self.m_selectedFiles: list[str] = []
        self.m_currentDirectory: str = ""
        self.m_selectedNameFilter: str = ""
        self.m_options: QFileDialog.Options = QFileDialog.Option(0)
        self.m_fileMode: QFileDialog.FileMode = QFileDialog.FileMode.AnyFile
        self.m_acceptMode: QFileDialog.AcceptMode = QFileDialog.AcceptMode.AcceptOpen

    def exec(self) -> QPlatformDialogHelper.DialogCode:
        if not self.m_fileDialog:
            self.m_fileDialog = QFileDialog()
        self._applyOptions()
        result = self.m_fileDialog.exec()
        if result == QDialog.DialogCode.Accepted:
            self.m_selectedFiles = self.m_fileDialog.selectedFiles()
            self.m_currentDirectory = self.m_fileDialog.directory().absolutePath()
            self.m_selectedNameFilter = self.m_fileDialog.selectedNameFilter()
            return QPlatformDialogHelper.DialogCode.Accepted
        return QPlatformDialogHelper.DialogCode.Rejected

    def show(self, parent_window_flags: Qt.WindowType, parent_window_state: Qt.WindowState, parent: QObject | None):
        if not self.m_fileDialog:
            self.m_fileDialog = QFileDialog(parent)
        self._applyOptions()
        self.m_fileDialog.setWindowFlags(parent_window_flags)
        self.m_fileDialog.setWindowState(parent_window_state)
        self.m_fileDialog.show()

    def hide(self):
        if self.m_fileDialog:
            self.m_fileDialog.hide()

    def setDirectory(self, directory: str):
        if self.m_fileDialog:
            self.m_fileDialog.setDirectory(directory)
        self.m_currentDirectory = directory

    def directory(self) -> str:
        if self.m_fileDialog:
            return self.m_fileDialog.directory().absolutePath()
        return self.m_currentDirectory

    def selectFile(self, filename: str):
        if self.m_fileDialog:
            self.m_fileDialog.selectFile(filename)

    def selectedFiles(self) -> list[str]:
        if self.m_fileDialog:
            return self.m_fileDialog.selectedFiles()
        return self.m_selectedFiles

    def setFilter(self):
        if self.m_fileDialog:
            filters: list[str] = []
            for name_filter in self.m_options.nameFilters():
                description, extensions = name_filter.split("(")
                extensions = extensions.strip(")").replace("*", "")
                filters.append(f"{description.strip()} ({extensions})")
            self.m_fileDialog.setNameFilters(filters)

    def selectNameFilter(self, filter: str):  # noqa: A002
        if self.m_fileDialog:
            self.m_fileDialog.selectNameFilter(filter)
        self.m_selectedNameFilter = filter

    def selectedNameFilter(self) -> str:
        if self.m_fileDialog:
            return self.m_fileDialog.selectedNameFilter()
        return self.m_selectedNameFilter

    def selectMimeTypeFilter(self, filter: str):  # noqa: A002
        if self.m_fileDialog:
            self.m_fileDialog.selectMimeTypeFilter(filter)

    def selectedMimeTypeFilter(self) -> str:
        if self.m_fileDialog:
            return self.m_fileDialog.selectedMimeTypeFilter()
        return ""

    def isSupportedUrl(self, url: str) -> bool:
        from qtpy.QtCore import QUrl
        parsed_url = QUrl(url)
        return parsed_url.isValid() and parsed_url.scheme() in ["file", ""]

    def defaultNameFilterString(self) -> str:
        return "All Files (*.*)"

    def setOptions(self, options: QFileDialog.Options):
        self.m_options = options
        if self.m_fileDialog:
            self._applyOptions()

    def options(self) -> QFileDialog.Options:
        return self.m_options

    def setFileMode(self, mode: QFileDialog.FileMode):
        self.m_fileMode = mode
        if self.m_fileDialog:
            self.m_fileDialog.setFileMode(mode)

    def fileMode(self) -> QFileDialog.FileMode:
        return self.m_fileMode

    def setAcceptMode(self, mode: QFileDialog.AcceptMode):
        self.m_acceptMode = mode
        if self.m_fileDialog:
            self.m_fileDialog.setAcceptMode(mode)

    def acceptMode(self) -> QFileDialog.AcceptMode:
        return self.m_acceptMode

    def setLabelText(self, label: QFileDialog.DialogLabel, text: str):
        if self.m_fileDialog:
            self.m_fileDialog.setLabelText(label, text)

    def labelText(self, label: QFileDialog.DialogLabel) -> str:
        if self.m_fileDialog:
            return self.m_fileDialog.labelText(label)
        return ""

    def setWindowTitle(self, title: str):
        if self.m_fileDialog:
            self.m_fileDialog.setWindowTitle(title)

    def windowTitle(self) -> str:
        if self.m_fileDialog:
            return self.m_fileDialog.windowTitle()
        return ""

    def _applyOptions(self):
        if self.m_fileDialog:
            self.m_fileDialog.setOptions(self.m_options)
            self.m_fileDialog.setFileMode(self.m_fileMode)
            self.m_fileDialog.setAcceptMode(self.m_acceptMode)

    def setDefaultSuffix(self, suffix: str):
        if self.m_fileDialog:
            self.m_fileDialog.setDefaultSuffix(suffix)

    def defaultSuffix(self) -> str:
        if self.m_fileDialog:
            return self.m_fileDialog.defaultSuffix()
        return ""

    def setHistory(self, paths: list[str]):
        if self.m_fileDialog:
            self.m_fileDialog.setHistory(paths)

    def history(self) -> list[str]:
        if self.m_fileDialog:
            return self.m_fileDialog.history()
        return []

    def setProxyModel(self, model: QAbstractProxyModel):
        if self.m_fileDialog:
            self.m_fileDialog.setProxyModel(model)

    def proxyModel(self) -> QAbstractProxyModel | None:
        if self.m_fileDialog:
            return self.m_fileDialog.proxyModel()
        return None

    def setSidebarUrls(self, urls: list[QUrl]):
        if self.m_fileDialog:
            self.m_fileDialog.setSidebarUrls(urls)

    def sidebarUrls(self) -> list[QUrl]:
        if self.m_fileDialog:
            return self.m_fileDialog.sidebarUrls()
        return []

    def setViewMode(self, mode: QFileDialog.ViewMode):
        if self.m_fileDialog:
            self.m_fileDialog.setViewMode(mode)

    def viewMode(self) -> QFileDialog.ViewMode:
        if self.m_fileDialog:
            return self.m_fileDialog.viewMode()
        return QFileDialog.ViewMode.Detail


class QWindowsColorDialogHelper(QWindowsDialogHelperBase, QPlatformColorDialogHelper):
    def __init__(self):
        super().__init__()
        self.m_color = QColor()

    def setCurrentColor(self, color: QColor):
        self.m_color: QColor = color
        self.currentColorChanged.emit(color)

    def currentColor(self) -> QColor:
        return self.m_color

    # Implement other required methods


class QWindowsFontDialogHelper(QWindowsDialogHelperBase, QPlatformFontDialogHelper):
    def __init__(self):
        super().__init__()
        self.m_font: QFont = QFont()
        self.m_options: QFontDialog.FontDialogOption | int = 0
        self.m_fontDialog: QFontDialog | None = None

    def exec(self) -> QPlatformDialogHelper.DialogCode:
        if not self.m_fontDialog:
            self.m_fontDialog = QFontDialog(self.m_font)
        self.m_fontDialog.setOptions(self.m_options)
        result = self.m_fontDialog.exec()
        if result == QFontDialog.DialogCode.Accepted:
            self.setCurrentFont(self.m_fontDialog.selectedFont())
            return QPlatformDialogHelper.DialogCode.Accepted
        return QPlatformDialogHelper.DialogCode.Rejected

    def show(self, parent_window_flags, parent_window_state: Qt.WindowState, parent: QObject | None):
        if not self.m_fontDialog:
            self.m_fontDialog = QFontDialog(self.m_font, parent)
        self.m_fontDialog.setOptions(self.m_options)
        self.m_fontDialog.setWindowFlags(parent_window_flags)
        self.m_fontDialog.setWindowState(parent_window_state)
        self.m_fontDialog.currentFontChanged.connect(self.currentFontChanged)
        self.m_fontDialog.show()

    def hide(self):
        if self.m_fontDialog:
            self.m_fontDialog.hide()

    def setCurrentFont(self, font: QFont):
        self.m_font = font
        if self.m_fontDialog:
            self.m_fontDialog.setCurrentFont(font)
        self.currentFontChanged.emit(font)

    def currentFont(self) -> QFont:
        if self.m_fontDialog:
            return self.m_fontDialog.currentFont()
        return self.m_font

    def setOption(self, option: QFontDialog.FontDialogOption, on: bool = True):  # noqa: FBT001, FBT002
        self.m_options.setFlag(option, on)
        if self.m_fontDialog:
            self.m_fontDialog.setOption(option, on)

    def testOption(self, option: QFontDialog.FontDialogOption) -> bool:
        return bool(self.m_options & option)

    def setOptions(self, options: QFontDialog.FontDialogOption):
        self.m_options = options
        if self.m_fontDialog:
            self.m_fontDialog.setOptions(options)

    def options(self) -> QFontDialog.FontDialogOption | int:
        return self.m_options

    def setWindowTitle(self, title: str):
        if self.m_fontDialog:
            self.m_fontDialog.setWindowTitle(title)

    def windowTitle(self) -> str:
        if self.m_fontDialog:
            return self.m_fontDialog.windowTitle()
        return ""

    def defaultStyleHint(self) -> QPlatformDialogHelper.StyleHint:
        return QPlatformDialogHelper.StyleHint.SH_CustomBase

    def styleHint(self) -> QPlatformDialogHelper.StyleHint:
        return self.defaultStyleHint()


    def updateFont(self, font: QFont):
        self.setCurrentFont(font)
        if self.m_fontDialog:
            self.m_fontDialog.setCurrentFont(font)


class QWindowsDialogHelper(QWindowsDialogHelperBase):
    def __init__(self):
        super().__init__()
        self.m_helper: QPlatformDialogHelper | None = None

    def exec(self) -> QPlatformDialogHelper.DialogCode:
        if self.m_helper:
            return self.m_helper.exec()
        return QPlatformDialogHelper.DialogCode.Rejected

    def show(self, parent_window_flags: Qt.WindowType, parent_window_state: Qt.WindowState, parent: QObject | None):
        if self.m_helper:
            self.m_helper.show(parent_window_flags, parent_window_state, parent)

    def hide(self):
        if self.m_helper:
            self.m_helper.hide()

    def setHelper(self, helper: QPlatformDialogHelper):
        self.m_helper: QPlatformDialogHelper = helper
