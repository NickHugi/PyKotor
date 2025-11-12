"""This module handles classes relating to editing LIP files.

LIP (Lip Sync) files contain animation data for synchronizing character mouth movements
with voice-over audio. Each LIP file contains a series of keyframes that specify mouth
shapes (visemes) at specific timestamps, allowing the game engine to animate character
lips during dialogue playback.

References:
----------
    vendor/reone/include/reone/graphics/format/lipreader.h:29-46 - LipReader class
    vendor/reone/include/reone/graphics/lipanimation.h:24-47 - LipAnimation class
    vendor/reone/src/libs/graphics/format/lipreader.cpp:24-78 - LIP loading implementation
    vendor/KotOR_IO/KotOR_IO/File Formats/LIP.cs:14-163 - C# LIP implementation
    vendor/KotOR.js/src/resource/LIPObject.ts:23-348 - TypeScript LIP implementation
    vendor/KotOR.js/src/enums/resource/LIPShape.ts:11-28 - LIPShape enum definitions
    vendor/xoreos/src/aurora/lipfile.cpp:38-142 - LIP file handling

Binary Format:
-------------
    Header (16 bytes):
        Offset | Size | Type   | Description
        -------|------|--------|-------------
        0x00   | 4    | char[] | File Type ("LIP ")
        0x04   | 4    | char[] | File Version ("V1.0")
        0x08   | 4    | float  | Sound Length (duration in seconds)
        0x0C   | 4    | uint32 | Entry Count (number of keyframes)
    
    Keyframe Entry (5 bytes each):
        Offset | Size | Type   | Description
        -------|------|--------|-------------
        0x00   | 4    | float  | Time Stamp (seconds from start)
        0x04   | 1    | uint8  | Shape (mouth shape index, 0-15)
        
    Reference: reone/lipreader.cpp:24-78, KotOR_IO:42-56, KotOR.js:99-117
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING

from pykotor.resource.formats._base import ComparableMixin
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from collections.abc import Iterator


class LIPShape(IntEnum):
    """Represents different mouth shapes (visemes) for lip sync animation.
    
    These shapes correspond to visual phonemes used in lip-sync animation. Each shape
    represents a specific mouth position for speech sounds, based on the Preston Blair
    phoneme series adapted for KotOR's animation system. The game engine interpolates
    between shapes to create smooth lip movement during dialogue.
    
    References:
    ----------
        vendor/reone/include/reone/graphics/lipanimation.h:28 (shape field, uint8_t)
        vendor/KotOR_IO/KotOR_IO/File Formats/LIP.cs:124-163 - LipState enum
        vendor/KotOR.js/src/enums/resource/LIPShape.ts:11-28 - LIPShape enum
        vendor/KotOR.js/src/apps/forge/data/LIPShapeLabels.ts - Shape label definitions
        
    Binary Format:
    -------------
        Stored as uint8 (single byte) in keyframe entries
        Valid range: 0-15 (16 possible shapes)
        Shape 0 is typically NEUTRAL/rest position
        
    Shape Definitions:
    -----------------
        NEUTRAL = 0: Neutral/rest position (used for pauses)
            Reference: KotOR.js/LIPShape.ts:12 (EE = 0, but NEUTRAL typically used)
            Default shape when no speech is occurring
            
        EE = 1: Teeth slightly apart, corners wide (as in "see", "teeth")
            Reference: KotOR_IO/LIP.cs:127 (ee = 0x0)
            Reference: KotOR.js/LIPShape.ts:12 (EE = 0)
            Used for long 'e' sounds
            
        EH = 2: Mouth relaxed, slightly open (as in "get", "bet", "red")
            Reference: KotOR_IO/LIP.cs:129 (eh = 0x1)
            Reference: KotOR.js/LIPShape.ts:13 (EH = 1)
            Used for short 'e' sounds
            
        AH = 3: Mouth open (as in "father", "bat", "cat")
            Reference: KotOR_IO/LIP.cs:133 (ah = 0x3)
            Reference: KotOR.js/LIPShape.ts:15 (AH = 3)
            Used for 'a' sounds
            
        OH = 4: Rounded lips (as in "go", "boat", "or")
            Reference: KotOR_IO/LIP.cs:135 (oh = 0x4)
            Reference: KotOR.js/LIPShape.ts:16 (OH = 4)
            Used for 'o' sounds
            
        OOH = 5: Pursed lips (as in "too", "blue", "wheel")
            Reference: KotOR_IO/LIP.cs:137 (oo = 0x5)
            Reference: KotOR.js/LIPShape.ts:17 (OOH = 5)
            Used for 'u' and 'w' sounds
            
        Y = 6: Slight smile (as in "yes", "you")
            Reference: KotOR_IO/LIP.cs:139 (y = 0x6)
            Reference: KotOR.js/LIPShape.ts:18 (Y = 6)
            Used for 'y' sounds
            
        STS = 7: Teeth together (as in "stop", "sick", "nets")
            Reference: KotOR_IO/LIP.cs:141 (s = 0x7)
            Reference: KotOR.js/LIPShape.ts:19 (S = 7)
            Used for 's', 'z', 'ts' sounds
            
        FV = 8: Lower lip touching upper teeth (as in "five", "fish", "very")
            Reference: KotOR_IO/LIP.cs:143 (f = 0x8)
            Reference: KotOR.js/LIPShape.ts:20 (FV = 8)
            Used for 'f' and 'v' sounds
            
        NG = 9: Back of tongue up (as in "ring", "nacho", "running")
            Reference: KotOR_IO/LIP.cs:145 (n = 0x9)
            Reference: KotOR.js/LIPShape.ts:21 (NNG = 9)
            Used for 'n' and 'ng' sounds
            
        TH = 10: Tongue between teeth (as in "thin", "think", "that")
            Reference: KotOR_IO/LIP.cs:147 (th = 0xA)
            Reference: KotOR.js/LIPShape.ts:22 (TH = 10)
            Used for 'th' sounds
            
        MPB = 11: Lips pressed together (as in "bump", "moose", "pop", "book")
            Reference: KotOR_IO/LIP.cs:149 (m = 0xB)
            Reference: KotOR.js/LIPShape.ts:23 (MBP = 11)
            Used for 'm', 'p', 'b' sounds
            
        TD = 12: Tongue up (as in "top", "table", "door")
            Reference: KotOR_IO/LIP.cs:151 (t = 0xC)
            Reference: KotOR.js/LIPShape.ts:24 (TD = 12)
            Used for 't' and 'd' sounds
            
        SH = 13: Rounded but relaxed (as in "measure", "cheese", "jee")
            Reference: KotOR_IO/LIP.cs:153 (sh = 0xD)
            Reference: KotOR.js/LIPShape.ts:25 (SH = 13)
            Used for 'sh', 'ch', 'j', 'zh' sounds
            
        L = 14: Tongue forward (as in "lip", "read")
            Reference: KotOR_IO/LIP.cs:155 (l = 0xE)
            Reference: KotOR.js/LIPShape.ts:26 (LR = 14)
            Used for 'l' and 'r' sounds
            
        KG = 15: Back of tongue raised (as in "kick", "green", "key", "he")
            Reference: KotOR_IO/LIP.cs:157 (k = 0xF)
            Reference: KotOR.js/LIPShape.ts:27 (KG = 15)
            Used for 'k', 'g', 'h' sounds
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




