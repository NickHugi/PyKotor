from __future__ import annotations

import io

from typing import TYPE_CHECKING

import qtpy

from PIL import Image, ImageOps
from qtpy.QtCore import Qt
from qtpy.QtGui import QImage, QPixmap

from pykotor.resource.formats.tpc import TPC, TPCTextureFormat, read_tpc, write_tpc
from pykotor.resource.formats.tpc.io_tga import _DataTypes
from pykotor.resource.type import ResourceType
from pykotor.tools.path import CaseAwarePath
from toolset.gui.editor import Editor

if TYPE_CHECKING:
    import os

    from qtpy.QtWidgets import QWidget

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
        super().__init__(parent, "Texture Viewer", "none", supported, supported, installation)

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.editors.tpc import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.editors.tpc import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.editors.tpc import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.editors.tpc import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()

        self._tpc: TPC = TPC()
        self._tpc.set_single(256, 256, bytes(0 for _ in range(256 * 256 * 4)), TPCTextureFormat.RGBA)

        self.new()

    def _setupSignals(self): ...

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes,
    ):
        """Load a resource into the editor.

        Args:
        ----
            filepath: The path to the resource file
            resref: The resource reference
            restype: The resource type
            data: The raw resource data

        Load resource:
        -------------
            - Read TPC data directly if type is TPC or TGA
            - Otherwise open as PIL Image, convert to RGBA, flip vertically
            - Extract TPC data from PIL image
            - Convert TPC to RGB format
            - Create QImage from RGB data
            - Create QPixmap from QImage with y-axis flip
            - Set pixmap on texture image label
            - Set TXI data on editor.
        """
        super().load(filepath, resref, restype, data)

        # Read image, convert to RGB, and y_flip.
        orig_format = None
        if restype in {ResourceType.TPC, ResourceType.TGA}:
            txi_filepath: CaseAwarePath | None = CaseAwarePath.pathify(filepath).with_suffix(".txi")
            self._tpc = read_tpc(data, txi_source=txi_filepath)
            orig_format = self._tpc.format()
            width, height, img_bytes = self._tpc.convert(TPCTextureFormat.RGB, 0, y_flip=True)
            self._tpc.set_data(width, height, [img_bytes], TPCTextureFormat.RGB)
        else:
            pillow: Image.Image = Image.open(io.BytesIO(data))
            pillow = pillow.convert("RGBA")
            pillow = ImageOps.flip(pillow)
            self._tpc = TPC()
            self._tpc.set_single(pillow.width, pillow.height, pillow.tobytes(), TPCTextureFormat.RGBA)
            width, height, img_bytes = self._tpc.convert(TPCTextureFormat.RGB, 0)

        # Calculate new dimensions maintaining aspect ratio
        max_width, max_height = 640, 480
        aspect_ratio = width / height
        if width / height > max_width / max_height:
            new_width = max_width
            new_height = int(new_width / aspect_ratio)
        else:
            new_height = max_height
            new_width = int(new_height * aspect_ratio)

        # Create QImage and scale it
        image = QImage(img_bytes, width, height, QImage.Format_RGB888)
        image = image.mirrored(False, True)  # False for no horizontal flip, True for vertical flip
        scaled_image = image.scaled(new_width, new_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        # Create QPixmap from the scaled QImage
        pixmap: QPixmap = QPixmap.fromImage(scaled_image)

        self.ui.textureImage.setPixmap(pixmap)
        self.ui.textureImage.setScaledContents(True)
        self.ui.txiEdit.setPlainText(self._tpc.txi)
        if self._tpc.original_datatype_code != _DataTypes.NO_IMAGE_DATA:
            self.setToolTip(f"{self._tpc.original_datatype_code.name} - {orig_format.name}")
        elif orig_format is not None:
            self.setToolTip(orig_format.name)

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

        image = QImage(rgba, width, height, QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(image)
        self.ui.textureImage.setPixmap(pixmap)
        self.ui.textureImage.setScaledContents(True)
        self.ui.txiEdit.setPlainText("")

    def build(self) -> tuple[bytes, bytes]:
        self._tpc.txi = self.ui.txiEdit.toPlainText()

        data: bytes | bytearray = bytearray()

        if self._restype in {ResourceType.TPC, ResourceType.TGA}:
            width, height, img_bytes = self._tpc.convert(TPCTextureFormat.RGB, 0, y_flip=True)
            self._tpc.set_data(width, height, [img_bytes], TPCTextureFormat.RGB)
            write_tpc(self._tpc, data, self._restype)
            return bytes(data), b""

        if self._restype in {ResourceType.PNG, ResourceType.BMP}:
            data = self.extract_png_bmp_bytes()
        elif self._restype is ResourceType.JPG:
            data = self.extract_tpc_jpeg_bytes()
        return data, b""

    def extract_tpc_jpeg_bytes(self) -> bytes:
        width, height, pixeldata = self._tpc.convert(TPCTextureFormat.RGB, 0)
        image = Image.frombuffer("RGB", (width, height), bytes(pixeldata))
        image = ImageOps.flip(image)

        dataIO = io.BytesIO()
        image.save(dataIO, "JPEG", quality=80)
        return dataIO.getvalue()

    def extract_png_bmp_bytes(self) -> bytes:
        width, height, pixeldata = self._tpc.convert(TPCTextureFormat.RGBA, 0)
        image = Image.frombuffer("RGBA", (width, height), pixeldata)
        image = ImageOps.flip(image)

        dataIO = io.BytesIO()
        image.save(dataIO, "PNG" if self._restype is ResourceType.PNG else "BMP")
        return dataIO.getvalue()
