# environment.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines environment configurations for areas. The engine uses this file to determine environment names and properties.

**Row Index**: Environment ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Environment label |
| `strref` | StrRef | String reference for environment name |
| Additional columns | Various | Environment properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:81`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L81) - StrRef column definition for environment.2da

---

