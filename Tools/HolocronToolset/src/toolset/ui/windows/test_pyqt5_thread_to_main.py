from __future__ import annotations

import sys
import threading

from qtpy.QtCore import QMetaObject, QThread, Qt, Slot
from qtpy.QtWidgets import QApplication, QMessageBox, QWidget


class ThreadSafeQMessageBox(QMessageBox):
    _lock = threading.Lock()

    @Slot()
    def exec_(self):
        QMetaObject.invokeMethod(self, "_real_exec_", Qt.ConnectionType.QueuedConnection)

    @Slot()
    def _real_exec_(self):
        QMessageBox.exec_(self)

    @classmethod
    def information(cls, parent: QWidget | None, title: str, text: str,
                    buttons: QMessageBox.StandardButtons = QMessageBox.Ok,
                    defaultButton: QMessageBox.StandardButton = QMessageBox.NoButton) -> QMessageBox.StandardButton:
        # Create an instance to handle the invocation
        instance = cls()
        instance._parent = parent
        instance._title = title
        instance._text = text
        instance._buttons = buttons
        instance._defaultButton = defaultButton
        result = []

        @Slot()
        def _real_information():
            result.append(QMessageBox.information(parent, title, text, buttons, defaultButton))

        instance._real_information = _real_information
        QMetaObject.invokeMethod(instance, "_real_information", Qt.ConnectionType.QueuedConnection)
        return result[0] if result else QMessageBox.NoButton  # Return default if not yet set


class WorkerThread(QThread):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.message_box = QMessageBox()

    def run(self):
        #self.message_box.setWindowTitle("Dynamic Title")
        #self.message_box.setText("This message is dynamically set at instantiation!")
        #self.message_box.exec_()
        assert QApplication.instance().thread() != QThread.currentThread(), "this is still the main thread!"
        self.message_box.information(None, "information title", "information text test")


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setGeometry(100, 100, 200, 200)
        self.setWindowTitle("Main Window")
        self._thread = WorkerThread()
        self._thread.start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
