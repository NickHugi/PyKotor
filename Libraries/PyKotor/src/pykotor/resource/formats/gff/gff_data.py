from __future__ import annotations

import difflib
import math

from copy import copy, deepcopy
from enum import Enum, IntEnum
from pathlib import PureWindowsPath
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar

from loggerplus import RobustLogger

from pykotor.common.geometry import Vector3, Vector4
from pykotor.common.language import LocalizedString
from pykotor.common.misc import ResRef
from pykotor.resource.type import ResourceType
from utility.common.misc_string.util import format_text
from utility.error_handling import safe_repr

if TYPE_CHECKING:
    import os

    from collections.abc import Callable, Generator, Iterator

T = TypeVar("T")
U = TypeVar("U")


def format_diff(old_value: object, new_value: object, name: str) -> str:
    # Convert values to strings if they aren't already
    str_old_value = str(old_value).splitlines(keepends=True)
    str_new_value = str(new_value).splitlines(keepends=True)

    # Generate unified diff
    diff = difflib.unified_diff(str_old_value, str_new_value, fromfile=f"(old){name}", tofile=f"(new){name}", lineterm="")

    # Return formatted diff
    return "\n".join(diff)

class GFFContent(Enum):
    """The different resources that the GFF can represent."""

    GFF = "GFF "
    BIC = "BIC "
    BTC = "BTC "
    BTD = "BTD "  # guess
    BTE = "BTE "  # guess
    BTI = "BTI "
    BTP = "BTP "  # guess
    BTM = "BTM "  # guess
    BTT = "BTT "  # guess
    UTC = "UTC "
    UTD = "UTD "
    UTE = "UTE "
    UTI = "UTI "
    UTP = "UTP "
    UTS = "UTS "
    UTM = "UTM "
    UTT = "UTT "
    UTW = "UTW "
    ARE = "ARE "
    DLG = "DLG "
    FAC = "FAC "
    GIT = "GIT "
    GUI = "GUI "
    IFO = "IFO "
    ITP = "ITP "
    JRL = "JRL "
    PTH = "PTH "
    NFO = "NFO "  # savenfo.res
    PT  = "PT  "  # partytable.res
    GVT = "GVT "  # GLOBALVARS.res
    INV = "INV "  # inventory in SAVEGAME.res

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

    @classmethod
    def get_extensions(cls) -> set[str]:
        gff_extensions: set[str] = set()
        res_contents: set[GFFContent] = {cls.PTH, cls.NFO, cls.PT, cls.GVT, cls.INV}
        for content_enum in cls:
            if content_enum in res_contents:
                gff_extensions.add("res")
                continue
            gff_extensions.add(content_enum.value.lower().strip())
        return gff_extensions

    @classmethod
    def from_res(cls, resname: str) -> GFFContent | None:
        lower_resname = resname.lower()
        gff_content = None
        if lower_resname == "savenfo":
            gff_content = GFFContent.NFO
        elif lower_resname == "partytable":
            gff_content = GFFContent.PT
        elif lower_resname == "globalvars":
            gff_content = GFFContent.GVT
        elif lower_resname == "inventory":
            gff_content = GFFContent.INV
        return gff_content


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


class Difference:
    def __init__(self, path: PureWindowsPath | str, old_value: object, new_value: object):
        """Initializes a Difference instance representing a specific difference between two GFFStructs.

        Args:
        ----
            path (PureWindowsPath | str): The path to the value within the GFFStruct where the difference was found.
            old_value (object): The value from the original GFFStruct at the specified path.
            new_value (object): The value from the compared GFFStruct at the specified path.
        """
        self.path: PureWindowsPath = PureWindowsPath(path)
        self.old_value: object = old_value
        self.new_value: object = new_value

    def __repr__(self):
        return f"Difference(path={self.path}, old_value={self.old_value}, new_value={self.new_value})"


