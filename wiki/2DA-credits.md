# credits.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines credits/acknowledgments configurations (KotOR 2 only). The engine uses this file to determine credits entries.

**Row Index**: Credit ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Credit label |
| `name` | StrRef | String reference for credit name |
| Additional columns | Various | Credit properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:251`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L251) - StrRef column definition for credits.2da (KotOR 2 only)

---

