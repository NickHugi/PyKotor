from __future__ import annotations

import os
import shutil
from copy import deepcopy
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from pykotor.common.stream import BinaryReader, BinaryWriter
from pykotor.extract.capsule import Capsule
from pykotor.extract.file import ResourceIdentifier
from pykotor.extract.installation import Installation
from pykotor.tools.encoding import decode_bytes_with_fallbacks
from pykotor.tools.misc import is_capsule_file
from pykotor.tools.path import CaseAwarePath
from pykotor.tools.resource import read_resource
from pykotor.tslpatcher.config import PatcherConfig
from pykotor.tslpatcher.logger import PatchLogger
from pykotor.tslpatcher.memory import PatcherMemory
from pykotor.tslpatcher.mods.install import InstallFile, create_backup
from pykotor.tslpatcher.mods.template import OverrideType, PatcherModifications
from utility.error_handling import universal_simplify_exception
from utility.path import PurePath

if TYPE_CHECKING:

    from pykotor.common.misc import Game
    from pykotor.resource.type import SOURCE_TYPES
    from pykotor.tslpatcher.mods.tlk import ModificationsTLK

class ModInstaller:
    def __init__(
        self,
        mod_path: os.PathLike | str,
        game_path: os.PathLike | str,
        changes_ini_path: os.PathLike | str,
        logger: PatchLogger | None = None,
    ):
        """Initialize a Patcher instance.

        Args:
        ----
            mod_path: {Path to the mod directory}
            game_path: {Path to the game directory}
            changes_ini_path: {Path to the changes ini file}
            logger: {Optional logger instance}.

        Returns:
        -------
            self: {Returns the Patcher instance}

        Processing Logic:
        ----------------
            - Initialize the logger if not already defined.
            - Initialize parameters passed for game, mod and changes ini paths
            - Handle legacy changes ini path syntax (changes_ini_path used to just be a filename)
            - Initialize other attributes.
        """
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

        game = Installation.determine_game(self.game_path)
        if game is None:
            msg = "Chosen KOTOR directory is not a valid installation - cannot initialize ModInstaller."
            raise RuntimeError(msg)
        self.game: Game = game
        self._config: PatcherConfig | None = None
        self._backup: CaseAwarePath | None = None
        self._processed_backup_files: set = set()

    def config(self) -> PatcherConfig:
        """Returns the PatcherConfig object associated with the mod installer.

        The object is created when the method is first called then cached for future calls.
        """
        if self._config is not None:
            return self._config

        ini_file_bytes = BinaryReader.load_file(self.changes_ini_path)
        try:
            ini_text = decode_bytes_with_fallbacks(ini_file_bytes)
        except UnicodeDecodeError:
            self.log.add_warning(f"Could not determine encoding of '{self.changes_ini_path.name}'. Attempting to force load...")
            ini_text = ini_file_bytes.decode(errors="ignore")

        self._config = PatcherConfig()
        self._config.load(ini_text, self.mod_path, self.log)

        if self._config.required_file:
            requiredfile_path: CaseAwarePath = self.game_path / "Override" / self._config.required_file
            if not requiredfile_path.exists():
                raise ImportError(self._config.required_message.strip() or "cannot install - missing a required mod")
        return self._config

    def backup(self) -> tuple[CaseAwarePath, set]:
        """Creates a backup of the patch files.

        Args:
        ----
            self: The Patcher object

        Returns:
        -------
            tuple[CaseAwarePath, set]: Returns a tuple containing the backup directory path and a set of processed backup files

        Processing Logic:
        ----------------
            - Checks if a backup folder was already initialized and return that and the currently processed files if so
            - Finds the mod path directory to backup from
            - Generates a timestamped subdirectory name
            - Removes any existing uninstall directories
            - Creates the backup directory
            - Returns the backup directory and new hashset that'll contain the processed files
        """
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
        self,
        patch: PatcherModifications,
        output_container_path: CaseAwarePath,
    ) -> tuple[bool, Capsule | None]:
        """Handle capsule file and create backup.

        Args:
        ----
            patch: PatcherModifications: Patch details
            output_container_path: CaseAwarePath: Output path.

        Returns:
        -------
            tuple[bool, Capsule | None]: Exists flag and capsule object

        Processing Logic:
        ----------------
            - Check if patch destination is capsule file
            - If yes, create Capsule object and backup file
            - Else, backup file directly
            - Return exists flag and capsule object.
        """
        capsule = None
        if is_capsule_file(patch.destination):
            capsule = Capsule(output_container_path)
            create_backup(self.log, output_container_path, *self.backup(), PurePath(patch.destination).parent)
            exists = capsule.exists(*ResourceIdentifier.from_path(patch.saveas))
        else:
            create_backup(self.log, output_container_path.joinpath(patch.saveas), *self.backup(), patch.destination)
            exists = output_container_path.joinpath(patch.saveas).exists()
        return (exists, capsule)

    def load_resource_file(self, source: SOURCE_TYPES) -> bytes:
        if self.config().ignore_file_extensions:
            return read_resource(source)
        return BinaryReader.from_auto(source).read_all()

    def lookup_resource(
        self,
        patch: PatcherModifications,
        output_container_path: CaseAwarePath,
        exists_at_output_location: bool | None = None,
        capsule: Capsule | None = None,
    ) -> bytes | None:
        """Looks up the file/resource that is expected to be patched.

        Args:
        ----
            patch: PatcherModifications - The desired patch information.
            output_container_path: CaseAwarePath - Path to output container (capsule/folder)
            exists_at_output_location: bool | None - Whether resource exists at destination location
            capsule: Capsule | None - Capsule to be patched, if one

        Returns:
        -------
            bytes | None - Loaded resource bytes or None

        Processing Logic:
        ----------------
            - Check if file should be replaced or doesn't exist at output, load from mod path
            - Otherwise, load the file to be patched from the destination if it exists.
                - If no capsule, it's a file and load it directly as a file.
                - If destination is a capsule, pull the resource from the capsule.
            - Return None and log error on failure (IO exceptions, permission issues, etc)
        """
        try:
            if patch.replace_file or not exists_at_output_location:
                return self.load_resource_file(self.mod_path / patch.sourcefolder / patch.sourcefile)
            if capsule is None:
                return self.load_resource_file(output_container_path / patch.saveas)
            return capsule.resource(*ResourceIdentifier.from_path(patch.saveas))
        except OSError as e:
            self.log.add_error(f"Could not load source file to {patch.action.lower().strip()}:{os.linesep}{universal_simplify_exception(e)}")
            return None

    def handle_override_type(self, patch: PatcherModifications):
        """Handles the desired behavior set by the !OverrideType tslpatcher var for the specified patch.

        Args:
        ----
            patch: PatcherModifications - The patch modification object.

        Processes the override type:
            - Checks if override type is empty or set to ignore and returns early.
            - Gets the override resource path.
            - If the path exists:
                - For rename, renames the file with incrementing number if filename exists.
                - For warn, logs a warning that the file is shadowing the mod's changes.
        """
        override_type = patch.override_type.lower().strip()
        if not override_type or override_type == OverrideType.IGNORE:
            return

        override_dir = self.game_path / "Override"
        override_resource_path = override_dir / patch.saveas
        if not override_resource_path.exists():
            override_resource_path = override_resource_path.resolve()
        if override_resource_path.exists():
            if override_type == OverrideType.RENAME:
                renamed_file_path: CaseAwarePath = override_dir / f"old_{patch.saveas}"
                i = 2
                while renamed_file_path.exists():  # tslpatcher does not do this loop.
                    stem = renamed_file_path.stem if i == 2 else renamed_file_path.stem[:4]
                    next_filename: str = f"{stem} ({i}){renamed_file_path.suffix}"
                    renamed_file_path = renamed_file_path.parent / next_filename
                    i += 1
                try:
                    renamed_file_path = renamed_file_path.resolve()
                    shutil.move(str(override_resource_path), str(renamed_file_path))
                except Exception as e:  # noqa: BLE001
                    # Handle exceptions such as permission errors or file in use.
                    self.log.add_error(f"Could not rename '{patch.saveas}' to '{renamed_file_path.name}' in the Override folder: {e!r}")
            elif override_type == OverrideType.WARN:
                self.log.add_warning(f"A resource located at '{override_resource_path!s}' is shadowing this mod's changes in {patch.destination}!")

    def should_patch(
        self,
        patch: PatcherModifications,
        exists: bool | None = False,
        capsule: Capsule | None = None,
    ) -> bool:
        """The name of this function is misleading, it only returns False if the capsule was not found (error)
        or an InstallList patch already exists at the output location without the Replace#= prefix. Otherwise, it is
        mostly used for logging purposes.

        Args:
        ----
            patch: PatcherModifications - The patch details
            exists: bool | None - Whether the target file already exists
            capsule: Capsule | None - The target capsule if patching one

        Returns:
        -------
            bool - Whether the patch should be applied

        Processing Logic:
        ----------------
            - Determines the local folder and container type from the patch details
            - Checks if the patch replaces an existing file and logs the action
            - Checks if the file already exists and the patch settings allow skipping
            - Checks if the target capsule exists if patching one
            - Logs the patching action
            - Returns True if the patch should be applied.
        """  # noqa: D205
        local_folder = self.game_path.name if patch.destination.strip("\\").strip("/") == "." else patch.destination
        container_type = "folder" if capsule is None else "archive"

        if patch.replace_file and exists:
            saveas_str = f"'{patch.saveas}' in" if patch.saveas != patch.sourcefile else "in"
            self.log.add_note(f"{patch.action[:-1]}ing '{patch.sourcefile}' and replacing existing file {saveas_str} the '{local_folder}' {container_type}")
            return True

        if not patch.skip_if_not_replace and not patch.replace_file and exists:
            self.log.add_note(f"{patch.action[:-1]}ing existing file '{patch.saveas}' in the '{local_folder}' {container_type}")
            return True

        if patch.skip_if_not_replace and not patch.replace_file and exists:  # [InstallList] only
            self.log.add_note(f"'{patch.saveas}' already exists in the '{local_folder}' {container_type}. Skipping file...")
            return False

        if capsule is not None and not capsule.path().exists():
            self.log.add_error(f"The capsule '{patch.destination}' did not exist when attempting to {patch.action.lower().rstrip()} '{patch.sourcefile}'. Skipping file...")
            return False

        # In capsules, I haven't seen any TSLPatcher mods reach this point. I know TSLPatcher at least supports this portion for non-capsules.
        # Most mods will use an [InstallList] to ensure the files exist before patching anyways, but not all.
        save_type: str = "adding" if capsule is not None and patch.saveas == patch.sourcefile else "saving"
        saving_as_str = f"as '{patch.saveas}' in" if patch.saveas != patch.sourcefile else "to"
        self.log.add_note(f"{patch.action[:-1]}ing '{patch.sourcefile}' and {save_type} {saving_as_str} the '{local_folder}' {container_type}")
        return True

    def install(self) -> None:
        """Install patches from the config file.

        Processing Logic:
        ----------------
            - Load config and determine game type
            - Get list of patches from config
            - For each patch:
                - Get output path and check for existing file/capsule
                - Apply patch if needed
                - Save patched data to destination file or add to capsule
            - Log completion.
        """
        config = self.config()

        tlk_patches = self.get_tlk_patches(config)
        patches_list: list[PatcherModifications] = [
            *config.install_list,  # Note: TSLPatcher executes [InstallList] after [TLKList]
            *tlk_patches,
            *config.patches_2da,
            *config.patches_gff,
            *config.patches_nss,
            *config.patches_ncs,   # Note: TSLPatcher executes [CompileList] after [HACKList]
            *config.patches_ssf,
        ]

        # Move nwscript.nss to Override if there are any nss patches to do
        if len(config.patches_nss) > 0:
            file_install = InstallFile("nwscript.nss", replace_existing=True)
            if file_install not in config.install_list:
                config.install_list.append(file_install)

        memory = PatcherMemory()
        for patch in patches_list:
            output_container_path = self.game_path / patch.destination
            exists, capsule = self.handle_capsule_and_backup(patch, output_container_path)
            if not self.should_patch(patch, exists, capsule):
                continue
            data_to_patch_bytes = self.lookup_resource(patch, output_container_path, exists, capsule)
            if data_to_patch_bytes is None:  # check None instead of `not data_to_patch_bytes` as sometimes mods will installlist empty files.
                self.log.add_error(f"Could not locate resource to {patch.action.lower().strip()}: '{patch.sourcefile}'")
                continue
            if not data_to_patch_bytes:
                self.log.add_note(f"'{patch.sourcefile}' has no content/data and is completely empty.")

            patched_bytes_data = patch.patch_resource(data_to_patch_bytes, memory, self.log, self.game)
            if capsule is not None:
                self.handle_override_type(patch)
                capsule.add(*ResourceIdentifier.from_path(patch.saveas), patched_bytes_data)
            else:
                output_container_path.mkdir(exist_ok=True, parents=True)
                BinaryWriter.dump(output_container_path / patch.saveas, patched_bytes_data)
            self.log.complete_patch()

        self.log.add_note(f"Successfully completed {self.log.patches_completed} total patches.")

    def get_tlk_patches(self, config: PatcherConfig) -> list[ModificationsTLK]:
        tlk_patches: list[ModificationsTLK] = []
        patches_tlk: ModificationsTLK = config.patches_tlk

        if not patches_tlk.modifiers:
            return tlk_patches

        tlk_patches.append(patches_tlk)

        female_dialog_filename = "dialogf.tlk"
        female_dialog_file: CaseAwarePath = self.game_path / female_dialog_filename

        if female_dialog_file.exists():
            female_tlk_patches: ModificationsTLK = deepcopy(patches_tlk)
            female_tlk_patches.sourcefile = (
                female_tlk_patches.sourcefile_f
                if (self.mod_path / female_tlk_patches.sourcefile_f).exists()
                else patches_tlk.sourcefile
            )
            female_tlk_patches.saveas = female_dialog_filename
            tlk_patches.append(female_tlk_patches)

        return tlk_patches


