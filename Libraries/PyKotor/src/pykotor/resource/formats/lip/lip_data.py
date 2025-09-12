"""This module handles classes relating to editing LIP files."""

from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

from pykotor.resource.formats._base import ComparableMixin
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from collections.abc import Iterator


class LIP(ComparableMixin):
    """Represents the data of a LIP file.

    Attributes:
    ----------
        length: The total duration of lip animation.
        frames: The keyframes for the lip animation.
    """

    BINARY_TYPE = ResourceType.LIP
    COMPARABLE_FIELDS = ("length",)
    COMPARABLE_SEQUENCE_FIELDS = ("frames",)

    def __init__(
        self,
    ):
        self.length: float = 0.0
        self.frames: list[LIPKeyFrame] = []

    def __iter__(
        self,
    ) -> Iterator[LIPKeyFrame]:
        """Iterates through the stored list of keyframes yielding the LIPKeyFrame each iteration."""
        yield from self.frames

    def __len__(
        self,
    ):
        """Returns the number of stored keyframes."""
        return len(self.frames)

    def __getitem__(
        self,
        item,  # noqa: ANN001
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

    # compare is provided by ComparableMixin


# mapping in LipSyncEditor is not very accurate. for example, shape 0 is neutral, not EE,
# meaning pauses are not properly represented when using LipSyncEditor. shape 15 is too open to be KG and etc.
# https://imgur.com/a/LIRZ8B1
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


class LIPKeyFrame(ComparableMixin):
    COMPARABLE_FIELDS = ("time", "shape")
    """A keyframe for a lip animation.

    Attributes:
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
