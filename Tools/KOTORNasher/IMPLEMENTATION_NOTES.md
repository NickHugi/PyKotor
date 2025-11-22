# KOTORNasher Implementation Notes

## Overview

KOTORNasher is a 1:1 implementation of nasher's syntax for KOTOR development, built entirely on PyKotor's comprehensive libraries. Unlike nasher which uses external tools, KOTORNasher leverages PyKotor's native Python implementations for all file format operations.

## Architecture

### Core Components

1. **`__main__.py`** - Entry point and argument parsing
2. **`cfg_parser.py`** - TOML configuration file parser (nasher-compatible)
3. **`logger.py`** - Colored logging system
4. **`config.py`** - Version and metadata

### Commands

All commands are in the `commands/` subdirectory:

- **`config.py`** - User configuration management
- **`init.py`** - Project initialization
- **`list.py`** - List targets
- **`unpack.py`** - Unpack modules/ERFs/haks to JSON source files
- **`convert.py`** - Convert JSON to GFF binary format
- **`compile.py`** - Compile NWScript (built-in + external compilers)
- **`pack.py`** - Pack sources into modules/ERFs/haks
- **`install.py`** - Pack and install to KOTOR directory
- **`launch.py`** - Install and launch game

## PyKotor Integration

KOTORNasher is built entirely on PyKotor and uses the following implementations:

### GFF Format Handling
- **Location**: `Libraries/PyKotor/src/pykotor/resource/formats/gff/`
- **Used for**: Converting between binary GFF and JSON
- **Key files**:
  - `gff_auto.py` - Auto-detection and conversion dispatcher
  - `io_gff.py` - Binary GFF reader/writer
  - `io_gff_json.py` - JSON GFF reader/writer
  - `gff_data.py` - GFF data structures

### ERF/Module/Hak Handling
- **Location**: `Libraries/PyKotor/src/pykotor/resource/formats/erf/`
- **Used for**: Packing/unpacking MOD, ERF, SAV, HAK files
- **Key files**:
  - `erf_auto.py` - Auto-detection and conversion
  - `io_erf.py` - Binary ERF reader/writer
  - `erf_data.py` - ERF data structures

### RIM Handling
- **Location**: `Libraries/PyKotor/src/pykotor/resource/formats/rim/`
- **Used for**: Reading RIM files
- **Key files**:
  - `rim_auto.py` - Auto-detection
  - `io_rim.py` - Binary RIM reader/writer
  - `rim_data.py` - RIM data structures

### NWScript Compilation
- **Location**: `Libraries/PyKotor/src/pykotor/resource/formats/ncs/`
- **Used for**: Compiling NSS to NCS (built-in compiler!)
- **Key files**:
  - `compilers.py` - InbuiltNCSCompiler and ExternalNCSCompiler
  - `ncs_auto.py` - Compilation dispatcher
  - `compiler/` - Full compiler implementation
    - `parser.py` - NSS parser
    - `lexer.py` - NSS lexer
    - `classes.py` - AST classes
    - `interpreter.py` - Code generation

### Resource Type System
- **Location**: `Libraries/PyKotor/src/pykotor/resource/type.py`
- **Used for**: Resource type identification and conversion
- **Features**: Maps file extensions to resource types (UTC, UTI, DLG, etc.)

## Vendor Code References

KOTORNasher's implementation is extensively informed by code in PyKotor's vendor directory:

### Primary References (High Quality)

#### **xoreos-tools** (`vendor/xoreos-tools/`)
- **Language**: C++
- **Files**: 387 C++ files
- **Key references**:
  - `src/aurora/gff3file.cpp` - GFF binary format
  - `src/aurora/erffile.cpp` - ERF format
  - `src/aurora/rimfile.cpp` - RIM format
  - `src/nwscript/compiler.cpp` - NSS compiler
- **Use**: Format specifications and edge cases

#### **KotOR.js** (`vendor/KotOR.js/`)
- **Language**: TypeScript/JavaScript
- **Files**: 983 TypeScript files
- **Key references**:
  - `src/formats/gff/GFFObject.ts` - GFF object model
  - `src/resource/ERFObject.ts` - ERF operations
  - `src/nwscript/NWScriptCompiler.ts` - NSS compilation
