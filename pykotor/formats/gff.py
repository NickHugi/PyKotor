from __future__ import annotations

import io
from enum import Enum, IntEnum
from typing import Union, BinaryIO, List
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

from pykotor.general.binary_reader import BinaryReader
from pykotor.general.binary_writer import BinaryWriter


class GFFType(Enum):
    GFF = 0
    IFO = 1
    ARE = 2
    GIT = 3
    UTC = 4
    UTD = 5
    UTE = 6
    UTI = 7
    UTP = 8
    UTS = 9
    UTM = 10
    UTT = 11
    UTW = 12
    DLG = 13
    JRL = 14
    FAC = 15
    ITP = 16

    def __str__(self):
        return self.nam


class FieldType(IntEnum):
    UInt8 = 0
    Int8 = 1
    UInt16 = 2
    Int16 = 3
    UInt32 = 4
    Int32 = 5
    UInt64 = 6
    Int64 = 7
    Float = 8
    Double = 9
    String = 10
    ResRef = 11
    LocalizedString = 12
    Binary = 13
    Struct = 14
    List = 15
    Vector4f = 16
    Vector3f = 17


class GFF:
    @staticmethod
    def load_binary(data: bytes) -> GFF:
        return _GFFReader.load(data)

    @staticmethod
    def load_xml(data: str) -> GFF:
        return _GFFReaderXML.load(data)

    def build_binary(self) -> bytes:
        return _GFFWriter.build(self)

    def build_xml(self) -> str:
        return _GFFWriterXML.build(self)

    def __init__(self):
        self.root = Struct.new(-1)
        self.gff_type = GFFType.GFF


class Struct:
    @staticmethod
    def new(struct_type: int) -> Struct:
        struct = Struct()
        struct.struct_type = struct_type
        return struct

    def __init__(self):
        self.struct_type: int = 0
        self.fields: List[Field] = []


class Field:
    # TODO
    @staticmethod
    def new_uint8(label: str, value: int) -> Field:
        field = Field()
        field.field_type = FieldType.UInt8
        field.label = label
        field.value = value
        return field

    def __init__(self):
        self.field_type = FieldType.UInt8
        self.label: str = ""
        self.value = 0


class _GFFReader(BinaryReader):
    @staticmethod
    def load(data: bytes) -> GFF:
        pass
        # TODO


class _GFFWriter(BinaryWriter):
    @staticmethod
    def build(gff: GFF) -> bytes:
        pass
        # TODO


class _GFFReaderXML:
    @staticmethod
    def load(data: str) -> GFF:
        pass
        # TODO


class _GFFWriterXML:
    @staticmethod
    def build(gff: GFF) -> str:
        pass
        # TODO
