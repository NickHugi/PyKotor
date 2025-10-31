# N-Way Comparison Implementation Plan

## Overview

Refactor the entire KotorDiff system to support arbitrary number of paths (N-way comparison) where each path can be:

- An Installation object (game installation directory)
- A folder containing arbitrary files
- A single file (including .rim, .mod, _s.rim,_dlg.erf, etc.)

## Key Requirements

### 1. Path Flexibility

- Any path can be any type (Installation | folder | file)
- Composite module logic must work across non-Installation paths
- Example: path1=.rim, path2=_s.rim, path3=.mod, path4=Installation
  - path1+path2 = composite module compared to path3.mod and path4's module

### 2. No Hardcoded Assumptions

- Remove all "vanilla" vs "modded" terminology
- Remove all `install1`/`install2` paired parameters
- All functions accept `list[Path | Installation]`
- Paths are interchangeable - no priority except optionally the last path

### 3. Patch Generation

- ALL differences across ALL N paths generate patches
- Resources in any path but not others → InstallList + patches
- TSLPatchdata generation works for N-way comparisons

## Implementation Status

### Completed ✓

1. Fixed GFF writer format bug (ResourceType.GFF not UTD/UTC)
2. Created `diff_n_installations_with_resolution()` wrapper function
3. Removed "REMOVED" logic - resources generate patches from any path
4. Updated terminology in resolution.py docstrings
5. Added `handle_n_way_diff_internal()` stub in app.py

### In Progress 🔄

1. **engine.py** - Core comparison logic
   - `run_differ_from_args_impl()` - Currently 2-way only
   - Need: `run_n_way_differ()` accepting `list[Path | Installation]`

2. **resolution.py** - Resource resolution
   - `diff_installations_with_resolution()` - Still requires install1/install2
   - Need: Full n-way iteration over all installations

### Not Started ❌

#### Core Engine (engine.py)

1. Create `PathInfo` dataclass to wrap Path | Installation with metadata
2. Create `compare_n_paths()` function that:
   - Loads all paths (Installation objects, folders, files)
   - Groups composite modules across ALL paths
   - Collects all unique resource identifiers across ALL paths
   - Compares each resource across ALL N paths
   - Generates patches for any differences

3. Update `handle_special_comparisons()` for n-way:
   - Handle mixed path types (some Install, some file, some folder)
   - Composite module detection across N paths
   - Resource resolution when some paths are Installations

4. Update `diff_capsule_files()` to accept list of capsule files

#### Resolution (resolution.py)

1. Complete n-way implementation in `diff_n_installations_with_resolution()`:
   - Remove delegation to 2-way function
   - Iterate over N installations
   - Compare each resource across all N installations
   - Generate patches from whichever installation has the resource

2. Update all helper functions to work with N installations:
   - `_log_consolidated_resolution()` - Already updated
   - `explain_resolution_order()` - Already updated
   - `_build_strref_cache()` - Works with single installation
   - `_build_twoda_cache()` - Works with single installation

#### CLI/App (app.py, **main**.py)

1. Update argument parsing:
   - Keep --mine, --older, --yours for compatibility
   - `args.extra_paths` already collects additional paths
   - Consolidate all into single `list[Path]`

2. Update `handle_n_way_diff()` to:
   - Create IncrementalTSLPatchDataWriter with N-way support
   - Initialize caches for ALL N paths (not just 0 and 1)
   - Call `run_n_way_differ()` with full path list

3. Update `_log_configuration()` to show all N paths

#### Incremental Writer (incremental_writer.py)

1. Update cache structures to handle N installations:
   - `twoda_caches: dict[int, CaseInsensitiveDict]` - Already supports N
   - Track source_index properly for N paths

2. Update `register_tlk_modification_with_source()`:
   - Works with any source_index (not just 0 and 1)

## Technical Details

### Composite Module Handling

The existing code has:

- `CompositeModuleCapsule` - Loads .rim + _s.rim +_dlg.erf as one unit
- `should_use_composite_for_file()` - Determines when to use composite
- `find_related_module_files()` - Finds related files

For N-way, need to:

1. Group modules by basename across ALL N paths
2. For each basename group:
   - Identify which paths have .mod
   - Identify which paths have .rim files (composite)
   - Compare .mod to composite OR composite to composite
   - Handle mixed scenarios (path1=.rim, path2=_s.rim from different paths)

### Resource Collection Strategy

```python
def collect_all_resources_n_way(paths: list[Path | Installation]) -> dict[str, dict[int, bytes]]:
    """
    Returns: {
        "resourcename.ext": {
            0: bytes_from_path0,
            1: bytes_from_path1,
            2: bytes_from_path2,
            # Missing paths don't have entries
        }
    }
    """
```

### Comparison Logic

```python
for resource_id, path_data in all_resources.items():
    if len(path_data) == 1:
        # Resource only in one path → InstallList + patch
        generate_install_patch(resource_id, path_data)
    else:
        # Resource in multiple paths → compare all pairs
        for (idx_a, data_a), (idx_b, data_b) in combinations(path_data.items(), 2):
            if data_a != data_b:
                generate_modification_patch(resource_id, idx_a, idx_b, data_a, data_b)
```

## Dependencies

- utility.system.path.Path
- pykotor.extract.installation.Installation
- pykotor.extract.capsule.Capsule
- pykotor.tslpatcher.diff.incremental_writer.IncrementalTSLPatchDataWriter

## Testing Strategy

1. Test 2-way (ensure backwards compatibility)
2. Test 3-way (mine, older, yours)
3. Test 4-way with extra_paths
4. Test mixed types:
   - Install + Install
   - Install + folder
   - Install + file
   - folder + file
   - file + file
5. Test composite modules:
   - .rim vs .mod
   - .rim + _s.rim (from different paths) vs .mod
   - Multiple composite modules
