from __future__ import annotations

from enum import IntFlag
from typing import TYPE_CHECKING, cast

from PyQt6.QtCore import QItemSelectionModel
from PyQt6.QtGui import QAction, QActionGroup, QShortcut
from PyQt6.QtWidgets import QMessageBox
from qtpy.QtCore import (
    QAbstractListModel,
    QAbstractProxyModel,
    QByteArray,
    QDir,
    QFile,
    QFileInfo,
    QModelIndex,
    QPersistentModelIndex,
    QPoint,
    QRect,
    QSettings,
    QSize,
    QUrl,
    Qt,
    Slot,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import QFontMetrics, QKeyEvent, QKeySequence, QPaintEvent, QPainter, QStandardItemModel
from qtpy.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QCompleter,
    QDialogButtonBox,
    QFileSystemModel,
    QLineEdit,
    QListView,
    QMenu,
    QSizePolicy,
    QStyle,
    QStyleOptionComboBox,
    QTreeView,
)

from utility.ui_libraries.qt.filesystem.explorer.qfiledialogpy._ui_qfiledialog import Ui_QFileDialog
from utility.ui_libraries.qt.filesystem.explorer.qfiledialogpy.private.qfiledialog import QFileDialog

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QHeaderView, QPushButton
    from qtpy.QtCore import QAbstractProxyModel, QRect
    from qtpy.QtGui import QKeyEvent, QPaintEvent
    from qtpy.QtWidgets import QWidget

    from utility.ui_libraries.qt.filesystem.explorer.qfiledialogpy.private.qfiledialog import QFileDialogArgs


class QFileDialogOptions(IntFlag):
    ShowDirsOnly = 0x00000001
    DontResolveSymlinks = 0x00000002
    DontConfirmOverwrite = 0x00000004
    DontUseSheet = 0x00000008
    DontUseNativeDialog = 0x00000010
    ReadOnly = 0x00000020
    HideNameFilterDetails = 0x00000040
    DontUseCustomDirectoryIcons = 0x00000080

    def __init__(self, file_dialog: QFileDialog):
        self.sidebar_urls: list[QUrl] = []
        self.mime_type_filters: list[QDir.Filter | QDir.Filters] = []
        self.file_dialog: QFileDialog = file_dialog

    def setMimeTypeFilters(self, filters: list[str]):
        self.mime_type_filters = filters
        self.file_dialog._private.ui.fileTypeCombo.clear()
        self.file_dialog._private.ui.fileTypeCombo.addItems(self.mime_type_filters)
        self.file_dialog._private.ui.fileTypeCombo.currentTextChanged.emit(self.file_dialog._private.ui.fileTypeCombo.currentText())

    def setSidebarUrls(self, urls: list[QUrl]):
        self.sidebar_urls: list[QUrl] = urls
        self.file_dialog._private.ui.sidebar.setUrls(urls)

    def sidebarUrls(self) -> list[QUrl]:
        return self.sidebar_urls













class QtPyFSCompleter(QCompleter):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.fsModel = QFileSystemModel(self)
        self.fsModel.setRootPath("")
        self.setModel(self.fsModel)

        self.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        # Use forward slash as path separator for consistency across platforms
        self.fsModel.setNameFilterDisables(False)
        self.fsModel.setNameFilters(["*"])

    def pathFromIndex(self, index):

        path = self.fsModel.filePath(index)
        return QDir.toNativeSeparators(path)

    def splitPath(self, path):
        path = QDir.fromNativeSeparators(path)
        return path.split("/")


