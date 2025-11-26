# itempropsdef.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines item property definitions and their base properties. This is the master table for all item properties in the game. The engine uses this file to determine item property types, costs, and effects.

**Row Index**: Item Property ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property label |
| Additional columns | Various | Property definitions, costs, and parameters |

**Note**: This file may be the same as or related to `itempropdef.2da` and `itemprops.2da` documented earlier. The exact relationship between these files may vary between KotOR 1 and 2.

**References**:

- [`vendor/KotOR.js/src/engine/rules/SWRuleSet.ts:167-173`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/engine/rules/SWRuleSet.ts#L167-L173) - Item properties initialization from 2DA

---

