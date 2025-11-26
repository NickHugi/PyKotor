# combatanimations.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines combat-specific animation properties and mappings. The engine uses this file to determine which animations to play during combat actions.

**Row Index**: Combat Animation ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Combat animation label |
| Additional columns | Various | Combat animation properties |

**References**:

- [`vendor/KotOR.js/src/module/ModuleCreature.ts:1482`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleCreature.ts#L1482) - Combat animation lookup from 2DA

---

