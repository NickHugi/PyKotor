from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from pykotor.common.language import LocalizedString
from pykotor.common.misc import ResRef
from pykotor.resource.formats.gff import GFF, GFFFieldType, GFFList, GFFStruct

if TYPE_CHECKING:
    from pykotor.tslpatcher.logger import PatchLogger
    from pykotor.tslpatcher.memory import PatcherMemory

# TODO: 2DAMEMORY# as field path+label, store+save


class LocalizedStringDelta(LocalizedString):
    def __init__(self, stringref: FieldValue | None = None) -> None:
        super().__init__(0)
        self.stringref: FieldValue | None = stringref

    def apply(self, locstring: LocalizedString, memory: PatcherMemory) -> None:
        if self.stringref is not None:
            locstring.stringref = self.stringref.value(memory, GFFFieldType.UInt32)
        for language, gender, text in self:
            locstring.set(language, gender, text)


# region Value Returners
class FieldValue(ABC):
    @abstractmethod
    def value(self, memory: PatcherMemory, field_type: GFFFieldType) -> Any:
        ...

    def validate(self, value: Any, field_type: GFFFieldType) -> Any:
        if field_type == GFFFieldType.ResRef and not isinstance(value, ResRef):
            value = ResRef(str(value))
        elif field_type == GFFFieldType.String and not isinstance(value, str):
            value = str(value)
        elif field_type.return_type() == int and isinstance(value, str):
            value = int(value)
        elif field_type.return_type() == float and isinstance(value, str):
            value = float(value)
        return value


class FieldValueConstant(FieldValue):
    def __init__(self, value: Any):
        self.stored = value

    def value(self, memory: PatcherMemory, field_type: GFFFieldType) -> Any:
        return self.validate(self.stored, field_type)


class FieldValue2DAMemory(FieldValue):
    def __init__(self, token_id: int):
        self.token_id = token_id

    def value(self, memory: PatcherMemory, field_type: GFFFieldType) -> Any:
        return self.validate(memory.memory_2da[self.token_id], field_type)


class FieldValueTLKMemory(FieldValue):
    def __init__(self, token_id: int):
        self.token_id = token_id

    def value(self, memory: PatcherMemory, field_type: GFFFieldType) -> Any:
        return self.validate(memory.memory_str[self.token_id], field_type)


# endregion


# region Modify GFF
class ModifyGFF(ABC):
    @abstractmethod
    def apply(
        self,
        container: GFFStruct | GFFList,
        memory: PatcherMemory,
        logger: PatchLogger,
    ) -> None:
        ...


class AddFieldGFF(ModifyGFF):
    def __init__(
        self,
        identifier: str,
        label: str,
        field_type: GFFFieldType,
        value: FieldValue,
        path: str | Path,
        modifiers: list[ModifyGFF] | None = None,
        index_to_list_token: int | None = None,
    ):
        self.identifier: str = identifier
        self.label: str = label
        self.field_type: GFFFieldType = field_type
        self.value: FieldValue = value
        self.path: Path = Path(path)
        self.index_to_list_token: int | None = index_to_list_token

        self.modifiers: list[ModifyGFF] = [] if modifiers is None else modifiers

    def apply(
        self,
        container: GFFStruct,
        memory: PatcherMemory,
        logger: PatchLogger,
    ) -> None:
        container = self._navigate_containers(
            container,
            self.path,
        )  # type: ignore
        if container is None:
            logger.add_warning(
                "Parent field at '{}' does not exist or is not a List or Struct. Unable to add new Field '{}'...".format(
                    self.path,
                    self.label,
                ),
            )
            return
        assert container is not None
        value = self.value.value(memory, self.field_type)

        def set_locstring() -> None:
            original = LocalizedString(0)
            value.apply(original, memory)
            container.set_locstring(self.label, original)

        def set_struct() -> GFFStruct | None:
            if isinstance(container, GFFStruct):
                return container.set_struct(self.label, value)
            if isinstance(container, GFFList):
                return container.add(value.struct_id)
            return None

        def set_list() -> GFFList:
            return container.set_list(self.label, value)

        func_map: dict[GFFFieldType, Any] = {
            GFFFieldType.Int8: lambda: container.set_int8(self.label, value),
            GFFFieldType.UInt8: lambda: container.set_uint8(self.label, value),
            GFFFieldType.Int16: lambda: container.set_int16(self.label, value),
            GFFFieldType.UInt16: lambda: container.set_uint16(self.label, value),
            GFFFieldType.Int32: lambda: container.set_int32(self.label, value),
            GFFFieldType.UInt32: lambda: container.set_uint32(self.label, value),
            GFFFieldType.Int64: lambda: container.set_int64(self.label, value),
            GFFFieldType.UInt64: lambda: container.set_uint64(self.label, value),
            GFFFieldType.Single: lambda: container.set_single(self.label, value),
            GFFFieldType.Double: lambda: container.set_double(self.label, value),
            GFFFieldType.String: lambda: container.set_string(self.label, value),
            GFFFieldType.ResRef: lambda: container.set_resref(self.label, value),
            GFFFieldType.LocalizedString: lambda: set_locstring(),  # pylint: disable=unnecessary-lambda
            GFFFieldType.Vector3: lambda: container.set_vector3(self.label, value),
            GFFFieldType.Vector4: lambda: container.set_vector4(self.label, value),
            GFFFieldType.Struct: lambda: set_struct(),  # pylint: disable=unnecessary-lambda
            GFFFieldType.List: lambda: set_list(),  # pylint: disable=unnecessary-lambda
        }
        container = func_map[self.field_type]()

        if not isinstance(container, GFFStruct | GFFList):
            msg = "container not a valid type"
            raise TypeError(msg)

        if self.index_to_list_token is not None and isinstance(container, GFFList):
            memory.memory_2da[self.index_to_list_token] = str(len(container) - 1)

        for add_field in self.modifiers:
            add_field.apply(container, memory, logger)

    def _navigate_containers(
        self,
        container: GFFStruct | GFFList,
        path: str | Path,
    ) -> GFFStruct | GFFList:
        path = Path(path)
        hierarchy: list[str] = [part for part in path.parts if part]

        for step in hierarchy:
            if isinstance(container, GFFStruct):
                container = container.acquire(step, None, (GFFStruct, GFFList))
            elif isinstance(container, GFFList):
                container = container.at(int(step))

        return container


