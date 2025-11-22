# KotOR RIM File Format Documentation

This document provides a detailed description of the RIM (Resource Information Module) file format used in Knights of the Old Republic (KotOR) games. RIM files store template resources used as module blueprints.

## Table of Contents

- [KotOR RIM File Format Documentation](#kotor-rim-file-format-documentation)
  - [Table of Contents](#table-of-contents)
  - [File Structure Overview](#file-structure-overview)
  - [Binary Format](#binary-format)
    - [File Header](#file-header)
    - [Resource Table](#resource-table)
    - [Resource Data](#resource-data)
  - [Extended Header](#extended-header)
  - [Implementation Details](#implementation-details)

---

## File Structure Overview

RIM files are similar to ERF files but are read-only from the game's perspective. The game loads RIM files as templates for modules and exports them to ERF format for runtime mutation.

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/rim/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/rim/)

**Reference**: [`vendor/reone/src/libs/resource/format/rimreader.cpp:24-100`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/rimreader.cpp#L24-L100)

---

## Binary Format

### File Header

The file header is 20 bytes (or 124 bytes with extended header):

| Name                | Type    | Offset | Size | Description                                    |
| ------------------- | ------- | ------ | ---- | ---------------------------------------------- |
| File Type           | char[4] | 0      | 4    | Always `"RIM "` (space-padded)                 |
| File Version        | char[4] | 4      | 4    | Always `"V1.0"`                                 |
| Unknown             | uint32  | 8      | 4    | Typically `0x00000000`                         |
| Resource Count      | uint32  | 12     | 4    | Number of resources in the archive             |
| Offset to Resource Table | uint32 | 16 | 4    | Offset to resource entries array                |

**Reference**: [`vendor/Kotor.NET/Kotor.NET/Formats/KotorRIM/RIMBinaryStructure.cs:13-53`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorRIM/RIMBinaryStructure.cs#L13-L53)

### Resource Table

Each resource entry is 32 bytes:

| Name          | Type     | Offset | Size | Description                                                      |
| ------------- | -------- | ------ | ---- | ---------------------------------------------------------------- |
| ResRef        | char[16] | 0      | 16   | Resource filename (null-padded, max 16 chars)                   |
| Resource Type ID | uint32 | 16   | 4    | Resource type identifier                                         |
| Resource ID   | uint32   | 20     | 4    | Resource index (usually sequential)                              |
| Offset to Data | uint32 | 24   | 4    | Offset to resource data in file                                  |
| Resource Size | uint32   | 28     | 4    | Size of resource data in bytes                                   |

**Reference**: [`vendor/reone/src/libs/resource/format/rimreader.cpp:40-70`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/rimreader.cpp#L40-L70)

### Resource Data

Resource data is stored at the offsets specified in the resource table:

| Name         | Type   | Description                                                      |
| ------------ | ------ | ---------------------------------------------------------------- |
| Resource Data | byte[] | Raw binary data for each resource                               |

---

## Extended Header

Extended RIM files (filenames ending in 'x', e.g., `module001x.rim`) have an additional 104 bytes after the standard header:

| Name         | Type    | Offset | Size | Description                                                      |
| ------------ | ------- | ------ | ---- | ---------------------------------------------------------------- |
| IsExtension  | uint8   | 20     | 1    | Flag indicating extended RIM (1 = extension)                    |
| Reserved     | byte[99] | 21   | 99   | Reserved bytes                                                   |

**Reference**: [`vendor/Kotor.NET/Kotor.NET/Formats/KotorRIM/RIMBinaryStructure.cs:40-50`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorRIM/RIMBinaryStructure.cs#L40-L50)

---

## Implementation Details

**Binary Reading**: [`Libraries/PyKotor/src/pykotor/resource/formats/rim/io_rim.py`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/rim/io_rim.py)

**Binary Writing**: [`Libraries/PyKotor/src/pykotor/resource/formats/rim/io_rim.py`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/rim/io_rim.py)

**RIM Class**: [`Libraries/PyKotor/src/pykotor/resource/formats/rim/rim_data.py:87-158`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/rim/rim_data.py#L87-L158)

---

This documentation aims to provide a comprehensive overview of the KotOR RIM file format, focusing on the detailed file structure and data formats used within the games.
