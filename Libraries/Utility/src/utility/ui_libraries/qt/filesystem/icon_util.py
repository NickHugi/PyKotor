from __future__ import annotations

import os
import pathlib
import sys

from loggerplus import RobustLogger


def update_sys_path(path: pathlib.Path):
    working_dir = str(path)
    print("<SDM> [update_sys_path scope] working_dir: ", working_dir)

    if working_dir not in sys.path:
        sys.path.append(working_dir)


file_absolute_path = pathlib.Path(__file__).resolve()

pykotor_path = file_absolute_path.parents[8] / "Libraries" / "PyKotor" / "src" / "pykotor"
if pykotor_path.exists():
    update_sys_path(pykotor_path.parent)
pykotor_gl_path = file_absolute_path.parents[8] / "Libraries" / "PyKotorGL" / "src" / "pykotor"
if pykotor_gl_path.exists():
    update_sys_path(pykotor_gl_path.parent)
utility_path = file_absolute_path.parents[5]
if utility_path.exists():
    update_sys_path(utility_path)
toolset_path = file_absolute_path.parents[8] / "Tools/HolocronToolset/src/toolset"
if toolset_path.exists():
    update_sys_path(toolset_path.parent)
    os.chdir(toolset_path)
print(toolset_path)
print(utility_path)

import qtpy  # noqa: E402

if qtpy.API_NAME in ("PyQt6", "PySide6"):
    QDesktopWidget = None
    from qtpy.QtGui import QUndoCommand, QUndoStack  # pyright: ignore[reportPrivateImportUsage]  # noqa: F401
elif qtpy.API_NAME in ("PyQt5", "PySide2"):
    from qtpy.QtWidgets import QDesktopWidget, QUndoCommand, QUndoStack  # noqa: F401  # pyright: ignore[reportPrivateImportUsage]
else:
    raise RuntimeError(f"Unexpected qtpy version: '{qtpy.API_NAME}'")



from qtpy.QtCore import QFileInfo, QTemporaryFile, Qt  # noqa: E402
from qtpy.QtGui import QIcon, QPainter, QPixmap  # noqa: E402
from qtpy.QtWidgets import QApplication, QFileIconProvider, QStyle  # noqa: E402


def qpixmap_to_qicon(
    std_pixmap: QStyle.StandardPixmap,
    w: int = 16,
    h: int = 16,
) -> QIcon:
    style = QApplication.style()
    assert style is not None
    icon = style.standardIcon(std_pixmap)  # seems to fail often, yet is the most widely accepted stackoverflow answer?
    if isinstance(icon, QIcon):
        return icon

    # fallback
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
