from __future__ import annotations

import shutil

from pathlib import PurePath
from typing import TYPE_CHECKING, Any

from pykotor.common.stream import BinaryReader
from pykotor.tslpatcher.mods.template import PatcherModifications
from utility.error_handling import universal_simplify_exception

if TYPE_CHECKING:
    import os

    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]

    from pykotor.common.misc import Game
    from pykotor.resource.type import SOURCE_TYPES
    from pykotor.tools.path import CaseAwarePath
    from pykotor.tslpatcher.logger import PatchLogger
    from pykotor.tslpatcher.memory import PatcherMemory


def create_backup(
    log: PatchLogger,
    destination_filepath: CaseAwarePath,
    backup_folderpath: CaseAwarePath,
    processed_files: set,
    subdirectory_path: os.PathLike | str | None = None,
):
    """Creates a backup of the provided file.

    Args:
    ----
        log: PatchLogger - Logger for logging messages
        destination_filepath: CaseAwarePath - Filepath to backup
        backup_folderpath: CaseAwarePath - Folder to store backups
        processed_files: set - Set of already backed up files
        subdirectory_path: os.PathLike/str/None - Optional subdirectory path

    Processing Logic:
    ----------------
        - Checks if file exists at destination_filepath
        - Copies file to backup folder if it exists
        - Generates new backup filename if one already exists
        - Logs backup action
        - Adds file path to processed_files set.
    """
    destination_file_str = str(destination_filepath)
    destination_file_str_lower: str = destination_file_str.lower()
    subdirectory_backup_path: CaseAwarePath | None = None
    backup_filepath: CaseAwarePath
    if subdirectory_path:
        subdirectory_backup_path = backup_folderpath / subdirectory_path
        backup_filepath = subdirectory_backup_path / destination_filepath.name
    else:
        backup_filepath = backup_folderpath / destination_filepath.name

    if destination_file_str_lower not in processed_files:
        # Write a list of files that should be removed in order to uninstall the mod
        uninstall_folder: CaseAwarePath = backup_folderpath.parent.parent.joinpath("uninstall")
        uninstall_str_lower: str = str(uninstall_folder).lower()
        if uninstall_str_lower not in processed_files:
            uninstall_folder.mkdir(exist_ok=True)

            # Write the PowerShell/Bash uninstall scripts to the uninstall folder
            subdir_temp: PurePath | None = PurePath(subdirectory_path) if subdirectory_path else None
            game_folder: CaseAwarePath = destination_filepath.parents[len(subdir_temp.parts)] if subdir_temp else destination_filepath.parent
            create_uninstall_scripts(backup_folderpath, uninstall_folder, game_folder)
            processed_files.add(uninstall_str_lower)

        if destination_filepath.is_file():
            # Check if the backup path exists and generate a new one if necessary
            i = 2
            filestem: str = backup_filepath.stem
            while backup_filepath.exists():
                backup_filepath = backup_filepath.parent / f"{filestem} ({i}){backup_filepath.suffix}"
                i += 1

            log.add_note(f"Backing up '{destination_file_str}'...")
            if subdirectory_backup_path:
                subdirectory_backup_path.mkdir(exist_ok=True, parents=True)
            try:  # sourcery skip: remove-redundant-exception
                shutil.copy(destination_filepath, backup_filepath)
            except (OSError, PermissionError) as e:
                log.add_warning(f"Failed to create backup of '{destination_file_str}': {universal_simplify_exception(e)}")
        else:
            # Write the file path to remove these files.txt in backup directory
            removal_files_txt: CaseAwarePath = backup_folderpath.joinpath("remove these files.txt")
            line: str = ("\n" if removal_files_txt.is_file() else "") + destination_file_str
            with removal_files_txt.open(mode="a", encoding="utf-8") as f:
                f.write(line)

        # Add the lowercased path string to the processed_files set
        processed_files.add(destination_file_str_lower)


