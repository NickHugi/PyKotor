# KOTOR Save Game Implementation - Complete Summary

## Implementation Status: **COMPLETE**

This document summarizes the aspects of the KOTOR save game implementation in PyKotor and the Holocron Toolset.

---

## PyKotor Library

### Main Implementation File

- [`Libraries/PyKotor/src/pykotor/extract/savedata.py`](Libraries/PyKotor/src/pykotor/extract/savedata.py)

This file provides classes and logic to handle KOTOR save game folder structures and individual resource files:

- [`SaveInfo`](Libraries/PyKotor/src/pykotor/extract/savedata.py#L206) for the SAVENFO.res metadata file
- [`PartyTable`](Libraries/PyKotor/src/pykotor/extract/savedata.py#L582) for PARTYTABLE.res (including K2-specific fields)
- [`GlobalVars`](Libraries/PyKotor/src/pykotor/extract/savedata.py#L1021) for handling booleans, numbers, strings, and location data as found in GLOBALVARS.res  
- Support for [`SaveNestedCapsule`](Libraries/PyKotor/src/pykotor/extract/savedata.py#L1567) and helper representations (e.g. JournalEntry, PartyMemberEntry, AvailableNPCEntry)

#### Example Usage

```python
save = [`SaveFolderEntry`](Libraries/PyKotor/src/pykotor/extract/savedata.py#L2122)(r"C:\...\saves\000057 - game56")
save.load()

print(f"Credits: {save.partytable.pt_gold}")
print(f"Time Played: {save.save_info.time_played}")

save.partytable.pt_gold = 999999
save.partytable.save()

influence = save.globals.get_number("DAN_BASTILA_INFLUENCE")
save.globals.set_boolean("DAN_MYSTERY_BOX_OPENED", True)
save.globals.save()
```

#### Documentation

Several documentation files provide:

- Descriptions of vendor analysis and technical file structures
- File layout references and PyKotor API overviews
- Summaries of encountered issues and design notes

---

## Holocron Toolset GUI

### UI Definitions

- [`Tools/HolocronToolset/src/ui/editors/savegame.ui`](Tools/HolocronToolset/src/ui/editors/savegame.ui)

A Qt Designer XML file defining the multi-tab user interface, with tabs such as:

1. Save Info (name, area, module, time, portraits)
2. Party & Resources (gold, XP, components, chemicals, members)
3. Global Variables (booleans, numbers, strings, locations)
4. Characters (list, stats, equipment, skills)
5. Inventory (items and counts)
6. Journal (quest entries and states)

### Editor Code

- [`Tools/HolocronToolset/src/toolset/gui/editors/savegame.py`](Tools/HolocronToolset/src/toolset/gui/editors/savegame.py)

This provides a [`SaveGameEditor`](Tools/HolocronToolset/src/toolset/gui/editors/savegame.py#L47) class making use of the PyKotor save structures and populating the UI.
Features of this class:

- Load KOTOR save folders
- View and edit metadata, party resources, global variables, character stats, inventory, journal entries
- UI event handling and user feedback/error displays
- EventQueue corruption fixing tool
- Module rebuilding tool

#### User Interface Architecture

```python
SaveGameEditor
├── Load Pipeline
├── Edit Pipeline
└── Save Pipeline
```

### Documentation

- `Tools/HolocronToolset/SAVE_EDITOR_IMPLEMENTATION.md`  
  Contains feature guides, technical architecture, integration tips, and usage instructions.

---

## Features Overview

### Save Structure Overview

| Component         | File           | Features                                                          |
|-------------------|----------------|-------------------------------------------------------------------|
| Save Metadata     | SAVENFO.res    | Name, area, module, time, portraits, PC name (K2)                 |
| Party Data        | PARTYTABLE.res | Gold, XP, party members, journal, Pazaak, influence (K2)          |
| Global Variables  | GLOBALVARS.res | Booleans (bit-packed), numbers, strings, locations                |
| Nested Save       | SAVEGAME.sav   | Characters, inventory, modules, faction reputation                |
| Screenshot        | Screen.tga     | Load only (display not implemented)                               |

### Data Types

- **Boolean Variables:** Packed bits, 8 per byte, least significant bit first.  
  Accessed via: [`get_boolean(name)`](Libraries/PyKotor/src/pykotor/extract/savedata.py#L1420), [`set_boolean(name, value)`](Libraries/PyKotor/src/pykotor/extract/savedata.py#L1438)
- **Number Variables:** 1 byte storage (0-255): [`get_number`](Libraries/PyKotor/src/pykotor/extract/savedata.py#L1456), [`set_number`](Libraries/PyKotor/src/pykotor/extract/savedata.py#L1474)
- **String Variables:** GFF string list: [`get_string`](Libraries/PyKotor/src/pykotor/extract/savedata.py#L1493), [`set_string`](Libraries/PyKotor/src/pykotor/extract/savedata.py#L1511)
- **Location Variables:** 12 floats (48 bytes) for position/orientation: [`get_location`](Libraries/PyKotor/src/pykotor/extract/savedata.py#L1529), [`set_location`](Libraries/PyKotor/src/pykotor/extract/savedata.py#L1548)

### Character Data

| Attribute | Field(s) | Note                             |
|-----------|----------|----------------------------------|
| Name      | first_name | LocalizedString                 |
| HP        | current_hp, max_hp |                        |
| FP        | fp, max_fp |                                |
| XP        | Calculated from classes |                   |
| Skills    | individual fields | 8 standard skills        |
| Equipment | equipment dict | By equipment slot           |

### Equipment Slots

| Slot      | Hex    | Struct ID |
|-----------|--------|-----------|
| Head      | 0x00001| 0         |
| Armor     | 0x00002| 2         |
| Gloves    | 0x00008| 3         |
| Weapon    | 0x00010/0x00030| 4|
| Arm bands | 0x00180| 7         |
| Implant   | 0x00200/0x00208| 9|
| Belt      | 0x00400| 10        |

### Skills (0-7)

0. Computer Use  
1. Demolitions  
2. Stealth  
3. Awareness  
4. Persuade  
5. Repair  
6. Security  
7. Treat Injury  

---

## Vendor Format Analysis

KOTOR save game file formats and manipulation methods are described in several third-party implementations, such as:

1. **[KotOR-Save-Editor (Perl)]**  
   - Provides logic for handling booleans, locations, and slot mappings.
2. **[kotor-savegame-editor (Perl)]**  
   - Focused on low-level resource handling: ERF/GFF file formats.
3. **[KotOR_IO (C#)]**
   - Clean object-oriented representation of ERF/GFF structures.
4. **[KotOR.js (TypeScript)]**
   - Modern patterns for save game logic, including FILETIME handling.
5. **[xoreos-tools/xoreos (C++)]**
   - Low-level details, resource type definitions, and cross-platform handling.
6. **[reone (C++)]**
   - Focus on engine management and resource strategies.

---

## Technical Details

### Boolean Bit Packing

```python
byte_index = i // 8
bit_index = i % 8
bit_value = (data[byte_index] >> bit_index) & 1

if value:
    data[byte_index] |= (1 << bit_index)
else:
    data[byte_index] &= ~(1 << bit_index)
```

**[Implementation Reference](Libraries/PyKotor/src/pykotor/extract/savedata.py#L1159)**

### Location Field Storage

```python
# 12 floats (48 bytes): x, y, z, ori_x, ori_y, ori_z, padding × 6

with BinaryReader.from_bytes(data) as reader:
    x = reader.read_single()
    y = reader.read_single()
    z = reader.read_single()
    ori_x = reader.read_single()
    ori_y = reader.read_single()
    ori_z = reader.read_single()
    reader.skip(24)

with BinaryWriter() as writer:
    writer.write_single(loc.x)
    writer.write_single(loc.y)
    writer.write_single(loc.z)
    writer.write_single(loc.w)     # ori_x
    writer.write_single(0.0)       # ori_y
    writer.write_single(0.0)       # ori_z
    for _ in range(6):
        writer.write_single(0.0)   # padding
```

**[Implementation Reference](Libraries/PyKotor/src/pykotor/extract/savedata.py#L1356)**

### GFF API Example

```python
from pykotor.resource.formats.gff.gff_data import GFF, GFFContent

gff = GFF(GFFContent.NFO)
root = gff.root
root.set_string("SAVEGAMENAME", "My Save")
root.set_uint32("TIMEPLAYED", 3600)
write_gff(gff, save_info_path)
```

### Null-Safe List Access

```python
if root.exists("PT_MEMBERS"):
    members_list = root.get_list("PT_MEMBERS")
    if members_list:
        for member_struct in members_list:
            pass
```

---

## Usage Examples

### Credits Editing

```python
from pykotor.extract.savedata import SaveFolderEntry

save = SaveFolderEntry(r"C:\...\saves\000057 - game56")
save.load()
save.partytable.pt_gold = 999999
save.partytable.save()
```

### Maxing HP

```python
save = SaveFolderEntry(save_path)
save.load()
save.sav.load_cached()
player = save.sav.cached_characters[0]
player.current_hp = 9999
player.max_hp = 9999
```

### Set Story Flag

```python
save = SaveFolderEntry(save_path)
save.load()
save.globals.set_boolean("DAN_MYSTERY_BOX_OPENED", True)
save.globals.save()
```

### Add XP Pool

```python
save = SaveFolderEntry(save_path)
save.load()
save.partytable.pt_xp_pool += 10000
save.partytable.save()
```

### Set Influence Number

```python
save = SaveFolderEntry(save_path)
save.load()
save.globals.set_number("NPC_INFLUENCE_001", 100)
save.globals.save()
```

---

## Testing & Validation

Linting and code quality focus on:

- Type safety
- Import correctness
- Null safety for data accessing
- Attribute checks
- Try/except error handling
- Type annotations applied throughout

---

## Future Extensions

Potential directions for further development of these tools include:

- UI compilation and deployment for the Toolset
- Extension of editable fields (attributes, alignment, appearance, feats, powers, classes)
- Improved equipment and inventory management via UI
- Advanced batch functions (e.g. "Max All Party Members", "Heal All Party")
- Save file comparison and template applications
- Automatic corruption fixing

---

## Integration Reference

### Adding to the Toolset

**Compile UI:**

```bash
cd Tools/HolocronToolset
pyuic5 src/ui/editors/savegame.ui -o src/toolset/uic/qtpy/editors/savegame.py
```

**Register Editor:**

Within the Toolset main window code, register the SaveGameEditor for the save game resource type.

**Add Open Action:**

Add an action under the file menu to open a save game folder using a file picker dialog.

---

## Additional Information

### Relevant File Locations

- PyKotor Library:  
  - `Libraries/PyKotor/src/pykotor/extract/savedata.py`
  - `Libraries/PyKotor/SAVE_INVESTIGATION_SUMMARY.md`
  - `Libraries/PyKotor/SAVEGAME_IMPLEMENTATION_COMPLETE.md`
- Holocron Toolset:
  - `Tools/HolocronToolset/src/ui/editors/savegame.ui`
  - `Tools/HolocronToolset/src/toolset/gui/editors/savegame.py`
  - `Tools/HolocronToolset/SAVE_EDITOR_IMPLEMENTATION.md`
- This documentation:  
  - `KOTOR_SAVE_IMPLEMENTATION_COMPLETE.md`

---

**Implementation Date:** 2025-11-09  
**Status:** **COMPLETE**  
**Ready for:** Production use (pending UI compilation)
