from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Any, Optional, Union, Tuple

from pykotor.common.language import LocalizedString
from pykotor.common.misc import ResRef

from pykotor.resource.formats.gff import GFF, GFFStruct, GFFList, GFFFieldType
from pykotor.tslpatcher.memory import PatcherMemory
from pykotor.tslpatcher.mods.twoda import WarningException


# TODO: 2DAMEMORY# as field path+label, store+save


class LocalizedStringDelta(LocalizedString):
    def __init__(self, stringref: Optional[FieldValue] = None):
        super().__init__(0)
        self.stringref: Optional[FieldValue] = stringref

    def apply(self, locstring: LocalizedString, memory: PatcherMemory) -> None:
        if self.stringref is not None:
            locstring.stringref = self.stringref.value(memory, GFFFieldType.UInt32)
        for language, gender, text in self:
            locstring.set(language, gender, text)


class ModifyGFF(ABC):
    @abstractmethod
    def apply(self, container: Union[GFFStruct, GFFList], memory: PatcherMemory) -> None:
        ...


# region Value Returners
class FieldValue(ABC):
    @abstractmethod
    def value(self, memory: PatcherMemory, field_type: GFFFieldType) -> Any:
        ...

    def validate(self, value: Any, field_type: GFFFieldType) -> Any:
        if field_type == GFFFieldType.ResRef and not isinstance(value, ResRef):
            value = ResRef(str(value))
        if field_type == GFFFieldType.String and not isinstance(value, str):
            value = str(value)
        if field_type.return_type() == int and isinstance(value, str):
            value = int(value)
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


class AddFieldGFF(ModifyGFF):
    def __init__(self, identifier: str, label: str, field_type: GFFFieldType, value: FieldValue, path: str = "", modifiers: List[ModifyGFF] = None, index_to_list_token: Optional[int] = None):
        self.identifier: str = identifier
        self.label: str = label
        self.field_type: GFFFieldType = field_type
        self.value: FieldValue = value
        self.path: Optional[str] = path
        self.index_to_list_token: Optional[int] = index_to_list_token

        self.modifiers: List[ModifyGFF] = [] if modifiers is None else modifiers

    def apply(self, container: Union[GFFStruct, GFFList], memory: PatcherMemory) -> None:
        container = self._navigate_containers(container, self.path)
        value = self.value.value(memory, self.field_type)

        def set_locstring():
            original = LocalizedString(0)
            value.apply(original, memory)
            container.set_locstring(self.label, original)

        def set_struct():
            if isinstance(container, GFFStruct):
                return container.set_struct(self.label, value)
            elif isinstance(container, GFFList):
                return container.add(value.struct_id)

        def set_list():
            return container.set_list(self.label, value)

        func_map = {
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
            GFFFieldType.LocalizedString: lambda: set_locstring(),
            GFFFieldType.Vector3: lambda: container.set_vector3(self.label, value),
            GFFFieldType.Vector4: lambda: container.set_vector4(self.label, value),
            GFFFieldType.Struct: lambda: set_struct(),
            GFFFieldType.List: lambda: set_list(),
        }
        container = func_map[self.field_type]()

        if self.index_to_list_token is not None and isinstance(container, GFFList):
            memory.memory_2da[self.index_to_list_token] = str(len(container) - 1)

        if container is None and self.modifiers:
            raise WarningException()

        for add_field in self.modifiers:
            add_field.apply(container, memory)

    def _navigate_containers(self, container: Union[GFFStruct, GFFList], path: str) -> GFFStruct:
        hierarchy = [container for container in path.split("\\") if container != ""]

        for path in hierarchy:
            if isinstance(container, GFFStruct):
                container = container.acquire(path, None, (GFFStruct, GFFList))
            elif isinstance(container, GFFList):
                container = container.at(int(path))
            else:
                raise WarningException()

        return container


class ModifyFieldGFF(ModifyGFF):
    def __init__(self, path: str, value: FieldValue):
        self.path: str = path
        self.value: FieldValue = value

    def apply(self, container: Union[GFFStruct, GFFList], memory: PatcherMemory) -> None:
        container, label, field_type = self._navigate_containers(container, self.path)
        value = self.value.value(memory, field_type)

        def set_locstring():
            if container.exists(label):
                original = container.get_locstring(label)
                value.apply(original, memory)
                container.set_locstring(label, original)
            else:
                container.set_locstring(label, value)

        func_map = {
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
            GFFFieldType.LocalizedString: lambda: set_locstring(),
            GFFFieldType.Vector3: lambda: container.set_vector3(label, value),
            GFFFieldType.Vector4: lambda: container.set_vector4(label, value),
        }
        func_map[field_type]()

    def _navigate_containers(self, container: Union[GFFStruct, GFFList], path: str) -> Tuple[GFFStruct, str, GFFFieldType]:
        hierarchy, label = path.split("\\")[:-1], path.split("\\")[-1:][0]

        for step in hierarchy:
            if isinstance(container, GFFStruct):
                container = container.acquire(step, None, (GFFStruct, GFFList))
            elif isinstance(container, GFFList):
                container = container.at(int(step))
            else:
                raise WarningException()

        field_type = container.what_type(label)
        return container, label, field_type


class ModificationsGFF:
    def __init__(self, filename: str, replace_file: bool, modifiers: List[ModifyGFF] = None, destination: str = None):
        self.filename: str = filename
        self.replace_file: bool = replace_file
        self.destination: str = destination if destination is not None else "/override/"+filename
        self.modifiers: List[ModifyGFF] = modifiers if modifiers is not None else []

    def apply(self, gff: GFF, memory: PatcherMemory) -> None:
        for change_field in self.modifiers:
            change_field.apply(gff.root, memory)
