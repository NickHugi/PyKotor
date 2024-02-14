from __future__ import annotations

import math
import os
from abc import abstractmethod
from copy import copy, deepcopy
from enum import Enum, IntEnum
from itertools import chain
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Iterable, TypeVar

from pykotor.common.geometry import Vector3, Vector4
from pykotor.common.language import LocalizedString
from pykotor.common.misc import ResRef
from pykotor.resource.type import ResourceType
from utility.string import compare_and_format, format_text
from utility.system.path import PureWindowsPath

if TYPE_CHECKING:
    from collections.abc import Generator, Iterator

T = TypeVar("T")
U = TypeVar("U")


class GFFContent(Enum):
    """The different resources that the GFF can represent."""

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
    NFO = "NFO "  # savenfo.res
    PT  = "PT  "  # partytable.res
    GVT = "GVT "  # GLOBALVARS.res

    @classmethod
    def has_value(
        cls,
        value,
    ):
        if isinstance(value, GFFContent):
            value = value.value
        elif not isinstance(value, str):
            raise NotImplementedError(value)
        return any(gff_content.value == value.upper() for gff_content in cls)

    @classmethod
    def get_valid_types(cls) -> set[str]:
        return {x.name for x in cls}


class GFFFieldType(IntEnum):
    """The different types of fields based off what kind of data it stores."""

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

    def return_type(
        self,
    ) -> type[int | str | ResRef | Vector3 | Vector4 | LocalizedString | GFFStruct | GFFList | bytes | float]:
        if self in {
            GFFFieldType.UInt8,
            GFFFieldType.UInt16,
            GFFFieldType.UInt32,
            GFFFieldType.UInt64,
            GFFFieldType.Int8,
            GFFFieldType.Int16,
            GFFFieldType.Int32,
            GFFFieldType.Int64,
        }:
            return int
        if self == GFFFieldType.String:
            return str
        if self == GFFFieldType.ResRef:
            return ResRef
        if self == GFFFieldType.Vector3:
            return Vector3
        if self == GFFFieldType.Vector4:
            return Vector4
        if self == GFFFieldType.LocalizedString:
            return LocalizedString
        if self == GFFFieldType.Struct:
            return GFFStruct
        if self == GFFFieldType.List:
            return GFFList
        if self == GFFFieldType.Binary:
            return bytes
        if self in {GFFFieldType.Double, GFFFieldType.Single}:
            return float
        raise ValueError(self)


class GFF:
    """Represents the data of a GFF file."""

    BINARY_TYPE: ResourceType = ResourceType.GFF

    def __init__(
        self,
        content: GFFContent = GFFContent.GFF,
    ):
        self.content: GFFContent = content
        self.root: GFFStruct = GFFStruct(-1)

    def print_tree(
        self,
        root: GFFStruct | None = None,
        indent: int = 0,
        column_len: int = 40,
    ):
        if root is None:
            root = self.root

        for label, field_type, value in root:
            length_or_id: int = -2
            gff_struct: GFFStruct = value
            gff_list: GFFList = value
            if field_type is GFFFieldType.Struct:
                length_or_id = gff_struct.struct_id
            if field_type is GFFFieldType.List:
                length_or_id = len(gff_list)

            print(("  " * indent + label).ljust(column_len), " ", length_or_id)

            if field_type is GFFFieldType.Struct:
                self.print_tree(value, indent + 1)
            if field_type is GFFFieldType.List:
                for i, gff_struct in enumerate(value):
                    print(
                        f'  {"  " * indent}[Struct {i}]'.ljust(column_len),
                        " ",
                        gff_struct.struct_id,
                    )
                    self.print_tree(gff_struct, indent + 2)

    def compare(self, other_gff: GFF, log_func: Callable = print, path: PureWindowsPath | None = None, ignore_default_changes: bool = False) -> bool:
        """Compare two GFF objects.

        Args:
        ----
            self: The GFF object to compare from
            other_gff: The GFF object to compare to
            log_func: Function used to log comparison messages (default print)
            path: Optional path to write comparison report to

        Returns:
        -------
            bool: True if GFFs are identical, False otherwise

        Processing Logic:
        ----------------
            - Compare root nodes of both GFFs
            - Recursively compare child nodes
            - Log any differences found
            - Write comparison report to given path if provided
            - Return True if no differences found, False otherwise.
        """
        return self.root.compare(other_gff.root, log_func, path, ignore_default_changes)



