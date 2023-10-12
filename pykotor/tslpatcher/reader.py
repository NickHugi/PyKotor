from __future__ import annotations

from configparser import ConfigParser
from itertools import tee
from typing import TYPE_CHECKING

try:
    import chardet
except ImportError:
    chardet = None

from pykotor.common.geometry import Vector3, Vector4
from pykotor.common.language import LocalizedString
from pykotor.common.misc import ResRef
from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.gff import GFFFieldType, GFFList, GFFStruct
from pykotor.resource.formats.ssf import SSFSound
from pykotor.resource.formats.tlk import TLK, read_tlk
from pykotor.tools.misc import is_float, is_int
from pykotor.tools.path import CaseAwarePath, PureWindowsPath
from pykotor.tslpatcher.config import PatcherConfig, PatcherNamespace
from pykotor.tslpatcher.logger import PatchLogger
from pykotor.tslpatcher.memory import NoTokenUsage, TokenUsage2DA, TokenUsageTLK
from pykotor.tslpatcher.mods.gff import (
    AddFieldGFF,
    AddStructToListGFF,
    FieldValue,
    FieldValue2DAMemory,
    FieldValueConstant,
    FieldValueTLKMemory,
    LocalizedStringDelta,
    Memory2DAModifierGFF,
    ModificationsGFF,
    ModifyFieldGFF,
)
from pykotor.tslpatcher.mods.install import InstallFile, InstallFolder
from pykotor.tslpatcher.mods.nss import ModificationsNSS
from pykotor.tslpatcher.mods.ssf import ModificationsSSF, ModifySSF
from pykotor.tslpatcher.mods.tlk import ModifyTLK
from pykotor.tslpatcher.mods.twoda import (
    AddColumn2DA,
    AddRow2DA,
    ChangeRow2DA,
    CopyRow2DA,
    Modifications2DA,
    Modify2DA,
    RowValue,
    RowValue2DAMemory,
    RowValueConstant,
    RowValueHigh,
    RowValueRowCell,
    RowValueRowIndex,
    RowValueRowLabel,
    RowValueTLKMemory,
    Target,
    TargetType,
)

if TYPE_CHECKING:
    import os

    from pykotor.resource.formats.tlk.tlk_data import TLKEntry
    from pykotor.tslpatcher.mods.gff import ModifyGFF


