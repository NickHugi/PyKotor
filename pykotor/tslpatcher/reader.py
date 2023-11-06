from __future__ import annotations

from configparser import ConfigParser
from itertools import tee
from typing import TYPE_CHECKING

from pykotor.common.geometry import Vector3, Vector4
from pykotor.common.language import LocalizedString
from pykotor.common.misc import CaseInsensitiveDict, ResRef, decode_bytes_with_fallbacks
from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.gff import GFFFieldType, GFFList, GFFStruct
from pykotor.resource.formats.ssf import SSFSound
from pykotor.resource.formats.tlk import TLK, read_tlk
from pykotor.tools.misc import is_float, is_int
from pykotor.tools.path import CaseAwarePath, Path, PureWindowsPath
from pykotor.tslpatcher.config import PatcherConfig, PatcherNamespace
from pykotor.tslpatcher.logger import PatchLogger
from pykotor.tslpatcher.memory import (
    NoTokenUsage,
    TokenUsage,
    TokenUsage2DA,
    TokenUsageTLK,
)
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

SECTION_NOT_FOUND_ERROR: str = "The [{}] section was not found in the ini, referenced by '{}={}' in [{}]"

class ConfigReader:
    def __init__(self, ini: ConfigParser, mod_path: os.PathLike | str, logger: PatchLogger | None = None) -> None:
        self.ini = ini
        self.mod_path: CaseAwarePath = mod_path if isinstance(mod_path, CaseAwarePath) else CaseAwarePath(mod_path)
        self.config: PatcherConfig
        self.log = logger or PatchLogger()

    @classmethod
    def from_filepath(cls, file_path: os.PathLike | str, logger: PatchLogger | None = None) -> PatcherConfig:
        resolved_file_path = (file_path if isinstance(file_path, Path) else Path(file_path)).resolve()

        ini = ConfigParser(
            delimiters=("="),
            allow_no_value=True,
            strict=False,
            interpolation=None,
        )
        # use case-sensitive keys
        ini.optionxform = lambda optionstr: optionstr  #  type: ignore[method-assign]

        ini_file_bytes = BinaryReader.load_file(resolved_file_path)
        ini_text: str | None = decode_bytes_with_fallbacks(ini_file_bytes)
        ini.read_string(ini_text)

        config = PatcherConfig()
        return ConfigReader(ini, resolved_file_path, logger).load(config)

    def load(self, config: PatcherConfig) -> PatcherConfig:
        self.config = config

        self.load_settings()
        self.load_tlk_list()
        self.load_filelist()
        self.load_2da()
        self.load_gff()
        self.load_nss()
        self.load_ssf()

        # check for unsupported [HACKList]
        hacklist_found = self.get_section_name("HACKList")
        if hacklist_found:
            msg = "TSLPatcher's [HACKList] section is not currently supported."
            raise NotImplementedError(msg)

        return self.config

    def get_section_name(self, section_name: str):
        return next(
            (
                section
                for section in self.ini.sections()
                if section.lower() == section_name.lower()
            ),
            None,
        )

    def load_settings(self) -> None:
        settings_section = self.get_section_name("settings")
        if not settings_section:
            self.log.add_warning("[Settings] section missing from ini.")
            return

        self.log.add_note("Loading [Settings] section from ini...")
        settings_ini = CaseInsensitiveDict(self.ini[settings_section].items())
        self.config.window_title = settings_ini.get("WindowCaption", "")
        self.config.confirm_message = settings_ini.get("ConfirmMessage", "")
        lookup_game_number = settings_ini.get("LookupGameNumber")
        if lookup_game_number:
            # Try to get the value and convert it to an integer
            try:
                self.config.game_number = int(lookup_game_number)
            except ValueError as e:
                msg = f"Invalid: 'LookupGameNumber={lookup_game_number}' - cannot start install."
                raise ValueError(msg) from e
        else:
            self.config.game_number = None
        self.config.required_file = settings_ini.get("Required")
        self.config.required_message = settings_ini.get("RequiredMsg", "")

    def load_filelist(self) -> None:  # TODO: !SourceFile, !SaveAs, !Filename
        install_list_section = self.get_section_name("installlist")
        if not install_list_section:
            self.log.add_warning("[InstallList] section missing from ini.")
            return

        self.log.add_note("Loading [InstallList] patches from ini...")
        for key, foldername in self.ini[install_list_section].items():
            foldername_section = self.get_section_name(key)
            if foldername_section is None:
                raise KeyError(SECTION_NOT_FOUND_ERROR.format(foldername, key, foldername, install_list_section))
            folder_install = InstallFolder(foldername)
            self.config.install_list.append(folder_install)

            for key2, filename in self.ini[foldername_section].items():
                replace_existing = key2.lower().startswith("replace")
                file_install = InstallFile(filename, replace_existing)
                folder_install.files.append(file_install)

    def load_tlk_list(self) -> None:
        tlk_list_section = self.get_section_name("tlklist")
        if not tlk_list_section:
            self.log.add_warning("[TLKList] section missing from ini.")
            return

        self.log.add_note("Loading [TLKList] patches from ini...")
        tlk_list_edits = CaseInsensitiveDict(self.ini[tlk_list_section].items())

        sourcefile = tlk_list_edits.pop("!SourceFile", "append.tlk")
        sourcefile_f = tlk_list_edits.pop("!SourceFileF", "appendf.tlk")  # Polish only?  # noqa: F841

        modifier_dict: dict[int, dict[str, str | ResRef]] = {}
        range_delims: list[str] = [":", "-", "to"]
        append_tlk_edits: TLK | None = None
        syntax_error_caught = False

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
                msg = f"start of range '{start}' must be less than end of range '{end}'."
                raise ValueError(msg)
            return range(start, end + 1)

        tlk_list_ignored_indices: set[int] = set()

        def process_tlk_entries(
            tlk_data: TLK,
            dialog_tlk_keys,
            modifications_tlk_keys,
            is_replacement: bool,
        ) -> None:
            for mod_key, mod_value in zip(
                dialog_tlk_keys,
                modifications_tlk_keys,
            ):
                change_indices: range = mod_key if isinstance(mod_key, range) else parse_range(str(mod_key))
                value_range = parse_range(str(mod_value)) if not isinstance(mod_value, range) and mod_value != "" else mod_key

                change_iter, value_iter = tee(change_indices)
                value_iter = iter(value_range)

                for mod_index in change_iter:
                    if mod_index in tlk_list_ignored_indices:
                        continue
                    token_id: int = next(value_iter)
                    entry: TLKEntry = tlk_data[token_id]
                    modifier = ModifyTLK(mod_index, entry.text, entry.voiceover, is_replacement)
                    self.config.patches_tlk.modifiers.append(modifier)

        for i in tlk_list_edits:
            try:
                if i.lower().startswith("ignore"):
                    tlk_list_ignored_indices.update(parse_range(i[6:]))
            except ValueError as e:  # noqa: PERF203
                msg = f"Could not parse ignore index '{i}' for modifier '{i}={tlk_list_edits[i]}' in [TLKList]"
                raise ValueError(msg) from e

        for key, value in tlk_list_edits.items():
            lowercase_key: str = key.lower()
            replace_file = lowercase_key.startswith("replace")
            append_file = lowercase_key.startswith("append")
            try:
                if lowercase_key.startswith("ignore"):
                    continue
                if lowercase_key.startswith("strref"):
                    # load append.tlk only if it's needed.
                    if append_tlk_edits is None:
                        append_tlk_edits = read_tlk(self.mod_path / sourcefile)
                    if len(append_tlk_edits) == 0:
                        syntax_error_caught = True
                        msg = f"'append.tlk' in mod directory is empty, but is required to perform modifier '{key}={value}' in [TLKList]"
                        raise ValueError(msg)  # noqa: TRY301
                    strref_range = parse_range(lowercase_key[6:])
                    token_id_range = parse_range(value)
                    process_tlk_entries(
                        append_tlk_edits,
                        strref_range,
                        token_id_range,
                        is_replacement=False,
                    )
                elif replace_file or append_file:
                    next_section_name = self.get_section_name(value)
                    if not next_section_name:
                        syntax_error_caught = True
                        raise ValueError(SECTION_NOT_FOUND_ERROR.format(value, key, value, tlk_list_section))  # noqa: TRY301

                    tlk_modifications_path: CaseAwarePath = self.mod_path / value
                    modifications_tlk_data: TLK = read_tlk(tlk_modifications_path)
                    if len(modifications_tlk_data) == 0:
                        syntax_error_caught = True
                        msg = f"'{value}' file in mod directory is empty, but is required to perform modifier '{key}={value}' in [TLKList]"
                        raise ValueError(msg)  # noqa: TRY301

                    process_tlk_entries(
                        modifications_tlk_data,
                        self.ini[next_section_name].keys(),
                        self.ini[next_section_name].values(),
                        is_replacement=replace_file,
                    )
                elif "\\" in lowercase_key or "/" in lowercase_key:
                    delimiter = "\\" if "\\" in lowercase_key else "/"
                    token_id_str, property_name = lowercase_key.split(delimiter)
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
                        syntax_error_caught = True
                        msg = f"Invalid [TLKList] syntax: '{key}={value}'! Expected '{key}' to be one of ['Sound', 'Text']"
                        raise ValueError(msg)  # noqa: TRY301

                    text = modifier_dict[token_id].get("text")
                    voiceover = modifier_dict[token_id].get("voiceover", ResRef.from_blank())

                    if isinstance(text, str) and isinstance(voiceover, ResRef):
                        modifier = ModifyTLK(token_id, text, voiceover, is_replacement=True)
                        self.config.patches_tlk.modifiers.append(modifier)
                else:
                    syntax_error_caught = True
                    msg = f"Invalid syntax found in [TLKList] '{key}={value}'! Expected '{key}' to be one of ['File', 'StrRef']"
                    raise ValueError(msg)  # noqa: TRY301
            except ValueError as e:
                if syntax_error_caught:
                    raise
                msg = f"Could not parse '{key}={value}' in [TLKList]"
                raise ValueError(msg) from e

    def load_2da(self) -> None:
        twoda_list_section = self.get_section_name("2dalist")
        if not twoda_list_section:
            self.log.add_warning("[2DAList] section missing from ini.")
            return

        self.log.add_note("Loading [2DAList] patches from ini...")

        for identifier, file in self.ini[twoda_list_section].items():

            file_section = self.get_section_name(file)
            if not file_section:
                raise KeyError(SECTION_NOT_FOUND_ERROR.format(file, identifier, file, twoda_list_section))

            modifications = Modifications2DA(file)
            self.config.patches_2da.append(modifications)

            modification_ids = CaseInsensitiveDict(self.ini[file_section].items())
            for key, modification_id in modification_ids.items():
                ini_section_dict = CaseInsensitiveDict(self.ini[modification_id].items())
                manipulation: Modify2DA | None = self.discern_2da(
                    key,
                    modification_id,
                    ini_section_dict,
                )
                if not manipulation:  # TODO: Does this denote an error occurred? If so we should raise.
                    continue
                modifications.modifiers.append(manipulation)

    def load_ssf(self) -> None:
        ssf_list_section = self.get_section_name("ssflist")
        if not ssf_list_section:
            self.log.add_warning("[SSFList] section missing from ini.")
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

        self.log.add_note("Loading [SSFList] patches from ini...")

        for identifier, file in self.ini[ssf_list_section].items():
            ssf_file_section = self.get_section_name(file)
            if not ssf_file_section:
                raise KeyError(SECTION_NOT_FOUND_ERROR.format(file, identifier, file, ssf_list_section))

            replace = identifier.lower().startswith("replace")
            modifications = ModificationsSSF(file, replace)
            self.config.patches_ssf.append(modifications)

            for name, value in self.ini[ssf_file_section].items():
                new_value: TokenUsage
                if value.lower().startswith("2damemory"):
                    token_id = int(value[9:])
                    new_value = TokenUsage2DA(token_id)
                elif value.lower().startswith("strref"):
                    token_id = int(value[6:])
                    new_value = TokenUsageTLK(token_id)
                else:
                    new_value = NoTokenUsage(int(value))

                sound = configstr_to_ssfsound[name]
                modifier = ModifySSF(sound, new_value)
                modifications.modifiers.append(modifier)

    def load_gff(self) -> None:
        gff_list_section = self.get_section_name("gfflist")
        if not gff_list_section:
            self.log.add_warning("[GFFList] section missing from ini.")
            return

        self.log.add_note("Loading [GFFList] patches from ini...")

        for identifier, file in self.ini[gff_list_section].items():
            file_section_name = self.get_section_name(file)
            if not file_section_name:
                raise KeyError(SECTION_NOT_FOUND_ERROR.format(file, identifier, file, gff_list_section))

            replace = identifier.lower().startswith("replace")
            modifications = ModificationsGFF(file, replace)
            self.config.patches_gff.append(modifications)

            modifier: ModifyGFF | None = None
            file_section = self.ini[file_section_name]
            for key, value in file_section.items():
                lowercase_key = key.lower()
                if lowercase_key == "!destination":
                    modifications.destination = value
                elif lowercase_key == "!replacefile":
                    modifications.replace_file = bool(int(value))
                elif lowercase_key == "!sourcefile":
                    modifications.sourcefile = value
                elif lowercase_key in ["!filename", "!saveas"]:
                    modifications.saveas = value
                elif lowercase_key == "!overridetype":
                    modifications.override_type = value.lower()
                else:
                    if lowercase_key.startswith("addfield"):
                        next_gff_section = self.get_section_name(value)
                        if not next_gff_section:
                            raise KeyError(SECTION_NOT_FOUND_ERROR.format(value, key, value, file_section_name))

                        next_section_dict = CaseInsensitiveDict(self.ini[next_gff_section].items())
                        modifier = self.add_field_gff(next_gff_section, next_section_dict)
                    elif lowercase_key.startswith("2damemory"):
                        modifier = Memory2DAModifierGFF(
                            file,
                            int(key[9:]),
                            PureWindowsPath(""),
                        )
                    else:
                        modifier = self.modify_field_gff(file_section_name, key, value)

                    modifications.modifiers.append(modifier)

    def load_nss(self) -> None:
        compilelist_section = self.get_section_name("compilelist")
        if not compilelist_section:
            self.log.add_warning("[CompileList] section missing from ini.")
            return

        self.log.add_note("Loading [CompileList] patches from ini...")
        files = CaseInsensitiveDict(self.ini[compilelist_section].items())
        default_destination: str = files.pop("!DefaultDestination", "Override")

        for identifier, file in files.items():
            replace = identifier.lower().startswith("replace")
            optional_file_section_name = self.get_section_name(file)
            modifications = ModificationsNSS(file, replace)
            if optional_file_section_name is not None:
                file_ini_section = CaseInsensitiveDict(self.ini[optional_file_section_name].items())
                modifications.destination = file_ini_section.pop("!Destination", default_destination)
                modifications.saveas = file_ini_section.pop("!SaveAs", file_ini_section.pop("!Filename", modifications.saveas))
                modifications.replace_file = bool(file_ini_section.pop("!ReplaceFile", replace))
                modifications.sourcefile = file_ini_section.pop("!SourceFile", modifications.sourcefile)
                modifications.destination = file_ini_section.pop("!Destination", default_destination)
            self.config.patches_nss.append(modifications)

    #################

    def field_value_gff(self, raw_value: str) -> FieldValue:
        if raw_value.lower().startswith("strref"):
            token_id = int(raw_value[6:])
            return FieldValueTLKMemory(token_id)
        if raw_value.lower().startswith("2damemory"):
            token_id = int(raw_value[9:])
            return FieldValueTLKMemory(token_id)
        return FieldValueConstant(int(raw_value))

    def modify_field_gff(self, identifier: str, key: str, string_value: str) -> ModifyFieldGFF:
        value: FieldValue | None = None
        string_value_lower = string_value.lower()
        key_lower = key.lower()
        if string_value_lower.startswith("2damemory"):
            token_id = int(string_value[9:])
            value = FieldValue2DAMemory(token_id)
        elif string_value_lower.startswith("strref"):
            token_id = int(string_value[6:])
            value = FieldValueTLKMemory(token_id)
        elif is_int(string_value):
            value = FieldValueConstant(int(string_value))
        elif is_float(string_value):
            value = FieldValueConstant(float(string_value.replace(",", ".")))
        elif string_value.count("|") == 2:
            components = string_value.split("|")
            value = FieldValueConstant(Vector3(*(float(x.replace(",", ".")) for x in components)))
        elif string_value.count("|") == 3:
            components = string_value.split("|")
            value = FieldValueConstant(Vector4(*(float(x.replace(",", ".")) for x in components)))
        else:
            value = FieldValueConstant(string_value.replace("<#LF#>", "\n").replace("<#CR#>", "\r"))
        if "(strref)" in key_lower:
            value = FieldValueConstant(LocalizedStringDelta(value))
            key = key[: key_lower.index("(strref)")]
        elif "(lang" in key_lower:
            substring_id = int(key[key_lower.index("(lang") + 5 : -1])
            language, gender = LocalizedString.substring_pair(substring_id)
            locstring = LocalizedStringDelta()
            locstring.set_data(language, gender, string_value)
            value = FieldValueConstant(locstring)
            key = key[: key_lower.index("(lang")]
        elif key_lower.startswith("2damemory"):
            if string_value_lower != "!fieldpath" and not string_value_lower.startswith("2damemory"):
                msg = f"Cannot parse '{key}={value}' in [{identifier}]. GFFList only supports 2DAMEMORY#=!FieldPath assignments"
                raise ValueError(msg)
            value = FieldValueConstant(PureWindowsPath(""))  # no path at the root

        return ModifyFieldGFF(PureWindowsPath(key), value)

    def add_field_gff(
        self,
        identifier: str,
        ini_data: CaseInsensitiveDict,
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
        value: FieldValue | None = None
        text: str
        struct_id = 0

        # required
        field_type: GFFFieldType = fieldname_to_fieldtype[ini_data["FieldType"]]
        label: str = ini_data["Label"].strip()

        # situational/optional
        raw_path: str = ini_data.get("Path", "").strip()
        raw_value: str | None = ini_data.get("Value")

        # Handle current gff path
        path: PureWindowsPath = PureWindowsPath(raw_path)
        path = path if path.name else (current_path or PureWindowsPath(""))

        if raw_value is None:
            if field_type.return_type() == LocalizedString:
                stringref = self.field_value_gff(ini_data["StrRef"])

                l_string_delta = LocalizedStringDelta(stringref)
                for substring, text in ini_data.items():
                    if not substring.lower().startswith("lang"):
                        continue
                    substring_id = int(substring[4:])
                    language, gender = l_string_delta.substring_pair(substring_id)
                    formatted_text = text.replace("<#LF#>", "\n").replace("<#CR#>", "\r")
                    l_string_delta.set_data(language, gender, formatted_text)
                value = FieldValueConstant(l_string_delta)
            elif field_type.return_type() == GFFList:
                value = FieldValueConstant(GFFList())
            elif field_type.return_type() == GFFStruct:
                raw_struct_id = ini_data["TypeId"].strip()
                if raw_struct_id and is_int(raw_struct_id):
                    struct_id = int(raw_struct_id)
                elif raw_struct_id:
                    msg = f"Invalid struct id: expected int but got '{raw_struct_id}' in '[{identifier}]'"
                    raise ValueError(msg)
                value = FieldValueConstant(GFFStruct(struct_id))
                path /= ">>##INDEXINLIST##<<"  # see the check in mods/gff.py. Perhaps need to check if label is set, first?
            else:
                msg = f"Could not find valid field return type in [{identifier}] matching field type '{field_type}' in this context"
                raise ValueError(msg)
        elif raw_value.lower().startswith("2damemory"):
            token_id = int(raw_value[9:])
            value = FieldValue2DAMemory(token_id)
        elif raw_value.lower().endswith("strref"):  # TODO: see if this is necessary, seems unused. Perhaps needs to be 'StrRef\d+'? Or is this already handled elsewhere?
            token_id = int(raw_value[6:])
            value = FieldValueTLKMemory(token_id)
        elif field_type.return_type() == int:
            value = FieldValueConstant(int(raw_value))
        elif field_type.return_type() == float:
            # Replace comma with dot for decimal separator to match TSLPatcher syntax.
            value = FieldValueConstant(float(raw_value.replace(",", ".")))
        elif field_type.return_type() == str:
            value = FieldValueConstant(raw_value.replace("<#LF#>", "\n").replace("<#CR#>", "\r"))
        elif field_type.return_type() == ResRef:
            value = FieldValueConstant(ResRef(raw_value))
        elif field_type.return_type() == Vector3:
            # Replace comma with dot for decimal separator to match TSLPatcher syntax.
            components = (float(axis.replace(",", ".")) for axis in raw_value.split("|"))
            value = FieldValueConstant(Vector3(*components))
        elif field_type.return_type() == Vector4:
            # Replace comma with dot for decimal separator to match TSLPatcher syntax.
            components = (float(axis.replace(",", ".")) for axis in raw_value.split("|"))
            value = FieldValueConstant(Vector4(*components))
        else:
            msg = f"Could not parse fieldtype '{field_type}' in section [{identifier}]"
            raise ValueError(msg)

        modifiers: list[ModifyGFF] = []

        index_in_list_token = None
        lower_iterated_value: str
        for key, iterated_value in ini_data.items():
            lower_key: str = key.lower()
            lower_iterated_value = iterated_value.lower()
            if lower_key.startswith("2damemory"):
                if lower_iterated_value == "listindex":
                    index_in_list_token = int(key[9:])
                elif lower_iterated_value == "!fieldpath":
                    modifier = Memory2DAModifierGFF(
                        identifier,
                        int(key[9:]),
                        path,
                    )
                    modifiers.insert(0, modifier)
            if lower_key.startswith("addfield"):
                next_section_name: str | None = self.get_section_name(iterated_value)
                if not next_section_name:
                    raise KeyError(SECTION_NOT_FOUND_ERROR.format(iterated_value, key, iterated_value, identifier))
                next_nested_section = CaseInsensitiveDict(self.ini[next_section_name].items())
                nested_modifier: ModifyGFF = self.add_field_gff(
                    next_section_name,
                    next_nested_section,
                    current_path=path / label,
                )
                modifiers.append(nested_modifier)

        # Check if label unset to determine if current ini section is a struct inside a list.
        if not label and field_type.return_type() is GFFStruct:
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
        modifiers: CaseInsensitiveDict,
    ) -> Modify2DA | None:

        exclusive_column: str | None
        modification: Modify2DA | None = None
        lowercase_key = key.lower()

        if lowercase_key.startswith("changerow"):
            target = self.target_2da(identifier, modifiers)
            if target is None:
                return None
            cells, store_2da, store_tlk = self.cells_2da(identifier, modifiers)
            modification = ChangeRow2DA(identifier, target, cells, store_2da, store_tlk)
        elif lowercase_key.startswith("addrow"):
            exclusive_column = modifiers.pop("ExclusiveColumn")
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
        elif lowercase_key.startswith("copyrow"):
            target = self.target_2da(identifier, modifiers)
            if not target:
                return None
            exclusive_column = modifiers.pop("ExclusiveColumn")
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
        elif lowercase_key.startswith("addcolumn"):
            header = modifiers.pop("ColumnLabel")
            if header is None:
                msg = f"Missing 'ColumnLabel' in [{identifier}]"
                raise KeyError(msg)
            default = modifiers.pop("DefaultValue")
            if default is None:
                msg = f"Missing 'DefaultValue' in [{identifier}]"
                raise KeyError(msg)
            default = default if default != "****" else ""
            index_insert, label_insert, store_2da = self.column_inserts_2da(  # type: ignore[assignment]
                identifier,
                modifiers,
            )
            modification = AddColumn2DA(
                identifier,
                header,
                default,
                index_insert,
                label_insert,
                store_2da,  # type: ignore[arg-type]
            )
        else:
            msg = f"Could not parse key '{key}={identifier}', expecting one of ['ChangeRow=', 'AddColumn=', 'AddRow=', 'CopyRow=']"
            raise KeyError(msg)

        return modification

    def target_2da(self, identifier: str, modifiers: CaseInsensitiveDict) -> Target | None:
        def get_target(target_type: TargetType, key: str, is_int: bool = False) -> Target:
            value = modifiers.pop(key)
            if value is None:
                msg = f"'{key}' missing from [{identifier}] in ini."
                raise ValueError(msg)
            if is_int:
                value = int(value)
            return Target(target_type, value)

        if "RowIndex" in modifiers:
            return get_target(TargetType.ROW_INDEX, "RowIndex", is_int=True)
        if "RowLabel" in modifiers: 
            return get_target(TargetType.ROW_LABEL, "RowLabel")
        if "LabelIndex" in modifiers:
            return get_target(TargetType.LABEL_COLUMN, "LabelIndex")

        self.log.add_warning(f"No line set to be modified in [{identifier}].")
        return None

    def cells_2da(
        self,
        identifier: str,
        modifiers: CaseInsensitiveDict[str],
    ) -> tuple[dict[str, RowValue], dict[int, RowValue], dict[int, RowValue]]:

        cells: dict[str, RowValue] = {}
        store_2da: dict[int, RowValue] = {}
        store_tlk: dict[int, RowValue] = {}

        for modifier, value in modifiers.items():
            modifier_lowercase = modifier.lower().strip()
            value_lowercase = value.lower()
            is_store_2da = modifier_lowercase.startswith("2damemory")
            is_store_tlk = modifier_lowercase.startswith("strref") and len(modifier_lowercase) > 6  # noqa: PLR2004
            is_row_label = modifier_lowercase in ["rowlabel", "newrowlabel"]

            row_value: RowValue | None = None
            if value_lowercase.startswith("2damemory"):
                token_id = int(value[9:])
                row_value = RowValue2DAMemory(token_id)
            elif value_lowercase.startswith("strref"):
                token_id = int(value[6:])
                row_value = RowValueTLKMemory(token_id)
            elif value_lowercase == "high()":
                row_value = RowValueHigh(None) if modifier == "rowlabel" else RowValueHigh(value)
            elif value_lowercase == "rowindex":
                row_value = RowValueRowIndex()
            elif value_lowercase == "rowlabel":
                row_value = RowValueRowLabel()
            elif is_store_2da or is_store_tlk:
                row_value = RowValueRowCell(value)
            elif value == "****":
                row_value = RowValueConstant("")
            else:
                row_value = RowValueConstant(value)

            if is_store_2da:
                token_id = int(modifier[9:])
                store_2da[token_id] = row_value
            elif is_store_tlk:
                token_id = int(modifier[6:])
                store_tlk[token_id] = row_value
            elif is_row_label:
                ...
            else:
                cells[modifier] = row_value

        return cells, store_2da, store_tlk

    def row_label_2da(self, identifier: str, modifiers: CaseInsensitiveDict[str]) -> str | None:
        if "RowLabel" in modifiers:
            return modifiers.pop("RowLabel")
        if "NewRowLabel" in modifiers:
            return modifiers.pop("NewRowLabel")
        return None

    def column_inserts_2da(
        self,
        identifier: str,
        modifiers: CaseInsensitiveDict[str],
    ) -> tuple[dict[int, RowValue], dict[str, RowValue], dict[int, str]]:
        index_insert: dict[int, RowValue] = {}
        label_insert: dict[str, RowValue] = {}
        store_2da: dict[int, str] = {}

        for modifier, value in modifiers.items():
            modifier_lowercase = modifier.lower()
            value_lowercase = value.lower()

            is_store_2da = value_lowercase.startswith("2damemory")
            is_store_tlk = value_lowercase.startswith("strref")

            row_value: RowValue | None = None
            if is_store_2da:
                token_id = int(value[9:])
                row_value = RowValue2DAMemory(token_id)
            elif is_store_tlk:
                token_id = int(value[6:])
                row_value = RowValueTLKMemory(token_id)
            else:
                row_value = RowValueConstant(value)

            if modifier_lowercase.startswith("i"):
                index = int(modifier[1:])
                index_insert[index] = row_value
            elif modifier_lowercase.startswith("l"):
                label = modifier[1:]
                label_insert[label] = row_value
            elif modifier_lowercase.startswith("2damemory"):
                token_id = int(modifier[9:])
                store_2da[token_id] = value

        return index_insert, label_insert, store_2da


