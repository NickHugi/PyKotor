# iprp_mosterhit.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Maps item property values to monster hit effect types. The engine uses this file to determine monster hit effect calculations for item properties.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | Monster hit effect mappings |

**Note**: The filename contains a typo ("mosterhit" instead of "monsterhit") which is preserved in the game files.

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:489`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L489) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:88`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L88) - HTInstallation constant

---

