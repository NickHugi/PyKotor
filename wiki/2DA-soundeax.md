# soundeax.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines EAX (Environmental Audio Extensions) sound presets for 3D audio processing. The engine uses this file to determine EAX preset configurations for different environments.

**Row Index**: EAX Preset ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | EAX preset label |
| Additional columns | Various | EAX preset parameters and properties |

**References**:

- [`vendor/KotOR.js/src/apps/forge/states/MenuTopState.tsx:420`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/apps/forge/states/MenuTopState.tsx#L420) - EAX presets loading from 2DA

---

