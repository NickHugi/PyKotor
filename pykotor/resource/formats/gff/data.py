"""
This module handles classes relating to editing LIP files.
"""
from __future__ import annotations

from copy import copy, deepcopy
from enum import IntEnum, Enum
from typing import List, Optional, Any, Dict, TypeVar, Union

from pykotor.common.geometry import Vector3, Vector4
from pykotor.common.language import LocalizedString
from pykotor.common.misc import ResRef


T = TypeVar("T")
U = TypeVar("U")


class GFFContent(Enum):
    """
    The different resources that the GFF can represent.
    """
    GFF = "GFF "
    IFO = "IFO "
    ARE = "ARE "
    GIT = "GIT "
    UTC = "UTC "
    UTD = "UTD "
    UTE = "UTE "
    UTI = "UTI "
    UTP = "UTP "
    UTS = "UTS "
    UTM = "UTM "
    UTT = "UTT "
    UTW = "UTW "
    DLG = "DLG "
    JRL = "JRL "
    FAC = "FAC "
    ITP = "ITP "
    BIC = "BIC "
    GUI = "GUI "
    PTH = "PTH "

    @classmethod
    def has_value(cls, value):
        for gff_content in GFFContent:
            if gff_content.value == value:
                return True
        else:
            return False


class GFFFieldType(IntEnum):
    """
    The different types of fields based off what kind of data it stores.
    """
    UInt8 = 0
    Int8 = 1
    UInt16 = 2
    Int16 = 3
    UInt32 = 4
    Int32 = 5
    UInt64 = 6
    Int64 = 7
    Single = 8
    Double = 9
    String = 10
    ResRef = 11
    LocalizedString = 12
    Binary = 13
    Struct = 14
    List = 15
    Vector4 = 16
    Vector3 = 17

    def return_type(self):
        if self in [GFFFieldType.UInt8, GFFFieldType.Int8, GFFFieldType.UInt16, GFFFieldType.Int16,
                    GFFFieldType.UInt32, GFFFieldType.Int32, GFFFieldType.UInt16, GFFFieldType.UInt64]:
            return int
        else:
            return str


class GFF:
    """
    Represents the data of a GFF file.
    """

    def __init__(self, content: GFFContent = GFFContent.GFF):
        self.content: GFFContent = content
        self.root: GFFStruct = GFFStruct(-1)

    def print_tree(self, root: Optional[GFFStruct] = None, indent: int = 0, column_len: int = 40):
        if root is None:
            root = self.root

        for label, field_type, value in root:
            value_str = str(value)
            if field_type is GFFFieldType.Struct:
                value_str = value.struct_id
            if field_type is GFFFieldType.List:
                value_str = len(value)

            print(("  "*indent + label).ljust(column_len), " ", value_str)

            if field_type is GFFFieldType.Struct:
                self.print_tree(value, indent + 1)
            if field_type is GFFFieldType.List:
                for i, child_struct in enumerate(value):
                    print("  {}[Struct {}]".format("  "*indent, i).ljust(column_len), " ", child_struct.struct_id)
                    self.print_tree(child_struct, indent + 2)


class _GFFField:
    """
    Read-only data structure for items stored in GFFStruct.
    """

    INTEGER_TYPES = {GFFFieldType.Int8, GFFFieldType.UInt8, GFFFieldType.Int16, GFFFieldType.UInt16,
                     GFFFieldType.Int32, GFFFieldType.UInt32, GFFFieldType.Int64, GFFFieldType.UInt64}
    STRING_TYPES = {GFFFieldType.String, GFFFieldType.ResRef}
    FLOAT_TYPES = {GFFFieldType.Single, GFFFieldType.Double}

    def __init__(self, field_type: GFFFieldType, value: Any):
        self._field_type: GFFFieldType = field_type
        self._value: Any = value

    def field_type(self) -> GFFFieldType:
        """
        Returns the field type.

        Returns:
            The field's field_type.
        """
        return self._field_type

    def value(self) -> Any:
        """
        Returns the value.

        Returns:
            The field's value.
        """
        return self._value


