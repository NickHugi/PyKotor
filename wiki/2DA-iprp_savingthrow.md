# iprp_savingthrow.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Maps item property values to saving throw types. The engine uses this file to determine saving throw calculations for item properties.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | Saving throw type mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:486`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L486) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:85`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L85) - HTInstallation constant

---