class QFileDialogPrivate:
    def __init__(self, q_ptr: QFileDialog):
        self._lastVisitedDir: QUrl = QUrl()
        self._public: QFileDialog = q_ptr
        self.model: QFileSystemModel | None = None
        self.proxyModel: QAbstractProxyModel | None = None
        self.currentHistoryLocation: int = -1
        self.useDefaultCaption: bool = True
        self.acceptLabel: str = QFileDialog.tr("&Open")
        self.options: QFileDialogOptions = QFileDialogOptions()
        self.currentHistory: list[dict[str, str]] = []

    def currentView(self) -> QAbstractItemView:
        return self.ui.stackedWidget.currentWidget()

    def q_func(self) -> QFileDialog:
        if self._public is None:
            raise RuntimeError("QFileDialogPrivate's q_ptr was not set")
        if not isinstance(self._public, QFileDialog):
            raise TypeError("QFileDialogPrivate's q_ptr is not a QFileDialog")
        return self._public

    def saveHistorySelection(self):
        self.currentHistory[self.currentHistoryLocation] = {"path": self.model.rootPath(), "selection": self._public.selectedFiles()}

    @Slot()

    def _q_pathChanged(self, path: str):
        self.ui.toParentButton.setEnabled(QDir(self.model.rootPath()).exists())
        self.ui.sidebar.selectUrl(QUrl.fromLocalFile(path))

        self.setHistory(self.ui.lookInCombo.history())

        newNativePath = QDir.toNativeSeparators(path)
        if self.currentHistoryLocation < 0 or self.currentHistory[self.currentHistoryLocation].path != newNativePath:
            if self.currentHistoryLocation >= 0:
                self.saveHistorySelection()
            while self.currentHistoryLocation >= 0 and self.currentHistoryLocation + 1 < len(self.currentHistory):
                self.currentHistory.pop()
            self.currentHistory.append({"path": newNativePath, "selection": []})
            self.currentHistoryLocation += 1

        self.ui.forwardButton.setEnabled(len(self.currentHistory) - self.currentHistoryLocation > 1)
        self.ui.backButton.setEnabled(self.currentHistoryLocation > 0)

    @Slot()
    def _q_navigateBackward(self):
        if self.currentHistory and self.currentHistoryLocation > 0:
            self.saveHistorySelection()
            self.currentHistoryLocation -= 1
            self.navigate(self.currentHistory[self.currentHistoryLocation])

    @Slot()
    def _q_navigateForward(self):
        if self.currentHistory and self.currentHistoryLocation < len(self.currentHistory) - 1:
            self.saveHistorySelection()
            self.currentHistoryLocation += 1
            self.navigate(self.currentHistory[self.currentHistoryLocation])

    @Slot()
    def _q_navigateToParent(self):
        dir = QDir(self.model.rootDirectory())
        if dir.isRoot():
            newDirectory = self.model.myComputer().toString()
        else:
            dir.cdUp()
            newDirectory = dir.absolutePath()
        self.setDirectory(newDirectory)
        self.directoryEntered.emit(newDirectory)

    @Slot()
    def _q_createDirectory(self):
        self.ui.listView.clearSelection()
        newFolderString = self.tr("New Folder")
        folderName = newFolderString
        prefix = self.directory().absolutePath() + QDir.separator()
        if QDir(prefix + folderName).exists():
            suffix = 2
            while QDir(prefix + folderName).exists():
                folderName = f"{newFolderString}{suffix}"
                suffix += 1

        parent: QModelIndex = self.currentView().rootIndex()
        index: QModelIndex = self.model.mkdir(parent, folderName)
        if index.isValid():
            index = self.select(index)
            if index.isValid():
                self.ui.treeView.setCurrentIndex(index)
                self.currentView().edit(index)

    @Slot()
    def _q_showListView(self):
        self.ui.listModeButton.setDown(True)
        self.ui.detailModeButton.setDown(False)
        self.ui.treeView.hide()
        self.ui.listView.show()
        assert self.ui.listView.parent() is self.ui.page
        self.ui.stackedWidget.setCurrentWidget(self.ui.listView.parent())

    @Slot()
    def _q_showDetailsView(self):
        self.ui.listModeButton.setDown(False)
        self.ui.detailModeButton.setDown(True)
        self.ui.listView.hide()
        self.ui.treeView.show()
        assert self.ui.treeView.parent() is self.ui.page_2
        self.ui.stackedWidget.setCurrentWidget(self.ui.treeView.parent())


    @Slot(QPoint)
    def _q_showContextMenu(self, position):
        view: QAbstractItemView = self.currentView()
        index: QModelIndex = view.indexAt(position)
        index = self.mapToSource(index.sibling(index.row(), 0))

        menu = QMenu(view)
        if index.isValid():
            ro: None | bool = self.model and self.model.isReadOnly()
            p: None | int = index.parent().data(QFileSystemModel.Roles.FilePermissions)
            self.renameAction.setEnabled(not ro and p & QFile.Permission.WriteUser)
            menu.addAction(self.renameAction)
            self.deleteAction.setEnabled(not ro and p & QFile.Permission.WriteUser)
            menu.addAction(self.deleteAction)
            menu.addSeparator()
        menu.addAction(self._public.showHiddenAction)
        if self.ui.newFolderButton.isVisible():
            self._public.newFolderAction.setEnabled(self.ui.newFolderButton.isEnabled())
            menu.addAction(self._public.newFolderAction)
        menu.exec(view.viewport().mapToGlobal(position))

    @Slot()
    def _q_renameCurrent(self):
        index: QModelIndex = self.ui.listView.currentIndex()
        index = index.sibling(index.row(), 0)
        self.currentView().edit(index)

    @Slot()
    def _q_deleteCurrent(self):
        if self.model.isReadOnly():
            return

        list = self.ui.listView.selectionModel().selectedRows()
        for i in range(list.count() - 1, -1, -1):
            index = QPersistentModelIndex(list[i])
            if index == self.ui.listView.rootIndex():
                continue

            index = self.mapToSource(index.sibling(index.row(), 0))
            if not index.isValid():
                continue

            fileName = index.data(QFileSystemModel.Roles.FileNameRole)
            filePath = index.data(QFileSystemModel.Roles.FilePathRole)

            p = index.parent().data(QFileSystemModel.Roles.FilePermissions)
            if not (p & QFile.Permission.WriteUser):
                # Show warning dialog
                q: QFileDialog = self.q_func()
                if (
                    QMessageBox.warning(
                        q,
                        q.tr("Delete"),
                        q.tr(f"'{fileName}' is write protected.\nDo you want to delete it anyway?"),
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No,

                    ) == QMessageBox.StandardButton.No
                ):
                    return

            if (
                QMessageBox.warning(
                    q,
                    q.tr("Delete"),
                    q.tr(f"Are you sure you want to delete '{fileName}'?"),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                ) == QMessageBox.StandardButton.No
            ):
                return


            # the event loop has run, we have to validate if the index is valid because the model might have removed it.
            if not index.isValid():
                return

            if self.model.isDir(index) and not self.model.fileInfo(index).isSymLink():
                if not self.removeDirectory(filePath):
                    QMessageBox.warning(
                        q,
                        q.windowTitle(),
                        q.tr("Could not delete directory."),
                    )

            else:
                self.model.remove(index)

    @Slot()
    def _q_showHidden(self):
        dirFilters: int = self.model.filter()
        dirFilters ^= QDir.Filter.Hidden
        self.model.setFilter(dirFilters)

    @Slot()
    def _q_updateOkButton(self):  # noqa: C901, PLR0912, PLR0915
        button: QPushButton | None = self.ui.buttonBox.button(
            QDialogButtonBox.StandardButton.Open
            if self._public.acceptMode() == QFileDialog.AcceptMode.AcceptOpen
            else QDialogButtonBox.StandardButton.Save
        )
        if not button:
            return

        fileMode: QFileDialog.FileMode = self._public.fileMode()
        enableButton: bool = True
        isOpenDirectory: bool = False

        files: list[str] = self._public.selectedFiles()
        lineEditText: str = self.ui.fileNameEdit.text()

        if lineEditText.startswith(("//", "\\")):

            button.setEnabled(True)
            self._public.updateOkButtonText()
            return

        if not files:
            enableButton = False
        elif lineEditText == "..":
            isOpenDirectory = True
        elif fileMode in (QFileDialog.Directory, QFileDialog.DirectoryOnly):
            fn = files[0]
            idx: QModelIndex = self.model.index(fn)
            if not idx.isValid():
                idx = self.model.index(self.getEnvironmentVariable(fn))
            if not idx.isValid() or not self.model.isDir(idx):
                enableButton = False
        elif fileMode == QFileDialog.FileMode.AnyFile:
            fn: str = files[0]
            info: QFileInfo = QFileInfo(fn)
            idx: QModelIndex = self.model.index(fn)
            fileDir: str = ""

            fileName: str = ""
            if info.isDir():
                fileDir = info.canonicalFilePath()
            else:
                fileDir = fn[:fn.rfind("/")]
                fileName = fn[len(fileDir)+1:]
            if ".." in lineEditText:
                fileDir = info.canonicalFilePath()
                fileName = info.fileName()

            if fileDir == self._public.directory().canonicalPath() and not fileName:
                enableButton = False
            elif idx.isValid() and self.model.isDir(idx):
                isOpenDirectory = True
                enableButton = True
            elif not idx.isValid():
                maxLength: int = self._public.maxNameLength(fileDir)
                enableButton = maxLength < 0 or len(fileName) <= maxLength
        elif fileMode in (QFileDialog.FileMode.ExistingFile, QFileDialog.FileMode.ExistingFiles):

            for file in files:
                idx: QModelIndex = self.model.index(file)
                if not idx.isValid():
                    native_path: str = QDir.toNativeSeparators(file)
                    idx: QModelIndex = self.model.index(native_path)


                if not idx.isValid():
                    enableButton = False
                    break
                if idx.isValid() and self.model.isDir(idx):
                    isOpenDirectory = True
                    break

        button.setEnabled(enableButton)
        self._public.updateOkButtonText(isOpenDirectory)

    @Slot(QModelIndex)
    def _q_currentChanged(self, index):
        self._q_updateOkButton()
        self._public.currentChanged.emit(self.model.filePath(index))

    @Slot(QModelIndex)
    def _q_enterDirectory(self, index: QModelIndex):
        if not index.isValid():
            return

        if self.model.isDir(index):
            self.ui.treeView.setCurrentIndex(index)
            self._public.setDirectory(self.model.filePath(index))
            self._public.directoryEntered.emit(self.model.filePath(index))
        else:
            self.accept()

    @Slot(QUrl)
    def _q_goToUrl(self, url: QUrl):
        self._public.setDirectoryUrl(url)

    @Slot()
    def _q_goHome(self):
        self._public.setDirectory(QDir.homePath())

    @Slot(QAction)
    def _q_showHeader(self, action: QAction):
        actionGroup: QActionGroup = self._public.sender()
        header: QHeaderView | None = self.ui.treeView.header()
        assert header is not None, "the filewidget header was None somehow."
        header.setSectionHidden(actionGroup.actions().index(action) + 1, not action.isChecked())



    @Slot(str)

    def _q_autoCompleteFileName(self, text: str):
        if self._public.acceptMode() != QFileDialog.AcceptMode.AcceptSave:
            return

        fileNames: list[str] = self._public.typedFiles()

        if len(fileNames) == 1:
            info: QFileInfo = QFileInfo(fileNames[0])
            if info.isDir():
                return

            completer: QtPyFSCompleter | None = self.completer
            if completer and completer.completionMode() == QCompleter.CompletionMode.InlineCompletion:
                completer.complete()


    @Slot(QModelIndex)
    def _q_rowsInserted(self, parent):
        if (not self.ui.treeView
            or parent != self.ui.treeView.rootIndex()
            or not self.ui.treeView.selectionModel()
            or self.ui.treeView.selectionModel().hasSelection()  # pyright: ignore[reportOptionalMemberAccess]
            or self.ui.treeView.model().rowCount(parent) == 0):  # pyright: ignore[reportOptionalMemberAccess]
            return

    @Slot(str, str, str)
    def _q_fileRenamed(self, path: str, oldName: str, newName: str):  # noqa: N803
        fileMode: QFileDialog.FileMode = self._public.fileMode()
        if (

            fileMode in (QFileDialog.FileMode.Directory, QFileDialog.FileMode.DirectoryOnly)
            and path == self.model.rootPath()
            and self.ui.fileNameEdit.text() == oldName
        ):
            self.ui.fileNameEdit.setText(newName)

    def init(self, args: QFileDialogArgs):
        q: QFileDialog = self.q_func()
        if not args.caption.isEmpty():
            self.useDefaultCaption = False
            self.setWindowTitle: str = args.caption
            q.setWindowTitle(args.caption)

        q.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        self.nativeDialogInUse = self.platformFileDialogHelper() is not None
        if not self.nativeDialogInUse:
            self.createWidgets()
        else:
            raise NotImplementedError("Native file dialog is coming soon! Please call setOptions(QFileDialog.Option.DontUseNativeDialog, False) to use the qt-style file dialog.")
        q.setFileMode(QFileDialog.FileMode.AnyFile)
        if not args.filter.isEmpty():
            q.setNameFilter(args.filter)
        dontStoreDir: bool = not args.directory.isValid() and not self._public.lastVisitedDir().isValid()
        q.setDirectoryUrl(args.directory)
        if dontStoreDir:
            self._public.lastVisitedDir().clear()
        if args.directory.isLocalFile():
            q.selectFile(args.selection)
        else:
            q.selectUrl(args.directory)

        if hasattr(QSettings, "UserScope") and not self.restoreFromSettings():
            settings = QSettings(QSettings.Scope.UserScope, "QtProject")
            q.restoreState(settings.value("Qt/filedialog").toByteArray())

        if hasattr(Qt, "Q_EMBEDDED_SMALLSCREEN"):
            self.ui.lookInLabel.setVisible(False)
            self.ui.fileNameLabel.setVisible(False)
            self.ui.fileTypeLabel.setVisible(False)
            self.ui.sidebar.hide()

        sizeHint: QSize = q.sizeHint()
        if sizeHint.isValid():
            q.resize(sizeHint)

    def createWidgets(self):  # noqa: PLR0915
        if self.ui:
            return
        q: QFileDialog = self.q_func()

        # Store initial window state and size
        preSize: QSize = q.size() if q.testAttribute(Qt.WidgetAttribute.WA_Resized) else QSize()
        preState: Qt.WindowState = q.windowState()

        self.model: QFileSystemModel = QFileSystemModel(q)
        self.model.setFilter(self.options.filter())
        self.model.setObjectName("qt_filesystem_model")
        self.model.setNameFilterDisables(False)
        # REM: THIS IS QFileSystemModelPrivate!!
        #self.model.d_func().disableRecursiveSort = True
        self.model.fileRenamed.connect(q._q_fileRenamed)  # noqa: SLF001

        self.model.rootPathChanged.connect(q._q_pathChanged)  # noqa: SLF001
        self.model.rowsInserted.connect(q._q_rowsInserted)  # noqa: SLF001
        self.model.setReadOnly(False)

        if self.nativeDialogInUse:  # TODO: Implement native dialog. We already have the com interfaces setup.
            self.deletePlatformHelper()

        self.ui: Ui_QFileDialog = Ui_QFileDialog()
        self.ui.setupUi(q)

        initialBookmarks: list[QUrl] = [QUrl("file:"), QUrl.fromLocalFile(QDir.homePath())]
        self.ui.sidebar.setModelAndUrls(self.model, initialBookmarks)
        self.ui.sidebar.goToUrl.connect(q._q_goToUrl)  # noqa: SLF001

        self.ui.buttonBox.accepted.connect(q.accept)
        self.ui.buttonBox.rejected.connect(q.reject)

        self.ui.lookInCombo.setFileDialogPrivate(self)
        self.ui.lookInCombo.activated[str].connect(q._q_goToDirectory)  # noqa: SLF001
        self.ui.lookInCombo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.ui.lookInCombo.setDuplicatesEnabled(False)

        self.ui.fileNameEdit.setFileDialogPrivate(self)
        self.ui.fileNameLabel.setBuddy(self.ui.fileNameEdit)
        self.completer = QtPyFSCompleter(self.model, q)
        self.ui.fileNameEdit.setCompleter(self.completer)
        self.ui.fileNameEdit.setInputMethodHints(Qt.InputMethodHint.ImhNoPredictiveText)
        self.ui.fileNameEdit.textChanged.connect(q._q_autoCompleteFileName)  # noqa: SLF001
        self.ui.fileNameEdit.textChanged.connect(q._q_updateOkButton)  # noqa: SLF001
        self.ui.fileNameEdit.returnPressed.connect(q.accept)

        self.ui.fileTypeCombo.setDuplicatesEnabled(False)
        self.ui.fileTypeCombo.setSizeAdjustPolicy(QComboBox.AdjustToContentsOnFirstShow)
        self.ui.fileTypeCombo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.ui.fileTypeCombo.activated[int].connect(q._q_useNameFilter)  # noqa: SLF001
        self.ui.fileTypeCombo.activated[str].connect(q.filterSelected)

        self.ui.listView.setFileDialogPrivate(self)
        self.ui.listView.setModel(self.model)
        self.ui.listView.activated.connect(q._q_enterDirectory)  # noqa: SLF001
        self.ui.listView.customContextMenuRequested.connect(q._q_showContextMenu)  # noqa: SLF001
        self.shortcut: QShortcut = QShortcut(self.ui.listView)
        self.shortcut.setKey(QKeySequence("Delete"))
        self.shortcut.activated.connect(q._q_deleteCurrent)  # noqa: SLF001

        self.ui.treeView.setFileDialogPrivate(self)
        self.ui.treeView.setModel(self.model)
        self.treeHeader: QHeaderView = self.ui.treeView.header()
        fm: QFontMetrics = QFontMetrics(q.font())
        self.treeHeader.resizeSection(0, fm.horizontalAdvance("wwwwwwwwwwwwwwwwwwwwwwwwww"))
        self.treeHeader.resizeSection(1, fm.horizontalAdvance("128.88 GB"))
        self.treeHeader.resizeSection(2, fm.horizontalAdvance("mp3Folder"))
        self.treeHeader.resizeSection(3, fm.horizontalAdvance("10/29/81 02:02PM"))
        self.treeHeader.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)


        self.showActionGroup: QActionGroup = QActionGroup(q)
        self.showActionGroup.setExclusive(False)
        self.showActionGroup.triggered.connect(q._q_showHeader)  # noqa: SLF001


        self.abstractModel: QAbstractProxyModel | QFileSystemModel = self.proxyModel if self.proxyModel else self.model
        for _col in range(1, self.abstractModel.columnCount(QModelIndex())):
            showHeader: QAction = QAction(self.showActionGroup)
            showHeader.setCheckable(True)
            showHeader.setChecked(True)
            self.treeHeader.addAction(showHeader)

        self.ui.treeView.setSelectionModel(self.ui.listView.selectionModel())

        self.ui.treeView.activated.connect(q._q_enterDirectory)  # noqa: SLF001
        self.ui.treeView.customContextMenuRequested.connect(q._q_showContextMenu)  # noqa: SLF001
        shortcut = QShortcut(self.ui.treeView)
        shortcut.setKey(QKeySequence("Delete"))
        shortcut.activated.connect(q._q_deleteCurrent)  # noqa: SLF001

        selections: QItemSelectionModel | None = self.ui.listView.selectionModel()
        selections.selectionChanged.connect(q._q_selectionChanged)  # noqa: SLF001
        selections.currentChanged.connect(q._q_currentChanged)  # noqa: SLF001
        self.ui.splitter.setStretchFactor(
            self.ui.splitter.indexOf(self.ui.splitter.widget(1)),
            QSizePolicy.Policy.Expanding
        )

        self.createToolButtons()
        self.createMenuActions()

        if not self.restoreFromSettings():
            settings: QSettings = QSettings(QSettings.Scope.UserScope, "QtProject")
            q.restoreState(settings.value("Qt/filedialog"))

        q.setFileMode(QFileDialog.FileMode(self._public.fileMode()))
        q.setAcceptMode(QFileDialog.AcceptMode(self._public.acceptMode()))
        q.setViewMode(QFileDialog.ViewMode(self._public.viewMode()))
        q.setOptions(QFileDialog.Options(int(self._public.options())))
        if self._public.sidebarUrls():
            q.setSidebarUrls(self._public.sidebarUrls())
        q.setDirectoryUrl(self._public.initialDirectory())
        if self._public.mimeTypeFilters():
            q.setMimeTypeFilters(self._public.mimeTypeFilters())
        elif self._public.nameFilters():
            q.setNameFilters(self._public.nameFilters())
        q.selectNameFilter(self._public.initiallySelectedNameFilter())
        q.setDefaultSuffix(self._public.defaultSuffix())
        q.setHistory(self._public.history())
        initiallySelectedFiles = self._public.initiallySelectedFiles()
        if len(initiallySelectedFiles) == 1:
            q.selectFile(initiallySelectedFiles[0].fileName())
        for url in initiallySelectedFiles:
            q.selectUrl(url)
        self.lineEdit().selectAll()
        self._q_updateOkButton()
        self.retranslateStrings()  # FIXME: function retranslateStrings doesn't exist here?
        q.resize(preSize if preSize.isValid() else q.sizeHint())
        q.setWindowState(preState)

    def lineEdit(self) -> QLineEdit:
        return self.ui.fileNameEdit

    def createToolButtons(self):

        q: QFileDialog = self.q_func()
        self.ui.backButton.setIcon(q.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack, None, q))
        self.ui.backButton.setAutoRaise(True)
        self.ui.backButton.setEnabled(False)
        self.ui.backButton.clicked.connect(q._q_navigateBackward)  # noqa: SLF001

        self.ui.forwardButton.setIcon(q.style().standardIcon(QStyle.StandardPixmap.SP_ArrowForward, None, q))
        self.ui.forwardButton.setAutoRaise(True)
        self.ui.forwardButton.setEnabled(False)
        self.ui.forwardButton.clicked.connect(q._q_navigateForward)  # noqa: SLF001

        self.ui.toParentButton.setIcon(q.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogToParent, None, q))
        self.ui.toParentButton.setAutoRaise(True)
        self.ui.toParentButton.setEnabled(False)
        self.ui.toParentButton.clicked.connect(q._q_navigateToParent)  # noqa: SLF001

        self.ui.listModeButton.setIcon(q.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogListView, None, q))
        self.ui.listModeButton.setAutoRaise(True)
        self.ui.listModeButton.setDown(True)
        self.ui.listModeButton.clicked.connect(q._q_showListView)  # noqa: SLF001

        self.ui.detailModeButton.setIcon(q.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView, None, q))
        self.ui.detailModeButton.setAutoRaise(True)
        self.ui.detailModeButton.clicked.connect(q._q_showDetailsView)  # noqa: SLF001

        toolSize = QSize(self.ui.fileNameEdit.sizeHint().height(), self.ui.fileNameEdit.sizeHint().height())
        self.ui.backButton.setFixedSize(toolSize)
        self.ui.listModeButton.setFixedSize(toolSize)
        self.ui.detailModeButton.setFixedSize(toolSize)
        self.ui.forwardButton.setFixedSize(toolSize)
        self.ui.toParentButton.setFixedSize(toolSize)

        self.ui.newFolderButton.setIcon(q.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder, None, q))
        self.ui.newFolderButton.setFixedSize(toolSize)
        self.ui.newFolderButton.setAutoRaise(True)
        self.ui.newFolderButton.setEnabled(False)
        self.ui.newFolderButton.clicked.connect(q._q_createDirectory)  # noqa: SLF001

    def createMenuActions(self):
        q = self.q_func()

        goHomeAction = QAction(q)
        goHomeAction.setShortcut(Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier | Qt.Key.Key_H)
        goHomeAction.triggered.connect(q._q_goHome)  # noqa: SLF001
        q.addAction(goHomeAction)

        goToParent = QAction(q)
        goToParent.setObjectName("qt_goto_parent_action")
        goToParent.setShortcut(Qt.KeyboardModifier.ControlModifier | Qt.Key.Key_Up)
        goToParent.triggered.connect(q._q_navigateToParent)  # noqa: SLF001
        q.addAction(goToParent)

        self.renameAction = QAction(q)
        self.renameAction.setEnabled(False)
        self.renameAction.setObjectName("qt_rename_action")
        self.renameAction.triggered.connect(q._q_renameCurrent)  # noqa: SLF001

        self.deleteAction = QAction(q)
        self.deleteAction.setEnabled(False)
        self.deleteAction.setObjectName("qt_delete_action")
        self.deleteAction.triggered.connect(q._q_deleteCurrent)  # noqa: SLF001

        self.showHiddenAction = QAction(q)
        self.showHiddenAction.setObjectName("qt_show_hidden_action")
        self.showHiddenAction.setCheckable(True)
        self.showHiddenAction.triggered.connect(q._q_showHidden)  # noqa: SLF001

        self.newFolderAction = QAction(q)
        self.newFolderAction.setObjectName("qt_new_folder_action")
        self.newFolderAction.triggered.connect(q._q_createDirectory)  # noqa: SLF001

    def _q_goHome(self):
        q: QFileDialog = self.q_func()
        q.setDirectory(QDir.homePath())

    def saveHistorySelection(self):
        if (self.ui is None or
            self.currentHistoryLocation < 0 or
            self.currentHistoryLocation >= len(self.currentHistory)):
            return
        item: dict[str, str] = self.currentHistory[self.currentHistoryLocation]
        item["selection"] = []
        selectedIndexes: list[QModelIndex] = self.ui.listView.selectionModel().selectedRows()
        for index in selectedIndexes:
            item["selection"].append(QPersistentModelIndex(index))

    def usingWidgets(self) -> bool:
        return not self.nativeDialogInUse and self.ui is not None

    def restoreFromSettings(self):

        settings = QSettings(QSettings.Scope.UserScope, "QtProject")
        if not settings.childGroups().contains("FileDialog"):
            return False

        settings.beginGroup("FileDialog")

        lastVisited = settings.value("lastVisited")
        if lastVisited:
            self.q_func().setDirectoryUrl(QUrl(lastVisited))

        viewMode = settings.value("viewMode")
        if viewMode:
            self.q_func().setViewMode(QFileDialog.ViewMode(int(viewMode)))

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


    def restoreWidgetState(self, history: list[str], splitterPosition: int) -> bool:  # noqa: N803
        if not self.usingWidgets():
            return False

        settings = QSettings(QSettings.Scope.UserScope, "QtProject")
        settings.beginGroup("FileDialog")

        if splitterPosition >= 0:
            splitterSizes: list[int] = [splitterPosition, self.ui.splitter.widget(1).sizeHint().width()]
            self.ui.splitter.setSizes(splitterSizes)
        else:
            splitterState = settings.value("splitterState", QByteArray())
            if not self.ui.splitter.restoreState(splitterState):
                return False
            sizes: list[int] = self.ui.splitter.sizes()
            if len(sizes) >= 2 and (sizes[0] == 0 or sizes[1] == 0):
                sizes = [self.ui.splitter.widget(i).sizeHint().width() for i in range(len(sizes))]
                self.ui.splitter.setSizes(sizes)

        self.ui.sidebar.setUrls(self.sidebarUrls)

        MAX_HISTORY_SIZE = 5  # TODO: Make this configurable
        if len(history) > MAX_HISTORY_SIZE:
            history = history[-MAX_HISTORY_SIZE:]
        self.q_func().setHistory(history)

        headerView: QHeaderView | None = self.ui.treeView.header()
        if headerView is not None and not headerView.restoreState(self.headerData):
            return False


        actions: list[QAction] = headerView.actions()
        abstractModel: QAbstractProxyModel | QFileSystemModel = self.model
        if hasattr(self, "proxyModel") and self.proxyModel is not None:  # noqa: E721
            abstractModel = self.proxyModel

        total: int = min(abstractModel.columnCount(), len(actions) + 1)
        for i in range(1, total):
            actions[i - 1].setChecked(not headerView.isSectionHidden(i))

        return True

    def _q_navigateToParent(self):
        root_qdir = QDir(self.model.rootDirectory())
        if root_qdir.isRoot():
            myComputerSomething: QUrl = self.model.myComputer()
            newDirectory = myComputerSomething.toString()
        else:
            root_qdir.cdUp()
            newDirectory = root_qdir.absolutePath()
        self._public.setDirectory(newDirectory)
        self._public.directoryEntered.emit(newDirectory)

    def _q_createDirectory(self):
        self.ui.listView.clearSelection()
        newFolderString = QFileDialog.tr("New Folder")
        folderName = newFolderString
        prefix = self._public.directory().absolutePath() + QDir.separator()
        if QDir(prefix + folderName).exists():
            suffix = 2
            while QDir(prefix + folderName).exists():
                folderName = f"{newFolderString}{suffix}"
                suffix += 1

        parent: QModelIndex = self.currentView().rootIndex()
        index: QModelIndex = self.model.mkdir(parent, folderName)
        if not index.isValid():
            return

        index: QModelIndex = self.currentView().selectionModel().select(index, QItemSelectionModel.SelectionFlag.ClearAndSelect)  # FIXME: function select doesn't exist here?
        if index.isValid():
            self.ui.treeView.setCurrentIndex(index)
            self.currentView().edit(index)

    def _q_showListView(self):
        self.ui.listModeButton.setDown(True)
        self.ui.detailModeButton.setDown(False)
        self.ui.treeView.hide()
        self.ui.listView.show()
        self.ui.stackedWidget.setCurrentWidget(self.ui.listView)
        self._public.setViewMode(QFileDialog.ViewMode.List)

    def _q_showDetailsView(self):
        self.ui.listModeButton.setDown(False)
        self.ui.detailModeButton.setDown(True)
        self.ui.listView.hide()
        self.ui.treeView.show()
        self.ui.stackedWidget.setCurrentWidget(self.ui.treeView)
        self._public.setViewMode(QFileDialog.ViewMode.Detail)

    def mapToSource(self, index):
        return self.proxyModel.mapToSource(index) if self.proxyModel else index

    def mapFromSource(self, index):
        return self.proxyModel.mapFromSource(index) if self.proxyModel else index

    def rootPath(self):
        return self.model.rootPath() if self.model else "/"

    def platformFileDialogHelper(self) -> QFileDialogPlatformHelper:
        return QFileDialogPlatformHelper(self._public.options())


    def setDirectory_sys(self, directory: QUrl):

        helper: QFileDialogPlatformHelper = self.platformFileDialogHelper()
        if helper and helper.isSupportedUrl(directory):
            helper.setDirectory(directory.toString())


    def directory_sys(self) -> QUrl:

        helper: QFileDialogPlatformHelper = self.platformFileDialogHelper()
        return QUrl(helper.directory()) if helper else QUrl()



    def selectFile_sys(self, filename: QUrl):
        helper: QFileDialogPlatformHelper = self.platformFileDialogHelper()
        if helper and helper.isSupportedUrl(filename):
            helper.selectFile(filename)


    def selectedFiles_sys(self) -> list[QUrl]:
        helper: QFileDialogPlatformHelper = self.platformFileDialogHelper()
        return [QUrl(url) for url in helper.selectedFiles()] if helper else []


    def setFilter_sys(self):
        helper: QFileDialogPlatformHelper = self.platformFileDialogHelper()
        if helper:
            helper.setFilter()


    def selectMimeTypeFilter_sys(self, filter: str):  # noqa: A002
        helper: QFileDialogPlatformHelper = self.platformFileDialogHelper()
        if helper:
            helper.selectMimeTypeFilter(filter)


    def selectedMimeTypeFilter_sys(self) -> str:
        helper: QFileDialogPlatformHelper = self.platformFileDialogHelper()
        return helper.selectedMimeTypeFilter() if helper else ""

    def selectNameFilter_sys(self, filter: str) -> None:  # noqa: A002

        self._public.selectNameFilter(filter)
        helper: QFileDialogPlatformHelper = self.platformFileDialogHelper()
        if helper:
            helper.selectNameFilter(filter)



    def selectedNameFilter_sys(self) -> str:
        helper: QFileDialogPlatformHelper = self.platformFileDialogHelper()
        return helper.selectedNameFilter() if helper else ""


    def getSelectedFiles(self) -> list[str]:
        selected_indexes: list[QModelIndex] = self.ui.listView.selectedIndexes()
        return [self.model.filePath(index) for index in selected_indexes]

    def itemViewKeyboardEvent(self, e: QKeyEvent) -> bool:
        if e.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            self.accept()
            return True
        return False

    def accept(self) -> None:
        if self._public.acceptMode() == self._public.AcceptMode.AcceptSave:
            self._public.accept()
        else:
            selected_files: list[str] = self.getSelectedFiles()
            if selected_files:
                self._public.accept()
            else:
                self._public.reject()


