# KOTORNasher Quick Start Guide

## Installation

```bash
cd Tools/KOTORNasher
pip install -e .
```

## 5-Minute Tutorial

### 1. Create a new project

```bash
kotornasher init mymod
cd mymod
```

This creates:
- `kotornasher.cfg` - Configuration file
- `src/` - Source directory structure
- `.gitignore` - Git ignore file
- `.kotornasher/` - Local config directory

### 2. Unpack an existing module (optional)

```bash
kotornasher unpack --file ~/path/to/mymodule.mod
```

This extracts all files from the module into your `src/` directory, converting GFF files to JSON format.

### 3. View your targets

```bash
kotornasher list
```

Shows all configured targets in your `kotornasher.cfg`.

### 4. Make changes

Edit files in the `src/` directory:
- Scripts: `src/scripts/*.nss`
- Dialogs: `src/dialogs/*.dlg.json`
- Creatures: `src/blueprints/creatures/*.utc.json`
- Areas: `src/areas/*.git.json`, `*.are.json`
- etc.

### 5. Pack your module

```bash
kotornasher pack
```

This will:
1. Convert JSON files to GFF
2. Compile NWScript files
3. Pack everything into a module file

### 6. Install and test

```bash
kotornasher install
```

This installs the packed module to your KOTOR directory.

Or launch the game directly:

```bash
kotornasher play
```

## Common Workflows

### Starting from scratch

```bash
kotornasher init mynewmod
cd mynewmod
# Create/edit source files
kotornasher pack
```

### Working with an existing module

```bash
kotornasher init mynewmod
cd mynewmod
kotornasher unpack --file ~/modules/existing.mod
# Edit source files
kotornasher install
```

### Testing changes quickly

```bash
kotornasher play
```

This runs convert, compile, pack, install, and launches the game in one command.

### Building multiple targets

```toml
# In kotornasher.cfg
[target]
name = "demo"
file = "demo.mod"

[target]
name = "full"
file = "full.mod"
```

```bash
kotornasher pack all        # Build all targets
kotornasher pack demo       # Build specific target
kotornasher install full    # Install specific target
```

## Configuration

### Global settings

```bash
# Set script compiler path
kotornasher config --global nssCompiler /path/to/nwnnsscomp

# Set KOTOR install directory
kotornasher config --global installDir ~/Documents/KotOR

# List all settings
kotornasher config --list --global
```

### Local (per-project) settings

```bash
kotornasher config --local modName "My Awesome Mod"
kotornasher config --list --local
```

## Tips & Tricks

### Use version control

```bash
cd mymod
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/mymod
git push -u origin main
```

### Clean builds

```bash
kotornasher pack --clean
```

Clears the cache before building.

### Skip steps

```bash
kotornasher pack --noConvert    # Don't convert JSON
kotornasher pack --noCompile    # Don't compile scripts
kotornasher install --noPack    # Just install existing file
```

### Compile specific files

```bash
kotornasher compile --file myscript.nss
```

### Verbose output

```bash
kotornasher pack --verbose
kotornasher pack --debug
```

### Quiet mode

```bash
kotornasher pack --quiet
```

## Next Steps

- Read the [README.md](README.md) for full command documentation
- Check [IMPLEMENTATION_NOTES.md](IMPLEMENTATION_NOTES.md) for technical details
- See [kotornasher.cfg examples](https://github.com/squattingmonk/nasher#nashercfg) (nasher-compatible)

## Getting Help

```bash
kotornasher --help
kotornasher <command> --help
```

For issues or questions, visit the [PyKotor repository](https://github.com/NickHugi/PyKotor).



