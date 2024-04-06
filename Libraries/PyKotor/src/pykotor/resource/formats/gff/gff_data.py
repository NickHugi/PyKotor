from __future__ import annotations

import difflib
import math

from collections.abc import Callable
from copy import deepcopy
from enum import Enum, IntEnum
from typing import TYPE_CHECKING, Any, ClassVar, Dict, Generic, List, Type, TypeVar, Union, cast, overload

from pykotor.common.geometry import Vector3, Vector4
from pykotor.common.language import LocalizedString
from pykotor.common.misc import Game, ResRef
from pykotor.resource.type import ResourceType
from utility.error_handling import safe_repr
from utility.logger_util import get_root_logger
from utility.string_util import format_text
from utility.system.path import PureWindowsPath

if TYPE_CHECKING:
    import os

    from collections.abc import Generator

    from typing_extensions import Self

T = TypeVar("T")
U = TypeVar("U")


def format_diff(old_value: object, new_value: object, name: str) -> str:
#     Convert values to strings if they aren't already
    str_old_value = str(old_value).splitlines(keepends=True)
    str_new_value = str(new_value).splitlines(keepends=True)

#     Generate unified diff
    diff = difflib.unified_diff(str_old_value, str_new_value, fromfile=f"(old){name}", tofile=f"(new){name}", lineterm="")

#     Return formatted diff
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


class Difference:
    def __init__(self, path: os.PathLike | str, old_value: Any, new_value: Any):
        """Initializes a Difference instance representing a specific difference between two GFFStructs.

        Args:
        ----
            path (os.PathLike | str): The path to the value within the GFFStruct where the difference was found.
            old_value (Any): The value from the original GFFStruct at the specified path.
            new_value (Any): The value from the compared GFFStruct at the specified path.
        """
        self.path: PureWindowsPath = PureWindowsPath.pathify(path)
        self.old_value: Any = old_value
        self.new_value: Any = new_value

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
    #     Return False if the list has any contents (meaning the objects are different), True if it's empty.
        return not bool(self.differences)

    def add_difference(self, path, old_value, new_value):
        """Adds a difference to the collection of tracked differences.

        Args:
        ----
            path (str): The path to the value where the difference was found.
            old_value (Any): The original value at the specified path.
            new_value (Any): The new value at the specified path that differs from the original.
        """
        self.differences.append(Difference(path, old_value, new_value))

    def get_changed_values(self) -> list[Difference]:
        """Returns a list of differences where the value has changed from the original.

        Returns:
        -------
            list[Difference]: The list of differences with changed values.
        """
        return [diff for diff in self.differences if diff.old_value is not None and diff.new_value is not None and diff.old_value != diff.new_value]

    def get_new_values(self) -> list[Difference]:
        """Returns a list of differences where a new value is present in the compared GFFStruct.

        Returns:
        -------
            list[Difference]: The list of differences with new values.
        """
        return [diff for diff in self.differences if diff.old_value is None and diff.new_value is not None]

    def get_removed_values(self) -> list[Difference]:
        """Returns a list of differences where a value is present in the original GFFStruct but not in the compared.

        Returns:
        -------
            list[Difference]: The list of differences with removed values.
        """
        return [diff for diff in self.differences if diff.old_value is not None and diff.new_value is None]


class GFF:
    """Represents the data of a GFF file."""

    BINARY_TYPE: ResourceType = ResourceType.GFF

    def __init__(
        self,
        content: GFFContent = GFFContent.GFF,
    ):
        self.content: GFFContent = content
        self.root: GFFStruct = GFFStruct(struct_id=-1)

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


class FieldGFF(Generic[T]):
    """Read-only immutable object representing a field stored in a GFF struct."""

    def __init__(
        self,
        field_type: GFFFieldType,
        value: T | None = None,
    ):
        self._field_type: GFFFieldType = field_type
        self._value: T = self.default(field_type) if value is None else value

        expected_type: type[T] = cast(Type[T], field_type.return_type())
        assert isinstance(self._value, expected_type), f"Expected value '{self._value!r}' to be {field_type.return_type().__name__}, was instead {self._value.__class__.__name__}"

    def __deepcopy__(self, memo):
        return self.__class__(self._field_type, deepcopy(self.value(), memo))

    @classmethod
    def default(cls, field_type: GFFFieldType) -> T:
        default = unique_sentinel
        if field_type.return_type() == int:
            default = 0
        elif field_type.return_type() == float:
            default = 0.0
        elif field_type == GFFFieldType.LocalizedString:
            default = LocalizedString.from_invalid()
        elif field_type == GFFFieldType.ResRef:
            default = ResRef.from_blank()
        elif field_type == GFFFieldType.Vector3:
            default = Vector3.from_null()
        elif field_type == GFFFieldType.Vector4:
            default = Vector4.from_null()
        elif field_type == GFFFieldType.String:
            default = ""
        elif field_type == GFFFieldType.Struct:
            default = GFFStruct()
        elif field_type == GFFFieldType.List:
            default = GFFList()
        if default is unique_sentinel:
            raise ValueError(f"Invalid gff field type in default lookup: {field_type!r}")
        expected_type = cast(Type[T], field_type.return_type())
        if not isinstance(default, expected_type):
            raise TypeError(f"Default '{default!r}' had unexpected type '{default.__class__.__name__}', expected '{expected_type.__name__}' which matches {field_type!r}")
        return default

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
    ) -> T:
        """Returns the value.

        Returns:
        -------
            The field's value.
        """
        assert isinstance(self._value, self._field_type.return_type()), f"Expected {self._value!r} to be {self._field_type.return_type().__name__}, was instead {type(self._value).__name__}"
        return self._value


