from __future__ import annotations

import os
import sys
import tempfile

from collections.abc import Callable
from enum import Enum, IntFlag
from typing import TYPE_CHECKING, ClassVar, Iterable, overload

from loggerplus import RobustLogger
from qtpy.QtCore import (
    QByteArray,
    QDataStream,
    QDir,
    QEvent,
    QFileInfo,
    QIODevice,
    QModelIndex,
    QObject,
    QPoint,
    QRegularExpression,
    QSortFilterProxyModel,
    QUrl,
    Qt,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtWidgets import QAction, QApplication, QDialog, QDialogButtonBox, QFileDialog as RealQFileDialog, QFileIconProvider, QFileSystemModel, QListView, QMessageBox

from utility.ui_libraries.qt.filesystem.explorer.qfiledialog.private.qfiledialog import QFileDialogOptionsPrivate, QFileDialogPrivate, qt_make_filter_list
from utility.ui_libraries.qt.kernel.qplatformdialoghelper.qplatformdialoghelper import QPlatformFileDialogHelper
from utility.ui_libraries.qt.tests.test_enum_handling import sip_enum_to_int

if TYPE_CHECKING:
    from qtpy.QtCore import (
        PYQT_SLOT,
        QAbstractProxyModel,  # pyright: ignore[reportPrivateImportUsage]
        QItemSelectionModel,
    )
    from qtpy.QtWidgets import QAbstractItemDelegate, QPushButton, QWidget


def qt_strip_filters(filters: list[str]) -> list[str]:
    """Strip the filters by removing the details, e.g. (*.*)."""
#if QT_CONFIG(regularexpression)
    strippedFilters = []
    r = QRegularExpression(QPlatformFileDialogHelper.filterRegExp)
    for filter in filters:
        filterName = ""
        match = r.match(filter)
        if match.hasMatch():
            filterName = match.captured(1)
        strippedFilters.append(filterName.strip())
    return strippedFilters
#else
#    return filters
#endif


class QFileDialogOptions(QObject):
    """Rewritten implementation of the exposed class QFileDialog.Option provides in the bindings."""
    ShowDirsOnly = RealQFileDialog.Option.ShowDirsOnly if hasattr(RealQFileDialog.Option, "ShowDirsOnly") else RealQFileDialog.ShowDirsOnly
    DontResolveSymlinks = RealQFileDialog.Option.DontResolveSymlinks if hasattr(RealQFileDialog.Option, "DontResolveSymlinks") else RealQFileDialog.DontResolveSymlinks
    DontConfirmOverwrite = RealQFileDialog.Option.DontConfirmOverwrite if hasattr(RealQFileDialog.Option, "DontConfirmOverwrite") else RealQFileDialog.DontConfirmOverwrite
    if hasattr(RealQFileDialog.Option, "DontUseSheet") or hasattr(RealQFileDialog.Option, "DontUseSheet"):
        DontUseSheet = RealQFileDialog.Option.DontUseSheet if hasattr(RealQFileDialog.Option, "DontUseSheet") else RealQFileDialog.DontUseSheet
    DontUseNativeDialog = RealQFileDialog.Option.DontUseNativeDialog if hasattr(RealQFileDialog.Option, "DontUseNativeDialog") else RealQFileDialog.DontUseNativeDialog
    ReadOnly = RealQFileDialog.Option.ReadOnly if hasattr(RealQFileDialog.Option, "ReadOnly") else RealQFileDialog.ReadOnly
    HideNameFilterDetails = RealQFileDialog.Option.HideNameFilterDetails if hasattr(RealQFileDialog.Option, "HideNameFilterDetails") else RealQFileDialog.HideNameFilterDetails
    DontUseCustomDirectoryIcons = RealQFileDialog.Option.DontUseCustomDirectoryIcons if hasattr(RealQFileDialog.Option, "DontUseCustomDirectoryIcons") else RealQFileDialog.DontUseCustomDirectoryIcons  # noqa: E501
    if not TYPE_CHECKING:
        FileDialogOption = RealQFileDialog.Option
    else:
        class FileDialogOption(IntFlag, RealQFileDialog.Option, int, RealQFileDialog.Options):
            """The exposed class QFileDialog provides in the bindings."""
            ShowDirsOnly = RealQFileDialog.Option.ShowDirsOnly if hasattr(RealQFileDialog.Option, "ShowDirsOnly") else RealQFileDialog.ShowDirsOnly
            DontResolveSymlinks = RealQFileDialog.Option.DontResolveSymlinks if hasattr(RealQFileDialog.Option, "DontResolveSymlinks") else RealQFileDialog.DontResolveSymlinks
            DontConfirmOverwrite = RealQFileDialog.Option.DontConfirmOverwrite if hasattr(RealQFileDialog.Option, "DontConfirmOverwrite") else RealQFileDialog.DontConfirmOverwrite  # noqa: E501
            DontUseSheet = RealQFileDialog.Option.DontUseSheet if hasattr(RealQFileDialog.Option, "DontUseSheet") else RealQFileDialog.DontUseSheet
            DontUseNativeDialog = RealQFileDialog.Option.DontUseNativeDialog if hasattr(RealQFileDialog.Option, "DontUseNativeDialog") else RealQFileDialog.DontUseNativeDialog
            ReadOnly = RealQFileDialog.Option.ReadOnly if hasattr(RealQFileDialog.Option, "ReadOnly") else RealQFileDialog.ReadOnly
            HideNameFilterDetails = RealQFileDialog.Option.HideNameFilterDetails if hasattr(RealQFileDialog.Option, "HideNameFilterDetails") else RealQFileDialog.HideNameFilterDetails  # noqa: E501
            DontUseCustomDirectoryIcons = RealQFileDialog.Option.DontUseCustomDirectoryIcons if hasattr(RealQFileDialog.Option, "DontUseCustomDirectoryIcons") else RealQFileDialog.DontUseCustomDirectoryIcons  # noqa: E501

            def __hash__(self):
                return int(self)
            def __bool__(self):
                return bool(int(self))
            def __invert__(self):
                return ~QFileDialogOptions.FileDialogOption(int(self))
            def __index__(self):
                return int(self)
            def __int__(self):
                return int(self)

            def __or__(self, other: QFileDialogOptions.FileDialogOption | RealQFileDialog.Options | RealQFileDialog.Option | int) -> QFileDialogOptions.FileDialogOption:
                if isinstance(other, (QFileDialogOptions.FileDialogOption,
                                    RealQFileDialog.Options, RealQFileDialog.Option, int)):
                    return QFileDialogOptions.FileDialogOption(int(self) | int(other))
                return NotImplemented
            def __ror__(self, other):
                if isinstance(other, (QFileDialogOptions.FileDialogOption,
                                    RealQFileDialog.Options, RealQFileDialog.Option, int)):
                    return RealQFileDialog.Options(int(self) | int(other))
                return NotImplemented
            def __and__(self, other: QFileDialogOptions.FileDialogOption | RealQFileDialog.Options | RealQFileDialog.Option | int) -> QFileDialogOptions.FileDialogOption:
                if isinstance(other, (QFileDialogOptions.FileDialogOption,
                                    RealQFileDialog.Options, RealQFileDialog.Option, int)):
                    return QFileDialogOptions.FileDialogOption(int(self) & int(other))
                return NotImplemented
            def __rand__(self, other):
                if isinstance(other, (QFileDialogOptions.FileDialogOption,
                                    RealQFileDialog.Options, RealQFileDialog.Option, int)):
                    return RealQFileDialog.Options(int(self) & int(other))
                return NotImplemented
            def __xor__(self, other: QFileDialogOptions.FileDialogOption | RealQFileDialog.Options | RealQFileDialog.Option | int) -> QFileDialogOptions.FileDialogOption:
                if isinstance(other, (QFileDialogOptions.FileDialogOption,
                                    RealQFileDialog.Options, RealQFileDialog.Option, int)):
                    return QFileDialogOptions.FileDialogOption(int(self) ^ int(other))
                return NotImplemented
            def __rxor__(self, other: QFileDialogOptions.FileDialogOption | RealQFileDialog.Options | RealQFileDialog.Option | int) -> QFileDialogOptions.FileDialogOption:
                if isinstance(other, (QFileDialogOptions.FileDialogOption,
                                    RealQFileDialog.Options, RealQFileDialog.Option, int)):
                    return QFileDialogOptions.FileDialogOption(int(other) ^ int(self))
                return NotImplemented

    if not TYPE_CHECKING:
        FileMode = RealQFileDialog.Option.FileMode if hasattr(RealQFileDialog.Option, "FileMode") else RealQFileDialog.FileMode
        AcceptMode = RealQFileDialog.Option.AcceptMode if hasattr(RealQFileDialog.Option, "AcceptMode") else RealQFileDialog.AcceptMode
        DialogLabel = RealQFileDialog.Option.DialogLabel if hasattr(RealQFileDialog.Option, "DialogLabel") else RealQFileDialog.DialogLabel
        ViewMode = RealQFileDialog.Option.ViewMode if hasattr(RealQFileDialog.Option, "ViewMode") else RealQFileDialog.ViewMode
    else:
        class ViewMode(Enum, RealQFileDialog.ViewMode if TYPE_CHECKING else object):
            Detail = RealQFileDialog.ViewMode.Detail if hasattr(RealQFileDialog.ViewMode, "Detail") else RealQFileDialog.Detail
            List = RealQFileDialog.ViewMode.List if hasattr(RealQFileDialog.ViewMode, "List") else RealQFileDialog.List
        class FileMode(Enum, RealQFileDialog.FileMode if TYPE_CHECKING else object):
            AnyFile = RealQFileDialog.FileMode.AnyFile if hasattr(RealQFileDialog.FileMode, "AnyFile") else RealQFileDialog.AnyFile
            ExistingFile = RealQFileDialog.FileMode.ExistingFile if hasattr(RealQFileDialog.FileMode, "ExistingFile") else RealQFileDialog.ExistingFile
            Directory = RealQFileDialog.FileMode.Directory if hasattr(RealQFileDialog.FileMode, "Directory") else RealQFileDialog.Directory
            ExistingFiles = RealQFileDialog.FileMode.ExistingFiles if hasattr(RealQFileDialog.FileMode, "ExistingFiles") else RealQFileDialog.ExistingFiles
        class AcceptMode(Enum, RealQFileDialog.AcceptMode if TYPE_CHECKING else object):
            AcceptOpen = RealQFileDialog.AcceptMode.AcceptOpen if hasattr(RealQFileDialog.AcceptMode, "AcceptOpen") else RealQFileDialog.AcceptOpen
            AcceptSave = RealQFileDialog.AcceptMode.AcceptSave if hasattr(RealQFileDialog.AcceptMode, "AcceptSave") else RealQFileDialog.AcceptSave
        class DialogLabel(Enum, RealQFileDialog.DialogLabel if TYPE_CHECKING else object):
            LookIn = RealQFileDialog.DialogLabel.LookIn if hasattr(RealQFileDialog.DialogLabel, "LookIn") else RealQFileDialog.LookIn
            FileName = RealQFileDialog.DialogLabel.FileName if hasattr(RealQFileDialog.DialogLabel, "FileName") else RealQFileDialog.FileName
            FileType = RealQFileDialog.DialogLabel.FileType if hasattr(RealQFileDialog.DialogLabel, "FileType") else RealQFileDialog.FileType
            Accept = RealQFileDialog.DialogLabel.Accept if hasattr(RealQFileDialog.DialogLabel, "Accept") else RealQFileDialog.Accept
            Reject = RealQFileDialog.DialogLabel.Reject if hasattr(RealQFileDialog.DialogLabel, "Reject") else RealQFileDialog.Reject

    List = ViewMode.List
    Detail = ViewMode.Detail

    AnyFile = FileMode.AnyFile
    ExistingFile = FileMode.ExistingFile
    Directory = FileMode.Directory
    ExistingFiles = FileMode.ExistingFiles

    AcceptOpen = AcceptMode.AcceptOpen
    AcceptSave = AcceptMode.AcceptSave

    Accept = DialogLabel.Accept
    Reject = DialogLabel.Reject
    LookIn = DialogLabel.LookIn
    FileName = DialogLabel.FileName
    FileType = DialogLabel.FileType

    def __init__(self, f: FileDialogOption | RealQFileDialog.Options | RealQFileDialog.Option | int = 0):
        super().__init__()
        self._options: RealQFileDialog.Options = QFileDialogOptions.FileDialogOption(int(f))
        self._private: QFileDialogOptionsPrivate = QFileDialogOptionsPrivate()

    def viewMode(self) -> RealQFileDialog.ViewMode:
        d: QFileDialogOptionsPrivate = self._private
        return d.viewMode
    def setViewMode(self, mode: RealQFileDialog.ViewMode) -> None:
        d: QFileDialogOptionsPrivate = self._private
        d.viewMode = mode

    def fileMode(self) -> RealQFileDialog.FileMode:  # noqa: F811
        d: QFileDialogOptionsPrivate = self._private
        return d.fileMode
    def setFileMode(self, mode: RealQFileDialog.FileMode) -> None:  # noqa: F811
        d: QFileDialogOptionsPrivate = self._private
        d.fileMode = mode

    def acceptMode(self) -> RealQFileDialog.AcceptMode:  # noqa: F811
        d: QFileDialogOptionsPrivate = self._private
        return d.acceptMode
    def setAcceptMode(self, mode: RealQFileDialog.AcceptMode) -> None:  # noqa: F811
        d: QFileDialogOptionsPrivate = self._private
        d.acceptMode = mode

    def filter(self) -> QDir.Filter | QDir.Filters:
        d: QFileDialogOptionsPrivate = self._private
        return d.filter
    def setFilter(self, filter: QDir.Filter | QDir.Filters) -> None:  # noqa: A002
        d: QFileDialogOptionsPrivate = self._private
        d.filter |= filter

    def sidebarUrls(self) -> list[QUrl]:
        d: QFileDialogOptionsPrivate = self._private
        return d.sidebarUrls
    def setSidebarUrls(self, urls: list[QUrl]) -> None:
        d: QFileDialogOptionsPrivate = self._private
        d.sidebarUrls = urls


    def labelText(self, label: RealQFileDialog.DialogLabel) -> str:
        int_label = sip_enum_to_int(label)
        d: QFileDialogOptionsPrivate = self._private
        dialog_label_count = len(d.labelTexts)
        return d.labelTexts[RealQFileDialog.DialogLabel(int_label)] if int_label < dialog_label_count else ""
    def setLabelText(self, label: RealQFileDialog.DialogLabel, text: str) -> None:
        d: QFileDialogOptionsPrivate = self._private
        dialog_label_count = len(d.labelTexts)
        int_label = sip_enum_to_int(label)
        if int_label < dialog_label_count:
            d.labelTexts[RealQFileDialog.DialogLabel(int_label)] = text
    def isLabelExplicitlySet(self, label: RealQFileDialog.DialogLabel) -> bool:
        d: QFileDialogOptionsPrivate = self._private
        dialog_label_count = len(d.labelTexts)
        int_label = sip_enum_to_int(label)
        if int_label < dialog_label_count:
            return bool(d.labelTexts[label])
        return False

    def initialDirectory(self) -> QUrl:
        d: QFileDialogOptionsPrivate = self._private
        return d.initialDirectory
    def setInitialDirectory(self, directory: QUrl) -> None:
        d: QFileDialogOptionsPrivate = self._private
        d.initialDirectory = directory

    def initiallySelectedMimeTypeFilter(self) -> str:
        d: QFileDialogOptionsPrivate = self._private
        return d.initiallySelectedMimeTypeFilter
    def setInitiallySelectedMimeTypeFilter(self, filter: str) -> None:  # noqa: A002
        d: QFileDialogOptionsPrivate = self._private
        d.initiallySelectedMimeTypeFilter = filter

    def initiallySelectedNameFilter(self) -> str:
        d: QFileDialogOptionsPrivate = self._private
        return d.initiallySelectedNameFilter
    def setInitiallySelectedNameFilter(self, filter: str) -> None:  # noqa: A002
        d: QFileDialogOptionsPrivate = self._private
        d.initiallySelectedNameFilter = filter

    def initiallySelectedFiles(self) -> list[QUrl]:
        d: QFileDialogOptionsPrivate = self._private
        return d.initiallySelectedFiles
    def setInitiallySelectedFiles(self, files: list[QUrl]) -> None:
        d: QFileDialogOptionsPrivate = self._private
        d.initiallySelectedFiles = files

    def setSupportedSchemes(self, schemes: list[str]) -> None:
        d: QFileDialogOptionsPrivate = self._private
        d.supportedSchemes = schemes
    def supportedSchemes(self) -> list[str]:
        d: QFileDialogOptionsPrivate = self._private
        return d.supportedSchemes

    def useDefaultNameFilters(self) -> bool:
        """Since 5.7
        Internal.

        The bool property useDefaultNameFilters indicates that no name filters have been
        set or that they are equivalent to "All Files (*)". If it is true, the
        platform can choose to hide the filter combo box.

        See Also:
            defaultNameFilterString()
        """
        d: QFileDialogOptionsPrivate = self._private
        return d.useDefaultNameFilters
    def setUseDefaultNameFilters(self, dnf: bool) -> None:  # noqa: FBT001
        d: QFileDialogOptionsPrivate = self._private
        d.useDefaultNameFilters = dnf

    @staticmethod
    def defaultNameFilterString() -> str:
        r"""Since 5.6
        Internal.

        Return the translated default name filter string (\gui{All Files (*)}).

        See Also:
            defaultNameFilters(), nameFilters()
        """
        app = QApplication.instance()
        assert app is not None
        return app.tr("All Files (*)", "QFileDialog")

    def nameFilters(self) -> list[str]:
        d: QFileDialogOptionsPrivate = self._private
        return d.nameFilters
    def setNameFilters(self, filters: Iterable[str]) -> None:
        d: QFileDialogOptionsPrivate = self._private
        d.nameFilters = list(filters)

    def mimeTypeFilters(self) -> list[str]:
        d: QFileDialogOptionsPrivate = self._private
        return d.mimeTypeFilters
    def setMimeTypeFilters(self, filters: Iterable[str]) -> None:
        d: QFileDialogOptionsPrivate = self._private
        d.mimeTypeFilters = list(filters)

    def defaultSuffix(self) -> str:
        return self._private.defaultSuffix.lstrip(".")
    def setDefaultSuffix(self, suffix: str) -> None:
        d: QFileDialogOptionsPrivate = self._private
        d.defaultSuffix = suffix

    def history(self) -> list[str]:
        return self._private.history
    def setHistory(self, paths: list[str]) -> None:
        d: QFileDialogOptionsPrivate = self._private
        d.history = paths

    # not here in our version.
    #def setWindowTitle(self, title: str) -> None:
    #    ...
    #def windowTitle(self) -> str:
    #    ...

    def options(self) -> RealQFileDialog.Options:
        d: QFileDialogOptionsPrivate = self._private
        return d.options
    def setOption(self, option: QFileDialogOptions.FileDialogOption, on: bool = True) -> None:  # noqa: FBT001, FBT002
        previous_options = self.options()
        if (not bool(previous_options & option)) != (not on):
            self.setOptions(previous_options ^ option)
    def setOptions(self, options: RealQFileDialog.Options) -> None:
        d: QFileDialogOptionsPrivate = self._private
        d.options = options
    def testOption(self, option: RealQFileDialog.Option) -> bool:
        d: QFileDialogOptionsPrivate = self._private
        return bool(d.options & option)


class QFileDialog(RealQFileDialog if TYPE_CHECKING else QDialog):
    """Pure Python implementation of QFileDialog using qtpy as the abstraction layer."""

    # Public Signals
    fileSelected: ClassVar[Signal] = Signal(str)
    filterSelected: ClassVar[Signal] = Signal(str)
    filesSelected: ClassVar[Signal] = Signal(list)
    directoryEntered: ClassVar[Signal] = Signal(str)
    currentChanged: ClassVar[Signal] = Signal(str)
    urlSelected: ClassVar[Signal] = Signal(QUrl)
    urlsSelected: ClassVar[Signal] = Signal(list)
    currentUrlChanged: ClassVar[Signal] = Signal(QUrl)
    directoryUrlEntered: ClassVar[Signal] = Signal(QUrl)

    # Private Signals
    _q_pathChanged: ClassVar[Signal] = Signal(str)
    _q_navigateBackward: ClassVar[Signal] = Signal()
    _q_navigateForward: ClassVar[Signal] = Signal()
    _q_navigateToParent: ClassVar[Signal] = Signal()
    _q_createDirectory: ClassVar[Signal] = Signal()
    _q_showListView: ClassVar[Signal] = Signal()
    _q_showDetailsView: ClassVar[Signal] = Signal()
    _q_showContextMenu: ClassVar[Signal] = Signal(QPoint)
    _q_renameCurrent: ClassVar[Signal] = Signal()
    _q_deleteCurrent: ClassVar[Signal] = Signal()
    _q_showHidden: ClassVar[Signal] = Signal()
    _q_updateOkButton: ClassVar[Signal] = Signal()
    _q_currentChanged: ClassVar[Signal] = Signal(QModelIndex)
    _q_enterDirectory: ClassVar[Signal] = Signal(QModelIndex)
    _q_emitUrlSelected: ClassVar[Signal] = Signal(QUrl)
    _q_emitUrlsSelected: ClassVar[Signal] = Signal(list)
    _q_nativeCurrentChanged: ClassVar[Signal] = Signal(QUrl)
    _q_nativeEnterDirectory: ClassVar[Signal] = Signal(QUrl)
    _q_goToDirectory: ClassVar[Signal] = Signal(str)

    _q_useNameFilter: ClassVar[Signal] = Signal(str)
    _q_selectionChanged: ClassVar[Signal] = Signal()
    _q_goToUrl: ClassVar[Signal] = Signal(QUrl)
    _q_goHome: ClassVar[Signal] = Signal()
    _q_showHeader: ClassVar[Signal] = Signal(QAction)
    _q_autoCompleteFileName: ClassVar[Signal] = Signal(str)
    _q_rowsInserted: ClassVar[Signal] = Signal(QModelIndex)
    _q_fileRenamed: ClassVar[Signal] = Signal(str, str, str)

    # Type checking and enums
    class FileMode(RealQFileDialog.FileMode if TYPE_CHECKING else Enum):
        """Specifies the file mode of the dialog."""

        AnyFile = RealQFileDialog.FileMode.AnyFile if hasattr(RealQFileDialog.FileMode, "AnyFile") else RealQFileDialog.AnyFile
        ExistingFile = RealQFileDialog.FileMode.ExistingFile if hasattr(RealQFileDialog.FileMode, "ExistingFile") else RealQFileDialog.ExistingFile
        Directory = RealQFileDialog.FileMode.Directory if hasattr(RealQFileDialog.FileMode, "Directory") else RealQFileDialog.Directory
        ExistingFiles = RealQFileDialog.FileMode.ExistingFiles if hasattr(RealQFileDialog.FileMode, "ExistingFiles") else RealQFileDialog.ExistingFiles
        if hasattr(RealQFileDialog.FileMode, "DirectoryOnly") or hasattr(RealQFileDialog.FileMode, "DirectoryOnly"):
            DirectoryOnly = RealQFileDialog.FileMode.DirectoryOnly if hasattr(RealQFileDialog.FileMode, "DirectoryOnly") else RealQFileDialog.DirectoryOnly

    AnyFile = FileMode.AnyFile
    ExistingFile = FileMode.ExistingFile
    Directory = FileMode.Directory
    ExistingFiles = FileMode.ExistingFiles
    if hasattr(FileMode, "DirectoryOnly"):
        DirectoryOnly = FileMode.DirectoryOnly

    class DialogLabel(RealQFileDialog.DialogLabel if TYPE_CHECKING else Enum):
        """Specifies the label of the dialog."""

        LookIn = RealQFileDialog.DialogLabel.LookIn if hasattr(RealQFileDialog.DialogLabel, "LookIn") else RealQFileDialog.LookIn
        FileName = RealQFileDialog.DialogLabel.FileName if hasattr(RealQFileDialog.DialogLabel, "FileName") else RealQFileDialog.FileName
        FileType = RealQFileDialog.DialogLabel.FileType if hasattr(RealQFileDialog.DialogLabel, "FileType") else RealQFileDialog.FileType
        Accept = RealQFileDialog.DialogLabel.Accept if hasattr(RealQFileDialog.DialogLabel, "Accept") else RealQFileDialog.Accept
        Reject = RealQFileDialog.DialogLabel.Reject if hasattr(RealQFileDialog.DialogLabel, "Reject") else RealQFileDialog.Reject

    LookIn = DialogLabel.LookIn
    FileName = DialogLabel.FileName
    FileType = DialogLabel.FileType
    Accept = DialogLabel.Accept
    Reject = DialogLabel.Reject

    class AcceptMode(RealQFileDialog.AcceptMode if TYPE_CHECKING else Enum):
        """Specifies whether the dialog is for opening or saving files."""

        AcceptOpen = RealQFileDialog.AcceptMode.AcceptOpen if hasattr(RealQFileDialog.AcceptMode, "AcceptOpen") else RealQFileDialog.AcceptOpen
        AcceptSave = RealQFileDialog.AcceptMode.AcceptSave if hasattr(RealQFileDialog.AcceptMode, "AcceptSave") else RealQFileDialog.AcceptSave
    AcceptOpen = AcceptMode.AcceptOpen
    AcceptSave = AcceptMode.AcceptSave

    class ViewMode(RealQFileDialog.ViewMode if TYPE_CHECKING else Enum):  # noqa: D106
        Detail = RealQFileDialog.ViewMode.Detail if hasattr(RealQFileDialog.ViewMode, "Detail") else RealQFileDialog.Detail
        List = RealQFileDialog.ViewMode.List if hasattr(RealQFileDialog.ViewMode, "List") else RealQFileDialog.List
    List = ViewMode.List
    Detail = ViewMode.Detail

    Option = QFileDialogOptions.FileDialogOption if TYPE_CHECKING else RealQFileDialog.Option
    Options = QFileDialogOptions.FileDialogOption if TYPE_CHECKING else RealQFileDialog.Options
    DontUseNativeDialog = Option.DontUseNativeDialog
    ShowDirsOnly = Option.ShowDirsOnly
    DontResolveSymlinks = Option.DontResolveSymlinks
    DontUseCustomDirectoryIcons = Option.DontUseCustomDirectoryIcons
    DontConfirmOverwrite = Option.DontConfirmOverwrite
    HideNameFilterDetails = Option.HideNameFilterDetails


    # Initialization
    @overload
    def __init__(self, parent: QWidget | None = None, f: Qt.WindowType | None = None) -> None: ...
    @overload
    def __init__(self, parent: QWidget | None = None, caption: str | None = None, directory: str | None = None, filter: str | None = None) -> None: ...
    def __init__(  # pyright: ignore[reportInconsistentOverload]
        self,
        parent: QWidget | None = None,
        caption: str | Qt.WindowType | None = None,
        directory: str | None = None,
        filter: str | None = None,  # noqa: A002
        *,
        f: Qt.WindowFlags | Qt.WindowType | None = None,
    ):
        """Args:
        parent (QWidget | None, optional): The parent widget for the file dialog.
            If None, the file dialog will be a top-level window. Defaults to None.

        caption (str, optional): The title of the file dialog window.
            This text appears in the title bar of the dialog. Defaults to an empty string.

        directory (str, optional): The starting directory for the file dialog.
            This is the directory that will be displayed when the dialog opens.
            If empty, the current working directory is used. Defaults to an empty string.

        filter (str, optional): A string that specifies the file type filters.
            Format: "Description (*.extension1 *.extension2);;All Files (*)".
            Example: "Images (*.png *.xpm *.jpg);;Text files (*.txt);;XML files (*.xml)".
            Defaults to an empty string, which shows all files.

        f (Qt.WindowType | None, optional): Window flags for the file dialog.
            These flags control the window's appearance and behavior.
            If None, default flags are used. If 'caption' is not a string and 'f' is None,
            'caption' is used as window flags. Defaults to None.
        """
        if isinstance(caption, Qt.WindowType):
            f = caption
            caption = ""
        if isinstance(f, Qt.WindowType):
            super().__init__(parent, f)  # pyright: ignore[reportCallIssue, reportArgumentType]
        else:
            super().__init__(parent)
        self._private = QFileDialogPrivate(self)
        self._tempdir = tempfile.TemporaryDirectory(prefix="qfiledialog_", suffix="_temp")
        self._private.directory = directory or self._tempdir.name
        self._private.selection = ""
        self._private.mode = QFileDialog.FileMode.AnyFile if hasattr(QFileDialog.FileMode, "AnyFile") else QFileDialog.AnyFile
        self._private.options = QFileDialogOptions()
        self._private.setWindowTitle = caption or ""
        self._private.filter = filter or ""
        self.setFileMode(self._private.mode)
        self.setOptions(self.options())
        self.selectFile(self._private.selection)
        self._private.init(self)

    def __del__(self) -> None:
        self._tempdir.cleanup()

    # Directory operations
    from functools import singledispatchmethod

    def tr(self, string: str, *args, **kwargs) -> str:
        """FIXME: This is a stub. Actual translation is not implemented yet."""
        return string
        #return self.tr(context or "QFileDialog", string)

    def d_func(self) -> QFileDialogPrivate:
        return self._private

    @overload
    def setDirectory(self, directory: str) -> None: ...  # noqa: F811
    @overload
    def setDirectory(self, adirectory: QDir) -> None: ...
    @singledispatchmethod
    def setDirectory(self, *args, **kwargs) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        raise NotImplementedError(f"Unsupported args: {args!r} {kwargs!r}")
    @setDirectory.register
    def _(self, adirectory: QDir) -> None:
        self.setDirectory(adirectory.absolutePath())
    @setDirectory.register
    def _(self, directory: str) -> None:
        """Sets the file dialog's current directory.

        Note: On iOS, if you set directory to QStandardPaths::standardLocations(QStandardPaths::PicturesLocation).last(),
        a native image picker dialog will be used for accessing the user's photo album.
        The filename returned can be loaded using QFile and related APIs.
        For this to be enabled, the Info.plist assigned to QMAKE_INFO_PLIST in the
        project file must contain the key NSPhotoLibraryUsageDescription. See
        Info.plist documentation from Apple for more information regarding this key.
        This feature was added in Qt 5.5.
        """
        d: QFileDialogPrivate = self._private
        new_directory: str = directory
        # we remove .. and . from the given path if exist
        if directory:
            new_directory = QDir.cleanPath(directory)

        if directory and not new_directory:
            return

        new_dir_url: QUrl = QUrl.fromLocalFile(new_directory)
        d.setLastVisitedDirectory(new_dir_url)

        d.options.setInitialDirectory(QUrl.fromLocalFile(directory))
        if not d.usingWidgets():
            d.setDirectory_sys(new_dir_url)
            return
        if d.rootPath() == new_directory:
            return
        assert d.model is not None, f"{type(self).__name__}.setDirectory: No model setup."
        assert d.qFileDialogUi is not None, f"{type(self).__name__}.setDirectory: No UI setup."
        root: QModelIndex = d.model.setRootPath(new_directory)
        if not d.nativeDialogInUse:
            assert d.completer is not None, f"{type(self).__name__}.setDirectory: No completer setup."
            d.qFileDialogUi.newFolderButton.setEnabled(bool(d.model.flags(root) & Qt.ItemIsDropEnabled))
            if root != d.rootIndex():
                if directory.endswith("/"):
                    d.completer.setCompletionPrefix(new_directory)
                else:
                    d.completer.setCompletionPrefix(new_directory + "/")
                d.setRootIndex(root)
            d.qFileDialogUi.listView.selectionModel().clear()
    def directory(self) -> QDir:
        d = self._private
        if d.nativeDialogInUse:
            _dir = d.directory_sys().toLocalFile()
            return QDir(_dir if _dir else d.options.initialDirectory().toLocalFile())
        return QDir(d.rootPath())

    # File operations
    def selectFile(self, filename: str | None) -> None:
        """Selects the given filename in the file dialog.

        Args:
            filename (str): The filename to select.
        """
        d: QFileDialogPrivate = self._private
        if not filename:
            return

        if not d.usingWidgets():
            url = QUrl()
            if QFileInfo(filename).isRelative():
                url = d.options.initialDirectory()
                path = url.path()
                if not path.endswith("/"):
                    path += "/"
                url.setPath(path + filename)
            else:
                url = QUrl.fromLocalFile(filename)
            d.selectFile_sys(url)
            d.options.setInitiallySelectedFiles([url])
            return

        assert d.model is not None, f"{type(self).__name__}.selectFile: No model setup."
        assert d.qFileDialogUi is not None, f"{type(self).__name__}.selectFile: No UI setup."
        if not QDir.isRelativePath(filename):
            info = QFileInfo(filename)
            filenamePath = info.absoluteDir().path()
            if d.model.rootPath() != filenamePath:
                self.setDirectory(filenamePath)

        index = d.model.index(filename)
        d.qFileDialogUi.listView.selectionModel().clear()
        if not self.isVisible() or not d.lineEdit().hasFocus():
            d.lineEdit().setText(index.data() if index.isValid() else self.fileFromPath(d.rootPath(), filename))

    def selectedFiles(self) -> list[str]:
        d = self._private
        files: list[str] = []
        userSelectedFiles = d.userSelectedFiles()
        for file in userSelectedFiles:
            files.append(file.toLocalFile())
        if not files and d.usingWidgets():
            fm = self.fileMode()
            if fm != QFileDialog.FileMode.ExistingFile and fm != QFileDialog.FileMode.ExistingFiles:
                files.append(d.rootIndex().data(QFileSystemModel.FilePathRole))
        return files

    def fileFromPath(self, rootPath: str, path: str) -> str:  # noqa: N803
        if not QFileInfo(path).isAbsolute():
            return path
        if path.startswith(rootPath, 0 if os.name == "nt" else None):
            path = path[len(rootPath):]

        if not path:
            return path

        if path[0] == QDir.separator() or (os.name == "nt" and path[0] == "/"):
            path = path[1:]
        return path

    # Filter operations
    def setNameFilter(self, filter: str) -> None:  # noqa: A002
        self.setNameFilters(qt_make_filter_list(filter))
    def setNameFilters(self, filters: Iterable[str]) -> None:
        """Sets the filters used in the file dialog.

        Note that the filter *.*} is not portable, because the historical
        assumption that the file extension determines the file type is not
        consistent on every operating system. It is possible to have a file with no
        dot in its name (for example, Makefile). In a native Windows file
        dialog, *.* will match such files, while in other types of file dialogs
        it may not. So it is better to use * if you mean to select any file.

        setMimeTypeFilters() has the advantage of providing all possible name
        filters for each file type. For example, JPEG images have three possible
        extensions; if your application can open such files, selecting the
        image/jpeg mime type as a filter will allow you to open all of them.
        """
        d: QFileDialogPrivate = self._private
        cleaned_filters: list[str] = [fil.strip() for fil in filters]
        d.options.setNameFilters(cleaned_filters)

        if not d.usingWidgets():
            return

        assert d.qFileDialogUi is not None, f"{type(self).__name__}.setNameFilters: No UI setup."
        d.qFileDialogUi.fileTypeCombo.clear()
        if not cleaned_filters:
            return

        if self.testOption(QFileDialog.Option.HideNameFilterDetails):
            d.qFileDialogUi.fileTypeCombo.addItems(qt_strip_filters(cleaned_filters))
        else:
            d.qFileDialogUi.fileTypeCombo.addItems(cleaned_filters)

        d._q_useNameFilter(0)  # noqa: SLF001
    def nameFilters(self) -> list[str]:
        d: QFileDialogPrivate = self._private
        return d.options.nameFilters()

    def selectNameFilter(self, filter: str) -> None:  # noqa: A002
        d: QFileDialogPrivate = self._private
        d.selectNameFilter_sys(filter)
    def selectedNameFilter(self) -> str:
        return self._private.selectedNameFilter_sys()

    # Mode operations
    def setFileMode(self, mode: RealQFileDialog.FileMode) -> None:  # noqa: F811
        d: QFileDialogPrivate = self._private
        d.options.setFileMode(mode)
    def fileMode(self) -> RealQFileDialog.FileMode:
        d: QFileDialogPrivate = self._private
        return d.options.fileMode()

    def setAcceptMode(self, mode: RealQFileDialog.AcceptMode) -> None:
        """Sets the accept mode of the dialog.

        The action mode defines whether the dialog is for opening or saving files.

        By default, this property is set to AcceptOpen.

        Args:
            mode (RealQFileDialog.AcceptMode): The accept mode to set.
        """
        d: QFileDialogPrivate = self._private
        d.options.setAcceptMode(mode)
        # clear WA_DontShowOnScreen so that d->canBeNativeDialog() doesn't return false incorrectly
        self.setAttribute(Qt.WA_DontShowOnScreen, False)  # noqa: FBT003
        if not d.usingWidgets():
            return

        assert d.qFileDialogUi is not None, f"{type(self).__name__}.setAcceptMode: No UI setup."
        accept_open = sip_enum_to_int(RealQFileDialog.AcceptMode.AcceptOpen)
        accept_save = sip_enum_to_int(RealQFileDialog.AcceptMode.AcceptSave)
        accept_mode = sip_enum_to_int(mode)
        button = QDialogButtonBox.Open if accept_mode == accept_open else QDialogButtonBox.Save
        d.qFileDialogUi.buttonBox.setStandardButtons(button | QDialogButtonBox.StandardButton.Cancel)
        d.qFileDialogUi.buttonBox.button(button).setEnabled(False)
        d._q_updateOkButton()  # noqa: SLF001
        if accept_mode == accept_save:
            d.qFileDialogUi.lookInCombo.setEditable(False)
        d.retranslateWindowTitle()
    def acceptMode(self) -> RealQFileDialog.AcceptMode:
        d: QFileDialogPrivate = self._private
        return d.options.acceptMode()

    # Option operations
    def setOption(self, option: RealQFileDialog.Option, on: bool = True) -> None:  # noqa: FBT001, FBT002
        previous_options: RealQFileDialog.Option | RealQFileDialog.Options = self.options()
        if (not bool(previous_options & option)) != (not on):
            self.setOptions(previous_options ^ option)
    def testOption(self, option: RealQFileDialog.Option) -> bool:
        return bool(self.options() & option)
    def setOptions(self, options: RealQFileDialog.Options | RealQFileDialog.Option) -> None:
        d: QFileDialogPrivate = self._private
        parsed_options = sip_enum_to_int(options)
        cur_options = sip_enum_to_int(self.options())
        changed = bool(parsed_options ^ cur_options)
        if not changed:
            return

        d.options.setOptions(RealQFileDialog.Options(parsed_options))

        dont_use_native_dialog = sip_enum_to_int(RealQFileDialog.Option.DontUseNativeDialog)
        if bool(parsed_options & dont_use_native_dialog) and not d.usingWidgets():
            d.createWidgets()

        if d.usingWidgets():
            assert d.model is not None, f"{type(self).__name__}.setOptions: d.model is None"

            dont_resolve_symlinks = sip_enum_to_int(RealQFileDialog.Option.DontResolveSymlinks)
            if bool(changed & dont_resolve_symlinks):
                d.model.setResolveSymlinks(not bool(options & dont_resolve_symlinks))
            read_only = sip_enum_to_int(RealQFileDialog.Option.ReadOnly)
            if bool(changed & read_only):
                ro = bool(options & read_only)
                d.model.setReadOnly(ro)

                assert d.qFileDialogUi is not None, f"{type(self).__name__}.setOptions: No UI setup."
                d.qFileDialogUi.newFolderButton.setEnabled(not ro)
                d.renameAction.setEnabled(not ro)
                d.deleteAction.setEnabled(not ro)

            dont_use_custom_directory_icons = sip_enum_to_int(RealQFileDialog.Option.DontUseCustomDirectoryIcons)
            if bool(changed & dont_use_custom_directory_icons):
                provider_options = self.iconProvider().options()
                provider_options |= dont_use_custom_directory_icons
                self.iconProvider().setOptions(provider_options)

        hide_name_filter_details = sip_enum_to_int(RealQFileDialog.Option.HideNameFilterDetails)
        if bool(changed & hide_name_filter_details):
            self.setNameFilters(self._private.options.nameFilters())

        show_dirs_only = sip_enum_to_int(RealQFileDialog.Option.ShowDirsOnly)
        if bool(changed & show_dirs_only):
            fil = sip_enum_to_int(self.filter())
            fil_files = sip_enum_to_int(QDir.Filter.Files)
            result = (
                (fil & ~fil_files)
                if bool(parsed_options & show_dirs_only)
                else (fil | fil_files)
            )
            self.setFilter(QDir.Filter(result))

    def options(self) -> RealQFileDialog.Options:
        return self._private.options.options()

    # MIME type operations
    def selectedMimeTypeFilter(self) -> str:
        d: QFileDialogPrivate = self._private
        return d.selectedMimeTypeFilter_sys()
    def supportedSchemes(self) -> list[str]:
        d: QFileDialogPrivate = self._private
        return d.options.supportedSchemes()
    def setSupportedSchemes(self, schemes: Iterable[str | None]) -> None:
        d: QFileDialogPrivate = self._private
        d.options.setSupportedSchemes(schemes)

    # URL operations
    def selectedUrls(self) -> list[QUrl]:
        d: QFileDialogPrivate = self._private
        return d.selectedFiles_sys()
    def selectUrl(self, url: QUrl) -> None:
        d: QFileDialogPrivate = self._private
        d.selectFile_sys(url)

    def directoryUrl(self) -> QUrl:
        d: QFileDialogPrivate = self._private
        return d.directory_sys()
    def setDirectoryUrl(self, directory: QUrl) -> None:
        """Sets the file dialog's current directory url.

        Note: The non-native QFileDialog supports only local files.

        Note: On Windows, it is possible to pass URLs representing
        one of the 'virtual folders', such as "Computer" or "Network".
        This is done by passing a QUrl using the scheme 'clsid' followed
        by the CLSID value with the curly braces removed. For example the URL
        clsid:374DE290-123F-4565-9164-39C4925E467B denotes the download
        location. For a complete list of possible values, see the MSDN documentation on
        KNOWNFOLDERID.

        Args:
            directory (QUrl): The directory URL to set.
        """
        if not directory.isValid():
            return

        d: QFileDialogPrivate = self._private
        d.setLastVisitedDirectory(directory)
        d.options.setInitialDirectory(directory)

        if d.nativeDialogInUse:
            d.setDirectory_sys(directory)
        elif directory.isLocalFile():
            self.setDirectory(directory.toLocalFile())
        elif d.usingWidgets():
            RobustLogger().warning("Non-native QFileDialog supports only local files")

    # Visibility operations
    def setVisible(self, visible: bool) -> None:  # noqa: FBT001
        d: QFileDialogPrivate = self._private
        if d.canBeNativeDialog():
            d.setVisible_sys(visible)
        else:
            QDialog.setVisible(self, visible)

    def setConfirmOverwrite(self, confirm: bool) -> None:  # noqa: FBT001
        self.setOption(RealQFileDialog.Option.DontConfirmOverwrite, not confirm)

    def confirmOverwrite(self) -> bool:
        return not self.testOption(RealQFileDialog.Option.DontConfirmOverwrite)

    # Open operations
    @overload
    def open(self) -> None: ...
    @overload
    def open(self, slot: PYQT_SLOT) -> None: ...
    def open(self, slot: PYQT_SLOT | None = None) -> None:
        QDialog.open(self)
        if slot is None:
            return
        if isinstance(slot, Callable):
            slot()
            return
        slot.emit()

    def setFilter(self, filters: QDir.Filter | QDir.Filters) -> None:
        self._private.options.setFilter(filters)
    def filter(self) -> QDir.Filter | QDir.Filters:  # pyright: ignore[reportIncompatibleMethodOverride]
        d: QFileDialogPrivate = self._private
        return d.options.filter()

    def proxyModel(self) -> QAbstractProxyModel | None:  # pyright: ignore[reportIncompatibleMethodOverride]  stubs are wrong
        """Returns the proxy model used by the file dialog. By default, no proxy is set."""
        d: QFileDialogPrivate = self._private
        return d.proxyModel or None

    def setProxyModel(self, model: QAbstractProxyModel | None) -> None:
        """Sets the model for the views to the given proxyModel. This is useful if you
        want to modify the underlying model; for example, to add columns, filter
        data or add drives.

        Any existing proxy model will be removed, but not deleted. The file dialog
        will take ownership of the proxyModel.
        """
        d: QFileDialogPrivate = self._private
        if not d.usingWidgets():
            return
        if (not model and not d.proxyModel) or (model == d.proxyModel):
            return

        if not d.model:
            return

        idx = d.rootIndex()
        if d.proxyModel:
            d.proxyModel.rowsInserted.disconnect(d._q_rowsInserted)
        else:
            d.model.rowsInserted.disconnect(d._q_rowsInserted)

        assert d.qFileDialogUi is not None, f"{type(self)}.setProxyModel: No UI setup."
        if model is not None:
            model.setParent(self)
            d.proxyModel = model
            model.setSourceModel(d.model)
            d.qFileDialogUi.listView.setModel(d.proxyModel)
            d.qFileDialogUi.treeView.setModel(d.proxyModel)
            if d.completer:
                d.completer.setModel(d.proxyModel)
                d.completer.proxyModel = d.proxyModel
            d.proxyModel.rowsInserted.connect(d._q_rowsInserted)
        else:
            d.proxyModel = None
            d.qFileDialogUi.listView.setModel(d.model)
            d.qFileDialogUi.treeView.setModel(d.model)
            if d.completer:
                d.completer.setModel(d.model)
                d.completer.sourceModel = d.model
                d.completer.proxyModel = None
            d.model.rowsInserted.connect(d._q_rowsInserted)

        _selModel: QItemSelectionModel = d.qFileDialogUi.treeView.selectionModel()
        d.qFileDialogUi.treeView.setSelectionModel(d.qFileDialogUi.listView.selectionModel())

        d.setRootIndex(idx)

        # reconnect selection
        selections = d.qFileDialogUi.listView.selectionModel()
        selections.selectionChanged.connect(d._q_selectionChanged)
        selections.currentChanged.connect(d._q_currentChanged)

    # State operations
    def restoreState(self, state: QByteArray | bytes | bytearray) -> bool:
        if isinstance(state, (bytes, bytearray, memoryview)):
            state = QByteArray(state)
        d: QFileDialogPrivate = self._private
        stream = QDataStream(state)
        stream.setVersion(QDataStream.Qt_5_0)
        if stream.atEnd():
            return False
        history: list[str] = []
        currentDirectory = QUrl()
        viewMode = 0
        QFileDialogMagic = 0xBE

        marker = stream.readInt32()
        version = stream.readInt32()
        # the code below only supports versions 3 and 4
        if marker != QFileDialogMagic or (version not in (3, 4)):
            return False

        d.splitterState = QByteArray(stream.readBytes())
        sidebarUrls = stream.readQVariant()
        if sidebarUrls is not None:
            d.sidebarUrls = sidebarUrls
        history = stream.readQStringList()
        if version == 3:
            currentDirectoryString: bytes = stream.readString()
            currentDirectory: QUrl = QUrl.fromLocalFile(currentDirectoryString.decode())
        else:
            currentDirectory = stream.readQVariant()
        d.headerData = QByteArray(stream.readBytes())
        viewMode: int = stream.readInt32()

        self.setDirectoryUrl(currentDirectory if d.lastVisitedDir.isEmpty() else d.lastVisitedDir)
        viewModeInt = sip_enum_to_int(RealQFileDialog.ViewMode(viewMode))
        self.setViewMode(viewModeInt)  # pyright: ignore[reportArgumentType]

        if not d.usingWidgets():
            return True

        return d.restoreWidgetState(history, -1)
    def saveState(self) -> QByteArray:
        d: QFileDialogPrivate = self._private
        version = 4
        data = QByteArray()
        stream = QDataStream(data, QIODevice.WriteOnly)
        stream.setVersion(QDataStream.Qt_5_0)

        QFileDialogMagic = 0xBE
        stream.writeInt32(QFileDialogMagic)
        stream.writeInt32(version)
        if d.usingWidgets():
            assert d.qFileDialogUi is not None, f"{type(self)}.saveState: No UI setup."
            stream.writeQVariant(d.qFileDialogUi.splitter.saveState())
            stream.writeQVariant(d.qFileDialogUi.sidebar.urls())
        else:
            stream.writeQVariant(d.splitterState)
            stream.writeQVariant(d.sidebarUrls)
        stream.writeQVariant(self.history())
        stream.writeQVariant(self._private.lastVisitedDir)
        if d.usingWidgets():
            assert d.qFileDialogUi is not None, f"{type(self)}.saveState: No UI setup."
            stream.writeQVariant(d.qFileDialogUi.treeView.header().saveState())
        else:
            stream.writeQVariant(d.headerData)
        view_mode = sip_enum_to_int(self.viewMode())
        stream.writeInt32(view_mode)
        return data

    # Sidebar operations
    def sidebarUrls(self) -> list[QUrl]:
        d: QFileDialogPrivate = self._private
        return d.options.sidebarUrls()
    def setSidebarUrls(self, urls: Iterable[QUrl]) -> None:
        d: QFileDialogPrivate = self._private
        d.options.setSidebarUrls(list(urls))
        if d.usingWidgets():
            assert d.qFileDialogUi is not None, f"{type(self)}.setSidebarUrls: No UI setup."
            d.qFileDialogUi.sidebar.setUrls(list(urls))

    def setLastVisitedDirectory(self, url: QUrl) -> None:
        d: QFileDialogPrivate = self._private
        d.lastVisitedDir = url
    def lastVisitedDirectory(self) -> QUrl:
        d: QFileDialogPrivate = self._private
        return d.lastVisitedDir

    # Event handling
    def changeEvent(self, e: QEvent) -> None:
        if e.type() == QEvent.Type.LanguageChange:
            d: QFileDialogPrivate = self._private
            d.retranslateStrings()
        super().changeEvent(e)
    def accept(self) -> None:  # noqa: C901, PLR0911, PLR0912, PLR0915
        d: QFileDialogPrivate = self._private
        if not d.usingWidgets():
            urls: list[QUrl] = self.selectedUrls()
            if not urls:
                return
            d._q_emitUrlsSelected(urls)  # noqa: SLF001
            if len(urls) == 1:
                d._q_emitUrlSelected(urls[0])  # noqa: SLF001
            super().accept()
            return

        files: list[str] = self.selectedFiles()
        if not files:
            return

        lineEditText: str = d.lineEdit().text().strip()
        if lineEditText == "..":
            d._q_navigateToParent()  # noqa: SLF001
            d.lineEdit().selectAll()
            return

        file_mode: RealQFileDialog.FileMode | int = sip_enum_to_int(self.fileMode())
        if file_mode in (
            sip_enum_to_int(RealQFileDialog.FileMode.DirectoryOnly),
            sip_enum_to_int(RealQFileDialog.FileMode.Directory),
        ):
            fn = files[0]
            info = QFileInfo(fn)
            if not info.exists():
                info = QFileInfo(os.path.expandvars(fn))
            if not info.exists():
                d.itemNotFound(info.fileName(), file_mode)
                return

            if info.isDir():
                d.emitFilesSelected(files)
                super().accept()
            return

        if file_mode == sip_enum_to_int(RealQFileDialog.FileMode.AnyFile):
            fn: str = files[0]
            info = QFileInfo(fn)
            if info.isDir():
                self.setDirectory(info.absoluteFilePath())
                return

            if not info.exists():
                max_name_length = d.maxNameLength(info.path())
                if max_name_length >= 0 and len(info.fileName()) > max_name_length:
                    QMessageBox.warning(
                        self,
                        self.tr("The file name is too long.", "QFileDialog"),
                        self.tr("File name too long", "QFileDialog"),
                        QMessageBox.StandardButton.Ok,
                        QMessageBox.StandardButton.Cancel,
                    )
                    return

            if (
                not info.exists()
                or self.testOption(RealQFileDialog.Option.DontConfirmOverwrite)
                or sip_enum_to_int(self.acceptMode()) == sip_enum_to_int(RealQFileDialog.AcceptMode.AcceptOpen)
            ):
                d.emitFilesSelected([fn])
                super().accept()
            elif d.itemAlreadyExists(info.fileName()):
                d.emitFilesSelected([fn])
                super().accept()
            return

        if file_mode in (
            sip_enum_to_int(RealQFileDialog.FileMode.ExistingFile),
            sip_enum_to_int(RealQFileDialog.FileMode.ExistingFiles),
        ):
            for file in files:
                info = QFileInfo(file)
                if not info.exists():
                    info = QFileInfo(os.path.expandvars(file))
                if not info.exists():
                    d.itemNotFound(info.fileName(), file_mode)
                    return

                if info.isDir():
                    self.setDirectory(info.absoluteFilePath())
                    d.lineEdit().clear()
                    return
            d._q_emitUrlsSelected([QUrl.fromLocalFile(file) for file in files])  # noqa: SLF001
            super().accept()
            return

    def done(self, result: int) -> None:
        super().done(result)

    def mimeTypeFilters(self) -> list[str]:
        d: QFileDialogPrivate = self._private
        return d.options.mimeTypeFilters()
    def setMimeTypeFilters(self, filters: Iterable[str]) -> None:
        d: QFileDialogPrivate = self._private
        d.options.setMimeTypeFilters(filters)

    def labelText(self, label: RealQFileDialog.DialogLabel) -> str:  # noqa: PLR0911
        d: QFileDialogPrivate = self._private
        if not d.usingWidgets():
            return d.options.labelText(label)
        button: QPushButton | None
        look_in = sip_enum_to_int(RealQFileDialog.DialogLabel.LookIn)
        file_name = sip_enum_to_int(RealQFileDialog.DialogLabel.FileName)
        file_type = sip_enum_to_int(RealQFileDialog.DialogLabel.FileType)
        accept = sip_enum_to_int(RealQFileDialog.DialogLabel.Accept)
        reject = sip_enum_to_int(RealQFileDialog.DialogLabel.Reject)
        accept_mode = sip_enum_to_int(RealQFileDialog.AcceptMode.AcceptOpen)
        if label == look_in:
            assert d.qFileDialogUi is not None, f"{type(self)}.labelText: No UI setup."
            return d.qFileDialogUi.lookInLabel.text()
        if label == file_name:
            assert d.qFileDialogUi is not None, f"{type(self)}.labelText: No UI setup."
            return d.qFileDialogUi.fileNameLabel.text()
        if label == file_type:
            assert d.qFileDialogUi is not None, f"{type(self)}.labelText: No UI setup."
            return d.qFileDialogUi.fileTypeLabel.text()
        if label == accept:
            if self.acceptMode() == accept_mode:
                assert d.qFileDialogUi is not None, f"{type(self)}.labelText: No UI setup."
                button = d.qFileDialogUi.buttonBox.button(QDialogButtonBox.StandardButton.Open)
            else:
                assert d.qFileDialogUi is not None, f"{type(self)}.labelText: No UI setup."
                button = d.qFileDialogUi.buttonBox.button(QDialogButtonBox.StandardButton.Save)
            return button.text() if button else ""
        if label == reject:
            assert d.qFileDialogUi is not None, f"{type(self)}.labelText: No UI setup."
            button = d.qFileDialogUi.buttonBox.button(QDialogButtonBox.StandardButton.Cancel)
            return button.text() if button else ""
        return ""
    def setLabelText(self, label: RealQFileDialog.DialogLabel, text: str) -> None:
        d: QFileDialogPrivate = self._private
        d.options.setLabelText(label, text)
        d.setLabelTextControl(label, text)
    def iconProvider(self) -> QFileIconProvider:
        d: QFileDialogPrivate = self._private
        if not d.model:
            return QFileIconProvider()
        return d.model.iconProvider()
    def setIconProvider(self, provider: QFileIconProvider) -> None:
        d: QFileDialogPrivate = self._private
        if not d.model:
            return
        d.model.setIconProvider(provider)

    def itemDelegate(self) -> QAbstractItemDelegate:
        d: QFileDialogPrivate = self._private
        assert d.qFileDialogUi is not None, f"{type(self)}.itemDelegate: No UI setup."
        return d.qFileDialogUi.listView.itemDelegate()
    def setItemDelegate(self, delegate: QAbstractItemDelegate) -> None:
        d: QFileDialogPrivate = self._private
        assert d.qFileDialogUi is not None, f"{type(self)}.setItemDelegate: No UI setup."
        d.qFileDialogUi.listView.setItemDelegate(delegate)

    def history(self) -> list[str]:
        d: QFileDialogPrivate = self._private
        return d.options.history()
    def setHistory(self, paths: Iterable[str]) -> None:
        d: QFileDialogPrivate = self._private
        d.options.setHistory(list(paths))

    def defaultSuffix(self) -> str:
        d: QFileDialogPrivate = self._private
        return d.options.defaultSuffix()
    def setDefaultSuffix(self, suffix: str) -> None:
        d: QFileDialogPrivate = self._private
        d.options.setDefaultSuffix(suffix)

    def viewMode(self) -> RealQFileDialog.ViewMode:
        d: QFileDialogPrivate = self._private
        return d.options.viewMode()
    def setViewMode(self, mode: RealQFileDialog.ViewMode) -> None:
        d: QFileDialogPrivate = self._private
        old_mode = sip_enum_to_int(d.options.viewMode())
        d.options.setViewMode(mode)
        if d.usingWidgets():
            assert d.qFileDialogUi is not None, f"{type(self)}.setViewMode: No UI setup."

            mode_int = sip_enum_to_int(mode)
            list_view_mode = sip_enum_to_int(RealQFileDialog.ViewMode.List)
            is_list_mode = bool(mode_int == list_view_mode)
            d.qFileDialogUi.listModeButton.setDown(is_list_mode)
            d.qFileDialogUi.listView.setVisible(is_list_mode)

            tree_view_mode = sip_enum_to_int(RealQFileDialog.ViewMode.Detail)
            is_tree_mode = bool(mode_int == tree_view_mode)
            d.qFileDialogUi.detailModeButton.setDown(is_tree_mode)
            d.qFileDialogUi.treeView.setVisible(is_tree_mode)

    @classmethod
    def getOpenFileContent(cls, nameFilter: str, fileOpenCompleted: Callable[[str, bytes], None]) -> None:  # noqa: N803
        """A convenience class method that returns the content of a file selected by the user.

        This function is used to access local files on Qt for WebAssembly, where the web
        sandbox places restrictions on how such access may happen. Its implementation will
        make the browser display a native file dialog, where the user makes the file selection
        based on the parameter nameFilter.

        It can also be used on other platforms, where it will fall back to using QFileDialog.

        The function is asynchronous and returns immediately. The fileOpenCompleted
        callback will be called when a file has been selected and its contents have been
        read into memory.

        Example usage:
            def file_open_completed(file_name: str, file_content: bytes) -> None:
                print(f"File name: {file_name}")
                print(f"File content: {file_content}")

            QFileDialog.getOpenFileContent("Text files (*.txt)", file_open_completed)

        Args:
            nameFilter (str): The name filter for the file dialog.
            fileOpenCompleted (Callable[[str, bytes], None]): Callback function to be called
                when a file has been selected and its contents have been read.

        Returns:
            None
        """
        import sys

        if sys.platform == "emscripten":
            # WebAssembly implementation
            from qtpy.QtCore import QObject
            from qtpy.QtWebEngine import QWebEngineView

            class FileOpener(QObject):
                fileSelected = Signal(str, bytes)

                def __init__(self):
                    super().__init__()
                    self.web_view = QWebEngineView()
                    self.web_view.loadFinished.connect(self.handle_file_selection)

                def open_file(self):
                    self.web_view.load("about:blank")
                    self.web_view.page().runJavaScript(f"""
                        var input = document.createElement('input');
                        input.type = 'file';
                        input.accept = '{nameFilter}';
                        input.onchange = function(e) {{
                            var file = e.target.files[0];
                            var reader = new FileReader();
                            reader.onload = function(e) {{
                                var content = e.target.result;
                                window.fileContent = content;
                                window.fileName = file.name;
                            }};
                            reader.readAsArrayBuffer(file);
                        }};
                        input.click();
                    """)

                def handle_file_selection(self):
                    self.web_view.page().runJavaScript("""
                        [window.fileName, window.fileContent]
                    """, self.emit_file_selected)

                def emit_file_selected(self, result):
                    if result and result[0] and result[1]:
                        file_name, file_content = result
                        self.fileSelected.emit(file_name, bytes(file_content))
                    else:
                        self.fileSelected.emit("", b"")

            file_opener = FileOpener()
            file_opener.fileSelected.connect(fileOpenCompleted)
            file_opener.open_file()
        else:
            # Non-WebAssembly implementation
            dialog = cls()
            dialog.setFileMode(cls.FileMode.ExistingFile)
            dialog.setNameFilter(nameFilter)

            def file_selected(file_name: str) -> None:
                file_content: bytes = b""
                if file_name:
                    with open(file_name, "rb") as f:  # noqa: PTH123
                        file_content = f.read()
                fileOpenCompleted(file_name, file_content)

            dialog.fileSelected.connect(file_selected)
            dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
            dialog.show()

    @classmethod
    def saveFileContent(cls, fileContent: bytes, fileNameHint: str = "") -> None:  # noqa: N803
        """A convenience static method that saves fileContent to a file, using
        a file name and location chosen by the user.

        This method is used to save files to the local file system on Qt for WebAssembly,
        where the web sandbox places restrictions on how such access may happen.
        Its implementation will make the browser display a native file dialog,
        where the user makes the file selection.

        It can also be used on other platforms, where it will fall back to using QFileDialog.

        The method is asynchronous and returns immediately.

        Args:
            fileContent (bytes): The content to be saved to the file.
            fileNameHint (str): A suggested file name to the user. Defaults to an empty string.

        Example:
            QFileDialog.saveFileContent(b"Hello, World!", "example.txt")
        """
        if sys.platform == "wasm32-emscripten":
            # WebAssembly implementation
            try:
                from importlib.util import find_spec
                if find_spec("qtpy.QtWebEngineWidgets") is None:
                    raise ImportError("qtpy.QtWebEngineWidgets is required for WebAssembly support.")  # noqa: TRY301
                from qtpy.QtWebEngineWidgets import QWebEngineView
            except ImportError as e:
                raise ImportError("qtpy.QtWebEngineWidgets is required for WebAssembly support.") from e

            class FileSaver(QObject):
                def __init__(self, parent=None):
                    super().__init__(parent)
                    self.web_view = QWebEngineView()
                    self.web_view.setVisible(False)

                def save_file(self):
                    self.web_view.setHtml("")
                    self.web_view.page().runJavaScript(f"""
                        var a = document.createElement('a');
                        a.href = URL.createObjectURL(new Blob([{fileContent}]));
                        a.download = '{fileNameHint}';
                        a.click();
                        URL.revokeObjectURL(a.href);
                    """)

            file_saver = FileSaver()
            file_saver.save_file()
        else:
            # Non-WebAssembly implementation
            dialog = cls()
            dialog.setAcceptMode(cls.AcceptMode.AcceptSave)
            dialog.setFileMode(cls.FileMode.AnyFile)
            dialog.selectFile(fileNameHint)

            def file_selected(file_name: str) -> None:
                if file_name:
                    with open(file_name, "wb") as f:  # noqa: PTH123
                        f.write(fileContent)

            dialog.fileSelected.connect(file_selected)
            dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            dialog.show()


    @classmethod
    def getOpenFileName(  # noqa: PLR0913
        cls,
        parent: QWidget | None = None,
        caption: str = "",
        directory: str = "",
        filter: str = "",  # noqa: A002
        initialFilter: str = "",  # noqa: N803
        options: QFileDialog.Option = Option(0),  # noqa: A002, N803, B008
    ) -> tuple[str, str]:  # noqa: A002, N803
        dialog = cls(parent, caption, directory, filter)
        dialog.setOptions(options)
        dialog.setFileMode(cls.FileMode.ExistingFile)
        dialog.setAcceptMode(cls.AcceptMode.AcceptOpen)
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
        options: QFileDialog.Option = Option(0),  # noqa: B008
    ) -> tuple[list[str], str]:
        dialog = cls(parent, caption, directory, filter)
        dialog.setOptions(options)
        dialog.setFileMode(cls.FileMode.ExistingFiles)
        dialog.setAcceptMode(cls.AcceptMode.AcceptOpen)
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
        options: RealQFileDialog.Option | RealQFileDialog.Options = Option(0),  # noqa: B008
    ) -> tuple[str, str]:
        dialog = cls(parent, caption, directory, filter)
        dialog.setOptions(options)
        dialog.setFileMode(cls.FileMode.AnyFile)
        dialog.setAcceptMode(cls.AcceptMode.AcceptSave)
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
        options: RealQFileDialog.Option | RealQFileDialog.Options = Option(0),  # noqa: B008
    ) -> str:
        dialog = cls(parent, caption, directory)
        dialog.setOptions(options)
        dialog.setFileMode(cls.FileMode.Directory)
        dialog.setAcceptMode(cls.AcceptMode.AcceptOpen)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.selectedFiles()[0]
        return ""

    @classmethod
    def getExistingDirectoryUrl(
        cls,
        parent: QWidget | None = None,
        caption: str = "",
        directory: QUrl = QUrl(),  # noqa: B008
        options: RealQFileDialog.Option | RealQFileDialog.Options = Option(0),  # noqa: B008
        supportedSchemes: Iterable[str] = (),  # noqa: N803
    ) -> QUrl:
        dialog = cls(parent, caption)
        dialog.setOptions(options)
        dialog.setFileMode(cls.FileMode.Directory)
        dialog.setAcceptMode(cls.AcceptMode.AcceptOpen)
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
        options: RealQFileDialog.Option | RealQFileDialog.Options = Option(0),  # noqa: B008
        supportedSchemes: Iterable[str] = (),  # noqa: N803
    ) -> tuple[QUrl, str]:
        dialog = cls(parent, caption)
        dialog.setOptions(options)
        dialog.setFileMode(cls.FileMode.ExistingFile)
        dialog.setAcceptMode(cls.AcceptMode.AcceptOpen)
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
        options: RealQFileDialog.Option | RealQFileDialog.Options = Option(0),  # noqa: B008
        supportedSchemes: Iterable[str] = (),  # noqa: N803
    ) -> tuple[list[QUrl], str]:
        dialog = cls(parent, caption)
        dialog.setOptions(options)
        dialog.setFileMode(cls.FileMode.ExistingFiles)
        dialog.setAcceptMode(cls.AcceptMode.AcceptOpen)
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
        options: RealQFileDialog.Option | RealQFileDialog.Options = Option(0),  # noqa: B008
        supportedSchemes: Iterable[str] = (),  # noqa: N803
    ) -> tuple[QUrl, str]:
        dialog = cls(parent, caption)
        dialog.setOptions(options)
        dialog.setFileMode(cls.FileMode.AnyFile)
        dialog.setAcceptMode(cls.AcceptMode.AcceptSave)
        dialog.setDirectoryUrl(directory)
        dialog.setNameFilter(filter)
        dialog.setSupportedSchemes(supportedSchemes)
        if initialFilter:
            dialog.selectNameFilter(initialFilter)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.selectedUrls()[0], dialog.selectedNameFilter()
        return QUrl(), ""


if __name__ == "__main__":

    app = QApplication([])
    sys.excepthook = lambda exc, value, tb: RobustLogger().exception("Unhandled exception caught by sys.excepthook", exc_info=(exc, value, tb))
    dialog = QFileDialog()
    dialog.show()
    sys.exit(app.exec())

