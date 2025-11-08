# TSLPatchData Generation - Visual Flow Diagrams

## 1. Overall Data Flow

```bash
                        ┌─────────────────────────────────────────────┐
                        │   Vanilla Installation / Base Files         │
                        │  (C:\Kotor\data\2da.bif, etc.)              │
                        └──────────────┬──────────────────────────────┘
                                       │ Read vanilla files
                                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         DIFF ENGINE                                       │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  1. Compare vanilla vs modded files                               │  │
│  │  2. Detect differences (AddRow, ChangeRow, ModifyField, etc.)    │  │
│  │  3. Generate Modification objects                                │  │
│  │  4. Allocate 2DAMEMORY tokens for cross-references              │  │
│  │  5. Build StrRef mappings for TLK linking                       │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────┬───────────────────────────────────────────────┘
                           │ Output: ModificationsByType
                           │ ├── list[Modifications2DA]
                           │ ├── list[ModificationsGFF]
                           │ ├── list[ModificationsTLK]
                           │ ├── list[ModificationsSSF]
                           │ └── list[ModificationsNCS]
                           ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    INCREMENTAL WRITER                                     │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  1. Initialize tslpatchdata/ directory                            │  │
│  │  2. Write changes.ini skeleton (header + section headers)         │  │
│  │  3. For each modification:                                        │  │
│  │     a. Dispatch to type-specific writer                          │  │
│  │     b. Save vanilla resource file to tslpatchdata/               │  │
│  │     c. Write INI section with modification instructions          │  │
│  │     d. Track 2DAMEMORY tokens for cross-file references          │  │
│  │     e. Build linking patches (StrRef, 2DA row references)        │  │
│  │  4. Finalize INI with complete section content                  │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────┬───────────────────────────────────────────────┘
                           │ Output: tslpatchdata/ directory structure
                           │ ├── changes.ini (10-50 KB)
                           │ ├── spells.2da (vanilla - ~100 KB)
                           │ ├── appearance.2da (vanilla)
                           │ ├── creature.utc (vanilla - ~200 KB)
                           │ ├── character.ssf (vanilla)
                           │ ├── append.tlk (new entries)
                           │ └── [other resources]
                           ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                       TSLPatcher Application                              │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  1. Read tslpatchdata/changes.ini                                 │  │
│  │  2. Load vanilla files from tslpatchdata/                         │  │
│  │  3. Parse INI sections (2DAList, GFFList, TLKList, etc.)         │  │
│  │  4. Apply modifications using INI instructions                    │  │
│  │  5. Resolve 2DAMEMORY and StrRef tokens                          │  │
│  │  6. Write modified files to installation directory               │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────┬───────────────────────────────────────────────┘
                           │ Output: Modified game installation
                           │ ├── data/2da.bif (updated)
                           │ ├── data/dialog.tlk (updated)
                           │ ├── override/creature.utc (new/modified)
                           │ └── modules/danm13.mod (updated)
                           ▼
                    ┌──────────────────┐
                    │  Modded Game     │
                    │  Ready to play!  │
                    └──────────────────┘
```

## 2. Writer Type Dispatch

```
            write_modification()
                    │
          ┌─────────┼─────────┬────────────┬────────────┐
          │         │         │            │            │
          ▼         ▼         ▼            ▼            ▼
     2DA GFF   TLK    SSF    NCS   (Others)
      │         │      │      │       │
      │         │      │      │       │
      ▼         ▼      ▼      ▼       ▼
   _write_2da_ _write_gff_ _write_tlk_ _write_ssf_ _write_ncs_
   modification modification modification modification modification
      │         │      │      │       │
      └─────────┴──────┴──────┴───────┘
             │
      Read vanilla file
      Write to tslpatchdata/
      Generate INI section
             │
      All resource files saved
      All INI sections written
```

## 3. Writer Internal State Machine

```bash
┌────────────────┐
│   Initialize   │
│                │
│ • Create dir   │
│ • Write header │
│ • Write INI    │
│   skeleton     │
└────────┬───────┘
         │
         ▼
┌────────────────────┐
│  Write Each Mod    │ ◄─────┐
│                    │       │
│ 1. Check if        │       │
│    already written │       │
│ 2. Read vanilla    │       │
│ 3. Save to         │       │
│    tslpatchdata/   │       │
│ 4. Generate INI    │       │
│    sections        │       │
│ 5. Track install   │       │ More
│    folders         │ mods?
│ 6. Build linking   │       │
│    patches         │       │
└────────┬───────────┘       │
         │                   │
         └───────────────────┘
         │
         │ (all mods written)
         ▼
┌─────────────────────────────┐
│    Finalize                 │
│                             │
│ 1. Apply pending refs       │
│ 2. Replace 2DAMEMORY tokens │
│ 3. Rewrite INI completely  │
│ 4. Summary stats            │
└─────────────────────────────┘
```

## 4. 2DA Modification Writing Sequence