- **Use**: Web-based implementation patterns

#### **reone** (`vendor/reone/`)
- **Language**: C++
- **Files**: 1069 C++ files
- **Key references**:
  - `src/libs/resource/format/gffreader.cpp` - GFF reader
  - `src/libs/resource/format/erfreader.cpp` - ERF reader
  - `src/libs/script/` - Script system
- **Use**: Engine-level format handling

#### **Kotor.NET** (`vendor/Kotor.NET/`)
- **Language**: C#
- **Files**: 337 C# files
- **Key references**:
  - `Kotor.NET/GFF/` - GFF implementation
  - `Kotor.NET/ERF/` - ERF implementation
  - `Kotor.NET/Patcher/` - Patching logic
- **Use**: .NET ecosystem patterns

### Secondary References

- **xoreos-docs** - Format specifications
- **NorthernLights** - C# editor reference
- **kotorblender** - Python/Blender integration
- **Vanilla_KOTOR_Script_Source** - Complete NSS reference

## Key Features

### 1. Built-in NSS Compiler

**Major Advantage over nasher**: KOTORNasher includes PyKotor's native NSS compiler, eliminating the need for external tools.

```python
from pykotor.resource.formats.ncs.compilers import InbuiltNCSCompiler

compiler = InbuiltNCSCompiler()
compiler.compile_script(source_path, output_path, game)
```

**References**:
- `vendor/KotOR.js/src/nwscript/NWScriptCompiler.ts` - TypeScript implementation
- `vendor/xoreos-tools/src/nwscript/compiler.cpp` - C++ implementation
- `Libraries/PyKotor/src/pykotor/resource/formats/ncs/compiler/` - Python implementation (used)

### 2. Native JSON Conversion

**Advantage**: Direct GFF↔JSON conversion without intermediate formats.

```python
from pykotor.resource.formats.gff import read_gff, write_gff
from pykotor.resource.type import ResourceType

# JSON to GFF
gff = read_gff(json_file, file_format=ResourceType.GFF_JSON)
write_gff(gff, output_file, file_format=ResourceType.GFF)
```

**References**:
- `vendor/NWNT/` - Alternative text format (not used)
- `Libraries/PyKotor/src/pykotor/resource/formats/gff/io_gff_json.py` - JSON implementation (used)

### 3. Comprehensive ERF Support

**Features**: Support for MOD, ERF, SAV, HAK formats with automatic type detection.

```python
from pykotor.resource.formats.erf import read_erf, write_erf, ERFType

erf = read_erf(module_file)
erf.erf_type = ERFType.MOD
write_erf(erf, output_file)
```

**References**:
- `vendor/KotOR.js/src/resource/ERFObject.ts` - TypeScript ERF
- `vendor/xoreos-tools/src/aurora/erffile.cpp` - C++ ERF
- `Libraries/PyKotor/src/pykotor/resource/formats/erf/` - Python implementation (used)

## Configuration File Format

KOTORNasher uses TOML format for `kotornasher.cfg`, which is compatible with nasher's syntax:

```toml
[package]
name = "Package Name"
description = "Description"
version = "1.0.0"
author = "Author Name"

  [package.sources]
  include = "src/**/*.{nss,json}"
  exclude = "**/test_*.nss"
  filter = "*.nss"  # Filter from final pack
  skipCompile = "util_i_*.nss"  # Don't compile (but allow includes)
  
  [package.rules]
  "*.nss" = "src/scripts"
  "*" = "src"

[target]
name = "default"
file = "mymod.mod"
description = "Default target"
```

## Key Implementation Details

### Script Compilation Strategy

1. **Check for external compiler** (`nwnnsscomp`, `nwnsc`)
2. **If found**: Use external compiler via subprocess
3. **If not found**: Use PyKotor's `InbuiltNCSCompiler`
4. **Fallback**: Always available due to built-in compiler

This is a significant improvement over nasher, which requires external tools.

### GFF Conversion Strategy

1. **Unpack**: Binary GFF → JSON using PyKotor's JSON writer
2. **Edit**: User modifies JSON in source control
3. **Convert**: JSON → Binary GFF using PyKotor's JSON reader
4. **Pack**: Binary GFF included in module/ERF

