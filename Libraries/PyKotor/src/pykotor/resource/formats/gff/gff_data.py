from __future__ import annotations

import difflib
import math

from copy import copy, deepcopy
from enum import Enum, IntEnum
from pathlib import PureWindowsPath  # pyright: ignore[reportMissingImports]
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar

from loggerplus import RobustLogger  # type: ignore[import-untyped]  # pyright: ignore[reportMissingTypeStubs]

from pykotor.common.geometry import Vector3, Vector4
from pykotor.common.language import LocalizedString
from pykotor.common.misc import ResRef
from pykotor.resource.formats._base import ComparableMixin
from pykotor.resource.type import ResourceType
from utility.error_handling import safe_repr  # pyright: ignore[reportMissingImports]
from utility.string_util import format_text  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    import os

    from collections.abc import Callable, Generator, Iterator

T = TypeVar("T")
U = TypeVar("U")


def format_diff(old_value: object, new_value: object, name: str) -> str:
    # Convert values to strings if they aren't already
    str_old_value = str(old_value).splitlines(keepends=True)
    str_new_value = str(new_value).splitlines(keepends=True)

    # Generate unified diff with clearer labels showing the actual values
    diff = difflib.unified_diff(
        str_old_value,
        str_new_value,
        fromfile=f"(old){name}={old_value}",
        tofile=f"(new){name}={new_value}",
        lineterm=""
    )

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
    def get_restypes(cls) -> set[ResourceType]:
        gff_restypes: set[ResourceType] = set()
        res_contents: set[GFFContent] = {cls.PTH, cls.NFO, cls.PT, cls.GVT, cls.INV}
        for content_enum in cls:
            if content_enum in res_contents:
                gff_restypes.add(ResourceType.RES)
                continue
            gff_restypes.add(ResourceType.from_extension(content_enum.value.lower().strip()).target_type())
        return gff_restypes

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

    def return_type(  # noqa: PLR0911, C901
        self,
    ) -> type[int | str | ResRef | Vector3 | Vector4 | LocalizedString | GFFStruct | GFFList | bytes | float]:  # type: ignore[valid-type]
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


