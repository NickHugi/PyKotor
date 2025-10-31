# Comprehensive 2DAMEMORY Analysis

## Overview

**2DAMEMORY** is a memory token system in TSLPatcher that allows storing and referencing 2DA (Two-Dimensional Array) values across different patch sections. It provides a mechanism for:

- Storing 2DA row data for later use
- Referencing stored values in subsequent patches
- Cross-patch communication (2DA → GFF, 2DA → SSF, 2DA → NCS, etc.)
- Handling dynamic row indices that change during installation

---

## Core Architecture

### Memory Storage

```python
# From memory.py
class PatcherMemory:
    memory_2da: dict[int, str | PureWindowsPath] = {}  # Token ID → Value
    memory_str: dict[int, int] = {}  # TLK token storage (different system)
```

**Key Point**: `memory_2da` can store:

- `str`: String values (most common)
- `PureWindowsPath`: GFF field paths for !FieldPath functionality

---

## Usage Scenarios by Patch Type

### 1. [2DAList] - Two-Dimensional Array Patches

#### 1.1 Storing Values FROM 2DA Rows (`2DAMEMORY#=...`)

**Syntax**: `2DAMEMORY{token_id}={source}`

Where `{source}` can be:

- **RowIndex** - Creates `RowValueRowIndex()` → Stores the numeric row index (0-based)
- **RowLabel** - Creates `RowValueRowLabel()` → Stores the row label string
- **ColumnName** - Creates `RowValueRowCell(column)` → Stores the value from that column

**Example 1: Storing RowIndex**

```ini
[change_row_0]
RowIndex=0
2DAMEMORY0=RowIndex
```

Result: `memory.memory_2da[0] = "0"` (the row index as string)

- Creates: `RowValueRowIndex()` object in `store_2da[0]`
- At runtime: Calls `row.index()` → Returns `"0"` as string

**Example 2: Storing RowLabel**

```ini
[add_row_0]
label=MyNewRow
2DAMEMORY1=RowLabel
```

Result: `memory.memory_2da[1] = "MyNewRow"`

- Creates: `RowValueRowLabel()` object in `store_2da[1]`
- At runtime: Calls `row.label()` → Returns `"MyNewRow"` as string

**Example 3: Storing Column Value**

```ini
[change_row_0]
RowIndex=5
label=SomeLabel
2DAMEMORY2=label
```

Result: `memory.memory_2da[2] = "SomeLabel"` (value from the `label` column)

- Creates: `RowValueRowCell("label")` object in `store_2da[2]`
- At runtime: Calls `row.get_string("label")` → Returns the cell value

**Supported in**:

- `ChangeRow2DA` (via `store_2da` dict)
- `AddRow2DA` (via `store_2da` dict)
- `CopyRow2DA` (via `store_2da` dict)

**Code Reference**:

```303:307:Libraries/PyKotor/src/pykotor/tslpatcher/mods/twoda.py
for token_id, value in self.store_2da.items():
    memory.memory_2da[token_id] = value.value(memory, twoda, source_row)
```

**Parsing Logic** (reader.py):

```1381:1386:Libraries/PyKotor/src/pykotor/tslpatcher/reader.py
elif lower_value == "rowindex":
    row_value = RowValueRowIndex()
elif lower_value == "rowlabel":
    row_value = RowValueRowLabel()
elif is_store_2da or is_store_tlk:
    row_value = RowValueRowCell(value)  # ColumnName creates RowValueRowCell
```

#### 1.2 Using Stored Values IN 2DA Cells (`ColumnName=2DAMEMORY#`)

**Syntax**: `{ColumnName}=2DAMEMORY{token_id}`

**Example**:

```ini
[change_row_0]
RowIndex=0
appearance=2DAMEMORY5
dialog=2DAMEMORY6
```

**Supported in**:

