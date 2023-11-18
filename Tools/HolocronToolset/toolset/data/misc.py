from __future__ import annotations

from typing import Set, Tuple

Bind = Tuple[Set[int], Set[int]]


class ControlItem:
    def __init__(self, bind: Bind):
        self.keys: set[int] = bind[0]
        self.mouse: set[int] = bind[1]

    def satisfied(self, buttons: set[int], keys: set[int], *, exactKeys=True) -> bool:
        if exactKeys:
            return (self.mouse == buttons or self.mouse is None) and (self.keys == keys or self.keys is None)
        return (self.mouse == buttons or self.mouse is None) and (self.keys.issubset(keys))

