from __future__ import annotations

import lzma

from typing import TYPE_CHECKING


from pykotor.common.misc import ResRef
from pykotor.resource.formats.bif.bif_data import BIF, BIFResource, BIFType
from pykotor.resource.type import ResourceReader, ResourceType, ResourceWriter, autoclose

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


_LZMA_RAW_FILTERS: list[dict[str, int]] = [{"id": lzma.FILTER_LZMA1}]


def _decompress_bzf_payload(payload: bytes, expected_size: int) -> bytes:
    """Handle both raw and containerised LZMA payloads, tolerating 4-byte padding."""
    try:
        data = lzma.decompress(payload, format=lzma.FORMAT_RAW, filters=_LZMA_RAW_FILTERS)
    except lzma.LZMAError:
        cleaned_payload = payload
        while True:
            try:
                decompressor = lzma.LZMADecompressor()
                data = decompressor.decompress(cleaned_payload)
            except lzma.LZMAError:
                stripped = cleaned_payload.rstrip(b"\0")
                if len(stripped) == len(cleaned_payload):
                    raise
                cleaned_payload = stripped
                continue

            leftover = getattr(decompressor, "unused_data", b"")
            if leftover and any(byte != 0 for byte in leftover):
                cleaned_payload = cleaned_payload[: len(cleaned_payload) - len(leftover)]
                continue

            break

    if len(data) != expected_size:
        msg = f"Decompressed size mismatch: got {len(data)}, expected {expected_size}"
        raise lzma.LZMAError(msg)

    return data


class BIFBinaryReader(ResourceReader):
    """Reads BIF/BZF files.
    
    BIF (BioWare Index File) files contain game resources indexed by KEY files.
    BZF files are compressed BIF files using LZMA compression.
    
    References:
    ----------
        vendor/reone/src/libs/resource/format/bifreader.cpp:26-30 (signature checking)
        vendor/reone/src/libs/resource/format/bifreader.cpp:32-39 (fixed resources handling)
        vendor/xoreos-tools/src/unkeybif.cpp (BIF extraction tool)
    
    Missing Features:
    ----------------
        - Fixed resources explicitly rejected (reone reads but doesn't use them)
    """
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        super().__init__(source, offset, size)
        self.bif: BIF = BIF()
        self.var_res_count: int = 0
        self.fixed_res_count: int = 0
        self.data_offset: int = 0

    @autoclose
    def load(self, *, auto_close: bool = True) -> BIF:  # noqa: FBT001, FBT002, ARG002
        """Load BIF/BZF data from source."""
        self._check_signature()
        self._read_header()
        self._read_resource_table()
        self._read_resource_data()
        return self.bif

    def _check_signature(self) -> None:
        """Check BIF/BZF signature."""
        # vendor/reone/src/libs/resource/format/bifreader.cpp:26-30
        signature: str = self._reader.read_string(8)  # "BIFFV1  " or "BZF V1  "

        # Check file type
        if signature[:4] == BIFType.BIF.value:
            self.bif.bif_type = BIFType.BIF
        elif signature[:4] == BIFType.BZF.value:
            self.bif.bif_type = BIFType.BZF
        else:
            msg = f"Invalid BIF/BZF file type: {signature[:4]}"
            raise ValueError(msg)

        # Check version - PyKotor supports "V1  " and "V1.1", reone only checks "BIFFV1  "
        # vendor/reone/src/libs/resource/format/bifreader.cpp:27
        if signature[4:] != "V1  " and signature[4:] != "V1.1":
            msg = f"Unsupported BIF/BZF version: {signature[4:]}"
            raise ValueError(msg)

    def _read_header(self) -> None:
        """Read BIF/BZF file header."""
        self.var_res_count = self._reader.read_uint32()
        self.fixed_res_count = self._reader.read_uint32()
        self.data_offset = self._reader.read_uint32()

        # vendor/reone/src/libs/resource/format/bifreader.cpp:32-39
        # NOTE: reone reads fixed_res_count but doesn't use it. PyKotor explicitly rejects.
        if self.fixed_res_count > 0:
            msg = "Fixed resources not supported"
            raise ValueError(msg)

    def _read_resource_table(self) -> None:
        """Read BIF/BZF resource table."""
        self._reader.seek(self.data_offset)

        for i in range(self.var_res_count):
            key_id: int = self._reader.read_uint32()
            offset: int = self._reader.read_uint32()
            size: int = self._reader.read_uint32()
            res_type: ResourceType = ResourceType.from_id(self._reader.read_uint32())

            # Create empty resource with placeholder data
            resource = BIFResource(ResRef.from_blank(), res_type, b"", key_id, size)
            resource.offset = offset

            # For BZF, calculate packed size from offset differences
            if self.bif.bif_type == BIFType.BZF and i > 0:
                prev_resource: BIFResource = self.bif.resources[-1]
                prev_resource.packed_size = offset - prev_resource.offset

            self.bif.resources.append(resource)

        # Set packed size for last resource in BZF
        if self.bif.bif_type == BIFType.BZF and self.bif.resources:
            last_resource: BIFResource = self.bif.resources[-1]
            last_resource.packed_size = self._reader.size() - last_resource.offset

    def _read_resource_data(self) -> None:
        """Read BIF/BZF resource data."""
        for i, resource in enumerate(self.bif.resources):
            self._reader.seek(resource.offset)

            if self.bif.bif_type == BIFType.BZF:
                # For BZF, decompress the data
                compressed: bytes = self._reader.read_bytes(resource.packed_size)
                try:
                    resource.data = _decompress_bzf_payload(compressed, resource.size)
                except lzma.LZMAError as e:  # noqa: PERF203
                    msg = f"Failed to decompress BZF resource: {e}"
                    raise ValueError(msg) from e
            else:
                # For BIF, read raw data
                resource.data = self._reader.read_bytes(resource.size)

        self.bif.build_lookup_tables()