class GFFCompareResult:
    """A comparison result from gff.compare/GFFStruct.compare.

    Contains enough differential information between the two GFF structs that it can be used to take one gff and reconstruct the other.
    Helper methods also exist for working with the data in other code.

    Backwards-compatibility note: the original gff.compare used to return a simple boolean. True if the gffs were the same, False if not. This class
    attempts to keep backwards compatibility while ensuring we can still return a type that's more detailed and informative.
    """

    def __init__(self):
        self.differences: list[Difference] = []

    def __bool__(self):
        # Return False if the list has any contents (meaning the objects are different), True if it's empty.
        return not self.differences

    def add_difference(self, path, old_value, new_value):
        """Adds a difference to the collection of tracked differences.

        Args:
        ----
            path (str): The path to the value where the difference was found.
            old_value (Any): The original value at the specified path.
            new_value (Any): The new value at the specified path that differs from the original.
        """
        self.differences.append(Difference(path, old_value, new_value))

    def get_changed_values(self) -> tuple[Difference, ...]:
        """Returns a tuple of differences where the value has changed from the original.

        Returns:
        -------
            tuple[Difference]: A collection of differences with changed values.
        """
        return tuple(
            diff
            for diff in self.differences
            if diff.old_value is not None
            and diff.new_value is not None
            and diff.old_value != diff.new_value
        )

    def get_new_values(self) -> tuple[Difference, ...]:
        """Returns a tuple of differences where a new value is present in the compared GFFStruct.

        Returns:
        -------
            tuple[Difference]: A collection of differences with new values.
        """
        return tuple(diff for diff in self.differences if diff.old_value is None and diff.new_value is not None)

    def get_removed_values(self) -> tuple[Difference, ...]:
        """Returns a tuple of differences where a value is present in the original GFFStruct but not in the compared.

        Returns:
        -------
            tuple[Difference]: A collection of differences with removed values.
        """
        return tuple(diff for diff in self.differences if diff.old_value is not None and diff.new_value is None)


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

    def compare(
        self,
        other_gff: GFF,
        log_func: Callable = print,
        path: PureWindowsPath | None = None,
        ignore_default_changes: bool = False,
    ) -> bool:
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
        self._value: Any
        if field_type in self.INTEGER_TYPES:
            self._value: Any = int(value)
        else:
            self._value = value

    def field_type(
        self,
    ) -> GFFFieldType:
        """Returns the field type.

        Returns:
        -------
            The field's field_type.
        """
        return self._field_type

    def value(
        self,
    ) -> Any:
        """Returns the value.

        Returns:
        -------
            The field's value.
        """
        return self._value