class HistoryItem:
    def __init__(self):
        self.path: str = ""
        self.selection: list[QPersistentModelIndex] = []


class QFileDialogListView(QListView):
    def __init__(
        self,
        parent: QFileDialog,
    ):
        super().__init__(parent)

    def setFileDialogPrivate(self, d_pointer: QFileDialogPrivate):
        self.d_ptr: QFileDialogPrivate = d_pointer
        self.setSelectionBehavior(QListView.SelectionBehavior.SelectRows)
        self.setWrapping(True)
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setEditTriggers(QAbstractItemView.EditTrigger.EditKeyPressed)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

    def _d_ptr(self) -> QFileDialogPrivate:
        from utility.ui_libraries.qt.filesystem.explorer.qfiledialogpy.private.qfiledialog import QFileDialog

        return cast(QFileDialog, self.parent())._private  # noqa: SLF001

    def sizeHint(self) -> QSize:
        height = max(10, self.sizeHintForRow(0))
        return QSize(super().sizeHint().width() * 2, height * 30)

    def keyPressEvent(self, e: QKeyEvent) -> None:
        if not self._d_ptr().itemViewKeyboardEvent(e):
            super().keyPressEvent(e)
        e.accept()


class QFileDialogLineEdit(QLineEdit):
    def __init__(
        self,
        parent: QFileDialog,
    ):
        super().__init__(parent)
        self.hideOnEsc: bool = False

    def keyPressEvent(self, e: QKeyEvent):
        super().keyPressEvent(e)
        if e.key() == Qt.Key.Key_Escape and self.hideOnEsc:
            self.hide()
        e.accept()

    def _d_ptr(self) -> QFileDialogPrivate:
        from utility.ui_libraries.qt.filesystem.explorer.qfiledialogpy.private.qfiledialog import QFileDialog

        return cast(QFileDialog, self.parent())._private  # noqa: SLF001

    def setFileDialogPrivate(self, d_pointer: QFileDialogPrivate):
        self.d_ptr: QFileDialogPrivate = d_pointer


