from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

from qtpy.QtCore import QEvent, QItemSelectionModel, QModelIndex, QSize, Qt
from qtpy.QtGui import QWheelEvent
from qtpy.QtWidgets import QListView, QStackedWidget, QTableView

from utility.ui_libraries.qt.widgets.itemviews.columnview import RobustColumnView
from utility.ui_libraries.qt.widgets.itemviews.headerview import RobustHeaderView
from utility.ui_libraries.qt.widgets.itemviews.listview import RobustListView
from utility.ui_libraries.qt.widgets.itemviews.tableview import RobustTableView
from utility.ui_libraries.qt.widgets.itemviews.tileview import RobustTileView
from utility.ui_libraries.qt.widgets.itemviews.treeview import RobustTreeView

if TYPE_CHECKING:
    from qtpy.QtCore import QObject, QRect
    from qtpy.QtGui import QMouseEvent
    from qtpy.QtWidgets import QWidget

    from utility.ui_libraries.qt.widgets.itemviews.abstractview import RobustAbstractItemView


class ViewMode(Enum):
    DETAILS = auto()
    LIST = auto()
    TILES = auto()
    COLUMN = auto()
    TREE = auto()
    HEADER = auto()


class RobustTableView(RobustTableView):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

    def setSelection(self, rect: QRect, command: QItemSelectionModel.SelectionFlags):
        index = self.indexAt(rect.topLeft())
        if index.isValid() and index.column() == 0:
            # Only allow selection if the click is in the first column
            super().setSelection(rect, command)
        else:
            # Clear selection if click is outside the first column
            self.clearSelection()

    def mousePressEvent(self, event: QMouseEvent):
        index = self.indexAt(event.pos())
        if index.isValid() and index.column() == 0:
            super().mousePressEvent(event)
        else:
            # Clear selection and reset the selection anchor
            self.clearSelection()

    def mouseReleaseEvent(self, event: QMouseEvent):
        index = self.indexAt(event.pos())
        if index.isValid() and index.column() == 0:
            super().mouseReleaseEvent(event)
        else:
            event.ignore()

    def clearSelection(self):
        self.selectionModel().clear()
        self.selectionModel().reset()
        self.selectionModel().setCurrentIndex(QModelIndex(), QItemSelectionModel.Clear)
        self.selectionModel().select(QModelIndex(), QItemSelectionModel.Clear | QItemSelectionModel.Rows)


def change_view_mode(proxy_view: DynamicView, mode: ViewMode):
    cur_size = QSize(16, 16)
    if mode == ViewMode.LIST:
        cur_view = next((view for view in proxy_view.all_views if isinstance(view, QListView) and not isinstance(view, RobustTileView)), None)
        if cur_view is None:
            return
        proxy_view.current_view_mode = ViewMode.LIST
        cur_view.setViewMode(QListView.ListMode)
        cur_view.setGridSize(QSize())
    elif mode == ViewMode.DETAILS:
        cur_view = next((view for view in proxy_view.all_views if isinstance(view, QTableView)), None)
        if cur_view is None:
            return
        proxy_view.current_view_mode = ViewMode.DETAILS
        cur_view.setShowGrid(False)
        cur_view.setSelectionBehavior(QTableView.SelectRows)
    elif mode == ViewMode.TILES:
        cur_view = next((view for view in proxy_view.all_views if isinstance(view, RobustTileView)), None)
        if cur_view is None:
            return
        proxy_view.current_view_mode = ViewMode.TILES
        cur_size = QSize(32, 32)
        cur_view.setGridSize(QSize(120, 80))
    proxy_view.setCurrentWidget(cur_view)
    cur_view.setIconSize(cur_size)
    update_view(proxy_view)


def change_icon_size(proxy_view: DynamicView, delta: float):
    new_mult = max(
        1.0,
        min(proxy_view.maximum_mult, proxy_view.icon_size_mult + delta),
    )
    if new_mult != proxy_view.icon_size_mult:
        proxy_view.icon_size_mult = new_mult

        if proxy_view.icon_size_mult <= proxy_view.details_max_mult:
            table_view = next((view for view in proxy_view.all_views if isinstance(view, QTableView)), None)
            if table_view is None:
                return
            proxy_view.current_view_mode = ViewMode.DETAILS
            proxy_view.setCurrentWidget(table_view)
        elif proxy_view.list_min_mult <= proxy_view.icon_size_mult <= proxy_view.list_max_mult:
            list_view = next((view for view in proxy_view.all_views if isinstance(view, QListView) and not isinstance(view, RobustTileView)), None)
            if list_view is None:
                return
            proxy_view.current_view_mode = ViewMode.LIST
            proxy_view.setCurrentWidget(list_view)
        else:
            tiles_view = next((view for view in proxy_view.all_views if isinstance(view, RobustTileView)), None)
            if tiles_view is None:
                return
            proxy_view.current_view_mode = ViewMode.TILES
            proxy_view.setCurrentWidget(tiles_view)

        update_view(proxy_view)


