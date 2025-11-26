# crtemplates.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines creature template configurations. The engine uses this file to determine creature template names and properties.

**Row Index**: Creature Template ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Creature template label |
| `strref` | StrRef | String reference for creature template name |
| Additional columns | Various | Creature template properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:76`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L76) - StrRef column definition for crtemplates.2da

---

