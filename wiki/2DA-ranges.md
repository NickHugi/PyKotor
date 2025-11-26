# ranges.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines perception ranges for creatures, including sight and hearing ranges. The engine uses this file to determine how far creatures can see and hear.

**Row Index**: Range ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Range label |
| `primaryrange` | Float | Primary perception range (sight range) |
| `secondaryrange` | Float | Secondary perception range (hearing range) |

**References**:

- [`vendor/reone/src/libs/game/object/creature.cpp:1398-1406`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/creature.cpp#L1398-L1406) - Perception range loading from 2DA
- [`vendor/KotOR.js/src/module/ModuleCreature.ts:3178-3187`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleCreature.ts#L3178-L3187) - Perception range access from 2DA

---

