# iprp_damagecost.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines cost calculations for damage bonus item properties. Used to determine item property costs based on damage bonus values.

**Row Index**: Damage bonus value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Damage bonus label |
| `cost` | Integer | Cost for this damage bonus value |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:99`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L99) - StrRef column definition for iprp_damagecost.2da (K1: name)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:277`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L277) - StrRef column definition for iprp_damagecost.2da (K2: name)

---

