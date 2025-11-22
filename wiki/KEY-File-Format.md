# KotOR KEY File Format Documentation

This document provides a detailed description of the KEY (Key Table) file format used in Knights of the Old Republic (KotOR) games. KEY files serve as the master index for all BIF files in the game.

## Table of Contents

- [KotOR KEY File Format Documentation](#kotor-key-file-format-documentation)
  - [Table of Contents](#table-of-contents)
  - [File Structure Overview](#file-structure-overview)
  - [Binary Format](#binary-format)
    - [File Header](#file-header)
    - [File Table](#file-table)
    - [Filename Table](#filename-table)
    - [Key Table](#key-table)
  - [Resource ID Encoding](#resource-id-encoding)
  - [Implementation Details](#implementation-details)

---

## File Structure Overview

KEY files map resource names (ResRefs) and types to specific locations within BIF archives. KotOR uses `chitin.key` as the main KEY file which references all game BIF files.

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/key/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/key/)

**Reference**: [`vendor/reone/src/libs/resource/format/keyreader.cpp:24-128`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/keyreader.cpp#L24-L128)

---

## Binary Format

### File Header

The file header is 64 bytes in size:

| Name                | Type    | Offset | Size | Description                                    |
| ------------------- | ------- | ------ | ---- | ---------------------------------------------- |
| File Type           | char[4] | 0      | 4    | Always `"KEY "` (space-padded)                 |
| File Version        | char[4] | 4      | 4    | `"V1  "` or `"V1.1"`                           |
| BIF Count           | uint32  | 8      | 4    | Number of BIF files referenced                 |
| Key Count           | uint32  | 12     | 4    | Number of resource entries                     |
| Offset to File Table | uint32 | 16     | 4    | Offset to BIF file entries array               |
| Offset to Key Table | uint32 | 20     | 4    | Offset to resource entries array               |
| Build Year          | uint32  | 24     | 4    | Build year (years since 1900)                  |
| Build Day           | uint32  | 28     | 4    | Build day (days since Jan 1)                   |
| Reserved            | byte[32] | 32   | 32   | Padding (usually zeros)                        |

**Reference**: [`vendor/Kotor.NET/Kotor.NET/Formats/KotorKEY/KEYBinaryStructure.cs:13-114`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorKEY/KEYBinaryStructure.cs#L13-L114)

### File Table

Each file entry is 12 bytes:

| Name            | Type   | Offset | Size | Description                                                      |
| --------------- | ------ | ------ | ---- | ---------------------------------------------------------------- |
| File Size       | uint32 | 0      | 4    | Size of BIF file on disk                                         |
| Filename Offset | uint32 | 4      | 4    | Offset into filename table                                       |
| Filename Length | uint16 | 8      | 2    | Length of filename in bytes                                      |
| Drives          | uint16 | 10     | 2    | Drive flags (0x0001=HD0, 0x0002=CD1, etc.)                      |

**Reference**: [`vendor/reone/src/libs/resource/format/keyreader.cpp:55-70`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/keyreader.cpp#L55-L70)

### Filename Table

The filename table contains null-terminated strings:

| Name      | Type   | Description                                                      |
| --------- | ------ | ---------------------------------------------------------------- |
| Filenames | char[] | Null-terminated BIF filenames (e.g., "data/models.bif")         |

### Key Table

Each key entry is 22 bytes:

| Name        | Type     | Offset | Size | Description                                                      |
| ----------- | -------- | ------ | ---- | ---------------------------------------------------------------- |
| ResRef      | char[16] | 0      | 16   | Resource filename (null-padded, max 16 chars)                   |
| Resource Type | uint16 | 16   | 2    | Resource type identifier                                         |
| Resource ID | uint32   | 18     | 4    | Encoded resource location (see [Resource ID Encoding](#resource-id-encoding)) |

**Reference**: [`vendor/reone/src/libs/resource/format/keyreader.cpp:72-100`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/keyreader.cpp#L72-L100)

---

## Resource ID Encoding

The Resource ID field encodes both the BIF index and resource index within that BIF:

- **Bits 31-20**: BIF Index (top 12 bits) - index into file table
- **Bits 19-0**: Resource Index (bottom 20 bits) - index within the BIF file

**Decoding:**
```python
bif_index = (resource_id >> 20) & 0xFFF
resource_index = resource_id & 0xFFFFF
```

**Reference**: [`vendor/reone/src/libs/resource/format/keyreader.cpp:95-100`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/keyreader.cpp#L95-L100)

---

## Implementation Details

**Binary Reading**: [`Libraries/PyKotor/src/pykotor/resource/formats/key/io_key.py`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/key/io_key.py)

**Binary Writing**: [`Libraries/PyKotor/src/pykotor/resource/formats/key/io_key.py`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/key/io_key.py)

**KEY Class**: [`Libraries/PyKotor/src/pykotor/resource/formats/key/key_data.py:100-462`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/key/key_data.py#L100-L462)

---

This documentation aims to provide a comprehensive overview of the KotOR KEY file format, focusing on the detailed file structure and data formats used within the games.
