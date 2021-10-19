"""
This module contains abstract classes intended to reduce boilerplate code for loading and writing methods present in
resource classes found in the submodules.
"""

from abc import ABC
from typing import overload, Union

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
    def load_binary(cls, reader: BinaryReader, offset: int = 0):
        ...

    @classmethod
    def load_binary(cls, source: Union[str, bytes, BinaryReader], offset: int = 0):
        with BinaryReader.from_auto(source, offset) as reader:
            return cls.BINARY_READER(reader).load()

    @classmethod
    @overload
    def write_binary(cls, filepath):
        ...

    @classmethod
    @overload
    def write_binary(cls, data: bytes):
        ...

    @classmethod
    @overload
    def write_binary(cls, reader: BinaryReader):
        ...

    @classmethod
    def write_binary(cls, source: Union[str, bytes, BinaryReader]):
        with BinaryWriter.to_auto(source) as reader:
            return cls.BINARY_WRITER(reader).load()


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
    def load_xml(cls, reader: BinaryReader, offset: int = 0):
        ...

    @classmethod
    def load_xml(cls, source: Union[str, bytes, BinaryReader], offset: int = 0):
        with BinaryReader.from_auto(source, offset) as reader:
            return cls.XML_READER(reader).load()

    @classmethod
    @overload
    def write_xml(cls, filepath):
        ...

    @classmethod
    @overload
    def write_xml(cls, data: bytes):
        ...

    @classmethod
    @overload
    def write_xml(cls, reader: BinaryReader):
        ...

    @classmethod
    def write_xml(cls, source: Union[str, bytes, BinaryReader]):
        with BinaryWriter.to_auto(source) as reader:
            return cls.XML_WRITER(reader).load()


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
    def load_csv(cls, reader: BinaryReader, offset: int = 0):
        ...

    @classmethod
    def load_csv(cls, source: Union[str, bytes, BinaryReader], offset: int = 0):
        with BinaryReader.from_auto(source, offset) as reader:
            return cls.CSV_READER(reader).load()

    @classmethod
    @overload
    def write_csv(cls, filepath):
        ...

    @classmethod
    @overload
    def write_csv(cls, data: bytes):
        ...

    @classmethod
    @overload
    def write_csv(cls, reader: BinaryReader):
        ...

    @classmethod
    def write_csv(cls, source: Union[str, bytes, BinaryReader]):
        with BinaryWriter.to_auto(source) as reader:
            return cls.CSV_WRITER(reader).load()
