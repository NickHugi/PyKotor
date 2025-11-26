# iprp_damagetype.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Maps item property values to damage type flags. The engine uses this file to determine damage type calculations for item properties.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | Damage type mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:481`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L481) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:80`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L80) - HTInstallation constant

---