def update_view(proxy_view: DynamicView):
    proxy_view.icon_size = int(proxy_view.base_icon_size * proxy_view.icon_size_mult)
    icon_size = QSize(proxy_view.icon_size, proxy_view.icon_size)

    if proxy_view.current_view_mode == ViewMode.DETAILS:
        table_view = next((view for view in proxy_view.all_views if isinstance(view, QTableView)), None)
        if table_view is None:
            return
        table_view.setShowGrid(False)
        table_view.setSelectionBehavior(QTableView.SelectRows)
        table_view.resizeColumnsToContents()
        table_view.horizontalHeader().setStretchLastSection(True)
    elif proxy_view.current_view_mode == ViewMode.LIST:
        list_view = next((view for view in proxy_view.all_views if isinstance(view, QListView) and not isinstance(view, RobustTileView)), None)
        if list_view is None:
            return
        list_view.setViewMode(QListView.ListMode)
        list_view.setResizeMode(QListView.Adjust)
        list_view.setWrapping(False)
        list_view.setUniformItemSizes(True)
        list_view.setModelColumn(0)
    proxy_view.currentWidget().setIconSize(icon_size)


ignored_attrs = (
    "currentWidget",
    "all_views",
    "current_view_mode",
    "base_icon_size",
    "base_mult",
    "icon_size",
    "icon_size_mult",
    "details_max_mult",
    "list_max_mult",
    "view_transition_mult",
    "list_min_mult",
    "maximum_mult",
    "setCurrentWidget",
)


if TYPE_CHECKING:
    class _Inherit(
        QStackedWidget,
        RobustListView,
        RobustTreeView,
        RobustHeaderView,
        RobustTableView,
        RobustColumnView,
    ): ...
else:
    _Inherit = QStackedWidget

class DynamicView(_Inherit):
    def __init__(
        self,
        parent: QWidget | None = None,
        base_icon_size: int = 16,
        icon_size_mult: float = 1.1,
        details_max_mult: float = 1.5,
        list_max_mult: float = 4.0,
        view_transition_mult: float = 25 / 24,
        maximum_mult: float = 16.0,
        all_views: list[RobustAbstractItemView] | None = None,
        initial_view_mode: ViewMode | None = None,
        initial_view: RobustAbstractItemView | None = None,
    ):
        super().__init__(parent)
        self.base_icon_size: int = base_icon_size
        self.icon_size: int = self.base_icon_size
        self.icon_size_mult: float = icon_size_mult
        self.details_max_mult: float = details_max_mult
        self.list_max_mult: float = list_max_mult
        self.view_transition_mult: float = view_transition_mult
        self.list_min_mult: float = self.details_max_mult * self.view_transition_mult
        self.maximum_mult: float = maximum_mult

        self.current_view_mode: ViewMode | None = initial_view_mode or ViewMode.DETAILS
        self.all_views: list[RobustAbstractItemView] = all_views or [
            RobustListView(self),
            RobustTreeView(self),
            RobustColumnView(self),
            RobustTableView(self),
            RobustTileView(self),
            RobustHeaderView(self),
        ]
        for view in self.all_views:
            view.setParent(self)
            view.hide()
            view.installEventFilter(self)
            view.viewport().installEventFilter(self)
            self.addWidget(view)
        initial_view = initial_view or self.all_views[0]
        self.setCurrentWidget(initial_view)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if isinstance(event, QEvent) and event.type() == QEvent.Wheel and isinstance(event, QWheelEvent) and bool(event.modifiers() & Qt.ControlModifier):
            delta = event.angleDelta().y() / 120  # Should become 1 or -1
            change_icon_size(self, delta)
            return True
        return super().eventFilter(obj, event)


if __name__ == "__main__":
    from qtpy.QtGui import QStandardItem, QStandardItemModel
    from qtpy.QtWidgets import QApplication, QMainWindow, QStyle

    app = QApplication([])
    window = QMainWindow()
    view = DynamicView(window)

    model = QStandardItemModel()
    icons = [
        QStyle.SP_FileIcon,
        QStyle.SP_DirIcon,
        QStyle.SP_DriveHDIcon,
        QStyle.SP_DriveNetIcon,
        QStyle.SP_DriveFDIcon,
        QStyle.SP_DriveCDIcon,
        QStyle.SP_DesktopIcon,
        QStyle.SP_ComputerIcon,
        QStyle.SP_DirLinkIcon,
        QStyle.SP_FileLinkIcon
    ]

    for i, icon_type in enumerate(icons):
        item = QStandardItem(app.style().standardIcon(icon_type), f"Item {i+1}")
        model.appendRow(item)
        for j in range(3):
            child = QStandardItem(app.style().standardIcon(QStyle.SP_FileIcon), f"Child {i+1}.{j+1}")
            item.appendRow(child)

    view.currentWidget().setModel(model)
    change_view_mode(view, ViewMode.DETAILS)
    window.setCentralWidget(view)
    window.setGeometry(100, 100, 800, 600)
    window.show()
    app.exec()
