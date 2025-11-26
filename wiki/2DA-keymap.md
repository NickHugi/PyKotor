# keymap.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines keyboard and controller key mappings for different game contexts (in-game, GUI, dialog, minigame, etc.). The engine uses this file to determine which keys trigger which actions in different contexts.

**Row Index**: Keymap Entry ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Keymap entry label |
| Additional columns | Various | Key mappings for different contexts (ingame, gui, dialog, minigame, freelook, movie) |

**References**:

- [`vendor/KotOR.js/src/controls/KeyMapper.ts:293-299`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/controls/KeyMapper.ts#L293-L299) - Keymap initialization from 2DA

---

