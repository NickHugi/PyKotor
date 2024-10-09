from __future__ import annotations

import sys
import traceback

from enum import Enum
from typing import TYPE_CHECKING, cast, overload

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from qtpy.QtCore import (
    QAbstractItemModel,
    QEvent,
    Qt,
)
from qtpy.QtGui import QMouseEvent
from qtpy.QtWidgets import QApplication, QFileDialog, QFileSystemModel, QMessageBox, QWidget

from utility.ui_libraries.qt.common.actions_dispatcher import ActionsDispatcher
from utility.ui_libraries.qt.common.tasks.actions_executor import FileActionsExecutor
from utility.ui_libraries.qt.filesystem.qfiledialogextended.ui_qfiledialogextended import Ui_QFileDialogExtended
from utility.ui_libraries.qt.widgets.itemviews.treeview import RobustTreeView
from utility.ui_libraries.qt.widgets.widgets.stacked_view import DynamicStackedView

if TYPE_CHECKING:
    from qtpy.QtCore import QAbstractItemModel, QModelIndex, QObject, QPoint
    from qtpy.QtWidgets import QAbstractItemView, QListView, QTreeView



class ReplaceStrategy(Enum):
    RECREATION_EXTENDED = "recreation_extended"
    RECREATION = "recreation"
    CLASS_REASSIGN = "class_reassign"


