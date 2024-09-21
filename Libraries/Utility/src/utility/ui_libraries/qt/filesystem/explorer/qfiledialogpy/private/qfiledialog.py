from __future__ import annotations

import sys

from enum import IntEnum, IntFlag
from typing import TYPE_CHECKING, ClassVar, Iterable, overload

import qtpy

from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QMessageBox
from PyQt6.QtCore import QModelIndex, QPoint
from PyQt6.QtGui import QAction
from qtpy.QtCore import (
    QDir,
    QEvent,
    QFileInfo,
    QUrl,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtWidgets import (
    QDialog,
    QFileIconProvider,
    QWidget,
)

from utility.ui_libraries.qt.filesystem.explorer.qfiledialogpy.private.qfiledialog_p import (
    QFileDialogOptions,
    QFileDialogPrivate,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from PyQt6.QtCore import QAbstractProxyModel, Qt
    from qtpy import QtCore, QtGui
    from qtpy.QtCore import PYQT_SLOT, QByteArray
    from qtpy.QtWidgets import (
        QAbstractItemDelegate,
        QFileDialog as RealQFileDialog,  # noqa: TCH004
        )


_TEST_FULL_OVERRIDE: bool = False


class QFileDialogArgs:
    def __init__(self, url: QUrl = QUrl()):  # noqa: B008
        self.parent: QWidget | None = None
        self.caption: str = ""
        self.directory: QUrl = url
        self.selection: str = ""
        self.filter: str = ""
        self.mode: int = QFileDialog.FileMode.AnyFile
        self.options: int = QFileDialog.Option.DontUseNativeDialog


class QFileDialog(RealQFileDialog if TYPE_CHECKING else QDialog):
    """A dialog that allows users to select files or directories."""
    # Signals
    fileSelected: ClassVar[Signal] = Signal(QUrl)
    filterSelected: ClassVar[Signal] = Signal(str)
    filesSelected: ClassVar[Signal] = Signal(list)
    directoryEntered: ClassVar[Signal] = Signal(str)
    currentChanged: ClassVar[Signal] = Signal(str)
    urlSelected = Signal(QUrl)
    urlsSelected = Signal(list)
    currentUrlChanged = Signal(QUrl)
    directoryUrlEntered = Signal(QUrl)
    _q_fileRenamed = Signal(str, str, str)
    _q_pathChanged = Signal(str)
    _q_navigateBackward = Signal()
    _q_navigateForward = Signal()
    _q_navigateToParent = Signal()
    _q_createDirectory = Signal()
    _q_showListView = Signal()
    _q_showDetailsView = Signal()
    _q_showContextMenu = Signal(QPoint)
    _q_renameCurrent = Signal()
    _q_deleteCurrent = Signal()

    _q_showHidden = Signal()
    _q_updateOkButton = Signal()
    _q_currentChanged = Signal(QModelIndex)
    _q_enterDirectory = Signal(QModelIndex)
    _q_emitUrlSelected = Signal(QUrl)
    _q_emitUrlsSelected = Signal(list)

    _q_nativeCurrentChanged = Signal(QUrl)
    _q_nativeEnterDirectory = Signal(QUrl)
    _q_goToDirectory = Signal(str)
    _q_useNameFilter = Signal(int)
    _q_selectionChanged = Signal()
    _q_goToUrl = Signal(QUrl)
    _q_goHome = Signal()
    _q_showHeader = Signal(QAction)
    _q_autoCompleteFileName = Signal(str)
    _q_rowsInserted = Signal(QModelIndex)


    def private(self) -> QFileDialogPrivate:

        if self._private is None:
            raise RuntimeError("QFileDialogPrivate's q_ptr was not set")
        if not isinstance(self._private, QFileDialogPrivate):
            raise TypeError("QFileDialogPrivate's q_ptr is not a QFileDialogPrivate")
        return self._private


    # Type checking and enums
    class FileMode(IntFlag):
        """Specifies the file mode of the dialog."""

        AnyFile = 0
        ExistingFile = 1
        Directory = 2
        ExistingFiles = 3
        DirectoryOnly = 4

    class DialogLabel(IntEnum):
        """Specifies the label of the dialog."""

        LookIn = 0
        FileName = 1
        FileType = 2
        Accept = 3
        Reject = 4

    class AcceptMode(IntEnum):
        """Specifies whether the dialog is for opening or saving files."""

        AcceptOpen = 0
        AcceptSave = 1

    class ViewMode(IntEnum):  # noqa: D106
        Detail = 0
        List = 1

    Option = RealQFileDialog.Option
    if qtpy.QT5:
        Options: type[RealQFileDialog.Options | QFileDialogOptions] = RealQFileDialog.Options
    if qtpy.QT6 or TYPE_CHECKING:
        Options = QFileDialogOptions

    def d_func(self) -> QFileDialogPrivate:
        if self._private is None:
            raise RuntimeError("QFileDialogPrivate was not set")
        if not isinstance(self._private, QFileDialogPrivate):
            raise TypeError(f"QFileDialogPrivate expected but got {type(self._private).__name__}")

        return self._private


    # Static methods (converted to class methods)

    @classmethod
    def getOpenFileContent(cls, nameFilter: str, fileContentsReady: Callable[[str, bytes], None]) -> None:  # noqa: N803
        # This method is platform-specific and might require additional implementation
        pass


    @classmethod
    def saveFileContent(cls, fileContent: bytes, fileNameHint: str = "") -> None:  # noqa: N803
        # This method is platform-specific and might require additional implementation

        pass

    @classmethod
    def getOpenFileName(  # noqa: PLR0913
        cls,
        parent: QWidget | None = None,

        caption: str = "",
        directory: str = "",
        filter: str = "",  # noqa: A002
        initialFilter: str = "",  # noqa: N803
        options: Option = Option(0),  # noqa: A002, N803, B008
    ) -> tuple[str, str]:  # noqa: A002, N803
        dialog = QFileDialog(parent, caption, directory, filter)
        dialog.setOptions(options)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        if initialFilter:
            dialog.selectNameFilter(initialFilter)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.selectedFiles()[0], dialog.selectedNameFilter()
        return "", ""

    @classmethod
    def getOpenFileNames(  # noqa: PLR0913
        cls,
        parent: QWidget | None = None,

        caption: str = "",
        directory: str = "",
        filter: str = "",  # noqa: A002
        initialFilter: str = "",  # noqa: N803
        options: Option = Option(0),  # noqa: B008
    ) -> tuple[list[str], str]:
        dialog = QFileDialog(parent, caption, directory, filter)
        dialog.setOptions(options)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        if initialFilter:
            dialog.selectNameFilter(initialFilter)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.selectedFiles(), dialog.selectedNameFilter()
        return [], ""

    @classmethod
    def getSaveFileName(  # noqa: PLR0913
        cls,
        parent: QWidget | None = None,

        caption: str = "",
        directory: str = "",
        filter: str = "",  # noqa: A002
        initialFilter: str = "",  # noqa: N803
        options: Option = Option(0),  # noqa: B008
    ) -> tuple[str, str]:
        dialog = QFileDialog(parent, caption, directory, filter)
        dialog.setOptions(options)
        dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        if initialFilter:
            dialog.selectNameFilter(initialFilter)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.selectedFiles()[0], dialog.selectedNameFilter()
        return "", ""

    @classmethod
    def getExistingDirectory(
        cls,
        parent: QWidget | None = None,

        caption: str = "",
        directory: str = "",
        options: Option = Option.ShowDirsOnly,
    ) -> str:
        dialog = QFileDialog(parent, caption, directory)
        dialog.setOptions(options)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.selectedFiles()[0]
        return ""

    @classmethod
    def getExistingDirectoryUrl(
        cls,
        parent: QWidget | None = None,

        caption: str = "",
        directory: QUrl = QUrl(),  # noqa: B008
        options: Option = Option.ShowDirsOnly,
        supportedSchemes: Iterable[str] = (),  # noqa: N803
    ) -> QUrl:
        dialog = QFileDialog(parent, caption)
        dialog.setOptions(options)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        dialog.setDirectoryUrl(directory)
        dialog.setSupportedSchemes(supportedSchemes)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.selectedUrls()[0]
        return QUrl()

    @classmethod
    def getOpenFileUrl(  # noqa: PLR0913
        cls,
        parent: QWidget | None = None,

        caption: str = "",
        directory: QUrl = QUrl(),  # noqa: B008
        filter: str = "",  # noqa: A002
        initialFilter: str = "",  # noqa: N803
        options: Option = Option(0),  # noqa: B008
        supportedSchemes: Iterable[str] = (),  # noqa: N803
    ) -> tuple[QUrl, str]:
        dialog = QFileDialog(parent, caption)
        dialog.setOptions(options)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        dialog.setDirectoryUrl(directory)
        dialog.setNameFilter(filter)
        dialog.setSupportedSchemes(supportedSchemes)
        if initialFilter:
            dialog.selectNameFilter(initialFilter)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.selectedUrls()[0], dialog.selectedNameFilter()
        return QUrl(), ""

    @classmethod
    def getOpenFileUrls(  # noqa: PLR0913
        cls,
        parent: QWidget | None = None,
        caption: str = "",
        directory: QUrl = QUrl(),  # noqa: B008
        filter: str = "",  # noqa: A002
        initialFilter: str = "",  # noqa: N803
        options: Option = Option(0),  # noqa: B008
        supportedSchemes: Iterable[str] = (),  # noqa: N803
    ) -> tuple[list[QUrl], str]:
        dialog = QFileDialog(parent, caption)
        dialog.setOptions(options)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        dialog.setDirectoryUrl(directory)
        dialog.setNameFilter(filter)
        dialog.setSupportedSchemes(supportedSchemes)
        if initialFilter:
            dialog.selectNameFilter(initialFilter)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.selectedUrls(), dialog.selectedNameFilter()
        return [], ""

    @classmethod
    def getSaveFileUrl(  # noqa: PLR0913
        cls,
        parent: QWidget | None = None,
        caption: str = "",
        directory: QUrl = QUrl(),  # noqa: B008
        filter: str = "",  # noqa: A002
        initialFilter: str = "",  # noqa: N803
        options: Option = Option(0),  # noqa: B008
        supportedSchemes: Iterable[str] = (),  # noqa: N803
    ) -> tuple[QUrl, str]:
        dialog = QFileDialog(parent, caption)
        dialog.setOptions(options)
        dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        dialog.setDirectoryUrl(directory)
        dialog.setNameFilter(filter)
        dialog.setSupportedSchemes(supportedSchemes)
        if initialFilter:
            dialog.selectNameFilter(initialFilter)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.selectedUrls()[0], dialog.selectedNameFilter()
        return QUrl(), ""

    # Initialization

    # Overloaded methods
    @overload
    def __init__(self, parent: QWidget | None = None, f: QtCore.Qt.WindowType | None = None) -> None: ...
    @overload
    def __init__(self, parent: QWidget | None = None, caption: str | None = None, directory: str | None = None, filter: str | None = None) -> None: ...

    def __init__(
        self,
        parent: QWidget | None = None,
        caption: str = "",
        directory: str = "",
        filter: str = "",  # noqa: A002
    ):
        self._private: QFileDialogPrivate = QFileDialogPrivate(self)
        super().__init__(parent)
        self._private.init(QFileDialogArgs(QUrl(directory)))

    # Directory operations
    @overload
    def setDirectory(self, directory: str) -> None: ...  # noqa: F811
    @overload
    def setDirectory(self, adirectory: QDir) -> None: ...
    def setDirectory(self, directory: str | QDir) -> None:  # pyright: ignore[reportInconsistentOverload]
        if isinstance(directory, QDir):
            directory = directory.absolutePath()
        self._private.setDirectory_sys(QUrl.fromLocalFile(directory))

    def directory(self) -> QDir:
        return QDir(self._private.directory_sys().toLocalFile())

    # File operations
    def selectFile(self, filename: str) -> None:
        self._private.selectFile_sys(QUrl.fromLocalFile(filename))

    def selectedFiles(self) -> list[str]:
        return [url.toLocalFile() for url in self._private.selectedFiles_sys()]

    # Filter operations
    def setNameFilter(self, filter: str) -> None:  # noqa: A002
        self._private.setNameFilters([filter])
    def setNameFilters(self, filters: list[str]) -> None:
        self._private.setNameFilters(filters)

    def nameFilters(self) -> list[str]:
        return self._private.nameFilters()

    def selectNameFilter(self, filter: str) -> None:  # noqa: A002
        self._private.selectNameFilter_sys(filter)
    def selectedNameFilter(self) -> str:
        return self._private.selectedNameFilter_sys()

    # Mode operations
    def setFileMode(self, mode: QFileDialog.FileMode) -> None:
        self._private.options.setFileMode(mode)
    def fileMode(self) -> QFileDialog.FileMode:
        return self._private.options.fileMode()


    def setAcceptMode(self, mode: QFileDialog.AcceptMode) -> None:
        self._private.options.setAcceptMode(mode)
    def acceptMode(self) -> QFileDialog.AcceptMode:
        return self._private.options.acceptMode()


    # Option operations
    def setOption(self, option: QFileDialog.Option, on: bool = True) -> None:  # noqa: FBT001, FBT002
        previous_options: QFileDialog.Options = self.options()
        if (not (previous_options & option)) != (not on):
            self.setOptions(previous_options ^ option)

    def testOption(self, option: QFileDialog.Option) -> bool:
        return self._private.options.testOption(option)

    def setOptions(self, options: QFileDialog.Options) -> None:
        changed: QFileDialogOptions = options ^ self.options()
        if not changed:
            return

        self._private.options.setOptions(QFileDialogOptions(int(options)))

        if (options & QFileDialog.Option.DontUseNativeDialog) and not self._private.usingWidgets():
            self._private.createWidgets()

        if self._private.usingWidgets():
            if changed & QFileDialog.Option .DontResolveSymlinks:
                self._private.model.setResolveSymlinks(not (options & QFileDialog.Option.DontResolveSymlinks))
            if changed & QFileDialog.Option.ReadOnly:
                ro = bool(options & QFileDialog.Option.ReadOnly)
                self._private.model.setReadOnly(ro)

                self._private.ui.newFolderButton.setEnabled(not ro)
                self._private.renameAction.setEnabled(not ro)
                self._private.deleteAction.setEnabled(not ro)

            if changed & QFileDialog.Option.DontUseCustomDirectoryIcons:
                provider_options: QFileDialog.Options = self.iconProvider().options()
                provider_options.setFlag(QFileIconProvider.Option.DontUseCustomDirectoryIcons,
                                         bool(options & QFileDialog.Option.DontUseCustomDirectoryIcons))

                self.iconProvider().setOptions(provider_options)

        if changed & QFileDialog.Option.HideNameFilterDetails:
            self.setNameFilters(self._private.options.nameFilters())

        if changed & QFileDialog.Option.ShowDirsOnly:
            self.setFilter(
                (self.filter() & ~QDir.Filter.Files)
                if (options & QFileDialog.Option.ShowDirsOnly)
                else (self.filter() | QDir.Filter.Files)
            )

    def options(self) -> QFileDialog.Options:
        return QFileDialog.Options(int(self._private.options.options()))

    # MIME type operations
    def selectedMimeTypeFilter(self) -> str:
        return self._private.selectedMimeTypeFilter_sys()
    def supportedSchemes(self) -> list[str]:
        return self._private.options.supportedSchemes()
    def setSupportedSchemes(self, schemes: Iterable[str | None]) -> None:
        self._private.options.setSupportedSchemes(schemes)

    # MIME type operations

    def selectMimeTypeFilter(self, filter: str | None) -> None:  # noqa: A002
        self._private.options.selectMimeTypeFilter(filter)
    def mimeTypeFilters(self) -> list[str]:
        return self._private.options.mimeTypeFilters()

    def setMimeTypeFilters(self, filters: Iterable[str | None]) -> None:
        self._private.options.setMimeTypeFilters(filters)

    # URL operations
    def selectedUrls(self) -> list[QUrl]:
        return self._private.selectedFiles_sys()
    def selectUrl(self, url: QUrl) -> None:
        self._private.selectFile_sys(url)
    def directoryUrl(self) -> QUrl:
        return self._private.directory_sys()
    def setDirectoryUrl(self, directory: QUrl) -> None:
        self._private.setDirectory_sys(directory)

    # Visibility operations
    def setVisible(self, visible: bool) -> None:  # noqa: FBT001
        if self._private.canBeNativeDialog():
            self._private.setVisible_sys(visible)
        else:
            QDialog.setVisible(self, visible)

    # Open operations
    @overload
    def open(self) -> None: ...
    @overload
    def open(self, slot: PYQT_SLOT) -> None: ...

    def setFilter(self, filters: Qt.Filters) -> None:
        self._private.options.setFilter(filters)
    def filter(self) -> QDir.Filters:
        return self._private.options.filter()
    def proxyModel(self) -> QAbstractProxyModel | None:
        return self._private.proxyModel
    def setProxyModel(self, model: QAbstractProxyModel | None) -> None:
        self._private.setProxyModel(model)

    # State operations
    def restoreState(self, state: QByteArray | bytes | bytearray | memoryview) -> bool:
        return self._private.restoreState(state)
    def saveState(self) -> QByteArray:
        return self._private.saveState()

    # Sidebar operations
    def sidebarUrls(self) -> list[QUrl]:
        return self._private.options.sidebarUrls()
    def setSidebarUrls(self, urls: list[QUrl]) -> None:
        self._private.options.setSidebarUrls(urls)
        if self._private.usingWidgets():
            self._private.ui.sidebar.setUrls(urls)


    # Event handling
    def changeEvent(self, e: QEvent) -> None:
        if e.type() == QEvent.Type.LanguageChange:
            self.retranslateStrings()
        super().changeEvent(e)

    def retranslateStrings(self) -> None:
        """Retranslate the UI, including all child widgets."""
        # Update main dialog elements
        self.setWindowTitle(QCoreApplication.translate("QFileDialog", "Select File"))
        self.setLabelText(self.DialogLabel.LookIn, QCoreApplication.translate("QFileDialog", "Look in:"))
        self.setLabelText(self.DialogLabel.FileName, QCoreApplication.translate("QFileDialog", "File name:"))
        self.setLabelText(self.DialogLabel.FileType, QCoreApplication.translate("QFileDialog", "Files of type:"))
        self.setLabelText(self.DialogLabel.Accept, QCoreApplication.translate("QFileDialog", "Open" if self.acceptMode() == self.AcceptMode.AcceptOpen else "Save"))
        self.setLabelText(self.DialogLabel.Reject, QCoreApplication.translate("QFileDialog", "Cancel"))

        # Recursively update all child widgets
        def retranslate_widget(widget: QWidget) -> None:
            widget.setToolTip(QCoreApplication.translate("QFileDialog", widget.toolTip()))
            widget.setWhatsThis(QCoreApplication.translate("QFileDialog", widget.whatsThis()))
            widget.setStatusTip(QCoreApplication.translate("QFileDialog", widget.statusTip()))
            widget.setAccessibleName(QCoreApplication.translate("QFileDialog", widget.accessibleName()))
            widget.setAccessibleDescription(QCoreApplication.translate("QFileDialog", widget.accessibleDescription()))
            widget.setWindowTitle(QCoreApplication.translate("QFileDialog", widget.windowTitle()))
            # Remove translation for window icon
            widget.setWindowIconText(QCoreApplication.translate("QFileDialog", widget.windowIconText()))

            # Recursively retranslate child widgets
            for child in widget.children():
                if isinstance(child, QWidget):
                    retranslate_widget(child)

        # Start the recursive retranslation from the main dialog
        retranslate_widget(self)

        # Update specific UI elements if using custom widgets
        if self._private.usingWidgets():
            self._private.ui.newFolderButton.setText(QCoreApplication.translate("QFileDialog", "New Folder"))
            self._private.ui.listModeButton.setText(QCoreApplication.translate("QFileDialog", "List View"))
            self._private.ui.detailModeButton.setText(QCoreApplication.translate("QFileDialog", "Detail View"))

    def accept(self) -> None:  # noqa: C901, PLR0911, PLR0912
        # Implementation from qfiledialog.cpp:2810
        files: list[str] = self.selectedFiles()
        if not files:
            return

        lineEditText = self._private.lineEdit().text()
        if lineEditText == "..":
            self._private._q_navigateToParent()  # noqa: SLF001
            self._private.lineEdit().selectAll()
            return

        file_mode = self.fileMode()
        if file_mode in (self.FileMode.DirectoryOnly, self.FileMode.Directory):
            fn = files[0]
            info = QFileInfo(fn)
            if not info.exists():
                info = QFileInfo(self._private.getEnvironmentVariable(fn))
            if not info.exists():
                self._private.showWarningMessage(
                    QCoreApplication.translate("QFileDialog", "The directory does not exist."),
                    QCoreApplication.translate("QFileDialog", "Directory not found"),
                    QMessageBox.StandardButton.Ok,
                    QMessageBox.StandardButton.Cancel,
                )
                return

            if info.isDir():
                self._private.emitFilesSelected(files)
                super().accept()
            return

        if file_mode == self.FileMode.AnyFile:
            fn = files[0]
            info = QFileInfo(fn)
            if info.isDir():
                self.setDirectory(info.absoluteFilePath())
                return

            if not info.exists():
                max_name_length = self._private.maxNameLength(info.path())
                if max_name_length >= 0 and len(info.fileName()) > max_name_length:
                    QMessageBox.warning(
                        QCoreApplication.translate("QFileDialog", "The file name is too long."),
                        QCoreApplication.translate("QFileDialog", "File name too long"),
                        QMessageBox.StandardButton.Ok,
                        QMessageBox.StandardButton.Cancel,
                    )
                    return


            if not info.exists() or self.testOption(self.Option.DontConfirmOverwrite) or self.acceptMode() == self.AcceptMode.AcceptOpen:
                self._private.emitFilesSelected([fn])
                super().accept()
            else:
                overwrite = self._private.showOverwriteConfirmationDialog(fn)
                if overwrite:
                    self._private.emitFilesSelected([fn])
                    super().accept()
            return

        if file_mode in (self.FileMode.ExistingFile, self.FileMode.ExistingFiles):
            for file in files:
                info = QFileInfo(file)
                if not info.exists():
                    info = QFileInfo(self._private.getEnvironmentVariable(file))
                if not info.exists():
                    QMessageBox.warning(
                        QCoreApplication.translate("QFileDialog", "The file does not exist."),
                        QCoreApplication.translate("QFileDialog", "File not found"),
                        QMessageBox.StandardButton.Ok,
                        QMessageBox.StandardButton.Cancel,
                    )
                    return

                if info.isDir():
                    self.setDirectory(info.absoluteFilePath())
                    self._private.lineEdit().clear()
                    return
            self._private.emitFilesSelected(files)
            super().accept()
            return
    def done(self, result: int) -> None:
        super().done(result)

    # Label operations
    def labelText(self, label: QFileDialog.DialogLabel) -> str:
        return super().labelText(label)
    def setLabelText(self, label: QFileDialog.DialogLabel, text: str | None) -> None:
        super().setLabelText(label, text)

    # Icon provider operations
    def iconProvider(self) -> QtGui.QAbstractFileIconProvider | None:
        return super().iconProvider()
    def setIconProvider(self, provider: QtGui.QAbstractFileIconProvider | None) -> None:
        super().setIconProvider(provider)

    # Item delegate operations
    def itemDelegate(self) -> QAbstractItemDelegate | None:
        return super().itemDelegate()
    def setItemDelegate(self, delegate: QAbstractItemDelegate | None) -> None:
        super().setItemDelegate(delegate)

    # History operations
    def history(self) -> list[str]:
        return super().history()
    def setHistory(self, paths: Iterable[str | None]) -> None:
        super().setHistory(paths)

    # Suffix operations
    def defaultSuffix(self) -> str:
        return super().defaultSuffix()
    def setDefaultSuffix(self, suffix: str | None) -> None:
        super().setDefaultSuffix(suffix)

    # View mode operations
    def viewMode(self) -> QFileDialog.ViewMode:
        return super().viewMode()

    def setViewMode(self, mode: QFileDialog.ViewMode) -> None:
        super().setViewMode(mode)

    def setFileMode(self, mode: QFileDialog.FileMode) -> None:
        ...  # noqa: F811



if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication

    app = QApplication([])
    dialog = QFileDialog()
    dialog.setDirectory("C:/")
    dialog.setNameFilter("*.txt")
    dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
    dialog.setOption(QFileDialog.Option.DontUseNativeDialog)
    dialog.setOption(QFileDialog.Option.ShowDirsOnly)
    dialog.setOption(QFileDialog.Option.DontConfirmOverwrite)
    dialog.setOption(QFileDialog.Option.ReadOnly)
    dialog.show()
    sys.exit(app.exec())
