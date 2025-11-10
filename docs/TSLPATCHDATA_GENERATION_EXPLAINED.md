# How TSLPatchData Files Are Generated - Complete Explanation

## Overview

The `tslpatchdata` folder contains the actual resource files and INI configuration needed for TSLPatcher to apply a mod. This document explains how the diff engine produces this directory structure.

## Architecture

```bash
Vanilla Files → Diff Engine → ModificationsByType → Writer → tslpatchdata/
                                                              ├── changes.ini
                                                              ├── spells.2da
                                                              ├── appearance.2da
                                                              ├── creature.utc
                                                              ├── append.tlk
                                                              ├── character.ssf
                                                              └── [other resources]
```

## Key Classes

### 1. **IncrementalTSLPatchDataWriter** (Main Writer Class)

Located in `writer.py` (line 1208), this class manages the entire `tslpatchdata` generation:

```python
class IncrementalTSLPatchDataWriter:
    def __init__(
        self,
        tslpatchdata_path: Path,      # Path to tslpatchdata folder
        ini_filename: str,             # Usually "changes.ini"
        base_data_path: Path | None = None,
        modded_data_path: Path | None = None,
        strref_cache: StrRefReferenceCache | None = None,
        twoda_caches: dict[int, CaseInsensitiveDict] | None = None,
        log_func: Callable[[str], None] | None = None,
    ):
```

**Key responsibilities:**

- Creates the `tslpatchdata_path` directory
- Initializes the INI file with all section headers
- Tracks which files have been written
- Manages 2DAMEMORY token allocation
- Builds linking patches for cross-file references

### 2. **Modification Objects** (Input to Writer)

From `pykotor.tslpatcher.mods.*`:

- **Modifications2DA** - Changes to 2DA files (AddRow, ChangeRow, AddColumn)
- **ModificationsGFF** - Changes to GFF files (ModifyField, AddField, AddStructToList)
- **ModificationsTLK** - Changes to TLK files (append/replace entries)
- **ModificationsSSF** - Changes to SSF sound files
- **ModificationsNCS** - Changes to NCS compiled scripts

Each contains:

- `sourcefile` - The resource filename (e.g., "spells.2da")
- `modifiers` - List of specific changes
- `replace_file` - Whether to replace the entire file

## Directory Structure Generated

### What Gets Saved to `tslpatchdata/`

```bash
tslpatchdata/
│
├── changes.ini                 ← Main TSLPatcher configuration file
│
├── [Resource Files - The ACTUAL data to be modified]
│   ├── spells.2da              ← Vanilla file to be patched
│   ├── appearance.2da          ← Vanilla file to be patched
│   ├── creature.utc            ← Vanilla file to be patched
│   ├── character.ssf           ← Vanilla file to be patched
│   ├── append.tlk              ← NEW TLK entries to append
│   └── ...
│
└── [No subdirectories - All files in root]
    Note: The destination (Override, modules\xyz.mod) is specified in INI,
          not as subdirectories in tslpatchdata/
```

**CRITICAL**: All resource files go directly in the `tslpatchdata` root, NOT in subdirectories. The `destination` field in the INI tells TSLPatcher where to install them at runtime.

## How Files Are Written - Step by Step

### Step 1: Initialization (Constructor)

```python
# Line 1262: Create tslpatchdata directory
self.tslpatchdata_path.mkdir(parents=True, exist_ok=True)

# Line 1286: Initialize INI with header and section structure
self._initialize_ini()
```

**Result**: `tslpatchdata/changes.ini` created with:

- Comment header with metadata
- [Settings] section
- All list section headers: [TLKList], [2DAList], [GFFList], [SSFList], etc.

### Step 2: Write Modifications (Main Loop)

