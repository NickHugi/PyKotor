from __future__ import annotations

from abc import ABC, abstractmethod
from itertools import zip_longest
from typing import TYPE_CHECKING, Any, Callable

from pykotor.common.language import LocalizedString
from pykotor.common.misc import Game, ResRef
from pykotor.resource.formats.gff import GFF, GFFFieldType, GFFList, GFFStruct, bytes_gff
from pykotor.resource.formats.gff.io_gff import GFFBinaryReader
from pykotor.tslpatcher.mods.template import PatcherModifications
from utility.path import PureWindowsPath

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import _GFFField
    from pykotor.resource.type import SOURCE_TYPES
    from pykotor.tslpatcher.logger import PatchLogger
    from pykotor.tslpatcher.memory import PatcherMemory


class LocalizedStringDelta(LocalizedString):
    def __init__(self, stringref: FieldValue | None = None) -> None:
        super().__init__(0)
        self.stringref: FieldValue | None = stringref

    def apply(self, locstring: LocalizedString, memory: PatcherMemory) -> None:
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
    def value(self, memory: PatcherMemory, field_type: GFFFieldType) -> Any:
        ...

    def validate(self, value: Any, field_type: GFFFieldType) -> ResRef | str | int | float | object:
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
        if isinstance(value, PureWindowsPath):
            return value
        if field_type == GFFFieldType.ResRef and not isinstance(value, ResRef):
            value = (
                ResRef(str(value))
                if not isinstance(value, str) or value.strip()
                else ResRef.from_blank()
            )
        elif field_type == GFFFieldType.String and not isinstance(value, str):
            value = str(value)
        elif field_type.return_type() == int and isinstance(value, str):
            value = int(value) if value.strip() else "0"
        elif field_type.return_type() == float and isinstance(value, str):
            value = float(value) if value.strip() else "0.0"
        return value


class FieldValueConstant(FieldValue):
    def __init__(self, value: Any):
        self.stored = value

    def value(self, memory: PatcherMemory, field_type: GFFFieldType):
        return self.validate(self.stored, field_type)


class FieldValue2DAMemory(FieldValue):
    def __init__(self, token_id: int):
        self.token_id = token_id

    def value(self, memory: PatcherMemory, field_type: GFFFieldType):
        return self.validate(memory.memory_2da[self.token_id], field_type)


class FieldValueTLKMemory(FieldValue):
    def __init__(self, token_id: int):
        self.token_id: int = token_id

    def value(self, memory: PatcherMemory, field_type: GFFFieldType):
        return self.validate(memory.memory_str[self.token_id], field_type)


# endregion


