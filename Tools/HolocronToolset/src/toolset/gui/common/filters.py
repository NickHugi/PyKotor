from __future__ import annotations

import uuid

from abc import abstractmethod
from contextlib import suppress
from typing import TYPE_CHECKING, Any, cast

from qtpy.QtCore import QEvent, QObject, QSortFilterProxyModel, Qt
from qtpy.QtGui import QKeyEvent, QStandardItemModel
from qtpy.QtWidgets import QAbstractSpinBox, QApplication, QComboBox, QDoubleSpinBox, QGroupBox, QSlider, QSpinBox, QWidget

if TYPE_CHECKING:
    from qtpy.QtCore import QModelIndex


class TemplateFilterProxyModel(QSortFilterProxyModel):
    @abstractmethod
    def get_sort_value(self, index: QModelIndex) -> Any:
        ...


class RobustSortFilterProxyModel(TemplateFilterProxyModel):
    def __init__(
        self,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self.setDynamicSortFilter(True)
        self._sort_states: dict[int, int] = {}

    def toggle_sort(self, column: int):
        if column not in self._sort_states:
            self._sort_states[column] = 0
        self._sort_states[column] = (self._sort_states[column] + 1) % 3

        if self._sort_states[column] == 0:
            self.reset_sort()
        elif self._sort_states[column] == 1:
            self.sort(column, Qt.AscendingOrder)
        elif self._sort_states[column] == 2:
            self.sort(column, Qt.DescendingOrder)

    def reset_sort(self):
        self.sort(-1)  # Reset sorting
        self.invalidate()  # Force a refresh
        self._sort_states = {}

    def get_sort_value(self, index: QModelIndex) -> Any:
        """Return the sort value based on the column."""
        srcModel = self.sourceModel()
        assert isinstance(srcModel, QStandardItemModel)
        return self.sourceModel().data(index)

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        left_data = self.get_sort_value(left)
        right_data = self.get_sort_value(right)

        with suppress(Exception):
            if type(left_data) is type(right_data) and hasattr(left_data, "__lt__"):
                return left_data < right_data
        return super().lessThan(left, right)


class NoScrollEventFilter(QObject):
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Wheel and isinstance(obj, QWidget):
            parent_widget = obj.parent()
            self_parent = self.parent()
            while parent_widget is not None and (
                not isinstance(parent_widget, self_parent.__class__)
                or self_parent.__class__ == QObject
            ):
                parent_widget = parent_widget.parent()
            if parent_widget:
                QApplication.sendEvent(parent_widget, event)
            return True
        return super().eventFilter(obj, event)

    def setup_filter(
        self,
        include_types: list[type[QWidget]] | None = None,
        parent_widget: QObject | QWidget | None = None,
    ) -> None:
        """Recursively install event filters on all child widgets."""
        if include_types is None:
            include_types = [QComboBox, QSlider, QSpinBox, QGroupBox, QAbstractSpinBox, QDoubleSpinBox]

        parent_widget = self.parent() if parent_widget is None else parent_widget
        for widget in parent_widget.findChildren(QWidget):
            if not widget.objectName():
                widget.setObjectName(widget.__class__.__name__ + uuid.uuid4().hex[6:])
            if isinstance(widget, tuple(include_types)):
                #RobustRootLogger.debug(f"Installing event filter on: {widget.objectName()} (type: {widget.__class__.__name__})")
                widget.installEventFilter(self)
            #else:
            #    RobustRootLogger.debug(f"Skipping NoScrollEventFilter installation on '{widget.objectName()}' due to instance check {widget.__class__.__name__}.")
            self.setup_filter(include_types, widget)


class HoverEventFilter(QObject):
    def __init__(self, debugKey: Qt.Key | None = None):
        super().__init__()
        self.current_widget: QObject | None = None
        self.debugKey: Qt.Key = Qt.Key_Pause if debugKey is None else debugKey

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.HoverEnter:
            self.current_widget = obj
        elif event.type() == QEvent.Type.HoverLeave:
            if self.current_widget == obj:
                self.current_widget = None
        elif event.type() == QEvent.Type.KeyPress and cast(QKeyEvent, event).key() == self.debugKey:
            if self.current_widget:
                print(f"Hovered control: {self.current_widget.__class__.__name__} ({self.current_widget.objectName()})")
            else:
                print("No control is currently hovered.")
        return super().eventFilter(obj, event)

