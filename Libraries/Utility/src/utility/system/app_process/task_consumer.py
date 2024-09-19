from __future__ import annotations

import functools
import multiprocessing
import sys
import time

from typing import TYPE_CHECKING, Any, Callable, Generic, Mapping, TypeVar

from loggerplus import RobustLogger

from utility.system.win32.job import assign_process_to_job_object, close_handle, create_job_object

if TYPE_CHECKING:
    from multiprocessing.popen_spawn_win32 import Popen as Popen_multiprocessing
    from multiprocessing.synchronize import Event as multiprocessing_Event


P = TypeVar("P", bound=Callable[..., Any])
R = TypeVar("R")


class TaskConsumer(Generic[P, R], multiprocessing.Process):
    """A worker process that consumes tasks from a queue, executes them, and puts the results in a result queue.

    The `ConsumerProcess` class is responsible for running tasks that are added to the `task_queue`. It continuously
    checks the `task_queue` for new tasks, and when a task is found, it executes the task function with the
    provided arguments and puts the result in the `result_queue`.

    When the `None` value is found in the `task_queue`, the process will exit.

    Args:
    ----
        group (None): The group of the process.
        target (Callable[[], R] | None): The target function to be executed by the process.
        name (str): The name of the process.
        *args: The arguments to be passed to the target function.
        **kwargs: The keyword arguments to be passed to the target function.
        daemon (bool): Whether the process is a daemon.
        stop_event (multiprocessing_Event | None): The event to stop the process.
        task_queue (multiprocessing.JoinableQueue[P] | None): The queue to put the tasks in.
        result_queue (multiprocessing.Queue[R | Exception] | None): The queue to put the results in.

    Attributes:
    ----------
        task_queue (multiprocessing.JoinableQueue[P]): Queue for storing tasks to be processed.
        result_queue (multiprocessing.Queue[R | Exception]): Queue for storing results of processed tasks.
        _stop_event (multiprocessing_Event): Event to signal the process to stop.
        args (tuple[Any, ...]): Positional arguments to be passed to the target function.
        kwargs (Mapping[str, Any]): Keyword arguments to be passed to the target function.
        _popen (Popen_multiprocessing | None): Popen object for the process. Only used on Windows.
        _job (int | None): Job object identifier.
        _target (Callable[[], R] | None): Target function to be executed by the process.
        name (str): Name of the process.
        daemon (bool): Whether the process is a daemon.
        _identity (tuple): Process identity, inherited from parent process with additional count.
        _config (dict): Configuration dictionary, copied from parent process.
        _parent_pid (int): Process ID of the parent process.
        _parent_name (str): Name of the parent process.
        _closed (bool): Flag indicating if the process is closed.
        _args (tuple): Tuple of positional arguments passed to the process.
        _kwargs (dict): Dictionary of keyword arguments passed to the process.
    """

    def __init__(  # noqa: PLR0913
        self,
        group: None = None,
        target: Callable[[], R | Exception] | None = None,
        name: str = "TaskConsumer",
        *args,
        daemon: bool = True,
        stop_event: multiprocessing_Event | None = None,
        task_queue: multiprocessing.JoinableQueue[Callable[[], R | Exception]] | None = None,
        result_queue: multiprocessing.Queue[R | Exception] | None = None,
        **kwargs,
    ):
        """Initialize the task consumer.

        Note that the handle is not open at this scope yet, even after the super().__init__ call.
        """
        super().__init__(group, target, name, args, kwargs, daemon=daemon)
        self.task_queue: multiprocessing.JoinableQueue[Callable[[], R | Exception]] = multiprocessing.JoinableQueue() if task_queue is None else task_queue
        self.result_queue: multiprocessing.Queue[R | Exception] = multiprocessing.Queue() if result_queue is None else result_queue
        self._stop_event: multiprocessing_Event = multiprocessing.Event() if stop_event is None else stop_event
        self.args: tuple[Any, ...] = args
        self.kwargs: Mapping[str, Any] = kwargs
        if sys.platform == "win32":
            self._popen: Popen_multiprocessing | None  # provided by base class
            self._job: int | None = None  # job object identifier, used to group processes in task manager

    def get_target(self) -> Callable[[], R | Exception] | None:
        return getattr(self, "_target", None)

    def run(self):
        """Run the task consumer.

        This method is called when the process starts. It will run the task until the stop event is set.
        """
        target: Callable[[], R | Exception] | None = self.get_target()
        if target is not None:
            result: R | Exception = target(*self.args, **self.kwargs)  # pyright: ignore[reportAssignmentType]
            if self.result_queue is not None:
                self.result_queue.put(result)
            return

        while not self._stop_event.is_set():
            if self.task_queue.empty():
                time.sleep(0.01)
                continue
            task = self.task_queue.get(block=True)
            try:
                result = task(*self.args, **self.kwargs)
                self.result_queue.put(result)
            except Exception as e:  # noqa: BLE001
                RobustLogger().exception("Error executing task")
                self.result_queue.put(e)
            if self._stop_event.is_set():
                break

            self.task_queue.task_done()

        if not self._stop_event.is_set():
            self._stop_event.set()
            self.stop()

    def start(self):
        """Start the task consumer.

        This method is called when the process starts. It will start the task consumer.

        Processing Logic:
        -----------------
            1. Start the process.
            2. (if windows) Assign the process to the job object, so that child processes will be grouped in task manager.
            3. Wait for the process to finish.
        """
        super().start()
        if sys.platform != "win32":
            return
        try:
            assert self._popen is not None
            self.job = create_job_object()
            open_handle: int = self._popen._handle  # pyright: ignore[reportAttributeAccessIssue]  # noqa: SLF001
            assign_process_to_job_object(self.job, open_handle)
        except Exception:  # noqa: BLE001
            RobustLogger().warning("Failed to assign process to job object", exc_info=True)

    def stop(self):
        """Stop the task consumer.

        This method is called when the process stops. It will stop the task consumer.
        """
        self._stop_event.set()
        if sys.platform == "win32":
            try:
                assert self._job is not None
                close_handle(self._job)
            except Exception:  # noqa: BLE001
                RobustLogger().warning("Failed to close job object", exc_info=True)


