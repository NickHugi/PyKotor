from __future__ import annotations

import functools
import multiprocessing

from concurrent.futures import ProcessPoolExecutor
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Generic, Iterable, Iterator, TypeVar

from utility.system.app_process.task_consumer import TaskConsumer

if TYPE_CHECKING:
    from multiprocessing.synchronize import Event as MultiprocessingEvent


T = TypeVar("T")


class CustomProcessPoolExecutor(Generic[T]):
    """This is a class created for educational purposes only.

    Use concurrent.futures.ProcessPoolExecutor instead of this implementation.
    """
    _shared_state: ClassVar[dict[str, Any]] = {}

    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls)
        obj.__dict__ = cls._shared_state
        return obj

    def __init__(
        self,
        *,
        max_workers: int | None = multiprocessing.cpu_count() * 2,
        initializer: Callable[[], None] | None = None,
        initargs: tuple[Any, ...] = (),
    ):
        if hasattr(self, "singleton_initialized"):
            return
        self.max_workers: int = max_workers or multiprocessing.cpu_count() * 2
        self.task_queue: multiprocessing.JoinableQueue[Callable[..., Any]] = multiprocessing.JoinableQueue()
        self.result_queue: multiprocessing.Queue[T] = multiprocessing.Queue()
        self.workers: list[tuple[MultiprocessingEvent, TaskConsumer]] = []
        self._initializer: Callable[[], None] | None = initializer
        self.executor: ProcessPoolExecutor = ProcessPoolExecutor(
            max_workers=self.max_workers,
            initializer=self._initializer,
            initargs=initargs,
        )
        self._create_workers()
        self.singleton_initialized: bool = True

    def __del__(self):
        self.shutdown(wait=False)

    async def run(self):
        while True:
            task = self.task_queue.get(block=False, timeout=0.01)
            if task is None:
                break
            result = await self.executor.submit(task).result()
            self.result_queue.put(result)
            self.task_queue.task_done()

    def _create_workers(self):
        for i in range(self.max_workers):
            worker = TaskConsumer(
                task_queue=self.task_queue,
                result_queue=self.result_queue,
                name=f"TaskConsumer-{i}",
                daemon=True,
            )
            worker.start()
            stop_event = multiprocessing.Event()
            self.workers.append((stop_event, worker))

    def shutdown(
        self,
        *,
        wait: bool = True,
        timeout: float | None = None,
    ):
        for stop_event, worker in self.workers:
            stop_event.set()
            worker.join(timeout=timeout)
        if not wait:
            return
        for stop_event, _ in self.workers:
            stop_event.wait(timeout=timeout)

    def map(self, fn: Callable[..., T], *iterables: Iterable[Any]) -> Iterator[T]:
        return self.executor.map(fn, *iterables)


# Singleton instance
_instance: CustomProcessPoolExecutor | None = None


def get_instance(*args, **kwargs) -> CustomProcessPoolExecutor:
    global _instance  # noqa: PLW0603
    if _instance is None:
        _instance = CustomProcessPoolExecutor(*args, **kwargs)
    return _instance


if __name__ == "__main__":

    def example_task(x: Any) -> Any:
        return x * x

    executor1 = get_instance(max_workers=1)
    executor2 = get_instance(max_workers=2)  # This will return the same instance as executor1

    results = list(
        executor1.map(
            functools.partial(print, "Hello World"),
            [(x, i) for i in range(10) for x in range(10)],
        )
    )

    print("Results:", results)
    print("executor1 is executor2:", executor1 is executor2)  # This should print True
