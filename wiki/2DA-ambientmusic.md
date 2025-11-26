# ambientmusic.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines ambient music tracks for areas. The engine uses this file to determine which music to play in different areas based on area properties.

**Row Index**: Music ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Music label |
| `music` | ResRef | Music file ResRef |
| `resource` | ResRef | Music resource ResRef |
| `stinger1`, `stinger2`, `stinger3` | ResRef (optional) | Stinger music ResRefs |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:206`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L206) - Music ResRef column definitions for ambientmusic.2da (K1: resource, stinger1, stinger2, stinger3)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:398`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L398) - Music ResRef column definitions for ambientmusic.2da (K2: resource, stinger1, stinger2, stinger3)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:545-548`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L545-L548) - GFF field mapping: "MusicDay", "MusicNight", "MusicBattle", "MusicDelay" -> ambientmusic.2da

---