def create_uninstall_scripts(
    backup_dir: CaseAwarePath,
    uninstall_folder: CaseAwarePath,
    main_folder: CaseAwarePath,
):
    with uninstall_folder.joinpath("uninstall.ps1").open("w", encoding="utf-8") as f:
        f.write(
            rf"""#!/usr/bin/env pwsh
$backupParentFolder = Get-Item -Path "..$([System.IO.Path]::DirectorySeparatorChar)backup"
$mostRecentBackupFolder = Get-ChildItem -LiteralPath $backupParentFolder.FullName -Directory | ForEach-Object {{
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
if ($null -eq $mostRecentBackupFolder -or -not $mostRecentBackupFolder -or -not (Test-Path -LiteralPath $mostRecentBackupFolder -ErrorAction SilentlyContinue)) {{
    $mostRecentBackupFolder = "{backup_dir}"
    if (-not (Test-Path -LiteralPath $mostRecentBackupFolder -ErrorAction SilentlyContinue)) {{
        Write-Host "No backups found in '$($backupParentFolder.FullName)'"
        Pause
        exit
    }}
    Write-Host "Using hardcoded backup dir: '$mostRecentBackupFolder'"
}} else {{
    Write-Host "Selected backup folder '$mostRecentBackupFolder'"
}}

$deleteListFile = $mostRecentBackupFolder + "$([System.IO.Path]::DirectorySeparatorChar)remove these files.txt"
$existingFiles = New-Object System.Collections.Generic.HashSet[string]
if (-not (Test-Path -LiteralPath $deleteListFile -ErrorAction SilentlyContinue)) {{
    Write-Host "Delete file list not found."
    #exit
}} else {{
    $filesToDelete = Get-Content -LiteralPath $deleteListFile
    foreach ($file in $filesToDelete) {{
        if ($file) {{ # Check if $file is non-null and non-empty
            if (Test-Path -LiteralPath $file -ErrorAction SilentlyContinue) {{
                # Check if the path is not a directory
                if (-not (Get-Item -LiteralPath $file).PSIsContainer) {{
                    $existingFiles.Add($file) | Out-Null
                }}
            }} else {{
                Write-Host "WARNING! $file no longer exists! Running this script is no longer recommended!"
            }}
        }}
    }}
}}


$numberOfExistingFiles = $existingFiles.Count

$allItemsInBackup = Get-ChildItem -LiteralPath $mostRecentBackupFolder -Recurse | Where-Object {{ $_.Name -ne 'remove these files.txt' }}
$filesInBackup = ($allItemsInBackup | Where-Object {{ -not $_.PSIsContainer }})
$folderCount = ($allItemsInBackup | Where-Object {{ $_.PSIsContainer }}).Count

# Display relative file paths if file count is less than 6
if ($filesInBackup.Count -lt 6) {{
    $allItemsInBackup |
    Where-Object {{ -not $_.PSIsContainer }} |
    ForEach-Object {{
        $relativePath = $_.FullName -replace [regex]::Escape($mostRecentBackupFolder), ""
        Write-Host $relativePath.TrimStart("\")
    }}
}}

$validConfirmations = @("y", "yes")
$confirmation = Read-Host "Really uninstall $numberOfExistingFiles files and restore the most recent backup (containing $($filesInBackup.Count) files and $folderCount folders)? (y/N)"
if ($confirmation.Trim().ToLower() -notin $validConfirmations) {{
    Write-Host "Operation cancelled."
    exit
}}

$deletedCount = 0
foreach ($file in $existingFiles) {{
    if ($file -and (Test-Path -LiteralPath $file -ErrorAction SilentlyContinue)) {{
        Remove-Item $file -Force
        Write-Host "Removed $file..."
        $deletedCount++
    }}
}}

if ($deletedCount -ne 0) {{
    Write-Host "Deleted $deletedCount files."
}}

foreach ($file in $filesInBackup) {{
    try {{
        $relativePath = $file.FullName.Substring($mostRecentBackupFolder.Length)
        $destinationPath = Join-Path "{main_folder}" -ChildPath $relativePath

        # Create the directory structure if it doesn't exist
        $destinationDir = [System.IO.Path]::GetDirectoryName($destinationPath)
        if (-not (Test-Path -LiteralPath $destinationDir)) {{
            New-Item -LiteralPath $destinationDir -ItemType Directory -Force
        }}

        # Copy the file to the destination
        Copy-Item -LiteralPath $file.FullName -Destination $destinationPath -Force
        Write-Host "Restoring backup of '$($file.Name)' to '$destinationDir'..."
    }} catch {{
        Write-Host "Failed to restore backup of $($file.Name) because of: $($_.Exception.Message)"
    }}
}}
Pause
""",  # noqa: E501
        )
    with uninstall_folder.joinpath("uninstall.sh").open("w", encoding="utf-8", newline="\n") as f:
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
        read -rp "Press enter to continue..."
        exit 1
    fi
    echo "Using hardcoded backup dir: '$mostRecentBackupFolder'"
else
    echo "Selected backup folder '$mostRecentBackupFolder'"
fi

existingFiles=()
deleteListFile="$mostRecentBackupFolder/remove these files.txt"
if [[ ! -f "$deleteListFile" ]]; then
    echo "File list not found."
    #exit 1
else
    declare -a filesToDelete
    mapfile -t filesToDelete < "$deleteListFile"
    echo "Building file lists..."
    for file in "${{filesToDelete[@]}}"; do
        normalizedFile=$(echo "$file" | tr '\\' '/')
        if [[ -n "$file" && -f "$file" ]]; then
            existingFiles+=("$file")
        else
            echo "WARNING! $file no longer exists! Running this script is no longer recommended!"
        fi
    done
fi


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
    destinationPath="{main_folder}/$relativePath"
    destinationDir=$(dirname "$destinationPath")
    if [[ ! -d "$destinationDir" ]]; then
        mkdir -p "$destinationDir"
    fi
    cp "$file" "$destinationPath" && echo "Restoring backup of '$(basename $file)' to '$destinationDir'..."
done < <(find "$mostRecentBackupFolder" -type f ! -name 'remove these files.txt' -print0)

read -rp "Press enter to continue..."

    """,  # noqa: E501
        )


class InstallFile(PatcherModifications):
    def __init__(
        self,
        filename: str,
        *,
        replace_existing: bool | None = None,
        destination: str | None = None,
    ):
        super().__init__(filename, replace=bool(replace_existing), destination=destination)

        self.action: str = "Copy "
        self.skip_if_not_replace: bool = True

    def __hash__(self):  # HACK(th3w1zard1): organize this into PatcherModifications class later, this is only used for nwscript.nss currently.
        return hash((self.destination, self.saveas, self.replace_file))

    def patch_resource(
        self,
        source: SOURCE_TYPES,
        memory: PatcherMemory,
        logger: PatchLogger,
        game: Game,
    ) -> bytes | Literal[True]:
        self.apply(source, memory, logger, game)
        with BinaryReader.from_auto(source) as reader:
            return reader.read_all()

    def apply(
        self,
        mutable_data: Any,
        memory: PatcherMemory,
        logger: PatchLogger,
        game: Game
    ):
        ...
