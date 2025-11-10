from __future__ import annotations

import inspect
import multiprocessing
import pickle
import queue
import threading
import uuid

from concurrent.futures import (
    Future as _ConcurrentFuture,
    ProcessPoolExecutor,
    ThreadPoolExecutor,
)
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from multiprocessing import Manager
from multiprocessing.managers import RemoteError, ValueProxy
from typing import Any, Callable, ClassVar, cast

import qtpy
import sys

Future = _ConcurrentFuture
sys.modules.setdefault("FileActionsExecutor", sys.modules[__name__])
CONTROL_KEYWORDS: set[str] = {"progress_queue", "pause_flag", "cancel_flag"}

from loggerplus import RobustLogger
from qtpy.QtCore import (
    QObject,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
)

from utility.ui_libraries.qt.common.expensive_functions import FileOperations

if qtpy.QT5:
    pass
else:
    pass

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from concurrent.futures import Future
    from multiprocessing import Queue
    from multiprocessing.managers import DictProxy, SyncManager


class TaskStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    PAUSED = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


@dataclass
class Task:
    id: str
    operation: str
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    priority: int = 0
    start_time: datetime | None = None
    end_time: datetime | None = None
    result: Any = None
    error: str | None = None
    description: str = ""


@dataclass
class TaskDetails:
    id: str
    operation: str
    status: str
    progress: float
    priority: int
    start_time: str | None
    end_time: str | None
    description: str
    error: str | None
    result: str | None


