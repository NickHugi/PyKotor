from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Any, Optional, Union, Tuple

from pykotor.common.language import LocalizedString

from pykotor.resource.formats.gff import GFF, GFFStruct, GFFList, GFFFieldType
from pykotor.tslpatcher.memory import PatcherMemory
from pykotor.tslpatcher.mods.twoda import WarningException


# TODO: 2DAMEMORY# as field path+label, store+save


class LocalizedStringDelta(LocalizedString):
    def __init__(self, stringref: Union[int, str, None] = None):
        super().__init__(0)
        self.stringref: Union[int, str, None] = stringref

    def apply(self, locstring: LocalizedString, memory: PatcherMemory) -> None:
        if isinstance(self.stringref, str) and self.stringref.startswith("2DAMEMORY"):
            token_id = int(self.stringref[9:])
            locstring.stringref = int(memory.memory_2da[token_id])
        if isinstance(self.stringref, str) and self.stringref.startswith("StrRef"):
            token_id = int(self.stringref[6:])
            locstring.stringref = int(memory.memory_str[token_id])
        elif isinstance(self.stringref, int):
            locstring.stringref = self.stringref

        for language, gender, text in self:
            locstring.set(language, gender, text)


class ModifyGFF(ABC):
    @abstractmethod
    def apply(self, container: Union[GFFStruct, GFFList], memory: PatcherMemory) -> None:
        ...

    def _determine_value(self, field_type: GFFFieldType, value: Any, memory: PatcherMemory) -> Any:
        if isinstance(value, str) and value.startswith("2DAMEMORY"):
            token_id = int(value[9:])
            value = memory.memory_2da[token_id]
            if field_type.return_type() == int:
                value = int(value)
        elif isinstance(value, str) and value.startswith("StrRef"):
            token_id = int(value[6:])
            value = memory.memory_str[token_id]
            if field_type.return_type() == str:
                value = str(value)

        return value


class AddFieldGFF(ModifyGFF):
    def __init__(self, identifier: str, label: str, field_type: GFFFieldType, value: Any, path: str = ""):
        self.identifier: str = identifier
        self.label: str = label
        self.field_type: GFFFieldType = field_type
        self.value: Any = value
        self.path: Optional[str] = path

        self.modifiers: List[ModifyGFF] = []

    def apply(self, container: Union[GFFStruct, GFFList], memory: PatcherMemory) -> None:
        container = self._navigate_containers(container, self.path)
        value = self._determine_value(self.field_type, self.value, memory)

        def set_locstring():
            original = LocalizedString(0)
            value.apply(original, memory)
            container.set_locstring(self.label, value)

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
            GFFFieldType.Struct: lambda: container.set_struct(self.label, value),
            GFFFieldType.List: lambda: container.set_list(self.label, value),
        }
        container = func_map[self.field_type]()

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


class AddStructToListGFF(ModifyGFF):
    """
    Add Struct to a List in the GFF file.

    Attributes:
        identifier: Unique identifier for this modifier.
        struct_id: The StructID for the Struct. If set to None it will use the index inside the list instead.
        path: Path to start from.
        index_to_token: The Token ID to store the index of the struct in the list. Set to None to not store anything.
    """

    def __init__(self, identifier: str, struct_id: Optional[int], path: str = "", index_to_token: Optional[int] = None):
        self.identifier: str = identifier
        self.struct_id: Optional[int] = struct_id
        self.modifiers: List[ModifyGFF] = []
        self.path: str = path

        self.index_to_token: Optional[int] = index_to_token

    def apply(self, container: Union[GFFStruct, GFFList], memory: PatcherMemory) -> None:
        container = self._navigate_containers(container, self.path)

        if not isinstance(container, GFFList):
            raise WarningException()

        struct_id = len(container) if self.struct_id is None else self.struct_id
        new_struct = container.add(struct_id)

        if self.index_to_token is not None:
            memory.memory_2da[self.index_to_token] = str(len(container) - 1)

        for add_field in self.modifiers:
            add_field.apply(new_struct, memory)

    def _navigate_containers(self, container: Union[GFFStruct, GFFList], path: str) -> Union[GFFStruct, GFFList]:
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
    def __init__(self, path: str, value: Any):
        self.path: str = path
        self.value: Any = value

    def apply(self, container: Union[GFFStruct, GFFList], memory: PatcherMemory) -> None:
        container, label, field_type = self._navigate_containers(container, self.path)
        value = self._determine_value(field_type, self.value, memory)

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

        for path in hierarchy:
            if isinstance(container, GFFStruct):
                container = container.acquire(path, None, (GFFStruct, GFFList))
            elif isinstance(container, GFFList):
                container = container.at(int(path))
            else:
                raise WarningException()

        field_type = container.what_type(label)
        return container, label, field_type


class ModificationsGFF:
    def __init__(self, filename: str, replace_file: bool, modifiers: List[ModifyGFF]):
        self.filename: str = filename
        self.replace_file: bool = replace_file
        self.modifiers: List[ModifyGFF] = modifiers

    def apply(self, gff: GFF, memory: PatcherMemory) -> None:
        for change_field in self.modifiers:
            change_field.apply(gff.root, memory)
