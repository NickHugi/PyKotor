# ammunitiontypes.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines ammunition types for ranged weapons, including their models and sound effects. The engine uses this file when loading items to determine ammunition properties for ranged weapons.

**Row Index**: Ammunition Type ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Ammunition type label |
| `model` | ResRef | Ammunition model ResRef |
| `shotsound0` | ResRef (optional) | Shot sound effect ResRef (variant 1) |
| `shotsound1` | ResRef (optional) | Shot sound effect ResRef (variant 2) |
| `impactsound0` | ResRef (optional) | Impact sound effect ResRef (variant 1) |
| `impactsound1` | ResRef (optional) | Impact sound effect ResRef (variant 2) |

**References**:

- [`vendor/reone/src/libs/game/object/item.cpp:164-171`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/item.cpp#L164-L171) - Ammunition type loading from 2DA

---

