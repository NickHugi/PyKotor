# subrace.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines subrace types for character creation and creature templates. The engine uses this file to determine subrace properties and restrictions.

**Row Index**: Subrace ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Subrace label |
| Additional columns | Various | Subrace properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:457`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L457) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:56`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L56) - HTInstallation constant

---

