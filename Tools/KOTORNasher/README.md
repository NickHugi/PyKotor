# KOTORNasher

A build tool for KOTOR projects with nasher-compatible syntax.

## Overview

KOTORNasher is a command-line tool for converting KOTOR modules, ERFs, and haks between binary and text-based source files. This allows git-based version control and team collaboration for KOTOR modding projects.

**Built on PyKotor** - KOTORNasher leverages PyKotor's comprehensive KOTOR file format libraries, providing native support for all KOTOR formats without external dependencies.

### Features

- **nasher-compatible syntax** - Uses the same command structure as nasher for familiarity
- **Git-friendly workflow** - Convert binary KOTOR files to JSON for version control
- **Built-in NSS compiler** - Compile scripts without external dependencies using PyKotor's native compiler
- **Fast** - Built on PyKotor's high-performance libraries
- **Multiple targets** - Support for modules, ERFs, haks, and more
- **Flexible source trees** - Organize your source files however you want
- **Pure Python** - No external tool dependencies required (nwnnsscomp optional)

## Installation

### From Source

```bash
cd Tools/KOTORNasher
pip install -e .
```

### Requirements

- Python 3.8+
- PyKotor library (automatically installed)
- nwnnsscomp (optional - falls back to built-in compiler)

## Quick Start

### 1. Initialize a new project

```bash
kotornasher init myproject
cd myproject
```

### 2. Unpack an existing module

```bash
kotornasher unpack --file path/to/mymodule.mod
```

### 3. Edit source files

Edit the files in the `src/` directory as needed.

### 4. Pack and install

```bash
kotornasher install
```

## PyKotor Integration

KOTORNasher is built on PyKotor and uses the following modules:

- **GFF/JSON Conversion**: `pykotor.resource.formats.gff` - Reads/writes GFF files in binary and JSON format
- **ERF/Module Handling**: `pykotor.resource.formats.erf` - Reads/writes ERF, MOD, SAV files
- **RIM Handling**: `pykotor.resource.formats.rim` - Reads/writes RIM files
- **NSS Compilation**: `pykotor.resource.formats.ncs.compilers` - Built-in NWScript compiler
- **Resource Types**: `pykotor.resource.type` - KOTOR resource type system

### Vendor Code References

KOTORNasher's implementation is informed by code from PyKotor's vendor directory:

- **xoreos-tools** (`vendor/xoreos-tools/`) - C++ reference for GFF, ERF, and NSS formats
- **KotOR.js** (`vendor/KotOR.js/`) - TypeScript reference for all KOTOR formats
- **Kotor.NET** (`vendor/Kotor.NET/`) - C# reference implementations
- **reone** (`vendor/reone/`) - Comprehensive C++ engine reimplementation

## Commands

### config

Get, set, or unset user-defined configuration options.

```bash
kotornasher config <key> [<value>]
kotornasher config --list
kotornasher config --global nssCompiler /path/to/nwnnsscomp
```

### init

Create a new kotornasher package.

```bash
kotornasher init [dir] [file]
kotornasher init myproject
kotornasher init myproject --file mymodule.mod
```

### list

List all targets defined in kotornasher.cfg.

```bash
kotornasher list
kotornasher list [target]
kotornasher list --verbose
```

### unpack

Unpack a file into the project source tree.

```bash
kotornasher unpack [target] [file]
kotornasher unpack
kotornasher unpack --file mymodule.mod
```

### convert

Convert all JSON sources to their GFF counterparts.

```bash
kotornasher convert [targets...]
kotornasher convert
kotornasher convert all
kotornasher convert demo test
```

### compile

Compile all NWScript sources for target.

**Note**: Uses PyKotor's built-in compiler by default. External compiler (nwnnsscomp) used if found in PATH.

```bash
kotornasher compile [targets...]
kotornasher compile
kotornasher compile --file myscript.nss
```

### pack

Convert, compile, and pack all sources for target.

```bash
kotornasher pack [targets...]
kotornasher pack
kotornasher pack all
kotornasher pack demo --clean
```

### install

Convert, compile, pack, and install target.

```bash
kotornasher install [targets...]
kotornasher install
kotornasher install demo
kotornasher install --installDir /path/to/kotor
```

### launch

Convert, compile, pack, install, and launch target in-game.

```bash
kotornasher launch [target]
kotornasher serve [target]
kotornasher play [target]
kotornasher test [target]
```

## Configuration File

The `kotornasher.cfg` file uses TOML format and is compatible with nasher's syntax.

### Example Configuration

```toml
[package]
name = "My KOTOR Mod"
description = "An awesome mod"
version = "1.0.0"
author = "Your Name <your.email@example.com>"

  [package.sources]
  include = "src/**/*.{nss,json,ncs}"
  exclude = "**/test_*.nss"

  [package.rules]
  "*.nss" = "src/scripts"
  "*.ncs" = "src/scripts"
  "*.utc" = "src/blueprints/creatures"
  "*" = "src"

[target]
name = "default"
file = "mymod.mod"
description = "Default module target"
```

## Differences from nasher

While KOTORNasher maintains nasher's command syntax for familiarity, it has key differences:

1. **Built on PyKotor** - Uses PyKotor's native Python libraries instead of neverwinter.nim
2. **Built-in Compiler** - Includes a native NSS compiler, no external tools required
3. **KOTOR-specific** - Targets KOTOR/KOTOR2 instead of Neverwinter Nights
4. **Python ecosystem** - Easier to extend and integrate with Python tools

## License

MIT License - See LICENSE file for details.

## Credits

- **Syntax inspired by**: [nasher](https://github.com/squattingmonk/nasher) by squattingmonk
- **Built on**: [PyKotor](https://github.com/NickHugi/PyKotor)
- **Format references**: xoreos-tools, KotOR.js, reone, Kotor.NET (in vendor/)

## Contributing

Contributions welcome! Please see the main PyKotor repository for contribution guidelines.

## Documentation

- [QUICKSTART.md](QUICKSTART.md) - 5-minute tutorial
- [IMPLEMENTATION_NOTES.md](IMPLEMENTATION_NOTES.md) - Technical details
- [CHANGELOG.md](CHANGELOG.md) - Version history
