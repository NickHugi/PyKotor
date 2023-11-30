from __future__ import annotations

from typing import Set, Tuple

Bind = Tuple[Set[int], Set[int]]


class ControlItem:
    def __init__(self, bind: Bind):
        self.keys: set[int] = bind[0]
        self.mouse: set[int] = bind[1]

    def satisfied(self, buttons: set[int], keys: set[int], *, exactKeys=True) -> bool:
        """Handles the mouse scroll event.

        Args:
        ----
            delta: The amount and direction of the scroll.
            buttons: The set of buttons currently pressed.
            keys: The set of keys currently pressed.

        Returns:
        -------
            bool: Whether the input is satisfied.

        Processing Logic:
        ----------------
        - Check if exactKeys is True
        - If True, check if buttons and keys are equal sets or if one is None
        - If False, check if buttons are equal sets or one is None, and keys is a superset.
        """
        if exactKeys:
            return (self.mouse == buttons or self.mouse is None) and (self.keys == keys or self.keys is None)
        return (self.mouse == buttons or self.mouse is None) and (self.keys.issubset(keys))

