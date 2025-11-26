# rumble.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines rumble/vibration patterns for controller feedback. The engine uses this file to determine rumble patterns for camera shake and controller vibration effects.

**Row Index**: Rumble Pattern ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Rumble pattern label |
| `lsamples` | Integer | Left channel sample count |
| `rsamples` | Integer | Right channel sample count |
| Additional columns | Various | Rumble pattern data |

**References**:

- [`vendor/KotOR.js/src/managers/CameraShakeManager.ts:46`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/managers/CameraShakeManager.ts#L46) - Rumble pattern loading from 2DA
- [`vendor/KotOR.js/src/nwscript/NWScriptDefK1.ts:4500-4515`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptDefK1.ts#L4500-L4515) - PlayRumblePattern and StopRumblePattern functions

---