class FieldProperty(FieldGFF[T], Generic[T, U]):
    """A property class representing a GFF field, useful for abstracting arbitrary GFF structs into specific generic classes."""

    def __init__(
        self,
        label: str,
        field_type: GFFFieldType,
        default: T | None = None,
        *,
        game: Game = Game.K1,
        return_type: type[U] | Callable[[T], U] | None = None,
        store_type: type[T] | Callable[[U], T] | None = None,
    ):
        assert isinstance(label, str), f"Expected label to be str, instead was {type(label).__name__}"
        assert len(label) <= 16, f"GFF Field Label's cannot exceed 16 characters, got {label} ({len(label)} characters)"
        self._default: T = self.default(field_type) if default is None else default
        super().__init__(field_type, default)
        self._label: str = label
        self._game: Game | None = game
        self._return_type: type[U] | Callable[[T], U] | None = return_type
        self._store_type: type[T] | Callable[[U], T] | None = store_type

    def __get__(self, instance: GFFStruct | None, owner: type[GFFStruct]) -> U:
        if instance is None:
            value = self._default
        else:
            lookup: FieldGFF[T] | None = instance.get(self._label)
            value: T | None = lookup.value() if lookup is not None else self._default
            if value is None:
                raise ValueError(f"'{self._label}' {self._field_type!r} field somehow was None ({owner.__name__}).")
        if self._return_type is None:
            return cast(U, value)
        if isinstance(self._return_type, Callable):
            return self._return_type(value)
        if not isinstance(value, self._return_type):  # Check if value is U
            return self._return_type(value)
        return value

    def __set__(self, instance: GFFStruct | None, value: T | U) -> None:
        assert instance is not None, "Improper access to FieldProperty.__set__ without an instance."
        sval = cast(T, value)
        rval = cast(U, value)
        if self._store_type is None:
            self._set_value(instance, sval)
            return
        if isinstance(self._store_type, Callable):
            self._set_value(instance, self._store_type(rval))
            return
        if not isinstance(value, self._store_type):  # Check if value is T
            self._set_value(instance, self._store_type(rval))
            return
        #assert isinstance(value, self._default.__class__), f"Incorrect type: {type(value).__name__} sent, expected {self._default.__class__.__name__}"
        self._set_value(instance, value)

    def _no_change_needed(self, value: T) -> bool:
        return value == self.value()

    def _set_value(self, struct: GFFStruct, value: T):
        if self._no_change_needed(value):
            return
        assert isinstance(value, self._field_type.return_type()), f"Cannot set {self._field_type!r} to a value of type {type(value).__name__}. Expected type {self._field_type.return_type().__name__}"
        if self._field_type == GFFFieldType.UInt8:
            struct.set_uint8(self._label, value)  # type: ignore[reportArgumentType]
        elif self._field_type == GFFFieldType.Int8:
            struct.set_int8(self._label, value)  # type: ignore[reportArgumentType]
        elif self._field_type == GFFFieldType.UInt16:
            struct.set_uint16(self._label, value)  # type: ignore[reportArgumentType]
        elif self._field_type == GFFFieldType.Int16:
            struct.set_int16(self._label, value)  # type: ignore[reportArgumentType]
        elif self._field_type == GFFFieldType.UInt32:
            struct.set_uint32(self._label, value)  # type: ignore[reportArgumentType]
        elif self._field_type == GFFFieldType.Int32:
            struct.set_int32(self._label, value)  # type: ignore[reportArgumentType]
        elif self._field_type == GFFFieldType.UInt64:
            struct.set_uint64(self._label, value)  # type: ignore[reportArgumentType]
        elif self._field_type == GFFFieldType.Int64:
            struct.set_int64(self._label, value)  # type: ignore[reportArgumentType]
        elif self._field_type == GFFFieldType.Single:
            struct.set_single(self._label, value)  # type: ignore[reportArgumentType]
        elif self._field_type == GFFFieldType.Double:
            struct.set_double(self._label, value)  # type: ignore[reportArgumentType]
        elif self._field_type == GFFFieldType.String:
            struct.set_string(self._label, value)  # type: ignore[reportArgumentType]
        elif self._field_type == GFFFieldType.ResRef:
            struct.set_resref(self._label, value)  # type: ignore[reportArgumentType]
        elif self._field_type == GFFFieldType.LocalizedString:
            struct.set_locstring(self._label, value)  # type: ignore[reportArgumentType]
        elif self._field_type == GFFFieldType.Binary:
            struct.set_binary(self._label, value)  # type: ignore[reportArgumentType]
        elif self._field_type == GFFFieldType.Struct:
            struct.set_struct(self._label, value)  # type: ignore[reportArgumentType]
        elif self._field_type == GFFFieldType.List:
            struct.set_list(self._label, value)  # type: ignore[reportArgumentType]
        elif self._field_type == GFFFieldType.Vector4:
            struct.set_vector4(self._label, value)  # type: ignore[reportArgumentType]
        elif self._field_type == GFFFieldType.Vector3:
            struct.set_vector3(self._label, value)  # type: ignore[reportArgumentType]
        else:
            msg = f"Unsupported field type for label {self._label}: {self._field_type!r}"
            raise TypeError(msg)


