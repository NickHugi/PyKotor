# loadscreens.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines loading screen configurations for area transitions. The engine uses this file to determine which loading screen image, music, and hints to display when transitioning between areas.

**Row Index**: Loading Screen ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Loading screen label |
| `bmpresref` | ResRef | Loading screen background image ResRef |
| `musicresref` | ResRef | Music track ResRef to play during loading |
| Additional columns | Various | Other loading screen properties |

**References**:

- [`vendor/KotOR.js/src/module/ModuleArea.ts:210`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleArea.ts#L210) - Comment referencing loadscreens.2da for area loading screen index
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:549`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L549) - GFF field mapping: "LoadScreenID" -> loadscreens.2da

---

