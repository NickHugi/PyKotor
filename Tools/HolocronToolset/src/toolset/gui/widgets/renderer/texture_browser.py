from __future__ import annotations

from qtpy.QtCore import Qt, Signal  # pyright: ignore[reportPrivateImportUsage]
from qtpy.QtGui import QPixmap
from qtpy.QtWidgets import QWidget


class TextureBrowser(QWidget):
    textureChanged: Signal = Signal(object)

    def __init__(
        self,
        parent: QWidget | None = None,
        flags: Qt.WindowFlags | Qt.WindowType = Qt.WindowType.Widget,
    ):
        """Initialize texture browser UI."""
        super().__init__(parent, flags)
        self.textures: list[QPixmap] = []  # List to store available textures

    def importTexture(self, texturePath: str):
        """Import and manage custom textures."""
        # Load texture from the given path and add to the list
        texture = QPixmap(texturePath)
        self.textures.append(texture)
        self.updateTextureDisplay()

    def updateTextureDisplay(self):
        """Update the UI to display all available textures."""
        # Logic to update the UI with the list of textures
        for texture in self.textures:
            # TODO: Add texture to the UI display (e.g., list or grid view)
            pass

    def setTexture(self, texture: QPixmap):
        """Set the texture to be displayed."""
        # TODO: Logic to set the selected texture in the UI
        self.textureChanged.emit(texture)