class ConfigReader:
    def __init__(self, ini: ConfigParser, mod_path: os.PathLike | str, logger: PatchLogger | None = None) -> None:
        self.ini = ini
        self.mod_path: CaseAwarePath = CaseAwarePath(mod_path)
        self.config: PatcherConfig
        self.log = logger or PatchLogger()

    @classmethod
    def from_filepath(cls, file_path: os.PathLike | str, logger: PatchLogger | None = None) -> PatcherConfig:
        resolved_file_path = CaseAwarePath(file_path).resolve()

        ini = ConfigParser(
            delimiters=("="),
            allow_no_value=True,
            strict=False,
            interpolation=None,
        )
        ini.optionxform = lambda optionstr: optionstr  # use case sensitive keys

        ini_file_bytes = BinaryReader.load_file(resolved_file_path)
        encoding = "utf8"
        if chardet:
            encoding = chardet.detect(ini_file_bytes).get("encoding") or encoding
        ini_data: str | None = None
        try:
            ini_data = ini_file_bytes.decode(encoding)
        except UnicodeDecodeError:
            try:
                ini_data = ini_file_bytes.decode("cp1252")
            except UnicodeDecodeError:
                try:
                    ini_data = ini_file_bytes.decode("windows-1252")
                except UnicodeDecodeError:
                    print(f"Could not determine encoding of '{resolved_file_path.name}'. Attempting to force load...")
                    ini_data = ini_file_bytes.decode(errors="replace")
        ini.read_string(ini_data)

        config = PatcherConfig()
        return ConfigReader(ini, resolved_file_path, logger).load(config)

    def load(self, config: PatcherConfig) -> PatcherConfig:
        self.config = config

        self.log.add_note("Loading [Settings] from ini...")
        self.load_settings()
        self.log.add_note("Loading [TLKList] patches from ini...")
        self.load_tlk_list()
        self.log.add_note("Loading [InstallList] patches from ini...")
        self.load_filelist()
        self.log.add_note("Loading [2DAList] patches from ini...")
        self.load_2da()
        self.log.add_note("Loading [GFFList] patches from ini...")
        self.load_gff()
        self.log.add_note("Loading [CompileList] patches from ini...")
        self.load_nss()
        self.log.add_note("Loading [SSFList] patches from ini...")
        self.load_ssf()

        return self.config

    def load_settings(self) -> None:
        self.config.window_title = self.ini.get(
            "Settings",
            "WindowCaption",
            fallback="",
        )
        self.config.confirm_message = self.ini.get(
            "Settings",
            "ConfirmMessage",
            fallback="",
        )
        # Try to get the value and convert it to an integer
        lookup_game_number = self.ini.get("Settings", "LookupGameNumber", fallback=None)
        if lookup_game_number is not None:
            try:
                self.config.game_number = int(lookup_game_number)
            except ValueError:
                self.log.add_error(f"Invalid game number: '{lookup_game_number}' Could not determine the kotor game!")
        else:
            self.config.game_number = None
        self.config.required_file = self.ini.get("Settings", "Required", fallback=None)
        self.config.required_message = self.ini.get("Settings", "Required", fallback="")

    def load_filelist(self) -> None:
        if "InstallList" not in self.ini:
            return

        folders_ini = dict(self.ini["InstallList"].items())
        for key, foldername in folders_ini.items():
            if key not in self.ini:
                msg = f"The section [{key}] was not found in the ini, referenced by {key}={foldername} in [InstallList]"
                raise KeyError(msg)
            folder_install = InstallFolder(foldername)
            self.config.install_list.append(folder_install)

            files_ini = dict(self.ini[key].items())
            for key2, filename in files_ini.items():
                replace_existing = key2.lower().startswith("replace")
                file_install = InstallFile(filename, replace_existing)
                folder_install.files.append(file_install)

    def load_tlk_list(self) -> None:
        if "TLKList" not in self.ini:
            return

        tlk_list_edits = dict(self.ini["TLKList"].items())
        modifier_dict: dict[int, dict[str, str | ResRef]] = {}
        append_tlk_edits = None

        def load_tlk(tlk_path: CaseAwarePath) -> TLK:
            return read_tlk(tlk_path) if tlk_path.exists() else TLK()

        range_delims = [":", "-", "to"]

        def extract_range_parts(range_str: str) -> tuple[int, int | None]:
            if range_str.lower().startswith("strref") or range_str.lower().startswith("ignore"):
                range_str = range_str[6:]
            for delim in range_delims:
                if delim in range_str:
                    parts: list[str] = range_str.split(delim)
                    start = int(parts[0].strip()) if parts[0].strip() else 0
                    end = int(parts[1].strip()) if parts[1].strip() else None
                    return start, end
            return int(range_str), None

        def parse_range(range_str: str) -> range:
            start, end = extract_range_parts(range_str)
            if end is None:
                return range(int(start), int(start) + 1)
            if end < start:
                self.log.add_error(f"start of range {start} must be less than end of range {end}. Skipping...")
                return range(0)  # empty range
            return range(start, end + 1)

        tlk_list_ignored_indices: set[int] = set()

        def process_tlk_entries(
            tlk_data: TLK,
            modifications_ini_keys,
            modifications_ini_values,
            is_replacement,
        ):
            def append_modifier(token_id, text, voiceover, is_replacement):
                modifier = ModifyTLK(token_id, text, voiceover, is_replacement)
                self.config.patches_tlk.modifiers.append(modifier)

            for mod_key, mod_value in zip(
                modifications_ini_keys,
                modifications_ini_values,
            ):
                try:
                    change_indices = mod_key if isinstance(mod_key, range) else parse_range(str(mod_key))
                    value_range = parse_range(str(mod_value)) if not isinstance(mod_value, range) and mod_value != "" else mod_key

                    change_iter, value_iter = tee(change_indices)
                    value_iter = iter(value_range)

                    for mod_index in change_iter:
                        if mod_index in tlk_list_ignored_indices:
                            continue
                        token_id = next(value_iter)
                        entry: TLKEntry = tlk_data[token_id]
                        append_modifier(
                            mod_index,
                            entry.text,
                            entry.voiceover,
                            is_replacement,
                        )
                except ValueError as e:
                    self.log.add_error(f"Could not parse {mod_key}={mod_value}: {e}. Skipping...")

        for i in tlk_list_edits:
            try:
                if i.lower().startswith("ignore"):
                    tlk_list_ignored_indices.update(
                        parse_range(i[6:]),
                    )
            except ValueError as e:
                self.log.add_error(f"Could not parse ignore index {i}: {e}. Skipping...")

        for key, value in tlk_list_edits.items():
            try:
                key: str = key.lower()
                if key.startswith("ignore"):
                    continue
                if key.startswith("strref"):
                    # load append.tlk only if it's needed.
                    if append_tlk_edits is None:
                        append_tlk_edits = load_tlk(self.mod_path / "append.tlk")
                    if len(append_tlk_edits) == 0:
                        self.log.add_error(f"Could not find append.tlk on disk to perform modifier '{key}={value}'. Skipping...")
                        continue
                    strref_range = parse_range(key[6:])
                    token_id_range = parse_range(value)
                    process_tlk_entries(
                        append_tlk_edits,
                        strref_range,
                        token_id_range,
                        is_replacement=False,
                    )
                elif key.startswith("file"):
                    tlk_modifications_path: CaseAwarePath = self.mod_path / value
                    if value not in self.ini:
                        self.log.add_error(f"INI header for '{value}' referenced in TLKList key '{key}' not found. Skipping...")
                        continue
                    tlk_ini_edits = dict(self.ini[value].items())
                    modifications_tlk_data: TLK = load_tlk(tlk_modifications_path)
                    if len(modifications_tlk_data) == 0:
                        self.log.add_error(f"Could not find {value}.tlk on disk to perform modifier 'key=value'. Skipping...")
                        continue
                    process_tlk_entries(
                        modifications_tlk_data,
                        tlk_ini_edits.keys(),
                        tlk_ini_edits.values(),
                        is_replacement=True,
                    )
                elif "\\" in key or "/" in key:
                    delimiter = "\\" if "\\" in key else "/"
                    token_id_str, property_name = key.split(delimiter)
                    token_id = int(token_id_str)

                    if token_id not in modifier_dict:
                        modifier_dict[token_id] = {
                            "text": "",
                            "voiceover": "",
                        }

                    if property_name == "text":
                        modifier_dict[token_id]["text"] = value
                    elif property_name == "sound":
                        modifier_dict[token_id]["voiceover"] = ResRef(value)
                    else:
                        self.log.add_error(
                            f"Invalid TLKList syntax for key '{key}' value '{value}', expected 'sound' or 'text'. Skipping...",
                        )
                        continue

                    text = modifier_dict[token_id].get("text")
                    voiceover = modifier_dict[token_id].get("voiceover")

                    # TODO(th3w1zard1): allow optional voiceover.
                    if isinstance(text, str) and isinstance(voiceover, ResRef):
                        modifier = ModifyTLK(token_id, text, voiceover, is_replacement=True)
                        self.config.patches_tlk.modifiers.append(modifier)
                else:
                    self.log.add_error(f"Invalid syntax in TLKList: '{key}={value}'. Skipping...")
            except ValueError as e:
                self.log.add_error(f"Could not parse {key}={value}: {e}. Skipping...")

    def load_2da(self) -> None:
        if "2DAList" not in self.ini:
            return

        files = dict(self.ini["2DAList"].items())

        for identifier, file in files.items():
            if file not in self.ini:
                msg = f"The section [{file}] was not found in the ini, referenced by {identifier}={file} in [2DAList]"
                raise KeyError(msg)
            modification_ids = dict(self.ini[file].items())

            modifications = Modifications2DA(file)
            self.config.patches_2da.append(modifications)

            for key, modification_id in modification_ids.items():
                manipulation: Modify2DA | None = self.discern_2da(
                    key,
                    modification_id,
                    dict(self.ini[modification_id].items()),
                )
                if not manipulation:  # an error occured
                    continue
                modifications.modifiers.append(manipulation)

    def load_ssf(self) -> None:
        if "SSFList" not in self.ini:
            return

        configstr_to_ssfsound: dict[str, SSFSound] = {
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
            if file not in self.ini:
                msg = f"The section [{file}] was not found in the ini, referenced by {identifier}={file} in [SSFList]"
                raise KeyError(msg)
            modifications_ini = dict(self.ini[file].items())
            replace = identifier.startswith("Replace")

            modifications = ModificationsSSF(file, replace)
            self.config.patches_ssf.append(modifications)

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
                modifications.modifiers.append(modifier)

    def load_gff(self) -> None:
        if "GFFList" not in self.ini:
            return

        files = dict(self.ini["GFFList"].items())

        for identifier, file in files.items():
            if file not in self.ini:
                msg = f"The section [{file}] was not found in the ini, referenced by {identifier}={file} in [GFFList]"
                raise KeyError(msg)
            modifications_ini = dict(self.ini[file].items())
            replace = identifier.startswith("Replace")

            modifications = ModificationsGFF(file, replace)
            self.config.patches_gff.append(modifications)

            modifier: ModifyGFF | None = None
            for key, value in modifications_ini.items():
                if key == "!Destination":
                    modifications.destination = CaseAwarePath(value)
                elif key == "!ReplaceFile":
                    modifications.replace_file = bool(int(value))
                elif key.lower() in ["!filename", "!saveas"]:
                    modifications.filename = value
                elif key.startswith("AddField"):
                    modifier = self.add_field_gff(value, dict(self.ini[value]))
                    if modifier:  # if None, then an error occurred
                        modifications.modifiers.append(modifier)
                elif key.startswith("2DAMEMORY"):
                    modifier = Memory2DAModifierGFF(
                        file,
                        int(key[9:]),
                        PureWindowsPath(""),
                    )
                    modifications.modifiers.append(modifier)
                else:
                    modifier = self.modify_field_gff(key, value)
                    modifications.modifiers.append(modifier)

    def load_nss(self) -> None:
        if "CompileList" not in self.ini:
            return

        files = dict(self.ini["CompileList"].items())
        destination = files.pop("!Destination", None)

        for identifier, file in files.items():
            replace = identifier.startswith("Replace")
            modifications = ModificationsNSS(file, replace)
            self.config.patches_nss.append(modifications)

            if destination is not None:
                modifications.destination = destination

    #################

    def field_value_gff(self, raw_value: str) -> FieldValue:
        if raw_value.startswith("StrRef"):
            token_id = int(raw_value[6:])
            return FieldValueTLKMemory(token_id)
        if raw_value.startswith("2DAMEMORY"):
            token_id = int(raw_value[9:])
            return FieldValueTLKMemory(token_id)
        return FieldValueConstant(int(raw_value))

    def modify_field_gff(self, key: str, string_value: str) -> ModifyFieldGFF:
        value = None
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
            value = FieldValueConstant(
                string_value.replace("<#LF#>", "\n").replace("<#CR#>", "\r"),
            )

        if "(strref)" in key:
            value = FieldValueConstant(LocalizedStringDelta(value))
            key = key[: key.index("(strref)")]
        elif "(lang" in key:
            substring_id = int(key[key.index("(lang") + 5 : -1])
            language, gender = LocalizedString.substring_pair(substring_id)
            locstring = LocalizedStringDelta()
            locstring.set_data(language, gender, string_value)
            value = FieldValueConstant(locstring)
            key = key[: key.index("(lang")]
        elif key.startswith("2DAMEMORY"):
            if value != "!FieldPath":
                msg = f"Cannot assign {value} to 2DAMEMORY here, GFFList only supports !FieldPath"
                raise ValueError(msg)
            value = FieldValueConstant(PureWindowsPath(""))  # no path at the root

        return ModifyFieldGFF(PureWindowsPath(key), value)

    def add_field_gff(
        self,
        identifier: str,
        ini_data: dict[str, str],
        inside_list: bool = False,
        current_path: PureWindowsPath | None = None,
    ) -> ModifyGFF:  # sourcery skip: extract-method, remove-unreachable-code
        fieldname_to_fieldtype = {
            "Byte": GFFFieldType.UInt8,
            "Char": GFFFieldType.Int8,
            "Word": GFFFieldType.UInt16,
            "Short": GFFFieldType.Int16,
            "DWORD": GFFFieldType.UInt32,
            "Int": GFFFieldType.Int32,
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

        field_type: GFFFieldType = fieldname_to_fieldtype[ini_data["FieldType"]]
        label: str = ini_data["Label"].strip()
        raw_path: str = ini_data.get("Path", "").strip()
        raw_value: str | None = ini_data.get("Value")
        value: FieldValue | LocalizedStringDelta | None = None
        struct_id = 0

        path: PureWindowsPath = PureWindowsPath(raw_path)
        path = path if path.name else (current_path or PureWindowsPath(""))

        if raw_value is None:
            if field_type.return_type() == LocalizedString:
                stringref = self.field_value_gff(ini_data["StrRef"])

                value = LocalizedStringDelta(stringref)
                for substring, text in ini_data.items():
                    if not substring.startswith("lang"):
                        continue
                    substring_id = int(substring[4:])
                    language, gender = value.substring_pair(substring_id)
                    formatted_text = text.replace("<#LF#>", "\n").replace("<#CR#>", "\r")
                    value.set_data(language, gender, formatted_text)
                value = FieldValueConstant(value)
            elif field_type.return_type() == GFFList:
                value = FieldValueConstant(GFFList())
            elif field_type.return_type() == GFFStruct:
                raw_struct_id = ini_data["TypeId"].strip()
                if raw_struct_id and is_int(raw_struct_id):
                    struct_id = int(raw_struct_id)
                elif raw_struct_id:
                    self.log.add_error(
                        f"Invalid struct id: expected int but got '{raw_struct_id}' in '{identifier}'. Using default of 0",
                    )
                value = FieldValueConstant(GFFStruct(struct_id))
                path /= ">>##INDEXINLIST##<<"
            else:
                msg = (
                    f"Could not find valid field return type in '{identifier}' matching field type '{field_type}' in this context"
                )
                raise ValueError(msg)
        elif raw_value.startswith("2DAMEMORY"):
            token_id = int(raw_value[9:])
            value = FieldValue2DAMemory(token_id)
        elif raw_value.endswith("StrRef"):
            token_id = int(raw_value[6:])
            value = FieldValueTLKMemory(token_id)

        elif field_type.return_type() == int:
            value = FieldValueConstant(int(raw_value))
        elif field_type.return_type() == float:
            # Replace comma with dot for decimal separator to match TSLPatcher syntax.
            value = FieldValueConstant(float(raw_value.replace(",", ".")))
        elif field_type.return_type() == str:
            value = FieldValueConstant(
                raw_value.replace("<#LF#>", "\n").replace("<#CR#>", "\r"),
            )
        elif field_type.return_type() == ResRef:
            value = FieldValueConstant(ResRef(raw_value))
        elif field_type.return_type() == Vector3:
            # Replace comma with dot for decimal separator to match TSLPatcher syntax.
            components = [float(axis.replace(",", ".")) for axis in raw_value.split("|")]
            value = FieldValueConstant(Vector3(*components))
        elif field_type.return_type() == Vector4:
            # Replace comma with dot for decimal separator to match TSLPatcher syntax.
            components = [float(axis.replace(",", ".")) for axis in raw_value.split("|")]
            value = FieldValueConstant(Vector4(*components))
        else:
            msg = f"Could not parse fieldtype '{field_type}' identifier '{identifier}' value '{value}'."
            raise ValueError(msg)

        modifiers: list[ModifyGFF] = []

        index_in_list_token = None
        for key, x in ini_data.items():
            if key.startswith("2DAMEMORY"):
                if x == "ListIndex":
                    index_in_list_token = int(key[9:])
                elif x == "!FieldPath":
                    modifier = Memory2DAModifierGFF(
                        identifier,
                        int(key[9:]),
                        path,
                    )
                    modifiers.insert(0, modifier)
            if key.startswith("AddField"):
                nested_ini = dict(self.ini[x].items())
                nested_modifier: ModifyGFF | None = self.add_field_gff(
                    x,
                    nested_ini,
                    inside_list=field_type.return_type() is GFFList,
                    current_path=path / label,
                )
                if nested_modifier:  # if none, an error occured.
                    modifiers.append(nested_modifier)

        # If current field is a struct inside a list, check inside_list OR no label defined.
        if not label.strip() and field_type.return_type() is GFFStruct:
            return AddStructToListGFF(
                identifier,
                struct_id,
                value,
                path,
                index_in_list_token,
                modifiers,
            )

        return AddFieldGFF(
            identifier,
            label,
            field_type,
            value,
            path,
            modifiers,
        )

    #################
    def discern_2da(
        self,
        key: str,
        identifier: str,
        modifiers: dict[str, str],
    ) -> Modify2DA | None:
        modification = None
        if key.startswith("ChangeRow"):
            target = self.target_2da(identifier, modifiers)
            if target is None:
                return None
            cells, store_2da, store_tlk = self.cells_2da(identifier, modifiers)
            modification = ChangeRow2DA(identifier, target, cells, store_2da, store_tlk)
        elif key.startswith("AddRow"):
            exclusive_column = self.exclusive_column_2da(modifiers)
            row_label = self.row_label_2da(identifier, modifiers)
            cells, store_2da, store_tlk = self.cells_2da(identifier, modifiers)
            modification = AddRow2DA(
                identifier,
                exclusive_column,
                row_label,
                cells,
                store_2da,
                store_tlk,
            )
        elif key.startswith("CopyRow"):
            target = self.target_2da(identifier, modifiers)
            if not target:
                return None
            exclusive_column = self.exclusive_column_2da(modifiers)
            row_label = self.row_label_2da(identifier, modifiers)
            cells, store_2da, store_tlk = self.cells_2da(identifier, modifiers)
            modification = CopyRow2DA(
                identifier,
                target,
                exclusive_column,
                row_label,
                cells,
                store_2da,
                store_tlk,
            )
        elif key.startswith("AddColumn"):
            header = modifiers.pop("ColumnLabel")
            default = modifiers.pop("DefaultValue")
            default = default if default != "****" else ""
            index_insert, label_insert, store_2da = self.column_inserts_2da(
                identifier,
                modifiers,
            )
            modification = AddColumn2DA(
                identifier,
                header,
                default,
                index_insert,
                label_insert,
                store_2da,
            )
        else:
            self.log.add_error(
                f"Could not parse key '{key}', expecting one of ['ChangeRow', 'AddColumn', 'AddRow', 'CopyRow']. Skipping...",
            )

        return modification

    def target_2da(self, identifier: str, modifiers: dict[str, str]) -> Target | None:
        target: Target | None = None
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
            self.log.add_warning(f"No line set to be modified for '{identifier}'.")

        return target

    def exclusive_column_2da(self, modifiers: dict[str, str]) -> str | None:
        if "ExclusiveColumn" in modifiers:
            return modifiers.pop("ExclusiveColumn")
        return None

    def cells_2da(
        self,
        identifier: str,
        modifiers: dict[str, str],
    ) -> tuple[dict[str, RowValue], dict[int, RowValue], dict[int, RowValue]]:
        cells: dict[str, RowValue] = {}
        store_2da: dict[int, RowValue] = {}
        store_tlk: dict[int, RowValue] = {}

        for modifier, value in modifiers.items():
            is_store_2da = modifier.startswith("2DAMEMORY")
            is_store_tlk = modifier.startswith("StrRef")
            is_row_label = modifier in ["RowLabel", "NewRowLabel"]

            row_value = None
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
            elif value == "****":
                row_value = RowValueConstant("")
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

    def row_label_2da(self, identifier: str, modifiers: dict[str, str]) -> str | None:
        if "RowLabel" in modifiers:
            return modifiers.pop("RowLabel")
        if "NewRowLabel" in modifiers:
            return modifiers.pop("NewRowLabel")
        return None

    def column_inserts_2da(
        self,
        identifier: str,
        modifiers: dict[str, str],
    ) -> tuple[dict[int, RowValue], dict[str, RowValue], dict[int, str]]:
        index_insert: dict[int, RowValue] = {}
        label_insert: dict[str, RowValue] = {}
        store_2da: dict[int, str] = {}

        for modifier, value in modifiers.items():
            is_store_2da = value.startswith("2DAMEMORY")
            is_store_tlk = value.startswith("StrRef")

            row_value: RowValue | None = None
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


# The `NamespaceReader` class is responsible for reading and loading namespaces from the namespaces.ini file.
class NamespaceReader:
    def __init__(self, ini: ConfigParser):
        self.ini = ini
        self.namespaces: list[PatcherNamespace] = []

    @classmethod
    def from_filepath(cls, path: os.PathLike | str) -> list[PatcherNamespace]:
        ini = ConfigParser(
            delimiters=("="),
            allow_no_value=True,
            strict=False,
            interpolation=None,
        )
        ini.optionxform = lambda optionstr: optionstr.lower()  # use case sensitive keys

        ini_file_bytes = BinaryReader.load_file(path)
        encoding = (chardet.detect(ini_file_bytes) or {}).get("encoding") if chardet else None

        if encoding is not None:
            ini.read_string(ini_file_bytes.decode(encoding))

        if encoding is None:
            ini_data: str | None = None
            try:
                ini_data = ini_file_bytes.decode()
            except UnicodeDecodeError:
                try:
                    ini_data = ini_file_bytes.decode("cp1252")
                except UnicodeDecodeError:
                    ini_data = ini_file_bytes.decode(errors="replace")
            ini.read_string(ini_data)

        return NamespaceReader(ini).load()

    def load(self) -> list[PatcherNamespace]:  # Case-insensitive access to section
        section_key = next((section for section in self.ini.sections() if section.lower() == "namespaces"), None)
        if section_key is None:
            msg = "'namespaces' section not found in INI file."
            raise KeyError(msg)
        namespace_ids = dict(self.ini[section_key].items()).values()
        namespaces: list[PatcherNamespace] = []

        for namespace_id in namespace_ids:
            # Case-insensitive access to namespace_id
            namespace_section_key = next(
                (section for section in self.ini.sections() if section.lower() == namespace_id.lower()),
                None,
            )
            if namespace_section_key is None:
                msg = f"'{namespace_id}' section not found in INI file."
                raise KeyError(msg)

            namespace = PatcherNamespace()
            namespace.namespace_id = namespace_section_key
            namespace.ini_filename = self.ini[namespace_section_key]["IniName"]
            namespace.info_filename = self.ini[namespace_section_key]["InfoName"]
            namespace.data_folderpath = self.ini[namespace_section_key].get("DataPath")
            namespace.name = self.ini[namespace_section_key].get("Name")
            namespace.description = self.ini[namespace_section_key].get("Description")
            namespaces.append(namespace)

        return namespaces