class NamespaceReader:
    """Responsible for reading and loading namespaces from the namespaces.ini file."""

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
        # use case insensitive keys
        ini.optionxform = lambda optionstr: optionstr.lower()  # type: ignore[method-assign]

        ini_file_bytes: bytes = BinaryReader.load_file(path)
        ini_text: str | None = decode_bytes_with_fallbacks(ini_file_bytes)
        ini.read_string(ini_text)

        return NamespaceReader(ini).load()

    def load(self) -> list[PatcherNamespace]:  # Case-insensitive access to section
        namespaces_section_name = next((section for section in self.ini.sections() if section.lower() == "namespaces"), None)
        if namespaces_section_name is None:
            msg = "The '[Namespaces]' section was not found in the 'namespaces.ini' file."
            raise KeyError(msg)
        namespace_ids: CaseInsensitiveDict[str] = CaseInsensitiveDict(self.ini[namespaces_section_name].items())
        namespaces: list[PatcherNamespace] = []

        for key, namespace_id in namespace_ids.items():
            # Case-insensitive access to namespace_id
            namespace_section_key = next(
                (section for section in self.ini.sections() if section.lower() == namespace_id.lower()),
                None,
            )
            if namespace_section_key is None:
                msg = f"The '[{namespace_id}]' section was not found in the 'namespaces.ini' file, referenced by '{key}={namespace_id}' in [{namespaces_section_name}]."
                raise KeyError(msg)

            this_namespace_section = CaseInsensitiveDict(self.ini[namespace_section_key].items())
            namespace = PatcherNamespace()

            # required
            namespace.ini_filename = this_namespace_section["IniName"]
            namespace.info_filename = this_namespace_section["InfoName"]

            # optional
            namespace.data_folderpath = this_namespace_section.get("DataPath", "")
            namespace.name = this_namespace_section.get("Name", "")
            namespace.description = this_namespace_section.get("Description", "")

            namespace.namespace_id = namespace_section_key
            namespaces.append(namespace)

        return namespaces
