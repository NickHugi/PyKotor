# KotOR KEY File Format Documentation

This document provides a detailed description of the KEY (Key Table) file format used in Knights of the Old Republic (KotOR) games. KEY files serve as the master index for all BIF files in the game.

## Table of Contents

- [KotOR KEY File Format Documentation](#kotor-key-file-format-documentation)
  - [Table of Contents](#table-of-contents)
  - [File Structure Overview](#file-structure-overview)
    - [KEY File Purpose](#key-file-purpose)
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

### KEY File Purpose

The KEY file serves as the master index for the game's resource system:

1. **Resource Lookup**: Maps ResRef + ResourceType → BIF location
2. **BIF Registration**: Tracks all BIF files and their install paths
3. **Resource Naming**: Provides the filename (ResRef) missing from BIF files
4. **Drive Mapping**: Historical feature indicating which media (CD/HD) contained each BIF

**Resource Resolution Order:**

When the game needs a resource, it searches in this order:

1. Override folder (`override/`)
2. Currently loaded MOD/ERF files
3. Currently loaded SAV file (if in-game)
4. BIF files via KEY lookup
5. Hardcoded defaults (if no resource found)

The KEY file only manages BIF resources (step 4). Higher-priority locations can override KEY-indexed resources without modifying the KEY file.

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/key/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/key/)

**Reference**: [`vendor/reone/src/libs/resource/format/keyreader.cpp:24-128`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/keyreader.cpp#L24-L128)

---

## [Binary Format](https://en.wikipedia.org/wiki/Binary_file)

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

**Drive Flags Explained:**

Drive flags are a legacy feature from the multi-CD distribution era:

| Flag Value | Meaning | Description |
| ---------- | ------- | ----------- |
| `0x0001` | HD (Hard Drive) | BIF is installed on the hard drive |
| `0x0002` | CD1 | BIF is on the first game disc |
| `0x0004` | CD2 | BIF is on the second game disc |
| `0x0008` | CD3 | BIF is on the third game disc |
| `0x0010` | CD4 | BIF is on the fourth game disc |

**Modern Usage:**

In contemporary distributions (Steam, GOG, digital):

- All BIF files use `0x0001` (HD flag) since everything is installed locally
- The engine doesn't prompt for disc swapping
- Multiple flags can be combined (bitwise OR) if a BIF could be on multiple sources
- Mod tools typically set this to `0x0001` for all files

The drive system was originally designed so the engine could:

- Prompt users to insert specific CDs when needed resources weren't on the hard drive
- Optimize installation by allowing users to choose what to install vs. run from CD
- Support partial installs to save disk space (common in the early 2000s)

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

**Critical Structure Packing Note:**

The key entry structure must use **byte or word alignment** (1-byte or 2-byte packing). If the structure is packed with 4-byte or 8-byte alignment, the `uint32` at offset 0x0012 (18) will be incorrectly placed at offset 0x0014 (20), causing incorrect resource ID decoding.

On non-Intel platforms, this alignment requirement may cause alignment faults unless the compiler provides an "unaligned" type or special care is taken when accessing the `uint32` field. The structure should be explicitly packed to ensure the `uint32` starts at offset 18 rather than being aligned to a 4-byte boundary.

**Reference**: [`vendor/reone/src/libs/resource/format/keyreader.cpp:72-100`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/keyreader.cpp#L72-L100)

---

## Resource ID Encoding

The Resource ID field encodes both the BIF index and resource index within that BIF:

- **Bits 31-20**: BIF Index (top 12 bits) - index into file table
- **Bits 19-0**: Resource Index (bottom 20 bits) - index within the BIF file

**Decoding:**

```python
bif_index = (resource_id >> 20) & 0xFFF  # Extract top 12 bits
resource_index = resource_id & 0xFFFFF   # Extract bottom 20 bits
```

**Encoding:**

```python
resource_id = (bif_index << 20) | resource_index
```

**Practical Limits:**

- Maximum BIF files: 4,096 (12-bit BIF index)
- Maximum resources per BIF: 1,048,576 (20-bit resource index)

These limits are more than sufficient for KotOR, which typically has:

- ~50-100 BIF files in a full installation
- ~100-10,000 resources per BIF (largest BIFs are texture packs)

**Example:**

Given Resource ID `0x00123456`:

```
Binary: 0000 0000 0001 0010 0011 0100 0101 0110
        |---- 12 bits -----|------ 20 bits ------|
BIF Index:     0x001 (BIF #1)
Resource Index: 0x23456 (Resource #144,470 within that BIF)
```

The encoding allows a single 32-bit integer to precisely locate any resource in the entire BIF system.

**Reference**: [`vendor/reone/src/libs/resource/format/keyreader.cpp:95-100`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/keyreader.cpp#L95-L100)

---

## Implementation Details

**Binary Reading**: [`Libraries/PyKotor/src/pykotor/resource/formats/key/io_key.py`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/key/io_key.py)

**Binary Writing**: [`Libraries/PyKotor/src/pykotor/resource/formats/key/io_key.py`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/key/io_key.py)

**KEY Class**: [`Libraries/PyKotor/src/pykotor/resource/formats/key/key_data.py:100-462`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/key/key_data.py#L100-L462)

---

This documentation aims to provide a comprehensive overview of the KotOR KEY file format, focusing on the detailed file structure and data formats used within the games.
