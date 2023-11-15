from __future__ import annotations

import io
from typing import TYPE_CHECKING, Optional

from PIL import Image, ImageOps
from PyQt5.QtGui import QImage, QPixmap, QTransform

from pykotor.resource.formats.tpc import TPC, TPCTextureFormat, read_tpc, write_tpc
from pykotor.resource.type import ResourceType
from toolset.gui.editor import Editor

if TYPE_CHECKING:
    import os

    from PyQt5.QtWidgets import QWidget

    from pykotor.extract.installation import Installation


class TPCEditor(Editor):
    def __init__(self, parent: Optional[QWidget], installation: Optional[Installation] = None):
        """Initializes the texture viewer window.

        Args:
        ----
            parent: {QWidget}: The parent widget of this window
            installation: {Installation}: The installation context
        Returns:
            None: Does not return anything
        Processing Logic:
            - Initializes the base class with supported resource types
            - Loads the UI from the designer file
            - Sets up menus and connects signals
            - Creates a default 256x256 RGBA texture
            - Calls new() to display the default texture.
        """
        supported = [ResourceType.TPC, ResourceType.TGA, ResourceType.JPG, ResourceType.PNG, ResourceType.BMP]
        super().__init__(parent, "Texture Viewer", "none", supported, supported, installation)

        from toolset.uic.editors.tpc import Ui_MainWindow

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()

        self._tpc: TPC = TPC()
        self._tpc.set_single(256, 256, bytes(0 for i in range(256 * 256 * 4)), TPCTextureFormat.RGBA)

        self.new()

    def _setupSignals(self) -> None:
        ...

    def load(self, filepath: os.PathLike | str, resref: str, restype: ResourceType, data: bytes) -> None:
        """Load a resource into the editor
        Args:
            filepath: The path to the resource file
            resref: The resource reference
            restype: The resource type
            data: The raw resource data
        Returns:
            None
        Load resource:
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

        if restype in [ResourceType.TPC, ResourceType.TGA]:
            self._tpc = read_tpc(data)
        else:
            pillow = Image.open(io.BytesIO(data))
            pillow = pillow.convert("RGBA")
            pillow = ImageOps.flip(pillow)
            self._tpc = TPC()
            self._tpc.set_single(pillow.width, pillow.height, pillow.tobytes(), TPCTextureFormat.RGBA)

        width, height, rgba = self._tpc.convert(TPCTextureFormat.RGB, 0)

        image = QImage(rgba, width, height, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(image).transformed(QTransform().scale(1, -1))

        self.ui.textureImage.setPixmap(pixmap)
        self.ui.txiEdit.setPlainText(self._tpc.txi)

    def new(self) -> None:
        """Set texture image from TPC texture.

        Args:
        ----
            self: The class instance
        Returns:
            None: No return value
        Processing Logic:
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
        self.ui.txiEdit.setPlainText("")

    def build(self) -> tuple[bytes, bytes]:
        self._tpc.txi = self.ui.txiEdit.toPlainText()

        data = bytearray()

        if self._restype in [ResourceType.TPC, ResourceType.TGA]:
            write_tpc(self._tpc, data, self._restype)
        elif self._restype in [ResourceType.PNG, ResourceType.BMP]:
            data = self.extract_png_bmp_bytes()
        elif self._restype in [ResourceType.JPG]:
            data = self.extract_tpc_jpeg_bytes()
        return data, b""

    # TODO Rename this here and in `build`
    def extract_tpc_jpeg_bytes(self):
        """Extracts image from TPC texture and returns JPEG bytes
        Args:
            self: The class instance
        Returns:
            bytes: JPEG image bytes
        - Converts TPC texture to RGB pixel data
        - Creates PIL Image from pixel data
        - Flips the image vertically
        - Saves image to BytesIO as JPEG with 80% quality
        - Returns JPEG bytes from BytesIO.
        """
        width, height, pixeldata = self._tpc.convert(TPCTextureFormat.RGB, 0)
        image = Image.frombuffer("RGB", (width, height), bytes(pixeldata))
        image = ImageOps.flip(image)

        dataIO = io.BytesIO()
        image.save(dataIO, "JPEG", quality=80)
        return dataIO.getvalue()

    # TODO Rename this here and in `build`
    def extract_png_bmp_bytes(self):
        """Extracts texture data from a TPC texture
        Args:
            self: The TPC texture object
        Returns:
            bytes: Texture image data as bytes
        - Converts TPC texture to RGBA format
        - Creates PIL Image from texture pixel data
        - Flips the image vertically
        - Saves image to BytesIO stream as PNG or BMP
        - Returns bytes of image data.
        """
        width, height, pixeldata = self._tpc.convert(TPCTextureFormat.RGBA, 0)
        image = Image.frombuffer("RGBA", (width, height), pixeldata)
        image = ImageOps.flip(image)

        dataIO = io.BytesIO()
        image.save(dataIO, "PNG" if self._restype == ResourceType.PNG else "BMP")
        return dataIO.getvalue()
