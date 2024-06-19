from __future__ import annotations

from typing import cast

from qtpy.QtCore import QEvent, QObject, Qt
from qtpy.QtGui import QKeyEvent
from qtpy.QtWidgets import QApplication, QWidget


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
