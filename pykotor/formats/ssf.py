from __future__ import annotations

from typing import List

from pykotor.general.binary_reader import BinaryReader


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
        self.entries: List[int] = [-1] * 40


class _SSFReader:
    @staticmethod
    def load(data: bytes) -> SSF:
        ssf = SSF()
        reader = BinaryReader.from_data(data)

        file_type = reader.read_string(4)
        file_version = reader.read_string(4)

        table_offset = reader.read_uint32()

        reader.seek(table_offset)
        for i in range(40):
            ssf.entries[i] = reader.read_int32()

        return ssf


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