class GFFStruct:
    """
    Stores a collection of GFFFields.

    Attributes:
        struct_id: User defined id.
    """

    def __init__(self, struct_id: int = 0):
        self.struct_id: int = struct_id
        self._fields: Dict[str, _GFFField] = {}

    def __len__(self):
        """
        Returns the number of fields.
        """
        return len(self._fields.values())

    def __iter__(self):
        """
        Iterates through the stored fields yielding each field's (label, type, value)
        """
        for label, field in self._fields.items():
            yield label, field.field_type(), field.value()

    def __getitem__(self, item):
        """
        Returns the value of the specified field.
        """
        if not isinstance(item, str):
            return NotImplemented
        return self._fields[item].value()

    def remove(self, label: str) -> None:
        """
        Removes the field with the specified label.

        Args:
            label: The field label.
        """
        if label in self._fields:
            self._fields.pop(label)

    def exists(self, label: str) -> bool:
        """
        Returns the type of the field with the specified label.

        Args:
            label: The field label.

        Returns:
            A GFFFieldType value.
        """
        return True if label in self._fields else None

    def acquire(self, label: str, default: T, object_type: U = None) -> Union[T, U]:
        """
        Gets the value from the specified field. If the field does not exist or the value type does not match the
        specified type then the default is returned instead.

        Args:
            label: The field label.
            default: Default value to return if value does not match object_type.
            object_type: The preferred type of the field value. If not specified it will match the default's type.

        Returns:
            The field value or default value.
        """
        value = default
        if object_type is None:
            object_type = type(value)
        if self.exists(label) and isinstance(self[label], object_type):
            value = self[label]
        return value

    def set_uint8(self, label: str, value: int) -> None:
        """
        Sets the value and field type of the field with the specified label.

        Args:
            label: The field label.
            value: The new field value.
        """
        self._fields[label] = _GFFField(GFFFieldType.UInt8, value)

    def set_uint16(self, label: str, value: int) -> None:
        """
        Sets the value and field type of the field with the specified label.

        Args:
            label: The field label.
            value: The new field value.
        """
        self._fields[label] = _GFFField(GFFFieldType.UInt16, value)

    def set_uint32(self, label: str, value: int) -> None:
        """
        Sets the value and field type of the field with the specified label.

        Args:
            label: The field label.
            value: The new field value.
        """
        self._fields[label] = _GFFField(GFFFieldType.UInt32, value)

    def set_uint64(self, label: str, value: int) -> None:
        """
        Sets the value and field type of the field with the specified label.

        Args:
            label: The field label.
            value: The new field value.
        """
        self._fields[label] = _GFFField(GFFFieldType.UInt64, value)

    def set_int8(self, label: str, value: int) -> None:
        """
        Sets the value and field type of the field with the specified label.

        Args:
            label: The field label.
            value: The new field value.
        """
        self._fields[label] = _GFFField(GFFFieldType.Int8, value)

    def set_int16(self, label: str, value: int) -> None:
        """
        Sets the value and field type of the field with the specified label.

        Args:
            label: The field label.
            value: The new field value.
        """
        self._fields[label] = _GFFField(GFFFieldType.Int16, value)

    def set_int32(self, label: str, value: int) -> None:
        """
        Sets the value and field type of the field with the specified label.

        Args:
            label: The field label.
            value: The new field value.
        """
        self._fields[label] = _GFFField(GFFFieldType.Int32, value)

    def set_int64(self, label: str, value: int) -> None:
        """
        Sets the value and field type of the field with the specified label.

        Args:
            label: The field label.
            value: The new field value.
        """
        self._fields[label] = _GFFField(GFFFieldType.Int64, value)

    def set_single(self, label: str, value: float) -> None:
        """
        Sets the value and field type of the field with the specified label.

        Args:
            label: The field label.
            value: The new field value.
        """
        self._fields[label] = _GFFField(GFFFieldType.Single, value)

    def set_double(self, label: str, value: float) -> None:
        """
        Sets the value and field type of the field with the specified label.

        Args:
            label: The field label.
            value: The new field value.
        """
        self._fields[label] = _GFFField(GFFFieldType.Double, value)

    def set_resref(self, label: str, value: ResRef) -> None:
        """
        Sets the value and field type of the field with the specified label.

        Args:
            label: The field label.
            value: The new field value.
        """
        self._fields[label] = _GFFField(GFFFieldType.ResRef, value)

    def set_string(self, label: str, value: str) -> None:
        """
        Sets the value and field type of the field with the specified label.

        Args:
            label: The field label.
            value: The new field value.
        """
        self._fields[label] = _GFFField(GFFFieldType.String, value)

    def set_locstring(self, label: str, value: LocalizedString) -> None:
        """
        Sets the value and field type of the field with the specified label.

        Args:
            label: The field label.
            value: The new field value.
        """
        self._fields[label] = _GFFField(GFFFieldType.LocalizedString, value)

    def set_binary(self, label: str, value: bytes) -> None:
        """
        Sets the value and field type of the field with the specified label.

        Args:
            label: The field label.
            value: The new field value.
        """
        self._fields[label] = _GFFField(GFFFieldType.Binary, value)

    def set_vector3(self, label: str, value: Vector3) -> None:
        """
        Sets the value and field type of the field with the specified label.

        Args:
            label: The field label.
            value: The new field value.
        """
        self._fields[label] = _GFFField(GFFFieldType.Vector3, value)

    def set_vector4(self, label: str, value: Vector4) -> None:
        """
        Sets the value and field type of the field with the specified label.

        Args:
            label: The field label.
            value: The new field value.
        """
        self._fields[label] = _GFFField(GFFFieldType.Vector4, value)

    def set_struct(self, label: str, value: GFFStruct) -> GFFStruct:
        """
        Sets the value and field type of the field with the specified label.

        Args:
            label: The field label.
            value: The new field value.

        Returns:
            The value that was passed to the method.
        """
        self._fields[label] = _GFFField(GFFFieldType.Struct, value)
        return value

    def set_list(self, label: str, value: GFFList) -> GFFList:
        """
        Sets the value and field type of the field with the specified label.

        Args:
            label: The field label.
            value: The new field value.

        Returns:
            The value that was passed to the method.
        """
        self._fields[label] = _GFFField(GFFFieldType.List, value)
        return value

    def get_uint8(self, label: str) -> int:
        """
        Returns the value of the field with the specified label.

        Args:
            label: The field label.

        Raises:
            TypeError: If the field type is not set to UInt8.

        Returns:
            The field value.
        """
        if self._fields[label].field_type() != GFFFieldType.UInt8:
            raise TypeError("The specified field does not store a UInt8 value.")
        return self._fields[label].value()

    def get_uint16(self, label: str) -> int:
        """
        Returns the value of the field with the specified label.

        Args:
            label: The field label.

        Raises:
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is not set to UInt16.

        Returns:
            The field value.
        """
        if self._fields[label].field_type() != GFFFieldType.UInt16:
            raise TypeError("The specified field does not store a UInt16 value.")
        return self._fields[label].value()

    def get_uint32(self, label: str) -> int:
        """
        Returns the value of the field with the specified label.

        Args:
            label: The field label.

        Raises:
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is not set to UInt32.

        Returns:
            The field value.
        """
        if self._fields[label].field_type() != GFFFieldType.UInt32:
            raise TypeError("The specified field does not store a UInt32 value.")
        return self._fields[label].value()

    def get_uint64(self, label: str) -> int:
        """
        Returns the value of the field with the specified label.

        Args:
            label: The field label.

        Raises:
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is not set to UInt64.

        Returns:
            The field value.
        """
        if self._fields[label].field_type() != GFFFieldType.UInt64:
            raise TypeError("The specified field does not store a UInt64 value.")
        return self._fields[label].value()

    def get_int8(self, label: str) -> int:
        """
        Returns the value of the field with the specified label.

        Args:
            label: The field label.

        Raises:
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is not set to Int8.

        Returns:
            The field value.
        """
        if self._fields[label].field_type() != GFFFieldType.Int8:
            raise TypeError("The specified field does not store a Int8 value.")
        return self._fields[label].value()

    def get_int16(self, label: str) -> int:
        """
        Returns the value of the field with the specified label.

        Args:
            label: The field label.

        Raises:
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is not set to Int16.

        Returns:
            The field value.
        """
        if self._fields[label].field_type() != GFFFieldType.Int16:
            raise TypeError("The specified field does not store a Int16 value.")
        return self._fields[label].value()

    def get_int32(self, label: str) -> int:
        """
        Returns the value of the field with the specified label.

        Args:
            label: The field label.

        Raises:
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is not set to Int32.

        Returns:
            The field value.
        """
        if self._fields[label].field_type() != GFFFieldType.Int32:
            raise TypeError("The specified field does not store a Int32 value.")
        return self._fields[label].value()

    def get_int64(self, label: str) -> int:
        """
        Returns the value of the field with the specified label.

        Args:
            label: The field label.

        Raises:
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is not set to Int64.

        Returns:
            The field value.
        """
        if self._fields[label].field_type() != GFFFieldType.Int64:
            raise TypeError("The specified field does not store a Int64 value.")
        return self._fields[label].value()

    def get_single(self, label: str) -> float:
        """
        Returns the value of the field with the specified label.

        Args:
            label: The field label.

        Raises:
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is not set to Single.

        Returns:
            The field value.
        """
        if self._fields[label].field_type() != GFFFieldType.Single:
            raise TypeError("The specified field does not store a Single value.")
        return self._fields[label].value()

    def get_double(self, label: str) -> float:
        """
        Returns the value of the field with the specified label.

        Args:
            label: The field label.

        Raises:
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is not set to Double.

        Returns:
            The field value.
        """
        if self._fields[label].field_type() != GFFFieldType.Double:
            raise TypeError("The specified field does not store a Double value.")
        return self._fields[label].value()

    def get_resref(self, label: str) -> ResRef:
        """
        Returns a copy of the value from the field with the specified label.

        Args:
            label: The field label.

        Raises:
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is not set to ResRef.

        Returns:
            A copy of the field value.
        """
        if self._fields[label].field_type() != GFFFieldType.ResRef:
            raise TypeError("The specified field does not store a ResRef value.")
        return deepcopy(self._fields[label].value())

    def get_string(self, label: str) -> str:
        """
        Returns the value of the field with the specified label.

        Args:
            label: The field label.

        Raises:
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is not set to String.

        Returns:
            The field value.
        """
        if self._fields[label].field_type() != GFFFieldType.String:
            raise TypeError("The specified field does not store a String value.")
        return self._fields[label].value()

    def get_locstring(self, label: str) -> LocalizedString:
        """
        Returns a copy of the value from the field with the specified label.

        Args:
            label: The field label.

        Raises:
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is not set to LocalizedString.

        Returns:
            A copy of the field value.
        """
        if self._fields[label].field_type() != GFFFieldType.LocalizedString:
            raise TypeError("The specified field does not store a LocalizedString value.")
        return self._fields[label].value()

    def get_vector3(self, label: str) -> Vector3:
        """
        Returns a copy of the value from the field with the specified label.

        Args:
            label: The field label.

        Raises:
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is not set to Vector3.

        Returns:
            A copy of the field value.
        """
        if self._fields[label].field_type() != GFFFieldType.Vector3:
            raise TypeError("The specified field does not store a Vector3 value.")
        return copy(self._fields[label].value())

    def get_vector4(self, label: str) -> Vector4:
        """
        Returns a copy of the value from the field with the specified label.

        Args:
            label: The field label.

        Raises:
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is not set to Vector4.

        Returns:
            A copy of the field value.
        """
        if self._fields[label].field_type() != GFFFieldType.Vector4:
            raise TypeError("The specified field does not store a Vector4 value.")
        return copy(self._fields[label].value())

    def get_binary(self, label: str) -> bytes:
        """
        Returns the value of the field with the specified label.

        Args:
            label: The field label.

        Raises:
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is not set to Binary.

        Returns:
            The field value.
        """
        if self._fields[label].field_type() != GFFFieldType.Binary:
            raise TypeError("The specified field does not store a Binary value.")
        return self._fields[label].value()

    def get_struct(self, label: str) -> GFFStruct:
        """
        Returns a copy of the value from the field with the specified label.

        Args:
            label: The field label.

        Raises:
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is not set to Struct.

        Returns:
            A copy of the field value.
        """
        if self._fields[label].field_type() != GFFFieldType.Struct:
            raise TypeError("The specified field does not store a Struct value.")
        return copy(self._fields[label].value())

    def get_list(self, label: str) -> GFFList:
        """
        Returns a copy of the value from the field with the specified label.

        Args:
            label: The field label.

        Raises:
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is not set to List.

        Returns:
            A copy of the field value.
        """
        if self._fields[label].field_type() != GFFFieldType.List:
            raise TypeError("The specified field does not store a List value.")
        return copy(self._fields[label].value())


class GFFList:
    """
    A collection of GFFStructs.
    """

    def __init__(self):
        self._structs: List[GFFStruct] = []

    def __len__(self):
        """
        Returns the number of elements in _structs.
        """
        return len(self._structs)

    def __iter__(self):
        """
        Iterates through _structs yielding each element.
        """
        for struct in self._structs:
            yield struct

    def __getitem__(self, item):
        """
        Returns the struct at the specified index.
        """
        if not isinstance(item, int):
            return NotImplemented
        return self._structs[item]

    def add(self, struct_id: int) -> GFFStruct:
        """
        Adds a new struct into the list.

        Args:
            struct_id: The StructID of the new struct.
        """
        gff_list = GFFStruct(struct_id)
        self._structs.append(gff_list)
        return gff_list

    def at(self, index: int) -> Optional[GFFStruct]:
        """
        Returns the struct at the index if it exists, otherwise returns None.

        Args:
            index: The index of the desired struct.

        Returns:
            The corresponding GFFList or None.
        """
        return self._structs[index] if index < len(self._structs) else None

    def remove(self, index: int) -> None:
        """
        Removes the struct at the specified index.

        Args:
            index: The index of the desired struct.
        """
        self._structs.pop(index)
