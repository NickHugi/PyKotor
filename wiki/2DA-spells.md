# spells.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines all Force powers (and legacy spell entries) in KotOR, including their costs, targeting modes, visual effects, and descriptions. The engine uses this file to determine Force power availability, casting requirements, and effects. Note: KotOR uses Force powers rather than traditional D&D spells, though the file structure is inherited from the Aurora engine (originally designed for Neverwinter Nights).

**Row Index**: Spell ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Spell label |
| `name` | StrRef | String reference for spell name |
| `school` | Integer | Spell school identifier |
| `range` | Integer | Spell range type |
| `vs` | Integer | Versus type (self, touch, etc.) |
| `metamagic` | Integer | Metamagic flags |
| `targettype` | Integer | Target type flags |
| `impactscript` | ResRef (optional) | Impact script ResRef |
| `innate` | Integer | Innate Force power level (0 = not available) |
| `conjtime` | Float | Casting/conjuration time |
| `conjtimevfx` | Integer (optional) | Casting time visual effect |
| `conjheadvfx` | Integer (optional) | Casting head visual effect |
| `conjhandvfx` | Integer (optional) | Casting hand visual effect |
| `conjgrndvfx` | Integer (optional) | Casting ground visual effect |
| `conjcastvfx` | Integer (optional) | Casting visual effect |
| `conjimpactscript` | ResRef (optional) | Conjuration impact script |
| `conjduration` | Float | Conjuration duration |
| `conjrange` | Integer | Conjuration range |
| `conjca` | Integer | Conjuration casting animation |
| `conjca2` through `conjca50` | Integer (optional) | Additional casting animations (numbered 2-50) |
| `hostilesetting` | Integer | Hostile setting flags |
| `featid` | Integer (optional) | Associated feat ID |
| `counter1` | Integer (optional) | Counter spell ID 1 |
| `counter2` | Integer (optional) | Counter spell ID 2 |
| `counter3` | Integer (optional) | Counter spell ID 3 |
| `projectile` | ResRef (optional) | Projectile model ResRef |
| `projectilesound` | ResRef (optional) | Projectile sound ResRef |
| `projectiletype` | Integer | Projectile type identifier |
| `projectileorient` | Integer | Projectile orientation |
| `projectilepath` | Integer | Projectile path type |
| `projectilehoming` | Boolean | Whether projectile homes on target |
| `projectilemodel` | ResRef (optional) | Projectile 3D model ResRef |
| `projectilemodel2` through `projectilemodel50` | ResRef (optional) | Additional projectile models (numbered 2-50) |
| `icon` | ResRef | Spell icon ResRef |
| `icon2` through `icon50` | ResRef (optional) | Additional icons (numbered 2-50) |
| `description` | StrRef | Spell description string reference |
| `altmessage` | StrRef (optional) | Alternative message string reference |
| `usewhencast` | Integer | Use when cast flags |
| `blood` | Boolean | Whether spell causes blood effects |
| `concentration` | Integer | Concentration check DC |
| `immunitytype` | Integer | Immunity type identifier |
| `immunitytype2` through `immunitytype50` | Integer (optional) | Additional immunity types (numbered 2-50) |
| `immunityitem` | Integer | Immunity item type |
| `immunityitem2` through `immunityitem50` | Integer (optional) | Additional immunity items (numbered 2-50) |

**Column Details** (from reone implementation):

The following columns are accessed by the reone engine:

- `name`: String reference for spell name
- `spelldesc`: String reference for spell description (note: column name is `spelldesc`, not `description`)
- `iconresref`: Icon ResRef (note: column name is `iconresref`, not `icon`)
- `pips`: Spell pips/ranks (hex integer)
- `conjtime`: Conjuration/casting time
- `casttime`: Cast time
- `catchtime`: Catch time
- `conjanim`: Conjuration animation type (e.g., "throw", "up")
- `hostilesetting`: Hostile setting flags
- `projectile`: Projectile ResRef
- `projectileHook`: Projectile hook point
- `projectileOrigin`: Projectile origin point
- `projectileTarget`: Projectile target point
- `projectileCurve`: Projectile curve type
- `projmodel`: Projectile model ResRef
- `range`: Spell range
- `impactscript`: Impact script ResRef
- `casthandvisual`: Cast hand visual effect

**Note**: The `spells.2da` file contains many optional columns for projectile models, icons, and immunity types (numbered 1-50). These are used for spell variations and visual effects.

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:149`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L149) - StrRef column definitions for spells.2da (K1: name, spelldesc)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:327`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L327) - StrRef column definitions for spells.2da (K2: name, spelldesc)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:239`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L239) - Script ResRef column definition for spells.2da (impactscript)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:432`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L432) - Script ResRef column definition for spells.2da (K2: impactscript)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:465`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L465) - TwoDARegistry.POWERS constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:558-560`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L558-L560) - GFF field mapping: "Subtype", "SpellId", and "Spell" -> spells.2da
- [`Libraries/PyKotor/src/pykotor/common/scriptdefs.py:9380-9381`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/common/scriptdefs.py#L9380-L9381) - GetLastForcePowerUsed function comment referencing Spells.2da
- [`Libraries/PyKotor/src/pykotor/common/scriptlib.py:5676`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/common/scriptlib.py#L5676) - Debug print referencing Spells.2DA ID

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:64`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L64) - HTInstallation.TwoDA_POWERS constant

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/d20/spells.cpp:32-48`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/d20/spells.cpp#L32-L48) - Spell loading from 2DA with column access
- [`vendor/KotOR.js/src/talents/TalentSpell.ts:16-44`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/talents/TalentSpell.ts#L16-L44) - Spell structure with additional columns
- [`vendor/KotOR.js/src/talents/TalentSpell.ts:42-53`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/talents/TalentSpell.ts#L42-L53) - Spell loading from 2DA

---

