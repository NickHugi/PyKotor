from __future__ import annotations

import shutil
from configparser import ConfigParser
from datetime import datetime, timezone
from enum import IntEnum
from typing import TYPE_CHECKING

from pykotor.common.misc import Game, decode_bytes_with_fallbacks
from pykotor.common.stream import BinaryReader, BinaryWriter
from pykotor.extract.capsule import Capsule
from pykotor.extract.file import ResourceIdentifier
from pykotor.tools.misc import is_capsule_file
from pykotor.tools.path import CaseAwarePath, PurePath
from pykotor.tslpatcher.logger import PatchLogger
from pykotor.tslpatcher.memory import PatcherMemory
from pykotor.tslpatcher.mods.install import InstallFile, create_backup
from pykotor.tslpatcher.mods.template import OverrideType
from pykotor.tslpatcher.mods.tlk import ModificationsTLK

if TYPE_CHECKING:
    import os

    from pykotor.tslpatcher.mods.gff import ModificationsGFF
    from pykotor.tslpatcher.mods.nss import ModificationsNSS
    from pykotor.tslpatcher.mods.ssf import ModificationsSSF
    from pykotor.tslpatcher.mods.template import PatcherModifications
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

        self.install_list: list[InstallFile] = []
        self.patches_2da: list[Modifications2DA] = []
        self.patches_gff: list[ModificationsGFF] = []
        self.patches_ssf: list[ModificationsSSF] = []
        self.patches_nss: list[ModificationsNSS] = []
        self.patches_tlk: ModificationsTLK = ModificationsTLK()

    def load(self, ini_text: str, mod_path: os.PathLike | str, logger: PatchLogger | None = None) -> None:
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

    def patch_count(self) -> int:
        return (
            len(self.patches_2da)
            + len(self.patches_gff)
            + len(self.patches_ssf)
            + len(self.patches_tlk.modifiers)
            + len(self.install_list)
            + len(self.patches_nss)
        )


class PatcherNamespace:
    def __init__(self) -> None:
        self.namespace_id: str = ""
        self.ini_filename: str = ""
        self.info_filename: str = ""
        self.data_folderpath: str = ""
        self.name: str = ""
        self.description: str = ""

    def __str__(self) -> str:
        return self.name

    def changes_filepath(self) -> str:
        ini_filename = self.ini_filename.strip() or "changes.ini"
        if self.data_folderpath:
            return str(
                PurePath(
                    self.data_folderpath,
                    ini_filename,
                ),
            )
        return ini_filename

    def rtf_filepath(self):
        info_filename = self.info_filename.strip() or "info.rtf"
        if self.data_folderpath:
            return str(
                PurePath(
                    self.data_folderpath,
                    info_filename,
                ),
            )
        return info_filename


