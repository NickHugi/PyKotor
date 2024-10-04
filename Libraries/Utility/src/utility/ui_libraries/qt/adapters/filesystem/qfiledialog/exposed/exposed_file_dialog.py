from __future__ import annotations

import contextlib
import sys
import traceback

from typing import TYPE_CHECKING, overload

from loggerplus import RobustLogger
from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDialogButtonBox,
    QFileDialog,
    QFileSystemModel,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QToolButton,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from qtpy.QtCore import QAbstractItemModel, QPoint
    from qtpy.QtWidgets import QLayout


class Ui_ExposedQFileDialog(QFileDialog):  # noqa: N801

    def setupUi(self, dialog: ExposedQFileDialog):
        # Main layout
        gridlayout: QLayout | None = dialog.layout()
        assert isinstance(gridlayout, QGridLayout)
        self.gridlayout: QGridLayout = gridlayout

        # Look In label and combo
        look_in_label: QLabel | None = dialog.findChild(QLabel, "lookInLabel")
        assert isinstance(look_in_label, QLabel)
        self.lookInLabel: QLabel = look_in_label

        look_in_combo: QComboBox | None = dialog.findChild(QComboBox, "lookInCombo")
        assert isinstance(look_in_combo, QComboBox)
        self.lookInCombo: QComboBox = look_in_combo

        # Toolbar buttons
        back_button: QToolButton | None = dialog.findChild(QToolButton, "backButton")
        assert isinstance(back_button, QToolButton)
        self.backButton: QToolButton = back_button

        forward_button: QToolButton | None = dialog.findChild(QToolButton, "forwardButton")
        assert isinstance(forward_button, QToolButton)
        self.forwardButton: QToolButton = forward_button

        to_parent_button: QToolButton | None = dialog.findChild(QToolButton, "toParentButton")
        assert isinstance(to_parent_button, QToolButton)
        self.toParentButton: QToolButton = to_parent_button

        new_folder_button: QToolButton | None = dialog.findChild(QToolButton, "newFolderButton")
        assert isinstance(new_folder_button, QToolButton)
        self.newFolderButton: QToolButton = new_folder_button

        list_mode_button: QToolButton | None = dialog.findChild(QToolButton, "listModeButton")
        assert isinstance(list_mode_button, QToolButton)
        self.listModeButton: QToolButton = list_mode_button

        detail_mode_button: QToolButton | None = dialog.findChild(QToolButton, "detailModeButton")
        assert isinstance(detail_mode_button, QToolButton)
        self.detailModeButton: QToolButton = detail_mode_button

        # Splitter
        splitter: QSplitter | None = dialog.findChild(QSplitter, "splitter")
        assert isinstance(splitter, QSplitter)
        self.splitter: QSplitter = splitter

        # Sidebar
        sidebar: QFrame | None = dialog.findChild(QFrame, "sidebar")  # QFileDialogSidebar
        assert isinstance(sidebar, QFrame)
        self.sidebar: QFrame = sidebar

        # Main frame
        frame: QFrame | None = dialog.findChild(QFrame, "frame")
        assert isinstance(frame, QFrame)
        self.frame: QFrame = frame

        # Stacked widget for list and tree views
        stacked_widget: QStackedWidget | None = dialog.findChild(QStackedWidget, "stackedWidget")
        assert isinstance(stacked_widget, QStackedWidget)
        self.stackedWidget: QStackedWidget = stacked_widget
        assert self.stackedWidget.count() == 2, "StackedWidget should contain 2 pages"

        # List view page
        page: QWidget | None = self.stackedWidget.widget(0)
        assert isinstance(page, QWidget)
        self.page: QWidget = page

        list_view: QListView | None = dialog.findChild(QListView, "listView")  # QFileDialogListView
        assert isinstance(list_view, QListView)
        self.listView: QListView = list_view

        # Tree view page
        page_2: QWidget | None = self.stackedWidget.widget(1)
        assert isinstance(page_2, QWidget)
        self.page_2: QWidget = page_2

        tree_view: QTreeView | None = dialog.findChild(QTreeView, "treeView")  # QFileDialogTreeView
        assert isinstance(tree_view, QTreeView)
        self.treeView: QTreeView = tree_view

        # File name label and edit
        file_name_label: QLabel | None = dialog.findChild(QLabel, "fileNameLabel")
        assert isinstance(file_name_label, QLabel)
        self.fileNameLabel: QLabel = file_name_label

        file_name_edit: QLineEdit | None = dialog.findChild(QLineEdit, "fileNameEdit")  # QFileDialogLineEdit
        assert isinstance(file_name_edit, QLineEdit)
        self.fileNameEdit: QLineEdit = file_name_edit

        # Button box
        button_box: QDialogButtonBox | None = dialog.findChild(QDialogButtonBox, "buttonBox")
        assert isinstance(button_box, QDialogButtonBox)
        self.buttonBox: QDialogButtonBox = button_box

        # File type label and combo
        file_type_label: QLabel | None = dialog.findChild(QLabel, "fileTypeLabel")
        assert isinstance(file_type_label, QLabel)
        self.fileTypeLabel: QLabel = file_type_label

        file_type_combo: QComboBox | None = dialog.findChild(QComboBox, "fileTypeCombo")
        assert isinstance(file_type_combo, QComboBox)
        self.fileTypeCombo: QComboBox = file_type_combo

        # Define layouts based on found widgets
        vboxlayout: QLayout | None = self.frame.layout()
        assert isinstance(vboxlayout, QVBoxLayout)
        self.vboxlayout: QVBoxLayout = vboxlayout

        vboxlayout1: QLayout | None = self.page.layout()
        assert isinstance(vboxlayout1, QVBoxLayout)
        self.vboxlayout1: QVBoxLayout = vboxlayout1

        vboxlayout2: QLayout | None = self.page_2.layout()
        assert isinstance(vboxlayout2, QVBoxLayout)
        self.vboxlayout2: QVBoxLayout = vboxlayout2

        hboxlayout: QLayout | None = self.gridlayout.itemAtPosition(0, 1).layout()
        assert isinstance(hboxlayout, QHBoxLayout)
        self.hboxlayout: QHBoxLayout = hboxlayout

        # Assert correct widget containment
        assert self.gridlayout.itemAtPosition(0, 0).widget() == self.lookInLabel
        assert self.gridlayout.itemAtPosition(0, 1).layout() == self.hboxlayout
        assert self.gridlayout.itemAtPosition(1, 0).widget() == self.splitter
        assert self.gridlayout.itemAtPosition(2, 0).widget() == self.fileNameLabel
        assert self.gridlayout.itemAtPosition(2, 1).widget() == self.fileNameEdit
        assert self.gridlayout.itemAtPosition(2, 2).widget() == self.buttonBox
        assert self.gridlayout.itemAtPosition(3, 0).widget() == self.fileTypeLabel
        assert self.gridlayout.itemAtPosition(3, 1).widget() == self.fileTypeCombo

        assert self.hboxlayout.itemAt(0).widget() == self.lookInCombo
        assert self.hboxlayout.itemAt(1).widget() == self.backButton
        assert self.hboxlayout.itemAt(2).widget() == self.forwardButton
        assert self.hboxlayout.itemAt(3).widget() == self.toParentButton
        assert self.hboxlayout.itemAt(4).widget() == self.newFolderButton
        assert self.hboxlayout.itemAt(5).widget() == self.listModeButton
        assert self.hboxlayout.itemAt(6).widget() == self.detailModeButton

        assert self.splitter.widget(0) == self.sidebar
        assert self.splitter.widget(1) == self.frame

        assert self.vboxlayout.itemAt(0).widget() == self.stackedWidget

        assert self.stackedWidget.widget(0) == self.page
        assert self.stackedWidget.widget(1) == self.page_2

        assert self.vboxlayout1.itemAt(0).widget() == self.listView
        assert self.vboxlayout2.itemAt(0).widget() == self.treeView

        assert self.page.layout() == self.vboxlayout1
        assert self.page_2.layout() == self.vboxlayout2
        return self


