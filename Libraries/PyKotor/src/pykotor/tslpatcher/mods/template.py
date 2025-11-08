from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]

    from pykotor.common.misc import Game
    from pykotor.resource.type import SOURCE_TYPES
    from pykotor.tslpatcher.logger import PatchLogger
    from pykotor.tslpatcher.memory import PatcherMemory
    from utility.common.more_collections import CaseInsensitiveDict


class OverrideType:
    """Possible actions for how the patcher should behave when patching a file to a ERF/MOD/RIM while that filename already exists in the Override folder."""

    IGNORE = "ignore"  # Do nothing: don't even check (TSLPatcher default)
    WARN = "warn"  # Log a warning (HoloPatcher default)
    RENAME = "rename"  # Rename the file in the Override folder with the 'old_' prefix. Also logs a warning.


class PatcherModifications(ABC):
    """Abstract base class for TSLPatcher modifications.

    Args:
    ----
        sourcefile (str): The source file for the modifications.
        replace (bool | None, optional): Whether to replace the file. Defaults to None.
        modifiers (list | None, optional): List of modifiers. Defaults to None.

    Attributes:
    ----------
        sourcefile (str): The source file for the modifications.
        sourcefolder (str): The source folder.
        saveas (str): The final name of the file this patch will save as (!SaveAs/!Filename)
        replace_file (bool): Whether to replace the file.
            This bool is True when using syntax Replace#=file_to_replace.ext, and therefore False when File#=file_to_replace.ext syntax is used.
            It is currently unknown whether this takes priority over !ReplaceFile, current PyKotor implementation will prioritize !ReplaceFile
        destination (str): The destination for the patch file.
        action (str): The action for this patch, purely used for logging purposes.
        override_type (str): The override type, see `class OverrideType` above.
        skip_if_not_replace (bool): Determines how !ReplaceFile will be handled.
            TSLPatcher's InstallList and CompileList are the only patchlists that handle replace behavior differently.
            in InstallList/CompileList, if this is True and !ReplaceFile is False or File#=file_to_install.ext, the resource will be skipped if the resource already exists.

    Methods:
    -------
        patch_resource(source, memory, logger, game): Patch the resource defined by the 'source' arg. Returns the bytes data of the result.
        apply(mutable_data, memory, logger, game): Apply this patch's modifications to the mutable_data object argument passed.
        pop_tslpatcher_vars(file_section_dict, default_destination): Parse optional TSLPatcher exclamation point variables.

    Exclamation-point variables:
    ---------------------------
        NOTE: All exclamation-point variables that define a path in TSLPatcher must be backslashed instead of forward-slashed. PyKotor will normalize both slashes though.
        - Top-level variables (e.g. [CompileList] [InstallList] [GFFList])
            !DefaultDestination=relative/path/to/destination/folder - Determines where the destination folder is for top-level patch objects.
                Note: !DefaultDestination is highly undocumented in TSLPatcher so it's unclear whether this matches what TSLPatcher does. I believe it takes priority over InstallList's destinations (excluding !Destination)
        - File-level variables ( e.g. [my_file.nss] )
            !SourceFile=this_file.extension - the name of the file to load. Defaults to 'this_file.ext' when using the `File#=this_file` or `Replace#=this_file` syntax.
            !ReplaceFile=<1 or 0> - Whether to replace the file. Takes priority over `Replace#=this_file.ext` syntax
            !SaveAs=<some_file.tpc> - Determines the final filename of the patch. Defaults to whatever !SourceFile is defined as.
            !Filename=<asdf_file.qwer> - Literally the same as !SaveAs
            !Destination=relative/path/to/destination/folder - The relative path to the folder to save this patched file.
            !OverrideType=<warn or ignore or rename> - How to handle conflict resolution. See `class OverrideType` above.
            !SourceFolder=relative/path/to/tslpatchdata/subfolder - **NEW HOLOPATCHER** support for pathing within the mod's tslpatchdata itself. Currently only used in InstallList.
        NOTE: Some patch lists, albeit rare, have different exclamation-point variables. See tslpatcher/mods/ncs.py and tslpatcher/mods/tlk.py for outliers.
    """  # noqa: E501, W505

    DEFAULT_DESTINATION = "Override"

    @abstractmethod
    def __init__(
        self,
        sourcefile: str,
        replace: bool | None = None,  # noqa: FBT001
        modifiers: list | None = None,
        *,
        destination: str | None = None,
    ):
        self.sourcefile: str = sourcefile
        self.sourcefolder: str = "."
        self.saveas: str = sourcefile
        self.replace_file: bool = bool(replace)
        self.destination: str = self.DEFAULT_DESTINATION if destination is None else destination

        # Full path to source file for copying to tslpatchdata (set by diff engine)
        self._source_filepath: Path | None = None

        self.action: str = "Patch" + " "
        self.override_type: str = OverrideType.WARN
        self.skip_if_not_replace: bool = False  # [InstallList] and [CompileList] only

    @abstractmethod
    def patch_resource(
        self,
        source: SOURCE_TYPES,
        memory: PatcherMemory,
        logger: PatchLogger,
        game: Game,
    ) -> bytes | Literal[True]:
        """If bytes is returned, patch the resource. If True is returned, skip this resource."""

    @abstractmethod
    def apply(
        self,
        mutable_data: Any,
        memory: PatcherMemory,
        logger: PatchLogger,
        game: Game,
    ): ...

    def pop_tslpatcher_vars(
        self,
        file_section_dict: CaseInsensitiveDict[str],
        default_destination: str | None = None,
        default_sourcefolder: str = ".",
    ):
        """All optional TSLPatcher vars that can be parsed for a given patch list."""
        ####
        # Note: The second argument passed to the 'pop' function is the default.
        ####

        self.sourcefile = file_section_dict.pop("!SourceFile", self.sourcefile)
        # !SaveAs and !Filename are the same.
        self.saveas = file_section_dict.pop("!Filename", file_section_dict.pop("!SaveAs", self.saveas))

        destination_fallback: str = self.DEFAULT_DESTINATION if default_destination is None else default_destination
        self.destination = file_section_dict.pop("!Destination", destination_fallback)

        # !ReplaceFile=1 is prioritized, see Stoffe's HLFP mod v2.1 for reference.
        replace_file: bool | str = file_section_dict.pop("!ReplaceFile", self.replace_file)
        self.replace_file = convert_to_bool(replace_file)

        # TSLPatcher defaults to "ignore". However realistically, Override file shadowing is
        # a major problem, so HoloPatcher defaults to "warn"
        self.override_type = file_section_dict.pop("!OverrideType", OverrideType.WARN).lower()
        # !SourceFolder: Relative path from mod_path (which is typically the tslpatchdata folder) to source files.
        # Default value "." refers to mod_path itself (the tslpatchdata folder), not its parent.
        # Path resolution: mod_path / sourcefolder / sourcefile
        # For example: if mod_path = "C:/Mod/tslpatchdata" and sourcefolder = ".", then:
        #   - Final path = "C:/Mod/tslpatchdata" / "." / "file.ext" = "C:/Mod/tslpatchdata/file.ext"
        #   - If sourcefolder = "subfolder", then: "C:/Mod/tslpatchdata" / "subfolder" / "file.ext" = "C:/Mod/tslpatchdata/subfolder/file.ext"
        self.sourcefolder = file_section_dict.pop("!SourceFolder", default_sourcefolder)


def convert_to_bool(value: bool | str) -> bool:  # noqa: FBT001
    """Convert a value to boolean.

    The value can be:
    - A boolean (True or False)
    - A string "1" (which should be converted to True)
    - A string "0" (which should be converted to False)

    This function is redundant, but provided for users that may not understand Python.
    """
    return value is True or value == "1"
