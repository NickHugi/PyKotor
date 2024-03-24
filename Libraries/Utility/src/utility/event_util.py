from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


class Observable:
    def __init__(self):
        self.callbacks: list[Callable] = []

    def subscribe(self, callback: Callable):
        self.callbacks.append(callback)

    def fire(self, message: object):
        for callback in self.callbacks:
            callback(message)
