# iprp_protection.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Maps item property values to protection/immunity types. The engine uses this file to determine protection calculations for item properties.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | Protection type mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:482`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L482) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:81`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L81) - HTInstallation constant

---

