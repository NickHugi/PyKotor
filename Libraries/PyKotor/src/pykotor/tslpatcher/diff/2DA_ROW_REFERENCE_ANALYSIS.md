# 2DA Row Reference Analysis

This document explains how KOTOR file formats reference and use 2DA row values, similar to how StrRef references work. This is essential for implementing findref/search functionality for 2DA rows.

## Current Implementation

The `TwoDAMemoryReferenceCache` currently scans for 2DA row references in:

### 1. **GFF Files** (Currently Implemented)

**Location:** `Libraries/PyKotor/src/pykotor/tslpatcher/diff/twoda_memory_cache.py`

**How it works:**

- Uses `GFF_FIELD_TO_2DA_MAPPING` dictionary to map GFF field names to 2DA filenames
- Scans GFF structures recursively for integer fields matching mapped field names
- Extracts the integer value as the row index

**Field Types:**

- `Int8`, `Int16`, `Int32`, `Int64` - Signed integers
- `UInt8`, `UInt16`, `UInt32`, `UInt64` - Unsigned integers

**Example Fields:**

- `Appearance_Type` → `appearance.2da`
- `SoundSetFile` → `soundset.2da`
- `BaseItem` → `baseitems.2da`
- `PortraitId` → `portraits.2da`
- etc. (see `GFF_FIELD_TO_2DA_MAPPING` for full list)

**Code Pattern:**

```python
if label in GFF_FIELD_TO_2DA_MAPPING:
    twoda_filename = GFF_FIELD_TO_2DA_MAPPING[label]
    if field_type in (Int8, Int16, Int32, Int64, UInt8, UInt16, UInt32, UInt64):
        row_index = value  # Integer value is the row index
        self._add_reference(twoda_filename, row_index, identifier, field_path)
```

## Other Potential Formats

### 2. **2DA Files (Cross-References)**

**Status:** Not Currently Implemented

**Use Case:**
Some 2DA files might reference rows from other 2DA files. For example:

- A 2DA file might have a column containing integer values that reference rows in another 2DA

**How to Implement:**

```python
def _scan_2da(
    self,
    identifier: ResourceIdentifier,
    data: bytes,
) -> None:
    """Scan 2DA file for references to other 2DA rows."""
    twoda_obj = read_2da(data)
    twoda_filename: str = identifier.resname.lower()
    
    # Need a mapping of: (source_2da_filename, column_name) -> target_2da_filename
    # For example: ("appearance.2da", "race") -> "racialtypes.2da"
    
    if twoda_filename in CROSS_REFERENCE_2DA_MAPPING:
        column_mappings = CROSS_REFERENCE_2DA_MAPPING[twoda_filename]
        
        for row_idx in range(twoda_obj.get_height()):
            for column_name, target_2da in column_mappings.items():
                cell_value = twoda_obj.get_cell(row_idx, column_name)
                if cell_value and cell_value.strip().isdigit():
                    target_row_index = int(cell_value.strip())
                    # Add reference: source 2DA row references target 2DA row
                    self._add_reference(target_2da, target_row_index, identifier, f"row_{row_idx}.{column_name}")
```

**Challenges:**

- Need to define which 2DA columns reference which other 2DA files
- Cross-references are less common than GFF references
- Many 2DA columns are just data, not references

### 3. **NCS Files (Compiled Scripts)**

**Status:** Not Currently Implemented (Similar to StrRef NCS scanning)

**Use Case:**
NCS files (compiled scripts) may contain integer constants that are 2DA row indices, similar to how they can contain StrRef constants.

**How to Implement (Similar to StrRef):**

```python
def _scan_ncs(
    self,
    identifier: ResourceIdentifier,
    data: bytes,
) -> None:
    """Scan NCS file for 2DA row index constants."""
    # Similar to _extract_ncs_consti_offsets in analyzers.py
    # Parse NCS bytecode and extract CONSTI instructions with integer values
    
    # Challenge: We need to know which 2DA file and which row index to search for
    # Unlike StrRef scanning where we can scan for all StrRefs and match later,
    # we need to know the target 2DA rows in advance OR scan for any integers
    # and validate if they're valid 2DA row indices
    
    # Option 1: Defer scanning until we know which rows are modified
    # Option 2: Scan all integers and cache potential matches (expensive)
    # Option 3: Skip NCS scanning for 2DA rows (most practical)
```

**Challenges:**

