from __future__ import annotations


class TaskGraph:
    """A class to represent a directed acyclic graph (DAG) of tasks.

    Attributes:
    ----------
        _graph: A dictionary representing the graph, where keys are task IDs and values are lists of dependent task IDs.
        _task_dependencies: A dictionary mapping task IDs to sets of their dependent task IDs.
        _task_status: A dictionary mapping task IDs to their current status.
    """

    def __init__(self):
        self._graph: dict[int, list[int]] = {}
        self._task_dependencies: dict[int, set[int]] = {}
        self._task_status: dict[int, str] = {}

    def add_task(self, task_id: int, dependencies: list[int]) -> None:
        """Adds a task to the graph.

        Args:
        ----
            task_id: The ID of the task to add.
            dependencies: A list of task IDs that this task depends on.
        """
        self._graph[task_id] = dependencies
        self._task_dependencies[task_id] = set(dependencies)
        self._task_status[task_id] = "pending"

    def get_dependencies(self, task_id: int) -> set[int]:
        """Returns the set of task IDs that the given task depends on.

        Args:
        ----
            task_id: The ID of the task.

        Returns:
        -------
            A set of task IDs that the given task depends on.
        """
        return self._task_dependencies.get(task_id, set())

    def get_dependents(self, task_id: int) -> set[int]:
        """Returns the set of task IDs that depend on the given task.

        Args:
        ----
            task_id: The ID of the task.

        Returns:
        -------
            A set of task IDs that depend on the given task.
        """
        dependents: set[int] = {
            task_id_in_graph
            for task_id_in_graph, dependencies in self._graph.items()
            if task_id in dependencies
        }
        return dependents

    def get_task_status(self, task_id: int) -> str:
        """Returns the current status of the given task.

        Args:
        ----
            task_id: The ID of the task.

        Returns:
        -------
            The current status of the task.
        """
        return self._task_status.get(task_id, "unknown")

    def update_task_status(self, task_id: int, status: str) -> None:
        """Updates the status of the given task.

        Args:
        ----
            task_id: The ID of the task.
            status: The new status of the task.
        """
        self._task_status[task_id] = status

    def is_task_ready(self, task_id: int) -> bool:
        """Checks if the given task is ready to be executed.

        A task is ready if all its dependencies have been completed.

        Args:
        ----
            task_id: The ID of the task.

        Returns:
        -------
            True if the task is ready, False otherwise.
        """
        return all(self.get_task_status(dependency) == "completed" for dependency in self.get_dependencies(task_id))

    def get_ready_tasks(self) -> list[int]:
        """Returns a list of task IDs that are ready to be executed.

        A task is ready if all its dependencies have been completed.

        Returns:
        -------
            A list of task IDs that are ready to be executed.
        """
        return [task_id for task_id in self._graph if self.is_task_ready(task_id)]

    def get_graph(self) -> dict[int, list[int]]:
        """Returns the graph representation as a dictionary.

        Returns:
        -------
            A dictionary representing the graph.
        """
        return self._graph

    def get_task_dependencies(self) -> dict[int, set[int]]:
        """Returns the task dependencies as a dictionary.

        Returns:
        -------
            A dictionary mapping task IDs to sets of their dependent task IDs.
        """
        return self._task_dependencies
