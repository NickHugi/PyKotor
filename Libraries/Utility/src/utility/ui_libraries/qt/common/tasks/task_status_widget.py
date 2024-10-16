from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from qtpy.QtCore import QTimer, Qt, Signal
from qtpy.QtWidgets import QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QProgressBar, QPushButton, QVBoxLayout, QWidget

from utility.ui_libraries.qt.common.tasks.actions_executor import TaskStatus

if TYPE_CHECKING:
    from qtpy.QtGui import QMouseEvent

    from utility.ui_libraries.qt.common.tasks.actions_executor import FileActionsExecutor, Task


from dataclasses import dataclass


@dataclass
class TaskWidget:
    widget: QWidget
    progress_bar: QProgressBar
    status_label: QLabel


class TaskStatusWidget(QWidget):
    task_clicked = Signal(str)  # task_id

    def __init__(
        self,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.dispatcher: FileActionsExecutor | None = None
        self.task_widgets: dict[str, TaskWidget] = {}

    def set_dispatcher(self, dispatcher: FileActionsExecutor) -> None:
        self.dispatcher = dispatcher
        self._connect_signals()

        self._setup_layout()
        self._create_widgets()
        self._setup_timer()

    def _setup_layout(self) -> None:
        """Set up the main layout for the widget."""
        layout = QVBoxLayout(self)
        if not isinstance(layout, QVBoxLayout):
            raise TypeError("Expected QVBoxLayout")
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(layout)

    def _connect_signals(self) -> None:
        """Connect signals from the dispatcher to the widget's slots."""
        self.dispatcher.TaskStarted.connect(self.add_task)
        self.dispatcher.TaskCompleted.connect(self.update_task_status)
        self.dispatcher.TaskFailed.connect(self.update_task_status)
        self.dispatcher.TaskCancelled.connect(self.update_task_status)
        self.dispatcher.TaskPaused.connect(self.update_task_status)
        self.dispatcher.TaskResumed.connect(self.update_task_status)
        self.dispatcher.TaskProgress.connect(self.update_task_progress)
        self.dispatcher.ProgressUpdated.connect(self.update_overall_progress)

    def _create_widgets(self) -> None:
        """Create and add widgets to the layout."""
        self.clear_completed_button = QPushButton("Clear Completed Tasks")
        self.clear_completed_button.clicked.connect(self.clear_completed_tasks)

        self.overall_progress_bar = self._create_progress_bar()
        self.task_list = self._create_task_list()

        layout = self.layout()
        if not isinstance(layout, QVBoxLayout):
            raise TypeError("Expected QVBoxLayout")
        layout.addWidget(self.overall_progress_bar)
        layout.addWidget(self.task_list)
        layout.addWidget(self.clear_completed_button)

    def _create_progress_bar(self) -> QProgressBar:
        """Create and style the overall progress bar."""
        progress_bar = QProgressBar(self)
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        progress_bar.setFormat("%v/%m tasks completed")
        progress_bar.setStyleSheet(
            """
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
            }

            QProgressBar::chunk {
                background-color: #3498db;
                width: 10px;
                margin: 0.5px;
            }
            """
        )
        return progress_bar

    def _create_task_list(self) -> QListWidget:
        """Create and style the task list widget."""
        task_list = QListWidget(self)
        task_list.setStyleSheet(
            """
            QListWidget {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
            }

            QListWidget::item {
                border-bottom: 1px solid #ecf0f1;
                padding: 5px;
            }

            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            """
        )
        return task_list

    def _setup_timer(self) -> None:
        """Set up a timer to update all tasks periodically."""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_all_tasks)
        self.update_timer.start(1000)  # Update every second

    def add_task(self, task_id: str) -> None:
        """Add a new task to the widget.

        This function is crucial for displaying task progress to the user.
        """
        task = self.dispatcher.get_task(task_id)
        if task is None:
            return
        task_widget = self._create_task_widget(task)
        self.task_widgets[task_id] = task_widget
        item = QListWidgetItem(self.task_list)
        if not isinstance(item, QListWidgetItem):
            raise TypeError("Expected QListWidgetItem")
        item.setSizeHint(task_widget.widget.sizeHint())
        self.task_list.addItem(item)
        self.task_list.setItemWidget(item, task_widget.widget)

    def update_task_status(self, task_id: str, error: Exception | None = None) -> None:
        """Update the status of a task in the widget.

        This function is essential for keeping the user informed about task progress.
        """
        if task_id not in self.task_widgets:
            return
        task = self.dispatcher.get_task(task_id)
        if task is None:
            return
        self._update_task_widget(task)

    def update_task_progress(self, task_id: str, progress: float) -> None:
        """Update the progress of a task in the widget.

        This function is crucial for providing real-time feedback to the user.
        """
        if task_id not in self.task_widgets:
            return
        task_widget = self.task_widgets[task_id]
        task_widget.progress_bar.setValue(int(progress * 100))

    def update_overall_progress(self, completed_tasks: int, total_tasks: int) -> None:
        """Update the overall progress of all tasks.

        This function is essential for giving the user a high-level view of task completion.
        """
        if not isinstance(self.overall_progress_bar, QProgressBar):
            raise TypeError("Expected QProgressBar")
        self.overall_progress_bar.setMaximum(total_tasks)
        self.overall_progress_bar.setValue(completed_tasks)

    def _create_task_widget(self, task: Task) -> TaskWidget:
        """Create a widget for a single task.

        This function is crucial for providing a visual representation of each task.
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)

        name_label = QLabel(task.operation)
        name_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(name_label)

        description_label = QLabel(task.description)
        description_label.setWordWrap(True)
        layout.addWidget(description_label)

        progress_bar = self._create_task_progress_bar(task)
        layout.addWidget(progress_bar)

        status_label = QLabel(task.status.name)
        status_label.setObjectName("status_label")
        layout.addWidget(status_label)

        button_layout = self._create_button_layout(task)
        layout.addLayout(button_layout)

        widget.setProperty("task_id", task.id)
        widget.mousePressEvent = self._create_mouse_press_event(task.id)

        return TaskWidget(widget=widget, progress_bar=progress_bar, status_label=status_label)

    def _create_task_progress_bar(self, task: Task) -> QProgressBar:
        """Create and style a progress bar for a single task."""
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(int(task.progress * 100))
        progress_bar.setStyleSheet(
            """
            QProgressBar {
                border: 1px solid grey;
                border-radius: 3px;
                text-align: center;
            }

            QProgressBar::chunk {
                background-color: #2ecc71;
                width: 5px;
                margin: 0.5px;
            }
            """
        )
        return progress_bar

    def _create_button_layout(self, task: Task) -> QHBoxLayout:
        """Create a layout with buttons for controlling a task."""
        button_layout = QHBoxLayout()

        cancel_button = self._create_button("Cancel", "#e74c3c", "#c0392b", self._create_cancel_callback(task.id))
        button_layout.addWidget(cancel_button)

        pause_resume_button = self._create_button("Pause", "#f39c12", "#d35400", self._create_pause_resume_callback(task.id))
        button_layout.addWidget(pause_resume_button)

        retry_button = self._create_button("Retry", "#3498db", "#2980b9", self._create_retry_callback(task.id))
        retry_button.setVisible(False)
        button_layout.addWidget(retry_button)

        return button_layout

    def _create_button(self, text: str, bg_color: str, hover_color: str, on_click: Callable[[], None]) -> QPushButton:
        """Create and style a button with the given parameters."""
        button = QPushButton(text)
        button.clicked.connect(on_click)
        button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {bg_color};
                color: white;
                border: none;
                padding: 5px;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            """
        )
        return button

    def _create_mouse_press_event(self, task_id: str) -> Callable[[QMouseEvent], None]:
        """Create a mouse press event handler for a task widget."""

        def mouse_press_event(event: QMouseEvent) -> None:
            self.task_clicked.emit(task_id)

        return mouse_press_event

    def _create_cancel_callback(self, task_id: str) -> Callable[[], None]:
        """Create a callback function for cancelling a task."""

        def cancel_task() -> None:
            self.dispatcher.cancel_task(task_id)

        return cancel_task

    def _create_pause_resume_callback(self, task_id: str) -> Callable[[], None]:
        """Create a callback function for pausing or resuming a task."""

        def toggle_pause_resume() -> None:
            self._toggle_pause_resume(task_id)

        return toggle_pause_resume

    def _create_retry_callback(self, task_id: str) -> Callable[[], None]:
        """Create a callback function for retrying a task."""

        def retry_task() -> None:
            self._retry_task(task_id)

        return retry_task

    def _toggle_pause_resume(self, task_id: str) -> None:
        """Toggle the pause/resume state of a task."""
        task = self.dispatcher.get_task(task_id)
        if task is None:
            return
        if task.status == TaskStatus.RUNNING:
            self.dispatcher.pause_task(task_id)
        elif task.status == TaskStatus.PAUSED:
            self.dispatcher.resume_task(task_id)

    def _retry_task(self, task_id: str) -> None:
        """Retry a failed or cancelled task."""
        self.dispatcher.retry_task(task_id)

    def _update_task_widget(self, task: Task) -> None:
        """Update the UI of a task widget based on its current state."""
        task_widget = self.task_widgets.get(task.id)
        if task_widget is None:
            return

        status_label = task_widget.widget.findChild(QLabel, "status_label")
        if not isinstance(status_label, QLabel):
            raise TypeError("Expected QLabel for status_label")
        status_label.setText(task.status.name)

        cancel_button = task_widget.widget.findChild(QPushButton, "Cancel")
        pause_resume_button = task_widget.widget.findChild(QPushButton, "Pause")
        retry_button = task_widget.widget.findChild(QPushButton, "Retry")

        if not all(isinstance(button, QPushButton) for button in (cancel_button, pause_resume_button, retry_button)):
            raise TypeError("Expected QPushButton for all buttons")

        task_widget.progress_bar.setValue(int(task.progress * 100))

        if task.status == TaskStatus.COMPLETED:
            self._update_completed_task_widget(task_widget, status_label, cancel_button, pause_resume_button, retry_button)
        elif task.status == TaskStatus.FAILED:
            self._update_failed_task_widget(task_widget, status_label, cancel_button, pause_resume_button, retry_button)
        elif task.status == TaskStatus.CANCELLED:
            self._update_cancelled_task_widget(task_widget, status_label, cancel_button, pause_resume_button, retry_button)
        elif task.status == TaskStatus.PAUSED:
            self._update_paused_task_widget(task_widget, status_label, cancel_button, pause_resume_button, retry_button)
        else:  # PENDING or RUNNING
            self._update_active_task_widget(task_widget, status_label, cancel_button, pause_resume_button, retry_button)

    def _update_completed_task_widget(
        self, task_widget: TaskWidget, status_label: QLabel, cancel_button: QPushButton, pause_resume_button: QPushButton, retry_button: QPushButton
    ) -> None:
        """Update the UI for a completed task."""
        status_label.setStyleSheet("color: #27ae60;")
        cancel_button.setEnabled(False)
        pause_resume_button.setEnabled(False)
        retry_button.setVisible(False)
        task_widget.progress_bar.setStyleSheet(
            """
            QProgressBar::chunk {
                background-color: #27ae60;
            }
            """
        )

    def _update_failed_task_widget(
        self, task_widget: TaskWidget, status_label: QLabel, cancel_button: QPushButton, pause_resume_button: QPushButton, retry_button: QPushButton
    ) -> None:
        """Update the UI for a failed task."""
        status_label.setStyleSheet("color: #c0392b;")
        cancel_button.setVisible(False)
        pause_resume_button.setEnabled(False)
        retry_button.setVisible(True)
        task_widget.progress_bar.setStyleSheet(
            """
            QProgressBar::chunk {
                background-color: #e74c3c;
            }
            """
        )

    def _update_cancelled_task_widget(
        self, task_widget: TaskWidget, status_label: QLabel, cancel_button: QPushButton, pause_resume_button: QPushButton, retry_button: QPushButton
    ) -> None:
        """Update the UI for a cancelled task."""
        status_label.setStyleSheet("color: #f39c12;")
        cancel_button.setVisible(False)
        pause_resume_button.setEnabled(False)
        retry_button.setVisible(True)
        task_widget.progress_bar.setStyleSheet(
            """
            QProgressBar::chunk {
                background-color: #f39c12;
            }
            """
        )

    def _update_paused_task_widget(
        self, task_widget: TaskWidget, status_label: QLabel, cancel_button: QPushButton, pause_resume_button: QPushButton, retry_button: QPushButton
    ) -> None:
        """Update the UI for a paused task."""
        status_label.setStyleSheet("color: #3498db;")
        cancel_button.setEnabled(True)
        pause_resume_button.setText("Resume")
        retry_button.setVisible(False)
        task_widget.progress_bar.setStyleSheet(
            """
            QProgressBar::chunk {
                background-color: #3498db;
            }
            """
        )

    def _update_active_task_widget(
        self, task_widget: TaskWidget, status_label: QLabel, cancel_button: QPushButton, pause_resume_button: QPushButton, retry_button: QPushButton
    ) -> None:
        """Update the UI for an active (pending or running) task."""
        status_label.setStyleSheet("color: #2ecc71;")
        cancel_button.setEnabled(True)
        pause_resume_button.setText("Pause")
        pause_resume_button.setEnabled(True)
        retry_button.setVisible(False)
        task_widget.progress_bar.setStyleSheet(
            """
            QProgressBar::chunk {
                background-color: #2ecc71;
            }
            """
        )

    def clear_completed_tasks(self) -> None:
        """Remove all completed tasks from the widget."""
        for i in range(self.task_list.count() - 1, -1, -1):
            item = self.task_list.item(i)
            if item is None:
                continue
            widget = self.task_list.itemWidget(item)
            if not isinstance(widget, QWidget):
                continue
            task_id = widget.property("task_id")
            if not isinstance(task_id, str):
                continue
            task = self.dispatcher.get_task(task_id)
            if task is None or task.status == TaskStatus.COMPLETED:
                self.task_list.takeItem(i)
                del self.task_widgets[task_id]

    def update_all_tasks(self) -> None:
        """Update the status and progress of all tasks."""
        for task_id, task_widget in self.task_widgets.items():
            task = self.dispatcher.get_task(task_id)
            if task is not None:
                self.update_task_progress(task_id, task.progress)
                self.update_task_status(task_id)

    def _update_task_widget(self, task: Task) -> None:
        task_widget = self.task_widgets[task.id]
        status_label = task_widget.findChild(QLabel, "status_label")
        cancel_button = task_widget.findChild(QPushButton, "Cancel")
        pause_resume_button = task_widget.findChild(QPushButton, "Pause")
        retry_button = task_widget.findChild(QPushButton, "Retry")
        progress_bar = task_widget.findChild(QProgressBar)

        status_label.setText(task.status.name)
        progress_bar.setValue(int(task.progress * 100))

        if task.status == TaskStatus.COMPLETED:
            status_label.setStyleSheet("color: #27ae60;")
            cancel_button.setEnabled(False)
            pause_resume_button.setEnabled(False)
            retry_button.setVisible(False)
            progress_bar.setStyleSheet(
                """
                QProgressBar::chunk {
                    background-color: #27ae60;
                }
                """
            )
        elif task.status == TaskStatus.FAILED:
            status_label.setStyleSheet("color: #c0392b;")
            cancel_button.setVisible(False)
            pause_resume_button.setEnabled(False)
            retry_button.setVisible(True)
            progress_bar.setStyleSheet(
                """
                QProgressBar::chunk {
                    background-color: #e74c3c;
                }
                """
            )
        elif task.status == TaskStatus.CANCELLED:
            status_label.setStyleSheet("color: #f39c12;")
            cancel_button.setVisible(False)
            pause_resume_button.setEnabled(False)
            retry_button.setVisible(True)
            progress_bar.setStyleSheet(
                """
                QProgressBar::chunk {
                    background-color: #f39c12;
                }
                """
            )
        elif task.status == TaskStatus.PAUSED:
            status_label.setStyleSheet("color: #3498db;")
            cancel_button.setEnabled(True)
            pause_resume_button.setText("Resume")
            retry_button.setVisible(False)
            progress_bar.setStyleSheet(
                """
                QProgressBar::chunk {
                    background-color: #3498db;
                }
                """
            )
        else:  # PENDING or RUNNING
            status_label.setStyleSheet("color: #2ecc71;")
            cancel_button.setEnabled(True)
            pause_resume_button.setText("Pause")
            pause_resume_button.setEnabled(True)
            retry_button.setVisible(False)
            progress_bar.setStyleSheet(
                """
                QProgressBar::chunk {
                    background-color: #2ecc71;
                }
                """
            )

    def _toggle_pause_resume(self, task_id: str):
        task = self.dispatcher.get_task(task_id)
        if task:
            if task.status == TaskStatus.RUNNING:
                self.dispatcher.pause_task(task_id)
            elif task.status == TaskStatus.PAUSED:
                self.dispatcher.resume_task(task_id)

    def _retry_task(self, task_id: str) -> None:
        self.dispatcher.retry_task(task_id)
        self.update_task_status(task_id)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        super().mousePressEvent(event)
        self.task_clicked.emit("")  # Emit signal to show task details dialog

    def remove_task(self, task_id: str) -> None:
        if task_id in self.task_widgets:
            widget = self.task_widgets[task_id]
            for i in range(self.task_list.count()):
                item = self.task_list.item(i)
                if self.task_list.itemWidget(item) == widget:
                    self.task_list.takeItem(i)
                    break
            del self.task_widgets[task_id]

    def clear_completed_tasks(self) -> None:
        completed_tasks = [task_id for task_id, task in self.dispatcher.get_all_tasks() if task.status == TaskStatus.COMPLETED]
        for task_id in completed_tasks:
            self.remove_task(task_id)

    def update_all_tasks(self) -> None:
        for task_id, task in self.dispatcher.get_all_tasks():
            self.update_task_progress(task_id, task.progress)
            self.update_task_status(task_id)

if __name__ == "__main__":
    import sys

    from qtpy.QtWidgets import QApplication

    from utility.ui_libraries.qt.filesystem.file_browser.file_system_executor import FileActionsExecutor

    app = QApplication(sys.argv)

    # Create a mock FileActionsExecutor for testing
    mock_executor = FileActionsExecutor()

    # Create the TaskStatusWidget
    task_status_widget = TaskStatusWidget(mock_executor)
    task_status_widget.show()

    # Add some mock tasks for testing
    mock_executor.TaskStarted.emit("task1")
    mock_executor.TaskProgress.emit("task1", 0.5)
    mock_executor.TaskStarted.emit("task2")
    mock_executor.TaskProgress.emit("task2", 0.3)
    mock_executor.TaskCompleted.emit("task1", None)  # Pass None as the second argument for no error

    sys.exit(app.exec())
