from typing import Callable, Optional, Any

from PyQt5 import QtCore
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QDialog, QWidget, QProgressBar, QMessageBox, QVBoxLayout, QLabel


class AsyncLoader(QDialog):
    def __init__(self, parent: QWidget, title: str, task: Callable, errorTitle: str = None):
        super().__init__(parent)

        self._progressBar = QProgressBar(self)
        self._progressBar.setMinimum(0)
        self._progressBar.setMaximum(0)
        self._progressBar.setTextVisible(False)

        self._infoText: QLabel = QLabel(self)
        self._infoText.setText("")
        self._infoText.setVisible(False)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self._progressBar)
        self.layout().addWidget(self._infoText)

        self.setWindowTitle(title)
        self.setFixedSize(260, 40)

        self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)

        self.value: Any = None
        self.error: Optional[Exception] = None
        self.errorTitle: Optional[str] = errorTitle

        self._worker = AsyncWorker(self, task)
        self._worker.successful.connect(self._onSuccessful)
        self._worker.failed.connect(self._onFailed)
        self._worker.start()

    def updateInfo(self, text: str):
        self._infoText.setText(text)
        if text == "":
            self.setFixedSize(260, 40)
            self._infoText.setVisible(False)
        else:
            self.setFixedSize(260, 60)
            self._infoText.setVisible(True)

    def _onSuccessful(self, result: Any):
        self.value = result
        self.accept()

    def _onFailed(self, error: Exception):
        self.error = error
        self.reject()

        if self.errorTitle:
            QMessageBox(QMessageBox.Critical, self.errorTitle, str(error)).exec_()


class AsyncWorker(QThread):
    successful = QtCore.pyqtSignal(object)
    failed = QtCore.pyqtSignal(object)

    def __init__(self, parent: QWidget, task: Callable):
        super().__init__(parent)
        self._task = task

    def run(self):
        try:
            self.successful.emit(self._task())
        except Exception as e:
            self.failed.emit(e)
