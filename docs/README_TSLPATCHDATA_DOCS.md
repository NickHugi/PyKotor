# TSLPatchData Generation Documentation

Complete documentation explaining how the diff engine generates `tslpatchdata` files and how they work with the writer.

## Quick Links

- **[HOW_TSLPATCHDATA_WORKS.md](HOW_TSLPATCHDATA_WORKS.md)** - Start here! Complete guide with examples
- **[TSLPATCHDATA_GENERATION_EXPLAINED.md](TSLPATCHDATA_GENERATION_EXPLAINED.md)** - Deep dive into the writer code
- **[TSLPATCHDATA_FLOW_DIAGRAM.md](TSLPATCHDATA_FLOW_DIAGRAM.md)** - Visual flowcharts and diagrams

## What You'll Learn

### From HOW_TSLPATCHDATA_WORKS.md

- What goes into `tslpatchdata/`
- Why vanilla files are needed
- How the INI file works
- The token system for cross-file references
- Complete working example
- File writing rules
- Performance considerations

### From TSLPATCHDATA_GENERATION_EXPLAINED.md

- The `IncrementalTSLPatchDataWriter` class
- How each file type is written
  - 2DA files
  - GFF files
  - TLK files
  - SSF files
- The initialization process
- INI section generation
- Key concepts and patterns
- How diff results become tslpatchdata

### From TSLPATCHDATA_FLOW_DIAGRAM.md

Visual representations of:

- Overall data flow (vanilla → diff → writer → tslpatchdata → TSLPatcher)
- Writer type dispatch
- Internal state machine
- 2DA modification sequence
- GFF modification sequence
- TLK modification sequence
- INI section generation order
- Cross-file reference chains
- Directory structure on disk

## The Big Picture

```
Diff Engine              Writer                    TSLPatcher
┌─────────────┐    ┌───────────────┐           ┌──────────────┐
│  Vanilla    │    │ Modification  │           │   Reads      │
│     vs      ├───→│  objects  (2DA,├──────────→│ tslpatchdata/│
│  Modded     │    │    GFF, TLK)  │           │ and applies  │
│   Files     │    │               │           │    changes   │
└─────────────┘    │ Allocate      │           └──────────────┘
                   │ tokens,       │                   │
                   │ generate INI, │                   │
                   │ write resources
                   │ to tslpatchdata/
                   └───────────────┘
```

## Key Concepts

### 1. Vanilla Files as Base

The writer saves vanilla files to `tslpatchdata/`. TSLPatcher reads these and patches them according to INI instructions.

### 2. The INI File

`changes.ini` contains all instructions for TSLPatcher:

- What files to modify
- What changes to make
- How to resolve tokens

### 3. Token System

`2DAMEMORY#` and `StrRef#` tokens allow cross-file references:

- 2DA rows can be referenced by GFF files
- New TLK entries can be referenced by all file types
- Tokens are resolved at patch time

### 4. File Types

- **2DA**: Spreadsheet-like data files
- **GFF**: Binary structured files (creatures, items, dialogs, etc.)
- **TLK**: Dialog/text database
- **SSF**: Sound set files

## File Structure Generated

```
tslpatchdata/
├── changes.ini              # Main configuration file
├── spells.2da              # Vanilla files (base for patching)
├── appearance.2da          # Vanilla files
├── creature.utc            # Vanilla GFF file
├── character.ssf           # Vanilla SSF file
├── append.tlk              # NEW: Appended TLK entries
└── [other resources...]    # Any modified files

Key Points:
✓ All files in root (no subdirectories)
✓ changes.ini specifies destinations
✓ Vanilla files are the base
✓ append.tlk contains new entries only
✓ Ready for TSLPatcher to read
```

## Writer Process (Simplified)

```
1. Initialize tslpatchdata/ directory
   └─ Create changes.ini with header and section structure

2. For each modification type:
   ├─ Read vanilla file from source
   ├─ Write vanilla file to tslpatchdata/
   ├─ Generate INI sections with instructions
   ├─ Track tokens for cross-references
   └─ Record installation destination

3. Apply linking patches:
   ├─ Find files referencing new 2DA rows
   ├─ Find files referencing new TLK entries
   ├─ Generate patches with token references
   └─ Update INI sections

4. Finalize:
   ├─ Replace token references in cells
   ├─ Rewrite complete INI file
   └─ Summary statistics
```

## Code References

### Key Classes

- **`IncrementalTSLPatchDataWriter`** (writer.py:1208)
  - Main writer class managing tslpatchdata generation
  - Handles all file type writing
  - Manages token allocation

