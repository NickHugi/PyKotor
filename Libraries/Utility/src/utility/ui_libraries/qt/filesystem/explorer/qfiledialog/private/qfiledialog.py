from __future__ import annotations

import os
import sys

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, cast

import qtpy

from loggerplus import RobustLogger
from qtpy.QtCore import QByteArray, QDir, QFile, QFileInfo, QItemSelectionModel, QModelIndex, QPersistentModelIndex, QSettings, QSize, QUrl, Qt
from qtpy.QtGui import QFontMetrics, QKeyEvent, QKeySequence
from qtpy.QtWidgets import (
    QAction,
    QActionGroup,
    QApplication,
    QComboBox,
    QCompleter,
    QDialog,
    QDialogButtonBox,
    QFileDialog as RealQFileDialog,
    QFileIconProvider,
    QFileSystemModel,
    QHeaderView,
    QMenu,
    QMessageBox,
    QPushButton,
    QShortcut,
    QSizePolicy,
    QStyle,
    QWidget,
)

from utility.ui_libraries.qt.kernel.qplatformdialoghelper.qplatformdialoghelper import QPlatformFileDialogHelper
from utility.ui_libraries.qt.tests.test_enum_handling import sip_enum_to_int

if TYPE_CHECKING:
    from qtpy.QtCore import QAbstractItemModel, QAbstractProxyModel, QFileDevice, QObject, QPoint
    from qtpy.QtGui import QKeyEvent
    from qtpy.QtWidgets import QAbstractItemView, QHeaderView, QLineEdit, QPushButton
    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]

    from utility.ui_libraries.qt.filesystem.explorer.qfiledialog.private.ui_qfiledialog import Ui_QFileDialog
    from utility.ui_libraries.qt.filesystem.explorer.qfiledialog.qfiledialog import QFileDialog, QFileDialogOptions  # noqa: TCH004


def qt_make_filter_list(filter_arg: str) -> list[str]:
    if not filter_arg:
        return []
    sep: Literal[";;", "\n"] = ";;" if ";;" not in filter_arg and "\n" in filter_arg else "\n"
    return filter_arg.split(sep)


class QFileDialogOptionsPrivate:
    def __init__(self):
        # Prevent circular import
        self.viewMode: RealQFileDialog.ViewMode = RealQFileDialog.ViewMode.Detail
        self.fileMode: RealQFileDialog.FileMode = RealQFileDialog.FileMode.AnyFile
        self.acceptMode: RealQFileDialog.AcceptMode = RealQFileDialog.AcceptMode.AcceptOpen
        self.labelTexts: dict[RealQFileDialog.DialogLabel, str] = {}
        for label in (
            RealQFileDialog.DialogLabel.LookIn,
            RealQFileDialog.DialogLabel.FileName,
            RealQFileDialog.DialogLabel.FileType,
            RealQFileDialog.DialogLabel.Accept,
            RealQFileDialog.DialogLabel.Reject,
        ):
            self.labelTexts[label] = ""
        self.filter: QDir.Filter | QDir.Filters = (
            QDir.Filter.AllEntries
            | QDir.Filter.NoDotAndDotDot
            | QDir.Filter.AllDirs
        )
        self.sidebarUrls: list[QUrl] = []
        self.nameFilters: list[str] = []
        self.mimeTypeFilters: list[str] = []
        self.defaultSuffix: str = ""
        self.history: list[str] = []
        self.initialDirectory: QUrl = QUrl()
        self.initiallySelectedMimeTypeFilter: str = ""
        self.initiallySelectedNameFilter: str = ""
        self.initiallySelectedFiles: list[QUrl] = []
        self.supportedSchemes: list[str] = []
        self.useDefaultNameFilters: bool = True
        self.options: RealQFileDialog.Options = RealQFileDialog.Options(
            RealQFileDialog.Option.DontUseNativeDialog
            if hasattr(RealQFileDialog.Option, "DontUseNativeDialog")
            else RealQFileDialog.DontUseNativeDialog
        )
        self.sidebar_urls: list[QUrl] = []
        self.default_suffix: str = ""


class QFSCompleter(QCompleter):
    def __init__(self, fs_model: QFileSystemModel, parent: QObject | None = None):
        super().__init__(parent)
        self.sourceModel: QFileSystemModel = fs_model
        self.sourceModel.setRootPath("")
        self.proxyModel: QAbstractProxyModel | None = None
        self.setModel(self.sourceModel)
        self.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

    def pathFromIndex(self, index: QModelIndex) -> str:
        dirModel: QAbstractItemModel | QFileSystemModel = self.proxyModel.sourceModel() if self.proxyModel else self.sourceModel
        assert isinstance(dirModel, QFileSystemModel), f"{type(self).__name__}.pathFromIndex: Expected QFileSystemModel, got {type(dirModel).__name__}"
        current_location = Path(dirModel.rootPath().strip())
        path = os.path.abspath(os.path.normpath(str(index.data(QFileSystemModel.FilePathRole)).strip()))  # noqa: PTH100
        relative_path = os.path.relpath(path, str(current_location))
        return os.path.normpath(relative_path).strip()

    def splitPath(self, path: str) -> list[str]:
        return list(Path(self.qt_tildeExpansion(os.path.normpath(path.strip()))).absolute().parts)

    def setSourceModel(self, model: QFileSystemModel):
        self.sourceModel = model
        if not self.proxyModel:
            self.setModel(model)

    def setProxyModel(self, model: QAbstractProxyModel):
        self.proxyModel = model
        if model:
            model.setSourceModel(self.sourceModel)
            self.setModel(model)
        else:
            self.setModel(self.sourceModel)

    def qt_tildeExpansion(self, path: str) -> str:
        if path.startswith("~"):
            return os.path.expanduser(path)  # noqa: PTH111
        return path


@dataclass
class HistoryItem:
    """Represents an item in the file dialog history."""

    path: str
    selection: list[QPersistentModelIndex]


def _qt_get_directory(url: QUrl, local: QFileInfo) -> QUrl:
    if url.isLocalFile():
        info: QFileInfo = local
        if not local.isAbsolute():
            info = QFileInfo(QDir.current(), url.toLocalFile())
        path_info = QFileInfo(info.absolutePath())
        if not path_info.exists() or not path_info.isDir():
            return QUrl()
        if info.exists() and info.isDir():
            return QUrl.fromLocalFile(QDir.cleanPath(info.absoluteFilePath()))
        return QUrl.fromLocalFile(path_info.absoluteFilePath())
    return url


