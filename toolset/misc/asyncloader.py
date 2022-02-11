import traceback
from typing import Callable, Optional, Any, List

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

        with open("errorlog.txt", 'a') as file:
            lines = traceback.format_exception(type(self.error), self.error, self.error.__traceback__)
            file.writelines(lines)
            file.write("\n----------------------\n")


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


class AsyncBatchLoader(QDialog):
    def __init__(self, parent: QWidget, title: str, tasks: List[Callable], errorTitle: str = None, *,
                 cascade: bool = False):
        super().__init__(parent)

        self._progressBar = QProgressBar(self)
        self._progressBar.setMinimum(0)
        self._progressBar.setMaximum(len(tasks))
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

        self.value: List[Any] = []
        self.errors: List[Exception] = []
        self.errorTitle: Optional[str] = errorTitle
        self.successCount = 0
        self.failCount = 0

        self._worker = AsyncBatchWorker(self, tasks, cascade)
        self._worker.successful.connect(self._onSuccessful)
        self._worker.failed.connect(self._onFailed)
        self._worker.completed.connect(self._onAllCompleted)
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
        self.value.append(result)
        self.successCount += 1
        self._progressBar.setValue(self._progressBar.value() + 1)

    def _onFailed(self, error: Exception):
        self.errors.append(error)
        self.failCount += 1
        self._progressBar.setValue(self._progressBar.value() + 1)

    def _onAllCompleted(self):
        if self.errors:
            self.reject()
            if self.errorTitle:
                errorStrings = [str(error)+"\n" for error in self.errors]
                QMessageBox(QMessageBox.Critical, self.errorTitle, ''.join(errorStrings)).exec_()
            with open("errorlog.txt", 'a') as file:
                lines = []
                lines.extend(traceback.format_exception(type(e), e, e.__traceback__) for e in self.errors)
                file.writelines(lines)
                file.write("\n----------------------\n")
        else:
            self.accept()


class AsyncBatchWorker(QThread):
    successful = QtCore.pyqtSignal(object)
    failed = QtCore.pyqtSignal(object)
    completed = QtCore.pyqtSignal()

    def __init__(self, parent: QWidget, tasks: List[Callable], cascade: bool):
        super().__init__(parent)
        self._tasks: List[Callable] = tasks
        self._cascade: bool = cascade

    def run(self):
        for task in self._tasks:
            try:
                result = task()
                self.successful.emit(result)
            except Exception as e:
                self.failed.emit(e)
                if self._cascade:
                    break
        self.completed.emit()
