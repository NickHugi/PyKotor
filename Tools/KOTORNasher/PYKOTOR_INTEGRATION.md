# PyKotor Integration Guide

This document details how KOTORNasher leverages PyKotor's comprehensive libraries and vendor code references.

## Key Advantages Over Initial Implementation

### 1. Built-in NSS Compiler (Major Feature!)

**Initial Implementation**: Required external nwnnsscomp/nwnsc
**Current Implementation**: Uses PyKotor's native `InbuiltNCSCompiler`

```python
from pykotor.resource.formats.ncs.compilers import InbuiltNCSCompiler
from pykotor.common.misc import Game

compiler = InbuiltNCSCompiler()
compiler.compile_script(
    source_path="test.nss",
    output_path="test.ncs",
    game=Game.K2,
    debug=False
)
```

**Benefits**:
- No external dependencies required
- Works out of the box
- Fallback to external compiler if available for performance
- Supports all KOTOR NSS features

**Vendor References**:
- `vendor/KotOR.js/src/nwscript/NWScriptCompiler.ts` - TypeScript compiler
- `vendor/xoreos-tools/src/nwscript/compiler.cpp` - C++ compiler
- `vendor/reone/src/libs/script/` - Engine script system

### 2. Native JSON Conversion

**Initial Implementation**: Manual JSON dict conversion
**Current Implementation**: Uses PyKotor's built-in JSON readers/writers

```python
from pykotor.resource.formats.gff import read_gff, write_gff
from pykotor.resource.type import ResourceType

# Read JSON
gff = read_gff("file.utc.json", file_format=ResourceType.GFF_JSON)

# Write binary
write_gff(gff, "file.utc", file_format=ResourceType.GFF)
```

**Benefits**:
- Proper type handling
- Maintains GFF structure integrity
- Handles LocalizedStrings correctly
- Auto-detects format

**Vendor References**:
- `vendor/xoreos-tools/src/aurora/gff3file.cpp` - Binary GFF format
- `vendor/KotOR.js/src/formats/gff/GFFObject.ts` - GFF object model
- `vendor/Kotor.NET/Kotor.NET/GFF/` - C# GFF implementation

### 3. Comprehensive Resource Type System

**Initial Implementation**: Manual extension mapping
**Current Implementation**: Uses `ResourceType` enum with `.is_gff()` method

```python
from pykotor.resource.type import ResourceType

restype = ResourceType.from_extension("utc")
if restype.is_gff():
    # Convert to JSON
    gff = read_gff(data)
    write_gff(gff, output, file_format=ResourceType.GFF_JSON)
```

**Benefits**:
- Automatic GFF detection
- Comprehensive type coverage
- Extension↔ResourceType mapping
- Type-aware operations

### 4. ERF/Module Handling

**Initial Implementation**: Basic ERF reading
**Current Implementation**: Full ERF/MOD/SAV/HAK support with proper typing

```python
from pykotor.resource.formats.erf import read_erf, write_erf, ERF, ERFType

# Read any ERF-type file
archive = read_erf("module.mod")

# Create new ERF
erf = ERF()
erf.erf_type = ERFType.MOD
erf.set("script", ResourceType.NCS, script_bytes)
write_erf(erf, "output.mod")
```

**Benefits**:
- Proper ERF type handling (MOD/ERF/SAV/HAK)
- Resource deduplication
- Metadata preservation
- Streaming for large files

**Vendor References**:
- `vendor/xoreos-tools/src/aurora/erffile.cpp` - ERF format spec
- `vendor/KotOR.js/src/resource/ERFObject.ts` - ERF operations
- `vendor/reone/src/libs/resource/format/erfreader.cpp` - Engine ERF reader

## Complete PyKotor Module Usage

### GFF Module (`pykotor.resource.formats.gff`)

**Files Used**:
- `gff_auto.py` - `read_gff()`, `write_gff()`, `detect_gff()`
- `io_gff.py` - `GFFBinaryReader`, `GFFBinaryWriter`
- `io_gff_json.py` - `GFFJSONReader`, `GFFJSONWriter`
- `gff_data.py` - `GFF`, `GFFStruct`, `GFFList`, `GFFFieldType`

