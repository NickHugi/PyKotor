from __future__ import annotations

import os
import sys
import tempfile
import unittest

from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import pytest

from qtpy.QtCore import (
    QAbstractItemModel,
    QDir,
    QEventLoop,
    QItemSelectionModel,
    QModelIndex,
    QObject,
    QSettings,
    QSortFilterProxyModel,
    QStandardPaths,
    QTemporaryDir,
    QTemporaryFile,
    QTime,
    QTimer,
    Qt,
    Slot,
)
from qtpy.QtGui import QCursor, QGuiApplication
from qtpy.QtTest import QSignalSpy, QTest
from qtpy.QtWidgets import (
    QAction,
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog as RealQFileDialog,
    QFileIconProvider,
    QFileSystemModel,
    QItemDelegate,
    QLineEdit,
    QListView,
    QPushButton,
    QToolButton,
    QTreeView,
    QWidget,
)

from utility.ui_libraries.qt.adapters.filesystem.qfiledialog.rewritten.private.qsidebar import QSidebar
from utility.ui_libraries.qt.adapters.filesystem.qfiledialog.rewritten.qfiledialog import QFileDialog as PythonQFileDialog

if TYPE_CHECKING:
    from qtpy.QtCore import QAbstractItemModel, QModelIndex, QUrl
    from qtpy.QtGui import QWindow
    from qtpy.QtWidgets import QCompleter
    from typing_extensions import Literal

class DialogRejecter(QObject):
    def __init__(self):
        super().__init__()
        QApplication.instance().focusChanged.connect(self.reject_file_dialog)

    @Slot()
    def reject_file_dialog(self):
        w = QApplication.activeModalWidget()
        if w and isinstance(w, QDialog):
            QTest.keyClick(w, Qt.Key.Key_Escape)


class qtbug57193DialogRejecter(DialogRejecter):  # noqa: N801
    def reject_file_dialog(self):
        top_level_windows: list[QWindow] = QGuiApplication.topLevelWindows()
        assert len(top_level_windows) == 1
        window: QWindow = top_level_windows[0]

        file_dialog: QWidget | None = QApplication.activeModalWidget()
        if not isinstance(file_dialog, RealQFileDialog):
            return

        # The problem in QTBUG-57193 was from a platform input context plugin that was
        # connected to QWindow::focusObjectChanged(), and consequently accessed the focus
        # object (the QFileDialog) that was in the process of being destroyed. This test
        # checks that the QFileDialog is never set as the focus object after its destruction process begins.
        window.focusObjectChanged.connect(lambda focus_object: unittest.TestCase().assertIsNot(focus_object, file_dialog))  # noqa: PT009
        super().reject_file_dialog()


