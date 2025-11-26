from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Generic, TypeVar

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from qtpy.QtCore import (
    QThread,
    QTimer,
    Qt,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtWidgets import QDialog, QLabel, QMessageBox, QProgressBar, QSizePolicy, QVBoxLayout

from toolset.gui.common.widgets.progressbar import AnimatedProgressBar
from utility.error_handling import format_exception_with_variables, universal_simplify_exception

if TYPE_CHECKING:
    from multiprocessing import Process, Queue

    from qtpy.QtGui import QCloseEvent
    from qtpy.QtWidgets import QWidget
    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]

T = TypeVar("T")


def human_readable_size(
    byte_size: float,
) -> str:
    for unit in ["bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]:
        if byte_size < 1024:  # noqa: PLR2004
            return f"{round(byte_size, 2)} {unit}"
        byte_size /= 1024
    return str(byte_size)


class ProgressDialog(QDialog):
    def __init__(
        self,
        progress_queue: Queue,
        title: str = "Operation Progress",
    ):
        super().__init__(None)
        self.progress_queue: Queue = progress_queue
        self.setWindowFlags(
            Qt.WindowType.Dialog  # pyright: ignore[reportGeneralTypeIssues]
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowStaysOnTopHint & ~Qt.WindowType.WindowContextHelpButtonHint & ~Qt.WindowType.WindowMinMaxButtonsHint
        )
        self.setWindowTitle(title)
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        from toolset.gui.common.localization import translate as tr
        self.status_label: QLabel = QLabel(tr("Initializing..."), self)
        self.bytes_label: QLabel = QLabel("")
        self.time_label: QLabel = QLabel(tr("Time remaining: --/--"))
        self.progress_bar: QProgressBar = QProgressBar(self)
        self.progress_bar.setMaximum(100)

        main_layout.addWidget(self.status_label)
        main_layout.addWidget(self.bytes_label)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.time_label)

        # Timer to poll the queue for new progress updates
        self.timer: QTimer = QTimer()
        self.timer.timeout.connect(self.check_queue)
        self.timer.start(100)  # Check every 100 ms
        self.setFixedSize(420, 80)

    def check_queue(self):
        while not self.progress_queue.empty():
            message = self.progress_queue.get()
            if message["action"] == "update_progress":
                # Handle progress updates
                data: dict[str, Any] = message["data"]
                total: int = data["total"]
                downloaded: int = data["downloaded"]
                progress: int = int((downloaded / total) * 100) if total else 0
                self.progress_bar.setValue(progress)
                from toolset.gui.common.localization import translate as tr, trf
                self.status_label.setText(trf("Downloading... {progress}%", progress=progress))
                time_remaining: str = data.get("time", self.time_label.text().replace(tr("Time remaining: "), ""))
                self.time_label.setText(trf("Time remaining: {time}", time=time_remaining))
                self.bytes_label.setText(f"{human_readable_size(downloaded)} / {human_readable_size(total)}")
            elif message["action"] == "update_status":
                # Handle status text updates
                text = message["text"]
                self.status_label.setText(text)
            elif message["action"] == "shutdown":
                self.close()

    def update_status(
        self,
        text: str,
    ):
        self.status_label.setText(text)

    @staticmethod
    def monitor_and_terminate(
        process: Process,
        timeout: int = 5,
    ):
        """Monitor and forcefully terminate if this doesn't exit gracefully."""
        process.join(timeout)  # Wait for the process to terminate for 'timeout' seconds
        if process.is_alive():  # Check if the process is still alive
            process.terminate()  # Forcefully terminate the process
            process.join()  # Wait for the process to terminate


