# KotOR 2DA File Format Documentation

This document provides a detailed description of the 2DA (Two-Dimensional Array) file format used in Knights of the Old Republic (KotOR) games. 2DA files store tabular game data in a spreadsheet-like format, containing configuration data for nearly all game systems: items, spells, creatures, skills, feats, and many other game mechanics.

## Table of Contents

- [KotOR 2DA File Format Documentation](#kotor-2da-file-format-documentation)
  - [Table of Contents](#table-of-contents)
  - [File Structure Overview](#file-structure-overview)
  - [Binary Format](#binary-format)
    - [File Header](#file-header)
    - [Column Headers](#column-headers)
    - [Row Count](#row-count)
    - [Row Labels](#row-labels)
    - [Cell Data Offsets](#cell-data-offsets)
    - [Cell Data String Table](#cell-data-string-table)
  - [Data Structure](#data-structure)
    - [TwoDA Class](#twoda-class)
    - [TwoDARow Class](#twodarow-class)
  - [Cell Value Types](#cell-value-types)
  - [Common 2DA Files](#common-2da-files)
    - [Character \& Combat](#character--combat)
    - [Items \& Properties](#items--properties)
    - [Objects \& Area](#objects--area)
    - [Visual Effects \& Animations](#visual-effects--animations)
    - [Progression Tables](#progression-tables)
    - [Name Generation](#name-generation)
  - [Implementation Details](#implementation-details)

---

## File Structure Overview

2DA files can be stored in two formats:

- **Binary Format** (`.2da`): Compact binary representation used by the game engine

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/twoda/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/twoda/)

---

## Binary Format

The binary format (version "V2.b") is the compact representation used by the game engine.

### File Header

The file header is 9 bytes in size:

| Name         | Type    | Offset | Size | Description                                    |
| ------------ | ------- | ------ | ---- | ---------------------------------------------- |
| File Type    | char[4] | 0      | 4    | Always `"2DA "` (space-padded)                 |
| File Version | char[4] | 4      | 4    | Always `"V2.b"` for binary format              |
| Line Break   | uint8   | 8      | 1    | Newline character (`\n`, value `0x0A`)        |

**Reference**: [`vendor/reone/src/libs/resource/format/2dareader.cpp:26-80`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/2dareader.cpp#L26-L80)

### Column Headers

Column headers immediately follow the header, terminated by a null byte:

| Name            | Type    | Description                                                      |
| --------------- | ------- | ---------------------------------------------------------------- |
| Column Headers  | char[]  | Tab-separated column names (e.g., `"label\tname\tdescription"`) |
| Null Terminator | uint8   | Single null byte (`\0`) marking end of headers                   |

**Reference**: [`vendor/TSLPatcher/lib/site/Bioware/TwoDA.pm:200-350`](https://github.com/th3w1zard1/TSLPatcher/blob/master/lib/site/Bioware/TwoDA.pm#L200-L350)

### Row Count

| Name      | Type    | Offset | Size | Description                    |
| --------- | ------- | ------ | ---- | ------------------------------ |
| Row Count | uint32  | varies | 4    | Number of data rows in the file |

### Row Labels

Row labels immediately follow the row count:

| Name       | Type    | Description                                                      |
| ---------- | ------- | ---------------------------------------------------------------- |
| Row Labels | char[]  | Tab-separated row labels (one per row, typically numeric)       |

Each row label is read as a tab-terminated string (tab character `0x09`). Row labels are usually numeric ("0", "1", "2"...) but can be arbitrary strings.

**Important**: The row label list is **not** terminated by a null byte (`0x00`). The reader must consume exactly `row_count` labels based on the count field. This differs from the column headers which do have a null terminator.

### Cell Data Offsets

After row labels, cell data offsets are stored:

| Name            | Type     | Size | Description                                                      |
| --------------- | -------- | ---- | ---------------------------------------------------------------- |
| Cell Offsets    | uint16[] | 2×N  | Array of offsets into cell data string table (N = row_count × column_count) |
| Cell Data Size  | uint16   | 2    | Total size of cell data string table in bytes                    |

Each cell has a 16-bit offset pointing to its string value in the cell data string table. Offsets are stored row-major order (all cells of row 0, then all cells of row 1, etc.).

**Reference**: [`vendor/Kotor.NET/Kotor.NET/Formats/Kotor2DA/TwoDABinaryStructure.cs:19-63`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/Kotor2DA/TwoDABinaryStructure.cs#L19-L63)

### Cell Data String Table

The cell data string table contains all cell values as null-terminated strings:

| Name         | Type   | Description                                                      |
| ------------ | ------ | ---------------------------------------------------------------- |
| Cell Strings | char[] | Null-terminated strings, deduplicated (same value shares offset) |

Blank cells are typically stored as empty strings (`""`) or the string `"****"`. The string table is deduplicated - multiple cells with the same value share the same offset.

---

## Data Structure

### TwoDA Class

The `TwoDA` class represents a complete 2DA file in memory:

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/twoda/twoda_data.py:77-119`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/twoda/twoda_data.py#L77-L119)

**Attributes:**

- `_rows`: List of dictionaries, each mapping column headers to cell values
- `_headers`: List of column header names (case-sensitive, typically lowercase)
- `_labels`: List of row labels (usually numeric strings like "0", "1", "2"...)

**Methods:**

- `get_cell(row_index, column_header)`: Get cell value by row index and column header
- `set_cell(row_index, column_header, value)`: Set cell value
- `get_column(header)`: Get all values for a column
- `add_row(label)`: Add a new row
- `add_column(header)`: Add a new column

### TwoDARow Class

The `TwoDARow` class provides a convenient interface for accessing row data:

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/twoda/twoda_data.py:850-950`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/twoda/twoda_data.py#L850-L950)

**Attributes:**

- `label`: Row label string
- `cells`: Dictionary mapping column headers to cell values

---

## Cell Value Types

All cell values are stored as strings in the 2DA file, but are interpreted as different types by the game engine:

- **Integers**: Numeric strings parsed as `int32` - used for numeric identifiers, counts, and enumerated values
- **Floats**: Decimal strings parsed as `float` - used for calculations like damage multipliers, timers, and percentages
- **ResRefs**: Resource references (max 16 characters, no extension) - point to other game resources like models, textures, or scripts
- **StrRefs**: String references into `dialog.tlk` (typically negative values like `-1` indicate no reference) - used for localized text display
- **Boolean**: `"0"` or `"1"` (sometimes `"TRUE"`/`"FALSE"`) - control feature flags and settings
- **Empty Cells**: Represented as `"****"` in both ASCII and binary formats - treated as null/undefined by the engine

The game engine parses cell values based on context and expected data type for each column. For example, the `appearance.2da` file uses integers for model indices, ResRefs for texture names, and StrRefs for race names.

---

## Common 2DA Files

Some commonly used 2DA files in KotOR:

### Character & Combat

- `appearance.2da`: Character appearance definitions - maps appearance IDs to model ResRefs, textures, and race associations
- `baseitems.2da`: Base item type definitions - defines weapon types, damage, item categories, and equipment slots
- `classes.2da`: Character class definitions - specifies class names, hit dice, skill point progression, and feat tables
- `feat.2da`: Feat definitions - lists all feats with names, descriptions, prerequisites, and icon references
- `skills.2da`: Skill definitions - skill names, descriptions, and which classes can use them
- `spells.2da`: Spell/Force power definitions - power costs, targeting modes, icons, and visual effects

### Items & Properties

- `iprp_feats.2da`: Item property feat definitions - maps item property values to feat bonuses
- `iprp_spells.2da`: Item property spell definitions - defines on-use and on-hit spell effects for items
- `iprp_ammocost.2da`: Ammunition cost per shot
- `iprp_damagecost.2da`: Damage bonus cost calculations
- `itemprops.2da`: Master item property type table

### Objects & Area

- `placeables.2da`: Placeable object definitions - container models, usable objects, and their properties
- `doortypes.2da`: Door models and animations
- `soundset.2da`: Character voice set assignments

### Visual Effects & Animations

- `visualeffects.2da`: Visual effect definitions - particle effects, impact effects, and durations
- `portraits.2da`: Character portrait assignments for selection screens
- `heads.2da`: Player and NPC head model definitions

### Progression Tables

- `classpowergain.2da`: Force power progression by class and level
- `cls_atk_*.2da`: Base attack bonus tables for each class
- `cls_savthr_*.2da`: Saving throw progression tables

### Name Generation

- `humanfirst.2da`, `humanlast.2da`: Random name tables for character creation
- Other `*first.2da` and `*last.2da` files for alien species

2DA files are the primary configuration mechanism for KotOR's game rules and content. Nearly every game system references at least one 2DA file for its behavior.

---

## Implementation Details

**Binary Reading**: [`Libraries/PyKotor/src/pykotor/resource/formats/twoda/io_twoda.py:12-106`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/twoda/io_twoda.py#L12-L106)

**Binary Writing**: [`Libraries/PyKotor/src/pykotor/resource/formats/twoda/io_twoda.py:109-174`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/twoda/io_twoda.py#L109-L174)

**ASCII Reading**: [`Libraries/PyKotor/src/pykotor/resource/formats/twoda/io_twoda_csv.py`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/twoda/io_twoda_csv.py)

**ASCII Writing**: [`Libraries/PyKotor/src/pykotor/resource/formats/twoda/io_twoda_csv.py`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/twoda/io_twoda_csv.py)

---

This documentation aims to provide a comprehensive overview of the KotOR 2DA file format, focusing on the detailed file structure and data formats used within the games.
