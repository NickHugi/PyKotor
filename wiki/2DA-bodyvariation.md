# bodyvariation.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines body variation types for items and creatures. The engine uses this file to determine body variation assignments, which affect model and texture selection for equipped items.

**Row Index**: Body Variation ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Body variation label |
| Additional columns | Various | Body variation properties |

**References**:

- [`vendor/reone/src/libs/resource/parser/gff/uti.cpp:45`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/gff/uti.cpp#L45) - GFF field parsing: "BodyVariation" from UTI (item) templates
- [`vendor/reone/src/libs/resource/parser/gff/utc.cpp:87`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/gff/utc.cpp#L87) - GFF field parsing: "BodyVariation" from UTC (creature) templates
- [`vendor/reone/src/libs/game/object/item.cpp:124,140,155`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/item.cpp#L124) - Body variation usage in item object
- [`vendor/KotOR.js/src/module/ModuleItem.ts:136`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleItem.ts#L136) - Body variation method in item module
- [`vendor/KotOR.js/src/module/ModuleCreature.ts:82,3908,4798`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleCreature.ts#L82) - Body variation field handling in creature module
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:539`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L539) - GFF field mapping: "BodyVariation" -> bodyvariation.2da

---

