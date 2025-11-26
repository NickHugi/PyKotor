# iprp_lightcol.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Maps item property values to light color configurations. The engine uses this file to determine light color settings for item properties.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | Light color mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:579`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L579) - GFF field mapping: "LightColor" -> iprp_lightcol.2da

---

