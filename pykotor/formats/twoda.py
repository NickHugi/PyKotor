from __future__ import annotations

from typing import List, Union


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
        pass
        # TODO


class _2DAWriter:
    @staticmethod
    def build(twoda: TwoDA) -> bytes:
        pass
        # TODO


class _2DAReaderCSV:
    @staticmethod
    def load(data: str) -> TwoDA:
        pass
        # TODO


class _2DAWriterCSV:
    @staticmethod
    def build(twoda: TwoDA) -> str:
        pass
        # TODO
