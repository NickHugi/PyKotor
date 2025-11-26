# Save Game Editing Progress

## Problem Statement

When opening resources from save game files (e.g., `.git`, `.ifo`, `.are` files from nested ERF structures in `SAVEGAME.sav`), the editors fail because:

1. **Incomplete Resources**: Save game resources only contain deltas/changes, not complete module data
2. **Extra Undocumented Fields**: Save game GFF files contain extra fields that aren't in the base module files
3. **Field Stripping**: When `build()` is called, editors create "clean" GFF files that strip these extra fields
4. **Save Corruption**: This breaks the save game because the extra fields are required

## Investigation Status

### ✅ Completed
- [x] Identified the problem: Save game resources are incomplete and contain extra fields
- [x] Found existing `attemptKeepOldGFFFields` mechanism in Editor base class
- [x] Located `add_missing()` method in GFF data structures
- [x] Reviewed SaveNestedCapsule structure and how it handles resources

### 🔄 In Progress
- [x] Investigating how reone/xoreos/KotOR.js handle save game resource loading
- [x] Understanding how KSE merges base module data with save game deltas
- [x] Creating detection mechanism for save game resources
- [x] Implementing field preservation in all GFF-based editors
- [x] Updating base.py editor class (if needed)
- [ ] Testing with actual save game files

### ⏳ Pending
- [ ] Test with actual save game files
- [ ] Ensure all editors (GIT, IFO, ARE, UTC, etc.) handle save resources correctly
- [ ] Document the solution

## Key Findings

### Current Implementation
- `Editor.save()` already has `attemptKeepOldGFFFields` mechanism (line 584-594 in editor.py)
- Uses `new_gff.root.add_missing(old_gff.root)` to preserve fields
- Only works if `_revert` data is available (original file data)

### Save Game Structure
- `SAVEGAME.sav` is a nested ERF containing:
  - Cached modules (`.sav` files) - each is another ERF
  - Each cached module contains incomplete GFF files (`.git`, `.ifo`, `.are`)
  - These GFF files have extra undocumented fields
  - They only contain changes/deltas from the base module

### KSE (kotor-savegame-editor) Approach
- Extracts resources to temp files
- When saving, imports back into nested ERF structure
- Preserves original byte structure where possible
- Merges changes with base module data when needed

## Solution Strategy

1. **Detection**: Detect when a resource is from a save game
   - Check filepath for nested ERF structure
   - Check if parent is a `.sav` file
   - Store save game context in editor

2. **Field Preservation**: Ensure extra fields are preserved
   - Use existing `attemptKeepOldGFFFields` mechanism
   - Ensure `_revert` data is always available for save resources
   - Potentially merge with base module data

3. **Base Module Merging**: When needed, merge with base module
   - Load base module resource
   - Apply save game deltas on top
   - Preserve all fields from both

4. **Editor Updates**: Update all GFF-based editors
   - GIT, IFO, ARE, UTC, UTP, UTD, UTE, UTI, UTM, UTS, UTT, UTW
   - Ensure they all handle save game resources correctly

## Implementation Details

### Save Game Detection
- Added `_is_save_game_resource` flag to Editor class
- Created `_detect_save_game_resource()` method that checks filepath for `.sav` files
- Detection works by traversing the filepath and checking if any parent is a `.sav` file
- This handles nested structures like `SAVEGAME.sav/module.sav/resource.git`

### Field Preservation
- Modified `Editor.save()` to ALWAYS preserve fields for save game resources
- Save game resources bypass the `attemptKeepOldGFFFields` setting
- Uses existing `add_missing()` mechanism to preserve extra fields
- Ensures `_revert` data is always available (set in `load()`)

### Code Changes
- `Tools/HolocronToolset/src/toolset/gui/editor.py`:
  - Added `_is_save_game_resource: bool` flag
  - Added `_detect_save_game_resource()` method
  - Updated `load()` to detect save game resources
  - Updated `save()` to force field preservation for save game resources
  - Updated `new()` to reset the flag

