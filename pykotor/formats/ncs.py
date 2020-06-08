from __future__ import annotations


class NCS:
    @staticmethod
    def load_binary(data: bytes) -> NCS:
        return _NCSReader.load(data)

    @staticmethod
    def load_ascii(data: str):
        return _NSSReader.load(data)

    def build_binary(self):
        return _NCSWriter.build(self)

    def build_ascii(self):
        return _NSSWriter.build(self)

    def __init__(self):
        pass
        # TODO


class _NCSReader:
    @staticmethod
    def load(data: bytes) -> NCS:
        pass
        # TODO


class _NCSWriter:
    @staticmethod
    def build(ncs: NCS) -> bytes:
        pass
        # TODO


class _NSSReader:
    @staticmethod
    def load(data: str) -> NCS:
        pass
        # TODO


class _NSSWriter:
    @staticmethod
    def build(ncs: NCS) -> str:
        pass
        # TODO
