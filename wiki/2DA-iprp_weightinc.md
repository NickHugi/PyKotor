# iprp_weightinc.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Maps item property values to weight increase calculations. The engine uses this file to determine weight increase calculations for item properties.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| `name` | StrRef | String reference for property name |
| Additional columns | Various | Weight increase mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:133,311`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L133) - StrRef column definition for iprp_weightinc.2da
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:586`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L586) - GFF field mapping: "WeightIncrease" -> iprp_weightinc.2da

---

