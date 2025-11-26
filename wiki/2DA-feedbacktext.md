# feedbacktext.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines feedback text strings displayed to the player for various game events and actions. The engine uses this file to provide contextual feedback messages.

**Row Index**: Feedback Text ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Feedback text label |
| Additional columns | Various | Feedback text strings and properties |

**References**:

- [`vendor/NorthernLights/nwscript.nss:3858`](https://github.com/th3w1zard1/NorthernLights/blob/master/nwscript.nss#L3858) - Comment referencing FeedBackText.2da
- [`vendor/KotOR.js/src/nwscript/NWScriptDefK1.ts:4464-4465`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptDefK1.ts#L4464-L4465) - DisplayFeedBackText function

---