class GFFStruct(Dict[str, FieldGFF]):
    """Stores a collection of GFFFields.

    Attributes:
    ----------
        struct_id: User defined id (defaults to 0).
    """
    MAX_LENGTH: ClassVar[int] = 16

    def __repr__(self):
        return repr(self._fields)

    def _validate_label(self, label: str):
        assert isinstance(label, str), f"Invalid field Label: '{label}'"
        assert len(label) <= self.MAX_LENGTH, f"GFF Field Labels have a maximum length of 16, got '{label}' ({len(label)} characters)"

    def __init__(self, struct_id: int = 0):
        self.struct_id: int = struct_id
        self._fields: dict[str, FieldGFF] = {}

    def __len__(
        self,
    ) -> int:
        """Returns the number of fields."""
        return len(self._fields)

    def items(
        self,
    ):
        return self._fields.items()

    def __iter__(
        self,
    ) -> Generator[tuple[str, GFFFieldType, Any], Any, None]:
        """Iterates through the stored fields yielding each field's (label, type, value)."""
        for label, field in self.items():
            yield label, field.field_type(), field.value()

    def __deepcopy__(self, memo: dict[int, Any]) -> Self:
        key_orig_to_copy: int = id(self)
        if key_orig_to_copy in memo:
            return memo[key_orig_to_copy]
        shallow: Self = GFFStruct.__new__(GFFStruct)  # type: ignore[assignment]
        memo[key_orig_to_copy] = shallow
        shallow.struct_id = self.struct_id
        shallow._fields = deepcopy(self._fields, memo)
        shallow.__class__ = self.__class__
        return shallow

    def __setitem__(self, key: str, value: FieldGFF[T]):
        self._validate_label(key)
        self._fields[key] = value

    def __getitem__(self, key: str) -> FieldGFF[type]:
        self._validate_label(key)
        return self._fields[key]

    @overload
    def get(self, __key: str) -> FieldGFF: ...
    @overload
    def get(self, __key: str, __default: T = None) -> FieldGFF | T: ...
    def get(self, __key: str, __default: T = None) -> FieldGFF | T:  # type: ignore[assignment]
        return self._fields.get(__key, __default)

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

    #     Create dictionaries for both old and new structures
        old_dict: dict[str, tuple[GFFFieldType, Any]] = {
            label or f"gffstruct({idx})": (ftype, value) for idx, (label, ftype, value) in enumerate(self) if label not in ignore_labels
        }
        new_dict: dict[str, tuple[GFFFieldType, Any]] = {
            label or f"gffstruct({idx})": (ftype, value) for idx, (label, ftype, value) in enumerate(other_gff_struct) if label not in ignore_labels
        }

    #     Union of labels from both old and new structures
        all_labels: set[str] = set(old_dict.keys()) | set(new_dict.keys())

        for label in all_labels:
            child_path: PureWindowsPath = current_path / str(label)
            old_ftype, old_value = old_dict.get(label, (None, None))
            new_ftype, new_value = new_dict.get(label, (None, None))

            if ignore_default_changes and is_ignorable_comparison(old_value, new_value):
                continue

        #     Check for missing fields/values in either structure
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

        #     Check if field types have changed
            if old_ftype != new_ftype:
                log_func(f"Field type is different at '{child_path}': '{old_ftype.name}'-->'{new_ftype.name}'")
                is_same = False
                continue

        #     Compare values depending on their types
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
        default: T | None = None,
        *,
        return_type: type[T] | tuple[U, ...] | tuple[T, ...] | None = None
    ) -> T:
        """Gets the value from the specified field.

        Args:
        ----
            label (str): The Field Label.
            default (T): Default value to return if not exists.
            return_type (type[T]): Type to return, useful when not sending a default.

        Returns:
        -------
            The field value. If the field does not exist then the default is returned instead.
        """
        field: FieldGFF[T] | None = self._fields.get(label)
        return cast(T, default if field is None else field.value())

    def value(
        self,
        label: str,
        *,
        return_type: type[T] | None = None
    ) -> T:
        field: FieldGFF[T] = self._fields[label]
        value: T = field.value()
        return value

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
        self._validate_label(label)
        self[label] = FieldGFF(GFFFieldType.UInt8, value)

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
        self._validate_label(label)
        self._fields[label] = FieldGFF(GFFFieldType.UInt16, value)

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
        self._validate_label(label)
        self._fields[label] = FieldGFF(GFFFieldType.UInt32, value)

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
        self._validate_label(label)
        self._fields[label] = FieldGFF(GFFFieldType.UInt64, value)

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
        self._validate_label(label)
        self._fields[label] = FieldGFF(GFFFieldType.Int8, value)

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
        self._validate_label(label)
        self._fields[label] = FieldGFF(GFFFieldType.Int16, value)

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
        self._validate_label(label)
        self._fields[label] = FieldGFF(GFFFieldType.Int32, value)

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
        self._validate_label(label)
        self._fields[label] = FieldGFF(GFFFieldType.Int64, value)

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
        self._validate_label(label)
        self._fields[label] = FieldGFF(GFFFieldType.Single, value)

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
        self._validate_label(label)
        self._fields[label] = FieldGFF(GFFFieldType.Double, value)

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
        self._validate_label(label)
        if isinstance(value, str):
            value = ResRef(value)
        self._fields[label] = FieldGFF(GFFFieldType.ResRef, value)

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
        self._validate_label(label)
        self._fields[label] = FieldGFF(GFFFieldType.String, value)

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
        self._validate_label(label)
        self._fields[label] = FieldGFF(GFFFieldType.LocalizedString, value)

    def set_binary(
        self,
        label: str,
        value: bytes | bytearray | memoryview,
    ):
        """Sets the value and field type of the field with the specified label.

        Args:
        ----
            label: The field label.
            value: The new field value.
        """
        self._validate_label(label)
        self._fields[label] = FieldGFF(GFFFieldType.Binary, value)

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
        self._validate_label(label)
        self._fields[label] = FieldGFF(GFFFieldType.Vector3, value)

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
        self._validate_label(label)
        self._fields[label] = FieldGFF(GFFFieldType.Vector4, value)

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
        self._validate_label(label)
        self._fields[label] = FieldGFF(GFFFieldType.Struct, value)
        return value

    def set_list(
        self,
        label: str,
        value: GFFList,
    ) -> GFFList:
        """Adds a GFFList with the specified label in our instance's Fields.

        Args:
        ----
            label (str): The Field Label.
            value (GFFList): The new field value.

        Returns:
        -------
            The value that was passed to the method.
        """
        self._validate_label(label)
        self._fields[label] = FieldGFF(GFFFieldType.List, value)
        return value

    def get_uint8(
        self,
        label: str,
    ) -> int:
        """Returns the UInt8 value stored in the field with the specified label.

        Args:
        ----
            label (str): The Field Label.

        Raises:
        ------
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is something other than UInt8.

        Returns:
        -------
            The UInt8 field value as an int.
        """
        ftype: GFFFieldType = self._fields[label].field_type()
        if ftype is not GFFFieldType.UInt8:
            raise TypeError(f"The specified field exists but does not store a UInt8 field ({ftype.name})")
        return self._fields[label].value()

    def get_uint16(
        self,
        label: str,
    ) -> int:
        """Returns the UInt16 value stored in the field with the specified label.

        Args:
        ----
            label (str): The Field Label.

        Raises:
        ------
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is something other than UInt16.

        Returns:
        -------
            The UInt16 field value as an int.
        """
        ftype: GFFFieldType = self._fields[label].field_type()
        if ftype is not GFFFieldType.UInt16:
            raise TypeError(f"The specified field exists but does not store a UInt16 field ({ftype.name})")
        return self._fields[label].value()

    def get_uint32(
        self,
        label: str,
    ) -> int:
        """Returns the UInt32 value stored in the field with the specified label.

        Args:
        ----
            label (str): The Field Label.

        Raises:
        ------
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is something other than UInt32.

        Returns:
        -------
            The UInt32 field value as an int.
        """
        ftype: GFFFieldType = self._fields[label].field_type()
        if ftype is not GFFFieldType.UInt32:
            raise TypeError(f"The specified field exists but does not store a UInt32 field ({ftype.name})")
        return self._fields[label].value()

    def get_uint64(
        self,
        label: str,
    ) -> int:
        """Returns the UInt64 value stored in the field with the specified label.

        Args:
        ----
            label (str): The Field Label.

        Raises:
        ------
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is something other than UInt64.

        Returns:
        -------
            The UInt64 field value as an int.
        """
        ftype: GFFFieldType = self._fields[label].field_type()
        if ftype is not GFFFieldType.UInt64:
            raise TypeError(f"The specified field exists but does not store a UInt64 field ({ftype.name})")
        return self._fields[label].value()

    def get_int8(
        self,
        label: str,
    ) -> int:
        """Returns the Int8 value stored in the field with the specified label.

        Args:
        ----
            label (str): The Field Label.

        Raises:
        ------
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is not set to Int8.

        Returns:
        -------
            The Int8 field value as an int.
        """
        ftype: GFFFieldType = self._fields[label].field_type()
        if ftype is not GFFFieldType.Int8:
            raise TypeError(f"The specified field exists but does not store a Int8 field ({ftype.name})")
        return self._fields[label].value()

    def get_int16(
        self,
        label: str,
    ) -> int:
        """Returns the Int16 value stored in the field with the specified label.

        Args:
        ----
            label (str): The Field Label.

        Raises:
        ------
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is something other than Int16.

        Returns:
        -------
            The Int16 field value as an int.
        """
        ftype: GFFFieldType = self._fields[label].field_type()
        if ftype is not GFFFieldType.Int16:
            raise TypeError(f"The specified field exists but does not store a Int16 field ({ftype.name})")
        return self._fields[label].value()

    def get_int32(
        self,
        label: str,
    ) -> int:
        """Returns the Int32 value stored in the field with the specified label.

        Args:
        ----
            label (str): The Field Label.

        Raises:
        ------
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is something other than Int32.

        Returns:
        -------
            The Int32 field value as an int.
        """
        ftype: GFFFieldType = self._fields[label].field_type()
        if ftype is not GFFFieldType.Int32:
            raise TypeError(f"The specified field exists but does not store a Int32 field ({ftype.name})")
        return self._fields[label].value()

    def get_int64(
        self,
        label: str,
    ) -> int:
        """Returns the Int64 value stored in the field with the specified label.

        Args:
        ----
            label (str): The Field Label.

        Raises:
        ------
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is something other than Int64.

        Returns:
        -------
            The Int64 field value as an int.
        """
        ftype: GFFFieldType = self._fields[label].field_type()
        if ftype is not GFFFieldType.Int64:
            raise TypeError(f"The specified field exists but does not store a Int64 field ({ftype.name})")
        return self._fields[label].value()

    def get_single(
        self,
        label: str,
    ) -> float:
        """Returns the single-point float value stored in the field with the specified label.

        Args:
        ----
            label (str): The Field Label.

        Raises:
        ------
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is something other than Single.

        Returns:
        -------
            The Single field value as a float.
        """
        ftype: GFFFieldType = self._fields[label].field_type()
        if ftype is not GFFFieldType.Single:
            raise TypeError(f"The specified field exists but does not store a Single field ({ftype.name})")
        return self._fields[label].value()

    def get_double(
        self,
        label: str,
    ) -> float:
        """Returns the double-point float value stored in the field with the specified label.

        Args:
        ----
            label (str): The Field Label.

        Raises:
        ------
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is something other than Double.

        Returns:
        -------
            The Double field value as a float.
        """
        ftype: GFFFieldType = self._fields[label].field_type()
        if ftype is not GFFFieldType.Double:
            raise TypeError(f"The specified field exists but does not store a Double field ({ftype.name})")
        return self._fields[label].value()

    def get_resref(
        self,
        label: str,
    ) -> ResRef:
        """Returns the ResRef value stored in the field with the specified label.

        Args:
        ----
            label (str): The Field Label.

        Raises:
        ------
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is something other than ResRef.

        Returns:
        -------
            The ResRef field value.
        """
        ftype: GFFFieldType = self._fields[label].field_type()
        if ftype is not GFFFieldType.ResRef:
            raise TypeError(f"The specified field exists but does not store a ResRef field ({ftype.name})")
        return self._fields[label].value()

    def get_string(
        self,
        label: str,
    ) -> str:
        """Returns the String value stored in the field with the specified label.

        Args:
        ----
            label (str): The Field Label.

        Raises:
        ------
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is something other than String.

        Returns:
        -------
            The String field value.
        """
        ftype: GFFFieldType = self._fields[label].field_type()
        if ftype is not GFFFieldType.String:
            raise TypeError(f"The specified field exists but does not store a String field ({ftype.name})")
        return self._fields[label].value()

    def get_locstring(
        self,
        label: str,
    ) -> LocalizedString:
        """Returns the LocalizedString value stored in the field with the specified label.

        Args:
        ----
            label (str): The Field Label.

        Raises:
        ------
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is something other than LocalizedString.

        Returns:
        -------
            The LocalizedString field value.
        """
        ftype: GFFFieldType = self._fields[label].field_type()
        if ftype is not GFFFieldType.LocalizedString:
            raise TypeError(f"The specified field exists but does not store a LocalizedString field ({ftype.name})")
        return self._fields[label].value()

    def get_vector3(
        self,
        label: str,
    ) -> Vector3:
        """Returns the Vector3 value stored in the field with the specified label.

        Args:
        ----
            label (str): The Field Label.

        Raises:
        ------
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is something other than Vector3.

        Returns:
        -------
            The Vector3 field value.
        """
        ftype: GFFFieldType = self._fields[label].field_type()
        if ftype is not GFFFieldType.Vector3:
            raise TypeError(f"The specified field exists but does not store a Vector3 field ({ftype.name})")
        return self._fields[label].value()

    def get_vector4(
        self,
        label: str,
    ) -> Vector4:
        """Returns the Vector4 value stored in the field with the specified label.

        Args:
        ----
            label (str): The Field Label.

        Raises:
        ------
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is something other than Vector4.

        Returns:
        -------
            The Vector4 field value.
        """
        ftype: GFFFieldType = self._fields[label].field_type()
        if ftype is not GFFFieldType.Vector4:
            raise TypeError(f"The specified field exists but does not store a Vector4 field ({ftype.name})")
        return self._fields[label].value()

    def get_binary(
        self,
        label: str,
    ) -> bytes:
        """Returns the Binary value stored in the field with the specified label.

        Args:
        ----
            label (str): The Field Label.

        Raises:
        ------
            KeyError: If no field exists with the specified label.
            TypeError: If the field type is something other than Binary.

        Returns:
        -------
            The Binary field value.
        """
        ftype: GFFFieldType = self._fields[label].field_type()
        if ftype is not GFFFieldType.Binary:
            raise TypeError(f"The specified field exists but does not store a Binary field ({ftype.name})")
        return self._fields[label].value()

    def get_struct(
        self,
        label: str,
    ) -> GFFStruct:
        """Returns a copy of the value from the field with the specified Label.

        Args:
        ----
            label (str): The Field Label.

        Raises:
        ------
            KeyError: If no field exists with the specified Label.
            TypeError: If the field type is not set to Struct.

        Returns:
        -------
            A shallow copy of the gff Struct at the specified Field.
        """
        ftype: GFFFieldType = self._fields[label].field_type()
        if ftype is not GFFFieldType.Struct:
            raise TypeError(f"The specified field exists but does not store a Struct field ({ftype.name})")
        return self._fields[label].value()

    def get_list(
        self,
        label: str,
    ) -> GFFList:
        """Returns a copy of the value from the field with the specified Label.

        Args:
        ----
            label (str): The Field Label.

        Raises:
        ------
            KeyError: If no field exists with the specified Label.
            TypeError: If the field type is not set to List.

        Returns:
        -------
            A shallow copy of the gff List at the specified Field.
        """
        ftype: GFFFieldType = self._fields[label].field_type()
        if ftype is not GFFFieldType.List:
            raise TypeError(f"The specified field exists but does not store a List field ({ftype.name})")
        return self._fields[label].value()

