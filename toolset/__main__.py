import multiprocessing
import os
import pathlib
import sys
import traceback
from types import TracebackType

from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QApplication

if getattr(sys, "frozen", False) is False:
    pykotor_path = pathlib.Path(__file__).parents[1] / "pykotor"
    if pykotor_path.joinpath("__init__.py").exists():
        working_dir = str(pykotor_path.parent)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.insert(0, working_dir)
    toolset_path = pathlib.Path(__file__).parents[1] / "toolset"
    if toolset_path.joinpath("__init__.py").exists():
        os.chdir(toolset_path)

from toolset.gui.windows.main import ToolWindow

os.environ["QT_MULTIMEDIA_PREFERRED_PLUGINS"] = "windowsmediafoundation"
os.environ["QT_DEBUG_PLUGINS"] = "1"

# os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
# os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"
# os.environ["QT_SCALE_FACTOR"] = "1"


def onAppCrash(e: BaseException, value: str, tback: TracebackType):
    with pathlib.Path("errorlog.txt").open("a") as file:
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
