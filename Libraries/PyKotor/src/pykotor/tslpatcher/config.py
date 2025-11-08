from __future__ import annotations

from configparser import ConfigParser
from copy import copy
from enum import IntEnum
from typing import TYPE_CHECKING

from pykotor.tslpatcher.mods.gff import AddFieldGFF, AddStructToListGFF, Memory2DAModifierGFF
from pykotor.tslpatcher.mods.tlk import ModificationsTLK
from pykotor.tslpatcher.namespaces import PatcherNamespace

if TYPE_CHECKING:
    import os

    from pykotor.tools.path import CaseAwarePath
    from pykotor.tslpatcher.logger import PatchLogger
    from pykotor.tslpatcher.mods.gff import ModificationsGFF, ModifyGFF
    from pykotor.tslpatcher.mods.install import InstallFile
    from pykotor.tslpatcher.mods.ncs import ModificationsNCS
    from pykotor.tslpatcher.mods.nss import ModificationsNSS
    from pykotor.tslpatcher.mods.ssf import ModificationsSSF
    from pykotor.tslpatcher.mods.twoda import Modifications2DA


class LogLevel(IntEnum):  # TODO(th3w1zard1): implement into HoloPatcher
    # Docstrings taken from ChangeEdit docs

    NOTHING = 0
    """No feedback at all. The text from "info.rtf" will continue to be displayed during installation"""

    GENERAL = 1
    """Only general progress information will be displayed. Not recommended."""

    ERRORS = 2
    """General progress information is displayed, along with any serious errors encountered."""

    WARNINGS = 3
    """General progress information, serious errors and warnings are displayed. This is
    recommended for the release version of your mod."""

    FULL = 4
    """Full feedback. On top of what is displayed at level 3, it also shows verbose progress
    information that may be useful for a Modder to see what is happening. Intended for
    Debugging."""


class PatcherConfig:
    def __init__(self):
        self.window_title: str = ""
        self.confirm_message: str = ""
        self.game_number: int | None = None

        self.required_files: list[tuple[str, ...]] = []
        self.required_messages: list[str] = []
        self.save_processed_scripts: int = 0
        self.log_level: LogLevel = LogLevel.WARNINGS

        self.install_list: list[InstallFile] = []
        self.patches_2da: list[Modifications2DA] = []
        self.patches_gff: list[ModificationsGFF] = []
        self.patches_ssf: list[ModificationsSSF] = []
        self.patches_nss: list[ModificationsNSS] = []
        self.patches_ncs: list[ModificationsNCS] = []
        self.patches_tlk: ModificationsTLK = ModificationsTLK()

        # optional hp features
        self.ignore_file_extensions: bool = False

    def load(
        self,
        ini_text: str,
        mod_path: os.PathLike | str,
        logger: PatchLogger | None = None,
        tslpatchdata_path: os.PathLike | str | None = None,
    ):
        """Loads configuration from a TSLPatcher changes ini text string.

        Args:
        ----
            ini_text: The ini text string to load configuration from.
            mod_path: The path to the mod being configured.
            logger: Optional logger for logging messages.

        Processing Logic:
        ----------------
            - Parse the ini text string into a ConfigParser object
            - Initialize a ConfigReader with the ConfigParser and pass it the mod path and logger
            - Set the ConfigParser to use case-insensitive keys. Ini is inherently case-insensitive by default.
            - Call the load method on the ConfigReader, passing self to populate the configuration instance.
        """
        from pykotor.tslpatcher.reader import ConfigReader  # noqa: PLC0415  Prevent circular imports.

        ini = ConfigParser(
            delimiters=("="),
            allow_no_value=True,
            strict=False,
            interpolation=None,
            inline_comment_prefixes=(";", "#"),
        )

        ini.optionxform = lambda optionstr: optionstr  # type: ignore[method-assign]  # use case-sensitive keys
        ini.read_string(ini_text)

        ConfigReader(ini, mod_path, logger, tslpatchdata_path).load(self)

    @classmethod
    def as_namespace(
        cls,
        filepath: CaseAwarePath,
    ) -> PatcherNamespace:
        """Builds a changes.ini file as PatcherNamespace object.

        When a changes.ini is loaded when no namespaces.ini is created, we create a namespace internally with this single entry.

        Args:
        ----
            filepath: CaseAwarePath - Path to the config file

        Returns:
        -------
            PatcherNamespace - Namespace containing the mod info.

        Processing Logic:
        ----------------
            - Loads settings from the config file at the given filepath
            - Creates a PatcherNamespace object
            - Sets the ini_filename, info_filename and name attributes from the config
            - Returns the populated PatcherNamespace
        """
        from pykotor.tslpatcher.reader import ConfigReader  # noqa: PLC0415  Prevent circular imports.

        reader: ConfigReader = ConfigReader.from_filepath(filepath)
        reader.load_settings()

        namespace: PatcherNamespace = PatcherNamespace.from_default()
        namespace.name = reader.config.window_title or filepath.parents[1].name.strip() or "<< Untitled Mod Loaded >>"

        return namespace

    def get_nested_gff_patches(
        self,
        arg_gff_modifier: AddFieldGFF | AddStructToListGFF,
    ) -> list[ModifyGFF]:
        nested_modifiers: list[ModifyGFF] = copy(arg_gff_modifier.modifiers)
        for gff_modifier in nested_modifiers:
            if isinstance(gff_modifier, (AddFieldGFF, AddStructToListGFF)):
                nested_modifiers.extend(self.get_nested_gff_patches(gff_modifier))
        return nested_modifiers

    def flatten_gff_patches(self) -> list[ModifyGFF]:
        flattened_gff_patches: list[ModifyGFF] = []
        for gff_patch in self.patches_gff:
            for gff_modifier in gff_patch.modifiers:
                is_memory_modifier: bool = isinstance(gff_modifier, Memory2DAModifierGFF)
                if not is_memory_modifier:
                    flattened_gff_patches.append(gff_modifier)

                # Only AddFieldGFF and AddStructToListGFF have modifiers attribute
                if isinstance(gff_modifier, (AddFieldGFF, AddStructToListGFF)):
                    modifier_with_nested: AddFieldGFF | AddStructToListGFF = gff_modifier
                    if modifier_with_nested.modifiers:
                        nested_modifiers = self.get_nested_gff_patches(modifier_with_nested)
                        # nested modifiers will reference the item from the flattened list.
                        modifier_with_nested.modifiers = nested_modifiers
                        flattened_gff_patches.extend(nested_modifiers)
        return flattened_gff_patches

    def patch_count(self) -> int:
        num_2da_patches: int = sum(len(twoda_patch.modifiers) for twoda_patch in self.patches_2da)
        num_gff_patches: int = len(self.flatten_gff_patches())
        num_ssf_patches: int = sum(len(ssf_patch.modifiers) for ssf_patch in self.patches_ssf)
        num_tlk_patches: int = len(self.patches_tlk.modifiers)
        num_install_list_patches: int = len(self.install_list)
        num_nss_patches: int = len(self.patches_nss)
        num_ncs_patches: int = len(self.patches_ncs)

        return (
            num_2da_patches
            + num_gff_patches
            + num_ssf_patches
            + num_tlk_patches
            + num_install_list_patches
            + num_nss_patches
            + num_ncs_patches
        )
