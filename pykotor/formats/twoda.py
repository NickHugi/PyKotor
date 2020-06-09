from __future__ import annotations

import csv
import io
from typing import List, Union

from pykotor.general.binary_reader import BinaryReader


class TwoDA:
    @staticmethod
    def load_binary(data: bytes) -> TwoDA:
        return _2DAReader.load(data)

    @staticmethod
    def load_csv(data: str) -> TwoDA:
        return _2DAReaderCSV.load(data)

    def build_binary(self):
        return _2DAWriter.build(self)

    def build_csv(self):
        return _2DAWriterCSV.build(self)

    def __init__(self):
        # _data [ row_0:dict(), row_1:dict(), ..., row_n:dict() ]
        self._columns: List[str] = []
        self._data: List[dict] = []

    # TODO - Error checking for all methods
    def column_exists(self, name: str) -> bool:
        return name in self._columns

    def column_count(self) -> int:
        return len(self._columns)

    def add_column(self, name: str, default: str = "") -> None:
        self._columns.append(name)
        for row in self._data:
            row[name] = default

    def remove_column(self, name: str) -> None:
        self._columns.remove(name)
        for row in self._data:
            del row[name]

    def get_columns(self):
        return self._columns.copy()

    def get_column(self, name: str) -> List[str]:
        column_data = []
        for row in self._data:
            column_data.append(row[name])
        return column_data

    def row_count(self) -> int:
        return len(self._data)

    def add_row(self, at=-1, default="") -> None:
        row_data = dict()
        for column in self._columns:
            row_data[column] = default
        if at == -1:
            self._data.append(row_data)
        elif self.row_count() > at >= 0:
            self._data.insert(at, row_data)

    def remove_row(self, at=-1) -> None:
        if at == -1:
            del self._data[-1]
        elif self.row_count() > at >= 0:
            del self._data[at]

    def get_row(self, row: int) -> dict:
        return self._data[row].copy()

    def set_data(self, column: str, row: int, value: Union[str, int]) -> None:
        self._data[row][column] = str(value)

    def get_data(self, column: str, row: int) -> str:
        return self._data[row][column]


class _2DAReader:
    @staticmethod
    def load(data: bytes) -> TwoDA:
        reader = BinaryReader.from_data(data)
        twoda = TwoDA()

        file_type = reader.read_string(4)
        file_version = reader.read_string(4)
        reader.skip(1)

        columns = []
        while reader.peek() != 0:
            columns.append(reader.read_terminated_string('\t'))
            twoda.add_column(columns[-1])
        column_count = len(columns)

        reader.skip(1)
        row_count = reader.read_int32()
        for i in range(row_count):
            row_name = reader.read_terminated_string('\t')

        cell_count = row_count * len(columns)
        cell_offsets = []
        for i in range(cell_count):
            cell_offsets.append(reader.read_uint16())

        reader.skip(2)
        data_offset = reader.position()

        for i in range(row_count):
            twoda.add_row()
            for j in range(column_count):
                cell_index = j + i * column_count
                reader.seek(data_offset + cell_offsets[cell_index])
                data = reader.read_terminated_string('\0')
                twoda.set_data(columns[j], i, data)

        return twoda


class _2DAWriter:
    @staticmethod
    def build(twoda: TwoDA) -> bytes:
        pass
        # TODO


class _2DAReaderCSV:
    @staticmethod
    def load(data: str) -> TwoDA:
        twoda = TwoDA()
        input = io.StringIO(data)
        reader = csv.reader(input)

        rows = list(reader)

        columns = []
        for column in rows[0]:
            columns.append(column)
            twoda.add_column(column)
        del rows[0]

        for i, row in enumerate(rows):
            twoda.add_row()
            for j, cell in enumerate(row):
                column = columns[j]
                twoda.set_data(column, i, cell)

        return twoda


class _2DAWriterCSV:
    @staticmethod
    def build(twoda: TwoDA) -> str:
        output = io.StringIO()

        wrap = csv.writer(output, quoting=csv.QUOTE_ALL)
        wrap.writerow(twoda.get_columns())

        columns = twoda.get_columns()
        for row in range(twoda.row_count()):
            row_data = []
            for column in columns:
                row_data.append(twoda.get_data(column, row))
            wrap.writerow(row_data)

        return output.getvalue().replace('\r', '')