class QtPyUrlModel(QAbstractListModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._urls: list[QUrl] = []

    def _d_ptr(self) -> QFileDialogPrivate:
        from utility.ui_libraries.qt.filesystem.explorer.qfiledialogpy.private.qfiledialog import QFileDialog
        return cast(QFileDialog, self.parent())._private  # noqa: SLF001

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        return len(self._urls)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self._urls):
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            return self._urls[index.row()].toString()
        if role == Qt.ItemDataRole.EditRole:
            return self._urls[index.row()].toLocalFile()
        return None

    def setUrls(self, urls: list[QUrl]) -> None:
        self.beginResetModel()
        self._urls = [url for url in urls if url.isLocalFile()]
        self.endResetModel()

    def urls(self):
        return self._urls

    def addUrl(self, url: QUrl) -> None:
        self.beginInsertRows(QModelIndex(), len(self._urls), len(self._urls))
        self._urls.append(url)
        self.endInsertRows()

    def removeUrl(self, url: QUrl) -> None:
        if url in self._urls:
            index: int = self._urls.index(url)
            self.beginRemoveRows(QModelIndex(), index, index)
            self._urls.pop(index)
            self.endRemoveRows()

    def addUrls(self, urls: list[QUrl], row: int = -1, *, prepend: bool = True) -> None:
        if not urls:
            return
        if row < 0:
            row = len(self._urls)
        if prepend:
            urls.reverse()
        self.beginInsertRows(QModelIndex(), row, row + len(urls) - 1)
        for url in urls:
            self._urls.insert(row, url)
        self.endInsertRows()


