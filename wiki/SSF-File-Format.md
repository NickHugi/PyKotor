# KotOR SSF File Format Documentation

This document provides a detailed description of the SSF (Sound Set File) file format used in Knights of the Old Republic (KotOR) games. SSF files contain mappings from sound event types to string references (StrRefs) in the [TLK file](TLK-File-Format).

**For mod developers:** To modify SSF files in your mods, see the [TSLPatcher SSFList Syntax Guide](TSLPatcher-SSFList-Syntax). For general modding information, see [HoloPatcher README for Mod Developers](HoloPatcher-README-for-mod-developers.).

**Related formats:** SSF files reference [TLK files](TLK-File-Format) for string references (StrRefs) that point to the actual sound text strings.

## Table of Contents

- [KotOR SSF File Format Documentation](#kotor-ssf-file-format-documentation)
  - [Table of Contents](#table-of-contents)
  - [File Structure Overview](#file-structure-overview)
  - [Binary Format](#binary-format)
    - [File Header](#file-header)
    - [Sound Table](#sound-table)
  - [Sound Event Types](#sound-event-types)
  - [Implementation Details](#implementation-details)

---

## File Structure Overview

SSF files define a set of 28 sound effects that creatures can play during various game events (battle cries, pain grunts, selection sounds, etc.). The StrRefs point to entries in `dialog.tlk` which contain the actual WAV file references.

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/ssf/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/ssf/)

**Reference**: [`vendor/reone/src/libs/resource/format/ssfreader.cpp:26-32`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/ssfreader.cpp#L26-L32)

---

## Binary Format

### File Header

The file header is 12 bytes in size:

| Name                | Type    | Offset | Size | Description                                    |
| ------------------- | ------- | ------ | ---- | ---------------------------------------------- |
| File Type           | char[4] | 0      | 4    | Always `"SSF "` (space-padded)                 |
| File Version        | char[4] | 4      | 4    | Always `"V1.1"`                                 |
| Offset to Sound Table | uint32 | 8    | 4    | Offset to sound table (typically 12)          |

**Reference**: [`vendor/Kotor.NET/Kotor.NET/Formats/KotorSSF/SSFBinaryStructure.cs:10-91`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorSSF/SSFBinaryStructure.cs#L10-L91)

### Sound Table

The sound table contains 28 StrRef entries (112 bytes total):

| Name              | Type   | Offset | Size | Description                                                      |
| ----------------- | ------ | ------ | ---- | ---------------------------------------------------------------- |
| StrRef Array      | int32[] | 0      | 4×28 | Array of 28 StrRef values (one per sound event type)            |

Each entry is a StrRef (string reference) into `dialog.tlk`. Value `-1` indicates no sound for that event type.

**Reference**: [`vendor/reone/src/libs/resource/format/ssfreader.cpp:31`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/ssfreader.cpp#L31)

---

## Sound Event Types

The 28 sound event types correspond to array indices:

| Index | Event Type          | Description                                                      |
| ----- | ------------------- | ---------------------------------------------------------------- |
| 0     | BATTLE_CRY_1        | First battle cry                                                 |
| 1     | BATTLE_CRY_2        | Second battle cry                                                |
| 2     | BATTLE_CRY_3        | Third battle cry                                                 |
| 3     | SELECT_1            | First selection sound                                             |
| 4     | SELECT_2             | Second selection sound                                            |
| 5     | SELECT_3             | Third selection sound                                             |
| 6     | ATTACK_1             | First attack sound                                                |
| 7     | ATTACK_2             | Second attack sound                                               |
| 8     | ATTACK_3             | Third attack sound                                               |
| 9     | PAIN_1               | First pain grunt                                                  |
| 10    | PAIN_2               | Second pain grunt                                                 |
| 11    | PAIN_3               | Third pain grunt                                                  |
| 12    | LOW_HEALTH           | Low health warning                                                |
| 13    | DEAD                 | Death sound                                                       |
| 14    | CRITICAL_HIT         | Critical hit sound                                                |
| 15    | IMMUNE               | Immune to attack sound                                            |
| 16    | LAYING_MINE          | Laying mine sound                                                 |
| 17    | DISARM_MINE          | Disarming mine sound                                              |
| 18    | STUN                 | Stunned sound                                                     |
| 19    | UNLOCK_DOOR          | Unlocking door sound                                              |
| 20    | LOCK_DOOR            | Locking door sound                                                |
| 21    | UNLOCK_CONTAINER     | Unlocking container sound                                         |
| 22    | LOCK_CONTAINER       | Locking container sound                                          |
| 23    | UNLOCKABLE           | Unlockable object sound                                           |
| 24    | LOCKED               | Locked object sound                                               |
| 25    | ELEVATOR_MOVING       | Elevator moving sound                                             |
| 26    | WHIRL_WIND            | Whirlwind sound                                                   |
| 27    | POISONED              | Poisoned sound                                                    |

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/ssf/ssf_data.py:50-258`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/ssf/ssf_data.py#L50-L258)

---

## Implementation Details

**Binary Reading**: [`Libraries/PyKotor/src/pykotor/resource/formats/ssf/io_ssf.py`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/ssf/io_ssf.py)

**Binary Writing**: [`Libraries/PyKotor/src/pykotor/resource/formats/ssf/io_ssf.py`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/ssf/io_ssf.py)

**SSF Class**: [`Libraries/PyKotor/src/pykotor/resource/formats/ssf/ssf_data.py:50-258`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/ssf/ssf_data.py#L50-L258)

---

This documentation aims to provide a comprehensive overview of the KotOR SSF file format, focusing on the detailed file structure and data formats used within the games.
