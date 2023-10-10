from __future__ import annotations

import multiprocessing
import os
from pathlib import Path
import sys
import traceback

from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QApplication

sys.path.append(".")
sys.path.append("..")
from typing import TYPE_CHECKING

from toolset.gui.windows.main import ToolWindow

if TYPE_CHECKING:
    from types import TracebackType

os.environ["QT_MULTIMEDIA_PREFERRED_PLUGINS"] = "windowsmediafoundation"
os.environ["QT_DEBUG_PLUGINS"] = "1"

# os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"  # noqa: ERA001
# os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"  # noqa: ERA001
# os.environ["QT_SCALE_FACTOR"] = "1"  # noqa: ERA001


def onAppCrash(e: BaseException, value: str, tback: TracebackType):
    with Path("errorlog.txt").open("a") as file:
        file.writelines(traceback.format_exception(e, value, tback))
        file.write("\n----------------------\n")
    raise e


if __name__ == "__main__":
    multiprocessing.freeze_support()

    app = QApplication(sys.argv)

    # font = app.font()  # noqa: ERA001
    # font.setPixelSize(15)  # noqa: ERA001
    # app.setFont(font)  # noqa: ERA001
    # app.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)  # noqa: ERA001
    # app.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)  # noqa: ERA001

    app.thread().setPriority(QThread.HighestPriority)

    sys.excepthook = onAppCrash
    window = ToolWindow()
    window.show()
    app.exec_()
