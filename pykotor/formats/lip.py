from __future__ import annotations


class LIP:
    @staticmethod
    def load(data: bytes) -> LIP:
        return _LIPReader.load(data)

    @staticmethod
    def build(self) -> bytes:
        _LIPWriter.build(self)

    def __init__(self):
        pass
        # TODO


class _LIPReader:
    @staticmethod
    def load(data: bytes) -> LIP:
        pass
        # TODO


class _LIPWriter:
    @staticmethod
    def build(lip: LIP) -> bytes:
        pass
        # TODO
