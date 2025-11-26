# gender.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines gender types for character creation and creature templates. The engine uses this file to determine gender-specific properties and restrictions.

**Row Index**: Gender ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Gender label |
| Additional columns | Various | Gender properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:461`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L461) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:60`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L60) - HTInstallation constant

---