class QFileDialogComboBox(QComboBox):
    def __init__(
        self,
        parent: QFileDialog,
    ):
        super().__init__(parent)
        self.urlModel: QtPyUrlModel | None = None
        self._private: QFileDialogPrivate | None = None
        self.m_history: list[str] = []

    def showPopup(self):
        if self.urlModel is None:
            self.urlModel = QtPyUrlModel(self)
            self.setModel(self.urlModel)
        self.urlModel.setUrls([])
        self.urlModel.addUrls([QUrl.fromLocalFile(path) for path in self.m_history], -1)
        idx: QModelIndex = self.model().index(self.model().rowCount() - 1, 0)
        urls: list[QUrl] = []
        for path in self.m_history:
            url = QUrl.fromLocalFile(path)
            if url not in urls:
                urls.insert(0, url)

        if urls:
            self.model().insertRow(self.model().rowCount())
            idx = self.model().index(self.model().rowCount() - 1, 0)
            self.model().setData(idx, QFileDialog.tr("Recent Places"))
            m: QStandardItemModel | None = cast(QStandardItemModel, self.model())
            if m is None:
                print("QStandardItemModel is None")
                return
            flags: Qt.ItemFlag = m.flags(idx)

            flags &= ~Qt.ItemFlag.ItemIsEnabled
            m.item(idx.row(), idx.column()).setFlags(flags)
        self.urlModel.addUrls(urls, -1, prepend=False)
        self.setCurrentIndex(0)

        super().showPopup()

    def setFileDialogPrivate(self, private: QFileDialogPrivate):
        self._private = private

    def showPopup(self):
        if self.urlModel is None:
            self.urlModel = QtPyUrlModel()
            self.setModel(self.urlModel)
        self.urlModel.setUrls([])
        self.urlModel.addUrls(self.m_history, -1)
        idx: QModelIndex = self.model().index(self.model().rowCount() - 1, 0)
        urls: list[QUrl] = []
        for path in self.m_history:
            url: QUrl = QUrl.fromLocalFile(path)
            if url not in urls:
                urls.insert(0, url)

        if urls:
            self.model().insertRow(self.model().rowCount())
            idx = self.model().index(self.model().rowCount() - 1, 0)
            self.model().setData(idx, QFileDialog.tr("Recent Places"))
            m: QStandardItemModel | None = cast(QStandardItemModel, self.model())
            if m:
                flags: Qt.ItemFlag = m.flags(idx)

                flags &= ~Qt.ItemFlag.ItemIsEnabled
                m.item(idx.row(), idx.column()).setFlags(flags)
            self.urlModel.addUrls(urls, -1, prepend=False)
        self.setCurrentIndex(0)
        super().showPopup()

    def _d_ptr(self) -> QFileDialogPrivate:
        from utility.ui_libraries.qt.filesystem.explorer.qfiledialogpy.private.qfiledialog import QFileDialog

        return cast(QFileDialog, self.parent())._private  # noqa: SLF001

    def setHistory(self, paths: list[str]):
        self.m_history = paths

    def history(self) -> list[str]:
        return self.m_history

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        opt = QStyleOptionComboBox()
        self.initStyleOption(opt)

        edit_rect: QRect = self.style().subControlRect(QStyle.ComplexControl.CC_ComboBox, opt, QStyle.SubControl.SC_ComboBoxEditField, self)
        size: int = edit_rect.width() - opt.iconSize.width() - 4
        opt.currentText = opt.fontMetrics.elidedText(opt.currentText, Qt.TextElideMode.ElideMiddle, size)

        self.style().drawComplexControl(QStyle.ComplexControl.CC_ComboBox, opt, painter, self)
        self.style().drawControl(QStyle.ControlElement.CE_ComboBoxLabel, opt, painter, self)

    def keyPressEvent(self, e: QKeyEvent):
        if not self._private.itemViewKeyboardEvent(e):
            super().keyPressEvent(e)
        e.accept()


