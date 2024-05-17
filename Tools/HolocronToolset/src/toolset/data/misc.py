from __future__ import annotations

from typing import Set, Tuple, Union

from utility.logger_util import RobustRootLogger

Bind = Tuple[Set[int], Union[Set[int], None]]


class ControlItem:
    def __init__(self, bind: Bind):
        self.keys: set[int] = bind[0]
        self.mouse: set[int] | None = bind[1]

    def noButtons(self) -> bool:
        return self.mouse is None

    def anyButtons(self) -> bool:
        return not self.mouse and not self.noButtons()

    def anyKeys(self) -> bool:
        return not self.keys

    def satisfied(
        self,
        buttons: set[int],
        keys: set[int],
        *,
        exactKeys: bool = True,
    ) -> bool:
        """Handles the key/mouse events, determine if the conditions are met.

        Args:
        ----
            delta: The amount and direction of the scroll.
            buttons: The set of buttons currently pressed.
            keys: The set of keys currently pressed.

        Returns:
        -------
            bool: Whether the input is satisfied.
        """
        mouseSatisfied = self.anyButtons() or self.mouse == buttons
        keysSatisfied = self.anyKeys() or (self.keys == keys if exactKeys else self.keys.issubset(keys))

        if mouseSatisfied and keysSatisfied:
            return True

        #RobustRootLogger.debug(f"Needed mouse: {self.mouse!r}, user pressing {buttons!r}. Satisfied? {mouseSatisfied} no_buttons? {self.noButtons()} any_buttons? {self.anyButtons()}")
        #RobustRootLogger.debug(f"Needed keys: {self.keys!r}, user pressing {keys!r} Satisfied? {keysSatisfied} any_keys? {self.keys} exactKeys? {exactKeys}")
        return False

