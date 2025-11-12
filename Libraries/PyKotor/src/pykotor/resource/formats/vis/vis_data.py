"""This module handles classes relating to editing VIS files.

VIS (Visibility) files define which rooms are visible from other rooms in a module.
This is used for occlusion culling optimization - the game engine only renders rooms
that are marked as visible from the player's current room. VIS files are ASCII text
files with a simple format: parent room names followed by indented child room names.

References:
----------
    vendor/reone/include/reone/resource/format/visreader.h:28-39 - VisReader class
    vendor/reone/src/libs/resource/format/visreader.cpp:27-51 - VIS loading implementation
    vendor/KotOR.js/src/resource/VISObject.ts:33-276 - TypeScript VIS implementation
    vendor/KotOR.js/src/interface/module/IVISRoom.ts - IVISRoom interface
    vendor/xoreos/src/aurora/visfile.cpp:38-142 - VIS file handling

ASCII Format:
------------
    Parent Room Line:
        room_name number_of_child_rooms
        Example: "room001 3"
        
    Child Room Lines (indented with 2 spaces):
          child_room_name
          child_room_name
        Example:
          room002
          room003
          room004
    
    Format Rules:
        - Parent rooms start at column 0
        - Child rooms are indented with exactly 2 spaces
        - Room names are case-insensitive (stored lowercase)
        - Empty lines are ignored
        - Whitespace is trimmed from room names
        
    Reference: reone/visreader.cpp:41-51, KotOR.js/VISObject.ts:71-126
"""

from __future__ import annotations

from copy import copy, deepcopy
from typing import TYPE_CHECKING, Any

from pykotor.resource.formats._base import ComparableMixin
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from collections.abc import Generator


class VIS(ComparableMixin):
    """Represents a VIS (Visibility) file defining room visibility relationships.
    
    VIS files optimize rendering by specifying which rooms are visible from each
    parent room. When the player is in a room, only rooms marked as visible in
    the VIS file are rendered. This prevents rendering rooms that are occluded
    by walls or geometry, improving performance.
    
    References:
    ----------
        vendor/reone/include/reone/resource/format/visreader.h:32 (visibility() method)
        vendor/reone/src/libs/resource/format/visreader.cpp:35 (_visibility map)
        vendor/KotOR.js/src/resource/VISObject.ts:34 (rooms Map)
        vendor/xoreos/src/aurora/visfile.h:40-95 - VISFile class
        
    Attributes:
    ----------
        _rooms: Set of all room names defined in this VIS file
            Reference: reone/visreader.cpp:46-49 (room name processing)
            Reference: KotOR.js/VISObject.ts:34,118 (rooms Map, room.name)
            Room names are stored lowercase for case-insensitive comparison
            Each room name corresponds to a room model/area in the module
            Used to validate room existence before setting visibility
            
        _visibility: Dictionary mapping observer rooms to sets of visible rooms
            Reference: reone/visreader.cpp:49 (_visibility.insert)
            Reference: KotOR.js/VISObject.ts:99 (currentRoom.rooms array)
            Key: Observer room name (room player is currently in)
            Value: Set of room names visible from the observer room
            If room A is in _visibility[room B], then room A is visible from room B
            Used by game engine for occlusion culling optimization
    """

    BINARY_TYPE = ResourceType.VIS
    COMPARABLE_SET_FIELDS = ("_rooms",)
    COMPARABLE_FIELDS = ("_visibility",)

    def __init__(
        self,
    ):
        # vendor/reone/src/libs/resource/format/visreader.cpp:46-49
        # vendor/KotOR.js/src/resource/VISObject.ts:34,118
        # Set of all room names (stored lowercase for case-insensitive comparison)
        self._rooms: set[str] = set()
        
        # vendor/reone/src/libs/resource/format/visreader.cpp:49
        # vendor/KotOR.js/src/resource/VISObject.ts:99
        # Dictionary: observer room -> set of visible rooms
        # Used for occlusion culling (only render visible rooms)
        self._visibility: dict[str, set[str]] = {}

    def __eq__(self, other):
        if not isinstance(other, VIS):
            return NotImplemented
        return self._rooms == other._rooms and self._visibility == other._visibility

    def __hash__(self):
        return hash((
            tuple(sorted(self._rooms)),
            tuple(sorted((k, tuple(sorted(v))) for k, v in self._visibility.items())),
        ))

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
    ):
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
    ):
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
    ):
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

        Returns:
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
    ):
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
    ):
        """Sets all rooms visible from each other.

        Processing Logic:
        ----------------
            - Loop through each room in self._rooms
            - For that room, loop through all other rooms
            - Set the visibility between the current room and other room to True.
        """
        for when_inside in self._rooms:
            for show in (room for room in self._rooms if room != when_inside):
                self.set_visible(when_inside, show, visible=True)
