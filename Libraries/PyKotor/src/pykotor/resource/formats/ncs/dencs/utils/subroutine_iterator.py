from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class SubroutineIterator:
    def __init__(self, subs: list):
        self.subs = subs
        self.index = 0

    def has_next(self) -> bool:
        return self.index < len(self.subs)

    def next(self):
        if not self.has_next():
            raise StopIteration
        result = self.subs[self.index]
        self.index += 1
        return result