class LIP(ComparableMixin):
    """Represents a LIP (Lip Sync) file containing mouth animation data.
    
    LIP files synchronize character mouth movements with voice-over audio during dialogue.
    They contain a series of keyframes that specify mouth shapes (visemes) at specific
    timestamps. The game engine interpolates between keyframes to create smooth lip
    animation that matches the spoken dialogue.
    
    References:
    ----------
        vendor/reone/include/reone/graphics/lipanimation.h:24-47 - LipAnimation class
        vendor/reone/src/libs/graphics/format/lipreader.cpp:24-78 - LIP loading
        vendor/KotOR_IO/KotOR_IO/File Formats/LIP.cs:14-163 - Complete LIP implementation
        vendor/KotOR.js/src/resource/LIPObject.ts:23-348 - LIPObject class
        vendor/xoreos/src/aurora/lipfile.h:40-95 - LIPFile class
        
    Attributes:
    ----------
        length: Total duration of lip animation in seconds
            Reference: reone/lipanimation.h:40 (length() method)
            Reference: KotOR_IO/LIP.cs:85 (SoundLength property)
            Reference: KotOR.js/LIPObject.ts:32 (duration field)
            Reference: KotOR.js/LIPObject.ts:106 (readSingle for duration)
            Matches the duration of the associated voice-over WAV file
            Stored as float32 in binary format (4 bytes)
            Used to determine animation playback bounds
            
        frames: List of keyframes defining mouth shapes at specific times
            Reference: reone/lipanimation.h:41 (keyframes() method)
            Reference: KotOR_IO/LIP.cs:117 (Entries list)
            Reference: KotOR.js/LIPObject.ts:29 (keyframes array)
            Reference: KotOR.js/LIPObject.ts:112-116 (keyframe reading loop)
            Each keyframe contains a timestamp and mouth shape
            Keyframes must be sorted by time for proper animation playback
            Game engine interpolates between consecutive keyframes
    """

    BINARY_TYPE = ResourceType.LIP
    FILE_HEADER = "LIP V1.0"
    COMPARABLE_FIELDS = ("length",)
    COMPARABLE_SEQUENCE_FIELDS = ("frames",)

    def __init__(self) -> None:
        # vendor/reone/include/reone/graphics/lipanimation.h:40
        # vendor/KotOR_IO/KotOR_IO/File Formats/LIP.cs:85
        # vendor/KotOR.js/src/resource/LIPObject.ts:32,106
        # Total duration of lip animation (matches voice-over length)
        self.length: float = 0.0
        
        # vendor/reone/include/reone/graphics/lipanimation.h:41
        # vendor/KotOR_IO/KotOR_IO/File Formats/LIP.cs:117
        # vendor/KotOR.js/src/resource/LIPObject.ts:29,112-116
        # List of keyframes (timestamp + mouth shape pairs)
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

