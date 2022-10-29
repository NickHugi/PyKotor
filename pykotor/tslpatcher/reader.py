import configparser
from typing import Dict, Optional

from pykotor.resource.formats.tlk import TLK, read_tlk
from pykotor.tslpatcher.config import PatcherConfig
from pykotor.tslpatcher.mods.tlk import ModifyTLK
from pykotor.tslpatcher.mods.twoda import ManipulateRow2DA, ChangeRow2DA, Target, TargetType, WarningException, AddRow2DA, \
    CopyRow2DA, AddColumn2DA, Modifications2DA


class ConfigReader:
    def __init__(self) -> None:
        self.ini = configparser.ConfigParser()
        self.config: Optional[PatcherConfig] = None
        self.append: TLK = TLK()

    def load(self, config: PatcherConfig) -> PatcherConfig:
        self.ini.optionxform = str
        self.ini.read(config.input_path + "/changes.ini")
        self.config = config

        self.append: TLK = read_tlk(config.input_path + "/append.tlk")

        self.load_stringref()
        self.load_2da()

        return self.config

    def load_stringref(self) -> None:
        stringrefs = dict(self.ini["TLKList"].items())
        for name, value in stringrefs.items():
            token_id = int(name[6:])
            append_index = int(value)
            entry = self.append.get(append_index)

            modifier = ModifyTLK(token_id, entry.text, entry.voiceover)
            self.config.patches_tlk.modifiers.append(modifier)

    def load_2da(self) -> None:
        files = dict(self.ini["2DAList"].items())

        for file in files.values():
            modification_ids = dict(self.ini[file].items())

            modificaitons = Modifications2DA(file)
            self.config.patches_2da.append(modificaitons)

            for key, modification_id in modification_ids.items():
                manipulation = self.discern_2da(key, modification_id, dict(self.ini[modification_id].items()))
                modificaitons.rows.append(manipulation)

    def discern_2da(self, key: str, identifier: str, modifiers: Dict[str, str]) -> ManipulateRow2DA:
        if key.startswith("ChangeRow"):
            manipulation = ChangeRow2DA(identifier, self.target_2da(modifiers), modifiers)
        elif key.startswith("AddRow"):
            manipulation = AddRow2DA()
            manipulation.identifier = identifier
            manipulation.exclusive_column = modifiers.pop("ExclusiveColumn", None)
            manipulation.modifiers = modifiers
        elif key.startswith("CopyRow"):
            manipulation = CopyRow2DA()
            manipulation.identifier = identifier
            manipulation.target = self.target_2da(modifiers)
            manipulation.exclusive_column = modifiers.pop("ExclusiveColumn", None)
            manipulation.modifiers = modifiers
        elif key.startswith("AddColumn"):
            manipulation = AddColumn2DA()
            manipulation.identifier = identifier
            manipulation.header = modifiers.pop("ColumnLabel")
            manipulation.default = modifiers.pop("DefaultValue")
            for modifier in modifiers:
                if modifier.startswith("I"):
                    manipulation.index_insert[int(modifier[1:])] = modifiers[modifier]
                elif modifier.startswith("L"):
                    manipulation.label_insert[modifier[1:]] = modifiers[modifier]
                elif modifier.startswith("2DAMEMORY"):
                    memory_index = int(modifier.replace("2DAMEMORY", ""))
                    manipulation.memory_saves[memory_index] = modifiers[modifier]
        else:
            raise WarningException()
        return manipulation

    def target_2da(self, modifiers: Dict[str, str]) -> Target:
        if "RowIndex" in modifiers:
            target = Target(TargetType.ROW_INDEX, int(modifiers.pop("RowIndex")))
        elif "RowLabel" in modifiers:
            target = Target(TargetType.ROW_LABEL, modifiers.pop("RowLabel"))
        elif "LabelIndex" in modifiers:
            target = Target(TargetType.LABEL_COLUMN, modifiers.pop("LabelIndex"))
        else:
            raise WarningException()

        return target
