from PyQt5 import QtCore
from PyQt5.QtGui import QKeyEvent, QMouseEvent
from PyQt5.QtWidgets import QPlainTextEdit


class HTPlainTextEdit(QPlainTextEdit):
    keyReleased = QtCore.pyqtSignal()
    doubleClicked = QtCore.pyqtSignal()

    def keyReleaseEvent(self, e: QKeyEvent) -> None:
        super().keyReleaseEvent(e)
        self.keyReleased.emit()

    def mouseDoubleClickEvent(self, e: QMouseEvent) -> None:
        super().mouseDoubleClickEvent(e)
        self.doubleClicked.emit()
