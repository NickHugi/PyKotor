from __future__ import annotations

import os
import shutil
import sys

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import PurePath
from typing import TYPE_CHECKING, Callable

from loggerplus import RobustLogger

from pykotor.common.stream import BinaryReader, BinaryWriter
from pykotor.extract.capsule import Capsule
from pykotor.extract.file import ResourceIdentifier
from pykotor.extract.installation import Installation
from pykotor.tools.encoding import decode_bytes_with_fallbacks
from pykotor.tools.misc import is_capsule_file, is_mod_file, is_rim_file
from pykotor.tools.module import rim_to_mod
from pykotor.tools.path import CaseAwarePath
from pykotor.tslpatcher.config import PatcherConfig
from pykotor.tslpatcher.logger import PatchLogger
from pykotor.tslpatcher.memory import PatcherMemory
from pykotor.tslpatcher.mods.install import InstallFile, create_backup
from pykotor.tslpatcher.mods.nss import ModificationsNSS, MutableString
from pykotor.tslpatcher.mods.template import OverrideType
from utility.error_handling import universal_simplify_exception

if TYPE_CHECKING:
    from threading import Event

    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]

    from pykotor.common.misc import Game
    from pykotor.resource.type import SOURCE_TYPES
    from pykotor.tslpatcher.mods.template import PatcherModifications
    from pykotor.tslpatcher.mods.tlk import ModificationsTLK