class TypedProperty(Generic[T]):
    def __init__(self, name: str, field: FieldGFF[T], default: T):
        self.name: str = f"_{name}"
        self.field: FieldGFF[T] = field
        self.default: T = default

    def __get__(self, instance: GFFStruct, owner) -> T:
        return getattr(instance, self.name, self.default)

    def __set__(self, instance: GFFStruct, value: T):
        field: FieldGFF[T] = self.field
        if not isinstance(value, field.field_type().return_type()):
            raise TypeError(f"Expected value of type {self.field.field_type().return_type().__name__}, got {type(value).__name__}")
        setattr(instance, self.name, value)

unique_sentinel = object()
class GFFStructInterface(GFFStruct):

    def __init__(self, struct_id: int = 0):
        super().__init__(struct_id)
        self._all_fields: dict[str, FieldProperty[Any, Any]] = {}

    def all_fields(self) -> dict[str, FieldProperty[Any, Any]]:
        """Returns a mapping for Label to the Field.

        Unfortunately this means any class inheriting GFFStructInterface must provide a FieldProperty for all fields
        that GFFStruct may contain. Otherwise the fallback won't work (see `__getitem__`)
        """
        if not hasattr(self, "_all_fields"):
            mro: list[type] = self.__class__.mro()
            self._all_fields = {
                value._label: value
                for cls in mro
                for key, value in cls.__dict__.items()
                if isinstance(value, FieldProperty)
            }
        return self._all_fields

    @classmethod
    def _recursive_unwrap(cls, struct: GFFStruct):
        struct.__class__ = GFFStruct
        for attr_name in struct.__dict__.copy():
            if attr_name in {"_fields", "struct_id"}:  # e.g. struct_id, _fields
                continue
            if attr_name.startswith("__"):
                continue
            delattr(struct, attr_name)

        for _label, ftype, value in struct:
            if ftype == GFFFieldType.Struct:
                assert isinstance(value, GFFStruct), f"{type(value).__name__}, field label: {_label}"
                value.__class__ = GFFStruct
                cls._recursive_unwrap(value)
            elif ftype == GFFFieldType.List:
                assert isinstance(value, GFFList), f"{type(value).__name__}, field label: {_label}"
                for child_struct in value:
                    assert isinstance(child_struct, GFFStruct), f"{type(child_struct).__name__}, field label: {_label}"
                    cls._recursive_unwrap(child_struct)

    def unwrap(self, *, game: Game, use_deprecated: bool = False) -> GFFStruct:
        """Take off the GFFStructInterface wrapper and return a plain GFFStruct.

        More specifically, create a deepcopy of self, modify nested instances of GFFStructInterface in _fields, recurse through all and
        set __class__ of all of them to GFFStruct.
        """
        new_struct = deepcopy(self)
        self._recursive_unwrap(new_struct)

        if game.is_k1():
            for label, field_property in self.all_fields().items():
                if field_property._game.is_k2():
                    get_root_logger().info(f"Removing k2-exclusive Field in unwrap process: {label}")
                    del self._fields[label]
        if use_deprecated:
            for label in self._fields.copy():
                if label not in self.all_fields():
                    get_root_logger().info(f"Removing unknown/deprecated Field in unwrap process: {label}")
                    del self._fields[label]
        return new_struct

    def __getitem__(self, key: str) -> FieldGFF[Any]:
        """Fallback to default values if the field doesn't exist. Defaults are grabbed dynamically from
        class-level FieldProperty definitions.
        """
        return super().__getitem__(key) if self.exists(key) else self.all_fields()[key]


