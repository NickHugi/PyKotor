from __future__ import annotations

from pathlib import Path
import struct

from pathlib import PurePath
from typing import TYPE_CHECKING

from pykotor.common.stream import BinaryReader
from pykotor.extract.file import FileResource, ResourceIdentifier
from pykotor.resource.type import ResourceType
from pykotor.tools.path import CaseAwarePath

if TYPE_CHECKING:
    import os

    from collections.abc import Iterator

    from pykotor.common.misc import Game


class Chitin:
    """Chitin object is used for loading the list of resources stored in the chitin.key/.bif files used by the game.

    Chitin support is read-only and you cannot write your own key/bif files with this class yet.
    
    References:
    ----------
        vendor/reone/src/libs/resource/format/keyreader.cpp:26-65 (KEY reading)
        vendor/reone/src/libs/resource/format/bifreader.cpp:26-63 (BIF reading)
        vendor/xoreos-tools/src/unkeybif.cpp (KEY/BIF extraction tool)
    """

    KEY_ELEMENT_SIZE = 8

    def __init__(
        self,
        key_path: os.PathLike | str,
        base_path: os.PathLike | str | None = None,
        game: Game | None = None,
    ):
        self._key_path: CaseAwarePath = CaseAwarePath(key_path)
        base_path = self._key_path.parent if base_path is None else base_path
        self._base_path: CaseAwarePath = CaseAwarePath(base_path)

        self._resources: list[FileResource] = []
        self._resource_dict: dict[str, list[FileResource]] = {}
        self.game: Game | None = game
        self.load()

    def __iter__(
        self,
    ) -> Iterator[FileResource]:
        yield from self._resources

    def __len__(
        self,
    ):
        return len(self._resources)

    def load(self):
        """Reload the list of resource info linked from the chitin.key file."""
        self._resources.clear()
        self._resource_dict.clear()

        keys: dict[int, str]
        bifs: list[str]
        keys, bifs = self._get_chitin_data()
        for bif in bifs:  # Loop through all bifs in the chitin.key
            self._resource_dict[bif] = []
            absolute_bif_path: Path = self._base_path.joinpath(bif)
            if self.game is not None and self.game.is_ios():  # For some reason, the chitin.key references the .bif path instead of the correct .bzf path.
                absolute_bif_path = absolute_bif_path.with_suffix(".bzf")
            self.read_bif(absolute_bif_path, keys, bif)

    def read_bif(
        self,
        bif_path: Path,
        keys: dict[int, str],
        bif_filename: str,
    ):
        # vendor/reone/src/libs/resource/format/bifreader.cpp:26-63
        with BinaryReader.from_file(bif_path) as reader:
            _bif_file_type: str = reader.read_string(4)  # 0x0
            _bif_file_version: str = reader.read_string(4)  # 0x4
            resource_count: int = reader.read_uint32()  # 0x8
            _fixed_resource_count: int = reader.read_uint32()  # unimplemented/padding (always 0x00000000?)
            resource_offset: int = reader.read_uint32()  # 0x10 always the value hex 0x14 (dec 20)
            reader.seek(resource_offset)  # Skip to 0x14
            # vendor/reone/src/libs/resource/format/bifreader.cpp:50-63
            for _ in range(resource_count):
                # Initialize the FileResource and add to this chitin object's collections.
                resource = FileResource(
                    resname=keys[reader.read_uint32()],  # resref str
                    offset=reader.read_uint32(),
                    size=reader.read_uint32(),
                    restype=ResourceType.from_id(reader.read_uint32()),
                    filepath=bif_path,
                )
                self._resources.append(resource)
                self._resource_dict[bif_filename].append(resource)

    def _get_chitin_data(self) -> tuple[dict[int, str], list[str]]:
        # vendor/reone/src/libs/resource/format/keyreader.cpp:26-65
        with BinaryReader.from_file(self._key_path) as reader:
            # _key_file_type = reader.read_string(4)  # noqa: ERA001
            # _key_file_version = reader.read_string(4)  # noqa: ERA001
            reader.skip(8)
            bif_count: int = reader.read_uint32()
            key_count: int = reader.read_uint32()
            file_table_offset: int = reader.read_uint32()
            reader.skip(4)  # key table offset uint32

            # vendor/reone/src/libs/resource/format/keyreader.cpp:38-59
            files: list[tuple[int, int]] = []
            reader.seek(file_table_offset)
            for _ in range(bif_count):
                reader.skip(4)  # ??? 0x000696E0 in k1, 0x000DDD8A in k2
                file_offset: int = reader.read_uint32()
                file_length: int = reader.read_uint16()
                reader.skip(2)  # ??? 0x0001 in K1, 0x0000 in K2
                files.append((file_offset, file_length))

            bifs: list[str] = []
            for file_offset, file_length in files:
                reader.seek(file_offset)
                bif: str = reader.read_string(file_length)
                bifs.append(bif)

            # vendor/reone/src/libs/resource/format/keyreader.cpp:61-68
            keys: dict[int, str] = {}
            for _ in range(key_count):
                resref: str = reader.read_string(16)
                reader.skip(2)  # restype_id uint16
                res_id: int = reader.read_uint32()
                keys[res_id] = resref

            return keys, bifs

    def resource(
        self,
        resref: str,
        restype: ResourceType,
    ) -> bytes | None:
        """Returns the bytes data of the specified resource. If the resource does not exist then returns None instead.

        Args:
        ----
            resref: The resource ResRef.
            restype: The resource type.

        Returns:
        -------
            None or bytes data of resource.
        """
        query = ResourceIdentifier(resref, restype)
        resource: FileResource | None = next(
            (resource for resource in self._resources if resource == query),
            None,
        )
        return None if resource is None else resource.data()
