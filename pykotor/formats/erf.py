from __future__ import annotations

import io
from typing import Union, List, Type, BinaryIO

from pykotor.formats.rim import RIM
from pykotor.general.binary_reader import BinaryReader
from pykotor.general.binary_writer import BinaryWriter
from pykotor.types import ResourceType, resource_types


class ERF:
    @staticmethod
    def load(data: bytes) -> ERF:
        return _ERFReader.load(data)

    def build(self) -> bytes:
        return _ERFWriter.build(self)

    def to_rim(self) -> RIM:
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
        pass
        # TODO


class _ERFWriter(BinaryWriter):
    @staticmethod
    def build(erf: ERF) -> bytes:
        pass
        # TODO
