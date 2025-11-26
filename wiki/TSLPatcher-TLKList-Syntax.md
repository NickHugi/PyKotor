# TSLPatcher TLKList Syntax Documentation

This guide explains how to modify TLK files using TSLPatcher syntax. For the complete TLK file format specification, see [TLK File Format](TLK-File-Format). For general TSLPatcher information, see [TSLPatcher's Official Readme](TSLPatcher's-Official-Readme). For HoloPatcher-specific information, see [HoloPatcher README for Mod Developers](HoloPatcher-README-for-mod-developers.).

## Overview

The `[TLKList]` section in TSLPatcher's changes.ini file enables you to modify TLK (Talk Table) files used throughout KotOR. TLK files store all in-game text strings and their associated voiceover sound references. The most important TLK file is `dialog.tlk`, which contains all dialog, item descriptions, conversations, and other text displayed in the game.

TSLPatcher was designed by Stoffe with an **append-only philosophy** for TLK modifications. This design maximizes mod compatibility by non-destructively adding new entries to the end of `dialog.tlk`, allowing multiple mods to safely coexist without conflicts.

## Benefits of TLK Modification

TSLPatcher's TLK modification system provides several key advantages:

- **Avoid distributing large files**: The `dialog.tlk` file is approximately 10 MB. Instead of distributing the entire modified file, TSLPatcher allows you to add only your new entries, significantly reducing mod file size.

- **Memory system integration**: TSLPatcher keeps StrRefs of newly added entries in memory, allowing you to insert those StrRefs into 2DA and GFF files as needed. For example, if you add the name of a new force power to `dialog.tlk`, TSLPatcher can memorize the StrRef the name string ended up as, and insert that value into the "name" column in `spells.2da`.

- **Cross-section token usage**: StrRef tokens created in `[TLKList]` can be used throughout other sections:
  - In `[2DAList]` to assign stringrefs to 2DA cells
  - In `[GFFList]` to assign stringrefs to GFF fields (including ExoLocString fields)
  - In `[CompileList]` scripts where `#StrRef#` tokens are replaced during compilation
  - In `[SSFList]` to assign stringrefs to soundset entries

## Glossary

- **TLK (Talk Table)**: Binary file format storing text strings and voiceover references. The primary file is `dialog.tlk`.

- **StringRef (StrRef)**: Short for "String Reference", this is a numeric identifier/index for an entry in a TLK file. StringRefs start at 0 and increment sequentially. Example: StringRef 12345 refers to the 12346th entry in a TLK file. The StrRef is the identifier number that the game engine uses to retrieve text strings from `dialog.tlk`.

- **Key**: The left side of the `=` symbol in an INI entry (e.g., `StrRef0`, `AppendFile0`)

- **Value**: The right side of the `=` symbol in an INI entry. In `[TLKList]`, values specify the index into TLK source files to read from.

- **Token**: A placeholder like `StrRef0` or `StrRef1` that gets replaced with an actual StringRef during patching.

- **Append**: Non-destructive operation that adds new entries to the end of `dialog.tlk`. This is TSLPatcher's primary and recommended method.

