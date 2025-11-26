# acbonus.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines armor class bonus calculations. The engine uses this file to determine AC bonus values for different scenarios and calculations.

**Row Index**: AC Bonus Entry ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | AC bonus entry label |
| Additional columns | Various | AC bonus calculation parameters |

**References**:

- [`vendor/KotOR.js/src/combat/CreatureClass.ts:302-304`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/combat/CreatureClass.ts#L302-L304) - AC bonus loading from 2DA

---

