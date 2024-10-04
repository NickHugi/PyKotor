from __future__ import annotations

import struct

from typing import TYPE_CHECKING, BinaryIO

from filelock.version import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Literal


class SeekOrigin:
    BEGIN: Literal[0] = 0
    CURRENT: Literal[1] = 1
    END: Literal[2] = 2


class BinaryReader:
    def __init__(self, path: str, byteorder: Literal["little", "big"] = "little"):
        self.file: BinaryIO = open(path, "rb")
        self.byteorder: Literal["little", "big"] = byteorder

    def __del__(self):
        self.file.close()

    def seek(
        self,
        offset: int,
        origin: Literal[0, 1, 2] = SeekOrigin.BEGIN,
    ):
        self.file.seek(offset, origin)

    def skip(self, offset: int):
        self.file.seek(offset, SeekOrigin.CURRENT)

    def tell(self):
        return self.file.tell()

    def read_int8(self) -> int:
        return int.from_bytes(self.file.read(1), self.byteorder, signed=True)

    def read_int16(self) -> int:
        return int.from_bytes(self.file.read(2), self.byteorder, signed=True)

    def read_int32(self) -> int:
        return int.from_bytes(self.file.read(4), self.byteorder, signed=True)

    def read_uint8(self) -> int:
        return int.from_bytes(self.file.read(1), self.byteorder, signed=False)

    def read_uint16(self) -> int:
        return int.from_bytes(self.file.read(2), self.byteorder, signed=False)

    def read_uint32(self) -> int:
        return int.from_bytes(self.file.read(4), self.byteorder, signed=False)

    def read_float(self) -> float:
        bo_literal: Literal[">", "<"] = ">" if self.byteorder == "big" else "<"
        [val] = struct.unpack(bo_literal + "f", self.file.read(4))
        return val

    def read_string(self, length: int) -> str:
        return self.file.read(length).decode("utf-8")

    def read_c_string(self) -> str:
        s: str = ""
        while True:
            ch = self.file.read(1).decode("utf-8")
            if ch == "\0":
                break
            s += ch
        return s

    def read_c_string_up_to(self, max_len: int) -> str:
        s: str = ""
        length: int = max_len
        while length > 0:
            ch = self.file.read(1).decode("utf-8")
            length -= 1
            if ch == "\0":
                break
            s += ch
        if length > 0:
            self.file.seek(length, 1)
        return s

    def read_bytes(self, count: int) -> bytes:
        return self.file.read(count)