class GFF(ComparableMixin):
    """Represents the data of a GFF file."""

    BINARY_TYPE: ResourceType = ResourceType.GFF
    COMPARABLE_FIELDS = ("content", "root")

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

    def compare(  # noqa: C901, PLR0911, PLR0912, PLR0913, PLR0915
        self,
        other: object,
        log_func: Callable = print,
        path: PureWindowsPath | None = None,
        ignore_default_changes: bool = False,  # noqa: FBT001, FBT002
    ) -> bool:
        """Compare two GFF objects.

        Args:
        ----
            self: The GFF object to compare from
            other: {object}: The GFF object to compare to
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
        if not isinstance(other, GFF):
            log_func(f"GFF counts have changed at '{path}': '<unknown>' --> '<unknown>'")
            log_func("")
            is_same = False
            return is_same
        if len(self.root) != len(other.root):
            log_func(f"GFF counts have changed at '{path}': '{len(self.root)}' --> '{len(other.root)}'")
            log_func("")
            is_same = False
            return is_same
        return self.root.compare(other.root, log_func, path, ignore_default_changes)


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
        if field_type in self.INTEGER_TYPES:
            self._value = int(value)
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


class GFFStruct(ComparableMixin):
    """Stores a collection of GFFFields.

    Attributes:
    ----------
        struct_id: User defined id.
    """

    COMPARABLE_FIELDS = ("struct_id", "_fields")

    def __init__(
        self,
        struct_id: int = 0,
    ):
        self.struct_id: int = struct_id
        self._fields: dict[str, _GFFField] = {}

    def __repr__(self) -> str:
        if not self._fields:
            return f"GFFStruct(struct_id={self.struct_id}, fields=[])"

        summary_items = []
        for idx, (label, field) in enumerate(self._fields.items()):
            if idx >= 3:
                summary_items.append(f"... ({len(self._fields) - 3} more)")
                break
            field_label = label or f"<unnamed:{idx}>"
            summary_items.append(f"{field_label}:{field.field_type().name}")

        summary = ", ".join(summary_items)
        return f"GFFStruct(struct_id={self.struct_id}, fields=[{summary}])"

    def __str__(self) -> str:
        def _format_value(value: Any) -> str:
            if isinstance(value, GFFStruct):
                return f"<Struct#{value.struct_id}>"
            if isinstance(value, GFFList):
                return f"<List[{len(value)}]>"
            if isinstance(value, bytes):
                return f"<bytes len={len(value)}>"
            value_str = repr(value) if isinstance(value, (str, int, float, bool)) else str(value)
            return value_str if len(value_str) <= 80 else f"{value_str[:77]}..."

        lines: list[str] = [f"GFFStruct #{self.struct_id} ({len(self._fields)} fields)"]
        if not self._fields:
            lines.append("  <empty>")
            return "\n".join(lines)

        for label, field in self._fields.items():
            field_label = label or "<unnamed>"
            field_type = field.field_type().name
            value = field.value()
            lines.append(f"  {field_label} ({field_type}): {_format_value(value)}")

        return "\n".join(lines)

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

    def compare(  # noqa: C901, PLR0911, PLR0912, PLR0913, PLR0915
        self,
        other: object,
        log_func: Callable = print,  # noqa: FBT001
        current_path: PureWindowsPath | os.PathLike | str | None = None,
        ignore_default_changes: bool = False,  # noqa: FBT001, FBT002
    ) -> bool:
        """Recursively compares two GFFStructs.

        Functionally the same as __eq__, but will log/print comparison information as well

        Args:
        ----
            other: {object}: GFFStruct to compare against
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
        if not isinstance(other, GFFStruct):
            log_func(f"GFFStruct counts have changed at '{current_path}': '{len(self)}' --> '<unknown>'")
            log_func()
            is_same = False
            return is_same
        if len(self) != len(other) and not ignore_default_changes:  # sourcery skip: class-extract-method
            log_func("")
            log_func(f"GFFStruct: number of fields have changed at '{current_path}': '{len(self)}' --> '{len(other)}'")
            is_same = False
        if self.struct_id != other.struct_id:
            log_func(f"Struct ID is different at '{current_path}': '{self.struct_id}' --> '{other.struct_id}'")
            is_same = False

        # Create dictionaries for both old and new structures
        old_dict: dict[str, tuple[GFFFieldType, Any]] = {
            label or f"gffstruct({idx})": (ftype, value) for idx, (label, ftype, value) in enumerate(self) if label not in ignore_labels
        }
        new_dict: dict[str, tuple[GFFFieldType, Any]] = {
            label or f"gffstruct({idx})": (ftype, value) for idx, (label, ftype, value) in enumerate(other) if label not in ignore_labels
        }

        # Union of labels from both old and new structures
        all_labels: set[str] = set(old_dict.keys()) | set(new_dict.keys())

        for label in all_labels:
            child_path: PureWindowsPath = current_path / str(label)  # pyright: ignore[reportOperatorIssue]
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
                    log_func(f"Field '{old_ftype.name}' is different at '{child_path}': String representations match, but have other properties that don't (such as a lang id difference).")  # noqa: E501
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
        #   and isinstance(self[label], object_type)  # TODO(th3w1zard1): uncomment this and assert type after fixing all the call typings
        ):
            value = self[label]
        if object_type is bool and value.__class__ is int:
            value = bool(value)  # type: ignore[assignment]  # pyright: ignore[reportAssignmentType]
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
    def _add_missing(target: GFFStruct, source: GFFStruct, relpath: PureWindowsPath | None = None):  # noqa: C901, PLR0912
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
                    value._add_missing(value, source.get_struct(label), relpath.joinpath(label))  # noqa: SLF001  # pyright: ignore[reportOptionalMemberAccess]
                elif field_type == GFFFieldType.List:
                    assert isinstance(value, GFFList)
                    target_list = target.get_list(label)
                    for i, (target_item, source_item) in enumerate(zip(target_list, value)):
                        target_item._add_missing(target_item, source_item, relpath.joinpath(label, str(i)))  # noqa: SLF001  # pyright: ignore[reportOptionalMemberAccess]
            else:
                RobustLogger().debug(f"Adding {field_type!r} '{relpath.joinpath(label)}' to target.")  # pyright: ignore[reportOptionalMemberAccess]
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


