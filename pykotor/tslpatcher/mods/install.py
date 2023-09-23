from __future__ import annotations

import concurrent.futures
import shutil
import threading
from typing import TYPE_CHECKING

from pykotor.common.stream import BinaryReader, BinaryWriter
from pykotor.extract.capsule import Capsule
from pykotor.extract.file import ResourceIdentifier
from pykotor.tools.misc import is_capsule_file

if TYPE_CHECKING:
    import os

    from pykotor.tools.path import CaseAwarePath
    from pykotor.tslpatcher.logger import PatchLogger


print_lock = threading.Lock()


def create_backup(
    log: PatchLogger,
    destination_filepath: CaseAwarePath,
    backup_folderpath: CaseAwarePath,
    processed_files: set,
    subdirectory_path: os.PathLike | str | None = None,
):
    destination_file_str = str(destination_filepath).lower()
    if subdirectory_path:
        subdirectory_path = backup_folderpath / subdirectory_path
        subdirectory_path.mkdir(exist_ok=True, parents=True)
        backup_filepath = subdirectory_path / destination_filepath.name
    else:
        backup_filepath = backup_folderpath / destination_filepath.name

    if destination_file_str not in processed_files and destination_filepath.exists():
        # Check if the backup path exists and generate a new one if necessary
        i = 2
        filestem = backup_filepath.stem
        while backup_filepath.exists():
            backup_filepath = backup_filepath.parent / f"{filestem} ({i}){backup_filepath.suffix}"
            i += 1

        log.add_note(f"Backing up '{destination_file_str}'...")
        shutil.copy(destination_filepath, backup_filepath)

    # Add the lowercased path string to the processed_files set
    processed_files.add(destination_file_str)


class InstallFile:
    def __init__(self, filename: str, replace_existing: bool) -> None:
        self.filename: str = filename
        self.replace_existing: bool = replace_existing

    def _identifier(self) -> ResourceIdentifier:
        return ResourceIdentifier.from_path(self.filename)

    def apply_encapsulated(
        self,
        log: PatchLogger,
        source_folder: CaseAwarePath,
        destination: Capsule,
        backup_dir: CaseAwarePath,
        processed_files: set,
    ) -> None:
        resname, restype = self._identifier()

        if self.replace_existing or destination.resource(resname, restype) is None:
            create_backup(log, destination.path(), backup_dir, processed_files)
            if self.replace_existing and destination.resource(resname, restype) is not None:
                with print_lock:
                    log.add_note(f"Replacing file '{self.filename}' in the '{destination.filename()}' archive...")
            else:
                with print_lock:
                    log.add_note(f"Adding file '{self.filename}' to the '{destination.filename()}' archive...")

            data = BinaryReader.load_file(source_folder / self.filename)
            destination.add(resname, restype, data)
        else:
            log.add_warning(
                f"A file named '{self.filename}' already exists in the '{destination.filename()}' archive. Skipping file...",
            )

    def apply_file(
        self,
        log: PatchLogger,
        source_folder: CaseAwarePath,
        destination: CaseAwarePath,
        local_folder: str,
        backup_dir: CaseAwarePath,
        processed_files: set,
    ) -> None:
        data = BinaryReader.load_file(source_folder / self.filename)
        save_file_to = destination / self.filename
        file_exists: bool = save_file_to.exists()

        if self.replace_existing or not file_exists:
            # reduce io work from destination.exists() by first using our file exists check.
            if not file_exists and not destination.exists():
                with print_lock:
                    log.add_note(f"Folder '{destination}' did not exist, creating it...")
                # might exist at this point due to multithreading so we set exist_ok=True.
                destination.mkdir(parents=True, exist_ok=True)

            with print_lock:
                if file_exists:
                    log.add_note(f"Replacing file '{self.filename}' in the '{local_folder}' folder...")
                    create_backup(log, save_file_to, backup_dir, processed_files)
                else:
                    log.add_note(f"Copying file '{self.filename}' to the '{local_folder}' folder...")
                    processed_files.add(str(save_file_to).lower())

            BinaryWriter.dump(save_file_to, data)
        else:
            with print_lock:
                log.add_warning(f"A file named '{self.filename}' already exists in the '{local_folder}' folder. Skipping file...")


class InstallFolder:
    # The `InstallFolder` class represents a folder that can be installed, and it provides a method to
    # apply the installation by copying files from a source path to a destination path.
    def __init__(
        self,
        foldername: str,
        files: list[InstallFile] | None = None,
    ) -> None:
        self.foldername: str = foldername
        self.files: list[InstallFile] = files or []

    def apply(
        self,
        log: PatchLogger,
        source_path: CaseAwarePath,
        destination_path: CaseAwarePath,
        backup_dir: CaseAwarePath,
        processed_files: set,
    ):
        target: CaseAwarePath = destination_path / self.foldername

        if is_capsule_file(self.foldername):
            destination = Capsule(target, create_nonexisting=True)
            for file in self.files:
                file.apply_encapsulated(log, source_path, destination, backup_dir, processed_files)
        else:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Submit each task individually using executor.submit
                futures = [
                    executor.submit(
                        lambda file: file.apply_file(
                            log,
                            source_path,
                            target,
                            self.foldername,
                            backup_dir,
                            processed_files,
                        ),
                        file,
                    )
                    for file in self.files
                ]

                # Use as_completed to get the results as they complete
                for future in concurrent.futures.as_completed(futures):
                    try:
                        future.result()  # Process the result if needed
                    except Exception as thread_exception:
                        # Handle any exceptions that occurred during execution
                        with print_lock:  # Acquire the lock before printing
                            log.add_error(f"Exception occurred: {thread_exception}")
