# KotOR GFF File Format Documentation

This document provides a detailed description of the GFF (Generic File Format) used in Knights of the Old Republic (KotOR) games. GFF is a container format used for many different game resource types, including character templates, areas, dialogs, placeables, creatures, items, and more.

## Table of Contents

- [KotOR GFF File Format Documentation](#kotor-gff-file-format-documentation)
  - [Table of Contents](#table-of-contents)
  - [File Structure Overview](#file-structure-overview)
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
    - [DLG (Dialogue)](#dlg-dialogue)
    - [GIT (Game Instance Template)](#git-game-instance-template)
    - [GUI](#gui)
    - [IFO (Module Info)](#ifo-module-info)
    - [JRL (Journal)](#jrl-journal)
    - [PTH (Path)](#pth-path)
    - [UTC (Creature)](#utc-creature)
    - [UTD (Door)](#utd-door)
    - [UTE (Encounter)](#ute-encounter)
    - [UTI (Item)](#uti-item)
    - [UTM (Merchant)](#utm-merchant)
    - [UTP (Placeable)](#utp-placeable)
    - [UTS (Sound)](#uts-sound)
    - [UTT (Trigger)](#utt-trigger)
    - [UTW (Waypoint)](#utw-waypoint)
  - [Implementation Details](#implementation-details)

---

## File Structure Overview

GFF files use a hierarchical structure with structs containing fields, which can be simple values or nested structs and lists. The format supports version V3.2 (KotOR) and later versions (V3.3, V4.0, V4.1) used in other BioWare games.

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
| Labels | char[16] | 16×N | Array of field name labels (null-padded to 16 bytes)            |

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

---

## GFF Generic Types

GFF files are used as containers for various game resource types. Each generic type has its own structure and field definitions.

### ARE (Area)

ARE files define area properties, including scripts, ambient sounds, weather, and area-specific settings.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/are.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/are.py)

*This section will document the ARE (Area) generic type structure and fields in detail.*

### DLG (Dialogue)

DLG files define conversation trees with nodes, entries, replies, and script triggers.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/dlg/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/generics/dlg/)

*This section will document the DLG (Dialogue) generic type structure and fields in detail.*

### GIT (Game Instance Template)

GIT files define instance data for areas, including placeables, creatures, doors, triggers, waypoints, and other interactive objects.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/git.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/git.py)

*This section will document the GIT (Game Instance Template) generic type structure and fields in detail.*

### GUI

GUI files define user interface layouts. See the [GUI File Format](GUI-File-Format) documentation for complete details.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/gui.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/gui.py)

### IFO (Module Info)

IFO files contain module metadata, including entry points, scripts, and module-specific settings.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/ifo.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/ifo.py)

*This section will document the IFO (Module Info) generic type structure and fields in detail.*

### JRL (Journal)

JRL files define journal quest entries and categories.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/jrl.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/jrl.py)

*This section will document the JRL (Journal) generic type structure and fields in detail.*

### PTH (Path)

PTH files define pathfinding waypoint networks for NPC movement.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/pth.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/pth.py)

*This section will document the PTH (Path) generic type structure and fields in detail.*

### UTC (Creature)

UTC files define creature templates with stats, feats, skills, inventory, and appearance.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py)

*This section will document the UTC (Creature) generic type structure and fields in detail.*

### UTD (Door)

UTD files define door templates with scripts, linked areas, and door-specific properties.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/utd.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utd.py)

*This section will document the UTD (Door) generic type structure and fields in detail.*

### UTE (Encounter)

UTE files define encounter templates that spawn creatures dynamically.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/ute.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/ute.py)

*This section will document the UTE (Encounter) generic type structure and fields in detail.*

### UTI (Item)

UTI files define item templates with properties, stats, and item-specific data.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/uti.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/uti.py)

*This section will document the UTI (Item) generic type structure and fields in detail.*

### UTM (Merchant)

UTM files define merchant templates with inventory lists and merchant-specific properties.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/utm.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utm.py)

*This section will document the UTM (Merchant) generic type structure and fields in detail.*

### UTP (Placeable)

UTP files define placeable object templates with scripts and placeable-specific properties.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/utp.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utp.py)

*This section will document the UTP (Placeable) generic type structure and fields in detail.*

### UTS (Sound)

UTS files define sound object templates for ambient sounds and sound effects.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/uts.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/uts.py)

*This section will document the UTS (Sound) generic type structure and fields in detail.*

### UTT (Trigger)

UTT files define trigger templates for area transitions and script activation.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/utt.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utt.py)

*This section will document the UTT (Trigger) generic type structure and fields in detail.*

### UTW (Waypoint)

UTW files define waypoint templates for NPC pathfinding and player fast travel.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/utw.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utw.py)

*This section will document the UTW (Waypoint) generic type structure and fields in detail.*

---

## Implementation Details

**Binary Reading**: [`Libraries/PyKotor/src/pykotor/resource/formats/gff/io_gff.py:26-419`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/gff/io_gff.py#L26-L419)

**Binary Writing**: [`Libraries/PyKotor/src/pykotor/resource/formats/gff/io_gff.py:421-800`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/gff/io_gff.py#L421-L800)

**GFF Class**: [`Libraries/PyKotor/src/pykotor/resource/formats/gff/gff_data.py:200-400`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/gff/gff_data.py#L200-L400)

**GFFStruct Class**: [`Libraries/PyKotor/src/pykotor/resource/formats/gff/gff_data.py:400-800`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/gff/gff_data.py#L400-L800)

---

This documentation aims to provide a comprehensive overview of the KotOR GFF file format, focusing on the detailed file structure and data formats used within the games.
