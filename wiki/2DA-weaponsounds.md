# weaponsounds.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines sound effects for weapon attacks based on base item type. The engine uses this file to play appropriate weapon sounds during combat.

**Row Index**: Base Item ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Base item label |
| Additional columns | ResRef | Sound effect ResRefs for different attack types |

**References**:

- [`vendor/KotOR.js/src/module/ModuleCreature.ts:1819-1822`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleCreature.ts#L1819-L1822) - Weapon sound lookup from 2DA

---

