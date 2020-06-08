from __future__ import annotations


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
        pass
        # TODO


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