- `ChangeRow2DA.cells` - Cell modifications
- `AddRow2DA.cells` - New row cell values
- `CopyRow2DA.cells` - Copied row cell values
- `AddColumn2DA.index_insert` - Index-based inserts (I#=2DAMEMORY#)
- `AddColumn2DA.label_insert` - Label-based inserts (Llabel=2DAMEMORY#)

**Code Reference**:

```1373:1375:Libraries/PyKotor/src/pykotor/tslpatcher/reader.py
if lower_value.startswith("2damemory"):
    token_id = int(value[len("2damemory") :])
    row_value = RowValue2DAMemory(token_id)
```

#### 1.3 Using 2DAMEMORY in Target Specifications

**Syntax**: `RowIndex=2DAMEMORY#` or `RowLabel=2DAMEMORY#`

**Example**:

```ini
[change_row_0]
RowIndex=2DAMEMORY10
```

This allows dynamically determining which row to modify based on a previously stored value.

**Supported in**:

- `Target` for `ChangeRow2DA`, `CopyRow2DA`
- `TargetType.ROW_INDEX` - Can use `RowValue2DAMemory`
- `TargetType.ROW_LABEL` - Can use `RowValue2DAMemory`

**Code Reference**:

```1319:1322:Libraries/PyKotor/src/pykotor/tslpatcher/reader.py
elif lower_raw_value.startswith("2damemory") and len(raw_value) > len("2damemory") and raw_value[9:].isdigit():
    value = RowValue2DAMemory(int(raw_value[9:]))
else:
    value = int(raw_value) if is_int else raw_value
```

#### 1.4 Storing Values FROM AddColumn Operations

**Syntax**: `2DAMEMORY#=I{index}` or `2DAMEMORY#=L{label}`

**Example**:

```ini
[add_column_0]
ColumnLabel=NewColumn
DefaultValue=****
I0=abc
I1=def
2DAMEMORY2=I1    # Store value from row index 1 in the new column
2DAMEMORY3=Llabel0    # Store value from row with label "label0"
```

**How it works**:

- `I{index}` format: Stores the cell value at row `{index}` in the newly added column
- `L{label}` format: Stores the cell value at the row with label `{label}` in the newly added column

**Code Reference**:

```564:577:Libraries/PyKotor/src/pykotor/tslpatcher/mods/twoda.py
for token_id, value in self.store_2da.items():
    if value.startswith("I"):
        cell: str = twoda.get_row(int(value[1:])).get_string(self.header)
        memory.memory_2da[token_id] = cell
    elif value.startswith("L"):
        row = twoda.find_row(value[1:])
        if row is None:
            msg = f"Could not find row {value[1:]} in {self.header}"
            raise WarningError(msg)
        cell = row.get_string(self.header)
        memory.memory_2da[token_id] = cell
```

---

### 2. [GFFList] - GFF (Generic File Format) Patches

#### 2.1 Using 2DAMEMORY Values as GFF Field Values

**Syntax**: `{Path}={Value}` where `{Value}` can be `2DAMEMORY{token_id}`

**Example 1: Direct Field Modification**

```ini
[test.gff]
EntryList\0\Label=2DAMEMORY5
```

**Example 2: In LocalizedString StrRef**

```ini
[add_loc]
FieldType=ExoLocString
Path=
Label=Field1
StrRef=2DAMEMORY5
```

**How it works**:

- `FieldValue2DAMemory` retrieves value from `memory.memory_2da[token_id]`
- The value is validated and converted to the appropriate GFF field type
- **Note**: Cannot be `PureWindowsPath` (that's for !FieldPath only)

**Code Reference**:

```174:183:Libraries/PyKotor/src/pykotor/tslpatcher/mods/gff.py
class FieldValue2DAMemory(FieldValue):
    def value(self, memory: PatcherMemory, field_type: GFFFieldType):
        memory_val: str | PureWindowsPath | None = memory.memory_2da.get(self.token_id, None)
        if memory_val is None:
            msg = f"2DAMEMORY{self.token_id} was not defined before use"
            raise KeyError(msg)
        return self.validate(memory_val, field_type)
```

#### 2.2 !FieldPath Support (`2DAMEMORY#=!FieldPath`)

**Syntax**: `2DAMEMORY{token_id}=!FieldPath`

**Purpose**: Store a GFF field path in 2DAMEMORY for later use.

**Example**:

```ini
[test.gff]
AddField0=add_field

[add_field]
FieldType=Struct
Path=
Label=NewStruct
TypeId=321
2DAMEMORY5=!FieldPath
```

**How it works**:

- Stores `PureWindowsPath` in `memory.memory_2da[token_id]`
- Later patches can navigate to that field using the stored path
- Used in `Memory2DAModifierGFF` class

**Code Reference**:

```465:469:Libraries/PyKotor/src/pykotor/tslpatcher/mods/gff.py
if self.src_token_id is None:  # assign the path and leave.
    display_src_name = f"!FieldPath({self.path})"
    logger.add_verbose(f"Assign {display_dest_name}={display_src_name}")
    memory.memory_2da[self.dest_token_id] = self.path
    return
```

#### 2.3 2DAMEMORY-to-2DAMEMORY Assignment (`2DAMEMORY#=2DAMEMORY#`)

**Syntax**: `2DAMEMORY{dest_token_id}=2DAMEMORY{src_token_id}`

**Purpose**: Copy a value from one 2DAMEMORY token to another, or copy a !FieldPath.

**Example**:

```ini
[test.gff]
2DAMEMORY5=!FieldPath
2DAMEMORY6=2DAMEMORY5    # Copy the field path from token 5 to token 6
```

**How it works**:

- If source token contains `PureWindowsPath`: Navigates to that field and copies its value
- If source token contains `str`: Copies the string value
- Used for complex GFF field manipulation

**Code Reference**:

```471:505:Libraries/PyKotor/src/pykotor/tslpatcher/mods/gff.py
display_src_name = f"2DAMEMORY{self.src_token_id}"
logger.add_verbose(f"GFFList ptr !fieldpath: Assign {display_dest_name}={display_src_name} initiated. iniPath: {self.path}, section: [{self.identifier}]")

ptr_to_dest: PureWindowsPath | Any = memory.memory_2da.get(self.dest_token_id, None) if self.dest_token_id is not None else self.path
if isinstance(ptr_to_dest, PureWindowsPath):
    dest_field = self._navigate_to_field(root_container, ptr_to_dest)
    # ... field manipulation logic
```

#### 2.4 Storing List Index (`2DAMEMORY#=listindex`)

**Syntax**: `2DAMEMORY{token_id}=listindex`

**Purpose**: In `AddStructToListGFF`, store the index of the newly added struct.

**Example**:

```ini
[add_struct_to_list]
FieldType=Struct
Path=EntryList
TypeId=100
2DAMEMORY5=listindex
```

**How it works**:

- After adding a struct to a list, stores the new struct's index (as string)
- Index = `len(list) - 1` (0-based)

**Code Reference**:

```340:343:Libraries/PyKotor/src/pykotor/tslpatcher/mods/gff.py
if self.index_to_token is not None:
    length = str(len(list_container) - 1)
    logger.add_verbose(f"Set 2DAMEMORY{self.index_to_token}={length}")
    memory.memory_2da[self.index_to_token] = length
```

#### 2.5 Using !FieldPath Values (2DAMEMORY Contains Path)

**Behavior**: When `FieldValue2DAMemory.value()` returns a `PureWindowsPath`, GFF patches navigate to that field and use its value.

**Code Reference**:

```410:423:Libraries/PyKotor/src/pykotor/tslpatcher/mods/gff.py
# if 2DAMEMORY holds a path from !FieldPath, navigate to that field and use its value.
if isinstance(value, PureWindowsPath):
    stored_fieldpath: PureWindowsPath = value
    if isinstance(self.value, FieldValue2DAMemory):
        logger.add_verbose(f"Looking up field pointer of stored !FieldPath ({stored_fieldpath}) in 2DAMEMORY{self.value.token_id}")
    # ... navigation and value extraction
    value = from_container.value(value.name)
```

---

### 3. [SSFList] - Sound Set File Patches

**Syntax**: `{SoundName}=2DAMEMORY{token_id}`

**Purpose**: Set SSF sound entry to a stringref value stored in 2DAMEMORY.

**Example**:

```ini
[test.ssf]
Battlecry 1=2DAMEMORY5
Battlecry 2=2DAMEMORY6
```

**How it works**:

- `TokenUsage2DA` retrieves value from `memory.memory_2da[token_id]`
- Value is converted to `int` for SSF sound assignment
- **Important**: Value must be numeric (cannot be `PureWindowsPath`)

**Code Reference**:

```34:43:Libraries/PyKotor/src/pykotor/tslpatcher/memory.py
class TokenUsage2DA(TokenUsage):
    def value(self, memory: PatcherMemory) -> str | PureWindowsPath:
        memory_val: str | PureWindowsPath | None = memory.memory_2da.get(self.token_id, None)
        if memory_val is None:
            msg = f"2DAMEMORY{self.token_id} was not defined before use"
            raise KeyError(msg)
        return memory_val
```

Used in:

```22:23:Libraries/PyKotor/src/pykotor/tslpatcher/mods/ssf.py
def apply(self, ssf: SSF, memory: PatcherMemory):
    ssf.set_data(self.sound, int(self.stringref.value(memory)))
```

---

### 4. [HACKList] - NCS (Compiled Script) Binary Patches

**Syntax**: `Hack{offset}=2DAMEMORY{token_id}` or `Hack{offset}=2DAMEMORY{token_id}:u16` / `:u32`

**Purpose**: Replace bytecode instructions with 2DAMEMORY values.

**Example**:

```ini
[script.ncs]
Hack00000010=2DAMEMORY5:u16
Hack00000020=2DAMEMORY6:u32
```

**Supported Types**:

- `MEMORY_2DA` - 16-bit unsigned (default)
- `MEMORY_2DA32` - 32-bit signed (CONSTI instruction)

**Constraints**:

- Value must be numeric (string that can be converted to int)
- **Cannot** be `PureWindowsPath` (raises TypeError)

**Code Reference**:

```152:162:Libraries/PyKotor/src/pykotor/tslpatcher/mods/ncs.py
def _write_2damemory(self, writer: BinaryWriter, memory: PatcherMemory, logger: PatchLogger, sourcefile: str):
    memory_val: str | PureWindowsPath | None = memory.memory_2da.get(self.token_id_or_value, None)
    if memory_val is None:
        msg = f"2DAMEMORY{self.token_id_or_value} was not defined before use"
        raise KeyError(msg)
    if isinstance(memory_val, PureWindowsPath):
        msg = f"Memory value cannot be !FieldPath in [HACKList] patches, got '{memory_val!r}'"
        raise TypeError(msg)
    value = int(memory_val)
    writer.write_uint16(value, big=True)
```

---

### 5. [CompileList] / NSS Script Processing

**Purpose**: `#2DAMEMORY#` tokens in NSS source files are replaced with stored values before compilation.

**Example NSS file**:

```nss
void main()
{
    int appearance = #2DAMEMORY5#;
    int dialogStrRef = #2DAMEMORY6#;
}
```

**How it works**:

1. NSS files are preprocessed to replace `#2DAMEMORY#` tokens
2. Values are looked up from `memory.memory_2da`
3. Token strings replaced with actual values
4. Then compiled to NCS

**Processing Order**:

- `[2DAList]` runs first → populates `memory.memory_2da`
- `[CompileList]` runs later → uses stored values

---

## Storage Value Types

### String Values (Most Common)

- Stored when: `2DAMEMORY#=RowIndex`, `2DAMEMORY#=RowLabel`, `2DAMEMORY#=ColumnName`
- Used for: Most 2DA operations, SSF, NCS, GFF field values
- Type: `str`

### PureWindowsPath Values (!FieldPath)

- Stored when: `2DAMEMORY#=!FieldPath` in GFF patches
- Used for: GFF field navigation and manipulation
- Type: `PureWindowsPath`
- **Special**: Cannot be used in 2DA patches, SSF patches, or NCS patches

---

## Complete Syntax Reference

### 1. Storing FROM 2DA Operations

| Syntax | Context | Stores |
|--------|---------|--------|
| `2DAMEMORY#=RowIndex` | ChangeRow/AddRow/CopyRow | Row index as string |
| `2DAMEMORY#=RowLabel` | ChangeRow/AddRow/CopyRow | Row label as string |
| `2DAMEMORY#={ColumnName}` | ChangeRow/AddRow/CopyRow | Value from column |
| `2DAMEMORY#=I{index}` | AddColumn | Value from row at index in new column |
| `2DAMEMORY#=L{label}` | AddColumn | Value from row with label in new column |
| `2DAMEMORY#=listindex` | AddStructToListGFF | Index of newly added struct |
| `2DAMEMORY#=!FieldPath` | GFF AddField/ModifyField | GFF field path |
| `2DAMEMORY#=2DAMEMORY#` | GFF Memory2DAModifierGFF | Copy value/token assignment |

### 2. Using IN 2DA Operations

| Syntax | Context | Purpose |
|--------|---------|---------|
| `{ColumnName}=2DAMEMORY#` | ChangeRow/AddRow/CopyRow cells | Set cell value from memory |
| `RowIndex=2DAMEMORY#` | ChangeRow/CopyRow target | Dynamic row targeting |
| `RowLabel=2DAMEMORY#` | ChangeRow/CopyRow target | Dynamic row targeting |
| `I{index}=2DAMEMORY#` | AddColumn index_insert | Set cell at index from memory |
| `L{label}=2DAMEMORY#` | AddColumn label_insert | Set cell at label from memory |

### 3. Using IN GFF Operations

| Syntax | Context | Purpose |
|--------|---------|---------|
| `{Path}=2DAMEMORY#` | ModifyFieldGFF | Set field value from memory |
| `StrRef=2DAMEMORY#` | LocalizedString fields | Set stringref from memory |
| `Value=2DAMEMORY#` | AddFieldGFF | Set field value from memory |

### 4. Using IN SSF Operations

| Syntax | Context | Purpose |
|--------|---------|---------|
| `{SoundName}=2DAMEMORY#` | ModifySSF | Set sound stringref from memory |

### 5. Using IN NCS Operations

| Syntax | Context | Purpose |
|--------|---------|---------|
| `Hack{offset}=2DAMEMORY#` | ModifyNCS | Write 16-bit value |
| `Hack{offset}=2DAMEMORY#:u16` | ModifyNCS | Write 16-bit unsigned |
| `Hack{offset}=2DAMEMORY#:u32` | ModifyNCS | Write 32-bit signed |

### 6. Using IN NSS Scripts

| Syntax | Context | Purpose |
|--------|---------|---------|
| `#2DAMEMORY#{token_id}#` | NSS source code | Preprocessor token replacement |

---

## Processing Order and Dependencies

**Critical**: Patches execute in this order:

1. `[TLKList]` - Creates StrRef tokens
2. `[InstallList]` - File installations
3. `[2DAList]` - Creates 2DAMEMORY tokens ← **Important!**
4. `[GFFList]` - Can use 2DAMEMORY tokens
5. `[CompileList]` - Preprocesses NSS with #2DAMEMORY# tokens
6. `[HACKList]` - Can use 2DAMEMORY tokens
7. `[SSFList]` - Can use 2DAMEMORY tokens

**Rule**: 2DAMEMORY tokens must be **defined before use**. Patches that use `2DAMEMORY#` must come **after** the patch that stores to `2DAMEMORY#`.

---

## Special Cases and Edge Cases

### 1. Runtime vs. Serialization Types

**Runtime-only types** (used in storage operations, not as cell values):

- `RowValueRowIndex()` - Created when `2DAMEMORY#=RowIndex` → Returns row index at runtime
- `RowValueRowLabel()` - Created when `2DAMEMORY#=RowLabel` → Returns row label at runtime  
- `RowValueRowCell(column)` - Created when `2DAMEMORY#=ColumnName` → Returns cell value at runtime

**Important**: These are used **only** in the LEFT side of `2DAMEMORY#=...` (storage operations).
They are **NOT** used on the RIGHT side (in cell assignments like `ColumnName=2DAMEMORY#`).

When using `2DAMEMORY#` as a VALUE (right side), you use `RowValue2DAMemory(token_id)` instead.

### 2. Type Validation

**FieldValue2DAMemory** validates types:

- Converts `str` to appropriate GFF field type
- Rejects `PureWindowsPath` in 2DA context
- Converts numeric strings to int/float as needed

### 3. Error Handling

**Common Errors**:

- `KeyError`: "2DAMEMORY{id} was not defined before use"
- `TypeError`: "!FieldPath cannot be used in 2DAList patches"
- `TypeError`: "Memory value cannot be !FieldPath in [HACKList] patches"

---

## Real-World Use Cases

### Use Case 1: Dynamic Row Referencing

```ini
[2DAList]
Table0=appearance.2da

[appearance.2da]
AddRow0=new_appearance

[new_appearance]
label=MyAppearance
2DAMEMORY0=RowIndex    # Store: row index of newly added appearance

[appearance.2da]
ChangeRow1=use_new_appearance

[use_new_appearance]
RowIndex=1
normalhead=2DAMEMORY0    # Use: set head to the stored row index
```

### Use Case 2: Cross-Patch Communication

```ini
[2DAList]
Table0=feats.2da

[feats.2da]
AddRow0=new_feat

[new_feat]
label=MY_FEAT
2DAMEMORY5=label    # Store: "MY_FEAT"

[GFFList]
File0=classes.2da

[classes.2da]
EntryList\0\FeatList\0\Feat=2DAMEMORY5    # Use: reference the feat name
```

### Use Case 3: List Index Tracking

```ini
[GFFList]
File0=test.gff

[test.gff]
AddField0=add_item

[add_item]
FieldType=Struct
Path=ItemList
TypeId=100
2DAMEMORY10=listindex    # Store: index of new item

[test.gff]
EntryList\0\ItemIndex=2DAMEMORY10    # Use: reference the item's index
```

### Use Case 4: !FieldPath Navigation

```ini
[GFFList]
File0=test.gff

[test.gff]
AddField0=store_path

[store_path]
FieldType=Int
Path=Root\SomeField
Label=SomeField
Value=42
2DAMEMORY5=!FieldPath    # Store: path to SomeField

[test.gff]
AddField1=use_path

[use_path]
FieldType=Int
Path=
Label=OtherField
Value=2DAMEMORY5    # Will navigate to SomeField and copy its value
```

---

## Implementation Classes

### Storage Classes

- `PatcherMemory.memory_2da: dict[int, str | PureWindowsPath]` - Core storage

### Value Classes (2DA Context)

- `RowValue2DAMemory` - Represents `2DAMEMORY#` reference in row values
- `RowValueConstant` - Represents literal string values
- `RowValueTLKMemory` - Represents `StrRef#` references

### Value Classes (GFF Context)

- `FieldValue2DAMemory` - Represents `2DAMEMORY#` reference in GFF fields
- `FieldValueConstant` - Represents literal GFF values
- `FieldValueTLKMemory` - Represents `StrRef#` references in GFF

### Token Usage Classes

- `TokenUsage2DA` - For SSF and other contexts that use token references

### Modifier Classes

- `Memory2DAModifierGFF` - Handles `2DAMEMORY#=!FieldPath` and `2DAMEMORY#=2DAMEMORY#`

---

## Test Coverage

From `test_tslpatcher.py`, comprehensive tests cover:

1. Storing RowIndex, RowLabel, ColumnName values
2. Using 2DAMEMORY in cell assignments
3. Using 2DAMEMORY in AddColumn operations
4. SSF patches with 2DAMEMORY
5. GFF patches with 2DAMEMORY in LocalizedString StrRef

---

## Summary

**2DAMEMORY** is a powerful cross-patch communication system that:

1. **Stores** 2DA row data during patch application
2. **References** stored values in subsequent patches
3. **Enables** dynamic patching based on runtime values
4. **Supports** complex scenarios like list index tracking and field path navigation
5. **Integrates** across all patch types: 2DA, GFF, SSF, NCS, NSS

The system is **order-dependent** - tokens must be stored before they can be referenced, following TSLPatcher's patch execution order.