**Used In**: `convert.py`, `unpack.py`

**Vendor References**:
```python
# vendor/xoreos-tools/src/aurora/gff3file.cpp:45
# GFF v3.2 format specification

# vendor/KotOR.js/src/formats/gff/GFFObject.ts:120
# JSON serialization format

# vendor/Kotor.NET/Kotor.NET/GFF/GFF.cs:87
# Field type handling
```

### ERF Module (`pykotor.resource.formats.erf`)

**Files Used**:
- `erf_auto.py` - `read_erf()`, `write_erf()`, `detect_erf()`
- `io_erf.py` - `ERFBinaryReader`, `ERFBinaryWriter`
- `erf_data.py` - `ERF`, `ERFResource`, `ERFType`

**Used In**: `pack.py`, `unpack.py`

**Vendor References**:
```python
# vendor/xoreos-tools/src/aurora/erffile.cpp:102
# ERF file format

# vendor/KotOR.js/src/resource/ERFObject.ts:45
# ERF resource handling

# vendor/reone/src/libs/resource/format/erfreader.cpp:67
# Module-specific ERF handling
```

### RIM Module (`pykotor.resource.formats.rim`)

**Files Used**:
- `rim_auto.py` - `read_rim()`, `write_rim()`
- `io_rim.py` - `RIMBinaryReader`, `RIMBinaryWriter`
- `rim_data.py` - `RIM`, `RIMResource`

**Used In**: `unpack.py`

**Vendor References**:
```python
# vendor/xoreos-tools/src/aurora/rimfile.cpp:55
# RIM file format

# vendor/KotOR.js/src/resource/RIMObject.ts:32
# RIM operations
```

### NCS Module (`pykotor.resource.formats.ncs`)

**Files Used**:
- `compilers.py` - `InbuiltNCSCompiler`, `ExternalNCSCompiler`
- `ncs_auto.py` - `compile_nss()`, `write_ncs()`
- `compiler/parser.py` - NSS parser
- `compiler/lexer.py` - NSS lexer
- `compiler/classes.py` - AST classes

**Used In**: `compile.py`

**Vendor References**:
```python
# vendor/KotOR.js/src/nwscript/NWScriptCompiler.ts:234
# NSS compilation process

# vendor/xoreos-tools/src/nwscript/compiler.cpp:89
# Compiler architecture

# vendor/xoreos-docs/specs/torlack/ncs.html
# NCS bytecode format
```

### Resource Type Module (`pykotor.resource.type`)

**Files Used**:
- `type.py` - `ResourceType` enum and conversion methods

**Used In**: All commands

**Features**:
- `.from_extension()` - Get ResourceType from file extension
- `.is_gff()` - Check if resource is GFF-based
- `.extension` - Get file extension for type
- Comprehensive type coverage (200+ types)

## Vendor Code Integration Points

### 1. GFF Format (Most Referenced)

**Primary References**:
1. **xoreos-tools** (`vendor/xoreos-tools/src/aurora/gff3file.cpp`)
   - Binary format specification
   - Field type definitions
   - Struct/list handling

2. **KotOR.js** (`vendor/KotOR.js/src/formats/gff/GFFObject.ts`)
   - Object model design
   - JSON serialization
   - Type conversion

3. **Kotor.NET** (`vendor/Kotor.NET/Kotor.NET/GFF/`)
   - C# implementation patterns
   - Field accessors
   - Type safety

**Usage in KOTORNasher**:
- `convert.py`: JSON → GFF conversion
- `unpack.py`: GFF → JSON conversion
- Both use PyKotor's implementations, vendor for reference

### 2. ERF Format

**Primary References**:
1. **xoreos-tools** (`vendor/xoreos-tools/src/aurora/erffile.cpp`)
   - File format structure
   - Resource table layout
   - Compression handling

2. **KotOR.js** (`vendor/KotOR.js/src/resource/ERFObject.ts`)
   - Resource management
   - Type detection
   - Memory efficiency

3. **reone** (`vendor/reone/src/libs/resource/format/erfreader.cpp`)
   - Engine-level handling
   - Performance patterns
   - Edge cases

