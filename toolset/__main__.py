import sys
import traceback
from types import TracebackType

from PyQt5.QtWidgets import QApplication

from mainwindow import ToolWindow


def onAppCrash(e: BaseException, value: str, tback: TracebackType):
    with open("errorlog.txt", 'a') as file:
        file.writelines(traceback.format_exception(e, value, tback))
        file.write("\n----------------------\n")
    raise e


if __name__ == '__main__':
    app = QApplication(sys.argv)
    sys.excepthook = onAppCrash
    window = ToolWindow()
    window.show()
    app.exec_()
