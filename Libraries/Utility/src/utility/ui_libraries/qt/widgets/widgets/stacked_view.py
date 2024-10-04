from __future__ import annotations

import sys

from typing import TYPE_CHECKING, Literal, TypeVar, cast

from qtpy.QtCore import QEvent, QItemSelectionModel, QModelIndex, QSize, Qt  # pyright: ignore[reportPrivateImportUsage]
from qtpy.QtGui import QWheelEvent
from qtpy.QtWidgets import QApplication, QStackedWidget

from utility.ui_libraries.qt.widgets.itemviews.abstractview import RobustAbstractItemView
from utility.ui_libraries.qt.widgets.itemviews.columnview import RobustColumnView  # noqa: F401
from utility.ui_libraries.qt.widgets.itemviews.headerview import RobustHeaderView  # noqa: F401
from utility.ui_libraries.qt.widgets.itemviews.listview import RobustListView
from utility.ui_libraries.qt.widgets.itemviews.tableview import RobustTableView
from utility.ui_libraries.qt.widgets.itemviews.treeview import RobustTreeView

if TYPE_CHECKING:
    from qtpy.QtCore import QAbstractItemModel, QObject
    from qtpy.QtGui import QIcon
    from qtpy.QtWidgets import QFileDialog, QWidget


T = TypeVar("T", bound=RobustAbstractItemView)


class DynamicStackedView(QStackedWidget):
    def __init__(
        self,
        parent: QWidget | None = None,
        all_views: list[RobustAbstractItemView | QWidget] | None = None,
        initial_view_mode: QFileDialog.ViewMode | RobustListView.ViewMode | None = None,
        initial_view: RobustAbstractItemView | QWidget | None = None,
        *,
        should_call_qt_init: bool = True,
    ):
        if should_call_qt_init:
            super().__init__(parent)
        self.current_view_mode: RobustListView.ViewMode | QFileDialog.ViewMode = initial_view_mode or RobustListView.ViewMode.ListMode
        if all_views:
            self.all_views = all_views
        else:
            list_view_icon_mode = RobustListView(self)
            list_view_icon_mode.setViewMode(RobustListView.ViewMode.IconMode)
            self.all_views: list[RobustAbstractItemView | QWidget] = [
                RobustTreeView(self),
                RobustTableView(self),
                #RobustHeaderView(self),
                RobustColumnView(self),
                list_view_icon_mode,
            ]
        for view in self.all_views:
            view.setParent(self)
            view.hide()
            view.installEventFilter(self)
            self.addWidget(view)
        self.setCurrentWidget(initial_view or self.all_views[0])

        self.min_text_size = 6
        self.current_view_index = 0

        # Set up a common selection model
        first_view = self.get_actual_view(self.all_views[0])
        common_selection_model = first_view.selectionModel() if first_view else None
        if common_selection_model is None:
            self.common_selection_model = QItemSelectionModel(first_view.model() if first_view else None)
        else:
            self.common_selection_model = common_selection_model
        for view in self.all_views:
            actual_view = self.get_actual_view(view)
            if actual_view:
                actual_view.setSelectionModel(self.common_selection_model)

    def get_actual_view(self, widget: QWidget, cls: type[T] = RobustAbstractItemView) -> T | None:
        if isinstance(widget, RobustAbstractItemView):
            return cast(cls, widget)
        for child in widget.findChildren(RobustAbstractItemView):
            return cast(cls, child)
        return None

    def setModel(self, model: QAbstractItemModel) -> None:
        for view in self.all_views:
            actual_view = self.get_actual_view(view)
            if actual_view:
                actual_view.setModel(model)

    def current_view(self) -> RobustAbstractItemView | None:
        return self.get_actual_view(self.currentWidget())

    def list_view(self) -> RobustListView | None:
        return next((self.get_actual_view(view) for view in self.all_views if isinstance(self.get_actual_view(view), RobustListView)), None)

    def table_view(self) -> RobustTableView | None:
        return next((self.get_actual_view(view) for view in self.all_views if isinstance(self.get_actual_view(view), RobustTableView)), None)

    def header_view(self) -> RobustHeaderView | None:
        return next((self.get_actual_view(view) for view in self.all_views if isinstance(self.get_actual_view(view), RobustHeaderView)), None)

    def column_view(self) -> RobustColumnView | None:
        return next((self.get_actual_view(view) for view in self.all_views if isinstance(self.get_actual_view(view), RobustColumnView)), None)

    def tree_view(self) -> RobustTreeView | None:
        return next((self.get_actual_view(view) for view in self.all_views if isinstance(self.get_actual_view(view), RobustTreeView)), None)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if (
            isinstance(event, QEvent)
            and event.type() == QEvent.Type.Wheel
            and isinstance(event, QWheelEvent)
            and bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
        ):
            delta: Literal[1, -1] = 1 if event.angleDelta().y() > 0 else -1
            self.adjust_view_size(delta)
            return True

        return super().eventFilter(obj, event)

    def adjust_view_size(self, delta: int) -> None:
        current_view = self.current_view()
        if not current_view:
            return
        new_text_size = current_view.get_text_size() + delta
        new_text_size = max(self.min_text_size, new_text_size)

        if delta > 0 and not self.is_size_suitable_for_view():
            self.switch_to_next_view()
        elif delta < 0 and new_text_size <= self.min_text_size:
            self.switch_to_previous_view()
        else:
            current_view.set_text_size(new_text_size)
            self.update_icon_size(new_text_size)

    def is_size_suitable_for_view(self, max_item_percent: float = 0.1) -> bool:
        current_view = self.current_view()
        if not current_view:
            return False
        viewport = current_view.viewport()
        model = current_view.model()
        if not viewport or not model:
            return False

        viewport_size = viewport.size()
        item_size = current_view.visualRect(model.index(0, 0)).size()

        viewport_area = viewport_size.width() * viewport_size.height()
        item_area = item_size.width() * item_size.height()

        max_allowed_area = viewport_area * max_item_percent

        if isinstance(current_view, RobustListView):
            return item_size.width() < 200

        if item_area > max_allowed_area:
            return False

        if item_size.width() == 0 or item_size.height() == 0:
            return False

        items_per_row = viewport_size.width() // item_size.width()
        items_per_column = viewport_size.height() // item_size.height()
        visible_items = items_per_row * items_per_column
        total_items = model.rowCount() * model.columnCount()

        if visible_items == 0:
            return False

        font_metrics = current_view.fontMetrics()
        item_text = model.data(model.index(0, 0))
        if (
            isinstance(item_text, str)
            and font_metrics.horizontalAdvance(item_text) > item_size.width()
        ):
            return False

        return visible_items >= max_item_percent * total_items

    def update_icon_size(self, text_size: int) -> None:
        icon_size = QSize(int(text_size), int(text_size))
        for view in self.all_views:
            actual_view = self.get_actual_view(view)
            if actual_view:
                actual_view.setIconSize(icon_size)

    def switch_to_next_view(self) -> None:
        if self.current_view_index < len(self.all_views) - 1:
            self.current_view_index += 1
            current_view = self.get_actual_view(self.all_views[self.current_view_index])
            model = current_view.model() if current_view else None
            while (
                self.current_view_index < len(self.all_views) - 1
                and isinstance(current_view, RobustTableView)
                and model is not None
                and model.columnCount() == 1
            ):
                self.current_view_index += 1
                current_view = self.get_actual_view(self.all_views[self.current_view_index])
                model = current_view.model() if current_view else None
            self.setCurrentWidget(self.all_views[self.current_view_index])
            for view in self.all_views:
                actual_view = self.get_actual_view(view)
                if actual_view:
                    actual_view.set_text_size(self.min_text_size)
            self.update_icon_size(self.min_text_size)

    def switch_to_previous_view(self) -> None:
        if self.current_view_index > 0:
            self.current_view_index -= 1
            current_view = self.get_actual_view(self.all_views[self.current_view_index])
            model = current_view.model() if current_view else None
            while (
                self.current_view_index > 0
                and isinstance(current_view, RobustTableView)
                and model is not None
                and model.columnCount() == 1
            ):
                self.current_view_index -= 1
                current_view = self.get_actual_view(self.all_views[self.current_view_index])
                model = current_view.model() if current_view else None
            self.setCurrentWidget(self.all_views[self.current_view_index])
            for view in self.all_views:
                actual_view = self.get_actual_view(view)
                if actual_view:
                    actual_view.set_text_size(64)
            self.update_icon_size(64)

    def setCurrentWidget(self, widget: QWidget) -> None:
        super().setCurrentWidget(widget)
        if widget not in self.all_views:
            self.all_views.append(widget)
        self.current_view_index = self.all_views.index(widget)

    def setRootIndex(self, index: QModelIndex) -> None:
        for view in self.all_views:
            actual_view = self.get_actual_view(view)
            if actual_view:
                actual_view.setRootIndex(index)

    def rootIndex(self) -> QModelIndex:
        current_view = self.current_view()
        return current_view.rootIndex() if current_view else QModelIndex()

    def clearSelection(self) -> None:
        for view in self.all_views:
            actual_view = self.get_actual_view(view)
            if actual_view:
                actual_view.clearSelection()

    def selectionModel(self) -> QItemSelectionModel:
        return self.common_selection_model

    def selectedIndexes(self) -> list[QModelIndex]:
        current_view = self.current_view()
        return current_view.selectedIndexes() if current_view else []

    def selectAll(self) -> None:
        current_view = self.current_view()
        if current_view:
            current_view.selectAll()


