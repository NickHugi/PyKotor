# iprp_acmodtype.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Maps item property values to armor class modifier types. The engine uses this file to determine AC modifier calculations for item properties.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | AC modifier type mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:483`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L483) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:82`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L82) - HTInstallation constant

---

