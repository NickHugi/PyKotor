# TSLPatcher 2DAList Syntax - Complete Guide

## Overview

This document explains **ALL** syntax and functionality for INI-based 2DA patches in TSLPatcher/HoloPatcher. 2DA files are two-dimensional arrays that contain game data like character appearances, items, planets, and more. The patching system allows you to modify these tables in sophisticated ways.

---

## Table of Contents

1. [Basic Structure](#basic-structure)
2. [Modification Types](#modification-types)
3. [Dynamic Value References](#dynamic-value-references)
4. [Memory System](#memory-system)
5. [Complete Examples](#complete-examples)
6. [Special Values and Symbols](#special-values-and-symbols)
7. [File-Level Options](#file-level-options)
8. [Important Notes](#important-notes)
9. [Troubleshooting](#troubleshooting)

---

## Basic Structure

All 2DA patches begin with a `[2DAList]` section that declares which 2DA files you want to modify:

```ini
[2DAList]
Table0=appearance.2da
Table1=baseitems.2da
Table2=portraits.2da

; Optional: Set default destination folder
!DefaultDestination=Override

; Optional: Set default source folder within your mod
!DefaultSourceFolder=tslpatchdata/2da
```

Then, for each file declared, you create a section `[filename.2da]` and list the modifications:

```ini
[appearance.2da]
ChangeRow0=appearance_change_0
AddRow0=appearance_add_0
AddColumn0=appearance_column_0

; Optional file-level settings:
!Destination=Override
!SaveAs=appearance_patched.2da
!SourceFile=appearance.2da
```

Each modification entry (e.g., `ChangeRow0`, `AddRow0`) references another section where the actual changes are defined.

---

## Modification Types

There are **four types** of 2DA modifications:

### 1. ChangeRow - Modify Existing Row

**Purpose:** Change values in an existing row.

**Basic Syntax:**

```ini
[my_change]
RowIndex=5          ; Target row by index (0-based)
ColumnName=NewValue ; Change a column's value
```

**Alternative Targeting Methods:**

```ini
[my_change]
RowLabel=labelname  ; Target row by its label (the first column value)
ColumnName=NewValue
```

```ini
[my_change]
LabelIndex=labelvalue  ; Find row where 'label' column equals this value
ColumnName=NewValue
```

**Important Notes:**

- You must specify ONE of: `RowIndex`, `RowLabel`, or `LabelIndex`
- All unspecified columns remain unchanged
- If the row doesn't exist, the patch will warn but continue

**Example:**

```ini
[appearance.2da]
ChangeRow0=fix_vima_head

[fix_vima_head]
RowLabel=Vima
normalhead=2DAMEMORY1
```

This finds the row with label "Vima" and changes its `normalhead` column to the value stored in 2DAMEMORY token #1.

---

### 2. AddRow - Add New Row

**Purpose:** Add a new row to the 2DA file.

**Basic Syntax:**

```ini
[my_add]
RowLabel=newrow    ; Optional: specify the label (defaults to next number)
Column1=Value1     ; Set column values
Column2=Value2
```

**ExclusiveColumn (Advanced):**

```ini
[my_add]
ExclusiveColumn=SomeColumn  ; Check if value exists in this column
SomeColumn=UniqueValue      ; If this value exists, UPDATE that row instead
OtherColumn=NewValue        ; Otherwise, add a new row with these values
```

**How ExclusiveColumn Works:**

- If you specify `ExclusiveColumn=AppearanceID` and `AppearanceID=123`
- The patcher checks if ANY row has `AppearanceID=123`
- **If found:** It updates that existing row with your new values
- **If not found:** It adds a completely new row
- This is useful for ensuring you don't create duplicate entries

**Row Label Options:**

- **Specified:** `RowLabel=custom_name` - Use this exact label
- **Default:** Omit `RowLabel` - Auto-generate based on current row count

**Example:**

```ini
[appearance.2da]
AddRow0=add_new_character

[add_new_character]
RowLabel=MyCustomCharacter
label=MyCustomCharacter
walkdist=1.813
rundist=3.96
modeltype=B
normalhead=517
```

---

### 3. AddColumn - Add New Column

**Purpose:** Add a new column to the 2DA file.

**Basic Syntax:**

```ini
[my_column]
ColumnLabel=NewColumnName  ; Required: Name of new column
DefaultValue=****          ; Required: Default value for all rows (use **** for empty)
```

**Setting Values for Specific Rows:**

You can override the default value for specific rows:

```ini
[my_column]
ColumnLabel=MyNewColumn
DefaultValue=0             ; All rows get "0" by default
I5=CustomValue             ; Row index 5 gets "CustomValue"
Llabelname=AnotherValue    ; Row with label "labelname" gets "AnotherValue"
```

**Syntax:**

- `I#=value` - Set value for row at index #
- `L#=value` - Set value for row with label #
- `#` is the row index or label

**Example:**

```ini
[appearance.2da]
AddColumn0=add_mod_support

[add_mod_support]
ColumnLabel=CompatibilityPatch
DefaultValue=0
I0=1                      ; Row 0 gets "1"
LPlayer=Installed         ; Row with label "Player" gets "Installed"
```

---

### 4. CopyRow - Clone and Modify Row

**Purpose:** Copy an existing row and optionally modify it.

**Basic Syntax:**

```ini
[my_copy]
RowIndex=3                ; Copy FROM this row
Column1=ModifiedValue     ; Change values in the copy
```

**How It Works:**

1. Find the source row (specified by `RowIndex`, `RowLabel`, or `LabelIndex`)
2. Create a new row with all the source row's values
3. Apply any specified column changes to the new row
4. Add it to the table

**ExclusiveColumn Support:**

Like `AddRow`, `CopyRow` also supports `ExclusiveColumn`:

```ini
[my_copy]
RowIndex=10               ; Copy row 10
ExclusiveColumn=ID        ; Check for duplicate ID
ID=123                    ; If ID=123 exists, UPDATE that row instead of adding
Name=Modified Name        ; Otherwise, add new row with these changes
```

**Example:**

```ini
[appearance.2da]
CopyRow0=clone_player_model

[clone_player_model]
RowLabel=Player
RowLabel=Player_Variant
normalhead=2DAMEMORY5
texa=Player_NewVariant
```

This copies the Player row, renames it to "Player_Variant", and changes specific columns.

---

## Dynamic Value References

Instead of hardcoded values, you can use **dynamic references** that are calculated at patch time:

### Memory References

#### StrRef# - TLK Memory

Reference a string reference (StrRef) that was stored earlier:

```ini
normalhead=StrRef5  ; Use whatever value was stored in StrRef5 token
```

#### 2DAMEMORY# - 2DA Memory

Reference a value that was stored earlier from another 2DA operation:

```ini
normalhead=2DAMEMORY1  ; Use whatever value was stored in 2DAMEMORY1 token
```

### Special Runtime References

#### RowIndex - Current Row Index

**Only usable when storing values to memory:**

```ini
2DAMEMORY5=RowIndex    ; Store the current row's index to 2DAMEMORY5
```

This stores "5" if the row being processed is at index 5.

#### RowLabel - Current Row Label

**Only usable when storing values to memory:**

```ini
2DAMEMORY5=RowLabel    ; Store the current row's label to 2DAMEMORY5
```

This stores the label (e.g., "Player") of the row being processed.

#### High() - Maximum Value

**Purpose:** Get the highest numeric value from a column or row labels.

**Syntax:**

```ini
MyColumn=High()           ; Get max from row labels
MyColumn=High(ColumnName) ; Get max from a specific column
```

**How It Works:**

- `High()` without column: Finds the highest **numeric row label** across the entire table
- `High(ColumnName)`: Finds the highest **numeric value** in that specific column

**Example:**

```ini
[my_add]
RowLabel=High()        ; Auto-number by finding highest existing row label
appearancenumber=High(appearancenumber)  ; Use next available appearance number
```

**Real Use Case:**

If your 2DA has rows labeled 0, 1, 2, 3... and you want to add the next one:

```ini
[appearance.2da]
AddRow0=add_next_row

[add_next_row]
RowLabel=High()    ; This becomes "4" (highest label is 3)
label=NewEntry
```

---

## Memory System

The memory system allows you to **store and reuse values** across different parts of your patch.

### Storing Values

You can store values **from any modification** using `2DAMEMORY#` or `StrRef#` assignments:

```ini
[my_change]
RowIndex=5
2DAMEMORY5=RowIndex      ; Store row index "5"
StrRef10=2DAMEMORY5      ; Copy 2DAMEMORY5 to StrRef10
MyColumn=SomeValue
```

**Valid Storage Targets:**

- `2DAMEMORY#=RowIndex` - Store current row index
- `2DAMEMORY#=RowLabel` - Store current row label  
- `2DAMEMORY#=ColumnName` - Store value from a column in the current row
- `2DAMEMORY#=2DAMEMORY#` - Copy from another 2DA memory token
- `StrRef#=Value` - Store a string reference

**Storage Scenarios:**

1. **Store Row Index:**

```ini
2DAMEMORY1=RowIndex    ; Stores the index of the row being modified
```

2. **Store Row Label:**

```ini
2DAMEMORY1=RowLabel    ; Stores the label of the row being modified
```

3. **Store Column Value:**

```ini
2DAMEMORY1=normalhead  ; Stores the VALUE from the normalhead column
```

4. **Store for AddColumn:**

For `AddColumn`, you can store which row to use:

```ini
[my_column]
ColumnLabel=NewColumn
DefaultValue=****
2DAMEMORY2=I5          ; Store that we're referencing row index 5
```

### Using Stored Values

Once stored, you can reference them anywhere:

```ini
; Earlier in your patch:
[setup_storage]
RowIndex=10
2DAMEMORY1=RowIndex    ; Store "10"

; Later in your patch:
[use_storage]
normalhead=2DAMEMORY1  ; Use "10" as the value
```

### For AddColumn: I# and L# Storage Syntax

When using `AddColumn`, you can store a reference to a row:

```ini
[my_column]
ColumnLabel=NewColumn
DefaultValue=0
I5=100                  ; Row 5 gets value "100"
2DAMEMORY2=I5          ; Store reference "I5" for later use
```

Later, you can retrieve the actual value:

```ini
value=2DAMEMORY2       ; Resolves to "100" (the value from row 5)
```

---

## Complete Examples

### Example 1: Simple Character Appearance Addition

```ini
[2DAList]
Table0=appearance.2da
Table1=heads.2da

[heads.2da]
AddRow0=new_head_1
AddRow1=new_head_2

[new_head_1]
head=PFHC10
2DAMEMORY36=RowIndex    ; Store row index for later use

[new_head_2]
head=PMHB03
2DAMEMORY37=RowIndex    ; Store row index for later use

[appearance.2da]
AddRow0=new_appearance

[new_appearance]
label=Vima
walkdist=1.6
rundist=3.96
modeltype=B
normalhead=2DAMEMORY36  ; Use the head we just added
backuphead=2DAMEMORY36
2DAMEMORY5=RowIndex     ; Store this appearance's row index for portraits
```

### Example 2: Portraits with Dynamic Referencing

```ini
[2DAList]
Table0=portraits.2da

[portraits.2da]
AddRow0=add_vima_portrait

[add_vima_portrait]
baseresref=po_pvima
sex=0
appearancenumber=High(appearancenumber)  ; Auto-number portrait
race=6
plot=0
forpc=0
baseresrefe=po_pvima
baseresrefve=po_pvima
baseresrefvve=po_pvima
baseresrefvvve=po_pvima
2DAMEMORY1=appearancenumber  ; Store the generated number

; Now reference it in appearance.2da:
[appearance.2da]
ChangeRow0=update_player_appearance

[update_player_appearance]
RowLabel=Player
normalhead=2DAMEMORY1  ; Use the portrait number we generated
```

### Example 3: Adding Support Column

```ini
[2DAList]
Table0=baseitems.2da

[baseitems.2da]
AddColumn0=mod_compatibility

[mod_compatibility]
ColumnLabel=MyModVersion
DefaultValue=0         ; Most items don't have this mod's changes
I15=1                  ; Item at row 15 is version 1
I23=1                  ; Item at row 23 is version 1
Lg_i_blstr001=1        ; Item with label "g_i_blstr001" is version 1
```

### Example 4: Conditional Row Addition

```ini
[2DAList]
Table0=appearance.2da

[appearance.2da]
AddRow0=conditional_add

[conditional_add]
ExclusiveColumn=label
label=MyCustomAppearance     ; If this label exists, update it
walkdist=2.0                 ; Otherwise, add new row
rundist=4.0
modeltype=B
```

### Example 5: Complex Workflow with Memory

```ini
[2DAList]
Table0=heads.2da
Table1=appearance.2da
Table2=portraits.2da

; Step 1: Add a head and store its ID
[heads.2da]
AddRow0=add_custom_head

[add_custom_head]
head=PFHC10
2DAMEMORY10=RowIndex     ; Store head row index

; Step 2: Add an appearance that uses that head
[appearance.2da]
AddRow0=add_custom_appearance

[add_custom_appearance]
label=MyCustomCharacter
normalhead=2DAMEMORY10   ; Reference the head we added
2DAMEMORY20=RowIndex     ; Store appearance row index

; Step 3: Add a portrait that references the appearance
[portraits.2da]
AddRow0=add_custom_portrait

[add_custom_portrait]
baseresref=po_mycustom
appearancenumber=2DAMEMORY20  ; Reference the appearance we added
sex=0
2DAMEMORY30=RowIndex     ; Store portrait row index for future use
```

---

## Special Values and Symbols

### Empty String (****)

Use `****` to represent an empty string:

```ini
DefaultValue=****        ; All cells get empty string
MyColumn=****            ; This specific column gets empty string
```

### Line Endings

For multi-line text values, use special tokens:

```
Text=Line 1<#LF#>Line 2<#LF#>Line 3
```

- `<#LF#>` - Line feed (newline)
- `<#CR#>` - Carriage return

### Float Values

Use either comma or period for decimals:

```
Value=3.14    ; Valid
Value=3,14    ; Also valid (automatically converted)
```

---

## File-Level Options

For each `[filename.2da]` section, you can specify:

```ini
[appearance.2da]
!Destination=Modules/module_folder  ; Where to save the patched file
!SaveAs=appearance_custom.2da      ; Save with different name
!SourceFile=appearance_v2.2da      ; Load different source file
!ReplaceFile=0                      ; 1 = replace, 0 = don't replace
!OverrideType=warn                  ; Conflict handling: warn/ignore/rename
```

---

## Important Notes

### Order Matters

Patches are applied **in order**. Plan your sequence:

```ini
[2DAList]
Table0=appearance.2da

[appearance.2da]
; ✅ CORRECT: Store first, then use
AddRow0=setup
AddRow1=use_setup

[setup]
RowLabel=Test
2DAMEMORY1=RowIndex

[use_setup]
normalhead=2DAMEMORY1  ; ✅ 2DAMEMORY1 is defined
```

### Target Type Conflicts

You can only specify ONE target type:

```ini
[my_change]
RowIndex=5          ; ✅ One target
RowLabel=Player     ; ❌ ERROR: Can't specify both
```

### Memory Token Management

- Tokens are global across the entire patch
- Store values before using them
- Reusing the same token overwrites previous value
- Start numbering from 0 or 1 based on your needs

### ExclusiveColumn Best Practices

Use `ExclusiveColumn` when:

- You want to ensure no duplicates
- You're not sure if a row already exists
- You want idempotent patches (safe to run multiple times)

---

## Troubleshooting

**"Row not found" warning:**

- Check spelling of RowLabel
- Verify RowIndex is within bounds
- Ensure LabelIndex value exists in label column

**"2DAMEMORY# not defined" error:**

- You're using a token before storing to it
- Reorder your patches
- Check token number spelling

**Values not changing:**

- Verify column names match exactly (case-sensitive)
- Check you're targeting the right row
- Ensure patches aren't being overwritten by later ones

---

## Advanced: Combining Everything

Here's a complex example showing multiple features:

```ini
[2DAList]
Table0=appearance.2da
Table1=heads.2da
Table2=portraits.2da
!DefaultDestination=Override

; ==========================================
; Phase 1: Add heads
; ==========================================
[heads.2da]
AddRow0=head_vima
AddRow1=head_variant

[head_vima]
head=PFHC10
2DAMEMORY100=RowIndex    ; Store head ID

[head_variant]
head=PFHC11
2DAMEMORY101=RowIndex    ; Store variant head ID

; ==========================================
; Phase 2: Add appearances using heads
; ==========================================
[appearance.2da]
AddRow0=app_vima
AddRow1=app_vima_variant

[app_vima]
label=Vima
normalhead=2DAMEMORY100   ; Use head we added
backuphead=2DAMEMORY100
modeltype=B
walkdist=1.6
rundist=3.96
2DAMEMORY200=RowIndex     ; Store appearance ID

[app_vima_variant]
ExclusiveColumn=label
label=Vima                 ; Update existing if found
normalhead=2DAMEMORY101    ; Use variant head
backuphead=2DAMEMORY101
modeltype=B
walkdist=1.6
rundist=3.96

; ==========================================
; Phase 3: Add portraits
; ==========================================
[portraits.2da]
AddRow0=port_vima
AddColumn0=compatibility_flags

[port_vima]
baseresref=po_pvima
appearancenumber=2DAMEMORY200  ; Use appearance we added
sex=0
race=6
2DAMEMORY300=RowIndex          ; Store portrait ID

; Add support column
[compatibility_flags]
ColumnLabel=HasCustomPortrait
DefaultValue=0
L0=1                          ; Portrait at label 0 has the custom portrait

; ==========================================
; Phase 4: Reference in other mods
; ==========================================
; Now 2DAMEMORY200 contains the appearance row ID
; 2DAMEMORY300 contains the portrait row ID
; These can be used in GFF patches, TLK patches, etc.
```

---

## Related Documentation

- [TSLPatcher's Official Readme](TSLPatcher's-Official-Readme)
- [HoloPatcher Documentation](HoloPatcher)
- [HoloPatcher README for Mod Developers](HoloPatcher-README-for-mod-developers.)
- [Mod Creation Best Practices](Mod-Creation-Best-Practices)