```python
def write_modification(
    self,
    modification: PatcherModifications,
    source_data: bytes | None = None,
    source_path: Installation | Path | None = None,
    modded_source_path: Installation | Path | None = None,
) -> None:
    # Line 1481: Apply pending StrRef references
    self._apply_pending_strref_references(filename_lower, modification, source_data, source_path)
    
    # Line 1485: Apply pending 2DA row references
    if isinstance(modification, ModificationsGFF):
        self._apply_pending_2da_row_references(filename_lower, modification, source_data, source_path)
    
    # Line 1488-1497: Dispatch to type-specific writer
    if isinstance(modification, Modifications2DA):
        self._write_2da_modification(modification, source_data, source_path, modded_source_path)
    elif isinstance(modification, ModificationsGFF):
        self._write_gff_modification(modification, source_data)
    elif isinstance(modification, ModificationsTLK):
        self._write_tlk_modification(modification)
    elif isinstance(modification, ModificationsSSF):
        self._write_ssf_modification(modification, source_data)
    elif isinstance(modification, ModificationsNCS):
        self._write_ncs_modification(modification, source_data)
```

### Step 3: Type-Specific Writers

#### 3A. Writing 2DA Files (`_write_2da_modification`)

```python
def _write_2da_modification(self, mod_2da: Modifications2DA, source_data: bytes | None, ...):
    
    # Line 1520: Construct output path - DIRECTLY IN TSLPATCHDATA ROOT
    output_path: Path = self.tslpatchdata_path / filename
    
    # Line 1522-1523: Read vanilla 2DA and write to tslpatchdata
    if source_data:
        twoda_obj = read_2da(source_data)
        write_2da(twoda_obj, output_path, ResourceType.TwoDA)
    
    # Line 1533: Add to install folder tracking (for InstallList INI section)
    self._add_to_install_folder("Override", filename)
    
    # Line 1536: Write INI section with AddRow/ChangeRow/AddColumn directives
    self._write_to_ini([mod_2da], "2da")
```

**Result**:

- File saved: `tslpatchdata/spells.2da` (vanilla version)
- INI updated with AddRow/ChangeRow/AddColumn sections

#### 3B. Writing GFF Files (`_write_gff_modification`)

```python
def _write_gff_modification(self, mod_gff: ModificationsGFF, source_data: bytes | None):
    
    # Line 1863-1866: Get destination and actual filename
    destination: str = getattr(mod_gff, "destination", "Override")
    actual_filename: str = getattr(mod_gff, "saveas", mod_gff.sourcefile)
    
    # Line 1870: Output path - DIRECTLY IN TSLPATCHDATA ROOT
    output_path: Path = self.tslpatchdata_path / actual_filename
    
    # Line 1875-1911: Read vanilla GFF, detect format, write to tslpatchdata
    if source_data:
        gff_obj = read_gff(source_data)
        ext = PurePath(actual_filename).suffix.lstrip(".").lower()
        restype: ResourceType | None = ResourceType.from_extension(ext)
        
        # Determine output format (GFF, GFF_XML, or GFF_JSON)
        file_format: ResourceType = detect_gff(source_data)
        if file_format not in {ResourceType.GFF, ResourceType.GFF_XML, ResourceType.GFF_JSON}:
            file_format = ResourceType.GFF
        
        write_gff(gff_obj, output_path, file_format)
    
    # Line 1921: Add to install folder tracking
    self._add_to_install_folder(destination, actual_filename)
    
    # Line 1924: Write INI section with ModifyField directives
    self._write_to_ini([mod_gff], "gff")
```

**Result**:

- File saved: `tslpatchdata/creature.utc` (vanilla version)
- INI updated with field modifications
- InstallList will specify destination folder

#### 3C. Writing TLK Files (`_write_tlk_modification`)

```python
def _write_tlk_modification(self, mod_tlk: ModificationsTLK):
    
    # Line 1948-1953: Extract append entries and create TLK object
    appends: list[ModifyTLK] = [m for m in mod_tlk.modifiers if not m.is_replacement]
    
    if appends:
        append_tlk: TLK = TLK()
        append_tlk.resize(len(appends))
        
        # Line 1957-1960: Populate TLK with new entries
        sorted_appends: list[ModifyTLK] = sorted(appends, key=lambda m: m.token_id)
        for append_idx, modifier in enumerate(sorted_appends):
            text: str = modifier.text if modifier.text else ""
            sound_str: str = str(modifier.sound) if modifier.sound else ""
            append_tlk.replace(append_idx, text, sound_str)
        
        # Line 1962-1963: Write append.tlk to tslpatchdata root
        append_path: Path = self.tslpatchdata_path / "append.tlk"
        write_tlk(append_tlk, append_path, ResourceType.TLK)
    
    # Line 1967: Add to install folders (note: destination is "." = game root)
    self._add_to_install_folder(".", "append.tlk")
```

