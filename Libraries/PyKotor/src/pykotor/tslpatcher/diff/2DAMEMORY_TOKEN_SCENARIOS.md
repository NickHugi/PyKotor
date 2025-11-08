# 2DAMEMORY Token Usage Scenarios - Comprehensive Analysis

This document catalogs ALL scenarios where 2DAMEMORY tokens are created, stored, and used in TSLPatcher, based on the official syntax documentation.

## Overview

2DAMEMORY tokens are NOT exclusively for row values. They can store:

- Row indices (`RowIndex`)
- Row labels (`RowLabel`)
- Column cell values (`ColumnName`)
- Field paths (`!FieldPath`)
- List indices (`ListIndex`)
- StrRef values (`StrRef#`)
- Token copies (`2DAMEMORY#`)

## Token Creation Scenarios

### 1. 2DAList - Token Storage Operations

**Location:** `[2DAList]` section, within ChangeRow/AddRow/CopyRow/AddColumn modifiers

#### 1.1 Store Row Index

```ini
[modify_appearance]
RowIndex=5
2DAMEMORY10=RowIndex
```

- **When:** During ChangeRow2DA/AddRow2DA/CopyRow2DA
- **Stores:** Row index as string (e.g., "5")
- **Internal:** `store_2da[token_id] = RowValueRowIndex()`
- **Current Implementation:** ✅ Handled in `_prepare_twoda_tokens()` - token stored in modifier.store_2da

#### 1.2 Store Row Label

```ini
[modify_appearance]
RowLabel=1
2DAMEMORY11=RowLabel
```

- **When:** During ChangeRow2DA/AddRow2DA/CopyRow2DA
- **Stores:** Row label value (first column value) as string
- **Internal:** `store_2da[token_id] = RowValueRowLabel()`
- **Current Implementation:** ⚠️ Needs verification - token stored but may not trigger linking patches

#### 1.3 Store Column Cell Value

```ini
[modify_appearance]
RowIndex=5
2DAMEMORY12=modeltype
```

- **When:** During ChangeRow2DA/AddRow2DA/CopyRow2DA
- **Stores:** Cell value from specified column as string
- **Internal:** `store_2da[token_id] = RowValueRowCell("modeltype")`
- **Current Implementation:** ⚠️ Needs verification - token stored but not used for linking

#### 1.4 Store StrRef Value

```ini
[modify_appearance]
RowIndex=5
name=12345
StrRef20=name
```

- **When:** During ChangeRow2DA/AddRow2DA/CopyRow2DA
- **Stores:** StrRef value in TLK memory, not 2DA memory
- **Note:** This is `StrRef#`, not `2DAMEMORY#` - separate system
- **Current Implementation:** ✅ Handled separately via StrRef system

#### 1.5 Copy Token Value

```ini
[modify_appearance]
RowIndex=5
2DAMEMORY13=2DAMEMORY10
```

- **When:** During ChangeRow2DA/AddRow2DA/CopyRow2DA
- **Stores:** Copies value from another 2DAMEMORY token
- **Internal:** Evaluates source token and stores result
- **Current Implementation:** ⚠️ Needs verification - depends on source token being set first

#### 1.6 Store from New Column (AddColumn)

```ini
[add_column]
ColumnLabel=NewColumn
DefaultValue=0
I5=Value
2DAMEMORY30=I5
```

- **When:** During AddColumn2DA
- **Stores:** Cell value from newly created column at specified row
- **Syntax:** `2DAMEMORY#=I#` (row index) or `2DAMEMORY#=Llabel` (row label)
- **Current Implementation:** ⚠️ Needs verification - AddColumn modifications may not be fully handled

### 2. GFFList - Token Storage Operations

**Location:** `[GFFList]` section, within file sections or AddField sections

#### 2.1 Store Field Path (!FieldPath)

