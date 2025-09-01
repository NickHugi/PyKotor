# KOTOR Configuration Generator

This enhanced version of KotorDiff includes a powerful configuration generator for HoloPatcher, enabling automatic creation of `changes.ini` files from KOTOR installation differences.

## Features

### Enhanced KotorDiff CLI
- **All original KotorDiff functionality** - Compare KOTOR installations, directories, and files
- **Configuration generation** - Generate HoloPatcher-compatible `changes.ini` files
- **GUI interface** - User-friendly tkinter-based interface
- **Improved file format support** - Enhanced diffing for GFF, 2DA, TLK, SSF, and LIP files

### Configuration Generator
- **Automatic diff analysis** - Compares two KOTOR installations and identifies all changes
- **HoloPatcher compatibility** - Generates `changes.ini` files that work seamlessly with HoloPatcher
- **Multiple file format support** - Handles GFF, 2DA, TLK, SSF, and other KOTOR file formats
- **Text-based diffing** - Converts binary formats to text for accurate difference detection

### GUI Application
- **Easy-to-use interface** - Select directories and generate configurations with a few clicks
- **Real-time progress** - See the generation process as it happens
- **Output preview** - View generated configuration content before saving
- **Error handling** - Clear error messages and validation

## Usage

### Command Line Interface

#### Basic diff (original functionality):
```bash
python -m kotordiff --path1=/path/to/original/kotor --path2=/path/to/modified/kotor
```

#### Generate configuration file:
```bash
python -m kotordiff --path1=/path/to/original/kotor --path2=/path/to/modified/kotor --generate-config --config-output=changes.ini
```

#### Launch GUI:
```bash
python -m kotordiff --gui
```

#### All CLI options:
```bash
python -m kotordiff --help
```

### Python API

```python
from kotordiff.config_generator import ConfigurationGenerator
from pathlib import Path

# Create generator
generator = ConfigurationGenerator()

# Generate configuration
result = generator.generate_config(
    Path("/path/to/original/kotor"),
    Path("/path/to/modified/kotor"),
    Path("changes.ini")
)

print(f"Generated {len(result.splitlines())} lines")
```

### Individual Components

#### Using the Differ:
```python
from kotordiff.differ import KotorDiffer
from pathlib import Path

differ = KotorDiffer()
diff_result = differ.diff_installations(
    Path("/path/to/original"),
    Path("/path/to/modified")
)

print(f"Found {len(diff_result.changes)} changes")
for change in diff_result.changes:
    print(f"  {change.path} ({change.change_type})")
```

#### Using the INI Generator:
```python
from kotordiff.generators.changes_ini import ChangesIniGenerator
from kotordiff.differ import DiffResult, FileChange

# Create mock diff result
diff_result = DiffResult()
diff_result.add_change(FileChange(
    path="Override/test.utc",
    change_type="modified",
    resource_type="utc"
))

# Generate INI
generator = ChangesIniGenerator()
ini_content = generator.generate_from_diff(diff_result)
```

## Generated changes.ini Format

The generator creates HoloPatcher-compatible `changes.ini` files with the following sections:

### Settings Section
```ini
[Settings]
WindowCaption=Generated Mod Configuration
ConfirmMessage=This mod was generated from a KOTOR installation diff.
```

### Install List (for new files)
```ini
[InstallList]
File1=Override

[Override]
File1=newfile.uti
Replace1=modifiedfile.utc
```

### GFF List (for modified GFF files)
```ini
[GFFList]
File1=test.utc

[test.utc]
ModifyField1=FieldModification1
```

### 2DA List (for modified 2DA files)
```ini
[2DAList]
File1=test.2da

[test.2da]
ChangeRow1=RowModification1
```

### TLK List (for dialog.tlk changes)
```ini
[TLKList]
StrRef1=12345
Text1=New dialog text
```

### SSF List (for sound files)
```ini
[SSFList]
File1=sounds.ssf

[sounds.ssf]
SoundName=newsound
```

## File Format Support

The generator supports all major KOTOR file formats:

- **GFF formats** (.utc, .uti, .utp, .utd, .ute, .utm, .uts, .are, .git, .ifo, .dlg, .jrl, .fac, .itp, .ptm, .ptt)
- **2DA files** (.2da) - Tabular data files
- **TLK files** (.tlk) - Dialog/string files
- **SSF files** (.ssf) - Sound set files
- **LIP files** (.lip) - Lip sync files
- **Other files** - Hash-based comparison for unsupported formats

## Testing

Run the test suite:
```bash
python -m pytest kotordiff/test_config_generator.py -v
```

Run the integration test:
```bash
python integration_test.py
```

## Requirements

- Python 3.12+
- PyKotor library
- tkinter (for GUI - optional)
- Standard Python libraries (pathlib, difflib, etc.)

## Example Workflow

1. **Install a KOTOR mod manually** to create a modified installation
2. **Run the configuration generator** to compare original vs modified installations
3. **Get a changes.ini file** that can be distributed with your mod
4. **Users can install your mod** using HoloPatcher with the generated configuration

This eliminates the need to manually create TSLPatcher configurations, making mod development much faster and less error-prone.

## Architecture

### Core Components

- **KotorDiffer** - Analyzes differences between installations
- **ChangesIniGenerator** - Converts diff results to INI format
- **ConfigurationGenerator** - Main orchestrator class
- **GUI Application** - User-friendly interface
- **CLI Integration** - Command-line interface enhancements

### Text Conversion

The system converts binary KOTOR formats to text representations for accurate diffing:
- GFF files → Structured text representation
- 2DA files → Tab-separated values
- TLK files → String entries with metadata
- SSF files → Sound name mappings
- Binary files → Hash comparison

This approach ensures that even small changes in binary files are detected and properly converted to HoloPatcher instructions.