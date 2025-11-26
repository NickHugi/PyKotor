# chargenclothes.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines character generation clothing configurations. The engine uses this file to determine starting clothing items for character creation.

**Row Index**: Character Generation Clothes ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Character generation clothes label |
| `itemresref` | ResRef | Item resource reference for clothing |
| Additional columns | Various | Character generation clothes properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:226,419`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L226) - Item ResRef column definition for chargenclothes.2da

---

