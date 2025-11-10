# Comprehensive TSLPatcher Diff & Writer Test Suite

This directory contains exhaustive tests for the TSLPatcher diff engine and INI writer components.

## Test Coverage

### 1. **2DAMEMORY Tests** (`Test2DAMemoryComprehensive`)

Tests for 2DA memory token generation and usage:

- ✅ `test_addrow_stores_row_index` - AddRow2DA stores row index in 2DAMEMORY token
- ✅ `test_changerow_stores_row_index` - ChangeRow2DA stores row index
- ✅ `test_2damemory_cross_reference_chain` - Chained 2DAMEMORY references across multiple 2DA files (weaponsounds → baseitems → GFF pattern)
- ✅ `test_addcolumn_with_2damemory_storage` - AddColumn with specific cell value storage
- ✅ `test_multiple_gff_files_use_same_2damemory_token` - Multiple GFF files referencing same token
- ⏸️ `test_2damemory_row_label_storage` - Storing row label (not index) in token
- ⏸️ `test_2damemory_row_cell_storage` - Storing specific cell value
- ✅ `test_2damemory_high_function` - Using High() function in 2DA modifications

### 2. **TLK/StrRef Tests** (`TestTLKStrRefComprehensive`)

Tests for TLK modifications and StrRef token generation:

- ✅ `test_tlk_append_basic` - Basic TLK append with new entries
- ✅ `test_tlk_replace_existing_entries` - TLK replace mode for modifying existing entries
- ✅ `test_strref_used_in_2da` - StrRef token used in 2DA file
- ⏸️ `test_strref_used_in_gff_localized_string` - StrRef in LocalizedString field
- ✅ `test_strref_used_in_ssf` - StrRef token used in SSF file

### 3. **GFF Tests** (`TestGFFComprehensive`)

Tests for all GFF modification types:

- ✅ `test_gff_modify_all_field_types` - Modify all GFF field types (Byte, Char, Word, Short, DWORD, Int, Int64, Float, Double, String, ResRef, LocalizedString, Vector3, Vector4)
- ✅ `test_gff_add_field_to_struct` - AddFieldGFF to add new fields
- ✅ `test_gff_nested_struct_modifications` - Modify fields in nested structs
- ✅ `test_gff_list_modifications` - Modifications to GFF lists (AddStructToListGFF)
- ✅ `test_gff_localized_string_with_multiple_languages` - LocalizedString with multiple language/gender variants

### 4. **SSF Tests** (`TestSSFComprehensive`)

Tests for SSF sound file modifications:

- ✅ `test_ssf_modify_all_sound_slots` - Modify all SSF sound slots

### 5. **Integration Tests** (`TestIntegrationComprehensive`)

Tests for cross-file references and complex scenarios:

- ✅ `test_full_mod_scenario_new_spell` - Complete mod: new force power (based on "Bastila Has Battle Meditation" pattern)
- ✅ `test_full_mod_scenario_new_item_type` - Complete mod: new item type (based on "dm_qrts" quarterstaff pattern)

### 6. **Real-World Scenario Tests** (`TestRealWorldScenarios`)

Tests based on actual mods from the workspace:

- ✅ `test_ajunta_pall_appearance_mod` - Ajunta Pall Unique Appearance pattern
- ✅ `test_k1_community_patch_pattern` - K1 Community Patch with extensive TLK modifications

### 7. **InstallList Tests** (`TestInstallListComprehensive`)

Tests for file installation specifications:

- ✅ `test_install_to_override` - Files installed to Override folder
- ⏸️ `test_install_to_modules` - Files installed to specific module folders

### 8. **Edge Cases & Error Conditions** (`TestEdgeCasesComprehensive`)

Tests for edge cases and potential error conditions:

- ✅ `test_empty_2da_modification` - 2DA with no actual changes
- ✅ `test_2da_with_empty_cells` - 2DA with **** empty cell markers
- ✅ `test_gff_with_special_characters_in_strings` - GFF strings with special characters (newlines, tabs)
- ✅ `test_large_2da_many_rows` - Large 2DA file with 100 rows

### 9. **Performance & Stress Tests** (`TestPerformanceComprehensive`)

Performance and scalability tests:

- ✅ `test_many_2da_files` - Diff with 20 2DA files
- ✅ `test_many_gff_files` - Diff with 20 GFF files

