# KotorDiff INI Generator

## Overview

The KotorDiff INI Generator is a comprehensive system for automatically generating TSLPatcher-compatible `changes.ini` files from game file differences. This allows modders to easily create installers for their mods by comparing modified game files against the originals.

## Features

### Supported File Types

The INI generator supports all major KOTOR/TSL file formats:

- **2DA Files**: Detects and generates patches for:
  - Row additions
  - Row modifications  
  - Column additions
  - Cell value changes

- **GFF Files** (UTC, UTI, UTP, UTE, UTM, UTD, UTW, DLG, ARE, GIT, IFO, GUI, etc.):
  - Field modifications
  - Field additions
  - Nested struct changes
  - List modifications

- **TLK Files**:
  - Entry modifications (replacements)
  - Entry additions (appends)
  - Text and voiceover changes

- **SSF Files**:
  - Sound slot modifications

## Usage

### Command Line Interface

#### Basic Three-Way Diff with INI Generation

```bash
python -m kotordiff --older path/to/original --yours path/to/modified --use-new-generator
```

This will:
1. Compare the original files against your modified files
2. Generate a unified diff output
3. Create a `changes.ini` file describing all differences

#### Specify Output Location

```bash
python -m kotordiff --older original/ --yours modified/ --out-ini my_mod/tslpatchdata/changes.ini --use-new-generator
```

#### Two-Way Diff (Experimental)

```bash
python -m kotordiff --path1 original/ --path2 modified/ --generate-ini --use-new-generator
```

### Python API

```python
from pathlib import Path
from kotordiff.ini_generator import ChangesINIWriter
from kotordiff.structured_diff import StructuredDiffEngine
from kotordiff.diff_analyzers import DiffAnalyzerFactory

# Initialize components
ini_writer = ChangesINIWriter()
diff_engine = StructuredDiffEngine()

# Compare 2DA files
left_data = Path("original/appearance.2da").read_bytes()
right_data = Path("modified/appearance.2da").read_bytes()

diff_result = diff_engine.compare_2da(left_data, right_data, "appearance.2da", "appearance.2da")

# Add to INI writer
ini_writer.add_diff_result(diff_result, "2da")

# Generate INI file
ini_writer.write_to_file(Path("tslpatchdata/changes.ini"))
```

### Advanced Usage: Direct Analyzer Access

```python
from kotordiff.diff_analyzers import TwoDADiffAnalyzer

# Create analyzer
analyzer = TwoDADiffAnalyzer()

# Analyze differences
modifications = analyzer.analyze(left_data, right_data, "appearance.2da")

# Access modification objects directly
for modifier in modifications.modifiers:
    print(f"Modifier: {modifier}")
```

## Architecture

### Components

1. **Structured Diff Engine** (`structured_diff.py`)
   - Performs deep comparison of game files
   - Returns structured diff results with detailed change information
   - Handles complex nested structures (GFF lists/structs)

2. **Diff Analyzers** (`diff_analyzers.py`)
   - Converts diff results into TSLPatcher modification objects
   - One analyzer per file type (2DA, GFF, TLK, SSF)
   - Generates proper `PatcherModifications` objects

3. **INI Generators** (`ini_generator.py`)
   - Converts structured diffs into INI format
   - One generator per file type
   - Handles TSLPatcher-specific syntax and conventions

4. **ChangesINIWriter** (`ini_generator.py`)
   - Orchestrates the generation process
   - Manages multiple file types
   - Writes final `changes.ini` file

### Data Flow

```
Original Files + Modified Files
        ↓
Structured Diff Engine
        ↓
DiffResult objects (TwoDADiffResult, GFFDiffResult, etc.)
        ↓
INI Generators
        ↓
INI Sections
        ↓
ChangesINIWriter
        ↓
changes.ini file
```

## Examples

### Example 1: Simple 2DA Modification

**Input**: Modified `appearance.2da` with one changed cell

**Command**:
```bash
python -m kotordiff --older kotor/appearance.2da --yours modified/appearance.2da --use-new-generator
```

**Generated INI**:
```ini
[appearance.2da]
ChangeRow0=change_row_5

[change_row_5]
RowIndex=5
modelb=P_BastilaBB01
```

