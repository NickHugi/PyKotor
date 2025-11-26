# KotOR GFF File Format Documentation

This document provides a detailed description of the GFF (Generic File Format) used in Knights of the Old Republic (KotOR) games. GFF is a container format used for many different game resource types, including character templates, areas, dialogs, placeables, creatures, items, and more.

**For mod developers:** To modify GFF files in your mods, see the [TSLPatcher GFFList Syntax Guide](TSLPatcher-GFFList-Syntax). For general modding information, see [HoloPatcher README for Mod Developers](HoloPatcher-README-for-mod-developers.).

**Related formats:** GFF files often reference other formats such as [2DA files](2DA-File-Format) for configuration data, [TLK files](TLK-File-Format) for text strings, [MDL/MDX files](MDL-MDX-File-Format) for 3D models, and [NCS files](NCS-File-Format) for scripts.

## Table of Contents

- [KotOR GFF File Format Documentation](#kotor-gff-file-format-documentation)
  - [Table of Contents](#table-of-contents)
  - [File Structure Overview](#file-structure-overview)
    - [GFF as a Universal Container](#gff-as-a-universal-container)
  - [Binary Format](#binary-format)
    - [File Header](#file-header)
    - [Label Array](#label-array)
    - [Struct Array](#struct-array)
    - [Field Array](#field-array)
    - [Field Data](#field-data)
    - [Field Indices](#field-indices)
    - [List Indices](#list-indices)
  - [GFF Data Types](#gff-data-types)
  - [GFF Structure](#gff-structure)
    - [GFFStruct](#gffstruct)
    - [GFFField](#gfffield)
    - [GFFList](#gfflist)
  - [GFF Generic Types](#gff-generic-types)
    - [ARE (Area)](#are-area)
      - [Core Identity Fields](#core-identity-fields)
      - [Lighting \& Sun](#lighting--sun)
      - [Fog Settings](#fog-settings)
      - [Moon Lighting (Unused)](#moon-lighting-unused)
      - [Grass Rendering](#grass-rendering)
      - [Weather System (KotOR2)](#weather-system-kotor2)
      - [Dirty/Dust Settings (KotOR2)](#dirtydust-settings-kotor2)
      - [Environment \& Camera](#environment--camera)
      - [Area Behavior Flags](#area-behavior-flags)
      - [Skill Check Modifiers](#skill-check-modifiers)
      - [Script Hooks](#script-hooks)
      - [Rooms \& Minimap](#rooms--minimap)
      - [Implementation Notes](#implementation-notes)
    - [DLG (Dialogue)](#dlg-dialogue)
      - [Conversation Properties](#conversation-properties)
      - [Script Hooks](#script-hooks-1)
      - [Node Lists](#node-lists)
      - [DLGNode Structure (Entries \& Replies)](#dlgnode-structure-entries--replies)
      - [DLGLink Structure](#dlglink-structure)
      - [Implementation Notes](#implementation-notes-1)
    - [GIT (Game Instance Template)](#git-game-instance-template)
      - [Area Properties](#area-properties)
      - [Instance Lists](#instance-lists)
      - [GITCreature Instances](#gitcreature-instances)
      - [GITDoor Instances](#gitdoor-instances)
      - [GITPlaceable Instances](#gitplaceable-instances)
      - [GITTrigger Instances](#gittrigger-instances)
      - [GITWaypoint Instances](#gitwaypoint-instances)
      - [GITEncounter Instances](#gitencounter-instances)
      - [GITStore Instances](#gitstore-instances)
      - [GITSound Instances](#gitsound-instances)
      - [GITCamera Instances](#gitcamera-instances)
      - [Implementation Notes](#implementation-notes-2)
    - [GUI](#gui)
      - [Core Identity Fields](#core-identity-fields-1)
      - [Control Structure](#control-structure)
      - [Common Properties](#common-properties)
      - [Control-Specific Fields](#control-specific-fields)
      - [Implementation Notes](#implementation-notes-3)
    - [IFO (Module Info)](#ifo-module-info)
      - [Core Module Identity](#core-module-identity)
      - [Entry Configuration](#entry-configuration)
      - [Area List](#area-list)
      - [Expansion Pack Requirements](#expansion-pack-requirements)
      - [Starting Movie \& HAK Files](#starting-movie--hak-files)
      - [Cache \& XP Settings](#cache--xp-settings)
      - [DawnStar Property (Unused)](#dawnstar-property-unused)
      - [Module Script Hooks](#module-script-hooks)
      - [Implementation Notes](#implementation-notes-4)
    - [JRL (Journal)](#jrl-journal)
      - [Quest Structure](#quest-structure)
      - [Quest Category (JRLQuest)](#quest-category-jrlquest)
      - [Quest Entry (JRLEntry)](#quest-entry-jrlentry)
      - [Implementation Notes](#implementation-notes-5)
    - [PTH (Path)](#pth-path)
      - [Path Points](#path-points)
      - [Path Connections](#path-connections)
      - [Usage](#usage)
    - [UTC (Creature)](#utc-creature)
      - [Core Identity Fields](#core-identity-fields-2)
      - [Appearance \& Visuals](#appearance--visuals)
      - [Core Stats \& Attributes](#core-stats--attributes)
      - [Character Progression](#character-progression)
      - [Combat \& Behavior](#combat--behavior)
      - [Equipment \& Inventory](#equipment--inventory)
      - [Script Hooks](#script-hooks-2)
      - [KotOR-Specific Features](#kotor-specific-features)
      - [Implementation Notes](#implementation-notes-6)
    - [UTD (Door)](#utd-door)
      - [Core Identity Fields](#core-identity-fields-3)
      - [Door Appearance \& Type](#door-appearance--type)
      - [Locking \& Security](#locking--security)
      - [Hit Points \& Durability](#hit-points--durability)
      - [Interaction \& Behavior](#interaction--behavior)
      - [Script Hooks](#script-hooks-3)
      - [Trap System](#trap-system)
      - [Load-Bearing Doors (KotOR2)](#load-bearing-doors-kotor2)
      - [Appearance Customization](#appearance-customization)
      - [Implementation Notes](#implementation-notes-7)
    - [UTE (Encounter)](#ute-encounter)
      - [Core Identity Fields](#core-identity-fields-4)
      - [Spawn Configuration](#spawn-configuration)
      - [Respawn Logic](#respawn-logic)
      - [Creature List](#creature-list)
      - [Trigger Logic](#trigger-logic)
    - [UTI (Item)](#uti-item)
      - [Core Identity Fields](#core-identity-fields-5)
      - [Base Item Configuration](#base-item-configuration)
      - [Item Properties](#item-properties)
      - [Weapon-Specific Fields](#weapon-specific-fields)
      - [Armor-Specific Fields](#armor-specific-fields)
      - [Quest \& Special Items](#quest--special-items)
      - [Upgrade System (KotOR1)](#upgrade-system-kotor1)
      - [Upgrade System (KotOR2 Enhanced)](#upgrade-system-kotor2-enhanced)
      - [Visual \& Audio](#visual--audio)
      - [Palette \& Editor](#palette--editor)
      - [Implementation Notes](#implementation-notes-8)
    - [UTM (Merchant)](#utm-merchant)
    - [UTP (Placeable)](#utp-placeable)
      - [Core Identity Fields](#core-identity-fields-6)
      - [Appearance \& Type](#appearance--type)
      - [Inventory System](#inventory-system)
      - [Locking \& Security](#locking--security-1)
      - [Hit Points \& Durability](#hit-points--durability-1)
      - [Interaction \& Behavior](#interaction--behavior-1)
      - [Script Hooks](#script-hooks-4)
      - [Trap System](#trap-system-1)
      - [Visual Customization](#visual-customization)
      - [Implementation Notes](#implementation-notes-9)
    - [UTS (Sound)](#uts-sound)
      - [Core Identity Fields](#core-identity-fields-7)
      - [Playback Control](#playback-control)
      - [Timing \& Interval](#timing--interval)
      - [Positioning](#positioning)
      - [Sound List](#sound-list)
    - [UTT (Trigger)](#utt-trigger)
      - [Core Identity Fields](#core-identity-fields-8)
      - [Trigger Configuration](#trigger-configuration)
      - [Transition Settings](#transition-settings)
      - [Trap System](#trap-system-2)
      - [Script Hooks](#script-hooks-5)
    - [UTW (Waypoint)](#utw-waypoint)
      - [Core Identity Fields](#core-identity-fields-9)
      - [Map Note Functionality](#map-note-functionality)
      - [Linking \& Appearance](#linking--appearance)
  - [Implementation Details](#implementation-details)

---

## File Structure Overview

GFF files use a [hierarchical](https://en.wikipedia.org/wiki/Hierarchical_data_model) structure with [structs](https://en.wikipedia.org/wiki/Struct_(C_programming_language)) containing fields, which can be simple values or nested structs and lists. The format supports version V3.2 (KotOR) and later versions (V3.3, V4.0, V4.1) used in other BioWare games.

### GFF as a Universal Container

GFF is BioWare's universal container format for structured game data. Think of it as a binary [JSON](https://en.wikipedia.org/wiki/JSON) or [XML](https://en.wikipedia.org/wiki/XML) with strong typing:

**Advantages:**

- **[Type Safety](https://en.wikipedia.org/wiki/Type_safety)**: Each field has an explicit data type (unlike text formats)
- **Compact**: [Binary encoding](https://en.wikipedia.org/wiki/Binary_code) is much smaller than equivalent XML/JSON
- **Fast**: Direct [memory mapping](https://en.wikipedia.org/wiki/Memory-mapped_file) without parsing overhead
- **[Hierarchical](https://en.wikipedia.org/wiki/Hierarchical_data_model)**: Natural representation of nested game data
- **Extensible**: New fields can be added without breaking compatibility

**Common Uses:**

- Character/Creature templates (UTC, UTP, UTD, UTE, etc.)
- Area definitions (ARE, GIT, IFO)
- Dialogue trees (DLG)
- Quest journals (JRL)
- Module information (IFO)
- Save game state (SAV files contain GFF resources)
- User interface layouts (GUI)

Every `.utc`, `.uti`, `.dlg`, `.are`, and dozens of other KotOR file types are GFF files with different file type signatures and field schemas.

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/gff/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/gff/)

**Reference**: [`vendor/reone/src/libs/resource/gff.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/gff.cpp)

---

## Binary Format

### File Header

The file header is 56 bytes in size:

| Name                | Type    | Offset | Size | Description                                    |
| ------------------- | ------- | ------ | ---- | ---------------------------------------------- |
| File Type           | char[4] | 0      | 4    | Content type (e.g., `"GFF "`, `"ARE "`, `"UTC "`) |
| File Version        | char[4] | 4      | 4    | Format version (`"V3.2"` for KotOR)           |
| Struct Array Offset | uint32  | 8      | 4    | Offset to struct array                        |
| Struct Count        | uint32  | 12     | 4    | Number of structs                              |
| Field Array Offset  | uint32  | 16     | 4    | Offset to field array                         |
| Field Count         | uint32  | 20     | 4    | Number of fields                               |
| Label Array Offset   | uint32  | 24     | 4    | Offset to label array                         |
| Label Count          | uint32  | 28     | 4    | Number of labels                               |
| Field Data Offset    | uint32  | 32     | 4    | Offset to field data section                  |
| Field Data Count     | uint32  | 36     | 4    | Size of field data section in bytes           |
| Field Indices Offset | uint32  | 40     | 4    | Offset to field indices array                 |
| Field Indices Count  | uint32  | 44     | 4    | Number of field indices                       |
| List Indices Offset  | uint32  | 48     | 4    | Offset to list indices array                  |
| List Indices Count   | uint32  | 52     | 4    | Number of list indices                        |

**Reference**: [`vendor/reone/src/libs/resource/format/gffreader.cpp:30-44`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/gffreader.cpp#L30-L44)

### Label Array

Labels are 16-byte null-terminated strings used as field names:

| Name   | Type     | Size | Description                                                      |
| ------ | -------- | ---- | ---------------------------------------------------------------- |
| Labels | char[16] | 16×N | [Array](https://en.wikipedia.org/wiki/Array_data_structure) of field name labels ([null-padded](https://en.wikipedia.org/wiki/Null-terminated_string) to 16 bytes)            |

**Reference**: [`vendor/reone/src/libs/resource/format/gffreader.cpp:151-154`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/gffreader.cpp#L151-L154)

### Struct Array

Each struct entry is 12 bytes:

| Name       | Type   | Offset | Size | Description                                                      |
| ---------- | ------ | ------ | ---- | ---------------------------------------------------------------- |
| Struct ID  | int32  | 0      | 4    | Structure type identifier                                        |
| Data/Offset| uint32 | 4      | 4    | Field index (if 1 field) or offset to field indices (if multiple) |
| Field Count| uint32 | 8      | 4    | Number of fields in this struct (0, 1, or >1)                   |

**Reference**: [`vendor/reone/src/libs/resource/format/gffreader.cpp:40-62`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/gffreader.cpp#L40-L62)

### Field Array

Each field entry is 12 bytes:

| Name        | Type   | Offset | Size | Description                                                      |
| ----------- | ------ | ------ | ---- | ---------------------------------------------------------------- |
| Field Type  | uint32 | 0      | 4    | Data type (see [GFF Data Types](#gff-data-types))              |
| Label Index | uint32 | 4      | 4    | Index into label array for field name                           |
| Data/Offset | uint32 | 8      | 4    | Inline data (simple types) or offset to field data (complex types) |

**Reference**: [`vendor/reone/src/libs/resource/format/gffreader.cpp:67-76`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/gffreader.cpp#L67-L76)

### Field Data

Complex field types store their data in the field data section:

| Field Type        | Storage Format                                                      |
| ----------------- | ------------------------------------------------------------------- |
| UInt64            | 8 bytes (uint64)                                                    |
| Int64             | 8 bytes (int64)                                                     |
| Double            | 8 bytes (double)                                                    |
| String            | 4 bytes length + N bytes string data                                |
| ResRef            | 1 byte length + N bytes resref data (max 16 chars)                  |
| LocalizedString   | 4 bytes count + N×8 bytes (Language ID + StrRef pairs)              |
| Binary            | 4 bytes length + N bytes binary data                                 |
| Vector3           | 12 bytes (3×float)                                                   |
| Vector4           | 16 bytes (4×float)                                                   |

**Reference**: [`vendor/reone/src/libs/resource/format/gffreader.cpp:78-146`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/gffreader.cpp#L78-L146)

### Field Indices

When a struct has multiple fields, the struct's data field contains an offset into the field indices array, which lists the field indices for that struct.

### List Indices

Lists are stored as arrays of struct indices. The list field contains an offset into the list indices array, which contains the struct indices that make up the list.

---

## GFF Data Types

GFF supports the following field types:

| Type ID | Name              | Size (inline) | Description                                                      |
| ------- | ----------------- | ------------- | ---------------------------------------------------------------- |
| 0       | Byte              | 1             | 8-bit unsigned integer                                           |
| 1       | Char              | 1             | 8-bit signed integer                                              |
| 2       | Word              | 2             | 16-bit unsigned integer                                          |
| 3       | Short             | 2             | 16-bit signed integer                                             |
| 4       | DWord             | 4             | 32-bit unsigned integer                                          |
| 5       | Int               | 4             | 32-bit signed integer                                             |
| 6       | DWord64           | 8             | 64-bit unsigned integer (stored in field data)                  |
| 7       | Int64              | 8             | 64-bit signed integer (stored in field data)                      |
| 8       | Float             | 4             | 32-bit floating point                                             |
| 9       | Double            | 8             | 64-bit floating point (stored in field data)                     |
| 10      | CExoString        | varies        | Null-terminated string (stored in field data)                    |
| 11      | ResRef            | varies        | Resource reference (stored in field data, max 16 chars)          |
| 12      | CExoLocString     | varies        | Localized string (stored in field data)                           |
| 13      | Void              | varies        | Binary data blob (stored in field data)                          |
| 14      | Struct            | 4             | Nested struct (struct index stored inline)                       |
| 15      | List              | 4             | List of structs (offset to list indices stored inline)            |
| 16      | Orientation       | 16            | Quaternion (4×float, stored in field data as Vector4)            |
| 17      | Vector            | 12            | 3D vector (3×float, stored in field data)                       |
| 18      | StrRef            | 4             | String reference (TLK StrRef, stored inline as int32)             |

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/gff/gff_data.py:73-108`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/gff/gff_data.py#L73-L108)

**Type Selection Guidelines:**

- Use **Byte/Char** for small integers (-128 to 255) and boolean flags
- Use **Word/Short** for medium integers like IDs and counts
- Use **DWord/Int** for large values and most numeric fields
- Use **Float** for decimals that don't need high precision (positions, angles)
- Use **Double** for high-precision calculations (rare in KotOR)
- Use **CExoString** for text that doesn't need localization
- Use **CExoLocString** for player-visible text that should be translated
- Use **ResRef** for filenames without extensions (models, textures, scripts)
- Use **Void** for binary blobs like encrypted data or custom structures
- Use **Struct** for nested objects with multiple fields
- Use **List** for arrays of structs (inventory items, dialogue replies)
- Use **Vector** for 3D positions and directions
- Use **Orientation** for quaternion rotations
- Use **StrRef** for references to dialog.tlk entries

**Storage Optimization:**

Inline types (0-5, 8, 14, 15, 18) store their value directly in the field entry, saving space and improving access speed. Complex types (6-7, 9-13, 16-17) require an offset to field data, adding overhead. When designing custom GFF schemas, prefer inline types where possible.

---

## GFF Structure

### GFFStruct

A GFF struct is a collection of named fields. Each struct has:

- **Struct ID**: Type identifier (often 0xFFFFFFFF for generic structs)
- **Fields**: Dictionary mapping field names (labels) to field values

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/gff/gff_data.py:400-800`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/gff/gff_data.py#L400-L800)

### GFFField

Fields can be accessed using type-specific getter/setter methods:

- `get_uint8(label)`, `set_uint8(label, value)`
- `get_int32(label)`, `set_int32(label, value)`
- `get_float(label)`, `set_float(label, value)`
- `get_string(label)`, `set_string(label, value)`
- `get_resref(label)`, `set_resref(label, value)`
- `get_locstring(label)`, `set_locstring(label, value)`
- `get_vector3(label)`, `set_vector3(label, value)`
- `get_struct(label)`, `set_struct(label, struct)`
- `get_list(label)`, `set_list(label, list)`

### GFFList

A GFF list is an ordered collection of structs. Lists are accessed via:

- `get_list(label)`: Returns a `GFFList` object
- `GFFList.get(i)`: Gets struct at index `i`
- `GFFList.append(struct)`: Adds a struct to the list

**Common List Usage:**

Lists are used extensively for variable-length arrays:

- **ItemList** in UTC files: Character inventory items
- **Equip_ItemList** in UTC files: Equipped items
- **EntryList** in DLG files: Dialogue entry nodes
- **ReplyList** in DLG files: Dialogue reply options
- **SkillList** in UTC files: Character skills
- **FeatList** in UTC files: Character feats
- **EffectList** in various files: Applied effects
- **Creature_List** in GIT files: Spawned creatures in area

When modifying lists, always maintain struct IDs and parent references to avoid breaking internal links.

---

## GFF Generic Types

GFF files are used as containers for various game resource types. Each generic type has its own structure and field definitions.

### ARE (Area)

ARE files define static area properties including lighting, weather, ambient audio, grass rendering, fog settings, script hooks, and minimap data. ARE files contain environmental and atmospheric data for game areas, while dynamic object placement is handled by GIT files.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/are.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/are.py)

#### Core Identity Fields

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Tag` | CExoString | Unique area identifier |
| `Name` | CExoLocString | Area name (localized) |
| `Comments` | CExoString | Developer notes/documentation |
| `Creator_ID` | DWord | Toolset creator identifier (unused at runtime) |
| `ID` | DWord | Unique area ID (unused at runtime) |
| `Version` | DWord | Area version (unused at runtime) |
| `Flags` | DWord | Area flags (unused in KotOR) |

#### Lighting & Sun

| Field | Type | Description |
| ----- | ---- | ----------- |
| `SunAmbientColor` | Color | Ambient light color RGB |
| `SunDiffuseColor` | Color | Sun diffuse light color RGB |
| `SunShadows` | Byte | Enable shadow rendering |
| `ShadowOpacity` | Byte | Shadow opacity (0-255) |
| `DynAmbientColor` | Color | Dynamic ambient light RGB |

**Lighting System:**

- **SunAmbientColor**: Base ambient illumination (affects all surfaces)
- **SunDiffuseColor**: Directional sunlight color
- **SunShadows**: Enables real-time shadow casting
- **ShadowOpacity**: Controls shadow darkness
- **DynAmbientColor**: Secondary ambient for dynamic lighting

#### Fog Settings

| Field | Type | Description |
| ----- | ---- | ----------- |
| `SunFogOn` | Byte | Enable fog rendering |
| `SunFogNear` | Float | Fog start distance |
| `SunFogFar` | Float | Fog end distance |
| `SunFogColor` | Color | Fog color RGB |

**Fog Rendering:**

- **SunFogOn=1**: Fog active
- **SunFogNear**: Distance where fog begins (world units)
- **SunFogFar**: Distance where fog is opaque
- **SunFogColor**: Fog tint color (atmosphere)

**Fog Calculation:**

- Linear interpolation from Near to Far
- Objects beyond Far fully obscured
- Creates depth perception and atmosphere

#### Moon Lighting (Unused)

| Field | Type | Description |
| ----- | ---- | ----------- |
| `MoonAmbientColor` | Color | Moon ambient light (unused) |
| `MoonDiffuseColor` | Color | Moon diffuse light (unused) |
| `MoonFogOn` | Byte | Moon fog toggle (unused) |
| `MoonFogNear` | Float | Moon fog start (unused) |
| `MoonFogFar` | Float | Moon fog end (unused) |
| `MoonFogColor` | Color | Moon fog color (unused) |
| `MoonShadows` | Byte | Moon shadows (unused) |
| `IsNight` | Byte | Night time flag (unused) |

**Moon System:**

- Defined in file format but not used by KotOR engine
- Intended for day/night cycle (not implemented)
- Always use Sun settings for lighting

#### Grass Rendering

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Grass_TexName` | ResRef | Grass texture name |
| `Grass_Density` | Float | Grass blade density (0.0-1.0) |
| `Grass_QuadSize` | Float | Size of grass patches |
| `Grass_Ambient` | Color | Grass ambient color RGB |
| `Grass_Diffuse` | Color | Grass diffuse color RGB |
| `Grass_Emissive` (KotOR2) | Color | Grass emissive color RGB |
| `Grass_Prob_LL` | Float | Spawn probability lower-left |
| `Grass_Prob_LR` | Float | Spawn probability lower-right |
| `Grass_Prob_UL` | Float | Spawn probability upper-left |
| `Grass_Prob_UR` | Float | Spawn probability upper-right |

**Grass System:**

- **Grass_TexName**: Texture for grass blades (TGA/TPC)
- **Grass_Density**: Coverage density (1.0 = full coverage)
- **Grass_QuadSize**: Patch size in world units
- **Probability Fields**: Control grass distribution across area

**Grass Rendering:**

1. Area divided into grid based on QuadSize
2. Each quad has spawn probability from corner interpolation
3. Density determines blades per quad
4. Grass billboards oriented to camera

#### Weather System (KotOR2)

| Field | Type | Description |
| ----- | ---- | ----------- |
| `ChanceRain` (KotOR2) | Int | Rain probability (0-100) |
| `ChanceSnow` (KotOR2) | Int | Snow probability (0-100) |
| `ChanceLightning` (KotOR2) | Int | Lightning probability (0-100) |

**Weather Effects:**

- Random weather based on probability
- Particle effects for rain/snow
- Lightning provides flash and sound

#### Dirty/Dust Settings (KotOR2)

| Field | Type | Description |
| ----- | ---- | ----------- |
| `DirtyARGBOne` (KotOR2) | DWord | First dust color ARGB |
| `DirtySizeOne` (KotOR2) | Float | First dust particle size |
| `DirtyFormulaOne` (KotOR2) | Int | First dust formula type |
| `DirtyFuncOne` (KotOR2) | Int | First dust function |
| `DirtyARGBTwo` (KotOR2) | DWord | Second dust color ARGB |
| `DirtySizeTwo` (KotOR2) | Float | Second dust particle size |
| `DirtyFormulaTwo` (KotOR2) | Int | Second dust formula type |
| `DirtyFuncTwo` (KotOR2) | Int | Second dust function |
| `DirtyARGBThree` (KotOR2) | DWord | Third dust color ARGB |
| `DirtySizeThree` (KotOR2) | Float | Third dust particle size |
| `DirtyFormulaThre` (KotOR2) | Int | Third dust formula type |
| `DirtyFuncThree` (KotOR2) | Int | Third dust function |

**Dust Particle System:**

- Three independent dust layers
- Each layer has color, size, and behavior
- Creates atmospheric dust/smoke effects

#### Environment & Camera

| Field | Type | Description |
| ----- | ---- | ----------- |
| `DefaultEnvMap` | ResRef | Default environment map texture |
| `CameraStyle` | Int | Camera behavior type |
| `AlphaTest` | Byte | Alpha testing threshold |
| `WindPower` | Int | Wind strength for effects |
| `LightingScheme` | Int | Lighting scheme identifier (unused) |

**Environment Mapping:**

- `DefaultEnvMap`: Cubemap for reflective surfaces
- Applied to models without specific envmaps

**Camera Behavior:**

- `CameraStyle`: Determines camera constraints
- Defines zoom, rotation, and collision behavior

#### Area Behavior Flags

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Unescapable` | Byte | Cannot use save/travel functions |
| `DisableTransit` | Byte | Cannot travel to other modules |
| `StealthXPEnabled` | Byte | Award stealth XP |
| `StealthXPLoss` | Int | Stealth detection XP penalty |
| `StealthXPMax` | Int | Maximum stealth XP per area |

**Stealth System:**

- **StealthXPEnabled**: Area rewards stealth gameplay
- **StealthXPMax**: Cap on XP from stealth
- **StealthXPLoss**: Penalty when detected

**Area Restrictions:**

- **Unescapable**: Prevents save/load menus (story sequences)
- **DisableTransit**: Locks player in current location

#### Skill Check Modifiers

| Field | Type | Description |
| ----- | ---- | ----------- |
| `ModSpotCheck` | Int | Awareness skill modifier (unused) |
| `ModListenCheck` | Int | Listen skill modifier (unused) |

**Skill Modifiers:**

- Intended to modify detection checks area-wide
- Not implemented in KotOR engine

#### Script Hooks

| Field | Type | Description |
| ----- | ---- | ----------- |
| `OnEnter` | ResRef | Fires when entering area |
| `OnExit` | ResRef | Fires when leaving area |
| `OnHeartbeat` | ResRef | Fires periodically |
| `OnUserDefined` | ResRef | Fires on user-defined events |

**Script Execution:**

- **OnEnter**: Area initialization, cinematics, spawns
- **OnExit**: Cleanup, state saving
- **OnHeartbeat**: Periodic updates (every 6 seconds)
- **OnUserDefined**: Custom event handling

#### Rooms & Minimap

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Rooms` | List | Room definitions for minimap |

**Rooms Struct Fields:**

- `RoomName` (CExoString): Room identifier
- `EnvAudio` (Int): Environment audio for room
- `AmbientScale` (Float): Ambient audio volume modifier

**Room System:**

- Defines minimap regions
- Each room has audio properties
- Audio transitions between rooms
- Minimap reveals room-by-room

#### Implementation Notes

**Area Loading Sequence:**

1. **Parse ARE**: Load static properties from GFF
2. **Apply Lighting**: Set sun/ambient colors
3. **Setup Fog**: Configure fog parameters
4. **Load Grass**: Initialize grass rendering if configured
5. **Configure Weather**: Activate weather systems (KotOR2)
6. **Register Scripts**: Setup area event handlers
7. **Load GIT**: Spawn dynamic objects (separate file)

**Lighting Performance:**

- Ambient/Diffuse colors affect all area geometry
- Shadow rendering is expensive (SunShadows=0 for performance)
- Dynamic lighting for special effects only

**Grass Optimization:**

- High density grass impacts framerate significantly
- Probability fields allow targeted grass placement
- Grass LOD based on camera distance

**Audio Zones:**

- Rooms define audio transitions
- EnvAudio from ARE and Rooms determines soundscape
- Smooth fade between zones

**Common Area Configurations:**

**Outdoor Areas:**

- Bright sunlight (high diffuse)
- Fog for horizon
- Grass rendering
- Wind effects

**Indoor Areas:**

- Low ambient lighting
- No fog (usually)
- No grass
- Controlled camera

**Dark Areas:**

- Minimal ambient
- Strong diffuse for dramatic shadows
- Fog for atmosphere

**Special Areas:**

- Unescapable for story sequences
- Custom camera styles for unique views
- Specific environment maps for mood

### DLG (Dialogue)

DLG files store conversation trees, forming the core of KotOR's narrative interaction. A dialogue consists of a hierarchy of Entry nodes (NPC lines) and Reply nodes (Player options), connected by Links.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/dlg/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/generics/dlg/)

#### Conversation Properties

| Field | Type | Description |
| ----- | ---- | ----------- |
| `DelayEntry` | Int | Delay before conversation starts |
| `DelayReply` | Int | Delay before player reply options appear |
| `NumWords` | Int | Total word count (unused) |
| `PreventSkipping` | Byte | Prevents skipping dialogue lines |
| `Skippable` | Byte | Allows skipping dialogue |
| `Sound` | ResRef | Background sound loop |
| `AmbientTrack` | Int | Background music track ID |
| `CameraModel` | ResRef | Camera model for cutscenes |
| `ComputerType` | Byte | Interface style (0=Modern, 1=Ancient) |
| `ConversationType` | Byte | 0=Human, 1=Computer, 2=Other |
| `OldHitCheck` | Byte | Legacy hit check flag (unused) |

**Conversation Types:**

- **Human**: Cinematic camera, VO support, standard UI
- **Computer**: Full-screen terminal interface, no VO, green text
- **Other**: Overhead text bubbles (bark strings)

#### Script Hooks

| Field | Type | Description |
| ----- | ---- | ----------- |
| `EndConversation` | ResRef | Fires when conversation ends normally |
| `EndConverAbort` | ResRef | Fires when conversation is aborted |

#### Node Lists

DLG files use two main lists for nodes and one for starting points:

| List Field | Contains | Description |
| ---------- | -------- | ----------- |
| `EntryList` | DLGEntry | NPC dialogue lines |
| `ReplyList` | DLGReply | Player response options |
| `StartingList` | DLGLink | Entry points into the dialogue tree |

**Graph Structure:**

- **StartingList** links to **EntryList** nodes (NPC starts)
- **EntryList** nodes link to **ReplyList** nodes (Player responds)
- **ReplyList** nodes link to **EntryList** nodes (NPC responds)
- Links can be conditional (Script checks)

#### DLGNode Structure (Entries & Replies)

Both Entry and Reply nodes share common fields:

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Text` | CExoLocString | Dialogue text |
| `VO_ResRef` | ResRef | Voice-over audio file |
| `Sound` | ResRef | Sound effect ResRef |
| `Script` | ResRef | Script to execute (Action) |
| `Delay` | Int | Delay before text appears |
| `Comment` | CExoString | Developer comment |
| `Speaker` | CExoString | Speaker tag (Entry only) |
| `Listener` | CExoString | Listener tag (unused) |
| `Quest` | CExoString | Journal tag to update |
| `QuestEntry` | Int | Journal entry ID |
| `PlotIndex` | Int | Plot index (legacy) |
| `PlotXPPercentage` | Float | XP reward percentage |

**Cinematic Fields:**

- `CameraAngle`: Camera angle ID
- `CameraID`: Specific camera ID
- `CameraAnimation`: Animation to play
- `CamFieldOfView`: Camera FOV
- `CamHeightOffset`: Camera height
- `CamVidEffect`: Video effect ID

**Animation List:**

- List of animations to play on participants
- `Participant`: Tag of object to animate
- `Animation`: Animation ID

#### DLGLink Structure

Links connect nodes and define flow control:

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Index` | Int | Index of target node in Entry/Reply list |
| `Active` | ResRef | Conditional script (returns TRUE/FALSE) |
| `Script` | ResRef | Action script (executed on transition) |
| `IsChild` | Byte | 1 if linking to node in list, 0 if logic link |
| `LinkComment` | CExoString | Developer comment |

**Conditional Logic:**

- **Active** script determines if link is available
- If script returns FALSE, link is skipped
- Engine evaluates links top-to-bottom
- First valid link is taken (for NPC lines)
- All valid links displayed (for Player replies)

**KotOR 2 Logic Extensions:**

- `Logic`: 0=AND, 1=OR (combines Active conditions)
- `Not`: Negates condition result

#### Implementation Notes

**Flow Evaluation:**

1. Conversation starts
2. Engine evaluates `StartingList` links
3. First link with valid `Active` condition is chosen
4. Transition to target `EntryList` node
5. Execute Entry `Script`, play `VO`, show `Text`
6. Evaluate Entry's links to `ReplyList`
7. Display all valid Replies to player
8. Player selects Reply
9. Transition to target `ReplyList` node
10. Evaluate Reply's links to `EntryList`
11. Loop until no links remain or `EndConversation` called

**Computer Dialogues:**

- `ComputerType=1` (Ancient) changes font/background
- No cinematic cameras
- Used for terminals and datapads

**Bark Strings:**

- `ConversationType=2`
- No cinematic mode, text floats over head
- Non-blocking interaction

**Journal Integration:**

- `Quest` and `QuestEntry` fields update JRL directly
- Eliminates need for scripts to update quests

### GIT (Game Instance Template)

GIT files store dynamic instance data for areas, defining where creatures, doors, placeables, triggers, waypoints, stores, encounters, sounds, and cameras are positioned in the game world. While ARE files define static environmental properties, GIT files contain all runtime object placement and instance-specific properties.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/git.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/git.py)

#### Area Properties

| Field | Type | Description |
| ----- | ---- | ----------- |
| `AmbientSndDay` | Int | Day ambient sound ID |
| `AmbientSndDayVol` | Int | Day ambient volume (0-127) |
| `AmbientSndNight` | Int | Night ambient sound ID |
| `AmbientSndNightVol` | Int | Night ambient volume |
| `EnvAudio` | Int | Environment audio type |
| `MusicBattle` | Int | Battle music track ID |
| `MusicDay` | Int | Standard/exploration music ID |
| `MusicNight` | Int | Night music track ID |
| `MusicDelay` | Int | Delay before music starts (seconds) |

**Audio Configuration:**

- **Ambient Sounds**: Looping background ambience
- **Music Tracks**: From `ambientmusic.2da` and `musicbattle.2da`
- **EnvAudio**: Reverb/echo type for area
- **MusicDelay**: Prevents instant music start

**Music System:**

- MusicDay plays during exploration
- MusicBattle triggers during combat
- MusicNight unused in KotOR (no day/night cycle)
- Smooth transitions between tracks

#### Instance Lists

GIT files contain multiple lists defining object instances:

| List Field | Contains | Description |
| ---------- | -------- | ----------- |
| `Creature List` | GITCreature | Spawned NPCs and enemies |
| `Door List` | GITDoor | Placed doors |
| `Placeable List` | GITPlaceable | Containers, furniture, objects |
| `Encounter List` | GITEncounter | Encounter spawn zones |
| `TriggerList` | GITTrigger | Trigger volumes |
| `WaypointList` | GITWaypoint | Waypoint markers |
| `StoreList` | GITStore | Merchant vendors |
| `SoundList` | GITSound | Positional audio emitters |
| `CameraList` | GITCamera | Camera definitions |

**Instance Structure:**

Each instance type has common fields plus type-specific data:

**Common Instance Fields:**

- Position (X, Y, Z coordinates)
- Orientation (quaternion or Euler angles)
- Template ResRef (UTC, UTD, UTP, etc.)
- Tag override (optional)

#### GITCreature Instances

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | ResRef | UTC template to spawn |
| `XPosition` | Float | World X coordinate |
| `YPosition` | Float | World Y coordinate |
| `ZPosition` | Float | World Z coordinate |
| `XOrientation` | Float | Orientation X component |
| `YOrientation` | Float | Orientation Y component |

**Creature Spawning:**

- Engine loads UTC template
- Applies position/orientation from GIT
- Creature initialized with template stats
- Scripts fire after spawn

#### GITDoor Instances

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | ResRef | UTD template |
| `Tag` | CExoString | Instance tag override |
| `LinkedToModule` | ResRef | Destination module |
| `LinkedTo` | CExoString | Destination waypoint tag |
| `LinkedToFlags` | Byte | Transition flags |
| `TransitionDestin` | CExoLocString | Destination label (UI) |
| `X`, `Y`, `Z` | Float | Position coordinates |
| `Bearing` | Float | Door orientation |
| `TweakColor` | DWord | Door color tint |
| `Hitpoints` | Short | Current HP override |

**Door Linking:**

- **LinkedToModule**: Target module ResRef
- **LinkedTo**: Waypoint tag in target module
- **TransitionDestin**: Loading screen text
- Doors can teleport between modules

**Door Instances:**

- Inherit properties from UTD template
- GIT can override HP, tag, linked destination
- Position/orientation instance-specific

#### GITPlaceable Instances

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | ResRef | UTP template |
| `Tag` | CExoString | Instance tag override |
| `X`, `Y`, `Z` | Float | Position coordinates |
| `Bearing` | Float | Rotation angle |
| `TweakColor` | DWord | Color tint |
| `Hitpoints` | Short | Current HP override |
| `Useable` | Byte | Can be used override |

**Placeable Spawning:**

- Template defines behavior, appearance
- GIT defines placement and orientation
- Can override usability and HP at instance level

#### GITTrigger Instances

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | ResRef | UTT template |
| `Tag` | CExoString | Instance tag |
| `TransitionDestin` | CExoLocString | Transition label |
| `LinkedToModule` | ResRef | Destination module |
| `LinkedTo` | CExoString | Destination waypoint |
| `LinkedToFlags` | Byte | Transition flags |
| `X`, `Y`, `Z` | Float | Trigger position |
| `XPosition`, `YPosition`, `ZPosition` | Float | Position (alternate) |
| `XOrientation`, `YOrientation`, `ZOrientation` | Float | Orientation |
| `Geometry` | List | Trigger volume vertices |

**Geometry Struct:**

- List of Vector3 points
- Defines trigger boundary polygon
- Planar geometry (Z-axis extrusion)

**Trigger Types:**

- **Area Transition**: LinkedToModule set
- **Script Trigger**: Fires scripts from UTT
- **Generic Trigger**: Custom behavior

#### GITWaypoint Instances

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | ResRef | UTW template |
| `Tag` | CExoString | Waypoint identifier |
| `Appearance` | DWord | Waypoint appearance type |
| `LinkedTo` | CExoString | Linked waypoint tag |
| `X`, `Y`, `Z` | Float | Position coordinates |
| `XOrientation`, `YOrientation` | Float | Orientation |
| `HasMapNote` | Byte | Has map note |
| `MapNote` | CExoLocString | Map note text |
| `MapNoteEnabled` | Byte | Map note visible |

**Waypoint Usage:**

- **Spawn Points**: Character entry locations
- **Pathfinding**: AI navigation targets
- **Script Targets**: "Go to waypoint X"
- **Map Notes**: Player-visible markers

#### GITEncounter Instances

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | ResRef | UTE template |
| `Tag` | CExoString | Encounter identifier |
| `X`, `Y`, `Z` | Float | Spawn position |
| `Geometry` | List | Spawn zone boundary |

**Encounter System:**

- Geometry defines trigger zone
- Engine spawns creatures from UTE when entered
- Respawn behavior from UTE template

#### GITStore Instances

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | ResRef | UTM template |
| `Tag` | CExoString | Store identifier |
| `X`, `Y`, `Z` | Float | Position (for UI, not physical) |
| `XOrientation`, `YOrientation` | Float | Orientation |

**Store System:**

- Stores don't have physical presence
- Position used for toolset only
- Accessed via conversations or scripts

#### GITSound Instances

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | ResRef | UTS template |
| `Tag` | CExoString | Sound identifier |
| `X`, `Y`, `Z` | Float | Emitter position |
| `MaxDistance` | Float | Audio falloff distance |
| `MinDistance` | Float | Full volume radius |
| `RandomRangeX`, `RandomRangeY` | Float | Position randomization |
| `Volume` | Byte | Volume level (0-127) |

**Positional Audio:**

- 3D sound emitter at position
- Volume falloff over distance
- Random offset for variation

#### GITCamera Instances

| Field | Type | Description |
| ----- | ---- | ----------- |
| `CameraID` | Int | Camera identifier |
| `FOV` | Float | Field of view (degrees) |
| `Height` | Float | Camera height |
| `MicRange` | Float | Audio capture range |
| `Orientation` | Vector4 | Camera rotation (quaternion) |
| `Pitch` | Float | Camera pitch angle |
| `Position` | Vector3 | Camera position |

**Camera System:**

- Defines fixed camera angles
- Used for cutscenes and dialogue
- FOV controls zoom level

#### Implementation Notes

**GIT Loading Process:**

1. **Parse GIT**: Read GFF structure
2. **Load Templates**: Read UTC, UTD, UTP, etc. files
3. **Instantiate Objects**: Create runtime objects from templates
4. **Apply Overrides**: GIT position, HP, tag overrides applied
5. **Link Objects**: Resolve LinkedTo references
6. **Execute Spawn Scripts**: Fire OnSpawn events
7. **Activate Triggers**: Register trigger geometry

**Instance vs. Template:**

- **Template (UTC/UTD/UTP/etc.)**: Defines what the object is
- **Instance (GIT entry)**: Defines where the object is
- GIT can override specific template properties
- Multiple instances can share one template

**Performance Considerations:**

- Large instance counts impact load time
- Complex trigger geometry affects collision checks
- Many sounds can overwhelm audio system
- Creature AI scales with creature count

**Dynamic vs. Static:**

- **GIT**: Dynamic, saved with game progress
- **ARE**: Static, never changes
- GIT instances can be destroyed, moved, modified
- ARE properties remain constant

**Save Game Integration:**

- GIT state saved in save files
- Instance positions, HP, inventory preserved
- Destroyed objects marked as deleted
- New dynamic objects added to save

**Common GIT Patterns:**

**Ambush Spawns:**

- Creatures placed outside player view
- Positioned for tactical advantage
- Often linked to trigger activation

**Progression Gates:**

- Locked doors requiring keys/skills
- Triggers that load new modules
- Waypoints marking objectives

**Interactive Areas:**

- Clusters of placeables (containers)
- NPCs for dialogue
- Stores for shopping
- Workbenches for crafting

**Navigation Networks:**

- Waypoints for AI pathfinding
- Logical connections via LinkedTo
- Map notes for player guidance

**Audio Atmosphere:**

- Ambient sound emitters positioned strategically
- Varied volumes and ranges
- Random offsets for natural feel

### GUI

GUI files define the layout and behavior of the user interface. They are GFF files describing hierarchies of panels, buttons, labels, and other controls.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/gui.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/gui.py)

#### Core Identity Fields

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Tag` | CExoString | Unique GUI identifier |
| `ObjName` | CExoString | Object name (unused) |
| `Comment` | CExoString | Developer comment |

#### Control Structure

GUI files contain a `Controls` list, which holds the top-level UI elements. Each control can contain child controls, forming a tree structure.

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Controls` | List | List of child controls |
| `Type` | Int | Control type identifier |
| `ID` | Int | Unique Control ID |
| `Tag` | CExoString | Control tag |

**Control Types:**

| ID | Name | Description |
| -- | ---- | ----------- |
| -1 | Invalid | Invalid control type |
| 0 | Control | Base container (rarely used) |
| 2 | Panel | Background panel/container |
| 4 | ProtoItem | Prototype item template (for ListBox items) |
| 5 | Label | Static text label |
| 6 | Button | Clickable button |
| 7 | CheckBox | Toggle checkbox |
| 8 | Slider | Sliding value control |
| 9 | ScrollBar | Scroll bar control |
| 10 | Progress | Progress bar indicator |
| 11 | ListBox | List of items with scrolling |

#### Common Properties

All controls share these base properties:

| Field | Type | Description |
| ----- | ---- | ----------- |
| `CONTROLTYPE` | Int | Control type identifier (see Control Types) |
| `ID` | Int | Unique control ID for script references |
| `TAG` | CExoString | Control tag identifier |
| `Obj_Locked` | Byte | Lock state (0=unlocked, 1=locked) |
| `Obj_Parent` | CExoString | Parent control tag (for hierarchy) |
| `Obj_ParentID` | Int | Parent control ID (for hierarchy) |
| `ALPHA` | Float | Opacity/transparency (0.0=transparent, 1.0=opaque) |
| `COLOR` | Vector | Control color modulation (RGB, 0.0-1.0) |
| `EXTENT` | Struct | Position and size rectangle |
| `BORDER` | Struct | Border rendering properties |
| `HILIGHT` | Struct | Highlight appearance (hover state) |
| `TEXT` | Struct | Text display properties |
| `MOVETO` | Struct | D-pad navigation targets |

**EXTENT Struct:**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `LEFT` | Int | X position relative to parent (pixels) |
| `TOP` | Int | Y position relative to parent (pixels) |
| `WIDTH` | Int | Control width (pixels) |
| `HEIGHT` | Int | Control height (pixels) |

**Positioning System:**

- Coordinates are relative to parent control
- Base resolution is 640x480, scaled for higher resolutions
- Negative values allowed for positioning outside parent bounds
- Root control (GUI) uses screen-relative coordinates

**BORDER Struct:**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `CORNER` | ResRef | Corner texture (TPC/TGA) |
| `EDGE` | ResRef | Edge texture (TPC/TGA) |
| `FILL` | ResRef | Fill/background texture (TPC/TGA) |
| `FILLSTYLE` | Int | Fill rendering style (-1=None, 0=Empty, 1=Solid, 2=Texture) |
| `DIMENSION` | Int | Border thickness in pixels |
| `INNEROFFSET` | Int | Inner padding X-axis (pixels) |
| `INNEROFFSETY` | Int | Inner padding Y-axis (pixels, optional) |
| `COLOR` | Vector | Border color modulation (RGB, 0.0-1.0) |
| `PULSING` | Byte | Pulsing animation flag (0=off, 1=on) |

**Border Rendering:**

- **CORNER**: 4 corner pieces (top-left, top-right, bottom-left, bottom-right)
- **EDGE**: 4 edge pieces (top, right, bottom, left)
- **FILL**: Center fill area (scaled to fit)
- **DIMENSION**: Thickness of border edges
- **FILLSTYLE**: Controls how fill texture is rendered (tiled, stretched, solid color)
- Border pieces are tiled/repeated along edges

**TEXT Struct:**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TEXT` | CExoString | Direct text content (overrides STRREF if set) |
| `STRREF` | DWord | TLK string reference (0xFFFFFFFF = unused) |
| `FONT` | ResRef | Font texture resource (TPC/TGA) |
| `ALIGNMENT` | Int | Text alignment flags (bitfield) |
| `COLOR` | Vector | Text color (RGB, 0.0-1.0) |
| `PULSING` | Byte | Pulsing animation flag (0=off, 1=on) |

**Text Alignment Values:**

- **1**: Top-Left
- **2**: Top-Center
- **3**: Top-Right
- **17**: Center-Left
- **18**: Center (most common)
- **19**: Center-Right
- **33**: Bottom-Left
- **34**: Bottom-Center
- **35**: Bottom-Right

**Text Resolution:**

- If both `TEXT` and `STRREF` are set, `TEXT` takes precedence
- Font textures contain character glyphs in fixed grid
- Text color modulates font texture (white = full color, black = no color)

**MOVETO Struct:**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `UP` | Int | Control ID to navigate to when pressing Up |
| `DOWN` | Int | Control ID to navigate to when pressing Down |
| `LEFT` | Int | Control ID to navigate to when pressing Left |
| `RIGHT` | Int | Control ID to navigate to when pressing Right |

**Navigation System:**

- Used for keyboard/D-pad navigation
- Value of -1 or 0 indicates no navigation in that direction
- Engine automatically wraps navigation at list boundaries
- Essential for controller/keyboard-only gameplay

**HILIGHT Struct:**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `CORNER` | ResRef | Corner texture for highlight state |
| `EDGE` | ResRef | Edge texture for highlight state |
| `FILL` | ResRef | Fill texture for highlight state |
| `FILLSTYLE` | Int | Fill style for highlight |
| `DIMENSION` | Int | Border thickness |
| `INNEROFFSET` | Int | Inner padding X-axis |
| `INNEROFFSETY` | Int | Inner padding Y-axis (optional) |
| `COLOR` | Vector | Highlight color modulation |
| `PULSING` | Byte | Pulsing animation flag |

**Highlight Behavior:**

- Shown when mouse hovers over control
- Replaces or overlays BORDER when active
- Used for interactive feedback
- Color typically brighter/more saturated than border

**SELECTED Struct:**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `CORNER` | ResRef | Corner texture for selected state |
| `EDGE` | ResRef | Edge texture for selected state |
| `FILL` | ResRef | Fill texture for selected state |
| `FILLSTYLE` | Int | Fill style for selected state |
| `DIMENSION` | Int | Border thickness |
| `INNEROFFSET` | Int | Inner padding X-axis |
| `INNEROFFSETY` | Int | Inner padding Y-axis (optional) |
| `COLOR` | Vector | Selected state color modulation |
| `PULSING` | Byte | Pulsing animation flag |

**HILIGHTSELECTED Struct:**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `CORNER` | ResRef | Corner texture for highlight+selected state |
| `EDGE` | ResRef | Edge texture for highlight+selected state |
| `FILL` | ResRef | Fill texture for highlight+selected state |
| `FILLSTYLE` | Int | Fill style |
| `DIMENSION` | Int | Border thickness |
| `INNEROFFSET` | Int | Inner padding X-axis |
| `INNEROFFSETY` | Int | Inner padding Y-axis (optional) |
| `COLOR` | Vector | Combined state color modulation |
| `PULSING` | Byte | Pulsing animation flag |

**State Priority:**

1. **HILIGHTSELECTED**: When control is both highlighted (hovered) and selected
2. **HILIGHT**: When control is highlighted (hovered) but not selected
3. **SELECTED**: When control is selected but not highlighted
4. **BORDER**: Default appearance

#### Control-Specific Fields

**ListBox (Type 11):**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `PROTOITEM` | Struct | Template for list item appearance |
| `SCROLLBAR` | Struct | Embedded scrollbar control |
| `PADDING` | Int | Spacing between items (pixels) |
| `MAXVALUE` | Int | Maximum scroll value (total items - visible items) |
| `CURVALUE` | Int | Current scroll position |
| `LOOPING` | Byte | Loop scrolling (0=no, 1=yes) |
| `LEFTSCROLLBAR` | Byte | Scrollbar on left side (0=right, 1=left) |

**ListBox Behavior:**

- **PROTOITEM**: Defines appearance template for each list item
- **SCROLLBAR**: Embedded scrollbar for navigating long lists
- **PADDING**: Vertical spacing between items
- **MAXVALUE**: Maximum scroll offset (when all items visible, MAXVALUE=0)
- **LOOPING**: When enabled, scrolling past end wraps to beginning
- **LEFTSCROLLBAR**: Positions scrollbar on left instead of right

**PROTOITEM Struct (for ListBox):**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `CONTROLTYPE` | Int | Always 4 (ProtoItem) |
| `EXTENT` | Struct | Item size and position |
| `BORDER` | Struct | Item border appearance |
| `HILIGHT` | Struct | Item highlight on hover |
| `HILIGHTSELECTED` | Struct | Item highlight when selected |
| `SELECTED` | Struct | Item appearance when selected |
| `TEXT` | Struct | Item text properties |
| `ISSELECTED` | Byte | Default selected state |

**ScrollBar (Type 9):**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `DIR` | Struct | Direction arrow buttons appearance |
| `THUMB` | Struct | Draggable thumb appearance |
| `MAXVALUE` | Int | Maximum scroll value |
| `VISIBLEVALUE` | Int | Number of visible items in viewport |
| `CURVALUE` | Int | Current scroll position |
| `DRAWMODE` | Byte | Drawing mode (0=normal, other values unused) |

**ScrollBar Behavior:**

- **MAXVALUE**: Total scrollable range
- **VISIBLEVALUE**: Size of visible area (determines thumb size)
- **CURVALUE**: Current scroll offset (0 to MAXVALUE)
- Thumb size = (VISIBLEVALUE / MAXVALUE) × track length

**DIR Struct (ScrollBar Direction Buttons):**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `IMAGE` | ResRef | Arrow button texture |
| `ALIGNMENT` | Int | Image alignment (typically 18=center) |
| `DRAWSTYLE` | Int | Drawing style (unused) |
| `FLIPSTYLE` | Int | Flip/rotation style (unused) |
| `ROTATE` | Float | Rotation angle (unused) |

**THUMB Struct (ScrollBar Thumb):**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `IMAGE` | ResRef | Thumb texture |
| `ALIGNMENT` | Int | Image alignment (typically 18=center) |
| `DRAWSTYLE` | Int | Drawing style (unused) |
| `FLIPSTYLE` | Int | Flip/rotation style (unused) |
| `ROTATE` | Float | Rotation angle (unused) |

**ProgressBar (Type 10):**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `PROGRESS` | Struct | Progress fill appearance |
| `CURVALUE` | Int | Current progress value (0-100) |
| `MAXVALUE` | Int | Maximum value (typically 100) |
| `STARTFROMLEFT` | Byte | Fill direction (0=right, 1=left) |

**ProgressBar Behavior:**

- **CURVALUE**: Current progress (0-100, or 0-MAXVALUE)
- **STARTFROMLEFT**: When 1, fills left-to-right; when 0, fills right-to-left
- Progress = (CURVALUE / MAXVALUE) × width

**PROGRESS Struct:**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `CORNER` | ResRef | Corner texture for progress fill |
| `EDGE` | ResRef | Edge texture for progress fill |
| `FILL` | ResRef | Fill texture for progress bar |
| `FILLSTYLE` | Int | Fill rendering style |
| `DIMENSION` | Int | Border thickness |
| `INNEROFFSET` | Int | Inner padding X-axis |
| `INNEROFFSETY` | Int | Inner padding Y-axis (optional) |
| `COLOR` | Vector | Progress fill color modulation |
| `PULSING` | Byte | Pulsing animation flag |

**CheckBox (Type 7):**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `SELECTED` | Struct | Appearance when checked |
| `HILIGHTSELECTED` | Struct | Appearance when checked and hovered |
| `ISSELECTED` | Byte | Default checked state (0=unchecked, 1=checked) |

**CheckBox Behavior:**

- Toggles between checked/unchecked on click
- **ISSELECTED**: Initial state
- **SELECTED**: Visual appearance when checked
- **HILIGHTSELECTED**: Visual appearance when checked and hovered

**Slider (Type 8):**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `THUMB` | Struct | Slider thumb appearance |
| `CURVALUE` | Int | Current slider value |
| `MAXVALUE` | Int | Maximum slider value |
| `DIRECTION` | Int | Orientation (0=horizontal, 1=vertical) |

**Slider Behavior:**

- **CURVALUE**: Current position (0 to MAXVALUE)
- **MAXVALUE**: Maximum value (typically 100)
- **DIRECTION**: 0=horizontal (left-right), 1=vertical (top-bottom)
- Thumb position = (CURVALUE / MAXVALUE) × track length

**Slider THUMB Struct:**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `IMAGE` | ResRef | Thumb texture |
| `ALIGNMENT` | Int | Image alignment |
| `DRAWSTYLE` | Int | Drawing style (unused) |
| `FLIPSTYLE` | Int | Flip/rotation style (unused) |
| `ROTATE` | Float | Rotation angle (unused) |

**Button (Type 6):**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `HILIGHT` | Struct | Hover state appearance |
| `MOVETO` | Struct | D-pad navigation targets |
| `TEXT` | Struct | Button label text |

**Button Behavior:**

- Clickable control with text label
- **HILIGHT**: Shown on mouse hover
- **TEXT**: Button label (can use STRREF for localization)
- **MOVETO**: Keyboard/D-pad navigation

**Label (Type 5):**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TEXT` | Struct | Text display properties |

**Label Behavior:**

- Static text display (non-interactive)
- **TEXT**: Text content, font, alignment, color
- Used for UI labels, descriptions, headers

**Panel (Type 2):**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `CONTROLS` | List | Child controls list |
| `BORDER` | Struct | Panel border (optional background) |
| `COLOR` | Vector | Panel color modulation |
| `ALPHA` | Float | Panel transparency |

**Panel Behavior:**

- Container for child controls
- **CONTROLS**: List of child controls (any type)
- **BORDER**: Optional background/border
- Child controls positioned relative to panel

**ProtoItem (Type 4):**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TEXT` | Struct | Item label text |
| `BORDER` | Struct | Item border appearance |
| `HILIGHT` | Struct | Item highlight on hover |
| `HILIGHTSELECTED` | Struct | Item highlight when selected |
| `SELECTED` | Struct | Item appearance when selected |
| `ISSELECTED` | Byte | Default selected state |

**ProtoItem Behavior:**

- Template for list items (used by ListBox)
- Defines appearance of individual list entries
- **ISSELECTED**: Initial selection state
- States: Normal, Highlighted, Selected, Highlighted+Selected

#### Implementation Notes

**Control Hierarchy:**

- GUI root contains `CONTROLS` list of top-level controls
- Controls can have child controls via `CONTROLS` list
- Child controls positioned relative to parent's EXTENT
- Parent visibility affects children (hidden parent hides children)
- Z-order: Children render above parents, later controls render above earlier ones (rendering order determined by control list order)

**Reference**: [`vendor/reone/src/libs/gui/gui.cpp:80-92`](https://github.com/th3w1zard1/reone/blob/master/src/libs/gui/gui.cpp#L80-L92) shows children are added to parent controls, and [`vendor/reone/src/libs/gui/control.cpp:192-194`](https://github.com/th3w1zard1/reone/blob/master/src/libs/gui/control.cpp#L192-L194) shows children are updated/rendered in order

**Positioning System:**

- Base resolution: 640×480 pixels (engine default, scaled for higher resolutions)
- Coordinates are pixel-based, engine scales for higher resolutions
- EXTENT.LEFT/TOP: Position relative to parent (or screen for root)
- Negative coordinates allowed (positioning outside parent bounds)
- Root control EXTENT defines GUI bounds

**Reference**: [`vendor/reone/include/reone/gui/gui.h:38-39`](https://github.com/th3w1zard1/reone/blob/master/include/reone/gui/gui.h#L38-L39) defines `kDefaultResolutionX = 640` and `kDefaultResolutionY = 480`

**Color System:**

- **COLOR** (Vector3): RGB color modulation (0.0-1.0 range)
- **ALPHA** (Float): Transparency (0.0=transparent, 1.0=opaque)
- Colors multiply with textures (white=full color, black=no color)
- KotOR 1 default text color: RGB(0.0, 0.659, 0.980) - cyan
- KotOR 2 default text color: RGB(0.102, 0.698, 0.549) - teal (exact values from engine)
- Default highlight color: RGB(1.0, 1.0, 0.0) - yellow

**Reference**: [`vendor/KotOR.js/src/gui/GUIControl.ts:188-194`](https://github.com/KobaltBlu/KotOR.js/blob/master/src/gui/GUIControl.ts#L188-L194) defines default colors for KotOR 1 and 2

**Border Rendering:**

- Border consists of 9 pieces: 4 corners, 4 edges, 1 fill
- CORNER textures: Top-left, top-right, bottom-left, bottom-right
- EDGE textures: Top, right, bottom, left (tiled along length)
- FILL texture: Center area (scaled or tiled based on FILLSTYLE)
- DIMENSION: Thickness of border edges in pixels
- INNEROFFSET: Padding between border and content

**Text Rendering:**

- Fonts are texture-based (TPC/TGA files with character grid)
- Each character has fixed width/height in font texture
- TEXT field takes precedence over STRREF if both set
- STRREF references dialog.tlk for localized strings
- ALIGNMENT uses bitfield: horizontal (1=left, 2=center, 3=right) + vertical (0=top, 16=center, 32=bottom)
- Text color modulates font texture

**State Management:**

- **Normal**: BORDER struct defines appearance
- **Hover**: HILIGHT struct overlays/replaces BORDER
- **Selected**: SELECTED struct defines appearance (CheckBox, ListBox items)
- **Hover+Selected**: HILIGHTSELECTED struct (highest priority)
- State transitions handled automatically by engine

**Control IDs:**

- **ID** field: Unique identifier for script references
- Control IDs are used by scripts and engine systems to locate specific controls
- Some engine behaviors may depend on specific Control IDs or Tags
- IDs should remain stable across GUI versions to maintain script compatibility

**Note**: While control IDs are used extensively for script references, explicit evidence of hardcoded ID dependencies in the engine is not found in vendor implementations. However, control tags (TAG field) are commonly used for engine lookups.

**Navigation:**

- **MOVETO** struct defines D-pad/keyboard navigation
- Value is Control ID of target control
- -1 or 0 indicates no navigation in that direction
- Engine handles wrapping at list boundaries
- Essential for controller/keyboard-only gameplay

**ScrollBar Integration:**

- ListBox controls can embed SCROLLBAR
- ScrollBar.MAXVALUE = total items - visible items
- ScrollBar.VISIBLEVALUE = number of visible items
- ScrollBar.CURVALUE = current scroll offset
- Thumb size = (VISIBLEVALUE / MAXVALUE) × track length
- LEFTSCROLLBAR: Positions scrollbar on left side

**Pulsing Animation:**

- **PULSING** flag in BORDER, TEXT, HILIGHT, SELECTED structs
- When enabled, control pulses (fades in/out)
- Used for attention-grabbing effects
- Animation speed controlled by engine

**Texture Formats:**

- GUI textures use TPC (Targa Packed) or TGA format
- Textures often have alpha channels for transparency
- Border pieces designed to tile seamlessly
- Font textures contain character glyphs in fixed grid

**Performance Considerations:**

- Complex GUIs with many controls impact rendering
- Nested controls increase draw calls
- Large texture borders increase memory usage
- Pulsing animations require per-frame updates

**Common Patterns:**

- **Main Menu**: Root Panel with Button controls
- **Dialogue**: Panel with Label (message) and ListBox (replies)
- **Inventory**: ListBox with ProtoItem template
- **Character Sheet**: Panel with multiple Label and Button controls
- **Options Menu**: Panel with Slider and CheckBox controls

**KotOR-Specific Notes:**

- GUIs are loaded from `.gui` files (GFF format)
- Engine scales GUIs for different resolutions
- Some controls have hardcoded behaviors (e.g., inventory slots)
- Scripts can access controls by TAG or ID
- GUI state can be modified at runtime via scripts

### IFO (Module Info)

IFO files define module-level metadata including entry configuration, expansion requirements, area lists, and module-wide script hooks. IFO files are the "main" descriptor for game modules, specifying where the player spawns and what scripts run at module scope.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/ifo.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/ifo.py)

#### Core Module Identity

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Mod_ID` | Void (16 bytes) | Unique module identifier (GUID) |
| `Mod_Tag` | CExoString | Module tag identifier |
| `Mod_Name` | CExoLocString | Module name (localized) |
| `Mod_Creator_ID` | DWord | Toolset creator ID |
| `Mod_Version` | DWord | Module version number |
| `Mod_VO_ID` | CExoString | Voice-over folder name |

**Module Identification:**

- **Mod_ID**: 16-byte GUID generated by toolset
- **Mod_Tag**: Script-accessible identifier
- **Mod_Name**: Displayed in load screens
- **Mod_VO_ID**: Subfolder in StreamVoice for voice files

#### Entry Configuration

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Mod_Entry_Area` | ResRef | Starting area ResRef |
| `Mod_Entry_X` | Float | Entry X coordinate |
| `Mod_Entry_Y` | Float | Entry Y coordinate |
| `Mod_Entry_Z` | Float | Entry Z coordinate |
| `Mod_Entry_Dir_X` | Float | Entry direction X (facing) |
| `Mod_Entry_Dir_Y` | Float | Entry direction Y (facing) |

**Player Spawn:**

- **Mod_Entry_Area**: Initial area to load (ARE/GIT)
- **Entry Position**: XYZ coordinates in world space
- **Entry Direction**: Player's initial facing angle
  - Direction computed as: `atan2(Dir_Y, Dir_X)`

**Module Start Sequence:**

1. Load IFO to get entry configuration
2. Load Mod_Entry_Area (ARE + GIT)
3. Spawn player character at Entry position
4. Set player orientation from Entry direction
5. Execute Mod_OnModStart script

#### Area List

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Mod_Area_list` | List | Areas in this module |

**Mod_Area_list Struct Fields:**

- `Area_Name` (ResRef): Area ResRef (ARE file)

**Area Management:**

- Lists all areas accessible in module
- Areas loaded on-demand as player transitions
- KotOR modules typically have 1 area per module
- KotOR2 can have multiple areas per module

#### Expansion Pack Requirements

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Expansion_Pack` | Word | Required expansion bitfield |
| `Mod_MinGameVer` | CExoString | Minimum game version |

**Expansion Flags (Bitfield):**

- **0x01**: Requires expansion pack 1
- **0x02**: Requires expansion pack 2
- Additional bits for future expansions

**Version Requirements:**

- **Mod_MinGameVer**: Minimum executable version
- Prevents loading in older game versions
- Format: "1.0", "1.03", "2.0", etc.

#### Starting Movie & HAK Files

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Mod_StartMovie` | ResRef | Starting movie file |
| `Mod_Hak` | CExoString | Required HAK file list |

**Module Initialization:**

- **Mod_StartMovie**: BIK movie played before module loads
- **Mod_Hak**: Semicolon-separated HAK file names
- HAKs loaded before module resources

**HAK System:**

- HAK files override base game resources
- Custom content (models, textures, scripts)
- Listed in load priority order

#### Cache & XP Settings

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Mod_IsSaveGame` | Byte | Module is from save file |
| `Mod_CacheNSSData` | Byte | Cache compiled scripts |
| `Mod_XPScale` | Byte | Experience point multiplier (0-200%) |

**Module Flags:**

- **Mod_IsSaveGame**: Internal flag (always 0 in files)
- **Mod_CacheNSSData**: Performance optimization
- **Mod_XPScale**: 100 = normal, 200 = double XP

#### DawnStar Property (Unused)

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Mod_DawnHour` | Byte | Dawn start hour (unused) |
| `Mod_DuskHour` | Byte | Dusk start hour (unused) |
| `Mod_MinPerHour` | DWord | Minutes per hour (unused) |

**Day/Night Cycle:**

- Defined but unused in KotOR
- Intended for time-based events
- No dynamic lighting/NPC schedules

#### Module Script Hooks

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Mod_OnAcquirItem` | ResRef | Fires when item acquired |
| `Mod_OnActvtItem` | ResRef | Fires when item activated/used |
| `Mod_OnClientEntr` | ResRef | Fires on player enter (multiplayer) |
| `Mod_OnClientLeav` | ResRef | Fires on player leave (multiplayer) |
| `Mod_OnCutsnAbort` | ResRef | Fires when cutscene aborted |
| `Mod_OnHeartbeat` | ResRef | Fires periodically (~6 seconds) |
| `Mod_OnModLoad` | ResRef | Fires when module finishes loading |
| `Mod_OnModStart` | ResRef | Fires after player spawned |
| `Mod_OnPlrDeath` | ResRef | Fires when player dies |
| `Mod_OnPlrDying` | ResRef | Fires when player HP reaches 0 |
| `Mod_OnPlrEqItm` | ResRef | Fires when equipment changed |
| `Mod_OnPlrLvlUp` | ResRef | Fires on level up |
| `Mod_OnPlrRest` | ResRef | Fires when player rests |
| `Mod_OnPlrUnEqItm` | ResRef | Fires when equipment removed |
| `Mod_OnSpawnBtnDn` | ResRef | Fires on spawn button (multiplayer) |
| `Mod_OnUnAqreItem` | ResRef | Fires when item lost/sold |
| `Mod_OnUsrDefined` | ResRef | Fires on user-defined events |

**Script Execution:**

- Module scripts run in module context
- Can access/modify module-wide state
- Higher scope than area scripts

**Common Script Uses:**

**Mod_OnModLoad:**

- Initialize global variables
- Setup persistent data structures
- Load saved state

**Mod_OnModStart:**

- Start cinematics
- Give starting equipment
- Setup initial conversations

**Mod_OnHeartbeat:**

- Update timers
- Check global conditions
- Ambient system updates

**Mod_OnPlrDeath:**

- Game over sequence
- Respawn handling
- Load last save

#### Implementation Notes

**Module Loading Sequence:**

1. **Read IFO**: Parse module metadata
2. **Check Requirements**: Verify Expansion_Pack and MinGameVer
3. **Load HAKs**: Mount HAK files in order
4. **Play Movie**: Show Mod_StartMovie if set
5. **Load Entry Area**: Read ARE + GIT for Mod_Entry_Area
6. **Spawn Player**: Place at Entry position/direction
7. **Fire OnModLoad**: Execute module load script
8. **Fire OnModStart**: Execute module start script
9. **Start Gameplay**: Enable player control

**IFO vs. ARE vs. GIT:**

- **IFO**: Module-level metadata and entry config
- **ARE**: Static area properties (lighting, fog, grass)
- **GIT**: Dynamic object instances (creatures, doors, etc.)

**Save Game Integration:**

- IFO saved with current state
- Entry position updated to save location
- Module scripts preserved
- Mod_IsSaveGame flag set

**Module Transitions:**

- When transitioning to new module:
  1. Current module IFO updated with player position
  2. Current module saved to save game
  3. New module IFO loaded
  4. Player spawned at new Entry position (or LinkedTo waypoint)

**Multi-Area Modules (KotOR2):**

- Mod_Area_list contains multiple areas
- Areas loaded as needed
- Transitions within module don't fire OnModStart
- Shared module-level state

**Single-Area Modules (KotOR1):**

- Typical KotOR1 pattern
- One area per IFO
- Module transition = area transition
- Simpler resource management

**Script Scope Hierarchy:**

1. **Module Scripts** (IFO): Highest scope, module-wide
2. **Area Scripts** (ARE): Area-specific events
3. **Object Scripts** (UTC/UTD/etc.): Individual object events

**Common Module Configurations:**

**Story Modules:**

- Specific entry position for narrative flow
- StartMovie for cinematics
- OnModStart for dialogue/cutscenes
- Custom HAKs for unique content

**Hub Modules:**

- Central entry position (hub center)
- Multiple area transitions
- Vendors, NPCs, quest givers
- No start movie typically

**Combat Modules:**

- Entry position near enemies
- OnModStart spawns for ambush
- Battle music configured
- XPScale adjusted for difficulty

**Tutorial Modules:**

- Guided entry position
- OnModStart tutorial dialogue
- Reduced XPScale
- Special script hooks for teaching mechanics

### JRL (Journal)

JRL files define the structure of the player's quest journal. They organize quests into categories and track progress through individual entries.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/jrl.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/jrl.py)

#### Quest Structure

JRL files contain a list of `Categories` (Quests), each containing a list of `EntryList` (States).

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Categories` | List | List of quests |

#### Quest Category (JRLQuest)

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Tag` | CExoString | Unique quest identifier |
| `Name` | CExoLocString | Quest title |
| `Comment` | CExoString | Developer comment |
| `Priority` | Int | Sorting priority (0=Highest, 4=Lowest) |
| `PlotIndex` | Int | Legacy plot index |
| `PlanetID` | Int | Planet association (unused) |
| `EntryList` | List | List of quest states |

**Priority Levels:**

- **0 (Highest)**: Main quest line
- **1 (High)**: Important side quests
- **2 (Medium)**: Standard side quests
- **3 (Low)**: Minor tasks
- **4 (Lowest)**: Completed/Archived

#### Quest Entry (JRLEntry)

| Field | Type | Description |
| ----- | ---- | ----------- |
| `ID` | Int | State identifier (referenced by scripts/dialogue) |
| `Text` | CExoLocString | Journal text displayed for this state |
| `End` | Byte | 1 if this state completes the quest |
| `XP_Percentage` | Float | XP reward multiplier for reaching this state |

**Quest Updates:**

- Scripts use `AddJournalQuestEntry("Tag", ID)` to update quests.
- Dialogues use `Quest` and `QuestEntry` fields.
- Only the highest ID reached is typically displayed (unless `AllowOverrideHigher` is set in `global.jrl` logic).
- `End=1` moves the quest to the "Completed" tab.

#### Implementation Notes

- **global.jrl**: The master journal file for the entire game.
- **Module JRLs**: Not typically used; most quests are global.
- **XP Rewards**: `XP_Percentage` scales the `journal.2da` XP value for the quest.

---

### PTH (Path)

PTH files define pathfinding data for modules, distinct from the navigation mesh (walkmesh). They store a network of waypoints and connections used for high-level AI navigation planning.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/pth.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/pth.py)

#### Path Points

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Path_Points` | List | List of navigation nodes |

**Path_Points Struct Fields:**

- `X` (Float): X Coordinate
- `Y` (Float): Y Coordinate
- `Z` (Float): Z Coordinate (unused/flat)

#### Path Connections

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Path_Connections` | List | List of edges between nodes |

**Path_Connections Struct Fields:**

- `Path_Source` (Int): Index of source point
- `Path_Dest` (Int): Index of destination point

#### Usage

- **AI Navigation**: Used by NPCs to plot paths across large distances or complex areas where straight-line walkmesh navigation fails.
- **Legacy Support**: Often redundant in modern engines with navigation meshes, but used in Aurora/Odyssey for optimization.
- **Editor**: Visualized as a web of lines connecting nodes.

---

### UTC (Creature)

UTC files define creature templates including NPCs, party members, enemies, and the player character. They are comprehensive GFF files containing all data needed to spawn and control a creature in the game world.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py)

#### Core Identity Fields

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | ResRef | Template identifier for this creature |
| `Tag` | CExoString | Unique tag for script/conversation references |
| `FirstName` | CExoLocString | Creature's first name (localized) |
| `LastName` | CExoLocString | Creature's last name (localized) |
| `Comment` | CExoString | Developer comment/notes |

#### Appearance & Visuals

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Appearance_Type` | DWord | Index into `appearance.2da` |
| `PortraitId` | Word | Index into `portraits.2da` |
| `Gender` | Byte | 0=Male, 1=Female, 2=Both, 3=Other, 4=None |
| `Race` | Word | Index into `racialtypes.2da` |
| `SubraceIndex` | Byte | Subrace identifier |
| `BodyVariation` | Byte | Body model variation (0-9) |
| `TextureVar` | Byte | Texture variation (1-9) |
| `SoundSetFile` | Word | Index into sound set table |

#### Core Stats & Attributes

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Str` | Byte | Strength score (3-255) |
| `Dex` | Byte | Dexterity score (3-255) |
| `Con` | Byte | Constitution score (3-255) |
| `Int` | Byte | Intelligence score (3-255) |
| `Wis` | Byte | Wisdom score (3-255) |
| `Cha` | Byte | Charisma score (3-255) |
| `HitPoints` | Short | Current hit points |
| `CurrentHitPoints` | Short | Alias for hit points |
| `MaxHitPoints` | Short | Maximum hit points |
| `ForcePoints` | Short | Current Force points (KotOR specific) |
| `CurrentForce` | Short | Alias for Force points |
| `MaxForcePoints` | Short | Maximum Force points |

#### Character Progression

| Field | Type | Description |
| ----- | ---- | ----------- |
| `ClassList` | List | List of character classes with levels |
| `Experience` | DWord | Total experience points |
| `LevelUpStack` | List | Pending level-up choices |
| `SkillList` | List | Skill ranks (index + rank) |
| `FeatList` | List | Acquired feats |
| `SpecialAbilityList` | List | Special abilities/powers |

**ClassList Struct Fields:**

- `Class` (Int): Index into `classes.2da`
- `ClassLevel` (Short): Levels in this class

**SkillList Struct Fields:**

- `Rank` (Byte): Skill rank value

**FeatList Struct Fields:**

- `Feat` (Word): Index into `feat.2da`

#### Combat & Behavior

| Field | Type | Description |
| ----- | ---- | ----------- |
| `FactionID` | Word | Faction identifier (determines hostility) |
| `NaturalAC` | Byte | Natural armor class bonus |
| `ChallengeRating` | Float | CR for encounter calculations |
| `PerceptionRange` | Byte | Perception distance category |
| `WalkRate` | Int | Movement speed identifier |
| `Interruptable` | Byte | Can be interrupted during actions |
| `NoPermDeath` | Byte | Cannot permanently die |
| `IsPC` | Byte | Is player character |
| `Plot` | Byte | Plot-critical (cannot die) |
| `MinOneHP` | Byte | Cannot drop below 1 HP |
| `PartyInteract` | Byte | Shows party selection interface |
| `Hologram` | Byte | Rendered as hologram |

#### Equipment & Inventory

| Field | Type | Description |
| ----- | ---- | ----------- |
| `ItemList` | List | Inventory items |
| `Equip_ItemList` | List | Equipped items with slots |
| `EquippedRes` | ResRef | Deprecated equipment field |

**ItemList Struct Fields:**

- `InventoryRes` (ResRef): UTI template ResRef
- `Repos_PosX` (Word): Inventory grid X position
- `Repos_Posy` (Word): Inventory grid Y position
- `Dropable` (Byte): Can be dropped/removed

**Equip_ItemList Struct Fields:**

- `EquippedRes` (ResRef): UTI template ResRef
- Equipment slots reference `equipmentslots.2da`

#### Script Hooks

| Field | Type | Description |
| ----- | ---- | ----------- |
| `ScriptAttacked` | ResRef | Fires when attacked |
| `ScriptDamaged` | ResRef | Fires when damaged |
| `ScriptDeath` | ResRef | Fires on death |
| `ScriptDialogue` | ResRef | Fires when conversation starts |
| `ScriptDisturbed` | ResRef | Fires when inventory disturbed |
| `ScriptEndRound` | ResRef | Fires at combat round end |
| `ScriptEndDialogue` | ResRef | Fires when conversation ends |
| `ScriptHeartbeat` | ResRef | Fires periodically |
| `ScriptOnBlocked` | ResRef | Fires when movement blocked |
| `ScriptOnNotice` | ResRef | Fires when notices something |
| `ScriptRested` | ResRef | Fires after rest |
| `ScriptSpawn` | ResRef | Fires on spawn |
| `ScriptSpellAt` | ResRef | Fires when spell cast at creature |
| `ScriptUserDefine` | ResRef | Fires on user-defined events |

#### KotOR-Specific Features

**Alignment:**

- `GoodEvil` (Byte): 0-100 scale (0=Dark, 100=Light)
- `LawfulChaotic` (Byte): Unused in KotOR

**Multiplayer (Unused in KotOR):**

- `Deity` (CExoString)
- `Subrace` (CExoString)
- `Morale` (Byte)
- `MorealBreak` (Byte)

**Special Abilities:**

- Stored in `SpecialAbilityList` referencing `spells.2da` or feat-based abilities

#### Implementation Notes

UTC files are loaded during module initialization or creature spawning. The engine:

1. **Reads template data** from the UTC GFF structure
2. **Applies appearance** based on `appearance.2da` lookup
3. **Calculates derived stats** (AC, saves, attack bonuses) from attributes and equipment
4. **Loads inventory** by instantiating UTI templates
5. **Applies effects** from equipped items and active powers
6. **Registers scripts** for the creature's event handlers

**Performance Considerations:**

- Complex creatures with many items/feats increase load time
- Script hooks fire frequently - keep handlers optimized
- Large SkillList/FeatList structures add memory overhead

**Common Use Cases:**

- **Party Members**: Full UTC with all progression data, complex equipment
- **Plot NPCs**: Basic stats, specific appearance, dialogue scripts
- **Generic Enemies**: Minimal data, shared appearance, basic AI scripts
- **Vendors**: Specialized with store inventory, merchant scripts
- **Placeables As Creatures**: Invisible creatures for complex scripting

### UTD (Door)

UTD files define door templates for all interactive doors in the game world. Doors can be locked, require keys, have hit points, conversations, and various gameplay interactions.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/utd.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utd.py)

#### Core Identity Fields

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | ResRef | Template identifier for this door |
| `Tag` | CExoString | Unique tag for script references |
| `LocName` | CExoLocString | Door name (localized) |
| `Description` | CExoLocString | Door description |
| `Comment` | CExoString | Developer comment/notes |

#### Door Appearance & Type

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Appearance` | DWord | Index into `genericdoors.2da` |
| `GenericType` | DWord | Generic door type category |
| `AnimationState` | Byte | Current animation state (always 0 in templates) |

**Appearance System:**

- `genericdoors.2da` defines door models and animations
- Different appearance types support different behaviors
- Opening animation determined by appearance entry

#### Locking & Security

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Locked` | Byte | Door is currently locked |
| `Lockable` | Byte | Door can be locked/unlocked |
| `KeyRequired` | Byte | Requires specific key item |
| `KeyName` | CExoString | Tag of required key item |
| `AutoRemoveKey` | Byte | Key consumed on use |
| `OpenLockDC` | Byte | Security skill DC to pick lock |
| `CloseLockDC` (KotOR2) | Byte | Security skill DC to lock door |

**Lock Mechanics:**

- **Locked**: Door cannot be opened normally
- **KeyRequired**: Must have key in inventory
- **OpenLockDC**: Player rolls Security skill vs. DC
- **AutoRemoveKey**: Key destroyed after successful use

#### Hit Points & Durability

| Field | Type | Description |
| ----- | ---- | ----------- |
| `HP` | Short | Maximum hit points |
| `CurrentHP` | Short | Current hit points |
| `Hardness` | Byte | Damage reduction |
| `Min1HP` (KotOR2) | Byte | Cannot drop below 1 HP |
| `Fort` | Byte | Fortitude save (always 0) |
| `Ref` | Byte | Reflex save (always 0) |
| `Will` | Byte | Will save (always 0) |

**Destructible Doors:**

- Doors with HP can be attacked and destroyed
- **Hardness** reduces each hit's damage
- **Min1HP** prevents destruction (plot doors)
- Save values unused in KotOR

#### Interaction & Behavior

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Plot` | Byte | Plot-critical (cannot be destroyed) |
| `Static` | Byte | Door is static geometry (no interaction) |
| `Interruptable` | Byte | Opening can be interrupted |
| `Conversation` | ResRef | Dialog file when used |
| `Faction` | Word | Faction identifier |
| `AnimationState` | Byte | Starting animation (0=closed, other values unused) |

**Conversation Doors:**

- When clicked, triggers dialogue instead of opening
- Useful for password entry, NPC interactions
- Dialog can conditionally open door via script

#### Script Hooks

| Field | Type | Description |
| ----- | ---- | ----------- |
| `OnOpen` | ResRef | Fires when door opens |
| `OnClose` | ResRef | Fires when door closes |
| `OnClosed` | ResRef | Fires after door finishes closing |
| `OnDamaged` | ResRef | Fires when door takes damage |
| `OnDeath` | ResRef | Fires when door is destroyed |
| `OnDisarm` | ResRef | Fires when trap is disarmed |
| `OnHeartbeat` | ResRef | Fires periodically |
| `OnLock` | ResRef | Fires when door is locked |
| `OnMeleeAttacked` | ResRef | Fires when attacked in melee |
| `OnSpellCastAt` | ResRef | Fires when spell cast at door |
| `OnUnlock` | ResRef | Fires when door is unlocked |
| `OnUserDefined` | ResRef | Fires on user-defined events |
| `OnClick` | ResRef | Fires when clicked |
| `OnFailToOpen` (KotOR2) | ResRef | Fires when opening fails |

#### Trap System

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TrapDetectable` | Byte | Trap can be detected |
| `TrapDetectDC` | Byte | Awareness DC to detect trap |
| `TrapDisarmable` | Byte | Trap can be disarmed |
| `DisarmDC` | Byte | Security DC to disarm trap |
| `TrapFlag` | Byte | Trap is active |
| `TrapOneShot` | Byte | Trap triggers only once |
| `TrapType` | Byte | Index into `traps.2da` |

**Trap Mechanics:**

1. **Detection**: Player rolls Awareness vs. `TrapDetectDC`
2. **Disarm**: Player rolls Security vs. `DisarmDC`
3. **Trigger**: If not detected/disarmed, trap fires on door use
4. **One-Shot**: Trap disabled after first trigger

#### Load-Bearing Doors (KotOR2)

| Field | Type | Description |
| ----- | ---- | ----------- |
| `LoadScreenID` (KotOR2) | Word | Loading screen to show |
| `LinkedTo` (KotOR2) | CExoString | Destination module tag |
| `LinkedToFlags` (KotOR2) | Byte | Transition behavior flags |
| `LinkedToModule` (KotOR2) | ResRef | Destination module ResRef |
| `TransitionDestin` (KotOR2) | CExoLocString | Destination label |

**Transition System:**

- Doors can load new modules/areas
- Loading screen displayed during transition
- Linked destination defines spawn point

#### Appearance Customization

| Field | Type | Description |
| ----- | ---- | ----------- |
| `PortraitId` | Word | Portrait icon identifier |
| `PaletteID` | Byte | Toolset palette category |

**Visual Representation:**

- `Appearance` determines 3D model
- Some doors have customizable textures
- Portrait used in UI elements

#### Implementation Notes

**Door State Machine:**

Doors maintain runtime state:

1. **Closed**: Default state, blocking
2. **Opening**: Animation playing, becoming non-blocking
3. **Open**: Fully open, non-blocking
4. **Closing**: Animation playing, becoming blocking
5. **Locked**: Closed and cannot open
6. **Destroyed**: Hit points depleted, permanently open

**Opening Sequence:**

1. Player clicks door
2. If conversation set, start dialog
3. If locked, check for key or Security skill
4. If trapped, check for detection/disarm
5. Fire `OnOpen` script
6. Play opening animation
7. Transition to "open" state

**Locking System:**

- **Lockable=0**: Door cannot be locked (always opens)
- **Locked=1, KeyRequired=1**: Must have specific key
- **Locked=1, OpenLockDC>0**: Can pick lock with Security skill
- **Locked=1, KeyRequired=0, OpenLockDC=0**: Locked via script only

**Common Door Types:**

**Standard Doors:**

- Simple open/close
- No lock, HP, or trap
- Used for interior navigation

**Locked Doors:**

- Requires key or Security skill
- Quest progression gates
- May have conversation for passwords

**Destructible Doors:**

- Have HP and Hardness
- Can be bashed down
- Alternative to lockpicking

**Trapped Doors:**

- Trigger trap on opening
- Require detection and disarming
- Often in hostile areas

**Transition Doors:**

- Load new modules/areas
- Show loading screens
- Used for major location changes

**Conversation Doors:**

- Trigger dialog on click
- May open after conversation
- Used for password entry, riddles

### UTE (Encounter)

UTE files define encounter templates which spawn creatures when triggered by the player. Encounters handle spawning logic, difficulty scaling, respawning, and faction settings for groups of enemies or neutral creatures.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/ute.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/ute.py)

#### Core Identity Fields

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | ResRef | Template identifier for this encounter |
| `Tag` | CExoString | Unique tag for script references |
| `LocalizedName` | CExoLocString | Encounter name (unused in game) |
| `Comment` | CExoString | Developer comment/notes |

#### Spawn Configuration

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Active` | Byte | Encounter is currently active |
| `Difficulty` | Int | Difficulty setting (unused) |
| `DifficultyIndex` | Int | Difficulty scaling index |
| `Faction` | Word | Faction of spawned creatures |
| `MaxCreatures` | Int | Maximum concurrent creatures |
| `RecCreatures` | Int | Recommended number of creatures |
| `SpawnOption` | Int | Spawn behavior (0=Continuous, 1=Single Shot) |

**Spawn Behavior:**

- **Active**: If 0, encounter won't trigger until activated by script
- **MaxCreatures**: Hard limit on spawned entities to prevent overcrowding
- **RecCreatures**: Target number to maintain
- **SpawnOption**: Single Shot encounters fire once and disable

#### Respawn Logic

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Reset` | Byte | Encounter resets after being cleared |
| `ResetTime` | Int | Time in seconds before reset |
| `Respawns` | Int | Number of times it can respawn (-1 = infinite) |

**Respawn System:**

- Allows for renewable enemy sources
- **ResetTime**: Cooldown period after players leave area
- **Respawns**: Limits farming/grinding

#### Creature List

| Field | Type | Description |
| ----- | ---- | ----------- |
| `CreatureList` | List | List of creatures to spawn |

**CreatureList Struct Fields:**

- `ResRef` (ResRef): UTC template to spawn
- `Appearance` (Int): Appearance type (optional override)
- `CR` (Float): Challenge Rating
- `SingleSpawn` (Byte): Unique spawn flag

**Spawn Selection:**

- Engine selects from CreatureList based on CR and difficulty
- Random selection weighted by difficulty settings

#### Trigger Logic

| Field | Type | Description |
| ----- | ---- | ----------- |
| `PlayerOnly` | Byte | Only triggers for player (not NPCs) |
| `OnEntered` | ResRef | Script fires when trigger entered |
| `OnExit` | ResRef | Script fires when trigger exited |
| `OnExhausted` | ResRef | Script fires when spawns depleted |
| `OnHeartbeat` | ResRef | Script fires periodically |
| `OnUserDefined` | ResRef | Script fires on user events |

**Implementation Notes:**

- Encounters are volumes (geometry defined in GIT)
- Spawning happens when volume is entered
- Creatures spawn at specific spawn points (UTW) or random locations

### UTI (Item)

UTI files define item templates for all objects in creature inventories, containers, and stores. Items range from weapons and armor to quest items, upgrades, and consumables.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/uti.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/uti.py)

#### Core Identity Fields

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | ResRef | Template identifier for this item |
| `Tag` | CExoString | Unique tag for script references |
| `LocalizedName` | CExoLocString | Item name (localized) |
| `Description` | CExoLocString | Generic description |
| `DescIdentified` | CExoLocString | Description when identified |
| `Comment` | CExoString | Developer comment/notes |

#### Base Item Configuration

| Field | Type | Description |
| ----- | ---- | ----------- |
| `BaseItem` | Int | Index into `baseitems.2da` (defines item type) |
| `Cost` | DWord | Base value in credits |
| `AddCost` | DWord | Additional cost from properties |
| `Plot` | Byte | Plot-critical item (cannot be sold/destroyed) |
| `Charges` | Byte | Number of uses remaining |
| `StackSize` | Word | Current stack quantity |
| `ModelVariation` | Byte | Model variation index (1-99) |
| `BodyVariation` | Byte | Body variation for armor (1-9) |
| `TextureVar` | Byte | Texture variation for armor (1-9) |

**BaseItem Types** (from `baseitems.2da`):

- **0-10**: Various weapon types (shortsword, longsword, blaster, etc.)
- **11-30**: Armor types and shields
- **31-50**: Quest items, grenades, medical supplies
- **51-70**: Upgrades, armbands, belts
- **71-90**: Droid equipment, special items
- **91+**: KotOR2-specific items

#### Item Properties

| Field | Type | Description |
| ----- | ---- | ----------- |
| `PropertiesList` | List | Item properties and enchantments |
| `Upgradable` | Byte | Can accept upgrades (KotOR1 only) |
| `UpgradeLevel` | Byte | Current upgrade tier (KotOR2 only) |

**PropertiesList Struct Fields:**

- `PropertyName` (Word): Index into `itempropdef.2da`
- `Subtype` (Word): Property subtype/category
- `CostTable` (Byte): Cost table index
- `CostValue` (Word): Cost value
- `Param1` (Byte): First parameter
- `Param1Value` (Byte): First parameter value
- `ChanceAppear` (Byte): Percentage chance to appear (random loot)
- `UsesPerDay` (Byte): Daily usage limit (0 = unlimited)
- `UsesLeft` (Byte): Remaining uses for today

**Common Item Properties:**

- **Attack Bonus**: +1 to +12 attack rolls
- **Damage Bonus**: Additional damage dice
- **Ability Bonus**: +1 to +12 to ability scores
- **Damage Resistance**: Reduce damage by amount/percentage
- **Saving Throw Bonus**: +1 to +20 to saves
- **Skill Bonus**: +1 to +50 to skills
- **Immunity**: Immunity to damage type or condition
- **On Hit**: Cast spell/effect on successful hit
- **Keen**: Expanded critical threat range
- **Massive Criticals**: Bonus damage on critical hit

#### Weapon-Specific Fields

| Field | Type | Description |
| ----- | ---- | ----------- |
| `WeaponColor` (KotOR2) | Byte | Blade color for lightsabers |
| `WeaponWhoosh` (KotOR2) | Byte | Whoosh sound type |

**Lightsaber Colors** (KotOR2 `WeaponColor`):

- 0: Blue, 1: Yellow, 2: Green, 3: Red
- 4: Violet, 5: Orange, 6: Cyan, 7: Silver
- 8: White, 9: Viridian, 10: Bronze

#### Armor-Specific Fields

| Field | Type | Description |
| ----- | ---- | ----------- |
| `BodyVariation` | Byte | Body model variation (1-9) |
| `TextureVar` | Byte | Texture variation (1-9) |
| `ModelVariation` | Byte | Model type (typically 1-3) |
| `ArmorRulesType` (KotOR2) | Byte | Armor class category |

**Armor Model Variations:**

- **Body + Texture Variation**: Creates visual diversity
- Armor adapts to wearer's body type and gender
- `appearance.2da` defines valid combinations

#### Quest & Special Items

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Plot` | Byte | Cannot be sold or destroyed |
| `Stolen` | Byte | Marked as stolen |
| `Cursed` | Byte | Cannot be unequipped |
| `Identified` | Byte | Player has identified the item |

**Plot Item Behavior:**

- Immune to destruction/selling
- Often required for quest completion
- Can have special script interactions

#### Upgrade System (KotOR1)

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Upgradable` | Byte | Item accepts upgrade items |

**Upgrade Mechanism:**

- Weapon/armor can have upgrade slots
- Player applies upgrade items to base item
- Properties from upgrade merge into base
- Referenced in `upgradetypes.2da`

#### Upgrade System (KotOR2 Enhanced)

| Field | Type | Description |
| ----- | ---- | ----------- |
| `UpgradeLevel` | Byte | Current upgrade tier (0-2) |
| `WeaponColor` | Byte | Lightsaber blade color |
| `WeaponWhoosh` | Byte | Swing sound type |
| `ArmorRulesType` | Byte | Armor restriction category |

**KotOR2 Upgrade Slots:**

- Weapons can have multiple upgrade slots
- Each slot has specific type restrictions
- Lightsabers get color customization
- Armor upgrades affect appearance

#### Visual & Audio

| Field | Type | Description |
| ----- | ---- | ----------- |
| `ModelVariation` | Byte | Base model index |
| `BodyVariation` | Byte | Body model for armor |
| `TextureVar` | Byte | Texture variant |

**Model Resolution:**

1. Engine looks up `BaseItem` in `baseitems.2da`
2. Retrieves model prefix (e.g., `w_lghtsbr`)
3. Appends variations: `w_lghtsbr_001.mdl`
4. Textures follow similar pattern

#### Palette & Editor

| Field | Type | Description |
| ----- | ---- | ----------- |
| `PaletteID` | Byte | Toolset palette category |
| `Comment` | CExoString | Designer notes/documentation |

**Toolset Integration:**

- `PaletteID` organizes items in editor
- Does not affect gameplay
- Used for content creation workflow

#### Implementation Notes

**Item Instantiation:**

1. **Template Loading**: GFF structure parsed from UTI
2. **Property Application**: PropertiesList merged into item
3. **Cost Calculation**: Base cost + AddCost + property costs
4. **Visual Setup**: Model/texture variants resolved
5. **Stack Handling**: StackSize determines inventory behavior

**Property System:**

- Properties defined in `itempropdef.2da`
- Each property has cost formula
- Properties stack or override based on type
- Engine recalculates effects when equipped

**Performance Optimization:**

- Simple items (no properties) load fastest
- Complex property lists increase spawn time
- Stack-based items share template data
- Unique items (non-stackable) require instance data

**Common Item Categories:**

**Weapons:**

- Melee: lightsabers, swords, vibroblades
- Ranged: blasters, rifles, heavy weapons
- Properties: damage, attack bonus, critical

**Armor:**

- Light, Medium, Heavy classes
- Robes (Force user specific)
- Properties: AC bonus, resistance, ability boosts

**Upgrades:**

- Weapon: Power crystals, energy cells, lens
- Armor: Overlays, underlays, plates
- Applied via crafting interface

**Consumables:**

- Medpacs: Restore health
- Stimulants: Temporary bonuses
- Grenades: Area damage/effects
- Single-use or limited charges

**Quest Items:**

- Plot-flagged, cannot be lost
- Often no combat value
- Trigger scripted events

**Droid Equipment:**

- Special items for droid party members
- Sensors, shields, weapons
- Different slot types than organic characters

### UTM (Merchant)

UTM files define merchant templates with inventory lists and merchant-specific properties.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/utm.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utm.py)

*This section will document the UTM (Merchant) generic type structure and fields in detail.*

### UTP (Placeable)

UTP files define placeable object templates including containers, furniture, switches, workbenches, and interactive environmental objects. Placeables can have inventories, be destroyed, locked, trapped, and trigger scripts.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/utp.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utp.py)

#### Core Identity Fields

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | ResRef | Template identifier for this placeable |
| `Tag` | CExoString | Unique tag for script references |
| `LocName` | CExoLocString | Placeable name (localized) |
| `Description` | CExoLocString | Placeable description |
| `Comment` | CExoString | Developer comment/notes |

#### Appearance & Type

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Appearance` | DWord | Index into `placeables.2da` |
| `Type` | Byte | Placeable type category |
| `AnimationState` | Byte | Current animation state |

**Appearance System:**

- `placeables.2da` defines models, lighting, and sounds
- Appearance determines visual model and interaction animation
- Type influences behavior (container, switch, generic)

#### Inventory System

| Field | Type | Description |
| ----- | ---- | ----------- |
| `HasInventory` | Byte | Placeable contains items |
| `ItemList` | List | Items in inventory |
| `BodyBag` | Byte | Container for corpse loot |

**ItemList Struct Fields:**

- `InventoryRes` (ResRef): UTI template ResRef
- `Repos_PosX` (Word): Grid X position (optional)
- `Repos_Posy` (Word): Grid Y position (optional)
- `Dropable` (Byte): Can drop item

**Container Behavior:**

- **HasInventory=1**: Can be looted
- **BodyBag=1**: Corpse container (special loot rules)
- ItemList populated on placeable instantiation
- Empty containers can still be interacted with

#### Locking & Security

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Locked` | Byte | Placeable is currently locked |
| `Lockable` | Byte | Can be locked/unlocked |
| `KeyRequired` | Byte | Requires specific key item |
| `KeyName` | CExoString | Tag of required key item |
| `AutoRemoveKey` | Byte | Key consumed on use |
| `OpenLockDC` | Byte | Security skill DC to pick lock |
| `CloseLockDC` (KotOR2) | Byte | Security DC to lock |
| `OpenLockDiff` (KotOR2) | Int | Additional difficulty modifier |
| `OpenLockDiffMod` (KotOR2) | Int | Modifier to difficulty |

**Lock Mechanics:**

- Identical to UTD door locking system
- Prevents access to inventory
- Can be picked or opened with key

#### Hit Points & Durability

| Field | Type | Description |
| ----- | ---- | ----------- |
| `HP` | Short | Maximum hit points |
| `CurrentHP` | Short | Current hit points |
| `Hardness` | Byte | Damage reduction |
| `Min1HP` (KotOR2) | Byte | Cannot drop below 1 HP |
| `Fort` | Byte | Fortitude save (usually 0) |
| `Ref` | Byte | Reflex save (usually 0) |
| `Will` | Byte | Will save (usually 0) |

**Destructible Placeables:**

- Containers, crates, and terminals can have HP
- Some placeables reveal items when destroyed
- Hardness reduces incoming damage

#### Interaction & Behavior

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Plot` | Byte | Plot-critical (cannot be destroyed) |
| `Static` | Byte | Static geometry (no interaction) |
| `Useable` | Byte | Can be clicked/used |
| `Conversation` | ResRef | Dialog file when used |
| `Faction` | Word | Faction identifier |
| `PartyInteract` | Byte | Requires party member selection |
| `NotBlastable` (KotOR2) | Byte | Immune to area damage |

**Usage Patterns:**

- **Useable=0**: Cannot be directly interacted with
- **Conversation**: Triggers dialog on use (terminals, panels)
- **PartyInteract**: Shows party selection GUI
- **Static**: Pure visual element, no gameplay

#### Script Hooks

| Field | Type | Description |
| ----- | ---- | ----------- |
| `OnClosed` | ResRef | Fires when container closes |
| `OnDamaged` | ResRef | Fires when placeable takes damage |
| `OnDeath` | ResRef | Fires when placeable is destroyed |
| `OnDisarm` | ResRef | Fires when trap is disarmed |
| `OnEndDialogue` | ResRef | Fires when conversation ends |
| `OnHeartbeat` | ResRef | Fires periodically |
| `OnInvDisturbed` | ResRef | Fires when inventory changed |
| `OnLock` | ResRef | Fires when locked |
| `OnMeleeAttacked` | ResRef | Fires when attacked in melee |
| `OnOpen` | ResRef | Fires when opened |
| `OnSpellCastAt` | ResRef | Fires when spell cast at placeable |
| `OnUnlock` | ResRef | Fires when unlocked |
| `OnUsed` | ResRef | Fires when used/clicked |
| `OnUserDefined` | ResRef | Fires on user-defined events |
| `OnFailToOpen` (KotOR2) | ResRef | Fires when opening fails |

#### Trap System

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TrapDetectable` | Byte | Trap can be detected |
| `TrapDetectDC` | Byte | Awareness DC to detect trap |
| `TrapDisarmable` | Byte | Trap can be disarmed |
| `DisarmDC` | Byte | Security DC to disarm trap |
| `TrapFlag` | Byte | Trap is active |
| `TrapOneShot` | Byte | Trap triggers only once |
| `TrapType` | Byte | Index into `traps.2da` |

**Trap Behavior:**

- Identical to door trap system
- Triggers on placeable use
- Common on containers and terminals

#### Visual Customization

| Field | Type | Description |
| ----- | ---- | ----------- |
| `PortraitId` | Word | Portrait icon identifier |
| `PaletteID` | Byte | Toolset palette category |

**Model & Lighting:**

- Appearance determines model and light color
- Some placeables have animated components
- Light properties defined in `placeables.2da`

#### Implementation Notes

**Placeable Categories:**

**Containers:**

- Footlockers, crates, corpses
- Have inventory (ItemList populated)
- Can be locked, trapped, destroyed
- `HasInventory=1`, `BodyBag` flag for corpses

**Switches & Terminals:**

- Trigger scripts or conversations
- No inventory typically
- `Useable=1`, `Conversation` or scripts set
- Common for puzzle activation

**Workbenches:**

- Special placeable type for crafting
- Opens crafting interface on use
- Defined by Type or Appearance

**Furniture:**

- Non-interactive decoration
- `Static=1` or `Useable=0`
- Pure visual elements

**Environmental Objects:**

- Explosive containers, power generators
- Can be destroyed with effects
- Often have HP and OnDeath scripts

**Instantiation Flow:**

1. **Template Load**: GFF parsed from UTP
2. **Appearance Setup**: Model loaded from `placeables.2da`
3. **Inventory Population**: ItemList instantiated
4. **Lock State**: Locked status applied
5. **Trap Activation**: Trap armed if configured
6. **Script Registration**: Event handlers registered

**Container Loot:**

- ItemList defines initial inventory
- Random loot can be added via script
- OnInvDisturbed fires when items taken
- BodyBag containers have special loot rules

**Conversation Placeables:**

- Terminals, control panels, puzzle interfaces
- Conversation property set to DLG file
- Use triggers dialog instead of direct interaction
- Dialog can have conditional responses

**Common Placeable Types:**

**Storage Containers:**

- Footlockers, crates, bins
- Standard inventory interface
- Often locked or trapped

**Corpses:**

- BodyBag flag set
- Contain enemy loot
- Disappear when looted (usually)

**Terminals:**

- Computer interfaces
- Trigger conversations or scripts
- May require Computer Use skill checks

**Switches:**

- Activate doors, puzzles, machinery
- Fire OnUsed script
- Visual feedback animation

**Workbenches:**

- Crafting interface activation
- Lab stations, upgrade benches
- Special Type value

**Decorative Objects:**

- No gameplay interaction
- Static or non-useable
- Environmental detail

**Mines (Special Case):**

- Placed as placeable or creature
- Trap properties define behavior
- Can be detected and disarmed
- Trigger on proximity or interaction

### UTS (Sound)

UTS files define sound object templates for ambient and environmental audio. These can be positional 3D sounds or global stereo sounds, with looping, randomization, and volume control.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/uts.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/uts.py)

#### Core Identity Fields

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | ResRef | Template identifier for this sound |
| `Tag` | CExoString | Unique tag for script references |
| `LocName` | CExoLocString | Sound name (unused) |
| `Comment` | CExoString | Developer comment/notes |

#### Playback Control

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Active` | Byte | Sound is currently active |
| `Continuous` | Byte | Sound plays continuously |
| `Looping` | Byte | Individual samples loop |
| `Positional` | Byte | Sound is 3D positional |
| `Random` | Byte | Randomly select from Sounds list |
| `Volume` | Byte | Volume level (0-127) |
| `VolumeVary` | Byte | Random volume variation |
| `PitchVary` | Byte | Random pitch variation |

#### Timing & Interval

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Interval` | Int | Delay between plays (seconds) |
| `IntervalVary` | Int | Random interval variation |
| `Times` | Int | Times to play (unused) |

**Playback Modes:**

- **Continuous**: Loops one sample indefinitely (machinery, hum)
- **Interval**: Plays samples with delays (birds, random creaks)
- **Random**: Picks different sample each time

#### Positioning

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Elevation` | Float | Height offset from ground |
| `MaxDistance` | Float | Distance where sound becomes inaudible |
| `MinDistance` | Float | Distance where sound is at full volume |
| `RandomPosition` | Byte | Randomize emitter position |
| `RandomRangeX` | Float | X-axis random range |
| `RandomRangeY` | Float | Y-axis random range |

**3D Audio:**

- **Positional=1**: Sound attenuates with distance and pans
- **Positional=0**: Global stereo sound (music, voiceover)
- **Min/Max Distance**: Controls falloff curve

#### Sound List

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Sounds` | List | List of WAV/MP3 files to play |

**Sounds Struct Fields:**

- `Sound` (ResRef): Audio file resource

**Randomization:**

- If `Random=1`, engine picks one sound from list each interval
- Allows for varied ambience (e.g., 5 different bird calls)

### UTT (Trigger)

UTT files define trigger templates for invisible volumes that fire scripts when entered, exited, or used. Triggers are essential for area transitions, cutscenes, traps, and game logic.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/utt.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utt.py)

#### Core Identity Fields

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | ResRef | Template identifier for this trigger |
| `Tag` | CExoString | Unique tag for script references |
| `LocName` | CExoLocString | Trigger name (localized) |
| `Comment` | CExoString | Developer comment/notes |

#### Trigger Configuration

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Type` | Int | Trigger type (0=Generic, 1=Transition, 2=Trap) |
| `Faction` | Word | Faction identifier |
| `Cursor` | Int | Cursor icon when hovered (0=None, 1=Door, etc) |
| `HighlightHeight` | Float | Height of selection highlight |

**Trigger Types:**

- **Generic**: Script execution volume
- **Transition**: Loads new module or moves to waypoint
- **Trap**: Damages/effects entering object

#### Transition Settings

| Field | Type | Description |
| ----- | ---- | ----------- |
| `LinkedTo` | CExoString | Destination waypoint tag |
| `LinkedToModule` | ResRef | Destination module ResRef |
| `LinkedToFlags` | Byte | Transition behavior flags |
| `LoadScreenID` | Word | Loading screen ID |
| `PortraitId` | Word | Portrait ID (unused) |

**Area Transitions:**

- **LinkedToModule**: Target module to load
- **LinkedTo**: Waypoint where player spawns
- **LoadScreenID**: Image displayed during load

#### Trap System

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TrapFlag` | Byte | Trigger is a trap |
| `TrapType` | Byte | Index into `traps.2da` |
| `TrapDetectable` | Byte | Can be detected |
| `TrapDetectDC` | Byte | Awareness DC to detect |
| `TrapDisarmable` | Byte | Can be disarmed |
| `DisarmDC` | Byte | Security DC to disarm |
| `TrapOneShot` | Byte | Fires once then disables |
| `AutoRemoveKey` | Byte | Key removed on use |
| `KeyName` | CExoString | Key tag required to disarm/bypass |

**Trap Mechanics:**

- Floor traps (mines, pressure plates) are triggers
- Detection makes trap visible and clickable
- Entering without disarm triggers trap effect

#### Script Hooks

| Field | Type | Description |
| ----- | ---- | ----------- |
| `OnClick` | ResRef | Fires when clicked |
| `OnDisarm` | ResRef | Fires when disarmed |
| `OnHeartbeat` | ResRef | Fires periodically |
| `OnScriptEnter` | ResRef | Fires when object enters |
| `OnScriptExit` | ResRef | Fires when object exits |
| `OnTrapTriggered` | ResRef | Fires when trap activates |
| `OnUserDefined` | ResRef | Fires on user event |

**Scripting:**

- **OnScriptEnter**: Most common hook (cutscenes, spawns)
- **OnHeartbeat**: Area-of-effect damage/buffs
- **OnClick**: Used for interactive transitions

### UTW (Waypoint)

UTW files define waypoint templates. Waypoints are invisible markers used for spawn points, navigation targets, map notes, and reference points for scripts.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/utw.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utw.py)

#### Core Identity Fields

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | ResRef | Template identifier for this waypoint |
| `Tag` | CExoString | Unique tag for script/linking references |
| `LocalizedName` | CExoLocString | Waypoint name |
| `Description` | CExoLocString | Description (unused) |
| `Comment` | CExoString | Developer comment/notes |

#### Map Note Functionality

| Field | Type | Description |
| ----- | ---- | ----------- |
| `HasMapNote` | Byte | Waypoint has a map note |
| `MapNoteEnabled` | Byte | Map note is initially visible |
| `MapNote` | CExoLocString | Text displayed on map |

**Map Notes:**

- If enabled, shows text on the in-game map
- Can be enabled/disabled via script (`SetMapPinEnabled`)
- Used for quest objectives and locations

#### Linking & Appearance

| Field | Type | Description |
| ----- | ---- | ----------- |
| `LinkedTo` | CExoString | Tag of linked object (unused) |
| `Appearance` | Byte | Appearance type (1=Waypoint) |
| `PaletteID` | Byte | Toolset palette category |

**Usage:**

- **Spawn Points**: `CreateObject` uses waypoint location
- **Patrols**: AI walks between waypoints
- **Teleport**: `JumpToLocation` targets waypoints
- **Transitions**: Doors/Triggers link to waypoint tags

---

## Implementation Details

**Binary Reading**: [`Libraries/PyKotor/src/pykotor/resource/formats/gff/io_gff.py:26-419`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/gff/io_gff.py#L26-L419)

**Binary Writing**: [`Libraries/PyKotor/src/pykotor/resource/formats/gff/io_gff.py:421-800`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/gff/io_gff.py#L421-L800)

**GFF Class**: [`Libraries/PyKotor/src/pykotor/resource/formats/gff/gff_data.py:200-400`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/gff/gff_data.py#L200-L400)

**GFFStruct Class**: [`Libraries/PyKotor/src/pykotor/resource/formats/gff/gff_data.py:400-800`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/gff/gff_data.py#L400-L800)

---

This documentation aims to provide a comprehensive overview of the KotOR GFF file format, focusing on the detailed file structure and data formats used within the games.
