# iprp_abilities.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Maps item property values to ability score bonuses. The engine uses this file to determine which ability score is affected by an item property.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | Ability score mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:478`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L478) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:77`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L77) - HTInstallation constant

---

