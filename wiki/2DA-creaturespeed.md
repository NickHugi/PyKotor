# creaturespeed.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines movement speed rates for creatures based on walk rate ID. The engine uses this file to determine walking and running speeds.

**Row Index**: Walk Rate ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Walk rate label |
| `walkrate` | Float | Walking speed rate |
| `runrate` | Float | Running speed rate |

**References**:

- [`vendor/KotOR.js/src/module/ModuleCreature.ts:2875-2887`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleCreature.ts#L2875-L2887) - Creature speed lookup from 2DA

---

