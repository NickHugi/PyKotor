from configparser import ConfigParser
from typing import Dict, Optional, Union, Tuple

from pykotor.common.language import LocalizedString

from pykotor.common.misc import ResRef

from pykotor.common.geometry import Vector3, Vector4

from pykotor.resource.formats.gff import GFFFieldType, GFFStruct, GFFList
from pykotor.resource.formats.ssf import SSFSound
from pykotor.resource.formats.tlk import TLK, read_tlk
from pykotor.tools.misc import is_float, is_int
from pykotor.tslpatcher.config import PatcherConfig
from pykotor.tslpatcher.memory import NoTokenUsage, TokenUsage2DA, TokenUsageTLK
from pykotor.tslpatcher.mods.gff import ModificationsGFF, ModifyFieldGFF, AddFieldGFF, \
    LocalizedStringDelta, FieldValueConstant, FieldValue2DAMemory, FieldValueTLKMemory, FieldValue
from pykotor.tslpatcher.mods.install import InstallFolder, InstallFile
from pykotor.tslpatcher.mods.ssf import ModifySSF, ModificationsSSF
from pykotor.tslpatcher.mods.tlk import ModifyTLK
from pykotor.tslpatcher.mods.twoda import Modify2DA, ChangeRow2DA, Target, TargetType, WarningException, AddRow2DA, \
    CopyRow2DA, AddColumn2DA, Modifications2DA, RowValue2DAMemory, RowValueTLKMemory, RowValueHigh, RowValueRowIndex, \
    RowValueRowLabel, RowValueConstant, RowValueRowCell


