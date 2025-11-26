# KotOR NSS File Format Documentation

NSS (NWScript Source) files contain human-readable NWScript source code that compiles to [NCS bytecode](NCS-File-Format). The `nwscript.nss` file defines all engine-exposed functions and constants available to scripts. KotOR 1 and KotOR 2 each have their own `nwscript.nss` with game-specific functions and constants.

## Table of Contents

<!-- TOC_START -->
<!-- TOC_END -->

## PyKotor Implementation

PyKotor implements `nwscript.nss` definitions in three Python modules:

### Data Structures

**`Libraries/PyKotor/src/pykotor/common/script.py`:**

- `ScriptFunction`: Represents a function signature with return type, name, parameters, description, and raw string
- `ScriptParam`: Represents a function parameter with type, name, and optional default value
- `ScriptConstant`: Represents a constant with type, name, and value
- `DataType`: Enumeration of all NWScript data types (INT, FLOAT, STRING, OBJECT, VECTOR, etc.)

**`Libraries/PyKotor/src/pykotor/common/scriptdefs.py`:**

- `KOTOR_FUNCTIONS`: List of 772 `ScriptFunction` objects for KotOR 1
- `TSL_FUNCTIONS`: List of functions for KotOR 2 (The Sith Lords)
- `KOTOR_CONSTANTS`: List of 1489 `ScriptConstant` objects for KotOR 1
- `TSL_CONSTANTS`: List of constants for KotOR 2

**`Libraries/PyKotor/src/pykotor/common/scriptlib.py`:**

- `KOTOR_LIBRARY`: Dictionary mapping library file names to their source code content (e.g., `"k_inc_generic"`, `"k_inc_utility"`)
- `TSL_LIBRARY`: Dictionary for KotOR 2 library files

### Compilation Integration

