from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.wav.wav_data import WAV, WAVType, WaveEncoding
from pykotor.resource.formats.wav.wav_obfuscation import deobfuscate_audio, obfuscate_audio
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
        """Load WAV file with automatic deobfuscation.

        Returns:
        -------
            WAV: The loaded WAV object (deobfuscated)

        Processing Logic:
        ----------------
            - Read all data and deobfuscate if needed
            - Parse RIFF/WAVE format
            - Read wave format data
            - Read audio data
        """
        # Read all data first - save current position
        saved_pos = self._reader.position()
        self._reader.seek(0)
        
        # Read all available data using RawBinaryReader API
        raw_data = self._reader.read_all()
        
        # Restore position
        self._reader.seek(saved_pos)
        
        # Deobfuscate the data
        deobfuscated_data: bytes = deobfuscate_audio(raw_data)
        
        # Determine WAV type based on whether deobfuscation occurred
        if len(deobfuscated_data) < len(raw_data):
            # Deobfuscation occurred - determine type
            if len(raw_data) - len(deobfuscated_data) == 470:  # 0x1D6
                wav_type = WAVType.SFX
            else:
                wav_type = WAVType.VO
        else:
            wav_type = WAVType.VO
        
        # Create a new reader from deobfuscated data
        from pykotor.common.stream import BinaryReader
        from io import BytesIO
        deobfuscated_stream = BytesIO(deobfuscated_data)
        reader = BinaryReader(deobfuscated_stream)
        
        # Read first 4 bytes to check format
        riff_tag: bytes = reader.read_bytes(4)

        if riff_tag != b"RIFF":
            msg = "Not a valid RIFF/WAVE file"
            raise ValueError(msg)

        # Read WAVE header
        _file_size: int = reader.read_uint32()
        wave_tag: bytes = reader.read_bytes(4)

        if wave_tag != b"WAVE":
            msg = "Not a valid WAVE file"
            raise ValueError(msg)

        # Read format chunk
        fmt_tag: bytes = reader.read_bytes(4)
        if fmt_tag != b"fmt ":
            msg = "Missing format chunk"
            raise ValueError(msg)

        fmt_size: int = reader.read_uint32()

        # Parse format data
        encoding: WaveEncoding = WaveEncoding(reader.read_uint16())
        channels: int = reader.read_uint16()
        sample_rate: int = reader.read_uint32()
        bytes_per_sec: int = reader.read_uint32()
        block_align: int = reader.read_uint16()
        bits_per_sample: int = reader.read_uint16()

        # Skip any extra format bytes
        if fmt_size > 0x10:
            reader.skip(fmt_size - 0x10)

        # Find data chunk
        while True:
            chunk_id: bytes = reader.read_bytes(4)
            chunk_size: int = reader.read_uint32()

            if chunk_id == b"data":
                break

            reader.skip(chunk_size)

        # Read audio data
        audio_data: bytes = reader.read_bytes(chunk_size)

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
        """Write WAV data to target with automatic obfuscation.

        Processing Logic:
        ----------------
            - Build clean RIFF/WAVE data
            - Obfuscate based on WAV type
            - Write obfuscated data to target
        """
        # Build clean WAV data first
        from io import BytesIO
        from pykotor.common.stream import BinaryWriter
        
        clean_buffer = BytesIO()
        clean_writer = BinaryWriter(clean_buffer)
        
        # Calculate sizes
        data_size: int = len(self.wav.data)
        file_size: int = 0x24 + data_size  # Standard RIFF size calculation

        # Write RIFF header
        clean_writer.write_bytes(b"RIFF")
        clean_writer.write_uint32(file_size)
        clean_writer.write_bytes(b"WAVE")

        # Write format chunk
        clean_writer.write_bytes(b"fmt ")
        clean_writer.write_uint32(0x10)  # Standard format chunk size
        clean_writer.write_uint16(self.wav.encoding.value)
        clean_writer.write_uint16(self.wav.channels)
        clean_writer.write_uint32(self.wav.sample_rate)
        bytes_per_sec: int = self.wav.sample_rate * self.wav.block_align
        clean_writer.write_uint32(bytes_per_sec)
        clean_writer.write_uint16(self.wav.block_align)
        clean_writer.write_uint16(self.wav.bits_per_sample)

        # Write fact chunk if needed
        if self.wav.wav_type == WAVType.VO:
            clean_writer.write_bytes(b"fact")
            clean_writer.write_uint32(4)  # Fact chunk size
            clean_writer.write_uint32(0)  # Fact data

        # Write data chunk
        clean_writer.write_bytes(b"data")
        clean_writer.write_uint32(data_size)
        clean_writer.write_bytes(self.wav.data)
        
        # Get clean data and obfuscate it
        clean_data = clean_buffer.getvalue()
        wav_type_str = "SFX" if self.wav.wav_type == WAVType.SFX else "VO"
        obfuscated_data = obfuscate_audio(clean_data, wav_type_str)
        
        # Write obfuscated data
        self._writer.write_bytes(obfuscated_data)