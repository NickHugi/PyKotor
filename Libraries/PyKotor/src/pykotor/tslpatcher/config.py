from __future__ import annotations

from configparser import ConfigParser
from enum import IntEnum
from typing import TYPE_CHECKING

from pykotor.tslpatcher.mods.tlk import ModificationsTLK
from pykotor.tslpatcher.namespaces import PatcherNamespace
from pykotor.tslpatcher.reader import ConfigReader

if TYPE_CHECKING:
    import os

    from pykotor.tools.path import CaseAwarePath
    from pykotor.tslpatcher.logger import PatchLogger
    from pykotor.tslpatcher.mods.gff import ModificationsGFF
    from pykotor.tslpatcher.mods.install import InstallFile
    from pykotor.tslpatcher.mods.ncs import ModificationsNCS
    from pykotor.tslpatcher.mods.nss import ModificationsNSS
    from pykotor.tslpatcher.mods.ssf import ModificationsSSF
    from pykotor.tslpatcher.mods.twoda import Modifications2DA


class LogLevel(IntEnum):
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
    def __init__(self) -> None:
        self.window_title: str = ""
        self.confirm_message: str = ""
        self.game_number: int | None = None

        self.required_file: str | None = None
        self.required_message: str = ""

        # optional hp features
        self.ignore_file_extensions: bool = False

        self.install_list: list[InstallFile] = []
        self.patches_2da: list[Modifications2DA] = []
        self.patches_gff: list[ModificationsGFF] = []
        self.patches_ssf: list[ModificationsSSF] = []
        self.patches_nss: list[ModificationsNSS] = []
        self.patches_ncs: list[ModificationsNCS] = []
        self.patches_tlk: ModificationsTLK = ModificationsTLK()

    def load(self, ini_text: str, mod_path: os.PathLike | str, logger: PatchLogger | None = None) -> None:
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
        from pykotor.tslpatcher.reader import ConfigReader

        ini = ConfigParser(
            delimiters=("="),
            allow_no_value=True,
            strict=False,
            interpolation=None,
        )
        # use case-sensitive keys
        ini.optionxform = lambda optionstr: optionstr  #  type: ignore[method-assign]
        ini.read_string(ini_text)

        ConfigReader(ini, mod_path, logger).load(self)

    def as_namespace(self, filepath: CaseAwarePath) -> PatcherNamespace:
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
        reader = ConfigReader.from_filepath(filepath)
        reader.load_settings()

        namespace = PatcherNamespace.from_default()
        namespace.name = reader.config.window_title
        if not namespace.name:
            try:
                namespace.name = filepath.parent.parent.name.strip() or "<< Untitled Mod Loaded >>"
            except Exception:  # noqa: BLE001
                namespace.name = "<< Untitled Mod Loaded >>"

        return namespace

    def patch_count(self) -> int:
        return (
            len(self.patches_2da)
            + len(self.patches_gff)
            + len(self.patches_ssf)
            + len(self.patches_tlk.modifiers)
            + len(self.install_list)
            + len(self.patches_nss)
        )