class ConfigReader:
    def __init__(self, ini: ConfigParser, append: TLK) -> None:
        self.ini = ini
        self.append: TLK = append

        self.config: Optional[PatcherConfig] = None

    def load(self, config: PatcherConfig) -> PatcherConfig:
        self.config = config

        self.load_filelist()
        self.load_stringref()
        self.load_2da()
        self.load_ssf()
        self.load_gff()

        return self.config

    def load_filelist(self) -> None:
        folders_ini = dict(self.ini["InstallList"].items())
        for _, foldername in folders_ini.items():
            folder_install = InstallFolder(foldername)
            self.config.install_list.append(folder_install)

            files_ini = dict(self.ini[_].items())
            for __, filename in files_ini.items():
                file_install = InstallFile(filename, False)
                folder_install.files.append(file_install)

    def load_stringref(self) -> None:
        if "TLKList" not in self.ini:
            return

        stringrefs = dict(self.ini["TLKList"].items())

        for name, value in stringrefs.items():
            token_id = int(name[6:])
            append_index = int(value)
            entry = self.append.get(append_index)

            modifier = ModifyTLK(token_id, entry.text, entry.voiceover)
            self.config.patches_tlk.modifiers.append(modifier)

    def load_2da(self) -> None:
        if "2DAList" not in self.ini:
            return

        files = dict(self.ini["2DAList"].items())

        for file in files.values():
            modification_ids = dict(self.ini[file].items())

            modificaitons = Modifications2DA(file)
            self.config.patches_2da.append(modificaitons)

            for key, modification_id in modification_ids.items():
                manipulation = self.discern_2da(key, modification_id, dict(self.ini[modification_id].items()))
                modificaitons.modifiers.append(manipulation)

    def load_ssf(self) -> None:
        if "SSFList" not in self.ini:
            return

        configstr_to_ssfsound = {
            "Battlecry 1": SSFSound.BATTLE_CRY_1,
            "Battlecry 2": SSFSound.BATTLE_CRY_2,
            "Battlecry 3": SSFSound.BATTLE_CRY_3,
            "Battlecry 4": SSFSound.BATTLE_CRY_4,
            "Battlecry 5": SSFSound.BATTLE_CRY_5,
            "Battlecry 6": SSFSound.BATTLE_CRY_6,
            "Selected 1": SSFSound.SELECT_1,
            "Selected 2": SSFSound.SELECT_2,
            "Selected 3": SSFSound.SELECT_3,
            "Attack 1": SSFSound.ATTACK_GRUNT_1,
            "Attack 2": SSFSound.ATTACK_GRUNT_2,
            "Attack 3": SSFSound.ATTACK_GRUNT_3,
            "Pain 1": SSFSound.PAIN_GRUNT_1,
            "Pain 2": SSFSound.PAIN_GRUNT_2,
            "Low health": SSFSound.LOW_HEALTH,
            "Death": SSFSound.DEAD,
            "Critical hit": SSFSound.CRITICAL_HIT,
            "Target immune": SSFSound.TARGET_IMMUNE,
            "Place mine": SSFSound.LAY_MINE,
            "Disarm mine": SSFSound.DISARM_MINE,
            "Stealth on": SSFSound.BEGIN_STEALTH,
            "Search": SSFSound.BEGIN_SEARCH,
            "Pick lock start": SSFSound.BEGIN_UNLOCK,
            "Pick lock fail": SSFSound.UNLOCK_FAILED,
            "Pick lock done": SSFSound.UNLOCK_SUCCESS,
            "Leave party": SSFSound.SEPARATED_FROM_PARTY,
            "Rejoin party": SSFSound.REJOINED_PARTY,
            "Poisoned": SSFSound.POISONED,
        }

        files = dict(self.ini["SSFList"].items())

        for identifier, file in files.items():
            modifications_ini = dict(self.ini[file].items())
            replace = identifier.startswith("Replace")

            modificaitons = ModificationsSSF(file, replace)
            self.config.patches_ssf.append(modificaitons)

            for name, value in modifications_ini.items():
                if value.startswith("2DAMEMORY"):
                    token_id = int(value[9:])
                    value = TokenUsage2DA(token_id)
                elif value.startswith("StrRef"):
                    token_id = int(value[6:])
                    value = TokenUsageTLK(token_id)
                else:
                    value = NoTokenUsage(int(value))

                sound = configstr_to_ssfsound[name]
                modifier = ModifySSF(sound, value)
                modificaitons.modifiers.append(modifier)

    def load_gff(self) -> None:
        if "GFFList" not in self.ini:
            return

        files = dict(self.ini["GFFList"].items())

        for identifier, file in files.items():
            modifications_ini = dict(self.ini[file].items())
            replace = identifier.startswith("Replace")

            modificaitons = ModificationsGFF(file, replace)
            self.config.patches_gff.append(modificaitons)

            for name, value in modifications_ini.items():
                if name.lower() == "!destination":
                    modificaitons.destination = value
                elif name.lower() == "!replacefile":
                    modificaitons.replace_file = bool(int(value))
                elif name.lower() == "!filename":
                    modificaitons.filename = value
                elif name.lower().startswith("addfield"):
                    modifier = self.add_field_gff(value, dict(self.ini[value]))
                    modificaitons.modifiers.append(modifier)
                else:
                    modifier = self.modify_field_gff(name, value)
                    modificaitons.modifiers.append(modifier)

    #################
    def field_value_gff(self, raw_value: str) -> FieldValue:
        if raw_value.startswith("StrRef"):
            token_id = int(raw_value[6:])
            return FieldValueTLKMemory(token_id)
        elif raw_value.startswith("2DAMEMORY"):
            token_id = int(raw_value[9:])
            return FieldValueTLKMemory(token_id)
        else:
            return FieldValueConstant(int(raw_value))

    def modify_field_gff(self, name: str, string_value: str) -> ModifyFieldGFF:
        if string_value.startswith("2DAMEMORY"):
            token_id = int(string_value[9:])
            value = FieldValue2DAMemory(token_id)
        elif string_value.startswith("StrRef"):
            token_id = int(string_value[6:])
            value = FieldValueTLKMemory(token_id)
        elif is_int(string_value):
            value = FieldValueConstant(int(string_value))
        elif is_float(string_value):
            value = FieldValueConstant(float(string_value))
        elif string_value.count("|") == 2:
            components = string_value.split("|")
            value = FieldValueConstant(Vector3(*[float(x) for x in components]))
        elif string_value.count("|") == 3:
            components = string_value.split("|")
            value = FieldValueConstant(Vector4(*[float(x) for x in components]))
        else:
            value = FieldValueConstant(string_value)

        if "(strref)" in name:
            value = FieldValueConstant(LocalizedStringDelta(value))
            name = name[:name.index("(strref)")]
        elif "(lang" in name:
            substring_id = int(name[name.index("(lang")+5:-1])
            language, gender = LocalizedString.substring_pair(substring_id)
            locstring = LocalizedStringDelta()
            locstring.set(language, gender, string_value)
            value = FieldValueConstant(locstring)
            name = name[:name.index("(lang")]

        modifier = ModifyFieldGFF(name, value)
        return modifier

    def add_field_gff(self, identifier: str, ini_data: Dict[str, str], inside_list: bool = False) -> AddFieldGFF:
        fieldname_to_fieldtype = {
            "Byte": GFFFieldType.UInt8,
            "Char": GFFFieldType.Int8,
            "Word": GFFFieldType.UInt16,
            "Short": GFFFieldType.Int16,
            "DWORD": GFFFieldType.UInt32,
            "Int": GFFFieldType.Int32,
            #"DWord64": GFFFieldType.UInt64,
            #"Binary": GFFFieldType.Binary,
            "Int64": GFFFieldType.Int64,
            "Float": GFFFieldType.Single,
            "Double": GFFFieldType.Double,
            "ExoString": GFFFieldType.String,
            "ResRef": GFFFieldType.ResRef,
            "ExoLocString": GFFFieldType.LocalizedString,
            "Position": GFFFieldType.Vector3,
            "Orientation": GFFFieldType.Vector4,
            "Struct": GFFFieldType.Struct,
            "List": GFFFieldType.List,
        }

        field_type = fieldname_to_fieldtype[ini_data["FieldType"]]
        path = ini_data["Path"] if "Path" in ini_data else ""
        label = ini_data.get("Label")
        raw_value = ini_data.get("Value")

        if raw_value is not None and raw_value.startswith("2DAMEMORY"):
            token_id = int(raw_value[9:])
            value = FieldValue2DAMemory(token_id)
        elif raw_value is not None and raw_value.endswith("StrRef"):
            token_id = int(raw_value[6:])
            value = FieldValueTLKMemory(token_id)

        elif field_type.return_type() == int:
            value = FieldValueConstant(int(raw_value))
        elif field_type.return_type() == float:
            value = FieldValueConstant(float(raw_value))
        elif field_type.return_type() == str:
            value = FieldValueConstant(raw_value)
        elif field_type.return_type() == ResRef:
            value = FieldValueConstant(ResRef(raw_value))
        elif field_type.return_type() == LocalizedString:
            stringref = self.field_value_gff(ini_data["StrRef"])

            value = LocalizedStringDelta(stringref)
            for substring, text in ini_data.items():
                if not substring.startswith("lang"):
                    continue
                substring_id = int(substring[4:])
                language, gender = value.substring_pair(substring_id)
                value.set(language, gender, text)
            value = FieldValueConstant(value)
        elif field_type.return_type() == Vector3:
            components = [float(axis) for axis in raw_value.split("|")]
            value = FieldValueConstant(Vector3(*components))
        elif field_type.return_type() == Vector4:
            components = [float(axis) for axis in raw_value.split("|")]
            value = FieldValueConstant(Vector4(*components))
        elif field_type.return_type() == GFFList:
            value = FieldValueConstant(GFFList())
        elif field_type.return_type() == GFFStruct:
            struct_id = int(ini_data["TypeId"])
            value = FieldValueConstant(GFFStruct(struct_id))
        else:
            raise ValueError(field_type)

        # Get nested fields/struct
        nested_modifiers = []
        for key, x in ini_data.items():
            if not key.startswith("AddField"):
                continue

            is_list = field_type.return_type() == GFFList
            modifier = self.add_field_gff(x, dict(self.ini[x].items()), is_list)
            nested_modifiers.append(modifier)

        index_in_list_token = None
        for key, memvalue in ini_data.items():
            if key.startswith("2DAMEMORY") and memvalue == "ListIndex" and field_type.return_type() != GFFStruct:
                index_in_list_token = int(key[9:])

        modifier = AddFieldGFF(identifier, label, field_type, value, path, nested_modifiers, index_in_list_token)

        return modifier

    #################
    def discern_2da(self, key: str, identifier: str, modifiers: Dict[str, str]) -> Modify2DA:
        if key.startswith("ChangeRow"):
            target = self.target_2da(identifier, modifiers)
            cells, store_2da, store_tlk = self.cells_2da(identifier, modifiers)
            modification = ChangeRow2DA(identifier, target, cells, store_2da, store_tlk)
        elif key.startswith("AddRow"):
            exclusive_column = self.exclusive_column_2da(modifiers)
            row_label = self.row_label_2da(identifier, modifiers)
            cells, store_2da, store_tlk = self.cells_2da(identifier, modifiers)
            modification = AddRow2DA(identifier, exclusive_column, row_label, cells, store_2da, store_tlk)
        elif key.startswith("CopyRow"):
            target = self.target_2da(identifier, modifiers)
            exclusive_column = self.exclusive_column_2da(modifiers)
            row_label = self.row_label_2da(identifier, modifiers)
            cells, store_2da, store_tlk = self.cells_2da(identifier, modifiers)
            modification = CopyRow2DA(identifier, target, exclusive_column, row_label, cells, store_2da, store_tlk)
        elif key.startswith("AddColumn"):
            header = modifiers.pop("ColumnLabel")
            default = modifiers.pop("DefaultValue")
            default = default if default != "****" else ""
            index_insert, label_insert, store_2da = self.column_inserts_2da(identifier, modifiers)
            modification = AddColumn2DA(identifier, header, default, index_insert, label_insert, store_2da)
        else:
            raise WarningException()

        return modification

    def target_2da(self, identifier: str, modifiers: Dict[str, str]) -> Target:
        if "RowIndex" in modifiers:
            target = Target(TargetType.ROW_INDEX, int(modifiers["RowIndex"]))
            modifiers.pop("RowIndex")
        elif "RowLabel" in modifiers:
            target = Target(TargetType.ROW_LABEL, modifiers["RowLabel"])
            modifiers.pop("RowLabel")
        elif "LabelIndex" in modifiers:
            target = Target(TargetType.LABEL_COLUMN, modifiers["LabelIndex"])
            modifiers.pop("LabelIndex")
        else:
            raise WarningException("No line set to be modified for '{}'.".format(identifier))

        return target

    def exclusive_column_2da(self, modifiers: Dict[str, str]) -> Optional[str]:
        if "ExclusiveColumn" in modifiers:
            return modifiers.pop("ExclusiveColumn")
        return None

    def cells_2da(self, identifier: str, modifiers: Dict[str, str]) -> Tuple:
        cells = {}
        store_2da = {}
        store_tlk = {}

        for modifier, value in modifiers.items():
            is_store_2da = modifier.startswith("2DAMEMORY")
            is_store_tlk = modifier.startswith("StrRef")
            is_row_label = modifier == "RowLabel" or modifier == "NewRowLabel"

            if value.startswith("2DAMEMORY"):
                token_id = int(value[9:])
                row_value = RowValue2DAMemory(token_id)
            elif value.startswith("StrRef"):
                token_id = int(value[6:])
                row_value = RowValueTLKMemory(token_id)
            elif value == "high()":
                row_value = RowValueHigh(None) if modifier == "RowLabel" else RowValueHigh(value)
            elif value == "RowIndex":
                row_value = RowValueRowIndex()
            elif value == "RowLabel":
                row_value = RowValueRowLabel()
            elif is_store_2da or is_store_tlk:
                row_value = RowValueRowCell(value)
            else:
                row_value = RowValueConstant(value)

            if is_store_2da or is_store_tlk:
                token_id = int(modifier[9:]) if is_store_2da else int(modifier[6:])
                store = store_2da if is_store_2da else store_tlk
                store[token_id] = row_value
            elif is_row_label:
                ...
            else:
                cells[modifier] = row_value

        return cells, store_2da, store_tlk

    def row_label_2da(self, identifier: str, modifiers: Dict[str, str]) -> Optional[str]:
        if "RowLabel" in modifiers:
            return modifiers.pop("RowLabel")
        elif "NewRowLabel" in modifiers:
            return modifiers.pop("NewRowLabel")
        else:
            return None

    def column_inserts_2da(self, identifier: str, modifiers: Dict[str, str]) -> Tuple:
        index_insert = {}
        label_insert = {}
        store_2da = {}

        for modifier, value in modifiers.items():
            is_store_2da = value.startswith("2DAMEMORY")
            is_store_tlk = value.startswith("StrRef")

            if is_store_2da:
                token_id = int(value[9:])
                row_value = RowValue2DAMemory(token_id)
            elif is_store_tlk:
                token_id = int(value[6:])
                row_value = RowValueTLKMemory(token_id)
            else:
                row_value = RowValueConstant(value)

            if modifier.startswith("I"):
                index = int(modifier[1:])
                index_insert[index] = row_value
            elif modifier.startswith("L"):
                label = modifier[1:]
                label_insert[label] = row_value
            elif modifier.startswith("2DAMEMORY"):
                token_id = int(modifier[9:])
                store_2da[token_id] = value

        return index_insert, label_insert, store_2da