```bash
Input: Modifications2DA
       ├── sourcefile: "spells.2da"
       ├── modifiers: [
       │   AddRow2DA {
       │     cells: {"label": "NEW", "name": "32000"},
       │     store_2da: {0: RowValueRowIndex()}
       │   }
       │ ]

Process:
┌─────────────────────────────────────────┐
│ 1. Read vanilla spells.2da              │
│    (1000 rows)                          │
│                                         │
│    Installation/data/2da.bif:           │
│    spells.2da (1000 rows)               │
│                                         │
│    ───────────────────────────────────  │
│ 2. Write to tslpatchdata/               │
│                                         │
│    tslpatchdata/spells.2da              │
│    (same 1000 rows)                     │
│                                         │
│    ───────────────────────────────────  │
│ 3. Generate INI sections                │
│                                         │
│    [spells.2da]                         │
│    AddRow0=new_spell                    │
│                                         │
│    [new_spell]                          │
│    RowLabel=1001                        │
│    label=NEW                            │
│    name=32000                           │
│    2DAMEMORY0=RowIndex                  │
│    ExclusiveColumn=label                │
│                                         │
│    ───────────────────────────────────  │
│ 4. Add to install folders               │
│                                         │
│    install_folders["Override"].append   │
│    ("spells.2da")                       │
└─────────────────────────────────────────┘

Output:
├── tslpatchdata/spells.2da
│   (1000 rows - vanilla)
│
└── changes.ini sections:
    [2DAList]
    Table0=spells.2da
    
    [spells.2da]
    AddRow0=new_spell
    
    [new_spell]
    RowLabel=1001
    label=NEW
    name=32000
    2DAMEMORY0=RowIndex
    ExclusiveColumn=label
```

## 5. GFF Modification Writing Sequence

```bash
Input: ModificationsGFF
       ├── sourcefile: "creature.utc"
       ├── destination: "override"
       ├── saveas: "creature.utc"
       ├── modifiers: [
       │   ModifyFieldGFF {
       │     path: "ClassList\\0\\KnownList0\\1\\Spell",
       │     value: FieldValue2DAMemory(0)
       │   }
       │ ]

Process:
┌──────────────────────────────────────────┐
│ 1. Read vanilla creature.utc             │
│                                          │
│    Installation/override/creature.utc    │
│    (GFF with ClassList, ItemList, etc.)  │
│                                          │
│    ──────────────────────────────────── │
│ 2. Write to tslpatchdata/                │
│                                          │
│    tslpatchdata/creature.utc             │
│    (same GFF structure)                  │
│                                          │
│    ──────────────────────────────────── │
│ 3. Generate INI sections                 │
│                                          │
│    [GFFList]                             │
│    File0=creature.utc                    │
│                                          │
│    [creature.utc]                        │
│    !ReplaceFile=0                        │
│    ClassList\\0\\KnownList0\\1\\Spell    │
│      =2DAMEMORY0                         │
│                                          │
│    ──────────────────────────────────── │
│ 4. Add to install folders                │
│                                          │
│    install_folders["override"].append    │
│    ("creature.utc")                      │
└──────────────────────────────────────────┘

Output:
├── tslpatchdata/creature.utc
│   (vanilla GFF)
│
└── changes.ini sections:
    [GFFList]
    File0=creature.utc
    
    [creature.utc]
    !ReplaceFile=0
    ClassList\\0\\KnownList0\\1\\Spell=2DAMEMORY0
```

## 6. TLK Modification Writing Sequence

```
Input: ModificationsTLK
       ├── sourcefile: "dialog.tlk"
       ├── modifiers: [
       │   ModifyTLK {
       │     token_id: 0,
       │     text: "New dialog entry",
       │     sound: "sound_id",
       │     is_replacement: false
       │   },
       │   ModifyTLK {
       │     token_id: 1,
       │     text: "Another entry",
       │     is_replacement: false
       │   }
       │ ]

Process:
┌──────────────────────────────────────┐
│ 1. Create NEW TLK object             │
│                                      │
│    TLK() with 2 entries              │
│    (not reading vanilla)             │
│                                      │
│ 2. Write to tslpatchdata/            │
│                                      │
│    tslpatchdata/append.tlk           │
│    Entry 0: "New dialog entry"       │
│    Entry 1: "Another entry"          │
│                                      │
│    ──────────────────────────────── │
│ 3. Generate INI sections             │
│                                      │
│    [TLKList]                         │
│    StrRef0=0                         │
│    StrRef1=1                         │
│                                      │
│    [append.tlk]                      │
│    (Internal reference table)        │
│                                      │
│    ──────────────────────────────── │
│ 4. Add to install folders            │
│                                      │
│    install_folders["."].append       │
│    ("append.tlk")                    │
└──────────────────────────────────────┘

Output:
├── tslpatchdata/append.tlk
│   (2 new entries)
│
└── changes.ini sections:
    [TLKList]
    StrRef0=0
    StrRef1=1
    
    [append.tlk]
    (Internal structure)
```

## 7. INI Section Generation Order

