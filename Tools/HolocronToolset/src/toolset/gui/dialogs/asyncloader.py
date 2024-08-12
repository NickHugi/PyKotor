from __future__ import annotations

import cProfile
import uuid

from typing import TYPE_CHECKING, Any, Callable, Generic, TypeVar

from qtpy import QtCore
from qtpy.QtCore import QThread, QTimer, Qt
from qtpy.QtWidgets import QDialog, QLabel, QMessageBox, QProgressBar, QSizePolicy, QVBoxLayout

from toolset.gui.common.widgets.progressbar import AnimatedProgressBar
from utility.error_handling import format_exception_with_variables, universal_simplify_exception
from utility.logger_util import RobustRootLogger

if TYPE_CHECKING:
    from multiprocessing import Process, Queue

    from qtpy.QtGui import QCloseEvent
    from qtpy.QtWidgets import QWidget
    from typing_extensions import Literal

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
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowStaysOnTopHint & ~QtCore.Qt.WindowContextHelpButtonHint & ~QtCore.Qt.WindowMinMaxButtonsHint)
        self.setWindowTitle(title)
        self.setLayout(QVBoxLayout())

        self.statusLabel = QLabel("Initializing...", self)
        self.bytesLabel = QLabel("")
        self.timeLabel = QLabel("Time remaining: --/--")
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
                time_remaining = data.get("time", self.timeLabel.text().replace("Time remaining: ", ""))
                self.timeLabel.setText(f"Time remaining: {time_remaining}")
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
    optionalFinishHook = QtCore.Signal(object)  # pyright: ignore[reportPrivateImportUsage]
    optionalErrorHook = QtCore.Signal(object)  # pyright: ignore[reportPrivateImportUsage]

    def __init__(
        self,
        parent: QWidget,
        title: str,
        task: Callable[..., T] | list[Callable[..., T]],
        errorTitle: str | None = None,
        *,
        startImmediately: bool = True,
        realtime_progress: bool = False,
    ):
        """Initializes a progress dialog.

        Args:
        ----
            parent: QWidget: The parent widget of the dialog.
            title: str: The title of the dialog window.
            task: Callable or list of Callables: The task(s) to run asynchronously.

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
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowStaysOnTopHint & ~QtCore.Qt.WindowContextHelpButtonHint & ~QtCore.Qt.WindowMinMaxButtonsHint)
        print("AsyncLoader.__init__: realtime_progress:", realtime_progress)

        self._progressBar = AnimatedProgressBar(self)
        self._progressBar.setMinimum(0)
        if isinstance(task, list):
            self._progressBar.setMaximum(len(task))
        else:
            self._progressBar.setMaximum(1 if realtime_progress else 0)
        self._progressBar.setTextVisible(realtime_progress or isinstance(task, list))

        self._mainTaskText: QLabel = QLabel(self)
        self._mainTaskText.setText("")
        self._mainTaskText.setVisible(realtime_progress or isinstance(task, list))

        self._subTaskText: QLabel = QLabel(self)
        self._subTaskText.setText("")
        self._subTaskText.setVisible(realtime_progress)

        self._taskProgressText: QLabel = QLabel(self)
        self._taskProgressText.setText("")
        self._taskProgressText.setVisible(isinstance(task, list))

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self._mainTaskText)
        self.layout().addWidget(self._progressBar)
        self.layout().addWidget(self._subTaskText)
        self.layout().addWidget(self._taskProgressText)

        self.setWindowTitle(title)
        self.setMinimumSize(260, 40)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setStyleSheet("""
    QDialog {
        border-radius: 10px;
        padding: 20px;
        font-size: 12pt;
    }
    QLabel {
        font-size: 12pt 'Arial';
        margin-top: 6px;
        margin-bottom: 6px;
    }
    QProgressBar {
        font-size: 12pt 'Arial';
        min-height: 20px;
        max-height: 20px;
        border: 1px solid palette(dark);
        border-radius: 10px;
        background-color: palette(base);
        text-align: center;
    }
    QProgressBar::chunk {
        border-radius: 9px;
        background: qlineargradient(
            x1: 0, y1: 0, x2: 1, y2: 0,
            stop: 0 #008800, stop: 0.5 #00ff00, stop: 1 #008800
        );
        border: 1px solid rgba(0, 255, 0, 0.5);
        margin: 1px;
    }
