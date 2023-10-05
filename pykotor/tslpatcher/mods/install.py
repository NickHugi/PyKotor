from __future__ import annotations

import concurrent.futures
import os
import shutil
import threading
from pathlib import PurePath
from typing import TYPE_CHECKING

from pykotor.common.stream import BinaryReader, BinaryWriter
from pykotor.extract.capsule import Capsule
from pykotor.extract.file import ResourceIdentifier
from pykotor.tools.misc import is_capsule_file

if TYPE_CHECKING:
    from pykotor.tools.path import CaseAwarePath
    from pykotor.tslpatcher.logger import PatchLogger


print_lock = threading.Lock()


def create_backup(
    log: PatchLogger,
    destination_filepath: CaseAwarePath,
    backup_folderpath: CaseAwarePath,
    processed_files: set,
    subdirectory_path: os.PathLike | str | None = None,
):  # sourcery skip: extract-method
    destination_file_str = str(destination_filepath)
    destination_file_str_lower = destination_file_str.lower()
    subdirectory_backup_path = None
    if subdirectory_path:
        subdirectory_backup_path = backup_folderpath / subdirectory_path
        backup_filepath = subdirectory_backup_path / destination_filepath.name
    else:
        backup_filepath = backup_folderpath / destination_filepath.name

    if destination_file_str_lower not in processed_files and destination_filepath.exists():
        # Check if the backup path exists and generate a new one if necessary
        i = 2
        filestem = backup_filepath.stem
        while backup_filepath.exists():
            backup_filepath = backup_filepath.parent / f"{filestem} ({i}){backup_filepath.suffix}"
            i += 1

        log.add_note(f"Backing up '{destination_file_str}'...")
        if subdirectory_backup_path:
            subdirectory_backup_path.mkdir(exist_ok=True, parents=True)
        try:
            shutil.copy(destination_filepath, backup_filepath)
        except PermissionError as e:
            log.add_warning(f"Failed to create backup of '{destination_file_str}': {e}")
    else:
        # Write a list of files that should be removed in order to uninstall the mod
        uninstall_folder = backup_folderpath.parent.parent.joinpath("uninstall")
        uninstall_folder.mkdir(exist_ok=True)

        # Write the file path to remove these files.txt in backup directory
        with backup_folderpath.joinpath("remove these files.txt").open("a") as f:
            f.write("\n" + str(destination_filepath))

        # Write the PowerShell uninstall script to the uninstall folder
        subdir_temp = PurePath(subdirectory_path) if subdirectory_path else None
        game_folder = destination_filepath.parents[len(subdir_temp.parts)] if subdir_temp else destination_filepath.parent
        write_powershell_uninstall_script(backup_folderpath, uninstall_folder, game_folder)

    # Add the lowercased path string to the processed_files set
    processed_files.add(destination_file_str_lower)