### Variable Expansion

Supports nasher-compatible variable expansion:
- `$variable` or `${variable}` syntax
- Package-level variables
- Target-level variables
- Environment variables
- Special `$target` variable

### Target Inheritance

Targets can inherit from:
- Parent targets (via `parent` key)
- Package-level defaults
- Reduces configuration duplication

## Differences from nasher

While KOTORNasher maintains nasher's command syntax, there are important differences:

### 1. File Formats
- **nasher**: Uses neverwinter.nim's implementations
- **KOTORNasher**: Uses PyKotor's native Python implementations

### 2. Script Compiler
- **nasher**: Requires nwnsc or nwn_script_comp
- **KOTORNasher**: Built-in compiler + optional external compiler support

### 3. Games Supported
- **nasher**: Neverwinter Nights / NWN:EE
- **KOTORNasher**: KOTOR / KOTOR II

### 4. Dependencies
- **nasher**: Nim + neverwinter.nim + nwnsc/nwn_script_comp
- **KOTORNasher**: Python 3.8+ + PyKotor (nwnnsscomp optional)

### 5. Text Format
- **nasher**: JSON or NWNT
- **KOTORNasher**: JSON only (PyKotor native)

## Testing

To test KOTORNasher with vendor code references:

```bash
# Install in development mode
cd Tools/KOTORNasher
pip install -e .

# Test basic workflow
kotornasher init test_project
cd test_project
kotornasher list
kotornasher pack

# Test built-in compiler
# (Should work without nwnnsscomp installed)
echo 'void main() {}' > src/test.nss
kotornasher compile

# Test JSON conversion
kotornasher unpack --file /path/to/module.mod
# Verify JSON files created
kotornasher convert
# Verify GFF files in cache
```

## Performance Considerations

### Compilation Speed
- **Built-in compiler**: Pure Python, ~10-50x slower than nwnnsscomp
- **External compiler**: Native C++, very fast
- **Strategy**: Auto-detect external compiler for best performance

### JSON Conversion
- **PyKotor**: Optimized C-extension paths for critical operations
- **Comparable** to neverwinter.nim's performance

### ERF Operations
- **PyKotor**: Streaming readers for large files
- **Memory efficient**: Doesn't load entire archives into memory

## Future Enhancements

Potential improvements informed by vendor code:

1. **RIM Packing**: Currently read-only, add write support
2. **Module Folder Support**: KOTOR2's development mode
3. **Improved Decompiler**: Leverage PyKotor's NCS decompiler
4. **TLK Support**: Currently minimal, enhance for full localization
5. **Parallel Compilation**: Compile multiple scripts concurrently
6. **Cache Optimization**: Better dependency tracking for incremental builds

## Vendor Code Usage Guidelines

When referencing vendor code:

1. **Always cite source**: Include file path and line numbers in comments
2. **Note differences**: KOTOR vs NWN format differences
3. **Prefer PyKotor**: Use PyKotor implementations, vendor for reference only
4. **Check accuracy**: reone, xoreos, KotOR.js most accurate
5. **Be cautious**: Some vendor projects may have bugs or be incomplete

## Contributing

When contributing to KOTORNasher:

1. **Maintain nasher syntax compatibility**
2. **Use PyKotor implementations** (don't reinvent the wheel)
3. **Add vendor references** in code comments
4. **Follow PyKotor conventions** (see CONVENTIONS.md)
5. **Update documentation** for new features
6. **Add tests** for functionality

## References

- [nasher](https://github.com/squattingmonk/nasher) - Original NWN build tool
- [neverwinter.nim](https://github.com/niv/neverwinter.nim) - NWN tools in Nim
- [NWNT](https://github.com/WilliamDraco/NWNT) - Alternative text format
- [PyKotor](https://github.com/NickHugi/PyKotor) - KOTOR modding library
- [xoreos-tools](https://github.com/xoreos/xoreos-tools) - File format tools
- [KotOR.js](https://github.com/KobaltBlu/KotOR.js) - Web-based engine
- [reone](https://github.com/seedhartha/reone) - KOTOR engine reimplementation