StructType_co = TypeVar("StructType_co", bound=GFFStruct, covariant=True)
class GFFList(List[Union[StructType_co, GFFStruct]]):  # type: ignore[pylance]
    """A collection of GFFStructs."""

    @property
    def _structs(self) -> Self:
        """Provided for backwards compatibility, deprecated."""
        return self

    def __init__(self, wrapper: type[GFFStruct] = GFFStruct):
        self.struct_wrapper: type[GFFStruct] = wrapper

    def add(
        self,
        struct_id: int,
    ) -> GFFStruct:
        """Create a new struct and append it into the end of the list.

        Args:
        ----
            struct_id (int): The StructID to use for the new struct.
        """
        new_struct: GFFStruct = self.struct_wrapper(struct_id)
        self.append(new_struct)
        return new_struct

    def at(
        self,
        index: int,
        *,
        default: T = None
    ) -> GFFStruct | T:
        """Returns the struct at the index if it exists, otherwise returns None.

        Args:
        ----
            index: The index of the desired struct.

        Returns:
        -------
            The corresponding GFFList or None.
        """
        if index < len(self._structs):
            return self[index]
        if default is None:
            return cast(T, None)
        assert isinstance(default, GFFStruct), f"Default arg to GFFList.at({index}, default={default!r}) must be a GFFStruct instance."
        self[index] = default
        return default

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

    #     Use the indices in the original lists as keys
        old_dict = dict(enumerate(self))
        new_dict = dict(enumerate(other_gff_list))

    #     Detect unique items in both lists
        unique_to_old = set(old_dict.keys()) - set(new_dict.keys())
        unique_to_new = set(new_dict.keys()) - set(old_dict.keys())

        struct: GFFStruct
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

    #     For items present in both lists
        common_items = old_dict.keys() & new_dict.keys()
        for list_index in common_items:
            old_child: GFFStruct = old_dict[list_index]
            new_child: GFFStruct = new_dict[list_index]
            if not old_child.compare(new_child, log_func, current_path / str(list_index), ignore_default_changes):
                is_same_result = False

        return is_same_result


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

    def __deepcopy__(self, memo):
        return self  # do not deepcopy.

    def setter(self) -> Callable[[GFFStruct, str, Any], Any]:
        func_map: dict[GFFFieldType, Callable[[GFFStruct, str, Any], Any]] = {
            GFFFieldType.Int8: GFFStruct.set_int8,
            GFFFieldType.UInt8: GFFStruct.set_uint8,
            GFFFieldType.Int16: GFFStruct.set_int16,
            GFFFieldType.UInt16: GFFStruct.set_uint16,
            GFFFieldType.Int32: GFFStruct.set_int32,
            GFFFieldType.UInt32: GFFStruct.set_uint32,
            GFFFieldType.Int64: GFFStruct.set_int64,
            GFFFieldType.UInt64: GFFStruct.set_uint64,
            GFFFieldType.Single: GFFStruct.set_single,
            GFFFieldType.Double: GFFStruct.set_double,
            GFFFieldType.String: GFFStruct.set_string,
            GFFFieldType.ResRef: GFFStruct.set_resref,
            GFFFieldType.LocalizedString: GFFStruct.set_locstring,
            GFFFieldType.Vector3: GFFStruct.set_vector3,
            GFFFieldType.Vector4: GFFStruct.set_vector4,
            GFFFieldType.Struct: GFFStruct.set_struct,
            GFFFieldType.List: GFFStruct.set_list,
        }
        return func_map[self]

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