- Need to know target 2DA filename and row index in advance (unlike StrRef which can scan all values)
- More complex than StrRef scanning
- Many integers in NCS are not 2DA row references

### 4. **SSF Files**

**Status:** Not Applicable

**Reason:**
SSF files (Sound Set Files) contain StrRef references, not 2DA row references. They are already handled by `StrRefReferenceCache`.

### 5. **TLK Files**

**Status:** Not Applicable

**Reason:**
TLK files are text databases, not binary formats that would reference 2DA rows.

## Comparison: StrRef vs 2DA Row References

### StrRef References

**Formats Scanned:**

1. **GFF files** - `LocalizedString` fields with `stringref` values
2. **2DA files** - Specific columns containing StrRef values (game-specific)
3. **SSF files** - Sound slots with StrRef values
4. **NCS files** - CONSTI instructions with StrRef constants (deferred)

**Key Difference:** StrRef values can be scanned and cached before knowing which TLK entries will be modified. We scan for ALL StrRef values and match them later when TLK modifications are created.

### 2DA Row References

**Formats Scanned:**

1. **GFF files** - Integer fields mapped to 2DA filenames via `GFF_FIELD_TO_2DA_MAPPING`

**Key Difference:** 2DA row references are context-dependent - we need to know:

- The 2DA filename (from field name mapping)
- The row index (from integer field value)
- Both together form the reference

**Why Limited:** Unlike StrRefs which are global identifiers, 2DA row references are specific to:

- A particular 2DA file (e.g., `appearance.2da`)
- A particular row index in that file

## Implementation Recommendations

### Current Status: ✅ GFF Files (Complete)

The current implementation correctly handles the primary use case:

- Most 2DA row references in KOTOR are in GFF files
- The `GFF_FIELD_TO_2DA_MAPPING` covers the vast majority of cases
- Integer fields are correctly extracted and mapped

### Future Enhancements

1. **2DA Cross-References** (Low Priority)
   - Define `CROSS_REFERENCE_2DA_MAPPING: dict[str, dict[str, str]]`
   - Map: `{source_2da: {column_name: target_2da}}`
   - Example: `{"appearance.2da": {"race": "racialtypes.2da"}}`
   - Only implement if there's evidence of actual cross-references being used

2. **NCS Scanning** (Low Priority)
   - Similar complexity to StrRef NCS scanning
   - Only worth implementing if there's evidence that NCS files commonly use 2DA row indices as constants
   - Defer until needed, as it's expensive and may yield few results

3. **Expand GFF Field Mapping** (Medium Priority)
   - Review all GFF file formats to ensure `GFF_FIELD_TO_2DA_MAPPING` is complete
   - Add any missing field-to-2DA mappings
   - Test with real mod files to find gaps

## Scanning Process Flow

```
1. Build cache from installation that HAS the 2DA row
   ↓
2. For each resource in installation:
   ↓
3. Check resource type:
   ├─ GFF file → Scan recursively for mapped fields
   ├─ 2DA file → (Future: Check for cross-references)
   ├─ NCS file → (Future: Parse bytecode for constants)
   └─ Other → Skip
   ↓
4. For each found reference:
   ├─ Extract: 2DA filename, row index, resource identifier, field path
   └─ Add to cache: (2da_filename, row_index) → [(identifier, [paths])]
```

## Testing Strategy

To verify the implementation is complete:

1. **GFF Files:**
   - Test with known GFF files that reference 2DA rows
   - Verify all fields in `GFF_FIELD_TO_2DA_MAPPING` are found
   - Check nested structs and lists are scanned

2. **Edge Cases:**
   - Negative row indices (should be ignored)
   - Very large row indices (boundary testing)
   - Fields with same name in different contexts (should all be scanned)

3. **Performance:**
   - Measure cache building time for full installation scan
   - Compare with StrRef cache building time
   - Verify cache lookup speed

## Summary

The current implementation focuses on **GFF files**, which is the correct primary target because:

- ✅ Most 2DA row references are in GFF files
- ✅ Field name mapping is straightforward and complete
- ✅ Integer extraction is reliable
- ✅ Nested structures are handled correctly

**Other formats (2DA cross-refs, NCS) are lower priority** because:

- Less common use cases
- More complex to implement
- May not yield significant additional value

The findref/search functionality for 2DA rows is effectively complete for the primary use case (GFF files), similar to how StrRef references work.