```ini
[example.dlg]
AddField0=new_reply
[new_reply]
FieldType=Struct
Path=RepliesList
Label=
TypeId=5
AddField0=text_field
2DAMEMORY0=!FieldPath

[text_field]
FieldType=ExoLocString
Path=
Label=Text
```

- **When:** During AddFieldGFF or at file level
- **Stores:** Full field path as `PureWindowsPath` (e.g., `PureWindowsPath("RepliesList\\3\\Text")`)
- **Internal:** `Memory2DAModifierGFF` creates `memory.memory_2da[token_id] = path`
- **Current Implementation:** ✅ Handled via `Memory2DAModifierGFF` in GFF modifications

#### 2.2 Store List Index

```ini
[new_reply]
FieldType=Struct
Path=RepliesList
Label=
TypeId=5
2DAMEMORY0=ListIndex
```

- **When:** When adding STRUCT to LIST field
- **Stores:** Index where struct was added (e.g., "3")
- **Internal:** `Memory2DAModifierGFF` with special `ListIndex` handling
- **Current Implementation:** ⚠️ Needs verification - ListIndex handling in AddFieldGFF

#### 2.3 Copy Token Value

```ini
[example.uti]
2DAMEMORY1=2DAMEMORY0
```

- **When:** At file level or in AddField sections
- **Stores:** Copies value from another 2DAMEMORY token
- **Internal:** `Memory2DAModifierGFF` reads source token and copies
- **Current Implementation:** ✅ Handled via `Memory2DAModifierGFF`

## Token Usage Scenarios

### 3. 2DAList - Token as Cell Values

**Location:** `[2DAList]` section, as cell values in ChangeRow/AddRow/CopyRow

#### 3.1 Use Token as Cell Value

```ini
[add_appearance]
label=NEW_APPEARANCE
modeltype=2DAMEMORY12
appearance=2DAMEMORY10
```

- **When:** Setting cell values in 2DA modifications
- **Syntax:** `ColumnName=2DAMEMORY#`
- **Internal:** `RowValue2DAMemory(token_id)` - looks up token from memory
- **Current Implementation:** ✅ Handled - tokens are looked up from `memory.memory_2da` during patch application

### 4. GFFList - Token as Field Values

**Location:** `[GFFList]` section, as field values in ModifyField or AddField

#### 4.1 Use Token as Field Value

```ini
[example.uti]
ModelVariation=2DAMEMORY5
LocalizedName=StrRef3
```

- **When:** Setting field values in GFF modifications
- **Syntax:** `FieldName=2DAMEMORY#`
- **Internal:** `FieldValue2DAMemory(token_id)` - looks up token from memory
- **Current Implementation:** ✅ Handled - tokens are looked up from `memory.memory_2da` during patch application

#### 4.2 Use Token as TypeId

```ini
[new_struct]
FieldType=Struct
Path=
Label=MyStruct
TypeId=2DAMEMORY10
```

- **When:** Setting TypeId in AddFieldGFF
- **Syntax:** `TypeId=2DAMEMORY#` (or `TypeId=ListIndex`)
- **Internal:** Special handling in AddFieldGFF for TypeId parsing
- **Current Implementation:** ⚠️ Needs verification - TypeId parsing with tokens

#### 4.3 Use Token as Field Path

```ini
2DAMEMORY0(strref)=StrRef50
2DAMEMORY0(lang0)=Updated text
```

- **When:** Using stored !FieldPath to modify fields dynamically
- **Syntax:** `2DAMEMORY#(strref)=...` or `2DAMEMORY#(lang#)=...`
- **Internal:** Token contains `PureWindowsPath`, used to navigate to field
- **Current Implementation:** ✅ Handled - `ModifyFieldGFF` and `AddFieldGFF` check for `PureWindowsPath` in value

## Deferred Application Pattern

### Current Implementation Focus

The deferred application pattern (via `Pending2DARowReference`) is specifically for:

**Scenario:** When we discover a GFF field containing an integer that references a 2DA row index, we need to create a linking patch. However, we don't know if that GFF file will be diffed or not.