class FileActionsExecutor(QObject):
    TaskStarted: ClassVar[Signal] = Signal(str)
    TaskCompleted: ClassVar[Signal] = Signal(str, object)
    TaskFailed: ClassVar[Signal] = Signal(str, Exception)
    TaskCancelled: ClassVar[Signal] = Signal(str)
    TaskPaused: ClassVar[Signal] = Signal(str)
    TaskResumed: ClassVar[Signal] = Signal(str)
    TaskProgress: ClassVar[Signal] = Signal(str, float)
    AllTasksCompleted: ClassVar[Signal] = Signal()
    ProgressUpdated: ClassVar[Signal] = Signal(int, int)

    def __init__(
        self,
        max_workers: int = multiprocessing.cpu_count(),
        max_queue_size: int = 100,
        max_age: timedelta = timedelta(days=1),
        default_priority: int = 0,
    ):
        super().__init__()
        worker_count: int = max_workers or multiprocessing.cpu_count()
        RobustLogger().debug(f"Initializing FileActionsExecutor with max_workers: {worker_count}")
        self.process_pool: ProcessPoolExecutor = ProcessPoolExecutor(max_workers=worker_count)
        self.thread_pool: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=worker_count)
        self.manager: SyncManager = Manager()
        self.tasks: DictProxy[str, Task] = self.manager.dict()
        self.futures: dict[str, Future] = {}
        RobustLogger().debug("FileActionsExecutor initialized")

    @property
    def completed_tasks(self) -> int:
        completed: int = sum(
            task.status
            in (
                TaskStatus.COMPLETED,
                TaskStatus.FAILED,
                TaskStatus.CANCELLED,
            )
            for task in self.tasks.values()
        )
        return completed

    @property
    def total_tasks(self) -> int:
        total: int = len(self.tasks)
        RobustLogger().debug(f"Total tasks: {total}")
        return total

    def queue_task(
        self,
        operation: str,
        args: tuple[Any, ...] = (),
        kwargs: dict[str, Any] | None = None,
        priority: int = 0,
        description: str = "",
        custom_function: Callable[..., Any] | None = None,
    ) -> str:
        task_id = str(uuid.uuid4())
        RobustLogger().debug(f"Queueing task: {task_id}, operation: {operation}")
        base_kwargs = dict(kwargs or {})
        for runtime_key in CONTROL_KEYWORDS:
            base_kwargs.pop(runtime_key, None)

        progress_queue: Queue[Any] = self.manager.Queue()
        pause_flag: ValueProxy[bool] = self.manager.Value("b", False)  # noqa: FBT003
        cancel_flag: ValueProxy[bool] = self.manager.Value("b", False)  # noqa: FBT003

        task_kwargs: dict[str, Any] = {
            **base_kwargs,
            "progress_queue": progress_queue,
            "pause_flag": pause_flag,
            "cancel_flag": cancel_flag,
        }

        task = Task(
            id=task_id,
            operation=operation,
            args=args,
            kwargs=task_kwargs,
            priority=priority,
            description=description,
        )
        task.start_time = datetime.now().astimezone()
        task.status = TaskStatus.RUNNING
        self.tasks[task_id] = task

        submitter = self.process_pool.submit
        if custom_function is not None and not self._is_picklable(custom_function):
            RobustLogger().debug(
                f"Task {task_id} custom function is not picklable; using thread pool execution"
            )
            submitter = self.thread_pool.submit

        future: Future[Any] = submitter(
            self._execute_task,
            operation,
            custom_function,
            *args,
            **task_kwargs,
        )
        self.futures[task_id] = future
        future.add_done_callback(lambda f: self._task_completed(task_id, f))
        self.TaskStarted.emit(task_id)
        self._update_progress()

        threading.Thread(target=self._monitor_progress, args=(task_id, progress_queue), daemon=True).start()

        RobustLogger().debug(f"Task queued: {task_id}, operation: {operation}")
        return task_id

    @staticmethod
    def _execute_task(
        operation: str,
        custom_function: Callable[..., Any] | None,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        RobustLogger().debug(f"Executing task: operation={operation}, args={args}, kwargs={kwargs}")
        if custom_function:
            filtered_kwargs = FileActionsExecutor._filter_control_kwargs(custom_function, kwargs)
            return custom_function(*args, **filtered_kwargs)
        func: FileOperations | None = getattr(FileOperations, operation, None)
        if not func:
            RobustLogger().debug(f"No FileOperations handler found for '{operation}', completing without action")
            progress_queue = kwargs.get("progress_queue")
            if progress_queue:
                try:
                    progress_queue.put(100)
                except Exception:  # noqa: BLE001
                    pass
            return None
        if hasattr(func, "handle_operation"):
            return func(*args, **kwargs)
        if hasattr(func, "handle_multiple"):
            paths: list[str] = args[0] if args else kwargs.get("paths", [])
            return func(paths, **kwargs)
        return func(*args, **kwargs)

    @staticmethod
    def _is_picklable(obj: Any) -> bool:
        try:
            pickle.dumps(obj)
        except Exception:  # noqa: BLE001
            return False
        return True

    @staticmethod
    def _filter_control_kwargs(
        func: Callable[..., Any],
        kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        if not kwargs:
            return {}
        try:
            signature = inspect.signature(func)
        except (TypeError, ValueError):
            return kwargs
        accepts_var_kw: bool = any(
            parameter.kind == inspect.Parameter.VAR_KEYWORD for parameter in signature.parameters.values()
        )
        if accepts_var_kw:
            return kwargs
        allowed_keys = set(signature.parameters.keys())
        filtered_kwargs: dict[str, Any] = {}
        for key, value in kwargs.items():
            if key in CONTROL_KEYWORDS and key not in allowed_keys:
                continue
            filtered_kwargs[key] = value
        return filtered_kwargs

    def _monitor_progress(
        self,
        task_id: str,
        progress_queue: Queue[int],
    ) -> None:
        while True:
            try:
                progress: int = progress_queue.get(timeout=1)
                self.update_task_progress(task_id, progress)
            except queue.Empty:  # noqa: PERF203
                try:
                    task = self.get_task(task_id)
                except (RemoteError, EOFError, KeyError):  # noqa: PERF203
                    break
                if task and task.status in (
                    TaskStatus.COMPLETED,
                    TaskStatus.FAILED,
                    TaskStatus.CANCELLED,
                ):
                    break
            except (RemoteError, EOFError, BrokenPipeError):
                break

    def get_task(
        self,
        task_id: str,
    ) -> Task | None:
        task: Task | None = self.tasks.get(task_id)
        RobustLogger().debug(f"Getting task: {task_id}, result: {task}")
        return task

    def cancel_task(
        self,
        task_id: str,
    ) -> None:
        RobustLogger().debug(f"Attempting to cancel task: {task_id}")
        task: Task | None = self.get_task(task_id)
        if task and task.status in (TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.PAUSED):
            task.kwargs["cancel_flag"].value = True
            self.futures[task_id].cancel()
            task.status = TaskStatus.CANCELLED
            self.tasks[task_id] = task  # Update the task in the shared dictionary
            self.TaskCancelled.emit(task_id)
            self._update_progress()
            RobustLogger().debug(f"Task cancelled: {task_id}")
        else:
            RobustLogger().debug(f"Unable to cancel task: {task_id}")

    def pause_task(
        self,
        task_id: str,
    ) -> None:
        RobustLogger().debug(f"Attempting to pause task: {task_id}")
        task: Task | None = self.get_task(task_id)
        if task and task.status == TaskStatus.RUNNING:
            cast(ValueProxy, task.kwargs["pause_flag"]).value = True
            task.status = TaskStatus.PAUSED
            self.tasks[task_id] = task  # Update the task in the shared dictionary
            self.TaskPaused.emit(task_id)
            RobustLogger().debug(f"Task paused: {task_id}")
        else:
            RobustLogger().debug(f"Unable to pause task: {task_id}")

    def resume_task(
        self,
        task_id: str,
    ) -> None:
        RobustLogger().debug(f"Attempting to resume task: {task_id}")
        task: Task | None = self.get_task(task_id)
        if task and task.status == TaskStatus.PAUSED:
            cast(ValueProxy, task.kwargs["pause_flag"]).value = False
            task.status = TaskStatus.RUNNING
            self.tasks[task_id] = task  # Update the task in the shared dictionary
            self.TaskResumed.emit(task_id)
            RobustLogger().debug(f"Task resumed: {task_id}")
        else:
            RobustLogger().debug(f"Unable to resume task: {task_id}")

    def retry_task(
        self,
        task_id: str,
    ) -> str | None:
        RobustLogger().debug(f"Attempting to retry task: {task_id}")
        task: Task | None = self.get_task(task_id)
        if task and task.status in (TaskStatus.FAILED, TaskStatus.CANCELLED):
            new_task_id: str = self.queue_task(task.operation, task.args, task.kwargs, task.priority, task.description)
            del self.tasks[task_id]
            self.futures.pop(task_id, None)
            RobustLogger().debug(f"Task retried: {task_id}, new task id: {new_task_id}")
            return new_task_id
        RobustLogger().debug(f"Unable to retry task: {task_id}")
        return None

    def _update_progress(self):
        completed: int = self.completed_tasks
        total: int = self.total_tasks
        RobustLogger().debug(f"Updating progress: {completed}/{total}")
        RobustLogger().debug(f"Task statuses: {[task.status.name for task in self.tasks.values()]}")
        self.ProgressUpdated.emit(completed, total)

    def get_all_tasks(self) -> list[tuple[str, Task]]:
        tasks = list(self.tasks.items())
        RobustLogger().debug(f"Getting all tasks, count: {len(tasks)}")
        return tasks

    def update_task_progress(
        self,
        task_id: str,
        progress: float,
    ) -> None:
        RobustLogger().debug(f"Updating task progress: {task_id}, progress: {progress}")
        task: Task | None = self.get_task(task_id)
        if task:
            task.progress = progress
            self.tasks[task_id] = task  # Update the task in the shared dictionary
            self.TaskProgress.emit(task_id, progress)
        else:
            RobustLogger().debug(f"Task not found for progress update: {task_id}")

    def cleanup_tasks(
        self,
        max_age: timedelta = timedelta(days=1),
    ) -> None:
        RobustLogger().debug(f"Cleaning up tasks older than {max_age}")
        current_time: datetime = datetime.now().astimezone()
        for task_id, task in list(self.tasks.items()):
            if not task.end_time:
                continue
            if (current_time - task.end_time) <= max_age:
                continue
            del self.tasks[task_id]
            self.futures.pop(task_id, None)
            RobustLogger().debug(f"Removed old task: {task_id}")
        self._update_progress()

    def get_task_details(
        self,
        task_id: str,
    ) -> TaskDetails | None:
        RobustLogger().debug(f"Getting task details for: {task_id}")
        task: Task | None = self.get_task(task_id)
        if not task:
            return None
        details: TaskDetails = TaskDetails(
            id=task.id,
            operation=task.operation,
            status=task.status.name,
            progress=task.progress,
            priority=task.priority,
            start_time=task.start_time.isoformat() if task.start_time else None,
            end_time=task.end_time.isoformat() if task.end_time else None,
            description=task.description,
            error=task.error,
            result=str(task.result) if task.result is not None else None,
        )
        RobustLogger().debug(f"Task details retrieved: {details}")
        return details

    def _task_completed(
        self,
        task_id: str,
        future: Future,
    ) -> None:
        RobustLogger().debug(f"Task completed callback for: {task_id}")
        task: Task | None = self.get_task(task_id)
        if task:
            task.end_time = datetime.now().astimezone()
            if task.status == TaskStatus.CANCELLED:
                if not future.cancelled():
                    try:
                        task.result = future.result()
                    except Exception as exc:  # noqa: BLE001
                        task.error = str(exc)
                self.tasks[task_id] = task
                self._update_progress()
                if self.completed_tasks == self.total_tasks:
                    self.AllTasksCompleted.emit()
                    RobustLogger().debug("All tasks completed")
                return
            if future.cancelled():
                task.status = TaskStatus.CANCELLED
                self.TaskCancelled.emit(task_id)
                RobustLogger().debug(f"Task cancelled: {task_id}")
            elif future.exception():
                task.status = TaskStatus.FAILED
                task.error = str(future.exception())
                self.TaskFailed.emit(task_id, future.exception())
                RobustLogger().debug(f"Task failed: {task_id}, error: {task.error}")
            else:
                task.status = TaskStatus.COMPLETED
                task.result = future.result()
                self.TaskCompleted.emit(task_id, task.result)
                RobustLogger().debug(f"Task completed successfully: {task_id}, result: {task.result}")
            self.tasks[task_id] = task
            self._update_progress()
            if self.completed_tasks == self.total_tasks:
                self.AllTasksCompleted.emit()
                RobustLogger().debug("All tasks completed")
        else:
            RobustLogger().debug(f"Task not found for completion: {task_id}")

    def __del__(self):
        RobustLogger().debug("Shutting down FileActionsExecutor")
        try:
            self.process_pool.shutdown(wait=True)
        except Exception:  # noqa: BLE001
            pass
        try:
            self.thread_pool.shutdown(wait=True)
        except Exception:  # noqa: BLE001
            pass


if __name__ == "__main__":
    import sys

    from qtpy.QtCore import QTimer
    from qtpy.QtWidgets import QApplication

    app = QApplication(sys.argv)
    executor = FileActionsExecutor(max_workers=2)

    def on_task_started(task_id: str):
        print(f"Task {task_id} started")

    def on_task_completed(task_id: str, result: Any):
        print(f"Task {task_id} completed with result: {result}")

    def on_task_failed(task_id: str, error: Exception):
        assert isinstance(error, Exception)
        RobustLogger().exception(f"Task {task_id} failed with error: {error!s}", exc_info=error or True)

    def on_task_progress(task_id: str, progress: float):
        print(f"Task {task_id} progress: {progress}%")

    def on_all_tasks_completed():
        print("All tasks completed")
        app.quit()

    executor.TaskStarted.connect(on_task_started)
    executor.TaskCompleted.connect(on_task_completed)
    executor.TaskFailed.connect(on_task_failed)
    executor.TaskProgress.connect(on_task_progress)
    executor.AllTasksCompleted.connect(on_all_tasks_completed)

    print("Queueing tasks...")
    executor.queue_task("create_file", args=("test1.txt", "Hello, World!"), priority=1)
    executor.queue_task("create_file", args=("test2.txt", "Python is awesome!"), priority=2)
    executor.queue_task("read_file", args=("test1.txt",), priority=0)
    print("Tasks queued")

    timer = QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(100)

    print("Starting event loop...")
    sys.exit(app.exec())
