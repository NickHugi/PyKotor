# actions.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines action types and their properties. The engine uses this file to determine action icons, descriptions, and behaviors for various in-game actions.

**Row Index**: Action ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Action label |
| `string_ref` | StrRef | String reference for action description |
| `iconresref` | ResRef | Icon ResRef for the action |
| Additional columns | Various | Action properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:70`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L70) - StrRef column definition for actions.2da
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:212`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L212) - Texture ResRef column definition for actions.2da

---

