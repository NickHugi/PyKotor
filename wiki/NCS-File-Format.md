# KotOR NCS File Format Documentation

NCS files contain compiled NWScript bytecode. Scripts run inside a [stack-based virtual machine](https://en.wikipedia.org/wiki/Stack_machine) shared by KotOR, NWN, and other Aurora-derived games. KotOR inherits the same format with minor opcode additions for game-specific systems.

## Table of Contents

- [KotOR NCS File Format Documentation](#kotor-ncs-file-format-documentation)
  - [Table of Contents](#table-of-contents)
  - [File Structure Overview](#file-structure-overview)
  - [Header](#header)
  - [Instruction Encoding](#instruction-encoding)
    - [Bytecode](#bytecode)
    - [Qualifier](#qualifier)
    - [Arguments](#arguments)
  - [Instruction Categories](#instruction-categories)
  - [Control Flow and Jumps](#control-flow-and-jumps)
  - [Implementation Details](#implementation-details)

---

## File Structure Overview

| Offset | Size | Description |
| ------ | ---- | ----------- |
| 0x00   | 4    | Signature `"NCS "` |
| 0x04   | 4    | Version `"V1.0"` |
| 0x08+  | —    | Stream of bytecode instructions |

- The VM executes sequential instructions; control-flow opcodes ([`JMP`](https://en.wikipedia.org/wiki/Jump_instruction), [`JZ`](https://en.wikipedia.org/wiki/Branch_(computer_science)#Conditional_branch), [`JSR`](https://en.wikipedia.org/wiki/Subroutine)) adjust the instruction pointer.  
- KotOR introduces no custom container sections—scripts are a flat stream.  
- All major reverse-engineered engines (`vendor/reone`, `vendor/xoreos`, `vendor/Kotor.NET`, `vendor/NorthernLights`) decode the same structure; KotOR.js uses a wasm VM but identical byte layouts.  

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/ncs/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/ncs)

---

## Header

| Name         | Type    | Offset | Size | Description |
| ------------ | ------- | ------ | ---- | ----------- |
| File Type    | char[4] | 0x00   | 4    | `"NCS "` |
| File Version | char[4] | 0x04   | 4    | `"V1.0"` |
| First Opcode | uint8   | 0x08   | 1    | Opcode of the first instruction (reading continues immediately) |

**Reference:** [`vendor/reone/src/libs/script/format/ncsreader.cpp:27-48`](https://github.com/th3w1zard1/reone/blob/master/src/libs/script/format/ncsreader.cpp#L27-L48)

---

## Instruction Encoding

Every instruction is stored as:

```text
<bytecode: uint8> <qualifier: uint8> <arguments: variable>
```

PyKotor reuses the NWScript opcode table; each opcode accepts a specific qualifier/argument layout described below.

### Bytecode

`bytecode` selects the fundamental instruction (stack manipulation, arithmetic, logic, control flow, etc.). KotOR supports the standard NWN opcodes plus Bioware extensions such as `STORE_STATE`. See [`Libraries/PyKotor/src/pykotor/resource/formats/ncs/ncs_data.py:70-142`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/ncs/ncs_data.py#L70-L142).

### Qualifier

`qualifier` refines the instruction to specific operand types (e.g., `IntInt`, `FloatFloat`, `VectorVector`).  
Example: `ADDxx` with qualifier `IntInt` performs integer addition, while the same opcode with qualifier `FloatFloat` adds floats.

**Reference:** [`Libraries/PyKotor/src/pykotor/resource/formats/ncs/ncs_data.py:119-143`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/ncs/ncs_data.py#L119-L143)

### Arguments

- **Immediate values**: `CONSTI`, `CONSTS`, `CONSTO`, etc., embed literal data after the qualifier.  
- **Offsets / Jump targets**: Control-flow opcodes store signed 32-bit offsets relative to the next instruction.  
- **Stack offsets**: `CPDOWNSP`, `CPTOPSP`, `RSADDx` include 16-bit stack offsets.  

PyKotor stores instructions as objects containing the decoded arguments and a pointer to the jump target if applicable.

**Reference:** [`vendor/xoreos/src/aurora/nwscript/ncsfile.cpp:194-1649`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/ncsfile.cpp#L194-L1649)

---

## Instruction Categories

| Category | Opcodes |
| -------- | ------- |
| Stack | `CPDOWNSP`, `CPTOPSP`, `MOVSP`, `CPDOWNBP`, `CPTOPBP`, `SAVEBP`, `RESTOREBP`, `INCxSP`, `DECxSP`, `INCxBP`, `DECxBP` |
| Constants | `CONSTI`, `CONSTF`, `CONSTS`, `CONSTO`, and typed variants |
| Arithmetic | `ADDxx`, `SUBxx`, `MULxx`, `DIVxx`, `MODxx`, `NEGx` |
| Bitwise/Logic | `LOGANDxx`, `LOGORxx`, `INCORxx`, `EXCORxx`, `BOOLANDxx`, `NOTx`, `COMPx`, `SHLEFTxx`, `SHRIGHTxx`, `USHRIGHTxx` |
| Comparison | `EQUALxx`, `NEQUALxx`, `GTxx`, `GEQxx`, `LTxx`, `LEQxx` |
| Control Flow | `JMP`, `JSR`, `JZ`, `JNZ`, `RETN`, `STORE_STATE`, `DESTRUCT` |
| Function Calls | `ACTION` (invokes engine-exposed script functions) |

**Reference:** [`Libraries/PyKotor/src/pykotor/resource/formats/ncs/ncs_data.py:144-242`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/ncs/ncs_data.py#L144-L242)

---

## Control Flow and Jumps

- Jump instructions store relative offsets; readers resolve them to absolute positions.  
- PyKotor’s `NCS` class tracks instruction objects and rewires the `jump` attribute so tooling can walk the control-flow graph without recomputing offsets.  
- Subroutines use `JSR` (push return address) and `RETN` (pop address and jump back).  
- `STORE_STATE`/`DESTRUCT` manage VM save/restore for suspended scripts (cutscenes, dialogs); the semantics are identical in Reone and Kotor.NET, while KotOR.js mirrors them for deterministic playback.  

**Reference:** [`Libraries/PyKotor/src/pykotor/resource/formats/ncs/ncs_data.py:244-421`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/ncs/ncs_data.py#L244-L421)

---

## Implementation Details

- **Binary Reader/Writer:** [`Libraries/PyKotor/src/pykotor/resource/formats/ncs/io_ncs.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/ncs/io_ncs.py)  
- **Data Model:** [`Libraries/PyKotor/src/pykotor/resource/formats/ncs/ncs_data.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/ncs/ncs_data.py)  
- **Reference Implementations:**  
  - [`vendor/reone/src/libs/script/format/ncsreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/script/format/ncsreader.cpp)  
  - [`vendor/xoreos/src/aurora/nwscript/ncsfile.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/ncsfile.cpp)  
  - [`vendor/Kotor.NET/Kotor.NET/Formats/KotorNCS/NCS.cs`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorNCS/NCS.cs)  
  - [`vendor/NorthernLights/nwnnsscomp/`](https://github.com/th3w1zard1/NorthernLights/tree/master/nwnnsscomp) (original Bioware compiler)  

The projects above implement the same opcode set and qualifier table, so scripts authored for PyKotor remain compatible with the other engines.
