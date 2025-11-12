"""GFF modification algorithms for TSLPatcher/HoloPatcher.

This module implements GFF field modification logic for applying patches from changes.ini files.
Handles field additions, modifications, list operations, and struct manipulations.

References:
----------
    vendor/TSLPatcher/TSLPatcher.pl - Original Perl GFF modification logic
    vendor/HoloPatcher.NET/src/TSLPatcher.Core/Mods/GFF/ - C# GFF modification implementation
    vendor/Kotor.NET/Kotor.NET.Patcher/ - Incomplete C# patcher
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from itertools import zip_longest
from pathlib import PureWindowsPath
from typing import TYPE_CHECKING, Any

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]  # type: ignore[import-untyped]

from pykotor.common.language import LocalizedString
from pykotor.common.misc import ResRef
from pykotor.resource.formats.gff import GFFFieldType, GFFList, GFFStruct, bytes_gff
from pykotor.resource.formats.gff.gff_data import _GFFField
from pykotor.resource.formats.gff.io_gff import GFFBinaryReader
from pykotor.tslpatcher.mods.template import PatcherModifications

if TYPE_CHECKING:
    import os

    from collections.abc import Callable

    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]

    from pykotor.common.misc import Game
    from pykotor.resource.formats._base import ComparableMixin
    from pykotor.resource.formats.gff import GFF
    from pykotor.resource.type import SOURCE_TYPES
    from pykotor.tslpatcher.logger import PatchLogger
    from pykotor.tslpatcher.memory import PatcherMemory


def set_locstring(
    struct: GFFStruct,
    label: str,
    value: LocalizedStringDelta,
    memory: PatcherMemory,
):
    original = LocalizedString(0)
    value.apply(original, memory)
    struct.set_locstring(label, original)


FIELD_TYPE_TO_GETTER: dict[GFFFieldType, Callable[[GFFStruct, str], Any]] = {
    GFFFieldType.Int8: GFFStruct.get_int8,
    GFFFieldType.UInt8: GFFStruct.get_uint8,
    GFFFieldType.Int16: GFFStruct.get_int16,
    GFFFieldType.UInt16: GFFStruct.get_uint16,
    GFFFieldType.Int32: GFFStruct.get_int32,
    GFFFieldType.UInt32: GFFStruct.get_uint32,
    GFFFieldType.Int64: GFFStruct.get_int64,
    GFFFieldType.UInt64: GFFStruct.get_uint64,
    GFFFieldType.Single: GFFStruct.get_single,
    GFFFieldType.Double: GFFStruct.get_double,
    GFFFieldType.String: GFFStruct.get_string,
    GFFFieldType.ResRef: GFFStruct.get_resref,
    GFFFieldType.LocalizedString: GFFStruct.get_locstring,
    GFFFieldType.Vector3: GFFStruct.get_vector3,
    GFFFieldType.Vector4: GFFStruct.get_vector4,
    GFFFieldType.List: GFFStruct.get_list,
    GFFFieldType.Struct: GFFStruct.get_struct
}


def _set_list(s: GFFStruct, lbl: str, v: Any, _m: PatcherMemory) -> None:
    GFFStruct.set_list(s, lbl, v)

def _set_struct(s: GFFStruct, lbl: str, v: Any, _m: PatcherMemory) -> None:
    GFFStruct.set_struct(s, lbl, v)

FIELD_TYPE_TO_SETTER: dict[GFFFieldType, Callable[[GFFStruct, str, Any, PatcherMemory], None]] = {
    GFFFieldType.Int8: lambda s, lbl, v, _m: GFFStruct.set_int8(s, lbl, v),
    GFFFieldType.UInt8: lambda s, lbl, v, _m: GFFStruct.set_uint8(s, lbl, v),
    GFFFieldType.Int16: lambda s, lbl, v, _m: GFFStruct.set_int16(s, lbl, v),
    GFFFieldType.UInt16: lambda s, lbl, v, _m: GFFStruct.set_uint16(s, lbl, v),
    GFFFieldType.Int32: lambda s, lbl, v, _m: GFFStruct.set_int32(s, lbl, v),
    GFFFieldType.UInt32: lambda s, lbl, v, _m: GFFStruct.set_uint32(s, lbl, v),
    GFFFieldType.Int64: lambda s, lbl, v, _m: GFFStruct.set_int64(s, lbl, v),
    GFFFieldType.UInt64: lambda s, lbl, v, _m: GFFStruct.set_uint64(s, lbl, v),
    GFFFieldType.Single: lambda s, lbl, v, _m: GFFStruct.set_single(s, lbl, v),
    GFFFieldType.Double: lambda s, lbl, v, _m: GFFStruct.set_double(s, lbl, v),
    GFFFieldType.String: lambda s, lbl, v, _m: GFFStruct.set_string(s, lbl, v),
    GFFFieldType.ResRef: lambda s, lbl, v, _m: GFFStruct.set_resref(s, lbl, v),
    GFFFieldType.LocalizedString: set_locstring,
    GFFFieldType.Vector3: lambda s, lbl, v, _m: GFFStruct.set_vector3(s, lbl, v),
    GFFFieldType.Vector4: lambda s, lbl, v, _m: GFFStruct.set_vector4(s, lbl, v),
    GFFFieldType.List: _set_list,
    GFFFieldType.Struct: _set_struct
}


class LocalizedStringDelta(LocalizedString):
    def __init__(self, stringref: FieldValue | None = None):
        super().__init__(0)
        self.stringref: FieldValue | None = stringref  # type: ignore[assignment]

    def __str__(self):
        return f"LocalizedString(stringref={self.stringref!r})"

    def apply(self, locstring: LocalizedString, memory: PatcherMemory):
        """Applies a LocalizedString patch to a LocalizedString object.

        Args:
        ----
            locstring: LocalizedString object to apply patch to
            memory: PatcherMemory object for resolving references

        Processing Logic:
        ----------------
            - Checks if stringref is set and sets locstring stringref if so
            - Iterates through tuple returned from function and sets language, gender and text on locstring.
        """
        if self.stringref is not None:
            locstring.stringref = self.stringref.value(memory, GFFFieldType.UInt32)
        for language, gender, text in self:
            locstring.set_data(language, gender, text)


# region Value Returners
class FieldValue(ABC):
    @abstractmethod
    def value(self, memory: PatcherMemory, field_type: GFFFieldType) -> Any: ...

    def validate(self, value: Any, field_type: GFFFieldType) -> ResRef | str | PureWindowsPath | int | float | object:
        """Validate a value based on its field type.

        Args:
        ----
            value: The value to validate
            field_type: The field type to validate against

        Returns:
        -------
            value: The validated value

        Processing Logic:
        ----------------
            - Check if value matches field type
            - Convert value to expected type if needed
            - Return validated value
        """
        if isinstance(value, PureWindowsPath):  # !FieldPath
            return value
        if field_type == GFFFieldType.ResRef and not isinstance(value, ResRef):
            value = (  # This is here to support empty statements like 'resref=' in ini (allow_no_entries=True in configparser)
                ResRef(str(value)) if not isinstance(value, str) or value.strip() else ResRef.from_blank()
            )
        elif field_type == GFFFieldType.String and not isinstance(value, str):
            value = str(value)
        elif field_type.return_type() is int and isinstance(value, str):
            value = int(value) if value.strip() else "0"
        elif field_type.return_type() is float and isinstance(value, str):
            value = float(value) if value.strip() else "0.0"
        return value


class FieldValueConstant(FieldValue):
    def __init__(self, value: Any):
        self.stored: Any = value

    def value(self, memory: PatcherMemory, field_type: GFFFieldType):  # noqa: ANN201
        return self.validate(self.stored, field_type)


class FieldValueListIndex(FieldValueConstant):
    def __init__(self, value: Any):
        self.stored: int | Literal["listindex"] = value

    def value(self, memory: PatcherMemory, field_type: GFFFieldType):  # noqa: ANN201
        if self.stored == "listindex":
            return self.stored
        return self.validate(self.stored, field_type)


class FieldValue2DAMemory(FieldValue):
    def __init__(self, token_id: int):
        self.token_id: int = token_id

    def value(self, memory: PatcherMemory, field_type: GFFFieldType):  # noqa: ANN201
        memory_val: str | PureWindowsPath | None = memory.memory_2da.get(self.token_id, None)
        if memory_val is None:
            msg = f"2DAMEMORY{self.token_id} was not defined before use"
            raise KeyError(msg)
        return self.validate(memory_val, field_type)


class FieldValueTLKMemory(FieldValue):
    def __init__(self, token_id: int):
        self.token_id: int = token_id

    def value(self, memory: PatcherMemory, field_type: GFFFieldType):  # noqa: ANN201
        memory_val: int | None = memory.memory_str.get(self.token_id, None)
        if memory_val is None:
            msg = f"StrRef{self.token_id} was not defined before use!"
            raise KeyError(msg)
        return self.validate(memory_val, field_type)


# endregion


# region Modify GFF
class ModifyGFF(ABC):
    @abstractmethod
    def apply(
        self,
        root_container: GFFStruct | GFFList,
        memory: PatcherMemory,
        logger: PatchLogger,
    ): ...

    def _navigate_containers(
        self,
        root_container: GFFStruct,
        path: PureWindowsPath | os.PathLike | str,
    ) -> GFFList | GFFStruct | None:
        """Navigates through gff lists/structs to find the specified path.

        Args:
        ----
            root_container (GFFStruct): The root container to start navigation

        Returns:
        -------
            container (GFFList | GFFStruct | None): The container at the end of the path or None if not found

        Processing Logic:
        ----------------
            - It checks if the path is valid PureWindowsPath
            - Loops through each part of the path
            - Acquires the container at each step from the parent container
            - Returns the container at the end or None if not found along the path
        """
        path = PureWindowsPath(path)
        if not path.name:
            return root_container
        container: ComparableMixin | GFFStruct | GFFList | None = root_container
        for step in path.parts:
            if isinstance(container, GFFStruct):
                container = container.acquire(step, None, (GFFStruct, GFFList))
            elif isinstance(container, GFFList):
                container = container.at(int(step))

        assert isinstance(container, (GFFStruct, GFFList, type(None))), f"{type(container).__name__}: {container}"
        return container

    def _navigate_to_field(
        self,
        root_container: GFFStruct,
        path: PureWindowsPath | os.PathLike | str,
    ) -> _GFFField | None:
        """Navigates to a field from the root gff struct from a path."""
        path = PureWindowsPath(path)
        container: GFFList | GFFStruct | None = self._navigate_containers(root_container, path.parent)
        label: str = path.name

        # Return the field if the container is a GFFStruct
        return container._fields[label] if isinstance(container, GFFStruct) else None


class AddStructToListGFF(ModifyGFF):
    def __init__(
        self,
        identifier: str,
        value: FieldValue,
        path: PureWindowsPath | os.PathLike | str,
        index_to_token: int | None = None,
        modifiers: list[ModifyGFF] | None = None,
    ):
        """Initialize a addfield patch that creates a new struct into an existing list.

        Args:
        ----
            identifier (str): INI section name
            value (FieldValue): Field value object
            path (PureWindowsPath): File path
            index_to_token (int | None): Token index
            modifiers (list[ModifyGFF]): Modifiers list
        """
        self.identifier: str = identifier
        if not isinstance(value, (FieldValueListIndex, FieldValueConstant)):
            raise TypeError(f"value must be FieldValueListIndex or FieldValueConstant, instead got {value.__class__.__name__}")
        self.value: FieldValueListIndex | FieldValueConstant = value
        self.path: PureWindowsPath = PureWindowsPath(path)
        self.index_to_token: int | None = index_to_token

        self.modifiers: list[ModifyGFF] = [] if modifiers is None else modifiers

    def apply(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        root_container: GFFStruct,  # type: ignore[override]
        memory: PatcherMemory,
        logger: PatchLogger,
    ):
        """Adds a new struct to a list.

        Args:
        ----
            root_struct: The root struct to navigate and modify.
            memory: The memory object to read/write values from.
            logger: The logger to log errors or warnings.

        Processing Logic:
        ----------------
            1. Navigates to the target list container using the provided path.
            2. Checks if the navigated container is a list, otherwise logs an error.
            3. Creates a new struct and adds it to the list.
            4. Applies any additional field modifications specified in the modifiers.
        """
        list_container: GFFList | None = None
        if self.path.name == ">>##INDEXINLIST##<<":
            #logger.add_verbose(f"Removing unique sentinel from AddStructToListGFF instance (ini section [{self.identifier}]). Path: '{self.path}'")
            self.path = self.path.parent  # HACK(th3w1zard1): idk why conditional parenting is necessary but it works
        navigated_container: GFFList | GFFStruct | None = self._navigate_containers(root_container, self.path) if self.path.name else root_container
        if navigated_container is root_container:
            logger.add_note(f"GFF path '{self.path}' not found, defaulting to the gff root struct.")
        if isinstance(navigated_container, GFFList):
            list_container = navigated_container
        else:
            reason: str = "Does not exist" if navigated_container is None else f"Path points to a '{navigated_container.__class__.__name__}', expected a GFFList."
            logger.add_error(f"Unable to add struct to list '{self.path or f'[{self.identifier}]'}': {reason}")
            return

        new_struct: GFFStruct | None = None
        try:
            lookup: Any = self.value.value(memory, GFFFieldType.Struct)
            if lookup == "listindex":
                new_struct = GFFStruct(len(list_container._structs)-1)  # noqa: SLF001
            elif isinstance(lookup, GFFStruct):
                new_struct = lookup
            else:
                raise ValueError(f"bad lookup: {lookup} ({lookup!r}) expected 'listindex' or GFFStruct")
        except KeyError as e:
            logger.add_error(f"INI section [{self.identifier}] threw an exception: {e}")

        if not isinstance(new_struct, GFFStruct):
            logger.add_error(f"Failed to add a new struct to list '{self.path}' in [{self.identifier}]. Reason: Expected GFFStruct but got '{new_struct}' ({new_struct!r}) of type {type(new_struct).__name__} Skipping...")
            return

        list_container._structs.append(new_struct)  # noqa: SLF001
        if self.index_to_token is not None:
            length = str(len(list_container) - 1)
            logger.add_verbose(f"Set 2DAMEMORY{self.index_to_token}={length}")
            memory.memory_2da[self.index_to_token] = length

        for add_field in self.modifiers:
            assert isinstance(add_field, (AddFieldGFF, AddStructToListGFF, Memory2DAModifierGFF, ModifyFieldGFF)), f"{type(add_field).__name__}: {add_field}"
            list_index = len(list_container) - 1
            newpath = self.path / str(list_index)
            #logger.add_verbose(f"Resolved GFFList path of [{add_field.identifier}] from '{add_field.path}' --> '{newpath}'")
            add_field.path = newpath
            add_field.apply(root_container, memory, logger)

    @property
    def field_type(self) -> GFFFieldType:
        return GFFFieldType.Struct

class AddFieldGFF(ModifyGFF):
    def __init__(  # noqa: PLR0913
        self,
        identifier: str,
        label: str,
        field_type: GFFFieldType,
        value: FieldValue,
        path: PureWindowsPath | os.PathLike | str,
        modifiers: list[ModifyGFF] | None = None,
    ):
        self.identifier: str = identifier
        self.label: str = label
        self.field_type: GFFFieldType = field_type
        self.value: FieldValue = value
        self.path: PureWindowsPath = PureWindowsPath(path)

        self.modifiers: list[ModifyGFF] = [] if modifiers is None else modifiers

    def apply(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        root_container: GFFStruct,  # type: ignore[override]
        memory: PatcherMemory,
        logger: PatchLogger,
    ):
        """Adds a new field to a GFF struct.

        Args:
        ----
            root_struct: GFFStruct - The root GFF struct to navigate and modify.
            memory: PatcherMemory - The memory state to read values from.
            logger: PatchLogger - The logger to record errors to.

        Processing Logic:
        ----------------
            - Navigates to the specified container path and gets the GFFStruct instance
            - Resolves the field value using the provided value expression
            - Resolves the value path if part of !FieldPath memory
            - Sets the field on the struct instance using the appropriate setter based on field type
            - Applies any modifier patches recursively
        """
        #logger.add_verbose(f"Apply patch from INI section [{self.identifier}] FieldType: {self.field_type.name} GFF Path: '{self.path}'")
        # Resolve the special sentinel used when adding a Struct so that navigation targets the parent container
        container_path = self.path.parent if self.path.name == ">>##INDEXINLIST##<<" else self.path
        navigated_container: GFFList | GFFStruct | None = self._navigate_containers(root_container, container_path)
        if isinstance(navigated_container, GFFStruct):
            struct_container = navigated_container
        else:
            reason = "does not exist!" if navigated_container is None else "is not an instance of a GFFStruct."
            logger.add_error(f"Unable to add new GFF Field '{self.label}' at GFF Path '{container_path}'! This {reason}")
            return

        value: Any = self.value.value(memory, self.field_type)

        # if 2DAMEMORY holds a path from !FieldPath, navigate to that field and use its value.
        if isinstance(value, PureWindowsPath):
            stored_fieldpath: PureWindowsPath = value
            if isinstance(self.value, FieldValue2DAMemory):
                logger.add_verbose(f"Looking up field pointer of stored !FieldPath ({stored_fieldpath}) in 2DAMEMORY{self.value.token_id}")
            else:
                logger.add_verbose(f'Found PureWindowsPath object in value() lookup from non-FieldValue2DAMemory object? Path: "{stored_fieldpath}" INI section: [{self.identifier}]')  # noqa: E501
            from_container: GFFList | GFFStruct | None = self._navigate_containers(root_container, stored_fieldpath.parent)
            if not isinstance(from_container, GFFStruct):
                reason = "does not exist!" if from_container is None else "is not an instance of a GFFStruct."
                logger.add_error(f"Unable to use !FieldPath from 2DAMEMORY. Parent field at '{stored_fieldpath}' {reason}")
                return
            value = from_container.value(value.name)
            logger.add_verbose(f"Acquired value '{value}' from 2DAMEMORY !FieldPath({stored_fieldpath})")

        logger.add_verbose(f"AddField: Creating field of type '{self.field_type.name}' value: '{value}' at GFF path '{self.path}'. INI section: [{self.identifier}]")
        FIELD_TYPE_TO_SETTER[self.field_type](struct_container, self.label, value, memory)

        for add_field in self.modifiers:
            assert isinstance(add_field, (AddFieldGFF, AddStructToListGFF, ModifyFieldGFF, Memory2DAModifierGFF)), f"{type(add_field).__name__}: {add_field}"

            # HACK(th3w1zard1): resolves any >>##INDEXINLIST##<<, not sure why lengths aren't the same though (hence use of zip_longest)? Whatever, it works.
            newpath = PureWindowsPath("")
            for part, resolvedpart in zip_longest(add_field.path.parts, self.path.parts):
                newpath /= resolvedpart or part
            #logger.add_verbose(f"Resolved gff path of INI section [{add_field.identifier}] from relative '{add_field.path}' --> absolute '{newpath}'")
            add_field.path = newpath

            add_field.apply(root_container, memory, logger)


class Memory2DAModifierGFF(ModifyGFF):
    """A modifier class used for !FieldPath support."""

    def __init__(
        self,
        identifier: str,
        path: PureWindowsPath | os.PathLike | str,
        dst_token_id: int,
        src_token_id: int | None = None,
    ):
        self.identifier: str = identifier
        self.dest_token_id: int = dst_token_id
        self.src_token_id: int | None = src_token_id
        self.path: PureWindowsPath = PureWindowsPath(path)

    def apply(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        root_container: GFFStruct,  # type: ignore[override]
        memory: PatcherMemory,
        logger: PatchLogger,
    ):
        dest_field: _GFFField | None = None
        source_field: _GFFField | None = None
        display_dest_name = f"2DAMEMORY{self.dest_token_id}"
        if self.src_token_id is None:  # assign the path and leave.
            display_src_name = f"!FieldPath({self.path})"
            logger.add_verbose(f"Assign {display_dest_name}={display_src_name}")
            memory.memory_2da[self.dest_token_id] = self.path
            return

        display_src_name = f"2DAMEMORY{self.src_token_id}"
        logger.add_verbose(f"GFFList ptr !fieldpath: Assign {display_dest_name}={display_src_name} initiated. iniPath: {self.path}, section: [{self.identifier}]")

        ptr_to_dest: PureWindowsPath | Any = memory.memory_2da.get(self.dest_token_id, None) if self.dest_token_id is not None else self.path
        if isinstance(ptr_to_dest, PureWindowsPath):
            dest_field = self._navigate_to_field(root_container, ptr_to_dest)
            if dest_field is None:
                raise ValueError(f"Cannot assign 2DAMEMORY{self.dest_token_id}=2DAMEMORY{self.src_token_id}: LEFT side of assignment's path '{ptr_to_dest}' does not point to a valid GFF Field!")  # noqa: E501
            assert isinstance(dest_field, _GFFField)
            logger.add_verbose(f"LEFT SIDE 2DAMEMORY{self.src_token_id} lookup at '{ptr_to_dest}' returned '{dest_field.value()}'")
        elif ptr_to_dest is None:
            logger.add_verbose(f"Left side {display_dest_name} is not defined yet.")
        else:
            logger.add_verbose(f"Left side {display_dest_name} value of {ptr_to_dest} will be overwritten.")

        # Lookup assigning value
        ptr_to_src: PureWindowsPath | Any = memory.memory_2da.get(self.src_token_id, None)
        if ptr_to_src is None:
            raise ValueError(f"Cannot assign {display_dest_name}={display_src_name} because RIGHT side of assignment is undefined.")

        if isinstance(ptr_to_src, PureWindowsPath):
            logger.add_verbose(f"Assigner {display_src_name} is a pointer !FieldPath to another field located at '{ptr_to_src}'")
            source_field = self._navigate_to_field(root_container, ptr_to_src)
            assert not isinstance(source_field, PureWindowsPath)
            assert isinstance(source_field, _GFFField)
        else:
            logger.add_verbose(f"Assigner {display_src_name} holds literal value '{ptr_to_src}'. other stored info debug: Path: '{self.path}' INI section: [{self.identifier}]")  # noqa: E501


        if isinstance(dest_field, _GFFField):
            logger.add_verbose("assign dest ptr field.")
            assert source_field is None or dest_field.field_type() is source_field.field_type(), f"Not a _GFFField: {ptr_to_src} ({display_src_name}) OR {dest_field.field_type()} != {source_field.field_type()}"  # noqa: E501
            dest_field._value = FieldValueConstant(ptr_to_src).value(memory, dest_field.field_type())  # noqa: SLF001
        else:
            memory.memory_2da[self.dest_token_id] = ptr_to_dest

class ModifyFieldGFF(ModifyGFF):
    def __init__(
        self,
        path: PureWindowsPath | os.PathLike | str,
        value: FieldValue,
        identifier: str = ""
    ):
        self.path: PureWindowsPath = PureWindowsPath(path)
        self.value: FieldValue = value
        self.identifier: str = identifier

    def apply(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        root_container: GFFStruct,  # type: ignore[override]
        memory: PatcherMemory,
        logger: PatchLogger,
    ):
        """Applies a patch to an existing field in a GFF structure.

        Args:
        ----
            root_struct: {GFF structure}: Root GFF structure to navigate and modify
            memory: {PatcherMemory}: Memory context to retrieve values
            logger: {PatchLogger}: Logger to record errors

        Processing Logic:
        ----------------
            - Navigates container hierarchy to the parent of the field using the patch path
            - Checks if parent container exists and is a GFFStruct
            - Gets the field type from the parent struct
            - Converts the patch value to the correct type
            - Calls the corresponding setter method on the parent struct
        """
        label: str = self.path.name
        navigated_container: GFFList | GFFStruct | None = self._navigate_containers(root_container, self.path.parent)
        if not isinstance(navigated_container, GFFStruct):
            reason: str = "does not exist!" if navigated_container is None else "is not an instance of a GFFStruct."
            logger.add_error(f"Unable to modify GFF field '{label}'. Path '{self.path}' {reason}")
            return

        navigated_struct: GFFStruct = navigated_container
        field_type: GFFFieldType = navigated_struct._fields[label].field_type()

        value: Any = self.value.value(memory, field_type)

        # if 2DAMEMORY holds a path from !FieldPath, navigate to that field and use its value.
        if isinstance(value, PureWindowsPath):
            stored_fieldpath: PureWindowsPath = value
            if isinstance(self.value, FieldValue2DAMemory):
                logger.add_verbose(f"Looking up field pointer of stored !FieldPath ({stored_fieldpath}) in 2DAMEMORY{self.value.token_id}")
            else:
                logger.add_verbose(f'Found PureWindowsPath object in value() lookup from non-FieldValue2DAMemory object? Path: "{stored_fieldpath}" INI section: [{self.identifier}]')  # noqa: E501
            from_container: GFFList | GFFStruct | None = self._navigate_containers(root_container, value.parent)
            if not isinstance(from_container, GFFStruct):
                reason = "does not exist!" if from_container is None else "is not an instance of a GFFStruct."
                logger.add_error(f"Unable use !FieldPath from 2DAMEMORY. Parent field at '{value.parent}' {reason}")
                return
            value = from_container.value(value.name)
            logger.add_verbose(f"Acquired value '{value}' from field at !FieldPath '{stored_fieldpath}'")

        try:
            orig_value = FIELD_TYPE_TO_GETTER[field_type](navigated_struct, label)
            logger.add_verbose(f"Found original value of '{orig_value}' ({orig_value!r}) at GFF Path {self.path}: Patch section: [{self.identifier}]")
        except KeyError:
            msg = (
                f"The field {field_type.name} did not exist at {self.path} in INI section [{self.identifier}]. Use AddField if you need to create fields/structs."
                "\nDue to the above error, no value will be set here."
            )
            RobustLogger().exception(msg)
            logger.add_error(msg)
            return

        logger.add_verbose(f"Direct set value of determined field type '{field_type.name}' at GFF path '{self.path}' to new value '{value}'. INI section: [{self.identifier}]")
        if field_type is not GFFFieldType.LocalizedString:
            FIELD_TYPE_TO_SETTER[field_type](navigated_struct, label, value, memory)
            return

        assert isinstance(value, LocalizedString), f"{type(value).__name__}: {value}"
        if not navigated_struct.exists(label):
            navigated_struct.set_locstring(label, value)
        else:
            assert isinstance(value, LocalizedStringDelta), f"{type(value).__name__}: {value}"
            original: LocalizedString = navigated_struct.get_locstring(label)
            value.apply(original, memory)
            navigated_struct.set_locstring(label, original)


# endregion


class ModificationsGFF(PatcherModifications):
    def __init__(
        self,
        filename: str,
        *,
        replace: bool,  # noqa: FBT001
        modifiers: list[ModifyGFF] | None = None,
    ):
        super().__init__(filename, replace)
        self.modifiers: list[ModifyGFF] = [] if modifiers is None else modifiers

    def patch_resource(
        self,
        source: SOURCE_TYPES,
        memory: PatcherMemory,
        logger: PatchLogger,
        game: Game,
    ) -> bytes:
        gff: GFF = GFFBinaryReader(source).load()
        self.apply(gff, memory, logger, game)
        return bytes_gff(gff)

    def apply(
        self,
        mutable_data: GFF,
        memory: PatcherMemory,
        logger: PatchLogger,
        game: Game,
    ):
        for change_field in self.modifiers:
            change_field.apply(mutable_data.root, memory, logger)
