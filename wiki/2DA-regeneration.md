# regeneration.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines regeneration rates for creatures in combat and non-combat states. The engine uses this file to determine how quickly creatures regenerate hit points and Force points.

**Row Index**: Regeneration State ID (integer, 0=combat, 1=non-combat)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Regeneration state label |
| Additional columns | Float | Regeneration rates for different resource types |

**References**:

- [`vendor/KotOR.js/src/module/ModuleCreature.ts:759`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleCreature.ts#L759) - Regeneration rate loading from 2DA

---