class QFileDialogExtended(QFileDialog):
    @overload
    def __init__(self, parent: QWidget | None = None, f: Qt.WindowType | None = None) -> None: ...
    @overload
    def __init__(self, parent: QWidget | None = None, caption: str | None = None, directory: str | None = None, filter: str | None = None) -> None: ...
    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        QFileDialog.__init__(self, *args, **kwargs)
        self.setOption(QFileDialog.Option.DontUseNativeDialog, True)  # noqa: FBT003
        self.setFileMode(QFileDialog.FileMode.Directory)
        self.setOption(QFileDialog.Option.ShowDirsOnly, False)  # noqa: FBT003
        self.ui: Ui_QFileDialogExtended = Ui_QFileDialogExtended()
        self.ui.setupUi(self)
        self.model_setup()
        self.executor: FileActionsExecutor = FileActionsExecutor()
        self.dispatcher: ActionsDispatcher = ActionsDispatcher(self.model, self, self.executor)
        self.connect_signals()
        self.setMouseTracking(True)
        #self.installEventFilter(self)
        #self.ui.listView.installEventFilter(self)
        #self.ui.listView.setMouseTracking(True)
        #self.ui.listView.viewport().installEventFilter(self)
        #self.ui.listView.viewport().setMouseTracking(True)
        #self.ui.treeView.installEventFilter(self)
        #self.ui.treeView.setMouseTracking(True)
        #self.ui.treeView.viewport().installEventFilter(self)
        #self.ui.treeView.viewport().setMouseTracking(True)
        #self.ui.stackedWidget.installEventFilter(self)
        #self.ui.sidebar.installEventFilter(self)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.MouseMove:
            mouse_event = cast(QMouseEvent, event)
            print("MouseMove event", mouse_event.pos())
            widget = self.childAt(mouse_event.pos())
            if widget:
                self.print_widget_info(widget)
            return False  # Let the event propagate
        return super().eventFilter(obj, event)

    def print_widget_info(self, widget: QWidget) -> None:
        print(
            f"Widget under mouse cls name: {widget.__class__.__name__}",
            "objectName:",
            widget.objectName(),
            "parent cls name:",
            widget.parent().__class__.__name__,
            f"parent objectName: {'' if widget.parent() is None else widget.parent().objectName()}",
        )

        # Recursively print info for child widgets
        for child in widget.children():
            if isinstance(child, QWidget):
                print(f"Child of {widget.objectName()}:")
                self.print_widget_info(child)

    def _q_showListView(self) -> None:
        """Changes the current view to list mode.

        This provides users with a different way to visualize the file system contents.

        If this function is removed, users would lose the ability to switch to list view,
        limiting the flexibility of the file dialog's interface.
        """
        assert self.ui is not None, f"{type(self).__name__}._q_showListView: No UI setup."
        self.ui.listModeButton.setDown(True)
        self.ui.detailModeButton.setDown(False)
        self.ui.treeView.hide()
        self.ui.listView.show()
        parent = self.ui.listView.parent()
        assert parent is self.ui.page, f"{type(self).__name__}._q_showListView: parent is not self.ui.page"
        self.ui.stackedWidget.setCurrentWidget(cast(QWidget, parent))
        self.setViewMode(QFileDialog.ViewMode.List)

    def _q_showDetailsView(self) -> None:
        """Changes the current view to details mode.

        This provides users with a more detailed view of file system contents.

        If this function is removed, users would lose the ability to switch to details view,
        limiting the flexibility of the file dialog's interface.
        """
        self.ui.listModeButton.setDown(False)
        self.ui.detailModeButton.setDown(True)
        self.ui.listView.hide()
        self.ui.treeView.show()
        parent = self.ui.treeView.parent()
        assert parent is self.ui.page_2, f"{type(self).__name__}._q_showDetailsView: parent is not self.ui.page"
        self.ui.stackedWidget.setCurrentWidget(cast(QWidget, parent))
        self.setViewMode(QFileDialog.ViewMode.Detail)

    def override_ui(self):

        # Replace treeView
        self.ui.stackedWidget.__class__ = DynamicStackedView
        DynamicStackedView.__init__(
            self.ui.stackedWidget,
            self.ui.frame,
            [self.ui.page, self.ui.page_2],
            should_call_qt_init=False,
        )
        self.ui.treeView.__class__ = RobustTreeView
        assert isinstance(self.ui.treeView, RobustTreeView)
        RobustTreeView.__init__(self.ui.treeView, self.ui.page_2, should_call_qt_init=False)
        cast(RobustTreeView, self.ui.treeView).setParent(self.ui.page_2)
        cast(RobustTreeView, self.ui.treeView).setObjectName("treeView")
        cast(RobustTreeView, self.ui.treeView).setModel(self.model)
        self.ui.vboxlayout2.update()

        self.ui.listModeButton.clicked.connect(self._q_showListView)
        self.ui.detailModeButton.clicked.connect(self._q_showDetailsView)

    def currentView(self) -> QAbstractItemView | None:
        assert self.ui is not None, f"{type(self).__name__}.currentView: UI is None"
        assert self.ui.stackedWidget is not None, f"{type(self).__name__}.currentView: stackedWidget is None"
        if isinstance(self.ui.stackedWidget, DynamicStackedView):
            return self.ui.stackedWidget.current_view()
        # vanilla logic.
        if self.ui.stackedWidget.currentWidget() == self.ui.listView.parent():
            return self.ui.listView
        return self.ui.treeView

    def mapToSource(self, index: QModelIndex) -> QModelIndex:
        proxy_model_lookup = self.proxyModel()
        return index if proxy_model_lookup is None else proxy_model_lookup.mapToSource(index)

    def _q_showContextMenu(self, position: QPoint) -> None:
        assert self.ui is not None, f"{type(self).__name__}._q_showContextMenu: No UI setup."
        assert self.model is not None, f"{type(self).__name__}._q_showContextMenu: No file system model setup."

        view: QAbstractItemView | None = self.currentView()
        assert view is not None, f"{type(self).__name__}._q_showContextMenu: No view found."

        index = view.indexAt(position)
        index = self.mapToSource(index.sibling(index.row(), 0))

        index = view.indexAt(position)
        if not index.isValid():
            view.clearSelection()
        menu = self.dispatcher.get_context_menu(view, position)
        menu.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)  # noqa: FBT003
        menu.exec(view.viewport().mapToGlobal(position))

    def model_setup(self):
        fs_model: QAbstractItemModel = self.ui.treeView.model()  # same as self.listView.model()
        assert isinstance(fs_model, QFileSystemModel), "QFileSystemModel not found in treeView"
        assert fs_model is self.ui.listView.model(), "QFileSystemModel in treeView differs from listView's model?"
        self.model: QFileSystemModel = fs_model

    def connect_signals(self):
        self.ui.treeView.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.listView.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        def show_context_menu(pos: QPoint, view: QListView | QTreeView):
            index = view.indexAt(pos)
            if not index.isValid():
                view.clearSelection()
            menu = self.dispatcher.get_context_menu(view, pos)
            if menu:
                menu.exec_(view.viewport().mapToGlobal(pos))

        self.ui.treeView.customContextMenuRequested.disconnect()
        self.ui.listView.customContextMenuRequested.disconnect()
        self.ui.treeView.customContextMenuRequested.connect(lambda pos: show_context_menu(pos, self.ui.treeView))
        self.ui.listView.customContextMenuRequested.connect(lambda pos: show_context_menu(pos, self.ui.listView))
        self.ui.treeView.doubleClicked.connect(self.dispatcher.on_open)

    def on_task_failed(self, task_id: str, error: Exception):
        RobustLogger().exception(f"Task {task_id} failed", exc_info=error)
        error_msg = QMessageBox()
        error_msg.setIcon(QMessageBox.Icon.Critical)
        error_msg.setText(f"Task {task_id} failed")
        error_msg.setInformativeText(str(error))
        error_msg.setDetailedText("".join(traceback.format_exception(type(error), error, None)))
        error_msg.setWindowTitle("Task Failed")
        error_msg.exec_()


if __name__ == "__main__":
    import faulthandler
    import sys
    import traceback
    faulthandler.enable()

    app = QApplication(sys.argv)

    file_dialog = QFileDialogExtended(None, Qt.WindowType.Window)
    file_dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)  # noqa: FBT003
    file_dialog.setFileMode(QFileDialog.FileMode.Directory)
    file_dialog.setOption(QFileDialog.Option.ShowDirsOnly, False)  # noqa: FBT003
    file_dialog.override_ui()

    file_dialog.resize(800, 600)
    file_dialog.show()

    sys.exit(app.exec())
