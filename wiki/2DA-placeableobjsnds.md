# placeableobjsnds.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines sound effects for placeable objects based on sound appearance type. The engine uses this file to play appropriate sounds when interacting with placeables.

**Row Index**: Sound Appearance Type ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Sound appearance type label |
| Additional columns | ResRef | Sound effect ResRefs for different interaction types |

**References**:

- [`vendor/KotOR.js/src/module/ModulePlaceable.ts:387-389`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModulePlaceable.ts#L387-L389) - Placeable sound lookup from 2DA
- [`vendor/KotOR.js/src/module/ModuleDoor.ts:239-241`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleDoor.ts#L239-L241) - Door sound lookup from 2DA

---