class ModifyFieldGFF(ModifyGFF):
    def __init__(self, path: str, value: FieldValue) -> None:
        self.path: str = path
        self.value: FieldValue = value

    def apply(
        self,
        container: GFFStruct | GFFList,
        memory: PatcherMemory,
        logger: PatchLogger,
    ) -> None:
        navigationtuple = self._navigate_containers(container, self.path)
        if navigationtuple is None:
            logger.add_warning(
                f"Unable to find a field label matching '{self.path}', skipping...",
            )
            return

        container, label, field_type = navigationtuple
        value = self.value.value(memory, field_type)

        def set_locstring() -> None:
            if container.exists(label):
                original: LocalizedString = container.get_locstring(label)
                value.apply(original, memory)
                container.set_locstring(label, original)
            else:
                container.set_locstring(label, value)

        func_map: dict[GFFFieldType, Callable] = {
            GFFFieldType.Int8: lambda: container.set_int8(label, value),
            GFFFieldType.UInt8: lambda: container.set_uint8(label, value),
            GFFFieldType.Int16: lambda: container.set_int16(label, value),
            GFFFieldType.UInt16: lambda: container.set_uint16(label, value),
            GFFFieldType.Int32: lambda: container.set_int32(label, value),
            GFFFieldType.UInt32: lambda: container.set_uint32(label, value),
            GFFFieldType.Int64: lambda: container.set_int64(label, value),
            GFFFieldType.UInt64: lambda: container.set_uint64(label, value),
            GFFFieldType.Single: lambda: container.set_single(label, value),
            GFFFieldType.Double: lambda: container.set_double(label, value),
            GFFFieldType.String: lambda: container.set_string(label, value),
            GFFFieldType.ResRef: lambda: container.set_resref(label, value),
            GFFFieldType.LocalizedString: lambda: set_locstring(),  # pylint: disable=unnecessary-lambda
            GFFFieldType.Vector3: lambda: container.set_vector3(label, value),
            GFFFieldType.Vector4: lambda: container.set_vector4(label, value),
        }
        func_map[field_type]()

    def _navigate_containers(
        self,
        container: GFFStruct | GFFList | object,
        path: Path | str,
    ) -> tuple[GFFStruct, str, GFFFieldType] | None:
        path = Path(path)
        hierarchy: list[Path] = list(path.parents)[::-1][1:]  # Removing the root
        label: str = path.name

        for step in hierarchy:
            if isinstance(container, GFFStruct):
                container = container.acquire(step.name, None, (GFFStruct, GFFList))
            elif isinstance(container, GFFList):
                container = container.at(int(step.name))

        if container is None:
            return None

        field_type = container.what_type(label)
        return container, label, field_type


# endregion


class ModificationsGFF:
    def __init__(
        self,
        filename: str,
        replace_file: bool,
        modifiers: list[ModifyGFF] | None = None,
        destination: str | None = None,
    ) -> None:
        self.filename: str = filename
        self.replace_file: bool = replace_file
        self.destination: str = (
            destination if destination is not None else str(Path("Override", filename))
        )
        self.modifiers: list[ModifyGFF] = modifiers if modifiers is not None else []

    def apply(
        self,
        gff: GFF,
        memory: PatcherMemory,
        logger: PatchLogger,
    ) -> None:
        for change_field in self.modifiers:
            change_field.apply(gff.root, memory, logger)
