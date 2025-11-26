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
    - [itemprops.2da](#itemprops2da)
    - [iprp\_feats.2da](#iprp_feats2da)
    - [iprp\_spells.2da](#iprp_spells2da)
    - [iprp\_ammocost.2da](#iprp_ammocost2da)
    - [iprp\_damagecost.2da](#iprp_damagecost2da)
  - [Objects \& Area 2DA Files](#objects--area-2da-files)
    - [placeables.2da](#placeables2da)
    - [genericdoors.2da / doortypes.2da](#genericdoors2da--doortypes2da)
    - [soundset.2da](#soundset2da)
  - [Visual Effects \& Animations 2DA Files](#visual-effects--animations-2da-files)
    - [visualeffects.2da](#visualeffects2da)
    - [portraits.2da](#portraits2da)
    - [heads.2da](#heads2da)
  - [Progression Tables 2DA Files](#progression-tables-2da-files)
    - [classpowergain.2da](#classpowergain2da)
    - [cls\_atk\_\*.2da](#cls_atk_2da)
    - [cls\_savthr\_\*.2da](#cls_savthr_2da)
  - [Name Generation 2DA Files](#name-generation-2da-files)
    - [humanfirst.2da / humanlast.2da](#humanfirst2da--humanlast2da)
    - [Other Name Generation Files](#other-name-generation-files)
  - [Additional 2DA Files](#additional-2da-files)
    - [ambientmusic.2da](#ambientmusic2da)
    - [ambientsound.2da](#ambientsound2da)
    - [ammunitiontypes.2da](#ammunitiontypes2da)
    - [camerastyle.2da](#camerastyle2da)
    - [footstepsounds.2da](#footstepsounds2da)
    - [prioritygroups.2da](#prioritygroups2da)
    - [repute.2da](#repute2da)
    - [surfacemat.2da](#surfacemat2da)
    - [loadscreenhints.2da](#loadscreenhints2da)
    - [bodybag.2da](#bodybag2da)
    - [ranges.2da](#ranges2da)
    - [regeneration.2da](#regeneration2da)
    - [animations.2da](#animations2da)
    - [combatanimations.2da](#combatanimations2da)
    - [weaponsounds.2da](#weaponsounds2da)
    - [placeableobjsnds.2da](#placeableobjsnds2da)
    - [creaturespeed.2da](#creaturespeed2da)
    - [exptable.2da](#exptable2da)
    - [guisounds.2da](#guisounds2da)
    - [dialoganimations.2da](#dialoganimations2da)
    - [tilecolor.2da](#tilecolor2da)
    - [forceshields.2da](#forceshields2da)
    - [plot.2da](#plot2da)
    - [traps.2da](#traps2da)
    - [modulesave.2da](#modulesave2da)
    - [tutorial.2da](#tutorial2da)
    - [globalcat.2da](#globalcat2da)
    - [subrace.2da](#subrace2da)
    - [gender.2da](#gender2da)
    - [racialtypes.2da](#racialtypes2da)
    - [upgrade.2da](#upgrade2da)
    - [encdifficulty.2da](#encdifficulty2da)
    - [itempropdef.2da](#itempropdef2da)
    - [emotion.2da](#emotion2da)
    - [facialanim.2da](#facialanim2da)
    - [videoeffects.2da](#videoeffects2da)
    - [planetary.2da](#planetary2da)
    - [cursors.2da](#cursors2da)
  - [Item Property Parameter \& Cost Tables 2DA Files](#item-property-parameter--cost-tables-2da-files)
    - [iprp\_paramtable.2da](#iprp_paramtable2da)
    - [iprp\_costtable.2da](#iprp_costtable2da)
    - [iprp\_abilities.2da](#iprp_abilities2da)
    - [iprp\_aligngrp.2da](#iprp_aligngrp2da)
    - [iprp\_combatdam.2da](#iprp_combatdam2da)
    - [iprp\_damagetype.2da](#iprp_damagetype2da)
    - [iprp\_protection.2da](#iprp_protection2da)
    - [iprp\_acmodtype.2da](#iprp_acmodtype2da)
    - [iprp\_immunity.2da](#iprp_immunity2da)
    - [iprp\_saveelement.2da](#iprp_saveelement2da)
    - [iprp\_savingthrow.2da](#iprp_savingthrow2da)
    - [iprp\_onhit.2da](#iprp_onhit2da)
    - [iprp\_ammotype.2da](#iprp_ammotype2da)
    - [iprp\_mosterhit.2da](#iprp_mosterhit2da)
    - [iprp\_walk.2da](#iprp_walk2da)
    - [ai\_styles.2da](#ai_styles2da)
    - [iprp\_damagevs.2da](#iprp_damagevs2da)
    - [iprp\_attackmod.2da](#iprp_attackmod2da)
    - [iprp\_bonusfeat.2da](#iprp_bonusfeat2da)
    - [iprp\_lightcol.2da](#iprp_lightcol2da)
    - [iprp\_monstdam.2da](#iprp_monstdam2da)
    - [iprp\_skillcost.2da](#iprp_skillcost2da)
    - [iprp\_weightinc.2da](#iprp_weightinc2da)
    - [iprp\_traptype.2da](#iprp_traptype2da)
    - [iprp\_damagered.2da](#iprp_damagered2da)
    - [iprp\_spellres.2da](#iprp_spellres2da)
    - [rumble.2da](#rumble2da)
    - [musictable.2da](#musictable2da)
    - [difficultyopt.2da](#difficultyopt2da)
    - [xptable.2da](#xptable2da)
    - [featgain.2da](#featgain2da)
    - [effecticon.2da](#effecticon2da)
    - [itempropsdef.2da](#itempropsdef2da)
    - [pazaakdecks.2da](#pazaakdecks2da)
    - [acbonus.2da](#acbonus2da)
    - [keymap.2da](#keymap2da)
    - [soundeax.2da](#soundeax2da)
    - [poison.2da](#poison2da)
    - [feedbacktext.2da](#feedbacktext2da)
    - [creaturesize.2da](#creaturesize2da)
    - [appearancesndset.2da](#appearancesndset2da)
    - [texpacks.2da](#texpacks2da)
    - [videoquality.2da](#videoquality2da)
    - [loadscreens.2da](#loadscreens2da)
    - [phenotype.2da](#phenotype2da)
    - [palette.2da](#palette2da)
    - [bodyvariation.2da](#bodyvariation2da)
    - [textures.2da](#textures2da)
    - [merchants.2da](#merchants2da)
    - [actions.2da](#actions2da)
    - [aiscripts.2da](#aiscripts2da)
    - [bindablekeys.2da](#bindablekeys2da)
    - [crtemplates.2da](#crtemplates2da)
    - [doortypes.2da](#doortypes2da)
    - [environment.2da](#environment2da)
    - [fractionalcr.2da](#fractionalcr2da)
    - [gamespyrooms.2da](#gamespyrooms2da)
    - [hen\_companion.2da](#hen_companion2da)
    - [hen\_familiar.2da](#hen_familiar2da)
    - [masterfeats.2da](#masterfeats2da)
    - [movies.2da](#movies2da)
    - [stringtokens.2da](#stringtokens2da)
    - [tutorial\_old.2da](#tutorial_old2da)
    - [credits.2da](#credits2da)
    - [disease.2da](#disease2da)
    - [droiddischarge.2da](#droiddischarge2da)
    - [minglobalrim.2da](#minglobalrim2da)
    - [upcrystals.2da](#upcrystals2da)
    - [chargenclothes.2da](#chargenclothes2da)
    - [aliensound.2da](#aliensound2da)
    - [alienvo.2da](#alienvo2da)
    - [grenadesnd.2da](#grenadesnd2da)
    - [inventorysnds.2da](#inventorysnds2da)
    - [areaeffects.2da](#areaeffects2da)
      - [Additional Item Property Files](#additional-item-property-files)
      - [Audio \& Music](#audio--music)
      - [Item Property Cost Tables](#item-property-cost-tables)
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

**Engine Usage**: The `appearance.2da` file is one of the most critical 2DA files in KotOR. It maps appearance IDs (used in creature templates and character creation) to 3D model ResRefs, texture assignments, race associations, and physical properties. The engine uses this file when loading creatures, determining which model and textures to display, calculating hit detection, and managing character animations.

**Row Index**: Appearance ID (integer, typically 0-based)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String (optional) | Human-readable label for the appearance |
| `modeltype` | String | Model type identifier (e.g., "F", "B", "P") |
| `modela` through `modeln` | ResRef (optional) | Model ResRefs for different body parts or variations (models a-n) |
| `texa` through `texn` | ResRef (optional) | Texture ResRefs for different body parts (textures a-n) |
| `texaevil`, `texbevil`, `texievil`, `texlevil`, `texnevil` | ResRef (optional) | Dark side variant textures |
| `race` | ResRef (optional) | Race identifier ResRef |
| `racetex` | ResRef (optional) | Race-specific texture ResRef |
| `racialtype` | Integer | Numeric racial type identifier |
| `normalhead` | Integer (optional) | Default head appearance ID |
| `backuphead` | Integer (optional) | Fallback head appearance ID |
| `portrait` | ResRef (optional) | Portrait image ResRef |
| `skin` | ResRef (optional) | Skin texture ResRef |
| `headtexe`, `headtexg`, `headtexve`, `headtexvg` | ResRef (optional) | Head texture variations |
| `headbone` | String (optional) | Bone name for head attachment |
| `height` | [Float](https://en.wikipedia.org/wiki/Single-precision_floating-point_format) | Character height multiplier |
| `hitdist` | [Float](https://en.wikipedia.org/wiki/Single-precision_floating-point_format) | Hit detection distance |
| `hitradius` | [Float](https://en.wikipedia.org/wiki/Single-precision_floating-point_format) | Hit detection radius |
| `sizecategory` | Integer | Size category (affects combat calculations) |
| `moverate` | String | Movement rate identifier |
| `walkdist` | Float | Walking distance threshold |
| `rundist` | Float | Running distance threshold |
| `prefatckdist` | Float | Preferred attack distance |
| `creperspace` | Float | Creature personal space radius |
| `perspace` | Float | Personal space radius |
| `cameraspace` | Float (optional) | Camera space offset |
| `cameraheightoffset` | String (optional) | Camera height offset |
| `targetheight` | String | Target height for combat |
| `perceptiondist` | Integer | Perception distance |
| `headArcH` | Integer | Head horizontal arc angle |
| `headArcV` | Integer | Head vertical arc angle |
| `headtrack` | Boolean | Whether head tracking is enabled |
| `hasarms` | Boolean | Whether creature has arms |
| `haslegs` | Boolean | Whether creature has legs |
| `groundtilt` | Boolean | Whether ground tilt is enabled |
| `footsteptype` | Integer (optional) | Footstep sound type |
| `footstepsound` | ResRef (optional) | Footstep sound ResRef |
| `footstepvolume` | Boolean | Whether footstep volume is enabled |
| `armorSound` | ResRef (optional) | Armor sound effect ResRef |
| `combatSound` | ResRef (optional) | Combat sound effect ResRef |
| `soundapptype` | Integer (optional) | Sound appearance type |
| `bloodcolr` | String | Blood color identifier |
| `deathvfx` | Integer (optional) | Death visual effect ID |
| `deathvfxnode` | String (optional) | Death VFX attachment node |
| `fadedelayondeath` | Boolean (optional) | Whether to fade on death |
| `destroyobjectdelay` | Boolean (optional) | Whether to delay object destruction |
| `disableinjuredanim` | Boolean (optional) | Whether to disable injured animations |
| `abortonparry` | Boolean | Whether to abort on parry |
| `freelookeffect` | Integer (optional) | Free look effect ID |
| `equipslotslocked` | Integer (optional) | Locked equipment slot flags |
| `weaponscale` | String (optional) | Weapon scale multiplier |
| `wingTailScale` | Boolean | Whether wing/tail scaling is enabled |
| `helmetScaleF` | String (optional) | Female helmet scale |
| `helmetScaleM` | String (optional) | Male helmet scale |
| `envmap` | ResRef (optional) | Environment map texture ResRef |
| `bodyBag` | Integer (optional) | Body bag appearance ID |
| `stringRef` | Integer (optional) | String reference for appearance name |
| `driveaccl` | Integer | Vehicle drive acceleration |
| `drivemaxspeed` | Float | Vehicle maximum speed |
| `driveanimwalk` | Float | Vehicle walk animation speed |
| `driveanimrunPc` | Float | PC vehicle run animation speed |
| `driveanimrunXbox` | Float | Xbox vehicle run animation speed |

**Column Details**:

The `appearance.2da` file contains a comprehensive set of columns for character appearance configuration. The complete column list is parsed by reone's appearance parser:

- Model columns: `modela` through `modeln` (14 model variations)
- Texture columns: `texa` through `texn` (14 texture variations)
- Evil texture columns: `texaevil`, `texbevil`, `texievil`, `texlevil`, `texnevil`
- Head texture columns: `headtexe`, `headtexg`, `headtexve`, `headtexvg`
- Movement: `walkdist`, `rundist`, `prefatckdist`, `moverate`
- Physical properties: `height`, `hitdist`, `hitradius`, `sizecategory`, `perceptiondist`
- Personal space: `perspace`, `creperspace`
- Camera: `cameraspace`, `cameraheightoffset`, `targetheight`
- Head tracking: `headArcH`, `headArcV`, `headtrack`
- Body parts: `hasarms`, `haslegs`, `groundtilt`, `wingTailScale`
- Footsteps: `footsteptype`, `footstepsound`, `footstepvolume`
- Sounds: `armorSound`, `combatSound`, `soundapptype`
- Visual effects: `deathvfx`, `deathvfxnode`, `fadedelayondeath`, `freelookeffect`
- Equipment: `equipslotslocked`, `weaponscale`, `helmetScaleF`, `helmetScaleM`
- Textures: `envmap`, `skin`, `portrait`, `race`, `racetex`, `racialtype`
- Heads: `normalhead`, `backuphead`, `headbone`
- Vehicle: `driveaccl`, `drivemaxspeed`, `driveanimwalk`, `driveanimrunPc`, `driveanimrunXbox`
- Other: `bloodcolr`, `bodyBag`, `stringRef`, `abortonparry`, `destroyobjectdelay`, `disableinjuredanim`

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:73`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L73) - StrRef column definition for appearance.2da (K1: string_ref)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:248`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L248) - StrRef column definition for appearance.2da (K2: string_ref)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:155`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L155) - ResRef column definition for appearance.2da (race)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:168`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L168) - Model ResRef column definitions for appearance.2da (modela through modelj)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:213-214`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L213-L214) - Texture ResRef column definitions for appearance.2da (racetex, texa through texj, headtexve, headtexe, headtexvg, headtexg)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:456`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L456) - TwoDARegistry.APPEARANCES constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:524`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L524) - GFF field mapping: "Appearance_Type" -> appearance.2da

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:55`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L55) - HTInstallation.TwoDA_APPEARANCES constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/utc.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utc.py) - Appearance selection combobox in UTC editor (UI reference)
- [`Tools/HolocronToolset/src/toolset/gui/editors/utp.py:124-131`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utp.py#L124-L131) - Appearance selection in UTP (placeable) editor
- [`Tools/HolocronToolset/src/toolset/gui/editors/utd.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utd.py) - Appearance selection in UTD (door) editor (UI reference)
- [`Tools/HolocronToolset/src/toolset/gui/editors/ute.py:181`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/ute.py#L181) - Appearance ID usage in encounter editor

**Vendor Implementations:**

- [`vendor/reone/src/libs/resource/parser/2da/appearance.cpp:28-125`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/2da/appearance.cpp#L28-L125) - Complete column parsing implementation with all column names
- [`vendor/reone/src/libs/game/object/creature.cpp:98-107`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/creature.cpp#L98-L107) - Appearance loading and column usage
- [`vendor/reone/src/libs/game/object/creature.cpp:1156-1228`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/creature.cpp#L1156-L1228) - Model and texture column access

---

### baseitems.2da

**Engine Usage**: Defines base item types that form the foundation for all items in the game. Each row represents a base item type (weapon, armor, shield, etc.) with properties like damage dice, weapon categories, equipment slots, and item flags. The engine uses this file to determine item behavior, combat statistics, and equipment compatibility.

**Row Index**: Base item ID (integer)

**Column Structure** (columns accessed by reone):

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Item type label |
| `name` | StrRef | String reference for item type name |
| `basecost` | Integer | Base gold cost |
| `stacking` | Integer | Stack size limit |
| `invslotwidth` | Integer | Inventory slot width |
| `invslotheight` | Integer | Inventory slot height |
| `canrotateicon` | Boolean | Whether icon can be rotated in inventory |
| `itemclass` | Integer | Item class identifier |
| `weapontype` | Integer | Weapon type (if weapon) |
| `weaponsize` | Integer | Weapon size category |
| `weaponwield` | Integer | Wield type (one-handed, two-handed, etc.) |
| `damagedice` | Integer | Damage dice count |
| `damagedie` | Integer | Damage die size |
| `damagebonus` | Integer | Base damage bonus |
| `damagetype` | Integer | Damage type flags |
| `weaponmattype` | Integer | Weapon material type |
| `weaponsound` | Integer | Weapon sound type |
| `ammunitiontype` | Integer | Ammunition type required |
| `rangedweapon` | Boolean | Whether item is a ranged weapon |
| `maxattackrange` | Integer | Maximum attack range |
| `preferredattackrange` | Integer | Preferred attack range |
| `attackmod` | Integer | Attack modifier |
| `damagebonusfeat` | Integer | Feat ID for damage bonus |
| `weaponfocustype` | Integer | Weapon focus type |
| `weaponfocusfeat` | Integer | Weapon focus feat ID |
| `description` | StrRef | String reference for item description |
| `icon` | ResRef | Icon image ResRef |
| `equipableslots` | Integer | Equipment slot flags |
| `model1` through `model6` | ResRef (optional) | 3D model ResRefs for different variations |
| `partenvmap` | ResRef (optional) | Partial environment map texture |
| `defaultmodel` | ResRef (optional) | Default model ResRef |
| `defaulticon` | ResRef (optional) | Default icon ResRef |
| `container` | Boolean | Whether item is a container |
| `weapon` | Boolean | Whether item is a weapon |
| `armor` | Boolean | Whether item is armor |
| `chargesstarting` | Integer | Starting charges (for usable items) |
| `costpercharge` | Integer | Cost per charge to recharge |
| `addcost` | Integer | Additional cost modifier |
| `stolen` | Boolean | Whether item is marked as stolen |
| `minlevel` | Integer | Minimum level requirement |
| `stacking` | Integer | Maximum stack size |
| `reqfeat0` through `reqfeat3` | Integer (optional) | Required feat IDs |
| `reqfeatcount0` through `reqfeatcount3` | Integer (optional) | Required feat counts |
| `reqclass` | Integer (optional) | Required class ID |
| `reqrace` | Integer (optional) | Required race ID |
| `reqalign` | Integer (optional) | Required alignment |
| `reqdeity` | Integer (optional) | Required deity ID |
| `reqstr` | Integer (optional) | Required strength |
| `reqdex` | Integer (optional) | Required dexterity |
| `reqint` | Integer (optional) | Required intelligence |
| `reqwis` | Integer (optional) | Required wisdom |
| `reqcon` | Integer (optional) | Required constitution |
| `reqcha` | Integer (optional) | Required charisma |

**Column Details** (from reone implementation):

The following columns are accessed by the reone engine:

- `maxattackrange`: Maximum attack range for ranged weapons
- `crithitmult`: Critical hit multiplier
- `critthreat`: Critical threat range
- `damageflags`: Damage type flags
- `dietoroll`: Damage die size
- `equipableslots`: Equipment slot flags (hex integer)
- `itemclass`: Item class identifier (string)
- `numdice`: Number of damage dice
- `weapontype`: Weapon type identifier
- `weaponwield`: Weapon wield type (one-handed, two-handed, etc.)
- `bodyvar`: Body variation for armor
- `ammunitiontype`: Ammunition type ID (used to look up `ammunitiontypes.2da`)

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:169`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L169) - Model ResRef column definition for baseitems.2da (defaultmodel)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:187`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L187) - Sound ResRef column definitions for baseitems.2da (powerupsnd, powerdownsnd, poweredsnd)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:215`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L215) - Texture ResRef column definition for baseitems.2da (defaulticon)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:225`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L225) - Item ResRef column definitions for baseitems.2da (itemclass, baseitemstatref)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:466`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L466) - TwoDARegistry.BASEITEMS constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:537`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L537) - GFF field mapping: "BaseItem" and "ModelVariation" -> baseitems.2da

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:65`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L65) - HTInstallation.TwoDA_BASEITEMS constant
- [`Tools/HolocronToolset/src/toolset/data/installation.py:594-607`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L594-L607) - get_item_icon_from_uti method using baseitems.2da for item class lookup
- [`Tools/HolocronToolset/src/toolset/data/installation.py:609-620`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L609-L620) - get_item_base_name method using baseitems.2da
- [`Tools/HolocronToolset/src/toolset/data/installation.py:630-643`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L630-L643) - get_item_icon_path method using baseitems.2da for item class and icon path
- [`Tools/HolocronToolset/src/toolset/gui/editors/uti.py:107-117`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/uti.py#L107-L117) - baseitems.2da loading and usage in UTI (item) editor for base item selection
- [`Tools/HolocronToolset/src/toolset/gui/dialogs/inventory.py:668-704`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/dialogs/inventory.py#L668-L704) - baseitems.2da usage for equipment slot and droid/human flag lookup

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/object/item.cpp:126-136`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/item.cpp#L126-L136) - Base item column access
- [`vendor/reone/src/libs/game/object/item.cpp:160-171`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/item.cpp#L160-L171) - Ammunition type lookup from baseitems.2da

---

### classes.2da

**Engine Usage**: Defines character classes with their progression tables, skill point calculations, hit dice, saving throw progressions, and feat access. The engine uses this file to determine class abilities, skill point allocation, and level progression mechanics.

**Row Index**: Class ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Class label |
| `name` | StrRef | String reference for class name |
| `description` | StrRef | String reference for class description |
| `hitdie` | Integer | Hit dice size (d6, d8, d10, etc.) |
| `skillpointbase` | Integer | Base skill points per level |
| `skillpointbonus` | Integer | Intelligence bonus skill points |
| `attackbonus` | String | Attack bonus progression table reference |
| `savingthrow` | String | Saving throw progression table reference |
| `savingthrowtable` | String | Saving throw table filename |
| `spellgaintable` | String | Spell/Force power gain table reference |
| `spellknowntable` | String | Spell/Force power known table reference |
| `primaryability` | Integer | Primary ability score for class |
| `preferredalignment` | Integer | Preferred alignment |
| `alignrestrict` | Integer | Alignment restrictions |
| `classfeat` | Integer | Class-specific feat ID |
| `classskill` | Integer | Class skill flags |
| `skillpointmaxlevel` | Integer | Maximum level for skill point calculation |
| `spellcaster` | Integer | Spellcasting level (0 = non-caster) |
| `spellcastingtype` | Integer | Spellcasting type identifier |
| `spelllevel` | Integer | Maximum spell level |
| `spellbook` | ResRef (optional) | Spellbook ResRef |
| `icon` | ResRef | Class icon ResRef |
| `portrait` | ResRef (optional) | Class portrait ResRef |
| `startingfeat0` through `startingfeat9` | Integer (optional) | Starting feat IDs |
| `startingpack` | Integer (optional) | Starting equipment pack ID |
| `description` | StrRef | Class description string reference |

**Column Details** (from reone implementation):

The following columns are accessed by the reone engine:

- `name`: String reference for class name
- `description`: String reference for class description
- `hitdie`: Hit dice size
- `skillpointbase`: Base skill points per level
- `str`, `dex`, `con`, `int`, `wis`, `cha`: Default ability scores
- `skillstable`: Skills table reference (used to check class skills in `skills.2da`)
- `savingthrowtable`: Saving throw table reference (e.g., `cls_savthr_jedi_guardian`)
- `attackbonustable`: Attack bonus table reference (e.g., `cls_atk_jedi_guardian`)

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:75`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L75) - StrRef column definitions for classes.2da (K1: name, description)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:250`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L250) - StrRef column definitions for classes.2da (K2: name, description)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:463`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L463) - TwoDARegistry.CLASSES constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:531`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L531) - GFF field mapping: "Class" -> classes.2da

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:62`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L62) - HTInstallation.TwoDA_CLASSES constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/utc.py:242`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utc.py#L242) - classes.2da included in batch cache for UTC editor
- [`Tools/HolocronToolset/src/toolset/gui/editors/utc.py:256`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utc.py#L256) - classes.2da loading from cache
- [`Tools/HolocronToolset/src/toolset/gui/editors/utc.py:291-298`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utc.py#L291-L298) - classes.2da usage in class selection comboboxes and label population

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/d20/class.cpp:34-56`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/d20/class.cpp#L34-L56) - Class loading from 2DA with column access
- [`vendor/reone/src/libs/game/d20/class.cpp:58-86`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/d20/class.cpp#L58-L86) - Class skills, saving throws, and attack bonuses loading

---

### feat.2da

**Engine Usage**: Defines all feats available in the game, including combat feats, skill feats, Force feats, and class-specific abilities. The engine uses this file to determine feat prerequisites, effects, and availability during character creation and level-up.

**Row Index**: Feat ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Feat label |
| `name` | StrRef | String reference for feat name |
| `description` | StrRef | String reference for feat description |
| `icon` | ResRef | Feat icon ResRef |
| `takentext` | StrRef | String reference for "feat taken" message |
| `prerequisite` | Integer (optional) | Prerequisite feat ID |
| `minattackbonus` | Integer (optional) | Minimum attack bonus requirement |
| `minstr` | Integer (optional) | Minimum strength requirement |
| `mindex` | Integer (optional) | Minimum dexterity requirement |
| `minint` | Integer (optional) | Minimum intelligence requirement |
| `minwis` | Integer (optional) | Minimum wisdom requirement |
| `mincon` | Integer (optional) | Minimum constitution requirement |
| `mincha` | Integer (optional) | Minimum charisma requirement |
| `minlevel` | Integer (optional) | Minimum character level |
| `minclasslevel` | Integer (optional) | Minimum class level |
| `minspelllevel` | Integer (optional) | Minimum spell level |
| `spellid` | Integer (optional) | Required spell ID |
| `successor` | Integer (optional) | Successor feat ID (for feat chains) |
| `maxrank` | Integer (optional) | Maximum rank for stackable feats |
| `minrank` | Integer (optional) | Minimum rank requirement |
| `masterfeat` | Integer (optional) | Master feat ID |
| `targetself` | Boolean | Whether feat targets self |
| `orreqfeat0` through `orreqfeat4` | Integer (optional) | Alternative prerequisite feat IDs |
| `reqskill` | Integer (optional) | Required skill ID |
| `reqskillrank` | Integer (optional) | Required skill rank |
| `constant` | Integer (optional) | Constant value for feat calculations |
| `toolscategories` | Integer (optional) | Tool categories flags |
| `effecticon` | ResRef (optional) | Effect icon ResRef |
| `effectdesc` | StrRef (optional) | Effect description string reference |
| `effectcategory` | Integer (optional) | Effect category identifier |
| `allclassescanuse` | Boolean | Whether all classes can use this feat |
| `category` | Integer | Feat category identifier |
| `maxcr` | Integer (optional) | Maximum challenge rating |
| `spellid` | Integer (optional) | Associated spell ID |
| `usesperday` | Integer (optional) | Uses per day limit |
| `masterfeat` | Integer (optional) | Master feat ID for feat trees |

**Column Details** (from reone implementation):

The following columns are accessed by the reone engine:

- `name`: String reference for feat name
- `description`: String reference for feat description
- `icon`: Icon ResRef
- `mincharlevel`: Minimum character level (hex integer)
- `prereqfeat1`: Prerequisite feat ID 1 (hex integer)
- `prereqfeat2`: Prerequisite feat ID 2 (hex integer)
- `successor`: Successor feat ID (hex integer)
- `pips`: Feat pips/ranks (hex integer)
- `allclassescanuse`: Boolean - whether all classes can use this feat
- `masterfeat`: Master feat ID
- `orreqfeat0` through `orreqfeat4`: Alternative prerequisite feat IDs
- `hostilefeat`: Boolean - whether feat is hostile
- `category`: Feat category identifier

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:82`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L82) - StrRef column definitions for feat.2da (K1: name, description)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:260`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L260) - StrRef column definitions for feat.2da (K2: name, description)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:227`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L227) - ResRef column definition for feat.2da (icon)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:464`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L464) - TwoDARegistry.FEATS constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:561-562`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L561-L562) - GFF field mapping: "FeatID" and "Feat" -> feat.2da
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:321-323`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L321-L323) - UTC feat list field documentation
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:432`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L432) - UTC feats list initialization
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:762-768`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L762-L768) - Feat list parsing from UTC GFF
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:907-909`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L907-L909) - Feat list writing to UTC GFF

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:63`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L63) - HTInstallation.TwoDA_FEATS constant

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/d20/feats.cpp:32-58`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/d20/feats.cpp#L32-L58) - Feat loading from 2DA with column access
- [`vendor/KotOR.js/src/talents/TalentFeat.ts:36-53`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/talents/TalentFeat.ts#L36-L53) - Feat structure with additional columns
- [`vendor/KotOR.js/src/talents/TalentFeat.ts:122-132`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/talents/TalentFeat.ts#L122-L132) - Feat loading from 2DA

---

### skills.2da

**Engine Usage**: Defines all skills available in the game, including which classes can use them, their key ability scores, and skill descriptions. The engine uses this file to determine skill availability, skill point costs, and skill checks.

**Row Index**: Skill ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Skill label |
| `name` | StrRef | String reference for skill name |
| `description` | StrRef | String reference for skill description |
| `keyability` | Integer | Key ability score (STR, DEX, INT, etc.) |
| `armorcheckpenalty` | Boolean | Whether armor check penalty applies |
| `allclassescanuse` | Boolean | Whether all classes can use this skill |
| `category` | Integer | Skill category identifier |
| `maxrank` | Integer | Maximum skill rank |
| `untrained` | Boolean | Whether skill can be used untrained |
| `constant` | Integer (optional) | Constant modifier |
| `hostileskill` | Boolean | Whether skill is hostile |
| `icon` | ResRef (optional) | Skill icon ResRef |

**Column Details** (from reone implementation):

The following columns are accessed by the reone engine:

- `name`: String reference for skill name
- `description`: String reference for skill description
- `icon`: Icon ResRef
- Dynamic class skill columns: For each class, there is a column named `{classname}_class` (e.g., `jedi_guardian_class`) that contains `1` if the skill is a class skill for that class
- `droidcanuse`: Boolean - whether droids can use this skill
- `npccanuse`: Boolean - whether NPCs can use this skill

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:148`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L148) - StrRef column definitions for skills.2da (K1: name, description)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:326`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L326) - StrRef column definitions for skills.2da (K2: name, description)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:472`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L472) - TwoDARegistry.SKILLS constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:563`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L563) - GFF field mapping: "SkillID" -> skills.2da

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:71`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L71) - HTInstallation.TwoDA_SKILLS constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/savegame.py:129`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/savegame.py#L129) - Skills table widget in save game editor
- [`Tools/HolocronToolset/src/toolset/gui/editors/savegame.py:511-519`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/savegame.py#L511-L519) - Skills table population in save game editor
- [`Tools/HolocronToolset/src/toolset/gui/editors/savegame.py:542-543`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/savegame.py#L542-L543) - Skills table update logic

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/d20/skills.cpp:32-48`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/d20/skills.cpp#L32-L48) - Skill loading from 2DA
- [`vendor/reone/src/libs/game/d20/class.cpp:58-65`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/d20/class.cpp#L58-L65) - Class skill checking using dynamic column names
- [`vendor/KotOR.js/src/talents/TalentSkill.ts:38-49`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/talents/TalentSkill.ts#L38-L49) - Skill loading from 2DA with droidcanuse and npccanuse columns

---

### spells.2da

**Engine Usage**: Defines all Force powers (and legacy spell entries) in KotOR, including their costs, targeting modes, visual effects, and descriptions. The engine uses this file to determine Force power availability, casting requirements, and effects. Note: KotOR uses Force powers rather than traditional D&D spells, though the file structure is inherited from the Aurora engine (originally designed for Neverwinter Nights).

**Row Index**: Spell ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Spell label |
| `name` | StrRef | String reference for spell name |
| `school` | Integer | Spell school identifier |
| `range` | Integer | Spell range type |
| `vs` | Integer | Versus type (self, touch, etc.) |
| `metamagic` | Integer | Metamagic flags |
| `targettype` | Integer | Target type flags |
| `impactscript` | ResRef (optional) | Impact script ResRef |
| `innate` | Integer | Innate Force power level (0 = not available) |
| `conjtime` | Float | Casting/conjuration time |
| `conjtimevfx` | Integer (optional) | Casting time visual effect |
| `conjheadvfx` | Integer (optional) | Casting head visual effect |
| `conjhandvfx` | Integer (optional) | Casting hand visual effect |
| `conjgrndvfx` | Integer (optional) | Casting ground visual effect |
| `conjcastvfx` | Integer (optional) | Casting visual effect |
| `conjimpactscript` | ResRef (optional) | Conjuration impact script |
| `conjduration` | Float | Conjuration duration |
| `conjrange` | Integer | Conjuration range |
| `conjca` | Integer | Conjuration casting animation |
| `conjca2` through `conjca50` | Integer (optional) | Additional casting animations (numbered 2-50) |
| `hostilesetting` | Integer | Hostile setting flags |
| `featid` | Integer (optional) | Associated feat ID |
| `counter1` | Integer (optional) | Counter spell ID 1 |
| `counter2` | Integer (optional) | Counter spell ID 2 |
| `counter3` | Integer (optional) | Counter spell ID 3 |
| `projectile` | ResRef (optional) | Projectile model ResRef |
| `projectilesound` | ResRef (optional) | Projectile sound ResRef |
| `projectiletype` | Integer | Projectile type identifier |
| `projectileorient` | Integer | Projectile orientation |
| `projectilepath` | Integer | Projectile path type |
| `projectilehoming` | Boolean | Whether projectile homes on target |
| `projectilemodel` | ResRef (optional) | Projectile 3D model ResRef |
| `projectilemodel2` through `projectilemodel50` | ResRef (optional) | Additional projectile models (numbered 2-50) |
| `icon` | ResRef | Spell icon ResRef |
| `icon2` through `icon50` | ResRef (optional) | Additional icons (numbered 2-50) |
| `description` | StrRef | Spell description string reference |
| `altmessage` | StrRef (optional) | Alternative message string reference |
| `usewhencast` | Integer | Use when cast flags |
| `blood` | Boolean | Whether spell causes blood effects |
| `concentration` | Integer | Concentration check DC |
| `immunitytype` | Integer | Immunity type identifier |
| `immunitytype2` through `immunitytype50` | Integer (optional) | Additional immunity types (numbered 2-50) |
| `immunityitem` | Integer | Immunity item type |
| `immunityitem2` through `immunityitem50` | Integer (optional) | Additional immunity items (numbered 2-50) |

**Column Details** (from reone implementation):

The following columns are accessed by the reone engine:

- `name`: String reference for spell name
- `spelldesc`: String reference for spell description (note: column name is `spelldesc`, not `description`)
- `iconresref`: Icon ResRef (note: column name is `iconresref`, not `icon`)
- `pips`: Spell pips/ranks (hex integer)
- `conjtime`: Conjuration/casting time
- `casttime`: Cast time
- `catchtime`: Catch time
- `conjanim`: Conjuration animation type (e.g., "throw", "up")
- `hostilesetting`: Hostile setting flags
- `projectile`: Projectile ResRef
- `projectileHook`: Projectile hook point
- `projectileOrigin`: Projectile origin point
- `projectileTarget`: Projectile target point
- `projectileCurve`: Projectile curve type
- `projmodel`: Projectile model ResRef
- `range`: Spell range
- `impactscript`: Impact script ResRef
- `casthandvisual`: Cast hand visual effect

**Note**: The `spells.2da` file contains many optional columns for projectile models, icons, and immunity types (numbered 1-50). These are used for spell variations and visual effects.

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:149`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L149) - StrRef column definitions for spells.2da (K1: name, spelldesc)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:327`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L327) - StrRef column definitions for spells.2da (K2: name, spelldesc)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:239`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L239) - Script ResRef column definition for spells.2da (impactscript)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:432`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L432) - Script ResRef column definition for spells.2da (K2: impactscript)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:465`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L465) - TwoDARegistry.POWERS constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:558-560`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L558-L560) - GFF field mapping: "Subtype", "SpellId", and "Spell" -> spells.2da
- [`Libraries/PyKotor/src/pykotor/common/scriptdefs.py:9380-9381`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/common/scriptdefs.py#L9380-L9381) - GetLastForcePowerUsed function comment referencing Spells.2da
- [`Libraries/PyKotor/src/pykotor/common/scriptlib.py:5676`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/common/scriptlib.py#L5676) - Debug print referencing Spells.2DA ID

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:64`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L64) - HTInstallation.TwoDA_POWERS constant

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/d20/spells.cpp:32-48`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/d20/spells.cpp#L32-L48) - Spell loading from 2DA with column access
- [`vendor/KotOR.js/src/talents/TalentSpell.ts:16-44`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/talents/TalentSpell.ts#L16-L44) - Spell structure with additional columns
- [`vendor/KotOR.js/src/talents/TalentSpell.ts:42-53`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/talents/TalentSpell.ts#L42-L53) - Spell loading from 2DA

---

## Items & Properties 2DA Files

### itemprops.2da

**Engine Usage**: Master table defining all item property types available in the game. Each row represents a property type (damage bonuses, ability score bonuses, skill bonuses, etc.) with their cost calculations and effect parameters. The engine uses this file to determine item property costs, effects, and availability.

**Row Index**: Item property ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property label |
| `name` | StrRef | String reference for property name |
| `costtable` | String | Cost calculation table reference |
| `param1` | String | Parameter 1 label |
| `param2` | String | Parameter 2 label |
| `subtype` | Integer | Property subtype identifier |
| `costvalue` | Integer | Base cost value |
| `param1value` | Integer | Parameter 1 default value |
| `param2value` | Integer | Parameter 2 default value |
| `description` | StrRef | Property description string reference |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:135`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L135) - StrRef column definition for itemprops.2da (K1: stringref)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:313`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L313) - StrRef column definition for itemprops.2da (K2: stringref)

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:74`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L74) - HTInstallation.TwoDA_ITEM_PROPERTIES constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/uti.py:107-111`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/uti.py#L107-L111) - itemprops.2da loading in UTI editor
- [`Tools/HolocronToolset/src/toolset/gui/editors/uti.py:278-287`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/uti.py#L278-L287) - itemprops.2da usage for property cost table and parameter lookups
- [`Tools/HolocronToolset/src/toolset/gui/editors/uti.py:449-465`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/uti.py#L449-L465) - itemprops.2da usage in property selection and loading

---

### iprp_feats.2da

**Engine Usage**: Maps item property values to feat bonuses. When an item grants a feat bonus, this table determines which feat is granted based on the property value.

**Row Index**: Item property value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| `feat` | Integer | Feat ID granted by this property value |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:102`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L102) - StrRef column definition for iprp_feats.2da (K1: name)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:280`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L280) - StrRef column definition for iprp_feats.2da (K2: name)

---

### iprp_spells.2da

**Engine Usage**: Maps item property values to spell/Force power grants. Defines on-use and on-hit spell effects for items based on property values. The engine uses this file to determine which spells or Force powers are granted by item properties.

**Row Index**: Item property value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| `spell` | Integer | Spell ID associated with this property value |
| `name` | StrRef | String reference for spell name (K1/K2) |
| `icon` | ResRef | Icon ResRef for the spell (K1/K2) |
| Additional columns | Various | Spell mappings |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:126`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L126) - StrRef column definition for iprp_spells.2da (K1: name)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:218`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L218) - ResRef column definition for iprp_spells.2da (K1: icon)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:304`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L304) - StrRef column definition for iprp_spells.2da (K2: name)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:411`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L411) - ResRef column definition for iprp_spells.2da (K2: icon)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:578`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L578) - GFF field mapping: "CastSpell" -> iprp_spells.2da

---

### iprp_ammocost.2da

**Engine Usage**: Defines ammunition cost per shot for ranged weapons. Used to calculate ammunition consumption rates.

**Row Index**: Ammunition type ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Ammunition type label |
| `cost` | Integer | Ammunition cost per shot |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:92`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L92) - StrRef column definition for iprp_ammocost.2da (K1: name)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:270`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L270) - StrRef column definition for iprp_ammocost.2da (K2: name)

---

### iprp_damagecost.2da

**Engine Usage**: Defines cost calculations for damage bonus item properties. Used to determine item property costs based on damage bonus values.

**Row Index**: Damage bonus value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Damage bonus label |
| `cost` | Integer | Cost for this damage bonus value |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:99`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L99) - StrRef column definition for iprp_damagecost.2da (K1: name)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:277`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L277) - StrRef column definition for iprp_damagecost.2da (K2: name)

---

## Objects & Area 2DA Files

### placeables.2da

**Engine Usage**: Defines placeable objects (containers, usable objects, interactive elements) with their models, properties, and behaviors. The engine uses this file when loading placeable objects in areas, determining their models, hit detection, and interaction properties.

**Row Index**: Placeable type ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String (optional) | Placeable type label |
| `modelname` | ResRef (optional) | 3D model ResRef |
| `strref` | Integer | String reference for placeable name |
| `bodybag` | Boolean | Whether placeable can contain bodies |
| `canseeheight` | Float | Can-see height for line of sight |
| `hitcheck` | Boolean | Whether hit detection is enabled |
| `hostile` | Boolean | Whether placeable is hostile |
| `ignorestatichitcheck` | Boolean | Whether to ignore static hit checks |
| `lightcolor` | String (optional) | Light color RGB values |
| `lightoffsetx` | String (optional) | Light X offset |
| `lightoffsety` | String (optional) | Light Y offset |
| `lightoffsetz` | String (optional) | Light Z offset |
| `lowgore` | String (optional) | Low gore model ResRef |
| `noncull` | Boolean | Whether to disable culling |
| `preciseuse` | Boolean | Whether precise use is enabled |
| `shadowsize` | Boolean | Whether shadow size is enabled |
| `soundapptype` | Integer (optional) | Sound appearance type |
| `usesearch` | Boolean | Whether placeable can be searched |

**Column Details**:

The complete column structure is defined in reone's placeables parser:

- `label`: Optional label string
- `modelname`: 3D model ResRef
- `strref`: String reference for placeable name
- `bodybag`: Boolean - whether placeable can contain bodies
- `canseeheight`: Float - can-see height for line of sight
- `hitcheck`: Boolean - whether hit detection is enabled
- `hostile`: Boolean - whether placeable is hostile
- `ignorestatichitcheck`: Boolean - whether to ignore static hit checks
- `lightcolor`: Optional string - light color RGB values
- `lightoffsetx`: Optional string - light X offset
- `lightoffsety`: Optional string - light Y offset
- `lightoffsetz`: Optional string - light Z offset
- `lowgore`: Optional string - low gore model ResRef
- `noncull`: Boolean - whether to disable culling
- `preciseuse`: Boolean - whether precise use is enabled
- `shadowsize`: Boolean - whether shadow size is enabled
- `soundapptype`: Optional integer - sound appearance type
- `usesearch`: Boolean - whether placeable can be searched

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:141`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L141) - StrRef column definition for placeables.2da (K1: strref)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:170`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L170) - Model ResRef column definition for placeables.2da (K1: modelname)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:319`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L319) - StrRef column definition for placeables.2da (K2: strref)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:349`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L349) - Model ResRef column definition for placeables.2da (K2: modelname)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:467`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L467) - TwoDARegistry.PLACEABLES constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:542`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L542) - GFF field mapping: "Appearance" -> placeables.2da

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:66`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L66) - HTInstallation.TwoDA_PLACEABLES constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/utp.py:52`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utp.py#L52) - placeables.2da cache initialization comment
- [`Tools/HolocronToolset/src/toolset/gui/editors/utp.py:62`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utp.py#L62) - placeables.2da cache loading
- [`Tools/HolocronToolset/src/toolset/gui/editors/utp.py:121-131`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utp.py#L121-L131) - placeables.2da usage in appearance selection combobox
- [`Tools/HolocronToolset/src/toolset/gui/editors/utp.py:471`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utp.py#L471) - placeables.2da usage for model name lookup

**Vendor Implementations:**

- [`vendor/reone/src/libs/resource/parser/2da/placeables.cpp:29-49`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/2da/placeables.cpp#L29-L49) - Complete column parsing implementation with all column names
- [`vendor/reone/src/libs/game/object/placeable.cpp:59-60`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/placeable.cpp#L59-L60) - Placeable loading from 2DA

---

### genericdoors.2da / doortypes.2da

**Engine Usage**: Defines door types with their models, animations, and properties. The engine uses this file when loading doors in areas, determining which model to display and how the door behaves.

**Row Index**: Door type ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Door type label |
| `modelname` | ResRef | 3D model ResRef |
| `name` | String (optional) | Door type name |
| `strref` | Integer (optional) | String reference for door name |
| `blocksight` | Boolean | Whether door blocks line of sight |
| `nobin` | Boolean | Whether door has no bin (container) |
| `preciseuse` | Boolean | Whether precise use is enabled |
| `soundapptype` | Integer (optional) | Sound appearance type |
| `staticanim` | String (optional) | Static animation ResRef |
| `visiblemodel` | Boolean | Whether model is visible |

**Column Details**:

The complete column structure is defined in reone's genericdoors parser:

- `label`: Door type label
- `modelname`: 3D model ResRef
- `name`: Optional door type name string
- `strref`: Optional integer - string reference for door name
- `blocksight`: Boolean - whether door blocks line of sight
- `nobin`: Boolean - whether door has no bin (container)
- `preciseuse`: Boolean - whether precise use is enabled
- `soundapptype`: Optional integer - sound appearance type
- `staticanim`: Optional string - static animation ResRef
- `visiblemodel`: Boolean - whether model is visible

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:78`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L78) - StrRef column definition for doortypes.2da (K1: stringrefgame)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:86`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L86) - StrRef column definition for genericdoors.2da (K1: strref)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:177`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L177) - Model ResRef column definition for doortypes.2da (K1: model)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:178`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L178) - Model ResRef column definition for genericdoors.2da (K1: modelname)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:256`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L256) - StrRef column definition for doortypes.2da (K2: stringrefgame)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:264`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L264) - StrRef column definition for genericdoors.2da (K2: strref)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:356`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L356) - Model ResRef column definition for doortypes.2da (K2: model)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:357`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L357) - Model ResRef column definition for genericdoors.2da (K2: modelname)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:468`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L468) - TwoDARegistry.DOORS constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:543`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L543) - GFF field mapping: "GenericType" -> genericdoors.2da

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:67`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L67) - HTInstallation.TwoDA_DOORS constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/utd.py:60`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utd.py#L60) - genericdoors.2da cache loading
- [`Tools/HolocronToolset/src/toolset/gui/editors/utd.py:117-123`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utd.py#L117-L123) - genericdoors.2da usage in appearance selection combobox
- [`Tools/HolocronToolset/src/toolset/gui/editors/utd.py:409`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utd.py#L409) - genericdoors.2da usage for model name lookup

**Vendor Implementations:**

- [`vendor/reone/src/libs/resource/parser/2da/genericdoors.cpp:29-41`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/2da/genericdoors.cpp#L29-L41) - Complete column parsing implementation with all column names
- [`vendor/reone/src/libs/game/object/door.cpp:66-67`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/door.cpp#L66-L67) - Door loading from 2DA

---

### soundset.2da

**Engine Usage**: Maps sound set IDs to voice set assignments for characters. The engine uses this file to determine which voice lines to play for characters based on their sound set.

**Row Index**: Sound set ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Sound set label |
| `resref` | ResRef | Sound set file ResRef (e.g., `c_human_m_01`) |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:143`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L143) - StrRef column definition for soundset.2da (K1: strref)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:321`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L321) - StrRef column definition for soundset.2da (K2: strref)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:459`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L459) - TwoDARegistry.SOUNDSETS constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:522`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L522) - GFF field mapping: "SoundSetFile" -> soundset.2da
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:90-92`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L90-L92) - UTC soundset_id field documentation
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:359`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L359) - UTC soundset_id field initialization
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:549-550`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L549-L550) - SoundSetFile field parsing from UTC GFF
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:821`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L821) - SoundSetFile field writing to UTC GFF

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:58`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L58) - HTInstallation.TwoDA_SOUNDSETS constant
- [`Tools/HolocronToolset/src/ui/editors/utc.ui:260-267`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/ui/editors/utc.ui#L260-L267) - Soundset selection combobox in UTC editor UI

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/object/creature.cpp:1347-1354`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/creature.cpp#L1347-L1354) - Sound set loading from 2DA

---

## Visual Effects & Animations 2DA Files

### visualeffects.2da

**Engine Usage**: Defines visual effects (particle effects, impact effects, environmental effects) with their durations, models, and properties. The engine uses this file when playing visual effects for spells, combat, and environmental events.

**Row Index**: Visual effect ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Visual effect label |
| `name` | StrRef | String reference for effect name |
| `model` | ResRef (optional) | Effect model ResRef |
| `impactmodel` | ResRef (optional) | Impact model ResRef |
| `impactorient` | Integer | Impact orientation |
| `impacttype` | Integer | Impact type identifier |
| `duration` | Float | Effect duration in seconds |
| `durationvariance` | Float | Duration variance |
| `loop` | Boolean | Whether effect loops |
| `render` | Boolean | Whether effect is rendered |
| `renderhint` | Integer | Render hint flags |
| `sound` | ResRef (optional) | Sound effect ResRef |
| `sounddelay` | Float | Sound delay in seconds |
| `soundvariance` | Float | Sound variance |
| `soundloop` | Boolean | Whether sound loops |
| `soundvolume` | Float | Sound volume (0.0-1.0) |
| `light` | Boolean | Whether effect emits light |
| `lightcolor` | String | Light color RGB values |
| `lightintensity` | Float | Light intensity |
| `lightradius` | Float | Light radius |
| `lightpulse` | Boolean | Whether light pulses |
| `lightpulselength` | Float | Light pulse length |
| `lightfade` | Boolean | Whether light fades |
| `lightfadelength` | Float | Light fade length |
| `lightfadestart` | Float | Light fade start time |
| `lightfadeend` | Float | Light fade end time |
| `lightshadow` | Boolean | Whether light casts shadows |
| `lightshadowradius` | Float | Light shadow radius |
| `lightshadowintensity` | Float | Light shadow intensity |
| `lightshadowcolor` | String | Light shadow color RGB values |
| `lightshadowfade` | Boolean | Whether light shadow fades |
| `lightshadowfadelength` | Float | Light shadow fade length |
| `lightshadowfadestart` | Float | Light shadow fade start time |
| `lightshadowfadeend` | Float | Light shadow fade end time |
| `lightshadowpulse` | Boolean | Whether light shadow pulses |
| `lightshadowpulselength` | Float | Light shadow pulse length |
| `lightshadowpulseintensity` | Float | Light shadow pulse intensity |
| `lightshadowpulsecolor` | String | Light shadow pulse color RGB values |
| `lightshadowpulsefade` | Boolean | Whether light shadow pulse fades |
| `lightshadowpulsefadelength` | Float | Light shadow pulse fade length |
| `lightshadowpulsefadestart` | Float | Light shadow pulse fade start time |
| `lightshadowpulsefadeend` | Float | Light shadow pulse fade end time |
| `lightshadowpulsefadeintensity` | Float | Light shadow pulse fade intensity |
| `lightshadowpulsefadecolor` | String | Light shadow pulse fade color RGB values |
| `lightshadowpulsefadepulse` | Boolean | Whether light shadow pulse fade pulses |
| `lightshadowpulsefadepulselength` | Float | Light shadow pulse fade pulse length |
| `lightshadowpulsefadepulseintensity` | Float | Light shadow pulse fade pulse intensity |
| `lightshadowpulsefadepulsecolor` | String | Light shadow pulse fade pulse color RGB values |
| `lightshadowpulsefadepulsefade` | Boolean | Whether light shadow pulse fade pulse fades |
| `lightshadowpulsefadepulsefadelength` | Float | Light shadow pulse fade pulse fade length |
| `lightshadowpulsefadepulsefadestart` | Float | Light shadow pulse fade pulse fade start time |
| `lightshadowpulsefadepulsefadeend` | Float | Light shadow pulse fade pulse fade end time |
| `lightshadowpulsefadepulsefadeintensity` | Float | Light shadow pulse fade pulse fade intensity |
| `lightshadowpulsefadepulsefadecolor` | String | Light shadow pulse fade pulse fade color RGB values |

**Note**: The `visualeffects.2da` file may contain many optional columns for advanced lighting and shadow effects.

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:593`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L593) - GFF field mapping: "VisualType" -> visualeffects.2da

---

### portraits.2da

**Engine Usage**: Maps portrait IDs to portrait image ResRefs for character selection screens and character sheets. The engine uses this file to display character portraits in the UI.

**Row Index**: Portrait ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Portrait label |
| `baseresref` | ResRef | Base portrait image ResRef |
| `appearancenumber` | Integer | Associated appearance ID |
| `appearance_s` | Integer | Small appearance ID |
| `appearance_l` | Integer | Large appearance ID |
| `forpc` | Boolean | Whether portrait is for player character |
| `sex` | Integer | Gender (0=male, 1=female) |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:455`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L455) - TwoDARegistry.PORTRAITS constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:523`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L523) - GFF field mapping: "PortraitId" -> portraits.2da
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:66`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L66) - Party portraits documentation comment
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:226-228`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L226-L228) - Portrait rotation logic documentation
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:241`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L241) - Party portraits field documentation
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:391`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L391) - Portraits parsing comment
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:456`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L456) - Portraits writing comment
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:2157`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L2157) - SAVENFO.res portraits documentation
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:2309`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L2309) - Party portraits documentation
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:2370`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L2370) - Portrait debug print

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:54`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L54) - HTInstallation.TwoDA_PORTRAITS constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/utc.py:140-152`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utc.py#L140-L152) - portraits.2da usage for portrait selection with alignment-based variant selection (baseresref, baseresrefe, baseresrefve, baseresrefvve, baseresrefvvve)
- [`Tools/HolocronToolset/src/ui/editors/utc.ui:407`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/ui/editors/utc.ui#L407) - Portrait selection combobox in UTC editor UI
- [`Tools/HolocronToolset/src/toolset/gui/editors/savegame.py:51`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/savegame.py#L51) - Portraits documentation in save game editor
- [`Tools/HolocronToolset/src/ui/editors/savegame.ui:94-98`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/ui/editors/savegame.ui#L94-L98) - Portraits group box in save game editor UI

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/portraits.cpp:33-51`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/portraits.cpp#L33-L51) - Portrait loading from 2DA with all column access

---

### heads.2da

**Engine Usage**: Defines head models and textures for player characters and NPCs. The engine uses this file when loading character heads, determining which 3D model and textures to apply.

**Row Index**: Head ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `head` | ResRef (optional) | Head model ResRef |
| `headtexe` | ResRef (optional) | Head texture E ResRef |
| `headtexg` | ResRef (optional) | Head texture G ResRef |
| `headtexve` | ResRef (optional) | Head texture VE ResRef |
| `headtexvg` | ResRef (optional) | Head texture VG ResRef |
| `headtexvve` | ResRef (optional) | Head texture VVE ResRef |
| `headtexvvve` | ResRef (optional) | Head texture VVVE ResRef |
| `alttexture` | ResRef (optional) | Alternative texture ResRef |

**Column Details**:

The complete column structure is defined in reone's heads parser:

- `head`: Optional ResRef - head model ResRef
- `alttexture`: Optional ResRef - alternative texture ResRef
- `headtexe`: Optional ResRef - head texture for evil alignment
- `headtexg`: Optional ResRef - head texture for good alignment
- `headtexve`: Optional ResRef - head texture for very evil alignment
- `headtexvg`: Optional ResRef - head texture for very good alignment
- `headtexvve`: Optional ResRef - head texture for very very evil alignment
- `headtexvvve`: Optional ResRef - head texture for very very very evil alignment

**References**:

- [`vendor/reone/src/libs/resource/parser/2da/heads.cpp:29-39`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/2da/heads.cpp#L29-L39) - Complete column parsing implementation with all column names
- [`vendor/reone/src/libs/game/object/creature.cpp:1223-1228`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/creature.cpp#L1223-L1228) - Head loading from 2DA

---

## Progression Tables 2DA Files

### classpowergain.2da

**Engine Usage**: Defines Force power progression by class and level. The engine uses this file to determine which Force powers are available to each class at each level.

**Row Index**: Level (integer, typically 1-20)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `level` | Integer | Character level |
| `jedi_guardian` | Integer | Jedi Guardian power gain |
| `jedi_consular` | Integer | Jedi Consular power gain |
| `jedi_sentinel` | Integer | Jedi Sentinel power gain |
| `soldier` | Integer | Soldier power gain |
| `scout` | Integer | Scout power gain |
| `scoundrel` | Integer | Scoundrel power gain |
| `jedi_guardian_prestige` | Integer (optional) | Jedi Guardian prestige power gain |
| `jedi_consular_prestige` | Integer (optional) | Jedi Consular prestige power gain |
| `jedi_sentinel_prestige` | Integer (optional) | Jedi Sentinel prestige power gain |

---

### cls_atk_*.2da

**Engine Usage**: Base attack bonus progression tables for each class. Files are named `cls_atk_<classname>.2da` (e.g., `cls_atk_jedi_guardian.2da`). The engine uses these files to calculate attack bonuses for each class at each level.

**Row Index**: Level (integer, typically 1-20)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `level` | Integer | Character level |
| `attackbonus` | Integer | Base attack bonus at this level |

---

### cls_savthr_*.2da

**Engine Usage**: Saving throw progression tables for each class. Files are named `cls_savthr_<classname>.2da` (e.g., `cls_savthr_jedi_guardian.2da`). The engine uses these files to calculate saving throw bonuses for each class at each level.

**Row Index**: Level (integer, typically 1-20)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `level` | Integer | Character level |
| `fortitude` | Integer | Fortitude save bonus |
| `reflex` | Integer | Reflex save bonus |
| `will` | Integer | Will save bonus |

---

## Name Generation 2DA Files

### humanfirst.2da / humanlast.2da

**Engine Usage**: Random name generation tables for human characters during character creation. The engine uses these files to generate random first and last names for human characters.

**Row Index**: Name index (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `name` | String | Name string |

---

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

**Engine Usage**: Defines ambient music tracks for areas. The engine uses this file to determine which music to play in different areas based on area properties.

**Row Index**: Music ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Music label |
| `music` | ResRef | Music file ResRef |
| `resource` | ResRef | Music resource ResRef |
| `stinger1`, `stinger2`, `stinger3` | ResRef (optional) | Stinger music ResRefs |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:206`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L206) - Music ResRef column definitions for ambientmusic.2da (K1: resource, stinger1, stinger2, stinger3)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:398`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L398) - Music ResRef column definitions for ambientmusic.2da (K2: resource, stinger1, stinger2, stinger3)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:545-548`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L545-L548) - GFF field mapping: "MusicDay", "MusicNight", "MusicBattle", "MusicDelay" -> ambientmusic.2da

---

### ambientsound.2da

**Engine Usage**: Defines ambient sound effects for areas. The engine uses this file to play ambient sounds in areas.

**Row Index**: Sound ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Sound label |
| `sound` | ResRef | Sound file ResRef |
| `resource` | ResRef | Sound resource ResRef |
| `description` | StrRef | Sound description string reference |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:72`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L72) - StrRef column definition for ambientsound.2da (K1: description)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:184`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L184) - Sound ResRef column definition for ambientsound.2da (K1: resource)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:247`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L247) - StrRef column definition for ambientsound.2da (K2: description)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:376`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L376) - Sound ResRef column definition for ambientsound.2da (K2: resource)
- [`Libraries/PyKotor/src/pykotor/common/scriptdefs.py:6986-6988`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/common/scriptdefs.py#L6986-L6988) - AmbientSoundPlay function comment

---

### ammunitiontypes.2da

**Engine Usage**: Defines ammunition types for ranged weapons, including their models and sound effects. The engine uses this file when loading items to determine ammunition properties for ranged weapons.

**Row Index**: Ammunition Type ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Ammunition type label |
| `model` | ResRef | Ammunition model ResRef |
| `shotsound0` | ResRef (optional) | Shot sound effect ResRef (variant 1) |
| `shotsound1` | ResRef (optional) | Shot sound effect ResRef (variant 2) |
| `impactsound0` | ResRef (optional) | Impact sound effect ResRef (variant 1) |
| `impactsound1` | ResRef (optional) | Impact sound effect ResRef (variant 2) |

**References**:

- [`vendor/reone/src/libs/game/object/item.cpp:164-171`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/item.cpp#L164-L171) - Ammunition type loading from 2DA

---

### camerastyle.2da

**Engine Usage**: Defines camera styles for areas, including distance, pitch, view angle, and height settings. The engine uses this file to configure camera behavior in different areas.

**Row Index**: Camera Style ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Camera style label |
| `name` | String | Camera style name |
| `distance` | Float | Camera distance from target |
| `pitch` | Float | Camera pitch angle |
| `viewangle` | Float | Camera view angle |
| `height` | Float | Camera height offset |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:497`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L497) - TwoDARegistry.CAMERAS constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:550`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L550) - GFF field mapping: "CameraStyle" -> camerastyle.2da
- [`Libraries/PyKotor/src/pykotor/resource/generics/are.py:37`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/are.py#L37) - ARE camera_style field documentation
- [`Libraries/PyKotor/src/pykotor/resource/generics/are.py:123`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/are.py#L123) - Camera style index comment
- [`Libraries/PyKotor/src/pykotor/resource/generics/are.py:442`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/are.py#L442) - CameraStyle field parsing from ARE GFF
- [`Libraries/PyKotor/src/pykotor/resource/generics/are.py:579`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/are.py#L579) - CameraStyle field writing to ARE GFF

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:96`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L96) - HTInstallation.TwoDA_CAMERAS constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/are.py:102`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/are.py#L102) - camerastyle.2da loading in ARE editor

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/camerastyles.cpp:29-42`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/camerastyles.cpp#L29-L42) - Camera style loading from 2DA
- [`vendor/reone/src/libs/game/object/area.cpp:140-148`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/area.cpp#L140-L148) - Camera style usage in areas

---

### footstepsounds.2da

**Engine Usage**: Defines footstep sound effects for different surface types and footstep types. The engine uses this file to play appropriate footstep sounds based on the surface material and creature footstep type.

**Row Index**: Footstep Type ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Footstep type label |
| `dirt0`, `dirt1`, `dirt2` | ResRef (optional) | Dirt surface footstep sounds |
| `grass0`, `grass1`, `grass2` | ResRef (optional) | Grass surface footstep sounds |
| `stone0`, `stone1`, `stone2` | ResRef (optional) | Stone surface footstep sounds |
| `wood0`, `wood1`, `wood2` | ResRef (optional) | Wood surface footstep sounds |
| `water0`, `water1`, `water2` | ResRef (optional) | Water surface footstep sounds |
| `carpet0`, `carpet1`, `carpet2` | ResRef (optional) | Carpet surface footstep sounds |
| `metal0`, `metal1`, `metal2` | ResRef (optional) | Metal surface footstep sounds |
| `leaves0`, `leaves1`, `leaves2` | ResRef (optional) | Leaves surface footstep sounds |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:188-198`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L188-L198) - Sound ResRef column definitions for footstepsounds.2da (K1: rolling, dirt0-2, grass0-2, stone0-2, wood0-2, water0-2, carpet0-2, metal0-2, puddles0-2, leaves0-2, force1-3)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:380-390`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L380-L390) - Sound ResRef column definitions for footstepsounds.2da (K2: rolling, dirt0-2, grass0-2, stone0-2, wood0-2, water0-2, carpet0-2, metal0-2, puddles0-2, leaves0-2, force1-3)

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/footstepsounds.cpp:31-57`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/footstepsounds.cpp#L31-L57) - Footstep sounds loading from 2DA
- [`vendor/reone/src/libs/game/object/creature.cpp:106`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/creature.cpp#L106) - Footstep type usage from appearance.2da

---

### prioritygroups.2da

**Engine Usage**: Defines priority groups for sound effects, determining which sounds take precedence when multiple sounds are playing. The engine uses this file to calculate sound priority values.

**Row Index**: Priority Group ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Priority group label |
| `priority` | Integer | Priority value (higher = more important) |

**References**:

- [`vendor/reone/src/libs/game/object/sound.cpp:92-96`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/sound.cpp#L92-L96) - Priority group loading from 2DA

---

### repute.2da

**Engine Usage**: Defines reputation values between different factions. The engine uses this file to determine whether creatures are enemies, friends, or neutral to each other based on their faction relationships.

**Row Index**: Faction ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Faction label |
| Additional columns | Integer | Reputation values for each faction (column names match faction labels) |

**Note**: The `repute.2da` file is a square matrix where each row represents a faction, and each column (after `label`) represents the reputation value toward another faction. Reputation values typically range from 0-100, where values below 50 are enemies, above 50 are friends, and 50 is neutral.

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:460`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L460) - TwoDARegistry.FACTIONS constant definition (maps to "repute")
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:526-527`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L526-L527) - GFF field mapping: "FactionID" and "Faction" -> repute.2da
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:92`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L92) - REPUTE.fac documentation comment
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:1593`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L1593) - REPUTE.fac file check comment
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:1627`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L1627) - REPUTE.fac documentation
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:1667`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L1667) - REPUTE_IDENTIFIER constant definition
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:1683-1684`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L1683-L1684) - repute GFF field initialization
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:1759-1761`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L1759-L1761) - REPUTE.fac parsing
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:1795-1796`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L1795-L1796) - REPUTE.fac writing

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:59`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L59) - HTInstallation.TwoDA_FACTIONS constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/utc.py:239`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utc.py#L239) - repute.2da included in batch cache for UTC editor
- [`Tools/HolocronToolset/src/toolset/gui/editors/utc.py:253-280`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utc.py#L253-L280) - repute.2da usage in faction selection combobox
- [`Tools/HolocronToolset/src/toolset/gui/editors/utp.py:121-128`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utp.py#L121-L128) - repute.2da usage in UTP editor
- [`Tools/HolocronToolset/src/toolset/gui/editors/utd.py:117-124`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utd.py#L117-L124) - repute.2da usage in UTD editor
- [`Tools/HolocronToolset/src/toolset/gui/editors/ute.py:106-109`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/ute.py#L106-L109) - repute.2da usage in UTE editor
- [`Tools/HolocronToolset/src/toolset/gui/editors/utt.py:72-78`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utt.py#L72-L78) - repute.2da usage in UTT editor

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/reputes.cpp:36-62`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/reputes.cpp#L36-L62) - Repute matrix loading from 2DA

---

### surfacemat.2da

**Engine Usage**: Defines surface material properties for walkmesh surfaces, including walkability, line of sight blocking, and grass rendering. The engine uses this file to determine surface behavior during pathfinding and rendering.

**Row Index**: Surface Material ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Surface material label |
| `walk` | Boolean | Whether surface is walkable |
| `walkcheck` | Boolean | Whether walk check applies |
| `lineofsight` | Boolean | Whether surface blocks line of sight |
| `grass` | Boolean | Whether surface has grass rendering |
| `sound` | String | Sound type identifier for footstep sounds |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/resource/formats/mdl/io_mdl.py:21`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/mdl/io_mdl.py#L21) - SurfaceMaterial import
- [`Libraries/PyKotor/src/pykotor/resource/formats/mdl/mdl_types.py:9`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/mdl/mdl_types.py#L9) - SurfaceMaterial import
- [`Libraries/PyKotor/src/pykotor/resource/formats/mdl/mdl_types.py:412`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/mdl/mdl_types.py#L412) - SurfaceMaterial.GRASS default value
- [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:47`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L47) - SurfaceMaterial ID per face documentation
- [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:784`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L784) - SurfaceMaterial ID field documentation
- [`Libraries/PyKotor/src/pykotor/resource/formats/mdl/mdl_data.py:1578`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/mdl/mdl_data.py#L1578) - Comment referencing surfacemat.2da for walkmesh surface material
- [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py:160`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py#L160) - SurfaceMaterial parsing from BWM

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/surfaces.cpp:29-44`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/surfaces.cpp#L29-L44) - Surface material loading from 2DA

---

### loadscreenhints.2da

**Engine Usage**: Defines loading screen hints displayed during area transitions. The engine uses this file to show helpful tips and hints to players while loading.

**Row Index**: Loading Screen Hint ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Hint label |
| `strref` | StrRef | String reference for hint text |

**References**:

- [`vendor/xoreos/src/engines/kotor/gui/loadscreen/loadscreen.cpp:45`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotor/gui/loadscreen/loadscreen.cpp#L45) - Loading screen hints TODO comment (KotOR-specific)

---

### bodybag.2da

**Engine Usage**: Defines body bag appearances for creatures when they die. The engine uses this file to determine which appearance to use for the body bag container that appears when a creature is killed.

**Row Index**: Body Bag ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Body bag label |
| `name` | StrRef | String reference for body bag name |
| `appearance` | Integer | Appearance ID for the body bag model |
| `corpse` | Boolean | Whether the body bag represents a corpse |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:536`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L536) - GFF field mapping: "BodyBag" -> bodybag.2da
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:296-298`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L296-L298) - UTC bodybag_id field documentation (not used by game engine)
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:438`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L438) - UTC bodybag_id field initialization
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:555-556`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L555-L556) - BodyBag field parsing from UTC GFF (deprecated)
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:944`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L944) - BodyBag field writing to UTC GFF
- [`Libraries/PyKotor/src/pykotor/resource/generics/utp.py:105`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utp.py#L105) - UTP bodybag_id field documentation
- [`Libraries/PyKotor/src/pykotor/resource/generics/utp.py:179`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utp.py#L179) - UTP bodybag_id field initialization
- [`Libraries/PyKotor/src/pykotor/resource/generics/utp.py:254`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utp.py#L254) - BodyBag field parsing from UTP GFF
- [`Libraries/PyKotor/src/pykotor/resource/generics/utp.py:341`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utp.py#L341) - BodyBag field writing to UTP GFF

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/object/creature.cpp:1357-1366`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/creature.cpp#L1357-L1366) - Body bag loading from 2DA

---

### ranges.2da

**Engine Usage**: Defines perception ranges for creatures, including sight and hearing ranges. The engine uses this file to determine how far creatures can see and hear.

**Row Index**: Range ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Range label |
| `primaryrange` | Float | Primary perception range (sight range) |
| `secondaryrange` | Float | Secondary perception range (hearing range) |

**References**:

- [`vendor/reone/src/libs/game/object/creature.cpp:1398-1406`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/creature.cpp#L1398-L1406) - Perception range loading from 2DA
- [`vendor/KotOR.js/src/module/ModuleCreature.ts:3178-3187`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleCreature.ts#L3178-L3187) - Perception range access from 2DA

---

### regeneration.2da

**Engine Usage**: Defines regeneration rates for creatures in combat and non-combat states. The engine uses this file to determine how quickly creatures regenerate hit points and Force points.

**Row Index**: Regeneration State ID (integer, 0=combat, 1=non-combat)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Regeneration state label |
| Additional columns | Float | Regeneration rates for different resource types |

**References**:

- [`vendor/KotOR.js/src/module/ModuleCreature.ts:759`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleCreature.ts#L759) - Regeneration rate loading from 2DA

---

### animations.2da

**Engine Usage**: Defines animation names and properties for creatures and objects. The engine uses this file to map animation IDs to animation names for playback.

**Row Index**: Animation ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Animation label |
| `name` | String | Animation name (used to look up animation in model) |

**References**:

- [`vendor/KotOR.js/src/module/ModuleCreature.ts:1474-1482`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleCreature.ts#L1474-L1482) - Animation lookup from 2DA
- [`vendor/KotOR.js/src/module/ModulePlaceable.ts:1063-1103`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModulePlaceable.ts#L1063-L1103) - Placeable animation lookup from 2DA
- [`vendor/KotOR.js/src/module/ModuleDoor.ts:1343-1365`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleDoor.ts#L1343-L1365) - Door animation lookup from 2DA

---

### combatanimations.2da

**Engine Usage**: Defines combat-specific animation properties and mappings. The engine uses this file to determine which animations to play during combat actions.

**Row Index**: Combat Animation ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Combat animation label |
| Additional columns | Various | Combat animation properties |

**References**:

- [`vendor/KotOR.js/src/module/ModuleCreature.ts:1482`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleCreature.ts#L1482) - Combat animation lookup from 2DA

---

### weaponsounds.2da

**Engine Usage**: Defines sound effects for weapon attacks based on base item type. The engine uses this file to play appropriate weapon sounds during combat.

**Row Index**: Base Item ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Base item label |
| Additional columns | ResRef | Sound effect ResRefs for different attack types |

**References**:

- [`vendor/KotOR.js/src/module/ModuleCreature.ts:1819-1822`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleCreature.ts#L1819-L1822) - Weapon sound lookup from 2DA

---

### placeableobjsnds.2da

**Engine Usage**: Defines sound effects for placeable objects based on sound appearance type. The engine uses this file to play appropriate sounds when interacting with placeables.

**Row Index**: Sound Appearance Type ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Sound appearance type label |
| Additional columns | ResRef | Sound effect ResRefs for different interaction types |

**References**:

- [`vendor/KotOR.js/src/module/ModulePlaceable.ts:387-389`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModulePlaceable.ts#L387-L389) - Placeable sound lookup from 2DA
- [`vendor/KotOR.js/src/module/ModuleDoor.ts:239-241`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleDoor.ts#L239-L241) - Door sound lookup from 2DA

---

### creaturespeed.2da

**Engine Usage**: Defines movement speed rates for creatures based on walk rate ID. The engine uses this file to determine walking and running speeds.

**Row Index**: Walk Rate ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Walk rate label |
| `walkrate` | Float | Walking speed rate |
| `runrate` | Float | Running speed rate |

**References**:

- [`vendor/KotOR.js/src/module/ModuleCreature.ts:2875-2887`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleCreature.ts#L2875-L2887) - Creature speed lookup from 2DA

---

### exptable.2da

**Engine Usage**: Defines experience point requirements for each character level. The engine uses this file to determine when a character levels up based on accumulated experience.

**Row Index**: Level (integer, typically 1-20)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Level label |
| Additional columns | Integer | Experience point requirements for leveling up |

**References**:

- [`vendor/KotOR.js/src/module/ModuleCreature.ts:2926-2941`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleCreature.ts#L2926-L2941) - Experience table lookup from 2DA

---

### guisounds.2da

**Engine Usage**: Defines sound effects for GUI interactions (button clicks, mouse enter events, etc.). The engine uses this file to play appropriate sounds when the player interacts with UI elements.

**Row Index**: Sound ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Sound label (e.g., "Clicked_Default", "Entered_Default") |
| `soundresref` | ResRef | Sound effect ResRef |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:200`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L200) - Sound ResRef column definition for guisounds.2da (K1: soundresref)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:392`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L392) - Sound ResRef column definition for guisounds.2da (K2: soundresref)

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/gui/sounds.cpp:31-45`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/gui/sounds.cpp#L31-L45) - GUI sound loading from 2DA

---

### dialoganimations.2da

**Engine Usage**: Maps dialog animation ordinals to animation names for use in conversations. The engine uses this file to determine which animation to play when a dialog line specifies an animation ordinal.

**Row Index**: Animation Index (integer, ordinal - 10000)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Animation label |
| `name` | String | Animation name (used to look up animation in model) |

**References**:

- [`vendor/reone/src/libs/game/gui/dialog.cpp:302-315`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/gui/dialog.cpp#L302-L315) - Dialog animation lookup from 2DA

---

### tilecolor.2da

**Engine Usage**: Defines tile colors for walkmesh rendering. The engine uses this file to determine color values for different walkmesh tiles.

**Row Index**: Tile Color ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Tile color label |
| Additional columns | Various | Color values and properties |

**References**:

- [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:618-626`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L618-L626) - Tile color loading from 2DA

---

### forceshields.2da

**Engine Usage**: Defines Force shield visual effects and properties. The engine uses this file to determine which visual effect to display when a Force shield is active.

**Row Index**: Force Shield ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Force shield label |
| Additional columns | Various | Force shield visual effect properties |

**References**:

- [`vendor/KotOR.js/src/nwscript/NWScriptDefK1.ts:5552`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptDefK1.ts#L5552) - Force shield lookup from 2DA

---

### plot.2da

**Engine Usage**: Defines journal/quest entries with their experience point rewards and labels. The engine uses this file to manage quest tracking, journal entries, and experience point calculations for quest completion.

**Row Index**: Plot ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Plot/quest label (used as quest identifier) |
| `xp` | Integer | Experience points awarded for quest completion |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:123-125`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L123-L125) - UTC plot field documentation
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:375`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L375) - UTC plot field initialization
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:579-580`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L579-L580) - Plot field parsing from UTC GFF
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:839`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L839) - Plot field writing to UTC GFF
- [`Libraries/PyKotor/src/pykotor/resource/generics/uti.py:71-73`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/uti.py#L71-L73) - UTI plot field documentation
- [`Libraries/PyKotor/src/pykotor/resource/generics/uti.py:129`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/uti.py#L129) - UTI plot field initialization
- [`Libraries/PyKotor/src/pykotor/resource/generics/uti.py:256-258`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/uti.py#L256-L258) - Plot field parsing from UTI GFF
- [`Libraries/PyKotor/src/pykotor/resource/generics/uti.py:339`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/uti.py#L339) - Plot field writing to UTI GFF
- [`Libraries/PyKotor/src/pykotor/resource/generics/dlg/io/gff.py:89-92`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/dlg/io/gff.py#L89-L92) - Dialog node PlotIndex and PlotXPPercentage field parsing

**Vendor Implementations:**

- [`vendor/KotOR.js/src/managers/JournalManager.ts:58-64`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/managers/JournalManager.ts#L58-L64) - Plot/quest experience lookup from 2DA
- [`vendor/KotOR.js/src/managers/JournalManager.ts:101-104`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/managers/JournalManager.ts#L101-L104) - Plot existence check from 2DA
- [`vendor/KotOR.js/src/nwscript/NWScriptDefK1.ts:7845-7848`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptDefK1.ts#L7845-L7848) - Plot table access for quest experience

---

### traps.2da

**Engine Usage**: Defines trap properties including models, sounds, and scripts. The engine uses this file when loading triggers with trap types to determine trap appearance and behavior.

**Row Index**: Trap Type ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Trap type label |
| `name` | StrRef | String reference for trap name |
| `model` | ResRef | Trap model ResRef |
| `explosionsound` | ResRef | Explosion sound effect ResRef |
| `resref` | ResRef | Trap script ResRef |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:150`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L150) - StrRef column definitions for traps.2da (K1: trapname, name)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:328`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L328) - StrRef column definitions for traps.2da (K2: trapname, name)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:470`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L470) - TwoDARegistry.TRAPS constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:568`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L568) - GFF field mapping: "TrapType" -> traps.2da
- [`Libraries/PyKotor/src/pykotor/common/scriptdefs.py:6347-6348`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/common/scriptdefs.py#L6347-L6348) - VersusTrapEffect function comments
- [`Libraries/PyKotor/src/pykotor/common/scriptdefs.py:7975-7976`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/common/scriptdefs.py#L7975-L7976) - GetLastHostileActor function comment mentioning traps
- [`Libraries/PyKotor/src/pykotor/common/scriptlib.py:21692`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/common/scriptlib.py#L21692) - Trap targeting comment

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:69`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L69) - HTInstallation.TwoDA_TRAPS constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/utt.py:73-87`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utt.py#L73-L87) - traps.2da loading and usage in trap type selection combobox
- [`Tools/HolocronToolset/src/toolset/gui/editors/utt.py:167`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utt.py#L167) - traps.2da usage for setting trap type index
- [`Tools/HolocronToolset/src/toolset/gui/editors/utt.py:216`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utt.py#L216) - traps.2da usage for getting trap type index
- [`Tools/HolocronToolset/src/ui/editors/utt.ui:252`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/ui/editors/utt.ui#L252) - Trap selection combobox in UTT editor UI

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/object/trigger.cpp:75-78`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/trigger.cpp#L75-L78) - Trap type loading from 2DA
- [`vendor/KotOR.js/src/module/ModuleTrigger.ts:605-611`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleTrigger.ts#L605-L611) - Trap loading from 2DA
- [`vendor/KotOR.js/src/module/ModuleObject.ts:1822`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleObject.ts#L1822) - Trap lookup from 2DA

---

### modulesave.2da

**Engine Usage**: Defines which modules should be included in save games. The engine uses this file to determine whether a module's state should be persisted when saving the game.

**Row Index**: Module Index (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Module label |
| `modulename` | String | Module filename (e.g., "001ebo") |
| `includeInSave` | Boolean | Whether module state should be saved (0 = false, 1 = true) |

**References**:

- [`vendor/KotOR.js/src/module/Module.ts:663-669`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/Module.ts#L663-L669) - Module save inclusion check from 2DA

---

### tutorial.2da

**Engine Usage**: Defines tutorial window tracking entries. The engine uses this file to track which tutorial windows have been shown to the player.

**Row Index**: Tutorial ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Tutorial label |
| Additional columns | Various | Tutorial window properties |

**References**:

- [`vendor/KotOR.js/src/managers/PartyManager.ts:180-187`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/managers/PartyManager.ts#L180-L187) - Tutorial window tracker initialization from 2DA
- [`vendor/KotOR.js/src/managers/PartyManager.ts:438`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/managers/PartyManager.ts#L438) - Tutorial table access

---

### globalcat.2da

**Engine Usage**: Defines global variables and their types for the game engine. The engine uses this file to initialize global variables at game start, determining which variables are integers, floats, or strings.

**Row Index**: Global Variable Index (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Global variable label |
| `name` | String | Global variable name |
| `type` | String | Variable type ("Number", "Boolean", "String", etc.) |

**References**:

- [`vendor/NorthernLights/Assets/Scripts/Systems/StateSystem.cs:282-294`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/Systems/StateSystem.cs#L282-L294) - Global variable initialization from 2DA

---

### subrace.2da

**Engine Usage**: Defines subrace types for character creation and creature templates. The engine uses this file to determine subrace properties and restrictions.

**Row Index**: Subrace ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Subrace label |
| Additional columns | Various | Subrace properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:457`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L457) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:56`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L56) - HTInstallation constant

---

### gender.2da

**Engine Usage**: Defines gender types for character creation and creature templates. The engine uses this file to determine gender-specific properties and restrictions.

**Row Index**: Gender ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Gender label |
| Additional columns | Various | Gender properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:461`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L461) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:60`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L60) - HTInstallation constant

---

### racialtypes.2da

**Engine Usage**: Defines racial types for character creation and creature templates. The engine uses this file to determine race-specific properties, restrictions, and bonuses.

**Row Index**: Race ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Race label |
| Additional columns | Various | Race properties and bonuses |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:471`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L471) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:70`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L70) - HTInstallation constant

---

### upgrade.2da

**Engine Usage**: Defines item upgrade types and properties. The engine uses this file to determine which upgrades can be applied to items and their effects.

**Row Index**: Upgrade Type ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Upgrade type label |
| Additional columns | Various | Upgrade properties and effects |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:473`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L473) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:72`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L72) - HTInstallation constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/uti.py:632-639`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/uti.py#L632-L639) - Upgrade selection in item editor

---

### encdifficulty.2da

**Engine Usage**: Defines encounter difficulty levels for area encounters. The engine uses this file to determine encounter scaling and difficulty modifiers.

**Row Index**: Difficulty ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Difficulty label |
| Additional columns | Various | Difficulty modifiers and properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:474`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L474) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:73`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L73) - HTInstallation constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/ute.py:101-104`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/ute.py#L101-L104) - Encounter difficulty selection

---

### itempropdef.2da

**Engine Usage**: Defines item property definitions and their base properties. This is the master table for all item properties in the game. The engine uses this file to determine item property types, costs, and effects.

**Row Index**: Item Property ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property label |
| Additional columns | Various | Property definitions, costs, and parameters |

**Note**: This file may be the same as or related to `itemprops.2da` documented earlier. The exact relationship between these files may vary between KotOR 1 and 2.

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:475`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L475) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:74`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L74) - HTInstallation constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/uti.py:107-111`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/uti.py#L107-L111) - Item property loading in item editor

---

### emotion.2da

**Engine Usage**: Defines emotion animations for dialog conversations (KotOR 2 only). The engine uses this file to determine which emotion animation to play during dialog lines.

**Row Index**: Emotion ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Emotion label |
| Additional columns | Various | Emotion animation properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:491`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L491) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:90`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L90) - HTInstallation constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/dlg/editor.py:1267-1319`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/dlg/editor.py#L1267-L1319) - Emotion loading in dialog editor (KotOR 2 only)

---

### facialanim.2da

**Engine Usage**: Defines facial animation expressions for dialog conversations (KotOR 2 only). The engine uses this file to determine which facial expression animation to play during dialog lines.

**Row Index**: Expression ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Expression label |
| Additional columns | Various | Facial animation properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:492`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L492) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:91`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L91) - HTInstallation constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/dlg/editor.py:1267-1325`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/dlg/editor.py#L1267-L1325) - Expression loading in dialog editor (KotOR 2 only)

---

### videoeffects.2da

**Engine Usage**: Defines video/camera effects for dialog conversations. The engine uses this file to determine which visual effect to apply during dialog camera shots.

**Row Index**: Video Effect ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Video effect label |
| Additional columns | Various | Video effect properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:493`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L493) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:92`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L92) - HTInstallation constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/dlg/editor.py:1263-1298`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/dlg/editor.py#L1263-L1298) - Video effect loading in dialog editor

---

### planetary.2da

**Engine Usage**: Defines planetary information for the galaxy map and travel system. The engine uses this file to determine planet names, descriptions, and travel properties.

**Row Index**: Planet ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Planet label |
| Additional columns | Various | Planet properties and travel information |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:495`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L495) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:94`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L94) - HTInstallation constant

---

### cursors.2da

**Engine Usage**: Defines cursor types for different object interactions. The engine uses this file to determine which cursor to display when hovering over different object types.

**Row Index**: Cursor ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Cursor label |
| Additional columns | Various | Cursor properties and ResRefs |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:469`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L469) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:68`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L68) - HTInstallation constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/utt.py:71-76`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utt.py#L71-L76) - Cursor selection in trigger editor

---

## Item Property Parameter & Cost Tables 2DA Files

The following 2DA files are used for item property parameter and cost calculations:

### iprp_paramtable.2da

**Engine Usage**: Master table listing all item property parameter tables. The engine uses this file to look up which parameter table to use for a specific item property type.

**Row Index**: Parameter Table ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Parameter table label |
| Additional columns | Various | Parameter table ResRefs and properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:476`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L476) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:75`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L75) - HTInstallation constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/uti.py:517-558`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/uti.py#L517-L558) - Parameter table lookup in item editor

---

### iprp_costtable.2da

**Engine Usage**: Master table listing all item property cost calculation tables. The engine uses this file to look up which cost table to use for calculating item property costs.

**Row Index**: Cost Table ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Cost table label |
| Additional columns | Various | Cost table ResRefs and properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:477`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L477) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:76`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L76) - HTInstallation constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/uti.py:486-496`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/uti.py#L486-L496) - Cost table lookup in item editor

---

### iprp_abilities.2da

**Engine Usage**: Maps item property values to ability score bonuses. The engine uses this file to determine which ability score is affected by an item property.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | Ability score mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:478`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L478) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:77`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L77) - HTInstallation constant

---

### iprp_aligngrp.2da

**Engine Usage**: Maps item property values to alignment group restrictions. The engine uses this file to determine alignment restrictions for item properties.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | Alignment group mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:479`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L479) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:78`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L78) - HTInstallation constant

---

### iprp_combatdam.2da

**Engine Usage**: Maps item property values to combat damage bonuses. The engine uses this file to determine damage bonus calculations for item properties.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | Combat damage mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:480`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L480) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:79`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L79) - HTInstallation constant

---

### iprp_damagetype.2da

**Engine Usage**: Maps item property values to damage type flags. The engine uses this file to determine damage type calculations for item properties.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | Damage type mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:481`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L481) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:80`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L80) - HTInstallation constant

---

### iprp_protection.2da

**Engine Usage**: Maps item property values to protection/immunity types. The engine uses this file to determine protection calculations for item properties.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | Protection type mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:482`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L482) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:81`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L81) - HTInstallation constant

---

### iprp_acmodtype.2da

**Engine Usage**: Maps item property values to armor class modifier types. The engine uses this file to determine AC modifier calculations for item properties.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | AC modifier type mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:483`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L483) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:82`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L82) - HTInstallation constant

---

### iprp_immunity.2da

**Engine Usage**: Maps item property values to immunity types. The engine uses this file to determine immunity calculations for item properties.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | Immunity type mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:484`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L484) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:83`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L83) - HTInstallation constant

---

### iprp_saveelement.2da

**Engine Usage**: Maps item property values to saving throw element types. The engine uses this file to determine saving throw element calculations for item properties.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | Saving throw element mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:485`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L485) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:84`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L84) - HTInstallation constant

---

### iprp_savingthrow.2da

**Engine Usage**: Maps item property values to saving throw types. The engine uses this file to determine saving throw calculations for item properties.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | Saving throw type mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:486`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L486) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:85`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L85) - HTInstallation constant

---

### iprp_onhit.2da

**Engine Usage**: Maps item property values to on-hit effect types. The engine uses this file to determine on-hit effect calculations for item properties.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | On-hit effect mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:487`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L487) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:86`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L86) - HTInstallation constant

---

### iprp_ammotype.2da

**Engine Usage**: Maps item property values to ammunition type restrictions. The engine uses this file to determine ammunition type calculations for item properties.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | Ammunition type mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:488`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L488) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:87`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L87) - HTInstallation constant

---

### iprp_mosterhit.2da

**Engine Usage**: Maps item property values to monster hit effect types. The engine uses this file to determine monster hit effect calculations for item properties.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | Monster hit effect mappings |

**Note**: The filename contains a typo ("mosterhit" instead of "monsterhit") which is preserved in the game files.

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:489`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L489) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:88`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L88) - HTInstallation constant

---

### iprp_walk.2da

**Engine Usage**: Maps item property values to movement/walk speed modifiers. The engine uses this file to determine movement speed calculations for item properties.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | Movement speed mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:490`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L490) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:89`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L89) - HTInstallation constant

---

### ai_styles.2da

**Engine Usage**: Defines AI behavior styles for creatures. The engine uses this file to determine AI behavior patterns and combat strategies.

**Row Index**: AI Style ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | AI style label |
| Additional columns | Various | AI behavior parameters |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:572`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L572) - GFF field mapping: "AIStyle" -> ai_styles.2da

---

### iprp_damagevs.2da

**Engine Usage**: Maps item property values to damage vs. specific creature type bonuses. The engine uses this file to determine damage bonuses against specific creature types.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | Damage vs. creature type mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:574`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L574) - GFF field mapping: "DamageVsType" -> iprp_damagevs.2da

---

### iprp_attackmod.2da

**Engine Usage**: Maps item property values to attack modifier bonuses. The engine uses this file to determine attack bonus calculations for item properties.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | Attack modifier mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:575`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L575) - GFF field mapping: "AttackModifier" -> iprp_attackmod.2da

---

### iprp_bonusfeat.2da

**Engine Usage**: Maps item property values to bonus feat grants. The engine uses this file to determine which feats are granted by item properties.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | Bonus feat mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:577`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L577) - GFF field mapping: "BonusFeatID" -> iprp_bonusfeat.2da

---

### iprp_lightcol.2da

**Engine Usage**: Maps item property values to light color configurations. The engine uses this file to determine light color settings for item properties.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | Light color mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:579`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L579) - GFF field mapping: "LightColor" -> iprp_lightcol.2da

---

### iprp_monstdam.2da

**Engine Usage**: Maps item property values to monster damage bonuses. The engine uses this file to determine damage bonus calculations for monster weapons.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | Monster damage mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:580`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L580) - GFF field mapping: "MonsterDamage" -> iprp_monstdam.2da

---

### iprp_skillcost.2da

**Engine Usage**: Maps item property values to skill bonus calculations. The engine uses this file to determine skill bonus cost calculations for item properties.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | Skill bonus mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:584`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L584) - GFF field mapping: "SkillBonus" -> iprp_skillcost.2da

---

### iprp_weightinc.2da

**Engine Usage**: Maps item property values to weight increase calculations. The engine uses this file to determine weight increase calculations for item properties.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| `name` | StrRef | String reference for property name |
| Additional columns | Various | Weight increase mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:133,311`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L133) - StrRef column definition for iprp_weightinc.2da
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:586`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L586) - GFF field mapping: "WeightIncrease" -> iprp_weightinc.2da

---

### iprp_traptype.2da

**Engine Usage**: Maps item property values to trap type configurations. The engine uses this file to determine trap type settings for item properties.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | Trap type mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:587`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L587) - GFF field mapping: "Trap" -> iprp_traptype.2da

---

### iprp_damagered.2da

**Engine Usage**: Maps item property values to damage reduction calculations. The engine uses this file to determine damage reduction calculations for item properties.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | Damage reduction mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:588`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L588) - GFF field mapping: "DamageReduction" -> iprp_damagered.2da

---

### iprp_spellres.2da

**Engine Usage**: Maps item property values to spell resistance calculations. The engine uses this file to determine spell resistance calculations for item properties.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | Spell resistance mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:592`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L592) - GFF field mapping: "SpellResistance" -> iprp_spellres.2da

---

### rumble.2da

**Engine Usage**: Defines rumble/vibration patterns for controller feedback. The engine uses this file to determine rumble patterns for camera shake and controller vibration effects.

**Row Index**: Rumble Pattern ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Rumble pattern label |
| `lsamples` | Integer | Left channel sample count |
| `rsamples` | Integer | Right channel sample count |
| Additional columns | Various | Rumble pattern data |

**References**:

- [`vendor/KotOR.js/src/managers/CameraShakeManager.ts:46`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/managers/CameraShakeManager.ts#L46) - Rumble pattern loading from 2DA
- [`vendor/KotOR.js/src/nwscript/NWScriptDefK1.ts:4500-4515`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptDefK1.ts#L4500-L4515) - PlayRumblePattern and StopRumblePattern functions

---

### musictable.2da

**Engine Usage**: Defines music tracks available in the main menu music selection. The engine uses this file to populate the music list in the options menu.

**Row Index**: Music Track ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Music track label |
| Additional columns | Various | Music track properties and ResRefs |

**References**:

- [`vendor/KotOR.js/src/game/tsl/menu/MainMusic.ts:63-68`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/game/tsl/menu/MainMusic.ts#L63-L68) - Music table loading for main menu

---

### difficultyopt.2da

**Engine Usage**: Defines difficulty options and their properties. The engine uses this file to determine difficulty settings, modifiers, and descriptions.

**Row Index**: Difficulty Option ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Difficulty option label |
| `desc` | String | Difficulty description (e.g., "Default") |
| Additional columns | Various | Difficulty modifiers and properties |

**References**:

- [`vendor/KotOR.js/src/engine/rules/SWRuleSet.ts:66-74`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/engine/rules/SWRuleSet.ts#L66-L74) - Difficulty options initialization from 2DA

---

### xptable.2da

**Engine Usage**: Defines experience point reward calculations for defeating enemies. The engine uses this file to calculate how much XP to grant when a creature is defeated, based on the defeated creature's level and properties.

**Row Index**: XP Table Entry ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | XP table entry label |
| Additional columns | Various | XP calculation parameters |

**Note**: This is different from `exptable.2da` which defines XP requirements for leveling up. `xptable.2da` defines XP rewards for defeating enemies.

**References**:

- [`vendor/KotOR.js/src/engine/rules/SWRuleSet.ts:89-95`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/engine/rules/SWRuleSet.ts#L89-L95) - XP table initialization from 2DA

---

### featgain.2da

**Engine Usage**: Defines feat gain progression by class and level. The engine uses this file to determine which feats are available to each class at each level.

**Row Index**: Feat Gain Entry ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Feat gain entry label |
| Additional columns | Various | Feat gain progression by class and level |

**References**:

- [`vendor/KotOR.js/src/engine/rules/SWRuleSet.ts:101-105`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/engine/rules/SWRuleSet.ts#L101-L105) - Feat gain initialization from 2DA

---

### effecticon.2da

**Engine Usage**: Defines effect icons displayed on character portraits and character sheets. The engine uses this file to determine which icon to display for status effects, buffs, and debuffs.

**Row Index**: Effect Icon ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Effect icon label |
| Additional columns | Various | Effect icon properties and ResRefs |

**References**:

- [`vendor/KotOR.js/src/engine/rules/SWRuleSet.ts:143-150`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/engine/rules/SWRuleSet.ts#L143-L150) - Effect icon initialization from 2DA
- [`vendor/KotOR.js/src/nwscript/NWScriptDefK1.ts:6441-6446`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptDefK1.ts#L6441-L6446) - SetEffectIcon function
- [`vendor/NorthernLights/nwscript.nss:4678`](https://github.com/th3w1zard1/NorthernLights/blob/master/nwscript.nss#L4678) - Comment referencing effecticon.2da

---

### itempropsdef.2da

**Engine Usage**: Defines item property definitions and their base properties. This is the master table for all item properties in the game. The engine uses this file to determine item property types, costs, and effects.

**Row Index**: Item Property ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property label |
| Additional columns | Various | Property definitions, costs, and parameters |

**Note**: This file may be the same as or related to `itempropdef.2da` and `itemprops.2da` documented earlier. The exact relationship between these files may vary between KotOR 1 and 2.

**References**:

- [`vendor/KotOR.js/src/engine/rules/SWRuleSet.ts:167-173`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/engine/rules/SWRuleSet.ts#L167-L173) - Item properties initialization from 2DA

---

### pazaakdecks.2da

**Engine Usage**: Defines Pazaak card decks for the Pazaak mini-game. The engine uses this file to determine which cards are available in opponent decks and player decks.

**Row Index**: Pazaak Deck ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Deck label |
| Additional columns | Various | Deck card definitions and properties |

**References**:

- [`vendor/KotOR.js/src/engine/rules/SWRuleSet.ts:178-185`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/engine/rules/SWRuleSet.ts#L178-L185) - Pazaak decks initialization from 2DA
- [`vendor/KotOR.js/src/nwscript/NWScriptDefK1.ts:4438`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptDefK1.ts#L4438) - StartPazaakGame function comment
- [`vendor/NorthernLights/nwscript.nss:3847`](https://github.com/th3w1zard1/NorthernLights/blob/master/nwscript.nss#L3847) - Comment referencing PazaakDecks.2da

---

### acbonus.2da

**Engine Usage**: Defines armor class bonus calculations. The engine uses this file to determine AC bonus values for different scenarios and calculations.

**Row Index**: AC Bonus Entry ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | AC bonus entry label |
| Additional columns | Various | AC bonus calculation parameters |

**References**:

- [`vendor/KotOR.js/src/combat/CreatureClass.ts:302-304`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/combat/CreatureClass.ts#L302-L304) - AC bonus loading from 2DA

---

### keymap.2da

**Engine Usage**: Defines keyboard and controller key mappings for different game contexts (in-game, GUI, dialog, minigame, etc.). The engine uses this file to determine which keys trigger which actions in different contexts.

**Row Index**: Keymap Entry ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Keymap entry label |
| Additional columns | Various | Key mappings for different contexts (ingame, gui, dialog, minigame, freelook, movie) |

**References**:

- [`vendor/KotOR.js/src/controls/KeyMapper.ts:293-299`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/controls/KeyMapper.ts#L293-L299) - Keymap initialization from 2DA

---

### soundeax.2da

**Engine Usage**: Defines EAX (Environmental Audio Extensions) sound presets for 3D audio processing. The engine uses this file to determine EAX preset configurations for different environments.

**Row Index**: EAX Preset ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | EAX preset label |
| Additional columns | Various | EAX preset parameters and properties |

**References**:

- [`vendor/KotOR.js/src/apps/forge/states/MenuTopState.tsx:420`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/apps/forge/states/MenuTopState.tsx#L420) - EAX presets loading from 2DA

---

### poison.2da

**Engine Usage**: Defines poison effect types and their properties. The engine uses this file to determine poison effects, durations, and damage calculations.

**Row Index**: Poison Type ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Poison type label |
| Additional columns | Various | Poison effect properties, damage, and duration |

**References**:

- [`vendor/NorthernLights/nwscript.nss:949`](https://github.com/th3w1zard1/NorthernLights/blob/master/nwscript.nss#L949) - Comment referencing poison.2da constants
- [`vendor/KotOR.js/src/nwscript/NWScriptDefK1.ts:3194-3199`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptDefK1.ts#L3194-L3199) - EffectPoison function

---

### feedbacktext.2da

**Engine Usage**: Defines feedback text strings displayed to the player for various game events and actions. The engine uses this file to provide contextual feedback messages.

**Row Index**: Feedback Text ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Feedback text label |
| Additional columns | Various | Feedback text strings and properties |

**References**:

- [`vendor/NorthernLights/nwscript.nss:3858`](https://github.com/th3w1zard1/NorthernLights/blob/master/nwscript.nss#L3858) - Comment referencing FeedBackText.2da
- [`vendor/KotOR.js/src/nwscript/NWScriptDefK1.ts:4464-4465`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptDefK1.ts#L4464-L4465) - DisplayFeedBackText function

---

### creaturesize.2da

**Engine Usage**: Defines creature size categories and their properties. The engine uses this file to determine size-based combat modifiers, reach, and other size-related calculations.

**Row Index**: Size Category ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Size category label |
| Additional columns | Various | Size category properties and modifiers |

**References**:

- [`vendor/Kotor.NET/Kotor.NET/Tables/Appearance.cs:42-44`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Tables/Appearance.cs#L42-L44) - Comment referencing creaturesize.2da for SizeCategoryID

---

### appearancesndset.2da

**Engine Usage**: Defines sound appearance types for creature appearances. The engine uses this file to determine which sound appearance type to use based on the creature's appearance.

**Row Index**: Sound Appearance Type ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Sound appearance type label |
| Additional columns | Various | Sound appearance type properties |

**References**:

- [`vendor/Kotor.NET/Kotor.NET/Tables/Appearance.cs:58-60`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Tables/Appearance.cs#L58-L60) - Comment referencing appearancesndset.2da for SoundAppTypeID

---

### texpacks.2da

**Engine Usage**: Defines texture pack configurations for graphics settings (KotOR 2 only). The engine uses this file to determine available texture pack options in the graphics menu.

**Row Index**: Texture Pack ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Texture pack label |
| `strrefname` | StrRef | String reference for texture pack name |
| Additional columns | Various | Texture pack properties and settings |

**References**:

- [`vendor/KotOR.js/src/game/tsl/menu/MenuGraphicsAdvanced.ts:51-122`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/game/tsl/menu/MenuGraphicsAdvanced.ts#L51-L122) - Texture pack loading from 2DA for graphics menu (KotOR 2 only)
- [`vendor/KotOR.js/src/game/kotor/menu/MenuGraphicsAdvanced.ts:63-121`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/game/kotor/menu/MenuGraphicsAdvanced.ts#L63-L121) - Texture pack usage in KotOR 1 graphics menu

---

### videoquality.2da

**Engine Usage**: Defines video quality settings and graphics configuration options. The engine uses this file to determine maximum dynamic lights, shadow-casting lights, and other graphics quality parameters.

**Row Index**: Video Quality Setting ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Video quality setting label |
| `NumDynamicLights` | Integer | Maximum number of dynamic lights |
| `NumShadowCastingLights` | Integer | Maximum number of shadow-casting lights |
| Additional columns | Various | Other video quality parameters |

**References**:

- [`vendor/KotOR.js/src/managers/LightManager.ts:17-18`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/managers/LightManager.ts#L17-L18) - Comments referencing videoquality.2da for NumDynamicLights and NumShadowCastingLights
- [`vendor/KotOR.js/src/managers/LightManager.ts:37-38`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/managers/LightManager.ts#L37-L38) - Hardcoded values with comments referencing videoquality.2da

---

### loadscreens.2da

**Engine Usage**: Defines loading screen configurations for area transitions. The engine uses this file to determine which loading screen image, music, and hints to display when transitioning between areas.

**Row Index**: Loading Screen ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Loading screen label |
| `bmpresref` | ResRef | Loading screen background image ResRef |
| `musicresref` | ResRef | Music track ResRef to play during loading |
| Additional columns | Various | Other loading screen properties |

**References**:

- [`vendor/KotOR.js/src/module/ModuleArea.ts:210`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleArea.ts#L210) - Comment referencing loadscreens.2da for area loading screen index
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:549`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L549) - GFF field mapping: "LoadScreenID" -> loadscreens.2da

---

### phenotype.2da

**Engine Usage**: Defines phenotype types for creatures. The engine uses this file to determine creature phenotype classifications, which affect model and texture selection.

**Row Index**: Phenotype ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Phenotype label |
| Additional columns | Various | Phenotype properties |

**References**:

- [`vendor/reone/src/libs/resource/parser/gff/utc.cpp:133`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/gff/utc.cpp#L133) - GFF field parsing: "Phenotype" from UTC (creature) templates
- [`vendor/KotOR.js/src/module/ModuleCreature.ts:118,4033,4689,4832`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleCreature.ts#L118) - Phenotype field handling in creature module
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:525`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L525) - GFF field mapping: "Phenotype" -> phenotype.2da

---

### palette.2da

**Engine Usage**: Defines palette configurations for placeable objects, items, and other game objects. The engine uses this file to determine color palette assignments for objects that support palette variations.

**Row Index**: Palette ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Palette label |
| Additional columns | Various | Palette color definitions and properties |

**References**:

- [`vendor/reone/src/libs/resource/parser/gff/utw.cpp:38`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/gff/utw.cpp#L38) - GFF field parsing: "PaletteID" from UTW (waypoint) templates
- [`vendor/reone/src/libs/resource/parser/gff/utt.cpp:44`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/gff/utt.cpp#L44) - GFF field parsing: "PaletteID" from UTT (trigger) templates
- [`vendor/reone/src/libs/resource/parser/gff/uts.cpp:47`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/gff/uts.cpp#L47) - GFF field parsing: "PaletteID" from UTS (sound) templates
- [`vendor/reone/src/libs/resource/parser/gff/utp.cpp:84`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/gff/utp.cpp#L84) - GFF field parsing: "PaletteID" from UTP (placeable) templates
- [`vendor/reone/src/libs/resource/parser/gff/uti.cpp:54`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/gff/uti.cpp#L54) - GFF field parsing: "PaletteID" from UTI (item) templates
- [`vendor/reone/src/libs/resource/parser/gff/ute.cpp:55`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/gff/ute.cpp#L55) - GFF field parsing: "PaletteID" from UTE (encounter) templates
- [`vendor/reone/src/libs/resource/parser/gff/utd.cpp:73`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/gff/utd.cpp#L73) - GFF field parsing: "PaletteID" from UTD (door) templates
- [`vendor/reone/src/libs/resource/parser/gff/utc.cpp:130`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/gff/utc.cpp#L130) - GFF field parsing: "PaletteID" from UTC (creature) templates
- [`vendor/KotOR.js/src/module/ModulePlaceable.ts:71,813,1152`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModulePlaceable.ts#L71) - PaletteID field handling in placeable module
- [`vendor/KotOR.js/src/module/ModuleItem.ts:745`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleItem.ts#L745) - PaletteID field handling in item module
- [`vendor/KotOR.js/src/module/ModuleDoor.ts:76,1088,1413`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleDoor.ts#L76) - PaletteID field handling in door module
- [`vendor/KotOR.js/src/module/ModuleEncounter.ts:52,383`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleEncounter.ts#L52) - PaletteID field handling in encounter module
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:535`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L535) - GFF field mapping: "PaletteID" -> palette.2da

---

### bodyvariation.2da

**Engine Usage**: Defines body variation types for items and creatures. The engine uses this file to determine body variation assignments, which affect model and texture selection for equipped items.

**Row Index**: Body Variation ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Body variation label |
| Additional columns | Various | Body variation properties |

**References**:

- [`vendor/reone/src/libs/resource/parser/gff/uti.cpp:45`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/gff/uti.cpp#L45) - GFF field parsing: "BodyVariation" from UTI (item) templates
- [`vendor/reone/src/libs/resource/parser/gff/utc.cpp:87`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/gff/utc.cpp#L87) - GFF field parsing: "BodyVariation" from UTC (creature) templates
- [`vendor/reone/src/libs/game/object/item.cpp:124,140,155`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/item.cpp#L124) - Body variation usage in item object
- [`vendor/KotOR.js/src/module/ModuleItem.ts:136`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleItem.ts#L136) - Body variation method in item module
- [`vendor/KotOR.js/src/module/ModuleCreature.ts:82,3908,4798`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleCreature.ts#L82) - Body variation field handling in creature module
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:539`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L539) - GFF field mapping: "BodyVariation" -> bodyvariation.2da

---

### textures.2da

**Engine Usage**: Defines texture variation configurations. The engine uses this file to determine texture variation assignments for objects that support texture variations.

**Row Index**: Texture Variation ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Texture variation label |
| Additional columns | Various | Texture variation properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:540`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L540) - GFF field mapping: "TextureVar" -> textures.2da

---

### merchants.2da

**Engine Usage**: Defines merchant markup and markdown configurations for shop transactions. The engine uses this file to determine buy/sell price multipliers for different merchant types.

**Row Index**: Merchant Type ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Merchant type label |
| Additional columns | Various | Markup and markdown price multipliers |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:564-565`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L564-L565) - GFF field mapping: "MarkUp" and "MarkDown" -> merchants.2da
- [`Libraries/PyKotor/src/pykotor/resource/generics/utm.py:54,60`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utm.py#L54) - Comments referencing merchants.2da for markup/markdown values

---

### actions.2da

**Engine Usage**: Defines action types and their properties. The engine uses this file to determine action icons, descriptions, and behaviors for various in-game actions.

**Row Index**: Action ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Action label |
| `string_ref` | StrRef | String reference for action description |
| `iconresref` | ResRef | Icon ResRef for the action |
| Additional columns | Various | Action properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:70`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L70) - StrRef column definition for actions.2da
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:212`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L212) - Texture ResRef column definition for actions.2da

---

### aiscripts.2da

**Engine Usage**: Defines AI script templates and their properties. The engine uses this file to determine AI script names and descriptions (KotOR 1 only; KotOR 2 uses `name_strref` only).

**Row Index**: AI Script ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | AI script label |
| `name_strref` | StrRef | String reference for AI script name |
| `description_strref` | StrRef | String reference for AI script description (KotOR 1 only) |
| Additional columns | Various | AI script properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:71`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L71) - StrRef column definitions for aiscripts.2da (K1: name_strref, description_strref; K2: name_strref only)

---

### bindablekeys.2da

**Engine Usage**: Defines bindable key actions and their string references. The engine uses this file to determine key action names for the key binding interface.

**Row Index**: Bindable Key ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Bindable key label |
| `keynamestrref` | StrRef | String reference for key name |
| Additional columns | Various | Key binding properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:74`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L74) - StrRef column definition for bindablekeys.2da

---

### crtemplates.2da

**Engine Usage**: Defines creature template configurations. The engine uses this file to determine creature template names and properties.

**Row Index**: Creature Template ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Creature template label |
| `strref` | StrRef | String reference for creature template name |
| Additional columns | Various | Creature template properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:76`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L76) - StrRef column definition for crtemplates.2da

---

### doortypes.2da

**Engine Usage**: Defines door type configurations and their properties. The engine uses this file to determine door type names, models, and behaviors.

**Row Index**: Door Type ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Door type label |
| `stringrefgame` | StrRef | String reference for door type name |
| `model` | ResRef | Model ResRef for the door type |
| Additional columns | Various | Door type properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:78`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L78) - StrRef column definition for doortypes.2da
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:177`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L177) - Model ResRef column definition for doortypes.2da

---

### environment.2da

**Engine Usage**: Defines environment configurations for areas. The engine uses this file to determine environment names and properties.

**Row Index**: Environment ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Environment label |
| `strref` | StrRef | String reference for environment name |
| Additional columns | Various | Environment properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:81`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L81) - StrRef column definition for environment.2da

---

### fractionalcr.2da

**Engine Usage**: Defines fractional challenge rating configurations. The engine uses this file to determine fractional CR display strings.

**Row Index**: Fractional CR ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Fractional CR label |
| `displaystrref` | StrRef | String reference for fractional CR display text |
| Additional columns | Various | Fractional CR properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:84`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L84) - StrRef column definition for fractionalcr.2da

---

### gamespyrooms.2da

**Engine Usage**: Defines GameSpy room configurations for multiplayer (if supported). The engine uses this file to determine GameSpy room names and properties.

**Row Index**: GameSpy Room ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | GameSpy room label |
| `str_ref` | StrRef | String reference for GameSpy room name |
| Additional columns | Various | GameSpy room properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:85`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L85) - StrRef column definition for gamespyrooms.2da

---

### hen_companion.2da

**Engine Usage**: Defines companion configurations (HEN - Henchman system). The engine uses this file to determine companion names and base resource references.

**Row Index**: Companion ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Companion label |
| `strref` | StrRef | String reference for companion name |
| `baseresref` | ResRef | Base resource reference for companion (not used in game engine) |
| Additional columns | Various | Companion properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:87`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L87) - StrRef column definition for hen_companion.2da
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:157`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L157) - ResRef column definition for hen_companion.2da (baseresref, not used in engine)

---

### hen_familiar.2da

**Engine Usage**: Defines familiar configurations (HEN - Henchman system). The engine uses this file to determine familiar base resource references (not used in game engine).

**Row Index**: Familiar ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Familiar label |
| `baseresref` | ResRef | Base resource reference for familiar (not used in game engine) |
| Additional columns | Various | Familiar properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:158`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L158) - ResRef column definition for hen_familiar.2da (baseresref, not used in engine)

---

### masterfeats.2da

**Engine Usage**: Defines master feat configurations. The engine uses this file to determine master feat names and properties.

**Row Index**: Master Feat ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Master feat label |
| `strref` | StrRef | String reference for master feat name |
| Additional columns | Various | Master feat properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:138`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L138) - StrRef column definition for masterfeats.2da

---

### movies.2da

**Engine Usage**: Defines movie/cutscene configurations. The engine uses this file to determine movie names and descriptions.

**Row Index**: Movie ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Movie label |
| `strrefname` | StrRef | String reference for movie name |
| `strrefdesc` | StrRef | String reference for movie description |
| Additional columns | Various | Movie properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:140`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L140) - StrRef column definitions for movies.2da

---

### stringtokens.2da

**Engine Usage**: Defines string token configurations. The engine uses this file to determine string token values for various game systems.

**Row Index**: String Token ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | String token label |
| `strref1` through `strref4` | StrRef | String references for token values |
| Additional columns | Various | String token properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:144`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L144) - StrRef column definitions for stringtokens.2da

---

### tutorial_old.2da

**Engine Usage**: Defines old tutorial message configurations (legacy). The engine uses this file to determine tutorial messages (replaced by `tutorial.2da` in newer versions).

**Row Index**: Tutorial Message ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Tutorial message label |
| `message0` through `message2` | StrRef | String references for tutorial messages |
| Additional columns | Various | Tutorial message properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:147`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L147) - StrRef column definitions for tutorial_old.2da

---

### credits.2da

**Engine Usage**: Defines credits/acknowledgments configurations (KotOR 2 only). The engine uses this file to determine credits entries.

**Row Index**: Credit ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Credit label |
| `name` | StrRef | String reference for credit name |
| Additional columns | Various | Credit properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:251`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L251) - StrRef column definition for credits.2da (KotOR 2 only)

---

### disease.2da

**Engine Usage**: Defines disease effect configurations. The engine uses this file to determine disease names, scripts, and properties.

**Row Index**: Disease ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Disease label |
| `name` | StrRef | String reference for disease name (KotOR 2) |
| `end_incu_script` | ResRef | Script ResRef for end incubation period |
| `24_hour_script` | ResRef | Script ResRef for 24-hour disease effect |
| Additional columns | Various | Disease properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:255`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L255) - StrRef column definition for disease.2da (KotOR 2)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:238,431`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L238) - Script ResRef column definitions for disease.2da

---

### droiddischarge.2da

**Engine Usage**: Defines droid discharge effect configurations. The engine uses this file to determine droid discharge properties.

**Row Index**: Droid Discharge ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Droid discharge label |
| `>>##HEADER##<<` | ResRef | Header resource reference |
| Additional columns | Various | Droid discharge properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:156`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L156) - ResRef column definition for droiddischarge.2da

---

### minglobalrim.2da

**Engine Usage**: Defines minimum global RIM configurations. The engine uses this file to determine module resource references.

**Row Index**: Global RIM ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Global RIM label |
| `moduleresref` | ResRef | Module resource reference |
| Additional columns | Various | Global RIM properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:161`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L161) - ResRef column definition for minglobalrim.2da

---

### upcrystals.2da

**Engine Usage**: Defines upgrade crystal configurations. The engine uses this file to determine crystal model variations for lightsaber upgrades.

**Row Index**: Upgrade Crystal ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Upgrade crystal label |
| `shortmdlvar` | ResRef | Short model variation ResRef |
| `longmdlvar` | ResRef | Long model variation ResRef |
| `doublemdlvar` | ResRef | Double-bladed model variation ResRef |
| Additional columns | Various | Crystal properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:172`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L172) - Model ResRef column definitions for upcrystals.2da

---

### chargenclothes.2da

**Engine Usage**: Defines character generation clothing configurations. The engine uses this file to determine starting clothing items for character creation.

**Row Index**: Character Generation Clothes ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Character generation clothes label |
| `itemresref` | ResRef | Item resource reference for clothing |
| Additional columns | Various | Character generation clothes properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:226,419`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L226) - Item ResRef column definition for chargenclothes.2da

---

### aliensound.2da

**Engine Usage**: Defines alien sound configurations. The engine uses this file to determine alien sound effect filenames.

**Row Index**: Alien Sound ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Alien sound label |
| `filename` | ResRef | Sound filename ResRef |
| Additional columns | Various | Alien sound properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:183`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L183) - Sound ResRef column definition for aliensound.2da

---

### alienvo.2da

**Engine Usage**: Defines alien voice-over configurations (KotOR 2 only). The engine uses this file to determine alien voice-over sound effects for various emotional states and situations.

**Row Index**: Alien Voice-Over ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Alien voice-over label |
| `angry_long`, `angry_medium`, `angry_short` | ResRef | Angry voice-over sound ResRefs |
| `comment_generic_long`, `comment_generic_medium`, `comment_generic_short` | ResRef | Generic comment voice-over sound ResRefs |
| `greeting_medium`, `greeting_short` | ResRef | Greeting voice-over sound ResRefs |
| `happy_thankful_long`, `happy_thankful_medium`, `happy_thankful_short` | ResRef | Happy/thankful voice-over sound ResRefs |
| `laughter_normal`, `laughter_mocking_medium`, `laughter_mocking_short`, `laughter_long`, `laughter_short` | ResRef | Laughter voice-over sound ResRefs |
| `pleading_medium`, `pleading_short` | ResRef | Pleading voice-over sound ResRefs |
| `question_long`, `question_medium`, `question_short` | ResRef | Question voice-over sound ResRefs |
| `sad_long`, `sad_medium`, `sad_short` | ResRef | Sad voice-over sound ResRefs |
| `scared_long`, `scared_medium`, `scared_short` | ResRef | Scared voice-over sound ResRefs |
| `seductive_long`, `seductive_medium`, `seductive_short` | ResRef | Seductive voice-over sound ResRefs |
| `silence` | ResRef | Silence voice-over sound ResRef |
| `wounded_medium`, `wounded_small` | ResRef | Wounded voice-over sound ResRefs |
| `screaming_medium`, `screaming_small` | ResRef | Screaming voice-over sound ResRefs |
| Additional columns | Various | Alien voice-over properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:363-375`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L363-L375) - Sound ResRef column definitions for alienvo.2da (KotOR 2 only)

---

### grenadesnd.2da

**Engine Usage**: Defines grenade sound configurations. The engine uses this file to determine grenade sound effects.

**Row Index**: Grenade Sound ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Grenade sound label |
| `sound` | ResRef | Sound ResRef for grenade |
| Additional columns | Various | Grenade sound properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:199`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L199) - Sound ResRef column definition for grenadesnd.2da

---

### inventorysnds.2da

**Engine Usage**: Defines inventory sound configurations. The engine uses this file to determine inventory sound effects for item interactions.

**Row Index**: Inventory Sound ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Inventory sound label |
| `inventorysound` | ResRef | Inventory sound ResRef |
| Additional columns | Various | Inventory sound properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:201`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L201) - Sound ResRef column definition for inventorysnds.2da

---

### areaeffects.2da

**Engine Usage**: Defines area effect configurations. The engine uses this file to determine area effect scripts for enter, heartbeat, and exit events.

**Row Index**: Area Effect ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Area effect label |
| `onenter` | ResRef | Script ResRef for on-enter event |
| `heartbeat` | ResRef | Script ResRef for heartbeat event |
| `onexit` | ResRef | Script ResRef for on-exit event |
| Additional columns | Various | Area effect properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:237`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L237) - Script ResRef column definitions for areaeffects.2da

---

#### Additional Item Property Files

The following additional 2DA files are used in KotOR games:

#### Audio & Music

- `ambientmusic.2da`: Ambient music track definitions for areas
- `ambientsound.2da`: Ambient sound effect definitions for areas

#### Item Property Cost Tables

The game uses numerous item property cost calculation tables. Common patterns include:

- `iprp_costtable.2da`: Base cost calculation tables for item properties
- `iprp_ammocost.2da`: Ammunition cost per shot (documented above)
- `iprp_damagecost.2da`: Damage bonus cost calculations (documented above)
- `iprp_onhit*.2da`: On-hit item property definitions and cost tables
- `iprp_onslash*.2da`: On-slash item property definitions and cost tables
- `iprp_onstab*.2da`: On-stab item property definitions and cost tables
- `iprp_oncrush*.2da`: On-crush item property definitions and cost tables
- `iprp_onunarmed*.2da`: On-unarmed item property definitions and cost tables
- `iprp_onranged*.2da`: On-ranged item property definitions and cost tables
- `iprp_onmonster*.2da`: On-monster-hit item property definitions and cost tables (for monster weapons)

Each attack type typically has multiple related files for damage, properties, costs, durations, saving throws, and value calculations. Many of these files have numbered variants (e.g., `iprp_onhitpropsvalue2.2da` through `iprp_onhitpropsvalue50.2da`) for different property value ranges.

**Note**: Some 2DA files may have variations between KotOR and KotOR 2. Always verify file structure against the specific game version. The reone dataminer tool can extract all 2DA files from game archives to analyze their structure.

**References**:

- [`vendor/reone/src/apps/dataminer/2daparsers.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/apps/dataminer/2daparsers.cpp) - Tool for extracting and analyzing all 2DA files from game archives

---

2DA files are the primary configuration mechanism for KotOR's game rules and content. Nearly every game system references at least one 2DA file for its behavior.

---

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