```bash
1. HEADER & SETTINGS
   ├── Comments (PyKotor branding)
   └── [Settings] (FileExists, LogLevel, etc.)

2. [TLKList]
   ├── StrRef tokens
   ├── [append.tlk] section (if needed)
   └── [replace.tlk] section (if needed)

3. [InstallList]
   ├── install_folder# references
   └── [install_folder#] sections

4. [2DAList]
   ├── Table# references
   ├── [filename] sections
   └── [modifier_identifier] sections

5. [GFFList]
   ├── File# or Replace# references
   ├── [filename] sections
   └── [AddField#] sections

6. [CompileList]
   └── NCS compilation (if needed)

7. [SSFList]
   ├── File# references
   └── [filename] sections

All sections are created UPFRONT
Then content is added INCREMENTALLY
Finally the complete INI is REWRITTEN
```

## 8. Cross-File Reference Chain

```bash
For "Bastila Battle Meditation" mod:

TLK Modifications:
  ├── StrRef0: "Spell Name"
  └── StrRef1: "Spell Description"

2DA Modifications:
  ├── spells.2da AddRow:
  │   ├── label=FORCE_POWER_SPELL
  │   ├── name=StrRef0
  │   ├── spelldesc=StrRef1
  │   └── 2DAMEMORY0=RowIndex (stores spell row)
  │
  ├── visualeffects.2da AddRow:
  │   ├── label=VFX_IMP_SPELL
  │   └── 2DAMEMORY1=RowIndex (stores VFX row)
  │
  └── effecticon.2da AddRow:
      └── 2DAMEMORY2=RowIndex (stores icon row)

GFF Modifications:
  ├── p_bastilla.utc:
  │   └── ClassList\0\KnownList0\1\Spell=2DAMEMORY0
  │
  ├── p_bastilla001.utc:
  │   └── ClassList\0\KnownList0\1\Spell=2DAMEMORY0
  │
  └── p_bastilla002.utc:
      └── ClassList\0\KnownList0\1\Spell=2DAMEMORY0

┌────────────────────────────────────┐
│          Generated INI              │
├────────────────────────────────────┤
│ [TLKList]                           │
│ StrRef0=0                           │
│ StrRef1=1                           │
│                                    │
│ [append.tlk]                        │
│ 25859=0  (mapped to new entry 0)   │
│ 25860=1  (mapped to new entry 1)   │
│                                    │
│ [spells.2da]                        │
│ AddRow0=battle_meditation           │
│                                    │
│ [battle_meditation]                 │
│ label=FORCE_POWER_SPELL             │
│ name=StrRef0                        │
│ spelldesc=StrRef1                   │
│ 2DAMEMORY0=RowIndex                 │
│ ExclusiveColumn=label               │
│                                    │
│ [p_bastilla.utc]                    │
│ ClassList\0\KnownList0\1\Spell      │
│   =2DAMEMORY0                       │
│                                    │
│ [p_bastilla001.utc]                 │
│ ClassList\0\KnownList0\1\Spell      │
│   =2DAMEMORY0                       │
└────────────────────────────────────┘

Data Flow at Runtime (TSLPatcher):
  1. Load append.tlk: Get entries for StrRef0, StrRef1
  2. Load spells.2da, resolve 2DAMEMORY0 = new row index
  3. Load p_bastilla.utc, resolve 2DAMEMORY0 to row index
  4. Update Spell field with resolved row index
  5. Repeat for all creatures using same token
  6. Write all modified files to installation
```

## 9. Files on Disk After Writer Finishes

```bash
tslpatchdata/
│
├── changes.ini (100-500 KB)
│   ├── [Settings]
│   ├── [TLKList]
│   │   ├── StrRef mappings
│   │   └── [append.tlk] section
│   │
│   ├── [InstallList]
│   │   ├── install_folder references
│   │   └── [install_folder#] sections
│   │
│   ├── [2DAList]
│   │   ├── Table references
│   │   ├── [filename] sections
│   │   └── [AddRow/ChangeRow] sections
│   │
│   ├── [GFFList]
│   │   ├── File references
│   │   ├── [filename] sections
│   │   └── [AddField] sections
│   │
│   ├── [SSFList]
│   │   ├── File references
│   │   └── [filename] sections
│   │
│   └── [Comments] for readability
│
├── spells.2da (50-200 KB, vanilla)
├── appearance.2da (vanilla)
├── soundset.2da (vanilla)
├── creature.utc (50-500 KB, vanilla GFF)
├── creature2.utc (vanilla GFF)
├── character.ssf (1-10 KB, vanilla)
├── append.tlk (variable, new entries only)
├── model.mdl (if applicable)
├── model.mdx (if applicable)
├── texture.tga (if applicable)
└── [other resource files...]

Total Size: 1-50 MB depending on mod complexity

Key Properties:
✓ ALL files in root (no subdirectories)
✓ changes.ini is the configuration
✓ Resource files are vanilla versions
✓ No compiled scripts or preprocessed data
✓ Ready for TSLPatcher to read
```

This structure allows TSLPatcher to function independently without needing the diff engine or original installation!
