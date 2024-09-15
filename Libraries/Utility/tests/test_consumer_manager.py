from __future__ import annotations

import asyncio
import multiprocessing
import unittest

from utility.system.app_process.consumer_manager import ConsumerManager


class TestConsumerManagerMainThreadAsync(unittest.TestCase):

    def test_singleton_behavior(self):
        # Ensure only one instance is created
        manager1 = ConsumerManager()
        manager2 = ConsumerManager()
        assert manager1 is manager2, "ConsumerManager is not a singleton"

    def test_initialization(self):
        # Check initial state
        assert isinstance(self.manager._task_queue, multiprocessing.JoinableQueue), f"Expected {multiprocessing.JoinableQueue}, got {type(self.manager._task_queue)}"  # noqa: SLF001
        assert isinstance(self.manager._result_queue, multiprocessing.Queue), f"Expected {multiprocessing.Queue}, got {type(self.manager._result_queue)}"  # noqa: SLF001
        assert len(self.manager._consumers) == 2, f"Expected 2 consumers, got {len(self.manager._consumers)}"  # noqa: SLF001, PLR2004
        assert not self.manager._is_running, f"Expected _is_running to be False, got {self.manager._is_running}"  # noqa: SLF001
        assert isinstance(self.manager._stop_event, asyncio.Event), f"Expected {asyncio.Event}, got {type(self.manager._stop_event)}"  # noqa: SLF001


    def test_add_task(self):
        # Add a task and check the task queue
        def sample_task(x):
            return x * 2

        self.manager.add_task(sample_task, 5)
        assert self.manager._task_queue.qsize() == 1, f"Expected task queue size to be 1, got {self.manager._task_queue.qsize()}"  # noqa: SLF001
        task = self.manager._task_queue.get_nowait()  # noqa: SLF001
        assert task[0] == sample_task, f"Expected task to be {sample_task}, got {task[0]}"
        assert task[1] == (5,), f"Expected task args to be (5,), got {task[1]}"
        assert task[2] == {}, f"Expected task kwargs to be {{}}, got {task[2]}"

    def test_run_and_process_tasks(self):
        # Start the manager and add tasks
        async def run_manager():
            await self.manager.run()

        def sample_task(x):
            return x * 2

        self.manager.add_task(sample_task, 5)
        self.manager.add_task(sample_task, 10)

        self.loop.run_until_complete(run_manager())
        assert self.manager._is_running, f"Expected _is_running to be True, got {self.manager._is_running}"  # noqa: SLF001

        # Check results
        result1 = self.manager.get_results()
        result2 = self.manager.get_results()
        assert result1 == 10, f"Expected 10, got {result1}"  # noqa: PLR2004
        assert result2 == 20, f"Expected 20, got {result2}"  # noqa: PLR2004

    def test_get_results(self):
        # Add tasks and get results
        def sample_task(x):
            return x * 2

        self.manager.add_task(sample_task, 5)
        self.manager.add_task(sample_task, 10)

        async def run_manager():
            await self.manager.run()

        self.loop.run_until_complete(run_manager())

        result1 = self.manager.get_results()
        result2 = self.manager.get_results()
        assert result1 == 10, f"Expected 10, got {result1}"  # noqa: PLR2004
        assert result2 == 20, f"Expected 20, got {result2}"  # noqa: PLR2004

    def test_queue_stop_event(self):
        # Test stopping the manager
        self.manager.queue_stop_event(process_remaining_tasks=False)
        assert not self.manager._is_running, f"Expected _is_running to be False, got {self.manager._is_running}"  # noqa: SLF001
        assert self.manager._consumer_stop_event.is_set(), f"Expected consumer_stop_event to be set, got {self.manager._consumer_stop_event.is_set()}"  # noqa: SLF001

    def test_process_remaining_tasks(self):
        # Add tasks and process remaining tasks
        def sample_task(x):
            return x * 2

        self.manager.add_task(sample_task, 5)
        self.manager.add_task(sample_task, 10)
        self.manager._process_remaining_tasks()  # noqa: SLF001

        result1 = self.manager.get_results()
        result2 = self.manager.get_results()
        assert result1 == 10, f"Expected 10, got {result1}"  # noqa: PLR2004
        assert result2 == 20, f"Expected 20, got {result2}"  # noqa: PLR2004

    def test_discard_remaining_tasks(self):
        # Add tasks and discard remaining tasks
        def sample_task(x):
            return x * 2

        self.manager.add_task(sample_task, 5)
        self.manager.add_task(sample_task, 10)
        self.manager._discard_remaining_tasks()  # noqa: SLF001

        assert self.manager._task_queue.empty(), f"Expected task queue to be empty, got {self.manager._task_queue.qsize()}"  # noqa: SLF001
        assert self.manager._result_queue.empty(), f"Expected result queue to be empty, got {self.manager._result_queue.qsize()}"  # noqa: SLF001

    def test_is_running(self):
        # Check if the manager is running
        assert not self.manager.is_running(), f"Expected is_running to be False, got {self.manager.is_running()}"
        self.loop.run_until_complete(self.manager.run())
        assert self.manager.is_running(), f"Expected is_running to be True, got {self.manager.is_running()}"

    def test_is_running_async(self):
        # Check if the manager is running asynchronously
        async def check_running():
            return await self.manager.is_running_async()

        assert not self.loop.run_until_complete(check_running()), f"Expected is_running to be False, got {self.manager.is_running()}"
        self.loop.run_until_complete(self.manager.run())
        assert self.loop.run_until_complete(check_running()), f"Expected is_running to be True, got {self.manager.is_running()}"

    def test_exception_handling_in_task(self):
        # Add a task that raises an exception
        def faulty_task():
            raise ValueError("Test exception")

        self.manager.add_task(faulty_task)
        async def run_manager():
            await self.manager.run()

        self.loop.run_until_complete(run_manager())
        result = self.manager.get_results()
        assert isinstance(result, ValueError), f"Expected ValueError, got {type(result)}"
        assert str(result) == "Test exception", f"Expected 'Test exception', got {result}"  # noqa: SLF001

    def test_consumer_start_and_stop(self):
        # Ensure consumers start and stop correctly
        for consumer in self.manager._consumers:  # noqa: SLF001
            assert not consumer.is_alive(), f"Expected consumer to be dead, got {consumer.is_alive()}"
        self.loop.run_until_complete(self.manager.run())
        for consumer in self.manager._consumers:  # noqa: SLF001
            assert consumer.is_alive(), f"Expected consumer to be alive, got {consumer.is_alive()}"
        self.manager.queue_stop_event()
        for consumer in self.manager._consumers:  # noqa: SLF001
            assert not consumer.is_alive(), f"Expected consumer to be dead, got {consumer.is_alive()}"

    def test_async_get_results(self):
        # Add tasks and get results asynchronously
        def sample_task(x):
            return x * 2

        self.manager.add_task(sample_task, 5)
        self.manager.add_task(sample_task, 10)

        async def run_manager():
            await self.manager.run()

        self.loop.run_until_complete(run_manager())

        async def get_results():
            result1 = await self.manager.get_results_async()
            result2 = await self.manager.get_results_async()
            return result1, result2

        result1, result2 = self.loop.run_until_complete(get_results())
        assert result1 == 10, f"Expected 10, got {result1}"  # noqa: PLR2004
        assert result2 == 20, f"Expected 20, got {result2}"  # noqa: PLR2004


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    manager = ConsumerManager(num_consumers=2)
    force_disabled = True
    PYTEST_AVAILABLE = False
    try:
        import pytest
        PYTEST_AVAILABLE = not force_disabled
    except ImportError:
        PYTEST_AVAILABLE = False
    if PYTEST_AVAILABLE:
        raise SystemExit(pytest.main([__file__, "-x", "-v", "--tb=native"]))
    else:
        raise SystemExit(unittest.main(failfast=True))