class _GFFField:
    """Read-only data structure for items stored in GFFStruct."""

    INTEGER_TYPES: ClassVar[set[GFFFieldType]] = {
        GFFFieldType.Int8,
        GFFFieldType.UInt8,
        GFFFieldType.Int16,
        GFFFieldType.UInt16,
        GFFFieldType.Int32,
        GFFFieldType.UInt32,
        GFFFieldType.Int64,
        GFFFieldType.UInt64,
    }
    STRING_TYPES: ClassVar[set[GFFFieldType]] = {
        GFFFieldType.String,
        GFFFieldType.ResRef,
    }
    FLOAT_TYPES: ClassVar[set[GFFFieldType]] = {
        GFFFieldType.Single,
        GFFFieldType.Double,
    }

    def __init__(
        self,
        field_type: GFFFieldType,
        value: Any,
    ):
        self._field_type: GFFFieldType = field_type
        self._value: Any = value

    def field_type(
        self,
    ) -> GFFFieldType:
        """Returns the field type.

        Returns
        -------
            The field's field_type.
        """
        return self._field_type

    def value(
        self,
    ) -> Any:
        """Returns the value.

        Returns
        -------
            The field's value.
        """
        return self._value

class GFFStruct:
    """Stores a collection of GFFFields.

    Attributes
    ----------
        struct_id: User defined id.
    """

    def __init__(
        self,
        struct_id: int = 0,
    ):
        self.struct_id: int = struct_id
        self._fields: dict[str, _GFFField] = {}

    def __len__(
        self,
    ) -> int:
        """Returns the number of fields."""
        return len(self._fields.values())

    def __iter__(
        self,
    ) -> Generator[tuple[str, GFFFieldType, Any], Any, None]:
        """Iterates through the stored fields yielding each field's (label, type, value)."""
        for label, field in self._fields.items():
            yield label, field.field_type(), field.value()

    def __getitem__(
        self,
        item: str,
    ) -> Any:
        """Returns the value of the specified field."""
        return self._fields[item].value() if isinstance(item, str) else NotImplemented

    def remove(
        self,
        label: str,
    ):
        """Removes the field with the specified label.

        Args:
        ----
            label: The field label.
        """
        if label in self._fields:
            self._fields.pop(label)

    def exists(
        self,
        label: str,
    ) -> bool:
        """Returns the type of the field with the specified label.

        Args:
        ----
            label: The field label.

        Returns:
        -------
            A GFFFieldType value.
        """
        return label in self._fields

    def compare(
        self,
        other_gff_struct: GFFStruct,
        log_func: Callable = print,
        current_path: PureWindowsPath | os.PathLike | str | None = None,
        ignore_default_changes=False,
    ) -> bool:
        """Recursively compares two GFFStructs.

        Functionally the same as __eq__, but will log/print comparison information as well

        Args:
        ----
            other_gff_struct: {GFFStruct}: GFFStruct to compare against
            log_func: {Callable}: Function to log differences. Defaults to print.
            current_path: {PureWindowsPath | os.PathLike | str | None}: Path of structure being compared

        Returns:
        -------
            bool: True if structures are the same, False otherwise

        Processing Logic:
        ----------------
            - Creates dictionaries of fields for each structure
            - Gets union of all field labels
            - Compares field types, values recursively for structs and lists
            - Logs any differences found
        """
        ignore_labels = {
            "KTInfoDate",
            "KTGameVerIndex",
            "KTInfoVersion",
            "EditorInfo",
        }
        def is_ignorable_value(v) -> bool:
            return not v or str(v) in {"0", "-1"}

        def is_ignorable_comparison(
            old_value,
            new_value,
        ) -> bool:
            return is_ignorable_value(old_value) and is_ignorable_value(new_value)

        is_same: bool = True
        current_path = PureWindowsPath(current_path or "GFFRoot")
        if len(self) != len(other_gff_struct) and not ignore_default_changes:  # sourcery skip: class-extract-method
            log_func()
            log_func(f"GFFStruct: number of fields have changed at '{current_path}': '{len(self)}' --> '{len(other_gff_struct)}'")
            is_same = False
        if self.struct_id != other_gff_struct.struct_id:
            log_func(f"Struct ID is different at '{current_path}': '{self.struct_id}' --> '{other_gff_struct.struct_id}'")
            is_same = False

        # Create dictionaries for both old and new structures
        old_dict: dict[str, tuple[GFFFieldType, Any]] = {label or f"gffstruct({idx})": (ftype, value) for idx, (label, ftype, value) in enumerate(self) if label not in ignore_labels}
        new_dict: dict[str, tuple[GFFFieldType, Any]] = {label or f"gffstruct({idx})": (ftype, value) for idx, (label, ftype, value) in enumerate(other_gff_struct) if label not in ignore_labels}

        # Union of labels from both old and new structures
        all_labels: set[str] = set(old_dict.keys()) | set(new_dict.keys())

        for label in all_labels:
            child_path: PureWindowsPath = current_path / str(label)
            old_ftype, old_value = old_dict.get(label, (None, None))
            new_ftype, new_value = new_dict.get(label, (None, None))

            if ignore_default_changes and is_ignorable_comparison(old_value, new_value):
                continue

            # Check for missing fields/values in either structure
            if old_ftype is None or old_value is None:
                if new_ftype is None:
                    msg = f"new_ftype shouldn't be None here. Relevance: old_ftype={old_ftype!r}, old_value={old_value!r}, new_value={new_value!r}"
                    raise RuntimeError(msg)
                log_func(f"Extra '{new_ftype.name}' field found at '{child_path}': {format_text(new_value)}" )
                is_same = False
                continue
            if new_value is None or new_ftype is None:
                log_func(f"Missing '{old_ftype.name}' field at '{child_path}': {format_text(old_value)}")
                is_same = False
                continue

            # Check if field types have changed
            if old_ftype != new_ftype:
                log_func(f"Field type is different at '{child_path}': '{old_ftype.name}'-->'{new_ftype.name}'")
                is_same = False
                continue

            # Compare values depending on their types
            if old_ftype == GFFFieldType.Struct:
                assert isinstance(new_value, GFFStruct)
                cur_struct_this: GFFStruct = old_value
                if cur_struct_this.struct_id != new_value.struct_id:
                    log_func(f"Struct ID is different at '{child_path}': '{cur_struct_this.struct_id}'-->'{new_value.struct_id}'")
                    is_same = False

                if not cur_struct_this.compare(new_value, log_func, child_path, ignore_default_changes):
                    is_same = False
                    continue
            elif old_ftype == GFFFieldType.List:
                gff_list: GFFList = old_value
                if not gff_list.compare(new_value, log_func, child_path, ignore_default_changes=ignore_default_changes):
                    is_same = False
                    continue

            elif old_value != new_value:
                if (
                    isinstance(old_value, float)
                    and isinstance(new_value, float)
                    and math.isclose(old_value, new_value, rel_tol=1e-4, abs_tol=1e-4)
                ):
                    continue

                is_same = False
                if str(old_value) == str(new_value):
                    log_func(f"Field '{old_ftype.name}' is different at '{child_path}': String representations match, but have other properties that don't (such as a lang id difference).")
                    continue

                formatted_old_value, formatted_new_value = map(str, (old_value, new_value))
                newlines_in_old: int = formatted_old_value.count("\n")
                newlines_in_new: int = formatted_new_value.count("\n")

                if newlines_in_old > 1 or newlines_in_new > 1:
                    formatted_old_value, formatted_new_value = compare_and_format(formatted_old_value, formatted_new_value)
                    log_func(f"Field '{old_ftype.name}' is different at '{child_path}': {format_text(formatted_old_value)}<-vvv->{format_text(formatted_new_value)}")
                    continue

                if newlines_in_old == 1 or newlines_in_new == 1:
                    log_func(f"Field '{old_ftype.name}' is different at '{child_path}': {os.linesep}{formatted_old_value}{os.linesep}<-vvv->{os.linesep}{formatted_new_value}")
                    continue

                log_func(f"Field '{old_ftype.name}' is different at '{child_path}': {formatted_old_value} --> {formatted_new_value}")

        return is_same

    def what_type(
        self,
        label: str,
    ) -> GFFFieldType:
        return self._fields[label].field_type()

    def acquire(
        self,
        label: str,
        default: T,
        object_type: type[U | T] | tuple[type[U], ...] | None = None,
    ) -> T | U:
        """Gets the value from the specified field.

        Args:
        ----
            label: The field label.
            default: Default value to return if value does not match object_type.
            object_type: The type of the field value. If not specified it will match the default's type.

        Returns:
        -------
            The field value. If the field does not exist or the value type does not match the specified type then the default is returned instead.
        """
        value: T = default
        if object_type is None:
            object_type = type(default)
        if (
            self.exists(label)
            and object_type is not None
#           and isinstance(self[label], object_type)  # TODO: uncomment this and assert type after fixing all the call typings
        ):
            value = self[label]
        return value

    def value(
        self,
        label: str,
    ) -> Any:
        return self._fields[label].value()

    def set_uint8(
        self,
        label: str,
        value: int,
    ):
        """Sets the value and field type of the field with the specified label.

        Args:
        ----
            label: The field label.
            value: The new field value.
        """
        self._fields[label] = _GFFField(GFFFieldType.UInt8, value)

    def set_uint16(
        self,
        label: str,
        value: int,
    ):
        """Sets the value and field type of the field with the specified label.

        Args:
        ----
            label: The field label.
            value: The new field value.
        """
        self._fields[label] = _GFFField(GFFFieldType.UInt16, value)

    def set_uint32(
        self,
        label: str,
        value: int,
    ):
        """Sets the value and field type of the field with the specified label.

        Args:
        ----
            label: The field label.
            value: The new field value.
        """
        self._fields[label] = _GFFField(GFFFieldType.UInt32, value)

    def set_uint64(
        self,
        label: str,
        value: int,
    ):
        """Sets the value and field type of the field with the specified label.

        Args:
        ----
            label: The field label.
            value: The new field value.
        """
        self._fields[label] = _GFFField(GFFFieldType.UInt64, value)

    def set_int8(
        self,
        label: str,
        value: int,
    ):
        """Sets the value and field type of the field with the specified label.

        Args:
        ----
            label: The field label.
            value: The new field value.
        """
        self._fields[label] = _GFFField(GFFFieldType.Int8, value)

    def set_int16(
        self,
        label: str,
        value: int,
    ):
        """Sets the value and field type of the field with the specified label.

        Args:
        ----
            label: The field label.
            value: The new field value.
        """
        self._fields[label] = _GFFField(GFFFieldType.Int16, value)

    def set_int32(
        self,
        label: str,
        value: int,
    ):
        """Sets the value and field type of the field with the specified label.

        Args:
        ----
            label: The field label.
            value: The new field value.
        """
        self._fields[label] = _GFFField(GFFFieldType.Int32, value)

    def set_int64(
        self,
        label: str,
        value: int,
    ):
        """Sets the value and field type of the field with the specified label.

        Args:
        ----
            label: The field label.
            value: The new field value.
        """
        self._fields[label] = _GFFField(GFFFieldType.Int64, value)

    def set_single(
        self,
        label: str,
        value: float,
    ):
        """Sets the value and field type of the field with the specified label.

        Args:
        ----
            label: The field label.
            value: The new field value.
        """
        self._fields[label] = _GFFField(GFFFieldType.Single, value)

    def set_double(
        self,
        label: str,
        value: float,
    ):
        """Sets the value and field type of the field with the specified label.

        Args:
        ----
            label: The field label.
            value: The new field value.
        """
        self._fields[label] = _GFFField(GFFFieldType.Double, value)

    def set_resref(
        self,
        label: str,
        value: str | ResRef,
    ) -> None:
        """Sets the value and field type of the field with the specified label.

        Args:
        ----
            label: The field label.
            value: The new field value.
        """
        if isinstance(value, str):
            value = ResRef(value)
        self._fields[label] = _GFFField(GFFFieldType.ResRef, value)

    def set_string(
        self,
        label: str,
        value: str,
    ):
        """Sets the value and field type of the field with the specified label.

        Args:
        ----
            label: The field label.
            value: The new field value.
        """
        self._fields[label] = _GFFField(GFFFieldType.String, value)

    def set_locstring(
        self,
        label: str,
        value: LocalizedString,
    ):
        """Sets the value and field type of the field with the specified label.

        Args:
        ----
            label: The field label.
            value: The new field value.
        """
        self._fields[label] = _GFFField(GFFFieldType.LocalizedString, value)

    def set_binary(
        self,
        label: str,
        value: bytes,
    ):
        """Sets the value and field type of the field with the specified label.

        Args:
        ----
            label: The field label.
            value: The new field value.
        """
        self._fields[label] = _GFFField(GFFFieldType.Binary, value)

    def set_vector3(
        self,
        label: str,
        value: Vector3,
    ):
        """Sets the value and field type of the field with the specified label.

        Args:
        ----
            label: The field label.
            value: The new field value.
        """
        self._fields[label] = _GFFField(GFFFieldType.Vector3, value)

    def set_vector4(
        self,
        label: str,
        value: Vector4,
    ):
        """Sets the value and field type of the field with the specified label.

        Args:
        ----
            label: The field label.
            value: The new field value.
        """
        self._fields[label] = _GFFField(GFFFieldType.Vector4, value)

    def set_struct(
        self,
        label: str,
        value: GFFStruct,
    ) -> GFFStruct:
        """Sets the value and field type of the field with the specified label.

        Args:
        ----
            label: The field label.
            value: The new field value.

        Returns:
        -------
            The value that was passed to the method.
        """
        self._fields[label] = _GFFField(GFFFieldType.Struct, value)
        return value

    def set_list(
        self,
        label: str,
        value: GFFList,
    ) -> GFFList:
        """Sets the value and field type of the field with the specified label.

        Args:
        ----
            label: The field label.
            value: The new field value.

        Returns:
        -------
            The value that was passed to the method.
        """
        self._fields[label] = _GFFField(GFFFieldType.List, value)
        return value

    def get_uint8(
        self,
        label: str,
    ) -> int:
        """Returns the value of the field with the specified label.

        Args:
        ----
            label: The field label.

        Raises:
        ------
            TypeError: If the field type is not set to UInt8.

        Returns:
        -------
            The field value.
        """
        if self._fields[label].field_type() != GFFFieldType.UInt8:
            msg = "The specified field does not store a UInt8 value."
            raise TypeError(msg)
        return self._fields[label].value()

    def get_uint16(
        self,
        label: str,
    ) -> int:
        """Returns the value of the field with the specified label.

        Args:
        ----
            label: The field label.

        Raises:
        ------
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is not set to UInt16.

        Returns:
        -------
            The field value.
        """
        if self._fields[label].field_type() != GFFFieldType.UInt16:
            msg = "The specified field does not store a UInt16 value."
            raise TypeError(msg)
        return self._fields[label].value()

    def get_uint32(
        self,
        label: str,
    ) -> int:
        """Returns the value of the field with the specified label.

        Args:
        ----
            label: The field label.

        Raises:
        ------
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is not set to UInt32.

        Returns:
        -------
            The field value.
        """
        if self._fields[label].field_type() != GFFFieldType.UInt32:
            msg = "The specified field does not store a UInt32 value."
            raise TypeError(msg)
        return self._fields[label].value()

    def get_uint64(
        self,
        label: str,
    ) -> int:
        """Returns the value of the field with the specified label.

        Args:
        ----
            label: The field label.

        Raises:
        ------
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is not set to UInt64.

        Returns:
        -------
            The field value.
        """
        if self._fields[label].field_type() != GFFFieldType.UInt64:
            msg = "The specified field does not store a UInt64 value."
            raise TypeError(msg)
        return self._fields[label].value()

    def get_int8(
        self,
        label: str,
    ) -> int:
        """Returns the value of the field with the specified label.

        Args:
        ----
            label: The field label.

        Raises:
        ------
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is not set to Int8.

        Returns:
        -------
            The field value.
        """
        if self._fields[label].field_type() != GFFFieldType.Int8:
            msg = "The specified field does not store a Int8 value."
            raise TypeError(msg)
        return self._fields[label].value()

    def get_int16(
        self,
        label: str,
    ) -> int:
        """Returns the value of the field with the specified label.

        Args:
        ----
            label: The field label.

        Raises:
        ------
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is not set to Int16.

        Returns:
        -------
            The field value.
        """
        if self._fields[label].field_type() != GFFFieldType.Int16:
            msg = "The specified field does not store a Int16 value."
            raise TypeError(msg)
        return self._fields[label].value()

    def get_int32(
        self,
        label: str,
    ) -> int:
        """Returns the value of the field with the specified label.

        Args:
        ----
            label: The field label.

        Raises:
        ------
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is not set to Int32.

        Returns:
        -------
            The field value.
        """
        if self._fields[label].field_type() != GFFFieldType.Int32:
            msg = "The specified field does not store a Int32 value."
            raise TypeError(msg)
        return self._fields[label].value()

    def get_int64(
        self,
        label: str,
    ) -> int:
        """Returns the value of the field with the specified label.

        Args:
        ----
            label: The field label.

        Raises:
        ------
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is not set to Int64.

        Returns:
        -------
            The field value.
        """
        if self._fields[label].field_type() != GFFFieldType.Int64:
            msg = "The specified field does not store a Int64 value."
            raise TypeError(msg)
        return self._fields[label].value()

    def get_single(
        self,
        label: str,
    ) -> float:
        """Returns the value of the field with the specified label.

        Args:
        ----
            label: The field label.

        Raises:
        ------
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is not set to Single.

        Returns:
        -------
            The field value.
        """
        if self._fields[label].field_type() != GFFFieldType.Single:
            msg = "The specified field does not store a Single value."
            raise TypeError(msg)
        return self._fields[label].value()

    def get_double(
        self,
        label: str,
    ) -> float:
        """Returns the value of the field with the specified label.

        Args:
        ----
            label: The field label.

        Raises:
        ------
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is not set to Double.

        Returns:
        -------
            The field value.
        """
        if self._fields[label].field_type() != GFFFieldType.Double:
            msg = "The specified field does not store a Double value."
            raise TypeError(msg)
        return self._fields[label].value()

    def get_resref(
        self,
        label: str,
    ) -> ResRef:
        """Returns a copy of the value from the field with the specified label.

        Args:
        ----
            label: The field label.

        Raises:
        ------
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is not set to ResRef.

        Returns:
        -------
            A copy of the field value.
        """
        if self._fields[label].field_type() != GFFFieldType.ResRef:
            msg = "The specified field does not store a ResRef value."
            raise TypeError(msg)
        return deepcopy(self._fields[label].value())

    def get_string(
        self,
        label: str,
    ) -> str:
        """Returns the value of the field with the specified label.

        Args:
        ----
            label: The field label.

        Raises:
        ------
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is not set to String.

        Returns:
        -------
            The field value.
        """
        if self._fields[label].field_type() != GFFFieldType.String:
            msg = "The specified field does not store a String value."
            raise TypeError(msg)
        return self._fields[label].value()

    def get_locstring(
        self,
        label: str,
    ) -> LocalizedString:
        """Returns a copy of the value from the field with the specified label.

        Args:
        ----
            label: The field label.

        Raises:
        ------
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is not set to LocalizedString.

        Returns:
        -------
            A copy of the field value.
        """
        if self._fields[label].field_type() != GFFFieldType.LocalizedString:
            msg = "The specified field does not store a LocalizedString value."
            raise TypeError(msg)
        return self._fields[label].value()

    def get_vector3(
        self,
        label: str,
    ) -> Vector3:
        """Returns a copy of the value from the field with the specified label.

        Args:
        ----
            label: The field label.

        Raises:
        ------
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is not set to Vector3.

        Returns:
        -------
            A copy of the field value.
        """
        if self._fields[label].field_type() != GFFFieldType.Vector3:
            msg = "The specified field does not store a Vector3 value."
            raise TypeError(msg)
        return copy(self._fields[label].value())

    def get_vector4(
        self,
        label: str,
    ) -> Vector4:
        """Returns a copy of the value from the field with the specified label.

        Args:
        ----
            label: The field label.

        Raises:
        ------
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is not set to Vector4.

        Returns:
        -------
            A copy of the field value.
        """
        if self._fields[label].field_type() != GFFFieldType.Vector4:
            msg = "The specified field does not store a Vector4 value."
            raise TypeError(msg)
        return copy(self._fields[label].value())

    def get_binary(
        self,
        label: str,
    ) -> bytes:
        """Returns the value of the field with the specified label.

        Args:
        ----
            label: The field label.

        Raises:
        ------
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is not set to Binary.

        Returns:
        -------
            The field value.
        """
        if self._fields[label].field_type() != GFFFieldType.Binary:
            msg = "The specified field does not store a Binary value."
            raise TypeError(msg)
        return self._fields[label].value()

    def get_struct(
        self,
        label: str,
    ) -> GFFStruct:
        """Returns a copy of the value from the field with the specified label.

        Args:
        ----
            label: The field label.

        Raises:
        ------
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is not set to Struct.

        Returns:
        -------
            A copy of the field value.
        """
        if self._fields[label].field_type() != GFFFieldType.Struct:
            msg = "The specified field does not store a Struct value."
            raise TypeError(msg)
        return copy(self._fields[label].value())

    def get_list(
        self,
        label: str,
    ) -> GFFList:
        """Returns a copy of the value from the field with the specified label.

        Args:
        ----
            label: The field label.

        Raises:
        ------
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is not set to List.

        Returns:
        -------
            A copy of the field value.
        """
        if self._fields[label].field_type() != GFFFieldType.List:
            msg = "The specified field does not store a List value."
            raise TypeError(msg)
        return copy(self._fields[label].value())

