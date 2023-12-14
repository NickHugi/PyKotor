"""This module handles classes relating to editing VIS files."""
from __future__ import annotations

from copy import copy, deepcopy
from typing import Any, Generator

from pykotor.resource.type import ResourceType


class VIS:
    """Represents a VIS file."""

    BINARY_TYPE = ResourceType.VIS

    def __init__(
        self,
    ) -> None:
        self._rooms: set[str] = set()
        self._visibility: dict[str, set[str]] = {}

    def __iter__(
        self,
    ) -> Generator[tuple[str, set[str]], Any, None]:
        for observer, observed in self._visibility.items():
            yield observer, deepcopy(observed)

    def all_rooms(
        self,
    ) -> set[str]:
        """Returns a copy of the set of rooms.

        Args:
        ----
            self: The class instance

        Returns:
        -------
            set[str]: A copy of the set of rooms

        Processing Logic:
        ----------------
            - Creates a copy of the internal _rooms set to avoid direct manipulation of the original set
            - The copy() method is used to make a shallow copy of the set
            - This allows returning the rooms set without allowing external modification of the internal state
            - Returns the copy of the rooms set.
        """
        return copy(self._rooms)

    def add_room(
        self,
        model: str,
    ) -> None:
        """Adds a room. If an room already exists, it is ignored; no error is thrown.

        Args:
        ----
            model: The name or model of the room.
        """
        model = model.lower()

        if model not in self._rooms:
            self._visibility[model] = set()

        self._rooms.add(model)

    def remove_room(
        self,
        model: str,
    ) -> None:
        """Removes a room. If a room does not exist, it is ignored; no error is thrown.

        Args:
        ----
            model: The name or model of the room.
        """
        lower_model: str = model.lower()

        for room in self._rooms:
            if lower_model in self._visibility[room]:
                self._visibility[room].remove(lower_model)

        if lower_model in self._rooms:
            self._rooms.remove(lower_model)

    def rename_room(
        self,
        old: str,
        new: str,
    ) -> None:
        """Renames a room.

        Args:
        ----
            old (str): Old room name
            new (str): New room name

        Processing Logic:
        ----------------
            - Lowercase old and new room names
            - Check if old and new names are the same
            - Remove old room name from rooms list
            - Add new room name to rooms list
            - Copy visibility of old room to new room
            - Delete visibility of old room
            - Replace old room name with new in other rooms' visibility lists.
        """
        old = old.lower()
        new = new.lower()

        if old == new:
            return

        self._rooms.remove(old)
        self._rooms.add(new)

        self._visibility[new] = copy(self._visibility[old])
        del self._visibility[old]

        for other in self._visibility:
            if other != new and old in self._visibility[other]:
                self._visibility[other].remove(old)
                self._visibility[other].add(new)

    def room_exists(
        self,
        model: str,
    ) -> bool:
        """Returns true if the specified room exists.

        Returns
        -------
            True if the room exists.
        """
        model.lower()
        return model in self._rooms

    def set_visible(
        self,
        when_inside: str,
        show: str,
        visible: bool,
    ) -> None:
        """Sets the visibility of a specified room based off when viewing from another specified room.

        Args:
        ----
            when_inside: The room of the observer.
            show: The observed room.
            visible: If the observed room is visible.
        """
        when_inside = when_inside.lower()
        show = show.lower()

        if when_inside not in self._rooms or show not in self._rooms:
            msg = "One of the specified rooms does not exist."
            raise ValueError(msg)

        if visible:
            self._visibility[when_inside].add(show)
        elif show in self._visibility[when_inside]:
            self._visibility[when_inside].remove(show)

    def get_visible(
        self,
        when_inside: str,
        show: str,
    ) -> bool:
        """Returns true if the observed room is visible from the observing room.

        Args:
        ----
            when_inside: The room of the observer.
            show: The observed room.

        Returns:
        -------
            True if the room is visible.
        """
        when_inside = when_inside.lower()
        show = show.lower()

        if when_inside not in self._rooms or show not in self._rooms:
            msg = "One of the specified rooms does not exist."
            raise ValueError(msg)

        return show in self._visibility[when_inside]

    def set_all_visible(
        self,
    ) -> None:
        """Sets all rooms visible from each other.

        Processing Logic:
        ----------------
            - Loop through each room in self._rooms
            - For that room, loop through all other rooms
            - Set the visibility between the current room and other room to True.
        """
        for when_inside in self._rooms:
            for show in [room for room in self._rooms if room != when_inside]:
                self.set_visible(when_inside, show, visible=True)
