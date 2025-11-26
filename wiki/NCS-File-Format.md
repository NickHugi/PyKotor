# KotOR NCS File Format Documentation

NCS files contain compiled NWScript [bytecode](https://en.wikipedia.org/wiki/Bytecode). Scripts run inside a [stack-based virtual machine](https://en.wikipedia.org/wiki/Stack_machine) shared by KotOR, NWN, and other Aurora-derived games. KotOR inherits the same format with minor [opcode](https://en.wikipedia.org/wiki/Opcode) additions for game-specific systems.

**For mod developers:** To modify NCS files directly in your mods (advanced), see [HoloPatcher README for Mod Developers](HoloPatcher-README-for-mod-developers.#hacklist-editing-ncs-directly) for HACKList syntax. For general modding information, see [HoloPatcher README for Mod Developers](HoloPatcher-README-for-mod-developers.).

## Table of Contents

- [KotOR NCS File Format Documentation](#kotor-ncs-file-format-documentation)
  - [Table of Contents](#table-of-contents)
  - [File Structure Overview](#file-structure-overview)
    - [Stack-Based Virtual Machine](#stack-based-virtual-machine)
  - [Header](#header)
  - [Instruction Encoding](#instruction-encoding)
    - [Bytecode](#bytecode)
    - [Qualifier](#qualifier)
    - [Arguments](#arguments)
    - [Instruction Encoding Examples](#instruction-encoding-examples)
      - [Example 1: Integer Constant](#example-1-integer-constant)
      - [Example 2: String Constant](#example-2-string-constant)
      - [Example 3: Jump Instruction](#example-3-jump-instruction)
      - [Example 4: Stack Copy Operation](#example-4-stack-copy-operation)
      - [Example 5: Engine Function Call](#example-5-engine-function-call)
      - [Example 6: Float Constant](#example-6-float-constant)
      - [Example 7: Object Constant (OBJECT\_SELF)](#example-7-object-constant-object_self)
      - [Example 8: Conditional Jump (JZ)](#example-8-conditional-jump-jz)
  - [Instruction Categories](#instruction-categories)
    - [Detailed Instruction Descriptions](#detailed-instruction-descriptions)
  - [Control Flow and Jumps](#control-flow-and-jumps)
    - [Subroutine Calls](#subroutine-calls)
    - [Jump Instructions](#jump-instructions)
  - [Implementation Details](#implementation-details)

---

## File Structure Overview

| Offset | Size | Description |
| ------ | ---- | ----------- |
| 0x00   | 4    | Signature `"NCS "` |
| 0x04   | 4    | Version `"V1.0"` |
| 0x08   | 1    | Program size marker opcode (`0x42`) |
| 0x09   | 4    | Total file size ([big-endian](https://en.wikipedia.org/wiki/Endianness) uint32) |
| 0x0D+  | —    | Stream of bytecode instructions |

- The VM executes sequential instructions; [control-flow](https://en.wikipedia.org/wiki/Control_flow) [opcodes](https://en.wikipedia.org/wiki/Opcode) ([`JMP`](https://en.wikipedia.org/wiki/Jump_instruction), [`JZ`](https://en.wikipedia.org/wiki/Branch_(computer_science)#Conditional_branch), [`JSR`](https://en.wikipedia.org/wiki/Subroutine)) adjust the [instruction pointer](https://en.wikipedia.org/wiki/Program_counter).  
- KotOR introduces no custom container sections—scripts are a flat stream.  
- All major reverse-engineered engines (`vendor/reone`, `vendor/xoreos`, `vendor/Kotor.NET`, `vendor/NorthernLights`) decode the same structure; KotOR.js uses a [WebAssembly](https://en.wikipedia.org/wiki/WebAssembly) VM but identical byte layouts.
- The program size marker at offset 8 (`0x42`) is not a real instruction but a metadata field containing the total file size. Execution begins at offset 13 (0x0D) after the header.

**Reference:** [`vendor/xoreos/src/aurora/nwscript/ncsfile.cpp:342-350`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/ncsfile.cpp#L342-L350), [`vendor/xoreos-tools/src/nwscript/ncsfile.cpp:116-125`](https://github.com/th3w1zard1/xoreos/blob/master/xoreos-tools/src/nwscript/ncsfile.cpp#L116-L125), [`vendor/reone/src/libs/script/format/ncsreader.cpp:28-40`](https://github.com/th3w1zard1/reone/blob/master/src/libs/script/format/ncsreader.cpp#L28-L40)

### Stack-Based Virtual Machine

NWScript uses a stack-based VM where all operations work on a stack rather than CPU registers. Stack grows downward with negative offsets, 4-byte aligned elements.

**[Stack Pointer](https://en.wikipedia.org/wiki/Stack_register) (SP):** `SP = (stackPtr + 1) * -4`. Stack positions are negative multiples of 4 (e.g., `-4`, `-8`, `-12`).

**Stack Layout Example:**

```plaintext
SP → -4:  j: 1        (topmost)
     -8:  i: 12       (second element)
     -12: (previous frame)
```

**Position Calculations:**

- Byte offset to position: `-offset / 4` (e.g., `-12` → position 3)
- Byte size to elements: `size / 4` (e.g., 12 bytes → 3 elements)

**Global Variables:** Accessed via [base pointer](https://en.wikipedia.org/wiki/Frame_pointer) (BP). The `#globals` routine initializes globals before `main()`, then `SAVEBP` saves current SP as BP. Functions access globals via `CPTOPBP`/`CPDOWNBP`. `RESTOREBP` restores previous BP.

**Stack Entry Types:**

- **Constants**: Immutable values (`CONSTx`) reawd from instructions — int, float, string, object
- **Variables**: Assignable stack slots created via `RSADDx`, modified via `CPDOWNSP`/`CPDOWNBP`
- **Structures**: Composite types spanning multiple positions (vectors = 3 positions/12 bytes, custom = 4-byte multiples)

**Lifecycle:** Create (`CONSTx`, `RSADDx`, `CPTOPSP`) → Modify (`CPDOWNSP`, `INCxSP`) → Consume (operations, `MOVSP`) → Destroy (`DESTRUCT`)

**[Decompilation](https://en.wikipedia.org/wiki/Decompiler) Tracking:**

- **[Reference Counting](https://en.wikipedia.org/wiki/Reference_counting)**: Track variable usage per stack instance
- **Assignment Status**: Distinguish initialized vs uninitialized variables
- **[Type Inference](https://en.wikipedia.org/wiki/Type_inference)**: Infer types through operation chains
- **Structure Recognition**: 12-byte copies → vectors (z, y, x order), other multiples of 4 → custom structures
- **Variable Naming**: Generate names from type + position or infer from usage patterns

**Reference:** [`vendor/xoreos/src/aurora/nwscript/ncsfile.cpp:105-172`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/ncsfile.cpp#L105-L172) (SP/BP), [`vendor/xoreos/src/aurora/nwscript/ncsfile.cpp:389-394`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/ncsfile.cpp#L389-L394) (globals), [`vendor/xoreos/src/aurora/nwscript/ncsfile.cpp:1039-1060`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/ncsfile.cpp#L1039-L1060) (SAVEBP/RESTOREBP), [`vendor/reone/src/libs/script/format/ncsreader.cpp:52-97`](https://github.com/th3w1zard1/reone/blob/master/src/libs/script/format/ncsreader.cpp#L52-L97) (parsing), [`vendor/xoreos-tools/src/nwscript/ncsfile.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/xoreos-tools/src/nwscript/ncsfile.cpp) (decompilation), [`vendor/KotOR.js/src/odyssey/NWScriptInstance.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/NWScriptInstance.ts) (JS runtime), [`vendor/NorthernLights/Assets/Scripts/ncs/NCSReader.cs`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/ncs/NCSReader.cs) (Unity)

---

## Header

| Name              | Type    | Offset | Size | Description |
| ----------------- | ------- | ------ | ---- | ----------- |
| File Type         | char[4] | 0x00   | 4    | `"NCS "` (must match exactly, [ASCII](https://en.wikipedia.org/wiki/ASCII) bytes: `0x4E 0x43 0x53 0x20`) |
| File Version      | char[4] | 0x04   | 4    | `"V1.0"` (must match exactly, [ASCII](https://en.wikipedia.org/wiki/ASCII) bytes: `0x56 0x31 0x2E 0x30`) |
| Size Marker       | uint8   | 0x08   | 1    | Program size marker opcode (`0x42`) |
| Total File Size   | uint32  | 0x09   | 4    | Total file size in bytes ([big-endian](https://en.wikipedia.org/wiki/Endianness)) |

The header is 13 bytes total. The size marker (`0x42`) is not a real instruction but a metadata field. All implementations validate that this byte equals `0x42` before reading the size field. The actual instruction stream begins at offset 13 (0x0D).

**Header Validation:**

All implementations validate:

1. File signature: `"NCS V1.0"` (bytes `[0x4E, 0x43, 0x53, 0x20, 0x56, 0x31, 0x2E, 0x30]`)
2. Size marker at offset 8: `0x42` (metadata, not an instruction)
3. File size ([big-endian](https://en.wikipedia.org/wiki/Endianness) uint32 at offset 9) ≤ actual file size
4. Seek to offset 13 (0x0D) to begin parsing

Reject file if any validation fails.

**Reference:** [`vendor/reone/src/libs/script/format/ncsreader.cpp:28-40`](https://github.com/th3w1zard1/reone/blob/master/src/libs/script/format/ncsreader.cpp#L28-L40) (header reading and validation), [`vendor/xoreos/src/aurora/nwscript/ncsfile.cpp:333-350`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/ncsfile.cpp#L333-L350) (includes validation of 0x42 marker), [`vendor/xoreos-tools/src/nwscript/ncsfile.cpp:106-125`](https://github.com/th3w1zard1/xoreos/blob/master/xoreos-tools/src/nwscript/ncsfile.cpp#L106-L125) (header parsing utilities), [`vendor/NorthernLights/Assets/Scripts/ncs/NCSReader.cs:876-886`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/ncs/NCSReader.cs#L876-L886) (0x42 marker handling), [`vendor/Kotor.NET/Kotor.NET/Formats/KotorNCS/NCS.cs`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorNCS/NCS.cs) (header reading), [`Libraries/PyKotor/src/pykotor/resource/formats/ncs/io_ncs.py:62-93`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/ncs/io_ncs.py#L62-L93)

---

## Instruction Encoding

Every instruction is stored as:

```text
<bytecode: uint8> <qualifier: uint8> <arguments: variable>
```

PyKotor reuses the NWScript opcode table; each opcode accepts a specific qualifier/argument layout described below.

### Bytecode

[Bytecode](https://en.wikipedia.org/wiki/Bytecode) selects the fundamental instruction (stack manipulation, arithmetic, logic, control flow, etc.). KotOR supports the standard NWN [opcodes](https://en.wikipedia.org/wiki/Opcode) plus Bioware extensions such as `STORE_STATE`. See [`Libraries/PyKotor/src/pykotor/resource/formats/ncs/ncs_data.py:70-142`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/ncs/ncs_data.py#L70-L142).

### Qualifier

`qualifier` refines the instruction to specific operand types (e.g., `IntInt`, `FloatFloat`, `VectorVector`).  
Example: `ADDxx` with qualifier `IntInt` performs integer addition, while the same opcode with qualifier `FloatFloat` adds floats.

**Qualifier Type Values:**

**Unary Types (Single Operand):**

- `0x03` - Integer (I) - 4 bytes
- `0x04` - Float (F) - 4 bytes
- `0x05` - String (S) - 4 bytes (pointer to string data)
- `0x06` - Object (O) - 4 bytes (object ID)
- `0x10` - Effect - 4 bytes
- `0x11` - Event - 4 bytes
- `0x12` - Location - 4 bytes
- `0x13` - Talent - 4 bytes
- `0x10-0x1F` - Engine Types (reserved range for game-specific types)

**Binary Types (Two Operands):**

- `0x20` - Integer, Integer (II) - 4 bytes each
- `0x21` - Float, Float (FF) - 4 bytes each
- `0x22` - Object, Object (OO) - 4 bytes each
- `0x23` - String, String (SS) - 4 bytes each (pointers)
- `0x24` - Structure, Structure (TT) - variable size (must be multiple of 4)
- `0x25` - Integer, Float (IF) - 4 bytes each
- `0x26` - Float, Integer (FI) - 4 bytes each
- `0x30` - Effect, Effect - 4 bytes each
- `0x31` - Event, Event - 4 bytes each
- `0x32` - Location, Location - 4 bytes each
- `0x33` - Talent, Talent - 4 bytes each
- `0x30-0x39` - Engine Type pairs (reserved range)
- `0x3A` - Vector, Vector (VV) - 12 bytes each (3 floats: x, y, z)
- `0x3B` - Vector, Float (VF) - 12 bytes + 4 bytes
- `0x3C` - Float, Vector (FV) - 4 bytes + 12 bytes

**Special Type Values:**

- `0x00` - Void (no type, used for return types)
- `0x01` - Stack (internal type marker)

**Type Size Information:**

- All primitive types (int, float, string pointer, object ID, engine types) are 4 bytes
- Vectors are 12 bytes (3 consecutive floats)
- Structures have variable size but must be 4-byte aligned
- The TT (Structure) qualifier type is used for comparing ranges of elements on the stack, specifically for structures and vectors. When used with `EQUALTT` or `NEQUALTT`, it requires a 2-byte size field indicating how many bytes to compare (must be a multiple of 4).

**Type System Details:**

The qualifier byte system allows the same opcode to operate on different data types. Type qualifiers are organized into ranges:

- Unary types (0x03-0x1F): Single operand types
- Binary types (0x20-0x3C): Two operand type combinations
- Special types (0x00, 0x01): Void and internal stack marker

Vector types are special: they occupy 3 stack positions (12 bytes) but are treated as a single composite type. When operations involve vectors, all three float components are processed together.

**Reference:** [`vendor/reone/src/libs/script/format/ncsreader.cpp:42-190`](https://github.com/th3w1zard1/reone/blob/master/src/libs/script/format/ncsreader.cpp#L42-L190), [`vendor/xoreos/src/aurora/nwscript/ncsfile.h:131-177`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/ncsfile.h#L131-L177), [`vendor/Kotor.NET/Kotor.NET/Formats/KotorNCS/NCS.cs`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorNCS/NCS.cs), [`vendor/NorthernLights/Assets/Scripts/ncs/NCSReader.cs`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/ncs/NCSReader.cs), [`vendor/KotOR.js/src/odyssey/NWScriptInstruction.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/NWScriptInstruction.ts)

### Arguments

Instruction arguments follow the qualifier byte and vary by instruction type. All multi-byte values are stored in [**big-endian**](https://en.wikipedia.org/wiki/Endianness) byte order.

**Argument Format Patterns:**

1. **No Arguments** (2 bytes total: opcode + qualifier):
   - `RSADDx`, `LOGANDII`, `LOGORII`, `INCORII`, `EXCORII`, `BOOLANDII`, `EQUALxx` (non-struct), `NEQUALxx` (non-struct), `GEQxx`, `GTxx`, `LTxx`, `LEQxx`, `SHLEFTII`, `SHRIGHTII`, `USHRIGHTII`, `ADDxx`, `SUBxx`, `MULxx`, `DIVxx`, `MODII`, `NEGx`, `COMPI`, `RETN`, `NOTI`, `SAVEBP`, `RESTOREBP`, `NOP`

2. **Signed 32-bit Integer** (6 bytes total: opcode + qualifier + 4 bytes):
   - `MOVSP`: Stack pointer adjustment offset (signed, allows positive and negative adjustments)
   - `JMP`, `JSR`, `JZ`, `JNZ`: Relative jump offset (signed, from start of instruction, allows forward and backward jumps)
   - `INCxSP`, `DECxSP`, `INCxBP`, `DECxBP`: Stack/base pointer offset (signed, negative offsets access stack elements)
   - `CONSTO`: Object ID constant (signed 32-bit: `0x00000000` = OBJECT_SELF, `0x00000001` or `0xFFFFFFFF` = OBJECT_INVALID)

3. **Unsigned 32-bit Integer** (6 bytes total: opcode + qualifier + 4 bytes):
   - `CONSTI`: Integer constant (stored as unsigned 32-bit big-endian, but may represent signed integer values in the range -2³¹ to 2³¹-1)

4. **Signed 32-bit Integer Pair** (10 bytes total: opcode + qualifier + 4 bytes + 4 bytes):
   - `STORE_STATE`: Two signed 32-bit size fields (total 10 bytes: opcode + qualifier + int32 size + int32 sizeLocals). The first field (`size`) indicates the total number of bytes of stack state to store, and the second field (`sizeLocals`) indicates the number of bytes of local variables to preserve.

5. **32-bit Float** (6 bytes total):
   - `CONSTF`: Float constant ([IEEE 754](https://en.wikipedia.org/wiki/IEEE_754) [big-endian](https://en.wikipedia.org/wiki/Endianness))

6. **String** (variable length: 2 bytes length + string data):
   - `CONSTS`: 2-byte length prefix ([big-endian](https://en.wikipedia.org/wiki/Endianness) uint16) followed by string bytes ([ASCII](https://en.wikipedia.org/wiki/ASCII))

7. **Stack Copy Operations** (8 bytes total: opcode + qualifier + 4 bytes offset + 2 bytes size):
   - `CPDOWNSP`, `CPTOPSP`, `CPDOWNBP`, `CPTOPBP`: Signed 32-bit stack offset + unsigned 16-bit size
   - Stack offset conversion: Negative byte offsets are converted to stack positions by dividing by 4 (e.g., offset -4 becomes position 1, offset -8 becomes position 2)
   - Size field indicates number of bytes to copy (must be multiple of 4 for alignment)

8. **Engine Function Call** (5 bytes total: opcode + qualifier + 2 bytes routine + 1 byte arg count):
   - `ACTION`: Unsigned 16-bit routine number + unsigned 8-bit argument count
   - Routine number indexes into the engine's function table (actions data)
   - Argument count specifies how many stack elements (not bytes) to pass to the function

9. **Destruct Operation** (8 bytes total: opcode + qualifier + 2 bytes + 2 bytes + 2 bytes):
   - `DESTRUCT`: Format: `[0x21][qualifier][uint16 size][signed16 stackOffset][uint16 sizeNoDestroy]`
     - `size`: Total number of bytes to destroy from stack
     - `stackOffset`: Signed 16-bit offset from stack pointer indicating where destruction begins (converted to position by dividing by 4)
     - `sizeNoDestroy`: Number of bytes to preserve (not destroyed) within the destruction range
     - Used for complex stack cleanup when removing multiple elements while preserving specific values (e.g., when unpacking structures or vectors)

10. **Struct Comparison** (4 bytes total: opcode + qualifier + 2 bytes):

- `EQUALTT`, `NEQUALTT`: Format: `[0x0B/0x0C][0x24][uint16 size]`
  - `size`: Number of bytes to compare (must be multiple of 4, as structures are 4-byte aligned)
  - Compares two structures on the stack byte-by-byte for equality/inequality
  - Both structures must be the same size
  - Only used when qualifier is `0x24` (Structure, Structure)

**Jump Offset Calculation:**
Jump offsets are **relative to the start of the jump instruction itself**, not the next instruction. The offset is a signed 32-bit integer allowing both forward and backward jumps.

**Byte Order:**

All multi-byte values in NCS files are stored in **[big-endian](https://en.wikipedia.org/wiki/Endianness)** ([network byte order](https://en.wikipedia.org/wiki/Endianness#Networking)):

- 16-bit values (uint16, int16): Most significant byte first
- 32-bit values (uint32, int32, float32): Most significant byte first
- This applies to: offsets, sizes, constants, jump targets, and all numeric arguments

**Instruction Parsing:**

Standard process: Read opcode + qualifier → Determine argument format via lookup → Read arguments (0 to variable bytes) → Advance IP by total instruction size → Repeat until EOF

**Variable-Length Instructions:**

- `CONSTx` (0x04): Qualifier determines type: Int (4B), Float (4B [IEEE 754](https://en.wikipedia.org/wiki/IEEE_754)), String (2B length + data), Object (4B)
- `CPDOWNSP`/`CPTOPSP`/`CPDOWNBP`/`CPTOPBP` (0x01/0x03/0x26/0x27): 4B offset + 2B size
- `JMP`/`JSR`/`JZ`/`JNZ` (0x1D/0x1E/0x1F/0x25): 4B signed offset (relative to instruction start)
- `DESTRUCT` (0x21): 2B size + 2B stackOffset + 2B sizeNoDestroy
- `STORE_STATE` (0x2C): 4B size + 4B sizeLocals
- `ACTION` (0x05): 2B routine + 1B argCount
- `EQUALTT`/`NEQUALTT` with qualifier 0x24: 2B size (multiple of 4)

All multi-byte values: [big-endian](https://en.wikipedia.org/wiki/Endianness)

**Execution State:**

- **IP**: [Instruction pointer](https://en.wikipedia.org/wiki/Program_counter) (starts at 0x0D)
- **SP**: [Stack pointer](https://en.wikipedia.org/wiki/Stack_register) (top of data stack)
- **BP**: [Base pointer](https://en.wikipedia.org/wiki/Frame_pointer) (globals area, set by `SAVEBP`/`RESTOREBP`)
- **Return Stack**: Separate stack for `JSR`/`RETN` addresses

**Execution Loop:** Parse instruction → Execute (manipulate stack/IP/BP, call functions) → Advance IP → Repeat until termination

**Instruction Sizes:** 2B base + arguments: None (2B), Int/Float/Object (6B), String (2+N B), Jump (6B), Stack copy (8B), ACTION (5B), DESTRUCT (8B), STORE_STATE (10B), Struct compare (4B)

Static sizing enables: instruction list building, jump target resolution, [code coverage](https://en.wikipedia.org/wiki/Code_coverage), [static analysis](https://en.wikipedia.org/wiki/Static_program_analysis)

**Reference:** [`vendor/xoreos/src/aurora/nwscript/ncsfile.cpp:194-1649`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/ncsfile.cpp#L194-L1649), [`vendor/reone/src/libs/script/format/ncsreader.cpp:42-190`](https://github.com/th3w1zard1/reone/blob/master/src/libs/script/format/ncsreader.cpp#L42-L190), [`vendor/Kotor.NET/Kotor.NET/Formats/KotorNCS/NCS.cs`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorNCS/NCS.cs), [`vendor/NorthernLights/Assets/Scripts/ncs/NCSReader.cs`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/ncs/NCSReader.cs), [`vendor/xoreos-tools/src/nwscript/ncsfile.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/xoreos-tools/src/nwscript/ncsfile.cpp), [`vendor/KotOR.js/src/odyssey/NWScriptInstance.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/NWScriptInstance.ts), [`vendor/xoreos/src/aurora/nwscript/ncsfile.h:86-280`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/ncsfile.h#L86-L280)

### Instruction Encoding Examples

#### Example 1: Integer Constant

```text
Bytes: [0x04][0x03][0x00][0x00][0x00][0x2A]
       └─┬─┘ └─┬─┘ └──────────┬──────────┘
      CONST  Int         42 (big-endian)
```

Pushes integer value 42 onto the stack.

#### Example 2: String Constant

```text
Bytes: [0x04][0x05][0x00][0x05][0x48][0x65][0x6C][0x6C][0x6F]
       └─┬─┘ └─┬─┘ └─┬─┘ └──────────────────────────┬──────────────────┘
      CONST  Str  length=5                    "Hello"
```

Pushes string "Hello" onto the stack.

#### Example 3: Jump Instruction

```text
Bytes: [0x1D][0x00][0x00][0x00][0x00][0x10]
       └─┬─┘ └─┬─┘ └──────────┬──────────┘
        JMP  qualifier    offset=16 bytes forward
```

Jumps 16 bytes forward from the start of this instruction.

#### Example 4: Stack Copy Operation

```text
Bytes: [0x01][0x00][0xFF][0xFF][0xFF][0xFC][0x00][0x04]
       └─┬─┘ └─┬─┘ └──────────┬──────────┘ └─┬─┘
    CPDOWNSP qualifier   offset=-4 bytes    size=4
```

Copies 4 bytes from top of stack to offset -4 (one element down).

#### Example 5: Engine Function Call

```text
Bytes: [0x05][0x00][0x00][0x01][0x02]
       └─┬─┘ └─┬─┘ └─┬─┘ └─┬─┘
      ACTION qualifier routine=1  argCount=2
```

Calls engine routine #1 with 2 arguments (which must be on stack in reverse order).

#### Example 6: Float Constant

```text
Bytes: [0x04][0x04][0x40][0x49][0x0F][0xDB]
       └─┬─┘ └─┬─┘ └──────────┬──────────┘
      CONST Float        3.14159... ([big-endian](https://en.wikipedia.org/wiki/Endianness) [IEEE 754](https://en.wikipedia.org/wiki/IEEE_754))
```

Pushes float value approximately 3.14159 (π) onto the stack.

#### Example 7: Object Constant (OBJECT_SELF)

```text
Bytes: [0x04][0x06][0x00][0x00][0x00][0x00]
       └─┬─┘ └─┬─┘ └──────────┬──────────┘
      CONST Object      OBJECT_SELF (0x00000000)
```

Pushes OBJECT_SELF constant onto the stack.

#### Example 8: Conditional Jump (JZ)

```text
Bytes: [0x1F][0x00][0xFF][0xFF][0xFF][0xF0]
       └─┬─┘ └─┬─┘ └──────────┬──────────┘
        JZ  qualifier    offset=-16 bytes backward
```

Jumps 16 bytes backward if top of stack is zero (consumes the integer from stack).

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

### Detailed Instruction Descriptions

**Stack Manipulation:**

- `CPDOWNSP` (0x01): Copy bytes from top of stack down to specified offset. Format: `[0x01][qualifier][signed32 offset][uint16 size]`. SP remains unchanged. Used to write local variables.
- `CPTOPSP` (0x03): Copy bytes from specified offset to top of stack. Format: `[0x03][qualifier][signed32 offset][uint16 size]`. SP increases by `size` bytes. Used to read local variables.
- `MOVSP` (0x1B): Adjust stack pointer by specified value. Format: `[0x1B][qualifier][signed32 offset]`. Used to allocate/deallocate stack space for local variables.
- `CPDOWNBP` (0x26): Copy bytes from base pointer down to specified offset (for global variables). Format: `[0x26][qualifier][signed32 offset][uint16 size]`. SP remains unchanged. Used to write global variables.
- `CPTOPBP` (0x27): Copy bytes from specified offset relative to base pointer to top of stack (for global variables). Format: `[0x27][qualifier][signed32 offset][uint16 size]`. SP increases by `size` bytes. Used to read global variables.
- `SAVEBP` (0x2A): Save current BP and set BP to current stack position. Format: `[0x2A][qualifier]`. Used when entering a new function scope.
- `RESTOREBP` (0x2B): Restore BP from previous SAVEBP. Format: `[0x2B][qualifier]`. Used when exiting a function scope.
- `RSADDx` (0x02): Reserve space on stack for a variable of specified type. Format: `[0x02][qualifier]`. SP increases by 4 bytes (or 12 for vectors). Qualifier determines type: `0x03`=int, `0x04`=float, `0x05`=string, `0x06`=object, `0x10-0x1F`=engine types.
- `INCxSP` (0x24): Increment variable on stack at specified offset. Format: `[0x24][qualifier][signed32 offset]`. Qualifier `0x03`=int, `0x04`=float.
- `DECxSP` (0x23): Decrement variable on stack at specified offset. Format: `[0x23][qualifier][signed32 offset]`. Qualifier `0x03`=int, `0x04`=float.
- `INCxBP` (0x29): Increment global variable at specified base pointer offset. Format: `[0x29][qualifier][signed32 offset]`.
- `DECxBP` (0x28): Decrement global variable at specified base pointer offset. Format: `[0x28][qualifier][signed32 offset]`.

**Stack Operation Details:**

- Offsets: Always negative (e.g., -4, -8), positive = invalid
- Copy ops: Signed 32-bit offset + unsigned 16-bit size (must be 4-byte multiple)
- `MOVSP`: Adjust SP (positive = deallocate, negative = allocate)
- BP ops: Identical to SP ops but use base pointer (set by `SAVEBP`, points to globals)
- Multi-element copies (size > 4): May indicate composite types (vectors, structs)
- `CPDOWNSP`/`CPDOWNBP`: Store to stack (SP unchanged, source = top of stack)
- `CPTOPSP`/`CPTOPBP`: Load from stack (SP increases by copied size)

**Position Conversion:**

- Byte offset → position: `-offset / 4` (e.g., -8 → 2, -12 → 3)
- Size → elements: `size / 4` (e.g., 12B → 3 elements)
- Position → offset: `-position * 4`

**Examples:** Offset -4 = position 1 (top), -8 = position 2, vector (12B) at -12 = positions 1-3

**Reference:** [`vendor/xoreos/src/aurora/nwscript/ncsfile.cpp:458-545`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/ncsfile.cpp#L458-L545), [`vendor/reone/src/libs/script/format/ncsreader.cpp:52-97`](https://github.com/th3w1zard1/reone/blob/master/src/libs/script/format/ncsreader.cpp#L52-L97), [`vendor/xoreos/src/aurora/nwscript/ncsfile.cpp:105-172`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/ncsfile.cpp#L105-L172), [`vendor/Kotor.NET/Kotor.NET/Formats/KotorNCS/NCS.cs`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorNCS/NCS.cs), [`vendor/NorthernLights/Assets/Scripts/ncs/NCSReader.cs`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/ncs/NCSReader.cs), [`vendor/KotOR.js/src/odyssey/NWScriptInstance.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/NWScriptInstance.ts)

**Constants:**

All use opcode `0x04`, qualifier determines type:

- `CONSTI` (0x03): `[0x04][0x03][uint32]` (6B), SP+4, unsigned but can represent signed (-2³¹ to 2³¹-1)
- `CONSTF` (0x04): `[0x04][0x04][float32]` (6B), SP+4, [IEEE 754](https://en.wikipedia.org/wiki/IEEE_754) [big-endian](https://en.wikipedia.org/wiki/Endianness)
- `CONSTS` (0x05): `[0x04][0x05][uint16 len][ASCII](https://en.wikipedia.org/wiki/ASCII)` (2+N B), SP+4 (pointer only, content stored separately), no [null terminator](https://en.wikipedia.org/wiki/Null-terminated_string)
- `CONSTO` (0x06): `[0x04][0x06][signed32]` (6B), SP+4, special: `0x00000000` = OBJECT_SELF, `0x00000001`/`0xFFFFFFFF` = OBJECT_INVALID

**Parsing:** Read opcode (0x04) → qualifier → type-specific args (uint32/float32/string length+data/signed32)

**Behavior:** Read value → Create immutable constant entry → Push onto stack (SP+4) → Remains until consumed/removed

**Reference:** [`vendor/xoreos/src/aurora/nwscript/ncsfile.cpp:500-545`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/ncsfile.cpp#L500-L545), [`vendor/reone/src/libs/script/format/ncsreader.cpp:60-73`](https://github.com/th3w1zard1/reone/blob/master/src/libs/script/format/ncsreader.cpp#L60-L73), [`vendor/Kotor.NET/Kotor.NET/Formats/KotorNCS/NCS.cs`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorNCS/NCS.cs), [`vendor/NorthernLights/Assets/Scripts/ncs/NCSReader.cs`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/ncs/NCSReader.cs), [`vendor/xoreos-tools/src/nwscript/ncsfile.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/xoreos-tools/src/nwscript/ncsfile.cpp), [`vendor/KotOR.js/src/odyssey/NWScriptDef.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/NWScriptDef.ts)

**Arithmetic Operations:**

All arithmetic operations consume operands from the top of the stack and place the result back on the stack. SP increases by result size and decreases by total operand sizes.

- `ADDxx`: Addition (supports II, IF, FI, FF, SS, VV)
- `SUBxx`: Subtraction (supports II, IF, FI, FF, VV)
- `MULxx`: Multiplication (supports II, IF, FI, FF, VF, FV)
- `DIVxx`: Division (supports II, IF, FI, FF, VF)
- `MODII`: Modulus (integer only)
- `NEGx`: Negation (supports I, F)

**Bitwise and Logical Operations:**

- `LOGANDII` (0x06): Logical AND of two integers
- `LOGORII` (0x07): Logical OR of two integers
- `INCORII` (0x08): [Bitwise](https://en.wikipedia.org/wiki/Bitwise_operation) inclusive OR of two integers
- `EXCORII` (0x09): [Bitwise](https://en.wikipedia.org/wiki/Bitwise_operation) exclusive OR of two integers
- `BOOLANDII` (0x0A): Boolean/[bitwise](https://en.wikipedia.org/wiki/Bitwise_operation) AND of two integers
- `NOTI` (0x22): Logical NOT of an integer
- `COMPI` (0x1A): [One's complement](https://en.wikipedia.org/wiki/Ones%27_complement) of an integer
- `SHLEFTII` (0x11): [Shift](https://en.wikipedia.org/wiki/Bitwise_operation#Bit_shifts) integer left by specified number of bits
- `SHRIGHTII` (0x12): [Shift](https://en.wikipedia.org/wiki/Bitwise_operation#Bit_shifts) integer right by specified number of bits (signed)
- `USHRIGHTII` (0x13): Unsigned [shift](https://en.wikipedia.org/wiki/Bitwise_operation#Bit_shifts) integer right by specified number of bits

**Comparison Operations:**

- `EQUALxx` (0x0B): Test for equality. Format: `[0x0B][qualifier][optional: uint16 size for TT]`. Supports II, FF, SS, OO, TT, and engine types. For TT (struct) qualifier, includes 2-byte size field (must be multiple of 4). Pops two operands from stack, compares them, pushes 1 if equal else 0.
- `NEQUALxx` (0x0C): Test for inequality. Format: `[0x0C][qualifier][optional: uint16 size for TT]`. Same as EQUALxx but pushes 1 if not equal else 0.
- `GTxx` (0x0E): Greater than. Format: `[0x0E][qualifier]`. Supports II, FF. Pops two operands (top is right operand), pushes 1 if left > right else 0.
- `GEQxx` (0x0D): Greater than or equal. Format: `[0x0D][qualifier]`. Supports II, FF. Pops two operands, pushes 1 if left >= right else 0.
- `LTxx` (0x0F): Less than. Format: `[0x0F][qualifier]`. Supports II, FF. Pops two operands, pushes 1 if left < right else 0.
- `LEQxx` (0x10): Less than or equal. Format: `[0x10][qualifier]`. Supports II, FF. Pops two operands, pushes 1 if left <= right else 0.

**Comparison Operation Details:**

- Comparison operations pop two operands from the stack and push a single integer result (1 for true, 0 for false)
- For binary comparisons (GT, GEQ, LT, LEQ), the top of stack is the right operand, and the value below it is the left operand
- Structure comparisons (`EQUALTT`, `NEQUALTT`) perform byte-by-byte comparison of the specified number of bytes
- The size field for structure comparisons must be a multiple of 4 to maintain alignment
- String comparisons compare string pointers (4-byte values), not string contents directly

**Reference:** [`vendor/xoreos/src/aurora/nwscript/ncsfile.cpp:712-768`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/ncsfile.cpp#L712-L768) (comparison opcode implementation), [`vendor/reone/src/libs/script/format/ncsreader.cpp:102-105`](https://github.com/th3w1zard1/reone/blob/master/src/libs/script/format/ncsreader.cpp#L102-L105) (comparison instruction parsing), [`vendor/Kotor.NET/Kotor.NET/Formats/KotorNCS/NCS.cs`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorNCS/NCS.cs) (comparison operation handling)

**Control Flow:**

- `JMP` (0x1D): Unconditional jump to relative offset. Format: `[0x1D][qualifier][signed32 offset]`. Offset is relative to the start of the JMP instruction. Used for loops and unconditional branches.
- `JSR` (0x1E): Jump to subroutine at relative offset. Format: `[0x1E][qualifier][signed32 offset]`. Pushes return address onto return stack, then jumps. Used for function calls within the script.
- `JZ` (0x1F): Jump if top of stack is zero. Format: `[0x1F][qualifier][signed32 offset]`. Consumes integer from top of stack (SP decreases by 4). If value is zero, jumps to offset; otherwise continues to next instruction.
- `JNZ` (0x25): Jump if top of stack is non-zero. Format: `[0x25][qualifier][signed32 offset]`. Consumes integer from top of stack (SP decreases by 4). If value is non-zero, jumps to offset; otherwise continues to next instruction.
- `RETN` (0x20): Return from subroutine. Format: `[0x20][qualifier]`. Pops return address from return stack and jumps to it. Used to exit script subroutines.
- `DESTRUCT` (0x21): Destroy elements on stack, preserving specified element. Format: `[0x21][qualifier][uint16 size][signed16 stackOffset][uint16 sizeNoDestroy]` (8 bytes total). This instruction performs complex stack cleanup by removing `size` bytes from the stack starting at `stackOffset`, but preserves `sizeNoDestroy` bytes within that range. The `stackOffset` is a signed 16-bit value converted to a stack position by dividing by 4. Used for complex stack cleanup operations, particularly when unpacking structures or vectors where only specific elements need to be preserved. The preserved element is moved to the top of the stack after destruction.

**DESTRUCT Operation Details:**

The DESTRUCT instruction is used in scenarios where multiple stack elements need to be removed, but a specific element within that range must be preserved:

1. The instruction identifies a range of stack elements starting at `stackOffset` and extending for `size` bytes
2. Within that range, `sizeNoDestroy` bytes starting at a calculated position are preserved
3. All other bytes in the range are removed from the stack
4. The preserved element is moved to the top of the stack (SP position 1)
5. This is commonly used when unpacking structures: the structure occupies multiple stack positions, but only one field needs to be extracted

The `stackOffset` parameter is a signed 16-bit value that is converted to a stack position by dividing by 4. The offset is relative to the current stack pointer, with negative values indicating positions deeper on the stack. The `size` parameter indicates the total number of bytes to destroy, and `sizeNoDestroy` indicates how many bytes within that range should be preserved.

Example: If a structure occupies positions 3-5 (12 bytes) and only the middle element (position 4) needs to be preserved, DESTRUCT would remove positions 3 and 5 while keeping position 4, then move it to the top.

**DESTRUCT Format:**

- Opcode: `0x21`
- Qualifier: Typically `0x00` (not used for type determination)
- Arguments: `[uint16 size][int16 stackOffset][uint16 sizeNoDestroy]` (6 bytes total, 8 bytes including opcode and qualifier)
- The preserved element is extracted from the destruction range and placed at the top of the stack, effectively replacing the destroyed elements with just the preserved value.

During decompilation, DESTRUCT identifies structure field accesses (preserved element position → field).

- `STORE_STATE` (0x2C): Save stack state for delayed execution. Format: `[0x2C][qualifier][int32 size][int32 sizeLocals]` (10B). Used with `DelayCommand`. `size` = total stack bytes, `sizeLocals` = local variable bytes. Separates temp values from persistent locals. Decompilers typically emit as-is with comments.

**Control Flow Details:**

- Jump offsets: Relative to instruction start (not end), signed 32-bit (±2GB range)
- `JSR`: Separate return stack (not data stack), return addr = after JSR
- `RETN`: Pop return addr from return stack, empty stack = main/error
- `JZ`/`JNZ`: Consume top int (removed regardless of jump)
- `DESTRUCT`: Atomic multi-element removal with preservation (structure unpacking)

**Examples:** JMP @100 +20 → 120, JZ @200 -16 → 184, JSR @300 +50 → 350 (return addr 306)

**Reference:** [`vendor/xoreos/src/aurora/nwscript/ncsfile.cpp:712-768`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/ncsfile.cpp#L712-L768), [`vendor/reone/src/libs/script/format/ncsreader.cpp:81-91`](https://github.com/th3w1zard1/reone/blob/master/src/libs/script/format/ncsreader.cpp#L81-L91), [`vendor/Kotor.NET/Kotor.NET/Formats/KotorNCS/NCS.cs`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorNCS/NCS.cs), [`vendor/NorthernLights/Assets/Scripts/ncs/NCSReader.cs`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/ncs/NCSReader.cs), [`vendor/xoreos-tools/src/nwscript/ncsfile.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/xoreos-tools/src/nwscript/ncsfile.cpp), [`vendor/KotOR.js/src/odyssey/controllers/NWScriptController.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/controllers/NWScriptController.ts)

**Engine Function Calls:**

- `ACTION` (0x05): Format: `[0x05][0x00][uint16 routine][uint8 argCount]` (5B). Routine = index into engine function table (K1/K2 differ). Args in reverse order (last on top). Engine removes args, pushes return value. Vectors = 3 floats (x, y, z). Synchronous execution.

**Function Table:**

Engine-specific mapping: routine number → function (name, params, return type). Used for decompilation (routine 1 → `GetFirstObject`). Invalid routine = error.

**Actions Data File:** Lists engine functions, format: `return_type function_name(param_type param, ...)`. Example: `int GetFirstObject(int nObjectFilter, object oArea);`

The decompiler parses this file to build a lookup table mapping routine numbers (indices in the file) to function signatures. This allows the decompiler to generate readable function calls instead of raw `ACTION` instructions with numeric routine IDs.

**See [NSS File Format](NSS-File-Format.md) for complete documentation of nwscript.nss, function definitions, and KotOR-specific functions/constants.**

**Reference:** [`vendor/xoreos/src/aurora/nwscript/ncsfile.cpp:643-660`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/ncsfile.cpp#L643-L660) (ACTION opcode implementation), [`vendor/reone/src/libs/script/format/ncsreader.cpp:74-77`](https://github.com/th3w1zard1/reone/blob/master/src/libs/script/format/ncsreader.cpp#L74-L77) (ACTION instruction parsing), [`vendor/Kotor.NET/Kotor.NET/Formats/KotorNCS/NCS.cs`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorNCS/NCS.cs) (ACTION instruction handling), [`vendor/NorthernLights/Assets/Scripts/ncs/NCSReader.cs`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/ncs/NCSReader.cs) (engine function call processing), [`vendor/xoreos-tools/src/nwscript/ncsfile.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/xoreos-tools/src/nwscript/ncsfile.cpp) (actions data parsing for decompilation)

**Special Instructions:**

- `NOP` (0x2D): No-operation, used as placeholder for debugger. Format: `[0x2D][qualifier]`. Does nothing, SP remains unchanged.
- Program size marker (0x42): Always found at offset 8 in NCS file header. Format: `[0x42][uint32 fileSize]`. This is not a real instruction and is never executed. It contains the total file size in bytes (big-endian). All implementations validate this marker before parsing instructions.

**Note:** All multi-byte values in NCS files are stored in **[big-endian](https://en.wikipedia.org/wiki/Endianness)** byte order. This includes all integers, floats, offsets, and size fields.

**Special Instruction Details:**

- `NOP` (0x2D) is a no-operation instruction that does nothing. It is typically used as a placeholder by debuggers or during script compilation. The qualifier is typically `0x00`.
- The program size marker (0x42) at offset 8 is never executed as an instruction. It is a metadata field that all implementations check before parsing the instruction stream. If this byte is not `0x42`, implementations should reject the file as invalid.

**Reference:** [`vendor/xoreos/src/aurora/nwscript/ncsfile.cpp:342-350`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/ncsfile.cpp#L342-L350) (header validation including 0x42 check), [`vendor/xoreos-docs/specs/torlack/ncs.html`](https://github.com/th3w1zard1/xoreos-docs/blob/master/specs/torlack/ncs.html) (Torlack's original NCS specification), [`vendor/NorthernLights/Assets/Scripts/ncs/NCSReader.cs:876-886`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/ncs/NCSReader.cs#L876-L886) (0x42 marker handling), [`vendor/Kotor.NET/Kotor.NET/Formats/KotorNCS/NCS.cs`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorNCS/NCS.cs) (NOP instruction handling), [`Libraries/PyKotor/src/pykotor/resource/formats/ncs/ncs_data.py:144-242`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/ncs/ncs_data.py#L144-L242) (instruction definitions)

---

## Control Flow and Jumps

- Jump instructions store relative offsets; readers resolve them to absolute positions.  
- PyKotor's `NCS` class tracks instruction objects and rewires the `jump` attribute so tooling can walk the control-flow graph without recomputing offsets.  
- Subroutines use `JSR` (push return address) and `RETN` (pop address and jump back).  
- `STORE_STATE`/`DESTRUCT` manage VM save/restore for suspended scripts (cutscenes, dialogs); the semantics are identical in Reone and Kotor.NET, while KotOR.js mirrors them for deterministic playback.

### Subroutine Calls

**Calling Conventions:**

**Script Subroutines:** Reserve return space → Push args (reverse) → `JSR` → Subroutine removes args → Return value at reserved location

**Engine Routines:** Push args (reverse) → `ACTION` (routine #, arg count) → Engine removes args → Engine pushes return

**Example:** `int j = DoSomeScriptSubroutine(12, 14);`

Before: `SP → -4: Arg1(12), -8: Arg2(14), -12: Return(??), -16: j(??)`  
After: `SP → -4: Return(??), -8: j(??)`

**Example Stack Layout for Engine Routine Call:**

Before call to `int j = DoSomeEngineRoutine(12, 14);`:

```plaintext
SP → -4:  Arg1: 12
     -8:  Arg2: 14
     -12: j: ??
```

After call:

```plaintext
SP → -4:  Return: ??
     -8:  j: ??
```

### Jump Instructions

All jump instructions use **relative offsets** from the start of the jump instruction itself:

- `JMP`: Unconditional jump to offset
- `JZ`: Jump if top of stack is zero (consumes the integer from stack)
- `JNZ`: Jump if top of stack is non-zero (consumes the integer from stack)
- `JSR`: Jump to subroutine (pushes return address, then jumps)

The offset is a signed 32-bit integer stored in [big-endian](https://en.wikipedia.org/wiki/Endianness) format, allowing forward and backward jumps within the script. The offset is calculated as: `target_address - instruction_address`.

**Jump Resolution:** Offsets resolved to absolute instruction pointers during parsing. PyKotor's `NCS` class stores direct instruction references in `jump` attribute for [CFG](https://en.wikipedia.org/wiki/Control-flow_graph) traversal. Format: Signed 32-bit [big-endian](https://en.wikipedia.org/wiki/Endianness), `target = instruction_addr + offset`, forward (+) or backward (-).

**Reference:** [`Libraries/PyKotor/src/pykotor/resource/formats/ncs/ncs_data.py:244-421`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/ncs/ncs_data.py#L244-L421) (instruction data model with jump resolution), [`Libraries/PyKotor/src/pykotor/resource/formats/ncs/io_ncs.py:262-269`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/ncs/io_ncs.py#L262-L269) (jump offset reading), [`vendor/reone/src/libs/script/format/ncsreader.cpp:81-85`](https://github.com/th3w1zard1/reone/blob/master/src/libs/script/format/ncsreader.cpp#L81-L85) (jump instruction parsing), [`vendor/xoreos/src/aurora/nwscript/ncsfile.cpp:712-768`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/ncsfile.cpp#L712-L768) (jump instruction execution), [`vendor/Kotor.NET/Kotor.NET/Formats/KotorNCS/NCS.cs`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorNCS/NCS.cs) (jump instruction handling)

---

## Implementation Details

**Reference Implementations:**

- [`vendor/reone/src/libs/script/format/ncsreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/script/format/ncsreader.cpp) - C++ reader/parser
- [`vendor/xoreos/src/aurora/nwscript/ncsfile.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/ncsfile.cpp) - C++ execution engine
- [`vendor/xoreos-tools/src/nwscript/ncsfile.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/xoreos-tools/src/nwscript/ncsfile.cpp) - Decompilation tools
- [`vendor/Kotor.NET/Kotor.NET/Formats/KotorNCS/NCS.cs`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorNCS/NCS.cs) - C# format
- [`vendor/NorthernLights/Assets/Scripts/ncs/NCSReader.cs`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/ncs/NCSReader.cs) - Unity C#
- [`vendor/KotOR.js/src/resource/NCSResource.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/NCSResource.ts) - TypeScript
- [`vendor/kotor-savegame-editor/src/formats/ncs.ts`](https://github.com/th3w1zard1/kotor-savegame-editor/blob/master/src/formats/ncs.ts) - TypeScript parser
- [`vendor/xoreos-docs/specs/torlack/ncs.html`](https://github.com/th3w1zard1/xoreos-docs/blob/master/specs/torlack/ncs.html) - Original specification

All use identical [opcodes](https://en.wikipedia.org/wiki/Opcode) (0x01-0x2D, 0x42 marker), qualifiers (0x03-0x3C), and [big-endian](https://en.wikipedia.org/wiki/Endianness) encoding.

**Instruction Sizes:** Base 2B + args: None (0B), Int/Float (4B), String (2+N B), Stack copy (6B), ACTION (3B), DESTRUCT (6B), STORE_STATE (8B), Struct compare (2B)

**Compatibility:** All implementations use identical [opcodes](https://en.wikipedia.org/wiki/Opcode) (0x01-0x2D, 0x42), qualifiers (0x03-0x3C), and [big-endian](https://en.wikipedia.org/wiki/Endianness) encoding, ensuring cross-engine compatibility (same ACTION routine table required).

**Decompilation Overview:**

Core analyses: Stack tracking (variable assignments/reads via copy ops), Control flow (jumps → if/loops/switches), Subroutine analysis (JSR → function calls, infer params/returns), Variable naming (type + position or usage patterns), [Dead code elimination](https://en.wikipedia.org/wiki/Dead_code_elimination)

**Analysis Passes:**

1. **Parse**: [Bytecode](https://en.wikipedia.org/wiki/Bytecode) → instructions + [control flow graph](https://en.wikipedia.org/wiki/Control-flow_graph) (jumps as edges)
2. **Subroutines**: Identify boundaries via `JSR`/`RETN`, analyze separately
3. **[Type Inference](https://en.wikipedia.org/wiki/Type_inference)**: Operations reveal types (`ADDII` → ints, calls → engine function table)
4. **Prototyping**: Infer subroutine signatures from usage (may need multiple passes for recursion)
5. **Stack Tracking**: Track state per instruction (variables, types, assignment), clone/merge at control flow joins
6. **Structure Recognition**: 12-byte copies → vectors, other multiples of 4 → custom structs
7. **Control Flow**: Jumps → `if`/loops (forward jumps = conditionals, backward = loops), multi-target = switch
8. **Code Gen**: Emit source with named variables, typed declarations, high-level constructs
9. **Cleanup**: Remove [dead code](https://en.wikipedia.org/wiki/Dead_code_elimination), optimize names, format

**Stack Analysis Details:**

- **Variables**: `CPDOWNSP`/`CPDOWNBP` = writes, `CPTOPSP`/`CPTOPBP` = reads, offset identifies variable, size determines primitive vs composite
- **Scope**: `MOVSP` = function entry/exit (negative = allocate, positive = deallocate)
- **Structures**: Vectors (12B) = z/y/x order, nested structures require hierarchy tracking
- **Globals**: BP operations, separate from locals (SP operations)
- **State Merging**: Converging paths require merging stack states (variables on all paths preserved)
- **[Reference Counting](https://en.wikipedia.org/wiki/Reference_counting)**: Track usage per stack instance, zero refs + unassigned = placeholder
- **Return Values**: Track separately, identified from stack state before `RETN`/after `JSR`

**Reference:** [`vendor/xoreos-tools/src/nwscript/ncsfile.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/xoreos-tools/src/nwscript/ncsfile.cpp), [`vendor/xoreos-tools/src/nwscript/decompiler.cpp`](https://github.com/th3w1zard1/xoreos-tools/blob/master/src/nwscript/decompiler.cpp), [`vendor/reone/src/libs/script/format/ncsreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/script/format/ncsreader.cpp), [`vendor/Kotor.NET/Kotor.NET/Formats/KotorNCS/NCS.cs`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorNCS/NCS.cs), [`vendor/xoreos/src/aurora/nwscript/ncsfile.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/ncsfile.cpp), [`vendor/kotor-savegame-editor/src/formats/ncs.ts`](https://github.com/th3w1zard1/kotor-savegame-editor/blob/master/src/formats/ncs.ts), [`vendor/NorthernLights/Assets/Scripts/ncs/NCSDecompiler.cs`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/ncs/NCSDecompiler.cs)
