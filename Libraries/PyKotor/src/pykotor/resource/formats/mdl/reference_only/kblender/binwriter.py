from __future__ import annotations

import struct

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import os

    from types import TracebackType

    from typing_extensions import Literal, Self


class BinaryWriter:
    def __init__(
        self,
        path: os.PathLike | str,
        byteorder: Literal["little", "big"] = "little",
    ):
        self.file_path = Path(path)
        self.byteorder: Literal["little", "big"] = byteorder

    def __enter__(self) -> Self:
        self.file = self.file_path.open("wb")
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ):
        if self.file:
            self.file.close()

    def tell(self):
        return self.file.tell()

    def write_int8(self, val: int):
        self.file.write(val.to_bytes(1, byteorder=self.byteorder, signed=True))

    def write_int16(self, val: int):
        self.file.write(val.to_bytes(2, byteorder=self.byteorder, signed=True))

    def write_int32(self, val: int):
        self.file.write(val.to_bytes(4, byteorder=self.byteorder, signed=True))

    def write_uint8(self, val: int):
        self.file.write(val.to_bytes(1, byteorder=self.byteorder, signed=False))

    def write_uint16(self, val: int):
        self.file.write(val.to_bytes(2, byteorder=self.byteorder, signed=False))

    def write_uint32(self, val: int):
        self.file.write(val.to_bytes(4, byteorder=self.byteorder, signed=False))

    def write_float(self, val: float):
        bo_literal = ">" if self.byteorder == "big" else "<"
        self.file.write(struct.pack(bo_literal + "f", val))

    def write_string(self, val: str):
        self.file.write(val.encode("utf-8"))

    def write_c_string(self, val: str):
        self.file.write((val + "\0").encode("utf-8"))

    def write_bytes(self, data: bytes):
        self.file.write(data)
