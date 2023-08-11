from __future__ import annotations

import csv
import io

from pykotor.resource.formats.twoda.twoda_data import TwoDA
from pykotor.resource.type import (
    SOURCE_TYPES,
    TARGET_TYPES,
    ResourceReader,
    ResourceWriter,
    autoclose,
)


class TwoDACSVReader(ResourceReader):
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        super().__init__(source, offset, size)
        self._twoda: TwoDA | None = None

    @autoclose
    def load(
        self,
        auto_close: bool = True,
    ) -> TwoDA:
        self._twoda = TwoDA()
        data = self._reader.read_bytes(self._reader.size()).decode()
        _csv: csv.reader = csv.reader(io.StringIO(data))

        headers = next(_csv)[1:]
        for header in headers:
            self._twoda.add_column(header)

        for row in _csv:
            label = row[:1][0]
            cells = dict(zip(headers, row[1:]))
            self._twoda.add_row(label, cells)

        return self._twoda


class TwoDACSVWriter(ResourceWriter):
    def __init__(
        self,
        twoda: TwoDA,
        target: TARGET_TYPES,
    ):
        super().__init__(target)
        self._twoda: TwoDA = twoda
        self._csv_string = io.StringIO("")
        self._csv_writer = csv.writer(self._csv_string)

    @autoclose
    def write(
        self,
        auto_close: bool = True,
    ) -> None:
        headers = self._twoda.get_headers()

        insert = [""]
        insert.extend(iter(headers))
        self._csv_writer.writerow(insert)

        for row in self._twoda:
            insert = [str(row.label())]
            insert.extend(row.get_string(header) for header in headers)
            self._csv_writer.writerow(insert)

        data = self._csv_string.getvalue().encode("ascii")
        self._writer.write_bytes(data)