class ModInstaller:
    def __init__(
        self,
        mod_path: os.PathLike | str,
        game_path: os.PathLike | str,
        changes_ini_path: os.PathLike | str,
        logger: PatchLogger | None = None,
    ):
        self.log: PatchLogger = logger or PatchLogger()
        self.game_path: CaseAwarePath = CaseAwarePath(game_path)
        self.mod_path: CaseAwarePath = CaseAwarePath(mod_path)
        self.changes_ini_path: CaseAwarePath = CaseAwarePath(changes_ini_path)
        if not self.changes_ini_path.exists():  # handle legacy syntax
            self.changes_ini_path = self.mod_path / self.changes_ini_path.name
            if not self.changes_ini_path.exists():
                self.changes_ini_path = self.mod_path / "tslpatchdata" / self.changes_ini_path.name
            if not self.changes_ini_path.exists():
                msg = f"Could not find the changes ini file {self.changes_ini_path!s} on disk! Could not start install!"
                raise FileNotFoundError(msg)

        self._config: PatcherConfig | None = None
        self._backup: CaseAwarePath | None = None
        self._processed_backup_files: set = set()
        self._game: Game | None = None

    def config(self) -> PatcherConfig:
        """Returns the PatcherConfig object associated with the mod installer. The object is created when the method is
        first called then cached for future calls.
        """
        if self._config is not None:
            return self._config

        ini_file_bytes = BinaryReader.load_file(self.changes_ini_path)
        try:
            ini_text = decode_bytes_with_fallbacks(ini_file_bytes)
        except UnicodeDecodeError:
            self.log.add_warning(f"Could not determine encoding of '{self.changes_ini_path.name}'. Attempting to force load...")
            ini_text = ini_file_bytes.decode(encoding="utf-32", errors="replace")

        self._config = PatcherConfig()
        self._config.load(ini_text, self.mod_path, self.log)

        if self._config.required_file:
            requiredfile_path: CaseAwarePath = self.game_path / "Override" / self._config.required_file
            if not requiredfile_path.exists():
                raise ImportError(self._config.required_message.strip() or "cannot install - missing a required mod")
        return self._config

    def game(self) -> Game:
        if self._game:
            return self._game
        path = self.game_path

        def check(x) -> bool:
            file_path: CaseAwarePath = path.joinpath(x)
            return file_path.exists()

        is_game1_stream = check("streamwaves") and not check("streamvoice")
        is_game1_exe = check("swkotor.exe") and not check("swkotor2.exe")
        is_game1_rims = check("rims")

        is_game2_stream = check("streamvoice") and not check("streamwaves")
        is_game2_exe = check("swkotor2.exe") and not check("swkotor.exe")

        if any((is_game2_stream, is_game2_exe)):  # check TSL first otherwise the 'rims' folder takes priority
            self._game = Game(2)
        if any((is_game1_stream, is_game1_exe, is_game1_rims)):
            self._game = Game(1)
        if self._game is not None:
            return self._game
        msg = "Could not determine whether we're patching to a K1 install or a TSL install!"
        raise ValueError(msg)

    def backup(self) -> tuple[CaseAwarePath, set]:
        if self._backup:
            return (self._backup, self._processed_backup_files)
        backup_dir = self.mod_path
        timestamp = datetime.now(tz=timezone.utc).astimezone().strftime("%Y-%m-%d_%H.%M.%S")
        while not backup_dir.joinpath("tslpatchdata").exists() and backup_dir.parent.name:
            backup_dir = backup_dir.parent
        uninstall_dir = backup_dir.joinpath("uninstall")
        try:
            if uninstall_dir.exists():
                shutil.rmtree(uninstall_dir)
        except PermissionError as e:
            self.log.add_warning(f"Could not initialize backup folder: {e!r}")
        backup_dir = backup_dir / "backup" / timestamp
        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            self.log.add_warning(f"Could not create backup folder: {e!r}")
        self.log.add_note(f"Using backup directory: '{backup_dir}'")
        self._backup = backup_dir
        self._processed_backup_files = set()
        return (self._backup, self._processed_backup_files)

    def handle_capsule_and_backup(
        self, patch: PatcherModifications, output_container_path: CaseAwarePath
    ) -> tuple[bool, Capsule | None]:
        capsule = None
        if is_capsule_file(patch.destination):
            capsule = Capsule(output_container_path)
            create_backup(self.log, output_container_path, *self.backup(), PurePath(patch.destination).parent)
            exists = capsule.exists(*ResourceIdentifier.from_path(patch.saveas))
        else:
            create_backup(self.log, output_container_path.joinpath(patch.saveas), *self.backup(), patch.destination)
            exists = output_container_path.joinpath(patch.saveas).exists()
        return (exists, capsule)

    def lookup_resource(
        self,
        patch: PatcherModifications,
        output_container_path: CaseAwarePath,
        exists_at_output_location: bool | None = None,
        capsule: Capsule | None = None,
    ) -> bytes | None:
        if patch.replace_file or not exists_at_output_location:
            return BinaryReader.load_file(self.mod_path / patch.sourcefile)
        if capsule is not None:
            return capsule.resource(*ResourceIdentifier.from_path(patch.saveas))
        return BinaryReader.load_file(output_container_path / patch.saveas)

    def handle_override_type(self, patch: PatcherModifications):
        override_type = patch.override_type.lower().strip()
        if not override_type or override_type == OverrideType.IGNORE:
            return

        override_dir = self.game_path / "Override"
        override_resource_path = override_dir / patch.saveas
        if override_resource_path.exists():
            if override_type == "rename":
                new_filepath: CaseAwarePath = override_dir / ("old_" + patch.saveas)
                i = 2
                while new_filepath.exists():  # tslpatcher does not do this loop.
                    stem = new_filepath.stem if i == 2 else (new_filepath.stem[4:] + f" ({i})")  # noqa: PLR2004
                    new_filepath = (new_filepath.parent / stem).with_suffix(new_filepath.suffix)
                    i += 1
                try:
                    shutil.move(override_resource_path, new_filepath)
                except Exception as e:  # noqa: BLE001
                    # Handle exceptions such as permission errors or file in use.
                    self.log.add_error(f"Could not rename file to {new_filepath.name}: {e!r}")
            elif override_type == "warn":
                self.log.add_warning(f"A resource located at '{override_resource_path}' is shadowing this mod's changes in {patch.destination}!")

    def should_patch(
        self,
        patch: PatcherModifications,
        exists: bool | None = False,
        capsule: Capsule | None = None,
    ) -> bool:
        local_folder = self.game_path.name if patch.destination == "." else patch.destination

        container_type = "folder" if capsule is None else "archive"

        if patch.replace_file and exists:
            self.log.add_note(f"{patch.action[:-1]}ing '{patch.sourcefile}' and replacing existing file '{patch.saveas}' in the '{local_folder}' {container_type}")
            return True

        if not patch.skip_if_not_replace and not patch.replace_file and exists:
            self.log.add_note(f"{patch.action[:-1]}ing existing file '{patch.saveas}' in the '{local_folder}' {container_type}")
            return True

        if patch.skip_if_not_replace and not patch.replace_file and exists:  # [InstallList] only?
            self.log.add_warning(f"'{patch.saveas}' already exists in the '{local_folder}' {container_type}. Skipping file...")
            return False

        if capsule is not None and not capsule.path().exists():
            self.log.add_error(f"The capsule '{patch.destination}' did not exist when attempting to {patch.action.lower().rstrip()} '{patch.sourcefile}'. Skipping file...")
            return False

        # In capsules, I haven't seen any TSLPatcher mods reach this point. I know TSLPatcher at least supports this portion for non-capsules.
        # Most mods will use an [InstallList] to ensure the files exist in the game path before patching anyways, but not all.
        save_type: str = "adding" if capsule is not None else "saving"
        self.log.add_note(f"{patch.action[:-1]}ing '{patch.sourcefile}' and {save_type} to the '{local_folder}' {container_type}")
        return True

    def install(self) -> None:
        config = self.config()
        self.game()  # ensure the KOTOR directory is somewhat valid
        memory = PatcherMemory()

        patches_list: list[PatcherModifications] = [
            *config.install_list,
            *([config.patches_tlk] if config.patches_tlk.modifiers else []),
            *config.patches_2da,
            *config.patches_gff,
            *config.patches_nss,
            *config.patches_ssf,
        ]

        for patch in patches_list:
            output_container_path = self.game_path / patch.destination
            exists, capsule = self.handle_capsule_and_backup(patch, output_container_path)
            if not self.should_patch(patch, exists, capsule):
                continue
            data_to_patch_bytes = self.lookup_resource(patch, output_container_path, exists, capsule)
            if not data_to_patch_bytes:
                self.log.add_error(f"Could not locate resource to {patch.action.lower().strip()}: '{patch.sourcefile}'")
                continue
            if capsule:
                self.handle_override_type(patch)

            patched_bytes_data = patch.apply(data_to_patch_bytes, memory, self.log, self.game())
            if capsule is not None:
                capsule.add(*ResourceIdentifier.from_path(patch.saveas), patched_bytes_data)
            else:
                BinaryWriter.dump(output_container_path / patch.saveas, patched_bytes_data)
            self.log.complete_patch()

        self.log.add_note(f"Successfully completed {self.log.patches_completed} total patches.")
