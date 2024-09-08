from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import Signal
from qtpy.QtWidgets import QWidget

if TYPE_CHECKING:
    from qtpy.QtGui import QPixmap


class TextureBrowser(QWidget):
    textureChanged: Signal = Signal(object)

    def __init__(self):
        """Initialize texture browser UI."""
        super().__init__()

    def importTexture(self, texturePath: str):
        """Import and manage custom textures."""

    def setTexture(self, texture: QPixmap):
        """Set the texture to be displayed."""
        self.textureChanged.emit(texture)