class ExposedQFileDialog(QFileDialog):
    @overload
    def __init__(self, parent: QWidget | None = None, f: Qt.WindowType | None = None) -> None: ...
    @overload
    def __init__(self, parent: QWidget | None = None, caption: str | None = None, directory: str | None = None, filter: str | None = None) -> None: ...
    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.setOption(QFileDialog.Option.DontUseNativeDialog, True)  # noqa: FBT003
        self.setFileMode(QFileDialog.FileMode.Directory)
        self.setOption(QFileDialog.Option.ShowDirsOnly, False)  # noqa: FBT003
        self.qFileDialogUi = self.ui = Ui_ExposedQFileDialog()
        self.qFileDialogUi.setupUi(self)
        self.model_setup()

    def model_setup(self):
        assert self.qFileDialogUi.listView is not None, "QFileDialog ListView not found"
        assert self.qFileDialogUi.treeView is not None, "QFileDialog TreeView not found"
        fs_model: QAbstractItemModel = self.qFileDialogUi.treeView.model()  # same as self.listView.model()
        assert isinstance(fs_model, QFileSystemModel), "QFileSystemModel not found in treeView"
        assert fs_model is self.qFileDialogUi.listView.model(), "QFileSystemModel in treeView differs from listView's model?"
        self.fs_model: QFileSystemModel = fs_model


if __name__ == "__main__":
    from utility.ui_libraries.qt.common.actions_dispatcher import MenuActionsDispatcher
    from utility.ui_libraries.qt.common.tasks.actions_executor import FileActionsExecutor

    def on_task_failed(task_id: str, error: Exception):
        RobustLogger().exception(f"Task {task_id} failed", exc_info=error)
        error_msg = QMessageBox()
        error_msg.setIcon(QMessageBox.Icon.Critical)
        error_msg.setText(f"Task {task_id} failed")
        error_msg.setInformativeText(str(error))
        error_msg.setDetailedText("".join(traceback.format_exception(type(error), error, getattr(error, "__traceback__", None))))
        error_msg.setWindowTitle("Task Failed")
        error_msg.exec()

    app = QApplication(sys.argv)

    file_dialog = ExposedQFileDialog()
    # test this later.
    #file_dialog.proxy_model = QSortFilterProxyModel()
    #file_dialog.proxy_model.setSourceModel(file_dialog.fs_model)
    #file_dialog.setProxyModel(file_dialog.proxy_model)

    executor = FileActionsExecutor()
    executor.TaskFailed.connect(on_task_failed)
    dispatcher = MenuActionsDispatcher(file_dialog.fs_model, None, executor)

    def override_context_menu():
        views = file_dialog.findChildren(QAbstractItemView)

        for view in views:
            print(f"Setting context menu policy for view: {view.objectName()} of type: {type(view).__name__}")

            def show_context_menu(pos: QPoint, view: QAbstractItemView = view):
                index = view.indexAt(pos)
                if not index.isValid():
                    view.clearSelection()
                dispatcher.selection_model = view.selectionModel()
                menu = dispatcher.get_context_menu(view, pos)
                if menu:
                    menu.exec_(view.viewport().mapToGlobal(pos))

            view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            with contextlib.suppress(TypeError):
                view.customContextMenuRequested.disconnect()
            view.customContextMenuRequested.connect(show_context_menu)

    override_context_menu()

    file_dialog.resize(800, 600)
    file_dialog.show()

    sys.exit(app.exec())