class GFFStruct:
    """Stores a collection of GFFFields.

    Attributes:
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
        return len(self._fields)

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
            A boolean result of whether the field exists or not.
        """
        return label in self._fields

    def compare(
        self,
        other_gff_struct: GFFStruct,
        log_func: Callable = print,
        current_path: PureWindowsPath | os.PathLike | str | None = None,
        ignore_default_changes: bool = False,
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

        def is_ignorable_value(v: Any) -> bool:
            return not v or str(v) in {"0", "-1"}

        def is_ignorable_comparison(
            old_value: object,
            new_value: object,
        ) -> bool:
            return is_ignorable_value(old_value) and is_ignorable_value(new_value)

        is_same: bool = True
        current_path = PureWindowsPath(current_path or "GFFRoot")
        if len(self) != len(other_gff_struct) and not ignore_default_changes:  # sourcery skip: class-extract-method
            log_func("")
            log_func(f"GFFStruct: number of fields have changed at '{current_path}': '{len(self)}' --> '{len(other_gff_struct)}'")
            is_same = False
        if self.struct_id != other_gff_struct.struct_id:
            log_func(f"Struct ID is different at '{current_path}': '{self.struct_id}' --> '{other_gff_struct.struct_id}'")
            is_same = False

        # Create dictionaries for both old and new structures
        old_dict: dict[str, tuple[GFFFieldType, Any]] = {
            label or f"gffstruct({idx})": (ftype, value) for idx, (label, ftype, value) in enumerate(self) if label not in ignore_labels
        }
        new_dict: dict[str, tuple[GFFFieldType, Any]] = {
            label or f"gffstruct({idx})": (ftype, value) for idx, (label, ftype, value) in enumerate(other_gff_struct) if label not in ignore_labels
        }

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
                log_func(f"Extra '{new_ftype.name}' field found at '{child_path}': {format_text(safe_repr(new_value))}")
                is_same = False
                continue
            if new_value is None or new_ftype is None:
                log_func(f"Missing '{old_ftype.name}' field at '{child_path}': {format_text(safe_repr(old_value))}")
                is_same = False
                continue

            # Check if field types have changed
            if old_ftype != new_ftype:
                log_func(f"Field type is different at '{child_path}': '{old_ftype.name}'-->'{new_ftype.name}'")
                is_same = False
                continue

            # Compare values depending on their types
            if old_ftype == GFFFieldType.Struct:
                assert isinstance(new_value, GFFStruct), f"{type(new_value).__name__}: {new_value}"
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
                    log_func(
                        f"Field '{old_ftype.name}' is different at '{child_path}': String representations match, but have other properties that don't (such as a lang id difference)."
                    )
                    continue
                log_func(f"Field '{old_ftype.name}' is different at '{child_path}':")
                log_func(format_diff(old_value, new_value, label))

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
        assert isinstance(default, object), f"{type(default).__name__}: {default}"
        value: T = default
        if object_type is None:
            object_type = default.__class__
        if (
            self.exists(label)
            and object_type is not None
#           and isinstance(self[label], object_type)  # TODO: uncomment this and assert type after fixing all the call typings
        ):
            value = self[label]
        if object_type is bool and value.__class__ is int:
            value = bool(value)
        return value

    def value(
        self,
        label: str,
    ) -> Any:
        return self._fields[label].value()

    def add_missing(self, other: GFFStruct):
        """Updates this GFFStruct with any missing fields from the other GFFStruct, deepcopying their values.

        Args:
        ----
            other: The GFFStruct from which missing fields will be sourced.
        """
        self._add_missing(self, other)

    @staticmethod
    def _add_missing(target: GFFStruct, source: GFFStruct, relpath: PureWindowsPath | None = None):
        """Static method to update target with missing fields from source, handling nested structures.

        Args:
        ----
            target: The GFFStruct to which fields will be added if they are missing.
            source: The GFFStruct from which missing fields will be sourced.
        """
        relpath = PureWindowsPath(".") if relpath is None else relpath
        for label, field_type, value in source:
            if target.exists(label):
                if field_type == GFFFieldType.Struct:
                    assert isinstance(value, GFFStruct)
                    value._add_missing(value, source.get_struct(label), relpath.joinpath(label))
                elif field_type == GFFFieldType.List:
                    assert isinstance(value, GFFList)
                    target_list = target.get_list(label)
                    for i, (target_item, source_item) in enumerate(zip(target_list, value)):
                        target_item._add_missing(target_item, source_item, relpath.joinpath(label, str(i)))
            else:
                RobustLogger().debug(f"Adding {field_type!r} '{relpath.joinpath(label)}' to target.")
                if field_type == GFFFieldType.UInt8:
                    target.set_uint8(label, deepcopy(value))
                elif field_type == GFFFieldType.UInt16:
                    target.set_uint16(label, deepcopy(value))
                elif field_type == GFFFieldType.UInt32:
                    target.set_uint32(label, deepcopy(value))
                elif field_type == GFFFieldType.UInt64:
                    target.set_uint64(label, deepcopy(value))
                elif field_type == GFFFieldType.Int8:
                    target.set_int8(label, deepcopy(value))
                elif field_type == GFFFieldType.Int16:
                    target.set_int16(label, deepcopy(value))
                elif field_type == GFFFieldType.Int32:
                    target.set_int32(label, deepcopy(value))
                elif field_type == GFFFieldType.Int64:
                    target.set_int64(label, deepcopy(value))
                elif field_type == GFFFieldType.Single:
                    target.set_single(label, deepcopy(value))
                elif field_type == GFFFieldType.Double:
                    target.set_double(label, deepcopy(value))
                elif field_type == GFFFieldType.ResRef:
                    target.set_resref(label, deepcopy(value))
                elif field_type == GFFFieldType.String:
                    target.set_string(label, deepcopy(value))
                elif field_type == GFFFieldType.LocalizedString:
                    target.set_locstring(label, deepcopy(value))
                elif field_type == GFFFieldType.Binary:
                    target.set_binary(label, deepcopy(value))
                elif field_type == GFFFieldType.Vector3:
                    target.set_vector3(label, deepcopy(value))
                elif field_type == GFFFieldType.Vector4:
                    target.set_vector4(label, deepcopy(value))
                elif field_type == GFFFieldType.Struct:
                    target.set_struct(label, deepcopy(value))
                elif field_type == GFFFieldType.List:
                    target.set_list(label, deepcopy(value))

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
        value: ResRef,
    ):
        """Sets the value and field type of the field with the specified label.

        Args:
        ----
            label: The field label.
            value: The new field value.
        """
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
        log_func: Callable[..., Any] = print,
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