""")
        self._progressBar.setFixedHeight(20)  # Makes the progress bar taller
        self._mainTaskText.setAlignment(Qt.AlignCenter)  # Centers the main task text
        self._subTaskText.setAlignment(Qt.AlignCenter)  # Centers the sub task text
        self._taskProgressText.setAlignment(Qt.AlignCenter)  # Centers the task progress text

        self.value: T | None = None  # type: ignore[assignment]
        self.error: Exception | None = None
        self.errors: list[Exception] = []
        self.errorTitle: str | None = errorTitle
        self._realtime_progress: bool = realtime_progress

        self._worker = AsyncWorker(self, task, realtime_progress=realtime_progress)
        self._worker.successful.connect(self._onSuccessful)
        self._worker.failed.connect(self._onFailed)
        self._worker.completed.connect(self._onCompleted)
        if realtime_progress or isinstance(task, list):
            self._worker.progress.connect(self._onProgress)
        if startImmediately:
            self.startWorker()

    def startWorker(self):
        self._worker.start()

    def closeEvent(self, e: QCloseEvent):
        self._worker.terminate()

    def _onSuccessful(self, result: Any):
        self.value = result
        self.optionalFinishHook.emit(result)

    def _onFailed(self, error: Exception):
        print("AsyncLoader._onFailed")
        self.errors.append(error)
        self.optionalErrorHook.emit(error)
        RobustRootLogger().error(str(error), exc_info=error)
        if len(self.errors) == 1:  # Keep the first error as the main error
            self.error = error

    def _onCompleted(self):
        print("_onCompleted")
        if self.error is not None:
            self.reject()
            self._showErrorDialog()
        else:
            self.accept()

    def _showErrorDialog(self):
        print("AsyncLoader._showErrorDialog")
        if self.errorTitle:
            error_msgs = ""
            for i, e in enumerate(self.errors):
                this_err_msg = str(universal_simplify_exception(e)).replace("\n", "<br>")
                error_msgs += f"<br>Error in task {i + 1}: {this_err_msg}"
            error_msgs += " "*700 + "<br>"*2
            msgBox = QMessageBox(QMessageBox.Icon.Critical, self.errorTitle + " "*700, error_msgs)
            msgBox.setDetailedText("\n\n".join(format_exception_with_variables(e) for e in self.errors))
            msgBox.exec_()

    def _onProgress(
        self,
        value: int | str,
        task_type: Literal["set_maximum", "increment", "update_maintask_text", "update_subtask_text"],
    ):
        if task_type == "increment":
            assert isinstance(value, int)
            self._progressBar.setValue(self._progressBar.value() + value)
        elif task_type == "set_maximum":
            assert isinstance(value, int)
            self._progressBar.setMaximum(value)
        elif task_type == "update_maintask_text":
            assert isinstance(value, str)
            self._mainTaskText.setText(value)
        elif task_type == "update_subtask_text":
            assert isinstance(value, str)
            self._subTaskText.setText(value)
        self._taskProgressText.setText(f"{self._progressBar.value()}/{self._progressBar.maximum()}")
        old_width = self.width()
        self.adjustSize()
        self.setMinimumSize(self.size())
        new_width = self.width()
        width_change = new_width - old_width
        if width_change > 0:
            self.move(self.x() - width_change // 2, self.y())


class AsyncWorker(QThread):
    successful = QtCore.Signal(object)  # pyright: ignore[reportPrivateImportUsage]
    failed = QtCore.Signal(object)  # pyright: ignore[reportPrivateImportUsage]
    progress = QtCore.Signal(object, str)  # pyright: ignore[reportPrivateImportUsage]
    completed = QtCore.Signal()  # pyright: ignore[reportPrivateImportUsage]

    def __init__(
        self,
        parent: QWidget,
        task: Callable[..., T] | list[Callable[..., T]],
        *,
        realtime_progress: bool = False,
        fast_fail: bool = False,
    ):
        super().__init__(parent)
        print("AsyncWorker.__init__: realtime_progress:", realtime_progress)
        self._tasks: list[Callable[..., T]] = task if isinstance(task, list) else [task]
        self._realtime_progress: bool = realtime_progress
        self._fast_fail: bool = fast_fail

    def run(self):
        use_profiler: bool = False # set to False to disable the profiler.
        if use_profiler:
            profiler = cProfile.Profile()
            profiler.enable()
        result = None
        for task in self._tasks:
            if len(self._tasks) > 1:
                self.progress_callback(1, "increment")
            try:
                result = task()
            except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
                self.failed.emit(e)
                if self._fast_fail:
                    print("fast fail, emit completed")
                    self.completed.emit()
                    break
            else:
                self.successful.emit(result)
        self.completed.emit()
        if use_profiler:
            profiler.disable()
            profiler.dump_stats(f"{uuid.uuid1().hex[:7]}_async_worker.pstat")

    def progress_callback(
        self,
        value: int | str,
        task_type: Literal["set_maximum", "increment", "update_maintask_text", "update_subtask_text"],
    ):
        self.progress.emit(value, task_type)
