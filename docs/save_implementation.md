# KotOR Save Game Reference

PyKotor ships a full helper stack for reading and writing Knights of the Old Republic save folders.  
All runtime code lives in [`Libraries/PyKotor/src/pykotor/extract/savedata.py`](Libraries/PyKotor/src/pykotor/extract/savedata.py) and works with both K1 and TSL.

Use this guide as the public reference for the save API. It replaces the old status reports.

---

## Save Folder Layout

Each save lives in its own directory (for example `000057 - game56`, `AUTOSAVE`, or `QUICKSAVE`).  
PyKotor expects the files below and leaves any additional content untouched.

| File | Purpose | Notes |
| --- | --- | --- |
| `SAVENFO.res` | Menu metadata (name, area, portraits, timestamp) | Required |
| `PARTYTABLE.res` | Party composition, credits, quest journal, K2 influence, etc. | Required |
| `GLOBALVARS.res` | Script variables (booleans, numbers, strings, locations) | Required |
| `SAVEGAME.sav` | Nested ERF containing cached modules, inventory, AVAILNPC UTCs, reputation data | Required |
| `Screen.tga` | Screenshot shown in the save UI | Optional – preserved if present |

None of the helpers create backups automatically; copy the folder somewhere safe before editing.

---

## High-Level Python API

### [`SaveFolderEntry`](Libraries/PyKotor/src/pykotor/extract/savedata.py#L2122)

*Attributes*