class ModInstaller:
    """Core mod installer implementing TSLPatcher/HoloPatcher logic.
    
    Handles mod installation, backup creation, and applying patches from changes.ini files.
    This is a Python rewrite of the original TSLPatcher Perl implementation.
    
    References:
    ----------
        vendor/TSLPatcher/TSLPatcher.pl - Original Perl TSLPatcher implementation
        vendor/HoloPatcher.NET/ - C# port of HoloPatcher
        vendor/Kotor.NET/Kotor.NET.Patcher/ - Incomplete C# patcher
    """
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
        self.game_path: CaseAwarePath = CaseAwarePath(game_path)
        self.mod_path: CaseAwarePath = CaseAwarePath(mod_path)
        self.changes_ini_path: CaseAwarePath = CaseAwarePath(changes_ini_path)
        self.tslpatchdata_path: CaseAwarePath | None = None
        self.log: PatchLogger = logger or PatchLogger()
        self.game: Game | None = Installation.determine_game(self.game_path)
        if not self.changes_ini_path.is_file():  # Handle legacy syntax
            self.changes_ini_path = self.mod_path / self.changes_ini_path.name
            if not self.changes_ini_path.is_file():
                self.changes_ini_path = self.mod_path / "tslpatchdata" / self.changes_ini_path.name
            if not self.changes_ini_path.is_file():
                import errno

                msg = "Could not find the changes ini file on disk."
                raise FileNotFoundError(errno.ENOENT, msg, str(self.changes_ini_path))

        self._config: PatcherConfig | None = None
        self._backup: CaseAwarePath | None = None
        self._processed_backup_files: set = set()

    def config(self) -> PatcherConfig:
        """Returns the PatcherConfig object associated with the mod installer.

        The object is created when the method is first called then cached for future calls.
        """
        if self._config is not None:
            return self._config

        ini_file_bytes: bytes = self.changes_ini_path.read_bytes()
        ini_text: str
        try:
            ini_text = decode_bytes_with_fallbacks(ini_file_bytes)
        except UnicodeDecodeError:
            self.log.add_warning(f"Could not determine encoding of '{self.changes_ini_path.name}'. Attempting to force load...")
            ini_text = ini_file_bytes.decode(errors="ignore")

        self._config = PatcherConfig()
        self._config.load(ini_text, self.mod_path, self.log, self.tslpatchdata_path)

        if self._config.required_files:
            for i, files in enumerate(self._config.required_files):
                for file in files:
                    requiredfile_path: CaseAwarePath = self.game_path / "Override" / file
                    if not requiredfile_path.is_file():
                        raise ImportError(self._config.required_messages[i].strip() or "cannot install - missing a required mod")
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
        backup_dir: CaseAwarePath = self.mod_path
        timestamp: str = datetime.now(tz=timezone.utc).astimezone().strftime("%Y-%m-%d_%H.%M.%S")
        while not backup_dir.joinpath("tslpatchdata").is_dir() and backup_dir.parent.name:
            backup_dir = backup_dir.parent
        uninstall_dir: CaseAwarePath = backup_dir.joinpath("uninstall")
        try:  # sourcery skip: remove-redundant-exception
            if uninstall_dir.is_dir():
                shutil.rmtree(uninstall_dir)
        except (PermissionError, OSError) as e:
            self.log.add_warning(f"Could not initialize uninstall directory: {universal_simplify_exception(e)}")
        backup_dir = backup_dir / "backup" / timestamp
        try:  # sourcery skip: remove-redundant-exception
            backup_dir.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            self.log.add_warning(f"Could not create backup folder: {universal_simplify_exception(e)}")
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
        capsule: Capsule | None = None
        exists: bool
        if is_capsule_file(patch.destination):
            module_root: str = Installation.get_module_root(output_container_path)
            tslrcm_omitted_rims: tuple[Literal["702KOR"], Literal["401DXN"]] = ("702KOR", "401DXN")
            if module_root.upper() not in tslrcm_omitted_rims and is_rim_file(output_container_path):
                self.log.add_warning(f"This mod is patching RIM file Modules/{output_container_path.name}!\nPatching RIMs is highly incompatible, not recommended, and widely considered bad practice. Please request the mod developer to fix this.")  # noqa: E501
            if not output_container_path.is_file():
                if is_mod_file(output_container_path):
                    self.log.add_note(
                        f"IMPORTANT! The module at path '{output_container_path}' did not exist, building one in the 'Modules' folder immediately from the following files:"  # noqa: ISC003
                        + f"\n    Modules/{module_root}.rim"
                        + f"\n    Modules/{module_root}_s.rim"
                        + (f"\n    Modules/{module_root}_dlg.erf" if self.game is not None and self.game.is_k2() else "")
                    )
                    try:
                        rim_to_mod(output_container_path, self.game_path / "Modules", module_root, self.game)
                    except Exception as e:  # noqa: BLE001
                        msg = f"Failed to build module '{output_container_path.name}': {e}"
                        self.log.add_error(msg)
                        raise
                else:
                    import errno

                    msg = f"The capsule '{patch.destination}' did not exist, or permission issues occurred, when attempting to {patch.action.lower().rstrip()} '{patch.sourcefile}'. Skipping file..."  # noqa: E501
                    raise FileNotFoundError(errno.ENOENT, msg, str(output_container_path))
            capsule = Capsule(output_container_path)
            create_backup(self.log, output_container_path, *self.backup(), PurePath(patch.destination).parent)
            exists = capsule.contains(*ResourceIdentifier.from_path(patch.saveas).unpack())
        else:
            create_backup(self.log, output_container_path.joinpath(patch.saveas), *self.backup(), patch.destination)
            exists = output_container_path.joinpath(patch.saveas).is_file()
        return (exists, capsule)

    def load_resource_file(self, source: SOURCE_TYPES) -> bytes:
        # if self._config and self._config.ignore_file_extensions:
        #    return read_resource(source)
        with BinaryReader.from_auto(source) as reader:
            return reader.read_all()

    def lookup_resource(
        self,
        patch: PatcherModifications,
        output_container_path: CaseAwarePath,
        exists_at_output_location: bool | None = None,  # noqa: FBT001
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
                # Path resolution: mod_path / sourcefolder / sourcefile
                # mod_path is typically the tslpatchdata folder (parent of changes.ini).
                # If sourcefolder = ".", this resolves to mod_path itself (tslpatchdata folder).
                return self.load_resource_file(self.mod_path / patch.sourcefolder / patch.sourcefile)
            if capsule is None:
                return self.load_resource_file(output_container_path / patch.saveas)
            return capsule.resource(*ResourceIdentifier.from_path(patch.saveas).unpack())
        except OSError as e:
            self.log.add_error(f"Could not load source file to {patch.action.lower().strip()}:{os.linesep}{universal_simplify_exception(e)}")
            return None

    def handle_modrim_shadow(
        self,
        patch: PatcherModifications,
    ):
        """Check if a patch is being installed into a rim and overshadowed by a .mod."""
        # uncomment and define the attrs if we decide this should be configurable.
        # modrim_type: str = patch.modrim_type.lower().strip()
        # if not modrim_type or modrim_type == ignore
        #    return
        erfrim_path: CaseAwarePath = self.game_path / patch.destination / patch.saveas
        mod_path: CaseAwarePath = erfrim_path.with_name(f"{Installation.get_module_root(erfrim_path.name)}.mod")
        if erfrim_path != mod_path and mod_path.is_file():
            self.log.add_warning(f"This mod intends to install '{patch.saveas}' into '{patch.destination}', but is overshadowed by the existing '{mod_path.name}'!")

    def handle_override_type(
        self,
        patch: PatcherModifications,
    ):
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
        override_type: str = patch.override_type.lower().strip()
        if not override_type or override_type == OverrideType.IGNORE:
            return

        override_dir: CaseAwarePath = self.game_path / "Override"
        override_resource_path: CaseAwarePath = override_dir / patch.saveas
        if override_resource_path.is_file():
            if override_type == OverrideType.RENAME:
                renamed_file_path: CaseAwarePath = override_dir / f"old_{patch.saveas}"
                i = 2
                filestem: str = renamed_file_path.stem
                while renamed_file_path.is_file():
                    renamed_file_path = renamed_file_path.parent / f"{filestem} ({i}){renamed_file_path.suffix}"
                    i += 1
                try:
                    shutil.move(str(override_resource_path), str(renamed_file_path))
                except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
                    # Handle exceptions such as permission errors or file in use.
                    self.log.add_error(f"Could not rename '{patch.saveas}' to '{renamed_file_path.name}' in the Override folder: {universal_simplify_exception(e)}")  # noqa: E501
            elif override_type == OverrideType.WARN:
                self.log.add_warning(f"A resource located at '{override_resource_path}' is shadowing this mod's changes in {patch.destination}!")  # noqa: E501

    def should_patch(
        self,
        patch: PatcherModifications,
        exists: bool | None = False,  # noqa: FBT002, FBT001
        capsule: Capsule | None = None,
    ) -> bool:
        """Log information about the patch, including source and destination.

        The name of this function can be misleading, it only returns False if the capsule was not found (error)
        or an InstallList patch already exists at the output location without the Replace#= prefix. Otherwise, it is
        mostly used for logging purposes.

        Args:
        ----
            patch (PatcherModifications): - The patch details
            exists (bool | None): - Whether the target file already exists
            capsule (Capsule | None): - The target capsule if patching one

        Returns:
        -------
            bool - Whether the patch should be applied
                False if the capsule was not found (error)
                False if an InstallList patch already exists at destination and patch configured to replace existing file or not (!ReplaceFile/#Replace=filename)
                True otherwise.

        Processing Logic:
        ----------------
            - Determines the local folder and container type from the patch details
            - Checks if the patch replaces an existing file and logs the action
            - Checks if the file already exists and the patch settings allow skipping
            - Checks if the target capsule exists if patching one
            - Logs the patching action
            - Returns True if the patch should be applied.
        """  # noqa: E501
        local_folder: str = self.game_path.name if patch.destination.strip("\\").strip("/") == "." else patch.destination
        container_type: Literal["folder", "archive"] = "folder" if capsule is None else "archive"

        if patch.replace_file and exists:
            saveas_str: str = f"'{patch.saveas}' in" if patch.saveas != patch.sourcefile else "in"
            self.log.add_note(f"{patch.action[:-1]}ing '{patch.sourcefile}' and replacing existing file {saveas_str} the '{local_folder}' {container_type}")  # noqa: E501
            return True

        if not patch.skip_if_not_replace and not patch.replace_file and exists:
            self.log.add_note(f"{patch.action[:-1]}ing existing file '{patch.saveas}' in the '{local_folder}' {container_type}")
            return True

        if patch.skip_if_not_replace and not patch.replace_file and exists:  # [InstallList] only
            self.log.add_note(f"'{patch.saveas}' already exists in the '{local_folder}' {container_type}. Skipping file...")
            return False

        if capsule is not None and not capsule.filepath().is_file():
            self.log.add_error(f"The capsule '{patch.destination}' did not exist when attempting to {patch.action.lower().rstrip()} '{patch.sourcefile}'. Skipping file...")  # noqa: E501
            return False

        save_type: str = "adding" if capsule is not None and patch.saveas == patch.sourcefile else "saving"
        saving_as_str: str = f"as '{patch.saveas}' in" if patch.saveas != patch.sourcefile else "to"
        self.log.add_note(f"{patch.action[:-1]}ing '{patch.sourcefile}' and {save_type} {saving_as_str} the '{local_folder}' {container_type}")
        return True

    def install(  # noqa: PLR0915, PLR0912, C901
        self,
        should_cancel: Event | None = None,
        progress_update_func: Callable | None = None,
    ):  # noqa: C901
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
        if self.game is None:
            msg = "Chosen KOTOR directory is not a valid installation - cannot initialize ModInstaller."
            raise RuntimeError(msg)

        memory = PatcherMemory()
        config: PatcherConfig = self.config()
        patches_list: list[PatcherModifications] = [
            *config.install_list,  # Note: TSLPatcher executes [InstallList] after [TLKList]
            *self.get_tlk_patches(config),
            *config.patches_2da,
            *config.patches_gff,
            # Note: TSLPatcher runs [CompileList] *after* [HACKList], which is objectively bad, so HoloPatcher here will do the inverse.
            *config.patches_nss,
            *config.patches_ncs,
            *config.patches_ssf,
        ]

        finished_preprocessed_scripts: bool = False
        temp_script_folder: CaseAwarePath = self.mod_path / "temp_nss_working_dir"
        for patch in patches_list:
            if should_cancel is not None and should_cancel.is_set():
                print("ModInstaller.install() received termination request, cancelling...")
                sys.exit()

            # Must run preprocessed scripts directly before GFFList so we don't interfere with !FieldPath assignments to 2DAMEMORY.
            if not finished_preprocessed_scripts and isinstance(patch, ModificationsNSS):
                self._prepare_compilelist(config, self.log, memory, self.game)
                finished_preprocessed_scripts = True

            # if self.game.is_ios():  # TODO(th3w1zard1):
            #    patch.destination = patch.destination.lower()
            output_container_path: CaseAwarePath = self.game_path / patch.destination
            try:
                exists, capsule = self.handle_capsule_and_backup(patch, output_container_path)
                if not self.should_patch(patch, exists, capsule):
                    continue

                data_to_patch: bytes | None = self.lookup_resource(patch, output_container_path, exists, capsule)
                if data_to_patch is None:
                    self.log.add_error(f"Could not locate resource to {patch.action.lower().strip()}: '{patch.sourcefile}'")
                    continue
                if not data_to_patch:
                    self.log.add_note(f"'{patch.sourcefile}' has no content/data and is completely empty.")

                patched_data: bytes | Literal[True] = patch.patch_resource(data_to_patch, memory, self.log, self.game)
                if patched_data is True:
                    self.log.add_note(f"Skipping '{patch.sourcefile}' - patch_resource determined that this file can be skipped.")
                    continue  # e.g. if nwnnsscomp tries to compile an Include script with no entrypoint

                if capsule is not None:
                    self.handle_override_type(patch)
                    self.handle_modrim_shadow(patch)
                    capsule.add(*ResourceIdentifier.from_path(patch.saveas).unpack(), patched_data)
                else:
                    # if self.game.is_ios():  # TODO(th3w1zard1):
                    #    patch.saveas = patch.saveas.lower()
                    output_container_path.mkdir(exist_ok=True, parents=True)  # Create non-existing folders when the patch demands it.
                    BinaryWriter.dump(output_container_path / patch.saveas, patched_data)
                self.log.complete_patch()
            except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
                exc_type, exc_msg = universal_simplify_exception(e)
                fmt_exc_str = f"{exc_type}: {exc_msg}"
                msg = f"An error occurred in patchlist {patch.__class__.__name__}:\n{fmt_exc_str}\n"
                self.log.add_error(msg)
                RobustLogger().exception(msg)
            if progress_update_func is not None:
                progress_update_func()

        if config.save_processed_scripts == 0 and temp_script_folder is not None and temp_script_folder.is_dir():
            self.log.add_note(f"Cleaning temporary script folder at '{temp_script_folder}' (hint: use 'SaveProcessedScripts=1' in [Settings] to keep these scripts)")  # noqa: E501
            shutil.rmtree(temp_script_folder, ignore_errors=True)

        num_patches_completed: int = config.patch_count()
        self.log.add_note(f"Successfully completed {num_patches_completed} {'patch' if num_patches_completed == 1 else 'total patches'}.")  # noqa: E501

    def _prepare_compilelist(
        self,
        config: PatcherConfig,
        log: PatchLogger,
        memory: PatcherMemory,
        game: Game,
    ) -> CaseAwarePath | None:
        """tslpatchdata should be read-only, this allows us to replace memory tokens while ensuring include scripts work correctly."""  # noqa: D403, E501
        if not config.patches_nss:
            return None

        # Move nwscript.nss to Override if there are any nss patches to do
        # This is required for any non-tslpatcher versions of nwnnsscomp.exe
        # See Libraries\PyKotor\src\pykotor\resource\formats\ncs\compilers.py for more information.
        if (self.mod_path / "nwscript.nss").is_file():
            file_install = InstallFile("nwscript.nss", replace_existing=True)
            if file_install not in config.install_list:
                config.install_list.append(file_install)

        # Copy all .nss files in the mod path, to a temp working directory
        # where we can change all the stringref/2damemory tokens without overwriting the original files.
        # First delete the temp folder if it already exists.
        temp_script_folder: CaseAwarePath = self.mod_path / "temp_nss_working_dir"
        if temp_script_folder.is_dir():
            shutil.rmtree(temp_script_folder, ignore_errors=True)
        temp_script_folder.mkdir(exist_ok=True, parents=True)
        for file in self.mod_path.iterdir():
            if file.suffix.lower() != ".nss" or not file.is_file():
                continue
            shutil.copy(file, temp_script_folder)

        # Next process the strref/2damemory in each. It's very important this function is called after 2dalist and tlklist are handled due to this.
        scripts_list: list[CaseAwarePath] = [*set(temp_script_folder.iterdir())]
        log.add_verbose(f"Preprocessing #StrRef# and #2DAMEMORY# tokens for all {len(scripts_list)} scripts, before running [CompileList]")
        for script in temp_script_folder.iterdir():
            if script.suffix.lower() != ".nss" or not script.is_file():
                continue
            log.add_verbose(f"Parsing tokens in '{script.name}'...")
            with script.open(mode="rb") as f:
                m_content = MutableString(decode_bytes_with_fallbacks(f.read()))
            ModificationsNSS(script.name).apply(m_content, memory, log, game)
            with script.open(mode="w", encoding="windows-1252") as f:
                f.write(m_content.value)

        # Store the location of the temp folder in each nss patch.
        for nss_patch in config.patches_nss:
            nss_patch.temp_script_folder = temp_script_folder
        return temp_script_folder

    def get_tlk_patches(
        self,
        config: PatcherConfig,
    ) -> list[ModificationsTLK]:
        tlk_patches: list[ModificationsTLK] = []
        patches_tlk: ModificationsTLK = config.patches_tlk

        if not patches_tlk.modifiers:
            return tlk_patches

        tlk_patches.append(patches_tlk)

        female_dialog_filename = "dialogf.tlk"
        female_dialog_file: CaseAwarePath = self.game_path / female_dialog_filename

        if female_dialog_file.is_file():
            female_tlk_patches: ModificationsTLK = deepcopy(patches_tlk)
            female_tlk_patches.sourcefile = (
                female_tlk_patches.sourcefile_f
                if (self.mod_path / female_tlk_patches.sourcefile_f).is_file()
                else patches_tlk.sourcefile
            )
            female_tlk_patches.saveas = female_dialog_filename
            tlk_patches.append(female_tlk_patches)

        return tlk_patches
