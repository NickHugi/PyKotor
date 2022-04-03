import sys
sys.path.append('.')
sys.path.append('..')

import multiprocessing
import os
import traceback
from types import TracebackType

from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QApplication

from mainwindow import ToolWindow


os.environ['QT_MULTIMEDIA_PREFERRED_PLUGINS'] = 'windowsmediafoundation'


def onAppCrash(e: BaseException, value: str, tback: TracebackType):
    with open("errorlog.txt", 'a') as file:
        file.writelines(traceback.format_exception(e, value, tback))
        file.write("\n----------------------\n")
    raise e


if __name__ == '__main__':
    multiprocessing.freeze_support()

    app = QApplication(sys.argv)
    app.thread().setPriority(QThread.HighestPriority)
    sys.excepthook = onAppCrash
    window = ToolWindow()
    window.show()
    app.exec_()
