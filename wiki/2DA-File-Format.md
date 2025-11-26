# KotOR 2DA File Format Documentation

This document provides a detailed description of the 2DA (Two-Dimensional Array) file format used in **Knights of the Old Republic (KotOR)** and **Knights of the Old Republic II: The Sith Lords (KotOR 2)**. 2DA files store tabular game data in a spreadsheet-like format, containing configuration data for nearly all game systems: items, Force powers, creatures, skills, feats, and many other game mechanics.

**For mod developers:** To modify 2DA files in your mods, see the [TSLPatcher 2DAList Syntax Guide](TSLPatcher-2DAList-Syntax). For general modding information, see [HoloPatcher README for Mod Developers](HoloPatcher-README-for-mod-developers.).

**Related formats:** 2DA files are often referenced by [GFF files](GFF-File-Format) (such as UTC, UTI, UTP templates) and may contain references to [TLK files](TLK-File-Format) for text strings.

**Important**: While the 2DA file format structure is shared across BioWare's Aurora engine games (including Neverwinter Nights, Dragon Age, and Jade Empire), this documentation focuses exclusively on KotOR and KotOR 2. All 2DA file examples, column structures, and engine usage descriptions are specific to these games. References to vendor implementations are marked as either KotOR-specific or generic Aurora engine code (shared format).

## Table of Contents

