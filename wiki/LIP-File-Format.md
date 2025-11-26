# KotOR LIP File Format Documentation

LIP (Lip Synchronization) files drive mouth animation for voiced dialogue. Each file contains a compact series of [keyframes](https://en.wikipedia.org/wiki/Key_frame) that map timestamps to discrete [viseme](https://en.wikipedia.org/wiki/Viseme) (mouth shape) indices so that the engine can [interpolate](https://en.wikipedia.org/wiki/Interpolation) character lip movement while playing the companion WAV line.

## Table of Contents

- [KotOR LIP File Format Documentation](#kotor-lip-file-format-documentation)
  - [Table of Contents](#table-of-contents)
  - [File Structure Overview](#file-structure-overview)
  - [Binary Format](#binary-format)
    - [Header](#header)
    - [Keyframe Table](#keyframe-table)
  - [Mouth Shapes (Viseme Table)](#mouth-shapes-viseme-table)
  - [Animation Rules](#animation-rules)
  - [Implementation Details](#implementation-details)

---

## File Structure Overview

- LIP files are always **[binary](https://en.wikipedia.org/wiki/Binary_file)** (`"LIP V1.0"` signature) and contain only animation data.  
- They are paired with WAV voice-over resources of identical duration; the LIP `length` field must match the WAV `data` playback time for glitch-free animation.  
- [Keyframes](https://en.wikipedia.org/wiki/Key_frame) are sorted chronologically and store a timestamp ([float](https://en.wikipedia.org/wiki/Single-precision_floating-point_format) seconds) plus a 1-byte [viseme](https://en.wikipedia.org/wiki/Viseme) index (0–15).  
- The layout is identical across `vendor/reone`, `vendor/xoreos`, `vendor/Kotor.NET`, `vendor/KotOR.js`, and `vendor/mdlops`, so the header/keyframe offsets below are cross-confirmed against those implementations.  

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/lip/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/lip)

---

## Binary Format

### Header

| Name          | Type    | Offset | Size | Description |
| ------------- | ------- | ------ | ---- | ----------- |
| File Type     | char[4] | 0x00   | 4    | Always `"LIP "` |
| File Version  | char[4] | 0x04   | 4    | Always `"V1.0"` |
| Sound Length  | [float32](https://en.wikipedia.org/wiki/Single-precision_floating-point_format) | 0x08   | 4    | Duration in seconds (must equal WAV length) |
| Entry Count   | [uint32](https://en.wikipedia.org/wiki/Integer_(computer_science))  | 0x0C   | 4    | Number of keyframes immediately following |

**Reference:** [`vendor/reone/src/libs/graphics/format/lipreader.cpp:27-42`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/lipreader.cpp#L27-L42)

### Keyframe Table

Keyframes follow immediately after the header; there is no padding.

| Name       | Type    | Offset (per entry) | Size | Description |
| ---------- | ------- | ------------------ | ---- | ----------- |
| Timestamp  | [float32](https://en.wikipedia.org/wiki/Single-precision_floating-point_format) | 0x00               | 4    | Seconds from animation start |
| Shape      | [uint8](https://en.wikipedia.org/wiki/Integer_(computer_science))   | 0x04               | 1    | [Viseme](https://en.wikipedia.org/wiki/Viseme) index (`0–15`) |

- Entries are stored sequentially and **must** be sorted ascending by timestamp.  
- Libraries average multiple implementations to validate this layout (`vendor/reone`, `vendor/xoreos`, `vendor/KotOR.js`, `vendor/Kotor.NET`).  

**Reference:** [`vendor/KotOR.js/src/resource/LIPObject.ts:93-146`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/LIPObject.ts#L93-L146)

---

## Mouth Shapes (Viseme Table)

KotOR reuses the 16-shape Preston Blair [phoneme](https://en.wikipedia.org/wiki/Phoneme) set. Every implementation agrees on the byte value assignments; KotOR.js only renames a few labels but the indices match.

| Value | Shape | Description |
| ----- | ----- | ----------- |
| 0 | NEUTRAL | Rest/closed mouth |
| 1 | EE | Teeth apart, wide smile (long “ee”) |
| 2 | EH | Relaxed mouth (“eh”) |
| 3 | AH | Mouth open (“ah/aa”) |
| 4 | OH | Rounded lips (“oh”) |
| 5 | OOH | Pursed lips (“oo”, “w”) |
| 6 | Y | Slight smile (“y”) |
| 7 | STS | Teeth touching (“s”, “z”, “ts”) |
| 8 | FV | Lower lip touches teeth (“f”, “v”) |
| 9 | NG | Tongue raised (“n”, “ng”) |
| 10 | TH | Tongue between teeth (“th”) |
| 11 | MPB | Lips closed (“m”, “p”, “b”) |
| 12 | TD | Tongue up (“t”, “d”) |
| 13 | SH | Rounded relaxed (“sh”, “ch”, “j”) |
| 14 | L | Tongue forward (“l”, “r”) |
| 15 | KG | Back of tongue raised (“k”, “g”, “h”) |

**Reference:** [`Libraries/PyKotor/src/pykotor/resource/formats/lip/lip_data.py:50-169`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/lip/lip_data.py#L50-L169)

---

## Animation Rules

- **[Interpolation](https://en.wikipedia.org/wiki/Interpolation):** The engine interpolates between consecutive [keyframes](https://en.wikipedia.org/wiki/Key_frame); PyKotor exposes `LIP.get_shapes()` to compute the left/right [visemes](https://en.wikipedia.org/wiki/Viseme) plus blend factor.  
  **Reference:** [`Libraries/PyKotor/src/pykotor/resource/formats/lip/lip_data.py:342-385`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/lip/lip_data.py#L342-L385)
- **Sorting:** When adding frames, PyKotor removes existing entries at the same timestamp and keeps the list sorted.  
  **Reference:** [`Libraries/PyKotor/src/pykotor/resource/formats/lip/lip_data.py:305-323`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/lip/lip_data.py#L305-L323)
- **Duration Alignment:** LIP `length` is updated to the max timestamp so exported animations stay aligned with their WAV line.  
  **Reference:** [`Libraries/PyKotor/src/pykotor/resource/formats/lip/lip_data.py:267-323`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/lip/lip_data.py#L267-L323)
- **Generation:** Automated pipelines (MDLOps, KotORBlender) map phonemes to visemes via `LIPShape.from_phoneme()`, and the same mapping table appears in the vendor projects referenced above to keep authoring tools consistent.  

---

## Implementation Details

- **Binary Reader:** [`Libraries/PyKotor/src/pykotor/resource/formats/lip/io_lip.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/lip/io_lip.py)  
- **Data Model:** [`Libraries/PyKotor/src/pykotor/resource/formats/lip/lip_data.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/lip/lip_data.py)  
- **Reference Implementations:**  
  - [`vendor/reone/src/libs/graphics/format/lipreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/lipreader.cpp)  
  - [`vendor/xoreos/src/aurora/lipfile.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/lipfile.cpp)  
  - [`vendor/KotOR.js/src/resource/LIPObject.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/LIPObject.ts)  
  - [`vendor/Kotor.NET/Kotor.NET/Formats/KotorLIP/LIP.cs`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorLIP/LIP.cs)  

The references above implement the same header layout and keyframe encoding, ensuring PyKotor stays compatible with the other toolchains.