**Solution:** Store the reference temporarily, and only create the patch when the GFF file is actually diffed.

**Limitation:** This only handles ONE specific scenario - GFF fields containing 2DA row indices.

### Other Scenarios That DON'T Need Deferred Application

1. **2DA Modifications Store Tokens:**
   - Tokens are stored directly in `modifier.store_2da`
   - Available immediately to all subsequent sections
   - ✅ Already handled correctly

2. **GFF AddField Stores !FieldPath:**
   - Tokens are stored via `Memory2DAModifierGFF`
   - Available immediately to later modifiers in same file
   - ✅ Already handled correctly

3. **GFF AddField Stores ListIndex:**
   - Tokens are stored when struct is added to list
   - Available immediately to later modifiers in same file
   - ⚠️ Needs verification - ensure ListIndex is properly captured

4. **Tokens Used as Values:**
   - `FieldValue2DAMemory` and `RowValue2DAMemory` look up tokens at patch time
   - No deferred application needed - tokens must exist before use
   - ✅ Already handled correctly

## Verification Checklist

### ✅ Fully Handled

- [x] 2DA modifications create tokens via `store_2da` (RowIndex, RowLabel, ColumnName)
- [x] GFF modifications use tokens as field values (`FieldValue2DAMemory`)
- [x] 2DA modifications use tokens as cell values (`RowValue2DAMemory`)
- [x] GFF !FieldPath storage (`Memory2DAModifierGFF`)
- [x] GFF token copy operations (`Memory2DAModifierGFF`)
- [x] Deferred application for 2DA row references in GFF fields

### ⚠️ Needs Verification

- [ ] AddColumn memory storage (`2DAMEMORY#=I#` or `2DAMEMORY#=Llabel`)
- [ ] ListIndex storage in AddFieldGFF (`2DAMEMORY#=ListIndex`)
- [ ] TypeId parsing with tokens (`TypeId=2DAMEMORY#`)
- [ ] Token storage in CopyRow2DA modifications
- [ ] Token copy operations in 2DA modifications (`2DAMEMORY#=2DAMEMORY#`)

### ❌ Not Applicable to Deferred Pattern

- Token usage as values (no deferred application needed)
- Token creation in 2DA/GFF modifications (immediate storage)
- StrRef tokens (separate system)

## Implementation Notes

### Current Architecture

1. **Immediate Storage:** Tokens created in 2DA/GFF modifications are stored immediately in `modifier.store_2da` or via `Memory2DAModifierGFF`. These are written to INI immediately.

2. **Deferred Application:** Only GFF fields containing 2DA row indices use deferred application:
   - `Pending2DARowReference` stores references temporarily
   - Applied when GFF file is diffed via `_apply_pending_2da_row_references()`

3. **Token Lookup:** All token usage (as values) happens at patch application time, not during INI generation.

### Key Insight

**2DAMEMORY tokens are NOT exclusively for row references.** The deferred application pattern only applies to ONE specific scenario: discovering GFF fields that reference 2DA row indices before we know if the GFF file will be diffed.

All other token scenarios (storage in 2DA/GFF modifications, usage as values) are handled immediately during INI generation, not deferred.

## Recommendations

1. **Verify AddColumn Handling:** Ensure `AddColumn2DA` modifications properly handle `2DAMEMORY#=I#` and `2DAMEMORY#=Llabel` syntax when writing INI.

2. **Verify ListIndex Handling:** Ensure `AddFieldGFF` properly captures `ListIndex` when adding structs to lists and stores it via `2DAMEMORY#=ListIndex`.

3. **Verify TypeId Parsing:** Ensure `AddFieldGFF` properly parses `TypeId=2DAMEMORY#` syntax.

4. **Document Token Flow:** The deferred application pattern is a specific optimization for one scenario. All other token operations are immediate and don't need deferred handling.
