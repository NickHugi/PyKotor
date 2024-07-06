from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy import QtCore
from qtpy.QtWidgets import QPlainTextEdit

from pykotor.common.language import LocalizedString

if TYPE_CHECKING:
    from qtpy.QtGui import QKeyEvent, QMouseEvent


class HTPlainTextEdit(QPlainTextEdit):
    keyReleased = QtCore.Signal()
    doubleClicked = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.locstring: LocalizedString | None = None

    def keyReleaseEvent(self, e: QKeyEvent):
        super().keyReleaseEvent(e)
        self.keyReleased.emit()

    def mouseDoubleClickEvent(self, e: QMouseEvent):
        super().mouseDoubleClickEvent(e)
        self.doubleClicked.emit()
