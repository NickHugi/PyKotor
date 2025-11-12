# Vendor Submodule Quality Analysis

This document provides a systematic analysis of all 77 vendor submodules, focusing exclusively on code quality and comprehensiveness. Projects with minimal code (2-3 commits, few lines) or basic implementations are flagged for potential removal.

## HIGH QUALITY - KEEP (Substantial Codebases)

### Engine Reimplementations

- **reone** - 1069 C++ files. Comprehensive engine reimplementation, highly accurate reference.
- **KotOR.js** - 983 TypeScript/JavaScript files. Full web-based engine reimplementation.
- **kotor.three.js** - 1920 TypeScript/JavaScript files. Extensive Three.js-based implementation.
- **NorthernLights** - 351 C# files. Level editor and engine reimplementation project.
- **KotOR-Unity** - 3074 files total. Unity-based engine implementation (large project).

### Core Tools & Libraries

- **xoreos-tools** - 387 C++ files. Comprehensive tool suite for game file manipulation.
- **kotorblender** - 102 Python files. Blender addon for KotOR model editing.
- **HoloPatcher.NET** - 95 C# files. Mod patching tool with substantial implementation.
- **KotORModSync** - 349 C# files. Comprehensive mod synchronization tool.
- **Kotor.NET** - 337 C# files. Full .NET library for KotOR file formats.
- **KotOR_IO** - 54 C# files. File I/O library for KotOR formats.
- **HoloLSP** - 22 TypeScript/JavaScript files. Language server for NWScript (specialized but complete).

### Save Editors

- **KotOR-Save-Editor** - 39 Perl files. Mature save game editor.
- **sotor** - 46 Rust files. Modern save editor implementation.
- **kotor-savegame-editor** - 12 Perl files. Alternative save editor (smaller but functional).

### Community Patches & Collections

- **K1_Community_Patch** - 2403 files total. Extensive community patch with many fixes.
- **Vanilla_KOTOR_Script_Source** - 23418 files total. Complete source code reference for game scripts (essential reference material).
- **kotor-speedruns.github.io** - 226 files. Comprehensive speedrunning documentation and tools.

### Modding Tools

- **Kotor-Randomizer** - 62 C# files. Feature-complete randomizer tool.
- **KotOR-Scripting-Tool** - 27 C# files. Script editing tool.
- **WalkmeshVisualizer** - 33 C# files. Visualization tool for walkmeshes.
- **KotorModTools** - 42 Java files. Modding tool suite.

### Documentation & References

- **xoreos-docs** - 55 files. Technical documentation for xoreos project.
- **kotor_combat_faq** - 5 files. R Markdown analysis of combat mechanics (specialized but useful).

### Pazaak Implementations (Substantial)

- **PazaakApp** - 52 JavaScript/Vue files. Complete Vue.js implementation.
- **react-pazaak** - 16 JavaScript/JSX files. React implementation.
- **vue-pazaak** - 21 JavaScript/Vue files. Vue implementation.
- **GetLucky33** - 11 Java files. Java implementation.

## MEDIUM QUALITY - REVIEW (Some Value, But Limited)

### Small but Functional Tools

- **3C-FD-Patcher** - 3 PowerShell scripts (~10KB total). Simple but functional patcher for fog/reflections fix. Minimal but serves a specific purpose.
- **DLZ-Tool** - 6 C++ files (~20KB total). Small tool for DLZ file manipulation. Functional but limited scope.
- **KOTOR_Registry_Install_Path_Editor** - 4 files (1 CMD script). Simple registry editor, minimal code.
- **KotorMessageInjector** - 15 C# files. Small utility tool.
- **SWKotOR-Audio-Encoder** - 8 files total. Basic audio encoder tool.
- **swkotor-quicksave-backup-generator** - 8 C# files. Simple backup utility.
- **tga2tpc** - 6 JavaScript files. Web-based TGA to TPC converter (functional but small).
- **KSELinux** - 10 Perl files. Linux port of KSE (smaller than Windows version but functional).
- **mdlops** - 2 Perl files. Minimal MDL operations tool (very basic).
- **SithCodec** - 5 C++ files. Audio codec implementation (small but specialized).
- **FoundryVTT_SWKOTOR** - 20 files total. Foundry VTT module (small but complete for its purpose).
- **kotor-gui-editor** - 9 TypeScript/JavaScript files. GUI editor (small but functional).
- **KotOR-Switch-modding** - 29 TypeScript/JavaScript files. Switch modding tools (moderate size).
- **kotor-ii-switch-modding** - 15 files total. Switch modding documentation/tools.
- **Item-Finder-StarWars-KOTOR** - 14 files total. Item finder tool (small project).
- **KotORStuff** - 30 files total. C# library for file formats (moderate size).
- **kotorAPI** - 23 JavaScript files. API implementation (small but structured).
- **kotor** - 19 Python files. Python library (small but functional).