def write_powershell_uninstall_script(backup_dir: CaseAwarePath, uninstall_folder: CaseAwarePath, main_folder: PurePath):
    if os.name == "nt":
        with uninstall_folder.joinpath("uninstall.ps1").open("w") as f:
            f.write(
                rf"""
#!/usr/bin/env pwsh
$backupParentFolder = Get-Item -Path "..$([System.IO.Path]::DirectorySeparatorChar)backup"
$mostRecentBackupFolder = Get-ChildItem -Path $backupParentFolder.FullName -Directory | ForEach-Object {{
    $dirName = $_.Name
    try {{
        [datetime]$dt = [datetime]::ParseExact($dirName, "yyyy-MM-dd_HH.mm.ss", $null)
        Write-Host "Found backup '$dirName'"
        return [PSCustomObject]@{{
            Directory = $_.FullName
            DateTime = $dt
        }}
    }} catch {{
        if ($dirName -and $dirName -ne '' -and -not ($dirName -match "^\s*$")) {{
            Write-Host "Ignoring directory '$dirName'. $($_.Exception.Message)"
        }}
    }}
}} | Sort-Object DateTime -Descending | Select-Object -ExpandProperty Directory -First 1
if (-not $mostRecentBackupFolder -and -not (Test-Path $mostRecentBackupFolder -ErrorAction SilentlyContinue)) {{
    $mostRecentBackupFolder = "{backup_dir}"
    if (-not (Test-Path $mostRecentBackupFolder -ErrorAction SilentlyContinue)) {{
        Write-Host "No backups found in '$backupParentFolder.FullName'"
        exit
    }}
    Write-Host "Using hardcoded backup dir: '$mostRecentBackupFolder'"
}} else {{
    Write-Host "Selected backup folder '$mostRecentBackupFolder'"
}}

$deleteListFile = $mostRecentBackupFolder + "$([System.IO.Path]::DirectorySeparatorChar)remove these files.txt"
if (-not (Test-Path $deleteListFile -ErrorAction SilentlyContinue)) {{
    Write-Host "File list not found."
    exit
}}

$filesToDelete = Get-Content $deleteListFile
$existingFiles = New-Object System.Collections.Generic.HashSet[string]
foreach ($file in $filesToDelete) {{
    if ($file) {{ # Check if $file is non-null and non-empty
        if (Test-Path $file -ErrorAction SilentlyContinue) {{
            # Check if the path is not a directory
            if (-not (Get-Item $file).PSIsContainer) {{
                $existingFiles.Add($file) | Out-Null
            }}
        }} else {{
            Write-Host "WARNING! $file no longer exists! Running this script is no longer recommended!"
        }}
    }}
}}

$numberOfExistingFiles = $existingFiles.Count

$allItemsInBackup = Get-ChildItem -Path $mostRecentBackupFolder -Recurse | Where-Object {{ $_.Name -ne 'remove these files.txt' }}
$fileCount = ($allItemsInBackup | Where-Object {{ -not $_.PSIsContainer }}).Count
$folderCount = ($allItemsInBackup | Where-Object {{ $_.PSIsContainer }}).Count

# Display relative file paths if file count is less than 6
if ($fileCount -lt 6) {{
    $allItemsInBackup |
    Where-Object {{ -not $_.PSIsContainer }} |
    ForEach-Object {{
        $relativePath = $_.FullName -replace [regex]::Escape($mostRecentBackupFolder), ""
        Write-Host $relativePath.TrimStart("\")
    }}
}}

$validConfirmations = @("y", "yes")
$confirmation = Read-Host "Really uninstall $numberOfExistingFiles files and restore the most recent backup (containing $fileCount files and $folderCount folders)?"
if ($confirmation.ToLower() -notin $validConfirmations) {{
    Write-Host "Operation cancelled."
    exit
}}

$deletedCount = 0
foreach ($file in $existingFiles) {{
    if ($file -and (Test-Path $file -ErrorAction SilentlyContinue)) {{
        Remove-Item $file -Force
        Write-Host "Removed $file..."
        $deletedCount++
    }}
}}

if ($deletedCount -ne 0) {{
    Write-Host "Deleted $deletedCount files."
}}

foreach ($file in $allItemsInBackup) {{
    try {{
        $relativePath = $file.FullName.Substring($mostRecentBackupFolder.Length)
        $destinationPath = Join-Path -Path "{main_folder}" -ChildPath $relativePath

        # Create the directory structure if it doesn't exist
        $destinationDir = [System.IO.Path]::GetDirectoryName($destinationPath)
        if (-not (Test-Path $destinationDir)) {{
            New-Item -Path $destinationDir -ItemType Directory -Force
        }}

        # Copy the file to the destination
        Copy-Item -Path $file.FullName -Destination $destinationPath -Force
        Write-Host "Restoring backup of '$($file.Name)' to '$destinationDir'..."
    }} catch {{
        Write-Host "Failed to restore backup of $($file.Name) because of: $($_.Exception.Message)"
    }}
}}
Pause

""",
            )
    elif os.name == "posix":
        with uninstall_folder.joinpath("uninstall.sh").open("w", newline="\n") as f:
            f.write(
                rf"""
#!/bin/bash

backupParentFolder="../backup"
mostRecentBackupFolder=$(ls -d "$backupParentFolder"/* | while read -r dir; do
    dirName=$(basename "$dir")
    if [[ "$dirName" =~ ^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}_[0-9]{{2}}\.[0-9]{{2}}\.[0-9]{{2}}$ ]]; then
        # Convert the directory name to a sortable format YYYYMMDDHHMMSS and echo both the sortable format and the original directory
        echo "${{dirName:0:4}}${{dirName:5:2}}${{dirName:8:2}}${{dirName:11:2}}${{dirName:14:2}}${{dirName:17:2}} $dir"
    else
        if [[ -n "$dirName" && ! "$dirName" =~ ^[[:space:]]*$ ]]; then
            echo "Ignoring directory '$dirName'" >&2
        fi
    fi
done | sort -r | awk 'NR==1 {{print $2}}')



if [[ ! -d "$mostRecentBackupFolder" ]]; then
    mostRecentBackupFolder="{backup_dir}"
    if [[ ! -d "$mostRecentBackupFolder" ]]; then
        echo "No backups found in '$backupParentFolder'"
        exit 1
    fi
    echo "Using hardcoded backup dir: '$mostRecentBackupFolder'"
else
    echo "Selected backup folder '$mostRecentBackupFolder'"
fi

deleteListFile="$mostRecentBackupFolder/remove these files.txt"
if [[ ! -f "$deleteListFile" ]]; then
    echo "File list not found."
    exit 1
fi

declare -a filesToDelete
mapfile -t filesToDelete < "$deleteListFile"
existingFiles=()
for file in "${{filesToDelete[@]}}"; do
    if [[ -n "$file" && -f "$file" ]]; then
        existingFiles+=("$file")
    else
        echo "WARNING! $file no longer exists! Running this script is no longer recommended!"
    fi
done

fileCount=$(find "$mostRecentBackupFolder" -type f ! -name 'remove these files.txt' | wc -l)
folderCount=$(find "$mostRecentBackupFolder" -type d | wc -l)

# Display relative file paths if file count is less than 6
if [[ $fileCount -lt 6 ]]; then
    find "$mostRecentBackupFolder" -type f ! -name 'remove these files.txt' | sed "s|^$mostRecentBackupFolder/||"
fi

read -rp "Really uninstall ${{#existingFiles[@]}} files and restore the most recent backup (containing $fileCount files and $folderCount folders)? " confirmation
if [[ "$confirmation" != "y" && "$confirmation" != "yes" ]]; then
    echo "Operation cancelled."
    exit 1
fi

deletedCount=0
for file in "${{existingFiles[@]}}"; do
    if [[ -f "$file" ]]; then
        rm -f "$file"
        echo "Removed $file..."
        ((deletedCount++))
    fi
done

if [[ $deletedCount -ne 0 ]]; then
    echo "Deleted $deletedCount files."
fi

while IFS= read -r -d $'\0' file; do
    relativePath=${{file#$mostRecentBackupFolder}}
    destinationPath="{main_folder}$relativePath"
    destinationDir=$(dirname "$destinationPath")
    if [[ ! -d "$destinationDir" ]]; then
        mkdir -p "$destinationDir"
    fi
    cp "$file" "$destinationPath" && echo "Restoring backup of '$(basename $file)' to '$destinationDir'..."
done < <(find "$mostRecentBackupFolder" -type f ! -name 'remove these files.txt' -print0)

read -rp "Press enter to continue..."

    """,
            )


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

        create_backup(log, destination.path(), backup_dir, processed_files, "Modules")
        if self.replace_existing or destination.resource(resname, restype) is None:
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

        with print_lock:
            create_backup(log, save_file_to, backup_dir, processed_files, local_folder)
        if self.replace_existing or not file_exists:
            # reduce io work from destination.exists() by first using our file exists check.
            if not file_exists and not destination.exists():
                with print_lock:
                    log.add_note(f"Folder '{destination}' did not exist, creating it...")
                # might exist at this point due to multithreading so we set exist_ok=True.
                destination.mkdir(parents=True, exist_ok=True)

            with print_lock:
                create_backup(log, save_file_to, backup_dir, processed_files, local_folder)
                if file_exists:
                    log.add_note(f"Replacing file '{self.filename}' in the '{local_folder}' folder...")
                else:
                    log.add_note(f"Copying file '{self.filename}' to the '{local_folder}' folder...")

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
