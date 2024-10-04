from __future__ import annotations

import sys

from io import BytesIO
from typing import TYPE_CHECKING

from loggerplus import RobustLogger
from qtpy.QtCore import QFileInfo, QObject, QTemporaryFile, QTimer, Qt, Signal
from qtpy.QtGui import QIcon, QImage, QPainter, QPixmap
from qtpy.QtWidgets import QApplication, QFileIconProvider, QStyle

if TYPE_CHECKING:
    import pathlib


import concurrent.futures


def load_icon_task(file_path: str) -> concurrent.futures.Future:
    app = QApplication.instance() or QApplication(sys.argv)
    future = concurrent.futures.Future()
    QTimer.singleShot(0, lambda: _load_icon_task(file_path, future))
    app.exec()
    return future

def _load_icon_task(file_path: str, future: concurrent.futures.Future) -> None:
    icon = QFileIconProvider().icon(QFileInfo(file_path))
    future.set_result((file_path, icon))


def load_thumbnail_task(file_path: str) -> concurrent.futures.Future:
    app = QApplication.instance() or QApplication(sys.argv)
    future = concurrent.futures.Future()
    QTimer.singleShot(0, lambda: _load_thumbnail_task(file_path, future))
    app.exec()
    return future

def _load_thumbnail_task(file_path: str, future: concurrent.futures.Future) -> None:
    image = QImage(file_path)
    if not image.isNull():
        image = image.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    else:
        image = QImage(64, 64, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)
    future.set_result((file_path, image))


class IconLoader(QObject):
    icon_loaded = Signal(str, QIcon)
    thumbnail_loaded = Signal(str, QImage)

    def __init__(self):
        super().__init__()
        self.executor = concurrent.futures.ProcessPoolExecutor()

    def load_icon(self, file_path: str):
        future = self.executor.submit(load_icon_task, file_path)
        future.add_done_callback(self._on_icon_loaded)

    def load_thumbnail(self, file_path: str):
        future = self.executor.submit(load_thumbnail_task, file_path)
        future.add_done_callback(self._on_thumbnail_loaded)

    def _on_icon_loaded(self, future):
        file_path, icon = future.result()
        self.icon_loaded.emit(file_path, icon)

    def _on_thumbnail_loaded(self, future):
        file_path, image = future.result()
        self.thumbnail_loaded.emit(file_path, image)


def qpixmap_to_qicon(
    std_pixmap: QStyle.StandardPixmap,
    w: int = 16,
    h: int = 16,
) -> QIcon:
    style = QApplication.style()
    assert style is not None
    icon = style.standardIcon(std_pixmap)
    if isinstance(icon, QIcon):
        return icon

    pixmap = QPixmap(w, h)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.drawPixmap(0, 0, style.standardPixmap(std_pixmap))
    painter.end()

    return QIcon(pixmap)


def qicon_from_file_ext(extension: str) -> QIcon:
    temp_file = QTemporaryFile(f"XXXXXX.{extension}")
    temp_file.setAutoRemove(False)
    temp_file.open()

    try:
        icon = QFileIconProvider().icon(QFileInfo(temp_file.fileName()))
        if icon.pixmap(32, 32).isNull():
            RobustLogger()(f"<SDM> Failed to retrieve a valid icon for extension '{extension}'")
            return qpixmap_to_qicon(QStyle.StandardPixmap.SP_DirIcon)
        return icon

    finally:
        temp_file.close()
        temp_file.remove()


def _process_qt_image(filepath_obj: pathlib.Path, mipmap: int) -> tuple[int, int, bytes] | None:
    from qtpy.QtCore import Qt
    from qtpy.QtGui import QImage, QImageReader

    if filepath_obj.suffix.lower() in [bytes(x.data()).decode().lower() for x in QImageReader.supportedImageFormats()]:
        qimg = QImage()
        if qimg.loadFromData(filepath_obj.read_bytes()):
            if mipmap < qimg.width() or mipmap < qimg.height():
                qimg = qimg.scaled(mipmap, mipmap, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            return qimg.width(), qimg.height(), bytes(qimg.constBits().asarray())
    return None

def _process_pil_image(filepath_obj: pathlib.Path, mipmap: int, img_format: str) -> tuple[int, int, bytes] | None:
    from PIL import Image

    if filepath_obj.suffix.lower() in Image.registered_extensions():
        with Image.open(BytesIO(filepath_obj.read_bytes())) as img:
            if mipmap < img.width or mipmap < img.height:
                resized_img = img.resize((mipmap, mipmap), Image.Resampling.LANCZOS)
            pil_img = resized_img.convert(img_format if img_format != "Default" else resized_img.mode)
        return pil_img.width, pil_img.height, pil_img.tobytes()
    return None

def _process_tpc_image(filepath_obj: pathlib.Path, mipmap: int) -> tuple[int, int, bytes] | None:
    if filepath_obj.suffix.lower() == ".tpc":
        from pykotor.resource.formats.tpc.tpc_auto import read_tpc
        from pykotor.resource.formats.tpc.tpc_data import TPCTextureFormat

        tpc = read_tpc(filepath_obj.read_bytes())
        best_mipmap = next((i for i in range(tpc.mipmap_count()) if tpc.get(i).width <= mipmap), 0)
        return tpc.convert(TPCTextureFormat.RGBA, best_mipmap)
    return None
