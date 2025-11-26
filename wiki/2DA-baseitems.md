# baseitems.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines base item types that form the foundation for all items in the game. Each row represents a base item type (weapon, armor, shield, etc.) with properties like damage dice, weapon categories, equipment slots, and item flags. The engine uses this file to determine item behavior, combat statistics, and equipment compatibility.

**Row Index**: Base item ID (integer)

**Column Structure** (columns accessed by reone):

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Item type label |
| `name` | StrRef | String reference for item type name |
| `basecost` | Integer | Base gold cost |
| `stacking` | Integer | Stack size limit |
| `invslotwidth` | Integer | Inventory slot width |
| `invslotheight` | Integer | Inventory slot height |
| `canrotateicon` | Boolean | Whether icon can be rotated in inventory |
| `itemclass` | Integer | Item class identifier |
| `weapontype` | Integer | Weapon type (if weapon) |
| `weaponsize` | Integer | Weapon size category |
| `weaponwield` | Integer | Wield type (one-handed, two-handed, etc.) |
| `damagedice` | Integer | Damage dice count |
| `damagedie` | Integer | Damage die size |
| `damagebonus` | Integer | Base damage bonus |
| `damagetype` | Integer | Damage type flags |
| `weaponmattype` | Integer | Weapon material type |
| `weaponsound` | Integer | Weapon sound type |
| `ammunitiontype` | Integer | Ammunition type required |
| `rangedweapon` | Boolean | Whether item is a ranged weapon |
| `maxattackrange` | Integer | Maximum attack range |
| `preferredattackrange` | Integer | Preferred attack range |
| `attackmod` | Integer | Attack modifier |
| `damagebonusfeat` | Integer | Feat ID for damage bonus |
| `weaponfocustype` | Integer | Weapon focus type |
| `weaponfocusfeat` | Integer | Weapon focus feat ID |
| `description` | StrRef | String reference for item description |
| `icon` | ResRef | Icon image ResRef |
| `equipableslots` | Integer | Equipment slot flags |
| `model1` through `model6` | ResRef (optional) | 3D model ResRefs for different variations |
| `partenvmap` | ResRef (optional) | Partial environment map texture |
| `defaultmodel` | ResRef (optional) | Default model ResRef |
| `defaulticon` | ResRef (optional) | Default icon ResRef |
| `container` | Boolean | Whether item is a container |
| `weapon` | Boolean | Whether item is a weapon |
| `armor` | Boolean | Whether item is armor |
| `chargesstarting` | Integer | Starting charges (for usable items) |
| `costpercharge` | Integer | Cost per charge to recharge |
| `addcost` | Integer | Additional cost modifier |
| `stolen` | Boolean | Whether item is marked as stolen |
| `minlevel` | Integer | Minimum level requirement |
| `stacking` | Integer | Maximum stack size |
| `reqfeat0` through `reqfeat3` | Integer (optional) | Required feat IDs |
| `reqfeatcount0` through `reqfeatcount3` | Integer (optional) | Required feat counts |
| `reqclass` | Integer (optional) | Required class ID |
| `reqrace` | Integer (optional) | Required race ID |
| `reqalign` | Integer (optional) | Required alignment |
| `reqdeity` | Integer (optional) | Required deity ID |
| `reqstr` | Integer (optional) | Required strength |
| `reqdex` | Integer (optional) | Required dexterity |
| `reqint` | Integer (optional) | Required intelligence |
| `reqwis` | Integer (optional) | Required wisdom |
| `reqcon` | Integer (optional) | Required constitution |
| `reqcha` | Integer (optional) | Required charisma |

**Column Details** (from reone implementation):

The following columns are accessed by the reone engine:

- `maxattackrange`: Maximum attack range for ranged weapons
- `crithitmult`: Critical hit multiplier
- `critthreat`: Critical threat range
- `damageflags`: Damage type flags
- `dietoroll`: Damage die size
- `equipableslots`: Equipment slot flags (hex integer)
- `itemclass`: Item class identifier (string)
- `numdice`: Number of damage dice
- `weapontype`: Weapon type identifier
- `weaponwield`: Weapon wield type (one-handed, two-handed, etc.)
- `bodyvar`: Body variation for armor
- `ammunitiontype`: Ammunition type ID (used to look up `ammunitiontypes.2da`)

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:169`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L169) - Model ResRef column definition for baseitems.2da (defaultmodel)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:187`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L187) - Sound ResRef column definitions for baseitems.2da (powerupsnd, powerdownsnd, poweredsnd)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:215`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L215) - Texture ResRef column definition for baseitems.2da (defaulticon)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:225`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L225) - Item ResRef column definitions for baseitems.2da (itemclass, baseitemstatref)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:466`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L466) - TwoDARegistry.BASEITEMS constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:537`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L537) - GFF field mapping: "BaseItem" and "ModelVariation" -> baseitems.2da

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:65`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L65) - HTInstallation.TwoDA_BASEITEMS constant
- [`Tools/HolocronToolset/src/toolset/data/installation.py:594-607`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L594-L607) - get_item_icon_from_uti method using baseitems.2da for item class lookup
- [`Tools/HolocronToolset/src/toolset/data/installation.py:609-620`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L609-L620) - get_item_base_name method using baseitems.2da
- [`Tools/HolocronToolset/src/toolset/data/installation.py:630-643`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L630-L643) - get_item_icon_path method using baseitems.2da for item class and icon path
- [`Tools/HolocronToolset/src/toolset/gui/editors/uti.py:107-117`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/uti.py#L107-L117) - baseitems.2da loading and usage in UTI (item) editor for base item selection
- [`Tools/HolocronToolset/src/toolset/gui/dialogs/inventory.py:668-704`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/dialogs/inventory.py#L668-L704) - baseitems.2da usage for equipment slot and droid/human flag lookup

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/object/item.cpp:126-136`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/item.cpp#L126-L136) - Base item column access
- [`vendor/reone/src/libs/game/object/item.cpp:160-171`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/item.cpp#L160-L171) - Ammunition type lookup from baseitems.2da

---

