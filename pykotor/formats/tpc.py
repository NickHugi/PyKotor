from __future__ import annotations


class TPC:
    @staticmethod
    def load(data: bytes) -> TPC:
        return _TPCReader.load(data)

    def build(self):
        return _TPCWriter.build(self)

    def __init__(self):
        self.txi: str = ""
        # TODO


class _TPCReader:
    @staticmethod
    def load(data: bytes) -> TPC:
        pass
        # TODO


class _TPCWriter:
    @staticmethod
    def build(tpc: TPC) -> bytes:
        pass
        # TODO


class _TGAWriter:
    @staticmethod
    def build(rgba: bytes) -> bytes:
        pass
        # TODO
