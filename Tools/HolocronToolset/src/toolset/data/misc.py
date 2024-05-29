from __future__ import annotations

from typing import Set, Tuple, Union

from toolset.utils.misc import getQtButtonString, getQtKeyString
from utility.logger_util import RobustRootLogger

Bind = Tuple[Set[int], Union[Set[int], None]]


class ControlItem:
    def __init__(self, bind: Bind):
        self.keys: set[int] = bind[0]
        self.mouse: set[int] | None = bind[1]

    def noButtons(self) -> bool:
        return self.mouse is None

    def anyButtons(self) -> bool:
        return self.mouse is not None and len(self.mouse) == 0

    def anyKeys(self) -> bool:
        return len(self.keys) == 0

    def satisfied(
        self,
        buttons: set[int],  # Do NOT send None here!
        keys: set[int],
        *,
        exactKeysAndButtons: bool = False,
        debugLog: bool = False,
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
        mouseSatisfied = self.noButtons() or self.anyButtons() or (self.mouse == buttons if exactKeysAndButtons else self.mouse.issubset(buttons))
        keysSatisfied = self.anyKeys() or (self.keys == keys if exactKeysAndButtons else self.keys.issubset(keys))

        if mouseSatisfied and keysSatisfied:
            return True

        if debugLog:
            RobustRootLogger.debug(f"Needed mouse: {[getQtButtonString(btn) for btn in iter(self.mouse)] if self.mouse is not None else 'None'}, user pressing {[getQtButtonString(btn) for btn in iter(buttons)]}. Satisfied? {mouseSatisfied} no_buttons? {self.noButtons()} any_buttons? {self.anyButtons()}")
            RobustRootLogger.debug(f"Needed keys: {[getQtKeyString(key) for key in iter(self.keys)]}, user pressing {[getQtKeyString(key) for key in iter(keys)]} Satisfied? {keysSatisfied} any_keys? {self.anyKeys()} exactKeys? {exactKeysAndButtons}")
        return False