**Result**:

- File saved: `tslpatchdata/append.tlk` (NEW file with appended entries)
- INI updated with StrRef mappings (line 1981)

#### 3D. Writing SSF Files (`_write_ssf_modification`)

```python
def _write_ssf_modification(self, mod_ssf: ModificationsSSF, source_data: bytes | None):
    
    # Similar to GFF:
    output_path: Path = self.tslpatchdata_path / filename
    
    if source_data:
        ssf_obj = read_ssf(source_data)
        write_ssf(ssf_obj, output_path, ResourceType.SSF)
    
    self._add_to_install_folder("Override", filename)
    self._write_to_ini([mod_ssf], "ssf")
```

**Result**:

- File saved: `tslpatchdata/character.ssf` (vanilla version)
- INI updated with sound slot modifications

## INI Generation

### Step 4: Finalize INI

```python
def finalize(self) -> None:
    """Finalize the INI file - all sections are already written incrementally."""
    
    # Line 4234: Flush any remaining pending writes
    self._flush_pending_writes()
```

### INI Structure Generated

```ini
; ============================================================================
;  TSLPatcher Modifications File — Generated by HoloPatcher (11/08/2025)
; ============================================================================

[Settings]
FileExists=1
LogLevel=3
InstallerMode=1
BackupFiles=1

[TLKList]                                    ← Section 1: Text entries
StrRef0=0
StrRef1=1

[append.tlk]                                 ← Maps StrRef IDs to entries
0=New dialog entry text
1=Another dialog entry

[InstallList]                                ← Section 2: File destinations
install_folder0=Override
install_folder1=modules\danm13.mod

[2DAList]                                    ← Section 3: Table modifications
Table0=spells.2da
Table1=appearance.2da

[spells.2da]                                 ← File-specific section
AddRow0=new_spell_section

[new_spell_section]                          ← Actual AddRow data
RowLabel=999
label=FORCE_POWER_NEW
name=32000
2DAMEMORY0=RowIndex
ExclusiveColumn=label

[GFFList]                                    ← Section 4: GFF modifications
File0=creature.utc

[creature.utc]                               ← File-specific section
ClassList\0\KnownList0\1\Spell=2DAMEMORY0   ← Uses token from 2DA

[SSFList]                                    ← Section 5: Sound file modifications
File0=character.ssf

[character.ssf]                              ← Sound modifications
Battlecry 1=StrRef0                         ← Uses token from TLK

[install_folder0]                           ← InstallList details
Replace0=model.mdl
Replace1=model.mdx
File2=texture.tga
```

## Key Concepts

### 1. **Vanilla Files as Input**

The writer reads the VANILLA versions of files (the unmodified originals) and saves them to `tslpatchdata/`.

Why? TSLPatcher needs:

- The ORIGINAL file to understand what to patch FROM
- The INI instructions describing what to change
- Together, they produce the final modded file

### 2. **INI as Instructions**

The INI file is pure INSTRUCTIONS. Example:

```ini
[spells.2da]
ChangeRow0=modify_spell

[modify_spell]
RowIndex=100
name=32000
spelldesc=32001
```

This says: "In spells.2da, modify row 100: set name to StrRef 32000, spelldesc to StrRef 32001"

### 3. **Resource Files as Base**

The resource files (spells.2da, creature.utc, etc.) are the BASE files that TSLPatcher will patch.

When TSLPatcher runs, it:

1. Reads the vanilla file from `tslpatchdata/spells.2da`
2. Reads the INI instructions
3. Applies the changes
4. Writes the result to the game directory

