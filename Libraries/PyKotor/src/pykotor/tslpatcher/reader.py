from __future__ import annotations

import base64

from configparser import ConfigParser, ParsingError
from pathlib import Path, PurePath, PureWindowsPath
from typing import TYPE_CHECKING

from pykotor.common.language import LocalizedString
from pykotor.common.misc import ResRef
from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.gff import GFFFieldType, GFFList, GFFStruct
from pykotor.resource.formats.ssf import SSFSound
from pykotor.tools.encoding import decode_bytes_with_fallbacks
from pykotor.tools.path import CaseAwarePath
from pykotor.tslpatcher.config import LogLevel
from pykotor.tslpatcher.logger import PatchLogger
from pykotor.tslpatcher.memory import NoTokenUsage, TokenUsage2DA, TokenUsageTLK
from pykotor.tslpatcher.mods.gff import (
    AddFieldGFF,
    AddStructToListGFF,
    FieldValue2DAMemory,
    FieldValueConstant,
    FieldValueListIndex,
    FieldValueTLKMemory,
    LocalizedStringDelta,
    Memory2DAModifierGFF,
    ModificationsGFF,
    ModifyFieldGFF,
)
from pykotor.tslpatcher.mods.install import InstallFile
from pykotor.tslpatcher.mods.ncs import ModificationsNCS, ModifyNCS, NCSTokenType
from pykotor.tslpatcher.mods.nss import ModificationsNSS
from pykotor.tslpatcher.mods.ssf import ModificationsSSF, ModifySSF
from pykotor.tslpatcher.mods.tlk import ModificationsTLK, ModifyTLK
from pykotor.tslpatcher.mods.twoda import (
    AddColumn2DA,
    AddRow2DA,
    ChangeRow2DA,
    CopyRow2DA,
    Modifications2DA,
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
from pykotor.tslpatcher.namespaces import PatcherNamespace
from utility.common.geometry import Vector3, Vector4
from utility.common.more_collections import CaseInsensitiveDict
from utility.misc import is_float, is_int

if TYPE_CHECKING:
    import os

    from typing_extensions import Literal, Self  # pyright: ignore[reportMissingModuleSource]

    from pykotor.tslpatcher.config import PatcherConfig
    from pykotor.tslpatcher.memory import TokenUsage
    from pykotor.tslpatcher.mods.gff import FieldValue, ModifyGFF
    from pykotor.tslpatcher.mods.twoda import Modify2DA, RowValue

SECTION_NOT_FOUND_ERROR = "The [{}] section was not found in the ini"
REFERENCES_TRACEBACK_MSG = ", referenced by '{}={}' in [{}]"


class NamespaceReader:
    """Responsible for reading and loading namespaces from the namespaces.ini file."""

    def __init__(self, ini: ConfigParser):
        self.ini: ConfigParser = ini
        self.namespaces: list[PatcherNamespace] = []

    @classmethod
    def from_filepath(
        cls,
        path: os.PathLike | str,
    ) -> list[PatcherNamespace]:
        ini = ConfigParser(
            delimiters=("="),
            allow_no_value=True,
            strict=False,
            interpolation=None,
            inline_comment_prefixes=(";", "#"),
        )
        # use case insensitive keys
        ini.optionxform = lambda optionstr: optionstr.lower()  # type: ignore[method-assign]

        ini.read_string(decode_bytes_with_fallbacks(BinaryReader.load_file(path)))
        return NamespaceReader(ini).load()

    def load(self) -> list[PatcherNamespace]:  # Case-insensitive access to section
        namespaces_section_name: str | None = next((section for section in self.ini.sections() if section.lower() == "namespaces"), None)
        if namespaces_section_name is None:
            raise KeyError(SECTION_NOT_FOUND_ERROR.format("Namespaces"))

        namespace_ids: CaseInsensitiveDict[str] = CaseInsensitiveDict(self.ini[namespaces_section_name])
        namespaces: list[PatcherNamespace] = []

        for key, namespace_id in namespace_ids.items():
            # Case-insensitive access to namespace_id
            namespace_section_key: str | None = next((section for section in self.ini.sections() if section.lower() == namespace_id.lower()), None)
            if namespace_section_key is None:
                msg = f"The '[{namespace_id}]' section was not found in the 'namespaces.ini' file, referenced by '{key}={namespace_id}' in [{namespaces_section_name}]."
                raise KeyError(msg)

            this_namespace_section = CaseInsensitiveDict(self.ini[namespace_section_key])

            # required
            ini_filename: str = this_namespace_section["IniName"]
            info_filename: str = this_namespace_section["InfoName"]
            namespace = PatcherNamespace(ini_filename, info_filename)

            # optional
            namespace.data_folderpath = PurePath(this_namespace_section.get("DataPath", ""))
            namespace.name = this_namespace_section.get("Name", "").strip()
            namespace.description = this_namespace_section.get("Description", "")

            namespace.namespace_id = namespace_section_key
            namespaces.append(namespace)

        return namespaces


class ConfigReader:
    def __init__(
        self,
        ini: ConfigParser,
        mod_path: os.PathLike | str,
        logger: PatchLogger | None = None,
        tslpatchdata_path: os.PathLike | str | None = None,
    ):
        self.previously_parsed_sections: set[str] = set()
        self.ini: ConfigParser = ini
        self.mod_path: CaseAwarePath = CaseAwarePath(mod_path)
        # path to the tslpatchdata, optional but we'll use it here for the nwnnsscomp.exe if it exists.
        self.tslpatchdata_path: CaseAwarePath | None = (
            None
            if tslpatchdata_path is None
            else CaseAwarePath(tslpatchdata_path)
        )
        self.config: PatcherConfig
        self.log: PatchLogger = logger or PatchLogger()

    @classmethod
    def from_filepath(
        cls,
        file_path: os.PathLike | str,
        logger: PatchLogger | None = None,
        tslpatchdata_path: os.PathLike | str | None = None,
    ) -> Self:
        """Load PatcherConfig from an INI file path.

        Args:
        ----
            file_path: The path to the INI file.
            logger: Optional logger instance.
            tslpatchdata_path: Optional path to the tslpatchdata directory.

        Returns:
        -------
            A PatcherConfig instance loaded from the file.

        Processing Logic:
        ----------------
            - Resolve the file path and load its contents
            - Parse the INI text into a ConfigParser
            - Initialize a PatcherConfig instance
            - Populate its config attribute from the ConfigParser
            - Return the initialized instance
        """
        from pykotor.tslpatcher.config import PatcherConfig  # noqa: PLC0415 Prevent circular imports

        resolved_file_path: Path = Path(file_path).resolve()

        ini = ConfigParser(
            delimiters=("="),
            allow_no_value=True,
            strict=False,
            interpolation=None,
            inline_comment_prefixes=(";", "#"),
        )

        # Use case-sensitive keys
        ini.optionxform = lambda optionstr: optionstr if optionstr.strip() else optionstr.strip()  # type: ignore[method-assign]
        try:
            ini.read_string(decode_bytes_with_fallbacks(BinaryReader.load_file(resolved_file_path)))
        except ParsingError as e:
            e.source = str(resolved_file_path)
            raise e  # noqa: TRY201  # don't `raise from e` here!

        instance: Self = cls(ini, resolved_file_path.parent, logger, tslpatchdata_path)
        instance.config = PatcherConfig()
        return instance

    def load(
        self,
        config: PatcherConfig,
    ) -> PatcherConfig:
        self.config: PatcherConfig = config
        self.previously_parsed_sections: set[str] = set()

        self.load_settings()
        self.load_tlk_list()
        self.load_install_list()
        self.load_2da_list()
        self.load_gff_list()
        self.load_compile_list()
        self.load_hack_list()
        self.load_ssf_list()
        self.log.add_note("The ConfigReader finished loading the INI")
        all_sections_set = set(self.ini.sections())
        orphaned_sections: set[str] = all_sections_set - self.previously_parsed_sections
        if len(orphaned_sections):
            orphaned_sections_str: str = "\n".join(orphaned_sections)
            self.log.add_note(f"There are some orphaned ini sections found in the changes:\n{orphaned_sections_str}")

        return self.config

    def get_section_name(
        self,
        section_name: str,
    ) -> str | None:
        """Resolves the case-insensitive section name string if found and returns the case-sensitive correct section name."""
        s: str | None = next(
            (
                section
                for section in self.ini.sections()
                if section.lower() == section_name.lower()
            ),
            None,
        )
        if s is not None:
            self.previously_parsed_sections.add(s)
        return s

    def load_settings(self):
        """Loads [Settings] from ini configuration into memory."""
        settings_section: str | None = self.get_section_name("settings")
        if settings_section is None:
            self.log.add_warning("[Settings] section missing from ini.")
            return

        self.log.add_note("Loading [Settings] section from ini...")
        settings_ini = CaseInsensitiveDict(self.ini[settings_section])

        self.config.window_title = settings_ini.get("WindowCaption", "")
        self.config.confirm_message = settings_ini.get("ConfirmMessage", "")
        for key, value in settings_ini.items():
            lower_key = key.lower()
            if lower_key == "required" or (lower_key.startswith("required") and len(key) > len("required") and not key[len("required") :].lower().startswith("msg")):
                if lower_key != "required" and not key[len("required") :].isdigit():
                    raise ValueError(f"Key '{key}' improperly defined in settings ini. Expected (Required) or (RequiredMsg)")
                these_files = tuple(filename.strip() for filename in value.split(","))
                self.config.required_files.append(these_files)

            if lower_key == "requiredmsg" or (lower_key.startswith("requiredmsg") and len(key) > len("requiredmsg")):
                if lower_key != "requiredmsg" and not key[len("requiredmsg") :].isdigit():
                    raise ValueError(f"Key '{key}' improperly defined in settings ini. Expected (Required) or (RequiredMsg)")
                self.config.required_messages.append(value.strip())
        if len(self.config.required_files) != len(self.config.required_messages):
            raise ValueError(f"Required files definitions must match required msg count ({len(self.config.required_files)}/{len(self.config.required_messages)})")
        self.config.save_processed_scripts = int(settings_ini.get("SaveProcessedScripts", 0))
        self.config.log_level = LogLevel(int(settings_ini.get("LogLevel", LogLevel.WARNINGS.value)))

        # HoloPatcher optional
        self.config.ignore_file_extensions = bool(settings_ini.get("IgnoreExtensions")) or False

        lookup_game_number: str | None = settings_ini.get("LookupGameNumber")
        if lookup_game_number:
            lookup_game_number = lookup_game_number.strip()
            if lookup_game_number not in {"1", "2"}:
                msg = f"Invalid: 'LookupGameNumber={lookup_game_number}' in [Settings], must be 1 or 2 representing the KOTOR game."
                raise ValueError(msg)
            self.config.game_number = int(lookup_game_number)
        else:
            self.config.game_number = None

    def load_install_list(self):
        """Loads [InstallList] from ini configuration into memory.

        Processing Logic:
        ----------------
            - Gets [InstallList] section from ini
            - Loops through section items getting foldername and filenames
            - Gets section for each filename
            - Creates InstallFile object for each filename
            - Adds InstallFile to config install list
            - Optionally loads additional vars from filename section
        """
        install_list_section: str | None = self.get_section_name("InstallList")
        if install_list_section is None:
            self.log.add_note("[InstallList] section missing from ini.")
            return

        self.log.add_note("Loading [InstallList] patches from ini...")
        for folder_key, foldername in self.ini[install_list_section].items():
            foldername_section: str | None = self.get_section_name(folder_key)
            if foldername_section is None:
                raise KeyError(SECTION_NOT_FOUND_ERROR.format(foldername) + REFERENCES_TRACEBACK_MSG.format(folder_key, foldername, install_list_section))

            folder_section_dict = CaseInsensitiveDict(self.ini[foldername_section])
            # !SourceFolder: Relative path from mod_path (which is typically the tslpatchdata folder) to source files.
            # Default value "." refers to mod_path itself (the tslpatchdata folder), not its parent.
            # For example: if mod_path = "C:/Mod/tslpatchdata", then:
            #   - !SourceFolder="." resolves to "C:/Mod/tslpatchdata"
            #   - !SourceFolder="textures" resolves to "C:/Mod/tslpatchdata/textures"
            sourcefolder: str = folder_section_dict.pop("!SourceFolder", ".")
            for file_key, filename in folder_section_dict.items():
                file_install = InstallFile(
                    filename,
                    replace_existing=file_key.lower().startswith("replace"),
                )
                file_install.destination = foldername
                file_install.sourcefolder = sourcefolder
                self.config.install_list.append(file_install)

                # Optional according to TSLPatcher readme
                file_section_name: str | None = self.get_section_name(filename)
                if file_section_name is not None:
                    file_section_dict = CaseInsensitiveDict(self.ini[file_section_name])
                    file_install.pop_tslpatcher_vars(file_section_dict, foldername, sourcefolder)

    def load_tlk_list(self):  # noqa: PLR0915
        """Loads TLK patches from the ini file into memory.

        Processing Logic:
        ----------------
            - Parses the [TLKList] section to get TLK patch entries
            - Handles different patch syntaxes like file replacements, string references etc
            - Builds ModifyTLK objects for each patch and adds to the patch list
            - Raises errors for invalid syntax or missing files
        """
        tlk_list_section: str | None = self.get_section_name("tlklist")
        if tlk_list_section is None:
            self.log.add_note("[TLKList] section missing from ini.")
            return

        self.log.add_note("Loading [TLKList] patches from ini...")
        tlk_list_edits = CaseInsensitiveDict(self.ini[tlk_list_section])

        default_destination = tlk_list_edits.pop("!DefaultDestination", ModificationsTLK.DEFAULT_DESTINATION)
        # !DefaultSourceFolder: Relative path from mod_path (which is typically the tslpatchdata folder) to source files.
        # Default value "." refers to mod_path itself (the tslpatchdata folder), not its parent.
        # For example: if mod_path = "C:/Mod/tslpatchdata", then:
        #   - !DefaultSourceFolder="." resolves to "C:/Mod/tslpatchdata"
        #   - !DefaultSourceFolder="textures" resolves to "C:/Mod/tslpatchdata/textures"
        default_sourcefolder = tlk_list_edits.pop("!DefaultSourceFolder", ".")
        self.config.patches_tlk.pop_tslpatcher_vars(tlk_list_edits, default_destination, default_sourcefolder)

        modifier_dict: dict[int, dict[str, str]] = {}
        syntax_error_caught = False

        def process_tlk_entries(
            tlk_filename: str,
            dialog_tlk_index: int,
            mod_tlk_index: int,
            *,
            is_replacement: bool,
        ):
            modifier = ModifyTLK(dialog_tlk_index, is_replacement)
            modifier.mod_index = mod_tlk_index
            # Path resolution: mod_path / sourcefolder / tlk_filename
            # mod_path is typically the tslpatchdata folder (parent of changes.ini).
            # If sourcefolder = ".", this resolves to mod_path itself (tslpatchdata folder).
            modifier.tlk_filepath = self.mod_path / self.config.patches_tlk.sourcefolder / tlk_filename
            self.config.patches_tlk.modifiers.append(modifier)

        for key, value in tlk_list_edits.items():
            lower_key: str = key.lower()
            replace_file: bool = lower_key.startswith("replace")
            append_file: bool = lower_key.startswith("append")
            try:
                if lower_key.startswith("strref"):
                    process_tlk_entries(
                        tlk_filename=self.config.patches_tlk.sourcefile,
                        dialog_tlk_index=int(lower_key[6:]),
                        mod_tlk_index=int(value),
                        is_replacement=False,
                    )
                elif replace_file or append_file:
                    next_section_name = self.get_section_name(value)
                    if next_section_name is None:
                        syntax_error_caught = True
                        raise ValueError(SECTION_NOT_FOUND_ERROR.format(value) + REFERENCES_TRACEBACK_MSG.format(key, value, tlk_list_section))  # noqa: TRY301

                    next_section_dict = CaseInsensitiveDict(self.ini[next_section_name])
                    self.config.patches_tlk.pop_tslpatcher_vars(next_section_dict, default_destination, default_sourcefolder)

                    for raw_dialog_tlk_index, raw_mod_tlk_index in zip(
                        self.ini[next_section_name].keys(),
                        self.ini[next_section_name].values(),
                    ):
                        dialog_tlk_index = int(raw_dialog_tlk_index[6:]) if raw_dialog_tlk_index.lower().startswith("strref") else int(raw_dialog_tlk_index)
                        mod_tlk_index = int(raw_mod_tlk_index[6:]) if raw_mod_tlk_index.lower().startswith("strref") else int(raw_mod_tlk_index)
                        process_tlk_entries(
                            tlk_filename=next_section_name,
                            dialog_tlk_index=dialog_tlk_index,
                            mod_tlk_index=mod_tlk_index,
                            is_replacement=replace_file,
                        )
                elif "\\" in lower_key or "/" in lower_key:
                    delimiter: Literal["\\", "/"] = "\\" if "\\" in lower_key else "/"
                    token_id_str, property_name = lower_key.split(delimiter)
                    token_id = int(token_id_str)

                    if token_id not in modifier_dict:
                        modifier_dict[token_id] = {"text": "", "voiceover": ""}

                    if property_name == "text":
                        modifier = ModifyTLK(token_id, is_replacement=True)
                        modifier.text = value
                        self.config.patches_tlk.modifiers.append(modifier)
                    elif property_name == "sound":
                        modifier = ModifyTLK(token_id, is_replacement=True)
                        modifier.sound = ResRef(value)
                        self.config.patches_tlk.modifiers.append(modifier)
                    else:
                        syntax_error_caught = True
                        msg = f"Invalid [TLKList] syntax: '{key}={value}'! Expected '{key}' to be one of ['Sound', 'Text']"
                        raise ValueError(msg)  # noqa: TRY301
                else:
                    syntax_error_caught = True
                    msg = f"Invalid syntax found in [TLKList] '{key}={value}'! Expected '{key}' to be one of ['AppendFile', 'ReplaceFile', '!SourceFile', 'StrRef', 'Text', 'Sound']"  # noqa: E501
                    raise ValueError(msg)  # noqa: TRY301

            except ValueError as e:
                if syntax_error_caught:
                    raise
                msg = f"Could not parse '{key}={value}' in [TLKList]"
                raise ValueError(msg) from e

    def load_2da_list(self):
        """Load 2D array patches from ini file into memory.

        Processing Logic:
        ----------------
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
        twoda_section_name: str | None = self.get_section_name("2DAList")
        if twoda_section_name is None:
            self.log.add_note("[2DAList] section missing from ini.")
            return

        self.log.add_note("Loading [2DAList] patches from ini...")

        twoda_section_dict = CaseInsensitiveDict(self.ini[twoda_section_name])
        default_destination: str = twoda_section_dict.pop("!DefaultDestination", Modifications2DA.DEFAULT_DESTINATION)
        # !DefaultSourceFolder: Relative path from mod_path (which is typically the tslpatchdata folder) to source files.
        # Default value "." refers to mod_path itself (the tslpatchdata folder), not its parent.
        # For example: if mod_path = "C:/Mod/tslpatchdata", then:
        #   - !DefaultSourceFolder="." resolves to "C:/Mod/tslpatchdata"
        #   - !DefaultSourceFolder="2da" resolves to "C:/Mod/tslpatchdata/2da"
        default_source_folder = twoda_section_dict.pop("!DefaultSourceFolder", ".")
        for identifier, file in twoda_section_dict.items():
            file_section: str | None = self.get_section_name(file)
            if file_section is None:
                raise KeyError(SECTION_NOT_FOUND_ERROR.format(file) + REFERENCES_TRACEBACK_MSG.format(identifier, file, twoda_section_name))

            modifications = Modifications2DA(file)
            file_section_dict = CaseInsensitiveDict(self.ini[file_section])
            modifications.pop_tslpatcher_vars(file_section_dict, default_destination, default_source_folder)

            self.config.patches_2da.append(modifications)

            for key, modification_id in file_section_dict.items():
                next_section_name: str | None = self.get_section_name(modification_id)
                if next_section_name is None:
                    raise KeyError(SECTION_NOT_FOUND_ERROR.format(modification_id) + REFERENCES_TRACEBACK_MSG.format(key, modification_id, file_section))

                modification_ids_dict = CaseInsensitiveDict(self.ini[modification_id])
                manipulation: Modify2DA | None = self.discern_2da(key, modification_id, modification_ids_dict)
                if not manipulation:  # TODO(th3w1zard1): Does this denote an error occurred? If so we should raise.
                    continue
                modifications.modifiers.append(manipulation)

    def load_ssf_list(self):
        """Loads SSF patches from the ini file into memory.

        Processing Logic:
        ----------------
            - Gets the [SSFList] section name from the ini file
            - Checks for [SSFList] section, logs warning if missing
            - Maps sound names to enum values
            - Loops through [SSFList] parsing patches
                - Gets section for each SSF file
                - Creates ModificationsSSF object
                - Parses file section into modifiers
            - Adds ModificationsSSF objects to config patches
        """
        ssf_list_section: str | None = self.get_section_name("SSFList")
        if ssf_list_section is None:
            self.log.add_note("[SSFList] section missing from ini.")
            return

        self.log.add_note("Loading [SSFList] patches from ini...")

        ssf_section_dict = CaseInsensitiveDict(self.ini[ssf_list_section])
        default_destination: str = ssf_section_dict.pop("!DefaultDestination", ModificationsSSF.DEFAULT_DESTINATION)
        # !DefaultSourceFolder: Relative path from mod_path (which is typically the tslpatchdata folder) to source files.
        # Default value "." refers to mod_path itself (the tslpatchdata folder), not its parent.
        # For example: if mod_path = "C:/Mod/tslpatchdata", then:
        #   - !DefaultSourceFolder="." resolves to "C:/Mod/tslpatchdata"
        #   - !DefaultSourceFolder="voices" resolves to "C:/Mod/tslpatchdata/voices"
        default_source_folder = ssf_section_dict.pop("!DefaultSourceFolder", ".")

        for identifier, file in ssf_section_dict.items():
            ssf_file_section: str | None = self.get_section_name(file)
            if ssf_file_section is None:
                raise KeyError(SECTION_NOT_FOUND_ERROR.format(file) + REFERENCES_TRACEBACK_MSG.format(identifier, file, ssf_list_section))

            replace: bool = identifier.lower().startswith("replace")
            modifications = ModificationsSSF(file, replace)
            self.config.patches_ssf.append(modifications)

            file_section_dict = CaseInsensitiveDict(self.ini[ssf_file_section])
            modifications.pop_tslpatcher_vars(file_section_dict, default_destination, default_source_folder)

            for name, value in file_section_dict.items():
                new_value: TokenUsage
                lower_value: str = value.lower()
                if lower_value.startswith("2damemory"):
                    token_id = int(value[9:])
                    new_value = TokenUsage2DA(token_id)
                elif lower_value.startswith("strref"):
                    token_id = int(value[6:])
                    new_value = TokenUsageTLK(token_id)
                else:
                    new_value = NoTokenUsage(int(value))

                sound: SSFSound = self.resolve_tslpatcher_ssf_sound(name)
                modifier = ModifySSF(sound, new_value)
                modifications.modifiers.append(modifier)

    def load_gff_list(self):
        """Loads GFF patches from the ini file into memory.

        Processing Logic:
        ----------------
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
        gff_list_section: str | None = self.get_section_name("GFFList")
        if gff_list_section is None:
            self.log.add_note("[GFFList] section missing from ini.")
            return

        self.log.add_note("Loading [GFFList] patches from ini...")
        gff_section_dict = CaseInsensitiveDict(self.ini[gff_list_section])
        default_destination: str = gff_section_dict.pop("!DefaultDestination", ModificationsGFF.DEFAULT_DESTINATION)
        # !DefaultSourceFolder: Relative path from mod_path (which is typically the tslpatchdata folder) to source files.
        # Default value "." refers to mod_path itself (the tslpatchdata folder), not its parent.
        # For example: if mod_path = "C:/Mod/tslpatchdata", then:
        #   - !DefaultSourceFolder="." resolves to "C:/Mod/tslpatchdata"
        #   - !DefaultSourceFolder="gff" resolves to "C:/Mod/tslpatchdata/gff"
        default_source_folder = gff_section_dict.pop("!DefaultSourceFolder", ".")

        for identifier, file in gff_section_dict.items():
            file_section_name: str | None = self.get_section_name(file)
            if file_section_name is None:
                raise KeyError(SECTION_NOT_FOUND_ERROR.format(file) + REFERENCES_TRACEBACK_MSG.format(identifier, file, gff_list_section))

            replace: bool = identifier.lower().startswith("replace")
            modifications = ModificationsGFF(file, replace=replace)
            self.config.patches_gff.append(modifications)

            file_section_dict = CaseInsensitiveDict(self.ini[file_section_name])
            modifications.pop_tslpatcher_vars(file_section_dict, default_destination, default_source_folder)

            for key, value in file_section_dict.items():
                modifier: ModifyGFF | None

                lowercase_key: str = key.lower()
                if lowercase_key.startswith("addfield"):
                    next_gff_section: str | None = self.get_section_name(value)
                    if next_gff_section is None:
                        raise KeyError(SECTION_NOT_FOUND_ERROR.format(value) + REFERENCES_TRACEBACK_MSG.format(key, value, file_section_name))

                    next_section_dict = CaseInsensitiveDict(self.ini[next_gff_section])
                    modifier = self.add_field_gff(next_gff_section, next_section_dict)

                elif lowercase_key.startswith("2damemory"):
                    if value.lower() == "!fieldpath":
                        modifier = Memory2DAModifierGFF(
                            file,
                            PureWindowsPath(""),
                            dst_token_id=int(key[9:]),
                        )
                    elif value.lower().startswith("2damemory"):
                        modifier = Memory2DAModifierGFF(
                            file,
                            PureWindowsPath(""),
                            dst_token_id=int(key[9:]),
                            src_token_id=int(value[9:]),
                        )
                    else:
                        msg = f"Cannot parse '{key}={value}' in [{identifier}]. GFFList only supports 2DAMEMORY#=!FieldPath and 2DAMEMORY#=2DAMEMORY# assignments"
                        raise ValueError(msg)
                else:
                    modifier = self.modify_field_gff(file_section_name, key, value)

                modifications.modifiers.append(modifier)

    def load_compile_list(self):
        """Loads patches from the [CompileList] section of the ini file.

        Processing Logic:
        ----------------
            - Parses the [CompileList] section of the ini file into a dictionary
            - Sets a default destination from an optional key
            - Loops through each identifier/file pair
                - Creates a ModificationsNSS object
                - Looks for an optional section for the file
                - Passes any values to populate the patch
            - Adds each patch to the config patches list
        """
        compilelist_section: str | None = self.get_section_name("CompileList")
        if compilelist_section is None:
            self.log.add_note("[CompileList] section missing from ini.")
            return

        self.log.add_note("Loading [CompileList] patches from ini...")
        compilelist_section_dict = CaseInsensitiveDict(self.ini[compilelist_section])
        default_destination: str = compilelist_section_dict.pop("!DefaultDestination", ModificationsNSS.DEFAULT_DESTINATION)
        # !DefaultSourceFolder: Relative path from mod_path (which is typically the tslpatchdata folder) to source files.
        # Default value "." refers to mod_path itself (the tslpatchdata folder), not its parent.
        # For example: if mod_path = "C:/Mod/tslpatchdata", then:
        #   - !DefaultSourceFolder="." resolves to "C:/Mod/tslpatchdata"
        #   - !DefaultSourceFolder="scripts" resolves to "C:/Mod/tslpatchdata/scripts"
        default_source_folder = compilelist_section_dict.pop("!DefaultSourceFolder", ".")

        # Path resolution: mod_path / default_source_folder / "nwnnsscomp.exe"
        # mod_path is typically the tslpatchdata folder (parent of changes.ini).
        # If default_source_folder = ".", this resolves to mod_path itself (tslpatchdata folder).
        nwnnsscomp_exepath = self.mod_path / default_source_folder / "nwnnsscomp.exe"
        if not nwnnsscomp_exepath.is_file():
            nwnnsscomp_exepath = None if self.tslpatchdata_path is None else self.tslpatchdata_path / "nwnnsscomp.exe"  # TSLPatcher default

        for identifier, file in compilelist_section_dict.items():
            replace: bool = identifier.lower().startswith("replace")
            modifications = ModificationsNSS(file, replace)
            modifications.destination = default_destination
            modifications.sourcefolder = default_source_folder

            optional_file_section_name: str | None = self.get_section_name(file)
            if optional_file_section_name is not None:
                file_section_dict = CaseInsensitiveDict(self.ini[optional_file_section_name])
                modifications.pop_tslpatcher_vars(file_section_dict, default_destination, default_source_folder)

            assert isinstance(nwnnsscomp_exepath, Path), f"{type(nwnnsscomp_exepath).__name__}: {nwnnsscomp_exepath}"
            modifications.nwnnsscomp_path = nwnnsscomp_exepath
            self.config.patches_nss.append(modifications)

    def load_hack_list(self):  # noqa: C901, PLR0912
        """Loads [HACKList] patches from ini file into memory.

        Processing Logic:
        ----------------
            1. Gets the "[HACKList]" section name from the ini file
            2. Loops through each identifier and file in the section
            3. Creates a ModificationsNCS object for each file
            4. Populates the object with offset/value pairs from the file's section
            5. Adds the populated object to the config patches list
        """
        hacklist_section: str | None = self.get_section_name("HACKList")
        if hacklist_section is None:
            self.log.add_note("[HACKList] section missing from ini.")
            return

        self.log.add_note("Loading [HACKList] patches from ini...")
        hacklist_section_dict = CaseInsensitiveDict(self.ini[hacklist_section])
        default_destination: str = hacklist_section_dict.pop("!DefaultDestination", ModificationsNCS.DEFAULT_DESTINATION)
        # !DefaultSourceFolder: Relative path from mod_path (which is typically the tslpatchdata folder) to source files.
        # Default value "." refers to mod_path itself (the tslpatchdata folder), not its parent.
        # For example: if mod_path = "C:/Mod/tslpatchdata", then:
        #   - !DefaultSourceFolder="." resolves to "C:/Mod/tslpatchdata"
        #   - !DefaultSourceFolder="scripts" resolves to "C:/Mod/tslpatchdata/scripts"
        default_source_folder: str = hacklist_section_dict.pop("!DefaultSourceFolder", ".")

        # Process each NCS file in HACKList
        for identifier, filename in hacklist_section_dict.items():
            replace: bool = identifier.lower().startswith("replace")
            modifications = ModificationsNCS(filename, replace)

            # Get the file-specific section
            file_section_name: str | None = self.get_section_name(filename)
            if file_section_name is None:
                raise KeyError(SECTION_NOT_FOUND_ERROR.format(filename) + REFERENCES_TRACEBACK_MSG.format(identifier, filename, hacklist_section))

            file_section_dict = CaseInsensitiveDict(self.ini[file_section_name])
            modifications.pop_tslpatcher_vars(file_section_dict, default_destination, default_source_folder)

            # Parse all hack entries for this file
            self._parse_ncs_hack_entries(file_section_dict, modifications)

            # Add the completed modifications to config
            self.config.patches_ncs.append(modifications)

    def _parse_ncs_hack_entries(
        self,
        file_section_dict: CaseInsensitiveDict[str],
        modifications: ModificationsNCS,
    ):
        """Parse NCS hack entries from a file section and add them to modifications.

        Args:
        ----
            file_section_dict: Dictionary containing offset=value pairs from INI section
            modifications: ModificationsNCS object to populate with ModifyNCS objects
        """
        for offset_str, value_str in file_section_dict.items():
            # Parse offset (hex or decimal)
            if offset_str.lower().startswith("0x"):
                offset: int = int(offset_str, 16)
            else:
                offset = int(offset_str, 10)

            # Parse type specifier and value
            type_specifier: str = "u16"  # Default to 16-bit unsigned
            parsed_value: str = value_str
            if ":" in value_str:
                type_specifier, parsed_value = value_str.split(":", 1)

            lower_value: str = parsed_value.lower()

            # Create appropriate ModifyNCS based on value type
            modify_ncs: ModifyNCS = self._create_modify_ncs_from_value(
                offset=offset,
                value_str=parsed_value,
                lower_value=lower_value,
                type_specifier=type_specifier,
            )

            modifications.modifiers.append(modify_ncs)

    def _create_modify_ncs_from_value(
        self,
        offset: int,
        value_str: str,
        lower_value: str,
        type_specifier: str,
    ) -> ModifyNCS:
        """Create a ModifyNCS object from parsed INI value.

        Args:
        ----
            offset: Byte offset in NCS file
            value_str: Raw value string from INI
            lower_value: Lowercased value string for comparison
            type_specifier: Type specifier (u8, u16, u32)

        Returns:
        -------
            ModifyNCS: Configured modification object
        """
        if lower_value.startswith("strref"):
            # StrRef token reference
            value = self._parse_int_value(value_str[6:].strip())
            # Use STRREF32 for compatibility (handles both 16-bit and 32-bit cases)
            return ModifyNCS(NCSTokenType.STRREF32, offset, value)

        if lower_value.startswith("2damemory"):
            # 2DA memory token reference
            value = self._parse_int_value(value_str[9:].strip())
            # Use MEMORY_2DA32 for compatibility (handles both 16-bit and 32-bit cases)
            return ModifyNCS(NCSTokenType.MEMORY_2DA32, offset, value)

        # Direct integer values
        value = self._parse_int_value(value_str)

        if type_specifier == "u8":
            return ModifyNCS(NCSTokenType.UINT8, offset, value)
        if type_specifier == "u32":
            return ModifyNCS(NCSTokenType.UINT32, offset, value)
        # Default to u16
        return ModifyNCS(NCSTokenType.UINT16, offset, value)

    @staticmethod
    def _parse_int_value(value_str: str) -> int:
        """Parse an integer value from string (hex or decimal).

        Args:
        ----
            value_str: String representation of integer (may be hex with 0x prefix)

        Returns:
        -------
            int: Parsed integer value
        """
        if value_str.startswith("0x"):
            return int(value_str, 16)
        return int(value_str, 10)

    #################

    @classmethod
    def modify_field_gff(
        cls,
        identifier: str,
        key: str,
        str_value: str,
    ) -> ModifyFieldGFF:
        """Modifies a field in a GFF based on the key(path) and string value.

        Args:
        ----
            identifier: str - The section name (for logging purposes)
            key: str - The key of the field to modify
            string_value: str - The string value to set the field to.

        Returns:
        -------
            ModifyFieldGFF - A ModifyFieldGFF object representing the modification

        Processing Logic:
        ----------------
            1. Parses the string value into a FieldValue
            2. Handles special cases for keys containing "(strref)", "(lang)" or starting with "2damemory"
            3. Returns a ModifyFieldGFF object representing the modification.
        """
        value: FieldValue = cls.field_value_from_unknown(str_value)
        lower_key: str = key.lower()
        if "(strref)" in lower_key:
            value = FieldValueConstant(LocalizedStringDelta(value))
            key = key[: lower_key.index("(strref)")]

        elif "(lang" in lower_key:
            substring_id = int(key[lower_key.index("(lang") + 5 : -1])
            language, gender = LocalizedString.substring_pair(substring_id)
            locstring = LocalizedStringDelta()
            locstring.set_data(language, gender, str_value)
            value = FieldValueConstant(locstring)
            key = key[: lower_key.index("(lang")]

        elif lower_key.startswith("2damemory"):
            lower_str_value: str = str_value.lower()
            if lower_str_value != "!fieldpath" and not lower_str_value.startswith("2damemory"):
                msg = f"Cannot parse '{key}={value}' in [{identifier}]. GFFList only supports 2DAMEMORY#=!FieldPath assignments"
                raise ValueError(msg)
            value = FieldValueConstant(PureWindowsPath(""))  # no path at the root

        return ModifyFieldGFF(PureWindowsPath(key), value, identifier)

    def add_field_gff(  # noqa: C901
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
        -------
            ModifyGFF - Object containing the field modification

        Processing Logic:
        ----------------
            1. Determines the field type from the field type string
            2. Gets the label and optional value, path from the ini data
            3. Construct a current path from the gff root struct based on recursion level and path key.
            3. Handles nested modifiers and structs in lists
            4. Returns an AddFieldGFF or AddStructToListGFF object based on whether a label is provided.
        """
        # Parse required values
        raw_field_type: str = ini_data.pop("FieldType")
        label: str = ini_data.pop("Label").strip()

        # Resolve TSLPatcher -> PyKotor GFFFieldType
        field_type: GFFFieldType = self.resolve_tslpatcher_gff_field_type(raw_field_type)

        # Handle current GFF path
        raw_path: str = ini_data.pop("Path", "").strip()
        path: PureWindowsPath = PureWindowsPath(raw_path)
        if not path.name and current_path and current_path.name:  # use current recursion path if section doesn't override with Path=
            path = current_path
        if field_type == GFFFieldType.Struct:
            path /= ">>##INDEXINLIST##<<"

        modifiers: list[ModifyGFF] = []
        index_in_list_token = None

        for key, iterated_value in ini_data.items():
            lower_key: str = key.lower()
            if lower_key.startswith("2damemory"):
                lower_iterated_value: str = iterated_value.lower()
                if lower_iterated_value == "listindex":
                    index_in_list_token = int(key[9:])
                elif lower_iterated_value == "!fieldpath":
                    modifier = Memory2DAModifierGFF(identifier, dst_token_id=int(key[9:]), path=path / label)  # Assign current path to 2damemory.
                    modifiers.insert(0, modifier)
                elif lower_iterated_value.startswith("2damemory"):
                    modifier = Memory2DAModifierGFF(
                        identifier, dst_token_id=int(key[9:]), src_token_id=int(iterated_value[9:]), path=path
                    )  # Assign field at path to a value or (path to field's value)
                    modifiers.insert(0, modifier)

            # Handle nested AddField's and recurse
            if lower_key.startswith("addfield"):
                next_section_name: str | None = self.get_section_name(iterated_value)
                if next_section_name is None:
                    raise KeyError(SECTION_NOT_FOUND_ERROR.format(iterated_value) + REFERENCES_TRACEBACK_MSG.format(key, iterated_value, identifier))

                next_nested_section = CaseInsensitiveDict(self.ini[next_section_name])
                nested_modifier: ModifyGFF = self.add_field_gff(
                    identifier=next_section_name,
                    ini_data=next_nested_section,
                    current_path=path / label,
                )

                modifiers.append(nested_modifier)

        # get AddField value based on this recursion level
        value: FieldValue = self._get_addfield_value(ini_data, field_type, identifier)

        # Check if label unset to determine if current ini section is a struct inside a list.
        if not label and field_type == GFFFieldType.Struct:
            return AddStructToListGFF(identifier, value, path, index_in_list_token, modifiers)

        # if field_type == GFFFieldType.Struct:  # not sure if this is invalid syntax or not.
        #     msg = f"Label={label} cannot be used when FieldType={GFFFieldType.Struct.value}. Error happened in [{identifier}] section in ini."
        #     raise ValueError(msg)
        if not label:
            msg = f"Label must be set for {field_type!r} (FieldType={field_type.value}). Error happened in [{identifier}] section in ini."
            raise ValueError(msg)
        return AddFieldGFF(identifier, label, field_type, value, path, modifiers)

    @classmethod
    def _get_addfield_value(
        cls,
        ini_section_dict: CaseInsensitiveDict[str],
        field_type: GFFFieldType,
        identifier: str,
    ) -> FieldValue:
        """Gets the value for an addfield from an ini section dictionary.

        Args:
        ----
            ini_section_dict: {CaseInsensitiveDict}: The section of the ini, as a dict.
            field_type: {GFFFieldType}: The field type of this addfield section.
            identifier: {str}: The name identifier for the section

        Returns:
        -------
            value: {FieldValue | None}: The parsed field value or None

        Processing Logic:
        ----------------
            - Parses the "Value" key to get a raw value and parses it based on field type
            - For LocalizedString, see field_value_from_localized_string
            - For GFFList and GFFStruct, constructs empty instances to be filled in later - see pykotor/tslpatcher/mods/gff.py
            - Returns None if value cannot be parsed or field type not supported (config err)
        """
        value: FieldValue | None = None

        raw_value: str | None = ini_section_dict.pop("Value", None)
        if raw_value is not None:
            ret_value: FieldValue | None = cls.field_value_from_type(raw_value, field_type)
            if ret_value is None:
                msg = f"Could not parse fieldtype '{field_type.name}' in GFFList section [{identifier}]"
                raise ValueError(msg)
            value = ret_value

        elif field_type == GFFFieldType.LocalizedString:
            value = cls.field_value_from_localized_string(ini_section_dict)

        elif field_type == GFFFieldType.List:
            value = FieldValueConstant(GFFList())

        elif field_type == GFFFieldType.Struct:
            raw_struct_id: str = ini_section_dict.pop("TypeId", "0").strip()  # 0 is the default struct id.
            if not is_int(raw_struct_id):
                if raw_struct_id.lower() == "listindex":
                    return FieldValueListIndex(raw_struct_id.lower())
                msg = f"Invalid TypeId: expected int (or 'listindex' literal) but got '{raw_struct_id}' in [{identifier}]"
                raise ValueError(msg)
            struct_id = int(raw_struct_id)
            value = FieldValueConstant(GFFStruct(struct_id))

        if value is None:
            msg = f"Could not find valid field return type in [{identifier}] matching field type '{field_type.name}'"
            raise ValueError(msg)

        return value

    @classmethod
    def field_value_from_localized_string(
        cls,
        ini_section_dict: CaseInsensitiveDict,
    ) -> FieldValueConstant:
        """Parses a localized string from an INI section dictionary (usually a GFF section).

        Args:
        ----
            ini_section_dict: CaseInsensitiveDict containing localized string data

        Returns:
        -------
            FieldValueConstant: Parsed TSLPatcher localized string

        Processing Logic:
        ----------------
            1. Pop the "StrRef" key to get the base string reference
            2. Lookup the string reference from memory or use it as-is if not found
            3. Iterate the keys, filtering for language codes
            4. Extract the language, gender and text from each key/value
            5. Normalize the text and set it in the string delta
            6. Return a FieldValueConstant containing the parsed string delta.
        """
        raw_stringref: str = ini_section_dict.pop("StrRef")
        stringref: FieldValue = cls.field_value_from_memory(raw_stringref) or FieldValueConstant(int(raw_stringref))
        l_string_delta = LocalizedStringDelta(stringref)

        for substring, text in ini_section_dict.items():
            if not substring.lower().startswith("lang"):
                continue

            substring_id = int(substring[4:])
            language, gender = l_string_delta.substring_pair(substring_id)
            formatted_text: str = cls.normalize_tslpatcher_crlf(text)
            l_string_delta.set_data(language, gender, formatted_text)

        return FieldValueConstant(l_string_delta)

    @staticmethod
    def field_value_from_memory(raw_value: str) -> FieldValue | None:
        """Extract field value from memory reference string.

        Args:
        ----
            raw_value: String value to parse

        Returns:
        -------
            FieldValue | None: FieldValue object or None

        Processing Logic:
        ----------------
            - Lowercase the raw value string
            - Check if it starts with "strref" and extract token ID
            - Check if it starts with "2damemory" and extract token ID
            - Return FieldValue memory object with token ID, or None if no match
        """
        lower_value: str = raw_value.lower()

        if lower_value.startswith("strref"):
            token_id = int(raw_value[6:])
            return FieldValueTLKMemory(token_id)

        if lower_value.startswith("2damemory"):
            token_id = int(raw_value[9:])
            return FieldValue2DAMemory(token_id)

        return None

    @staticmethod
    def field_value_from_unknown(  # noqa: PLR0911
        raw_value: str,
    ) -> FieldValue:
        """Extracts a field value from an unknown string representation.

            This section determines how to parse ini key/value pairs in gfflist such as:
                EntryList/0/RepliesList/0/TypeId=5

        Args:
        ----
            string_value: The string to parse.

        Returns:
        -------
            FieldValue: The parsed value represented as a FieldValue object.

        Processing Logic:
        ----------------
            - Checks if the value is already cached in memory
            - Tries to parse as int if possible
            - Otherwise parses as float by normalizing the string
            - Checks for Vector3 or Vector4 by counting pipe separators
            - Falls back to returning as string if no other type matches
            - Returns a FieldValueConstant wrapping the extracted value
        """
        # StrRef or 2DAMemory
        field_value_memory: FieldValue | None = ConfigReader.field_value_from_memory(raw_value)
        if field_value_memory is not None:
            return field_value_memory

        # Int
        if is_int(raw_value):
            return FieldValueConstant(int(raw_value))

        # Float
        parsed_float_str: str = ConfigReader.normalize_tslpatcher_float(raw_value)
        if is_float(parsed_float_str):  # float
            return FieldValueConstant(float(parsed_float_str))

        num_pipe_seps: int = raw_value.count("|")

        # String
        if not num_pipe_seps:
            return FieldValueConstant(ConfigReader.normalize_tslpatcher_crlf(raw_value))

        # Vector
        not_a_vector: bool = False
        components: list[float] = []
        for x in parsed_float_str.split("|"):
            if is_float(x):
                components.append(float(x))
                continue
            not_a_vector = True
            break

        # String containing the character '|'
        if not_a_vector:
            return FieldValueConstant(ConfigReader.normalize_tslpatcher_crlf(raw_value))

        # Three floats
        if num_pipe_seps == 2:  # noqa: PLR2004
            return FieldValueConstant(Vector3(*components))

        # Four floats
        if num_pipe_seps == 3:  # noqa: PLR2004
            return FieldValueConstant(Vector4(*components))

        msg = f"Cannot determine type/value from '{raw_value}'"
        raise ValueError(msg)

    @staticmethod
    def field_value_from_type(  # noqa: C901, PLR0912
        raw_value: str,
        field_type: GFFFieldType,
    ) -> FieldValue | None:
        # sourcery skip: assign-if-exp, reintroduce-else
        """Extracts field value from raw string based on field type.

        Args:
        ----
            raw_value (str): {Raw string value from file}
            field_type (GFFFieldType): {Field type enum}.

        Returns:
        -------
            FieldValue: {Field value object}

        Processing Logic:
        ----------------
            - Checks if value already exists in memory as a 2DAMEMORY or StrRef
            - Otherwise, converts raw_value to appropriate type based on field_type
            - Returns FieldValueConstant object wrapping extracted value.
        """
        field_value_memory: FieldValue | None = ConfigReader.field_value_from_memory(raw_value)
        if field_value_memory is not None:
            return field_value_memory

        components: list[float]
        value: ResRef | str | int | float | Vector3 | Vector4 | bytes | None = None

        if field_type.return_type() is ResRef:
            value = ResRef(raw_value)

        elif field_type.return_type() is str:
            value = ConfigReader.normalize_tslpatcher_crlf(raw_value)

        elif issubclass(field_type.return_type(), int):
            value = int(raw_value)

        elif issubclass(field_type.return_type(), float):
            value = float(ConfigReader.normalize_tslpatcher_float(raw_value))

        elif field_type.return_type() is Vector3:
            components = [float(ConfigReader.normalize_tslpatcher_float(axis)) for axis in raw_value.split("|")]
            value = Vector3(*components)

        elif field_type.return_type() is Vector4:
            components = [float(ConfigReader.normalize_tslpatcher_float(axis)) for axis in raw_value.split("|")]
            value = Vector4(*components)

        elif field_type.return_type() is bytes:
            if not raw_value.strip().replace("1", "").replace("0", ""):
                value = bytes(int(raw_value[i : i + 8], 2) for i in range(0, len(raw_value), 8))
            elif raw_value.strip().lower().startswith("0x"):
                hex_string: str = raw_value[2:]
                if len(hex_string) % 2:
                    hex_string = f"0{hex_string}"
                value = bytes.fromhex(hex_string.strip())
            else:
                try:
                    value = base64.b64decode(raw_value)
                except Exception as e:  # noqa: BLE001
                    raise ValueError(f"The raw value for the binary field specified was invalid: '{raw_value}'") from e

        if value is None:
            return None

        return FieldValueConstant(value)

    #################

    def discern_2da(
        self,
        key: str,
        identifier: str,
        modifiers: CaseInsensitiveDict[str],
    ) -> Modify2DA | None:
        """Determines the type of 2DA modification based on the key.

        Args:
        ----
            key: str - The key identifying the type of modification
            identifier: str - The identifier of the 2DA (section name)
            modifiers: CaseInsensitiveDict[str] - Additional parameters for the modification

        Returns:
        -------
            Modify2DA | None - The 2DA modification object or None

        Processing Logic:
        ----------------
            - Parses the key to determine modification type
            - Checks for required parameters
            - Constructs the appropriate modification object
            - Returns the modification object or None.
        """
        exclusive_column: str | None
        target: Target | None
        row_label: str | None
        cells: dict[str, RowValue]
        store_2da: dict[int, RowValue]
        store_tlk: dict[int, RowValue]

        modification: Modify2DA | None = None
        lowercase_key: str = key.lower()

        if lowercase_key.startswith("changerow"):
            target = self.target_2da(identifier, modifiers)
            if target is None:
                return None
            cells, store_2da, store_tlk = self.cells_2da(identifier, modifiers)
            modification = ChangeRow2DA(identifier, target, cells, store_2da, store_tlk)

        elif lowercase_key.startswith("addrow"):
            exclusive_column = modifiers.pop("ExclusiveColumn", None)
            row_label = self.row_label_2da(identifier, modifiers)
            cells, store_2da, store_tlk = self.cells_2da(identifier, modifiers)
            modification = AddRow2DA(identifier, exclusive_column, row_label, cells, store_2da, store_tlk)

        elif lowercase_key.startswith("copyrow"):
            target = self.target_2da(identifier, modifiers)
            if not target:
                return None
            exclusive_column = modifiers.pop("ExclusiveColumn", None)
            row_label = self.row_label_2da(identifier, modifiers)
            cells, store_2da, store_tlk = self.cells_2da(identifier, modifiers)
            modification = CopyRow2DA(identifier, target, exclusive_column, row_label, cells, store_2da, store_tlk)

        elif lowercase_key.startswith("addcolumn"):
            modification = self._read_add_column(modifiers, identifier)

        else:
            msg = f"Could not parse key '{key}={identifier}', expecting one of ['ChangeRow=', 'AddColumn=', 'AddRow=', 'CopyRow=']"
            raise KeyError(msg)

        return modification

    def _read_add_column(
        self,
        modifiers: CaseInsensitiveDict[str],
        identifier: str,
    ) -> AddColumn2DA:
        """Loads the add new column to be added to the 2D array.

        Args:
        ----
            modifiers: CaseInsensitiveDict[str]: Dictionary of column modifiers.
            identifier: str: Identifier of the column.

        Returns:
        -------
            AddColumn2DA: Object containing details of added column.

        Processing Logic:
        ----------------
            - Pop 'ColumnLabel' and 'DefaultValue' from modifiers dict
            - Raise error if 'ColumnLabel' or 'DefaultValue' is missing
            - Call column_inserts_2da() to get insert details
            - Return AddColumn2DA object
        """
        header: str | None = modifiers.pop("ColumnLabel", None)
        if header is None:
            msg = f"Missing 'ColumnLabel' in [{identifier}]"
            raise KeyError(msg)
        default: str | None = modifiers.pop("DefaultValue", None)
        if default is None:
            msg = f"Missing 'DefaultValue' in [{identifier}]"
            raise KeyError(msg)
        default = default if default != "****" else ""

        index_insert: dict[int, RowValue]
        label_insert: dict[str, RowValue]
        store_2da: dict[int, str]

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

    def target_2da(
        self,
        identifier: str,
        modifiers: CaseInsensitiveDict[str],
    ) -> Target | None:
        """Gets or creates a 2D target from modifiers.

        Args:
        ----
            identifier: str - Identifier for target
            modifiers: CaseInsensitiveDict[str] - Modifiers dictionary

        Returns:
        -------
            Target | None: Target object or None

        Processing Logic:
        ----------------
            - Checks for RowIndex, RowLabel or LabelIndex key
            - Calls get_target() to create Target object
            - Returns None if no valid key found with warning
        """

        def get_target(
            target_type: TargetType,
            key: str,
            *,
            is_int: bool = False,
        ) -> Target:
            raw_value: str | None = modifiers.pop(key, None)
            if raw_value is None:
                msg = f"[2DAList] parse error: '{key}' missing from [{identifier}] in ini."
                raise ValueError(msg)
            lower_raw_value = raw_value.lower()
            if lower_raw_value.startswith("strref") and len(raw_value) > len("strref") and raw_value[6:].isdigit():
                value: str | int | RowValue2DAMemory | RowValueTLKMemory = RowValueTLKMemory(int(raw_value[6:]))
            elif lower_raw_value.startswith("2damemory") and len(raw_value) > len("2damemory") and raw_value[9:].isdigit():
                value = RowValue2DAMemory(int(raw_value[9:]))
            else:
                value = int(raw_value) if is_int else raw_value
            return Target(target_type, value)

        if "RowIndex" in modifiers:
            return get_target(TargetType.ROW_INDEX, "RowIndex", is_int=True)
        if "RowLabel" in modifiers:
            return get_target(TargetType.ROW_LABEL, "RowLabel")
        if "LabelIndex" in modifiers:
            return get_target(TargetType.LABEL_COLUMN, "LabelIndex")

        self.log.add_warning(f"No line set to be modified in [{identifier}].")
        return None

    def cells_2da(  # noqa: C901
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
            tuple[dict[str, RowValue], dict[int, RowValue], dict[int, RowValue]] - tuple containing cells dictionary, 2DA store dictionary, TLK store dictionary

        Processing Logic:
        ----------------
            1. Loops through each modifier and value
            2. Determines modifier type (cell, 2DA store, TLK store, row label)
            3. Creates appropriate RowValue for cell/store value
            4. Adds cell/store value to return dictionaries
        """
        cells: dict[str, RowValue] = {}
        store_2da: dict[int, RowValue] = {}
        store_tlk: dict[int, RowValue] = {}

        for modifier, value in modifiers.items():
            lower_modifier: str = modifier.lower().strip()
            lower_value: str = value.lower()

            is_store_2da: bool = lower_modifier.startswith("2damemory") and len(lower_modifier) > len("2damemory") and modifier[len("2damemory") :].isdigit()
            is_store_tlk: bool = modifier.startswith("strref") and len(lower_modifier) > len("strref") and modifier[len("strref") :].isdigit()
            is_row_label: bool = lower_modifier in {"rowlabel", "newrowlabel"}

            row_value: RowValue | None = None
            if lower_value.startswith("2damemory"):
                token_id = int(value[len("2damemory") :])
                row_value = RowValue2DAMemory(token_id)
            elif lower_value.startswith("strref"):
                token_id = int(value[len("strref") :])
                row_value = RowValueTLKMemory(token_id)
            elif lower_value == "high()":
                row_value = RowValueHigh(None) if modifier == "rowlabel" else RowValueHigh(modifier)
            elif lower_value == "rowindex":
                row_value = RowValueRowIndex()
            elif lower_value == "rowlabel":
                row_value = RowValueRowLabel()
            elif is_store_2da or is_store_tlk:
                row_value = RowValueRowCell(value)
            elif value == "****":
                row_value = RowValueConstant("")
            else:
                row_value = RowValueConstant(value)

            if is_store_2da:
                token_id = int(modifier[len("2damemory") :])
                store_2da[token_id] = row_value
            elif is_store_tlk:
                token_id = int(modifier[len("strref") :])
                store_tlk[token_id] = row_value
            elif not is_row_label:
                cells[modifier] = row_value

        return cells, store_2da, store_tlk

    def row_label_2da(
        self,
        identifier: str,
        modifiers: CaseInsensitiveDict[str],
    ) -> str | None:
        """Returns the row label for a 2D array based on modifiers.

        Args:
        ----
            identifier: Identifier for the 2D array
            modifiers: CaseInsensitiveDict of modifiers for the 2D array

        Returns:
        -------
            str | None: The row label or None if not found

        Processing Logic:
        ----------------
            - Check if 'RowLabel' exists as a key in modifiers
            - If not present, check if 'NewRowLabel' exists as a key
            - Return the value of the key if present, else return None.
        """
        return modifiers.pop(
            "RowLabel",
            modifiers.pop("NewRowLabel", None),
        )

    def column_inserts_2da(
        self,
        identifier: str,
        modifiers: CaseInsensitiveDict[str],
    ) -> tuple[dict[int, RowValue], dict[str, RowValue], dict[int, str]]:
        """Extracts specific 2DA patch information from the ini.

        Args:
        ----
            identifier: str - Section name being handled
            modifiers: CaseInsensitiveDict[str] - Modifiers to insert values

        Returns:
        -------
            tuple[dict[int, RowValue], dict[str, RowValue], dict[int, str]] - Index inserts, label inserts, 2DA store

        Processes Logic:
        ---------------
            - Loops through modifiers and extracts value type
            - Assigns row value based on value type
            - Inserts into appropriate return dictionary based on modifier key
            - Returns tuple of inserted values dictionaries.
        """
        index_insert: dict[int, RowValue] = {}
        label_insert: dict[str, RowValue] = {}
        store_2da: dict[int, str] = {}

        for modifier, value in modifiers.items():
            modifier_lowercase: str = modifier.lower()
            value_lowercase: str = value.lower()

            is_store_2da: bool = value_lowercase.startswith("2damemory")
            is_store_tlk: bool = value_lowercase.startswith("strref")

            row_value: RowValue | None = None
            if is_store_2da:
                token_id = int(value[len("2damemory") :])
                row_value = RowValue2DAMemory(token_id)
            elif is_store_tlk:
                token_id = int(value[len("strref") :])
                row_value = RowValueTLKMemory(token_id)
            else:
                row_value = RowValueConstant(value)

            if modifier_lowercase.startswith("i"):
                index = int(modifier[1:])
                index_insert[index] = row_value
            elif modifier_lowercase.startswith("l"):
                label: str = modifier[1:]
                label_insert[label] = row_value
            elif modifier_lowercase.startswith("2damemory"):
                token_id = int(modifier[len("2damemory") :])
                store_2da[token_id] = value

        return index_insert, label_insert, store_2da

    #################

    @staticmethod
    def normalize_tslpatcher_float(
        value_str: str,
    ) -> str:
        """Normalize a float value string by replacing commas with periods.

        Args:
        ----
            value_str: String value to normalize

        Returns:
        -------
            str: Normalized string value with commas replaced with periods
        """
        return value_str.replace(",", ".")

    @staticmethod
    def normalize_tslpatcher_crlf(
        value_str: str,
    ) -> str:
        r"""Normalize line endings in a string value.

        Args:
        ----
            value_str: String value to normalize line endings

        Returns:
        -------
            str: String with normalized line endings

        Processes line endings:
            - Replaces "<#LF#>" with "\n"
            - Replaces "<#CR#>" with "\r"
            - Returns string with all line endings normalized
        """
        return value_str.replace("<#LF#>", "\n").replace("<#CR#>", "\r")

    @staticmethod
    def resolve_tslpatcher_ssf_sound(
        name: str,
    ) -> SSFSound:
        """Resolves a config string to an SSFSound enum value.

        Args:
        ----
            name (str): The config string name

        Returns:
        -------
            SSFSound: The resolved SSFSound enum value

        Processing Logic:
        ----------------
            - Defines a CaseInsensitiveDict mapping config strings to SSFSound enum values
            - Looks up the provided name in the dict and returns the corresponding SSFSound value.
        """
        configstr_to_ssfsound = CaseInsensitiveDict(
            {
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
            }.items(),
        )
        return configstr_to_ssfsound[name]

    @staticmethod
    def resolve_tslpatcher_gff_field_type(
        field_type_num_str: str,
    ) -> GFFFieldType:
        """Resolves a TSLPatcher GFF field type to a PyKotor GFFFieldType enum.

        Use this function to work with the ini's FieldType= values in PyKotor.

        Args:
        ----
            field_type_num_str: {String containing the field type number}.

        Returns:
        -------
            GFFFieldType: {The GFFFieldType enum value corresponding to the input string}

        Processing Logic:
        ----------------
            - Defines a dictionary mapping field type number strings to GFFFieldType enum values
            - Looks up the input string in the dictionary
            - Returns the corresponding GFFFieldType value.
        """
        fieldname_to_fieldtype = CaseInsensitiveDict(
            {
                "Binary": GFFFieldType.Binary,  # HoloPatcher only.
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