- **Replace**: Destructive operation that overwrites existing entries in `dialog.tlk`. **Should ONLY be used for fixing grammar, spelling, or typographical errors in existing game content.** See [Replace Functionality Warning](#replace-functionality-warning) for details.

- **append.tlk**: Default source file containing new strings to append. Created using TalkEd.exe (see [Creating TLK Files](#creating-tlk-files)). Located in `tslpatchdata` folder.

- **appendf.tlk**: Feminine/non-English localized version of `append.tlk`. Used exclusively for KotOR1 Polish localization. Must have exactly the same number of entries as `append.tlk`. See [Localized Versions](#localized-versions) for details.

- **dialog.tlk**: The game's main TLK file containing all in-game text (typically ~10 MB). Modified files are written to the game's root directory (not override folder). TSLPatcher allows you to add new entries without distributing the entire large file.

## Table of Contents

- [Glossary](#glossary)
- [Benefits of TLK Modification](#benefits-of-tlk-modification)
- [Replace Functionality Warning](#replace-functionality-warning)
- [Creating TLK Files](#creating-tlk-files)
- [Basic Structure](#basic-structure)
- [Configuration Keys](#configuration-keys)
- [Entry Syntax](#entry-syntax)
  - [How Token Creation Works](#how-token-creation-works)
  - [StrRef Entries](#strref-entries)
  - [AppendFile Syntax](#appendfile-syntax)
- [Localized Versions](#localized-versions)
- [Memory System](#memory-system)
- [Processing Order](#processing-order)
- [File Structure](#file-structure)
- [Complete Examples](#complete-examples)
- [Common Use Cases](#common-use-cases)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)
- [Reference](#reference)

## Replace Functionality Warning

⚠️ **CRITICAL: Replace functionality should ONLY be used for fixing grammar, spelling, or typographical errors in existing game content.**

TSLPatcher was designed by Stoffe to be **append-only** for TLK modifications. The original TSLPatcher exclusively appended new entries to the end of `dialog.tlk` and never replaced existing entries. This design was intentional to maximize mod compatibility:

### Why Replace Should Be Avoided for New Content

- **Breaks mod compatibility**: If two mods replace the same stringref, they conflict irreconcilably
- **Destroys vanilla content**: Replaces original game text permanently, making it impossible to restore
- **Prevents mod stacking**: Can't safely use multiple mods that replace different entries simultaneously
- **Defeats TSLPatcher's design**: The tool was specifically designed for non-destructive appending to avoid conflicts

### Why Append Works Better

- **Non-destructive**: Appending preserves all existing game text, preventing conflicts between mods
- **Dynamic indexing**: Uses tokens (`StrRef#`) to handle variable stringref assignments without hard-coding indices
- **Mod stacking**: Multiple mods can safely add entries without interfering with each other
- **Compatibility**: Avoids the need to distribute full `dialog.tlk` files (10+ MB), reducing mod size

### Acceptable Uses of Replace

- ✅ Fixing typos in base game text (e.g., "teh" → "the")
- ✅ Correcting grammar mistakes in vanilla content
- ✅ Fixing broken or corrupted entries
- ✅ Community patch projects (like K1CP) that systematically fix errors

### When NOT to Use Replace

- ❌ Adding new content (use AppendFile or StrRef syntax instead)
- ❌ Modifying existing text for flavor/preference
- ❌ Any scenario where append would work

**For all new content, always use the append-based syntaxes described in [Entry Syntax](#entry-syntax).**

## Creating TLK Files

To use custom dialog.tlk entries in your mod, you must create source TLK files containing your new strings:

### Using TalkEd.exe

1. **Create a new TLK file**: Use TalkEd.exe (a TLK editor tool) to create a new TLK file
2. **Add your entries**: Add all your new text strings and voiceover sound references to this file
3. **Save as append.tlk**: Name the file exactly `append.tlk` (case-sensitive)
4. **Place in tslpatchdata**: Save `append.tlk` in the `tslpatchdata` folder

### Localized Versions (KotOR1 Polish only)

If you are using a non-English version of KotOR1 that has a `dialogf.tlk` file (Polish localization), you must also:

1. **Create appendf.tlk**: Create a new file with the feminine form of your strings
2. **Name it appendf.tlk**: Must be named exactly `appendf.tlk` (case-sensitive)
3. **Match entry count**: **`appendf.tlk` must have exactly the same number of entries as `append.tlk`**
4. **Matching indices**: Each index in `appendf.tlk` should correspond to the same index in `append.tlk`
5. **Handle missing forms**: If a string has no specific feminine form, put the same text in both files

**Important**: The entry count must match exactly. If `append.tlk` has 100 entries, `appendf.tlk` must also have exactly 100 entries, even if some are identical between the two files.

### Using ChangeEdit (Optional)

The ChangeEdit application provides a user-friendly GUI interface for configuring TLK entries without manually editing the INI file:

1. **Open append.tlk**: In ChangeEdit, navigate to the "TLK Entries" section in the tree view
2. **Load file**: Press the "Open append.tlk file..." button on top of the right list
3. **View entries**: This lists all your custom text entries in the list to the right
4. **Select entries**: Select an entry you wish TSLPatcher to add to `dialog.tlk`
5. **Add to list**: Press the left arrow icon (←) to add the entry to the list on the left
6. **Token creation**: Take note of the value in the left column, which should look like `StrRef0` for the first entry, with an incrementing number (`StrRef1`, `StrRef2`, etc.) for each subsequent entry
7. **Use tokens**: This token (e.g., `StrRef0`) is what you'll use in the 2DA and GFF sections to assign the resulting StrRef value to a 2DA cell or GFF field

**Manual Editing**: While ChangeEdit provides a GUI interface, you can also edit the `changes.ini` file directly with any text editor (Notepad, VS Code, etc.). The INI format is plain text and human-readable.

**Important**: When using ChangeEdit, always verify the generated INI entries match your expectations, especially for token names and entry indices.

## Basic Structure

```ini
[TLKList]
!DefaultDestination=.
!DefaultSourceFolder=.
!SourceFile=append.tlk
!SourceFileF=appendf.tlk

; Append new entries
StrRef0=0
StrRef1=1

; Append from custom file (Useful if you have a LOT of TLK entries and want to organize within multiple TLK files)
AppendFile0=custom_entries.tlk

[custom_entries.tlk]
0=10
1=11
```

**Key Points:**

- All examples use **append** operations - the recommended approach
- Values specify which StrRef indices to read from source files

## Configuration Keys

### `!DefaultDestination`

- **Type**: String (path)
- **Default**: `.` (kotor game installation path root)
- **Description**: Default destination folder for TLK files when not overridden
- **Example**: `!DefaultDestination=override`

### `!DefaultSourceFolder`

- **Type**: String (path)
- **Default**: `.` (tslpatchdata folder)
- **Description**: Default folder to search for TLK source files (e.g., `append.tlk`). This is a relative path from `mod_path`, which is typically the `tslpatchdata` folder (the parent directory of the `changes.ini` file). The default value `.` refers to the `tslpatchdata` folder itself.
- **Path Resolution**: Files are resolved as `mod_path / !DefaultSourceFolder / filename`. When `mod_path = "C:/Mod/tslpatchdata"`:
  - `!DefaultSourceFolder=.` resolves to e.g. `"C:/Mod/tslpatchdata"`
  - `!DefaultSourceFolder=tlk_files` resolves to e.g. `"C:/Mod/tslpatchdata/tlk_files"`
- **Example**: `!DefaultSourceFolder=.` (default, refers to tslpatchdata folder)

### `!SourceFile`

- **Type**: String (filename)
- **Default**: `append.tlk`
- **Description**: Name of the TLK file to use when appending entries via StrRef syntax
- **Example**: `!SourceFile=my_strings.tlk`

### `!SourceFileF`

- **Type**: String (filename)
- **Default**: `appendf.tlk`
- **Description**: Name of the TLK file to use for feminine/non-English localized versions (exclusively KotOR1 Polish)
- **Version Added**: 1.2.8b6
- **Note**: Must have exactly the same number of entries as `!SourceFile`. Each index in `appendf.tlk` maps directly to the same index in `append.tlk`. If a string has no specific feminine form, put the same text in both files.
- **Example**: `!SourceFileF=my_strings_f.tlk`

### Unsupported Keys

The following keys are **NOT** supported in `[TLKList]`:

- `!ReplaceFile` - Not applicable to TLK files
- `!OverrideType` - Not applicable to TLK files

## Entry Syntax

The `[TLKList]` section supports two primary entry syntax patterns, both using **append** operations:

1. **StrRef Entries** - Append from the default source file (`append.tlk`)
2. **AppendFile Syntax** - Append from custom TLK files with flexible mappings

### How Token Creation Works

**Important**: Tokens are created from the **value** (the number on the right side of `=`). For `StrRef<number>=<number>` entries, the number in the key and value must match, and this matching number determines the token name.

- `StrRef0=0` creates token `StrRef0` (reads index 0 from `append.tlk`)
- `StrRef5=5` creates token `StrRef5` (reads index 5 from `append.tlk`)
- For AppendFile subsections, `10=10` creates token `StrRef10` (reads index 10 from the source TLK)

The token name `StrRef<number>` is created from the matching number, and this token stores the new stringref that gets appended to `dialog.tlk` for use in other sections.

### StrRef Entries

**Purpose**: Append new entries to `dialog.tlk` from the default source file (`append.tlk`)

**Syntax**:

```ini
StrRef<number>=<number>
```

**Parameters**:

- `<number>` - The index into `append.tlk` (or `!SourceFile`) to read from. This number must match in both the key and value.

**Behavior**:

- Appends a new entry to the end of `dialog.tlk` (non-destructive)
- Reads text and sound from `append.tlk` at the specified index
- The new entry receives the next available stringref automatically
- Creates token `StrRef<number>` from the matching number (see [How Token Creation Works](#how-token-creation-works))
- Stores that new stringref in memory for use in other sections via the token

**Examples**:

```ini
[TLKList]
StrRef0=0  ; Reads index 0 from append.tlk, creates token StrRef0
StrRef1=1  ; Reads index 1 from append.tlk, creates token StrRef1
StrRef2=2  ; Reads index 2 from append.tlk, creates token StrRef2
```

### AppendFile Syntax

**Purpose**: Add entries from a custom TLK file using index mappings

**Syntax**:

```ini
AppendFile<anything>=<tlk_filename>
```

**Parameters**:

- `<tlk_filename>` - Name of a TLK file in the source folder OR name of a subsection in the INI

**Behavior**:

- Creates a **new section** `[<tlk_filename>]` if the file doesn't exist in source
- Maps entries from the source TLK to `dialog.tlk` using the subsection mappings
- All entries are **added** (not replaced) to `dialog.tlk`
- For AppendFile, entries are appended and tokens are created from the mapping values

**Subsection Syntax**:

```ini
[<tlk_filename>]
<token_identifier>=<source_index>
StrRef<token_identifier>=StrRef<source_index>  ; Alternative explicit syntax
```

**Subsection Parameters**:

- `<source_index>` - The index into the source TLK file to read from. Token `StrRef{source_index}` is created from this value. The number in the key should match the number in the value for clarity.

**Examples**:

```ini
[TLKList]
AppendFile0=planets.tlk  ; Creates subsection [planets.tlk] for mappings

[planets.tlk]
10=10  ; Reads index 10, creates token StrRef10
11=11  ; Reads index 11, creates token StrRef11
12=12  ; Reads index 12, creates token StrRef12 (alternative: StrRef12=StrRef12)
```

**Important Notes**:

- The `<anything>` in `AppendFile<anything>` is arbitrary and ignored
- The subsection `[planets.tlk]` can define mappings using numeric indices or `StrRef` syntax

## Localized Versions

### KotOR1 Polish Localization

KotOR1 Polish edition uses both `dialog.tlk` and `dialogf.tlk` files. If your mod supports this localization:

1. **Create both files**: Create `append.tlk` (masculine/standard) and `appendf.tlk` (feminine/localized)
2. **Match entry counts**: Both files must have exactly the same number of entries
3. **Map indices**: Entry at index 0 in `append.tlk` corresponds to index 0 in `appendf.tlk`
4. **Handle duplicates**: If a string doesn't have a feminine form, use the same text in both files

### Configuration

```ini
[TLKList]
!SourceFile=append.tlk
!SourceFileF=appendf.tlk
StrRef0=0
StrRef1=1
```

When TSLPatcher processes entries, it automatically uses `appendf.tlk` when the target game has `dialogf.tlk` present.

### Non-English Localization Notes

- **KotOR2**: Does not use `dialogf.tlk` - only `dialog.tlk` is used
- **Other Languages**: Currently only KotOR1 Polish uses the dual-TLK system
- **Entry Matching**: The strict requirement for matching entry counts ensures proper localization mapping

## Memory System

When TLK entries are **added** via append operations, TSLPatcher stores them in memory for use in other patch sections.

### Memory Storage

```python
# After append operation (StrRef or AppendFile)
memory.memory_str[token_identifier] = new_stringref
```

**Behavior**:

- For **append** operations: Stores the new stringref that was added, mapped to the token identifier (see [How Token Creation Works](#how-token-creation-works))
- For **replace** operations: Memory is not typically stored (no need since stringref is static)

### Token Creation from Values

Tokens are created from the matching number in both the key and value. See [How Token Creation Works](#how-token-creation-works) for details. After processing, tokens are available for use in other sections like `[2DAList]`, `[GFFList]`, and `[CompileList]`.

### Using TLK Memory in Other Sections

**In 2DA files**:

```ini
[TLKList]
StrRef0=0  ; Creates token StrRef0

[2DAList]
Table0=spells.2da

[spells.2da]
AddRow0=new_spell
2DAMEMORY0=StrRef0  ; Store stringref in 2DA memory for cross-file use

[new_spell]
name=StrRef0  ; Token gets replaced with actual stringref
```

**In GFF files**:

```ini
[TLKList]
StrRef0=0  ; Creates token StrRef0

[GFFList]
File0=item.uti

[item.uti]
LocalizedName=StrRef0  ; Token gets replaced with actual stringref
```

**In NSS Scripts (CompileList)**:

```nss
// Script compilation will replace #StrRef# tokens
void main() {
    // #StrRef0# token gets replaced with actual stringref during compilation
    SendMessageToPC(GetFirstPC(), #StrRef0#);
}
```

## Processing Order

### TSLPatcher Execution Order

In **TSLPatcher v1.2.8 and later**, the TLKList section is processed **first** in the patching pipeline (before InstallList):

```text
TSLPatcher Execution Order (v1.2.8+):
1. [TLKList]         - Add TLK entries (append operations)
2. [InstallList]     - Copy files to installation
3. [2DAList]         - Add/Modify 2DA entries
4. [GFFList]         - Add/Modify GFF entries
5. [CompileList]     - Compile NSS scripts (replaces #StrRef# tokens)
6. [SSFList]         - Modify soundset files
```

**Note**: In TSLPatcher v1.2.8b0 (2006-08-06), the processing order was changed so that TLK Appending happens before Install List. According to the official change log, this allows ERF/MOD/RIM files to be placed in their proper locations before GFF and script compilation sections run, so modified files can be saved into those archive files.

**Older TSLPatcher versions** (before 1.2.8) processed InstallList before TLKList.

### HoloPatcher Execution Order

**HoloPatcher** (a modern Python drop-in replacement for TSLPatcher) uses a **different execution order**:

```text
HoloPatcher Execution Order:
1. [InstallList]     - Copy files to installation
2. [TLKList]         - Add TLK entries (append operations) ← HERE
3. [2DAList]         - Add/Modify 2DA entries
4. [GFFList]         - Add/Modify GFF entries
5. [CompileList]     - Compile NSS scripts (replaces #StrRef# tokens)
6. [HACKList]        - Patch NCS files
7. [SSFList]         - Modify soundset files
```

**Important Compatibility Note**: This is a **backwards-compatible discrepancy** between TSLPatcher and HoloPatcher. HoloPatcher processes InstallList before TLKList to allow users to install a base `dialog.tlk` file (or other files) via InstallList, which can then be modified by TLK appending operations. This order provides greater flexibility for mod workflows.

### Analysis: Order Comparison

**TSLPatcher's reasoning** (TLKList → InstallList):

- Allows ERF/MOD/RIM files to be placed before GFF/Compile sections that save into them

**HoloPatcher's reasoning** (InstallList → TLKList):

- ✅ **More flexible**: Users can install a custom base `dialog.tlk` file via InstallList, then TLK appending modifies it
- ✅ **Better for testing**: Allows installing known-good TLK files before appending new entries
- ✅ **Preserves dependencies**: TLK entries are still processed before 2DA/GFF/Compile/SSF sections that reference them
- ✅ **More intuitive**: File installation happens first, then modifications are applied

**Critical Timing** (applies to both TSLPatcher and HoloPatcher):

- TLK entries are added to the destination target `dialog.tlk` **before** 2DA and GFF modifications
- This ensures stringrefs/tlk entries are available when referenced by other sections
- Script compilation happens **after** TLK processing, so `#StrRef#` tokens can be resolved
- Tokens are substituted in 2DA, GFF, and script files after TLK entries have been appended

## File Structure

### TLK File Format

A TLK file is a binary format containing:

- **Header**: File type (`TLK`), version (`V3.0`), language ID, string count, entries offset
- **Entry Headers**: Flags, sound ResRef (16 bytes), volume/pitch variance (unused), text offset, text length, sound length (unused)
- **Text Data**: Actual string content stored at the specified offsets

**TLK Entry Structure**:

```python
class TLKEntry:
    text: str              # The display text (UTF-8 or cp1252 encoding)
    voiceover: ResRef      # Sound file ResRef (max 16 characters)
    sound_length: float    # Unused by KotOR (present in format but ignored)
```

**String Length Limitations**:

- **TSLPatcher v1.2.8b6 and later**: Can handle TLK entries with strings of **any size** (no practical limit)
- **Earlier versions**: Had a bug that prevented proper handling of strings longer than 4096 characters
- If you encounter issues with long strings, ensure you're using TSLPatcher v1.2.8b6 or later. HoloPatcher does **NOT** have this bug.

### KotOR TLK Files

**Standard Files**:

- `dialog.tlk` - Main English dialog (always present in game directory)

**Localized Versions** (exclusively KotOR1 Polish):

- `dialogf.tlk` - Feminine/non-English localized version
- Must match the number of entries in `dialog.tlk` exactly

**Entry Indices**:

- StringRefs start at 0 and increment sequentially
- Valid entries: 0 to (total_entries - 1)
- Reference entries as integers throughout the game and mod files

## Complete Examples

### Example 1: Simple Append with StrRef

Add new string entries from `append.tlk` to `dialog.tlk`:

```ini
[TLKList]
StrRef0=0
StrRef1=1
StrRef2=2
```

**Files**: `tslpatchdata/append.tlk` contains entries 0, 1, 2 with your custom text

**Result**: Each entry from `append.tlk` is appended to `dialog.tlk` and assigned the next available stringref (e.g., 123456, 123457, 123458). These new stringrefs are stored in memory as tokens `StrRef0`, `StrRef1`, `StrRef2` for use in other sections.

### Example 2: Append with Custom File

Add entries from a custom TLK file using index mappings:

```ini
[TLKList]
AppendFile0=planets.tlk

[planets.tlk]
0=10   ; Reads index 10, creates token StrRef10
1=11   ; Reads index 11, creates token StrRef11
2=12   ; Reads index 12, creates token StrRef12
```

**Files**: `tslpatchdata/planets.tlk` contains entries at indices 10, 11, 12, etc.

**Result**: Each entry from `planets.tlk` is appended to `dialog.tlk` and tokens `StrRef10`, `StrRef11`, `StrRef12` are created (from the values, not the keys).

### Example 3: Combined Append Operations

Use multiple append methods together:

```ini
[TLKList]
!SourceFile=append.tlk
StrRef0=0
StrRef1=1
AppendFile0=items.tlk

[items.tlk]
0=100   ; Creates token StrRef100
1=101   ; Creates token StrRef101
```

**Files**: `tslpatchdata/append.tlk` (entries 0, 1), `tslpatchdata/items.tlk` (entries 100, 101)

**Processing Order**: Entries are processed sequentially, creating tokens `StrRef0`, `StrRef1`, `StrRef100`, `StrRef101`.

### Example 4: Localized Version (Polish KotOR1)

Support for feminine/localized versions:

```ini
[TLKList]
!SourceFile=append.tlk
!SourceFileF=appendf.tlk
StrRef0=0
StrRef1=1
StrRef2=2
```

**Files**:

- `append.tlk` (masculine/English) - Contains 3 entries (indices 0, 1, 2)
- `appendf.tlk` (feminine/Polish) - Must have exactly 3 entries (indices 0, 1, 2)

**Requirements**:

- Both files must have **exactly the same number of entries**
- Entry at index 0 in `append.tlk` maps to index 0 in `appendf.tlk`
- If a string has no feminine form, use the same text in both files
- TSLPatcher automatically uses `appendf.tlk` when the target game has `dialogf.tlk` present

## Common Use Cases

### Adding New Dialog for NPCs

**Scenario**: Add custom lines for a new NPC

**Solution**:

```ini
[TLKList]
StrRef0=0  ; Greeting line
StrRef1=1  ; Quest offer
StrRef2=2  ; Refusal response

[GFFList]
File0=my_npc.dlg

[my_npc.dlg]
; Reference tokens StrRef0, StrRef1, StrRef2 in dialog entries
```

### Adding Item Descriptions

**Scenario**: Add descriptions for new items

**Solution**:

```ini
[TLKList]
AppendFile0=items.tlk

[items.tlk]
0=10  ; Item name → token StrRef10
1=11  ; Item description → token StrRef11
2=12  ; Another item name → token StrRef12
3=13  ; Another item description → token StrRef13

[GFFList]
File0=new_item.uti

[new_item.uti]
LocalizedName=StrRef10
DescIdentified=StrRef11
```

### Translating Mod Content

**Scenario**: Create English and non-English versions

**Solution**:

```ini
[TLKList]
!SourceFile=append_en.tlk
!SourceFileF=append_de.tlk
StrRef0=0
StrRef1=1
StrRef2=2
```

**Files**: Both `append_en.tlk` (English) and `append_de.tlk` (German) must match entry count exactly. TSLPatcher uses the appropriate file based on game localization.

## Troubleshooting

### Error: "Invalid syntax found in [TLKList]"

**Cause**: Unrecognized key format

**Solutions**:

- Check for typos in key names
- Ensure you're using one of the supported syntaxes: `StrRef<key>=<value>` or `AppendFile<key>=<value>`
- Verify the key matches the expected pattern

**Correct Syntaxes**:

```ini
; StrRef syntax: Key can be anything, value must be numeric
StrRef0=0
StrRef1=1

; AppendFile syntax: Key starts with "AppendFile", value is filename
AppendFile0=file.tlk
AppendFile1=another.tlk
```

### Error: "Could not parse 'key=value' in [TLKList]"

**Cause**: Invalid numeric values or malformed entries

**Solutions**:

- Ensure values are valid integers for StrRef/AppendFile mappings
- Check that numeric keys can be parsed as integers if using numeric format
- Verify no extra spaces or invalid characters

**Correct**:

```ini
StrRef0=0
StrRef123=123
```

**Incorrect**:

```ini
StrRef0=abc  ; Value must be numeric
StrRef=0  ; Missing numeric part in key
```

### Error: "Section [filename] not found"

**Cause**: Referenced TLK file or subsection doesn't exist

**Solutions**:

- Create the subsection in the INI if using internal mappings:

  ```ini
  AppendFile0=myfile.tlk
  [myfile.tlk]  ; Must create this subsection
  0=1
  ```

- Or ensure the file exists in the source folder if using external TLK files
- Check `!DefaultSourceFolder` path is correct

### Error: "Cannot replace nonexistent stringref in dialog.tlk"

**Cause**: Trying to replace an entry that doesn't exist (if using replace functionality)

**Solutions**:

- For new content, use append syntax (`StrRef` or `AppendFile`) instead of replace
- Verify the stringref number is correct if you must use replace for error fixing
- Remember: **Always use append for new content** - see [Replace Functionality Warning](#replace-functionality-warning)

**Adding New** (use this):

```ini
StrRef0=0  ; Appends new entry, creates token StrRef0
```

### Issue: Entries Not Appearing

**Cause**: Multiple possible issues

**Solutions**:

- Check file paths: `!DefaultSourceFolder` and file locations
- Verify TLK file format: must be valid binary TLK
- Check file encoding: should be UTF-8 or cp1252
- Ensure the file is in the tslpatchdata folder (or specified source folder)
- Review the log for processing errors
- Verify keys and values are correctly formatted

### Issue: Wrong Token Created

**Cause**: Confusion about token creation from keys vs values

**Solutions**:

- See [How Token Creation Works](#how-token-creation-works) - tokens are created from the **value** (matching number)
- `StrRef0=0` creates token `StrRef0`
- `StrRef5=5` creates token `StrRef5`

### Issue: Memory Tokens Not Working

**Cause**: Token not created or not accessible in other sections

**Solutions**:

- Verify the stringref was actually added (check logs)
- Ensure you're using the correct token name (created from matching number)
- Check memory is being used in the correct execution order
- Tokens are only created for **append** operations, not replace operations

**Example**:

```ini
[TLKList]
StrRef0=0  ; Creates token StrRef0

[2DAList]
Table0=spells.2da

[spells.2da]
name=StrRef0  ; Use the token
```

### Issue: Files with Many Entries

**Best Practice**: Use AppendFile with subsections for clarity and organization

**Good** (Organized by content type):

```ini
[TLKList]
AppendFile0=items.tlk
AppendFile1=npcs.tlk

[items.tlk]
0=100   ; Token: StrRef100 - Item name
1=101   ; Token: StrRef101 - Item description
; ... many more entries

[npcs.tlk]
0=200   ; Token: StrRef200 - NPC greeting
1=201   ; Token: StrRef201 - NPC dialogue
; ... many more entries
```

**Less Ideal** (but still works for small mods):

```ini
[TLKList]
StrRef0=0
StrRef1=1
StrRef2=2
; ... 200 more lines becomes hard to manage
```

### Issue: Write-Protected dialog.tlk

**Cause**: Some systems have `dialog.tlk` set to read-only or write-protected

**Solutions**:

- Check file permissions on `dialog.tlk` in the game directory
- Run TSLPatcher with administrator privileges if needed
- Ensure the game is not running when installing mods
- Check if antivirus software is blocking file modification

**Note**: TSLPatcher v1.2.8b8 fixed a bug where installation would stop when `dialog.tlk` was write-protected. If using an older version, ensure the file is writable.

## Best Practices

### 1. Organization

- Group related entries in separate TLK files
- Use descriptive file names: `npcs.tlk`, `items.tlk`, `planets.tlk`
- Keep the main INI clean with AppendFile/StrRef references
- Document which tokens correspond to which content

### 2. Token Management

- See [How Token Creation Works](#how-token-creation-works) for token creation details
- Use consistent numbering to create predictable token names
- Document token usage in comments when helpful:

  ```ini
  StrRef0=0  ; NPC greeting
  ```

### 3. Compatibility

- **Always use append for new content** - this is TSLPatcher's design
- Never use replace functionality except for fixing existing errors (see [Replace Functionality Warning](#replace-functionality-warning))
- Document which stringrefs are custom vs modified
- Use descriptive token names by choosing appropriate numbers

### 4. Testing

- Verify all TLK files are valid before packaging
- Check stringref assignments in logs
- Test with multiple mods installed to check compatibility
- Use `KotorDiff` to compare before/after `dialog.tlk`
- Verify tokens are correctly created and accessible

### 5. File Management

- **Create with TalkEd.exe**: Use TalkEd.exe to create and edit your source TLK files (see [Creating TLK Files](#creating-tlk-files))
- **Keep source TLK files readable**: Use JSON export for debugging if your TLK editor supports it
- **Maintain consistent naming**: Always use `append.tlk` and `appendf.tlk` (or set `!SourceFile`/`!SourceFileF` if using custom names)
- **Version control**: Keep TLK files separately from other mod files for easier management
- **Match entry counts**: If using localized versions, ensure `append.tlk` and `appendf.tlk` have **exactly the same number of entries**
- **File size considerations**: The `dialog.tlk` file is ~10 MB, but you only need to distribute small `append.tlk` files with your mod

### 6. Localization

- **KotOR1 Polish only**: The dual-TLK system (`dialog.tlk` + `dialogf.tlk`) is exclusively for KotOR1 Polish localization
- **Maintain parallel files**: If supporting Polish, maintain both `append.tlk` and `appendf.tlk`
- **Exact entry matching**: Entry counts must match exactly between `append.tlk` and `appendf.tlk`
- **Map indices**: Each index must correspond between the two files (index 0 → index 0, index 1 → index 1, etc.)
- **Handle duplicates**: If a string has no feminine form, use the same text in both files
- **Use configuration keys**: Set `!SourceFileF` to specify the feminine version filename
- **Documentation**: Document language support in your mod's README
- **KotOR2/TSL**: Does not use `dialogf.tlk` - only create `append.tlk` for KotOR2 mods

### 7. Key/Value Clarity

- Keys appear on the left side of `=`, values on the right
- For `StrRef<number>=<number>`, numbers must match for proper token creation
- Use consistent numbering for readability

## Reference

### Supported Entry Patterns

| Pattern | Syntax | Purpose | Replacement |
|---------|--------|---------|-------------|
| StrRef | `StrRef<number>=<number>` | Append from default file | No |
| AppendFile | `AppendFile<anything>=<filename>` | Append from custom file | No |

### Memory System Reference

```python
# After StrRef append
# StrRef0=0 → Creates token StrRef0
# Memory: memory.memory_str[0] = new_stringref (from dialog.tlk append)

# After AppendFile append
# Subsection: 10=10 → Creates token StrRef10
# Memory: memory.memory_str[10] = new_stringref (from dialog.tlk append)
```

**Key Points**: See [How Token Creation Works](#how-token-creation-works) and [Memory System](#memory-system) for details. Tokens are available for use in `[2DAList]`, `[GFFList]`, and `[CompileList]` sections.

### Processing Flow

1. Parse [TLKList] section
2. Load source TLK files from `!SourceFile`/`!SourceFileF` e.g. `!SourceFile=append.tlk`
3. For each StrRef entry:
   - Parse: *Key* (ignored), *Value* (source index)
   - Load entry from source file at *Value* index
   - Append to dialog.tlk (gets new stringref)
   - Create token StrRef{value} from *Value* to store the new stringref
4. For each AppendFile entry:
   - Parse: Key (part after the word 'append' is ignored), *Value* (filename) e.g. `AppendFile0=some_append_contents.tlk`
   - Parse subsection [filename] mappings
   - For each mapping:
     - Parse: *Key* (ignored), *Value* (source index)
     - Load entry from referenced file at *Value* index
     - Append to dialog.tlk (gets new stringref)
     - Create token StrRef{value} from *Value* to store the new stringref
5. Tokens are now available for substitution in:
   - [2DAList] sections (2DAMEMORY#=StrRef#)
   - [GFFList] sections (FieldName=StrRef#)
   - [CompileList] scripts (#StrRef# tokens)

### Token Substitution Examples

**In 2DA files**: `name=StrRef0` (token gets replaced with actual stringref)

**In GFF files**: `LocalizedName=StrRef0` (token gets replaced with actual stringref)

**In NSS scripts**: `SendMessageToPC(GetFirstPC(), #StrRef0#);` (token gets replaced during compilation)

### Version History Notes

**TSLPatcher v1.2.8b6 (2006-10-03)**:

- Added optional `!SourceFile` and `!SourceFileF` keys to the `[TLKList]` section
- If present, these can be used to set an alternative name of the TLK file to use
- If left out, default values are `append.tlk` and `appendf.tlk` as before
- **Fixed bug**: Previously couldn't handle TLK entries with strings longer than 4096 characters - now supports strings of any size

**TSLPatcher v1.2.8b0 (2006-08-06)**:

- Changed processing order: TLK Appending now happens before Install List
- This allows ERF/MOD/RIM files to be placed before GFF and script compilation sections run

**TSLPatcher v1.2.8b8 (2006-12-02)**:

- Fixed bug that caused TSLPatcher to stop installation into games where the `dialog.tlk` file was write-protected

## Related Documentation

- [TSLPatcher's Official Readme](TSLPatcher's-Official-Readme.md) - General TSLPatcher information and ChangeEdit usage
- [TSLPatcher 2DAList Syntax](TSLPatcher-2DAList-Syntax.md) - How to modify 2DA files (can use StrRef tokens)
- [TSLPatcher GFFList Syntax](TSLPatcher-GFFList-Syntax.md) - How to modify GFF files (can use StrRef tokens)
- [TSLPatcher SSFList Syntax](TSLPatcher-SSFList-Syntax.md) - How to modify soundset files (can use StrRef tokens)
- [TSLPatcher CompileList Syntax](TSLPatcher-CompileList-Syntax.md) - How to compile scripts (can use #StrRef# tokens)
- [Mod Creation Best Practices](Mod-Creation-Best-Practices.md) - Best practices for modding
- [HoloPatcher Documentation](HoloPatcher.md) - PyKotor implementation details
