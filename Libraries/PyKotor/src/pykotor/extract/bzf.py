from __future__ import annotations

import lzma
import struct

from dataclasses import dataclass
from typing import TYPE_CHECKING, BinaryIO

if TYPE_CHECKING:
    from pykotor.extract.keyfile import BIFResource, KEYFile

# Constants
BZF_ID = b"BIFF"
VERSION_1 = b"V1  "


@dataclass
class IResource:
    offset: int = 0
    size: int = 0
    type: int = 0
    packed_size: int = 0


@dataclass
class Resource:
    name: str = ""
    type: int = 0
    index: int = 0


class BZFFile:
    """Reads BZF (compressed BIF) files.
    
    BZF files are LZMA-compressed BIF archives used in KotOR. This class handles
    decompression and resource indexing for compressed BIF files.
    
    References:
    ----------
        vendor/reone/src/libs/resource/format/bifreader.cpp (BIF/BZF reading)
        vendor/xoreos-tools/src/unkeybif.cpp (BIF/BZF extraction)
        vendor/KotOR-Bioware-Libs/BIF.pm (Perl BIF/BZF implementation)
    
    Missing Features:
    ----------------
        - Fixed resources not yet supported (see line 67)
    """
    def __init__(self, bzf: BinaryIO):
        self._bzf: BinaryIO = bzf
        self._resources: list[Resource] = []
        self._iResources: list[IResource] = []
        self.load(bzf)

    def load(self, bzf: BinaryIO):
        self._read_header(bzf)

        if self._id != BZF_ID:
            raise ValueError(f"Not a BZF file ({self._id})")

        if self._version != VERSION_1:
            raise ValueError(f"Unsupported BZF file version {self._version}")

        var_res_count = struct.unpack("<I", bzf.read(4))[0]
        fix_res_count = struct.unpack("<I", bzf.read(4))[0]

        if fix_res_count != 0:
            raise NotImplementedError("Fixed BZF resources are not supported yet")

        self._iResources = [IResource() for _ in range(var_res_count)]

        off_var_res_table = struct.unpack("<I", bzf.read(4))[0]

        self._read_var_res_table(bzf, off_var_res_table)

    def _read_header(self, bzf: BinaryIO):
        self._id = bzf.read(4)
        self._version = bzf.read(4)

    def _read_var_res_table(self, bzf: BinaryIO, offset: int):
        bzf.seek(offset)

        for i in range(len(self._iResources)):
            bzf.read(4)  # Skip ID

            self._iResources[i].offset = struct.unpack("<I", bzf.read(4))[0]
            self._iResources[i].size = struct.unpack("<I", bzf.read(4))[0]
            self._iResources[i].type = struct.unpack("<I", bzf.read(4))[0]

            if i > 0:
                self._iResources[i - 1].packed_size = self._iResources[i].offset - self._iResources[i - 1].offset

        if self._iResources:
            self._iResources[-1].packed_size = bzf.seek(0, 2) - self._iResources[-1].offset

    def merge_KEY(self, key: KEYFile, data_file_index: int):
        key_res_list: list[BIFResource] = key.get_resources()

        for key_res in key_res_list:
            if key_res.bif_index != data_file_index:
                continue

            if key_res.res_index >= len(self._iResources):
                print(f"Resource index out of range ({key_res.res_index}/{len(self._iResources)})")
                continue

            if key_res.type != self._iResources[key_res.res_index].type:
                print(f'KEY and BZF disagree on the type of the resource "{key_res.name}" ' f"({key_res.type}, {self._iResources[key_res.res_index].type}). Trusting the BZF")

            res = Resource()
            res.name = key_res.name
            res.type = self._iResources[key_res.res_index].type
            res.index = key_res.res_index

            self._resources.append(res)

    def get_internal_resource_count(self) -> int:
        return len(self._iResources)

    def get_resources(self) -> list[Resource]:
        return self._resources

    def get_iresource(self, index: int) -> IResource:
        if index >= len(self._iResources):
            raise IndexError(f"Resource index out of range ({index}/{len(self._iResources)})")
        return self._iResources[index]

    def get_resource_size(self, index: int) -> int:
        return self.get_iresource(index).size

    def get_resource(self, index: int) -> bytes:
        res = self.get_iresource(index)
        self._bzf.seek(res.offset)
        compressed_data: bytes = self._bzf.read(res.packed_size)
        return lzma.decompress(compressed_data, format=lzma.FORMAT_RAW, filters=[{"id": lzma.FILTER_LZMA1}])
