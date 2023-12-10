from __future__ import annotations

import os
import shutil
from datetime import datetime
from tkinter import messagebox

from pykotor.tslpatcher.logger import PatchLogger
from utility.error_handling import universal_simplify_exception
from utility.path import Path


class ModUninstaller:
    """A class that provides functionality to uninstall a selected mod using the most recent backup folder created during the last install.

    Args:
    ----
        backups_location_path (Path): The path to the location of the backup folders.
        game_path (Path): The path to the game folder.
        logger (PatchLogger | None, optional): An optional logger object. Defaults to a new PatchLogger.

    Attributes:
    ----------
        backups_location_path (Path): The path to the location of the backup folders.
        game_path (Path): The path to the game folder.
        log (PatchLogger): The logger object.

    Methods:
    -------
        is_valid_backup_folder(folder: Path, datetime_pattern="%Y-%m-%d_%H.%M.%S") -> bool:
            Check if a folder name is a valid backup folder name based on a datetime pattern.
        get_most_recent_backup(backup_folder_path: Path) -> Path | None:
            Returns the most recent valid backup folder.
        restore_backup(backup_folder: Path, existing_files: set[str], files_in_backup: list[Path]) -> None:
            Restores a game backup folder to the existing game files.
        get_backup_info() -> tuple[Path | None, set[str], list[Path], int]:
            Get information about the most recent valid backup.
        uninstall_selected_mod() -> None:
            Uninstalls the selected mod using the most recent backup folder created during the last install.
    """

    def __init__(self, backups_location_path: Path, game_path: Path, logger: PatchLogger | None = None):
        self.backups_location_path: Path = backups_location_path
        self.game_path: Path = game_path
        self.log: PatchLogger = logger or PatchLogger()

    @staticmethod
    def is_valid_backup_folder(folder: Path, datetime_pattern="%Y-%m-%d_%H.%M.%S") -> bool:
        """Check if a folder name is valid backup folder name based on datetime pattern.

        Args:
        ----
            folder: Path object of the folder to validate
            datetime_pattern: String pattern to match folder name against (default: "%Y-%m-%d_%H.%M.%S").

        Returns:
        -------
            bool: True if folder name matches datetime pattern, False otherwise

        Processing Logic:
        ----------------
            - Try to parse folder name as datetime string with given pattern
            - Return True if parsing succeeds without error
            - Return False if parsing fails with ValueError
        """
        try:
            datetime.strptime(folder.name, datetime_pattern).astimezone()
        except ValueError:
            return False
        else:
            return True

    @staticmethod
    def get_most_recent_backup(backup_folder: os.PathLike | str) -> Path | None:
        """Returns the most recent valid backup folder.

        Args:
        ----
            backup_folder: os.PathLike | str - Path to the backup folder.

        Returns:
        -------
            Path | None: Path to the most recent valid backup folder or None

        Processing Logic:
        ----------------
            - Filter subfolders to only valid backup folders
            - Return None if no valid backups found
            - Otherwise return the subfolder with the maximum datetime parsed from folder name.
        """
        backup_folder_path = backup_folder if isinstance(backup_folder, Path) else Path(backup_folder)
        valid_backups: list[Path] = [
            subfolder
            for subfolder in backup_folder_path.iterdir()  # type: ignore[attr-defined]
            if subfolder.is_dir() and ModUninstaller.is_valid_backup_folder(subfolder)
        ]
        if not valid_backups:
            messagebox.showerror(
                "No backups found!",
                f"No backups found at '{backup_folder_path}'!{os.linesep}"
                "HoloPatcher cannot uninstall TSLPatcher.exe installations.",
            )
            return None
        return max(valid_backups, key=lambda x: datetime.strptime(x.name, "%Y-%m-%d_%H.%M.%S").astimezone())

    def restore_backup(
        self,
        backup_folder: Path,
        existing_files,
        files_in_backup,
    ) -> None:
        """Restores a game backup folder to the existing game files.

        Args:
        ----
            backup_folder: Path to the backup folder
            existing_files: set of existing file paths
            files_in_backup: list of file paths in the backup

        Processing Logic:
        ----------------
            - Remove any existing files not in the backup
            - Copy each file from the backup folder to the destination restoring the file structure
            - Log each file operation

        Examples:
        --------
            restore_backup(Path('backup'), {'file1.txt', 'file2.txt'}, [Path('backup/file1.txt'), Path('backup/file2.txt')])
        """
        for file in existing_files:
            file_path = file if isinstance(file, Path) else Path(file)
            rel_filepath = file_path.relative_to(self.game_path)  # type: ignore[attr-defined]
            file_path.unlink(missing_ok=True)  # type: ignore[attr-defined]
            self.log.add_note(f"Removed {rel_filepath}...")
        for file in files_in_backup:
            file_path = file if isinstance(file, Path) else Path(file)
            destination_path = self.game_path / file_path.relative_to(backup_folder)  # type: ignore[attr-defined]
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(file_path, destination_path)
            self.log.add_note(f"Restoring backup of '{file_path.name}' to '{destination_path.relative_to(self.game_path.parent)}'...")  # type: ignore[attr-defined]

    def get_backup_info(self) -> tuple[Path | None, set[str], list[Path], int]:
        """Get info about the most recent valid backup."""
        most_recent_backup_folder = self.get_most_recent_backup(self.backups_location_path)
        if not most_recent_backup_folder:
            return None, set(), [], 0

        delete_list_file = most_recent_backup_folder / "remove these files.txt"
        files_to_delete: set[str] = set()
        existing_files: set[str] = set()
        if delete_list_file.exists():
            with delete_list_file.open("r") as f:
                files_to_delete = {line.strip() for line in f if line.strip()}
                existing_files = {line.strip() for line in files_to_delete if line.strip() and Path(line.strip()).is_file()}
            if len(existing_files) < len(files_to_delete) and not messagebox.askyesno(
                    "Backup out of date or mismatched",
                    (
                        f"This backup doesn't match your current KOTOR installation. Files are missing/changed in your KOTOR install.{os.linesep}"
                        f"It is important that you uninstall all mods in their installed order when utilizing this feature.{os.linesep}"
                        f"Also ensure you selected the right mod, and the right KOTOR folder.{os.linesep}"
                        "Continue anyway?"
                    ),
            ):
                return None, set(), [], 0

        files_in_backup = list(filter(Path.is_file, most_recent_backup_folder.rglob("*")))
        folder_count: int = len(list(most_recent_backup_folder.rglob("*"))) - len(files_in_backup)

        return most_recent_backup_folder, existing_files, files_in_backup, folder_count

    def uninstall_selected_mod(self) -> None:
        """Uninstalls the selected mod using the most recent backup folder created during the last install.

        Processing Logic:
        ----------------
            - Check if an install is already running
            - Get the selected namespace option
            - Check for valid namespace and game path
            - Get the backup folder path
            - Sort backup folders by date
            - Get the most recent backup folder
            - Check for required files in backup
            - Confirm uninstall with user
            - Delete existing files
            - Restore files from backup
            - Offer to delete restored backup.
        """
        most_recent_backup_folder, existing_files, files_in_backup, folder_count = self.get_backup_info()
        if not most_recent_backup_folder:
            return
        self.log.add_note(f"Using backup folder '{most_recent_backup_folder}'")

        if len(files_in_backup) < 6:  # noqa: PLR2004[6 represents a small number of files to display]
            for item in files_in_backup:
                self.log.add_note(f"Would restore file '{item.relative_to(most_recent_backup_folder)!s}'")
        if not messagebox.askyesno(
            "Confirmation",
            f"Really uninstall {len(existing_files)} files and restore the most recent backup (containing {len(files_in_backup)} files and {folder_count} folders)?",
        ):
            return
        try:
            self.restore_backup(most_recent_backup_folder, existing_files, files_in_backup)
        except Exception as e:  # noqa: BLE001
            error_name, msg = universal_simplify_exception(e)
            messagebox.showerror(
                error_name,
                f"Failed to restore backup because of exception.{os.linesep*2}{msg}",
            )
        while messagebox.askyesno(
            "Uninstall completed!",
            f"Deleted {len(existing_files)} files and successfully restored backup {most_recent_backup_folder.name}{os.linesep*2}"
            f"Would you like to delete the backup {most_recent_backup_folder.name} now that it's been restored?",
        ):
            try:
                shutil.rmtree(most_recent_backup_folder)
                self.log.add_note(f"Deleted restored backup '{most_recent_backup_folder.name}'")
            except PermissionError:  # noqa: PERF203
                messagebox.showerror(
                    "Permission Error",
                    "Unable to delete the restored backup due to permission issues. Please try again.",
                )
            else:
                break
