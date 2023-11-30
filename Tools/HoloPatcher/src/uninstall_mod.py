from __future__ import annotations

import os
import shutil
from datetime import datetime
from tkinter import messagebox

from pykotor.tslpatcher.logger import PatchLogger
from utility.error_handling import universal_simplify_exception
from utility.path import Path


class ModUninstaller:
    def __init__(self, backups_location_path: Path, game_path: Path, logger: PatchLogger | None = None):
        self.backups_location_path: Path = backups_location_path
        self.game_path: Path = game_path
        self.log: PatchLogger = logger or PatchLogger()

    @staticmethod
    def is_valid_backup_folder(folder: Path) -> bool:
        """Check if a folder name is valid backup folder format, i.e. the folder name can be parsed to datetime
        Args:
            folder: Path object to check folder name
        Returns:
            bool: True if valid backup folder format, False otherwise
        Checks if folder name can be parsed to datetime.
        """
        try:
            datetime.strptime(folder.name, "%Y-%m-%d_%H.%M.%S").astimezone()
        except ValueError:
            return False
        else:
            return True

    @staticmethod
    def get_most_recent_backup(backup_folder_path: Path) -> Path | None:
        valid_backups: list[Path] = [
            subfolder
            for subfolder in backup_folder_path.iterdir()
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

    def restore_backup(self, backup_folder: Path, existing_files: set[str], files_in_backup: list[Path]) -> None:
        for file in existing_files:
            file_path = Path(file)
            rel_filepath = file_path.relative_to(self.game_path)
            file_path.unlink(missing_ok=True)
            self.log.add_note(f"Removed {rel_filepath}...")
        for file_path in files_in_backup:
            destination_path = self.game_path / file_path.relative_to(backup_folder)
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(file_path, destination_path)
            self.log.add_note(f"Restoring backup of '{file_path.name}' to '{destination_path.relative_to(self.game_path.parent)}'...")

    def get_backup_info(self) -> tuple[Path | None, set[str], list[Path], int]:
        """Get info about the most recent valid backup."""
        most_recent_backup_folder = self.get_most_recent_backup(self.backups_location_path)
        if not most_recent_backup_folder:
            return None, set(), [], 0

        delete_list_file = most_recent_backup_folder / "remove these files.txt"
        existing_files: set[str] = set()
        if delete_list_file.exists():
            with delete_list_file.open("r") as f:
                file_lines = [line.strip() for line in f if line.strip()]
                existing_files = {line.strip() for line in f if line.strip() and Path(line.strip()).is_file()}
            if len(existing_files) < len(file_lines) and not messagebox.askyesno(
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
        while not messagebox.askyesno(
            "Confirmation",
            f"Really uninstall {len(existing_files)} files and restore the most recent backup (containing {len(files_in_backup)} files and {folder_count} folders)?",
        ):
            try:
                self.restore_backup(most_recent_backup_folder, existing_files, files_in_backup)
            except Exception as e:  # noqa: BLE001, PERF203
                error_name, msg = universal_simplify_exception(e)
                messagebox.showerror(
                    error_name,
                    f"Failed to restore backup because of exception. Please try again:{os.linesep*2}{msg}",
                )
            else:
                break
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
