from __future__ import annotations

import asyncio

from typing import TYPE_CHECKING, Any, Callable

from loggerplus import RobustLogger
from qtpy.QtCore import QObject, QTimer

from utility.system.app_process.consumer_manager import ConsumerManager
from utility.system.app_process.task_consumer import TaskConsumer

if TYPE_CHECKING:
    import multiprocessing


class ConsumerManager(ConsumerManager, QObject):
    def __init__(self, num_consumers: int | None = None):
        ConsumerManager.__init__(self, num_consumers)
        QObject.__init__(self)
        QTimer.singleShot(0, lambda: asyncio.create_task(self.run()))

    async def run(self):
        if self._is_running:
            return
        self._is_running = True
        self.consumers = [TaskConsumer(args=(self._task_queue, self._result_queue)) for _ in range(self.num_consumers)]
        for consumer in self.consumers:
            consumer.start()
        await self._stop_event.wait()

    def queue_stop_event(
        self,
        graceful_shutdown_timeout: int = 5,
        *,
        process_remaining_tasks: bool = False,
    ):
        self._is_running = False

        # Signal consumers to stop
        for _ in self.consumers:
            self._task_queue.put(None)

        # Wait for consumers to finish
        for consumer in self.consumers:
            try:
                consumer.join(timeout=graceful_shutdown_timeout)
                if consumer.is_alive():
                    RobustLogger().warning(f"Consumer {consumer.name} did not terminate gracefully")
                    consumer.terminate()
            except TimeoutError:  # noqa: PERF203
                RobustLogger().warning(f"Timeout while stopping consumer {consumer.name}")
            except RuntimeError as e:
                RobustLogger().exception(f"Error stopping consumer {consumer.name}: {e}")
            finally:
                consumer.close()

        self.consumers.clear()

        # Process remaining tasks if requested
        if process_remaining_tasks:
            self._process_remaining_tasks()
        else:
            self._discard_remaining_tasks()

        RobustLogger().info("ConsumerManager stopped")

    def _process_remaining_tasks(self) -> None:
        while not self._task_queue.empty():
            task = self._task_queue.get(timeout=1)  # Add timeout to allow for graceful shutdown
            if task is not None:
                func, args = task
                try:
                    result = func(*args)
                    self._result_queue.put(("success", result))
                except Exception as e:  # noqa: BLE001
                    RobustLogger().exception(f"Error executing remaining task: {func.__name__}")
                    self._result_queue.put(("error", str(e)))

    def _discard_remaining_tasks(self) -> None:
        while not self._task_queue.empty():
            self._task_queue.get_nowait()

        while not self._result_queue.empty():
            self._result_queue.get_nowait()

    def add_task(self, func: Callable[..., Any], *args: Any) -> None:
        self._task_queue.put((func, args))

    @property
    def consumer_queue(self) -> multiprocessing.Queue:
        return self._result_queue

    def __del__(self):
        if self._is_running:
            self.queue_stop_event(process_remaining_tasks=True)


if __name__ == "__main__":
    import asyncio
    import sys

    from qasync import QEventLoop  # pyright: ignore[reportMissingTypeStubs]
    from qtpy.QtWidgets import QApplication

    def test_func():
        RobustLogger().info("Hello, world!")

    def main():
        app = QApplication(sys.argv)
        loop = QEventLoop(app)
        asyncio.set_event_loop(loop)
        manager = ConsumerManager(num_consumers=4)

        manager.add_task(test_func)

        with loop:
            loop.run_forever()

    main()