- **Modification Objects**
  - `Modifications2DA` - 2DA changes
  - `ModificationsGFF` - GFF changes
  - `ModificationsTLK` - TLK changes
  - `ModificationsSSF` - SSF changes

### Key Methods

- **`write_modification()`** (writer.py:1465)
  - Main entry point, dispatches to type-specific writers

- **`_write_2da_modification()`** (writer.py:1501)
  - Handles 2DA file writing

- **`_write_gff_modification()`** (writer.py:1846)
  - Handles GFF file writing

- **`_write_tlk_modification()`** (writer.py:1931)
  - Handles TLK file writing and StrRef linking

- **`_write_ssf_modification()`** (writer.py:3726)
  - Handles SSF file writing

## Example Walkthrough

### Simple Example: Modify a Spell

**Vanilla**:

```
spells.2da (row 100):
  label=Force_Heal
  name=100
```

**Modded**:

```
spells.2da (row 100):
  label=Force_Heal
  name=32000  (new StrRef)
```

**Writer Process**:

1. Detect change: name field changed from 100 to StrRef 32000
2. Read vanilla spells.2da (1000 rows)
3. Write to tslpatchdata/spells.2da
4. Generate INI:

```ini
[2DAList]
Table0=spells.2da

[spells.2da]
ChangeRow0=modify_spell

[modify_spell]
RowIndex=100
name=StrRef0
```

**TSLPatcher Runtime**:

1. Load tslpatchdata/spells.2da
2. Read ChangeRow instruction
3. Modify row 100: name = StrRef 0 value
4. Write modified spells.2da to game

### Complex Example: New Spell with Creatures

See HOW_TSLPATCHDATA_WORKS.md for a complete walkthrough of adding a spell that's granted to multiple creatures using 2DAMEMORY tokens.

## Common Patterns

### Pattern 1: Add 2DA Row

```ini
[2DAList]
Table0=spells.2da

[spells.2da]
AddRow0=new_spell

[new_spell]
RowLabel=1001
label=MY_SPELL
2DAMEMORY0=RowIndex  # Store row index
ExclusiveColumn=label
```

### Pattern 2: Modify GFF Field

```ini
[GFFList]
File0=creature.utc

[creature.utc]
Appearance_Type=999  # Direct modification
```

### Pattern 3: Use Token in GFF

```ini
[creature.utc]
ClassList\0\KnownList0\1\Spell=2DAMEMORY0  # Reference token
```

### Pattern 4: Add TLK Entry

```ini
[TLKList]
StrRef0=0

[append.tlk]
25859=0  # Map old StrRef to new entry

[spells.2da]
name=StrRef0  # Reference in 2DA
```

## Testing

The comprehensive test suite in `test_diff_comprehensive.py` includes tests for all tslpatchdata generation patterns:

- 2DAMEMORY token storage and usage
- Cross-file reference chains
- TLK entry generation and mapping
- GFF field modifications
- SSF sound modifications
- Real-world mod patterns
- Edge cases and performance

See [QUICK_START.md](QUICK_START.md) for instructions on running tests.

## Troubleshooting

### Generated files don't appear

- Check `tslpatchdata_path` is writable
- Verify modification object has source data
- Check file type dispatcher is called

### INI syntax issues

- Review expected INI format in documentation
- Compare with real mod examples in workspace
- Check backslash escaping in paths

### Tokens not resolving

- Verify token allocated during diff
- Check token used in correct sections
- Ensure token numbers don't conflict

## Related Documentation

- [TSLPATCHDATA_GENERATION_EXPLAINED.md](TSLPATCHDATA_GENERATION_EXPLAINED.md) - Code-level explanation
- [TSLPATCHDATA_FLOW_DIAGRAM.md](TSLPATCHDATA_FLOW_DIAGRAM.md) - Visual flowcharts
- [HOW_TSLPATCHDATA_WORKS.md](HOW_TSLPATCHDATA_WORKS.md) - Complete working guide

## Summary

The writer converts diff results into a self-contained `tslpatchdata/` folder that TSLPatcher can read and apply independently:

1. **Input**: Modification objects from diff engine
2. **Processing**: Save vanilla files, generate INI instructions
3. **Output**: Complete tslpatchdata/ ready for TSLPatcher
4. **Result**: Mod applied to game installation

All documentation, code references, and visual diagrams are provided to understand this critical part of the PyKotor TSLPatcher ecosystem.
