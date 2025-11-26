# iprp_damagered.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Maps item property values to damage reduction calculations. The engine uses this file to determine damage reduction calculations for item properties.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | Damage reduction mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:588`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L588) - GFF field mapping: "DamageReduction" -> iprp_damagered.2da

---