class GFFStructInterface(GFFStruct):

    @classmethod
    def _get_FIELDS(cls) -> dict[str, _GFFField]:
        return cls.FIELDS

    @classmethod
    def _get_K2_FIELDS(cls) -> dict[str, _GFFField]:
        return cls.K2_FIELDS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __dir__(self) -> Iterable[str]:
        return chain(
            super().__dir__(),
            (
                label for label in {**type(self)._get_FIELDS(), **type(self)._get_K2_FIELDS()}
                if self.exists(label)
            ),
        )

    @classmethod
    def from_struct(cls, struct: GFFStruct):
        new_instance = cls.__new__(cls)
        super(cls, new_instance).__init__()
        new_instance._update_from_struct(struct)
        return new_instance

    def _update_from_struct(self, struct: GFFStruct):
        all_fields: dict[str, _GFFField] = {}
        all_fields.update(self._get_FIELDS())
        all_fields.update(self._get_K2_FIELDS())
        for label, field_type, value in struct:
            self._set_field_value(field_type, label, value)

    def __getattribute__(self, attr: str):
        if attr.startswith("_") or attr == "struct_id" or attr in GFFStruct.__dict__ or attr in type(self).__dict__:
            return super().__getattribute__(attr)
        all_fields: dict[str, _GFFField] = {}
        all_fields.update(type(self)._get_FIELDS())
        all_fields.update(type(self)._get_K2_FIELDS())
        if attr not in all_fields:
            msg = f"'{self.__class__.__name__}' object has no attribute '{attr}'"
            raise AttributeError(msg)
        gff_field: _GFFField = all_fields[attr]
        return super().acquire(
            attr,
            gff_field.value(),
            gff_field.field_type().return_type(),
        )

    def __setattr__(self, attr, value) -> None:
        if attr.startswith("_") or attr == "struct_id":
            super().__setattr__(attr, value)
            return
        all_fields: dict[str, _GFFField] = {}
        all_fields.update(type(self)._get_FIELDS())
        all_fields.update(type(self)._get_K2_FIELDS())
        field_type: GFFFieldType | None
        if attr not in all_fields:
            field_type = self.what_type(attr) if self.exists(attr) else None
        else:
            field_type = all_fields[attr].field_type()
        if field_type is None:
            msg = f"'{self.__class__.__name__}' object has no attribute '{attr}'"
            raise AttributeError(msg)
        #if not field_type:
        #    msg = f"'{self.__class__.__name__}' No field type defined for {attr}"
        #    raise TypeError(msg)
        self._set_field_value(field_type, attr, value)

    def _set_field_value(self, field_type, attr, value):
        if field_type == GFFFieldType.UInt8:
            super().set_uint8(attr, value)
        elif field_type == GFFFieldType.Int8:
            super().set_int8(attr, value)
        elif field_type == GFFFieldType.UInt16:
            super().set_uint16(attr, value)
        elif field_type == GFFFieldType.Int16:
            super().set_int16(attr, value)
        elif field_type == GFFFieldType.UInt32:
            super().set_uint32(attr, value)
        elif field_type == GFFFieldType.Int32:
            super().set_int32(attr, value)
        elif field_type == GFFFieldType.UInt64:
            super().set_uint64(attr, value)
        elif field_type == GFFFieldType.Int64:
            super().set_int64(attr, value)
        elif field_type == GFFFieldType.Single:
            super().set_single(attr, value)
        elif field_type == GFFFieldType.Double:
            super().set_double(attr, value)
        elif field_type == GFFFieldType.String:
            super().set_string(attr, value)
        elif field_type == GFFFieldType.ResRef:
            super().set_resref(attr, value)
        elif field_type == GFFFieldType.LocalizedString:
            super().set_locstring(attr, value)
        elif field_type == GFFFieldType.Binary:
            super().set_binary(attr, value)
        elif field_type == GFFFieldType.Struct:
            super().set_struct(attr, value)
        elif field_type == GFFFieldType.List:
            super().set_list(attr, value)
        elif field_type == GFFFieldType.Vector4:
            super().set_vector4(attr, value)
        elif field_type == GFFFieldType.Vector3:
            super().set_vector3(attr, value)
        else:
            msg = f"Unsupported field type for {attr}"
            raise TypeError(msg)

