from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import (
    Qt,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import QImage, QPixmap
from qtpy.QtWidgets import QLabel, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from qtpy.QtGui import QIcon


class PreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout(self))
        self.preview_label: QLabel = QLabel(self)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(self.preview_label)

    def set_icon(self, icon: QIcon):
        pixmap = icon.pixmap(128, 128)
        self.preview_label.setPixmap(pixmap)

    def set_image(self, data: bytes, width: int, height: int):
        image = QImage(data, width, height, QImage.Format.Format_RGBA8888)
        pixmap = QPixmap.fromImage(image)
        scaled_pixmap = pixmap.scaled(256, 256, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.preview_label.setPixmap(scaled_pixmap)
