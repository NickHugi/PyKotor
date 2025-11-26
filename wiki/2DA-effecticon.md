# effecticon.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines effect icons displayed on character portraits and character sheets. The engine uses this file to determine which icon to display for status effects, buffs, and debuffs.

**Row Index**: Effect Icon ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Effect icon label |
| Additional columns | Various | Effect icon properties and ResRefs |

**References**:

- [`vendor/KotOR.js/src/engine/rules/SWRuleSet.ts:143-150`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/engine/rules/SWRuleSet.ts#L143-L150) - Effect icon initialization from 2DA
- [`vendor/KotOR.js/src/nwscript/NWScriptDefK1.ts:6441-6446`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptDefK1.ts#L6441-L6446) - SetEffectIcon function
- [`vendor/NorthernLights/nwscript.nss:4678`](https://github.com/th3w1zard1/NorthernLights/blob/master/nwscript.nss#L4678) - Comment referencing effecticon.2da

---

