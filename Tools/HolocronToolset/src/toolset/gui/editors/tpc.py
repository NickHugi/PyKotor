from __future__ import annotations

import io

from typing import TYPE_CHECKING

from PIL import Image, ImageOps
from qtpy.QtCore import Qt
from qtpy.QtGui import QImage, QPixmap
from qtpy.QtWidgets import QFileDialog
from typing_extensions import Literal

from pykotor.resource.formats.tpc import TPC, TPCTextureFormat, read_tpc, write_tpc
from pykotor.resource.formats.tpc.io_tga import _DataTypes
from pykotor.resource.type import ResourceType
from pykotor.tools.path import CaseAwarePath
from toolset.gui.editor import Editor

if TYPE_CHECKING:
    import os

    from qtpy.QtCore import QSize
    from qtpy.QtWidgets import QWidget
    from qtpy.sip import voidptr

    from pykotor.extract.installation import Installation


class TPCEditor(Editor):
    def __init__(
        self,
        parent: QWidget | None,
        installation: Installation | None = None,
    ):
        """Initializes the texture viewer window.

        Args:
        ----
            parent: {QWidget}: The parent widget of this window
            installation: {Installation}: The installation context
        Returns:
            None: Does not return anything
        Processing Logic:
        ----------------
            - Initializes the base class with supported resource types
            - Loads the UI from the designer file
            - Sets up menus and connects signals
            - Creates a default 256x256 RGBA texture
            - Calls new() to display the default texture.
        """
        supported: list[ResourceType] = [ResourceType.TPC, ResourceType.TGA, ResourceType.JPG, ResourceType.PNG, ResourceType.BMP]
        super().__init__(parent, "Texture Viewer", "none", supported, supported, installation)  # type: ignore[arg-type]

        from toolset.uic.qtpy.editors.tpc import Ui_MainWindow
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.zoom_factor: float = 1.0
        self._setup_signals()
        self._setup_ui()
        self._setup_menus()
        self._setup_signals()

        self._tpc: TPC = TPC()
        self._tpc.set_single(256, 256, bytes(0 for _ in range(256 * 256 * 4)), TPCTextureFormat.RGBA)

        self.new()

    def _setup_ui(self):

        self.ui.formatComboBox.addItems(
            [
                format.name
                for format in TPCTextureFormat
            ]
        )

    def _setup_signals(self):
        self.ui.zoomInButton.clicked.connect(self.zoom_in)
        self.ui.zoomOutButton.clicked.connect(self.zoom_out)
        self.ui.resetZoomButton.clicked.connect(self.reset_zoom)
        self.ui.rotateLeftButton.clicked.connect(self.rotate_left)

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes,
    ):
        super().load(filepath, resref, restype, data)

        orig_format: TPCTextureFormat | None = None
        if restype in {ResourceType.TPC, ResourceType.TGA}:
            txi_filepath: CaseAwarePath | None = CaseAwarePath(filepath).with_suffix(".txi")
            self._tpc = read_tpc(data, txi_source=txi_filepath)
            orig_format = self._tpc.format()
            if restype is ResourceType.TPC:
                if self._tpc.format() is TPCTextureFormat.DXT1:
                    tpc_format = TPCTextureFormat.RGB
                    width, height, img_bytes = self._tpc.convert(tpc_format)
                elif self._tpc.format() is TPCTextureFormat.DXT5:
                    tpc_format = TPCTextureFormat.RGBA
                    width, height, img_bytes = self._tpc.convert(tpc_format)
                else:
                    width, height, tpc_format, img_bytes = self._tpc.get()
            else:
                width, height, tpc_format, img_bytes = self._tpc.get()
        else:
            pillow: Image.Image = Image.open(io.BytesIO(data))
            pillow = pillow.convert("RGBA")
            pillow = ImageOps.flip(pillow)
            self._tpc = TPC()
            self._tpc.set_single(pillow.width, pillow.height, pillow.tobytes(), TPCTextureFormat.RGBA)
            width, height, img_bytes = self._tpc.convert(TPCTextureFormat.RGB)

        image = QImage(bytes(img_bytes), width, height, QImage.Format.Format_RGB888)
        image: QImage = image.mirrored(False, True)  # flip vertically.

        # Calculate new dimensions maintaining aspect ratio
        max_width, max_height = 640, 480
        aspect_ratio: float = width / height
        if width / height > max_width / max_height:
            new_width = max_width
            new_height = int(new_width / aspect_ratio)
        else:
            new_height = max_height
            new_width = int(new_height * aspect_ratio)

        scaled_image: QImage = image.scaled(
            new_width,
            new_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.ui.textureImage.setPixmap(QPixmap.fromImage(scaled_image))
        self.ui.textureImage.setScaledContents(True)
        self.ui.txiEdit.setPlainText(self._tpc.txi)
        if self._tpc.original_datatype_code != _DataTypes.NO_IMAGE_DATA and orig_format is not None:
            self.setToolTip(f"{self._tpc.original_datatype_code.name} - {orig_format.name}")
        elif orig_format is not None:
            self.setToolTip(orig_format.name)
        self.center_and_adjust_window()

    def new(self):
        """Set texture image from TPC texture.

        Args:
        ----
            self: The class instance

        Processing Logic:
        ----------------
            1. Call super().new() to initialize parent class
            2. Create TPC object and set single texture
            3. Convert TPC texture to RGBA format
            4. Create QImage from RGBA data
            5. Create QPixmap from QImage
            6. Set pixmap to texture image label
            7. Clear texture index edit field.
        """
        super().new()

        self._tpc: TPC = TPC()
        self._tpc.set_single(256, 256, bytes(0 for _ in range(256 * 256 * 4)), TPCTextureFormat.RGBA)
        width, height, rgba = self._tpc.convert(TPCTextureFormat.RGBA, 0)

        image = QImage(bytes(rgba), width, height, QImage.Format.Format_RGBA8888)
        pixmap: QPixmap = QPixmap.fromImage(image)
        self.ui.textureImage.setPixmap(pixmap)  # type: ignore[arg-type]
        self.ui.textureImage.setScaledContents(True)
        self.ui.txiEdit.setPlainText("")

    def build(self) -> tuple[bytes, bytes]:
        self._tpc.txi = self.ui.txiEdit.toPlainText()

        data: bytes | bytearray = bytearray()

        if self._restype in {ResourceType.TPC, ResourceType.TGA}:
            width, height, img_bytes = self._tpc.convert(TPCTextureFormat.RGB, 0, y_flip=True)
            self._tpc.set_data([img_bytes], TPCTextureFormat.RGB, width, height)
            write_tpc(self._tpc, data, self._restype)
            return bytes(data), b""

        if self._restype in {ResourceType.PNG, ResourceType.BMP}:
            data = self.extract_png_bmp_bytes()
        elif self._restype is ResourceType.JPG:
            data = self.extract_tpc_jpeg_bytes()
        return bytes(data), b""

    def zoom_in(self):
        self.zoom_factor *= 1.2
        self.update_image()

    def zoom_out(self):
        self.zoom_factor /= 1.2
        self.update_image()

    def reset_zoom(self):
        self.zoom_factor = 1.0
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

    def convert_format(self):
        new_format = TPCTextureFormat[self.ui.formatComboBox.currentText()]
        width, height, img_bytes = self._tpc.convert(new_format, 0)
        self._tpc.set_data([img_bytes], new_format, width, height)
        self.update_image()

    def export_image(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Image", "", "PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp)")
        if file_path:
            width, height, img_bytes = self._tpc.convert(TPCTextureFormat.RGBA, 0)
            image = Image.frombytes("RGBA", (width, height), img_bytes)
            image.save(file_path)

    def update_image(self):
        width, height, img_bytes = self._tpc.convert(TPCTextureFormat.RGB, 0)
        image = QImage(width, height, QImage.Format.Format_RGB888)
        image.loadFromData(img_bytes)
        pixmap: QPixmap = QPixmap.fromImage(image)
        scaled_size: QSize = pixmap.size() * self.zoom_factor
        self.ui.textureImage.setPixmap(pixmap.scaled(scaled_size, Qt.AspectRatioMode.KeepAspectRatio))
        self.ui.textureImage.setFixedSize(scaled_size)

    def qimage_to_pillow_image(self, qimage: QImage) -> Image.Image:
        # Convert QImage to bytes
        qimage = qimage.convertToFormat(
            QImage.Format.Format_RGBA8888,
            Qt.ImageConversionFlag.AutoColor,
        )
        width, height = qimage.width(), qimage.height()
        qimg_data: voidptr | None = qimage.constBits()
        assert qimg_data is not None, f"qimg_data is None in {self.__class__.__name__}.qimage_to_pillow_image()"
        return Image.frombuffer("RGBA", (width, height), io.BytesIO(bytes(qimg_data.asarray())), "raw", "RGBA", 0, 1)

    def extract_tpc_jpeg_bytes(self) -> bytes:
        width, height, pixeldata = self._tpc.convert(TPCTextureFormat.RGB)
        image: Image.Image = Image.frombuffer("RGB", (width, height), bytes(pixeldata))
        yflipped_img: Image.Image = ImageOps.flip(image)

        dataIO = io.BytesIO()
        yflipped_img.save(dataIO, "JPEG", quality=80)
        return dataIO.getvalue()

    def extract_png_bmp_bytes(self) -> bytes:
        pixmap: QPixmap = self.ui.textureImage.pixmap()
        if pixmap is None:
            raise ValueError("No image available in QLabel")
        qimage: QImage = pixmap.toImage()
        pil_image: Image.Image = self.qimage_to_pillow_image(qimage)  # type: ignore[arg-type]
        dataIO = io.BytesIO()
        image_format: Literal["PNG", "BMP"] = "PNG" if self._restype is ResourceType.PNG else "BMP"
        pil_image.save(dataIO, format=image_format)
        return dataIO.getvalue()
