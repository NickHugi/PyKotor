# KitGenerator

Extract kit resources from KOTOR module files (RIM/ERF) for use with the Holocron Toolset.

## Description

KitGenerator is a command-line tool that extracts kit resources (MDL, MDX, WOK, TGA, TXI, UTD files) from KOTOR module files and generates a kit structure that can be used by the Holocron Toolset.

## Features

- Supports both RIM and ERF file formats (`.rim`, `.erf`, `.mod`, `.hak`, `.sav`)
- Extracts components (room models with walkmeshes)
- Extracts textures and lightmaps with TXI metadata
- Extracts doors with automatic dimension calculation
- Generates minimap images from walkmeshes
- Extracts doorhook positions from walkmesh transitions
- Interactive CLI with helpful prompts
- Comprehensive logging

## Installation

KitGenerator is part of the PyKotor project. To use it:

1. Clone the PyKotor repository
2. Install dependencies (see main README)
3. Run from the Tools/KitGenerator directory

## Usage

### Interactive Mode

Simply run the tool without arguments for interactive prompts:

```bash
python -m kitgenerator
```

### Command-Line Arguments

You can also provide arguments directly:

```bash
python -m kitgenerator --installation "C:\Program Files (x86)\Steam\steamapps\common\swkotor" --module danm13 --output ./output --kit-id jedienclave
```

### Arguments

- `--installation`: Path to KOTOR installation directory
- `--module`: Module name (e.g., `danm13`). Extension and path will be automatically stripped
- `--output`: Output directory for the generated kit
- `--kit-id`: Kit identifier (defaults to module name)
- `--log-level`: Logging level (`debug`, `info`, `warning`, `error`, `critical`)

## Examples

### Extract from RIM files

```bash
python -m kitgenerator --module danm13
```

This will search for `danm13.rim` and `danm13_s.rim` in the installation's modules directory.

### Extract from ERF file

```bash
python -m kitgenerator --module mymodule.mod
```

This will search for `mymodule.mod` in the installation's modules directory.

### Extract with custom kit ID

```bash
python -m kitgenerator --module danm13 --kit-id jedienclave
```

## Output Structure

The generated kit will have the following structure:

```
output/
├── {kit_id}/
│   ├── {component_id}.mdl
│   ├── {component_id}.mdx
│   ├── {component_id}.wok
│   ├── {component_id}.png
│   ├── textures/
│   │   ├── {texture_name}.tga
│   │   └── {texture_name}.txi
│   ├── lightmaps/
│   │   ├── {lightmap_name}.tga
│   │   └── {lightmap_name}.txi
│   ├── doors/
│   │   ├── {door_name}_k1.utd
│   │   └── {door_name}_k2.utd
│   └── skyboxes/
│       ├── {skybox_name}.mdl
│       └── {skybox_name}.mdx
└── {kit_id}.json
```

## References

- [Kit Structure Documentation](../../wiki/Kit-Structure-Documentation.md)
- [Holocron Toolset](../../Tools/HolocronToolset)
- [PyKotor Libraries](../../Libraries/PyKotor)

## License

LGPL-3.0-or-later