#    UInt8: GFFFieldType[int] = type("UInt8", (int, _FieldType), {})
#    Int8: GFFFieldType[int] = type("Int8", (int, _FieldType), {})
#    UInt16: GFFFieldType[int] = type("UInt16", (int, _FieldType), {})
#    Int16: GFFFieldType[int] = type("Int16", (int, _FieldType), {})
#    UInt32: GFFFieldType[int] = type("UInt32", (int, _FieldType), {})
#    Int32: GFFFieldType[int] = type("Int32", (int, _FieldType), {})
#    UInt64: GFFFieldType[int] = type("UInt64", (int, _FieldType), {})
#    Int64: GFFFieldType[int] = type("Int64", (int, _FieldType), {})
#    Single: GFFFieldType[int] = type("Single", (float, _FieldType), {})
#    Double: GFFFieldType[float] = type("Double", (float, _FieldType), {})
#    String: GFFFieldType[str] = type("String", (str, _FieldType), {})
#    ResRef: GFFFieldType[ResRef] = type("ResRef", (ResRef,_FieldType), {})
#    LocalizedString: GFFFieldType[LocalizedString] = type("LocalizedString", (LocalizedString, _FieldType), {})
#    Binary: GFFFieldType[bytes] = type("Binary", (bytes, _FieldType), {})
#    Struct: GFFFieldType[GFFStruct] = type("Struct", (GFFStruct, _FieldType), {})
#    List: GFFFieldType[GFFList] = type("List", (GFFList, _FieldType), {})
#    Vector4: GFFFieldType[Vector4] = type("Vector4", (Vector4, _FieldType), {})
#    Vector3: GFFFieldType[Vector3] = type("Vector3", (Vector3, _FieldType), {})

