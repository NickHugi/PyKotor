# iprp_costtable.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Master table listing all item property cost calculation tables. The engine uses this file to look up which cost table to use for calculating item property costs.

**Row Index**: Cost Table ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Cost table label |
| Additional columns | Various | Cost table ResRefs and properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:477`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L477) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:76`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L76) - HTInstallation constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/uti.py:486-496`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/uti.py#L486-L496) - Cost table lookup in item editor

---

