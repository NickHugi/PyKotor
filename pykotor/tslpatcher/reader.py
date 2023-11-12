from __future__ import annotations

from configparser import ConfigParser
from itertools import tee
from typing import TYPE_CHECKING

from pykotor.common.geometry import Vector3, Vector4
from pykotor.common.language import LocalizedString
from pykotor.common.misc import CaseInsensitiveDict, ResRef, decode_bytes_with_fallbacks
from pykotor.common.stream import BinaryReader
from pykotor.helpers.path import Path, PureWindowsPath
from pykotor.resource.formats.gff import GFFFieldType, GFFList, GFFStruct
from pykotor.resource.formats.ssf import SSFSound
from pykotor.resource.formats.tlk import TLK, read_tlk
from pykotor.tools.misc import is_float, is_int
from pykotor.tools.path import CaseAwarePath
from pykotor.tslpatcher.config import PatcherConfig, PatcherNamespace
from pykotor.tslpatcher.logger import PatchLogger
from pykotor.tslpatcher.memory import NoTokenUsage, TokenUsage, TokenUsage2DA, TokenUsageTLK
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
from pykotor.tslpatcher.mods.install import InstallFile
from pykotor.tslpatcher.mods.nss import ModificationsNSS
from pykotor.tslpatcher.mods.ssf import ModificationsSSF, ModifySSF
from pykotor.tslpatcher.mods.tlk import ModificationsTLK, ModifyTLK
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
        """Loads PatcherConfig from an INI file.

        Args:
        ----
            file_path: The path to the INI file.
            logger: Optional logger for logging errors.

        Returns:
        -------
            PatcherConfig: The loaded configuration.
        Processing Logic:
            1. Resolve the file path.
            2. Initialize an ConfigParser to parse the INI file. 
            3. Load and decode the INI file contents.
            4. Parse the INI sections/keys and populate a PatcherConfig object.
            5. Return the populated PatcherConfig.
        """
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
        """Resolves the case-insensitive section name string if found and returns the case-sensitive correct section name."""
        return next(
            (section for section in self.ini.sections() if section.lower() == section_name.lower()),
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

    def load_filelist(self) -> None:
        """Loads [InstallList] from ini configuration.

        Args:
        ----
            self: The class instance.

        Returns:
        -------
            None: No value is returned.
        Loading File List:
        - Gets [InstallList] section from ini
        - Loops through section items getting foldername and filenames
        - Gets section for each filename
        - Creates InstallFile object for each filename
        - Adds InstallFile to config install list
        - Optionally loads additional vars from filename section
        """
        install_list_section = self.get_section_name("installlist")
        if not install_list_section:
            self.log.add_note("[InstallList] section missing from ini.")
            return

        self.log.add_note("Loading [InstallList] patches from ini...")
        for key, foldername in self.ini[install_list_section].items():
            foldername_section = self.get_section_name(key)
            if foldername_section is None:
                raise KeyError(SECTION_NOT_FOUND_ERROR.format(foldername, key, foldername, install_list_section))

            for key2, filename in self.ini[foldername_section].items():
                replace_existing = key2.lower().startswith("replace")
                file_install = InstallFile(filename, replace_existing)
                file_install.destination = foldername
                self.config.install_list.append(file_install)

                # optional according to tslpatcher readme
                file_section_name = self.get_section_name(filename)
                if file_section_name:
                    file_section_dict = CaseInsensitiveDict(self.ini[file_section_name].items())
                    file_install.pop_tslpatcher_vars(file_section_dict, foldername)

    def load_tlk_list(self) -> None:
        """Load TLK list patches from ini file.

        Processing Logic:
            - Get [TLKList] section from ini file
            - Load TLK list edits into a dictionary
            - Parse range strings and handle ignore indices
            - Process TLK entries based on key syntax.
        """
        tlk_list_section: str | None = self.get_section_name("tlklist")
        if not tlk_list_section:
            self.log.add_note("[TLKList] section missing from ini.")
            return

        self.log.add_note("Loading [TLKList] patches from ini...")
        tlk_list_edits = CaseInsensitiveDict(self.ini[tlk_list_section].items())

        default_destination = tlk_list_edits.pop("!DefaultDestination", ModificationsTLK.DEFAULT_DESTINATION)
        self.config.patches_tlk.pop_tslpatcher_vars(tlk_list_edits, default_destination)

        modifier_dict: dict[int, dict[str, str | ResRef]] = {}
        range_delims: list[str] = [":", "-", "to"]
        append_tlk_edits: TLK | None = None
        syntax_error_caught = False

        def extract_range_parts(range_str: str) -> tuple[int, int | None]:
            """Extracts start and end parts from a range string.

            Args:
            ----
                range_str: String containing range in format start-end or start.

            Returns:
            -------
                tuple[int, int | None]: Tuple containing start and end parts as integers or None.
            - Splits the range string on delimiters like '-' or '.'
            - Converts start and end parts to integers if present
            - Returns start and end as a tuple of integers or integer and None
            """
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
            """Parses a string representing a range into a range object
            Args:
                range_str: String representing a range
            Returns:
                range: Parsed range object from the string
            - Extracts the start and end parts from the range string
            - If end is None, return a range from start to start+1 (meaning no range)
            - Check invalid syntax i.e. if end is less than start, raise ValueError
            - Return the range from start to end+1.
            """
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
            """Processes TLK entries based on provided modifications.

            Args:
            ----
                tlk_data: TLK - TLK data object
                dialog_tlk_keys - Keys for dialog entries to modify
                modifications_tlk_keys - New values for the dialog entries
                is_replacement: bool - Whether it is replacing or modifying text
            Processing Logic:
                - Zips the dialog keys and modification values
                - Parses the keys and values to get the change indices and new values
                - Iterates through the change indices
                    - Skips ignored indices
                    - Gets the TLK entry at the next value index
                    - Creates a modifier object and adds it to the patches list
            """
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
                        append_tlk_edits = read_tlk(self.mod_path / self.config.patches_tlk.sourcefile)
                    if len(append_tlk_edits) == 0:
                        syntax_error_caught = True
                        msg = f"'{self.config.patches_tlk.sourcefile}' in mod directory is empty, but is required to perform modifier '{key}={value}' in [TLKList]"
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
                    msg = f"Invalid syntax found in [TLKList] '{key}={value}'! Expected '{key}' to be one of ['AppendFile', 'ReplaceFile', '!SourceFile', 'StrRef']"
                    raise ValueError(msg)  # noqa: TRY301
            except ValueError as e:
                if syntax_error_caught:
                    raise
                msg = f"Could not parse '{key}={value}' in [TLKList]"
                raise ValueError(msg) from e

    def load_2da(self) -> None:
        """Load 2D array patches from ini file
        Processing Logic:
            - Get the section name for the [2DAList] section
            - Load the section into a dictionary
            - Pop the default destination key
            - Iterate through each identifier and file
                - Get the section for the file
                - Create a Modifications2DA object for the file
                - Load the section into a dictionary and populate the object
                - Append the object to the config patches list
                - Iterate through each key and modification ID
                    - Get the section for the ID
                    - Load the section into a dictionary
                    - Discern and add the modifier to the file object.
        """
        twoda_section_name = self.get_section_name("2dalist")
        if not twoda_section_name:
            self.log.add_note("[2DAList] section missing from ini.")
            return

        self.log.add_note("Loading [2DAList] patches from ini...")

        twoda_section_dict = CaseInsensitiveDict(self.ini[twoda_section_name].items())
        default_destination = twoda_section_dict.pop("!DefaultDestination", Modifications2DA.DEFAULT_DESTINATION)
        for identifier, file in twoda_section_dict.items():
            file_section = self.get_section_name(file)
            if not file_section:
                raise KeyError(SECTION_NOT_FOUND_ERROR.format(file, identifier, file, twoda_section_name))

            modifications = Modifications2DA(file)
            file_section_dict = CaseInsensitiveDict(self.ini[file_section].items())
            modifications.pop_tslpatcher_vars(file_section_dict)
            if modifications.destination == modifications.DEFAULT_DESTINATION:
                modifications.destination = default_destination
            self.config.patches_2da.append(modifications)

            for key, modification_id in file_section_dict.items():
                next_section_name = self.get_section_name(modification_id)
                if not next_section_name:
                    raise KeyError(SECTION_NOT_FOUND_ERROR.format(modification_id, key, modification_id, file_section))
                modification_ids_dict = CaseInsensitiveDict(self.ini[modification_id].items())
                manipulation: Modify2DA | None = self.discern_2da(
                    key,
                    modification_id,
                    modification_ids_dict,
                )
                if not manipulation:  # TODO: Does this denote an error occurred? If so we should raise.
                    continue
                modifications.modifiers.append(manipulation)

    def load_ssf(self) -> None:
        """Loads SSF patches from the ini file.

        - Gets the [SSFList] section name from the ini file
        - Checks for [SSFList] section, logs warning if missing
        - Maps sound names to enum values
        - Loops through [SSFList] parsing patches
            - Gets section for each SSF file
            - Creates ModificationsSSF object
            - Parses file section into modifiers
        - Adds ModificationsSSF objects to config patches
        """
        ssf_list_section = self.get_section_name("ssflist")
        if not ssf_list_section:
            self.log.add_note("[SSFList] section missing from ini.")
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

        ssf_section_dict = CaseInsensitiveDict(self.ini[ssf_list_section].items())
        default_destination = ssf_section_dict.pop("!DefaultDestination", ModificationsSSF.DEFAULT_DESTINATION)

        for identifier, file in ssf_section_dict.items():
            ssf_file_section = self.get_section_name(file)
            if not ssf_file_section:
                raise KeyError(SECTION_NOT_FOUND_ERROR.format(file, identifier, file, ssf_list_section))

            replace = identifier.lower().startswith("replace")
            modifications = ModificationsSSF(file, replace)
            self.config.patches_ssf.append(modifications)

            file_section_dict = CaseInsensitiveDict(self.ini[ssf_file_section].items())
            modifications.pop_tslpatcher_vars(file_section_dict, default_destination)

            for name, value in file_section_dict.items():
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
        """Loads GFF patches from the ini file
        Args:
            self: The object instance
        Returns:
            None: No value is returned
        Loading GFF Patches:
        - Gets the "[GFFList]" section from the ini file
        - Loops through each GFF patch defined
            - Gets the section for the individual GFF file
            - Creates a ModificationsGFF object for it
            - Populates variables from the GFF section
            - Loops through each modifier
                - Creates the appropriate modifier object
                - Adds it to the modifications object
        - Adds the fully configured modifications object to the config.
        """
        gff_list_section = self.get_section_name("gfflist")
        if not gff_list_section:
            self.log.add_note("[GFFList] section missing from ini.")
            return

        self.log.add_note("Loading [GFFList] patches from ini...")
        modifier: ModifyGFF | None = None

        gff_section_dict = CaseInsensitiveDict(self.ini[gff_list_section].items())

        default_destination = gff_section_dict.pop("!DefaultDestination", ModificationsGFF.DEFAULT_DESTINATION)
        for identifier, file in gff_section_dict.items():
            file_section_name = self.get_section_name(file)
            if not file_section_name:
                raise KeyError(SECTION_NOT_FOUND_ERROR.format(file, identifier, file, gff_list_section))

            replace = identifier.lower().startswith("replace")
            modifications = ModificationsGFF(file, replace)
            self.config.patches_gff.append(modifications)

            file_section_dict = CaseInsensitiveDict(self.ini[file_section_name].items())
            modifications.pop_tslpatcher_vars(file_section_dict, default_destination)

            for key, value in file_section_dict.items():
                lowercase_key = key.lower()
                if lowercase_key.startswith("addfield"):
                    next_gff_section = self.get_section_name(value)
                    if not next_gff_section:
                        raise KeyError(SECTION_NOT_FOUND_ERROR.format(value, key, value, file_section_name))

                    next_section_dict = CaseInsensitiveDict(self.ini[next_gff_section].items())
                    modifier = self.add_field_gff(next_gff_section, next_section_dict)
                elif lowercase_key.startswith("2damemory"):
                    if value.lower() != "!fieldpath" and not value.startswith("2damemory"):
                        msg = f"Cannot parse '{key}={value}' in [{identifier}]. GFFList only supports 2DAMEMORY#=!FieldPath assignments"
                        raise ValueError(msg)
                    modifier = Memory2DAModifierGFF(
                        file,
                        int(key[9:]),
                        PureWindowsPath(""),
                    )
                else:
                    modifier = self.modify_field_gff(file_section_name, key, value)

                modifications.modifiers.append(modifier)

    def load_nss(self) -> None:
        """Loads patches from the [CompileList] section of the ini file.

        Args:
        ----
            self: The reader instance
        Returns:
            None
        - Parses the [CompileList] section of the ini file into a dictionary
        - Sets a default destination from an optional key
        - Loops through each identifier/file pair
            - Creates a ModificationsNSS object
            - Looks for an optional section for the file
            - Passes any values to populate the patch
        - Adds each patch to the config patches list
        """
        compilelist_section = self.get_section_name("compilelist")
        if not compilelist_section:
            self.log.add_note("[CompileList] section missing from ini.")
            return

        self.log.add_note("Loading [CompileList] patches from ini...")
        compilelist_section_dict = CaseInsensitiveDict(self.ini[compilelist_section].items())
        default_destination = compilelist_section_dict.pop("!DefaultDestination", ModificationsNSS.DEFAULT_DESTINATION)

        for identifier, file in compilelist_section_dict.items():
            replace = identifier.lower().startswith("replace")
            modifications = ModificationsNSS(file, replace)

            optional_file_section_name = self.get_section_name(file)
            if optional_file_section_name is not None:
                file_section_dict = CaseInsensitiveDict(self.ini[optional_file_section_name].items())
                modifications.pop_tslpatcher_vars(file_section_dict, default_destination)
            self.config.patches_nss.append(modifications)

    #################

    @staticmethod
    def normalize_tslpatcher_float(value_str: str) -> str:
        return value_str.replace(",", ".")
    @staticmethod
    def normalize_tslpatcher_crlf(value_str: str) -> str:
        return value_str.replace("<#LF#>", "\n").replace("<#CR#>", "\r")

    @staticmethod
    def resolve_tslpatcher_field_type(field_type_num_str: str) -> GFFFieldType:
        fieldname_to_fieldtype = CaseInsensitiveDict(
            {
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
            }.items(),
        )
        return fieldname_to_fieldtype[field_type_num_str]

    @staticmethod
    def field_value_from_memory(raw_value: str) -> FieldValue | None:
        """Extract field value from memory reference string.

        Args:
        ----
            raw_value: String value to parse
        Returns:
            FieldValue|None: FieldValue object or None
        Processing Logic:
        - Lowercase the raw value string
        - Check if it starts with "strref" and extract token ID
        - Check if it starts with "2damemory" and extract token ID
        - Return FieldValue memory object with token ID, or None if no match
        """
        lower_str_value = raw_value.lower()
        if lower_str_value.startswith("strref"):
            token_id = int(raw_value[6:])
            return FieldValueTLKMemory(token_id)
        if lower_str_value.startswith("2damemory"):
            token_id = int(raw_value[9:])
            return FieldValue2DAMemory(token_id)
        return None

    @staticmethod
    def field_value_from_unknown(string_value: str) -> FieldValue:
        field_value_memory: FieldValue | None = ConfigReader.field_value_from_memory(string_value)
        if field_value_memory is not None:
            return field_value_memory
        if is_int(string_value):
            return FieldValueConstant(int(string_value))
        parsed_float: str = ConfigReader.normalize_tslpatcher_float(string_value)
        if is_float(parsed_float):
            return FieldValueConstant(float(parsed_float))
        if string_value.count("|") == 2:
            components = parsed_float.split("|")
            return FieldValueConstant(Vector3(*[float(x) for x in components]))
        if string_value.count("|") == 3:
            components = parsed_float.split("|")
            return FieldValueConstant(Vector4(*[float(x) for x in components]))

        return FieldValueConstant(ConfigReader.normalize_tslpatcher_crlf(string_value))

    @staticmethod
    def field_value_from_type(raw_value: str, field_type: GFFFieldType):
        if value := ConfigReader.field_value_from_memory(raw_value):
            return value
        if field_type.return_type() == ResRef:
            return FieldValueConstant(ResRef(raw_value))
        if field_type.return_type() == str:
            return FieldValueConstant(ConfigReader.normalize_tslpatcher_crlf(raw_value))
        if field_type.return_type() == int:
            return FieldValueConstant(int(raw_value))
        if field_type.return_type() == float:
            return FieldValueConstant(float(ConfigReader.normalize_tslpatcher_float(raw_value)))
        if field_type.return_type() == Vector3:
            components = [float(ConfigReader.normalize_tslpatcher_float(axis)) for axis in raw_value.split("|")]
            return FieldValueConstant(Vector3(*components))
        if field_type.return_type() == Vector4:
            components = [float(ConfigReader.normalize_tslpatcher_float(axis)) for axis in raw_value.split("|")]
            return FieldValueConstant(Vector4(*components))
        msg = f"Could not parse fieldtype '{field_type}' in GFFList section [{identifier}]"
        raise ValueError(msg)

    def modify_field_gff(self, identifier: str, key: str, string_value: str) -> ModifyFieldGFF:
        """Modifies a field in a GFF based on the key(path) and string value
        Args:
            identifier: str - The section name (for logging purposes)
            key: str - The key of the field to modify
            string_value: str - The string value to set the field to
        Returns:
            ModifyFieldGFF - A ModifyFieldGFF object representing the modification
        Processing Logic:
            1. Parses the string value into a FieldValue
            2. Handles special cases for keys containing "(strref)", "(lang)" or starting with "2damemory"
            3. Returns a ModifyFieldGFF object representing the modification.
        """
        value: FieldValue = self.field_value_from_unknown(string_value)
        key_lower = key.lower()
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
            string_value_lower = string_value.lower()
            if string_value_lower != "!fieldpath" and not string_value_lower.startswith("2damemory"):
                msg = f"Cannot parse '{key}={value}' in [{identifier}]. GFFList only supports 2DAMEMORY#=!FieldPath assignments"
                raise ValueError(msg)
            value = FieldValueConstant(PureWindowsPath(""))  # no path at the root

        return ModifyFieldGFF(PureWindowsPath(key), value)

    def add_field_gff(
        self,
        identifier: str,
        ini_data: CaseInsensitiveDict[str],
        current_path: PureWindowsPath | None = None,
    ) -> ModifyGFF:  # sourcery skip: extract-method, remove-unreachable-code
        """Parse GFFList's AddField syntax from the ini to determine what fields/structs/lists to add.

        Args:
        ----
            identifier: str - Identifier of the section in the current recursion from the ini file
            ini_data: CaseInsensitiveDict - Data from the ini section
            current_path: PureWindowsPath or None - Current path in the GFF
        Returns:
            ModifyGFF - Object containing the field modification
        Processing Logic:
            1. Determines the field type from the field type string
            2. Gets the label and optional value, path from the ini data
            3. Construct a current path from the gff root struct based on recursion level and path key.
            3. Handles nested modifiers and structs in lists
            4. Returns an AddFieldGFF or AddStructToListGFF object based on whether a label is provided.
        """
        value: FieldValue
        text: str
        struct_id: int | None = None

        # required
        field_type: GFFFieldType = self.__class__.resolve_tslpatcher_field_type(ini_data["FieldType"])
        label: str = ini_data["Label"].strip()

        # situational/optional
        raw_path: str = ini_data.get("Path", "").strip()
        raw_value: str | None = ini_data.get("Value")

        # Handle current gff path
        path: PureWindowsPath = PureWindowsPath(raw_path)
        path = path if path.name else (current_path or PureWindowsPath(""))

        if raw_value is None:
            if field_type.return_type() == LocalizedString:
                raw_stringref = ini_data["StrRef"]
                stringref: FieldValue = self.field_value_from_memory(raw_stringref) or FieldValueConstant(int(raw_stringref))
                l_string_delta = LocalizedStringDelta(stringref)

                for substring, text in ini_data.items():
                    if not substring.lower().startswith("lang"):
                        continue
                    substring_id = int(substring[4:])
                    language, gender = l_string_delta.substring_pair(substring_id)
                    formatted_text = self.__class__.normalize_tslpatcher_crlf(text)
                    l_string_delta.set_data(language, gender, formatted_text)
                value = FieldValueConstant(l_string_delta)
            elif field_type.return_type() == GFFList:
                value = FieldValueConstant(GFFList())
            elif field_type.return_type() == GFFStruct:
                raw_struct_id = ini_data["TypeId"].strip()
                if not is_int(raw_struct_id):
                    msg = f"Invalid struct id: expected int but got '{raw_struct_id}' in '[{identifier}]'"
                    raise ValueError(msg)

                struct_id = int(raw_struct_id)
                path /= ">>##INDEXINLIST##<<"  # see the check in mods/gff.py. Perhaps need to check if label is set, first?
                value = FieldValueConstant(GFFStruct(struct_id))
            else:
                msg = f"Could not find valid field return type in [{identifier}] matching field type '{field_type}' in this context"
                raise ValueError(msg)
        else:
            value = self.field_value_from_type(raw_value, field_type)

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
                struct_id or 0,  # TODO: Is the '0' needed? Is this the default value?
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
        modifiers: CaseInsensitiveDict[str],
    ) -> Modify2DA | None:
        """Determines the type of 2DA modification based on the key
        Args:
            key: str - The key identifying the type of modification
            identifier: str - The identifier of the 2DA (section name)
            modifiers: CaseInsensitiveDict - Additional parameters for the modification
        Returns:
            Modify2DA | None - The 2DA modification object or None
        Processing Logic:
        - Parses the key to determine modification type
        - Checks for required parameters
        - Constructs the appropriate modification object
        - Returns the modification object or None.
        """
        lowercase_key = key.lower()
        cells, store_2da, store_tlk = self.cells_2da(identifier, modifiers)
        if lowercase_key.startswith("addcolumn"):
            return self.add_2da_column(modifiers, identifier)
        if lowercase_key.startswith("addrow"):
            return AddRow2DA(
                identifier,
                modifiers.pop("ExclusiveColumn", None),
                self.row_label_2da(identifier, modifiers),
                cells,
                store_2da,
                store_tlk,
            )

        target = self.target_2da(identifier, modifiers)
        if target is None:
            return None
        if lowercase_key.startswith("changerow"):
            return ChangeRow2DA(
                identifier,
                target,
                cells,
                store_2da,
                store_tlk,
            )
        if lowercase_key.startswith("copyrow"):
            return CopyRow2DA(
                identifier,
                target,
                modifiers.pop("ExclusiveColumn", None),
                self.row_label_2da(identifier, modifiers),
                cells,
                store_2da,
                store_tlk,
            )
        msg = f"Could not parse key '{key}={identifier}', expecting one of ['ChangeRow=', 'AddColumn=', 'AddRow=', 'CopyRow=']"
        raise KeyError(msg)

    def add_2da_column(self, modifiers: CaseInsensitiveDict[str], identifier: str):
        """Adds a column to a 2DA table.

        Args:
        ----
            modifiers: CaseInsensitiveDict[str]: Modifiers for the column
            identifier: str: Identifier for the 2DA table
        Returns:
            AddColumn2DA: Object to add the column to the 2DA table
        Processing Logic:
        1. Gets the required 'ColumnLabel' and 'DefaultValue' modifiers
        2. Checks for missing required modifiers and raises error
        3. Gets index and label inserts for the new column from column_inserts_2da
        4. Returns AddColumn2DA object to add the column.
        """
        def get_required_modifier(key):
            value = modifiers.pop(key, None)
            if value is None:
                msg = f"Missing '{key}' in [{identifier}]"
                raise KeyError(msg)
            return value
        header = get_required_modifier("ColumnLabel")
        default = get_required_modifier("DefaultValue")
        default = "" if default == "****" else default
        index_insert, label_insert, store_2da = self.column_inserts_2da(
            identifier,
            modifiers,
        )
        return AddColumn2DA(
            identifier,
            header,
            default,
            index_insert,
            label_insert,
            store_2da,
        )

    def target_2da(self, identifier: str, modifiers: CaseInsensitiveDict[str]) -> Target | None:
        """Gets or creates a 2D target from modifiers.

        Args:
        ----
            identifier: Identifier for target
            modifiers: Modifiers dictionary
        Returns:
            Target | None: Target object or None
        - Checks for RowIndex, RowLabel or LabelIndex key
        - Calls get_target() to create Target object
        - Returns None if no valid key found with warning
        """
        def get_target(target_type: TargetType, key: str, is_int: bool = False) -> Target:
            raw_value: str | None = modifiers.pop(key, None)
            if raw_value is None:
                msg = f"'{key}' missing from [{identifier}] in ini."
                raise ValueError(msg)
            value: str | int = int(raw_value) if is_int else raw_value
            return Target(target_type, value)

        if "RowIndex" in modifiers:
            return get_target(TargetType.ROW_INDEX, "RowIndex", is_int=True)
        if "RowLabel" in modifiers:
            return get_target(TargetType.ROW_LABEL, "RowLabel")
        if "LabelIndex" in modifiers:
            return get_target(TargetType.LABEL_COLUMN, "LabelIndex")

        self.log.add_warning(f"No line set to be modified in [{identifier}].")  # TODO: should raise an exception?
        return None

    def cells_2da(
        self,
        identifier: str,
        modifiers: CaseInsensitiveDict[str],
    ) -> tuple[dict[str, RowValue], dict[int, RowValue], dict[int, RowValue]]:
        """Parses modifiers to extract 2DA and TLK cell values and row labels.

        Args:
        ----
            identifier: str - Section name for this 2DA
            modifiers: CaseInsensitiveDict[str] - Modifiers dictionary

        Returns:
        -------
            tuple[dict[str, RowValue], dict[int, RowValue], dict[int, RowValue]] - Tuple containing cells dictionary, 2DA store dictionary, TLK store dictionary

        Processing Logic:
        1. Loops through each modifier and value
        2. Determines modifier type (cell, 2DA store, TLK store, row label)
        3. Creates appropriate RowValue for cell/store value
        4. Adds cell/store value to return dictionaries
        """
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
            elif not is_row_label:
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
        """Extracts specific 2DA patch information from the ini
        Args:
            identifier: str - Section name being handled
            modifiers: CaseInsensitiveDict[str] - Modifiers to insert values
        Returns:
            tuple[dict[int, RowValue], dict[str, RowValue], dict[int, str]] - Index inserts, label inserts, 2DA store
        Processes Logic:
        - Loops through modifiers and extracts value type
        - Assigns row value based on value type
        - Inserts into appropriate return dictionary based on modifier key
        - Returns tuple of inserted values dictionaries.
        """
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
