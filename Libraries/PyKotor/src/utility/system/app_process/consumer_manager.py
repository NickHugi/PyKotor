from __future__ import annotations

import asyncio
import atexit
import multiprocessing
import threading
import time

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, ClassVar, Generic, TypeVar

from loggerplus import RobustLogger

from utility.system.app_process.graph import TaskGraph
from utility.system.app_process.scheduler import PrioritizedTask, TaskPriority, TaskScheduler
from utility.system.app_process.task_consumer import P, R, TaskConsumer

if TYPE_CHECKING:
    from multiprocessing.synchronize import Event as multiprocessing_Event, Lock as multiprocessing_Lock


T = TypeVar("T")


class ConsumerManager(Generic[P, R]):
    _instance: ConsumerManager | None = None
    _loop: asyncio.AbstractEventLoop | None = None
    _stop_event: asyncio.Event
    _consumer_stop_event: multiprocessing_Event
    _consumers: list[TaskConsumer[P, R]]
    _consumer_tasks: ClassVar[list[asyncio.Task[Any]]] = []
    _task_queue: asyncio.Queue[PrioritizedTask]
    _result_queue: multiprocessing.Queue[tuple[int, R | Exception]]
    _consumer_task_queue: multiprocessing.JoinableQueue[tuple[int, PrioritizedTask]]
    _is_running: bool = False
    _main_thread_id: int = threading.get_ident()
    _main_task: asyncio.Task | None = None
    _is_main_thread: bool = False
    _is_main_process: bool = False
    _graceful_shutdown_timeout: float = 5.0
    _thread_lock: threading.Lock = threading.Lock()
    _process_lock: multiprocessing_Lock = multiprocessing.Lock()
    _async_lock: asyncio.Lock = asyncio.Lock()
    _task_count: int = 0
    _completed_task_count: int = 0
    _failed_task_count: int = 0
    _start_time: float = 0.0
    _paused: bool = False
    _scheduled_tasks: ClassVar[list[tuple[float, PrioritizedTask]]] = []
    _task_status: ClassVar[dict[int, dict[str, Any]]] = {}
    _max_retries: int = 3
    _task_graph: TaskGraph = TaskGraph()
    _task_priorities: ClassVar[dict[int, TaskPriority]] = {}
    _task_dependencies: ClassVar[dict[int, set[int]]] = {}
    _task_scheduler: TaskScheduler = TaskScheduler()

    def __new__(cls, *args: Any, **kwargs: Any) -> ConsumerManager:
        with cls._thread_lock, cls._process_lock:
            if cls._instance is None:
                instance = super().__new__(cls)
                cls._instance = instance
                cls._loop = asyncio.get_event_loop()

                def atexit_stop_event():
                    stop_event: asyncio.Event | None = getattr(cls, "_stop_event", None)
                    if stop_event is None:
                        return
                    stop_event.set()
                    del cls._instance

                atexit.register(atexit_stop_event)
            return cls._instance

    def __init__(self, num_consumers: int | None = multiprocessing.cpu_count() * 2, retry_policy: dict[str, Any] | None = None):
        RobustLogger().info(f"ConsumerManager.__init__ called with num_consumers={num_consumers}")
        if self.__class__._instance is None:
            raise RuntimeError("ConsumerManager instance does not exist")
        self._consumer_stop_event = multiprocessing.Event()
        self._task_queue = asyncio.Queue()
        self._result_queue = multiprocessing.Queue()
        self._consumer_task_queue = multiprocessing.JoinableQueue()
        self._is_main_thread = threading.current_thread() is threading.main_thread()
        self._is_main_process = multiprocessing.current_process().name == "MainProcess"
        self._consumers = [
            TaskConsumer(
                name=f"ConsumerManager.consumer.{i}",
                daemon=True,
                stop_event=self._consumer_stop_event,
                task_queue=self._consumer_task_queue,
                result_queue=self._result_queue,
            )
            for i in range(num_consumers or max(1, multiprocessing.cpu_count() * 2))
        ]
        self._is_running = False
        self._stop_event = asyncio.Event()
        self._retry_policy: dict[str, Any] = retry_policy or {"max_retries": 3, "retry_delay": 1.0}
        if self.__class__ is not ConsumerManager:
            RobustLogger().info("ConsumerManager.__init__ called on a subclass, nothing to do")
            return
        try:
            self._loop = asyncio.get_event_loop()
        except RuntimeError:
            RobustLogger().warning(f"{self.__class__.__name__}: Error getting existing event loop")
        finally:
            if self._loop is None:

                def start_new_event_loop():
                    with self._thread_lock, self._process_lock:
                        self._loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(self._loop)
                    asyncio.run(self.run())

                thread = threading.Thread(target=start_new_event_loop, name="ConsumerManager.run_thread", daemon=False)
                thread.start()
            else:
                self._main_task = asyncio.create_task(self.run(), name="ConsumerManager.run")

    def __del__(self):
        self.queue_stop_event(process_remaining_tasks=True)

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    async def run(self) -> None:
        RobustLogger().warning("ConsumerManager.run called")
        async with self._async_lock:
            if self._is_running:
                return
            RobustLogger().info("ConsumerManager.run setting running to True")
            self._is_running = True
        RobustLogger().info("ConsumerManager.run starting consumers")
        for consumer in self._consumers:
            consumer.start()
        RobustLogger().info("ConsumerManager.run started consumers")
        self._loop = asyncio.get_event_loop()
        self._start_time = time.time()
        last_queue_check = 0
        while not self._stop_event.is_set():
            await self._transfer_tasks()  # Send any pending tasks to the consumer processes.
            try:
                current_time = self._loop.time()
                if current_time - last_queue_check >= 0.1:  # Check queue every 100ms
                    await self._process_scheduled_tasks(current_time)
                    last_queue_check = current_time
                await self._process_results_async()
            except asyncio.TimeoutError:  # noqa: PERF203
                RobustLogger().warning(f"{self.__class__.__name__}.run timeout")
            except Exception as e:  # noqa: BLE001
                RobustLogger().warning(f"Exception {e.__class__.__name__} thrown in {self.__class__.__name__}.run", exc_info=True)
            finally:
                await asyncio.sleep(0.01 if not self._paused else 0.1)

    async def _transfer_tasks(self) -> None:
        while self._is_running:
            try:
                task = await asyncio.wait_for(self._task_queue.get(), timeout=0.1)
                task_id = id(task)
                print("transfer_tasks: put task in consumer_task_queue")
                self._consumer_task_queue.put((task_id, task))
                self._task_queue.task_done()
                print("transfer_tasks: task_done")
            except asyncio.TimeoutError:  # noqa: PERF203
                print("transfer_tasks: timeout")
                break
            except Exception as e:  # noqa: BLE001
                print(f"transfer_tasks: Error transferring task: {e}")
                RobustLogger().warning(f"Error transferring task: {e}", exc_info=True)
            await asyncio.sleep(0.01)

    def _process_remaining_tasks(self) -> None:
        print("process_remaining_tasks called")
        while not self._task_queue.empty():
            task = self._task_queue.get_nowait()
            self._consumer_task_queue.put((id(task), task))

    def _discard_remaining_tasks(self) -> None:
        print("discard_remaining_tasks called")
        while not self._task_queue.empty():
            self._task_queue.get_nowait()
        while not self._result_queue.empty():
            self._result_queue.get_nowait()

    async def add_task(
        self, func: P, *args: Any, priority: TaskPriority = TaskPriority.NORMAL, timeout: float | None = None, dependencies: list[int] = None, **kwargs: Any
    ) -> int:
        print("add_task called")
        if not self._is_running:
            raise RuntimeError("ConsumerManager is not running")

        task = PrioritizedTask(priority=priority, task=func, args=args, kwargs=kwargs, timeout=timeout, dependencies=dependencies or [], checkpoints={})
        task_id = id(task)
        self._task_graph.add_task(task_id, dependencies or [])
        self._task_priorities[task_id] = priority
        self._task_scheduler.add_task(task)
        return await self._add_task_status(task)

    def check_task_queue(self) -> None:
        print("check_task_queue called")
        if self._paused:
            return
        assert self._loop is not None, f"{self.__class__.__name__}.check_task_queue error: loop is not running"
        while not self._consumer_task_queue.empty():
            task_id, task = self._consumer_task_queue.get()
            if task_id is not None and task is not None:
                try:
                    self._update_task_status(task_id, "running")
                    if task.timeout is not None:
                        try:
                            result = self._loop.run_until_complete(asyncio.wait_for(self._execute_task(task), timeout=task.timeout))
                            self._result_queue.put((task_id, result))
                            self._completed_task_count += 1
                            self._update_task_status(task_id, "completed")
                        except asyncio.TimeoutError:
                            RobustLogger().warning(f"Task {task.task.__name__} timed out after {task.timeout} seconds")
                            self._failed_task_count += 1
                            self._update_task_status(task_id, "timeout")
                            self._result_queue.put((task_id, TimeoutError(f"Task {task.task.__name__} timed out")))
                    else:
                        result = self._loop.run_until_complete(self._execute_task(task))
                        self._result_queue.put((task_id, result))
                        self._completed_task_count += 1
                        self._update_task_status(task_id, "completed")
                    self._task_status.pop(task_id, None)
                    self._consumer_task_queue.task_done()
                except Exception as e:  # noqa: F841, BLE001
                    RobustLogger().error(f"Error executing task: {task.task.__name__}", exc_info=True)

    def is_running(self) -> bool:
        with self._thread_lock, self._process_lock:
            return self._is_running

    async def is_running_async(self) -> bool:
        with self._thread_lock, self._process_lock:
            async with self._async_lock:
                return self._is_running

    async def start(self) -> None:
        if not self._is_running:
            await self.run()

    def queue_stop_event(
        self,
        *,
        process_remaining_tasks: bool = True,
        graceful_shutdown_timeout: float = 1.0,
    ) -> None:
        RobustLogger().warning("ConsumerManager.stop called")
        self._is_running = False
        for _ in self._consumers:
            with self._thread_lock, self._process_lock:
                self._consumer_stop_event.set()

        for consumer in self._consumers:
            try:
                consumer.join(timeout=graceful_shutdown_timeout)
                if consumer.is_alive():
                    RobustLogger().warning(f"Consumer {consumer.name} did not terminate gracefully")
                    consumer.terminate()
            except (TimeoutError, RuntimeError) as e:  # noqa: PERF203
                RobustLogger().warning(f"Error stopping consumer {consumer.name}: {e}", exc_info=True)
            finally:
                consumer.close()

        self._consumers.clear()
        self._process_remaining_tasks() if process_remaining_tasks else self._discard_remaining_tasks()
        RobustLogger().warning("ConsumerManager stopped")

    def stop(self, *, process_remaining_tasks: bool = True, graceful_shutdown_timeout: float = 1.0):
        RobustLogger().warning("ConsumerManager.stop called")
        self._is_running = False
        for _ in self._consumers:
            with self._thread_lock, self._process_lock:
                self._consumer_stop_event.set()

        for consumer in self._consumers:
            try:
                consumer.join(timeout=graceful_shutdown_timeout)
                if consumer.is_alive():
                    RobustLogger().warning(f"Consumer {consumer.name} did not terminate gracefully")
                    consumer.terminate()
            except (TimeoutError, RuntimeError) as e:  # noqa: PERF203
                RobustLogger().warning(f"Error stopping consumer {consumer.name}: {e}", exc_info=True)
            finally:
                consumer.close()

        self._consumers.clear()
        self._process_remaining_tasks() if process_remaining_tasks else self._discard_remaining_tasks()
        RobustLogger().warning(f"{self.__class__.__name__} stopped")

    def get_result(
        self,
        task_id: int,
        *,
        block: bool = True,
        timeout: float | None = None,
    ) -> tuple[int, R | Exception]:
        start_time = time.time()
        while True:
            if task_id not in self._task_status:
                return (task_id, KeyError(f"Task {task_id} not found"))  # Task not found or already completed
            if self._task_status[task_id] == "completed":
                result = self._result_queue.get(block=block, timeout=timeout)
                if isinstance(result, Exception):
                    continue
                if task_id == result[0]:
                    return result
            if timeout is not None and time.time() - start_time > timeout:
                raise TimeoutError(f"Task {task_id} did not complete within the specified timeout")
            time.sleep(0.1)

    async def get_result_async(
        self,
        task_id: int,
        *,
        block: bool = True,
    ) -> tuple[int, R | Exception]:
        while not self._stop_event.is_set():
            if task_id not in self._task_status:
                return (task_id, KeyError(f"Task {task_id} not found"))  # Task not found or already completed
            if self._task_status[task_id] == "completed":
                result = self._result_queue.get(block=block)
                if isinstance(result, Exception):
                    continue
                if task_id == result[0]:
                    return result
            await asyncio.sleep(0.1)
        return (task_id, TimeoutError(f"Task {task_id} timed out somehow"))

    async def _process_results_async(self) -> None:
        while not self._result_queue.empty():
            try:
                task_id, result = await self.get_result_async(block=False)
                if isinstance(result, Exception):
                    self._update_task_status(task_id, "failed")
                    self._failed_task_count += 1
                else:
                    self._update_task_status(task_id, "completed")
                    self._completed_task_count += 1
                self._task_status.pop(task_id, None)
            except asyncio.TimeoutError:  # noqa: E722, PERF203
                break
            except Exception as e:  # noqa: BLE001
                RobustLogger().warning(f"Error processing result: {e}", exc_info=True)

    async def _execute_task(self, task: PrioritizedTask) -> R:
        try:
            if task.progress_callback:
                result = await task.task(*task.args, progress_callback=task.progress_callback, **task.kwargs)
            else:
                result = await task.task(*task.args, **task.kwargs)
        except Exception as e:
            RobustLogger().warning(f"Error executing task {task.task.__name__}: {e}", exc_info=True)
            if task.retry_count < self._max_retries:
                task.retry_count += 1
                await self._task_queue.put(task)
                RobustLogger().info(f"Retrying task {task.task.__name__} (attempt {task.retry_count})")
            else:
                raise
        else:
            return result

    def _add_task_status(self, task: PrioritizedTask) -> int:
        task_id = id(task)
        self._task_status[task_id] = {"status": "pending", "checkpoints": {}}
        self._task_count += 1
        return task_id

    def _update_task_status(self, task_id: int, status: str) -> None:
        self._task_status[task_id]["status"] = status

    async def _process_scheduled_tasks(self, current_time: float) -> None:
        tasks_to_execute = [task for scheduled_time, task in self._scheduled_tasks if scheduled_time <= current_time]
        self._scheduled_tasks = [(scheduled_time, task) for scheduled_time, task in self._scheduled_tasks if scheduled_time > current_time]
        for task in tasks_to_execute:
            await self._task_queue.put(task)

    async def schedule_task(
        self,
        func: P,
        delay: float,
        priority: TaskPriority = TaskPriority.NORMAL,
        *args: Any,
        **kwargs: Any,
    ) -> int:
        scheduled_time = time.time() + delay
        task = PrioritizedTask(priority=priority, task=func, args=args, kwargs=kwargs)
        self._scheduled_tasks.append((scheduled_time, task))
        self._scheduled_tasks.sort(key=lambda x: x[0])
        return self._add_task_status(task)

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def get_stats(self) -> dict[str, Any]:
        return {
            "task_count": self._task_count,
            "completed_task_count": self._completed_task_count,
            "failed_task_count": self._failed_task_count,
            "queue_size": self._task_queue.qsize(),
            "is_running": self._is_running,
            "uptime": time.time() - self._start_time,
            "paused": self._paused,
        }

    @property
    def task_graph(self) -> TaskGraph:
        return self._task_graph

    @property
    def task_scheduler(self) -> TaskScheduler:
        return self._task_scheduler

    @asynccontextmanager
    async def checkpoint(self, task_id: int, checkpoint_name: str):
        try:
            yield
        finally:
            self._task_status[task_id]["checkpoints"][checkpoint_name] = time.time()

    async def get_task_status(self, task_id: int) -> dict[str, Any]:
        return self._task_status.get(task_id, {})

    async def cancel_task(self, task_id: int) -> bool:
        if task_id in self._task_status:
            self._task_status[task_id]["status"] = "cancelled"
            return True
        return False

    @classmethod
    async def create_async(cls, num_consumers: int | None = None) -> ConsumerManager:
        instance = cls(num_consumers=num_consumers)
        await instance.start()
        return instance


