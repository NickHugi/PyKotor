from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from qtpy.QtCore import QTimer
from qtpy.QtWidgets import QDialog, QFormLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout

from utility.ui_libraries.qt.common.tasks.actions_executor import TaskStatus

if TYPE_CHECKING:
    from qtpy.QtGui import QCloseEvent
    from qtpy.QtWidgets import QWidget

    from utility.ui_libraries.qt.common.tasks.actions_executor import FileActionsExecutor


class TaskDetailsDialog(QDialog):
    """Dialog to display and manage task details."""

    def __init__(
        self,
        file_actions_executor: FileActionsExecutor,
        task_id: str,
        parent: QWidget | None = None,
    ):
        """Initialize the TaskDetailsDialog."""
        super().__init__(parent)
        self.file_actions_executor: FileActionsExecutor = file_actions_executor
        self.task_id: str = task_id
        self.task_details: dict[str, Any] | None = self.file_actions_executor.get_task_details(self.task_id)
        self.setup_ui()

    def setup_ui(self) -> None:
        """Set up the user interface for the dialog."""
        layout = QVBoxLayout(self)

        if self.task_details is not None:
            self._setup_task_details(layout)
        else:
            self._setup_error_message(layout)

        self.setLayout(layout)
        self.setWindowTitle(f"Task Details - {self.task_details['operation'] if self.task_details else 'Unknown'}")
        self.resize(500, 300)

        self._setup_update_timer()

    def _setup_task_details(self, layout: QVBoxLayout) -> None:
        """Set up the UI components for displaying task details."""
        details_layout = QFormLayout()
        self._add_task_info_to_layout(details_layout)
        layout.addLayout(details_layout)

        button_layout = self._create_button_layout()
        layout.addLayout(button_layout)

    def _add_task_info_to_layout(self, layout: QFormLayout) -> None:
        """Add task information to the given layout."""
        if self.task_details is None:
            return

        layout.addRow("Task ID:", QLabel(self.task_details["id"]))
        layout.addRow("Operation:", QLabel(self.task_details["operation"]))
        layout.addRow("Description:", QLabel(self.task_details["description"]))
        self.status_label = QLabel(self.task_details["status"])
        layout.addRow("Status:", self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(int(self.task_details["progress"] * 100))
        layout.addRow("Progress:", self.progress_bar)

        layout.addRow("Priority:", QLabel(str(self.task_details["priority"])))

        if self.task_details["start_time"]:
            layout.addRow("Start Time:", QLabel(self.task_details["start_time"]))
        if self.task_details["end_time"]:
            layout.addRow("End Time:", QLabel(self.task_details["end_time"]))

        if self.task_details["error"]:
            error_label = QLabel(self.task_details["error"])
            error_label.setWordWrap(True)
            layout.addRow("Error:", error_label)

        if self.task_details["result"] is not None:
            result_label = QLabel(self.task_details["result"])
            result_label.setWordWrap(True)
            layout.addRow("Result:", result_label)

    def _create_button_layout(self) -> QHBoxLayout:
        """Create and return a layout with control buttons."""
        button_layout = QHBoxLayout()

        self.retry_button = self._create_button("Retry", self.retry_task)
        self.cancel_button = self._create_button("Cancel", self.cancel_task)
        self.pause_resume_button = self._create_button("Pause", self.pause_resume_task)

        button_layout.addWidget(self.retry_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.pause_resume_button)

        self._update_button_states()

        return button_layout

    def _create_button(self, text: str, slot: Callable[[], None]) -> QPushButton:
        """Create and return a button with the given text and connected slot."""
        button = QPushButton(text)
        button.clicked.connect(slot)
        return button

    def _update_button_states(self) -> None:
        """Update the enabled state of buttons based on task status."""
        if self.task_details is None:
            return

        self.retry_button.setEnabled(self.task_details["status"] in (TaskStatus.FAILED.name, TaskStatus.CANCELLED.name))
        self.cancel_button.setEnabled(self.task_details["status"] == TaskStatus.RUNNING.name)
        self.pause_resume_button.setEnabled(self.task_details["status"] in (TaskStatus.RUNNING.name, TaskStatus.PAUSED.name))

        if self.task_details["status"] == TaskStatus.PAUSED.name:
            self.pause_resume_button.setText("Resume")
        else:
            self.pause_resume_button.setText("Pause")

    def _setup_error_message(self, layout: QVBoxLayout) -> None:
        """Set up an error message when task details are not found."""
        error_label = QLabel("Task not found")
        layout.addWidget(error_label)

    def _setup_update_timer(self) -> None:
        """Set up a timer to periodically update task details."""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_task_details)
        self.update_timer.start(1000)  # Update every second

    def update_task_details(self) -> None:
        """Update the displayed task details."""
        self.task_details = self.file_actions_executor.get_task_details(self.task_id)
        if self.task_details is not None:
            self.status_label.setText(self.task_details["status"])
            self.progress_bar.setValue(int(self.task_details["progress"] * 100))
            self._update_button_states()

    def retry_task(self) -> None:
        """Retry the current task."""
        self.file_actions_executor.retry_task(self.task_id)
        self.accept()

    def cancel_task(self) -> None:
        """Cancel the current task."""
        self.file_actions_executor.cancel_task(self.task_id)
        self.accept()

    def pause_resume_task(self) -> None:
        """Pause or resume the current task."""
        if self.task_details is None:
            return

        if self.task_details["status"] == TaskStatus.RUNNING.name:
            self.file_actions_executor.pause_task(self.task_id)
        elif self.task_details["status"] == TaskStatus.PAUSED.name:
            self.file_actions_executor.resume_task(self.task_id)
        self.update_task_details()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle the dialog close event."""
        self.update_timer.stop()
        super().closeEvent(event)


if __name__ == "__main__":
    import sys

    from qtpy.QtWidgets import QApplication

    from utility.ui_libraries.qt.common.tasks.actions_executor import FileActionsExecutor, TaskStatus

    class MockFileActionsExecutor(FileActionsExecutor):
        def __init__(self):
            super().__init__()
            self.mock_task: dict[str, Any] = {
                "id": "task1",
                "operation": "Copy",
                "description": "Copying file.txt to destination",
                "status": TaskStatus.RUNNING.name,
                "progress": 0.5,
                "priority": 1,
                "start_time": "2023-09-29 10:00:00",
                "end_time": None,
                "error": None,
                "result": None,
            }

        def get_task_details(self, task_id: str) -> dict[str, Any]:
            return self.mock_task

        def retry_task(self, task_id: str) -> None:
            self.mock_task["status"] = TaskStatus.RUNNING.name

        def cancel_task(self, task_id: str) -> None:
            self.mock_task["status"] = TaskStatus.CANCELLED.name

        def pause_task(self, task_id: str) -> None:
            self.mock_task["status"] = TaskStatus.PAUSED.name

        def resume_task(self, task_id: str) -> None:
            self.mock_task["status"] = TaskStatus.RUNNING.name

    app = QApplication(sys.argv)
    mock_executor = MockFileActionsExecutor()
    dialog = TaskDetailsDialog(mock_executor, "task1")
    dialog.show()
    sys.exit(app.exec())
