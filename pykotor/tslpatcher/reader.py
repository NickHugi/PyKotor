import os
from configparser import ConfigParser, DuplicateOptionError, DuplicateSectionError, RawConfigParser, SectionProxy
from pathlib import Path
import sys
from typing import Dict, Optional, Union, Tuple, List

from pykotor.common.language import LocalizedString

from pykotor.common.misc import ResRef

from pykotor.common.geometry import Vector3, Vector4
from pykotor.common.stream import BinaryReader

from pykotor.resource.formats.gff import GFFFieldType, GFFStruct, GFFList
from pykotor.resource.formats.ssf import SSFSound
from pykotor.resource.formats.tlk import TLK, read_tlk
from pykotor.tools.misc import is_float, is_int
from pykotor.tslpatcher.config import PatcherConfig, PatcherNamespace
from pykotor.tslpatcher.memory import NoTokenUsage, TokenUsage2DA, TokenUsageTLK
from pykotor.tslpatcher.mods.gff import ModificationsGFF, ModifyFieldGFF, AddFieldGFF, \
    LocalizedStringDelta, FieldValueConstant, FieldValue2DAMemory, FieldValueTLKMemory, FieldValue
from pykotor.tslpatcher.mods.install import InstallFolder, InstallFile
from pykotor.tslpatcher.mods.nss import ModificationsNSS
from pykotor.tslpatcher.mods.ssf import ModifySSF, ModificationsSSF
from pykotor.tslpatcher.mods.tlk import ModifyTLK
from pykotor.tslpatcher.mods.twoda import Modify2DA, ChangeRow2DA, Target, TargetType, WarningException, AddRow2DA, \
    CopyRow2DA, AddColumn2DA, Modifications2DA, RowValue2DAMemory, RowValueTLKMemory, RowValueHigh, RowValueRowIndex, \
    RowValueRowLabel, RowValueConstant, RowValueRowCell

class ConfigParser(RawConfigParser):
    def _read(self, fp, fpname):
        """Override the _read in RawConfigParser so it doesn't throw exceptions when there's no header defined.
        This override matches TSLPatcher.
        """
        elements_added = set()
        cursect = None                        # None, or a dictionary
        sectname = None
        optname = None
        lineno = 0
        indent_level = 0
        e = None                              # None, or an exception
        for lineno, line in enumerate(fp, start=1):
            comment_start = sys.maxsize
            # strip inline comments
            inline_prefixes = {p: -1 for p in self._inline_comment_prefixes}
            while comment_start == sys.maxsize and inline_prefixes:
                next_prefixes = {}
                for prefix, index in inline_prefixes.items():
                    index = line.find(prefix, index+1)
                    if index == -1:
                        continue
                    next_prefixes[prefix] = index
                    if index == 0 or (index > 0 and line[index-1].isspace()):
                        comment_start = min(comment_start, index)
                inline_prefixes = next_prefixes
            # strip full line comments
            for prefix in self._comment_prefixes:
                if line.strip().startswith(prefix):
                    comment_start = 0
                    break
            if comment_start == sys.maxsize:
                comment_start = None
            value = line[:comment_start].strip()
            if not value:
                if self._empty_lines_in_values:
                    # add empty line to the value, but only if there was no
                    # comment on the line
                    if (comment_start is None and
                        cursect is not None and
                        optname and
                        cursect[optname] is not None):
                        cursect[optname].append('') # newlines added at join
                else:
                    # empty line marks end of value
                    indent_level = sys.maxsize
                continue
            # continuation line?
            first_nonspace = self.NONSPACECRE.search(line)
            cur_indent_level = first_nonspace.start() if first_nonspace else 0
            if (cursect is not None and optname and cur_indent_level > indent_level):
                cursect[optname].append(value)
            # a section header or option header?
            else:
                indent_level = cur_indent_level
                # is it a section header?
                if mo := self.SECTCRE.match(value):
                    sectname = mo.group('header')
                    if sectname in self._sections:
                        if self._strict and sectname in elements_added:
                            raise DuplicateSectionError(sectname, fpname,
                                                        lineno)
                        cursect = self._sections[sectname]
                        elements_added.add(sectname)
                    elif sectname == self.default_section:
                        cursect = self._defaults
                    else:
                        cursect = self._dict()
                        self._sections[sectname] = cursect
                        self._proxies[sectname] = SectionProxy(self, sectname)
                        elements_added.add(sectname)
                    # So sections can't start with a continuation line
                    optname = None
                # no section header in the file?
                elif cursect is None:
                    continue # this is the patch
                # an option line?
                else:
                    mo = self._optcre.match(value)
                    if mo:
                        optname, vi, optval = mo.group('option', 'vi', 'value')
                        if not optname:
                            e = self._handle_error(e, fpname, lineno, line)
                        optname = self.optionxform(optname.rstrip())
                        if (self._strict and
                            (sectname, optname) in elements_added):
                            raise DuplicateOptionError(sectname, optname,
                                                       fpname, lineno)
                        elements_added.add((sectname, optname))
                        # This check is fine because the OPTCRE cannot
                        # match if it would set optval to None
                        if optval is not None:
                            optval = optval.strip()
                            cursect[optname] = [optval]
                        else:
                            # valueless option handling
                            cursect[optname] = None
                    else:
                        # a non-fatal parsing error occurred. set up the
                        # exception but keep going. the exception will be
                        # raised at the end of the file and will contain a
                        # list of all bogus lines
                        e = self._handle_error(e, fpname, lineno, line)
        self._join_multiline_values()
        # if any parsing errors occurred, raise an exception
        if e:
            raise e