- `Tools/HolocronToolset/src/toolset/gui/editor/base.py`:
  - Same changes as above (for editors using the base.py Editor class)

- `Tools/HolocronToolset/src/toolset/gui/editors/lyt.py`:
  - Fixed non-standard `load()` signature to match standard `load(filepath, resref, restype, data)`
  - Added `super().load()` call to enable save game detection (for consistency)
  - Note: LYT files are plain-text ASCII, NOT GFF files, so they don't need field preservation
  - The fix ensures LYT editor follows the same pattern as other editors for consistency

### Editor Coverage - ALL GFF-BASED EDITORS COVERED ✅

**All GFF-based editors automatically inherit save game detection and field preservation** because they all inherit from the base `Editor` class and call `super().load()`. This includes:

✅ **GIT Editor** - Handles `.git` files (area instance data) - **COVERED**
✅ **IFO Editor** - Handles `.ifo` files (module information) - **COVERED**
✅ **ARE Editor** - Handles `.are` files (area information) - **COVERED**
✅ **UTC Editor** - Handles `.utc` files (creature templates) - **COVERED**
✅ **UTI Editor** - Handles `.uti` files (item templates) - **COVERED**
✅ **UTP Editor** - Handles `.utp` files (placeable templates) - **COVERED**
✅ **UTD Editor** - Handles `.utd` files (door templates) - **COVERED**
✅ **UTE Editor** - Handles `.ute` files (encounter templates) - **COVERED**
✅ **UTM Editor** - Handles `.utm` files (merchant templates) - **COVERED**
✅ **UTS Editor** - Handles `.uts` files (sound templates) - **COVERED**
✅ **UTT Editor** - Handles `.utt` files (trigger templates) - **COVERED**
✅ **UTW Editor** - Handles `.utw` files (waypoint templates) - **COVERED**
✅ **DLG Editor** - Handles `.dlg` files (dialogue trees) - **COVERED**
✅ **JRL Editor** - Handles `.jrl` files (journal entries) - **COVERED**
✅ **PTH Editor** - Handles `.pth` files (pathfinding data) - **COVERED**
✅ **SAV Editor** - Handles `.sav` files (save game resources) - **COVERED**
✅ **LYT Editor** - Handles `.lyt` files (layout files, plain-text ASCII, NOT GFF) - **FIXED** (was using non-standard load signature, now fixed - doesn't need field preservation since it's not GFF)

**Special Cases (No Action Needed):**
- **GFF Editor**: Intentionally excluded from field preservation (it's a raw GFF editor that should allow full control)
- **ERF Editor**: Overrides `save()` but doesn't edit GFF files directly (edits ERF archives, not individual GFF resources)
- **SaveGame Editor**: Overrides `save()` but doesn't edit individual GFF resources (edits save folders)

## Testing

Comprehensive test suite created in `tests/test_toolset/gui/editors/`:

### `test_savegame_editor.py`
Tests all 8 Save Game Editor improvements:
1. ✅ Screenshot aspect ratio preservation
2. ✅ Party member names and tooltips
3. ✅ Scrollbar interaction disabled
4. ✅ Global variables whitespace optimization
5. ✅ Character names and equipment editing
6. ✅ Skills tab label
7. ✅ Inventory item names
8. ✅ Journal tab redesign

### `test_savegame_resource_detection.py`
Tests save game resource handling:
- ✅ Save game detection from file paths
- ✅ Field preservation for save game resources
- ✅ All GFF-based editors inherit detection
- ✅ LYT editor uses correct load signature
- ✅ Roundtrip testing (load -> modify -> save -> load)
- ✅ Edge cases (case-insensitive, deeply nested paths)

## Next Steps

1. ✅ Investigate reone/xoreos/KotOR.js save game handling
2. ✅ Create save game detection utility
3. ✅ Implement field preservation in Editor base class
4. ✅ Update base.py editor class
5. ✅ Verify all GFF-based editors are covered (they are - via inheritance)
6. ✅ Create comprehensive test suite
7. ⏳ Test with actual save game files

