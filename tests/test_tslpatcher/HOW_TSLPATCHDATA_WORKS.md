# How TSLPatchData Works - Complete Guide

## The 60-Second Summary

1. **Diff Engine** analyzes vanilla vs modded files and generates `Modification` objects
2. **Writer** converts these to `tslpatchdata/` folder containing:
   - `changes.ini` - Instructions for TSLPatcher
   - Resource files (vanilla versions) - The base files to patch
   - `append.tlk` (if TLK changes) - New dialog entries
3. **TSLPatcher** reads this folder and applies the mod to your game

## What Goes Into tslpatchdata/

```bash
tslpatchdata/
├── changes.ini                    ← The key file: all instructions
├── [Vanilla Resource Files]
│   ├── spells.2da                ← Base for patching
│   ├── appearance.2da            ← Base for patching
│   ├── creature.utc              ← Base for patching
│   ├── character.ssf             ← Base for patching
│   └── ... other resources ...
└── [NEW Files if Applicable]
    └── append.tlk                 ← New TLK entries (if TLK changes)
```

### Why Vanilla Files?

**TSLPatcher needs:**

- Original file to understand structure
- INI instructions to know what to change
- Together: `original + instructions = modified file`

Example:

```text
spells.2da (vanilla)        changes.ini (instructions)        spells.2da (modded)
[1000 rows]            +    [Add row 1001 with these]    =    [1001 rows]
                            values at these locations]
```

## The Four Main Writers

### 1. **2DA Writer** (`_write_2da_modification`)

**Input**: Modifications2DA with AddRow/ChangeRow/AddColumn

**Process**:

1. Read vanilla 2DA from installation (e.g., spells.2da)
2. Write vanilla to tslpatchdata/spells.2da
3. Generate INI sections:

    ```ini
    [2DAList]
    Table0=spells.2da

    [spells.2da]
    AddRow0=new_spell

    [new_spell]
    RowLabel=1001
    label=FORCE_POWER_NEW
    2DAMEMORY0=RowIndex
    ```

**Output**:

- File: `tslpatchdata/spells.2da` (vanilla)
- INI: Sections describing what to add/change

### 2. **GFF Writer** (`_write_gff_modification`)

**Input**: ModificationsGFF with ModifyField/AddField/AddStructToList

**Process**:

1. Read vanilla GFF (e.g., creature.utc)
2. Detect format (binary GFF, XML, JSON)
3. Write vanilla to tslpatchdata/creature.utc
4. Generate INI sections:

    ```ini
    [GFFList]
    File0=creature.utc
    
    [creature.utc]
    !ReplaceFile=0
    ClassList\0\KnownList0\1\Spell=2DAMEMORY0
    ```

**Output**:

- File: `tslpatchdata/creature.utc` (vanilla)
- INI: Sections describing field modifications

### 3. **TLK Writer** (`_write_tlk_modification`)

**Input**: ModificationsTLK with new/modified dialog entries

**Process**:

1. Create NEW TLK object (not reading vanilla)
2. Add new dialog entries from modifications
3. Write to tslpatchdata/append.tlk
4. Generate INI sections:

```ini
   [TLKList]
   StrRef0=0
   StrRef1=1

   [append.tlk]
   (Internal structure mapping)
```

**Output**:

- File: `tslpatchdata/append.tlk` (NEW file with appended entries)
- INI: StrRef token mappings

### 4. **SSF Writer** (`_write_ssf_modification`)

**Input**: ModificationsSSF with sound slot changes

**Process**:

1. Read vanilla SSF (e.g., character.ssf)
2. Write vanilla to tslpatchdata/character.ssf
3. Generate INI sections:

```ini
   [SSFList]
   File0=character.ssf
   
   [character.ssf]
   Battlecry 1=StrRef0
   Selected 1=StrRef1
```

**Output**:

- File: `tslpatchdata/character.ssf` (vanilla)
- INI: Sections describing sound modifications

## The INI File - How It Works

The `changes.ini` file is a **recipe** for TSLPatcher:

```ini
[TLKList]                              ; "Here are TLK changes"
StrRef0=0                              ; Map token 0 to dialog entry 0
StrRef1=1                              ; Map token 1 to dialog entry 1

[append.tlk]
25859=0                                ; Old StrRef 25859 → new token 0
25860=1                                ; Old StrRef 25860 → new token 1

[2DAList]                              ; "Here are 2DA changes"
Table0=spells.2da                      ; File to modify

[spells.2da]                           ; "In spells.2da:"
AddRow0=new_spell                      ; Add row defined in [new_spell]

[new_spell]
RowLabel=1001
label=FORCE_POWER_NEW
name=StrRef0                           ; Reference TLK token 0
2DAMEMORY0=RowIndex                    ; Store row index in token 0

[GFFList]
File0=creature.utc

[creature.utc]
ClassList\0\KnownList0\1\Spell=2DAMEMORY0    ; Use 2DA token 0
```

## The Token System - Cross-File References

**Problem**: How does a GFF file reference a newly added 2DA row?

**Solution**: Use tokens!

Step 1: 2DA stores its new row index
[spells.2da AddRow]
→ 2DAMEMORY0=RowIndex  (store row 1001 in token 0)

Step 2: GFF references that token
[creature.utc ModifyField]
→ Spell=2DAMEMORY0  (use token 0, will be row 1001)

Step 3: TSLPatcher resolves at runtime

- Loads spells.2da, finds new row = 1001
- Stores 1001 in token 0
- Loads creature.utc, replaces 2DAMEMORY0 with 1001
- Sets Spell field to 1001

