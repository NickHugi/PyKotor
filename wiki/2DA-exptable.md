# exptable.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines experience point requirements for each character level. The engine uses this file to determine when a character levels up based on accumulated experience.

**Row Index**: Level (integer, typically 1-20)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Level label |
| Additional columns | Integer | Experience point requirements for leveling up |

**References**:

- [`vendor/KotOR.js/src/module/ModuleCreature.ts:2926-2941`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleCreature.ts#L2926-L2941) - Experience table lookup from 2DA

---

