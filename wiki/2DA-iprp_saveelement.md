# iprp_saveelement.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Maps item property values to saving throw element types. The engine uses this file to determine saving throw element calculations for item properties.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | Saving throw element mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:485`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L485) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:84`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L84) - HTInstallation constant

---