if __name__ == "__main__":
    """Test the task consumer."""
    from multiprocessing import JoinableQueue, Queue

    task_queue = JoinableQueue()
    result_queue = Queue()
    task_consumer = TaskConsumer(task_queue=task_queue, result_queue=result_queue, daemon=True)
    task_consumer.start()

    task_queue.put(functools.partial(str, "Task 1 completed"))
    task_queue.put(functools.partial(str, "Task 2 completed"))
    task_queue.put(functools.partial(str, "Task 3 completed"))
    task_queue.put(functools.partial(str, "Task 4 completed"))
    task_queue.put(functools.partial(str, "Task 5 completed"))
    task_queue.put(functools.partial(str, "Task 6 completed"))
    task_queue.put(functools.partial(str, "Task 7 completed"))
    task_queue.put(functools.partial(str, "Task 8 completed"))
    task_queue.put(functools.partial(str, "Task 9 completed"))

    result1 = result_queue.get()
    result2 = result_queue.get()
    result3 = result_queue.get()
    result4 = result_queue.get()
    result5 = result_queue.get()
    result6 = result_queue.get()
    result7 = result_queue.get()
    result8 = result_queue.get()
    result9 = result_queue.get()

    assert result1 == "Task 1 completed", result1
    assert result2 == "Task 2 completed", result2
    assert result3 == "Task 3 completed", result3
    assert result4 == "Task 4 completed", result4
    assert result5 == "Task 5 completed", result5
    assert result6 == "Task 6 completed", result6
    assert result7 == "Task 7 completed", result7
    assert result8 == "Task 8 completed", result8
    assert result9 == "Task 9 completed", result9

    print("All tasks completed: ", result1, result2, result3, result4, result5, result6, result7, result8, result9)