class BIFBinaryWriter(ResourceWriter):
    """Writes BIF/BZF files."""

    def __init__(
        self,
        bif: BIF,
        target: TARGET_TYPES,
    ):
        super().__init__(target)
        self.bif: BIF = bif
        self._data_offset: int = 0

    @autoclose
    def write(self, *, auto_close: bool = True) -> None:  # noqa: FBT001, FBT002, ARG002  # pyright: ignore[reportUnusedParameters]
        """Write BIF/BZF data to target."""
        self._write_header()
        self._write_resource_table()
        self._write_resource_data()

    def _write_header(self) -> None:
        """Write BIF/BZF file header."""
        # Write signature
        self._writer.write_string(self.bif.bif_type.value)
        self._writer.write_string("V1  ")

        # Write counts and offset to resource table (always right after header)
        self._writer.write_uint32(self.bif.var_count)
        self._writer.write_uint32(self.bif.fixed_count)
        self._writer.write_uint32(BIF.HEADER_SIZE)  # Offset to variable resource table (20 bytes)

    def _write_resource_table(self) -> None:
        """Write BIF/BZF resource table."""
        # Calculate absolute file offsets for resource data
        # Data section starts after header and resource table
        data_section_offset = BIF.HEADER_SIZE + (self.bif.var_count * BIF.VAR_ENTRY_SIZE)
        current_offset = data_section_offset
        
        for resource in self.bif.resources:
            # Align resource data to 4-byte boundary
            if current_offset % 4 != 0:
                current_offset += 4 - (current_offset % 4)
            resource.offset = current_offset

            if self.bif.bif_type == BIFType.BZF:
                # For BZF, compress the data to get size using raw LZMA1 format
                compressed: bytes = lzma.compress(resource.data, format=lzma.FORMAT_RAW, filters=_LZMA_RAW_FILTERS)
                resource.packed_size = len(compressed)
                current_offset += resource.packed_size
            else:
                current_offset += resource.size

        # Write resource table entries with absolute file offsets
        for resource in self.bif.resources:
            self._writer.write_uint32(resource.resname_key_index)
            self._writer.write_uint32(resource.offset)  # Absolute file offset
            self._writer.write_uint32(resource.size)
            self._writer.write_uint32(resource.restype.type_id)

    def _write_resource_data(self) -> None:
        """Write BIF/BZF resource data."""
        for resource in self.bif.resources:
            # Align to 4-byte boundary
            current_pos: int = self._writer.position()
            calc: int = current_pos % 4
            if calc != 0:
                self._writer.write_bytes(bytes(4 - calc))

            if self.bif.bif_type == BIFType.BZF:
                # Write compressed data for BZF using raw LZMA1 format
                compressed: bytes = lzma.compress(resource.data, format=lzma.FORMAT_RAW, filters=_LZMA_RAW_FILTERS)
                self._writer.write_bytes(compressed)
            else:
                # Write raw data for BIF
                self._writer.write_bytes(resource.data)
