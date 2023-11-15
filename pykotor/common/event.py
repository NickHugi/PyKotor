from typing import Callable, List


class Observable:
    def __init__(self):
        self.callbacks: List[Callable] = []

    def subscribe(self, callback: Callable) -> None:
        self.callbacks.append(callback)

    def fire(self, message: object) -> None:
        for callback in self.callbacks:
            callback(message)
