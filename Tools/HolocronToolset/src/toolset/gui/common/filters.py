from __future__ import annotations

from typing import cast

from qtpy.QtCore import QEvent, QObject, Qt
from qtpy.QtGui import QKeyEvent
from qtpy.QtWidgets import QAbstractSpinBox, QApplication, QComboBox, QDoubleSpinBox, QGroupBox, QSlider, QSpinBox, QWidget


class NoScrollEventFilter(QObject):
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Wheel and isinstance(obj, QWidget):
            parent_widget = obj.parent()
            while parent_widget and (not isinstance(parent_widget, self.parent().__class__) or self.parent().__class__ == QObject):
                parent_widget = parent_widget.parent()
            if parent_widget:
                QApplication.sendEvent(parent_widget, event)
            return True
        return super().eventFilter(obj, event)

    @classmethod
    def installEventFilters(
        cls,
        parent_widget: QWidget,
        event_filter: QObject,
        include_types: list[type[QWidget]] | None = None
    ) -> None:
        """Recursively install event filters on all child widgets."""
        if include_types is None:
            include_types = [QComboBox, QSlider, QSpinBox, QGroupBox, QAbstractSpinBox, QDoubleSpinBox]

        for widget in parent_widget.findChildren(QWidget):
            if not widget.objectName():
                widget.setObjectName(widget.__class__.__name__)
            if isinstance(widget, tuple(include_types)):
                #RobustRootLogger.debug(f"Installing event filter on: {widget.objectName()} (type: {widget.__class__.__name__})")
                widget.installEventFilter(event_filter)
            #else:
            #    RobustRootLogger.debug(f"Skipping NoScrollEventFilter installation on '{widget.objectName()}' due to instance check {widget.__class__.__name__}.")
            cls.installEventFilters(widget, event_filter, include_types)


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
