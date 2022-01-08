"""
This module handles classes relating to editing LIP files.
"""
from __future__ import annotations

from enum import IntEnum
from typing import List, Optional


class LIP:
    """
    Represents the data of a LIP file.

    Attributes:
        length: The total duration of lip animation.
        frames: The keyframes for the lip animation.
    """

    def __init__(self):
        self.length: float = 0.0
        self.frames: List[LIPKeyFrame] = []

    def __iter__(self):
        """
        Iterates through the stored list of keyframes yielding the LIPKeyFrame each iteration.
        """
        for frame in self.frames:
            yield frame

    def __len__(self):
        """
        Returns the number of stored keyframes.
        """
        return len(self.frames)

    def __getitem__(self, item):
        """
        Returns a keyframe from the specified index.

        Args:
            item: The index of the keyframe.

        Raises:
            IndexError: If the index is out of bounds.

        Returns:
            The corresponding LIPKeyFrame object.
        """
        if not isinstance(item, int):
            return NotImplemented
        return self.frames[item]

    def add(self, time: float, shape: LIPShape) -> None:
        """
        Adds a new keyframe.

        Args:
            time: The keyframe start time.
            shape: The mouth shape for the keyframe.
        """
        self.frames.append(LIPKeyFrame(time, shape))

    def get(self, index: int) -> Optional[LIPKeyFrame]:
        """
        Returns the keyframe at the specified index if it exists, otherwise returns None.

        Args:
            index: The index of the keyframe.

        Returns:
            The corresponding LIPKeyFrame object or None.
        """
        return self.frames[index] if index < len(self.frames) else None


class LIPShape(IntEnum):
    EE = 0
    EH = 1
    SCHWA = 2
    AH = 3
    OH = 4
    OOH = 5
    Y = 6
    STS = 7
    FV = 8
    NNG = 9
    TH = 10
    MPB = 11
    TD = 12
    JSH = 13
    L = 14
    KG = 15


class LIPKeyFrame:
    """
    A keyframe for a lip animation.

    Attributes:
        time: The time the keyframe animation occurs.
        shape: The mouth shape.
    """

    def __init__(self, time: float, shape: LIPShape):
        self.time: float = time
        self.shape: LIPShape = shape