During NSS compilation (see [`Libraries/PyKotor/src/pykotor/resource/formats/ncs/ncs_auto.py:126-205`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/ncs/ncs_auto.py#L126-L205)):

1. **Parser Initialization**: The `NssParser` is created with game-specific functions and constants:

   ```python
   nss_parser = NssParser(
       functions=KOTOR_FUNCTIONS if game.is_k1() else TSL_FUNCTIONS,
       constants=KOTOR_CONSTANTS if game.is_k1() else TSL_CONSTANTS,
       library=KOTOR_LIBRARY if game.is_k1() else TSL_LIBRARY,
       library_lookup=lookup_arg,
   )
   ```

2. **Function Resolution**: When the parser encounters a function call, it:
   - Looks up the function name in the functions list
   - Validates parameter types and counts
   - Resolves the routine number (index in the functions list)
   - Generates an `ACTION` instruction with the routine number

3. **Constant Resolution**: When the parser encounters a constant:
   - Looks up the constant name in the constants list
   - Replaces the constant with its value
   - Generates appropriate `CONSTx` instruction

4. **Library Inclusion**: When the parser encounters `#include`:
   - Looks up the library name in the library dictionary
   - Parses the included source code
   - Merges functions and constants into the current scope

**Reference:** [`Libraries/PyKotor/src/pykotor/common/script.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/common/script.py) (data structures), [`Libraries/PyKotor/src/pykotor/common/scriptdefs.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/common/scriptdefs.py) (function/constant definitions), [`Libraries/PyKotor/src/pykotor/common/scriptlib.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/common/scriptlib.py) (library files)

---

## Shared Functions (K1 & TSL)

<!-- SHARED_FUNCTIONS_START -->
<!-- SHARED_FUNCTIONS_END -->

## K1-Only Functions

<!-- K1_ONLY_FUNCTIONS_START -->
<!-- K1_ONLY_FUNCTIONS_END -->

## TSL-Only Functions

<!-- TSL_ONLY_FUNCTIONS_START -->
<!-- TSL_ONLY_FUNCTIONS_END -->

## Shared Constants (K1 & TSL)

<!-- SHARED_CONSTANTS_START -->
<!-- SHARED_CONSTANTS_END -->

## K1-Only Constants

<!-- K1_ONLY_CONSTANTS_START -->
<!-- K1_ONLY_CONSTANTS_END -->

## TSL-Only Constants

<!-- TSL_ONLY_CONSTANTS_START -->
<!-- TSL_ONLY_CONSTANTS_END -->

## Compilation Process

When compiling NSS to NCS (see [`Libraries/PyKotor/src/pykotor/resource/formats/ncs/ncs_auto.py:126-205`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/ncs/ncs_auto.py#L126-L205)):

1. **Parser Creation**: `NssParser` initialized with game-specific functions/constants
2. **Source Parsing**: NSS source code parsed into Abstract Syntax Tree (AST)
3. **Function Resolution**: Function calls resolved to routine numbers via function list lookup
4. **Constant Substitution**: Constants replaced with their literal values
5. **Bytecode Generation**: AST compiled to NCS bytecode instructions
6. **Optimization**: Post-compilation optimizers applied (NOP removal, etc.)

**Function Call Resolution:**

```nss
// Source code
int result = GetGlobalNumber("K_QUEST_COMPLETED");
```

```nss
// Compiler looks up "GetGlobalNumber" in KOTOR_FUNCTIONS
// Finds it at index 159 (routine number)
// Generates: ACTION 159 with 1 argument (string "K_QUEST_COMPLETED")
```

**Constant Resolution:**

```nss
// Source code
if (nPlanet == PLANET_TARIS) { ... }
```

```nss
// Compiler looks up PLANET_TARIS in KOTOR_CONSTANTS
// Finds value: 1
// Generates: CONSTI 1 (pushes integer 1 onto stack)
```

**Reference:** [`Libraries/PyKotor/src/pykotor/resource/formats/ncs/ncs_auto.py:126-205`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/ncs/ncs_auto.py#L126-L205), [`wiki/NCS-File-Format.md#engine-function-calls`](NCS-File-Format#engine-function-calls)

---

## Commented-Out Elements in nwscript.nss

The `nwscript.nss` files in KOTOR 1 and 2 contain numerous constants and functions that are commented out (prefixed with `//`). These represent features from the original Neverwinter Nights (NWN) scripting system that were not implemented or supported in the Aurora engine variant used by KOTOR. BioWare deliberately disabled these elements to prevent crashes, errors, or undefined behavior if used.

### Reasons for Commented-Out Elements

KOTOR's `nwscript.nss` retains many NWN-era declarations but prefixes unsupported ones with `//` to disable them during compilation. This deliberate choice by BioWare ensures:

- **Engine Compatibility**: KOTOR's Aurora implementation lacks opcodes or assets for certain NWN features (e.g., advanced animations, UI behaviors), leading to crashes or no-ops if invoked.

- **Modder Safety**: Prevents accidental use in custom scripts, which would fail at runtime. File-internal comments often explicitly state `// disabled` (e.g., for creature orientation in dialogues).

- **Game-Specific Differences**: K1 and K2/TSL `nwscript.nss` vary slightly; K2 has a notorious syntax error in `SetOrientOnClick` (fixed by modders via override).

No official BioWare documentation explains this (as KOTOR predates widespread modding support), but forum consensus attributes it to engine streamlining for single-player RPG vs. NWN's multiplayer focus.

### Key Examples of Commented Elements

| Category | Examples | Notes from nwscript.nss |
|----------|----------|-------------------------|
| Animations | `//int ANIMATION_LOOPING_LOOK_FAR = 5;`<br>`//int ANIMATION_LOOPING_SIT_CHAIR = 6;`<br>`//int ANIMATION_LOOPING_SIT_CROSS = 7;` | Not usable in KOTOR; modders note them when scripting custom behaviors. |
| Effects/Functions | `EffectMovementSpeedIncrease` (with detailed commented description) | Function exists but capped (~200%); higher values ignored, despite "turbo" cheat allowing more. |
| Behaviors | `SetOrientOnClick` | Syntax-broken in early K2; comments note `// disabled` for orient-to-player on click. |

### Common Modder Workarounds

Modders have developed several strategies for working with commented-out elements:

- **Override nwscript.nss**: Extract from `scripts.bif` via Holocron Toolset, fix issues (e.g., K2 syntax error at line ~5710), place in `Override` folder for compilers/DeNCS.

- **Add custom constants**: Modders append new ones (e.g., for feats) rather than uncommenting old.

- **Avoid direct edits**: Messing with core declarations risks compilation failures across all scripts.

**Standard Override Workflow:**

1. Extract via Holocron Toolset (`scripts.bif > Script, Source > nwscript.nss`).
2. Edit (fix/add), save as `.nss` in `Override`.
3. Use with `nwnnsscomp` for compilation.

**K2 Syntax Fix:**

The notorious K2 syntax error in `SetOrientOnClick` can be fixed by changing:

```nss
void SetOrientOnClick( object = OBJECT_SELF, ... )
```

to:

```nss
void SetOrientOnClick( object oCreature = OBJECT_SELF, ... )
```

### Forum Discussions and Community Knowledge

Modding communities actively reference these commented sections, especially on **Deadly Stream** (primary KOTOR hub), **LucasForums archives**, **Holowan Laboratories** (via MixNMojo/Mixmojo forums), and Reddit.

| Forum | Key Threads | Topics Covered |
|-------|-------------|----------------|
| Deadly Stream | [Script Shack](https://deadlystream.com/topic/4808-fair-strides-script-shack/page/7/), [nwscript.nss Request](https://deadlystream.com/topic/6892-nwscriptnss/) | Animations, overrides |
| LucasForums Archive | [Syntax Error](https://www.lucasforumsarchive.com/thread/142901-syntax-error-in-kotor2-nwscriptnss), [Don't Mess with It](https://www.lucasforumsarchive.com/thread/168643-im-trying-to-change-classes2da) | Fixes, warnings |
| Reddit r/kotor | [Movement Speed](https://www.reddit.com/r/kotor/comments/9dr8iy/modding_question_movement_speed_increase_in_k2/) | Effect caps |
| Czerka R&D Wiki | [nwscript.nss](https://czerka-rd.fandom.com/wiki/Nwscript.nss) | General documentation |

**Notable Discussion Points:**

- **Deadly Stream - Fair Strides' Script Shack** (2016 thread, 100+ pages): Users troubleshooting animations flag the exact commented lines (e.g., `ANIMATION_LOOPING_*`), confirming they can't be used natively. No successful uncommenting reported; focus on alternatives like `ActionPlayAnimation` workarounds.

- **Reddit r/kotor** (2018): Thread on speed boosts quotes the commented description for `EffectMovementSpeedIncrease` (line ~165). Users test values >200% (no effect due to cap), note "turbo" cheat bypasses it partially.

- **LucasForums Archive** (2004-2007 threads): Multiple posts warn against editing `nwscript.nss` ("very bad idea... loads of trouble"). Syntax fix for K2 widely shared; `// disabled` snippets appear in context of `SetOrientOnClick`.

### Attempts to Uncomment or Modify

- **Direct Uncommenting**: No documented successes; implied to cause runtime crashes (engine lacks implementation). Forums advise against.

- **Overrides & Additions**: Standard modding workflow (see above). Examples: TSLPatcher/TSL Patcher tools bundle fixed versions; mods like Hardcore/Improved AI reference custom includes (not core uncomments).

- **Advanced Usage**: DeNCS/ncs2nss require game-specific `nwscript.nss` for accurate decompiles; modders parse it for custom tools.

In summary, while no one has publicly shared a "uncomment everything" patch (likely futile), the modding scene thrives on careful overrides, with thousands of posts across these sites confirming the practice since 2003.

### Key Citations

- [Deadly Stream: Fair Strides' Script Shack](https://deadlystream.com/topic/4808-fair-strides-script-shack/page/7/)
- [Czerka Wiki: nwscript.nss](https://czerka-rd.fandom.com/wiki/Nwscript.nss)
- [LucasForums: Syntax Error in K2 nwscript.nss](https://www.lucasforumsarchive.com/thread/142901-syntax-error-in-kotor2-nwscriptnss)
- [Reddit: Movement Speed Modding](https://www.reddit.com/r/kotor/comments/9dr8iy/modding_question_movement_speed_increase_in_k2/)
- [Deadly Stream: nwscript.nss Thread](https://deadlystream.com/topic/6892-nwscriptnss/)
- [LucasForums: Warning on Editing nwscript.nss](https://www.lucasforumsarchive.com/thread/168643-im-trying-to-change-classes2da)

---

## Reference Implementations

**Parsing nwscript.nss:**

- [`vendor/reone/src/apps/dataminer/routines.cpp:149-184`](https://github.com/th3w1zard1/reone/blob/master/src/apps/dataminer/routines.cpp#L149-L184) - Parses nwscript.nss using regex patterns for constants and functions
- [`vendor/reone/src/apps/dataminer/routines.cpp:382-427`](https://github.com/th3w1zard1/reone/blob/master/src/apps/dataminer/routines.cpp#L382-L427) - Extracts functions from nwscript.nss in chitin.key for K1 and K2
- [`vendor/xoreos-tools/src/nwscript/actions.cpp`](https://github.com/th3w1zard1/xoreos-tools/blob/master/src/nwscript/actions.cpp) - Actions data parsing for decompilation
- [`vendor/xoreos-tools/src/nwscript/ncsfile.cpp`](https://github.com/th3w1zard1/xoreos-tools/blob/master/src/nwscript/ncsfile.cpp) - NCS file parsing with actions data integration
- [`vendor/NorthernLights/Assets/Scripts/ncs/nwscript_actions.cs`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/ncs/nwscript_actions.cs) - Unity C# actions table
- [`vendor/NorthernLights/Assets/Scripts/ncs/nwscript.cs`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/ncs/nwscript.cs) - Unity C# NWScript class
- [`vendor/KotOR-Scripting-Tool/NWN Script/NWScriptParser.cs`](https://github.com/th3w1zard1/KotOR-Scripting-Tool/blob/master/NWN%20Script/NWScriptParser.cs) - C# parser for nwscript.nss

**Function Definitions:**

- [`vendor/KotOR.js/src/nwscript/NWScript.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScript.ts) - TypeScript function definitions
- [`vendor/KotOR.js/src/nwscript/NWScriptDefK1.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptDefK1.ts) - KotOR 1 definitions
- [`vendor/KotOR.js/src/nwscript/NWScriptDefK2.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptDefK2.ts) - KotOR 2 definitions
- [`vendor/KotOR.js/src/nwscript/NWScriptParser.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptParser.ts) - TypeScript parser for nwscript.nss
- [`vendor/KotOR.js/src/nwscript/NWScriptCompiler.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptCompiler.ts) - TypeScript NSS compiler
- [`vendor/KotOR.js/src/nwscript/NWScriptInstructionSet.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptInstructionSet.ts) - Instruction set definitions
- [`vendor/KotOR.js/src/nwscript/NWScriptConstants.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptConstants.ts) - Constant definitions
- [`vendor/HoloLSP/server/src/nwscript/`](https://github.com/th3w1zard1/HoloLSP/blob/master/server/src/nwscript/) - Language server definitions
- [`vendor/HoloLSP/server/src/nwscript-parser.ts`](https://github.com/th3w1zard1/HoloLSP/blob/master/server/src/nwscript-parser.ts) - Language server parser
- [`vendor/HoloLSP/server/src/nwscript-lexer.ts`](https://github.com/th3w1zard1/HoloLSP/blob/master/server/src/nwscript-lexer.ts) - Language server lexer
- [`vendor/HoloLSP/server/src/nwscript-ast.ts`](https://github.com/th3w1zard1/HoloLSP/blob/master/server/src/nwscript-ast.ts) - Language server AST
- [`vendor/HoloLSP/syntaxes/nwscript.tmLanguage.json`](https://github.com/th3w1zard1/HoloLSP/blob/master/syntaxes/nwscript.tmLanguage.json) - TextMate syntax definition
- [`vendor/nwscript-mode.el/nwscript-mode.el`](https://github.com/th3w1zard1/nwscript-mode.el/blob/master/nwscript-mode.el) - Emacs mode for NWScript
- [`vendor/nwscript-ts-mode/`](https://github.com/th3w1zard1/nwscript-ts-mode) - TypeScript mode for NWScript

**Original Sources:**

- [`vendor/Vanilla_KOTOR_Script_Source`](https://github.com/th3w1zard1/Vanilla_KOTOR_Script_Source) - Original KotOR script sources including nwscript.nss
- [`vendor/Vanilla_KOTOR_Script_Source/K1/Data/scripts.bif/`](https://github.com/th3w1zard1/Vanilla_KOTOR_Script_Source/tree/master/K1/Data/scripts.bif) - KotOR 1 script sources from BIF
- [`vendor/Vanilla_KOTOR_Script_Source/TSL/Vanilla/Data/Scripts/`](https://github.com/th3w1zard1/Vanilla_KOTOR_Script_Source/tree/master/TSL/Vanilla/Data/Scripts) - KotOR 2 script sources
- [`vendor/KotOR-Scripting-Tool/NWN Script/k1/nwscript.nss`](https://github.com/th3w1zard1/KotOR-Scripting-Tool/blob/master/NWN%20Script/k1/nwscript.nss) - KotOR 1 nwscript.nss
- [`vendor/KotOR-Scripting-Tool/NWN Script/k2/nwscript.nss`](https://github.com/th3w1zard1/KotOR-Scripting-Tool/blob/master/NWN%20Script/k2/nwscript.nss) - KotOR 2 nwscript.nss
- [`vendor/NorthernLights/Scripts/k1_nwscript.nss`](https://github.com/th3w1zard1/NorthernLights/blob/master/Scripts/k1_nwscript.nss) - KotOR 1 nwscript.nss (NorthernLights)
- [`vendor/NorthernLights/Scripts/k2_nwscript.nss`](https://github.com/th3w1zard1/NorthernLights/blob/master/Scripts/k2_nwscript.nss) - KotOR 2 nwscript.nss (NorthernLights)

**PyKotor Implementation:**

- [`Libraries/PyKotor/src/pykotor/common/script.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/common/script.py) - Data structures (ScriptFunction, ScriptConstant, DataType)
- [`Libraries/PyKotor/src/pykotor/common/scriptdefs.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/common/scriptdefs.py) - Function and constant definitions (772 K1 functions, 1489 K1 constants)
- [`Libraries/PyKotor/src/pykotor/common/scriptlib.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/common/scriptlib.py) - Library file definitions (k_inc_generic, k_inc_utility, etc.)
- [`Libraries/PyKotor/src/pykotor/resource/formats/ncs/ncs_auto.py:126-205`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/ncs/ncs_auto.py#L126-L205) - Compilation integration

**Other Implementations:**

- [`vendor/Kotor.NET/Kotor.NET/Formats/KotorNCS/NCS.cs`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorNCS/NCS.cs) - C# NCS format with actions data support
- [`vendor/KotORModSync/KOTORModSync.Core/Data/NWScriptHeader.cs`](https://github.com/th3w1zard1/KotORModSync/blob/master/KOTORModSync.Core/Data/NWScriptHeader.cs) - C# NWScript header parser
- [`vendor/KotORModSync/KOTORModSync.Core/Data/NWScriptFileReader.cs`](https://github.com/th3w1zard1/KotORModSync/blob/master/KOTORModSync.Core/Data/NWScriptFileReader.cs) - C# NWScript file reader

**NWScript VM and Execution:**

- [`vendor/reone/src/libs/script/routine/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/routine) - Routine implementations for engine functions
- [`vendor/reone/src/libs/script/format/ncsreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/script/format/ncsreader.cpp) - NCS bytecode reader
- [`vendor/reone/src/libs/script/format/ncswriter.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/script/format/ncswriter.cpp) - NCS bytecode writer
- [`vendor/xoreos/src/aurora/nwscript/`](https://github.com/th3w1zard1/xoreos/tree/master/src/aurora/nwscript) - NWScript VM implementation
- [`vendor/xoreos/src/aurora/nwscript/ncsfile.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/ncsfile.cpp) - NCS file parsing and execution
- [`vendor/xoreos/src/aurora/nwscript/object.h`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/object.h) - NWScript object type definitions
- [`vendor/xoreos/src/engines/kotorbase/object.h`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/object.h) - KotOR object implementation
- [`vendor/NorthernLights/Assets/Scripts/ncs/control.cs`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/ncs/control.cs) - Unity C# NCS VM control
- [`vendor/NorthernLights/Assets/Scripts/ncs/NCSReader.cs`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/ncs/NCSReader.cs) - Unity C# NCS reader
- [`vendor/KotOR.js/src/odyssey/controllers/NWScriptController.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/controllers/NWScriptController.ts) - TypeScript NWScript VM controller
- [`vendor/KotOR.js/src/nwscript/NWScriptInstance.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptInstance.ts) - TypeScript NWScript instance
- [`vendor/KotOR.js/src/nwscript/NWScriptStack.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptStack.ts) - TypeScript stack implementation
- [`vendor/KotOR.js/src/nwscript/NWScriptSubroutine.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptSubroutine.ts) - TypeScript subroutine handling

**Documentation and Specifications:**

- [`vendor/xoreos-docs/`](https://github.com/th3w1zard1/xoreos-docs) - xoreos documentation including format specifications
- [`vendor/xoreos-docs/specs/torlack/ncs.html`](https://github.com/th3w1zard1/xoreos-docs/blob/master/specs/torlack/ncs.html) - NCS format specification (if available)

**NWScript Language Support:**

- [`vendor/HoloLSP/server/src/kotor-definitions.ts`](https://github.com/th3w1zard1/HoloLSP/blob/master/server/src/kotor-definitions.ts) - KotOR function and constant definitions for language server
- [`vendor/HoloLSP/server/src/nwscript-runtime.ts`](https://github.com/th3w1zard1/HoloLSP/blob/master/server/src/nwscript-runtime.ts) - NWScript runtime definitions
- [`vendor/HoloLSP/server/src/server.ts`](https://github.com/th3w1zard1/HoloLSP/blob/master/server/src/server.ts) - Language server implementation with NWScript support

**NWScript Parsing and Compilation:**

- [`vendor/reone/src/libs/script/parser/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/parser) - NSS parser implementation
- [`vendor/reone/src/libs/script/compiler/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/compiler) - NSS to NCS compiler
- [`vendor/xoreos-tools/src/nwscript/compiler.cpp`](https://github.com/th3w1zard1/xoreos-tools/blob/master/src/nwscript/compiler.cpp) - NSS compiler implementation
- [`vendor/xoreos-tools/src/nwscript/decompiler.cpp`](https://github.com/th3w1zard1/xoreos-tools/blob/master/src/nwscript/decompiler.cpp) - NCS decompiler implementation

**NWScript Execution:**

- [`vendor/reone/src/libs/script/execution/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/execution) - NWScript VM execution engine
- [`vendor/reone/src/libs/script/vm/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/vm) - Virtual machine implementation
- [`vendor/xoreos/src/aurora/nwscript/execution.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/execution.cpp) - NWScript execution engine
- [`vendor/xoreos/src/aurora/nwscript/variable.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/variable.cpp) - Variable handling
- [`vendor/xoreos/src/aurora/nwscript/function.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/function.cpp) - Function call handling
- [`vendor/NorthernLights/Assets/Scripts/ncs/control.cs`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/ncs/control.cs) - Unity C# NCS VM control and execution
- [`vendor/KotOR.js/src/nwscript/NWScriptController.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptController.ts) - TypeScript NWScript controller and execution

**Routine Implementations:**

- [`vendor/reone/src/libs/script/routine/main/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/routine/main) - Main routine implementations
- [`vendor/reone/src/libs/script/routine/action/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/routine/action) - Action routine implementations
- [`vendor/reone/src/libs/script/routine/effect/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/routine/effect) - Effect routine implementations
- [`vendor/xoreos/src/aurora/nwscript/routines.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/routines.cpp) - Routine implementations
- [`vendor/xoreos/src/engines/kotorbase/script/routines.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/script/routines.cpp) - KotOR-specific routine implementations

**NWScript Type System:**

- [`vendor/xoreos/src/aurora/nwscript/types.h`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/types.h) - NWScript type definitions
- [`vendor/xoreos/src/aurora/nwscript/types.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/types.cpp) - Type system implementation
- [`vendor/KotOR.js/src/enums/nwscript/NWScriptDataType.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/enums/nwscript/NWScriptDataType.ts) - TypeScript data type enumerations
- [`vendor/KotOR.js/src/enums/nwscript/NWScriptTypes.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/enums/nwscript/NWScriptTypes.ts) - TypeScript type definitions

**NWScript Events:**

- [`vendor/KotOR.js/src/nwscript/events/NWScriptEvent.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/events/NWScriptEvent.ts) - Event handling
- [`vendor/KotOR.js/src/nwscript/events/NWScriptEventFactory.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/events/NWScriptEventFactory.ts) - Event factory
- [`vendor/KotOR.js/src/enums/nwscript/NWScriptEventType.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/enums/nwscript/NWScriptEventType.ts) - Event type enumerations

**NWScript Bytecode:**

- [`vendor/KotOR.js/src/nwscript/NWScriptOPCodes.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptOPCodes.ts) - Opcode definitions
- [`vendor/KotOR.js/src/nwscript/NWScriptInstruction.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptInstruction.ts) - Instruction handling
- [`vendor/KotOR.js/src/nwscript/NWScriptInstructionInfo.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptInstructionInfo.ts) - Instruction information
- [`vendor/KotOR.js/src/enums/nwscript/NWScriptByteCode.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/enums/nwscript/NWScriptByteCode.ts) - Bytecode enumerations

**NWScript Stack:**

- [`vendor/KotOR.js/src/nwscript/NWScriptStack.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptStack.ts) - Stack implementation
- [`vendor/KotOR.js/src/nwscript/NWScriptStackVariable.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptStackVariable.ts) - Stack variable handling

**NWScript Interface Definitions:**

- [`vendor/KotOR.js/src/interface/nwscript/INWScriptStoreState.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/interface/nwscript/INWScriptStoreState.ts) - Store state interface
- [`vendor/KotOR.js/src/interface/nwscript/INWScriptDefAction.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/interface/nwscript/INWScriptDefAction.ts) - Action definition interface

**NWScript AST and Parsing:**

- [`vendor/KotOR.js/src/nwscript/AST/nwscript.jison.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/AST/nwscript.jison.ts) - Jison parser grammar
- [`vendor/HoloLSP/server/src/nwscript-ast.ts`](https://github.com/th3w1zard1/HoloLSP/blob/master/server/src/nwscript-ast.ts) - Abstract syntax tree definitions

**Game-Specific NWScript Extensions:**

- [`vendor/xoreos/src/engines/kotorbase/script/routines.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/script/routines.cpp) - KotOR-specific routine implementations
- [`vendor/reone/src/libs/script/routine/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/routine) - Routine implementations for K1 and K2
- [`vendor/xoreos/src/engines/nwn/script/functions_action.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/nwn/script/functions_action.cpp) - NWN action function implementations
- [`vendor/NorthernLights/Assets/Scripts/ncs/constants.cs`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/ncs/constants.cs) - NWScript constant definitions
- [`vendor/reone/src/libs/script/routine.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/script/routine.cpp) - Routine base class implementation
- [`vendor/reone/src/libs/game/script/routines.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/script/routines.cpp) - Game-specific routine implementations
- [`vendor/reone/include/reone/script/routines.h`](https://github.com/th3w1zard1/reone/blob/master/include/reone/script/routines.h) - Routine header definitions
- [`vendor/reone/include/reone/script/routine.h`](https://github.com/th3w1zard1/reone/blob/master/include/reone/script/routine.h) - Routine base class header
- [`vendor/reone/include/reone/game/script/routines.h`](https://github.com/th3w1zard1/reone/blob/master/include/reone/game/script/routines.h) - Game routine header
- [`vendor/xoreos-tools/src/nwscript/subroutine.cpp`](https://github.com/th3w1zard1/xoreos-tools/blob/master/src/nwscript/subroutine.cpp) - Subroutine handling
- [`vendor/xoreos-tools/src/nwscript/subroutine.h`](https://github.com/th3w1zard1/xoreos-tools/blob/master/src/nwscript/subroutine.h) - Subroutine header
- [`vendor/xoreos/src/engines/kotorbase/types.h`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/types.h) - KotOR type definitions including base item types
- [`vendor/KotOR.js/src/module/Module.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/Module.ts) - Module loading and management
- [`vendor/KotOR.js/src/module/ModuleArea.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleArea.ts) - Area management and transitions
- [`vendor/xoreos/src/engines/nwn/module.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/nwn/module.cpp) - NWN module implementation
- [`vendor/xoreos/src/engines/nwn2/module.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/nwn2/module.cpp) - NWN2 module implementation
- [`vendor/xoreos/src/engines/nwn2/module.h`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/nwn2/module.h) - NWN2 module header
- [`vendor/xoreos/src/engines/dragonage2/script/functions_module.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/dragonage2/script/functions_module.cpp) - Dragon Age 2 module functions
- [`vendor/xoreos/src/engines/nwn/script/functions_effect.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/nwn/script/functions_effect.cpp) - NWN effect function implementations
- [`vendor/xoreos/src/engines/nwn/script/functions_object.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/nwn/script/functions_object.cpp) - NWN object function implementations
- [`vendor/xoreos/src/engines/nwn2/script/functions.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/nwn2/script/functions.cpp) - NWN2 function implementations
- [`vendor/reone/src/libs/script/routine/action/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/routine/action) - Action routine implementations
- [`vendor/reone/src/libs/script/routine/effect/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/routine/effect) - Effect routine implementations
- [`vendor/reone/src/libs/script/routine/object/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/routine/object) - Object routine implementations
- [`vendor/reone/src/libs/script/routine/party/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/routine/party) - Party routine implementations
- [`vendor/reone/src/libs/script/routine/combat/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/routine/combat) - Combat routine implementations
- [`vendor/NorthernLights/Assets/Scripts/ncs/nwscript_actions.cs`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/ncs/nwscript_actions.cs) - Complete actions table mapping routine numbers to function names
- [`vendor/NorthernLights/Assets/Scripts/Systems/AuroraActions/AuroraAction.cs`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/Systems/AuroraActions/AuroraAction.cs) - Action system implementation

---

### Other Constants

- `TRUE` (1) **(K1 & TSL)**: True
- `FALSE` (0) **(K1 & TSL)**: False
- `PI` (3.141592653589793) **(K1 & TSL)**: Pi
- `ATTITUDE_NEUTRAL` (0) **(K1 & TSL)**: Attitude Neutral
- `ATTITUDE_AGGRESSIVE` (1) **(K1 & TSL)**: Attitude Aggressive
- `ATTITUDE_DEFENSIVE` (2) **(K1 & TSL)**: Attitude Defensive
- `ATTITUDE_SPECIAL` (3) **(K1 & TSL)**: Attitude Special
- `RADIUS_SIZE_SMALL` (1.67) **(K1 & TSL)**: Radius Size Small
- `RADIUS_SIZE_MEDIUM` (3.33) **(K1 & TSL)**: Radius Size Medium
- `RADIUS_SIZE_LARGE` (5.0) **(K1 & TSL)**: Radius Size Large
- `RADIUS_SIZE_HUGE` (6.67) **(K1 & TSL)**: Radius Size Huge
- `RADIUS_SIZE_GARGANTUAN` (8.33) **(K1 & TSL)**: Radius Size Gargantuan
- `RADIUS_SIZE_COLOSSAL` (10.0) **(K1 & TSL)**: Radius Size Colossal
- `ATTACK_RESULT_INVALID` (0) **(K1 & TSL)**: Attack Result Invalid
- `ATTACK_RESULT_HIT_SUCCESSFUL` (1) **(K1 & TSL)**: Attack Result Hit Successful
- `ATTACK_RESULT_CRITICAL_HIT` (2) **(K1 & TSL)**: Attack Result Critical Hit
- `ATTACK_RESULT_AUTOMATIC_HIT` (3) **(K1 & TSL)**: Attack Result Automatic Hit
- `ATTACK_RESULT_MISS` (4) **(K1 & TSL)**: Attack Result Miss
- `ATTACK_RESULT_ATTACK_RESISTED` (5) **(K1 & TSL)**: Attack Result Attack Resisted
- `ATTACK_RESULT_ATTACK_FAILED` (6) **(K1 & TSL)**: Attack Result Attack Failed
- `ATTACK_RESULT_PARRIED` (8) **(K1 & TSL)**: Attack Result Parried
- `ATTACK_RESULT_DEFLECTED` (9) **(K1 & TSL)**: Attack Result Deflected
- `AOE_PER_FOGACID` (0) **(K1 & TSL)**: Aoe Per Fogacid
- `AOE_PER_FOGFIRE` (1) **(K1 & TSL)**: Aoe Per Fogfire
- `AOE_PER_FOGSTINK` (2) **(K1 & TSL)**: Aoe Per Fogstink
- `AOE_PER_FOGKILL` (3) **(K1 & TSL)**: Aoe Per Fogkill
- `AOE_PER_FOGMIND` (4) **(K1 & TSL)**: Aoe Per Fogmind
- `AOE_PER_WALLFIRE` (5) **(K1 & TSL)**: Aoe Per Wallfire
- `AOE_PER_WALLWIND` (6) **(K1 & TSL)**: Aoe Per Wallwind
- `AOE_PER_WALLBLADE` (7) **(K1 & TSL)**: Aoe Per Wallblade
- `AOE_PER_WEB` (8) **(K1 & TSL)**: Aoe Per Web
- `AOE_PER_ENTANGLE` (9) **(K1 & TSL)**: Aoe Per Entangle
- `AOE_PER_DARKNESS` (11) **(K1 & TSL)**: Aoe Per Darkness
- `AOE_MOB_CIRCEVIL` (12) **(K1 & TSL)**: Aoe Mob Circevil
- `AOE_MOB_CIRCGOOD` (13) **(K1 & TSL)**: Aoe Mob Circgood
- `AOE_MOB_CIRCLAW` (14) **(K1 & TSL)**: Aoe Mob Circlaw
- `AOE_MOB_CIRCCHAOS` (15) **(K1 & TSL)**: Aoe Mob Circchaos
- `AOE_MOB_FEAR` (16) **(K1 & TSL)**: Aoe Mob Fear
- `AOE_MOB_BLINDING` (17) **(K1 & TSL)**: Aoe Mob Blinding
- `AOE_MOB_UNEARTHLY` (18) **(K1 & TSL)**: Aoe Mob Unearthly
- `AOE_MOB_MENACE` (19) **(K1 & TSL)**: Aoe Mob Menace
- `AOE_MOB_UNNATURAL` (20) **(K1 & TSL)**: Aoe Mob Unnatural
- `AOE_MOB_STUN` (21) **(K1 & TSL)**: Aoe Mob Stun
- `AOE_MOB_PROTECTION` (22) **(K1 & TSL)**: Aoe Mob Protection
- `AOE_MOB_FIRE` (23) **(K1 & TSL)**: Aoe Mob Fire
- `AOE_MOB_FROST` (24) **(K1 & TSL)**: Aoe Mob Frost
- `AOE_MOB_ELECTRICAL` (25) **(K1 & TSL)**: Aoe Mob Electrical
- `AOE_PER_FOGGHOUL` (26) **(K1 & TSL)**: Aoe Per Fogghoul
- `AOE_MOB_TYRANT_FOG` (27) **(K1 & TSL)**: Aoe Mob Tyrant Fog
- `AOE_PER_STORM` (28) **(K1 & TSL)**: Aoe Per Storm
- `AOE_PER_INVIS_SPHERE` (29) **(K1 & TSL)**: Aoe Per Invis Sphere
- `AOE_MOB_SILENCE` (30) **(K1 & TSL)**: Aoe Mob Silence
- `AOE_PER_DELAY_BLAST_FIREBALL` (31) **(K1 & TSL)**: Aoe Per Delay Blast Fireball
- `AOE_PER_GREASE` (32) **(K1 & TSL)**: Aoe Per Grease
- `AOE_PER_CREEPING_DOOM` (33) **(K1 & TSL)**: Aoe Per Creeping Doom
- `AOE_PER_EVARDS_BLACK_TENTACLES` (34) **(K1 & TSL)**: Aoe Per Evards Black Tentacles
- `AOE_MOB_INVISIBILITY_PURGE` (35) **(K1 & TSL)**: Aoe Mob Invisibility Purge
- `AOE_MOB_DRAGON_FEAR` (36) **(K1 & TSL)**: Aoe Mob Dragon Fear
- `FORCE_POWER_ALL_FORCE_POWERS` (-1) **(K1 & TSL)**: Force Power All Force Powers
- `FORCE_POWER_MASTER_ALTER` (0) **(K1 & TSL)**: Force Power Master Alter
- `FORCE_POWER_MASTER_CONTROL` (1) **(K1 & TSL)**: Force Power Master Control
- `FORCE_POWER_MASTER_SENSE` (2) **(K1 & TSL)**: Force Power Master Sense
- `FORCE_POWER_FORCE_JUMP_ADVANCED` (3) **(K1 & TSL)**: Force Power Force Jump Advanced
- `FORCE_POWER_LIGHT_SABER_THROW_ADVANCED` (4) **(K1 & TSL)**: Force Power Light Saber Throw Advanced
- `FORCE_POWER_REGNERATION_ADVANCED` (5) **(K1 & TSL)**: Force Power Regneration Advanced
- `FORCE_POWER_AFFECT_MIND` (6) **(K1 & TSL)**: Force Power Affect Mind
- `FORCE_POWER_AFFLICTION` (7) **(K1 & TSL)**: Force Power Affliction
- `FORCE_POWER_SPEED_BURST` (8) **(K1 & TSL)**: Force Power Speed Burst
- `FORCE_POWER_CHOKE` (9) **(K1 & TSL)**: Force Power Choke
- `FORCE_POWER_CURE` (10) **(K1 & TSL)**: Force Power Cure
- `FORCE_POWER_DEATH_FIELD` (11) **(K1 & TSL)**: Force Power Death Field
- `FORCE_POWER_DROID_DISABLE` (12) **(K1 & TSL)**: Force Power Droid Disable
- `FORCE_POWER_DROID_DESTROY` (13) **(K1 & TSL)**: Force Power Droid Destroy
- `FORCE_POWER_DOMINATE` (14) **(K1 & TSL)**: Force Power Dominate
- `FORCE_POWER_DRAIN_LIFE` (15) **(K1 & TSL)**: Force Power Drain Life
- `FORCE_POWER_FEAR` (16) **(K1 & TSL)**: Force Power Fear
- `FORCE_POWER_FORCE_ARMOR` (17) **(K1 & TSL)**: Force Power Force Armor
- `FORCE_POWER_FORCE_AURA` (18) **(K1 & TSL)**: Force Power Force Aura
- `FORCE_POWER_FORCE_BREACH` (19) **(K1 & TSL)**: Force Power Force Breach
- `FORCE_POWER_FORCE_IMMUNITY` (20) **(K1 & TSL)**: Force Power Force Immunity
- `FORCE_POWER_FORCE_JUMP` (21) **(K1 & TSL)**: Force Power Force Jump
- `FORCE_POWER_FORCE_MIND` (22) **(K1 & TSL)**: Force Power Force Mind
- `FORCE_POWER_FORCE_PUSH` (23) **(K1 & TSL)**: Force Power Force Push
- `FORCE_POWER_FORCE_SHIELD` (24) **(K1 & TSL)**: Force Power Force Shield
- `FORCE_POWER_FORCE_STORM` (25) **(K1 & TSL)**: Force Power Force Storm
- `FORCE_POWER_FORCE_WAVE` (26) **(K1 & TSL)**: Force Power Force Wave
- `FORCE_POWER_FORCE_WHIRLWIND` (27) **(K1 & TSL)**: Force Power Force Whirlwind
- `FORCE_POWER_HEAL` (28) **(K1 & TSL)**: Force Power Heal
- `FORCE_POWER_HOLD` (29) **(K1 & TSL)**: Force Power Hold
- `FORCE_POWER_HORROR` (30) **(K1 & TSL)**: Force Power Horror
- `FORCE_POWER_INSANITY` (31) **(K1 & TSL)**: Force Power Insanity
- `FORCE_POWER_KILL` (32) **(K1 & TSL)**: Force Power Kill
- `FORCE_POWER_KNIGHT_MIND` (33) **(K1 & TSL)**: Force Power Knight Mind
- `FORCE_POWER_KNIGHT_SPEED` (34) **(K1 & TSL)**: Force Power Knight Speed
- `FORCE_POWER_LIGHTNING` (35) **(K1 & TSL)**: Force Power Lightning
- `FORCE_POWER_MIND_MASTERY` (36) **(K1 & TSL)**: Force Power Mind Mastery
- `FORCE_POWER_SPEED_MASTERY` (37) **(K1 & TSL)**: Force Power Speed Mastery
- `FORCE_POWER_PLAGUE` (38) **(K1 & TSL)**: Force Power Plague
- `FORCE_POWER_REGENERATION` (39) **(K1 & TSL)**: Force Power Regeneration
- `FORCE_POWER_RESIST_COLD_HEAT_ENERGY` (40) **(K1 & TSL)**: Force Power Resist Cold Heat Energy
- `FORCE_POWER_RESIST_FORCE` (41) **(K1 & TSL)**: Force Power Resist Force
- `FORCE_POWER_SHOCK` (43) **(K1 & TSL)**: Force Power Shock
- `FORCE_POWER_SLEEP` (44) **(K1 & TSL)**: Force Power Sleep
- `FORCE_POWER_SLOW` (45) **(K1 & TSL)**: Force Power Slow
- `FORCE_POWER_STUN` (46) **(K1 & TSL)**: Force Power Stun
- `FORCE_POWER_DROID_STUN` (47) **(K1 & TSL)**: Force Power Droid Stun
- `FORCE_POWER_SUPRESS_FORCE` (48) **(K1 & TSL)**: Force Power Supress Force
- `FORCE_POWER_LIGHT_SABER_THROW` (49) **(K1 & TSL)**: Force Power Light Saber Throw
- `FORCE_POWER_WOUND` (50) **(K1 & TSL)**: Force Power Wound
- `PERSISTENT_ZONE_ACTIVE` (0) **(K1 & TSL)**: Persistent Zone Active
- `PERSISTENT_ZONE_FOLLOW` (1) **(K1 & TSL)**: Persistent Zone Follow
- `INVALID_STANDARD_FACTION` (-1) **(K1 & TSL)**: Invalid Standard Faction
- `STANDARD_FACTION_HOSTILE_1` (1) **(K1 & TSL)**: Standard Faction Hostile 1
- `STANDARD_FACTION_FRIENDLY_1` (2) **(K1 & TSL)**: Standard Faction Friendly 1
- `STANDARD_FACTION_HOSTILE_2` (3) **(K1 & TSL)**: Standard Faction Hostile 2
- `STANDARD_FACTION_FRIENDLY_2` (4) **(K1 & TSL)**: Standard Faction Friendly 2
- `STANDARD_FACTION_NEUTRAL` (5) **(K1 & TSL)**: Standard Faction Neutral
- `STANDARD_FACTION_INSANE` (6) **(K1 & TSL)**: Standard Faction Insane
- `STANDARD_FACTION_PTAT_TUSKAN` (7) **(K1 & TSL)**: Standard Faction Ptat Tuskan
- `STANDARD_FACTION_GLB_XOR` (8) **(K1 & TSL)**: Standard Faction Glb Xor
- `STANDARD_FACTION_SURRENDER_1` (9) **(K1 & TSL)**: Standard Faction Surrender 1
- `STANDARD_FACTION_SURRENDER_2` (10) **(K1 & TSL)**: Standard Faction Surrender 2
- `STANDARD_FACTION_PREDATOR` (11) **(K1 & TSL)**: Standard Faction Predator
- `STANDARD_FACTION_PREY` (12) **(K1 & TSL)**: Standard Faction Prey
- `STANDARD_FACTION_TRAP` (13) **(K1 & TSL)**: Standard Faction Trap
- `STANDARD_FACTION_ENDAR_SPIRE` (14) **(K1 & TSL)**: Standard Faction Endar Spire
- `STANDARD_FACTION_RANCOR` (15) **(K1 & TSL)**: Standard Faction Rancor
- `STANDARD_FACTION_GIZKA_1` (16) **(K1 & TSL)**: Standard Faction Gizka 1
- `STANDARD_FACTION_GIZKA_2` (17) **(K1 & TSL)**: Standard Faction Gizka 2
- `SUBSKILL_FLAGTRAP` (100) **(K1 & TSL)**: Subskill Flagtrap
- `SUBSKILL_RECOVERTRAP` (101) **(K1 & TSL)**: Subskill Recovertrap
- `SUBSKILL_EXAMINETRAP` (102) **(K1 & TSL)**: Subskill Examinetrap
- `TALENT_TYPE_FORCE` (0) **(K1 & TSL)**: Talent Type Force
- `TALENT_TYPE_SPELL` (0) **(K1 & TSL)**: Talent Type Spell
- `TALENT_TYPE_FEAT` (1) **(K1 & TSL)**: Talent Type Feat
- `TALENT_TYPE_SKILL` (2) **(K1 & TSL)**: Talent Type Skill
- `TALENT_EXCLUDE_ALL_OF_TYPE` (-1) **(K1 & TSL)**: Talent Exclude All Of Type
- `GUI_PANEL_PLAYER_DEATH` (0) **(K1 & TSL)**: Gui Panel Player Death
- `POLYMORPH_TYPE_WEREWOLF` (0) **(K1 & TSL)**: Polymorph Type Werewolf
- `POLYMORPH_TYPE_WERERAT` (1) **(K1 & TSL)**: Polymorph Type Wererat
- `POLYMORPH_TYPE_WERECAT` (2) **(K1 & TSL)**: Polymorph Type Werecat
- `POLYMORPH_TYPE_GIANT_SPIDER` (3) **(K1 & TSL)**: Polymorph Type Giant Spider
- `POLYMORPH_TYPE_TROLL` (4) **(K1 & TSL)**: Polymorph Type Troll
- `POLYMORPH_TYPE_UMBER_HULK` (5) **(K1 & TSL)**: Polymorph Type Umber Hulk
- `POLYMORPH_TYPE_PIXIE` (6) **(K1 & TSL)**: Polymorph Type Pixie
- `POLYMORPH_TYPE_ZOMBIE` (7) **(K1 & TSL)**: Polymorph Type Zombie
- `POLYMORPH_TYPE_RED_DRAGON` (8) **(K1 & TSL)**: Polymorph Type Red Dragon
- `POLYMORPH_TYPE_FIRE_GIANT` (9) **(K1 & TSL)**: Polymorph Type Fire Giant
- `POLYMORPH_TYPE_BALOR` (10) **(K1 & TSL)**: Polymorph Type Balor
- `POLYMORPH_TYPE_DEATH_SLAAD` (11) **(K1 & TSL)**: Polymorph Type Death Slaad
- `POLYMORPH_TYPE_IRON_GOLEM` (12) **(K1 & TSL)**: Polymorph Type Iron Golem
- `POLYMORPH_TYPE_HUGE_FIRE_ELEMENTAL` (13) **(K1 & TSL)**: Polymorph Type Huge Fire Elemental
- `POLYMORPH_TYPE_HUGE_WATER_ELEMENTAL` (14) **(K1 & TSL)**: Polymorph Type Huge Water Elemental
- `POLYMORPH_TYPE_HUGE_EARTH_ELEMENTAL` (15) **(K1 & TSL)**: Polymorph Type Huge Earth Elemental
- `POLYMORPH_TYPE_HUGE_AIR_ELEMENTAL` (16) **(K1 & TSL)**: Polymorph Type Huge Air Elemental
- `POLYMORPH_TYPE_ELDER_FIRE_ELEMENTAL` (17) **(K1 & TSL)**: Polymorph Type Elder Fire Elemental
- `POLYMORPH_TYPE_ELDER_WATER_ELEMENTAL` (18) **(K1 & TSL)**: Polymorph Type Elder Water Elemental
- `POLYMORPH_TYPE_ELDER_EARTH_ELEMENTAL` (19) **(K1 & TSL)**: Polymorph Type Elder Earth Elemental
- `POLYMORPH_TYPE_ELDER_AIR_ELEMENTAL` (20) **(K1 & TSL)**: Polymorph Type Elder Air Elemental
- `POLYMORPH_TYPE_BROWN_BEAR` (21) **(K1 & TSL)**: Polymorph Type Brown Bear
- `POLYMORPH_TYPE_PANTHER` (22) **(K1 & TSL)**: Polymorph Type Panther
- `POLYMORPH_TYPE_WOLF` (23) **(K1 & TSL)**: Polymorph Type Wolf
- `POLYMORPH_TYPE_BOAR` (24) **(K1 & TSL)**: Polymorph Type Boar
- `POLYMORPH_TYPE_BADGER` (25) **(K1 & TSL)**: Polymorph Type Badger
- `POLYMORPH_TYPE_PENGUIN` (26) **(K1 & TSL)**: Polymorph Type Penguin
- `POLYMORPH_TYPE_COW` (27) **(K1 & TSL)**: Polymorph Type Cow
- `POLYMORPH_TYPE_DOOM_KNIGHT` (28) **(K1 & TSL)**: Polymorph Type Doom Knight
- `POLYMORPH_TYPE_YUANTI` (29) **(K1 & TSL)**: Polymorph Type Yuanti
- `POLYMORPH_TYPE_IMP` (30) **(K1 & TSL)**: Polymorph Type Imp
- `POLYMORPH_TYPE_QUASIT` (31) **(K1 & TSL)**: Polymorph Type Quasit
- `POLYMORPH_TYPE_SUCCUBUS` (32) **(K1 & TSL)**: Polymorph Type Succubus
- `POLYMORPH_TYPE_DIRE_BROWN_BEAR` (33) **(K1 & TSL)**: Polymorph Type Dire Brown Bear
- `POLYMORPH_TYPE_DIRE_PANTHER` (34) **(K1 & TSL)**: Polymorph Type Dire Panther
- `POLYMORPH_TYPE_DIRE_WOLF` (35) **(K1 & TSL)**: Polymorph Type Dire Wolf
- `POLYMORPH_TYPE_DIRE_BOAR` (36) **(K1 & TSL)**: Polymorph Type Dire Boar
- `POLYMORPH_TYPE_DIRE_BADGER` (37) **(K1 & TSL)**: Polymorph Type Dire Badger
- `CREATURE_SIZE_INVALID` (0) **(K1 & TSL)**: Creature Size Invalid
- `CREATURE_SIZE_TINY` (1) **(K1 & TSL)**: Creature Size Tiny
- `CREATURE_SIZE_SMALL` (2) **(K1 & TSL)**: Creature Size Small
- `CREATURE_SIZE_MEDIUM` (3) **(K1 & TSL)**: Creature Size Medium
- `CREATURE_SIZE_LARGE` (4) **(K1 & TSL)**: Creature Size Large
- `CREATURE_SIZE_HUGE` (5) **(K1 & TSL)**: Creature Size Huge
- `CAMERA_MODE_CHASE_CAMERA` (0) **(K1 & TSL)**: Camera Mode Chase Camera
- `CAMERA_MODE_TOP_DOWN` (1) **(K1 & TSL)**: Camera Mode Top Down
- `CAMERA_MODE_STIFF_CHASE_CAMERA` (2) **(K1 & TSL)**: Camera Mode Stiff Chase Camera
- `GAME_DIFFICULTY_VERY_EASY` (0) **(K1 & TSL)**: Game Difficulty Very Easy
- `GAME_DIFFICULTY_EASY` (1) **(K1 & TSL)**: Game Difficulty Easy
- `GAME_DIFFICULTY_NORMAL` (2) **(K1 & TSL)**: Game Difficulty Normal
- `GAME_DIFFICULTY_CORE_RULES` (3) **(K1 & TSL)**: Game Difficulty Core Rules
- `GAME_DIFFICULTY_DIFFICULT` (4) **(K1 & TSL)**: Game Difficulty Difficult
- `ACTION_MOVETOPOINT` (0) **(K1 & TSL)**: Action Movetopoint
- `ACTION_PICKUPITEM` (1) **(K1 & TSL)**: Action Pickupitem
- `ACTION_DROPITEM` (2) **(K1 & TSL)**: Action Dropitem
- `ACTION_ATTACKOBJECT` (3) **(K1 & TSL)**: Action Attackobject
- `ACTION_CASTSPELL` (4) **(K1 & TSL)**: Action Castspell
- `ACTION_OPENDOOR` (5) **(K1 & TSL)**: Action Opendoor
- `ACTION_CLOSEDOOR` (6) **(K1 & TSL)**: Action Closedoor
- `ACTION_DIALOGOBJECT` (7) **(K1 & TSL)**: Action Dialogobject
- `ACTION_DISABLETRAP` (8) **(K1 & TSL)**: Action Disabletrap
- `ACTION_RECOVERTRAP` (9) **(K1 & TSL)**: Action Recovertrap
- `ACTION_FLAGTRAP` (10) **(K1 & TSL)**: Action Flagtrap
- `ACTION_EXAMINETRAP` (11) **(K1 & TSL)**: Action Examinetrap
- `ACTION_SETTRAP` (12) **(K1 & TSL)**: Action Settrap
- `ACTION_OPENLOCK` (13) **(K1 & TSL)**: Action Openlock
- `ACTION_LOCK` (14) **(K1 & TSL)**: Action Lock
- `ACTION_USEOBJECT` (15) **(K1 & TSL)**: Action Useobject
- `ACTION_ANIMALEMPATHY` (16) **(K1 & TSL)**: Action Animalempathy
- `ACTION_REST` (17) **(K1 & TSL)**: Action Rest
- `ACTION_TAUNT` (18) **(K1 & TSL)**: Action Taunt
- `ACTION_ITEMCASTSPELL` (19) **(K1 & TSL)**: Action Itemcastspell
- `ACTION_COUNTERSPELL` (31) **(K1 & TSL)**: Action Counterspell
- `ACTION_HEAL` (33) **(K1 & TSL)**: Action Heal
- `ACTION_PICKPOCKET` (34) **(K1 & TSL)**: Action Pickpocket
- `ACTION_FOLLOW` (35) **(K1 & TSL)**: Action Follow
- `ACTION_WAIT` (36) **(K1 & TSL)**: Action Wait
- `ACTION_SIT` (37) **(K1 & TSL)**: Action Sit
- `ACTION_FOLLOWLEADER` (38) **(K1 & TSL)**: Action Followleader
- `ACTION_INVALID` (65535) **(K1 & TSL)**: Action Invalid
- `ACTION_QUEUEEMPTY` (65534) **(K1 & TSL)**: Action Queueempty
- `SWMINIGAME_TRACKFOLLOWER_SOUND_ENGINE` (0) **(K1 & TSL)**: Swminigame Trackfollower Sound Engine
- `SWMINIGAME_TRACKFOLLOWER_SOUND_DEATH` (1) **(K1 & TSL)**: Swminigame Trackfollower Sound Death
- `PLOT_O_DOOM` (0) **(K1 & TSL)**: Plot O Doom
- `PLOT_O_SCARY_STUFF` (1) **(K1 & TSL)**: Plot O Scary Stuff
- `PLOT_O_BIG_MONSTERS` (2) **(K1 & TSL)**: Plot O Big Monsters
- `FORMATION_WEDGE` (0) **(K1 & TSL)**: Formation Wedge
- `FORMATION_LINE` (1) **(K1 & TSL)**: Formation Line
- `SUBSCREEN_ID_NONE` (0) **(K1 & TSL)**: Subscreen Id None
- `SUBSCREEN_ID_EQUIP` (1) **(K1 & TSL)**: Subscreen Id Equip
- `SUBSCREEN_ID_ITEM` (2) **(K1 & TSL)**: Subscreen Id Item
- `SUBSCREEN_ID_CHARACTER_RECORD` (3) **(K1 & TSL)**: Subscreen Id Character Record
- `SUBSCREEN_ID_ABILITY` (4) **(K1 & TSL)**: Subscreen Id Ability
- `SUBSCREEN_ID_MAP` (5) **(K1 & TSL)**: Subscreen Id Map
- `SUBSCREEN_ID_QUEST` (6) **(K1 & TSL)**: Subscreen Id Quest
- `SUBSCREEN_ID_OPTIONS` (7) **(K1 & TSL)**: Subscreen Id Options
- `SUBSCREEN_ID_MESSAGES` (8) **(K1 & TSL)**: Subscreen Id Messages
- `SHIELD_DROID_ENERGY_1` (0) **(K1 & TSL)**: Shield Droid Energy 1
- `SHIELD_DROID_ENERGY_2` (1) **(K1 & TSL)**: Shield Droid Energy 2
- `SHIELD_DROID_ENERGY_3` (2) **(K1 & TSL)**: Shield Droid Energy 3
- `SHIELD_DROID_ENVIRO_1` (3) **(K1 & TSL)**: Shield Droid Enviro 1
- `SHIELD_DROID_ENVIRO_2` (4) **(K1 & TSL)**: Shield Droid Enviro 2
- `SHIELD_DROID_ENVIRO_3` (5) **(K1 & TSL)**: Shield Droid Enviro 3
- `SHIELD_ENERGY` (6) **(K1 & TSL)**: Shield Energy
- `SHIELD_ENERGY_SITH` (7) **(K1 & TSL)**: Shield Energy Sith
- `SHIELD_ENERGY_ARKANIAN` (8) **(K1 & TSL)**: Shield Energy Arkanian
- `SHIELD_ECHANI` (9) **(K1 & TSL)**: Shield Echani
- `SHIELD_MANDALORIAN_MELEE` (10) **(K1 & TSL)**: Shield Mandalorian Melee
- `SHIELD_MANDALORIAN_POWER` (11) **(K1 & TSL)**: Shield Mandalorian Power
- `SHIELD_DUELING_ECHANI` (12) **(K1 & TSL)**: Shield Dueling Echani
- `SHIELD_DUELING_YUSANIS` (13) **(K1 & TSL)**: Shield Dueling Yusanis
- `SHIELD_VERPINE_PROTOTYPE` (14) **(K1 & TSL)**: Shield Verpine Prototype
- `SHIELD_ANTIQUE_DROID` (15) **(K1 & TSL)**: Shield Antique Droid
- `SHIELD_PLOT_TAR_M09AA` (16) **(K1 & TSL)**: Shield Plot Tar M09Aa
- `SHIELD_PLOT_UNK_M44AA` (17) **(K1 & TSL)**: Shield Plot Unk M44Aa
- `VIDEO_EFFECT_NONE` (-1) **(K1 & TSL)**: Video Effect None
- `VIDEO_EFFECT_SECURITY_CAMERA` (0) **(K1 & TSL)**: Video Effect Security Camera
- `VIDEO_EFFECT_FREELOOK_T3M4` (1) **(K1 & TSL)**: Video Effect Freelook T3M4
- `VIDEO_EFFECT_FREELOOK_HK47` (2) **(K1 & TSL)**: Video Effect Freelook Hk47
- `TUTORIAL_WINDOW_START_SWOOP_RACE` (0) **(K1 & TSL)**: Tutorial Window Start Swoop Race
- `TUTORIAL_WINDOW_RETURN_TO_BASE` (1) **(K1 & TSL)**: Tutorial Window Return To Base
- `TUTORIAL_WINDOW_MOVEMENT_KEYS` (2) **(K1)**: Tutorial Window Movement Keys
- `LIVE_CONTENT_PKG1` (1) **(K1 & TSL)**: Live Content Pkg1
- `LIVE_CONTENT_PKG2` (2) **(K1 & TSL)**: Live Content Pkg2
- `LIVE_CONTENT_PKG3` (3) **(K1 & TSL)**: Live Content Pkg3
- `LIVE_CONTENT_PKG4` (4) **(K1 & TSL)**: Live Content Pkg4
- `LIVE_CONTENT_PKG5` (5) **(K1 & TSL)**: Live Content Pkg5
- `LIVE_CONTENT_PKG6` (6) **(K1 & TSL)**: Live Content Pkg6
- `FORM_MASK_FORCE_FOCUS` (1) **(TSL)**: Form Mask Force Focus
- `FORM_MASK_ENDURING_FORCE` (2) **(TSL)**: Form Mask Enduring Force
- `FORM_MASK_FORCE_AMPLIFICATION` (4) **(TSL)**: Form Mask Force Amplification
- `FORM_MASK_FORCE_POTENCY` (8) **(TSL)**: Form Mask Force Potency
- `FORM_MASK_REGENERATION` (16) **(TSL)**: Form Mask Regeneration
- `FORM_MASK_POWER_OF_THE_DARK_SIDE` (32) **(TSL)**: Form Mask Power Of The Dark Side
- `FORCE_POWER_MASTER_ENERGY_RESISTANCE` (133) **(TSL)**: Force Power Master Energy Resistance
- `FORCE_POWER_MASTER_HEAL` (134) **(TSL)**: Force Power Master Heal
- `FORCE_POWER_FORCE_BARRIER` (135) **(TSL)**: Force Power Force Barrier
- `FORCE_POWER_IMPROVED_FORCE_BARRIER` (136) **(TSL)**: Force Power Improved Force Barrier
- `FORCE_POWER_MASTER_FORCE_BARRIER` (137) **(TSL)**: Force Power Master Force Barrier
- `FORCE_POWER_BATTLE_MEDITATION_PC` (138) **(TSL)**: Force Power Battle Meditation Pc
- `FORCE_POWER_IMPROVED_BATTLE_MEDITATION_PC` (139) **(TSL)**: Force Power Improved Battle Meditation Pc
- `FORCE_POWER_MASTER_BATTLE_MEDITATION_PC` (140) **(TSL)**: Force Power Master Battle Meditation Pc
- `FORCE_POWER_BAT_MED_ENEMY` (141) **(TSL)**: Force Power Bat Med Enemy
- `FORCE_POWER_IMP_BAT_MED_ENEMY` (142) **(TSL)**: Force Power Imp Bat Med Enemy
- `FORCE_POWER_MAS_BAT_MED_ENEMY` (143) **(TSL)**: Force Power Mas Bat Med Enemy
- `FORCE_POWER_CRUSH_OPPOSITION_I` (144) **(TSL)**: Force Power Crush Opposition I
- `FORCE_POWER_CRUSH_OPPOSITION_II` (145) **(TSL)**: Force Power Crush Opposition Ii
- `FORCE_POWER_CRUSH_OPPOSITION_III` (146) **(TSL)**: Force Power Crush Opposition Iii
- `FORCE_POWER_CRUSH_OPPOSITION_IV` (147) **(TSL)**: Force Power Crush Opposition Iv
- `FORCE_POWER_CRUSH_OPPOSITION_V` (148) **(TSL)**: Force Power Crush Opposition V
- `FORCE_POWER_CRUSH_OPPOSITION_VI` (149) **(TSL)**: Force Power Crush Opposition Vi
- `FORCE_POWER_FORCE_BODY` (150) **(TSL)**: Force Power Force Body
- `FORCE_POWER_IMPROVED_FORCE_BODY` (151) **(TSL)**: Force Power Improved Force Body
- `FORCE_POWER_MASTER_FORCE_BODY` (152) **(TSL)**: Force Power Master Force Body
- `FORCE_POWER_DRAIN_FORCE` (153) **(TSL)**: Force Power Drain Force
- `FORCE_POWER_IMPROVED_DRAIN_FORCE` (154) **(TSL)**: Force Power Improved Drain Force
- `FORCE_POWER_MASTER_DRAIN_FORCE` (155) **(TSL)**: Force Power Master Drain Force
- `FORCE_POWER_FORCE_CAMOUFLAGE` (156) **(TSL)**: Force Power Force Camouflage
- `FORCE_POWER_IMPROVED_FORCE_CAMOUFLAGE` (157) **(TSL)**: Force Power Improved Force Camouflage
- `FORCE_POWER_MASTER_FORCE_CAMOUFLAGE` (158) **(TSL)**: Force Power Master Force Camouflage
- `FORCE_POWER_FORCE_SCREAM` (159) **(TSL)**: Force Power Force Scream
- `FORCE_POWER_IMPROVED_FORCE_SCREAM` (160) **(TSL)**: Force Power Improved Force Scream
- `FORCE_POWER_MASTER_FORCE_SCREAM` (161) **(TSL)**: Force Power Master Force Scream
- `FORCE_POWER_FORCE_REPULSION` (162) **(TSL)**: Force Power Force Repulsion
- `FORCE_POWER_FURY` (164) **(TSL)**: Force Power Fury
- `FORCE_POWER_IMPROVED_FURY` (165) **(TSL)**: Force Power Improved Fury
- `FORCE_POWER_MASTER_FURY` (166) **(TSL)**: Force Power Master Fury
- `FORCE_POWER_INSPIRE_FOLLOWERS_I` (167) **(TSL)**: Force Power Inspire Followers I
- `FORCE_POWER_INSPIRE_FOLLOWERS_II` (168) **(TSL)**: Force Power Inspire Followers Ii
- `FORCE_POWER_INSPIRE_FOLLOWERS_III` (169) **(TSL)**: Force Power Inspire Followers Iii
- `FORCE_POWER_INSPIRE_FOLLOWERS_IV` (170) **(TSL)**: Force Power Inspire Followers Iv
- `FORCE_POWER_INSPIRE_FOLLOWERS_V` (171) **(TSL)**: Force Power Inspire Followers V
- `FORCE_POWER_INSPIRE_FOLLOWERS_VI` (172) **(TSL)**: Force Power Inspire Followers Vi
- `FORCE_POWER_REVITALIZE` (173) **(TSL)**: Force Power Revitalize
- `FORCE_POWER_IMPROVED_REVITALIZE` (174) **(TSL)**: Force Power Improved Revitalize
- `FORCE_POWER_MASTER_REVITALIZE` (175) **(TSL)**: Force Power Master Revitalize
- `FORCE_POWER_FORCE_SIGHT` (176) **(TSL)**: Force Power Force Sight
- `FORCE_POWER_FORCE_CRUSH` (177) **(TSL)**: Force Power Force Crush
- `FORCE_POWER_PRECOGNITION` (178) **(TSL)**: Force Power Precognition
- `FORCE_POWER_BATTLE_PRECOGNITION` (179) **(TSL)**: Force Power Battle Precognition
- `FORCE_POWER_FORCE_ENLIGHTENMENT` (180) **(TSL)**: Force Power Force Enlightenment
- `FORCE_POWER_MIND_TRICK` (181) **(TSL)**: Force Power Mind Trick
- `FORCE_POWER_CONFUSION` (200) **(TSL)**: Force Power Confusion
- `FORCE_POWER_BEAST_TRICK` (182) **(TSL)**: Force Power Beast Trick
- `FORCE_POWER_BEAST_CONFUSION` (184) **(TSL)**: Force Power Beast Confusion
- `FORCE_POWER_DROID_TRICK` (201) **(TSL)**: Force Power Droid Trick
- `FORCE_POWER_DROID_CONFUSION` (269) **(TSL)**: Force Power Droid Confusion
- `FORCE_POWER_BREATH_CONTROL` (270) **(TSL)**: Force Power Breath Control
- `FORCE_POWER_WOOKIEE_RAGE_I` (271) **(TSL)**: Force Power Wookiee Rage I
- `FORCE_POWER_WOOKIEE_RAGE_II` (272) **(TSL)**: Force Power Wookiee Rage Ii
- `FORCE_POWER_WOOKIEE_RAGE_III` (273) **(TSL)**: Force Power Wookiee Rage Iii
- `FORM_LIGHTSABER_PADAWAN_I` (205) **(TSL)**: Form Lightsaber Padawan I
- `FORM_LIGHTSABER_PADAWAN_II` (206) **(TSL)**: Form Lightsaber Padawan Ii
- `FORM_LIGHTSABER_PADAWAN_III` (207) **(TSL)**: Form Lightsaber Padawan Iii
- `FORM_LIGHTSABER_DAKLEAN_I` (208) **(TSL)**: Form Lightsaber Daklean I
- `FORM_LIGHTSABER_DAKLEAN_II` (209) **(TSL)**: Form Lightsaber Daklean Ii
- `FORM_LIGHTSABER_DAKLEAN_III` (210) **(TSL)**: Form Lightsaber Daklean Iii
- `FORM_LIGHTSABER_SENTINEL_I` (211) **(TSL)**: Form Lightsaber Sentinel I
- `FORM_LIGHTSABER_SENTINEL_II` (212) **(TSL)**: Form Lightsaber Sentinel Ii
- `FORM_LIGHTSABER_SENTINEL_III` (213) **(TSL)**: Form Lightsaber Sentinel Iii
- `FORM_LIGHTSABER_SODAK_I` (214) **(TSL)**: Form Lightsaber Sodak I
- `FORM_LIGHTSABER_SODAK_II` (215) **(TSL)**: Form Lightsaber Sodak Ii
- `FORM_LIGHTSABER_SODAK_III` (216) **(TSL)**: Form Lightsaber Sodak Iii
- `FORM_LIGHTSABER_ANCIENT_I` (217) **(TSL)**: Form Lightsaber Ancient I
- `FORM_LIGHTSABER_ANCIENT_II` (218) **(TSL)**: Form Lightsaber Ancient Ii
- `FORM_LIGHTSABER_ANCIENT_III` (219) **(TSL)**: Form Lightsaber Ancient Iii
- `FORM_LIGHTSABER_MASTER_I` (220) **(TSL)**: Form Lightsaber Master I
- `FORM_LIGHTSABER_MASTER_II` (221) **(TSL)**: Form Lightsaber Master Ii
- `FORM_LIGHTSABER_MASTER_III` (222) **(TSL)**: Form Lightsaber Master Iii
- `FORM_CONSULAR_FORCE_FOCUS_I` (223) **(TSL)**: Form Consular Force Focus I
- `FORM_CONSULAR_FORCE_FOCUS_II` (224) **(TSL)**: Form Consular Force Focus Ii
- `FORM_CONSULAR_FORCE_FOCUS_III` (225) **(TSL)**: Form Consular Force Focus Iii
- `FORM_CONSULAR_ENDURING_FORCE_I` (226) **(TSL)**: Form Consular Enduring Force I
- `FORM_CONSULAR_ENDURING_FORCE_II` (227) **(TSL)**: Form Consular Enduring Force Ii
- `FORM_CONSULAR_ENDURING_FORCE_III` (228) **(TSL)**: Form Consular Enduring Force Iii
- `FORM_CONSULAR_FORCE_AMPLIFICATION_I` (229) **(TSL)**: Form Consular Force Amplification I
- `FORM_CONSULAR_FORCE_AMPLIFICATION_II` (230) **(TSL)**: Form Consular Force Amplification Ii
- `FORM_CONSULAR_FORCE_AMPLIFICATION_III` (231) **(TSL)**: Form Consular Force Amplification Iii
- `FORM_CONSULAR_FORCE_SHELL_I` (232) **(TSL)**: Form Consular Force Shell I
- `FORM_CONSULAR_FORCE_SHELL_II` (233) **(TSL)**: Form Consular Force Shell Ii
- `FORM_CONSULAR_FORCE_SHELL_III` (234) **(TSL)**: Form Consular Force Shell Iii
- `FORM_CONSULAR_FORCE_POTENCY_I` (235) **(TSL)**: Form Consular Force Potency I
- `FORM_CONSULAR_FORCE_POTENCY_II` (236) **(TSL)**: Form Consular Force Potency Ii
- `FORM_CONSULAR_FORCE_POTENCY_III` (237) **(TSL)**: Form Consular Force Potency Iii
- `FORM_CONSULAR_REGENERATION_I` (238) **(TSL)**: Form Consular Regeneration I
- `FORM_CONSULAR_REGENERATION_II` (239) **(TSL)**: Form Consular Regeneration Ii
- `FORM_CONSULAR_REGENERATION_III` (240) **(TSL)**: Form Consular Regeneration Iii
- `FORM_CONSULAR_POWER_OF_THE_DARK_SIDE_I` (241) **(TSL)**: Form Consular Power Of The Dark Side I
- `FORM_CONSULAR_POWER_OF_THE_DARK_SIDE_II` (242) **(TSL)**: Form Consular Power Of The Dark Side Ii
- `FORM_CONSULAR_POWER_OF_THE_DARK_SIDE_III` (243) **(TSL)**: Form Consular Power Of The Dark Side Iii
- `FORM_SABER_I_SHII_CHO` (258) **(TSL)**: Form Saber I Shii Cho
- `FORM_SABER_II_MAKASHI` (259) **(TSL)**: Form Saber Ii Makashi
- `FORM_SABER_III_SORESU` (260) **(TSL)**: Form Saber Iii Soresu
- `FORM_SABER_IV_ATARU` (261) **(TSL)**: Form Saber Iv Ataru
- `FORM_SABER_V_SHIEN` (262) **(TSL)**: Form Saber V Shien
- `FORM_SABER_VI_NIMAN` (263) **(TSL)**: Form Saber Vi Niman
- `FORM_SABER_VII_JUYO` (264) **(TSL)**: Form Saber Vii Juyo
- `FORM_FORCE_I_FOCUS` (265) **(TSL)**: Form Force I Focus
- `FORM_FORCE_II_POTENCY` (266) **(TSL)**: Form Force Ii Potency
- `FORM_FORCE_III_AFFINITY` (267) **(TSL)**: Form Force Iii Affinity
- `FORM_FORCE_IV_MASTERY` (268) **(TSL)**: Form Force Iv Mastery
- `STANDARD_FACTION_SELF_LOATHING` (21) **(TSL)**: Standard Faction Self Loathing
- `STANDARD_FACTION_ONE_ON_ONE` (22) **(TSL)**: Standard Faction One On One
- `STANDARD_FACTION_PARTYPUPPET` (23) **(TSL)**: Standard Faction Partypuppet
- `ACTION_FOLLOWOWNER` (43) **(TSL)**: Action Followowner
- `PUP_SENSORBALL` (0) **(TSL)**: Pup Sensorball
- `PUP_OTHER1` (1) **(TSL)**: Pup Other1
- `PUP_OTHER2` (2) **(TSL)**: Pup Other2
- `SHIELD_PLOT_MAN_M28AA` (18) **(TSL)**: Shield Plot Man M28Aa
- `SHIELD_HEAT` (19) **(TSL)**: Shield Heat
- `SHIELD_DREXL` (20) **(TSL)**: Shield Drexl
- `VIDEO_EFFECT_CLAIRVOYANCE` (3) **(TSL)**: Video Effect Clairvoyance
- `VIDEO_EFFECT_FORCESIGHT` (4) **(TSL)**: Video Effect Forcesight
- `VIDEO_EFFECT_VISAS_FREELOOK` (5) **(TSL)**: Video Effect Visas Freelook
- `VIDEO_EFFECT_CLAIRVOYANCEFULL` (6) **(TSL)**: Video Effect Clairvoyancefull
- `VIDEO_EFFECT_FURY_1` (7) **(TSL)**: Video Effect Fury 1
- `VIDEO_EFFECT_FURY_2` (8) **(TSL)**: Video Effect Fury 2
- `VIDEO_EFFECT_FURY_3` (9) **(TSL)**: Video Effect Fury 3
- `VIDEO_FFECT_SECURITY_NO_LABEL` (10) **(TSL)**: Video Ffect Security No Label
- `TUTORIAL_WINDOW_TEMP1` (42) **(TSL)**: Tutorial Window Temp1
- `TUTORIAL_WINDOW_TEMP2` (43) **(TSL)**: Tutorial Window Temp2
- `TUTORIAL_WINDOW_TEMP3` (44) **(TSL)**: Tutorial Window Temp3
- `TUTORIAL_WINDOW_TEMP4` (45) **(TSL)**: Tutorial Window Temp4
- `TUTORIAL_WINDOW_TEMP5` (46) **(TSL)**: Tutorial Window Temp5
- `TUTORIAL_WINDOW_TEMP6` (47) **(TSL)**: Tutorial Window Temp6
- `TUTORIAL_WINDOW_TEMP7` (48) **(TSL)**: Tutorial Window Temp7
- `TUTORIAL_WINDOW_TEMP8` (49) **(TSL)**: Tutorial Window Temp8
- `TUTORIAL_WINDOW_TEMP9` (50) **(TSL)**: Tutorial Window Temp9
- `TUTORIAL_WINDOW_TEMP10` (51) **(TSL)**: Tutorial Window Temp10
- `TUTORIAL_WINDOW_TEMP11` (52) **(TSL)**: Tutorial Window Temp11
- `TUTORIAL_WINDOW_TEMP12` (53) **(TSL)**: Tutorial Window Temp12
- `TUTORIAL_WINDOW_TEMP13` (54) **(TSL)**: Tutorial Window Temp13
- `TUTORIAL_WINDOW_TEMP14` (55) **(TSL)**: Tutorial Window Temp14
- `TUTORIAL_WINDOW_TEMP15` (56) **(TSL)**: Tutorial Window Temp15
- `AI_LEVEL_VERY_HIGH` (4) **(TSL)**: Ai Level Very High
- `AI_LEVEL_HIGH` (3) **(TSL)**: Ai Level High
- `AI_LEVEL_NORMAL` (2) **(TSL)**: Ai Level Normal
- `AI_LEVEL_LOW` (1) **(TSL)**: Ai Level Low
- `AI_LEVEL_VERY_LOW` (0) **(TSL)**: Ai Level Very Low
- `IMPLANT_NONE` (0) **(TSL)**: Implant None
- `IMPLANT_REGEN` (1) **(TSL)**: Implant Regen
- `IMPLANT_STR` (2) **(TSL)**: Implant Str
- `IMPLANT_END` (3) **(TSL)**: Implant End
- `IMPLANT_AGI` (4) **(TSL)**: Implant Agi
- `FORFEIT_NO_FORCE_POWERS` (1) **(TSL)**: Forfeit No Force Powers
- `FORFEIT_NO_ITEMS` (2) **(TSL)**: Forfeit No Items
- `FORFEIT_NO_WEAPONS` (4) **(TSL)**: Forfeit No Weapons
- `FORFEIT_DXUN_SWORD_ONLY` (8) **(TSL)**: Forfeit Dxun Sword Only
- `FORFEIT_NO_ARMOR` (16) **(TSL)**: Forfeit No Armor
- `FORFEIT_NO_RANGED` (32) **(TSL)**: Forfeit No Ranged
- `FORFEIT_NO_LIGHTSABER` (64) **(TSL)**: Forfeit No Lightsaber
- `FORFEIT_NO_ITEM_BUT_SHIELD` (128) **(TSL)**: Forfeit No Item But Shield

<a id="true"></a>

#### `TRUE` **(K1 & TSL)**

(1): True
<a id="false"></a>

#### `FALSE` **(K1 & TSL)**

(0): False
<a id="pi"></a>

#### `PI` **(K1 & TSL)**

(3.141592): Pi
<a id="attitude_neutral"></a>

#### `ATTITUDE_NEUTRAL` **(K1 & TSL)**

(0): Attitude Neutral
<a id="attitude_aggressive"></a>

#### `ATTITUDE_AGGRESSIVE` **(K1 & TSL)**

(1): Attitude Aggressive
<a id="attitude_defensive"></a>

#### `ATTITUDE_DEFENSIVE` **(K1 & TSL)**

(2): Attitude Defensive
<a id="attitude_special"></a>

#### `ATTITUDE_SPECIAL` **(K1 & TSL)**

(3): Attitude Special
<a id="radius_size_small"></a>

#### `RADIUS_SIZE_SMALL` **(K1 & TSL)**

(1.67): Radius Size Small
<a id="radius_size_medium"></a>

#### `RADIUS_SIZE_MEDIUM` **(K1 & TSL)**

(3.33): Radius Size Medium
<a id="radius_size_large"></a>

#### `RADIUS_SIZE_LARGE` **(K1 & TSL)**

(5.0): Radius Size Large
<a id="radius_size_huge"></a>

#### `RADIUS_SIZE_HUGE` **(K1 & TSL)**

(6.67): Radius Size Huge
<a id="radius_size_gargantuan"></a>

#### `RADIUS_SIZE_GARGANTUAN` **(K1 & TSL)**

(8.33): Radius Size Gargantuan
<a id="radius_size_colossal"></a>

#### `RADIUS_SIZE_COLOSSAL` **(K1 & TSL)**

(10.0): Radius Size Colossal
<a id="attack_result_invalid"></a>

#### `ATTACK_RESULT_INVALID` **(K1 & TSL)**

(0): Attack Result Invalid
<a id="attack_result_hit_successful"></a>

#### `ATTACK_RESULT_HIT_SUCCESSFUL` **(K1 & TSL)**

(1): Attack Result Hit Successful
<a id="attack_result_critical_hit"></a>

#### `ATTACK_RESULT_CRITICAL_HIT` **(K1 & TSL)**

(2): Attack Result Critical Hit
<a id="attack_result_automatic_hit"></a>

#### `ATTACK_RESULT_AUTOMATIC_HIT` **(K1 & TSL)**

(3): Attack Result Automatic Hit
<a id="attack_result_miss"></a>

#### `ATTACK_RESULT_MISS` **(K1 & TSL)**

(4): Attack Result Miss
<a id="attack_result_attack_resisted"></a>

#### `ATTACK_RESULT_ATTACK_RESISTED` **(K1 & TSL)**

(5): Attack Result Attack Resisted
<a id="attack_result_attack_failed"></a>

#### `ATTACK_RESULT_ATTACK_FAILED` **(K1 & TSL)**

(6): Attack Result Attack Failed
<a id="attack_result_parried"></a>

#### `ATTACK_RESULT_PARRIED` **(K1 & TSL)**

(8): Attack Result Parried
<a id="attack_result_deflected"></a>

#### `ATTACK_RESULT_DEFLECTED` **(K1 & TSL)**

(9): Attack Result Deflected
<a id="aoe_per_fogacid"></a>

#### `AOE_PER_FOGACID` **(K1 & TSL)**

(0): Aoe Per Fogacid
<a id="aoe_per_fogfire"></a>

#### `AOE_PER_FOGFIRE` **(K1 & TSL)**

(1): Aoe Per Fogfire
<a id="aoe_per_fogstink"></a>

#### `AOE_PER_FOGSTINK` **(K1 & TSL)**

(2): Aoe Per Fogstink
<a id="aoe_per_fogkill"></a>

#### `AOE_PER_FOGKILL` **(K1 & TSL)**

(3): Aoe Per Fogkill
<a id="aoe_per_fogmind"></a>

#### `AOE_PER_FOGMIND` **(K1 & TSL)**

(4): Aoe Per Fogmind
<a id="aoe_per_wallfire"></a>

#### `AOE_PER_WALLFIRE` **(K1 & TSL)**

(5): Aoe Per Wallfire
<a id="aoe_per_wallwind"></a>

#### `AOE_PER_WALLWIND` **(K1 & TSL)**

(6): Aoe Per Wallwind
<a id="aoe_per_wallblade"></a>

#### `AOE_PER_WALLBLADE` **(K1 & TSL)**

(7): Aoe Per Wallblade
<a id="aoe_per_web"></a>

#### `AOE_PER_WEB` **(K1 & TSL)**

(8): Aoe Per Web
<a id="aoe_per_entangle"></a>

#### `AOE_PER_ENTANGLE` **(K1 & TSL)**

(9): Aoe Per Entangle
<a id="aoe_per_darkness"></a>

#### `AOE_PER_DARKNESS` **(K1 & TSL)**

(11): Aoe Per Darkness
<a id="aoe_mob_circevil"></a>

#### `AOE_MOB_CIRCEVIL` **(K1 & TSL)**

(12): Aoe Mob Circevil
<a id="aoe_mob_circgood"></a>

#### `AOE_MOB_CIRCGOOD` **(K1 & TSL)**

(13): Aoe Mob Circgood
<a id="aoe_mob_circlaw"></a>

#### `AOE_MOB_CIRCLAW` **(K1 & TSL)**

(14): Aoe Mob Circlaw
<a id="aoe_mob_circchaos"></a>

#### `AOE_MOB_CIRCCHAOS` **(K1 & TSL)**

(15): Aoe Mob Circchaos
<a id="aoe_mob_fear"></a>

#### `AOE_MOB_FEAR` **(K1 & TSL)**

(16): Aoe Mob Fear
<a id="aoe_mob_blinding"></a>

#### `AOE_MOB_BLINDING` **(K1 & TSL)**

(17): Aoe Mob Blinding
<a id="aoe_mob_unearthly"></a>

#### `AOE_MOB_UNEARTHLY` **(K1 & TSL)**

(18): Aoe Mob Unearthly
<a id="aoe_mob_menace"></a>

#### `AOE_MOB_MENACE` **(K1 & TSL)**

(19): Aoe Mob Menace
<a id="aoe_mob_unnatural"></a>

#### `AOE_MOB_UNNATURAL` **(K1 & TSL)**

(20): Aoe Mob Unnatural
<a id="aoe_mob_stun"></a>

#### `AOE_MOB_STUN` **(K1 & TSL)**

(21): Aoe Mob Stun
<a id="aoe_mob_protection"></a>

#### `AOE_MOB_PROTECTION` **(K1 & TSL)**

(22): Aoe Mob Protection
<a id="aoe_mob_fire"></a>

#### `AOE_MOB_FIRE` **(K1 & TSL)**

(23): Aoe Mob Fire
<a id="aoe_mob_frost"></a>

#### `AOE_MOB_FROST` **(K1 & TSL)**

(24): Aoe Mob Frost
<a id="aoe_mob_electrical"></a>

#### `AOE_MOB_ELECTRICAL` **(K1 & TSL)**

(25): Aoe Mob Electrical
<a id="aoe_per_fogghoul"></a>

#### `AOE_PER_FOGGHOUL` **(K1 & TSL)**

(26): Aoe Per Fogghoul
<a id="aoe_mob_tyrant_fog"></a>

#### `AOE_MOB_TYRANT_FOG` **(K1 & TSL)**

(27): Aoe Mob Tyrant Fog
<a id="aoe_per_storm"></a>

#### `AOE_PER_STORM` **(K1 & TSL)**

(28): Aoe Per Storm
<a id="aoe_per_invis_sphere"></a>

#### `AOE_PER_INVIS_SPHERE` **(K1 & TSL)**

(29): Aoe Per Invis Sphere
<a id="aoe_mob_silence"></a>

#### `AOE_MOB_SILENCE` **(K1 & TSL)**

(30): Aoe Mob Silence
<a id="aoe_per_delay_blast_fireball"></a>

#### `AOE_PER_DELAY_BLAST_FIREBALL` **(K1 & TSL)**

(31): Aoe Per Delay Blast Fireball
<a id="aoe_per_grease"></a>

#### `AOE_PER_GREASE` **(K1 & TSL)**

(32): Aoe Per Grease
<a id="aoe_per_creeping_doom"></a>

#### `AOE_PER_CREEPING_DOOM` **(K1 & TSL)**

(33): Aoe Per Creeping Doom
<a id="aoe_per_evards_black_tentacles"></a>

#### `AOE_PER_EVARDS_BLACK_TENTACLES` **(K1 & TSL)**

(34): Aoe Per Evards Black Tentacles
<a id="aoe_mob_invisibility_purge"></a>

#### `AOE_MOB_INVISIBILITY_PURGE` **(K1 & TSL)**

(35): Aoe Mob Invisibility Purge
<a id="aoe_mob_dragon_fear"></a>

#### `AOE_MOB_DRAGON_FEAR` **(K1 & TSL)**

(36): Aoe Mob Dragon Fear
<a id="force_power_all_force_powers"></a>

#### `FORCE_POWER_ALL_FORCE_POWERS` **(K1 & TSL)**

(-1): Force Power All Force Powers
<a id="force_power_master_alter"></a>

#### `FORCE_POWER_MASTER_ALTER` **(K1 & TSL)**

(0): Force Power Master Alter
<a id="force_power_master_control"></a>

#### `FORCE_POWER_MASTER_CONTROL` **(K1 & TSL)**

(1): Force Power Master Control
<a id="force_power_master_sense"></a>

#### `FORCE_POWER_MASTER_SENSE` **(K1 & TSL)**

(2): Force Power Master Sense
<a id="force_power_force_jump_advanced"></a>

#### `FORCE_POWER_FORCE_JUMP_ADVANCED` **(K1 & TSL)**

(3): Force Power Force Jump Advanced
<a id="force_power_light_saber_throw_advanced"></a>

#### `FORCE_POWER_LIGHT_SABER_THROW_ADVANCED` **(K1 & TSL)**

(4): Force Power Light Saber Throw Advanced
<a id="force_power_regneration_advanced"></a>

#### `FORCE_POWER_REGNERATION_ADVANCED` **(K1 & TSL)**

(5): Force Power Regneration Advanced
<a id="force_power_affect_mind"></a>

#### `FORCE_POWER_AFFECT_MIND` **(K1 & TSL)**

(6): Force Power Affect Mind
<a id="force_power_affliction"></a>

#### `FORCE_POWER_AFFLICTION` **(K1 & TSL)**

(7): Force Power Affliction
<a id="force_power_speed_burst"></a>

#### `FORCE_POWER_SPEED_BURST` **(K1 & TSL)**

(8): Force Power Speed Burst
<a id="force_power_choke"></a>

#### `FORCE_POWER_CHOKE` **(K1 & TSL)**

(9): Force Power Choke
<a id="force_power_cure"></a>

#### `FORCE_POWER_CURE` **(K1 & TSL)**

(10): Force Power Cure
<a id="force_power_death_field"></a>

#### `FORCE_POWER_DEATH_FIELD` **(K1 & TSL)**

(11): Force Power Death Field
<a id="force_power_droid_disable"></a>

#### `FORCE_POWER_DROID_DISABLE` **(K1 & TSL)**

(12): Force Power Droid Disable
<a id="force_power_droid_destroy"></a>

#### `FORCE_POWER_DROID_DESTROY` **(K1 & TSL)**

(13): Force Power Droid Destroy
<a id="force_power_dominate"></a>

#### `FORCE_POWER_DOMINATE` **(K1 & TSL)**

(14): Force Power Dominate
<a id="force_power_drain_life"></a>

#### `FORCE_POWER_DRAIN_LIFE` **(K1 & TSL)**

(15): Force Power Drain Life
<a id="force_power_fear"></a>

#### `FORCE_POWER_FEAR` **(K1 & TSL)**

(16): Force Power Fear
<a id="force_power_force_armor"></a>

#### `FORCE_POWER_FORCE_ARMOR` **(K1 & TSL)**

(17): Force Power Force Armor
<a id="force_power_force_aura"></a>

#### `FORCE_POWER_FORCE_AURA` **(K1 & TSL)**

(18): Force Power Force Aura
<a id="force_power_force_breach"></a>

#### `FORCE_POWER_FORCE_BREACH` **(K1 & TSL)**

(19): Force Power Force Breach
<a id="force_power_force_immunity"></a>

#### `FORCE_POWER_FORCE_IMMUNITY` **(K1 & TSL)**

(20): Force Power Force Immunity
<a id="force_power_force_jump"></a>

#### `FORCE_POWER_FORCE_JUMP` **(K1 & TSL)**

(21): Force Power Force Jump
<a id="force_power_force_mind"></a>

#### `FORCE_POWER_FORCE_MIND` **(K1 & TSL)**

(22): Force Power Force Mind
<a id="force_power_force_push"></a>

#### `FORCE_POWER_FORCE_PUSH` **(K1 & TSL)**

(23): Force Power Force Push
<a id="force_power_force_shield"></a>

#### `FORCE_POWER_FORCE_SHIELD` **(K1 & TSL)**

(24): Force Power Force Shield
<a id="force_power_force_storm"></a>

#### `FORCE_POWER_FORCE_STORM` **(K1 & TSL)**

(25): Force Power Force Storm
<a id="force_power_force_wave"></a>

#### `FORCE_POWER_FORCE_WAVE` **(K1 & TSL)**

(26): Force Power Force Wave
<a id="force_power_force_whirlwind"></a>

#### `FORCE_POWER_FORCE_WHIRLWIND` **(K1 & TSL)**

(27): Force Power Force Whirlwind
<a id="force_power_heal"></a>

#### `FORCE_POWER_HEAL` **(K1 & TSL)**

(28): Force Power Heal
<a id="force_power_hold"></a>

#### `FORCE_POWER_HOLD` **(K1 & TSL)**

(29): Force Power Hold
<a id="force_power_horror"></a>

#### `FORCE_POWER_HORROR` **(K1 & TSL)**

(30): Force Power Horror
<a id="force_power_insanity"></a>

#### `FORCE_POWER_INSANITY` **(K1 & TSL)**

(31): Force Power Insanity
<a id="force_power_kill"></a>

#### `FORCE_POWER_KILL` **(K1 & TSL)**

(32): Force Power Kill
<a id="force_power_knight_mind"></a>

#### `FORCE_POWER_KNIGHT_MIND` **(K1 & TSL)**

(33): Force Power Knight Mind
<a id="force_power_knight_speed"></a>

#### `FORCE_POWER_KNIGHT_SPEED` **(K1 & TSL)**

(34): Force Power Knight Speed
<a id="force_power_lightning"></a>

#### `FORCE_POWER_LIGHTNING` **(K1 & TSL)**

(35): Force Power Lightning
<a id="force_power_mind_mastery"></a>

#### `FORCE_POWER_MIND_MASTERY` **(K1 & TSL)**

(36): Force Power Mind Mastery
<a id="force_power_speed_mastery"></a>

#### `FORCE_POWER_SPEED_MASTERY` **(K1 & TSL)**

(37): Force Power Speed Mastery
<a id="force_power_plague"></a>

#### `FORCE_POWER_PLAGUE` **(K1 & TSL)**

(38): Force Power Plague
<a id="force_power_regeneration"></a>

#### `FORCE_POWER_REGENERATION` **(K1 & TSL)**

(39): Force Power Regeneration
<a id="force_power_resist_cold_heat_energy"></a>

#### `FORCE_POWER_RESIST_COLD_HEAT_ENERGY` **(K1 & TSL)**

(40): Force Power Resist Cold Heat Energy
<a id="force_power_resist_force"></a>

#### `FORCE_POWER_RESIST_FORCE` **(K1 & TSL)**

(41): Force Power Resist Force
<a id="force_power_shock"></a>

#### `FORCE_POWER_SHOCK` **(K1 & TSL)**

(43): Force Power Shock
<a id="force_power_sleep"></a>

#### `FORCE_POWER_SLEEP` **(K1 & TSL)**

(44): Force Power Sleep
<a id="force_power_slow"></a>

#### `FORCE_POWER_SLOW` **(K1 & TSL)**

(45): Force Power Slow
<a id="force_power_stun"></a>

#### `FORCE_POWER_STUN` **(K1 & TSL)**

(46): Force Power Stun
<a id="force_power_droid_stun"></a>

#### `FORCE_POWER_DROID_STUN` **(K1 & TSL)**

(47): Force Power Droid Stun
<a id="force_power_supress_force"></a>

#### `FORCE_POWER_SUPRESS_FORCE` **(K1 & TSL)**

(48): Force Power Supress Force
<a id="force_power_light_saber_throw"></a>

#### `FORCE_POWER_LIGHT_SABER_THROW` **(K1 & TSL)**

(49): Force Power Light Saber Throw
<a id="force_power_wound"></a>

#### `FORCE_POWER_WOUND` **(K1 & TSL)**

(50): Force Power Wound
<a id="persistent_zone_active"></a>

#### `PERSISTENT_ZONE_ACTIVE` **(K1 & TSL)**

(0): Persistent Zone Active
<a id="persistent_zone_follow"></a>

#### `PERSISTENT_ZONE_FOLLOW` **(K1 & TSL)**

(1): Persistent Zone Follow
<a id="invalid_standard_faction"></a>

#### `INVALID_STANDARD_FACTION` **(K1 & TSL)**

(-1): Invalid Standard Faction
<a id="standard_faction_hostile_1"></a>

#### `STANDARD_FACTION_HOSTILE_1` **(K1 & TSL)**

(1): Standard Faction Hostile 1
<a id="standard_faction_friendly_1"></a>

#### `STANDARD_FACTION_FRIENDLY_1` **(K1 & TSL)**

(2): Standard Faction Friendly 1
<a id="standard_faction_hostile_2"></a>

#### `STANDARD_FACTION_HOSTILE_2` **(K1 & TSL)**

(3): Standard Faction Hostile 2
<a id="standard_faction_friendly_2"></a>

#### `STANDARD_FACTION_FRIENDLY_2` **(K1 & TSL)**

(4): Standard Faction Friendly 2
<a id="standard_faction_neutral"></a>

#### `STANDARD_FACTION_NEUTRAL` **(K1 & TSL)**

(5): Standard Faction Neutral
<a id="standard_faction_insane"></a>

#### `STANDARD_FACTION_INSANE` **(K1 & TSL)**

(6): Standard Faction Insane
<a id="standard_faction_ptat_tuskan"></a>

#### `STANDARD_FACTION_PTAT_TUSKAN` **(K1 & TSL)**

(7): Standard Faction Ptat Tuskan
<a id="standard_faction_glb_xor"></a>

#### `STANDARD_FACTION_GLB_XOR` **(K1 & TSL)**

(8): Standard Faction Glb Xor
<a id="standard_faction_surrender_1"></a>

#### `STANDARD_FACTION_SURRENDER_1` **(K1 & TSL)**

(9): Standard Faction Surrender 1
<a id="standard_faction_surrender_2"></a>

#### `STANDARD_FACTION_SURRENDER_2` **(K1 & TSL)**

(10): Standard Faction Surrender 2
<a id="standard_faction_predator"></a>

#### `STANDARD_FACTION_PREDATOR` **(K1 & TSL)**

(11): Standard Faction Predator
<a id="standard_faction_prey"></a>

#### `STANDARD_FACTION_PREY` **(K1 & TSL)**

(12): Standard Faction Prey
<a id="standard_faction_trap"></a>

#### `STANDARD_FACTION_TRAP` **(K1 & TSL)**

(13): Standard Faction Trap
<a id="standard_faction_endar_spire"></a>

#### `STANDARD_FACTION_ENDAR_SPIRE` **(K1 & TSL)**

(14): Standard Faction Endar Spire
<a id="standard_faction_rancor"></a>

#### `STANDARD_FACTION_RANCOR` **(K1 & TSL)**

(15): Standard Faction Rancor
<a id="standard_faction_gizka_1"></a>

#### `STANDARD_FACTION_GIZKA_1` **(K1 & TSL)**

(16): Standard Faction Gizka 1
<a id="standard_faction_gizka_2"></a>

#### `STANDARD_FACTION_GIZKA_2` **(K1 & TSL)**

(17): Standard Faction Gizka 2
<a id="subskill_flagtrap"></a>

#### `SUBSKILL_FLAGTRAP` **(K1 & TSL)**

(100): Subskill Flagtrap
<a id="subskill_recovertrap"></a>

#### `SUBSKILL_RECOVERTRAP` **(K1 & TSL)**

(101): Subskill Recovertrap
<a id="subskill_examinetrap"></a>

#### `SUBSKILL_EXAMINETRAP` **(K1 & TSL)**

(102): Subskill Examinetrap
<a id="talent_type_force"></a>

#### `TALENT_TYPE_FORCE` **(K1 & TSL)**

(0): Talent Type Force
<a id="talent_type_spell"></a>

#### `TALENT_TYPE_SPELL` **(K1 & TSL)**

(0): Talent Type Spell
<a id="talent_type_feat"></a>

#### `TALENT_TYPE_FEAT` **(K1 & TSL)**

(1): Talent Type Feat
<a id="talent_type_skill"></a>

#### `TALENT_TYPE_SKILL` **(K1 & TSL)**

(2): Talent Type Skill
<a id="talent_exclude_all_of_type"></a>

#### `TALENT_EXCLUDE_ALL_OF_TYPE` **(K1 & TSL)**

(-1): Talent Exclude All Of Type
<a id="gui_panel_player_death"></a>

#### `GUI_PANEL_PLAYER_DEATH` **(K1 & TSL)**

(0): Gui Panel Player Death
<a id="polymorph_type_werewolf"></a>

#### `POLYMORPH_TYPE_WEREWOLF` **(K1 & TSL)**

(0): Polymorph Type Werewolf
<a id="polymorph_type_wererat"></a>

#### `POLYMORPH_TYPE_WERERAT` **(K1 & TSL)**

(1): Polymorph Type Wererat
<a id="polymorph_type_werecat"></a>

#### `POLYMORPH_TYPE_WERECAT` **(K1 & TSL)**

(2): Polymorph Type Werecat
<a id="polymorph_type_giant_spider"></a>

#### `POLYMORPH_TYPE_GIANT_SPIDER` **(K1 & TSL)**

(3): Polymorph Type Giant Spider
<a id="polymorph_type_troll"></a>

#### `POLYMORPH_TYPE_TROLL` **(K1 & TSL)**

(4): Polymorph Type Troll
<a id="polymorph_type_umber_hulk"></a>

#### `POLYMORPH_TYPE_UMBER_HULK` **(K1 & TSL)**

(5): Polymorph Type Umber Hulk
<a id="polymorph_type_pixie"></a>

#### `POLYMORPH_TYPE_PIXIE` **(K1 & TSL)**

(6): Polymorph Type Pixie
<a id="polymorph_type_zombie"></a>

#### `POLYMORPH_TYPE_ZOMBIE` **(K1 & TSL)**

(7): Polymorph Type Zombie
<a id="polymorph_type_red_dragon"></a>

#### `POLYMORPH_TYPE_RED_DRAGON` **(K1 & TSL)**

(8): Polymorph Type Red Dragon
<a id="polymorph_type_fire_giant"></a>

#### `POLYMORPH_TYPE_FIRE_GIANT` **(K1 & TSL)**

(9): Polymorph Type Fire Giant
<a id="polymorph_type_balor"></a>

#### `POLYMORPH_TYPE_BALOR` **(K1 & TSL)**

(10): Polymorph Type Balor
<a id="polymorph_type_death_slaad"></a>

#### `POLYMORPH_TYPE_DEATH_SLAAD` **(K1 & TSL)**

(11): Polymorph Type Death Slaad
<a id="polymorph_type_iron_golem"></a>

#### `POLYMORPH_TYPE_IRON_GOLEM` **(K1 & TSL)**

(12): Polymorph Type Iron Golem
<a id="polymorph_type_huge_fire_elemental"></a>

#### `POLYMORPH_TYPE_HUGE_FIRE_ELEMENTAL` **(K1 & TSL)**

(13): Polymorph Type Huge Fire Elemental
<a id="polymorph_type_huge_water_elemental"></a>

#### `POLYMORPH_TYPE_HUGE_WATER_ELEMENTAL` **(K1 & TSL)**

(14): Polymorph Type Huge Water Elemental
<a id="polymorph_type_huge_earth_elemental"></a>

#### `POLYMORPH_TYPE_HUGE_EARTH_ELEMENTAL` **(K1 & TSL)**

(15): Polymorph Type Huge Earth Elemental
<a id="polymorph_type_huge_air_elemental"></a>

#### `POLYMORPH_TYPE_HUGE_AIR_ELEMENTAL` **(K1 & TSL)**

(16): Polymorph Type Huge Air Elemental
<a id="polymorph_type_elder_fire_elemental"></a>

#### `POLYMORPH_TYPE_ELDER_FIRE_ELEMENTAL` **(K1 & TSL)**

(17): Polymorph Type Elder Fire Elemental
<a id="polymorph_type_elder_water_elemental"></a>

#### `POLYMORPH_TYPE_ELDER_WATER_ELEMENTAL` **(K1 & TSL)**

(18): Polymorph Type Elder Water Elemental
<a id="polymorph_type_elder_earth_elemental"></a>

#### `POLYMORPH_TYPE_ELDER_EARTH_ELEMENTAL` **(K1 & TSL)**

(19): Polymorph Type Elder Earth Elemental
<a id="polymorph_type_elder_air_elemental"></a>

#### `POLYMORPH_TYPE_ELDER_AIR_ELEMENTAL` **(K1 & TSL)**

(20): Polymorph Type Elder Air Elemental
<a id="polymorph_type_brown_bear"></a>

#### `POLYMORPH_TYPE_BROWN_BEAR` **(K1 & TSL)**

(21): Polymorph Type Brown Bear
<a id="polymorph_type_panther"></a>

#### `POLYMORPH_TYPE_PANTHER` **(K1 & TSL)**

(22): Polymorph Type Panther
<a id="polymorph_type_wolf"></a>

#### `POLYMORPH_TYPE_WOLF` **(K1 & TSL)**

(23): Polymorph Type Wolf
<a id="polymorph_type_boar"></a>

#### `POLYMORPH_TYPE_BOAR` **(K1 & TSL)**

(24): Polymorph Type Boar
<a id="polymorph_type_badger"></a>

#### `POLYMORPH_TYPE_BADGER` **(K1 & TSL)**

(25): Polymorph Type Badger
<a id="polymorph_type_penguin"></a>

#### `POLYMORPH_TYPE_PENGUIN` **(K1 & TSL)**

(26): Polymorph Type Penguin
<a id="polymorph_type_cow"></a>

#### `POLYMORPH_TYPE_COW` **(K1 & TSL)**

(27): Polymorph Type Cow
<a id="polymorph_type_doom_knight"></a>

#### `POLYMORPH_TYPE_DOOM_KNIGHT` **(K1 & TSL)**

(28): Polymorph Type Doom Knight
<a id="polymorph_type_yuanti"></a>

#### `POLYMORPH_TYPE_YUANTI` **(K1 & TSL)**

(29): Polymorph Type Yuanti
<a id="polymorph_type_imp"></a>

#### `POLYMORPH_TYPE_IMP` **(K1 & TSL)**

(30): Polymorph Type Imp
<a id="polymorph_type_quasit"></a>

#### `POLYMORPH_TYPE_QUASIT` **(K1 & TSL)**

(31): Polymorph Type Quasit
<a id="polymorph_type_succubus"></a>

#### `POLYMORPH_TYPE_SUCCUBUS` **(K1 & TSL)**

(32): Polymorph Type Succubus
<a id="polymorph_type_dire_brown_bear"></a>

#### `POLYMORPH_TYPE_DIRE_BROWN_BEAR` **(K1 & TSL)**

(33): Polymorph Type Dire Brown Bear
<a id="polymorph_type_dire_panther"></a>

#### `POLYMORPH_TYPE_DIRE_PANTHER` **(K1 & TSL)**

(34): Polymorph Type Dire Panther
<a id="polymorph_type_dire_wolf"></a>

#### `POLYMORPH_TYPE_DIRE_WOLF` **(K1 & TSL)**

(35): Polymorph Type Dire Wolf
<a id="polymorph_type_dire_boar"></a>

#### `POLYMORPH_TYPE_DIRE_BOAR` **(K1 & TSL)**

(36): Polymorph Type Dire Boar
<a id="polymorph_type_dire_badger"></a>

#### `POLYMORPH_TYPE_DIRE_BADGER` **(K1 & TSL)**

(37): Polymorph Type Dire Badger
<a id="creature_size_invalid"></a>

#### `CREATURE_SIZE_INVALID` **(K1 & TSL)**

(0): Creature Size Invalid
<a id="creature_size_tiny"></a>

#### `CREATURE_SIZE_TINY` **(K1 & TSL)**

(1): Creature Size Tiny
<a id="creature_size_small"></a>

#### `CREATURE_SIZE_SMALL` **(K1 & TSL)**

(2): Creature Size Small
<a id="creature_size_medium"></a>

#### `CREATURE_SIZE_MEDIUM` **(K1 & TSL)**

(3): Creature Size Medium
<a id="creature_size_large"></a>

#### `CREATURE_SIZE_LARGE` **(K1 & TSL)**

(4): Creature Size Large
<a id="creature_size_huge"></a>

#### `CREATURE_SIZE_HUGE` **(K1 & TSL)**

(5): Creature Size Huge
<a id="camera_mode_chase_camera"></a>

#### `CAMERA_MODE_CHASE_CAMERA` **(K1 & TSL)**

(0): Camera Mode Chase Camera
<a id="camera_mode_top_down"></a>

#### `CAMERA_MODE_TOP_DOWN` **(K1 & TSL)**

(1): Camera Mode Top Down
<a id="camera_mode_stiff_chase_camera"></a>

#### `CAMERA_MODE_STIFF_CHASE_CAMERA` **(K1 & TSL)**

(2): Camera Mode Stiff Chase Camera
<a id="game_difficulty_very_easy"></a>

#### `GAME_DIFFICULTY_VERY_EASY` **(K1 & TSL)**

(0): Game Difficulty Very Easy
<a id="game_difficulty_easy"></a>

#### `GAME_DIFFICULTY_EASY` **(K1 & TSL)**

(1): Game Difficulty Easy
<a id="game_difficulty_normal"></a>

#### `GAME_DIFFICULTY_NORMAL` **(K1 & TSL)**

(2): Game Difficulty Normal
<a id="game_difficulty_core_rules"></a>

#### `GAME_DIFFICULTY_CORE_RULES` **(K1 & TSL)**

(3): Game Difficulty Core Rules
<a id="game_difficulty_difficult"></a>

#### `GAME_DIFFICULTY_DIFFICULT` **(K1 & TSL)**

(4): Game Difficulty Difficult
<a id="action_movetopoint"></a>

#### `ACTION_MOVETOPOINT` **(K1 & TSL)**

(0): Action Movetopoint
<a id="action_pickupitem"></a>

#### `ACTION_PICKUPITEM` **(K1 & TSL)**

(1): Action Pickupitem
<a id="action_dropitem"></a>

#### `ACTION_DROPITEM` **(K1 & TSL)**

(2): Action Dropitem
<a id="action_attackobject"></a>

#### `ACTION_ATTACKOBJECT` **(K1 & TSL)**

(3): Action Attackobject
<a id="action_castspell"></a>

#### `ACTION_CASTSPELL` **(K1 & TSL)**

(4): Action Castspell
<a id="action_opendoor"></a>

#### `ACTION_OPENDOOR` **(K1 & TSL)**

(5): Action Opendoor
<a id="action_closedoor"></a>

#### `ACTION_CLOSEDOOR` **(K1 & TSL)**

(6): Action Closedoor
<a id="action_dialogobject"></a>

#### `ACTION_DIALOGOBJECT` **(K1 & TSL)**

(7): Action Dialogobject
<a id="action_disabletrap"></a>

#### `ACTION_DISABLETRAP` **(K1 & TSL)**

(8): Action Disabletrap
<a id="action_recovertrap"></a>

#### `ACTION_RECOVERTRAP` **(K1 & TSL)**

(9): Action Recovertrap
<a id="action_flagtrap"></a>

#### `ACTION_FLAGTRAP` **(K1 & TSL)**

(10): Action Flagtrap
<a id="action_examinetrap"></a>

#### `ACTION_EXAMINETRAP` **(K1 & TSL)**

(11): Action Examinetrap
<a id="action_settrap"></a>

#### `ACTION_SETTRAP` **(K1 & TSL)**

(12): Action Settrap
<a id="action_openlock"></a>

#### `ACTION_OPENLOCK` **(K1 & TSL)**

(13): Action Openlock
<a id="action_lock"></a>

#### `ACTION_LOCK` **(K1 & TSL)**

(14): Action Lock
<a id="action_useobject"></a>

#### `ACTION_USEOBJECT` **(K1 & TSL)**

(15): Action Useobject
<a id="action_animalempathy"></a>

#### `ACTION_ANIMALEMPATHY` **(K1 & TSL)**

(16): Action Animalempathy
<a id="action_rest"></a>

#### `ACTION_REST` **(K1 & TSL)**

(17): Action Rest
<a id="action_taunt"></a>

#### `ACTION_TAUNT` **(K1 & TSL)**

(18): Action Taunt
<a id="action_itemcastspell"></a>

#### `ACTION_ITEMCASTSPELL` **(K1 & TSL)**

(19): Action Itemcastspell
<a id="action_counterspell"></a>

#### `ACTION_COUNTERSPELL` **(K1 & TSL)**

(31): Action Counterspell
<a id="action_heal"></a>

#### `ACTION_HEAL` **(K1 & TSL)**

(33): Action Heal
<a id="action_pickpocket"></a>

#### `ACTION_PICKPOCKET` **(K1 & TSL)**

(34): Action Pickpocket
<a id="action_follow"></a>

#### `ACTION_FOLLOW` **(K1 & TSL)**

(35): Action Follow
<a id="action_wait"></a>

#### `ACTION_WAIT` **(K1 & TSL)**

(36): Action Wait
<a id="action_sit"></a>

#### `ACTION_SIT` **(K1 & TSL)**

(37): Action Sit
<a id="action_followleader"></a>

#### `ACTION_FOLLOWLEADER` **(K1 & TSL)**

(38): Action Followleader
<a id="action_invalid"></a>

#### `ACTION_INVALID` **(K1 & TSL)**

(65535): Action Invalid
<a id="action_queueempty"></a>

#### `ACTION_QUEUEEMPTY` **(K1 & TSL)**

(65534): Action Queueempty
<a id="swminigame_trackfollower_sound_engine"></a>

#### `SWMINIGAME_TRACKFOLLOWER_SOUND_ENGINE` **(K1 & TSL)**

(0): Swminigame Trackfollower Sound Engine
<a id="swminigame_trackfollower_sound_death"></a>

#### `SWMINIGAME_TRACKFOLLOWER_SOUND_DEATH` **(K1 & TSL)**

(1): Swminigame Trackfollower Sound Death
<a id="plot_o_doom"></a>

#### `PLOT_O_DOOM` **(K1 & TSL)**

(0): Plot O Doom
<a id="plot_o_scary_stuff"></a>

#### `PLOT_O_SCARY_STUFF` **(K1 & TSL)**

(1): Plot O Scary Stuff
<a id="plot_o_big_monsters"></a>

#### `PLOT_O_BIG_MONSTERS` **(K1 & TSL)**

(2): Plot O Big Monsters
<a id="formation_wedge"></a>

#### `FORMATION_WEDGE` **(K1 & TSL)**

(0): Formation Wedge
<a id="formation_line"></a>

#### `FORMATION_LINE` **(K1 & TSL)**

(1): Formation Line
<a id="subscreen_id_none"></a>

#### `SUBSCREEN_ID_NONE` **(K1 & TSL)**

(0): Subscreen Id None
<a id="subscreen_id_equip"></a>

#### `SUBSCREEN_ID_EQUIP` **(K1 & TSL)**

(1): Subscreen Id Equip
<a id="subscreen_id_item"></a>

#### `SUBSCREEN_ID_ITEM` **(K1 & TSL)**

(2): Subscreen Id Item
<a id="subscreen_id_character_record"></a>

#### `SUBSCREEN_ID_CHARACTER_RECORD` **(K1 & TSL)**

(3): Subscreen Id Character Record
<a id="subscreen_id_ability"></a>

#### `SUBSCREEN_ID_ABILITY` **(K1 & TSL)**

(4): Subscreen Id Ability
<a id="subscreen_id_map"></a>

#### `SUBSCREEN_ID_MAP` **(K1 & TSL)**

(5): Subscreen Id Map
<a id="subscreen_id_quest"></a>

#### `SUBSCREEN_ID_QUEST` **(K1 & TSL)**

(6): Subscreen Id Quest
<a id="subscreen_id_options"></a>

#### `SUBSCREEN_ID_OPTIONS` **(K1 & TSL)**

(7): Subscreen Id Options
<a id="subscreen_id_messages"></a>

#### `SUBSCREEN_ID_MESSAGES` **(K1 & TSL)**

(8): Subscreen Id Messages
<a id="shield_droid_energy_1"></a>

#### `SHIELD_DROID_ENERGY_1` **(K1 & TSL)**

(0): Shield Droid Energy 1
<a id="shield_droid_energy_2"></a>

#### `SHIELD_DROID_ENERGY_2` **(K1 & TSL)**

(1): Shield Droid Energy 2
<a id="shield_droid_energy_3"></a>

#### `SHIELD_DROID_ENERGY_3` **(K1 & TSL)**

(2): Shield Droid Energy 3
<a id="shield_droid_enviro_1"></a>

#### `SHIELD_DROID_ENVIRO_1` **(K1 & TSL)**

(3): Shield Droid Enviro 1
<a id="shield_droid_enviro_2"></a>

#### `SHIELD_DROID_ENVIRO_2` **(K1 & TSL)**

(4): Shield Droid Enviro 2
<a id="shield_droid_enviro_3"></a>

#### `SHIELD_DROID_ENVIRO_3` **(K1 & TSL)**

(5): Shield Droid Enviro 3
<a id="shield_energy"></a>

#### `SHIELD_ENERGY` **(K1 & TSL)**

(6): Shield Energy
<a id="shield_energy_sith"></a>

#### `SHIELD_ENERGY_SITH` **(K1 & TSL)**

(7): Shield Energy Sith
<a id="shield_energy_arkanian"></a>

#### `SHIELD_ENERGY_ARKANIAN` **(K1 & TSL)**

(8): Shield Energy Arkanian
<a id="shield_echani"></a>

#### `SHIELD_ECHANI` **(K1 & TSL)**

(9): Shield Echani
<a id="shield_mandalorian_melee"></a>

#### `SHIELD_MANDALORIAN_MELEE` **(K1 & TSL)**

(10): Shield Mandalorian Melee
<a id="shield_mandalorian_power"></a>

#### `SHIELD_MANDALORIAN_POWER` **(K1 & TSL)**

(11): Shield Mandalorian Power
<a id="shield_dueling_echani"></a>

#### `SHIELD_DUELING_ECHANI` **(K1 & TSL)**

(12): Shield Dueling Echani
<a id="shield_dueling_yusanis"></a>

#### `SHIELD_DUELING_YUSANIS` **(K1 & TSL)**

(13): Shield Dueling Yusanis
<a id="shield_verpine_prototype"></a>

#### `SHIELD_VERPINE_PROTOTYPE` **(K1 & TSL)**

(14): Shield Verpine Prototype
<a id="shield_antique_droid"></a>

#### `SHIELD_ANTIQUE_DROID` **(K1 & TSL)**

(15): Shield Antique Droid
<a id="shield_plot_tar_m09aa"></a>

#### `SHIELD_PLOT_TAR_M09AA` **(K1 & TSL)**

(16): Shield Plot Tar M09Aa
<a id="shield_plot_unk_m44aa"></a>

#### `SHIELD_PLOT_UNK_M44AA` **(K1 & TSL)**

(17): Shield Plot Unk M44Aa
<a id="video_effect_none"></a>

#### `VIDEO_EFFECT_NONE` **(K1 & TSL)**

(-1): Video Effect None
<a id="video_effect_security_camera"></a>

#### `VIDEO_EFFECT_SECURITY_CAMERA` **(K1 & TSL)**

(0): Video Effect Security Camera
<a id="video_effect_freelook_t3m4"></a>

#### `VIDEO_EFFECT_FREELOOK_T3M4` **(K1 & TSL)**

(1): Video Effect Freelook T3M4
<a id="video_effect_freelook_hk47"></a>

#### `VIDEO_EFFECT_FREELOOK_HK47` **(K1 & TSL)**

(2): Video Effect Freelook Hk47
<a id="tutorial_window_start_swoop_race"></a>

#### `TUTORIAL_WINDOW_START_SWOOP_RACE` **(K1 & TSL)**

(0): Tutorial Window Start Swoop Race
<a id="tutorial_window_return_to_base"></a>

#### `TUTORIAL_WINDOW_RETURN_TO_BASE` **(K1 & TSL)**

(1): Tutorial Window Return To Base
<a id="tutorial_window_movement_keys"></a>

#### `TUTORIAL_WINDOW_MOVEMENT_KEYS` **(K1)**

(2): Tutorial Window Movement Keys
<a id="live_content_pkg1"></a>

#### `LIVE_CONTENT_PKG1` **(K1 & TSL)**

(1): Live Content Pkg1
<a id="live_content_pkg2"></a>

#### `LIVE_CONTENT_PKG2` **(K1 & TSL)**

(2): Live Content Pkg2
<a id="live_content_pkg3"></a>

#### `LIVE_CONTENT_PKG3` **(K1 & TSL)**

(3): Live Content Pkg3
<a id="live_content_pkg4"></a>

#### `LIVE_CONTENT_PKG4` **(K1 & TSL)**

(4): Live Content Pkg4
<a id="live_content_pkg5"></a>

#### `LIVE_CONTENT_PKG5` **(K1 & TSL)**

(5): Live Content Pkg5
<a id="live_content_pkg6"></a>

#### `LIVE_CONTENT_PKG6` **(K1 & TSL)**

(6): Live Content Pkg6
<a id="slanguage"></a>

#### `sLanguage` **(K1)**

(""nwscript""): Slanguage
<a id="form_mask_force_focus"></a>

#### `FORM_MASK_FORCE_FOCUS` **(TSL)**

(1): Form Mask Force Focus
<a id="form_mask_enduring_force"></a>

#### `FORM_MASK_ENDURING_FORCE` **(TSL)**

(2): Form Mask Enduring Force
<a id="form_mask_force_amplification"></a>

#### `FORM_MASK_FORCE_AMPLIFICATION` **(TSL)**

(4): Form Mask Force Amplification
<a id="form_mask_force_potency"></a>

#### `FORM_MASK_FORCE_POTENCY` **(TSL)**

(8): Form Mask Force Potency
<a id="form_mask_regeneration"></a>

#### `FORM_MASK_REGENERATION` **(TSL)**

(16): Form Mask Regeneration
<a id="form_mask_power_of_the_dark_side"></a>

#### `FORM_MASK_POWER_OF_THE_DARK_SIDE` **(TSL)**

(32): Form Mask Power Of The Dark Side
<a id="force_power_master_energy_resistance"></a>

#### `FORCE_POWER_MASTER_ENERGY_RESISTANCE` **(TSL)**

(133): Force Power Master Energy Resistance
<a id="force_power_master_heal"></a>

#### `FORCE_POWER_MASTER_HEAL` **(TSL)**

(134): Force Power Master Heal
<a id="force_power_force_barrier"></a>

#### `FORCE_POWER_FORCE_BARRIER` **(TSL)**

(135): Force Power Force Barrier
<a id="force_power_improved_force_barrier"></a>

#### `FORCE_POWER_IMPROVED_FORCE_BARRIER` **(TSL)**

(136): Force Power Improved Force Barrier
<a id="force_power_master_force_barrier"></a>

#### `FORCE_POWER_MASTER_FORCE_BARRIER` **(TSL)**

(137): Force Power Master Force Barrier
<a id="force_power_battle_meditation_pc"></a>

#### `FORCE_POWER_BATTLE_MEDITATION_PC` **(TSL)**

(138): Force Power Battle Meditation Pc
<a id="force_power_improved_battle_meditation_pc"></a>

#### `FORCE_POWER_IMPROVED_BATTLE_MEDITATION_PC` **(TSL)**

(139): Force Power Improved Battle Meditation Pc
<a id="force_power_master_battle_meditation_pc"></a>

#### `FORCE_POWER_MASTER_BATTLE_MEDITATION_PC` **(TSL)**

(140): Force Power Master Battle Meditation Pc
<a id="force_power_bat_med_enemy"></a>

#### `FORCE_POWER_BAT_MED_ENEMY` **(TSL)**

(141): Force Power Bat Med Enemy
<a id="force_power_imp_bat_med_enemy"></a>

#### `FORCE_POWER_IMP_BAT_MED_ENEMY` **(TSL)**

(142): Force Power Imp Bat Med Enemy
<a id="force_power_mas_bat_med_enemy"></a>

#### `FORCE_POWER_MAS_BAT_MED_ENEMY` **(TSL)**

(143): Force Power Mas Bat Med Enemy
<a id="force_power_crush_opposition_i"></a>

#### `FORCE_POWER_CRUSH_OPPOSITION_I` **(TSL)**

(144): Force Power Crush Opposition I
<a id="force_power_crush_opposition_ii"></a>

#### `FORCE_POWER_CRUSH_OPPOSITION_II` **(TSL)**

(145): Force Power Crush Opposition Ii
<a id="force_power_crush_opposition_iii"></a>

#### `FORCE_POWER_CRUSH_OPPOSITION_III` **(TSL)**

(146): Force Power Crush Opposition Iii
<a id="force_power_crush_opposition_iv"></a>

#### `FORCE_POWER_CRUSH_OPPOSITION_IV` **(TSL)**

(147): Force Power Crush Opposition Iv
<a id="force_power_crush_opposition_v"></a>

#### `FORCE_POWER_CRUSH_OPPOSITION_V` **(TSL)**

(148): Force Power Crush Opposition V
<a id="force_power_crush_opposition_vi"></a>

#### `FORCE_POWER_CRUSH_OPPOSITION_VI` **(TSL)**

(149): Force Power Crush Opposition Vi
<a id="force_power_force_body"></a>

#### `FORCE_POWER_FORCE_BODY` **(TSL)**

(150): Force Power Force Body
<a id="force_power_improved_force_body"></a>

#### `FORCE_POWER_IMPROVED_FORCE_BODY` **(TSL)**

(151): Force Power Improved Force Body
<a id="force_power_master_force_body"></a>

#### `FORCE_POWER_MASTER_FORCE_BODY` **(TSL)**

(152): Force Power Master Force Body
<a id="force_power_drain_force"></a>

#### `FORCE_POWER_DRAIN_FORCE` **(TSL)**

(153): Force Power Drain Force
<a id="force_power_improved_drain_force"></a>

#### `FORCE_POWER_IMPROVED_DRAIN_FORCE` **(TSL)**

(154): Force Power Improved Drain Force
<a id="force_power_master_drain_force"></a>

#### `FORCE_POWER_MASTER_DRAIN_FORCE` **(TSL)**

(155): Force Power Master Drain Force
<a id="force_power_force_camouflage"></a>

#### `FORCE_POWER_FORCE_CAMOUFLAGE` **(TSL)**

(156): Force Power Force Camouflage
<a id="force_power_improved_force_camouflage"></a>

#### `FORCE_POWER_IMPROVED_FORCE_CAMOUFLAGE` **(TSL)**

(157): Force Power Improved Force Camouflage
<a id="force_power_master_force_camouflage"></a>

#### `FORCE_POWER_MASTER_FORCE_CAMOUFLAGE` **(TSL)**

(158): Force Power Master Force Camouflage
<a id="force_power_force_scream"></a>

#### `FORCE_POWER_FORCE_SCREAM` **(TSL)**

(159): Force Power Force Scream
<a id="force_power_improved_force_scream"></a>

#### `FORCE_POWER_IMPROVED_FORCE_SCREAM` **(TSL)**

(160): Force Power Improved Force Scream
<a id="force_power_master_force_scream"></a>

#### `FORCE_POWER_MASTER_FORCE_SCREAM` **(TSL)**

(161): Force Power Master Force Scream
<a id="force_power_force_repulsion"></a>

#### `FORCE_POWER_FORCE_REPULSION` **(TSL)**

(162): Force Power Force Repulsion
<a id="force_power_fury"></a>

#### `FORCE_POWER_FURY` **(TSL)**

(164): Force Power Fury
<a id="force_power_improved_fury"></a>

#### `FORCE_POWER_IMPROVED_FURY` **(TSL)**

(165): Force Power Improved Fury
<a id="force_power_master_fury"></a>

#### `FORCE_POWER_MASTER_FURY` **(TSL)**

(166): Force Power Master Fury
<a id="force_power_inspire_followers_i"></a>

#### `FORCE_POWER_INSPIRE_FOLLOWERS_I` **(TSL)**

(167): Force Power Inspire Followers I
<a id="force_power_inspire_followers_ii"></a>

#### `FORCE_POWER_INSPIRE_FOLLOWERS_II` **(TSL)**

(168): Force Power Inspire Followers Ii
<a id="force_power_inspire_followers_iii"></a>

#### `FORCE_POWER_INSPIRE_FOLLOWERS_III` **(TSL)**

(169): Force Power Inspire Followers Iii
<a id="force_power_inspire_followers_iv"></a>

#### `FORCE_POWER_INSPIRE_FOLLOWERS_IV` **(TSL)**

(170): Force Power Inspire Followers Iv
<a id="force_power_inspire_followers_v"></a>

#### `FORCE_POWER_INSPIRE_FOLLOWERS_V` **(TSL)**

(171): Force Power Inspire Followers V
<a id="force_power_inspire_followers_vi"></a>

#### `FORCE_POWER_INSPIRE_FOLLOWERS_VI` **(TSL)**

(172): Force Power Inspire Followers Vi
<a id="force_power_revitalize"></a>

#### `FORCE_POWER_REVITALIZE` **(TSL)**

(173): Force Power Revitalize
<a id="force_power_improved_revitalize"></a>

#### `FORCE_POWER_IMPROVED_REVITALIZE` **(TSL)**

(174): Force Power Improved Revitalize
<a id="force_power_master_revitalize"></a>

#### `FORCE_POWER_MASTER_REVITALIZE` **(TSL)**

(175): Force Power Master Revitalize
<a id="force_power_force_sight"></a>

#### `FORCE_POWER_FORCE_SIGHT` **(TSL)**

(176): Force Power Force Sight
<a id="force_power_force_crush"></a>

#### `FORCE_POWER_FORCE_CRUSH` **(TSL)**

(177): Force Power Force Crush
<a id="force_power_precognition"></a>

#### `FORCE_POWER_PRECOGNITION` **(TSL)**

(178): Force Power Precognition
<a id="force_power_battle_precognition"></a>

#### `FORCE_POWER_BATTLE_PRECOGNITION` **(TSL)**

(179): Force Power Battle Precognition
<a id="force_power_force_enlightenment"></a>

#### `FORCE_POWER_FORCE_ENLIGHTENMENT` **(TSL)**

(180): Force Power Force Enlightenment
<a id="force_power_mind_trick"></a>

#### `FORCE_POWER_MIND_TRICK` **(TSL)**

(181): Force Power Mind Trick
<a id="force_power_confusion"></a>

#### `FORCE_POWER_CONFUSION` **(TSL)**

(200): Force Power Confusion
<a id="force_power_beast_trick"></a>

#### `FORCE_POWER_BEAST_TRICK` **(TSL)**

(182): Force Power Beast Trick
<a id="force_power_beast_confusion"></a>

#### `FORCE_POWER_BEAST_CONFUSION` **(TSL)**

(184): Force Power Beast Confusion
<a id="force_power_droid_trick"></a>

#### `FORCE_POWER_DROID_TRICK` **(TSL)**

(201): Force Power Droid Trick
<a id="force_power_droid_confusion"></a>

#### `FORCE_POWER_DROID_CONFUSION` **(TSL)**

(269): Force Power Droid Confusion
<a id="force_power_breath_control"></a>

#### `FORCE_POWER_BREATH_CONTROL` **(TSL)**

(270): Force Power Breath Control
<a id="force_power_wookiee_rage_i"></a>

#### `FORCE_POWER_WOOKIEE_RAGE_I` **(TSL)**

(271): Force Power Wookiee Rage I
<a id="force_power_wookiee_rage_ii"></a>

#### `FORCE_POWER_WOOKIEE_RAGE_II` **(TSL)**

(272): Force Power Wookiee Rage Ii
<a id="force_power_wookiee_rage_iii"></a>

#### `FORCE_POWER_WOOKIEE_RAGE_III` **(TSL)**

(273): Force Power Wookiee Rage Iii
<a id="form_lightsaber_padawan_i"></a>

#### `FORM_LIGHTSABER_PADAWAN_I` **(TSL)**

(205): Form Lightsaber Padawan I
<a id="form_lightsaber_padawan_ii"></a>

#### `FORM_LIGHTSABER_PADAWAN_II` **(TSL)**

(206): Form Lightsaber Padawan Ii
<a id="form_lightsaber_padawan_iii"></a>

#### `FORM_LIGHTSABER_PADAWAN_III` **(TSL)**

(207): Form Lightsaber Padawan Iii
<a id="form_lightsaber_daklean_i"></a>

#### `FORM_LIGHTSABER_DAKLEAN_I` **(TSL)**

(208): Form Lightsaber Daklean I
<a id="form_lightsaber_daklean_ii"></a>

#### `FORM_LIGHTSABER_DAKLEAN_II` **(TSL)**

(209): Form Lightsaber Daklean Ii
<a id="form_lightsaber_daklean_iii"></a>

#### `FORM_LIGHTSABER_DAKLEAN_III` **(TSL)**

(210): Form Lightsaber Daklean Iii
<a id="form_lightsaber_sentinel_i"></a>

#### `FORM_LIGHTSABER_SENTINEL_I` **(TSL)**

(211): Form Lightsaber Sentinel I
<a id="form_lightsaber_sentinel_ii"></a>

#### `FORM_LIGHTSABER_SENTINEL_II` **(TSL)**

(212): Form Lightsaber Sentinel Ii
<a id="form_lightsaber_sentinel_iii"></a>

#### `FORM_LIGHTSABER_SENTINEL_III` **(TSL)**

(213): Form Lightsaber Sentinel Iii
<a id="form_lightsaber_sodak_i"></a>

#### `FORM_LIGHTSABER_SODAK_I` **(TSL)**

(214): Form Lightsaber Sodak I
<a id="form_lightsaber_sodak_ii"></a>

#### `FORM_LIGHTSABER_SODAK_II` **(TSL)**

(215): Form Lightsaber Sodak Ii
<a id="form_lightsaber_sodak_iii"></a>

#### `FORM_LIGHTSABER_SODAK_III` **(TSL)**

(216): Form Lightsaber Sodak Iii
<a id="form_lightsaber_ancient_i"></a>

#### `FORM_LIGHTSABER_ANCIENT_I` **(TSL)**

(217): Form Lightsaber Ancient I
<a id="form_lightsaber_ancient_ii"></a>

#### `FORM_LIGHTSABER_ANCIENT_II` **(TSL)**

(218): Form Lightsaber Ancient Ii
<a id="form_lightsaber_ancient_iii"></a>

#### `FORM_LIGHTSABER_ANCIENT_III` **(TSL)**

(219): Form Lightsaber Ancient Iii
<a id="form_lightsaber_master_i"></a>

#### `FORM_LIGHTSABER_MASTER_I` **(TSL)**

(220): Form Lightsaber Master I
<a id="form_lightsaber_master_ii"></a>

#### `FORM_LIGHTSABER_MASTER_II` **(TSL)**

(221): Form Lightsaber Master Ii
<a id="form_lightsaber_master_iii"></a>

#### `FORM_LIGHTSABER_MASTER_III` **(TSL)**

(222): Form Lightsaber Master Iii
<a id="form_consular_force_focus_i"></a>

#### `FORM_CONSULAR_FORCE_FOCUS_I` **(TSL)**

(223): Form Consular Force Focus I
<a id="form_consular_force_focus_ii"></a>

#### `FORM_CONSULAR_FORCE_FOCUS_II` **(TSL)**

(224): Form Consular Force Focus Ii
<a id="form_consular_force_focus_iii"></a>

#### `FORM_CONSULAR_FORCE_FOCUS_III` **(TSL)**

(225): Form Consular Force Focus Iii
<a id="form_consular_enduring_force_i"></a>

#### `FORM_CONSULAR_ENDURING_FORCE_I` **(TSL)**

(226): Form Consular Enduring Force I
<a id="form_consular_enduring_force_ii"></a>

#### `FORM_CONSULAR_ENDURING_FORCE_II` **(TSL)**

(227): Form Consular Enduring Force Ii
<a id="form_consular_enduring_force_iii"></a>

#### `FORM_CONSULAR_ENDURING_FORCE_III` **(TSL)**

(228): Form Consular Enduring Force Iii
<a id="form_consular_force_amplification_i"></a>

#### `FORM_CONSULAR_FORCE_AMPLIFICATION_I` **(TSL)**

(229): Form Consular Force Amplification I
<a id="form_consular_force_amplification_ii"></a>

#### `FORM_CONSULAR_FORCE_AMPLIFICATION_II` **(TSL)**

(230): Form Consular Force Amplification Ii
<a id="form_consular_force_amplification_iii"></a>

#### `FORM_CONSULAR_FORCE_AMPLIFICATION_III` **(TSL)**

(231): Form Consular Force Amplification Iii
<a id="form_consular_force_shell_i"></a>

#### `FORM_CONSULAR_FORCE_SHELL_I` **(TSL)**

(232): Form Consular Force Shell I
<a id="form_consular_force_shell_ii"></a>

#### `FORM_CONSULAR_FORCE_SHELL_II` **(TSL)**

(233): Form Consular Force Shell Ii
<a id="form_consular_force_shell_iii"></a>

#### `FORM_CONSULAR_FORCE_SHELL_III` **(TSL)**

(234): Form Consular Force Shell Iii
<a id="form_consular_force_potency_i"></a>

#### `FORM_CONSULAR_FORCE_POTENCY_I` **(TSL)**

(235): Form Consular Force Potency I
<a id="form_consular_force_potency_ii"></a>

#### `FORM_CONSULAR_FORCE_POTENCY_II` **(TSL)**

(236): Form Consular Force Potency Ii
<a id="form_consular_force_potency_iii"></a>

#### `FORM_CONSULAR_FORCE_POTENCY_III` **(TSL)**

(237): Form Consular Force Potency Iii
<a id="form_consular_regeneration_i"></a>

#### `FORM_CONSULAR_REGENERATION_I` **(TSL)**

(238): Form Consular Regeneration I
<a id="form_consular_regeneration_ii"></a>

#### `FORM_CONSULAR_REGENERATION_II` **(TSL)**

(239): Form Consular Regeneration Ii
<a id="form_consular_regeneration_iii"></a>

#### `FORM_CONSULAR_REGENERATION_III` **(TSL)**

(240): Form Consular Regeneration Iii
<a id="form_consular_power_of_the_dark_side_i"></a>

#### `FORM_CONSULAR_POWER_OF_THE_DARK_SIDE_I` **(TSL)**

(241): Form Consular Power Of The Dark Side I
<a id="form_consular_power_of_the_dark_side_ii"></a>

#### `FORM_CONSULAR_POWER_OF_THE_DARK_SIDE_II` **(TSL)**

(242): Form Consular Power Of The Dark Side Ii
<a id="form_consular_power_of_the_dark_side_iii"></a>

#### `FORM_CONSULAR_POWER_OF_THE_DARK_SIDE_III` **(TSL)**

(243): Form Consular Power Of The Dark Side Iii
<a id="form_saber_i_shii_cho"></a>

#### `FORM_SABER_I_SHII_CHO` **(TSL)**

(258): Form Saber I Shii Cho
<a id="form_saber_ii_makashi"></a>

#### `FORM_SABER_II_MAKASHI` **(TSL)**

(259): Form Saber Ii Makashi
<a id="form_saber_iii_soresu"></a>

#### `FORM_SABER_III_SORESU` **(TSL)**

(260): Form Saber Iii Soresu
<a id="form_saber_iv_ataru"></a>

#### `FORM_SABER_IV_ATARU` **(TSL)**

(261): Form Saber Iv Ataru
<a id="form_saber_v_shien"></a>

#### `FORM_SABER_V_SHIEN` **(TSL)**

(262): Form Saber V Shien
<a id="form_saber_vi_niman"></a>

#### `FORM_SABER_VI_NIMAN` **(TSL)**

(263): Form Saber Vi Niman
<a id="form_saber_vii_juyo"></a>

#### `FORM_SABER_VII_JUYO` **(TSL)**

(264): Form Saber Vii Juyo
<a id="form_force_i_focus"></a>

#### `FORM_FORCE_I_FOCUS` **(TSL)**

(265): Form Force I Focus
<a id="form_force_ii_potency"></a>

#### `FORM_FORCE_II_POTENCY` **(TSL)**

(266): Form Force Ii Potency
<a id="form_force_iii_affinity"></a>

#### `FORM_FORCE_III_AFFINITY` **(TSL)**

(267): Form Force Iii Affinity
<a id="form_force_iv_mastery"></a>

#### `FORM_FORCE_IV_MASTERY` **(TSL)**

(268): Form Force Iv Mastery
<a id="standard_faction_self_loathing"></a>

#### `STANDARD_FACTION_SELF_LOATHING` **(TSL)**

(21): Standard Faction Self Loathing
<a id="standard_faction_one_on_one"></a>

#### `STANDARD_FACTION_ONE_ON_ONE` **(TSL)**

(22): Standard Faction One On One
<a id="standard_faction_partypuppet"></a>

#### `STANDARD_FACTION_PARTYPUPPET` **(TSL)**

(23): Standard Faction Partypuppet
<a id="action_followowner"></a>

#### `ACTION_FOLLOWOWNER` **(TSL)**

(43): Action Followowner
<a id="pup_sensorball"></a>

#### `PUP_SENSORBALL` **(TSL)**

(0): Pup Sensorball
<a id="pup_other1"></a>

#### `PUP_OTHER1` **(TSL)**

(1): Pup Other1
<a id="pup_other2"></a>

#### `PUP_OTHER2` **(TSL)**

(2): Pup Other2
<a id="shield_plot_man_m28aa"></a>

#### `SHIELD_PLOT_MAN_M28AA` **(TSL)**

(18): Shield Plot Man M28Aa
<a id="shield_heat"></a>

#### `SHIELD_HEAT` **(TSL)**

(19): Shield Heat
<a id="shield_drexl"></a>

#### `SHIELD_DREXL` **(TSL)**

(20): Shield Drexl
<a id="video_effect_clairvoyance"></a>

#### `VIDEO_EFFECT_CLAIRVOYANCE` **(TSL)**

(3): Video Effect Clairvoyance
<a id="video_effect_forcesight"></a>

#### `VIDEO_EFFECT_FORCESIGHT` **(TSL)**

(4): Video Effect Forcesight
<a id="video_effect_visas_freelook"></a>

#### `VIDEO_EFFECT_VISAS_FREELOOK` **(TSL)**

(5): Video Effect Visas Freelook
<a id="video_effect_clairvoyancefull"></a>

#### `VIDEO_EFFECT_CLAIRVOYANCEFULL` **(TSL)**

(6): Video Effect Clairvoyancefull
<a id="video_effect_fury_1"></a>

#### `VIDEO_EFFECT_FURY_1` **(TSL)**

(7): Video Effect Fury 1
<a id="video_effect_fury_2"></a>

#### `VIDEO_EFFECT_FURY_2` **(TSL)**

(8): Video Effect Fury 2
<a id="video_effect_fury_3"></a>

#### `VIDEO_EFFECT_FURY_3` **(TSL)**

(9): Video Effect Fury 3
<a id="video_ffect_security_no_label"></a>

#### `VIDEO_FFECT_SECURITY_NO_LABEL` **(TSL)**

(10): Video Ffect Security No Label
<a id="tutorial_window_temp1"></a>

#### `TUTORIAL_WINDOW_TEMP1` **(TSL)**

(42): Tutorial Window Temp1
<a id="tutorial_window_temp2"></a>

#### `TUTORIAL_WINDOW_TEMP2` **(TSL)**

(43): Tutorial Window Temp2
<a id="tutorial_window_temp3"></a>

#### `TUTORIAL_WINDOW_TEMP3` **(TSL)**

(44): Tutorial Window Temp3
<a id="tutorial_window_temp4"></a>

#### `TUTORIAL_WINDOW_TEMP4` **(TSL)**

(45): Tutorial Window Temp4
<a id="tutorial_window_temp5"></a>

#### `TUTORIAL_WINDOW_TEMP5` **(TSL)**

(46): Tutorial Window Temp5
<a id="tutorial_window_temp6"></a>

#### `TUTORIAL_WINDOW_TEMP6` **(TSL)**

(47): Tutorial Window Temp6
<a id="tutorial_window_temp7"></a>

#### `TUTORIAL_WINDOW_TEMP7` **(TSL)**

(48): Tutorial Window Temp7
<a id="tutorial_window_temp8"></a>

#### `TUTORIAL_WINDOW_TEMP8` **(TSL)**

(49): Tutorial Window Temp8
<a id="tutorial_window_temp9"></a>

#### `TUTORIAL_WINDOW_TEMP9` **(TSL)**

(50): Tutorial Window Temp9
<a id="tutorial_window_temp10"></a>

#### `TUTORIAL_WINDOW_TEMP10` **(TSL)**

(51): Tutorial Window Temp10
<a id="tutorial_window_temp11"></a>

#### `TUTORIAL_WINDOW_TEMP11` **(TSL)**

(52): Tutorial Window Temp11
<a id="tutorial_window_temp12"></a>

#### `TUTORIAL_WINDOW_TEMP12` **(TSL)**

(53): Tutorial Window Temp12
<a id="tutorial_window_temp13"></a>

#### `TUTORIAL_WINDOW_TEMP13` **(TSL)**

(54): Tutorial Window Temp13
<a id="tutorial_window_temp14"></a>

#### `TUTORIAL_WINDOW_TEMP14` **(TSL)**

(55): Tutorial Window Temp14
<a id="tutorial_window_temp15"></a>

#### `TUTORIAL_WINDOW_TEMP15` **(TSL)**

(56): Tutorial Window Temp15
<a id="ai_level_very_high"></a>

#### `AI_LEVEL_VERY_HIGH` **(TSL)**

(4): Ai Level Very High
<a id="ai_level_high"></a>

#### `AI_LEVEL_HIGH` **(TSL)**

(3): Ai Level High
<a id="ai_level_normal"></a>

#### `AI_LEVEL_NORMAL` **(TSL)**

(2): Ai Level Normal
<a id="ai_level_low"></a>

#### `AI_LEVEL_LOW` **(TSL)**

(1): Ai Level Low
<a id="ai_level_very_low"></a>

#### `AI_LEVEL_VERY_LOW` **(TSL)**

(0): Ai Level Very Low
<a id="implant_none"></a>

#### `IMPLANT_NONE` **(TSL)**

(0): Implant None
<a id="implant_regen"></a>

#### `IMPLANT_REGEN` **(TSL)**

(1): Implant Regen
<a id="implant_str"></a>

#### `IMPLANT_STR` **(TSL)**

(2): Implant Str
<a id="implant_end"></a>

#### `IMPLANT_END` **(TSL)**

(3): Implant End
<a id="implant_agi"></a>

#### `IMPLANT_AGI` **(TSL)**

(4): Implant Agi
<a id="forfeit_no_force_powers"></a>

#### `FORFEIT_NO_FORCE_POWERS` **(TSL)**

(1): Forfeit No Force Powers
<a id="forfeit_no_items"></a>

#### `FORFEIT_NO_ITEMS` **(TSL)**

(2): Forfeit No Items
<a id="forfeit_no_weapons"></a>

#### `FORFEIT_NO_WEAPONS` **(TSL)**

(4): Forfeit No Weapons
<a id="forfeit_dxun_sword_only"></a>

#### `FORFEIT_DXUN_SWORD_ONLY` **(TSL)**

(8): Forfeit Dxun Sword Only
<a id="forfeit_no_armor"></a>

#### `FORFEIT_NO_ARMOR` **(TSL)**

(16): Forfeit No Armor
<a id="forfeit_no_ranged"></a>

#### `FORFEIT_NO_RANGED` **(TSL)**

(32): Forfeit No Ranged
<a id="forfeit_no_lightsaber"></a>

#### `FORFEIT_NO_LIGHTSABER` **(TSL)**

(64): Forfeit No Lightsaber
<a id="forfeit_no_item_but_shield"></a>

#### `FORFEIT_NO_ITEM_BUT_SHIELD` **(TSL)**

(128): Forfeit No Item But Shield

## Cross-References

- **[NCS File Format](NCS-File-Format.md)**: Compiled bytecode format that NSS compiles to
- **[GFF File Format](GFF-File-Format.md)**: Scripts are stored in GFF files (UTC, UTD, etc.)
- **[KEY File Format](KEY-File-Format.md)**: nwscript.nss is stored in chitin.key
