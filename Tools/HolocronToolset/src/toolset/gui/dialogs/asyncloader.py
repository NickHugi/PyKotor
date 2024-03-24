from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Generic, TypeVar

from PyQt5 import QtCore
from PyQt5.QtCore import QThread, QTimer
from PyQt5.QtWidgets import QDialog, QLabel, QMessageBox, QProgressBar, QVBoxLayout

from utility.error_handling import format_exception_with_variables, universal_simplify_exception
from utility.system.path import Path

if TYPE_CHECKING:
    from multiprocessing import Process, Queue

    from PyQt5.QtGui import QCloseEvent
    from PyQt5.QtWidgets import QWidget

T = TypeVar("T")

def human_readable_size(byte_size: float) -> str:
    for unit in ["bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]:
        if byte_size < 1024:  # noqa: PLR2004
            return f"{round(byte_size, 2)} {unit}"
        byte_size /= 1024
    return str(byte_size)

class ProgressDialog(QDialog):
    def __init__(self, progress_queue: Queue, title: str = "Operation Progress"):
        super().__init__(None)
        self.progress_queue: Queue = progress_queue
        self.setWindowTitle(title)
        self.setLayout(QVBoxLayout())

        self.statusLabel = QLabel("Initializing...", self)
        self.bytesLabel = QLabel("")
        self.timeLabel = QLabel("--/--")
        self.progressBar = QProgressBar(self)
        self.progressBar.setMaximum(100)

        self.layout().addWidget(self.statusLabel)
        self.layout().addWidget(self.bytesLabel)
        self.layout().addWidget(self.progressBar)
        self.layout().addWidget(self.timeLabel)

        # Timer to poll the queue for new progress updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_queue)
        self.timer.start(100)  # Check every 100 ms
        self.setFixedSize(420, 80)

    def check_queue(self):
        while not self.progress_queue.empty():
            message = self.progress_queue.get()
            if message["action"] == "update_progress":
                # Handle progress updates
                data: dict[str, Any] = message["data"]
                downloaded = data["downloaded"]
                total = data["total"]
                progress = int((downloaded / total) * 100) if total else 0
                self.progressBar.setValue(progress)
                self.statusLabel.setText(f"Downloading... {progress}%")
                self.timeLabel.setText(f"Time remaining: {data.get('time', self.timeLabel.text())}")
                self.bytesLabel.setText(f"{human_readable_size(downloaded)} / {human_readable_size(total)}")
            elif message["action"] == "update_status":
                # Handle status text updates
                text = message["text"]
                self.statusLabel.setText(text)
            elif message["action"] == "shutdown":
                self.close()

    def update_status(self, text: str):
        self.statusLabel.setText(text)

    @staticmethod
    def monitor_and_terminate(process: Process, timeout: int = 5):
        """Monitor and forcefully terminate if this doesn't exit gracefully."""
        process.join(timeout)  # Wait for the process to terminate for 'timeout' seconds
        if process.is_alive():  # Check if the process is still alive
            process.terminate()  # Forcefully terminate the process
            process.join()  # Wait for the process to terminate


class AsyncLoader(QDialog, Generic[T]):
    optionalFinishHook = QtCore.pyqtSignal(object)
    optionalErrorHook = QtCore.pyqtSignal(object)

    def __init__(
        self,
        parent: QWidget,
        title: str,
        task: Callable[..., T],
        errorTitle: str | None = None,
        *,
        startImmediately: bool = True,
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

        self.value: T = None
        self.error: Exception | None = None
        self.errorTitle: str | None = errorTitle

        self._worker = AsyncWorker(self, task)
        self._worker.successful.connect(self._onSuccessful)
        self._worker.failed.connect(self._onFailed)
        if startImmediately:
            self.startWorker()

    def startWorker(self):
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
        self.optionalFinishHook.emit(result)
        self.accept()

    def _onFailed(self, error: Exception):
        self.error = error
        self.optionalErrorHook.emit(error)
        self.reject()

        with Path("errorlog.txt").open("a", encoding="utf-8") as file:
            lines = format_exception_with_variables(self.error)
            file.writelines(lines)
            file.write("\n----------------------\n")

        if self.errorTitle:
            error_msg = str(universal_simplify_exception(error)).replace("\n", "<br>")
            QMessageBox(QMessageBox.Critical, self.errorTitle, error_msg).exec_()


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
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
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
            except Exception:  # pylint: disable=W0718  # noqa: BLE001
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
            "\n".join(str(universal_simplify_exception(error)).replace(",", ":", 1) + "<br>" for error in self.errors),
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
            except Exception as e:  # pylint: disable=W0718  # noqa: PERF203, BLE001
                self.failed.emit(e)
                if self._cascade:
                    break
        self.completed.emit()

    def addTask(self, task: Callable):
        self._tasks.append(task)

    def numTasks(self) -> int:
        return len(self._tasks)
