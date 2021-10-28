"""
This module contains abstract classes intended to reduce boilerplate code for loading and writing methods present in
resource classes found in the submodules.
"""

from abc import ABC
from typing import overload, Union, Any

from pykotor.common.stream import BinaryReader, BinaryWriter


class BinaryOps(ABC):
    BINARY_READER = None
    BINARY_WRITER = None

    @classmethod
    @overload
    def load_binary(cls, filepath: str, offset: int = 0):
        ...

    @classmethod
    @overload
    def load_binary(cls, data: bytes, offset: int = 0):
        ...

    @classmethod
    @overload
    def load_binary(cls, data: bytearray, offset: int = 0):
        ...

    @classmethod
    @overload
    def load_binary(cls, reader: BinaryReader, offset: int = 0):
        ...

    @classmethod
    def load_binary(cls, source: Union[str, bytes, bytearray, BinaryReader], offset: int = 0):
        with BinaryReader.from_auto(source, offset) as reader:
            return cls.BINARY_READER(reader).load()

    @overload
    def write_binary(self, filepath) -> None:
        ...

    @overload
    def write_binary(self, data: bytearray) -> None:
        ...

    @overload
    def write_binary(self, reader: BinaryReader) -> None:
        ...

    def write_binary(self, destination: Union[str, bytearray, BinaryReader]) -> None:
        with BinaryWriter.to_auto(destination) as writer:
            return self.BINARY_WRITER(writer, self).write()


class XMLOps(ABC):
    XML_READER = None
    XML_WRITER = None

    @classmethod
    @overload
    def load_xml(cls, filepath: str, offset: int = 0):
        ...

    @classmethod
    @overload
    def load_xml(cls, data: bytes, offset: int = 0):
        ...

    @classmethod
    @overload
    def load_xml(cls, data: bytearray, offset: int = 0):
        ...

    @classmethod
    @overload
    def load_xml(cls, reader: BinaryReader, offset: int = 0):
        ...

    @classmethod
    def load_xml(cls, source: Union[str, bytes, bytearray, BinaryReader], offset: int = 0):
        with BinaryReader.from_auto(source, offset) as reader:
            return cls.XML_READER(reader).load()

    @overload
    def write_xml(self, filepath):
        ...

    @overload
    def write_xml(self, data: bytearray):
        ...

    @overload
    def write_xml(self, reader: BinaryReader):
        ...

    def write_xml(self, destination: Union[str, bytearray, BinaryReader]) -> None:
        with BinaryWriter.to_auto(destination) as writer:
            return self.XML_WRITER(writer, self).write(self)


class CSVOps(ABC):
    CSV_READER = None
    CSV_WRITER = None

    @classmethod
    @overload
    def load_csv(cls, filepath: str, offset: int = 0):
        ...

    @classmethod
    @overload
    def load_csv(cls, data: bytes, offset: int = 0):
        ...

    @classmethod
    @overload
    def load_csv(cls, data: bytearray, offset: int = 0):
        ...

    @classmethod
    @overload
    def load_csv(cls, reader: BinaryReader, offset: int = 0):
        ...

    @classmethod
    def load_csv(cls, source: Union[str, bytes, bytearray, BinaryReader], offset: int = 0):
        with BinaryReader.from_auto(source, offset) as reader:
            return cls.CSV_READER(reader).load()

    @overload
    def write_csv(self, filepath):
        ...

    @overload
    def write_csv(self, data: bytearray):
        ...

    @overload
    def write_csv(self, reader: BinaryReader):
        ...

    def write_csv(self, destination: Union[str, bytearray, BinaryReader]) -> None:
        with BinaryWriter.to_auto(destination) as writer:
            return self.CSV_WRITER(writer, self).write(self)
