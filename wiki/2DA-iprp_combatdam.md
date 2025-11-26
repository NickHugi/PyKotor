# iprp_combatdam.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Maps item property values to combat damage bonuses. The engine uses this file to determine damage bonus calculations for item properties.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | Combat damage mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:480`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L480) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:79`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L79) - HTInstallation constant

---

