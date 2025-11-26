# upcrystals.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines upgrade crystal configurations. The engine uses this file to determine crystal model variations for lightsaber upgrades.

**Row Index**: Upgrade Crystal ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Upgrade crystal label |
| `shortmdlvar` | ResRef | Short model variation ResRef |
| `longmdlvar` | ResRef | Long model variation ResRef |
| `doublemdlvar` | ResRef | Double-bladed model variation ResRef |
| Additional columns | Various | Crystal properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:172`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L172) - Model ResRef column definitions for upcrystals.2da

---

