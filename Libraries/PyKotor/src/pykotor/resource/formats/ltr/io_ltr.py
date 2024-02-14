from __future__ import annotations

import itertools

from pykotor.resource.formats.ltr.ltr_data import LTR
from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES, ResourceReader, ResourceWriter


class LTRBinaryReader(ResourceReader):
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        super().__init__(source, offset, size)
        self._lip: LTR | None = None

    def load(
        self,
        auto_close: bool = True,
    ) -> LTR:
        self._ltr = LTR()

        file_type = self._reader.read_string(4)
        file_version = self._reader.read_string(4)

        if file_type != "LTR ":
            msg = "The file type that was loaded is invalid."
            raise TypeError(msg)

        if file_version != "V1.0":
            msg = "The LTR version that was loaded is not supported."
            raise TypeError(msg)

        letter_count = self._reader.read_uint8()
        if letter_count != 28:
            msg = "LTR files that do not handle exactly 28 characters are not supported."
            raise TypeError(msg)

        self._ltr._singles._start = [self._reader.read_single() for _ in range(28)]
        self._ltr._singles._middle = [self._reader.read_single() for _ in range(28)]
        self._ltr._singles._end = [self._reader.read_single() for _ in range(28)]

        for i in range(28):
            self._ltr._doubles[i]._start = [self._reader.read_single() for _ in range(28)]
            self._ltr._doubles[i]._middle = [self._reader.read_single() for _ in range(28)]
            self._ltr._doubles[i]._end = [self._reader.read_single() for _ in range(28)]

        for i in range(28):
            for j in range(28):
                self._ltr._triples[i][j]._start = [self._reader.read_single() for _ in range(28)]
                self._ltr._triples[i][j]._middle = [self._reader.read_single() for _ in range(28)]
                self._ltr._triples[i][j]._end = [self._reader.read_single() for _ in range(28)]

        if auto_close:
            self._reader.close()

        return self._ltr


class LTRBinaryWriter(ResourceWriter):
    def __init__(
        self,
        ltr: LTR,
        target: TARGET_TYPES,
    ):
        super().__init__(target)
        self._ltr: LTR = ltr

    def write(
        self,
        auto_close: bool = True,
    ):
        self._writer.write_string("LTR V1.0")
        self._writer.write_uint8(28)

        for chance in self._ltr._singles._start:
            self._writer.write_single(chance)
        for chance in self._ltr._singles._middle:
            self._writer.write_single(chance)
        for chance in self._ltr._singles._end:
            self._writer.write_single(chance)

        for i in range(28):
            for chance in self._ltr._doubles[i]._start:
                self._writer.write_single(chance)
            for chance in self._ltr._doubles[i]._middle:
                self._writer.write_single(chance)
            for chance in self._ltr._doubles[i]._end:
                self._writer.write_single(chance)

        for i, j in itertools.product(range(28), range(28)):
            for chance in self._ltr._triples[i][j]._start:
                self._writer.write_single(chance)
            for chance in self._ltr._triples[i][j]._middle:
                self._writer.write_single(chance)
            for chance in self._ltr._triples[i][j]._end:
                self._writer.write_single(chance)

        if auto_close:
            self._writer.close()