**Usage in KOTORNasher**:
- `pack.py`: Creating ERF/MOD/HAK files
- `unpack.py`: Reading ERF/MOD/HAK files

### 3. NWScript Compilation

**Primary References**:
1. **KotOR.js** (`vendor/KotOR.js/src/nwscript/NWScriptCompiler.ts`)
   - Parser implementation
   - AST construction
   - Code generation

2. **xoreos-tools** (`vendor/xoreos-tools/src/nwscript/compiler.cpp`)
   - Lexer/parser architecture
   - Optimization passes
   - Error handling

3. **xoreos-docs** (`vendor/xoreos-docs/specs/torlack/ncs.html`)
   - NCS bytecode specification
   - Instruction set
   - Stack operations

**Usage in KOTORNasher**:
- `compile.py`: Uses PyKotor's InbuiltNCSCompiler
- Fallback to external compiler if available

## Configuration and Best Practices

### 1. Prefer PyKotor's Built-in Implementations

**Do**:
```python
from pykotor.resource.formats.gff import read_gff, write_gff

gff = read_gff(source, file_format=ResourceType.GFF_JSON)
write_gff(gff, target, file_format=ResourceType.GFF)
```

**Don't**:
```python
import json
# Manual JSON parsing - loses type information
```

### 2. Use ResourceType for Type Safety

**Do**:
```python
from pykotor.resource.type import ResourceType

restype = ResourceType.from_extension(ext)
if restype.is_gff():
    # Handle GFF files
```

**Don't**:
```python
if ext in (".utc", ".uti", ".utp", ...):  # Incomplete
    # Manual type checking
```

### 3. Leverage Built-in Compiler

**Do**:
```python
from pykotor.resource.formats.ncs.compilers import InbuiltNCSCompiler

compiler = InbuiltNCSCompiler()
compiler.compile_script(source, output, game)
```

**Don't**:
```python
subprocess.run(["nwnnsscomp", source])  # Requires external tool
```

### 4. Use Type-Aware ERF Operations

**Do**:
```python
from pykotor.resource.formats.erf import ERF, ERFType

erf = ERF()
erf.erf_type = ERFType.MOD  # Proper typing
```

**Don't**:
```python
# Manual binary construction
```

## Testing Strategy

### 1. Test with PyKotor's Test Suite

```bash
# Run PyKotor's GFF tests
cd Libraries/PyKotor
pytest tests/resource/formats/test_gff.py

# Run PyKotor's ERF tests
pytest tests/resource/formats/test_erf.py
```

### 2. Test Built-in Compiler

```bash
# Test without external compiler
cd Tools/KOTORNasher
kotornasher compile --clean
# Should use InbuiltNCSCompiler
```

### 3. Validate Against Vendor Examples

```bash
# Compare output with vendor implementations
# Use files from vendor/Vanilla_KOTOR_Script_Source for testing
kotornasher unpack --file /path/to/module.mod
# Verify JSON matches vendor expectations
```

## Maintenance and Updates

### Keeping PyKotor Integration Current

1. **Monitor PyKotor Updates**
   - Watch for new features in PyKotor
   - Adopt improved APIs when available
   - Update vendor references as needed

2. **Vendor Code Accuracy**
   - Prioritize: reone, xoreos, KotOR.js, Kotor.NET
   - Question: Other vendor projects may be incomplete
   - Document: Any deviations or corrections

3. **Performance Optimization**
   - Profile compilation with both compilers
   - Monitor JSON conversion performance
   - Consider caching strategies

## Summary

KOTORNasher successfully leverages PyKotor's comprehensive KOTOR modding library while maintaining nasher's familiar syntax. Key achievements:

1. **100% PyKotor Integration** - All file operations use PyKotor
2. **Built-in Compiler** - No external tools required
3. **Vendor-Informed** - Implementation guided by multiple references
4. **Type-Safe** - Leverages PyKotor's resource type system
5. **nasher-Compatible** - Maintains familiar command syntax

This makes KOTORNasher a powerful, self-contained KOTOR modding tool with the ergonomics of nasher and the capabilities of PyKotor.



