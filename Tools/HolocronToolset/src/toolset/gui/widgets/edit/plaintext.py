from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5 import QtCore
from PyQt5.QtWidgets import QPlainTextEdit

if TYPE_CHECKING:
    from PyQt5.QtGui import QKeyEvent, QMouseEvent


class HTPlainTextEdit(QPlainTextEdit):
    keyReleased = QtCore.pyqtSignal()
    doubleClicked = QtCore.pyqtSignal()

    def keyReleaseEvent(self, e: QKeyEvent):
        super().keyReleaseEvent(e)
        self.keyReleased.emit()

    def mouseDoubleClickEvent(self, e: QMouseEvent):
        super().mouseDoubleClickEvent(e)
        self.doubleClicked.emit()
