from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from PyQt5 import QtCore
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QDialog, QLabel, QMessageBox, QProgressBar, QVBoxLayout

from toolset.__main__ import is_frozen
from utility.error_handling import format_exception_with_variables, universal_simplify_exception
from utility.misc import is_debug_mode
from utility.system.path import Path

if TYPE_CHECKING:
    from PyQt5.QtGui import QCloseEvent
    from PyQt5.QtWidgets import QWidget


class AsyncLoader(QDialog):
    def __init__(
        self,
        parent: QWidget,
        title: str,
        task: Callable,
        errorTitle: str | None = None,
    ):
        """Initializes a progress dialog.

        Args:
        ----
            parent: QWidget: The parent widget of the dialog.
            title: str: The title of the dialog window.
            task: Callable: The task to run asynchronously.

        Returns:
        -------
            None: Does not return anything.

        Processing Logic:
        ----------------
            - Creates a QProgressBar and QLabel to display progress
            - Sets the dialog layout, title and size
            - Starts an AsyncWorker thread to run the task asynchronously
            - Connects callbacks for successful/failed task completion.
        """
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
        self.error: Exception | None = None
        self.errorTitle: str | None = errorTitle

        self._worker = AsyncWorker(self, task)
        self._worker.successful.connect(self._onSuccessful)
        self._worker.failed.connect(self._onFailed)
        self._worker.start()

    def closeEvent(self, e: QCloseEvent):
        self._worker.terminate()

    def updateInfo(self, text: str):
        self._infoText.setText(text)
        if not text:
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

        with Path("errorlog.txt").open("a", encoding="utf-8") as file:
            lines = format_exception_with_variables(self.error)
            file.writelines(lines)
            file.write("\n----------------------\n")

        if self.errorTitle:
            QMessageBox(QMessageBox.Critical, self.errorTitle, str(universal_simplify_exception(error))).exec_()


class AsyncWorker(QThread):
    successful = QtCore.pyqtSignal(object)
    failed = QtCore.pyqtSignal(object)

    def __init__(
        self,
        parent: QWidget,
        task: Callable,
    ):
        super().__init__(parent)
        self._task = task

    def run(self):
        try:
            self.successful.emit(self._task())
        except Exception as e:  # noqa: BLE001
            self.failed.emit(e)


class AsyncBatchLoader(QDialog):
    def __init__(
        self,
        parent: QWidget | None,
        title: str,
        tasks: list[Callable],
        errorTitle: str | None = None,
        *,
        cascade: bool = False,
    ):
        """Initializes a progress dialog for running multiple tasks asynchronously.

        Args:
        ----
            parent (QWidget): Parent widget
            title (str): Title of the progress dialog
            tasks (list[Callable]): List of tasks to run
            errorTitle (str | None): Title for error dialog, if any

        Processing Logic:
        ----------------
            - Sets up progress bar, info text and layout
            - Starts AsyncBatchWorker thread to run tasks asynchronously
            - Connects signals from worker for successful, failed and completed tasks.
        """
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

        self.value: list[Any] = []
        self.errors: list[Exception] = []
        self.errorTitle: str | None = errorTitle
        self.successCount = 0
        self.failCount = 0

        self._worker = AsyncBatchWorker(self, tasks, cascade)
        self._worker.successful.connect(self._onSuccessful)
        self._worker.failed.connect(self._onFailed)
        self._worker.completed.connect(self._onAllCompleted)
        self._worker.start()

    def closeEvent(self, e: QCloseEvent):
        self._worker.terminate()

    def addTask(self, task: Callable):
        self._worker.addTask(task)
        self._progressBar.setMaximum(self._worker.numTasks())

    def updateInfo(self, text: str):
        self._infoText.setText(text)
        if not text:
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
        with Path("errorlog.txt").open("a", encoding="utf-8") as file:
            try:
                file.writelines(format_exception_with_variables(error))
            except Exception:  # noqa: BLE001
                file.writelines(str(error))

    def _onAllCompleted(self):
        if not self.errors:
            self.accept()
            return

        self.reject()
        if not self.errorTitle:
            return

        errorTitle = self.errorTitle
        if self.failCount:
            errorTitle = f"{self.errorTitle} ({self.failCount} errors)"
        QMessageBox(
            QMessageBox.Critical,
            errorTitle,
            "\n".join(str(universal_simplify_exception(error)) for error in self.errors),
        ).exec_()


class AsyncBatchWorker(QThread):
    successful = QtCore.pyqtSignal(object)
    failed = QtCore.pyqtSignal(object)
    completed = QtCore.pyqtSignal()

    def __init__(
        self,
        parent: QWidget,
        tasks: list[Callable],
        cascade: bool,
    ):
        super().__init__(parent)
        self._tasks: list[Callable] = tasks
        self._cascade: bool = cascade

    def run(self):
        for task in self._tasks:
            try:
                result = task()
                self.successful.emit(result)
            except Exception as e:  # noqa: PERF203, BLE001
                self.failed.emit(e)
                if self._cascade:
                    break
        self.completed.emit()

    def addTask(self, task: Callable):
        self._tasks.append(task)

    def numTasks(self) -> int:
        return len(self._tasks)