class GFFList(ComparableMixin):
    """A collection of GFFStructs."""

    COMPARABLE_SEQUENCE_FIELDS = ("_structs",)

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

    def __repr__(self) -> str:
        """Returns a detailed string representation of the GFFList."""
        if not self._structs:
            return "GFFList([])"

        # Show summary with struct IDs
        struct_ids = [f"Struct#{s.struct_id}" for s in self._structs[:3]]
        preview = ", ".join(struct_ids)
        if len(self._structs) > 3:  # noqa: PLR2004
            preview += f", ... ({len(self._structs) - 3} more)"

        return f"GFFList([{preview}], total={len(self._structs)})"

    def __str__(self) -> str:
        """Returns a human-readable string representation of the GFFList."""
        if not self._structs:
            return "GFFList (empty)"

        lines = [f"GFFList with {len(self._structs)} structs:"]
        for i, struct in enumerate(self._structs):
            lines.append(f"  [{i}] Struct#{struct.struct_id} ({len(struct)} fields)")
            # Show first few fields of each struct
            max_fields_preview = 3
            for field_count, (label, field_type, value) in enumerate(struct):
                if field_count >= max_fields_preview:
                    lines.append(f"      ... ({len(struct) - max_fields_preview} more fields)")
                    break
                # Format value based on type
                if field_type == GFFFieldType.Struct:
                    value_str = f"<Struct#{value.struct_id}>"
                elif field_type == GFFFieldType.List:
                    value_str = f"<List[{len(value)}]>"
                elif isinstance(value, (str, int, float)):
                    value_str = repr(value)
                else:
                    value_str = str(value)
                lines.append(f"      {label}: {value_str}")

        return "\n".join(lines)

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

    def append(
        self,
        struct: GFFStruct,
    ) -> None:
        """Appends an existing struct to the list without creating a copy.

        Args:
        ----
            struct: The `GFFStruct` instance to append.

        Raises:
        ------
            TypeError: If `struct` is not an instance of `GFFStruct`.
        """
        if not isinstance(struct, GFFStruct):
            struct_type = type(struct)
            RobustLogger().error(f"Failed to append struct; expected GFFStruct, received {struct_type!r}.")
            msg = f"The struct must be a GFFStruct instance, got {struct_type!r} instead."
            raise TypeError(msg)

        self._structs.append(struct)
        RobustLogger().debug(f"Appended Struct#{struct.struct_id} to GFFList; list_length={len(self._structs)}.")

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
        other: object,
        log_func: Callable[..., Any] = print,  # noqa: FBT001
        current_path: PureWindowsPath | None = None,
        *,
        ignore_default_changes: bool = False,  # noqa: FBT001, FBT002
    ) -> bool:
        """Compare two GFFLists recursively with content-based detection of moved/reordered entries.

        Functionally the same as __eq__, but will also log/print the differences.
        Similar to TLK comparison, this detects when structs have been shifted/reordered but still exist.

        Args:
        ----
            other: object - the GFF List to compare to
            log_func: the function to use for logging. Defaults to print.
            current_path: PureWindowsPath - Path being compared
            ignore_default_changes: bool - Whether to ignore default value changes

        Returns:
        -------
            is_same_result: bool - Whether the lists are the same

        Processing Logic:
        ----------------
            - Build content-based lookup to detect moved/reordered structs
            - Compare list lengths and log differences
            - Detect truly added/removed structs (content-based, not index-based)
            - Detect moved/reordered structs (same content, different index)
            - Compare structs at same index that haven't moved
        """
        current_path = current_path or PureWindowsPath("GFFList")
        is_same_result = True

        if not isinstance(other, GFFList):
            log_func(f"GFFList counts have changed at '{current_path}': '{len(self)}' --> '<unknown>'")
            log_func("")
            is_same_result = False
            return is_same_result

        # Build content-based lookup to detect moved/reordered structs
        def _hashable_value(value: Any) -> Any:
            """Convert a GFF field value into a hashable, comparable representation."""
            from pykotor.common.geometry import Vector3, Vector4  # Local import to avoid circular deps
            from pykotor.common.language import LocalizedString
            from pykotor.common.misc import ResRef
            if value is None or isinstance(value, (int, float, str, bool, bytes)):
                return value
            if isinstance(value, ResRef):
                return ("ResRef", str(value))
            if isinstance(value, Vector3):
                return ("Vector3", value.x, value.y, value.z)
            if isinstance(value, Vector4):
                return ("Vector4", value.x, value.y, value.z, value.w)
            if isinstance(value, LocalizedString):
                return (
                    "LocalizedString",
                    value.stringref,
                    tuple((lang, gender, text) for lang, gender, text in value),
                )
            if isinstance(value, GFFStruct):
                return struct_key(value)
            if isinstance(value, GFFList):
                return tuple(struct_key(child_struct) for child_struct in value)
            if isinstance(value, (list, tuple, set)):
                return tuple(_hashable_value(item) for item in value)
            if isinstance(value, dict):
                return tuple(sorted((key, _hashable_value(val)) for key, val in value.items()))

            # Fallback: use repr for deterministic but comparable form
            return ("repr", repr(value))

        def struct_key(struct: GFFStruct) -> tuple[int, tuple[tuple[str, GFFFieldType, Any], ...]]:
            """Create a hashable key for a struct based on struct_id and field contents.

            This allows us to detect when structs have been moved/reordered.
            """
            fields_tuple: tuple[tuple[str, GFFFieldType, Any], ...] = tuple(
                sorted(
                    (
                        label,
                        field_type,
                        _hashable_value(value),
                    )
                    for label, field_type, value in struct
                )
            )
            return (struct.struct_id, fields_tuple)

        # Build maps of content to indices
        old_structs_map: dict[tuple[int, tuple[tuple[str, GFFFieldType, Any], ...]], list[int]] = {}  # content -> list of indices
        new_structs_map: dict[tuple[int, tuple[tuple[str, GFFFieldType, Any], ...]], list[int]] = {}  # content -> list of indices

        for idx, struct in enumerate(self):
            key = struct_key(struct)
            if key not in old_structs_map:
                old_structs_map[key] = []
            old_structs_map[key].append(idx)

        for idx, struct in enumerate(other):
            key = struct_key(struct)
            if key not in new_structs_map:
                new_structs_map[key] = []
            new_structs_map[key].append(idx)

        # Find structs that exist in both (at any index) vs truly added/removed
        added_keys = set(new_structs_map.keys()) - set(old_structs_map.keys())
        removed_keys = set(old_structs_map.keys()) - set(new_structs_map.keys())
        common_keys = set(old_structs_map.keys()) & set(new_structs_map.keys())

        # Track which indices we've reported
        reported_indices_old: set[int] = set()
        reported_indices_new: set[int] = set()

        # Report size difference
        len1 = len(self)
        len2 = len(other)

        if len1 != len2:
            log_func(f"GFFList size mismatch at '{current_path}': Old has {len1} structs, New has {len2} structs (diff: {len2 - len1:+d})")

        # Report added structs (in new file only, by content)
        if added_keys:
            log_func(f"\n{len(added_keys)} struct(s) added in new GFFList at '{current_path}':")
            for key in sorted(added_keys, key=lambda k: new_structs_map[k][0]):  # Sort by first occurrence
                indices = new_structs_map[key]
                for idx in indices:
                    struct = other[idx]
                    log_func(f"  [New:{idx}] Struct#{struct.struct_id} (struct_id={struct.struct_id})")
                    log_func("  Contents of new struct:")
                    for label, field_type, field_value in struct:
                        log_func(f"    {field_type.name}: {label}: {format_text(field_value)}")
                    log_func("")
                    reported_indices_new.add(idx)
            is_same_result = False

        # Report removed structs (in old file only, by content)
        if removed_keys:
            log_func(f"\n{len(removed_keys)} struct(s) removed from old GFFList at '{current_path}':")
            for key in sorted(removed_keys, key=lambda k: old_structs_map[k][0]):  # Sort by first occurrence
                indices = old_structs_map[key]
                for idx in indices:
                    struct = self[idx]
                    log_func(f"  [Old:{idx}] Struct#{struct.struct_id} (struct_id={struct.struct_id})")
                    log_func("  Contents of old struct:")
                    for label, field_type, field_value in struct:
                        log_func(f"    {field_type.name}: {label}: {format_text(field_value)}")
                    log_func("")
                    reported_indices_old.add(idx)
            is_same_result = False

        # Detect moved/reordered structs (same content, different index)
        moved_count = 0
        for key in common_keys:
            old_indices = old_structs_map[key]
            new_indices = new_structs_map[key]

            # If indices don't match, structs have been moved/reordered
            if set(old_indices) != set(new_indices):
                if moved_count == 0:
                    log_func(f"\nStructs moved/reordered in GFFList at '{current_path}':")
                moved_count += 1
                struct_id = key[0]
                old_indices_str = ", ".join(str(i) for i in sorted(old_indices))
                new_indices_str = ", ".join(str(i) for i in sorted(new_indices))
                log_func(f"  Struct#{struct_id}: moved from index [{old_indices_str}] to [{new_indices_str}]")
                # Mark these indices as reported so we don't double-report them
                reported_indices_old.update(old_indices)
                reported_indices_new.update(new_indices)

        if moved_count > 0:
            log_func("")
            is_same_result = False

        # Check for structs at same index that have different content (genuine modifications)
        modified_count = 0
        max_index = min(len1, len2)
        for idx in range(max_index):
            if idx in reported_indices_old or idx in reported_indices_new:
                continue

            old_struct = self[idx]
            new_struct = other[idx]

            # Compare structs at same index
            old_key = struct_key(old_struct)
            new_key = struct_key(new_struct)

            if old_key != new_key:
                # This is a genuine content change at the same index
                if modified_count == 0:
                    log_func(f"\nStructs modified at same index in GFFList at '{current_path}':")
                modified_count += 1
                log_func(f"  [{idx}] Old: Struct#{old_struct.struct_id}")
                log_func(f"  [{idx}] New: Struct#{new_struct.struct_id}")
                # Do detailed comparison of the structs
                if not old_struct.compare(new_struct, log_func, current_path / str(idx), ignore_default_changes):
                    is_same_result = False
                reported_indices_old.add(idx)
                reported_indices_new.add(idx)

        # For structs at same index with same content (not moved, not modified), still do comparison
        # to catch any nested differences
        for idx in range(max_index):
            if idx in reported_indices_old or idx in reported_indices_new:
                continue

            old_struct = self[idx]
            new_struct = other[idx]

            # These should be identical at the top level, but check nested structures
            if not old_struct.compare(new_struct, log_func, current_path / str(idx), ignore_default_changes):
                is_same_result = False

        # Summary
        has_differences = bool(added_keys or removed_keys or moved_count or modified_count)
        if has_differences:
            log_func(f"\nGFFList Summary at '{current_path}': {len(added_keys)} added, {len(removed_keys)} removed, {moved_count} moved/reordered, {modified_count} modified")

        return not has_differences
