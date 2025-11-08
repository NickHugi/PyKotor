from __future__ import annotations

from typing import Set, Tuple, Union

from loggerplus import RobustLogger
from qtpy.QtCore import Qt

from toolset.utils.misc import get_qt_button_string, get_qt_key_string

Bind = Tuple[Set[Qt.Key], Union[Set[Qt.MouseButton], None]]


class ControlItem:
    def __init__(
        self,
        bind: Bind,
    ):
        self.keys: set[Qt.Key] = bind[0]
        self.mouse: set[Qt.MouseButton] | None = bind[1]

    def satisfied(
        self,
        buttons: set[Qt.MouseButton],  # Do NOT send None here!
        keys: set[Qt.Key],
        *,
        exact_keys_and_buttons: bool = False,
        debug_log: bool = False,
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
        no_buttons: bool = self.mouse is None
        any_buttons: bool = self.mouse is not None and len(self.mouse) == 0
        any_keys: bool = len(self.keys) == 0
        if exact_keys_and_buttons:
            mouse_equal: bool = self.mouse == buttons
            mouse_satisfied: bool = no_buttons or any_buttons or mouse_equal
        else:
            mouse_subset = True if self.mouse is None else self.mouse.issubset(buttons)
            mouse_satisfied = no_buttons or any_buttons or mouse_subset

        if exact_keys_and_buttons:
            keys_equal: bool = self.keys == keys
            keys_satisfied: bool = any_keys or keys_equal
        else:
            keys_subset: bool = self.keys.issubset(keys)
            keys_satisfied: bool = any_keys or keys_subset

        if not debug_log:
            return bool(mouse_satisfied and keys_satisfied)
        needed_mouse: list[str] = [get_qt_button_string(btn) for btn in iter(self.mouse)] if self.mouse is not None else ["None"]
        user_pressing_mouse: list[str] = [get_qt_button_string(btn) for btn in iter(buttons)]
        needed_keys: list[str] = [get_qt_key_string(key) for key in iter(self.keys)]
        user_pressing_keys: list[str] = [get_qt_key_string(key) for key in iter(keys)]

        RobustLogger().debug(
            f"Needed mouse: {needed_mouse}, user pressing {user_pressing_mouse}. Satisfied? {mouse_satisfied} no_buttons? {no_buttons} any_buttons? {any_buttons}"
        )  # noqa: E501
        RobustLogger().debug(
            f"Needed keys: {needed_keys}, user pressing {user_pressing_keys} Satisfied? {keys_satisfied} any_keys? {any_keys} exactKeys? {exact_keys_and_buttons}"
        )  # noqa: E501

        return bool(mouse_satisfied and keys_satisfied)


class ControlGroup:
    def __init__(
        self,
        *controls: ControlItem,
    ):
        self.controls: list[ControlItem] = list(controls)

    def satisfied(
        self,
        buttons: set[Qt.MouseButton],  # Do NOT send None here!
        keys: set[Qt.Key],
        *,
        exact_keys_and_buttons: bool = False,
        debug_log: bool = False,
    ) -> bool:
        return any(
            control.satisfied(
                buttons,
                keys,
                exact_keys_and_buttons=exact_keys_and_buttons,
                debug_log=debug_log,
            )
            for control in self.controls
        )
