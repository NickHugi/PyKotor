# xptable.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines experience point reward calculations for defeating enemies. The engine uses this file to calculate how much XP to grant when a creature is defeated, based on the defeated creature's level and properties.

**Row Index**: XP Table Entry ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | XP table entry label |
| Additional columns | Various | XP calculation parameters |

**Note**: This is different from `exptable.2da` which defines XP requirements for leveling up. `xptable.2da` defines XP rewards for defeating enemies.

**References**:

- [`vendor/KotOR.js/src/engine/rules/SWRuleSet.ts:89-95`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/engine/rules/SWRuleSet.ts#L89-L95) - XP table initialization from 2DA

---

