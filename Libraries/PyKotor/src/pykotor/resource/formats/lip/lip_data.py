"""This module handles classes relating to editing LIP files."""
from __future__ import annotations

from enum import IntEnum
from typing import Any, Generator

from pykotor.resource.type import ResourceType


class LIP:
    """Represents the data of a LIP file.

    Attributes
    ----------
        length: The total duration of lip animation.
        frames: The keyframes for the lip animation.
    """

    BINARY_TYPE = ResourceType.LIP

    def __init__(
        self,
    ):
        self.length: float = 0.0
        self.frames: list[LIPKeyFrame] = []

    def __iter__(
        self,
    ) -> Generator[LIPKeyFrame, Any, None]:
        """Iterates through the stored list of keyframes yielding the LIPKeyFrame each iteration."""
        yield from self.frames

    def __len__(
        self,
    ):
        """Returns the number of stored keyframes."""
        return len(self.frames)

    def __getitem__(
        self,
        item,
    ) -> LIPKeyFrame:
        """Returns a keyframe from the specified index.

        Args:
        ----
            item: The index of the keyframe.

        Raises:
        ------
            IndexError: If the index is out of bounds.

        Returns:
        -------
            The corresponding LIPKeyFrame object.
        """
        return self.frames[item] if isinstance(item, int) else NotImplemented

    def add(
        self,
        time: float,
        shape: LIPShape,
    ):
        """Adds a new keyframe.

        Args:
        ----
            time: The keyframe start time.
            shape: The mouth shape for the keyframe.
        """
        self.frames.append(LIPKeyFrame(time, shape))

    def get(
        self,
        index: int,
    ) -> LIPKeyFrame | None:
        """Returns the keyframe at the specified index if it exists, otherwise returns None.

        Args:
        ----
            index: The index of the keyframe.

        Returns:
        -------
            The corresponding LIPKeyFrame object or None.
        """
        return self.frames[index] if index < len(self.frames) else None

    def compare(self, other: LIP, log_func=print) -> bool:
        ret = True

        # Check for differences in the length attribute
        if self.length != other.length:
            log_func(f"Length mismatch: '{self.length}' --> '{self.length}'")
            ret = False

        # Check for keyframe mismatches
        old_frames = len(self)
        new_frames = len(other)

        if old_frames != new_frames:
            log_func(f"Keyframe count mismatch: {old_frames} --> {new_frames}")
            ret = False

        # Compare individual keyframes
        for i in range(min(old_frames, new_frames)):
            old_keyframe: LIPKeyFrame = self[i]
            new_keyframe: LIPKeyFrame = other[i]

            if old_keyframe.time != new_keyframe.time:
                log_func(f"Time mismatch at keyframe {i}: '{old_keyframe.time}' --> '{new_keyframe.time}'")
                ret = False

            if old_keyframe.shape != new_keyframe.shape:
                log_func(f"Shape mismatch at keyframe {i}: '{old_keyframe.shape.name}' --> '{new_keyframe.shape.name}'")
                ret = False

        return ret


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
    """A keyframe for a lip animation.

    Attributes
    ----------
        time: The time the keyframe animation occurs.
        shape: The mouth shape.
    """

    def __init__(
        self,
        time: float,
        shape: LIPShape,
    ):
        self.time: float = time
        self.shape: LIPShape = shape
