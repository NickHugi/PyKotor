# videoquality.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines video quality settings and graphics configuration options. The engine uses this file to determine maximum dynamic lights, shadow-casting lights, and other graphics quality parameters.

**Row Index**: Video Quality Setting ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Video quality setting label |
| `NumDynamicLights` | Integer | Maximum number of dynamic lights |
| `NumShadowCastingLights` | Integer | Maximum number of shadow-casting lights |
| Additional columns | Various | Other video quality parameters |

**References**:

- [`vendor/KotOR.js/src/managers/LightManager.ts:17-18`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/managers/LightManager.ts#L17-L18) - Comments referencing videoquality.2da for NumDynamicLights and NumShadowCastingLights
- [`vendor/KotOR.js/src/managers/LightManager.ts:37-38`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/managers/LightManager.ts#L37-L38) - Hardcoded values with comments referencing videoquality.2da

---

