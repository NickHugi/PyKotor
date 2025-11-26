# KotOR TLK File Format Documentation

This document provides a detailed description of the TLK (Talk Table) file format used in Knights of the Old Republic (KotOR) games. TLK files contain all text strings used in the game, both written and spoken, enabling easy [localization](https://en.wikipedia.org/wiki/Internationalization_and_localization) by providing a [lookup table](https://en.wikipedia.org/wiki/Lookup_table) from string reference numbers (StrRef) to localized text and associated voice-over audio files.

**For mod developers:** To modify TLK files in your mods, see the [TSLPatcher TLKList Syntax Guide](TSLPatcher-TLKList-Syntax). For general modding information, see [HoloPatcher README for Mod Developers](HoloPatcher-README-for-mod-developers.).

**Related formats:** TLK files are referenced by [GFF files](GFF-File-Format) (especially DLG dialogue files), [2DA files](2DA-File-Format) for item names and descriptions, and [SSF files](SSF-File-Format) for character sound sets.

## Table of Contents

- [KotOR TLK File Format Documentation](#kotor-tlk-file-format-documentation)
  - [Table of Contents](#table-of-contents)
  - [File Structure Overview](#file-structure-overview)
  - [Binary Format](#binary-format)
    - [File Header](#file-header)
    - [String Data Table](#string-data-table)
    - [String Entries](#string-entries)
  - [TLKEntry Structure](#tlkentry-structure)
  - [String References (StrRef)](#string-references-strref)
    - [Custom TLK Files](#custom-tlk-files)
  - [Localization](#localization)
  - [Implementation Details](#implementation-details)

---

## File Structure Overview

TLK files store localized strings in a [binary format](https://en.wikipedia.org/wiki/Binary_file). The game loads `dialog.tlk` at startup and references strings throughout the game using StrRef numbers ([array indices](https://en.wikipedia.org/wiki/Array_data_structure)).

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/tlk/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/tlk/)

**Reference**: [`vendor/TSLPatcher/lib/site/Bioware/TLK.pm:1-533`](https://github.com/th3w1zard1/TSLPatcher/blob/master/lib/site/Bioware/TLK.pm#L1-L533)

---

## Binary Format

### File Header

The file header is 20 bytes in size:

| Name                | Type    | Offset | Size | Description                                    |
| ------------------- | ------- | ------ | ---- | ---------------------------------------------- |
| File Type           | char[4] | 0      | 4    | Always `"TLK "` (space-padded)                  |
| File Version        | char[4] | 4      | 4    | `"V3.0"` for KotOR, `"V4.0"` for Jade Empire  |
| Language ID         | int32   | 8      | 4    | Language identifier (see [Localization](#localization)) |
| String Count        | int32   | 12     | 4    | Number of string entries in the file           |
| String Entries Offset | int32 | 16     | 4    | Offset to string entries array (typically 20)  |

**Reference**: [`vendor/reone/src/libs/resource/format/tlkreader.cpp:31-84`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/tlkreader.cpp#L31-L84)

### String Data Table

The string data table contains metadata for each string entry. Each entry is 40 bytes:

| Name              | Type      | Offset | Size | Description                                                      |
| ----------------- | --------- | ------ | ---- | ---------------------------------------------------------------- |
| Flags             | uint32    | 0      | 4    | [Bit flags](https://en.wikipedia.org/wiki/Bit_field): bit 0=text present, bit 1=sound present, bit 2=sound length present |
| Sound ResRef      | char[16]  | 4      | 16   | Voice-over audio filename ([null-terminated](https://en.wikipedia.org/wiki/Null-terminated_string), max 16 chars)        |
| Volume Variance   | uint32    | 20     | 4    | Unused in KotOR (always 0)                                      |
| Pitch Variance    | uint32    | 24     | 4    | Unused in KotOR (always 0)                                      |
| Offset to String  | uint32    | 28     | 4    | Offset to string text (relative to String Entries Offset)       |
| String Size       | uint32    | 32     | 4    | Length of string text in bytes                                  |
| Sound Length      | float     | 36     | 4    | Duration of voice-over audio in seconds                         |

**Reference**: [`vendor/Kotor.NET/Kotor.NET/Formats/KotorTLK/TLKBinaryStructure.cs:57-90`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorTLK/TLKBinaryStructure.cs#L57-L90)

**Flag Bits:**

- **Bit 0 (0x0001)**: Text present - string has text content
- **Bit 1 (0x0002)**: Sound present - string has associated voice-over audio
- **Bit 2 (0x0004)**: Sound length present - sound length field is valid

**Flag Combinations:**

Common flag patterns in KotOR TLK files:

| Flags | Hex | Description | Usage |
| ----- | --- | ----------- | ----- |
| `0x0001` | `0x01` | Text only | Menu options, item descriptions, non-voiced dialog |
| `0x0003` | `0x03` | Text + Sound | Voiced dialog lines (most common for party/NPC speech) |
| `0x0007` | `0x07` | Text + Sound + Length | Fully voiced with duration data (cutscenes, important dialog) |
| `0x0000` | `0x00` | Empty entry | Unused StrRef slots |

The engine uses these flags to decide:

- Whether to display subtitles (Text present flag)
- Whether to play voice-over audio (Sound present flag)
- How long to wait before auto-advancing dialog (Sound length present flag)

Missing flags are treated as `false` - if Text present is not set, the string is treated as empty even if text data exists.

### String Entries

String entries follow the string data table:

| Name         | Type   | Description                                                      |
| ------------ | ------ | ---------------------------------------------------------------- |
| String Text  | char[] | [Null-terminated](https://en.wikipedia.org/wiki/Null-terminated_string) string data ([UTF-8](https://en.wikipedia.org/wiki/UTF-8) or [Windows-1252](https://en.wikipedia.org/wiki/Windows-1252) encoded)     |

String text is stored at the offset specified in the string data table entry. The encoding depends on the language ID (see [Localization](#localization)).

---

## TLKEntry Structure

Each TLK entry contains:

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/tlk/tlk_data.py:293-424`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/tlk/tlk_data.py#L293-L424)

| Attribute        | Type   | Description                                                      |
| ---------------- | ------ | ---------------------------------------------------------------- |
| `text`           | str    | Localized text string                                            |
| `voiceover`      | ResRef | Voice-over audio filename (WAV file)                            |
| `text_present`   | bool   | Whether text content exists                                      |
| `sound_present`  | bool   | Whether voice-over audio exists                                  |
| `soundlength_present` | bool | Whether sound length is valid                                    |
| `sound_length`   | [float](https://en.wikipedia.org/wiki/Single-precision_floating-point_format)  | Duration of voice-over audio in seconds                         |

---

## String References (StrRef)

String references (StrRef) are integer indices into the TLK file's entry array:

- **StrRef 0**: First entry in the TLK file
- **StrRef -1**: No string reference (used to indicate missing/empty strings)
- **StrRef N**: Nth entry (0-based indexing)

The game uses StrRef values throughout GFF files, scripts, and other resources to reference localized text. When displaying text, the game looks up the StrRef in `dialog.tlk` and displays the corresponding text.

### Custom TLK Files

Mods can add custom TLK files to extend available strings:

**Dialog.tlk Structure:**

- Base game: `dialog.tlk` (read-only, ~50,000-100,000 entries)
- Custom content: `dialogf.tlk` or custom TLK files placed in override

**StrRef Ranges:**

- `0` to `~50,000`: Base game strings (varies by language)
- `16,777,216` (`0x01000000`) and above: Custom TLK range (TSLPatcher convention)
- Negative values: Invalid/missing references

**Mod Tools Approach:**

TSLPatcher and similar tools use high StrRef ranges for custom strings:

```plaintext
Base StrRef:   0 - 50,000 (dialog.tlk)
Custom Range:  16777216+ (custom TLK files)
```

This avoids conflicts with base game strings and allows mods to add thousands of custom text entries without overwriting existing content.

**Multiple TLK Files:**

The game can load multiple TLK files:

1. `dialog.tlk` - Primary game text
2. `dialogf.tlk` - Female-specific variants (polish K1 only)

Priority: Custom TLKs → dialogf.tlk → dialog.tlk

**Reference**: [`vendor/TSLPatcher/lib/site/Bioware/TLK.pm:31-123`](https://github.com/th3w1zard1/TSLPatcher/blob/master/lib/site/Bioware/TLK.pm#L31-L123)

---

## Localization

TLK files support multiple languages through the Language ID field:

| Language ID | Language | Encoding      |
| ----------- | -------- | ------------- |
| 0           | English  | Windows-1252  |
| 1           | French   | Windows-1252  |
| 2           | German   | Windows-1252  |
| 3           | Italian  | Windows-1252  |
| 4           | Spanish  | Windows-1252  |
| 5           | Polish   | Windows-1250  |
| 6           | Korean   | UTF-8         |
| 7           | Chinese  | UTF-8         |
| 8           | Japanese | UTF-8         |

**Note**: KotOR games typically ignore the Language ID field and always use `dialog.tlk`. The field is primarily used by modding tools to identify language.

**Reference**: [`vendor/Kotor.NET/Kotor.NET/Formats/KotorTLK/TLKBinaryStructure.cs:63`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorTLK/TLKBinaryStructure.cs#L63)

---

## Implementation Details

**Binary Reading**: [`Libraries/PyKotor/src/pykotor/resource/formats/tlk/io_tlk.py:19-115`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/tlk/io_tlk.py#L19-L115)

**Binary Writing**: [`Libraries/PyKotor/src/pykotor/resource/formats/tlk/io_tlk.py:117-178`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/tlk/io_tlk.py#L117-L178)

**TLK Class**: [`Libraries/PyKotor/src/pykotor/resource/formats/tlk/tlk_data.py:56-291`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/tlk/tlk_data.py#L56-L291)

---

This documentation aims to provide a comprehensive overview of the KotOR TLK file format, focusing on the detailed file structure and data formats used within the games.
