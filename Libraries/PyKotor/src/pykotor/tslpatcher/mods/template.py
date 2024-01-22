from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pykotor.common.misc import CaseInsensitiveDict, Game
    from pykotor.resource.type import SOURCE_TYPES
    from pykotor.tslpatcher.logger import PatchLogger
    from pykotor.tslpatcher.memory import PatcherMemory
    from typing_extensions import Literal

class OverrideType:
    """Possible actions for how the patcher should behave when patching a file to a ERF/MOD/RIM while that filename already exists in the Override folder."""

    IGNORE = "ignore"  # Do nothing: don't even check (TSLPatcher default)
    WARN   = "warn"    # Log a warning (HoloPatcher default)
    RENAME = "rename"  # Rename the file in the Override folder with the 'old_' prefix. Also logs a warning.

class PatcherModifications(ABC):
    DEFAULT_DESTINATION = "Override"

    @abstractmethod
    def __init__(self, sourcefile: str, replace: bool | None = None, modifiers: list | None = None) -> None:
        self.sourcefile: str = sourcefile
        self.sourcefolder: str = "."
        self.saveas: str = sourcefile
        self.replace_file: bool = bool(replace)
        self.destination: str = self.DEFAULT_DESTINATION

        self.action: str = "Patch" + " "
        self.override_type: str = OverrideType.WARN
        self.skip_if_not_replace = False  # [InstallList] only

    @abstractmethod
    def patch_resource(
        self,
        source: SOURCE_TYPES,
        memory: PatcherMemory,
        logger: PatchLogger,
        game: Game,
    ) -> bytes | Literal[True]:
        """If bytes is returned, patch the resource. If True is returned, skip this resource."""
        ...

    @abstractmethod
    def apply(
        self,
        mutable_data: Any,
        memory: PatcherMemory,
        logger: PatchLogger,
        game: Game,
    ) -> None:
        ...

    def pop_tslpatcher_vars(self, file_section_dict: CaseInsensitiveDict[str], default_destination=None) -> None:
        """All optional TSLPatcher vars that can be parsed for a given patch list."""
        self.sourcefile = file_section_dict.pop("!SourceFile", self.sourcefile)
        # !SaveAs and !Filename are the same.
        self.saveas = file_section_dict.pop("!Filename", file_section_dict.pop("!SaveAs", self.saveas))
        self.destination = file_section_dict.pop("!Destination", default_destination if default_destination is not None else self.DEFAULT_DESTINATION)

        # !ReplaceFile=1 is prioritized, see Stoffe's HLFP mod v2.1 for reference.
        replace_file: bool | str = file_section_dict.pop("!ReplaceFile", self.replace_file)
        self.replace_file = bool(int(replace_file))

        # TSLPatcher defaults to "ignore". Realistically, Override file shadowing is a major problem.
        self.override_type = file_section_dict.pop("!OverrideType", OverrideType.WARN)
