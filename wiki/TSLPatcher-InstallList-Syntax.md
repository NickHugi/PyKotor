# TSLPatcher InstallList Syntax Documentation

This guide explains how to install files using TSLPatcher syntax. For general TSLPatcher information, see [TSLPatcher's Official Readme](TSLPatcher's-Official-Readme). For HoloPatcher-specific information, see [HoloPatcher README for Mod Developers](HoloPatcher-README-for-mod-developers.).

## Overview

The `[InstallList]` section in TSLPatcher's changes.ini file enables you to copy files from your mod's `tslpatchdata` folder to their proper location in the game installation. This includes installing files to folders (such as `Override`, `Modules`, `StreamVoice`, etc.) or directly into ERF/RIM/MOD archive files. Unlike other patch lists, InstallList is designed for copying files that haven't been modified by other sections.

**Important:** Do **not** add any files that have been modified by any of the other sections ([GFFList](TSLPatcher-GFFList-Syntax), CompileList, [2DAList](TSLPatcher-2DAList-Syntax), etc.) to the InstallList, or the modified files might be overwritten! The other sections already handle saving files to their proper locations. The only exception to this is ERF files which have had files added to them by those sections. They must still be added to the InstallList to be put in their proper places.

## Table of Contents

- [Basic Structure](#basic-structure)
- [Processing Order](#processing-order)
- [Folder-Level Configuration](#folder-level-configuration)
- [File-Level Configuration](#file-level-configuration)
- [File Replacement Behavior](#file-replacement-behavior)
- [Installing to Folders](#installing-to-folders)
- [Installing to Archives](#installing-to-archives)
- [Renaming Files](#renaming-files)
- [Source Folder Configuration](#source-folder-configuration)
- [Override Type Handling](#override-type-handling)
- [Examples](#examples)
- [Special Cases and Edge Cases](#special-cases-and-edge-cases)
- [Troubleshooting](#troubleshooting)

## Basic Structure

The InstallList uses a two-level hierarchical structure:

```ini
[InstallList]
Folder0=Override
Folder1=Modules
Folder2=StreamVoice\AVO\_HuttHap

[Override]
File0=my_texture.tpc
File1=my_script.ncs
Replace0=existing_file.tpc

[Modules]
!SourceFolder=modules
File0=new_module.mod

[StreamVoice\AVO\_HuttHap]
File0=sound1.wav
File1=sound2.wav
```

### Structure Explanation

1. **`[InstallList]` section**: Contains keys that map to folder destination names. Each key (like `Folder0`, `Folder1`, etc.) should reference a section with the same name as the value (the destination folder).

2. **Folder sections** (e.g., `[Override]`, `[Modules]`): Contain the list of files to install to that folder, along with optional folder-level configuration.

3. **File sections** (optional): Individual files can have their own sections for per-file configuration options.

## Processing Order

In **HoloPatcher**, the InstallList runs **first** in the patch execution order:

1. **[InstallList]** - Files are installed first
2. **[TLKList]** - TLK modifications
3. **[2DAList]** - 2DA file modifications
4. **[GFFList]** - GFF file modifications
5. **[CompileList]** - Script compilation
6. **[HACKList]** - Binary hacking
7. **[SSFList]** - Sound set modifications

**Note:** In original TSLPatcher, InstallList executes **after** TLKList, but HoloPatcher changed this order to allow installing a whole dialog.tlk file before TLK modifications are applied. This priority change should not affect the output of mods.

## Folder-Level Configuration

Each folder section (e.g., `[Override]`) supports the following configuration keys:

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `!SourceFolder` | string | `.` (tslpatchdata folder) | Relative path from `mod_path` (typically the `tslpatchdata` folder, the parent directory of `changes.ini` or `namespaces.ini`) where files should be sourced from. The default value `.` refers to the `tslpatchdata` folder itself, not its parent directory. Path resolution: `mod_path / !SourceFolder / filename`. **HoloPatcher extension** - allows subfolder organization within tslpatchdata. |

### Folder Section File List Keys

The folder section contains the list of files to install. Each file entry uses one of two syntaxes:

| Key Format | Replace Behavior | Description |
|------------|-----------------|-------------|
| `File#=filename.ext` | No replacement | Install the file only if it doesn't already exist at the destination. If the file exists, it will be skipped (warning logged). |
| `Replace#=filename.ext` | Replacement enabled | Install the file and overwrite any existing file at the destination. |

**Syntax Notes:**
- `#` is a sequential number starting from 0 (File0, File1, File2, ..., Replace0, Replace1, etc.)
- Numbers can be sequential, but gaps are allowed (File0, File2, File5 is valid)
- Case-insensitive matching is used for the prefix (file, replace, File, Replace all work)
- The filename can include subdirectories if using `!SourceFolder`

**Examples:**

```ini
[Override]
File0=texture1.tpc
File1=texture2.tpc
Replace0=existing.tpc
Replace1=another_existing.tpc
File2=subfolder\texture3.tpc
```

## File-Level Configuration

Each file can optionally have its own section (e.g., `[my_texture.tpc]`) for per-file configuration:

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `!SourceFile` | string | Same as filename in File#/Replace# entry | Alternative source filename to load from tslpatchdata. The file will be installed with the name specified in the File#/Replace# entry (or `!SaveAs`/`!Filename` if specified). |
| `!SaveAs` | string | Same as `!SourceFile` | The final filename to save the file as at the destination. Allows renaming during installation. |
| `!Filename` | string | Same as `!SaveAs` | Alias for `!SaveAs`. Both keys are equivalent. |
| `!Destination` | string | Inherited from folder section name | Override the destination folder for this specific file. Can specify a different folder or archive path. |
| `!ReplaceFile` | 0/1 | Determined by File#/Replace# prefix | Whether to replace existing files. Takes priority over the File#/Replace# prefix syntax. `1` = replace, `0` = don't replace. |
| `!SourceFolder` | string | Inherited from folder section `!SourceFolder` | Override the source folder for this specific file. Relative path within tslpatchdata. |
| `!OverrideType` | `ignore`/`warn`/`rename` | `warn` (HoloPatcher) / `ignore` (TSLPatcher) | How to handle conflicts when installing to archives. See [Override Type Handling](#override-type-handling) section. |

### Example with File-Level Configuration

```ini
[InstallList]
Folder0=Override

[Override]
File0=source_texture.tpc
File1=renamed_script.ncs

[source_texture.tpc]
!SourceFile=original_name.tpc
!SaveAs=final_texture.tpc
!Destination=textures

[renamed_script.ncs]
!Filename=custom_name.ncs
!ReplaceFile=1
```

## File Replacement Behavior

InstallList has special behavior regarding file replacement that differs from other patch lists:

### Skip If Not Replace

InstallList (and CompileList) use `skip_if_not_replace=True`, which means:

- If `!ReplaceFile=0` (or using `File#=` syntax) **and** the file already exists at the destination:
  - The file will be **skipped** (not installed)
  - A note is logged: `'filename.ext' already exists in the 'destination' folder. Skipping file...`
  - No error is raised - this is expected behavior

- If `!ReplaceFile=1` (or using `Replace#=` syntax) **and** the file already exists:
  - The file will be **replaced** (overwritten)
  - A note is logged: `Copying 'filename.ext' and replacing existing file in the 'destination' folder`

- If the file does **not** exist:
  - The file will be installed normally
  - A note is logged: `Copying 'filename.ext' and saving to the 'destination' folder`

### Replacement Priority

1. **`!ReplaceFile`** key (if present) takes **highest priority**
2. **`Replace#=`** prefix syntax (if `!ReplaceFile` not specified)
3. **`File#=`** prefix syntax (default, no replacement)

**Example:**

```ini
[Override]
Replace0=example.tpc

[example.tpc]
!ReplaceFile=0
```

In this case, even though `Replace0=` was used, `!ReplaceFile=0` takes priority, so the file will NOT replace existing files.

## Installing to Folders

### Standard Game Folders

The most common use case is installing files to standard game folders:

```ini
[InstallList]
Folder0=Override
Folder1=Modules
Folder2=StreamVoice
Folder3=StreamMusic
Folder4=StreamWaves

[Override]
File0=my_texture.tpc
File1=my_item.uti

[Modules]
File0=custom_module.mod

[StreamVoice]
File0=voice_line.wav

[StreamMusic]
File0=background_music.mp3

[StreamWaves]
File0=sound_effect.wav
```

### Subdirectories

You can install files into subdirectories by specifying the relative path with backslashes:

```ini
[InstallList]
Folder0=StreamVoice\AVO\_HuttHap

[StreamVoice\AVO\_HuttHap]
File0=conversation1.wav
File1=conversation2.wav
```

**Important Notes:**
- Use **backslashes** (`\`) for path separators (TSLPatcher convention)
- HoloPatcher/PyKotor will normalize both forward slashes (`/`) and backslashes (`\`)
- If the specified folder path does not exist, it will be **automatically created**
- Folder creation happens recursively (parent folders are created as needed)

### Game Root Folder

To install files directly into the game root folder, use `.\` as the folder name:

```ini
[InstallList]
Folder0=.\

[.\]
File0=readme.txt
File1=config.ini
```

**Note:** In logs, `.\` is reported as the "Game" folder for clarity.

### Default Destination

You can set a default destination for all files in InstallList using `!DefaultDestination`:

```ini
[InstallList]
!DefaultDestination=Override
Folder0=Override
Folder1=Modules

[Override]
File0=file1.tpc

[Modules]
File0=file2.mod
```

**Note:** `!DefaultDestination` is highly undocumented in TSLPatcher. In PyKotor/HoloPatcher, it is believed to take priority over folder section destinations, except when `!Destination` is explicitly set in a file section.

## Installing to Archives

InstallList supports installing files directly into ERF/MOD/RIM archive files. This is done by specifying the archive file path (relative to the game folder) as the destination.

### Archive File Syntax

```ini
[InstallList]
Folder0=Modules\901myn.mod
Folder1=Modules\custom_module.rim

[Modules\901myn.mod]
File0=new_resource.uti
File1=new_texture.tpc
Replace0=existing_resource.uti

[Modules\custom_module.rim]
File0=another_resource.2da
```

### Archive Behavior

- If the archive **does not exist** at the specified path:
  - An error is logged: `The capsule 'Modules\901myn.mod' did not exist when attempting to copy 'filename.ext'. Skipping file...`
  - The patch is skipped (no error is raised, execution continues)

- If the archive **exists**:
  - The file is added to the archive
  - If a resource with the same name already exists in the archive:
    - If `!ReplaceFile=1` or `Replace#=`: The existing resource is overwritten
    - If `!ReplaceFile=0` or `File#=`: The file is skipped (see [File Replacement Behavior](#file-replacement-behavior))

- **Archive Types Supported:**
  - `.mod` (MOD/ERF format)
  - `.erf` (ERF format)
  - `.rim` (RIM format)
  - `.sav` (Save game ERF format)

### Installing Modified Archives

If you've modified an archive using GFFList or CompileList (e.g., added resources to it), you **must** include that archive in InstallList to save it to its proper location:

```ini
[GFFList]
File0=Modules\901myn.mod

[Modules\901myn.mod]
; ... GFF modifications ...

[InstallList]
Folder0=Modules

[Modules]
Replace0=901myn.mod  ; Must include to save the modified archive
```

## Renaming Files

You can rename files during installation using `!SaveAs` or `!Filename`:

```ini
[InstallList]
Folder0=Override

[Override]
File0=source_name.tpc

[source_name.tpc]
!SourceFile=original_filename.tpc
!SaveAs=final_filename.tpc
```

This will:
1. Load `original_filename.tpc` from tslpatchdata
2. Install it as `final_filename.tpc` to the Override folder

**Notes:**
- `!SaveAs` and `!Filename` are equivalent - use either one
- If `!SourceFile` is not specified, the filename from the File#/Replace# entry is used as the source
- The source file must exist in the tslpatchdata folder (or `!SourceFolder` if specified)

## Source Folder Configuration

### Folder-Level Source Folder

You can specify a source folder for all files in a folder section:

```ini
[InstallList]
Folder0=Override

[Override]
!SourceFolder=textures
File0=texture1.tpc
File1=texture2.tpc
```

This will look for files in `tslpatchdata\textures\` instead of `tslpatchdata\`.

### File-Level Source Folder

You can override the source folder for individual files:

```ini
[InstallList]
Folder0=Override

[Override]
!SourceFolder=default_folder
File0=file1.tpc
File1=file2.tpc

[file1.tpc]
!SourceFolder=custom_folder
```

In this example:
- `file1.tpc` is loaded from `tslpatchdata\custom_folder\`
- `file2.tpc` is loaded from `tslpatchdata\default_folder\`

### Source Folder Notes

- `!SourceFolder` is a **HoloPatcher extension** - original TSLPatcher may not support this feature
- Paths are relative to the `tslpatchdata` folder
- Use `.` (period) to reference the root tslpatchdata folder explicitly
- Supports subdirectory paths: `!SourceFolder=subfolder\deeper\folder`
- Backslashes and forward slashes are both normalized

## Override Type Handling

When installing files to archives (ERF/MOD/RIM), there's a potential conflict: a file might already exist in the Override folder with the same name. The `!OverrideType` setting controls how this conflict is handled:

| Value | Behavior | Description |
|-------|----------|-------------|
| `ignore` | No action | Do nothing - don't even check for conflicts. This is the TSLPatcher default. |
| `warn` | Log warning | Check for conflicts and log a warning if found, but continue with installation. This is the HoloPatcher default. |
| `rename` | Rename override file | If a conflicting file exists in Override, rename it with an `old_` prefix (e.g., `old_filename.ext`) and log a warning. |

**Example:**

```ini
[Modules\901myn.mod]
File0=resource.uti
!OverrideType=warn
```

**Why This Matters:**

The game's resource loading system checks folders in this order:
1. Override folder (highest priority)
2. Module archives (.mod files)
3. RIM files
4. Other archives

If a file exists in both Override and an archive, the Override version takes precedence. The `!OverrideType` setting helps manage this shadowing behavior.

## Examples

### Example 1: Basic Installation to Override

```ini
[InstallList]
Folder0=Override

[Override]
File0=my_texture.tpc
File1=my_item.uti
File2=my_script.ncs
Replace0=existing_file.tpc
```

### Example 2: Installing to Multiple Folders with Source Folders

```ini
[InstallList]
Folder0=Override
Folder1=StreamVoice\AVO\_HuttHap
Folder2=Modules

[Override]
!SourceFolder=override_files
File0=texture1.tpc
File1=texture2.tpc

[StreamVoice\AVO\_HuttHap]
!SourceFolder=voice_files
File0=conv1.wav
File1=conv2.wav

[Modules]
!SourceFolder=modules
File0=custom.mod
```

### Example 3: Renaming Files During Installation

```ini
[InstallList]
Folder0=Override

[Override]
File0=renamed_texture.tpc
File1=renamed_item.uti

[renamed_texture.tpc]
!SourceFile=original_texture.tpc
!SaveAs=final_texture_name.tpc

[renamed_item.uti]
!SourceFile=source_item.uti
!Filename=custom_item_name.uti
```

### Example 4: Installing to Archives

```ini
[InstallList]
Folder0=Modules\901myn.mod
Folder1=Modules\custom.rim

[Modules\901myn.mod]
File0=new_creature.utc
File1=new_dialog.dlg
Replace0=existing_item.uti
!OverrideType=warn

[Modules\custom.rim]
File0=custom_2da.2da
!ReplaceFile=1
```

### Example 5: Complex Example with All Features

```ini
[InstallList]
!DefaultDestination=Override
Folder0=Override
Folder1=Modules
Folder2=Modules\901myn.mod
Folder3=StreamVoice\AVO\_HuttHap

[Override]
!SourceFolder=textures
File0=texture1.tpc
File1=texture2.tpc
Replace0=existing_texture.tpc

[texture1.tpc]
!SourceFile=original_name.tpc
!SaveAs=final_texture.tpc
!Destination=textures
!OverrideType=rename

[Modules]
!SourceFolder=modules
Replace0=modified_module.mod

[Modules\901myn.mod]
File0=new_resource.uti
File1=new_texture.tpc
Replace0=modified_resource.utc
!SourceFolder=archive_resources

[new_resource.uti]
!Filename=custom_name.uti
!ReplaceFile=1

[StreamVoice\AVO\_HuttHap]
!SourceFolder=voice
File0=line1.wav
File1=line2.wav
```

## Special Cases and Edge Cases

### Empty InstallList

An empty `[InstallList]` section is valid and will be skipped:

```ini
[InstallList]
```

No files will be installed, and a note will be logged: `[InstallList] section missing from ini.` (if the section doesn't exist) or no error if the section exists but is empty.

### Missing Folder Sections

If a folder key in `[InstallList]` references a section that doesn't exist, a `KeyError` is raised:

```ini
[InstallList]
Folder0=NonExistentFolder
; Error: Section [NonExistentFolder] not found
```

### Missing Source Files

If a source file specified in a File#/Replace# entry doesn't exist in tslpatchdata (or the specified `!SourceFolder`), an error is logged:

```
Could not locate resource to copy: 'missing_file.tpc'
```

The patcher will continue with the next file.

### Automatic Folder Creation

Folders are automatically created if they don't exist:

```ini
[InstallList]
Folder0=NewFolder\SubFolder\DeepFolder

[NewFolder\SubFolder\DeepFolder]
File0=file.tpc
```

All parent folders (`NewFolder`, `SubFolder`, `DeepFolder`) will be created automatically.

### Archive File Handling

- **Archive doesn't exist**: Error logged, patch skipped
- **Archive exists but is read-only**: Permission error logged, patch skipped
- **Archive exists, file already in archive**: See [File Replacement Behavior](#file-replacement-behavior)
- **Archive exists, file doesn't exist in archive**: File is added normally

### Case Sensitivity

- Folder and file keys are **case-insensitive**: `File0`, `file0`, `FILE0` all work
- `Replace#` prefix detection is **case-insensitive**: `Replace0`, `replace0`, `REPLACE0` all work
- File paths on Windows are case-insensitive, but PyKotor uses `CaseAwarePath` to preserve case when possible

### Path Separators

- TSLPatcher convention: Use backslashes (`\`) for Windows paths
- PyKotor/HoloPatcher: Normalizes both backslashes (`\`) and forward slashes (`/`)
- Archive paths: Use backslashes: `Modules\901myn.mod`

### nwscript.nss Automatic Installation

If the mod contains `nwscript.nss` in the tslpatchdata folder and there are scripts to compile (`[CompileList]`), HoloPatcher will automatically append an InstallFile entry to install `nwscript.nss` to the Override folder. This is required for some versions of nwnnsscomp.exe that expect nwscript.nss to be in Override rather than tslpatchdata.

This happens during the `_prepare_compilelist` phase before the main patch loop runs.

## Troubleshooting

### File Not Installing

**Problem:** File listed in InstallList but not being installed.

**Possible Causes:**
1. File already exists and `Replace#=` or `!ReplaceFile=1` not set
   - **Solution:** Check logs for "already exists... Skipping file" message
   - **Fix:** Use `Replace#=` or set `!ReplaceFile=1`

2. Source file doesn't exist in tslpatchdata
   - **Solution:** Check logs for "Could not locate resource" error
   - **Fix:** Ensure file exists in tslpatchdata (or specified `!SourceFolder`)

3. Archive doesn't exist
   - **Solution:** Check logs for "capsule did not exist" error
   - **Fix:** Create the archive first or ensure the path is correct

4. Permission errors
   - **Solution:** Check logs for permission/access denied errors
   - **Fix:** Run with appropriate permissions, check file/folder permissions

### Wrong Destination

**Problem:** File installing to wrong location.

**Possible Causes:**
1. `!Destination` override in file section
2. `!DefaultDestination` set incorrectly
3. Folder section name typo

**Solution:** Check file section for `!Destination`, verify folder section names match destination paths.

### Archive Not Updating

**Problem:** File not appearing in archive after installation.

**Possible Causes:**
1. Archive doesn't exist (error logged)
2. File already exists and replacement not enabled
3. Archive is read-only or locked

**Solution:** Check logs for errors, ensure `Replace#=` or `!ReplaceFile=1` is set, verify archive permissions.

### Files Being Skipped Unexpectedly

**Problem:** Files that should install are being skipped.

**Possible Causes:**
1. `File#=` syntax used with existing files (expected behavior - use `Replace#=`)
2. `!ReplaceFile=0` explicitly set
3. File already exists in archive without replacement enabled

**Solution:** Review [File Replacement Behavior](#file-replacement-behavior) section, use `Replace#=` or `!ReplaceFile=1` to enable replacement.

## Reference: Complete Syntax Summary

### Top-Level [InstallList] Section

```ini
[InstallList]
!DefaultDestination=<folder_path>  ; Optional: default destination for all files
Folder#=<destination_path>          ; Required: map to folder section
```

### Folder Section (e.g., [Override])

```ini
[<destination_path>]
!SourceFolder=<relative_path>        ; Optional: source folder within tslpatchdata
File#=<filename.ext>                ; Install file (skip if exists)
Replace#=<filename.ext>             ; Install file (replace if exists)
```

### File Section (e.g., [filename.ext])

```ini
[<filename.ext>]
!SourceFile=<source_filename.ext>  ; Optional: alternative source file
!SaveAs=<final_filename.ext>       ; Optional: rename during installation
!Filename=<final_filename.ext>      ; Optional: alias for !SaveAs
!Destination=<destination_path>     ; Optional: override folder destination
!ReplaceFile=<0|1>                  ; Optional: override replacement behavior
!SourceFolder=<relative_path>      ; Optional: override source folder
!OverrideType=<ignore|warn|rename> ; Optional: conflict resolution mode
```

## Additional Notes

- All paths in TSLPatcher use backslashes (`\`) by convention, but HoloPatcher/PyKotor normalizes both slashes
- Folder paths are created automatically if they don't exist
- Archive paths must exist before files can be installed to them
- InstallList runs before other patch lists in HoloPatcher (but after TLKList in original TSLPatcher)
- Files are backed up before installation (if they exist)
- Uninstall scripts are generated automatically in the backup folder

## See Also

- [TSLPatcher's Official Readme](TSLPatcher's-Official-Readme.md) - Original TSLPatcher documentation
- [Explanations on HoloPatcher Internal Logic](Explanations-on-HoloPatcher-Internal-Logic.md) - Internal implementation details
- [TSLPatcher GFFList Syntax](TSLPatcher-GFFList-Syntax.md) - Documentation for GFF modifications
- [Mod Creation Best Practices](Mod-Creation-Best-Practices.md) - Best practices for mod development

