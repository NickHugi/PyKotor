# TSLPatcher SSFList Syntax Documentation

This guide explains how to modify SSF files using TSLPatcher syntax. For the complete SSF file format specification, see [SSF File Format](SSF-File-Format). For general TSLPatcher information, see [TSLPatcher's Official Readme](TSLPatcher's-Official-Readme). For HoloPatcher-specific information, see [HoloPatcher README for Mod Developers](HoloPatcher-README-for-mod-developers.).

## Overview

The `[SSFList]` section in TSLPatcher's changes.ini file enables you to modify SSF (Sound Set File) files that define sound string references for characters. SSF files contain 28 predefined sound slots that map to specific character audio cues such as battle cries, select sounds, attack grunts, pain reactions, and various action-based sound effects.

## Table of Contents

- [Basic Structure](#basic-structure)
- [File-Level Configuration](#file-level-configuration)
- [Sound Entry Modifiers](#sound-entry-modifiers)
- [Memory Token System](#memory-token-system)
- [Available Sound Entries](#available-sound-entries)
- [Examples](#examples)

## Basic Structure

```ini
[SSFList]
!DefaultDestination=Override
!DefaultSourceFolder=.  ; Note: `.` refers to the tslpatchdata folder (where changes.ini is located)
File0=example.ssf
Replace0=different_soundset.ssf

[example.ssf]
!Destination=Override
!SourceFolder=.
!SourceFile=source.ssf
!ReplaceFile=0

; Modify sound entries
Battlecry 1=12345
Battlecry 2=2DAMEMORY5
Attack 1=StrRef10
Death=100
```

The `[SSFList]` section declares SSF files to patch. Each entry references another section with the same name as the filename.

## File-Level Configuration

### Top-Level Keys in [SSFList]

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `!DefaultDestination` | string | `Override` | Default destination for all SSF files in this section |
| `!DefaultSourceFolder` | string | `.` | Default source folder for SSF files. This is a relative path from `mod_path`, which is typically the `tslpatchdata` folder (the parent directory of the `changes.ini` file). The default value `.` refers to the `tslpatchdata` folder itself. Path resolution: `mod_path / !DefaultSourceFolder / filename` |

### File Section Configuration

Each SSF file requires its own section (e.g., `[example.ssf]`).

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `!Destination` | string | Inherited from `!DefaultDestination` | Where to save the modified file (`Override` or `path\to\file.mod`) |
| `!SourceFolder` | string | Inherited from `!DefaultSourceFolder` | Source folder for the SSF file. Relative path from `mod_path` (typically the tslpatchdata folder). When `.`, refers to the tslpatchdata folder itself. |
| `!SourceFile` | string | Same as section name | Alternative source filename |
| `!ReplaceFile` | 0/1 | 0 | Overwrite existing file before modifications |

**Destination Values:**

- `Override` or empty: Save to the Override folder
- `Modules\module.mod`: Insert into an ERF/MOD/RIM archive
- Use backslashes for path separators

**Replace File Behavior:**

- If `FileN=filename.ssf` is used: The SSF file will be checked if it exists in the target destination. If it exists, it will be modified in place. If it doesn't exist, a copy from tslpatchdata will be made and modified.
- If `ReplaceN=filename.ssf` is used: The SSF file will be copied from tslpatchdata to the target destination (overwriting any existing file with the same name) and then modified.
- If `!ReplaceFile=1` is set in the file section: Same behavior as `ReplaceN`, taking priority over the `FileN` vs `ReplaceN` syntax.

## Sound Entry Modifiers

Each line in the SSF file section defines a sound entry to modify. The format is:

```ini
[SoundName]=Value
```

Where:

- `SoundName` is one of the 28 predefined sound entry names (see [Available Sound Entries](#available-sound-entries))
- `Value` can be:
  - A numeric stringref value
  - A `StrRef#` token referencing TLK memory
  - A `2DAMEMORY#` token referencing 2DA memory

### Value Syntax Examples

```ini
[example.ssf]
; Set sound to a constant stringref number
Battlecry 1=12345

; Set sound to a TLK memory token
Selected 1=StrRef5

; Set sound to a 2DA memory token
Attack 1=2DAMEMORY10

; Negative values are supported (represents "no sound")
Pain 1=-1
```

**Important Notes:**

- Sound entry names are **case-insensitive**
- Sound entry names must match exactly (including spaces) from the allowed list
- Negative values (including -1) are valid and typically represent "no sound" or unused sound slots
- Stringref values must be numeric strings

## Memory Token System

SSFList supports both TLK and 2DA memory tokens for dynamic stringref assignment.

### StrRef Tokens

`StrRef#` tokens reference TLK (Talk) memory tokens that have been set elsewhere in changes.ini (typically from TLKList entries). When the SSF file is patched, the stored StrRef value from memory will be used.

```ini
[example.ssf]
; Use StrRef5 from TLK memory
Battlecry 1=StrRef5

; Use StrRef12 from TLK memory
Attack 1=StrRef12
```

**Syntax:** `StrRef` followed immediately by a numeric token ID

**When to use:** When you want the sound entry to reference a dialog entry you've added to the game's TLK file.

### 2DAMEMORY Tokens

`2DAMEMORY#` tokens reference 2DA memory tokens that have been set elsewhere in changes.ini (typically from 2DAList entries). The stored value is converted to an integer stringref.

```ini
[example.ssf]
; Use 2DAMEMORY5 from 2DA memory
Selected 1=2DAMEMORY5

; Use 2DAMEMORY10 from 2DA memory
Pain 1=2DAMEMORY10
```

**Syntax:** `2DAMEMORY` followed immediately by a numeric token ID

**When to use:** When you want the sound entry to reference a value stored in 2DA memory (typically row indices or other numeric identifiers).

### Token Resolution

Both token types are resolved during patch application:

1. TLK Memory (`StrRef#`): Returns the stored integer stringref value
2. 2DA Memory (`2DAMEMORY#`): Returns the stored integer value (converted from string)
3. Constant values: Used directly as integer stringref values

If a token references an uninitialized memory slot, the behavior is undefined and may cause errors.

## Available Sound Entries

SSF files contain exactly 28 sound slots. The following table lists all available sound entry names:

| Sound Entry Name | ID | Enum Value | Description |
|------------------|----|----|-------------|
| `Battlecry 1` | 0 | BATTLE_CRY_1 | First battle cry sound |
| `Battlecry 2` | 1 | BATTLE_CRY_2 | Second battle cry sound |
| `Battlecry 3` | 2 | BATTLE_CRY_3 | Third battle cry sound |
| `Battlecry 4` | 3 | BATTLE_CRY_4 | Fourth battle cry sound |
| `Battlecry 5` | 4 | BATTLE_CRY_5 | Fifth battle cry sound |
| `Battlecry 6` | 5 | BATTLE_CRY_6 | Sixth battle cry sound |
| `Selected 1` | 6 | SELECT_1 | First selection sound |
| `Selected 2` | 7 | SELECT_2 | Second selection sound |
| `Selected 3` | 8 | SELECT_3 | Third selection sound |
| `Attack 1` | 9 | ATTACK_GRUNT_1 | First attack grunt sound |
| `Attack 2` | 10 | ATTACK_GRUNT_2 | Second attack grunt sound |
| `Attack 3` | 11 | ATTACK_GRUNT_3 | Third attack grunt sound |
| `Pain 1` | 12 | PAIN_GRUNT_1 | First pain grunt sound |
| `Pain 2` | 13 | PAIN_GRUNT_2 | Second pain grunt sound |
| `Low health` | 14 | LOW_HEALTH | Low health warning sound |
| `Death` | 15 | DEAD | Death sound effect |
| `Critical hit` | 16 | CRITICAL_HIT | Critical hit sound |
| `Target immune` | 17 | TARGET_IMMUNE | Target immune to attack sound |
| `Place mine` | 18 | LAY_MINE | Mine placement sound |
| `Disarm mine` | 19 | DISARM_MINE | Mine disarming sound |
| `Stealth on` | 20 | BEGIN_STEALTH | Stealth activation sound |
| `Search` | 21 | BEGIN_SEARCH | Search action sound |
| `Pick lock start` | 22 | BEGIN_UNLOCK | Lockpicking start sound |
| `Pick lock fail` | 23 | UNLOCK_FAILED | Lockpicking failure sound |
| `Pick lock done` | 24 | UNLOCK_SUCCESS | Lockpicking success sound |
| `Leave party` | 25 | SEPARATED_FROM_PARTY | Party separation sound |
| `Rejoin party` | 26 | REJOINED_PARTY | Party rejoin sound |
| `Poisoned` | 27 | POISONED | Poison effect sound |

**Note:** All sound entry names are case-insensitive when used in changes.ini. The spaces in entry names must match exactly (e.g., "Battlecry 1" not "Battlecry1").

## Examples

### Example 1: Basic Sound Set Modification

This example modifies an existing sound set by changing a few sound entries to constant values:

```ini
[SSFList]
File0=custom_voice.ssf

[custom_voice.ssf]
Battlecry 1=50001
Battlecry 2=50002
Selected 1=50003
Attack 1=50004
Death=50005
```

### Example 2: Using TLK Memory Tokens

This example uses StrRef tokens to dynamically reference dialog entries added to the TLK file:

```ini
[TLKList]
StrRef1000=Hello, warrior!
StrRef1001=For the Republic!
StrRef1002=AAAGH!

[SSFList]
File0=jedi_soundset.ssf

[jedi_soundset.ssf]
Selected 1=StrRef1000
Battlecry 1=StrRef1001
Pain 1=StrRef1002
```

### Example 3: Using 2DA Memory Tokens

This example uses 2DAMEMORY tokens to reference row indices from a custom appearance.2da table:

```ini
[2DAList]
2DAMEMORY100=appearance_sounds.2da
2DAMEMORY101=sound_battlecry_row
2DAMEMORY102=sound_selected_row

[appearance_sounds.2da]
; Column is soundset_strref
row_label|soundset_strref
JediVoice|50000
SithVoice|50100

[sound_battlecry_row]
; References the appearance_sounds.2da row index
RowIndex=2DAMEMORY100

[sound_selected_row]
RowIndex=2DAMEMORY101

[SSFList]
File0=dynamic_voice.ssf

[dynamic_voice.ssf]
Battlecry 1=2DAMEMORY102
Selected 1=2DAMEMORY103
```

**Note:** The 2DAMEMORY values in this example would need to extract the actual stringref values from the 2DA cells, which requires additional configuration in the 2DA section.

### Example 4: Replace File Behavior

This example demonstrates the difference between FileN and ReplaceN syntax:

```ini
[SSFList]
!DefaultDestination=Override
File0=modify_existing.ssf
Replace0=always_fresh.ssf

[modify_existing.ssf]
; This will be loaded from Override if it exists,
; otherwise copied from tslpatchdata and then modified
Battlecry 1=60001
Selected 1=60002

[always_fresh.ssf]
; This will always copy fresh from tslpatchdata,
; overwriting any existing file, then be modified
Battlecry 1=70001
Selected 1=70002
```

### Example 5: Complex Multi-File Sound Set

This example patches multiple sound sets with different configurations:

```ini
[SSFList]
!DefaultDestination=Override
!DefaultSourceFolder=voices
File0=jedi_male.ssf
File1=jedi_female.ssf
Replace0=sith_dark.ssf

[jedi_male.ssf]
!SourceFolder=voices/jedi
Battlecry 1=40001
Battlecry 2=40002
Selected 1=40003
Attack 1=40004
Death=40005
Critical hit=40006

[jedi_female.ssf]
!SourceFolder=voices/jedi
Battlecry 1=40051
Battlecry 2=40052
Selected 1=40053
Attack 1=40054
Death=40055
Critical hit=40056

[sith_dark.ssf]
!Destination=Override
!ReplaceFile=1
Battlecry 1=40101
Battlecry 2=40102
Selected 1=40103
Attack 1=40104
Death=40105
Critical hit=40106
Target immune=40107
```

### Example 6: Comprehensive Sound Set with All Entries

This example demonstrates patching all 28 sound entries:

```ini
[SSFList]
File0=comprehensive_voice.ssf

[comprehensive_voice.ssf]
Battlecry 1=50001
Battlecry 2=50002
Battlecry 3=50003
Battlecry 4=50004
Battlecry 5=50005
Battlecry 6=50006
Selected 1=50010
Selected 2=50011
Selected 3=50012
Attack 1=50020
Attack 2=50021
Attack 3=50022
Pain 1=50030
Pain 2=50031
Low health=50040
Death=50050
Critical hit=50060
Target immune=50070
Place mine=50080
Disarm mine=50081
Stealth on=50090
Search=50091
Pick lock start=50100
Pick lock fail=50101
Pick lock done=50102
Leave party=50110
Rejoin party=50111
Poisoned=50120
```

### Example 7: Modifying SSF Files in Archives

This example shows how to patch SSF files that are stored in ERF/MOD/RIM archive files:

```ini
[SSFList]
File0=npc_voice.ssf

[npc_voice.ssf]
!Destination=Modules\my_module.mod
Battlecry 1=60001
Selected 1=60002
Attack 1=60003
Death=60004
```

**Important:** When patching files in archives, ensure that:

1. The archive file exists in the game directory
2. The SSF file already exists in that archive (or use ReplaceN to force overwrite)
3. Use backslashes for path separators in `!Destination`

### Example 8: Clearing Sound Entries

This example demonstrates setting sound entries to -1 (no sound):

```ini
[SSFList]
File0=quiet_character.ssf

[quiet_character.ssf]
; Remove all battle cries
Battlecry 1=-1
Battlecry 2=-1
Battlecry 3=-1
Battlecry 4=-1
Battlecry 5=-1
Battlecry 6=-1

; Keep only selection sounds
Selected 1=12345
Selected 2=12346
Selected 3=12347
```

**Note:** The value -1 (or any negative value) typically represents "no sound" in the game engine. Setting all entries to -1 would create a silent character soundset.

## Advanced Usage

### Combining Multiple Token Types

You can mix different value types within the same SSF file section:

```ini
[SSFList]
File0=mixed_tokens.ssf

[mixed_tokens.ssf]
Battlecry 1=12345
Battlecry 2=StrRef100
Battlecry 3=2DAMEMORY50
Battlecry 4=-1
Selected 1=StrRef101
Attack 1=54321
Pain 1=2DAMEMORY51
```

### Inheritance of Configuration

Configuration options cascade from the `[SSFList]` section to individual file sections:

```ini
[SSFList]
!DefaultDestination=Override
!DefaultSourceFolder=voices
File0=voice1.ssf
File1=voice2.ssf

[voice1.ssf]
; Inherits !DefaultDestination=Override
; Inherits !DefaultSourceFolder=voices
Battlecry 1=10001

[voice2.ssf]
; Inherits !DefaultDestination=Override
; Inherits !DefaultSourceFolder=voices
!SourceFolder=voices/alternate
Battlecry 1=20001
```

### Compatibility Notes

- SSF files are binary format files with version "V1.1"
- All stringref values are stored as 32-bit unsigned integers
- The game engine interprets negative values (-1) as "no sound"
- SSF files have a fixed structure with exactly 28 sound slots
- Empty or unset sound slots default to -1 when a new SSF is created
- PyKotor/TSLPatcher loads existing SSF files from the override folder or specified archive if they exist

## Troubleshooting

### Common Issues

**Problem:** Sound entries not applying

- **Solution:** Verify that the sound entry name matches exactly (including spaces) from the [Available Sound Entries](#available-sound-entries) table
- **Solution:** Ensure the SSF file exists in the specified source location (tslpatchdata folder)

**Problem:** Token values not resolving

- **Solution:** Ensure TLK memory tokens (StrRef#) are set before SSFList section runs
- **Solution:** Ensure 2DA memory tokens (2DAMEMORY#) are set before SSFList section runs
- **Solution:** Verify token IDs match between where they're set and where they're used

**Problem:** File not found in destination

- **Solution:** When using FileN syntax, the file must either exist in destination or in tslpatchdata
- **Solution:** Use ReplaceN syntax to always copy from tslpatchdata
- **Solution:** Set `!ReplaceFile=1` in the file section to force replacement

**Problem:** Incorrect file being loaded

- **Solution:** Check `!SourceFolder` path is correct relative to tslpatchdata root
- **Solution:** Verify `!SourceFile` matches the actual filename if different from section name
- **Solution:** Ensure !DefaultSourceFolder is set correctly at SSFList level

**Problem:** Archive insertion failing

- **Solution:** Verify the archive file exists in the game directory
- **Solution:** Use backslashes (not forward slashes) in !Destination paths
- **Solution:** Ensure the SSF file already exists in the archive if not using ReplaceN syntax

### Installation Order

TSLPatcher processes sections in a specific order. SSFList is processed after:

1. TLK Appending (TLKList)
2. Install List
3. 2DA changes (2DAList)
4. GFF Changes (GFFList)
5. Script compilation

This means that memory tokens set in TLKList and 2DAList will be available when SSFList runs. SSFList runs before final file installation operations.

## Reference

### Implementation Details

**Binary Format:**

- Header: "SSF " (4 bytes)
- Version: "V1.1" (4 bytes)
- Offset to sound data: 4 bytes (uint32)
- Sound entries: 28 x 4 bytes (uint32 each) = 112 bytes
- Padding: 12 x 4 bytes (0xFFFFFFFF) = 48 bytes
- Total size: ~160 bytes

**Default Values:**

- All sound entries default to -1 in a new SSF file
- Replacement behavior defaults to modifying existing files when possible
- Destination defaults to Override folder
- Source folder defaults to tslpatchdata root (`.`)

**Supported Operations:**

- Read existing SSF files from Override or archives
- Write modified SSF files to Override or archives
- Modify any of the 28 sound entry stringrefs
- Support for TLK and 2DA memory token resolution
- Replace file or modify existing file modes

---

**Last Updated:** Based on PyKotor implementation and TSLPatcher v1.2.10b compatibility