## Real-World Examples Used

The test suite is based on analysis of actual mods from the workspace:

### Bastila Has Battle Meditation
```ini
[spells.2da]
AddRow0=Battle_Meditation
[Battle_Meditation]
2DAMEMORY1=RowIndex

[p_bastilla.utc]
ClassList\0\KnownList0\1\Spell=2DAMEMORY1
```

### DeadMan's Quarterstaffs (dm_qrts)
```ini
[weaponsounds.2da]
AddRow0=weaponsounds_row_dm_electrostaff_0
[weaponsounds_row_dm_electrostaff_0]
2DAMEMORY1=RowIndex

[baseitems.2da]
AddRow0=baseitems_row_dm_electrostaff_0
[baseitems_row_dm_electrostaff_0]
weaponmattype=2DAMEMORY1
2DAMEMORY2=RowIndex

[propqs02.uti]
BaseItem=2DAMEMORY2
```

### K1 Community Patch
```ini
[TLKList]
StrRef0=0
StrRef1=1
...
StrRef39=39

[append.tlk]
25859=27
45953=29
```

## Test Helper Utilities

### `TestDataHelper` Class

Provides utility methods for creating test data:

- `create_test_env()` - Create temp directories (vanilla, modded, tslpatchdata)
- `cleanup_test_env()` - Clean up temp directories
- `create_basic_2da()` - Create a 2DA file with headers and rows
- `create_basic_gff()` - Create a GFF file with root-level fields
- `create_basic_tlk()` - Create a TLK file with entries
- `create_basic_ssf()` - Create an SSF file with sound mappings
- `run_diff()` - Run the diff engine and return generated INI
- `assert_ini_section_exists()` - Assert INI section exists
- `assert_ini_key_value()` - Assert INI key/value pair

## Running Tests

### Run All Tests
```bash
cd tests/test_tslpatcher
python test_diff_comprehensive.py
```

### Run Specific Test Class
```bash
python test_diff_comprehensive.py Test2DAMemoryComprehensive
```

### Run Specific Test
```bash
python test_diff_comprehensive.py Test2DAMemoryComprehensive.test_addrow_stores_row_index -v
```

### Run with Coverage
```bash
uv run pytest test_diff_comprehensive.py --cov=pykotor.tslpatcher --cov-report=html
```

## Expected Test Output

Each test prints the generated INI content for manual inspection:

```
=== test_addrow_stores_row_index ===
; ============================================================================
;  TSLPatcher Modifications File — Generated by HoloPatcher (11/08/2025)
; ============================================================================
...
[2DAList]
Table0=spells.2da

[spells.2da]
AddRow0=spells_2da_addrow_2

[spells_2da_addrow_2]
RowLabel=2
label=new_spell
name=102
2DAMEMORY0=RowIndex
ExclusiveColumn=label
```

## Test Status Legend

- ✅ **Implemented** - Test is fully implemented and runs
- ⏸️ **Skipped** - Test is implemented but skipped (waiting for feature implementation)
- ❌ **Failed** - Test exists but currently failing
- 🔄 **In Progress** - Test is being developed

## Coverage Goals

The test suite aims for:

- **100% coverage** of TSLPatcher INI syntax from official documentation
- **Real-world scenarios** from actual mods in the community
- **Edge cases** that might break the differ or writer
- **Performance** validation for large-scale mods

## Contributing

When adding new tests:

1. Use descriptive test names that explain what's being tested
2. Include docstrings with the pattern being tested
3. Print generated INI for manual inspection
4. Add real-world examples if available
5. Update this README with test status

## References

- [TSLPatcher Official Readme](../../wiki/TSLPatcher's-Official-Readme.md)
- [TSLPatcher 2DAList Syntax](../../wiki/TSLPatcher-2DAList-Syntax.md)
- [TSLPatcher GFFList Syntax](../../wiki/TSLPatcher-GFFList-Syntax.md)
- [2DAMEMORY Token Scenarios](../../Libraries/PyKotor/src/pykotor/tslpatcher/diff/2DAMEMORY_TOKEN_SCENARIOS.md)
- [2DA Row Reference Analysis](../../Libraries/PyKotor/src/pykotor/tslpatcher/diff/2DA_ROW_REFERENCE_ANALYSIS.md)