class PickledTask:
    """A class to represent a task.

    Attributes:
    ----------
        message (str): The message to be returned when the task is called.
    """

    def __init__(self, message: str):
        self.message = message

    def __call__(self):
        return self.message


if __name__ == "__main__":
    """Test the consumer manager."""

    async def main():
        consumer_manager = await ConsumerManager.create_async(num_consumers=1)

        await consumer_manager.add_task(PickledTask("Task 1 completed"))
        await consumer_manager.add_task(PickledTask("Task 2 completed"))
        await consumer_manager.add_task(PickledTask("Task 3 completed"))
        await consumer_manager.add_task(PickledTask("Task 4 completed"))
        await consumer_manager.add_task(PickledTask("Task 5 completed"))
        await consumer_manager.add_task(PickledTask("Task 6 completed"))
        await consumer_manager.add_task(PickledTask("Task 7 completed"))
        await consumer_manager.add_task(PickledTask("Task 8 completed"))
        await consumer_manager.add_task(PickledTask("Task 9 completed"))

        await asyncio.sleep(1)  # Give some time for tasks to be processed

        results = await consumer_manager.get_results()

        for i, result in enumerate(results):
            assert result[i + 1] == f"Task {i + 1} completed", result

        print("All tasks completed: ", results)

        await consumer_manager.stop()

    asyncio.run(main())
