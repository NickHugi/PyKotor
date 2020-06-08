from __future__ import annotations


class WOK:
    @staticmethod
    def load_binary(data: bytes) -> WOK:
        return _WOKReader.load(data)

    @staticmethod
    def build_binary(self) -> bytes:
        return _WOKWriter.build(self)

    def __init__(self):
        pass
        # TODO


class _WOKReader:
    @staticmethod
    def load(data: bytes) -> WOK:
        pass
        # TODO


class _WOKWriter:
    @staticmethod
    def build(wok: WOK) -> bytes:
        pass
        # TODO
