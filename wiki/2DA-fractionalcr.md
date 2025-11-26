# fractionalcr.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines fractional challenge rating configurations. The engine uses this file to determine fractional CR display strings.

**Row Index**: Fractional CR ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Fractional CR label |
| `displaystrref` | StrRef | String reference for fractional CR display text |
| Additional columns | Various | Fractional CR properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:84`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L84) - StrRef column definition for fractionalcr.2da

---

