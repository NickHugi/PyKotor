from __future__ import annotations

import os
import sys
import tempfile
import unittest

from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import qtpy

from PyQt5.QtWidgets import QPushButton
from qtpy.QtCore import (
    QAbstractProxyModel,
    QCoreApplication,
    QDataStream,
    QDir,
    QFile,
    QFileInfo,
    QIODevice,
    QModelIndex,
    QPoint,
    QRandomGenerator,
    QSettings,
    QSortFilterProxyModel,
    QStandardPaths,
    QTemporaryFile,
    QTimer,
    QUrl,
    Qt,
)
from qtpy.QtGui import QCursor
from qtpy.QtTest import QSignalSpy, QTest
from qtpy.QtWidgets import (
    QAction,  # pyright: ignore[reportPrivateImportUsage]
    QApplication,
    QComboBox,
    QDialogButtonBox,
    QFileSystemModel,  # pyright: ignore[reportPrivateImportUsage]
    QLineEdit,
    QListView,
    QToolButton,
    QTreeView,
    QWidget,
)

from utility.ui_libraries.qt.adapters.filesystem.pyfileinfogatherer import PyFileInfoGatherer as QFileInfoGatherer
from utility.ui_libraries.qt.adapters.filesystem.qfiledialog.rewritten.private.qsidebar import QSidebar
from utility.ui_libraries.qt.adapters.filesystem.qfiledialog.rewritten.qfiledialog import QFileDialog as PythonQFileDialog
from utility.ui_libraries.qt.adapters.kernel.qplatformdialoghelper.qplatformdialoghelper import QPlatformFileDialogHelper

if TYPE_CHECKING:
    from qtpy.QtCore import QAbstractItemModel
    from qtpy.QtWidgets import QPushButton


