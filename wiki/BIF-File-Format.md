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

BIF files work in tandem with KEY files which provide the filename-to-resource mappings. BIF files contain only resource IDs, types, and data - the actual filenames (ResRefs) are stored in the KEY file. BIF files are [archive containers](https://en.wikipedia.org/wiki/Archive_file) that store the bulk of game resources.

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

The [modular structure](https://en.wikipedia.org/wiki/Modular_programming) allows for efficient loading and potential platform-specific optimizations. Resources in BIF files are read-only at runtime; mods override them via the `override/` directory or custom ERF/MOD files.

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/bif/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/bif/)

**Reference**: [`vendor/reone/src/libs/resource/format/bifreader.cpp:24-73`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/bifreader.cpp#L24-L73)

---

## [Binary Format](https://en.wikipedia.org/wiki/Binary_file)

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

**Reference**: [`vendor/xoreos/src/aurora/biffile.cpp:64-67`](https://github.com/xoreos/xoreos/blob/master/src/aurora/biffile.cpp#L64-L67) explicitly checks that fixed resource count is 0 and throws an exception if it's not. [`vendor/reone/src/libs/resource/format/bifreader.cpp:34`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/bifreader.cpp#L34) reads the fixed resource count but does not use it.

**Reference**: [`vendor/Kotor.NET/Kotor.NET/Formats/KotorBIF/BIFBinaryStructure.cs:13-67`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorBIF/BIFBinaryStructure.cs#L13-L67)

### Variable Resource Table

Each variable resource entry is 16 bytes:

| Name        | Type   | Offset | Size | Description                                                      |
| ----------- | ------ | ------ | ---- | ---------------------------------------------------------------- |
| Resource ID | uint32 | 0      | 4    | Resource ID (matches KEY file entry, encodes BIF index and resource index) |
| Offset      | uint32 | 4      | 4    | Offset to resource data in file (absolute file offset)                    |
| File Size   | uint32 | 8      | 4    | Uncompressed size of resource data (bytes)                                 |
| Resource Type | uint32 | 12   | 4    | Resource type identifier (see ResourceType enum)                          |

**Entry Reading Order:**

Entries are read sequentially from the variable resource table. The table is located at the offset specified in the file header. Each entry is exactly 16 bytes, allowing efficient sequential reading.

**Reference**: [`vendor/reone/src/libs/resource/format/bifreader.cpp:50-63`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/bifreader.cpp#L50-L63) shows the exact reading order: Resource ID, Offset, File Size, Resource Type. [`vendor/Kotor.NET/Kotor.NET/Formats/KotorBIF/BIFBinaryStructure.cs:51-65`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorBIF/BIFBinaryStructure.cs#L51-L65) confirms the same structure. [`vendor/xoreos/src/aurora/biffile.cpp:84-96`](https://github.com/xoreos/xoreos/blob/master/src/aurora/biffile.cpp#L84-L96) shows reading with version-specific handling (V1.1 includes an additional flags field that KotOR does not use).

### Resource Data

Resource data is stored at the offsets specified in the resource table:

| Name         | Type   | Description                                                      |
| ------------ | ------ | ---------------------------------------------------------------- |
| Resource Data | byte[] | Raw binary data for each resource                               |

**Resource Storage Details:**

- Resources are stored sequentially but not necessarily contiguously (gaps may exist between resources)
- Each resource's size is specified in the variable resource table entry
- Resource data is stored in its native format (no additional BIF-specific wrapping or metadata)
- Offsets in the variable resource table are absolute file offsets (relative to start of file)
- Resource data begins immediately at the specified offset

**Resource Access Flow:**

The engine reads resources through the following process:

1. **KEY Lookup**: Look up the ResRef (and optionally ResourceType) in the KEY file to get the Resource ID
2. **ID Decoding**: Extract the BIF index (upper 12 bits) and resource index (lower 20 bits) from the Resource ID
3. **BIF Selection**: Use the BIF index to identify which BIF file contains the resource
4. **Table Access**: Read the BIF file header to find the offset to the variable resource table
5. **Entry Lookup**: Find the resource entry at the specified index in the variable resource table
6. **Data Reading**: Seek to the offset specified in the entry and read the number of bytes specified by the file size

**Reference**: [`vendor/xoreos/src/aurora/biffile.cpp:84-96`](https://github.com/xoreos/xoreos/blob/master/src/aurora/biffile.cpp#L84-L96) shows how variable resource entries are read. [`vendor/reone/src/libs/resource/format/bifreader.cpp:41-48`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/bifreader.cpp#L41-L48) demonstrates resource table loading. [`vendor/xoreos/src/aurora/biffile.cpp:99-123`](https://github.com/xoreos/xoreos/blob/master/src/aurora/biffile.cpp#L99-L123) shows the mergeKEY process that combines KEY and BIF information.

**Resource IDs:**

The Resource ID in the BIF file's variable resource table must match the Resource ID stored in the KEY file. The Resource ID is a 32-bit value that encodes two pieces of information:

- **Lower 20 bits (bits 0-19)**: Resource index within the BIF file (0-based index into the variable resource table)
- **Upper 12 bits (bits 20-31)**: BIF index in the KEY file's BIF table (identifies which BIF file contains this resource)

**Example:** A Resource ID of `0x00400029` decodes as:

- Resource index: `0x29` (41st resource in the BIF)
- BIF index: `0x004` (4th BIF file in the KEY's BIF table)

**Reference**: [`vendor/xoreos-docs/specs/torlack/key.html:154-168`](https://github.com/xoreos/xoreos-docs/blob/master/specs/torlack/key.html#L154-L168) provides detailed explanation of Resource ID encoding. [`vendor/reone/src/libs/resource/format/bifreader.cpp:50-54`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/bifreader.cpp#L50-L54) shows how Resource IDs are read from BIF entries.

---

## BZF [Compression](https://en.wikipedia.org/wiki/Data_compression)

BZF files are LZMA-compressed BIF files used primarily in iOS (and maybe Android) ports of KotOR. The BZF header contains `"BZF "` + `"V1.0"`, followed by LZMA-compressed BIF data. Decompression reveals a standard BIF structure.

### BZF Format Details

The BZF format wraps a complete BIF file in LZMA compression:

1. **BZF Header** (8 bytes): `"BZF "` + `"V1.0"` signature
2. **LZMA Stream**: Compressed BIF file data using LZMA algorithm
3. **Decompressed Result**: Standard BIF file structure (as described above)

**Compression Details:**

- The entire BIF file (after the 8-byte header) is compressed using LZMA (Lempel-Ziv-Markov chain Algorithm)
- LZMA provides high compression ratios with good decompression speed
- The compressed stream follows immediately after the BZF header
- Decompression yields a standard BIF file that can be read normally

**Benefits of BZF:**

- Significantly reduced file sizes (typically 40-60% compression ratio)
- Faster download times for mobile platforms
- Reduced storage requirements
- Identical resource access after decompression
- No performance penalty during gameplay (decompressed once at load time)

**Platform Usage:**

- PC releases use uncompressed BIF files for faster access
- Mobile releases (iOS/Android) use BZF for storage efficiency
- Modding tools can (and should) convert between BIF and BZF formats freely

**Implementation Notes:**

The BZF wrapper is completely transparent to the game engine - once decompressed in memory, the resource access patterns are identical to standard BIF files. Tools should decompress BZF files before reading resource entries, as the variable resource table offsets are relative to the decompressed BIF structure.

**Reference**: [`vendor/xoreos/src/aurora/biffile.h:56-60`](https://github.com/xoreos/xoreos/blob/master/src/aurora/biffile.h#L56-L60) documents BZF as compressed BIF files found exclusively in Android and iOS versions. [`vendor/reone/src/libs/resource/format/bifreader.cpp:27-30`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/bifreader.cpp#L27-L30) shows BIF signature detection. [`Libraries/PyKotor/src/pykotor/resource/formats/bif/bif_data.py:45-52`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bif/bif_data.py#L45-L52) documents BZF compression details.

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
