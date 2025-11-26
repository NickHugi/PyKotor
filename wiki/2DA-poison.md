# poison.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines poison effect types and their properties. The engine uses this file to determine poison effects, durations, and damage calculations.

**Row Index**: Poison Type ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Poison type label |
| Additional columns | Various | Poison effect properties, damage, and duration |

**References**:

- [`vendor/NorthernLights/nwscript.nss:949`](https://github.com/th3w1zard1/NorthernLights/blob/master/nwscript.nss#L949) - Comment referencing poison.2da constants
- [`vendor/KotOR.js/src/nwscript/NWScriptDefK1.ts:3194-3199`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptDefK1.ts#L3194-L3199) - EffectPoison function

---