class FilterDirModel(QAbstractProxyModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sourceModel = None

    def setSourceModel(self, sourceModel: QAbstractItemModel):  # noqa: N803
        self._sourceModel = sourceModel
        super().setSourceModel(sourceModel)

    def mapToSource(self, proxyIndex: QModelIndex) -> QModelIndex:  # noqa: N803
        if not self._sourceModel:
            return QModelIndex()
        return self._sourceModel.index(proxyIndex.row(), proxyIndex.column(), proxyIndex.parent())

    def mapFromSource(self, sourceIndex: QModelIndex) -> QModelIndex:  # noqa: N803
        if not sourceIndex.isValid():
            return QModelIndex()
        return self.index(sourceIndex.row(), sourceIndex.column(), sourceIndex.parent())

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:  # noqa: B008
        if not self._sourceModel:
            return QModelIndex()
        return self.createIndex(row, column, self._sourceModel.index(row, column, parent).internalPointer())

    def parent(self, child: QModelIndex = QModelIndex()) -> QModelIndex:  # pyright: ignore[reportIncompatibleMethodOverride]  # noqa: B008
        if not self._sourceModel:
            return QModelIndex()
        return self._sourceModel.parent(self.mapToSource(child))

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        if not self._sourceModel:
            return 0
        return self._sourceModel.rowCount(self.mapToSource(parent))

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        if not self._sourceModel:
            return 0
        return self._sourceModel.columnCount(self.mapToSource(parent))

    def data(self, proxyIndex: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any | None:  # noqa: N803
        if not self._sourceModel:
            return None
        sourceIndex = self.mapToSource(proxyIndex)
        if not sourceIndex.isValid():
            return None
        if not isinstance(self._sourceModel, QFileSystemModel):
            return None
        if self._sourceModel.isDir(sourceIndex):
            return self._sourceModel.data(sourceIndex, role)
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags | Qt.ItemFlag:  # pyright: ignore[reportIncompatibleMethodOverride]
        if not self._sourceModel:
            return Qt.ItemFlag.NoItemFlags
        return self._sourceModel.flags(self.mapToSource(index))


class TestQFileDialog2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app: QApplication = cast(QApplication, QApplication.instance() or QApplication(sys.argv))
        cls.temp_dir: tempfile.TemporaryDirectory = tempfile.TemporaryDirectory()
        cls.temp_path: Path = Path(os.path.normpath(cls.temp_dir.name)).absolute()
        cls.temp_path_str: str = str(cls.temp_path)
        assert cls.temp_path.exists(), f"Temporary directory is not valid: {cls.temp_path}"
        QStandardPaths.setTestModeEnabled(True)

    @classmethod
    def tearDownClass(cls):
        QStandardPaths.setTestModeEnabled(False)
        cls.temp_dir.cleanup()
        cls.app.quit()

    def setUp(self):
        self.cleanupSettingsFile()
        self.fd_class: type[PythonQFileDialog] = PythonQFileDialog
        self._test_data: dict[str, list[Any]] = {}
        self._current_row: str | None = None
        self._qtest: type[QTest] = QTest  # TypeError: PyQt5.QtTest.QTest represents a C++ namespace and cannot be instantiated

    def tearDown(self):
        self.temp_dir.cleanup()
        self.cleanupSettingsFile()
        for widget in self.app.topLevelWidgets():
            widget.close()
            widget.deleteLater()

    def cleanupSettingsFile(self):
        settings = QSettings(QSettings.Scope.UserScope, "QtProject")
        settings.beginGroup("FileDialog")
        settings.remove("")
        settings.endGroup()
        settings.beginGroup("Qt")  # Compatibility settings
        settings.remove("filedialog")
        settings.endGroup()

    def openContextMenu(self, fd: PythonQFileDialog) -> bool:
        try:
            fd.d_func()._q_showContextMenu(QCursor.pos())  # noqa: SLF001
        except Exception as e:  # noqa: BLE001
            print(f"Error opening context menu: {e}")
            return False
        else:
            return True

    def test_listRoot(self):
        fileInfoGatherer = QFileInfoGatherer()
        fileInfoGatherer.start()
        self._qtest.qWait(1500)
        # qt_test_resetFetchedRoot()  # TODO
        dir = QDir.currentPath()  # noqa: A001
        fd = self.fd_class(None, "", dir)
        fd.show()
        # self.assertFalse(qt_test_isFetchedRoot())  # TODO
        fd.setDirectory("")
        # self.assertEqual(qt_test_isFetchedRoot(), True)  # TODO

    def test_heapCorruption(self):
        dialogs: list[PythonQFileDialog] = []
        for _ in range(10):
            f = self.fd_class(None)
            dialogs.append(f)
        for dialog in dialogs:
            dialog.deleteLater()

    def test_deleteDirAndFiles(self):
        tempPath = self.temp_path / "QFileDialogTestDir4FullDelete"
        tempPath.mkdir(parents=True, exist_ok=True)
        (tempPath / "foo").mkdir(parents=True, exist_ok=True)
        (tempPath / "foo/B").mkdir(parents=True, exist_ok=True)
        (tempPath / "foo/c").mkdir(parents=True, exist_ok=True)
        (tempPath / "bar").mkdir(parents=True, exist_ok=True)
        t = tempfile.NamedTemporaryFile(dir=tempPath / "foo", delete=False)
        t.close()
        t = tempfile.NamedTemporaryFile(dir=tempPath / "foo/B", delete=False)
        t.close()
        fd = self.fd_class()
        fd.setDirectory(str(tempPath))
        fd.show()
        fd.d_func().removeDirectory(str(tempPath))
        assert not QFileInfo.exists(str(tempPath))

    def test_filter(self):
        fd = self.fd_class()
        hiddenAction = fd.findChild(QAction, "qt_show_hidden_action")
        assert hiddenAction is not None, "qt_show_hidden_action was None, expected QAction"
        assert hiddenAction.isEnabled(), "qt_show_hidden_action was not enabled"
        assert not hiddenAction.isChecked(), "qt_show_hidden_action was checked"
        filter = fd.filter()
        filter |= QDir.Filter.Hidden
        fd.setFilter(filter)
        assert hiddenAction.isChecked(), "qt_show_hidden_action was not checked"

    def test_showNameFilterDetails(self):
        fd = self.fd_class()
        filters = fd.findChild(QComboBox, "fileTypeCombo")
        assert filters is not None, "Filter combobox fileTypeCombo was None"
        assert not fd.testOption(self.fd_class.Option.HideNameFilterDetails), "HideNameFilterDetails was not False"

        filterChoices: list[str] = ["Image files (*.png *.xpm *.jpg)", "Text files (*.txt)", "Any files (*.*)"]
        fd.setNameFilters(filterChoices)

        fd.setOption(self.fd_class.Option.HideNameFilterDetails, True)  # noqa: FBT003
        assert filters.itemText(0) == "Image files"
        assert filters.itemText(1) == "Text files"
        assert filters.itemText(2) == "Any files"

        fd.setOption(self.fd_class.Option.HideNameFilterDetails, False)  # noqa: FBT003
        assert filters.itemText(0) == filterChoices[0]
        assert filters.itemText(1) == filterChoices[1]
        assert filters.itemText(2) == filterChoices[2]

    def test_unc(self):
        dir = QDir.currentPath()
        assert QFile.exists(dir), f"Directory DoesNotExist: {dir}"
        fd = self.fd_class(None, "", dir)
        model = fd.findChild(QFileSystemModel, "qt_filesystem_model")
        assert model is not None, "qt_filesystem_model was None"
        fd_dir_path = fd.directory().absolutePath()
        model_index_fd = model.index(fd_dir_path)
        model_index_dir = model.index(dir)
        assert model_index_fd == model_index_dir, f"qt_filesystem_model index was not equal to directory: {model_index_fd} != {model_index_dir}"

    def test_emptyUncPath(self):
        fd = self.fd_class()
        fd.show()
        lineEdit = fd.findChild(QLineEdit, "fileNameEdit")
        assert lineEdit is not None, "Line edit was not found with name 'fileNameEdit'"
        for i in range(3):
            self._qtest.keyPress(lineEdit, Qt.Key.Key_Backslash)
        model = fd.findChild(QFileSystemModel, "qt_filesystem_model")
        assert model is not None, "qt_filesystem_model was None"

    def test_task143519_deleteAndRenameActionBehavior(self):
        class TestContext:
            def __init__(self, path):
                self.current = QDir(str(path))
                self.test = QDir()
                self.file = QFile()

            def __del__(self):
                self.file.remove()
                self.current.rmdir(self.test.dirName())

        ctx = TestContext(self.temp_path)

        # setup testbed
        assert ctx.current.mkdir("task143519_deleteAndRenameActionBehavior_test"), f"Failed to create test directory: {ctx.current.absolutePath()}"
        ctx.test = QDir(ctx.current)
        assert ctx.test.cd("task143519_deleteAndRenameActionBehavior_test"), f"Failed to cd to test directory: {ctx.test.absolutePath()}"
        ctx.file.setFileName(ctx.test.absoluteFilePath("hello"))
        assert ctx.file.open(QIODevice.OpenModeFlag.WriteOnly), "Failed to open file for writing"
        assert bool(ctx.file.permissions() & QFile.Permission.WriteUser), "File does not have write permission"
        ctx.file.close()

        fd = self.fd_class()
        fd.setViewMode(self.fd_class.ViewMode.List)
        fd.setDirectory(ctx.test.absolutePath())
        fd.selectFile(ctx.file.fileName())
        fd.show()

        assert self._qtest.qWaitForWindowExposed(fd), "File dialog was not exposed"

        # grab some internals:
        rm = fd.findChild(QAction, "qt_delete_action")
        assert rm is not None, "Delete action was not found with name 'qt_delete_action'"
        mv = fd.findChild(QAction, "qt_rename_action")
        assert mv is not None, "Rename action was not found with name 'qt_rename_action'"

        # these are the real test cases:

        # defaults
        assert self.openContextMenu(fd), "Failed to open context menu"
        assert fd.selectedFiles() == [ctx.file.fileName()], f"Selected files were not correct, expected: {ctx.file.fileName()}, got: {fd.selectedFiles()}"
        assert rm.isEnabled() != fd.testOption(
            self.fd_class.Option.ReadOnly
        ), f"Delete action was not enabled, expected: {not fd.testOption(self.fd_class.Option.ReadOnly)}, got: {rm.isEnabled()}"
        assert mv.isEnabled() != fd.testOption(
            self.fd_class.Option.ReadOnly
        ), f"Rename action was not enabled, expected: {not fd.testOption(self.fd_class.Option.ReadOnly)}, got: {mv.isEnabled()}"

        # change to non-defaults:
        fd.setOption(self.fd_class.Option.ReadOnly, not fd.testOption(self.fd_class.Option.ReadOnly))  # noqa: FBT003

        assert self.openContextMenu(fd), "Failed to open context menu"
        assert len(fd.selectedFiles()) == 1, f"Selected files were not correct, expected: 1, got: {len(fd.selectedFiles())}"
        assert rm.isEnabled() != fd.testOption(
            self.fd_class.Option.ReadOnly
        ), f"Delete action was not enabled, expected: {not fd.testOption(self.fd_class.Option.ReadOnly)}, got: {rm.isEnabled()}"
        assert mv.isEnabled() != fd.testOption(
            self.fd_class.Option.ReadOnly
        ), f"Rename action was not enabled, expected: {not fd.testOption(self.fd_class.Option.ReadOnly)}, got: {mv.isEnabled()}"

        # and changed back to defaults:
        fd.setOption(self.fd_class.Option.ReadOnly, not fd.testOption(self.fd_class.Option.ReadOnly))

        assert self.openContextMenu(fd), "Failed to open context menu"
        assert len(fd.selectedFiles()) == 1, f"Selected files were not correct, expected: 1, got: {len(fd.selectedFiles())}"
        assert rm.isEnabled() != fd.testOption(
            self.fd_class.Option.ReadOnly
        ), f"Delete action was not enabled, expected: {not fd.testOption(self.fd_class.Option.ReadOnly)}, got: {rm.isEnabled()}"
        assert mv.isEnabled() != fd.testOption(
            self.fd_class.Option.ReadOnly
        ), f"Rename action was not enabled, expected: {not fd.testOption(self.fd_class.Option.ReadOnly)}, got: {mv.isEnabled()}"

    def test_task178897_minimumSize(self):
        fd = self.fd_class()
        oldMs = fd.layout().minimumSize()
        history = fd.history()
        history.append(QDir.toNativeSeparators("/verylongdirectory/aaaaaaaaaabbbbbbbbcccccccccccddddddddddddddeeeeeeeeeeeeffffffffffgggtggggggggghhhhhhhhiiiiiijjjk"))
        fd.setHistory(history)
        fd.show()
        ms = fd.layout().minimumSize()
        assert ms.width() <= oldMs.width(), f"Minimum size was not correct, expected: {oldMs.width()}, got: {ms.width()}"

    def test_task180459_lastDirectory_data(self):
        self.addColumn("path", str)
        self.addColumn("directory", str)
        self.addColumn("isEnabled", bool)
        self.addColumn("result", str)
        self.newRow("path+file").setData(QDir.homePath() + QDir.separator() + "Vugiu1co", QDir.homePath(), True, QDir.homePath() + QDir.separator() + "Vugiu1co")
        self.newRow("no path").setData("", self.temp_path, False, "")
        self.newRow("file").setData("foo", QDir.currentPath(), True, QDir.currentPath() + QDir.separator() + "foo")
        self.newRow("path").setData(QDir.homePath(), QDir.homePath(), False, "")
        self.newRow("path not existing").setData("/usr/bin/foo/bar/foo/foo.txt", self.temp_path, True, self.temp_path.joinpath("foo.txt"))

    @unittest.skipIf(sys.platform == "darwin", "Insignificant on OSX")
    def test_task180459_lastDirectory(self):
        dlg = self.fd_class(None, "", str(self.temp_path))
        model = dlg.findChild(QFileSystemModel, "qt_filesystem_model")
        assert model is not None, "File system model was not found with name 'qt_filesystem_model'"
        assert model.index(str(self.temp_path)) == model.index(
            dlg.directory().absolutePath()
        ), f"Selected file was not correct, expected: {dlg.directory().absolutePath()}, got: {dlg.selectedFiles().first()}"
        dlg.deleteLater()
        path = self.getData("path")
        directory = self.getData("directory")
        isEnabled = self.getData("isEnabled")
        result = self.getData("result")
        dlg = self.fd_class(None, "", path)
        model: QFileSystemModel | None = dlg.findChild(QFileSystemModel, "qt_filesystem_model")
        assert model is not None, "File system model was not found with name 'qt_filesystem_model'"
        dlg.setAcceptMode(self.fd_class.AcceptSave)
        assert model.index(dlg.directory().absolutePath()) == model.index(
            str(directory)
        ), f"Selected file was not correct, expected: {directory}, got: {dlg.directory().absolutePath()}"
        buttonBox: QDialogButtonBox | None = dlg.findChild(QDialogButtonBox, "buttonBox")
        button: QPushButton = buttonBox.button(QDialogButtonBox.Save)
        assert button is not None, "Save button was not found with name 'Save'"
        assert button.isEnabled() == isEnabled, f"Save button was not enabled, expected: {isEnabled}, got: {button.isEnabled()}"
        if isEnabled:
            assert model.index(str(result)) == model.index(
                dlg.selectedFiles().first()
            ), f"Selected file was not correct, expected: {result}, got: {dlg.selectedFiles().first()}"
        dlg.deleteLater()

    def test_settingsCompatibility_data(self):
        self.addColumn("qtVersion", str)
        self.addColumn("dsVersion", QDataStream.Version)
        if qtpy.QT6:
            self.newRow("6.2.3").setData("6.2.3", QDataStream.Version.Qt_6_0)
            self.newRow("6.5").setData("6.5", QDataStream.Version.Qt_6_5)
        self.newRow("15.5.2").setData("5.15.2", QDataStream.Version.Qt_5_15)
        self.newRow("15.5.9").setData("5.15.9", QDataStream.Version.Qt_5_15)

    def test_settingsCompatibility(self):
        ba32 = (
            b"\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\xf7\x00\x00\x00\x04\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            b"d\xff\xff\xff\xff\x00\x00\x00\x81\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x01\t\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00>\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00"
            b"B\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00n\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x03\xe8\x00\xff\xff\xff\xff\x00\x00\x00\x00"
        )
        fd = self.fd_class()

        fd.setProxyModel(FilterDirModel(QDir.currentPath()))
        fd.show()
        self._qtest.qWaitForWindowExposed(fd)
        edit: QLineEdit | None = fd.findChild(QLineEdit, "fileNameEdit")
        assert edit is not None, "File name edit was not found with name 'fileNameEdit'"
        self._qtest.keyClick(edit, Qt.Key.Key_T)
        self._qtest.keyClick(edit, Qt.Key.Key_S)
        self._qtest.keyClick(edit.completer().popup(), Qt.Key.Key_Down)
        dialog = CrashDialog(None, "crash dialog test", QDir.homePath(), "*")
        dialog.show()
        dialog.show()
        self._qtest.qWaitForWindowExposed(dialog)
        _list = dialog.findChild(QListView, "listView")
        assert _list is not None, "List view was not found with name 'listView'"
        self._qtest.keyClick(_list, Qt.Key.Key_Down)
        self._qtest.keyClick(_list, Qt.Key.Key_Return)
        dialog.close()
        fd.close()
        fd2 = self.fd_class(None, "I should not crash with a proxy", str(self.temp_path), Qt.KeyboardModifier.NoModifier)
        pm = QSortFilterProxyModel()
        fd2.setProxyModel(pm)
        fd2.show()
        sidebar = fd2.findChild(QSidebar, "sidebar")
        assert sidebar is not None, "Sidebar was not found with name 'sidebar'"
        sidebar.setFocus()
        sidebar.selectUrl(QUrl.fromLocalFile(QDir.homePath()))
        self._qtest.mouseClick(sidebar.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, sidebar.visualRect(sidebar.model().index(1, 0)).center())
        self._qtest.qWait(250)

    def test_task227930_correctNavigationKeyboardBehavior(self):
        current = QDir(QDir.currentPath())
        current.mkdir("test")
        current.cd("test")
        file = QFile("test/out.txt")
        file2 = QFile("test/out2.txt")

        assert file.open(QIODevice.OpenModeFlag.WriteOnly | QIODevice.OpenModeFlag.Text), "Failed to open file for writing"
        assert file2.open(QIODevice.OpenModeFlag.WriteOnly | QIODevice.OpenModeFlag.Text), "Failed to open file for writing"
        current.cdUp()
        current.mkdir("test2")
        fd = self.fd_class()
        fd.setViewMode(self.fd_class.ViewMode.List)
        fd.setDirectory(current.absolutePath())
        fd.show()
        self._qtest.qWaitForWindowExposed(fd)
        QCoreApplication.processEvents()
        listView: QListView | None = fd.findChild(QListView, "listView")
        assert listView is not None, "List view was not found with name 'listView'"
        self._qtest.keyClick(listView, Qt.Key.Key_Down)
        self._qtest.keyClick(listView, Qt.Key.Key_Return)
        self._qtest.mouseClick(listView.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        self._qtest.keyClick(listView, Qt.Key.Key_Down)
        self._qtest.keyClick(listView, Qt.Key.Key_Backspace)
        self._qtest.keyClick(listView, Qt.Key.Key_Down)
        self._qtest.keyClick(listView, Qt.Key.Key_Down)
        self._qtest.keyClick(listView, Qt.Key.Key_Return)
        assert fd.isVisible(), "File dialog was not visible"
        file.close()
        file2.close()
        file.remove()
        file2.remove()
        current.rmdir("test")
        current.rmdir("test2")

    def test_task226366_lowerCaseHardDriveWindows(self):
        fd = self.fd_class()
        fd.setDirectory(QDir.root().path())
        fd.show()
        edit: QLineEdit | None = fd.findChild(QLineEdit, "fileNameEdit")
        buttonParent: QToolButton | None = fd.findChild(QToolButton, "toParentButton")
        assert edit is not None, "File name edit was not found with name 'fileNameEdit'"
        assert buttonParent is not None, "To parent button was not found with name 'toParentButton'"
        self._qtest.qWait(200)
        self._qtest.mouseClick(buttonParent, Qt.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(0, 0))
        self._qtest.qWait(2000)
        self._qtest.keyClick(edit, Qt.Key_C)
        self._qtest.qWait(200)
        self._qtest.keyClick(edit.completer().popup(), Qt.Key_Down)
        self._qtest.qWait(200)
        assert edit.text() == "C:/", f"File name edit was not correct, expected: 'C:/', got: {edit.text()!r}"
        self._qtest.qWait(2000)
        self._qtest.keyClick(edit.completer().popup(), Qt.Key_Down)
        edit.clear()
        self._qtest.keyClick(edit, Qt.Key_C, Qt.ShiftModifier)
        self._qtest.qWait(200)
        self._qtest.keyClick(edit.completer().popup(), Qt.Key_Down)
        assert edit.text() == "C:/", f"File name edit was not correct, expected: 'C:/', got: {edit.text()!r}"

    def test_completionOnLevelAfterRoot(self):  # noqa: C901
        fd = self.fd_class()
        fd.setDirectory("C:/")
        current: QDir = fd.directory()
        entryList: list[str] = current.entryList([], QDir.Dirs)
        testDir = ""
        for entry in entryList:
            if len(entry) > 5 and entry.isascii() and entry.isalpha():
                invalid = False
                for i in range(5):
                    if not entry[i].isalpha():
                        invalid = True
                        break
                if not invalid:
                    for check in entryList:
                        if check.startswith(entry[:5]) and check != entry:
                            invalid = True
                            break
                if not invalid:
                    testDir = entry
                    break
        if not testDir:
            self.skipTest("This test requires to have a unique directory of at least six ascii characters under c:/")
        fd.show()
        edit: QLineEdit | None = fd.findChild(QLineEdit, "fileNameEdit")
        assert edit is not None, "File name edit was not found with name 'fileNameEdit'"
        self._qtest.qWait(2000)
        for i in range(5):
            self._qtest.keyClick(edit, testDir[i].lower())
        self._qtest.qWait(200)
        self._qtest.keyClick(edit.completer().popup(), Qt.Key_Down)
        self._qtest.qWait(200)
        assert edit.text() == testDir, f"File name edit was not correct, expected: {testDir!r}, got: {edit.text()!r}"

    def test_task233037_selectingDirectory(self):
        current = QDir(QDir.currentPath())
        current.mkdir("test")
        fd = self.fd_class()
        fd.setViewMode(self.fd_class.List)
        fd.setDirectory(current.absolutePath())
        fd.setAcceptMode(self.fd_class.AcceptSave)
        fd.show()
        listView: QListView | None = fd.findChild(QListView, "listView")
        assert listView is not None, "List view was not found with name 'listView'"
        self._qtest.qWait(3000)
        self._qtest.keyClick(listView, Qt.Key.Key_Down)
        buttonBox: QDialogButtonBox | None = fd.findChild(QDialogButtonBox, "buttonBox")
        assert buttonBox is not None, "Button box was not found with name 'buttonBox'"
        button: QPushButton = buttonBox.button(QDialogButtonBox.Save)
        assert button is not None, "Save button was not found with name 'Save'"
        assert button.isEnabled(), "Save button was not enabled"
        current.rmdir("test")

    def test_task235069_hideOnEscape_data(self):
        self.addColumn("childName", str)
        self.addColumn("viewMode", self.fd_class.ViewMode)
        self.newRow("listView").setData("listView", self.fd_class.List)
        self.newRow("fileNameEdit").setData("fileNameEdit", self.fd_class.List)
        self.newRow("treeView").setData("treeView", self.fd_class.Detail)

    def test_task235069_hideOnEscape(self):
        childName = str(self.getData("childName"))
        viewMode = self.getData("viewMode")
        assert isinstance(viewMode, self.fd_class.ViewMode), f"View mode was not correct, expected: {self.fd_class.ViewMode}, got: {viewMode}"
        current = QDir(QDir.currentPath())
        fd = self.fd_class()
        spyFinished = QSignalSpy(fd, fd.finished)
        assert spyFinished.isValid(), f"QSignalSpy was not valid for {childName}, expected valid fd.finished signal"
        spyRejected = QSignalSpy(fd, fd.rejected)
        assert spyRejected.isValid(), f"QSignalSpy was not valid for {childName}, expected valid fd.rejected signal"
        fd.setViewMode(viewMode)
        fd.setDirectory(current.absolutePath())
        fd.setAcceptMode(self.fd_class.AcceptSave)
        fd.show()
        self._qtest.qWaitForWindowExposed(fd)
        child: QWidget | None = fd.findChild(QWidget, childName)
        assert child is not None, f"Child widget was not found with name '{childName}'"
        child.setFocus()
        self._qtest.keyClick(child, Qt.Key_Escape)
        assert not fd.isVisible(), "File dialog was visible"
        assert len(spyFinished) == 1, "QTBUG-7690"  # reject(), don't hide()

    def test_task236402_dontWatchDeletedDir(self):
        # THIS TEST SHOULD NOT DISPLAY WARNINGS
        current = QDir(QDir.currentPath())
        # make sure it is the first on the list
        current.mkdir("aaaaaaaaaa")
        fd = self.fd_class()  # Friendlyself.dialog_class()
        fd.setViewMode(self.fd_class.List)
        fd.setDirectory(current.absolutePath())
        fd.setAcceptMode(self.fd_class.AcceptSave)
        fd.show()
        self._qtest.qWaitForWindowExposed(fd)
        listView: QListView | None = fd.findChild(QListView, "listView")
        assert listView is not None, "List view was not found"
        listView.setFocus()
        self._qtest.keyClick(listView, Qt.Key.Key_Return)
        self._qtest.keyClick(listView, Qt.Key.Key_Backspace)
        self._qtest.keyClick(listView, Qt.Key.Key_Down)
        fd.d_func().removeDirectory(os.path.join(current.absolutePath(), "aaaaaaaaaa"))  # noqa: PTH118
        self._qtest.qWait(1000)

    def test_task203703_returnProperSeparator(self):
        current = QDir(QDir.currentPath())
        current.mkdir("aaaaaaaaaaaaaaaaaa")
        fd = self.fd_class()
        fd.setDirectory(current.absolutePath())
        fd.setViewMode(self.fd_class.List)
        fd.setFileMode(self.fd_class.Directory)
        fd.show()
        self._qtest.qWaitForWindowExposed(fd)
        listView: QListView | None = fd.findChild(QListView, "listView")
        assert listView is not None, "List view was not found with name 'listView'"
        listView.setFocus()
        self._qtest.keyClick(listView, Qt.Key.Key_Return)
        buttonBox: QDialogButtonBox | None = fd.findChild(QDialogButtonBox, "buttonBox")
        assert buttonBox is not None, "Button box was not found with name 'buttonBox'"
        button = buttonBox.button(QDialogButtonBox.Cancel)
        assert button is not None, "Cancel button was not found with name 'Cancel'"
        self._qtest.keyClick(button, Qt.Key.Key_Return)
        result: str = fd.selectedFiles()[0]
        assert result[-1] != "/", f"Result was not a directory, got: {result!r}"
        assert "\\" not in result, f"Result was not a directory, got: {result!r}"
        current.rmdir("aaaaaaaaaaaaaaaaaa")

    def test_task228844_ensurePreviousSorting(self):
        current = QDir(QDir.currentPath())
        current.mkdir("aaaaaaaaaaaaaaaaaa")
        current.cd("aaaaaaaaaaaaaaaaaa")
        current.mkdir("a")
        current.mkdir("b")
        current.mkdir("c")
        current.mkdir("d")
        current.mkdir("e")
        current.mkdir("f")
        current.mkdir("g")
        tempFile = QTemporaryFile(current.absolutePath() + "/rXXXXXX")
        assert tempFile.open(), f"Temporary file was not opened, got: {tempFile.errorString()!r}"
        current.cdUp()

        fd = self.fd_class()
        fd.setDirectory(current.absolutePath())
        fd.setViewMode(self.fd_class.Detail)
        fd.show()
        self._qtest.qWaitForWindowExposed(fd)
        tree: QTreeView | None = fd.findChild(QTreeView, "treeView")
        assert tree is not None, "Tree view was not found with name 'treeView'"
        tree.header().setSortIndicator(3, Qt.SortOrder.DescendingOrder)
        buttonBox: QDialogButtonBox | None = fd.findChild(QDialogButtonBox, "buttonBox")
        assert buttonBox is not None, "Button box was not found with name 'buttonBox'"
        button: QPushButton = buttonBox.button(QDialogButtonBox.StandardButton.Open)
        assert button is not None, "Open button was not found with name 'Open'"
        self._qtest.mouseClick(button, Qt.MouseButton.LeftButton)
        fd2 = self.fd_class()
        fd2.setFileMode(self.fd_class.Directory)
        fd2.restoreState(fd.saveState())
        current.cd("aaaaaaaaaaaaaaaaaa")
        fd2.setDirectory(current.absolutePath())
        fd2.show()
        self._qtest.qWaitForWindowExposed(fd2)
        tree2: QTreeView | None = fd2.findChild(QTreeView, "treeView")
        assert tree2 is not None, "Tree view was not found with name 'treeView'"
        tree2.setFocus()

        assert (
            tree2.rootIndex().data(QFileSystemModel.Roles.FilePathRole) == current.absolutePath()
        ), f"Root index was not correct, expected: {current.absolutePath()!r}, got: {tree2.rootIndex().data(QFileSystemModel.Roles.FilePathRole)!r}"

        buttonBox2: QDialogButtonBox | None = fd2.findChild(QDialogButtonBox, "buttonBox")
        assert buttonBox2 is not None, "Button box was not found with name 'buttonBox'"
        button2: QPushButton = buttonBox2.button(QDialogButtonBox.StandardButton.Open)
        assert button2 is not None, "Open button was not found with name 'Open'"
        fd2.selectFile("g")
        self._qtest.mouseClick(button2, Qt.MouseButton.LeftButton)
        assert (
            fd2.selectedFiles()[0] == current.absolutePath() + "/g"
        ), f"Selected file was not correct, expected: {current.absolutePath() + '/g'!r}, got: {fd2.selectedFiles()[0]!r}"

        fd3 = self.fd_class(None, "This is a third file dialog", tempFile.fileName())
        fd3.restoreState(fd.saveState())
        fd3.setFileMode(self.fd_class.Directory)
        fd3.show()
        self._qtest.qWaitForWindowExposed(fd3)
        tree3: QTreeView | None = fd3.findChild(QTreeView, "treeView")
        assert tree3 is not None, "Tree view was not found with name 'treeView'"
        tree3.setFocus()

        assert (
            tree3.rootIndex().data(QFileSystemModel.Roles.FilePathRole) == current.absolutePath()
        ), f"Root index was not correct, expected: {current.absolutePath()!r}, got: {tree3.rootIndex().data(QFileSystemModel.Roles.FilePathRole)!r}"

        buttonBox3: QDialogButtonBox | None = fd3.findChild(QDialogButtonBox, "buttonBox")
        assert buttonBox3 is not None, "Button box was not found with name 'buttonBox'"
        button3: QPushButton = buttonBox3.button(QDialogButtonBox.StandardButton.Open)
        assert button3 is not None, "Open button was not found with name 'Open'"
        self._qtest.mouseClick(button3, Qt.MouseButton.LeftButton)
        assert fd3.selectedFiles()[0] == tempFile.fileName(), f"Selected file was not correct, expected: {tempFile.fileName()!r}, got: {fd3.selectedFiles()[0]!r}"

        current.cd("aaaaaaaaaaaaaaaaaa")
        current.rmdir("a")
        current.rmdir("b")
        current.rmdir("c")
        current.rmdir("d")
        current.rmdir("e")
        current.rmdir("f")
        current.rmdir("g")
        tempFile.close()
        del tempFile
        current.cdUp()
        current.rmdir("aaaaaaaaaaaaaaaaaa")

    def test_task239706_editableFilterCombo(self):
        d = self.fd_class()
        d.setNameFilter("*.cpp *.h")
        d.show()
        self._qtest.qWaitForWindowExposed(d)

        comboList: list[QComboBox] = d.findChildren(QComboBox)
        filterCombo: QComboBox | None = None
        for combo in comboList:
            if combo.objectName() == "fileTypeCombo":
                filterCombo = combo
                break
        assert filterCombo is not None, "Filter combo was not found with name 'fileTypeCombo'"
        filterCombo.setEditable(True)
        self._qtest.mouseClick(filterCombo, Qt.MouseButton.LeftButton)
        self._qtest.keyPress(filterCombo, Qt.Key.Key_X)
        self._qtest.keyPress(filterCombo, Qt.Key.Key_Enter)  # should not trigger assertion failure

    def test_task218353_relativePaths(self):
        appDir: QDir = QDir.current()
        assert appDir.cdUp(), "Failed to cd up"
        d = self.fd_class(None, "TestDialog", "..")
        assert d.directory().absolutePath() == appDir.absolutePath(), f"Directory was not correct, expected: {appDir.absolutePath()!r}, got: {d.directory().absolutePath()!r}"

        d.setDirectory(appDir.absolutePath() + "/non-existing-directory/../another-non-existing-dir/../")
        assert d.directory().absolutePath() == appDir.absolutePath(), f"Directory was not correct, expected: {appDir.absolutePath()!r}, got: {d.directory().absolutePath()!r}"

        QDir.current().mkdir("test")
        appDir = QDir.current()
        d.setDirectory(appDir.absolutePath() + "/test/../test/../")
        assert d.directory().absolutePath() == appDir.absolutePath(), f"Directory was not correct, expected: {appDir.absolutePath()!r}, got: {d.directory().absolutePath()!r}"
        appDir.rmdir("test")

    def test_task251321_sideBarHiddenEntries(self):
        fd = self.fd_class()

        current = QDir(QDir.currentPath())
        current.mkdir(".hidden")
        hiddenDir = QDir(".hidden")
        hiddenDir.mkdir("subdir")
        hiddenSubDir = QDir(".hidden/subdir")
        hiddenSubDir.mkdir("happy")
        hiddenSubDir.mkdir("happy2")

        urls: list[QUrl] = [QUrl.fromLocalFile(hiddenSubDir.absolutePath())]
        fd.setSidebarUrls(urls)
        fd.show()
        self._qtest.qWaitForWindowExposed(fd)

        sidebar: QSidebar | None = fd.findChild(QSidebar, "sidebar")
        assert sidebar is not None, "Sidebar was not found with name 'sidebar'"
        sidebar.setFocus()
        sidebar.selectUrl(QUrl.fromLocalFile(hiddenSubDir.absolutePath()))
        self._qtest.mouseClick(sidebar.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, sidebar.visualRect(sidebar.model().index(0, 0)).center())
        self._qtest.qWait(250)

        model: QFileSystemModel | None = fd.findChild(QFileSystemModel, "qt_filesystem_model")
        assert model is not None, "Model was not found with name 'qt_filesystem_model'"
        assert (
            model.rowCount(model.index(hiddenSubDir.absolutePath())) == 2
        ), f"Row count was not correct, expected: 2, got: {model.rowCount(model.index(hiddenSubDir.absolutePath()))!r}"

        hiddenSubDir.rmdir("happy2")
        hiddenSubDir.rmdir("happy")
        hiddenDir.rmdir("subdir")
        QDir(current).rmdir(".hidden")

    def test_task251341_sideBarRemoveEntries(self):
        fd = self.fd_class()

        current = QDir(QDir.currentPath())
        current.mkdir("testDir")
        testSubDir = QDir("testDir")

        urls: list[QUrl] = [QUrl.fromLocalFile(testSubDir.absolutePath()), QUrl.fromLocalFile("NotFound")]
        fd.setSidebarUrls(urls)
        fd.show()
        self._qtest.qWaitForWindowExposed(fd)

        sidebar: QSidebar | None = fd.findChild(QSidebar, "sidebar")
        assert sidebar is not None, "Sidebar was not found with name 'sidebar'"
        sidebar.setFocus()
        sidebar.selectUrl(QUrl.fromLocalFile(testSubDir.absolutePath()))
        self._qtest.mouseClick(sidebar.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, sidebar.visualRect(sidebar.model().index(0, 0)).center())

        model: QFileSystemModel | None = fd.findChild(QFileSystemModel, "qt_filesystem_model")
        assert model is not None, "Model was not found with name 'qt_filesystem_model'"
        assert (
            model.rowCount(model.index(testSubDir.absolutePath())) == 0
        ), f"Row count was not correct, expected: 0, got: {model.rowCount(model.index(testSubDir.absolutePath()))!r}"
        value = sidebar.model().index(0, 0).data(Qt.ItemDataRole.UserRole + 2)
        assert value, "Value was not correct"

        sidebar.setFocus()
        sidebar.selectUrl(QUrl.fromLocalFile("NotFound"))
        self._qtest.mouseClick(sidebar.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, sidebar.visualRect(sidebar.model().index(1, 0)).center())

        assert model.rowCount(model.index("NotFound")) == model.rowCount(
            model.index(model.rootPath())
        ), f"Row count was not correct, expected: {model.rowCount(model.index(model.rootPath()))!r}, got: {model.rowCount(model.index('NotFound'))!r}"
        value = sidebar.model().index(1, 0).data(Qt.ItemDataRole.UserRole + 2)
        assert not value, "Value was not correct"

        mySideBar: QSidebar | None = QSidebar()  # MyQSideBar
        mySideBar.setModelAndUrls(model, urls)
        mySideBar.show()
        mySideBar.selectUrl(QUrl.fromLocalFile(testSubDir.absolutePath()))
        self._qtest.qWait(1000)
        mySideBar.removeSelection()

        expected: list[QUrl] = [QUrl.fromLocalFile("NotFound")]
        assert mySideBar.urls() == expected, f"Urls were not correct, got: {mySideBar.urls()!r}, expected: {expected!r}"

        mySideBar.selectUrl(QUrl.fromLocalFile("NotFound"))
        mySideBar.removeSelection()

        expected = []
        assert mySideBar.urls() == expected, f"Urls were not correct, got: {mySideBar.urls()!r}, expected: {expected!r}"

        current.rmdir("testDir")

    def test_task254490_selectFileMultipleTimes(self):
        tempPath: Path = self.temp_path
        t = QTemporaryFile()
        assert t.open()
        t.open()
        fd = self.fd_class(None, "TestFileDialog")

        fd.setDirectory(tempPath)
        fd.setViewMode(self.fd_class.List)
        fd.setAcceptMode(self.fd_class.AcceptSave)
        fd.setFileMode(self.fd_class.AnyFile)

        fd.selectFile(t.fileName())
        fd.selectFile("new_file.txt")

        fd.show()
        self._qtest.qWaitForWindowExposed(fd)

        lineEdit: QLineEdit | None = fd.findChild(QLineEdit, "fileNameEdit")
        assert lineEdit is not None, "Line edit was not found"
        assert lineEdit.text() == "new_file.txt", "Line edit text was not correct"
        listView: QListView | None = fd.findChild(QListView, "listView")
        assert listView is not None, "List view was not found"
        assert listView.selectionModel().selectedRows(0) == [], "Selected rows were not correct"

        t.close()

    def test_task257579_sideBarWithNonCleanUrls(self):
        qdir = QDir(str(self.temp_path))
        dirname = "autotest_task257579"
        qdir.rmdir(dirname)
        assert qdir.mkdir(dirname)
        url = os.path.join(qdir.absolutePath(), dirname, "..")  # noqa: FBT003
        fd = self.fd_class()
        fd.setSidebarUrls([QUrl.fromLocalFile(url)])
        sidebar: QSidebar | None = fd.findChild(QSidebar, "sidebar")
        assert sidebar is not None, "Sidebar was not found"
        assert len(sidebar.urls()) == 1, "Sidebar urls were not correct"
        assert sidebar.urls()[0].toLocalFile() != url, "Sidebar urls were not correct"
        assert sidebar.urls()[0].toLocalFile() == QDir.cleanPath(url), "Sidebar urls were not correct"

        assert str(sidebar.model().index(0, 0).data()).lower() == qdir.dirName().lower(), "Sidebar model index was not correct"

        assert qdir.rmdir(dirname), "Directory was not removed"

    def test_task259105_filtersCornerCases(self):
        fd = self.fd_class(None, "TestFileDialog")
        fd.setNameFilter("All Files! (*);;Text Files (*.txt)")
        fd.setOption(self.fd_class.HideNameFilterDetails, True)  # noqa: FBT003
        fd.show()
        self._qtest.qWaitForWindowExposed(fd)

        filters: QComboBox | None = fd.findChild(QComboBox, "fileTypeCombo")
        assert filters is not None
        assert filters.currentText() == "All Files!"
        filters.setCurrentIndex(1)
        assert filters.currentText() == "Text Files"

        fd.setOption(self.fd_class.HideNameFilterDetails, False)  # noqa: FBT003
        filters.setCurrentIndex(0)
        assert filters.currentText() == "All Files! (*)"
        filters.setCurrentIndex(1)
        assert filters.currentText() == "Text Files (*.txt)"

        fd.setNameFilter("é (I like cheese) All Files! (*);;Text Files (*.txt)")
        assert filters.currentText() == "é (I like cheese) All Files! (*)"
        filters.setCurrentIndex(1)
        assert filters.currentText() == "Text Files (*.txt)"

        fd.setOption(self.fd_class.HideNameFilterDetails, True)  # noqa: FBT003
        filters.setCurrentIndex(0)
        assert filters.currentText() == "é (I like cheese) All Files!"
        filters.setCurrentIndex(1)
        assert filters.currentText() == "Text Files"

    def test_QTBUG4419_lineEditSelectAll(self):
        # if not QGuiApplicationPrivate.platformIntegration().hasCapability(QPlatformIntegration.WindowActivation):
        #    self.skipTest("Window activation is not supported")

        tempPath = self.temp_path
        temporaryFile = QTemporaryFile(str(tempPath / "tst_qfiledialog2_lineEditSelectAll.XXXXXX"))
        assert temporaryFile.open(), f"Temporary file was not opened, got: {temporaryFile.errorString()!r}"
        fd = self.fd_class(None, "TestFileDialog", temporaryFile.fileName())

        fd.setDirectory(str(tempPath))
        fd.setViewMode(self.fd_class.ViewMode.List)
        fd.setAcceptMode(self.fd_class.AcceptMode.AcceptSave)
        fd.setFileMode(self.fd_class.FileMode.AnyFile)

        fd.show()
        fd.activateWindow()
        assert self._qtest.qWaitForWindowActive(fd), "File dialog was not active"
        assert fd.isVisible(), "File dialog was not visible"
        assert self.app.activeWindow() == fd, "Active window was not correct"

        lineEdit: QLineEdit | None = fd.findChild(QLineEdit, "fileNameEdit")
        assert lineEdit is not None, "Line edit was not found"

        self.app.processEvents()  # Equivalent to QTRY_COMPARE
        assert tempPath / lineEdit.text() == Path(temporaryFile.fileName()), f"Line edit text was not correct: '{lineEdit.text()!r}'"
        assert tempPath / lineEdit.selectedText() == Path(temporaryFile.fileName()), f"Line edit selected text was not correct: '{lineEdit.selectedText()!r}'"

    def test_QTBUG6558_showDirsOnly(self):
        # if not QGuiApplicationPrivate.platformIntegration().hasCapability(QPlatformIntegration.WindowActivation):
        #    self.skipTest("Window activation is not supported")

        temp_path = self.temp_path
        dir_temp = QDir(str(temp_path))
        temp_name = f"showDirsOnly.{QRandomGenerator.global_().generate()}"
        dir_temp.mkdir(temp_name)
        dir_temp.cd(temp_name)
        self.app.processEvents()  # Equivalent to QTRY_VERIFY
        assert dir_temp.exists(), "Directory was not created"

        dir_path = dir_temp.absolutePath()
        qdirpath = QDir(dir_path)

        # Create two dirs
        qdirpath.mkdir("a")
        qdirpath.mkdir("b")

        # Create a file
        with open(dir_path + "/plop.txt", "w") as temp_file:
            temp_file.write("The magic number is: 49\n")

        fd = self.fd_class(None, "TestFileDialog")

        fd.setDirectory(qdirpath.absolutePath())
        fd.setViewMode(self.fd_class.ViewMode.List)
        fd.setAcceptMode(self.fd_class.AcceptMode.AcceptSave)
        fd.setOption(self.fd_class.Option.ShowDirsOnly, True)
        fd.show()

        self.app.setActiveWindow(fd)
        assert self._qtest.qWaitForWindowActive(fd), "File dialog was not active"
        assert fd.isVisible()
        assert self.app.activeWindow() == fd

        model: QFileSystemModel | None = fd.findChild(QFileSystemModel, "qt_filesystem_model")
        assert model is not None, "Model was not found"
        self.app.processEvents()  # Equivalent to QTRY_COMPARE
        assert model.rowCount(model.index(qdirpath.absolutePath())) == 2

        fd.setOption(self.fd_class.Option.ShowDirsOnly, False)  # noqa: FBT003
        self.app.processEvents()  # Equivalent to QTRY_COMPARE
        assert model.rowCount(model.index(qdirpath.absolutePath())) == 3

        fd.setOption(self.fd_class.Option.ShowDirsOnly, True)  # noqa: FBT003
        self.app.processEvents()  # Equivalent to QTRY_COMPARE
        assert model.rowCount(model.index(qdirpath.absolutePath())) == 2
        assert bool(fd.options() & self.fd_class.Option.ShowDirsOnly)

        fd.setDirectory(QDir.homePath())

        # Cleanup handled in tearDown

    def test_QTBUG4842_selectFilterWithHideNameFilterDetails(self):
        # if not QGuiApplicationPrivate.platformIntegration().hasCapability(QPlatformIntegration.WindowActivation):
        #    self.skipTest("Window activation is not supported")

        filtersStr: list[str] = ["Images (*.png *.xpm *.jpg)", "Text files (*.txt)", "XML files (*.xml)"]
        chosenFilterString = "Text files (*.txt)"

        fd = self.fd_class(None, "TestFileDialog")
        fd.setAcceptMode(self.fd_class.AcceptMode.AcceptSave)
        fd.setOption(self.fd_class.Option.HideNameFilterDetails, True)  # noqa: FBT003
        fd.setNameFilters(filtersStr)
        fd.selectNameFilter(chosenFilterString)
        fd.show()

        self.app.setActiveWindow(fd)
        assert self._qtest.qWaitForWindowActive(fd), "File dialog was not active"
        assert fd.isVisible(), "File dialog was not visible"
        assert self.app.activeWindow() == fd, "Active window was not correct"

        filters = fd.findChild(QComboBox, "fileTypeCombo")
        assert filters is not None, "Filters were not found"
        assert filters.currentText() == "Text files", f"Filters were not correct: '{filters.currentText()!r}'"

        fd2 = self.fd_class(None, "TestFileDialog")
        fd2.setAcceptMode(self.fd_class.AcceptMode.AcceptSave)
        fd2.setOption(self.fd_class.Option.HideNameFilterDetails, False)  # noqa: FBT003
        fd2.setNameFilters(filtersStr)
        fd2.selectNameFilter(chosenFilterString)
        fd2.show()

        assert self._qtest.qWaitForWindowActive(fd2), "File dialog was not active"
        assert fd2.isVisible(), "File dialog was not visible"
        assert self.app.activeWindow() == fd2, "Active window was not correct"

        filters2 = fd2.findChild(QComboBox, "fileTypeCombo")
        assert filters2 is not None, "Filters were not found"
        assert filters2.currentText() == chosenFilterString, f"Filters were not correct: '{filters2.currentText()!r}'"

    def test_dontShowCompleterOnRoot(self):
        # if not QGuiApplicationPrivate.platformIntegration().hasCapability(QPlatformIntegration.WindowActivation):
        #    self.skipTest("Window activation is not supported")

        fd = self.fd_class(None, "TestFileDialog")
        fd.setAcceptMode(self.fd_class.AcceptMode.AcceptSave)
        fd.show()

        self.app.setActiveWindow(fd)
        assert self._qtest.qWaitForWindowActive(fd), "File dialog was not active"
        assert fd.isVisible(), "File dialog was not visible"
        assert self.app.activeWindow() == fd, "Active window was not correct"

        fd.setDirectory("")
        lineEdit = fd.findChild(QLineEdit, "fileNameEdit")
        assert lineEdit is not None, "Line edit was not found"
        self.app.processEvents()  # Equivalent to QTRY_VERIFY
        assert lineEdit.text() == "", f"Line edit text was not correct: '{lineEdit.text()!r}'"

        self.app.processEvents()

        self.app.processEvents()  # Equivalent to QTRY_VERIFY
        completer = lineEdit.completer()
        assert completer is not None, "Completer was not found"
        assert completer.popup().isHidden(), "Completer was not hidden"

    def test_nameFilterParsing_data(self):
        fd = self.fd_class()
        self.addColumn("filterString", str)
        self.addColumn("filters", list)

        self.newRow("text").setData(
            "plain text document (*.txt *.asc *,v *.doc)",
            ["*.txt", "*.asc", "*,v", "*.doc"],
        )
        self.newRow("html").setData(
            "HTML document (*.html *.htm)",
            ["*.html", "*.htm"],
        )
        filterString = self.getData("filterString")
        filters = self.getData("filters")
        assert QPlatformFileDialogHelper.cleanFilterList(filterString) == filters, "Filters were not correct"


FORCE_UNITTEST = False
VERBOSE = True
FAIL_FAST = False


def run_tests():
    print("Running tests of TestQFileDialog2")
    try:
        import pytest

        if not FORCE_UNITTEST:
            if VERBOSE:
                if FAIL_FAST:
                    pytest.main(["-v", "-x", "--tb=native", __file__])
                else:
                    pytest.main(["-v", "--tb=native", __file__])
            elif FAIL_FAST:
                pytest.main(["-x", "--tb=native", __file__])
            else:
                pytest.main(["--tb=native", __file__])
        else:
            raise ImportError  # noqa: TRY301
    except ImportError:
        unittest.main(verbosity=2 if VERBOSE else 1, failfast=FAIL_FAST)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    QTimer.singleShot(0, run_tests)
    app.exec()
