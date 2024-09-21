from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Sequence, cast

from qtpy.QtCore import QEvent, QSize, Qt
from qtpy.QtGui import QWheelEvent
from qtpy.QtWidgets import QStackedWidget

from utility.ui_libraries.qt.widgets.itemviews.abstractview import QAbstractItemView
from utility.ui_libraries.qt.widgets.itemviews.columnview import QColumnView  # noqa: F401
from utility.ui_libraries.qt.widgets.itemviews.headerview import QHeaderView  # noqa: F401
from utility.ui_libraries.qt.widgets.itemviews.html_delegate import HTMLDelegate
from utility.ui_libraries.qt.widgets.itemviews.listview import RobustListView
from utility.ui_libraries.qt.widgets.itemviews.tableview import RobustTableView
from utility.ui_libraries.qt.widgets.itemviews.tileview import RobustTileView
from utility.ui_libraries.qt.widgets.itemviews.treeview import RobustTreeView

if TYPE_CHECKING:
    from qtpy.QtCore import QObject
    from qtpy.QtWidgets import QAbstractItemDelegate, QWidget


class DynamicStackWidget(QStackedWidget):
    def __init__(
        self,
        parent: QWidget | None = None,
        base_icon_size: int = 16,
        min_icon_size: int = 8,
        all_views: list[QAbstractItemView] | None = None,
        initial_view: QAbstractItemView | None = None,
    ):
        super().__init__(parent)
        self.base_icon_size: int = base_icon_size
        self.icon_size: int = base_icon_size
        self.min_icon_size: int = 8
        self.all_views: Sequence[QAbstractItemView] = all_views or [
            RobustListView(self),
            RobustTreeView(self),
            RobustTileView(self),
            RobustTableView(self),
        ]

        for view in self.all_views:
            self._setup_view(view)

        self.setCurrentWidget(initial_view or self.all_views[0])

    def _setup_view(self, view: QAbstractItemView):
        view.setParent(self)
        view.installEventFilter(self)
        view.viewport().installEventFilter(self)
        self.addWidget(view)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if isinstance(event, QWheelEvent) and event.type() == QEvent.Type.Wheel and bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            delta: Literal[1, -1] = 1 if event.angleDelta().y() > 0 else -1
            self.change_icon_and_view(delta)
            return True
        return super().eventFilter(obj, event)

    def change_icon_and_view(self, delta: Literal[1, -1]):
        new_icon_size = self.icon_size + delta * 2
        new_icon_size = max(6, min(new_icon_size, 128))

        current_index = self.all_views.index(self.currentWidget())
        new_index = current_index

        if delta > 0 and new_icon_size > 48 and current_index < len(self.all_views) - 1:
            print(self.all_views[current_index].__class__.__name__, "->", self.all_views[current_index + 1].__class__.__name__, new_icon_size)
            new_index = current_index + 1
            new_icon_size = 6


        if delta < 0 and new_icon_size < 24 and current_index > 0:
            print(self.all_views[current_index].__class__.__name__, "->", self.all_views[current_index - 1].__class__.__name__, new_icon_size)
            new_index = current_index - 1
            new_icon_size = 48

        if new_index != current_index:
            print(self.all_views[new_index].__class__.__name__, new_icon_size)
            self.setCurrentWidget(self.all_views[new_index])

        self.icon_size = new_icon_size

        self.update_icon_size(self.currentWidget())

    def treeView(self) -> RobustTreeView:
        return cast(RobustTreeView, self.all_views[1])

    def listView(self) -> RobustListView:
        return cast(RobustListView, self.all_views[0])

    def tileView(self) -> RobustTileView:
        return cast(RobustTileView, self.all_views[2])

    def tableView(self) -> RobustTableView:
        return cast(RobustTableView, self.all_views[3])

    def update_icon_size(self, view: QAbstractItemView):
        delegate: QAbstractItemDelegate | None = view.itemDelegate()
        if isinstance(delegate, HTMLDelegate):
            delegate.set_text_size(self.icon_size)
            return
        view.setIconSize(QSize(self.icon_size, self.icon_size))





if __name__ == "__main__":
    from qtpy.QtGui import QStandardItem, QStandardItemModel
    from qtpy.QtWidgets import QApplication, QMainWindow, QStyle

    app = QApplication([])
    window = QMainWindow()
    view = DynamicStackWidget(window)

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
