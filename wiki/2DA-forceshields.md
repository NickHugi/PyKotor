# forceshields.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines Force shield visual effects and properties. The engine uses this file to determine which visual effect to display when a Force shield is active.

**Row Index**: Force Shield ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Force shield label |
| Additional columns | Various | Force shield visual effect properties |

**References**:

- [`vendor/KotOR.js/src/nwscript/NWScriptDefK1.ts:5552`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptDefK1.ts#L5552) - Force shield lookup from 2DA

---

