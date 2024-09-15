from __future__ import annotations

import time

from dataclasses import dataclass, field
from enum import IntEnum
from typing import TYPE_CHECKING, Generic, TypeVar

from utility.system.app_process.graph import TaskGraph

if TYPE_CHECKING:
    from typing import Any, Callable

    from utility.system.app_process.task_consumer import R
else:
    R = TypeVar("R")  # Prevent circular import


class TaskPriority(IntEnum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass(order=True)
class PrioritizedTask(Generic[R]):
    """A class representing a task with a priority.

    Attributes:
    ----------
        priority: The priority of the task.
        task: The task to be executed.
        args: The arguments to be passed to the task.
        kwargs: The keyword arguments to be passed to the task.
        timeout: The timeout for the task.
        dependencies: The dependencies of the task.
        progress_callback: The callback to be called with the progress of the task.
        retry_count: The number of times the task has been retried.
        timestamp: The timestamp of the task.
        checkpoints: The checkpoints of the task.
    """
    priority: TaskPriority
    task: Callable[..., R] = field(compare=False)
    args: tuple[Any, ...] = field(compare=False)
    kwargs: dict[str, Any] = field(compare=False)
    timeout: float | None = field(default=None, compare=False)
    dependencies: list[int] = field(default_factory=list, compare=False)
    progress_callback: Callable[[float], None] | None = field(default=None, compare=False)
    retry_count: int = field(default=0, compare=False)
    timestamp: float = field(default_factory=time.time, compare=False)
    checkpoints: dict[str, Any] = field(default_factory=dict, compare=False)


class TaskScheduler:
    """A class to schedule tasks based on their dependencies and priorities.

    Attributes:
    ----------
        _task_queue: A list of tasks to be scheduled.
        _task_graph: A TaskGraph object representing the task dependencies.
        _task_priorities: A dictionary mapping task IDs to their priorities.
    """

    def __init__(self):
        self._task_queue: list[PrioritizedTask[Any]] = []
        self._task_graph: TaskGraph = TaskGraph()
        self._task_priorities: dict[int, TaskPriority] = {}

    def add_task(self, task: PrioritizedTask) -> None:
        """Adds a task to the scheduler.

        Args:
        ----
            task: The task to be scheduled.
        """
        task_id = id(task)
        self._task_graph.add_task(task_id, task.dependencies)
        self._task_priorities[task_id] = task.priority
        self._task_queue.append(task)
        self._task_queue.sort(key=lambda x: (x.priority, x.timestamp))



    async def add_task_async(self, task: PrioritizedTask) -> None:
        """Asynchronously adds a task to the scheduler.

        Args:
        ----
            task: The task to be scheduled.
        """
        task_id = id(task)
        self._task_graph.add_task(task_id, task.dependencies)
        self._task_priorities[task_id] = task.priority
        self._task_queue.append(task)
        self._task_queue.sort(key=lambda x: (x.priority, x.timestamp))

    def get_next_task(self) -> PrioritizedTask | None:
        """Returns the next task to be executed, based on dependencies and priorities.

        Returns:
        -------
            The next task to be executed, or None if no tasks are ready.
        """
        ready_tasks = self._task_graph.get_ready_tasks()
        if not ready_tasks:
            return None
        next_task_id = min(ready_tasks, key=lambda x: (self._task_priorities[x], next(i for i, task in enumerate(self._task_queue) if id(task) == x)))
        return next(task for task in self._task_queue if id(task) == next_task_id)

    def get_task_queue(self) -> list[PrioritizedTask]:
        """Returns the task queue.

        Returns:
        -------
            The task queue.
        """
        return self._task_queue

    def get_task_graph(self) -> TaskGraph:
        """Returns the task graph.

        Returns:
        -------
            The task graph.
        """
        return self._task_graph

    def get_task_priorities(self) -> dict[int, TaskPriority]:
        """Returns the task priorities.

        Returns:
        -------
            The task priorities.
        """
        return self._task_priorities
