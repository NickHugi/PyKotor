from __future__ import annotations

import os

from typing import TYPE_CHECKING

from qtpy.QtCore import QSize, Qt, Signal  # pyright: ignore[reportPrivateImportUsage]
from qtpy.QtGui import QIcon, QPixmap
from qtpy.QtWidgets import QFileDialog, QGridLayout, QListWidget, QListWidgetItem, QPushButton, QScrollArea, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from os import PathLike

    from qtpy.QtCore import QMimeData
    from qtpy.QtGui import QDragEnterEvent, QDropEvent


class TextureBrowser(QWidget):
    sig_texture_changed = Signal(str)  # Emits texture name when changed
    sig_texture_selected = Signal(str)  # Emits texture name when selected

    def __init__(
        self,
        parent: QWidget | None = None,
        flags: Qt.WindowType = Qt.WindowType.Widget,
    ):
        """Initialize texture browser UI."""
        super().__init__(parent, flags)
        self.textures: dict[str, QPixmap] = {}  # Map texture names to pixmaps
        self.selected_texture: str | None = None
        self.initUI()

    def initUI(self):
        """Set up the texture browser UI."""
        layout = QVBoxLayout(self)

        # Add import button
        from toolset.gui.common.localization import translate as tr
        import_button = QPushButton(tr("Import Texture"), self)
        import_button.clicked.connect(self.import_texture_dialog)
        layout.addWidget(import_button)

        # Create scroll area for textures
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        # Create widget to hold texture grid
        self.texture_widget = QWidget()
        self.texture_layout = QGridLayout(self.texture_widget)
        scroll.setWidget(self.texture_widget)

        # Create list widget for textures
        self.texture_list: QListWidget = QListWidget(self)
        self.texture_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.texture_list.setIconSize(QSize(64, 64))
        self.texture_list.setSpacing(5)
        self.texture_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.texture_list.itemClicked.connect(self.on_texture_selected)
        layout.addWidget(self.texture_list)

        # Enable drag and drop
        self.setAcceptDrops(True)

    def import_texture_dialog(self):
        """Open file dialog to import textures."""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            tr("Import Textures"),
            "",
            "Image Files (*.tga *.dds *.jpg *.png *.bmp)",
        )
        for path in file_paths:
            self.import_texture(str(path))

    def import_texture(self, texture_path: str | PathLike[str]) -> str | None:
        """Import and manage custom textures."""
        texture_path = str(texture_path)
        texture_name = os.path.basename(texture_path)  # noqa: PTH119
        texture = QPixmap(texture_path)

        if not texture.isNull():
            self.textures[texture_name] = texture
            self.update_texture_display()
            return texture_name
        return None

    def update_texture_display(self):
        """Update the UI to display all available textures."""
        self.texture_list.clear()

        for name, pixmap in self.textures.items():
            # Create scaled icon
            scaled = pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon = QIcon(scaled)

            # Create list item
            item = QListWidgetItem(icon, name)
            item.setToolTip(name)
            self.texture_list.addItem(item)

    def on_texture_selected(self, item: QListWidgetItem):
        """Handle texture selection."""
        self.selected_texture = item.text()
        self.sig_texture_selected.emit(self.selected_texture)
        self.sig_texture_changed.emit(self.selected_texture)

    def get_textures(self) -> list[str]:
        """Get list of all texture names."""
        return list(self.textures.keys())

    def highlight_texture(self, texture_name: str):
        """Highlight a specific texture in the browser."""
        for i in range(self.texture_list.count()):
            item = self.texture_list.item(i)
            if item.text() == texture_name:
                item.setSelected(True)
                self.texture_list.scrollToItem(item)
                break

    def get_texture(self, name: str) -> QPixmap | None:
        """Get texture pixmap by name."""
        return self.textures.get(name)

    def get_selected_texture(self) -> str | None:
        """Get currently selected texture name."""
        return self.selected_texture

    def get_textures(self) -> list[str]:
        """Get list of all texture names."""
        return list(self.textures.keys())

    def clear_textures(self):
        """Clear all textures."""
        self.textures.clear()
        self.texture_list.clear()
        self.selected_texture = None

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events for texture import."""
        mime_data: QMimeData | None = event.mimeData()
        if mime_data is not None and mime_data.hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """Handle drop events for texture import."""
        mime_data: QMimeData | None = event.mimeData()
        if mime_data is None:
            return
        for url in mime_data.urls():
            if url.isLocalFile():
                file_path = url.toLocalFile()
                if isinstance(file_path, str) and file_path.lower().endswith((".tga", ".dds", ".jpg", ".png", ".bmp")):
                    self.import_texture(file_path)
        event.acceptProposedAction()

    def add_texture(self, name: str, pixmap: QPixmap):
        """Add a texture programmatically."""
        if not isinstance(name, str):
            return
        if not isinstance(pixmap, QPixmap):
            return
        self.textures[name] = pixmap
        self.update_texture_display()

    def remove_texture(self, name: str):
        """Remove a texture by name."""
        if not isinstance(name, str):
            return
        if name not in self.textures:
            return
        del self.textures[name]
        self.update_texture_display()
        if self.selected_texture == name:
            self.selected_texture = None
