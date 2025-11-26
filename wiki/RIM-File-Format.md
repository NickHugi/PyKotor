# KotOR RIM File Format Documentation

This document provides a detailed description of the RIM (Resource Information Module) file format used in Knights of the Old Republic (KotOR) games. RIM files store template resources used as module blueprints.

## Table of Contents

- [KotOR RIM File Format Documentation](#kotor-rim-file-format-documentation)
  - [Table of Contents](#table-of-contents)
  - [File Structure Overview](#file-structure-overview)
    - [RIM vs. ERF/MOD](#rim-vs-erfmod)
  - [Binary Format](#binary-format)
    - [File Header](#file-header)
    - [Resource Table](#resource-table)
    - [Resource Data](#resource-data)
  - [Extended Header](#extended-header)
  - [Implementation Details](#implementation-details)

---

## File Structure Overview

RIM files are similar to ERF files but are read-only from the game's perspective. The game loads RIM files as templates for modules and exports them to ERF format for runtime mutation.

### RIM vs. ERF/MOD

While RIM files share structural similarities with ERF/MOD files, they serve different purposes:

**RIM Files:**

- Stored as `<module_name>.rim` and `<module_name>_s.rim` (secondary/localized)
- Read-only template data - never modified during gameplay
- Contain base module resources before player modifications
- Typically paired with corresponding ERF files during development

**Module Loading Process:**

1. Game loads the RIM file as the base template
2. If a save exists, corresponding SAV file overrides modified resources
3. Override folder and HAK files can replace specific resources
4. Runtime changes (opened doors, looted containers) are saved to SAV, not RIM

**Extended RIM Files:**

Files with '_s' suffix (e.g., `module001_s.rim`) are "extended" RIM files:

- Contain additional or updated content for the base module
- Loaded after the primary RIM but before player saves
- Often used for patches or expansion content
- Include an extended header (104 additional bytes)

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/rim/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/rim/)

**Reference**: [`vendor/reone/src/libs/resource/format/rimreader.cpp:24-100`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/rimreader.cpp#L24-L100)

---

## [Binary Format](https://en.wikipedia.org/wiki/Binary_file)

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
| Compression  | uint32  | 120    | 4    | Compression type (typically 0 = none)                           |

**Extended Header Purpose:**

The extended header was added to support additional module features:

- **Modular Updates**: Extended RIMs can patch or add to base modules without replacing them entirely
- **Compression Support**: Reserved space for future compression (though KotOR doesn't use it)
- **Versioning**: Allows identification of expansion/patch content

**Usage Example:**

```plaintext
module001.rim   - Base module (Endar Spire)
module001_s.rim  - Extended content (additional areas or restored content)
module001_dlg.erf  - Dialog for the module (weird quirk exclusive to K2/TSL)
```

The game loads both files, with the extended RIM's resources taking precedence over conflicting base RIM resources.

**Identifying Extended RIMs:**

Extended RIMs can be identified by:

1. Filename ending in 'x' (e.g., `danm14aax.rim`)
2. IsExtension flag = 1 in the extended header
3. Total header size of 124 bytes instead of 20 bytes

Standard RIMs that aren't extended can still function normally even if parsers check for the extended header - they'll simply find the resource table immediately after the 20-byte header.

**Reference**: [`vendor/Kotor.NET/Kotor.NET/Formats/KotorRIM/RIMBinaryStructure.cs:40-50`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorRIM/RIMBinaryStructure.cs#L40-L50)

---

## Implementation Details

**Binary Reading**: [`Libraries/PyKotor/src/pykotor/resource/formats/rim/io_rim.py`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/rim/io_rim.py)

**Binary Writing**: [`Libraries/PyKotor/src/pykotor/resource/formats/rim/io_rim.py`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/rim/io_rim.py)

**RIM Class**: [`Libraries/PyKotor/src/pykotor/resource/formats/rim/rim_data.py:87-158`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/rim/rim_data.py#L87-L158)

---

This documentation aims to provide a comprehensive overview of the KotOR RIM file format, focusing on the detailed file structure and data formats used within the games.