#  Test 2
#    UInt8 = int
#    Int8 = int
#    UInt16 = int
#    Int16 = int
#    UInt32 = int
#    Int32 = int
#    UInt64 = int
#    Int64 = int
#    Single = float
#    Double = float
#    String = str
#    ResRef = ResRef
#    LocalizedString = str
#    Binary = bytes
#    Struct = GFFStruct
#    List = GFFList
#    Vector4 = Vector4
#    Vector3 = Vector3
#  Test 3
#    UInt8 = NewType("UInt8", int)
#    Int8 = NewType("Int8", int)
#    UInt16 = NewType("UInt16", int)
#    Int16 = NewType("Int16", int)
#    UInt32 = NewType("UInt32", int)
#    Int32 = NewType("Int32", int)
#    UInt64 = NewType("UInt64", int)
#    Int64 = NewType("Int64", int)
#    Single = NewType("Single", float)
#    Double = NewType("Double", float)
#    String = NewType("String", str)
#    ResRef = NewType("ResRef", ResRef)
#    LocalizedString = NewType("LocalizedString", LocalizedString)
#    Binary = NewType("Binary", bytes)
#    Struct = NewType("Struct", GFFStruct)
#    List = NewType("List", GFFList)
#    Vector4 = NewType("Vector4", Vector4)
#    Vector3 = NewType("Vector3", Vector3)

if __name__ == "__main__":
    test_uint8 = GFFFieldType.UInt8
    assert issubclass(test_uint8, GFFFieldType)
    assert not isinstance(test_uint8(), GFFFieldType)
    assert isinstance(test_uint8(), GFFFieldType.UInt8)
    assert not isinstance(test_uint8, GFFFieldType.UInt16)
    assert issubclass(test_uint8, GFFFieldType)
    assert issubclass(test_uint8, GFFFieldType.UInt8)
    assert not issubclass(test_uint8, GFFFieldType.UInt16)
