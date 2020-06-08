from __future__ import annotations

import io
from typing import Union, List, Type, BinaryIO

from pykotor.general.binary_reader import BinaryReader
from pykotor.general.binary_writer import BinaryWriter
from pykotor.types import ResourceType, resource_types
import pykotor.formats.rim


class ERF:
    @staticmethod
    def load(data: bytes) -> ERF:
        return _ERFReader.load(data)

    def build(self) -> bytes:
        return _ERFWriter.build(self)

    def to_rim(self) -> pykotor.formats.rim.RIM:
        pass
        # TODO

    def __init__(self):
        self.resources: List[Resource] = []

    def add(self, resource: Resource) -> None:
        self.resources.append(resource)

    def remove(self, index: int) -> Resource:
        resource = self.resources[index]
        del self.resources[index]
        return resource

    def get(self, index: int) -> Resource:
        return self.resources[index]

    def all(self) -> List[Resource]:
        return self.resources


class Resource:
    @staticmethod
    def new(res_ref: str, res_type: Union[str, int, ResourceType], res_data: bytearray) -> Resource:
        resource = Resource()
        resource.res_ref = res_ref
        resource.res_type = ResourceType.get(res_type)
        resource.res_data = res_data
        return resource

    def __init__(self):
        self.res_ref: str = ""
        self.res_type: ResourceType = resource_types[0]
        self.res_data: bytearray = bytearray()


class _ERFReader(BinaryReader):
    @staticmethod
    def load(data: bytes) -> ERF:
        reader = BinaryReader.from_data(data)
        erf = ERF()

        file_type = reader.read_string(4)
        file_version = reader.read_string(4)
        reader.seek(16)
        resource_count = reader.read_uint32()
        reader.seek(24)
        key_list_offset = reader.read_uint32()
        resource_list_offset = reader.read_uint32()

        for i in range(resource_count):
            reader.seek(key_list_offset + 24 * i)
            res_ref = reader.read_string(16)
            reader.skip(4)
            res_type = ResourceType.get(reader.read_uint16())
            reader.skip(2)

            reader.seek(resource_list_offset + 8 * i)
            res_offset = reader.read_uint32()
            res_size = reader.read_uint32()

            reader.seek(res_offset)
            res_data = reader.read_bytes(res_size)
            erf.add(Resource.new(res_ref, res_type, res_data))

        return erf


class _ERFWriter(BinaryWriter):
    @staticmethod
    def build(erf: ERF) -> bytes:
        pass
        # TODO
