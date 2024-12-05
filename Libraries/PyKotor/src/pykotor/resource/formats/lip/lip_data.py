"""This module handles classes relating to editing LIP files."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING, Any, Callable

from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from collections.abc import Iterator


class LIPShape(IntEnum):
    """Represents different mouth shapes for lip sync animation.

    These shapes correspond to visemes (visual phonemes) used in lip-sync animation.
    Each shape represents a specific mouth position for speech sounds.

    The mapping is based on Preston Blair phoneme series with some modifications
    for KotOR's specific needs.


    """
    NEUTRAL = 0    # Neutral/rest position (used for pauses)
    EE = 1        # Teeth slightly apart, corners wide (as in "see")
    EH = 2        # Mouth relaxed, slightly open (as in "get")
    AH = 3        # Mouth open (as in "father")
    OH = 4        # Rounded lips (as in "go")
    OOH = 5       # Pursed lips (as in "too")
    Y = 6         # Slight smile (as in "yes")
    STS = 7       # Teeth together (as in "stop")
    FV = 8        # Lower lip touching upper teeth (as in "five")
    NG = 9        # Back of tongue up (as in "ring")
    TH = 10       # Tongue between teeth (as in "thin")
    MPB = 11      # Lips pressed together (as in "bump")
    TD = 12       # Tongue up (as in "top")
    SH = 13       # Rounded but relaxed (as in "measure")
    L = 14        # Tongue forward (as in "lip")
    KG = 15       # Back of tongue raised (as in "kick")

    @classmethod
    def from_phoneme(cls, phoneme: str) -> LIPShape:
        """Convert a phoneme to its corresponding lip shape.

        This helps with automatic lip sync generation from text/phonemes.
        """
        phoneme = phoneme.upper()
        mapping: dict[str, LIPShape] = {
            "AA": cls.AH,    # father
            "AE": cls.AH,    # cat
            "AH": cls.AH,    # but
            "AO": cls.OH,    # bought
            "AW": cls.AH,    # down
            "AY": cls.AH,    # bite
            "B": cls.MPB,    # be
            "CH": cls.SH,    # cheese
            "D": cls.TD,     # dee
            "DH": cls.TH,    # thee
            "EH": cls.EH,    # bet
            "ER": cls.EH,    # bird
            "EY": cls.EE,    # bait
            "F": cls.FV,     # fee
            "G": cls.KG,     # green
            "HH": cls.KG,    # he
            "IH": cls.EE,    # bit
            "IY": cls.EE,    # beet
            "JH": cls.SH,    # jee
            "K": cls.KG,     # key
            "L": cls.L,      # lee
            "M": cls.MPB,    # me
            "N": cls.NG,     # knee
            "NG": cls.NG,    # ping
            "OW": cls.OH,    # boat
            "OY": cls.OH,    # boy
            "P": cls.MPB,    # pee
            "R": cls.L,      # read
            "S": cls.STS,    # sea
            "SH": cls.SH,    # she
            "T": cls.TD,     # tea
            "TH": cls.TH,    # theta
            "UH": cls.OOH,   # book
            "UW": cls.OOH,   # boot
            "V": cls.FV,     # vee
            "W": cls.OOH,    # we
            "Y": cls.Y,      # yield
            "Z": cls.STS,    # zee
            "ZH": cls.SH,    # seizure
            " ": cls.NEUTRAL,  # pause
            "-": cls.NEUTRAL,  # pause
        }
        return mapping.get(phoneme, cls.NEUTRAL)


@dataclass
class LIPKeyFrame:
    """A keyframe for a lip animation.

    Attributes:
    ----------
        time: The time the keyframe animation occurs (in seconds)
        shape: The mouth shape for this keyframe
    """
    time: float
    shape: LIPShape

    def __lt__(self, other: LIPKeyFrame) -> bool:
        """Enable sorting keyframes by time."""
        return self.time < other.time

    def interpolate(self, other: LIPKeyFrame, time: float) -> tuple[LIPShape, LIPShape, float]:
        """Calculate interpolation between this keyframe and another.

        Args:
        ----
            other: The next keyframe to interpolate towards
            time: The current time to interpolate at

        Returns:
        -------
            Tuple of (left shape, right shape, interpolation factor)
        """
        if self == other:
            return self.shape, other.shape, 0.0

        factor = (time - self.time) / (other.time - self.time)
        factor = max(0.0, min(1.0, factor))  # Clamp between 0 and 1

        return self.shape, other.shape, factor


class LIP:
    """Represents the data of a LIP file.

    A LIP file contains lip-sync animation data, consisting of a series of
    keyframes that define mouth shapes at specific times.

    The animation system interpolates between keyframes to create smooth
    transitions between mouth shapes.

    Attributes:
    ----------
        length: The total duration of lip animation in seconds
        frames: The keyframes for the lip animation, sorted by time
    """

    BINARY_TYPE = ResourceType.LIP
    FILE_HEADER = "LIP V1.0"

    def __init__(self) -> None:
        self.length: float = 0.0
        self.frames: list[LIPKeyFrame] = []

    def __iter__(self) -> Iterator[LIPKeyFrame]:
        """Iterates through the stored list of keyframes yielding the LIPKeyFrame each iteration."""
        yield from self.frames

    def __len__(self) -> int:
        """Returns the number of stored keyframes."""
        return len(self.frames)

    def __getitem__(self, item: int) -> LIPKeyFrame:
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
        return self.frames[item]

    def add(self, time: float, shape: LIPShape) -> None:
        """Adds a new keyframe and maintains time-based sorting.

        Args:
        ----
            time: The keyframe start time in seconds
            shape: The mouth shape for the keyframe

        The keyframes are automatically sorted by time to ensure proper animation playback.
        If a keyframe already exists at the given time, it will be replaced.
        """
        # Remove any existing keyframe at this time
        self.frames = [f for f in self.frames if abs(f.time - time) > 0.0001]

        frame = LIPKeyFrame(time, shape)
        self.frames.append(frame)
        self.frames.sort()  # Sort by time
        self.length = max(self.length, time)

    def remove(self, index: int) -> None:
        """Remove a keyframe at the specified index.

        Args:
        ----
            index: Index of the keyframe to remove

        Raises:
        ------
            IndexError: If index is out of range
        """
        if 0 <= index < len(self.frames):
            del self.frames[index]
            if self.frames:
                self.length = max(frame.time for frame in self.frames)
            else:
                self.length = 0.0

    def get_shapes(self, time: float) -> tuple[LIPShape, LIPShape, float] | None:
        """Gets interpolated shape data for a given time.

        Args:
        ----
            time: The time to get shapes for, in seconds

        Returns:
        -------
            A tuple containing:
            - Left shape (the previous keyframe's shape)
            - Right shape (the next keyframe's shape)
            - Interpolation factor between the shapes (0.0 to 1.0)
            Returns None if no valid keyframes exist for the given time.

        The interpolation factor can be used to blend between the two shapes
        for smooth animation. A factor of 0.0 means use the left shape entirely,
        while 1.0 means use the right shape entirely.
        """
        if not self.frames:
            return None

        # Handle time before first keyframe
        if time <= self.frames[0].time:
            return self.frames[0].shape, self.frames[0].shape, 0.0

        # Handle time after last keyframe
        if time >= self.frames[-1].time:
            return self.frames[-1].shape, self.frames[-1].shape, 0.0

        # Find surrounding keyframes
        left_frame: LIPKeyFrame = self.frames[0]
        right_frame: LIPKeyFrame = self.frames[0]

        for frame in self.frames:
            if time > frame.time:
                left_frame = frame
            if time <= frame.time:
                right_frame = frame
                break


        return left_frame.interpolate(right_frame, time)

    def get(self, index: int) -> LIPKeyFrame | None:
        """Returns the keyframe at the specified index if it exists.

        Args:
        ----
            index: The index of the keyframe.

        Returns:
        -------
            The corresponding LIPKeyFrame object or None if index is out of bounds.
        """
        return self.frames[index] if 0 <= index < len(self.frames) else None

    def compare(self, other: LIP, log_func: Callable[[str], Any] = print) -> bool:
        """Compare this LIP with another LIP file.

        Args:
        ----
            other: The other LIP file to compare against
            log_func: Function to use for logging differences

        Returns:
        -------
            True if the LIPs are identical, False if there are differences

        This is useful for verifying that LIP files are identical after
        conversion between formats or after editing.
        """
        ret = True

        # Check for differences in the length attribute
        if abs(self.length - other.length) > 0.0001:  # Use small epsilon for float comparison
            log_func(f"Length mismatch: '{self.length}' --> '{other.length}'")
            ret = False

        # Check for keyframe mismatches
        old_frames = len(self)
        new_frames = len(other)

        if old_frames != new_frames:
            log_func(f"Keyframe count mismatch: {old_frames} --> {new_frames}")
            ret = False

        # Compare individual keyframes
        for i in range(min(old_frames, new_frames)):
            old_keyframe = self[i]
            new_keyframe = other[i]

            if abs(old_keyframe.time - new_keyframe.time) > 0.0001:
                log_func(f"Time mismatch at keyframe {i}: '{old_keyframe.time}' --> '{new_keyframe.time}'")
                ret = False

            if old_keyframe.shape != new_keyframe.shape:
                log_func(f"Shape mismatch at keyframe {i}: '{old_keyframe.shape.name}' --> '{new_keyframe.shape.name}'")
                ret = False

        return ret

    def get_shape_at_time(self, time: float) -> LIPShape | None:
        """Get the interpolated shape at a specific time.

        This is a convenience method that returns just the appropriate shape
        for the given time, handling interpolation internally.

        Args:
        ----
            time: The time to get the shape for

        Returns:
        -------
            The appropriate LIPShape for the given time, or None if no animation exists
        """
        shapes: tuple[LIPShape, LIPShape, float] | None = self.get_shapes(time)
        if not shapes:
            return None

        left_shape, right_shape, factor = shapes

        # For now, just return the shape we're closest to
        # In a full implementation, this would do proper shape interpolation
        return right_shape if factor > 0.5 else left_shape

    def clear(self) -> None:
        """Clear all keyframes from the animation."""
        self.frames.clear()
        self.length = 0.0

    def validate(self) -> list[str]:
        """Validate the LIP data for common issues.

        Returns:
        -------
            List of validation error messages, empty if valid
        """
        errors: list[str] = []

        if not self.frames:
            errors.append("No keyframes defined")
            return errors

        # Check for negative times
        for frame in self.frames:
            if frame.time < 0:
                errors.append(f"Negative time value: {frame.time}")

        # Check for proper ordering
        last_time = -1
        for frame in self.frames:
            if frame.time < last_time:
                errors.append(f"Keyframes out of order: {frame.time} after {last_time}")
            last_time: float = frame.time

        # Check length matches last keyframe
        if self.frames and abs(self.length - self.frames[-1].time) > 0.0001:
            errors.append(f"Length ({self.length}) doesn't match last keyframe time ({self.frames[-1].time})")

        return errors