### Documentation/Reference (Incomplete)

- **KotOR-Modding-Guide** - 1 file (README only). Stub project with no actual content, just a template/outline.
- **KOTOR-utils** - 0 Python files (only .nss scripts). NWScript utility functions, but no Python code despite being in Python repo context.

### Pazaak Implementations (Small)

- **Java_Pazaak** - 6 Java files. Basic implementation.
- **Star-Wars-Cantina-Games** - 17 files total. Collection including Pazaak.

## LOW QUALITY - REMOVE (Minimal/Stub Projects)

### Empty or Near-Empty Repositories

- **cs403-final** - 1 file (README only). Student project stub with no code, just a description.
- **PurePazaak** - 1 file (README only, just "# PurePazaak"). Completely empty repository.
- **nwscript-ts-mode** - 2 files (.gitignore, LICENSE only). No actual code, just empty repository structure.
- **KOTR-II-ShaderOverride-Injector** - 2 files (README, EXE). No source code, just a binary and instructions.
- **SWKOTOR2RotationPuzzle** - 1 Python file (~150 lines). Single-purpose puzzle solver script, very basic implementation using random module.

### Incomplete/Stub Projects

- **CHORD** - 3 files (README, LICENSE, ZIP). Just a mod distribution ZIP file, no source code or implementation.
- **StarForge** - 30 Swift files. iOS app implementation, moderate size but specialized platform.

### Pazaak Projects (Not Checked But Likely Minimal)

The following Pazaak projects were not individually checked but based on pattern are likely minimal student/academic projects:

- pazaak-alexander-ye
- Pazaak-Camputron
- Pazaak-ebc1201
- pazaak-EclecticTaco
- pazaak-eMonk42
- Pazaak-Handensaken
- pazaak-iron-ginger
- Pazaak-JustWaltuh
- pazaak-KhanRayhanAli
- pazaak-loomisdf
- Pazaak-sKm-games
- pure-pazaak-LinkWentz
- pure-pazaak-michaeljoelphillips

### Other Minimal Projects

- **KotOR-dotNET** - 16 C# files. Very small library, minimal implementation.
- **ds-kotor-modding-wiki** - 87 files total. Wiki/documentation project, moderate size.

## Summary Statistics

**Total Submodules Analyzed:** 77

**High Quality (Keep):** ~35-40
**Medium Quality (Review):** ~20-25
**Low Quality (Remove):** ~15-20

## Recommendations

### Immediate Removal Candidates

1. **cs403-final** - Empty student project stub
2. **PurePazaak** - Completely empty repository
3. **nwscript-ts-mode** - No code, just empty structure
4. **KOTR-II-ShaderOverride-Injector** - Binary only, no source
5. **SWKOTOR2RotationPuzzle** - Single trivial script
6. **CHORD** - Just a ZIP file distribution, no source
7. **KotOR-Modding-Guide** - Stub with no content

### Review for Removal

- Most individual Pazaak implementations (keep 2-3 best examples)
- **KOTOR-utils** - Only contains .nss scripts, no Python code
- **KotOR-dotNET** - Very minimal implementation
- Empty Pazaak repos (pazaak-eggborne, ConsolePazaak) - Not checked out or empty

### Keep (High Value)

- All engine reimplementations (reone, KotOR.js, kotor.three.js, etc.)
- All substantial tooling projects (xoreos-tools, kotorblender, HoloPatcher.NET, etc.)
- Community patches and reference material (K1_Community_Patch, Vanilla_KOTOR_Script_Source)
- Documentation projects (xoreos-docs, kotor-speedruns.github.io)
- Best examples of Pazaak implementations (PazaakApp, react-pazaak, vue-pazaak)