- `save_info`: [`SaveInfo`](Libraries/PyKotor/src/pykotor/extract/savedata.py#L206)
- `partytable`: [`PartyTable`](Libraries/PyKotor/src/pykotor/extract/savedata.py#L582)
- `globals`: [`GlobalVars`](Libraries/PyKotor/src/pykotor/extract/savedata.py#L1021)
- `sav`: [`SaveNestedCapsule`](Libraries/PyKotor/src/pykotor/extract/savedata.py#L1567)
- `screenshot`: `bytes | None` (loaded if `Screen.tga` exists)

*Lifecycle*

- `load()` loads `SAVEGAME.sav`, `PARTYTABLE.res`, `SAVENFO.res`, and `GLOBALVARS.res` (in that order) and infers whether the save belongs to K1 or K2 by inspecting party data.
- `save()` writes each component back to disk and repacks `SAVEGAME.sav` using the cached payloads from `SaveNestedCapsule`. The implementation prints progress messages to stdout; silence or redirect those if you are building a UI.

### [`SaveInfo`](Libraries/PyKotor/src/pykotor/extract/savedata.py#L206)

Wraps the `SAVENFO.res` GFF file. Normal fields are exposed as attributes such as `savegame_name`, `area_name`, `last_module`, `time_played`, portrait `ResRef`s, and `pc_name` (TSL only).  
`load()` reads the GFF; `save()` rebuilds the GFF in memory with `write_gff` and overwrites the original file.

### [`PartyTable`](Libraries/PyKotor/src/pykotor/extract/savedata.py#L582)

Represents `PARTYTABLE.res`. Key attributes include:

- `pt_members`: list of `PartyMemberEntry` storing party leader flags and the member index. `pt_num_members` is a property that always mirrors `len(pt_members)`.
- `pt_avail_npcs`: availability and selection flags for each recruitable companion.
- `pt_gold`, `pt_xp_pool`, `pt_cheat_used`, `time_played`.
- `jnl_entries`: quest journal entries (`plot_id`, `state`, `date`, `time`).
- `pt_influence`, `pt_item_componen`, `pt_item_chemical`, `pt_pcname`: TSL specific fields that only populate when present in the save.
- `additional_fields`: dict of untouched GFF fields (label → `(field_type, value)`), useful when new fields appear in future game versions.

`load()` reconstructs those attributes from the GFF. `save()` writes a fresh GFF while preserving anything stored in `additional_fields`.

### [`GlobalVars`](Libraries/PyKotor/src/pykotor/extract/savedata.py#L1021)

Stores script globals that NWScript exposes through `GetGlobal*` and `SetGlobal*`.  
Attributes are lists of `(name, value)` tuples:

- `global_bools`: boolean flags.
- `global_numbers`: 0–255 integer values.
- `global_strings`: arbitrary strings.
- `global_locs`: locations, stored as `(name, Vector4)` where `(x, y, z)` represents the world position and `.w` stores `cos(yaw)`. The binary format also stores `sin(yaw)` and padding; the helper recomputes the sine when saving.

Convenience methods (`get_boolean`, `set_boolean`, `get_number`, `set_number`, `get_string`, `set_string`, `get_location`, `set_location`, `remove_*`, etc.) mutate the in-memory lists. Each helper updates the binary cache immediately so a single call to `save()` writes the updated `GLOBALVARS.res`.

### [`SaveNestedCapsule`](Libraries/PyKotor/src/pykotor/extract/savedata.py#L1567)

Represents the contents of `SAVEGAME.sav`. It keeps several caches:

- `resource_order` and `resource_data` preserve the original ERF byte layout.
- `cached_modules`: ERFs for each cached module (`*.sav`).
- `cached_characters`: parsed `UTC` data for `AVAILNPC#.utc` along with `cached_character_indices`.
- `inventory`: list of `UTI` objects, backed by `inventory_gff` for round‑trip writes.
- `repute`: parsed `REPUTE.fac`.
- `other_resources`: every remaining resource, stored verbatim.

Call `load()` (or `load_cached()`) before mutating anything.  
Call `save()` after edits to refresh `resource_data`; `SaveFolderEntry.save()` will then repack the ERF using `bytes_erf`.

Helpers such as `set_resource` and `remove_resource` let you inject custom payloads. When you replace a resource, the class eagerly updates the relevant cache so subsequent reads see the new data.

---

## Working with Data

### Boolean Packing

Booleans use the engine’s packed-bit format. The helper already inflates and collapses the byte array, but the formula is useful when you work with the binary buffer directly:

```python
byte_index = i // 8
bit_index = i % 8
mask = 1 << bit_index
```

### Numbers

Numbers occupy a single unsigned byte (0–255). Values outside that range are truncated by the game, so clamp them yourself before saving.

### Strings

String globals are stored as two GFF lists (`CatString` and `ValString`) that share indices. `GlobalVars` keeps them as tuples so you only have to modify the text.

### Locations

Each entry is 12 floats (48 bytes):

| Floats | Meaning |
| --- | --- |
| 0–2 | Position `(x, y, z)` |
| 3 | `cos(yaw)` (stored in the `Vector4.w` component) |
| 4 | `sin(yaw)` (recomputed when saving) |
| 5 | Reserved (`0.0` in retail saves) |
| 6–11 | Padding (`0.0`) |

Use `set_location(name, vector4)` to change a value. The helper rewrites the unused sine slot when exporting.

### Nested Resources

When you modify `self.sav.cached_modules` or `self.sav.cached_characters`, remember to call `self.sav.save()` (or let `SaveFolderEntry.save()` do it for you) so `resource_data` stays in sync.

---

## Common Tasks

### Load, Edit, Save

```python
from pathlib import Path
from pykotor.extract.savedata import SaveFolderEntry

save_path = Path(r"C:\KOTOR\saves\000057 - game56")
save = SaveFolderEntry(save_path)

# Load every component
save.load()

# Award 5,000 credits
save.partytable.pt_gold += 5000

# Mark a story flag
save.globals.set_boolean("DAN_MYSTERY_BOX_OPENED", True)

# Update a spawn location (face east)
from math import cos, sin, radians
heading = radians(90)
save.globals.set_location(
    "DAN_PLAYER_ENTRY",
    (0.0, 5.0, 0.0, cos(heading)),
)

# Persist every file back to disk
save.save()
```

### Update Influence in TSL

```python
save.load()

# Influence array order mirrors the companion index in PT_AVAIL_NPCS.
atton_slot = 0
if atton_slot < len(save.partytable.pt_influence):
    save.partytable.pt_influence[atton_slot] = 100

save.save()
```

### Replace a Cached Module

```python
from pykotor.resource.formats.erf.erf_auto import read_erf, bytes_erf
from pykotor.extract.savedata import SaveFolderEntry

save.load()

module_id = "ebo_m12aa"
identifier = save.sav.make_identifier(module_id, "sav")

patched_module = read_erf("patched_module.sav")
save.sav.cached_modules[identifier] = patched_module
save.sav.resource_data[identifier] = bytes_erf(patched_module)

save.save()
```

---

## Best Practices & Limitations

- **Back up first.** The helpers overwrite the existing files in place.
- **Call `save()` after mutations.** Component objects do not flush automatically.
- **Pazaak data is preserved but not interpreted.** `PartyTable` leaves the raw `GFFList` entries intact; you can copy them between saves but the library does not unpack the card structures.
- **Inventory editing requires valid `UTI` objects.** Use the constructors in `pykotor.resource.generics.uti` to build new items or clone ones already in the list.
- **K1 vs K2 detection** is based on party data and save info. If you inject TSL-only fields into a K1 save, set `save.sav.game = Game.K1` manually before calling `save()`.
- **External resources** (anything not explicitly decoded) remain byte-identical through round trips because `SaveNestedCapsule.resource_data` keeps the original payload unless you overwrite it.

---

## Related Documentation

- `mdl_format.md` – MDL/MDX format notes used by the same extraction layer.
- `walkmesh.md` – Module walkmesh documentation.
- Holocron Toolset documentation – GUI editing workflows powered by the same Python classes.

If you encounter a field that is not surfaced by these helpers, check `PartyTable.additional_fields` or `SaveNestedCapsule.other_resources`; both expose the raw data needed for custom tooling.
