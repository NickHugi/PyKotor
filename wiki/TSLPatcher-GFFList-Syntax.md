# TSLPatcher GFFList Syntax Documentation

This guide explains how to modify GFF files using TSLPatcher syntax. For the complete GFF file format specification, see [GFF File Format](GFF-File-Format). For general TSLPatcher information, see [TSLPatcher's Official Readme](TSLPatcher's-Official-Readme). For HoloPatcher-specific information, see [HoloPatcher README for Mod Developers](HoloPatcher-README-for-mod-developers.).

## Overview

The `[GFFList]` section in TSLPatcher's `changes.ini` lets you edit or add data inside GFF (Generic File Format) files used across KotOR. You will use this to change items (.UTI), creatures (.UTC), dialogs (.DLG), placeables (.UTP), triggers (.UTT), waypoints (.UTW), modules (.MOD), areas (.ARE), journal entries (.JRL), paths (.PTH), module info (.IFO), and scripts data (.GIT).

If you can fill out a form, you can use `[GFFList]`.

## Table of Contents

- [Quick Start](#quick-start)
- [Cheatsheet](#cheatsheet)
- [Basic Structure](#basic-structure)
- [File-Level Configuration](#file-level-configuration)
- [Modifying Existing Fields](#modifying-existing-fields)
- [Adding New Fields](#adding-new-fields)
- [Field Types and Value Syntax](#field-types-and-value-syntax)
- [Memory Token System](#memory-token-system)
- [Nested Structures](#nested-structures)
- [Special Features](#special-features)
- [Common Pitfalls and Troubleshooting](#common-pitfalls-and-troubleshooting)
- [Execution Order and Dependencies](#execution-order-and-dependencies)
- [Complete Examples](#complete-examples)

## Quick Start

<!-- markdownlint-disable MD029 -->
1. Add your file under `[GFFList]`

```ini
[GFFList]
File0=my_item.uti
```

2. Create a section named exactly like that file and set where to save it:

```ini
[my_item.uti]
!Destination=override
```

3. Change an existing field by writing its path on the left and the new value on the right:

```ini
BaseItem=28
LocalizedName(strref)=12345
Comment(lang0)=Hello there
```

4. Add a brand-new field using `AddField#` → create another section for its details:

```ini
AddField0=new_property

[new_property]
FieldType=Struct
Path=PropertyList
Label=
TypeId=7
```

5. Use tokens when a value comes from earlier steps (TLK/2DA):

```ini
ModelVariation=2DAMEMORY5
Description=StrRef10
```
<!-- markdownlint-enable MD029 -->

That's it. The rest of this page explains the knobs and dials you'll use as your files get more complex.

## Cheatsheet

- Paths use backslashes: `Parent\Child\Field`
- Lists use numbers: `RepliesList\0\Text`
- Localized strings use parentheses on the field name:
  - `(strref)` → set the dialog.tlk reference
  - `(lang0)`..`(lang9)` → set per-language text
- Vectors: `Position=1.5|2.0|3.0`, `Orientation=0.0|0.0|0.0|1.0`
- Tokens as values:
  - `StrRef#` → a TLK token you set elsewhere
  - `2DAMEMORY#` → a 2DA token you set elsewhere
- Tokens for dynamic field targets and list indices:
  - In AddField: `2DAMEMORY#=ListIndex` saves where a struct was inserted
  - `2DAMEMORY#=!FieldPath` saves the full path to a field you just added
  - Later: use that `2DAMEMORY#` in place of a field path to modify it

## Basic Structure

```ini
[GFFList]
!DefaultDestination=override
!DefaultSourceFolder=.  ; Note: `.` refers to the tslpatchdata folder (where changes.ini is located)
File0=example.dlg
Replace0=different_dlg.dlg

[example.dlg]
!Destination=override
!SourceFolder=.
!SourceFile=source.dlg
!ReplaceFile=1

; Modify existing fields
FieldName=123
NestedField\0\SubField=value

; Add new fields
AddField0=new_field_add

[new_field_add]
FieldType=Byte
Path=
Label=MyNewField
Value=42

; Use 2DA memory tokens
2DAMEMORY0=!FieldPath
2DAMEMORY1=2DAMEMORY2
```

The `[GFFList]` section declares GFF files to patch. Each entry references another section with the same name as the filename.

## File-Level Configuration

### Top-Level Keys in [GFFList]

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `!DefaultDestination` | string | `override` | Default destination for all GFF files in this section |
| `!DefaultSourceFolder` | string | `.` | Default source folder for GFF files. Relative path from `mod_path` (typically the `tslpatchdata` folder, which is the parent directory of `changes.ini` and `namespaces.ini`). When `.`, refers to the `tslpatchdata` folder itself. Path resolution: `mod_path / !DefaultSourceFolder / filename` |

### File Section Configuration

Each GFF file requires its own section (e.g., `[example.dlg]`).

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `!Destination` | string | Inherited from `!DefaultDestination` | Where to save the modified file (`override` or `path\to\file.mod`) |
| `!SourceFolder` | string | Inherited from `!DefaultSourceFolder` | Source folder for the GFF file. Relative path from `mod_path` (typically the tslpatchdata folder). When `.`, refers to the tslpatchdata folder itself. |
| `!SourceFile` | string | Same as section name | Alternative source filename (useful for multiple setup options using different source files) |
| `!ReplaceFile` | 0/1 | 0 | If `1`, overwrite existing file before applying modifications. If `0` (default), modify the existing file in place. |
| `!SaveAs` | string | Same as section name | Alternative filename to save as (useful for renaming files during installation) |
| `!OverrideType` | string | `ignore` | How to handle existing files in Override when destination is an ERF/RIM archive. Valid values: `ignore` (default), `warn` (log warning), `rename` (prefix with `old_`) |

**Destination Values:**

- `override` or empty: Save to the Override folder
- `Modules\module.mod`: Insert into an ERF/MOD/RIM archive (use backslashes for path separators)
- Archive paths must be relative to the game folder root

**Source File Resolution:**

The patcher resolves source files in this order:

1. If `!ReplaceFile=1` or file doesn't exist at destination: Load from `mod_path / !SourceFolder / !SourceFile` (or section name if `!SourceFile` not set)
2. Otherwise: Load existing file from destination location (override or archive)
3. Apply all modifications from the section
4. Save to `!Destination` with name `!SaveAs` (or section name if `!SaveAs` not set)

## Modifying Existing Fields

To change an existing field's value, use the field name as the key:

```ini
[example.uti]
; Modify root-level field
LocalizedName=strref12345

; Modify nested field (use backslash to separate path components)
PropertiesList\0\Subtype=5
Comment(objref)=2DAMEMORY10

; Modify localized string strref
Comments(strref)=123

; Modify localized string substring (lang0 = English)
Comments(lang0)=Hello World

; Modify vector/orientation
Position=1.5|2.0|3.0
Orientation=0.0|0.0|0.0|1.0
```

### Field Path Syntax

- Use backslash (`\`) to separate hierarchy levels
- Use numeric indices for list elements: `ListName\0\Field`
- Case-sensitive labels
- Parenthesis syntax for complex types:
  - `FieldName(strref)` for localized string strref
  - `FieldName(lang0)` through `FieldName(lang9)` for language/gender strings

**Supported Memory Token Formats:**

- `StrRef#` - References TLK memory token
- `2DAMEMORY#` - References 2DA memory token

## Adding New Fields

Use `AddFieldN` keys to define new fields. Each requires its own section:

```ini
[example.uti]
AddField0=new_item_property

[new_item_property]
FieldType=Word
Path=
Label=NewProperty
Value=123
```

### AddField Section Structure

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `FieldType` | string | Yes | One of: Byte, Char, Word, Short, DWORD, Int, Int64, Double, Float, ExoString, ResRef, ExoLocString, Binary, Struct, List, Orientation, Position |
| `Label` | string | Yes* | Field name (max 16 alphanumeric characters, no spaces). Must be unique within the same STRUCT parent. |
| `Path` | string | No | Field location in GFF hierarchy. Empty string (`Path=`) means root level. For nested AddField sections, if `Path` is empty or not specified, it inherits the path from the parent AddField. Use backslashes to separate hierarchy levels. |
| `Value` | varies | Conditional | Field value (see Field Types below). Not used for Struct, List, or ExoLocString types. |
| `StrRef` | int/string | LocString only | TLK stringref value, `StrRef#` token, `2DAMEMORY#` token, or `-1` (no dialog.tlk reference) |
| `TypeId` | int/string | Struct only | Struct Type ID (numeric), `ListIndex` (auto-set to list index), `StrRef#` token, or `2DAMEMORY#` token |
| `lang#` | string | LocString only | Localized string entries where `#` is the language+gender ID (0-9). Use `<#LF#>` for linefeeds. |
| `AddField#` | string | No | Reference to another section for nested field addition |
| `2DAMEMORY#` | string | No | Store field path (`!FieldPath`), list index (`ListIndex`), or copy from another token (`2DAMEMORY#`) |

*Label is optional (blank) **only** when adding a STRUCT to a LIST field. All other field types require a label, including fields added inside structs.

### Understanding Struct vs Field Addition

There are two distinct scenarios when using AddField:

1. **Adding a STRUCT to a LIST**: When you want to add a new element to an existing LIST field
   - `FieldType=Struct` is required
   - `Label=` must be **blank** (LIST elements don't have labels)
   - `Path=` must point to the LIST field name (e.g., `Path=RepliesList`)
   - The struct will be appended to the end of the list

2. **Adding a field to a STRUCT**: When you want to add any field type (including structs) inside an existing or newly-created STRUCT
   - Any `FieldType` is allowed
   - `Label=` is **required** (except when the struct itself is being added to a list)
   - `Path=` can be empty to inherit from parent, or explicit to target a specific location

**Critical Distinction:**

```ini
; Scenario 1: Adding a STRUCT to a LIST (note blank Label)
[new_list_entry]
FieldType=Struct
Path=MyList              ; Points to the LIST field
Label=                   ; MUST be blank - list elements have no labels
TypeId=5

; Scenario 2: Adding a field INSIDE a struct (note Label is required)
[new_struct_field]
FieldType=Byte
Path=                    ; Can be empty (inherits) or explicit path
Label=MyField            ; MUST have a label - fields have names
Value=42
```

### Path Inheritance for Nested Fields

When adding nested fields via `AddField#`, child sections automatically inherit the parent's resolved path if their `Path=` is empty. This allows you to build complex nested structures without repeating full paths.

**Basic Path Inheritance (Struct within Struct):**

```ini
[parent_struct]
FieldType=Struct
Path=PropertyList
Label=NewProperty
AddField0=child_field

[child_field]
FieldType=Byte
Path=              ; Inherits "PropertyList\NewProperty" from parent
Label=SubField
Value=42
```

**Path Inheritance with Lists (Special Case):**

When adding a STRUCT to a LIST, the patcher automatically resolves the list index at runtime. Child fields added inside that struct inherit a path that includes the resolved index:

```ini
[example.dlg]
AddField0=new_reply

[new_reply]
FieldType=Struct
Path=RepliesList         ; Target the RepliesList field
Label=                   ; Blank - adding struct TO list
TypeId=5
AddField0=reply_text     ; Add a field INSIDE the newly-added struct
AddField1=reply_sound

[reply_text]
FieldType=ExoLocString
Path=                    ; Empty path inherits from parent
                        ; Parent resolves to "RepliesList\{index}" where {index} is the position
                        ; where the struct was added (e.g., "RepliesList\3")
Label=Text               ; Required - adding field INSIDE struct
StrRef=-1
lang0=New reply option

[reply_sound]
FieldType=ResRef
Path=                    ; Also inherits "RepliesList\{index}"
Label=Sound               ; Required - adding field INSIDE struct
Value=
```

**How Path Resolution Works:**

1. When you add a STRUCT to a LIST with `Path=MyList`, the patcher:
   - Finds the LIST field named "MyList"
   - Appends the new struct to the end of that list
   - The struct's position becomes its index (0-based: first element is 0, second is 1, etc.)

2. When child AddField sections have `Path=` empty:
   - They inherit the parent's resolved path
   - For structs in lists, this includes the dynamically-resolved index
   - Example: If the struct was added as the 5th element (index 4), child fields inherit `MyList\4\{field}`

3. You can override inheritance by explicitly setting `Path=` in the child section

### Complete Examples: Adding to Lists vs Adding to Structs

**Example 1: Adding a Property to an Item (Struct within Struct)**

```ini
[example.uti]
AddField0=item_property_struct

[item_property_struct]
FieldType=Struct
Path=PropertyList        ; Add struct to existing PropertyList
Label=                   ; Blank - struct is being added to list
TypeId=7
AddField0=property_subtype
AddField1=property_value

[property_subtype]
FieldType=Word
Path=                    ; Inherits "PropertyList\{index}\"
Label=Subtype            ; Required - field inside struct
Value=15

[property_value]
FieldType=Int
Path=                    ; Inherits "PropertyList\{index}\"
Label=Value              ; Required - field inside struct
Value=500
```

**Example 2: Adding a Nested Struct (Struct within Struct at Root Level)**

```ini
[example.uti]
AddField0=outer_struct

[outer_struct]
FieldType=Struct
Path=                    ; Root level
Label=OuterContainer     ; Required - field at root level
TypeId=100
AddField0=inner_struct

[inner_struct]
FieldType=Struct
Path=                    ; Inherits "OuterContainer" from parent
Label=InnerContainer     ; Required - field inside struct
TypeId=200
AddField0=inner_field

[inner_field]
FieldType=Byte
Path=                    ; Inherits "OuterContainer\InnerContainer"
Label=Data               ; Required - field inside struct
Value=42
```

**Example 3: Complex Dialog Entry (Struct in List with Multiple Nested Fields)**

```ini
[example.dlg]
AddField0=dialog_entry

[dialog_entry]
FieldType=Struct
Path=EntryList           ; Add struct to EntryList
Label=                   ; Blank - adding struct to list
TypeId=0
2DAMEMORY10=ListIndex    ; Store index for later cross-referencing
AddField0=entry_text
AddField1=entry_speaker
AddField2=entry_replies

[entry_text]
FieldType=ExoLocString
Path=                    ; Inherits "EntryList\{index}\"
Label=Text               ; Required
StrRef=StrRef50
lang0=Welcome to my shop!

[entry_speaker]
FieldType=ResRef
Path=                    ; Inherits "EntryList\{index}\"
Label=Speaker            ; Required
Value=shop_keeper

[entry_replies]
FieldType=List
Path=                    ; Inherits "EntryList\{index}\"
Label=RepliesList        ; Required
AddField0=reply_struct

[reply_struct]
FieldType=Struct
Path=                    ; Inherits "EntryList\{index}\RepliesList"
                        ; Note: This struct is being added to the NEWLY CREATED RepliesList
Label=                   ; Blank - adding struct to the nested list
TypeId=0
AddField0=reply_text_field

[reply_text_field]
FieldType=ExoLocString
Path=                    ; Inherits "EntryList\{entry_index}\RepliesList\{reply_index}\"
Label=Text               ; Required
StrRef=-1
lang0=Thank you!
```

### Overriding Path Inheritance

You can explicitly set `Path=` in child sections to override automatic inheritance:

```ini
[parent]
FieldType=Struct
Path=OuterList
Label=OuterStruct
AddField0=child1
AddField1=child2

[child1]
FieldType=Byte
Path=                    ; Inherits "OuterList\OuterStruct"
Label=InheritedPath
Value=1

[child2]
FieldType=Byte
Path=DifferentPath       ; Explicit path overrides inheritance
Label=CustomPath
Value=2
```

## Field Types and Value Syntax

### Integer Types

| Field Type | Size | Range | Example |
|------------|------|-------|---------|
| Byte (UInt8) | 8-bit unsigned | 0 to 255 | `Value=128` |
| Char (Int8) | 8-bit signed | -128 to 127 | `Value=-50` |
| Word (UInt16) | 16-bit unsigned | 0 to 65535 | `Value=1024` |
| Short (Int16) | 16-bit signed | -32768 to 32767 | `Value=-4096` |
| DWORD (UInt32) | 32-bit unsigned | 0 to 4294967295 | `Value=123456` |
| Int (Int32) | 32-bit signed | -2147483648 to 2147483647 | `Value=-1000000` |
| Int64 | 64-bit signed | -9223372036854775808 to 9223372036854775807 | `Value=1234567890` |

### Float Types

| Field Type | Size | Precision | Example |
|------------|------|-----------|---------|
| Float (Single) | 32-bit | ~7 digits | `Value=3.14159` |
| Double | 64-bit | ~15 digits | `Value=2.718281828` |

### String and Resource Types

| Field Type | Description | Example |
|------------|-------------|---------|
| ExoString | Null-terminated string | `Value=Hello World` |
| ResRef | Resource reference (max 16 chars) | `Value=myscript` |
| Binary | Binary data (hex/base64) | `Value=0xFF00FF00` or `Value=base64data` (HoloPatcher only) |

### Complex Types

#### ExoLocString (Localized String)

```ini
[localized_field]
FieldType=ExoLocString
Path=
Label=MyLocalizedString
StrRef=-1
lang0=Hello World
lang3=Bonjour le monde
```

- `StrRef`: Numeric value, `StrRef#`, `2DAMEMORY#`, or `-1`
- `lang#`: Language+gender substring (see table below)
- Use `<#LF#>` for linefeeds/carriage returns in lang# values

#### Position (Vector3)

```ini
[position_field]
FieldType=Position
Path=
Label=Location
Value=1.5|2.0|3.0
```

Three float coordinates (X, Y, Z) separated by `|`.

#### Orientation (Vector4)

```ini
[orientation_field]
FieldType=Orientation
Path=
Label=Rotation
Value=0.0|0.0|0.0|1.0
```

Four float components (quaternion) separated by `|`.

#### Struct

```ini
[struct_field]
FieldType=Struct
Path=
Label=MyStruct
TypeId=123
AddField0=nested_field
```

- `TypeId`: Numeric Type ID, `ListIndex`, `StrRef#`, or `2DAMEMORY#`
- `AddFieldN`: Child fields

#### List

```ini
[list_field]
FieldType=List
Path=
Label=MyList
AddField0=first_entry
AddField1=second_entry
```

- Contains `AddFieldN` entries for each element
- Elements are typically STRUCTs without labels

#### Binary (HoloPatcher Only)

```ini
[binary_field]
FieldType=Binary
Path=
Label=BinaryData
Value=0xFF00FF00
```

**Supported formats (auto-detected):**

1. **Binary string**: `Value=10101010` (sequence of 0s and 1s, processed in 8-bit chunks)
2. **Hex string**: `Value=0xFF00FF00` or `Value=FF00FF00` (hexadecimal, even length required; `0x` prefix optional)
3. **Base64**: `Value=SGVsbG8gV29ybGQ=` (standard Base64 encoding)

**Note:** The Binary field type is a HoloPatcher extension and is not supported by classic TSLPatcher. Classic TSLPatcher does not support adding Binary fields via GFFList.

### Language/Gender IDs for LocString

| ID | Language | Gender |
|----|----------|--------|
| 0 | English | Male |
| 1 | English | Female |
| 2 | French | Male |
| 3 | French | Female |
| 4 | German | Male |
| 5 | German | Female |
| 6 | Italian | Male |
| 7 | Italian | Female |
| 8 | Spanish | Male |
| 9 | Spanish | Female |

## Memory Token System

### 2DAMEMORY Tokens

Store and retrieve 2DA data:

```ini
[example.uti]
; Store root-level field path
2DAMEMORY0=!FieldPath

; Copy value between tokens
2DAMEMORY1=2DAMEMORY2

; Store list index
AddField0=new_list_entry
[new_list_entry]
FieldType=Struct
Path=
Label=
TypeId=5
2DAMEMORY0=ListIndex
```

**2DAMEMORY# Usage:**

1. At file level:
   - `2DAMEMORY#=!FieldPath` - Store absolute field path
   - `2DAMEMORY#=2DAMEMORY#` - Copy token value
   - Numeric ranges and 2DA operations not supported

2. In AddField sections:
   - `2DAMEMORY#=ListIndex` - Store list index
   - `2DAMEMORY#=!FieldPath` - Store field path
   - `2DAMEMORY#=2DAMEMORY#` - Copy token value

### StrRef Tokens

Reference TLK entries:

```ini
[example.uti]
; Direct strref reference
LocalizedName=strref12345

; Use TLK memory token
LocalizedName=StrRef5

; In AddField with LocString
AddField0=localized_description
[localized_description]
FieldType=ExoLocString
Path=
Label=Description
StrRef=StrRef8
```

### Using Memory Tokens as Values

```ini
; Use 2DA token as field value
[example.uti]
ModelVariation=2DAMEMORY5

; Use TLK token as field value
LocalizedName=StrRef3

; Use memory in nested fields
AddField0=dynamic_property
[dynamic_property]
FieldType=Word
Path=
Label=PropertyValue
Value=2DAMEMORY10
```

## Nested Structures

### Adding Structs to Existing Lists

When adding a STRUCT element to an existing LIST field, you must follow specific rules:

**Required Configuration:**

- `FieldType=Struct` - Only structs can be list elements
- `Label=` must be **blank** - List elements don't have labels
- `Path=` must point to the LIST field name (e.g., `Path=RepliesList`)
- `TypeId=` specifies the struct's Type ID (numeric, `ListIndex`, or token)

**Example - Basic Struct Addition to List:**

```ini
[example.dlg]
AddField0=new_reply_entry

[new_reply_entry]
FieldType=Struct
Path=RepliesList            ; Must point to the LIST field name
Label=                       ; MUST be blank - list elements have no labels
TypeId=5                     ; Struct Type ID
AddField0=reply_text        ; Add fields INSIDE the newly-added struct
AddField1=reply_sound

[reply_text]
FieldType=ExoLocString
Path=                       ; Empty path inherits parent's resolved path
                        ; Parent resolves to "RepliesList\{index}" automatically
Label=Text                   ; Required - fields inside structs have labels
StrRef=-1
lang0=New reply option

[reply_sound]
FieldType=ResRef
Path=                       ; Also inherits "RepliesList\{index}"
Label=Sound                  ; Required - fields inside structs have labels
Value=
```

**Understanding List Index Resolution:**

When you add a struct to a list, the patcher automatically determines which position (index) it occupies:

- First struct added becomes index 0
- Second struct added becomes index 1
- And so on...

This index is used to construct the full path for any child fields. For example, if you're adding the 3rd struct to RepliesList:

- The struct itself is added to `RepliesList[2]` (0-based indexing)
- Child fields with empty `Path=` inherit `RepliesList\2\{field_name}`

**Storing and Using the List Index:**

You can store the index where a struct is added for later reference:

```ini
[new_reply_entry]
FieldType=Struct
Path=RepliesList
Label=
TypeId=5
2DAMEMORY0=ListIndex        ; Store the index (e.g., 3) in 2DAMEMORY0
```

**Using `ListIndex` for Type ID:**

Some GFF structures require the Type ID to match the list index. Use `TypeId=ListIndex`:

```ini
[example.jrl]
AddField0=journal_category

[journal_category]
FieldType=Struct
Path=Categories
Label=                      ; Blank - adding struct to list
TypeId=ListIndex            ; Auto-sets Type ID to the list index where struct is added
AddField0=category_name

[category_name]
FieldType=ExoLocString
Path=                       ; Inherits "Categories\{index}\"
Label=Name                  ; Required - field inside struct
StrRef=StrRef100
lang0=My Custom Quests
```

**Complete Example - Dialog Entry with Cross-References:**

```ini
[example.dlg]
AddField0=new_entry
AddField1=new_reply

; Add a dialog entry
[new_entry]
FieldType=Struct
Path=EntryList
Label=                      ; Blank - adding struct to list
TypeId=0
2DAMEMORY5=ListIndex        ; Store entry index (e.g., 5)
AddField0=entry_text

[entry_text]
FieldType=ExoLocString
Path=                       ; Inherits "EntryList\{entry_index}\"
Label=Text                  ; Required
StrRef=-1
lang0=Hello, traveler!

; Add a reply that references the entry
[new_reply]
FieldType=Struct
Path=RepliesList
Label=                      ; Blank - adding struct to list
TypeId=0
2DAMEMORY6=ListIndex        ; Store reply index (e.g., 2)
AddField0=reply_text
AddField1=reply_entry_link

[reply_text]
FieldType=ExoLocString
Path=                       ; Inherits "RepliesList\{reply_index}\"
Label=Text                  ; Required
StrRef=-1
lang0=Thank you!

[reply_entry_link]
FieldType=DWORD
Path=                       ; Inherits "RepliesList\{reply_index}\"
Label=EntriesRepliesList   ; Required - field inside struct
Value=2DAMEMORY5            ; Use stored entry index as value
```

**Key Rules Summary:**

1. **Adding STRUCT to LIST**: `Label=` must be blank, `Path=` points to list name
2. **Adding field to STRUCT**: `Label=` is required, `Path=` can be empty (inherits) or explicit
3. **Path inheritance**: Child fields with empty `Path=` automatically inherit parent's resolved path, including list indices
4. **List index resolution**: Happens automatically at runtime based on insertion order
5. **TypeId=ListIndex**: Auto-sets Type ID to match the list index (used in journal categories, etc.)
6. **2DAMEMORY#=ListIndex**: Stores the index for later use in cross-references or calculations

### Adding Complete Nested Structures

This example demonstrates adding a LIST field containing STRUCT elements, with fields inside those structs:

```ini
[example.uti]
AddField0=item_properties

; First, add a new LIST field at the root level
[item_properties]
FieldType=List
Path=                      ; Empty - root level
Label=PropertyList         ; Required - fields have labels
AddField0=property_struct  ; Add a struct element to the newly-created list

; Add a STRUCT element to the PropertyList (list elements have no labels)
[property_struct]
FieldType=Struct
Path=                      ; Inherits "PropertyList" from parent
                        ; This struct will be added to the list, so Path resolves to 
                        ; "PropertyList\{index}" where index is automatically determined
Label=                     ; MUST be blank - adding struct to list
TypeId=7                   ; Property struct Type ID
AddField0=property_subtype
AddField1=property_value

; Add fields INSIDE the struct that was added to the list
[property_subtype]
FieldType=Word
Path=                      ; Inherits "PropertyList\{index}\" from parent struct
Label=Subtype              ; Required - fields inside structs have labels
Value=8

[property_value]
FieldType=Int
Path=                      ; Inherits "PropertyList\{index}\" from parent struct
Label=Value                ; Required - fields inside structs have labels
Value=123
```

**Step-by-Step Breakdown:**

1. `item_properties` creates a new LIST field named "PropertyList" at root level
2. `property_struct` adds a STRUCT element to that list (hence blank `Label=`)
3. `property_subtype` and `property_value` add fields inside the struct (hence required `Label=`)

This pattern is common when adding new property lists, dialog entries, journal categories, and similar list-based structures.

## Special Features

### Dynamic Field Paths (2DAMEMORY with !FieldPath)

Store and use field paths dynamically. This feature (added in TSLPatcher v1.2.7b9) allows you to add fields and then reference them later using memory tokens.

**Storing a Field Path:**

```ini
[example.dlg]
; First, add a field and store its path
AddField0=dynamic_reply
[dynamic_reply]
FieldType=Struct
Path=RepliesList
Label=
TypeId=5
AddField0=text_field
2DAMEMORY0=!FieldPath        ; Store the full path to the "Text" field

[text_field]
FieldType=ExoLocString
Path=                         ; Inherits "RepliesList\{index}\"
Label=Text
StrRef=-1
lang0=Dynamic reply text
```

**Using a Stored Field Path:**

After storing a path with `2DAMEMORY#=!FieldPath`, you can use that token as a field path to modify the field:

```ini
; Modify the field using the stored path
2DAMEMORY0(strref)=StrRef50   ; Sets the StrRef of the field stored in 2DAMEMORY0
2DAMEMORY0(lang0)=Updated text ; Sets the lang0 substring of that field
```

**Copying Field Paths Between Tokens:**

```ini
; Copy a field path from one token to another
2DAMEMORY1=2DAMEMORY0         ; Copy the path stored in 2DAMEMORY0 to 2DAMEMORY1
```

**Use Cases:**

- **Dynamic Dialog Branches**: Add new dialog entries/replies and cross-reference them using stored paths
- **Self-Referencing Structures**: Create fields that need to reference other dynamically-added fields
- **Conditional Field Updates**: Store multiple field paths and update them based on runtime conditions

**Important:** When using `2DAMEMORY#=!FieldPath` in an AddField section, the stored path includes the field's label. For nested fields, the path is the full absolute path from the GFF root.

### Using ListIndex for Type ID

Some GFF structures require the STRUCT's Type ID to match its position (index) in the list. This is common in:

- Journal category lists (`.jrl` files)
- Certain dialog structures
- Other list-based structures where Type ID corresponds to list position

**Syntax:**

Set `TypeId=ListIndex` (literal text, not a token) when adding a struct to a list:

```ini
[example.jrl]
AddField0=journal_category

[journal_category]
FieldType=Struct
Path=Categories
Label=                      ; Blank - adding struct to list
TypeId=ListIndex            ; Auto-sets Type ID to match list index
AddField0=category_name

[category_name]
FieldType=ExoLocString
Path=                       ; Inherits "Categories\{index}\"
Label=Name                  ; Required - field inside struct
StrRef=StrRef100
lang0=My Custom Quests
```

**How It Works:**

- When `TypeId=ListIndex` is specified, the patcher automatically determines the index where the struct is added
- The Type ID is set to that numeric index (0, 1, 2, etc.)
- For example, if the struct becomes the 5th element (index 4), the Type ID will be set to 4

**Note:** `TypeId=ListIndex` is different from `2DAMEMORY#=ListIndex`. The former sets the struct's Type ID, while the latter stores the index in a memory token for later use.

### ExclusiveColumn (in Nested 2DA Integration)

GFFList does not support 2DA-style ExclusiveColumn.

## Common Pitfalls and Troubleshooting

### Field and Path Issues

- **Case sensitivity**: Field names are case-sensitive. `Comments` ≠ `comments`. Use a GFF viewer to copy labels exactly.
- **List indices**: Lists start at 0. The first element is `\0\`, second is `\1\`, etc.
- **Blank labels**: `Label=` blank is **only** valid when `FieldType=Struct` and adding that struct **to a LIST**. All other field types require a label, including fields added **inside** structs that are themselves in lists.
- **Adding to list vs adding to struct**: Confusing these two operations is a common mistake:
  - Adding STRUCT to LIST: `Label=` blank, `Path=` points to list name
  - Adding field to STRUCT: `Label=` required, `Path=` can be empty (inherits)
- **Path inheritance confusion**: Remember that when adding a struct to a list, child fields with empty `Path=` inherit the resolved path including the list index. You don't need to (and shouldn't) manually specify the index.
- **Container fields**: Don't assign `Value=` to `Struct` or `List` fields—they are containers. Set values in their child fields instead.
- **List index resolution**: The index where a struct is added is automatically determined at runtime. You cannot manually set or predict the exact index ahead of time if other mods might add structs to the same list.

### Localized String Syntax

- **StrRef vs lang#**: Use `FieldName(strref)=...` for the StrRef value, and `FieldName(lang#)=...` for text substrings. Don't mix them on the same key.
- **Multiple substrings**: You can set multiple `lang#` entries for the same field (e.g., `lang0=English`, `lang2=French`).
- **Line breaks**: Use `<#LF#>` for linefeeds in `lang#` values, not literal newlines.

### Memory Tokens

- **Token initialization**: Tokens must be set before use. Using `2DAMEMORY5` before assignment results in an error.
- **Execution order**: Within GFFList, AddField sections run before field modifications. Store `!FieldPath` when creating fields, then use the token to modify them.
- **Token scope**: `StrRef#` tokens are created in TLKList and available to GFFList. `2DAMEMORY#` tokens are file-scoped unless explicitly copied.

### Path and Source Configuration

- **Source folder resolution**: `.` refers to the `tslpatchdata` folder (where `changes.ini` is located). Don't explicitly specify `tslpatchdata` in the path.
- **Path separators**: Use backslashes (`\`) in field paths: `Parent\Child\Field`. Forward slashes may not work consistently.
- **Empty paths**: For root-level fields, use `Path=` (empty) or omit it entirely. Don't use `Path=\` or `Path=.`.

### Field Type Issues

- **Type compatibility**: Ensure values match field types. Don't assign strings to integer fields or vice versa.
- **Missing fields**: Attempting to modify a non-existent field will log an error. Use AddField to create new fields first.
- **Binary type**: The `Binary` field type is HoloPatcher-only and not supported by classic TSLPatcher.

### Common Error Messages

- **"Cannot parse 'key=value'"**: Invalid syntax for memory token assignment or field path
- **"Field did not exist at path"**: Tried to modify a field that doesn't exist (use AddField instead)
- **"2DAMEMORY# was not defined before use"**: Token was referenced before being set
- **"Label must be set for FieldType"**: Non-Struct field requires a label, or Struct in LIST requires blank label

### Debugging Tips

- Enable verbose logging (`LogLevel=4`) to see detailed path resolution and token assignments
- Verify field paths using a GFF editor before writing patches
- Test AddField sections before adding modifications that depend on them
- Check token assignments match between 2DAList/TLKList and GFFList sections

## Execution Order and Dependencies

Understanding execution order is crucial when your edits depend on earlier tokens or dynamically created fields.

**Standard Execution Order:**

1. **TLKList**: Appends entries to dialog.tlk, creates `StrRef#` tokens
2. **InstallList**: Copies files to destination (ERF/RIM archives may be created here)
3. **2DAList**: Modifies 2DA files, creates `2DAMEMORY#` tokens
4. **GFFList**: Modifies GFF files (can use `StrRef#` and `2DAMEMORY#` tokens)
5. **CompileList**: Preprocesses NSS scripts (replaces `#StrRef#` and `#2DAMEMORY#` tokens), then compiles
6. **HACKList**: Applies binary patches to NCS files
7. **SSFList**: Modifies soundset files

**Within GFFList Section:**

Modifications within a single GFF file are processed in order:

1. **AddField sections** are processed first (fields are created)
2. **Memory assignments** (`2DAMEMORY#=!FieldPath`, `2DAMEMORY#=ListIndex`) are evaluated as fields are added
3. **Field modifications** are processed last (can reference stored paths via `2DAMEMORY#` tokens)

**Best Practices:**

- **Add before modify**: Use AddField to create structures, store their paths with `2DAMEMORY#=!FieldPath`, then modify them using those tokens
- **Token dependencies**: Ensure tokens are set before use. `2DAMEMORY#` tokens from 2DAList are available to GFFList
- **Archive handling**: If patching files into ERF/RIM archives, the archive must exist (created by InstallList) or be built automatically by the patcher

**Important Notes:**

- Script token preprocessing (in CompileList) runs **before** GFFList to avoid interfering with `!FieldPath` assignments
- If multiple GFF files reference the same tokens, they can share `StrRef#` and `2DAMEMORY#` values across files
- The `!OverrideType` setting controls behavior when a file exists in Override but you're patching into an archive

## Complete Examples

### Example 1: Simple Item Template Modification

```ini
[GFFList]
File0=my_item.uti

[my_item.uti]
!Destination=override

; Modify existing fields
LocalizedName=strref50000
Description=strref50001
BaseItem=28
; Add new property
AddField0=new_property

[new_property]
FieldType=Struct
Path=PropertyList
Label=
TypeId=7
AddField0=subtype_field
AddField1=value_field

[subtype_field]
FieldType=Word
Path=
Label=Subtype
Value=15

[value_field]
FieldType=Int
Path=
Label=Value
Value=500
```

### Example 2: Dialog File with New Branches

```ini
[GFFList]
File0=my_dialog.dlg

[my_dialog.dlg]
!Destination=override

; Add new entry
AddField0=new_entry

[new_entry]
FieldType=Struct
Path=EntryList
Label=
TypeId=0
2DAMEMORY0=ListIndex
AddField0=speaker
AddField1=text
AddField2=replies

[speaker]
FieldType=ResRef
Path=
Label=Speaker
Value=npc_speaker

[text]
FieldType=ExoLocString
Path=
Label=Text
StrRef=-1
lang0=Welcome to my mod!

[replies]
FieldType=List
Path=
Label=RepliesList
AddField0=reply1

[reply1]
FieldType=Struct
Path=
Label=
TypeId=0
AddField0=reply_text

[reply_text]
FieldType=ExoLocString
Path=
Label=Text
StrRef=-1
lang0=Thank you!
```

### Example 3: Creature Template with Dynamic Data

```ini
[GFFList]
File0=new_creature.utc

[new_creature.utc]
!Destination=override

; Use 2DA memory token for appearance (set elsewhere)
AddField0=appearance_value

[appearance_value]
FieldType=Word
Path=
Label=Appearance_Type
Value=2DAMEMORY5

; Add localized name using TLK token
AddField0=name_field

[name_field]
FieldType=ExoLocString
Path=
Label=LocalizedName
StrRef=StrRef0
lang0=Custom Creature
```

### Example 4: Journal Entry

```ini
[GFFList]
File0=global.jrl

[global.jrl]
!Destination=override

; Add new category with ListIndex
AddField0=new_category

[new_category]
FieldType=Struct
Path=Categories
Label=
TypeId=ListIndex
AddField0=category_strref

[category_strref]
FieldType=ExoLocString
Path=
Label=Name
StrRef=StrRef100
lang0=My Custom Quests
```

### Example 5: Complex Nested Structure

```ini
[GFFList]
File0=complex_item.uti

[complex_item.uti]
!Destination=override

; Add properties list with multiple entries
AddField0=properties_list

[properties_list]
FieldType=List
Path=
Label=PropertyList
AddField0=property1
AddField1=property2
AddField2=property3

[property1]
FieldType=Struct
Path=
Label=
TypeId=7
AddField0=prop_subtype
AddField1=prop_value
AddField2=prop_parameter1
AddField3=prop_parameter2
AddField4=prop_cost

[prop_subtype]
FieldType=Word
Path=
Label=Subtype
Value=12

[prop_value]
FieldType=Int
Path=
Label=Value
Value=10

[prop_parameter1]
FieldType=DWORD
Path=
Label=Parameter1
Value=0

[prop_parameter2]
FieldType=DWORD
Path=
Label=Parameter2
Value=0

[prop_cost]
FieldType=DWORD
Path=
Label=Cost
Value=0

[property2]
FieldType=Struct
Path=
Label=
TypeId=7
AddField0=prop_subtype2
AddField1=prop_value2

[prop_subtype2]
FieldType=Word
Path=
Label=Subtype
Value=25

[prop_value2]
FieldType=Int
Path=
Label=Value
Value=5

[property3]
FieldType=Struct
Path=
Label=
TypeId=7
AddField0=prop_subtype3
AddField1=prop_value3

[prop_subtype3]
FieldType=Word
Path=
Label=Subtype
Value=30

[prop_value3]
FieldType=Int
Path=
Label=Value
Value=15
```

## Common Patterns

### Pattern 1: Store and Reference List Index

```ini
[GFFList]
File0=item.uti

[item.uti]
; Add struct to list, store index
AddField0=store_index_property

[store_index_property]
FieldType=Struct
Path=PropertyList
Label=
TypeId=7
2DAMEMORY0=ListIndex

; Later, use that index elsewhere
Index=2DAMEMORY0
```

### Pattern 2: Dynamic Localized Strings

```ini
[GFFList]
File0=dialog.dlg

[dialog.dlg]
; Add entry with stored strref
AddField0=entry_with_strref

[entry_with_strref]
FieldType=Struct
Path=EntryList
Label=
TypeId=0
AddField0=localized_text

[localized_text]
FieldType=ExoLocString
Path=
Label=Text
StrRef=StrRef50
lang0=English text
lang2=French text
lang4=German text
```

### Pattern 3: Cross-Reference Tokens

```ini
[GFFList]
File0=templates.uti

[templates.uti]
; Store value from 2DA
AddField0=from_2da

[from_2da]
FieldType=Word
Path=
Label=From2DA
Value=2DAMEMORY10

; Copy 2DA token
2DAMEMORY20=2DAMEMORY10

; Use copied token
AddField0=use_copied

[use_copied]
FieldType=Int
Path=
Label=Value
Value=2DAMEMORY20
```

## Best Practices

1. Unique labels across each GFF hierarchy level
2. Prefer memory tokens for dynamic values
3. List indices start at 0
4. Backslash path separators for nested paths
5. Case-sensitive field names
6. Verify file structure with a GFF editor
7. Sort complex nested structures for clarity
8. Use meaningful identifiers for AddField sections

## Error Handling

Common mistakes:

- Modifying non-existent fields
- Invalid FieldType
- Missing required keys
- Circular memory references
- Invalid 2DAMEMORY/StrRef syntax

PyKotor validates configuration and logs errors during INI loading and patching.

## Compatibility

Tested on:

- HoloPatcher
- TSLPatcher v1.2.10b
- PyKotor’s TSLPatcher implementation
- KotOR1/KotOR2 GFF files

Field type compatibility:

- All standard types supported
- Nested structures supported
- Memory tokens supported
- Dynamic paths supported

## Additional Resources

### Documentation

- [TSLPatcher Official Readme](TSLPatcher's-Official-Readme.md) - Original TSLPatcher documentation
- [HoloPatcher Documentation](HoloPatcher.md) - HoloPatcher-specific features and improvements

### Source Code References

- `pykotor/resource/formats/gff/gff_data.py` - GFF data structure definitions
- `pykotor/resource/formats/gff/io_gff.py` - GFF file I/O implementation
- `pykotor/tslpatcher/reader.py` - INI configuration parsing (see `load_gff_list`, `add_field_gff`, `modify_field_gff`)
- `pykotor/tslpatcher/mods/gff.py` - GFF modification logic (see `ModificationsGFF`, `AddFieldGFF`, `ModifyFieldGFF`)
- `pykotor/tslpatcher/patcher.py` - Main patcher execution flow

### GFF File Types

Common GFF-based file types you can modify:

- **.ARE** - Area files
- **.DLG** - Dialogs
- **.GIT** - Module instance files
- **.IFO** - Module info
- **.JRL** - Journal entries
- **.PTH** - AI Pathing files
- **.UTC** - Creature templates  
- **.UTD** - Doors
- **.UTE** - Encounters
- **.UTI** - Item templates
- **.UTM** - Merchants
- **.UTP** - Placeable templates
- **.UTS** - Sounds
- **.UTT** - Trigger templates
- **.UTW** - Waypoint templates

## Version History

### TSLPatcher Versions

- **[1.2.10b](TSLPatcher's-Official-Readme.md#change-log-for-version-1210b1-rel)** (2007-09-19): Fixed ExoLocString substring linefeed handling (use `<#LF#>` for newlines)
- **[1.2.9b](TSLPatcher's-Official-Readme.md#change-log-for-version-129b-rel)** (2007-08-13): Changed behavior when adding duplicate fields—now modifies existing field instead of skipping
- **[1.2.8b10](TSLPatcher's-Official-Readme.md#change-log-for-version-128b10-rel)** (2006-12-10): Bug fixes for required file checks
- **[1.2.8b6](TSLPatcher's-Official-Readme.md#change-log-for-version-128b6-rel)** (2006-10-03): Added `!OverrideType` support for ERF/RIM destinations
- **[1.2.7b9](TSLPatcher's-Official-Readme.md#change-log-for-version-127b9-rel)** (2006-07-23): **Dynamic field paths** - Added `!FieldPath` support for storing and using field paths via `2DAMEMORY#` tokens
- **[1.2.7b4](TSLPatcher's-Official-Readme.md#change-log-for-version-127b4-rel)** (2006-05-11): Multiple setups support improvements
- **[1.2.6b3](TSLPatcher's-Official-Readme.md#change-log-for-version-126b3-rel)** (2006-03-09): SSF soundset file modification support added
- **[1.2a](TSLPatcher's-Official-Readme.md#change-log-for-version-12a-rel)** (2006-01-10): **AddField support** - Initial support for adding new fields to GFF files

### HoloPatcher Extensions

- **Binary field type**: Support for adding/modifying Binary fields (not in classic TSLPatcher)

---

**For issues or questions**, check PyKotor’s GitHub Issues or the KotOR modding forums.