class ConfigReader:
    def __init__(self, ini: ConfigParser, append: TLK) -> None:
        self.ini = ini
        self.append: TLK = append

        self.config: Optional[PatcherConfig] = None

    @classmethod
    def from_filepath(cls, path: Path | str, append_path_arg: Union[Path, str] | None) -> PatcherConfig: # type: ignore
        append_path: Path | None = Path(append_path_arg) if append_path_arg else None
        ini_file_bytes = BinaryReader.load_file(path)
        ini_text = None
        try:
            ini_text = ini_file_bytes.decode()
        except UnicodeDecodeError as ex:
            try:
                # If UTF-8 failed, try 'cp1252' (similar to ANSI)
                ini_text = ini_file_bytes.decode('cp1252')
            except UnicodeDecodeError as ex2:
                # Raise an exception if all decodings failed
                raise ex2 from ex

        ini = ConfigParser()
        ini.optionxform = str
        ini.read_string(ini_text)

        config = PatcherConfig()
        append: TLK | None = None
        if append_path is not None and append_path.exists():
            append = read_tlk(append_path)
        if append is None:
            append = TLK()
        return ConfigReader(ini, append).load(config)

    def load(self, config: PatcherConfig) -> PatcherConfig:
        self.config = config

        self.load_settings()
        print("Parsing file list from [InstallList]")
        self.load_filelist()
        print("Parsing stringrefs from [TLKList]")
        self.load_stringref()
        print("Parsing 2da from [2DAList]")
        self.load_2da()
        print("Parsing SSF from [SSFList]")
        self.load_ssf()
        print("Parsing GFF from [GFFList]")
        self.load_gff()
        print("Parsing NSS from [NSSList]")
        self.load_nss()

        return self.config

    def load_settings(self) -> None:
        self.config.window_title = self.ini.get("Settings", "WindowCaption", fallback="")
        self.config.confirm_message = self.ini.get("Settings", "ConfirmMessage", fallback="")
        self.config.game_number = self.ini.get("Settings", "LookupGameNumber", fallback=None)
        self.config.required_file = self.ini.get("Settings", "Required", fallback=None)
        self.config.required_message = self.ini.get("Settings", "Required", fallback="")

    def load_filelist(self) -> None:
        folders_ini = dict(self.ini["InstallList"].items())
        for _, foldername in folders_ini.items():
            folder_install = InstallFolder(foldername)
            self.config.install_list.append(folder_install)

            files_ini = dict(self.ini[_].items())
            for __, filename in files_ini.items():
                replace_existing = __.lower().startswith("replace")
                file_install = InstallFile(filename, replace_existing)
                folder_install.files.append(file_install)

    def load_stringref(self) -> None:
        if "TLKList" not in self.ini:
            return

        stringrefs = dict(self.ini["TLKList"].items())

        for name, value in stringrefs.items():
            if name[:7].lower() == "replace":
                folder_install = InstallFolder("Override/../")
                folder_install.files.append(InstallFile(value, True))
                self.config.install_list.append(folder_install)
                continue
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

            modifications = Modifications2DA(file)
            self.config.patches_2da.append(modifications)

            for key, modification_id in modification_ids.items():
                manipulation = self.discern_2da(key, modification_id, dict(self.ini[modification_id].items()))
                modifications.modifiers.append(manipulation)

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
            modifications_ini = dict(self.ini[file].items())
            replace = identifier.startswith("Replace")

            modifications = ModificationsGFF(file, replace)
            self.config.patches_gff.append(modifications)

            for name, value in modifications_ini.items():
                lowercase_name = name.lower()
                if lowercase_name == "!destination":
                    modifications.destination = value
                elif lowercase_name == "!replacefile":
                    modifications.replace_file = bool(int(value))
                elif lowercase_name == "!filename" or lowercase_name == "!saveas":
                    modifications.filename = value
                elif lowercase_name.startswith("addfield"):
                    modifier = self.add_field_gff(value, dict(self.ini[value]))
                    modifications.modifiers.append(modifier)
                else:
                    modifier = self.modify_field_gff(name, value)
                    modifications.modifiers.append(modifier)

    def load_nss(self) -> None:
        if "CompileList" not in self.ini:
            return

        files = dict(self.ini["CompileList"].items())
        destination = files.pop("!destination", None)

        for identifier, file in files.items():
            replace = identifier.lower().startswith("replace")
            modifications = ModificationsNSS(file, replace)
            self.config.patches_nss.append(modifications)

            if destination is not None:
                modifications.destination = destination
        print("Parsing NSS files done!")


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
            value = FieldValueConstant(string_value.replace("<#LF#>", "\n").replace("<#CR#>", "\r"))

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

        return ModifyFieldGFF(name, value)

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
        path = ini_data.get("Path", "")
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
            # Replace comma with dot for decimal separator to match TSLPatcher syntax.
            float_val = raw_value.replace(',', '.')
            value = FieldValueConstant(float(float_val))
        elif field_type.return_type() == str:
            value = FieldValueConstant(raw_value.replace("<#LF#>", "\n").replace("<#CR#>", "\r"))
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
            components = [float(axis.replace(",", ".")) for axis in raw_value.split("|")]
            value = FieldValueConstant(Vector3(*components))
        elif field_type.return_type() == Vector4:
            components = [float(axis.replace(",", ".")) for axis in raw_value.split("|")]
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
        """
        The `discern_2da` function takes in various parameters and based on the value of the `key`
        parameter, it creates and returns an instance of a specific class.

        :param key: The `key` parameter is a string that indicates the type of modification to be performed
        on a 2DA file. It is used to determine which modification class should be instantiated
        :type key: str
        :param identifier: The `identifier` parameter is a string that represents the identifier of the 2DA
        file. It is used to specify which 2DA file the modification should be applied to
        :type identifier: str
        :param modifiers: The `modifiers` parameter is a dictionary that contains additional information or
        options for the function. It is used to modify the behavior of the function based on the specific
        requirements or conditions
        :type modifiers: Dict[str, str]
        :return: an instance of the `Modify2DA` class, which is determined based on the value of the `key`
        parameter. The specific type of modification object returned depends on the value of `key` and the
        provided `modifiers`.
        """
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

    def cells_2da(self, identifier: str, modifiers: Dict[str, str]) -> Tuple[Dict[str, str], Dict[int, str], Dict[int, str]]:
        cells: Dict[str, str] = {}
        store_2da: Dict[int, str] = {}
        store_tlk: Dict[int, str] = {}

        for modifier, value in modifiers.items():
            is_store_2da = modifier.startswith("2DAMEMORY")
            is_store_tlk = modifier.startswith("StrRef")
            is_row_label = modifier in ["RowLabel", "NewRowLabel"]

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

    def row_label_2da(self, identifier: str, modifiers: Dict[str, str]) -> Optional[str]:
        if "RowLabel" in modifiers:
            return modifiers.pop("RowLabel")
        elif "NewRowLabel" in modifiers:
            return modifiers.pop("NewRowLabel")
        else:
            return None

    def column_inserts_2da(self, identifier: str, modifiers: Dict[str, str]) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
        """
        The function `column_inserts_2da` takes an identifier and a dictionary of modifiers, and returns
        three dictionaries: `index_insert`, `label_insert`, and `store_2da`.

        :param identifier: The `identifier` parameter is a string that represents an identifier for the
        column inserts. It is used to uniquely identify the column inserts in the context of the program or
        system
        :type identifier: str
        :param modifiers: The `modifiers` parameter is a dictionary that contains key-value pairs. The keys
        represent modifiers, and the values represent the corresponding values for those modifiers
        :type modifiers: Dict[str, str]
        :return: The function `column_inserts_2da` returns a tuple containing three dictionaries:
        `index_insert`, `label_insert`, and `store_2da`.
        """
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


