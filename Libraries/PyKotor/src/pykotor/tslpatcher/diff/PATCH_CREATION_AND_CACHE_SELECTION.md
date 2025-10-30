# Patch Creation and Cache Selection

This document explains where StrRef# and 2DAMEMORY# linking patches are created and how cache selection currently works.

## Where Patches Are Created

### 1. StrRef# Patches (for TLK modifications)

**Location:** `incremental_writer.py` - `_create_linking_patches_from_cache()` (line 683)

**Called from:** `_write_tlk_modification()` (line 674)

**Patches created in:**

- **[GFFList]**: GFF files with `LocalizedString` fields referencing modified StrRefs
- **[2DAList]**: 2DA files with StrRef columns referencing modified StrRefs  
- **[SSFList]**: SSF files with StrRef sound entries referencing modified StrRefs
- **[HACKList]**: NCS files with CONSTI instructions referencing modified StrRefs

**Cache used:** `self.strref_cache` (single cache, no choice)

**Flow:**

```
TLK modification detected
  → _write_tlk_modification()
    → _create_linking_patches_from_cache()
      → Query strref_cache.get_references(old_strref)
      → Create ModifyFieldGFF/ModifySSF/ChangeRow2DA/ModifyNCS patches
```

### 2. 2DAMEMORY# Patches (for 2DA row modifications)

**Location:** `incremental_writer.py` - Two separate functions:

- `_create_2da_linking_patches_for_existing_rows()` (line 401) - for ChangeRow2DA
- `_create_2da_linking_patches_for_new_rows()` (line 487) - for AddRow2DA

**Called from:** `_write_2da_modification()` (lines 314, 320)

**Patches created in:**

- **[GFFList]**: GFF files with fields referencing modified 2DA rows

**Cache selection:**

- `ChangeRow2DA` → Always uses `vanilla_twoda_cache` (hardcoded)
- `AddRow2DA` → Always uses `modded_twoda_cache` (hardcoded)

**Flow:**

```
2DA modification detected
  → _write_2da_modification()
    → _prepare_twoda_tokens()  # Splits into change vs add based on modifier type
      → change_row_targets (ChangeRow2DA modifiers) → vanilla_twoda_cache
      → add_row_targets (AddRow2DA modifiers) → modded_twoda_cache
    → _create_2da_linking_patches_for_existing_rows(change_row_targets)
      → Query vanilla_twoda_cache.get_references()
      → Create ModifyFieldGFF patches
    → _create_2da_linking_patches_for_new_rows(add_row_targets)
      → Query modded_twoda_cache.get_references()
      → (Currently only logs, doesn't create patches due to row_index unknown)
```

## Current Cache Selection Logic

### StrRef Cache

- **Single cache**: `self.strref_cache`
- **No selection needed**: All StrRef patches use the same cache
- **Built from**: Installation that has StrRefs that others don't (determined during diff)

### 2DA Cache  

- **Two caches**: `vanilla_twoda_cache` and `modded_twoda_cache`
- **Selection method**: Based on **modifier type**, not which installation has the entry:
  - `ChangeRow2DA` modifier → `vanilla_twoda_cache`
  - `AddRow2DA` modifier → `modded_twoda_cache`

**Problem:** This assumes:

- `ChangeRow2DA` = row exists in install1
- `AddRow2DA` = row exists in install2

This only works correctly for 2-way diffs. For n-way diffs, we need to determine which installation(s) actually have the entry and use the appropriate cache(s).

## N-Way Diff Issue

For n-way diffs, the cache selection should be based on **which installation has the entry**, not modifier type:

**Current (assumes 2-way):**

- `ChangeRow2DA` → always use `vanilla_twoda_cache`
- `AddRow2DA` → always use `modded_twoda_cache`

**Should be (n-way aware):**

- Entry exists in install1 but not install2 → use `vanilla_twoda_cache`
- Entry exists in install2 but not install1 → use `modded_twoda_cache`
- Entry exists in install3 but not install1/install2 → use cache built from install3
- etc.

## Proposed Solution

The cache selection logic in `_prepare_twoda_tokens()` and `_write_2da_modification()` needs to be aware of which installation(s) have each entry, not just assume based on modifier type.

This could be done by:

1. Tracking which installations have each 2DA row during the diff process
2. Passing this information through to the modifier creation
3. Using it to select the correct cache(s) for linking patches