class QFileDialogPrivate:
    """Private implementation of QFileDialog."""

    def __init__(
        self,
        q: QFileDialog,
        *,
        selection: str | None = None,
        directory: QUrl | None = None,
        mode: RealQFileDialog.FileMode | None = None,
        filter: str | None = None,  # noqa: A002
        options: QFileDialogOptions | None = None,
        caption: str | None = None,
    ):
        """Initialize QFileDialogPrivate, calls _init_dialog_properties and _setup_dialog_components to setup the ui components."""
        self._public: QFileDialog = q
        self.nativeDialogInUse: bool = False
        self.platformHelper: QPlatformFileDialogHelper | None = None
        self.model: QFileSystemModel | None = None
        self.proxyModel: QAbstractProxyModel | None = None
        self.lastVisitedDir: QUrl = QUrl()
        self.currentHistoryLocation: int = -1
        self.currentHistory: list[HistoryItem] = []

        self.acceptLabel: str = "&Open"
        self.showActionGroup: QActionGroup = QActionGroup(q)
        self.renameAction: QAction = QAction("&Rename", q)
        self.deleteAction: QAction = QAction("&Delete", q)
        self.showHiddenAction: QAction = QAction("&Show Hidden", q)
        self.newFolderAction: QAction = QAction("&New Folder", q)

        self.completer: QFSCompleter | None = None
        self.useDefaultCaption: bool = True

        # Memory of what was read from QSettings in restoreState() in case widgets are not used
        self.splitterState: QByteArray = QByteArray()
        self.headerData: QByteArray = QByteArray()
        self.sidebarUrls: list[QUrl] = []
        self.defaultIconProvider: QFileIconProvider = QFileIconProvider()

        # QFileDialogArgs struct, used in some static methods of QFileDialog.
        from utility.ui_libraries.qt.filesystem.explorer.qfiledialog.qfiledialog import QFileDialogOptions

        self.options: QFileDialogOptions = QFileDialogOptions() if options is None else options
        self.filter: str = "" if filter is None else filter
        self.setWindowTitle: str = "" if caption is None else caption  # caption
        any_file = RealQFileDialog.FileMode.AnyFile if hasattr(RealQFileDialog.FileMode, "AnyFile") else RealQFileDialog.AnyFile
        self.mode: RealQFileDialog.FileMode = any_file if mode is None else mode
        self.options.setOption(QFileDialogOptions.FileDialogOption.DontUseNativeDialog, True)  # TODO: native dialog, disable for now.  # noqa: FBT003

        # init_directory
        self.directory: str = "" if directory is None else directory.toLocalFile()
        self.selection: str = "" if selection is None else selection

        self.qFileDialogUi: Ui_QFileDialog | None = None
        # from utility.ui_libraries.qt.filesystem.explorer.qfiledialog.private.ui_qfiledialog import Ui_QFileDialog
        # self.qFileDialogUi: Ui_QFileDialog = Ui_QFileDialog()
        # self.qFileDialogUi.setupUi(q)
        #self.init_directory(url=QUrl.fromLocalFile(self.directory))

    def init_directory(self, url: QUrl) -> None:
        """Initialize the directory and selection from the given URL.

        This is a QFileDialogArgs constructor in the Qt src.
        We handle slightly differently, e.g. they assign a method pointer to self.directory.
        """
        local: QFileInfo = QFileInfo(url.toLocalFile())
        # default case, re-use QFileInfo to avoid stat'ing
        if not url.isEmpty():
            self.directory = str(_qt_get_directory(url, local))
        # Get the initial directory URL
        if url.isEmpty():
            lastVisited: QUrl = self.lastVisitedDir
            if os.path.normpath(lastVisited.toLocalFile()).strip("\\").strip("/") != os.path.normpath(self.directory).strip("\\").strip("/"):
                self.directory = str(_qt_get_directory(lastVisited, local))
        # The initial directory can contain both the initial directory
        # and initial selection, e.g. /home/user/foo.txt
        if self.selection.strip() and not url.isEmpty():
            if url.isLocalFile():
                if not local.isDir():
                    self.selection = local.fileName()
            else:
                # With remote URLs we can only assume.
                self.selection = url.fileName()

    def init(self, q: QFileDialog) -> None:
        """Create widgets, layout and set default values.

        Updates attributes after construction, allowing us to start the dialog from any
        reused instance.

        This method sets up the file dialog based on the provided arguments,
        including setting the window title, file mode, name filter, directory,
        and selection. It also handles the display of the dialog and the use of
        native dialogs if available.
        """
        self._public = q
        if self.setWindowTitle.strip():  # if args.caption.isEmpty():
            self.useDefaultCaption = False
            q.setWindowTitle(self.setWindowTitle)

        q.setAcceptMode(RealQFileDialog.AcceptOpen)
        self.nativeDialogInUse = self.platformFileDialogHelper() is not None
        if not self.nativeDialogInUse:
            self.createWidgets()
        q.setFileMode(RealQFileDialog.AnyFile)
        if self.filter.strip():
            q.setNameFilter(self.filter)
        dirUrl = QUrl.fromLocalFile(self.directory)
        # QTBUG-70798, prevent the default blocking the restore logic.
        dontStoreDir = not dirUrl.isValid() and not self.lastVisitedDir.isValid()
        q.setDirectoryUrl(dirUrl)
        if dontStoreDir:
            self.lastVisitedDir.clear()
        if dirUrl.isLocalFile():
            q.selectFile(self.selection)
        else:
            q.selectUrl(dirUrl)

        q = self._public
        if hasattr(QSettings, "UserScope") or not self.restoreFromSettings():
            # Try to restore from the FileDialog settings group; if it fails, fall back
            # to the pre-5.5 QByteArray serialized settings.
            settings = QSettings(QSettings.Scope.UserScope, "QtProject")
            value = settings.value("Qt/filedialog_py", QByteArray())
            if isinstance(value, QByteArray):
                q.restoreState(value)
            else:
                RobustLogger().warning(f"{type(self).__name__}.init: Invalid value type for Qt/filedialog_py: {type(value).__name__}")

        if hasattr(Qt, "Q_EMBEDDED_SMALLSCREEN"):  # FIXME(th3w1zard1): incorrect check, look at docs later.
            assert self.qFileDialogUi is not None, "QFileDialogUi is None"
            self.qFileDialogUi.lookInLabel.setVisible(False)
            self.qFileDialogUi.fileNameLabel.setVisible(False)
            self.qFileDialogUi.fileTypeLabel.setVisible(False)
            self.qFileDialogUi.sidebar.hide()

        sizeHint = q.sizeHint()
        if sizeHint.isValid():
            q.resize(sizeHint)

    def createWidgets(self) -> None:
        """Initialize and configure all the UI components of the file dialog.
        This is essential for creating the visual interface of the dialog.

        If this function is removed, the dialog would lack its UI components,
        rendering it non-functional and unable to display any interface to the user.
        """
        if self.qFileDialogUi:
            return
        q = self._public

        # This function is sometimes called late (e.g as a fallback from setVisible). In that case we
        # need to ensure that the following UI code (setupUI in particular) doesn't reset any explicitly
        # set window state or geometry.
        self.preSize: QSize = q.size() if q.testAttribute(Qt.WidgetAttribute.WA_Resized) else QSize()
        self.preState: Qt.WindowStates = q.windowState()

        self.model = QFileSystemModel(q)
        self.model.setIconProvider(self.defaultIconProvider)
        self.model.setFilter(self.options.filter())
        self.model.setObjectName("qt_filesystem_model")
        if self.platformFileDialogHelper():
            self.model.setNameFilterDisables(self.platformFileDialogHelper().defaultNameFilterDisables())
        else:
            self.model.setNameFilterDisables(False)
        # self.model.d_func().disableRecursiveSort = True  # NOTE: This is QFileSystemModelPrivate::disableRecursiveSort
        self.model.fileRenamed.connect(self._q_fileRenamed)  # noqa: SLF001
        self.model.rootPathChanged.connect(self._q_pathChanged)  # noqa: SLF001
        self.model.rowsInserted.connect(self._q_rowsInserted)  # noqa: SLF001
        self.model.setReadOnly(False)

        # Initialize UI
        from utility.ui_libraries.qt.filesystem.explorer.qfiledialog.private.ui_qfiledialog import Ui_QFileDialog

        self.qFileDialogUi = Ui_QFileDialog()
        self.qFileDialogUi.setupUi(q)

        # Setup sidebar
        initialBookmarks: list[QUrl] = [QUrl("file:"), QUrl.fromLocalFile(QDir.homePath())]
        self.qFileDialogUi.sidebar.setModelAndUrls(self.model, initialBookmarks)
        self.qFileDialogUi.sidebar.goToUrl.connect(self._q_goToUrl)  # noqa: SLF001

        # Setup button box
        self.qFileDialogUi.buttonBox.accepted.connect(q.accept)
        self.qFileDialogUi.buttonBox.rejected.connect(q.reject)

        self.qFileDialogUi.lookInCombo.setFileDialogPrivate(self)
        self.qFileDialogUi.lookInCombo.textActivated.connect(self._q_goToDirectory)  # noqa: SLF001
        self.qFileDialogUi.lookInCombo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.qFileDialogUi.lookInCombo.setDuplicatesEnabled(False)

        # filename
        self.qFileDialogUi.fileNameEdit.setFileDialogPrivate(self)
        self.qFileDialogUi.fileNameLabel.setBuddy(self.qFileDialogUi.fileNameEdit)
        self.completer = QFSCompleter(self.model, q)
        self.qFileDialogUi.fileNameEdit.setCompleter(self.completer)

        self.qFileDialogUi.fileNameEdit.setInputMethodHints(Qt.InputMethodHint.ImhNoPredictiveText)
        self.qFileDialogUi.fileNameEdit.textChanged.connect(self._q_autoCompleteFileName)  # noqa: SLF001
        self.qFileDialogUi.fileNameEdit.textChanged.connect(self._q_updateOkButton)  # noqa: SLF001
        self.qFileDialogUi.fileNameEdit.returnPressed.connect(q.accept)

        # Setup file type combo
        self.qFileDialogUi.fileTypeCombo.setDuplicatesEnabled(False)
        self.qFileDialogUi.fileTypeCombo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContentsOnFirstShow)
        self.qFileDialogUi.fileTypeCombo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.qFileDialogUi.fileTypeCombo.activated.connect(self._q_useNameFilter)  # noqa: SLF001
        self.qFileDialogUi.fileTypeCombo.textActivated.connect(q.filterSelected)

        self.qFileDialogUi.listView.setFileDialogPrivate(self)
        self.qFileDialogUi.listView.setModel(self.model)
        self.qFileDialogUi.listView.activated.connect(self._q_enterDirectory)  # noqa: SLF001
        self.qFileDialogUi.listView.customContextMenuRequested.connect(self._q_showContextMenu)  # noqa: SLF001
        shortcut = QShortcut(QKeySequence.StandardKey.Delete, self.qFileDialogUi.listView)
        shortcut.activated.connect(self._q_deleteCurrent)  # noqa: SLF001

        self.qFileDialogUi.treeView.setFileDialogPrivate(self)
        self.qFileDialogUi.treeView.setModel(self.model)
        self.qFileDialogUi.treeView.setSelectionModel(self.qFileDialogUi.listView.selectionModel())
        self.qFileDialogUi.treeView.activated.connect(self._q_enterDirectory)  # noqa: SLF001
        self.qFileDialogUi.treeView.customContextMenuRequested.connect(self._q_showContextMenu)  # noqa: SLF001
        shortcut = QShortcut(QKeySequence.StandardKey.Delete, self.qFileDialogUi.treeView)
        shortcut.activated.connect(self._q_deleteCurrent)  # noqa: SLF001

        treeHeader: QHeaderView = self.qFileDialogUi.treeView.header()
        fm = QFontMetrics(q.font())
        treeHeader.resizeSection(0, fm.horizontalAdvance("wwwwwwwwwwwwwwwwwwwwwwwwww"))
        treeHeader.resizeSection(1, fm.horizontalAdvance("128.88 GB"))
        treeHeader.resizeSection(2, fm.horizontalAdvance("mp3Folder"))
        treeHeader.resizeSection(3, fm.horizontalAdvance("10/29/81 02:02PM"))
        treeHeader.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)

        # Setup show action group
        showActionGroup = QActionGroup(q)
        showActionGroup.setExclusive(False)
        showActionGroup.triggered.connect(self._q_showHeader)  # noqa: SLF001

        abstractModel = self.proxyModel if self.proxyModel else self.model
        for _ in range(1, abstractModel.columnCount(QModelIndex())):
            showHeader = QAction(showActionGroup)
            showHeader.setCheckable(True)
            showHeader.setChecked(True)
            treeHeader.addAction(showHeader)

        # Setup selection model
        selections = self.qFileDialogUi.listView.selectionModel()
        selections.selectionChanged.connect(self._q_selectionChanged)  # noqa: SLF001
        selections.currentChanged.connect(self._q_currentChanged)  # noqa: SLF001

        self.qFileDialogUi.splitter.setStretchFactor(self.qFileDialogUi.splitter.indexOf(self.qFileDialogUi.splitter.widget(1)), 1)

        self.createToolButtons()
        self.createMenuActions()

        # Restore settings
        if not self.restoreFromSettings():
            settings = QSettings(QSettings.Scope.UserScope, "QtProject")
            q.restoreState(settings.value("Qt/filedialog"))

        # Set initial widget states from options
        q.setFileMode(self.options.fileMode())
        q.setAcceptMode(self.options.acceptMode())
        q.setViewMode(self.options.viewMode())
        q.setOptions(int(self.options.options() if qtpy.API_NAME == "PyQt5" else self.options.options().value))  # pyright: ignore[reportAttributeAccessIssue]
        if self.options.sidebarUrls():
            q.setSidebarUrls(self.options.sidebarUrls())
        q.setDirectoryUrl(self.options.initialDirectory())
        if self.options.mimeTypeFilters():
            q.setMimeTypeFilters(self.options.mimeTypeFilters())
        elif self.options.nameFilters():
            q.setNameFilters(self.options.nameFilters())
        q.selectNameFilter(self.options.initiallySelectedNameFilter())
        q.setDefaultSuffix(self.options.defaultSuffix())
        q.setHistory(self.options.history())
        initiallySelectedFiles = self.options.initiallySelectedFiles()
        if len(initiallySelectedFiles) == 1:
            q.selectFile(initiallySelectedFiles[0].fileName())
        for url in initiallySelectedFiles:
            q.selectUrl(url)
        self.lineEdit().selectAll()
        self._q_updateOkButton()  # noqa: SLF001
        self.retranslateStrings()
        q.resize(self.preSize if self.preSize.isValid() else q.sizeHint())
        q.setWindowState(self.preState)

    def retranslateStrings(self) -> None:
        """Retranslate the UI, including all child widgets."""
        d: QFileDialogPrivate = self
        q: QFileDialog = self._public
        app = QApplication.instance()
        assert app is not None

        if d.options.useDefaultNameFilters():
            q.setNameFilter(self.options.defaultNameFilterString())
        if not d.usingWidgets():
            return

        assert d.qFileDialogUi is not None, f"{type(self)}.retranslateStrings: No UI setup."
        actions = d.qFileDialogUi.treeView.header().actions()
        abstractModel = d.model
        assert abstractModel is not None
        if d.proxyModel:
            abstractModel = d.proxyModel
        total = min(abstractModel.columnCount(QModelIndex()), len(actions) + 1)
        for i in range(1, total):
            actions[i - 1].setText(app.tr("Show ") + abstractModel.headerData(i, Qt.Horizontal, Qt.DisplayRole))

        # MENU ACTIONS
        d.renameAction.setText(app.tr("&Rename"))
        d.deleteAction.setText(app.tr("&Delete"))
        d.showHiddenAction.setText(app.tr("Show &hidden files"))
        d.newFolderAction.setText(app.tr("&New Folder"))
        d.qFileDialogUi.retranslateUi(q)
        d.updateLookInLabel()
        d.updateFileNameLabel()
        d.updateFileTypeLabel()
        d.updateCancelButtonText()

    def createToolButtons(self) -> None:
        assert self.qFileDialogUi is not None, "QFileDialogUi is None"
        q = self._public
        self.qFileDialogUi.backButton.setIcon(q.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack, None, q))
        self.qFileDialogUi.backButton.setAutoRaise(True)
        self.qFileDialogUi.backButton.setEnabled(False)
        self.qFileDialogUi.backButton.clicked.connect(self._q_navigateBackward)

        self.qFileDialogUi.forwardButton.setIcon(q.style().standardIcon(QStyle.StandardPixmap.SP_ArrowForward, None, q))
        self.qFileDialogUi.forwardButton.setAutoRaise(True)
        self.qFileDialogUi.forwardButton.setEnabled(False)
        self.qFileDialogUi.forwardButton.clicked.connect(self._q_navigateForward)

        self.qFileDialogUi.toParentButton.setIcon(q.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogToParent, None, q))
        self.qFileDialogUi.toParentButton.setAutoRaise(True)
        self.qFileDialogUi.toParentButton.setEnabled(False)
        self.qFileDialogUi.toParentButton.clicked.connect(self._q_navigateToParent)

        self.qFileDialogUi.listModeButton.setIcon(q.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogListView, None, q))
        self.qFileDialogUi.listModeButton.setAutoRaise(True)
        self.qFileDialogUi.listModeButton.setDown(True)
        self.qFileDialogUi.listModeButton.clicked.connect(self._q_showListView)

        self.qFileDialogUi.detailModeButton.setIcon(q.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView, None, q))
        self.qFileDialogUi.detailModeButton.setAutoRaise(True)
        self.qFileDialogUi.detailModeButton.clicked.connect(self._q_showDetailsView)

        toolSize = QSize(self.qFileDialogUi.fileNameEdit.sizeHint().height(), self.qFileDialogUi.fileNameEdit.sizeHint().height())
        self.qFileDialogUi.backButton.setFixedSize(toolSize)
        self.qFileDialogUi.listModeButton.setFixedSize(toolSize)
        self.qFileDialogUi.detailModeButton.setFixedSize(toolSize)
        self.qFileDialogUi.forwardButton.setFixedSize(toolSize)
        self.qFileDialogUi.toParentButton.setFixedSize(toolSize)

        self.qFileDialogUi.newFolderButton.setIcon(q.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder, None, q))
        self.qFileDialogUi.newFolderButton.setFixedSize(toolSize)
        self.qFileDialogUi.newFolderButton.setAutoRaise(True)
        self.qFileDialogUi.newFolderButton.setEnabled(False)
        self.qFileDialogUi.newFolderButton.clicked.connect(self._q_createDirectory)

    def createMenuActions(self) -> None:
        q = self._public

        goHomeAction = QAction(q)
        goHomeAction.setShortcut(QKeySequence(Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier | Qt.Key.Key_H))
        goHomeAction.triggered.connect(self._q_goHome)
        q.addAction(goHomeAction)

        goToParent = QAction(q)
        goToParent.setObjectName("qt_goto_parent_action")
        goToParent.setShortcut(QKeySequence(Qt.KeyboardModifier.ControlModifier | Qt.Key.Key_Up))
        goToParent.triggered.connect(self._q_navigateToParent)
        q.addAction(goToParent)

        self.renameAction = QAction(q)
        self.renameAction.setEnabled(False)
        self.renameAction.setObjectName("qt_rename_action")
        self.renameAction.triggered.connect(self._q_renameCurrent)

        self.deleteAction = QAction(q)
        self.deleteAction.setEnabled(False)
        self.deleteAction.setObjectName("qt_delete_action")
        self.deleteAction.triggered.connect(self._q_deleteCurrent)

        self.showHiddenAction = QAction(q)
        self.showHiddenAction.setObjectName("qt_show_hidden_action")
        self.showHiddenAction.setCheckable(True)
        self.showHiddenAction.triggered.connect(self._q_showHidden)

        self.newFolderAction = QAction(q)
        self.newFolderAction.setObjectName("qt_new_folder_action")
        self.newFolderAction.triggered.connect(self._q_createDirectory)

    def initHelper(self, h: QPlatformFileDialogHelper) -> None:
        """Initialize the platform file dialog helper.

        Connects signals from the helper to the appropriate slots in the file dialog.
        Ensures that the file dialog responds correctly to user interactions in the native dialog.

        If this function is removed, the file dialog would not respond to user actions in the native dialog,
        breaking the expected behavior of the file dialog.
        """
        q = self._public
        h.fileSelected.connect(self._q_emitUrlSelected)  # noqa: SLF001
        h.filesSelected.connect(self._q_emitUrlsSelected)  # noqa: SLF001
        h.currentChanged.connect(self._q_nativeCurrentChanged)  # noqa: SLF001
        h.directoryEntered.connect(self._q_nativeEnterDirectory)  # noqa: SLF001
        h.filterSelected.connect(q.filterSelected)
        # this will need to be fixed later
        # h.setOptions(self.options)  # TODO(th3w1zard1): implement the platform helpers.

    def q_func(self) -> QFileDialog:
        return self._public

    def helperPrepareShow(self, h: QPlatformFileDialogHelper) -> None:
        """Prepare the platform file dialog helper before showing the dialog.

        Sets up the initial state of the native dialog to match the current state of the QFileDialog.
        Ensures consistency between the Qt dialog and the native dialog.

        If this function is removed, the native dialog would not reflect the current state of the QFileDialog,
        leading to inconsistencies in the user interface.
        """
        q = self._public
        self.setWindowTitle = q.windowTitle()
        self.options.setHistory(q.history())
        if self.usingWidgets():
            self.options.setSidebarUrls(self.qFileDialogUi.sidebar.urls())
        if not self.options.initiallySelectedNameFilter():
            self.options.setInitiallySelectedNameFilter(q.selectedNameFilter())
        if not self.options.initiallySelectedFiles():
            self.options.setInitiallySelectedFiles(self.userSelectedFiles())

    def helperDone(self, code: QDialog.DialogCode, h: QPlatformFileDialogHelper) -> None:
        """Handle the completion of the native file dialog.

        Updates the QFileDialog state based on the result of the native dialog.
        Ensures that the QFileDialog reflects the user's actions in the native dialog.

        If this function is removed, changes made in the native dialog would not be
        reflected in the QFileDialog, leading to inconsistencies in the dialog's state.
        """
        if code == QDialog.DialogCode.Accepted:
            q = self._public
            q.setViewMode(RealQFileDialog.ViewMode(self.options.viewMode()))
            q.setSidebarUrls(self.options.sidebarUrls())
            q.setHistory(self.options.history())

    def _q_useNameFilter(self, index: int) -> None:
        """Sets the current name filter to be nameFilter and
        update the qFileDialogUi->fileNameEdit when in AcceptSave mode with the new extension.
        """
        assert self.qFileDialogUi is not None, f"{type(self).__name__}._q_useNameFilter: UI is None"
        nameFilters: list[str] = self.options.nameFilters()
        if index == len(nameFilters):
            comboModel = self.qFileDialogUi.fileTypeCombo.model()
            nameFilters.append(comboModel.index(comboModel.rowCount() - 1, 0).data())
            self.options.setNameFilters(nameFilters)

        nameFilter = nameFilters[index]
        newNameFilters = QPlatformFileDialogHelper.cleanFilterList(nameFilter)
        if sip_enum_to_int(self.q_func().acceptMode()) == sip_enum_to_int(RealQFileDialog.AcceptSave):
            newNameFilterExtension = ""
            if len(newNameFilters) > 0:
                newNameFilterExtension = QFileInfo(newNameFilters[0]).suffix()

            fileName = self.lineEdit().text()
            fileNameExtension = QFileInfo(fileName).suffix()
            if fileNameExtension and newNameFilterExtension:
                fileNameExtensionLength = len(fileNameExtension)
                fileName = fileName[:-fileNameExtensionLength] + newNameFilterExtension
                self.qFileDialogUi.listView.clearSelection()
                self.lineEdit().setText(fileName)

        assert self.model is not None, f"{type(self).__name__}._q_useNameFilter: model is None"
        self.model.setNameFilters(newNameFilters)

    def _q_goToDirectory(self, path: str) -> None:
        """Changes the file dialog's current directory to the one specified by path."""
        assert self.qFileDialogUi is not None, f"{type(self).__name__}._q_goToDirectory: UI is None"
        assert self.model is not None, f"{type(self).__name__}._q_goToDirectory: model is None"
        q = self._public
        url_role = Qt.UserRole + 1

        index: QModelIndex = self.qFileDialogUi.lookInCombo.model().index(
            self.qFileDialogUi.lookInCombo.currentIndex(),
            self.qFileDialogUi.lookInCombo.modelColumn(),
            self.qFileDialogUi.lookInCombo.rootModelIndex(),
        )

        path2 = path
        if not index.isValid():
            index = self.mapFromSource(self.model.index(os.path.expandvars(path)))
        else:
            path2 = index.data(url_role).toLocalFile()
            index = self.mapFromSource(self.model.index(path2))

        _dir = QDir(path2)
        if not _dir.exists():
            _dir.setPath(os.path.expandvars(path2))

        if _dir.exists() or not path2 or path2 == self.model.myComputer().toString():
            self._q_enterDirectory(index)
        else:
            message = q.tr(f"{path2}\nDirectory not found.\nPlease verify the correct directory name was given.")
            QMessageBox.warning(q, q.windowTitle(), message)

    def userSelectedFiles(self) -> list[QUrl]:
        """Get the list of files selected by the user.

        Retrieves the files selected by the user, either from the widget-based dialog or the system dialog.
        Crucial for returning the correct selection to the user of the QFileDialog.

        If this function is removed, the file dialog would not be able to return the user's file selection,
        breaking a core functionality of the file dialog.
        """
        files: list[QUrl] = []
        if not self.usingWidgets():
            return self.addDefaultSuffixToUrls(self.selectedFiles_sys())
        files = [QUrl.fromLocalFile(index.data(QFileSystemModel.FilePathRole)) for index in self.qFileDialogUi.listView.selectionModel().selectedRows()]
        if not files and self.lineEdit().text():
            files.extend([QUrl.fromLocalFile(path) for path in self.typedFiles()])
        return files

    def addDefaultSuffixToFiles(self, filesToFix: list[str]) -> list[str]:  # noqa: N803
        """Add the default suffix to files if necessary.

        Ensures that files without extensions get the default suffix added.
        This is important for maintaining consistent file naming conventions.
        """
        files: list[str] = []
        for name in filesToFix:
            newName = self.toInternal(name)
            defaultSuffix = self.options.defaultSuffix()
            if defaultSuffix.strip() and not os.path.isdir(newName) and "." not in os.path.basename(newName):  # noqa: PTH112, PTH119
                newName = os.path.splitext(newName)[0] + "." + defaultSuffix  # noqa: PTH122
            if os.path.isabs(newName):  # noqa: PTH117
                files.append(newName)
            else:
                path = os.path.join(self.rootPath(), newName)  # noqa: PTH118
                files.append(path)
        return files

    def addDefaultSuffixToUrls(self, urlsToFix: list[QUrl]) -> list[QUrl]:  # noqa: N803
        """Add the default suffix to URLs if necessary.

        Ensures that file URLs without extensions get the default suffix added.
        This is important for maintaining consistent file naming conventions when working with URLs.
        """
        urls: list[QUrl] = []
        defaultSuffix = self.options.defaultSuffix()
        for url in urlsToFix:
            if not defaultSuffix:
                urls.append(url)
                continue

            urlPath = url.path()
            if os.path.splitext(urlPath)[1] or os.path.isdir(urlPath):  # noqa: PTH112, PTH122
                urls.append(url)
                continue

            url.setPath(
                os.path.join(  # noqa: PTH118
                    os.path.dirname(urlPath),  # noqa: PTH120
                    os.path.basename(urlPath) + "." + defaultSuffix,  # noqa: PTH119
                )
            )
            urls.append(url)
        return urls

    def retranslateWindowTitle(self) -> None:
        """Update the window title based on the current dialog mode.

        Sets an appropriate title for the file dialog based on its current mode (Open, Save, Find Directory).
        This provides clear context to the user about the dialog's purpose.
        """
        q = self._public
        if not self.useDefaultCaption or self.setWindowTitle != q.windowTitle():
            return
        if q.acceptMode() == q.AcceptOpen:
            fileMode = q.fileMode()
            if fileMode == q.Directory:
                q.setWindowTitle(q.tr("Find Directory", "QFileDialog"))
            else:
                q.setWindowTitle(q.tr("Open", "QFileDialog"))
        else:
            q.setWindowTitle(q.tr("Save As", "QFileDialog"))
        self.setWindowTitle = q.windowTitle()

    def usingWidgets(self) -> bool:
        """Checks the Qt widget-based dialog is being used instead of the native dialog.

        This affects how various UI operations are handled.
        """
        return not self.nativeDialogInUse and self.qFileDialogUi is not None

    def rootIndex(self) -> QModelIndex:
        """Provides the root index of the current file system view.

        Crucial for correctly navigating and displaying the file system hierarchy.
        """
        view: QAbstractItemView | None = self.currentView()
        assert view is not None, f"{type(self).__name__}.rootIndex: No view found."
        return self.mapToSource(view.rootIndex())

    def setRootIndex(self, index: QModelIndex) -> None:
        """Updates the root index for both the tree and list views.

        Ensures that both views are synchronized and showing the same directory.

        If this function is removed, the tree and list views might become desynchronized,
        leading to inconsistent directory views and potential user confusion.
        """
        assert index.isValid() and index.model() == self.model, f"{type(self).__name__}.setRootIndex: Invalid index or model mismatch."
        idx = self.mapFromSource(index)
        assert self.qFileDialogUi is not None, f"{type(self).__name__}.setRootIndex: UI is None"
        self.qFileDialogUi.treeView.setRootIndex(idx)
        self.qFileDialogUi.listView.setRootIndex(idx)

    def currentView(self) -> QAbstractItemView | None:
        """Returns the currently active view (either list or tree view).

        This is essential for performing operations on the correct view based on the current UI state.
        """
        assert self.qFileDialogUi is not None, f"{type(self).__name__}.currentView: UI is None"
        assert self.qFileDialogUi.stackedWidget is not None, f"{type(self).__name__}.currentView: stackedWidget is None"
        if self.qFileDialogUi.stackedWidget.currentWidget() == self.qFileDialogUi.listView.parent():
            return self.qFileDialogUi.listView
        return self.qFileDialogUi.treeView

    def saveHistorySelection(self) -> None:
        """Preserves the current selection state in the history.

        Allows for restoring the selection when navigating back in history.

        If this function is removed, the dialog would lose the ability to remember selections
        when navigating through history, degrading the user experience.
        """
        if self.currentHistoryLocation < 0 or self.currentHistoryLocation >= len(self.currentHistory):
            RobustLogger().warning(f"{type(self).__name__}.saveHistorySelection: Invalid history location: {self.currentHistoryLocation}")
            return

        if self.qFileDialogUi is None or self.model is None:
            RobustLogger().warning(f"{type(self).__name__}.saveHistorySelection: UI or model is None")
            return

        item: HistoryItem = self.currentHistory[self.currentHistoryLocation]
        item.selection = []
        selectedIndexes: list[QModelIndex] = self.qFileDialogUi.listView.selectionModel().selectedRows()
        for i, index in enumerate(selectedIndexes):
            if not index.isValid():
                RobustLogger().warning(f"{type(self).__name__}.saveHistorySelection: Invalid index: {index} at index {i} in the selection model's rows list.")
                continue
            item.selection.append(QPersistentModelIndex(index))

    def _q_pathChanged(self, path: str) -> None:
        """Updates the UI and internal state when the current path changes.

        Ensures that the dialog reflects the new location correctly.

        If this function is removed, the dialog would not respond to path changes,
        leading to an inconsistent state between the actual location and what's displayed.
        """
        if self.qFileDialogUi is None or self.model is None:
            RobustLogger().warning(f"{type(self).__name__}._q_pathChanged: UI or model is None")
            return

        q = self._public
        self.qFileDialogUi.toParentButton.setEnabled(QFileInfo(self.model.rootPath()).exists())
        self.qFileDialogUi.sidebar.selectUrl(QUrl.fromLocalFile(path))
        q.setHistory(self.qFileDialogUi.lookInCombo.history())

        newNativePath = QDir.toNativeSeparators(path)
        if self.currentHistoryLocation < 0 or self.currentHistory[self.currentHistoryLocation].path != newNativePath:
            if self.currentHistoryLocation >= 0:
                self.saveHistorySelection()
            while self.currentHistoryLocation >= 0 and self.currentHistoryLocation + 1 < len(self.currentHistory):
                self.currentHistory.pop()
            self.currentHistory.append(HistoryItem(newNativePath, []))
            self.currentHistoryLocation += 1

        self.qFileDialogUi.forwardButton.setEnabled(len(self.currentHistory) - self.currentHistoryLocation > 1)
        self.qFileDialogUi.backButton.setEnabled(self.currentHistoryLocation > 0)

    def maxNameLength(self, path: str | None = None) -> int:
        """Determines the maximum allowed length for file names in the current file system.

        This is important for validating file names and preventing errors when creating or renaming files.
        """
        return int(os.environ.get("PC_NAME_MAX", 255))

    def emitFilesSelected(self, files: list[str]) -> None:
        """Notifies listeners about the files selected by the user.

        Crucial for the dialog to communicate its result to the calling code.

        If this function is removed, the dialog would not be able to inform the rest of the application
        about the user's file selection, breaking a core functionality of the file dialog.
        """
        q = self._public
        q.filesSelected.emit(files)
        if len(files) == 1:
            q.fileSelected.emit(files[0])

    def itemNotFound(self, fileName: str, mode: QFileDialog.FileMode) -> None:  # noqa: N803
        """Displays an appropriate error message when a requested file or directory is not found.

        This provides feedback to the user about why their action couldn't be completed.

        If this function is removed, the dialog would not inform users when they try to access
        non-existent files or directories, leading to confusion and a poor user experience.
        """
        q = self._public
        if mode == QFileDialog.FileMode.Directory:
            message = q.tr(f"{fileName}\nDirectory not found.\n" f"Please verify the correct directory name was given.", "QFileDialog")
        else:
            message = q.tr(f"{fileName}\nFile not found.\nPlease verify the " f"correct file name was given.", "QFileDialog")

        QMessageBox.warning(q, q.windowTitle(), message)

    def itemAlreadyExists(self, fileName: str) -> bool:  # noqa: N803
        """Prompts the user for confirmation when trying to overwrite an existing file.

        This prevents accidental data loss by overwriting files without user consent.
        """
        q = self._public
        msg: str = q.tr(f"{fileName} already exists.\nDo you want to replace it?", "QFileDialog")
        res: QMessageBox.StandardButton = QMessageBox.warning(q, q.windowTitle(), msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        return res == QMessageBox.StandardButton.Yes

    def _removeForwardHistory(self) -> None:
        """Clears the forward history when a new path is visited.

        Ensures that the history behaves like a typical browser history.

        If this function is removed, the history navigation would become inconsistent,
        with the forward history remaining even after visiting new locations.
        """
        while self.currentHistoryLocation >= 0 and self.currentHistoryLocation + 1 < len(self.currentHistory):
            self.currentHistory.pop()

    def _updateNavigationButtons(self) -> None:
        """Enables or disables the forward and back buttons based on the current history state.

        This provides visual feedback about the availability of history navigation.
        """
        assert self.qFileDialogUi is not None, f"{type(self).__name__}._updateNavigationButtons: No UI setup."
        self.qFileDialogUi.forwardButton.setEnabled(len(self.currentHistory) - self.currentHistoryLocation > 1)
        self.qFileDialogUi.backButton.setEnabled(self.currentHistoryLocation > 0)

    def _q_navigateBackward(self) -> None:
        """Implements the functionality for the back button.

        This allows users to return to previously visited directories.
        """
        if self.currentHistory and self.currentHistoryLocation > 0:
            self.saveHistorySelection()
            self.currentHistoryLocation -= 1
            self._navigateToHistoryItem(self.currentHistory[self.currentHistoryLocation])

    def _q_navigateForward(self) -> None:
        """Implements the functionality for the forward button.

        This allows users to move forward in the directory history after going back.
        """
        if self.currentHistory and self.currentHistoryLocation < len(self.currentHistory) - 1:
            self.saveHistorySelection()
            self.currentHistoryLocation += 1
            self._navigateToHistoryItem(self.currentHistory[self.currentHistoryLocation])

    def _navigateToHistoryItem(self, item: HistoryItem) -> None:
        """Restores the state of a previously visited directory, including selection.

        Ensures consistent behavior when navigating through history.
        """
        assert self.qFileDialogUi is not None, f"{type(self).__name__}._navigateToHistoryItem: No UI setup."
        q = self._public
        q.setDirectory(item.path)
        for i, persistent_index in enumerate(item.selection):
            if not persistent_index.isValid():
                RobustLogger().warning(f"{type(self).__name__}._navigateToHistoryItem: Invalid index: {persistent_index} at index {i} in the selection model's rows list.")
                continue
            # transform QPersistentModelIndex to QModelIndex
            index = persistent_index.model().index(
                persistent_index.row(),
                persistent_index.column(),
                persistent_index.parent(),
            )
            if index.isValid():
                self.qFileDialogUi.listView.selectionModel().select(index, QItemSelectionModel.Select)
            else:
                RobustLogger().warning(f"{type(self).__name__}._navigateToHistoryItem: Failed to create valid QModelIndex from persistent index.")

    def _q_navigateToParent(self) -> None:
        """Implements the functionality for the "Up" or "Parent Directory" button.

        This allows users to navigate up the directory hierarchy.
        """
        assert self.model is not None, f"{type(self).__name__}._q_navigateToParent: No file system model setup."

        q = self._public
        root_dir = QDir(self.model.rootDirectory())
        if root_dir.isRoot():
            newDirectory = cast(str, self.model.myComputer())
        else:
            root_dir.cdUp()
            newDirectory = root_dir.absolutePath()

        q.setDirectory(newDirectory)
        q.directoryEntered.emit(newDirectory)

    def _q_createDirectory(self) -> None:
        """Implements the functionality for creating a new folder in the current directory.

        This is a common operation in file dialogs, especially when saving files.
        """
        assert self.qFileDialogUi is not None, f"{type(self).__name__}._q_createDirectory: No UI setup."
        assert self.model is not None, f"{type(self).__name__}._q_createDirectory: No file system model setup."

        q = self._public
        self.qFileDialogUi.listView.clearSelection()

        newFolderString = q.tr("New Folder")
        folderName = newFolderString
        prefix = q.directory().absolutePath() + QDir.separator()
        if QFile.exists(prefix + folderName):
            suffix = 2
            while QFile.exists(prefix + folderName):
                folderName = newFolderString + str(suffix)
                suffix += 1

        parent = self.rootIndex()
        index = self.model.mkdir(parent, folderName)
        if not index.isValid():
            return

        index = self.select(index)
        if index.isValid():
            self.qFileDialogUi.treeView.setCurrentIndex(index)
            self.currentView().edit(index)

    def _q_showListView(self) -> None:
        """Changes the current view to list mode.

        This provides users with a different way to visualize the file system contents.

        If this function is removed, users would lose the ability to switch to list view,
        limiting the flexibility of the file dialog's interface.
        """
        assert self.qFileDialogUi is not None, f"{type(self).__name__}._q_showListView: No UI setup."
        self.qFileDialogUi.listModeButton.setDown(True)
        self.qFileDialogUi.detailModeButton.setDown(False)
        self.qFileDialogUi.treeView.hide()
        self.qFileDialogUi.listView.show()
        parent = self.qFileDialogUi.listView.parent()
        assert parent is self.qFileDialogUi.page, f"{type(self).__name__}._q_showListView: parent is not self.ui.page"
        self.qFileDialogUi.stackedWidget.setCurrentWidget(cast(QWidget, parent))
        q = self._public
        q.setViewMode(RealQFileDialog.ViewMode.List)

    def _q_showDetailsView(self) -> None:
        """Changes the current view to details mode.

        This provides users with a more detailed view of file system contents.

        If this function is removed, users would lose the ability to switch to details view,
        limiting the flexibility of the file dialog's interface.
        """
        self.qFileDialogUi.listModeButton.setDown(False)
        self.qFileDialogUi.detailModeButton.setDown(True)
        self.qFileDialogUi.listView.hide()
        self.qFileDialogUi.treeView.show()
        parent = self.qFileDialogUi.treeView.parent()
        assert parent is self.qFileDialogUi.page_2, f"{type(self).__name__}._q_showDetailsView: parent is not self.ui.page"
        self.qFileDialogUi.stackedWidget.setCurrentWidget(cast(QWidget, parent))
        q = self._public
        q.setViewMode(q.ViewMode.Detail)

    def _q_showContextMenu(self, position: QPoint) -> None:
        """Displays a context menu with relevant actions for the selected item.

        This provides quick access to common operations on files and directories.

        If this function is removed, users would lose access to context-specific actions,
        significantly reducing the functionality and usability of the file dialog.
        """
        assert self.qFileDialogUi is not None, f"{type(self).__name__}._q_showContextMenu: No UI setup."
        assert self.model is not None, f"{type(self).__name__}._q_showContextMenu: No file system model setup."

        view: QAbstractItemView | None = self.currentView()
        assert view is not None, f"{type(self).__name__}._q_showContextMenu: No view found."

        index = view.indexAt(position)
        index = self.mapToSource(index.sibling(index.row(), 0))

        menu = QMenu(view)
        menu.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        if index.isValid():
            self._add_file_context_menu_actions(menu, index)
        self._add_context_menu_view_actions(menu)
        menu.exec(view.viewport().mapToGlobal(position))

    def _add_file_context_menu_actions(self, menu: QMenu, index: QModelIndex) -> None:
        """Populates the context menu with actions specific to the selected file or directory.

        This provides quick access to common file operations.

        If this function is removed, the context menu would lack file-specific actions,
        reducing the functionality and convenience of the file dialog.
        """
        if self.model is None:
            RobustLogger().warning(f"{type(self).__name__}._add_file_context_menu_actions: No file system model setup.")
            return

        ro: bool = self.model.isReadOnly()
        p: QFileDevice.Permissions = self.model.fileInfo(index).permissions()

        if self.renameAction is not None:
            self.renameAction.setEnabled(not ro and bool(p & QFile.Permission.WriteUser))
            menu.addAction(self.renameAction)
        if self.deleteAction is not None:
            self.deleteAction.setEnabled(not ro and bool(p & QFile.Permission.WriteUser))
            menu.addAction(self.deleteAction)
        menu.addSeparator()

    def _add_context_menu_view_actions(self, menu: QMenu) -> None:
        """Adds general view-related actions to the context menu.

        This provides access to view options and other general operations.

        If this function is removed, the context menu would lack important general actions,
        limiting the user's ability to control the view and perform common operations.
        """
        if self.showHiddenAction is not None:
            menu.addAction(self.showHiddenAction)
        if self.newFolderAction is not None and self.qFileDialogUi.newFolderButton.isVisible():
            self.newFolderAction.setEnabled(self.qFileDialogUi.newFolderButton.isEnabled())
            menu.addAction(self.newFolderAction)

    def _q_renameCurrent(self) -> None:
        """Initiates the renaming process for the selected file or directory.

        This allows users to easily rename items directly from the file dialog.

        If this function is removed, users would lose the ability to rename files and directories
        from within the file dialog, reducing its functionality and convenience.
        """
        index = self.qFileDialogUi.listView.currentIndex()
        index = index.sibling(index.row(), 0)
        # index = self.mapToSource(index)
        view = self.currentView()
        assert view is not None, f"{type(self).__name__}._q_renameCurrent: No view found."
        view.edit(index)

    def removeDirectory(self, path: str) -> bool:
        """Removes the specified directory from the file system.

        This is a crucial operation for managing directories within the file dialog.

        If this function is removed, users would lose the ability to delete directories
        from within the file dialog, limiting its file management capabilities.
        """
        assert self.model is not None, f"{type(self).__name__}.removeDirectory: No file system model setup."
        modelIndex: QModelIndex = self.model.index(path)
        return self.model.remove(modelIndex)

    def _q_deleteCurrent(self) -> None:
        """Implements the functionality for deleting files or directories.

        This is a common file management operation that users expect in a file dialog.

        If this function is removed, users would lose the ability to delete files and directories
        from within the file dialog, significantly reducing its file management capabilities.
        """
        if self.qFileDialogUi is None or self.model is None or self.model.isReadOnly():
            return

        selectedRows: list[QModelIndex] = self.qFileDialogUi.listView.selectionModel().selectedRows()
        for index in reversed(selectedRows):
            self._delete_item(index)

    def _delete_item(self, index: QModelIndex) -> None:
        """Handles the actual deletion of a file or directory.

        This function encapsulates the logic for safely removing an item from the file system.
        """
        if not index.isValid() or index.parent() is None or index == self.qFileDialogUi.listView.rootIndex():
            RobustLogger().warning(f"{type(self).__name__}._delete_item: Invalid index: {index}.")
            return

        index = self.mapToSource(index.sibling(index.row(), 0))
        if not index.isValid():
            RobustLogger().warning(f"{type(self).__name__}._delete_item: Invalid index: {index}.")
            return

        assert self.model is not None, f"{type(self).__name__}._delete_item: No file system model setup."

        fileName = index.data(QFileSystemModel.Roles.FileNameRole)
        filePath = index.data(QFileSystemModel.Roles.FilePathRole)

        p: int | None = index.data(QFileSystemModel.Roles.FilePermissions)
        if not isinstance(p, int):
            raise TypeError(f"Invalid file permissions: {p!r}")

        if not bool(p & QFile.Permission.WriteUser) and self._write_protected_warning(fileName):
            return

        # the event loop has run, we have to validate if the index is valid because the model might have removed it.
        if not index.isValid() and self._confirm_deletion(fileName):
            return

        if self.model.isDir(index) and not self.model.fileInfo(index).isSymLink():
            if not self.removeDirectory(filePath):
                self._show_deletion_error()
            return
        self.model.remove(index)

    def _write_protected_warning(self, fileName: str) -> bool:  # noqa: N803
        """Warns the user when attempting to delete a write-protected file."""
        q = self._public
        result: QMessageBox.StandardButton = QMessageBox.warning(
            q,
            q.tr("Delete", "QFileDialog"),
            q.tr(f"'{fileName}' is write protected.\nDo you want to delete it anyway?", "QFileDialog"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return result == QMessageBox.StandardButton.Yes

    def _confirm_deletion(self, fileName: str) -> bool:  # noqa: N803
        """Asks for user confirmation before deleting a file or directory.

        This prevents accidental deletions and gives users a chance to reconsider their action.
        """
        q = self._public
        result: QMessageBox.StandardButton = QMessageBox.warning(
            q, q.tr("Delete", "QFileDialog"), q.tr(f"Are you sure you want to delete '{fileName}'?", "QFileDialog"), QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        return result == QMessageBox.StandardButton.Yes

    def _show_deletion_error(self) -> None:
        """Show an error message for failed deletion.

        Displays an error message when a directory deletion fails.
        This informs the user that the operation was unsuccessful and allows them to take appropriate action.
        """
        q = self._public
        QMessageBox.warning(q, q.windowTitle(), q.tr("Could not delete directory.", "QFileDialog"))

    def _q_autoCompleteFileName(self, text: str) -> None:
        """Auto-complete the file name.

        Provides auto-completion functionality for file names in the dialog.
        This improves user efficiency by suggesting matching file names as the user types.
        """
        assert self.model is not None, f"{type(self).__name__}._q_autoCompleteFileName: No file system model setup."
        assert self.qFileDialogUi is not None, f"{type(self).__name__}._q_autoCompleteFileName: No UI setup."
        if text.startswith(("//", "\\")):
            self.qFileDialogUi.listView.selectionModel().clearSelection()
            return

        multipleFiles: list[str] = self.typedFiles()
        if not multipleFiles:
            return
        oldFiles: list[QModelIndex] = self.qFileDialogUi.listView.selectionModel().selectedRows()
        newFiles: list[QModelIndex] = []
        for file in multipleFiles:
            idx = self.model.index(file)
            if idx not in oldFiles:
                newFiles.append(idx)
            else:
                oldFiles.remove(idx)
        for newFile in newFiles:
            self.select(newFile)
        if not self.lineEdit().hasFocus():
            return
        sm = self.qFileDialogUi.listView.selectionModel()
        for oldFile in oldFiles:
            sm.select(
                oldFile,
                QItemSelectionModel.Toggle | QItemSelectionModel.Rows,
            )

    def typedFiles(self) -> list[str]:
        """Returns the text in the line edit which can be one or more file names.

        Parses the user input in the file name field to extract file names.
        This is essential for handling user-typed file names, especially in save dialogs.
        """
        q = self._public
        files: list[str] = []
        editText: str = self.lineEdit().text().strip()
        if '"' not in editText:
            prefix = q.directory().absolutePath() + QDir.separator()
            if os.path.exists(os.path.join(prefix, editText)):  # noqa: PTH110, PTH118
                files.append(editText)
            else:
                files.append(self.qt_tildeExpansion(editText))
        else:
            # " is used to separate files like so: "file1" "file2" "file3" ...
            # ### need escape character for filenames with quotes (")
            tokens: list[str] = editText.split('"')
            for i in range(1, len(tokens), 2):  # Every even token is a separator
                token = tokens[i]
                prefix = q.directory().absolutePath()
                if os.path.exists(os.path.join(prefix, token)):  # noqa: PTH110, PTH118
                    files.append(token)
                else:
                    files.append(self.qt_tildeExpansion(token))
        return self.addDefaultSuffixToFiles(files)

    def qt_tildeExpansion(self, path: str) -> str:
        """Expand tilde in file paths.

        Expands the tilde (~) in file paths to the user's home directory on Unix-like systems.
        This allows users to use the tilde shorthand in file paths.
        """
        if os.name == "posix":
            return os.path.expanduser(path)  # noqa: PTH111
        return path

    def toInternal(self, path: str) -> str:
        """Convert file path to internal representation.

        Ensures consistent internal representation of file paths across different platforms.
        Crucial for maintaining cross-platform compatibility in file handling.
        """
        if os.name == "posix":
            return path.replace("\\", "/")
        return path

    def _q_updateOkButton(self) -> None:  # noqa: C901, PLR0912, PLR0915
        """Dynamically enables or disables the OK button based on the current selection and dialog mode.

        Ensures that the button is only active when a valid selection or input is present.
        """
        q = self._public
        assert self.qFileDialogUi is not None, f"{type(self).__name__}._q_updateOkButton: No UI setup."
        button: QPushButton | None = self.qFileDialogUi.buttonBox.button(
            QDialogButtonBox.Open
            if q.acceptMode() == sip_enum_to_int(RealQFileDialog.AcceptMode.AcceptOpen)
            else QDialogButtonBox.Save
        )
        if button is None:
            return
        fileMode: int = sip_enum_to_int(q.fileMode())

        enableButton: bool = True
        isOpenDirectory: bool = False

        files: list[str] = q.selectedFiles()
        lineEditText: str = self.lineEdit().text()

        if lineEditText.startswith(("//", "\\")):
            button.setEnabled(True)
            self.updateOkButtonText()
            return

        if not files:
            enableButton = False
        elif lineEditText == "..":
            isOpenDirectory = True
        elif fileMode == sip_enum_to_int(RealQFileDialog.FileMode.Directory):
            assert self.model is not None, f"{type(self).__name__}._q_updateOkButton: No file system model setup."
            fn: str = files[0]
            idx: QModelIndex = self.model.index(fn)
            if not idx.isValid():
                idx = self.model.index(os.path.expandvars(fn))
            if not idx.isValid() or not self.model.isDir(idx):
                enableButton = False
        elif fileMode == sip_enum_to_int(RealQFileDialog.FileMode.AnyFile):
            assert self.model is not None, f"{type(self).__name__}._q_updateOkButton: No file system model setup."
            fn: str = files[0]
            assert fn is not None, f"{type(self).__name__}._q_updateOkButton: File name is None."
            info = QFileInfo(fn)
            idx: QModelIndex = self.model.index(fn)
            fileDir: str = ""
            fileName: str = ""
            if info.isDir():
                fileDir = info.canonicalFilePath()
            else:
                fileDir = fn[: fn.rfind("/")]
                fileName = fn[len(fileDir) + 1 :]
            if ".." in lineEditText:
                fileDir = info.canonicalFilePath()
                fileName = info.fileName()

            if fileDir == q.directory().canonicalPath() and not fileName:
                enableButton = False
            elif idx.isValid() and self.model.isDir(idx):
                isOpenDirectory = True
                enableButton = True
            elif not idx.isValid():
                maxLength: int = self.maxNameLength(fileDir)
                enableButton = maxLength < 0 or len(fileName) <= maxLength
        elif fileMode in (sip_enum_to_int(RealQFileDialog.FileMode.ExistingFile), sip_enum_to_int(RealQFileDialog.FileMode.ExistingFiles)):
            assert self.model is not None, f"{type(self).__name__}._q_updateOkButton: No file system model setup."
            for file in files:
                idx: QModelIndex = self.model.index(file)
                if not idx.isValid():
                    idx = self.model.index(os.path.expandvars(file))
                if not idx.isValid():
                    enableButton = False
                    break
                if idx.isValid() and self.model.isDir(idx):
                    isOpenDirectory = True
                    break

        button.setEnabled(enableButton)
        self.updateOkButtonText(isOpenDirectory)

    def updateOkButtonText(self, saveAsOnFolder: bool = False) -> None:  # noqa: FBT002, FBT001, N803
        """Adjusts the text on the OK button based on the current dialog mode and selection.

        This provides clear context to the user about what action the button will perform.
        """
        q = self._public

        if saveAsOnFolder:
            self.setLabelTextControl(RealQFileDialog.DialogLabel.Accept, q.tr("&Open", "QFileDialog"))
        elif self.options.isLabelExplicitlySet(RealQFileDialog.DialogLabel.Accept):
            self.setLabelTextControl(
                RealQFileDialog.DialogLabel.Accept,
                self.options.labelText(RealQFileDialog.DialogLabel.Accept),
            )
            return
        elif sip_enum_to_int(q.fileMode()) == sip_enum_to_int(RealQFileDialog.FileMode.Directory):
            self.setLabelTextControl(RealQFileDialog.DialogLabel.Accept, q.tr("&Choose", "QFileDialog"))
        else:
            text = (
                q.tr("&Open", "QFileDialog")
                if sip_enum_to_int(q.acceptMode()) == sip_enum_to_int(RealQFileDialog.AcceptMode.AcceptOpen)
                else q.tr("&Save", "QFileDialog")
            )
            self.setLabelTextControl(RealQFileDialog.DialogLabel.Accept, text)

    def setLabelTextControl(self, label: RealQFileDialog.DialogLabel, text: str) -> None:
        """Updates the text of different UI elements in the file dialog.

        Allows for dynamic updating of labels based on the dialog's state or localization needs.
        """
        assert self.qFileDialogUi is not None, f"{type(self).__name__}.setLabelTextControl: No UI setup."
        int_label = sip_enum_to_int(label)
        if int_label == sip_enum_to_int(RealQFileDialog.DialogLabel.LookIn):
            self.qFileDialogUi.lookInLabel.setText(text)
        elif int_label == sip_enum_to_int(RealQFileDialog.DialogLabel.FileName):
            self.qFileDialogUi.fileNameLabel.setText(text)
        elif int_label == sip_enum_to_int(RealQFileDialog.DialogLabel.FileType):
            self.qFileDialogUi.fileTypeLabel.setText(text)
        elif int_label == sip_enum_to_int(RealQFileDialog.DialogLabel.Accept):
            q = self._public
            if q.acceptMode() == sip_enum_to_int(RealQFileDialog.AcceptMode.AcceptOpen):
                button: QPushButton = self.qFileDialogUi.buttonBox.button(QDialogButtonBox.Open)
            else:
                button = self.qFileDialogUi.buttonBox.button(QDialogButtonBox.Save)
            if button is not None:
                button.setText(text)
        elif int_label == sip_enum_to_int(RealQFileDialog.DialogLabel.Reject):
            button = self.qFileDialogUi.buttonBox.button(QDialogButtonBox.Cancel)
            if button is not None:
                button.setText(text)

    def _q_goToUrl(self, url: QUrl) -> None:
        """Navigate to the specified URL.

        Allows navigation to a specific URL in the file dialog.
        Crucial for enabling users to quickly jump to specific locations in the file system.

        If this function is removed, users would lose the ability to directly navigate to
        specific URLs, significantly hampering navigation capabilities in the file dialog.
        """
        assert self.qFileDialogUi is not None, f"{type(self.qFileDialogUi).__name__}._setupFileNameEdit: {type(self.qFileDialogUi).__name__} is None"
        assert self.model is not None, f"{type(self.qFileDialogUi).__name__}._setupFileNameEdit: {type(self.model).__name__} is None"
        local_path = url.toLocalFile()
        idx: QModelIndex = self.model.index(local_path)
        if not idx.isValid():
            RobustLogger().warning(f"{type(self).__name__}._q_goToUrl: Invalid index: {idx}.")
            return
        if idx.isValid():
            self._q_enterDirectory(idx)
            return

    def select(self, index: QModelIndex) -> QModelIndex:
        """Selects a specific item in the file dialog's list view.

        Crucial for programmatically selecting files or directories.

        If this function is removed, the dialog would lose the ability to programmatically
        select items, breaking functionality that relies on automatic selection.
        """
        assert self.model is not None, f"{type(self.qFileDialogUi).__name__}._setupFileNameEdit: {type(self.model).__name__} is None"
        assert self.qFileDialogUi is not None, f"{type(self.qFileDialogUi).__name__}._setupFileNameEdit: {type(self.qFileDialogUi).__name__} is None"
        idx = self.mapFromSource(index)
        if idx.isValid() and not self.qFileDialogUi.listView.selectionModel().isSelected(idx):
            self.qFileDialogUi.listView.selectionModel().select(idx, QItemSelectionModel.Select | QItemSelectionModel.Rows)
        return idx

    def _q_showHidden(self) -> None:
        """Toggles the visibility of hidden files and directories in the file dialog.

        This allows users to view or hide system and hidden files as needed.
        """
        q = self._public
        dirFilters = q.filter()
        dirFilters ^= sip_enum_to_int(QDir.Filter.Hidden)
        q.setFilter(dirFilters)

    def _q_rowsInserted(self, parent: QModelIndex) -> None:
        """Automatically selects the first item when new items are added to an empty view.

        This provides a default selection in cases where the view was previously empty.
        """
        assert self.qFileDialogUi is not None, f"{type(self).__name__}._q_rowsInserted: {type(self.qFileDialogUi).__name__} is None"
        if (
            not self.qFileDialogUi.treeView
            or parent != self.qFileDialogUi.treeView.rootIndex()
            or not self.qFileDialogUi.treeView.selectionModel()
            or self.qFileDialogUi.treeView.selectionModel().hasSelection()
            or self.qFileDialogUi.treeView.model().rowCount(parent) == 0
        ):
            return

        # Select the first row if conditions are met
        first_index = self.qFileDialogUi.treeView.model().index(0, 0, parent)
        if first_index.isValid():
            self.qFileDialogUi.treeView.selectionModel().select(first_index, QItemSelectionModel.SelectCurrent | QItemSelectionModel.Rows)

    def _q_fileRenamed(self, path: str, oldName: str, newName: str) -> None:  # noqa: N803
        """Updates the dialog's state when a file or directory is renamed.

        Ensures that the dialog reflects the current state of the file system accurately.

        If this function is removed, the dialog might display outdated information
        after file renames, leading to confusion and potential errors in file operations.
        """
        q = self._public
        fileMode = sip_enum_to_int(q.fileMode())
        if (
            fileMode == sip_enum_to_int(RealQFileDialog.FileMode.Directory)
            and path == self.rootPath()
            and self.lineEdit().text() == oldName
        ):
            self.lineEdit().setText(newName)

    def _q_emitUrlSelected(self, file: QUrl) -> None:
        """Notifies listeners about a selected URL and its corresponding local file path.

        Crucial for communicating the user's selection to the rest of the application.

        If this function is removed, the dialog would not properly notify the application
        about URL selections, breaking functionality that relies on these signals.
        """
        q = self._public
        q.urlSelected.emit(file)
        if file.isLocalFile():
            q.fileSelected.emit(file.toLocalFile())

    def _q_emitUrlsSelected(self, files: list[QUrl]) -> None:
        """Notifies listeners about multiple selected URLs and their corresponding local file paths.

        This is essential for communicating multiple selections to the rest of the application.

        If this function is removed, the dialog would not properly notify the application
        about multiple URL selections, breaking functionality that relies on these signals.
        """
        q = self._public
        q.urlsSelected.emit(files)
        localFiles: list[str] = [file.toLocalFile() for file in files if file.isLocalFile()]
        if localFiles:
            q.filesSelected.emit(localFiles)

    def _q_nativeCurrentChanged(self, file: QUrl) -> None:
        """Notifies listeners about changes in the current URL and file selection in native dialogs.

        Ensures that the application stays updated with the user's current selection in native dialogs.
        """
        q = self._public
        q.currentUrlChanged.emit(file)
        if file.isLocalFile():
            q.currentChanged.emit(file.toLocalFile())

    def _q_nativeEnterDirectory(self, directory: QUrl) -> None:
        """Notifies listeners when a new directory is entered in native dialogs.

        Crucial for updating the application's state to reflect the current directory in native dialogs.
        """
        q = self._public
        q.directoryUrlEntered.emit(directory)
        if directory:  # Windows native dialogs occasionally emit signals with empty strings.
            self.lastVisitedDir = directory
            if directory.isLocalFile():
                q.directoryEntered.emit(directory.toLocalFile())

    def canBeNativeDialog(self) -> bool:
        """Determines whether the current platform supports native file dialogs.

        This is important for deciding whether to use native dialogs or Qt-based dialogs.
        """
        return False  # TODO(th3w1zard1): Implement this

    def _q_currentChanged(self, index: QModelIndex) -> None:
        """Updates the dialog's state and emits signals when the current item changes.

        Ensures that the dialog and the application stay in sync with the user's current selection.
        """
        self._q_updateOkButton()
        self.q_func().currentChanged.emit(index.data(QFileSystemModel.Roles.FilePathRole))

    def _q_selectionChanged(self) -> None:
        """Handles the selection change event in the list view.

        This method is triggered when the selection changes in the list view.
        It updates the file list based on the current selection and updates the OK button state.
        """
        assert self.model is not None, f"{type(self).__name__}._q_selectionChanged: {type(self.model).__name__} is None"
        assert self.qFileDialogUi is not None, f"{type(self.qFileDialogUi).__name__}._q_selectionChanged: {type(self.qFileDialogUi).__name__} is None"
        q = self._public
        file_mode: int = sip_enum_to_int(q.fileMode())
        indexes: list[QModelIndex] = self.qFileDialogUi.listView.selectionModel().selectedRows()
        strip_dirs: bool = file_mode != sip_enum_to_int(RealQFileDialog.FileMode.Directory)

        all_files: list[str] = []
        for index in indexes:
            if strip_dirs and self.model.isDir(self.mapToSource(index)):
                continue
            all_files.append(index.data())

        if len(all_files) > 1:
            all_files = [f'"{f}"' for f in all_files]

        final_files = " ".join(all_files)
        if final_files and not self.lineEdit().hasFocus() and self.lineEdit().isVisible():
            self.lineEdit().setText(final_files)
        else:
            self._q_updateOkButton()

    def _q_enterDirectory(self, index: QModelIndex) -> None:
        """Handles the action of entering a selected directory.

        Crucial for navigating the file system hierarchy within the dialog.

        If this function is removed, users would lose the ability to navigate into directories
        by selecting them, significantly hampering the dialog's navigation capabilities.
        """
        if not index.isValid() or self.model is None:
            return

        q = self._public
        if self.model.isDir(index):
            assert self.qFileDialogUi is not None, f"{type(self).__name__}._q_enterDirectory: {type(self.qFileDialogUi).__name__} is None"
            self.qFileDialogUi.treeView.setCurrentIndex(index)
            filePath = self.model.filePath(index)
            q.setDirectory(filePath)
            q.directoryEntered.emit(filePath)
        else:
            self.accept()

    def _q_goHome(self) -> None:
        """Provides a quick way to navigate to the user's home directory.

        This is a common and expected feature in file dialogs for easy access to personal files.
        """
        q = self._public
        q.setDirectory(QDir.homePath())

    def _q_showHeader(self, action: QAction) -> None:
        """Toggles the visibility of specific columns in the details view.

        This allows users to customize the information displayed in the file dialog.

        If this function is removed, users would lose the ability to customize the
        visible columns in the details view, reducing the dialog's flexibility and usability.
        """
        if self.qFileDialogUi is None or self.showActionGroup is None:
            return

        actionGroup: QActionGroup = self.showActionGroup
        header: QHeaderView = self.qFileDialogUi.treeView.header()
        columnIndex = actionGroup.actions().index(action) + 1
        header.setSectionHidden(columnIndex, not action.isChecked())

    def setLastVisitedDirectory(self, dir: QUrl) -> None:  # noqa: F811, A002
        """Updates the record of the last directory visited by the user.

        This is important for maintaining navigation history and providing quick access to recent locations.
        """
        self.lastVisitedDir = dir

    def setVisible(self, visible: bool) -> None:  # noqa: FBT001
        """Internal method to handle visibility changes.

        The logic has to live here so that the call to hide() QDialog calls
        this function; it wouldn't call an override of QDialog::setVisible().
        """
        q = self._public
        if visible:
            if q.testAttribute(Qt.WidgetAttribute.WA_WState_ExplicitShowHide) and not q.testAttribute(Qt.WidgetAttribute.WA_WState_Hidden):
                return
        elif q.testAttribute(Qt.WidgetAttribute.WA_WState_ExplicitShowHide) and q.testAttribute(Qt.WidgetAttribute.WA_WState_Hidden):
            return

        if self.canBeNativeDialog():
            # NOTE: this is QDialogPrivate::setNativeDialogVisible(visible)!
            # Since we don't want to define
            # the entirety of QDialogPrivate (qfiledialogprivate was already too much),
            # the following line will be skipped.
            #
            # if self.setNativeDialogVisible(visible):
            #
            # Instead, the following line will be used:
            if self.options.testOption(RealQFileDialog.Option.DontUseNativeDialog):
                # Set WA_DontShowOnScreen so that QDialogPrivate::setVisible(visible) below
                # updates the state correctly, but skips showing the non-native version:
                q.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen)
                # So the completer doesn't try to complete and therefore show a popup
                if not self.nativeDialogInUse:
                    self.completer.setModel(None)
            else:
                self.createWidgets()
                q.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, False)  # noqa: FBT003
                if not self.nativeDialogInUse:
                    if self.proxyModel is not None:
                        self.completer.setModel(self.proxyModel)
                    else:
                        self.completer.setModel(self.model)

        if visible and self.usingWidgets():
            self.qFileDialogUi.fileNameEdit.setFocus()

        QDialog.setVisible(q, visible)  # NOTE: QDialogPrivate::setVisible(visible);

    def lineEdit(self) -> QLineEdit:
        """Provides access to the file name input field of the dialog.

        Crucial for operations involving direct file name input or manipulation.
        """
        if self.qFileDialogUi is None:
            raise RuntimeError("UI is not initialized")
        return self.qFileDialogUi.fileNameEdit

    def restoreFromSettings(self) -> bool:
        """Attempts to restore the dialog's state from previously saved settings.

        Helps maintain consistency in the dialog's appearance and behavior across sessions.
        """
        settings = QSettings(QSettings.Scope.UserScope, "QtProject")
        if "FileDialog" not in settings.childGroups():
            return False

        q = self._public
        settings.beginGroup("FileDialog")

        lastVisited = settings.value("lastVisited")
        if lastVisited:
            q.setDirectoryUrl(QUrl(lastVisited))

        viewMode = RealQFileDialog.ViewMode.Detail if settings.value("viewMode") == "Detail" else RealQFileDialog.ViewMode.List
        if sip_enum_to_int(viewMode):
            q.setViewMode(viewMode)

        self.sidebarUrls: list[QUrl] = [QUrl(url) for url in settings.value("shortcuts", [])]
        self.headerData = settings.value("treeViewHeader", QByteArray())

        history: list[str] = []
        urlStrings: list[str] = settings.value("history", [])
        for urlStr in urlStrings:
            url = QUrl(urlStr)
            if url.isLocalFile():
                history.append(url.toLocalFile())

        sidebarWidth: int = int(settings.value("sidebarWidth", -1))

        return self.restoreWidgetState(history, sidebarWidth)

    def saveSettings(self) -> None:
        """Saves the current state and configuration of the file dialog to persistent settings.

        Allows user preferences and configurations to be remembered across sessions.
        """
        q = self._public
        settings = QSettings(QSettings.Scope.UserScope, "QtProject")
        settings.beginGroup("FileDialog")

        if self.usingWidgets():
            settings.setValue("sidebarWidth", self.qFileDialogUi.splitter.sizes()[0])
            settings.setValue("shortcuts", [url.toString() for url in self.qFileDialogUi.sidebar.urls()])
            settings.setValue("treeViewHeader", self.qFileDialogUi.treeView.header().saveState())

        historyUrls: list[str] = [QUrl.fromLocalFile(path).toString() for path in q.history()]
        settings.setValue("history", historyUrls)
        settings.setValue("lastVisited", q.directoryUrl().toString())
        settings.setValue("viewMode", int(q.viewMode()))
        settings.setValue("qtVersion", qtpy.API_NAME)

    def restoreWidgetState(self, history: list[str], splitterPosition: int) -> bool:  # noqa: N803
        """Restores the state of various widgets in the file dialog, including splitter position and history.

        Ensures that the dialog's layout and navigation history are preserved across sessions.
        """
        if not self.usingWidgets() or self.qFileDialogUi is None:
            return False

        settings = QSettings(QSettings.Scope.UserScope, "QtProject")
        settings.beginGroup("FileDialog")

        self._restoreSplitterState(splitterPosition, settings)
        self._restoreSidebarUrls()
        self._restoreHistory(history)
        self._restoreHeaderState(settings)

        return True

    def _restoreSplitterState(self, splitterPosition: int, settings: QSettings) -> None:  # noqa: N803
        """Restores the position of the splitter in the file dialog.

        Ensures that the layout of the dialog is consistent with the user's previous session.
        """
        if splitterPosition >= 0:
            splitterSizes: list[int] = [
                splitterPosition,
                self.qFileDialogUi.splitter.widget(1).sizeHint().width(),
            ]
            self.qFileDialogUi.splitter.setSizes(splitterSizes)
            return

        # splitterPosition < 0
        splitterState: QByteArray = settings.value("splitterState", QByteArray())
        if not self.qFileDialogUi.splitter.restoreState(splitterState):
            sizes: list[int] = self.qFileDialogUi.splitter.sizes()
            if len(sizes) >= 2 and (sizes[0] == 0 or sizes[1] == 0):
                sizes: list[int] = [self.qFileDialogUi.splitter.widget(i).sizeHint().width() for i in range(len(sizes))]
                self.qFileDialogUi.splitter.setSizes(sizes)

    def _restoreSidebarUrls(self) -> None:
        """Restores the URLs in the sidebar of the file dialog, preserving custom sidebar shortcuts across sessions."""
        assert self.sidebarUrls is not None, f"{type(self)}.setUrls: URLs is None"
        self.qFileDialogUi.sidebar.setUrls(self.sidebarUrls)

    def _restoreHistory(self, history: list[str]) -> None:
        """Restores the navigation history of the file dialog, allowing users to quickly return to recently visited directories."""
        q = self._public
        MAX_HISTORY_SIZE = 5  # TODO: Make this configurable
        if len(history) > MAX_HISTORY_SIZE:
            history = history[-MAX_HISTORY_SIZE:]
        q.setHistory(history)

    def _restoreHeaderState(self, settings: QSettings) -> None:
        """Restores the state of the tree view header, including column visibility and sizes.

        Ensures that the user's preferred view settings are maintained across sessions.
        """
        headerView: QHeaderView = self.qFileDialogUi.treeView.header()
        if headerView is None or not headerView.restoreState(self.headerData):
            return

        actions: list[QAction] = headerView.actions()
        abstractModel: QAbstractProxyModel | QFileSystemModel | None = self.proxyModel if self.proxyModel is not None else self.model
        if abstractModel is None:
            return

        total: int = min(abstractModel.columnCount(), len(actions) + 1)
        for i in range(1, total):
            actions[i - 1].setChecked(not headerView.isSectionHidden(i))

    def mapToSource(self, index: QModelIndex) -> QModelIndex:
        """Translates an index from the proxy model to the source model.

        Crucial for correctly interpreting and manipulating model indices when a proxy model is in use.
        """
        return self.proxyModel.mapToSource(index) if self.proxyModel else index

    def mapFromSource(self, index: QModelIndex) -> QModelIndex:
        """Translates an index from the source model to the proxy model.
        This is essential for maintaining consistency when working with indices across different model layers.
        """
        return self.proxyModel.mapFromSource(index) if self.proxyModel else index

    def updateLookInLabel(self):
        if self.options.isLabelExplicitlySet(self.options.LookIn):
            self.setLabelTextControl(RealQFileDialog.LookIn, self.options.labelText(self.options.LookIn))

    def updateFileNameLabel(self):
        if self.options.isLabelExplicitlySet(self.options.FileName):
            self.setLabelTextControl(RealQFileDialog.FileName, self.options.labelText(self.options.FileName))
        else:
            q = self._public
            if sip_enum_to_int(q.fileMode()) == sip_enum_to_int(RealQFileDialog.FileMode.Directory):
                self.setLabelTextControl(RealQFileDialog.FileName, self.options.tr("Directory:"))
            else:
                self.setLabelTextControl(RealQFileDialog.FileName, self.options.tr("File &name:"))

    def updateFileTypeLabel(self):
        if self.options.isLabelExplicitlySet(self.options.FileType):
            self.setLabelTextControl(RealQFileDialog.FileType, self.options.labelText(self.options.FileType))

    def updateCancelButtonText(self):
        if self.options.isLabelExplicitlySet(self.options.Reject):
            self.setLabelTextControl(QFileDialog.Reject, self.options.labelText(self.options.Reject))

    def rootPath(self) -> str:
        """Retrieves the root path of the file system model.

        Crucial for understanding the current base directory of the file dialog.
        """
        return self.model.rootPath() if self.model else "/"

    def platformFileDialogHelper(self) -> QPlatformFileDialogHelper | None:
        """Provides access to the platform-specific file dialog helper.

        This is important for implementing platform-specific dialog behaviors.
        """
        return self.platformHelper or None

    def setDirectory_sys(self, directory: QUrl) -> None:
        """Sets the current directory for the system (native) file dialog.

        Ensures that the native dialog opens in the correct directory.

        If this function is removed, the native dialog might not open in
        the intended directory, causing inconsistency with the Qt-based dialog.
        """
        helper = self.platformFileDialogHelper()
        if helper and helper.isSupportedUrl(directory):
            helper.setDirectory(directory.toString())

    def directory_sys(self) -> QUrl:
        """Retrieves the current directory from the system (native) file dialog.

        This is important for maintaining consistency between Qt and native dialogs.

        If this function is removed, the Qt dialog might not be able to
        synchronize its directory with the native dialog, leading to inconsistencies.
        """
        helper = self.platformFileDialogHelper()
        return QUrl(helper.directory()) if helper else QUrl.fromLocalFile(self.directory)

    def selectFile_sys(self, filename: QUrl) -> None:
        """Selects a file in the system (native) file dialog.

        Ensures that file selections are properly handled in native dialogs.

        If this function is removed, file selections made programmatically
        might not be reflected in native dialogs, causing inconsistencies.
        """
        # helper = self.platformFileDialogHelper()
        # if helper and helper.isSupportedUrl(filename):
        #    helper.selectFile(filename)
        if self.model:
            file_path = filename.toLocalFile()
            index = self.model.index(file_path)
            if index.isValid():
                self.select(index)

    def selectedFiles_sys(self) -> list[QUrl]:
        """Retrieves the list of selected files from the system (native) file dialog.

        Crucial for obtaining the user's file selection from native dialogs.
        """
        # helper = self.platformFileDialogHelper()
        # return [QUrl(url) for url in helper.selectedFiles()] if helper else []
        curView: QAbstractItemView | None = self.currentView()
        if curView is None:
            return []
        return [QUrl.fromLocalFile(index.data(QFileSystemModel.Roles.FilePathRole)) for index in curView.selectedIndexes()]

    def setFilter_sys(self) -> None:
        """Sets the file filter for the system (native) file dialog.

        Ensures that file filtering is consistent between Qt and native dialogs.
        """
        helper = self.platformFileDialogHelper()
        if helper:
            helper.setFilter()

    def selectMimeTypeFilter_sys(self, filter: str) -> None:
        """Selects a MIME type filter in the system (native) file dialog.

        Allows for consistent MIME type filtering across Qt and native dialogs.
        """
        helper = self.platformFileDialogHelper()
        if helper:
            helper.selectMimeTypeFilter(filter)

    def selectedMimeTypeFilter_sys(self) -> str:
        """Retrieves the currently selected MIME type filter from the system (native) file dialog.

        Ensures consistency in MIME type filtering between Qt and native dialogs.
        """
        helper = self.platformFileDialogHelper()
        return helper.selectedMimeTypeFilter() if helper else ""

    def selectNameFilter_sys(self, filter: str) -> None:
        """Selects a name filter in the system (native) file dialog.

        Ensures that file name filtering is consistent between Qt and native dialogs.
        """
        helper = self.platformFileDialogHelper()
        if helper:
            helper.selectNameFilter(filter)

    def selectedNameFilter_sys(self) -> str:
        """Retrieves the currently selected name filter from the system (native) file dialog.

        Ensures consistency in name filtering between Qt and native dialogs.
        """
        helper = self.platformFileDialogHelper()
        return helper.selectedNameFilter() if helper else ""

    def setVisible_sys(self, visible: bool) -> None:
        """Sets the visibility of the system (native) file dialog.

        Ensures that the native dialog is visible or hidden as needed.
        """
        helper = self.platformFileDialogHelper()
        if helper:
            helper.setVisible(visible)

    def visible_sys(self) -> bool:
        """Retrieves the visibility of the system (native) file dialog.

        Crucial for determining if the native dialog is currently visible.
        """
        helper = self.platformFileDialogHelper()
        return helper.isVisible() if helper else False

    def getSelectedFiles(self) -> list[str]:
        """Retrieves the list of files currently selected in the file dialog.

        Crucial for obtaining the user's file selection from the dialog.
        """
        if self.qFileDialogUi is None or self.model is None:
            return []

        selected_indexes: list[QModelIndex] = self.qFileDialogUi.listView.selectedIndexes()
        return [self.model.filePath(index) for index in selected_indexes]

    def itemViewKeyboardEvent(self, e: QKeyEvent) -> bool:
        """Processes keyboard events in the item view of the file dialog.

        Allows for keyboard-based navigation and selection in the file list.
        """
        if e.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            self.accept()
            return True
        return False

    def accept(self) -> None:
        """Handles the acceptance of the file dialog, including different behaviors for open and save modes.

        Crucial for finalizing the user's file selection or save operation.
        """
        q = self._public
        if q.acceptMode() == q.AcceptMode.AcceptSave:
            q.accept()
            return
        # else:  # AcceptOpen
        selected_files: list[str] = self.getSelectedFiles()
        if selected_files:
            q.accept()
            return

        q.reject()


if __name__ == "__main__":
    from utility.ui_libraries.qt.filesystem.explorer.qfiledialog.qfiledialog import QFileDialog as CustomQFileDialog

    app = QApplication(sys.argv)
    dialog = CustomQFileDialog()
    dialog.show()
    sys.exit(app.exec())
