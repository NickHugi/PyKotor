from __future__ import annotations

import struct

from pathlib import PurePath
from typing import TYPE_CHECKING

from pykotor.common.stream import BinaryReader, BinaryWriter
from pykotor.extract.file import FileResource, ResourceIdentifier
from pykotor.resource.type import ResourceType
from pykotor.tools.path import CaseAwarePath

if TYPE_CHECKING:
    import os

    from pykotor.common.misc import Game


class Chitin:
    """Chitin object is used for loading the list of resources stored in the chitin.key/.bif files used by the game.

    Chitin support is read-only and you cannot write your own key/bif files with this class yet.
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

        self._resources: list[FileResource]
        self._resource_dict: dict[str, list[FileResource]]
        self.game: Game | None = game
        self.reload()

    def __iter__(
        self,
    ):
        yield from self._resources

    def __len__(
        self,
    ):
        return len(self._resources)

    def reload(self):
        """Reload the list of resource info linked from the chitin.key file."""
        self._resources = []
        self._resource_dict = {}

        keys, bifs = self._get_chitin_data()
        for bif in bifs:  # Loop through all bifs in the chitin.key
            self._resource_dict[bif] = []
            absolute_bif_path = self._base_path.joinpath(bif)
            if self.game is not None and self.game.is_ios():  # For some reason, the chitin.key references the .bif path instead of the correct .bzf path.
                absolute_bif_path = absolute_bif_path.with_suffix(".bzf")
            self.read_bif(absolute_bif_path, keys, bif)

    def read_bif(
        self,
        bif_path: CaseAwarePath,
        keys: dict[int, str],
        bif_filename: str,
    ):
        with BinaryReader.from_file(bif_path) as reader:
            _bif_file_type = reader.read_string(4)        # 0x0
            _bif_file_version = reader.read_string(4)     # 0x4
            resource_count = reader.read_uint32()         # 0x8
            _fixed_resource_count = reader.read_uint32()  # unimplemented/padding (always 0x00000000?)
            resource_offset = reader.read_uint32()        # 0x10 always the value hex 0x14 (dec 20)
            reader.seek(resource_offset)                  # Skip to 0x14
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

    def save(self):
        """(unfinished) Writes the list of resource info to the chitin.key file and associated .bif files."""
        keys, bifs = self._get_chitin_data()
        resource_lookup: dict[str, tuple[PurePath, FileResource]] = {
            resource.resname(): (PurePath(bif), resource)
            for bif, bif_resources in self._resource_dict.items()
            for resource in bif_resources
        }

        # Initialize a dictionary to store bytearrays for each bif file
        bif_data: dict[PurePath, bytearray] = {}
        bif_offsets: dict[PurePath, int] = {}  # To track the current offset for each bif file

        for index, resref in keys.items():
            if resref not in resource_lookup:
                msg = f"Resource {resref} not found."
                raise ValueError(msg)

            this_bif, this_resource = resource_lookup[resref]

            if this_bif not in bif_data:
                bif_data[this_bif] = bytearray()
                bif_offsets[this_bif] = 0  # Initialize offset to 0

            # Accumulate resource data in bytes
            resource_data = this_resource.data()
            restype_id = this_resource.restype().type_id
            resource_data_length = len(resource_data)

            # Calculate the current offset
            current_offset = bif_offsets[this_bif]
            bif_offsets[this_bif] += resource_data_length

            # Format: index, current offset, length, type_id, data
            data_block = struct.pack(f"<I I I I {resource_data_length}s", index, current_offset, resource_data_length, restype_id, resource_data)
            bif_data[this_bif].extend(data_block)

        for bif_path, byte_array_data in bif_data.items():
            absolute_bif_path = self._base_path / bif_path
            merged_bytearrays = bytearray()
            bif_writer = BinaryWriter.to_bytearray(merged_bytearrays)
            # Write file type and version
            bif_writer.write_string("BIFF")  # 0x0
            bif_writer.write_string("V1  ")  # 0x4

            resource_count = len(self._resource_dict[str(bif_path)])
            bif_writer.write_uint32(resource_count)  # 0x8
            bif_writer.write_uint32(0)   # 0xC padding (always 0x00000000?)
            bif_writer.write_uint32(20)  # 0x10 resource offset
            merged_bytearrays.extend(byte_array_data)
            BinaryWriter.dump(absolute_bif_path, merged_bytearrays)

    def _get_chitin_data(self) -> tuple[dict[int, str], list[str]]:
        with BinaryReader.from_file(self._key_path) as reader:
            # _key_file_type = reader.read_string(4)  # noqa: ERA001
            # _key_file_version = reader.read_string(4)  # noqa: ERA001
            reader.skip(8)
            bif_count = reader.read_uint32()
            key_count = reader.read_uint32()
            file_table_offset = reader.read_uint32()
            reader.skip(4)  # key table offset uint32

            files = []
            reader.seek(file_table_offset)
            for _ in range(bif_count):
                reader.skip(4)  # ??? 0x000696E0 in k1, 0x000DDD8A in k2
                file_offset = reader.read_uint32()
                file_length = reader.read_uint16()
                reader.skip(2)  # ??? 0x0001 in K1, 0x0000 in K2
                files.append((file_offset, file_length))

            bifs: list[str] = []
            for file_offset, file_length in files:
                reader.seek(file_offset)
                bif = reader.read_string(file_length)
                bifs.append(bif)

            keys: dict[int, str] = {}
            for _ in range(key_count):
                resref = reader.read_string(16)
                reader.skip(2)  # restype_id uint16
                res_id = reader.read_uint32()
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
        resource = next(
            (resource for resource in self._resources if resource == query),
            None,
        )
        return None if resource is None else resource.data()

    def exists(
        self,
        resref: str,
        restype: ResourceType,
    ) -> bool:
        """Checks if a resource exists in the registry.

        Args:
        ----
            resref: Resource reference string
            restype: Resource type

        Returns:
        -------
            bool: True if resource exists, False otherwise

        Processes the following logic:
            - Constructs a ResourceIdentifier object from the resref and restype
            - Iterates through internal _resources list to find matching resource
            - Returns True if match found, False otherwise.
        """
        query = ResourceIdentifier(resref, restype)
        resource = next(
            (resource for resource in self._resources if resource == query),
            None,
        )
        return resource is not None
