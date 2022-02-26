from __future__ import annotations

import csv
import io
from typing import Optional

from pykotor.resource.formats.twoda.twoda_data import TwoDA
from pykotor.resource.type import TARGET_TYPES, SOURCE_TYPES, ResourceReader, ResourceWriter


class TwoDACSVReader(ResourceReader):
    def __init__(self, source: SOURCE_TYPES, offset: int = 0, size: int = 0):
        super().__init__(source, offset, size)
        self._csv: csv.reader = csv.reader(io.StringIO(self._reader.read_bytes(self._size).decode()))
        self._twoda: Optional[TwoDA] = None

    def load(self, auto_close: bool = True) -> TwoDA:
        self._twoda = TwoDA()

        headers = next(self._csv)[1:]
        for header in headers:
            self._twoda.add_column(header)

        for row in self._csv:
            label = int(row[:1][0])
            cells = dict(zip(headers, row[1:]))
            self._twoda.add_row(label, cells)

        if auto_close:
            self._reader.close()

        return self._twoda


class TwoDACSVWriter(ResourceWriter):
    def __init__(self, twoda: TwoDA, target: TARGET_TYPES):
        super().__init__(target)
        self._twoda: TwoDA = twoda
        self._csv_string = io.StringIO("")
        self._csv_writer = csv.writer(self._csv_string)

    def write(self, auto_close: bool = True) -> None:
        headers = self._twoda.get_headers()

        insert = [""]
        for header in headers:
            insert.append(header)
        self._csv_writer.writerow(insert)

        for row in self._twoda:
            insert = [str(row.label())]
            for header in headers:
                insert.append(row.get_string(header))
            self._csv_writer.writerow(insert)

        data = self._csv_string.getvalue().encode('ascii')
        self._writer.write_bytes(data)

        if auto_close:
            self._writer.close()
