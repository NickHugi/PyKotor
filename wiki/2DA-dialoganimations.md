# dialoganimations.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Maps dialog animation ordinals to animation names for use in conversations. The engine uses this file to determine which animation to play when a dialog line specifies an animation ordinal.

**Row Index**: Animation Index (integer, ordinal - 10000)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Animation label |
| `name` | String | Animation name (used to look up animation in model) |

**References**:

- [`vendor/reone/src/libs/game/gui/dialog.cpp:302-315`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/gui/dialog.cpp#L302-L315) - Dialog animation lookup from 2DA

---

