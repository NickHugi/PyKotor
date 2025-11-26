# Kit Structure Documentation

Kits are collections of reusable indoor map components for the Holocron Toolset. They contain room models, textures, lightmaps, doors, and other resources that can be assembled into complete game modules.

## Table of Contents

- [Kit Structure Documentation](#kit-structure-documentation)
  - [Table of Contents](#table-of-contents)
  - [Kit Overview](#kit-overview)
  - [Kit Directory Structure](#kit-directory-structure)
  - [Kit JSON File](#kit-json-file)
  - [Components](#components)
  - [Textures and Lightmaps](#textures-and-lightmaps)
  - [Always Folder](#always-folder)
  - [Doors](#doors)
  - [Skyboxes](#skyboxes)
  - [Doorway Padding](#doorway-padding)
  - [Resource Extraction](#resource-extraction)
  - [Implementation Details](#implementation-details)

---

## Kit Overview

A kit is a self-contained collection of resources that can be used to build indoor maps. Kits are stored in `Tools/HolocronToolset/src/toolset/kits/kits/` and consist of:

- **Components**: Room models (MDL/MDX/WOK) with hook points for connecting to other rooms
- **Textures**: TGA/TPC texture files with optional TXI metadata
- **Lightmaps**: TGA/TPC lightmap files with optional TXI metadata
- **Doors**: UTD door templates (K1 and K2 versions)
- **Skyboxes**: Optional MDL/MDX models for sky rendering
- **Always Resources**: Static resources included in every generated module

**Reference**: [`Tools/HolocronToolset/src/toolset/data/indoorkit/`](https://github.com/th3w1zard1/PyKotor/tree/master/Tools/HolocronToolset/src/toolset/data/indoorkit)

---

## Kit Directory Structure

```
kits/
├── {kit_id}/
│   ├── {kit_id}.json          # Kit definition file
│   ├── {component_id}.mdl     # Component model files
│   ├── {component_id}.mdx
│   ├── {component_id}.wok
│   ├── {component_id}.png     # Component minimap image
│   ├── textures/              # Texture files
│   │   ├── {texture_name}.tga
│   │   └── {texture_name}.txi
│   ├── lightmaps/             # Lightmap files
│   │   ├── {lightmap_name}.tga
│   │   └── {lightmap_name}.txi
│   ├── always/                # Always-included resources (optional)
│   │   └── {resource_name}.{ext}
│   ├── skyboxes/              # Skybox models (optional)
│   │   ├── {skybox_name}.mdl
│   │   └── {skybox_name}.mdx
│   ├── doorway/               # Door padding models (optional)
│   │   ├── {side|top}_{door_id}_size{size}.mdl
│   │   └── {side|top}_{door_id}_size{size}.mdx
│   └── {door_name}_k1.utd     # Door templates
│   └── {door_name}_k2.utd
```

**Example**: `jedienclave/` contains textures and lightmaps but no components (texture-only kit). `enclavesurface/` contains full components with models, walkmeshes, and minimaps.

---

## Kit JSON File

The kit JSON file (`{kit_id}.json`) defines the kit structure:

```json
{
    "name": "Kit Display Name",
    "id": "kitid",
    "ht": "2.0.2",
    "version": 1,
    "components": [
        {
            "name": "Component Name",
            "id": "component_id",
            "native": 1,
            "doorhooks": [
                {
                    "x": 0.0,
                    "y": 0.0,
                    "z": 0.0,
                    "rotation": 90.0,
                    "door": 0,
                    "edge": 20
                }
            ]
        }
    ],
    "doors": [
        {
            "utd_k1": "door_name_k1",
            "utd_k2": "door_name_k2",
            "width": 2.0,
            "height": 3.0
        }
    ]
}
```

**Fields**:
- `name`: Display name for the kit
- `id`: Unique kit identifier (matches folder name)
- `ht`: Holocron Toolset version compatibility
- `version`: Kit version number
- `components`: List of room components (can be empty for texture-only kits)
- `doors`: List of door definitions

**Reference**: [`Tools/HolocronToolset/src/toolset/data/indoorkit/indoorkit_loader.py:23-135`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/indoorkit/indoorkit_loader.py#L23-L135)

---

## Components

Components are reusable room models that can be placed and connected to build indoor maps.

**Component Files**:
- `{component_id}.mdl`: 3D model geometry
- `{component_id}.mdx`: Material/lightmap index data
- `{component_id}.wok`: Walkmesh for pathfinding
- `{component_id}.png`: Minimap image (top-down view)

**Component JSON Structure**:
```json
{
    "name": "Hall 1",
    "id": "hall_1",
    "native": 1,
    "doorhooks": [
        {
            "x": -4.476789474487305,
            "y": -17.959964752197266,
            "z": 3.8257503509521484,
            "rotation": 90.0,
            "door": 0,
            "edge": 25
        }
    ]
}
```

**Door Hooks**:
- `x`, `y`, `z`: World-space position of the hook point
- `rotation`: Rotation angle in degrees (0-360)
- `door`: Index into the kit's `doors` array
- `edge`: Edge index on the walkmesh where the door connects

**Hook Connection Logic**: Components are connected when their hook points are within proximity. The toolset automatically links compatible hooks to form room connections.

**Reference**: [`Tools/HolocronToolset/src/toolset/data/indoorkit/indoorkit_base.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/indoorkit/indoorkit_base.py)

---

## Textures and Lightmaps

Kits contain all textures and lightmaps referenced by their component models, plus any additional shared resources.

### Texture Extraction

Textures are extracted from:
1. **RIM Files**: Module-specific textures in `.rim` files
2. **Installation**: Shared textures from:
   - `texturepacks/` (TPA/ERF files)
   - `textures_gui/` (GUI textures)
   - `chitin/` (Base game BIF files)

**Texture Naming**:
- Textures: Standard names (e.g., `lda_wall02`, `i_datapad`)
- Lightmaps: Suffixed with `_lm` or prefixed with `l_` (e.g., `m13aa_01a_lm0`, `l_sky01`)

**TXI Files**: Each texture/lightmap can have an accompanying `.txi` file containing texture metadata (filtering, wrapping, etc.). TXI files are extracted from:
- Embedded TXI data in TPC files
- Standalone TXI files in the installation
- Default TXI if none found

**Reference**: [`Tools/HolocronToolset/src/toolset/gui/windows/main.py:1636-1734`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/windows/main.py#L1636-L1734)

### Shared Resources

Some kits include textures/lightmaps from **other modules** that are not directly referenced by the kit's own models. These are typically:

- **Shared Lightmaps**: Lightmaps from other modules stored in `lightmaps3.bif` (CHITIN) that may be used by multiple areas
  - Example: `m03af_01a_lm13`, `m10aa_01a_lm13`, `m14ab_02a_lm13` from `jedienclave` kit
  - These are found in `data/lightmaps3.bif` as shared resources across multiple modules
  - They may be referenced by other modules that share resources with the kit's source module
- **Common Textures**: Textures from `swpc_tex_tpa.erf` (texture packs) used across multiple modules
  - Example: `lda_*` textures (lda_bark04, lda_flr07, etc.) from texture packs
  - These are shared resources that may be used by multiple areas
- **Manual Additions**: Resources manually included for convenience or compatibility
  - Some resources may be included even if not directly referenced
  - These ensure the kit is self-contained and doesn't depend on external resources

**Investigation Results**: Analysis of the `jedienclave` kit shows:
- **13 lightmaps** from other modules (m03af, m03mg, m10aa, m10ac, m14ab, m15aa, m22aa, m22ab, m28ab, m33ab, m36aa, m44ab) are NOT referenced by `danm13` models
- These lightmaps are stored in `lightmaps3.bif` (CHITIN) as shared resources
- **4 textures** are not referenced by `danm13` models (i_datapad, lda_flr07, lda_flr08, h_f_lo01headtest)
- Most `lda_*` textures ARE referenced by `danm13` models (lda_bark04, lda_flr11, lda_grass07, etc.)

**Why Include Shared Resources?**:
- **Self-Containment**: Ensures the kit has all resources it might need
- **Compatibility**: Some resources may be referenced indirectly or by other systems
- **Convenience**: Manually curated collections of commonly used resources
- **Future-Proofing**: Resources that might be needed when the kit is used in different contexts

**Reference**: Investigation using `Installation.locations()` shows these resources are found in:
- `data/lightmaps3.bif` (CHITIN) for shared lightmaps
- `texturepacks/swpc_tex_tpa.erf` (TEXTURES_TPA) for common textures

---

## Always Folder

The `always/` folder contains resources that are **always included** in the generated module, regardless of which components are used.

**Purpose**:
- **Static Resources**: Resources that should be included in every generated module using the kit
- **Common Assets**: Shared textures, models, or other resources needed by all rooms
- **Override Resources**: Resources that override base game files and should be included in every room
- **Non-Component Resources**: Resources that don't belong to specific components but are needed for the kit to function

**Usage**: When a kit is used to generate a module, all files in the `always/` folder are automatically added to the mod's resource list via `add_static_resources()`. These resources are included in every room, even if they're not directly referenced by component models.

**Processing**: Resources in the `always/` folder are processed during indoor map generation:
1. Each file in `always/` is loaded into `kit.always[filename]`
2. When a room is processed, `add_static_resources()` extracts the resource name and type from the filename
3. The resource is added to the mod with `mod.set_data(resname, restype, data)`
4. This happens for every room, ensuring the resource is always available

**Example**: The `sithbase` kit includes:
- `CM_asith.tpc`: Common texture used across all rooms
- `lsi_floor01b.tpc`, `lsi_flr03b.tpc`, `lsi_flr04b.tpc`: Floor textures for all rooms
- `lsi_win01bmp.tpc`: Window texture used throughout the base

These are added to every room when using the sithbase kit, ensuring consistent appearance across all generated rooms.

**When to Use**:
- Resources that should be available in every room (e.g., common floor textures)
- Override resources that replace base game files
- Resources needed for kit functionality but not tied to specific components
- Shared assets that multiple components might reference

**Reference**: [`Tools/HolocronToolset/src/toolset/data/indoormap.py:221-241`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/indoormap.py#L221-L241)

---

## Doors

Doors are defined in the kit JSON and have corresponding UTD files:

**Door Files**:
- `{door_name}_k1.utd`: KotOR 1 door template
- `{door_name}_k2.utd`: KotOR 2 door template

**Door JSON Structure**:
```json
{
    "utd_k1": "door_name_k1",
    "utd_k2": "door_name_k2",
    "width": 2.0,
    "height": 3.0
}
```

**Door Properties**:
- `utd_k1`, `utd_k2`: ResRefs of UTD files (without `.utd` extension)
- `width`: Door width in world units
- `height`: Door height in world units

Doors are placed at component hook points and connect adjacent rooms. The door templates define appearance, locking, scripts, and other properties.

**Reference**: [`wiki/GFF-File-Format.md#utd-door`](GFF-File-Format#utd-door)

---

## Skyboxes

Skyboxes are optional MDL/MDX models used for outdoor area rendering. They are stored in the `skyboxes/` folder.

**Skybox Files**:
- `{skybox_name}.mdl`: Skybox model geometry
- `{skybox_name}.mdx`: Skybox material data

Skyboxes are typically used for outdoor areas and provide the distant sky/background rendering. They are loaded separately from room components and don't have walkmeshes.

---

## Doorway Padding

The `doorway/` folder contains padding models that fill gaps around doors:

**Padding Files**:
- `side_{door_id}_size{size}.mdl`: Side padding for horizontal doors
- `top_{door_id}_size{size}.mdl`: Top padding for vertical doors
- Corresponding `.mdx` files

**Padding Purpose**: When doors are inserted into walls, gaps may appear. Padding models fill these gaps to create seamless door transitions.

**Naming Convention**:
- `side_` or `top_`: Padding orientation
- `{door_id}`: Door identifier (matches door index in JSON)
- `size{size}`: Padding size in world units (e.g., `size650`, `size800`)

---

## Resource Extraction

When generating a kit from module RIM files, the extraction process:

1. **Loads Module Resources**: Uses `Module.all_resources()` to find all resources associated with the module
2. **Identifies Components**: Finds MDL files with corresponding WOK files (room models)
3. **Extracts Textures/Lightmaps**: 
   - Scans all MDL files for texture/lightmap references using `iterate_textures()` and `iterate_lightmaps()`
   - Locates resources using `Installation.locations()` with search order:
     - OVERRIDE (user mods)
     - TEXTURES_GUI (GUI textures)
     - TEXTURES_TPA (texture packs)
     - CHITIN (base game BIF files)
4. **Converts TPC to TGA**: Extracts TPC files and converts to TGA format
5. **Extracts TXI**: Finds TXI files for all textures/lightmaps (from TPC embedded data or standalone files)
6. **Extracts Doors**: Finds UTD files in the module
7. **Extracts Skyboxes**: Identifies MDL/MDX pairs without WOK files (likely skyboxes)

**Search Order**: The extraction follows the same search order as the game engine, ensuring resources are found in the correct priority order.

**Reference**: [`scripts/generate_kit_from_rim.py`](https://github.com/th3w1zard1/PyKotor/blob/master/scripts/generate_kit_from_rim.py)

---

## Implementation Details

### Kit Loading

Kits are loaded by `load_kits()` which:
1. Scans the kits directory for JSON files
2. Loads kit metadata from JSON
3. Loads textures/lightmaps from `textures/` and `lightmaps/` folders
4. Loads always resources from `always/` folder (if present)
5. Loads skyboxes from `skyboxes/` folder (if present)
6. Loads doorway padding from `doorway/` folder (if present)
7. Loads door UTD files
8. Loads component models (MDL/MDX/WOK) and minimap images (PNG)
9. Constructs `Kit` objects with `KitComponent` and `KitDoor` instances

**Reference**: [`Tools/HolocronToolset/src/toolset/data/indoorkit/indoorkit_loader.py:23-135`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/indoorkit/indoorkit_loader.py#L23-L135)

### Indoor Map Generation

When generating an indoor map from kits:
1. **Component Placement**: Components are placed at specified positions with rotations/flips
2. **Hook Connection**: Hook points are matched to connect adjacent rooms
3. **Model Transformation**: Models are flipped, rotated, and transformed based on room properties
4. **Texture/Lightmap Renaming**: Textures and lightmaps are renamed to module-specific names
5. **Walkmesh Merging**: Room walkmeshes are combined into a single area walkmesh
6. **Door Insertion**: Doors are inserted at hook points with appropriate padding
7. **Resource Generation**: ARE, GIT, LYT, VIS, IFO files are generated
8. **Minimap Generation**: Minimap images are generated from component PNGs

**Reference**: [`Tools/HolocronToolset/src/toolset/data/indoormap.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/indoormap.py)

### Coordinate System

- **World Coordinates**: Meters in left-handed coordinate system (X=right, Y=forward, Z=up)
- **Hook Positions**: World-space coordinates relative to component origin
- **Rotations**: Degrees (0-360), counterclockwise from positive X-axis
- **Transforms**: Components can be flipped on X/Y axes and rotated around Z-axis

**Reference**: [`wiki/BWM-File-Format.md`](BWM-File-Format) and [`wiki/LYT-File-Format.md`](LYT-File-Format)

---

## Kit Types

### Component-Based Kits

Kits with `components` array (e.g., `enclavesurface`, `endarspire`):
- Contain reusable room models
- Have hook points for connecting rooms
- Include textures/lightmaps referenced by components
- Generate complete indoor maps

### Texture-Only Kits

Kits with empty `components` array (e.g., `jedienclave`):
- Contain only textures and lightmaps
- May include shared resources from multiple modules
- Used for texture packs or shared resource collections
- Don't generate room layouts (no components to place)

---

## Best Practices

1. **Component Naming**: Use descriptive, consistent naming (e.g., `hall_1`, `junction_2`)
2. **Texture Organization**: Group related textures logically
3. **Always Folder**: Use sparingly for truly shared resources
4. **Door Definitions**: Ensure door UTD files match JSON definitions
5. **Hook Placement**: Place hooks at logical connection points
6. **Minimap Images**: Generate accurate top-down views for component selection

---

This documentation provides a comprehensive overview of the kit structure and how kits are used in the Holocron Toolset for generating indoor maps.
