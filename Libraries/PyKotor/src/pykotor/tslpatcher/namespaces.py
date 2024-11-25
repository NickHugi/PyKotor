from __future__ import annotations

from pathlib import PurePath
from typing import ClassVar


class PatcherNamespace:
    DEFAULT_INI_FILENAME: ClassVar[str] = "changes.ini"
    DEFAULT_INFO_FILENAME: ClassVar[str] = "info.rtf"

    def __init__(
        self,
        ini_filename: str,
        info_filename: str,
    ):
        """Initialize configuration from ini and info files.

        Args:
        ----
            ini_filename: str - Filename of ini configuration file
            info_filename: str - Filename of info configuration file

        Processing Logic:
        ----------------
            - Read namespace id, data folder path, name and description from ini file
            - Read name and description from info file if not present in ini file
            - Initialize attributes with values read from files.
        """
        self.namespace_id: str = ""
        self.ini_filename: str = ini_filename.strip() or self.DEFAULT_INI_FILENAME
        self.info_filename: str = info_filename.strip() or self.DEFAULT_INFO_FILENAME
        self.data_folderpath: PurePath = PurePath()
        self.name: str = ""
        self.description: str = ""

    @classmethod
    def from_default(cls):
        """Creates a PatcherNamespace instance using default fields.

        Args:
        ----
            cls: The PatcherNamespace class

        Returns:
        -------
            PatcherNamespace: A PatcherNamespace instance initialized with default filenames

        Creates an instance initialized with default filenames for the ini and info files stored as class attributes:
            - Gets the default ini filename from the class attribute DEFAULT_INI_FILENAME
            - Gets the default info filename from the class attribute DEFAULT_INFO_FILENAME
            - Initializes a new PatcherNamespace instance with these filenames
            - Returns the new PatcherNamespace instance.
        """
        return cls(cls.DEFAULT_INI_FILENAME, cls.DEFAULT_INFO_FILENAME)

    def __str__(self) -> str:
        return self.name

    def changes_filepath(self) -> PurePath:
        return self.data_folderpath / self.ini_filename

    def rtf_filepath(self) -> PurePath:
        return self.data_folderpath / self.info_filename