@dataclass
class LIPKeyFrame(ComparableMixin):
    """A single keyframe in a LIP animation sequence.
    
    Each keyframe specifies a mouth shape at a specific timestamp. The game engine
    interpolates between consecutive keyframes to create smooth lip movement during
    dialogue playback. Keyframes are sorted by time to enable efficient lookup and
    interpolation.
    
    References:
    ----------
        vendor/reone/include/reone/graphics/lipanimation.h:26-29 - Keyframe struct
        vendor/KotOR_IO/KotOR_IO/File Formats/LIP.cs:90-111 - LipEntry struct
        vendor/KotOR.js/src/interface/resource/ILIPKeyFrame.ts - ILIPKeyFrame interface
        vendor/KotOR.js/src/resource/LIPObject.ts:113-115 (keyframe reading)
        
    Binary Format (5 bytes):
    -----------------------
        Offset | Size | Type   | Description
        -------|------|--------|-------------
        0x00   | 4    | float  | Time Stamp (seconds from start of audio)
        0x04   | 1    | uint8  | Shape (mouth shape index, 0-15)
        
        Reference: reone/lipreader.cpp:56-62, KotOR_IO:53-54, KotOR.js:114-115
    
    Attributes:
    ----------
        time: Timestamp when this keyframe occurs (seconds from start)
            Reference: reone/lipanimation.h:27 (time field, float)
            Reference: KotOR_IO/LIP.cs:95 (TimeStamp property)
            Reference: KotOR.js/LIPObject.ts:114 (readSingle for time)
            Stored as float32 in binary format (4 bytes)
            Must be >= 0.0 and <= animation length
            Keyframes should be sorted by time for proper playback
            
        shape: Mouth shape (viseme) for this keyframe
            Reference: reone/lipanimation.h:28 (shape field, uint8_t)
            Reference: KotOR_IO/LIP.cs:99 (State property, LipState enum)
            Reference: KotOR.js/LIPObject.ts:115 (readByte for shape)
            Stored as uint8 in binary format (1 byte)
            Valid range: 0-15 (16 possible shapes, see LIPShape enum)
            Index into character's "talk" animation keyframes
            Game engine uses this to select the appropriate mouth mesh pose
    """
    
    time: float
    shape: LIPShape
    COMPARABLE_FIELDS = ("time", "shape")

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

    def __lt__(self, other: LIPKeyFrame) -> bool:
        """Enable sorting keyframes by time."""
        return self.time < other.time