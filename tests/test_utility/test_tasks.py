from __future__ import annotations

import sys
import unittest

import pytest

from concurrent.futures import Future
from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

from qtpy.QtWidgets import QApplication
from typing_extensions import Literal

from utility.ui_libraries.qt.common.tasks.actions_executor import FileActionsExecutor, Task, TaskStatus

if TYPE_CHECKING:
    from multiprocessing import Queue
    from multiprocessing.managers import ValueProxy

    from utility.ui_libraries.qt.common.tasks.actions_executor import Task, TaskDetails


class TestFileActionsExecutor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app: QApplication = QApplication(sys.argv)

    @classmethod
    def tearDownClass(cls):
        cls.app.quit()

    def setUp(self):
        self.executor: FileActionsExecutor = FileActionsExecutor()

    def test_queue_task_with_custom_function(self):
        def custom_func(x: int, y: int) -> int:
            return x + y

        custom_func_result: int = 3
        task_id: str = self.executor.queue_task("custom_operation", args=(1, 2), custom_function=custom_func)
        future: Future[int] = self.executor.futures[task_id]
        result: int = future.result()
        assert result == custom_func_result, f"{result} == {custom_func_result}"
        task: Task | None = self.executor.get_task(task_id)
        assert task is not None, f"Task {task_id} not found"
        assert task.operation == "custom_operation", f"{task.operation} == custom_operation"
        assert task.status == TaskStatus.COMPLETED, f"{task.status} == {TaskStatus.COMPLETED}"
        assert task.result == custom_func_result, f"{task.result} != {custom_func_result}"
        assert task.start_time is not None, f"{task.start_time} is not None"
        assert task.end_time is not None, f"{task.end_time} is not None"
        assert task.progress == 0.0, f"{task.progress} is not 0.0"
        assert task.priority == 0, f"{task.priority} is not 0"
        assert task.description == "", f"{task.description} is not ''"
        assert task.error is None, f"{task.error} is not None"

    def test_cancel_task(self):
        task_id: str = self.executor.queue_task("operation")
        self.executor.cancel_task(task_id)
        task: Task | None = self.executor.get_task(task_id)
        assert task is not None, f"Task {task_id} not found"
        assert task.status == TaskStatus.CANCELLED, f"{task.status} == {TaskStatus.CANCELLED}"

    def test_pause_resume_task(self):
        task_id: str = self.executor.queue_task("operation")
        task: Task | None = self.executor.get_task(task_id)
        assert task is not None, f"{task} is not None"
        task.status = TaskStatus.RUNNING
        self.executor.tasks[task_id] = task  # Update the task in the shared dictionary
        self.executor.pause_task(task_id)
        get_task_test1: Task | None = self.executor.get_task(task_id)
        assert get_task_test1 is not None, f"{get_task_test1} is not None"
        assert get_task_test1.status == TaskStatus.PAUSED, f"{get_task_test1.status} == {TaskStatus.PAUSED}"
        self.executor.resume_task(task_id)
        get_task_test2: Task | None = self.executor.get_task(task_id)
        assert get_task_test2 is not None, "get_task_test2 is not None"
        assert get_task_test2.status == TaskStatus.RUNNING, f"{get_task_test2.status} == {TaskStatus.RUNNING}"

    def test_retry_task(self):
        task_id: str = self.executor.queue_task("operation")
        task: Task | None = self.executor.get_task(task_id)
        assert task is not None, f"{task} is not None"
        task.status = TaskStatus.FAILED
        self.executor.tasks[task_id] = task  # Update the task in the shared dictionary
        new_task_id: str | None = self.executor.retry_task(task_id)
        assert new_task_id is not None, "new_task_id is not None"
        assert task_id != new_task_id, "task_id != new_task_id"
        assert task_id not in self.executor.tasks, "task_id not in self.executor.tasks"
        assert new_task_id in self.executor.tasks, "new_task_id not in self.executor.tasks"

    def test_get_task_details(self):
        task_id: str = self.executor.queue_task("operation")
        details: TaskDetails | None = self.executor.get_task_details(task_id)
        assert details is not None, f"{details} is not None"
        assert details.id == task_id, f"{details.id} == {task_id}"
        assert details.operation == "operation", f"{details.operation} == operation"

    @patch("FileActionsExecutor.Future")
    def test_task_completed(
        self,
        mock_future: Mock,
    ):
        task_id: str = self.executor.queue_task("operation")
        future: Mock = Mock(spec=Future)
        future.cancelled.return_value = False
        future.exception.return_value = None
        future.result.return_value = "result"
        self.executor._task_completed(task_id, future)  # noqa: SLF001
        task: Task | None = self.executor.get_task(task_id)
        assert task is not None, f"{task} is not None"
        assert task.status == TaskStatus.COMPLETED, f"{task.status} == {TaskStatus.COMPLETED}"
        assert task.result == "result", f"{task.result} == result"

    def test_queue_task(self):
        task_id: str = self.executor.queue_task("operation")
        assert task_id in self.executor.tasks, f"{task_id} not in self.executor.tasks"
        assert task_id in self.executor.futures, f"{task_id} not in self.executor.futures"

    def test_get_task(self):
        task_id: str = self.executor.queue_task("operation")
        task: Task | None = self.executor.get_task(task_id)
        assert task is not None, f"{task} is not None"
        assert task.operation == "operation", f"{task.operation} == operation"

    def test_update_task_progress(self):
        task_id: str = self.executor.queue_task("operation")
        expected_progress = 0.5
        self.executor.update_task_progress(task_id, expected_progress)
        task: Task | None = self.executor.get_task(task_id)
        assert task is not None, f"{task} is not None"
        assert task.progress == expected_progress, f"{task.progress} == {expected_progress}"

    def test_cleanup_tasks(self):
        task_id: str = self.executor.queue_task("operation")
        task: Task | None = self.executor.get_task(task_id)
        assert task is not None, f"{task} is not None"
        task.end_time = datetime.now().astimezone() - timedelta(days=2)
        self.executor.tasks[task_id] = task  # Update the task in the shared dictionary
        self.executor.cleanup_tasks(timedelta(days=1))
        assert task_id not in self.executor.tasks, f"{task_id} not in self.executor.tasks"

    def test_custom_function(self):
        def custom_func(x: int, y: int) -> int:
            return x + y

        custom_func_result = 3
        task_id: str = self.executor.queue_task("custom_operation", args=(1, 2), custom_function=custom_func)
        future: Future[int] = self.executor.futures[task_id]
        result: int = future.result()
        assert result == custom_func_result, f"{result} == {custom_func_result}"

    def test_pickleable_task(self):
        import pickle

        task_id: str = self.executor.queue_task("operation")
        task: Task | None = self.executor.get_task(task_id)
        assert task is not None, f"{task} is not None"
        pickled_task: bytes = pickle.dumps(task)
        unpickled_task: Task | None = pickle.loads(pickled_task)  # noqa: S301
        assert unpickled_task is not None, f"{unpickled_task} is not None"
        assert unpickled_task.id == task.id, f"{unpickled_task.id} == {task.id}"
        assert task.id == unpickled_task.id, f"{task.id} == {unpickled_task.id}"
        assert task.operation == unpickled_task.operation, f"{task.operation} == {unpickled_task.operation}"

    def test_task_status(self):
        task_id: str = self.executor.queue_task("operation")
        task: Task | None = self.executor.get_task(task_id)
        assert task is not None, f"{task} is not None"
        assert task.status == TaskStatus.RUNNING, f"{task.status} == {TaskStatus.RUNNING}"
        self.executor.cancel_task(task_id)
        task: Task | None = self.executor.get_task(task_id)
        assert task is not None, f"{task} is not None"
        assert task.status == TaskStatus.CANCELLED, f"{task.status} == {TaskStatus.CANCELLED}"

    def test_task_result(self):
        def custom_func(x: int, y: int) -> int:
            return x * y

        custom_func_result = 12
        task_id: str = self.executor.queue_task("custom_operation", args=(3, 4), custom_function=custom_func)
        future: Future[int] = self.executor.futures[task_id]
        result: int = future.result()
        assert result == custom_func_result, f"{result} == {custom_func_result}"

    def test_task_error(self):
        def custom_func(_x: int, _y: int) -> int:
            raise ValueError("Test error")

        task_id: str = self.executor.queue_task("custom_operation", args=(1, 2), custom_function=custom_func)
        future: Future[int] = self.executor.futures[task_id]
        with pytest.raises(ValueError):
            future.result()

    def test_task_progress(self):
        def custom_func(progress_queue: Queue, *args, **kwargs) -> Literal["done"]:
            for i in range(5):
                progress_queue.put(i * 20)
            return "done"

        progress_expected = 80
        task_id: str = self.executor.queue_task("custom_operation", custom_function=custom_func)
        future: Future[int] = self.executor.futures[task_id]
        result: int = future.result()
        assert result == "done", f"{result} == done"
        task: Task | None = self.executor.get_task(task_id)
        assert task is not None, f"{task} is not None"
        assert task.progress == progress_expected, f"{task.progress} == {progress_expected}"

    def test_task_priority(self):
        task_id1: str = self.executor.queue_task("operation1", priority=1)
        task_id2: str = self.executor.queue_task("operation2", priority=2)
        task1: Task | None = self.executor.get_task(task_id1)
        task2: Task | None = self.executor.get_task(task_id2)
        assert task1 is not None, f"{task1} is not None"
        assert task2 is not None, f"{task2} is not None"
        assert task1.priority == 1, f"{task1.priority} == 1"
        assert task2.priority == 2, f"{task2.priority} == 2"  # noqa: PLR2004

    def test_task_description(self):
        task_id: str = self.executor.queue_task("operation", description="Test task")
        task: Task | None = self.executor.get_task(task_id)
        assert task is not None, f"{task} is not None"
        assert task.description == "Test task", f"{task.description} == Test task"

    def test_task_start_time(self):
        task_id: str = self.executor.queue_task("operation")
        task: Task | None = self.executor.get_task(task_id)
        assert task is not None, f"{task} is not None"
        assert task.start_time is not None, f"{task.start_time} is not None"

    def test_task_end_time(self):
        task_id: str = self.executor.queue_task("operation")
        future: Future[int] = self.executor.futures[task_id]
        future.result()
        task: Task | None = self.executor.get_task(task_id)
        assert task is not None, f"{task} is not None"
        assert task.end_time is not None, f"{task.end_time} is not None"

    def test_task_kwargs(self):
        def custom_func(a: int, b: int, c: int = 0) -> int:
            return a + b + c

        custom_func_result = 6
        task_id: str = self.executor.queue_task(
            "custom_operation",
            args=(1, 2),
            kwargs={"c": 3},
            custom_function=custom_func,
        )
        future: Future[int] = self.executor.futures[task_id]
        result: int = future.result()
        assert result == custom_func_result, f"{result} == {custom_func_result}"

    def test_task_pause_flag(self):
        def custom_func(pause_flag: ValueProxy, *args, **kwargs) -> Literal["paused"]:
            while not pause_flag.value:
                pass
            return "paused"

        task_id: str = self.executor.queue_task("custom_operation", custom_function=custom_func)
        self.executor.pause_task(task_id)
        future: Future[int] = self.executor.futures[task_id]
        result: int = future.result()
        assert result == "paused", f"{result} == paused"

    def test_task_cancel_flag(self):
        def custom_func(
            cancel_flag: ValueProxy,
            *args,
            **kwargs,
        ) -> Literal["cancelled"]:  # noqa: ANN001
            while not cancel_flag.value:
                pass
            return "cancelled"

        task_id: str = self.executor.queue_task("custom_operation", custom_function=custom_func)
        self.executor.cancel_task(task_id)
        future: Future[int] = self.executor.futures[task_id]
        result: int = future.result()
        assert result == "cancelled", f"{result} == cancelled"

    def test_task_retry(self):
        def custom_func(x: int, y: int) -> int:
            return x - y

        custom_func_result = 2
        task_id: str = self.executor.queue_task("custom_operation", args=(5, 3), custom_function=custom_func)
        future: Future[int] = self.executor.futures[task_id]
        result: int = future.result()
        assert result == custom_func_result, f"{result} == {custom_func_result}"

        task: Task | None = self.executor.get_task(task_id)
        assert task is not None, f"{task} is not None"
        task.status = TaskStatus.FAILED
        self.executor.tasks[task_id] = task  # Update the task in the shared dictionary
        new_task_id: str | None = self.executor.retry_task(task_id)
        assert new_task_id is not None, "new_task_id is not None"
        assert task_id != new_task_id, "task_id != new_task_id"
        assert task_id not in self.executor.tasks, "task_id not in self.executor.tasks"
        assert new_task_id in self.executor.tasks, "new_task_id not in self.executor.tasks"
        new_future: Future[int] = self.executor.futures[new_task_id]
        new_result: int = new_future.result()
        assert new_result == custom_func_result, f"{new_result} == {custom_func_result}"


if __name__ == "__main__":
    try:
        import pytest
    except ImportError:  # pragma: no cover
        unittest.main(
            argv=sys.argv,
            verbosity=2,
            catchbreak=True,
            testLoader=unittest.TestLoader(),
            testRunner=unittest.TextTestRunner(),
        )
    else:
        pytest.main(["-v", __file__])
