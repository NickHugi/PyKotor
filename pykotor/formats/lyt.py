from __future__ import annotations


class LYT:
    @staticmethod
    def load(data: str) -> LYT:
        return _LYTReader.load(data)

    def build(self) -> str:
        return _LYTWriter.build(self)

    def __init__(self):
        pass
        # TODO


class _LYTReader:
    @staticmethod
    def load(data: str) -> LYT:
        pass
        # TODO


class _LYTWriter:
    @staticmethod
    def build(lyt: LYT) -> str:
        pass
        # TODO