- [KotOR 2DA File Format Documentation](#kotor-2da-file-format-documentation)
  - [Table of Contents](#table-of-contents)
  - [File Structure Overview](#file-structure-overview)
  - [Format](#format)
    - [Cell Data Offsets](#cell-data-offsets)
    - [Cell Data String Table](#cell-data-string-table)
    - [Column Headers](#column-headers)
    - [File Header](#file-header)
    - [Row Count](#row-count)
    - [Row Labels](#row-labels)
  - [Data Structure](#data-structure)
    - [TwoDA Class](#twoda-class)
    - [TwoDARow Class](#twodarow-class)
  - [Cell Value Types](#cell-value-types)
  - [Confirmed Engine Usage](#confirmed-engine-usage)
  - [Known 2DA Files](#known-2da-files)
  - [Character \& Combat 2DA Files](#character--combat-2da-files)
    - [appearance.2da](#appearance2da)
    - [baseitems.2da](#baseitems2da)
    - [classes.2da](#classes2da)
    - [feat.2da](#feat2da)
    - [skills.2da](#skills2da)
    - [spells.2da](#spells2da)
  - [Items \& Properties 2DA Files](#items--properties-2da-files)
    - [iprp\_ammocost.2da](#iprp_ammocost2da)
    - [iprp\_damagecost.2da](#iprp_damagecost2da)
    - [iprp\_feats.2da](#iprp_feats2da)
    - [iprp\_spells.2da](#iprp_spells2da)
    - [itemprops.2da](#itemprops2da)
  - [Objects \& Area 2DA Files](#objects--area-2da-files)
    - [doortypes.2da](#doortypes2da)
    - [genericdoors.2da](#genericdoors2da)
    - [placeables.2da](#placeables2da)
    - [soundset.2da](#soundset2da)
  - [Visual Effects \& Animations 2DA Files](#visual-effects--animations-2da-files)
    - [heads.2da](#heads2da)
    - [portraits.2da](#portraits2da)
    - [visualeffects.2da](#visualeffects2da)
  - [Progression Tables 2DA Files](#progression-tables-2da-files)
    - [classpowergain.2da](#classpowergain2da)
    - [cls\_atk\_\*.2da](#cls_atk_2da)
    - [cls\_savthr\_\*.2da](#cls_savthr_2da)
  - [Name Generation 2DA Files](#name-generation-2da-files)
    - [humanfirst.2da](#humanfirst2da)
    - [humanlast.2da](#humanlast2da)
    - [Other Name Generation Files](#other-name-generation-files)
  - [Additional 2DA Files](#additional-2da-files)
    - [ambientmusic.2da](#ambientmusic2da)
    - [ambientsound.2da](#ambientsound2da)
    - [ammunitiontypes.2da](#ammunitiontypes2da)
    - [animations.2da](#animations2da)
    - [bodybag.2da](#bodybag2da)
    - [camerastyle.2da](#camerastyle2da)
    - [combatanimations.2da](#combatanimations2da)
    - [creaturespeed.2da](#creaturespeed2da)
    - [cursors.2da](#cursors2da)
    - [dialoganimations.2da](#dialoganimations2da)
    - [emotion.2da](#emotion2da)
    - [encdifficulty.2da](#encdifficulty2da)
    - [exptable.2da](#exptable2da)
    - [facialanim.2da](#facialanim2da)
    - [footstepsounds.2da](#footstepsounds2da)
    - [forceshields.2da](#forceshields2da)
    - [gender.2da](#gender2da)
    - [globalcat.2da](#globalcat2da)
    - [guisounds.2da](#guisounds2da)
    - [itempropdef.2da](#itempropdef2da)
    - [loadscreenhints.2da](#loadscreenhints2da)
    - [modulesave.2da](#modulesave2da)
    - [placeableobjsnds.2da](#placeableobjsnds2da)
    - [planetary.2da](#planetary2da)
    - [plot.2da](#plot2da)
    - [prioritygroups.2da](#prioritygroups2da)
    - [racialtypes.2da](#racialtypes2da)
    - [ranges.2da](#ranges2da)
    - [regeneration.2da](#regeneration2da)
    - [repute.2da](#repute2da)
    - [subrace.2da](#subrace2da)
    - [surfacemat.2da](#surfacemat2da)
    - [tilecolor.2da](#tilecolor2da)
    - [traps.2da](#traps2da)
    - [tutorial.2da](#tutorial2da)
    - [upgrade.2da](#upgrade2da)
    - [videoeffects.2da](#videoeffects2da)
    - [weaponsounds.2da](#weaponsounds2da)
  - [Item Property Parameter \& Cost Tables 2DA Files](#item-property-parameter--cost-tables-2da-files)
    - [acbonus.2da](#acbonus2da)
    - [actions.2da](#actions2da)
    - [ai\_styles.2da](#ai_styles2da)
    - [aiscripts.2da](#aiscripts2da)
    - [aliensound.2da](#aliensound2da)
    - [alienvo.2da](#alienvo2da)
    - [appearancesndset.2da](#appearancesndset2da)
    - [areaeffects.2da](#areaeffects2da)
    - [bindablekeys.2da](#bindablekeys2da)
    - [bodyvariation.2da](#bodyvariation2da)
    - [chargenclothes.2da](#chargenclothes2da)
    - [creaturesize.2da](#creaturesize2da)
    - [credits.2da](#credits2da)
    - [crtemplates.2da](#crtemplates2da)
    - [difficultyopt.2da](#difficultyopt2da)
    - [disease.2da](#disease2da)
    - [droiddischarge.2da](#droiddischarge2da)
    - [effecticon.2da](#effecticon2da)
    - [environment.2da](#environment2da)
    - [featgain.2da](#featgain2da)
    - [feedbacktext.2da](#feedbacktext2da)
    - [fractionalcr.2da](#fractionalcr2da)
    - [gamespyrooms.2da](#gamespyrooms2da)
    - [grenadesnd.2da](#grenadesnd2da)
    - [hen\_companion.2da](#hen_companion2da)
    - [hen\_familiar.2da](#hen_familiar2da)
    - [inventorysnds.2da](#inventorysnds2da)
    - [iprp\_abilities.2da](#iprp_abilities2da)
    - [iprp\_acmodtype.2da](#iprp_acmodtype2da)
    - [iprp\_aligngrp.2da](#iprp_aligngrp2da)
    - [iprp\_ammotype.2da](#iprp_ammotype2da)
    - [iprp\_attackmod.2da](#iprp_attackmod2da)
    - [iprp\_bonusfeat.2da](#iprp_bonusfeat2da)
    - [iprp\_combatdam.2da](#iprp_combatdam2da)
    - [iprp\_costtable.2da](#iprp_costtable2da)
    - [iprp\_damagered.2da](#iprp_damagered2da)
    - [iprp\_damagetype.2da](#iprp_damagetype2da)
    - [iprp\_damagevs.2da](#iprp_damagevs2da)
    - [iprp\_immunity.2da](#iprp_immunity2da)
    - [iprp\_lightcol.2da](#iprp_lightcol2da)
    - [iprp\_monstdam.2da](#iprp_monstdam2da)
    - [iprp\_mosterhit.2da](#iprp_mosterhit2da)
    - [iprp\_onhit.2da](#iprp_onhit2da)
    - [iprp\_paramtable.2da](#iprp_paramtable2da)
    - [iprp\_protection.2da](#iprp_protection2da)
    - [iprp\_saveelement.2da](#iprp_saveelement2da)
    - [iprp\_savingthrow.2da](#iprp_savingthrow2da)
    - [iprp\_skillcost.2da](#iprp_skillcost2da)
    - [iprp\_spellres.2da](#iprp_spellres2da)
    - [iprp\_traptype.2da](#iprp_traptype2da)
    - [iprp\_walk.2da](#iprp_walk2da)
    - [iprp\_weightinc.2da](#iprp_weightinc2da)
    - [itempropsdef.2da](#itempropsdef2da)
    - [keymap.2da](#keymap2da)
    - [loadscreens.2da](#loadscreens2da)
    - [masterfeats.2da](#masterfeats2da)
    - [merchants.2da](#merchants2da)
    - [minglobalrim.2da](#minglobalrim2da)
    - [movies.2da](#movies2da)
    - [musictable.2da](#musictable2da)
    - [palette.2da](#palette2da)
    - [pazaakdecks.2da](#pazaakdecks2da)
    - [phenotype.2da](#phenotype2da)
    - [poison.2da](#poison2da)
    - [rumble.2da](#rumble2da)
    - [soundeax.2da](#soundeax2da)
    - [stringtokens.2da](#stringtokens2da)
    - [texpacks.2da](#texpacks2da)
    - [textures.2da](#textures2da)
    - [tutorial\_old.2da](#tutorial_old2da)
    - [upcrystals.2da](#upcrystals2da)
    - [videoquality.2da](#videoquality2da)
    - [xptable.2da](#xptable2da)
  - [Implementation Details](#implementation-details)
    - [PyKotor Implementation](#pykotor-implementation)
    - [Vendor Implementations](#vendor-implementations)

---

## File Structure Overview

2DA files store tabular game data in a compact format used by the KotOR game engine. Files use version "V2.b" and have the `.2da` extension.

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/twoda/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/twoda/)

**Reference**: [`vendor/kotor/docs/2da.md`](https://github.com/th3w1zard1/kotor/blob/master/docs/2da.md) - Basic format structure

---

## Format

The 2DA file format (version "V2.b") is the representation used by the game engine.

### File Header

The file header is 9 bytes in size:

| Name         | Type    | Offset | Size | Description                                    |
| ------------ | ------- | ------ | ---- | ---------------------------------------------- |
| File Type    | char[4] | 0      | 4    | Always `"2DA "` (space-padded) or `"2DA\t"` (tab-padded) |
| File Version | char[4] | 4      | 4    | Always `"V2.b"`              |
| Line Break   | uint8   | 8      | 1    | Newline character (`\n`, value `0x0A`)        |

The file type can be either `"2DA "` (space-padded) or `"2DA\t"` (tab-padded). Both are valid and accepted by the game engine.

**References**:

- [`vendor/reone/src/libs/resource/format/2dareader.cpp:29-32`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/2dareader.cpp#L29-L32) - KotOR-specific header validation
- [`vendor/xoreos/src/aurora/2dafile.cpp:48-51`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/2dafile.cpp#L48-L51) - Generic Aurora engine header constants (format shared across KotOR and other Aurora games)
- [`vendor/KotOR-Unity/Assets/Scripts/FileObjects/2DAObject.cs:25-32`](https://github.com/th3w1zard1/KotOR-Unity/blob/master/Assets/Scripts/FileObjects/2DAObject.cs#L25-L32) - KotOR-specific header reading

### Column Headers

Column headers immediately follow the header, terminated by a null byte:

| Name            | Type    | Description                                                      |
| --------------- | ------- | ---------------------------------------------------------------- |
| Column Headers  | char[]  | [Tab-separated](https://en.wikipedia.org/wiki/Tab-separated_values) column names (e.g., `"label\tname\tdescription"`) |
| Null Terminator | uint8   | Single [null byte](https://en.wikipedia.org/wiki/Null-terminated_string) (`\0`) marking end of headers                   |

Each column name is terminated by a tab character (`0x09`). The entire header list is terminated by a [null byte](https://en.wikipedia.org/wiki/Null-terminated_string) (`0x00`). Column names are case-sensitive and typically lowercase in KotOR files.

**References**:

- [`vendor/reone/src/libs/resource/format/2dareader.cpp:72-89`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/2dareader.cpp#L72-L89) - KotOR-specific token reading with tab separator
- [`vendor/xoreos/src/aurora/2dafile.cpp:260-275`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/2dafile.cpp#L260-L275) - Generic Aurora engine header reading (format shared across KotOR and other Aurora games)
- [`vendor/KotOR-Unity/Assets/Scripts/FileObjects/2DAObject.cs:36-48`](https://github.com/th3w1zard1/KotOR-Unity/blob/master/Assets/Scripts/FileObjects/2DAObject.cs#L36-L48) - KotOR-specific column header parsing
- [`vendor/kotor/docs/2da.md:32-37`](https://github.com/th3w1zard1/kotor/blob/master/docs/2da.md#L32-L37) - KotOR-specific column structure

### Row Count

| Name      | Type    | Offset | Size | Description                    |
| --------- | ------- | ------ | ---- | ------------------------------ |
| Row Count | uint32  | varies | 4    | Number of data rows in the file ([little-endian](https://en.wikipedia.org/wiki/Endianness)) |

The row count is stored as a 32-bit unsigned integer in [little-endian](https://en.wikipedia.org/wiki/Endianness) byte order. This value determines how many row labels and data rows follow.

**References**:

- [`vendor/reone/src/libs/resource/format/2dareader.cpp:34`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/2dareader.cpp#L34) - KotOR-specific row count reading
- [`vendor/xoreos/src/aurora/2dafile.cpp:284`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/2dafile.cpp#L284) - Generic Aurora engine row count reading (format shared across KotOR and other Aurora games)
- [`vendor/kotor/docs/2da.md:39-44`](https://github.com/th3w1zard1/kotor/blob/master/docs/2da.md#L39-L44) - KotOR-specific row indices structure

### Row Labels

Row labels immediately follow the row count:

| Name       | Type    | Description                                                      |
| ---------- | ------- | ---------------------------------------------------------------- |
| Row Labels | char[]  | [Tab-separated](https://en.wikipedia.org/wiki/Tab-separated_values) row labels (one per row, typically numeric)       |

Each row label is read as a tab-terminated string (tab character `0x09`). Row labels are usually numeric ("0", "1", "2"...) but can be arbitrary strings.

**Important**: The row label list is **not** terminated by a [null byte](https://en.wikipedia.org/wiki/Null-terminated_string) (`0x00`). The reader must consume exactly `row_count` labels based on the count field. This differs from the column headers which do have a [null terminator](https://en.wikipedia.org/wiki/Null-terminated_string). The row labels are primarily for human readability and editing tools - the actual row indexing in the game engine is based on position, not label value.

**References**:

- [`vendor/reone/src/libs/resource/format/2dareader.cpp:35`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/2dareader.cpp#L35) - KotOR-specific row label reading (skipped in reone)
- [`vendor/xoreos/src/aurora/2dafile.cpp:277-294`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/2dafile.cpp#L277-L294) - Generic Aurora engine row label skipping implementation (format shared across KotOR and other Aurora games)
- [`vendor/KotOR-Unity/Assets/Scripts/FileObjects/2DAObject.cs:56-70`](https://github.com/th3w1zard1/KotOR-Unity/blob/master/Assets/Scripts/FileObjects/2DAObject.cs#L56-L70) - KotOR-specific row label parsing
- [`vendor/kotor/docs/2da.md:39-46`](https://github.com/th3w1zard1/kotor/blob/master/docs/2da.md#L39-L46) - KotOR-specific row indices structure and termination note

### Cell Data Offsets

After row labels, cell data offsets are stored:

| Name            | Type     | Size | Description                                                      |
| --------------- | -------- | ---- | ---------------------------------------------------------------- |
| Cell Offsets    | uint16[] | 2×N  | [Array](https://en.wikipedia.org/wiki/Array_data_structure) of offsets into cell data string table (N = row_count × column_count, [little-endian](https://en.wikipedia.org/wiki/Endianness)) |
| Cell Data Size  | uint16   | 2    | Total size of cell data string table in bytes ([little-endian](https://en.wikipedia.org/wiki/Endianness))   |

Each cell has a 16-bit unsigned integer offset ([little-endian](https://en.wikipedia.org/wiki/Endianness)) pointing to its string value in the cell data string table. Offsets are stored in [row-major order](https://en.wikipedia.org/wiki/Row-_and_column-major_order) (all cells of row 0, then all cells of row 1, etc.). The cell data size field immediately follows the offset array and precedes the actual cell data.

**Important**: The offsets are relative to the start of the cell data string table (which begins immediately after the `cell_data_size` field). Multiple cells can share the same offset value if they contain identical strings, enabling data [deduplication](https://en.wikipedia.org/wiki/Data_deduplication).

**References**:

- [`vendor/reone/src/libs/resource/format/2dareader.cpp:47-52`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/2dareader.cpp#L47-L52) - KotOR-specific offset array reading
- [`vendor/xoreos/src/aurora/2dafile.cpp:314-317`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/2dafile.cpp#L314-L317) - Generic Aurora engine offset reading (format shared across KotOR and other Aurora games)
- [`vendor/KotOR-Unity/Assets/Scripts/FileObjects/2DAObject.cs:72-83`](https://github.com/th3w1zard1/KotOR-Unity/blob/master/Assets/Scripts/FileObjects/2DAObject.cs#L72-L83) - KotOR-specific offset array parsing
- [`vendor/reone/src/libs/resource/format/2dawriter.cpp:63-89`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/2dawriter.cpp#L63-L89) - KotOR-specific offset [deduplication](https://en.wikipedia.org/wiki/Data_deduplication) during writing
- [`vendor/kotor/docs/2da.md:48-54`](https://github.com/th3w1zard1/kotor/blob/master/docs/2da.md#L48-L54) - KotOR-specific cell offsets structure

### Cell Data String Table

The cell data string table contains all cell values as null-terminated strings:

| Name         | Type   | Description                                                      |
| ------------ | ------ | ---------------------------------------------------------------- |
| Cell Strings | char[] | [Null-terminated](https://en.wikipedia.org/wiki/Null-terminated_string) strings, [deduplicated](https://en.wikipedia.org/wiki/Data_deduplication) (same value shares offset) |

The cell data string table begins immediately after the `cell_data_size` field. Each string is [null-terminated](https://en.wikipedia.org/wiki/Null-terminated_string) (`0x00`). Blank or empty cells are typically stored as empty strings (immediately [null-terminated](https://en.wikipedia.org/wiki/Null-terminated_string)) or the string `"****"`. The string table is [deduplicated](https://en.wikipedia.org/wiki/Data_deduplication) - multiple cells with the same value share the same offset, reducing file size.

**Reading Process**: For each cell, the reader:

1. Retrieves the 16-bit offset from the offset array (indexed by `row_index × column_count + column_index`)
2. Seeks to `cell_data_start_position + offset`
3. Reads a [null-terminated](https://en.wikipedia.org/wiki/Null-terminated_string) string from that position

**References**:

- [`vendor/reone/src/libs/resource/format/2dareader.cpp:54-65`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/2dareader.cpp#L54-L65) - KotOR-specific cell data reading with offset calculation
- [`vendor/xoreos/src/aurora/2dafile.cpp:319-335`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/2dafile.cpp#L319-L335) - Generic Aurora engine cell data reading (format shared across KotOR and other Aurora games, with KotOR-specific comment at line 545)
- [`vendor/KotOR-Unity/Assets/Scripts/FileObjects/2DAObject.cs:85-100`](https://github.com/th3w1zard1/KotOR-Unity/blob/master/Assets/Scripts/FileObjects/2DAObject.cs#L85-L100) - KotOR-specific cell data reading loop
- [`vendor/xoreos/src/aurora/2dafile.cpp:63-64`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/2dafile.cpp#L63-L64) - Generic Aurora engine empty cell representation (`"****"`, shared across KotOR and other Aurora games)
- [`vendor/kotor/docs/2da.md:57-64`](https://github.com/th3w1zard1/kotor/blob/master/docs/2da.md#L57-L64) - KotOR-specific cell data structure

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

- **Integers**: Numeric strings parsed as [`int32`](https://en.wikipedia.org/wiki/Integer_(computer_science)) - used for numeric identifiers, counts, and enumerated values
- **Floats**: Decimal strings parsed as [`float`](https://en.wikipedia.org/wiki/Single-precision_floating-point_format) - used for calculations like damage multipliers, timers, and percentages
- **ResRefs**: Resource references (max 16 characters, no extension) - point to other game resources like models, textures, or scripts
- **StrRefs**: String references into `dialog.tlk` (typically negative values like `-1` indicate no reference) - used for localized text display
- **Boolean**: `"0"` or `"1"` (sometimes `"TRUE"`/`"FALSE"`) - control feature flags and settings
- **Empty Cells**: Represented as `"****"` - treated as null/undefined by the engine

The game engine parses cell values based on context and expected data type for each column. For example, the `appearance.2da` file uses integers for model indices, ResRefs for texture names, and StrRefs for race names.

---

## Confirmed Engine Usage

The following 2DA files have been confirmed to be actively loaded and used by the KotOR game engine through reverse engineering analysis of the game binaries and engine reimplementations (reone, xoreos):

**Core Game Systems:**

- `classes.2da` - Class definitions and progression
- `feat.2da` - Feat definitions
- `featgain.2da` - Feat gain tables (referenced in engine error messages)
- `skills.2da` - Skill definitions
- `spells.2da` - Force power/spell definitions

**Character & Appearance:**

- `appearance.2da` - Creature appearance definitions
- `racialtypes.2da` - Race definitions
- `subrace.2da` - Subrace definitions
- `gender.2da` - Gender definitions
- `portraits.2da` - Portrait definitions
- `heads.2da` - Head appearance definitions
- `creaturespeed.2da` - Creature movement speed definitions

**Items & Equipment:**

- `baseitems.2da` - Base item type definitions

**Objects & Areas:**

- `placeables.2da` - Placeable object definitions
- `genericdoors.2da` / `doortypes.2da` - Door type definitions
- `traps.2da` - Trap definitions
- `encdifficulty.2da` - Encounter difficulty definitions

**Audio & Visual:**

- `guisounds.2da` - GUI sound definitions
- `footstepsounds.2da` - Footstep sound definitions
- `camerastyle.2da` - Camera style definitions
- `surfacemat.2da` - Surface material definitions

**Factions & Reputation:**

- `repute.2da` - Faction/reputation definitions

**Note:** Many other 2DA files documented below may be remnants from Neverwinter Nights (NWN) or may be used in ways not yet identified through reverse engineering. The files listed above are confirmed to be actively loaded and referenced by the game engine during normal gameplay.

## Known 2DA Files

This section documents all known 2DA files used in KotOR and KotOR 2, organized by category. Each entry includes engine usage, column definitions, and data structure details.

---

## Character & Combat 2DA Files

### appearance.2da

See [appearance.2da](2DA-appearance) for detailed documentation.

### baseitems.2da

See [baseitems.2da](2DA-baseitems) for detailed documentation.

### classes.2da

See [classes.2da](2DA-classes) for detailed documentation.

### feat.2da

See [feat.2da](2DA-feat) for detailed documentation.

### skills.2da

See [skills.2da](2DA-skills) for detailed documentation.

### spells.2da

See [spells.2da](2DA-spells) for detailed documentation.

## Items & Properties 2DA Files

### itemprops.2da

See [itemprops.2da](2DA-itemprops) for detailed documentation.

### iprp_feats.2da

See [iprp_feats.2da](2DA-iprp_feats) for detailed documentation.

### iprp_spells.2da

See [iprp_spells.2da](2DA-iprp_spells) for detailed documentation.

### iprp_ammocost.2da

See [iprp_ammocost.2da](2DA-iprp_ammocost) for detailed documentation.

### iprp_damagecost.2da

See [iprp_damagecost.2da](2DA-iprp_damagecost) for detailed documentation.

## Objects & Area 2DA Files

### placeables.2da

See [placeables.2da](2DA-placeables) for detailed documentation.

### genericdoors.2da

See [genericdoors.2da](2DA-genericdoors) for detailed documentation.

### doortypes.2da

See [doortypes.2da](2DA-doortypes) for detailed documentation.

### soundset.2da

See [soundset.2da](2DA-soundset) for detailed documentation.

## Visual Effects & Animations 2DA Files

### visualeffects.2da

See [visualeffects.2da](2DA-visualeffects) for detailed documentation.

### portraits.2da

See [portraits.2da](2DA-portraits) for detailed documentation.

### heads.2da

See [heads.2da](2DA-heads) for detailed documentation.

## Progression Tables 2DA Files

### classpowergain.2da

See [classpowergain.2da](2DA-classpowergain) for detailed documentation.

### cls_atk_*.2da

See [cls_atk_*.2da](cls_atk__pattern_pattern) for detailed documentation.

### cls_savthr_*.2da

See [cls_savthr_*.2da](cls_savthr__pattern_pattern) for detailed documentation.

## Name Generation 2DA Files

### humanfirst.2da

See [humanfirst.2da](2DA-humanfirst) for detailed documentation.

### humanlast.2da

See [humanlast.2da](2DA-humanlast) for detailed documentation.

### Other Name Generation Files

Similar name generation files exist for other species:

- `twilekfirst.2da` / `twileklast.2da`: Twi'lek names
- `zabrakfirst.2da` / `zabraklast.2da`: Zabrak names
- `wookieefirst.2da` / `wookieelast.2da`: Wookiee names
- `rodianfirst.2da` / `rodianlast.2da`: Rodian names
- `droidfirst.2da` / `droidlast.2da`: Droid names
- `catharfirst.2da` / `catharlast.2da`: Cathar names (KotOR 2)
- `miralukafirst.2da` / `miralukalast.2da`: Miraluka names (KotOR 2)
- `miracianfirst.2da` / `miracianlast.2da`: Miraluka names (KotOR 2, alternate spelling)

---

## Additional 2DA Files

### ambientmusic.2da

See [ambientmusic.2da](2DA-ambientmusic) for detailed documentation.

### ambientsound.2da

See [ambientsound.2da](2DA-ambientsound) for detailed documentation.

### ammunitiontypes.2da

See [ammunitiontypes.2da](2DA-ammunitiontypes) for detailed documentation.

### camerastyle.2da

See [camerastyle.2da](2DA-camerastyle) for detailed documentation.

### footstepsounds.2da

See [footstepsounds.2da](2DA-footstepsounds) for detailed documentation.

### prioritygroups.2da

See [prioritygroups.2da](2DA-prioritygroups) for detailed documentation.

### repute.2da

See [repute.2da](2DA-repute) for detailed documentation.

### surfacemat.2da

See [surfacemat.2da](2DA-surfacemat) for detailed documentation.

### loadscreenhints.2da

See [loadscreenhints.2da](2DA-loadscreenhints) for detailed documentation.

### bodybag.2da

See [bodybag.2da](2DA-bodybag) for detailed documentation.

### ranges.2da

See [ranges.2da](2DA-ranges) for detailed documentation.

### regeneration.2da

See [regeneration.2da](2DA-regeneration) for detailed documentation.

### animations.2da

See [animations.2da](2DA-animations) for detailed documentation.

### combatanimations.2da

See [combatanimations.2da](2DA-combatanimations) for detailed documentation.

### weaponsounds.2da

See [weaponsounds.2da](2DA-weaponsounds) for detailed documentation.

### placeableobjsnds.2da

See [placeableobjsnds.2da](2DA-placeableobjsnds) for detailed documentation.

### creaturespeed.2da

See [creaturespeed.2da](2DA-creaturespeed) for detailed documentation.

### exptable.2da

See [exptable.2da](2DA-exptable) for detailed documentation.

### guisounds.2da

See [guisounds.2da](2DA-guisounds) for detailed documentation.

### dialoganimations.2da

See [dialoganimations.2da](2DA-dialoganimations) for detailed documentation.

### tilecolor.2da

See [tilecolor.2da](2DA-tilecolor) for detailed documentation.

### forceshields.2da

See [forceshields.2da](2DA-forceshields) for detailed documentation.

### plot.2da

See [plot.2da](2DA-plot) for detailed documentation.

### traps.2da

See [traps.2da](2DA-traps) for detailed documentation.

### modulesave.2da

See [modulesave.2da](2DA-modulesave) for detailed documentation.

### tutorial.2da

See [tutorial.2da](2DA-tutorial) for detailed documentation.

### globalcat.2da

See [globalcat.2da](2DA-globalcat) for detailed documentation.

### subrace.2da

See [subrace.2da](2DA-subrace) for detailed documentation.

### gender.2da

See [gender.2da](2DA-gender) for detailed documentation.

### racialtypes.2da

See [racialtypes.2da](2DA-racialtypes) for detailed documentation.

### upgrade.2da

See [upgrade.2da](2DA-upgrade) for detailed documentation.

### encdifficulty.2da

See [encdifficulty.2da](2DA-encdifficulty) for detailed documentation.

### itempropdef.2da

See [itempropdef.2da](2DA-itempropdef) for detailed documentation.

### emotion.2da

See [emotion.2da](2DA-emotion) for detailed documentation.

### facialanim.2da

See [facialanim.2da](2DA-facialanim) for detailed documentation.

### videoeffects.2da

See [videoeffects.2da](2DA-videoeffects) for detailed documentation.

### planetary.2da

See [planetary.2da](2DA-planetary) for detailed documentation.

### cursors.2da

See [cursors.2da](2DA-cursors) for detailed documentation.

## Item Property Parameter & Cost Tables 2DA Files

The following 2DA files are used for item property parameter and cost calculations:

### iprp_paramtable.2da

See [iprp_paramtable.2da](2DA-iprp_paramtable) for detailed documentation.

### iprp_costtable.2da

See [iprp_costtable.2da](2DA-iprp_costtable) for detailed documentation.

### iprp_abilities.2da

See [iprp_abilities.2da](2DA-iprp_abilities) for detailed documentation.

### iprp_aligngrp.2da

See [iprp_aligngrp.2da](2DA-iprp_aligngrp) for detailed documentation.

### iprp_combatdam.2da

See [iprp_combatdam.2da](2DA-iprp_combatdam) for detailed documentation.

### iprp_damagetype.2da

See [iprp_damagetype.2da](2DA-iprp_damagetype) for detailed documentation.

### iprp_protection.2da

See [iprp_protection.2da](2DA-iprp_protection) for detailed documentation.

### iprp_acmodtype.2da

See [iprp_acmodtype.2da](2DA-iprp_acmodtype) for detailed documentation.

### iprp_immunity.2da

See [iprp_immunity.2da](2DA-iprp_immunity) for detailed documentation.

### iprp_saveelement.2da

See [iprp_saveelement.2da](2DA-iprp_saveelement) for detailed documentation.

### iprp_savingthrow.2da

See [iprp_savingthrow.2da](2DA-iprp_savingthrow) for detailed documentation.

### iprp_onhit.2da

See [iprp_onhit.2da](2DA-iprp_onhit) for detailed documentation.

### iprp_ammotype.2da

See [iprp_ammotype.2da](2DA-iprp_ammotype) for detailed documentation.

### iprp_mosterhit.2da

See [iprp_mosterhit.2da](2DA-iprp_mosterhit) for detailed documentation.

### iprp_walk.2da

See [iprp_walk.2da](2DA-iprp_walk) for detailed documentation.

### ai_styles.2da

See [ai_styles.2da](2DA-ai_styles) for detailed documentation.

### iprp_damagevs.2da

See [iprp_damagevs.2da](2DA-iprp_damagevs) for detailed documentation.

### iprp_attackmod.2da

See [iprp_attackmod.2da](2DA-iprp_attackmod) for detailed documentation.

### iprp_bonusfeat.2da

See [iprp_bonusfeat.2da](2DA-iprp_bonusfeat) for detailed documentation.

### iprp_lightcol.2da

See [iprp_lightcol.2da](2DA-iprp_lightcol) for detailed documentation.

### iprp_monstdam.2da

See [iprp_monstdam.2da](2DA-iprp_monstdam) for detailed documentation.

### iprp_skillcost.2da

See [iprp_skillcost.2da](2DA-iprp_skillcost) for detailed documentation.

### iprp_weightinc.2da

See [iprp_weightinc.2da](2DA-iprp_weightinc) for detailed documentation.

### iprp_traptype.2da

See [iprp_traptype.2da](2DA-iprp_traptype) for detailed documentation.

### iprp_damagered.2da

See [iprp_damagered.2da](2DA-iprp_damagered) for detailed documentation.

### iprp_spellres.2da

See [iprp_spellres.2da](2DA-iprp_spellres) for detailed documentation.

### rumble.2da

See [rumble.2da](2DA-rumble) for detailed documentation.

### musictable.2da

See [musictable.2da](2DA-musictable) for detailed documentation.

### difficultyopt.2da

See [difficultyopt.2da](2DA-difficultyopt) for detailed documentation.

### xptable.2da

See [xptable.2da](2DA-xptable) for detailed documentation.

### featgain.2da

See [featgain.2da](2DA-featgain) for detailed documentation.

### effecticon.2da

See [effecticon.2da](2DA-effecticon) for detailed documentation.

### itempropsdef.2da

See [itempropsdef.2da](2DA-itempropsdef) for detailed documentation.

### pazaakdecks.2da

See [pazaakdecks.2da](2DA-pazaakdecks) for detailed documentation.

### acbonus.2da

See [acbonus.2da](2DA-acbonus) for detailed documentation.

### keymap.2da

See [keymap.2da](2DA-keymap) for detailed documentation.

### soundeax.2da

See [soundeax.2da](2DA-soundeax) for detailed documentation.

### poison.2da

See [poison.2da](2DA-poison) for detailed documentation.

### feedbacktext.2da

See [feedbacktext.2da](2DA-feedbacktext) for detailed documentation.

### creaturesize.2da

See [creaturesize.2da](2DA-creaturesize) for detailed documentation.

### appearancesndset.2da

See [appearancesndset.2da](2DA-appearancesndset) for detailed documentation.

### texpacks.2da

See [texpacks.2da](2DA-texpacks) for detailed documentation.

### videoquality.2da

See [videoquality.2da](2DA-videoquality) for detailed documentation.

### loadscreens.2da

See [loadscreens.2da](2DA-loadscreens) for detailed documentation.

### phenotype.2da

See [phenotype.2da](2DA-phenotype) for detailed documentation.

### palette.2da

See [palette.2da](2DA-palette) for detailed documentation.

### bodyvariation.2da

See [bodyvariation.2da](2DA-bodyvariation) for detailed documentation.

### textures.2da

See [textures.2da](2DA-textures) for detailed documentation.

### merchants.2da

See [merchants.2da](2DA-merchants) for detailed documentation.

### actions.2da

See [actions.2da](2DA-actions) for detailed documentation.

### aiscripts.2da

See [aiscripts.2da](2DA-aiscripts) for detailed documentation.

### bindablekeys.2da

See [bindablekeys.2da](2DA-bindablekeys) for detailed documentation.

### crtemplates.2da

See [crtemplates.2da](2DA-crtemplates) for detailed documentation.

### environment.2da

See [environment.2da](2DA-environment) for detailed documentation.

### fractionalcr.2da

See [fractionalcr.2da](2DA-fractionalcr) for detailed documentation.

### gamespyrooms.2da

See [gamespyrooms.2da](2DA-gamespyrooms) for detailed documentation.

### hen_companion.2da

See [hen_companion.2da](2DA-hen_companion) for detailed documentation.

### hen_familiar.2da

See [hen_familiar.2da](2DA-hen_familiar) for detailed documentation.

### masterfeats.2da

See [masterfeats.2da](2DA-masterfeats) for detailed documentation.

### movies.2da

See [movies.2da](2DA-movies) for detailed documentation.

### stringtokens.2da

See [stringtokens.2da](2DA-stringtokens) for detailed documentation.

### tutorial_old.2da

See [tutorial_old.2da](2DA-tutorial_old) for detailed documentation.

### credits.2da

See [credits.2da](2DA-credits) for detailed documentation.

### disease.2da

See [disease.2da](2DA-disease) for detailed documentation.

### droiddischarge.2da

See [droiddischarge.2da](2DA-droiddischarge) for detailed documentation.

### minglobalrim.2da

See [minglobalrim.2da](2DA-minglobalrim) for detailed documentation.

### upcrystals.2da

See [upcrystals.2da](2DA-upcrystals) for detailed documentation.

### chargenclothes.2da

See [chargenclothes.2da](2DA-chargenclothes) for detailed documentation.

### aliensound.2da

See [aliensound.2da](2DA-aliensound) for detailed documentation.

### alienvo.2da

See [alienvo.2da](2DA-alienvo) for detailed documentation.

### grenadesnd.2da

See [grenadesnd.2da](2DA-grenadesnd) for detailed documentation.

### inventorysnds.2da

See [inventorysnds.2da](2DA-inventorysnds) for detailed documentation.

### areaeffects.2da

See [areaeffects.2da](2DA-areaeffects) for detailed documentation.

## Implementation Details

### PyKotor Implementation

**Reading**: [`Libraries/PyKotor/src/pykotor/resource/formats/twoda/io_twoda.py:12-106`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/twoda/io_twoda.py#L12-L106)

**Writing**: [`Libraries/PyKotor/src/pykotor/resource/formats/twoda/io_twoda.py:109-174`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/twoda/io_twoda.py#L109-L174)

### Vendor Implementations

**reone** (C++):

- Reading: [`vendor/reone/src/libs/resource/format/2dareader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/2dareader.cpp)
- Writing: [`vendor/reone/src/libs/resource/format/2dawriter.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/2dawriter.cpp)
- Data Structure: [`vendor/reone/src/libs/resource/2da.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/2da.cpp)

**xoreos** (C++):

- Reading: [`vendor/xoreos/src/aurora/2dafile.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/2dafile.cpp) - Generic Aurora engine 2DA format parser (shared across KotOR, Neverwinter Nights, and other Aurora engine games). The format structure is the same, but specific 2DA files and their columns are KotOR-specific.

**KotOR-Unity** (C#):

- Reading: [`vendor/KotOR-Unity/Assets/Scripts/FileObjects/2DAObject.cs:23-105`](https://github.com/th3w1zard1/KotOR-Unity/blob/master/Assets/Scripts/FileObjects/2DAObject.cs#L23-L105) - Complete 2DA reading implementation with column parsing, row indices, and cell data reading

**TSLPatcher** (Perl):

- Reading/Writing: [`vendor/TSLPatcher/lib/site/Bioware/TwoDA.pm`](https://github.com/th3w1zard1/TSLPatcher/blob/master/lib/site/Bioware/TwoDA.pm)

**KotOR.js** (TypeScript):

- Reading: [`vendor/KotOR.js/src/resource/TwoDAObject.ts:69-145`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/TwoDAObject.ts#L69-L145) - Complete 2DA reading implementation
- Manager: [`vendor/KotOR.js/src/managers/TwoDAManager.ts:21-37`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/managers/TwoDAManager.ts#L21-L37) - 2DA table loading from game archives
- Usage: [`vendor/KotOR.js/src/talents/TalentFeat.ts:122-132`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/talents/TalentFeat.ts#L122-L132) - Feat loading from `feat.2da`

**Kotor.NET** (C#):

- Structure: [`vendor/Kotor.NET/Kotor.NET/Formats/Kotor2DA/TwoDABinaryStructure.cs`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/Kotor2DA/TwoDABinaryStructure.cs)

---

This documentation aims to provide a comprehensive overview of the KotOR 2DA file format, focusing on the detailed file structure and data formats used within the games.