class QFileDialogTreeView(QTreeView):
    def __init__(
        self,
        parent: QFileDialog,
    ):
        super().__init__(parent)
        self._private: QFileDialogPrivate | None = None

    def setFileDialogPrivate(self, private: QFileDialogPrivate):
        self._private = private
        self.setSelectionBehavior(QTreeView.SelectionBehavior.SelectRows)
        self.setRootIsDecorated(False)
        self.setItemsExpandable(False)
        self.setSortingEnabled(True)
        self.header().setSortIndicator(0, Qt.SortOrder.AscendingOrder)
        self.header().setStretchLastSection(False)
        self.setTextElideMode(Qt.TextElideMode.ElideMiddle)
        self.setEditTriggers(QAbstractItemView.EditTrigger.EditKeyPressed)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

    @property
    def _d_ptr(self) -> QFileDialogPrivate:
        from utility.ui_libraries.qt.filesystem.explorer.qfiledialogpy.private.qfiledialog import QFileDialog

        return cast(QFileDialog, self.parent())._private  # noqa: SLF001

    def keyPressEvent(self, e: QKeyEvent):
        if not self._private.itemViewKeyboardEvent(e):
            super().keyPressEvent(e)
        e.accept()

    def sizeHint(self) -> QSize:
        height: int = max(10, self.sizeHintForRow(0))
        size_hint: QSize = self.header().sizeHint()
        return QSize(size_hint.width() * 4, height * 30)