This works because:

1. Tokens are resolved **at patch time**, not at diff time
2. The row index might not be known until TSLPatcher runs
3. Adding row 1001 to spells.2da creates the new row
4. GFF then references that same row via token

## Complete Example: Adding a Spell

### Vanilla State

```text
spells.2da (1000 rows)
creature.utc with ClassList[0].KnownList[0][0].Spell = 50
```

### Modded State

```text
spells.2da (1001 rows)
  Row 1001: FORCE_POWER_NEW (NEW)
creature.utc with ClassList[0].KnownList[0][0].Spell = 50
            + ClassList[0].KnownList[0][1].Spell = 1001 (NEW)
```

### Diff Output

```text
Modifications2DA:
  AddRow: label=FORCE_POWER_NEW, name=32000, 2DAMEMORY0=RowIndex

ModificationsGFF:
  AddStructToList: ItemList, value references 2DAMEMORY0
```

### Writer Process

1. Read vanilla spells.2da (1000 rows)
2. Write to tslpatchdata/spells.2da
3. Generate INI:

    ```ini
    [spells.2da]
    AddRow0=force_power_new
    [force_power_new]
    RowLabel=1001
    label=FORCE_POWER_NEW
    2DAMEMORY0=RowIndex
    ```

4. Read vanilla creature.utc
5. Write to tslpatchdata/creature.utc
6. Generate INI:

    ```ini
    [creature.utc]
    AddField0=new_spell_entry
    [new_spell_entry]
    FieldType=Struct
    Path=ClassList\0\KnownList0
    TypeId=1
    Value=<subfied>
    [subfied]
    Spell=2DAMEMORY0  ← Uses token!
    ```

### TSLPatcher Runtime

1. Load tslpatchdata/changes.ini
2. Load tslpatchdata/spells.2da (1000 rows)
3. Apply AddRow directive:
   - Add row 1001: FORCE_POWER_NEW
   - Resolve 2DAMEMORY0 = row 1001
   - Store in token 0
4. Load tslpatchdata/creature.utc
5. Apply AddStructToList directive:
   - Add struct to ClassList[0].KnownList[0]
   - Set Spell field to 2DAMEMORY0
   - Resolve 2DAMEMORY0 to 1001
   - Set Spell field to 1001
6. Write modified files to installation

## File Writing Rules

### Critical Rules

1. **All files go in tslpatchdata root**, NOT in subdirectories

   ✓ tslpatchdata/spells.2da
   ✗ tslpatchdata/data/2da/spells.2da

2. **Destination is specified in INI**, not directory structure

   ```ini
   [install_folder0]
   Override
   [install_folder1]
   modules\danm13.mod
   ```

3. **Vanilla files are the base**
   - TSLPatcher reads vanilla from tslpatchdata/
   - Applies INI instructions
   - Writes modified to installation

4. **Filename might differ from sourcefile**

   ```python
   sourcefile = "creature.utc"  # Original name in diff
   saveas = "companion_bastila.utc"  # Saved as this name
   destination = "modules\danm13.mod"  # Installed here
   ```

## INI Section Generation Order

```text
1. HEADER & SETTINGS
   └── PyKotor branding, FileExists, LogLevel, etc.

2. [TLKList]
   ├── StrRef token mappings
   └── [append.tlk] (if any TLK changes)

3. [InstallList]
   ├── install_folder# references
   └── [install_folder#] (file listings)

4. [2DAList]
   ├── Table# references
   ├── [filename] sections
   └── [modifier] sections

5. [GFFList]
   ├── File# or Replace# references
   ├── [filename] sections
   └── [AddField#] sections

6. [CompileList]
   └── NCS compilation (if applicable)

7. [SSFList]
   ├── File# references
   └── [filename] sections
```

## Performance Considerations

### Batch Processing

- Multiple 2DA rows written together
- StrRef references batched for lookup
- INI sections written incrementally
- Final INI rewritten once for completeness

### Memory Usage

- Vanilla files loaded once per modification
- TLK caches built to find references
- 2DAMEMORY tokens allocated during diff
- No temporary files created

### Typical Sizes

```text
Simple 2DA changes:        2-10 KB
GFF modifications:         10-50 KB
Complex mod with TLK:      50-500 KB
Large installations:       1-50 MB
```

## Troubleshooting

### Files Not Found

- Check `tslpatchdata/` directory exists
- Verify `changes.ini` has correct [TLKList], [2DAList], etc. sections
- Ensure resource files (spells.2da, creature.utc) are present

### INI Syntax Errors

- Verify backslashes in paths: `ClassList\0\...`
- Check token format: `2DAMEMORY#=RowIndex`
- Ensure section names match exactly

### Missing 2DAMEMORY Tokens

- Check AddRow/ChangeRow sections have `2DAMEMORY#=` lines
- Verify token is used in GFF field
- Ensure token numbers don't conflict

### Token References Not Resolving

- Verify token stored in 2DA: `2DAMEMORY0=RowIndex`
- Check GFF uses correct token number: `Field=2DAMEMORY0`
- Ensure both files in same INI

## Summary

**tslpatchdata** is the bridge between the **diff engine** and **TSLPatcher**:

- **Input**: Diff results (Modification objects)
- **Output**: Self-contained folder with all needed files
- **TSLPatcher**: Reads this folder and applies the mod independently

The writer's job:

1. Read vanilla files from source
2. Generate INI instructions
3. Save vanilla files as base for patching
4. Allocate and track tokens for cross-file references
5. Create complete, self-contained tslpatchdata/

Result: TSLPatcher can apply your mod without needing anything else!
