# guisounds.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines sound effects for GUI interactions (button clicks, mouse enter events, etc.). The engine uses this file to play appropriate sounds when the player interacts with UI elements.

**Row Index**: Sound ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Sound label (e.g., "Clicked_Default", "Entered_Default") |
| `soundresref` | ResRef | Sound effect ResRef |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:200`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L200) - Sound ResRef column definition for guisounds.2da (K1: soundresref)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:392`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L392) - Sound ResRef column definition for guisounds.2da (K2: soundresref)

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/gui/sounds.cpp:31-45`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/gui/sounds.cpp#L31-L45) - GUI sound loading from 2DA

---

