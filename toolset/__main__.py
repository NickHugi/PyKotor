import sys
import os

from PyQt5 import QtCore


sys.path.append('.')
sys.path.append('..')
if os.path.exists("./toolset") and getattr(sys, 'frozen', False) == False:
    os.chdir("./toolset")

import multiprocessing
import traceback
from types import TracebackType

from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QApplication

from mainwindow import ToolWindow


os.environ['QT_MULTIMEDIA_PREFERRED_PLUGINS'] = 'windowsmediafoundation'

os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
# os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"
# os.environ["QT_SCALE_FACTOR"] = "1"


def onAppCrash(e: BaseException, value: str, tback: TracebackType):
    with open("errorlog.txt", 'a') as file:
        file.writelines(traceback.format_exception(e, value, tback))
        file.write("\n----------------------\n")
    raise e


if __name__ == '__main__':
    multiprocessing.freeze_support()

    app = QApplication(sys.argv)

    # font = app.font()
    # font.setPixelSize(15)
    # app.setFont(font)
    # app.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    # app.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

    app.thread().setPriority(QThread.HighestPriority)

    sys.excepthook = onAppCrash
    window = ToolWindow()
    window.show()
    app.exec_()
