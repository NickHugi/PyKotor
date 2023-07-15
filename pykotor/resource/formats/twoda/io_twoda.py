from __future__ import annotations

from typing import Optional

from pykotor.resource.formats.twoda.twoda_data import TwoDA
from pykotor.resource.type import TARGET_TYPES, SOURCE_TYPES, ResourceReader, ResourceWriter, autoclose


class TwoDABinaryReader(ResourceReader):
    def __init__(
            self,
            source: SOURCE_TYPES,
            offset: int = 0,
            size: int = 0
    ):
        super().__init__(source, offset, size)
        self._twoda: Optional[TwoDA] = None

    @autoclose
    def load(
            self,
            auto_close: bool = True
    ) -> TwoDA:
        self._twoda = TwoDA()

        file_type = self._reader.read_string(4)
        file_version = self._reader.read_string(4)

        if file_type != "2DA ":
            raise TypeError("The file type that was loaded is invalid.")

        if file_version != "V2.b":
            raise TypeError("The 2DA version that was loaded is not supported.")

        self._reader.read_uint8()  # \n

        columns = []
        while self._reader.peek() != b'\0':
            column_header = self._reader.read_terminated_string("\t")
            self._twoda.add_column(column_header)
            columns.append(column_header)

        self._reader.read_uint8()  # \0

        row_count = self._reader.read_uint32()
        column_count = self._twoda.get_width()
        cell_count = row_count * column_count
        for i in range(row_count):
            row_header = self._reader.read_terminated_string("\t")
            row_label = row_header
            self._twoda.add_row(row_label)

        cell_offsets = [0] * cell_count
        for i in range(cell_count):
            cell_offsets[i] = self._reader.read_uint16()

        cell_data_size = self._reader.read_uint16()
        cell_data_offset = self._reader.position()

        for i in range(cell_count):
            column_id = i % column_count
            row_id = i // column_count
            column_header = columns[column_id]
            self._reader.seek(cell_data_offset + cell_offsets[i])
            cell_value = self._reader.read_terminated_string("\0")
            self._twoda.set_cell(row_id, column_header, cell_value)

        return self._twoda


class TwoDABinaryWriter(ResourceWriter):
    def __init__(
            self,
            twoda: TwoDA,
            target: TARGET_TYPES
    ):
        super().__init__(target)
        self._twoda: TwoDA = twoda

    @autoclose
    def write(
            self,
            auto_close: bool = True
    ) -> None:
        headers = self._twoda.get_headers()

        self._writer.write_string("2DA ")
        self._writer.write_string("V2.b")

        self._writer.write_string("\n")
        for header in headers:
            self._writer.write_string(header + "\t")
        self._writer.write_string("\0")

        self._writer.write_uint32(self._twoda.get_height())
        for row_label in self._twoda.get_labels():
            self._writer.write_string(str(row_label) + "\t")

        values = []
        value_offsets = []
        cell_offsets = []
        data_size = 0

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
