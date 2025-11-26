# TSLPatcher 2DAList Syntax - Complete Guide

This guide explains how to modify 2DA files using TSLPatcher syntax. For the complete 2DA file format specification, see [2DA File Format](2DA-File-Format). For general TSLPatcher information, see [TSLPatcher's Official Readme](TSLPatcher's-Official-Readme). For HoloPatcher-specific information, see [HoloPatcher README for Mod Developers](HoloPatcher-README-for-mod-developers.).

## Overview

The `[2DAList]` section in TSLPatcher's `changes.ini` enables you to modify 2DA (Two-Dimensional Array) files used throughout KotOR and TSL. 2DA files are tabular data structures that store game information such as appearances, classes, feats, items, spells, and more. You can change existing rows, add new rows, copy rows, and add columns using various targeting methods and value types.

The `[2DAList]` section is processed **after** `[TLKList]` but **before** `[GFFList]` in HoloPatcher, meaning you can use `StrRef#` tokens from [TLKList](TSLPatcher-TLKList-Syntax), and any `2DAMEMORY#` tokens you create will be available to [GFFList](TSLPatcher-GFFList-Syntax) and other sections.

## Table of Contents

- [Quick Start](#quick-start)
- [Cheatsheet](#cheatsheet)
- [Basic Structure](#basic-structure)
- [Processing Order](#processing-order)
- [File-Level Configuration](#file-level-configuration)
- [Modification Types](#modification-types)
  - [ChangeRow - Modify Existing Row](#changerow---modify-existing-row)
  - [AddRow - Add New Row](#addrow---add-new-row)
  - [CopyRow - Copy and Conditionally Add Row](#copyrow---copy-and-conditionally-add-row)
  - [AddColumn - Add New Column](#addcolumn---add-new-column)
- [Target Types](#target-types)
- [Cell Values and RowValue Types](#cell-values-and-rowvalue-types)
- [Memory Token System](#memory-token-system)
- [Special Functions](#special-functions)
- [Examples](#examples)
- [Common Pitfalls and Troubleshooting](#common-pitfalls-and-troubleshooting)
- [Integration with Other Sections](#integration-with-other-sections)

## Quick Start

<!-- markdownlint-disable MD029 -->
1. Add your 2DA file under `[2DAList]`:

```ini
[2DAList]
Table0=appearance.2da
```

2. Create a section named exactly like that file:

```ini
[appearance.2da]
ChangeRow0=modify_appearance
```

3. Create the modification section to change a row:

```ini
[modify_appearance]
RowIndex=5
label=CUSTOM_APPEARANCE
modeltype=1
```

4. Store values for later use with `2DAMEMORY#` tokens:

```ini
[modify_appearance]
RowIndex=5
label=CUSTOM_APPEARANCE
2DAMEMORY10=RowIndex
2DAMEMORY11=label
```

5. Use tokens from TLKList or other 2DA modifications:

```ini
[add_new_appearance]
label=MY_NEW_APPEARANCE
name=StrRef50
appearance=2DAMEMORY10
```
<!-- markdownlint-enable MD029 -->

## Cheatsheet

- **Modification types**: `ChangeRow#`, `AddRow#`, `CopyRow#`, `AddColumn#`
- **Row targeting**:
  - `RowIndex=#` → Target by numeric row index (0-based)
  - `RowLabel=label` → Target by row label (first column value)
  - `LabelIndex=value` → Find row where "label" column equals value
- **Cell values**:
  - `ColumnName=value` → Set cell to constant string
  - `ColumnName=StrRef#` → Use TLK stringref token
  - `ColumnName=2DAMEMORY#` → Use 2DA memory token
  - `ColumnName=high()` → Maximum value in that column
  - `ColumnName=RowIndex` → Current row's index
  - `ColumnName=RowLabel` → Current row's label
  - `ColumnName=RowCell('column')` → Value from another cell
  - `ColumnName=****` → Empty string
- **Memory storage**:
  - `2DAMEMORY#=RowIndex` → Store row index
  - `2DAMEMORY#=RowLabel` → Store row label
  - `2DAMEMORY#=ColumnName` → Store cell value from that column
  - `StrRef#=value` → Store stringref for later use
- **Special row properties**:
  - `RowLabel=value` → Set row label (for AddRow/CopyRow)
  - `NewRowLabel=value` → Alternative name for RowLabel
  - `ExclusiveColumn=name` → Check for existing row by column value (AddRow/CopyRow)

## Basic Structure

```ini
[2DAList]
!DefaultDestination=override
!DefaultSourceFolder=.
Table0=appearance.2da
Replace0=classes.2da

[appearance.2da]
!Destination=override
!SourceFolder=.
!SourceFile=custom_appearance.2da
!ReplaceFile=0
!SaveAs=appearance.2da
ChangeRow0=modify_row_1
AddRow0=add_new_row
CopyRow0=copy_existing_row
AddColumn0=add_new_column

[modify_row_1]
RowIndex=5
label=CUSTOM_APPEARANCE
modeltype=1

[add_new_row]
ExclusiveColumn=label
RowLabel=10
label=NEW_APPEARANCE
name=StrRef100

[copy_existing_row]
RowLabel=1
ExclusiveColumn=label
NewRowLabel=9
label=COPIED_APPEARANCE

[add_new_column]
ColumnLabel=NewColumn
DefaultValue=0
I5=CustomValue
L1=AnotherValue
```

The `[2DAList]` section declares which 2DA files you want to modify. Each entry (like `Table0`, `Table1`, etc., or `Replace0`, `Replace1`, etc.) references another section with the same name as the filename.

**Syntax Notes:**

- Use `Table#` to add a new 2DA file modification (non-replacing)
- Use `Replace#` to replace an existing 2DA file before applying modifications
- The `#` is a sequential number starting from 0 (Table0, Table1, Table2, etc.)
- Numbers can be sequential, but gaps are allowed (Table0, Table2, Table5 is valid)
- Each file section contains modification entries (`ChangeRow#`, `AddRow#`, `CopyRow#`, `AddColumn#`)

## Processing Order

In **HoloPatcher**, the 2DAList runs in the following execution order:

1. **[InstallList]** - Files are installed first
2. **[TLKList]** - TLK modifications (creates `StrRef#` tokens)
3. **[2DAList]** ← **You are here** - 2DA file modifications (creates `2DAMEMORY#` tokens)
4. **[GFFList]** - GFF file modifications (can use `StrRef#` and `2DAMEMORY#` tokens)
5. **[CompileList]** - Script compilation (can use `StrRef#` and `2DAMEMORY#` tokens)
6. **[HACKList]** - Binary hacking (can use `StrRef#` and `2DAMEMORY#` tokens)
7. **[SSFList]** - Sound set modifications (can use `StrRef#` and `2DAMEMORY#` tokens)

**Important:** Since 2DAList runs after TLKList, you can use `StrRef#` tokens in your 2DA modifications. Any `2DAMEMORY#` tokens you create will be available to all subsequent sections (GFFList, CompileList, HACKList, SSFList).

## File-Level Configuration

### Top-Level Keys in [2DAList]

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `!DefaultDestination` | string | `override` | Default destination for all 2DA files in this section |
| `!DefaultSourceFolder` | string | `.` | Default source folder for 2DA files. Relative path from `mod_path` (typically the `tslpatchdata` folder, which is the parent directory of `changes.ini` and `namespaces.ini`). When `.`, refers to the `tslpatchdata` folder itself. Path resolution: `mod_path / !DefaultSourceFolder / filename` |

### File Section Configuration

Each 2DA file requires its own section (e.g., `[appearance.2da]`).

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `!Destination` | string | Inherited from `!DefaultDestination` | Where to save the modified file (`override` or `path\to\file.mod`) |
| `!SourceFolder` | string | Inherited from `!DefaultSourceFolder` | Source folder for the 2DA file. Relative path from `mod_path` (typically the tslpatchdata folder). When `.`, refers to the tslpatchdata folder itself. |
| `!SourceFile` | string | Same as section name | Alternative source filename (useful for multiple setup options using different source files) |
| `!ReplaceFile` | 0/1 | 0 | If `1`, overwrite existing file before applying modifications. If `0` (default), modify the existing file in place. |
| `!SaveAs` | string | Same as section name | Alternative filename to save as (useful for renaming files during installation) |
| `!OverrideType` | string | `warn` (HoloPatcher) / `ignore` (TSLPatcher) | How to handle existing files in Override when destination is an ERF/RIM archive. Valid values: `ignore`, `warn`, `rename` |

**Destination Values:**

- `override` or empty: Save to the Override folder
- `Modules\module.mod`: Insert into an ERF/MOD/RIM archive (use backslashes for path separators)
- Archive paths must be relative to the game folder root

**Syntax Notes:**

- `!DefaultSourceFolder` and `!SourceFolder` default to `.` which refers to the `tslpatchdata` folder itself
- When specifying paths, use backslashes (`\`) as path separators (TSLPatcher style), though forward slashes (`/`) are also accepted and normalized
- Path resolution: `mod_path / !SourceFolder / !SourceFile` (or section name if `!SourceFile` is not set)

## Modification Types

### ChangeRow - Modify Existing Row

**Syntax:** `ChangeRow#=section_name`

Changes an existing row in the 2DA file. You must specify which row to modify using one of the target types (see [Target Types](#target-types)).

**Required Keys:**

- One of: `RowIndex`, `RowLabel`, or `LabelIndex` (to identify which row to modify)

**Optional Keys:**

- Any column name (to modify cell values)
- `2DAMEMORY#=value` (to store values in memory)
- `StrRef#=value` (to store stringref values in memory)

**Example:**

```ini
[2DAList]
Table0=appearance.2da

[appearance.2da]
ChangeRow0=modify_appearance_5

[modify_appearance_5]
RowIndex=5
label=CUSTOM_APPEARANCE
modeltype=1
```

**Example with Memory Storage:**

```ini
[modify_appearance_5]
RowIndex=5
label=CUSTOM_APPEARANCE
modeltype=1
2DAMEMORY10=RowIndex      ; Store row index (5) in memory token 10
2DAMEMORY11=RowLabel      ; Store row label in memory token 11
2DAMEMORY12=modeltype     ; Store modeltype value in memory token 12
StrRef20=name             ; Store name stringref in TLK memory token 20
```

**Behavior:**

- If the target row is not found, a warning is logged and the modification is skipped
- Existing cell values are overwritten with new values
- Columns that are not specified remain unchanged
- Memory tokens are evaluated and stored after cell modifications are applied

### AddRow - Add New Row

**Syntax:** `AddRow#=section_name`

Adds a new row to the 2DA file. If `ExclusiveColumn` is specified and a row with that value already exists, the existing row is modified instead of adding a new one.

**Required Keys:**

- None (empty section creates a row with default/empty values)

**Optional Keys:**

- `ExclusiveColumn=column_name` → Check if a row with the same value in this column already exists; if so, modify it instead of adding
- `RowLabel=value` or `NewRowLabel=value` → Set the row label (defaults to current row count if not specified)
- Any column name (to set cell values)
- `2DAMEMORY#=value` (to store values in memory)
- `StrRef#=value` (to store stringref values in memory)

**Example:**

```ini
[appearance.2da]
AddRow0=add_new_appearance

[add_new_appearance]
ExclusiveColumn=label
RowLabel=100
label=MY_NEW_APPEARANCE
name=StrRef200
modeltype=2
```

**Example with Exclusive Column (Prevent Duplicates):**

```ini
[add_new_appearance]
ExclusiveColumn=label
label=MY_NEW_APPEARANCE
name=StrRef200
```

If a row with `label=MY_NEW_APPEARANCE` already exists, it will be modified. Otherwise, a new row will be added.

**Behavior:**

- New row is added with the specified cell values
- If `ExclusiveColumn` is specified and a matching row exists, that row is updated instead
- Row label defaults to the current row count (as a string) if `RowLabel`/`NewRowLabel` is not specified
- Memory tokens are evaluated and stored after the row is added/modified

### CopyRow - Copy and Conditionally Add Row

**Syntax:** `CopyRow#=section_name`

Copies an existing row (identified by a target) and optionally adds it as a new row or modifies an existing one if `ExclusiveColumn` matches.

**Required Keys:**

- One of: `RowIndex`, `RowLabel`, or `LabelIndex` (to identify the source row to copy)

**Optional Keys:**

- `ExclusiveColumn=column_name` → If a row with the same value in this column already exists, modify that row instead of adding a new one
- `RowLabel=value` or `NewRowLabel=value` → Set the new row's label (defaults to current row count if not specified)
- Any column name (to override cell values from the copied row)
- `2DAMEMORY#=value` (to store values in memory)
- `StrRef#=value` (to store stringref values in memory)

**Example:**

```ini
[appearance.2da]
CopyRow0=copy_appearance_1

[copy_appearance_1]
RowLabel=1
ExclusiveColumn=label
NewRowLabel=50
label=COPIED_APPEARANCE
name=StrRef300
```

**Example - Copy and Modify:**

```ini
[copy_appearance_1]
RowIndex=5
ExclusiveColumn=label
label=MODIFIED_COPY
modeltype=3
```

**Behavior:**

- The source row (identified by target) is copied
- All cell values from the source row are preserved unless overridden
- If `ExclusiveColumn` is specified and a matching row exists, that existing row is updated
- If `ExclusiveColumn` is not specified or no match is found, a new row is added
- If the source row is not found, an error is raised
- Memory tokens are evaluated and stored after the row is copied/modified

### AddColumn - Add New Column

**Syntax:** `AddColumn#=section_name`

Adds a new column to the 2DA file with a default value for all rows. Specific rows can be given custom values using index or label-based inserts.

**Required Keys:**

- `ColumnLabel=column_name` → The name of the new column
- `DefaultValue=value` → Default value for all rows (use `****` for empty string)

**Optional Keys:**

- `I#=value` → Set value for row at index `#` (e.g., `I5=CustomValue` sets row index 5)
- `Llabel=value` → Set value for row with label `label` (e.g., `L1=CustomValue` sets row with label "1")
- `2DAMEMORY#=I#` or `2DAMEMORY#=Llabel` → Store the cell value from the new column into memory token `#` after the column is created
  - Use `I#` format to reference by row index (e.g., `2DAMEMORY10=I5` stores the value from row index 5 in the new column)
  - Use `Llabel` format to reference by row label (e.g., `2DAMEMORY10=L1` stores the value from the row with label "1" in the new column)
  - Memory storage happens **after** the column is created and all insert values are applied

**Example:**

```ini
[appearance.2da]
AddColumn0=add_custom_column

[add_custom_column]
ColumnLabel=CustomColumn
DefaultValue=0
I5=SpecialValue
L1=AnotherValue
2DAMEMORY10=I5
```

**Example with Memory Storage:**

```ini
[add_custom_column]
ColumnLabel=NewProperty
DefaultValue=****
I0=ValueForRow0
I1=ValueForRow1
L5=ValueForLabel5
2DAMEMORY20=I0    ; Store value from row index 0 after column is created
2DAMEMORY21=L5    ; Store value from row label 5 after column is created
```

**Behavior:**

- New column is added to all rows
- All rows initially receive the `DefaultValue`
- Rows specified in `I#` or `Llabel` entries get their custom values
- If a row specified in `I#` doesn't exist, an error is raised
- If a row specified in `Llabel` doesn't exist, an error is raised
- **Memory Storage:** Memory tokens specified with `2DAMEMORY#=I#` or `2DAMEMORY#=Llabel` store the cell value from the new column **after** it's created and all insert values are applied
  - `2DAMEMORY#=I5` retrieves the cell value from row index 5 in the newly created column
  - `2DAMEMORY#=L1` retrieves the cell value from the row with label "1" in the newly created column
  - This allows you to capture values from the new column for use in later modifications

**Special Value Syntax in AddColumn:**

For `I#` and `Llabel` values (the right side of the assignment), you can use:

- Constant strings: `I5=CustomValue`
- Token references: `I5=2DAMEMORY10`, `I5=StrRef20`
- Special functions (`high()`, `RowIndex`, `RowLabel`) are **not supported** in AddColumn (unlike ChangeRow/AddRow/CopyRow)

**Memory Storage Syntax:**

For memory storage (`2DAMEMORY#=`), you must use:

- `2DAMEMORY#=I#` - Store value from row at index `#` in the new column
- `2DAMEMORY#=Llabel` - Store value from row with label `label` in the new column

The `I#` and `Llabel` on the right side of `2DAMEMORY#=` refer to which row's value to store from the newly created column, not the value to insert.

## Target Types

Target types identify which row to modify in ChangeRow and CopyRow operations. Only one target type can be specified per modification.

### RowIndex

**Syntax:** `RowIndex=integer`

Targets a row by its numeric index (0-based).

**Example:**

```ini
[modify_row]
RowIndex=5
label=MODIFIED
```

**Behavior:**

- Directly accesses the row at the specified index
- If the index is out of bounds, the row is not found and a warning is logged
- The value must be a valid integer
- **Dynamic targeting**: Can use `2DAMEMORY#` tokens for dynamic row selection (e.g., `RowIndex=2DAMEMORY10` will use the value stored in token 10)

### RowLabel

**Syntax:** `RowLabel=label_string`

Targets a row by its label (the value in the first column, typically named "label").

**Example:**

```ini
[modify_row]
RowLabel=1
label=MODIFIED
```

**Behavior:**

- Searches for a row where the row label matches the specified value
- Uses string comparison (case-sensitive)
- If no matching row is found, a warning is logged
- **Dynamic targeting**: RowLabel can accept token references for dynamic row selection:
  - `RowLabel=2DAMEMORY10` - Uses the value stored in 2DA memory token 10
  - `RowLabel=StrRef20` - Uses the stringref value from TLK memory token 20 (converted to string)
- This allows you to dynamically determine which row to modify based on previously stored values

### LabelIndex

**Syntax:** `LabelIndex=value`

Targets a row by searching the "label" column for a matching value. This is different from `RowLabel` because it searches within a specific column named "label" rather than using the row's label value.

**Example:**

```ini
[modify_row]
LabelIndex=MY_APPEARANCE
label=MODIFIED
```

**Behavior:**

- Requires the 2DA to have a column named "label"
- Searches all rows for a cell in the "label" column that matches the specified value
- If the "label" column doesn't exist, an error is raised
- If no matching row is found, a warning is logged
- **Dynamic targeting**: LabelIndex can accept token references for dynamic row selection:
  - `LabelIndex=2DAMEMORY10` - Uses the value stored in 2DA memory token 10
  - `LabelIndex=StrRef20` - Uses the stringref value from TLK memory token 20 (converted to string)
- This allows you to dynamically search for rows based on previously stored values

**Note:** `RowLabel` and `LabelIndex` may seem similar, but they operate differently:

- `RowLabel` uses the row's label value (first column's value)
- `LabelIndex` searches within a column named "label" for a matching value

## Cell Values and RowValue Types

When setting cell values in ChangeRow, AddRow, and CopyRow, you can use various value types. Each cell value is parsed as a `RowValue` type based on the syntax.

### Constant String Values

**Syntax:** `ColumnName=any_string`

The simplest value type - a literal string that will be placed in the cell.

**Example:**

```ini
label=CUSTOM_APPEARANCE
modeltype=1
description=This is a custom appearance
```

### Empty String

**Syntax:** `ColumnName=****`

Use `****` to set a cell to an empty string.

**Example:**

```ini
comment=****
notes=****
```

### Token References

#### StrRef Tokens

**Syntax:** `ColumnName=StrRef#`

References a stringref token created in the `[TLKList]` section. The token number is extracted and the value is looked up from TLK memory.

**Example:**

```ini
name=StrRef50
description=StrRef100
```

**Behavior:**

- Token must be defined in `[TLKList]` before use
- Value stored in the token is used as the cell value
- If token is not found, an error is raised

#### 2DAMEMORY Token References(#2damemory-token-references)

**Syntax:** `ColumnName=2DAMEMORY#`

References a 2DA memory token created in a previous 2DAList modification. The token number is extracted and the value is looked up from 2DA memory.

**Example:**

```ini
appearance=2DAMEMORY10
model=2DAMEMORY5
```

**Behavior:**

- Token must be defined earlier in the same or a previous 2DA file modification
- Value stored in the token (as a string) is used as the cell value
- If token is not found, an error is raised
- **Important:** `!FieldPath` tokens (used in GFFList) cannot be used here - only string values are supported
- The token value is looked up from `memory.memory_2da[token_id]` at runtime
- If the token contains a `PureWindowsPath` (from GFFList `!FieldPath`), a `TypeError` will be raised

### Special Functions

#### high() - Maximum Value

**Syntax:** `ColumnName=high()` or `ColumnName=high(column_name)`

Returns the maximum value from a column or the maximum row label.

**Without Column Name:**

```ini
RowLabel=high()    ; Maximum row label (used when setting row label)
forcehostile=high()  ; Maximum value in the "forcehostile" column
```

**With Column Name:**

```ini
forcehostile=high(modeltype)  ; Maximum value from "modeltype" column
```

**Behavior:**

- `high()` without column name in `RowLabel` context returns the maximum row label
- `high()` without column name in a cell context returns the maximum value from that cell's column
- `high(column)` returns the maximum value from the specified column
- Values are compared as integers if possible, otherwise as strings
- Only works in ChangeRow, AddRow, and CopyRow (not in AddColumn)

#### RowIndex - Current Row Index

**Syntax:** `ColumnName=RowIndex`

Returns the numeric index of the current row as a string.

**Example:**

```ini
index_value=RowIndex
```

**Behavior:**

- Returns the row index (0-based) as a string
- Only works in ChangeRow, AddRow, and CopyRow cell values
- Cannot be used as a target (use `RowIndex=#` for targeting)

#### RowLabel - Current Row Label

**Syntax:** `ColumnName=RowLabel`

Returns the label of the current row (value in the first column).

**Example:**

```ini
label_copy=RowLabel
```

**Behavior:**

- Returns the row's label value as a string
- Only works in ChangeRow, AddRow, and CopyRow cell values
- Cannot be used as a target (use `RowLabel=value` for targeting)

#### RowCell - Value from Another Cell

**Syntax:** `ColumnName=RowCell('column_name')`

**Note:** This syntax is not directly supported in the INI format. In practice, you would reference a column name directly to get its value, or use `2DAMEMORY#` tokens. The `RowCell` type exists internally but is primarily used for memory storage operations.

**For Memory Storage:**

```ini
2DAMEMORY10=modeltype  ; Stores value from "modeltype" column (this internally uses RowCell)
```

## Memory Token System

The memory token system allows you to store values from 2DA modifications for use in other sections or later modifications.

### 2DAMEMORY Tokens

**Syntax:** `2DAMEMORY#=value_source`

Stores a value in 2DA memory at token `#`. The token number can be any non-negative integer (typically starting from 0 or 1).

**Available Value Sources:**

| Value Source | Description | Example | Internal Type |
|--------------|-------------|---------|---------------|
| `RowIndex` | Store the row's numeric index (0-based) as string | `2DAMEMORY10=RowIndex` | `RowValueRowIndex()` |
| `RowLabel` | Store the row's label value (first column) | `2DAMEMORY11=RowLabel` | `RowValueRowLabel()` |
| `ColumnName` | Store the value from a specific column in the current row | `2DAMEMORY12=modeltype` | `RowValueRowCell(column)` |
| `StrRef#` | Store the stringref value from a TLK token (converted to string) | `2DAMEMORY13=StrRef50` | `RowValueTLKMemory(token_id)` |
| `2DAMEMORY#` | Copy value from another 2DA token | `2DAMEMORY14=2DAMEMORY10` | References existing token |

**Note:** The internal types listed above are runtime evaluation objects that compute values when the modification is applied. They are **only used for storage operations** (left side of `2DAMEMORY#=`), not for cell value assignments (right side of `ColumnName=`).

**Example - Storing Multiple Values:**

```ini
[modify_appearance]
RowIndex=5
label=CUSTOM_APPEARANCE
modeltype=1
2DAMEMORY10=RowIndex      ; Stores "5"
2DAMEMORY11=RowLabel      ; Stores "CUSTOM_APPEARANCE" or row label value
2DAMEMORY12=modeltype     ; Stores "1"
```

**Example - Using Stored Values:**

```ini
[add_new_appearance]
label=ANOTHER_APPEARANCE
modeltype=2DAMEMORY12     ; Use stored modeltype value
appearance=2DAMEMORY10    ; Use stored row index
```

**Behavior:**

- Tokens are stored as strings in 2DA memory (`memory.memory_2da[token_id]`)
- **Evaluation Order:** Memory storage operations (`2DAMEMORY#=...`) are evaluated **after** all cell modifications are applied within the same modification section
- This means you cannot use a token in a cell value (`ColumnName=2DAMEMORY#`) and create it (`2DAMEMORY#=...`) in the same section - create tokens in earlier modifications
- Tokens are available to all subsequent sections (GFFList, CompileList, HACKList, SSFList)
- Tokens persist across multiple 2DA file modifications within the same `[2DAList]` section
- If a token is referenced before being set, a `KeyError` is raised: `"2DAMEMORY{id} was not defined before use"`
- **Storage Type:** Values are stored as `str` type (or `PureWindowsPath` for GFFList `!FieldPath`, but those cannot be used in 2DAList)

### StrRef Tokens (TLK Memory)

**Syntax:** `StrRef#=value_source`

Stores a stringref value in TLK memory at token `#`. These tokens are primarily created in `[TLKList]`, but can also be set here.

**Available Value Sources:**

| Value Source | Description | Example |
|--------------|-------------|---------|
| `ColumnName` | Store the stringref from a specific column (value must be convertible to integer) | `StrRef20=name` |
| `StrRef#` | Copy stringref value from another TLK token | `StrRef21=StrRef20` |
| `2DAMEMORY#` | Store stringref from a 2DA token (value must be convertible to integer) | `StrRef22=2DAMEMORY10` |

**Example:**

```ini
[modify_appearance]
RowIndex=5
name=12345
StrRef30=name          ; Store stringref 12345 in token 30
StrRef31=StrRef30      ; Copy token 30 to token 31
```

**Behavior:**

- Values are stored as integers in TLK memory
- The source value must be convertible to an integer (stringrefs are integers)
- Tokens are available to all subsequent sections
- StrRef tokens are primarily used in GFFList for localized string fields

### Token Usage in Other Sections

Once created, `2DAMEMORY#` and `StrRef#` tokens can be used in:

1. **Later 2DA modifications** - Use in ChangeRow, AddRow, CopyRow, or AddColumn
2. **GFFList** - Use in field values, field paths, or TypeId fields
3. **CompileList** - Use as preprocessor tokens in NSS scripts (`#2DAMEMORY#` and `#StrRef#`)
4. **HACKList** - Use in binary patch values
5. **SSFList** - Use for sound stringref assignments

**Example Cross-Section Usage:**

```ini
[2DAList]
Table0=appearance.2da

[appearance.2da]
AddRow0=new_appearance

[new_appearance]
RowLabel=100
label=MY_APPEARANCE
2DAMEMORY10=RowIndex

[GFFList]
File0=item.uti

[item.uti]
ModelVariation=2DAMEMORY10  ; Use the stored row index
```

## Examples

### Example 1: Modify Existing Appearance

```ini
[2DAList]
Table0=appearance.2da

[appearance.2da]
ChangeRow0=modify_human_male

[modify_human_male]
RowLabel=1
label=HUMAN_MALE
modeltype=1
2DAMEMORY10=RowIndex
```

### Example 1a: Dynamic Row Targeting with Tokens

```ini
[2DAList]
Table0=appearance.2da

[appearance.2da]
AddRow0=store_row_index

[store_row_index]
RowLabel=100
label=MY_APPEARANCE
2DAMEMORY10=RowIndex    ; Store the new row's index

[appearance.2da]
ChangeRow0=modify_using_token

[modify_using_token]
RowIndex=2DAMEMORY10    ; Dynamically target the row we just created
label=MODIFIED_APPEARANCE
modeltype=2
```

This demonstrates how you can store a row index in one modification and use it to target that row in a later modification.

### Example 2: Add New Appearance with Exclusive Check

```ini
[2DAList]
Table0=appearance.2da

[appearance.2da]
AddRow0=add_custom_appearance

[add_custom_appearance]
ExclusiveColumn=label
RowLabel=100
label=CUSTOM_APPEARANCE
name=StrRef500
modeltype=2
```

### Example 3: Copy Row and Modify

```ini
[2DAList]
Table0=appearance.2da

[appearance.2da]
CopyRow0=copy_and_modify

[copy_and_modify]
RowIndex=5
ExclusiveColumn=label
label=MODIFIED_COPY
modeltype=3
2DAMEMORY20=RowIndex
```

### Example 4: Add Column with Custom Values

```ini
[2DAList]
Table0=appearance.2da

[appearance.2da]
AddColumn0=add_custom_property

[add_custom_property]
ColumnLabel=CustomProperty
DefaultValue=0
I5=100
L1=200
2DAMEMORY30=I5
```

### Example 5: Complex Multi-Row Modification

```ini
[2DAList]
Table0=appearance.2da

[appearance.2da]
ChangeRow0=modify_row_1
ChangeRow1=modify_row_2
AddRow0=add_new_row
CopyRow0=copy_row
AddColumn0=add_column

[modify_row_1]
RowIndex=1
label=MODIFIED_1
2DAMEMORY10=RowIndex

[modify_row_2]
RowLabel=2
label=MODIFIED_2
appearance=2DAMEMORY10

[add_new_row]
ExclusiveColumn=label
RowLabel=50
label=NEW_APPEARANCE
name=StrRef1000

[copy_row]
RowIndex=1
ExclusiveColumn=label
label=COPIED_APPEARANCE
modeltype=2DAMEMORY10

[add_column]
ColumnLabel=NewColumn
DefaultValue=****
I1=Value1
I2=Value2
L50=Value3
2DAMEMORY40=I1
```

### Example 6: Using Tokens from TLKList

```ini
[TLKList]
StrRef1000=Hello World

[2DAList]
Table0=appearance.2da

[appearance.2da]
AddRow0=new_appearance

[new_appearance]
RowLabel=100
label=MY_APPEARANCE
name=StrRef1000    ; Use token from TLKList
```

### Example 7: Cross-File Token Usage

```ini
[2DAList]
Table0=appearance.2da
Table1=classes.2da

[appearance.2da]
AddRow0=store_appearance

[store_appearance]
RowLabel=100
label=MY_APPEARANCE
2DAMEMORY10=RowIndex

[classes.2da]
ChangeRow0=use_appearance

[use_appearance]
RowIndex=5
appearance=2DAMEMORY10  ; Use token from previous file modification
```

## Common Pitfalls and Troubleshooting

### Row Not Found Errors

**Problem:** "The source row was not found during the search"

**Solutions:**

- Verify the target row exists (check RowIndex is within bounds, RowLabel matches exactly, or LabelIndex value exists in "label" column)
- Ensure case-sensitivity: `RowLabel=MyLabel` will not match `mylabel`
- Check that the 2DA file has been loaded correctly
- Verify `!SourceFile` is correct if using a custom source file

**Example Fix:**

```ini
; Before (may fail if row doesn't exist)
[modify_row]
RowIndex=999
label=MODIFIED

; After (check row exists first, or use safer targeting)
[modify_row]
RowLabel=1
label=MODIFIED
```

### Token Not Defined Errors

**Problem:** "2DAMEMORY# was not defined before use" or "StrRef# was not defined before use"

**Solutions:**

- Ensure the token is created **before** it's used
- For 2DAMEMORY tokens: Create in an earlier modification in the same file or previous file
- For StrRef tokens: Ensure they're created in `[TLKList]` or earlier in `[2DAList]`
- Check token numbers match exactly (no typos)

**Example Fix:**

```ini
; Wrong - token used before creation
[add_row]
label=NEW
appearance=2DAMEMORY10
2DAMEMORY10=RowIndex    ; Too late!

; Correct - token created first
[add_row]
label=NEW
2DAMEMORY10=RowIndex     ; Create first
appearance=2DAMEMORY10   ; Use after creation
```

**Note:** Within the same modification section, memory storage operations (`2DAMEMORY#=...`) are evaluated **after** cell modifications (`ColumnName=...`), so you cannot use a token in a cell value and create it in the same section.

**Example of the problem:**

```ini
; This will FAIL - token used before it's created
[add_row]
label=NEW
appearance=2DAMEMORY10    ; Tries to use token 10 (not yet created)
2DAMEMORY10=RowIndex      ; Creates token 10 (too late!)
```

**Solution:** Create tokens in earlier modifications, then use them in later ones.

### Invalid Column Names

**Problem:** Column doesn't exist in the 2DA file

**Solutions:**

- Verify column names match exactly (case-sensitive)
- Use AddColumn to add the column first if it doesn't exist
- Check the source 2DA file to see available columns

### ExclusiveColumn Behavior

**Problem:** Unexpected row modification instead of adding new row (or vice versa)

**Solutions:**

- Understand that `ExclusiveColumn` checks if a row with the same value exists
- If match found: existing row is modified
- If no match: new row is added
- Ensure the column specified in `ExclusiveColumn` is included in the cell modifications

**Example:**

```ini
; This will modify existing row if label="MY_APPEARANCE" exists
[add_row]
ExclusiveColumn=label
label=MY_APPEARANCE
name=StrRef100
```

### AddColumn Memory Storage Syntax

**Problem:** Incorrect syntax for storing values from new column

**Solutions:**

- Use `I#` format for row index: `2DAMEMORY#=I5` (stores value from row index 5 in the new column)
- Use `Llabel` format for row label: `2DAMEMORY#=L1` (stores value from row with label "1" in the new column)
- Memory is stored **after** the column is created and all insert values (`I#=` and `Llabel=`) are applied
- Cannot use other RowValue types (like `RowIndex`, `RowLabel`, `ColumnName`, etc.) directly in AddColumn memory storage - only `I#` and `Llabel` formats are supported
- The `I#` or `Llabel` syntax tells the patcher to retrieve the cell value from that specific row in the newly created column

**Example:**

```ini
[add_column]
ColumnLabel=NewColumn
DefaultValue=0
I5=Value
2DAMEMORY10=I5    ; Correct - stores value from row index 5
2DAMEMORY11=RowIndex  ; Wrong - RowIndex not supported in AddColumn memory storage
```

### Target Type Confusion

**Problem:** Confusion between `RowLabel` and `LabelIndex`

**Solutions:**

- `RowLabel=value` → Uses the row's label (first column value) to find the row
- `LabelIndex=value` → Searches the "label" column for a matching value
- Use `RowLabel` when you know the row label value
- Use `LabelIndex` when you need to search within a column named "label"

### Empty String vs Missing Values

**Problem:** Confusion about `****` vs omitted keys

**Solutions:**

- `****` explicitly sets a cell to an empty string
- Omitting a column key leaves the cell unchanged (in ChangeRow/CopyRow) or empty (in AddRow)
- Use `****` when you want to explicitly clear a value

### Special Functions Not Working

**Problem:** `high()`, `RowIndex`, `RowLabel` not working as expected

**Solutions:**

- Special functions only work in ChangeRow, AddRow, and CopyRow cell values
- They do **not** work in AddColumn inserts or default values
- `high()` without column name uses the current column context
- Check syntax: `high()` not `high`, `RowIndex` not `Rowindex`

## Integration with Other Sections

### Using StrRef Tokens from TLKList

Since `[2DAList]` runs after `[TLKList]`, you can use `StrRef#` tokens in your 2DA modifications:

```ini
[TLKList]
StrRef500=Custom Appearance Name

[2DAList]
Table0=appearance.2da

[appearance.2da]
AddRow0=new_appearance

[new_appearance]
RowLabel=100
label=CUSTOM_APPEARANCE
name=StrRef500
```

### Creating 2DAMEMORY Tokens for GFFList

Any `2DAMEMORY#` tokens you create in `[2DAList]` are available in `[GFFList]`:

```ini
[2DAList]
Table0=appearance.2da

[appearance.2da]
AddRow0=store_appearance_id

[store_appearance_id]
RowLabel=100
label=MY_APPEARANCE
2DAMEMORY10=RowIndex

[GFFList]
File0=item.uti

[item.uti]
ModelVariation=2DAMEMORY10  ; Use stored row index
```

### Using 2DAMEMORY Tokens in CompileList

In `[CompileList]`, you can use `2DAMEMORY#` tokens as preprocessor tokens in NSS scripts:

```ini
[2DAList]
Table0=appearance.2da

[appearance.2da]
AddRow0=store_id

[store_id]
RowLabel=100
2DAMEMORY10=RowIndex

[CompileList]
File0=script.nss

[script.nss]
; In script.nss:
; ChangeObjectAppearance(OBJECT_SELF, #2DAMEMORY10#);
```

### Using 2DAMEMORY Tokens in HACKList

In `[HACKList]`, you can use `2DAMEMORY#` tokens for binary patch values:

```ini
[2DAList]
Table0=appearance.2da

[appearance.2da]
AddRow0=store_id

[store_id]
RowLabel=100
2DAMEMORY10=RowIndex

[HACKList]
File0=script.ncs

[script.ncs]
40=2DAMEMORY10  ; Modify offset 40 (hex 0x28) with stored value
```

### Using 2DAMEMORY Tokens in SSFList

In `[SSFList]`, you can use `2DAMEMORY#` tokens for sound stringref assignments:

```ini
[2DAList]
Table0=appearance.2da

[appearance.2da]
AddRow0=store_id

[store_id]
RowLabel=100
2DAMEMORY10=RowIndex

[SSFList]
File0=soundset.ssf

[soundset.ssf]
Battlecry 1=2DAMEMORY10  ; Use stored value as stringref
```

## Processing Order and Execution

### Modification Order Within a File

Modifications within a single 2DA file are processed in the order they appear in the file section:

```ini
[appearance.2da]
ChangeRow0=modify_first
ChangeRow1=modify_second
AddRow0=add_new
CopyRow0=copy_existing
AddColumn0=add_column
```

Processing order:

1. All `ChangeRow#` modifications (in order)
2. All `AddRow#` modifications (in order)
3. All `CopyRow#` modifications (in order)
4. All `AddColumn#` modifications (in order)

**Important:** Since AddColumn runs last, columns added by AddColumn cannot be used in earlier ChangeRow/AddRow/CopyRow modifications within the same file. However, tokens created in earlier modifications are available for AddColumn.

### Cross-File Token Availability

Tokens created in earlier files are available to later files:

```ini
[2DAList]
Table0=appearance.2da
Table1=classes.2da

[appearance.2da]
AddRow0=create_token
[create_token]
RowLabel=100
2DAMEMORY10=RowIndex

[classes.2da]
ChangeRow0=use_token
[use_token]
RowIndex=5
appearance=2DAMEMORY10  ; Token from previous file is available
```

## Advanced Patterns

### Pattern 1: Conditional Row Creation

Use `ExclusiveColumn` to prevent duplicate rows:

```ini
[add_appearance]
ExclusiveColumn=label
label=MY_APPEARANCE
name=StrRef100
```

This will modify existing row if `label=MY_APPEARANCE` exists, otherwise add a new row.

### Pattern 2: Storing Multiple Values from One Row

```ini
[modify_appearance]
RowIndex=5
2DAMEMORY10=RowIndex
2DAMEMORY11=RowLabel
2DAMEMORY12=modeltype
2DAMEMORY13=name
```

Store multiple values for use in other sections.

### Pattern 3: Incremental Row Labels

Use `high()` to automatically assign the next available row label:

```ini
[add_appearance]
RowLabel=high()
label=NEW_APPEARANCE
```

### Pattern 4: Copy and Modify Pattern

Copy an existing row, modify some values, and store the new row index:

```ini
[copy_modify]
RowIndex=1
ExclusiveColumn=label
label=MODIFIED_COPY
modeltype=3
2DAMEMORY10=RowIndex
```

## Summary

The `[2DAList]` section provides powerful tools for modifying 2DA files:

- **ChangeRow**: Modify existing rows by index, label, or label column
- **AddRow**: Add new rows with optional duplicate checking
- **CopyRow**: Copy existing rows with modifications
- **AddColumn**: Add new columns with default and custom values
- **Memory Tokens**: Store values for cross-file and cross-section use
- **Token Integration**: Use StrRef tokens from TLKList and provide 2DAMEMORY tokens to other sections

Key points to remember:

1. Tokens are evaluated after cell modifications within the same section
2. Tokens persist across multiple files in the same `[2DAList]` section
3. `ExclusiveColumn` provides smart duplicate prevention
4. Special functions (`high()`, `RowIndex`, `RowLabel`) only work in ChangeRow/AddRow/CopyRow
5. AddColumn runs last within a file, so new columns can't be used in earlier modifications
6. All memory tokens are available to subsequent sections (GFFList, CompileList, HACKList, SSFList)

For more information on related sections, see:

- [TSLPatcher TLKList Syntax](TSLPatcher-TLKList-Syntax.md) - Creating StrRef tokens
- [TSLPatcher GFFList Syntax](TSLPatcher-GFFList-Syntax.md) - Using 2DAMEMORY tokens in GFF files
- [TSLPatcher CompileList Syntax](TSLPatcher's-Official-Readme.md) - Using tokens in script compilation
- [TSLPatcher HACKList Syntax](TSLPatcher-HACKList-Syntax.md) - Using tokens in binary patches
- [TSLPatcher SSFList Syntax](TSLPatcher-SSFList-Syntax.md) - Using tokens in sound sets
