# encdifficulty.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines encounter difficulty levels for area encounters. The engine uses this file to determine encounter scaling and difficulty modifiers.

**Row Index**: Difficulty ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Difficulty label |
| Additional columns | Various | Difficulty modifiers and properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:474`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L474) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:73`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L73) - HTInstallation constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/ute.py:101-104`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/ute.py#L101-L104) - Encounter difficulty selection

---