### 4. **Token System (2DAMEMORY, StrRef)**

The writer generates TOKENS to link cross-file references:

```ini
[spells.2da]
AddRow0=new_spell

[new_spell]
2DAMEMORY0=RowIndex          ← Store row index in token 0

[creature.utc]
ClassList\0\KnownList0\1\Spell=2DAMEMORY0    ← Use token 0
```

This allows GFF files to reference 2DA rows by token instead of hardcoded indices.

## Directory Structure Summary

```
tslpatchdata/
├── changes.ini              [The INI configuration file - ~10-50 KB]
├── spells.2da               [Vanilla file - typically small, ~50-200 KB]
├── appearance.2da           [Vanilla file - typically small]
├── baseitems.2da            [Vanilla file - typically small]
├── creature.utc             [Vanilla GFF file - typically ~50-500 KB]
├── character.ssf            [Vanilla SSF file - typically ~1-10 KB]
├── append.tlk               [NEW TLK with appended entries - variable size]
└── [other resource files as needed]
```

**Key Point**: NO subdirectories. Everything is in the root. The destination folder is specified in the INI.

## How Diff Results → tslpatchdata

1. **Diff Engine** runs and produces:
   - `Modifications2DA` objects with AddRow/ChangeRow/AddColumn data
   - `ModificationsGFF` objects with ModifyField/AddField data
   - `ModificationsTLK` objects with new/modified TLK entries
   - `ModificationsSSF` objects with modified sound slots

2. **Writer** receives modifications:
   - Reads vanilla files from installation
   - Writes vanilla files to tslpatchdata/
   - Creates INI sections with modification instructions
   - Allocates 2DAMEMORY tokens for cross-references
   - Generates linking patches for StrRef/2DA references

3. **tslpatchdata/** is created with:
   - Vanilla resource files (base for patching)
   - changes.ini (instructions for TSLPatcher)
   - append.tlk if needed (new TLK entries)

4. **TSLPatcher** reads this and applies the mod:
   - Loads vanilla files from tslpatchdata/
   - Reads INI instructions
   - Modifies the files according to INI
   - Writes modified files to game installation

## Example: Complete Workflow

### Input (from Diff Engine)

```python
Modifications2DA(
    sourcefile="spells.2da",
    modifiers=[
        AddRow2DA(
            identifier="new_spell",
            cells={"label": "FORCE_POWER_NEW", "name": "32000"},
            store_2da={0: RowValueRowIndex()}  # Store index in token 0
        )
    ]
)
```

### Writer Process

1. Reads vanilla spells.2da from installation → 1,000 rows
2. Writes vanilla spells.2da to tslpatchdata/spells.2da
3. Generates INI section:

```ini
[spells.2da]
AddRow0=new_spell

[new_spell]
RowLabel=1001
label=FORCE_POWER_NEW
name=32000
2DAMEMORY0=RowIndex
ExclusiveColumn=label
```

### Output (tslpatchdata/)

```
tslpatchdata/
├── changes.ini [with AddRow section]
└── spells.2da [vanilla version with 1000 rows]
```

### TSLPatcher Execution

1. Reads tslpatchdata/spells.2da (1000 rows)
2. Reads INI: "AddRow with label=FORCE_POWER_NEW, name=32000"
3. Adds new row 1001 with these values
4. Writes result to game installation

## Summary

The `tslpatchdata` folder contains:

1. **Resource Files** - Vanilla versions of files to be patched
2. **changes.ini** - Instructions describing HOW to patch them
3. **Linking Tokens** - 2DAMEMORY and StrRef mappings for cross-file references

The **writer converts diff output to this structure**:

- Reads vanilla files (from installation or provided data)
- Allocates tokens for 2DA rows and TLK entries
- Writes INI instructions
- Saves vanilla resource files as the base
- Tracks file destinations and installation folders

When **TSLPatcher runs**, it:

1. Loads vanilla files from tslpatchdata/
2. Reads INI instructions
3. Applies modifications
4. Installs result to game

This separation allows TSLPatcher to work independently without needing the diff engine or the original installation!
