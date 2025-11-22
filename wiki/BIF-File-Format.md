# KotOR BIF File Format Documentation

This document provides a detailed description of the BIF (BioWare Index File) file format used in Knights of the Old Republic (KotOR) games. BIF files are archive containers that store the bulk of game resources.

## Table of Contents

- [KotOR BIF File Format Documentation](#kotor-bif-file-format-documentation)
  - [Table of Contents](#table-of-contents)
  - [File Structure Overview](#file-structure-overview)
    - [BIF Usage in KotOR](#bif-usage-in-kotor)
  - [Binary Format](#binary-format)
    - [File Header](#file-header)
    - [Variable Resource Table](#variable-resource-table)
    - [Resource Data](#resource-data)
  - [BZF Compression](#bzf-compression)
    - [BZF Format Details](#bzf-format-details)
  - [KEY File Relationship](#key-file-relationship)
  - [Implementation Details](#implementation-details)

---

## File Structure Overview

BIF files work in tandem with KEY files which provide the filename-to-resource mappings. BIF files contain only resource IDs, types, and data - the actual filenames (ResRefs) are stored in the KEY file.

### BIF Usage in KotOR

BIF archives are the primary storage mechanism for game assets. The game organizes resources into multiple BIF files by category:

- `data/models.bif`: 3D model files (MDL/MDX)
- `data/textures_*.bif`: Texture data (TPC/TXI files) - split across multiple archives
- `data/sounds.bif`: Audio files (WAV)
- `data/2da.bif`: Game data tables (2DA files)
- `data/scripts.bif`: Compiled scripts (NCS)
- `data/dialogs.bif`: Conversation files (DLG)
- `data/lips.bif`: Lip-sync animation data (LIP)
- Additional platform-specific BIFs (e.g., `dataxbox/`, `data_mac/`)

The modular structure allows for efficient loading and potential platform-specific optimizations. Resources in BIF files are read-only at runtime; mods override them via the `override/` directory or custom ERF/MOD files.

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/bif/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/bif/)

**Reference**: [`vendor/reone/src/libs/resource/format/bifreader.cpp:24-73`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/bifreader.cpp#L24-L73)

---

## Binary Format

### File Header

The file header is 20 bytes in size:

| Name                      | Type    | Offset | Size | Description                                    |
| ------------------------- | ------- | ------ | ---- | ---------------------------------------------- |
| File Type                 | char[4] | 0      | 4    | `"BIFF"` for BIF, `"BZF "` for compressed BIF  |
| File Version              | char[4] | 4      | 4    | `"V1  "` for BIF, `"V1.0"` for BZF             |
| Variable Resource Count   | uint32  | 8      | 4    | Number of variable-size resources              |
| Fixed Resource Count      | uint32  | 12     | 4    | Number of fixed-size resources (unused, always 0) |
| Offset to Variable Resource Table | uint32 | 16 | 4 | Offset to variable resource entries            |

**Note on Fixed Resources:** The "Fixed Resource Count" field is a legacy holdover from Neverwinter Nights where some resource types had predetermined sizes. In KotOR, this field is always `0` and fixed resource tables are never used. All resources are stored in the variable resource table regardless of their size.

**Reference**: [`vendor/Kotor.NET/Kotor.NET/Formats/KotorBIF/BIFBinaryStructure.cs:13-67`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorBIF/BIFBinaryStructure.cs#L13-L67)

### Variable Resource Table

Each variable resource entry is 16 bytes:

| Name        | Type   | Offset | Size | Description                                                      |
| ----------- | ------ | ------ | ---- | ---------------------------------------------------------------- |
| Resource ID | uint32 | 0      | 4    | Resource ID (matches KEY file entry)                             |
| Offset      | uint32 | 4      | 4    | Offset to resource data in file                                  |
| File Size   | uint32 | 8      | 4    | Uncompressed size of resource data                              |
| Resource Type | uint32 | 12   | 4    | Resource type identifier                                         |

**Reference**: [`vendor/reone/src/libs/resource/format/bifreader.cpp:35-50`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/bifreader.cpp#L35-L50)

### Resource Data

Resource data is stored at the offsets specified in the resource table:

| Name         | Type   | Description                                                      |
| ------------ | ------ | ---------------------------------------------------------------- |
| Resource Data | byte[] | Raw binary data for each resource                               |

**Resource Storage Details:**

- Resources are stored sequentially but not necessarily contiguously (gaps may exist)
- Each resource's size is specified in the variable resource table entry
- Resource data is stored in its native format (no additional BIF-specific wrapping)
- The engine reads resources by:
  1. Looking up the ResRef in the KEY file to get the Resource ID
  2. Extracting the BIF index and resource index from the Resource ID
  3. Reading the BIF file header to find the variable resource table
  4. Finding the resource entry by index
  5. Seeking to the offset and reading the specified number of bytes

**Resource IDs:**

The Resource ID in the BIF file's variable resource table must match the Resource ID stored in the KEY file. The KEY file encodes both the BIF index (top 12 bits) and resource index within the BIF (bottom 20 bits) into a single 32-bit value.

---

## BZF Compression

BZF files are LZMA-compressed BIF files used primarily in iOS (and maybe Android) ports of KotOR. The BZF header contains `"BZF "` + `"V1.0"`, followed by LZMA-compressed BIF data. Decompression reveals a standard BIF structure.

### BZF Format Details

The BZF format wraps a complete BIF file in LZMA compression:

1. **BZF Header** (8 bytes): `"BZF "` + `"V1.0"` signature
2. **LZMA Stream**: Compressed BIF file data using LZMA algorithm
3. **Decompressed Result**: Standard BIF file structure (as described above)

**Benefits of BZF:**

- Significantly reduced file sizes (typically 40-60% compression ratio)
- Faster download times for mobile platforms
- Identical resource access after decompression
- No performance penalty during gameplay (decompressed once at load time)

**Platform Usage:**

- PC releases use uncompressed BIF files for faster access
- Mobile releases (iOS/Android) use BZF for storage efficiency
- Modding tools can (and should) convert between BIF and BZF formats freely

The BZF wrapper is completely transparent to the game engine - once decompressed in memory, the resource access patterns are identical to standard BIF files.

**Reference**: [`vendor/reone/src/libs/resource/format/bifreader.cpp:48-76`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/bifreader.cpp#L48-L76)

---

## KEY File Relationship

BIF files require a KEY file to map resource IDs to filenames (ResRefs). The KEY file contains:

- BIF file entries (filename, size, location)
- Key entries mapping ResRef + ResourceType to Resource ID

The Resource ID in the BIF file matches the Resource ID in the KEY file's key entries.

**Reference**: See [KEY File Format](KEY-File-Format) documentation.

---

## Implementation Details

**Binary Reading**: [`Libraries/PyKotor/src/pykotor/resource/formats/bif/io_bif.py`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/bif/io_bif.py)

**Binary Writing**: [`Libraries/PyKotor/src/pykotor/resource/formats/bif/io_bif.py`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/bif/io_bif.py)

**BIF Class**: [`Libraries/PyKotor/src/pykotor/resource/formats/bif/bif_data.py:100-575`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bif/bif_data.py#L100-L575)

---

This documentation aims to provide a comprehensive overview of the KotOR BIF file format, focusing on the detailed file structure and data formats used within the games.