class AsyncLoader(QDialog, Generic[T]):
    optional_finish_hook: Signal = Signal(object)  # pyright: ignore[reportPrivateImportUsage]
    optional_error_hook: Signal = Signal(object)  # pyright: ignore[reportPrivateImportUsage]

    def __init__(  # noqa: PLR0913
        self,
        parent: QWidget,
        title: str,
        task: Callable[..., T] | list[Callable[..., T]],
        error_title: str | None = None,
        *,
        start_immediately: bool = True,
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
        self.setWindowFlags(
            Qt.WindowType.Dialog  # pyright: ignore[reportArgumentType]
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowMinMaxButtonsHint  # Enable minimize/maximize buttons
            & ~Qt.WindowType.WindowContextHelpButtonHint
        )
        print("AsyncLoader.__init__: realtime_progress:", realtime_progress)

        self._progress_bar: AnimatedProgressBar = AnimatedProgressBar(self)
        self._progress_bar.setMinimum(0)
        if isinstance(task, list):
            self._progress_bar.setMaximum(len(task))
        else:
            self._progress_bar.setMaximum(1 if realtime_progress else 0)
        self._progress_bar.setTextVisible(realtime_progress or isinstance(task, list))

        self._main_task_text: QLabel = QLabel(self)
        self._main_task_text.setText("")
        self._main_task_text.setVisible(realtime_progress or isinstance(task, list))

        self._sub_task_text: QLabel = QLabel(self)
        self._sub_task_text.setText("")
        self._sub_task_text.setVisible(realtime_progress)

        self._task_progress_text: QLabel = QLabel(self)
        self._task_progress_text.setText("")
        self._task_progress_text.setVisible(isinstance(task, list))

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        main_layout.addWidget(self._main_task_text)
        main_layout.addWidget(self._progress_bar)
        main_layout.addWidget(self._sub_task_text)
        main_layout.addWidget(self._task_progress_text)

        self.setWindowTitle(title)
        self.setMinimumSize(260, 40)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
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
        self._progress_bar.setFixedHeight(20)  # Makes the progress bar taller
        self._main_task_text.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Centers the main task text
        self._sub_task_text.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Centers the sub task text
        self._task_progress_text.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Centers the task progress text

        self.value: T | None = None  # type: ignore[assignment]
        self.error: Exception | None = None
        self.errors: list[Exception] = []
        self.error_title: str | None = error_title
        self._realtime_progress: bool = realtime_progress

        self._worker: AsyncWorker = AsyncWorker(self, task, realtime_progress=realtime_progress)
        self._worker.successful.connect(self._on_successful)
        self._worker.failed.connect(self._on_failed)
        self._worker.completed.connect(self._on_completed)
        if realtime_progress or isinstance(task, list):
            self._worker.progress.connect(self._on_progress)
        if start_immediately:
            self.start_worker()

    def progress_callback_api(
        self,
        data: int | str,
        mtype: Literal["set_maximum", "increment", "update_maintask_text", "update_subtask_text"],
    ):
        self._worker.progress.emit(data, mtype)

    def start_worker(self):
        self._worker.start()

    def closeEvent(
        self,
        e: QCloseEvent,  # pyright: ignore[reportIncompatibleMethodOverride]
    ):
        self._worker.terminate()

    def _on_successful(
        self,
        result: Any,
    ):
        self.value = result
        self.optional_finish_hook.emit(result)

    def _on_failed(
        self,
        error: Exception,
    ):
        print("AsyncLoader._on_failed")
        self.errors.append(error)
        self.optional_error_hook.emit(error)
        RobustLogger().error(str(error), exc_info=error)
        if len(self.errors) == 1:  # Keep the first error as the main error
            self.error = error

    def _on_completed(self):
        print("_on_completed")
        if self.error is not None:
            self.reject()
            self._show_error_dialog()
        else:
            self.accept()

    def _show_error_dialog(self):
        print("AsyncLoader._show_error_dialog")
        if self.error_title:
            error_msgs = ""
            for i, e in enumerate(self.errors):
                this_err_msg = str(universal_simplify_exception(e)).replace("\n", "<br>")
                error_msgs += f"<br>Error in task {i + 1}: {this_err_msg}"
            error_msgs += " " * 700 + "<br>" * 2
            msg_box = QMessageBox(QMessageBox.Icon.Critical, self.error_title + " " * 700, error_msgs)
            msg_box.setDetailedText("\n\n".join(format_exception_with_variables(e) for e in self.errors))
            msg_box.exec()

    def _on_progress(
        self,
        value: int | str,
        task_type: Literal["set_maximum", "increment", "update_maintask_text", "update_subtask_text"],
    ):
        if task_type == "increment":
            assert isinstance(value, int)
            self._progress_bar.setValue(self._progress_bar.value() + value)
        elif task_type == "set_maximum":
            assert isinstance(value, int)
            self._progress_bar.setMaximum(value)
        elif task_type == "update_maintask_text":
            assert isinstance(value, str)
            self._main_task_text.setText(value)
        elif task_type == "update_subtask_text":
            assert isinstance(value, str)
            self._sub_task_text.setText(value)
        self._task_progress_text.setText(f"{self._progress_bar.value()}/{self._progress_bar.maximum()}")
        old_width = self.width()
        self.adjustSize()
        self.setMinimumSize(self.size())
        new_width = self.width()
        width_change = new_width - old_width
        if width_change > 0:
            self.move(self.x() - width_change // 2, self.y())


class AsyncWorker(QThread, Generic[T]):
    successful: Signal = Signal(object)  # pyright: ignore[reportPrivateImportUsage]
    failed: Signal = Signal(object)  # pyright: ignore[reportPrivateImportUsage]
    progress: Signal = Signal(object, str)  # pyright: ignore[reportPrivateImportUsage]
    completed: Signal = Signal()  # pyright: ignore[reportPrivateImportUsage]

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

    def progress_callback(
        self,
        value: int | str,
        task_type: Literal["set_maximum", "increment", "update_maintask_text", "update_subtask_text"],
    ):
        self.progress.emit(value, task_type)
