"""This module contains classes for reading and writing GFF files in JSON format."""

from __future__ import annotations

import json

from typing import TYPE_CHECKING, Any, cast

from pykotor.common.language import LocalizedString
from pykotor.resource.formats.gff.gff_data import GFF, GFFFieldType, GFFList, GFFStruct, _GFFField
from pykotor.resource.type import ResourceReader, ResourceWriter, autoclose

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES

# Constants for GFF field types
GFF_FIELD_TYPE_STRUCT = 14
GFF_FIELD_TYPE_LIST = 15
GFF_FIELD_TYPE_LOCSTRING = 12


class GFFJSONReader(ResourceReader):
    """Class for reading GFF data from JSON format.

    This class is responsible for parsing JSON data and converting it into a GFF object.
    """

    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        """Initialize the GFFJSONReader.

        Args:
        ----
            source: The source of the JSON data.
            offset: The byte offset into the source.
            size: The size of the data to read.
        """
        super().__init__(source, offset, size)

    @autoclose
    def load(self, *, auto_close: bool = True) -> GFF:  # noqa: FBT002, FBT001
        """Load the GFF data from JSON.

        Args:
        ----
            auto_close: Whether to automatically close the reader after loading.

        Returns:
        -------
            A GFF object.
        """
        json_data = self._reader.read_string(self._size)
        data = json.loads(json_data)

        gff = GFF()
        gff.root = self._parse_struct(data)
        return gff

    def _parse_struct(self, data: dict[str, Any]) -> GFFStruct:
        """Parse a JSON object into a GFFStruct.

        Args:
        ----
            data: The JSON object to parse.

        Returns:
        -------
            A GFFStruct object.
        """
        struct = GFFStruct()
        struct.struct_id = data.get("struct_id", 0)

        for field_name, field_data in data.get("fields", {}).items():
            field_type = GFFFieldType(field_data.get("type", 0))
            field_value = self._parse_field_value(field_type, field_data.get("value"))
            struct._fields[field_name] = _GFFField(field_type, field_value)

        return struct

    def _parse_field_value(self, field_type: GFFFieldType, value: Any) -> Any:
        """Parse a field value based on its type.

        Args:
        ----
            field_type: The type of the field.
            value: The value to parse.

        Returns:
        -------
            The parsed field value.
        """
        if field_type.value == GFF_FIELD_TYPE_STRUCT:
            return self._parse_struct(value)
        if field_type.value == GFF_FIELD_TYPE_LIST:
            return self._parse_list(value)
        if field_type.value == GFF_FIELD_TYPE_LOCSTRING:
            return self._parse_locstring(value)
        return value

    def _parse_list(self, data: list[dict[str, Any]]) -> GFFList:
        """Parse a JSON array into a GFFList.

        Args:
        ----
            data: The JSON array to parse.

        Returns:
        -------
            A GFFList object.
        """
        gff_list = GFFList()
        for item in data:
            struct = self._parse_struct(item)
            gff_list._structs.append(struct)
        return gff_list

    def _parse_locstring(self, data: dict[str, Any]) -> LocalizedString:
        """Parse a JSON object into a LocalizedString.

        Args:
        ----
            data: The JSON object to parse.

        Returns:
        -------
            A LocalizedString object.
        """
        return LocalizedString.from_dict(data)


class GFFJSONWriter(ResourceWriter):
    """Class for writing GFF data to JSON format.

    This class is responsible for converting a GFF object into JSON data.
    """

    def __init__(
        self,
        gff: GFF,
        target: TARGET_TYPES,
    ):
        """Initialize the GFFJSONWriter.

        Args:
        ----
            gff: The GFF object to write.
            target: The target to write the JSON data to.
        """
        super().__init__(target)
        self._gff = gff

    @autoclose
    def write(self, *, auto_close: bool = True):  # noqa: FBT001, FBT002, ARG002  # pyright: ignore[reportUnusedParameters]
        """Write the GFF data as JSON.

        This method converts the GFF object to a JSON object and writes it to the target.
        """
        json_data = self._serialize_struct(self._gff.root)
        json_str = json.dumps(json_data, indent=2)
        self._writer.write_string(json_str)

    def _serialize_struct(self, struct: GFFStruct) -> dict[str, Any]:
        """Serialize a GFFStruct to a JSON object.

        Args:
        ----
            struct: The GFFStruct to serialize.

        Returns:
        -------
            A JSON object.
        """
        result: dict[str, Any] = {"struct_id": struct.struct_id, "fields": {}}
        for field_name, field in struct._fields.items():
            result["fields"][field_name] = {
                "type": field.field_type().value,
                "value": self._serialize_field_value(field),
            }
        return result

    def _serialize_field_value(self, field: _GFFField) -> Any:
        """Serialize a field value based on its type.

        Args:
        ----
            field: The field to serialize.

        Returns:
        -------
            The serialized field value.
        """
        field_type = field.field_type()
        field_value = field.value()
        if field_type.value == GFF_FIELD_TYPE_STRUCT:
            return self._serialize_struct(cast("GFFStruct", field_value))
        if field_type.value == GFF_FIELD_TYPE_LIST:
            return self._serialize_list(cast("GFFList", field_value))
        if field_type.value == GFF_FIELD_TYPE_LOCSTRING:
            return self._serialize_locstring(cast("LocalizedString", field_value))
        return field_value

    def _serialize_list(self, gff_list: GFFList) -> list[dict[str, Any]]:
        """Serialize a GFFList to a JSON array.

        Args:
        ----
            gff_list: The GFFList to serialize.

        Returns:
        -------
            A JSON array.
        """
        return [self._serialize_struct(struct) for struct in gff_list._structs]

    def _serialize_locstring(self, locstring: LocalizedString) -> dict[str, Any]:
        """Serialize a LocalizedString to a JSON object.

        Args:
        ----
            locstring: The LocalizedString to serialize.

        Returns:
        -------
            A JSON object.
        """
        return locstring.to_dict()
