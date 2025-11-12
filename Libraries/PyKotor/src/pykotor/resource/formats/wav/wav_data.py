"""This module handles classes relating to editing WAV files.

WAV files in KotOR can be voice-over (VO) or sound effects (SFX) with various encodings.

References:
----------
    vendor/reone/src/libs/resource/format/wavreader.cpp - WAV parsing
    vendor/SithCodec - Audio codec for KotOR WAV handling
    vendor/SWKotOR-Audio-Encoder - Audio encoding tools
    vendor/xoreos-tools/src/sound/audiostream.cpp - Audio stream handling
    vendor/KotOR.js/src/audio/AudioEngine.ts - Audio playback
    vendor/reone/src/libs/audio/ - Audio system implementation
    Note: KotOR WAV files may have obfuscation headers requiring deobfuscation (see tools.sound)
"""

from __future__ import annotations

from enum import Enum, auto

from pykotor.resource.type import ResourceType


class WaveEncoding(Enum):
    """Wave encoding types used by Bioware."""
    PCM = 0x01
    ADPCM = 0x11  # Not supported by webkit, must be converted to PCM


class WAVType(Enum):
    """The type of WAV file."""
    VO = auto()  # Voice over WAV
    SFX = auto()   # Sound effects WAV


class WAV:
    """Represents a WAV file.

    Attributes:
    ----------
        wav_type: The WAV type (standard or bioware)
        encoding: The wave encoding type
        channels: Number of audio channels
        sample_rate: Audio sample rate
        bits_per_sample: Bits per audio sample
        block_align: Block alignment
        data: The raw audio data
    """

    BINARY_TYPE = ResourceType.WAV

    def __init__(
        self,
        wav_type: WAVType = WAVType.VO,
        encoding: WaveEncoding = WaveEncoding.PCM,
        channels: int = 1,
        sample_rate: int = 44100,
        bits_per_sample: int = 16,
        bytes_per_sec: int = 0,
        block_align: int = 0,
        data: bytes | None = None,
    ):
        self.wav_type: WAVType = wav_type
        self.encoding: WaveEncoding = encoding
        self.channels: int = channels
        self.sample_rate: int = sample_rate
        self.bits_per_sample: int = bits_per_sample
        self.bytes_per_sec: int = bytes_per_sec
        self.block_align: int = block_align or (channels * bits_per_sample // 8)
        self.data: bytes = data if data is not None else b""

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, WAV):
            return NotImplemented
        return (
            self.wav_type == other.wav_type
            and self.encoding == other.encoding
            and self.channels == other.channels
            and self.sample_rate == other.sample_rate
            and self.bits_per_sample == other.bits_per_sample
            and self.block_align == other.block_align
            and self.data == other.data
        )

    def __hash__(self):
        return hash((self.wav_type, self.encoding, self.channels, self.sample_rate, self.bits_per_sample, self.block_align, self.data))