class TestQFileDialog(unittest.TestCase):
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
        self.fd_class: type[PythonQFileDialog] = PythonQFileDialog
        self._test_data: dict[str, list[Any]] = {}
        self._current_row: str | None = None
        self._qtest: type[QTest] = QTest  # TypeError: PyQt5.QtTest.QTest represents a C++ namespace and cannot be instantiated

    def tearDown(self):
        self.temp_dir.cleanup()
        for widget in self.app.topLevelWidgets():
            widget.close()
            widget.deleteLater()
        # Clean up sidebar settings
        settings = QSettings(QSettings.Scope.UserScope, "QtProject")
        settings.beginGroup("FileDialog")
        settings.remove("")
        settings.endGroup()
        settings.beginGroup("Qt")
        settings.remove("filedialog")
        settings.endGroup()
        self._qtest.qWait(200)

    @staticmethod
    def wait_for_dir_populated(list_view: QListView, needle: str) -> bool:
        timeout = 5000  # Total timeout in ms
        wait_interval = 100  # Interval in ms
        elapsed_time = 0

        while elapsed_time < timeout:
            model: QAbstractItemModel = list_view.model()
            root: QModelIndex = list_view.rootIndex()
            for r in range(model.rowCount(root)):
                if needle == model.index(r, 0, root).data(Qt.ItemDataRole.DisplayRole):
                    return True
            QTest.qWait(100)
            elapsed_time += wait_interval
        return False

    @staticmethod
    def select_dir_test(list_view: QListView, needle: str) -> bool:
        for _ in range(50):  # Adjust timeout as needed
            if needle == list_view.currentIndex().data(Qt.ItemDataRole.DisplayRole):
                return True
            QTest.keyClick(list_view, Qt.Key.Key_Down)
            QTest.qWait(100)
        return False

    def test_currentChangedSignal(self):
        fd = PythonQFileDialog()
        fd.setViewMode(RealQFileDialog.ViewMode.List)
        spyCurrentChanged = QSignalSpy(fd._private.qFileDialogUi.listView.selectionModel().currentChanged)

        listView: QListView | None = fd.findChild(QListView, "listView")
        assert listView is not None, "QListView not found with name 'listView'"
        assert listView
        fd.setDirectory(QDir.root())
        root = listView.rootIndex()
        self.app.processEvents(QEventLoop.ProcessEventsFlag.AllEvents)
        assert listView.model().rowCount(root) > 0

        folder = None
        for i in range(listView.model().rowCount(root)):
            folder = listView.model().index(i, 0, root)
            if listView.model().hasChildren(folder):
                break
        assert folder is not None
        assert listView.model().hasChildren(folder)
        listView.setCurrentIndex(folder)

        assert len(spyCurrentChanged) == 1

    def test_directoryEnteredSignal(self):
        fd = PythonQFileDialog(None, "", QDir.root().path())
        fd.setViewMode(RealQFileDialog.ViewMode.List)
        spyDirectoryEntered = QSignalSpy(fd.directoryEntered)

        sidebar: QSidebar | None = fd.findChild(QSidebar, "sidebar")
        assert sidebar is not None, "QSidebar not found with name 'sidebar'"
        assert sidebar
        if sidebar.model().rowCount() < 2:
            self.skipTest("This test requires at least 2 side bar entries.")

        fd.show()
        assert fd.isVisible()

        # sidebar
        second_item: QModelIndex = sidebar.model().index(1, 0)
        assert second_item.isValid()
        sidebar.setCurrentIndex(second_item)
        self._qtest.keyPress(sidebar.viewport(), Qt.Key.Key_Return)
        assert len(spyDirectoryEntered) == 1
        spyDirectoryEntered = QSignalSpy(fd.directoryEntered)  # clear

        # lookInCombo
        combo_box: QComboBox | None = fd.findChild(QComboBox, "lookInCombo")
        assert combo_box is not None
        combo_box.showPopup()
        assert combo_box.view().model().index(1, 0).isValid()
        combo_box.view().setCurrentIndex(combo_box.view().model().index(1, 0))
        self._qtest.keyPress(combo_box.view().viewport(), Qt.Key.Key_Return)
        assert len(spyDirectoryEntered) == 1

    @pytest.mark.parametrize(
        "file_mode",
        [
            RealQFileDialog.FileMode.AnyFile,
            RealQFileDialog.FileMode.ExistingFile,
            RealQFileDialog.FileMode.Directory,
            RealQFileDialog.FileMode.ExistingFiles,
        ],
    )
    def test_filesSelectedSignal(
        self,
        file_mode: RealQFileDialog.FileMode = RealQFileDialog.FileMode.AnyFile,
    ):
        # Create temporary files and directories
        file1 = self.temp_path / "file1.txt"
        file1.touch()
        file2 = self.temp_path / "file2.txt"
        file2.touch()
        dir1 = self.temp_path / "dir1"
        dir1.mkdir()
        dir2 = self.temp_path / "dir2"
        dir2.mkdir()
        file3 = dir1 / "file3.txt"
        file3.touch()
        fd = PythonQFileDialog()
        fd.setViewMode(RealQFileDialog.ViewMode.List)
        test_dir = QDir(str(self.temp_path))
        fd.setDirectory(test_dir)
        fd.setFileMode(file_mode)
        spyFilesSelected = QSignalSpy(fd.filesSelected)

        fd.show()
        self._qtest.qWaitForWindowExposed(fd)
        list_view: QListView | None = fd.findChild(QListView, "listView")
        assert list_view is not None, "QListView not found with name 'listView'"
        fs_model: QAbstractItemModel = list_view.model()
        assert isinstance(fs_model, QFileSystemModel), f"List view model is not a QFileSystemModel, was instead {type(fs_model).__name__}"
        assert fs_model is fd._private.model, "List view model is not the main filesystem model"  # noqa: SLF001

        root: QModelIndex = list_view.rootIndex()
        assert fs_model.rowCount() > 0, "List view model is empty."
        assert fs_model.rowCount(root) > 0, "List view model is empty under root."
        file: QModelIndex | None = None
        for i in range(fs_model.rowCount(root)):
            file = fs_model.index(i, 0, root)
            if file_mode == RealQFileDialog.FileMode.Directory:
                if fs_model.hasChildren(file):
                    break
            elif not fs_model.hasChildren(file):
                break
        assert file is not None, "file cannot be None"
        assert file.isValid(), "No valid file found"
        current_index_spy = QSignalSpy(fd.currentChanged)
        list_view.selectionModel().select(file, QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows)
        list_view.setCurrentIndex(file)

        button_box: QDialogButtonBox | None = fd.findChild(QDialogButtonBox, "buttonBox")
        assert button_box is not None, "QDialogButtonBox not found with name 'buttonBox'"
        button: QPushButton | None = button_box.button(QDialogButtonBox.StandardButton.Open)
        assert button is not None, "Open button not found"
        assert button.isEnabled(), "Open button is not enabled"
        button.animateClick()

        self.app.processEvents()  # Process events
        self._qtest.qWait(100)
        assert not fd.isVisible(), "File dialog is still visible after clicking Open"
        assert len(spyFilesSelected) == 1, "filesSelected signal was not emitted exactly once"

    def test_filterSelectedSignal(self):
        fd = PythonQFileDialog()
        fd.setAcceptMode(RealQFileDialog.AcceptMode.AcceptSave)
        fd.show()
        spyFilterSelected = QSignalSpy(fd.filterSelected)

        filter_choices: list[str] = ["Image files (*.png *.xpm *.jpg)", "Text files (*.txt)", "Any files (*.*)"]
        fd.setNameFilters(filter_choices)
        assert fd.nameFilters() == filter_choices

        filters: QComboBox | None = fd.findChild(QComboBox, "fileTypeCombo")
        assert filters is not None, "QComboBox with name 'fileTypeCombo' not found"
        assert filters.view() is not None, "QComboBox view not found"
        assert filters.isVisible(), "QComboBox with name 'fileTypeCombo' is not visible"

        self._qtest.keyPress(filters, Qt.Key.Key_Down)

        assert len(spyFilterSelected) == 1, f"filterSelected signal was emitted {len(spyFilterSelected)} times instead of expected 1 time"

    def test_args(self):
        parent = None
        caption = "caption"
        directory = QDir.tempPath()
        filter = "*.mp3"
        fd = PythonQFileDialog(parent, caption, directory, filter)

        assert fd.parent() is None, f"{fd.parent()} is not None"
        assert fd.windowTitle() == caption, f"{fd.windowTitle()} == {caption}"
        assert fd.directory().absolutePath() == QDir(directory).absolutePath(), f"{fd.directory().absolutePath()} == {QDir(directory).absolutePath()}"
        assert fd.nameFilters() == [filter], f"{fd.nameFilters()} == {filter}"

    def test_directory(self):
        fd = PythonQFileDialog()
        fd.setViewMode(RealQFileDialog.ViewMode.List)
        model = fd.findChild(QFileSystemModel, "qt_filesystem_model")
        assert model is not None, "QFileSystemModel not found"

        current_path = QDir.currentPath()
        fd.setDirectory(current_path)
        spy_current_changed = QSignalSpy(fd.currentChanged)
        spy_directory_entered = QSignalSpy(fd.directoryEntered)
        spy_files_selected = QSignalSpy(fd.filesSelected)
        spy_filter_selected = QSignalSpy(fd.filterSelected)

        fd_directory = fd.directory().absolutePath()
        assert current_path == fd_directory, f"{current_path} == {fd_directory}"

        temp = QDir.temp()
        temp_path = temp.absolutePath()
        fd.setDirectory(temp_path)

        fd_directory = fd.directory().absolutePath()
        assert temp_path == fd_directory, f"{temp_path} == {fd_directory}"
        assert len(spy_current_changed) == 0, f"{len(spy_current_changed)} == 0"
        assert len(spy_directory_entered) == 0, f"{len(spy_directory_entered)} == 0"
        assert len(spy_files_selected) == 0, f"{len(spy_files_selected)} == 0"
        assert len(spy_filter_selected) == 0, f"{len(spy_filter_selected)} == 0"

        list_view = fd.findChild(QListView, "listView")
        assert list_view is not None, "QListView not found"
        list_view_root_data = list_view.rootIndex().data()
        temp_dir_name = temp.dirName()
        assert list_view_root_data == temp_dir_name, f"{list_view_root_data} == {temp_dir_name}"

        dlg = PythonQFileDialog(None, "", temp_path)
        model_index_temp = model.index(temp_path)
        dlg_directory = dlg.directory().absolutePath()
        model_index_dlg = model.index(dlg_directory)
        assert model_index_temp == model_index_dlg, f"{model_index_temp} == {model_index_dlg}"

        temp_data = model_index_temp.data(QFileSystemModel.FileNameRole)
        dlg_data = model_index_dlg.data(QFileSystemModel.FileNameRole)
        assert temp_data == dlg_data, f"{temp_data} == {dlg_data}"
        del dlg

    @pytest.mark.parametrize(
        argnames="start_path, input_text, expected",
        argvalues=[
            ["", "r", 10],
            ["", "x", 0],
            ["", "../", -1],
            ["", QDir.rootPath(), -1],
            [QDir.rootPath(), "", -1],
            pytest.param(
                QDir.root().entryInfoList(QDir.Dirs | QDir.NoDotAndDotDot)[0].absoluteFilePath(),
                "r",
                -1,
                marks=pytest.mark.skipif(len(QDir.root().entryInfoList(QDir.Dirs | QDir.NoDotAndDotDot)) == 0, reason="No folders in root directory"),
            ),
            pytest.param(
                QDir.root().entryInfoList(QDir.Dirs | QDir.NoDotAndDotDot)[0].absoluteFilePath(),
                "../",
                -1,
                marks=pytest.mark.skipif(len(QDir.root().entryInfoList(QDir.Dirs | QDir.NoDotAndDotDot)) == 0, reason="No folders in root directory"),
            ),
        ],
    )
    def test_completer(
        self,
        tmp_path="",
        start_path="",
        input_text="r",
        expected=10,
    ):
        if not start_path:
            start_path = str(tmp_path)
            # Create temporary files
            for i in range(10):
                Path(tmp_path, f"r{i:06d}").touch()

        fd = PythonQFileDialog(None, self.id(), start_path)
        fd.show()
        QTest.qWaitForWindowExposed(fd)

        model: QFileSystemModel | None = fd.findChild(QFileSystemModel, "qt_filesystem_model")
        assert model is not None, "QFileSystemModel not found with name 'qt_filesystem_model'"

        line_edit: QLineEdit | None = fd.findChild(QLineEdit, "fileNameEdit")
        assert line_edit is not None, "QLineEdit not found with name 'fileNameEdit'"

        completer: QCompleter | None = line_edit.completer()
        assert completer is not None, "QCompleter not found"

        c_model: QAbstractItemModel = completer.completionModel()
        assert c_model is not None, "Completion model not found"

        self.app.processEvents()  # Allow the model to populate
        dir1 = fd.directory().path()
        assert dir1 == start_path, f"'{dir1}' == '{start_path}'"
        idx_start_path: QModelIndex = model.index(start_path)
        idx_dir1: QModelIndex = model.index(dir1)
        assert idx_dir1 == idx_start_path, f"'{idx_dir1}' == '{idx_start_path}'"

        # Input the text
        for char in input_text:
            QTest.keyClick(line_edit, char)

        self.app.processEvents()  # Allow the completer to update

        if expected == -1:
            # Calculate expected completions
            full_path: str = os.path.join(start_path, input_text)  # noqa: PTH118
            if input_text.startswith(QDir.rootPath()):
                full_path = input_text
                input_text = ""

            dir_path: str = os.path.dirname(full_path)  # noqa: PTH120
            file_list: list[str] = os.listdir(dir_path)
            expected: int = sum(1 for f in file_list if f.startswith(input_text))

            # Account for possible hidden temporary directory
            if tmp_path and str(tmp_path).startswith(dir_path):
                tmp_dir_name = os.path.basename(str(tmp_path))  # noqa: PTH119
                if tmp_dir_name not in file_list:
                    expected += 1

        assert c_model.rowCount() == expected, f"{c_model.rowCount()} == {expected}"

    def test_completer_up(self):
        fd = PythonQFileDialog()
        fd.show()
        QTest.qWaitForWindowExposed(fd)

        line_edit: QLineEdit | None = fd.findChild(QLineEdit, "fileNameEdit")
        assert line_edit is not None, "QLineEdit not found with name 'fileNameEdit'"

        current_changed_spy = QSignalSpy(fd.currentChanged)
        directory_entered_spy = QSignalSpy(fd.directoryEntered)
        files_selected_spy = QSignalSpy(fd.filesSelected)
        filter_selected_spy = QSignalSpy(fd.filterSelected)

        depth = len(QDir.currentPath().split("/"))
        for _ in range(depth * 3 + 1):
            line_edit.insert("../")
            self.app.processEvents()

        assert len(current_changed_spy) == 0, "currentChanged signal was emitted"
        assert len(directory_entered_spy) == 0, "directoryEntered signal was emitted"
        assert len(files_selected_spy) == 0, "filesSelected signal was emitted"
        assert len(filter_selected_spy) == 0, "filterSelected signal was emitted"

    def test_acceptMode(self):
        fd = PythonQFileDialog()
        fd.show()
        QTest.qWaitForWindowExposed(fd)

        new_folder_button: QToolButton | None = fd.findChild(QToolButton, "newFolderButton")
        assert new_folder_button is not None, "New folder button not found"

        # Test default accept mode
        assert fd.acceptMode() == RealQFileDialog.AcceptOpen
        assert new_folder_button.isVisible()

        # Test AcceptSave mode
        fd.setAcceptMode(RealQFileDialog.AcceptSave)
        assert fd.acceptMode() == RealQFileDialog.AcceptSave
        assert new_folder_button.isVisible()

        # Test switching back to AcceptOpen mode
        fd.setAcceptMode(RealQFileDialog.AcceptOpen)
        assert fd.acceptMode() == RealQFileDialog.AcceptOpen
        assert new_folder_button.isVisible()

    def test_confirmOverwrite(self):
        fd = PythonQFileDialog()
        assert not fd.testOption(RealQFileDialog.Option.DontConfirmOverwrite), "DontConfirmOverwrite should be false by default"
        fd.setOption(RealQFileDialog.Option.DontConfirmOverwrite, False)  # noqa: FBT003
        assert not fd.testOption(RealQFileDialog.Option.DontConfirmOverwrite), "DontConfirmOverwrite should still be false"
        fd.setOption(RealQFileDialog.Option.DontConfirmOverwrite, True)  # noqa: FBT003
        assert fd.testOption(RealQFileDialog.Option.DontConfirmOverwrite), "DontConfirmOverwrite should be true"
        fd.setOption(RealQFileDialog.Option.DontConfirmOverwrite, False)  # noqa: FBT003
        assert not fd.testOption(RealQFileDialog.Option.DontConfirmOverwrite), "DontConfirmOverwrite should be false again"

    def test_defaultSuffix(self):
        fd = PythonQFileDialog()
        assert fd.defaultSuffix() == "", "Default suffix should be empty initially"
        fd.setDefaultSuffix("txt")
        assert fd.defaultSuffix() == "txt", "Default suffix not set correctly"
        fd.setDefaultSuffix(".txt")
        assert fd.defaultSuffix() == "txt", "Default suffix should not include leading dot"
        fd.setDefaultSuffix("")
        assert fd.defaultSuffix() == "", "Default suffix should be empty after clearing"

    def test_fileMode(self):
        fd = PythonQFileDialog()
        assert fd.fileMode() == RealQFileDialog.FileMode.AnyFile, "Default file mode should be AnyFile"

        fd.setFileMode(RealQFileDialog.FileMode.ExistingFile)
        assert fd.fileMode() == RealQFileDialog.FileMode.ExistingFile, "File mode not set to ExistingFile"

        fd.setFileMode(RealQFileDialog.FileMode.Directory)
        assert fd.fileMode() == RealQFileDialog.FileMode.Directory, "File mode not set to Directory"

        fd.setFileMode(RealQFileDialog.FileMode.ExistingFiles)
        assert fd.fileMode() == RealQFileDialog.FileMode.ExistingFiles, "File mode not set to ExistingFiles"

    def test_caption(self):
        fd = PythonQFileDialog()
        fd.setWindowTitle("testing")
        fd.setFileMode(RealQFileDialog.FileMode.Directory)
        assert fd.windowTitle() == "testing", "Window title not set correctly"

    def test_filters(self):
        fd = PythonQFileDialog()
        spy_current_changed = QSignalSpy(fd.currentChanged)
        spy_directory_entered = QSignalSpy(fd.directoryEntered)
        spy_files_selected = QSignalSpy(fd.filesSelected)
        spy_filter_selected = QSignalSpy(fd.filterSelected)
        assert fd.nameFilters() == ["All Files (*)"]

        filters: list[str] = ["Image files (*.png *.xpm *.jpg)", "Text files (*.txt)", "Any files (*.*)"]
        fd.setNameFilters(filters)
        assert fd.nameFilters() == filters, f"{fd.nameFilters()} != {filters}"

        fd.setNameFilter("Image files (*.png *.xpm *.jpg);;Text files (*.txt);;Any files (*.*)")
        assert fd.nameFilters() == filters, f"{fd.nameFilters()} != {filters}"

        assert len(spy_current_changed) == 0, f"{len(spy_current_changed)} != 0"
        assert len(spy_directory_entered) == 0, f"{len(spy_directory_entered)} != 0"
        assert len(spy_files_selected) == 0, f"{len(spy_files_selected)} != 0"
        assert len(spy_filter_selected) == 0, f"{len(spy_filter_selected)} != 0"

        fd.show()
        fd.setAcceptMode(RealQFileDialog.AcceptMode.AcceptSave)

        combo_box: QComboBox | None = fd.findChild(QComboBox, "fileTypeCombo")
        assert combo_box is not None, "QComboBox not found named 'fileTypeCombo'"
        assert combo_box.isVisible(), "QComboBox named 'fileTypeCombo' is not visible"

        for i in range(combo_box.count()):
            combo_box.setCurrentIndex(i)

        assert len(spy_filter_selected) == 0, f"{len(spy_filter_selected)} != 0"

    def test_selectFilter(self):
        fd = PythonQFileDialog()
        spy_filter_selected = QSignalSpy(fd.filterSelected)
        assert fd.selectedNameFilter() == "All Files (*)"

        filters = ["Image files (*.png *.xpm *.jpg)", "Text files (*.txt)", "Any files (*.*)"]
        fd.setNameFilters(filters)
        assert fd.selectedNameFilter() == filters[0], f"{fd.selectedNameFilter()} != {filters[0]}"

        fd.selectNameFilter(filters[1])
        assert fd.selectedNameFilter() == filters[1], f"{fd.selectedNameFilter()} != {filters[1]}"

        fd.selectNameFilter(filters[2])
        assert fd.selectedNameFilter() == filters[2], f"{fd.selectedNameFilter()} != {filters[2]}"

        fd.selectNameFilter("bob")
        assert fd.selectedNameFilter() == filters[2], f"{fd.selectedNameFilter()} != {filters[2]}"

        fd.selectNameFilter("")
        assert fd.selectedNameFilter() == filters[2], f"{fd.selectedNameFilter()} != {filters[2]}"

        assert len(spy_filter_selected) == 0, f"{len(spy_filter_selected)} != 0"

    def test_history(self):
        fd = PythonQFileDialog()
        fd.setViewMode(RealQFileDialog.ViewMode.List)

        # Check initial history
        assert fd.history()[0] == QDir.toNativeSeparators(fd.directory().absolutePath()), f"{fd.history()[0]} != {QDir.toNativeSeparators(fd.directory().absolutePath())}"

        # Set directory and check history
        fd.setDirectory(QDir.currentPath())

        # Set custom history
        history: list[str] = [QDir.toNativeSeparators(QDir.currentPath()), QDir.toNativeSeparators(QDir.homePath()), QDir.toNativeSeparators(QDir.tempPath())]
        fd.setHistory(history)
        assert fd.history() == history, f"{fd.history()} != {history}"

        # Test with invalid history
        bad_history: list[str] = ["junk"]
        fd.setHistory(bad_history)
        expected_history: list[str] = [*bad_history, QDir.toNativeSeparators(QDir.currentPath())]
        assert fd.history() == expected_history, f"{fd.history()} != {expected_history}"

    def test_iconProvider(self):
        fd = PythonQFileDialog()
        assert fd.iconProvider() is not None, f"{fd.iconProvider()} is None"
        ip = QFileIconProvider()
        fd.setIconProvider(ip)
        assert fd.iconProvider() == ip, f"{fd.iconProvider()} != {ip}"

    def test_isReadOnly(self):
        fd = PythonQFileDialog()

        new_button: QPushButton | None = fd.findChild(QPushButton, "newFolderButton")
        rename_action: QAction | None = fd.findChild(QAction, "qt_rename_action")
        delete_action: QAction | None = fd.findChild(QAction, "qt_delete_action")

        assert not fd.testOption(RealQFileDialog.Option.ReadOnly), f"{fd.testOption(RealQFileDialog.Option.ReadOnly)}"

        # This is dependent upon the file/dir, find cross platform way to test
        # fd.setDirectory(QDir.homePath())
        # assert new_button and new_button.isEnabled()
        # assert rename_action and rename_action.isEnabled()
        # assert delete_action and delete_action.isEnabled()

        fd.setOption(RealQFileDialog.Option.ReadOnly, True)  # noqa: FBT003
        assert fd.testOption(RealQFileDialog.Option.ReadOnly), f"{fd.testOption(RealQFileDialog.Option.ReadOnly)}"

        assert not (new_button and new_button.isEnabled()), f"not ({new_button} and {new_button.isEnabled()})"
        assert not (rename_action and rename_action.isEnabled()), f"not ({rename_action} and {rename_action.isEnabled()})"
        assert not (delete_action and delete_action.isEnabled()), f"not ({delete_action} and {delete_action.isEnabled()})"

    def test_itemDelegate(self):
        fd = PythonQFileDialog()
        delegate = QItemDelegate()
        fd.setItemDelegate(delegate)
        assert fd.itemDelegate() == delegate

    def test_labelText(self):
        fd = PythonQFileDialog()
        cancel_button = QDialogButtonBox().addButton(QDialogButtonBox.Cancel)

        assert fd.labelText(RealQFileDialog.DialogLabel.LookIn) == "Look in:", f"{fd.labelText(RealQFileDialog.DialogLabel.LookIn)} != 'Look in:'"
        assert fd.labelText(RealQFileDialog.DialogLabel.FileName) == "File &name:", f"{fd.labelText(RealQFileDialog.DialogLabel.FileName)} != 'File &name:'"
        assert fd.labelText(RealQFileDialog.DialogLabel.FileType) == "Files of type:", f"{fd.labelText(RealQFileDialog.DialogLabel.FileType)} != 'Files of type:'"
        assert fd.labelText(RealQFileDialog.DialogLabel.Accept) == "&Open", f"{fd.labelText(RealQFileDialog.DialogLabel.Accept)} != '&Open'"
        assert fd.labelText(RealQFileDialog.DialogLabel.Reject) == cancel_button.text(), f"{fd.labelText(RealQFileDialog.DialogLabel.Reject)} != '{cancel_button.text()}'"

        fd.setLabelText(RealQFileDialog.DialogLabel.LookIn, "1")
        assert fd.labelText(RealQFileDialog.DialogLabel.LookIn) == "1", f"{fd.labelText(RealQFileDialog.DialogLabel.LookIn)} != '1'"
        fd.setLabelText(RealQFileDialog.DialogLabel.FileName, "2")
        assert fd.labelText(RealQFileDialog.DialogLabel.FileName) == "2", f"{fd.labelText(RealQFileDialog.DialogLabel.FileName)} != '2'"
        fd.setLabelText(RealQFileDialog.DialogLabel.FileType, "3")
        assert fd.labelText(RealQFileDialog.DialogLabel.FileType) == "3", f"{fd.labelText(RealQFileDialog.DialogLabel.FileType)} != '3'"
        fd.setLabelText(RealQFileDialog.DialogLabel.Accept, "4")
        assert fd.labelText(RealQFileDialog.DialogLabel.Accept) == "4", f"{fd.labelText(RealQFileDialog.DialogLabel.Accept)} != '4'"
        fd.setLabelText(RealQFileDialog.DialogLabel.Reject, "5")
        assert fd.labelText(RealQFileDialog.DialogLabel.Reject) == "5", f"{fd.labelText(RealQFileDialog.DialogLabel.Reject)} != '5'"

    def test_resolveSymlinks(self):
        fd = PythonQFileDialog()

        # default
        assert not fd.testOption(RealQFileDialog.Option.DontResolveSymlinks), f"{fd.testOption(RealQFileDialog.Option.DontResolveSymlinks)}"
        fd.setOption(RealQFileDialog.Option.DontResolveSymlinks, True)  # noqa: FBT003
        assert fd.testOption(RealQFileDialog.Option.DontResolveSymlinks), f"{fd.testOption(RealQFileDialog.Option.DontResolveSymlinks)}"
        fd.setOption(RealQFileDialog.Option.DontResolveSymlinks, False)  # noqa: FBT003
        assert not fd.testOption(RealQFileDialog.Option.DontResolveSymlinks), f"{fd.testOption(RealQFileDialog.Option.DontResolveSymlinks)}"

        # the file dialog doesn't do anything based upon this, just passes it to the model
        # the model should fully test it, don't test it here

    @pytest.mark.parametrize(
        argnames="file, count",
        argvalues=[
            ("temp", 1),
            (None, 1),
            ("foo", 1),
        ],
    )
    def test_selectFile(self, file: Literal["foo", "temp", None] = "foo", count: Literal[1] = 1):
        fd = PythonQFileDialog()
        model: QFileSystemModel | None = fd.findChild(QFileSystemModel, "qt_filesystem_model")
        assert model is not None, f"{model} is None"

        fd.setDirectory(QDir.currentPath())
        selected_files: list[str] = fd.selectedFiles()
        selected_files_count = len(selected_files)
        expected_count = 1  # default value
        assert selected_files_count == expected_count, f"{selected_files_count} != {expected_count}"

        temp_file = None
        if file == "temp":
            temp_file = QTemporaryFile(QDir.tempPath() + "/aXXXXXX")
            assert temp_file.open(), "file would not open"
            file = temp_file.fileName()  # pyright: ignore[reportAssignmentType]

        fd.selectFile(file)
        selected_files = fd.selectedFiles()
        selected_files_count = len(selected_files)
        assert selected_files_count == count, f"{selected_files_count} != {count}"

        current_dir = fd.directory().path()
        current_dir_index = model.index(current_dir)

        if temp_file is None:
            expected_dir = QDir.currentPath()
        else:
            expected_dir = QDir.tempPath()

        expected_dir_index = model.index(expected_dir)
        assert current_dir_index == expected_dir_index, f"{current_dir_index} != {expected_dir_index}"

        # Ensure the file dialog lets go of the temporary file for "temp"
        del fd
        if temp_file:
            temp_file.close()

    @staticmethod
    def isCaseSensitiveFileSystem(path: str) -> bool:
        return os.path.exists(path) and os.path.exists(path.upper())  # noqa: PTH110

    def test_selectFilesWrongCaseSaveAs(self):
        home = QDir.homePath()
        if self.isCaseSensitiveFileSystem(home):
            self.skipTest("This test is intended for case-insensitive file systems only.")

        file_name = "foo.txt"
        path = os.path.join(home, file_name)  # noqa: PTH118
        wrong_case_path = "".join(c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(path))

        fd = PythonQFileDialog(None, "QTBUG-38162", wrong_case_path)
        fd.setAcceptMode(RealQFileDialog.AcceptMode.AcceptSave)
        fd.selectFile(wrong_case_path)

        line_edit = fd.findChild(QLineEdit, "fileNameEdit")
        assert line_edit is not None, f"{line_edit} is None"
        assert line_edit.text().lower() == file_name.lower(), f"{line_edit.text().lower()} != {file_name.lower()}"

    def test_selectFiles(self):
        fd = PythonQFileDialog()
        fd.setViewMode(RealQFileDialog.ViewMode.List)
        fd.setDirectory(str(self.temp_path))
        fd.setFileMode(RealQFileDialog.FileMode.ExistingFiles)

        spy_current_changed = QSignalSpy(fd.currentChanged)
        spy_directory_entered = QSignalSpy(fd.directoryEntered)
        spy_files_selected = QSignalSpy(fd.filesSelected)
        spy_filter_selected = QSignalSpy(fd.filterSelected)

        files_path = fd.directory().absolutePath()
        for i in range(5):
            file_path = os.path.join(files_path, f"qfiledialog_auto_test_not_pres_{i}")  # noqa: PTH118
            with open(file_path, "wb") as f:
                f.write(b"\0" * 1024)

        # Get a list of files in the view and then get the corresponding indexes
        file_list: list[str] = fd.directory().entryList(QDir.Files)
        to_select: list[QModelIndex] = []
        assert len(file_list) > 1, "No files in the directory"
        list_view: QListView | None = fd.findChild(QListView, "listView")
        assert list_view is not None, "Failed to find list view"
        for file_name in file_list:
            fd.selectFile(os.path.join(fd.directory().path(), file_name))  # noqa: PTH118
            assert self.wait_for(lambda: list_view.selectionModel().selectedRows()), "Failed to get selected rows"
            to_select.append(list_view.selectionModel().selectedRows()[-1])
        assert len(spy_files_selected) == 0, f"Spy files selected is not empty: {len(spy_files_selected)}"

        list_view.selectionModel().clear()
        assert len(spy_files_selected) == 0, f"Spy files selected is not empty: {len(spy_files_selected)}"

        # Select the indexes
        for index in to_select:
            list_view.selectionModel().select(index, QItemSelectionModel.Select | QItemSelectionModel.Rows)
        assert len(fd.selectedFiles()) == len(to_select), f"Selected files is not the same length as to_select ({len(fd.selectedFiles())} != {len(to_select)})"
        assert len(spy_current_changed) == 0, f"Spy current changed is not empty: {len(spy_current_changed)}"
        assert len(spy_directory_entered) == 0, f"Spy directory entered is not empty: {len(spy_directory_entered)}"
        assert len(spy_files_selected) == 0, f"Spy files selected is not empty: {len(spy_files_selected)}"
        assert len(spy_filter_selected) == 0, f"Spy filter selected is not empty: {len(spy_filter_selected)}"

        # Test for AnyFile mode
        self.temp_dir.cleanup()
        dialog = PythonQFileDialog(None, "Save")
        dialog.setFileMode(RealQFileDialog.FileMode.AnyFile)
        dialog.setAcceptMode(RealQFileDialog.AcceptMode.AcceptSave)
        dialog.selectFile(os.path.join(self.temp_path, "blah"))  # noqa: PTH118
        dialog.show()
        assert self.wait_for_window_exposed(dialog), "Failed to show window"
        line_edit = dialog.findChild(QLineEdit, "fileNameEdit")
        assert line_edit is not None, "Failed to find line edit with name 'fileNameEdit'"
        assert line_edit.text() == "blah", f"Expected line edit text to be 'blah', but got '{line_edit.text()}'"

    def test_viewMode(self):
        fd = PythonQFileDialog()
        fd.setViewMode(RealQFileDialog.ViewMode.List)
        fd.show()

        # Find widgets
        tree_view: list[QTreeView] = fd.findChildren(QTreeView, "treeView")
        assert len(tree_view) == 1, f"Expected 1 tree view, but found {len(tree_view)}"
        list_view: list[QListView] = fd.findChildren(QListView, "listView")
        assert len(list_view) == 1, f"Expected 1 list view, but found {len(list_view)}"
        list_button: list[QToolButton] = fd.findChildren(QToolButton, "listModeButton")
        assert len(list_button) == 1, f"Expected 1 list mode button, but found {len(list_button)}"
        tree_button: list[QToolButton] = fd.findChildren(QToolButton, "detailModeButton")
        assert len(tree_button) == 1, f"Expected 1 detail mode button, but found {len(tree_button)}"

        # Default value
        assert fd.viewMode() == RealQFileDialog.ViewMode.List, "Default view mode should be List"

        # Detail mode
        fd.setViewMode(RealQFileDialog.ViewMode.Detail)
        self.app.processEvents()

        assert fd.viewMode() == RealQFileDialog.ViewMode.Detail, "View mode should be Detail"
        assert not list_view[0].isVisible(), "List view should not be visible in Detail mode"
        assert not list_button[0].isDown(), "List mode button should not be down in Detail mode"
        # this assert fails incorrectly right after a setVisible(True) call?
        #assert tree_view[0].isVisible(), "Tree view should be visible in Detail mode"
        assert tree_button[0].isDown(), "Detail mode button should be down in Detail mode"

        # List mode
        fd.setViewMode(RealQFileDialog.ViewMode.List)

        assert fd.viewMode() == RealQFileDialog.ViewMode.List, "View mode should be List"
        assert not tree_view[0].isVisible(), "Tree view should not be visible in List mode"
        assert not tree_button[0].isDown(), "Detail mode button should not be down in List mode"
        assert list_view[0].isVisible(), "List view should be visible in List mode"
        assert list_button[0].isDown(), "List mode button should be down in List mode"

    def test_proxyModel(self):
        fd = PythonQFileDialog()
        assert fd.proxyModel() is None, f"{fd.proxyModel()} is not None"

        fd.setProxyModel(None)
        assert fd.proxyModel() is None, f"{fd.proxyModel()} is not None"

        proxyModel = QSortFilterProxyModel(fd)
        fd.setProxyModel(proxyModel)
        assert fd.proxyModel() == proxyModel, f"{fd.proxyModel()} != {proxyModel}"

        fd.setProxyModel(None)
        assert fd.proxyModel() is None, f"{fd.proxyModel()} is not None"

    def test_setMimeTypeFilters(self):
        fd = PythonQFileDialog()
        fd.setDirectory(QDir.tempPath())
        fd.setMimeTypeFilters(["text/plain", "text/html"])
        fd.show()
        QTest.qWaitForWindowExposed(fd)

        assert fd.mimeTypeFilters() == ["text/plain", "text/html"], "MIME type filters not set correctly."

    @pytest.mark.parametrize(
        argnames="name_filter_details_visible, filters, select_filter, expected_selected_filter",
        argvalues=[
            (True, [], "", ""),
            (False, [], "", ""),
            (True, ["Any files (*)", "Image files (*.png *.xpm *.jpg)", "Text files (*.txt)"], "Image files (*.png *.xpm *.jpg)", "Image files (*.png *.xpm *.jpg)"),
            (False, ["Any files (*)", "Image files (*.png *.xpm *.jpg)", "Text files (*.txt)"], "Image files (*.png *.xpm *.jpg)", "Image files"),
            (True, ["Any files (*)", "Image files (*.png *.xpm *.jpg)", "Text files (*.txt)"], "foo", "Any files (*)"),
            (False, ["Any files (*)", "Image files (*.png *.xpm *.jpg)", "Text files (*.txt)"], "foo", "Any files"),
        ],
    )
    def test_setNameFilter(
        self,
        name_filter_details_visible: bool = True,  # noqa: FBT001, FBT002
        filters: list[str] = [],  # noqa: B006
        select_filter: str = "",
        expected_selected_filter: str = "",
    ):
        fd = PythonQFileDialog()
        fd.setDirectory(QDir.tempPath())
        fd.setNameFilters(filters)
        fd.setOption(RealQFileDialog.Option.HideNameFilterDetails, not name_filter_details_visible)
        fd.selectNameFilter(select_filter)
        fd.show()
        QTest.qWaitForWindowExposed(fd)

        assert fd.selectedNameFilter() == expected_selected_filter, "Selected filter not set correctly."

    def test_setEmptyNameFilter(self):
        fd = PythonQFileDialog()
        fd.setNameFilter("")
        fd.setNameFilters([])

    @unittest.skip("c++-specific test.")
    def test_focus(self):
        #if not QGuiApplicationPrivate.platformIntegration().hasCapability(QPlatformIntegration.Capability.WindowActivation):
        #    self.skipTest("Window activation is not supported")
        fd = PythonQFileDialog()
        fd.setDirectory(QDir.currentPath())
        fd.show()
        self.app.setActiveWindow(fd)
        assert QTest.qWaitForWindowActive(fd), "Failed to wait for window to be active"
        assert fd.isVisible() is True, "File dialog was not visible"
        assert self.app.activeWindow() == fd, "File dialog was not active window"
        self.app.processEvents()

        # make sure the tests work with focus follows mouse
        QCursor.setPos(fd.geometry().center())

        file_name_edit: list[QWidget] = fd.findChildren(QWidget, "fileNameEdit")
        assert len(file_name_edit) == 1, "Expected 1 QWidget with name 'fileNameEdit'"
        assert file_name_edit[0] is not None, "QWidget with name 'fileNameEdit' was not found"
        self.app.processEvents()  # Allow for focus to settle
        assert file_name_edit[0].hasFocus() is True, "Expected QWidget with name 'fileNameEdit' to have focus"
        assert file_name_edit[0].hasFocus() is True, "Expected QWidget with name 'fileNameEdit' to have focus"

    def test_historyBack(self):
        fd = PythonQFileDialog()
        fd.setViewMode(RealQFileDialog.ViewMode.List)
        fd.show()
        QTest.qWaitForWindowExposed(fd)

        model: QFileSystemModel | None = fd.findChild(QFileSystemModel, "qt_filesystem_model")
        assert model, f"File system model not found, got: '{model}'"
        back_button: QToolButton | None = fd.findChild(QToolButton, "backButton")
        assert back_button, f"Back button not found, got: '{back_button}'"
        forward_button: QToolButton | None = fd.findChild(QToolButton, "forwardButton")
        assert forward_button, f"Forward button not found, got: '{forward_button}'"

        home = fd.directory().absolutePath()
        desktop = QDir.homePath()
        temp = QDir.tempPath()

        assert not back_button.isEnabled(), f"Back button should be disabled initially, got: '{back_button.isEnabled()}'"
        assert not forward_button.isEnabled(), f"Forward button should be disabled initially, got: '{forward_button.isEnabled()}'"

        fd.setDirectory(temp)
        self.app.processEvents()
        assert back_button.isEnabled(), f"Back button should be enabled after changing directory, got: '{back_button.isEnabled()}'"
        assert not forward_button.isEnabled(), f"Forward button should still be disabled, got: '{forward_button.isEnabled()}'"

        fd.setDirectory(desktop)
        self.app.processEvents()

        back_button.click()
        self.app.processEvents()
        assert back_button.isEnabled(), f"Back button should still be enabled, got: '{back_button.isEnabled()}'"
        assert forward_button.isEnabled(), f"Forward button should be enabled after going back, got: '{forward_button.isEnabled()}'"
        assert fd.directory().absolutePath() == temp, f"Directory should be temp after going back, got: '{fd.directory().absolutePath()}'"

        back_button.click()
        self.app.processEvents()
        assert fd.directory().absolutePath() == home, f"Directory should be home after going back again, got: '{fd.directory().absolutePath()}'"
        assert not back_button.isEnabled(), f"Back button should be disabled at home, got: '{back_button.isEnabled()}'"
        assert forward_button.isEnabled(), f"Forward button should be enabled, got: '{forward_button.isEnabled()}'"

        back_button.click()
        self.app.processEvents()
        assert fd.directory().absolutePath() == home, f"Directory should not change when back button is clicked at home, got: '{fd.directory().absolutePath()}'"
        assert not back_button.isEnabled(), f"Back button should still be disabled, got: '{back_button.isEnabled()}'"
        assert forward_button.isEnabled(), f"Forward button should still be enabled, got: '{forward_button.isEnabled()}'"

    def test_historyForward(self):
        fd = PythonQFileDialog()
        fd.setViewMode(RealQFileDialog.ViewMode.List)
        fd.show()
        QTest.qWaitForWindowExposed(fd)

        back_button: QToolButton | None = fd.findChild(QToolButton, "backButton")
        assert back_button, "Back button not found."
        forward_button: QToolButton | None = fd.findChild(QToolButton, "forwardButton")
        assert forward_button, "Forward button not found."

        model: QFileSystemModel | None = fd.findChild(QFileSystemModel, "qt_filesystem_model")
        assert model, "File system model not found."

        home: str = fd.directory().absolutePath()
        desktop: str = QDir.homePath()
        temp: str = QDir.tempPath()

        fd.setDirectory(home)
        fd.setDirectory(temp)
        fd.setDirectory(desktop)

        back_button.click()
        self.app.processEvents()
        assert forward_button.isEnabled(), f"Forward button should be enabled after going back, got: '{forward_button.isEnabled()}'"
        assert fd.directory().absolutePath() == temp, f"Directory should be temp after going back, got: '{fd.directory().absolutePath()}'"

        forward_button.click()
        self.app.processEvents()
        assert fd.directory().absolutePath() == desktop, f"Directory should be desktop after going forward, got: '{fd.directory().absolutePath()}'"
        assert back_button.isEnabled(), f"Back button should be enabled, got: '{back_button.isEnabled()}'"
        assert not forward_button.isEnabled(), f"Forward button should be disabled at the end of history, got: '{forward_button.isEnabled()}'"

        back_button.click()
        self.app.processEvents()
        assert fd.directory().absolutePath() == temp, f"Directory should be temp after going back, got: '{fd.directory().absolutePath()}'"
        assert back_button.isEnabled(), f"Back button should be enabled, got: '{back_button.isEnabled()}'"

        back_button.click()
        self.app.processEvents()
        assert fd.directory().absolutePath() == home, f"Directory should be home after going back again, got: '{fd.directory().absolutePath()}'"
        assert not back_button.isEnabled(), f"Back button should be disabled at home, got: '{back_button.isEnabled()}'"
        assert forward_button.isEnabled(), f"Forward button should be enabled, got: '{forward_button.isEnabled()}'"

        forward_button.click()
        self.app.processEvents()
        assert fd.directory().absolutePath() == temp, "Directory should be temp after going forward."
        back_button.click()
        self.app.processEvents()
        assert fd.directory().absolutePath() == home, f"Directory should be home after going back, got: '{fd.directory().absolutePath()}'"

        forward_button.click()
        self.app.processEvents()
        assert fd.directory().absolutePath() == temp, f"Directory should be temp after going forward, got: '{fd.directory().absolutePath()}'"
        forward_button.click()
        self.app.processEvents()
        assert fd.directory().absolutePath() == desktop, f"Directory should be desktop after going forward again, got: '{fd.directory().absolutePath()}'"

        back_button.click()
        self.app.processEvents()
        assert fd.directory().absolutePath() == temp, f"Directory should be temp after going back, got: '{fd.directory().absolutePath()}'"
        back_button.click()
        self.app.processEvents()
        assert fd.directory().absolutePath() == home, f"Directory should be home after going back again, got: '{fd.directory().absolutePath()}'"
        fd.setDirectory(desktop)
        self.app.processEvents()
        assert not forward_button.isEnabled(), f"Forward button should be disabled after setting new directory, got: '{forward_button.isEnabled()}'"

    @pytest.mark.parametrize(
        "file_mode",
        [
            RealQFileDialog.FileMode.AnyFile,
            RealQFileDialog.FileMode.ExistingFile,
            RealQFileDialog.FileMode.Directory,
            RealQFileDialog.FileMode.ExistingFiles,
        ],
    )
    def test_disableSaveButton(self, file_mode=RealQFileDialog.FileMode.AnyFile):
        fd = PythonQFileDialog()
        fd.setAcceptMode(RealQFileDialog.AcceptMode.AcceptSave)
        fd.setFileMode(file_mode)
        fd.setDirectory(QDir.tempPath())
        fd.show()
        QTest.qWaitForWindowExposed(fd)

        button_box: QDialogButtonBox | None = fd.findChild(QDialogButtonBox, "buttonBox")
        assert button_box, "Button box not found with name 'buttonBox'"
        save_button: QPushButton = button_box.button(QDialogButtonBox.StandardButton.Save)
        assert save_button, "Save button not found with name 'Save'"

        line_edit: QLineEdit | None = fd.findChild(QLineEdit, "fileNameEdit")
        assert line_edit, "Line edit not found with name 'fileNameEdit'"

        if file_mode == RealQFileDialog.FileMode.Directory:
            assert save_button.isEnabled(), "Save button should be enabled for Directory mode."
        else:
            assert not save_button.isEnabled(), "Save button should be disabled initially."

            line_edit.setText("foo")
            assert save_button.isEnabled(), "Save button should be enabled after entering text."

            line_edit.setText("")
            assert not save_button.isEnabled(), "Save button should be disabled after clearing text."

    @pytest.mark.parametrize(
        argnames="path, label, caption",
        argvalues=[
            ("", None, "&Save"),
            ("qfiledialog.new_file", None, "&Save"),
            (QDir.temp().absolutePath(), None, "&Open"),
            ("qfiledialog.new_file", "Mooo", "Mooo"),
            (QDir.temp().absolutePath(), "Poo", "&Open"),
        ],
    )
    def test_saveButtonText(self, path: str, label: Literal["Mooo", "Poo"] | None, caption: str):
        fd = PythonQFileDialog(None, "auto test", QDir.temp().absolutePath())
        fd.setAcceptMode(RealQFileDialog.AcceptMode.AcceptSave)
        if label is not None:
            fd.setLabelText(RealQFileDialog.DialogLabel.Accept, label)
        fd.setDirectory(QDir.temp())
        fd.selectFile(path)
        button_box: QDialogButtonBox | None = fd.findChild(QDialogButtonBox, "buttonBox")
        assert button_box is not None, "QDialogButtonBox was not found with name 'buttonBox'"
        button: QPushButton = button_box.button(QDialogButtonBox.StandardButton.Save)
        assert button is not None, "Save QPushButton was not found"
        assert button.text() == self.app.tr(caption), f"Save QPushButton text is incorrect for path: {path}, label: {label}"

    def test_clearLineEdit(self):
        work_dir = QTemporaryDir(f"{QDir.tempPath()}/tst_qfd_clearXXXXXX")
        assert work_dir.isValid(), f"Temporary directory was not valid, got: '{work_dir.path()}'"
        work_dir_path = work_dir.path()
        dir_name = "aaaaa"
        assert QDir(work_dir_path).mkdir(dir_name), f"Directory was not created, got: '{work_dir_path}'"

        fd = PythonQFileDialog(None, f"{self.__class__.__name__}.{self._testMethodName} AnyFile", "foo")
        fd.setViewMode(RealQFileDialog.ViewMode.List)
        fd.setFileMode(RealQFileDialog.FileMode.AnyFile)
        fd.show()

        assert self.wait_for_window_exposed(fd), "File dialog was not exposed"
        line_edit: QLineEdit | None = fd.findChild(QLineEdit, "fileNameEdit")
        assert line_edit is not None, "QLineEdit was not found with name 'fileNameEdit'"
        assert line_edit.text() == "foo", f"QLineEdit text was not correct, got: '{line_edit.text()}'"

        list_view: QListView | None = fd.findChild(QListView, "listView")
        assert list_view is not None, "QListView was not found with name 'listView'"

        fd.setDirectory(work_dir_path)
        assert self.wait_for(
            lambda: dir_name
            in [
                list_view.model().index(r, 0, list_view.rootIndex()).data()
                for r in range(list_view.model().rowCount(list_view.rootIndex()))
            ]
        ), "Directory was not found in list view"

        list_view.setFocus()

        assert self.wait_for(lambda: list_view.currentIndex().data() == dir_name), f"Directory was not found in list view, got: '{list_view.currentIndex().data()}'"

        list_view.selectionModel().select(
            list_view.currentIndex(),
            QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows,
        )
        list_view.setCurrentIndex(list_view.currentIndex())

        assert self.wait_for(lambda: fd.directory().absolutePath() != work_dir_path), f"Directory was not found in list view, got: '{fd.directory().absolutePath()}'"
        assert line_edit.text(), f"QLineEdit text was not correct, got: '{line_edit.text()}'"

        fd.setFileMode(RealQFileDialog.FileMode.Directory)
        fd.setWindowTitle(f"{self.__class__.__name__}.{self._testMethodName} Directory")
        fd.setDirectory(work_dir_path)
        assert self.wait_for(
            lambda: dir_name
            in [
                list_view.model().index(r, 0, list_view.rootIndex()).data()
                for r in range(list_view.model().rowCount(list_view.rootIndex()))
            ]
        ), "Directory was not found in list view"

        assert self.wait_for(lambda: list_view.currentIndex().data() == dir_name), f"Directory was not found in list view, got: '{list_view.currentIndex().data()}'"

        list_view.selectionModel().select(
            list_view.currentIndex(),
            QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows,
        )
        list_view.setCurrentIndex(list_view.currentIndex())

        assert self.wait_for(lambda: fd.directory().absolutePath() != work_dir_path), "Directory was not found in list view"
        assert not line_edit.text(), f"QLineEdit text was not correct, got: '{line_edit.text()}'"

        back_button = fd.findChild(QToolButton, "backButton")
        assert back_button is not None, "Back button was not found with name 'backButton'"
        tree_view = fd.findChildren(QTreeView, "treeView")[0]
        assert tree_view is not None, "QTreeView was not found with name 'treeView'"
        back_button.click()
        assert self.wait_for(
            lambda: tree_view.selectionModel().selectedIndexes()[0].data() == dir_name
        ), "Directory was not found in list view"

    def test_enableChooseButton(self):
        fd = PythonQFileDialog()
        fd.setFileMode(RealQFileDialog.FileMode.Directory)
        fd.show()
        button_box: QDialogButtonBox | None = fd.findChild(QDialogButtonBox, "buttonBox")
        assert button_box is not None, "QDialogButtonBox was not found with name 'buttonBox'"
        button: QPushButton = button_box.button(QDialogButtonBox.StandardButton.Open)
        assert button is not None, "Open button was not found with name 'Open'"
        assert button.isEnabled(), "Open button was not enabled"

    @unittest.skip("native dialogs are not implemented yet")
    def test_widgetlessNativeDialog(self):
        # if not QGuiApplication.platformTheme().usePlatformNativeDialog(QPlatformTheme.DialogType.FileDialog):
        #    self.skipTest("This platform always uses widgets to realize its QFileDialog, instead of the native file dialog.")
        QGuiApplication.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeDialogs, False)  # noqa: FBT003
        fd = PythonQFileDialog()
        fd.setWindowModality(Qt.WindowModality.ApplicationModal)
        fd.show()
        assert self.wait_for(lambda: fd.isVisible()), "File dialog was not visible"
        model: QFileSystemModel | None = fd.findChild(QFileSystemModel, "qt_filesystem_model")
        assert model is None, "QFileSystemModel was found with name 'qt_filesystem_model'"
        button: QPushButton | None = fd.findChild(QPushButton)
        assert button is None, "QPushButton was found"
        QGuiApplication.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeDialogs, True)  # noqa: FBT003

    @unittest.skip("native dialogs are not implemented yet")
    def test_hideNativeByDestruction(self):
        # if not QGuiApplication.platformTheme().usePlatformNativeDialog(QPlatformTheme.DialogType.FileDialog):
        #    self.skipTest("This platform always uses widgets to realize its QFileDialog, instead of the native file dialog.")
        QGuiApplication.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeDialogs, False)  # noqa: FBT003
        def reset_attribute() -> None:
            return QGuiApplication.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeDialogs, True)  # noqa: FBT003
        self.addCleanup(reset_attribute)

        window = QWidget()
        child = QWidget(window)
        dialog = PythonQFileDialog(child)
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        window.show()
        assert self.wait_for_window_active(window), "Window was not active"
        dialog.open()

        def window_active():
            return window.isActiveWindow()
        def window_inactive():
            return not window.isActiveWindow()
        if not self.wait_for(window_inactive, 2000):
            self.skipTest("Dialog didn't activate")

        child.deleteLater()
        assert self.wait_for(window_inactive, 2000), "Dialog was not closed"
        window.activateWindow()
        assert self.wait_for(window_active, 2000), "Window was not active"

    @unittest.skip("native dialogs are not implemented yet")
    def test_SelectedFilesWithoutWidgets(self):
        fd = PythonQFileDialog()
        fd.setAcceptMode(RealQFileDialog.AcceptMode.AcceptOpen)
        assert len(fd.selectedFiles()) >= 0, f"Selected files was not correct, expected: >= 0, got: {len(fd.selectedFiles())}"

    def test_selectedFileWithDefaultSuffix(self):
        temp_dir = QTemporaryDir(f"{QDir.tempPath()}/abcXXXXXX.def")
        assert temp_dir.isValid(), f"Temporary directory was not valid, got: {temp_dir.path()}"

        fd = PythonQFileDialog()
        fd.setDirectory(temp_dir.path())
        fd.setDefaultSuffix(".txt")
        fd.selectFile("xxx")
        selected_files = fd.selectedFiles()
        assert len(selected_files) == 1, f"Selected files was not correct, expected: 1, got: {len(selected_files)}"
        assert selected_files[0].endswith(".txt"), f"Selected file was not correct, expected: .txt, got: {selected_files[0]}"

    def test_trailingDotsAndSpaces(self):
        if sys.platform != "win32":
            self.skipTest("This is only tested on Windows")
        fd = PythonQFileDialog()
        fd.setViewMode(RealQFileDialog.ViewMode.List)
        fd.setFileMode(RealQFileDialog.FileMode.ExistingFile)
        fd.show()
        line_edit = fd.findChild(QLineEdit, "fileNameEdit")
        assert line_edit is not None, "QLineEdit was not found with name 'fileNameEdit'"
        list_view = fd.findChild(QListView, "listView")
        assert list_view is not None, "QListView was not found with name 'listView'"
        self.wait(1000)
        current_children_count = list_view.model().rowCount(list_view.rootIndex())
        QTest.keyClick(line_edit, Qt.Key.Key_Space)
        QTest.keyClick(line_edit, Qt.Key.Key_Period)
        self.wait(1000)
        assert current_children_count == list_view.model().rowCount(list_view.rootIndex()), f"QListView was not correct, expected: {current_children_count}, got: {list_view.model().rowCount(list_view.rootIndex())}"
        line_edit.clear()
        QTest.keyClick(line_edit, Qt.Key.Key_Period)
        QTest.keyClick(line_edit, Qt.Key.Key_Space)
        self.wait(1000)
        assert current_children_count == list_view.model().rowCount(list_view.rootIndex()), f"QListView was not correct, expected: {current_children_count}, got: {list_view.model().rowCount(list_view.rootIndex())}"

    @pytest.mark.parametrize(
        argnames="tilde_path, expanded_path",
        argvalues=[
            ["", ""],
            ["~", QDir.homePath()],
            ["~/some/sub/dir/", QDir.homePath() + "/some/sub/dir"],
            [f"~{os.environ.get('USER', '')}", QDir.homePath()],
            [f"~{os.environ.get('USER', '')}/some/sub/dir", QDir.homePath() + "/some/sub/dir"],
            ["~thisIsNotAValidUserName", "~thisIsNotAValidUserName"],
        ],
    )
    def test_tildeExpansion(self, tilde_path: str = "", expanded_path: str = ""):
        if sys.platform != "linux":
            pytest.skip("This test is only for Unix systems")

        result = qt_tildeExpansion(tilde_path)
        assert result == expanded_path, f"Expected {expanded_path}, but got {result}"

    def test_rejectModalDialogs(self):
        # if QGuiApplication.platformName().startswith("wayland", Qt.CaseSensitivity.CaseInsensitive):
        #    self.skipTest("Wayland: This freezes. Figure out why.")
        dr = DialogRejecter()

        result: tuple[QUrl, str] = PythonQFileDialog.getOpenFileUrl(None, "getOpenFileUrl")
        assert isinstance(result, tuple), "Return value is not a tuple"
        url, selected_filter = result
        assert url.isEmpty(), "URL was not empty"
        assert isinstance(selected_filter, str), "Selected filter is not a string"
        assert selected_filter == "", "Selected filter is not an empty string"
        assert not url.isValid(), "URL was not valid"

        url: QUrl = PythonQFileDialog.getExistingDirectoryUrl(None, "getExistingDirectoryUrl")
        assert url.isEmpty(), "URL was not empty"
        assert not url.isValid(), "URL was not valid"

        result: tuple[QUrl, str] = PythonQFileDialog.getSaveFileUrl(None, "getSaveFileUrl")
        assert isinstance(result, tuple), "Return value is not a tuple"
        url, selected_filter = result
        assert url.isEmpty(), "URL was not empty"
        assert isinstance(selected_filter, str), "Selected filter is not a string"
        assert selected_filter == "", "Selected filter is not an empty string"
        assert not url.isValid(), "URL was not valid"

        result2: tuple[str, str] = PythonQFileDialog.getOpenFileName(None, "getOpenFileName")
        assert isinstance(result2, tuple), "Return value is not a tuple"
        file, selected_filter = result2
        assert file == "", "File was not empty"
        assert selected_filter == "", "Selected filter is not an empty string"
        assert file.endswith(".txt"), "File was not correct"

        file: tuple[str, str] = PythonQFileDialog.getExistingDirectory(None, "getExistingDirectory")
        assert file == ("", ""), "File was not empty"

        file: tuple[str, str] = PythonQFileDialog.getSaveFileName(None, "getSaveFileName")
        assert file == ("", ""), "File was not empty"

    def test_QTBUG49600_nativeIconProviderCrash(self):
        # if not QGuiApplication.platformTheme().usePlatformNativeDialog(QPlatformTheme.DialogType.FileDialog):
        #    self.skipTest("This platform always uses widgets to realize its QFileDialog, instead of the native file dialog.")
        fd = PythonQFileDialog()
        fd.iconProvider()

    def wait_for_window_exposed(self, window: QWidget) -> bool:
        return self.wait_for(lambda: window.isVisible() and window.windowHandle() and window.windowHandle().isExposed())

    def wait_for_window_active(self, window: QWidget) -> bool:
        return self.wait_for(lambda: window.isActiveWindow())

    def wait_for(self, predicate, timeout=5000) -> bool:
        start_time = QTime.currentTime()
        while QTime.currentTime().msecsTo(start_time) < timeout:
            self.app.processEvents()
            if predicate():
                return True
        return False

    def wait(self, msecs):
        QTest.qWait(msecs)


FORCE_UNITTEST = False
VERBOSE = True
FAIL_FAST = False


def run_tests():
    print("Running tests of TestQFileDialog")
    try:
        import pytest

        if not FORCE_UNITTEST:
            pytest.main(["-v" if VERBOSE else "", "-x" if FAIL_FAST else "", "--tb=native", __file__])
        else:
            raise ImportError  # noqa: TRY301
    except ImportError:
        unittest.main(verbosity=2 if VERBOSE else 1, failfast=FAIL_FAST)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    QTimer.singleShot(0, run_tests)
    app.exec()
