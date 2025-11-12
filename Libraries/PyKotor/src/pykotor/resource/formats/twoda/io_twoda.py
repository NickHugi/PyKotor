from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.twoda.twoda_data import TwoDA
from pykotor.resource.type import ResourceReader, ResourceWriter, autoclose

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class TwoDABinaryReader(ResourceReader):
    """Reads 2DA (Two-Dimensional Array) files.
    
    2DA files store tabular data used throughout KotOR for game configuration, item stats,
    spell data, and other structured information.
    
    References:
    ----------
        vendor/reone/src/libs/resource/format/2dareader.cpp:26-80 (2DA reading)
        vendor/reone/src/libs/resource/format/2dawriter.cpp (2DA writing)
    
    Algorithm Differences:
    ---------------------
        - Cell reading: PyKotor uses read_terminated_string, reone uses readCStringAt with limit
        - Token reading approaches differ between implementations
    """
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        super().__init__(source, offset, size)
        self._twoda: TwoDA | None = None

    @autoclose
    def load(self, *, auto_close: bool = True) -> TwoDA:  # noqa: FBT001, FBT002, ARG002
        """Loads a 2DA file from the provided reader.

        Args:
        ----
            auto_close: Whether to close the reader after loading - default True

        Returns:
        -------
            TwoDA: The loaded TwoDA object

        Processing Logic:
        ----------------
            - Read file header and validate type and version
            - Read column headers
            - Read row count and populate rows
            - Read cell offsets
            - Seek to cell data and populate cells
        """
        self._twoda = TwoDA()

        file_type: str = self._reader.read_string(4)
        file_version: str = self._reader.read_string(4)

        if file_type != "2DA ":
            msg = "The file type that was loaded is invalid."
            raise TypeError(msg)

        if file_version != "V2.b":
            msg = "The 2DA version that was loaded is not supported."
            raise TypeError(msg)

        self._reader.read_uint8()  # \n

        columns: list[str] = []
        while self._reader.peek() != b"\0":
            column_header: str = self._reader.read_terminated_string("\t")
            self._twoda.add_column(column_header)
            columns.append(column_header)

        self._reader.read_uint8()  # \0

        row_count: int = self._reader.read_uint32()
        column_count: int = self._twoda.get_width()
        cell_count: int = row_count * column_count
        for _ in range(row_count):
            row_header: str = self._reader.read_terminated_string("\t")
            row_label: str = row_header
            self._twoda.add_row(row_label)

        cell_offsets: list[int] = [0] * cell_count
        for i in range(cell_count):
            cell_offsets[i] = self._reader.read_uint16()

        self._reader.read_uint16()
        cell_data_offset: int = self._reader.position()

        for i in range(cell_count):
            column_id: int = i % column_count
            row_id: int = i // column_count
            column_header: str = columns[column_id]
            self._reader.seek(cell_data_offset + cell_offsets[i])
            # vendor/reone/src/libs/resource/format/2dareader.cpp:65-70
            # NOTE: reone uses readCStringAt with limit, PyKotor uses read_terminated_string
            # Should verify buffer limits match vendor behavior
            cell_value: str = self._reader.read_terminated_string("\0")
            self._twoda.set_cell(row_id, column_header, cell_value)

        return self._twoda


class TwoDABinaryWriter(ResourceWriter):
    def __init__(
        self,
        twoda: TwoDA,
        target: TARGET_TYPES,
    ):
        super().__init__(target)
        self._twoda: TwoDA = twoda

    @autoclose
    def write(self, *, auto_close: bool = True) -> None:  # noqa: FBT001, FBT002, ARG002  # pyright: ignore[reportUnusedParameters]
        """Writes the 2DA data to a binary file.

        Args:
        ----
            auto_close: {Whether to close the writer after writing is complete}

        Returns:
        -------
            None: {Nothing is returned}

        Processing Logic:
        ----------------
            - Get the headers and row labels from the 2DA
            - Write the header string and version
            - Write the headers and row labels
            - Loop through each cell and writes the value offsets and data
            - Close the writer if auto_close is True
        """
        headers: list[str] = self._twoda.get_headers()

        self._writer.write_string("2DA ")
        self._writer.write_string("V2.b")

        self._writer.write_string("\n")
        for header in headers:
            self._writer.write_string(header + "\t")
        self._writer.write_string("\0")

        self._writer.write_uint32(self._twoda.get_height())
        for row_label in self._twoda.get_labels():
            self._writer.write_string(str(row_label) + "\t")

        values: list[str] = []
        value_offsets: list[int] = []
        cell_offsets: list[int] = []
        data_size: int = 0

        for row in self._twoda:
            for header in self._twoda.get_headers():
                value = row.get_string(header) + "\0"
                if value not in values:
                    value_offset = len(values[-1]) + value_offsets[-1] if value_offsets else 0
                    values.append(value)
                    value_offsets.append(value_offset)
                    data_size += len(value)
                cell_offset = value_offsets[values.index(value)]
                cell_offsets.append(cell_offset)

        for cell_offset in cell_offsets:
            self._writer.write_uint16(cell_offset)
        self._writer.write_uint16(data_size)

        for value in values:
            self._writer.write_string(value)
