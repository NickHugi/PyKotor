# tutorial.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines tutorial window tracking entries. The engine uses this file to track which tutorial windows have been shown to the player.

**Row Index**: Tutorial ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Tutorial label |
| Additional columns | Various | Tutorial window properties |

**References**:

- [`vendor/KotOR.js/src/managers/PartyManager.ts:180-187`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/managers/PartyManager.ts#L180-L187) - Tutorial window tracker initialization from 2DA
- [`vendor/KotOR.js/src/managers/PartyManager.ts:438`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/managers/PartyManager.ts#L438) - Tutorial table access

---