# region Modify GFF
class ModifyGFF(ABC):
    @abstractmethod
    def apply(
        self,
        root_container: GFFStruct | GFFList,
        memory: PatcherMemory,
        logger: PatchLogger,
    ) -> None:
        ...

    def _navigate_containers(
        self,
        root_container: GFFStruct,
        path: PureWindowsPath,
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
        path = path if isinstance(path, PureWindowsPath) else PureWindowsPath(path)
        if not path.name:
            return root_container
        container: GFFStruct | GFFList | None = root_container
        for step in path.parts:
            if isinstance(container, GFFStruct):
                container = container.acquire(step, None, (GFFStruct, GFFList))
            elif isinstance(container, GFFList):
                container = container.at(int(step))

        return container

    def _navigate_to_field(
        self,
        root_container: GFFStruct,
        path: PureWindowsPath | str,
    ) -> _GFFField | None:
        path = path if isinstance(path, PureWindowsPath) else PureWindowsPath(path)
        label: str = path.name
        container: GFFStruct | GFFList | None = root_container
        for step in path.parent.parts:
            if isinstance(container, GFFStruct):
                container = container.acquire(step, None, (GFFStruct, GFFList))
            elif isinstance(container, GFFList):
                container = container.at(int(step))
            else:
                return None

        return container._fields[label] if isinstance(container, GFFStruct) else None


class AddStructToListGFF(ModifyGFF):
    def __init__(
        self,
        identifier: str,
        value: FieldValue,
        path: PureWindowsPath,
        index_to_token: int | None = None,
        modifiers: list[ModifyGFF] | None = None,
    ):
        """Initialize a addfield patch that creates a new struct into an existing list.

        Args:
        ----
            identifier (str): Field identifier
            value (FieldValue): Field value object
            path (PureWindowsPath): File path
            index_to_token (int | None): Token index
            modifiers (list[ModifyGFF]): Modifiers list
        """
        self.identifier: str = identifier
        self.value: FieldValue = value
        self.path: PureWindowsPath = path if isinstance(path, PureWindowsPath) else PureWindowsPath(path)
        self.index_to_token: int | None = index_to_token

        self.modifiers: list[ModifyGFF] = [] if modifiers is None else modifiers

    def apply(
        self,
        root_struct,
        memory: PatcherMemory,
        logger: PatchLogger,
    ) -> None:
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
            self.path = self.path.parent  # HACK: idk why conditional parenting is necessary but it works
        navigated_container: GFFList | GFFStruct | None = (
            self._navigate_containers(root_struct, self.path)
            if self.path.name
            else root_struct
        )
        if isinstance(navigated_container, GFFList):
            list_container = navigated_container
        else:
            reason: str = "does not exist!" if navigated_container is None else "is not an instance of a GFFList."
            logger.add_error(f"Unable to add struct to list in '{self.path or f'[{self.identifier}]'}' {reason}")
            return
        new_struct = self.value.value(memory, GFFFieldType.Struct)

        if not isinstance(new_struct, GFFStruct):
            logger.add_error(f"Failed to add a new struct to list '{self.path}' in [{self.identifier}]. Skipping...")
            return
        list_container._structs.append(new_struct)
        if self.index_to_token is not None:
            memory.memory_2da[self.index_to_token] = str(len(list_container) - 1)

        for add_field in self.modifiers:
            assert isinstance(add_field, (AddFieldGFF, AddStructToListGFF))
            add_field.path = self.path / str(len(list_container) - 1)
            add_field.apply(root_struct, memory, logger)


class AddFieldGFF(ModifyGFF):
    def __init__(
        self,
        identifier: str,
        label: str,
        field_type: GFFFieldType,
        value: FieldValue,
        path: PureWindowsPath,
        modifiers: list[ModifyGFF] | None = None,
    ):
        self.identifier: str = identifier
        self.label: str = label
        self.field_type: GFFFieldType = field_type
        self.value: FieldValue = value
        self.path: PureWindowsPath = path if isinstance(path, PureWindowsPath) else PureWindowsPath(path)

        self.modifiers: list[ModifyGFF] = [] if modifiers is None else modifiers

    def apply(
        self,
        root_struct,
        memory: PatcherMemory,
        logger: PatchLogger,
    ) -> None:
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
        navigated_container: GFFList | GFFStruct | None = self._navigate_containers(root_struct, self.path)
        if isinstance(navigated_container, GFFStruct):
            struct_container = navigated_container
        else:
            reason = "does not exist!" if navigated_container is None else "is not an instance of a GFFStruct."
            logger.add_error(f"Unable to add new Field '{self.label}'. Parent field at '{self.path}' {reason}")
            return

        value = self.value.value(memory, self.field_type)

        # if 2DAMEMORY holds a path string from !FieldPath, navigate to that field and use its value.
        if isinstance(value, PureWindowsPath):
            from_path = value if isinstance(value, PureWindowsPath) else PureWindowsPath(value)
            if from_path.parent.name:
                from_container = self._navigate_containers(root_struct, from_path.parent)
                if not isinstance(from_container, GFFStruct):
                    reason = "does not exist!" if from_container is None else "is not an instance of a GFFStruct."
                    logger.add_error(f"Unable use !FieldPath from 2DAMEMORY. Parent field at '{from_path}' {reason}")
                    return
                value = from_container.value(from_path.name)

        def set_locstring():
            original = LocalizedString(0)
            assert isinstance(value, LocalizedStringDelta)
            value.apply(original, memory)
            struct_container.set_locstring(self.label, original)

        def set_struct():
            assert isinstance(value, GFFStruct)
            struct_container.set_struct(self.label, value)

        def set_list():
            assert isinstance(value, GFFList)
            struct_container.set_list(self.label, value)

        func_map: dict[GFFFieldType, Any] = {
            GFFFieldType.Int8: lambda: struct_container.set_int8(self.label, value),
            GFFFieldType.UInt8: lambda: struct_container.set_uint8(self.label, value),
            GFFFieldType.Int16: lambda: struct_container.set_int16(self.label, value),
            GFFFieldType.UInt16: lambda: struct_container.set_uint16(self.label, value),
            GFFFieldType.Int32: lambda: struct_container.set_int32(self.label, value),
            GFFFieldType.UInt32: lambda: struct_container.set_uint32(self.label, value),
            GFFFieldType.Int64: lambda: struct_container.set_int64(self.label, value),
            GFFFieldType.UInt64: lambda: struct_container.set_uint64(self.label, value),
            GFFFieldType.Single: lambda: struct_container.set_single(self.label, value),
            GFFFieldType.Double: lambda: struct_container.set_double(self.label, value),
            GFFFieldType.String: lambda: struct_container.set_string(self.label, value),
            GFFFieldType.ResRef: lambda: struct_container.set_resref(self.label, value),
            GFFFieldType.LocalizedString: set_locstring,
            GFFFieldType.Vector3: lambda: struct_container.set_vector3(self.label, value),
            GFFFieldType.Vector4: lambda: struct_container.set_vector4(self.label, value),
            GFFFieldType.Struct: set_struct,
            GFFFieldType.List: set_list,
        }
        func_map[self.field_type]()

        for add_field in self.modifiers:
            #assert isinstance(add_field, (AddFieldGFF, AddStructToListGFF))
            newpath = PureWindowsPath("")
            for part, resolvedpart in zip_longest(add_field.path.parts, self.path.parts):
                newpath /= resolvedpart or part
            add_field.path = newpath  # resolves any >>##INDEXINLIST##<<, not sure why lengths aren't the same though (ziplongest)? Whatever, it works.
            add_field.apply(root_struct, memory, logger)


class Memory2DAModifierGFF(ModifyGFF):
    """A modifier class used for !FieldPath support."""

    def __init__(
        self,
        identifier: str,
        twoda_index: int,
        path: PureWindowsPath,
    ):
        self.identifier: str = identifier
        self.twoda_index: int = twoda_index
        self.path: PureWindowsPath = path if isinstance(path, PureWindowsPath) else PureWindowsPath(path)

    def apply(self, container, memory: PatcherMemory, logger: PatchLogger):
        memory.memory_2da[self.twoda_index] = self.path


class ModifyFieldGFF(ModifyGFF):
    def __init__(
        self,
        path: PureWindowsPath | str,
        value: FieldValue,
    ) -> None:
        self.path: PureWindowsPath = path if isinstance(path, PureWindowsPath) else PureWindowsPath(path)
        self.value: FieldValue = value

    def apply(
        self,
        root_struct,
        memory: PatcherMemory,
        logger: PatchLogger,
    ) -> None:
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
        label = self.path.name
        navigated_container: GFFList | GFFStruct | None = self._navigate_containers(root_struct, self.path.parent)
        if not isinstance(navigated_container, GFFStruct):
            reason: str = "does not exist!" if navigated_container is None else "is not an instance of a GFFStruct."
            logger.add_error(f"Unable to modify Field '{label}'. Parent field at '{self.path}' {reason}")
            return

        navigated_struct: GFFStruct = navigated_container
        field_type = navigated_struct._fields[label].field_type()
        value = self.value.value(memory, field_type)

        def set_locstring() -> None:
            assert isinstance(value, LocalizedStringDelta)
            if navigated_struct.exists(label):
                original: LocalizedString = navigated_struct.get_locstring(label)
                value.apply(original, memory)
                navigated_struct.set_locstring(label, original)
            else:
                navigated_struct.set_locstring(label, value)

        func_map: dict[GFFFieldType, Callable] = {
            GFFFieldType.Int8: lambda: navigated_struct.set_int8(label, value),
            GFFFieldType.UInt8: lambda: navigated_struct.set_uint8(label, value),
            GFFFieldType.Int16: lambda: navigated_struct.set_int16(label, value),
            GFFFieldType.UInt16: lambda: navigated_struct.set_uint16(label, value),
            GFFFieldType.Int32: lambda: navigated_struct.set_int32(label, value),
            GFFFieldType.UInt32: lambda: navigated_struct.set_uint32(label, value),
            GFFFieldType.Int64: lambda: navigated_struct.set_int64(label, value),
            GFFFieldType.UInt64: lambda: navigated_struct.set_uint64(label, value),
            GFFFieldType.Single: lambda: navigated_struct.set_single(label, value),
            GFFFieldType.Double: lambda: navigated_struct.set_double(label, value),
            GFFFieldType.String: lambda: navigated_struct.set_string(label, value),
            GFFFieldType.ResRef: lambda: navigated_struct.set_resref(label, value),
            GFFFieldType.LocalizedString: set_locstring,
            GFFFieldType.Vector3: lambda: navigated_struct.set_vector3(label, value),
            GFFFieldType.Vector4: lambda: navigated_struct.set_vector4(label, value),
        }
        func_map[field_type]()


# endregion


class ModificationsGFF(PatcherModifications):
    def __init__(
        self,
        filename: str,
        replace: bool,
        modifiers: list[ModifyGFF] | None = None,
    ) -> None:
        super().__init__(filename, replace)
        self.modifiers: list[ModifyGFF] = modifiers if modifiers is not None else []

    def patch_resource(
        self,
        source_gff: SOURCE_TYPES,
        memory: PatcherMemory,
        logger: PatchLogger | None = None,
        game: Game | None = None,
    ) -> bytes:
        gff: GFF = GFFBinaryReader(source_gff).load()
        self.apply(gff, memory, logger, game)
        return bytes_gff(gff)

    def apply(
        self,
        gff: GFF,
        memory: PatcherMemory,
        logger: PatchLogger | None = None,
        game: Game | None = None,
    ) -> None:
        for change_field in self.modifiers:
            change_field.apply(gff.root, memory, logger)

