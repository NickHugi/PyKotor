import os
import sys
from pathlib import Path

toolset_path = Path(__file__).parent
if toolset_path.exists() and getattr(sys, "frozen", False) is False:
    sys.path.append(str(toolset_path))
    sys.path.append(str(toolset_path.parent))

import multiprocessing
import traceback
from types import TracebackType

from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QApplication

from toolset.gui.windows.main import ToolWindow

os.environ["QT_MULTIMEDIA_PREFERRED_PLUGINS"] = "windowsmediafoundation"
os.environ["QT_DEBUG_PLUGINS"] = "1"

#os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
# os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"
# os.environ["QT_SCALE_FACTOR"] = "1"


def onAppCrash(e: BaseException, value: str, tback: TracebackType):
    with Path("errorlog.txt").open("a") as file:
        file.writelines(traceback.format_exception(e, value, tback))
        file.write("\n----------------------\n")
    raise e


if __name__ == "__main__":
    multiprocessing.freeze_support()

    app = QApplication(sys.argv)

    # font = app.font()
    # font.setPixelSize(15)
    # app.setFont(font)
    # app.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    # app.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

    app.thread().setPriority(QThread.HighestPriority)  # type: ignore[reportGeneralTypeIssues]

    sys.excepthook = onAppCrash
    window = ToolWindow()
    window.show()
    app.exec_()
