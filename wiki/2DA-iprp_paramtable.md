# iprp_paramtable.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Master table listing all item property parameter tables. The engine uses this file to look up which parameter table to use for a specific item property type.

**Row Index**: Parameter Table ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Parameter table label |
| Additional columns | Various | Parameter table ResRefs and properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:476`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L476) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:75`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L75) - HTInstallation constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/uti.py:517-558`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/uti.py#L517-L558) - Parameter table lookup in item editor

---