if __name__ == "__main__":
    from qtpy.QtGui import QStandardItem, QStandardItemModel
    from qtpy.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget

    app = QApplication(sys.argv)
    window = QMainWindow()
    central_widget = QWidget()
    layout = QVBoxLayout(central_widget)

    label = QLabel()
    layout.addWidget(label)

    stacked_widget = DynamicStackedView(window)
    layout.addWidget(stacked_widget)

    window.setCentralWidget(central_widget)

    model = QStandardItemModel()

    icons: list[QIcon] = [
        QApplication.style().standardIcon(getattr(QApplication.style().StandardPixmap, attr))
        for attr in dir(QApplication.style().StandardPixmap)
        if not attr.startswith("_") and attr not in (
            "as_integer_ratio",
            "bit_length",
            "conjugate",
            "denominator",
            "from_bytes",
            "imag",
            "numerator",
            "real",
            "to_bytes",
        )
    ]
    import random

    for i in range(len(icons)):
        item = QStandardItem(icons[i], f"Item {i+1}")
        model.appendRow(item)
        for _ in range(random.randint(0, 5)):  # noqa: S311
            child = QStandardItem(
                icons[random.randint(0, len(icons) - 1)],  # noqa: S311
                f"Child {i+1}.{_+1}",
            )
            item.appendRow(child)

    stacked_widget.setModel(model)

    def update_label():
        label.setText(f"Current View: {stacked_widget.current_view().__class__.__name__}")

    stacked_widget.currentChanged.connect(update_label)
    update_label()  # Initial update

    window.setGeometry(100, 100, 1200, 800)
    window.show()
    app.exec()
