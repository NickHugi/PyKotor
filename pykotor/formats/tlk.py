from __future__ import annotations
import io
from typing import List, BinaryIO, Union
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

from pykotor.general.binary_reader import BinaryReader
from pykotor.general.binary_writer import BinaryWriter
from pykotor.types import Language


class TLK:
    @staticmethod
    def load_binary(data: bytes) -> TLK:
        return _TLKReader.load(data)

    @staticmethod
    def load_xml(data: str) -> TLK:
        return _TLKReaderXML.load(data)

    def build_binary(self) -> bytes:
        return _TLKWriter.build(self)

    def build_xml(self) -> str:
        return _TLKWriterXML.build(self)

    def __init__(self):
        self.entries: List[Entry] = []
        self.language: Language = Language.English


class Entry:
    def __init__(self):
        self.res_ref: str = ""
        self.text: str = ""


class _TLKReader(BinaryReader):
    @staticmethod
    def load(data: bytes) -> TLK:
        pass
        # TODO


class _TLKWriter(BinaryWriter):
    @staticmethod
    def build(tlk: TLK) -> bytes:
        pass
        # TODO


class _TLKReaderXML:
    @staticmethod
    def load(data: str) -> TLK:
        pass
        # TODO


class _TLKWriterXML:
    @staticmethod
    def build(tlk: TLK) -> str:
        pass
        # TODO