class GFFList:
    """A collection of GFFStructs."""

    def __init__(
        self,
    ):
        self._structs: list[GFFStruct] = []

    def __len__(
        self,
    ) -> int:
        """Returns the number of elements in _structs."""
        return len(self._structs)

    def __iter__(
        self,
    ) -> Iterator[GFFStruct]:
        """Iterates through _structs yielding each element."""
        yield from self._structs

    def __getitem__(
        self,
        item: int,
    ) -> GFFStruct:
        """Returns the struct at the specified index."""
        return self._structs[item] if isinstance(item, int) else NotImplemented

    def add(
        self,
        struct_id: int,
    ) -> GFFStruct:
        """Adds a new struct into the list.

        Args:
        ----
            struct_id: The StructID of the new struct.
        """
        new_struct = GFFStruct(struct_id)
        self._structs.append(new_struct)
        return new_struct

    def at(
        self,
        index: int,
    ) -> GFFStruct | None:
        """Returns the struct at the index if it exists, otherwise returns None.

        Args:
        ----
            index: The index of the desired struct.

        Returns:
        -------
            The corresponding GFFList or None.
        """
        return self._structs[index] if index < len(self._structs) else None

    def remove(
        self,
        index: int,
    ):
        """Removes the struct at the specified index.

        Args:
        ----
            index: The index of the desired struct.
        """
        self._structs.pop(index)


    def compare(
        self,
        other_gff_list: GFFList,
        log_func=print,
        current_path: PureWindowsPath | None = None,
        *,
        ignore_default_changes: bool = False,
    ) -> bool:
        """Compare two GFFLists recursively.

        Functionally the same as __eq__, but will also log/print the differences.

        Args:
        ----
            other_gff_list: GFFList - the GFF List to compare to
            log_func: the function to use for logging. Defaults to print.
            current_path: PureWindowsPath - Path being compared

        Returns:
        -------
            is_same_result: bool - Whether the lists are the same

        Processing Logic:
        ----------------
            - Compare list lengths and log differences
            - Create dictionaries to index lists for comparison
            - Detect unique items in each list and log differences
            - Compare common items and log structural differences.
        """
        current_path = current_path or PureWindowsPath("GFFList")
        is_same_result = True

        if len(self) != len(other_gff_list):
            log_func(f"GFFList counts have changed at '{current_path}': '{len(self)}' --> '{len(other_gff_list)}'")
            log_func()
            is_same_result = False

        # Use the indices in the original lists as keys
        old_dict = dict(enumerate(self))
        new_dict = dict(enumerate(other_gff_list))

        # Detect unique items in both lists
        unique_to_old = set(old_dict.keys()) - set(new_dict.keys())
        unique_to_new = set(new_dict.keys()) - set(old_dict.keys())

        for list_index in unique_to_old:
            struct = old_dict[list_index]
            log_func(f"Missing GFFStruct at '{current_path / str(list_index)}' with struct ID '{struct.struct_id}'")
            log_func("Contents of old struct:")
            for label, field_type, field_value in struct:
                log_func(field_type.name, f"{label}: {format_text(field_value)}")
            log_func()
            is_same_result = False

        for list_index in unique_to_new:
            struct = new_dict[list_index]
            log_func(f"Extra GFFStruct at '{current_path / str(list_index)}' with struct ID '{struct.struct_id}'")
            log_func("Contents of new struct:")
            for label, field_type, field_value in struct:
                log_func(field_type.name, f"{label}: {format_text(field_value)}")
            log_func()
            is_same_result = False

        # For items present in both lists
        common_items = old_dict.keys() & new_dict.keys()
        for list_index in common_items:
            old_child: GFFStruct = old_dict[list_index]
            new_child: GFFStruct = new_dict[list_index]
            if not old_child.compare(new_child, log_func, current_path / str(list_index), ignore_default_changes):
                is_same_result = False

        return is_same_result
