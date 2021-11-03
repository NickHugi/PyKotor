from __future__ import annotations

import io
from typing import Optional
from xml.etree import ElementTree

from pykotor.common.stream import BinaryReader, BinaryWriter

import pykotor.resource.formats.lip


class LIPBinaryReader:
    def __init__(self, reader: BinaryReader):
        self._reader: BinaryReader = reader
        self._lip: Optional[pykotor.resource.formats.lip.LIP] = None

    def load(self) -> pykotor.resource.formats.lip.LIP:
        self._lip = pykotor.resource.formats.lip.LIP()

        file_type = self._reader.read_string(4)
        file_version = self._reader.read_string(4)

        if file_type != "LIP ":
            raise TypeError("The file type that was loaded is invalid.")

        if file_version != "V1.0":
            raise TypeError("The LIP version that was loaded is not supported.")

        self._lip.length = self._reader.read_single()
        entry_count = self._reader.read_uint32()

        for i in range(entry_count):
            time = self._reader.read_single()
            shape = pykotor.resource.formats.lip.LIPShape(self._reader.read_uint8())
            self._lip.add(time, shape)

        return self._lip


class LIPBinaryWriter:
    HEADER_SIZE = 16
    LIP_ENTRY_SIZE = 5

    def __init__(self, writer: BinaryWriter, lip: pykotor.resource.formats.lip.LIP):
        self._writer: BinaryWriter = writer
        self._lip: pykotor.resource.formats.lip.LIP = lip

    def write(self) -> None:
        self._writer.write_string("LIP ")
        self._writer.write_string("V1.0")
        self._writer.write_single(self._lip.length)
        self._writer.write_uint32(len(self._lip))

        for keyframe in self._lip:
            self._writer.write_single(keyframe.time)
            self._writer.write_uint8(keyframe.shape.value)

        data = self._writer.data()
        self._writer.close()


class LIPXMLReader:
    def __init__(self, reader: BinaryReader):
        self._xml_root: ElementTree.Element = ElementTree.parse(io.StringIO(reader.read_all().decode())).getroot()
        self._lip: Optional[pykotor.resource.formats.lip.LIP] = None

    def load(self) -> pykotor.resource.formats.lip.LIP:
        if self._xml_root.tag != "lip":
            raise TypeError("The XML file that was loaded was not a valid LIP.")

        self._lip = pykotor.resource.formats.lip.LIP()

        self._lip.length = float(self._xml_root.get("duration"))

        for subelement in self._xml_root:
            time = float(subelement.get("time"))
            shape = pykotor.resource.formats.lip.LIPShape(int(subelement.get("shape")))
            self._lip.add(time, shape)

        return self._lip


class LIPXMLWriter:
    def __init__(self, writer: BinaryWriter, tlk: pykotor.resource.formats.lip.LIP):
        self._lip = tlk
        self._xml_root: ElementTree.Element = ElementTree.Element("lip")
        self._writer = writer

    def write(self) -> None:
        self._xml_root.set("duration", str(self._lip.length))

        for keyframe in self._lip:
            ElementTree.SubElement(self._xml_root,
                                   "keyframe",
                                   time=str(keyframe.time),
                                   shape=str(keyframe.shape.value))

        ElementTree.indent(self._xml_root)
        self._writer.write_bytes(ElementTree.tostring(self._xml_root))
