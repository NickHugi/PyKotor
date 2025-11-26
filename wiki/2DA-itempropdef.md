# itempropdef.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines item property definitions and their base properties. This is the master table for all item properties in the game. The engine uses this file to determine item property types, costs, and effects.

**Row Index**: Item Property ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property label |
| Additional columns | Various | Property definitions, costs, and parameters |

**Note**: This file may be the same as or related to `itemprops.2da` documented earlier. The exact relationship between these files may vary between KotOR 1 and 2.

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:475`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L475) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:74`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L74) - HTInstallation constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/uti.py:107-111`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/uti.py#L107-L111) - Item property loading in item editor

---