# The `NamespaceReader` class is responsible for reading and loading namespaces from the namespaces.ini file.
class NamespaceReader:
    def __init__(self, ini: ConfigParser):
        self.ini = ini
        self.namespaces: List[PatcherNamespace] = []

    @classmethod
    def from_filepath(cls, path: str) -> List[PatcherNamespace]:
        """
        The function `from_filepath` reads an INI file from a given file path, parses it using
        `ConfigParser`, and returns a list of `PatcherNamespace` objects.

        :param cls: The parameter `cls` is a reference to the class itself. It is used to call the class
        method `from_filepath` from within the class or its subclasses
        :param path: The `path` parameter is a string that represents the file path of the INI file that
        needs to be loaded
        :type path: str
        :return: a list of `PatcherNamespace` objects.
        """
        ini_file_bytes = BinaryReader.load_file(path)
        ini_text = None
        try:
            ini_text = ini_file_bytes.decode()
        except UnicodeDecodeError:
            try:
                # If UTF-8 failed, try 'cp1252' (similar to ANSI)
                ini_text = ini_file_bytes.decode('cp1252')
            except UnicodeDecodeError:
                # Raise an exception if all decodings failed
                raise Exception('Could not decode file')
        ini = ConfigParser()
        ini.optionxform = lambda optionstr: optionstr
        ini.read_string(ini_text)
        return NamespaceReader(ini).load()

    def load(self) -> List[PatcherNamespace]:
        """
        The function `load` loads data from an INI file and creates a list of `PatcherNamespace` objects
        based on the loaded data.
        :return: a list of `PatcherNamespace` objects.
        """
        namespace_ids = dict(self.ini["Namespaces"].items()).values()
        self.ini = {key.lower(): value for key, value in self.ini.items()}
        namespaces: List[PatcherNamespace] = []

        for namespace_id in namespace_ids:
            namespace = PatcherNamespace()
            namespace_id = namespace_id.lower()
            namespace.namespace_id = namespace_id
            namespace.ini_filename = self.ini[namespace_id]["IniName"]
            namespace.info_filename = self.ini[namespace_id]["InfoName"]
            namespace.data_folderpath = self.ini[namespace_id].get("DataPath")
            namespace.name = self.ini[namespace_id].get("Name")
            namespace.description = self.ini[namespace_id].get("Description")
            namespaces.append(namespace)

        return namespaces