### Example 2: GFF Field Addition

**Input**: Modified `module.ifo` with new field

**Generated INI**:
```ini
[module.ifo]
AddField0=add_NewField

[add_NewField]
FieldType=Int
Path=
Label=NewField
Value=123
```

### Example 3: TLK Entry Modifications

**Input**: Modified dialog.tlk with changed entries

**Generated INI**:
```ini
[TLKList]
StrRef0=0
StrRef1=1

[replace.tlk]
100=0
250=1
```

## Comparison with Legacy Generator

The new structured INI generator offers several improvements over the legacy implementation:

### Advantages

1. **Comprehensive Coverage**: Handles all file types uniformly
2. **Type-Safe**: Uses proper type annotations and structured objects
3. **Extensible**: Easy to add new file type support
4. **Testable**: Comprehensive unit tests for all components
5. **Accurate**: Uses PyKotor's native comparison methods
6. **Maintainable**: Clean separation of concerns

### Using the New Generator

By default, KotorDiff uses the legacy generator for backward compatibility. To use the new structured generator, add the `--use-new-generator` flag:

```bash
python -m kotordiff --older original/ --yours modified/ --use-new-generator
```

## Testing

The INI generator includes comprehensive tests in `tests/tslpatcher/diff/test_ini_generator.py`:

```bash
# Run INI generator tests
python -m pytest tests/tslpatcher/diff/test_ini_generator.py -v

# Run specific test
python -m pytest tests/tslpatcher/diff/test_ini_generator.py::TestTwoDAINIGenerator::test_generate_row_change -v
```

## Limitations and Future Work

### Current Limitations

1. **GFF Lists**: Complex list modifications may not be fully captured
2. **NSS/NCS**: Script patching not yet implemented
3. **Binary Files**: TGA, TPC, MDL, etc. are not supported (copy/replace only)
4. **Namespace Support**: Multiple namespaces in one INI not yet supported

### Planned Enhancements

1. Add support for NSS script modifications
2. Improve GFF list handling with proper AddStructToListGFF generation
3. Add support for CompileList sections
4. Add support for HackList sections
5. Generate install.ini metadata
6. Generate namespace.ini for multi-namespace mods

## Troubleshooting

### Issue: Generated INI doesn't apply changes

**Solution**: Ensure you're using the correct file paths and that the original files match what's in the target installation.

### Issue: "No differences detected"

**Solution**: Verify that files are actually different. The generator only creates sections for files that have changed.

### Issue: Linter errors

**Solution**: Run type checking to identify issues:
```bash
python -m mypy Tools/KotorDiff/src/kotordiff/
```

## Contributing

To contribute to the INI generator:

1. Add tests in `tests/tslpatcher/diff/test_ini_generator.py`
2. Ensure all tests pass: `pytest tests/tslpatcher/diff/`
3. Run linting: `ruff check Tools/KotorDiff/src/kotordiff/`
4. Submit a pull request

## API Reference

### StructuredDiffEngine

```python
class StructuredDiffEngine:
    def compare_2da(left_data: bytes, right_data: bytes, left_id: str, right_id: str) -> TwoDADiffResult
    def compare_gff(left_data: bytes, right_data: bytes, left_id: str, right_id: str) -> GFFDiffResult
    def compare_tlk(left_data: bytes, right_data: bytes, left_id: str, right_id: str) -> TLKDiffResult
```

### DiffAnalyzerFactory

```python
class DiffAnalyzerFactory:
    @staticmethod
    def get_analyzer(resource_type: str) -> DiffAnalyzer | None
```

### ChangesINIWriter

```python
class ChangesINIWriter:
    def __init__(self)
    def add_diff_result(diff_result: DiffResult[Any], resource_type: str)
    def write_to_file(output_path: Path)
    def write_to_string() -> str
```

## License

This project is part of PyKotor and follows the same license terms.

## Credits

- **Original TSLPatcher**: stoffe, with updates by many contributors
- **PyKotor**: Library providing KOTOR file format support
- **KotorDiff INI Generator**: Built on PyKotor's TSLPatcher implementation




