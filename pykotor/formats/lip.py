from __future__ import annotations

from enum import IntEnum
from typing import List

from pykotor.general.binary_reader import BinaryReader


class Shape(IntEnum):
    EE = 0
    EH = 1
    SCHWA = 2
    AH = 3
    OH = 4
    OOH = 5
    Y = 6
    STS = 7
    FV = 8
    NNG = 9
    TH = 10
    MPB = 11
    TD = 12
    JSH = 13
    L = 14
    KG = 15


class LIP:
    @staticmethod
    def load(data: bytes) -> LIP:
        return _LIPReader.load(data)

    @staticmethod
    def build(self) -> bytes:
        _LIPWriter.build(self)

    def __init__(self):
        self.length: float = 0.0
        self.frames: List[KeyFrame] = []


class KeyFrame:
    @staticmethod
    def new(time: float, shape: Shape) -> KeyFrame:
        keyframe = KeyFrame()
        keyframe.time = time
        keyframe.shape = shape
        return keyframe

    def __init__(self):
        self.time: float = 0.0
        self.shape: Shape = Shape.EE


class _LIPReader:
    @staticmethod
    def load(data: bytes) -> LIP:
        pass
        # TODO


class _LIPWriter:
    @staticmethod
    def build(lip: LIP) -> bytes:
        pass
        # TODO
