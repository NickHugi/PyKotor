from __future__ import annotations

from abc import abstractmethod
from contextlib import suppress
from typing import TYPE_CHECKING, Any, cast

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from qtpy.QtCore import QEvent, QObject, QSortFilterProxyModel, Qt
from qtpy.QtGui import QStandardItemModel
from qtpy.QtWidgets import QAbstractSpinBox, QApplication, QComboBox, QDoubleSpinBox, QGroupBox, QSlider, QSpinBox, QWidget

if TYPE_CHECKING:
    from qtpy.QtCore import QAbstractItemModel, QModelIndex
    from qtpy.QtCore import QModelIndex
    from qtpy.QtGui import QKeyEvent


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
        self.sort_states: dict[int, int] = {}

    def toggle_sort(
        self,
        column: int,
    ):
        if column not in self.sort_states:
            self.sort_states[column] = 0
        self.sort_states[column] = (self.sort_states[column] + 1) % 3

        if self.sort_states[column] == 0:
            self.reset_sort()
        elif self.sort_states[column] == 1:
            self.sort(column, Qt.SortOrder.AscendingOrder)
        elif self.sort_states[column] == 2:  # noqa: PLR2004
            self.sort(column, Qt.SortOrder.DescendingOrder)

    def reset_sort(self):
        self.sort(-1)  # Reset sorting
        self.invalidate()  # Force a refresh
        self.sort_states.clear()

    def get_sort_value(
        self,
        index: QModelIndex,
    ) -> Any:
        """Return the sort value based on the column."""
        src_model: QAbstractItemModel | None = self.sourceModel()
        assert isinstance(src_model, QStandardItemModel)
        return src_model.data(index)

    def lessThan(
        self,
        left: QModelIndex,
        right: QModelIndex,
    ) -> bool:
        left_data = self.get_sort_value(left)
        right_data = self.get_sort_value(right)

        with suppress(Exception):
            if type(left_data) is type(right_data) and hasattr(left_data, "__lt__"):
                return left_data < right_data
        return super().lessThan(left, right)


class NoScrollEventFilter(QObject):
    def eventFilter(
        self,
        obj: QObject,
        event: QEvent,
    ) -> bool:  # pyright: ignore[reportIncompatibleMethodOverride]
        event_type: QEvent.Type = event.type()
        if event_type != QEvent.Type.Wheel or not isinstance(obj, QWidget):
            return super().eventFilter(obj, event)

        parent_widget: QObject | None = obj.parent()
        self_parent: QObject | None = self.parent()
        while parent_widget is not None and (
            not isinstance(parent_widget, self_parent.__class__)
            or self_parent.__class__ == QObject
        ):
            parent_widget: QObject | None = parent_widget.parent()
        if parent_widget:
            QApplication.sendEvent(parent_widget, event)
        return True

    def setup_filter(
        self,
        include_types: list[type[QWidget]] | None = None,
        parent_widget: QObject | QWidget | None = None,
    ) -> None:
        """Recursively install event filters on all child widgets."""
        if include_types is None:
            include_types = [QComboBox, QSlider, QSpinBox, QGroupBox, QAbstractSpinBox, QDoubleSpinBox]

        parent_widget = self.parent() if parent_widget is None else parent_widget
        if parent_widget is None:
            RobustLogger().warning(
                "NoScrollEventFilter has nothing to do, please provide a widget to process (parent_widget was somehow None here)",
                stack_info=True,
            )
            return
        for widget in parent_widget.findChildren(QWidget):
            if not isinstance(widget, QWidget):
                continue
            if isinstance(widget, tuple(include_types)):
                #RobustLogger.debug(f"Installing event filter on: {widget.objectName()} (type: {widget.__class__.__name__})")
                widget.installEventFilter(self)
            #else:
            #    RobustLogger.debug(f"Skipping NoScrollEventFilter installation on '{widget.objectName()}' due to instance check {widget.__class__.__name__}.")
            self.setup_filter(include_types, widget)


class HoverEventFilter(QObject):
    def __init__(
        self,
        debug_key: Qt.Key | None = None,
    ):
        super().__init__()
        self.current_widget: QObject | None = None
        self.debug_key: Qt.Key = Qt.Key.Key_Pause if debug_key is None else debug_key

    def eventFilter(
        self,
        obj: QObject,
        event: QEvent,
    ) -> bool:  # pyright: ignore[reportIncompatibleMethodOverride]
        event_type: QEvent.Type = event.type()
        if event_type == QEvent.Type.HoverEnter:
            self.current_widget = obj
        elif event_type == QEvent.Type.HoverLeave:
            if self.current_widget == obj:
                self.current_widget = None
        elif event_type == QEvent.Type.KeyPress and cast(QKeyEvent, event).key() == self.debug_key:
            if self.current_widget:
                print(f"Hovered control: {self.current_widget.__class__.__name__} ({self.current_widget.objectName()})")
            else:
                print("No control is currently hovered.")
        return super().eventFilter(obj, event)

