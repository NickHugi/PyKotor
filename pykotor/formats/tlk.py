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

    def add(self, entry: Entry):
        self.entries.append(entry)

    def set_language(self, language: Language):
        self.language = language


class Entry:
    @staticmethod
    def new(res_ref, text):
        entry = Entry()
        entry.res_ref = res_ref
        entry.text = text
        return entry

    def __init__(self):
        self.res_ref: str = ""
        self.text: str = ""


class _TLKReader(BinaryReader):
    @staticmethod
    def load(data: bytes) -> TLK:
        reader = BinaryReader.from_data(data)
        tlk = TLK()

        file_type = reader.read_string(4)
        file_version = reader.read_string(4)
        tlk.language_id = reader.read_uint32()
        string_count = reader.read_uint32()
        string_entries_offset = reader.read_uint32()

        for i in range(string_count):
            reader.seek(20 + i * 40)
            flags = reader.read_uint32()
            res_ref = reader.read_string(16)
            reader.skip(4)
            reader.skip(4)
            offset_to_string = reader.read_uint32() + string_entries_offset
            string_size = reader.read_uint32()
            reader.skip(4)

            reader.seek(offset_to_string)
            text = reader.read_string(string_size)

            tlk.add(Entry.new(res_ref, text))

        return tlk


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
