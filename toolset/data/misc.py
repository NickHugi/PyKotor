from typing import Tuple, Set


Bind = Tuple[Set[int], Set[int]]


class ControlItem:
    def __init__(self, bind: Bind):
        self.keys: Set[int] = bind[0]
        self.mouse: Set[int] = bind[1]

    def satisfied(self, buttons: Set[int], keys: Set[int]) -> bool:
        return (self.mouse == buttons or self.mouse is None) and (self.keys == keys or self.keys is None)

