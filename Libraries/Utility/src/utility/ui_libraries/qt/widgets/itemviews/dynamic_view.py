from __future__ import annotations

from typing import TYPE_CHECKING, Literal, cast

from qtpy.QtCore import QEvent, Qt
from qtpy.QtGui import QWheelEvent
from qtpy.QtWidgets import QFileDialog, QStackedWidget

from utility.ui_libraries.qt.widgets.itemviews.abstractview import RobustAbstractItemView
from utility.ui_libraries.qt.widgets.itemviews.columnview import RobustColumnView  # noqa: F401
from utility.ui_libraries.qt.widgets.itemviews.headerview import RobustHeaderView  # noqa: F401
from utility.ui_libraries.qt.widgets.itemviews.listview import RobustListView
from utility.ui_libraries.qt.widgets.itemviews.tableview import RobustTableView
from utility.ui_libraries.qt.widgets.itemviews.tileview import RobustTileView
from utility.ui_libraries.qt.widgets.itemviews.treeview import RobustTreeView

if TYPE_CHECKING:
    from qtpy.QtCore import QObject
    from qtpy.QtWidgets import QWidget


class DynamicView(QStackedWidget):
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
        initial_view_mode: QFileDialog.ViewMode | None = None,
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

        self.current_view_mode: QFileDialog.ViewMode | None = initial_view_mode or QFileDialog.ViewMode
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

    def current_view(self) -> RobustAbstractItemView | QWidget:
        return cast(RobustAbstractItemView, self.currentWidget())

    def list_view(self) -> RobustListView | None:
        return next((view for view in self.all_views if isinstance(view, RobustListView)), None)

    def table_view(self) -> RobustTableView | None:
        return next((view for view in self.all_views if isinstance(view, RobustTableView)), None)

    def header_view(self) -> RobustHeaderView | None:
        return next((view for view in self.all_views if isinstance(view, RobustHeaderView)), None)

    def tiles_view(self) -> RobustTileView | None:
        return next((view for view in self.all_views if isinstance(view, RobustTileView)), None)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if isinstance(event, QEvent) and event.type() == QEvent.Wheel and isinstance(event, QWheelEvent) and bool(event.modifiers() & Qt.ControlModifier):
            delta: Literal[1, -1] = 1 if event.angleDelta().y() > 0 else -1
            self.current_view().set_text_size(self.current_view().get_text_size() + delta)
            return True

        return super().eventFilter(obj, event)


if __name__ == "__main__":
    from qtpy.QtGui import QStandardItem, QStandardItemModel
    from qtpy.QtWidgets import QApplication, QMainWindow, QStyle

    app = QApplication([])
    window = QMainWindow()
    view = DynamicView(window)

    model = QStandardItemModel()

    icons: list[QStyle.StandardPixmap] = [
        QStyle.StandardPixmap.SP_FileIcon,
        QStyle.StandardPixmap.SP_DirIcon,
        QStyle.StandardPixmap.SP_DriveHDIcon,
        QStyle.StandardPixmap.SP_DriveNetIcon,
        QStyle.StandardPixmap.SP_DriveFDIcon,
        QStyle.StandardPixmap.SP_DriveCDIcon,
        QStyle.StandardPixmap.SP_DesktopIcon,
        QStyle.StandardPixmap.SP_ComputerIcon,
        QStyle.StandardPixmap.SP_DirLinkIcon,
        QStyle.StandardPixmap.SP_FileLinkIcon,
    ]

    for i, icon_type in enumerate(icons):
        item = QStandardItem(app.style().standardIcon(icon_type), f"Item {i+1}")
        model.appendRow(item)
        for j in range(3):
            child = QStandardItem(app.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon), f"Child {i+1}.{j+1}")
            item.appendRow(child)

    cast(QAbstractItemView, view.currentWidget()).setModel(model)
    window.setCentralWidget(view)


    window.setGeometry(100, 100, 800, 600)
    window.show()
    app.exec()
