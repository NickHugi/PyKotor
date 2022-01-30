import sys

from PyQt5.QtWidgets import QApplication

from mainwindow import ToolWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ToolWindow()
    window.show()
    sys.exit(app.exec_())
