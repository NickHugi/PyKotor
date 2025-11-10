from __future__ import annotations

import warnings

from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image
from qtpy.QtCore import Qt  # type: ignore[attr-defined]
from qtpy.QtGui import QIcon, QImage, QImageReader, QPixmap
from qtpy.QtWidgets import (
    QAction,  # pyright: ignore[reportPrivateImportUsage]
    QFileDialog,
    QHBoxLayout,
    QMenu,
    QPushButton,
    QStyle,
    QToolButton,
    QVBoxLayout,
)

from pykotor.resource.formats.tpc import TPC, TPCTextureFormat, read_tpc, write_tpc
from pykotor.resource.type import ResourceType
from toolset.gui.editor import Editor

if TYPE_CHECKING:
    import os

    from qtpy.QtWidgets import QLayoutItem, QWidget

    from pykotor.extract.installation import Installation
    from pykotor.resource.formats.tpc.tpc_data import TPCMipmap


class TPCEditor(Editor):
    def __init__(
        self,
        parent: QWidget | None,
        installation: Installation | None = None,
    ):
        supported: list[ResourceType] = [ResourceType.TPC, ResourceType.TGA, ResourceType.JPG, ResourceType.PNG, ResourceType.BMP]
        super().__init__(parent, "Texture Viewer", "none", supported, supported, installation)  # type: ignore[arg-type]

        self._tpc: TPC = TPC.from_blank()
        self.current_frame: int = 0
        self.zoom_factor: float = 1.0

        from toolset.uic.qtpy.editors.tpc import Ui_MainWindow

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setup_signals()
        self._setup_menus()
        self._setup_toolbar()

        self.new()

    def _setup_toolbar(self):
        self.convert_format_button = QToolButton(self.ui.toolBar)
        self.convert_format_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.convert_format_button.setText("Convert Format")
        self.convert_format_button.setToolTip("Convert TPC Texture Format")
        self.convert_format_menu = QMenu(self)
        self.convert_format_button.setMenu(self.convert_format_menu)

        for format_name, format_value in TPCTextureFormat.__members__.items():
            action = QAction(format_name, self)
            action.setData(format_value)
            self.convert_format_menu.addAction(action)

        style: QStyle | None = self.style()
        if style is not None:
            self.convert_format_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_ArrowDown))
            self.ui.actionResetZoom.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
            self.ui.actionRotateLeft.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_ArrowLeft))
            self.ui.actionRotateRight.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_ArrowRight))
            self.ui.actionFlipHorizontal.setIcon(QIcon.fromTheme("object-flip-horizontal"))
            self.ui.actionFlipVertical.setIcon(QIcon.fromTheme("object-flip-vertical"))
            self.ui.actionExport.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
            self.ui.actionToggleTXIEditor.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
        self.convert_format_menu.triggered.connect(self.on_convert_format_selected)
        self.ui.toolBar.addWidget(self.convert_format_button)

    def _setup_signals(self):
        self.ui.actionResetZoom.triggered.connect(self.reset_zoom)
        self.ui.actionRotateLeft.triggered.connect(self.rotate_left)
        self.ui.actionRotateRight.triggered.connect(self.rotate_right)
        self.ui.zoomSlider.valueChanged.connect(self.on_zoom_slider_changed)
        self.ui.actionFlipHorizontal.triggered.connect(self.flip_horizontal)
        self.ui.actionFlipVertical.triggered.connect(self.flip_vertical)
        self.setup_navigation_buttons()

    def on_convert_format_selected(self, action):
        selected_format = action.data()
        self._tpc.convert(selected_format)
        self.update_image()

    def setup_navigation_buttons(self):
        layout = self.ui.scrollAreaWidgetContents.layout()
        assert isinstance(layout, (QVBoxLayout, QHBoxLayout))
        if self._tpc.is_animated or self._tpc.is_cube_map:
            hbox = QHBoxLayout()
            prev_button = QPushButton("Previous")
            next_button = QPushButton("Next")
            prev_button.clicked.connect(lambda: self.navigate_frames(-1))
            next_button.clicked.connect(lambda: self.navigate_frames(1))
            hbox.addWidget(prev_button)
            hbox.addWidget(next_button)
            layout.addLayout(hbox)
        else:
            for i in range(layout.count()):
                item: QLayoutItem | None = layout.itemAt(i)
                if isinstance(item, QHBoxLayout):
                    layout.removeItem(item)
                    break

    def new(self):
        super().new()

        self._tpc = TPC.from_blank()
        self.update_image()

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes,
    ):
        super().load(filepath, resref, restype, data)
        self._tpc = TPC()
        if restype in {ResourceType.TPC, ResourceType.TGA}:
            self._tpc = read_tpc(data, txi_source=Path(filepath).with_suffix(".txi"))
        else:
            supported_formats: list[str] = [x.data().decode().strip().lstrip(".") for x in QImageReader.supportedImageFormats()]  # pyright: ignore[reportGeneralTypeIssues]
            if restype.extension.lstrip(".") not in supported_formats:
                warnings.warn(f"Unsupported image format: {restype.extension!r}", stacklevel=1)
            image: QImage = QImage.fromData(data)
            if image.isNull():
                raise ValueError(f"Failed to load image data for resource of type {restype!r}")
            self._tpc.convert(TPCTextureFormat.from_qimage_format(image.format()))
        self.current_frame = 0
        self.update_image()

    def build(self) -> tuple[bytes, bytes]:
        self._tpc.txi = self.ui.txiEdit.toPlainText()

        data: bytes | bytearray = bytearray()

        if self._restype in {ResourceType.TPC, ResourceType.TGA}:
            write_tpc(self._tpc, data, self._restype)
            return bytes(self._tpc.layers[0].mipmaps[0].data), b""
        return bytes(data), b""

    def on_zoom_slider_changed(self, value):
        self.zoom_factor = value / 100
        self.update_image()

    def reset_zoom(self):
        self.ui.zoomSlider.setValue(100)
        self.update_image()

    def rotate_left(self):
        self._tpc.rotate90(-1)
        self.update_image()

    def rotate_right(self):
        self._tpc.rotate90(1)
        self.update_image()

    def flip_horizontal(self):
        self._tpc.flip_horizontally()
        self.update_image()

    def flip_vertical(self):
        self._tpc.flip_vertically()
        self.update_image()

    def export_image(self):
        file_path: str = ""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Image",
            "",
            "PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp);;TGA (*.tga)",
        )  # pyright: ignore[reportGeneralTypeIssues]
        if not file_path or not file_path.strip():
            print("User cancelled exporting the image to a path.")
            return
        layer_index = 0
        if self._tpc.is_animated or self._tpc.is_cube_map:
            layer_index = max(0, min(self.current_frame, len(self._tpc.layers) - 1))
        mm: TPCMipmap = self._tpc.layers[layer_index].mipmaps[0].copy()
        export_format = mm.tpc_format
        if export_format == TPCTextureFormat.DXT1:
            mm.convert(TPCTextureFormat.RGB)
        elif export_format in (TPCTextureFormat.DXT3, TPCTextureFormat.DXT5, TPCTextureFormat.BGRA):
            mm.convert(TPCTextureFormat.RGBA)
        elif export_format == TPCTextureFormat.BGR:
            mm.convert(TPCTextureFormat.RGB)
        elif export_format == TPCTextureFormat.Greyscale:
            mm.convert(TPCTextureFormat.RGBA)
        image = Image.frombytes(mm.tpc_format.to_pil_mode(), (mm.width, mm.height), bytes(mm.data))
        image.save(file_path)

    def update_image(self):
        if not self._tpc.layers or not self._tpc.layers[0].mipmaps:
            return

        layer_index: int = 0
        if self._tpc.is_animated or self._tpc.is_cube_map:
            layer_index = max(0, min(self.current_frame, len(self._tpc.layers) - 1))

        mm: TPCMipmap = self._tpc.layers[layer_index].mipmaps[0].copy()
        display_format = mm.tpc_format
        if display_format == TPCTextureFormat.DXT1:
            mm.convert(TPCTextureFormat.RGB)
        elif display_format in (TPCTextureFormat.DXT3, TPCTextureFormat.DXT5, TPCTextureFormat.BGRA):
            mm.convert(TPCTextureFormat.RGBA)
        elif display_format == TPCTextureFormat.BGR:
            mm.convert(TPCTextureFormat.RGB)
        elif display_format == TPCTextureFormat.Greyscale:
            mm.convert(TPCTextureFormat.RGBA)
        target_format = mm.tpc_format

        image: QImage = QImage(
            bytes(mm.data),
            mm.width,
            mm.height,
            target_format.to_qimage_format(),
        )
        image = image.mirrored(False, True)  # flip vertically.

        # Calculate new dimensions maintaining aspect ratio
        max_width, max_height = 640, 480
        aspect_ratio: float = mm.width / mm.height if mm.height else 1.0
        if mm.height and mm.width / mm.height > max_width / max_height:
            new_width = max_width
            new_height = int(new_width / aspect_ratio)
        else:
            new_height = max_height
            new_width = int(new_height * aspect_ratio)

        image = image.scaled(
            int(new_width * self.zoom_factor),
            int(new_height * self.zoom_factor),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        pixmap: QPixmap = QPixmap.fromImage(image)
        self.ui.textureImage.setPixmap(pixmap)
        self.ui.textureImage.setScaledContents(True)
        self.ui.txiEdit.setPlainText(self._tpc.txi)
        self.setup_navigation_buttons()
        self.center_and_adjust_window()

    def navigate_frames(self, direction: int):
        num_frames: int = len(self._tpc.layers)
        if num_frames > 0:
            self.current_frame = max(0, min(self.current_frame + direction, num_frames - 1))
            self.update_image()
