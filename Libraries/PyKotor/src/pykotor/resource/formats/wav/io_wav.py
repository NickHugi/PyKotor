from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.wav.wav_data import WAV, WAVType, WaveEncoding
from pykotor.resource.type import ResourceReader, ResourceWriter, autoclose

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class WAVBinaryReader(ResourceReader):
    """Handles reading WAV binary data.
    
    WAV files store audio data. KotOR uses both standard RIFF/WAVE format (VO) and
    Bioware-encrypted format (SFX) with a 470-byte header.
    
    References:
    ----------
        vendor/reone/src/libs/audio/format/wavreader.cpp (WAV reading)
        vendor/SithCodec/src/codec.cpp (Audio codec implementation)
        vendor/SWKotOR-Audio-Encoder/ (Full audio encoder with GUI)
    
    Missing Features:
    ----------------
        - Full audio codec support (SithCodec/SWKotOR-Audio-Encoder provide encoding/decoding)
    """
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0x0,
        size: int = 0x0,
    ):
        super().__init__(source, offset, size)
        self._wav: WAV | None = None

    @autoclose
    def load(self, *, auto_close: bool = True) -> WAV:  # noqa: FBT001, FBT002, ARG002
        """Load WAV file.

        Returns:
        -------
            WAV: The loaded WAV object

        Processing Logic:
        ----------------
            - Check for Bioware header
            - Parse RIFF/WAVE format
            - Read wave format data
            - Read audio data
        """
        # Read first 4 bytes to check format
        riff_tag: bytes = self._reader.read_bytes(4)

        # Check if this is a Bioware WAV (needs deobfuscation)
        if riff_tag == b"RIFF":
            wav_type = WAVType.VO
        else:
            # Skip Bioware header
            # vendor/reone/src/libs/audio/format/wavreader.cpp
            # Bioware SFX files have 470-byte header before RIFF data
            self._reader.seek(470)  # SFX header size
            riff_tag: bytes = self._reader.read_bytes(4)
            wav_type = WAVType.SFX

        if riff_tag != b"RIFF":
            msg = "Not a valid RIFF/WAVE file"
            raise ValueError(msg)

        # Read WAVE header
        file_size: int = self._reader.read_uint32()
        wave_tag: bytes = self._reader.read_bytes(4)

        if wave_tag != b"WAVE":
            msg = "Not a valid WAVE file"
            raise ValueError(msg)

        # Read format chunk
        fmt_tag: bytes = self._reader.read_bytes(4)
        if fmt_tag != b"fmt ":
            msg = "Missing format chunk"
            raise ValueError(msg)

        fmt_size: int = self._reader.read_uint32()

        # Parse format data
        encoding: WaveEncoding = WaveEncoding(self._reader.read_uint16())
        channels: int = self._reader.read_uint16()
        sample_rate: int = self._reader.read_uint32()
        bytes_per_sec: int = self._reader.read_uint32()
        block_align: int = self._reader.read_uint16()
        bits_per_sample: int = self._reader.read_uint16()

        # Skip any extra format bytes
        if fmt_size > 0x10:
            self._reader.skip(fmt_size - 0x10)

        # Find data chunk
        while True:
            chunk_id: bytes = self._reader.read_bytes(4)
            chunk_size: int = self._reader.read_uint32()

            if chunk_id == b"data":
                break

            self._reader.skip(chunk_size)

        # Read audio data
        audio_data: bytes = self._reader.read_bytes(chunk_size)

        # Create WAV object
        self._wav = WAV(
            wav_type=wav_type,
            encoding=encoding,
            channels=channels,
            sample_rate=sample_rate,
            bits_per_sample=bits_per_sample,
            bytes_per_sec=bytes_per_sec,
            block_align=block_align,
            data=audio_data
        )

        return self._wav


class WAVBinaryWriter(ResourceWriter):
    """Handles writing WAV binary data."""

    def __init__(
        self,
        wav: WAV,
        target: TARGET_TYPES,
    ):
        super().__init__(target)
        self.wav: WAV = wav

    @autoclose
    def write(self, *, auto_close: bool = True) -> None:  # noqa: FBT001, FBT002, ARG002  # pyright: ignore[reportUnusedParameters]
        """Write WAV data to target.

        Processing Logic:
        ----------------
            - Write appropriate header based on WAV type
            - Write RIFF/WAVE header
            - Write format chunk
            - Write fact chunk (if needed)
            - Write data chunk
        """
        # Write appropriate header based on WAV type
        if self.wav.wav_type == WAVType.SFX:
            # Write SFX header
            self._writer.write_bytes(bytes([
                0xff, 0xff, 0xff, 0xff,  # 0x00: Magic number
                0xff, 0xff, 0xff, 0xf3,  # 0x04: Magic number
                0x60, 0xc4, 0x00, 0x00,  # 0x08: Unknown
                0x00, 0x03, 0x48, 0x00,  # 0x0C: Unknown
                0x00, 0x00, 0x00, 0x4c,  # 0x10: Unknown
                0x41, 0x4d, 0x45, 0x33,  # 0x14: "LAME3"
                0x2e, 0x39, 0x33, 0x55,  # 0x18: ".93U"
            ] + [0x55] * 442))  # Pad with 0x55 until 470 bytes

        # Calculate sizes
        data_size: int = len(self.wav.data)
        file_size: int = 0x24 + data_size  # Standard RIFF size calculation

        # Write RIFF header
        self._writer.write_bytes(b"RIFF")
        self._writer.write_uint32(file_size)
        self._writer.write_bytes(b"WAVE")

        # Write format chunk
        self._writer.write_bytes(b"fmt ")
        self._writer.write_uint32(0x10)  # Standard format chunk size
        self._writer.write_uint16(self.wav.encoding.value)
        self._writer.write_uint16(self.wav.channels)
        self._writer.write_uint32(self.wav.sample_rate)
        bytes_per_sec: int = self.wav.sample_rate * self.wav.block_align
        self._writer.write_uint32(bytes_per_sec)
        self._writer.write_uint16(self.wav.block_align)
        self._writer.write_uint16(self.wav.bits_per_sample)

        # Write fact chunk if needed
        if self.wav.wav_type == WAVType.VO:
            self._writer.write_bytes(b"fact")
            self._writer.write_uint32(4)  # Fact chunk size
            self._writer.write_uint32(0)  # Fact data

        # Write data chunk
        self._writer.write_bytes(b"data")
        self._writer.write_uint32(data_size)
        self._writer.write_bytes(self.wav.data)