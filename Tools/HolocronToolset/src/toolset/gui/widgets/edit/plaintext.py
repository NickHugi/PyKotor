from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy import QtCore
from qtpy.QtWidgets import QPlainTextEdit

if TYPE_CHECKING:
    from qtpy.QtGui import QKeyEvent, QMouseEvent

    from pykotor.common.language import LocalizedString


class HTPlainTextEdit(QPlainTextEdit):
    sig_key_released = QtCore.Signal()  # pyright: ignore[reportPrivateImportUsage]
    sig_double_clicked = QtCore.Signal()  # pyright: ignore[reportPrivateImportUsage]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.locstring: LocalizedString | None = None

    def keyReleaseEvent(self, e: QKeyEvent):
        super().keyReleaseEvent(e)
        self.sig_key_released.emit()

    def mouseDoubleClickEvent(self, e: QMouseEvent):
        super().mouseDoubleClickEvent(e)
        self.sig_double_clicked.emit()
