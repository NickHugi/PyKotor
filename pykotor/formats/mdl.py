from __future__ import annotations

import io
from enum import IntEnum
from typing import List, Optional

from pykotor.data.vertex import Vertex
from pykotor.general.binary_reader import BinaryReader
from pykotor.general.binary_writer import BinaryWriter


class ModelType(IntEnum):
    Other = 0
    Effect = 1
    MoveEffect = 2
    CharacterOrCamera = 4
    Door = 8
    Lightsaber = 16
    Placeable = 32
    Unknown = 64


class MDL:
    @staticmethod
    def load_binary(mdl_data: bytearray, mdx_data: Optional[bytearray] = None) -> MDL:
        return _MDLReader.load(mdl_data, mdx_data)

    @staticmethod
    def load_ascii(mdl_data: str):
        return _MDLReaderAscii.build(mdl_data)

    @staticmethod
    def build_binary(self):
        return _MDLWriter.build(self)

    @staticmethod
    def build_ascii(self):
        return _MDLWriterAscii.build(self)

    def __init__(self):
        self.model_name: str = ""
        self.supermodel: str = ""
        self.root: Node = Node()
        self.animations: List[Animation] = []
        self.box_min: Vertex = Vertex()
        self.box_max: Vertex = Vertex()
        self.radius: float = 0.0
        self.animation_scale: float = 1.0
        self.enable_fog: bool = False
        self.model_type: ModelType = ModelType.Other


class Node:
    def __init__(self):
        self.children: List[Node] = []
        self.controller: List = []


class Animation:
    pass


class _MDLReader:
    @staticmethod
    def load(mdl_data: bytearray, mdx_data:bytearray) -> MDL:
        pass
        # TODO


class _MDLWriter:
    @staticmethod
    def build(mdl: MDL) -> bytearray:
        pass
        # TODO


class _MDLReaderAscii:
    @staticmethod
    def load(mdl_data: str) -> MDL:
        pass
        # TODO


class _MDLWriterAscii:
    @staticmethod
    def build(mdl: MDL) -> str:
        pass