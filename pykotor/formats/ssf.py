from __future__ import annotations


class SSF:
    @staticmethod
    def load_binary(data: bytes) -> SSF:
        return _SSFReader.load(data)

    @staticmethod
    def load_xml(data: str) -> SSF:
        return _SSFReaderXML.load(data)

    def build_binary(self) -> bytes:
        return _SSFWriter.build(self)

    def build_xml(self) -> str:
        return _SSFWriterXML.build(self)

    def __init__(self):
        pass


class _SSFReader:
    @staticmethod
    def load(data: bytes) -> SSF:
        pass
        # TODO


class _SSFWriter:
    @staticmethod
    def build(ssf: SSF) -> bytes:
        pass
        # TODO


class _SSFReaderXML:
    @staticmethod
    def load(data: str) -> SSF:
        pass
        # TODO


class _SSFWriterXML:
    @staticmethod
    def build(ssf: SSF) -> str:
        pass
        # TODO
