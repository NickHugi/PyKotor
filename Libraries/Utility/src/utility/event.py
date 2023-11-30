from __future__ import annotations

from typing import Callable


class Observable:
    def __init__(self):
        self.callbacks: list[Callable] = []

    def subscribe(self, callback: Callable) -> None:
        self.callbacks.append(callback)

    def fire(self, message: object) -> None:
        for callback in self.callbacks:
            callback(message)
