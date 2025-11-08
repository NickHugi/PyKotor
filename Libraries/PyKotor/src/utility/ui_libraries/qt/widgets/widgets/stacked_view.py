from __future__ import annotations

import sys

from typing import TYPE_CHECKING, Literal, Optional, TypeVar, cast

from qtpy.QtCore import QAbstractItemModel, QItemSelectionModel, QModelIndex, QSize, Qt  # pyright: ignore[reportPrivateImportUsage]
from qtpy.QtGui import QFont, QStandardItem, QStandardItemModel
from qtpy.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QColumnView,
    QHeaderView,
    QLabel,
    QListView,
    QMainWindow,
    QStackedWidget,
    QStyle,
    QTableView,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from utility.ui_libraries.qt.widgets.itemviews.abstractview import RobustAbstractItemView
from utility.ui_libraries.qt.widgets.itemviews.columnview import RobustColumnView  # noqa: F401

if TYPE_CHECKING:
    from collections.abc import Iterable

    from qtpy.QtCore import QAbstractItemModel
    from qtpy.QtGui import QFontMetrics, QIcon, QWheelEvent


T = TypeVar("T", bound=QAbstractItemView)


class DynamicStackedView(QStackedWidget):
    def __init__(
        self,
        parent: QWidget | None = None,
        all_views: list[QAbstractItemView | QWidget] | None = None,
        initial_view_mode: QListView.ViewMode | None = None,
        initial_view: QAbstractItemView | QWidget | None = None,
        *,
        should_call_qt_init: bool = True,
    ):
        if should_call_qt_init:
            super().__init__(parent)
        self.current_view_mode: QListView.ViewMode = initial_view_mode or QListView.ViewMode.ListMode
        if all_views:
            self.set_widgets(all_views)
        else:
            list_view_icon_mode = QListView(self)
            list_view_icon_mode.setViewMode(QListView.ViewMode.IconMode)
            self.set_widgets(
                [
                    QListView(self),
                    QTreeView(self),
                    QTableView(self),
                    QColumnView(self),
                    list_view_icon_mode,
                ],
            )
        self.setCurrentWidget(initial_view or self.all_widgets()[0])

        self.min_text_size = 6
        self.current_view_index: int = 0

        # Set up a common selection model
        first_view: QAbstractItemView = self.all_views()[0]
        common_selection_model: QItemSelectionModel | None = first_view.selectionModel()
        if common_selection_model is None:
            self.common_selection_model = QItemSelectionModel(first_view.model())
        else:
            self.common_selection_model: QItemSelectionModel = common_selection_model
        for widget in self.all_widgets():
            actual_view: QAbstractItemView = self.get_actual_view(widget)
            if actual_view:
                actual_view.setSelectionModel(self.common_selection_model)

    def all_widgets(self) -> tuple[QWidget, ...]:
        return tuple(cast(QWidget, self.widget(i)) for i in range(self.count()))

    def set_widgets(self, value: Iterable[QWidget]) -> None:
        for i, widget in enumerate(value):
            widget_container: QWidget = widget
            if isinstance(widget, QAbstractItemView):
                widget_container = QWidget()
                widget_container.setObjectName(f"dyn_stack_page_{i}")
                layout = QVBoxLayout(widget_container)
                layout.setContentsMargins(2, 2, 2, 2)
                layout.addWidget(widget)
            self.addWidget(widget_container)
            view: QAbstractItemView = self.get_actual_view(widget)
            if isinstance(view, RobustAbstractItemView):
                view.wheelEvent = self.wheelEvent
                assert view.__class__.wheelEvent is not self.wheelEvent

    def all_views(self) -> list[QAbstractItemView]:
        return [self.get_actual_view(widget) for widget in self.all_widgets()]

    def get_actual_view(
        self,
        widget: QWidget,
        cls: type[T] = QAbstractItemView,
    ) -> T:
        if isinstance(widget, QAbstractItemView):
            return cast(cls, widget)
        for child in widget.findChildren(QAbstractItemView):
            return cast(cls, child)
        raise ValueError(f"No view of type {cls.__name__} found in widget {widget.__class__.__name__}")

    def setModel(
        self,
        model: QAbstractItemModel,
    ) -> None:
        for view in self.all_views():
            view.setModel(model)

    def current_view(self) -> QAbstractItemView | None:
        current_widget: QWidget | None = self.currentWidget()
        if current_widget is None:
            return None
        return self.get_actual_view(current_widget)

    def list_view(self) -> QListView | None:
        for view in self.all_views():
            if isinstance(view, QListView):
                return cast(QListView, view)
        return None

    def table_view(self) -> QTableView | None:
        for view in self.all_views():
            if isinstance(view, QTableView):
                return cast(QTableView, view)
        return None

    def header_view(self) -> QHeaderView | None:
        for view in self.all_views():
            if isinstance(view, QHeaderView):
                return cast(QHeaderView, view)
        return None

    def column_view(self) -> QColumnView | None:
        for view in self.all_views():
            if isinstance(view, QColumnView):
                return cast(QColumnView, view)
        return None

    def tree_view(self) -> QTreeView | None:
        for view in self.all_views():
            if isinstance(view, QTreeView):
                return cast(QTreeView, view)
        return None

    def wheelEvent(self, event: QWheelEvent) -> None:
        if bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            delta: Literal[1, -1] = 1 if event.angleDelta().y() > 0 else -1
            self.adjust_view_size(delta)
            event.accept()
        else:
            super().wheelEvent(event)

    def adjust_view_size(
        self,
        delta: int,
    ) -> None:
        current_view: QAbstractItemView | None = self.current_view()
        if current_view is None:
            return
        cur_text_size: int = current_view.get_text_size() if isinstance(current_view, RobustAbstractItemView) else current_view.font().pointSize()
        new_text_size: int = cur_text_size + delta
        new_text_size = max(self.min_text_size, new_text_size)

        if delta > 0 and not self.is_size_suitable_for_view():
            self.switch_to_next_view()
        elif delta < 0 and new_text_size <= self.min_text_size:
            self.switch_to_previous_view()
        else:
            if isinstance(current_view, RobustAbstractItemView):
                current_view.set_text_size(new_text_size)
            else:
                current_view.setFont(QFont(current_view.font().family(), new_text_size))
            self.update_icon_size(new_text_size)

    def is_size_suitable_for_view(  # noqa: PLR0911
        self,
        max_item_percent: float = 0.1,
    ) -> bool:
        current_view: QAbstractItemView | None = self.current_view()
        if not current_view:
            return False
        viewport: QWidget | None = current_view.viewport()
        model: QAbstractItemModel | None = current_view.model()
        if not viewport or not model:
            return False

        viewport_size: QSize = viewport.size()
        item_size: QSize = current_view.visualRect(model.index(0, 0)).size()

        viewport_area: int = viewport_size.width() * viewport_size.height()
        item_area: int = item_size.width() * item_size.height()

        max_allowed_area: float = viewport_area * max_item_percent

        if isinstance(current_view, QListView):
            return item_size.width() < 200  # noqa: PLR2004
        if item_area > max_allowed_area:
            return False
        if item_size.width() == 0 or item_size.height() == 0:
            return False

        items_per_row: int = viewport_size.width() // item_size.width()
        items_per_column: int = viewport_size.height() // item_size.height()
        visible_items: int = items_per_row * items_per_column
        total_items: int = model.rowCount() * model.columnCount()

        if visible_items == 0:
            return False

        font_metrics: QFontMetrics = current_view.fontMetrics()
        item_text: str | None = model.data(model.index(0, 0))
        if isinstance(item_text, str) and font_metrics.horizontalAdvance(item_text) > item_size.width():
            return False

        return visible_items >= max_item_percent * total_items

    def update_icon_size(
        self,
        text_size: int,
    ) -> None:
        icon_size: QSize = QSize(int(text_size), int(text_size))
        for view in self.all_widgets():
            actual_view: QAbstractItemView | None = self.get_actual_view(view)
            if actual_view is None:
                continue
            actual_view.setIconSize(icon_size)

    def switch_to_next_view(self) -> None:
        if self.current_view_index >= len(self.all_widgets()) - 1:
            return
        self.current_view_index += 1
        current_view: QAbstractItemView = self.get_actual_view(self.all_widgets()[self.current_view_index])
        model: QAbstractItemModel | None = current_view.model() if current_view else None
        while self.current_view_index < len(self.all_widgets()) - 1 and isinstance(current_view, QTableView) and model is not None and model.columnCount() == 1:
            self.current_view_index += 1
            current_view = self.get_actual_view(self.all_widgets()[self.current_view_index])
            model = current_view.model() if current_view else None
        self.setCurrentWidget(self.all_widgets()[self.current_view_index])
        for view in self.all_views():
            if isinstance(view, RobustAbstractItemView):
                view.set_text_size(self.min_text_size)
            else:
                view.setFont(QFont(view.font().family(), self.min_text_size))
        self.update_icon_size(self.min_text_size)

    def switch_to_previous_view(self) -> None:
        if self.current_view_index > 0:
            self.current_view_index -= 1
            current_view: QAbstractItemView = self.all_views()[self.current_view_index]
            model: QAbstractItemModel | None = current_view.model() if current_view else None
            while self.current_view_index > 0 and isinstance(current_view, QTableView) and model is not None and model.columnCount() == 1:
                self.current_view_index -= 1
                current_view = self.all_views()[self.current_view_index]
                model = current_view.model() if current_view else None
            self.setCurrentWidget(self.all_widgets()[self.current_view_index])
            for view in self.all_views():
                if isinstance(view, RobustAbstractItemView):
                    view.set_text_size(64)
                else:
                    view.setFont(QFont(view.font().family(), 64))
            self.update_icon_size(64)

    def setCurrentWidget(
        self,
        widget: QWidget,
    ) -> None:
        super().setCurrentWidget(widget)
        if widget not in self.all_widgets():
            self.set_widgets((*self.all_widgets(), widget))
        self.current_view_index = self.all_widgets().index(widget)

    def setRootIndex(
        self,
        index: QModelIndex,
    ) -> None:
        for view in self.all_views():
            view.setRootIndex(index)

    def rootIndex(self) -> QModelIndex:
        current_view: QAbstractItemView | None = self.current_view()
        return QModelIndex() if current_view is None else current_view.rootIndex()

    def clearSelection(self) -> None:
        for view in self.all_views():
            view.clearSelection()

    def selectionModel(self) -> QItemSelectionModel:
        return self.common_selection_model

    def selectedIndexes(self) -> list[QModelIndex]:
        current_view: QAbstractItemView | None = self.current_view()
        return current_view.selectedIndexes() if current_view else []

    def selectAll(self) -> None:
        current_view: QAbstractItemView | None = self.current_view()
        if current_view is None:
            return
        current_view.selectAll()


if __name__ == "__main__":
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

    qapp: QApplication | None = cast(Optional[QApplication], QApplication.instance())
    assert qapp is not None
    q_app_style: QStyle | None = qapp.style()
    assert q_app_style is not None
    icons: list[QIcon] = [
        q_app_style.standardIcon(getattr(q_app_style.StandardPixmap, attr))
        for attr in dir(QStyle.StandardPixmap)
        if not attr.startswith("_")
        and attr
        not in (
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
