# animations.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines animation names and properties for creatures and objects. The engine uses this file to map animation IDs to animation names for playback.

**Row Index**: Animation ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Animation label |
| `name` | String | Animation name (used to look up animation in model) |

**References**:

- [`vendor/KotOR.js/src/module/ModuleCreature.ts:1474-1482`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleCreature.ts#L1474-L1482) - Animation lookup from 2DA
- [`vendor/KotOR.js/src/module/ModulePlaceable.ts:1063-1103`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModulePlaceable.ts#L1063-L1103) - Placeable animation lookup from 2DA
- [`vendor/KotOR.js/src/module/ModuleDoor.ts:1343-1365`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleDoor.ts#L1343-L1365) - Door animation lookup from 2DA

---

