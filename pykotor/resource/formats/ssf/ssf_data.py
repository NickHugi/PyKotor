"""
This module handles classes relating to editing SSF files.
"""

from __future__ import annotations

from enum import IntEnum
from typing import List, Optional

from pykotor.resource.type import ResourceType


class SSF:
    """
    Represents the data stored in a SSF file.
    """

    BINARY_TYPE = ResourceType.SSF

    def __init__(
            self
    ):
        self._sounds: List[int] = [-1] * 28

    def __getitem__(
            self,
            item
    ):
        """
        Returns the stringref for the specified sound.
        """
        if not isinstance(item, SSFSound):
            return NotImplemented
        return self._sounds[item]

    def reset(
            self
    ) -> None:
        """
        Sets all the sound stringrefs to -1.
        """
        for i in range(28):
            self._sounds[i] = -1

    def set(
            self,
            sound: SSFSound,
            stringref: int
    ) -> None:
        """
        Set the stringref for the specified sound.

        Args:
            sound: The sound.
            stringref: The new stringref for the sound.
        """
        self._sounds[sound] = stringref

    def get(
            self,
            sound: SSFSound
    ) -> Optional[int]:
        """
        Returns the stringref for the specified sound.

        Args:
            sound: The sound.

        Returns:
            The corresponding stringref.
        """
        return self._sounds[sound]


class SSFSound(IntEnum):
    BATTLE_CRY_1 = 0
    BATTLE_CRY_2 = 1
    BATTLE_CRY_3 = 2
    BATTLE_CRY_4 = 3
    BATTLE_CRY_5 = 4
    BATTLE_CRY_6 = 5
    SELECT_1 = 6
    SELECT_2 = 7
    SELECT_3 = 8
    ATTACK_GRUNT_1 = 9
    ATTACK_GRUNT_2 = 10
    ATTACK_GRUNT_3 = 11
    PAIN_GRUNT_1 = 12
    PAIN_GRUNT_2 = 13
    LOW_HEALTH = 14
    DEAD = 15
    CRITICAL_HIT = 16
    TARGET_IMMUNE = 17
    LAY_MINE = 18
    DISARM_MINE = 19
    BEGIN_STEALTH = 20
    BEGIN_SEARCH = 21
    BEGIN_UNLOCK = 22
    UNLOCK_FAILED = 23
    UNLOCK_SUCCESS = 24
    SEPARATED_FROM_PARTY = 25
    REJOINED_PARTY = 26
    POISONED = 27
